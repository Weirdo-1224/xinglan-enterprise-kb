# 质量门

每个 Stage 必须按顺序满足以下质量门：

1. Gate 1：Schema 完整，字段、枚举和格式符合契约。
2. Gate 2：知识 ID 唯一，文件名唯一且命名合规。
3. Gate 3：企业事实一致，所有公司事实回指企业 Canonical Facts。
4. Gate 4：来源血缘完整；合成内容有声明；`VERIFIED` 来源无占位和必填缺失。
5. Gate 5：模拟数据与公开事实不混淆，内部阈值不冒充国家要求。
6. Gate 6：制度、SOP、FAQ、案例和模板逻辑一致。
7. Gate 7：12 个 Agent 的每项核心能力均映射到具体资产。
8. Gate 8：同一项目跨文件的时间、人员、成本、合同、变更和验收事实一致。
9. Gate 9：每个最终 ZIP 文件数不超过 100。
10. Gate 10：上传 ZIP 根目录平铺，不含子目录。
11. Gate 11 — Semantic Dependency Validity：SOP、FAQ/RULE 和项目案例具有业务可解释的上游依赖与 `dependency_rationale`。
12. Gate 12 — Capability Coverage Validity：逐 Agent、逐 capability 校验所需资产类型和明确 ID；仅全部满足时为 `FULL`。
13. Gate 13 — Source Applicability Validity：先判断适用性，再判断规范效力、状态、有效日期/版本、具体性和来源权威；官方来源不自动直接适用。
14. Gate 14 — Project Canonical Consistency：P001/P002/P003 各有唯一项目事实源，Manifest 文件集合、日期、金额、风险、变更和验收与其一致。
15. Gate 15 — No Mechanical ID Mapping：`SOPnnn → POLnnn` 或 `FAQnnn → SOPnnn` 的单一同号依赖一律失败；只有写入显式白名单且具备可审计业务理由时才能例外。当前白名单为空。

Stage 1.1 只验证规划层和项目 Canonical Facts；没有正文时，正文元数据与正文内容校验必须明确报告跳过。任何语义门失败，Stage 1.1 不得标记 PASS。

当前 `PACKAGE_PLAN.csv` 的 100 / 99 / 40 是 Stage 1/1.1 逻辑规划，不是最终上传分包，也不作为 Stage 2 阻塞项。Gate 9 和 Gate 10 的最终验收在 Stage 6 package rebalancing 后执行：每包不超过 100 个文件并建议保留 10~20 个文件余量，包内文件平铺；Package 只作为运输单元，不改变知识 ID、领域或语义归属。
