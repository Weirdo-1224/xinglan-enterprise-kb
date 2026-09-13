"""Validate enterprise anchors, package counts and project canonical facts."""
import json
from datetime import date

from validation_common import fail, manifest_rows, read_csv, ROOT

errors = []
facts = (ROOT / "enterprise_model/CANONICAL_FACTS.yaml").read_text(encoding="utf-8")
for required in ["星澜数字科技有限公司", "founded_year: 2021", "headquarters: \"成都\"", "employee_count: 286", "D01:", "D08:"]:
    if required not in facts: errors.append(f"Canonical Facts missing {required}")

rows = manifest_rows()
if len(rows) != len({r["knowledge_id"] for r in rows}): errors.append("manifest IDs are not unique")
# Stage 6 final transport plan: 4 flat ZIPs covering all assets plus the
# PROJECT_INDEX.csv transport copy in PACKAGE-03.
plans = read_csv(ROOT / "manifests/PACKAGE_PLAN.csv")
total_estimate = sum(int(p["estimated_file_count"]) for p in plans)
if total_estimate != len(rows) + 1:
    errors.append(f"package plan total {total_estimate} != {len(rows)} assets + PROJECT_INDEX.csv")
if any(int(p["estimated_file_count"]) > 100 for p in plans):
    errors.append("package plan exceeds the 100-file upload limit")

manifest_ids = {r["knowledge_id"] for r in rows}
required_project_fields = {
    "project_id", "project_name", "project_type", "customer_type", "contract_amount", "budget",
    "planned_start_date", "planned_end_date", "actual_start_date", "actual_end_date", "delay_days",
    "project_manager", "team_size", "milestones", "procurement", "contracts", "changes", "risks",
    "acceptance", "financials", "final_status", "lessons", "documents",
}
projects = {}
for pid in ("P001", "P002", "P003"):
    path = ROOT / "enterprise_model/projects" / f"{pid}_CANONICAL_FACTS.yaml"
    try:
        project = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{pid}: unreadable canonical facts: {exc}")
        continue
    projects[pid] = project
    if required_project_fields - set(project): errors.append(f"{pid}: missing canonical fields {sorted(required_project_fields-set(project))}")
    if project.get("project_id") != pid: errors.append(f"{pid}: project_id mismatch")
    docs = set(project.get("documents", []))
    planned = {kid for kid in manifest_ids if kid.startswith(f"{pid}_")}
    if docs != planned: errors.append(f"{pid}: canonical documents differ from manifest; missing={sorted(planned-docs)}, extra={sorted(docs-planned)}")
    try:
        planned_end = date.fromisoformat(project["planned_end_date"])
        actual_end = date.fromisoformat(project["actual_end_date"])
        calculated_delay = max(0, (actual_end - planned_end).days)
        if project["delay_days"] != calculated_delay: errors.append(f"{pid}: delay_days {project['delay_days']} != {calculated_delay}")
    except (KeyError, ValueError, TypeError):
        errors.append(f"{pid}: invalid project date fields")
    budget = project.get("budget", {}).get("amount")
    cost = project.get("financials", {}).get("actual_cost", {}).get("amount")
    variance = project.get("financials", {}).get("budget_variance", {}).get("amount")
    if all(isinstance(v, (int, float)) for v in (budget, cost, variance)) and cost - budget != variance:
        errors.append(f"{pid}: budget_variance inconsistent with actual cost")

if "P001" in projects:
    p = projects["P001"]
    if p["delay_days"] != 0 or p["acceptance"]["result"] != "passed" or p["financials"]["actual_cost"]["amount"] > p["budget"]["amount"]:
        errors.append("P001 does not model an on-time, controlled, smoothly accepted project")
if "P002" in projects:
    text = json.dumps(projects["P002"], ensure_ascii=False)
    for marker in ("人员不足", "知识版本冲突", "付款条件", "成本", "变更"):
        if marker not in text: errors.append(f"P002 missing problem marker: {marker}")
    if len(projects["P002"]["changes"]) < 3 or projects["P002"]["delay_days"] <= 0:
        errors.append("P002 must contain multiple changes and delay")
    if projects["P002"]["financials"]["actual_cost"]["amount"] <= projects["P002"]["budget"]["amount"]:
        errors.append("P002 must exceed budget")
if "P003" in projects:
    text = json.dumps(projects["P003"], ensure_ascii=False)
    for marker in ("GPU", "视频", "算法", "技术", "验收", "数据"):
        if marker not in text: errors.append(f"P003 missing complexity marker: {marker}")

body_files = [p for p in (ROOT / "knowledge").rglob("*") if p.is_file() and p.name != "README.md"]
print("NOTE: knowledge bodies detected; later-stage body consistency is additionally required" if body_files else "SKIP: no knowledge bodies; body-level consistency is deferred")
fail(errors)
print("PASS: enterprise anchors, package totals and P001/P002/P003 canonical facts are consistent")
