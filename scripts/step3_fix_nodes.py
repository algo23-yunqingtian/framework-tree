#!/usr/bin/env python3
"""修正 step3_final.json 的 nodes 字段。

问题: 原 /tmp/decision_indicators.json 的节点映射解析错误(全落 2.1)。
根因: decision 文件里指标格式是 `- **指标名** 【标签】 描述`,
      之前用 `^\*\*([^*]+)\*\*$` 行首正则匹配不到(指标前有 "- " 前缀)。

修法: 重解析 decision 文件, 用正确正则 `- \*\*(.+?)\*\*` 提取,
      并把"排除项"区的指标过滤掉(它们不该参与 search)。
然后 patch step3_final.json 的 nodes 字段。

输出: /tmp/decision_indicators_fixed.json (正确映射)
      step3_final.json (nodes 已修正)
"""
import glob, json, os, re

REPO = "/home/ubuntu/framework-tree"
ROOT = os.path.join(REPO, "analysis/iwencai")

# 1. 重解析 decision 文件
# 兼容两种格式:
#   脚本初稿版: "- **指标名** 【标签】 描述"
#   子代理精修版: "1. **【标签】指标名** —— 描述"
IND_SCRIPT = re.compile(r"^- \*\*(.+?)\*\*", re.M)
IND_REFINED = re.compile(r"^\d+\. \*\*【[^】]*】(.+?)\*\*", re.M)

def clean_name(s):
    """去掉标签括号和尾部空描述, 返回纯指标名"""
    s = re.sub(r"【[^】]*】", "", s)
    s = re.sub(r"——.*$", "", s)
    return s.strip()

def norm_key(q):
    """指标名归一化: 去标签前缀/单位尾巴, 便于跨文件匹配"""
    s = re.sub(r"【[^】]*】", "", str(q)).strip()
    s = re.sub(r"——.*$", "", s).strip()
    s = re.sub(r"[（(][^）)]*[）)]\s*$", "", s).strip()
    return s

def parse_decision(path):
    """返回 (候选指标列表, 排除项列表)"""
    t = open(path, encoding="utf-8").read()
    parts = t.split("## 排除项")
    cand_sec = parts[0]
    excl_sec = parts[1] if len(parts) > 1 else ""
    # 先用脚本版正则, 若为0再用精修版
    cands_raw = IND_SCRIPT.findall(cand_sec)
    if not cands_raw:
        cands_raw = IND_REFINED.findall(cand_sec)
    excl_raw = IND_SCRIPT.findall(excl_sec) or IND_REFINED.findall(excl_sec)
    cands = [clean_name(m) for m in cands_raw if clean_name(m)]
    excl = [clean_name(m) for m in excl_raw if clean_name(m)]
    return cands, excl

result = {}
stats = []
for code in ["CU", "AL"]:
    result[code] = {}
    for f in sorted(glob.glob(os.path.join(REPO, f"analysis/iwencai/{code}/decision_*.md"))):
        node = re.search(r"decision_([\d.]+)\.md", f).group(1)
        cands, excl = parse_decision(f)
        result[code][node] = cands
        stats.append((code, node, len(cands), len(excl)))

json.dump(result, open("/tmp/decision_indicators_fixed.json", "w"),
          ensure_ascii=False, indent=1)

print("=== 节点解析结果(前12) ===")
for code, node, c, e in stats[:12]:
    print("  %s %s: 候选%d 排除%d" % (code, node, c, e))
print("...")
total_c = sum(s[2] for s in stats)
total_e = sum(s[3] for s in stats)
print("合计: 候选%d 排除%d" % (total_c, total_e))

# 2. patch step3_final.json 的 nodes
final = json.load(open(os.path.join(ROOT, "step3_final.json")))
patched = 0
for code in ["CU", "AL"]:
    node_map = result.get(code, {})
    # 建 指标名 -> [节点] 反向索引 (排除项不加); 同时存归一化键
    rev = {}
    rev_norm = {}
    for node, cands in node_map.items():
        for c in cands:
            rev.setdefault(c, []).append(node)
            rev_norm.setdefault(norm_key(c), []).append(node)
    for q, v in final[code].items():
        new_nodes = rev.get(q) or rev_norm.get(norm_key(q))
        if new_nodes and new_nodes != v.get("nodes"):
            v["nodes"] = new_nodes
            patched += 1
        elif not new_nodes and v.get("nodes") != ["00"]:
            v["nodes"] = ["00"]
            patched += 1

json.dump(final, open(os.path.join(ROOT, "step3_final.json"), "w"),
          ensure_ascii=False, indent=1)
print("\nstep3_final.json 修正 nodes 字段: %d 条" % patched)

# 3. 抽查修正效果
print("=== 抽查(CU 3.1.1 相关指标) ===")
for q, v in final["CU"].items():
    if "权益产量" in q or "矿山" in q:
        print("  %s -> nodes=%s tier=%s" % (q[:24], v["nodes"], v["tier"]))