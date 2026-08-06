"""CLI for the PanoWorld package validator.

Repository invocation (package=false):
``uv run python tools/validate_package.py <scene-dir>``.

Config-dependent checks are enabled via flags instead of a YAML config file so
the locked dependency set stays PyYAML-free (PLAN-000 C8):

    pwa-validate <scene-dir> [--start-image NAME] [--pano-image-name NAME]
                 [--max-views N] [--json]

Exit codes: 0 = valid (warnings allowed), 1 = errors found, 2 = usage/IO error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pwa.validator.package_validator import PackageValidator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pwa-validate", description=__doc__)
    parser.add_argument("scene_dir", type=Path)
    parser.add_argument("--start-image", default=None)
    parser.add_argument("--pano-image-name", default=None)
    parser.add_argument("--max-views", type=int, default=None)
    parser.add_argument("--json", action="store_true", help="emit the full report as JSON")
    args = parser.parse_args(argv)

    if not args.scene_dir.is_dir():
        print(f"error: scene dir not found: {args.scene_dir}", file=sys.stderr)
        return 2

    report = PackageValidator(
        args.scene_dir,
        start_image=args.start_image,
        pano_image_name=args.pano_image_name,
        max_views=args.max_views,
    ).validate()

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        for f in report.errors:
            print(f"ERROR {f['code']}: {f['path']}: {f['message']}")
        for f in report.warnings:
            print(f"WARN  {f['code']}: {f['path']}: {f['message']}")
        print(
            f"{report.scene}: {len(report.errors)} error(s), "
            f"{len(report.warnings)} warning(s) [{report.mode}]"
        )
    return 0 if report.ok() else 1


if __name__ == "__main__":
    raise SystemExit(main())
