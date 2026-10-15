#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
common_crawler_lib.py — 外部数据爬虫公共库 (External Crawler Shared Library)
=============================================================================
TASK_ID: V88_PHASE03_P1_DSHB_POST_FIX_WATCHER_EXTEND_JOB (T2 / T3)
AGENT:   DSHB | BRANCH: feature/v88-g1

Purpose
-------
为 COMEX 仓单 (COMEX_AL/NI/PB/SN/ZN) 与 LC 碳酸锂期货 (LC_FU00015030)
外部爬虫提供统一的公共能力:

  * UA 轮换 (User-Agent rotation)          -> USER_AGENTS / random_user_agent()
  * HTTP 请求 (超时/重试/退避)              -> http_get()           [默认不执行]
  * 速率限制 (可配置 sleep)                 -> RateLimiter
  * MD5 文件校验和 + 快照                   -> md5_file() / write_md5_snapshot()
  * CSV schema 校验 + 只追加写入            -> validate_csv() / write_csv_append_only()
  * 只追加清单 (_manifest.json)             -> append_manifest()
  * 结构化日志 + JSONL 审计                 -> get_logger() / JsonlAudit
  * 指标 / 数据源注册表                     -> INDICATORS / SOURCE_REGISTRY

Hard Constraints (inherited from task brief)
--------------------------------------------
  NO_ZHIJI_API_CALL = True   本库与所有爬虫一律不调用 zhiji_api.py。
  NO_OVERWRITE      = True   绝不截断/覆盖已存在的输出文件。
  APPEND_ONLY       = True   新数据只追加; 幂等键命中则跳过, 不重写历史行。
  DRY_RUN           = True   http_get() 默认被 DryRunGuard 拦截, 不发起真实网络请求。
                             真实请求必须由调用方显式传 dry_run=False 才能发生。

Python 环境: Python 3.8+ / Windows, 仅使用标准库 (urllib.request, csv, hashlib,
re, logging, json ...) — 无 requests / BeautifulSoup / lxml。

Usage
-----
  from common_crawler_lib import (
      USER_AGENTS, random_user_agent, http_get, RateLimiter,
      md5_file, write_md5_snapshot, validate_csv, write_csv_append_only,
      append_manifest, get_logger, JsonlAudit, now_iso, ensure_dir,
      INDICATORS, SOURCE_REGISTRY, SCHEMAS,
  )

  # 库自身可执行自检:
  python common_crawler_lib.py --selftest
"""

import os
import sys
import platform
import time
import random
import hashlib
import logging
import argparse
import csv
import json
import socket
import re
from pathlib import Path
from datetime import datetime, date, timedelta
from collections import OrderedDict
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# =============================================================================
# 0. Hard constraints (module-level, machine readable)
# =============================================================================

CONSTRAINTS = OrderedDict([
    ("NO_ZHIJI_API_CALL", True),   # 严禁调用 zhiji_api.py
    ("NO_OVERWRITE", True),        # 严禁截断/覆盖已有输出
    ("APPEND_ONLY", True),         # 仅追加, 幂等去重
    ("DRY_RUN_DEFAULT", True),     # http_get 默认被拦截
    ("STD_LIB_ONLY", True),        # 仅标准库
])

TASK_ID = "V88_PHASE03_P1_DSHB_POST_FIX_WATCHER_EXTEND_JOB"
AGENT = "DSHB"
BRANCH = "feature/v88-g1"
LIB_VERSION = "1.0.0"

# =============================================================================
# 1. Platform setup (Windows UTF-8)
# =============================================================================

def setup_environment():
    """Windows 下强制 UTF-8 控制台编码。幂等, 可重复调用。"""
    if platform.system() == "Windows":
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")
        os.environ.setdefault("PYTHONUNBUFFERED", "1")
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except AttributeError:
                pass
            except Exception:
                pass


# =============================================================================
# 2. Time helpers
# =============================================================================

ISO_FMT = "%Y-%m-%dT%H:%M:%S"
DATE_FMT = "%Y-%m-%d"


def now_iso():
    """当前时间 ISO8601 字符串 (秒精度, 无时区后缀 — 与仓库既有脚本保持一致)。"""
    return datetime.now().strftime(ISO_FMT)


def today_str():
    """今天 YYYY-MM-DD。"""
    return datetime.now().strftime(DATE_FMT)


def parse_date(value):
    """宽松日期解析 -> datetime.date。失败返回 None。

    接受: YYYY-MM-DD / YYYY/MM/DD / YYYYMMDD / Excel 序列号 (1900 epoch)。
    """
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    s = str(value).strip()
    if not s:
        return None
    for fmt in (DATE_FMT, "%Y/%m/%d", "%Y%m%d", "%Y.%m.%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    # Excel serial number (1 = 1900-01-01)
    try:
        n = float(s.replace(",", ""))
        if 20000 < n < 60000:
            return date(1899, 12, 30) + timedelta(days=int(n))
    except (ValueError, OverflowError):
        pass
    return None


def parse_number(value):
    """宽松数值解析 -> float。空串/不可解析返回 None。

    自动剥离逗号千分位、空格、百分号、括号负数 (会计写法)。
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s:
        return None
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]
    s = s.replace(",", "").replace(" ", "").replace("%", "").replace("\u00a0", "")
    # 容忍尾部孤立的分隔符 ("12,500." / "12,500," / "12.500.") 与前置小数点
    s = re.sub(r"[.,]+$", "", s)
    if s.startswith(".") and not s.startswith(".-") and not s.startswith("+-"):
        s = "0" + s
    m = re.fullmatch(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", s)
    if not m:
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if negative else v


# =============================================================================
# 3. Path / FS helpers
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
CRAWLER_DIR = SCRIPT_DIR
RAW_DIR = CRAWLER_DIR / "external_raw"
LOG_DIR = SCRIPT_DIR / "logs"
SAMPLES_DIRNAME = "_dryrun_samples"   # dry-run 合成样本子目录前缀, DQA 默认跳过


def ensure_dir(path):
    """确保目录存在 (含父目录), 返回 Path。"""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_name(name):
    """文件名安全化: 仅保留 [A-Za-z0-9_.-], 其余转下划线。"""
    return re.sub(r"[^A-Za-z0-9_.-]", "_", str(name))


# =============================================================================
# 4. Logging
# =============================================================================

def get_logger(name, level=logging.INFO, fmt=None):
    """返回配置好的 logger。默认输出到 stderr, 时间戳前缀。"""
    lg = logging.getLogger(name)
    lg.setLevel(level)
    lg.propagate = False
    fmt = fmt or "%(asctime)s [%(levelname)s] %(name)s :: %(message)s"
    if not lg.handlers:
        h = logging.StreamHandler(sys.stderr)
        h.setFormatter(logging.Formatter(fmt))
        lg.addHandler(h)
    return lg


class JsonlAudit(object):
    """JSONL 追加审计日志。APPEND_ONLY: 只追加, 永不截断。

    每行一个 JSON 对象; 写入前 flush, 崩溃不丢已确认行。
    """

    def __init__(self, path, logger=None):
        self.path = Path(path)
        ensure_dir(self.path.parent)
        self.logger = logger
        # 单进程写入无需真锁; 保留字段供多进程扩展。
        self._lock_serial = True

    def append(self, entry):
        if not isinstance(entry, dict):
            entry = {"value": entry}
        entry.setdefault("ts", now_iso())
        ensure_dir(self.path.parent)
        with open(str(self.path), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
            f.flush()
            os.fsync(f.fileno())
        if self.logger:
            self.logger.info("AUDIT %s" % json.dumps(
                entry, ensure_ascii=False, default=str))
        return entry

    def read_all(self):
        if not self.path.exists():
            return []
        rows = []
        with open(str(self.path), "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        rows.append({"_raw_line": line, "_parse_error": True})
        return rows


# =============================================================================
# 5. User-Agent rotation
# =============================================================================

USER_AGENTS = [
    # Chrome / Windows 11
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    # Chrome / macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    # Firefox / Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    # Safari / macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    # Edge / Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
    # Chrome / Linux (服务器侧抓取常见 UA)
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36",
    # 声明式 bot UA (部分站点要求显式声明; 用于有 robots.txt 的公开数据站)
    "Mozilla/5.0 (compatible; V88-DSHB-ResearchCrawler/1.0; +https://research.local/crawler)",
]

_UA_IDX = {"i": 0}


def random_user_agent(seed=None, sequential=False):
    """返回一个 UA。

    sequential=True 时轮转 (可预测, 便于审计); 默认按 seed/随机选择。
    """
    if sequential:
        ua = USER_AGENTS[_UA_IDX["i"] % len(USER_AGENTS)]
        _UA_IDX["i"] += 1
        return ua
    if seed is not None:
        rnd = random.Random(seed)
    else:
        rnd = random
    return rnd.choice(USER_AGENTS)


def build_headers(ua=None, accept=None, referer=None, extra=None):
    """构造请求头。默认声明 UA + Accept + Accept-Language + Connection。"""
    h = OrderedDict()
    h["User-Agent"] = ua or random_user_agent()
    h["Accept"] = accept or "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    h["Accept-Language"] = "zh-CN,zh;q=0.9,en;q=0.8"
    h["Accept-Encoding"] = "identity"          # identity: 不做 gzip, 避免额外解码依赖
    h["Connection"] = "close"
    h["Cache-Control"] = "no-cache"
    if referer:
        h["Referer"] = referer
    if extra:
        for k, v in extra.items():
            h[k] = v
    return h


# =============================================================================
# 6. Rate limiting
# =============================================================================

class RateLimiter(object):
    """简单时间间隔限流器。

    RateLimiter(3.0) -> 相邻两次 acquire() 至少间隔 3 秒。
    线程内单调计时, 不阻塞非调用方。
    """

    def __init__(self, min_interval_sec=3.0, logger=None, jitter_pct=0.15):
        self.min_interval = float(min_interval_sec)
        self.jitter = float(jitter_pct)
        self.logger = logger
        self._last = 0.0

    def acquire(self, label=""):
        now = time.time()
        target = self._last + self.min_interval
        wait = target - now
        if wait > 0:
            jitter = wait * self.jitter * random.uniform(-1.0, 1.0)
            sleep_for = max(0.0, wait + jitter)
            if self.logger:
                self.logger.info(
                    "RATELIMIT %.2fs -> %.2fs (%s)" % (wait, sleep_for, label))
            time.sleep(sleep_for)
        self._last = time.time()
        return self._last


# =============================================================================
# 7. Dry-run guard + HTTP
# =============================================================================

class DryRunGuard(Exception):
    """dry-run 模式下调用 http_get 触发。非错误 — 属预期路径。"""


class HttpResponse(object):
    """统一的 HTTP 响应封装。"""

    def __init__(self, url, status, headers, body_bytes, elapsed_sec, final_url=None):
        self.url = url
        self.status = status
        self.headers = headers or {}
        self.body_bytes = body_bytes
        self.elapsed_sec = elapsed_sec
        self.final_url = final_url or url

    @property
    def body_text(self):
        for enc in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
            try:
                return self.body_bytes.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return self.body_bytes.decode("utf-8", errors="replace")

    @property
    def ok(self):
        return 200 <= int(self.status or 0) < 400

    def __repr__(self):
        return "HttpResponse(%d, %d bytes, %.2fs)" % (
            self.status, len(self.body_bytes or b""), self.elapsed_sec)


def make_request(url, headers, method="GET", data=None):
    req = Request(url, data=data)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    req.get_method = lambda m=method: m
    return req


def http_get(url, headers=None, timeout=20.0, retries=3, backoff=2.0,
             dry_run=True, logger=None, session=None, referer=None):
    """HTTP GET。

    dry_run=True (默认) 时 **不发起任何网络请求**, 抛出 DryRunGuard。
    dry_run=False 时才通过 urllib.request 真实请求, 带 UA 轮换/超时/指数退避重试。

    返回 HttpResponse。永不向外抛出网络异常 — 失败返回 HttpResponse(status=0)
    或 (retry 耗尽后) 最后一次失败信息, 调用方据 .ok 判断。
    """
    if dry_run:
        raise DryRunGuard("dry-run mode: no HTTP request sent for %s" % url)

    headers = build_headers(ua=(headers or {}).get("User-Agent"),
                            accept=(headers or {}).get("Accept"),
                            referer=referer or (headers or {}).get("Referer"))
    last_err = None
    last_status = 0
    opener = session
    for attempt in range(1, int(retries) + 1):
        started = time.time()
        try:
            if opener is None:
                resp = urlopen(make_request(url, headers), timeout=timeout)
                body = resp.read()
                status = getattr(resp, "status", None) or resp.getcode()
                hdrs = dict(resp.getheaders())
                final_url = resp.geturl()
                resp.close()
            else:
                with opener.open(make_request(url, headers), timeout=timeout) as resp:
                    body = resp.read()
                    status = resp.status
                    hdrs = dict(resp.headers.items())
                    final_url = resp.url
            elapsed = time.time() - started
            r = HttpResponse(url, status, hdrs, body, elapsed, final_url)
            if r.ok:
                if logger:
                    logger.info("HTTP OK %d %s (%d bytes, %.2fs)" % (
                        status, url, len(body), elapsed))
                return r
            last_err = "HTTP %d" % status
            last_status = status
        except DryRunGuard:
            raise
        except (HTTPError) as e:
            last_err = "HTTPError %s" % e
            last_status = e.code
            # 4xx 不重试 (除 429)
            if 400 <= e.code < 500 and e.code != 429:
                if logger:
                    logger.error("HTTP %d not retried: %s" % (e.code, url))
                return HttpResponse(url, e.code, dict(e.headers or {}),
                                    getattr(e, "read", lambda: b"")() or b"",
                                    time.time() - started)
        except (URLError, socket.timeout, socket.error, TimeoutError) as e:
            last_err = "%s: %s" % (type(e).__name__, e)
            last_status = 0
        except Exception as e:                       # noqa: BLE001
            last_err = "%s: %s" % (type(e).__name__, e)
            last_status = 0
        if attempt < retries:
            sleep_for = backoff * (2 ** (attempt - 1))
            if logger:
                logger.warning(
                    "HTTP retry %d/%d after %.1fs (%s) :: %s" % (
                        attempt, retries, sleep_for, last_err, url))
            time.sleep(sleep_for)
    if logger:
        logger.error("HTTP FAILED after %d tries: %s :: %s" % (retries, last_err, url))
    return HttpResponse(url, last_status, {}, b"", 0.0)


def http_probe_head(url, dry_run=True, logger=None, timeout=10.0):
    """URL 可达性探测 (HEAD, 回退 GET)。仅用于 --verify-urls, 默认 dry-run。

    返回 dict: {url, reachable, status, verified_at, note}
    """
    result = {"url": url, "reachable": False, "status": 0,
              "verified_at": now_iso(), "note": ""}
    if dry_run:
        result["note"] = "dry-run: probe skipped"
        return result
    headers = build_headers()
    for method in ("HEAD", "GET"):
        try:
            req = make_request(url, headers, method=method)
            resp = urlopen(req, timeout=timeout)
            status = getattr(resp, "status", None) or resp.getcode()
            result.update(reachable=(200 <= status < 500), status=status,
                          note="%s -> %d" % (method, status))
            try:
                resp.close()
            except Exception:
                pass
            if result["reachable"]:
                return result
        except Exception as e:                       # noqa: BLE001
            result["note"] = "%s: %s" % (method, type(e).__name__)
    if logger:
        logger.warning("PROBE unreachable: %s (%s)" % (url, result["note"]))
    return result


# =============================================================================
# 8. MD5 checksum + snapshot
# =============================================================================

MD5_CHUNK = 1024 * 1024
MD5_SNAPSHOT_SUFFIX = ".md5"


def md5_bytes(data):
    return hashlib.md5(data).hexdigest()


def md5_file(path, chunk_size=MD5_CHUNK):
    """文件 MD5 (十六进制小写)。文件不存在返回 None。"""
    p = Path(path)
    if not p.exists():
        return None
    h = hashlib.md5()
    with open(str(p), "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def write_md5_snapshot(data_path, snapshot_dir=None, snapshot_name=None,
                       algo="md5", extra_meta=None, logger=None):
    """写 MD5 快照。返回快照 dict。

    两种输出:
      1. 旁路快照文件  <data>.md5  (内容: "<md5>  <basename>\n" — md5sum 兼容格式)
      2. 附加元数据    {file, md5, size, mtime, algo, computed_at}
    快照写入为覆盖写 (快照本身是派生元数据, 不是原始数据; 原始 CSV 仍 APPEND_ONLY)。
    """
    p = Path(data_path)
    if not p.exists():
        return {"file": str(p), "error": "not_found"}
    digest = md5_file(p)
    size = p.stat().st_size
    mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime(ISO_FMT)
    info = OrderedDict([
        ("file", str(p.relative_to(CRAWLER_DIR)) if str(p).startswith(str(CRAWLER_DIR)) else str(p)),
        ("algo", algo),
        ("checksum", digest),
        ("size_bytes", size),
        ("mtime", mtime),
        ("computed_at", now_iso()),
    ])
    if extra_meta:
        for k, v in extra_meta.items():
            info[k] = v

    # 1) 旁路 .md5 文件 (md5sum 兼容)
    sidecar = p.with_suffix(p.suffix + MD5_SNAPSHOT_SUFFIX)
    ensure_dir(sidecar.parent)
    with open(str(sidecar), "w", encoding="ascii") as f:
        f.write("%s  %s\n" % (digest, p.name))

    # 2) 可选独立 JSON 快照
    if snapshot_dir is not None:
        snap_dir = ensure_dir(snapshot_dir)
        nm = snapshot_name or (p.name + ".json")
        with open(str(snap_dir / nm), "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2, ensure_ascii=False)

    info["_sidecar"] = str(sidecar)
    if logger:
        logger.info("MD5SNAP %s %s (%d bytes)" % (digest, p.name, size))
    return info


# =============================================================================
# 9. Indicator / source registry
# =============================================================================
#
# 说明:
#   * 本注册表是「原型」配置。所有外部 URL 均为候选模式, verified=False。
#     上线前必须用 --verify-urls 或人工访问逐一核实 (见设计文档第 5 节)。
#   * 不调用 zhiji_api.py; 所有取值都来自公开网页 / 公开接口。
# =============================================================================

SOURCE_REGISTRY = OrderedDict([
    ("lme", OrderedDict([
        ("name", "LME (London Metal Exchange) — Stocks & Warrants"),
        ("kind", "html+pdf"),
        ("rate_limit_sec", 3.0),
        ("urls", [
            "https://www.lme.com/en/metals/non-ferrous/stocks-and-warrants",
            "https://www.lme.com/en/metals/non-ferrous/stocks-and-warrants/lme-weekly-stock-table",
        ]),
        ("notes", "LME 每日库存与仓单报告, 按仓库(warehouse)拆分明细, "
                  "含美国 COMEX 仓库条目。页面为 JS 渲染, 需 fallback 到 PDF/CSV 导出。"),
        ("verified", False),
    ])),
    ("cme_comex", OrderedDict([
        ("name", "CME Group — COMEX Storage / Warehouse Receipts"),
        ("kind", "html+json"),
        ("rate_limit_sec", 3.0),
        ("urls", [
            "https://www.cmegroup.com/en-us/markets/metal/storage.html",
            "https://www.cmegroup.com/cme-services/market-data/reports.html",
        ]),
        ("notes", "COMEX 仓库仓单/库存报告。CME 对批量数据有访问限制, 需评估许可。"),
        ("verified", False),
    ])),
    ("shfe", OrderedDict([
        ("name", "上海期货交易所 (SHFE) — 每日行情 .dat"),
        ("kind", "dat_text"),
        ("rate_limit_sec", 3.0),
        # SHFE 真实公开路径模式: /data/dailydata/kx/<variety_lower>/<variety><YYYYMMDD>.dat
        ("url_pattern", "https://www.shfe.com.cn/data/dailydata/kx/{variety}/{variety}{ymd}.dat"),
        ("urls", [
            "https://www.shfe.com.cn/reports/tradedata/dailydata/",
        ]),
        ("notes", "SHFE 每日行情为 GBK/GB18030 编码 tab 分隔文本 (.dat)。"
                  "碳酸锂 (LC) 自 2023-07-21 上市。非交易日无文件。"),
        ("verified", False),
    ])),
    ("eastmoney", OrderedDict([
        ("name", "东方财富网 — 期货持仓排名 / 行情"),
        ("kind", "html+json_api"),
        ("rate_limit_sec", 2.0),
        ("urls", [
            "https://data.eastmoney.com/ifdata/lcholding.html",
            "https://quote.eastmoney.com/qihuo/lc2501.html",
        ]),
        ("api_pattern", "https://datacenter-web.eastmoney.com/api/data/v1/get?"
                        "{params}"),
        ("notes", "datacenter-web API 需 reportName + columns + filter, "
                  "参数模式未核实; HTML 页面为 JS 渲染, 原型使用正则兜底解析。"),
        ("verified", False),
    ])),
])


# 6 个高可行性指标注册表
INDICATORS = OrderedDict()

for _metal, _abbr, _unit, _note in [
    ("COMEX_AL", "AL", "metric_tonnes", "铝 (Aluminium) — COMEX/美国仓库仓单库存"),
    ("COMEX_NI", "NI", "metric_tonnes", "镍 (Nickel) — COMEX/美国仓库仓单库存"),
    ("COMEX_PB", "PB", "metric_tonnes", "铅 (Lead) — COMEX/美国仓库仓单库存"),
    ("COMEX_SN", "SN", "metric_tonnes", "锡 (Tin) — COMEX/美国仓库仓单库存"),
    ("COMEX_ZN", "ZN", "metric_tonnes", "锌 (Zinc) — COMEX/美国仓库仓单库存"),
]:
    INDICATORS[_metal] = OrderedDict([
        ("abbr", _abbr),
        ("indicator_id_mapped", _metal),
        ("target_value_column", "closing_stocks"),
        ("unit", _unit),
        ("collect_frequency", "daily"),
        ("primary_source", "lme"),
        ("fallback_source", "cme_comex"),
        ("url", "https://www.lme.com/en/metals/non-ferrous/stocks-and-warrants"),
        ("url_pattern",
         "https://www.lme.com/en/metals/non-ferrous/stocks-and-warrants"
         "?metal={abbr_lower}&warehouse=COMEX"),
        ("regex_selectors", [
            r"(\d{4}-\d{2}-\d{2})[^\d]{1,40}([\d,]+)",
        ]),
        ("xpath_selectors", []),
        ("collection_notes", _note),
        ("feasibility", "high"),
        ("verified", False),
        ("db_indicator_id_placeholder", "placeholder_comex%s" % _abbr.lower()),
        ("db_commodity", _abbr.lower()),
    ])

INDICATORS["LC_FU00015030"] = OrderedDict([
    ("abbr", "LC"),
    ("indicator_id_mapped", "LC_FU00015030"),
    ("target_value_column", "close_price"),
    ("unit", "CNY/tonne"),
    ("collect_frequency", "daily"),
    ("primary_source", "shfe"),
    ("fallback_source", "eastmoney"),
    ("url", "https://www.shfe.com.cn/reports/tradedata/dailydata/"),
    ("url_pattern",
     "https://www.shfe.com.cn/data/dailydata/kx/lc/lc{ymd}.dat"),
    ("html_url", "https://data.eastmoney.com/ifdata/lcholding.html"),
    ("regex_selectors", [
        # SHFE .dat: 合约代码\t... 行内 tab 分隔字段
        r"^(LC\d{3,6})\t(.*)$",
        # eastmoney HTML 行情片段兜底
        r'"(?:closePrice|close)":"?([\d.]+)"?',
    ]),
    ("xpath_selectors", []),
    ("collection_notes",
     "碳酸锂期货 (Shanghai LC) 主力合约。"
     "注意: 代码 FU00015030 在 DB 映射表中对应「收盘价」(li_21_close_2 -> LI_FU00015030), "
     "「持仓量」对应 LC_HOLD_OPEN / LI_HOLD_OPEN; 本爬虫同时抓取两者, 落库时按映射表选择列。"),
    ("feasibility", "high"),
    ("verified", False),
    ("db_indicator_id_placeholder", "li_21_close_2_p09fix"),
    ("db_commodity", "li"),
])


# =============================================================================
# 10. CSV schemas + validation
# =============================================================================

# 通用外部原始数据 CSV 规范 (所有爬虫输出必须兼容)
CSV_CONVENTIONS = OrderedDict([
    ("required_columns", ["date", "indicator_code", "value", "unit",
                          "source", "fetched_at"]),
    ("date_column", "date"),
    ("idempotency_key", ["date", "indicator_code", "source"]),
    ("encoding", "utf-8"),
    ("delimiter", ","),
    ("quotechar", '"'),
    ("line_terminator", "\n"),
])

SCHEMAS = OrderedDict()

# COMEX 仓单: 日期 + 金属 + 仓库 + 转入/转出/净变动/期末库存
SCHEMAS["comex_warehouse_receipts"] = OrderedDict([
    ("fieldnames", ["date", "indicator_code", "metal_abbr", "warehouse",
                    "on_warrant", "off_warrant", "net_change",
                    "closing_stocks", "unit", "source", "fetched_at", "raw_ref"]),
    ("required_columns", ["date", "indicator_code", "closing_stocks",
                          "unit", "source", "fetched_at"]),
    ("date_columns", ["date"]),
    ("numeric_columns", ["on_warrant", "off_warrant", "net_change",
                         "closing_stocks"]),
    ("value_column", "closing_stocks"),
    ("min_rows", 1),
    ("allowed_units", ["metric_tonnes", "tonnes", "tons", "lot"]),
    ("positive_required", ["closing_stocks", "on_warrant", "off_warrant"]),
])

# LC 碳酸锂期货行情
SCHEMAS["lc_futures_quote"] = OrderedDict([
    ("fieldnames", ["date", "indicator_code", "contract", "close_price",
                    "settlement_price", "volume", "open_interest", "turnover",
                    "unit", "source", "fetched_at", "raw_ref"]),
    ("required_columns", ["date", "indicator_code", "close_price",
                          "unit", "source", "fetched_at"]),
    ("date_columns", ["date"]),
    ("numeric_columns", ["close_price", "settlement_price", "volume",
                         "open_interest", "turnover"]),
    ("value_column", "close_price"),
    ("min_rows", 1),
    ("allowed_units", ["CNY/tonne", "CNY", "contracts", "lots"]),
    ("positive_required", ["close_price", "open_interest", "volume"]),
])


def _norm_row(row):
    """行规范化: strip 字符串, 数值解析, 日期解析。返回 (normalized, problems)。"""
    out = OrderedDict()
    problems = []
    for k, v in row.items():
        if isinstance(v, str):
            v = v.strip()
        out[k] = v
    return out, problems


def validate_csv(path, schema_name=None, schema=None, max_rows=None,
                 logger=None, strict=True):
    """校验 CSV。返回 report dict:

    {
      "file", "schema", "ok", "row_count", "column_count",
      "problems": [ {code, column, row_index, value, detail} ],
      "stats": {col: {min,max,mean,stddev,non_null,nulls}},
      "columns"
    }

    校验内容:
      E01 数值范围 (>=0, 且 schema.positive_required 列 > 0)
      E02 日期格式可解析
      E03 必填列存在
      E04 重复幂等键 (date+indicator_code+source)
      E05 空值率过高 (数值列 null > 50%)
    """
    p = Path(path)
    report = OrderedDict([
        ("file", str(p)),
        ("schema", schema_name or (schema or {}).get("name", "auto")),
        ("ok", True),
        ("row_count", 0),
        ("column_count", 0),
        ("problems", []),
        ("stats", OrderedDict()),
        ("columns", []),
    ])
    if not p.exists():
        report.update(ok=False, error="not_found")
        return report

    schema = schema or SCHEMAS.get(schema_name) or _auto_schema(p)
    fieldnames = schema.get("fieldnames")
    numeric_cols = list(schema.get("numeric_columns", []))
    date_cols = list(schema.get("date_columns", []))
    positive_required = list(schema.get("positive_required", []))
    min_rows = int(schema.get("min_rows", 0))

    if not fieldnames:
        # 仅存在 fieldnames 的 schema
        fieldnames = fieldnames or []

    with open(str(p), "r", encoding="utf-8-sig", newline="") as f:
        sniffer = csv.reader(f)
        try:
            header = next(sniffer)
        except StopIteration:
            report.update(ok=False, error="empty_file")
            return report
        header = [h.strip() for h in header]
        report["columns"] = header
        report["column_count"] = len(header)

        # E03 必填列
        required = list(schema.get("required_columns",
                                   CSV_CONVENTIONS["required_columns"]))
        for col in required:
            if col not in header:
                if strict:
                    report["ok"] = False
                report["problems"].append({
                    "code": "E03_MISSING_COLUMN", "column": col,
                    "row_index": -1, "value": None,
                    "detail": "required column absent",
                })

        # 若 schema 声明的数值/日期列不存在于表头, 降级为表头中的数值列推断
        numeric_cols = [c for c in numeric_cols if c in header]
        date_cols = [c for c in date_cols if c in header]

        rows = []
        for idx, raw in enumerate(sniffer):
            if max_rows is not None and len(rows) >= max_rows:
                break
            if not raw or all(not str(c).strip() for c in raw):
                continue
            row = OrderedDict()
            for i, col in enumerate(header):
                row[col] = raw[i] if i < len(raw) else ""
            row["_row_index"] = idx + 2  # 1-based, 含表头
            rows.append(row)

    report["row_count"] = len(rows)
    if len(rows) < min_rows:
        report["ok"] = False
        report["problems"].append({
            "code": "E06_ROWCOUNT_LOW", "column": "_all_",
            "row_index": -1, "value": len(rows),
            "detail": "rows < min_rows(%d)" % min_rows,
        })

    key_counts = OrderedDict()
    agg = {c: [] for c in numeric_cols}
    nulls = {c: 0 for c in numeric_cols}

    for row in rows:
        # 幂等键
        key_parts = []
        missing_key = False
        for kcol in CSV_CONVENTIONS["idempotency_key"]:
            if kcol in header:
                key_parts.append(str(row.get(kcol, "")).strip())
            else:
                missing_key = True
        if not missing_key and key_parts:
            key = "|".join(key_parts)
            key_counts[key] = key_counts.get(key, 0) + 1

        # 日期
        for dcol in date_cols:
            if parse_date(row.get(dcol)) is None:
                report["ok"] = False
                report["problems"].append({
                    "code": "E02_DATE_FORMAT", "column": dcol,
                    "row_index": row["_row_index"],
                    "value": row.get(dcol), "detail": "unparseable date",
                })

        # 数值
        for ncol in numeric_cols:
            raw_v = row.get(ncol, "")
            num = parse_number(raw_v)
            if num is None:
                if str(raw_v).strip() == "":
                    nulls[ncol] += 1
                    continue
                report["ok"] = False
                report["problems"].append({
                    "code": "E05_NON_NUMERIC", "column": ncol,
                    "row_index": row["_row_index"], "value": raw_v,
                    "detail": "not a number",
                })
                continue
            agg[ncol].append(num)
            if num < 0:
                report["ok"] = False
                report["problems"].append({
                    "code": "E01_NEGATIVE", "column": ncol,
                    "row_index": row["_row_index"], "value": num,
                    "detail": "negative value not allowed",
                })
            elif ncol in positive_required and num == 0:
                report["problems"].append({
                    "code": "E01_ZERO", "column": ncol,
                    "row_index": row["_row_index"], "value": num,
                    "detail": "positive_required column is zero",
                })

    # E04 重复幂等键
    for key, cnt in key_counts.items():
        if cnt > 1:
            report["ok"] = False
            report["problems"].append({
                "code": "E04_DUPLICATE_KEY", "column": "|".join(
                    CSV_CONVENTIONS["idempotency_key"]),
                "row_index": -1, "value": key, "detail": "count=%d" % cnt,
            })

    # 统计
    for c, vals in agg.items():
        if vals:
            mn, mx = min(vals), max(vals)
            mean = sum(vals) / len(vals)
            var = sum((v - mean) ** 2 for v in vals) / len(vals)
            sd = var ** 0.5
            report["stats"][c] = OrderedDict([
                ("non_null", len(vals)),
                ("nulls", nulls.get(c, 0)),
                ("min", mn), ("max", mx),
                ("mean", round(mean, 6)), ("stddev", round(sd, 6)),
            ])
        else:
            report["stats"][c] = OrderedDict([
                ("non_null", 0), ("nulls", nulls.get(c, 0)),
                ("min", None), ("max", None), ("mean", None), ("stddev", None),
            ])

    if logger:
        lg = ("VALID %s ok=%s rows=%d problems=%d" % (
            p.name, report["ok"], report["row_count"], len(report["problems"])))
        (logger.error if not report["ok"] else logger.info)(lg)
    return report


def _auto_schema(path):
    """无 schema 时: 读表头并探测列类型。

    探测规则 (最多扫描 200 行, 采样判定):
      * 列名在 {date,trade_date,datetime,ts,时间,日期} 或 >=80% 值可被 parse_date
        解析 -> date_columns
      * >=60% 非空值可被 parse_number 解析, 且解析失败率 < 20% -> numeric_columns
      * 其余视为字符串列。
    """
    p = Path(path)
    numeric_candidates = {}
    date_hits = {}
    total = {}
    header = []
    try:
        with open(str(p), "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            header = [h.strip() for h in next(reader)]
            for i, raw in enumerate(reader):
                if i >= 200:
                    break
                for idx, col in enumerate(header):
                    if idx >= len(raw):
                        continue
                    v = str(raw[idx]).strip()
                    if v == "":
                        continue
                    total[col] = total.get(col, 0) + 1
                    if parse_date(v) is not None:
                        date_hits[col] = date_hits.get(col, 0) + 1
                    if parse_number(v) is not None:
                        numeric_candidates[col] = numeric_candidates.get(col, 0) + 1
    except (StopIteration, OSError):
        return {"fieldnames": [], "numeric_columns": [], "date_columns": []}

    DATE_NAMES = {"date", "trade_date", "trading_date", "datetime", "ts",
                  "date_str", "时间", "日期", "交易日期"}
    value_names = {"value", "price", "close", "close_price", "open", "high", "low",
                   "settlement_price", "volume", "open_interest", "turnover",
                   "on_warrant", "off_warrant", "net_change", "closing_stocks",
                   "stock", "stocks", "change", "qty", "quantity", "total"}

    date_cols, numeric_cols = [], []
    for col in header:
        n = total.get(col, 0)
        if n == 0:
            continue
        cl = col.lower()
        if cl in DATE_NAMES or (date_hits.get(col, 0) / float(n)) >= 0.80:
            date_cols.append(col)
        elif ((numeric_candidates.get(col, 0) / float(n)) >= 0.60
              or cl in value_names):
            numeric_cols.append(col)

    return {"fieldnames": header,
            "numeric_columns": numeric_cols,
            "date_columns": date_cols}


def write_csv_append_only(path, rows, fieldnames, idempotency_key=None,
                          dry_run=True, logger=None, encoding="utf-8"):
    """APPEND_ONLY + NO_OVERWRITE 写入 CSV。

    规则:
      * 文件不存在 -> 新建并写表头。
      * 文件已存在 -> 只追加 (open "a"), 永不截断。
      * 幂等: 读取已有行的 idempotency_key 集合, 命中则跳过 (返回 skipped 计数),
              防止重跑产生重复行 (重复留给 DQA-EXT-02 报告)。
      * dry_run=True 时不写盘, 仅返回计划。

    返回 {written, skipped, total, path, dry_run, file_created, error?}
    """
    p = Path(path)
    idk = list(idempotency_key or CSV_CONVENTIONS["idempotency_key"])
    result = OrderedDict([
        ("path", str(p)),
        ("file_created", False),
        ("rows_planned", len(rows)),
        ("written", 0),
        ("skipped", 0),
        ("dry_run", dry_run),
        ("error", None),
    ])

    existing_keys = set()
    file_exists = p.exists()
    if file_exists:
        try:
            with open(str(p), "r", encoding=encoding, newline="") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    key = "|".join(str(r.get(k, "")).strip() for k in idk)
                    existing_keys.add(key)
        except (OSError, csv.Error) as e:
            result["error"] = "read_existing_failed: %s" % e
            return result

    new_rows = []
    for row in rows:
        key = "|".join(str(row.get(k, "")).strip() for k in idk)
        if key in existing_keys:
            result["skipped"] += 1
            continue
        existing_keys.add(key)
        new_rows.append(row)

    if dry_run:
        if logger:
            logger.info("DRYRUN would append %d rows (skip %d) -> %s",
                        len(new_rows), result["skipped"], p)
        result["written"] = len(new_rows)
        return result

    if not file_exists:
        ensure_dir(p.parent)
        with open(str(p), "w", encoding=encoding, newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames,
                               extrasaction="ignore",
                               lineterminator=CSV_CONVENTIONS["line_terminator"])
            w.writeheader()
            for row in new_rows:
                w.writerow({k: row.get(k, "") for k in fieldnames})
            f.flush()
            os.fsync(f.fileno())
        result["file_created"] = True
        result["written"] = len(new_rows)
    else:
        # 追加模式 — 永不截断
        with open(str(p), "a", encoding=encoding, newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames,
                               extrasaction="ignore",
                               lineterminator=CSV_CONVENTIONS["line_terminator"])
            for row in new_rows:
                w.writerow({k: row.get(k, "") for k in fieldnames})
            f.flush()
            os.fsync(f.fileno())
        result["written"] = len(new_rows)

    if logger:
        logger.info("CSV %s written=%d skipped=%d (file_created=%s)",
                    p.name, result["written"], result["skipped"],
                    result["file_created"])
    return result


# =============================================================================
# 11. Manifest (append-only 目录清单, 记录每次写入 + MD5)
# =============================================================================

def append_manifest(dir_path, entries, logger=None):
    """向 <dir>/_manifest.jsonl 追加写入记录。APPEND_ONLY。

    entries: list[dict], 每项建议含 indicator_code / file / rows_written /
             checksum / computed_at。
    返回 {"manifest": path, "appended": n}
    """
    d = ensure_dir(dir_path)
    manifest = d / "_manifest.jsonl"
    for e in entries:
        if not isinstance(e, dict):
            e = {"value": e}
        e.setdefault("ts", now_iso())
    with open(str(manifest), "a", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False, default=str) + "\n")
        f.flush()
        os.fsync(f.fileno())
    if logger:
        logger.info("MANIFEST +%d -> %s" % (len(entries), manifest))
    return {"manifest": str(manifest), "appended": len(entries)}


def read_manifest(dir_path):
    d = Path(dir_path)
    m = d / "_manifest.jsonl"
    if not m.exists():
        return []
    out = []
    with open(str(m), "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    out.append({"_raw_line": line, "_parse_error": True})
    return out


# =============================================================================
# 12. HTML/regex extraction helpers (stdlib only)
# =============================================================================

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def strip_tags(html):
    return WS_RE.sub(" ", TAG_RE.sub(" ", html or "")).strip()


def extract_by_regex(html, pattern, group=1, cast=None, flags=0, limit=None):
    """按正则提取。返回 list[str|number]。cast='float'/'int' 时转数值。"""
    out = []
    for m in re.finditer(pattern, html or "", flags):
        try:
            val = m.group(group) if isinstance(group, int) else m.groups()[group]
        except (IndexError, TypeError):
            val = m.group(0)
        if val is None:
            continue
        val = val.strip()
        if cast == "float":
            val = parse_number(val)
        elif cast == "int":
            v = parse_number(val)
            val = int(v) if v is not None else None
        if val is not None:
            out.append(val)
        if limit is not None and len(out) >= limit:
            break
    return out


def extract_table_by_regex(html, row_pattern, cell_pattern,
                           cast_map=None, flags=0, limit=None):
    """双正则提取表格: row_pattern 定位每一行, cell_pattern 从行内取单元格。

    row_pattern   必须含 1 个分组 (行内容)
    cell_pattern  作用于行内容, findall 得到单元格列表
    cast_map      {0: 'float', 1: None, ...} 按位置转换
    返回 list[list]
    """
    rows = []
    for m in re.finditer(row_pattern, html or "", flags):
        body = m.group(1)
        cells = re.findall(cell_pattern, body)
        if not isinstance(cells, list):
            cells = [cells]
        if cast_map:
            converted = []
            for i, c in enumerate(cells):
                c = c.strip() if isinstance(c, str) else c
                kind = cast_map.get(i)
                if kind == "float":
                    c = parse_number(c)
                elif kind == "int":
                    v = parse_number(c)
                    c = int(v) if v is not None else None
                converted.append(c)
            cells = converted
        rows.append(cells)
        if limit is not None and len(rows) >= limit:
            break
    return rows


def normalize_text_table(lines, delimiter="\t", header_keywords=None):
    """把 SHFE .dat 之类的定宽/tab 分隔文本规范成 list[dict]。

    header_keywords 若给出, 用于在第 1 个分隔行定位列名 (取含关键词最多的行)。
    """
    lines = [ln.rstrip("\r\n") for ln in lines if ln.strip()]
    if not lines:
        return [], []
    delim = "\t" if "\t" in lines[0] else ("\t" if delimiter == "\t" else delimiter)
    parsed = [ln.split(delim) for ln in lines]

    header_idx = 0
    if header_keywords:
        best_score = -1
        for i, cols in enumerate(parsed):
            joined = " ".join(cols).lower()
            score = sum(1 for k in header_keywords if k in joined)
            if score > best_score:
                best_score, header_idx = score, i
    header = [str(c).strip() for c in parsed[header_idx]]
    rows = []
    for cols in parsed[header_idx + 1:]:
        if len(cols) < len(header):
            cols = cols + [""] * (len(header) - len(cols))
        elif len(cols) > len(header):
            cols = cols[:len(header)]
        rows.append(OrderedDict((h, str(c).strip()) for h, c in zip(header, cols)))
    return rows, header


# =============================================================================
# 13. Dry-run synthetic samples (仅用于流水线 / DQA 冒烟测试)
# =============================================================================

def synthetic_rows(indicator_code, schema_name, n_days=30, end_date=None,
                   jitter=0.05, seed=None):
    """生成合成样本行。**仅供 dry-run 冒烟测试**, 绝不进入正式 external_raw。

    写入位置必须是 external_raw/_dryrun_samples/<dir>/, 且每行含
    dry_run_sample=True 标记列, DQA 默认跳过 _ 前缀目录。
    """
    seed_key = seed if seed is not None else "%s:%d" % (indicator_code, n_days)
    rnd = random.Random(str(seed_key))
    end = parse_date(end_date) or date.today()
    start = end - timedelta(days=n_days - 1)
    schema = SCHEMAS.get(schema_name, {})
    fieldnames = list(schema.get("fieldnames", []))
    value_col = schema.get("value_column", "value")
    unit = "metric_tonnes"
    if indicator_code.startswith("COMEX"):
        base = 12000.0
    else:
        base = 98000.0
        unit = "CNY/tonne"
    rows = []
    for i in range(n_days):
        d = start + timedelta(days=i)
        # 周末空窗: 保持连续以便 DQA-EXT-03 可测试 (显式填充工作日序列)
        if d.weekday() >= 5:
            continue
        drift = 1.0 + 0.0006 * i
        noise = 1.0 + rnd.uniform(-jitter, jitter)
        v = round(base * drift * noise, 2)
        row = OrderedDict((f, "") for f in fieldnames)
        row["_row_index"] = i + 2
        row["dry_run_sample"] = "True"     # 标记列: DQA 默认跳过合成样本
        if "date" in row:
            row["date"] = d.strftime(DATE_FMT)
        if "indicator_code" in row:
            row["indicator_code"] = indicator_code
        if "unit" in row:
            row["unit"] = unit
        if "source" in row:
            row["source"] = "dryrun_sample"
        if "fetched_at" in row:
            row["fetched_at"] = now_iso()
        if "raw_ref" in row:
            row["raw_ref"] = "SYNTHETIC://dry-run-sample"
        if "metal_abbr" in row:
            row["metal_abbr"] = indicator_code.split("_")[-1]
        if "warehouse" in row:
            row["warehouse"] = "COMEX_US"
        if "contract" in row:
            row["contract"] = "LC0"
        if value_col in row:
            row[value_col] = v
        if "on_warrant" in row:
            row["on_warrant"] = round(rnd.uniform(0, 900), 2)
        if "off_warrant" in row:
            row["off_warrant"] = round(rnd.uniform(0, 900), 2)
        if "net_change" in row:
            row["net_change"] = round(rnd.uniform(-700, 700), 2)
        if "closing_stocks" in row:
            row["closing_stocks"] = v
        if "settlement_price" in row:
            row["settlement_price"] = round(v * 1.0012, 2)
        if "volume" in row:
            row["volume"] = int(rnd.uniform(5000, 90000))
        if "open_interest" in row:
            row["open_interest"] = int(rnd.uniform(80000, 160000))
        if "turnover" in row:
            row["turnover"] = round(rnd.uniform(1e9, 6e9), 2)
        rows.append(row)
    return rows


# =============================================================================
# 14. Self test
# =============================================================================

def _selftest(logger):
    """库自检。全部通过返回 True。"""
    ok = True
    checks = []

    def chk(name, cond, detail=""):
        nonlocal ok
        checks.append((name, bool(cond), detail))
        if not cond:
            ok = False

    # UA
    chk("UA count >= 5", len(USER_AGENTS) >= 5, "got %d" % len(USER_AGENTS))
    chk("UA distinct", len(set(USER_AGENTS)) == len(USER_AGENTS))
    chk("UA sequential cycle", random_user_agent(sequential=True) in USER_AGENTS)

    # Dates / numbers
    chk("parse_date iso", parse_date("2026-10-15") == date(2026, 10, 15))
    chk("parse_date compact", parse_date("20261015") == date(2026, 10, 15))
    chk("parse_date slash", parse_date("2026/10/15") == date(2026, 10, 15))
    chk("parse_date excel", parse_date(46000) == date(2025, 10, 19) or
        parse_date("46000") is not None, str(parse_date("46000")))
    chk("parse_date bad", parse_date("not-a-date") is None)
    chk("parse_number comma", parse_number("1,234.5") == 1234.5)
    chk("parse_number pct", parse_number("12.3%") == 12.3)
    chk("parse_number negparen", parse_number("(5)") == -5.0)
    chk("parse_number bad", parse_number("abc") is None)
    chk("parse_number empty", parse_number("") is None)

    # MD5
    chk("md5_bytes known", md5_bytes(b"abc") == "900150983cd24fb0d6963f7d28e17f72")

    # RateLimiter (极小间隔)
    rl = RateLimiter(0.02, jitter_pct=0.0)
    rl.acquire()
    chk("RateLimiter no error", True)

    # Dry-run guard
    guarded = False
    try:
        http_get("https://example.invalid/x", dry_run=True)
    except DryRunGuard:
        guarded = True
    chk("http_get dry-run guarded", guarded)

    # CSV append-only idempotency (temp file)
    import tempfile
    tmpdir = tempfile.mkdtemp(prefix="crawlib_selftest_")
    tp = Path(tmpdir) / "t.csv"
    fn = ["date", "indicator_code", "value", "unit", "source", "fetched_at"]

    def _mk(d, code, val, src="lme"):
        return OrderedDict([("date", d), ("indicator_code", code), ("value", val),
                            ("unit", "metric_tonnes"), ("source", src),
                            ("fetched_at", now_iso())])

    r1 = write_csv_append_only(tp, [
        _mk("2026-10-15", "COMEX_AL", "100"),
        _mk("2026-10-16", "COMEX_AL", "110"),
    ], fn, dry_run=False, logger=logger)
    r2 = write_csv_append_only(tp, [
        _mk("2026-10-15", "COMEX_AL", "100"),
        _mk("2026-10-17", "COMEX_AL", "120"),
    ], fn, dry_run=False, logger=logger)
    chk("csv first write", r1["written"] == 2 and r1["file_created"], str(r1))
    chk("csv idempotent append", r2["written"] == 1 and r2["skipped"] == 1, str(r2))
    chk("csv append no truncate", tp.exists() and
        sum(1 for _ in open(str(tp), encoding="utf-8")) == 4,
        "linecount=%d" % sum(1 for _ in open(str(tp), encoding="utf-8")))

    # MD5 snapshot
    snap = write_md5_snapshot(tp, logger=logger)
    chk("md5 snapshot", snap.get("checksum") == md5_file(tp) and
        tp.with_suffix(tp.suffix + MD5_SNAPSHOT_SUFFIX).exists(), str(snap))

    # Validate csv (clean)
    rep = validate_csv(tp, schema_name=None, logger=logger)
    chk("validate_csv ok", rep["ok"] is True, str(rep["problems"][:3]))

    # Validate csv with duplicate key
    dup = Path(tmpdir) / "dup.csv"
    write_csv_append_only(dup, [_mk("2026-10-15", "A", "1")], fn, dry_run=False)
    with open(str(dup), "a", encoding="utf-8", newline="") as f:
        f.write("2026-10-15,A,2,metric_tonnes,lme,x\n")
    rep2 = validate_csv(dup, logger=logger)
    chk("validate_csv dup detected", any(pr["code"] == "E04_DUPLICATE_KEY"
                                         for pr in rep2["problems"]), str(rep2["problems"]))

    # Synthetic rows
    rows = synthetic_rows("COMEX_AL", "comex_warehouse_receipts", n_days=20)
    chk("synthetic rows > 0", len(rows) > 0, "n=%d" % len(rows))
    chk("synthetic dates unique", len({r["date"] for r in rows}) == len(rows))

    # Indicator registry
    chk("INDICATORS == 6", len(INDICATORS) == 6, "n=%d" % len(INDICATORS))
    chk("SOURCE_REGISTRY >= 4", len(SOURCE_REGISTRY) >= 4)

    for name, passed, detail in checks:
        logger.info("SELFCHECK %-32s %s  %s" % (name, "PASS" if passed else "FAIL", detail))
    return ok


# =============================================================================
# 15. CLI
# =============================================================================

def main():
    setup_environment()
    parser = argparse.ArgumentParser(
        description="V88 Phase03 P1 DSHB external crawler shared library")
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="do not touch the network (default)")
    g.add_argument("--live", "--no-dry-run", dest="dry_run", action="store_false",
                   help="allow real network I/O")
    parser.add_argument("--selftest", action="store_true", help="run library self test")
    parser.add_argument("--list", action="store_true", help="print indicator/source registry")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logger = get_logger("crawlib", level=logging.DEBUG if args.verbose else logging.INFO)
    logger.info("LIB %s | %s | %s | dry_run=%s", LIB_VERSION, TASK_ID, BRANCH, args.dry_run)
    logger.info("CONSTRAINTS %s", dict(CONSTRAINTS))

    if args.list:
        print(json.dumps({
            "indicators": INDICATORS,
            "sources": SOURCE_REGISTRY,
            "schemas": {k: {kk: vv for kk, vv in v.items() if kk != "fieldnames"}
                        | {"fieldnames": v["fieldnames"]} for k, v in SCHEMAS.items()},
        }, indent=2, ensure_ascii=False, default=str))
        return 0

    if not args.selftest:
        parser.print_help()
        return 0

    ok = _selftest(logger)
    logger.info("SELFCHECK overall=%s", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    setup_environment()
    sys.exit(main())
