# Repository Baseline

本文件冻结 Repository Cleanup 之后的仓库基线，作为 Stage 3.1 及以后各阶段的对照基准。

> **本文档是时点快照，不是当前状态说明。**
> 第 1、3、4、7、8、9 节是架构不变量，长期有效；第 2、5、6 节记录的是**冻结时点**
> （commit `b2d2eb3`，2026-09-12）的数值，随 Stage 推进会过时。
> **当前状态以 `README.md` 为唯一权威**；第 10 节在每次 Stage 收口时刷新，供快速对照。

## 1. 目录结构

```
sources/            来源登记与核验备注
enterprise_model/   企业与项目 Canonical Facts、企业概览、知识治理
manifests/          知识资产、覆盖、血缘、声明溯源、上传包规划
knowledge/          core/（100 份核心知识）、cases/、templates/、business_data/
schemas/            知识、来源、项目、业务数据契约
scripts/            活动 validator + validate_all.py；archive/ 存放停用生成器
docs/               长期治理文档；archive/ 存放阶段性历史记录
deliverables/       仅最终交付物；archive/ 存放 Stage 中间报告
```

## 2. 阶段状态（冻结时点 `b2d2eb3`）

Stage 1 / 1.1 / 2 / 3 已完成；Stage 3.1（知识深化与 Claim 补全）尚未开始；Stage 4 / 5 / 6 未执行。

> 该状态已被后续 Stage 推进超越，见第 10 节。

## 3. 权威数据源

- 企业事实：`enterprise_model/CANONICAL_FACTS.yaml`（`ENTERPRISE_OVERVIEW.md` 仅为派生阅读视图，冲突以 Canonical 为准）
- 项目事实：`enterprise_model/projects/P001~P003_CANONICAL_FACTS.yaml`
- 来源索引：`sources/SOURCE_REGISTRY.csv`
- 知识资产总目录：`manifests/KNOWLEDGE_MANIFEST.csv`
- 外部来源血缘：`manifests/SOURCE_LINEAGE.csv`
- 关键 Claim 血缘：`manifests/CLAIM_PROVENANCE.csv`
- 项目事件台账：`manifests/PROJECT_EVENT_LEDGER.csv`（Stage 4 引入，案件事实的跨文件一致性依据）

## 4. 活动 Manifest

`KNOWLEDGE_MANIFEST.csv`、`AGENT_COVERAGE.csv`、`SOURCE_LINEAGE.csv`、`CLAIM_PROVENANCE.csv`、`PROJECT_EVENT_LEDGER.csv`、`PACKAGE_PLAN.csv`。`manifests/archive/` 内为已派生/停用清单，不参与校验。

## 5. 知识资产数量（冻结时点 `b2d2eb3`）

239 项 Manifest 资产；其中 Stage 3 核心知识 100 份正文全部完成并通过校验。

## 6. Source 数量（冻结时点 `b2d2eb3`）

58 个登记来源；79 条来源血缘记录；79 条关键 Claim 溯源记录。

## 7. Validator 入口

统一入口：`python scripts/validate_all.py`（逐项 PASS / REVIEW / FAIL，任意 FAIL 返回非 0）。
新增校验器时必须同时注册进 `validate_all.py` 的 `VALIDATORS` 列表，否则不会被统一入口执行。

冻结时（`b2d2eb3`）为 9 个活动 validator 且全部 PASS；各时点的实际数量与结果见第 10 节。

## 8. Archive 规则

各 `archive/` 目录仅为历史记录，不是当前权威数据：不被 validator 当正式输入，不被生成器默认读取，不参与 Manifest / Source / Knowledge 正式校验。`generate_stage3.py` 等一次性生成器仅保留历史复现用途，不得再次运行。新的人工复核事项写入活动路径 `docs/STAGE3_REVIEW_REQUIRED.md`，不得写入 archive。

## 9. 后续 Stage 边界

从 Stage 3.1 开始，原则上冻结目录结构。后续只新增或修改知识、案例、模板、业务数据和必要校验逻辑，不再进行架构级目录重构。

## 10. 当前状态（滚动更新）

> 每次 Stage 收口时刷新本节。**当前状态的唯一权威是 `README.md`**，本节仅作与冻结基线的快速对照。

| 项 | 冻结时点 `b2d2eb3` | 当前 |
| --- | --- | --- |
| 已完成 Stage | 1 / 1.1 / 2 / 3 | 1 / 1.1 / 2 / 3 / 3.1 / 4 / 5 |
| Manifest 资产 | 239 | 239 |
| 核心知识正文 | 100 | 100 |
| 项目案例正文 | 0 | 99（P001 33 / P002 31 / P003 31 / CASE 复盘 4） |
| 业务数据 | 0 | 12（结构化 XLSX） |
| 标准模板 | 0 | 28（Markdown） |
| 登记来源 | 58 | 58 |
| 来源血缘记录 | 79 | 94 |
| 关键 Claim 溯源 | 79 | 97 |
| 项目事件台账 | 无 | 84 |
| 活动 validator | 9（全部 PASS） | 12（全部 PASS） |

未执行：Stage 6 全局 QA / RAG 适配 / 最终打包。
