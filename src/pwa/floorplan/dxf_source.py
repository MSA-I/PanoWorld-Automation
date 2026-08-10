"""Bounded DXF source adapter with a subprocess worker boundary."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

from pwa.floorplan.config import MAX_DXF_BYTES, MAX_WORKER_STDIO_BYTES, PARSER_TIMEOUT_S
from pwa.floorplan.findings import Finding, FloorplanError
from pwa.floorplan.types import RawDimension, RawGeometry, RawOpening, RawRoom, RawWall, SourceFrame


def _bounded_text(path: Path, limit: int) -> str:
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        data = data[:limit]
    return data.decode("utf-8", errors="replace")


def _worker_command(path: Path, output_path: Path) -> list[str]:
    return [sys.executable, "-m", "pwa.floorplan.dxf_worker", str(path), str(output_path)]


def _kill_process_tree(proc: subprocess.Popen) -> None:
    """Kill the worker and any children it may have spawned.

    §12: "the worker is forbidden to spawn children; the parent uses
    OS-specific stdlib/process-group termination to kill the worker tree on
    timeout". `proc.kill()` alone only terminates the direct child handle;
    on Windows that is `TerminateProcess`, which is not tree-aware.
    """
    if os.name == "nt":
        result = subprocess.run(
            ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode != 0:
            proc.kill()
    else:
        # start_new_session=True below makes the worker's pid its own
        # process group id, so killing that group reaches any children.
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, OSError):
            proc.kill()
    proc.wait()


def _run_worker(path: Path) -> dict:
    if path.stat().st_size > MAX_DXF_BYTES:
        raise FloorplanError("PARSE_RESOURCE_LIMIT", "DXF exceeds byte limit", source_ref=str(path.name))

    with tempfile.TemporaryDirectory(prefix="pwa-floorplan-dxf-", ignore_cleanup_errors=True) as temp_dir:
        temp_root = Path(temp_dir)
        output_path = temp_root / "worker-output.json"
        stdout_path = temp_root / "worker.stdout.txt"
        stderr_path = temp_root / "worker.stderr.txt"
        with stdout_path.open("xb") as stdout_stream, stderr_path.open("xb") as stderr_stream:
            repo_root = Path(__file__).resolve().parents[3]
            src_root = repo_root / "src"
            env = os.environ.copy()
            pythonpath_parts = [str(src_root)]
            if env.get("PYTHONPATH"):
                pythonpath_parts.append(env["PYTHONPATH"])
            env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
            kwargs: dict[str, object] = {
                "stdin": subprocess.DEVNULL,
                "stdout": stdout_stream,
                "stderr": stderr_stream,
                "cwd": str(repo_root),
                "env": env,
            }
            if os.name == "nt":
                kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(
                    subprocess, "CREATE_NO_WINDOW", 0
                )
            else:
                kwargs["start_new_session"] = True
            proc = subprocess.Popen(_worker_command(path, output_path), **kwargs)
            try:
                exit_code = proc.wait(timeout=PARSER_TIMEOUT_S)
            except subprocess.TimeoutExpired as exc:
                _kill_process_tree(proc)
                raise FloorplanError("PARSE_TIMEOUT", "DXF worker timed out", source_ref=path.name) from exc
        if exit_code != 0:
            stderr_text = _bounded_text(stderr_path, MAX_WORKER_STDIO_BYTES).strip()
            raise ValueError(f"worker failed: {stderr_text or f'exit {exit_code}'}")
        if not output_path.exists():
            raise ValueError("worker emitted no output")
        try:
            # M-6 (code review, 2026-08-10): MAX_WORKER_STDIO_BYTES (1 MiB)
            # documents the cap on the worker's stdout/stderr *log* channels
            # (used just above for stderr_path), not its JSON *result*
            # payload. Applying the log-channel cap here silently truncated
            # legal, within-MAX_WALLS/MAX_DXF_ENTITIES results (e.g. ~12,000
            # walls -> ~1.2 MB JSON), which then failed as "malformed JSON"
            # instead of parsing successfully. Reuse the existing
            # MAX_DXF_BYTES bound (already the accepted worst-case size for
            # this pipeline) for the result channel instead of introducing a
            # new named constant.
            return json.loads(_bounded_text(output_path, MAX_DXF_BYTES))
        except json.JSONDecodeError as exc:
            raise ValueError("worker emitted malformed JSON") from exc


class DxfSource:
    def accepts(self, path: Path) -> bool:
        return path.suffix.lower() == ".dxf"

    def extract(self, path: Path) -> RawGeometry:
        try:
            payload = _run_worker(Path(path))
        except FloorplanError:
            raise
        except ValueError:
            raise
        if "fatal_error_code" in payload:
            raise FloorplanError(str(payload["fatal_error_code"]), str(payload.get("message") or payload["fatal_error_code"]), source_ref=Path(path).name)
        return RawGeometry(
            frame=SourceFrame(**payload["frame"]),
            walls=tuple(
                RawWall(item["index"], item["source_ref"], tuple(item["start"]), tuple(item["end"]))
                for item in payload["walls"]
            ),
            rooms=tuple(
                RawRoom(item["index"], item["source_ref"], tuple(tuple(point) for point in item["polygon"]))
                for item in payload["rooms"]
            ),
            openings=tuple(
                RawOpening(
                    item["index"],
                    item["source_ref"],
                    item["kind"],
                    tuple(item["center"]),
                    item["width_m"],
                    tuple(tuple(point) for point in item["span"]),
                    None,
                )
                for item in payload["openings"]
            ),
            dimensions=tuple(
                RawDimension(item["index"], item["source_ref"], tuple(item["a"]), tuple(item["b"]), item["declared_length_m"])
                for item in payload["dimensions"]
            ),
            scanned_entities=payload["scanned_entities"],
            unmapped=tuple(Finding(**item) for item in payload["unmapped"]),
            errors=tuple(Finding(**item) for item in payload.get("errors", [])),
        )
