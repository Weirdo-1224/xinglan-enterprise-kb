"""Build upload-ready, agent-specific knowledge-base ZIP packages.

The source RAG manifest is authoritative: an asset is included in an agent's
package exactly when its ``served_agents`` field contains that agent ID.
"""

from __future__ import annotations

import csv
import shutil
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAG_ROOT = ROOT / "deliverables" / "rag"
OUTPUT_ROOT = ROOT / "deliverables" / "agent_kb_packages"

AGENTS = {
    "A01": "需求洞察与方案顾问",
    "A02": "AI项目经理",
    "A03": "企业知识管家",
    "A04": "智能会议协同官",
    "A05": "企业文档创作官",
    "A06": "文档规范与排版官",
    "A07": "AI招聘与人才助手",
    "A08": "培训绩效与员工发展助手",
    "A09": "智能采购顾问",
    "A10": "招投标审查官",
    "A11": "合同与履约风控官",
    "A12": "企业经营分析师",
}


def main() -> None:
    manifest_path = RAG_ROOT / "RAG_MANIFEST.csv"
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True)

    summary: list[tuple[str, str, int, int]] = []
    for agent_id, name in AGENTS.items():
        package_name = f"{agent_id}_{name}"
        package_root = OUTPUT_ROOT / package_name
        knowledge_root = package_root / "知识库"
        selected = [
            row
            for row in rows
            if agent_id in {item.strip() for item in row["served_agents"].split(";")}
        ]

        type_counts: Counter[str] = Counter()
        for row in selected:
            relative_path = Path(row["rag_path"])
            source = RAG_ROOT / relative_path
            if not source.is_file():
                raise FileNotFoundError(f"Missing asset in manifest: {source}")
            target = knowledge_root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            type_counts[row["knowledge_type"]] += 1

        with (package_root / "00_知识包说明.md").open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(f"# {name}知识包\n\n")
            handle.write(f"- 智能体编号：{agent_id}\n")
            handle.write(f"- 知识文件数：{len(selected)}\n")
            handle.write("- 分包规则：仅包含 RAG_MANIFEST.csv 中 `served_agents` 标记为本智能体的资产。\n")
            handle.write("- 上传范围：上传本压缩包中的 `知识库` 目录内全部文件；请勿与其他智能体包混传。\n\n")
            handle.write("## 文件类型统计\n\n")
            for knowledge_type, count in sorted(type_counts.items()):
                handle.write(f"- {knowledge_type}: {count}\n")

        # Keep a filtered provenance manifest outside the upload directory for audit.
        with (package_root / "资产清单_仅供核对.csv").open(
            "w", encoding="utf-8-sig", newline=""
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(selected)

        # ZIPs are intended for direct RAG upload, so include knowledge assets only.
        # The package folder retains the explanatory and audit files separately.
        archive = shutil.make_archive(str(OUTPUT_ROOT / package_name), "zip", knowledge_root)
        summary.append((agent_id, name, len(selected), Path(archive).stat().st_size))

    with (OUTPUT_ROOT / "上传包总览.md").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("# 智能体知识库上传包总览\n\n")
        handle.write("每个 ZIP 对应一个智能体。知识在职责交叉处会按授权复制到多个包，这是正常且必要的。\n\n")
        handle.write("| 编号 | 智能体 | 知识文件数 | ZIP 大小（字节） |\n")
        handle.write("| --- | --- | ---: | ---: |\n")
        for agent_id, name, count, size in summary:
            handle.write(f"| {agent_id} | {name} | {count} | {size} |\n")

    print(f"Created {len(summary)} ZIP packages in {OUTPUT_ROOT}")
    for agent_id, name, count, size in summary:
        print(f"{agent_id}\t{name}\t{count} files\t{size} bytes")


if __name__ == "__main__":
    main()
