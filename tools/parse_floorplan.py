"""Thin shim for `python -m pwa.floorplan.cli`."""

from __future__ import annotations

from pwa.floorplan.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
