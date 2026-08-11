<!-- Amendment 1 to the approved post-approval spatial brief. The brief itself
     (evidence/PLAN-002/design/post-approval-spatial-brief-2026-08-09.md) is an approved
     append-only record and is NOT edited; this file amends it by reference, which is the only
     way to change it. Routed by the orchestrator after the NA-3g implementer correctly declined
     to edit the brief in place, and extended with the four additions the NA-3h reviewer required
     before it would consider the amendment complete. Repository-relative paths only. -->

# Amendment 1 to the post-approval spatial brief — residual finalization state

Amends: `evidence/PLAN-002/design/post-approval-spatial-brief-2026-08-09.md`, section 11.4
(the `overlay_omitted_reason` vocabulary).

Origin: NA-3g's Fix 1 moved the "a finalized directory was left behind" signal out of
`overlay_omitted_reason`, which describes overlay omission, into its own diagnostic field. The
implementer proposed the amendment text and correctly did not apply it. The NA-3h reviewer judged
the proposed text "right in substance" but "incomplete on four points" and would not route it as
written. All four additions are folded in below.

## 1. `overlay_omitted_reason` keeps its closed vocabulary, and it is load-bearing again

`overlay_omitted_reason` remains limited to exactly:

    "no_normalized_geometry" | "overlay_exceeds_max_bytes" | "source_raster_exceeds_limits"

Section 11.4's sentence that this field is **never produced for operational failures** is restated
here deliberately, not merely implied: it was violated between NA-3e and NA-3g, when the
rollback double-fault borrowed this field to report filesystem state, and it is true again. Treat
it as load-bearing.

## 2. Residual filesystem state has its own field, with its own closed vocabulary

A failure to roll a finalized run directory back to staging is recorded as:

    residual_state: "finalized_directory_left_behind"

The vocabulary of `residual_state` is closed, and today it contains exactly that one value.
Closing it now is the point of the amendment: introducing a second open vocabulary would repeat the
mistake that made Fix 1 necessary.

## 3. Where the field actually lives — the carrier, named

`residual_state` is carried by the **in-memory diagnostic** returned from `parse_run()` and is
emitted by `src/pwa/floorplan/cli.py` to **stderr** on exit 2. On the current code it is **never
written to `parse/parse-report.json`**, and the reason is structural rather than incidental: the
field is set only for `FinalizedRunLeftBehindError`, and that error by construction means the
staging directory no longer exists, so the guard that writes a staged report cannot fire.

This is stated explicitly because an amendment that said only "recorded at the top level" would
send a future reader looking for the field on disk and let them conclude the code is broken when it
is not.

## 4. The retained staging report is replaced, and why

After a **successful** rollback, the retained staging directory keeps the happy-path
`parse/parse-report.json`, whose `"outcome": "complete"` is no longer true. That report is therefore
replaced by the operational-failure report. The replacement is prepared as an exclusively-created
transient sibling and renamed over the stale file atomically, so exclusive creation still governs
the new bytes while a retained staging directory can no longer claim success for a run that failed.

## 5. The transient sibling, and when an operator will find it

The sibling is named:

    parse/parse-report.operational-failure.tmp

On the normal path it does not survive — the atomic rename consumes it. **If the atomic replacement
itself fails, the sibling remains inside the retained staging directory**, and it contains the
truthful operational-failure report while `parse-report.json` still contains the stale `complete`
claim. An operator who finds that file has found evidence, not corruption, and this record exists so
they read it that way.

That condition is the residual the NA-3h review recorded as W-1 and explicitly accepted: it needs
two independent filesystem failures, it cannot make `parse_run()` raise, and its worst case
degrades to the pre-NA-3g state plus a file containing the correct information.

## Status

`REVIEW` — routed by the orchestrator, incorporating the NA-3h reviewer's four required additions.
Nothing here retracts the implementer's proposed wording; it extends it. The brief it amends is
untouched.
