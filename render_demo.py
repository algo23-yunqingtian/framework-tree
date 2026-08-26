import sys, json, urllib.request, urllib.error

def fetch(metric):
    try:
        r = urllib.request.urlopen(f"http://127.0.0.1:8787/api/indicator?code=PB&metric={metric}", timeout=40)
        return json.loads(r.read())
    except Exception as e:
        return {"points": [], "error": str(e)}

METRICS = [
    ("i1","交易所库存","LME铅库存(吨)","吨"),
    ("i2","仓单","SHFE铅仓单(吨)","吨"),
    ("i3","社会库存","SMM铅锭五地社库(万吨)","万吨"),
    ("i4","工厂库存","原生铅成品库存(万吨)","万吨"),
    ("i5","隐性·在途","进口铅精矿港口库存(万吨)","万吨"),
]

def stats(pts):
    if not pts: return None
    valid=[p for p in pts if p.get('value') is not None]
    if len(valid)<2: return None
    def v(p):
        try: return float(p['value'])
        except: return None
    vals=[(p['date'],v(p)) for p in valid if v(p) is not None]
    if len(vals)<2: return None
    # valid 是倒序(最新在前),所以最新=vals[0]
    lst=vals[0]; wk=vals[7] if len(vals)>=8 else vals[-1]; mo=vals[29] if len(vals)>=30 else vals[-1]; yr=vals[249] if len(vals)>=250 else vals[-1]
    def chg(a,b):
        if a is None or b is None or b==0: return 0
        return (a-b)/b*100
    def fmt(x): return f"{x:,.2f}" if abs(x)<100 else f"{x:,.0f}"
    return dict(
        latest=fmt(lst[1]), ldate=lst[0], lval=lst[1],
        wk=chg(lst[1],wk[1]), mo=chg(lst[1],mo[1]), yr=chg(lst[1],yr[1]),
        count=len(valid),
        spark=[(p[0],p[1]) for p in vals[-60:]],
    )

rows=[]
for m,name,full,unit in METRICS:
    d=fetch(m)
    s=stats(d['points'])
    rows.append((m,name,full,s,d.get('source'),d.get('error')))
    if s:
        print(f"[{m}] {name} | 最新 {s['latest']} {unit} ({s['ldate']}) | 周{s['wk']:+.1f}% 月{s['mo']:+.1f}% 年{s['yr']:+.1f}% | {s['count']}点")
    else:
        print(f"[{m}] {name} | 无数据: {d.get('error')}")

# 写一份带数据的迷你图表 HTML 演示页(同色系,反拷贝)
def spark_line(spark):
    if not spark: return "", "", 320, 60
    pts=[(d,v) for d,v in spark]
    vmin=min(v for _,v in pts); vmax=max(v for _,v in pts)
    if vmax==vmin: vmax=vmin+1
    W,H=320,60
    path_parts=[]; area_parts=[]
    for i,(d,v) in enumerate(pts):
        x = (i/(len(pts)-1)*W) if len(pts)>1 else (W/2)
        y = H-((v-vmin)/(vmax-vmin))*H
        op = "M" if i==0 else "L"
        path_parts.append(op+"{:.1f},{:.1f}".format(x,y))
        area_parts.append(op+"{:.1f},{:.1f}".format(x,y))
    path = "".join(path_parts)
    area = "M0,{H} ".format(H=H) + " ".join(area_parts) + " L{W},{H} Z".format(W=W, H=H)
    return path, area, W, H

html=['<html><head><meta charset="UTF-8"><style>','body{font-family:-apple-system,"Segoe UI","PingFang SC",sans-serif;background:#1e2128;color:#dcdcdc;margin:0;padding:24px}','h1{color:#b0a38a;font-size:18px;font-weight:600;margin:0 0 6px}h2{color:#8b8171;font-size:13px;font-weight:400;margin:0 0 20px}','grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:16px}','card{background:#282c34;border:1px solid #3a3f4b;border-radius:8px;padding:16px}','card h3{font-size:13px;color:#b0a38a;margin:0 0 2px;display:flex;justify-content:space-between}','card .sub{font-size:11px;color:#6f6a5d;margin-bottom:14px}','nums{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin:10px 0 12px}','ncell{background:#1e2128;border-radius:5px;padding:8px 10px}','ncell .lbl{font-size:10px;color:#6f6a5d}','ncell .val{font-size:17px;font-weight:600}up{color:#4caf50}dn{color:#f44336}','svg{display:block;width:100%;height:60px}','.src{font-size:10px;color:#6f6a5d;margin-top:8px;letter-spacing:1px}','.err{color:#f44336;font-size:11px}','.meta{font-size:11px;color:#8b8171;margin-bottom:14px}','</style></head><body>','<h1>▮▮ 有色金属研究框架 · 铅(PB)库存看板</h1>','<h2>API 8787 实时数据 · 2026-08-26 · 本地演示(图表待接入 ECharts)</h2>','<div class="grid">']

for m,name,full,s,src,err in rows:
    html.append('<div class="card"><h3>'+full+' <span style="font-size:10px;color:#6f6a5d">4.'+m[-1]+'</span></h3><div class="sub">'+name+' · '+src+'</div>')
    if err:
        html.append('<div class="err">⚠️ '+err+'</div>')
    elif s:
        wkcl='up' if s['wk']>=0 else 'dn'; mocl='up' if s['mo']>=0 else 'dn'; yrcl='up' if s['yr']>=0 else 'dn'
        html.append(f'<div class="nums"><div class="ncell"><div class="lbl">最新值</div><div class="val">{s["latest"]}</div></div><div class="ncell"><div class="lbl">日期</div><div class="val" style="font-size:13px">{s["ldate"]}</div></div>')
        html.append(f'<div class="ncell"><div class="lbl">周变化</div><div class="val {wkcl}">{s["wk"]:+.1f}%</div></div><div class="ncell"><div class="lbl">月变化</div><div class="val {mocl}">{s["mo"]:+.1f}%</div></div>')
        html.append(f'<div class="ncell"><div class="lbl">年变化</div><div class="val {yrcl}">{s["yr"]:+.1f}%</div></div><div class="ncell"><div class="lbl">数据点</div><div class="val">{s["count"]}</div></div></div>')
        path,area,W,H=spark_line(s['spark'])
        html.append(f'<svg viewBox="0 0 {W} {H}"><path d="{area}" fill="rgba(176,163,138,0.18)"/><path d="{path}" fill="none" stroke="#b0a38a" stroke-width="1.5"/></svg>')
    html.append(f'<div class="src">API: /api/indicator?code=PB&metric={m} · {src}</div></div>')

html.append('</div></body></html>')

open('/home/ubuntu/framework-tree/pb_stock_demo.html','w',encoding='utf-8').write('\n'.join(html))
print('\n✅ 演示页已生成: /home/ubuntu/framework-tree/pb_stock_demo.html')
