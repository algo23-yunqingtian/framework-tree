#!/usr/bin/env python3
"""Step1 弹药最终适配：把驱动脚本纳入 repo + manifest 转英文 dim。

问题（实测 ~/.hermes/scripts/iwencai_batch_driver.py 的 3 处硬编码）:
  1. var_cn_map 只有 {CU,AL,PB,ZN,NI} → 缺 SN/SI/LI
  2. MANIFEST 硬编码 CU_AL_manifest.json → 新 5 金属 manifest 读不到
  3. task["dim"] 期望英文值 (price/supply/inventory/demand/trade/cost)
     而我生成的 manifest 写的是中文 dim → 正例关键词 POS 查不到

另外 ~/.hermes/scripts/ 不在 git 里，跨服务器 agent 拿不到驱动脚本。
解决: 把驱动脚本复制到 repo (scripts/iwencai_batch_driver.py) 并打补丁，
agent 通过 git 就能拿到可运行的驱动。

产出:
  scripts/iwencai_batch_driver.py          (补丁版, 支持 --manifest/--code)
  analysis/iwencai/5metals_step1_manifest.json  (dim 改英文值)
  analysis/iwencai/<CODE>_manifest.json   (dim 改英文值)
"""
import json, os, shutil, re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = Path.home() / ".hermes" / "scripts" / "iwencai_batch_driver.py"
DST = BASE / "scripts" / "iwencai_batch_driver.py"

# 中文 dim → 驱动脚本期望的英文 dim
DIM_EN = {
    "价格": "price", "价格信号": "price",
    "供应": "supply", "供给": "supply",
    "库存": "inventory",
    "需求": "demand",
    "进出口": "trade",
    "成本利润": "cost", "成本·利润": "cost",
}
# 驱动脚本的 var_cn_map 完整版
VAR_CN = {"CU": "铜", "AL": "铝", "PB": "铅", "ZN": "锌",
          "NI": "镍", "SN": "锡", "SI": "硅", "LI": "锂",
          "LC": "碳酸锂", "FE": "铁矿石"}
# 驱动脚本的 label 映射（英文 dim → 中文 label）
LABEL_CN = {"price": "价格信号", "supply": "供给", "inventory": "库存",
            "demand": "需求", "trade": "进出口", "cost": "成本·利润"}


def patch_driver():
    """复制驱动脚本到 repo 并打补丁"""
    if not SRC.exists():
        print(f"  ⚠ 源脚本不存在: {SRC}")
        return False
    txt = SRC.read_text(encoding="utf-8")
    orig = txt

    # 补丁1: var_cn_map 扩展为全品种
    txt = re.sub(
        r'var_cn_map = \{[^}]*\}',
        f'var_cn_map = {json.dumps(VAR_CN, ensure_ascii=False)}',
        txt, count=1)

    # 补丁2: MANIFEST 支持 --manifest 参数（默认仍用 CU_AL）
    txt = txt.replace(
        'ap.add_argument("--end", type=int)',
        'ap.add_argument("--end", type=int)\n'
        '    ap.add_argument("--manifest", default=None, help="manifest 路径, 默认 CU_AL_manifest.json")')
    txt = txt.replace(
        '        man = json.load(open(MANIFEST))',
        '        mp = args.manifest or MANIFEST\n'
        '        man = json.load(open(mp))')

    # 补丁3: state 文件按 manifest 区分，避免和 CU_AL 状态冲突
    txt = txt.replace(
        '    state = json.load(open(STATE)) if os.path.exists(STATE) else {"done": {}}',
        '    mtag = os.path.basename(args.manifest or "CU_AL_manifest.json").replace("_manifest", "").replace(".json", "")\n'
        '    S = STATE.replace("_driver_state", f"_driver_state_{mtag}")\n'
        '    state = json.load(open(S)) if os.path.exists(S) else {"done": {}}')
    txt = txt.replace(
        'json.dump(state, open(STATE, "w"), ensure_ascii=False, indent=1)',
        'json.dump(state, open(S, "w"), ensure_ascii=False, indent=1)')

    # 补丁4: 输出路径 BASE 改成 repo 自适应（原脚本硬编码 /home/ubuntu/framework-tree）
    txt = txt.replace(
        'BASE = "/home/ubuntu/framework-tree"',
        'BASE = os.environ.get("FRAMEWORK_TREE", "/home/ubuntu/framework-tree")')

    if txt == orig:
        print("  ⚠ 未做任何补丁（正则未匹配），原样复制")
    DST.write_text(txt, encoding="utf-8")
    print(f"  驱动脚本已纳入 repo: {DST.name} ({len(txt)} bytes)")
    return True


def fix_manifests():
    """把 manifest 的 dim 从中文转成英文"""
    fixes = []
    # 汇总 manifest
    agg = BASE / "analysis" / "iwencai" / "5metals_step1_manifest.json"
    if agg.exists():
        d = json.loads(agg.read_text(encoding="utf-8"))
        n = 0
        for t in d.get("tasks", []):
            en = DIM_EN.get(t.get("dim"))
            if en:
                t["dim"] = en
                t["label"] = LABEL_CN.get(en, t.get("label"))
                n += 1
        agg.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        fixes.append(f"{agg.name}: {n} tasks dim→英文")
    # 单品种 manifest
    for code in ["ZN", "NI", "SN", "SI", "LI"]:
        p = BASE / "analysis" / "iwencai" / f"{code}_manifest.json"
        if not p.exists():
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        n = 0
        for t in d.get("tasks", []):
            en = DIM_EN.get(t.get("dim"))
            if en:
                t["dim"] = en
                t["label"] = LABEL_CN.get(en, t.get("label"))
                n += 1
        p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        fixes.append(f"{p.name}: {n} tasks dim→英文")
    return fixes


def main():
    print("=== 1. 驱动脚本纳入 repo (打补丁) ===")
    patch_driver()
    print("\n=== 2. manifest dim 转英文 ===")
    for f in fix_manifests():
        print(f"  {f}")

    # 验证
    print("\n=== 3. 验证 ===")
    agg = BASE / "analysis" / "iwencai" / "5metals_step1_manifest.json"
    d = json.loads(agg.read_text(encoding="utf-8"))
    from collections import Counter
    c = Counter(t["dim"] for t in d["tasks"])
    print(f"  manifest tasks: {len(d['tasks'])}, dim 分布: {dict(c)}")
    cn = [t["variety"] for t in d["tasks"] if t["variety"] not in VAR_CN]
    print(f"  未在 var_cn_map 的品种: {set(cn) or '无'}")
    # 抽查一个
    t0 = d["tasks"][0]
    print(f"  样例 task[0]: {json.dumps(t0, ensure_ascii=False)}")
    print("\n=== 完成 ===")


if __name__ == "__main__":
    main()