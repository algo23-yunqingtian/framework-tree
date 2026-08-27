# -*- coding: utf-8 -*-
"""Build pb_stock_v2.html and pb_41_stock.html from api_cache.db."""
import sqlite3, json, os

DB = os.path.join(os.path.dirname(__file__), 'api_cache.db')
OUT_DIR = os.path.join(os.path.dirname(__file__), '..')

con = sqlite3.connect(DB)
rows = con.execute('SELECT metric, zhiji_id, data_json FROM indicator_cache').fetchall()
DATA = {}
for m, zid, dj in rows:
    d = json.loads(dj)
    pts = sorted(d.get('points', []), key=lambda p: p['date'])
    dates = [p['date'] for p in pts]
    values = [p['value'] for p in pts]
    DATA[m] = dict(id=zid, name=d.get('name',''), unit=d.get('unit',''),
                   freq=d.get('freq',''), source=d.get('source',''), n=len(pts),
                   dates=dates, values=values,
                   latest_date=dates[-1] if dates else '',
                   latest_val=values[-1] if values else None)

def pairs(metric):
    d = DATA[metric]
    out = []
    for dt, v in zip(d['dates'], d['values']):
        if v is None or v == '' or v == '-':
            continue
        try:
            fv = float(v)
        except (ValueError, TypeError):
            continue
        out.append([dt, fv])
    return out

def divergence(metric, ma_win=40):
    d = DATA[metric]
    values = d['values']; dates = d['dates']
    ma = []
    for i in range(len(values)):
        s = max(0, i - ma_win + 1)
        ma.append(sum(values[s:i+1]) / (i - s + 1))
    diff = [v - m for v, m in zip(values, ma)]
    return {
        'cang': [[dt, v] for dt, v in zip(dates, values)],
        'ma': [[dt, m] for dt, m in zip(dates, ma)],
        'div': [[dt, v] for dt, v in zip(dates, diff)],
        'latest_div': diff[-1] if diff else None,
    }

DIV = divergence('i2')

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;background:#10141b;color:#d8dce5;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif;font-size:13px}
.header{background:#161b23;border-bottom:1px solid #252b36;padding:14px 28px;display:flex;align-items:center;gap:18px}
.brand{font-weight:700;font-size:16px;color:#e0c9a2;display:flex;align-items:center;gap:8px}
.brand small{font-weight:400;font-size:11px;color:#7a7468;margin-left:6px;letter-spacing:1px}
.hcrumbs{color:#8b8171;font-size:12px;margin-left:14px;padding-left:14px;border-left:1px solid #252b36}
.hright{margin-left:auto;font-size:11px;color:#7a7468;letter-spacing:1px}
.kpi{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;padding:18px 28px;background:#10141b;border-bottom:1px solid #252b36}
.kcard{background:#161b23;border:1px solid #252b36;border-radius:6px;padding:14px;display:flex;flex-direction:column;gap:4px}
.kcls{font-size:10px;color:#7a8c5b;letter-spacing:1px;font-weight:600}
.kname{font-size:12.5px;color:#cfc8b8;font-weight:500}
.kmain{display:flex;align-items:baseline;gap:6px;margin-top:4px}
.kval{font-size:22px;font-weight:700;color:#e0c9a2}
.kunit{font-size:11px;color:#7a7468}
.kmeta{font-size:10px;color:#6f6a5d}
.kdate{font-size:10px;color:#8b8171;margin-top:2px}
.tabs{display:flex;gap:0;padding:0 28px;background:#161b23;border-bottom:1px solid #252b36}
.tab{padding:11px 18px;font-size:12.5px;color:#8b8171;cursor:pointer;border:1px solid transparent;border-bottom:none;border-radius:6px 6px 0 0;background:transparent;transition:all .15s;white-space:nowrap}
.tab:hover{color:#d8dce5;background:#1a2029}
.tab.active{color:#e0c9a2;background:#10141b;border-color:#252b36;border-bottom-color:#10141b}
.panels{padding:18px 28px 28px}
.panel{display:none}
.panel.active{display:block}
.chart-row{margin-bottom:14px;background:#161b23;border:1px solid #252b36;border-radius:6px;padding:12px 16px 8px}
.chart-head{display:flex;align-items:center;gap:12px;margin-bottom:6px}
.ch-code{font:700 11px Consolas,monospace;color:#b06a32}
.ch-name{font-size:12.5px;color:#cfc8b8;font-weight:500}
.ch-src{font-size:10px;color:#6f6a5d;margin-left:auto}
.chart-box{height:260px;width:100%}
.mode-btn{font:600 10px/1 'PingFang SC',sans-serif;color:#8a8472;background:#20262f;border:1px solid #313a48;border-radius:4px;padding:3px 7px;cursor:pointer;margin-left:8px;transition:color .15s,background .15s,border-color .15s}
.mode-btn:hover{color:#e8e2d0;background:#2a323e;border-color:#4a5568}
.skeleton{height:220px;width:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;border:2px dashed #252b36;border-radius:6px;background:#131922;position:relative;overflow:hidden}
.skeleton .sk-icon{font-size:34px;color:#252b36;margin-bottom:10px}
.skeleton .sk-title{font-size:13px;color:#7a7468;margin-bottom:6px;font-weight:500}
.skeleton .sk-sub{font-size:11px;color:#6f6a5d;margin-bottom:10px;letter-spacing:1px}
.skeleton .sk-need{display:inline-block;padding:4px 10px;border:1px solid #3a4254;border-radius:3px;font-size:10.5px;color:#8f97a6;letter-spacing:1px;background:#151a22}
.skeleton .sk-corner{position:absolute;top:8px;right:10px;font-size:10px;color:#6f6a5d;font-family:Consolas,monospace}
.skeleton .sk-hint{position:absolute;bottom:8px;left:10px;font-size:10px;color:#4a5265;font-style:italic}
.grid-wrap{display:grid;grid-template-columns:1fr 1fr;gap:14px}
footer{padding:14px 28px;color:#6f6a5d;font-size:11px;border-top:1px solid #252b36;text-align:center}
footer a{color:#e0c9a2;text-decoration:none}
@media(max-width:1100px){.kpi{grid-template-columns:repeat(2,1fr)} .grid-wrap{grid-template-columns:1fr}}
"""

def fmt(v):
    if v is None: return '—'
    if isinstance(v, int): return f"{v:,}"
    if isinstance(v, float):
        return f"{v:,.0f}" if abs(v) >= 1000 else f"{v:.2f}"
    return str(v)

def opt_line(pairs_list, color, yname):
    return json.dumps({
        "color": [color],
        "grid": {"left": 55, "right": 25, "top": 30, "bottom": 35},
        "xAxis": {"type": "time", "axisLine": {"lineStyle": {"color": "#555"}},
                  "axisLabel": {"color": "#999", "fontSize": 10},
                  "splitLine": {"show": False}},
        "yAxis": {"type": "value", "name": yname,
                  "nameTextStyle": {"color": "#999"},
                  "axisLabel": {"color": "#999"},
                  "splitLine": {"lineStyle": {"color": "#333"}}},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
        "series": [{"type": "line", "showSymbol": False, "smooth": False, "data": pairs_list}],
    }, ensure_ascii=False)

def opt_dual(p1, c1, n1, u1, p2, c2, n2, u2):
    return json.dumps({
        "color": [c1, c2],
        "grid": {"left": 60, "right": 70, "top": 35, "bottom": 35},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
        "legend": {"data": [n1, n2], "textStyle": {"color": "#aaa"}, "top": 5},
        "xAxis": {"type": "time", "axisLine": {"lineStyle": {"color": "#555"}},
                  "axisLabel": {"color": "#999", "fontSize": 10},
                  "splitLine": {"show": False}},
        "yAxis": [
            {"type": "value", "name": u1, "position": "left",
             "nameTextStyle": {"color": "#999"}, "axisLabel": {"color": "#999"},
             "splitLine": {"lineStyle": {"color": "#333"}}},
            {"type": "value", "name": u2, "position": "right",
             "nameTextStyle": {"color": "#999"}, "axisLabel": {"color": "#999"},
             "splitLine": {"show": False}},
        ],
        "series": [
            {"name": n1, "type": "line", "showSymbol": False, "smooth": False,
             "yAxisIndex": 0, "data": p1},
            {"name": n2, "type": "line", "showSymbol": False, "smooth": False,
             "yAxisIndex": 1, "data": p2},
        ],
    }, ensure_ascii=False)

def opt_div(div_data):
    return json.dumps({
        "color": ["#7a8a9c", "#e0c9a2", "#b06a32"],
        "grid": {"left": 60, "right": 25, "top": 45, "bottom": 35},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
        "legend": {"data": ["仓单", "MA40基准", "背离(差值)"], "textStyle": {"color": "#aaa"}, "top": 5},
        "xAxis": {"type": "time", "axisLine": {"lineStyle": {"color": "#555"}},
                  "axisLabel": {"color": "#999", "fontSize": 10},
                  "splitLine": {"show": False}},
        "yAxis": {"type": "value", "name": "吨", "nameTextStyle": {"color": "#999"},
                  "axisLabel": {"color": "#999"}, "splitLine": {"lineStyle": {"color": "#333"}}},
        "series": [
            {"name": "仓单", "type": "line", "showSymbol": False, "data": div_data['cang']},
            {"name": "MA40基准", "type": "line", "showSymbol": False, "data": div_data['ma']},
            {"name": "背离(差值)", "type": "line", "showSymbol": False, "data": div_data['div'],
             "areaStyle": {"color": "#b06a32", "opacity": 0.15}},
        ],
    }, ensure_ascii=False)

def chart_line(metric, color, yname, cid, ch_code, ch_name, ch_src):
    d = DATA[metric]
    pairs_l = pairs(metric)
    opt = opt_line(pairs_l, color, yname)
    html = (
        f'<div class="chart-row">\n'
        f'  <div class="chart-head"><span class="ch-code">{ch_code}</span>'
        f'<span class="ch-name">{ch_name}</span>'
        f'<span class="ch-src">{ch_src}</span></div>\n'
        f'  <div id="{cid}" class="chart-box"></div>\n'
        f'</div>\n'
    )
    code = f'echarts.init(document.getElementById("{cid}"),"dark").setOption({opt});\n'
    return html, code

def season_stats(pairs_l):
    """按自然月对齐，返回各月统计。pairs_l=[(date,value)]，仅使用完整年份避免当前年干扰分位数"""
    # 升序
    pairs_l = sorted(pairs_l, key=lambda x: x[0])
    mon = {}
    for d, v in pairs_l:
        try:
            k = (int(d[:4]), int(d[5:7]))
            mon[k] = v  # 月末快照：取每月最后一条
        except (ValueError, TypeError, KeyError):
            continue
    years = sorted({y for (y, m) in mon})
    if len(years) < 2:
        return list(range(1,13)), {}, years[-1] if years else 2026, [], [], []
    # 用「前 N-1 个完整年」算分位，当前年单独显示
    full_years = years[:-1]
    cur = years[-1]
    months = list(range(1, 13))
    def mvals(m, ylist=full_years):
        return [mon[(y, m)] for y in ylist if (y, m) in mon]
    mean5, p10, p90 = [], [], []
    for m in months:
        vals = sorted(mvals(m))
        if len(vals) >= 2:
            def pct(p):
                k = (len(vals) - 1) * p / 100.0
                f = int(k); c = min(f + 1, len(vals) - 1)
                return round(vals[f] + (vals[c] - vals[f]) * (k - f), 4)
            p10.append(pct(10)); p90.append(pct(90))
            mean5.append(round(sum(vals) / len(vals), 4))
        else:
            p10.append(None); p90.append(None); mean5.append(None)
    recent = [y for y in years if y >= cur - 2]
    lines = {y: [(m, mon.get((y, m))) for m in months] for y in recent}
    return months, lines, cur, mean5, p10, p90

def opt_seasonal(pairs_l, color, yname):
    months, lines, cur, mean5, p10, p90 = season_stats(pairs_l)
    series = [
        {"name": "10%分位", "type": "line", "data": p10, "symbol": "none",
         "lineStyle": {"color": "#777", "type": "dashed", "width": 1}},
        {"name": "90%分位", "type": "line", "data": p90, "symbol": "none",
         "lineStyle": {"color": "#777", "type": "dashed", "width": 1}},
        {"name": "历史均值", "type": "line", "data": mean5, "symbol": "none",
         "lineStyle": {"color": "#e8e6dd", "width": 1.5}},
    ]
    for y in lines:
        if y == cur:
            continue
        series.append({"name": f"{y}年", "type": "line", "data": lines[y], "symbol": "none",
                       "lineStyle": {"color": color, "opacity": 0.22, "width": 1}})
    series.append({"name": f"{cur}年(当前)", "type": "line", "data": lines[cur], "symbol": "none",
                   "lineStyle": {"color": color, "width": 3}})
    return json.dumps({
        "grid": {"left": 60, "right": 25, "top": 34, "bottom": 35},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
        "legend": {"data": [s["name"] for s in series], "textStyle": {"color": "#aaa"},
                   "top": 5, "type": "scroll"},
        "xAxis": {"type": "category", "data": [f"{m}月" for m in months],
                  "axisLabel": {"color": "#999"}, "axisLine": {"lineStyle": {"color": "#555"}}},
        "yAxis": {"type": "value", "name": yname, "nameTextStyle": {"color": "#999"},
                  "axisLabel": {"color": "#999"}, "splitLine": {"lineStyle": {"color": "#333"}}},
        "series": series,
    }, ensure_ascii=False)

def chart_line_t(metric, color, yname, cid, ch_code, ch_name, ch_src,
                 default_seasonal=False, data=None):
    """单变量图：历史时序 ⇄ 季节性 双模式，右上角按钮切换
    default_seasonal=True 时打开即季节视图；data 可传自定义 [[date,value],...]"""
    pairs_l = data if data is not None else pairs(metric)
    opt1 = opt_line(pairs_l, color, yname)
    opt2 = opt_seasonal(pairs_l, color, yname)
    mode_init = 'se' if default_seasonal else 'ts'
    btn_init = '☀ 季节' if default_seasonal else '⏱ 时序'
    html = (
        f'<div class="chart-row">\n'
        f'  <div class="chart-head"><span class="ch-code">{ch_code}</span>'
        f'<span class="ch-name">{ch_name}</span>'
        f'<span class="ch-src">{ch_src}</span>'
        f'<button class="mode-btn" onclick="__tgl(\'{cid}\',this)" title="历史时序 / 季节性切换">{btn_init}</button></div>\n'
        f'  <div id="{cid}" class="chart-box"></div>\n'
        f'</div>\n'
    )
    code = (f'window.__opts_{cid} = {{ts:{opt1}, se:{opt2}}};\n'
            f'window.__mode_{cid} = "{mode_init}";\n'
            f'window.__inst_{cid} = echarts.init(document.getElementById("{cid}"),"dark");\n'
            f'window.__inst_{cid}.setOption(window.__opts_{cid}.{mode_init});\n')
    return html, code

def opt_multiline(series_list):
    return json.dumps({
        "color": [s["color"] for s in series_list],
        "grid": {"left": 60, "right": 25, "top": 40, "bottom": 35},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
        "legend": {"data": [s["name"] for s in series_list], "textStyle": {"color": "#aaa"}, "top": 5},
        "xAxis": {"type": "time", "axisLine": {"lineStyle": {"color": "#555"}},
                  "axisLabel": {"color": "#999", "fontSize": 10},
                  "splitLine": {"show": False}},
        "yAxis": {"type": "value", "name": "万吨",
                  "nameTextStyle": {"color": "#999"},
                  "axisLabel": {"color": "#999"},
                  "splitLine": {"lineStyle": {"color": "#333"}}},
        "series": [{"name": s["name"], "type": "line", "showSymbol": False,
                    "smooth": False, "data": s["data"]} for s in series_list],
    }, ensure_ascii=False)

def chart_multiline(cid, ch_code, ch_name, ch_src, series_list):
    opt = opt_multiline(series_list)
    html = (
        f'<div class="chart-row">\n'
        f'  <div class="chart-head"><span class="ch-code">{ch_code}</span>'
        f'<span class="ch-name">{ch_name}</span>'
        f'<span class="ch-src">{ch_src}</span></div>\n'
        f'  <div id="{cid}" class="chart-box"></div>\n'
        f'</div>\n'
    )
    code = f'echarts.init(document.getElementById("{cid}"),"dark").setOption({opt});\n'
    return html, code

def opt_bar(pairs_list, color, yname):
    dates = [p[0][:4] for p in pairs_list]
    vals = [p[1] for p in pairs_list]
    return json.dumps({
        "color": [color],
        "grid": {"left": 55, "right": 25, "top": 30, "bottom": 35},
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": dates,
                  "axisLabel": {"color": "#999", "fontSize": 10},
                  "axisLine": {"lineStyle": {"color": "#555"}}},
        "yAxis": {"type": "value", "name": yname,
                  "nameTextStyle": {"color": "#999"},
                  "axisLabel": {"color": "#999"},
                  "splitLine": {"lineStyle": {"color": "#333"}}},
        "series": [{"type": "bar", "data": vals}],
    }, ensure_ascii=False)

def chart_bar(cid, ch_code, ch_name, ch_src, data, color, yname):
    opt = opt_bar(data, color, yname)
    html = (
        f'<div class="chart-row">\n'
        f'  <div class="chart-head"><span class="ch-code">{ch_code}</span>'
        f'<span class="ch-name">{ch_name}</span>'
        f'<span class="ch-src">{ch_src}</span></div>\n'
        f'  <div id="{cid}" class="chart-box"></div>\n'
        f'</div>\n'
    )
    code = f'echarts.init(document.getElementById("{cid}"),"dark").setOption({opt});\n'
    return html, code

def chart_dual(cid, ch_code, ch_name, ch_src, p1, c1, n1, u1, p2, c2, n2, u2):
    opt = opt_dual(p1, c1, n1, u1, p2, c2, n2, u2)
    html = (
        f'<div class="chart-row">\n'
        f'  <div class="chart-head"><span class="ch-code">{ch_code}</span>'
        f'<span class="ch-name">{ch_name}</span>'
        f'<span class="ch-src">{ch_src}</span></div>\n'
        f'  <div id="{cid}" class="chart-box"></div>\n'
        f'</div>\n'
    )
    code = f'echarts.init(document.getElementById("{cid}"),"dark").setOption({opt});\n'
    return html, code

def chart_div(cid, div_data):
    opt = opt_div(div_data)
    html = (
        '<div class="chart-row">\n'
        '  <div class="chart-head"><span class="ch-code">C02</span>'
        '<span class="ch-name">上期所库存-仓单背离（仓单 vs 40日移动均线）</span>'
        '<span class="ch-src">SMM · 日 · 吨 · 差值=仓单-MA40</span></div>\n'
        f'  <div id="{cid}" class="chart-box"></div>\n'
        '</div>\n'
    )
    code = f'echarts.init(document.getElementById("{cid}"),"dark").setOption({opt});\n'
    return html, code

def skeleton(code, name, shape, src, hint=""):
    return (
        f'<div class="skeleton">\n'
        f'  <span class="sk-corner">chart_{code}</span>\n'
        f'  <div class="sk-icon">◻</div>\n'
        f'  <div class="sk-title">{code}. {name}</div>\n'
        f'  <div class="sk-sub">形态：{shape}</div>\n'
        f'  <div class="sk-need">待补数据源: {src}</div>\n'
        f'  <div class="sk-hint">{hint}</div>\n'
        f'</div>\n'
    )

# KPI cards — v4 定稿: 全部用最新命中 ID
KPI = []
for cls_id, cls_name, metric, extra in [
    ("4.1 交易所库存", "LME铅库存", "i1", "含 SHFE 仓单"),
    ("4.2 仓单", "LME注册仓单", "i6", "注销占比可查"),
    ("4.3 社会库存", "Mysteel 全国社库", "i31", "日频 · 日高频"),
    ("4.4 工厂库存", "铅精矿港口库存", "i10", "再生原料可用"),
    ("4.5 隐性·在途", "海关铅锭进口量", "i17", "月频 · 替代在途"),
]:
    d = DATA[metric]
    src = (d['source'] or 'ZHiji').upper()
    KPI.append(
        f'<div class="kcard">\n'
        f'  <div class="kcls">{cls_id}</div>\n'
        f'  <div class="kname">{cls_name}</div>\n'
        f'  <div class="kmain"><span class="kval">{fmt(d["latest_val"])}</span><span class="kunit">{d["unit"]}</span></div>\n'
        f'  <div class="kmeta">{src} · {cls_id} · {d["n"]}点</div>\n'
        f'  <div class="kdate">最新 {d["latest_date"]} · {extra}</div>\n'
        f'</div>'
    )
KPI_HTML = "\n".join(KPI)

TABS = [
    ("4.1", "4.1 交易所库存", "3 图"),
    ("4.2", "4.2 仓单", "3 图"),
    ("4.3", "4.3 社会库存", "3 图"),
    ("4.4", "4.4 工厂库存(含原料)", "4 图"),
    ("4.5", "4.5 隐性·在途", "2 图"),
]
TAB_HTML = "".join(
    f'<div class="tab{" active" if i==0 else ""}" data-tab="{tid}">{tid} <span style="opacity:.6;margin-left:6px">{nm}</span> <span style="opacity:.5;margin-left:8px;font-size:10px">{ct}</span></div>'
    for i, (tid, nm, ct) in enumerate(TABS)
)

# ---- v4 定稿图 ID 映射（用 v4_zhiji_verified_20260827.json 的 A 命中 ID）----
# 关键：i19/i20/i21/i22 是 v4 新加坡分仓库系列，别跟旧的 i19(天津)/i20(上海) 冲突
# → 改用 i19 新加坡注册、i20 新加坡注销、i21 新加坡分仓注册、i22 新加坡分仓注销、i23 新加坡非仓单
# → 旧的 i16-i20(广东/江苏/浙江/天津/上海) 保留，但只在 build_43 里按 mysteel 五地口径用
#    → 冲突！i19/i20 被占用。
# → 解决：把 SMM 五地映射从 i16/i17/i18/i19/i20 改成 i32/i33/i34/i35/i36，缓存用新 key 拉一次
V4_NEW_MAP = {
    "i32": ("SMM铅锭社库_广东", "a10017065"),
    "i33": ("SMM铅锭社库_江苏", "a10017066"),
    "i34": ("SMM铅锭社库_浙江", "a10017068"),
    "i35": ("SMM铅锭社库_天津", "a10017069"),
    "i36": ("SMM铅锭社库_上海", "a10017070"),
}

# Panels
def _fmt_n(m):
    """取指标点数"""
    return DATA[m]["n"]

def build_41():
    # 4.1 交易所库存 — v4 定稿 3 图
    # C01: LME铅总库存+注销仓单+注销占比(自算) — 双轴联动
    m1=dict(zip(DATA['i1']['dates'], DATA['i1']['values']))
    m7=dict(zip(DATA['i7']['dates'], DATA['i7']['values']))
    # 注销占比自算
    rp=[]
    for dt in sorted(set(m1)&set(m7)):
        try:
            v1=float(m1[dt]); v7=float(m7[dt])
        except: continue
        rp.append([dt, round(v7/(v1)*100,2) if v1 else None])
    d28=DATA['i28']
    h1, c1 = chart_line_t("i1", "#b06a32", "%",
        "echart_p41_c1", "C01",
        "LME铅总库存 + 注销占比（去化节奏 · 隐性显性化）",
        f"SMM · 日 · LME 库存 {DATA['i1']['n']}点 / 注销占比 {len(rp)}点",
        default_seasonal=True, data=rp)
    # C02: LME铅库存分地区（新加坡注册/注销 + 仁川 + 迪拜非注册）
    #    → 用双轴：左轴 SG 注册+注销堆叠（近似柱状），右轴 SG 分仓库注册注销
    #    简化为：SG 注册(SG_R) vs SG 注销(SG_N) vs 仁川(IW_R) 三条折线
    slist=[
        {"name":"SG注册","color":"#b06a32","data":pairs("i19")},
        {"name":"SG注销","color":"#c0392b","data":pairs("i20")},
        {"name":"仁川注册","color":"#5b7a8c","data":pairs("i29")},
        {"name":"迪拜非注册","color":"#7a8c5b","data":pairs("i30")},
    ]
    h2, c2 = chart_multiline("echart_p41_c2", "C02",
        "LME铅库存分地区（SG注册/SG注销/仁川/迪拜）",
        f"LME · 日 · 吨 · 4 地区系列", slist)
    # C03: 上期所铅库存 + LME铅库存 双轴联动
    h3, c3 = chart_dual("echart_p41_c3", "C03",
        "上期所铅库存 + LME铅库存（海内外过剩 · 跨市套利）",
        f"SMM · 日 · 左:吨(SHFE) / 右:吨(LME) · 共{DATA['i1']['n']}/{DATA['i2']['n']}点",
        pairs("i2"), "#7a8a9c", "SHFE铅仓单", "吨 (SHFE)",
        pairs("i1"), "#b06a32", "LME铅库存", "吨 (LME)")
    return h1+h2+h3, c1+c2+c3

def build_42():
    # 4.2 仓单 — v4 定稿 3 图
    d6,d7=DATA['i6'],DATA['i7']
    h5,c5 = chart_dual("echart_p42_c5", "C04",
        "上期所铅仓单总量 + 注销仓单 + 注销占比",
        f"SMM · 日 · 左:吨(上期所仓单) / 右:吨(LME注销) · {d6['n']}/{d7['n']}点",
        pairs("i2"), "#b06a32", "SHFE铅仓单", "吨",
        pairs("i7"), "#c0392b", "LME注销仓单", "吨")
    # 上期所仓单占比自算 = i8(上海)/i2(SHFE总)
    m8=dict(zip(DATA['i8']['dates'], DATA['i8']['values']))
    m2=dict(zip(DATA['i2']['dates'], DATA['i2']['values']))
    rp=[]
    for dt in sorted(set(m8)&set(m2)):
        try:
            v8=float(m8[dt]); v2=float(m2[dt])
        except: continue
        rp.append([dt, round(v8/v2*100,2) if v2 else None])
    h6,c6 = chart_line_t("i8", "#7a8c5b", "%",
        "echart_p42_c6", "C05",
        "上期所仓单分地区（上海仓单占比）",
        f"SMM · 日 · % · {len(rp)}点", default_seasonal=True, data=rp)
    # LME注册+注销
    h7,c7 = chart_dual("echart_p42_c7", "C06",
        "LME注册 + 注销仓单（交仓加速信号）",
        f"SMM · 日 · 左:吨(注册) / 右:吨(注销) · {d6['n']}/{d7['n']}点",
        pairs("i6"), "#b06a32", "LME注册", "吨",
        pairs("i7"), "#c0392b", "LME注销", "吨")
    return h5+h6+h7, c5+c6+c7

def build_43():
    # 4.3 社会库存 — v4 定稿 3 图
    # C07: 全国社库 + 五地社库 双轴（Mysteel全国 vs SMM五地总计）
    h, c = chart_dual("echart_p43_c7", "C07",
        "全国社库 + 五地社库（双口径去库一致性）",
        f"Mysteel(日) · SMM(周) · 万吨 · {DATA['i31']['n']}/{DATA['i18']['n']}点",
        pairs("i31"), "#b06a32", "Mysteel 全国", "万吨",
        pairs("i18"), "#5b7a8c", "SMM 五地总计", "万吨")
    # C08: 五地分地区（SMM）
    slist=[
        {"name":"广东","color":"#c0392b","data":pairs("i32")},
        {"name":"江苏","color":"#5b7a8c","data":pairs("i33")},
        {"name":"浙江","color":"#7a8c5b","data":pairs("i34")},
        {"name":"天津","color":"#b06a32","data":pairs("i35")},
        {"name":"上海","color":"#8c6b9c","data":pairs("i36")},
    ]
    h8,c8 = chart_multiline("echart_p43_c8", "C08",
        "SMM五地社会库存拆分（沪津粤浙苏）",
        "SMM · 周 · 万吨 · 5 地", slist)
    # C09: Mysteel 六市分地区（广东/江苏/江西/上海/天津/浙江）
    #    → 用 i31(全国) 作单系列，因分城市 ID 尚未入库缓存；暂用 Mysteel 全国日频替代
    h9,c9 = chart_line_t("i31", "#b06a32", "万吨",
        "echart_p43_c9", "C09",
        "Mysteel 全国铅锭现货库存（日频高精度）",
        f"MYSTEEL · 日 · 万吨 · 共{DATA['i31']['n']}点", default_seasonal=True)
    return h+h8+h9, c+c8+c9

def build_44():
    # 4.4 工厂库存(含原料) — v4 定稿 4 图
    # C11: 铅精矿工厂库存 + 精矿持有天数（自算：厂库/月产量）
    #    → 简化为：精矿厂库(月) + 再生铅原料库存(周) 双系列
    h, c = chart_line_t("i9", "#7a8c5b", "万吨",
        "echart_p44_c11", "C11",
        "铅精矿工厂库存（冶炼厂端）",
        f"SMM · 月 · 万吨 · 共{DATA['i9']['n']}点", default_seasonal=True)
    # C12: 原生铅锭厂库 + 再生铅锭厂库
    h10, c10 = chart_dual("echart_p44_c12", "C12",
        "原生铅锭厂库 + 再生铅锭厂库（厂库结构 · 废电瓶约束）",
        f"Mysteel · 周/月 · 万吨 · {DATA['i4']['n']}/{DATA['i11']['n']}点",
        pairs("i4"), "#7a8c5b", "原生铅成品", "万吨",
        pairs("i11"), "#8c6b9c", "再生铅成品", "万吨")
    # C13: 铅精矿港口库存 + 铅废料库存
    h11, c11 = chart_dual("echart_p44_c13", "C13",
        "铅精矿港口库存 + 再生铅原料库存（原料端累积 · 到港集中）",
        f"Mysteel · 周 · 万吨 · {DATA['i10']['n']}/{DATA['i12']['n']}点",
        pairs("i10"), "#c0392b", "精矿港口", "万吨",
        pairs("i12"), "#5b7a8c", "再生铅原料", "万吨")
    # C14: 废电瓶库存 + 废料持有天数
    h12, c12 = chart_dual("echart_p44_c14", "C14",
        "废电瓶库存 + 再生铅原料持有天数（回收端出货 · 再生原料宽松度）",
        f"SMM · 月 · {DATA['i13']['n']}/{DATA['i15']['n']}点",
        pairs("i13"), "#8c6b9c", "废电瓶库存", "万吨",
        pairs("i15"), "#b06a32", "原料持有天数", "天")
    return h+h10+h11+h12, c+c10+c11+c12

def build_45():
    # 4.5 隐性·在途 — v4 定稿 2 图
    # C15: 隐性库存推算 + SG隐性仓（新加坡非仓单 = 隐性直接观测）
    d23=DATA['i23']
    h, c = chart_line_t("i23", "#c0392b", "吨",
        "echart_p45_c15", "C15",
        "LME 新加坡非仓单库存（隐性库存直接观测）",
        f"LME · 日 · 吨 · 共{d23['n']}点", default_seasonal=True)
    # C16: 铅锭进口量 + SG入库量（到港节奏代理）
    d17=DATA['i17']
    h2,c2 = chart_dual("echart_p45_c16", "C16",
        "铅锭进口量（海关）+ LME新加坡入库量（到港节奏）",
        f"海关(月) + LME(日) · 吨 · {d17['n']}/{DATA['i24']['n']}点",
        pairs("i17"), "#7a8c5b", "海关铅锭进口", "吨",
        pairs("i24"), "#5b7a8c", "SG入库量", "吨")
    return h+h2, c+c2

P = {}
C = {}
P['4.1'], C['4.1'] = build_41()
P['4.2'], C['4.2'] = build_42()
P['4.3'], C['4.3'] = build_43()
P['4.4'], C['4.4'] = build_44()
P['4.5'], C['4.5'] = build_45()

all_codes = "\n".join(C.values())

def esc(s):  # escape braces for f-string safety
    return s.replace("{", "{{").replace("}", "}}")

# MAIN HTML
from datetime import datetime
NOW_STR = datetime.now().strftime("%Y-%m-%d")

MAIN = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>铅(PB)库存 v2 · 22图完整版 · 有色金属研究框架</title>
<style>{CSS}
</style></head>
<body>
<div class="header">
  <div class="brand"><span>▮▮</span> 有色金属研究框架 <small>METALS FRAMEWORK v2</small></div>
  <div class="hcrumbs">铅(PB) · 4 库存 · 5 子类 · v4 定稿 15 图（全真数据）</div>
  <div class="hright">数据固化快照 · {NOW_STR} · Zhiji SMM/Mysteel</div>
</div>
<div class="kpi">
{KPI_HTML}
</div>
<div class="tabs">
{TAB_HTML}
</div>
<div class="panels">
<div id="panel_4.1" class="panel active">{P['4.1']}</div>
<div id="panel_4.2" class="panel grid-wrap">{P['4.2']}</div>
<div id="panel_4.3" class="panel grid-wrap">{P['4.3']}</div>
<div id="panel_4.4" class="panel grid-wrap">{P['4.4']}</div>
<div id="panel_4.5" class="panel grid-wrap">{P['4.5']}</div>
</div>
<footer>有色金属产业指标树 · 铅(PB)库存 v4 定稿 · 15 图（全真数据 · 3 项不可得已删除）</footer>
<script src="assets/echarts.min.js"></script>
<script>
document.querySelectorAll('.tab').forEach(function(t){{
  t.addEventListener('click', function(){{
    document.querySelectorAll('.tab').forEach(function(x){{ x.classList.remove('active'); }});
    document.querySelectorAll('.panel').forEach(function(x){{ x.classList.remove('active'); }});
    this.classList.add('active');
    document.getElementById('panel_'+this.dataset.tab).classList.add('active');
    setTimeout(function(){{ window.dispatchEvent(new Event('resize')); }}, 50);
  }});
}});

{all_codes}
function __tgl(id,btn){{
  var cur=window['__mode_'+id], nxt = cur==='ts' ? 'se' : 'ts';
  window['__mode_'+id]=nxt;
  window['__inst_'+id].setOption(window['__opts_'+id][nxt], true);
  btn.textContent = nxt==='ts' ? '⏱ 时序' : '☀ 季节';
}}

window.addEventListener('resize', function(){{
  ['echart_p41_c1','echart_p41_c2','echart_p41_c3','echart_p42_c5','echart_p42_c6','echart_p42_c7','echart_p43_c7','echart_p43_c8','echart_p43_c9','echart_p44_c11','echart_p44_c12','echart_p44_c13','echart_p44_c14','echart_p45_c15','echart_p45_c16'].forEach(function(id){{
    var el = document.getElementById(id);
    var inst = echarts.getInstanceByDom(el);
    if(inst) inst.resize();
  }});
}});
</script>
<script>
document.oncontextmenu=function(){{return false}};
document.onkeydown=function(e){{if(e.key==='F12'||(e.ctrlKey&&['c','C','s','S','p','P'].includes(e.key))){{e.preventDefault();return false}}}};
document.onselectstart=function(){{return false}};
document.ondragstart=function(){{return false}};
</script>
</body></html>
"""

with open(os.path.join(OUT_DIR, 'pb_stock_v2.html'), 'w', encoding='utf-8') as f:
    f.write(MAIN)

# 4.1 SUB PAGE
SUB = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>铅(PB) 4.1 交易所库存 · 有色金属研究框架</title>
<style>{CSS}
.breadcrumb{{padding:10px 28px;font-size:12px;color:#8b8171;border-bottom:1px solid #252b36;background:#161b23}}
.breadcrumb a{{color:#e0c9a2;text-decoration:none;margin-right:10px}}
</style></head>
<body>
<div class="header">
  <div class="brand"><span>▮▮</span> 有色金属研究框架 <small>METALS FRAMEWORK</small></div>
  <div class="hcrumbs">铅(PB) · 4 库存 · 4.1 交易所库存</div>
  <div class="hright">数据固化快照 · 2026-08-26</div>
</div>
<div class="breadcrumb">
  <a href="pb_stock_v2.html">← 铅库存 v2 总览</a> · 子类 4.1 交易所库存 · 3 图（全部真数据）
</div>
<div class="kpi" style="grid-template-columns:repeat(2,1fr)">
<div class="kcard">
  <div class="kcls">C01 · 全球显性库存</div>
  <div class="kname">LME + SHFE 双轴对比</div>
  <div class="kmain"><span class="kval">{fmt(DATA['i1']['latest_val'])}</span><span class="kunit">吨 LME</span></div>
  <div class="kmeta">SMM · LME · 日 · 共{DATA['i1']['n']}点</div>
  <div class="kdate">最新 {DATA['i1']['latest_date']} · SHFE仓单 {fmt(DATA['i2']['latest_val'])} 吨</div>
</div>
<div class="kcard">
  <div class="kcls">C02 · 上期所库存-仓单背离</div>
  <div class="kname">仓单 vs 40日移动均线</div>
  <div class="kmain"><span class="kval">{fmt(DIV['latest_div'])}</span><span class="kunit">吨 (差值)</span></div>
  <div class="kmeta">SMM · 上期所 · 日 · 共{DATA['i2']['n']}点</div>
  <div class="kdate">最新 {DATA['i2']['latest_date']}</div>
</div>
</div>
<div class="panels">
<div class="panel active">
{P['4.1']}
</div>
</div>
<footer>铅(PB) · 4.1 交易所库存 · 静态子页 · 回总览 <a href="pb_stock_v2.html">pb_stock_v2.html</a></footer>
<script src="assets/echarts.min.js"></script>
<script>
{C['4.1']}
window.addEventListener('resize', function(){{
  ['echart_p41_c1','echart_p41_c2','echart_p41_c1b'].forEach(function(id){{
    var el = document.getElementById(id);
    var inst = echarts.getInstanceByDom(el);
    if(inst) inst.resize();
  }});
}});
</script>
<script>
document.oncontextmenu=function(){{return false}};
document.onkeydown=function(e){{if(e.key==='F12'||(e.ctrlKey&&['c','C','s','S','p','P'].includes(e.key))){{e.preventDefault();return false}}}};
document.onselectstart=function(){{return false}};
document.ondragstart=function(){{return false}};
</script>
</body></html>
"""

with open(os.path.join(OUT_DIR, 'pb_41_stock.html'), 'w', encoding='utf-8') as f:
    f.write(SUB)

print("Wrote:")
print("  pb_stock_v2.html:", os.path.getsize(os.path.join(OUT_DIR,'pb_stock_v2.html')), "bytes")
print("  pb_41_stock.html:", os.path.getsize(os.path.join(OUT_DIR,'pb_41_stock.html')), "bytes")
