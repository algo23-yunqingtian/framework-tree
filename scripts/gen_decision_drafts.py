#!/usr/bin/env python3
"""批量从同花顺发散记录生成 Step2 decision 初稿（脚本抽取，非 LLM）。

读 analysis/iwencai/{CU,AL}/divergence_<节点>.md 的结构化表格：
  表1「独立基础指标枚举」：序号|基础指标|直接含义|归属判断
  表2「核心图表设计方案」：序号|图名称|包含指标|题材归属度|数据源|形态|观测用途
输出 decision_<节点>.md 初稿：候选指标清单 + 推荐图组合。
正主/辅助标注与排除项留待 agent 知几验证时人工确认（初稿里标记【待核】）。
"""
import glob, os, re, sys

ROOT = "/home/ubuntu/framework-tree/analysis/iwencai"

def split_row(row):
    """兼容 tab 与 | 分隔（| 分隔时去掉首尾|）。"""
    r = row.strip()
    if r.startswith("|") and r.endswith("|"):
        return [c.strip() for c in r[1:-1].split("|")]
    if "\t" in r:
        return [c.strip() for c in r.split("\t")]
    return [c.strip() for c in r.split("|")]

def parse(filepath):
    lines = open(filepath, encoding="utf-8").read().split("\n")
    mode = None          # 'ind' 指标枚举表 / 'chart' 图表方案表
    ind_rows, chart_rows = [], []
    header_seen = {}
    for ln in lines:
        s = ln.strip()
        # 切换表模式
        if s.startswith("1. 独立基础指标枚举") or s.startswith("1.独立基础指标枚举"):
            mode = "ind"; header_seen['ind']=False; continue
        if re.match(r"2\.\s*核心图表设计", s) or "核心图表设计方案" in s or ("图名称" in s and s.startswith("序号")):
            # 可能是图表表的表头行，先判表头
            if "图名称" in s:
                mode = "chart"; header_seen['chart']=True; continue
            mode = "chart"; header_seen['chart']=False; continue
        if "本子类共" in s or "本维度" in s:
            mode = None; continue
        # 指标枚举表表头
        if mode == "ind" and not header_seen['ind'] and re.search(r"基础指标", s):
            header_seen['ind'] = True
            continue
        # 图表表表头（独立行 "序号\t图名称..." 或 "| 序号 | 图名称 |")
        if mode == "chart" and not header_seen['chart'] and "图名称" in s:
            header_seen['chart'] = True
            continue
        if mode == "ind" and header_seen['ind'] and re.match(r"^\d+[\t|]", s):
            cells = split_row(s)
            if len(cells) >= 3:
                ind_rows.append(cells)
        if mode == "chart" and header_seen['chart'] and re.match(r"^\d+[\t|]", s):
            cells = split_row(s)
            if len(cells) >= 3:
                chart_rows.append(cells)
    return ind_rows, chart_rows

def make_decision(code, node, title, ind_rows, chart_rows):
    out = [f"# {code}·{node} {title} Step2 候选（脚本抽取初稿）", ""]
    out.append("> ⚠️ 本文件由脚本从发散记录自动抽取，**正主/辅助/排除项需 agent 知几验证时人工确认**。")
    out.append("> 抽取来源：发散记录的「独立基础指标枚举」表 +「核心图表设计方案」表。")
    out.append("")
    out.append("## 候选指标（来自枚举表，含原始归属判断）")
    out.append("")
    if not ind_rows:
        out.append("（枚举表未解析到，需人工回看发散记录）")
    for r in ind_rows:
        name = r[1] if len(r) > 1 else ""
        desc = r[2] if len(r) > 2 else ""
        belong = r[3] if len(r) > 3 else ""
        tail = f"【{belong}】" if belong else ""
        out.append(f"- **{name}** {tail} {desc}")
    out.append("")
    # 自动提取排除项（归属判断含“更相关/应归属”的指标）
    excl = [r for r in ind_rows if len(r) > 3 and ("更相关" in r[3] or "应归属" in r[3] or "不属" in r[3])]
    if excl:
        out.append("## 排除项（脚本自动标记：发散记录归属判断指向其他环节）")
        out.append("")
        for r in excl:
            out.append(f"- **{r[1]}** —— {r[3]}（{r[2]}）")
        out.append("")
    else:
        out.append("## 排除项")
        out.append("")
        out.append("（无自动标记，需 agent 知几验证时人工核对跨类指标）")
        out.append("")
    out.append("## 推荐图组合（来自图表方案表）")
    out.append("")
    if not chart_rows:
        out.append("（图表表未解析到，需人工回看发散记录）")
    for r in chart_rows:
        fig = r[1] if len(r) > 1 else ""
        inds = r[2] if len(r) > 2 else ""
        grade = r[3] if len(r) > 3 else ""
        use = r[6] if len(r) > 6 else ""
        src = r[4] if len(r) > 4 else ""
        out.append(f"### {fig}")
        out.append(f"- 指标：{inds}")
        out.append(f"- 归属度：{grade}")
        out.append(f"- 数据源：{src}")
        out.append(f"- 观测用途：{use}")
        out.append("")
    return "\n".join(out)

def main():
    code = sys.argv[1] if len(sys.argv) > 1 else "all"
    codes = ["CU", "AL"] if code == "all" else [code]
    total = 0
    for c in codes:
        files = sorted(glob.glob(os.path.join(ROOT, c, "divergence_*.md")))
        for f in files:
            base = os.path.basename(f)
            m = re.match(r"divergence_(.+)\.md$", base)
            if not m:
                continue
            node = m.group(1)
            ind_rows, chart_rows = parse(f)
            # 标题：从文件第一行 # CU·xx·节点 提取
            title = ""
            with open(f, encoding="utf-8") as fh:
                first = fh.readline().strip()
            if first.startswith("# "):
                title = first[2:].split(" ")[-1] if "·" in first else ""
            outfile = os.path.join(ROOT, c, f"decision_{node}.md")
            content = make_decision(c, node, title, ind_rows, chart_rows)
            # 不覆盖已经由子代理写好的精细版（含「正主」字样的一般是人工版）
            if os.path.exists(outfile):
                exist = open(outfile, encoding="utf-8").read()
                if "正主" in exist and "脚本抽取" not in exist:
                    print(f"SKIP {c}/{node} (已有精修版)")
                    continue
            open(outfile, "w", encoding="utf-8").write(content)
            total += 1
            print(f"OK {c}/{node} ind={len(ind_rows)} chart={len(chart_rows)}")
    print(f"\n完成，共生成/更新 {total} 份")

if __name__ == "__main__":
    main()