"""Source selection primitives for floorplan adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pwa.floorplan.types import RawGeometry


class FloorplanSource(Protocol):
    def accepts(self, path: Path) -> bool:
        ...

    def extract(self, path: Path) -> RawGeometry:
        ...
