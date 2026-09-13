# 星澜企业知识库交付指南

- 版本：Stage 6 Final Delivery
- 交付日期：2026-09-13
- 适用对象：RAG 平台运营、知识库管理员、12 个企业 Agent 的维护人员

---

## 1. 企业知识库简介

本知识库是合成企业**星澜数字科技有限公司**（模拟，2021 年成立，成都，AI 与数字化科技公司，模拟员工 286 人）的企业级知识库，覆盖企业基础、制度、流程、FAQ、岗位、公开法规依据、三个完整历史项目案例、结构化经营数据和标准模板，供 12 个企业 Agent 检索增强使用。

**重要声明**：库内企业、人员、客户、供应商、项目、金额与事件均为合成数据，用于知识库演示与评测，不代表任何真实企业或真实事件；公开法规依据（REF）来自真实公开来源，已逐条标注适用性边界。

## 2. 239 项资产构成

| 层 | 数量 | 内容 | 来源类型 |
| --- | --- | --- | --- |
| 企业基础 KB | 12 | 公司简介、组织、部门职责、审批原则、数据分级、风险等级、术语、业务链 | SYNTHETIC |
| 公开依据 REF | 18 | 真实法律法规/标准/公开实践的工作摘要，含适用性与生效日期治理 | PUBLIC |
| 企业制度 POL | 18 | 六段式管理制度（HR、采购、合同、项目、财务、信息安全等） | INTERNAL_DERIVED |
| 标准流程 SOP | 30 | 含触发条件、编号步骤、判断分支、失败路径的可执行流程 | INTERNAL_DERIVED |
| 常见问题 FAQ | 12 | 结论 + 适用条件 + 依据 + 例外的问答规则 | INTERNAL_DERIVED |
| 岗位 ROLE | 10 | 十段结构岗位说明 | SYNTHETIC |
| 项目案例 P001~P003 | 95 | 三个完整历史项目的全链路档案（33+31+31） | SYNTHETIC |
| 跨项目复盘 CASE | 4 | 变更/采购成本/验收/文档规范四个跨项目复盘 | SYNTHETIC_DERIVED |
| 模板 TPL | 28 | 立项、方案、周报、会议纪要、采购、合同、评审等标准模板 | INTERNAL_DERIVED |
| 业务数据 DATA | 12 | 员工、客户、供应商、项目、合同、采购、工时、成本、预算、收入、能力、经营指标（XLSX，含字段字典与元数据） | SYNTHETIC / SYNTHETIC_DERIVED |
| **合计** | **239** | | |

## 3. 12 Agent 与知识域关系

| Agent | 名称 | 主要知识域 |
| --- | --- | --- |
| A01 | 需求洞察与方案顾问 | 需求/方案 SOP 与模板、投标协同、P001/P002 案例 |
| A02 | AI项目经理 | 立项、WBS、进度、风险、变更、验收、工时与经营数据 |
| A03 | 企业知识管家 | 知识治理制度、知识新增/版本/废止 SOP、FAQ、经营指标 |
| A04 | 智能会议协同官 | 会议制度与 SOP、纪要/待办模板、会议 FAQ |
| A05 | 企业文档创作官 | 公文制度、写作 SOP、文档模板、公开依据 |
| A06 | 文档规范与排版官 | 文档规范 KB/POL、格式检查 SOP/FAQ、排版模板、CASE004 |
| A07 | AI招聘与人才助手 | 招聘制度与 SOP、岗位 ROLE、人员能力数据 |
| A08 | 培训绩效与员工发展助手 | 培训/绩效制度、目标/回顾/评价 SOP 与模板、能力标签 |
| A09 | 智能采购顾问 | 采购阈值与制度、采购/供应商 SOP、供应商与采购台账 |
| A10 | 招投标审查官 | 招投标制度与 SOP、审查模板、P001 投标案例、公开法规 |
| A11 | 合同与履约风控官 | 合同制度与 SOP、付款/验收控制、合同台账、P002 争议案例 |
| A12 | 企业经营分析师 | 经营指标字典、预算/成本/收入/项目台账、项目复盘 |

完整能力-资产映射见 `manifests/AGENT_COVERAGE.csv`；每项资产服务的 Agent 见各文件发布头的 `served_agents`。

## 4. 四个上传包

平台约束：每包 ≤100 文件、包内无子目录、中文文件名、不含源码/archive/校验器等工程文件。

| 包 | 文件数 | 内容 |
| --- | --- | --- |
| `PACKAGE-01_CORE.zip` | 100 | 全部核心知识（KB/REF/POL/SOP/FAQ/ROLE） |
| `PACKAGE-02_PROJECT_MEMORY.zip` | 99 | P001/P002/P003 案例链 95 份 + CASE001~004 跨项目复盘 |
| `PACKAGE-03_BUSINESS_DATA.zip` | 13 | 12 份 XLSX（保留字段字典与元数据 sheet）+ `PROJECT_INDEX.csv` |
| `PACKAGE-04_TEMPLATES.zip` | 28 | 全部标准模板 |

每份发布资产保留轻量身份头：`knowledge_id`、`knowledge_type`、`domain`、`title`、`served_agents`、`source_type`（项目案例另含 `project_id`、`history_level`），保证可追溯；完整治理元数据、血缘与来源表保留在仓库治理原版（`knowledge/` + `manifests/` + `sources/`），不随上传包发布。

## 5. 项目历史层级（history_level）

| 层级 | 项目 | 含义 |
| --- | --- | --- |
| **FULL_HISTORY** | P001、P002、P003 | 拥有完整 Stage 4 项目档案（需求、方案、合同、采购、风险、变更、会议、验收、复盘全链路），可回答历史事件类问题 |
| **STRUCTURED_ONLY** | P004~P012 | 仅有 Stage 5 结构化经营数据（DATA004~DATA010），不存在完整会议/变更/风险等历史材料 |

**Agent 行为要求**：面对 STRUCTURED_ONLY 项目的历史细节问题（如"P008 的纠偏会议是什么？"），必须回答"当前仅有该项目的结构化经营记录，没有完整会议/变更历史材料"，不得编造。层级判定依据 `PROJECT_INDEX.csv`（随 PACKAGE-03 发布，治理版见 `manifests/PROJECT_INDEX.csv`）。

## 6. PUBLIC / SYNTHETIC / SYNTHETIC_DERIVED 区别

| source_type | 含义 | 使用边界 |
| --- | --- | --- |
| PUBLIC | 真实公开来源（法律法规、标准、公开案例），经核验登记 | 按条目级适用性（DIRECT/ANALOGICAL）使用；ANALOGICAL 仅作方法参考，不构成企业义务 |
| SYNTHETIC | 基于企业 Canonical Facts 合成的内部事实 | 仅在本知识库演示范围内有效，不代表真实企业 |
| SYNTHETIC_DERIVED | 由合成项目事实二次派生（跨项目复盘、合成经营数据行） | 事实优先级低于项目原始事实与 Canonical Facts；冲突时以上游为准 |

另有 INTERNAL_DERIVED：由制度/流程上游派生的内部知识（SOP、FAQ、模板等），不新增上游不存在的规则。

## 7. 上传顺序

1. **PACKAGE-01_CORE.zip**（制度与规则底座，其他包的知识依赖它）
2. **PACKAGE-03_BUSINESS_DATA.zip**（结构化数据与 PROJECT_INDEX，建立项目主数据与 history_level）
3. **PACKAGE-02_PROJECT_MEMORY.zip**（项目案例，引用制度与数据）
4. **PACKAGE-04_TEMPLATES.zip**（模板，引用 SOP）

上传后建议按 `evaluation/eval_set.json`（144 题）抽样做端到端冒烟测试，重点验证：17 万采购档位判断、P002 延期原因、P008 历史问题返回"仅有结构化经营记录"。

## 8. 更新与维护原则

1. **治理原版为唯一事实源**：所有修改先在仓库 `knowledge/` 进行并跑通 `python scripts/validate_all.py`，再用 `scripts/build_rag_package.py` 重新生成发布版、`scripts/build_upload_packages.py` 重新打包，**禁止直接编辑发布版或上传包**。
2. **事实优先级**：Canonical Facts → 项目原始事实（P00X_*）→ 结构化业务数据（DATA）→ 项目汇总/复盘 → 跨项目 CASE；冲突时下层服从上层。
3. **不臆造**：无上游依据的值不补、不改；无法裁定的差异记录为已知边界而非编造数值。
4. **CASE 是经验不是制度**：案例复盘中的建议不自动成为现行规则；模板不得创造 POLICY/SOP 中不存在的强制要求。
5. **history_level 治理**：新增项目默认 STRUCTURED_ONLY，只有补齐全链路档案并通过 Stage 4 同级校验后才升级 FULL_HISTORY。

## 9. 已知边界

1. **P004~P012 采购-成本对账差异**：32 个通用采购单中 24 单的 DATA006 订单额与 DATA008 挂钩入账不一致（含 5 单 completed 零入账）；P009 采购总额 108 万超过项目预算 81 万。属合成数据生成缺陷族，无上游事实可裁定正确值，保留原样；回答相关问题时应按订单口径与入账口径分别说明。
2. **采购阈值 20 万元端点重叠**："5 万至 20 万三家比选"与"20 万至 100 万竞争性采购"同时包含 20 万元（Canonical 层口径）；恰为 20 万元的采购应说明重叠并按知识治理规则裁决。
3. **通用采购行日期同值**：P004~P012 采购行的 request_date 与合同 sign_date 同值（生成缺陷族），受日期链校验看守，不单独作为事实引用。
4. **入职日期公式残留**：DATA001 多数合成员工入职日期呈公式化分布（日=月、含周末入职），属合成特征；三位具名项目经理为自然日期。
5. **收入台账无实际到账日字段**：DATA010 的日期为到期日/收入确认日口径，与叙述层资金到账日是两套口径，不应逐笔等同比较。
6. **评测为离线确定性评测**：仓库无运行中的 RAG 平台与 Agent 实例，`evaluation/EVALUATION_REPORT.md` 的指标基于发布版语料的可路由性、可答性、证据命中与边界核验，上线后应以真实端到端评测复核。

## 10. 可追溯性

- 发布清单：`deliverables/rag/RAG_MANIFEST.csv`（239 行，含 source_type 与 history_level）
- 治理清单：`manifests/KNOWLEDGE_MANIFEST.csv`、`CLAIM_PROVENANCE.csv`、`SOURCE_LINEAGE.csv`
- 来源登记：`sources/SOURCE_REGISTRY.csv` 与 `sources/source_notes/`
- 评测：`evaluation/eval_set.json`、`evaluation/EVALUATION_REPORT.md`
- 全局 QA：`docs/STAGE6_GLOBAL_QA.md`
