#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
updated_auto_semantic_check.py — V85 语义互斥词黑名单自动校验模块 (v2.0)

工单: HERMES_THS_RENDER_PREP_AND_PORTAL_FINAL_INTEGRATE
升级自: auto_semantic_check.py (v1.0, HERMES_V85_PREP_FOR_THS_AND_AUTO_CHECK_ENHANCE)

v2.0 升级点:
  1) 接入统一风险库 (semantic_blacklist_hermes_fixed.json v2.0-fixed)
     - 黑名单内联为 fallback，支持外部路径覆盖
     - 新增 BL-021 修复 (G08 移除"均价"/"现货价"误报)
  2) 按指标维度标记风险:
     - P0: 语义互斥对立 → 拦截渲染
     - P1: 近似口径不等价 → 人工复核
     - BLOCKED: INVALID/MISSING zhiji_id → 阻塞
     - INFO: 关键词命中但无冲突 / THS待匹配
     - CLEAN: 无风险
  3) 新增 check_template_batch(): 批量校验模板列表，输出分级渲染任务清单
  4) 新增 check_ths_internal(): THS模板内系列间互斥检测
  5) 新增 generate_render_task_list(): 生成分级渲染任务编排JSON
  6) 内联已知P0案例 (known_p0_cases_v85) 做回归测试

约束(T4): 纯静态文本校验, 不调用 zhiji 接口, 不拉时序数据, 不修改原始模板。

用法:
  # 单对校验
  python3 updated_auto_semantic_check.py --pair "新能源乘用车 产量" "SMM: 国产乘用车销量-新能源汽车: 周度"

  # 批量校验 PDF 模板
  python3 updated_auto_semantic_check.py --pdf pdf_web_chart_template_hermes_ready.json

  # 批量校验 THS 适配模板
  python3 updated_auto_semantic_check.py --ths ths_adapted_all.json

  # 全量校验 + 生成分级渲染任务清单
  python3 updated_auto_semantic_check.py --full --pdf <path> --ths <path> --out output/

  # P0 回归测试
  python3 updated_auto_semantic_check.py --verify-cases

  # 作为模块导入
  from updated_auto_semantic_check import UnifiedSemanticChecker
  checker = UnifiedSemanticChecker()
  result = checker.check_pair("系列名A", "系列名B")
"""

import json
import re
import os
import sys
import csv
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

# === 统一风险库路径 ===
DEFAULT_BLACKLIST_PATH = Path(__file__).parent / "semantic_blacklist_hermes_fixed.json"
# fallback: 上一版路径
LEGACY_BLACKLIST_PATH = Path(__file__).parent.parent / "prep_for_ths_and_auto_check_enhance" / "semantic_blacklist_hermes.json"

# === 内联风险库 (fallback, 当外部文件不存在时使用) ===
INLINE_BLACKLIST = {
    "version": "2.0-fixed-inline",
    "conflict_groups": [
        {"group_id": "G01_output_vs_consumption", "severity": "P0",
         "label": "产量 ↔ 消费量/销量（供给端↔需求端，完全相反口径）",
         "keywords": ["产量", "消费量", "消费", "销量", "表观消费", "消费量指数"]},
        {"group_id": "G02_onsite_vs_offsite_inventory", "severity": "P0",
         "label": "场内库存 ↔ 场外/非仓单库存（仓库归属对立）",
         "keywords": ["场内库存", "场内", "仓单库存", "非仓单", "非仓单库存", "场外库存", "场外", "仓外"]},
        {"group_id": "G03_inventory_vs_transit", "severity": "P0",
         "label": "库存 ↔ 在途/堆场（存量↔流量，性质对立）",
         "keywords": ["库存", "在途", "在途库存", "堆场", "堆场站台", "站台堆积", "积压"]},
        {"group_id": "G04_fitted_vs_official", "severity": "P1",
         "label": "拟合/估算 ↔ 官方指数（估算值↔官方统计，精度不等价）",
         "keywords": ["拟合", "拟合值", "估算", "估算值", "消费指数", "指数"]},
        {"group_id": "G05_nickel_discount_vs_conversion", "severity": "P1",
         "label": "折镍价 ↔ 折合价（原料折价↔成品折算，方向不同）",
         "keywords": ["折镍价", "折合", "折价", "废不锈钢折价", "折合镍铁"]},
        {"group_id": "G06_social_vs_warrant_inventory", "severity": "P1",
         "label": "社会库存 ↔ 期货仓单（流通端↔交易所端）",
         "keywords": ["社会库存", "社库", "期货仓单", "仓单", "交易所库存", "交易所仓单"]},
        {"group_id": "G07_utilization_vs_output", "severity": "P1",
         "label": "开工率/产能利用率 ↔ 产量（相对率↔绝对量）",
         "keywords": ["开工率", "开工", "产能利用率", "负荷率"]},
        {"group_id": "G08_price_vs_cost", "severity": "P1",
         "label": "价格 ↔ 成本（收益端↔投入端）",
         "keywords": ["价格", "成本", "完全成本", "加工费"]},
        {"group_id": "G09_export_vs_import", "severity": "P0",
         "label": "出口 ↔ 进口（贸易方向相反）",
         "keywords": ["出口", "进口", "出口量", "进口量", "出口额", "进口额"]},
        {"group_id": "G10_domestic_vs_imported", "severity": "P0",
         "label": "国产 ↔ 进口/海外（来源地相反）",
         "keywords": ["国产", "进口", "海外", "境外", "海外仓"]},
    ],
}


class RiskResult:
    """指标维度风险标记结果"""

    LEVELS = ("CLEAN", "INFO", "P1", "P0", "BLOCKED")

    def __init__(self, risk_level: str = "CLEAN", risk_type: str = "no_risk",
                 severity: Optional[str] = None,
                 group_id: Optional[str] = None, group_label: Optional[str] = None,
                 hit_words_a: Optional[List[str]] = None,
                 hit_words_b: Optional[List[str]] = None,
                 reason: str = "", source: str = ""):
        self.risk_level = risk_level
        self.risk_type = risk_type
        self.severity = severity or risk_level
        self.group_id = group_id
        self.group_label = group_label
        self.hit_words_a = hit_words_a or []
        self.hit_words_b = hit_words_b or []
        self.reason = reason
        self.source = source

    @property
    def is_risky(self) -> bool:
        return self.risk_level in ("P0", "P1", "BLOCKED")

    @property
    def blocks_render(self) -> bool:
        return self.risk_level in ("P0", "BLOCKED")

    def __bool__(self):
        return self.is_risky

    def __repr__(self):
        if not self.is_risky:
            return f"<{self.risk_level}>"
        return (f"<{self.risk_level} {self.risk_type} {self.group_id or ''} "
                f"A={self.hit_words_a} B={self.hit_words_b} {self.reason}>")

    def to_dict(self) -> Dict[str, Any]:
        return {
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


class UnifiedSemanticChecker:
    """统一语义校验器 v2.0 — 接入统一风险库"""

    def __init__(self, blacklist_path: Optional[str] = None):
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

    @property
    def blacklist_version(self) -> str:
        return self.blacklist.get("version", "unknown")

    @property
    def blacklist_source(self) -> str:
        return self._blacklist_source

    # --- 基础检测 ---

    def _find_hits(self, text: str) -> List[str]:
        if not text:
            return []
        hits = []
        for kw in sorted(self.keyword_index.keys(), key=len, reverse=True):
            if kw in text:
                hits.append(kw)
        return hits

    def _is_pure_inclusion(self, a: str, b: str) -> bool:
        a2 = a.replace("：", ":").replace(" ", "").strip()
        b2 = b.replace("：", ":").replace(" ", "").strip()
        return a2 in b2 or b2 in a2

    def _is_key_embedding_anomaly(self, a: str, b: str) -> bool:
        a2 = a.replace("：", ":").replace(" ", "").strip()
        b2 = b.replace("：", ":").replace(" ", "").strip()
        if not a2 or not b2:
            return False
        shorter, longer = (a2, b2) if len(a2) <= len(b2) else (b2, a2)
        if shorter not in longer:
            return False
        return len(shorter) > 0.6 * len(longer)

    def check_pair(self, name_a: str, name_b: str,
                   context: Optional[str] = None) -> RiskResult:
        """校验两个指标名是否语义冲突，返回 RiskResult。"""
        if not name_a or not name_b:
            return RiskResult("CLEAN", "no_risk", reason="输入为空, 跳过")

        hits_a = self._find_hits(name_a)
        hits_b = self._find_hits(name_b)

        if not hits_a or not hits_b:
            return RiskResult("CLEAN", "no_risk",
                              hit_words_a=hits_a, hit_words_b=hits_b,
                              reason="无黑名单关键词命中")

        groups_a: Dict[str, set] = {}
        groups_b: Dict[str, set] = {}
        for kw in hits_a:
            gid = self.keyword_index[kw]["group_id"]
            groups_a.setdefault(gid, set()).add(kw)
        for kw in hits_b:
            gid = self.keyword_index[kw]["group_id"]
            groups_b.setdefault(gid, set()).add(kw)

        common = set(groups_a.keys()) & set(groups_b.keys())
        if not common:
            return RiskResult("INFO", "keyword_hit_no_conflict",
                              hit_words_a=hits_a, hit_words_b=hits_b,
                              reason=f"A命中组{list(groups_a.keys())} B命中组{list(groups_b.keys())} 无交集")

        if self._is_pure_inclusion(name_a, name_b):
            if self._is_key_embedding_anomaly(name_a, name_b):
                gid_hint = next(iter(groups_a.keys()))
                info = self.keyword_index[next(iter(self._find_hits(name_a)))]
                return RiskResult("P1", "key_embedding_anomaly",
                                  severity="P1", group_id=info["group_id"],
                                  group_label=info["label"],
                                  hit_words_a=hits_a, hit_words_b=hits_b,
                                  reason="键匹配异常: 系列名是zhiji名的子串(重复嵌入)")
            return RiskResult("INFO", "inclusion_whitelist",
                              hit_words_a=hits_a, hit_words_b=hits_b,
                              reason="白名单: 纯包含关系(同名同义)")

        for gid in common:
            kws_a = groups_a[gid]
            kws_b = groups_b[gid]
            info = self.keyword_index[next(iter(kws_a))]
            if kws_a.isdisjoint(kws_b):
                return RiskResult(info["severity"], "semantic_conflict",
                                  severity=info["severity"], group_id=gid,
                                  group_label=info["label"],
                                  hit_words_a=sorted(kws_a), hit_words_b=sorted(kws_b),
                                  reason=f"语义互斥: A={sorted(kws_a)} B={sorted(kws_b)} 同属{gid}但对立")
            else:
                only_a = kws_a - kws_b
                only_b = kws_b - kws_a
                if only_a and only_b:
                    return RiskResult(info["severity"], "semantic_conflict",
                                      severity=info["severity"], group_id=gid,
                                      group_label=info["label"],
                                      hit_words_a=sorted(kws_a), hit_words_b=sorted(kws_b),
                                      reason=f"语义对立: A独有{sorted(only_a)} vs B独有{sorted(only_b)}")
        return RiskResult("INFO", "same_group_same_root",
                          hit_words_a=hits_a, hit_words_b=hits_b,
                          reason="共同组内同类词根, 非对立")

    # --- 批量校验 ---

    def check_pdf_template(self, template: Dict) -> Dict[str, Any]:
        """校验单个 PDF 模板，返回带风险标签的模板对象。"""
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

            # INVALID/MISSING
            if verify_status in ("INVALID", "MISSING") or (zhiji_id and not zhiji_id.startswith("ID")):
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
            "template_id": tid,
            "variety": template.get("variety", ""),
            "chart_type": template.get("chart_type", ""),
            "series_count": len(series_list),
            "template_risk_level": level,
            "p0_count": p0, "p1_count": p1, "blocked_count": blocked,
            "series_with_risk": results,
        }

    def check_ths_template(self, template: Dict) -> Dict[str, Any]:
        """校验单个 THS 适配模板，返回带风险标签的模板对象。"""
        tid = template.get("chart_id", "")
        series_list = template.get("series", [])
        results = []
        for i, s in enumerate(series_list):
            name_a = s.get("name", "") or s.get("original_name", "")
            name_b = s.get("note", "") or ""
            zhiji_id = s.get("zhiji_id")
            status = s.get("status", "")

            entry = dict(s)
            entry["series_index"] = i

            if not zhiji_id:
                r = RiskResult("INFO", "ths_pending_match",
                               reason="THS模板无zhiji_id，需后续匹配")
            else:
                r = self.check_pair(name_a, name_b, context=f"{tid}/series[{i}]")

            entry["semantic_check"] = r.to_dict()
            results.append(entry)

        # THS 同模板内系列间互斥检测
        internal_conflicts = self.check_ths_internal(series_list)

        p0 = sum(1 for r in results if r["semantic_check"]["risk_level"] == "P0")
        p1 = sum(1 for r in results if r["semantic_check"]["risk_level"] == "P1")
        internal_p0 = sum(1 for c in internal_conflicts if c.get("severity") == "P0")
        internal_p1 = sum(1 for c in internal_conflicts if c.get("severity") == "P1")
        level = "P0" if (p0 + internal_p0) > 0 else ("P1" if (p1 + internal_p1) > 0 else "CLEAN")

        return {
            "template_id": tid,
            "title": template.get("title", ""),
            "variety": template.get("meta", {}).get("variety", "") if isinstance(template.get("meta"), dict) else "",
            "series_count": len(series_list),
            "template_risk_level": level,
            "p0_count": p0, "p1_count": p1,
            "internal_conflicts": internal_conflicts,
            "series_with_risk": results,
        }

    def check_ths_internal(self, series_list: List[Dict]) -> List[Dict]:
        """THS 模板内系列间互斥检测。"""
        conflicts = []
        for i in range(len(series_list)):
            for j in range(i + 1, len(series_list)):
                ni = series_list[i].get("name", "") or series_list[i].get("original_name", "")
                nj = series_list[j].get("name", "") or series_list[j].get("original_name", "")
                r = self.check_pair(ni, nj)
                if r.is_risky:
                    conflicts.append({
                        "series_i": i, "series_j": j,
                        "name_i": ni, "name_j": nj,
                        "severity": r.severity, "group_id": r.group_id,
                        "group_label": r.group_label, "reason": r.reason,
                    })
        return conflicts

    def check_template_batch(self, templates: List[Dict],
                             source: str = "PDF") -> List[Dict[str, Any]]:
        """批量校验模板列表，返回分级结果。"""
        if source == "PDF":
            return [self.check_pdf_template(t) for t in templates]
        elif source == "THS":
            return [self.check_ths_template(t) for t in templates]
        else:
            raise ValueError(f"未知模板来源: {source}")

    def generate_render_task_list(self, pdf_results: List[Dict],
                                  ths_results: List[Dict]) -> Dict[str, Any]:
        """生成分级渲染任务清单。"""
        groups = {
            "can_render": [],      # CLEAN — 可直接渲染
            "review_first": [],    # P1/INFO — 人工复核后渲染
            "blocked": [],         # P0/BLOCKED — 阻塞不渲染
        }

        for r in pdf_results:
            entry = {
                "source": "PDF",
                "template_id": r["template_id"],
                "variety": r["variety"],
                "risk_level": r["template_risk_level"],
                "p0": r["p0_count"], "p1": r["p1_count"], "blocked": r["blocked_count"],
                "strategy": "",
            }
            if r["template_risk_level"] == "P0":
                entry["strategy"] = "阻塞: 存在P0语义冲突或INVALID zhiji_id, 禁止渲染"
                groups["blocked"].append(entry)
            elif r["template_risk_level"] == "P1":
                entry["strategy"] = "人工复核: 存在P1近似口径不等价, 复核后决定是否渲染"
                groups["review_first"].append(entry)
            else:
                entry["strategy"] = "可直接渲染"
                groups["can_render"].append(entry)

        for r in ths_results:
            entry = {
                "source": "THS",
                "template_id": r["template_id"],
                "variety": r["variety"],
                "risk_level": r["template_risk_level"],
                "p0": r["p0_count"], "p1": r["p1_count"],
                "strategy": "",
            }
            if r["template_risk_level"] == "P0":
                entry["strategy"] = "阻塞: 存在P0语义冲突或内部互斥"
                groups["blocked"].append(entry)
            elif r["template_risk_level"] == "P1":
                entry["strategy"] = "人工复核: 存在P1近似口径不等价或内部对立"
                groups["review_first"].append(entry)
            else:
                # THS 模板即使 CLEAN 也需要先匹配 zhiji_id 才能渲染
                entry["strategy"] = "待匹配zhiji_id后渲染 (THS模板无zhiji_id)"
                groups["review_first"].append(entry)

        return {
            "version": "1.0",
            "generated_at": "2026-09-30T16:10:00+08:00",
            "summary": {
                "can_render": len(groups["can_render"]),
                "review_first": len(groups["review_first"]),
                "blocked": len(groups["blocked"]),
                "total": len(groups["can_render"]) + len(groups["review_first"]) + len(groups["blocked"]),
            },
            "groups": groups,
        }

    # --- P0 回归测试 ---

    def verify_known_cases(self) -> Dict[str, Any]:
        """验证能否识别 known_p0_cases_v85。"""
        cases = self.blacklist.get("known_p0_cases_v85", [])
        results = []
        passed = 0
        for c in cases:
            r = self.check_pair(c.get("series", ""), c.get("zhiji_name", ""))
            status = "PASS" if r.is_risky or c.get("group") is None else "FAIL"
            if c.get("group") is None:
                status = "SKIP (INVALID/MISSING)"
            elif r.is_risky:
                passed += 1
                status = f"PASS ({r.severity})"
            results.append({
                "case_id": c.get("case_id"),
                "template": c.get("template"),
                "series": c.get("series", "")[:40],
                "zhiji_name": c.get("zhiji_name", "")[:40],
                "expected_group": c.get("group"),
                "actual": r.to_dict(),
                "status": status,
            })
        total_with_group = sum(1 for c in cases if c.get("group"))
        return {
            "passed": passed,
            "total": total_with_group,
            "pass_rate": f"{passed}/{total_with_group}",
            "details": results,
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="V85 统一语义校验 v2.0")
    parser.add_argument("--pair", nargs=2, help="校验单对指标名 A B")
    parser.add_argument("--pdf", help="PDF 模板 JSON 文件路径")
    parser.add_argument("--ths", help="THS 适配模板 JSON 文件路径")
    parser.add_argument("--full", action="store_true", help="全量校验 + 生成分级渲染任务清单")
    parser.add_argument("--out", default=".", help="输出目录")
    parser.add_argument("--verify-cases", action="store_true", help="P0 回归测试")
    parser.add_argument("--blacklist", help="自定义黑名单路径")
    args = parser.parse_args()

    checker = UnifiedSemanticChecker(blacklist_path=args.blacklist)
    print(f"黑名单版本: {checker.blacklist_version} (源: {checker.blacklist_source})")
    print(f"冲突组数: {len(checker.groups)}\n")

    if args.verify_cases:
        result = checker.verify_known_cases()
        print(f"=== P0 回归测试: {result['pass_rate']} 通过 ===\n")
        for d in result["details"]:
            print(f"  {d['status']:20s} {d['case_id']:8s} {d['series'][:25]:25s} → {d['zhiji_name'][:25]}")
        return

    if args.pair:
        a, b = args.pair
        r = checker.check_pair(a, b)
        print(f"文本A: {a}")
        print(f"文本B: {b}")
        print(f"结果:  {r}")
        print(f"详情:  {json.dumps(r.to_dict(), ensure_ascii=False, indent=2)}")
        return

    if args.full or args.pdf or args.ths:
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)

        pdf_results = []
        ths_results = []

        if args.pdf:
            with open(args.pdf, encoding="utf-8") as f:
                pdf_data = json.load(f)
            templates = pdf_data.get("templates", pdf_data if isinstance(pdf_data, list) else [])
            print(f"=== PDF 模板校验: {len(templates)} 个 ===")
            pdf_results = checker.check_template_batch(templates, source="PDF")
            p0 = sum(1 for r in pdf_results if r["template_risk_level"] == "P0")
            p1 = sum(1 for r in pdf_results if r["template_risk_level"] == "P1")
            clean = sum(1 for r in pdf_results if r["template_risk_level"] == "CLEAN")
            print(f"  P0: {p0}  P1: {p1}  CLEAN: {clean}\n")

        if args.ths:
            with open(args.ths, encoding="utf-8") as f:
                ths_templates = json.load(f)
            print(f"=== THS 模板校验: {len(ths_templates)} 个 ===")
            ths_results = checker.check_template_batch(ths_templates, source="THS")
            p0 = sum(1 for r in ths_results if r["template_risk_level"] == "P0")
            p1 = sum(1 for r in ths_results if r["template_risk_level"] == "P1")
            clean = sum(1 for r in ths_results if r["template_risk_level"] == "CLEAN")
            print(f"  P0: {p0}  P1: {p1}  CLEAN: {clean}\n")

        if args.full:
            task_list = checker.generate_render_task_list(pdf_results, ths_results)
            task_path = out_dir / "ths_render_task_list.json"
            with open(task_path, "w", encoding="utf-8") as f:
                json.dump(task_list, f, ensure_ascii=False, indent=2)
            print(f"✅ 渲染任务清单: {task_path}")
            print(f"   可直接渲染: {task_list['summary']['can_render']}")
            print(f"   人工复核: {task_list['summary']['review_first']}")
            print(f"   阻塞: {task_list['summary']['blocked']}")

        return


if __name__ == "__main__":
    main()
