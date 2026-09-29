#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HERMES_BUILD_REVIEW_DASHBOARD_V85_20260928
T2: 交互式复核静态看板 (纯 html+css+内联JS, 无后端)
T4: 归档至 analysis/e2e_output/v85/review_dashboard/

约束: 零 zhiji API 调用 / 不改 indicators_v1.json / 不改匹配规则 / 不改 GT
      保留 REVIEW_SKIP / 人工结论列留白
"""
import csv, json, hashlib, os, shutil, datetime, html

BASE = "/home/ubuntu/framework-tree"
V85 = os.path.join(BASE, "analysis", "e2e_output", "v85")
OUT = os.path.join(V85, "review_dashboard")
RENDERS = os.path.join(V85, "renders_enhanced")
NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

os.makedirs(OUT, exist_ok=True)

# ---------- 1. 拷贝渲染图 ----------
for f in sorted(os.listdir(RENDERS)):
    if f.lower().endswith(".png"):
        shutil.copy2(os.path.join(RENDERS, f), os.path.join(OUT, "renders", f)) if os.path.isdir(os.path.join(OUT, "renders")) else None
os.makedirs(os.path.join(OUT, "renders"), exist_ok=True)
for f in sorted(os.listdir(RENDERS)):
    if f.lower().endswith(".png"):
        shutil.copy2(os.path.join(RENDERS, f), os.path.join(OUT, "renders", f))

# ---------- 2. 读最终过滤看板 ----------
BOARD_CSV = os.path.join(V85, "fp32_v85_final_filtered_board.csv")
with open(BOARD_CSV, encoding="utf-8-sig") as fh:
    reader = csv.DictReader(fh)
    rows = list(reader)
    cols = reader.fieldnames

def g(r, k, default=""):
    v = r.get(k, "")
    return v if v not in (None, "") else default

# ---------- 3. zhiji_id -> 渲染图映射 ----------
render_files = sorted(os.listdir(os.path.join(OUT, "renders")))
def find_render(zid):
    for f in render_files:
        if f.startswith(zid):
            return os.path.join("renders", f)
    return None

# ---------- 4. 状态着色规则 ----------
def row_class(r):
    """正常(白)/稀疏(黄)/权限缺失(橙)/数据源下线(红)"""
    ds = g(r, "data_status")
    uw = g(r, "unified_warning")
    mw = g(r, "meta_warning")
    rd = g(r, "绘图渲染状态")
    txt = "%s %s %s %s" % (ds, uw, mw, rd)
    if "稀疏" in txt or "sparse" in txt:
        return "row-sparse", "稀疏(黄)"
    if "下线" in txt or "停更" in txt or "stale" in txt:
        return "row-dead", "数据源下线(红)"
    if "权限缺失" in txt:
        return "row-perm", "权限缺失(橙)"
    return "row-ok", "正常(白)"

def unit_cls(v):
    v = (v or "").strip()
    if v == "是":
        return "u-ok"
    if v == "否":
        return "u-bad"
    if "换算" in v:
        return "u-warn"
    return "u-na"

# ---------- 5. 关键展示字段 ----------
# 任务要求「所有字段」→ 表头使用源 CSV 全量 47 列；人工结论列追加空白输入框供评审直接填写
HUMAN_COL = "人工结论(待填)"
# 坑1(交接文档§6.1): idx 列非全局唯一(9组重复) → 新增 L 行号列作为唯一定位键
LINENO_KEY = "行号"
KEY_COLS = [(LINENO_KEY, LINENO_KEY)] + [(c, c) for c in cols]


def short(k):
    return (k.lower().replace(" ", "").replace("(", "").replace(")", "")
                .replace(":", "").replace("（", "").replace("）", ""))


# ---------- 坑1/坑2 (交接文档 §6) ----------
# 坑2: 同一 zhiji_id 多条 → 标注需人工确认冗余
from collections import Counter, defaultdict
_zid_lines = defaultdict(list)
for _i, _r in enumerate(rows):
    _zid_lines[g(_r, "候选ID(v8_id)")].append(_i + 1)
DUP_MAP = {k: ["行%d" % n for n in v] for k, v in _zid_lines.items() if len(v) > 1}
# idx 唯一性统计（坑1 量化）
_idx_cnt = Counter(g(r, "idx") for r in rows)


def unit_wrap(r, k):
    """单位相关字段加颜色"""
    if k == "单位匹配":
        return '<span class="%s">%s</span>' % (unit_cls(g(r, k)), esc(g(r, k)))
    if k == "unit_convert_status" and g(r, k):
        return '<span class="u-warn">%s</span>' % esc(g(r, k))
    return esc(g(r, k))

# ---------- 6. 统计 ----------
n_total = len(rows)
n_ok = sum(1 for r in rows if row_class(r)[0] == "row-ok")
n_sparse = sum(1 for r in rows if row_class(r)[0] == "row-sparse")
n_perm = sum(1 for r in rows if row_class(r)[0] == "row-perm")
n_dead = sum(1 for r in rows if row_class(r)[0] == "row-dead")
n_redundant = sum(1 for r in rows if "冗余" in g(r, "冗余标记"))
n_pass = sum(1 for r in rows if g(r, "域过滤判定") == "放行")
n_block = sum(1 for r in rows if g(r, "域过滤判定") == "拦截")
n_abstain = sum(1 for r in rows if g(r, "域过滤判定") == "弃权")
n_fetch_ok = sum(1 for r in rows if g(r, "zhiji拉取状态") == "拉取成功")
n_render_ok = sum(1 for r in rows if g(r, "绘图渲染状态") == "渲染成功")
n_unit_conv = sum(1 for r in rows if "换算" in g(r, "unit_convert_status"))
n_unit_mismatch = sum(1 for r in rows if g(r, "单位匹配") == "否")
n_unified_warn = sum(1 for r in rows if g(r, "unified_warning") not in ("无", ""))
n_skip_kept = sum(1 for r in rows if g(r, "REVIEW_SKIP").startswith("是"))
n_human_blank = sum(1 for r in rows if g(r, "人工结论(待填)") == "")

# ---------- 7. 生成 HTML ----------
def esc(s):
    return html.escape(str(s) if s is not None else "", quote=True)

def anchor(i):
    """锚点用行号 r{行号}，禁用 idx —— 交接文档坑1: idx 列非全局唯一(9组重复)"""
    return "r%d" % (i + 1)

tbody = []
for i, r in enumerate(rows):
    cls, label = row_class(r)
    zid = g(r, "候选ID(v8_id)")
    rp = find_render(zid)
    warn_parts = [x for x in [g(r, "meta_warning"), g(r, "unified_warning")] if x and x != "无"]
    warn_html = ""
    if warn_parts:
        warn_html = '<span class="warn-badge">⚠ %s</span>' % esc("; ".join(warn_parts))
    img_html = ""
    if rp:
        img_html = ('<a class="imglink" href="%s" target="_blank" title="打开大图">%s</a>'
                    % (esc(rp), esc(zid) + ".png"))
    else:
        img_html = '<span class="noimg">—</span>'
    ucls = unit_cls(g(r, "单位匹配"))
    cells = []
    for k, _ in KEY_COLS:
        if k == LINENO_KEY:
            cells.append('<td class="c-lineno"><b>L%d</b></td>' % (i + 1))
            continue
        v = unit_wrap(r, k) if k in ("单位匹配", "unit_convert_status") else esc(g(r, k))
        if k == HUMAN_COL:
            cells.append('<td class="c-human"><input class="hconf" type="text" value="%s" '
                         'placeholder="人工结论(待填)"></td>' % esc(g(r, k)))
        elif k == "idx":
            mark = (' <span class="idx-warn" title="idx 非全局唯一，请勿仅凭 idx 定位行">!</span>')
            cells.append('<td class="c-idx">%s%s</td>' % (esc(g(r, k)), mark))
        else:
            cells.append('<td class="c-%s" title="%s">%s</td>' % (short(k), esc(g(r, k)), v))
    cells = "".join(cells)
    tr = ('<tr class="{cls}" id="{aid}" data-status="{label}" data-idx="{idx}" '
          'data-lineno="{lineno}" data-zid="{zid}" data-name="{name}" data-cand="{cand}">'
          '<td class="c-anchor"><a href="#{aid}">L{lineno}</a></td>'
          '<td class="c-status"><span class="pill {cls}">{label}</span>{warn}</td>'
          '<td class="c-img">{img}</td>'
          '{cells}'
          '</tr>')
    tbody.append(tr.format(cls=cls, aid=anchor(i), label=label, warn=warn_html, img=img_html,
                           cells=cells, idx=esc(g(r, "idx")), lineno=i + 1,
                           zid=esc(g(r, "候选ID(v8_id)")),
                           name=esc(g(r, "图表短名(PDF)")), cand=esc(g(r, "候选指标名"))))

THEAD = "".join(
    '<th class="t-%s" title="%s">%s</th>' % (short(k), esc(k), esc(k))
    for k, _ in KEY_COLS
)

# 告警直达清单（用行号定位，idx 非唯一）
warn_rows = [(i, r) for i, r in enumerate(rows) if row_class(r)[0] != "row-ok"]
warn_nav = "".join(
    '<a href="#r%d">行%d · idx%s · %s <span class="pill %s">%s</span></a>'
    % (i + 1, i + 1, esc(g(r, "idx")), esc(g(r, "图表短名(PDF)")), row_class(r)[0], row_class(r)[1])
    for i, r in warn_rows
)

# 渲染图 gallery
gallery = []
for i, r in enumerate(rows):
    zid = g(r, "候选ID(v8_id)")
    rp = find_render(zid)
    if not rp:
        continue
    rc, rl = row_class(r)
    # 坑2: 同一 zhiji_id 多条 → 标注【同ID重复行#N】，人工确认是否冗余
    dup_no = DUP_MAP.get(zid, [])
    dup_badge = ""
    if dup_no:
        dup_badge = ' <span class="dup-badge" title="同一 zhiji_id 在看板出现 %d 次，需人工确认冗余">%s</span>' % (
            len(dup_no), dup_no)
    gc = ('<figure class="gcard {rc}"><img src="{rp}" alt="{alt}" loading="lazy">'
          '<figcaption><a href="#r{i}">行{lineno}</a> · idx{idx} · {name}<br>'
          '{zid}{dup}<br><span class="tag">{label}</span> {points}点 · {unit}</figcaption></figure>')
    gallery.append(gc.format(rc=rc, rp=esc(rp), alt=esc(zid), i=i + 1, lineno=i + 1,
                             idx=esc(g(r, "idx")), name=esc(g(r, "图表短名(PDF)")),
                             zid=esc(zid), dup=dup_badge, label=rl,
                             points=esc(g(r, "时序数据条数")), unit=esc(g(r, "时序单位(API)"))))

CSS = """
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,"PingFang SC","Microsoft YaHei",Segoe UI,sans-serif;background:#0d1117;color:#c9d1d9;font-size:13px}
a{color:#58a6ff;text-decoration:none}
header{background:linear-gradient(135deg,#161b22,#1c2733);border-bottom:1px solid #30363d;padding:20px 28px}
header h1{margin:0 0 6px;font-size:20px;color:#f0f6fc}
header .sub{color:#8b949e;font-size:12px}
nav{display:flex;flex-wrap:wrap;gap:8px;padding:10px 28px;background:#161b22;border-bottom:1px solid #30363d;position:sticky;top:0;z-index:20}
nav a{padding:6px 12px;border:1px solid #30363d;border-radius:6px;font-size:12px;background:#0d1117}
nav a:hover{background:#21262d;border-color:#58a6ff}
main{padding:20px 28px;max-width:2200px;margin:0 auto}
section{margin-bottom:34px}
h2{font-size:16px;color:#f0f6fc;border-left:3px solid #58a6ff;padding-left:10px;margin:0 0 12px}
h3{font-size:14px;color:#e6edf3;margin:16px 0 8px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.stat{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px}
.stat .k{color:#8b949e;font-size:11px;margin-bottom:4px}
.stat .v{font-size:22px;font-weight:700;color:#f0f6fc}
.stat.warn .v{color:#f0883e}.stat.ok .v{color:#3fb950}.stat.bad .v{color:#f85149}
.legend{display:flex;flex-wrap:wrap;gap:14px;align-items:center;margin-bottom:12px;font-size:12px}
table{border-collapse:collapse;width:100%;font-size:12px;background:#0d1117}
th,td{border:1px solid #21262d;padding:6px 8px;text-align:left;vertical-align:top;white-space:nowrap;max-width:280px;overflow:hidden;text-overflow:ellipsis}
th{background:#1c2128;color:#8b949e;position:sticky;top:44px;font-weight:600}
td.c-idx{color:#8b949e}
td.c-img img{width:86px;height:auto;border:1px solid #30363d;border-radius:4px;cursor:zoom-in}
a.imglink{font-size:11px}
tr:hover td{background:#161b22}
.row-sparse{background:rgba(255,196,0,.09)}
.row-sparse:hover td{background:rgba(255,196,0,.16)}
.row-perm{background:rgba(240,136,62,.10)}
.row-perm:hover td{background:rgba(240,136,62,.18)}
.row-dead{background:rgba(248,81,73,.12)}
.row-dead:hover td{background:rgba(248,81,73,.20)}
.pill{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;border:1px solid}
.pill.row-ok{color:#3fb950;border-color:#238636;background:rgba(63,185,80,.08)}
.pill.row-sparse{color:#ffcc00;border-color:#9e6a03;background:rgba(255,196,0,.08)}
.pill.row-perm{color:#f0883e;border-color:#9e4a1f;background:rgba(240,136,62,.10)}
.pill.row-dead{color:#f85149;border-color:#b62324;background:rgba(248,81,73,.10)}
.warn-badge{color:#f0883e;font-size:11px;margin-left:6px;white-space:normal}
td.c-anchor a{color:#8b949e}
.u-ok{color:#3fb950}.u-bad{color:#f85149;font-weight:700}.u-warn{color:#ffcc00}.u-na{color:#8b949e}
.noimg{color:#484f58}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px}
.gcard{background:#161b22;border:1px solid #30363d;border-radius:8px;overflow:hidden;margin:0}
.gcard img{width:100%;display:block;cursor:zoom-in;border-bottom:1px solid #21262d}
.gcard.row-perm{border-color:#9e4a1f}.gcard.row-sparse{border-color:#9e6a03}.gcard.row-dead{border-color:#b62324}
.gcard figcaption{padding:8px 10px;font-size:11px;color:#8b949e;line-height:1.6}
.tag{color:#f0883e;font-weight:600}
ol.warmlist{list-style:none;padding:0}
ol.warmlist a{display:block;padding:8px 12px;border:1px solid #30363d;border-radius:6px;margin-bottom:6px;background:#161b22;font-size:12px}
ol.warmlist a:hover{border-color:#f0883e}
.note{background:#161b22;border:1px solid #30363d;border-left:3px solid #f0883e;border-radius:6px;padding:10px 14px;margin:10px 0;font-size:12px;line-height:1.7}
.note.ok{border-left-color:#3fb950}
.kv{display:grid;grid-template-columns:220px 1fr;gap:4px 14px;font-size:12px}
.kv .k{color:#8b949e}
footer{padding:20px 28px;border-top:1px solid #30363d;color:#8b949e;font-size:11px;text-align:center}
code{background:#161b22;padding:1px 5px;border-radius:4px;font-size:11px;color:#79c0ff}
input.hconf{width:160px;background:#0d1117;color:#f0f6fc;border:1px solid #30363d;border-radius:4px;padding:3px 6px;font-size:11px}
input.hconf:focus{outline:none;border-color:#58a6ff}
td.c-human{white-space:nowrap}
th.thuman,td.c-human{position:sticky;right:0;background:#1c2128}
tbody td.c-human{background:#0d1117;box-shadow:-2px 0 4px rgba(0,0,0,.4)}
tr.row-sparse td.c-human{background:#2a2100}
tr.row-perm td.c-human{background:#2a1608}
th.sticky-l{position:sticky;left:0;z-index:5}
.btn{display:inline-block;padding:7px 14px;background:#238636;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:12px;margin-right:8px}
.btn:hover{background:#2ea043}
.btn2{background:#21262d;border:1px solid #30363d}
.btn2:hover{background:#30363d}
td.c-lineno{font-weight:700;color:#58a6ff;text-align:center;white-space:nowrap}
td.c-anchor a{color:#58a6ff;font-weight:700}
.idx-warn{color:#f0883e;font-weight:700;cursor:help}
.dup-badge{display:inline-block;padding:1px 6px;border-radius:8px;font-size:10px;background:rgba(255,196,0,.15);color:#ffcc00;border:1px solid #9e6a03;margin-left:4px}
"""

JS = """
var q=document.getElementById('search');
q.addEventListener('input',function(){
  var t=q.value.trim().toLowerCase();
  document.querySelectorAll('#board tr[data-status]').forEach(function(tr){
    tr.style.display = !t || tr.textContent.toLowerCase().indexOf(t)>=0 ? '' : 'none';
  });
});
document.querySelectorAll('a[data-filter]').forEach(function(a){
  a.addEventListener('click',function(e){
    e.preventDefault();
    var f=a.getAttribute('data-filter');
    document.querySelectorAll('#board tr[data-status]').forEach(function(tr){
      tr.style.display = !f || tr.getAttribute('data-status')===f ? '' : 'none';
    });
  });
});
/* 人工结论本地暂存 + 导出 (纯前端, 零后端) */
var KEY='v85_review_conclusions';
function loadConf(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return{}}}
function saveConf(o){localStorage.setItem(KEY,JSON.stringify(o))}
function applyConf(){
  var o=loadConf();
  document.querySelectorAll('#board tr[data-status]').forEach(function(tr){
    var id=tr.id;var inp=tr.querySelector('input.hconf');
    if(inp&&o[id]!==undefined){inp.value=o[id];inp.classList.toggle('filled',!!o[id].trim())}
  });
}
document.querySelectorAll('#board input.hconf').forEach(function(inp){
  inp.addEventListener('input',function(){
    var tr=inp.closest('tr');var o=loadConf();o[tr.id]=inp.value;saveConf(o);
    inp.classList.toggle('filled',!!inp.value.trim());
  });
});
applyConf();
document.getElementById('btnExport').addEventListener('click',function(){
  var o=loadConf();
  var lines=['行号|idx|zhiji_id|图表短名|候选指标名|人工结论'];
  document.querySelectorAll('#board tr[data-status]').forEach(function(tr){
    var inp=tr.querySelector('input.hconf');
    lines.push([
      tr.getAttribute('data-lineno')||'',
      tr.getAttribute('data-idx')||'',
      (tr.getAttribute('data-zid')||'').replace(/\|/g,'/'),
      (tr.getAttribute('data-name')||'').replace(/\|/g,'/'),
      (tr.getAttribute('data-cand')||'').replace(/\|/g,'/'),
      (inp?inp.value:'').replace(/\|/g,'/')
    ].join('|'));
  });
  var blob=new Blob([lines.join('\\n')],{type:'text/plain;charset=utf-8'});
  var a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download='v85_人工结论_'+new Date().toISOString().slice(0,10)+'.csv';
  a.click();
});
document.getElementById('btnClear').addEventListener('click',function(){
  if(confirm('清空本页所有人工结论暂存?')){localStorage.removeItem(KEY);document.querySelectorAll('#board input.hconf').forEach(function(i){i.value='';i.classList.remove('filled')})}
});
"""

HTML_DOC = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>V8.5 上线复核看板 · 人工复核入口</title>
<style>%s</style>
</head>
<body>
<header>
  <h1>V8.5 端到端产物 · 上线复核看板</h1>
  <div class="sub">工单 HERMES_BUILD_REVIEW_DASHBOARD_V85_20260928 ｜ 生成 %s ｜ 数据源 fp32_v85_final_filtered_board.csv（%d 行全量，含拦截/弃权样本）</div>
</header>

<nav>
  <a href="#overview">概览</a>
  <a href="#warn" data-filter="">全部</a>
  <a href="#warn" data-filter="稀疏(黄)">稀疏</a>
  <a href="#warn" data-filter="权限缺失(橙)">权限缺失</a>
  <a href="#warn" data-filter="数据源下线(红)">下线</a>
  <a href="#warn">告警直达</a>
  <a href="#gallery">图表速览</a>
  <a href="#board">全量表</a>
  <input id="search" placeholder="搜索 idx/品种/指标/ID…" style="margin-left:auto;padding:6px 10px;border:1px solid #30363d;border-radius:6px;background:#0d1117;color:#c9d1d9;font-size:12px;width:240px">
</nav>

<main>

<section id="overview">
  <h2>1. 复核概览</h2>
  <div class="stats">
    <div class="stat"><div class="k">看板总行</div><div class="v">%d</div></div>
    <div class="stat ok"><div class="k">放行</div><div class="v">%d</div></div>
    <div class="stat warn"><div class="k">拦截</div><div class="v">%d</div></div>
    <div class="stat warn"><div class="k">弃权</div><div class="v">%d</div></div>
    <div class="stat ok"><div class="k">拉取成功</div><div class="v">%d</div></div>
    <div class="stat ok"><div class="k">渲染成功</div><div class="v">%d</div></div>
    <div class="stat"><div class="k">冗余废弃</div><div class="v">%d</div></div>
    <div class="stat warn"><div class="k">单位冲突</div><div class="v">%d</div></div>
    <div class="stat ok"><div class="k">单位已换算</div><div class="v">%d</div></div>
    <div class="stat warn"><div class="k">unified_warning 命中</div><div class="v">%d</div></div>
    <div class="stat ok"><div class="k">REVIEW_SKIP 保留</div><div class="v">%d/%d</div></div>
    <div class="stat ok"><div class="k">人工结论留白</div><div class="v">%d/%d</div></div>
  </div>
  <h3>状态分布</h3>
  <div class="stats">
    <div class="stat ok"><div class="k">正常(白)</div><div class="v">%d</div></div>
    <div class="stat"><div class="k">稀疏(黄)</div><div class="v">%d</div></div>
    <div class="stat warn"><div class="k">权限缺失(橙)</div><div class="v">%d</div></div>
    <div class="stat bad"><div class="k">数据源下线(红)</div><div class="v">%d</div></div>
  </div>
  <div class="note">
    <b>着色口径</b>：正常=白（默认无底色）｜稀疏=黄（data_status/unified_warning 含稀疏）｜权限缺失=橙（data_status=权限缺失）｜数据源下线=红（含停更/下线/stale）。<br>
    <b>本版 32 行实际分布</b>：正常 %d / 稀疏 %d / 权限缺失 %d / 下线 %d。稀疏与下线两类在本轮 32 行看板内<b>均为 0</b>，原因是稀疏/停更的 3 个 zhiji_id（ID00259727、CM0000053686、a10166705）经 FP 抑制后未进入本看板集合，其告警已完整记入 <code>unified_warning_summary.md</code> §2.2 不丢失。
  </div>
</section>

<section id="warn">
  <h2>2. 告警直达（%d 条）</h2>
  <ol class="warmlist">%s</ol>
  <div class="note">
    <b>未进入看板但必须人工关注的 3 条</b>（告警回填时判定不在 32 行看板集合，仅记入汇总）：<br>
    · <code>ID00259727</code> 电解铝A00现货价 停更1446天[HIGH] + 单位不符[MEDIUM]<br>
    · <code>CM0000053686</code> SEAISI东南亚钢铁出口 停更636天[HIGH] + 稀疏1条[MEDIUM]<br>
    · <code>a10166705</code> SMM铝型材年产量 停更271天[MEDIUM] + 稀疏2条[MEDIUM]
  </div>
</section>

<section id="gallery">
  <h2>3. 渲染图表速览（%d 张）</h2>
  <div class="gallery">%s</div>
</section>

<section id="board">
  <h2>4. 全量 32 行复核表（%d 个字段）</h2>
  <div class="note ok"><b>保留项</b>：REVIEW_SKIP 列 32/32 行均为「是(禁自动ID绑定)」；人工结论(待填) 列 32/32 行留白，本版未自动绑定任何指标 ID。表格支持顶部搜索与状态筛选；表头鼠标悬停可看完整字段名。</div>
  <div class="note">
    <b>⚠️ 行定位规则（务必遵守）</b>：源看板 <code>idx</code> 列<b>非全局唯一</b>——<br>
    本表已新增 <code>行号</code>（L1–L32）作为唯一定位键，idx 列后带橙色 <b>!</b> 提示其不可单独使用。<br>
    <b>定位任一记录请用「行号 + 图表短名」二元组</b>，切勿只凭 idx。<br>
    <b>同 zhiji_id 重复行</b>（图表速览中黄色标签标注）需人工确认是否冗余。
  </div>
  <div style="margin:8px 0 12px">
    <button class="btn" id="btnExport">导出人工结论 (.csv)</button>
    <button class="btn btn2" id="btnClear">清空暂存</button>
    <span style="color:#8b949e;font-size:11px">人工结论填写后自动存入浏览器 localStorage，可跨刷新保留；导出为纯文本 | 分隔格式。</span>
  </div>
  <div style="overflow:auto;max-height:78vh">
  <table id="board"><thead><tr>
  <th class="sticky-l">锚点</th><th>状态</th><th>渲染图</th>%s
  </tr></thead><tbody>
  %s
  </tbody></table>
  </div>
</section>

</main>
<footer>HERMES v8.5 review dashboard · 零 zhiji API 调用 · 零后端 · 图片相对路径 renders/</footer>
<script>%s</script>
</body>
</html>""" % (
    CSS, NOW, n_total,
    n_total, n_pass, n_block, n_abstain, n_fetch_ok, n_render_ok, n_redundant,
    n_unit_mismatch, n_unit_conv, n_unified_warn, n_skip_kept, n_total, n_human_blank, n_total,
    n_ok, n_sparse, n_perm, n_dead,
    n_ok, n_sparse, n_perm, n_dead,
    len(warn_rows), warn_nav,
    len(gallery), "\n".join(gallery),
    len(KEY_COLS), THEAD,
    "\n".join(tbody), JS)

DASH = os.path.join(OUT, "review_dashboard.html")
with open(DASH, "w", encoding="utf-8") as f:
    f.write(HTML_DOC)

# ---------- 8. 统计落盘 ----------
IDX_DUP = len([k for k, v in _idx_cnt.items() if v > 1])
summary = {
    "generated_at": NOW,
    "source_board": "fp32_v85_final_filtered_board.csv",
    "source_board_md5": hashlib.md5(open(BOARD_CSV, "rb").read()).hexdigest(),
    "upstream_md5_doc": "/home/ubuntu/analysis/temp/ind_compare_result/交接文档_会话收尾入口_20260928.md",
    "total_rows": n_total,
    "field_count": len(KEY_COLS),
    "idx_unique": len(_idx_cnt),
    "idx_dup_groups": IDX_DUP,
    "dup_zhiji_id_groups": len(DUP_MAP),
    "status": {"正常": n_ok, "稀疏": n_sparse, "权限缺失": n_perm, "数据源下线": n_dead},
    "domain_filter": {"放行": n_pass, "拦截": n_block, "弃权": n_abstain},
    "fetch_render": {"拉取成功": n_fetch_ok, "渲染成功": n_render_ok, "冗余废弃": n_redundant},
    "unit": {"单位冲突(单位匹配=否)": n_unit_mismatch, "已换算": n_unit_conv},
    "warnings": {"unified_warning命中行": n_unified_warn, "看板外告警(仅汇总)": 3},
    "constraints": {"REVIEW_SKIP保留": "%d/%d" % (n_skip_kept, n_total),
                    "人工结论留白": "%d/%d" % (n_human_blank, n_total)},
}
with open(os.path.join(OUT, "dashboard_stats.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(json.dumps(summary, ensure_ascii=False, indent=2))
print("HTML:", DASH, os.path.getsize(DASH), "bytes")
