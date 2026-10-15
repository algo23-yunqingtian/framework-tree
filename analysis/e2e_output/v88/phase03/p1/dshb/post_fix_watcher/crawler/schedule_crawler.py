#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
schedule_crawler.py — 外部爬虫每日调度器 (Cron-like Scheduler)
===============================================================
TASK_ID: V88_PHASE03_P1_DSHB_POST_FIX_WATCHER_EXTEND_JOB (T2)
AGENT:   DSHB | BRANCH: feature/v88-g1

Purpose
-------
编排 3 个外部数据作业的日常执行, 带 cron 式调度、错误处理与报告:

    job_id        script                   默认 cron      数据内容
    -----------   ----------------------   -----------    ----------------
    comex_daily   comex_daily_crawler.py   0 8 * * 1-5    COMEX 5 金属仓单库存
    lc_fu_daily   lc_fu_crawler.py         30 18 * * 1-5  LC 碳酸锂期货行情
    dqa_ext       crawler_dqa_check.py     0 19 * * 1-5   外部原始数据 DQA 校验

调度说明:
    * cron 表达式为 5 字段标准格式 "分 时 日 月 周", 0-6 = 周日..周六 (7 亦为周日)。
    * 日/周 同时受限时采用标准 cron 的 OR 语义 (任一命中即执行)。
    * 表达式按本地系统时间求值, 设计时假设 Asia/Shanghai (UTC+8)。
      用 --tz-offset-hours 可显式校正; 用 --now 可注入当前时间做离线测试。
    * 错过窗口 (--catch-up-minutes) 内的作业在下次唤醒时补跑。

约束 (继承任务书):
    NO_ZHIJI_API_CALL  不 import / 不执行 zhiji_api.py
    NO_OVERWRITE       调度器自身只写 checkpoint / audit / report
    APPEND_ONLY        audit JSONL 与 log 只追加
    DRY_RUN            默认 True -> 子进程收到 --dry-run (不发网络、不落 raw)

Usage
-----
    python schedule_crawler.py --list                     # 打印作业表 + 下次运行时间
    python schedule_crawler.py --status                   # 同 --list, 含运行历史
    python schedule_crawler.py --once                     # 立即执行全部作业 (dry-run)
    python schedule_crawler.py --once --job dqa_ext       # 只执行一个作业
    python schedule_crawler.py --cron --max-cycles 2      # 守护模式 (限制循环数)
    python schedule_crawler.py --cron --max-sleep 5       # 守护模式 (缩短轮询)
    python schedule_crawler.py --once --live              # 真实执行子爬虫
    python schedule_crawler.py --no-exec --now 2026-10-15T08:00:00   # 只算调度, 不启动子进程

退出码:
    0 = 全部作业成功; 4 = 至少一个作业失败; 1 = 用法/环境错误
"""

import os
import sys
import re
import json
import argparse
import logging
import subprocess
import time
from pathlib import Path
from collections import OrderedDict
from datetime import datetime, date, timedelta

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
RUN_RESULT_DIR = LOG_DIR / "run_results"
SCRIPT_NAME = "schedule_crawler"
AUDIT_LOG = LOG_DIR / "schedule_crawler_audit.jsonl"
CHECKPOINT_FILE = LOG_DIR / "schedule_crawler_checkpoint.json"
JOB_LOG_DIR = LOG_DIR / "job_stdout"

DEFAULT_TZ_OFFSET_HOURS = 8.0      # 设计基线: Asia/Shanghai
DEFAULT_JOB_TIMEOUT = 900          # 单作业超时 (秒)
DEFAULT_CATCHUP_MINUTES = 60       # 错过窗口补跑范围
DEFAULT_MAX_SLEEP = 60             # 守护模式最大单次休眠 (秒)

# 作业表: cron 时刻为 Asia/Shanghai 的「数据发布后」时间
JOBS = [
    OrderedDict([
        ("id", "comex_daily"),
        ("script", "comex_daily_crawler.py"),
        ("cron", "0 8 * * 1-5"),
        ("description", "COMEX AL/NI/PB/SN/ZN 仓单库存 (LME Stocks & Warrants)"),
        ("extra_args", []),
    ]),
    OrderedDict([
        ("id", "lc_fu_daily"),
        ("script", "lc_fu_crawler.py"),
        ("cron", "30 18 * * 1-5"),
        ("description", "LC 碳酸锂期货行情 (SHFE .dat, 东方财富 fallback)"),
        ("extra_args", []),
    ]),
    OrderedDict([
        ("id", "dqa_ext"),
        ("script", "crawler_dqa_check.py"),
        ("cron", "0 19 * * 1-5"),
        ("description", "外部原始数据 DQA 校验 (DQA-EXT-01..06)"),
        ("extra_args", []),
    ]),
]

JOB_TIMEOUT_OVERRIDES = {
    "comex_daily": 1200,
    "lc_fu_daily": 600,
    "dqa_ext": 600,
}


# =============================================================================
# Cron 表达式解析 (仅标准库)
# =============================================================================

MONTH_NAMES = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
               "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
DOW_NAMES = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}
FIELD_SPECS = [
    ("minute", 0, 59, {}),
    ("hour", 0, 23, {}),
    ("day_of_month", 1, 31, {}),
    ("month", 1, 12, MONTH_NAMES),
    ("day_of_week", 0, 7, DOW_NAMES),   # 7 归一化为 0 (周日)
]


class CronError(ValueError):
    pass


def _parse_field(token, lo, hi, names, field_name):
    """解析单个 cron 字段 -> set[int]。支持 * , - / 与名称。"""
    token = token.strip().lower()
    if not token:
        raise CronError("empty %s field" % field_name)
    out = set()
    for part in token.split(","):
        part = part.strip()
        if not part:
            raise CronError("empty part in %s field" % field_name)
        step = 1
        if "/" in part:
            base, step_s = part.split("/", 1)
            try:
                step = int(step_s)
            except ValueError:
                raise CronError("bad step %r in %s field" % (step_s, field_name))
            if step <= 0:
                raise CronError("step must be > 0 in %s field" % field_name)
            part = base
        if part == "*":
            start, end = lo, hi
        elif "-" in part:
            a, b = part.split("-", 1)
            start, end = _val(a, names, field_name), _val(b, names, field_name)
        else:
            start = end = _val(part, names, field_name)
        if start > end:
            # 跨边界范围 (如 dow 5-1 = 周五..周一): 环绕展开后再按 step 抽样
            span = list(range(start, hi + 1)) + list(range(lo, end + 1))
        else:
            span = list(range(start, end + 1))
        for i, v in enumerate(span):
            if i % step == 0:
                out.add(_norm(v, field_name))
    return out


def _val(token, names, field_name):
    token = token.strip()
    if token.isdigit():
        return int(token)
    if token in names:
        return names[token]
    raise CronError("bad value %r in %s field" % (token, field_name))


def _norm(v, field_name):
    if field_name == "day_of_week" and v == 7:
        return 0
    return v


class CronSpec(object):
    """5 字段 cron 表达式: 分 时 日 月 周。"""

    def __init__(self, expr):
        self.expr = expr
        parts = str(expr).split()
        if len(parts) != 5:
            raise CronError("cron expr needs 5 fields, got %r" % expr)
        self._dom_restricted = parts[2] != "*"
        self._dow_restricted = parts[4] != "*"
        self.minutes = set()
        self.hours = set()
        self.dom = set()
        self.months = set()
        self.dow = set()
        for (name, lo, hi, names), token in zip(FIELD_SPECS, parts):
            vals = _parse_field(token, lo, hi, names, name)
            setattr(self, name, vals)
        if not self.minutes or not self.hours:
            raise CronError("empty minute/hour set")

    def _day_matches(self, d):
        if d.month not in self.months:
            return False
        dom_ok = d.day in self.dom
        dow_ok = d.weekday() in self.dow      # Python: 0=Mon..6=Sun
        # Python weekday -> cron dow (0=Sun..6=Sat)
        cron_dow = (d.weekday() + 1) % 7
        dow_ok = cron_dow in self.dow
        if self._dom_restricted and self._dow_restricted:
            return dom_ok or dow_ok
        return dom_ok and dow_ok

    def matches(self, dt):
        return (dt.second == 0 and dt.minute in self.minutes
                and dt.hour in self.hours and self._day_matches(dt.date()))

    def next_run(self, after):
        """返回 strictly after 的下一个匹配时刻; 找不到返回 None。"""
        start = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
        cur = start.date()
        for day_offset in range(366 * 2):
            day = cur + timedelta(days=day_offset)
            if not self._day_matches(day):
                continue
            for h in sorted(self.hours):
                for mi in sorted(self.minutes):
                    cand = datetime(day.year, day.month, day.day, h, mi)
                    if cand >= start:
                        return cand
        return None

    def describe(self):
        return "cron(%s) minutes=%d hours=%d" % (
            self.expr, len(self.minutes), len(self.hours))


def parse_iso(value):
    """宽松 ISO8601 解析 -> datetime。"""
    if not value:
        return None
    s = str(value).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M", "%Y-%m-%d", C.ISO_FMT):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


# =============================================================================
# Checkpoint / audit
# =============================================================================

def load_checkpoint():
    if CHECKPOINT_FILE.exists():
        try:
            with open(str(CHECKPOINT_FILE), "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
    return None


def save_checkpoint(state):
    C.ensure_dir(CHECKPOINT_FILE.parent)
    with open(str(CHECKPOINT_FILE), "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False, default=str)
        f.flush()
        os.fsync(f.fileno())


def default_checkpoint():
    return OrderedDict([
        ("task_id", TASK_ID),
        ("agent", AGENT),
        ("branch", BRANCH),
        ("library_version", C.LIB_VERSION),
        ("script", SCRIPT_NAME),
        ("created_at", C.now_iso()),
        ("jobs_run_total", 0),
        ("jobs_ok_total", 0),
        ("jobs_failed_total", 0),
        ("jobs", OrderedDict((j["id"], OrderedDict([
            ("runs", 0), ("ok", 0), ("failed", 0),
            ("last_started_at", None), ("last_finished_at", None),
            ("last_exit_code", None), ("last_error", None),
            ("last_cron_fire", None),
        ])) for j in JOBS)),
    ])


# =============================================================================
# Job execution
# =============================================================================

def build_job_cmd(job, dry_run, extra_args=None):
    """构造子进程命令行。"""
    script = CRAWLER_DIR / job["script"]
    cmd = [sys.executable, str(script)]
    if dry_run:
        cmd.append("--dry-run")
    else:
        cmd.append("--live")
    for a in (job.get("extra_args") or []):
        cmd.append(a)
    for a in (extra_args or []):
        cmd.append(a)
    return cmd


def run_job(job, args, logger, audit, checkpoint):
    """执行单个作业。返回结果 dict。"""
    script_path = CRAWLER_DIR / job["script"]
    result = OrderedDict([
        ("job_id", job["id"]),
        ("script", job["script"]),
        ("cron", job["cron"]),
        ("dry_run", bool(args.dry_run)),
        ("started_at", C.now_iso()),
        ("ok", False), ("exit_code", None), ("duration_sec", 0.0),
        ("cmd", None), ("stdout_tail", ""), ("stderr_tail", ""),
        ("error", None),
    ])

    if not script_path.exists():
        result["error"] = "script not found: %s" % script_path
        logger.error("JOB %s %s" % (job["id"], result["error"]))
        return result

    cmd = build_job_cmd(job, args.dry_run, args.job_args)
    result["cmd"] = " ".join(cmd)
    timeout = int(JOB_TIMEOUT_OVERRIDES.get(job["id"], args.job_timeout))

    if args.no_exec:
        result["ok"] = True
        result["exit_code"] = 0
        result["error"] = "no-exec: command planned but not launched"
        if logger:
            logger.info("NO-EXEC %s -> %s" % (job["id"], result["cmd"]))
        return result

    # 作业 stdout/stderr 落盘 (追加), 便于事后追溯
    joblog = JOB_LOG_DIR / ("%s.log" % job["id"])
    C.ensure_dir(joblog.parent)

    started = time.time()
    if logger:
        logger.info("JOB %s START %s (timeout=%ds)" % (job["id"], result["cmd"], timeout))
    try:
        with open(str(joblog), "a", encoding="utf-8") as fh:
            fh.write("\n===== %s JOB %s (dry_run=%s) =====\n" % (
                result["started_at"], job["id"], args.dry_run))
            fh.flush()
            proc = subprocess.run(
                cmd,
                stdout=fh,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
                cwd=str(CRAWLER_DIR),
            )
            exit_code = proc.returncode
    except subprocess.TimeoutExpired as e:
        exit_code = 124
        result["error"] = "timeout after %ds" % timeout
        result["stdout_tail"] = (e.output or b"").decode("utf-8", "replace")[-400:] \
            if isinstance(e.output, bytes) else str(e.output)[-400:]
        if logger:
            logger.error("JOB %s %s" % (job["id"], result["error"]))
    except FileNotFoundError as e:
        exit_code = 127
        result["error"] = "interpreter not found: %s" % e
    except Exception as e:                            # noqa: BLE001
        exit_code = -1
        result["error"] = "%s: %s" % (type(e).__name__, e)

    result["exit_code"] = exit_code
    result["duration_sec"] = round(time.time() - started, 2)
    result["ok"] = (exit_code == 0)
    result["log_file"] = str(joblog)

    # 尾部输出 (最多 400 字符) 便于在报告里直接看到失败原因
    try:
        if joblog.exists():
            data = joblog.read_text(encoding="utf-8", errors="replace")
            result["stdout_tail"] = data[-400:].replace("\r", " ").strip()
    except OSError:
        pass

    if result["ok"]:
        logger.info("JOB %s OK in %.1fs (exit=0)", job["id"], result["duration_sec"])
    else:
        logger.error("JOB %s FAILED exit=%s in %.1fs :: %s",
                     job["id"], exit_code, result["duration_sec"], result["error"])

    # --- checkpoint 更新 ---
    jstat = checkpoint.setdefault("jobs", OrderedDict()).setdefault(
        job["id"], OrderedDict([("runs", 0), ("ok", 0), ("failed", 0)]))
    jstat["runs"] = int(jstat.get("runs", 0)) + 1
    jstat["ok"] = int(jstat.get("ok", 0)) + (1 if result["ok"] else 0)
    jstat["failed"] = int(jstat.get("failed", 0)) + (0 if result["ok"] else 1)
    jstat["last_started_at"] = result["started_at"]
    jstat["last_finished_at"] = C.now_iso()
    jstat["last_exit_code"] = exit_code
    jstat["last_error"] = result.get("error")
    checkpoint["jobs_run_total"] = int(checkpoint.get("jobs_run_total", 0)) + 1
    checkpoint["jobs_ok_total"] = int(checkpoint.get("jobs_ok_total", 0)) + (1 if result["ok"] else 0)
    checkpoint["jobs_failed_total"] = int(checkpoint.get("jobs_failed_total", 0)) + (0 if result["ok"] else 1)
    checkpoint["last_job_id"] = job["id"]
    checkpoint["last_run_at"] = C.now_iso()

    if audit:
        audit.append({
            "event": "job",
            "job_id": job["id"],
            "exit_code": exit_code,
            "ok": result["ok"],
            "duration_sec": result["duration_sec"],
            "dry_run": result["dry_run"],
            "error": result.get("error"),
        })
    return result


# =============================================================================
# Schedule resolution
# =============================================================================

def resolve_schedule(jobs, now, catchup_minutes, logger=None):
    """决定 now 时刻应执行哪些作业。

    返回 (due_now, missed_window, all_jobs_state)
      due_now        : cron 精确命中 (±1 分钟容差) 的作业 id 列表
      missed_window  : 落在 (now - catchup, now) 且未记录的漏跑作业
      all_jobs_state : {job_id: {spec, last_fire, next_fire, due, missed}}
    """
    checkpoint = load_checkpoint() or default_checkpoint()
    due_now, missed = [], []
    state = OrderedDict()
    one_min = timedelta(minutes=1)

    for job in jobs:
        try:
            spec = CronSpec(job["cron"])
        except CronError as e:
            if logger:
                logger.error("BAD CRON %s %r: %s" % (job["id"], job["cron"], e))
            state[job["id"]] = {"error": str(e)}
            continue
        last_fire = None
        jstat = checkpoint.get("jobs", {}).get(job["id"], {})
        jlast = jstat.get("last_cron_fire")
        if jlast:
            last_fire = parse_iso(jlast)

        # cron 精确命中: now 的分钟与 spec 匹配
        due = spec.matches(now.replace(second=0, microsecond=0))
        if due and last_fire != now.replace(second=0, microsecond=0):
            due_now.append(job["id"])

        # 漏跑检测: 上一个候选时刻落在 catch-up 窗口内且未执行
        missed_fire = None
        nxt = spec.next_run(now)
        prev = None
        probe = now - one_min
        while probe >= now - timedelta(minutes=catchup_minutes) and prev is None:
            if spec.matches(probe.replace(second=0, microsecond=0)):
                prev = probe.replace(second=0, microsecond=0)
            probe -= one_min
        if prev and prev <= now and last_fire != prev:
            missed_fire = prev

        if missed_fire:
            missed.append({"job_id": job["id"], "missed_at": missed_fire.strftime(C.ISO_FMT)})

        state[job["id"]] = OrderedDict([
            ("cron", job["cron"]),
            ("description", job.get("description", "")),
            ("last_fire_recorded", last_fire.strftime(C.ISO_FMT) if last_fire else None),
            ("due_now", bool(due)),
            ("missed_at", missed_fire.strftime(C.ISO_FMT) if missed_fire else None),
            ("next_fire", nxt.strftime(C.ISO_FMT) if nxt else None),
        ])

    return due_now, missed, state, checkpoint


def record_fire(checkpoint, job_ids, now):
    """记录一次 cron 命中 (防止重复补跑)。"""
    stamp = now.strftime(C.ISO_FMT)
    for jid in job_ids:
        jstat = checkpoint.setdefault("jobs", OrderedDict()).setdefault(
            jid, OrderedDict())
        jstat["last_cron_fire"] = stamp
    checkpoint["last_cron_fire_at"] = stamp
    save_checkpoint(checkpoint)


# =============================================================================
# Reporting
# =============================================================================

def print_schedule_table(state, now, tz_offset):
    lines = []
    lines.append("=" * 100)
    lines.append("External Crawler Schedule — %s" % now.strftime(C.ISO_FMT))
    lines.append("=" * 100)
    lines.append("TASK_ID        : %s" % TASK_ID)
    lines.append("AGENT          : %s | BRANCH %s | LIB %s" % (AGENT, BRANCH, C.LIB_VERSION))
    lines.append("TZ             : UTC+%g (Asia/Shanghai baseline)" % tz_offset)
    lines.append("")
    lines.append("%-13s %-24s %-13s %-24s %-20s %s" % (
        "JOB_ID", "CRON", "NEXT_FIRE", "LAST_FIRE", "DUE/MISSED", "DESCRIPTION"))
    lines.append("-" * 100)
    for jid, s in state.items():
        if s.get("error"):
            lines.append("%-13s %s" % (jid, "ERROR: %s" % s["error"]))
            continue
        flag = ""
        if s.get("due_now"):
            flag += "DUE "
        if s.get("missed_at"):
            flag += "MISSED@%s " % s["missed_at"]
        lines.append("%-13s %-24s %-13s %-24s %-20s %s" % (
            jid, s["cron"], str(s.get("next_fire") or "-"),
            str(s.get("last_fire_recorded") or "-"), flag.strip() or "-",
            s.get("description", "")))
    lines.append("-" * 100)
    txt = "\n".join(lines)
    print(txt)
    return txt


def print_run_report(results, summary):
    lines = []
    lines.append("")
    lines.append("=" * 100)
    lines.append("Scheduler Run Report")
    lines.append("=" * 100)
    lines.append("Triggered at : %s" % summary.get("triggered_at"))
    lines.append("Dry run      : %s" % summary.get("dry_run"))
    lines.append("Jobs         : %d total / %d ok / %d failed | %.1fs" % (
        summary.get("jobs_total", 0), summary.get("jobs_ok", 0),
        summary.get("jobs_failed", 0), summary.get("duration_sec", 0.0)))
    lines.append("")
    lines.append("%-13s %-6s %-9s %-9s %-46s %s" % (
        "JOB_ID", "EXIT", "DURATION", "OK", "CMD", "ERROR/NOTE"))
    lines.append("-" * 100)
    for r in results:
        lines.append("%-13s %-6s %-9s %-9s %-46s %s" % (
            r["job_id"], r.get("exit_code"), "%.1fs" % r.get("duration_sec", 0.0),
            "YES" if r.get("ok") else "NO",
            (r.get("cmd") or "")[-46:], str(r.get("error") or "-")))
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
        description="V88 Phase03 P1 DSHB — external crawler cron-like scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--dry-run", dest="dry_run", action="store_true", default=True,
                   help="pass --dry-run to child crawlers (default)")
    g.add_argument("--live", "--no-dry-run", dest="dry_run", action="store_false",
                   help="pass --live to child crawlers")

    m = parser.add_mutually_exclusive_group()
    m.add_argument("--once", action="store_true",
                   help="run every job once, immediately, and exit")
    m.add_argument("--cron", action="store_true",
                   help="daemon mode: evaluate schedule continuously")
    m.add_argument("--status", action="store_true",
                   help="print schedule table and exit")
    m.add_argument("--list", action="store_true",
                   help="same as --status")
    parser.add_argument("--job", default=None, metavar="JOB_ID",
                        help="only consider this job id (repeatable with --jobs)")
    parser.add_argument("--jobs", nargs="+", default=None, metavar="JOB_ID",
                        help="job ids to consider (overrides --job)")
    parser.add_argument("--now", default=None, metavar="ISO_DATETIME",
                        help="inject 'current time' (offline schedule testing)")
    parser.add_argument("--no-exec", action="store_true",
                        help="resolve schedule and build commands, but launch nothing")
    parser.add_argument("--catchup-minutes", type=int,
                        default=DEFAULT_CATCHUP_MINUTES,
                        help="missed-window catch-up in minutes (default %(default)s)")
    parser.add_argument("--max-cycles", type=int, default=0,
                        help="daemon mode: stop after N cycles (0 = run forever)")
    parser.add_argument("--max-sleep", type=float, default=DEFAULT_MAX_SLEEP,
                        help="daemon mode: max single sleep seconds (default %(default)s)")
    parser.add_argument("--sleep", type=float, default=20.0,
                        help="daemon mode: polling interval seconds (default %(default)s)")
    parser.add_argument("--job-timeout", type=int, default=DEFAULT_JOB_TIMEOUT,
                        help="per-job timeout seconds (default %(default)s)")
    parser.add_argument("--tz-offset-hours", type=float,
                        default=DEFAULT_TZ_OFFSET_HOURS,
                        help="informational TZ offset of cron expressions "
                             "(default %(default)s)")
    parser.add_argument("--date", default=None, metavar="YYYY-MM-DD",
                        help="forward --date to child crawlers")
    parser.add_argument("--emit-samples", action="store_true",
                        help="forward --emit-samples to child crawlers")
    parser.add_argument("--output-root", default=None, metavar="DIR",
                        help="forward --output-root to child crawlers")
    parser.add_argument("--job-args", nargs="*", default=None,
                        help="extra args forwarded to every child crawler")
    parser.add_argument("--json-out", default=None, metavar="FILE",
                        help="write scheduler run result JSON")
    parser.add_argument("--report-md", default=None, metavar="FILE",
                        help="write scheduler run report markdown")
    parser.add_argument("--no-audit", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logger = C.get_logger(SCRIPT_NAME, level=logging.DEBUG if args.verbose
                          else logging.INFO)
    audit = None
    if not args.no_audit:
        audit = C.JsonlAudit(AUDIT_LOG, logger=logger)

    checkpoint = load_checkpoint()
    fresh = False
    if checkpoint is None:
        checkpoint = default_checkpoint()
        fresh = True

    logger.info("START %s | dry_run=%s | mode=%s", TASK_ID, args.dry_run,
                "once" if args.once else ("cron" if args.cron else "status"))
    logger.info("CONSTRAINTS %s" % dict(C.CONSTRAINTS))
    logger.info("STDLIB_ONLY | zhiji_api.py NEVER called")

    # ---- 作业过滤 ----
    wanted = None
    if args.jobs:
        wanted = set(args.jobs)
    elif args.job:
        wanted = {args.job}
    jobs = JOBS
    if wanted is not None:
        known = {j["id"] for j in JOBS}
        bad = wanted - known
        if bad:
            logger.error("unknown job id(s): %s (known: %s)",
                         ",".join(sorted(bad)), ",".join(sorted(known)))
            parser.print_help()
            return 1
        jobs = [j for j in JOBS if j["id"] in wanted]

    # ---- 当前时间 ----
    now = parse_iso(args.now) if args.now else datetime.now()
    if now is None:
        logger.error("bad --now value: %r", args.now)
        return 1

    # 转发给子爬虫的公共参数
    fwd = []
    if args.date:
        fwd += ["--date", args.date]
    if args.emit_samples:
        fwd.append("--emit-samples")
    if args.output_root:
        fwd += ["--output-root", args.output_root]
    args.job_args = (args.job_args or []) + fwd

    # ---- 状态 / 列表模式 ----
    if args.status or args.list:
        due_now, missed, state, checkpoint = resolve_schedule(
            jobs, now, args.catchup_minutes, logger=logger)
        print_schedule_table(state, now, args.tz_offset_hours)
        if missed:
            print("\nMISSED WINDOW (last %d min): %s" % (
                args.catchup_minutes,
                ", ".join("%s@%s" % (m["job_id"], m["missed_at"]) for m in missed)))
        if due_now:
            print("DUE NOW: %s" % ", ".join(due_now))
        return 0

    # ---- 执行模式 ----
    results = []
    summary = OrderedDict([
        ("task_id", TASK_ID), ("agent", AGENT), ("branch", BRANCH),
        ("script", SCRIPT_NAME), ("library_version", C.LIB_VERSION),
        ("constraints", dict(C.CONSTRAINTS)),
        ("triggered_at", now.strftime(C.ISO_FMT)),
        ("dry_run", bool(args.dry_run)),
        ("no_exec", bool(args.no_exec)),
        ("mode", "once" if args.once else "cron"),
        ("jobs_selected", [j["id"] for j in jobs]),
        ("forwarded_args", list(args.job_args)),
    ])

    if args.once:
        started = time.time()
        for job in jobs:
            results.append(run_job(job, args, logger, audit, checkpoint))
        summary.update({
            "jobs_total": len(results),
            "jobs_ok": sum(1 for r in results if r["ok"]),
            "jobs_failed": sum(1 for r in results if not r["ok"]),
            "duration_sec": round(time.time() - started, 2),
        })
        if fresh or audit:
            save_checkpoint(checkpoint)
        _emit(summary, results, args, logger, audit)
        return 4 if summary["jobs_failed"] > 0 else 0

    # ---- 守护模式 ----
    if not args.cron:
        parser.print_help()
        return 1

    logger.info("DAEMON start | cycle_sleep=%.1fs | max_sleep=%.1fs | max_cycles=%d",
                args.sleep, args.max_sleep, args.max_cycles)
    cycles = 0
    started = time.time()
    try:
        while True:
            cycles += 1
            now = datetime.now()
            due_now, missed, state, checkpoint = resolve_schedule(
                jobs, now, args.catchup_minutes, logger=logger)
            to_run = []
            for m in missed:
                if m["job_id"] not in due_now:
                    due_now.append(m["job_id"])
                    to_run.append(m["job_id"])
            if due_now:
                logger.info("CYCLE %d DUE %s (missed catch-up: %d)",
                            cycles, ",".join(due_now), len(to_run))
                record_fire(checkpoint, due_now, now)
                run_ids = [j["id"] for j in jobs if j["id"] in set(due_now)]
                for job in jobs:
                    if job["id"] in set(due_now):
                        results.append(run_job(job, args, logger, audit, checkpoint))
                summary["cycles"] = cycles
                summary["last_cycle_at"] = now.strftime(C.ISO_FMT)
                summary["last_cycle_due"] = run_ids
                summary["last_cycle_ok"] = sum(
                    1 for r in results[-len(run_ids):] if r["ok"])
                summary["last_cycle_failed"] = sum(
                    0 for r in results[-len(run_ids):] if r["ok"]) + \
                    sum(1 for r in results[-len(run_ids):] if not r["ok"])
                save_checkpoint(checkpoint)
                _emit(summary, results, args, logger, audit)
            else:
                summary["cycles"] = cycles
                summary["last_cycle_at"] = now.strftime(C.ISO_FMT)
                if logger:
                    logger.info("CYCLE %d idle (next fires: %s)", cycles,
                                ", ".join("%s=%s" % (k, v.get("next_fire"))
                                          for k, v in state.items()))
            if args.max_cycles and cycles >= args.max_cycles:
                logger.info("DAEMON reached --max-cycles=%d, exiting", args.max_cycles)
                break
            # 计算到最近一次 next_fire 的距离, 但不超过 --sleep / --max-sleep
            wait = args.sleep
            for jid, s in state.items():
                nf = parse_iso(s.get("next_fire"))
                if nf:
                    delta = (nf - now).total_seconds()
                    if 0 <= delta < wait:
                        wait = delta + 1
            wait = max(0.5, min(wait, args.max_sleep))
            time.sleep(wait)
    except KeyboardInterrupt:
        logger.info("DAEMON stopped by user (Ctrl+C) after %d cycles", cycles)
    finally:
        summary.update({
            "cycles_total": cycles,
            "jobs_total": len(results),
            "jobs_ok": sum(1 for r in results if r["ok"]),
            "jobs_failed": sum(1 for r in results if not r["ok"]),
            "duration_sec": round(time.time() - started, 2),
        })
        save_checkpoint(checkpoint)
        _emit(summary, results, args, logger, audit)

    return 4 if summary.get("jobs_failed", 0) > 0 else 0


def _emit(summary, results, args, logger, audit):
    """写 JSON / Markdown 报告 + 审计。"""
    full = OrderedDict([("summary", summary), ("results", results)])
    text = json.dumps(full, indent=2, ensure_ascii=False, default=str)
    if args.json_out:
        p = Path(args.json_out)
        C.ensure_dir(p.parent)
        with open(str(p), "w", encoding="utf-8") as f:
            f.write(text)
        logger.info("RESULT_JSON -> %s" % p)
    if args.report_md:
        p = Path(args.report_md)
        C.ensure_dir(p.parent)
        md = []
        md.append("# V88 Phase03 P1 — 外部爬虫调度运行报告")
        md.append("")
        md.append("> **TASK_ID**: %s" % summary["task_id"])
        md.append("> **AGENT**: %s | **BRANCH**: %s | **LIB**: %s" % (
            summary["agent"], summary["branch"], summary["library_version"]))
        md.append("> **触发时间**: %s | **模式**: %s | **dry_run**: %s" % (
            summary["triggered_at"], summary["mode"], summary["dry_run"]))
        md.append("> **作业**: %d 总 / %d OK / %d 失败 | 耗时 %.1fs" % (
            summary.get("jobs_total", 0), summary.get("jobs_ok", 0),
            summary.get("jobs_failed", 0), summary.get("duration_sec", 0.0)))
        md.append("")
        md.append("## 1. 作业执行明细")
        md.append("")
        md.append("| 作业 | cron | 退出码 | 耗时 | 结果 | 错误/备注 |")
        md.append("|------|------|:----:|----:|:----:|-----------|")
        for r in results:
            md.append("| `%s` | `%s` | %s | %.1fs | %s | %s |" % (
                r["job_id"], r["cron"], r.get("exit_code"),
                r.get("duration_sec", 0.0), "PASS" if r.get("ok") else "FAIL",
                str(r.get("error") or "-").replace("|", "/")))
        md.append("")
        md.append("## 2. 命令与日志")
        md.append("")
        for r in results:
            md.append("- `%s` -> `%s`" % (r["job_id"], r.get("cmd") or "-"))
            if r.get("log_file"):
                md.append("  - stdout/stderr: `%s`" % r["log_file"])
        md.append("")
        md.append("## 3. 约束声明")
        md.append("")
        for k, v in summary.get("constraints", {}).items():
            md.append("- **%s** = %s" % (k, v))
        md.append("")
        md.append("---")
        md.append("")
        md.append("*Generated by schedule_crawler.py | %s*" % C.now_iso())
        with open(str(p), "w", encoding="utf-8") as f:
            f.write("\n".join(md) + "\n")
        logger.info("REPORT_MD -> %s" % p)
    if audit:
        audit.append({"event": "run_summary", **{
            k: v for k, v in summary.items() if k != "constraints"}})


if __name__ == "__main__":
    C.setup_environment()
    sys.exit(main())
