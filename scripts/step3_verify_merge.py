#!/usr/bin/env python3
"""Step3 最终判定合并器: 读 search + refine 结果, 输出每个指标的候选命中汇总表。

用法: python3 step3_verify_merge.py
输出: analysis/iwencai/step3_verify_summary.json
  {code: {指标名: {
    "nodes": [...], "reason": "",  # 判定: matched / unmatch / maybe
    "hits": [{id,name,source,unit}] # 按优先级排序, 供人工复核或灌库
  }}}
"""
import json, os, re

ROOT = "/home/ubuntu/framework-tree/analysis/iwencai"

OFFICIAL_SOURCES = ["smm", "mysteel"]

def clean(name):
    return re.sub(r"【[^】]*】", "", name).strip()

def main():
    # 读 search 结果
    search = json.load(open(os.path.join(ROOT, "step3_search_results.json")))
    refine = {}
    rf = os.path.join(ROOT, "step3_search_refine.json")
    if os.path.exists(rf):
        refine = json.load(open(rf))

    summary = {}
    for code in ["CU", "AL"]:
        cu = search.get(code, {})
        summary[code] = {}
        for q, v in cu.items():
            cq = clean(q)
            if not cq or cq == "正主/辅助/排除项需 agent 知几验证时人工确认":
                continue
            hits = v.get("hits", [])
            entry = {"nodes": v.get("nodes", []), "hits": hits}
            # 合并精修结果: prefer refine hits
            if code in refine and q in refine.get(code, {}):
                rv = refine[code][q]
                if rv.get("skip"):
                    entry["skip"] = True
                for a in rv.get("attempts", []):
                    for h in a.get("hits", []):
                        if h not in entry["hits"]:
                            entry["hits"].append(h)
            summary[code][cq] = entry

    json.dump(summary, open(os.path.join(ROOT, "step3_verify_summary.json"), "w"),
              ensure_ascii=False, indent=1)
    for code in ["CU", "AL"]:
        print(f"{code}: {len(summary.get(code, {}))} 指标")

if __name__ == "__main__":
    main()