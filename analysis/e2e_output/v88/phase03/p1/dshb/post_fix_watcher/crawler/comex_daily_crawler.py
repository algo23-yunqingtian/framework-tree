#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
comex_daily_crawler.py — COMEX 仓单库存日度爬虫 (COMEX_AL/NI/PB/SN/ZN)
========================================================================
TASK_ID: V88_PHASE03_P1_DSHB_POST_FIX_WATCHER_EXTEND_JOB (T2)
AGENT:   DSHB | BRANCH: feature/v88-g1

Purpose
-------
采集 5 个高可行性 COMEX 仓单库存指标:

    COMEX_AL  铝 (Aluminium)   metric_tonnes
    COMEX_NI  镍 (Nickel)     metric_tonnes
    COMEX_PB  铅 (Lead)       metric_tonnes
    COMEX_SN  锡 (Tin)        metric_tonnes
    COMEX_ZN  锌 (Zinc)       metric_tonnes

数据源 (候选, 均 verified=False, 上线前必须核实):
    1. LME Stocks & Warrants  — https://www.lme.com/en/metals/non-ferrous/stocks-and-warrants
       LME 每日库存按仓库(warehouse)拆分, 含美国 COMEX 仓库条目。
    2. CME Group COMEX Storage — https://www.cmegroup.com/en-us/markets/metal/storage.html
       (许可受限, 作为 fallback)

输出 (APPEND_ONLY + NO_OVERWRITE):
    external_raw/comex_al/comex_al_receipts.csv      + .csv.md5
    external_raw/comex_ni/comex_ni_receipts.csv      + .csv.md5
    external_raw/comex_pb/comex_pb_receipts.csv      + .csv.md5
    external_raw/comex_sn/comex_sn_receipts.csv      + .csv.md5
    external_raw/comex_zn/comex_zn_receipts.csv      + .csv.md5
    external_raw/comex_<m>/_manifest.jsonl           (每次写入的追加审计)
    logs/comex_daily_crawler_audit.jsonl             (运行审计)
    logs/comex_daily_crawler_<ts>.json               (单次运行结构化结果)

约束 (继承任务书):
    NO_ZHIJI_API_CALL  本脚本及依赖库绝不 import / 调用 zhiji_api.py
    NO_OVERWRITE       已存在 CSV 只追加, 永不截断
    APPEND_ONLY        幂等键 (date+indicator_code+source) 命中则跳过
    DRY_RUN            默认 True, http_get 被 common_crawler_lib.DryRunGuard 拦截

Usage
-----
    # 默认: 全部 5 个指标, dry-run, 不落盘 (打印计划)
    python comex_daily_crawler.py

    # dry-run + 落合成样本 (供 DQA 冒烟测试, 写入 external_raw/_dryrun_samples/)
    python comex_daily_crawler.py --emit-samples

    # 只跑两个指标, 指定交易日
    python comex_daily_crawler.py --indicators COMEX_AL COMEX_ZN --date 2026-10-15

    # 真实抓取 (需显式 --live; 上线前先用 --verify-urls 核实 URL)
    python comex_daily_crawler.py --live --rate-limit 3.0

    # 仅核实候选 URL 可达性 (不发正式抓取请求)
    python comex_daily_crawler.py --verify-urls --live
"""

import sys
import re
import json
import argparse
import logging
import time
from pathlib import Path
from collections import OrderedDict

# ---- 公共库 (同目录) ----
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_crawler_lib as C            # noqa: E402

# =============================================================================
# Configuration
# =============================================================================

TASK_ID = C.TASK_ID
AGENT = C.AGENT
BRANCH = C.BRANCH

CRAWLER_DIR = C.CRAWLER_DIR
RAW_DIR = C.RAW_DIR
LOG_DIR = C.LOG_DIR
SCRIPT_NAME = "comex_daily_crawler"
AUDIT_LOG = LOG_DIR / "comex_daily_crawler_audit.jsonl"
RUN_RESULT_DIR = LOG_DIR / "run_results"

SCHEMA_NAME = "comex_warehouse_receipts"
OUTPUT_FILE_SUFFIX = "receipts"          # -> comex_al_receipts.csv
DEFAULT_RATE_LIMIT = 3.0                # 秒, 相邻请求最小间隔
DEFAULT_TIMEOUT = 25.0
DEFAULT_RETRIES = 3
HTTP_BACKOFF = 2.0

# 5 个目标指标 (顺序即抓取顺序)
COMEX_INDICATORS = ["COMEX_AL", "COMEX_NI", "COMEX_PB", "COMEX_SN", "COMEX_ZN"]


# =============================================================================
# Parsing — 多策略防御式解析
# =============================================================================
#
# 说明: 由于候选 URL 的页面结构尚未核实 (verified=False), 解析器必须对任意
# HTML 都不崩溃, 并尽力提取 (date, 数值...) 对。任何策略失败都降级为 0 行 +
# 警告, 绝不抛异常中断整批。
# =============================================================================

DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{4}/\d{2}/\d{2}|\d{1,2}/\d{1,2}/\d{4})\b")
# 数值 token: 要求小数点后必须有数字, 避免吞入句末孤立点号 ("12,500.")
NUM_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
TR_RE = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
TD_RE = re.compile(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", re.IGNORECASE | re.DOTALL)
# 策略 A 的扫描窗口在遇到「行边界」时截断, 防止把下一行的数值并进当前日期
ROW_BOUNDARY_RE = re.compile(r"\n|</tr\s*>|</table\s*>|;", re.IGNORECASE)


def _cells_from_row_html(row_html):
    """从 <tr>...</tr> 内提取单元格文本列表。"""
    cells = []
    for m in TD_RE.finditer(row_html):
        txt = C.strip_tags(m.group(1))
        txt = txt.replace("&nbsp;", " ").replace("&#160;", " ").replace("&amp;", "&")
        txt = txt.strip()
        if txt:
            cells.append(txt)
    return cells


def _strategy_a_date_anchored(html):
    """策略 A: 以日期为锚点, 向后扫描窗口内的数值 (仅散文/混排文本)。

    窗口在行边界 (\\n, </tr>, </table>, ;) 处截断, 避免跨行污染。
    返回 [(date_str, [numbers...]), ...]
    """
    out = []
    seen = set()
    for m in DATE_RE.finditer(html or ""):
        dstr = m.group(1)
        if dstr in seen:
            continue
        seen.add(dstr)
        window = html[m.end():m.end() + 400]
        b = ROW_BOUNDARY_RE.search(window)
        if b:
            window = window[:b.start()]
        # 排除窗口内的日期片段, 再取数值
        window_no_date = DATE_RE.sub(" ", window)
        nums = [C.parse_number(n) for n in NUM_RE.findall(window_no_date)]
        nums = [n for n in nums if n is not None]
        # 过滤明显不是库存量级的噪声 (年份/百分比基数)
        nums = [n for n in nums if abs(n) >= 1]
        if nums:
            out.append((dstr, nums))
    return out


def _strategy_b_html_table(html):
    """策略 B: 解析 <table> 结构。

    保留: 单元格数 >= 2 且含可解析日期 + 至少一个数值 的行。
    返回 [(date_str, [numbers...]), ...]
    """
    out = []
    for tr in TR_RE.finditer(html or ""):
        cells = _cells_from_row_html(tr.group(1))
        if len(cells) < 2:
            continue
        dm = None
        for c in cells:
            if DATE_RE.fullmatch(c.strip()):
                dm = c.strip()
                break
        if not dm:
            continue
        nums = []
        for c in cells:
            if c.strip() == dm:
                continue
            n = C.parse_number(c)
            if n is not None and abs(n) >= 1:
                nums.append(n)
        if nums:
            out.append((dm, nums))
    return out


def _strategy_c_delimited(html):
    """策略 C: 定宽/TSV/CSV 文本 (用于 PDF/CSV 导出附件)。"""
    out = []
    lines = (html or "").splitlines()
    for ln in lines:
        stripped = ln.strip()
        if not stripped:
            continue
        delim = "\t" if "\t" in stripped else ("," if "," in stripped else None)
        parts = stripped.split(delim) if delim else C.strip_tags(stripped).split()
        dm = None
        for p in parts:
            p = p.strip().strip('"')
            if DATE_RE.fullmatch(p):
                dm = p
                break
        if not dm:
            continue
        nums = []
        for p in parts:
            p = p.strip().strip('"')
            if p == dm:
                continue
            n = C.parse_number(p)
            if n is not None and abs(n) >= 1:
                nums.append(n)
        if nums:
            out.append((dm, nums))
    return out


PARSE_STRATEGIES = [
    ("A_date_anchored", _strategy_a_date_anchored),
    ("B_html_table", _strategy_b_html_table),
    ("C_delimited", _strategy_c_delimited),
]


def sniff_strategy_order(html):
    """按内容嗅探决定策略优先级。

    * 含 <tr>           -> 先试 HTML 表格 (结构化, 列序最可靠)
    * 含 \\t 或大量逗号  -> 再试定分隔文本 (SHFE .dat / CSV 导出)
    * 其余              -> 散文日期锚点
    全部策略最终都会作为兜底依次尝试。
    """
    h = html or ""
    low = h.lower()
    order = []
    if "<tr" in low:
        order.append("B_html_table")
    if "\t" in h or low.count(",") >= 5:
        order.append("C_delimited")
    order.append("A_date_anchored")
    for name in [n for n, _ in PARSE_STRATEGIES]:
        if name not in order:
            order.append(name)
    return order


def parse_stocks_page(html, indicator_code, metal_abbr, source, raw_ref,
                      logger=None):
    """把原始 HTML/文本解析成 SCHEMAS[comex_warehouse_receipts] 行。

    最佳努力列映射 (页面结构待核实的过渡方案):
        1 个数值 -> closing_stocks
        2 个数值 -> (closing_stocks, net_change)
        3 个数值 -> (on_warrant, off_warrant, closing_stocks)
        4+ 数值  -> (on_warrant, off_warrant, net_change, closing_stocks)

    返回 {"rows": [...], "strategy": str|None, "candidate_rows": int}
    """
    by_name = dict(PARSE_STRATEGIES)
    for name in sniff_strategy_order(html):
        fn = by_name.get(name)
        if fn is None:
            continue
        try:
            pairs = fn(html)
        except Exception as e:                            # noqa: BLE001
            if logger:
                logger.warning("PARSE %s strategy=%s failed: %s",
                               indicator_code, name, e)
            continue
        pairs = [p for p in pairs if p[1]]
        if not pairs:
            continue
        rows = _map_pairs_to_rows(pairs, indicator_code, metal_abbr,
                                  source, raw_ref)
        if logger:
            logger.info("PARSE %s strategy=%s pairs=%d rows=%d",
                        indicator_code, name, len(pairs), len(rows))
        return {"rows": rows, "strategy": name, "candidate_rows": len(pairs)}
    if logger:
        logger.warning("PARSE %s no strategy produced rows (page structure "
                       "likely unverified)", indicator_code)
    return {"rows": [], "strategy": None, "candidate_rows": 0}


def _map_pairs_to_rows(pairs, indicator_code, metal_abbr, source, raw_ref):
    rows = []
    for dstr, nums in pairs:
        d = C.parse_date(dstr)
        if d is None:
            continue
        n = len(nums)
        on_w = off_w = net = close = ""
        if n == 1:
            close = nums[0]
        elif n == 2:
            close, net = nums[0], nums[1]
        elif n == 3:
            on_w, off_w, close = nums[0], nums[1], nums[2]
        else:
            on_w, off_w, net, close = nums[0], nums[1], nums[2], nums[3]
        rows.append(OrderedDict([
            ("date", d.strftime(C.DATE_FMT)),
            ("indicator_code", indicator_code),
            ("metal_abbr", metal_abbr),
            ("warehouse", "COMEX_US"),
            ("on_warrant", _fmt(on_w)),
            ("off_warrant", _fmt(off_w)),
            ("net_change", _fmt(net)),
            ("closing_stocks", _fmt(close)),
            ("unit", "metric_tonnes"),
            ("source", source),
            ("fetched_at", C.now_iso()),
            ("raw_ref", raw_ref),
        ]))
    return rows


def _fmt(v):
    """数值 -> CSV 单元格字符串 (整数去小数点)。"""
    if v == "" or v is None:
        return ""
    f = float(v)
    return str(int(f)) if f.is_integer() else ("%.2f" % f)


# =============================================================================
# Fetch
# =============================================================================

def build_urls(indicator_code, target_date=None):
    """按注册表展开候选 URL 列表。返回 [(source_key, url), ...]"""
    ind = C.INDICATORS.get(indicator_code)
    if not ind:
        return []
    urls = []
    abbr = ind.get("abbr", "")
    for key in (ind.get("primary_source"), ind.get("fallback_source")):
        if not key:
            continue
        src = C.SOURCE_REGISTRY.get(key)
        if not src:
            continue
        for u in src.get("urls", []):
            urls.append((key, u))
        pat = src.get("url_pattern")
        if pat:
            urls.append((key, pat.format(abbr_lower=abbr.lower(), abbr=abbr,
                                          ymd=(target_date or C.today_str())
                                          .replace("-", ""))))
        # 指标级 URL / URL pattern
    iurl = ind.get("url")
    if iurl and not urls:
        urls.append((ind.get("primary_source", "unknown"), iurl))
    ipat = ind.get("url_pattern")
    if ipat:
        urls.append((ind.get("primary_source", "unknown"),
                     ipat.format(abbr_lower=abbr.lower(), abbr=abbr)))
    # 去重保序
    seen, out = set(), []
    for k, u in urls:
        if u not in seen:
            seen.add(u)
            out.append((k, u))
    return out


def fetch_indicator(indicator_code, dry_run, logger, rate_limit, timeout,
                    retries, target_date=None):
    """抓取第一个可用数据源。返回 dict:

    {indicator_code, ok, source, url, html, elapsed_sec, notes, attempts}
    """
    urls = build_urls(indicator_code, target_date)
    result = OrderedDict([
        ("indicator_code", indicator_code),
        ("ok", False), ("source", None), ("url", None),
        ("html", None), ("elapsed_sec", 0.0),
        ("notes", ""), ("attempts", 0),
    ])
    if not urls:
        result["notes"] = "no candidate URLs registered"
        if logger:
            logger.warning("FETCH %s %s", indicator_code, result["notes"])
        return result

    for source_key, url in urls:
        result["attempts"] += 1
        src = C.SOURCE_REGISTRY.get(source_key, {})
        rl = float(src.get("rate_limit_sec", rate_limit))
        if logger:
            logger.info("FETCH %s -> %s (%s) url=%s",
                        indicator_code, source_key, url, "dry-run" if dry_run else "live")
        try:
            resp = C.http_get(
                url,
                timeout=timeout,
                retries=retries,
                backoff=HTTP_BACKOFF,
                dry_run=dry_run,
                logger=logger,
            )
        except C.DryRunGuard:
            result["ok"] = False
            result["source"] = source_key
            result["url"] = url
            result["notes"] = "dry-run: request not sent"
            if logger:
                logger.info("DRYRUN skip network for %s (%s)" % (
                    indicator_code, url))
            return result
        except Exception as e:                            # noqa: BLE001
            result["notes"] = "exception: %s" % e
            if logger:
                logger.error("FETCH %s exception: %s" % (indicator_code, e))
            continue

        result["elapsed_sec"] = resp.elapsed_sec
        if not resp.ok:
            result["notes"] = "http_status=%s" % resp.status
            if logger:
                logger.warning("FETCH %s status=%s, trying next source",
                               indicator_code, resp.status)
            continue

        result.update(ok=True, source=source_key, url=url, html=resp.body_text)
        if logger:
            logger.info("FETCH %s OK %d bytes from %s",
                        indicator_code, len(resp.body_bytes), source_key)
        return result
    if logger:
        logger.error("FETCH %s all %d candidate sources failed",
                     indicator_code, result["attempts"])
    return result


# =============================================================================
# Per-indicator run
# =============================================================================

def output_paths(indicator_code, output_root=None):
    """返回 (dir, csv_path)。dry-run 样本走 _dryrun_samples 子树。"""
    ind = C.INDICATORS[indicator_code]
    stem = "comex_%s" % ind["abbr"].lower()
    root = Path(output_root) if output_root else RAW_DIR
    d = root / stem
    return d, d / ("%s_%s.csv" % (stem, OUTPUT_FILE_SUFFIX))


def output_paths_samples(indicator_code, output_root=None):
    stem = "comex_%s" % C.INDICATORS[indicator_code]["abbr"].lower()
    root = Path(output_root) if output_root else RAW_DIR
    d = root / C.SAMPLES_DIRNAME / stem
    return d, d / ("%s_%s.csv" % (stem, OUTPUT_FILE_SUFFIX))


def run_one(indicator_code, args, logger, audit, limiter):
    """执行单个指标采集。返回结构化结果 dict。"""
    ind = C.INDICATORS[indicator_code]
    res = OrderedDict([
        ("indicator_code", indicator_code),
        ("schema", SCHEMA_NAME),
        ("target_date", args.date),
        ("dry_run", bool(args.dry_run)),
        ("started_at", C.now_iso()),
        ("ok", False), ("stage", "init"),
        ("rows_fetched", 0), ("rows_written", 0), ("rows_skipped", 0),
        ("file", None), ("checksum", None), ("parse_strategy", None),
        ("error", None),
    ])

    try:
        # --- stage 1: fetch (dry-run 下被 DryRunGuard 拦截) ---
        res["stage"] = "fetch"
        fetched = fetch_indicator(
            indicator_code,
            dry_run=args.dry_run,
            logger=logger,
            rate_limit=args.rate_limit,
            timeout=args.timeout,
            retries=args.retries,
            target_date=args.date,
        )
        res.update({
            "source": fetched.get("source"),
            "url": fetched.get("url"),
            "fetch_elapsed_sec": round(fetched.get("elapsed_sec", 0.0), 3),
            "fetch_attempts": fetched.get("attempts"),
            "fetch_note": fetched.get("notes"),
        })

        html = fetched.get("html")
        rows = []
        if html:
            res["stage"] = "parse"
            parsed = parse_stocks_page(
                html, indicator_code, ind["abbr"],
                str(fetched.get("source") or ""),
                str(fetched.get("url") or ""), logger=logger)
            rows = parsed.get("rows", [])
            res["parse_strategy"] = parsed.get("strategy")
            res["candidate_rows"] = parsed.get("candidate_rows", 0)
        else:
            res["parse_strategy"] = None
            if args.dry_run:
                # 计划模式: 打印将要请求的候选 URL 列表
                res["planned_urls"] = [u for _k, u in build_urls(
                    indicator_code, args.date)]

        # --- dry-run 合成样本 (仅当显式 --emit-samples) ---
        if not rows and args.dry_run and args.emit_samples:
            res["stage"] = "synthetic_samples"
            rows = C.synthetic_rows(indicator_code, SCHEMA_NAME,
                                    n_days=args.sample_days,
                                    end_date=args.date, seed=indicator_code)
            res["samples_emitted"] = True
            res["parse_strategy"] = "synthetic"
            if logger:
                logger.info("SAMPLES %s -> %d synthetic rows",
                            indicator_code, len(rows))

        res["rows_fetched"] = len(rows)
        res["stage"] = "write"

        if rows:
            if args.dry_run and args.emit_samples:
                out_dir, out_csv = output_paths_samples(
                    indicator_code, args.output_root)
                res["dry_run_samples"] = True
            else:
                out_dir, out_csv = output_paths(indicator_code, args.output_root)
            res["file"] = str(out_csv)

            wr = C.write_csv_append_only(
                out_csv, rows,
                C.SCHEMAS[SCHEMA_NAME]["fieldnames"],
                dry_run=(not args.emit_samples) if args.dry_run else False,
                logger=logger,
            )
            res.update({
                "rows_written": wr.get("written", 0),
                "rows_skipped": wr.get("skipped", 0),
                "file_created": wr.get("file_created", False),
            })
            if wr.get("error"):
                res["error"] = wr["error"]
                logger.error("WRITE %s failed: %s", indicator_code, wr["error"])
                return res

            # --- MD5 快照 (每次写入后) ---
            if wr.get("written", 0) > 0 and out_csv.exists():
                res["stage"] = "md5_snapshot"
                snap = C.write_md5_snapshot(
                    out_csv,
                    extra_meta={"indicator_code": indicator_code,
                                "schema": SCHEMA_NAME,
                                "rows_written": wr.get("written", 0)},
                    logger=logger,
                )
                res["checksum"] = snap.get("checksum")
                res["checksum_size_bytes"] = snap.get("size_bytes")
                res["checksum_sidecar"] = snap.get("_sidecar")

                # --- 追加清单 (APPEND_ONLY) ---
                C.append_manifest(out_dir, [{
                    "indicator_code": indicator_code,
                    "file": str(out_csv),
                    "schema": SCHEMA_NAME,
                    "rows_written": wr.get("written", 0),
                    "rows_skipped": wr.get("skipped", 0),
                    "checksum": snap.get("checksum"),
                    "source": res.get("source"),
                    "target_date": args.date,
                    "dry_run": bool(args.dry_run),
                    "dry_run_samples": bool(res.get("dry_run_samples")),
                }], logger=logger)
                res["manifest"] = str(out_dir / "_manifest.jsonl")

        # --- 限流: 每个指标一次 acquire ---
        limiter.acquire(label="post_%s" % indicator_code)

        # 模式化成功判定:
        #   plan    (dry-run, 无样本)  -> 只要无异常即视为计划成功
        #   samples (dry-run+样本)     -> 以 rows_written>0 判定
        #   live    (--live)           -> 以 rows_written>0 判定
        if args.dry_run and not args.emit_samples:
            res["mode"] = "plan"
            res["ok"] = (res["error"] is None)
        elif args.dry_run and args.emit_samples:
            res["mode"] = "samples"
            res["ok"] = (res["rows_written"] > 0)
        else:
            res["mode"] = "live"
            res["ok"] = (res["rows_written"] > 0)
        res["stage"] = "done"
    except Exception as e:                                # noqa: BLE001
        res["error"] = "%s: %s" % (type(e).__name__, e)
        res["ok"] = False
        logger.error("RUN %s failed at stage=%s: %s" % (
            indicator_code, res.get("stage"), res["error"]))

    res["finished_at"] = C.now_iso()
    return res


# =============================================================================
# URL verification
# =============================================================================

def verify_urls(args, logger):
    """对全部候选 URL 做可达性探测。--live 才真正发请求。"""
    probes = []
    seen = set()
    for code in COMEX_INDICATORS:
        for source_key, url in build_urls(code, args.date):
            if url in seen:
                continue
            seen.add(url)
            if not args.dry_run:
                limiter = C.RateLimiter(args.rate_limit, logger=logger)
                limiter.acquire(label="probe")
            probes.append(C.http_probe_head(url, dry_run=args.dry_run,
                                            logger=logger))
    ok_n = sum(1 for p in probes if p.get("reachable"))
    return {"probes": probes, "total": len(probes), "reachable": ok_n,
            "unreachable": len(probes) - ok_n}


# =============================================================================
# Reporting
# =============================================================================

def summarize(results):
    return OrderedDict([
        ("task_id", TASK_ID),
        ("agent", AGENT),
        ("branch", BRANCH),
        ("script", SCRIPT_NAME),
        ("library_version", C.LIB_VERSION),
        ("constraints", dict(C.CONSTRAINTS)),
        ("indicators_total", len(results)),
        ("indicators_ok", sum(1 for r in results if r.get("ok"))),
        ("indicators_failed", sum(1 for r in results if not r.get("ok"))),
        ("rows_fetched_total", sum(r.get("rows_fetched", 0) for r in results)),
        ("rows_written_total", sum(r.get("rows_written", 0) for r in results)),
        ("rows_skipped_total", sum(r.get("rows_skipped", 0) for r in results)),
        ("dry_run", all(r.get("dry_run") for r in results)),
    ])


def print_summary(summary, results, logger=None):
    lines = []
    lines.append("=" * 100)
    lines.append("COMEX Daily Crawler — Run Summary")
    lines.append("=" * 100)
    lines.append("TASK_ID    : %s" % summary["task_id"])
    lines.append("AGENT      : %s | BRANCH %s | LIB %s" % (
        summary["agent"], summary["branch"], summary["library_version"]))
    lines.append("TARGET_DATE: %s" % summary.get("target_date"))
    lines.append("DRY_RUN    : %s | ROWS fetched=%d written=%d skipped=%d | %.2fs" % (
        summary["dry_run"], summary["rows_fetched_total"],
        summary["rows_written_total"], summary["rows_skipped_total"],
        summary.get("elapsed_sec", 0.0)))
    lines.append("Indicators : %d total / %d ok / %d failed" % (
        summary["indicators_total"], summary["indicators_ok"],
        summary["indicators_failed"]))
    lines.append("")
    lines.append("%-12s %-8s %-9s %-6s %-8s %-9s %-8s %s" % (
        "INDICATOR", "MODE", "STAGE", "FETCH", "WRITTEN", "SKIPPED",
        "STRATEGY", "FILE / NOTE"))
    lines.append("-" * 100)
    for r in results:
        fn = (r.get("file") or "-")
        fn = fn.split("\\")[-1].split("/")[-1] if fn != "-" else "-"
        lines.append("%-12s %-8s %-9s %-6d %-8d %-9d %-8s %s" % (
            r["indicator_code"], r.get("mode", "-"), r.get("stage", "-"),
            r.get("rows_fetched", 0), r.get("rows_written", 0),
            r.get("rows_skipped", 0),
            str(r.get("parse_strategy") or "-"), fn))
    lines.append("")
    for r in results:
        if r.get("error"):
            lines.append("ERROR %-12s %s" % (r["indicator_code"], r["error"]))
        elif r.get("planned_urls"):
            lines.append("PLAN  %-12s %d candidate URL(s): %s" % (
                r["indicator_code"], len(r["planned_urls"]),
                ", ".join(r["planned_urls"][:2]) +
                (" ..." if len(r["planned_urls"]) > 2 else "")))
    lines.append("-" * 100)
    txt = "\n".join(lines)
    print(txt)
    return txt


# =============================================================================
# Main
# =============================================================================

def main():
    C.setup_environment()
    parser = argparse.ArgumentParser(
        description="V88 Phase03 P1 DSHB — COMEX warehouse receipts daily crawler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Indicators: %s" % ", ".join(COMEX_INDICATORS))
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="no network, no writes (default)")
    g.add_argument("--live", "--no-dry-run", dest="dry_run", action="store_false",
                   help="allow real HTTP requests")
    parser.add_argument("--indicators", nargs="+", default=None, metavar="CODE",
                        choices=COMEX_INDICATORS,
                        help="subset of indicators to run (default: all 5)")
    parser.add_argument("--date", default=None, metavar="YYYY-MM-DD",
                        help="target trading date (default: today)")
    parser.add_argument("--emit-samples", action="store_true",
                        help="dry-run only: write synthetic sample CSVs under "
                             "external_raw/_dryrun_samples/ for DQA smoke test")
    parser.add_argument("--sample-days", type=int, default=30,
                        help="synthetic sample window in days (default 30)")
    parser.add_argument("--output-root", default=None, metavar="DIR",
                        help="override external_raw root (default: "
                             "%(default)s)")
    parser.add_argument("--rate-limit", type=float, default=DEFAULT_RATE_LIMIT,
                        help="min seconds between requests (default %(default)s)")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help="HTTP timeout seconds (default %(default)s)")
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES,
                        help="HTTP retries (default %(default)s)")
    parser.add_argument("--verify-urls", action="store_true",
                        help="only probe candidate URL reachability and exit")
    parser.add_argument("--json-out", default=None, metavar="FILE",
                        help="write full run result JSON to FILE")
    parser.add_argument("--no-audit", action="store_true",
                        help="do not append to audit JSONL")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logger = C.get_logger(SCRIPT_NAME, level=logging.DEBUG if args.verbose
                          else logging.INFO)
    audit = None
    if not args.no_audit:
        audit = C.JsonlAudit(AUDIT_LOG, logger=logger)

    args.date = args.date or C.today_str()
    targets = args.indicators or COMEX_INDICATORS
    args.output_root = args.output_root or str(RAW_DIR)

    logger.info("START %s indicators=%s date=%s dry_run=%s emit_samples=%s",
                TASK_ID, ",".join(targets), args.date, args.dry_run,
                args.emit_samples)
    logger.info("CONSTRAINTS %s" % dict(C.CONSTRAINTS))
    logger.info("STDLIB_ONLY (no requests/bs4/lxml) | zhiji_api.py NEVER called")

    # ---- URL verification only ----
    if args.verify_urls:
        probes = verify_urls(args, logger)
        out = OrderedDict([
            ("task_id", TASK_ID), ("script", SCRIPT_NAME),
            ("verified_at", C.now_iso()), ("dry_run", bool(args.dry_run)),
            ("total_urls", probes["total"]), ("reachable", probes["reachable"]),
            ("unreachable", probes["unreachable"]),
            ("probes", probes["probes"]),
        ])
        text = json.dumps(out, indent=2, ensure_ascii=False, default=str)
        print(text)
        if args.json_out:
            C.ensure_dir(Path(args.json_out).parent)
            with open(args.json_out, "w", encoding="utf-8") as f:
                f.write(text)
        if audit:
            audit.append({"event": "verify_urls",
                          "total": probes["total"], "reachable": probes["reachable"],
                          "dry_run": bool(args.dry_run)})
        logger.info("VERIFY_URLS total=%d reachable=%d (dry_run=%s)",
                    probes["total"], probes["reachable"], args.dry_run)
        if args.dry_run:
            print("\n[note] dry-run: no probe actually sent. Re-run with --live "
                  "--verify-urls to test real reachability.")
            return 0
        return 0 if probes["reachable"] == probes["total"] else 2

    # ---- main run ----
    limiter = C.RateLimiter(args.rate_limit, logger=logger)
    started = time.time()
    results = []
    for i, code in enumerate(targets):
        if i > 0:
            limiter.acquire(label="pre_%s" % code)
        results.append(run_one(code, args, logger, audit, limiter))
    elapsed = time.time() - started

    summary = summarize(results)
    summary["elapsed_sec"] = round(elapsed, 2)
    summary["target_date"] = args.date
    summary["started_at"] = C.now_iso()
    full = OrderedDict([("summary", summary), ("results", results)])
    text = json.dumps(full, indent=2, ensure_ascii=False, default=str)

    if args.json_out:
        C.ensure_dir(Path(args.json_out).parent)
        with open(args.json_out, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info("RESULT_JSON -> %s" % args.json_out)

    if audit:
        audit.append({"event": "run", **{k: v for k, v in summary.items()}})

    print_summary(summary, results, logger=logger)

    if not args.dry_run and summary["indicators_failed"] > 0:
        logger.warning("LIVE run completed with %d failed indicator(s)",
                       summary["indicators_failed"])
    if args.dry_run and not args.emit_samples:
        print("\n[note] dry-run produced no files. Use --emit-samples to exercise "
              "the write+MD5+DQA pipeline with synthetic data, or --live for "
              "real HTTP (after --verify-urls).")

    # 退出码: 0 = 全部成功或 dry-run; 3 = 有失败指标
    return 0 if (args.dry_run or summary["indicators_ok"] == len(results)) else 3


if __name__ == "__main__":
    C.setup_environment()
    sys.exit(main())
