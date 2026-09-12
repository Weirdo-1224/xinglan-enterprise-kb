"""Semantic content QA for Stage 3.1 deepened core knowledge."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import yaml

from validation_common import ROOT, fail, read_csv

CORE = ROOT / "knowledge" / "core"
SOURCES = {row["source_id"]: row for row in read_csv(ROOT / "sources/SOURCE_REGISTRY.csv")}


def parse(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8-sig")
    end = text.index("\n---\n", 4)
    return yaml.safe_load(text[4:end]), text[end + 5 :].strip()


def section(body: str, heading: str) -> str:
    match = re.search(rf"(?ms)^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)", body)
    return match.group(1).strip() if match else ""


def bullet_count(text: str) -> int:
    return len(re.findall(r"(?m)^- ", text))


assets = {meta["knowledge_id"]: (meta, body, path) for path in CORE.glob("*.md") for meta, body in [parse(path)]}
errors: list[str] = []

expected_counts = {"KB": 12, "REF": 18, "POL": 18, "SOP": 30, "FAQ": 12, "ROLE": 10}
for prefix, expected in expected_counts.items():
    actual = sum(kid.startswith(prefix) for kid in assets)
    if actual != expected:
        errors.append(f"{prefix}: {actual} files, expected {expected}")

policy_terms = {
    "POL001": ("劳动合同", "考勤", "离职"), "POL002": ("候选人", "面试", "录用"),
    "POL003": ("课程", "考核", "培训"), "POL004": ("目标", "校准", "申诉"),
    "POL005": ("WBS", "里程碑", "验收"), "POL006": ("立项", "附条件批准", "收益"),
    "POL007": ("变更请求", "影响分析", "基线"), "POL008": ("议程", "纪要", "行动项"),
    "POL009": ("版本", "电子档案", "废止"), "POL010": ("文种", "请示", "签发"),
    "POL011": ("比选", "单一来源", "验收"), "POL012": ("供应商", "准入", "退出"),
    "POL013": ("资格", "评分", "电子投标"), "POL014": ("合同", "履约", "违约"),
    "POL015": ("预算", "现金流", "会计"), "POL016": ("成本", "工时", "完工预测"),
    "POL017": ("权限", "日志", "备份"), "POL018": ("知识产权", "开源", "商业秘密"),
}
for kid, terms in policy_terms.items():
    body = assets[kid][1]
    required = ["1. 目的、对象与触发", "2. 职责分工", "3. 领域规则", "4. 审批与关键控制点", "5. 例外、停止与升级", "6. 记录与归档"]
    for heading in required:
        if not section(body, heading):
            errors.append(f"{kid}: missing or empty section {heading}")
    if bullet_count(section(body, "3. 领域规则")) < 5:
        errors.append(f"{kid}: fewer than 5 domain rules")
    missing = [term for term in terms if term not in body]
    if missing:
        errors.append(f"{kid}: missing domain terms {missing}")

for kid, (meta, body, _) in assets.items():
    if not kid.startswith("SOP"):
        continue
    for heading in ["触发条件与使用边界", "必要输入与完整性检查", "参与角色", "可执行步骤", "关键判断与分支", "输出物与完成条件", "失败路径与人工升级"]:
        if not section(body, heading):
            errors.append(f"{kid}: missing or empty section {heading}")
    if len(re.findall(r"(?m)^\d+\. ", section(body, "可执行步骤"))) < 6:
        errors.append(f"{kid}: fewer than 6 executable steps")
    if bullet_count(section(body, "必要输入与完整性检查")) < 3:
        errors.append(f"{kid}: fewer than 3 necessary inputs")
    if bullet_count(section(body, "关键判断与分支")) < 3:
        errors.append(f"{kid}: fewer than 3 decision branches")
    if "不新增金额阈值、审批权限或法律义务" not in body:
        errors.append(f"{kid}: no-new-rule guardrail missing")

faq_topics = {
    "FAQ001": ("请假", "考勤"), "FAQ002": ("面试", "候选人"), "FAQ003": ("目标", "绩效"),
    "FAQ004": ("延期", "变更"), "FAQ005": ("会议", "行动项"), "FAQ006": ("格式", "文档"),
    "FAQ007": ("采购", "万元"), "FAQ008": ("供应商", "准入"), "FAQ009": ("投标", "资格"),
    "FAQ010": ("合同", "付款"), "FAQ011": ("成本", "偏差"), "FAQ012": ("数据", "安全"),
}
for kid, terms in faq_topics.items():
    body = assets[kid][1]
    questions = re.findall(r"(?m)^### 问：(.+)$", body)
    if not 5 <= len(questions) <= 12:
        errors.append(f"{kid}: {len(questions)} questions, expected 5-12")
    if any(term not in body for term in terms):
        errors.append(f"{kid}: title/topic terms not covered: {terms}")
    answers = re.findall(r"(?ms)^答：(.*?)(?=^### 问：|^## |\Z)", body)
    if len(answers) != len(questions):
        errors.append(f"{kid}: question/answer count differs")
    for index, answer in enumerate(answers, 1):
        if "结论：" not in answer or "依据：" not in answer:
            errors.append(f"{kid}: answer {index} lacks conclusion or basis")
    bounded = sum(any(word in answer for word in ("例外", "确认", "核验", "判断", "升级", "不可以", "不能", "不得")) for answer in answers)
    if bounded < max(2, len(answers) // 3):
        errors.append(f"{kid}: too few answers state an exception/manual decision boundary")
    if "不替代上游制度" not in body or "不新增金额、比例、时限、审批层级或法律义务" not in body:
        errors.append(f"{kid}: FAQ no-new-rule boundary missing")

role_headings = ["岗位定位与所属部门", "汇报与协作关系", "核心职责", "日常任务", "专业技能", "工具与技术能力", "项目职责与权限边界", "招聘评价维度", "培训方向", "绩效关注点"]
for kid, (meta, body, _) in assets.items():
    if not kid.startswith("ROLE"):
        continue
    for heading in role_headings:
        if not section(body, heading):
            errors.append(f"{kid}: missing or empty section {heading}")
    for heading in ["核心职责", "日常任务", "专业技能", "招聘评价维度", "培训方向", "绩效关注点"]:
        if bullet_count(section(body, heading)) < 3:
            errors.append(f"{kid}: section {heading} is not specific enough")
if not all(term in assets["ROLE004"][1] for term in ("Python", "LLM", "RAG", "Agent", "向量", "模型评测", "API", "部署")):
    errors.append("ROLE004: required real AI engineering capabilities missing")

for kid, (meta, body, _) in assets.items():
    if not kid.startswith("REF"):
        continue
    match = re.search(r"Metadata applicability：([A-Z_]+)", body)
    if not match or match.group(1) != meta["applicability"]:
        errors.append(f"{kid}: metadata/body applicability mismatch")
    related_text = section(body, "关联知识")
    related = re.findall(r"\b(?:KB|POL|SOP|FAQ|ROLE)\d{3}\b", related_text)
    if len(related) != len(set(related)):
        errors.append(f"{kid}: duplicate related knowledge ID")
    if len(set(related)) < 3:
        errors.append(f"{kid}: fewer than 3 semantic related assets")
    source_ids = meta["source_ids"]
    if len(source_ids) == 1:
        expected = SOURCES[source_ids[0]]["effective_date"] or None
        actual = str(meta.get("effective_date")) if meta.get("effective_date") else None
        if actual != expected:
            errors.append(f"{kid}: effective_date {actual!r} != source {expected!r}")
    elif meta.get("effective_date") is not None:
        errors.append(f"{kid}: multi-source reference must not invent one effective_date")
    for sid in source_ids:
        if SOURCES[sid]["applicability"] == "ANALOGICAL" and "仅作方法或案例参考" not in body:
            errors.append(f"{kid}: ANALOGICAL boundary missing for {sid}")

kb008 = assets["KB008"][1]
if re.search(r"(?:20000|100000)\s*词", kb008):
    errors.append("KB008: platform unit must be 字, not 词")
for value in ("20000 字", "100000 字"):
    if value not in kb008:
        errors.append(f"KB008: platform limit missing {value}")

paragraphs: Counter[str] = Counter()
owners: dict[str, list[str]] = {}
for kid, (_, body, _) in assets.items():
    for paragraph in re.split(r"\n\s*\n", body):
        normalized = " ".join(paragraph.split())
        if len(normalized) >= 80 and not normalized.startswith(("#", "|")):
            paragraphs[normalized] += 1
            owners.setdefault(normalized, []).append(kid)
for paragraph, count in paragraphs.items():
    if count >= 4:
        errors.append(f"template paragraph repeated {count} times in {owners[paragraph][:5]}: {paragraph[:80]}")

claims = read_csv(ROOT / "manifests/CLAIM_PROVENANCE.csv")
claim_counts = Counter(row["knowledge_id"] for row in claims)
for i in range(1, 19):
    kid = f"POL{i:03d}"
    if claim_counts[kid] < 2:
        errors.append(f"{kid}: fewer than 2 provenance claims")
for kid in ("POL001", "POL002", "POL009", "POL013", "POL014", "POL015", "POL017", "POL018"):
    if not any(row["knowledge_id"] == kid and row["claim_type"] in {"EXPLICIT", "SYNTHETIC"} for row in claims):
        errors.append(f"{kid}: lacks explicit/synthetic provenance for precise rule")

lineage = read_csv(ROOT / "manifests/SOURCE_LINEAGE.csv")
lineage_keys = {(row["knowledge_id"], row["source_id"]) for row in lineage}
for kid, (meta, _, _) in assets.items():
    if not kid.startswith("ROLE"):
        continue
    for sid in [s for s in meta["source_ids"] if s.startswith("SRC-ROLE-")]:
        if (kid, sid) not in lineage_keys:
            errors.append(f"{kid}: JD source {sid} has no lineage row")

fail(errors)
print("PASS: Stage 3.1 content depth, executability, retrieval value and role realism")
print("PASS: REF applicability, effective dates and semantic links")
print("PASS: KB units, anti-template checks and critical claim provenance")
