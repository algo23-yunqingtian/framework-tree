#!/usr/bin/env python3
"""补齐 3 个维度词库（价格/进出口/成本利润）+ 渲染 5 金属 × 6 维度 = 30 份 prompt。

背景: prompt_lib/dimensions/ 原先只有 供应/库存/需求 3 个维度。
要做全 7 板块的 Step1 发散，需补齐 价格信号/进出口/成本利润 3 个维度，
使每个品种可按 6 维度 prompt 覆盖 2/3/4/5/6/7 板块（板块8供需平衡不做图表）。

产出:
  prompt_lib/dimensions/{价格,进出口,成本利润}.json
  pb_prompt/batch/<CODE>_<维度>_v19.md  (5金属 × 6维度 = 30 份)
  pb_prompt/batch/batch_manifest_5metals.json  (重生成, 含全维度)
"""
import json, os, subprocess, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PROMPT_LIB = BASE / "prompt_lib"
OUT_DIR = BASE / "pb_prompt" / "batch"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DIMS_DIR = PROMPT_LIB / "dimensions"

CODES = ["ZN", "NI", "SN", "SI", "LI"]

# 3 个新维度词库（结构对齐已有 供应/库存/需求）
NEW_DIMS = {
    "价格": {
        "dim": "价格",
        "meta": {"version": "1.0", "updated": "2026-08-30",
                 "source": "主脑补齐（Step1 发散前置，待首次实测校准）",
                 "usage": "render_prompt.py --dim 价格"},
        "positive_keywords": [
            "期货主力价/收盘价/结算价",
            "现货价(1#/A00)/升贴水/基差",
            "海外价(LME/COMEX/现金/3个月)/期限结构",
            "价差(月差/近远月/比价)/进出口比价",
            "估值分位/加工费/进口盈亏",
            "持仓量/成交量/前20会员多空中空/席位",
        ],
        "compound_themes": [
            "价+量+持仓三轴联动",
            "期现货基差双轴",
            "国内外价格+升贴水复合",
            "期限结构(Contango/Backwardation)叠加现货",
            "加工费+利润+比价三线对比",
        ],
        "usage_examples": [
            "判断盘面趋势与库存去化是否同步",
            "判断内外价差是否打开进口窗口",
            "判断期限结构是否反映现货紧张度",
            "判断主力多空持仓是否偏多/偏空",
        ],
        "boundary_tips": [
            "库存/仓单/社库/工厂库 —— 归库存维度",
            "产量/开工率/检修/进口量 —— 归供应或进出口维度",
            "冶炼成本/原料成本/能源成本 —— 归成本利润维度",
        ],
        "note": "价格维度正例词未经同花顺实测，首次使用后按返回校准回填本文件。",
    },
    "进出口": {
        "dim": "进出口",
        "meta": {"version": "1.0", "updated": "2026-08-30",
                 "source": "主脑补齐（Step1 发散前置，待首次实测校准）",
                 "usage": "render_prompt.py --dim 进出口"},
        "positive_keywords": [
            "原料进口量(精矿/矿石/废料)",
            "精炼金属进口量/出口量/净进口",
            "制品出口(HS编码)/分国别结构",
            "进口均价/出口金额",
            "海外对华发运/到港节奏/在途量",
            "分国别进口结构占比",
        ],
        "compound_themes": [
            "进口量+出口量+净进口三轴",
            "分国别进口结构占比",
            "发运-到港节奏对比",
            "进口均价+数量双轴",
        ],
        "usage_examples": [
            "判断贸易流是否顺差/逆差",
            "判断进口来源国结构变化",
            "判断海外发运节奏是否加快",
        ],
        "boundary_tips": [
            "期货价/现货价/升贴水 —— 归价格维度",
            "库存/仓单/社库 —— 归库存维度",
            "冶炼成本/原料成本 —— 归成本利润维度",
        ],
        "note": "进出口维度正例词未经同花顺实测，首次使用后按返回校准回填本文件。",
    },
    "成本利润": {
        "dim": "成本利润",
        "meta": {"version": "1.0", "updated": "2026-08-30",
                 "source": "主脑补齐（Step1 发散前置，待首次实测校准）",
                 "usage": "render_prompt.py --dim 成本利润"},
        "positive_keywords": [
            "冶炼成本/冶炼加工费/TC-RC",
            "原料成本(精矿/废料/氧化矿/云母)",
            "能源成本(电价/燃料/运输)",
            "副产品收益(硫酸/金/银/铋/硒)",
            "冶炼利润/再生利润/日度盈亏",
            "成本曲线/C1现金成本/分位",
        ],
        "compound_themes": [
            "成本曲线(原料+能源+加工费)堆叠",
            "日度利润+现金成本双轴",
            "副产品收益+冶炼利润对比",
            "分位/现金成本/完全成本三线",
        ],
        "usage_examples": [
            "判断冶炼端是否减产/停产",
            "判断再生/原生比价是否打开套利",
            "判断利润分位是否处于历史低位",
        ],
        "boundary_tips": [
            "期货价/现货价/升贴水 —— 归价格维度",
            "产量/开工率/检修 —— 归供应维度",
            "库存/仓单/社库 —— 归库存维度",
        ],
        "note": "成本利润维度正例词未经同花顺实测，首次使用后按返回校准回填本文件。",
    },
}

SUBDIRS = {
    "价格": "2.1盘面结构|2.2现货与升贴水|2.3海外价格|2.4价差体系|2.5估值与利润|2.6持仓席位观察",
    "供应": "3.1.1海外矿·财报产量|3.1.2海外矿·分国别总量|3.1.3国内矿产量|3.1.4矿进口量与分国别|3.1.5TC加工费|3.2.1精炼产量|3.2.2开工率与检修|3.2.3再生·二次供应|3.2.4冶炼利润→供应弹性",
    "库存": "4.1交易所库存|4.2仓单|4.3社会库存|4.4工厂库存|4.5隐性·在途库存",
    "需求": "5.1初级消费|5.2终端细分消费|5.3需求先行指标",
    "进出口": "6.1原料进口|6.2精炼金属进出口|6.3制品出口|6.4海外对华发运",
    "成本利润": "7.1成本曲线与分位|7.2日度利润测算|7.3能源·原料成本",
}


def main():
    # 1. 补齐维度词库（已存在则跳过）
    print("=== 补齐维度词库 ===")
    for dim, data in NEW_DIMS.items():
        p = DIMS_DIR / f"{dim}.json"
        if p.exists():
            print(f"  {p.name} 已存在，跳过")
        else:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
            print(f"  维度词库已创建: {p.name}")

    # 2. 渲染 5 金属 × 6 维度 = 30 份 prompt
    print("\n=== 渲染 v19 prompt (5金属 × 6维度) ===")
    ok = fail = 0
    manifest = []
    for code in CODES:
        for dim, subdirs in SUBDIRS.items():
            out_name = f"{code}_{dim}_v19.md"
            out_path = OUT_DIR / out_name
            cmd = [sys.executable, str(PROMPT_LIB / "render_prompt.py"),
                   "--dim", dim, "--variety", code, "--subdirs", subdirs,
                   "-o", str(out_path)]
            r = subprocess.run(cmd, capture_output=True, text=True,
                               cwd=str(BASE), timeout=60)
            if r.returncode != 0 or not out_path.exists() or out_path.stat().st_size < 200:
                print(f"  {out_name}: FAIL")
                fail += 1
            else:
                print(f"  {out_name}: OK {out_path.stat().st_size} bytes")
                ok += 1
            manifest.append({"variety": code, "dim": dim, "file": out_name,
                             "subdirs": subdirs.split("|")})

    # 3. 重生成 manifest（覆盖全维度）
    man_path = OUT_DIR / "batch_manifest_5metals.json"
    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n=== 完成: 成功 {ok} 失败 {fail} 份 prompt + manifest -> {man_path.name} ===")
    print(f"=== 待发散节点总数: {sum(len(m['subdirs']) for m in manifest)} ===")


if __name__ == "__main__":
    main()