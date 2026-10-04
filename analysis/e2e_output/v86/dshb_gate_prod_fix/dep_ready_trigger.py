#!/usr/bin/env python3
"""
DSHB V86-RC2 DEP就绪自动复测触发器
基于 trigger_config.yaml 配置周期性探测zhiji API短ID解析能力，
一旦检测到就绪则自动触发全量178指标复测。

工单: DSHB_V86_RC2_DEP_MONITOR_T3.2
约束: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE

用法:
  python3 dep_ready_trigger.py                      # 使用默认配置
  python3 dep_ready_trigger.py --config <path>     # 指定配置文件
  python3 dep_ready_trigger.py --mode daemon        # 持续后台运行
  python3 dep_ready_trigger.py --mode once          # 单次运行
  python3 dep_ready_trigger.py --mode test           # 测试模式 (快速验证)
  python3 dep_ready_trigger.py --probe-only         # 仅探测不触发
"""

import json, os, sys, time, hashlib, urllib.request, urllib.parse, urllib.error, subprocess
from pathlib import Path
from datetime import datetime
from copy import deepcopy

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
        "user_agent": "Mozilla/5.0 DSHB_DepReady_Trigger/1.0",
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
        "post_trigger_actions": [
            "update_bridge_table",
            "generate_summary_json",
            "generate_bridge_snapshot",
            "compute_md5",
            "notify_dshe",
            "notify_hermes",
            "update_risk_register",
            "update_gate_package",
        ],
        "alert": {
            "enabled": True,
            "channels": ["log", "stdout", "file"],
            "alert_event_file": "dep_ready_trigger_events.json",
        },
    },
    "paths": {
        "work_dir": ".",
        "output_dir": "full_reverify_v3_batch_logs",
        "bridge_table_file": "v86_rc2_prod_id_bridge_mapping_v3_retest.md",
        "dshe_snapshot_file": "v86_rc2_dshb_bridge_snapshot_for_dshe.json",
        "risk_register_file": "v86_rc2_dshb_risk_re_evaluate_v3.md",
        "gate_package_file": "v86_rc2_gate_pre_submit_package_v2.md",
        "inspection_log_file": "v86_rc2_dshb_dp_ticket_weekly_log.md",
        "summary_json_file": "full_reverify_v3_combined_178_summary.json",
        "md5_manifest_file": "MD5_CHECKSUM_LIST_dep_trigger.md",
    },
    "meta": {
        "version": "1.0",
        "task_id": "DSHB_V86_RC2_DEP_MONITOR_T3.2",
        "release_id": "V86-RC2 (DEP Monitor Phase)",
        "ticket_id": "DSHB-DP-REQ-20261015-001",
        "created_date": "2026-10-15",
        "branch": "feature/v85-chart-template",
    },
}


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
        print(f"{'='*70}", flush=True)


class ConfigLoader:
    """YAML配置加载器 (简单解析, 不依赖PyYAML)"""

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

        for line in lines:
            stripped = line.rstrip()
            if not stripped or stripped.startswith("#"):
                continue

            # 计算缩进
            indent = len(line) - len(line.lstrip())
            content = stripped.strip()

            if indent == 0 and content.endswith(":"):
                # 顶级section
                current_section = content[:-1]
                current_subsection = None
                current_subsub = None
            elif indent == 2 and content.endswith(":"):
                # 二级section
                current_subsection = content[:-1]
                current_subsub = None
                if current_section not in config:
                    config[current_section] = {}
                if current_subsection not in config[current_section]:
                    config[current_section][current_subsection] = {}
            elif indent == 4 and content.endswith(":"):
                # 三级section
                current_subsub = content[:-1]
                if current_section in config and current_subsection in config[current_section]:
                    if current_subsub not in config[current_section][current_subsection]:
                        config[current_section][current_subsection][current_subsub] = {}
            elif ":" in content and not content.startswith("- "):
                # key: value 或 key: [list]
                key, _, value = content.partition(":")
                key = key.strip()
                value = value.strip()

                if value == "":
                    value = {}
                elif value.startswith("[") and value.endswith("]") and len(value) > 2:
                    # Simple list parsing
                    inner = value[1:-1].strip()
                    if inner:
                        value = [v.strip().strip('"\'') for v in inner.split(",")]
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
                if current_subsub:
                    target = config[current_section][current_subsection][current_subsub]
                    target[key] = value
                elif current_subsection:
                    target = config[current_section][current_subsection]
                    target[key] = value
                elif current_section:
                    target = config[current_section]
                    target[key] = value
                else:
                    config[key] = value
            elif content.startswith("- "):
                # List item
                item = content[2:].strip().strip('"\'')
                if current_subsub:
                    target = config[current_section][current_subsection][current_subsub]
                elif current_subsection:
                    target = config[current_section][current_subsection]
                else:
                    target = config.get(current_section, {})

                # Find the last key that was a list or add to current section
                # This is a simplified approach
                for k, v in target.items():
                    if isinstance(v, list):
                        v.append(item)
                        break
                else:
                    # Try to add to a list in parent
                    if current_subsection and current_section in config:
                        for k, v in config[current_section][current_subsection].items():
                            if isinstance(v, list):
                                v.append(item)
                                break

        return config


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
        now = time.time()
        wait = self.rate_sec - (now - self._last_request_time)
        if wait > 0:
            time.sleep(wait)
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

            # 解析响应
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

            # 判定
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

            time.sleep(self.probe_interval)

        # 判定整体状态: 任一探测ID就绪即认为DEP就绪
        is_ready = ready_count > 0
        return is_ready, results


class DepReadyTrigger:
    """DEP就绪自动复测触发器核心逻辑"""

    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger or TriggerLogger(config["polling"]["log_level"])
        self.prober = ZhijiProber(
            config["api"], config["probe"], self.logger
        )
        self.paths = config["paths"]
        self.alert_config = config["trigger"].get("alert", {})
        self.work_dir = Path(self.paths.get("work_dir", "."))
        self.events = []

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
        """触发全量复测"""
        script_name = self.config["trigger"]["retest_script"]
        script_path = self.work_dir / script_name

        if not script_path.exists():
            self.logger.error(f"复测脚本不存在: {script_path}")
            return False

        self.logger.banner("触发全量178指标复测")
        self.logger.info(f"执行脚本: {script_path}")

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=3600,  # 1小时超时
                cwd=str(self.work_dir),
            )
            if result.returncode == 0:
                self.logger.info("复测脚本执行成功")
                # 输出复测日志摘要
                if result.stdout:
                    # 仅输出最后50行
                    lines = result.stdout.strip().split("\n")
                    for line in lines[-50:]:
                        self.logger.debug(f"  [retest] {line}")
                return True
            else:
                self.logger.error(f"复测脚本执行失败 (exit={result.returncode})")
                if result.stderr:
                    self.logger.error(f"  stderr: {result.stderr[:500]}")
                return False
        except subprocess.TimeoutExpired:
            self.logger.error("复测脚本执行超时 (1小时)")
            return False
        except Exception as e:
            self.logger.error(f"复测脚本执行异常: {e}")
            return False

    def generate_md5_manifest(self):
        """生成MD5校验清单"""
        self.logger.info("生成MD5校验清单...")
        manifest_path = self.work_dir / self.paths["md5_manifest_file"]
        output_dir = self.work_dir / self.paths["output_dir"]

        files_to_hash = []

        # 收集输出目录中的文件
        if output_dir.exists():
            for f in sorted(output_dir.iterdir()):
                if f.is_file() and f.suffix in (".json", ".md", ".py"):
                    files_to_hash.append(f)

        # 收集根目录中的关键文件
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
            f"# MD5校验清单 — DEP就绪触发器自动生成",
            f"# 生成时间: {datetime.now().isoformat()}",
            f"# 文件数: {len(files_to_hash)}",
            f"",
        ]

        for fp in files_to_hash:
            md5 = hashlib.md5(fp.read_bytes()).hexdigest().upper()
            rel_path = fp.relative_to(self.work_dir) if self.work_dir != Path(".") else fp.name
            size = fp.stat().st_size
            lines.append(f"{md5}  {rel_path}  ({size} bytes)")

        manifest_path.write_text("\n".join(lines), encoding="utf-8")
        self.logger.info(f"MD5清单已保存: {manifest_path} ({len(files_to_hash)} files)")
        return True

    def generate_bridge_snapshot(self):
        """
        确保DSHE桥接快照是最新的
        实际快照由复测脚本 full_reverify_v3_batch_v2.py 自动生成
        这里做校验确认
        """
        snapshot_path = self.work_dir / self.paths["dshe_snapshot_file"]
        if snapshot_path.exists():
            md5 = hashlib.md5(snapshot_path.read_bytes()).hexdigest().upper()
            size = snapshot_path.stat().st_size
            self.logger.info(f"DSHE桥接快照: {snapshot_path.name} ({size}B, MD5={md5})")
            return True
        else:
            self.logger.warning(f"DSHE桥接快照不存在: {snapshot_path}")
            return False

    def write_alert_event(self, event_type, details):
        """写入告警事件"""
        if not self.alert_config.get("enabled", True):
            return

        event = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "task_id": self.config["meta"]["task_id"],
            "ticket_id": self.config["meta"]["ticket_id"],
        }

        # 追加到事件文件
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
        event_file.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        # 控制台输出
        for channel in self.alert_config.get("channels", ["stdout"]):
            if channel == "stdout":
                self.logger.event(f"🔔 {event_type}: {json.dumps(details, ensure_ascii=False)[:200]}")
            elif channel == "log":
                self.logger.info(f"ALERT_EVENT: {event_type}")
            elif channel == "file":
                pass  # 已写入文件

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
                self.logger.info(f"  [update_risk_register] 风险台账: {self.paths['risk_register_file']}")
            elif action == "update_gate_package":
                self.logger.info(f"  [update_gate_package] Gate预审包: {self.paths['gate_package_file']}")
            else:
                self.logger.warning(f"  [UNKNOWN_ACTION] {action}")

    def run_once(self):
        """单次运行模式"""
        self.logger.banner("DSHB V86-RC2 DEP就绪自动复测触发器 — 单次运行")
        self.logger.info(f"版本: {self.config['meta']['version']}")
        self.logger.info(f"工单: {self.config['meta']['ticket_id']}")
        self.logger.info(f"分支: {self.config['meta']['branch']}")
        self.logger.info(f"探测ID: {', '.join(self.prober.probe_ids)}")

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

        self.logger.banner("DSHB V86-RC2 DEP就绪自动复测触发器 — 后台运行")
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
                    time.sleep(interval)

        self.logger.banner("后台运行结束")

    def run_test(self):
        """测试模式 — 快速验证探测逻辑"""
        self.logger.banner("DSHB V86-RC2 DEP就绪触发器 — 测试模式")
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


def parse_args(args):
    """解析命令行参数"""
    opts = {
        "config": "trigger_config.yaml",
        "mode": None,
        "probe_only": False,
        "verbose": False,
    }

    i = 0
    while i < len(args):
        if args[i] == "--config" and i + 1 < len(args):
            opts["config"] = args[i + 1]
            i += 2
        elif args[i] == "--mode" and i + 1 < len(args):
            opts["mode"] = args[i + 1]
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

    # 设置工作目录
    script_dir = Path(__file__).parent
    config["paths"]["work_dir"] = str(script_dir)

    # 初始化触发器
    logger = TriggerLogger(config["polling"]["log_level"])
    trigger = DepReadyTrigger(config, logger)

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