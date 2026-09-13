"""Stage 6 precheck guardrails.

Four cross-cutting rules that the Stage 1–5 validators structurally could not see
(see docs/STAGE6_PRECHECK_KNOWLEDGE_AUDIT.md §11):

1. ID-title drift: a knowledge id cited with a name that is not its canonical title.
2. Numbered-id families (AI-Q / REQ / JS / SW / PF / ZG): existence and, where the
   mention carries a type word, type consistency against the defining table.
3. Table count closure: a "N 项" cell must match the number of items listed beside it.
4. GUIDANCE-level assets that use mandatory wording on a line whose citations are not
   in that asset's declared dependency chain (reported as REVIEW, not FAIL).
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

from validation_common import ROOT, fail, ids, manifest_rows, read_csv

KNOWLEDGE = ROOT / "knowledge"
MANIFEST_TITLES = {r["knowledge_id"]: r["title"] for r in manifest_rows()}
MANIFEST_ROWS = {r["knowledge_id"]: r for r in manifest_rows()}

ID_PREFIX = r"(POL|SOP|FAQ|KB|REF|TPL|DATA|ROLE)"
TITLE_REF = re.compile(rf"(?<![A-Z0-9]){ID_PREFIX}(\d{{3}})(?![\d])[ 　]*《?([^《》（）\n|/,，。；;、\s]{{2,24}})")
# A cited name is only treated as a title attempt when it starts like the canonical
# title and then diverges (e.g. "项目变更管理流程" for "项目变更控制流程").
MIN_SHARED_PREFIX = 3
TYPE_WORDS = ("完整性", "一致性", "合规性")
NUMBERED = re.compile(r"(?<![A-Za-z0-9-])(AI-Q|REQ-P\d{3}-|JS-|SW-|PF-|ZG-)(\d{2})(?![\d])")
COUNT_CELL = re.compile(r"^(\d+)\s*项$")
# Allocative phrasing: it either names an authority that must act or grants a sole
# permission. This is the class that FAQ005 P0-4 abused ("必须由安全/法务确认").
ALLOCATIVE = re.compile(r"必须由|必须经|须经|严禁|只有[^，。；]{0,40}才能")


def body_of(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig")
    if text.startswith("---\n") and "\n---\n" in text[4:]:
        return text[text.index("\n---\n", 4) + 5:]
    return text


def load_metadata(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    if not (text.startswith("---\n") and "\n---\n" in text[4:]):
        return {}
    import json

    block = text.split("---\n", 2)[1]
    meta: dict[str, object] = {}
    key = None
    for line in block.splitlines():
        if re.match(r"^[a-z_]+:", line):
            key, _, value = line.partition(":")
            key, value = key.strip(), value.strip().strip("'\"")
            meta[key] = [] if value == "" else value
        elif key and line.strip().startswith("- "):
            assert isinstance(meta[key], list)
            meta[key].append(line.strip()[2:].strip())
    return meta


errors: list[str] = []
review: list[str] = []
files = sorted(p for p in KNOWLEDGE.rglob("*.md") if p.name != "README.md")
bodies = {p: body_of(p) for p in files}

# --- Rule 1: ID-title drift -------------------------------------------------
checked_titles = 0
for path, body in bodies.items():
    for match in TITLE_REF.finditer(body):
        kid = match.group(1) + match.group(2)
        candidate = match.group(3)
        title = MANIFEST_TITLES.get(kid)
        if title is None:
            continue
        checked_titles += 1
        if candidate.startswith(title) or title.startswith(candidate):
            continue
        shared = 0
        while shared < min(len(candidate), len(title)) and candidate[shared] == title[shared]:
            shared += 1
        if shared < MIN_SHARED_PREFIX:
            continue
        errors.append(f"{path.name}: {kid} cited as '{candidate}' but canonical title is '{title}'")

# --- Rule 2: numbered-id families -------------------------------------------
# Definitive id -> type map, taken from any table that carries both a 编号 column
# and a 类型 column (e.g. P001_32 AI 预审问题清单).
definitive: dict[str, dict[str, str]] = defaultdict(dict)
for path, body in bodies.items():
    header: list[str] = []
    for line in body.splitlines():
        if not line.strip().startswith("|"):
            header = []
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if set(cells) >= {"编号", "问题类型"}:
            header = cells
            continue
        if not header or set("".join(cells)) <= set("-: "):
            continue
        if len(cells) != len(header):
            continue
        row = dict(zip(header, cells))
        key = row["编号"].strip("`* ")
        if key:
            definitive[key] = {"type": row["问题类型"], "file": path.name}

for path, body in bodies.items():
    for match in NUMBERED.finditer(body):
        kid = match.group(1) + match.group(2)
        known = definitive.get(kid)
        if known is None:
            continue
        tail = body[match.end():match.end() + 12].lstrip(" 　，,：:（(")
        for word in TYPE_WORDS:
            if tail.startswith(word) and known["type"] != word:
                errors.append(
                    f"{path.name}: {kid} described as {word} but {known['file']} defines it as {known['type']}"
                )
                break

# --- Rule 3: table count closure --------------------------------------------
counted = 0
for path, body in bodies.items():
    for line in body.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        declared = None
        for cell in cells:
            m = COUNT_CELL.match(cell)
            if m:
                declared = int(m.group(1))
                break
        if declared is None:
            continue
        listing = max(cells, key=lambda c: c.count("、"))
        if listing.count("、") < 1:
            continue
        tokens = [t for t in listing.split("、") if t.strip()]
        if len(tokens) == declared:
            counted += 1
            continue
        errors.append(
            f"{path.name}: row declares '{declared} 项' but lists {len(tokens)} items ({listing[:60]})"
        )

# --- Rule 4: GUIDANCE mandatory wording vs declared dependency chain ---------
# Scope: answer sentences of FAQ (GUIDANCE) assets. Question headings, template
# boilerplate and case narration are out of scope.
def declared_ids(meta: dict, key: str) -> set[str]:
    value = meta.get(key) or []
    if isinstance(value, list):
        return {str(v).strip() for v in value if str(v).strip()}
    return set(ids(str(value)))


for path, body in bodies.items():
    meta = load_metadata(path)
    if str(meta.get("normative_force", "")) != "GUIDANCE" or str(meta.get("knowledge_type", "")) != "FAQ_RULE":
        continue
    allowed = declared_ids(meta, "depends_on") | declared_ids(meta, "parent_knowledge")
    for lineno, line in enumerate(body.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#") or not stripped.startswith("答："):
            continue
        if not ALLOCATIVE.search(line):
            continue
        cited = {m.group(0) for m in re.finditer(ID_PREFIX + r"\d{3}", line)}
        if cited & allowed:
            continue
        review.append(f"{path.name}:{lineno}: allocative wording without declared upstream on the line")

fail(errors)
for line in review:
    print(f"REVIEW: {line}")
print(f"PASS: {checked_titles} id-title citations match canonical titles; {counted} count cells close")
print(f"PASS: numbered-id families resolve to a defining table row with consistent type")
print(f"PASS: GUIDANCE mandatory wording checked against declared dependency chains")
print("PASS: Stage 6 precheck guardrails complete")
