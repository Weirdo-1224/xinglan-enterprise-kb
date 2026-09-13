"""Stage 6 final delivery validation.

Checks the global QA / RAG publication / agent evaluation / final packaging
deliverables end to end:

- all 239 governed assets still exist under knowledge/
- RAG publication holds the correct counts and every published md keeps the
  lightweight identity header and its key business rules
- no engineering noise, TODO or placeholder in published assets
- history_level governance is consistent (PROJECT_INDEX vs RAG_MANIFEST)
- upload ZIPs are <=100 files, flat, and match the publication listing
- evaluation set and report are complete and meet their targets
- DELIVERY_GUIDE.md exists with the required sections
"""

from __future__ import annotations

import csv
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"
RAG = ROOT / "deliverables" / "rag"
PACKAGES = ROOT / "deliverables" / "packages"

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)
    print(f"FAIL: {msg}")


def ok(msg: str) -> None:
    print(f"PASS: {msg}")


def read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


manifest = read_csv(ROOT / "manifests" / "KNOWLEDGE_MANIFEST.csv")
rag_manifest = {r["knowledge_id"]: r for r in read_csv(RAG / "RAG_MANIFEST.csv")} if (RAG / "RAG_MANIFEST.csv").is_file() else {}

# 1. governed originals intact: every manifest asset exists under knowledge/
orig_missing = []
for r in manifest:
    sub = {"POLICY": "core", "SOP": "core", "FAQ_RULE": "core", "ENTERPRISE_FOUNDATION": "core",
           "PUBLIC_REFERENCE": "core", "ROLE": "core", "PROJECT_CASE": "cases",
           "TEMPLATE": "templates", "BUSINESS_DATA": "business_data"}[r["knowledge_type"]]
    if not (KNOWLEDGE / sub / r["filename"]).is_file():
        orig_missing.append(r["knowledge_id"])
if len(manifest) == 239 and not orig_missing:
    ok("239/239 governed assets intact under knowledge/")
else:
    fail(f"governed assets: manifest={len(manifest)}, missing={orig_missing}")

# 2. RAG publication counts
counts = {d: len(list((RAG / d).iterdir())) if (RAG / d).is_dir() else -1
          for d in ("core", "cases", "templates", "business_data")}
if counts == {"core": 100, "cases": 99, "templates": 28, "business_data": 12} and len(rag_manifest) == 239:
    ok(f"RAG publication counts correct {counts}, manifest rows={len(rag_manifest)}")
else:
    fail(f"RAG counts {counts}, rag manifest rows={len(rag_manifest)}")

# 3. identity header + no engineering noise + no placeholder in published md
NOISE = ("validator", "validate_", "scripts/", ".py", "Codex", "enterprise_model/",
         "repository", "KNOWLEDGE_MANIFEST", "source_strategy", "synthetic_fields",
         "minimum_source_count", "dependency_rationale")
PLACEHOLDER = ("TODO", "TBD", "PLACEHOLDER", "待补充", "待完善", "待填写", "此处填写", "示例内容", "XXXX")
REQUIRED_KEYS = ("knowledge_id", "knowledge_type", "domain", "title", "served_agents", "source_type")
noise_hits, placeholder_hits, header_bad = [], [], []
published_md = list(RAG.glob("core/*.md")) + list(RAG.glob("cases/*.md")) + list(RAG.glob("templates/*.md"))
for path in published_md:
    text = path.read_text(encoding="utf-8")
    header = text.split("---", 2)[1] if text.startswith("---") else ""
    for key in REQUIRED_KEYS:
        if f"{key}:" not in header:
            header_bad.append(f"{path.name}: missing {key}")
    body = text.split("---", 2)[-1]
    for token in NOISE:
        if token in body:
            noise_hits.append(f"{path.name}: {token}")
    for token in PLACEHOLDER:
        if token in body:
            placeholder_hits.append(f"{path.name}: {token}")
if not header_bad:
    ok(f"all {len(published_md)} published md keep the lightweight identity header")
else:
    fail(f"identity header problems: {header_bad[:5]}")
if not noise_hits:
    ok("no engineering noise in published assets")
else:
    fail(f"engineering noise: {noise_hits[:5]}")
if not placeholder_hits:
    ok("no TODO/placeholder in published assets")
else:
    fail(f"placeholders: {placeholder_hits[:5]}")

# 4. key business rules preserved in the RAG version
SENTINELS = {
    "KB005": ["5 万元至 20 万元", "100 万元"],
    "POL011": ["5 万元至 20 万元原则上三家比选", "20 万元至 100 万元竞争性采购"],
    "SOP016": ["三家比选", "竞争性"],
    "FAQ007": ["5 万元至 20 万元", "100 万元"],
    "TPL018": ["原则上三家比选", "20万至100万元竞争性"],
    "POL007": ["变更"],
    "KB007": ["数据分类"],
    "P001_11": ["2024-04-08"],
    "P002_19": ["18 万"],
    "P003_11": ["2024-06-06", "2024-09-10"],
    "CASE001": ["2024-06-12"],
    "CASE003": ["P003 沉淀 3 项"],
    "P001_19": ["预备费 15 万元"],
}
rule_misses = []
for kid, needles in SENTINELS.items():
    row = rag_manifest.get(kid)
    if not row:
        rule_misses.append(f"{kid}: not in RAG manifest")
        continue
    text = (RAG / row["rag_path"]).read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            rule_misses.append(f"{kid}: lost '{needle}'")
if not rule_misses:
    ok(f"key business rules preserved ({len(SENTINELS)} sentinel assets)")
else:
    fail(f"business rules lost: {rule_misses}")

# 5. history_level governance
index_rows = read_csv(ROOT / "manifests" / "PROJECT_INDEX.csv")
index = {r["project_id"]: r["history_level"] for r in index_rows}
index_ok = (len(index_rows) == 12
            and all(index.get(f"P{i:03d}") == "FULL_HISTORY" for i in (1, 2, 3))
            and all(index.get(f"P{i:03d}") == "STRUCTURED_ONLY" for i in range(4, 13)))
rag_hl = [(r["knowledge_id"], r["history_level"]) for r in rag_manifest.values()
          if r["knowledge_type"] == "PROJECT_CASE"]
rag_hl_ok = rag_hl and all(h == "FULL_HISTORY" for _, h in rag_hl)
non_case_hl = [r["knowledge_id"] for r in rag_manifest.values()
               if r["knowledge_type"] != "PROJECT_CASE" and r["history_level"]]
if index_ok and rag_hl_ok and not non_case_hl:
    ok("history_level correct: P001~P003 FULL_HISTORY, P004~P012 STRUCTURED_ONLY, 99 PROJECT_CASE tagged")
else:
    fail(f"history_level problems: index_ok={index_ok}, rag_case_tags={len(rag_hl)}, stray={non_case_hl[:5]}")

# 6. ZIP constraints and filename agreement with the publication listing
rag_names = {r["rag_path"].split("/")[-1] for r in rag_manifest.values()} | {"PROJECT_INDEX.csv"}
zip_problems = []
zips = sorted(PACKAGES.glob("*.zip"))
if len(zips) != 4:
    zip_problems.append(f"expected 4 ZIPs, found {len(zips)}")
for zp in zips:
    with zipfile.ZipFile(zp) as zf:
        infos = zf.infolist()
        if len(infos) > 100:
            zip_problems.append(f"{zp.name}: {len(infos)} files > 100")
        for info in infos:
            if "/" in info.filename or "\\" in info.filename:
                zip_problems.append(f"{zp.name}: non-flat entry {info.filename}")
            if info.filename.startswith("#U"):
                zip_problems.append(f"{zp.name}: escaped filename {info.filename}")
            if info.filename not in rag_names:
                zip_problems.append(f"{zp.name}: {info.filename} not in publication listing")
if not zip_problems:
    ok("4 ZIPs: <=100 files each, flat, filenames match publication listing, no #Uxxxx")
else:
    fail(f"ZIP problems: {zip_problems[:5]}")

# 7. evaluation data complete
eval_file = ROOT / "evaluation" / "eval_set.json"
report_file = ROOT / "evaluation" / "EVALUATION_REPORT.md"
if not eval_file.is_file() or not report_file.is_file():
    fail("evaluation/eval_set.json or EVALUATION_REPORT.md missing; run scripts/evaluate_agents.py")
else:
    questions = json.loads(eval_file.read_text(encoding="utf-8"))
    agents = {q["agent_id"] for q in questions}
    types = {q["question_type"] for q in questions}
    per_agent = {a: sum(1 for q in questions if q["agent_id"] == a) for a in agents}
    report = report_file.read_text(encoding="utf-8")
    if (120 <= len(questions) <= 180 and len(agents) == 12
            and all(10 <= n <= 15 for n in per_agent.values()) and len(types) == 10):
        ok(f"evaluation set complete: {len(questions)} questions, 12 agents, 10 types")
    else:
        fail(f"evaluation set incomplete: {len(questions)} questions, agents={len(agents)}, types={len(types)}, per_agent={per_agent}")
    if "FAIL" not in report.split("## Failures")[0]:
        ok("evaluation report meets all metric targets")
    else:
        fail("evaluation report contains target FAILs")

# 8. DELIVERY_GUIDE.md
guide = ROOT / "deliverables" / "DELIVERY_GUIDE.md"
REQUIRED_SECTIONS = ("239", "FULL_HISTORY", "STRUCTURED_ONLY", "PUBLIC", "SYNTHETIC",
                     "上传顺序", "已知边界", "PACKAGE-01", "PACKAGE-02", "PACKAGE-03", "PACKAGE-04")
if not guide.is_file():
    fail("deliverables/DELIVERY_GUIDE.md missing")
else:
    text = guide.read_text(encoding="utf-8")
    absent = [s for s in REQUIRED_SECTIONS if s not in text]
    if absent:
        fail(f"DELIVERY_GUIDE.md missing sections/tokens: {absent}")
    else:
        ok("DELIVERY_GUIDE.md exists with all required sections")

print()
if errors:
    print(f"Stage 6 final delivery validation FAIL ({len(errors)} errors)")
    raise SystemExit(1)
print("Stage 6 final delivery validation PASS")
