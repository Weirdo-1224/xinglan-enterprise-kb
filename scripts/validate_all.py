"""Unified repository validation entry: run all active validators in a stable order.

Usage: python scripts/validate_all.py
Each validator reports PASS / REVIEW / FAIL; any FAIL makes the overall exit code non-zero.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VALIDATORS = [
    ("Manifest", "validate_manifest.py"),
    ("Metadata", "validate_metadata.py"),
    ("Source Lineage", "validate_source_lineage.py"),
    ("Source Coverage", "validate_source_coverage.py"),
    ("Agent Coverage", "validate_agent_coverage.py"),
    ("Semantic Dependency", "validate_semantic_dependencies.py"),
    ("Canonical Consistency", "validate_consistency.py"),
    ("Upload Constraints", "validate_upload_constraints.py"),
    ("Core Knowledge", "validate_core_knowledge.py"),
    ("Stage 3.1 Content QA", "validate_stage31_content.py"),
    ("Stage 4 Project Cases", "validate_stage4_cases.py"),
]


def run_validator(script: str) -> tuple[str, str]:
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
        env=env,
    )
    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        return "FAIL", output
    if any(line.startswith("REVIEW:") for line in output.splitlines()):
        return "REVIEW", output
    return "PASS", output


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    results: list[tuple[str, str]] = []
    for name, script in VALIDATORS:
        status, output = run_validator(script)
        results.append((name, status))
        print(f"===== {name} ({script}) : {status} =====")
        print(output.strip())
        print()

    print("Repository Validation")
    width = max(len(name) for name, _ in results)
    overall = "PASS"
    for name, status in results:
        print(f"- {name.ljust(width)}  {status}")
        if status == "FAIL":
            overall = "FAIL"
        elif status == "REVIEW" and overall == "PASS":
            overall = "REVIEW"
    print()
    print(f"Overall: {overall}")
    if overall == "FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
