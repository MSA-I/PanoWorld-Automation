"""Manual annotation adapter."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from pwa.contracts import compute_content_hash, validate_artifact
from pwa.files import sha256_file
from pwa.floorplan.findings import FloorplanError
from pwa.floorplan.types import RawDimension, RawGeometry, RawOpening, RawRoom, RawWall, SourceFrame

# GC-5 (OpenAI cross-provider rework review, 2026-08-10): section 6 permits
# annotation image binding only to "the immutable PNG/JPEG floorplan input or
# one explicitly selected intake-generated PDF page ... already listed in the
# source manifest." The current source-inventory "kind" vocabulary
# (src/pwa/intake.py) only distinguishes "floorplan" unambiguously -- PDF-page
# derivatives and other generated artifacts are all tagged "other" alongside
# each other, so there is no separate kind to safelist for them without a
# manifest/contract change (out of bounded scope here; see rework report).
_APPROVED_ANNOTATION_IMAGE_KINDS = {"floorplan"}


class AnnotationSource:
    def accepts(self, path: Path) -> bool:
        return path.suffix.lower() == ".json"

    def extract(
        self,
        path: Path,
        *,
        source_root: Path | None = None,
        source_inventory: dict[str, dict] | None = None,
    ) -> RawGeometry:
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
        if source_inventory is not None and image_ref not in source_inventory:
            raise ValueError("annotation source image is not part of the source inventory")
        # GC-5: membership and hash were checked, but not "kind" -- an
        # annotation could bind to the style-reference image (or any other
        # non-floorplan inventory entry) instead of the floorplan raster.
        if source_inventory is not None and source_inventory[image_ref].get("kind") not in _APPROVED_ANNOTATION_IMAGE_KINDS:
            raise ValueError("annotation source image is not an approved floorplan source artifact")
        image_path = (source_root / image_ref) if source_root is not None else (Path(path).parent / image_ref)
        if sha256_file(image_path) != payload["image"]["sha256"]:
            raise FloorplanError("PARSE_SOURCE_HASH_MISMATCH", "annotation image hash mismatch")
        if source_inventory is not None and source_inventory[image_ref]["sha256"] != payload["image"]["sha256"]:
            raise FloorplanError("PARSE_SOURCE_HASH_MISMATCH", "annotation image hash does not match source inventory")
        with Image.open(image_path) as image:
            width_px, height_px = image.width, image.height
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
        )
