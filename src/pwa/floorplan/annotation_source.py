"""Manual annotation adapter."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

from PIL import Image

from pwa.contracts import compute_content_hash, validate_artifact
from pwa.floorplan.config import MAX_SOURCE_RASTER_BYTES
from pwa.floorplan.findings import FloorplanError
from pwa.floorplan.runs import resolve_contained_relpath
from pwa.floorplan.types import RawDimension, RawGeometry, RawOpening, RawRoom, RawWall, SourceFrame

_APPROVED_ANNOTATION_IMAGE_KINDS = {"floorplan", "floorplan_page"}
_APPROVED_FORMATS_BY_KIND = {
    "floorplan": {"PNG", "JPEG"},
    "floorplan_page": {"PNG"},
}


class AnnotationSource:
    def accepts(self, path: Path) -> bool:
        return path.suffix.lower() == ".json"

    def extract(
        self,
        path: Path,
        *,
        source_root: Path | None = None,
        source_inventory: dict[str, dict] | None = None,
        document: dict | None = None,
    ) -> RawGeometry:
        geometry, _ = self.extract_with_image_snapshot(
            path,
            source_root=source_root,
            source_inventory=source_inventory,
            document=document,
        )
        return geometry

    def extract_with_image_snapshot(
        self,
        path: Path,
        *,
        source_root: Path | None = None,
        source_inventory: dict[str, dict] | None = None,
        document: dict | None = None,
    ) -> tuple[RawGeometry, bytes]:
        if document is None:
            document = json.loads(Path(path).read_text(encoding="utf-8"))
        errors = validate_artifact(document)
        if errors:
            raise ValueError(errors[0].message)
        # GC-4 (OpenAI cross-provider rework review, 2026-08-10): schema
        # validation alone does not prove the payload was not tampered with
        # after content_hash was computed -- recompute and verify it the
        # same way every other source artifact's hash is checked (source
        # manifest, quality report, inventory items).
        if document.get("content_hash") != compute_content_hash(document):
            raise FloorplanError("PARSE_SOURCE_HASH_MISMATCH", "annotation content_hash mismatch")
        payload = document["payload"]
        image_ref = payload["image"]["source_image_ref"]
        approved_formats = {"PNG", "JPEG"}
        if source_inventory is not None:
            inventory_entry = source_inventory.get(image_ref)
            if inventory_entry is None:
                raise FloorplanError(
                    "PARSE_SOURCE_UNSUPPORTED",
                    "annotation source image is not part of the source inventory",
                    source_ref=image_ref,
                )
            inventory_kind = inventory_entry.get("kind")
            if inventory_kind not in _APPROVED_ANNOTATION_IMAGE_KINDS:
                raise FloorplanError(
                    "PARSE_SOURCE_UNSUPPORTED",
                    "annotation source image is not an approved floorplan source artifact",
                    source_ref=image_ref,
                )
            approved_formats = _APPROVED_FORMATS_BY_KIND[inventory_kind]
        image_root = source_root if source_root is not None else Path(path).parent
        image_path = resolve_contained_relpath(image_root, image_ref)
        with image_path.open("rb") as stream:
            image_bytes = stream.read(MAX_SOURCE_RASTER_BYTES + 1)
        if len(image_bytes) > MAX_SOURCE_RASTER_BYTES:
            raise FloorplanError(
                "PARSE_RESOURCE_LIMIT",
                "source raster exceeds byte limit",
                source_ref=image_ref,
            )
        image_sha256 = "sha256:" + hashlib.sha256(image_bytes).hexdigest()
        if image_sha256 != payload["image"]["sha256"]:
            raise FloorplanError("PARSE_SOURCE_HASH_MISMATCH", "annotation image hash mismatch")
        if source_inventory is not None and image_sha256 != source_inventory[image_ref]["sha256"]:
            raise FloorplanError("PARSE_SOURCE_HASH_MISMATCH", "annotation image hash does not match source inventory")
        try:
            with Image.open(io.BytesIO(image_bytes)) as image:
                if image.format not in approved_formats:
                    raise FloorplanError(
                        "PARSE_SOURCE_UNSUPPORTED",
                        "annotation source image format is unsupported for its inventory kind",
                        source_ref=image_ref,
                    )
                image.load()
                width_px, height_px = image.width, image.height
        except FloorplanError:
            raise
        except (OSError, SyntaxError, ValueError) as exc:
            raise FloorplanError(
                "PARSE_SOURCE_UNSUPPORTED",
                "annotation source image bytes do not decode to an approved format",
                source_ref=image_ref,
            ) from exc
        if width_px != payload["image"]["width_px"] or height_px != payload["image"]["height_px"]:
            raise ValueError("annotation image dimensions do not match the decoded source image")
        frame = SourceFrame(
            kind="raster",
            unit_scale_m=payload["scale_m_per_px"],
            y_down=True,
            height_px=height_px,
            source_units="px",
        )
        return RawGeometry(
            frame=frame,
            walls=tuple(
                RawWall(index, f"annotation:walls[{index}]", tuple(item["start_px"]), tuple(item["end_px"]))
                for index, item in enumerate(payload["walls"])
            ),
            rooms=tuple(
                RawRoom(index, f"annotation:rooms[{index}]", tuple(tuple(point) for point in item["polygon_px"]))
                for index, item in enumerate(payload["rooms"])
            ),
            openings=tuple(
                RawOpening(
                    index,
                    f"annotation:openings[{index}]",
                    item["type"],
                    tuple(item["center_px"]),
                    item["width_m"],
                    None,
                    item["wall_index"],
                )
                for index, item in enumerate(payload["openings"])
            ),
            dimensions=tuple(
                RawDimension(
                    index,
                    f"annotation:declared_dimensions[{index}]",
                    tuple(item["a_px"]),
                    tuple(item["b_px"]),
                    item["length_m"],
                )
                for index, item in enumerate(payload["declared_dimensions"])
            ),
            scanned_entities=(
                len(payload["walls"]) + len(payload["rooms"]) + len(payload["openings"]) + len(payload["declared_dimensions"])
            ),
            unmapped=(),
        ), image_bytes
