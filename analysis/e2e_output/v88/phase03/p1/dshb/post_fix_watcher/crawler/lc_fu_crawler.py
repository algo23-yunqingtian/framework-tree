#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lc_fu_crawler.py — LC 碳酸锂期货行情爬虫 (LC_FU00015030)
==========================================================
TASK_ID: V88_PHASE03_P1_DSHB_POST_FIX_WATCHER_EXTEND_JOB (T2)
AGENT:   DSHB | BRANCH: feature/v88-g1

Purpose
-------
采集 1 个高可行性指标:

    LC_FU00015030  碳酸锂期货 (SHFE LC) 主力合约  CNY/tonne

数据源 (候选, 均 verified=False, 上线前必须核实):
    1. 上海期货交易所 SHFE 每日行情 .dat (主源)
       URL 模式: https://www.shfe.com.cn/data/dailydata/kx/lc/lc{YYYYMMDD}.dat
       编码 GBK/GB18030, tab 分隔文本; 非交易日无文件。
       碳酸锂 (LC) 于 2023-07-21 上市。
    2. 东方财富网 (fallback)
       https://data.eastmoney.com/ifdata/lcholding.html   (持仓排名)
       https://quote.eastmoney.com/qihuo/lc2501.html      (合约行情)
       HTML 为 JS 渲染, 原型用正则兜底解析。

输出 (APPEND_ONLY + NO_OVERWRITE):
    external_raw/lc_fu/lc_fu_futures_quote.csv   + .csv.md5
    external_raw/lc_fu/_manifest.jsonl
    logs/lc_fu_crawler_audit.jsonl
    logs/run_results/lc_fu_crawler_<ts>.json

代码映射提示 (重要):
    DB 映射表 v88_phase03_p1_metric_indicator_code_mapping.md 中:
      li_21_close_2         -> LI_FU00015030  (碳酸锂期货收盘价)
      li_21_close_2_p09fix  -> LC_FU00015030  (p09 修正后主映射)
      li_21_openinterest_2  -> LI_HOLD_OPEN   (持仓量, 另一列)
      li_21_openinterest_2_p09fix -> LC_HOLD_OPEN
    因此 FU 系列代码 = 收盘价; 持仓量走 HOLD_OPEN 系列。
    本爬虫同时抓取 close_price / settlement_price / volume / open_interest /
    turnover 五列, 落库时按映射表取用对应列。

约束 (继承任务书):
    NO_ZHIJI_API_CALL  本脚本及依赖库绝不 import / 调用 zhiji_api.py
    NO_OVERWRITE       已存在 CSV 只追加, 永不截断
    APPEND_ONLY        幂等键 (date+indicator_code+contract+source) 命中则跳过
    DRY_RUN            默认 True, http_get 被 common_crawler_lib.DryRunGuard 拦截

Usage
-----
    python lc_fu_crawler.py                                    # dry-run 计划
    python lc_fu_crawler.py --emit-samples                    # dry-run + 合成样本
    python lc_fu_crawler.py --date 2026-10-15                  # 指定交易日
    python lc_fu_crawler.py --all-contracts                    # 抓取全部合约
    python lc_fu_crawler.py --contract LC2501                  # 指定合约
    python lc_fu_crawler.py --verify-urls --live               # 核实候选 URL
    python lc_fu_crawler.py --live --rate-limit 3.0            # 真实抓取
"""

import sys
import re
import json
import argparse
import logging
import time
from pathlib import Path
from collections import OrderedDict
from datetime import date, timedelta

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
SCRIPT_NAME = "lc_fu_crawler"
AUDIT_LOG = LOG_DIR / "lc_fu_crawler_audit.jsonl"
RUN_RESULT_DIR = LOG_DIR / "run_results"

SCHEMA_NAME = "lc_futures_quote"
INDICATOR_CODE = "LC_FU00015030"
OUTPUT_DIR_STEM = "lc_fu"
OUTPUT_FILE = "lc_fu_futures_quote"
DEFAULT_RATE_LIMIT = 3.0
DEFAULT_TIMEOUT = 25.0
DEFAULT_RETRIES = 3
HTTP_BACKOFF = 2.0

# 幂等键: 合约维度独立, 避免同一天不同合约互相覆盖/去重
IDEMPOTENCY_KEY = ["date", "indicator_code", "contract", "source"]

# SHFE 每日行情 .dat 的 GBK 表头关键词 -> 规范化列名
SHFE_HEADER_MAP = [
    ("contract",         ("合约代码", "合约", "品种")),
    ("prev_settle",      ("昨结算",)),
    ("prev_close",       ("昨收",)),
    ("open_price",       ("今开", "开盘价")),
    ("high",             ("最高")),
    ("low",              ("最低")),
    ("settlement_price", ("今结", "结算价")),
    ("close_price",      ("今收", "收盘价")),
    ("change1",          ("涨跌1",)),
    ("change2",          ("涨跌2",)),
    ("volume",           ("成交量",)),
    ("open_interest",    ("持仓量",)),
    ("warrant",          ("仓单",)),
    ("change_qty",       ("增减",)),
    ("turnover",         ("成交额",)),
    ("avg_price",        ("平均价",)),
]

# 碳酸锂合约代码: LC + 1~4 位数字 (LC0 为主力连续, LC2501 = 25年1月)
CONTRACT_RE = re.compile(r"^(LC\d{1,4})$", re.IGNORECASE)
# 东方财富 / 通用 JSON 片段兜底
EM_PRICE_RE = re.compile(
    r'"(?:closePrice|settlementPrice|close|settle)"?\s*[:=]\s*"?([\d.]+)"?')
EM_VOL_RE = re.compile(
    r'"(?:volume|vol)"?\s*[:=]\s*"?([\d,]+)"?')
EM_OI_RE = re.compile(
    r'"(?:openInterest|position|holding)"?\s*[:=]\s*"?([\d,]+)"?')
EM_CONTRACT_RE = re.compile(
    r'"?(?:symbol|contractCode|contract|secuCode)"?\s*[:=]\s*"?((?:LC|lc)\d{1,4})"?')


# =============================================================================
# Parsing
# =============================================================================

def _normalize_shfe_headers(headers):
    """把 SHFE .dat 的中文表头映射成规范化列名。返回 [(orig, canon)]"""
    out = []
    for h in headers:
        hl = str(h).strip()
        canon = None
        for target, kws in SHFE_HEADER_MAP:
            for kw in kws:
                if kw and kw in hl:
                    canon = target
                    break
            if canon:
                break
        out.append((hl, canon))
    return out


def _pick_main_contract(rows):
    """从全部合约行中挑主力合约: 优先 volume 最大, 其次 open_interest 最大。"""
    if not rows:
        return None
    def key(r):
        v = C.parse_number(r.get("volume"))
        oi = C.parse_number(r.get("open_interest"))
        return (v if v is not None else -1, oi if oi is not None else -1)
    return max(rows, key=key)


def parse_shfe_dat(text, trade_date, source, raw_ref, contract_filter=None,
                   all_contracts=False, logger=None):
    """解析 SHFE 每日行情 .dat (tab 分隔, GBK/GB18030 已解码)。

    返回 {"rows": [...], "strategy": str, "candidate_rows": int}
    """
    d = C.parse_date(trade_date)
    rows = []
    if text is None:
        return {"rows": [], "strategy": "shfe_dat", "candidate_rows": 0}

    # 逐行 split: SHFE .dat 每行一个合约, tab 分隔, 第 1 行通常是表头
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return {"rows": [], "strategy": "shfe_dat", "candidate_rows": 0}

    mapped_headers = _normalize_shfe_headers(lines[0].split("\t"))
    canon = {}
    for i, (orig, c) in enumerate(mapped_headers):
        canon.setdefault(c, i)          # 同名取首个列

    def cell(cells, c):
        i = canon.get(c)
        if i is None or i >= len(cells):
            return ""
        return cells[i].strip()

    candidate = 0
    for ln in lines:
        cells = ln.split("\t")
        code = cell(cells, "contract")
        m = CONTRACT_RE.match(code)
        if not m:
            # 无表头或列序不同的情况: 尝试在行内直接找合约代码
            found = None
            for c in cells:
                if CONTRACT_RE.match(c.strip()):
                    found = c.strip()
                    break
            if not found:
                continue
            code = found
            # 无表头时按经验列序解析 (SHFE kx 常见序)
            nums = [C.parse_number(c) for c in cells[1:]]
            nums = [n for n in nums if n is not None]
            close_p = settlement_p = volume_v = oi_v = turnover_v = ""
            if len(nums) >= 4:
                settlement_p, close_p, volume_v, oi_v = nums[0], nums[1], nums[2], nums[3]
            elif len(nums) == 3:
                close_p, volume_v, oi_v = nums
            elif len(nums) == 2:
                close_p, oi_v = nums
            elif len(nums) == 1:
                close_p = nums[0]
            if turnover_v == "" and len(nums) >= 5:
                turnover_v = nums[4]
            candidate += 1
            if contract_filter and code.upper() != contract_filter.upper():
                continue
            rows.append(_lc_row(d, INDICATOR_CODE, code, close_p, settlement_p,
                                volume_v, oi_v, turnover_v, source, raw_ref,
                                "no_header_row"))
            continue

        candidate += 1
        if contract_filter and code.upper() != contract_filter.upper():
            continue
        close_p = cell(cells, "close_price")
        settlement_p = cell(cells, "settlement_price")
        volume_v = cell(cells, "volume")
        oi_v = cell(cells, "open_interest")
        turnover_v = cell(cells, "turnover")
        rows.append(_lc_row(d, INDICATOR_CODE, code, close_p, settlement_p,
                            volume_v, oi_v, turnover_v, source, raw_ref,
                            "header_row"))

    # 主力合约筛选
    if not all_contracts and rows:
        main = _pick_main_contract(rows)
        if main is not None:
            if logger:
                logger.info("SHFE main contract = %s (from %d contract rows)",
                            main.get("contract"), len(rows))
            rows = [main]

    if logger:
        logger.info("PARSE shfe_dat candidates=%d emitted=%d all_contracts=%s",
                    candidate, len(rows), all_contracts)
    return {"rows": rows, "strategy": "shfe_dat", "candidate_rows": candidate}


def _lc_row(trade_date, indicator_code, contract, close_p, settlement_p,
            volume_v, oi_v, turnover_v, source, raw_ref, kind):
    """构造一行 lc_futures_quote。kind = 'contract' | 'main'"""
    return OrderedDict([
        ("date", trade_date.strftime(C.DATE_FMT) if trade_date else ""),
        ("indicator_code", indicator_code),
        ("contract", contract),
        ("close_price", _fmt(close_p)),
        ("settlement_price", _fmt(settlement_p)),
        ("volume", _fmt(volume_v)),
        ("open_interest", _fmt(oi_v)),
        ("turnover", _fmt(turnover_v)),
        ("unit", "CNY/tonne"),
        ("source", source),
        ("fetched_at", C.now_iso()),
        ("raw_ref", raw_ref),
        ("row_kind", kind or "contract"),
    ])


def _fmt(v):
    """数值/字符串 -> CSV 单元格。"""
    if v is None:
        return ""
    if isinstance(v, str):
        v = v.strip()
        if v == "":
            return ""
        n = C.parse_number(v)
        v = n if n is not None else v
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else ("%.2f" % v)
    return str(v)


def _enclosing_object(html, pos):
    """返回覆盖 pos 的 {...} 对象文本 (括号配平)。

    用于把东方财富 JSON 片段中每个合约的字段隔离开来, 避免
    LC2501 的价格窗口里混入 LC2503 的数值。
    """
    start = html.rfind("{", 0, pos)
    if start < 0:
        return html[max(0, pos - 2000):pos + 4000]
    depth = 0
    in_str = False
    for i in range(start, len(html)):
        ch = html[i]
        if ch == '"' and (i == start or html[i - 1] != "\\"):
            in_str = not in_str
        if in_str:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return html[start:i + 1]
    return html[start:start + 4000]


def parse_eastmoney_html(html, trade_date, source, raw_ref, contract_filter=None,
                         all_contracts=False, logger=None):
    """解析东方财富 HTML/JSON 片段 (JS 渲染页面的正则兜底)。

    尽力而为: 抓取页面上所有 LC 合约 token, 并仅在其所属 {...} 对象内
    提取 价格 / 成交量 / 持仓量 (括号配平, 防止跨合约串值)。
    返回 {"rows": [...], "strategy": str, "candidate_rows": int}
    """
    d = C.parse_date(trade_date)
    html = html or ""
    rows = []
    candidate = 0

    for m in EM_CONTRACT_RE.finditer(html):
        c = m.group(1).upper()
        candidate += 1
        if contract_filter and c != contract_filter.upper():
            continue
        window = _enclosing_object(html, m.start())
        prices = [C.parse_number(x) for x in EM_PRICE_RE.findall(window)]
        vols = [C.parse_number(x) for x in EM_VOL_RE.findall(window)]
        ois = [C.parse_number(x) for x in EM_OI_RE.findall(window)]
        rows.append(_lc_row(
            d, INDICATOR_CODE, c,
            prices[0] if prices else "",
            prices[1] if len(prices) > 1 else "",
            vols[0] if vols else "",
            ois[0] if ois else "",
            "", source, raw_ref, "html_row",
        ))

    if not rows:
        # 无合约 token: 退化为单行 (主力) 抓取
        prices = [C.parse_number(x) for x in EM_PRICE_RE.findall(html)]
        vols = [C.parse_number(x) for x in EM_VOL_RE.findall(html)]
        ois = [C.parse_number(x) for x in EM_OI_RE.findall(html)]
        if prices or vols or ois:
            candidate = 1
            rows.append(_lc_row(
                d, INDICATOR_CODE, contract_filter or "LC0",
                prices[0] if prices else "",
                prices[1] if len(prices) > 1 else "",
                vols[0] if vols else "",
                ois[0] if ois else "",
                "", source, raw_ref, "html_row",
            ))

    if not all_contracts and rows:
        main = _pick_main_contract(rows)
        if main is not None:
            rows = [main]

    if logger:
        logger.info("PARSE eastmoney_html contracts=%d emitted=%d",
                    candidate, len(rows))
    return {"rows": rows, "strategy": "eastmoney_html", "candidate_rows": candidate}


# =============================================================================
# Fetch
# =============================================================================

def build_urls(trade_date=None):
    """展开候选 URL: [(source_key, url, kind, referer)]"""
    ind = C.INDICATORS[INDICATOR_CODE]
    ymd = (trade_date or C.today_str()).replace("-", "")
    urls = []
    for key in (ind.get("primary_source"), ind.get("fallback_source")):
        src = C.SOURCE_REGISTRY.get(key)
        if not src:
            continue
        pat = src.get("url_pattern")
        if pat:
            urls.append((key, pat.format(abbr_lower="lc", abbr="LC",
                                          variety="lc", ymd=ymd),
                         "dat", "https://www.shfe.com.cn/"))
        for u in src.get("urls", []):
            kind = "dat" if u.endswith(".dat") else "html"
            urls.append((key, u, kind,
                         "https://www.shfe.com.cn/" if key == "shfe"
                         else "https://data.eastmoney.com/"))
    ihtml = ind.get("html_url")
    if ihtml:
        urls.append((ind.get("fallback_source", "eastmoney"), ihtml, "html",
                     "https://data.eastmoney.com/"))
    seen, out = set(), []
    for k, u, kind, ref in urls:
        if u not in seen:
            seen.add(u)
            out.append((k, u, kind, ref))
    return out


def fetch_indicator(dry_run, logger, rate_limit, timeout, retries,
                    trade_date=None):
    """抓取第一个可用数据源。返回 dict。"""
    urls = build_urls(trade_date)
    result = OrderedDict([
        ("ok", False), ("source", None), ("url", None), ("kind", None),
        ("text", None), ("elapsed_sec", 0.0), ("notes", ""), ("attempts", 0),
    ])
    if not urls:
        result["notes"] = "no candidate URLs registered"
        return result

    for source_key, url, kind, referer in urls:
        result["attempts"] += 1
        if logger:
            logger.info("FETCH %s %s (%s) url=%s %s", INDICATOR_CODE, source_key,
                        kind, url, "dry-run" if dry_run else "live")
        try:
            resp = C.http_get(
                url,
                headers=C.build_headers(),
                timeout=timeout,
                retries=retries,
                backoff=HTTP_BACKOFF,
                dry_run=dry_run,
                logger=logger,
                referer=referer,
            )
        except C.DryRunGuard:
            result.update(ok=False, source=source_key, url=url, kind=kind,
                          notes="dry-run: request not sent")
            if logger:
                logger.info("DRYRUN skip network for %s (%s)" % (INDICATOR_CODE, url))
            return result
        except Exception as e:                            # noqa: BLE001
            result["notes"] = "exception: %s" % e
            if logger:
                logger.error("FETCH exception: %s" % e)
            continue

        result["elapsed_sec"] = resp.elapsed_sec
        if not resp.ok:
            result["notes"] = "http_status=%s" % resp.status
            if logger:
                logger.warning("FETCH status=%s, trying next source", resp.status)
            continue

        body = resp.body_bytes
        if kind == "dat":
            # SHFE .dat 为 GBK/GB18030; 优先显式解码
            text = None
            for enc in ("gb18030", "gbk", "utf-8-sig", "utf-8"):
                try:
                    text = body.decode(enc)
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            if text is None:
                text = body.decode("gb18030", errors="replace")
        else:
            text = resp.body_text
        result.update(ok=True, source=source_key, url=url, kind=kind, text=text)
        if logger:
            logger.info("FETCH OK %d bytes from %s", len(body), source_key)
        return result
    if logger:
        logger.error("FETCH all %d candidate sources failed", result["attempts"])
    return result


# =============================================================================
# Per-run
# =============================================================================

def output_paths(output_root=None):
    root = Path(output_root) if output_root else RAW_DIR
    d = root / OUTPUT_DIR_STEM
    return d, d / ("%s.csv" % OUTPUT_FILE)


def output_paths_samples(output_root=None):
    root = Path(output_root) if output_root else RAW_DIR
    d = root / C.SAMPLES_DIRNAME / OUTPUT_DIR_STEM
    return d, d / ("%s.csv" % OUTPUT_FILE)


def run_one(args, logger, audit, limiter):
    """执行一次 LC 采集。返回结构化结果。"""
    res = OrderedDict([
        ("indicator_code", INDICATOR_CODE),
        ("schema", SCHEMA_NAME),
        ("target_date", args.date),
        ("dry_run", bool(args.dry_run)),
        ("contract_filter", args.contract),
        ("all_contracts", bool(args.all_contracts)),
        ("started_at", C.now_iso()),
        ("ok", False), ("stage", "init"),
        ("rows_fetched", 0), ("rows_written", 0), ("rows_skipped", 0),
        ("file", None), ("checksum", None), ("parse_strategy", None),
        ("main_contract", None), ("error", None),
    ])

    try:
        # --- stage 1: fetch ---
        res["stage"] = "fetch"
        fetched = fetch_indicator(
            dry_run=args.dry_run, logger=logger, rate_limit=args.rate_limit,
            timeout=args.timeout, retries=args.retries, trade_date=args.date)
        res.update({
            "source": fetched.get("source"),
            "url": fetched.get("url"),
            "url_kind": fetched.get("kind"),
            "fetch_elapsed_sec": round(fetched.get("elapsed_sec", 0.0), 3),
            "fetch_attempts": fetched.get("attempts"),
            "fetch_note": fetched.get("notes"),
        })

        text = fetched.get("text")
        rows = []
        if text:
            res["stage"] = "parse"
            kind = fetched.get("kind") or "html"
            if kind == "dat":
                parsed = parse_shfe_dat(
                    text, args.date, str(fetched.get("source") or ""),
                    str(fetched.get("url") or ""),
                    contract_filter=args.contract, all_contracts=args.all_contracts,
                    logger=logger)
            else:
                parsed = parse_eastmoney_html(
                    text, args.date, str(fetched.get("source") or ""),
                    str(fetched.get("url") or ""),
                    contract_filter=args.contract, all_contracts=args.all_contracts,
                    logger=logger)
            rows = parsed.get("rows", [])
            res["parse_strategy"] = parsed.get("strategy")
            res["candidate_rows"] = parsed.get("candidate_rows", 0)
        else:
            res["parse_strategy"] = None
            if args.dry_run:
                res["planned_urls"] = [
                    "%s[%s]: %s" % (k, kind, u) for k, u, kind, _r in
                    build_urls(args.date)]

        # --- dry-run 合成样本 ---
        if not rows and args.dry_run and args.emit_samples:
            res["stage"] = "synthetic_samples"
            rows = C.synthetic_rows(INDICATOR_CODE, SCHEMA_NAME,
                                    n_days=args.sample_days, end_date=args.date,
                                    seed=INDICATOR_CODE)
            res["samples_emitted"] = True
            res["parse_strategy"] = "synthetic"
            if logger:
                logger.info("SAMPLES %s -> %d synthetic rows",
                            INDICATOR_CODE, len(rows))

        res["rows_fetched"] = len(rows)
        res["main_contract"] = rows[0].get("contract") if rows else None
        res["stage"] = "write"

        if rows:
            if args.dry_run and args.emit_samples:
                out_dir, out_csv = output_paths_samples(args.output_root)
                res["dry_run_samples"] = True
            else:
                out_dir, out_csv = output_paths(args.output_root)
            res["file"] = str(out_csv)

            wr = C.write_csv_append_only(
                out_csv, rows, C.SCHEMAS[SCHEMA_NAME]["fieldnames"],
                idempotency_key=IDEMPOTENCY_KEY,
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
                logger.error("WRITE failed: %s" % wr["error"])
                return res

            # --- MD5 快照 + 追加清单 ---
            if wr.get("written", 0) > 0 and out_csv.exists():
                res["stage"] = "md5_snapshot"
                snap = C.write_md5_snapshot(
                    out_csv,
                    extra_meta={"indicator_code": INDICATOR_CODE,
                                "schema": SCHEMA_NAME,
                                "rows_written": wr.get("written", 0),
                                "contract": res.get("main_contract")},
                    logger=logger,
                )
                res["checksum"] = snap.get("checksum")
                res["checksum_size_bytes"] = snap.get("size_bytes")
                res["checksum_sidecar"] = snap.get("_sidecar")
                C.append_manifest(out_dir, [{
                    "indicator_code": INDICATOR_CODE,
                    "file": str(out_csv),
                    "schema": SCHEMA_NAME,
                    "rows_written": wr.get("written", 0),
                    "rows_skipped": wr.get("skipped", 0),
                    "checksum": snap.get("checksum"),
                    "contract": res.get("main_contract"),
                    "source": res.get("source"),
                    "target_date": args.date,
                    "dry_run": bool(args.dry_run),
                    "dry_run_samples": bool(res.get("dry_run_samples")),
                }], logger=logger)
                res["manifest"] = str(out_dir / "_manifest.jsonl")

        limiter.acquire(label="post_%s" % INDICATOR_CODE)

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
            INDICATOR_CODE, res.get("stage"), res["error"]))

    res["finished_at"] = C.now_iso()
    return res


# =============================================================================
# URL verification / reporting
# =============================================================================

def verify_urls(args, logger):
    probes = []
    seen = set()
    for source_key, url, kind, _ref in build_urls(args.date):
        if url in seen:
            continue
        seen.add(url)
        if not args.dry_run:
            C.RateLimiter(args.rate_limit, logger=logger).acquire(label="probe")
        probes.append(C.http_probe_head(url, dry_run=args.dry_run, logger=logger))
    ok_n = sum(1 for p in probes if p.get("reachable"))
    return {"probes": probes, "total": len(probes), "reachable": ok_n,
            "unreachable": len(probes) - ok_n}


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


def print_summary(summary, results):
    lines = []
    lines.append("=" * 100)
    lines.append("LC Futures Crawler — Run Summary")
    lines.append("=" * 100)
    lines.append("TASK_ID    : %s" % summary["task_id"])
    lines.append("AGENT      : %s | BRANCH %s | LIB %s" % (
        summary["agent"], summary["branch"], summary["library_version"]))
    lines.append("TARGET_DATE: %s" % summary.get("target_date"))
    lines.append("DRY_RUN    : %s | ROWS fetched=%d written=%d skipped=%d | %.2fs" % (
        summary["dry_run"], summary["rows_fetched_total"],
        summary["rows_written_total"], summary["rows_skipped_total"],
        summary.get("elapsed_sec", 0.0)))
    lines.append("")
    lines.append("%-14s %-9s %-9s %-7s %-7s %-7s %-12s %-8s %s" % (
        "INDICATOR", "MODE", "STAGE", "FETCH", "WRITTEN", "SKIP",
        "STRATEGY", "CONTRACT", "FILE / NOTE"))
    lines.append("-" * 100)
    for r in results:
        fn = r.get("file") or "-"
        fn = fn.split("\\")[-1].split("/")[-1] if fn != "-" else "-"
        lines.append("%-14s %-9s %-9s %-7d %-7d %-7d %-12s %-8s %s" % (
            r["indicator_code"], r.get("mode", "-"), r.get("stage", "-"),
            r.get("rows_fetched", 0), r.get("rows_written", 0),
            r.get("rows_skipped", 0), str(r.get("parse_strategy") or "-"),
            str(r.get("main_contract") or "-"), fn))
    lines.append("")
    for r in results:
        if r.get("error"):
            lines.append("ERROR %s %s" % (r["indicator_code"], r["error"]))
        elif r.get("planned_urls"):
            lines.append("PLAN  %s %d candidate URL(s):" % (
                r["indicator_code"], len(r["planned_urls"])))
            for u in r["planned_urls"]:
                lines.append("        %s" % u)
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
        description="V88 Phase03 P1 DSHB — LC lithium carbonate futures crawler "
                    "(LC_FU00015030)",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="no network, no writes (default)")
    g.add_argument("--live", "--no-dry-run", dest="dry_run", action="store_false",
                   help="allow real HTTP requests")
    parser.add_argument("--date", default=None, metavar="YYYY-MM-DD",
                        help="target trading date (default: today)")
    parser.add_argument("--emit-samples", action="store_true",
                        help="dry-run only: write synthetic sample CSV under "
                             "external_raw/_dryrun_samples/")
    parser.add_argument("--sample-days", type=int, default=30,
                        help="synthetic sample window in days (default 30)")
    parser.add_argument("--contract", default=None, metavar="CODE",
                        help="only this contract, e.g. LC2501 or LC0")
    parser.add_argument("--all-contracts", action="store_true",
                        help="emit every LC contract row instead of main only")
    parser.add_argument("--output-root", default=None, metavar="DIR",
                        help="override external_raw root")
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
    args.output_root = args.output_root or str(RAW_DIR)

    logger.info("START %s indicator=%s date=%s dry_run=%s emit_samples=%s",
                TASK_ID, INDICATOR_CODE, args.date, args.dry_run,
                args.emit_samples)
    logger.info("CONSTRAINTS %s" % dict(C.CONSTRAINTS))
    logger.info("STDLIB_ONLY (no requests/bs4/lxml) | zhiji_api.py NEVER called")
    logger.info("MAP NOTE FU00015030=close_price; open_interest -> LC_HOLD_OPEN")

    if args.verify_urls:
        probes = verify_urls(args, logger)
        out = OrderedDict([
            ("task_id", TASK_ID), ("script", SCRIPT_NAME),
            ("indicator_code", INDICATOR_CODE),
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
                  "--verify-urls.")
            return 0
        return 0 if probes["reachable"] == probes["total"] else 2

    limiter = C.RateLimiter(args.rate_limit, logger=logger)
    started = time.time()
    results = [run_one(args, logger, audit, limiter)]
    summary = summarize(results)
    summary["elapsed_sec"] = round(time.time() - started, 2)
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

    print_summary(summary, results)

    if not args.dry_run and summary["indicators_failed"] > 0:
        logger.warning("LIVE run completed with %d failed indicator(s)",
                       summary["indicators_failed"])
    if args.dry_run and not args.emit_samples:
        print("\n[note] dry-run produced no files. Use --emit-samples to exercise "
              "write+MD5+DQA, or --live for real HTTP (after --verify-urls).")

    return 0 if (args.dry_run or summary["indicators_ok"] == len(results)) else 3


if __name__ == "__main__":
    C.setup_environment()
    sys.exit(main())
