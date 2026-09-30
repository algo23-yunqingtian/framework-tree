#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enhanced_auto_semantic_check.py — V85 语义校验器 v3.0（DSHB 动态加载 + 结构化日志）

工单: HERMES_V85_REVIEW_PORTAL_ENHANCE_AND_RENDER_SIMULATION
升级自: updated_auto_semantic_check.py v2.0

v3.0 新增:
  1) DSHB unified_indicator_risk_db.csv 动态加载:
     - 预留加载入口，DSHB CSV 一旦提交可一键替换
     - CSV schema 兼容多种格式（indicator_id/series_name/zhiji_name/risk_level/group_id）
     - 加载后自动刷新全部风险标签，输出 diff 报告
  2) 结构化日志输出:
     - 每次扫描输出 JSONL 结构化日志
     - 记录每条模板校验命中的规则ID、风险描述、系列名、zhiji名
     - 日志可被 render_simulation 复用

继承 v2.0 能力:
  - 统一风险库接入 (semantic_blacklist_hermes_fixed.json v2.0-fixed)
  - 5 级风险标记 (P0/P1/BLOCKED/INFO/CLEAN)
  - THS 内部互斥检测
  - 分级渲染任务生成
  - P0 回归测试 (6/6)

约束(T4):
  - 全程禁止调用 zhiji 接口，不获取真实时序数据
  - 不修改原始 chart_risk_bound_all.json、ths_render_task_list.json 等绑定文件
  - indicators_v1.json、tree_config.json 保持只读
  - 仅新增文件，禁止覆盖仓库历史产物

用法:
  # DSHB CSV 动态加载 + 刷新风险标签
  python3 enhanced_auto_semantic_check.py --load-dshb <unified_indicator_risk_db.csv>

  # 全量扫描 + 结构化日志
  python3 enhanced_auto_semantic_check.py --scan --pdf <path> --ths <path> --log out.jsonl

  # 单对校验
  python3 enhanced_auto_semantic_check.py --pair "新能源乘用车 产量" "SMM: 国产乘用车销量-新能源汽车: 周度"

  # P0 回归测试
  python3 enhanced_auto_semantic_check.py --verify-cases
"""

import json
import re
import os
import sys
import csv
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

# === 路径 ===
HERE = Path(__file__).parent
INT_BASE = HERE / "v85_final_integrate"
BINDING_PATH = INT_BASE / "chart_risk_bound_all.json"
DEFAULT_BLACKLIST_PATH = HERE / "review_package/blacklist_update" / "semantic_blacklist_hermes_fixed.json"
LEGACY_BLACKLIST_PATH = HERE / "prep_for_ths_and_auto_check_enhance" / "semantic_blacklist_hermes.json"

# DSHB CSV 路径（预留，DSHB 提交后填入）
DSHB_CSV_CANDIDATES = [
    HERE / "unified_indicator_risk_db.csv",
    INT_BASE / "unified_indicator_risk_db.csv",
    HERE.parent / "unified_indicator_risk_db.csv",
]

# === 内联风险库 (fallback) ===
INLINE_BLACKLIST = {
    "version": "2.0-fixed-inline",
    "conflict_groups": [
        {"group_id": "G01_output_vs_consumption", "severity": "P0",
         "label": "产量 ↔ 消费量/销量", "keywords": ["产量", "消费量", "消费", "销量", "表观消费", "消费量指数"]},
        {"group_id": "G02_onsite_vs_offsite_inventory", "severity": "P0",
         "label": "场内库存 ↔ 场外/非仓单库存", "keywords": ["场内库存", "场内", "仓单库存", "非仓单", "非仓单库存", "场外库存", "场外", "仓外"]},
        {"group_id": "G03_inventory_vs_transit", "severity": "P0",
         "label": "库存 ↔ 在途/堆场", "keywords": ["库存", "在途", "在途库存", "堆场", "堆场站台", "站台堆积", "积压"]},
        {"group_id": "G04_fitted_vs_official", "severity": "P1",
         "label": "拟合/估算 ↔ 官方指数", "keywords": ["拟合", "拟合值", "估算", "估算值", "消费指数", "指数"]},
        {"group_id": "G05_nickel_discount_vs_conversion", "severity": "P1",
         "label": "折镍价 ↔ 折合价", "keywords": ["折镍价", "折合", "折价", "废不锈钢折价", "折合镍铁"]},
        {"group_id": "G06_social_vs_warrant_inventory", "severity": "P1",
         "label": "社会库存 ↔ 期货仓单", "keywords": ["社会库存", "社库", "期货仓单", "仓单", "交易所库存", "交易所仓单"]},
        {"group_id": "G07_utilization_vs_output", "severity": "P1",
         "label": "开工率 ↔ 产量", "keywords": ["开工率", "开工", "产能利用率", "负荷率"]},
        {"group_id": "G08_price_vs_cost", "severity": "P1",
         "label": "价格 ↔ 成本", "keywords": ["价格", "成本", "完全成本", "加工费"]},
        {"group_id": "G09_export_vs_import", "severity": "P0",
         "label": "出口 ↔ 进口", "keywords": ["出口", "进口", "出口量", "进口量", "出口额", "进口额"]},
        {"group_id": "G10_domestic_vs_imported", "severity": "P0",
         "label": "国产 ↔ 进口/海外", "keywords": ["国产", "进口", "海外", "境外", "海外仓"]},
    ],
}


class RiskResult:
    """指标维度风险标记结果"""

    def __init__(self, risk_level="CLEAN", risk_type="no_risk", severity=None,
                 group_id=None, group_label=None, hit_words_a=None, hit_words_b=None,
                 reason="", source="", rule_id=None):
        self.risk_level = risk_level
        self.risk_type = risk_type
        self.severity = severity or risk_level
        self.group_id = group_id
        self.group_label = group_label
        self.hit_words_a = hit_words_a or []
        self.hit_words_b = hit_words_b or []
        self.reason = reason
        self.source = source
        self.rule_id = rule_id or group_id or ""

    @property
    def is_risky(self):
        return self.risk_level in ("P0", "P1", "BLOCKED")

    @property
    def blocks_render(self):
        return self.risk_level in ("P0", "BLOCKED")

    def __bool__(self):
        return self.is_risky

    def __repr__(self):
        if not self.is_risky:
            return f"<{self.risk_level}>"
        return f"<{self.risk_level} {self.risk_type} {self.group_id or ''} {self.reason}>"

    def to_dict(self):
        d = {
            "risk_level": self.risk_level,
            "risk_type": self.risk_type,
            "severity": self.severity,
            "group_id": self.group_id,
            "group_label": self.group_label,
            "hit_words_a": self.hit_words_a,
            "hit_words_b": self.hit_words_b,
            "reason": self.reason,
            "source": self.source,
        }
        if self.rule_id:
            d["rule_id"] = self.rule_id
        return d


class StructuredLogger:
    """结构化日志输出（JSONL）"""

    def __init__(self, log_path: Optional[str] = None):
        self.log_path = log_path
        self.entries = []
        self._fh = None
        if log_path:
            self._fh = open(log_path, "w", encoding="utf-8")

    def log(self, event_type: str, **fields):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
        }
        entry.update(fields)
        self.entries.append(entry)
        if self._fh:
            self._fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def close(self):
        if self._fh:
            self._fh.close()
            self._fh = None

    @property
    def entry_count(self):
        return len(self.entries)


class EnhancedSemanticChecker:
    """增强语义校验器 v3.0 — DSHB 动态加载 + 结构化日志"""

    def __init__(self, blacklist_path: Optional[str] = None, logger: Optional[StructuredLogger] = None):
        self.logger = logger or StructuredLogger()
        self._load_blacklist(blacklist_path)

    def _load_blacklist(self, blacklist_path: Optional[str] = None):
        """加载语义黑名单（外部文件 → 内联 fallback）"""
        bp = blacklist_path or str(DEFAULT_BLACKLIST_PATH)
        if not os.path.exists(bp):
            bp = str(LEGACY_BLACKLIST_PATH)
        if os.path.exists(bp):
            with open(bp, "r", encoding="utf-8") as f:
                self.blacklist = json.load(f)
            self._blacklist_source = bp
        else:
            self.blacklist = INLINE_BLACKLIST
            self._blacklist_source = "inline-fallback"

        self.groups = self.blacklist["conflict_groups"]
        self.keyword_index = {}
        for g in self.groups:
            for kw in g["keywords"]:
                self.keyword_index[kw] = {
                    "group_id": g["group_id"],
                    "severity": g["severity"],
                    "label": g["label"],
                }
        self.logger.log("BLACKLIST_LOADED",
                         version=self.blacklist.get("version"),
                         source=self._blacklist_source,
                         groups=len(self.groups),
                         keywords=len(self.keyword_index))

    @property
    def blacklist_version(self):
        return self.blacklist.get("version", "unknown")

    @property
    def blacklist_source(self):
        return self._blacklist_source

    # --- DSHB CSV 动态加载 ---

    def load_dshb_csv(self, csv_path: str) -> Dict[str, Any]:
        """
        加载 DSHB unified_indicator_risk_db.csv，替换/补充内部风险库。

        兼容多种 CSV schema（自动识别列名）:
          必需: indicator_id 或 template_id 或 chart_id
          可选: series_name, zhiji_name, risk_level, group_id, severity, label, keywords

        加载后自动刷新全部风险标签，输出 diff 报告。
        不修改原始 chart_risk_bound_all.json（只读）。
        """
        path = Path(csv_path)
        if not path.exists():
            # 尝试候选路径
            found = False
            for cand in DSHB_CSV_CANDIDATES:
                if cand.exists():
                    path = cand
                    found = True
                    break
            if not found:
                self.logger.log("DSHB_CSV_NOT_FOUND", requested=csv_path,
                                 tried=[str(c) for c in DSHB_CSV_CANDIDATES])
                return {"status": "NOT_FOUND", "message": f"DSHB CSV 不存在: {csv_path}"}

        # 解析 CSV
        rows = []
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append({k: (v or "").strip() for k, v in row.items()})

        if not rows:
            return {"status": "EMPTY", "message": "CSV 为空"}

        # 自动识别列名
        headers = list(rows[0].keys())
        id_col = next((c for c in headers if "id" in c.lower() or "template" in c.lower() or "chart" in c.lower()), None)
        series_col = next((c for c in headers if "series" in c.lower() or "name" in c.lower() and "zhiji" not in c.lower()), None)
        zhiji_col = next((c for c in headers if "zhiji" in c.lower()), None)
        level_col = next((c for c in headers if "risk" in c.lower() or "level" in c.lower() or "severity" in c.lower()), None)
        group_col = next((c for c in headers if "group" in c.lower()), None)
        label_col = next((c for c in headers if "label" in c.lower()), None)
        keywords_col = next((c for c in headers if "keyword" in c.lower()), None)

        # 构建 DSHB 风险条目
        dshb_entries = []
        for row in rows:
            entry = {}
            if id_col:
                entry["template_id"] = row.get(id_col, "")
            if series_col:
                entry["series_name"] = row.get(series_col, "")
            if zhiji_col:
                entry["zhiji_name"] = row.get(zhiji_col, "")
            if level_col:
                lvl = row.get(level_col, "").upper()
                entry["risk_level"] = lvl if lvl in ("P0", "P1", "P2", "CLEAN", "INFO", "BLOCKED") else lvl
            if group_col:
                entry["group_id"] = row.get(group_col, "")
            if label_col:
                entry["group_label"] = row.get(label_col, "")
            if keywords_col:
                kws = row.get(keywords_col, "")
                entry["keywords"] = [k.strip() for k in re.split(r"[,;、/]", kws) if k.strip()]
            dshb_entries.append(entry)

        # 构建 DSHB 关键词索引（如果 CSV 提供了 keywords）
        dshb_keyword_index = {}
        for entry in dshb_entries:
            kws = entry.get("keywords", [])
            gid = entry.get("group_id", "")
            level = entry.get("risk_level", "P0")
            label = entry.get("group_label", "")
            for kw in kws:
                dshb_keyword_index[kw] = {
                    "group_id": gid,
                    "severity": level,
                    "label": label,
                }

        # 刷新 keyword_index（DSHB 优先）
        merged_index = dict(self.keyword_index)
        merged_index.update(dshb_keyword_index)  # DSHB 覆盖本地
        self.keyword_index = merged_index

        # 构建 DSHB 已知冲突索引（按 template_id）
        self.dshb_conflict_index = {}
        for entry in dshb_entries:
            tid = entry.get("template_id", "")
            if tid:
                self.dshb_conflict_index[tid] = entry

        # 计算 diff
        prev_groups = len(set(self.keyword_index.keys() & set(merged_index.keys())))
        new_groups = len(merged_index) - prev_groups
        diff_report = {
            "status": "LOADED",
            "csv_path": str(path),
            "csv_md5": hashlib.md5(open(path, "rb").read()).hexdigest(),
            "csv_row_count": len(rows),
            "csv_headers": headers,
            "recognized_columns": {
                "id": id_col, "series": series_col, "zhiji": zhiji_col,
                "level": level_col, "group": group_col, "label": label_col,
                "keywords": keywords_col,
            },
            "dshb_keyword_count": len(dshb_keyword_index),
            "dshb_conflict_count": len(self.dshb_conflict_index),
            "merged_keyword_count": len(merged_index),
            "diff": {
                "keywords_added": len(dshb_keyword_index),
                "keywords_overridden": len(set(dshb_keyword_index.keys()) & set(self.keyword_index.keys()) - set(dshb_keyword_index.keys())),
            },
            "version_after_load": "3.0-dshb-merged",
        }

        self.blacklist["_dshb_merged"] = True
        self.blacklist["_dshb_version"] = "3.0"
        self.logger.log("DSHB_CSV_LOADED",
                         path=str(path),
                         rows=len(rows),
                         keywords=len(dshb_keyword_index),
                         conflicts=len(self.dshb_conflict_index))

        return diff_report

    def refresh_risk_labels(self, binding_path: Optional[str] = None) -> Dict[str, Any]:
        """
        DSHB 加载后刷新全部风险标签。
        读取 chart_risk_bound_all.json（只读），基于新风险库重新扫描，
        输出刷新后的标签 + diff 报告。不修改原始文件。
        """
        bp = binding_path or str(BINDING_PATH)
        if not os.path.exists(bp):
            return {"status": "NOT_FOUND", "message": f"绑定文件不存在: {bp}"}

        with open(bp, "r", encoding="utf-8") as f:
            binding = json.load(f)

        templates = binding.get("templates", [])
        refreshed = []
        diff_count = 0

        for t in templates:
            tid = t["template_id"]
            source = t.get("source", "")
            series_risks = t.get("series_risks", [])

            for sr in series_risks:
                name_a = sr.get("series_name", "")
                name_b = sr.get("zhiji_name", "") or sr.get("zhiji_name", "")
                old_level = sr.get("risk_level", "CLEAN")

                # DSHB 已知冲突优先
                dshb_entry = self.dshb_conflict_index.get(tid)
                if dshb_entry and dshb_entry.get("series_name") == name_a:
                    new_level = dshb_entry.get("risk_level", "P0")
                else:
                    result = self.check_pair(name_a, name_b)
                    new_level = result.risk_level

                if new_level != old_level:
                    diff_count += 1
                    self.logger.log("RISK_LABEL_CHANGED",
                                     template_id=tid, source=source,
                                     series=name_a[:40],
                                     old_level=old_level, new_level=new_level)

            refreshed.append(t)

        self.logger.log("RISK_LABELS_REFRESHED",
                         templates=len(templates),
                         label_changes=diff_count)

        return {
            "status": "REFRESHED",
            "binding_path": bp,
            "templates_scanned": len(templates),
            "label_changes": diff_count,
            "dshb_merged": self.blacklist.get("_dshb_merged", False),
        }

    # --- 基础检测（继承 v2.0） ---

    def _find_hits(self, text: str) -> List[str]:
        if not text:
            return []
        return [kw for kw in sorted(self.keyword_index.keys(), key=len, reverse=True) if kw in text]

    def _is_pure_inclusion(self, a, b):
        a2 = a.replace("：", ":").replace(" ", "").strip()
        b2 = b.replace("：", ":").replace(" ", "").strip()
        return a2 in b2 or b2 in a2

    def _is_key_embedding_anomaly(self, a, b):
        a2 = a.replace("：", ":").replace(" ", "").strip()
        b2 = b.replace("：", ":").replace(" ", "").strip()
        if not a2 or not b2:
            return False
        shorter, longer = (a2, b2) if len(a2) <= len(b2) else (b2, a2)
        if shorter not in longer:
            return False
        return len(shorter) > 0.6 * len(longer)

    def check_pair(self, name_a: str, name_b: str, context: Optional[str] = None) -> RiskResult:
        if not name_a or not name_b:
            return RiskResult("CLEAN", "no_risk", reason="输入为空, 跳过")

        hits_a = self._find_hits(name_a)
        hits_b = self._find_hits(name_b)
        if not hits_a or not hits_b:
            return RiskResult("CLEAN", "no_risk", hit_words_a=hits_a, hit_words_b=hits_b,
                              reason="无黑名单关键词命中")

        groups_a = {}
        groups_b = {}
        for kw in hits_a:
            gid = self.keyword_index[kw]["group_id"]
            groups_a.setdefault(gid, set()).add(kw)
        for kw in hits_b:
            gid = self.keyword_index[kw]["group_id"]
            groups_b.setdefault(gid, set()).add(kw)

        common = set(groups_a.keys()) & set(groups_b.keys())
        if not common:
            r = RiskResult("INFO", "keyword_hit_no_conflict",
                            hit_words_a=hits_a, hit_words_b=hits_b,
                            reason=f"A/B 命中组无交集")
            self._log_check(context, name_a, name_b, r)
            return r

        if self._is_pure_inclusion(name_a, name_b):
            if self._is_key_embedding_anomaly(name_a, name_b):
                gid_hint = next(iter(groups_a.keys()))
                info = self.keyword_index[next(iter(self._find_hits(name_a)))]
                r = RiskResult("P1", "key_embedding_anomaly", severity="P1",
                                group_id=info["group_id"], group_label=info["label"],
                                hit_words_a=hits_a, hit_words_b=hits_b,
                                reason="键匹配异常: 系列名是zhiji名的子串(重复嵌入)")
            else:
                r = RiskResult("INFO", "inclusion_whitelist",
                                hit_words_a=hits_a, hit_words_b=hits_b,
                                reason="白名单: 纯包含关系")
            self._log_check(context, name_a, name_b, r)
            return r

        for gid in common:
            kws_a = groups_a[gid]
            kws_b = groups_b[gid]
            info = self.keyword_index[next(iter(kws_a))]
            if kws_a.isdisjoint(kws_b):
                r = RiskResult(info["severity"], "semantic_conflict", severity=info["severity"],
                                group_id=gid, group_label=info["label"],
                                hit_words_a=sorted(kws_a), hit_words_b=sorted(kws_b),
                                reason=f"语义互斥: A={sorted(kws_a)} B={sorted(kws_b)}")
                self._log_check(context, name_a, name_b, r)
                return r
            else:
                only_a = kws_a - kws_b
                only_b = kws_b - kws_a
                if only_a and only_b:
                    r = RiskResult(info["severity"], "semantic_conflict", severity=info["severity"],
                                    group_id=gid, group_label=info["label"],
                                    hit_words_a=sorted(kws_a), hit_words_b=sorted(kws_b),
                                    reason=f"语义对立: A独有{sorted(only_a)} vs B独有{sorted(only_b)}")
                    self._log_check(context, name_a, name_b, r)
                    return r

        r = RiskResult("INFO", "same_group_same_root",
                        hit_words_a=hits_a, hit_words_b=hits_b,
                        reason="共同组内同类词根")
        self._log_check(context, name_a, name_b, r)
        return r

    def _log_check(self, context, name_a, name_b, result: RiskResult):
        """记录单条校验的结构化日志"""
        self.logger.log("SEMANTIC_CHECK",
                         context=context or "",
                         series_name=name_a[:60],
                         zhiji_name=name_b[:60],
                         rule_id=result.rule_id,
                         group_id=result.group_id,
                         risk_level=result.risk_level,
                         risk_type=result.risk_type,
                         reason=result.reason,
                         hit_words_a=result.hit_words_a,
                         hit_words_b=result.hit_words_b)

    # --- 批量校验（继承 v2.0） ---

    def check_pdf_template(self, template: Dict) -> Dict[str, Any]:
        tid = template.get("template_id", "")
        series_list = template.get("series", [])
        results = []
        for i, s in enumerate(series_list):
            name_a = s.get("name", "")
            name_b = s.get("verify_note", "") or s.get("zhiji_name", "")
            zhiji_id = s.get("zhiji_id", "")
            verify_status = s.get("verify_status", "")
            entry = dict(s)
            entry["series_index"] = i

            if verify_status in ("INVALID", "MISSING") or (zhiji_id and not str(zhiji_id).startswith("ID")):
                r = RiskResult("BLOCKED", "invalid_zhiji_id",
                                reason=f"verify_status={verify_status}, zhiji_id无效或缺失")
            else:
                r = self.check_pair(name_a, name_b, context=f"{tid}/series[{i}]")

            entry["semantic_check"] = r.to_dict()
            if r.blocks_render:
                entry["render_blocked"] = True
                entry["p0_red_tag"] = f"⚠️ {r.risk_level} {' '.join(filter(None, [r.group_label, r.reason]))}"
            results.append(entry)

        p0 = sum(1 for r in results if r["semantic_check"]["risk_level"] == "P0")
        p1 = sum(1 for r in results if r["semantic_check"]["risk_level"] == "P1")
        blocked = sum(1 for r in results if r["semantic_check"]["risk_level"] == "BLOCKED")
        level = "P0" if (p0 + blocked) > 0 else ("P1" if p1 > 0 else "CLEAN")

        return {
            "template_id": tid, "source": "PDF", "variety": template.get("variety", ""),
            "chart_type": template.get("chart_type", ""), "series_count": len(series_list),
            "template_risk_level": level, "p0_count": p0, "p1_count": p1, "blocked_count": blocked,
            "series_with_risk": results,
        }

    def check_ths_template(self, template: Dict) -> Dict[str, Any]:
        tid = template.get("chart_id", "")
        series_list = template.get("series", [])
        results = []
        for i, s in enumerate(series_list):
            name_a = s.get("name", "") or s.get("original_name", "")
            name_b = s.get("note", "") or ""
            zhiji_id = s.get("zhiji_id")
            entry = dict(s)
            entry["series_index"] = i

            if not zhiji_id:
                r = RiskResult("INFO", "ths_pending_match", reason="THS模板无zhiji_id，需后续匹配")
            else:
                r = self.check_pair(name_a, name_b, context=f"{tid}/series[{i}]")
            entry["semantic_check"] = r.to_dict()
            results.append(entry)

        internal_conflicts = self.check_ths_internal(series_list)
        p0 = sum(1 for r in results if r["semantic_check"]["risk_level"] == "P0")
        p1 = sum(1 for r in results if r["semantic_check"]["risk_level"] == "P1")
        internal_p0 = sum(1 for c in internal_conflicts if c.get("severity") == "P0")
        internal_p1 = sum(1 for c in internal_conflicts if c.get("severity") == "P1")
        level = "P0" if (p0 + internal_p0) > 0 else ("P1" if (p1 + internal_p1) > 0 else "CLEAN")

        return {
            "template_id": tid, "source": "THS", "title": template.get("title", ""),
            "variety": template.get("meta", {}).get("variety", "") if isinstance(template.get("meta"), dict) else "",
            "series_count": len(series_list), "template_risk_level": level,
            "p0_count": p0, "p1_count": p1, "internal_conflicts": internal_conflicts,
            "series_with_risk": results,
        }

    def check_ths_internal(self, series_list):
        conflicts = []
        for i in range(len(series_list)):
            for j in range(i + 1, len(series_list)):
                ni = series_list[i].get("name", "") or series_list[i].get("original_name", "")
                nj = series_list[j].get("name", "") or series_list[j].get("original_name", "")
                r = self.check_pair(ni, nj)
                if r.is_risky:
                    conflicts.append({
                        "series_i": i, "series_j": j, "name_i": ni, "name_j": nj,
                        "severity": r.severity, "group_id": r.group_id,
                        "group_label": r.group_label, "reason": r.reason,
                    })
        return conflicts

    def check_template_batch(self, templates, source="PDF"):
        if source == "PDF":
            return [self.check_pdf_template(t) for t in templates]
        elif source == "THS":
            return [self.check_ths_template(t) for t in templates]
        raise ValueError(f"未知模板来源: {source}")

    def verify_known_cases(self):
        cases = self.blacklist.get("known_p0_cases_v85", [])
        results = []
        passed = 0
        for c in cases:
            r = self.check_pair(c.get("series", ""), c.get("zhiji_name", ""))
            if c.get("group") is None:
                status = "SKIP (INVALID/MISSING)"
            elif r.is_risky:
                passed += 1
                status = f"PASS ({r.severity})"
            else:
                status = "FAIL"
            results.append({"case_id": c.get("case_id"), "status": status, "result": r.to_dict()})
        total_with_group = sum(1 for c in cases if c.get("group"))
        self.logger.log("VERIFY_CASES", passed=passed, total=total_with_group)
        return {"passed": passed, "total": total_with_group, "pass_rate": f"{passed}/{total_with_group}", "details": results}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="V85 语义校验器 v3.0 (DSHB动态加载+结构化日志)")
    parser.add_argument("--pair", nargs=2, help="校验单对指标名 A B")
    parser.add_argument("--pdf", help="PDF 模板 JSON")
    parser.add_argument("--ths", help="THS 适配模板 JSON")
    parser.add_argument("--scan", action="store_true", help="全量扫描")
    parser.add_argument("--log", default="", help="结构化日志输出路径 (JSONL)")
    parser.add_argument("--load-dshb", help="加载 DSHB unified_indicator_risk_db.csv")
    parser.add_argument("--refresh", action="store_true", help="DSHB加载后刷新风险标签")
    parser.add_argument("--verify-cases", action="store_true", help="P0 回归测试")
    parser.add_argument("--blacklist", help="自定义黑名单路径")
    args = parser.parse_args()

    log_path = args.log or None
    logger = StructuredLogger(log_path)
    checker = EnhancedSemanticChecker(blacklist_path=args.blacklist, logger=logger)

    print(f"黑名单: {checker.blacklist_version} (源: {checker.blacklist_source})")
    print(f"冲突组: {len(checker.groups)} | 关键词: {len(checker.keyword_index)}\n")

    # DSHB 动态加载
    if args.load_dshb:
        print("=== DSHB CSV 动态加载 ===")
        diff = checker.load_dshb_csv(args.load_dshb)
        print(json.dumps({k: v for k, v in diff.items() if k != "csv_headers"}, ensure_ascii=False, indent=2))

        if args.refresh:
            print("\n=== 刷新风险标签 ===")
            refresh = checker.refresh_risk_labels()
            print(json.dumps(refresh, ensure_ascii=False, indent=2))

    # P0 回归测试
    if args.verify_cases:
        result = checker.verify_known_cases()
        print(f"\n=== P0 回归测试: {result['pass_rate']} 通过 ===")
        for d in result["details"]:
            print(f"  {d['status']:25s} {d.get('case_id','')}")

    # 单对校验
    if args.pair:
        r = checker.check_pair(args.pair[0], args.pair[1])
        print(f"文本A: {args.pair[0]}\n文本B: {args.pair[1]}\n结果: {r}")
        print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2))

    # 全量扫描
    if args.scan:
        results = {"PDF": [], "THS": []}
        if args.pdf:
            with open(args.pdf, encoding="utf-8") as f:
                data = json.load(f)
            templates = data.get("templates", data if isinstance(data, list) else [])
            print(f"=== PDF 扫描: {len(templates)} 模板 ===")
            results["PDF"] = checker.check_template_batch(templates, "PDF")
            print(f"  P0:{sum(1 for r in results['PDF'] if r['template_risk_level']=='P0')} "
                  f"P1:{sum(1 for r in results['PDF'] if r['template_risk_level']=='P1')} "
                  f"CLEAN:{sum(1 for r in results['PDF'] if r['template_risk_level']=='CLEAN')}")

        if args.ths:
            with open(args.ths, encoding="utf-8") as f:
                templates = json.load(f)
            print(f"=== THS 扫描: {len(templates)} 模板 ===")
            results["THS"] = checker.check_template_batch(templates, "THS")
            print(f"  P0:{sum(1 for r in results['THS'] if r['template_risk_level']=='P0')} "
                  f"P1:{sum(1 for r in results['THS'] if r['template_risk_level']=='P1')} "
                  f"CLEAN:{sum(1 for r in results['THS'] if r['template_risk_level']=='CLEAN')}")

    logger.close()
    if log_path:
        print(f"\n✅ 结构化日志: {log_path} ({logger.entry_count} 条)")


if __name__ == "__main__":
    main()
