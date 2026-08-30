#!/usr/bin/env python3
"""Step3-5M: 汇总 + 报告 (五金属)。

五金属无 Tier A 人工判定 (138节点/1099指标量级, 由规则判定器兜底),
matched → Tier B (灌库前建议抽查); unmatched → Tier C (备用库)。
输出:
  analysis/iwencai/step3_final_5m.json   分层清单
  analysis/iwencai/step3_report_5m.md    可读验收报告
"""
import json, os

ROOT = "/home/ubuntu/framework-tree/analysis/iwencai"
SRC = os.path.join(ROOT, "step3_slices", "verdict_rule_5m.json")
FINAL = os.path.join(ROOT, "step3_final_5m.json")
REPORT = os.path.join(ROOT, "step3_report_5m.md")
CODES = ["ZN", "NI", "SN", "SI", "LI"]
CN = {"ZN": "锌", "NI": "镍", "SN": "锡", "SI": "硅", "LI": "锂"}

rule = json.load(open(SRC, encoding="utf-8"))

final = {}
for code in CODES:
    final[code] = {}
    for q, v in rule[code].items():
        final[code][q] = {
            "nodes": v.get("nodes", []),
            "tier": "B" if v["matched"] else "C",
            "matched": v["matched"],
            "chosen": v.get("chosen"),
            "note": v.get("note", ""),
        }

json.dump(final, open(FINAL, "w"), ensure_ascii=False, indent=1)

lines = ["# 五金属(锌/镍/锡/硅/锂) Step3 知几验证 · 最终报告", "",
         "## 分层结果", "",
         "| 品种 | 总指标 | Tier B 规则通过 | Tier C 备用库 | 通过率 |",
         "|---|---|---|---|---|"]
for code in CODES:
    d = final[code]
    b = sum(1 for x in d.values() if x["tier"] == "B")
    c = len(d) - b
    lines.append("| %s(%s) | %d | %d | %d | %.0f%% |" % (
        code, CN[code], len(d), b, c, 100.0 * b / max(1, len(d))))
tb = sum(1 for code in CODES for x in final[code].values() if x["tier"] == "B")
tt = sum(len(final[code]) for code in CODES)
lines.append("| **合计** | **%d** | **%d** | **%d** | **%.0f%%** |" % (
    tt, tb, tt - tb, 100.0 * tb / max(1, tt)))

lines += ["", "## 说明", "",
          "- **Tier B**：规则判定 matched（品种词 + 字段词 + 交易所前缀 + 地理冲突 + 矿端/冶炼端 + 跨品种串台 六重校验，阈值 score≥5）。灌库前建议抽查 20%。",
          "- **Tier C**：unmatched → 备用库，标注原因。多数为「有命中但口径/字段弱」，即知几有相邻口径指标但不完全对应（如 菲律宾镍矿进口 vs 冰镍进口）。",
          "- **无 Tier A**：五金属 138 节点 / 1099 唯一指标，量级超过人工判定阈值，全部走规则判定；抽查后如有误配再降 Tier。",
          "",
          "## 提取管线（v2 改进点）", "",
          "1. **decision.md 解析**：只取 `## 推荐图组合` 之后的 `###` 分节（排除项区在前，早期版本截断方向反了导致 0 提取）。",
          "2. **拆分符**：只按「、」拆指标名，不按「,，/」拆——全角括号单位（元/吨、万吨LCE）会被误切碎。",
          "3. **品种前缀补全**：发散输出常漏前缀（「持仓量（手）」→「锌持仓量（手）」），补全后 matched 290→344；补全时若已含任何品种/交易所词则不动，避免「镍镍持仓量」。",
          "",
          "## Tier C 主要失败模式"]
modes = {}
for code in CODES:
    for q, v in final[code].items():
        if v["tier"] == "C":
            n = v["note"]
            if "无任何命中" in n:
                k = "知几完全无序列"
            elif "设计说明" in n:
                k = "设计说明文字(非指标)"
            else:
                k = "有命中但口径/字段弱"
            modes.setdefault(k, []).append((code, q))
for k, qs in sorted(modes.items(), key=lambda x: -len(x[1])):
    lines.append("- **%s**：%d 个 — 例 %s" % (
        k, len(qs), " / ".join("%s·%s" % (c, q[:18]) for c, q in qs[:4])))

lines += ["", "## 已知缺口（需外部源/SMM 补录）", ""]
gap = [q for code in CODES for q, v in final[code].items()
       if v["tier"] == "C" and "无任何命中" in v["note"]]
lines.append("- 知几无序列 %d 个，集中在" % len(gap))
for g in gap[:15]:
    lines.append("  - `%s`" % g)
if len(gap) > 15:
    lines.append("  - ……（余 %d 个见 step3_final_5m.json）" % (len(gap) - 15))

lines += ["", "## 产出文件", "",
          "- `step3_final_5m.json` — 最终分层清单",
          "- `step3_report_5m.md` — 本报告",
          "- `step3_slices/verdict_rule_5m.json` — 规则判定结果",
          "- `step3_search_results_5m.json` — 原始 search 命中（1332 项，含 v1+v2）",
          "- 脚本：`step3_5m_extract.py`（提取+前缀补全）/ `step3_5m_search.py`（并行 search）/ `step3_5m_judge.py`（六重判定）",
          "", "## 注册建议", "",
          "Tier B 共 %d 条建议注册（脚本 `step3_5m_register.py`，命名 `zn_/ni_/sn_/si_/li_<节点短码>_<slug>`，"
          "id 去重跳过已在库的）。建议抽查 20%% 无误配后执行。" % tb]

open(REPORT, "w").write("\n".join(lines))
for code in CODES:
    d = final[code]
    b = sum(1 for x in d.values() if x["tier"] == "B")
    print("%s(%s): B=%d C=%d (总%d)" % (code, CN[code], b, len(d) - b, len(d)))
print("合计 B=%d/%d  报告 -> %s" % (tb, tt, REPORT))
