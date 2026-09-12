"""Validate capability-based coverage for all 12 agents."""
from collections import defaultdict

from semantic_rules import AGENT_REQUIRED_CAPABILITIES
from validation_common import AGENTS, fail, ids, manifest_rows, read_csv, ROOT

assets = {r["knowledge_id"]: r for r in manifest_rows()}
rows = read_csv(ROOT / "manifests/AGENT_COVERAGE.csv")
errors = []
required = {"agent_id", "agent_name", "capability", "required_asset_type", "required_asset_ids", "minimum_viable_coverage", "coverage_status", "gap"}
if not rows or required - set(rows[0]): errors.append(f"coverage missing columns {sorted(required - set(rows[0]) if rows else required)}")
if {r["agent_id"] for r in rows} != AGENTS: errors.append("coverage must contain exactly A01..A12")

seen = set()
actual_capabilities = defaultdict(set)
for r in rows:
    key = (r["agent_id"], r["capability"])
    if key in seen: errors.append(f"duplicate capability row {key}")
    seen.add(key)
    actual_capabilities[r["agent_id"]].add(r["capability"])
    required_ids = ids(r["required_asset_ids"])
    required_types = set(ids(r["required_asset_type"]))
    if not required_ids: errors.append(f"{r['agent_id']}/{r['capability']}: no mapped assets")
    missing = [kid for kid in required_ids if kid not in assets]
    if missing: errors.append(f"{r['agent_id']}/{r['capability']}: unknown IDs {missing}")
    mapped_types = {assets[kid]["knowledge_type"] for kid in required_ids if kid in assets}
    missing_types = required_types - mapped_types
    if missing_types: errors.append(f"{r['agent_id']}/{r['capability']}: required types not mapped {sorted(missing_types)}")
    unserved = [kid for kid in required_ids if kid in assets and r["agent_id"] not in ids(assets[kid]["served_agents"])]
    if unserved: errors.append(f"{r['agent_id']}/{r['capability']}: assets do not serve agent {unserved}")
    expected_status = "FULL" if required_ids and not missing and not missing_types and not unserved else "PARTIAL"
    if r["coverage_status"] not in {"FULL", "PARTIAL", "MISSING"}: errors.append(f"{key}: invalid coverage_status")
    elif r["coverage_status"] != expected_status: errors.append(f"{key}: status {r['coverage_status']} should be {expected_status}")
    if not r["minimum_viable_coverage"].strip(): errors.append(f"{key}: missing minimum viable coverage")

for aid, expected in AGENT_REQUIRED_CAPABILITIES.items():
    actual = actual_capabilities[aid]
    if actual != expected:
        errors.append(f"{aid}: capability set mismatch; missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")

fail(errors)
for aid in sorted(AGENTS):
    status = "FULL" if all(r["coverage_status"] == "FULL" for r in rows if r["agent_id"] == aid) else "PARTIAL"
    print(f"{aid}: {status} ({len(actual_capabilities[aid])} core capabilities)")
print("PASS: all 12 agents satisfy the curated capability-based coverage model")
