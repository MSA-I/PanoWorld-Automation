# samples

Input material downloaded for future PLAN work. **Not** part of any approved
fixture set yet — adopting anything here as a project fixture is a PLAN decision,
not something an agent may do on its own.

## Status: parked on purpose

Moshe decided on 2026-08-10 that this plan is **not to be run through the pipeline
yet**. The outstanding PLAN-002 review findings get fixed first — there is no
value in exercising a real floorplan against code we already know has a
containment hole in it.

The ordered roadmap lives in `PROJECT-STATE.yaml` under `next_actions` (NA-1
through NA-5) on branch `panoworld-dev/t_b7ade39e-p1-02-floorplan-parsing`.
Annotating this file is **NA-5**, the last step, and it is blocked until the
fixes, the re-review and Moshe's overlay approval are all done.

If you are an agent reading this: do not annotate or parse this file because it
looks like the obvious next task. Check `next_actions` first.

## Sample_Floorplan.jpg

| | |
|---|---|
| Source | https://commons.wikimedia.org/wiki/File:Sample_Floorplan.jpg |
| Direct file | https://upload.wikimedia.org/wikipedia/commons/9/9a/Sample_Floorplan.jpg |
| Author | Boereck (Wikimedia Commons, uploaded 2006-03-21) |
| License | **Public domain** — released worldwide by the creator with no restrictions |
| Format | JPEG, 842 × 569 px, RGB |
| Size | 235,297 bytes |
| SHA-256 | `917A5753FECEB65F8401381894BFB0809BD43194879002D2AA2ACB74EE80DF08` |
| Downloaded | 2026-08-10, at Moshe's explicit request |

Public domain, so it carries no attribution or share-alike obligation and does not
add to the open D-010 licensing risk. It is also not private or sensitive, so the
PLAN-002 §13 Layer B rights/sensitivity attestation does not apply.

### What this file can and cannot do today

It is a **raster** image. PLAN-002 Part 1 has no OCR and no learned raster parser
(§3 non-goals). Nothing in the current pipeline can turn this picture into
geometry on its own.

To parse it, someone must first produce a `floorplan_annotation` 1.0.0 JSON that
lists, in **pixel** coordinates: every wall endpoint, every room polygon, every
door/window centre and width, plus `scale_m_per_px`. The annotation adapter then
converts that to metres. That marking-up step is manual in Part 1 by design.

The image carries 7 EXIF tags. The OpenAI rework review flagged that the raster
overlay embeds source bytes verbatim, so EXIF would be copied into
`parse/overlay.svg`. That is an open finding against §12 and applies to this file.

### Notes on the drawing itself

Roughly eight labelled spaces, mostly axis-aligned walls, with one angled bay at
the upper left. It also contains furniture symbols, stair treads, compass rose and
text labels, none of which the Part 1 contract represents — an annotator ignores
them. There is no scale bar, so `scale_m_per_px` has to come from a known real
dimension or from the project manifest.
