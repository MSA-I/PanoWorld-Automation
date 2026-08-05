# Schemas — contract conventions (PLAN-000 T3, per ADR-0002)

- Dialect: JSON Schema **draft 2020-12**.
- Layout: `schemas/<name>/v<major>/<name>-<semver>.schema.json`, versioned `$id`.
- Every artifact document is an **envelope** (common fields, provenance, status/errors)
  with the type-specific content under `payload`. Artifact schemas pin
  `schema_id`/`schema_version` with `const` and constrain `payload` via `allOf`
  with the envelope schema.
- Versioning: MINOR/PATCH are additive only (enforced by keeping every historical
  example fixture green); breaking change = new MAJOR directory + ADR.
- A single `contracts_bundle_version` is recorded in `project_manifest` and
  `run_manifest` payloads.
- Hashes are always `sha256:<64 hex>`. Timestamps are RFC 3339 / ISO-8601.
- **`content_hash` definition (normative):** sha256 over the canonical UTF-8 JSON
  serialization of the artifact document **with the top-level `content_hash`
  member removed** (no self-reference). Canonical form =
  `json.dumps(doc, ensure_ascii=False, separators=(",", ":"), sort_keys=True)`
  encoded UTF-8. `sort_keys` applies ONLY to this ephemeral hashing
  serialization — files written to disk (map JSON, manifests) keep insertion
  order untouched. Reference implementation: `pwa.contracts.compute_content_hash`.
  `inputs[].content_hash` and `approval_record.target_content_hash` refer to the
  same definition applied to the input/target document.
- **State-value serialization (normative):** pipeline run states written
  anywhere OUTSIDE `contracts/state_machine.yaml` (PROJECT-STATE, reports,
  artifacts such as `retry_request.target_state`) are serialized with the
  namespace prefix — `RUN:<STATE>` (e.g. `RUN:CAMERAS_PLANNED`) — so they can
  never be confused with the PLAN work-statuses of docs/04.
- Reason/error codes are `UPPER_SNAKE_CASE`; the validator vocabulary lives in
  `contracts/error_codes.md` and is locked for downstream consumers (dashboard).
- Paths inside artifacts are repo-/scene-relative with forward slashes; never
  absolute, never OS-specific separators.

Current schemas (all v1, draft 1.0.0): envelope, project_manifest,
input_quality_report, floorplan_parse, scene_geometry, assumptions, camera_plan,
style_spec, panoworld_manifest, run_manifest, qa_report, approval_record,
retry_request, remote_job.
