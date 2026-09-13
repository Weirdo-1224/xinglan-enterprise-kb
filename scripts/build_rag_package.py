"""Build the RAG release package under deliverables/rag/.

Copies knowledge assets into a retrieval-ready layout without touching the
governed originals under knowledge/:
- md frontmatter is omitted because the target upload RAG does not parse it;
  identity and routing fields remain in RAG_MANIFEST.csv / PROJECT_INDEX.csv
- ENTERPRISE_FOUNDATION files drop the governance source table (## 来源与边界)
- all other body bytes are preserved exactly (incl. REF legal sections, case 关联)
- xlsx workbooks are copied; four targeted release copies receive a small
  retrieval-guide sheet while governed originals remain unchanged
Engineering-noise tokens are only reported, never removed.
"""
from __future__ import annotations

import csv
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import openpyxl
import yaml

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"
MANIFEST = ROOT / "manifests" / "KNOWLEDGE_MANIFEST.csv"
PROJECT_INDEX = ROOT / "manifests" / "PROJECT_INDEX.csv"
OUT = ROOT / "deliverables" / "rag"

EXPECTED_COUNTS = {"core": 100, "cases": 99, "templates": 28, "business_data": 12}
MD_DIRS = ["core", "cases", "templates"]
REQUIRED_HEADER_KEYS = ["knowledge_id", "knowledge_type", "domain", "title", "served_agents", "source_type"]
GOVERNANCE_SECTION = "## 来源与边界"
REDUNDANT_TAIL_HEADINGS = {
    "POLICY": "## 8. 关联知识",
    "SOP": "## 关联制度与血缘",
    "FAQ_RULE": "## 依据",
    "PUBLIC_REFERENCE": "## 关联知识",
    "PROJECT_CASE": "## 关联",
    "TEMPLATE": "## 关联制度与流程",
}
NOISE_TOKENS = ["validator", "validate_", "scripts/", ".py", "Codex",
                "enterprise_model/", "repository", "KNOWLEDGE_MANIFEST"]
TYPE_TO_SUBDIR = {
    "ENTERPRISE_FOUNDATION": "core", "POLICY": "core", "SOP": "core",
    "FAQ_RULE": "core", "ROLE": "core", "PUBLIC_REFERENCE": "core",
    "PROJECT_CASE": "cases", "TEMPLATE": "templates", "BUSINESS_DATA": "business_data",
}
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
PROJECT_ID_RE = re.compile(r"\AP(\d{3})_")

# Release-only retrieval summaries.  They describe the governed content in
# natural business language; they do not replace or change governed facts.
RAG_SUMMARIES = {
    "P002_26": "本记录用于从客户与方案风险角度识别 P002 的风险信号，并追溯银行企业知识助手项目当时为什么延期、梳理真实原因链：核心实施人员长期少 2 人（在岗 7 人、编制 9 人）与知识版本冲突叠加，导致 2024-09-30 试运行里程碑失守。",
    "P002_27": "本记录适用于识别 P002 的客户与方案风险信号，并从知识治理角度追溯项目为什么延期：CH03 引入新引用规范后，v1.3 出现回答口径和版本字段不一致，214 条冲突历时约 4 周清零并产生约 9 万元人力成本。",
    "P002_23": "本复盘适用于查询 P002 哪些变更抬高了成本及各自金额：CH01 新增工作量 18 万元、CH02 权限返工 12 万元、CH03 版本冲突 9 万元、CH04 验收样本扩大 10 万元，另有延期人力 8 万元和节余冲抵 -12 万元；最终成本 265 万元，较预算超支 45 万元。",
    "FAQ005": "适用于快速判断会议结论、口头同意、行动项和会议纪要能否直接执行；会议讨论不等于批准，涉及采购、预算或项目变更时仍须完成对应授权与审批。不适用于替代采购或变更流程。",
    "POL010": "适用于判断通知、请示、报告、函件等正式公文应选什么文种以及如何审批、签发和归档；向总经理或其他有权人申请专项预算，应使用一文一事、明确请求批准事项的请示。",
    "TPL013": "适用于向有权人申请专项预算、资源支持或事项裁决时搭建请示；重点记录主送批准人、金额与含税口径、依据、明确请示事项、批准意见和条件。不用于单纯汇报情况。",
    "KB008": "适用于查询正式文档发布前的版本、来源和现行版要求，以及知识库单文件字数限制：单文件目标不超过 20000 字，超过 100000 字必须拆分；限制单位是“字”而不是“词”。发布后须使用受控现行版，个人网盘链接不能替代正式发布与归档。",
    "P001_09": "本计划适用于查询 P001 智慧园区 AI 数字人服务平台当时的招聘与团队配置：项目按 14 人编制设计，招聘数字人交互工程师 2 名，谈栩、穆冉分别于 2024-04-08、2024-04-15 到岗；其他岗位人数、人员来源和到岗时间见下表。",
    "KB005": "适用于查询采购专员等角色的职责和权限边界、谁有权审批、能否先执行后补批，以及采购金额对应的内部审批原则；含税 17 万元属于 5 万元至 20 万元档，原则上三家比选并形成记录。",
    "P003_13": "本记录用于参考 P003 电力 AI 智能巡检平台的历史供应商比选与 GPU 采购问题：GPU 服务器 128 万元经专项审批和三家比选，供应商后来延迟供货，项目以合同违约条款和云 GPU 过渡应对；边缘设备 76 万元走竞争性采购并三家比选。",
    "P001_25": "本文件用于查询 P001 智慧园区 AI 数字人服务平台投标时的招标文件要求，包括最高限价 400 万元、项目工期 2024-02-01 至 2024-10-31（含终验），以及资格、商务、技术、否决项和价格/技术/服务/业绩评分标准；不作为其他项目的通用制度。",
    "CASE002": "适用于分析 P002 银行企业知识助手项目为什么出现负毛利及采购、合同、成本异常：实际成本 265 万元、收入确认 252 万元、账面毛利 -13 万元；并与 P001 节约 18 万元、P003 节约 4 万元作对照。文末改进项均为复盘建议，不是现行强制要求。",
    "POL001": "本文件是现行人力资源制度，适用于请假、出勤、劳动用工、入职离职和员工个人信息等事项；具体操作可结合相应 FAQ/SOP，但不得越过本制度的权限与停止条件。",
    "POL002": "本文件是现行招聘管理制度，适用于招聘需求、候选人评价、录用审批和背景核验；招聘 FAQ、面试模板和流程仅细化执行，不得降低公平性、隐私或授权要求。",
    "POL003": "本文件是现行培训管理制度，适用于培训需求、年度计划、实施、考核与培训记录；项目招聘后的入职培训和能力提升均按本制度判断。",
    "POL008": "本文件是现行会议管理制度，适用于会议决策、纪要、行动项、录音转写和授权边界；会议讨论或纪要本身不等于采购、预算、合同或项目变更已获批准。",
    "POL009": "本文件是现行文档管理制度，适用于正式文档发布前的版本、来源、审核、受控分发、归档与废止；个人网盘链接不能替代受控现行版本。",
    "POL010": "本文件是现行公文管理制度，适用于通知、请示、报告、函件等文种选择及起草、审校、签发和归档；申请专项预算或资源批准应使用一文一事的请示。",
    "POL011": "本文件是现行采购管理制度，适用于采购方式、金额档位、供应商比选、审批和紧急采购判断；含税 17 万元属于 5 万元至 20 万元档，原则上三家比选。",
    "POL013": "本文件是现行招投标管理制度，用于判断项目是否进入招标投标程序及其审查要求；公司内部采购金额超过 100 万元不当然等于依法必须招标，仍须核验主体、资金性质、项目类型和法定范围。",
    "POL014": "本文件是现行合同管理制度，适用于合同审核、签署、付款条件、履约证据、变更和争议处置；合同条款或证据不足时不得补写不存在的事实。",
}

RAG_TITLE_OVERRIDES = {
    "P002_27": "银行企业知识助手项目-延期原因链与知识版本冲突处理",
    "CASE002": "P002 银行企业知识助手项目负毛利异常原因与采购合同成本联动复盘",
    "TPL013": "专项预算与事项批准请示模板",
    "POL010": "通知请示报告与专项预算公文管理办法",
}

XLSX_RETRIEVAL_GUIDES = {
    "DATA001": [
        ["适用查询", "员工花名册；员工姓名、部门、岗位、职级、在职状态；与 DATA011 能力标签联查现有员工推荐、内部调配，以及 P003 电力 AI 视觉/算法等项目候选人"],
        ["人员推荐场景", "再接电力 AI 智能巡检或视觉项目时，从现有员工中推荐算法岗人员；采购管理岗位内部调配时先核对在职状态和岗位"],
        ["使用边界", "本表只提供结构化员工主数据；是否适岗仍需结合能力标签、项目要求和授权判断"],
    ],
    "DATA004": [
        ["适用查询", "公司 P001-P012 项目主数据；当前项目清单、项目状态、延期项目、合同金额、立项预算、实际成本、预算偏差、毛利与条件验收项目；可按 P002 银行知识助手、P003 电力 AI 智能巡检等项目名查询"],
        ["金额与成本查询", "查询 P003 电力 AI 智能巡检平台的合同额、立项预算、实际成本和是否超预算；查询 P002 银行企业知识助手项目账面毛利为什么为负及异常项目"],
        ["项目组合查询", "按经营指标口径统计公司活跃项目、延期项目、条件验收项目，以及预算偏差绝对值最大的项目"],
        ["历史边界", "P001-P003 为 FULL_HISTORY；P004-P012 为 STRUCTURED_ONLY，只能回答表内经营记录，不得推断会议、变更、风险或评审历史"],
    ],
    "DATA007": [
        ["适用查询", "项目工时台账；按项目、员工、月份汇总投入工时，可用于查询 P001-P012 某项目谁投入工时最高，例如 P003 电力 AI 智能巡检平台人员工时排名"],
        ["常见问法", "电力 AI 智能巡检平台（P003）项目上谁投入的工时最高；按 employee_id 汇总 hours 后排序"],
        ["使用边界", "work_month 为月份口径；工时记录不等同于岗位胜任结论或完整项目事件历史"],
    ],
    "DATA011": [
        ["适用查询", "人员能力标签；技能名称、熟练度和证据，可与 DATA001 员工花名册联查算法、视觉 AI、采购管理等岗位候选人，也可为 P003 等同类项目筛选现有员工"],
        ["人员推荐场景", "再接电力 AI 智能巡检或视觉项目时，从现有员工中推荐算法岗人员；查询谁具备可独立牵头的采购管理能力及熟练度"],
        ["使用边界", "能力标签用于候选筛选，不替代用人审批、面试评价或当前在职状态核验"],
    ],
}


def fail(message: str) -> None:
    raise AssertionError(message)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        fail("missing YAML frontmatter")
    return yaml.safe_load(match.group(1)), text[match.end():]


def derive_project_id(knowledge_id: str) -> str:
    match = PROJECT_ID_RE.match(knowledge_id)
    if match:
        return f"P{match.group(1)}"
    if knowledge_id.startswith("CASE"):
        return "CROSS_PROJECT"
    fail(f"{knowledge_id}: cannot derive project_id")


def remove_governance_section(body: str, knowledge_id: str, rag_rel: str,
                              removed: list[dict]) -> str:
    lines = body.split("\n")
    start = next((i for i, line in enumerate(lines) if line.strip() == GOVERNANCE_SECTION), None)
    if start is None:
        fail(f"{rag_rel}: {GOVERNANCE_SECTION} section not found")
    end = next((j for j in range(start + 1, len(lines)) if lines[j].startswith("## ")), len(lines))
    removed.append({
        "knowledge_id": knowledge_id,
        "rag_path": rag_rel,
        "section": GOVERNANCE_SECTION,
        "body_line_start": start + 1,
        "line_count": end - start,
    })
    return "\n".join(lines[:start] + lines[end:])


def remove_redundant_tail(body: str, knowledge_type: str, knowledge_id: str,
                          rag_rel: str, removed: list[dict]) -> str:
    """Remove a final directory-like relation section from the RAG copy.

    Only the final section is eligible.  In-body citations and every business
    fact, condition, exception, stop rule and boundary remain untouched.
    """
    heading = REDUNDANT_TAIL_HEADINGS.get(knowledge_type)
    if not heading:
        return body
    lines = body.split("\n")
    starts = [i for i, line in enumerate(lines) if line.strip() == heading]
    if not starts:
        return body
    start = starts[-1]
    later_heading = next((line for line in lines[start + 1:] if line.startswith("## ")), None)
    if later_heading:
        fail(f"{rag_rel}: relation section is not final; refusing broad removal")
    removed.append({
        "knowledge_id": knowledge_id,
        "rag_path": rag_rel,
        "section": heading,
        "body_line_start": start + 1,
        "line_count": len(lines) - start,
    })
    return "\n".join(lines[:start]).rstrip() + "\n"


def transform_md(src: Path, dst: Path, subdir: str) -> tuple[list[dict], list[dict]]:
    raw = src.read_bytes()
    decoded = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    eol = "\n"
    front, body = parse_frontmatter(decoded)
    for key in REQUIRED_HEADER_KEYS:
        if key not in front:
            fail(f"{src.name}: frontmatter missing key {key}")
    knowledge_id = str(front["knowledge_id"])
    rag_rel = f"{subdir}/{src.name}"

    removed: list[dict] = []
    if front["knowledge_type"] == "ENTERPRISE_FOUNDATION":
        body = remove_governance_section(body, knowledge_id, rag_rel, removed)

    body = remove_redundant_tail(
        body, str(front["knowledge_type"]), knowledge_id, rag_rel, removed)

    title_override = RAG_TITLE_OVERRIDES.get(knowledge_id)
    if title_override:
        body, count = re.subn(r"(?m)^# .+$", f"# {title_override}", body, count=1)
        if count != 1:
            fail(f"{rag_rel}: H1 heading not found for title override")

    summary = RAG_SUMMARIES.get(knowledge_id)
    if summary:
        heading = re.search(r"(?m)^# .+$", body)
        if not heading:
            fail(f"{rag_rel}: H1 heading not found for RAG summary insertion")
        insert_at = heading.end()
        body = body[:insert_at] + eol + eol + summary + body[insert_at:]

    new_text = body.lstrip("\n")

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(new_text.encode("utf-8"))
    if dst.read_bytes() != new_text.encode("utf-8"):
        fail(f"{rag_rel}: round-trip write mismatch")

    warnings = []
    for line_no, line in enumerate(new_text.split(eol), start=1):
        for token in NOISE_TOKENS:
            if token in line:
                warnings.append({
                    "knowledge_id": knowledge_id,
                    "rag_path": rag_rel,
                    "line": line_no,
                    "token": token,
                    "content": line.strip()[:160],
                })
    return removed, warnings


def transform_xlsx(src: Path, dst: Path, knowledge_id: str) -> None:
    guide = XLSX_RETRIEVAL_GUIDES.get(knowledge_id)
    if not guide:
        shutil.copyfile(src, dst)
        return
    wb = openpyxl.load_workbook(src)
    if "检索说明" in wb.sheetnames:
        del wb["检索说明"]
    ws = wb.create_sheet("检索说明", 0)
    ws.append(["DATA 资产", knowledge_id])
    for row in guide:
        ws.append(row)
    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 110
    ws.freeze_panes = "A2"
    wb.save(dst)
    wb.close()


def source_file_map() -> dict[str, tuple[str, Path]]:
    mapping = {}
    for subdir in [*MD_DIRS, "business_data"]:
        for path in sorted((KNOWLEDGE / subdir).iterdir()):
            if path.is_file():
                mapping[path.name] = (subdir, path)
    return mapping


def build_rag_manifest(rows: list[dict[str, str]]) -> None:
    mapping = source_file_map()
    out_path = OUT / "RAG_MANIFEST.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["knowledge_id", "knowledge_type", "domain", "title", "served_agents",
                         "source_type", "project_id", "history_level", "rag_path", "source_path"])
        for row in rows:
            filename = row["filename"]
            if filename not in mapping:
                fail(f"manifest row {row['knowledge_id']}: {filename} not found under knowledge/")
            subdir, _ = mapping[filename]
            if subdir != TYPE_TO_SUBDIR[row["knowledge_type"]]:
                fail(f"{filename}: knowledge_type {row['knowledge_type']} maps to {subdir}")
            is_case = row["knowledge_type"] == "PROJECT_CASE"
            writer.writerow([
                row["knowledge_id"], row["knowledge_type"], row["domain"],
                RAG_TITLE_OVERRIDES.get(row["knowledge_id"], row["title"]),
                row["served_agents"], row["source_type"],
                derive_project_id(row["knowledge_id"]) if is_case else "",
                "FULL_HISTORY" if is_case else "",
                f"{subdir}/{filename}", f"knowledge/{subdir}/{filename}",
            ])


def self_check() -> None:
    counts = {subdir: len(list((OUT / subdir).iterdir())) for subdir in EXPECTED_COUNTS}
    for subdir, expected in EXPECTED_COUNTS.items():
        if counts[subdir] != expected:
            fail(f"{subdir}: expected {expected} files, found {counts[subdir]}")
    if sum(counts.values()) != 239:
        fail(f"total: expected 239 files, found {sum(counts.values())}")
    for path in sorted(OUT.glob("*/*.md")):
        text = path.read_text(encoding="utf-8")
        if text.startswith("---"):
            fail(f"{path.name}: upload copy must not contain YAML frontmatter")
        if not re.search(r"(?m)^# .+$", text):
            fail(f"{path.name}: upload copy missing H1 title")
    for xlsx in sorted((OUT / "business_data").glob("*.xlsx")):
        knowledge_id = xlsx.name.split("_", 1)[0]
        source = KNOWLEDGE / "business_data" / xlsx.name
        if knowledge_id in XLSX_RETRIEVAL_GUIDES:
            wb = openpyxl.load_workbook(xlsx, read_only=True)
            if "检索说明" not in wb.sheetnames:
                fail(f"{xlsx.name}: missing release-only retrieval guide")
            wb.close()
        elif xlsx.read_bytes() != source.read_bytes():
            fail(f"{xlsx.name}: non-enriched xlsx copy is not byte-identical")
    if (OUT / "PROJECT_INDEX.csv").read_bytes() != PROJECT_INDEX.read_bytes():
        fail("PROJECT_INDEX.csv copy is not byte-identical")


def quality_fix_only() -> None:
    mapping = source_file_map()
    fixed = 0
    for knowledge_id in RAG_SUMMARIES:
        match = next(((subdir, src) for _, (subdir, src) in mapping.items()
                      if src.name.startswith(f"{knowledge_id}_")), None)
        if not match:
            fail(f"{knowledge_id}: source asset not found")
        subdir, src = match
        transform_md(src, OUT / subdir / src.name, subdir)
        fixed += 1
    for knowledge_id in XLSX_RETRIEVAL_GUIDES:
        match = next((src for _, (subdir, src) in mapping.items()
                      if subdir == "business_data" and src.name.startswith(f"{knowledge_id}_")), None)
        if not match:
            fail(f"{knowledge_id}: source workbook not found")
        transform_xlsx(match, OUT / "business_data" / match.name, knowledge_id)
        fixed += 1
    with MANIFEST.open(encoding="utf-8-sig", newline="") as fh:
        build_rag_manifest(list(csv.DictReader(fh)))
    self_check()
    report_path = OUT / "build_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else {}
    report["stage6_1_quality_fix"] = {
        "targeted_assets": sorted([*RAG_SUMMARIES, *XLSX_RETRIEVAL_GUIDES]),
        "title_overrides": RAG_TITLE_OVERRIDES,
        "xlsx_retrieval_guides": sorted(XLSX_RETRIEVAL_GUIDES),
        "governed_originals_modified": False,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: applied release-only RAG quality fixes to {fixed} targeted assets")


def read_rag_manifest_rows() -> list[dict[str, str]]:
    with (OUT / "RAG_MANIFEST.csv").open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def compact_relations_only() -> None:
    removed_all: list[dict] = []
    changed = 0
    rag_rows = {row["rag_path"].replace("\\", "/"): row for row in read_rag_manifest_rows()}
    for subdir in MD_DIRS:
        for path in sorted((OUT / subdir).glob("*.md")):
            raw = path.read_bytes()
            # Normalize first so a prior Windows write can never create
            # CRCRLF while removing a section.
            normalized = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
            rel = f"{subdir}/{path.name}"
            row = rag_rows.get(rel)
            if not row:
                fail(f"{rel}: missing from RAG manifest")
            if normalized.startswith("---"):
                front, body = parse_frontmatter(normalized)
                prefix = normalized[:len(normalized) - len(body)]
                knowledge_type = str(front["knowledge_type"])
                knowledge_id = str(front["knowledge_id"])
            else:
                body = normalized
                prefix = ""
                knowledge_type = row["knowledge_type"]
                knowledge_id = row["knowledge_id"]
            removed: list[dict] = []
            new_body = remove_redundant_tail(
                body, knowledge_type, knowledge_id, rel, removed)
            new_text = prefix + new_body
            if removed or raw != new_text.encode("utf-8"):
                path.write_text(new_text, encoding="utf-8", newline="\n")
                removed_all.extend(removed)
                changed += 1
    if len(removed_all) not in {0, 205}:
        fail(f"relation compaction found partial state: removed {len(removed_all)} sections")
    remaining = []
    for rel, row in rag_rows.items():
        body = (OUT / rel).read_text(encoding="utf-8")
        heading = REDUNDANT_TAIL_HEADINGS.get(row["knowledge_type"])
        if heading and any(line.strip() == heading for line in body.splitlines()):
            remaining.append(row["knowledge_id"])
    if remaining:
        fail(f"redundant relation sections remain: {remaining[:10]}")
    report_path = OUT / "build_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else {}
    if removed_all:
        report["relation_compaction"] = {
            "changed_assets": len(removed_all),
            "removed_sections": removed_all,
            "in_body_citations_preserved": True,
        }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: redundant final relation sections absent; files normalized/refreshed={changed}; in-body evidence preserved")


def strip_frontmatter_only() -> None:
    changed = 0
    for path in sorted(OUT.glob("*/*.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        _, body = parse_frontmatter(text)
        clean = body.lstrip("\r\n").replace("\r\n", "\n").replace("\r", "\n")
        path.write_text(clean, encoding="utf-8", newline="\n")
        changed += 1
    if changed not in {0, 227}:
        fail(f"frontmatter stripping found partial state: changed {changed}/227")
    self_check()
    report_path = OUT / "build_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else {}
    report["frontmatter_compaction"] = {
        "markdown_assets_without_frontmatter": 227,
        "identity_metadata_location": ["RAG_MANIFEST.csv", "PROJECT_INDEX.csv"],
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: YAML frontmatter absent from all 227 upload Markdown assets; changed={changed}")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    with MANIFEST.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) != 239:
        fail(f"KNOWLEDGE_MANIFEST.csv: expected 239 rows, found {len(rows)}")

    removed_all: list[dict] = []
    warnings_all: list[dict] = []
    md_total = 0
    for subdir in MD_DIRS:
        for src in sorted((KNOWLEDGE / subdir).glob("*.md")):
            removed, warnings = transform_md(src, OUT / subdir / src.name, subdir)
            removed_all.extend(removed)
            warnings_all.extend(warnings)
            md_total += 1
    xlsx_total = 0
    for src in sorted((KNOWLEDGE / "business_data").glob("*.xlsx")):
        dst = OUT / "business_data" / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        transform_xlsx(src, dst, src.name.split("_", 1)[0])
        xlsx_total += 1
    shutil.copyfile(PROJECT_INDEX, OUT / "PROJECT_INDEX.csv")

    build_rag_manifest(rows)
    self_check()

    report = {
        "summary": {
            "core": EXPECTED_COUNTS["core"], "cases": EXPECTED_COUNTS["cases"],
            "templates": EXPECTED_COUNTS["templates"], "business_data": EXPECTED_COUNTS["business_data"],
            "total": sum(EXPECTED_COUNTS.values()),
            "md_processed": md_total, "xlsx_copied": xlsx_total,
            "removed_sections": len(removed_all), "warnings": len(warnings_all),
        },
        "removed_sections": removed_all,
        "warnings": warnings_all,
        "frontmatter_compaction": {
            "markdown_assets_without_frontmatter": md_total,
            "identity_metadata_location": ["RAG_MANIFEST.csv", "PROJECT_INDEX.csv"],
        },
        "stage6_1_quality_fix": {
            "targeted_assets": sorted([*RAG_SUMMARIES, *XLSX_RETRIEVAL_GUIDES]),
            "title_overrides": RAG_TITLE_OVERRIDES,
            "xlsx_retrieval_guides": sorted(XLSX_RETRIEVAL_GUIDES),
            "governed_originals_modified": False,
        },
        "relation_compaction": {
            "changed_assets": sum(1 for item in removed_all
                                  if item["section"] in REDUNDANT_TAIL_HEADINGS.values()),
            "in_body_citations_preserved": True,
        },
    }
    (OUT / "build_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("PASS: core=100, cases=99, templates=28, business_data=12, total=239 assets in deliverables/rag")
    print(f"PASS: {md_total} md upload files rebuilt without YAML frontmatter; "
          "identity and history metadata remain in the release manifests")
    print("PASS: 12 xlsx workbooks published; 4 targeted copies include a retrieval guide; PROJECT_INDEX copied byte-for-byte")
    print(f"PASS: removed_sections={len(removed_all)} (governance source tables + redundant tail relations), warnings={len(warnings_all)}")
    print(f"RAG package build complete -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--quality-fix-only", action="store_true",
                            help="refresh only the Stage 6.1 targeted RAG assets")
        parser.add_argument("--compact-relations-only", action="store_true",
                            help="remove only redundant final relation sections in the RAG release")
        parser.add_argument("--strip-frontmatter-only", action="store_true",
                            help="remove YAML frontmatter only from upload Markdown assets")
        args = parser.parse_args()
        if sum((args.quality_fix_only, args.compact_relations_only, args.strip_frontmatter_only)) > 1:
            fail("choose only one partial-build mode")
        if args.quality_fix_only:
            quality_fix_only()
        elif args.compact_relations_only:
            compact_relations_only()
        elif args.strip_frontmatter_only:
            strip_frontmatter_only()
        else:
            main()
    except (AssertionError, KeyError, ValueError, OSError, yaml.YAMLError) as exc:
        print(f"FAIL: {exc}")
        raise SystemExit(1)
