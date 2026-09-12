"""Validate Stage 3 PACKAGE-01 core knowledge bodies and semantic guardrails."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from validation_common import ROOT, fail, ids, manifest_rows, read_csv

CORE = ROOT / "knowledge" / "core"
ALLOWED_TYPES = {"ENTERPRISE_FOUNDATION", "PUBLIC_REFERENCE", "POLICY", "SOP", "FAQ_RULE", "ROLE"}
EXPECTED = [row for row in manifest_rows() if row["package"] == "PACKAGE-01" and row["knowledge_type"] in ALLOWED_TYPES]
ASSETS = {row["knowledge_id"]: row for row in manifest_rows()}
SOURCES = {row["source_id"]: row for row in read_csv(ROOT / "source_registry/SOURCE_REGISTRY.csv")}
SCHEMA = yaml.safe_load((ROOT / "schemas/knowledge_metadata.schema.json").read_text(encoding="utf-8-sig"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())


def parse(path: Path):
    text = path.read_text(encoding="utf-8-sig")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError("missing delimited YAML front matter")
    end = text.index("\n---\n", 4)
    return yaml.safe_load(text[4:end]), text[end + 5:].strip()


errors: list[str] = []
reviews: list[str] = []
files = list(CORE.glob("*.md")) if CORE.exists() else []
expected_names = {row["filename"] for row in EXPECTED}
actual_names = {path.name for path in files}
if len(files) != 100:
    errors.append(f"core file count {len(files)} != 100")
if expected_names != actual_names:
    errors.append(f"filename set differs; missing={sorted(expected_names-actual_names)}, extra={sorted(actual_names-expected_names)}")

counts = Counter()
parsed: dict[str, tuple[dict, str, Path]] = {}
for path in files:
    try:
        meta, body = parse(path)
    except (ValueError, yaml.YAMLError) as exc:
        errors.append(f"{path.name}: {exc}")
        continue
    kid = meta.get("knowledge_id", "") if isinstance(meta, dict) else ""
    if kid in parsed:
        errors.append(f"{path.name}: duplicate knowledge_id {kid}")
    parsed[kid] = (meta, body, path)
    row = ASSETS.get(kid)
    if not row:
        errors.append(f"{path.name}: unknown knowledge_id {kid}")
        continue
    counts[row["knowledge_type"]] += 1
    if path.name != row["filename"]:
        errors.append(f"{kid}: filename differs from manifest")
    for issue in VALIDATOR.iter_errors(meta):
        location = ".".join(map(str, issue.absolute_path)) or "$"
        errors.append(f"{kid}: metadata {location}: {issue.message}")
    if not body or len(body) < 180:
        errors.append(f"{kid}: body is empty or too small")
    if re.search(r"\b(?:TODO|TBD|placeholder)\b|待补充|占位", body, re.I):
        errors.append(f"{kid}: placeholder text found")
    if re.search(r"\b(?:Stage|Codex|Manifest)\b", body, re.I):
        errors.append(f"{kid}: engineering noise found in body")
    if len(body.split()) > 20000 or len(body) > 100000:
        errors.append(f"{kid}: exceeds platform body limit")
    if meta.get("served_agents") != ids(row["served_agents"]):
        errors.append(f"{kid}: served_agents differs from manifest")
    if meta.get("business_chain_stage") != ids(row["business_chain_stage"]):
        errors.append(f"{kid}: business_chain_stage differs from manifest")
    if meta.get("parent_knowledge") != ids(row["parent_knowledge"]):
        errors.append(f"{kid}: parent_knowledge differs from manifest")
    if meta.get("depends_on") != ids(row["depends_on"]):
        errors.append(f"{kid}: depends_on differs from manifest")
    for parent in meta.get("parent_knowledge", []):
        if parent not in ASSETS:
            errors.append(f"{kid}: unknown parent_knowledge {parent}")
    for sid in meta.get("source_ids", []):
        if sid not in SOURCES:
            errors.append(f"{kid}: unknown source_id {sid}")
        elif SOURCES[sid]["verification_status"] != "VERIFIED":
            errors.append(f"{kid}: source_id {sid} is not VERIFIED")
    verified_external = {
        sid for sid in meta.get("source_ids", [])
        if sid in SOURCES and SOURCES[sid]["verification_status"] == "VERIFIED"
        and SOURCES[sid]["source_type"] not in {"SYNTHETIC", "SYNTHETIC_DERIVED", "INTERNAL_DERIVED"}
    }
    if len(verified_external) < meta.get("minimum_source_count", 0):
        errors.append(f"{kid}: verified external source count {len(verified_external)} below minimum {meta.get('minimum_source_count')}")

expected_counts = {"ENTERPRISE_FOUNDATION": 12, "PUBLIC_REFERENCE": 18, "POLICY": 18, "SOP": 30, "FAQ_RULE": 12, "ROLE": 10}
for ktype, expected in expected_counts.items():
    if counts[ktype] != expected:
        errors.append(f"{ktype}: {counts[ktype]} != {expected}")

all_bodies = "\n".join(body for _, body, _ in parsed.values())
for anchor in ["星澜数字科技有限公司", "2021 年", "成都", "286 人", "市场营销中心", "综合管理部"]:
    if anchor not in all_bodies:
        errors.append(f"canonical anchor missing from corpus: {anchor}")
thresholds = ["小于 5 万元", "5 万元至 20 万元", "20 万元至 100 万元", "100 万元及以上"]
for kid in ("KB005", "POL011", "FAQ007"):
    body = parsed.get(kid, ({}, "", Path()))[1]
    for threshold in thresholds:
        if threshold not in body:
            errors.append(f"{kid}: canonical procurement threshold missing: {threshold}")
    if "模拟内部规则" not in body and "内部合成规则" not in body:
        errors.append(f"{kid}: procurement thresholds are not marked synthetic/internal")
for kid in ("KB009", "SOP008"):
    body = parsed.get(kid, ({}, "", Path()))[1]
    for level in ("L1", "L2", "L3", "L4"):
        if level not in body:
            errors.append(f"{kid}: risk level {level} missing")

for kid, (meta, body, _) in parsed.items():
    ktype = meta.get("knowledge_type")
    deps = set(meta.get("depends_on", []))
    if ktype == "SOP":
        policy_deps = {item for item in deps if item.startswith("POL")}
        if not policy_deps and not any(item.startswith(("KB", "REF")) for item in deps):
            errors.append(f"{kid}: no governed upstream rule")
        if "不新增金额阈值、审批权限或法律义务" not in body:
            errors.append(f"{kid}: missing no-new-rule guardrail")
    if ktype == "FAQ_RULE":
        if "不替代上游制度" not in body:
            errors.append(f"{kid}: missing no-new-rule boundary")
        if kid == "FAQ011" and ("当前项目金额" not in body or "经核验的成本台账" not in body):
            errors.append("FAQ011: must avoid inventing Stage 5 operating figures")
    if ktype == "PUBLIC_REFERENCE":
        for sid in meta.get("source_ids", []):
            source = SOURCES[sid]
            if source["applicability"] == "ANALOGICAL" and "仅作方法或案例参考" not in body:
                errors.append(f"{kid}: ANALOGICAL source {sid} lacks explicit boundary")

if "REF004" in parsed:
    body = parsed["REF004"][1]
    if "第二十三条" not in body or "不少于六个月" not in body:
        errors.append("REF004: current 2025 Cybersecurity Law locator/retention requirement missing")
if "POL017" in parsed:
    body = parsed["POL017"][1]
    if "第二十三条" not in body or "不少于六个月" not in body:
        errors.append("POL017: current Cybersecurity Law control missing")

claims_path = ROOT / "manifests/CLAIM_PROVENANCE.csv"
if not claims_path.exists():
    errors.append("CLAIM_PROVENANCE.csv missing")
else:
    claims = read_csv(claims_path)
    if not claims:
        errors.append("CLAIM_PROVENANCE.csv is empty")
    if len({row["claim_id"] for row in claims}) != len(claims):
        errors.append("CLAIM_PROVENANCE.csv has duplicate claim_id")
    for row in claims:
        if row["knowledge_id"] not in parsed:
            errors.append(f"{row['claim_id']}: claim knowledge_id not in core")
        if row["claim_type"] not in {"EXPLICIT", "DERIVED", "SYNTHETIC"}:
            errors.append(f"{row['claim_id']}: invalid claim_type")
        if not row["evidence_ref"] or not row["evidence_locator"]:
            errors.append(f"{row['claim_id']}: incomplete evidence")
    print(f"PASS: {len(claims)} critical claims validated")

review_path = ROOT / "docs/STAGE3_REVIEW_REQUIRED.md"
if not review_path.exists():
    errors.append("STAGE3_REVIEW_REQUIRED.md missing")
else:
    review_text = review_path.read_text(encoding="utf-8-sig")
    reviews.extend(line[2:].strip() for line in review_text.splitlines() if line.startswith("- REVIEW:"))

fail(errors)
print("PASS: exactly 100 PACKAGE-01 core files match manifest filenames and IDs")
print("PASS: metadata, VERIFIED sources, lineage, non-empty bodies and platform limits")
print("PASS: canonical facts, procurement thresholds and risk levels are consistent")
print("PASS: POLICY-to-SOP and POLICY/SOP-to-FAQ guardrails are present")
print("PASS: PUBLIC_REFERENCE applicability boundaries are explicit")
if reviews:
    for item in reviews:
        print(f"REVIEW: {item}")
else:
    print("PASS: no unresolved semantic issue requires manual review")
