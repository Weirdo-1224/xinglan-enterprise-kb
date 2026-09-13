# 星澜数字科技有限公司模拟企业知识库

本项目为“模拟企业知识库 + 12 个企业智能体”准备可上传、可验证的知识资产。当前规划 239 项资产，已完成 Stage 3 企业核心知识库 100 份正文、Stage 3.1 内容深化与关键 Claim 补全、Stage 4 三个历史项目 99 份正文，以及 Stage 5 的 12 份结构化业务数据和 28 份标准模板；工程已从 Stage 驱动的实验脚手架收敛为可长期维护的正式知识库结构。

## 为什么使用模拟企业

模拟企业可以在不暴露真实组织、客户、合同和员工信息的前提下，完整演示从客户需求到项目经营复盘的企业业务闭环。所有合成数据必须明确标注为 `SYNTHETIC` 或 `SYNTHETIC_DERIVED`，不得冒充真实企业事实。

## 知识来源与上传包

知识治理分别记录来源权威、规范效力和业务适用性，避免把“官方来源”等同于“直接适用于模拟企业”。最终规划三个平铺上传包：

1. `PACKAGE-01` 企业核心知识库
2. `PACKAGE-02` 企业历史案例库
3. `PACKAGE-03` 企业业务数据与模板库

## 权威数据源

- 企业事实唯一权威源：`enterprise_model/CANONICAL_FACTS.yaml`。`enterprise_model/ENTERPRISE_OVERVIEW.md` 仅为便于人阅读的派生视图，不得作为独立权威事实源；两者冲突时以 `CANONICAL_FACTS.yaml` 为准。
- 项目事实唯一权威源：`enterprise_model/projects/P001_CANONICAL_FACTS.yaml`、`P002_CANONICAL_FACTS.yaml`、`P003_CANONICAL_FACTS.yaml`。
- 来源权威索引：`sources/SOURCE_REGISTRY.csv`。
- 知识资产总目录：`manifests/KNOWLEDGE_MANIFEST.csv`。
- 外部来源血缘：`manifests/SOURCE_LINEAGE.csv`。
- 关键 Claim 血缘：`manifests/CLAIM_PROVENANCE.csv`（97 条关键声明，按 `EXPLICIT` / `DERIVED` / `SYNTHETIC` 区分依据强度）。
- 项目事件台账：`manifests/PROJECT_EVENT_LEDGER.csv`（84 条事件，P001/P002/P003 跨文件事实一致性的依据）。

## 12 个智能体

需求洞察与方案顾问、AI项目经理、企业知识管家、智能会议协同官、企业文档创作官、文档规范与排版官、AI招聘与人才助手、培训绩效与员工发展助手、智能采购顾问、招投标审查官、合同与履约风控官、企业经营分析师。

## 企业主业务链

客户需求 → 需求澄清 → 解决方案 → 项目立项 → 项目计划 → 人员配置 → 招聘 / 培训 → 采购 → 招投标 → 合同 → 项目执行 → 会议协同 → 风险管理 → 验收 → 结项 → 经营分析 → 知识沉淀。

## 工程主链与目录

工程主链：`sources → enterprise_model → manifests → knowledge → validation(scripts) → deliverables`。

- `sources/`：来源登记表 `SOURCE_REGISTRY.csv`、逐条来源核验备注 `source_notes/`，原始文件缓存（如有）只放 `raw/`
- `enterprise_model/`：企业 Canonical Facts 唯一事实源、企业概览、知识治理规则，以及 `projects/` 下 P001/P002/P003 项目唯一事实源
- `manifests/`：知识资产 Manifest、智能体能力覆盖、来源血缘、声明溯源和上传包规划；已派生/停用清单归档于 `archive/`
- `knowledge/`：知识正文与结构化数据；`core/` 为 Stage 3 核心知识 100 份，`cases/` 为 Stage 4 项目案例 99 份，`templates/` 为 Stage 5 标准模板 28 份，`business_data/` 为 Stage 5 结构化业务数据 12 份
- `schemas/`：知识、来源、项目和业务数据契约
- `scripts/`：质量校验脚本；停用生成器归档于 `archive/`
- `docs/`：架构、来源、合成数据和质量门等长期治理文档；阶段性说明归档于 `archive/`
- `deliverables/`：仅存放最终交付物；Stage 中间报告归档于 `archive/`

## Stage 顺序

Stage 1 项目初始化；Stage 1.1 语义修复；Stage 2 公开真实资料搜集；Stage 3 企业核心知识库（100 份正文，已完成）；Stage 3.1 知识深化与 Claim 补全（已完成）；Stage 4 三个完整历史项目（99 份正文，已完成）；Stage 5 业务数据与模板（40 份，已完成）；Stage 6 全局 QA、RAG 适配与最终打包。

## 运行校验

在仓库根目录执行统一入口：

```powershell
python scripts/validate_all.py
```

该入口按稳定顺序执行全部 12 个活动 validator（Manifest、Metadata、Source Lineage、Source Coverage、Agent Coverage、Semantic Dependency、Canonical Consistency、Upload Constraints、Core Knowledge、Stage 3.1 Content QA、Stage 4 Project Cases、Stage 5 Business Data & Templates），逐项报告 PASS / REVIEW / FAIL，任意 FAIL 时以非 0 退出。也可单独运行 `scripts/validate_*.py` 中的任意一个；新增校验器必须同时注册进 `validate_all.py` 的 `VALIDATORS` 列表。

规划层校验脚本仅使用 Python 标准库；`validate_metadata.py`、`validate_core_knowledge.py`、`validate_stage31_content.py` 与 `validate_stage4_cases.py` 另需 `pyyaml` 和 `jsonschema`。

当前无活动生成器：`generate_stage1.py` 与 `generate_stage3.py` 均已归档至 `scripts/archive/`，仅保留历史复现用途。其中 `generate_stage3.py` 会直接重写 `knowledge/core/` 下 100 份正式正文，无覆盖保护，不得再次运行。
