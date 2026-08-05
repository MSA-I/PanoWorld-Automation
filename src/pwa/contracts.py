"""Load and apply the versioned JSON Schema contracts (PLAN-000 T3/T5).

Schemas live in ``schemas/<name>/v<major>/<name>-<semver>.schema.json`` and are
registered by their versioned ``$id`` so cross-schema ``$ref`` (every artifact
references the envelope) resolves offline.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = REPO_ROOT / "schemas"


def compute_content_hash(doc: dict) -> str:
    """Normative content_hash (schemas/README.md): sha256 over the canonical
    UTF-8 JSON of the document with the top-level ``content_hash`` removed.

    ``sort_keys`` here applies ONLY to this ephemeral hashing serialization —
    never to files written to disk (map JSON insertion order is load-bearing).
    """
    stripped = {k: v for k, v in doc.items() if k != "content_hash"}
    canonical = json.dumps(stripped, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_all_schemas(schemas_dir: Path | None = None) -> dict[str, dict]:
    """Return ``{schema_id: schema}`` for every schema file on disk.

    ponytail: exactly one version exists per schema today; when a second version
    appears, pick latest per major here and add a compatibility matrix test.
    """
    schemas_dir = Path(schemas_dir or SCHEMAS_DIR)
    out: dict[str, dict] = {}
    for path in sorted(schemas_dir.rglob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        name = path.parent.parent.name  # schemas/<name>/v<major>/<file>
        out[name] = schema
    return out


def build_registry(schemas: dict[str, dict] | None = None) -> Registry:
    schemas = schemas or load_all_schemas()
    return Registry().with_resources(
        (s["$id"], Resource.from_contents(s)) for s in schemas.values()
    )


def validator_for(schema_id: str, schemas: dict[str, dict] | None = None) -> Draft202012Validator:
    schemas = schemas or load_all_schemas()
    if schema_id not in schemas:
        raise KeyError(f"Unknown schema_id: {schema_id!r}")
    return Draft202012Validator(schemas[schema_id], registry=build_registry(schemas))


def validate_artifact(doc: dict, schemas: dict[str, dict] | None = None) -> list:
    """Validate a full artifact document against its declared ``schema_id``.

    Returns the (possibly empty) list of jsonschema errors, all of them —
    detailed multi-error reporting is a stage-0 gate requirement (doc 03).
    """
    schema_id = doc.get("schema_id")
    if not isinstance(schema_id, str):
        raise ValueError("Artifact document has no string schema_id field")
    validator = validator_for(schema_id, schemas)
    return sorted(validator.iter_errors(doc), key=lambda e: e.json_path)
