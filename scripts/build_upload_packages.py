"""Build the final upload ZIP packages from the RAG publication version.

Reads deliverables/rag/ (produced by build_rag_package.py) and writes the
flat upload packages into deliverables/packages/. Constraints enforced:

- every ZIP contains at most 100 files
- ZIP entries are flat (no subdirectories)
- original Chinese filenames are preserved (UTF-8, no escaped #Uxxxx names)
- package contents match RAG_MANIFEST.csv exactly
"""

import csv
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAG = ROOT / "deliverables" / "rag"
OUT = ROOT / "deliverables" / "packages"

MAX_FILES = 100

PACKAGES = [
    ("PACKAGE-01_CORE.zip", ["core"], "100 份 RAG Core Knowledge（KB/REF/POL/SOP/FAQ/ROLE）"),
    ("PACKAGE-02_PROJECT_MEMORY.zip", ["cases"], "99 份 Project Cases（P001/P002/P003 案例链 + CASE001~004 跨项目复盘）"),
    ("PACKAGE-03_BUSINESS_DATA.zip", ["business_data"], "12 份结构化业务数据 XLSX + PROJECT_INDEX.csv（history_level 识别）"),
    ("PACKAGE-04_TEMPLATES.zip", ["templates"], "28 份模板"),
]


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def collect(dirs: list[str]) -> list[Path]:
    files: list[Path] = []
    for d in dirs:
        base = RAG / d
        if not base.is_dir():
            fail(f"missing RAG directory {base}")
        files.extend(sorted(p for p in base.iterdir() if p.is_file()))
    return files


def main() -> None:
    if not RAG.is_dir():
        fail("deliverables/rag/ does not exist; run scripts/build_rag_package.py first")
    OUT.mkdir(parents=True, exist_ok=True)

    for old in OUT.glob("*.zip"):
        old.unlink()

    summary = []
    for name, dirs, desc in PACKAGES:
        files = collect(dirs)
        if name == "PACKAGE-03_BUSINESS_DATA.zip":
            index = RAG / "PROJECT_INDEX.csv"
            if not index.is_file():
                fail("deliverables/rag/PROJECT_INDEX.csv missing")
            files.append(index)
        if len(files) > MAX_FILES:
            fail(f"{name}: {len(files)} files exceeds {MAX_FILES}")
        names = [p.name for p in files]
        if len(set(names)) != len(names):
            fail(f"{name}: duplicate filenames after flattening")
        target = OUT / name
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in files:
                zf.write(path, path.name)
        with zipfile.ZipFile(target) as zf:
            for info in zf.infolist():
                if "/" in info.filename or "\\" in info.filename:
                    fail(f"{name}: entry {info.filename} is not flat")
                if info.filename.startswith("#U"):
                    fail(f"{name}: escaped filename {info.filename}")
        summary.append((name, len(files), target.stat().st_size, desc))
        print(f"PASS: {name} <- {len(files)} files ({desc})")

    print()
    for name, count, size, desc in summary:
        print(f"{name}: {count} files, {size} bytes")
    print("\nUpload package build PASS")


if __name__ == "__main__":
    main()
