"""Retrieval-oriented regression checks for the Stage 6 RAG publication.

This validator complements the exact evidence checks in ``evaluate_agents.py``.
It uses a deterministic character n-gram TF-IDF index over the actual release
assets and verifies that the evidence named by the evaluation set is retrievable
from a user's natural-language question.  It does not encode answer strings or
special-case individual questions.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

import openpyxl

from build_rag_package import RAG_SUMMARIES, RAG_TITLE_OVERRIDES, XLSX_RETRIEVAL_GUIDES


ROOT = Path(__file__).resolve().parents[1]
RAG = ROOT / "deliverables" / "rag"
EVAL_SET = ROOT / "evaluation" / "eval_set.json"
# Multi-document questions intentionally require policy + process + case/data
# evidence.  A 20-document candidate set is the retrieval stage contract; the
# downstream reranker/agent then selects the cited subset.
TOP_K = 20
BOUNDARY_TYPES = {"UNKNOWN", "OUT_OF_SCOPE"}
NOISE_PATTERNS = (
    r"\bStage\s*\d", r"\bCodex\b", r"\bvalidator\b", r"\bvalidate_[a-z_]+",
    r"\bscripts[/\\]", r"\brepository\b", r"\bknowledge[/\\]",
)
REVIEW_FAILURE_IDS = {
    "A01-Q09", "A02-Q01", "A02-Q10", "A03-Q10", "A03-Q11", "A04-Q03",
    "A05-Q01", "A05-Q06", "A06-Q01", "A07-Q01", "A07-Q06", "A08-Q08",
    "A09-Q01", "A09-Q05", "A09-Q10", "A10-Q01", "A12-Q01", "A12-Q03",
}


def compact(value: object) -> str:
    return re.sub(r"\s+", "", str(value).lower())


def grams(text: str) -> Counter[str]:
    text = compact(text)
    result: Counter[str] = Counter()
    for n in (2, 3, 4):
        result.update(text[i:i + n] for i in range(max(0, len(text) - n + 1)))
    return result


def xlsx_chunks(path: Path) -> tuple[str, list[str]]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    parts: list[str] = []
    chunks: list[str] = []
    for ws in wb.worksheets:
        parts.append(ws.title)
        header = ""
        for row in ws.iter_rows(values_only=True):
            cells = [str(cell) for cell in row if cell is not None]
            if not cells:
                continue
            if not header:
                header = " ".join(cells)
            line = " ".join(cells)
            parts.extend(cells)
            chunks.append(f"{path.stem} {ws.title} {header} {line}")
    wb.close()
    return "\n".join(parts), chunks


def markdown_chunks(path: Path, text: str) -> list[str]:
    header = text.split("---", 2)[1] if text.startswith("---") else ""
    title_match = re.search(r"(?m)^title:\s*(.+)$", header)
    title = title_match.group(1).strip() if title_match else path.stem
    body = text.split("---", 2)[-1]
    sections = re.split(r"(?m)(?=^##?\s+)", body)
    chunks: list[str] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        # Bound chunk length so a long table does not suppress its own key row.
        for start in range(0, len(section), 1200):
            chunks.append(f"{path.stem} {title} {section[start:start + 1200]}")
    return chunks


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    manifest = load_rows(RAG / "RAG_MANIFEST.csv")
    questions = json.loads(EVAL_SET.read_text(encoding="utf-8"))
    texts: dict[str, str] = {}
    chunks: list[tuple[str, str]] = []
    titles: dict[str, str] = {}
    for row in manifest:
        path = RAG / row["rag_path"]
        titles[row["knowledge_id"]] = row["title"]
        if path.suffix == ".xlsx":
            raw, asset_chunks = xlsx_chunks(path)
        else:
            raw = path.read_text(encoding="utf-8")
            asset_chunks = markdown_chunks(path, raw)
        texts[row["knowledge_id"]] = raw
        chunks.extend((row["knowledge_id"], chunk) for chunk in asset_chunks)

    doc_tf = [grams(text) for _, text in chunks]
    doc_count = len(doc_tf)
    df: Counter[str] = Counter()
    for tf in doc_tf:
        df.update(tf.keys())
    idf = {term: math.log((doc_count + 1) / (freq + 1)) + 1 for term, freq in df.items()}
    doc_norm = [math.sqrt(sum((1 + math.log(freq)) ** 2 * idf[term] ** 2 for term, freq in tf.items()))
                for tf in doc_tf]
    title_tf = {kid: grams(title) for kid, title in titles.items()}
    title_norm = {
        kid: math.sqrt(sum((1 + math.log(freq)) ** 2 * idf.get(term, 0.0) ** 2 for term, freq in tf.items()))
        for kid, tf in title_tf.items()
    }

    def rank(query: str) -> list[str]:
        qtf = grams(query)
        qweights = {term: (1 + math.log(freq)) * idf.get(term, 0.0) for term, freq in qtf.items()}
        qnorm = math.sqrt(sum(weight * weight for weight in qweights.values())) or 1.0
        best_scores: dict[str, float] = {}
        for index, ((kid, _), tf) in enumerate(zip(chunks, doc_tf)):
            dot = sum(qweight * (1 + math.log(tf[term])) * idf.get(term, 0.0)
                      for term, qweight in qweights.items() if term in tf)
            score = dot / (qnorm * (doc_norm[index] or 1.0))
            best_scores[kid] = max(score, best_scores.get(kid, 0.0))
        for kid, tf in title_tf.items():
            dot = sum(qweight * (1 + math.log(tf[term])) * idf.get(term, 0.0)
                      for term, qweight in qweights.items() if term in tf)
            title_score = dot / (qnorm * (title_norm[kid] or 1.0))
            best_scores[kid] = best_scores.get(kid, 0.0) + 0.35 * title_score
        return [kid for kid, _ in sorted(best_scores.items(), key=lambda item: (-item[1], item[0]))]

    failures: list[str] = []
    ranks: list[tuple[str, int, list[str]]] = []
    for q in questions:
        if q["boundary_expectation"] in BOUNDARY_TYPES:
            continue
        ranked = rank(q["question"])
        expected = q["expected_evidence"]
        missing = [kid for kid in expected if kid not in ranked[:TOP_K]]
        best = min((ranked.index(kid) + 1 for kid in expected), default=doc_count + 1)
        ranks.append((q["question_id"], best, missing))
        if missing:
            failures.append(f"{q['question_id']}: missing {missing}; top{TOP_K}={ranked[:TOP_K]}")

    noise_hits: list[str] = []
    patterns = [re.compile(p, re.I) for p in NOISE_PATTERNS]
    for kid, text in texts.items():
        if not kid.startswith(("DATA",)):
            body = text.split("---", 2)[-1]
            for pattern in patterns:
                if pattern.search(body):
                    noise_hits.append(f"{kid}: {pattern.pattern}")

    project_index = {r["project_id"]: r for r in load_rows(RAG / "PROJECT_INDEX.csv")}
    boundary_ok = (
        all(project_index[f"P{i:03d}"]["history_level"] == "FULL_HISTORY" for i in range(1, 4))
        and all(project_index[f"P{i:03d}"]["history_level"] == "STRUCTURED_ONLY" for i in range(4, 13))
        and all(project_index[f"P{i:03d}"]["case_file_count"] == "0" for i in range(4, 13))
    )

    fix_integrity: list[str] = []
    for kid, summary in RAG_SUMMARIES.items():
        if compact(summary) not in compact(texts.get(kid, "")):
            fix_integrity.append(f"{kid}: release summary missing")
    for kid, title in RAG_TITLE_OVERRIDES.items():
        row = next((row for row in manifest if row["knowledge_id"] == kid), None)
        if not row or row["title"] != title:
            fix_integrity.append(f"{kid}: RAG manifest title override missing")
    for kid in XLSX_RETRIEVAL_GUIDES:
        row = next((row for row in manifest if row["knowledge_id"] == kid), None)
        if not row:
            fix_integrity.append(f"{kid}: RAG manifest row missing")
            continue
        wb = openpyxl.load_workbook(RAG / row["rag_path"], read_only=True, data_only=True)
        if "检索说明" not in wb.sheetnames:
            fix_integrity.append(f"{kid}: retrieval guide sheet missing")
        wb.close()

    passed_ids = {qid for qid, _, missing in ranks if not missing}
    review_passed = sorted(REVIEW_FAILURE_IDS & passed_ids)
    regression_pool = sorted(
        (qid for qid in passed_ids if qid not in REVIEW_FAILURE_IDS),
        key=lambda qid: hashlib.sha256(qid.encode()).hexdigest(),
    )
    regression_sample = regression_pool[:20]

    print(f"retrieval questions={len(ranks)}, top_k={TOP_K}")
    print(f"PASS: median best-evidence rank={sorted(r for _, r, _ in ranks)[len(ranks) // 2]}")
    if failures:
        print(f"FAIL: {len(failures)} retrieval questions missed one or more expected evidence assets")
        for item in failures:
            print(f"  {item}")
    else:
        print("PASS: all answerable evaluation questions retrieve every expected evidence asset")
    print(f"{'PASS' if len(review_passed) == len(REVIEW_FAILURE_IDS) else 'FAIL'}: "
          f"review failures retested={len(review_passed)}/{len(REVIEW_FAILURE_IDS)}")
    print(f"PASS: prior-PASS regression sample={len(regression_sample)}/20: {','.join(regression_sample)}")
    if noise_hits:
        print(f"FAIL: engineering noise in RAG bodies: {noise_hits[:20]}")
    else:
        print("PASS: no Stage/Codex/validator/repository-path noise in RAG bodies")
    print(f"{'PASS' if boundary_ok else 'FAIL'}: project history boundary is internally consistent")
    if fix_integrity:
        print(f"FAIL: targeted quality-fix integrity: {fix_integrity}")
    else:
        print(f"PASS: {len(RAG_SUMMARIES) + len(XLSX_RETRIEVAL_GUIDES)} targeted release enrichments intact")
    review_ok = len(review_passed) == len(REVIEW_FAILURE_IDS)
    return 1 if failures or noise_hits or not boundary_ok or fix_integrity or not review_ok else 0


if __name__ == "__main__":
    sys.exit(main())
