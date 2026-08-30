#!/usr/bin/env python3
"""批量知几验证脚本 (Step3 第一层: search 阶段)
读 /tmp/decision_indicators.json (code -> node -> [指标名])
对每个 (code, 指标名) 去重后调用 zhiji search, 保存 top3 命中到
analysis/iwencai/step3_search_results.json

裁判逻辑:
  - 命中分: 3 = SMM 且名称含品种词; 2 = 非SMM但名称含品种词; 1 = 名称相关; 0 = 无相关
  - 每指标记录 best_* (id/name/source/score文字/unit)
"""
import json, os, subprocess, sys, time

ROOT = "/home/ubuntu/framework-tree/analysis/iwencai"
SRC = "/tmp/decision_indicators.json"
OUT = os.path.join(ROOT, "step3_search_results.json")

def clean(name):
    # 去掉【正主】【辅助】【待验证】等前缀标记
    import re
    n = re.sub(r"【[^】]*】", "", name).strip()
    n = re.sub(r"^[*-]\s*", "", n).strip()
    return n

def main():
    code = sys.argv[1] if len(sys.argv) > 1 else "CU"
    data = json.load(open(SRC))
    nodes = data.get(code, {})
    # 收集唯一指标名
    uniq = {}
    for node, names in nodes.items():
        for n in names:
            c = clean(n)
            if not c or len(c) < 2:
                continue
            uniq.setdefault(c, []).append(node)
    print(f"[{code}] 唯一指标名: {len(uniq)}")

    # 已有结果继续（断点续跑）
    results = {}
    if os.path.exists(OUT):
        results = json.load(open(OUT))
    results.setdefault(code, {})

    done = set(results[code].keys())
    todo = [n for n in uniq if n not in done]
    print(f"[{code}] 已跑 {len(done)}, 待跑 {len(todo)}")
    if not todo:
        return

    for i, q in enumerate(todo, 1):
        try:
            r = subprocess.run(
                [sys.executable, os.path.expanduser("~/.hermes/scripts/zhiji_api.py"),
                 "search", q],
                capture_output=True, text=True, timeout=60)
            raw = r.stdout.strip()
            try:
                j = json.loads(raw)
            except Exception:
                j = {"raw": raw[:300]}
            hits = j.get("results", [])[:3]
            results[code][q] = {
                "nodes": uniq[q],
                "hits": [
                    {"id": h.get("id"), "name": h.get("name"),
                     "source": h.get("source"), "unit": h.get("unit"),
                     "path": (h.get("path") or "")[:60]}
                    for h in hits
                ],
                "count": j.get("count"),
            }
        except Exception as e:
            results[code][q] = {"nodes": uniq[q], "hits": [], "error": str(e)}
        if i % 10 == 0 or i == len(todo):
            json.dump(results, open(OUT, "w"), ensure_ascii=False, indent=1)
            print(f"[{code}] {i}/{len(todo)} 已写入")
        time.sleep(1.2)
    json.dump(results, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"[{code}] 完成, 共 {len(todo)} 个, 已保存 {OUT}")

if __name__ == "__main__":
    main()