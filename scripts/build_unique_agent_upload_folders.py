"""Build physically de-duplicated RAG upload folders for the twelve agents.

Each RAG asset is copied exactly once to its best-fit owning agent folder.
The accompanying CSV retains every agent listed in RAG_MANIFEST.csv as a
recommended platform label, so cross-agent retrieval can be restored without
uploading the same file more than once.
"""

from __future__ import annotations

import csv
import shutil
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAG_ROOT = ROOT / "deliverables" / "rag"
OUTPUT_ROOT = RAG_ROOT / "按智能体拆分上传"

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

PRIMARY_BY_ID = {
    # Enterprise foundations, policies, procedures, FAQs and roles.
    **{f"KB{i:03d}": "A03" for i in range(1, 13)},
    "KB009": "A02",
    "REF001": "A07", "REF002": "A03", "REF003": "A03", "REF004": "A03",
    "REF005": "A09", "REF006": "A10", "REF007": "A10", "REF008": "A11",
    "REF009": "A05", "REF010": "A12", "REF011": "A03", "REF012": "A02",
    "REF013": "A09", "REF014": "A12", "REF015": "A07", "REF016": "A04",
    "REF017": "A03", "REF018": "A01",
    "POL001": "A07", "POL002": "A07", "POL003": "A08", "POL004": "A08",
    "POL005": "A02", "POL006": "A02", "POL007": "A02", "POL008": "A04",
    "POL009": "A05", "POL010": "A05", "POL011": "A09", "POL012": "A09",
    "POL013": "A10", "POL014": "A11", "POL015": "A12", "POL016": "A12",
    "POL017": "A03", "POL018": "A11",
    "SOP001": "A01", "SOP002": "A01", "SOP003": "A02", "SOP004": "A02",
    "SOP005": "A02", "SOP006": "A02", "SOP007": "A02", "SOP008": "A02",
    "SOP009": "A02", "SOP010": "A02", "SOP011": "A02", "SOP012": "A04",
    "SOP013": "A05", "SOP014": "A07", "SOP015": "A08", "SOP016": "A09",
    "SOP017": "A09", "SOP018": "A11", "SOP019": "A03", "SOP020": "A03",
    "SOP021": "A03", "SOP022": "A06", "SOP023": "A06", "SOP024": "A06",
    "SOP025": "A08", "SOP026": "A08", "SOP027": "A08", "SOP028": "A08",
    "SOP029": "A10", "SOP030": "A10",
    "FAQ001": "A07", "FAQ002": "A07", "FAQ003": "A08", "FAQ004": "A02",
    "FAQ005": "A04", "FAQ006": "A06", "FAQ007": "A09", "FAQ008": "A09",
    "FAQ009": "A10", "FAQ010": "A11", "FAQ011": "A12", "FAQ012": "A03",
    "ROLE001": "A02", "ROLE002": "A01", "ROLE003": "A01", "ROLE004": "A02",
    "ROLE005": "A09", "ROLE006": "A07", "ROLE007": "A12", "ROLE008": "A11",
    "ROLE009": "A04", "ROLE010": "A02",
    # Templates.
    "TPL001": "A02", "TPL002": "A01", "TPL003": "A05", "TPL004": "A02",
    "TPL005": "A02", "TPL006": "A02", "TPL007": "A02", "TPL008": "A02",
    "TPL009": "A04", "TPL010": "A04", "TPL011": "A04", "TPL012": "A05",
    "TPL013": "A05", "TPL014": "A05", "TPL015": "A07", "TPL016": "A07",
    "TPL017": "A08", "TPL018": "A09", "TPL019": "A09", "TPL020": "A11",
    "TPL021": "A06", "TPL022": "A06", "TPL023": "A08", "TPL024": "A08",
    "TPL025": "A08", "TPL026": "A10", "TPL027": "A10", "TPL028": "A10",
    # Structured data.
    "DATA001": "A07", "DATA002": "A01", "DATA003": "A09", "DATA004": "A02",
    "DATA005": "A11", "DATA006": "A09", "DATA007": "A02", "DATA008": "A12",
    "DATA009": "A12", "DATA010": "A12", "DATA011": "A08", "DATA012": "A12",
    # Cross-project historical cases.
    "CASE001": "A02", "CASE002": "A12", "CASE003": "A02", "CASE004": "A06",
}

CASE_OWNER_BY_SEQUENCE = {
    1: "A01", 2: "A01", 3: "A01", 4: "A01", 5: "A12", 6: "A02", 7: "A02",
    8: "A04", 9: "A07", 10: "A07", 11: "A09", 12: "A09", 13: "A09", 14: "A10",
    15: "A11", 16: "A11", 17: "A02", 18: "A02", 19: "A02", 20: "A02", 21: "A02",
    22: "A02", 23: "A12", 24: "A03", 25: "A10", 26: "A10", 27: "A10", 28: "A10",
    29: "A10", 30: "A10", 31: "A10", 32: "A10", 33: "A10",
}


def choose_primary(row: dict[str, str]) -> str:
    knowledge_id = row["knowledge_id"]
    if knowledge_id in PRIMARY_BY_ID:
        return PRIMARY_BY_ID[knowledge_id]
    if knowledge_id.startswith(("P001_", "P002_", "P003_")):
        sequence = int(knowledge_id.rsplit("_", 1)[1])
        # P003 adds specialist deliverables after the shared project lifecycle.
        if knowledge_id == "P003_25":
            return "A09"
        if knowledge_id == "P003_26":
            return "A02"
        if knowledge_id == "P003_27":
            return "A03"
        if knowledge_id == "P003_28":
            return "A03"
        if knowledge_id == "P003_29":
            return "A02"
        if knowledge_id == "P003_30":
            return "A11"
        if knowledge_id == "P003_31":
            return "A02"
        return CASE_OWNER_BY_SEQUENCE[sequence]
    raise ValueError(f"No primary owner rule for {knowledge_id}")


def main() -> None:
    with (RAG_ROOT / "RAG_MANIFEST.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if OUTPUT_ROOT.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {OUTPUT_ROOT}")
    OUTPUT_ROOT.mkdir()
    for agent_id, agent_name in AGENTS.items():
        (OUTPUT_ROOT / f"{agent_id}_{agent_name}").mkdir()

    copied_paths: list[Path] = []
    label_rows: list[dict[str, str]] = []
    for row in rows:
        owner = choose_primary(row)
        served_agents = row["served_agents"].split(";")
        if owner not in served_agents:
            raise ValueError(f"Primary owner {owner} is not eligible for {row['knowledge_id']}")
        source = RAG_ROOT / row["rag_path"]
        if not source.is_file():
            raise FileNotFoundError(f"Missing source file: {source}")
        destination = OUTPUT_ROOT / f"{owner}_{AGENTS[owner]}" / source.name
        if destination.exists():
            raise FileExistsError(f"Duplicate destination name: {destination}")
        shutil.copy2(source, destination)
        copied_paths.append(destination)
        label_rows.append({
            "knowledge_id": row["knowledge_id"],
            "file_name": source.name,
            "primary_upload_agent_id": owner,
            "primary_upload_agent": AGENTS[owner],
            "recommended_agent_labels": ";".join(f"{agent_id}_{AGENTS[agent_id]}" for agent_id in served_agents),
            "knowledge_type": row["knowledge_type"],
            "domain": row["domain"],
            "title": row["title"],
            "source_type": row["source_type"],
            "project_id": row["project_id"],
        })

    if len(copied_paths) != len(rows) or len(set(path.name for path in copied_paths)) != len(rows):
        raise ValueError("Files were not copied exactly once with unique upload names")

    with (OUTPUT_ROOT / "标签关联清单.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(label_rows[0]))
        writer.writeheader()
        writer.writerows(label_rows)

    counts = Counter(row["primary_upload_agent_id"] for row in label_rows)
    with (OUTPUT_ROOT / "上传说明.md").open("w", encoding="utf-8") as handle:
        handle.write("# 智能体知识库上传目录\n\n")
        handle.write("每份知识文件仅存在于一个智能体文件夹，目录间无重复文件。")
        handle.write("上传后请按 `标签关联清单.csv` 的 `recommended_agent_labels` 为文件补充多智能体标签。\n\n")
        handle.write("| 智能体 | 文件数 |\n| --- | ---: |\n")
        for agent_id, agent_name in AGENTS.items():
            handle.write(f"| {agent_id}_{agent_name} | {counts[agent_id]} |\n")
        handle.write(f"\n合计：{len(rows)} 份知识文件。\n")

    print(f"PASS: copied {len(rows)} unique files into {len(AGENTS)} agent folders")
    for agent_id, agent_name in AGENTS.items():
        print(f"{agent_id}_{agent_name}: {counts[agent_id]}")


if __name__ == "__main__":
    main()
