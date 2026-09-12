"""Validate source registry semantics and source-to-knowledge lineage."""
from datetime import date

from semantic_rules import APPLICABILITIES, NORMATIVE_FORCES, SOURCE_AUTHORITIES
from validation_common import fail, manifest_rows, read_csv, ROOT

manifest_ids = {r["knowledge_id"] for r in manifest_rows()}
sources = read_csv(ROOT / "sources/SOURCE_REGISTRY.csv")
source_ids = {r["source_id"] for r in sources}
rows = read_csv(ROOT / "manifests/SOURCE_LINEAGE.csv")
errors = []
placeholders = ("占位", "待核验", "tbd", "todo", "placeholder")
source_types = {"PUBLIC_OFFICIAL", "PUBLIC_CORPORATE", "PUBLIC_CASE", "SYNTHETIC_DERIVED", "SYNTHETIC", "INTERNAL_DERIVED"}
statuses = {"candidate", "active", "deprecated", "archived"}
specificities = {"GENERAL", "DOMAIN", "ENTERPRISE", "SCENARIO"}

if len(source_ids) != len(sources): errors.append("duplicate source_id")
for source in sources:
    sid = source["source_id"]
    if source["source_type"] not in source_types: errors.append(f"{sid}: invalid source_type")
    if source["status"] not in statuses: errors.append(f"{sid}: invalid status")
    if source["specificity"] not in specificities: errors.append(f"{sid}: invalid specificity")
    if source["source_authority"] not in SOURCE_AUTHORITIES: errors.append(f"{sid}: invalid source_authority")
    if source["normative_force"] not in NORMATIVE_FORCES: errors.append(f"{sid}: invalid normative_force")
    if source["applicability"] not in APPLICABILITIES: errors.append(f"{sid}: invalid applicability")
    if source["verification_status"] == "VERIFIED":
        for field in ("title", "publisher", "url", "access_date", "source_type", "source_authority", "normative_force", "applicability", "domain"):
            value = source.get(field, "").strip()
            if not value: errors.append(f"{sid}: VERIFIED source missing {field}")
            if field in {"title", "publisher"} and any(token in value.lower() for token in placeholders):
                errors.append(f"{sid}: VERIFIED source has placeholder {field}")
        try:
            date.fromisoformat(source["access_date"])
        except ValueError:
            errors.append(f"{sid}: invalid VERIFIED access_date")
    elif source["verification_status"] == "PENDING" and source["status"] != "candidate":
        errors.append(f"{sid}: PENDING source must remain candidate")
    if sid == "SRC-MOF-001" and source["applicability"] != "ANALOGICAL":
        errors.append("government procurement placeholder must be ANALOGICAL for internal procurement")

lineage_ids = [r["lineage_id"] for r in rows]
if len(lineage_ids) != len(set(lineage_ids)): errors.append("duplicate lineage_id")
for row in rows:
    if row["knowledge_id"] not in manifest_ids: errors.append(f"{row['lineage_id']}: unknown knowledge_id")
    if row["source_id"] not in source_ids: errors.append(f"{row['lineage_id']}: unknown source_id")

fail(errors)
print(f"PASS: {len(sources)} sources satisfy authority/force/applicability and VERIFIED requirements; {len(rows)} lineage rows are valid")
