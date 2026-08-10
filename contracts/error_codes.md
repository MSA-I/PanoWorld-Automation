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
