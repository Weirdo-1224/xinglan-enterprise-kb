# 星澜数字科技有限公司模拟企业知识库

本项目为“模拟企业知识库 + 12 个企业智能体”准备可上传、可验证的知识资产规划。Stage 1.1 在 Stage 1 的 195 项基础上完成语义修复，现规划 239 项资产；只建立规则、企业与项目唯一事实源、数据契约、Manifest、能力覆盖矩阵和校验框架，不批量生成知识正文。

## 为什么使用模拟企业

模拟企业可以在不暴露真实组织、客户、合同和员工信息的前提下，完整演示从客户需求到项目经营复盘的企业业务闭环。所有合成数据必须明确标注为 `SYNTHETIC` 或 `SYNTHETIC_DERIVED`，不得冒充真实企业事实。

## 知识来源与上传包

知识治理分别记录来源权威、规范效力和业务适用性，避免把“官方来源”等同于“直接适用于模拟企业”。最终规划三个平铺上传包：

1. `PACKAGE-01` 企业核心知识库
2. `PACKAGE-02` 企业历史案例库
3. `PACKAGE-03` 企业业务数据与模板库

## 12 个智能体

需求洞察与方案顾问、AI项目经理、企业知识管家、智能会议协同官、企业文档创作官、文档规范与排版官、AI招聘与人才助手、培训绩效与员工发展助手、智能采购顾问、招投标审查官、合同与履约风控官、企业经营分析师。

## 企业主业务链

客户需求 → 需求澄清 → 解决方案 → 项目立项 → 项目计划 → 人员配置 → 招聘 / 培训 → 采购 → 招投标 → 合同 → 项目执行 → 会议协同 → 风险管理 → 验收 → 结项 → 经营分析 → 知识沉淀。

## 工程目录

- `enterprise_model/`：企业 Canonical Model，以及 P001/P002/P003 项目唯一事实源
- `schemas/`：知识、来源、项目和业务数据契约
- `manifests/`：知识资产、智能体、业务链、来源血缘和打包规划
- `source_registry/`、`sources/`：来源登记与 Stage 2 来源存放区
- `knowledge/`：后续知识正文和结构化数据的目标目录
- `scripts/`：基础质量校验脚本
- `docs/`：架构、来源、合成数据和质量门规范

## Stage 顺序

Stage 1 项目初始化；Stage 1.1 语义修复；Stage 2 公开真实资料搜集；Stage 3 企业核心知识库；Stage 4 三个完整历史项目；Stage 5 业务数据与模板；Stage 6 全局 QA、RAG 适配与最终打包。

## 当前状态

Stage 1.1 已完成语义依赖、能力覆盖、来源适用性和项目 Canonical Model 的架构升级。当前没有批量知识正文、真实业务数据、最终 ZIP，也未执行 Stage 2。

## 运行校验

在仓库根目录执行：

```powershell
python scripts/validate_manifest.py
python scripts/validate_metadata.py
python scripts/validate_source_lineage.py
python scripts/validate_agent_coverage.py
python scripts/validate_semantic_dependencies.py
python scripts/validate_consistency.py
python scripts/validate_upload_constraints.py
```

校验脚本使用 Python 标准库，不依赖第三方包。
