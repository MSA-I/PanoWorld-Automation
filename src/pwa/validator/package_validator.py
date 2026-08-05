"""PanoWorld input-package validator (PLAN-000 T8, green phase).

Validates a scene directory against the format PanoWorld's loaders actually
enforce — every check traces to verified upstream behaviour
(evidence/SESSION-001/agent-reports/panoworld-compat.md) or to the locked
vocabulary in contracts/error_codes.md.

Modes:
- scene-only (default): structural checks needing no run config.
- with-config: any of start_image / pano_image_name / max_views enables the
  config-dependent checks (START_IMAGE_MISSING, PANO_NAME_COLLISION,
  VIEWPOINT_BUDGET_EXCEEDED).

Reported paths are scene-relative with forward slashes so reports are
snapshot-stable across machines.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

import numpy as np
from PIL import Image

REQUIRED_FILES = (
    "extrinsics.txt",
    "place_image.png",
    "place_depth.png",
    "place_depth_scale.txt",
)

# Codes that report but never fail validation (contracts/error_codes.md).
WARN_CODES = frozenset({
    "VIEWPOINT_NOT_IN_MAP",
    "NONSTANDARD_WORLD_CONVENTION",
    "CAMERA_HEIGHT_OUTLIER",
    "CAMERA_POSITION_OUTLIER",
    "VIEWPOINTS_TOO_CLOSE",
    "ODD_DIMENSIONS",
    "DEPTH_RANGE_IMPLAUSIBLE",
    "VRAM_BUDGET_WARNING",
})

DEPTH_MODES = ("I", "I;16")  # 16-bit single channel; Pillow reports either.

_RESERVED_NAMES = (
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)


@dataclass
class Report:
    scene: str
    mode: str
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        return {
            "scene": self.scene,
            "mode": self.mode,
            "errors": self.errors,
            "warnings": self.warnings,
            "summary": self.summary,
        }


def check_filename(name: str) -> bool:
    """True if the name is safe on Windows/NTFS: no reserved device name, no
    trailing dot or space (NTFS cannot round-trip those via the normal API)."""
    if not name or name != name.rstrip(". "):
        return False
    stem = name.split(".", 1)[0].upper()
    return stem not in _RESERVED_NAMES


def check_extrinsics_matrix(matrix) -> list[str]:
    """Return codes for a parsed extrinsics matrix (camera-to-world, 4x4).

    Hard errors first; convention/height warnings only for otherwise-clean
    matrices (a broken matrix makes convention analysis meaningless).
    """
    m = np.asarray(matrix, dtype=float)
    if m.ndim != 2 or m.shape != (4, 4):
        return ["INVALID_MATRIX_SHAPE"]

    codes: list[str] = []
    if abs(float(np.linalg.det(m))) < 1e-9:
        codes.append("MATRIX_NOT_INVERTIBLE")
    if not np.allclose(m[3], [0.0, 0.0, 0.0, 1.0], atol=1e-6):
        codes.append("MATRIX_LAST_ROW_INVALID")

    r = m[:3, :3]
    if "MATRIX_NOT_INVERTIBLE" not in codes:
        if not np.allclose(r.T @ r, np.eye(3), atol=1e-4):
            codes.append("MATRIX_NOT_ORTHONORMAL")
        elif float(np.linalg.det(r)) < 0:
            codes.append("MATRIX_NOT_RIGHT_HANDED")

    if not codes:
        # Demo-data convention: camera +Y (image down) maps to world -Z (Z-up).
        if not np.allclose(r[:, 1], [0.0, 0.0, -1.0], atol=1e-3):
            codes.append("NONSTANDARD_WORLD_CONVENTION")
        else:
            height = float(m[2, 3])
            if not 0.5 <= height <= 3.0:
                codes.append("CAMERA_HEIGHT_OUTLIER")
        if float(np.linalg.norm(m[:3, 3])) > 50.0:
            codes.append("CAMERA_POSITION_OUTLIER")
    return codes


class _DuplicateMapKey(ValueError):
    pass


def _parse_map(path: Path) -> list[tuple[str, list[str]]]:
    """Parse a map JSON preserving insertion order; raise on duplicate keys
    (intra-map only) or structural nonconformance."""
    entries: list[tuple[str, list[str]]] = []

    def hook(pairs):
        keys = [k for k, _ in pairs]
        if len(keys) != len(set(keys)):
            raise _DuplicateMapKey(path.name)
        return dict(pairs)

    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=hook)
    if not isinstance(data, dict) or not data:
        raise ValueError("map root must be a non-empty JSON object")
    for key, values in data.items():
        if not isinstance(key, str) or not isinstance(values, list) or not all(
            isinstance(v, str) for v in values
        ):
            raise ValueError("map must be {string: [string, ...]}")
        entries.append((key, list(values)))
    return entries


class PackageValidator:
    def __init__(
        self,
        scene_dir: Path,
        *,
        start_image: str | None = None,
        pano_image_name: str | None = None,
        max_views: int | None = None,
    ) -> None:
        self.scene_dir = Path(scene_dir)
        self.start_image = start_image
        self.pano_image_name = pano_image_name
        self.max_views = max_views

    # -- helpers -------------------------------------------------------------

    def _add(self, findings: list, code: str, rel_path: str, message: str) -> None:
        findings.append({"code": code, "path": rel_path, "message": message})

    # -- main ----------------------------------------------------------------

    def validate(self) -> Report:
        with_config = any(
            v is not None for v in (self.start_image, self.pano_image_name, self.max_views)
        )
        report = Report(
            scene=self.scene_dir.name,
            mode="with-config" if with_config else "scene-only",
        )
        findings: list[dict] = []
        scene = self.scene_dir
        vps_dir = scene / "viewpoints"

        if not vps_dir.is_dir():
            self._add(findings, "MISSING_VIEWPOINTS_DIR", "viewpoints",
                      "viewpoints/ must be a sibling directory of the map JSON")
            self._finish(report, findings, maps=0, mapped=set(), on_disk=[])
            return report

        on_disk = sorted(p.name for p in vps_dir.iterdir() if p.is_dir())

        # Windows-hostile names anywhere under viewpoints/.
        for entry in sorted(vps_dir.iterdir(), key=lambda p: p.name):
            if not check_filename(entry.name):
                self._add(findings, "INVALID_FILENAME", f"viewpoints/{entry.name}",
                          "reserved device name or trailing dot/space")
            if entry.is_dir():
                for child in sorted(entry.iterdir(), key=lambda p: p.name):
                    if not check_filename(child.name):
                        self._add(findings, "INVALID_FILENAME",
                                  f"viewpoints/{entry.name}/{child.name}",
                                  "reserved device name or trailing dot/space")

        # Maps: arbitrary map*.json names (upstream name is a convention only).
        map_files = sorted(scene.glob("map*.json"))
        if not map_files:
            self._add(findings, "NO_MAP_FILE", ".", "no map*.json found in scene root")

        mapped: set[str] = set()
        traversal_totals: list[int] = []
        parsed_maps: list[tuple[str, list[tuple[str, list[str]]]]] = []
        for mf in map_files:
            try:
                entries = _parse_map(mf)
            except _DuplicateMapKey:
                self._add(findings, "DUPLICATE_MAP_KEY", mf.name,
                          "the same key appears twice within one map file")
                continue
            except (json.JSONDecodeError, ValueError, UnicodeDecodeError) as exc:
                self._add(findings, "MAP_JSON_INVALID", mf.name, str(exc))
                continue

            parsed_maps.append((mf.name, entries))
            if not entries[0][1]:
                self._add(findings, "EMPTY_MAP_VALUES", mf.name,
                          "the start key has an empty values array")
            referenced: list[str] = []
            for key, values in entries:
                referenced.append(key)
                referenced.extend(values)
            for name in referenced:
                if name not in on_disk:
                    self._add(findings, "MAP_REFERENCES_UNKNOWN_VIEWPOINT", mf.name,
                              f"references viewpoint {name!r} with no directory")
                else:
                    mapped.add(name)
            # Upstream traversal appends: start, every value, every non-first key.
            traversal_totals.append(len({k for k, _ in entries})
                                    + sum(len(v) for _, v in entries))

        for name in on_disk:
            if name not in mapped:
                self._add(findings, "VIEWPOINT_NOT_IN_MAP", f"viewpoints/{name}",
                          "directory exists but no map references it (spare start node?)")

        # Per-viewpoint file checks (mapped viewpoints only).
        positions: dict[str, np.ndarray] = {}
        image_width: int | None = None
        for vp in sorted(mapped & set(on_disk)):
            vp_dir = vps_dir / vp
            rel = f"viewpoints/{vp}"
            present: dict[str, Path] = {}
            for name in REQUIRED_FILES:
                f = vp_dir / name
                if not f.is_file():
                    self._add(findings, "MISSING_REQUIRED_FILE", f"{rel}/{name}",
                              "required file missing")
                elif f.stat().st_size == 0:
                    self._add(findings, "EMPTY_FILE", f"{rel}/{name}", "file is empty")
                else:
                    present[name] = f

            # extrinsics
            if "extrinsics.txt" in present:
                try:
                    matrix = np.loadtxt(str(present["extrinsics.txt"]))
                except Exception as exc:  # np.loadtxt raises ValueError subclasses
                    self._add(findings, "MATRIX_PARSE_ERROR", f"{rel}/extrinsics.txt", str(exc))
                else:
                    for code in check_extrinsics_matrix(matrix):
                        self._add(findings, code, f"{rel}/extrinsics.txt",
                                  "extrinsics check failed" if code not in WARN_CODES
                                  else "extrinsics convention warning")
                    if getattr(matrix, "shape", None) == (4, 4):
                        positions[vp] = np.asarray(matrix, dtype=float)[:3, 3]

            # place_image
            img_size = None
            if "place_image.png" in present:
                try:
                    with Image.open(present["place_image.png"]) as im:
                        img_mode, img_size = im.mode, im.size
                except Exception as exc:
                    self._add(findings, "IMAGE_UNREADABLE", f"{rel}/place_image.png", str(exc))
                else:
                    if img_mode != "RGB":
                        self._add(findings, "INVALID_IMAGE_MODE", f"{rel}/place_image.png",
                                  f"expected RGB, got {img_mode}")
                    self._check_dims(findings, f"{rel}/place_image.png", img_size)
                    image_width = max(image_width or 0, img_size[0])

            # place_depth
            depth_arr = None
            if "place_depth.png" in present:
                try:
                    with Image.open(present["place_depth.png"]) as im:
                        depth_mode, depth_size = im.mode, im.size
                        depth_arr = np.array(im, dtype=np.float64)
                except Exception as exc:
                    self._add(findings, "IMAGE_UNREADABLE", f"{rel}/place_depth.png", str(exc))
                else:
                    if depth_mode not in DEPTH_MODES:
                        self._add(findings, "INVALID_IMAGE_MODE", f"{rel}/place_depth.png",
                                  f"expected 16-bit single channel (I/I;16), got {depth_mode}")
                    self._check_dims(findings, f"{rel}/place_depth.png", depth_size)
                    if img_size is not None and depth_size != img_size:
                        self._add(findings, "DEPTH_RGB_DIMENSION_MISMATCH",
                                  f"{rel}/place_depth.png",
                                  f"depth {list(depth_size)} != rgb {list(img_size)}")
                    if depth_arr is not None and depth_arr.size:
                        zero_frac = float((depth_arr == 0).mean())
                        if zero_frac > 0.5:
                            self._add(findings, "DEPTH_MOSTLY_INVALID",
                                      f"{rel}/place_depth.png",
                                      f"{zero_frac:.0%} of depth pixels are 0/invalid")

            # depth scale (depth_m = pixel / scale; upstream raises on <= 0)
            if "place_depth_scale.txt" in present:
                raw = present["place_depth_scale.txt"].read_text(encoding="utf-8").strip()
                try:
                    scale_val = float(raw)
                except ValueError:
                    scale_val = math.nan
                if not math.isfinite(scale_val) or scale_val <= 0:
                    self._add(findings, "INVALID_DEPTH_SCALE",
                              f"{rel}/place_depth_scale.txt",
                              f"must be a finite positive number, got {raw!r}")
                elif depth_arr is not None and depth_arr.size:
                    valid = depth_arr[depth_arr > 0]
                    if valid.size:
                        max_m = float(valid.max()) / scale_val
                        median_m = float(np.median(valid)) / scale_val
                        if not (0.05 < max_m < 50.0) or not (0.1 < median_m < 30.0):
                            self._add(findings, "DEPTH_RANGE_IMPLAUSIBLE",
                                      f"{rel}/place_depth_scale.txt",
                                      f"max={max_m:.2f}m median={median_m:.2f}m "
                                      "outside plausible indoor range")

        # Cross-viewpoint sanity.
        for a, b in combinations(sorted(positions), 2):
            if float(np.linalg.norm(positions[a] - positions[b])) < 0.2:
                self._add(findings, "VIEWPOINTS_TOO_CLOSE", f"viewpoints/{a}",
                          f"less than 0.2 m from viewpoints/{b}")

        # Config-dependent checks.
        if with_config and parsed_maps:
            for map_name, entries in parsed_maps:
                start_key = entries[0][0]
                if self.start_image is not None and start_key in on_disk:
                    if not (vps_dir / start_key / self.start_image).is_file():
                        self._add(findings, "START_IMAGE_MISSING",
                                  f"viewpoints/{start_key}/{self.start_image}",
                                  f"start viewpoint of {map_name} lacks the configured start image")
                if self.max_views is not None:
                    total = len({k for k, _ in entries}) + sum(len(v) for _, v in entries)
                    if total > self.max_views:
                        self._add(findings, "VIEWPOINT_BUDGET_EXCEEDED", map_name,
                                  f"traversal has {total} nodes > max_views={self.max_views}")
            if self.pano_image_name is not None:
                for vp in sorted(mapped & set(on_disk)):
                    if (vps_dir / vp / self.pano_image_name).exists():
                        self._add(findings, "PANO_NAME_COLLISION",
                                  f"viewpoints/{vp}/{self.pano_image_name}",
                                  "configured pano_image_name collides with an existing "
                                  "input file (inference writes outputs back into viewpoint dirs)")

        # VRAM heuristic (warn-only; the memory table is not primary-source-verified).
        if image_width is not None and image_width >= 2048 and traversal_totals:
            worst = max(traversal_totals)
            if worst >= 12:
                self._add(findings, "VRAM_BUDGET_WARNING", ".",
                          f"{worst} traversal nodes at width {image_width}: the local "
                          "guide's memory table reports OOM at 12 views @ 2048 on H200")

        self._finish(report, findings, maps=len(map_files), mapped=mapped, on_disk=on_disk)
        return report

    def _check_dims(self, findings: list, rel: str, size: tuple[int, int]) -> None:
        width, height = size
        if height == 0 or width / height != 2:  # exact compare, as upstream enforces
            self._add(findings, "INVALID_ASPECT_RATIO", rel,
                      f"width/height must be exactly 2, got {width}x{height}")
        if width % 2 or height % 2:
            self._add(findings, "ODD_DIMENSIONS", rel,
                      "dimensions should be even (patch alignment)")

    def _finish(self, report: Report, findings: list, *, maps: int,
                mapped: set, on_disk: list) -> None:
        for f in sorted(findings, key=lambda f: (f["path"], f["code"])):
            (report.warnings if f["code"] in WARN_CODES else report.errors).append(f)
        report.summary = {
            "maps": maps,
            "viewpoints_mapped": len(mapped),
            "viewpoints_on_disk": len(on_disk),
        }
