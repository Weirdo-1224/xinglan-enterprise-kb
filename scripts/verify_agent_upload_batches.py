"""Verify the <=9-file agent upload ZIP batches."""

from __future__ import annotations

import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "deliverables" / "agent_kb_packages"
KNOWLEDGE_DIR = "知识库"
UPLOAD_DIR = "上传包_每包最多9文件"
MAX_FILES_PER_ARCHIVE = 9


def main() -> None:
    failures: list[str] = []
    total_archives = 0
    total_files = 0

    for agent_root in sorted(path for path in PACKAGE_ROOT.iterdir() if path.is_dir()):
        knowledge_root = agent_root / KNOWLEDGE_DIR
        upload_root = agent_root / UPLOAD_DIR
        knowledge_files = {
            path.name
            for path in knowledge_root.rglob("*")
            if path.is_file()
        }
        if len(knowledge_files) != sum(1 for path in knowledge_root.rglob("*") if path.is_file()):
            failures.append(f"{agent_root}: duplicate source filenames prevent flat ZIP verification")
        archived_files: list[str] = []
        archives = sorted(upload_root.glob("*.zip"))

        for archive_path in archives:
            with zipfile.ZipFile(archive_path) as archive:
                entries = [entry.filename for entry in archive.infolist() if not entry.is_dir()]
            if not 1 <= len(entries) <= MAX_FILES_PER_ARCHIVE:
                failures.append(f"{archive_path}: expected 1-9 files, found {len(entries)}")
            if any("/" in entry or "\\" in entry for entry in entries):
                failures.append(f"{archive_path}: contains a directory path")
            archived_files.extend(entries)

        if len(archived_files) != len(set(archived_files)):
            failures.append(f"{agent_root}: duplicate files across archives")
        if set(archived_files) != knowledge_files:
            failures.append(f"{agent_root}: archived files differ from knowledge files")

        total_archives += len(archives)
        total_files += len(archived_files)
        print(f"{agent_root.name.split('_', 1)[0]}: {len(archives)} ZIPs / {len(archived_files)} files")

    if failures:
        raise SystemExit("VERIFY FAILED:\n" + "\n".join(failures))
    print(f"VERIFY PASS: {total_archives} ZIPs / {total_files} files; all ZIPs contain 1-9 files.")


if __name__ == "__main__":
    main()
