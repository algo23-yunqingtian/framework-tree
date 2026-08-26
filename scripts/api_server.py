#!/usr/bin/env python3
"""
framework-tree 数据 API 服务器
===============================
机制：实时调用 + 3天滑动缓存
  - 首次请求某指标 → 调 Zhiji API → 存缓存 → 返回
  - 3天内重复请求 → 直接返缓存（重置3天计时器）
  - 超过3天 → 重新调 Zhiji → 更新缓存

端口：8786（本地）
接口：GET /api/indicator?code=ZN&metric=社库
返回：{"points":[{"date":"2026-01-01","value":123.45},...],"meta":{...}}
"""
import json, os, sys, subprocess, sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

ZHJI = os.path.expanduser("~/.hermes/scripts/zhiji_api.py")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_cache.db")
CACHE_DAYS = 3  # 滑动缓存窗口（天）

# ===== 指标 ID 映射（品种代码 × 指标名 → Zhiji ID）=====
# ⚠️ 注意：以下是占位 ID，正式使用前必须 search→series 逐一验证
INDICATOR_IDS = {
    # 通用价格
    "主连": {"CU":"FU00014941","AL":"FU00014934","PB":"FU00014946","ZN":"FU00014950",
             "NI":"FU00014982","SN":"FU00014952","SI":"FU00015015","LC":"FU00015030","freq":"daily"},
    "LME库存": {"CU":"FU00014813","AL":"FU00014812","PB":"FU00014814","ZN":"FU00014815",
               "NI":"FU00014816","SN":"FU00014817","freq":"daily"},
    "SHFE库存": {"CU":"FU00014935","AL":"FU00014930","PB":"FU00014943","ZN":"FU00014947",
                "NI":"FU00014980","SN":"FU00014953","SI":"FU00015013","LC":"FU00015028","freq":"daily"},
    "社库": {"CU":"ID00188319","AL":"ID00188307","PB":"ID00188315","ZN":"ID00188329",
            "NI":"ID00185743","SN":"ID01517441","LC":"ID01002500","freq":"weekly"},
    "TC": {"CU":"ID01154994","PB":"a10127385","ZN":"ID01320080","NI":"ID01002200",
           "SN":"ID01001800","freq":"weekly"},
    "精炼产量": {"CU":"ID00188139","AL":"a10124317","PB":"a10017062","ZN":"ID01510883",
                "NI":"a10018516","SN":"a10003083","SI":"ID01448337","LC":"a10006555","freq":"monthly"},
    "表观消费": {"CU":"ID00188149","AL":"ID00188317","PB":"ID00188325","ZN":"ID01510893",
                "NI":"ID01001570","SN":"ID00187499","SI":"ID01448347","LC":"ID01002510","freq":"monthly"},
    "开工率": {"CU":"ID01067717","AL":"a10031808","PB":"ID01030005","ZN":"a10097188",
              "NI":"a10019689","SN":"a10083975","SI":"ID01448357","LC":"a10001859","freq":"monthly"},
}

app = Flask(__name__)


def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS indicator_cache (
            code TEXT NOT NULL,
            metric TEXT NOT NULL,
            zhiji_id TEXT,
            data_json TEXT,
            fetched_at TEXT DEFAULT (datetime('now')),
            error_msg TEXT,
            PRIMARY KEY(code, metric)
        )
    """)
    conn.commit()
    return conn


def call_zhiji(zhiji_id, freq):
    """调 Zhiji API 拉一个指标的历史数据"""
    end = datetime.now().strftime("%Y-%m-%d")
    if freq == "daily":
        start = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
    elif freq == "weekly":
        start = (datetime.now() - timedelta(days=1095)).strftime("%Y-%m-%d")
    else:
        start = (datetime.now() - timedelta(days=1095)).strftime("%Y-%m-%d")

    cmd = [sys.executable, ZHJI, "series", zhiji_id, start, end]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return {"error": r.stderr[:200]}
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"error": "JSON parse fail"}


def fetch_indicator(code, metric):
    """核心逻辑：滑动缓存 + 实时调用"""
    conn = db_conn()

    # 1. 查缓存（3天内有效）
    cutoff = (datetime.now() - timedelta(days=CACHE_DAYS)).isoformat()
    row = conn.execute(
        "SELECT data_json, fetched_at, error_msg FROM indicator_cache "
        "WHERE code=? AND metric=? AND fetched_at>? ORDER BY fetched_at DESC LIMIT 1",
        (code, metric, cutoff)
    ).fetchone()

    if row and row[0]:  # 缓存命中
        conn.execute("UPDATE indicator_cache SET fetched_at=datetime('now') WHERE code=? AND metric=?", (code, metric))
        conn.commit()
        conn.close()
        return json.loads(row[0]), "cache"

    # 2. 缓存未命中 → 调 Zhiji
    info = INDICATOR_IDS.get(metric, {})
    zhiji_id = info.get(code)
    if not zhiji_id:
        conn.close()
        return {"error": f"指标映射缺失: {code}/{metric}"}, "missing"

    freq = info.get("freq", "daily")
    result = call_zhiji(zhiji_id, freq)

    # 3. 存缓存
    conn.execute(
        "INSERT OR REPLACE INTO indicator_cache(code,metric,zhiji_id,data_json,fetched_at,error_msg) "
        "VALUES(?,?,?,?,datetime('now'),?)",
        (code, metric, zhiji_id, json.dumps(result, ensure_ascii=False),
         result.get("error") if isinstance(result, dict) else None)
    )
    conn.commit()
    conn.close()

    return result, "api"


@app.route("/api/indicator")
def api_indicator():
    code = request.args.get("code", "").upper()
    metric = request.args.get("metric", "")

    if not code or not metric:
        return jsonify({"error": "缺少 code 或 metric 参数"})

    data, source = fetch_indicator(code, metric)

    # 构造返回
    points = []
    if isinstance(data, dict) and "points" in data:
        pts = data["points"]
        # 最近120点
        points = pts[-120:] if len(pts) > 120 else pts

    return jsonify({
        "code": code,
        "metric": metric,
        "source": source,
        "points": points,
        "count": len(points),
        "cached_at": None,
        "error": data.get("error") if isinstance(data, dict) else None
    })


@app.route("/api/cache/stats")
def cache_stats():
    conn = db_conn()
    total = conn.execute("SELECT COUNT(*) FROM indicator_cache").fetchone()[0]
    hit = conn.execute("SELECT COUNT(*) FROM indicator_cache WHERE fetched_at > datetime('now','-3 days')").fetchone()[0]
    size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    conn.close()
    return jsonify({"total": total, "valid_cache": hit, "db_size_mb": round(size/1024/1024, 2)})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8786
    print(f"📡 framework-tree API 启动 → http://127.0.0.1:{port}")
    print(f"   缓存: {DB_PATH} (3天滑动)")
    app.run(host="127.0.0.1", port=port, debug=False)
