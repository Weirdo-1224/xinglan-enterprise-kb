"""Build agent-specific upload ZIP batches with at most nine files each.

Knowledge assets are read from each agent's existing ``知识库`` directory. The
source files and any legacy ZIP archives are retained unchanged. New ZIP files
are written under ``上传包_每包最多9文件`` inside the corresponding agent folder.
"""

from __future__ import annotations

import shutil
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "deliverables" / "agent_kb_packages"
KNOWLEDGE_DIR = "知识库"
UPLOAD_DIR = "上传包_每包最多9文件"
MAX_FILES_PER_ARCHIVE = 9


def collect_files(knowledge_root: Path) -> list[Path]:
    """Return a stable, recursive list of uploadable knowledge files."""
    return sorted(
        (path for path in knowledge_root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(knowledge_root).as_posix(),
    )


def chunked(items: list[Path], size: int) -> list[list[Path]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def build_agent_batches(agent_root: Path) -> list[tuple[str, int]]:
    knowledge_root = agent_root / KNOWLEDGE_DIR
    if not knowledge_root.is_dir():
        raise FileNotFoundError(f"Missing knowledge directory: {knowledge_root}")

    files = collect_files(knowledge_root)
    if not files:
        raise ValueError(f"No knowledge files found: {knowledge_root}")
    duplicate_names = [name for name, count in Counter(path.name for path in files).items() if count > 1]
    if duplicate_names:
        raise ValueError(
            f"Cannot create a flat ZIP with duplicate filenames for {agent_root}: "
            + ", ".join(sorted(duplicate_names))
        )

    upload_root = agent_root / UPLOAD_DIR
    if upload_root.exists():
        shutil.rmtree(upload_root)
    upload_root.mkdir()

    result: list[tuple[str, int]] = []
    for batch_number, batch in enumerate(chunked(files, MAX_FILES_PER_ARCHIVE), start=1):
        archive_name = f"{agent_root.name}_知识库_{batch_number:02d}.zip"
        archive_path = upload_root / archive_name
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for source in batch:
                # The upload platform accepts files only: ZIP entries must be flat.
                archive.write(source, source.name)

        with zipfile.ZipFile(archive_path) as archive:
            archived_files = [entry for entry in archive.infolist() if not entry.is_dir()]
            if len(archived_files) != len(batch) or len(archived_files) > MAX_FILES_PER_ARCHIVE:
                raise ValueError(f"Invalid archive contents: {archive_path}")
            if any("/" in entry.filename or "\\" in entry.filename for entry in archived_files):
                raise ValueError(f"Archive contains a directory entry: {archive_path}")
        result.append((archive_name, len(batch)))

    return result


def main() -> None:
    agent_roots = sorted(path for path in PACKAGE_ROOT.iterdir() if path.is_dir())
    if not agent_roots:
        raise FileNotFoundError(f"No agent directories found: {PACKAGE_ROOT}")

    total_archives = 0
    total_files = 0
    for agent_root in agent_roots:
        batches = build_agent_batches(agent_root)
        file_count = sum(count for _, count in batches)
        total_archives += len(batches)
        total_files += file_count
        print(f"{agent_root.name}: {len(batches)} ZIPs, {file_count} files")
        for archive_name, count in batches:
            print(f"  {archive_name}: {count} files")

    print(f"PASS: {total_archives} ZIPs, {total_files} files; max {MAX_FILES_PER_ARCHIVE} files per ZIP")


if __name__ == "__main__":
    main()
