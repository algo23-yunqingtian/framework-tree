#!/usr/bin/env python3
"""
指标树数据层 — SQLite 存储 + Zhiji 增量拉取

架构：
  Zhiji API ──(每日增量)──→ indicators.db (SQLite) ──(页面访问)──→ ECharts 渲染
  首次全量拉取 → 每天 cron 增量 → 看板永远读本地，不消耗配额

用法：
  python data_layer.py full    首次全量拉取所有品种所有指标
  python data_layer.py inc     每日增量更新（cron用）
  python data_layer.py status  查看各指标数据量
  python data_layer.py query ZN 社库    查询单指标数据（供看板调用）
"""
import sqlite3, json, os, sys, subprocess
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "indicators.db"
ZHJI = os.path.expanduser("~/.hermes/scripts/zhiji_api.py")

# ============================================================
# 指标 ID 映射表（后续与同花顺确认后扩充/修正）
# code: 品种, metric: 指标编码, zhiji_id: Zhiji指标ID
# ============================================================
INDICATORS = {
    # 通用价格（各品种复用）
    "主连": {"name": "期货主连结算价", "freq": "daily", "sources": {
        "CU": "FU00014941", "AL": "FU00014934", "PB": "FU00014946",
        "ZN": "FU00014950", "NI": "FU00014982", "SN": "FU00014952",
        "SI": "FU00015015", "LC": "FU00015030"
    }},
    "LME库存": {"name": "LME库存", "freq": "daily", "sources": {
        "CU": "FU00014813", "ZN": "FU00014815", "AL": "FU00014812",
        "PB": "FU00014814", "NI": "FU00014816", "SN": "FU00014817"
    }},
    "仓单": {"name": "LME注册仓单", "freq": "daily", "sources": {
        "CU": "FU00014818", "ZN": "FU00014820", "NI": "FU00014818"
    }},
    "SHFE库存": {"name": "上期所库存", "freq": "daily", "sources": {
        "CU": "FU00014935", "AL": "FU00014930", "PB": "FU00014943",
        "ZN": "FU00014947", "NI": "FU00014980", "SN": "FU00014953",
        "SI": "FU00015013", "LC": "FU00015028"
    }},
    "社库": {"name": "社会库存", "freq": "weekly", "sources": {
        "ZN": "ID01000170", "AL": "ID01000160", "CU": "ID01000150",
        "NI": "ID01001673", "SN": "ID01001700", "PB": "ID01000180",
        "SI": "ID01002100", "LC": "ID01002500"
    }},
    "TC": {"name": "TC加工费", "freq": "weekly", "sources": {
        "ZN": "ID01000200", "CU": "ID01000120", "NI": "ID01002200",
        "SN": "ID01001800", "PB": "ID01000190"
    }},
    "精炼产量": {"name": "精炼产量", "freq": "monthly", "sources": {
        "ZN": "ID01000210", "AL": "ID01000170", "CU": "ID01000130",
        "NI": "ID01002085", "SN": "ID01001750", "PB": "ID01000185",
        "SI": "ID01002150", "LC": "ID01002400"
    }},
    "表观消费": {"name": "表观消费", "freq": "monthly", "sources": {
        "ZN": "ID01000220", "AL": "ID01000175", "CU": "ID01000135",
        "NI": "ID01001570", "SN": "ID01001760", "PB": "ID01000195"
    }},
    "开工率": {"name": "冶炼开工率", "freq": "monthly", "sources": {
        "ZN": "ID01000230", "CU": "ID01000140", "NI": "ID01002084",
        "AL": "ID01000165", "SN": "ID01001770", "PB": "ID01000188"
    }},
}

# 注意：上面 ID 是占位符，正式使用前必须 search→series 逐一验证


def db_connect():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS indicator_series (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,           -- 品种 CU/ZN...
            metric TEXT NOT NULL,         -- 指标名 社库/TC...
            zhiji_id TEXT,                -- Zhiji 原始ID
            date TEXT NOT NULL,           -- YYYY-MM-DD
            value REAL,                   -- 数值
            freq TEXT,                    -- daily/weekly/monthly
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(code, metric, date)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_code_metric ON indicator_series(code, metric)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON indicator_series(date)")
    conn.commit()
    return conn


def zhiji_series(zhiji_id, start, end):
    """调一次 Zhiji API 取时序"""
    cmd = [sys.executable, ZHJI, "series", zhiji_id, start, end]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return []
    try:
        data = json.loads(r.stdout)
        return data.get("points", [])
    except (json.JSONDecodeError, TypeError):
        return []


def full_pull(code=None, metrics=None):
    """首次全量拉取：所有品种所有指标 3年历史"""
    conn = db_connect()
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=1095)).strftime("%Y-%m-%d")

    codes = [code] if code else ["CU", "AL", "PB", "ZN", "NI", "SN", "LC", "SI"]
    metric_list = metrics or list(INDICATORS.keys())

    total = 0
    for metric_name in metric_list:
        meta = INDICATORS[metric_name]
        for c in codes:
            zhiji_id = meta["sources"].get(c)
            if not zhiji_id:
                continue
            points = zhiji_series(zhiji_id, start, end)
            if not points:
                print(f"  ⚠ {c}/{metric_name} 无数据（ID {zhiji_id} 可能无效）")
                continue
            for p in points:
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO indicator_series(code, metric, zhiji_id, date, value, freq)
                        VALUES (?,?,?,?,?,?)
                    """, (c, metric_name, zhiji_id, p["date"], p["value"], meta["freq"]))
                    total += 1
                except Exception as e:
                    pass
            print(f"  ✓ {c}/{metric_name}: {len(points)} 点")
    conn.commit()
    conn.close()
    print(f"\n✅ 全量拉取完成，共写入 {total} 条记录 → {DB_PATH}")
    return total


def incremental_pull():
    """每日增量：只拉今天的数据"""
    conn = db_connect()
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    for metric_name, meta in INDICATORS.items():
        for code, zhiji_id in meta["sources"].items():
            # 只看最近3天（覆盖周末/节假日）
            points = zhiji_series(zhiji_id, yesterday, today)
            for p in points:
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO indicator_series(code, metric, zhiji_id, date, value, freq)
                        VALUES (?,?,?,?,?,?)
                    """, (code, metric_name, zhiji_id, p["date"], p["value"], meta["freq"]))
                except:
                    pass
    conn.commit()
    conn.close()
    print(f"✅ 增量更新完成 ({today})")


def query(code, metric, limit=120):
    """查询单指标数据（供看板 API 调用）"""
    conn = db_connect()
    rows = conn.execute("""
        SELECT date, value FROM indicator_series
        WHERE code=? AND metric=? AND value IS NOT NULL
        ORDER BY date DESC LIMIT ?
    """, (code, metric, limit)).fetchall()
    conn.close()
    return [{"date": r[0], "value": r[1]} for r in reversed(rows)]


def status():
    """显示各指标数据量"""
    conn = db_connect()
    rows = conn.execute("""
        SELECT code, metric, freq, COUNT(*) as cnt,
               MIN(date) as first_date, MAX(date) as last_date
        FROM indicator_series WHERE value IS NOT NULL
        GROUP BY code, metric, freq ORDER BY code, metric
    """).fetchall()
    conn.close()
    if not rows:
        print("⚠️ 数据库为空，先运行: python data_layer.py full")
        return
    print(f"{'品种':<4} {'指标':<10} {'频率':<8} {'记录数':>6}  {'起始':<12} {'最新':<12}")
    print("-" * 60)
    for r in rows:
        print(f"{r[0]:<4} {r[1]:<10} {r[2]:<8} {r[3]:>6}  {r[4]:<12} {r[5]:<12}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "full":
        full_pull()
    elif cmd == "inc":
        incremental_pull()
    elif cmd == "status":
        status()
    elif cmd == "query":
        code, metric = sys.argv[2], sys.argv[3]
        data = query(code, metric)
        print(json.dumps(data, ensure_ascii=False))
    else:
        print(f"未知命令: {cmd}")