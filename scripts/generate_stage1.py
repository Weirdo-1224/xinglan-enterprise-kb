"""Generate Stage 1.1 manifests from an explicit, semantic asset catalog.

Every SOP/FAQ dependency and every agent capability mapping is curated below.
Do not replace these tables with numeric ID pairing.
"""
from __future__ import annotations

import csv
from pathlib import Path

from semantic_rules import AGENT_REQUIRED_CAPABILITIES

ROOT = Path(__file__).resolve().parents[1]
AGENTS = {
    "A01": "需求洞察与方案顾问", "A02": "AI项目经理", "A03": "企业知识管家",
    "A04": "智能会议协同官", "A05": "企业文档创作官", "A06": "文档规范与排版官",
    "A07": "AI招聘与人才助手", "A08": "培训绩效与员工发展助手", "A09": "智能采购顾问",
    "A10": "招投标审查官", "A11": "合同与履约风控官", "A12": "企业经营分析师",
}
CHAIN = {
    "B01": "客户需求", "B02": "需求澄清", "B03": "解决方案", "B04": "项目立项",
    "B05": "项目计划", "B06": "人员配置", "B07": "招聘", "B08": "培训",
    "B09": "采购", "B10": "招投标", "B11": "合同", "B12": "项目执行",
    "B13": "会议协同", "B14": "风险管理", "B15": "验收", "B16": "结项",
    "B17": "经营分析", "B18": "知识沉淀",
}

MANIFEST_FIELDS = [
    "knowledge_id", "filename", "title", "domain", "knowledge_type", "priority", "package",
    "served_agents", "business_chain_stage", "source_strategy", "source_type", "required_source_categories",
    "minimum_source_count", "synthetic_fields", "source_requirement", "parent_knowledge",
    "depends_on", "dependency_rationale", "source_authority", "normative_force", "applicability",
    "status", "notes",
]


def source_type_for(kid, ktype, authority):
    """Assign the planned source type without deferring classification to Stage 3."""
    if ktype == "PUBLIC_REFERENCE":
        return {"OFFICIAL": "PUBLIC_OFFICIAL", "PUBLIC_CORPORATE": "PUBLIC_CORPORATE", "PUBLIC_CASE": "PUBLIC_CASE"}[authority]
    if ktype == "ENTERPRISE_FOUNDATION":
        return "SYNTHETIC"
    if ktype == "POLICY" or ktype == "ROLE":
        return "SYNTHETIC_DERIVED"
    if ktype in {"SOP", "FAQ_RULE", "TEMPLATE"}:
        return "INTERNAL_DERIVED"
    if ktype == "PROJECT_CASE":
        return "SYNTHETIC_DERIVED" if kid.startswith("CASE") else "SYNTHETIC"
    if ktype == "BUSINESS_DATA":
        return "SYNTHETIC"
    raise ValueError(f"No source_type rule for {kid} ({ktype})")


def asset(kid, title, domain, ktype, package, agents, stages, deps="", rationale="",
          parent="", strategy="SYNTHETIC enterprise design", requirement="Internal synthetic rule",
          categories="", min_sources=0, synthetic="", authority="SYNTHETIC",
          force="NONE", applicability="DIRECT", filename=None, priority="P1", notes=""):
    prefix = {
        "ENTERPRISE_FOUNDATION": "企业基础", "PUBLIC_REFERENCE": "公开依据", "POLICY": "企业制度",
        "PROJECT_CASE": "历史项目案例", "BUSINESS_DATA": "结构化业务数据",
    }.get(ktype, domain)
    ext = ".xlsx" if ktype == "BUSINESS_DATA" else ".md"
    return {
        "knowledge_id": kid, "filename": filename or f"{kid}_{prefix}_{title}{ext}", "title": title,
        "domain": domain, "knowledge_type": ktype, "priority": priority, "package": package,
        "served_agents": ";".join(agents), "business_chain_stage": ";".join(stages),
        "source_strategy": strategy, "source_type": source_type_for(kid, ktype, authority),
        "required_source_categories": categories,
        "minimum_source_count": str(min_sources), "synthetic_fields": synthetic,
        "source_requirement": requirement, "parent_knowledge": parent,
        "depends_on": deps, "dependency_rationale": rationale,
        "source_authority": authority, "normative_force": force, "applicability": applicability,
        "status": "planned", "notes": notes,
    }


FOUNDATIONS = [
    ("公司简介", "企业基础", ["A03", "A05"], ["B01", "B18"], ""),
    ("组织架构", "企业基础", ["A02", "A03", "A07", "A08"], ["B04", "B06"], "KB001"),
    ("部门职责", "企业基础", ["A02", "A03", "A07", "A08", "A09", "A10", "A11", "A12"], ["B04", "B06", "B09", "B10", "B11"], "KB002"),
    ("项目制协作模型", "企业基础", ["A01", "A02", "A03", "A04", "A09", "A10", "A11", "A12"], ["B04", "B05", "B12", "B18"], "KB003"),
    ("权限审批基本原则", "企业基础", ["A02", "A03", "A09", "A10", "A11", "A12"], ["B04", "B09", "B10", "B11", "B14"], "KB003"),
    ("知识治理与冲突解析", "企业基础", ["A03", "A05", "A06", "A10", "A11"], ["B01", "B02", "B03", "B18"], "KB001"),
    ("数据分类分级", "信息安全数据治理", ["A03", "A09", "A10", "A11", "A12"], ["B09", "B10", "B11", "B12", "B14"], "KB006"),
    ("文档与版本规则", "企业文档", ["A03", "A05", "A06", "A10", "A11"], ["B02", "B03", "B12", "B18"], "KB006"),
    ("风险等级规则", "信息安全数据治理", ["A01", "A02", "A09", "A10", "A11", "A12"], ["B09", "B10", "B11", "B14"], "KB007"),
    ("业务术语表", "企业基础", list(AGENTS), list(CHAIN), "KB001"),
    ("企业主业务链", "企业基础", list(AGENTS), list(CHAIN), "KB004"),
    ("模拟企业与数据声明", "企业基础", list(AGENTS), ["B18"], "KB001"),
]

REFERENCES = [
    ("劳动合同相关规则", "人力资源", ["A07", "A08"], ["B06", "B07", "B08"], "OFFICIAL", "CONDITIONAL"),
    ("个人信息保护相关规则", "信息安全数据治理", ["A03", "A07", "A11"], ["B07", "B08", "B12"], "OFFICIAL", "DIRECT"),
    ("数据安全相关规则", "信息安全数据治理", ["A03", "A10", "A11", "A12"], ["B10", "B11", "B12", "B14"], "OFFICIAL", "DIRECT"),
    ("网络安全相关规则", "信息安全数据治理", ["A03", "A10", "A11"], ["B10", "B12", "B14"], "OFFICIAL", "CONDITIONAL"),
    ("政府采购基本规则", "公共法规标准", ["A09", "A10", "A11"], ["B09", "B10", "B11"], "OFFICIAL", "ANALOGICAL"),
    ("招标投标基本规则", "公共法规标准", ["A01", "A09", "A10", "A11"], ["B03", "B10", "B11"], "OFFICIAL", "CONDITIONAL"),
    ("电子招标投标规则", "公共法规标准", ["A09", "A10"], ["B09", "B10"], "OFFICIAL", "CONDITIONAL"),
    ("合同示范与民商事规则", "公共法规标准", ["A01", "A10", "A11"], ["B03", "B10", "B11"], "OFFICIAL", "CONDITIONAL"),
    ("档案管理相关规则", "公共法规标准", ["A03", "A04", "A05"], ["B13", "B16", "B18"], "OFFICIAL", "CONDITIONAL"),
    ("会计与项目成本规则", "公共法规标准", ["A02", "A12"], ["B04", "B16", "B17"], "OFFICIAL", "DIRECT"),
    ("信息安全管理体系参考", "公共法规标准", ["A03", "A10", "A11"], ["B10", "B11", "B12", "B14"], "OFFICIAL", "ANALOGICAL"),
    ("项目管理实践参考", "公共法规标准", ["A02", "A04", "A12"], ["B04", "B05", "B12", "B16"], "PUBLIC_CORPORATE", "ANALOGICAL"),
    ("采购需求编制参考", "公共法规标准", ["A01", "A09", "A10"], ["B03", "B09", "B10"], "OFFICIAL", "ANALOGICAL"),
    ("企业内部控制参考", "公共法规标准", ["A02", "A09", "A11", "A12"], ["B09", "B11", "B14", "B17"], "OFFICIAL", "ANALOGICAL"),
    ("人力资源管理实践参考", "公共企业实践", ["A07", "A08"], ["B06", "B07", "B08"], "PUBLIC_CORPORATE", "ANALOGICAL"),
    ("会议治理实践参考", "公共企业实践", ["A02", "A04", "A05"], ["B05", "B13", "B16"], "PUBLIC_CORPORATE", "ANALOGICAL"),
    ("知识管理实践参考", "公共企业实践", ["A03", "A05", "A06"], ["B12", "B16", "B18"], "PUBLIC_CORPORATE", "ANALOGICAL"),
    ("公开政企项目案例研究方法", "公共案例", ["A01", "A02", "A10", "A12"], ["B01", "B03", "B12", "B17"], "PUBLIC_CASE", "ANALOGICAL"),
]

# title, domain, agents, stages, dependencies, required source categories, synthetic fields
POLICIES = [
    ("人力资源管理办法", "人力资源", ["A03", "A07", "A08"], ["B06", "B07", "B08"], "KB003;REF001;REF002;REF015", "劳动与用工官方规则;个人信息保护规则;企业人力资源实践", "岗位体系;审批层级;员工规模"),
    ("招聘管理制度", "招聘", ["A03", "A07", "A08"], ["B06", "B07"], "POL001;REF001;REF002;REF015", "劳动相关官方规则;个人信息保护规则;企业招聘实践", "招聘审批;面试轮次;录用权限"),
    ("培训管理制度", "培训绩效", ["A03", "A07", "A08"], ["B07", "B08"], "POL001;REF015;KB003", "劳动与职业发展相关规则;企业培训实践;培训案例", "培训预算;课程分级;审批角色"),
    ("绩效管理办法", "培训绩效", ["A07", "A08", "A12"], ["B06", "B08", "B17"], "POL001;REF015;KB003", "劳动相关官方规则;企业绩效实践;绩效改进案例", "绩效周期;评分口径;审批与申诉链"),
    ("项目管理制度", "项目管理", ["A01", "A02", "A03", "A12"], ["B04", "B05", "B12", "B16"], "KB004;KB005;REF012", "项目管理标准或指南;企业项目实践;政企项目案例", "项目分级;治理角色;里程碑阈值"),
    ("项目立项管理办法", "项目管理", ["A01", "A02", "A12"], ["B03", "B04"], "POL005;POL015;KB005", "项目管理实践;企业投资或立项内控;公开项目案例", "立项门槛;审批层级;材料清单"),
    ("项目变更管理办法", "项目管理", ["A02", "A10", "A11", "A12"], ["B05", "B12", "B14", "B15"], "POL005;POL014;REF012", "项目变更实践;合同变更规则;变更争议案例", "变更等级;审批时限;影响阈值"),
    ("会议管理制度", "会议协同", ["A02", "A03", "A04", "A05"], ["B05", "B13", "B16"], "KB003;REF009;REF016", "档案管理规则;企业会议实践;项目会议案例", "会议分级;召集权限;归档时限"),
    ("文档管理制度", "企业文档", ["A03", "A04", "A05", "A06"], ["B12", "B16", "B18"], "KB006;KB008;REF009;REF017", "档案管理规则;知识管理实践;企业文档规范", "文档分类;版本编号;审批发布链"),
    ("公文管理办法", "公文规范", ["A03", "A05", "A06"], ["B13", "B18"], "POL009;KB008;REF009", "公文与档案官方规则;公开企业公文实践;格式案例", "公司版式;签发权限;模板编号"),
    ("采购管理制度", "采购", ["A02", "A09", "A10", "A11"], ["B09", "B10"], "KB005;REF005;REF013;REF014", "官方采购或招投标规则;企业采购内控实践;信息化采购案例", "采购金额阈值;审批层级;部门名称"),
    ("供应商管理制度", "供应商", ["A09", "A10", "A11", "A12"], ["B09", "B10", "B12"], "POL011;REF014;REF018", "企业内控参考;供应商管理实践;供应商风险案例", "准入评分;分级阈值;复评周期"),
    ("招投标管理制度", "招投标", ["A01", "A09", "A10", "A11"], ["B03", "B10", "B11"], "KB005;REF005;REF006;REF007", "招标投标官方规则;电子招投标规则;公开招投标案例", "内部职责;审查节点;风险分级"),
    ("合同管理制度", "合同履约", ["A01", "A02", "A10", "A11"], ["B03", "B10", "B11", "B12"], "KB005;REF008;REF014", "民商事与合同官方规则;企业合同内控实践;合同争议案例", "合同审批权限;付款节点;归档要求"),
    ("预算管理制度", "财务", ["A02", "A09", "A11", "A12"], ["B04", "B09", "B11", "B17"], "KB005;REF010;REF014", "会计与预算规则;企业预算内控;项目预算案例", "预算科目;审批阈值;滚动周期"),
    ("项目成本管理制度", "财务", ["A02", "A12"], ["B05", "B12", "B16", "B17"], "POL005;POL015;REF010", "会计与成本规则;项目成本实践;成本偏差案例", "成本口径;预警阈值;分摊规则"),
    ("信息安全管理制度", "信息安全数据治理", ["A03", "A07", "A10", "A11", "A12"], ["B10", "B11", "B12", "B14"], "KB007;REF002;REF003;REF004;REF011", "数据与个人信息官方规则;网络安全规则;信息安全标准实践", "数据分级;授权角色;处置时限"),
    ("知识产权与保密管理制度", "信息安全数据治理", ["A03", "A05", "A10", "A11"], ["B03", "B10", "B11", "B18"], "POL014;POL017;REF002;REF008", "知识产权与合同官方规则;个人信息保护规则;企业保密实践", "密级;授权范围;内部处置流程"),
]

# title, domain, agents, stages, dependencies, rationale
SOPS = [
    ("客户需求澄清流程", "项目管理", ["A01", "A02"], ["B01", "B02"], "POL005;REF012;KB011", "需求澄清受项目治理、业务链和项目实践约束。"),
    ("解决方案设计流程", "项目管理", ["A01", "A02", "A05"], ["B02", "B03"], "POL005;POL018;KB007", "方案设计需遵循项目治理、保密与数据分级。"),
    ("项目立项流程", "项目管理", ["A01", "A02", "A12"], ["B03", "B04"], "POL005;POL006;POL015;KB005", "立项同时受项目制度、预算和审批权限约束。"),
    ("WBS与里程碑编制流程", "项目管理", ["A02", "A12"], ["B04", "B05"], "POL005;POL016;REF012", "计划拆解需满足项目与成本管理要求。"),
    ("项目资源配置流程", "项目管理", ["A02", "A07", "A08"], ["B05", "B06"], "POL005;POL001;POL004;KB003", "资源配置受项目、人力、绩效与部门职责约束。"),
    ("项目启动流程", "项目管理", ["A02", "A04"], ["B04", "B05", "B13"], "POL005;POL008;KB005", "项目启动需完成治理授权和会议留痕。"),
    ("项目周报与进度管理流程", "项目管理", ["A02", "A04", "A12"], ["B05", "B12", "B13"], "POL005;POL016;POL008", "进度报告需联动项目基线、成本和会议决策。"),
    ("项目风险管理流程", "项目管理", ["A01", "A02", "A10", "A11", "A12"], ["B12", "B14"], "POL005;POL007;POL017;KB009", "风险处置需结合变更、安全制度和风险分级。"),
    ("项目变更控制流程", "项目管理", ["A01", "A02", "A10", "A11", "A12"], ["B02", "B03", "B12", "B14"], "POL005;POL007;POL014;KB005", "变更必须评估项目、合同和授权影响。"),
    ("项目验收流程", "项目管理", ["A01", "A02", "A10", "A11"], ["B15", "B16"], "POL005;POL007;POL014;KB005", "验收以项目基线、有效变更和合同条件为依据。"),
    ("项目结项与复盘流程", "项目管理", ["A02", "A03", "A12"], ["B16", "B17", "B18"], "POL005;POL016;POL009;REF009", "结项需完成经营核对、档案归集和知识沉淀。"),
    ("会议议程与纪要流程", "会议协同", ["A02", "A04", "A05"], ["B13", "B18"], "POL008;POL009;REF016", "会议产出受会议治理、文档归档和公开实践约束。"),
    ("通知请示报告写作流程", "企业文档", ["A03", "A05", "A06"], ["B13", "B16", "B18"], "POL009;POL010;KB008", "企业写作需遵循文档、公文和版本规则。"),
    ("招聘需求到录用流程", "招聘", ["A07", "A08"], ["B06", "B07"], "POL001;POL002;KB005;REF001;REF002", "招聘需同时满足用工、招聘、权限和个人信息规则。"),
    ("入职培训实施流程", "培训绩效", ["A07", "A08"], ["B07", "B08"], "POL001;POL003;REF015", "入职培训由人力与培训制度及公开实践共同约束。"),
    ("采购申请与询价流程", "采购", ["A09", "A10", "A11"], ["B09"], "POL011;POL012;POL015;KB005", "采购申请需满足采购、供应商、预算和审批规则。"),
    ("供应商比选与准入流程", "供应商", ["A09", "A10", "A11", "A12"], ["B09", "B10"], "POL011;POL012;KB005;REF014", "比选准入需联动采购制度、供应商规则与内控。"),
    ("合同审核与履约跟踪流程", "合同履约", ["A02", "A10", "A11", "A12"], ["B11", "B12", "B15", "B17"], "POL014;POL015;POL018;KB005;REF008", "合同审查与履约需覆盖授权、预算、付款、知识产权和保密。"),
    ("知识新增与审核流程", "知识治理", ["A03", "A05"], ["B18"], "POL009;KB006;KB008;REF017", "知识入库需有责任人、依据、审核和版本标识。"),
    ("知识版本与冲突处理流程", "知识治理", ["A03", "A06", "A11"], ["B18"], "POL009;KB006;KB008", "版本和冲突处理依照适用性、效力、状态、日期、具体性与权威顺序。"),
    ("知识废止与归档流程", "知识治理", ["A03", "A04", "A05"], ["B16", "B18"], "POL009;KB006;REF009", "废止知识必须停止现行使用并保留可追溯归档。"),
    ("文档格式检查流程", "公文规范", ["A05", "A06"], ["B03", "B13", "B18"], "POL009;POL010;KB008", "格式检查以文档、公文与版本规则为基线。"),
    ("文档排版流程", "公文规范", ["A05", "A06"], ["B03", "B13", "B18"], "POL009;POL010;KB008", "排版统一版式、层级、图表和可访问性要求。"),
    ("格式修复与模板套用流程", "公文规范", ["A05", "A06"], ["B03", "B13", "B18"], "POL009;POL010;KB008", "修复和套版必须保持内容语义、版本与模板一致。"),
    ("绩效目标制定流程", "培训绩效", ["A08", "A12"], ["B06", "B08", "B17"], "POL004;POL005;KB003", "目标需从岗位职责、项目目标和绩效制度分解。"),
    ("中期绩效回顾流程", "培训绩效", ["A02", "A08"], ["B08", "B12", "B17"], "POL004;SOP007;KB003", "中期回顾以目标、进度证据和职责边界为依据。"),
    ("绩效评价与反馈流程", "培训绩效", ["A07", "A08", "A12"], ["B08", "B17"], "POL004;POL001;REF015", "评价反馈需符合绩效、人力规则并保留依据。"),
    ("绩效改进计划流程", "培训绩效", ["A07", "A08"], ["B08", "B17"], "POL004;POL003;SOP027", "改进计划承接评价结果并联动培训发展。"),
    ("招标文件审查流程", "招投标", ["A01", "A09", "A10", "A11"], ["B10"], "POL013;POL014;REF005;REF006;REF007;KB009", "招标文件需审查合规、合同、评分与否决风险。"),
    ("投标文件审查流程", "招投标", ["A01", "A10", "A11"], ["B10", "B11"], "POL013;POL014;SOP029;REF006;REF007;KB009", "投标文件需逐项核对资格、商务、技术、评分和证据定位。"),
]

FAQS = [
    ("请假与出勤常见问题", "人力资源", ["A03", "A07", "A08"], ["B06", "B08"], "POL001;REF001", "请假与出勤答复必须回溯人力制度和适用劳动规则。"),
    ("招聘面试评价常见问题", "招聘", ["A07", "A08"], ["B07"], "POL002;SOP014;REF002;REF015", "面试评价来自招聘流程、隐私规则和招聘实践。"),
    ("绩效目标设定常见问题", "培训绩效", ["A07", "A08", "A12"], ["B06", "B08", "B17"], "POL004;SOP025", "绩效问答以绩效制度和目标制定流程为准。"),
    ("项目延期处理规则", "项目管理", ["A02", "A10", "A11", "A12"], ["B12", "B14", "B15"], "POL005;POL007;SOP007;SOP008", "延期处置需联动进度、风险和变更控制。"),
    ("会议决策与待办常见问题", "会议协同", ["A02", "A04", "A05"], ["B13"], "POL008;SOP012", "会议决策与待办必须以会议制度和纪要流程留痕。"),
    ("公文格式快速检查规则", "公文规范", ["A05", "A06"], ["B13", "B18"], "POL009;POL010;SOP022;KB008", "快速检查项来自文档、公文及格式检查基线。"),
    ("采购阈值适用问答", "采购", ["A09", "A10", "A11", "A12"], ["B09", "B10"], "POL011;POL015;KB005", "采购阈值是企业参数，需同时满足预算与审批权限。"),
    ("供应商准入问答", "供应商", ["A09", "A10", "A11"], ["B09"], "POL012;SOP017;REF014", "供应商答复源于准入制度、执行流程和内控参考。"),
    ("招投标完整性资格商务技术评分与风险检查规则", "招投标", ["A01", "A10", "A11"], ["B10"], "POL013;SOP029;SOP030;REF006;REF007;KB009", "规则覆盖完整性、资格、商务、技术、评分、否决风险和证据定位。"),
    ("合同付款条件检查规则", "合同履约", ["A10", "A11", "A12"], ["B11", "B12", "B17"], "POL014;POL015;SOP018", "付款条件需同时满足合同、预算和履约证据要求。"),
    ("项目成本偏差问答", "经营分析", ["A02", "A11", "A12"], ["B12", "B17"], "POL016;POL015;DATA008", "成本偏差口径来自成本、预算制度和成本台账。"),
    ("敏感数据使用问答", "信息安全数据治理", ["A03", "A10", "A11", "A12"], ["B09", "B10", "B11", "B12"], "POL017;POL018;REF002;REF003;REF004", "敏感数据使用取决于信息安全、保密和适用公共规则。"),
]

ROLES = [
    ("项目经理", "项目管理", ["A02"], ["B04", "B05", "B12", "B16"]),
    ("解决方案顾问", "项目管理", ["A01"], ["B01", "B02", "B03"]),
    ("产品经理", "企业基础", ["A01", "A02"], ["B02", "B03", "B12"]),
    ("技术与算法工程师", "信息安全数据治理", ["A01", "A02", "A11"], ["B03", "B12", "B14"]),
    ("采购专员", "采购", ["A09"], ["B09", "B10"]),
    ("HRBP与招聘专员", "招聘", ["A07", "A08"], ["B06", "B07", "B08"]),
    ("财务经理", "财务", ["A02", "A12"], ["B04", "B09", "B11", "B17"]),
    ("法务风控经理", "合同履约", ["A10", "A11"], ["B10", "B11", "B14"]),
    ("综合行政专员", "会议协同", ["A03", "A04", "A05", "A06"], ["B13", "B16", "B18"]),
    ("项目成员", "项目管理", ["A02", "A04", "A12"], ["B05", "B12", "B15"]),
]

# Common project chain. Dependencies point to relevant rules/templates, never to
# the previous project document merely because its number is adjacent.
COMMON_CASES = [
    ("客户需求说明", "项目管理", list(AGENTS), ["B01", "B02"], "SOP001;TPL002"),
    ("需求调研记录", "项目管理", ["A01", "A02", "A03", "A04", "A10", "A11", "A12"], ["B02"], "SOP001;TPL002"),
    ("需求分析报告", "项目管理", ["A01", "A02", "A10", "A11", "A12"], ["B02", "B03"], "SOP001;POL005"),
    ("解决方案", "项目管理", ["A01", "A02", "A05", "A10", "A11"], ["B03"], "SOP002;TPL003"),
    ("报价说明", "财务", ["A01", "A02", "A09", "A12"], ["B03"], "POL015;POL016"),
    ("项目立项申请", "项目管理", ["A02", "A03", "A12"], ["B04"], "SOP003;TPL001"),
    ("WBS与里程碑计划", "项目管理", ["A02", "A12"], ["B05"], "SOP004;TPL004"),
    ("项目启动会材料", "会议协同", ["A02", "A04", "A05"], ["B05", "B13"], "SOP006;SOP012"),
    ("人员配置计划", "项目管理", ["A02", "A07", "A08"], ["B06"], "SOP005;DATA011"),
    ("招聘需求", "招聘", ["A07", "A08"], ["B07"], "SOP014;TPL015"),
    ("采购申请", "采购", ["A09", "A10", "A11"], ["B09"], "SOP016;TPL018"),
    ("采购需求规格", "采购", ["A09", "A10"], ["B09"], "SOP016;REF013"),
    ("供应商比选记录", "供应商", ["A09", "A10", "A11", "A12"], ["B09", "B10"], "SOP017;TPL019"),
    ("招投标材料与审查计划", "招投标", ["A01", "A09", "A10", "A11"], ["B10"], "POL013;SOP029;SOP030"),
    ("合同审核意见", "合同履约", ["A10", "A11"], ["B11"], "SOP018;TPL020"),
    ("项目合同摘要", "合同履约", ["A10", "A11", "A12"], ["B11"], "POL014;SOP018"),
    ("项目周报汇总", "项目管理", ["A02", "A04", "A12"], ["B12", "B13"], "SOP007;TPL005"),
    ("风险台账", "项目管理", ["A02", "A10", "A11", "A12"], ["B14"], "SOP008;TPL006"),
    ("变更记录", "项目管理", ["A01", "A02", "A10", "A11"], ["B12", "B14"], "SOP009;TPL007"),
    ("验收方案", "项目管理", ["A01", "A02", "A10", "A11"], ["B15"], "SOP010;TPL008"),
    ("验收报告", "项目管理", ["A01", "A02", "A10", "A11", "A12"], ["B15"], "SOP010;POL014"),
    ("结项报告", "项目管理", ["A02", "A03", "A12"], ["B16"], "SOP011;POL005"),
    ("项目经营复盘", "经营分析", ["A02", "A11", "A12"], ["B17"], "POL016;DATA008;DATA010"),
    ("知识沉淀清单", "知识治理", list(AGENTS), ["B18"], "SOP019;SOP020;SOP021"),
]

PROJECTS = [
    ("P001", "智慧园区 AI 数字人服务平台", "优秀项目"),
    ("P002", "银行企业知识助手项目", "问题项目"),
    ("P003", "电力 AI 智能巡检平台", "复杂技术项目"),
]

PROJECT_EXTRAS = {
    "P001": [
        ("招标文件关键条款", "招投标", ["B10"], "POL013;POL014;REF006"),
        ("招标文件审查记录", "招投标", ["B10"], "SOP029;TPL026"),
        ("投标文件响应材料", "招投标", ["B10"], "SOP030;POL013"),
        ("资格材料", "招投标", ["B10"], "FAQ009;SOP030"),
        ("商务响应表", "招投标", ["B10"], "FAQ009;SOP030"),
        ("技术参数响应表", "招投标", ["B10"], "FAQ009;SOP030"),
        ("评分响应材料", "招投标", ["B10"], "FAQ009;SOP030"),
        ("AI审核问题清单", "招投标", ["B10"], "FAQ009;TPL028"),
        ("人工复核与审核结论", "招投标", ["B10"], "SOP030;TPL027;TPL028"),
    ],
    "P002": [
        ("需求变更申请", "项目管理", ["B12", "B14"], "SOP009;TPL007"),
        ("项目延期风险升级记录", "项目管理", ["B12", "B14"], "FAQ004;SOP008"),
        ("知识版本冲突处理记录", "知识治理", ["B18"], "SOP020;KB006"),
        ("人员不足资源申请", "项目管理", ["B06", "B12"], "SOP005;KB003"),
        ("成本超支预警", "经营分析", ["B14", "B17"], "POL016;DATA008"),
        ("合同付款争议记录", "合同履约", ["B11", "B14"], "FAQ010;SOP018"),
        ("项目纠偏会议纪要", "会议协同", ["B13", "B14"], "SOP012;TPL010"),
    ],
    "P003": [
        ("GPU采购技术规格", "采购", ["B09"], "SOP016;REF013"),
        ("算法指标专项评审", "项目管理", ["B12", "B15"], "SOP002;SOP010"),
        ("数据安全评审", "信息安全数据治理", ["B12", "B14"], "POL017;REF003;REF004"),
        ("视频数据治理说明", "信息安全数据治理", ["B12", "B14"], "POL017;KB007"),
        ("技术方案变更评审", "项目管理", ["B12", "B14"], "SOP009;POL007"),
        ("验收指标争议纪要", "项目管理", ["B13", "B15"], "SOP010;SOP012"),
        ("算法测试专项报告", "项目管理", ["B12", "B15"], "SOP010;POL017"),
    ],
}

CROSS_CASES = [
    ("CASE001", "需求变更与基线控制复盘", "项目管理", ["A01", "A02", "A10", "A11", "A12"], "SOP009;P001_19;P002_25;P003_29"),
    ("CASE002", "采购合同与成本联动复盘", "经营分析", ["A02", "A09", "A11", "A12"], "SOP016;SOP018;P002_29;P003_25"),
    ("CASE003", "验收指标与知识沉淀复盘", "项目管理", ["A01", "A02", "A03", "A10", "A11", "A12"], "SOP010;SOP019;P001_21;P003_30"),
    ("CASE004", "文档格式与排版正反案例", "公文规范", ["A05", "A06"], "SOP022;SOP023;SOP024;FAQ006"),
]

TEMPLATES = [
    ("项目立项模板", "项目管理", ["A01", "A02"], ["B03", "B04"], "SOP003"),
    ("需求调研模板", "项目管理", ["A01", "A02"], ["B01", "B02"], "SOP001"),
    ("解决方案模板", "企业文档", ["A01", "A05"], ["B02", "B03"], "SOP002;KB008"),
    ("WBS计划模板", "项目管理", ["A02"], ["B05"], "SOP004"),
    ("项目周报模板", "项目管理", ["A02", "A04"], ["B12", "B13"], "SOP007"),
    ("项目风险台账模板", "项目管理", ["A02", "A10", "A11"], ["B14"], "SOP008;KB009"),
    ("项目变更单模板", "项目管理", ["A02", "A10", "A11"], ["B12", "B14"], "SOP009"),
    ("验收方案模板", "项目管理", ["A01", "A02", "A10", "A11"], ["B15"], "SOP010"),
    ("会议议程模板", "会议协同", ["A02", "A04", "A05"], ["B13"], "SOP012"),
    ("会议纪要模板", "会议协同", ["A02", "A04", "A05"], ["B13", "B18"], "SOP012"),
    ("决策与待办清单模板", "会议协同", ["A02", "A04"], ["B13"], "SOP012"),
    ("通知模板", "公文规范", ["A05", "A06"], ["B13"], "SOP013;SOP023"),
    ("请示模板", "公文规范", ["A05", "A06"], ["B13"], "SOP013;SOP023"),
    ("工作报告模板", "企业文档", ["A05", "A06", "A12"], ["B16", "B17"], "SOP013;SOP023"),
    ("岗位JD模板", "招聘", ["A07", "A08"], ["B07"], "SOP014;POL002"),
    ("面试评价表模板", "招聘", ["A07", "A08"], ["B07"], "SOP014;FAQ002"),
    ("培训计划模板", "培训绩效", ["A08"], ["B08"], "SOP015;POL003"),
    ("采购申请模板", "采购", ["A09"], ["B09"], "SOP016"),
    ("供应商比选表模板", "供应商", ["A09", "A10"], ["B09", "B10"], "SOP017"),
    ("合同审查清单模板", "合同履约", ["A10", "A11"], ["B11", "B12"], "SOP018;POL014"),
    ("文档格式检查清单", "公文规范", ["A05", "A06"], ["B13", "B18"], "SOP022;FAQ006"),
    ("格式修复与模板映射记录", "公文规范", ["A06"], ["B13", "B18"], "SOP024;KB008"),
    ("绩效目标表", "培训绩效", ["A08", "A12"], ["B08", "B17"], "SOP025"),
    ("中期绩效回顾表", "培训绩效", ["A02", "A08"], ["B08", "B17"], "SOP026"),
    ("绩效评价反馈与改进计划模板", "培训绩效", ["A07", "A08"], ["B08", "B17"], "SOP027;SOP028"),
    ("招标文件审查清单", "招投标", ["A09", "A10", "A11"], ["B10"], "SOP029;FAQ009"),
    ("投标文件审核报告模板", "招投标", ["A01", "A10", "A11"], ["B10"], "SOP030;FAQ009"),
    ("招投标问题定位模板", "招投标", ["A10", "A11"], ["B10"], "SOP029;SOP030;FAQ009"),
]

DATASETS = [
    ("员工花名册", "HIGHLY_SENSITIVE", ["A07", "A08"], ["B06", "B07", "B08"]),
    ("客户主数据", "SENSITIVE", ["A01", "A02", "A12"], ["B01", "B03", "B17"]),
    ("供应商主数据", "SENSITIVE", ["A09", "A10", "A11"], ["B09", "B10"]),
    ("项目主数据", "INTERNAL", ["A02", "A03", "A12"], ["B04", "B12", "B16", "B17"]),
    ("合同台账", "HIGHLY_SENSITIVE", ["A10", "A11", "A12"], ["B11", "B12", "B17"]),
    ("采购订单台账", "SENSITIVE", ["A09", "A11", "A12"], ["B09", "B12", "B17"]),
    ("项目工时台账", "SENSITIVE", ["A02", "A08", "A12"], ["B06", "B12", "B17"]),
    ("项目成本台账", "HIGHLY_SENSITIVE", ["A02", "A11", "A12"], ["B12", "B16", "B17"]),
    ("年度预算台账", "HIGHLY_SENSITIVE", ["A02", "A11", "A12"], ["B04", "B17"]),
    ("项目收入台账", "HIGHLY_SENSITIVE", ["A02", "A11", "A12"], ["B11", "B16", "B17"]),
    ("人员能力标签", "SENSITIVE", ["A07", "A08", "A02"], ["B06", "B07", "B08"]),
    ("经营指标字典", "INTERNAL", ["A02", "A03", "A12"], ["B17", "B18"]),
]

# capability|Chinese label, required knowledge types, required asset IDs
COVERAGE_SPECS = {
    "A01": [
        ("needs_discovery|需求识别与澄清", "SOP;TEMPLATE;PROJECT_CASE", "SOP001;TPL002;P001_02"),
        ("solution_design|解决方案设计", "SOP;TEMPLATE;PROJECT_CASE", "SOP002;TPL003;P001_04"),
        ("scope_baseline|范围与需求基线", "POLICY;SOP;PROJECT_CASE", "POL005;SOP009;P002_25"),
        ("proposal_evidence|方案证据组织", "PUBLIC_REFERENCE;PROJECT_CASE", "REF018;P001_04"),
        ("bid_collaboration|投标协同", "POLICY;SOP;PROJECT_CASE", "POL013;SOP029;P001_25"),
        ("customer_risk|客户与方案风险", "ENTERPRISE_FOUNDATION;SOP;PROJECT_CASE", "KB009;SOP008;P002_26"),
    ],
    "A02": [
        ("project_initiation|项目立项", "POLICY;SOP;TEMPLATE", "POL005;SOP003;TPL001"),
        ("wbs_milestones|WBS与里程碑", "SOP;TEMPLATE;PROJECT_CASE", "SOP004;TPL004;P001_07"),
        ("resource_planning|资源配置", "SOP;BUSINESS_DATA", "SOP005;DATA007;DATA011"),
        ("progress_control|进度管理", "SOP;TEMPLATE;PROJECT_CASE", "SOP007;TPL005;P002_26"),
        ("risk_control|风险管理", "SOP;TEMPLATE;PROJECT_CASE", "SOP008;TPL006;P003_27"),
        ("change_control|变更管理", "POLICY;SOP;TEMPLATE", "POL007;SOP009;TPL007"),
        ("meeting_coordination|会议协同", "SOP;TEMPLATE", "SOP012;TPL009;TPL010"),
        ("acceptance_closeout|验收结项", "SOP;TEMPLATE;PROJECT_CASE", "SOP010;SOP011;TPL008;P003_30"),
    ],
    "A03": [
        ("knowledge_governance|知识治理", "ENTERPRISE_FOUNDATION;POLICY", "KB006;POL009"),
        ("knowledge_intake_review|知识新增审核", "SOP;PROJECT_CASE", "SOP019;P001_24"),
        ("version_conflict_control|版本与冲突", "SOP;PROJECT_CASE", "SOP020;P002_27"),
        ("knowledge_retirement|知识废止归档", "SOP;PUBLIC_REFERENCE", "SOP021;REF009"),
        ("knowledge_capture|知识沉淀", "SOP;PROJECT_CASE", "SOP011;P003_24"),
        ("faq_retrieval|FAQ检索", "FAQ_RULE;ENTERPRISE_FOUNDATION", "FAQ001;FAQ012;KB010"),
        ("cross_domain_retrieval|跨域检索", "ENTERPRISE_FOUNDATION;BUSINESS_DATA", "KB003;KB011;DATA012"),
    ],
    "A04": [
        ("meeting_planning|会议规划", "POLICY;SOP;TEMPLATE", "POL008;SOP012;TPL009"),
        ("minutes_generation|纪要生成", "SOP;TEMPLATE;PROJECT_CASE", "SOP012;TPL010;P001_08"),
        ("decision_tracking|决策跟踪", "FAQ_RULE;TEMPLATE", "FAQ005;TPL011"),
        ("action_followup|待办跟进", "SOP;TEMPLATE", "SOP007;TPL011"),
        ("project_coordination|项目协调", "ENTERPRISE_FOUNDATION;SOP", "KB004;SOP006"),
        ("meeting_archiving|会议归档", "POLICY;SOP;PUBLIC_REFERENCE", "POL009;SOP021;REF009"),
    ],
    "A05": [
        ("business_writing|企业文档写作", "POLICY;SOP;TEMPLATE", "POL009;SOP013;TPL014"),
        ("solution_document|方案文档", "SOP;TEMPLATE;PROJECT_CASE", "SOP002;TPL003;P001_04"),
        ("meeting_document|会议文档", "SOP;TEMPLATE", "SOP012;TPL009;TPL010"),
        ("template_drafting|模板化创作", "ENTERPRISE_FOUNDATION;SOP;TEMPLATE", "KB008;SOP024;TPL012"),
        ("evidence_based_drafting|依据驱动写作", "ENTERPRISE_FOUNDATION;PUBLIC_REFERENCE", "KB006;REF017"),
        ("document_archiving|文档归档", "POLICY;SOP;PUBLIC_REFERENCE", "POL009;SOP021;REF009"),
    ],
    "A06": [
        ("document_format_rules|文档格式规则", "ENTERPRISE_FOUNDATION;POLICY", "KB008;POL009;POL010"),
        ("format_inspection|格式检查", "SOP;FAQ_RULE;TEMPLATE", "SOP022;FAQ006;TPL021"),
        ("typesetting|文档排版", "SOP;TEMPLATE", "SOP023;TPL012;TPL014"),
        ("template_application|模板套用", "SOP;TEMPLATE", "SOP024;TPL022"),
        ("format_repair|格式修复", "SOP;TEMPLATE", "SOP024;TPL021;TPL022"),
        ("positive_negative_examples|正反案例", "PROJECT_CASE;FAQ_RULE", "CASE004;FAQ006"),
    ],
    "A07": [
        ("workforce_request|用人需求", "POLICY;SOP;PROJECT_CASE", "POL001;SOP005;P001_10"),
        ("job_description|岗位说明", "ROLE;TEMPLATE", "ROLE006;TPL015"),
        ("candidate_screening|候选人筛选", "POLICY;SOP;PUBLIC_REFERENCE", "POL002;SOP014;REF015"),
        ("interview_evaluation|面试评价", "FAQ_RULE;TEMPLATE", "FAQ002;TPL016"),
        ("offer_onboarding|录用入职", "POLICY;SOP", "POL002;SOP014;SOP015"),
        ("privacy_compliance|招聘隐私合规", "POLICY;PUBLIC_REFERENCE", "POL017;REF002"),
    ],
    "A08": [
        ("training_governance|培训制度", "POLICY;TEMPLATE", "POL003;TPL017"),
        ("training_delivery|培训实施", "SOP;PROJECT_CASE", "SOP015;P001_09"),
        ("competency_model|能力模型", "ENTERPRISE_FOUNDATION;ROLE;BUSINESS_DATA", "KB003;ROLE006;DATA011"),
        ("performance_governance|绩效制度", "POLICY;PUBLIC_REFERENCE", "POL004;REF015"),
        ("goal_setting|目标制定", "SOP;TEMPLATE;FAQ_RULE", "SOP025;TPL023;FAQ003"),
        ("midterm_review|中期回顾", "SOP;TEMPLATE", "SOP026;TPL024"),
        ("evaluation_feedback|评价反馈", "SOP;TEMPLATE", "SOP027;TPL025"),
        ("improvement_plan|绩效改进", "SOP;TEMPLATE", "SOP028;TPL025"),
    ],
    "A09": [
        ("purchase_request|采购申请", "POLICY;SOP;TEMPLATE", "POL011;SOP016;TPL018"),
        ("sourcing_method|采购方式判断", "ENTERPRISE_FOUNDATION;POLICY;FAQ_RULE", "KB005;POL011;FAQ007"),
        ("supplier_admission|供应商准入", "POLICY;SOP;FAQ_RULE", "POL012;SOP017;FAQ008"),
        ("supplier_comparison|供应商比选", "SOP;TEMPLATE;PROJECT_CASE", "SOP017;TPL019;P001_13"),
        ("procurement_risk|采购风险", "ENTERPRISE_FOUNDATION;POLICY;PUBLIC_REFERENCE", "KB009;POL011;REF014"),
        ("purchase_tracking|采购跟踪", "BUSINESS_DATA;PROJECT_CASE", "DATA003;DATA006;P003_25"),
    ],
    "A10": [
        ("tender_document_review|招标文件审查", "POLICY;SOP;TEMPLATE", "POL013;SOP029;TPL026"),
        ("bid_document_review|投标文件审查", "SOP;TEMPLATE;PROJECT_CASE", "SOP030;TPL027;P001_27"),
        ("qualification_review|资格审查", "FAQ_RULE;PROJECT_CASE", "FAQ009;P001_28"),
        ("commercial_review|商务响应审查", "FAQ_RULE;PROJECT_CASE", "FAQ009;P001_29"),
        ("technical_review|技术响应审查", "FAQ_RULE;PROJECT_CASE", "FAQ009;P001_30"),
        ("scoring_review|评分项审查", "FAQ_RULE;PROJECT_CASE", "FAQ009;P001_31"),
        ("rejection_risk|否决投标风险", "ENTERPRISE_FOUNDATION;FAQ_RULE;PUBLIC_REFERENCE", "KB009;FAQ009;REF006"),
        ("issue_traceability|问题定位与证据追踪", "TEMPLATE;PROJECT_CASE", "TPL028;P001_32;P001_33"),
    ],
    "A11": [
        ("contract_review|合同审查", "POLICY;SOP;TEMPLATE", "POL014;SOP018;TPL020"),
        ("performance_tracking|履约跟踪", "SOP;BUSINESS_DATA", "SOP018;DATA005"),
        ("contract_change|合同变更", "POLICY;SOP;PROJECT_CASE", "POL007;SOP009;P002_25"),
        ("payment_control|付款控制", "POLICY;FAQ_RULE;BUSINESS_DATA", "POL015;FAQ010;DATA005"),
        ("acceptance_control|验收控制", "SOP;PROJECT_CASE", "SOP010;P003_30"),
        ("breach_risk|违约风险", "ENTERPRISE_FOUNDATION;POLICY;SOP", "KB009;POL014;SOP008"),
        ("ip_confidentiality|知识产权与保密", "POLICY;PUBLIC_REFERENCE", "POL018;REF002;REF008"),
        ("evidence_traceability|合同证据追踪", "TEMPLATE;PROJECT_CASE", "TPL020;P002_30"),
    ],
    "A12": [
        ("kpi_definition|经营指标定义", "BUSINESS_DATA;ENTERPRISE_FOUNDATION", "DATA012;KB010"),
        ("budget_analysis|预算分析", "POLICY;BUSINESS_DATA", "POL015;DATA009"),
        ("cost_analysis|成本分析", "POLICY;BUSINESS_DATA;FAQ_RULE", "POL016;DATA008;FAQ011"),
        ("revenue_cash_analysis|收入回款分析", "BUSINESS_DATA;FAQ_RULE", "DATA010;DATA005;FAQ010"),
        ("portfolio_analysis|项目组合分析", "BUSINESS_DATA;PROJECT_CASE", "DATA004;CASE002"),
        ("risk_change_analysis|风险变更分析", "SOP;PROJECT_CASE", "SOP008;SOP009;CASE001"),
        ("project_review|项目复盘", "SOP;PROJECT_CASE", "SOP011;P001_23;P002_23;P003_23"),
        ("management_reporting|经营报告", "TEMPLATE;BUSINESS_DATA", "TPL014;DATA012"),
    ],
}


def build_assets():
    rows = []
    for i, (title, domain, agents, stages, dep) in enumerate(FOUNDATIONS, 1):
        rows.append(asset(
            f"KB{i:03d}", title, domain, "ENTERPRISE_FOUNDATION", "PACKAGE-01", agents, stages,
            dep, "由企业唯一事实源建立基础知识层级。" if dep else "企业唯一事实源的直接可读入口。",
            dep, "CANONICAL_FACTS + synthetic enterprise design", "Canonical Facts",
            synthetic="企业名称;组织;内部规则", force="INTERNAL_MANDATORY", priority="P0",
            notes="模拟企业基础；以 enterprise_model/CANONICAL_FACTS.yaml 为准",
        ))
    for i, (title, domain, agents, stages, authority, applicability) in enumerate(REFERENCES, 1):
        rows.append(asset(
            f"REF{i:03d}", title, domain, "PUBLIC_REFERENCE", "PACKAGE-01", agents, stages,
            "KB006", "公开资料须经适用性、效力与版本判断后使用。", "KB006",
            "Stage 2 authoritative-source collection", "Stage 2 核验适用范围与有效性",
            "官方规则;公开实践或案例", 1, authority=authority, force="REFERENCE",
            applicability=applicability, notes="Stage 1.1 仅规划来源；未搜集外部资料",
        ))
    for i, (title, domain, agents, stages, deps, categories, synthetic) in enumerate(POLICIES, 1):
        rows.append(asset(
            f"POL{i:03d}", title, domain, "POLICY", "PACKAGE-01", agents, stages, deps,
            "制度综合适用公共依据、公开实践和星澜内部参数。", "KB005",
            "PUBLIC_OFFICIAL + PUBLIC_CORPORATE/PUBLIC_CASE + SYNTHETIC_PARAMETERS",
            "Stage 2 至少核验三类来源；内部参数必须与公共依据分层", categories, 3, synthetic,
            "INTERNAL_DERIVED", "INTERNAL_MANDATORY",
        ))
    for i, (title, domain, agents, stages, deps, rationale) in enumerate(SOPS, 1):
        parent = ";".join(x for x in deps.split(";") if x.startswith(("POL", "KB", "REF")))
        rows.append(asset(
            f"SOP{i:03d}", title, domain, "SOP", "PACKAGE-01", agents, stages, deps, rationale,
            parent, "INTERNAL_DERIVED from curated upstream rules",
            "内部流程；Stage 2 公共来源仅在适用时作为依据", synthetic="角色;审批节点;内部时限",
            authority="INTERNAL_DERIVED", force="INTERNAL_MANDATORY",
        ))
    for i, (title, domain, agents, stages, deps, rationale) in enumerate(FAQS, 1):
        parent = ";".join(x for x in deps.split(";") if x.startswith(("POL", "KB", "REF")))
        rows.append(asset(
            f"FAQ{i:03d}", title, domain, "FAQ_RULE", "PACKAGE-01", agents, stages, deps, rationale,
            parent, "INTERNAL_DERIVED from policy/SOP/reference",
            "内部派生规则；引用公共依据时需核验适用性", authority="INTERNAL_DERIVED", force="GUIDANCE",
        ))
    for i, (title, domain, agents, stages) in enumerate(ROLES, 1):
        rows.append(asset(
            f"ROLE{i:03d}", title, domain, "ROLE", "PACKAGE-01", agents, stages, "KB002;KB003",
            "岗位职责由组织架构和部门职责共同定义。", "KB002;KB003",
            synthetic="岗位职责;权限边界", force="INTERNAL_MANDATORY",
        ))

    for project, project_name, classification in PROJECTS:
        for i, (title, domain, agents, stages, deps) in enumerate(COMMON_CASES, 1):
            kid = f"{project}_{i:02d}"
            rows.append(asset(
                kid, f"{project_name}-{title}", domain, "PROJECT_CASE", "PACKAGE-02", agents, stages,
                deps, "案例文件引用本项目 Canonical Facts，并以对应业务规则或模板为结构依据。", deps,
                "SYNTHETIC project facts from project canonical model",
                f"enterprise_model/projects/{project}_CANONICAL_FACTS.yaml", synthetic="客户;金额;人员;日期;项目事件",
                filename=f"{kid}_{title}.md", notes=f"{project} {classification}；Stage 4 生成正文",
            ))
        for i, (title, domain, stages, deps) in enumerate(PROJECT_EXTRAS[project], 25):
            kid = f"{project}_{i:02d}"
            if project == "P001":
                agents = ["A01", "A09", "A10", "A11"]
            elif project == "P002":
                agents = ["A01", "A02", "A03", "A10", "A11", "A12"]
            else:
                agents = ["A02", "A03", "A09", "A10", "A11", "A12"]
            rows.append(asset(
                kid, f"{project_name}-{title}", domain, "PROJECT_CASE", "PACKAGE-02", agents, stages,
                deps, "差异化案例由项目唯一事实源和相关领域规则共同约束。", deps,
                "SYNTHETIC project facts from project canonical model",
                f"enterprise_model/projects/{project}_CANONICAL_FACTS.yaml", synthetic="项目事件;金额;日期;人员",
                filename=f"{kid}_{title}.md", notes=f"{project} 差异化案例；Stage 4 生成正文",
            ))
    for kid, title, domain, agents, deps in CROSS_CASES:
        rows.append(asset(
            kid, title, domain, "PROJECT_CASE", "PACKAGE-02", agents, ["B18"], deps,
            "跨项目案例仅从相关项目事实与领域规则派生。", deps,
            "SYNTHETIC cross-project derived case planned for Stage 4", "项目 Canonical Facts 和适用流程",
            synthetic="案例情节;项目对比", notes="Stage 4 生成正文",
        ))
    for i, (title, domain, agents, stages, deps) in enumerate(TEMPLATES, 1):
        rows.append(asset(
            f"TPL{i:03d}", title, domain, "TEMPLATE", "PACKAGE-03", agents, stages, deps,
            "模板字段与对应流程、制度或检查规则保持一致。", deps, "SYNTHETIC reusable template",
            "内部合成模板", synthetic="模板字段;示例值", force="GUIDANCE",
        ))
    for i, (title, confidentiality, agents, stages) in enumerate(DATASETS, 1):
        rows.append(asset(
            f"DATA{i:03d}", title, "结构化业务数据", "BUSINESS_DATA", "PACKAGE-03", agents, stages,
            "KB007", "数据集受数据分类分级和最小必要原则约束。", "KB007",
            "SYNTHETIC controlled business-data generation", "仅生成合成行；不得使用真实个人信息",
            synthetic="全部业务记录", filename=f"DATA{i:03d}_结构化业务数据_{title}.xlsx",
            notes=f"confidentiality={confidentiality}",
        ))
    return rows


def build_coverage_rows():
    rows = []
    actual = {}
    for aid, specs in COVERAGE_SPECS.items():
        actual[aid] = set()
        for capability_label, types, asset_ids in specs:
            capability, label = capability_label.split("|", 1)
            actual[aid].add(capability)
            rows.append({
                "agent_id": aid, "agent_name": AGENTS[aid], "capability": capability,
                "capability_name": label, "required_asset_type": types, "required_asset_ids": asset_ids,
                "minimum_viable_coverage": "存在明确资产，并包含该能力所需的规则/流程/模板/案例组合",
                "coverage_status": "FULL", "gap": "Stage 2 公开来源尚待核验",
                "notes": "FULL 仅表示 Stage 1.1 规划覆盖，不表示来源核验或正文生成已完成",
            })
    if actual != AGENT_REQUIRED_CAPABILITIES:
        raise ValueError("COVERAGE_SPECS diverges from AGENT_REQUIRED_CAPABILITIES")
    return rows


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    assets = build_assets()
    write_csv(ROOT / "manifests/KNOWLEDGE_MANIFEST.csv", assets, MANIFEST_FIELDS)

    chain_rows = []
    for bid, name in CHAIN.items():
        selected = [a for a in assets if bid in a["business_chain_stage"].split(";")]
        chain_rows.append({
            "business_chain_id": bid, "stage_name": name, "sequence": bid[1:],
            "knowledge_ids": ";".join(a["knowledge_id"] for a in selected),
            "primary_domains": ";".join(dict.fromkeys(a["domain"] for a in selected)),
            "notes": "由语义策展后的 Manifest 生成；资产变更时同步重建",
        })
    write_csv(ROOT / "manifests/BUSINESS_CHAIN_MAPPING.csv", chain_rows,
              ["business_chain_id", "stage_name", "sequence", "knowledge_ids", "primary_domains", "notes"])

    write_csv(ROOT / "manifests/AGENT_COVERAGE.csv", build_coverage_rows(), [
        "agent_id", "agent_name", "capability", "capability_name", "required_asset_type",
        "required_asset_ids", "minimum_viable_coverage", "coverage_status", "gap", "notes",
    ])

    counts = {p: sum(a["package"] == p for a in assets) for p in ("PACKAGE-01", "PACKAGE-02", "PACKAGE-03")}
    package_rows = [
        {"package_id": "PACKAGE-01", "package_name": "企业核心知识库", "scope": "企业基础、公开依据、制度、SOP、FAQ/规则、岗位", "estimated_file_count": counts["PACKAGE-01"], "max_file_count": 100, "flattened": "YES", "contents": "KB;REF;POL;SOP;FAQ;ROLE", "status": "planned", "planning_note": "Stage 1/1.1 逻辑规划，非最终上传分包；Stage 6 须重新平衡并尽量保留 10~20 个文件余量"},
        {"package_id": "PACKAGE-02", "package_name": "企业历史案例库", "scope": "差异化 P001/P002/P003 案例与跨项目复盘", "estimated_file_count": counts["PACKAGE-02"], "max_file_count": 100, "flattened": "YES", "contents": "P001/P002/P003;CASE", "status": "planned", "planning_note": "Stage 1/1.1 逻辑规划，非最终上传分包；Stage 6 须重新平衡并尽量保留 10~20 个文件余量"},
        {"package_id": "PACKAGE-03", "package_name": "企业业务数据与模板库", "scope": "模板与结构化合成业务数据", "estimated_file_count": counts["PACKAGE-03"], "max_file_count": 100, "flattened": "YES", "contents": "TPL;DATA", "status": "planned", "planning_note": "Stage 1/1.1 逻辑规划，非最终上传分包；Stage 6 须重新平衡并尽量保留 10~20 个文件余量"},
    ]
    write_csv(ROOT / "manifests/PACKAGE_PLAN.csv", package_rows,
              ["package_id", "package_name", "scope", "estimated_file_count", "max_file_count", "flattened", "contents", "status", "planning_note"])

    source_specs = [
        ("SRC-LAW-001", "劳动合同相关公共法规（占位）", "", "PUBLIC_OFFICIAL", "人力资源", "L0", "OFFICIAL", "MANDATORY", "PENDING_REVIEW", "REF001", "Stage 2 核验后判断具体条款是否直接适用"),
        ("SRC-STD-001", "信息安全管理标准（占位）", "", "PUBLIC_OFFICIAL", "信息安全数据治理", "L0", "OFFICIAL", "GUIDANCE", "PENDING_REVIEW", "REF011", "标准是否强制取决于采用、认证或合同约定"),
        ("SRC-MOF-001", "政府采购规则（占位）", "", "PUBLIC_OFFICIAL", "采购", "L0", "OFFICIAL", "REFERENCE", "ANALOGICAL", "REF005", "政府采购规则不自动适用于星澜内部采购"),
        ("SRC-CORP-001", "公开企业管理实践（占位）", "", "PUBLIC_CORPORATE", "企业管理", "L5", "PUBLIC_CORPORATE", "REFERENCE", "ANALOGICAL", "REF015", "公开实践仅作类比参考"),
        ("SRC-BID-001", "公开招投标案例（占位）", "", "PUBLIC_CASE", "招投标", "L4", "PUBLIC_CASE", "NONE", "ANALOGICAL", "REF018", "公开案例不构成星澜内部规则"),
        ("SRC-SYN-001", "Canonical Facts 合成企业基线", "星澜 Stage 1.1", "SYNTHETIC", "企业基础", "L1", "SYNTHETIC", "INTERNAL_MANDATORY", "DIRECT", "KB001-KB012", "模拟企业唯一事实源，不代表真实企业"),
    ]
    source_rows = []
    for sid, title, publisher, stype, domain, level, authority, force, applicability, used_by, note in source_specs:
        verified = sid == "SRC-SYN-001"
        source_rows.append({
            "source_id": sid, "title": title, "publisher": publisher, "source_type": stype,
            "domain": domain, "publication_date": "", "effective_date": "2026-09-12" if verified else "",
            "status": "active" if verified else "candidate",
            "url": "repo://enterprise_model/CANONICAL_FACTS.yaml" if verified else "",
            "access_date": "2026-09-12" if verified else "", "authority_level": level,
            "source_authority": authority, "normative_force": force, "applicability": applicability,
            "specificity": "ENTERPRISE" if verified else "DOMAIN",
            "applicable_scope": "模拟企业全域" if verified else domain,
            "summary": "唯一内部合成事实源" if verified else "Stage 2 搜集并核验", "used_by": used_by,
            "verification_status": "VERIFIED" if verified else "PENDING", "notes": note,
        })
    write_csv(ROOT / "source_registry/SOURCE_REGISTRY.csv", source_rows, [
        "source_id", "title", "publisher", "source_type", "domain", "publication_date", "effective_date",
        "status", "url", "access_date", "authority_level", "source_authority", "normative_force",
        "applicability", "specificity", "applicable_scope", "summary", "used_by", "verification_status", "notes",
    ])

    lineage = [
        {"lineage_id": "LIN-001", "knowledge_id": "KB001", "source_id": "SRC-SYN-001", "relationship": "canonical_fact_source", "claim_scope": "公司名称、成立年份、总部、员工数", "transformation": "direct", "confidence": "HIGH", "review_status": "VERIFIED", "notes": "唯一事实源"},
        {"lineage_id": "LIN-002", "knowledge_id": "REF001", "source_id": "SRC-LAW-001", "relationship": "planned_external_source", "claim_scope": "劳动合同相关规则", "transformation": "to_be_extracted", "confidence": "PENDING", "review_status": "PENDING", "notes": "Stage 2 核验后方可使用"},
        {"lineage_id": "LIN-003", "knowledge_id": "POL011", "source_id": "SRC-SYN-001", "relationship": "synthetic_parameter_source", "claim_scope": "内部采购阈值与审批层级", "transformation": "derived_with_internal_thresholds", "confidence": "HIGH", "review_status": "VERIFIED", "notes": "公共规则与企业参数必须分层"},
        {"lineage_id": "LIN-004", "knowledge_id": "P001_23", "source_id": "SRC-SYN-001", "relationship": "project_canonical_source", "claim_scope": "优秀项目经营复盘规划", "transformation": "synthetic_generation_planned", "confidence": "PENDING", "review_status": "PENDING", "notes": "Stage 4 生成正文"},
        {"lineage_id": "LIN-005", "knowledge_id": "P002_23", "source_id": "SRC-SYN-001", "relationship": "project_canonical_source", "claim_scope": "问题项目经营复盘规划", "transformation": "synthetic_generation_planned", "confidence": "PENDING", "review_status": "PENDING", "notes": "Stage 4 生成正文"},
        {"lineage_id": "LIN-006", "knowledge_id": "P003_23", "source_id": "SRC-SYN-001", "relationship": "project_canonical_source", "claim_scope": "复杂技术项目经营复盘规划", "transformation": "synthetic_generation_planned", "confidence": "PENDING", "review_status": "PENDING", "notes": "Stage 4 生成正文"},
    ]
    write_csv(ROOT / "manifests/SOURCE_LINEAGE.csv", lineage,
              ["lineage_id", "knowledge_id", "source_id", "relationship", "claim_scope", "transformation", "confidence", "review_status", "notes"])
    print(f"Generated {len(assets)} assets; " + ", ".join(f"{p}={counts[p]}" for p in counts))


if __name__ == "__main__":
    main()
