#!/usr/bin/env python3
"""Step3-5M: 从 decision_*.md 提取 指标清单 → /tmp/decision_indicators_5m.json

结构: {CODE: {node: [指标名, ...]}}
只取「直接相关」分节；排除区(## 排除项)之后的分节全部丢弃。
"""
import json, os, re, sys

ROOT = "/home/ubuntu/framework-tree/analysis/iwencai"
CODES = ["ZN", "NI", "SN", "SI", "LI"]
OUT = "/tmp/decision_indicators_5m.json"

# 品种中文词: 用于补全裸指标名 (发散输出常漏前缀, 如「持仓量（手）」应为「锌持仓量（手）」)
VAR_CN = {"ZN": "锌", "NI": "镍", "SN": "锡", "SI": "硅", "LI": "锂"}
# 已知品种词 (补全时判断是否已带前缀, 避免「镍镍持仓量」)
ALL_VAR_WORDS = ["锌", "镍", "锡", "硅", "锂", "锌锭", "镍生铁", "高冰镍",
                 "碳酸锂", "氢氧化锂", "金属硅", "工业硅", "多晶硅", "有机硅",
                 "硅铁", "电解镍", "精炼锡", "LME", "SHFE", "COMEX", "CFTC",
                 "USGS", "ILZSG", "SMM", "Copper", "Zinc", "Nickel", "Tin",
                 "Lithium", "Silicon", "Cobalt", "铝", "铜", "铅"]

def normalize(name, code):
    """给裸指标名补品种前缀: 「持仓量（手）」→「锌持仓量（手）」。
    已含任何品种词/交易所词/单位开头的不动, 避免「镍镍持仓量」。"""
    if any(w in name for w in ALL_VAR_WORDS):
        return name
    cn = VAR_CN[code]
    # 括号/单位开头的不补 (如「（元/吨）」单独出现)
    if name.startswith(("（", "(", "《")):
        return name
    # 数量词开头的也补 (最常见漏前缀场景)
    return cn + name


def parse(path, code):
    t = open(path, encoding="utf-8").read()
    # 只取「## 推荐图组合」之后的分节 (前面有「## 排除项」等噪声区)
    m = re.search(r"^##\s*推荐图组合.*$", t, flags=re.M)
    if m:
        t = t[m.end():]
    node = os.path.basename(path)[len("decision_"):-3]
    secs = re.split(r"^###\s+", t, flags=re.M)[1:]
    names = []
    for s in secs:
        head = s.strip().split("\n")[0].strip()
        # 取 - 指标：xxx、yyy
        m = re.search(r"^-\s*指标[：:]\s*(.+)$", s, flags=re.M)
        if not m:
            # 退路: 分节标题本身当指标名
            if head and not head.startswith(">"):
                names.append(head)
            continue
        raw = m.group(1).strip()
        # 只按「、」拆: 括号内常含 / , ， (如 元/吨、元,吨), 误拆会切碎单位
        for n in re.split(r"、", raw):
            n = re.sub(r"【[^】]*】", "", n).strip()
            n = re.sub(r"^[*-]\s*", "", n).strip()
            if len(n) >= 2 and not n.startswith("近"):  # 近3年同月均值 等衍生项不单独搜
                names.append(normalize(n, code))
    return node, names

def main():
    data = {}
    total_ind = 0
    total_node = 0
    for code in CODES:
        d = {}
        for f in sorted(os.listdir(os.path.join(ROOT, code))):
            if not re.match(r"^decision_.*\.md$", f):
                continue
            node, names = parse(os.path.join(ROOT, code, f), code)
            # 去重保序
            seen = set()
            names = [n for n in names if not (n in seen or seen.add(n))]
            if names:
                d[node] = names
                total_node += 1
                total_ind += len(names)
        data[code] = d
    json.dump(data, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("节点数:", total_node)
    print("指标名总数:", total_ind)
    for c in CODES:
        u = set()
        for ns in data[c].values():
            u.update(ns)
        print("  %s: %d 节点 / %d 唯一指标" % (c, len(data[c]), len(u)))
    print("->", OUT)

if __name__ == "__main__":
    main()
