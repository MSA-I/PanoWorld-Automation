"""Small immutable-file helpers shared by PLAN-001 intake and packaging."""
from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path


def is_link_or_reparse(path: Path) -> bool:
    info = path.lstat()
    return path.is_symlink() or bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def copy_immutable(source: Path, destination: Path) -> str:
    source = Path(source)
    if not source.is_file() or is_link_or_reparse(source):
        raise ValueError("input must be a regular file, not a link or reparse point")
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with source.open("rb") as src, destination.open("xb") as dst:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            digest.update(chunk)
            dst.write(chunk)
        dst.flush()
        os.fsync(dst.fileno())
    result = "sha256:" + digest.hexdigest()
    if sha256_file(destination) != result:
        raise OSError("copied file hash mismatch")
    return result


def write_json_exclusive(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(document, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
