#!/usr/bin/env python3
"""Step3-5M: 并行知几 search (138节点/1102唯一指标)。

输入: /tmp/decision_indicators_5m.json  {CODE:{node:[指标名]}}
输出: analysis/iwencai/step3_search_results_5m.json
      {CODE:{指标名:{nodes,hits:[{id,name,source,unit,path}],count}}}

分批提交(consumer 立即消费, 避免 1102 任务全堆积); 断点续跑。
并发 4, 批间隔 0.3s。
"""
import json, os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

ROOT = "/home/ubuntu/framework-tree/analysis/iwencai"
SRC = "/tmp/decision_indicators_5m.json"
OUT = os.path.join(ROOT, "step3_search_results_5m.json")
ZJ = os.path.expanduser("~/.hermes/scripts/zhiji_api.py")
CODES = ["ZN", "NI", "SN", "SI", "LI"]
BATCH = 40
BATCH_GAP = 0.3

def clean(name):
    n = re.sub(r"【[^】]*】", "", name).strip()
    return re.sub(r"^[*-]\s*", "", n).strip()

def search_one(code, q):
    try:
        r = subprocess.run([sys.executable, ZJ, "search", q],
                           capture_output=True, text=True, timeout=60)
        j = json.loads(r.stdout.strip())
        hits = j.get("results", [])[:3]
        return {"nodes": q_nodes[code][q],
                "hits": [{"id": h.get("id"), "name": h.get("name"),
                          "source": h.get("source"), "unit": h.get("unit"),
                          "path": (h.get("path") or "")[:60]} for h in hits],
                "count": j.get("count")}
    except Exception as e:
        return {"nodes": q_nodes[code][q], "hits": [], "error": str(e)[:200]}

q_nodes = {}

def main():
    data = json.load(open(SRC, encoding="utf-8"))
    for code in CODES:
        uniq = {}
        for node, names in data[code].items():
            for n in names:
                c = clean(n)
                if c and len(c) >= 2:
                    uniq.setdefault(c, []).append(node)
        q_nodes[code] = uniq

    results = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    for code in CODES:
        results.setdefault(code, {})

    todo = [(code, q) for code in CODES for q in q_nodes[code]
            if q not in results[code]]
    print("待搜: %d" % len(todo), flush=True)
    if not todo:
        return

    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        for start in range(0, len(todo), BATCH):
            batch = todo[start:start + BATCH]
            futs = {ex.submit(search_one, c, q): (c, q) for c, q in batch}
            for f in futs:
                c, q = futs[f]
                results[c][q] = f.result()
                done += 1
            json.dump(results, open(OUT, "w"), ensure_ascii=False, indent=1)
            if done % 200 == 0 or done == len(todo):
                el = time.time() - t0
                print("%d/%d  %.0fs  avg %.2fs/项" % (done, len(todo), el, el / done),
                      flush=True)
            time.sleep(BATCH_GAP)

    print("\n=== 汇总 ===")
    tot_hit = 0
    for code in CODES:
        d = results[code]
        zero = sum(1 for v in d.values() if not v.get("hits"))
        tot_hit += len(d) - zero
        print("%s: %d 指标, 零命中 %d" % (code, len(d), zero), flush=True)
    print("有命中合计: %d" % tot_hit)
    print("完成 ->", OUT)

if __name__ == "__main__":
    main()
