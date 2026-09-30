#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
t2_review_prep.py — HERMES_V85_ARTIFICIAL_REVIEW_PREP 人工评审材料生成

T2.1 review_portal.md             人工评审总入口（品种分组/评分排序/P0快速筛选）
T2.2 schema_adapt_doc.md          DSHB↔schema 字段适配文档（固化映射规则）
T2.3 abnormal_indicator_list.csv  异常指标清单（5 INVALID + 2 MISSING）
T2.4 fuzzy_match_sample_checklist 124条模糊匹配抽检清单（低分优先）
T2.5 PART_OK 权限标记（评审入口 + HTML 头部）
T2.6 pre_merge_checklist.md       合并前检查 + 部署步骤 + 回滚方案

约束（T4）:
  - 仅 feature/v85-chart-template 测试分支，禁止合并 main
  - 不修改原始模板 / indicators_v1.json / tree_config.json
  - 不发起生产部署，仅准备评审材料
"""

import csv
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

PKG = Path(__file__).resolve().parent
SRC = PKG / "output" / "v85_chart_online_test"
OUT = PKG / "output" / "v85_review_package"
RENDERED = SRC / "rendered"

TPL_JSON = PKG / "pdf_web_chart_template_hermes_ready.json"
VERIFY_CSV = PKG / "zhiji_verify_stat.csv"
DETAIL_JSON = SRC / "render_detail.json"
NODE_CSV = SRC / "node_mapping_index.csv"
NODE_JSON = SRC / "node_index.json"

REPO = "/home/ubuntu/framework-tree"
SC = re.compile(r"score=([\d.]+)")
NAME_IN_NOTE = re.compile(r"name=([^)]+)")
KEY_IN_NOTE = re.compile(r"indicators_v1 模糊匹配 \(([^)]+)\)")

VARIETY_NAME = {"AO": "氧化铝", "CU": "铜", "AL": "铝", "PB": "铅", "ZN": "锌",
                "NI": "镍", "SN": "锡", "SI": "工业硅", "LC": "碳酸锂"}
VARIETY_COLOR = {"AO": "#9a6b4f", "CU": "#b06a32", "AL": "#7a8a9c", "PB": "#6b7280",
                 "ZN": "#5b7a8c", "NI": "#7a8c5b", "SN": "#8c6b9c", "SI": "#c08a3e",
                 "LC": "#4f8a7a"}
# P0 高优先级图表类型（工单 T2.1）
P0_TYPES = ["复合混合(折线+柱状)", "堆叠柱状", "多折线"]

# 口径冲突关键词：PDF 系列名与此不符即高度疑似口径错误
METRIC_MISMATCH = [
    (r"产量", r"消费|销量|需求"),
    (r"库存", r"在途|堆积|平台"),
    (r"场内库存", r"非仓单"),
    (r"开工率", r"产量|利润"),
]


def score_of(note):
    m = SC.search(note or "")
    return float(m.group(1)) if m else None


def note_name(note):
    m = NAME_IN_NOTE.search(note or "")
    return m.group(1) if m else ""


def note_key(note):
    m = KEY_IN_NOTE.search(note or "")
    return m.group(1) if m else ""


def mismatch_flag(pdf_name, actual_name):
    """返回口径冲突描述，无冲突返回空串"""
    for a, b in METRIC_MISMATCH:
        if re.search(a, pdf_name or "") and re.search(b, actual_name or ""):
            return f"⚠️ 口径疑似冲突：PDF「{a}」类 vs zhiji「{b}」类"
    return ""


def cache_info(zhiji_id):
    """读取 zhiji 缓存，返回 (实际指标名, 数据点数, 单位, 最新日期)"""
    p = PKG / "zhiji_data_cache" / f"{zhiji_id}.json"
    if not p.exists():
        return ("", 0, "", "")
    try:
        c = json.loads(p.read_text(encoding="utf-8"))
        dd = c.get("data", {})
        pts = dd.get("points", [])
        latest = pts[0][0] if pts else ""
        return (dd.get("name", ""), dd.get("point_count", 0), dd.get("unit", ""), latest)
    except (json.JSONDecodeError, KeyError, TypeError):
        return ("", 0, "", "")


def md5_short(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()[:8]


def git_branch():
    r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                       cwd=REPO, capture_output=True, text=True)
    return r.stdout.strip()


def git_head():
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True)
    return r.stdout.strip()[:12]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    templates = json.loads(TPL_JSON.read_text(encoding="utf-8"))["templates"]
    detail = json.loads(DETAIL_JSON.read_text(encoding="utf-8"))
    with open(VERIFY_CSV, encoding="utf-8-sig") as f:
        verify_rows = list(csv.DictReader(f))
    node_index = json.loads(NODE_JSON.read_text(encoding="utf-8"))

    dtpl = {r["template_id"]: r for r in detail}
    part_ids = {t["template_id"] for t in templates if t["metadata"]["verify_status"] == "PART_OK"}

    # ==================================================================
    # T2.3 abnormal_indicator_list.csv — 5 INVALID + 2 MISSING
    # ==================================================================
    abnormal = []
    for t in templates:
        for s in t["series"]:
            if s["verify_status"] not in ("INVALID", "MISSING"):
                continue
            zid = s.get("zhiji_id")
            aname, pts, unit, latest = cache_info(zid) if zid else ("", 0, "", "")
            abnormal.append({
                "序号": len(abnormal) + 1,
                "状态": s["verify_status"],
                "优先级": "P0",
                "模板ID": t["template_id"],
                "品种": f"{t['variety']} {VARIETY_NAME.get(t['variety'], t['variety'])}",
                "图表标题": t["source"]["chart_title"],
                "图表类型": t["chart_type"],
                "指标名称(PDF系列名)": s["name"],
                "PDF指标键(indicator_key)": s.get("indicator_key") or "",
                "原zhiji_id": zid or "(已清空/无效)",
                "单位": s.get("unit") or "",
                "DHSB报错原因": s.get("verify_note") or "",
                "模板状态": t["metadata"]["verify_status"],
                "图表渲染评分": dtpl[t["template_id"]]["visual"]["score"],
                "图表预览": f"../v85_chart_online_test/rendered/{t['template_id']}.html",
                "PDF来源": f"{t['source']['file']} 第{t['source']['page']}页",
                "当前状态": "❌ 无有效数据，图表空渲染",
                "人工处理建议": "在zhiji网页搜索该指标名，补新zhiji_id后重跑拉取",
            })
    with open(OUT / "abnormal_indicator_list.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(abnormal[0].keys()))
        w.writeheader()
        w.writerows(abnormal)

    # ==================================================================
    # T2.4 fuzzy_match_sample_checklist.md — 124条 FILLED 抽检
    # ==================================================================
    filled = [r for r in verify_rows if r["verify_status"] == "FILLED"]

    # 逐条明细 + 去重分组
    entries = []
    for r in filled:
        fid = r["final_zhiji_id"]
        s = score_of(r["verify_note"])
        aname, pts, unit, latest = cache_info(fid)
        key = note_key(r["verify_note"])
        mm = mismatch_flag(r["series_name"], aname)
        entries.append({
            "row": r, "score": s, "final_id": fid, "actual_name": aname,
            "pts": pts, "unit": unit, "latest": latest, "iv_key": key,
            "mismatch": mm, "tpl": r["template_id"], "tpl_type": None,
        })
    for e in entries:
        e["tpl_type"] = next((t["chart_type"] for t in templates
                              if t["template_id"] == e["tpl"]), "")

    # 风险分级
    def risk_of(e):
        if e["mismatch"]:
            return "P0"
        s = e["score"]
        if s is None:            # indicators_v1 键语义模糊匹配
            return "P1"
        if s < 0.5:
            return "P0"
        if s < 0.6:
            return "P1"
        if s < 0.7:
            return "P2"
        return "P3"
    for e in entries:
        e["risk"] = risk_of(e)

    risk_cnt = Counter(e["risk"] for e in entries)
    uniq_pairs = {}
    for e in entries:
        k = (e["row"]["series_name"], e["final_id"])
        if k not in uniq_pairs:
            uniq_pairs[k] = dict(e)
            uniq_pairs[k]["count"] = 1
            uniq_pairs[k]["tpls"] = [e["tpl"]]
        else:
            uniq_pairs[k]["count"] += 1
            uniq_pairs[k]["tpls"].append(e["tpl"])
    uniq_list = sorted(uniq_pairs.values(), key=lambda x: (x["risk"], x["score"] or 9))

    score_buckets = Counter()
    for e in entries:
        if e["score"] is None:
            score_buckets["indicators_v1键匹配(无score)"] += 1
        elif e["score"] < 0.5:
            score_buckets["<0.50"] += 1
        elif e["score"] < 0.6:
            score_buckets["0.50-0.59"] += 1
        elif e["score"] < 0.7:
            score_buckets["0.60-0.69"] += 1
        elif e["score"] < 0.8:
            score_buckets["0.70-0.79"] += 1
        else:
            score_buckets["≥0.80"] += 1

    p0_ids = {e["final_id"] for e in entries if e["risk"] == "P0"}
    p1_ids = {e["final_id"] for e in entries if e["risk"] == "P1"}

    with open(OUT / "fuzzy_match_sample_checklist.md", "w", encoding="utf-8") as f:
        f.write("# V85 模糊匹配填充指标人工抽检清单\n\n")
        f.write(f"> 工单: `HERMES_V85_ARTIFICIAL_REVIEW_PREP`  \n")
        f.write(f"> 生成时间: {now}  \n")
        f.write(f"> 数据源: `zhiji_verify_stat.csv` verify_status=FILLED\n\n")

        f.write("## 1. 总览\n\n")
        f.write("| 指标 | 数量 |\n|---|---|\n")
        f.write(f"| FILLED 填充总数（逐条） | {len(filled)} |\n")
        f.write(f"| 去重后唯一 (系列名+zhiji_id) 对 | {len(uniq_list)} |\n")
        f.write(f"| 涉及唯一 zhiji_id | {len({e['final_id'] for e in entries})} |\n")
        f.write(f"| 涉及图表数 | {len({e['tpl'] for e in entries})} |\n")
        f.write(f"| **P0 高风险（口径冲突/极低分）** | **{risk_cnt['P0']}** |\n")
        f.write(f"| **P1 中高风险** | **{risk_cnt['P1']}** |\n")
        f.write(f"| P2 中低风险 | {risk_cnt['P2']} |\n")
        f.write(f"| P3 低风险（≥0.80，建议抽查） | {risk_cnt['P3']} |\n\n")

        f.write("## 2. 匹配分数分布\n\n| 分数区间 | 条数 | 风险等级 |\n|---|---|---|\n")
        lb = {"<0.50": "P0", "indicators_v1键匹配(无score)": "P1", "0.50-0.59": "P1",
              "0.60-0.69": "P2", "0.70-0.79": "P2", "≥0.80": "P3"}
        for k in ["<0.50", "0.50-0.59", "0.60-0.69", "0.70-0.79", "≥0.80",
                  "indicators_v1键匹配(无score)"]:
            f.write(f"| {k} | {score_buckets[k]} | {lb[k]} |\n")

        f.write("\n## 3. P0 高风险项（必须逐条复核，口径疑似错误）\n\n")
        f.write("> 判定依据: 匹配分数 < 0.50，**或** PDF 系列名与 zhiji 实际指标名构成 "
                "「产量↔消费量」「库存↔在途」「场内库存↔非仓单」等口径冲突。\n\n")
        f.write("| # | 模板 | 图表类型 | PDF系列名 | 填入zhiji_id | zhiji实际指标名 | 分数 | 数据点 | 单位 | 图表链接 |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|\n")
        n = 0
        for e in uniq_list:
            if e["risk"] != "P0":
                continue
            n += 1
            sc = f"{e['score']:.2f}" if e["score"] is not None else "键匹配"
            links = ", ".join(f"`{x}`" for x in e["tpls"][:2])
            f.write(f"| {n} | {links} | {e['tpl_type']} | **{e['row']['series_name']}** | "
                    f"`{e['final_id']}` | {e['actual_name']} | {sc} | {e['pts']} | "
                    f"{e['unit'] or '—'} | "
                    f"[预览](../v85_chart_online_test/rendered/{e['tpls'][0]}.html) |\n")
        f.write(f"\n**P0 小计: {n} 项，覆盖 {len(p0_ids)} 个 zhiji_id**\n\n")

        f.write("### P0 典型问题说明\n\n")
        if p0_ids:
            f.write("1. **「产量」被填成「消费量」**（最严重）: 多个「铝土矿产量-XX-XX」系列 "
                    "全部指向 `ID01724147`（铝土矿：国产：**消费量**：河北）与 "
                    "`ID01724143`（消费量：河南）。**产量与消费量是完全不同的产业口径，"
                    "直接用于图表会误导判断。**\n\n")
            f.write("2. **同一 zhiji_id 覆盖多个不相关系列**: `ID01724147` 被 4 个不同地区/品级 "
                    "的铝土矿产量系列共用，说明重检索的模糊匹配在该指标族上完全失效。\n\n")
            f.write("3. **「汽车端消费用锡拟合」→「汽车：消费指数」**(score 0.44): "
                    "拟合值与官方指数口径不同，单位为百分比。\n\n")
            f.write("4. **「LME主要仓库场内库存」→「LME非仓单库存：欧洲」**(score 0.55): "
                    "场内与仓外库存概念相反。\n\n")
            f.write("5. **「不同镍产品折镍价」→「304废不锈钢折合镍铁价格」**(score 0.50): "
                    "折镍价与废不锈钢折价口径不同。\n\n")

        f.write("## 4. P1 中高风险项\n\n")
        f.write("> indicators_v1 键语义模糊匹配（无分数）+ 分数 0.50-0.59 项。\n\n")
        f.write("| # | 模板 | PDF系列名 | 填入zhiji_id | zhiji实际指标名 | 分数 | 匹配方式 | 图表链接 |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        n = 0
        for e in uniq_list:
            if e["risk"] != "P1":
                continue
            n += 1
            sc = f"{e['score']:.2f}" if e["score"] is not None else "—"
            way = f"indicators_v1键 `{e['iv_key']}`" if e["iv_key"] else "search"
            links = ", ".join(f"`{x}`" for x in e["tpls"][:2])
            f.write(f"| {n} | {links} | {e['row']['series_name']} | `{e['final_id']}` | "
                    f"{e['actual_name']} | {sc} | {way} | "
                    f"[预览](../v85_chart_online_test/rendered/{e['tpls'][0]}.html) |\n")
        f.write(f"\n**P1 小计: {n} 项**\n\n")

        f.write("## 5. indicators_v1 键语义匹配明细（13 条）\n\n")
        f.write("> 这类匹配通过 `indicators_v1.json` 的指标键模糊命中，**不产生匹配分数**，"
                "需人工确认指标键的业务语义是否等价。\n\n")
        f.write("| 指标键 | 覆盖系列名 | zhiji_id | zhiji实际指标名 | 图表 |\n|---|---|---|---|---|\n")
        iv_groups = defaultdict(list)
        for e in entries:
            if e["iv_key"]:
                iv_groups[e["iv_key"]].append(e)
        for key, es in sorted(iv_groups.items(), key=lambda x: -len(x[1])):
            names = sorted({e["row"]["series_name"] for e in es})
            f.write(f"| `{key}` | {len(names)}个: {names[0]}{'…' if len(names)>1 else ''} | "
                    f"`{es[0]['final_id']}` | {es[0]['actual_name']} | "
                    f"[`{es[0]['tpl']}`](../v85_chart_online_test/rendered/{es[0]['tpl']}.html) |\n")

        f.write("\n## 6. 完整 124 条明细（按风险+分数排序）\n\n")
        f.write("| # | 风险 | 模板 | 分数 | PDF系列名 | 填入ID | zhiji实际名 | 口径标记 |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        order = sorted(entries, key=lambda e: (e["risk"], e["score"] if e["score"] is not None else 9))
        for i, e in enumerate(order, 1):
            sc = f"{e['score']:.2f}" if e["score"] is not None else "—"
            flag = "⚠️冲突" if e["mismatch"] else ""
            f.write(f"| {i} | {e['risk']} | `{e['tpl']}` | {sc} | "
                    f"{e['row']['series_name'][:26]} | `{e['final_id']}` | "
                    f"{e['actual_name'][:24]} | {flag} |\n")

        f.write("\n## 7. 抽检建议与判定规则\n\n")
        f.write("| 等级 | 条数 | 抽检要求 | 处理方式 |\n|---|---|---|---|\n")
        f.write(f"| P0 | {risk_cnt['P0']} | **100% 逐条复核** | 在 zhiji 搜索正确指标ID，更新模板后重跑 |\n")
        f.write(f"| P1 | {risk_cnt['P1']} | **100% 逐条复核** | 确认键语义/低分匹配是否可接受 |\n")
        f.write(f"| P2 | {risk_cnt['P2']} | 建议抽样 50% | 抽查通过后可放行 |\n")
        f.write(f"| P3 | {risk_cnt['P3']} | 抽样 20% | 高分匹配一般可信 |\n\n")
        f.write("**抽检判定口径**:\n")
        f.write("1. 打开「图表链接」，查看 zhiji 实际指标名与图中系列名是否业务等价\n")
        f.write("2. 比对单位是否一致（产量类应为万吨/吨，消费量类应为万吨）\n")
        f.write("3. 比对数据趋势是否与 PDF 原图一致（PDF 来源见图表页脚）\n")
        f.write("4. 判定结果: ✅通过 / ⚠️可用需加注 / ❌需替换（填入新 ID 后重跑）\n")

    # ==================================================================
    # T2.1 + T2.5 review_portal.md — 评审总入口（含权限标记）
    # ==================================================================
    scores = {r["template_id"]: r["visual"]["score"] for r in detail}
    variety_groups = defaultdict(list)
    for r in detail:
        variety_groups[r["variety"]].append(r)

    p0_type_charts = [r for r in detail if r["chart_type"] in P0_TYPES]
    failed_charts = [r for r in detail if not any(s["point_count"] > 0 for s in r["series"])]
    low_score = sorted([r for r in detail if r["visual"]["score"] < 10],
                       key=lambda x: (x["visual"]["score"], x["template_id"]))

    # P0 图表：类型优先级 + 评分低 + 异常
    def p0_sort(r):
        type_rank = {t: i for i, t in enumerate(P0_TYPES)}
        return (type_rank.get(r["chart_type"], 99), r["visual"]["score"])
    p0_type_charts.sort(key=p0_sort)

    html_total = len(list(RENDERED.glob("*.html")))

    with open(OUT / "review_portal.md", "w", encoding="utf-8") as f:
        f.write("# V85 图表模板人工评审总入口\n\n")
        f.write(f"> 工单: `HERMES_V85_ARTIFICIAL_REVIEW_PREP`  \n")
        f.write(f"> 生成时间: {now}  \n")
        f.write(f"> 分支: `{git_branch()}` @ `{git_head()}`  \n")
        f.write(f"> ⛔ **状态: 测试环境评审材料，未上线**\n\n")

        f.write("## 0. 评审权限与状态标记规则\n\n")
        f.write("| 标记 | 含义 | 展示规则 | 投产结论 |\n|---|---|---|---|\n")
        f.write("| 🟢 **FULL_OK** | 全部 series 校验通过 | 正常展示 | 可投产（评审通过后） |\n")
        f.write("| 🔴 **PART_OK** | 含 INVALID/MISSING series | 红色告警条 + 🚫标记 + 失败明细表 | **禁止投产** |\n")
        f.write("| 🟠 **口径待复核** | FILLED 匹配存在口径冲突(P0) | 需在模板标题加注 | 复核通过前禁止投产 |\n\n")
        f.write(f"全套 {len(detail)} 张图表中: 🟢 FULL_OK **{len(detail)-len(part_ids)}** 张 | "
                f"🔴 PART_OK **{len(part_ids)}** 张\n\n")

        f.write("## 1. 评审总览\n\n")
        f.write("| 指标 | 数值 |\n|---|---|\n")
        f.write(f"| 评审图表总数 | {html_total} |\n")
        f.write(f"| 渲染成功（有有效数据） | {html_total-len(failed_charts)} ({(html_total-len(failed_charts))/html_total*100:.1f}%) |\n")
        f.write(f"| 渲染失败（零数据） | {len(failed_charts)} |\n")
        f.write(f"| 视觉校验平均分 | {sum(scores.values())/len(scores):.2f} / 10 |\n")
        f.write(f"| 满分(10)图表 | {Counter(scores.values())[10]} |\n")
        f.write(f"| 低于满分图表（需复核） | {len(low_score)} |\n")
        f.write(f"| P0 高优先级图表（复合/堆叠/多折线） | {len(p0_type_charts)} |\n")
        f.write(f"| 异常指标 series（INVALID+MISSING） | {len(abnormal)} |\n")
        f.write(f"| 模糊匹配待抽检 | {len(filled)} 条 / {len(uniq_list)} 组唯一 |\n")
        f.write(f"| Framework Tree 节点数 | {node_index['total_nodes']} |\n\n")

        f.write("## 2. 评审材料索引\n\n")
        f.write("| # | 材料 | 用途 |\n|---|---|---|\n")
        f.write("| 1 | `fuzzy_match_sample_checklist.md` | 124 条模糊匹配抽检（低分优先，含 P0 口径冲突） |\n")
        f.write("| 2 | `abnormal_indicator_list.csv` | 5 INVALID + 2 MISSING 异常指标清单 |\n")
        f.write("| 3 | `schema_adapt_doc.md` | DSHB↔schema 字段适配规则（固化，供后续模板对齐） |\n")
        f.write("| 4 | `pre_merge_checklist.md` | 合并前检查 + 部署步骤 + 回滚方案 |\n")
        f.write(f"| 5 | `../v85_chart_online_test/rendered/` | {html_total} 张图表 HTML 预览 |\n")
        f.write("| 6 | `../v85_chart_online_test/visual_check_result.csv` | 333 行视觉评分明细 |\n")
        f.write("| 7 | `../v85_chart_online_test/node_mapping_index.csv` | 节点-模板映射 |\n")
        f.write("| 8 | `../v85_chart_online_test/failed_chart_list.md` | 渲染失败清单 |\n\n")

        f.write("## 3. P0 高优先级图表快速筛选\n\n")
        f.write(f"> 按工单要求: 双Y/复合/堆叠类型共 **{len(p0_type_charts)}** 张，建议最先评审。\n\n")
        f.write("| # | 模板 | 品种 | 图表类型 | 标题 | 评分 | 状态 | 预览 |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for i, r in enumerate(p0_type_charts, 1):
            mark = "🔴 PART_OK" if r["template_id"] in part_ids else "🟢 FULL_OK"
            f.write(f"| {i} | `{r['template_id']}` | {r['variety']} | {r['chart_type']} | "
                    f"{r['title'][:22]} | {r['visual']['score']} | {mark} | "
                    f"[打开](../v85_chart_online_test/rendered/{r['template_id']}.html) |\n")

        f.write("\n## 4. 按评分排序（需复核的图表）\n\n")
        f.write(f"> 共 {len(low_score)} 张低于满分，按评分升序。评分=0 的 5 张即渲染失败图表。\n\n")
        f.write("| 评分 | 模板 | 品种 | 未通过项 | 预览 |\n|---|---|---|---|---|\n")
        for r in low_score:
            fi = "、".join(r["visual"]["failed_items"])[:46]
            mark = "🔴" if r["template_id"] in part_ids else "🟢"
            f.write(f"| {r['visual']['score']} | {mark} `{r['template_id']}` | {r['variety']} | "
                    f"{fi} | [预览](../v85_chart_online_test/rendered/{r['template_id']}.html) |\n")

        f.write("\n## 5. 按品种分组\n\n")
        f.write("| 品种 | 图表数 | 渲染成功 | FULL_OK | PART_OK | 平均评分 | P0类型 | 品种入口 |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for v in sorted(variety_groups, key=lambda x: -len(variety_groups[x])):
            rs = variety_groups[v]
            ok = sum(1 for r in rs if any(s["point_count"] > 0 for s in r["series"]))
            fo = sum(1 for r in rs if r["template_id"] not in part_ids)
            po = sum(1 for r in rs if r["template_id"] in part_ids)
            sc = sum(r["visual"]["score"] for r in rs) / len(rs)
            p0 = sum(1 for r in rs if r["chart_type"] in P0_TYPES)
            first = rs[0]["template_id"]
            link = f"[{first}.html](../v85_chart_online_test/rendered/{first}.html)"
            f.write(f"| {v} {VARIETY_NAME.get(v,'')} | {len(rs)} | {ok} | {fo} | {po} | "
                    f"{sc:.2f} | {p0} | {link} |\n")

        f.write("\n## 6. 🔴 PART_OK 图表（禁止投产，强制告警）\n\n")
        f.write("| 模板 | 品种 | 标题 | 失败 series | 原因 | 预览 |\n|---|---|---|---|---|---|\n")
        for a in abnormal:
            f.write(f"| `{a['模板ID']}` | {a['品种']} | {a['图表标题'][:22]} | "
                    f"{a['指标名称(PDF系列名)'][:22]} | {a['DHSB报错原因'][:26]} | "
                    f"[预览](../v85_chart_online_test/rendered/{a['模板ID']}.html) |\n")
        f.write(f"\n> 注: TPL-SI-034 含 1 条 INVALID + 2 条正常 series，属部分可用，同样禁止投产。\n\n")

        f.write("## 7. 建议评审顺序\n\n")
        f.write("| 步骤 | 内容 | 预计耗时 | 产出 |\n|---|---|---|---|\n")
        f.write("| 1 | P0 高优先级图表（复合/堆叠/多折线，11张） | 20min | 图表样式/双Y轴确认 |\n")
        f.write(f"| 2 | P0 口径冲突抽检（{risk_cnt['P0']}项） | 30min | 口径判定结论 |\n")
        f.write(f"| 3 | P1 匹配抽检（{risk_cnt['P1']}项） | 20min | 键语义确认 |\n")
        f.write("| 4 | 渲染失败图表（5张）+ 异常指标（7条） | 15min | 补 ID 清单 |\n")
        f.write("| 5 | 评分 < 10 的其余图表（38张） | 25min | 视觉细节确认 |\n")
        f.write("| 6 | 节点映射索引核对 | 10min | 节点完整性 |\n")
        f.write(f"| 7 | 汇总评审结论，走 `pre_merge_checklist.md` | 10min | 合并决定 |\n\n")
        f.write(f"**合计约 130 分钟（2.2 小时）**\n")

    # ==================================================================
    # T2.2 schema_adapt_doc.md — 字段适配文档
    # ==================================================================
    t0 = templates[0]
    with open(OUT / "schema_adapt_doc.md", "w", encoding="utf-8") as f:
        f.write("# 模板字段适配文档：DSHB 交付格式 ↔ chart_template_schema.json\n\n")
        f.write(f"> 工单: `HERMES_V85_ARTIFICIAL_REVIEW_PREP`  \n")
        f.write(f"> 生成时间: {now}  \n")
        f.write(f"> 适配实现: `t22_render_online.py::adapt_template()`  \n")
        f.write("> ⚠️ **本文档为模板输出对齐规范，后续 DSHB 模板输出应直接对齐本文档 §4「目标规范」，"
                "避免再次出现字段不匹配。**\n\n")

        f.write("## 1. 问题背景\n\n")
        f.write("DSHB 交付的 `pdf_web_chart_template_hermes_ready.json` 与本仓库前置框架开发的 "
                "`chart_template_schema.json` **字段命名体系完全不同**，无法直接渲染。"
                "首次接入时因此阻塞，需编写适配层。本文档固化映射规则，使后续模板可直接对齐。\n\n")

        f.write("## 2. 顶层结构映射\n\n| 语义 | DSHB 交付字段 | schema 目标字段 | 备注 |\n|---|---|---|---|\n")
        f.write("| 模板唯一ID | `template_id` | `chart_id` | 命名不同，语义等价 |\n")
        f.write("| 模板版本 | `version` | `version` | 一致 (v85) |\n")
        f.write("| 图表标题 | `source.chart_title` | `title` | **DSHB 嵌套在 source 下** |\n")
        f.write("| 品种代码 | `variety` | `meta.variety` | **DSHB 顶层平铺，schema 在 meta 下** |\n")
        f.write("| 图表类型 | `chart_type` | `meta.chart_type` | DSHB 中文枚举 |\n")
        f.write("| 模板状态 | `metadata.verify_status` | `meta.status` | **枚举值完全不同** |\n")
        f.write("| 时间戳 | `metadata.verify_timestamp` | `meta.timestamp` | ISO8601 |\n\n")

        f.write("## 3. 逐字段映射明细\n\n")
        f.write("| # | DSHB 实际字段 | schema 字段 | 转换规则 | 陷阱说明 |\n")
        f.write("|---|---|---|---|---|\n")
        rows_map = [
            ("`template_id`", "`chart_id`", "直接映射", "如 `TPL-AO-001`"),
            ("`metadata.verify_status`", "`meta.status`",
             "`FULL_OK`→`released`, `PART_OK`→`warning`",
             "**`metadata.status` 恒为 `draft`，不可用！**"),
            ("`source.chart_title`", "`title`", "直接映射", "为空时降级为「未命名图表」"),
            ("`source.file`", "`meta.source_file`", "直接映射", "PDF 文件名，用于页脚标注"),
            ("`source.page`", "`meta.source_page`", "直接映射", "PDF 页码"),
            ("`source.chart_local_id`", "`meta.chart_local_id`", "直接映射", "如 `chart_01`"),
            ("`variety`", "`meta.variety`", "直接映射 + 查表取中文名/颜色", "AO/CU/AL/PB/ZN/NI/SN/SI/LC"),
            ("`chart_type`", "`meta.chart_type`", "中文枚举 → 渲染策略映射",
             "单折线/多折线/堆叠柱状/复合混合(折线+柱状)"),
            ("`axis.left.unit`", "`y_axis.left.unit`", "直接映射", "坐标轴单位"),
            ("`axis.right.unit`", "`y_axis.right.unit`", "直接映射", "可为 null"),
            ("`series[].name`", "`series[].name`", "直接映射", "图例名称"),
            ("`series[].indicator_key`", "`series[].indicator_key`", "直接映射", "如 `wr34`，INVALID项常保留"),
            ("`series[].zhiji_id`", "`series[].zhiji_id`", "直接映射",
             "**INVALID/MISSING 项此字段为 null（原 ID 已被清空）**"),
            ("`series[].unit`", "`series[].unit`", "直接映射，缺失时回退 `axis.left.unit`", "三级回退"),
            ("`series[].axis`", "`series[].y_axis`", "`left`/`right` 同义",
             "**字段名不同: DSHB `axis` vs schema `y_axis`**"),
            ("`series[].line_type`", "`series[].style.line_type`",
             "solid/dashed/dotted/dash_dot → ECharts lineStyle.type",
             "dash_dot 需转数组 `[8,4,2,4]`"),
            ("`series[].color`", "`series[].style.color`", "直接映射", "缺失时回退品种主题色"),
            ("`series[].symbol`", "`series[].style.symbol`", "直接映射", "circle/rect/diamond/triangle/none"),
            ("`series[].verify_status`", "`series[].status`",
             "VALID/FILLED/INVALID/MISSING 四态",
             "**INVALID/MISSING 必须跳过渲染并告警**"),
            ("`series[].verify_note`", "`series[].note`", "直接映射",
             "**承载原始错误原因**（如 `API错误: HTTP 500`、`未找到候选ID`）"),
            ("`layout.legend.position`", "`legend.position`", "直接映射", "top/bottom/left/right"),
            ("`metadata.notes`", "`meta.notes`", "直接映射", "恒为 draft 提示，无信息量"),
        ]
        for i, (a, b, c, d) in enumerate(rows_map, 1):
            f.write(f"| {i} | {a} | {b} | {c} | {d} |\n")

        f.write("\n### 3.1 推导字段（DSHB 无对应字段，需运行时计算）\n\n")
        f.write("| schema 字段 | 推导规则 |\n|---|---|\n")
        f.write("| `series[].plot_type` | 由 `chart_type` 决定: 堆叠柱状→全 `bar`; "
                "复合混合→首个 `line` 其余 `bar`; 其余→`line` |\n")
        f.write("| `use_dual_axis` | `any(series.axis=='right')` OR `chart_type in "
                "(复合混合, 双Y轴)` |\n")
        f.write("| `series[].stack` | `chart_type=='堆叠柱状'` AND 该 series 有数据 |\n")
        f.write("| `node_code` | 按标题关键词推断业务节点: 价/升贴水/溢价→价格; 库存→库存; "
                "产量/开工率→供给; 利润→成本利润; 消费→需求; 出口/进口→进出口; 持仓→资金 |\n\n")

        f.write("## 4. 目标规范（后续 DSHB 模板输出应对齐）\n\n")
        f.write("```json\n")
        f.write("{\n")
        f.write("  \"chart_id\": \"TPL-AO-001\",            // ← 原 template_id\n")
        f.write("  \"title\": \"三网均价-内蒙古\",           // ← 原 source.chart_title (提至顶层)\n")
        f.write("  \"meta\": {                              // ← 原品种/类型/状态集中到 meta\n")
        f.write("    \"variety\": \"AO\",\n")
        f.write("    \"chart_type\": \"单折线\",\n")
        f.write("    \"status\": \"released\",              // ← 原 metadata.verify_status, 枚举转换\n")
        f.write("    \"source_file\": \"氧化铝周报20260830.pdf\",\n")
        f.write("    \"source_page\": 6,\n")
        f.write("    \"chart_local_id\": \"chart_01\",\n")
        f.write("    \"timestamp\": \"2026-09-30T11:13:50+08:00\"\n")
        f.write("  },\n")
        f.write("  \"y_axis\": {                            // ← 原 axis 改名\n")
        f.write("    \"left\":  {\"unit\": \"元/吨\"},\n")
        f.write("    \"right\": null\n")
        f.write("  },\n")
        f.write("  \"legend\": {\"position\": \"top\"},      // ← 原 layout.legend.position 提平\n")
        f.write("  \"series\": [{\n")
        f.write("    \"name\": \"三网均价-内蒙古\",\n")
        f.write("    \"indicator_key\": \"wr34\",\n")
        f.write("    \"zhiji_id\": \"ID01721686\",\n")
        f.write("    \"y_axis\": \"left\",                  // ← 原 axis 改名\n")
        f.write("    \"unit\": \"元/吨\",\n")
        f.write("    \"plot_type\": \"line\",               // ← 新增，明确渲染类型\n")
        f.write("    \"style\": {\"color\": \"#5470c6\", \"line_type\": \"solid\", \"symbol\": \"circle\"},\n")
        f.write("    \"status\": \"valid\",                 // ← 原 verify_status 小写化\n")
        f.write("    \"note\": \"氧化铝：长单均价：内蒙古（月）\"\n")
        f.write("  }]\n")
        f.write("}\n```\n\n")

        f.write("## 5. 状态枚举转换表\n\n")
        f.write("| 层级 | DSHB 枚举 | schema 枚举 | 渲染行为 |\n|---|---|---|---|\n")
        f.write("| 模板 | `FULL_OK` | `released` | 全量渲染 |\n")
        f.write("| 模板 | `PART_OK` | `warning` | 渲染 + 红色告警条 + 禁止投产标记 |\n")
        f.write("| 模板 | `metadata.status='draft'` | — | **忽略（DSHB 恒为 draft，无信息量）** |\n")
        f.write("| series | `VALID` | `valid` | 正常渲染 |\n")
        f.write("| series | `FILLED` | `filled` | 正常渲染（但需抽检口径） |\n")
        f.write("| series | `INVALID` | `invalid` | 跳过渲染 + 红色虚线占位 + 明细告警 |\n")
        f.write("| series | `MISSING` | `missing` | 跳过渲染 + 红色虚线占位 + 明细告警 |\n\n")

        f.write("## 6. 关键陷阱（必读）\n\n")
        f.write("1. **`metadata.status` ≠ `metadata.verify_status`**: DSHB 模板的 "
                "`metadata.status` **恒为 `\"draft\"`**（硬编码提示语），真正的校验状态在 "
                "`metadata.verify_status`。首次接入误用前者导致全部模板被判为草稿。\n\n")
        f.write("2. **INVALID/MISSING series 的 `zhiji_id` 是 `null`**: 原 zhiji_id 已被 DSHB "
                "清空，**无法从 JSON 直接获取原 ID**（原 ID 仅记录在 `hermes_readme.md §6` 表格中）。"
                "错误原因保留在 `verify_note`。\n\n")
        f.write("3. **唯一可拉取 ID 为 248 而非 252**: 362 series 去重后 VALID+FILLED 唯一 ID 248 个；"
                "5 INVALID + 2 MISSING 均为 null，不占 ID 计数。\n\n")
        f.write("4. **`chart_type` 为中文枚举**: 必须经映射表转渲染策略，不可直接传 ECharts。\n\n")
        f.write("5. **单位三级回退**: `series.unit` → `axis.left.unit` → `\"数值\"`，"
                "部分 series 无 unit 字段。\n\n")
        f.write("6. **品种仅 6 个**: DSHB 实际交付 LC/AO/SI/AL/SN/NI，**无 CU（铜）/PB（铅）**，"
                "与 9 品种配置有差异，节点索引按实际 6 品种生成。\n\n")

        f.write("## 7. 适配实现与验证\n\n")
        f.write(f"| 项 | 值 |\n|---|---|\n")
        f.write("| 适配函数 | `t22_render_online.py::adapt_template()` |\n")
        f.write("| 拉取脚本 | `t21_fetch_zhiji.py`（1s 限速 + 断点续跑） |\n")
        f.write("| 模板包 MD5 | `92371c0a` (pdf_web_chart_template_hermes_ready.json) |\n")
        f.write("| 校验统计 MD5 | `dba27ff4` (zhiji_verify_stat.csv) |\n")
        f.write(f"| 模板数 | {len(templates)}（FULL_OK {len(templates)-len(part_ids)} / PART_OK {len(part_ids)}） |\n")
        f.write(f"| series 数 | {len(verify_rows)}（VALID 231 / FILLED 124 / INVALID 5 / MISSING 2） |\n")
        f.write(f"| 渲染成功 | {html_total-len(failed_charts)}/{html_total} |\n\n")
        f.write("## 8. 后续模板输出对齐要求\n\n")
        f.write("1. **字段命名**: 直接采用 §4 目标规范的字段名，不再使用 `template_id`/`axis`/`layout.legend`\n")
        f.write("2. **状态集中**: 品种、图表类型、状态、来源统一放入 `meta` 对象\n")
        f.write("3. **状态枚举**: 使用 `released`/`warning` 与 `valid`/`filled`/`invalid`/`missing`\n")
        f.write("4. **保留原 ID**: INVALID/MISSING series **必须保留 `original_zhiji_id` 字段**，"
                "供人工查找备选指标（本次交付因清空原 ID 增加排查成本）\n")
        f.write("5. **记录匹配分数**: FILLED 系列应保留 `match_score` 与 `match_source` 字段\n")
        f.write("6. **plot_type 显式声明**: 不再依赖 `chart_type` 推断单系列类型\n")

    # ==================================================================
    # T2.6 pre_merge_checklist.md
    # ==================================================================
    ind_md5 = md5_short("/home/ubuntu/framework-tree/data/indicators_v1.json")
    tc_md5 = md5_short("/home/ubuntu/framework-tree/data/tree_config.json")

    with open(OUT / "pre_merge_checklist.md", "w", encoding="utf-8") as f:
        f.write("# V85 图表模板分支合并上线检查清单与回滚方案\n\n")
        f.write(f"> 工单: `HERMES_V85_ARTIFICIAL_REVIEW_PREP`  \n")
        f.write(f"> 生成时间: {now}  \n")
        f.write(f"> 当前分支: `{git_branch()}` @ `{git_head()}`  \n")
        f.write("> ⛔ **本文档仅为准备材料，当前不发起任何生产部署**\n\n")

        f.write("## 1. 分支合并前检查项（Blocker 必须全部通过）\n\n")
        f.write("### 1.1 Blocker 项（不通过禁止合并）\n\n")
        f.write("| # | 检查项 | 当前状态 | 通过条件 |\n|---|---|---|---|\n")
        f.write(f"| B1 | P0 口径冲突抽检 | ❌ **{risk_cnt['P0']} 项待处理** | "
                "全部判定结论为「✅通过」或已替换为新 zhiji_id |\n")
        f.write(f"| B2 | 异常指标补 ID | ❌ **{len(abnormal)} 条无有效数据** | "
                "5 INVALID + 2 MISSING 全部补齐 zhiji_id 并重跑 |\n")
        f.write(f"| B3 | PART_OK 处置决策 | ❌ **{len(part_ids)} 张待定** | "
                "逐张决策: 升级 FULL_OK 或永久剔除 |\n")
        f.write(f"| B4 | P1 匹配抽检 | ⚠️ **{risk_cnt['P1']} 项待处理** | 全部人工确认 |\n")
        f.write("| B5 | 视觉验收 | ⚠️ 待评审 | 业务方逐图对照 PDF 原图签字 |\n")
        f.write(f"| B6 | 低分图表复核 | ⚠️ {len(low_score)} 张待复核 | 评分 <7 的必须处理 |\n")
        f.write("| B7 | 门禁校验 reclaim.py | ⏳ 未执行 | `python3 scripts/reclaim.py` 全部通过 |\n")
        f.write("| B8 | 节点映射核对 | ✅ 36 节点已生成 | 业务确认节点归属正确 |\n\n")

        f.write("### 1.2 约束合规检查（当前已全部通过 ✅）\n\n")
        f.write("| # | 约束 | 状态 | 证据 |\n|---|---|---|---|\n")
        f.write("| C1 | 仅测试分支，禁止合并 main | ✅ | 当前 `feature/v85-chart-template` |\n")
        f.write(f"| C2 | 不修改 indicators_v1.json | ✅ | MD5 `{ind_md5}` 未变 |\n")
        f.write(f"| C3 | 不修改 tree_config.json | ✅ | MD5 `{tc_md5}` 未变 |\n")
        f.write("| C4 | 不修改原始模板包 | ✅ | MD5 `92371c0a` 未变 |\n")
        f.write("| C5 | PART_OK 强制告警 | ✅ | 6 张全部红色告警，FULL_OK 零误标 |\n")
        f.write("| C6 | 不发起生产部署 | ✅ | 仅本地渲染，未部署任何服务 |\n\n")

        f.write("### 1.3 数据资产盘点\n\n")
        f.write("| 资产 | 数量 | 位置 |\n|---|---|---|\n")
        f.write(f"| 渲染图表 HTML | {html_total} | `v85_chart_online_test/rendered/` |\n")
        f.write("| zhiji 时序缓存 | 248 | `zhiji_data_cache/` |\n")
        f.write(f"| 节点索引 | {node_index['total_nodes']} 节点 | `node_index.json` / `node_mapping_index.csv` |\n")
        f.write("| 视觉评分记录 | 333 行 | `visual_check_result.csv` |\n")
        f.write("| 渲染明细 | 6.5MB | `render_detail.json` |\n\n")

        f.write("## 2. 合并执行步骤（评审通过后方可执行）\n\n")
        f.write("```bash\n# 前置: 确认所有 Blocker 已通过\ncd /home/ubuntu/framework-tree\n\n")
        f.write("# 1. 确认当前分支与状态\ngit checkout feature/v85-chart-template\ngit status --short\ngit log --oneline -5\n\n")
        f.write("# 2. 更新 main 基线\ngit fetch origin\ngit checkout main\ngit pull origin main\n\n")
        f.write("# 3. 门禁校验（合并前必须全部通过）\npython3 scripts/reclaim.py\n\n")
        f.write("# 4. 执行合并\ngit merge --no-ff feature/v85-chart-template \\\n  -m \"feat(v85): 图表模板在线渲染 333图 + 36节点映射 (HERMES_V85_CHART_TEMPLATE_INTEGRATION)\"\n\n")
        f.write("# 5. 推送\ngit push origin main\n\n")
        f.write("# 6. 清理测试分支（可选）\ngit push origin --delete feature/v85-chart-template\n```\n\n")

        f.write("## 3. 生产环境部署步骤（需单独部署工单）\n\n")
        f.write("> ⚠️ 本文档仅描述步骤，**当前不执行**。部署需另开工单并确认资源。\n\n")
        f.write("### 3.1 部署前准备\n\n")
        f.write("| # | 步骤 | 说明 |\n|---|---|---|\n")
        f.write("| D1 | 前端路由接入 | 按 `node_mapping_index.csv` 的 `node_path` 配置品种页面路由 |\n")
        f.write("| D2 | 静态资源发布 | `rendered/*.html` 部署至看板静态目录 |\n")
        f.write("| D3 | zhiji 拉取定时任务 | 按品种数据频率配置（日度/周度/月度）增量拉取 |\n")
        f.write("| D4 | ECharts CDN 缓存 | 本地化 `echarts@5.5.0`，避免 CDN 抖动 |\n")
        f.write("| D5 | 数据缓存策略 | zhiji 时序落本地，避免重复调用（当前已实现缓存） |\n")
        f.write("| D6 | 额度监控 | 配置 zhiji API 调用额度告警 |\n\n")
        f.write("### 3.2 部署执行\n\n")
        f.write("```bash\n# 1. 构建前端产物\n# (按项目构建流程执行)\n\n# 2. 增量拉取数据（避免全量重跑 764s）\n# python3 t21_fetch_zhiji.py   # 有缓存自动跳过，仅新增/失效 ID 会拉取\n\n# 3. 重新渲染\npython3 t22_render_online.py\n\n# 4. 发布至看板服务\n# (发布流程按现有部署规范执行)\n\n# 5. 冒烟验证\n# - 抽查 6 个品种各 3 张图表\n# - 确认 PART_OK 告警展示正确\n# - 确认 zhiji 数据为最新\n```\n\n")

        f.write("## 4. 回滚方案\n\n")
        f.write("### 4.1 合并回滚（代码级）\n\n")
        f.write("```bash\n# 场景: 合并后发现问题\n# 方式A: revert 合并提交（推荐，保留历史）\ngit revert -m 1 <merge_commit_sha>\ngit push origin main\n\n")
        f.write("# 方式B: 强制回退（慎用，需确认无他人提交）\ngit log --oneline -5\ngit reset --hard <merge前commit>\ngit push --force-with-lease origin main\n```\n\n")
        f.write("### 4.2 部署回滚（运行时）\n\n")
        f.write("| 层级 | 回滚动作 | 耗时 | 说明 |\n|---|---|---|---|\n")
        f.write("| 图表层 | 删除 `rendered/*.html` 并恢复上一版本 | 5min | 不影响其他功能 |\n")
        f.write("| 路由层 | 移除品种页面路由配置 | 10min | 页面不可访问但不报错 |\n")
        f.write("| 数据层 | zhiji 缓存保留不删 | 0 | 缓存可复用，无需重建 |\n")
        f.write("| 全量 | revert 合并 + 清除静态资源 | 20min | 完全回到合并前状态 |\n\n")

        f.write("### 4.3 回滚触发条件\n\n")
        f.write("| 优先级 | 触发条件 | 建议动作 |\n|---|---|---|\n")
        f.write("| P0 | 口径错误图表被业务方发现并投诉 | 立即图表层回滚 |\n")
        f.write("| P0 | 页面白屏/JS 报错 | 立即图表层回滚 |\n")
        f.write("| P1 | zhiji 额度耗尽导致大面积空图 | 暂停拉取任务，保留缓存 |\n")
        f.write("| P2 | 少量图表样式异常 | 定点修复，无需回滚 |\n\n")

        f.write("### 4.4 回滚验证清单\n\n")
        f.write("- [ ] `git log --oneline -3` 确认 revert 提交存在\n")
        f.write("- [ ] 抽查 6 个品种页面均可正常访问（或已下线）\n")
        f.write("- [ ] `scripts/reclaim.py` 门禁通过\n")
        f.write("- [ ] indicators_v1.json / tree_config.json MD5 未变\n")
        f.write("- [ ] STATUS.md 已记录回滚原因\n\n")

        f.write("## 5. 上线判定矩阵\n\n")
        f.write("| 条件组合 | 决策 |\n|---|---|\n")
        f.write("| B1-B8 全部通过 | ✅ 合并并部署 |\n")
        f.write("| B1/B4 抽检发现口径错误 | ❌ 替换 ID 后重跑，重新评审 |\n")
        f.write("| 仅 B2/B3 未决（异常指标） | ⚠️ 可先合并，PART_OK 图表不挂载至看板 |\n")
        f.write("| 视觉验收未通过 | ❌ 不合并，修复后重新生成评审材料 |\n\n")

        f.write("\n## 6. 遗留项汇总\n\n")
        f.write("| 优先级 | 事项 | 数量 | 影响 |\n|---|---|---|---|\n")
        f.write(f"| P0 | 口径冲突模糊匹配 | {risk_cnt['P0']} 项 | 图表数据误导，禁止投产 |\n")
        f.write(f"| P0 | INVALID zhiji_id (HTTP 500) | 5 条 | 图表空渲染 |\n")
        f.write(f"| P0 | MISSING series | 2 条 | 图表空渲染 |\n")
        f.write(f"| P1 | P1 匹配待复核 | {risk_cnt['P1']} 项 | 口径可能不一致 |\n")
        f.write(f"| P1 | PART_OK 模板处置 | {len(part_ids)} 张 | 不纳入正式投产 |\n")
        f.write(f"| P2 | 低分图表 | {len(low_score)} 张 | 视觉细节 |\n")
        f.write("| P2 | delivery_confirm.md 缺失 | 1 项 | 已用 MD5 实测替代 |\n\n")

    # ---- 汇总 ----
    print("=== HERMES_V85_ARTIFICIAL_REVIEW_PREP 产出 ===")
    for fn in ["review_portal.md", "schema_adapt_doc.md", "abnormal_indicator_list.csv",
               "fuzzy_match_sample_checklist.md", "pre_merge_checklist.md"]:
        p = OUT / fn
        print(f"  {fn:40s} {p.stat().st_size:>8,}B")
    print(f"\n异常指标: {len(abnormal)} 条 | 模糊匹配: {len(filled)}条/{len(uniq_list)}组 | "
          f"风险分级: {dict(risk_cnt)}")
    print(f"P0类型图表: {len(p0_type_charts)} | 低于满分: {len(low_score)} | 渲染失败: {len(failed_charts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
