"""Validate Stage 5 business-data workbooks and reusable templates."""
from __future__ import annotations

import csv
import json
import re
import sys
import zipfile
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests" / "KNOWLEDGE_MANIFEST.csv"
DATA_DIR = ROOT / "knowledge" / "business_data"
TEMPLATE_DIR = ROOT / "knowledge" / "templates"
DATA_SCHEMA = json.loads((ROOT / "schemas" / "business_data.schema.json").read_text(encoding="utf-8"))
META_SCHEMA = json.loads((ROOT / "schemas" / "knowledge_metadata.schema.json").read_text(encoding="utf-8"))
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main", "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships", "p": "http://schemas.openxmlformats.org/package/2006/relationships"}

MIN_ROWS = {
    "DATA001": 286, "DATA002": 20, "DATA003": 20, "DATA004": 12,
    "DATA005": 20, "DATA006": 30, "DATA007": 500, "DATA008": 60,
    "DATA009": 50, "DATA010": 30, "DATA011": 500, "DATA012": 30,
}
PRIMARY_KEYS = {
    "DATA001": "employee_id", "DATA002": "customer_id", "DATA003": "supplier_id",
    "DATA004": "project_id", "DATA005": "contract_id", "DATA006": "procurement_id",
    "DATA007": "timesheet_id", "DATA008": "cost_id", "DATA009": "budget_line_id",
    "DATA010": "revenue_id", "DATA011": "skill_tag_id", "DATA012": "metric_id",
}
DEPARTMENTS = {f"D{i:02d}" for i in range(1, 9)}
REQUIRED_TEMPLATE_SECTIONS = [
    "使用场景与边界", "适用角色", "文档控制", "必填字段", "可选字段", "填写规则",
    "状态与审批信息", "输出结构", "检查清单", "关联制度与流程",
]

# Stage 5.1 realism rules
AS_OF = date(2026, 9, 12)
EXCEL_EPOCH = date(1899, 12, 30)
DATASET_NAMES = {
    "员工花名册": "DATA001", "客户主数据": "DATA002", "供应商主数据": "DATA003",
    "项目主数据": "DATA004", "合同台账": "DATA005", "采购订单台账": "DATA006",
    "项目工时台账": "DATA007", "项目成本台账": "DATA008", "年度预算台账": "DATA009",
    "项目收入台账": "DATA010", "人员能力标签": "DATA011", "经营指标字典": "DATA012",
}
ALLOWED_SKILLS = {
    "D01": {"解决方案设计", "需求分析", "项目管理", "文档规范"},
    "D02": {"Java开发", "Python开发", "算法建模", "知识工程", "数据治理", "测试管理", "需求分析", "解决方案设计", "项目管理", "文档规范"},
    "D03": {"项目管理", "需求分析", "实施交付", "解决方案设计", "数据治理", "测试管理", "知识工程", "文档规范"},
    "D04": {"采购管理", "合同审查", "预算分析", "项目管理", "文档规范"},
    "D05": {"招聘面试", "培训设计", "项目管理", "文档规范"},
    "D06": {"预算分析", "合同审查", "项目管理", "文档规范"},
    "D07": {"合同审查", "数据治理", "项目管理", "文档规范"},
    "D08": {"文档规范", "培训设计", "采购管理", "预算分析", "项目管理"},
}
PM_CAPABLE_POSITIONS = {"项目经理", "实施顾问", "交付工程师", "质量经理", "数据治理工程师"}
MANAGER_LEVELS = {"M1", "P3", "P4"}
COST_PROCUREMENT_COMPAT = {
    "设备采购": {"设备"}, "测试环境采购": {"云服务"}, "GPU服务器采购": {"GPU与服务器"},
    "边缘设备采购": {"边缘设备"}, "软硬件采购": {"办公设备", "网络设备", "GPU与服务器", "边缘设备"},
    "云服务与许可": {"云服务", "软件许可", "数据服务"}, "外包服务": {"实施服务"}, "外包实施": {"实施服务"},
}
MANDATORY_COST_LINKS = {"设备采购", "测试环境采购", "GPU服务器采购", "边缘设备采购"}
FORMULA_KEYWORDS = {"SUM", "COUNT", "COUNT_DISTINCT", "MAX", "MIN", "AVG", "TOP5",
                    "GROUP", "BY", "WHERE", "AND", "OR", "NOT", "IN", "NULL"}


def fail(message: str) -> None:
    raise AssertionError(message)


def manifest_rows(kind: str) -> list[dict[str, str]]:
    with MANIFEST.open(encoding="utf-8-sig", newline="") as fh:
        return [row for row in csv.DictReader(fh) if row["knowledge_type"] == kind]


def col_index(cell_ref: str) -> int:
    letters = re.match(r"[A-Z]+", cell_ref).group(0)
    value = 0
    for ch in letters:
        value = value * 26 + ord(ch) - 64
    return value - 1


def read_xlsx(path: Path) -> dict[str, list[list[object]]]:
    with zipfile.ZipFile(path) as zf:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            shared = ["".join(node.text or "" for node in si.findall(".//m:t", NS)) for si in root.findall("m:si", NS)]
        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels.findall("p:Relationship", NS)}
        sheets: dict[str, list[list[object]]] = {}
        for sheet in workbook.findall("m:sheets/m:sheet", NS):
            name = sheet.attrib["name"]
            target = rel_map[sheet.attrib[f"{{{NS['r']}}}id"]].lstrip("/")
            xml_path = target if target.startswith("xl/") else "xl/" + target
            root = ET.fromstring(zf.read(xml_path))
            output: list[list[object]] = []
            for row in root.findall("m:sheetData/m:row", NS):
                values: dict[int, object] = {}
                for cell in row.findall("m:c", NS):
                    idx = col_index(cell.attrib["r"])
                    kind = cell.attrib.get("t")
                    value_node = cell.find("m:v", NS)
                    raw = value_node.text if value_node is not None else None
                    if kind == "s" and raw is not None:
                        value: object = shared[int(raw)]
                    elif kind == "inlineStr":
                        value = "".join(n.text or "" for n in cell.findall(".//m:t", NS))
                    elif kind == "b":
                        value = raw == "1"
                    elif kind in {"str", "e"}:
                        value = raw or ""
                    elif raw is None:
                        value = ""
                    else:
                        number = float(raw)
                        value = int(number) if number.is_integer() else number
                    values[idx] = value
                if values:
                    output.append([values.get(i, "") for i in range(max(values) + 1)])
            sheets[name] = output
        return sheets


def records(rows: list[list[object]]) -> list[dict[str, object]]:
    if not rows:
        return []
    headers = [str(v) for v in rows[0]]
    return [{headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))} for row in rows[1:]]


def metadata_map(rows: list[list[object]]) -> dict[str, object]:
    return {str(row[0]): row[1] if len(row) > 1 else "" for row in rows if row}


def split_ids(text: str) -> list[str]:
    return [item for item in text.split(";") if item]


def parse_front_matter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        fail("Markdown missing YAML front matter")
    parts = text.split("---\n", 2)
    if len(parts) != 3:
        fail("Malformed YAML front matter")
    return yaml.safe_load(parts[1]), parts[2]


def validate_templates(rows: list[dict[str, str]]) -> None:
    expected = {row["filename"]: row for row in rows}
    actual = {p.name for p in TEMPLATE_DIR.glob("*.md")}
    if actual != set(expected):
        fail(f"TEMPLATE filenames differ from Manifest; missing={sorted(set(expected)-actual)}, extra={sorted(actual-set(expected))}")
    for filename, row in expected.items():
        text = (TEMPLATE_DIR / filename).read_text(encoding="utf-8")
        meta, body = parse_front_matter(text)
        jsonschema.validate(meta, META_SCHEMA)
        exact = {
            "knowledge_id": row["knowledge_id"], "title": row["title"], "domain": row["domain"],
            "knowledge_type": "TEMPLATE", "priority": row["priority"], "source_type": row["source_type"],
            "source_authority": row["source_authority"], "normative_force": row["normative_force"],
            "applicability": row["applicability"],
        }
        for key, value in exact.items():
            if meta.get(key) != value:
                fail(f"{filename}: metadata {key}={meta.get(key)!r}, expected {value!r}")
        if meta["served_agents"] != split_ids(row["served_agents"]):
            fail(f"{filename}: served_agents differ from Manifest")
        if meta["business_chain_stage"] != split_ids(row["business_chain_stage"]):
            fail(f"{filename}: business_chain_stage differ from Manifest")
        if meta["depends_on"] != split_ids(row["depends_on"]):
            fail(f"{filename}: depends_on differ from Manifest")
        for section in REQUIRED_TEMPLATE_SECTIONS:
            if f"## {section}" not in body:
                fail(f"{filename}: missing section {section}")
        if body.count("| 必填 |") < 10 or len(body) < 2200:
            fail(f"{filename}: insufficient field coverage or content depth")
        for dep in meta["depends_on"]:
            if dep not in body:
                fail(f"{filename}: dependency {dep} not explained in body")
        if not all(phrase in body for phrase in ["不增加审批权限、金额阈值或法律义务", "案例", "可选"]):
            fail(f"{filename}: missing normative-boundary guardrail")
        if re.search(r"\bTODO\b|placeholder|Codex|Stage\s*[0-9]", text, re.I):
            fail(f"{filename}: engineering noise or placeholder found")
        if any(token in body for token in ["林澄", "周骁", "顾川", "智慧园区 AI 数字人服务平台", "银行企业知识助手项目", "电力 AI 智能巡检平台"]):
            fail(f"{filename}: historical case-specific value leaked into reusable template")


def validate_business_data(rows: list[dict[str, str]]) -> dict[str, list[dict[str, object]]]:
    expected = {row["filename"]: row for row in rows}
    actual = {p.name for p in DATA_DIR.glob("*.xlsx")}
    if actual != set(expected):
        fail(f"BUSINESS_DATA filenames differ from Manifest; missing={sorted(set(expected)-actual)}, extra={sorted(actual-set(expected))}")
    loaded: dict[str, list[dict[str, object]]] = {}
    for filename, row in expected.items():
        sheets = read_xlsx(DATA_DIR / filename)
        if set(sheets) != {"数据", "字段字典", "元数据"}:
            fail(f"{filename}: required sheets are 数据/字段字典/元数据")
        meta = metadata_map(sheets["元数据"])
        dataset_id = row["knowledge_id"]
        if meta.get("dataset_id") != dataset_id or meta.get("dataset_name") != row["title"]:
            fail(f"{filename}: workbook metadata differs from Manifest")
        if meta.get("filename") != filename or meta.get("synthetic_notice") is not True:
            fail(f"{filename}: filename/synthetic_notice metadata invalid")
        data_records = records(sheets["数据"])
        if len(data_records) < MIN_ROWS[dataset_id]:
            fail(f"{filename}: {len(data_records)} records below minimum {MIN_ROWS[dataset_id]}")
        if int(meta.get("record_count", -1)) != len(data_records):
            fail(f"{filename}: record_count metadata mismatch")
        primary_key = PRIMARY_KEYS[dataset_id]
        keys = [str(item.get(primary_key, "")) for item in data_records]
        if "" in keys or len(keys) != len(set(keys)):
            fail(f"{filename}: primary key {primary_key} blank or duplicate")
        if any(item.get("source_type") not in {"SYNTHETIC", "SYNTHETIC_DERIVED"} for item in data_records):
            fail(f"{filename}: invalid source_type")
        dictionary = records(sheets["字段字典"])
        headers = list(data_records[0])
        if [str(item["field"]) for item in dictionary] != headers:
            fail(f"{filename}: field dictionary does not match data columns")
        descriptor = {
            "dataset_id": dataset_id, "dataset_name": row["title"], "dataset_type": meta["dataset_type"],
            "synthetic_notice": True, "confidentiality": meta["confidentiality"],
            "fields": [{"name": str(item["field"]), "type": str(item["type"]), "description": str(item["description"])} for item in dictionary],
        }
        jsonschema.validate(descriptor, DATA_SCHEMA)
        loaded[dataset_id] = data_records
    return loaded


def values(dataset: list[dict[str, object]], field: str) -> set[str]:
    return {str(row[field]) for row in dataset if row.get(field) not in {"", None}}


def check_refs(dataset: list[dict[str, object]], field: str, allowed: set[str], label: str) -> None:
    missing = sorted(values(dataset, field) - allowed)
    if missing:
        fail(f"{label}: invalid {field} references {missing[:8]}")


def sum_by(dataset: list[dict[str, object]], key: str, amount: str) -> dict[str, float]:
    totals: dict[str, float] = {}
    for row in dataset:
        totals[str(row[key])] = totals.get(str(row[key]), 0.0) + float(row[amount])
    return totals


def validate_integrity(data: dict[str, list[dict[str, object]]]) -> None:
    employee_ids, customer_ids = values(data["DATA001"], "employee_id"), values(data["DATA002"], "customer_id")
    supplier_ids, project_ids = values(data["DATA003"], "supplier_id"), values(data["DATA004"], "project_id")
    contract_ids, procurement_ids = values(data["DATA005"], "contract_id"), values(data["DATA006"], "procurement_id")
    if len(data["DATA001"]) != 286:
        fail("Employee master must reconcile to Canonical employee_count=286")
    counts = Counter(str(row["department_id"]) for row in data["DATA001"])
    if set(counts) != DEPARTMENTS or sum(counts.values()) != 286 or min(counts.values()) <= 0:
        fail(f"Employee department distribution invalid: {dict(counts)}")
    check_refs(data["DATA001"], "manager_employee_id", employee_ids, "employee hierarchy")
    check_refs(data["DATA002"], "account_owner_employee_id", employee_ids, "customer master")
    check_refs(data["DATA004"], "customer_id", customer_ids, "project master")
    check_refs(data["DATA004"], "project_manager_employee_id", employee_ids, "project master")
    for ds, refs in {
        "DATA005": [("project_id", project_ids), ("customer_id", customer_ids), ("supplier_id", supplier_ids), ("owner_employee_id", employee_ids)],
        "DATA006": [("project_id", project_ids), ("supplier_id", supplier_ids), ("purchase_contract_id", contract_ids)],
        "DATA007": [("project_id", project_ids), ("employee_id", employee_ids), ("approver_employee_id", employee_ids)],
        "DATA008": [("project_id", project_ids), ("related_procurement_id", procurement_ids)],
        "DATA009": [("project_id", project_ids), ("owner_employee_id", employee_ids)],
        "DATA010": [("project_id", project_ids), ("contract_id", contract_ids)],
        "DATA011": [("employee_id", employee_ids), ("reviewer_employee_id", employee_ids)],
    }.items():
        for field, allowed in refs:
            check_refs(data[ds], field, allowed, ds)
    for row in data["DATA006"]:
        amount = float(row["amount"])
        expected = "简化采购" if amount < 50000 else "三家比选" if amount < 200000 else "竞争性采购" if amount < 1000000 else "公开招标或专项审批"
        if row["method"] != expected:
            fail(f"{row['procurement_id']}: method {row['method']} does not match threshold {expected}")

    canonical: dict[str, dict[str, object]] = {}
    for pid in ["P001", "P002", "P003"]:
        canonical[pid] = yaml.safe_load((ROOT / "enterprise_model" / "projects" / f"{pid}_CANONICAL_FACTS.yaml").read_text(encoding="utf-8"))
    project_map = {str(row["project_id"]): row for row in data["DATA004"]}
    cost_totals = sum_by(data["DATA008"], "project_id", "amount")
    budget_totals = sum_by(data["DATA009"], "project_id", "approved_amount")
    recognized_totals = sum_by(data["DATA010"], "project_id", "recognized_amount")
    collected_totals = sum_by(data["DATA010"], "project_id", "collected_amount")
    team_counts = {pid: len({str(row["employee_id"]) for row in data["DATA007"] if row["project_id"] == pid}) for pid in project_ids}
    for pid, fact in canonical.items():
        row = project_map[pid]
        exact = {
            "project_name": fact["project_name"], "project_manager_name": fact["project_manager"],
            "team_size": fact["team_size"], "contract_amount": fact["contract_amount"]["amount"],
            "budget_amount": fact["budget"]["amount"], "actual_cost": fact["financials"]["actual_cost"]["amount"],
            "recognized_revenue": fact["financials"]["recognized_revenue"]["amount"], "project_status": fact["final_status"],
            "acceptance_result": fact["acceptance"]["result"], "highest_risk_level": max((r["level"] for r in fact["risks"]), key=lambda v: int(v[1:])),
        }
        for field, expected in exact.items():
            if row[field] != expected:
                fail(f"{pid}: {field}={row[field]!r}, expected Canonical {expected!r}")
        if team_counts[pid] != fact["team_size"]:
            fail(f"{pid}: timesheet team count {team_counts[pid]} != {fact['team_size']}")
        if cost_totals[pid] != fact["financials"]["actual_cost"]["amount"] or budget_totals[pid] != fact["budget"]["amount"]:
            fail(f"{pid}: cost/budget ledger does not reconcile")
        if recognized_totals[pid] != fact["financials"]["recognized_revenue"]["amount"]:
            fail(f"{pid}: recognized revenue ledger does not reconcile")
        expected_collected = fact["contract_amount"]["amount"] if pid != "P002" else 2520000
        if collected_totals[pid] != expected_collected:
            fail(f"{pid}: collected amount does not reconcile")
        sales = [item for item in data["DATA005"] if item["contract_id"] == fact["contracts"][0]["contract_id"]]
        if len(sales) != 1 or sales[0]["amount"] != fact["contracts"][0]["amount"]["amount"] or sales[0]["contract_status"] != fact["contracts"][0]["status"]:
            fail(f"{pid}: canonical sales contract mismatch")
        canonical_proc = {(item["item"], item["amount"]["amount"], item["method"], item["status"]) for item in fact["procurement"]}
        actual_proc = {(item["item_name"], item["amount"], item["method"], item["status"]) for item in data["DATA006"] if item["project_id"] == pid and item["source_type"] == "SYNTHETIC_DERIVED"}
        if actual_proc != canonical_proc:
            fail(f"{pid}: procurement ledger does not match Canonical")

    text_values: list[str] = []
    for dataset in data.values():
        for row in dataset:
            text_values.extend(str(value) for value in row.values() if isinstance(value, str))
    joined = "\n".join(text_values)
    if re.search(r"\b1[3-9]\d{9}\b|\b\d{17}[0-9Xx]\b|[\w.+-]+@[\w.-]+\.\w+", joined):
        fail("Potential real phone, identity number or email found")
    if re.search(r"\bTODO\b|placeholder|Codex|Stage\s*[0-9]", joined, re.I):
        fail("Engineering noise or placeholder found in business data")


def as_date(value: object) -> date | None:
    if value in ("", None):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)):
        return EXCEL_EPOCH + timedelta(days=int(value))
    return date.fromisoformat(str(value))


def validate_realism(data: dict[str, list[dict[str, object]]]) -> None:
    employees = {str(row["employee_id"]): row for row in data["DATA001"]}
    projects = {str(row["project_id"]): row for row in data["DATA004"]}

    for row in data["DATA001"]:
        hire = as_date(row["hire_date"])
        if row["employment_status"] == "在职" and hire and hire > AS_OF:
            fail(f"{row['employee_id']}: active employee hired in the future ({hire})")

    for row in data["DATA006"]:
        request, delivery = as_date(row["request_date"]), as_date(row["delivery_date"])
        if request and request > AS_OF:
            fail(f"{row['procurement_id']}: request date {request} after as_of {AS_OF}")
        if row["status"] in {"completed", "delayed"} and (delivery is None or delivery > AS_OF):
            fail(f"{row['procurement_id']}: {row['status']} procurement delivered in the future ({delivery})")
        if row["status"] == "approved" and delivery is not None:
            fail(f"{row['procurement_id']}: approved procurement must not have a delivery date")
    for row in data["DATA005"]:
        if row["contract_status"] == "completed" and as_date(row["end_date"]) and as_date(row["end_date"]) > AS_OF:
            fail(f"{row['contract_id']}: contract completed in the future ({as_date(row['end_date'])})")
    for row in data["DATA010"]:
        if float(row["recognized_amount"] or 0) > 0:
            recognized = as_date(row["recognized_date"])
            if recognized is None or recognized > AS_OF:
                fail(f"{row['revenue_id']}: revenue recognized without a valid past recognized_date ({recognized})")
    for dataset, field in [("DATA007", "work_month"), ("DATA008", "cost_date"), ("DATA011", "last_verified_date")]:
        for row in data[dataset]:
            if as_date(row[field]) and as_date(row[field]) > AS_OF:
                fail(f"{dataset}: {field} {as_date(row[field])} after as_of {AS_OF}")

    report_counts = Counter(str(row["manager_employee_id"]) for row in data["DATA001"] if row["manager_employee_id"] not in {"", None})
    dept_roots: dict[str, list[dict[str, object]]] = {dept: [] for dept in DEPARTMENTS}
    for row in data["DATA001"]:
        eid = str(row["employee_id"])
        manager = str(row["manager_employee_id"]) if row["manager_employee_id"] not in {"", None} else ""
        if not manager:
            dept_roots[str(row["department_id"])].append(row)
        elif str(employees[manager]["department_id"]) != str(row["department_id"]):
            fail(f"{eid}: manager {manager} is in another department")
        if report_counts.get(eid, 0) > 0:
            if row["employment_type"] == "实习" or row["job_level"] not in MANAGER_LEVELS:
                fail(f"{eid}: intern or junior ({row['job_level']}) employee has {report_counts[eid]} reports")
            if report_counts[eid] > 15:
                fail(f"{eid}: span of control {report_counts[eid]} exceeds 15")
    for dept, roots in dept_roots.items():
        if len(roots) != 1:
            fail(f"{dept}: expected exactly one department root, got {len(roots)}")
        root = roots[0]
        if root["employment_type"] != "正式" or root["job_level"] != "M1":
            fail(f"{dept}: root {root['employee_id']} must be a regular M1 employee")
    root_of = {dept: str(roots[0]["employee_id"]) for dept, roots in dept_roots.items()}

    pm_of = {str(row["project_id"]): str(row["project_manager_employee_id"]) for row in data["DATA004"]}
    skills_by_emp: dict[str, set[str]] = {}
    for row in data["DATA011"]:
        skills_by_emp.setdefault(str(row["employee_id"]), set()).add(str(row["skill_name"]))
    for row in data["DATA004"]:
        pm = employees[str(row["project_manager_employee_id"])]
        if row["project_manager_name"] != pm["employee_name"]:
            fail(f"{row['project_id']}: project_manager_name does not match employee master")
        if pm["employment_type"] != "正式" or pm["employment_status"] != "在职":
            fail(f"{row['project_id']}: project manager {pm['employee_id']} is not a regular active employee")
        if pm["job_level"] not in MANAGER_LEVELS or pm["position_name"] not in PM_CAPABLE_POSITIONS:
            fail(f"{row['project_id']}: project manager {pm['employee_id']} lacks seniority/delivery capability "
                 f"({pm['position_name']}, {pm['job_level']})")
        if "项目管理" not in skills_by_emp.get(str(pm["employee_id"]), set()):
            fail(f"{row['project_id']}: project manager {pm['employee_id']} has no 项目管理 skill tag")

    for row in data["DATA007"]:
        eid, approver, pid = str(row["employee_id"]), str(row["approver_employee_id"]), str(row["project_id"])
        if eid == approver:
            fail(f"{row['timesheet_id']}: self-approved timesheet")
        pm = pm_of[pid]
        if eid == pm:
            if approver != root_of[str(employees[pm]["department_id"])]:
                fail(f"{row['timesheet_id']}: project manager timesheet must be approved by the department head")
        elif approver != pm:
            fail(f"{row['timesheet_id']}: timesheet must be approved by the project manager {pm}")

    for row in data["DATA011"]:
        emp = employees[str(row["employee_id"])]
        if str(row["skill_name"]) not in ALLOWED_SKILLS[str(emp["department_id"])]:
            fail(f"{row['skill_tag_id']}: skill {row['skill_name']} mismatches {emp['department_id']} ({emp['position_name']})")
        if str(row["reviewer_employee_id"]) == str(row["employee_id"]):
            fail(f"{row['skill_tag_id']}: self-reviewed skill tag")

    for row in data["DATA003"]:
        due = as_date(row["recheck_due_date"])
        if row["status"] == "有效" and due and due < AS_OF:
            fail(f"{row['supplier_id']}: active supplier past recheck due date {due}")
        if due and due < AS_OF and (row["status"] != "观察" or row["qualification_status"] != "附条件通过"):
            fail(f"{row['supplier_id']}: overdue recheck must be conditional-use (观察/附条件通过)")

    dataset_fields = {dsid: set(data[dsid][0]) for dsid in data}
    for row in data["DATA012"]:
        if row["status"] != "active":
            if str(row["calculation_formula"]).strip() != "N/A" or "无法由单一数据集" not in str(row["calculation_rule"]):
                fail(f"{row['metric_id']}: inactive metric must carry N/A formula and an explicit non-computable rule")
            continue
        sources = str(row["source_dataset"]).split(";")
        unknown = [name for name in sources if name not in DATASET_NAMES]
        if unknown:
            fail(f"{row['metric_id']}: unknown source_dataset {unknown}")
        allowed_fields = set().union(*(dataset_fields[DATASET_NAMES[name]] for name in sources))
        formula = re.sub(r"'[^']*'", "", str(row["calculation_formula"]))
        for token in re.findall(r"\w+(?:\.\w+)?", formula):
            if token in FORMULA_KEYWORDS or token.isdigit():
                continue
            if "." in token:
                dataset_name, field = token.split(".", 1)
                if dataset_name not in DATASET_NAMES or field not in dataset_fields[DATASET_NAMES[dataset_name]]:
                    fail(f"{row['metric_id']}: formula reference {token} does not resolve")
            elif token not in allowed_fields:
                fail(f"{row['metric_id']}: formula field {token} not present in {sources}")

    procurement = {str(row["procurement_id"]): row for row in data["DATA006"]}
    for row in data["DATA008"]:
        link = str(row["related_procurement_id"]) if row["related_procurement_id"] not in {"", None} else ""
        category = str(row["cost_category"])
        if not link:
            if category in MANDATORY_COST_LINKS:
                fail(f"{row['cost_id']}: procurement-category cost {category} must reference a procurement")
            continue
        proc = procurement.get(link)
        if proc is None or str(proc["project_id"]) != str(row["project_id"]):
            fail(f"{row['cost_id']}: related procurement {link} missing or cross-project")
        if category in COST_PROCUREMENT_COMPAT and str(proc["category"]) not in COST_PROCUREMENT_COMPAT[category]:
            fail(f"{row['cost_id']}: cost category {category} incompatible with procurement category {proc['category']}")

    for row in data["DATA004"]:
        planned_end, actual_end = as_date(row["planned_end_date"]), as_date(row["actual_end_date"])
        forecast = as_date(row["forecast_end_date"])
        if actual_end:
            if actual_end > AS_OF or row["project_status"] not in {"completed", "completed_with_issues"}:
                fail(f"{row['project_id']}: completed project status/end inconsistent ({row['project_status']}, {actual_end})")
        elif planned_end and planned_end < AS_OF:
            if row["project_status"] != "delayed" or forecast is None or forecast <= AS_OF or forecast <= planned_end:
                fail(f"{row['project_id']}: overdue project must be delayed with a future forecast_end_date")
        else:
            if row["project_status"] != "in_progress" or forecast is not None:
                fail(f"{row['project_id']}: on-track project must stay in_progress without forecast_end_date")

    def effective_end(project: dict[str, object]) -> date:
        return as_date(project["actual_end_date"]) or as_date(project["forecast_end_date"]) or as_date(project["planned_end_date"])

    for row in data["DATA006"]:
        project = projects[str(row["project_id"])]
        request = as_date(row["request_date"])
        if request and request < as_date(project["actual_start_date"]):
            fail(f"{row['procurement_id']}: requested before project start ({request})")
        if row["status"] in {"completed", "delayed"} and as_date(row["delivery_date"]) > effective_end(project):
            fail(f"{row['procurement_id']}: delivered after project lifecycle end {effective_end(project)}")
        if row["status"] == "approved" and as_date(row["committed_delivery_date"]) > effective_end(project):
            fail(f"{row['procurement_id']}: committed delivery beyond project lifecycle end {effective_end(project)}")
    for row in data["DATA005"]:
        if row["contract_type"] != "采购合同":
            continue
        project = projects[str(row["project_id"])]
        if as_date(row["sign_date"]) and as_date(row["sign_date"]) < as_date(project["actual_start_date"]):
            fail(f"{row['contract_id']}: purchase contract signed before project start")
        if row["contract_status"] == "completed" and as_date(row["end_date"]) > effective_end(project):
            fail(f"{row['contract_id']}: purchase contract ends after project lifecycle end {effective_end(project)}")

    recognized = sum_by(data["DATA010"], "project_id", "recognized_amount")
    collected = sum_by(data["DATA010"], "project_id", "collected_amount")
    for row in data["DATA004"]:
        pid = str(row["project_id"])
        if float(row["recognized_revenue"]) != recognized.get(pid, 0.0) or float(row["collected_amount"]) != collected.get(pid, 0.0):
            fail(f"{pid}: revenue ledger does not reconcile with project master")
        if float(row["outstanding_amount"]) != float(row["contract_amount"]) - collected.get(pid, 0.0):
            fail(f"{pid}: outstanding amount does not equal contract minus collected")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    templates = manifest_rows("TEMPLATE")
    business = manifest_rows("BUSINESS_DATA")
    if len(templates) != 28 or len(business) != 12:
        fail(f"Manifest Stage 5 scope invalid: TEMPLATE={len(templates)}, BUSINESS_DATA={len(business)}")
    validate_templates(templates)
    data = validate_business_data(business)
    validate_integrity(data)
    validate_realism(data)
    counts = ", ".join(f"{key}={len(data[key])}" for key in sorted(data))
    print("PASS: exactly 28 TEMPLATE and 12 BUSINESS_DATA assets match the Manifest")
    print("PASS: template metadata, field depth, policy/SOP boundaries and reusable-content checks")
    print("PASS: workbook metadata, business-data schema, primary keys and minimum record depth")
    print("PASS: employee, customer, supplier, procurement, contract, project and finance referential integrity")
    print("PASS: P001/P002/P003 Canonical amounts, managers, team sizes, statuses, risks and ledgers reconcile")
    print("PASS: no future hires/completions/recognized revenue beyond as_of_date 2026-09-12")
    print("PASS: org hierarchy has qualified M1 department roots, no intern/junior managers, span <= 15")
    print("PASS: project managers are qualified and no timesheet is self-approved")
    print("PASS: skill tags match position/department pools and supplier recheck states are realistic")
    print("PASS: metric formulas reference real fields and procurement-cost links are traceable")
    print("PASS: delayed projects carry forecast dates; project and revenue ledgers reconcile")
    print("PASS: no real-format phone/email/identity data, placeholders or engineering noise detected")
    print(f"Records: {counts}")
    print("Stage 5 business data and template validation complete")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, jsonschema.ValidationError, KeyError, ValueError, zipfile.BadZipFile) as exc:
        print(f"FAIL: {exc}")
        raise SystemExit(1)
