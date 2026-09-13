"""Validate Stage 1.1 planning-level manifest constraints."""
from pathlib import PurePath

from semantic_rules import APPLICABILITIES, NORMATIVE_FORCES, SOURCE_AUTHORITIES, SOURCE_TYPES
from validation_common import AGENTS, KNOWLEDGE_TYPES, PACKAGES, fail, ids, manifest_rows, read_csv, ROOT

rows = manifest_rows()
errors = []
required_columns = {
    "knowledge_id", "filename", "title", "domain", "knowledge_type", "priority", "package",
    "served_agents", "business_chain_stage", "source_strategy", "source_type", "required_source_categories",
    "minimum_source_count", "synthetic_fields", "source_requirement", "parent_knowledge",
    "depends_on", "dependency_rationale", "source_authority", "normative_force", "applicability",
    "status", "notes",
}
if not rows:
    errors.append("manifest is empty")
elif required_columns - set(rows[0]):
    errors.append(f"manifest missing columns {sorted(required_columns - set(rows[0]))}")
if len(rows) < 150:
    errors.append(f"asset count {len(rows)} below viable planning baseline 150")

kids = [r["knowledge_id"] for r in rows]
filenames = [r["filename"] for r in rows]
if len(kids) != len(set(kids)): errors.append("duplicate knowledge_id")
if len(filenames) != len(set(filenames)): errors.append("duplicate filename")
known = set(kids)

for r in rows:
    kid = r["knowledge_id"]
    if r["knowledge_type"] not in KNOWLEDGE_TYPES: errors.append(f"{kid}: invalid knowledge_type")
    if r["package"] not in PACKAGES: errors.append(f"{kid}: invalid package")
    if PurePath(r["filename"]).name != r["filename"]: errors.append(f"{kid}: filename must be flat")
    if r["source_type"] not in SOURCE_TYPES: errors.append(f"{kid}: invalid source_type")
    if r["source_authority"] not in SOURCE_AUTHORITIES: errors.append(f"{kid}: invalid source_authority")
    if r["normative_force"] not in NORMATIVE_FORCES: errors.append(f"{kid}: invalid normative_force")
    if r["applicability"] not in APPLICABILITIES: errors.append(f"{kid}: invalid applicability")
    unknown_agents = set(ids(r["served_agents"])) - AGENTS
    if unknown_agents: errors.append(f"{kid}: invalid agents {sorted(unknown_agents)}")
    for field in ("depends_on", "parent_knowledge"):
        values = ids(r[field])
        missing = set(values) - known
        if missing: errors.append(f"{kid}: {field} missing IDs {sorted(missing)}")
        if len(values) != len(set(values)): errors.append(f"{kid}: duplicate IDs in {field}")
        if kid in values: errors.append(f"{kid}: self-reference in {field}")
    if ids(r["depends_on"]) and not r["dependency_rationale"].strip():
        errors.append(f"{kid}: missing dependency_rationale")
    try:
        minimum = int(r["minimum_source_count"])
        if minimum < 0: raise ValueError
    except ValueError:
        errors.append(f"{kid}: invalid minimum_source_count")
        minimum = 0
    if r["knowledge_type"] == "POLICY":
        if minimum < 3: errors.append(f"{kid}: core policy requires at least 3 planned sources")
        if len(ids(r["required_source_categories"])) < 3: errors.append(f"{kid}: insufficient source categories")
        if not ids(r["synthetic_fields"]): errors.append(f"{kid}: policy synthetic_fields not planned")

plans = read_csv(ROOT / "manifests/PACKAGE_PLAN.csv")
# Stage 6: PACKAGE_PLAN is the final transport plan (4 flat upload ZIPs).
# The manifest `package` column stays the logical 3-way assignment:
# PACKAGE-01/02 coincide with transport 01/02; logical PACKAGE-03 (TPL+DATA)
# is rebalanced into transport PACKAGE-03 (DATA + PROJECT_INDEX) and PACKAGE-04 (TPL).
plan_ids = [p["package_id"] for p in plans]
if plan_ids != ["PACKAGE-01", "PACKAGE-02", "PACKAGE-03", "PACKAGE-04"]:
    errors.append("package plan must contain exactly PACKAGE-01..04 (final transport plan)")
else:
    logical = {pid: sum(r["package"] == pid for r in rows) for pid in PACKAGES}
    estimates = {p["package_id"]: int(p["estimated_file_count"]) for p in plans}
    for p in plans:
        estimate, maximum = int(p["estimated_file_count"]), int(p["max_file_count"])
        if estimate > maximum or maximum > 100:
            errors.append(f"{p['package_id']}: package exceeds 100-file limit")
    if estimates["PACKAGE-01"] != logical["PACKAGE-01"]:
        errors.append(f"PACKAGE-01: estimate {estimates['PACKAGE-01']} != logical {logical['PACKAGE-01']}")
    if estimates["PACKAGE-02"] != logical["PACKAGE-02"]:
        errors.append(f"PACKAGE-02: estimate {estimates['PACKAGE-02']} != logical {logical['PACKAGE-02']}")
    if estimates["PACKAGE-03"] + estimates["PACKAGE-04"] != logical["PACKAGE-03"] + 1:
        errors.append("PACKAGE-03+04: estimates must equal logical PACKAGE-03 plus PROJECT_INDEX.csv")

fail(errors)
print(f"PASS: Manifest {len(rows)} assets; source types, structural fields, dependencies, policy source plans and package counts are valid")
