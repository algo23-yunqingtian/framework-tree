#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_translation.py — 指标翻译线 Step5 建页引擎 v1

读 translation-workspace/mapping/{品种}/step2_match_*.json（A/B 级、series 实测有数据的）
→ 按品种+板块 分组 → 复用 chart_kits 渲染单指标时序图 → 生成 HTML 子页。

设计目标（用户核心诉求）：
  「几百个指标与网页建立稳定映射关系——改映射表一两个指标，重跑本脚本即可刷新网页」
  所以：本引擎 100% 读表驱动，不写死任何指标。改表 → 重跑 → 页面更新。

用法：
  python3 scripts/build_translation.py --all              # 全部品种
  python3 scripts/build_translation.py --variety ZN       # 单品种
  python3 scripts/build_translation.py --dry --variety ZN # 只打印计划
  python3 scripts/build_translation.py --skip-series-check # 跳过实测结果过滤（默认只画有数据的）

输出： 仓库根目录 zn_*.html / cu_*.html / al_*.html / ni_*.html（板块级子页）
映射： 本引擎读 mapping 的即时结果；Step4 固化进 indicators_v1.json 后可切换数据源
"""
import argparse, json, os, re, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from chart_kits import (load_metric, pairs, latest, chart_line_t,
                        page_html, make_crumb, out, write_html)

CODE_CN = {"ZN": "锌", "CU": "铜", "AL": "铝", "NI": "镍", "SN": "锡", "SI": "硅", "LI": "锂"}
CODE_COLOR = {"ZN": "#5b7a8c", "CU": "#b06a32", "AL": "#7a8a9c", "NI": "#7a8c5b",
              "SN": "#4a7c6f", "SI": "#8a6a7c", "LI": "#5a8a8a"}
SECTION_NAME = {"2": "价格信号", "3": "供给", "4": "库存", "5": "需求", "6": "进出口", "7": "成本利润"}
MIN_POINTS = 8


def load_mapping(variety):
    """读 step2_match_{品种}.json，返回 {board: [ {name,hit_id,hit_name,grade} ]}"""
    path = os.path.join(ROOT, "translation-workspace", "mapping", variety,
                        "step2_match_%s.json" % variety)
    if not os.path.exists(path):
        return {}
    d = json.load(open(path, encoding="utf-8"))
    boards = defaultdict(list)
    for k, vv in d.items():
        if vv.get("grade") not in ("A", "B"):
            continue
        if not vv.get("hit_id"):
            continue
        sub = vv.get("subnode", "") or "?"
        board = re.match(r"^(\d)", sub).group(1) if re.match(r"^(\d)", sub) else "0"
        boards[board].append({
            "name": vv.get("name", ""),
            "hit_id": vv["hit_id"],
            "hit_name": vv.get("hit_name", ""),
            "grade": vv.get("grade"),
        })
    return boards


def load_series_ok(variety):
    """读实测结果（/tmp/series_ok.json: [{...}]），返回有数据的 hit_id 集合。
    若实测未跑完则返回 None（调用方决定是否放行）。"""
    p = "/tmp/series_ok.json"
    if not os.path.exists(p):
        return None
    try:
        data = json.load(open(p))
    except Exception:
        return None
    s = set()
    for r in data:
        if isinstance(r, dict) and r.get("hit_id"):
            s.add(r["hit_id"])
        elif isinstance(r, (list, tuple)) and len(r) >= 2 and isinstance(r[1], dict) and r[1].get("hit_id"):
            s.add(r[1]["hit_id"])
    return s


def build_variety(variety, skip_series=False, dry=False):
    boards = load_mapping(variety)
    if not boards:
        print(f"{variety}: 无映射数据")
        return []
    series_ok = load_series_ok(variety)
    if series_ok is not None and not skip_series:
        print(f"{variety}: 使用 series 实测过滤（有数据 {len(series_ok)} 条）")
    elif skip_series:
        print(f"{variety}: --skip-series-check，不过滤实测")
    else:
        print(f"{variety}: ⚠️ 实测未完成，跳过过滤（可能含无数据图）")

    total_charts = 0
    produced = []
    for board in sorted(boards):
        items = boards[board]
        # 按实测结果过滤：只保留有数据的 hit_id
        kept = []
        for it in items:
            if series_ok is not None and not skip_series and it["hit_id"] not in series_ok:
                continue
            data = load_metric(it["hit_id"], variety)
            if data and data["n"] >= MIN_POINTS:
                it["data"] = data
                kept.append(it)
        if not kept:
            continue
        node_label = board + ".X"
        section = board
        section_name = SECTION_NAME.get(section, f"板块{section}")
        fname = "%s_%s.html" % (variety.lower(), section)
        # 面包屑
        crumb = make_crumb(CODE_CN[variety], variety, section, section_name,
                           node_label, "翻译线Step5", "1", len(kept))
        note_html = (
            '<div class="chart-note" style="margin-bottom:16px;">'
            '<strong>%s · %s</strong><br>映射来源：Step2 知几验证 · A/B 级 · 数据可得</div>'
        ) % (variety, section_name)

        all_html = []
        all_js = []
        cids = []
        for i, it in enumerate(kept):
            cid = "echart_%s_%s_c%d" % (variety.lower(), section, i + 1)
            cids.append(cid)
            m = it["data"]
            title = (it["name"] or it["hit_name"] or "指标")[:50]
            note_text = "📌 %s\n最新(%s)：%s%s" % (
                "知几命中：%s" % it["hit_name"][:50],
                latest(m),
                m["values"][-1] if m["values"] else "-",
                m.get("unit", ""))
            can_season = len(m["points"]) >= 36 and m.get("freq") in ("daily", "日", "")
            h, j = chart_line_t(
                cid, title,
                "%s · %s · 至%s" % (m.get("unit", ""), m.get("freq", ""), latest(m)),
                CODE_COLOR[variety], pairs(m),
                note=note_text, default_seasonal=can_season
            )
            all_html.append(h)
            all_js.append(j)
        footer = ("有色金属产业指标树 · %s(%s) 板块%s · 翻译线Step5 v1 · %d 图"
                  % (CODE_CN[variety], variety, section, len(kept)))
        html = page_html(
            title="%s(%s) %s · 有色金属研究框架" % (CODE_CN[variety], variety, section_name),
            hcrumbs=crumb, hright="翻译线Step5 · 数据可得图",
            h1="\n".join(all_html), h2="", h3="",
            note_html=note_html, footer_text=footer,
            js_body="\n".join(all_js), cids=cids,
            nav_back='<a href="%s_2_overview.html">← 回 %s 总览</a>' % (variety.lower(), CODE_CN[variety]),
        )
        if not dry:
            write_html(os.path.join(ROOT, fname), html)
        produced.append((fname, len(kept)))
        total_charts += len(kept)
        print(f"  {fname}: {len(kept)} 图")
    print(f"{variety}: 共 {len(produced)} 页 / {total_charts} 图")
    return produced


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--variety")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--skip-series-check", action="store_true")
    args = ap.parse_args()
    varieties = ["ZN", "CU", "AL", "NI", "SN", "SI", "LI"] if args.all or not args.variety else [args.variety]
    for v in varieties:
        print(f"\n===== {v} =====", flush=True)
        build_variety(v, skip_series=args.skip_series_check, dry=args.dry)


if __name__ == "__main__":
    main()
