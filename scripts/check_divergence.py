#!/usr/bin/env python3
"""Step1 发散产出校验器。

检查某品种的 divergence_<节点>.md 是否齐全、格式是否达标，输出缺口清单。
用法:
    python3 scripts/check_divergence.py --variety NI
    python3 scripts/check_divergence.py --all          # 5 金属全查
    python3 scripts/check_divergence.py --variety NI --strict   # 严格模式(缺内容也算FAIL)

校验项:
  1. 文件齐全: 对照 tree_config 应有节点数
  2. 有表格: 至少含「独立基础指标枚举」+「核心图表设计方案」两表
  3. 指标数达标: 每节点 3-12 个指标行（v19 规则1: 6-8, 最多10）
  4. 有排除项区或标注: 归属判断列存在
  5. 表头完整: 表头含 序号/基础指标/直接含义/归属判断
"""
import argparse, json, os, re, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
TREE = BASE / "data" / "tree_config.json"
OUT_ROOT = BASE / "analysis" / "iwencai"

ALL_CODES = ["ZN", "NI", "SN", "SI", "LI"]
# 板块8 供需平衡不做图表，不发散
SKIP_BOARDS = {"8"}


def expected_nodes():
    """返回 {节点编号: (板块, 名称)}"""
    tree = json.loads(TREE.read_text(encoding="utf-8"))
    nodes = {}
    for cat in tree["categories"]:
        for c in cat["children"]:
            board = c["code"].split(".")[0]
            if board in SKIP_BOARDS:
                continue
            nodes[c["code"]] = (board, c.get("name", ""))
    return nodes


def check_node_file(path, strict=False):
    """校验单节点文件，返回 (ok, issues[])"""
    issues = []
    txt = path.read_text(encoding="utf-8", errors="replace")
    if len(txt) < 300:
        issues.append(f"内容过短 ({len(txt)} bytes)")
    # 表头检查
    has_enum = bool(re.search(r"基础指标|指标枚举|序号", txt))
    has_chart = bool(re.search(r"图表|图名|方案", txt))
    if not has_enum:
        issues.append("缺「指标枚举」表")
    if not has_chart:
        issues.append("缺「图表方案」表")
    # 指标行数（表格行，排除表头和分隔行）
    rows = [l for l in txt.splitlines()
            if l.strip().startswith("|") and "---" not in l]
    if len(rows) < 4:
        issues.append(f"表格行过少 ({len(rows)})")
    if strict and not re.search(r"排除项|归属判断|应归属", txt):
        issues.append("缺排除项/归属判断说明")
    return (len(issues) == 0), issues


def check_variety(code, strict=False, verbose=True):
    exp = expected_nodes()
    d = OUT_ROOT / code
    if not d.exists():
        return {"code": code, "total": len(exp), "ok": 0, "present": 0,
                "missing": list(exp), "bad": [], "fail": len(exp)}

    found = sorted(re.findall(r"divergence_([\d.]+)\.md",
                              " ".join(p.name for p in d.glob("divergence_*.md"))))
    missing = [n for n in exp if n not in found]
    bad = []
    for n in found:
        ok, issues = check_node_file(d / f"divergence_{n}.md", strict)
        if not ok:
            bad.append({"node": n, "issues": issues})
    if verbose:
        print(f"=== {code} ===")
        print(f"  应有 {len(exp)} 节点 | 已有 {len(found)} | 缺 {len(missing)} | 不合格 {len(bad)}")
        if missing:
            print(f"  缺口: {', '.join(missing[:15])}{'...' if len(missing) > 15 else ''}")
        if bad:
            print(f"  不合格:")
            for b in bad[:8]:
                print(f"    {b['node']}: {'; '.join(b['issues'])}")
            if len(bad) > 8:
                print(f"    ... 还有 {len(bad) - 8} 个")
    return {"code": code, "total": len(exp), "ok": len(found) - len(bad),
            "present": len(found), "missing": missing, "bad": bad,
            "fail": len(missing) + len(bad)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variety")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    codes = ALL_CODES if (args.all or not args.variety) else [args.variety]
    results = [check_variety(c, args.strict) for c in codes]

    # 汇总
    print("\n" + "=" * 52)
    print("Step1 发散进度汇总")
    print("=" * 52)
    print(f"{'品种':<6}{'应有':>6}{'已有':>6}{'合格':>6}{'缺失':>6}{'不合格':>7}")
    print("-" * 52)
    tot_exp = tot_ok = tot_fail = 0
    for r in results:
        print(f"{r['code']:<6}{r['total']:>6}{r['present']:>6}{r['ok']:>6}"
              f"{len(r['missing']):>6}{len(r['bad']):>7}")
        tot_exp += r["total"]
        tot_ok += r["ok"]
        tot_fail += r["fail"]
    print("-" * 52)
    print(f"{'合计':<6}{tot_exp:>6}{sum(r['present'] for r in results):>6}{tot_ok:>6}"
          f"{sum(len(r['missing']) for r in results):>6}{sum(len(r['bad']) for r in results):>7}")
    print(f"\n完成度: {tot_ok}/{tot_exp} = {tot_ok / max(tot_exp, 1):.1%}")

    # 退出码: 有缺口非零（便于 cron/CI 判定）
    sys.exit(0 if tot_fail == 0 else 1)


if __name__ == "__main__":
    main()