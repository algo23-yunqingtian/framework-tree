#!/usr/bin/env python3
"""check_html.py — framework-tree 静态页自动验证（P2，v1.0 2026-08-28）。

职责：build 后自动校验 4 个铅 6.x 子页，输出 PASS/FAIL 表格。消灭手工 curl+grep 的低级错误。

校验维度（每页 6 项）：
  1. 文件存在
  2. 字节数在允许区间（防止空文件/截断/异常膨胀）
  3. 图表容器数正确（chart 块数 = 图数）
  4. chart-note 图备注数正确（= 图数，每图一处）
  5. 全部图表 id 已初始化（__inst_<cid>）
  6. 公共 JS 关键函数存在（__seasonalize / __tgl / resize 监听）

用法：
  python3 check_html.py                 # 校验本地文件
  python3 check_html.py --build         # 先重新 build 4 页再校验
  python3 check_html.py --online <url>  # 从线上 URL 拉取后校验（需 --max-time）

退出码：0=全 PASS，1=有 FAIL。
"""
import os, sys, re, subprocess, json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)

# 5 页的期望配置：文件名 / 最小字节 / 图数 / 图表 id 列表
PAGES = {
    "21": {
        "file": "pb_21_price_structure.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_21_c1", "echart_21_c2", "echart_21_c3"],
        "label": "2.1 盘面结构",
        "has_seasonal": True,
    },
    "22": {
        "file": "pb_22_spot_premium.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_22_c1", "echart_22_c2", "echart_22_c3"],
        "label": "2.2 现货与升贴水",
        "has_seasonal": True,
    },
    "23": {
        "file": "pb_23_overseas_price.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_23_c1", "echart_23_c2", "echart_23_c3"],
        "label": "2.3 海外价格",
        "has_seasonal": True,
    },
    "24": {
        "file": "pb_24_spread_system.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_24_c1", "echart_24_c2", "echart_24_c3"],
        "label": "2.4 价差体系",
        "has_seasonal": False,
    },
    "25": {
        "file": "pb_25_valuation_profit.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_25_c1", "echart_25_c2", "echart_25_c3"],
        "label": "2.5 估值与利润",
        "has_seasonal": False,
    },
    "61": {
        "file": "pb_61_raw_material_import.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_61_c1", "echart_61_c2", "echart_61_c3"],
        "label": "6.1 原料进口",
        "has_seasonal": True,   # 有 chart_line_t 图，需校验季节真数据
    },
    "62": {
        "file": "pb_62_import_export.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_62_c1", "echart_62_c2", "echart_62_c3"],
        "label": "6.2 精炼金属进出口",
        "has_seasonal": True,
    },
    "63": {
        "file": "pb_63_product_export.html",
        "min_bytes": 20000,
        "charts": 3,
        "cids": ["echart_63_c1", "echart_63_c2", "echart_63_c3"],
        "label": "6.3 制品出口",
        "has_seasonal": True,
    },
    "64": {
        "file": "pb_64_overseas_shipping.html",
        "min_bytes": 300000,
        "charts": 3,
        "cids": ["echart_64_c1", "echart_64_c2", "echart_64_c3"],
        "label": "6.4 海外对华发运",
        "has_seasonal": False,  # 3 图全为 dual/triple，无季节切换模式
    },
}

# 公共 JS 必须包含的函数/特征（不含季节真数据调用，那项按页类型单独校验）
COMMON_JS_TOKENS = ["function __seasonalizeByYear", "function __tgl", "addEventListener('resize'"]


def run_builds():
    """重新 build 4 页。"""
    scripts = ["build_pb_21.py", "build_pb_61.py", "build_pb_62_demo.py", "build_pb_63.py", "build_pb_64.py"]
    for s in scripts:
        r = subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, s)],
                           cwd=SCRIPT_DIR, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            print("[BUILD FAIL] %s\n%s" % (s, r.stderr))
            return False
    return True


def fetch_online(base_url):
    """从线上拉取 4 页 HTML。返回 {key: html}。用 --max-time 90 防大文件超时。"""
    out = {}
    for k, cfg in PAGES.items():
        url = base_url.rstrip("/") + "/" + cfg["file"]
        r = subprocess.run(["curl", "-s", "--max-time", "90", url], capture_output=True, text=True)
        out[k] = r.stdout if r.returncode == 0 else ""
    return out


def check_page(cfg, html, source):
    """校验单页，返回 [(check_name, ok, detail), ...]"""
    res = []
    size = len(html.encode("utf-8"))
    # 1. 文件/内容存在
    res.append(("内容非空", bool(html.strip()), "%s (%s)" % (source, size)))
    # 2. 字节数下限
    res.append(("字节≥%d" % cfg["min_bytes"], size >= cfg["min_bytes"], "%d 字节" % size))
    # 3. 图表容器数
    n_chart = len(re.findall(r'<div class="chart">', html))
    res.append(("chart 容器=%d" % cfg["charts"], n_chart == cfg["charts"], "实际 %d" % n_chart))
    # 4. chart-note 图备注数
    n_note = html.count('class="chart-note"')
    res.append(("chart-note=%d" % cfg["charts"], n_note == cfg["charts"], "实际 %d" % n_note))
    # 5. 图表 id 初始化
    missing = [c for c in cfg["cids"] if ("__inst_%s" % c) not in html]
    res.append(("全部 cid 已 __inst", not missing, "缺 %s" % missing if missing else "3/3 OK"))
    # 6. 公共 JS 关键函数
    miss_js = [t for t in COMMON_JS_TOKENS if t not in html]
    res.append(("公共 JS 完整", not miss_js, "缺 %s" % miss_js if miss_js else "3/3 OK"))
    # 7. 季节真数据（仅含 chart_line_t 的页）
    if cfg.get("has_seasonal"):
        # v1.1：季节视图改用 __seasonalizeByYear(data, years, palette) 产出历年 series
        ok = ("window.__seasonalizeByYear" in html and "__yrs_" in html and "__pal_" in html)
        res.append(("季节真数据 __seasonalizeByYear", ok,
                    "缺失：可能未用新的历年 series 函数"))
    else:
        res.append(("季节真数据", True, "本页无季节模式，跳过"))
    # 额外：echarts 引用
    res.append(("echarts.min.js 引用", "assets/echarts.min.js" in html, ""))
    # 额外：指标版本（跟随 indicators_v1.json 实际版本，v1.x/v2.x 均通过）
    has_ver = bool(re.search(r"indicators_v1\.json v\d+\.\d+", html))
    res.append(("indicators_v1.json 版本", has_ver, ""))
    return res


def main():
    online = False
    base_url = None
    do_build = False
    for i, a in enumerate(sys.argv[1:]):
        if a == "--build":
            do_build = True
        elif a == "--online":
            online = True
            base_url = sys.argv[i + 2]
        elif a == "--help":
            print(__doc__)
            return 0

    print("=" * 74)
    print("framework-tree 静态页校验 (check_html.py v1.0)")
    print("=" * 74)

    if do_build:
        print("\n[BUILD] 重新 build 4 页 ...")
        if not run_builds():
            print("[ABORT] build 失败")
            return 1
        print("[BUILD] OK\n")

    if online:
        htmls = fetch_online(base_url)
        print("[SOURCE] 线上 %s\n" % base_url)
    else:
        htmls = {}
        for k, cfg in PAGES.items():
            p = os.path.join(ROOT, cfg["file"])
            if os.path.exists(p):
                with open(p, encoding="utf-8") as f:
                    htmls[k] = f.read()
            else:
                htmls[k] = ""
        print("[SOURCE] 本地 %s\n" % ROOT)

    all_ok = True
    rows = []
    for k, cfg in PAGES.items():
        html = htmls.get(k, "")
        res = check_page(cfg, html, "local") if not online else check_page(cfg, html, "online")
        ok = all(r[1] for r in res)
        all_ok = all_ok and ok
        rows.append((k, cfg["label"], ok, res))

    # 输出表格
    print("%-4s %-16s %-6s %s" % ("页", "名称", "结果", "明细"))
    print("-" * 74)
    for k, label, ok, res in rows:
        print("%-4s %-16s %-6s" % (k, label, "✅PASS" if ok else "❌FAIL"))
        for name, good, detail in res:
            print("        %s %-22s %s" % ("·" if good else "!", name, detail if not good else ""))
        print()

    print("=" * 74)
    print("总结: %d/%d 页通过  →  %s" % (sum(1 for r in rows if r[2]), len(rows),
                                         "✅ 全部 PASS" if all_ok else "❌ 存在 FAIL"))
    print("=" * 74)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())