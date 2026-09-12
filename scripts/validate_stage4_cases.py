"""Stage 4 PROJECT_CASE body validation: manifest coverage, metadata contract,
canonical fact consistency, event-ledger integrity and cross-document coherence."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import date, timedelta

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from validation_common import ROOT, fail, ids, manifest_rows, read_csv

CASES = ROOT / "knowledge" / "cases"
LEDGER = ROOT / "manifests" / "PROJECT_EVENT_LEDGER.csv"
PROJECTS = ("P001", "P002", "P003")
PMS = {"P001": "林澄", "P002": "周骁", "P003": "顾川"}

errors: list[str] = []
rows = manifest_rows()
manifest_ids = {r["knowledge_id"] for r in rows}
case_rows = [r for r in rows if r["knowledge_type"] == "PROJECT_CASE"]
case_by_id = {r["knowledge_id"]: r for r in case_rows}

schema = yaml.safe_load((ROOT / "schemas/knowledge_metadata.schema.json").read_text(encoding="utf-8-sig"))
validator = Draft202012Validator(schema, format_checker=FormatChecker())

projects: dict[str, dict] = {}
for pid in PROJECTS:
    projects[pid] = json.loads((ROOT / "enterprise_model/projects" / f"{pid}_CANONICAL_FACTS.yaml").read_text(encoding="utf-8-sig"))


def parse(path):
    text = path.read_text(encoding="utf-8-sig")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError("missing delimited YAML front matter")
    end = text.index("\n---\n", 4)
    return yaml.safe_load(text[4:end]), text[end + 5:].strip()


# --- 1/2. Manifest coverage: every PROJECT_CASE body exists with exact filename ---
files = sorted(CASES.glob("*.md")) if CASES.exists() else []
expected_names = {r["filename"] for r in case_rows}
actual_names = {p.name for p in files}
if expected_names != actual_names:
    errors.append(f"case filename set differs; missing={sorted(expected_names - actual_names)}, extra={sorted(actual_names - expected_names)}")
counts = defaultdict(int)
for r in case_rows:
    m = re.match(r"^(P\d{3})_", r["knowledge_id"])
    counts[m.group(1) if m else "CASE"] += 1
print(f"PASS: manifest lists {len(case_rows)} PROJECT_CASE assets ({dict(counts)})")

# --- per-file checks ---
parsed: dict[str, tuple[dict, str]] = {}
for path in files:
    try:
        meta, body = parse(path)
    except (ValueError, yaml.YAMLError) as exc:
        errors.append(f"{path.name}: {exc}")
        continue
    kid = meta.get("knowledge_id", "") if isinstance(meta, dict) else ""
    parsed[path.name] = (meta, body)
    row = case_by_id.get(kid)
    if row is None:
        errors.append(f"{path.name}: knowledge_id {kid} not a PROJECT_CASE manifest row")
        continue
    # knowledge_id / filename consistency
    if row["filename"] != path.name:
        errors.append(f"{path.name}: filename mismatch with manifest {row['filename']}")
    if not path.name.startswith(kid + "_"):
        errors.append(f"{path.name}: filename does not start with knowledge_id {kid}")
    # 3. legal project id
    m = re.match(r"^(P\d{3})_\d{2}$", kid)
    if m and m.group(1) not in PROJECTS:
        errors.append(f"{kid}: unknown project_id {m.group(1)}")
    if m and kid not in projects[m.group(1)].get("documents", []):
        errors.append(f"{kid}: not listed in {m.group(1)} canonical documents")
    if not m and not re.match(r"^CASE\d{3}$", kid):
        errors.append(f"{kid}: illegal PROJECT_CASE id form")
    # 4. metadata schema
    for error in sorted(validator.iter_errors(meta), key=lambda e: tuple(str(p) for p in e.absolute_path)):
        errors.append(f"{path.name} metadata: {error.message}")
    # manifest field fidelity
    def split(value):
        return ids(value)
    checks = [
        ("title", row["title"]), ("domain", row["domain"]), ("knowledge_type", "PROJECT_CASE"),
        ("priority", row["priority"]), ("source_type", row["source_type"]),
        ("source_strategy", row["source_strategy"]), ("source_authority", row["source_authority"]),
        ("normative_force", row["normative_force"]), ("applicability", row["applicability"]),
        ("dependency_rationale", row["dependency_rationale"]),
    ]
    for field, expected in checks:
        if meta.get(field) != expected:
            errors.append(f"{kid}: metadata {field} != manifest ({meta.get(field)!r} != {expected!r})")
    for field in ("served_agents", "business_chain_stage", "synthetic_fields", "parent_knowledge", "depends_on"):
        if list(meta.get(field) or []) != split(row[field]):
            errors.append(f"{kid}: metadata {field} != manifest values")
    if int(meta.get("minimum_source_count", -1)) != int(row["minimum_source_count"]):
        errors.append(f"{kid}: minimum_source_count mismatch")
    if list(meta.get("required_source_categories") or []) != split(row["required_source_categories"]):
        errors.append(f"{kid}: required_source_categories mismatch")
    for field, expected in (("company", "星澜数字科技有限公司"), ("status", "active"), ("authority_level", "L4")):
        if meta.get(field) != expected:
            errors.append(f"{kid}: {field} must be {expected}")
    # 9/10/11. body hygiene
    if "SYNTHETIC" not in body:
        errors.append(f"{kid}: body lacks SYNTHETIC declaration")
    if not re.search(r"(?m)^## 关联\s*$", body):
        errors.append(f"{kid}: body lacks '## 关联' section")
    for token in ("TODO", "待补充", "占位", "placeholder", "TBD", "Codex", "validator", "Stage"):
        if token.lower() in body.lower():
            errors.append(f"{kid}: body contains engineering noise '{token}'")
    if "应当" in body or "原则上" in body:
        errors.append(f"{kid}: body uses normative wording (应当/原则上), case must narrate facts")
    if not re.search(r"20[12]\d\s*[-年]", body):
        errors.append(f"{kid}: body carries no concrete project date")

# --- 5/8/12. canonical fact consistency per project ---
wan = lambda amount: f"{amount / 10000:g}"
for pid, project in projects.items():
    corpus = "\n".join(body for name, (meta, body) in parsed.items() if name.startswith(f"{pid}_"))
    if not corpus:
        errors.append(f"{pid}: no parsed bodies")
        continue
    key_amounts = {
        "contract_amount": project["contract_amount"]["amount"],
        "budget": project["budget"]["amount"],
        "actual_cost": project["financials"]["actual_cost"]["amount"],
    }
    for label, amount in key_amounts.items():
        if not re.search(rf"{re.escape(wan(amount))}\s*万", corpus):
            errors.append(f"{pid}: canonical {label} {wan(amount)}万 not found in project corpus")
    for item in project.get("procurement", []):
        if not re.search(rf"{re.escape(wan(item['amount']['amount']))}\s*万", corpus):
            errors.append(f"{pid}: procurement amount {wan(item['amount']['amount'])}万 not found in corpus")
    pm = project["project_manager"].split("（")[0]
    if pm not in corpus:
        errors.append(f"{pid}: project manager {pm} missing from corpus")
    for other, other_pm in PMS.items():
        if other != pid and other_pm in corpus:
            errors.append(f"{pid}: corpus contaminated by {other} PM {other_pm}")
    for other, facts in projects.items():
        if other == pid:
            continue
        foreign = wan(facts["contract_amount"]["amount"])
        if re.search(rf"{re.escape(foreign)}\s*万", corpus):
            errors.append(f"{pid}: corpus contains {other} contract amount {foreign}万")
    for risk in project.get("risks", []):
        if risk["risk_id"] not in corpus:
            errors.append(f"{pid}: canonical risk {risk['risk_id']} never referenced in bodies")
    for change in project.get("changes", []):
        if change["change_id"] not in corpus:
            errors.append(f"{pid}: canonical change {change['change_id']} never referenced in bodies")
    if project["acceptance"]["date"] not in corpus:
        errors.append(f"{pid}: acceptance date {project['acceptance']['date']} missing from corpus")

# --- cross-project differentiation ---
markers = {
    "P001": ("招标", "数字人"),
    "P002": ("知识版本", "纠偏"),
    "P003": ("GPU", "巡检"),
}
for pid, words in markers.items():
    corpus = "\n".join(body for name, (meta, body) in parsed.items() if name.startswith(f"{pid}_"))
    for word in words:
        if word not in corpus:
            errors.append(f"{pid}: differentiation marker '{word}' missing")

# --- 9. referenced knowledge ids exist ---
ref_pattern = re.compile(r"(?<![A-Z0-9])(POL|SOP|FAQ|KB|REF|TPL|DATA|ROLE)\d{3}(?![0-9])")
for name, (meta, body) in parsed.items():
    for ref in sorted(set(m.group(0) for m in ref_pattern.finditer(body))):
        if ref not in manifest_ids:
            errors.append(f"{name}: references unknown knowledge id {ref}")

# --- 6/7/14. event ledger integrity and causal closure ---
ledger = read_csv(LEDGER)
required_cols = {"event_id", "project_id", "date", "event_type", "title", "actors", "trigger", "decision",
                 "impact_scope", "impact_schedule", "impact_cost", "related_case_ids", "related_risk_id",
                 "related_change_id", "status"}
if not ledger or required_cols - set(ledger[0]):
    errors.append(f"ledger missing columns {sorted(required_cols - set(ledger[0] if ledger else []))}")
    ledger = []
event_ids = [r["event_id"] for r in ledger]
if len(event_ids) != len(set(event_ids)):
    errors.append("ledger duplicate event_id")
risk_ids = {r["risk_id"] for p in projects.values() for r in p.get("risks", [])}
change_ids = {c["change_id"] for p in projects.values() for c in p.get("changes", [])}
per_project: dict[str, list[dict]] = defaultdict(list)
for row in ledger:
    pid = row["project_id"]
    if pid not in PROJECTS:
        errors.append(f"{row['event_id']}: illegal project_id {pid}")
        continue
    per_project[pid].append(row)
    try:
        row["_d"] = date.fromisoformat(row["date"])
    except ValueError:
        errors.append(f"{row['event_id']}: invalid date {row['date']}")
        continue
    for cid in ids(row["related_case_ids"]):
        if cid not in manifest_ids:
            errors.append(f"{row['event_id']}: unknown related_case_id {cid}")
    for rid in ids(row["related_risk_id"]):
        if rid not in risk_ids:
            errors.append(f"{row['event_id']}: unknown risk id {rid}")
    for cid in ids(row["related_change_id"]):
        if cid not in change_ids:
            errors.append(f"{row['event_id']}: unknown change id {cid}")
for pid, events in per_project.items():
    dates = [e["_d"] for e in events if "_d" in e]
    if dates != sorted(dates):
        errors.append(f"{pid}: ledger events out of chronological order")
    p = projects[pid]
    start, end = date.fromisoformat(p["planned_start_date"]), date.fromisoformat(p["actual_end_date"])
    if dates and (min(dates) < start - timedelta(days=400) or max(dates) > end + timedelta(days=120)):
        errors.append(f"{pid}: ledger dates outside plausible project window")
    ledger_risks = {rid for e in events for rid in ids(e["related_risk_id"])}
    ledger_changes = {cid for e in events for cid in ids(e["related_change_id"])}
    for risk in p.get("risks", []):
        if risk["risk_id"] not in ledger_risks:
            errors.append(f"{pid}: canonical risk {risk['risk_id']} absent from ledger")
    for change in p.get("changes", []):
        if change["change_id"] not in ledger_changes:
            errors.append(f"{pid}: canonical change {change['change_id']} absent from ledger")
    acc = date.fromisoformat(p["acceptance"]["date"])
    if not any(e.get("_d") == acc and e["event_type"] == "验收" for e in events):
        errors.append(f"{pid}: no 验收 ledger event on canonical acceptance date {acc}")

# EVT references in bodies must exist in ledger and match the file's project
evt_pattern = re.compile(r"EVT-(P\d{3})-\d{3}")
ledger_ids = set(event_ids)
for name, (meta, body) in parsed.items():
    file_pid = name.split("_")[0]
    for evt in sorted(set(m.group(0) for m in evt_pattern.finditer(body))):
        if evt not in ledger_ids:
            errors.append(f"{name}: references unknown ledger event {evt}")
        elif file_pid in PROJECTS and not evt.startswith(f"EVT-{file_pid}-"):
            errors.append(f"{name}: references other project event {evt}")

# P002 causal chain closure: changes -> escalation -> correction meeting -> acceptance
p002_events = per_project.get("P002", [])
typed = defaultdict(list)
for e in p002_events:
    if "_d" in e:
        typed[e["event_type"]].append(e["_d"])
if p002_events:
    chain = [("变更", typed.get("变更")), ("风险", typed.get("风险")), ("会议", typed.get("会议")),
             ("付款", typed.get("付款")), ("验收", typed.get("验收"))]
    for label, values in chain:
        if not values:
            errors.append(f"P002: causal chain missing event_type {label}")
    if typed.get("变更") and typed.get("验收") and max(typed["变更"]) > max(typed["验收"]):
        errors.append("P002: last change occurs after acceptance; chain broken")
    titles = " ".join(e["title"] for e in p002_events)
    if "纠偏" not in titles:
        errors.append("P002: ledger lacks 纠偏 meeting event")

# --- Stage 4.1 governance checks ---

# G1. CASE001-004 must not create new mandatory enterprise rules without policy basis.
# A normative line is allowed only when it (a) cites an existing POL/SOP/KB/FAQ/REF id on the
# same line, (b) carries a suggestion / pending-review marker, or (c) matches the explicit
# allowlist of factual narration lines.
normative_tokens = ("必须", "不得", "自动上调", "一律", "强制要求", "应在")
suggestion_markers = ("建议", "推荐", "可考虑", "待制度评审", "后续可纳入")
policy_ref = re.compile(r"(POL|SOP|KB|FAQ|REF)\d{3}")
normative_allowlist = (
    "不构成现行企业强制规则",
    "缺少制度化的强制纠偏动作",
)
for case_id in ("CASE001", "CASE002", "CASE003", "CASE004"):
    entry = next(((n, b) for n, (m, b) in parsed.items() if m.get("knowledge_id") == case_id), None)
    if entry is None:
        errors.append(f"{case_id}: missing from parsed cases")
        continue
    name, body = entry
    for lineno, line in enumerate(body.splitlines(), start=1):
        if not any(token in line for token in normative_tokens):
            continue
        if policy_ref.search(line) or any(marker in line for marker in suggestion_markers):
            continue
        if any(fragment in line for fragment in normative_allowlist):
            continue
        errors.append(f"{name}:{lineno}: normative wording without policy basis or review marker: {line.strip()[:60]}")

# G2/G3. P003 meeting ids must use MTG-P003-xx; legacy P003-Mxx must be gone from active files.
legacy_meeting = re.compile(r"P003-M\d{2}")
for name, (meta, body) in parsed.items():
    if legacy_meeting.search(body):
        errors.append(f"{name}: legacy meeting id P003-Mxx still present")
ledger_text = LEDGER.read_text(encoding="utf-8-sig")
if legacy_meeting.search(ledger_text):
    errors.append("PROJECT_EVENT_LEDGER.csv: legacy meeting id P003-Mxx still present")
p003_corpus = "\n".join(body for name, (meta, body) in parsed.items() if name.startswith("P003_"))
for seq in range(1, 8):
    mtg = f"MTG-P003-{seq:02d}"
    if mtg not in p003_corpus:
        errors.append(f"P003: expected meeting id {mtg} missing from project corpus")

# G4. SYNTHETIC_DERIVED assets with source_ids: every id must exist and be VERIFIED.
source_registry = {r["source_id"]: r for r in read_csv(ROOT / "sources" / "SOURCE_REGISTRY.csv")}
for name, (meta, body) in parsed.items():
    if meta.get("source_type") != "SYNTHETIC_DERIVED":
        continue
    for sid in meta.get("source_ids") or []:
        source = source_registry.get(sid)
        if source is None:
            errors.append(f"{name}: source_id {sid} not in SOURCE_REGISTRY")
        elif source["verification_status"] != "VERIFIED":
            errors.append(f"{name}: source_id {sid} not VERIFIED ({source['verification_status']})")

fail(errors)
print(f"PASS: parsed {len(parsed)} case bodies; metadata matches manifest and schema")
print(f"PASS: canonical amounts/dates/PM/risks/changes consistent across P001/P002/P003 corpora")
print(f"PASS: ledger {len(ledger)} events; chronological, cross-references and causal chains closed")
print(f"PASS: project differentiation markers and knowledge-id references valid")
print(f"PASS: CASE001-004 normative wording grounded in policy or marked as suggestion/pending-review")
print(f"PASS: P003 meeting ids unified to MTG-P003-01..07; no legacy P003-Mxx in active files")
print(f"PASS: SYNTHETIC_DERIVED source_ids all registered and VERIFIED")
print("PASS: Stage 4 project case validation complete")
