#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick Step2 draft gate for 5 metals decision_<node>.md.

Usage:
    python scripts/check_step2_drafts.py

Checks ZN/NI/SI/SN/LI each have 30 decision_<node>.md files, each containing
candidate indicators, exclusions, at least 4 recommended charts, and the Step3
handoff note.
"""
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "analysis" / "iwencai"
CODES = ["ZN", "NI", "SI", "SN", "LI"]
EXPECTED = [
    "2.1", "2.2", "2.3", "2.4", "2.5", "2.6",
    "3.1.1", "3.1.2", "3.1.3", "3.1.4", "3.1.5",
    "3.2.1", "3.2.2", "3.2.3", "3.2.4",
    "4.1", "4.2", "4.3", "4.4", "4.5",
    "5.1", "5.2", "5.3",
    "6.1", "6.2", "6.3", "6.4",
    "7.1", "7.2", "7.3",
]

problems = []
for code in CODES:
    d = BASE / code
    files = sorted(d.glob("decision_*.md"))
    by_node = {
        re.search(r"decision_(.+)\.md$", f.name).group(1): f
        for f in files
        if f.name.startswith("decision_")
    }
    missing = [n for n in EXPECTED if n not in by_node]
    extra = [n for n in by_node if n not in EXPECTED]
    if missing:
        problems.append(f"{code} missing {missing}")
    if extra:
        problems.append(f"{code} extra {extra}")
    for n, f in by_node.items():
        txt = f.read_text(encoding="utf-8")
        if len(txt) < 1500:
            problems.append(f"{code}/{n} too short {len(txt)}")
        if "## 候选指标" not in txt or "## 排除项" not in txt or "## 推荐图组合" not in txt:
            problems.append(f"{code}/{n} missing sections")
        if txt.count("### ") < 4:
            problems.append(f"{code}/{n} charts < 4")
        if "Step3 知几验证" not in txt:
            problems.append(f"{code}/{n} missing Step3 note")

print(f"codes={len(CODES)} expected_nodes={len(EXPECTED)} files={sum(1 for c in CODES for _ in (BASE / c).glob('decision_*.md'))}")
if problems:
    print("FAIL")
    print("\n".join(problems[:80]))
    raise SystemExit(1)
print("PASS")
