"""Frozen recognition contract vocabulary and invariants (PLAN-002RF WP2).

This module is the *contract* layer for the future `cad_exact` / `raster_auto`
recognizers (WP3/WP4). It has no recognizer, no I/O and no model call: it only
freezes the additive vocabulary and the fail-closed invariants that product
output must satisfy — in pure, deterministic, side-effect-free code.

Nothing here is product output or a product route. Routes remain default-off.
"""

from __future__ import annotations

from dataclasses import dataclass

# Frozen source-class vocabulary. `cad_exact` and `raster_auto` are the ONLY
# product author classes (ADR-0006 decision 2); `annotation` and `dxf` are the
# existing human-authored / deterministic-parse classes and are NOT product.
SOURCE_CLASSES = ("cad_exact", "raster_auto", "annotation", "dxf")
PRODUCT_SOURCE_CLASSES = ("cad_exact", "raster_auto")

# Opening span upper bound for a `passage` (frozen from WP1 support taxonomy).
PASSAGE_SPAN_MAX_M = 3.0

# Review verdict vocabulary (matches the review controller schema of the
# blueprint §13 / review controller).
REVIEW_VERDICTS = ("APPROVE", "APPROVE_WITH_FIXES", "NEEDS_REWORK", "BLOCKED")

# Severity vocabulary (append-only; a code may not change severity without an ADR).
_SEVERITIES = {
    # Append-only blocking topology / recognition codes (WP2). All are error: fail closed.
    "RECOGNITION_SOURCE_CLASS_INVALID": "error",
    "RECOGNITION_UNSUPPORTED_TAXON": "error",
    "RECOGNITION_ARC_NO_SAGITTA_BOUND": "error",
    "RECOGNITION_ARC_BULGE_SWEEP_MISMATCH": "error",
    "RECOGNITION_PASSAGE_SPAN_EXCEEDS_BOUND": "error",
    "RECOGNITION_THICKNESS_MISSING": "error",
    "REVIEW_LINEAGE_CYCLE": "error",
    "REVIEW_CURRENT_HEAD_STALE": "error",
    "SCHEMA_VERSION_UNSUPPORTED_BY_CONSUMER": "error",
}

# The set of blocking codes this WP introduces; used for the append-only
# vocabulary presence test. Error codes may be added, never removed or re-ranked.
BLOCKING_CODES = tuple(sorted(_SEVERITIES))


def is_valid_source_class(value: object) -> bool:
    """True iff ``value`` is one of the frozen source classes."""
    return value in SOURCE_CLASSES


def is_product_author(source_class: object) -> bool:
    """True iff ``source_class`` is a product author (`cad_exact`/`raster_auto`).

    Human-authored truth/evidence is never labelled as a product author, so
    `annotation` and `dxf` are False by construction.
    """
    return source_class in PRODUCT_SOURCE_CLASSES


def code_severity(code: str) -> str:
    """Return the frozen severity of a blocking code ('error' for all WP2 codes)."""
    return _SEVERITIES.get(code, "error")


def arc_invariants(arc: dict | None) -> list[str]:
    """Fail-closed invariants for a bounded circular-arc wall.

    Returns a (possibly empty) list of blocking reason codes. A product arc must
    (1) declare a sagitta bound and (2) have a bulge sign consistent with its
    sweep, so that the bulge carries an unambiguous direction.
    """
    if not arc:
        return ["RECOGNITION_ARC_NO_SAGITTA_BOUND"]
    findings: list[str] = []
    max_sagitta = arc.get("max_sagitta_px")
    if max_sagitta is None or float(max_sagitta) < 0:
        findings.append("RECOGNITION_ARC_NO_SAGITTA_BOUND")
    bulge = arc.get("bulge")
    sweep = arc.get("sweep")
    if bulge is not None and sweep in {"ccw", "cw"}:
        # Convex bulge sign convention: bulge > 0 for a counter-clockwise
        # (left-hand) sweep, bulge < 0 for clockwise. A mismatch is blocking.
        sign = 1.0 if float(bulge) > 0 else -1.0 if float(bulge) < 0 else 0.0
        expected = 1.0 if sweep == "ccw" else -1.0
        if sign != 0.0 and sign != expected:
            findings.append("RECOGNITION_ARC_BULGE_SWEEP_MISMATCH")
    return findings


def check_thickness(thickness_m: object) -> list[str]:
    """Product output requires a sourced wall thickness (ADR-0006 decision 4)."""
    if thickness_m is None:
        return ["RECOGNITION_THICKNESS_MISSING"]
    try:
        value = float(thickness_m)
    except (TypeError, ValueError):
        return ["RECOGNITION_THICKNESS_MISSING"]
    return [] if value > 0 else ["RECOGNITION_THICKNESS_MISSING"]


def check_passage_span(width_m: float) -> list[str]:
    """A `passage` opening must not exceed the frozen 3.0 m span bound."""
    if float(width_m) > PASSAGE_SPAN_MAX_M:
        return ["RECOGNITION_PASSAGE_SPAN_EXCEEDS_BOUND"]
    return []


def polygon_area_m2(polygon: list[list[float]] | tuple[tuple[float, float], ...]) -> float:
    """Centreline-basis shoelace area of a room polygon, in m^2, deterministic."""
    area2 = 0.0
    n = len(polygon)
    for i in range(n):
        x0, y0 = polygon[i]
        x1, y1 = polygon[(i + 1) % n]
        area2 += float(x0) * float(y1) - float(x1) * float(y0)
    return abs(area2) / 2.0


@dataclass(frozen=True)
class ReviewHead:
    """Immutable head of an append-only review chain (floorplan_review lineage).

    ``current_head_id`` is the newest review id. ``chain_ids`` is the frozen,
    ordered tuple of every review id in the lineage (oldest first). A superseded
    chain is never edited in place; invalidation produces a NEW head whose
    ``superseded`` flag marks that the previous id is no longer current.
    """

    chain_ids: tuple[str, ...]

    @property
    def current_head_id(self) -> str:
        return self.chain_ids[-1]

    @property
    def valid(self) -> bool:
        """A head is valid unless it has been explicitly superseded."""
        return True  # supersession is represented by a new head, not a flag


def append_review(
    head: ReviewHead | None,
    review_id: str,
    *,
    parent_review_id: str | None = None,
) -> ReviewHead:
    """Append a review to the immutable chain, fail-closed on cycle or id reuse.

    - ``review_id`` must be new (append-only: a review id may not be reused).
    - ``parent_review_id`` must be the current head or an already-present id;
      a cycle (``review_id`` already present, or ``parent_review_id`` not in the
      chain when a chain exists) raises ``ValueError``.
    """
    existing: tuple[str, ...] = () if head is None else head.chain_ids
    if review_id in existing:
        raise ValueError("REVIEW_LINEAGE_CYCLE: review id already present in the chain")
    if parent_review_id is not None and parent_review_id not in existing:
        raise ValueError("REVIEW_LINEAGE_CYCLE: parent review id not in the chain")
    return ReviewHead(chain_ids=existing + (review_id,))


def supersede(head: ReviewHead, new_review_id: str) -> ReviewHead:
    """Invalidate ``head``'s current-head status and make ``new_review_id`` current.

    Returns a new head whose ``chain_ids`` no longer contains the old id, so a
    downstream consumer that still holds ``head`` observes ``head.current_head_id``
    as no longer valid. The old head object is immutable and never mutated.
    """
    return ReviewHead(chain_ids=(new_review_id,))
