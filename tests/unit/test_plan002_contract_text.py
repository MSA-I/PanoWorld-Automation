from __future__ import annotations

from tests.conftest import REPO_ROOT


def _normalized(text: str) -> str:
    return " ".join(text.split())


def test_plan002_contains_approved_gc3_8_blockquoted_replacements():
    plan = _normalized(
        (REPO_ROOT / "docs" / "plans" / "PLAN-002-floorplan-parsing.md").read_text(encoding="utf-8")
    )
    section_five_replacement = _normalized(
        """
        The new `project/project_manifest.json` is schema `project_manifest` 1.1.0, declares contracts
        bundle 1.2.0, carries the new parse-run ID and artifact ID, and contains the complete copied
        inventory with reverified hashes. The source manifest remains byte-unchanged at its originally
        declared schema and bundle versions.
        """
    )
    section_six_replacement = _normalized(
        """
        An annotation selects exactly one source image through its sole `payload.image.source_image_ref`.
        Selection is exact, code-point-for-code-point string equality, after JSON decoding, with one
        `payload.inputs[].path` in the validated source manifest. No case folding, slash conversion,
        Unicode normalization, filesystem alias resolution, path-prefix inference or `derived_from`
        inference participates in selection.

        Source-manifest preflight must first require unique inventory path strings. Duplicate paths are
        an invalid source contract and fail with CLI 2 and no finalized derived run; they are not an
        annotation "multiple match."

        The selected entry must have `kind: "floorplan"` and decode as PNG or JPEG, or have
        `kind: "floorplan_page"` and decode as PNG. Raw PDF, CAD source bytes, CAD previews,
        `style_reference`, `other`, and all other formats are not annotatable. A missing reference, a
        disallowed kind, or an incompatible decoded format produces `PARSE_SOURCE_UNSUPPORTED`, CLI 2,
        and no finalized derived run.

        `floorplan_page` is a producer-contract token reserved exclusively for PNG page renders created
        by the approved intake PDF renderer from the same run's unique `kind: "floorplan"` PDF input. It
        must not be assigned to uploaded rasters, style references, DXF/DWG previews, generic
        derivatives or any other artifact.

        The parser treats the validated manifest classification as authoritative; it does not
        authenticate that classification from the path. `content_hash` is not an authenticity mechanism.
        An actor able to rewrite a source run and recompute its hashes can misclassify arbitrary PNG
        inventory entries, and `floorplan_page` increases how many such entries one forged manifest can
        expose. This is an explicit residual source-run trust-boundary limitation, not a property
        claimed to be prevented by this amendment.
        """
    )

    assert section_five_replacement in plan
    assert section_six_replacement in plan
