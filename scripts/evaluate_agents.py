"""Offline deterministic evaluation of the 12-agent evaluation set.

There is no live RAG platform or agent runtime in this repository, so the
harness measures, for every question in evaluation/shards/*.json, whether the
RAG publication corpus (deliverables/rag/) supports the golden route, answer,
evidence and boundary behavior:

- Route Accuracy      : expected evidence assets actually serve the question's
                        agent (served_agents in KNOWLEDGE_MANIFEST.csv).
                        Boundary questions (UNKNOWN/OUT_OF_SCOPE) are exempt
                        from the evidence-route check and instead validated
                        against PROJECT_INDEX / corpus absence.
- Answer Correctness  : every expected_answer_point appears verbatim in the
                        union of the question's evidence assets.
- Evidence Correctness: evidence ids exist in RAG_MANIFEST.csv and jointly
                        contain all answer points.
- Boundary Accuracy   : UNKNOWN questions are genuinely unanswerable from the
                        corpus (no answer material exists; STRUCTURED_ONLY
                        projects carry no case archive), OUT_OF_SCOPE topics
                        are absent, ANSWER/CONFLICT questions are answerable.
- Hallucination Rate  : share of questions whose forbidden_facts (plausible
                        but wrong values) appear in the evidence/corpus.

Targets: Route >= 95%, Answer >= 90%, Evidence >= 95%, Boundary >= 95%,
Hallucination <= 5%.
"""

import csv
import json
import re
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
RAG = ROOT / "deliverables" / "rag"
SHARDS = ROOT / "evaluation" / "shards"
MERGED = ROOT / "evaluation" / "eval_set.json"
REPORT = ROOT / "evaluation" / "EVALUATION_REPORT.md"

TARGETS = {"route": 95.0, "answer": 90.0, "evidence": 95.0, "boundary": 95.0, "hallucination_max": 5.0}

BOUNDARY_TYPES = {"UNKNOWN", "OUT_OF_SCOPE"}
QUESTION_TYPES = {
    "FACT_QUERY", "POLICY_JUDGMENT", "PROCESS_GUIDANCE", "CROSS_DOCUMENT_REASONING",
    "HISTORICAL_CASE", "STRUCTURED_DATA_QUERY", "TEMPLATE_GENERATION",
    "CONFLICT", "UNKNOWN", "OUT_OF_SCOPE",
}


def norm(text: str) -> str:
    return re.sub(r"\s+", "", text)


def load_manifest() -> dict[str, dict[str, str]]:
    with open(ROOT / "manifests" / "KNOWLEDGE_MANIFEST.csv", encoding="utf-8-sig", newline="") as fh:
        return {r["knowledge_id"]: r for r in csv.DictReader(fh)}


def load_rag_manifest() -> dict[str, dict[str, str]]:
    with open(RAG / "RAG_MANIFEST.csv", encoding="utf-8-sig", newline="") as fh:
        return {r["knowledge_id"]: r for r in csv.DictReader(fh)}


def load_project_index() -> dict[str, str]:
    with open(ROOT / "manifests" / "PROJECT_INDEX.csv", encoding="utf-8-sig", newline="") as fh:
        return {r["project_id"]: r["history_level"] for r in csv.DictReader(fh)}


def xlsx_text(path: Path) -> str:
    wb = openpyxl.load_workbook(path, read_only=True)
    parts = []
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            parts.extend(str(c) for c in row if c is not None)
    wb.close()
    return "\n".join(parts)


class Corpus:
    def __init__(self) -> None:
        self.texts: dict[str, str] = {}
        rag_manifest = load_rag_manifest()
        for kid, row in rag_manifest.items():
            path = RAG / row["rag_path"]
            raw = xlsx_text(path) if path.suffix == ".xlsx" else path.read_text(encoding="utf-8")
            self.texts[kid] = norm(raw)
        self.texts["PROJECT_INDEX"] = norm((RAG / "PROJECT_INDEX.csv").read_text(encoding="utf-8-sig"))
        self.full_text = "\n".join(self.texts.values())
        self.case_project_ids = {
            row["project_id"] for row in rag_manifest.values()
            if row["knowledge_type"] == "PROJECT_CASE" and row["project_id"].startswith("P")
        }

    def evidence_text(self, ids: list[str]) -> str:
        return "\n".join(self.texts.get(i, "") for i in ids)


def evaluate() -> int:
    questions = []
    for shard in sorted(SHARDS.glob("*.json")):
        questions.extend(json.loads(shard.read_text(encoding="utf-8")))
    MERGED.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest = load_manifest()
    project_index = load_project_index()
    corpus = Corpus()

    structural_errors = []
    seen_ids = set()
    for q in questions:
        for field in ("question_id", "agent_id", "question_type", "question", "gold_answer",
                      "expected_answer_points", "expected_evidence", "forbidden_facts",
                      "boundary_expectation"):
            if field not in q:
                structural_errors.append(f"{q.get('question_id', '?')}: missing field {field}")
        qid = q["question_id"]
        if qid in seen_ids:
            structural_errors.append(f"{qid}: duplicate question_id")
        seen_ids.add(qid)
        if q["question_type"] not in QUESTION_TYPES:
            structural_errors.append(f"{qid}: bad question_type {q['question_type']}")
        if q["boundary_expectation"] not in {"ANSWER", "UNKNOWN", "OUT_OF_SCOPE", "CONFLICT"}:
            structural_errors.append(f"{qid}: bad boundary_expectation {q['boundary_expectation']}")
        if q["question_type"] in BOUNDARY_TYPES and q["question_type"] != q["boundary_expectation"]:
            structural_errors.append(f"{qid}: type {q['question_type']} != boundary {q['boundary_expectation']}")
    if structural_errors:
        for e in structural_errors:
            print(f"FAIL: {e}")
        return 1

    agents = sorted({q["agent_id"] for q in questions})
    per_question = []
    for q in questions:
        qid, agent = q["question_id"], q["agent_id"]
        boundary = q["boundary_expectation"]
        evidence_ids = q["expected_evidence"]
        points = [norm(p) for p in q["expected_answer_points"]]
        forbidden = [norm(f) for f in q["forbidden_facts"]]
        is_boundary_q = boundary in BOUNDARY_TYPES
        evidence_text = corpus.evidence_text(evidence_ids)

        missing_assets = [e for e in evidence_ids if e not in corpus.texts]
        route_ok = is_boundary_q or all(
            agent in manifest.get(e, {}).get("served_agents", "").split(";") for e in evidence_ids
        )
        evidence_ok = not missing_assets and (is_boundary_q or all(p in evidence_text for p in points))
        answer_ok = all(p in evidence_text for p in points) if not is_boundary_q else True

        if boundary == "UNKNOWN":
            mentioned = re.findall(r"P\d{3}", q["question"] + q["gold_answer"])
            structured = [p for p in mentioned if project_index.get(p) == "STRUCTURED_ONLY"]
            boundary_ok = all(f not in corpus.full_text for f in forbidden)
            if structured:
                boundary_ok = boundary_ok and all(p not in corpus.case_project_ids for p in structured)
        elif boundary == "OUT_OF_SCOPE":
            boundary_ok = all(f not in corpus.full_text for f in forbidden) and all(
                p not in corpus.full_text for p in points
            )
        else:
            boundary_ok = answer_ok

        hallucination_hit = [f for f in forbidden if f in evidence_text]
        per_question.append({
            "question_id": qid, "agent_id": agent, "question_type": q["question_type"],
            "boundary_expectation": boundary,
            "route": route_ok, "answer": answer_ok, "evidence": evidence_ok,
            "boundary": boundary_ok, "hallucination": not hallucination_hit,
            "missing_assets": missing_assets, "hallucination_hits": hallucination_hit,
        })

    def rate(key: str, subset: list[dict]) -> float:
        return 100.0 * sum(1 for r in subset if r[key]) / len(subset) if subset else 0.0

    total = len(per_question)
    metrics = {
        "route": rate("route", per_question),
        "answer": rate("answer", per_question),
        "evidence": rate("evidence", per_question),
        "boundary": rate("boundary", per_question),
        "hallucination": 100.0 - rate("hallucination", per_question),
    }
    unknown_subset = [r for r in per_question if r["boundary_expectation"] in BOUNDARY_TYPES]

    lines = [
        "# 12 Agent Offline Evaluation Report", "",
        f"- 评测题总数：{total}（Agent 数：{len(agents)}）",
        f"- 评测方式：离线确定性评测（无运行中的 RAG 平台/Agent 实例，基于 RAG 发布版语料逐字核验）",
        f"- UNKNOWN / OUT_OF_SCOPE 题：{len(unknown_subset)} 道，单独统计", "",
        "## Overall Metrics", "",
        "| 指标 | 结果 | 目标 | 判定 |", "| --- | --- | --- | --- |",
        f"| Route Accuracy | {metrics['route']:.1f}% | >= {TARGETS['route']}% | {'PASS' if metrics['route'] >= TARGETS['route'] else 'FAIL'} |",
        f"| Answer Correctness | {metrics['answer']:.1f}% | >= {TARGETS['answer']}% | {'PASS' if metrics['answer'] >= TARGETS['answer'] else 'FAIL'} |",
        f"| Evidence Correctness | {metrics['evidence']:.1f}% | >= {TARGETS['evidence']}% | {'PASS' if metrics['evidence'] >= TARGETS['evidence'] else 'FAIL'} |",
        f"| Boundary Accuracy | {metrics['boundary']:.1f}% | >= {TARGETS['boundary']}% | {'PASS' if metrics['boundary'] >= TARGETS['boundary'] else 'FAIL'} |",
        f"| Hallucination Rate | {metrics['hallucination']:.1f}% | <= {TARGETS['hallucination_max']}% | {'PASS' if metrics['hallucination'] <= TARGETS['hallucination_max'] else 'FAIL'} |",
        "", "## Per-Agent Breakdown", "",
        "| Agent | 题数 | Route | Answer | Evidence | Boundary | Hallucination |", "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for agent in agents:
        subset = [r for r in per_question if r["agent_id"] == agent]
        lines.append(
            f"| {agent} | {len(subset)} | {rate('route', subset):.1f}% | {rate('answer', subset):.1f}% "
            f"| {rate('evidence', subset):.1f}% | {rate('boundary', subset):.1f}% "
            f"| {100.0 - rate('hallucination', subset):.1f}% |"
        )
    lines += ["", "## Boundary Questions (UNKNOWN / OUT_OF_SCOPE)", "",
              "| question_id | 类型 | Boundary 判定 |", "| --- | --- | --- |"]
    for r in unknown_subset:
        lines.append(f"| {r['question_id']} | {r['boundary_expectation']} | {'PASS' if r['boundary'] else 'FAIL'} |")
    failures = [r for r in per_question if not all([r["route"], r["answer"], r["evidence"], r["boundary"], r["hallucination"]])]
    lines += ["", "## Failures", ""]
    if failures:
        for r in failures:
            bad = [k for k in ("route", "answer", "evidence", "boundary", "hallucination") if not r[k]]
            lines.append(f"- {r['question_id']} ({r['agent_id']}, {r['question_type']}): {', '.join(bad)}"
                         + (f" hallucination_hits={r['hallucination_hits']}" if r["hallucination_hits"] else ""))
    else:
        lines.append("无失败题。")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"questions={total} agents={len(agents)} boundary_questions={len(unknown_subset)}")
    for key, target in (("route", TARGETS["route"]), ("answer", TARGETS["answer"]),
                        ("evidence", TARGETS["evidence"]), ("boundary", TARGETS["boundary"])):
        status = "PASS" if metrics[key] >= target else "FAIL"
        print(f"{status}: {key} {metrics[key]:.1f}% (target >= {target}%)")
    status = "PASS" if metrics["hallucination"] <= TARGETS["hallucination_max"] else "FAIL"
    print(f"{status}: hallucination {metrics['hallucination']:.1f}% (target <= {TARGETS['hallucination_max']}%)")
    overall = (metrics["route"] >= TARGETS["route"] and metrics["answer"] >= TARGETS["answer"]
               and metrics["evidence"] >= TARGETS["evidence"] and metrics["boundary"] >= TARGETS["boundary"]
               and metrics["hallucination"] <= TARGETS["hallucination_max"])
    print(f"\nAgent evaluation {'PASS' if overall else 'FAIL'}; report at {REPORT.relative_to(ROOT)}")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(evaluate())
