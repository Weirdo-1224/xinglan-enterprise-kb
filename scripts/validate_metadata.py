"""Validate schema contracts and the Stage 1.1 data instances."""
import json

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from validation_common import fail, read_csv, ROOT


def instance_path(error):
    """Render a JSONPath-like location for an instance validation error."""
    path = "$"
    for part in error.absolute_path:
        path += f"[{part}]" if isinstance(part, int) else f".{part}"
    return path


errors = []
schemas = {}
schema_names = (
    "knowledge_metadata.schema.json",
    "source_registry.schema.json",
    "project_case.schema.json",
    "business_data.schema.json",
)
for name in schema_names:
    try:
        schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8-sig"))
        Draft202012Validator.check_schema(schema)
        schemas[name] = schema
    except (OSError, json.JSONDecodeError, SchemaError) as exc:
        errors.append(f"{name}: invalid JSON schema: {exc}")

knowledge = schemas.get("knowledge_metadata.schema.json", {})
props = knowledge.get("properties", {})
for field in ("parent_knowledge", "depends_on", "source_ids", "served_agents", "business_chain_stage"):
    if props.get(field, {}).get("type") != "array":
        errors.append(f"knowledge metadata {field} must be array")
for field in ("source_authority", "normative_force", "applicability", "dependency_rationale"):
    if field not in props:
        errors.append(f"knowledge metadata missing {field}")

source = schemas.get("source_registry.schema.json", {})
for field in ("source_authority", "normative_force", "applicability"):
    if field not in source.get("properties", {}):
        errors.append(f"source registry schema missing {field}")
if source and not source.get("allOf"):
    errors.append("source registry schema lacks VERIFIED conditional")

project = schemas.get("project_case.schema.json", {})
project_required = {
    "contract_amount", "budget", "milestones", "procurement", "contracts", "changes",
    "risks", "acceptance", "financials", "final_status",
}
if project and project_required - set(project.get("required", [])):
    errors.append("project schema lacks lifecycle facts")

project_validator = None
if project:
    project_validator = Draft202012Validator(project, format_checker=FormatChecker())
for project_id in ("P001", "P002", "P003"):
    path = ROOT / "enterprise_model" / "projects" / f"{project_id}_CANONICAL_FACTS.yaml"
    if project_validator is None:
        errors.append(f"{project_id}: project schema is unavailable")
        continue
    try:
        instance = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except (OSError, yaml.YAMLError) as exc:
        errors.append(f"{project_id}: cannot parse {path.relative_to(ROOT)}: {exc}")
        continue
    validation_errors = sorted(
        project_validator.iter_errors(instance),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if validation_errors:
        for error in validation_errors:
            errors.append(f"{project_id} {instance_path(error)}: {error.message}")
    else:
        print(f"PASS: {project_id} Schema Validation")

source_validator = None
if source:
    source_validator = Draft202012Validator(source, format_checker=FormatChecker())
registry_path = ROOT / "sources" / "SOURCE_REGISTRY.csv"
try:
    source_rows = read_csv(registry_path)
except OSError as exc:
    errors.append(f"SOURCE_REGISTRY: cannot read {registry_path.relative_to(ROOT)}: {exc}")
    source_rows = []
if source_validator is None:
    errors.append("SOURCE_REGISTRY: source registry schema is unavailable")
elif not source_rows:
    errors.append("SOURCE_REGISTRY: no records found")
else:
    source_error_count = 0
    for row_number, record in enumerate(source_rows, start=2):
        record_errors = sorted(
            source_validator.iter_errors(record),
            key=lambda item: tuple(str(part) for part in item.absolute_path),
        )
        source_error_count += len(record_errors)
        for error in record_errors:
            source_id = record.get("source_id") or "<missing source_id>"
            errors.append(f"SOURCE_REGISTRY row {row_number} ({source_id}) {instance_path(error)}: {error.message}")
    if source_error_count == 0:
        print(f"PASS: SOURCE_REGISTRY Schema Validation ({len(source_rows)} rows)")

body_dirs = [
    ROOT / "knowledge/core",
    ROOT / "knowledge/cases",
    ROOT / "knowledge/templates",
    ROOT / "knowledge/business_data",
]
files = [
    path
    for directory in body_dirs
    if directory.exists()
    for path in directory.rglob("*")
    if path.is_file() and path.suffix.lower() in {".md", ".txt", ".pdf", ".docx", ".xlsx", ".xls", ".pptx", ".ppt"}
]
if not files:
    print("SKIP: no knowledge bodies exist; body metadata validation remains deferred to Stage 3-5")
else:
    knowledge_validator = Draft202012Validator(knowledge, format_checker=FormatChecker()) if knowledge else None
    for path in files:
        if path.suffix.lower() != ".md":
            continue
        text = path.read_text(encoding="utf-8-sig")
        if not text.startswith("---\n"):
            errors.append(f"{path.relative_to(ROOT)}: missing YAML front matter")
            continue
        try:
            closing = text.index("\n---\n", 4)
            instance = yaml.safe_load(text[4:closing])
        except (ValueError, yaml.YAMLError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: invalid YAML front matter: {exc}")
            continue
        if not isinstance(instance, dict):
            errors.append(f"{path.relative_to(ROOT)}: front matter must be an object")
            continue
        if knowledge_validator is None:
            errors.append(f"{path.relative_to(ROOT)}: knowledge metadata schema is unavailable")
            continue
        record_errors = sorted(
            knowledge_validator.iter_errors(instance),
            key=lambda item: tuple(str(part) for part in item.absolute_path),
        )
        for error in record_errors:
            errors.append(f"{path.relative_to(ROOT)} {instance_path(error)}: {error.message}")
    if not any("knowledge/core" in str(message).replace("\\", "/") for message in errors):
        core_count = len(list((ROOT / "knowledge/core").glob("*.md")))
        print(f"PASS: parsed and schema-validated {core_count} core Markdown metadata blocks")

fail(errors)
print("PASS: metadata schema contracts and Stage 1.1 project/source instances are valid")
