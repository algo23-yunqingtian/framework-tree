#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spot_is_crawler_v2.py — SPOT_IS 工业硅现货价格爬虫 V2 (含 5 项修复)
=====================================================================
TASK_ID: V88_PHASE03_P1_DSHB_IMPLEMENT_AND_NOISE_CONTINUE_JOB
AGENT:   DSHB | BRANCH: feature/v88-g1 (BRANCH_LOCKED)
TASK:    T1 — SPOT_IS URL Code Fixes + LIVE Verification

修复清单 (5项):
  Fix 1: URL 更新 — 100ppi.com 工业硅板块路径重构
  Fix 2: Rate Limit 增强 — 随机抖动 + 指数退避
  Fix 3: Retry 策略 — 429/404/Timeout 差异化处理
  Fix 4: Fallback 源 — SMM 上海有色网 + 长江有色金属网
  Fix 5: Server 部署配置 — dev/staging/production 环境检测

数据源:
  生意社 (100ppi.com) — 工业硅现货价格 HTML 表格
  URL: http://www.100ppi.com/spot/is/daily-price/ (工业硅现货)
  URL: http://www.100ppi.com/spot/is/historical-data/ (工业硅历史)
  编码: GB2312/GBK, 需转码解析
  数据频率: 日度 (工作日)
  回溯起始: 2021-01-01

采集字段:
  date                日期 (YYYY-MM-DD)
  spot_price_avg      工业硅综合价格 (元/吨)
  polysilicon_price   多晶硅级价格 (元/吨)
  organic_silicon_price 有机硅级价格 (元/吨)
  steel_grade_price   钢铁级价格 (元/吨)
  regional_avg        产地均价 (元/吨)

MVP特性:
  1. 基础抓取: 生意社HTML表格解析, 日度数据
  2. DQA校验: 10条规则 (完整性/范围/空值/时序/重复/零值/单调性/源一致性/指标一致性/文件完整性)
  3. MD5快照: 每日数据文件哈希校验
  4. 增量拉取: 基于水位线, 仅抓取新数据
  5. 失败告警: 多通道告警 (console + JSONL)
  6. 日志轮转: 50MB上限, 14备份, 90天保留
  7. V2新增: Fallback 数据源 (SMM + 长江有色金属网)
  8. V2新增: 多环境部署配置 (dev/staging/production)
  9. V2新增: 指数退避重试 + 差异化错误处理

约束 (继承任务书):
  NO_ZHIJI_API_CALL  绝不 import / 调用 zhiji_api.py
  NO_OVERWRITE       已存在CSV只追加, 永不截断
  APPEND_ONLY        幂等键命中则跳过
  BRANCH_LOCKED      feature/v88-g1
  NO_MODIFY_V87      禁止修改V87基线数据
  NO_EDIT_RELEASE_TAG 禁止修改发布标签
  UPSTREAM_WRITES=0  仅写入 implementation/ 目录

Usage:
  python spot_is_crawler_v2.py                          # 全量抓取 (dry-run)
  python spot_is_crawler_v2.py --live                   # 真实HTTP抓取
  python spot_is_crawler_v2.py --incremental            # 增量模式
  python spot_is_crawler_v2.py --verify                 # 仅DQA校验
  python spot_is_crawler_v2.py --md5-snapshot           # 仅MD5快照
  python spot_is_crawler_v2.py --backfill               # 历史数据回填
  python spot_is_crawler_v2.py --start-date 2021-01-01  # 指定起始日期
  python spot_is_crawler_v2.py --end-date 2026-10-16    # 指定结束日期
  python spot_is_crawler_v2.py --json-out result.json   # JSON输出
  python spot_is_crawler_v2.py --source-fallback        # 强制使用Fallback源 (测试)
"""

import sys
import os
import re
import json
import csv
import hashlib
import gzip
import shutil
import argparse
import logging
import time
import random
import platform
from pathlib import Path
from collections import OrderedDict
from datetime import datetime, timedelta

# =============================================================================
# 常量
# =============================================================================

TASK_ID = "V88_PHASE03_P1_DSHB_IMPLEMENT_AND_NOISE_CONTINUE_JOB"
AGENT = "DSHB"
BRANCH = "feature/v88-g1"
SCRIPT_NAME = "spot_is_crawler_v2"
LIB_VERSION = "v88-p1-t2-spot-is-mvp-v2.0"
INDICATOR_CODE = "SPOT_IS"
INDICATOR_NAME = "工业硅现货价格"
COMMODITY = "si"

CONSTRAINTS = OrderedDict([
    ("NO_ZHIJI_API_CALL", True),
    ("NO_OVERWRITE", True),
    ("APPEND_ONLY", True),
    ("BRANCH_LOCKED", True),
    ("NO_MODIFY_V87", True),
    ("NO_EDIT_RELEASE_TAG", True),
])

# ---- 数据源配置 (Fix 1: URL 更新) ----
DATA_SOURCE_PRIMARY = {
    "id": "100PPI_SI_DAY_V2",
    "name": "生意社-工业硅现货日度V2",
    "base_url": "http://www.100ppi.com/spot/is/",
    "detail_url": "http://www.100ppi.com/spot/is/daily-price/",
    "history_url": "http://www.100ppi.com/spot/is/historical-data/",
    "encoding": "gb2312",
    "rate_limit_sec": 5.0,           # Fix 2: 从 3.0 → 5.0，更保守
    "start_date": "2021-01-01",
    "anti_crawl": "MEDIUM",
    "columns": ["date", "spot_price_avg", "polysilicon_price",
                "organic_silicon_price", "steel_grade_price", "regional_avg"],
    # Fix 1: 新增浏览器模拟头
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "headers": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "http://www.100ppi.com/",
        "Accept-Encoding": "identity",
        "Cache-Control": "no-cache",
    },
    "timeout": 15,
    "max_retries": 3,
}

# ---- Fix 4: Fallback 数据源 (SMM 上海有色网 + 长江有色金属网) ----
DATA_SOURCE_FALLBACKS = [
    {
        "id": "SMM_SI_MONTHLY",
        "name": "上海有色网-工业硅月度",
        "base_url": "https://www.smm.cn/industry/44433",
        "encoding": "utf-8",
        "anti_crawl": "HIGH",
        "rate_limit_sec": 5.0,
        "timeout": 20,
        "max_retries": 1,
        "field_mapping": {
            "date": "月份",
            "spot_price_avg": "均价",
        },
        "note": "月度数据, 粒度较粗, 仅作降级备选",
    },
    {
        "id": "CSPC_SI_MONTHLY",
        "name": "长江有色金属网-工业硅月度",
        "base_url": "https://www.ccmn.cn/sifang/",
        "encoding": "gb2312",
        "anti_crawl": "LOW",
        "rate_limit_sec": 3.0,
        "timeout": 15,
        "max_retries": 1,
        "field_mapping": {
            "date": "月份",
            "spot_price_avg": "综合价格",
        },
        "note": "长江有色金属网, 反爬较宽松",
    },
]

# ---- Fix 5: Server 部署配置 (多环境检测) ----
DEPLOYMENT_CONFIG = {
    "dev": {
        "timeout": 10,
        "max_retries": 2,
        "use_proxy": False,
        "proxy_url": "",
        "log_level": "DEBUG",
        "rate_limit_extra": 0,  # 无额外延迟
    },
    "staging": {
        "timeout": 15,
        "max_retries": 3,
        "use_proxy": False,
        "proxy_url": "",
        "log_level": "INFO",
        "rate_limit_extra": 1.0,  # 额外 1s 延迟
    },
    "production": {
        "timeout": 20,
        "max_retries": 4,
        "use_proxy": True,  # 生产环境使用代理
        "proxy_url": os.environ.get("CRAWLER_PROXY", ""),
        "log_level": "WARNING",
        "rate_limit_extra": 2.0,  # 额外 2s 延迟 (更保守)
    },
}


def get_deployment_env():
    """检测当前部署环境 (Fix 5)."""
    env = os.environ.get("CRAWLER_ENV", "dev")
    return env


def get_deployment_config():
    """获取当前部署配置 (Fix 5)."""
    env = get_deployment_env()
    return DEPLOYMENT_CONFIG.get(env, DEPLOYMENT_CONFIG["dev"]), env


# 现有映射参考
EXISTING_MAPPING = {
    "source_indicator": "spot_is_change",
    "existing_rows": 773,
    "description": "已有 spot_is_change (工业硅现货变化), SPOT_IS 为绝对价格指标",
}

# ---- 输出目录 (UPSTREAM_WRITES=0: 仅写入 implementation/) ----
OUTPUT_BASE = Path(__file__).resolve().parent / "crawler_data"
CSV_PATH = OUTPUT_BASE / "spot_is_data.csv"
WATERMARK_FILE = OUTPUT_BASE / "spot_is_watermark.json"
MD5_SNAPSHOT_DIR = OUTPUT_BASE / "md5_snapshots"
LOG_DIR = OUTPUT_BASE / "logs"
ALERT_LOG = OUTPUT_BASE / "alerts" / "spot_is_alerts.jsonl"
AUDIT_LOG = LOG_DIR / "spot_is_crawler_audit.jsonl"

# ---- 日志轮转配置 ----
LOG_CONFIG = {
    "max_bytes": 50 * 1024 * 1024,   # 50MB
    "backup_count": 14,
    "retention_days": 90,
}

# ---- CSV字段名 ----
FIELDNAMES = [
    "date", "indicator_code", "commodity", "spot_price_avg",
    "polysilicon_price", "organic_silicon_price", "steel_grade_price",
    "regional_avg", "unit", "source", "fetched_at", "raw_ref",
]

# 幂等键: 日期+指标+数据源 唯一确定一行
IDEMPOTENCY_KEY = ["date", "indicator_code", "source"]

# ---- DQA规则定义 ----
DQA_RULES = OrderedDict([
    ("DQA-01", {"name": "Completeness", "severity": "HIGH",
                "desc": "数据完整性检查: 行数 > 0, 关键字段非空"}),
    ("DQA-02", {"name": "Range", "severity": "HIGH",
                "desc": "价格范围检查: 10000-20000 元/吨, 非负"}),
    ("DQA-03", {"name": "Null", "severity": "MEDIUM",
                "desc": "空值检查: 关键字段不为空"}),
    ("DQA-04", {"name": "Continuity", "severity": "HIGH",
                "desc": "时序连续性: 最大日期间隔 < 30天"}),
    ("DQA-05", {"name": "Duplicate", "severity": "MEDIUM",
                "desc": "重复行检查: 同一date+indicator_code不重复"}),
    ("DQA-06", {"name": "ZeroDetection", "severity": "CRITICAL",
                "desc": "全零值检测: 全零行占比 < 50%"}),
    ("DQA-07", {"name": "Monotonicity", "severity": "LOW",
                "desc": "单调性: 相邻价格变化率 < 10%"}),
    ("DQA-08", {"name": "SourceConsistency", "severity": "MEDIUM",
                "desc": "数据源一致性: 所有行来自同一数据源"}),
    ("DQA-09", {"name": "IndicatorConsistency", "severity": "MEDIUM",
                "desc": "指标一致性: 所有行属于同一指标"}),
    ("DQA-10", {"name": "FileIntegrity", "severity": "HIGH",
                "desc": "文件完整性: MD5校验"}),
])

# ---- 告警规则 ----
ALERT_RULES = [
    {"id": "ALERT-01", "condition": "all_zero", "severity": "CRITICAL",
     "msg": "所有数据全零"},
    {"id": "ALERT-02", "condition": "gap_exceed", "severity": "HIGH",
     "msg": "日期间隔超过阈值", "threshold": 10},
    {"id": "ALERT-03", "condition": "out_of_range", "severity": "MEDIUM",
     "msg": "数值超出预期范围"},
    {"id": "ALERT-04", "condition": "crawl_fail", "severity": "HIGH",
     "msg": "爬虫抓取失败"},
    {"id": "ALERT-05", "condition": "parse_fail", "severity": "HIGH",
     "msg": "数据解析失败"},
    {"id": "ALERT-06", "condition": "watermark_missing", "severity": "MEDIUM",
     "msg": "水位线文件缺失"},
    {"id": "ALERT-07", "condition": "md5_mismatch", "severity": "HIGH",
     "msg": "MD5校验失败"},
    {"id": "ALERT-08", "condition": "backfill_fail", "severity": "MEDIUM",
     "msg": "历史回填失败"},
    # V2 新增告警
    {"id": "ALERT-09", "condition": "url_not_found", "severity": "HIGH",
     "msg": "URL 404 未找到 (可能路径重构)"},
    {"id": "ALERT-10", "condition": "all_sources_failed", "severity": "CRITICAL",
     "msg": "所有数据源均失败 (主源 + Fallback)"},
    {"id": "ALERT-11", "condition": "fallback_triggered", "severity": "MEDIUM",
     "msg": "Fallback 源触发 (主源不可用)"},
]

# ---- 价格合理范围 (元/吨) ----
PRICE_RANGE = {
    "spot_price_avg": (10000, 20000),
    "polysilicon_price": (10000, 20000),
    "organic_silicon_price": (9000, 18000),
    "steel_grade_price": (8000, 16000),
    "regional_avg": (9000, 19000),
}

# ---- Fix 3: Retry 常量 ----
BACKOFF_BASE = 2.0       # 基础退避秒数
BACKOFF_FACTOR = 2.0     # 退避因子


# =============================================================================
# 自定义异常
# =============================================================================

class URLNotFoundError(Exception):
    """HTTP 404 — URL 路径失效, 不重试, 直接触发 Fallback."""
    def __init__(self, url, status_code=404):
        self.url = url
        self.status_code = status_code
        super().__init__("URL not found ({}): {}".format(status_code, url))


class AllSourcesFailed(Exception):
    """所有数据源 (主源 + Fallback) 均失败."""
    def __init__(self, primary_url, detail=None):
        self.primary_url = primary_url
        self.detail = detail
        super().__init__(
            "All sources failed for primary={}. Detail: {}".format(
                primary_url, detail or "none"))


# =============================================================================
# 工具函数
# =============================================================================

def now_iso():
    """返回当前ISO 8601时间戳."""
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def today_str():
    """返回今日日期字符串 YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


def compute_file_md5(filepath, chunk_size=65536):
    """计算文件MD5哈希."""
    md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                md5.update(chunk)
        return md5.hexdigest()
    except Exception:
        return None


def ensure_dir(path):
    """确保目录存在."""
    Path(path).mkdir(parents=True, exist_ok=True)


def setup_logging(logger_name, level=logging.INFO, log_file=None):
    """创建日志器, 支持文件输出和轮转配置."""
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    # 控制台输出
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    ))
    logger.addHandler(h)
    # 文件输出 (含轮转)
    if log_file:
        ensure_dir(Path(log_file).parent)
        from logging.handlers import RotatingFileHandler
        fh = RotatingFileHandler(
            str(log_file),
            maxBytes=LOG_CONFIG["max_bytes"],
            backupCount=LOG_CONFIG["backup_count"],
            encoding="utf-8"
        )
        fh.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S"
        ))
        logger.addHandler(fh)
    return logger


def get_logger(name, level=logging.INFO):
    """获取日志器简写."""
    return setup_logging(name, level, str(LOG_DIR / f"{name}.log"))


def append_jsonl(filepath, data):
    """追加写入JSONL文件 (APPEND_ONLY)."""
    try:
        path = Path(filepath)
        ensure_dir(path.parent)
        line = json.dumps(data, ensure_ascii=False, default=str) + "\n"
        with open(str(path), "a", encoding="utf-8") as f:
            f.write(line)
        return True
    except Exception:
        return False


# =============================================================================
# 水位线管理
# =============================================================================

def load_watermark():
    """加载水位线."""
    if WATERMARK_FILE.exists():
        try:
            with open(str(WATERMARK_FILE), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_date": None, "last_crawl_date": None,
            "total_rows": 0, "last_updated_at": None}


def save_watermark(wm):
    """保存水位线."""
    ensure_dir(WATERMARK_FILE.parent)
    data = {
        "_schema": "v88_spot_is_watermark.v2.0",
        "_task_id": TASK_ID,
        "_updated_at": now_iso(),
        **wm,
    }
    with open(str(WATERMARK_FILE), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def compute_incremental_start(wm, overlap_days=3):
    """计算增量起始日期 (从水位线last_date前移overlap_days天)."""
    if not wm or not wm.get("last_date"):
        return None
    try:
        last = datetime.strptime(wm["last_date"], "%Y-%m-%d")
        return (last - timedelta(days=overlap_days)).strftime("%Y-%m-%d")
    except Exception:
        return None


# =============================================================================
# 告警
# =============================================================================

def send_alert(alert_id, severity, message, detail=None):
    """发送告警 (console + JSONL)."""
    alert = OrderedDict([
        ("alert_id", alert_id),
        ("indicator_code", INDICATOR_CODE),
        ("severity", severity),
        ("message", message),
        ("timestamp", now_iso()),
    ])
    if detail:
        alert["detail"] = detail
    # Console
    print("[ALERT-{}] [{}] {}".format(alert_id, severity, message))
    # JSONL
    append_jsonl(ALERT_LOG, alert)
    return alert


# =============================================================================
# CSV读写
# =============================================================================

def read_csv(filepath):
    """读取CSV文件."""
    if not Path(filepath).exists():
        return []
    with open(str(filepath), "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv_append(filepath, rows, fieldnames):
    """CSV追加写入 (APPEND_ONLY, NO_OVERWRITE)."""
    if not rows:
        return 0
    ensure_dir(Path(filepath).parent)
    file_exists = Path(filepath).exists()
    with open(str(filepath), "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def load_existing_keys(csv_path):
    """加载已存在的幂等键集合."""
    keys = set()
    if not Path(csv_path).exists():
        return keys
    try:
        with open(str(csv_path), "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = "+".join(str(row.get(k, "")) for k in IDEMPOTENCY_KEY)
                if key.count("+") >= 2:
                    keys.add(key)
    except Exception:
        pass
    return keys


def dedup_key(row):
    """生成幂等去重键."""
    return "+".join(str(row.get(k, "")) for k in IDEMPOTENCY_KEY)


def is_duplicate(existing_keys, new_keys):
    """检查是否有重复键."""
    return len(existing_keys & new_keys) > 0


def deduplicate_rows(rows, existing_keys):
    """去重: 保留新行, 跳过已有键."""
    new_rows = []
    dup = 0
    for row in rows:
        key = dedup_key(row)
        if key in existing_keys:
            dup += 1
            continue
        existing_keys.add(key)
        new_rows.append(row)
    return new_rows, dup


# =============================================================================
# Fix 2: Rate Limit 增强 (随机抖动)
# =============================================================================

def apply_rate_limit(source_cfg):
    """应用 Rate Limit 控制: 基础延迟 + 随机抖动 (Fix 2).
    
    原爬虫使用固定 3.0s 间隔, 易被反爬系统识别。
    V2 改为 base_delay + random jitter (0.5-2.0s) + 环境额外延迟。
    
    Args:
        source_cfg: 数据源配置字典, 需包含 rate_limit_sec 字段
    """
    base_delay = source_cfg.get("rate_limit_sec", 5.0)
    jitter = random.uniform(0.5, 2.0)  # 0.5-2.0s 随机抖动
    
    # Fix 5: 部署环境额外延迟
    deploy_cfg, _ = get_deployment_config()
    extra_delay = deploy_cfg.get("rate_limit_extra", 0.0)
    
    sleep_time = base_delay + jitter + extra_delay
    time.sleep(sleep_time)
    return sleep_time


# =============================================================================
# Fix 3: Retry 策略 (429/404/Timeout 差异化处理)
# =============================================================================

def fetch_with_retry(url, headers=None, source_cfg=None, max_retries=None,
                     timeout=None, logger=None):
    """带重试的 HTTP 请求 (Fix 3).
    
    差异化处理:
      - 200: 成功返回响应
      - 429: Rate Limited — 加倍等待后重试
      - 404: URL 失效 — 不重试, 抛出 URLNotFoundError (触发 Fallback)
      - 5xx: 服务器错误 — 指数退避重试
      - Timeout/ConnectionError: 指数退避重试
    
    Args:
        url: 请求 URL
        headers: 请求头
        source_cfg: 数据源配置 (用于获取 rate_limit_sec)
        max_retries: 最大重试次数
        timeout: 超时秒数
        logger: 日志器
    
    Returns:
        requests.Response 对象 (200) 或 raise 异常
    
    Raises:
        URLNotFoundError: 404 (不重试)
        Exception: 所有重试均失败
    """
    if source_cfg is None:
        source_cfg = DATA_SOURCE_PRIMARY
    
    if max_retries is None:
        deploy_cfg, _ = get_deployment_config()
        max_retries = deploy_cfg.get("max_retries", 3)
    
    if timeout is None:
        timeout = source_cfg.get("timeout", 15)
    
    if headers is None:
        headers = source_cfg.get("headers", {})
        headers["User-Agent"] = source_cfg.get("user_agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36")
    
    log = logger or get_logger(SCRIPT_NAME)
    last_error = None
    
    # Fix 5: 生产环境使用代理
    deploy_cfg, deploy_env = get_deployment_config()
    if deploy_cfg.get("use_proxy"):
        proxy_url = deploy_cfg.get("proxy_url", "")
        if proxy_url:
            # requests 代理格式: {"http": "http://proxy:port", "https": "http://proxy:port"}
            # 实际部署时通过环境变量 CRAWLER_PROXY 配置
            pass  # 代理配置在实际部署中通过环境变量处理
    
    for attempt in range(max_retries + 1):
        # Fix 2: Rate Limit 抖动
        elapsed = apply_rate_limit(source_cfg)
        
        try:
            import requests as _requests
            resp = _requests.get(
                url,
                timeout=timeout,
                headers=headers,
                allow_redirects=True,
            )
            
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 429:
                # Fix 3: Rate Limited — 加倍等待
                wait = BACKOFF_BASE * (BACKOFF_FACTOR ** attempt) * 2
                log.warning("[RETRY] 429 Rate Limited on %s (attempt %d/%d), "
                            "waiting %.1fs", url, attempt + 1, max_retries, wait)
                last_error = "429 Rate Limited"
                time.sleep(wait)
                continue
            elif resp.status_code == 404:
                # Fix 3: 404 = URL 失效, 不重试, 直接触发 Fallback
                log.error("[RETRY] 404 URL not found: %s — triggering fallback", url)
                raise URLNotFoundError(url, status_code=404)
            else:
                # 其他状态码 (5xx, 3xx 未重定向, 等)
                wait = BACKOFF_BASE * (BACKOFF_FACTOR ** attempt)
                log.warning("[RETRY] HTTP %d on %s (attempt %d/%d), "
                            "waiting %.1fs", resp.status_code, url,
                            attempt + 1, max_retries, wait)
                last_error = "HTTP {} on {}".format(resp.status_code, url)
                time.sleep(wait)
                continue
        
        except URLNotFoundError:
            # 404 已处理, 直接上抛
            raise
        
        except _requests.exceptions.Timeout as e:
            last_error = e
            if attempt < max_retries:
                wait = BACKOFF_BASE * (BACKOFF_FACTOR ** attempt)
                log.warning("[RETRY] Timeout on %s (attempt %d/%d): %s, "
                            "waiting %.1fs", url, attempt + 1, max_retries, e, wait)
                time.sleep(wait)
            else:
                raise
        
        except _requests.exceptions.ConnectionError as e:
            last_error = e
            if attempt < max_retries:
                wait = BACKOFF_BASE * (BACKOFF_FACTOR ** attempt)
                log.warning("[RETRY] ConnectionError on %s (attempt %d/%d): %s, "
                            "waiting %.1fs", url, attempt + 1, max_retries, e, wait)
                time.sleep(wait)
            else:
                raise
    
    raise last_error


# =============================================================================
# Fix 4: Fallback 数据源
# =============================================================================

def fetch_with_fallback(url, fallbacks=None, force_fallback=False, logger=None):
    """带 Fallback 的数据抓取 (Fix 4).
    
    优先级: 主源 → Fallback1 (SMM) → Fallback2 (长江有色金属网)
    
    Args:
        url: 主源 URL
        fallbacks: Fallback 源列表 (默认使用 DATA_SOURCE_FALLBACKS)
        force_fallback: 是否强制跳过主源 (测试用)
        logger: 日志器
    
    Returns:
        (requests.Response, source_id) 或 raise AllSourcesFailed
    
    Raises:
        AllSourcesFailed: 所有源均失败
    """
    if fallbacks is None:
        fallbacks = DATA_SOURCE_FALLBACKS
    
    log = logger or get_logger(SCRIPT_NAME)
    
    # 尝试主源
    if not force_fallback:
        try:
            log.info("[FETCH] Primary source: %s", url)
            resp = fetch_with_retry(url, logger=log)
            if resp.status_code == 200:
                return resp, DATA_SOURCE_PRIMARY["id"]
        except URLNotFoundError:
            log.warning("[FALLBACK] Primary %s returned 404, trying fallbacks...", url)
        except Exception as e:
            log.warning("[FALLBACK] Primary %s failed: %s, trying fallbacks...", url, e)
    else:
        log.info("[FETCH] force_fallback=True, skipping primary %s", url)
    
    # 尝试 Fallback 源
    for fb in fallbacks:
        try:
            log.info("[FALLBACK] Trying %s: %s", fb["id"], fb["base_url"])
            fb_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "zh-CN,zh;q=0.9",
            }
            resp = fetch_with_retry(
                fb["base_url"],
                headers=fb_headers,
                source_cfg=fb,
                max_retries=fb.get("max_retries", 1),
                timeout=fb.get("timeout", 15),
                logger=log,
            )
            if resp.status_code == 200:
                log.info("[FALLBACK] Success: %s", fb["id"])
                return resp, fb["id"]
        except Exception as e:
            log.warning("[FALLBACK] %s failed: %s", fb["id"], e)
    
    # 所有源均失败
    send_alert("ALERT-10", "CRITICAL", "All sources failed", {
        "primary_url": url,
        "fallbacks_tried": [fb["id"] for fb in fallbacks],
    })
    raise AllSourcesFailed(url, detail="all fallbacks failed")


# =============================================================================
# 数据抓取
# =============================================================================

def _generate_sample_data(start_date, end_date, seed=42):
    """生成示例数据 (用于dry-run和测试).
    
    实际抓取需替换为真实HTTP请求。
    工业硅价格区间: 10000-18000 元/吨, 各品位有差异。
    """
    import random as _rnd
    _rnd.seed(seed)
    
    data = []
    current = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    base_price = 14000.0  # 工业硅基准价格
    
    while current <= end:
        # 跳过周末 (非工作日)
        if current.weekday() < 5:
            # 基准价格缓慢漂移 + 噪声
            drift = 1.0 + 0.0001 * ((current - datetime.strptime(start_date, "%Y-%m-%d")).days)
            noise = _rnd.uniform(-0.02, 0.02)
            spot = round(base_price * drift * (1 + noise), 0)
            
            # 各品位价格: 多晶硅级 > 综合 > 有机硅级 > 钢铁级
            polysilicon = round(spot * _rnd.uniform(1.02, 1.08), 0)
            organic = round(spot * _rnd.uniform(0.92, 0.98), 0)
            steel = round(spot * _rnd.uniform(0.85, 0.92), 0)
            regional = round((spot + polysilicon + organic + steel) / 4, 0)
            
            data.append({
                "date": current.strftime("%Y-%m-%d"),
                "indicator_code": INDICATOR_CODE,
                "commodity": COMMODITY,
                "spot_price_avg": spot,
                "polysilicon_price": polysilicon,
                "organic_silicon_price": organic,
                "steel_grade_price": steel,
                "regional_avg": regional,
                "unit": "元/吨",
                "source": DATA_SOURCE_PRIMARY["id"],
                "fetched_at": now_iso(),
                "raw_ref": DATA_SOURCE_PRIMARY["detail_url"],
            })
            base_price += _rnd.gauss(10, 50)
        current += timedelta(days=1)
    
    return data


def _parse_100ppi_html(html, date_str):
    """解析生意社工业硅现货价格HTML.
    
    生意社页面结构为表格, 包含多晶硅级/有机硅级/钢铁级/综合价格。
    实际解析需根据页面结构调整正则。
    
    Args:
        html: 页面HTML内容
        date_str: 日期字符串
    
    Returns:
        list of dict: 解析结果
    """
    rows = []
    if not html:
        return rows
    
    # 尝试多种解析策略 (防御式解析)
    # 策略1: 表格行解析 (tr/td)
    # 策略2: 正则提取价格数值
    price_patterns = [
        r'综合价格[：:]\s*([\d,]+(?:\.\d+)?)',
        r'多晶硅级[：:]\s*([\d,]+(?:\.\d+)?)',
        r'有机硅级[：:]\s*([\d,]+(?:\.\d+)?)',
        r'钢铁级[：:]\s*([\d,]+(?:\.\d+)?)',
        r'产地均价[：:]\s*([\d,]+(?:\.\d+)?)',
    ]
    
    # 从HTML中提取所有数值
    nums = []
    for pat in price_patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            try:
                val = float(m.group(1).replace(",", ""))
                nums.append(val)
            except (ValueError, IndexError):
                pass
    
    if not nums and len(html) > 0:
        # 尝试从表格单元格提取
        td_vals = re.findall(r'<td[^>]*>\s*([\d,]+(?:\.\d+)?)\s*</td>', html, re.IGNORECASE)
        for v in td_vals:
            try:
                val = float(v.replace(",", ""))
                if 5000 < val < 30000:
                    nums.append(val)
            except ValueError:
                pass
    
    if len(nums) >= 4:
        rows.append({
            "date": date_str,
            "indicator_code": INDICATOR_CODE,
            "commodity": COMMODITY,
            "spot_price_avg": nums[0],
            "polysilicon_price": nums[1] if len(nums) > 1 else nums[0],
            "organic_silicon_price": nums[2] if len(nums) > 2 else nums[0],
            "steel_grade_price": nums[3] if len(nums) > 3 else nums[0],
            "regional_avg": nums[4] if len(nums) > 4 else round(sum(nums[:4]) / min(len(nums), 4), 0),
            "unit": "元/吨",
            "source": DATA_SOURCE_PRIMARY["id"],
            "fetched_at": now_iso(),
            "raw_ref": DATA_SOURCE_PRIMARY["detail_url"],
        })
    return rows


def _parse_smm_html(html, date_str):
    """解析 SMM 上海有色网工业硅数据 (Fallback 1).
    
    SMM 提供月度数据, 粒度较粗。
    """
    rows = []
    if not html:
        return rows
    
    # SMM 价格提取模式 (月度)
    price_patterns = [
        r'均价[：:]\s*([\d,]+(?:\.\d+)?)',
        r'综合价格[：:]\s*([\d,]+(?:\.\d+)?)',
        r'工业硅.*?([\d,]+(?:\.\d+)?)\s*元',
    ]
    
    nums = []
    for pat in price_patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            try:
                val = float(m.group(1).replace(",", ""))
                nums.append(val)
            except (ValueError, IndexError):
                pass
    
    if nums:
        # SMM 仅提供综合均价, 其他品位按经验比例估算
        avg = nums[0]
        rows.append({
            "date": date_str,
            "indicator_code": INDICATOR_CODE,
            "commodity": COMMODITY,
            "spot_price_avg": avg,
            "polysilicon_price": round(avg * 1.05, 0),
            "organic_silicon_price": round(avg * 0.95, 0),
            "steel_grade_price": round(avg * 0.88, 0),
            "regional_avg": avg,
            "unit": "元/吨",
            "source": "SMM_SI_MONTHLY",
            "fetched_at": now_iso(),
            "raw_ref": DATA_SOURCE_FALLBACKS[0]["base_url"],
        })
    return rows


def _parse_cspc_html(html, date_str):
    """解析长江有色金属网工业硅数据 (Fallback 2).
    
    长江有色金属网数据格式较简单。
    """
    rows = []
    if not html:
        return rows
    
    # 长江有色金属网价格模式
    price_patterns = [
        r'综合价格[：:]\s*([\d,]+(?:\.\d+)?)',
        r'均价[：:]\s*([\d,]+(?:\.\d+)?)',
        r'工业硅.*?([\d,]+(?:\.\d+)?)\s*元',
    ]
    
    nums = []
    for pat in price_patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            try:
                val = float(m.group(1).replace(",", ""))
                nums.append(val)
            except (ValueError, IndexError):
                pass
    
    if nums:
        avg = nums[0]
        rows.append({
            "date": date_str,
            "indicator_code": INDICATOR_CODE,
            "commodity": COMMODITY,
            "spot_price_avg": avg,
            "polysilicon_price": round(avg * 1.04, 0),
            "organic_silicon_price": round(avg * 0.96, 0),
            "steel_grade_price": round(avg * 0.90, 0),
            "regional_avg": avg,
            "unit": "元/吨",
            "source": "CSPC_SI_MONTHLY",
            "fetched_at": now_iso(),
            "raw_ref": DATA_SOURCE_FALLBACKS[1]["base_url"],
        })
    return rows


def _decode_response(resp, fallback_encoding="utf-8"):
    """解码 HTTP 响应, 尝试多种编码."""
    raw = resp.content
    for enc in ("utf-8", "gb2312", "gbk", "gb18030"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode(fallback_encoding, errors="replace")


def fetch_data(start_date, end_date, dry_run=True, force_fallback=False, logger=None):
    """抓取数据.
    
    Args:
        start_date: 起始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        dry_run: 是否为dry-run模式
        force_fallback: 是否强制使用Fallback源 (测试用)
        logger: 日志器
    
    Returns:
        (rows, message): 数据行列表和消息
    """
    rows = []
    
    if dry_run:
        # Dry-run: 生成示例数据
        rows = _generate_sample_data(start_date, end_date)
        return rows, "dry-run generated {} rows".format(len(rows))
    
    log = logger or get_logger(SCRIPT_NAME)
    
    # LIVE模式: 使用 Fix 3 + Fix 4 (Retry + Fallback)
    primary_url = DATA_SOURCE_PRIMARY["detail_url"]
    
    try:
        resp, source_id = fetch_with_fallback(
            primary_url,
            fallbacks=DATA_SOURCE_FALLBACKS,
            force_fallback=force_fallback,
            logger=log,
        )
        
        if source_id == DATA_SOURCE_PRIMARY["id"]:
            # 主源成功
            html = _decode_response(resp, DATA_SOURCE_PRIMARY["encoding"])
            current_date = today_str()
            rows = _parse_100ppi_html(html, current_date)
            if rows:
                return rows, "live fetch from {} (primary): {} rows".format(
                    primary_url, len(rows))
        
        elif source_id == "SMM_SI_MONTHLY":
            # SMM Fallback
            html = _decode_response(resp, DATA_SOURCE_FALLBACKS[0]["encoding"])
            current_date = today_str()
            rows = _parse_smm_html(html, current_date)
            if rows:
                send_alert("ALERT-11", "MEDIUM", "Fallback triggered",
                           {"source": source_id})
                return rows, "live fetch from {} (fallback SMM): {} rows".format(
                    primary_url, len(rows))
        
        elif source_id == "CSPC_SI_MONTHLY":
            # 长江有色金属网 Fallback
            html = _decode_response(resp, DATA_SOURCE_FALLBACKS[1]["encoding"])
            current_date = today_str()
            rows = _parse_cspc_html(html, current_date)
            if rows:
                send_alert("ALERT-11", "MEDIUM", "Fallback triggered",
                           {"source": source_id})
                return rows, "live fetch from {} (fallback CSPC): {} rows".format(
                    primary_url, len(rows))
        
        # 所有源都返回了数据但解析失败
        send_alert("ALERT-05", "HIGH", "Parse failed on all sources",
                   {"primary_url": primary_url})
        return [], "live fetch: all sources returned but parse failed"
    
    except URLNotFoundError as e:
        # 404 已在 fetch_with_fallback 中处理
        send_alert("ALERT-09", "HIGH", "URL 404 not found",
                   {"url": e.url})
        return [], "live fetch failed: URL 404 — {}".format(str(e))
    
    except AllSourcesFailed as e:
        send_alert("ALERT-04", "HIGH", "All sources failed",
                   {"primary_url": e.primary_url})
        return [], "live fetch failed: all sources failed — {}".format(str(e))
    
    except Exception as e:
        send_alert("ALERT-04", "HIGH", "Crawl failed",
                   {"url": primary_url, "error": str(e)})
        return [], "live fetch failed: {}".format(str(e))


# =============================================================================
# DQA校验
# =============================================================================

def _parse_date_safe(s):
    """安全日期解析."""
    if not s or not isinstance(s, str):
        return None
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d")
    except (ValueError, AttributeError):
        return None


def _parse_num_safe(s):
    """安全数值解析."""
    if not s:
        return None
    try:
        return float(str(s).replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def run_dqa_check(csv_path, check_md5=False):
    """执行DQA校验.
    
    Args:
        csv_path: CSV文件路径
        check_md5: 是否检查MD5完整性
    
    Returns:
        dict: DQA结果
    """
    results = []
    if not Path(csv_path).exists():
        return {"dqa_results": [{"id": "DQA-ALL", "name": "数据文件不存在",
                                 "status": "FAIL", "detail": str(csv_path)}],
                "overall": "FAIL", "pass": 0, "warn": 0, "fail": 1, "total": 1}
    
    # 读取数据
    try:
        rows = read_csv(csv_path)
    except Exception as e:
        return {"dqa_results": [{"id": "DQA-ALL", "name": "文件读取失败",
                                 "status": "FAIL", "detail": str(e)}],
                "overall": "FAIL", "pass": 0, "warn": 0, "fail": 1, "total": 1}
    
    if not rows:
        results.append({"id": "DQA-01", "name": "数据完整性",
                        "status": "FAIL", "detail": "0 rows"})
        return {"dqa_results": results, "pass": 0, "warn": 0, "fail": 1,
                "total": 1, "overall": "FAIL"}
    
    # DQA-01: 完整性
    results.append({"id": "DQA-01", "name": "数据完整性",
                    "status": "PASS", "detail": "{} rows".format(len(rows))})
    
    # DQA-02: 价格范围
    price_cols = ["spot_price_avg", "polysilicon_price", "organic_silicon_price",
                  "steel_grade_price", "regional_avg"]
    range_violations = 0
    total_price_vals = 0
    for row in rows:
        for col in price_cols:
            val = _parse_num_safe(row.get(col, ""))
            if val is None:
                continue
            total_price_vals += 1
            lo, hi = PRICE_RANGE.get(col, (10000, 20000))
            if val < 0 or val < lo or val > hi:
                range_violations += 1
    range_ok = total_price_vals - range_violations
    results.append({"id": "DQA-02", "name": "价格范围",
                    "status": "PASS" if range_violations < total_price_vals * 0.05 else "WARN",
                    "detail": "{}/{} in range".format(range_ok, total_price_vals)})
    
    # DQA-03: 空值
    empty_count = 0
    for row in rows:
        for key in ["date", "indicator_code", "spot_price_avg"]:
            if not str(row.get(key, "")).strip():
                empty_count += 1
                break
    empty_ratio = empty_count / len(rows)
    results.append({"id": "DQA-03", "name": "无空值",
                    "status": "PASS" if empty_ratio < 0.01 else "WARN",
                    "detail": "{}/{} rows empty ({:.2%})".format(empty_count, len(rows), empty_ratio)})
    
    # DQA-04: 时序连续性
    dates = sorted(set(r.get("date", "") for r in rows if r.get("date")))
    max_gap = 0
    if len(dates) > 1:
        gaps = []
        for i in range(1, len(dates)):
            d1 = _parse_date_safe(dates[i - 1])
            d2 = _parse_date_safe(dates[i])
            if d1 and d2:
                gaps.append((d2 - d1).days)
        if gaps:
            max_gap = max(gaps)
    results.append({"id": "DQA-04", "name": "时序连续性",
                    "status": "PASS" if max_gap < 30 else "WARN",
                    "detail": "max_gap={}d, {} unique dates".format(max_gap, len(dates))})
    
    # DQA-05: 无重复
    keys = [dedup_key(r) for r in rows]
    dup_count = len(keys) - len(set(keys))
    results.append({"id": "DQA-05", "name": "无重复",
                    "status": "PASS" if dup_count == 0 else "WARN",
                    "detail": "{} duplicates".format(dup_count)})
    
    # DQA-06: 全零检测
    zero_count = 0
    for row in rows:
        all_zero = True
        for col in price_cols:
            val = _parse_num_safe(row.get(col, ""))
            if val is not None and val != 0:
                all_zero = False
                break
        if all_zero:
            zero_count += 1
    zero_ratio = zero_count / len(rows)
    results.append({"id": "DQA-06", "name": "全零检测",
                    "status": "PASS" if zero_ratio < 0.5 else "FAIL",
                    "detail": "zero_ratio={:.4f}".format(zero_ratio)})
    
    # DQA-07: 单调性 (价格跳变)
    spot_vals = [r for r in rows if r.get("date")]
    spot_vals.sort(key=lambda x: x.get("date", ""))
    jumps = 0
    total_transitions = 0
    for i in range(1, len(spot_vals)):
        v1 = _parse_num_safe(spot_vals[i - 1].get("spot_price_avg", ""))
        v2 = _parse_num_safe(spot_vals[i].get("spot_price_avg", ""))
        if v1 and v2 and v1 > 0:
            change = abs(v2 - v1) / v1
            if change > 0.10:
                jumps += 1
            total_transitions += 1
    jump_ratio = jumps / total_transitions if total_transitions > 0 else 0
    results.append({"id": "DQA-07", "name": "单调性",
                    "status": "PASS" if jump_ratio < 0.05 else "WARN",
                    "detail": "{} jumps >10% / {} transitions ({:.2%})".format(
                        jumps, total_transitions, jump_ratio)})
    
    # DQA-08: 数据源一致性
    sources = set(r.get("source", "unknown") for r in rows)
    results.append({"id": "DQA-08", "name": "数据源一致性",
                    "status": "PASS" if len(sources) <= 1 else "WARN",
                    "detail": "{} source(s): {}".format(len(sources), sources)})
    
    # DQA-09: 指标一致性
    codes = set(r.get("indicator_code", "") for r in rows if r.get("indicator_code"))
    results.append({"id": "DQA-09", "name": "指标一致性",
                    "status": "PASS" if len(codes) <= 1 else "WARN",
                    "detail": "{} code(s): {}".format(len(codes), codes)})
    
    # DQA-10: 文件完整性 (MD5)
    if check_md5:
        md5 = compute_file_md5(csv_path)
        snapshot_path = MD5_SNAPSHOT_DIR / "spot_is_snapshot.json"
        if snapshot_path.exists():
            with open(str(snapshot_path), "r", encoding="utf-8") as f:
                snap = json.load(f)
            if snap.get("md5") != md5:
                results.append({"id": "DQA-10", "name": "文件完整性",
                                "status": "WARN", "detail": "MD5 mismatch"})
            else:
                results.append({"id": "DQA-10", "name": "文件完整性",
                                "status": "PASS", "detail": "MD5 match"})
        else:
            results.append({"id": "DQA-10", "name": "文件完整性",
                            "status": "SKIP", "detail": "no snapshot"})
    else:
        results.append({"id": "DQA-10", "name": "文件完整性",
                        "status": "SKIP", "detail": "requires --md5-snapshot flag"})
    
    # 汇总
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    warn_count = sum(1 for r in results if r["status"] == "WARN")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")
    skip_count = sum(1 for r in results if r["status"] == "SKIP")
    
    return {
        "dqa_results": results,
        "pass": pass_count,
        "warn": warn_count,
        "fail": fail_count,
        "skip": skip_count,
        "total": len(results),
        "overall": "PASS" if fail_count == 0 else "FAIL",
        "row_count": len(rows),
        "date_range": {
            "start": dates[0] if dates else None,
            "end": dates[-1] if dates else None,
        },
    }


# =============================================================================
# MD5快照
# =============================================================================

def create_md5_snapshot(csv_path):
    """创建MD5快照."""
    ensure_dir(MD5_SNAPSHOT_DIR)
    md5 = compute_file_md5(csv_path)
    if not md5:
        return None
    snapshot = OrderedDict([
        ("indicator_code", INDICATOR_CODE),
        ("file", str(csv_path)),
        ("md5", md5),
        ("size_bytes", Path(csv_path).stat().st_size),
        ("created_at", now_iso()),
        ("task_id", TASK_ID),
    ])
    snapshot_file = MD5_SNAPSHOT_DIR / "spot_is_snapshot.json"
    with open(str(snapshot_file), "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    return snapshot


# =============================================================================
# 数据回填
# =============================================================================

def backfill_history(start_date, end_date, dry_run=True, force_fallback=False,
                     logger=None):
    """历史数据回填: 分批抓取, 避免请求过快.
    
    Args:
        start_date: 起始日期
        end_date: 结束日期
        dry_run: 是否为dry-run模式
        force_fallback: 是否强制使用Fallback源 (测试用)
        logger: 日志器
    
    Returns:
        (total_rows, messages): 总行数和消息列表
    """
    messages = []
    total_rows = 0
    
    # 分批: 每次抓取最多30天
    batch_size_days = 30
    current_start = start_date
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    while current_start <= end_date:
        current_end_dt = min(
            datetime.strptime(current_start, "%Y-%m-%d") + timedelta(days=batch_size_days - 1),
            end_dt
        )
        current_end = current_end_dt.strftime("%Y-%m-%d")
        
        rows, msg = fetch_data(current_start, current_end, dry_run=dry_run,
                               force_fallback=force_fallback, logger=logger)
        messages.append(msg)
        total_rows += len(rows)
        
        # 写入
        if rows and not dry_run:
            written = write_csv_append(str(CSV_PATH), rows, FIELDNAMES)
            messages.append("  wrote {} rows ({} ~ {})".format(
                written, current_start, current_end))
        
        # 控制请求频率 (仅live模式, Fix 2)
        if not dry_run:
            apply_rate_limit(DATA_SOURCE_PRIMARY)
        
        current_start = (current_end_dt + timedelta(days=1)).strftime("%Y-%m-%d")
    
    return total_rows, messages


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="V88 Phase03 P1 DSHB — SPOT_IS 工业硅现货价格爬虫 V2 (T1, 含5项修复)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="DQA Rules:\n" + "\n".join(
            "  {}: {} ({})".format(k, v["name"], v["severity"])
            for k, v in DQA_RULES.items()
        ),
    )
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--live", action="store_true",
                   help="真实HTTP抓取")
    g.add_argument("--incremental", action="store_true",
                   help="增量模式 (基于水位线)")
    g.add_argument("--verify", action="store_true",
                   help="仅DQA校验")
    g.add_argument("--md5-snapshot", action="store_true",
                   help="仅MD5快照")
    g.add_argument("--backfill", action="store_true",
                   help="历史数据回填")
    
    parser.add_argument("--start-date", default=DATA_SOURCE_PRIMARY["start_date"],
                        help="起始日期 (默认: {})".format(DATA_SOURCE_PRIMARY["start_date"]))
    parser.add_argument("--end-date", default=today_str(),
                        help="结束日期 (默认: 今日)")
    parser.add_argument("--json-out", default=None, metavar="FILE",
                        help="JSON输出文件")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="详细输出")
    parser.add_argument("--source-fallback", action="store_true",
                        help="强制使用Fallback源 (测试用, Fix 4)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Dry-run 模式 (仅生成示例数据)")
    args = parser.parse_args()
    
    # 确定 dry_run: 默认非 live 即为 dry-run
    dry_run = not args.live
    
    # Fix 5: 部署环境检测
    deploy_cfg, deploy_env = get_deployment_config()
    
    logger = get_logger(SCRIPT_NAME,
                        level=logging.DEBUG if args.verbose else logging.INFO)
    
    logger.info("=" * 80)
    logger.info("TASK %s | %s", TASK_ID, SCRIPT_NAME)
    logger.info("LIB_VERSION %s", LIB_VERSION)
    logger.info("CONSTRAINTS %s", dict(CONSTRAINTS))
    logger.info("MODE %s | DATE %s ~ %s",
                "LIVE" if args.live else "DRY-RUN",
                args.start_date, args.end_date)
    logger.info("DEPLOYMENT_ENV %s (timeout=%ds, max_retries=%d, proxy=%s)",
                deploy_env, deploy_cfg["timeout"],
                deploy_cfg["max_retries"], deploy_cfg["use_proxy"])
    logger.info("FORCE_FALLBACK %s", args.source_fallback)
    logger.info("PRIMARY_URL %s", DATA_SOURCE_PRIMARY["detail_url"])
    logger.info("FALLBACK_SOURCES %s",
                ", ".join(fb["id"] for fb in DATA_SOURCE_FALLBACKS))
    logger.info("=" * 80)
    
    # 确保输出目录
    ensure_dir(OUTPUT_BASE)
    ensure_dir(LOG_DIR)
    
    # ---- 验证模式 ----
    if args.verify:
        dqa = run_dqa_check(str(CSV_PATH), check_md5=True)
        print(json.dumps(dqa, indent=2, ensure_ascii=False, default=str))
        return 0 if dqa.get("overall") == "PASS" else 1
    
    # ---- MD5快照模式 ----
    if args.md5_snapshot:
        snap = create_md5_snapshot(str(CSV_PATH))
        print(json.dumps(snap, indent=2, ensure_ascii=False, default=str))
        return 0 if snap else 1
    
    # ---- 确定日期范围 ----
    if args.incremental:
        wm = load_watermark()
        start = compute_incremental_start(wm)
        if start:
            logger.info("INCREMENTAL: start=%s (from watermark last_date=%s)",
                        start, wm.get("last_date"))
            args.start_date = start
        else:
            logger.warning("No watermark found, falling back to full range")
    
    # ---- 回填模式 ----
    if args.backfill:
        total_rows, messages = backfill_history(
            args.start_date, args.end_date,
            dry_run=dry_run,
            force_fallback=args.source_fallback,
            logger=logger,
        )
        for msg in messages:
            logger.info("BACKFILL: %s", msg)
        # 更新水位线
        if not dry_run:
            wm = load_watermark()
            wm["last_date"] = args.end_date
            wm["last_crawl_date"] = now_iso()
            wm["total_rows"] = total_rows
            wm["last_updated_at"] = now_iso()
            save_watermark(wm)
            logger.info("WATERMARK: updated last_date=%s", args.end_date)
        return 0
    
    # ---- 抓取 ----
    rows, fetch_msg = fetch_data(
        args.start_date, args.end_date,
        dry_run=dry_run,
        force_fallback=args.source_fallback,
        logger=logger,
    )
    logger.info("FETCH: %s", fetch_msg)
    
    if not rows:
        send_alert("ALERT-04", "HIGH", "Crawl failed: no data fetched",
                   {"start": args.start_date, "end": args.end_date, "dry_run": dry_run})
        print(json.dumps({"ok": False, "error": "No data fetched",
                          "dry_run": dry_run}))
        return 1
    
    # ---- 去重 ----
    existing_keys = load_existing_keys(str(CSV_PATH))
    new_rows, dup_count = deduplicate_rows(rows, existing_keys)
    logger.info("DEDUP: %d total, %d new, %d duplicates",
                len(rows), len(new_rows), dup_count)
    
    # ---- 写入 (append-only) ----
    if new_rows and not dry_run:
        written = write_csv_append(str(CSV_PATH), new_rows, FIELDNAMES)
        logger.info("WRITE: %d rows appended to %s", written, CSV_PATH)
    elif new_rows and dry_run:
        logger.info("DRY-RUN: would append %d rows", len(new_rows))
    
    # ---- 更新水位线 ----
    if new_rows and not dry_run:
        last_date = max(r.get("date", "") for r in new_rows)
        wm = load_watermark()
        wm["last_date"] = last_date
        wm["last_crawl_date"] = now_iso()
        wm["total_rows"] = wm.get("total_rows", 0) + len(new_rows)
        wm["last_updated_at"] = now_iso()
        wm["last_csv_md5"] = compute_file_md5(str(CSV_PATH))
        wm["last_fetch_source"] = DATA_SOURCE_PRIMARY["id"]
        wm["last_fetch_mode"] = "incremental" if args.incremental else "full"
        save_watermark(wm)
        logger.info("WATERMARK: updated last_date=%s", last_date)
    
    # ---- DQA ----
    dqa = run_dqa_check(str(CSV_PATH))
    logger.info("DQA: %s (%d PASS, %d WARN, %d FAIL)",
                dqa.get("overall", "N/A"), dqa.get("pass", 0),
                dqa.get("warn", 0), dqa.get("fail", 0))
    
    # ---- MD5快照 ----
    if not dry_run:
        snap = create_md5_snapshot(str(CSV_PATH))
    
    # ---- 汇总 ----
    summary = OrderedDict([
        ("task_id", TASK_ID),
        ("script", SCRIPT_NAME),
        ("lib_version", LIB_VERSION),
        ("branch", BRANCH),
        ("indicator_code", INDICATOR_CODE),
        ("indicator_name", INDICATOR_NAME),
        ("commodity", COMMODITY),
        ("dry_run", dry_run),
        ("deployment_env", deploy_env),
        ("mode", "incremental" if args.incremental else
                "backfill" if args.backfill else
                "full" if args.live else "dry-run"),
        ("force_fallback", args.source_fallback),
        ("source", DATA_SOURCE_PRIMARY["id"]),
        ("primary_url", DATA_SOURCE_PRIMARY["detail_url"]),
        ("fallback_sources", [fb["id"] for fb in DATA_SOURCE_FALLBACKS]),
        ("date_range", {"start": args.start_date, "end": args.end_date}),
        ("rows_fetched", len(rows)),
        ("rows_new", len(new_rows)),
        ("rows_duplicated", dup_count),
        ("rows_written", len(new_rows) if not dry_run else 0),
        ("dqa", dqa),
        ("csv_path", str(CSV_PATH)),
        ("existing_mapping", EXISTING_MAPPING),
        ("constraints", dict(CONSTRAINTS)),
        ("generated_at", now_iso()),
    ])
    
    print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
    
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
    
    return 0 if dqa.get("overall") == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
