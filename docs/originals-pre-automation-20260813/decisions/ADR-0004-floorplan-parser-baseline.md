# ADR-0004 — Part 1 floorplan parser baseline and source conventions

- Status: ACCEPTED (Moshe, 2026-08-09, explicit PLAN-002 approval; resolves D-004)
- Context: PLAN-002 must establish a deterministic, local and reviewable G1 path without selecting an unverified raster ML stack, adding dependencies, using a third-party dataset, or accessing remote/GPU infrastructure.
- Decision:
  1. Part 1 uses a contract-first baseline with schema-validated manual raster annotation and a deliberately narrow DXF adapter. Production raster parsing remains a later decision after labeled Layer B evidence exists.
  2. DXF accepts only 2D modelspace geometry at zero elevation: `LINE` on `PWA-WALL`, closed zero-bulge `LWPOLYLINE` on `PWA-ROOM`, and `LINE` on `PWA-DOOR`/`PWA-WINDOW`. Layer matching is exact and case-sensitive; unsupported source semantics fail loudly and external references are never resolved.
  3. Both adapters normalize into the canonical geometry projection and must agree on the tracked Layer A fixture while retaining adapter-specific confidence and provenance.
  4. A source-aligned, self-contained deterministic SVG overlay is mandatory for complete/partial output. Raster overlays embed the verified source image; DXF overlays render source primitives and normalized detections in aligned coordinates. No scripts, external URLs or arbitrary filesystem references are permitted.
  5. Private Layer B input may be used only after Moshe attests rights and non-sensitivity. Git may receive only redacted hashes/counts/metrics; unlabeled smoke data is not accuracy evidence.
- Consequences: the Part 1 pipeline proves contracts, geometry invariants, traceability and G1 evidence but does not claim scalable automatic raster parsing or production accuracy. Many real DXF files will be rejected by design. OCR, learned parsing, curves, blocks, xrefs and robust overlap-area analysis remain deferred.
- Evidence: `docs/plans/PLAN-002-floorplan-parsing.md` sections 4, 6, 10, 13 and 20; Kanban task `t_b7ade39e` approval comment dated 2026-08-09.
