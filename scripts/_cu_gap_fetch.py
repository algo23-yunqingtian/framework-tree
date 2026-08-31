#!/usr/bin/env python3
"""拉取知几数据并写入 api_cache.db（铜缺口节点专用）"""
import json, os, sqlite3, sys, subprocess, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "scripts", "api_cache.db")
ZHIFI_API = os.path.expanduser("~/.hermes/scripts/zhiji_api.py")

# (metric_key, zhiji_id, name, unit, freq)
TARGETS = [
    ("cu_44_smelter_stock", "a10001152", "SMM 冶炼厂电解铜库存", "吨", "月"),
    ("cu_44_anode_days", "a12854090", "SMM 阳极铜库存天数", "天", "月"),
    ("cu_45_intransit", "a12839473", "SMM 冶炼厂电解铜在途库存", "吨", "周"),
    ("cu_45_total_est", "a10001154", "SMM 估计电解铜库存总数", "吨", "月"),
    ("cu_72_smm_profit", "j02870870", "SMM 中国铜冶炼厂现货冶炼利润", "元/金属吨", "日"),
    ("cu_72_smelt_cost", "a12855622", "SMM 铜冶炼厂冶炼成本", "元/金属吨", "月"),
    ("cu_73_imp_cost", "a12819794", "中国海关 电解铜出口原料进口成本", "元/吨", "日"),
]

def fetch_series(zhiji_id, start="2015-01-01", end="2026-08-31"):
    """调用 zhiji_api.py series 获取数据。"""
    cmd = [sys.executable, ZHIFI_API, "series", zhiji_id, start, end]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"  ERROR: {result.stderr[:200]}")
            return None
        data = json.loads(result.stdout)
        return data
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

def save_to_db(metric_key, zhiji_id, name, unit, freq, data):
    """保存数据到 api_cache.db。"""
    if not data or "points" not in data:
        return False
    points = data["points"]
    if not points:
        return False
    
    # 转换为 [{"date":..., "value":...}] 格式
    data_list = [{"date": p["date"], "value": p["value"]} for p in points]
    data_json = json.dumps(data_list, ensure_ascii=False)
    now = datetime.datetime.now().isoformat()
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 删除旧记录（如果有）
    c.execute("DELETE FROM indicator_cache WHERE metric=? AND code=?", (metric_key, "CU"))
    c.execute(
        "INSERT INTO indicator_cache (code, metric, zhiji_id, data_json, fetched_at, name, unit, freq) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("CU", metric_key, zhiji_id, data_json, now, name, unit, freq)
    )
    conn.commit()
    n = len(data_list)
    conn.close()
    return n

def main():
    print("=" * 60)
    print("拉取知几数据并写入 api_cache.db")
    print("=" * 60)
    for mid, zid, name, unit, freq in TARGETS:
        print(f"\n  {mid} ({zid})...")
        data = fetch_series(zid)
        if not data:
            print(f"    FAIL: 无数据")
            continue
        n = save_to_db(mid, zid, name, unit, freq, data)
        if n:
            print(f"    OK: {n} points saved")
        else:
            print(f"    FAIL: 保存失败")
    
    # 验证
    print("\n" + "=" * 60)
    print("验证入库结果")
    print("=" * 60)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for mid, zid, name, unit, freq in TARGETS:
        row = c.execute(
            "SELECT metric, code, zhiji_id, name, unit, freq, length(data_json) FROM indicator_cache WHERE metric=? AND code=?",
            (mid, "CU")
        ).fetchone()
        if row:
            print(f"  ✅ {mid}: {row[3]} ({row[5]}, json_len={row[6]})")
        else:
            print(f"  ❌ {mid}: NOT FOUND")
    conn.close()

if __name__ == "__main__":
    main()
