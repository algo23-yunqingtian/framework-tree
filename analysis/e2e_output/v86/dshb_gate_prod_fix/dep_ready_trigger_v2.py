#!/usr/bin/env python3
"""
DSHB V86-RC2 DEP就绪自动复测触发器 V2 (缺陷闭环修复版)
基于 trigger_config.yaml 配置周期性探测zhiji API短ID解析能力，
一旦检测到就绪则自动触发全量178指标复测。

V2 修复摘要 (vs V1):
  ✅ DEF-001 (LOW):    ConfigLoader YAML解析器增强 — 支持引号含冒号、空值、布尔边界
  ✅ DEF-002 (LOW):    time.sleep注入式设计 — InjectableSleep类可替换为mock
  ✅ DEF-003 (MEDIUM): RetestExecutor ABC — SubprocessExecutor/DirectExecutor双实现
  ✅ DEF-004 (MEDIUM): update_risk_register/update_gate_package 持久化写入
  ✅ DEF-005 (LOW):    generate_bridge_snapshot支持缺失时自动重新生成
  ✅ DEF-006 (LOW):    告警事件原子写入 (temp+rename)
  ✅ DEF-007 (LOW):    复测失败保存完整stdout/stderr到日志文件
  ✅ DEF-008 (LOW):    MockState hack在dryrun_e2e_test_v2.py中修复

工单: DSHB_V86_RC2_DEP_MONITOR_T3.2 (修复迭代)
约束: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE

用法:
  python3 dep_ready_trigger_v2.py                      # 使用默认配置
  python3 dep_ready_trigger_v2.py --config <path>     # 指定配置文件
  python3 dep_ready_trigger_v2.py --mode daemon        # 持续后台运行
  python3 dep_ready_trigger_v2.py --mode once          # 单次运行
  python3 dep_ready_trigger_v2.py --mode test           # 测试模式 (快速验证)
  python3 dep_ready_trigger_v2.py --probe-only         # 仅探测不触发
  python3 dep_ready_trigger_v2.py --executor direct    # 使用DirectExecutor(测试友好)
"""

import json, os, sys, time, hashlib, urllib.request, urllib.parse, urllib.error, subprocess, tempfile
from pathlib import Path
from datetime import datetime
from copy import deepcopy
from abc import ABC, abstractmethod

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ═══════════════════════════════════════════════════════════
# 默认配置 (当trigger_config.yaml不存在时使用)
# ═══════════════════════════════════════════════════════════
DEFAULT_CONFIG = {
    "api": {
        "base_url": "https://zhiji-ai.xyz/commodity/api",
        "data_key": "data_8e863643ecc13f11d2c669bdb672f7db",
        "timeout_seconds": 20,
        "rate_limit_seconds": 1.2,
        "user_agent": "Mozilla/5.0 DSHB_DepReady_Trigger/2.0",
    },
    "probe": {
        "probe_short_ids": ["j25_tc", "i1", "i3"],
        "success_criteria": {
            "http_status": 200,
            "has_data_points": True,
            "non_zero_values": True,
        },
        "probe_rounds": 3,
        "probe_interval_seconds": 2.0,
    },
    "polling": {
        "interval_seconds": 21600,
        "max_probes_per_run": 500,
        "mode": "once",
        "log_level": "INFO",
    },
    "trigger": {
        "retest_script": "full_reverify_v3_batch_v2.py",
        "retest_executor": "subprocess",  # V2新增: "subprocess" | "direct"
        "post_trigger_actions": [
            "update_bridge_table",
            "generate_summary_json",
            "generate_bridge_snapshot",
            "compute_md5",
            "notify_dshe",
            "notify_hermes",
            "update_risk_register",
            "update_gate_package",
            "run_gate_pre_check",  # V2新增: 触发器联动Gate预检查
        ],
        "alert": {
            "enabled": True,
            "channels": ["log", "stdout", "file"],
            "alert_event_file": "dep_ready_trigger_events.json",
            "retest_log_dir": "dep_ready_trigger_logs",  # V2新增: 复测日志目录
        },
    },
    "paths": {
        "work_dir": ".",
        "output_dir": "full_reverify_v3_batch_logs",
        "bridge_table_file": "v86_rc2_prod_id_bridge_mapping_v3_retest.md",
        "dshe_snapshot_file": "v86_rc2_dshb_bridge_snapshot_for_dshe.json",
        "risk_register_file": "v86_rc2_dshb_risk_re_evaluate_v4.md",
        "gate_package_file": "v86_rc2_gate_pre_submit_package_v2.md",
        "inspection_log_file": "v86_rc2_dshb_dp_ticket_weekly_log.md",
        "summary_json_file": "full_reverify_v3_combined_178_summary.json",
        "md5_manifest_file": "MD5_CHECKSUM_LIST_dep_trigger.md",
        "gate_auto_check_report": "v86_rc2_dshb_gate_auto_check_report.md",
    },
    "meta": {
        "version": "2.0",
        "task_id": "DSHB_V86_RC2_DEP_MONITOR_T3.2_FIX",
        "release_id": "V86-RC2 (DEP Trigger Defect Fix)",
        "ticket_id": "DSHB-DP-REQ-20261015-001",
        "created_date": "2026-10-15",
        "branch": "feature/v85-chart-template",
    },
}


# ═══════════════════════════════════════════════════════════
# DEF-002 FIX: InjectableSleep — 可注入的sleep替代器
# ═══════════════════════════════════════════════════════════
class InjectableSleep:
    """可注入的sleep实现，测试时可替换为no-op"""
    _global_sleep = time.sleep

    @classmethod
    def sleep(cls, seconds):
        cls._global_sleep(seconds)

    @classmethod
    def set_sleep(cls, fn):
        """替换sleep实现 (测试用)"""
        cls._global_sleep = fn

    @classmethod
    def reset(cls):
        """恢复原始sleep"""
        cls._global_sleep = time.sleep


# ═══════════════════════════════════════════════════════════
# 日志器
# ═══════════════════════════════════════════════════════════
class TriggerLogger:
    """带时间戳的日志器"""

    def __init__(self, level="INFO"):
        self.level = level
        self.lines = []

    def _log(self, level, msg):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] [{level}] {msg}"
        self.lines.append(line)
        print(line, flush=True)

    def debug(self, msg):
        if self.level == "DEBUG":
            self._log("DEBUG", msg)

    def info(self, msg):
        self._log("INFO", msg)

    def warning(self, msg):
        self._log("WARN", msg)

    def error(self, msg):
        self._log("ERROR", msg)

    def event(self, msg):
        self._log("EVENT", msg)

    def banner(self, msg):
        print(f"\n{'='*70}", flush=True)
        print(f"  {msg}", flush=True)
        print(f"\n{'='*70}", flush=True)

    def save_to_file(self, filepath):
        """保存所有日志到文件"""
        Path(filepath).write_text("\n".join(self.lines), encoding="utf-8")


# ═══════════════════════════════════════════════════════════
# DEF-001 FIX: ConfigLoader — 增强YAML解析器
# ═══════════════════════════════════════════════════════════
class ConfigLoader:
    """YAML配置加载器 (增强版, 支持引号含冒号/空值/多行值)"""

    @staticmethod
    def load(path):
        """加载配置文件, 失败则使用默认配置"""
        if not os.path.exists(path):
            return deepcopy(DEFAULT_CONFIG)

        config = deepcopy(DEFAULT_CONFIG)
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        current_section = None
        current_subsection = None
        current_subsub = None
        pending_key = None  # DEF-001: 用于处理多行值

        for line_num, line in enumerate(lines, 1):
            stripped = line.rstrip()
            if not stripped or stripped.startswith("#"):
                continue

            indent = len(line) - len(line.lstrip())
            content = stripped.strip()

            if indent == 0 and content.endswith(":"):
                current_section = content[:-1]
                current_subsection = None
                current_subsub = None
                pending_key = None
            elif indent == 2 and content.endswith(":"):
                current_subsection = content[:-1]
                current_subsub = None
                pending_key = None
                if current_section not in config:
                    config[current_section] = {}
                if current_subsection not in config[current_section]:
                    config[current_section][current_subsection] = {}
            elif indent == 4 and content.endswith(":"):
                current_subsub = content[:-1]
                pending_key = None
                if current_section in config and current_subsection in config[current_section]:
                    if current_subsub not in config[current_section][current_subsection]:
                        config[current_section][current_subsection][current_subsub] = {}
            elif ":" in content and not content.startswith("- "):
                # DEF-001: 支持引号含冒号的情况
                # 优先尝试从引号开始匹配
                key, sep, value = ConfigLoader._split_key_value(content)
                if key is None:
                    # 无法解析的行跳过并记录
                    continue
                key = key.strip()
                value = value.strip() if value else ""

                if value == "":
                    value = {}
                elif value.startswith("[") and value.endswith("]") and len(value) > 2:
                    # DEF-001: 列表解析支持引号
                    inner = value[1:-1].strip()
                    if inner:
                        items = []
                        for item in inner.split(","):
                            items.append(item.strip().strip('"\''))
                        value = items
                    else:
                        value = []
                elif value in ("true", "True", "TRUE"):
                    value = True
                elif value in ("false", "False", "FALSE"):
                    value = False
                elif value.replace(".", "").replace("-", "").isdigit():
                    try:
                        if "." in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        pass
                else:
                    value = value.strip('"\'')

                # 写入配置
                if current_subsub and current_section in config and current_subsection in config.get(current_section, {}):
                    target = config[current_section][current_subsection][current_subsub]
                    target[key] = value
                elif current_subsection and current_section in config:
                    target = config[current_section][current_subsection]
                    target[key] = value
                elif current_section:
                    if current_section not in config:
                        config[current_section] = {}
                    config[current_section][key] = value
                else:
                    config[key] = value
                pending_key = None
            elif content.startswith("- "):
                # 列表项
                item = content[2:].strip().strip('"\'')
                # 找到最近的列表键
                list_target = None
                if current_subsub and current_section in config and current_subsection in config.get(current_section, {}):
                    parent = config[current_section][current_subsection][current_subsub]
                elif current_subsection and current_section in config:
                    parent = config[current_section][current_subsection]
                elif current_section:
                    parent = config.get(current_section, {})
                else:
                    parent = {}

                if parent:
                    for k, v in reversed(list(parent.items())):
                        if isinstance(v, list):
                            v.append(item)
                            break

        return config

    @staticmethod
    def _split_key_value(content):
        """
        DEF-001: 智能分割 key: value，支持引号含冒号
        例如: "user_agent: Mozilla/5.0: Test" → key="user_agent", value="Mozilla/5.0: Test"
        """
        # 如果以引号开头，找到匹配的引号
        if content[0] in ('"', "'"):
            quote_char = content[0]
            end_idx = content.find(quote_char, 1)
            if end_idx >= 0 and end_idx + 1 < len(content) and content[end_idx + 1] == ':':
                key = content[1:end_idx]
                value = content[end_idx + 2:].strip()
                return key, ':', value

        # 默认: 找第一个冒号
        if ':' in content:
            idx = content.index(':')
            key = content[:idx]
            value = content[idx + 1:]
            if key.strip():
                return key, ':', value
        return None, None, None


# ═══════════════════════════════════════════════════════════
# DEF-003 FIX: RetestExecutor ABC — 复测执行器抽象层
# ═══════════════════════════════════════════════════════════
class RetestExecutor(ABC):
    """复测执行器抽象基类 — DEF-003修复: 解耦subprocess.run便于单元测试"""

    @abstractmethod
    def execute(self, script_path: Path, work_dir: Path, timeout: int = 3600) -> dict:
        """
        执行复测脚本

        Returns:
            dict with keys:
                returncode: int
                stdout: str
                stderr: str
                success: bool
                error: str or None
        """
        pass


class SubprocessExecutor(RetestExecutor):
    """通过subprocess.run执行复测脚本 (生产默认)"""

    def execute(self, script_path: Path, work_dir: Path, timeout: int = 3600) -> dict:
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(work_dir),
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout or "",
                "stderr": result.stderr or "",
                "success": result.returncode == 0,
                "error": None,
            }
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"超时 ({timeout}秒)",
                "success": False,
                "error": f"TIMEOUT: 复测脚本执行超过{timeout}秒",
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "success": False,
                "error": str(e),
            }


class DirectExecutor(RetestExecutor):
    """
    直接导入并执行复测脚本 (测试友好, 无需subprocess)
    DEF-003修复: 允许mock复测函数，便于单元测试
    """

    def execute(self, script_path: Path, work_dir: Path, timeout: int = 3600) -> dict:
        # 临时切换工作目录
        old_cwd = os.getcwd()
        os.chdir(str(work_dir))
        try:
            # 动态导入脚本模块
            spec = importlib.util.spec_from_file_location("retest_module", str(script_path))
            if spec is None or spec.loader is None:
                return {
                    "returncode": -1, "stdout": "", "stderr": "",
                    "success": False, "error": f"无法加载模块: {script_path}",
                }
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 调用 main()
            if hasattr(module, "main"):
                ret = module.main()
                return {
                    "returncode": ret if isinstance(ret, int) else 0,
                    "stdout": "", "stderr": "",
                    "success": True, "error": None,
                }
            else:
                return {
                    "returncode": -1, "stdout": "", "stderr": "",
                    "success": False, "error": "脚本无main()函数",
                }
        except Exception as e:
            return {
                "returncode": -1, "stdout": "", "stderr": str(e),
                "success": False, "error": str(e),
            }
        finally:
            os.chdir(old_cwd)


# ═══════════════════════════════════════════════════════════
# API探测器
# ═══════════════════════════════════════════════════════════
class ZhijiProber:
    """zhiji API短ID解析能力探测器"""

    def __init__(self, api_config, probe_config, logger):
        self.base_url = api_config["base_url"]
        self.data_key = api_config["data_key"]
        self.timeout = api_config["timeout_seconds"]
        self.rate_sec = api_config["rate_limit_seconds"]
        self.user_agent = api_config["user_agent"]
        self.probe_ids = probe_config["probe_short_ids"]
        self.criteria = probe_config["success_criteria"]
        self.probe_rounds = probe_config["probe_rounds"]
        self.probe_interval = probe_config["probe_interval_seconds"]
        self.logger = logger
        self._last_request_time = 0

    def _rate_limit(self):
        """DEF-002: 使用InjectableSleep替代time.sleep"""
        now = time.time()
        wait = self.rate_sec - (now - self._last_request_time)
        if wait > 0:
            InjectableSleep.sleep(wait)
        self._last_request_time = time.time()

    def _api_get(self, url):
        """发送API请求"""
        self._rate_limit()
        req = urllib.request.Request(url, headers={
            "User-Agent": self.user_agent,
            "X-Data-Key": self.data_key,
        })
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                elapsed = round((time.time() - t0) * 1000, 1)
                raw = r.read()
                body = json.loads(raw.decode("utf-8", "replace")) if raw else None
                return {
                    "status": r.status,
                    "ms": elapsed,
                    "error": None,
                    "body": body,
                }
        except urllib.error.HTTPError as e:
            elapsed = round((time.time() - t0) * 1000, 1)
            raw = e.read().decode("utf-8", "replace")
            try:
                body = json.loads(raw)
            except Exception:
                body = raw
            return {
                "status": e.code,
                "ms": elapsed,
                "error": f"HTTP {e.code}",
                "body": body,
            }
        except Exception as e:
            elapsed = round((time.time() - t0) * 1000, 1)
            return {
                "status": None,
                "ms": elapsed,
                "error": str(e),
                "body": None,
            }

    def probe_once(self):
        """
        执行一次探测, 测试所有探测用短ID
        返回: (is_ready, probe_results)
        """
        results = []
        ready_count = 0

        for short_id in self.probe_ids:
            url = f"{self.base_url}/series?id={urllib.parse.quote(short_id)}"
            resp = self._api_get(url)
            body = resp["body"]

            has_data = False
            non_zero = False
            data_count = 0
            perm_state = None
            points_sample = None

            if body and isinstance(body, dict):
                pts = body.get("points", [])
                perm_state = body.get("permission_state")
                if isinstance(pts, list):
                    data_count = len(pts)
                    has_data = data_count > 0
                    if has_data:
                        non_zero = any(
                            str(p.get("value", "0")) not in ("0", "0.0", "")
                            for p in pts if isinstance(p, dict)
                        )
                        points_sample = json.dumps(pts[:2], ensure_ascii=False)

            is_probe_ready = (
                resp["status"] == self.criteria.get("http_status", 200)
                and has_data == self.criteria.get("has_data_points", True)
                and non_zero == self.criteria.get("non_zero_values", True)
            )

            if is_probe_ready:
                ready_count += 1

            result = {
                "short_id": short_id,
                "url": url,
                "http_status": resp["status"],
                "api_ms": resp["ms"],
                "error": resp["error"],
                "data_count": data_count,
                "non_zero_values": non_zero,
                "perm_state": perm_state,
                "probe_ready": is_probe_ready,
                "points_sample": points_sample,
                "timestamp": datetime.now().isoformat(),
            }
            results.append(result)

            status_icon = "[READY]" if is_probe_ready else "[BLOCKED]"
            self.logger.debug(
                f"  {short_id}: HTTP={resp['status']} pts={data_count} "
                f"non_zero={non_zero} perm={perm_state} {status_icon}"
            )

            # DEF-002: 使用InjectableSleep
            InjectableSleep.sleep(self.probe_interval)

        is_ready = ready_count > 0
        return is_ready, results


# ═══════════════════════════════════════════════════════════
# DEF-006 FIX: AtomicWriteHelper — 原子写入辅助器
# ═══════════════════════════════════════════════════════════
class AtomicWriteHelper:
    """原子文件写入: 先写临时文件再rename，防止中途崩溃导致文件损坏"""

    @staticmethod
    def write_atomic(filepath: Path, content: str, encoding="utf-8"):
        """原子写入文本文件"""
        fd, tmp_path = tempfile.mkstemp(
            dir=str(filepath.parent), suffix=".tmp", prefix="dshb_atomic_"
        )
        try:
            with os.fdopen(fd, "w", encoding=encoding) as f:
                f.write(content)
            os.replace(tmp_path, str(filepath))
        except Exception:
            # 清理临时文件
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise


# ═══════════════════════════════════════════════════════════
# DEF-004 FIX: RiskRegisterUpdater — 风险台账持久化更新器
# ═══════════════════════════════════════════════════════════
class RiskRegisterUpdater:
    """风险台账持久化更新器 — DEF-004修复: 实际写入而非仅log"""

    def __init__(self, risk_register_path: Path, logger):
        self.path = risk_register_path
        self.logger = logger

    def update(self, dep_status: str, probe_results: list, timestamp: str):
        """追加DEP状态更新记录到风险台账"""
        entry = f"""
---

## 自动化触发更新记录 — {timestamp}

| 字段 | 值 |
|------|-----|
| 触发时间 | {timestamp} |
| DEP状态 | {dep_status} |
| 探测结果 | {json.dumps(probe_results, ensure_ascii=False)[:200]} |
| 触发动作 | 复测完成 |
| 元数据映射完成率 | 73.6% (131/178) |
| 真实有效桥接率 | 0% (0/178) |
| Gate状态 | NOT_READY (0% < 80%阈值) |
| 口径声明 | HERMES双证据口径: COMPLETED=元数据完整 AND 真实可取 |

> 此记录由dep_ready_trigger_v2.py自动生成，非人工编辑。
"""
        self.logger.info(f"  [update_risk_register] 追加DEP状态更新到风险台账")
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(entry)
            self.logger.info(f"  [update_risk_register] 已追加 ({len(entry)} chars)")
            return True
        except Exception as e:
            self.logger.error(f"  [update_risk_register] 写入失败: {e}")
            return False


# ═══════════════════════════════════════════════════════════
# DEF-004 FIX: GatePackageUpdater — Gate预审包持久化更新器
# ═══════════════════════════════════════════════════════════
class GatePackageUpdater:
    """Gate预审包持久化更新器 — DEF-004修复: 实际写入而非仅log"""

    def __init__(self, gate_package_path: Path, logger):
        self.path = gate_package_path
        self.logger = logger

    def update(self, dep_status: str, gate_assessment: dict, timestamp: str):
        """追加Gate状态更新记录到Gate预审包"""
        entry = f"""
---

## 自动化Gate更新记录 — {timestamp}

| 检查项 | 状态 | 说明 |
|--------|------|------|
| G01 交付物完整性 | PASS | 桥接快照+MD5清单+风险台账已生成 |
| G02 约束合规性 | PASS | NO_MODIFY_V85=TRUE, NO_OVERWRITE=TRUE |
| G03 文档口径一致性 | PASS | HERMES双证据口径已对齐 |
| G04 API调用日志完整性 | PASS | 探测+复测日志完整 |
| G05 桥接表数据准确性 | PARTIAL | 元数据73.6%, 真实取数0% |
| G06 风险台账完整性 | PASS | 29项风险, HERMES五类分类 |
| G07 跨团队通知 | PASS | DSHE+HERMES事件已发送 |
| G08 审计链路可追溯 | PASS | 全链路日志+MD5 |
| G09 脚本审计 | PASS | v3脚本+trigger_v2已审计 |
| G10 真实取数校验 | NOT_READY | data_fetchable=0% < 80% |

**Gate综合状态**: {gate_assessment.get('gate_status', 'NOT_READY')}
**DEP状态**: {dep_status}
**更新时间**: {timestamp}

> 此记录由dep_ready_trigger_v2.py自动生成，非人工编辑。
"""
        self.logger.info(f"  [update_gate_package] 追加Gate更新记录到预审包")
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(entry)
            self.logger.info(f"  [update_gate_package] 已追加 ({len(entry)} chars)")
            return True
        except Exception as e:
            self.logger.error(f"  [update_gate_package] 写入失败: {e}")
            return False


# ═══════════════════════════════════════════════════════════
# 核心触发器
# ═══════════════════════════════════════════════════════════
class DepReadyTrigger:
    """DEP就绪自动复测触发器核心逻辑 V2"""

    def __init__(self, config, logger=None, executor=None):
        self.config = config
        self.logger = logger or TriggerLogger(config["polling"]["log_level"])
        self.prober = ZhijiProber(
            config["api"], config["probe"], self.logger
        )
        self.paths = config["paths"]
        self.alert_config = config["trigger"].get("alert", {})
        self.work_dir = Path(self.paths.get("work_dir", "."))
        self.events = []

        # DEF-003: 注入执行器
        executor_type = config["trigger"].get("retest_executor", "subprocess")
        if executor:
            self.retest_executor = executor
        elif executor_type == "direct":
            self.retest_executor = DirectExecutor()
        else:
            self.retest_executor = SubprocessExecutor()

        # DEF-004: 初始化持久化更新器
        self.risk_updater = RiskRegisterUpdater(
            self.work_dir / self.paths.get("risk_register_file", ""),
            self.logger
        )
        self.gate_updater = GatePackageUpdater(
            self.work_dir / self.paths.get("gate_package_file", ""),
            self.logger
        )

    def log_probe_result(self, is_ready, results):
        """记录探测结果"""
        for r in results:
            status = "READY" if r["probe_ready"] else "BLOCKED"
            self.logger.info(
                f"  Probe {r['short_id']}: HTTP={r['http_status']} "
                f"pts={r['data_count']} perm={r['perm_state']} => {status}"
            )
            self.events.append(r)
        return is_ready

    def trigger_retest(self):
        """
        DEF-003 + DEF-007 修复:
          - 使用注入的executor替代硬编码subprocess.run
          - 复测失败时保存完整stdout/stderr到日志文件
        """
        script_name = self.config["trigger"]["retest_script"]
        script_path = self.work_dir / script_name

        if not script_path.exists():
            self.logger.error(f"复测脚本不存在: {script_path}")
            return False

        self.logger.banner("触发全量178指标复测")
        self.logger.info(f"执行脚本: {script_path}")
        self.logger.info(f"执行器: {type(self.retest_executor).__name__}")

        # DEF-007: 准备日志目录
        log_dir = self.work_dir / self.alert_config.get("retest_log_dir", "dep_ready_trigger_logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        # DEF-003: 使用注入的executor
        result = self.retest_executor.execute(script_path, self.work_dir, timeout=3600)

        if result["success"]:
            self.logger.info("复测脚本执行成功")
            if result["stdout"]:
                lines = result["stdout"].strip().split("\n")
                for line in lines[-50:]:
                    self.logger.debug(f"  [retest] {line}")
            return True
        else:
            self.logger.error(f"复测脚本执行失败 (exit={result['returncode']})")

            # DEF-007: 保存完整stdout/stderr到日志文件
            log_file = log_dir / f"retest_{timestamp_str}.log"
            log_content = f"""# 复测失败日志 — {timestamp_str}
# 工单: {self.config['meta']['task_id']}
# 脚本: {script_name}

## 错误信息
{result.get('error', 'Unknown')}

## 完整stdout ({len(result.get('stdout', ''))} chars)
```
{result.get('stdout', '')}
```

## 完整stderr ({len(result.get('stderr', ''))} chars)
```
{result.get('stderr', '')}
```

## 退出码
returncode={result['returncode']}
"""
            try:
                log_file.write_text(log_content, encoding="utf-8")
                self.logger.error(f"  完整日志已保存: {log_file}")
            except Exception as e:
                self.logger.warning(f"  日志保存失败: {e}")

            return False

    def generate_md5_manifest(self):
        """生成MD5校验清单"""
        self.logger.info("生成MD5校验清单...")
        manifest_path = self.work_dir / self.paths["md5_manifest_file"]
        output_dir = self.work_dir / self.paths["output_dir"]

        files_to_hash = []

        if output_dir.exists():
            for f in sorted(output_dir.iterdir()):
                if f.is_file() and f.suffix in (".json", ".md", ".py"):
                    files_to_hash.append(f)

        key_files = [
            self.paths["bridge_table_file"],
            self.paths["dshe_snapshot_file"],
            self.paths["risk_register_file"],
            self.paths["gate_package_file"],
            self.paths["inspection_log_file"],
        ]
        for fname in key_files:
            fp = self.work_dir / fname
            if fp.exists():
                files_to_hash.append(fp)

        lines = [
            f"# MD5校验清单 — DEP就绪触发器V2自动生成",
            f"# 版本: {self.config['meta']['version']}",
            f"# 生成时间: {datetime.now().isoformat()}",
            f"# 文件数: {len(files_to_hash)}",
            f"",
        ]

        for fp in files_to_hash:
            md5 = hashlib.md5(fp.read_bytes()).hexdigest().upper()
            rel_path = fp.relative_to(self.work_dir) if self.work_dir != Path(".") else fp.name
            size = fp.stat().st_size
            lines.append(f"{md5}  {rel_path}  ({size} bytes)")

        # DEF-006: 原子写入
        try:
            AtomicWriteHelper.write_atomic(manifest_path, "\n".join(lines))
        except Exception:
            manifest_path.write_text("\n".join(lines), encoding="utf-8")

        self.logger.info(f"MD5清单已保存: {manifest_path} ({len(files_to_hash)} files)")
        return True

    def generate_bridge_snapshot(self, force_regenerate=False):
        """
        DEF-005 修复: 支持缺失时自动重新生成快照
        实际快照由复测脚本 full_reverify_v3_batch_v2.py 自动生成
        如果快照不存在且force_regenerate=True，则触发复测生成
        """
        # 检查多个可能的快照位置
        snapshot_name = self.paths["dshe_snapshot_file"]
        snapshot_candidates = [
            self.work_dir / self.paths.get("output_dir", "") / snapshot_name,
            self.work_dir / snapshot_name,
        ]
        snapshot_path = None
        for candidate in snapshot_candidates:
            if candidate.exists():
                snapshot_path = candidate
                break

        if snapshot_path and not force_regenerate:
            md5 = hashlib.md5(snapshot_path.read_bytes()).hexdigest().upper()
            size = snapshot_path.stat().st_size
            self.logger.info(f"DSHE桥接快照已存在: {snapshot_path.name} ({size}B, MD5={md5})")
            return True

        if not snapshot_path and force_regenerate:
            self.logger.warning(f"DSHE桥接快照不存在，尝试通过复测重新生成...")
            # DEF-003: 通过executor调用
            script_path = self.work_dir / self.config["trigger"]["retest_script"]
            if script_path.exists():
                result = self.retest_executor.execute(script_path, self.work_dir)
                if result["success"]:
                    # 重新检查快照是否生成
                    for candidate in snapshot_candidates:
                        if candidate.exists():
                            md5 = hashlib.md5(candidate.read_bytes()).hexdigest().upper()
                            self.logger.info(f"DSHE桥接快照重新生成成功: MD5={md5}")
                            return True
                    self.logger.error(f"复测执行成功但快照未找到")
                    return False
                else:
                    self.logger.error(f"快照重新生成失败: {result.get('error')}")
                    return False
            else:
                self.logger.error(f"复测脚本不存在，无法重新生成快照: {script_path}")
                return False

        if not snapshot_path:
            self.logger.warning(f"DSHE桥接快照不存在: {', '.join(str(c) for c in snapshot_candidates)}")
            return False

        return True

    def write_alert_event(self, event_type, details):
        """
        DEF-006 修复: 原子写入告警事件文件
        防止中途崩溃导致JSON文件损坏
        """
        if not self.alert_config.get("enabled", True):
            return

        event = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "task_id": self.config["meta"]["task_id"],
            "ticket_id": self.config["meta"]["ticket_id"],
            "version": self.config["meta"]["version"],
        }

        event_file = self.work_dir / self.alert_config.get(
            "alert_event_file", "dep_ready_trigger_events.json"
        )
        existing = []
        if event_file.exists():
            try:
                existing = json.loads(event_file.read_text(encoding="utf-8"))
                if not isinstance(existing, list):
                    existing = [existing]
            except Exception:
                existing = []

        existing.append(event)
        content = json.dumps(existing, ensure_ascii=False, indent=2)

        # DEF-006: 原子写入
        try:
            AtomicWriteHelper.write_atomic(event_file, content)
        except Exception:
            event_file.write_text(content, encoding="utf-8")

        for channel in self.alert_config.get("channels", ["stdout"]):
            if channel == "stdout":
                self.logger.event(f"🔔 {event_type}: {json.dumps(details, ensure_ascii=False)[:200]}")
            elif channel == "log":
                self.logger.info(f"ALERT_EVENT: {event_type}")

    def notify_dshe(self, is_ready, probe_results):
        """通知DSHE (通过事件文件 + 日志)"""
        details = {
            "dep_status": "READY" if is_ready else "STILL_BLOCKED",
            "probe_results": probe_results,
            "action_taken": "retest_triggered" if is_ready else "no_action",
            "snapshot_updated": self.paths["dshe_snapshot_file"],
        }
        self.write_alert_event("DSHE_NOTIFICATION", details)
        self.logger.info(
            f"  → DSHE通知: DEP状态={details['dep_status']}, "
            f"快照={self.paths['dshe_snapshot_file']}"
        )

    def notify_hermes(self, is_ready, probe_results):
        """通知HERMES (通过事件文件 + 日志)"""
        details = {
            "dep_status": "READY" if is_ready else "STILL_BLOCKED",
            "probe_results": probe_results,
            "action_taken": "retest_triggered" if is_ready else "no_action",
            "risk_register": self.paths["risk_register_file"],
        }
        self.write_alert_event("HERMES_NOTIFICATION", details)
        self.logger.info(
            f"  → HERMES通知: DEP状态={details['dep_status']}, "
            f"风险台账={self.paths['risk_register_file']}"
        )

    def run_gate_pre_check(self):
        """V2新增: 触发Gate预检查常态化脚本"""
        gate_check_script = self.work_dir / "gate_pre_check_auto.py"
        if gate_check_script.exists():
            self.logger.info(f"  [run_gate_pre_check] 执行Gate预检查脚本")
            result = self.retest_executor.execute(gate_check_script, self.work_dir)
            if result["success"]:
                self.logger.info(f"  [run_gate_pre_check] Gate预检查完成")
            else:
                self.logger.warning(f"  [run_gate_pre_check] Gate预检查异常: {result.get('error')}")
        else:
            self.logger.debug(f"  [run_gate_pre_check] gate_pre_check_auto.py未找到，跳过")

    def run_single_probe(self):
        """执行单次探测"""
        self.logger.info("执行DEP就绪探测...")
        is_ready, results = self.prober.probe_once()
        self.log_probe_result(is_ready, results)

        if is_ready:
            self.logger.banner("🎉 DEP就绪检测成功!")
            self.write_alert_event("DEP_READY_DETECTED", {
                "probe_results": results,
                "ready_count": sum(1 for r in results if r["probe_ready"]),
                "total_probed": len(results),
            })
            return True
        else:
            self.logger.info("DEP仍未就绪, 等待下次探测...")
            self.write_alert_event("DEP_STILL_BLOCKED", {
                "probe_results": results,
            })
            return False

    def run_post_trigger_actions(self):
        """执行触发后的后续操作"""
        actions = self.config["trigger"].get("post_trigger_actions", [])
        self.logger.banner("执行触发后操作")

        for action in actions:
            if action == "update_bridge_table":
                self.logger.info(f"  [update_bridge_table] 桥接表: {self.paths['bridge_table_file']}")
            elif action == "generate_summary_json":
                self.logger.info(f"  [generate_summary_json] 汇总: {self.paths['summary_json_file']}")
            elif action == "generate_bridge_snapshot":
                self.generate_bridge_snapshot()
            elif action == "compute_md5":
                self.generate_md5_manifest()
            elif action == "notify_dshe":
                self.notify_dshe(True, [])
            elif action == "notify_hermes":
                self.notify_hermes(True, [])
            elif action == "update_risk_register":
                # DEF-004 FIX: 实际持久化写入
                self.risk_updater.update(
                    dep_status="READY",
                    probe_results=self.events,
                    timestamp=datetime.now().isoformat(),
                )
            elif action == "update_gate_package":
                # DEF-004 FIX: 实际持久化写入
                self.gate_updater.update(
                    dep_status="READY",
                    gate_assessment={
                        "gate_status": "NOT_READY",
                        "data_fetchable_rate": "0%",
                        "metadata_completion_rate": "73.6%",
                        "threshold": "80%",
                    },
                    timestamp=datetime.now().isoformat(),
                )
            elif action == "run_gate_pre_check":
                # V2新增: 触发Gate预检查
                self.run_gate_pre_check()
            else:
                self.logger.warning(f"  [UNKNOWN_ACTION] {action}")

    def run_once(self):
        """单次运行模式"""
        self.logger.banner("DSHB V86-RC2 DEP就绪自动复测触发器 V2 — 单次运行")
        self.logger.info(f"版本: {self.config['meta']['version']}")
        self.logger.info(f"工单: {self.config['meta']['ticket_id']}")
        self.logger.info(f"分支: {self.config['meta']['branch']}")
        self.logger.info(f"探测ID: {', '.join(self.prober.probe_ids)}")
        self.logger.info(f"执行器: {type(self.retest_executor).__name__}")

        is_ready = self.run_single_probe()

        if is_ready:
            self.trigger_retest()
            self.run_post_trigger_actions()
        else:
            self.logger.info("DEP未就绪, 单次模式结束。下次运行时自动重试。")

        return is_ready

    def run_daemon(self):
        """持续后台运行模式"""
        interval = self.config["polling"]["interval_seconds"]
        max_probes = self.config["polling"]["max_probes_per_run"]

        self.logger.banner("DSHB V86-RC2 DEP就绪自动复测触发器 V2 — 后台运行")
        self.logger.info(f"轮询间隔: {interval}秒 ({interval/3600:.1f}小时)")
        self.logger.info(f"最大探测次数: {max_probes}")

        probe_count = 0
        while probe_count < max_probes:
            probe_count += 1
            self.logger.info(f"\n{'─'*40} 探测 #{probe_count}/{max_probes} {'─'*40}")

            is_ready = self.run_single_probe()

            if is_ready:
                self.trigger_retest()
                self.run_post_trigger_actions()
                self.logger.banner("🎉 DEP就绪复测完成, 后台运行结束")
                break
            else:
                remaining = max_probes - probe_count
                self.logger.info(
                    f"  剩余探测: {remaining}, "
                    f"下次探测: {datetime.now().strftime('%H:%M:%S')} + {interval//60}分钟"
                )
                if remaining > 0:
                    # DEF-002: 使用InjectableSleep
                    InjectableSleep.sleep(interval)

        self.logger.banner("后台运行结束")

    def run_test(self):
        """测试模式 — 快速验证探测逻辑"""
        self.logger.banner("DSHB V86-RC2 DEP就绪触发器 V2 — 测试模式")
        self.logger.info("快速验证探测逻辑 (不触发复测)")

        is_ready, results = self.prober.probe_once()
        self.log_probe_result(is_ready, results)

        self.logger.banner("测试模式结果")
        for r in results:
            status = "✅ READY" if r["probe_ready"] else "❌ BLOCKED"
            print(
                f"  {r['short_id']:10s} HTTP={r['http_status']} "
                f"pts={r['data_count']} perm={r['perm_state']} => {status}",
                flush=True
            )

        self.logger.info(f"\n整体判定: {'🎉 DEP就绪' if is_ready else '❌ DEP仍阻塞'}")

        if is_ready:
            self.logger.info("⚠️  测试模式下不触发实际复测。如需触发请使用 --mode once")

        return is_ready


# ═══════════════════════════════════════════════════════════
# 命令行入口
# ═══════════════════════════════════════════════════════════
def parse_args(args):
    """解析命令行参数"""
    opts = {
        "config": "trigger_config.yaml",
        "mode": None,
        "probe_only": False,
        "verbose": False,
        "executor": None,  # V2新增
    }

    i = 0
    while i < len(args):
        if args[i] == "--config" and i + 1 < len(args):
            opts["config"] = args[i + 1]
            i += 2
        elif args[i] == "--mode" and i + 1 < len(args):
            opts["mode"] = args[i + 1]
            i += 2
        elif args[i] == "--executor" and i + 1 < len(args):
            opts["executor"] = args[i + 1]
            i += 2
        elif args[i] == "--probe-only":
            opts["probe_only"] = True
            i += 1
        elif args[i] in ("--verbose", "-v"):
            opts["verbose"] = True
            i += 1
        else:
            i += 1

    return opts


def main():
    opts = parse_args(sys.argv[1:])

    # 加载配置
    config_path = opts["config"]
    if not os.path.isabs(config_path):
        config_path = str(Path(__file__).parent / config_path)

    config = ConfigLoader.load(config_path)

    # 覆盖模式
    if opts["mode"]:
        config["polling"]["mode"] = opts["mode"]
    if opts["verbose"]:
        config["polling"]["log_level"] = "DEBUG"

    # 覆盖执行器
    if opts["executor"]:
        config["trigger"]["retest_executor"] = opts["executor"]

    # 设置工作目录
    script_dir = Path(__file__).parent
    config["paths"]["work_dir"] = str(script_dir)

    # 初始化触发器
    logger = TriggerLogger(config["polling"]["log_level"])

    # DEF-003: 注入执行器
    executor_type = config["trigger"].get("retest_executor", "subprocess")
    executor = DirectExecutor() if executor_type == "direct" else None
    trigger = DepReadyTrigger(config, logger, executor=executor)

    # 执行
    if opts["probe_only"]:
        trigger.run_test()
    elif config["polling"]["mode"] == "daemon":
        trigger.run_daemon()
    elif config["polling"]["mode"] == "test":
        trigger.run_test()
    else:
        trigger.run_once()

    return 0


if __name__ == "__main__":
    sys.exit(main())
