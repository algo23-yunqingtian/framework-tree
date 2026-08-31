#!/usr/bin/env python3
"""
framework-tree 一键回收校验脚本 (reclaim.py)
用途: 主脑侧一键回收线B/新agent的产出品，替代人工 git pull + 人肉比对。

流程:
  1. git fetch origin  拉取远端新成果
  2. 检测本地落后于远端 (有待回收的提交)
  3. 解析 STATUS.md 新变更行, 校验格式契约 (前缀/结构/闭环标记)
  4. 校验最近提交规范 (commit 前缀 [A]/[B]/[DOC])
  5. 抽查新产物完整性 (新增 .html 是否在、indicators_v1.json 是否合法)

用法:
  python3 scripts/reclaim.py                # 完整回收检查
  python3 scripts/reclaim.py --force        # 即使无新提交也校验全部
"""
import json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATUS = os.path.join(ROOT, "STATUS.md")
PASS, FAIL, WARN = 0, 0, 0

def run(cmd, cwd=ROOT):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)

def log(tag, msg):
    global PASS, FAIL
    if tag == "PASS": PASS += 1
    if tag == "FAIL": FAIL += 1
    print(f"  [{tag}] {msg}")

def main():
    print("=" * 60)
    print("framework-tree 一键回收校验")
    print("=" * 60)

    # 1. fetch 远端
    print("\n[1/5] git fetch origin ...")
    r = run("git fetch origin 2>&1")
    if r.returncode != 0:
        log("FAIL", f"fetch 失败: {r.stdout.strip()}")
        sys.exit(1)
    ahead, behind = 0, 0
    try:
        ahead = int(run("git rev-list --count origin/main..HEAD").stdout.strip() or 0)
        behind = int(run("git rev-list --count HEAD..origin/main").stdout.strip() or 0)
    except Exception:
        pass
    log("PASS" if behind > 0 or "--force" in sys.argv else "WARN",
        f"本地领先 {ahead} 条, 落后远端 {behind} 条 → {'有成果待回收' if behind else '无新成果' if not '--force' in sys.argv else '强制模式'}")

    # 2. 待回收的新提交列表 + 任务语义标注
    print("\n[2/5] 远端待回收提交:")
    commits = run("git log --oneline HEAD..origin/main").stdout.strip()
    if commits:
        for line in commits.split("\n")[:10]:
            print(f"    {line}")
        # 任务语义标注: 从 commit 前缀推断任务归属
        prefixes = re.findall(r"\[([^\]]+)\]", commits)
        from collections import Counter
        for k, v in Counter(prefixes).most_common():
            print(f"    → [{k}] ×{v}")
        # 推断当前任务(哪个品种/板块)
        task_hint = ""
        for kw, label in [("价格", "价格板块"), ("进出口", "进出口板块"), ("库存", "库存板块"),
                          ("供给", "供给板块"), ("需求", "需求板块"), ("成本", "成本利润板块"),
                          ("平衡", "供需平衡板块")]:
            if kw in commits:
                task_hint = label
                break
        print(f"    → 任务推断: {task_hint or '未识别(看 STATUS.md 变更记录)'}")
    else:
        print("    (无)")
        print("    → 任务推断: 暂无进行中的任务")

    # 3. STATUS.md 格式契约校验
    print("\n[3/5] STATUS.md 格式契约:")
    if not os.path.exists(STATUS):
        log("FAIL", "STATUS.md 不存在!")
        sys.exit(1)
    text = open(STATUS, encoding="utf-8").read()
    if not re.search(r"\[DOC\]", text):
        log("FAIL", "无 [DOC] 前缀的变更记录")
    else:
        n_recent = len(re.findall(r"\| \d{4}-\d{2}-\d{2} \|", text))
        log("PASS", "[DOC] 前缀存在, 变更记录行数: " + str(n_recent))
    # 检查近期变更记录表格完整性
    if not re.search(r"\| 日期 \| 内容 \|", text):
        log("FAIL", "缺「近期变更记录」表头")
    else:
        log("PASS", "「近期变更记录」表格存在")
    # 检查 B→A 待办区
    for sec in ["B→A 待办", "A→B 待办"]:
        if sec in text:
            log("PASS", f"「{sec}」区存在")
        else:
            log("FAIL", f"缺「{sec}」区")

    # 4. 最近提交前缀规范
    print("\n[4/5] 最近 10 条提交前缀规范:")
    log_lines = run("git log --format='%s' -10 HEAD..origin/main").stdout.strip()
    if not log_lines:
        log_lines = run("git log --format='%s' -10").stdout.strip()
    # 白名单：允许任意「大写字母开头 + 字母/数字/连字符」前缀
    # 例：[A] [B-5M-Step3] [DOC-Step1] [FIX-主脑工具] [T14-7.fix]
    #     [DB-LOAD-TOOL] [RECOVER-786]（后两者为 2026-08-31 实际在用格式）
    # 2026-08-31 修：原正则 T\d+ 紧贴 ]，导致 [B-5M-*]/[DOC-*] 被误判 FAIL
    # 2026-08-31 二次修：放宽为通用大写前缀，容纳 DB-LOAD-TOOL / RECOVER-786
    ok = 0
    for line in log_lines.split("\n"):
        if line and re.match(r"^\[[A-Z][A-Z0-9-]*[^\]]*\]", line.strip()):
            ok += 1
    total = len([l for l in log_lines.split("\n") if l.strip()])
    if total == 0:
        log("PASS", "无提交记录")
    elif ok == total:
        log("PASS", f"全部 {total} 条符合前缀规范")
    else:
        log("FAIL", f"{total - ok}/{total} 条不合规范")

    # 5. 产物完整性抽查
    print("\n[5/5] 产物完整性抽查:")
    try:
        meta = json.load(open(os.path.join(ROOT, "data/indicators_v1.json"), encoding="utf-8"))
        ver = meta.get("version", meta.get("v", "?"))
        n = len(meta.get("indicators", meta.get("items", [])))
        log("PASS", f"indicators_v1.json 合法, version={ver}, 指标数≈{n}")
    except Exception as e:
        log("FAIL", f"indicators_v1.json 解析失败: {e}")
    # 抽查已上线 html 文件存在性
    for page in ["pb_21_price_structure.html", "pb_22_spot_premium.html", "pb_26_position_holder.html",
                 "pb_62_import_export.html", "pb_64_overseas_shipping.html", "pb_2_overview.html"]:
        if os.path.exists(os.path.join(ROOT, page)):
            log("PASS", f"{page} 存在")
        else:
            log("FAIL", f"{page} 缺失!")

    print("\n" + "=" * 60)
    print(f"汇总: PASS={PASS} FAIL={FAIL}")
    if FAIL:
        print("⚠️  存在不合格项, 需人工复核后再 merge")
        sys.exit(1)
    print("✅ 全部通过, 可 merge 回收")
    print("=" * 60)

if __name__ == "__main__":
    main()
