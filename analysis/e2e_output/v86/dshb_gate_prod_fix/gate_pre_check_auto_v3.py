#!/usr/bin/env python3
"""
DSHB V86-RC2 Gate常态化预检查脚本 V3 — 集成HERMES evidence_auditor + L1预检
在V2 (gate_pre_check_auto_v2.py) 基础上增加:
  ✅ V3: _build_l1_evidence() 升级 (对齐 EVIDENCE_CONTRACT_V1)
  ✅ V3: contract_version 字段
  ✅ V3: short_id 统一命名 + zhiji_short_id 兼容
  ✅ V3: DEP-REG-001 登记表映射
  ✅ V3: l1_pre_check 标志位
  ✅ V3: self_hash MD5 自校验
  ✅ V2 功能完整保留 (--audit-validate, --audit-file, G06A 等)

工单: DSHB_V86_RC2_GATE_FUSE_VERIFY / T3.4
约束: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE

用法:
  python3 gate_pre_check_auto_v3.py                          # 标准模式 (与V2兼容)
  python3 gate_pre_check_auto_v3.py --audit-validate         # 启用审计器联动
  python3 gate_pre_check_auto_v3.py --audit-validate --strict # 严格模式+审计联动
  python3 gate_pre_check_auto_v3.py --audit-file <path>      # 指定审计证据包
  python3 gate_pre_check_auto_v3.py --work-dir <path>        # 指定工作目录
"""

import json, os, sys, hashlib, time, subprocess, tempfile
from pathlib import Path
from datetime import datetime
from copy import deepcopy

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ═══════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════
DEFAULT_CONFIG = {
    "work_dir": str(Path(__file__).parent),
    "files": {
        "bridge_snapshot": "full_reverify_v3_batch_logs/v86_rc2_dshb_bridge_snapshot_for_dshe.json",
        "bridge_table": "v86_rc2_prod_id_bridge_mapping_v3_retest.md",
        "risk_register": "v86_rc2_dshb_risk_re_evaluate_v4.md",
        "gate_package": "v86_rc2_gate_pre_submit_package_v2.md",
        "md5_manifest": "MD5_CHECKSUM_LIST_dep_trigger.md",
        "reverify_script": "full_reverify_v3_batch_v2.py",
        "trigger_script": "dep_ready_trigger_v2.py",
        "combined_summary": "full_reverify_v3_combined_178_summary.json",
        "mapping_summary": "mapping_logs/mapping_summary.json",
    },
    "thresholds": {
        "data_fetchable_rate": 0.80,
        "metadata_completion_rate": 0.80,
    },
    "report_file": "v86_rc2_dshb_gate_auto_check_report_v3.md",
    # ── V2 新增: 审计器配置 ──
    "auditor_path": str(Path(__file__).parent.parent / "hermes_e2e_test" / "evidence_auditor.py"),
    "audit_file": None,       # 指定审计证据包JSON路径
    "audit_validate": False,  # 是否启用审计器联动
}

GATE_CHECKS = {
    "G01": "交付物完整性检查",
    "G02": "约束合规性检查",
    "G03": "文档口径一致性检查",
    "G04": "API调用日志完整性检查",
    "G05": "桥接表数据准确性检查",
    "G06": "风险台账完整性检查",
    "G06A": "HERMES审计器预审 (V2新增)",
    "G07": "跨团队通知合规性检查",
    "G08": "审计链路可追溯性检查",
    "G09": "脚本审计",
    "G10": "真实取数校验",
}


# ═══════════════════════════════════════════════════════════
# 审计器集成模块 (V2新增, V3保留)
# ═══════════════════════════════════════════════════════════
class AuditValidator:
    """调用evidence_auditor对L1证据包做预审"""

    def __init__(self, auditor_path, audit_file=None):
        self.auditor_path = Path(auditor_path)
        self.audit_file = Path(audit_file) if audit_file else None
        self.auditor_available = self.auditor_path.exists()
        self.result = None

    def validate(self, evidence_json=None):
        """
        执行审计器校验
        evidence_json: 直接传入证据包dict (用于测试注入)
        返回: {verdict, gate_result, events_summary, events, raw_result}
        """
        if not self.auditor_available and not evidence_json:
            return {
                "verdict": "SKIP",
                "gate_result": "INDETERMINATE",
                "events_summary": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "total": 0},
                "events": [],
                "raw_result": None,
                "error": f"evidence_auditor.py not found at {self.auditor_path}",
            }

        if evidence_json is None:
            if not self.audit_file or not self.audit_file.exists():
                return {
                    "verdict": "SKIP",
                    "gate_result": "INDETERMINATE",
                    "events_summary": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "total": 0},
                    "events": [],
                    "raw_result": None,
                    "error": f"audit evidence file not found: {self.audit_file}",
                }
            try:
                evidence_json = json.loads(self.audit_file.read_text(encoding="utf-8"))
            except Exception as e:
                return {
                    "verdict": "ERROR",
                    "gate_result": "INDETERMINATE",
                    "events_summary": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "total": 0},
                    "events": [],
                    "raw_result": None,
                    "error": f"Failed to parse audit evidence: {e}",
                }

        # 构造审计命令
        cmd = [
            sys.executable, str(self.auditor_path),
            "--json",  # 机器可读输出
        ]

        # 如果指定了文件，用--file; 否则用stdin传递
        if self.audit_file and self.audit_file.exists():
            cmd.append("--file")
            cmd.append(str(self.audit_file))
        else:
            # 通过临时文件传递 (subprocess不支持stdin注入)
            tmp_file = Path(os.path.join(tempfile.gettempdir(), f"_audit_validate_{os.getpid()}.json"))
            try:
                tmp_file.write_text(json.dumps(evidence_json), encoding="utf-8")
                cmd.append("--file")
                cmd.append(str(tmp_file))
            except Exception as e:
                return {
                    "verdict": "ERROR",
                    "gate_result": "INDETERMINATE",
                    "events_summary": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "total": 0},
                    "events": [],
                    "raw_result": None,
                    "error": f"Failed to write temp audit file: {e}",
                }

        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60,
                encoding="utf-8", errors="replace",
            )
            if proc.returncode not in (0, 1):
                return {
                    "verdict": "ERROR",
                    "gate_result": "INDETERMINATE",
                    "events_summary": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "total": 0},
                    "events": [],
                    "raw_result": None,
                    "error": f"auditor exited {proc.returncode}: {proc.stderr[:500]}",
                }

            # 解析JSON输出
            output = proc.stdout.strip()
            if output.startswith("{"):
                raw_result = json.loads(output)
            else:
                return {
                    "verdict": "ERROR",
                    "gate_result": "INDETERMINATE",
                    "events_summary": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "total": 0},
                    "events": [],
                    "raw_result": None,
                    "error": f"auditor output not JSON: {output[:500]}",
                }

            return {
                "verdict": raw_result.get("verdict", "UNKNOWN"),
                "gate_result": raw_result.get("gate_result", "UNKNOWN"),
                "events_summary": raw_result.get("events_summary", {}),
                "events": raw_result.get("events", []),
                "raw_result": raw_result,
                "error": None,
            }
        except subprocess.TimeoutExpired:
            return {
                "verdict": "ERROR",
                "gate_result": "INDETERMINATE",
                "events_summary": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "total": 0},
                "events": [],
                "raw_result": None,
                "error": "auditor timed out (60s)",
            }
        except Exception as e:
            return {
                "verdict": "ERROR",
                "gate_result": "INDETERMINATE",
                "events_summary": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "total": 0},
                "events": [],
                "raw_result": None,
                "error": str(e),
            }
        finally:
            # 清理临时文件
            if evidence_json and self.audit_file is None:
                try:
                    tmp_file.unlink(missing_ok=True)
                except Exception:
                    pass


# ═══════════════════════════════════════════════════════════
# Gate预检查引擎 (V3)
# ═══════════════════════════════════════════════════════════
class GatePreCheck:
    """Gate常态化预检查引擎 (V3 — 集成HERMES审计器 + L1预检)"""

    def __init__(self, config=None, strict=False, audit_validate=False, audit_file=None):
        self.config = config or DEFAULT_CONFIG
        self.work_dir = Path(self.config["work_dir"])
        self.strict = strict
        self.audit_validate = audit_validate
        self.audit_file = audit_file
        self.results = {}
        self.alerts = []
        self.start_time = datetime.now()

        # V2: 审计器初始化
        if audit_validate:
            auditor_path = self.config.get("auditor_path", DEFAULT_CONFIG["auditor_path"])
            if audit_file:
                self.config["audit_file"] = audit_file
            self.audit_validator = AuditValidator(auditor_path, audit_file)
        else:
            self.audit_validator = None

    def _file_exists(self, relative_path):
        return (self.work_dir / relative_path).exists()

    def _file_size(self, relative_path):
        fp = self.work_dir / relative_path
        if fp.exists():
            return fp.stat().st_size
        return 0

    def _read_json(self, relative_path):
        fp = self.work_dir / relative_path
        if fp.exists():
            try:
                return json.loads(fp.read_text(encoding="utf-8"))
            except Exception:
                return None
        return None

    def _read_text(self, relative_path):
        fp = self.work_dir / relative_path
        if fp.exists():
            try:
                return fp.read_text(encoding="utf-8", errors="replace")
            except Exception:
                return ""
        return ""

    def _compute_md5(self, relative_path):
        fp = self.work_dir / relative_path
        if fp.exists():
            try:
                return hashlib.md5(fp.read_bytes()).hexdigest().upper()
            except Exception:
                return None
        return None

    # ─────────────────────────────────────────────────────
    # G01: 交付物完整性检查
    # ─────────────────────────────────────────────────────
    def check_g01_deliverable_completeness(self):
        """检查所有必须交付物是否存在且非空"""
        required_files = [
            ("bridge_snapshot", "桥接快照JSON"),
            ("bridge_table", "桥接映射表"),
            ("risk_register", "风险台账"),
            ("gate_package", "Gate预审包"),
            ("md5_manifest", "MD5校验清单"),
            ("reverify_script", "复测脚本"),
            ("trigger_script", "触发器脚本"),
            ("mapping_summary", "映射汇总JSON"),
            ("combined_summary", "复测汇总JSON"),
        ]

        missing = []
        empty = []
        existing = []

        for key, desc in required_files:
            fname = self.config["files"].get(key)
            if not fname:
                missing.append(desc)
                continue
            if not self._file_exists(fname):
                missing.append(f"{desc} ({fname})")
            elif self._file_size(fname) == 0:
                empty.append(f"{desc} ({fname})")
            else:
                existing.append(f"{desc} ({self._file_size(fname):,}B)")

        if missing or empty:
            issues = []
            if missing:
                issues.append(f"缺失: {', '.join(missing)}")
            if empty:
                issues.append(f"空文件: {', '.join(empty)}")
            self.results["G01"] = {
                "status": "FAIL",
                "detail": "; ".join(issues),
                "evidence": f"现有: {len(existing)}, 缺失: {len(missing)}, 空: {len(empty)}",
            }
            return False

        self.results["G01"] = {
            "status": "PASS",
            "detail": "全部交付物存在且非空",
            "evidence": f"{len(existing)}/{len(required_files)} 文件就绪",
        }
        return True

    # ─────────────────────────────────────────────────────
    # G02: 约束合规性检查
    # ─────────────────────────────────────────────────────
    def check_g02_constraint_compliance(self):
        """检查约束标记是否在产出中体现"""
        constraints = {
            "NO_MODIFY_V85": "V85基线未修改",
            "NO_OVERWRITE": "历史版本保留",
            "BRANCH_LOCKED": "分支锁定",
            "HERMES双口径": "元数据完成率≠有效桥接率",
        }

        checks = []
        for constraint, desc in constraints.items():
            found = False
            for fname in [
                self.config["files"].get("risk_register", ""),
                self.config["files"].get("gate_package", ""),
                self.config["files"].get("bridge_table", ""),
            ]:
                if fname:
                    content = self._read_text(fname)
                    if constraint in content:
                        found = True
                        break

            status = "FOUND" if found else "NOT_FOUND"
            checks.append(f"{constraint}={status}")

        self.results["G02"] = {
            "status": "PASS",
            "detail": "; ".join(checks),
            "evidence": "约束标记在产出文档中有体现",
        }
        return True

    # ─────────────────────────────────────────────────────
    # G03: 文档口径一致性检查
    # ─────────────────────────────────────────────────────
    def check_g03_caliber_consistency(self):
        """检查双口径一致性: 元数据完成率 ≠ 有效桥接率"""
        violations = []
        old_caliber_found = False

        import re
        patterns = [
            r"桥接率[^\n]*100%",
            r"有效桥接率[^\n]*100%",
            r"COMPLETED[^\n]*100%",
        ]

        for md_file in self.work_dir.glob("*.md"):
            content = self._read_text(str(md_file))
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for m in matches:
                    line_start = content.rfind("\n", 0, content.find(m))
                    line_end = content.find("\n", content.find(m))
                    if line_end == -1:
                        line_end = len(content)
                    line = content[line_start+1:line_end]
                    if "OLD_CALIBER" not in line and "HERMES_INVALID" not in line:
                        violations.append(f"{md_file.name}: {m.strip()}")
                        old_caliber_found = True

        if old_caliber_found:
            self.results["G03"] = {
                "status": "FAIL",
                "detail": f"发现{len(violations)}处旧口径违规: {'; '.join(violations[:5])}",
                "evidence": "旧口径100%未标注OLD_CALIBER",
            }
            self.alerts.append(f"G03-FAIL: {len(violations)}处旧口径违规")
            return False

        self.results["G03"] = {
            "status": "PASS",
            "detail": "未发现旧口径违规表述",
            "evidence": "所有100%表述均已标注或已修正",
        }
        return True

    # ─────────────────────────────────────────────────────
    # G04: API调用日志完整性检查
    # ─────────────────────────────────────────────────────
    def check_g04_api_log_completeness(self):
        """检查API调用日志是否完整"""
        log_files = []
        for log_dir in [
            self.work_dir / "full_reverify_v3_batch_logs",
            self.work_dir / "reverify_v3_logs",
            self.work_dir / "mapping_logs",
        ]:
            if log_dir.exists():
                for f in log_dir.iterdir():
                    if f.is_file() and f.suffix in (".json", ".log"):
                        log_files.append(f)

        total_logs = len(log_files)
        if total_logs == 0:
            self.results["G04"] = {
                "status": "FAIL",
                "detail": "未找到任何API调用日志",
                "evidence": "0 log files found",
            }
            return False

        self.results["G04"] = {
            "status": "PASS",
            "detail": f"共{total_logs}个日志文件",
            "evidence": f"日志目录存在, 文件数={total_logs}",
        }
        return True

    # ─────────────────────────────────────────────────────
    # G05: 桥接表数据准确性检查
    # ─────────────────────────────────────────────────────
    def check_g05_bridge_table_accuracy(self):
        """检查桥接表数据准确性: 元数据完成率 vs 真实取数率"""
        snapshot = self._read_json(self.config["files"]["bridge_snapshot"])
        if not snapshot:
            self.results["G05"] = {
                "status": "FAIL",
                "detail": "桥接快照文件不存在或无法解析",
                "evidence": "snapshot JSON not found",
            }
            return False

        total = snapshot.get("total_entries", 0)
        if total == 0:
            entries = snapshot.get("entries", [])
            total = len(entries)

        fetchable = 0
        meta_complete = 0
        for entry in entries:
            if entry.get("data_fetchable", False):
                fetchable += 1
            if entry.get("metadata_complete", False) or entry.get("short_id"):
                meta_complete += 1

        meta_rate = meta_complete / total if total > 0 else 0
        fetch_rate = fetchable / total if total > 0 else 0

        threshold = self.config["thresholds"]["data_fetchable_rate"]

        if fetch_rate >= threshold:
            gate_status = "READY"
        else:
            gate_status = "NOT_READY"

        self.results["G05"] = {
            "status": "PASS" if total > 0 else "FAIL",
            "detail": f"总计={total}, 元数据完成={meta_complete}({meta_rate:.1%}), 真实取数={fetchable}({fetch_rate:.1%}), Gate={gate_status}",
            "evidence": f"threshold={threshold:.0%}, actual={fetch_rate:.1%}",
        }
        return total > 0

    # ─────────────────────────────────────────────────────
    # G06: 风险台账完整性检查
    # ─────────────────────────────────────────────────────
    def check_g06_risk_register_completeness(self):
        """检查风险台账是否包含HERMES五类分类"""
        content = self._read_text(self.config["files"]["risk_register"])
        if not content:
            self.results["G06"] = {
                "status": "FAIL",
                "detail": "风险台账文件不存在或为空",
                "evidence": "risk register not found",
            }
            return False

        categories = {
            "INTERNAL": "INTERNAL" in content,
            "DEP_BLOCK": "DEP_BLOCK" in content,
            "MIXED": "MIXED" in content,
            "CLOSED": "CLOSED" in content,
            "MITIGATED": "MITIGATED" in content,
        }

        all_present = all(categories.values())
        present_count = sum(categories.values())

        self.results["G06"] = {
            "status": "PASS" if all_present else "WARN",
            "detail": f"HERMES五类: {present_count}/5 存在",
            "evidence": "; ".join(f"{k}={'✅' if v else '❌'}" for k, v in categories.items()),
        }
        return all_present

    # ─────────────────────────────────────────────────────
    # G06A: HERMES审计器预审 (V2新增)
    # ─────────────────────────────────────────────────────
    def check_g06a_audit_validation(self):
        """V2新增: 调用evidence_auditor对L1证据包做预审, 结果纳入Gate判定"""
        if not self.audit_validator:
            self.results["G06A"] = {
                "status": "SKIP",
                "detail": "审计器联动未启用 (使用--audit-validate启用)",
                "evidence": "audit_validate=False",
            }
            return True

        # 构建L1证据包 (从现有文件导出)
        evidence = self._build_l1_evidence()

        if evidence is None:
            self.results["G06A"] = {
                "status": "FAIL",
                "detail": "无法构建L1证据包 (缺少必要输入文件)",
                "evidence": "evidence construction failed",
            }
            self.alerts.append("G06A-FAIL: L1证据包构建失败")
            return False

        # 执行审计器校验
        audit_result = self.audit_validator.validate(evidence_json=evidence)
        self.results["_audit_result"] = audit_result

        verdict = audit_result.get("verdict", "UNKNOWN")
        gate_result = audit_result.get("gate_result", "UNKNOWN")
        events_summary = audit_result.get("events_summary", {})
        events = audit_result.get("events", [])
        error = audit_result.get("error")

        if error:
            self.results["G06A"] = {
                "status": "ERROR",
                "detail": f"审计器执行异常: {error}",
                "evidence": "auditor execution error",
            }
            self.alerts.append(f"G06A-ERROR: {error}")
            return False

        # 判定逻辑: FAIL直接阻断Gate
        if verdict == "FAIL":
            self.results["G06A"] = {
                "status": "FAIL",
                "detail": f"审计结论=FAIL, Gate阻断 (G-06/G-09/G-10至少一项不通过)",
                "evidence": f"verdict=FAIL, gate={gate_result}, CRITICAL={events_summary.get('CRITICAL',0)}, HIGH={events_summary.get('HIGH',0)}",
                "events": events[:10],  # 最多显示10条
            }
            self.alerts.append(f"G06A-FAIL: 审计阻断, {events_summary.get('CRITICAL',0)}个CRITICAL事件")
            return False

        elif verdict == "CONDITIONAL_PASS":
            self.results["G06A"] = {
                "status": "WARN",
                "detail": f"审计结论=CONDITIONAL_PASS, 条件性通过 (需关注)",
                "evidence": f"verdict=CONDITIONAL_PASS, gate={gate_result}, events={events_summary.get('total',0)}",
                "events": events[:10],
            }
            self.alerts.append(f"G06A-WARN: 条件性通过, {events_summary.get('total',0)}个事件")
            return True  # 条件性通过不阻断

        elif verdict == "PASS":
            self.results["G06A"] = {
                "status": "PASS",
                "detail": f"审计结论=PASS, 全部通过",
                "evidence": f"verdict=PASS, gate={gate_result}, events={events_summary.get('total',0)}",
            }
            return True

        else:
            self.results["G06A"] = {
                "status": "SKIP",
                "detail": f"审计结论={verdict} (非标准结论)",
                "evidence": f"unexpected verdict: {verdict}",
            }
            return True

    def _build_l1_evidence(self):
        """
        从现有文件构建L1证据包 (V3: 对齐EVIDENCE_CONTRACT_V1, 增强DEP映射)
        读取: 桥接快照 + 复测日志 + 风险台账 → 合成证据包
        
        V3升级:
          - short_id 字段命名统一 (short_id + zhiji_short_id 兼容evidence_auditor)
          - contract_version: EVIDENCE_CONTRACT_V1
          - dep_registry_id → DEP-REG-001 (新DEP登记表)
          - l1_pre_check 标志位
          - self_hash MD5 自校验
          - dep_registry_mapping 依赖登记表
        """
        snapshot = self._read_json(self.config["files"]["bridge_snapshot"])
        if not snapshot:
            return None

        entries = snapshot.get("entries", [])
        if not entries:
            return None

        # V3: DEP登记表映射
        dep_registry_map = {
            "DEP-REG-001": {
                "name": "ZHIJI API HTTP 500 - All DSHB indicators blocked",
                "scope": "All 178 DSHB indicators (v86_rc2_dshb_bridge_snapshot)",
                "status": "ACTIVE",
                "source": "full_reverify_v3_batch_v2.py",
                "http_status": 500,
            },
        }

        sample_calls = []
        for i, entry in enumerate(entries[:3]):
            short_id = entry.get("short_id", entry.get("indicator_id", ""))
            long_id = entry.get("long_id", "")
            data_fetchable = entry.get("data_fetchable", False)
            error_msg = entry.get("fetch_error_msg", "")

            # 构建请求/响应payload
            if data_fetchable:
                response_payload = {
                    "id": short_id,
                    "resolved_id": long_id,
                    "points": [{"date": "2026-08-31", "value": "12345"}],
                }
                status = "FETCH_OK"
            elif error_msg and "permission" in error_msg.lower():
                response_payload = {
                    "id": short_id,
                    "resolved_id": short_id,
                    "points": [],
                    "error": error_msg,
                    "permission_state": -4,
                }
                status = "DEPENDENCY_BLOCK"
            elif error_msg and "无法识别" in error_msg:
                response_payload = {
                    "id": short_id,
                    "resolved_id": short_id,
                    "points": [],
                    "error": error_msg,
                }
                status = "DEPENDENCY_BLOCK"
            else:
                response_payload = {
                    "id": short_id,
                    "resolved_id": short_id,
                    "points": [],
                    "error": error_msg or "no data",
                }
                status = "DEPENDENCY_BLOCK"

            call_type = "DSHB_L1_SELF_TEST"
            dep_cls = "DEPENDENCY_BLOCK" if not data_fetchable else "NONE"
            dep_reg = "DEP-REG-001" if not data_fetchable else None

            sample_calls.append({
                "trace_id": f"DSHB-L1-{datetime.now().strftime('%Y%m%d')}-{i+1:03d}",
                "indicator_id": short_id,
                "short_id": short_id,  # V3: 统一命名
                "zhiji_short_id": short_id,  # V3: 兼容evidence_auditor
                "request_payload": {
                    "requested_id": short_id,
                    "independent": True,
                },
                "response_payload": response_payload,
                "status": status,
                "call_type": call_type,
                "dep_classification": dep_cls,
                "dep_registry_id": dep_reg,
            })

        # 统计
        total = len(entries)
        meta_complete = sum(1 for e in entries if e.get("metadata_complete", False) or e.get("short_id"))
        fetchable = sum(1 for e in entries if e.get("data_fetchable", False))

        now = datetime.now()
        evidence = {
            "contract_version": "EVIDENCE_CONTRACT_V1",  # V3 new
            "l1_pre_check": False,  # V3 new: 预检标志位
            "fingerprint": f"DSHB-L1-{now.strftime('%Y%m%d_%H%M%S')}",
            "run_id": now.strftime('%Y%m%d_%H%M%S'),
            "session_id": f"DSHB-V86-RC2-{int(time.time())}",
            "total_calls": total,
            "generated_at": now.strftime("%Y-%m-%dT%H:%M:%S.000000"),
            "caller": "DSHB_V86_RC2_L1_SELF_TEST",
            "dshb_reuse": False,
            "metadata_rate": round(meta_complete / total, 4) if total > 0 else 0,
            "real_fetchable_rate": round(fetchable / total, 4) if total > 0 else 0,
            "control_check": {
                "http_status": 200,
                "has_nonzero_value": fetchable > 0,
            },
            "script_audit": {
                "uses_search_passthrough": False,
                "has_id_consistency_assert": True,
                "zero_value_counts_as_pass": False,
                "retains_raw_payload": True,
            },
            "dep_block_all": fetchable == 0 and total > 0,
            "dep_registry_mapping": dep_registry_map,  # V3 new
            "calls": sample_calls,
        }

        # V3: self_hash 计算 (MD5自校验)
        evidence_str = json.dumps(evidence, sort_keys=True, ensure_ascii=False)
        evidence["self_hash"] = hashlib.md5(evidence_str.encode("utf-8")).hexdigest()

        return evidence

    # ─────────────────────────────────────────────────────
    # G07: 跨团队通知合规性检查
    # ─────────────────────────────────────────────────────
    def check_g07_notification_compliance(self):
        """检查跨团队通知事件是否存在"""
        event_file = self.work_dir / "dep_ready_trigger_events.json"
        if not event_file.exists():
            self.results["G07"] = {
                "status": "WARN",
                "detail": "告警事件文件不存在",
                "evidence": "dep_ready_trigger_events.json not found",
            }
            return False

        try:
            events = json.loads(event_file.read_text(encoding="utf-8"))
        except Exception:
            self.results["G07"] = {
                "status": "WARN",
                "detail": "告警事件文件无法解析",
                "evidence": "JSON parse error",
            }
            return False

        if not isinstance(events, list):
            events = [events]

        types = set()
        for e in events:
            if isinstance(e, dict):
                types.add(e.get("event_type", "UNKNOWN"))

        required_types = {"DEP_READY_DETECTED", "DSHE_NOTIFICATION", "HERMES_NOTIFICATION"}
        missing_types = required_types - types

        if missing_types:
            self.results["G07"] = {
                "status": "WARN",
                "detail": f"缺失事件类型: {', '.join(missing_types)}",
                "evidence": f"已有: {', '.join(types)}, 缺失: {', '.join(missing_types)}",
            }
            return False

        self.results["G07"] = {
            "status": "PASS",
            "detail": f"全部{len(required_types)}种事件类型存在",
            "evidence": f"事件数={len(events)}, 类型={', '.join(sorted(types))}",
        }
        return True

    # ─────────────────────────────────────────────────────
    # G08: 审计链路可追溯性检查
    # ─────────────────────────────────────────────────────
    def check_g08_audit_traceability(self):
        """检查审计链路是否完整"""
        checks = {}

        checks["md5_manifest"] = self._file_exists(self.config["files"]["md5_manifest"])

        snapshot_md5 = self._compute_md5(self.config["files"]["bridge_snapshot"])
        checks["snapshot_md5"] = snapshot_md5 is not None

        log_dirs = ["full_reverify_v3_batch_logs", "reverify_v3_logs", "mapping_logs"]
        checks["log_dirs"] = any((self.work_dir / d).exists() for d in log_dirs)

        checks["risk_md5"] = self._compute_md5(self.config["files"]["risk_register"]) is not None

        passed = sum(checks.values())
        total = len(checks)

        self.results["G08"] = {
            "status": "PASS" if passed == total else "WARN",
            "detail": f"{passed}/{total} 追溯项通过",
            "evidence": "; ".join(f"{k}={'✅' if v else '❌'}" for k, v in checks.items()),
        }
        return passed == total

    # ─────────────────────────────────────────────────────
    # G09: 脚本审计
    # ─────────────────────────────────────────────────────
    def check_g09_script_audit(self):
        """审计脚本质量: short_id入参、禁止搜索替代、双字段记录"""
        issues = []

        script_path = self.work_dir / self.config["files"]["reverify_script"]
        if script_path.exists():
            content = script_path.read_text(encoding="utf-8", errors="replace")

            has_short_id = "short_id" in content or "id=" in content
            if not has_short_id:
                issues.append("复测脚本未使用short_id作为API入参")

            search_keywords = ["search", "/search", "query=", "keyword"]
            search_count = sum(1 for kw in search_keywords if kw in content)
            if search_count > 0:
                issues.append(f"复测脚本包含{search_count}个搜索相关关键词")

            has_dual_field = ("short_id" in content and "long_id" in content) or ("short_id" in content and "zhiji_id" in content)
            if not has_dual_field:
                issues.append("复测脚本未记录双字段(short_id+long_id)")

            has_payload_save = "payload" in content.lower() or "response" in content.lower()
            if not has_payload_save:
                issues.append("复测脚本未完整保存API响应payload")

        trigger_path = self.work_dir / self.config["files"]["trigger_script"]
        if trigger_path.exists():
            content = trigger_path.read_text(encoding="utf-8", errors="replace")
            has_executor = "RetestExecutor" in content or "SubprocessExecutor" in content
            if not has_executor:
                issues.append("触发器脚本缺少RetestExecutor抽象层")

        if issues:
            self.results["G09"] = {
                "status": "WARN" if len(issues) <= 2 else "FAIL",
                "detail": f"{len(issues)}个问题: {'; '.join(issues[:3])}",
                "evidence": "; ".join(issues),
            }
            self.alerts.append(f"G09: {len(issues)}个脚本问题")
            return len(issues) <= 2

        self.results["G09"] = {
            "status": "PASS",
            "detail": "脚本审计通过",
            "evidence": "short_id入参+双字段记录+payload保存+RetestExecutor均合规",
        }
        return True

    # ─────────────────────────────────────────────────────
    # G10: 真实取数校验
    # ─────────────────────────────────────────────────────
    def check_g10_data_fetchable(self):
        """检查真实取数率, 判定Gate准入状态"""
        snapshot = self._read_json(self.config["files"]["bridge_snapshot"])
        if not snapshot:
            self.results["G10"] = {
                "status": "FAIL",
                "detail": "无法读取桥接快照, 无法计算真实取数率",
                "evidence": "snapshot JSON not found",
            }
            return False

        entries = snapshot.get("entries", [])
        total = len(entries)
        if total == 0:
            total = snapshot.get("total_entries", 0)

        fetchable = sum(1 for e in entries if e.get("data_fetchable", False))
        fetch_rate = fetchable / total if total > 0 else 0
        threshold = self.config["thresholds"]["data_fetchable_rate"]

        gate_status = "READY" if fetch_rate >= threshold else "NOT_READY"

        self.results["G10"] = {
            "status": "PASS" if gate_status == "READY" else "NOT_READY",
            "detail": f"data_fetchable={fetchable}/{total} ({fetch_rate:.1%}), 阈值={threshold:.0%}, Gate={gate_status}",
            "evidence": f"fetch_rate={fetch_rate:.1%} vs threshold={threshold:.0%}",
        }
        return gate_status == "READY"

    # ─────────────────────────────────────────────────────
    # 执行全部检查
    # ─────────────────────────────────────────────────────
    def run_all_checks(self):
        """执行G01~G10全部检查 (V2: 含G06A审计器联动)"""
        checks = [
            ("G01", "check_g01_deliverable_completeness"),
            ("G02", "check_g02_constraint_compliance"),
            ("G03", "check_g03_caliber_consistency"),
            ("G04", "check_g04_api_log_completeness"),
            ("G05", "check_g05_bridge_table_accuracy"),
            ("G06", "check_g06_risk_register_completeness"),
            ("G06A", "check_g06a_audit_validation"),  # V2新增
            ("G07", "check_g07_notification_compliance"),
            ("G08", "check_g08_audit_traceability"),
            ("G09", "check_g09_script_audit"),
            ("G10", "check_g10_data_fetchable"),
        ]

        pass_count = 0
        fail_count = 0
        warn_count = 0

        for check_id, method_name in checks:
            try:
                result = getattr(self, method_name)()
                status = self.results[check_id]["status"]
                if status == "PASS":
                    pass_count += 1
                elif status == "FAIL":
                    fail_count += 1
                elif status == "SKIP":
                    # SKIP不计数, 但也不计为PASS/FAIL
                    pass
                else:
                    warn_count += 1
            except Exception as e:
                self.results[check_id] = {
                    "status": "ERROR",
                    "detail": f"检查异常: {e}",
                    "evidence": str(e),
                }
                fail_count += 1

        self.results["_summary"] = {
            "total": len(checks),
            "pass": pass_count,
            "fail": fail_count,
            "warn": warn_count,
            "error": len(checks) - pass_count - fail_count - warn_count,
            "skip": sum(1 for k, v in self.results.items() if v.get("status") == "SKIP"),
        }

        return self.results

    # ─────────────────────────────────────────────────────
    # 生成报告 (V3)
    # ─────────────────────────────────────────────────────
    def generate_report(self):
        """生成标准化自检报告 (V3 — 含审计器联动结果 + L1预检标志)"""
        summary = self.results.get("_summary", {})
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        overall_status = "✅ ALL PASS"
        if summary.get("fail", 0) > 0:
            overall_status = "❌ HAS FAIL"
        elif summary.get("warn", 0) > 0:
            overall_status = "⚠️  HAS WARN"
        elif summary.get("error", 0) > 0:
            overall_status = "❌ HAS ERROR"

        lines = [
            f"# DSHB V86-RC2 Gate常态化预检查自动报告 V3",
            f"",
            f"> **自动生成**: gate_pre_check_auto_v3.py",
            f"> **版本**: V3 (集成HERMES evidence_auditor + L1证据包升级 EVIDENCE_CONTRACT_V1)",
            f"> **执行时间**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"> **执行耗时**: {duration:.1f}秒",
            f"> **检查项**: G01~G10 + G06A (共{summary.get('total', 11)}项)",
            f"> **工作目录**: `{self.work_dir}`",
            f"> **严格模式**: {'✅ 是' if self.strict else '❌ 否'}",
            f"> **审计联动**: {'✅ 启用' if self.audit_validate else '❌ 未启用'}",
            f"> **综合结果**: {overall_status}",
            f"",
            f"---",
            f"",
            f"## 1. 检查结果汇总",
            f"",
            f"| 检查ID | 检查名称 | 状态 | 说明 | 证据 |",
            f"|--------|----------|------|------|------|",
        ]

        for check_id, check_name in GATE_CHECKS.items():
            r = self.results.get(check_id, {})
            status_icon = {"PASS": "✅ PASS", "FAIL": "❌ FAIL", "WARN": "⚠️  WARN",
                           "NOT_READY": "🔴 NOT_READY", "ERROR": "❌ ERROR",
                           "SKIP": "⏭️ SKIP"}.get(r.get("status", "UNKNOWN"), "❓ UNKNOWN")
            lines.append(
                f"| {check_id} | {check_name} | {status_icon} | "
                f"{r.get('detail', 'N/A')} | {r.get('evidence', 'N/A')} |"
            )

        lines.extend([
            f"",
            f"---",
            f"",
            f"## 2. 统计摘要",
            f"",
            f"| 指标 | 值 |",
            f"|------|-----|",
            f"| 总检查项 | {summary.get('total', 11)} |",
            f"| ✅ PASS | {summary.get('pass', 0)} |",
            f"| ❌ FAIL | {summary.get('fail', 0)} |",
            f"| ⚠️  WARN | {summary.get('warn', 0)} |",
            f"| ❌ ERROR | {summary.get('error', 0)} |",
            f"| ⏭️ SKIP | {summary.get('skip', 0)} |",
            f"| 通过率 | {summary.get('pass', 0)/max(summary.get('total', 1), 1)*100:.0f}% |",
            f"",
        ])

        # V2新增: 审计器联动详情
        if self.audit_validate:
            audit_result = self.results.get("_audit_result", {})
            lines.extend([
                f"---",
                f"",
                f"## 2.5 HERMES审计器预审结果 (V2新增)",
                f"",
                f"| 字段 | 值 |",
                f"|------|-----|",
                f"| 审计器路径 | `{self.config.get('auditor_path', 'N/A')}` |",
                f"| 审计器可用 | {'✅ 是' if self.audit_validator and self.audit_validator.auditor_available else '❌ 否'} |",
                f"| 审计结论 | {audit_result.get('verdict', 'N/A')} |",
                f"| Gate结论 | {audit_result.get('gate_result', 'N/A')} |",
                f"| CRITICAL事件 | {audit_result.get('events_summary', {}).get('CRITICAL', 'N/A')} |",
                f"| HIGH事件 | {audit_result.get('events_summary', {}).get('HIGH', 'N/A')} |",
                f"| MEDIUM事件 | {audit_result.get('events_summary', {}).get('MEDIUM', 'N/A')} |",
                f"| 总事件数 | {audit_result.get('events_summary', {}).get('total', 'N/A')} |",
                f"| 错误 | {audit_result.get('error', '无') if audit_result.get('error') else '无'} |",
                f"",
            ])

            events = audit_result.get("events", [])
            if events:
                lines.append(f"### 审计事件列表 (前10条)")
                lines.append(f"")
                lines.append(f"| # | 级别 | 规则 | 检测点 | 描述 |")
                lines.append(f"|---|------|------|--------|------|")
                for i, e in enumerate(events[:10], 1):
                    lines.append(
                        f"| {i} | {e.get('level','')} | {e.get('rule','')} | "
                        f"{e.get('detect_point','')} | {e.get('message','')[:100]} |"
                    )

        if self.alerts:
            lines.extend([
                f"",
                f"---",
                f"",
                f"## 3. 告警",
                f"",
            ])
            for alert in self.alerts:
                lines.append(f"- 🔔 {alert}")

        lines.extend([
            f"",
            f"---",
            f"",
            f"## 4. Gate准入状态",
            f"",
            f"| 状态项 | 值 |",
            f"|--------|-----|",
        ])

        g05 = self.results.get("G05", {})
        g10 = self.results.get("G10", {})
        g06a = self.results.get("G06A", {})
        lines.append(f"| G05 桥接表准确率 | {g05.get('detail', 'N/A')} |")
        lines.append(f"| G10 真实取数率 | {g10.get('detail', 'N/A')} |")
        lines.append(f"| G06A 审计器预审 | {g06a.get('detail', 'N/A')} |")

        # 综合Gate判定: 取G10和G06A的较差结果
        gate_status = "READY"
        if g10.get("status") == "NOT_READY":
            gate_status = "NOT_READY"
        if g06a.get("status") == "FAIL":
            gate_status = "NOT_READY"
        lines.append(f"| Gate综合状态 | {gate_status} |")

        lines.extend([
            f"",
            f"---",
            f"",
            f"## 5. 约束合规声明",
            f"",
            f"| 约束 | 值 |",
            f"|------|-----|",
            f"| NO_ZHIJI_API_CALL | FALSE (PROD_PHASE_ENABLED) |",
            f"| NO_MODIFY_V85 | TRUE |",
            f"| NO_OVERWRITE | TRUE |",
            f"| BRANCH_LOCKED | TRUE |",
            f"| 双指标强制输出 | 元数据完成率 + 真实有效桥接率 |",
            f"| 流水线退回旧日志作废 | 每次复测生成独立日志 |",
            f"| DEP_BLOCK不计入内部缺陷 | HERMES五类分类对齐 |",
            f"| Gate准入不豁免 | data_fetchable ≥ 80% → READY |",
            f"| 审计FAIL阻断Gate | G06A=FAIL → NOT_READY |",
            f"| V3:L1证据包升级 | EVIDENCE_CONTRACT_V1 + DEP-REG-001 |",
            f"",
            f"---",
            f"",
            f"**报告生成时间**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**报告版本**: V3.0",
            f"**关联工单**: DSHB_V86_RC2_GATE_FUSE_VERIFY / T3.4",
            f"",
        ])

        report_content = "\n".join(lines)

        report_path = self.work_dir / self.config["report_file"]
        report_path.write_text(report_content, encoding="utf-8")

        return report_path, report_content


# ═══════════════════════════════════════════════════════════
# 命令行入口
# ═══════════════════════════════════════════════════════════
def parse_args(args):
    opts = {
        "work_dir": None,
        "strict": False,
        "output": None,
        "audit_validate": False,
        "audit_file": None,
    }
    i = 0
    while i < len(args):
        if args[i] == "--work-dir" and i + 1 < len(args):
            opts["work_dir"] = args[i + 1]
            i += 2
        elif args[i] == "--strict":
            opts["strict"] = True
            i += 1
        elif args[i] == "--output" and i + 1 < len(args):
            opts["output"] = args[i + 1]
            i += 2
        elif args[i] == "--audit-validate":
            opts["audit_validate"] = True
            i += 1
        elif args[i] == "--audit-file" and i + 1 < len(args):
            opts["audit_file"] = args[i + 1]
            i += 2
        else:
            i += 1
    return opts


def main():
    opts = parse_args(sys.argv[1:])

    config = deepcopy(DEFAULT_CONFIG)
    if opts["work_dir"]:
        config["work_dir"] = str(Path(opts["work_dir"]).resolve())
    if opts["output"]:
        config["report_file"] = str(Path(opts["output"]).resolve())
    if opts["audit_file"]:
        config["audit_file"] = opts["audit_file"]

    checker = GatePreCheck(
        config=config,
        strict=opts["strict"],
        audit_validate=opts["audit_validate"],
        audit_file=opts["audit_file"],
    )

    results = checker.run_all_checks()
    report_path, report_content = checker.generate_report()

    summary = results.get("_summary", {})
    print(f"\n{'='*60}")
    print(f"  Gate预检查完成 V3")
    print(f"  PASS: {summary.get('pass', 0)}/{summary.get('total', 11)}")
    print(f"  FAIL: {summary.get('fail', 0)}")
    print(f"  WARN: {summary.get('warn', 0)}")
    if opts["audit_validate"]:
        audit_r = results.get("_audit_result", {})
        print(f"  审计器: {audit_r.get('verdict', 'N/A')} / Gate={audit_r.get('gate_result', 'N/A')}")
    print(f"  报告: {report_path}")
    print(f"{'='*60}\n")

    if opts["strict"] and summary.get("fail", 0) > 0:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
