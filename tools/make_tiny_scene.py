"""CLI wrapper for the Layer-A tiny-scene factory: python tools/make_tiny_scene.py <dest>."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # package=false: no install

from pwa.fixtures import make_tiny_scene  # noqa: E402

if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    scene = make_tiny_scene(dest)
    print(f"tiny scene created at: {scene}")
