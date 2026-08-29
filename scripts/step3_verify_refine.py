#!/usr/bin/env python3
"""Step3 精修: 对 CU 首次搜索不确定的指标, 用更精确关键词重查。
策略: 预置关键词映射 + 自动变体 (加"铜"/"电解铜"/英文), 全部记录。
"""
import json, os, subprocess, sys, time, re

ROOT = "/home/ubuntu/framework-tree/analysis/iwencai"
OUT = os.path.join(ROOT, "step3_search_refine.json")

# 精确关键词映射 (指标名 -> [候选关键词])
KEYWORDS = {
    "进口盈亏（元/吨）": ["电解铜进口盈亏", "铜 进口盈亏 日度"],
    "沪伦比（元/吨 ÷ 美元/吨）": ["沪伦比 铜", "铜 沪伦比"],
    "人民币兑美元中间价": ["美元兑人民币 中间价", "USDCNY 中间价"],
    "LME 0-3 升贴水（美元/吨）": ["LME 铜 0-3", "LME铜 现货 3个月"],
    "美元兑相关货币汇率": ["美元指数 日度", "美元指数"],
    "各合约成交量与持仓量": ["沪铜 成交量 持仓量", "SHFE 铜 成交量"],
    "全球铜矿C1现金成本": ["铜矿 C1 成本", "C1现金成本 铜"],
    "中国铜冶炼现金成本": ["铜冶炼 成本", "电解铜 冶炼 成本"],
    "硫磺价格": ["硫磺 价格 日度", "硫磺 中国"],
    "沪铜主力合约前20多单持仓量": ["SHFE 铜 前20 多单", "铜 会员持仓 前20"],
    "沪铜主力合约前20空单持仓量": ["SHFE 铜 前20 空单", "铜 空头 前20"],
    "前20名多头持仓集中度": ["铜 多单集中度", "铜 前20 集中度"],
    "前20名空头持仓集中度": ["铜 空单集中度", "铜 空头 集中度"],
    "前5名多头持仓量": ["铜 前5 多单", "铜 前五 持仓"],
    "前5名空头持仓量": ["铜 前5 空单", "铜 前五 空头"],
    "席位方向性净持仓": ["铜 净持仓", "铜 席位 净多"],
    "CFTC商业多头/商业空头/非商业净多持仓": ["CFTC 铜 持仓", "COMEX 铜 非商业"],
    "持仓成员类型结构": ["铜 持仓 结构", "铜 会员 持仓"],
    "前20席位成交活跃度": ["铜 席位 成交", "SHFE 铜 成交排名"],
    "权益产量": ["铜矿 权益产量", "铜 权益 产量"],
    "矿山可采储量": ["铜 可采储量", "铜矿 储量"],
    "矿山剩余开采年限": ["铜矿 开采年限", "铜 矿山 寿命"],
    "矿山现金成本与AIPC": ["铜矿 AIPC", "铜 矿山 现金成本"],
    "主要矿山项目产量": ["铜矿 项目 产量", "铜 矿山 产量"],
    "矿石入选品位": ["铜 入选品位", "铜矿 品位"],
    "中国废铜投料量": ["废铜 投料", "废铜 使用量"],
    "中国进口阴极铜量": ["阴极铜 进口", "电解铜 进口 中国"],
    "冶炼厂开工率/产能利用率": ["铜冶炼 开工率", "电解铜 开工率"],
    "中国电解铜冶炼厂开工率": ["电解铜 冶炼 开工率", "铜 冶炼 产能利用率"],
    "冶炼厂检修影响量": ["铜冶炼 检修", "电解铜 检修 影响"],
    "因原料问题导致的产量减量": ["铜 产量 减量", "铜 减产"],
    "计划外停产/降负荷冶炼厂数量": ["铜冶炼 停产", "铜 计划外 检修"],
    "粗铜/阳极铜开工率": ["粗铜 开工率", "阳极铜 开工率"],
    "电解铜实际产量": ["电解铜 产量 月", "SMM 电解铜 产量"],
    "废产阳极板供应量": ["阳极板 铜", "铜 阳极板 产量"],
    "国内废铜回收量": ["废铜 回收", "中国 废铜 回收量"],
    "再生铜企业开工率": ["再生铜 开工率", "再生铜 企业 开工"],
    "再生铜杆开工率": ["再生铜杆 开工率", "再生铜杆 开工"],
    "硫酸出厂价": ["硫酸 出厂价", "硫酸 价格 中国"],
    "冶炼厂单位现金加工成本": ["铜 加工成本", "铜 冶炼 成本 现金"],
    "计划外减产冶炼厂数量": ["铜 减产 冶炼厂", "铜 停产 数量"],
}

def clean(name):
    return re.sub(r"【[^】]*】", "", name).strip()

def main():
    cu = json.load(open(os.path.join(ROOT, "step3_search_results.json")))["CU"]
    refine = {}
    if os.path.exists(OUT):
        refine = json.load(open(OUT))
    refine.setdefault("CU", {})

    done = set(refine["CU"].keys())
    todo = [q for q in KEYWORDS if q not in done]
    # 顺带处理脚本噪声标记: 记录为 SKIP
    refine["CU"]["正主/辅助/排除项需 agent 知几验证时人工确认"] = {"skip": "脚本噪声, 非指标"}

    print(f"待精修: {len(todo)}")
    for i, q in enumerate(todo, 1):
        kws = KEYWORDS[q]
        entry = {"orig": q, "nodes": cu.get(q, {}).get("nodes", []), "attempts": []}
        for kw in kws:
            try:
                r = subprocess.run(
                    [sys.executable, os.path.expanduser("~/.hermes/scripts/zhiji_api.py"),
                     "search", kw],
                    capture_output=True, text=True, timeout=60)
                j = json.loads(r.stdout.strip() or '{"results":[]}')
                hits = j.get("results", [])[:3]
                entry["attempts"].append({
                    "kw": kw, "count": j.get("count"),
                    "hits": [{"id": h.get("id"), "name": h.get("name"),
                              "source": h.get("source"), "unit": h.get("unit")}
                             for h in hits]
                })
                # 若已有含铜命中, 不再试后续关键词
                if any("铜" in h.get("name", "") or "Copper" in h.get("name", "") or
                       "CU" in (h.get("id") or "").upper()
                       for h in hits):
                    break
            except Exception as e:
                entry["attempts"].append({"kw": kw, "error": str(e)})
            time.sleep(1.2)
        refine["CU"][q] = entry
        if i % 5 == 0 or i == len(todo):
            json.dump(refine, open(OUT, "w"), ensure_ascii=False, indent=1)
            print(f"{i}/{len(todo)}")
    json.dump(refine, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("精修完成")

if __name__ == "__main__":
    main()