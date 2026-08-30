#!/usr/bin/env python3
"""Step1 弹药准备：为 5 金属 × 30 节点生成 150 个「单节点 prompt」+ 驱动脚本用 manifest。

背景:
  ~/.hermes/scripts/iwencai_batch_driver.py 要求:
    · prompt 文件: analysis/iwencai/prompts/<VARIETY>_<node_code>.md (每节点一个, 单子类)
    · manifest: analysis/iwencai/<CODE>_manifest.json
                {generated, tasks:[{variety,dim,label,node_code,node_name,q}]}
  之前只有 CU/AL 的 60 个单节点 prompt。这里补齐 ZN/NI/SN/SI/LI 共 150 个。

维度→板块映射（板块8 供需平衡不做图表，跳过）：
  价格     2.1-2.6        供应 3.1.1-3.1.5,3.2.1-3.2.4
  库存     4.1-4.5        需求 5.1-5.3
  进出口   6.1-6.4        成本利润 7.1-7.3

产出:
  analysis/iwencai/prompts/{ZN,NI,SN,SI,LI}_<node_code>.md   150 份
  analysis/iwencai/{ZN,NI,SN,SI,LI}_manifest.json             5 份
  analysis/iwencai/5metals_step1_manifest.json                汇总（150 tasks）
"""
import json, os, subprocess, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PROMPT_LIB = BASE / "prompt_lib"
PROMPT_DIR = BASE / "analysis" / "iwencai" / "prompts"
PROMPT_DIR.mkdir(parents=True, exist_ok=True)

CODES = ["ZN", "NI", "SN", "SI", "LI"]

# 板块 → 维度映射
BOARD_DIM = {
    "2": "价格", "3": "供应", "4": "库存",
    "5": "需求", "6": "进出口", "7": "成本利润",
}


def render_single(dim, variety, node_code, node_name, out_path):
    """渲染单节点 prompt (subdirs 只含该节点)"""
    subdirs = f"{node_code}{node_name}"
    cmd = [sys.executable, str(PROMPT_LIB / "render_prompt.py"),
           "--dim", dim, "--variety", variety, "--subdirs", subdirs,
           "-o", str(out_path)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BASE), timeout=60)
    if r.returncode != 0:
        return False, r.stderr[:200]
    if not out_path.exists() or out_path.stat().st_size < 500:
        return False, "输出过小/不存在"
    return True, out_path.stat().st_size


def main():
    tree = json.load(open(BASE / "data" / "tree_config.json", encoding="utf-8"))
    # 建 节点编号 -> (维度, 名称, q, 板块label) 索引（取第一个匹配）
    node_idx = {}
    for cat in tree["categories"]:
        for c in cat["children"]:
            board = c["code"].split(".")[0]
            dim = BOARD_DIM.get(board)
            if not dim:
                continue  # 板块8 跳过
            node_idx[c["code"]] = {
                "dim": dim, "name": c["name"], "q": c.get("q", ""),
                "board": cat["label"],
            }

    total = ok = fail = 0
    all_tasks = []
    summary = {}
    for code in CODES:
        tasks = []
        code_ok = code_fail = 0
        for node_code, info in node_idx.items():
            total += 1
            out_path = PROMPT_DIR / f"{code}_{node_code}.md"
            good, info2 = render_single(info["dim"], code, node_code, info["name"], out_path)
            if good:
                ok += 1
                code_ok += 1
                size = info2
            else:
                fail += 1
                code_fail += 1
                print(f"  FAIL {code}_{node_code}.md: {info2}")
            tasks.append({
                "variety": code,
                "dim": info["dim"],
                "label": info["board"],
                "node_code": node_code,
                "node_name": info["name"],
                "q": info["q"],
                "status": "prompt_ready" if good else "prompt_failed",
                "prompt": f"prompts/{code}_{node_code}.md",
            })
        all_tasks.extend(tasks)
        summary[code] = {"ok": code_ok, "fail": code_fail}
        # 写单品种 manifest
        man_path = BASE / "analysis" / "iwencai" / f"{code}_manifest.json"
        man_path.write_text(json.dumps({
            "generated": "2026-08-30",
            "variety": code,
            "step": "step1_prompt_ready",
            "node_count": len(tasks),
            "tasks": tasks,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  {code}: {code_ok}/{len(tasks)} prompt 就绪, manifest -> {code}_manifest.json")

    # 写汇总 manifest（driver 的 --all 模式会读；格式对齐 CU_AL_manifest.json）
    agg_path = BASE / "analysis" / "iwencai" / "5metals_step1_manifest.json"
    agg_path.write_text(json.dumps({
        "generated": "2026-08-30",
        "step": "step1_prompt_ready",
        "note": "5金属(ZN/NI/SN/SI/LI)共150节点单节点prompt，供 iwencai_batch_driver.py 逐节点驱动",
        "summary": summary,
        "tasks": all_tasks,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n=== 完成: 成功 {ok}/{total} 单节点 prompt ===")
    print(f"    manifest -> {agg_path.name} (含 {len(all_tasks)} tasks)")


if __name__ == "__main__":
    main()