from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests/KNOWLEDGE_MANIFEST.csv"
AGENTS = {f"A{i:02d}" for i in range(1, 13)}
KNOWLEDGE_TYPES = {"ENTERPRISE_FOUNDATION", "PUBLIC_REFERENCE", "POLICY", "SOP", "FAQ_RULE", "ROLE", "PROJECT_CASE", "TEMPLATE", "BUSINESS_DATA"}
PACKAGES = {"PACKAGE-01", "PACKAGE-02", "PACKAGE-03"}

def read_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def manifest_rows():
    return read_csv(MANIFEST)

def ids(value):
    return [x.strip() for x in (value or "").split(";") if x.strip()]

def fail(messages):
    for message in messages:
        print(f"FAIL: {message}")
    if messages:
        raise SystemExit(1)
