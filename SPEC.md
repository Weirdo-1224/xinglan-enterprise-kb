# 星澜数字科技有限公司知识库项目总规格

## 1. 目标与范围

构建一套面向 12 个企业智能体的模拟企业知识库。Stage 1.1 的交付物是稳定的规则、目录、企业与项目 Canonical Model、数据契约、239 项知识资产 Manifest、能力驱动的智能体覆盖矩阵、业务链映射、来源血缘结构和语义质量校验框架。

Stage 1.1 明确不包含：大规模公开资料搜集、PDF 下载、知识正文批量生成、完整历史项目正文、Excel 业务数据、最终 ZIP 和 Stage 2~6 执行。

## 2. 事实基线

企业唯一事实源为 `enterprise_model/CANONICAL_FACTS.yaml`；`enterprise_model/ENTERPRISE_OVERVIEW.md` 仅为便于人阅读的派生视图，不得作为独立权威事实源，两者冲突时以 `CANONICAL_FACTS.yaml` 为准。三个项目的唯一事实源为 `enterprise_model/projects/P001_CANONICAL_FACTS.yaml` 等文件。公司与项目事实在其他文件中不得自行变体。当前企业是合成企业；所有未由公共来源支持的内部规则都必须标记为 `SYNTHETIC` 或 `SYNTHETIC_DERIVED`。

其余权威索引：来源以 `sources/SOURCE_REGISTRY.csv` 为唯一登记表；知识资产总目录为 `manifests/KNOWLEDGE_MANIFEST.csv`；外部来源血缘为 `manifests/SOURCE_LINEAGE.csv`；关键 Claim 血缘为 `manifests/CLAIM_PROVENANCE.csv`。正式知识可以引用和表达 Canonical Facts，但不得维护脱离 Canonical 的独立事实配置。

## 3. 知识治理

来源治理同时记录 `source_authority`、`normative_force` 和 `applicability`。L0~L5 仅表示知识层级，不单独决定冲突。冲突依次比较适用性、规范效力、状态、有效日期/版本、具体性和来源权威；无法解决时标记 `CONFLICT`。官方来源不自动直接适用于企业内部业务。

## 4. 平台与打包约束

主要知识文件采用 Markdown；单文件目标不超过 20,000 字，超过 100,000 字必须拆分。当前 `PACKAGE_PLAN.csv` 中 100 / 99 / 40 的分配仅是 Stage 1/1.1 逻辑规划，不是最终上传分包，且不作为 Stage 2 阻塞项。Stage 6 必须执行 package rebalancing：每个 ZIP 最多 100 个文件，建议尽量保留 10~20 个文件余量，最终上传包根目录平铺、无子文件夹。Package 只是运输单元，不改变知识 ID、领域或语义归属。图片不是核心知识载体，图片必须有同步文字说明。

## 5. 资产要求

每项资产必须至少服务一个智能体或一个业务链阶段，具有唯一 `knowledge_id` 和唯一文件名，并通过多值 `parent_knowledge`、`depends_on` 和 `dependency_rationale` 追溯前置知识。核心 POLICY 还要规划 Stage 2 来源类别、最少数量和合成字段。Manifest 是规划清单，不等于正文存在。

## 6. 安全与边界

公开事实、内部合成规则和结构化合成数据分层管理。采购金额阈值等企业内部规则不得表述为国家法律要求。敏感信息、员工信息、客户信息、合同信息和经营数据进入 `SENSITIVE` 或 `HIGHLY_SENSITIVE` 范畴，并按最小必要原则使用。

## 7. 交付验收

以 `docs/QUALITY_GATE.md` 为验收标准。Stage 1.1 必须通过 Manifest、Schema、来源、能力覆盖、语义依赖、项目 Canonical 一致性和上传约束校验；正文元数据校验在无正文时只报告跳过，不冒充已完成。
