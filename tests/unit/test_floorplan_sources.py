from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import ezdxf
import pytest
from PIL import Image

from pwa.contracts import compute_content_hash
from pwa.floorplan.annotation_source import AnnotationSource
from pwa.floorplan.dxf_source import DxfSource
from pwa.floorplan.findings import FloorplanError
from pwa.floorplan.dxf_worker import extract_dxf
from pwa.floorplan.normalize import canonical_projection, normalize
from pwa.files import sha256_file


def _write_annotation_fixture(root: Path) -> tuple[Path, Path]:
    image_path = root / "project" / "inputs" / "originals" / "layer-a-1.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (2000, 1800), "white").save(image_path, format="PNG")
    payload = {
        "image": {
            "source_image_ref": "project/inputs/originals/layer-a-1.png",
            "sha256": "sha256:" + "0" * 64,
            "width_px": 2000,
            "height_px": 1800,
        },
        "scale_m_per_px": 0.005,
        "walls": [
            {"start_px": [200, 1400], "end_px": [1800, 1400]},
            {"start_px": [1800, 1400], "end_px": [1800, 200]},
            {"start_px": [200, 200], "end_px": [1800, 200]},
            {"start_px": [200, 1400], "end_px": [200, 200]},
            {"start_px": [1200, 1400], "end_px": [1200, 200]},
        ],
        "rooms": [
            {"polygon_px": [[200, 1400], [1200, 1400], [1200, 200], [200, 200]]},
            {"polygon_px": [[1200, 1400], [1800, 1400], [1800, 200], [1200, 200]]},
        ],
        "openings": [
            {"type": "door", "wall_index": 0, "center_px": [700, 1400], "width_m": 0.9},
            {"type": "door", "wall_index": 4, "center_px": [1200, 800], "width_m": 0.9},
            {"type": "window", "wall_index": 2, "center_px": [600, 200], "width_m": 1.2},
            {"type": "window", "wall_index": 1, "center_px": [1800, 500], "width_m": 1.2},
        ],
        "declared_dimensions": [
            {"a_px": [200, 1400], "b_px": [1800, 1400], "length_m": 8.0},
            {"a_px": [200, 1400], "b_px": [200, 200], "length_m": 6.0},
        ],
    }
    payload["image"]["sha256"] = sha256_file(image_path)
    doc = {
        "schema_id": "floorplan_annotation",
        "schema_version": "1.0.0",
        "artifact_id": "annotation-001",
        "project_id": "demo-project",
        "run_id": "RUN-20260809-demo",
        "created_at": "2026-08-09T10:00:00Z",
        "producer": {"agent": "test", "provider": "local", "model": "deterministic", "effort": "N/A"},
        "inputs": [],
        "content_hash": "sha256:" + "0" * 64,
        "status": "complete",
        "errors": [],
        "payload": payload,
    }
    # GC-4 (OpenAI cross-provider rework review, 2026-08-10): AnnotationSource
    # now recomputes/verifies content_hash, so fixtures must carry a real one
    # instead of the all-zero placeholder.
    doc["content_hash"] = compute_content_hash(doc)
    annotation_path = root / "annotation.json"
    annotation_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return annotation_path, image_path


def _write_dxf_fixture(path: Path, mutate=None) -> None:
    document = ezdxf.new("R2013")
    document.header["$INSUNITS"] = 4
    modelspace = document.modelspace()
    modelspace.add_line((1000, 2000), (9000, 2000), dxfattribs={"layer": "PWA-WALL"})
    modelspace.add_line((9000, 2000), (9000, 8000), dxfattribs={"layer": "PWA-WALL"})
    modelspace.add_line((1000, 8000), (9000, 8000), dxfattribs={"layer": "PWA-WALL"})
    modelspace.add_line((1000, 2000), (1000, 8000), dxfattribs={"layer": "PWA-WALL"})
    modelspace.add_line((6000, 2000), (6000, 8000), dxfattribs={"layer": "PWA-WALL"})
    modelspace.add_lwpolyline(
        [(1000, 2000), (6000, 2000), (6000, 8000), (1000, 8000)],
        dxfattribs={"layer": "PWA-ROOM"},
        close=True,
    )
    modelspace.add_lwpolyline(
        [(6000, 2000), (9000, 2000), (9000, 8000), (6000, 8000)],
        dxfattribs={"layer": "PWA-ROOM"},
        close=True,
    )
    modelspace.add_line((3050, 2000), (3950, 2000), dxfattribs={"layer": "PWA-DOOR"})
    modelspace.add_line((6000, 4550), (6000, 5450), dxfattribs={"layer": "PWA-DOOR"})
    modelspace.add_line((2400, 8000), (3600, 8000), dxfattribs={"layer": "PWA-WINDOW"})
    modelspace.add_line((9000, 5900), (9000, 7100), dxfattribs={"layer": "PWA-WINDOW"})
    if mutate is not None:
        mutate(document)
    document.saveas(path)


def test_annotation_source_extracts_layer_a_fixture(tmp_path):
    annotation_path, _ = _write_annotation_fixture(tmp_path)

    raw = AnnotationSource().extract(annotation_path)

    assert raw.frame.kind == "raster"
    assert raw.frame.unit_scale_m == 0.005
    assert len(raw.walls) == 5
    assert len(raw.rooms) == 2
    assert len(raw.openings) == 4
    assert len(raw.dimensions) == 2


def test_annotation_source_reads_one_raster_snapshot_for_hash_and_dimensions(tmp_path, monkeypatch):
    annotation_path, image_path = _write_annotation_fixture(tmp_path)
    image_ref = image_path.relative_to(tmp_path).as_posix()
    expected_bytes = image_path.read_bytes()
    image_reads = 0
    real_read_bytes = Path.read_bytes

    def counted_read_bytes(path):
        nonlocal image_reads
        if Path(path) == image_path:
            image_reads += 1
        return real_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", counted_read_bytes)

    raw, image_snapshot = AnnotationSource().extract_with_image_snapshot(
        annotation_path,
        source_root=tmp_path,
        source_inventory={image_ref: {"kind": "floorplan", "sha256": sha256_file(image_path)}},
    )

    assert image_reads == 1
    assert image_snapshot == expected_bytes
    assert raw.frame.height_px == 1800


def test_annotation_source_rejects_reparse_image_ref_before_open(tmp_path, monkeypatch):
    source_root = tmp_path / "source-root"
    source_root.mkdir()
    annotation_path, _ = _write_annotation_fixture(source_root)
    outside_root = tmp_path / "outside-root"
    outside_root.mkdir()
    outside_image = outside_root / "outside.png"
    Image.new("RGB", (2000, 1800), "white").save(outside_image, format="PNG")
    linked_root = source_root / "linked"

    if os.name == "nt":
        subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(linked_root), str(outside_root)],
            check=True,
            capture_output=True,
        )
    else:
        linked_root.symlink_to(outside_root, target_is_directory=True)

    document = json.loads(annotation_path.read_text(encoding="utf-8"))
    document["payload"]["image"].update(
        {
            "source_image_ref": "linked/outside.png",
            "sha256": sha256_file(outside_image),
        }
    )
    document["content_hash"] = compute_content_hash(document)
    annotation_path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    real_read_bytes = Path.read_bytes
    opened_linked_image = False

    def guarded_read_bytes(path):
        nonlocal opened_linked_image
        if Path(path) == linked_root / "outside.png":
            opened_linked_image = True
        return real_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)

    try:
        with pytest.raises(ValueError):
            AnnotationSource().extract(
                annotation_path,
                source_root=source_root,
                source_inventory=None,
            )
        assert not opened_linked_image
    finally:
        if linked_root.exists() or linked_root.is_symlink():
            if os.name == "nt":
                linked_root.rmdir()
            else:
                linked_root.unlink()


def test_dxf_source_extracts_layer_a_fixture(tmp_path):
    dxf_path = tmp_path / "layer-a-1.dxf"
    _write_dxf_fixture(dxf_path)

    raw = DxfSource().extract(dxf_path)

    assert raw.frame.kind == "dxf"
    assert raw.frame.source_units == "mm"
    assert len(raw.walls) == 5
    assert len(raw.rooms) == 2
    assert len(raw.openings) == 4


def test_dxf_and_annotation_sources_normalize_to_same_projection(tmp_path):
    annotation_path, _ = _write_annotation_fixture(tmp_path)
    dxf_path = tmp_path / "layer-a-1.dxf"
    _write_dxf_fixture(dxf_path)

    ann = normalize(AnnotationSource().extract(annotation_path))
    dxf = normalize(DxfSource().extract(dxf_path))

    assert canonical_projection(ann) == canonical_projection(dxf)


class _FakeProc:
    def __init__(self, *, wait_error: Exception | None = None):
        self.wait_error = wait_error
        self.killed = False

    def wait(self, timeout: float | None = None) -> int:
        if self.wait_error is not None:
            raise self.wait_error
        return 0

    def kill(self) -> None:
        self.killed = True


def test_dxf_source_maps_worker_timeout_to_parse_timeout(tmp_path, monkeypatch):
    dxf_path = tmp_path / "layer-a-1.dxf"
    _write_dxf_fixture(dxf_path)
    proc = _FakeProc(wait_error=subprocess.TimeoutExpired(cmd="worker", timeout=0.01))

    def fake_run_worker(path: Path):
        raise FloorplanError("PARSE_TIMEOUT", "worker timed out")

    monkeypatch.setattr("pwa.floorplan.dxf_source._run_worker", fake_run_worker, raising=False)

    with pytest.raises(FloorplanError) as exc:
        DxfSource().extract(dxf_path)

    assert exc.value.finding.code == "PARSE_TIMEOUT"


def test_worker_output_channel_is_not_truncated_at_the_stdio_log_cap(tmp_path):
    """M-6 (code review, 2026-08-10): MAX_WORKER_STDIO_BYTES (1 MiB)
    documents the cap on the worker's stdout/stderr log channels, not its
    JSON result payload. A legal, within-limits DXF (e.g. ~12,000 walls)
    produces a worker JSON result comfortably over 1 MiB; applying the
    log-channel cap to that channel silently truncated it and the result
    failed to parse as "malformed JSON" -- an operational CLI 2 for a
    documented-legal input.
    """
    from pwa.floorplan.config import MAX_WORKER_STDIO_BYTES
    from pwa.floorplan.dxf_source import _bounded_text

    payload = {"walls": [{"index": i, "source_ref": f"dxf:Model/PWA-WALL#{i:x}"} for i in range(20_000)]}
    text = json.dumps(payload, ensure_ascii=False)
    assert len(text.encode("utf-8")) > MAX_WORKER_STDIO_BYTES  # sanity: exceeds the old (wrong) cap

    output_path = tmp_path / "worker-output.json"
    output_path.write_text(text, encoding="utf-8")

    # The old cap would silently truncate this and json.loads would raise.
    with pytest.raises(json.JSONDecodeError):
        json.loads(_bounded_text(output_path, MAX_WORKER_STDIO_BYTES))

    # The fixed cap (reused MAX_DXF_BYTES) must round-trip the full payload.
    from pwa.floorplan.config import MAX_DXF_BYTES

    result = json.loads(_bounded_text(output_path, MAX_DXF_BYTES))
    assert len(result["walls"]) == 20_000


@pytest.mark.skipif(os.name != "nt", reason="asserts the Windows taskkill tree-kill path")
def test_dxf_worker_timeout_kills_the_process_tree_not_just_the_child(tmp_path, monkeypatch):
    """M-5 (code review, 2026-08-10): on timeout, the parent used to call
    only proc.kill() (TerminateProcess on Windows), which is not tree-aware
    -- a grandchild the worker spawned would survive. The parent must use an
    OS-level tree-kill mechanism instead.
    """
    dxf_path = tmp_path / "layer-a-1.dxf"
    _write_dxf_fixture(dxf_path)

    class _TimeoutProc:
        pid = 987654

        def __init__(self):
            self._waits = 0

        def wait(self, timeout=None):
            self._waits += 1
            if self._waits == 1:
                raise subprocess.TimeoutExpired(cmd="worker", timeout=timeout or 0)
            return 1

        def kill(self):
            pass

    monkeypatch.setattr("pwa.floorplan.dxf_source.subprocess.Popen", lambda *args, **kwargs: _TimeoutProc())

    tree_kill_calls: list[list[str]] = []

    class _Completed:
        returncode = 0

    def fake_run(cmd, **kwargs):
        tree_kill_calls.append(cmd)
        return _Completed()

    monkeypatch.setattr("pwa.floorplan.dxf_source.subprocess.run", fake_run)

    from pwa.floorplan.dxf_source import _run_worker

    with pytest.raises(FloorplanError) as exc:
        _run_worker(dxf_path)

    assert exc.value.finding.code == "PARSE_TIMEOUT"
    assert tree_kill_calls, "expected an OS-level tree-kill command on timeout, not just proc.kill()"
    assert "taskkill" in tree_kill_calls[0][0].lower()
    assert str(_TimeoutProc.pid) in tree_kill_calls[0]
    assert "/T" in tree_kill_calls[0]
    assert "/F" in tree_kill_calls[0]


def test_dxf_source_rejects_malformed_worker_json(tmp_path, monkeypatch):
    dxf_path = tmp_path / "layer-a-1.dxf"
    _write_dxf_fixture(dxf_path)

    def fake_run_worker(path: Path):
        raise ValueError("worker emitted malformed JSON")

    monkeypatch.setattr("pwa.floorplan.dxf_source._run_worker", fake_run_worker, raising=False)

    with pytest.raises(ValueError, match="worker"):
        DxfSource().extract(dxf_path)


def test_dxf_worker_rejects_unknown_units(tmp_path):
    dxf_path = tmp_path / "units-unknown.dxf"
    document = ezdxf.new("R2013")
    document.header["$INSUNITS"] = 0
    document.modelspace().add_line((0, 0), (1000, 0), dxfattribs={"layer": "PWA-WALL"})
    document.saveas(dxf_path)

    with pytest.raises(ValueError, match="PARSE_UNITS_MISMATCH"):
        extract_dxf(dxf_path)


def test_dxf_worker_flags_arc_on_known_layer_as_unsupported(tmp_path):
    dxf_path = tmp_path / "unsupported-arc.dxf"
    document = ezdxf.new("R2013")
    document.header["$INSUNITS"] = 4
    document.modelspace().add_arc(center=(0, 0), radius=1, start_angle=0, end_angle=90, dxfattribs={"layer": "PWA-WALL"})
    document.saveas(dxf_path)

    payload = extract_dxf(dxf_path)

    assert [item["code"] for item in payload["errors"]] == ["PARSE_UNSUPPORTED_FEATURE"]
    assert payload["walls"] == []


def test_dxf_worker_flags_room_bulge_as_unsupported(tmp_path):
    dxf_path = tmp_path / "unsupported-bulge.dxf"
    document = ezdxf.new("R2013")
    document.header["$INSUNITS"] = 4
    document.modelspace().add_lwpolyline(
        [(0, 0, 0.1), (1000, 0, 0), (1000, 1000, 0)],
        format="xyb",
        dxfattribs={"layer": "PWA-ROOM"},
    )
    document.saveas(dxf_path)

    payload = extract_dxf(dxf_path)

    assert [item["code"] for item in payload["errors"]] == ["PARSE_UNSUPPORTED_FEATURE"]
    assert payload["rooms"] == []


def test_dxf_worker_enforces_entity_limit(tmp_path, monkeypatch):
    dxf_path = tmp_path / "limit-entities.dxf"
    document = ezdxf.new("R2013")
    document.header["$INSUNITS"] = 4
    modelspace = document.modelspace()
    modelspace.add_line((0, 0), (1000, 0), dxfattribs={"layer": "PWA-WALL"})
    modelspace.add_line((0, 1000), (1000, 1000), dxfattribs={"layer": "PWA-WALL"})
    document.saveas(dxf_path)
    monkeypatch.setattr("pwa.floorplan.dxf_worker.MAX_DXF_ENTITIES", 1)

    with pytest.raises(ValueError, match="PARSE_RESOURCE_LIMIT"):
        extract_dxf(dxf_path)


def test_dxf_worker_records_unmapped_source_entities(tmp_path):
    dxf_path = tmp_path / "unmapped-layer.dxf"
    document = ezdxf.new("R2013")
    document.header["$INSUNITS"] = 4
    document.modelspace().add_line((0, 0), (1000, 0), dxfattribs={"layer": "NOTES-UNMAPPED"})
    document.saveas(dxf_path)

    payload = extract_dxf(dxf_path)

    assert payload["unmapped"][0]["code"] == "PARSE_UNMAPPED_SOURCE_ENTITY"
    assert "NOTES-UNMAPPED" not in json.dumps(payload["unmapped"])
    assert "unknown-layer-0001" in payload["unmapped"][0]["source_ref"]
