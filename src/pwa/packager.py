"""Fixture-backed immutable PanoWorld packager baseline (PLAN-001)."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pwa.contracts import compute_content_hash, validate_artifact
from pwa.files import copy_immutable, sha256_file, write_json_exclusive
from pwa.fixtures import STYLE_PANO_NAME, make_tiny_scene
from pwa.intake import ingest_project
from pwa.validator.package_validator import PackageValidator, REQUIRED_FILES, _parse_map

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_FIXTURE = REPO_ROOT / "tests" / "golden" / "panoworld_demo_subset"
_RUN_ID_RE = re.compile(r"^RUN-\d{8}-\d{6}-[a-z0-9]{4,16}$")


def package_tree_hash(scene_dir: Path) -> tuple[str, list[dict]]:
    inventory = [
        {
            "path": path.relative_to(scene_dir).as_posix(),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(scene_dir.rglob("*"), key=lambda p: p.as_posix())
        if path.is_file()
    ]
    canonical = json.dumps(inventory, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest(), inventory


def _manifest_artifact(payload: dict, *, project_id: str, run_id: str) -> dict:
    document = {
        "schema_id": "panoworld_manifest",
        "schema_version": "1.0.0",
        "artifact_id": f"{run_id}:panoworld_manifest",
        "project_id": project_id,
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "producer": {
            "agent": "plan001-fixture-packager",
            "provider": "local",
            "model": "deterministic-python",
            "effort": "N/A",
        },
        "inputs": [],
        "content_hash": "sha256:" + "0" * 64,
        "status": "complete",
        "errors": [],
        "payload": payload,
    }
    document["content_hash"] = compute_content_hash(document)
    errors = validate_artifact(document)
    if errors:
        raise ValueError(f"generated panoworld_manifest failed schema: {errors[0].message}")
    return document


def _fixture_source(layer: str, temp_root: Path) -> Path:
    if layer == "golden":
        return GOLDEN_FIXTURE
    if layer == "tiny":
        return make_tiny_scene(temp_root)
    raise ValueError("fixture layer must be 'tiny' or 'golden'")


def build_fixture_package(
    run_root: Path,
    *,
    project_id: str,
    run_id: str,
    fixture_layer: str,
) -> tuple[dict, dict, list[dict]]:
    package_scene = run_root / "package" / "scene"
    with tempfile.TemporaryDirectory(dir=run_root, prefix=".fixture-") as temp:
        source = _fixture_source(fixture_layer, Path(temp))
        map_payloads: list[dict] = []
        viewpoint_ids: list[str] = []
        for source_map in sorted(source.glob("map*.json")):
            entries = _parse_map(source_map)
            map_payloads.append(
                {"file": source_map.name, "entries": [{"key": key, "values": values} for key, values in entries]}
            )
            for key, values in entries:
                for viewpoint_id in [key, *values]:
                    if viewpoint_id not in viewpoint_ids:
                        viewpoint_ids.append(viewpoint_id)
            output_map = package_scene / source_map.name
            output_map.parent.mkdir(parents=True, exist_ok=True)
            with output_map.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump({key: values for key, values in entries}, stream, indent=2)
                stream.write("\n")

        if not map_payloads or not viewpoint_ids:
            raise ValueError("fixture has no usable map/viewpoints")

        viewpoints: list[dict] = []
        for viewpoint_id in viewpoint_ids:
            source_dir = source / "viewpoints" / viewpoint_id
            target_dir = package_scene / "viewpoints" / viewpoint_id
            files = {}
            for filename in REQUIRED_FILES:
                copy_immutable(source_dir / filename, target_dir / filename)
            files.update(
                {
                    "place_image": "place_image.png",
                    "place_depth": "place_depth.png",
                    "place_depth_scale": "place_depth_scale.txt",
                    "extrinsics": "extrinsics.txt",
                }
            )
            style_source = source_dir / STYLE_PANO_NAME
            has_style = style_source.is_file()
            if has_style:
                copy_immutable(style_source, target_dir / STYLE_PANO_NAME)
            viewpoints.append({"id": viewpoint_id, "files": files, "has_style_pano": has_style})

    package_hash, inventory = package_tree_hash(package_scene)
    manifest = _manifest_artifact(
        {
            "scene_dir": "package/scene",
            "maps": map_payloads,
            "viewpoints": viewpoints,
            "start": {
                "panoworld_start_image": STYLE_PANO_NAME,
                "pano_image_name": "panoImage_2048.png",
            },
            "package_hash": package_hash,
        },
        project_id=project_id,
        run_id=run_id,
    )
    write_json_exclusive(run_root / "artifacts" / "panoworld_manifest.json", manifest)

    validator = PackageValidator(
        package_scene,
        start_image=STYLE_PANO_NAME if fixture_layer == "tiny" else None,
        pano_image_name="panoImage_2048.png" if fixture_layer == "tiny" else None,
        max_views=8 if fixture_layer == "tiny" else None,
    )
    report = validator.validate().to_dict()
    write_json_exclusive(run_root / "evidence" / "package-validator.json", report)
    if report["errors"]:
        raise ValueError(f"packaged fixture failed validator: {report['errors'][0]['code']}")
    return manifest, report, inventory


def make_run_id(floorplan: Path, style_reference: Path) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    digest = hashlib.sha256(
        (sha256_file(Path(floorplan)) + sha256_file(Path(style_reference))).encode("ascii")
    ).hexdigest()[:8]
    return f"RUN-{stamp}-{digest}"


def build_baseline_run(
    *,
    runs_root: Path,
    project_id: str,
    floorplan: Path,
    style_reference: Path,
    goal: str = "conceptual",
    units: str = "unknown",
    m_per_px: float | None = None,
    fixture_layer: str = "tiny",
    run_id: str | None = None,
) -> tuple[Path, bool]:
    runs_root = Path(runs_root)
    run_id = run_id or make_run_id(floorplan, style_reference)
    if not _RUN_ID_RE.fullmatch(run_id):
        raise ValueError("run_id must match RUN-YYYYMMDD-HHMMSS-<short-hash>")
    final = runs_root / run_id
    staging = runs_root / ".staging" / run_id
    if final.exists() or staging.exists():
        raise FileExistsError(f"run already exists: {run_id}")
    staging.mkdir(parents=True)
    _, report = ingest_project(
        staging,
        project_id=project_id,
        run_id=run_id,
        floorplan=floorplan,
        style_reference=style_reference,
        goal=goal,
        units=units,
        m_per_px=m_per_px,
    )
    complete = report["status"] == "complete"
    if complete:
        build_fixture_package(
            staging,
            project_id=project_id,
            run_id=run_id,
            fixture_layer=fixture_layer,
        )
    final.parent.mkdir(parents=True, exist_ok=True)
    os.replace(staging, final)
    return final, complete
