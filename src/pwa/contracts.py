"""Load and apply the versioned JSON Schema contracts (PLAN-000 T3/T5).

Schemas live in ``schemas/<name>/v<major>/<name>-<semver>.schema.json`` and are
registered by their versioned ``$id`` so cross-schema ``$ref`` (every artifact
references the envelope) resolves offline.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = REPO_ROOT / "schemas"
_SEMVER_RE = re.compile(r"-(\d+)\.(\d+)\.(\d+)\.schema\.json$")

# Single source of truth for the contracts bundle version (ADR-0002). Bumped to
# 1.3.0 by PLAN-002RF WP2 for the additive cad_exact/raster_auto contract round;
# historical finalized manifests keep their recorded (older) bundle version.
CONTRACTS_BUNDLE_VERSION = "1.3.0"


def compute_content_hash(doc: dict) -> str:
    """Normative content_hash (schemas/README.md): sha256 over the canonical
    UTF-8 JSON of the document with the top-level ``content_hash`` removed.

    ``sort_keys`` here applies ONLY to this ephemeral hashing serialization —
    never to files written to disk (map JSON insertion order is load-bearing).
    """
    stripped = {k: v for k, v in doc.items() if k != "content_hash"}
    canonical = json.dumps(stripped, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _semver_tuple(value: str) -> tuple[int, int, int]:
    major, minor, patch = value.split(".")
    return int(major), int(minor), int(patch)


def _schema_const(schema: dict, field: str) -> str:
    if field == "schema_id" and isinstance(schema.get("title"), str) and schema["title"] == "Artifact envelope":
        return "envelope"
    if field == "schema_version" and isinstance(schema.get("title"), str) and schema["title"] == "Artifact envelope":
        return "1.0.0"
    for entry in schema.get("allOf", ()):
        if not isinstance(entry, dict):
            continue
        properties = entry.get("properties")
        if not isinstance(properties, dict):
            continue
        field_schema = properties.get(field)
        if isinstance(field_schema, dict) and isinstance(field_schema.get("const"), str):
            return field_schema["const"]
    raise ValueError(f"Schema missing {field!r} const")


def load_schema_catalog(schemas_dir: Path | None = None) -> dict[tuple[str, str], dict]:
    """Return every schema version keyed by ``(schema_id, schema_version)``."""
    schemas_dir = Path(schemas_dir or SCHEMAS_DIR)
    out: dict[tuple[str, str], dict] = {}
    ids_seen: set[str] = set()
    for path in sorted(schemas_dir.rglob("*.schema.json")):
        match = _SEMVER_RE.search(path.name)
        if match is None:
            raise ValueError(f"Schema filename does not end with a semantic version: {path}")
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema_id = _schema_const(schema, "schema_id")
        schema_version = _schema_const(schema, "schema_version")
        if path.parent.parent.name != schema_id:
            raise ValueError(f"Schema path/name mismatch for {path}")
        if schema_version != ".".join(match.groups()):
            raise ValueError(f"Schema version does not match filename for {path}")
        key = (schema_id, schema_version)
        if key in out:
            raise ValueError(f"Duplicate schema version pair: {key}")
        if schema["$id"] in ids_seen:
            raise ValueError(f"Duplicate schema $id: {schema['$id']}")
        out[key] = schema
        ids_seen.add(schema["$id"])
    return out


def load_all_schemas(schemas_dir: Path | None = None) -> dict[str, dict]:
    """Return the latest schema per ``schema_id`` by semantic version."""
    out: dict[str, dict] = {}
    for (schema_id, schema_version), schema in load_schema_catalog(schemas_dir).items():
        current = out.get(schema_id)
        if current is None or _semver_tuple(schema_version) > _semver_tuple(_schema_const(current, "schema_version")):
            out[schema_id] = schema
    return out


def build_registry(catalog: dict[tuple[str, str], dict] | None = None) -> Registry:
    catalog = catalog or load_schema_catalog()
    return Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in catalog.values()
    )


def validator_for(
    schema_id: str,
    schema_version: str | None = None,
    catalog: dict[tuple[str, str], dict] | None = None,
) -> Draft202012Validator:
    catalog = catalog or load_schema_catalog()
    if schema_version is None:
        latest = load_all_schemas()
        if schema_id not in latest:
            raise KeyError(f"Unknown schema_id: {schema_id!r}")
        schema = latest[schema_id]
    else:
        key = (schema_id, schema_version)
        if key not in catalog:
            raise KeyError(f"Unknown schema/version pair: {key!r}")
        schema = catalog[key]
    return Draft202012Validator(schema, registry=build_registry(catalog))


def validate_artifact(
    doc: dict,
    catalog: dict[tuple[str, str], dict] | None = None,
) -> list:
    """Validate a full artifact document against its declared ``schema_id``.

    Returns the (possibly empty) list of jsonschema errors, all of them —
    detailed multi-error reporting is a stage-0 gate requirement (doc 03).
    """
    schema_id = doc.get("schema_id")
    schema_version = doc.get("schema_version")
    if not isinstance(schema_id, str):
        raise ValueError("Artifact document has no string schema_id field")
    if not isinstance(schema_version, str):
        raise ValueError("Artifact document has no string schema_version field")
    validator = validator_for(schema_id, schema_version, catalog)
    return sorted(validator.iter_errors(doc), key=lambda e: e.json_path)


def contract_rejection_reason(
    doc: dict,
    consumer_schema_version: str | None,
    catalog: dict[tuple[str, str], dict] | None = None,
) -> dict | None:
    """Predict and explain an old consumer's rejection of a document.

    Additive/new-runs-only contracts mean a NEWER document (or a newer field) is
    predictably rejected by an OLDER consumer whose schema pins
    ``additionalProperties:false``. This helper is purely diagnostic: it returns a
    machine-readable reason (code + detail), or ``None`` when the consumer's schema
    version can represent the document. It never mutates ``doc``.

    Returns ``{"code": "SCHEMA_VERSION_UNSUPPORTED_BY_CONSUMER", "detail": ...}``.
    """
    catalog = catalog or load_schema_catalog()
    schema_id = doc.get("schema_id")
    schema_version = doc.get("schema_version")
    if not isinstance(schema_id, str) or not isinstance(schema_version, str):
        return None
    consumer_key = (schema_id, consumer_schema_version) if consumer_schema_version else None
    if consumer_key is None or consumer_key not in catalog:
        # The consumer cannot even load its declared version for this schema id.
        return {
            "code": "SCHEMA_VERSION_UNSUPPORTED_BY_CONSUMER",
            "detail": (
                f"consumer has no schema for ({schema_id!r}, {consumer_schema_version!r}); "
                f"document declares {schema_version!r}"
            ),
        }
    if _semver_tuple(schema_version) > _semver_tuple(consumer_schema_version):
        return {
            "code": "SCHEMA_VERSION_UNSUPPORTED_BY_CONSUMER",
            "detail": (
                f"document schema {schema_version!r} is newer than consumer schema "
                f"{consumer_schema_version!r}"
            ),
        }
    # Same-or-older version: the consumer's schema can validate the document as-is.
    # (Any additional-property rejection is then the jsonschema layer's job, and
    # ``validate_artifact`` reports those precisely.)
    consumer_errors = validate_artifact(doc, catalog) if doc.get("schema_version") == consumer_schema_version else []
    if consumer_errors:
        return {
            "code": "SCHEMA_VERSION_UNSUPPORTED_BY_CONSUMER",
            "detail": (
                f"document is not valid under consumer schema {consumer_schema_version!r}: "
                f"{consumer_errors[0].message} at {consumer_errors[0].json_path}"
            ),
        }
    return None
