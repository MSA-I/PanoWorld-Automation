# Package validator — error-code vocabulary (locked, PLAN-000 T8)

Severity: `error` fails validation (exit code 1); `warn` is reported but does not fail.
Codes are append-only; meaning/severity changes require an ADR. Consumers match on
codes, never on message text. Test-case numbers refer to the 15 failure-injection
cases (test-architect §3, as amended by plan-reviewer M-4 and missed-risk 1).

| Code | Severity | Meaning | Test case |
|---|---|---|---|
| `MISSING_VIEWPOINTS_DIR` | error | `viewpoints/` is not a sibling directory of the map JSON | — |
| `NO_MAP_FILE` | error | No `map*.json` found in the scene root | — |
| `MAP_JSON_INVALID` | error | Map file is not valid JSON, or root is not an object of string→array-of-strings | 14 |
| `DUPLICATE_MAP_KEY` | error | The same key appears twice **within one** map file (intra-map only; the same key in *different* map files is legitimate, as in upstream scene0000) | 15 |
| `DUPLICATE_VIEWPOINT_IN_MAP` | warn | The same viewpoint appears more than once in one map's traversal (as key and/or value) — it would be generated twice (panoworld-compat implication) | — |
| `EMPTY_MAP_VALUES` | error | The first (start) key of a map has an empty values array | — |
| `MAP_REFERENCES_UNKNOWN_VIEWPOINT` | error | A map key or value has no matching `viewpoints/<name>/` directory | 6 |
| `VIEWPOINT_NOT_IN_MAP` | warn | A viewpoint directory exists on disk but is referenced by no map (upstream demo legitimately has such spares: 0019/0021) | 7 |
| `MISSING_REQUIRED_FILE` | error | A mapped viewpoint lacks one of the 4 required files | 1, 11 |
| `EMPTY_FILE` | error | A required file exists but is zero bytes / truncated-empty | 13 |
| `INVALID_FILENAME` | error | Windows-hostile name: reserved device name (CON, NUL, COM1…), or trailing dot/space (NTFS cannot round-trip these; redefined for Windows per reviewer missed-risk 1) | 12 |
| `MATRIX_PARSE_ERROR` | error | `extrinsics.txt` is not parseable as a whitespace-separated float matrix | 4 |
| `INVALID_MATRIX_SHAPE` | error | Parsed matrix is not 4x4 | 2 |
| `MATRIX_NOT_INVERTIBLE` | error | Matrix is numerically singular (abs(det) < 1e-9) | 3 |
| `MATRIX_LAST_ROW_INVALID` | error | Bottom row is not `[0,0,0,1]` (tol 1e-6) | — |
| `MATRIX_NOT_ORTHONORMAL` | error | Rotation block fails RᵀR≈I (tol 1e-4) | — |
| `MATRIX_NOT_RIGHT_HANDED` | error | det(R) ≉ +1 | — |
| `NONSTANDARD_WORLD_CONVENTION` | warn | R[:,1] ≉ (0,0,−1): scene is not Z-up like the demo data (the code is convention-agnostic; the control models may not be) | — |
| `CAMERA_HEIGHT_OUTLIER` | warn | Camera height (t[2] under standard convention) outside [0.5, 3.0] m | — |
| `CAMERA_POSITION_OUTLIER` | warn | ‖t‖ > 50 m | — |
| `VIEWPOINTS_TOO_CLOSE` | warn | Two viewpoints closer than 0.2 m | — |
| `IMAGE_UNREADABLE` | error | PIL cannot open a required image | — |
| `INVALID_IMAGE_MODE` | error | `place_image.png` not RGB, or `place_depth.png` not single-channel 16-bit (mode I / I;16) | 8 |
| `INVALID_ASPECT_RATIO` | error | Image width/height ≠ 2 exactly (upstream hard-rejects; exact float compare) | — |
| `ODD_DIMENSIONS` | warn | Image dimension not even (patch alignment is 2) | — |
| `DEPTH_RGB_DIMENSION_MISMATCH` | error | `place_depth.png` dimensions differ from `place_image.png` | 5 |
| `DEPTH_MOSTLY_INVALID` | error | More than 50% of depth pixels are 0 (invalid/no-hit), including all-zero | — |
| `INVALID_DEPTH_SCALE` | error | `place_depth_scale.txt` is non-numeric, NaN/inf, zero or negative (upstream raises on ≤0; depth_m = pixel ÷ scale) | 9, 10 |
| `DEPTH_RANGE_IMPLAUSIBLE` | warn | max(depth)/scale outside (0.05, 50) m or median outside (0.1, 30) m — cheapest guard against the divide/multiply inversion | — |
| `DEPTH_SCALE_SATURATED` | warn | More than 1% of valid depth pixels plateau at 65535 — the scale likely clips the true max range. (A single pixel at 65535 is legitimate: upstream normalizes so the farthest pixel hits the ceiling — verified on scene0000) | — |
| `START_IMAGE_MISSING` | error (config mode) | The start viewpoint (first key of a map) lacks the configured `panoworld_start_image` file | — |
| `PANO_NAME_COLLISION` | error (config mode) | Configured `pano_image_name` collides with an existing input file (inference writes outputs back into viewpoint dirs) | — |
| `VIEWPOINT_BUDGET_EXCEEDED` | error (config mode) | A map's total traversal node count exceeds `max_views` (mirrors verified `viewpoint_max_view`, default 8) | — |
| `VRAM_BUDGET_WARNING` | warn | Width ≥ 2048 with ≥ 12 total traversal nodes — the local guide's memory table says 12 views @ 2048 OOMs an H200. Warn-only: the table is not primary-source-verified (reviewer missed-risk 3) | — |
## Floorplan parser ג€” append-only `PARSE_*` vocabulary (PLAN-002)

| Code | Severity | Meaning |
|---|---|---|
| `PARSE_SOURCE_UNSUPPORTED` | error | Input is not accepted by any PLAN-002 adapter or annotation contract validation failed before parse. |
| `PARSE_SOURCE_HASH_MISMATCH` | error | Verified source bytes do not match the recorded immutable hash. |
| `PARSE_UNITS_MISMATCH` | error | DXF `$INSUNITS` is unsupported or contradicts the source manifest units. |
| `PARSE_UNSUPPORTED_FEATURE` | error | The DXF uses semantics outside the approved narrow `PWA-*` convention. |
| `PARSE_SCALE_UNKNOWN` | error | Source scale is missing or contradictory after a complete/blocker-free preflight. |
| `PARSE_EMPTY_GEOMETRY` | error | The parse path yielded no usable walls or rooms after the required stage. |
| `PARSE_OPEN_POLYGON` | error | A room polygon is open or too short after canonical closing rules. |
| `PARSE_SELF_INTERSECTING_POLYGON` | error | A room polygon is zero-area, repeated-vertex, or self-crossing. |
| `PARSE_DEGENERATE_WALL` | error | A wall is shorter than the minimum allowed metric length. |
| `PARSE_DUPLICATE_ENTITY` | error | Canonical geometry collided within one run; no suffix or merge is allowed. |
| `PARSE_UNKNOWN_WALL_REF` | error | An opening references or resolves to no wall. |
| `PARSE_AMBIGUOUS_WALL_REF` | error | An opening resolves to more than one wall candidate. |
| `PARSE_OPENING_OFF_WALL` | error | An opening contradicts its declared wall or lies outside the allowed offset. |
| `PARSE_OPENING_WIDTH_EXCEEDS_WALL` | error | Opening span does not fit within its wall under the approved slack rule. |
| `PARSE_DIMENSION_INCONSISTENT` | error | Declared dimension differs from measured geometry beyond tolerance. |
| `PARSE_RESOURCE_LIMIT` | error | A configured byte/count/pixel/overlay/resource bound was exceeded. |
| `PARSE_TIMEOUT` | error | DXF parsing exceeded the bounded timeout. |
| `PARSE_LOW_CONFIDENCE` | warn | At least one normalized entity fell below the low-confidence threshold. |
| `PARSE_UNMAPPED_SOURCE_ENTITY` | warn | A source entity was recorded and ignored because its layer was unmapped. |
| `PARSE_ROOM_BOUNDARY_UNMATCHED` | warn | Two room boundaries properly cross; Part 1 flags it but stays fail-open under warning semantics. |

## Floorplan recognition / review — append-only blocking vocabulary (WP2)

These codes are append-only and all `error` (fail-closed). A code may be added but
never removed or re-ranked; changing a meaning or severity requires an ADR.
Consumers match on codes, never on message text.

| Code | Severity | Meaning |
|---|---|---|
| `RECOGNITION_SOURCE_CLASS_INVALID` | error | `source_class` is not one of `cad_exact` / `raster_auto` / `annotation` / `dxf`. |
| `RECOGNITION_UNSUPPORTED_TAXON` | error | A recognised motif falls outside the predeclared support taxonomy and must route to refusal. |
| `RECOGNITION_ARC_NO_SAGITTA_BOUND` | error | A circular-arc wall lacks a stated `max_sagitta_px` bound. |
| `RECOGNITION_ARC_BULGE_SWEEP_MISMATCH` | error | An arc's bulge sign contradicts its declared sweep direction. |
| `RECOGNITION_PASSAGE_SPAN_EXCEEDS_BOUND` | error | A `passage` opening span exceeds the frozen 3.0 m bound. |
| `RECOGNITION_THICKNESS_MISSING` | error | A product wall lacks sourced thickness (required for `cad_exact`/`raster_auto`). |
| `REVIEW_LINEAGE_CYCLE` | error | A review-chain append would form a cycle or reuse an existing review id. |
| `REVIEW_CURRENT_HEAD_STALE` | error | A review that is no longer the current head was treated as authoritative. |
| `SCHEMA_VERSION_UNSUPPORTED_BY_CONSUMER` | error | A document's schema version (or additive field) is not representable by the consumer's older schema. |

## Geometry compiler — append-only `GEOM_*` vocabulary (PLAN-003)

| Code | Severity | Meaning |
|---|---|---|
| `GEOM_SOURCE_HASH_MISMATCH` | error | Consumed parse artifact content_hash does not match its canonical hash. |
| `GEOM_RESOURCE_LIMIT` | error | A configured count/byte/coordinate bound was exceeded, or a field is non-finite/malformed. |
| `GEOM_EMPTY_GEOMETRY` | error | Parse payload did not contain at least one wall and one room. |
| `GEOM_DUPLICATE_ENTITY` | error | Derived geometry IDs collided within one run; no silent merge or renumber. |
| `GEOM_OPEN_POLYGON` | error | A room polygon is not closed. |
| `GEOM_SELF_INTERSECTING_POLYGON` | error | A room polygon is zero-area or self-crossing. |
| `GEOM_DEGENERATE_WALL` | error | A wall is shorter than the minimum allowed metric length. |
| `GEOM_OPENING_UNRESOLVED_WALL` | error | An opening references no wall. |
| `GEOM_OPENING_AMBIGUOUS_WALL_REF` | error | An opening resolves to more than one wall candidate (fail-closed). |
| `GEOM_OPENING_OFF_WALL` | error | An opening centre lies outside the allowed offset from its host wall. |
| `GEOM_OPENING_WIDTH_EXCEEDS_WALL` | error | Opening span does not fit within its host wall. |
| `GEOM_OPENING_ABOVE_WALL` | error | `sill_m + height_m` exceeds the host wall height. |
| `GEOM_OPEN_ROOM_BOUNDARY` | warn | A wall endpoint is off every room vertex, or a room edge has no supporting wall (fail-open, reported). |

## Camera planner — append-only `CAM_*` vocabulary (PLAN-004 / ADR-0008)

These codes are append-only and carry explicit severity and tier. `PARSE_*` and `GEOM_*`
are untouched; `CAM_*` is purely additive and consumes `camera_plan` 1.0.0 as-is. A code
may be added but never removed or re-ranked; changing a meaning or severity requires an ADR.
Consumers match on codes, never on message text.

| Code | Severity | Tier | Meaning |
|---|---|---|---|
| `CAM_SOURCE_HASH_MISMATCH` | error | 0 | Consumed geometry artifact `content_hash` does not match its canonical hash. |
| `CAM_RESOURCE_LIMIT` | error | 0 | A configured count/byte/coordinate bound was exceeded, or a field was non-finite/malformed. |
| `CAM_EMPTY_GEOMETRY` | error | 2 | Geometry payload lacks at least one room (and, for coverage scoring, at least one usable room polygon). |
| `CAM_DUPLICATE_ENTITY` | error | 2 | Viewpoint IDs or positions collided within one run (fail-closed, no silent merge/renumber). |
| `CAM_UNCOVERED_ROOM` | error | 3 | A target room has zero valid viewpoint placements after free-space resolution (fail-closed; the room is not silently skipped). |
| `CAM_VIEWPOINT_OUTSIDE_ROOM` | error | 3 | A viewpoint lies outside or on the boundary of its room polygon. |
| `CAM_VIEWPOINT_COLLIDES_WALL` | error | 3 | A viewpoint is closer than the wall clearance (`thickness_m/2 + 0.35 m`) to a wall centreline. |
| `CAM_VIEWPOINT_COLLIDES_OPENING` | error | 3 | A viewpoint is closer than `0.20 m` to a door/window opening centre. |
| `CAM_EXTRINSICS_INVALID` | error | 3 | A produced 4×4 fails `check_extrinsics_matrix` (not orthonormal, not right-handed, wrong last row, or non-Z-up convention). |
| `CAM_CAMERA_HEIGHT_OUT_OF_RANGE` | error | 3 | Camera height is non-finite or outside `[0.5, 3.0]` m. |
| `CAM_MAP_ADJACENCY_UNRESOLVED` | warn | 4 | A door opening does not resolve to two distinct covered rooms, so no adjacency edge is emitted (fail-open, reported). |

