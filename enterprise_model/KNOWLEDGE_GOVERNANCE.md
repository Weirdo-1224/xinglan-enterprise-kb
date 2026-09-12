# 知识治理

## 三维来源判断

`authority_level`（L0~L5）仅表示知识资产在星澜知识体系中的层级，不再单独决定冲突结果。每条来源还必须记录三个互相独立的维度：

- `source_authority`：`OFFICIAL`、`PUBLIC_CORPORATE`、`PUBLIC_CASE`、`SYNTHETIC_DERIVED`、`SYNTHETIC`、`INTERNAL_DERIVED`。
- `normative_force`：`MANDATORY`、`CONTRACTUAL`、`INTERNAL_MANDATORY`、`GUIDANCE`、`REFERENCE`、`NONE`。
- `applicability`：`DIRECT`、`CONDITIONAL`、`ANALOGICAL`、`NOT_APPLICABLE`、`PENDING_REVIEW`。

官方资料只说明来源权威，不代表其必然直接适用于星澜。比如政府采购制度对于星澜普通内部采购通常是 `OFFICIAL + REFERENCE + ANALOGICAL`；只有业务主体、交易类型和适用条件均满足时，才能评为 `DIRECT`。

## 冲突解析顺序

冲突处理使用以下决策顺序，而不是简单的 L0 > L1 > ...：

```text
candidates = remove(applicability == NOT_APPLICABLE)
if no candidate with applicability == DIRECT:
    keep CONDITIONAL only when its stated conditions are satisfied
    use ANALOGICAL only as reference; never convert it into an internal mandate
prefer stronger normative_force in the current scope
    MANDATORY / CONTRACTUAL / INTERNAL_MANDATORY are compared by their applicable legal,
    contractual and organizational scopes, not by a universal numeric ranking
prefer active; deprecated/archived cannot be the current rule
when force and scope are comparable, prefer later effective date and current version
then prefer the rule that is more specific to the actor, transaction and scenario
use source_authority as supporting evidence, not as an applicability shortcut
if material disagreement remains: return CONFLICT and request human resolution
```

合同义务、强制法律和内部强制制度可能作用于不同范围，因此不得仅凭枚举顺序覆盖。任何 `PENDING_REVIEW` 来源均不得作为最终依据。回答状态为 `EXPLICIT`、`DERIVED`、`UNKNOWN`、`CONFLICT`、`OUT_OF_SCOPE`。

## 生命周期

知识新增必须经过来源、适用性、语义依赖和责任人审核；版本更新必须记录有效日期和被替代项；冲突必须留存比较维度和裁决；废止知识停止现行使用但保留归档与引用链。所有合成企业规则必须与公共依据分层，项目事实以 `enterprise_model/projects/*_CANONICAL_FACTS.yaml` 为项目唯一事实源。
