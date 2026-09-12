"""Curated Stage 1.1 semantic dependency and anti-mechanical checks."""
import re
from collections import defaultdict

from semantic_rules import AGENT_REQUIRED_CAPABILITIES
from validation_common import fail, ids, manifest_rows, read_csv, ROOT

rows = manifest_rows()
assets = {r["knowledge_id"]: r for r in rows}
errors = []
upstream_types = {"POLICY", "ENTERPRISE_FOUNDATION", "PUBLIC_REFERENCE"}
rule_upstream_types = upstream_types | {"SOP"}

def numeric_id(kid):
    match = re.search(r"(\d+)$", kid)
    return int(match.group(1)) if match else None

for row in rows:
    kid = row["knowledge_id"]
    deps = ids(row["depends_on"])
    parents = ids(row["parent_knowledge"])
    dep_rows = [assets[x] for x in deps if x in assets]
    parent_rows = [assets[x] for x in parents if x in assets]
    if row["knowledge_type"] == "SOP":
        if len(deps) == 1 and deps[0].startswith("POL") and numeric_id(kid) == numeric_id(deps[0]):
            errors.append(f"{kid}: mechanical same-number POLICY dependency")
        if not any(x["knowledge_type"] in upstream_types for x in dep_rows):
            errors.append(f"{kid}: lacks POLICY/ENTERPRISE_FOUNDATION/PUBLIC_REFERENCE upstream")
        if not parents or not all(x["knowledge_type"] in upstream_types for x in parent_rows):
            errors.append(f"{kid}: parent_knowledge must trace to higher-level rules")
    if row["knowledge_type"] == "FAQ_RULE":
        if len(deps) == 1 and deps[0].startswith("SOP") and numeric_id(kid) == numeric_id(deps[0]):
            errors.append(f"{kid}: mechanical same-number SOP dependency")
        if not any(x["knowledge_type"] in rule_upstream_types for x in dep_rows):
            errors.append(f"{kid}: FAQ/RULE lacks upstream rule")
        if not parents or not all(x["knowledge_type"] in upstream_types for x in parent_rows):
            errors.append(f"{kid}: parent_knowledge must trace to higher-level rules")
    if row["knowledge_type"] in {"SOP", "FAQ_RULE", "PROJECT_CASE"} and not row["dependency_rationale"].strip():
        errors.append(f"{kid}: semantic asset missing dependency rationale")

dedicated_sops = {
    "A10 tender": ("A10", ("招标文件审查流程", "投标文件审查流程")),
    "A06 document": ("A06", ("文档格式检查流程", "文档排版流程", "格式修复与模板套用流程")),
    "A08 performance": ("A08", ("绩效目标制定流程", "中期绩效回顾流程", "绩效评价与反馈流程", "绩效改进计划流程")),
    "A03 knowledge": ("A03", ("知识新增与审核流程", "知识版本与冲突处理流程", "知识废止与归档流程")),
}
for label, (aid, titles) in dedicated_sops.items():
    for title in titles:
        matches = [r for r in rows if r["knowledge_type"] == "SOP" and r["title"] == title and aid in ids(r["served_agents"])]
        if not matches: errors.append(f"{label}: missing dedicated SOP {title}")

coverage = read_csv(ROOT / "manifests/AGENT_COVERAGE.csv")
mapped = defaultdict(set)
for row in coverage:
    if ids(row["required_asset_ids"]): mapped[row["agent_id"]].add(row["capability"])
for aid, required in AGENT_REQUIRED_CAPABILITIES.items():
    missing = required - mapped[aid]
    if missing: errors.append(f"{aid}: capabilities without asset mapping {sorted(missing)}")

# Domain constraints intentionally allow adjacent business domains, but reject
# obviously unrelated dependencies (for example recruiting rules under tender cases).
allowed = {
    "项目管理": {"项目管理", "企业基础", "财务", "会议协同", "合同履约", "信息安全数据治理", "知识治理", "结构化业务数据", "企业文档"},
    "财务": {"财务", "结构化业务数据", "企业基础", "项目管理"},
    "会议协同": {"会议协同", "项目管理", "企业文档", "公文规范", "公共法规标准", "知识治理"},
    "招聘": {"招聘", "人力资源", "培训绩效", "企业基础", "结构化业务数据", "信息安全数据治理"},
    "采购": {"采购", "供应商", "财务", "企业基础", "公共法规标准", "结构化业务数据"},
    "供应商": {"供应商", "采购", "公共法规标准", "企业基础"},
    "招投标": {"招投标", "采购", "合同履约", "公共法规标准", "信息安全数据治理", "企业基础"},
    "合同履约": {"合同履约", "财务", "项目管理", "信息安全数据治理", "企业基础", "公共法规标准", "结构化业务数据"},
    "经营分析": {"经营分析", "财务", "结构化业务数据", "项目管理", "合同履约", "采购", "企业基础"},
    "知识治理": {"知识治理", "企业基础", "企业文档", "公共企业实践", "公共法规标准", "项目管理"},
    "公文规范": {"公文规范", "企业文档", "企业基础", "公共法规标准"},
    "信息安全数据治理": {"信息安全数据治理", "项目管理", "采购", "公共法规标准", "企业基础"},
}
for row in rows:
    if row["knowledge_type"] != "PROJECT_CASE": continue
    permitted = allowed.get(row["domain"], {row["domain"]})
    for dep in ids(row["depends_on"]):
        if dep in assets and assets[dep]["domain"] not in permitted:
            errors.append(f"{row['knowledge_id']}: dependency {dep} domain {assets[dep]['domain']} unrelated to {row['domain']}")
    if re.match(r"^P\d{3}_\d{2}$", row["knowledge_id"]):
        pid, seq = row["knowledge_id"].split("_")
        previous = f"{pid}_{int(seq)-1:02d}"
        if ids(row["depends_on"]) == [previous]:
            errors.append(f"{row['knowledge_id']}: mechanical previous-document dependency")

project_titles = defaultdict(set)
for row in rows:
    match = re.match(r"^(P\d{3})_", row["knowledge_id"])
    if match: project_titles[match.group(1)].add(row["title"].split("-", 1)[-1])
required_markers = {
    "P002": {"需求变更申请", "项目延期风险升级记录", "知识版本冲突处理记录", "人员不足资源申请", "成本超支预警", "合同付款争议记录", "项目纠偏会议纪要"},
    "P003": {"GPU采购技术规格", "算法指标专项评审", "数据安全评审", "视频数据治理说明", "技术方案变更评审", "验收指标争议纪要", "算法测试专项报告"},
    "P001": {"招标文件关键条款", "招标文件审查记录", "投标文件响应材料", "资格材料", "商务响应表", "技术参数响应表", "评分响应材料", "AI审核问题清单", "人工复核与审核结论"},
}
for pid, expected in required_markers.items():
    missing = expected - project_titles[pid]
    if missing: errors.append(f"{pid}: missing differentiated case assets {sorted(missing)}")
if project_titles["P001"] == project_titles["P002"] or project_titles["P002"] == project_titles["P003"]:
    errors.append("project case manifests remain template-identical")

fail(errors)
print("PASS: semantic dependencies, dedicated SOPs, capabilities, case domains and anti-mechanical rules are valid")
