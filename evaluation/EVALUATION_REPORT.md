# 12 Agent Offline Evaluation Report

- 评测题总数：144（Agent 数：12）
- 评测方式：离线确定性评测（无运行中的 RAG 平台/Agent 实例，基于 RAG 发布版语料逐字核验）
- UNKNOWN / OUT_OF_SCOPE 题：23 道，单独统计

## Overall Metrics

| 指标 | 结果 | 目标 | 判定 |
| --- | --- | --- | --- |
| Route Accuracy | 100.0% | >= 95.0% | PASS |
| Answer Correctness | 100.0% | >= 90.0% | PASS |
| Evidence Correctness | 100.0% | >= 95.0% | PASS |
| Boundary Accuracy | 100.0% | >= 95.0% | PASS |
| Hallucination Rate | 0.0% | <= 5.0% | PASS |

## Per-Agent Breakdown

| Agent | 题数 | Route | Answer | Evidence | Boundary | Hallucination |
| --- | --- | --- | --- | --- | --- | --- |
| A01 | 12 | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% |
| A02 | 12 | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% |
| A03 | 12 | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% |
| A04 | 12 | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% |
| A05 | 12 | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% |
| A06 | 12 | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% |
| A07 | 12 | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% |
| A08 | 12 | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% |
| A09 | 12 | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% |
| A10 | 12 | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% |
| A11 | 12 | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% |
| A12 | 12 | 100.0% | 100.0% | 100.0% | 100.0% | 0.0% |

## Boundary Questions (UNKNOWN / OUT_OF_SCOPE)

| question_id | 类型 | Boundary 判定 |
| --- | --- | --- |
| A01-Q10 | UNKNOWN | PASS |
| A01-Q12 | OUT_OF_SCOPE | PASS |
| A02-Q04 | UNKNOWN | PASS |
| A02-Q12 | OUT_OF_SCOPE | PASS |
| A03-Q12 | UNKNOWN | PASS |
| A04-Q10 | UNKNOWN | PASS |
| A04-Q11 | OUT_OF_SCOPE | PASS |
| A05-Q11 | UNKNOWN | PASS |
| A05-Q12 | OUT_OF_SCOPE | PASS |
| A06-Q11 | UNKNOWN | PASS |
| A06-Q12 | OUT_OF_SCOPE | PASS |
| A07-Q10 | UNKNOWN | PASS |
| A07-Q11 | OUT_OF_SCOPE | PASS |
| A08-Q10 | UNKNOWN | PASS |
| A08-Q11 | OUT_OF_SCOPE | PASS |
| A09-Q11 | UNKNOWN | PASS |
| A09-Q12 | OUT_OF_SCOPE | PASS |
| A10-Q11 | UNKNOWN | PASS |
| A10-Q12 | OUT_OF_SCOPE | PASS |
| A11-Q10 | UNKNOWN | PASS |
| A11-Q11 | OUT_OF_SCOPE | PASS |
| A12-Q10 | UNKNOWN | PASS |
| A12-Q11 | OUT_OF_SCOPE | PASS |

## Failures

无失败题。
