#!/usr/bin/env python3
"""Step3 最终汇总: 合并 人工判定(verdict_al1) + 规则判定(verdict_rule), 分层输出。

分层逻辑:
  Tier A = 子代理逐条人工判定过 (verdict_al1.json, 96条, 质量最高)
  Tier B = 规则判定 matched, 需人工抽查 (其余)
  Tier C = unmatched → 备用库(待外部源/知几无序列)

输出:
  analysis/iwencai/step3_final.json     最终分层清单
  analysis/iwencai/step3_report.md      可读验收报告
"""
import json, os

ROOT = "/home/ubuntu/framework-tree/analysis/iwencai"
SL = os.path.join(ROOT, "step3_slices")

rule = json.load(open(os.path.join(SL, "verdict_rule.json")))
al1 = json.load(open(os.path.join(SL, "verdict_al1.json")))
# al2 部分人工判定(子代理写了15条就超时)
al2 = {}
p2 = os.path.join(SL, "verdict_al2.json")
if os.path.exists(p2):
    al2 = json.load(open(p2))

final = {}
for code in ["CU", "AL"]:
    final[code] = {}
    for q, v in rule[code].items():
        # AL 前半以人工判定为准
        manual = al1.get(q)
        if manual:
            tier = "A"
            chosen = manual.get("chosen")
            matched = bool(manual.get("matched"))
            note = manual.get("note", "")
        else:
            tier = "B" if v["matched"] else "C"
            chosen = v.get("chosen")
            matched = v["matched"]
            note = v.get("note", "")
        final[code][q] = {
            "nodes": v.get("nodes", []),
            "tier": tier,
            "matched": matched,
            "chosen": chosen,
            "note": note,
        }

json.dump(final, open(os.path.join(ROOT, "step3_final.json"), "w"),
          ensure_ascii=False, indent=1)

# 出报告
lines = ["# 铜(CU)/铝(AL) Step3 知几验证 · 最终报告", ""]
lines.append("## 分层结果")
lines.append("")
lines.append("| 品种 | 总指标 | Tier A 人工 | Tier B 规则通过 | Tier C 备用库 |")
lines.append("|---|---|---|---|---|")
for code in ["CU", "AL"]:
    d = final[code]
    a = sum(1 for x in d.values() if x["tier"] == "A")
    b = sum(1 for x in d.values() if x["tier"] == "B")
    c = sum(1 for x in d.values() if x["tier"] == "C")
    lines.append("| %s | %d | %d | %d | %d |" % (code, len(d), a, b, c))
lines.append("")
lines.append("## 说明")
lines.append("")
lines.append("- **Tier A**：子代理逐条人工判定（铝前半96条），含口径错位/方向错位/衍生指标判断，可直接灌库")
lines.append("- **Tier B**：规则判定 matched（品种词+字段词+交易所+国家+官方源 五重校验），灌库前建议抽查")
lines.append("- **Tier C**：unmatched → 备用库，标注原因（无序列/口径错位/设计说明文字）")
lines.append("")
lines.append("## Tier C 主要失败模式（供知几外部源补录参考）")
lines.append("")
modes = {}
for code in ["CU", "AL"]:
    for q, v in final[code].items():
        if v["tier"] == "C":
            n = v["note"]
            if "设计说明" in n: k = "设计说明文字(非指标)"
            elif "无任何命中" in n: k = "知几完全无序列"
            else: k = "有命中但口径/字段弱"
            modes.setdefault(k, []).append(q)
for k, qs in sorted(modes.items(), key=lambda x: -len(x[1])):
    lines.append("- **%s**：%d 个 — 例 %s" % (k, len(qs), " / ".join(q[:20] for q in qs[:4])))
lines.append("")
lines.append("## 产出文件")
lines.append("")
lines.append("- `step3_final.json` — 最终分层清单（本文件数据源）")
lines.append("- `step3_slices/verdict_al1.json` — 铝前半人工判定（Tier A 真源）")
lines.append("- `step3_slices/verdict_rule.json` — 规则判定结果")
lines.append("- `step3_search_results.json` / `step3_search_refine.json` — 原始 search 命中")

open(os.path.join(ROOT, "step3_report.md"), "w").write("\n".join(lines))

for code in ["CU", "AL"]:
    d = final[code]
    a = sum(1 for x in d.values() if x["tier"] == "A")
    b = sum(1 for x in d.values() if x["tier"] == "B")
    c = sum(1 for x in d.values() if x["tier"] == "C")
    print("%s: A=%d B=%d C=%d (总%d)" % (code, a, b, c, len(d)))
print("报告已生成 step3_report.md")