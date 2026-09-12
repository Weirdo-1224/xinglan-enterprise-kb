# 来源策略

Stage 1.1 只规划来源需求，不执行公开资料搜集。Stage 2 按每项核心 POLICY 的 `source_strategy`、`required_source_categories` 和 `minimum_source_count` 搜集，并逐条登记来源和知识血缘。

制度的目标合成方式为：公开权威依据 + 公开企业实践 + 公开业务案例 + 星澜模拟参数 → 星澜企业制度。内部阈值、部门名称、审批层级和时限必须列入 `synthetic_fields`，不得伪装成公共规则。

每条来源分别判断：

1. `source_authority`：来源是谁、其公开身份是什么。
2. `normative_force`：在当前关系中是强制、合同、内部强制、指导、参考还是无规范效力。
3. `applicability`：对当前星澜业务是直接、附条件、类比、不适用还是待复核。

优先搜集官方现行文本，再补公开企业实践和公开案例，但来源权威不能替代适用性判断。政府采购规则对于普通科技企业内部采购不得自动标为 `DIRECT`；公开企业制度不得复制为星澜制度；公开案例不得成为强制规则。

`VERIFIED` 来源必须具有非占位标题、发布者、URL、访问日期、确定的来源类型、来源权威、规范效力、适用性和领域。`PENDING` 可以保留空字段，但只能作为候选，不得进入已发布正文。冲突解析以 `enterprise_model/KNOWLEDGE_GOVERNANCE.md` 为准。
