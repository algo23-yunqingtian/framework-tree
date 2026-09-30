#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_semantic_check.py — V85 语义互斥词黑名单自动校验模块

工单: HERMES_V85_PREP_FOR_THS_AND_AUTO_CHECK_ENHANCE
任务: T2-1 增强自动校验规则

功能:
  1) 加载 semantic_blacklist_hermes.json 语义互斥黑名单
  2) 对任意两个指标名(PDF系列名 vs zhiji实际指标名)做语义冲突判定
  3) 集成到渲染前自动校验: 命中黑名单 → 打 P0 红标, 拦截渲染
  4) 支持批量校验 CSV/JSON 输入

约束(T4): 纯静态文本校验, 不调用 zhiji 接口, 不拉时序数据, 不修改原始模板。

用法:
  # 单对校验
  python3 auto_semantic_check.py --pair "新能源乘用车 产量" "SMM: 国产乘用车销量-新能源汽车: 周度"

  # 批量校验 P0 案例 CSV
  python3 auto_semantic_check.py --batch abnormal_indicator_list.csv

  # 作为模块导入(渲染管线集成)
  from auto_semantic_check import SemanticChecker
  checker = SemanticChecker()
  result = checker.check_pair("系列名A", "系列名B")
  if result.is_conflict and result.severity == "P0":
      mark_p0_red_tag()  # 拦截
"""

import json
import re
import os
import sys
import csv
from pathlib import Path
from typing import Optional, Tuple, List, Dict

BLACKLIST_PATH = Path(__file__).parent / "semantic_blacklist_hermes.json"


class SemanticConflictResult:
    """语义冲突判定结果"""

    def __init__(self, is_conflict: bool, severity: Optional[str] = None,
                 group_id: Optional[str] = None, group_label: Optional[str] = None,
                 hit_words_a: Optional[List[str]] = None,
                 hit_words_b: Optional[List[str]] = None,
                 reason: str = ""):
        self.is_conflict = is_conflict
        self.severity = severity
        self.group_id = group_id
        self.group_label = group_label
        self.hit_words_a = hit_words_a or []
        self.hit_words_b = hit_words_b or []
        self.reason = reason

    def __bool__(self):
        return self.is_conflict

    def __repr__(self):
        if not self.is_conflict:
            return "<NO_CONFLICT>"
        return (f"<CONFLICT {self.severity} {self.group_id} "
                f"A={self.hit_words_a} B={self.hit_words_b} {self.reason}>")

    def to_dict(self):
        return {
            "is_conflict": self.is_conflict,
            "severity": self.severity,
            "group_id": self.group_id,
            "group_label": self.group_label,
            "hit_words_a": self.hit_words_a,
            "hit_words_b": self.hit_words_b,
            "reason": self.reason,
        }


class SemanticChecker:
    """语义互斥校验器"""

    def __init__(self, blacklist_path: Optional[str] = None):
        bp = blacklist_path or str(BLACKLIST_PATH)
        if not os.path.exists(bp):
            raise FileNotFoundError(f"黑名单文件不存在: {bp}")
        with open(bp, "r", encoding="utf-8") as f:
            self.blacklist = json.load(f)

        self.groups = self.blacklist["conflict_groups"]
        # 预处理: 建立 keyword → (group_id, severity, label) 反向索引
        self.keyword_index = {}
        for g in self.groups:
            for kw in g["keywords"]:
                self.keyword_index[kw] = {
                    "group_id": g["group_id"],
                    "severity": g["severity"],
                    "label": g["label"],
                }

    def _find_hits(self, text: str) -> List[str]:
        """在文本中查找所有黑名单关键词命中(长词优先匹配)"""
        if not text:
            return []
        hits = []
        # 长词优先, 避免"库存"抢先于"仓单库存"
        for kw in sorted(self.keyword_index.keys(), key=len, reverse=True):
            if kw in text:
                hits.append(kw)
        return hits

    def _is_pure_inclusion(self, text_a: str, text_b: str) -> bool:
        """判断两文本是否仅前缀/后缀包含关系(白名单: 同名同义包含)"""
        a = text_a.replace("：", ":").replace(" ", "").strip()
        b = text_b.replace("：", ":").replace(" ", "").strip()
        return a in b or b in a

    def _is_key_embedding_anomaly(self, text_a: str, text_b: str) -> bool:
        """
        检测"键匹配异常": 系列名几乎是zhiji名的子串(重复嵌入)。

        这是模糊匹配失效的典型表现——键被错误嵌入到系列名，导致系列名
        包含完整zhiji指标名作为子串，说明匹配过程把指标名拼接进去了。

        判定: 短文本(系列名)长度 > 长文本(zhiji名)的 60%，且为子串关系。
        """
        a = text_a.replace("：", ":").replace(" ", "").strip()
        b = text_b.replace("：", ":").replace(" ", "").strip()
        if not a or not b:
            return False
        shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
        if shorter not in longer:
            return False
        # 子串长度超过长串60% → 高度重复嵌入异常
        return len(shorter) > 0.6 * len(longer)

    def _normalize(self, text: str) -> str:
        """规范化: 统一冒号, 去除频率后缀(日/周/月)和地区后缀用于比对"""
        if not text:
            return ""
        t = text.replace("：", ":").replace(" ", "")
        # 去除频率后缀
        t = re.sub(r"[（(](日|周|月|年)[)）]$", "", t)
        return t

    def check_pair(self, name_a: str, name_b: str,
                   context: Optional[str] = None) -> SemanticConflictResult:
        """
        校验两个指标名是否语义冲突。

        判定逻辑:
          1. 分别提取两文本的黑名单关键词命中
          2. 若两文本命中同一冲突组的不同词根(且非纯包含关系) → 冲突
          3. 同一组内若命中相同词根(如同为"产量") → 不冲突(是同类指标)

        Args:
          name_a: 文本A (如 PDF 系列名)
          name_b: 文本B (如 zhiji 实际指标名)
          context: 上下文(模板ID等, 用于报告)

        Returns:
          SemanticConflictResult
        """
        if not name_a or not name_b:
            return SemanticConflictResult(False, reason="输入为空, 跳过")

        hits_a = self._find_hits(name_a)
        hits_b = self._find_hits(name_b)

        # 无命中 → 无冲突
        if not hits_a or not hits_b:
            return SemanticConflictResult(False, reason="无黑名单关键词命中")

        # 按冲突组分组
        groups_a = {}  # group_id -> set of hit keywords
        groups_b = {}
        for kw in hits_a:
            gid = self.keyword_index[kw]["group_id"]
            groups_a.setdefault(gid, set()).add(kw)
        for kw in hits_b:
            gid = self.keyword_index[kw]["group_id"]
            groups_b.setdefault(gid, set()).add(kw)

        # 找共同冲突组
        common_groups = set(groups_a.keys()) & set(groups_b.keys())
        if not common_groups:
            return SemanticConflictResult(
                False, reason=f"A命中组{list(groups_a.keys())} B命中组{list(groups_b.keys())} 无交集")

        # 白名单: 纯包含关系不触发【常规同名同义】
        if self._is_pure_inclusion(name_a, name_b):
            # 但若为"键匹配异常"——系列名是zhiji名的子串(重复嵌入) → P1告警
            if self._is_key_embedding_anomaly(name_a, name_b):
                # 找最长命中的组作为上下文
                gid_hint = next(iter(groups_a.keys()))
                info = self.keyword_index[next(iter(self._find_hits(name_a)))]
                return SemanticConflictResult(
                    True, severity="P1", group_id=info["group_id"],
                    group_label=info["label"],
                    hit_words_a=hits_a, hit_words_b=hits_b,
                    reason="键匹配异常: 系列名是zhiji实际指标名的子串(重复嵌入), 疑似指标名拼接错误")
            return SemanticConflictResult(
                False, reason="白名单: 两文本为纯包含关系(同名同义)")

        # 对每个共同组检查: 是否命中"不同词根"
        for gid in common_groups:
            kws_a = groups_a[gid]
            kws_b = groups_b[gid]
            info = self.keyword_index[next(iter(kws_a))]

            # 关键判定: A的命中词 与 B的命中词 是否不同(对立)
            if kws_a.isdisjoint(kws_b):
                # 完全不重叠 → 对立冲突 (P0)
                return SemanticConflictResult(
                    True, severity=info["severity"], group_id=gid,
                    group_label=info["label"],
                    hit_words_a=sorted(kws_a), hit_words_b=sorted(kws_b),
                    reason=f"语义互斥: A命中{kws_a} B命中{kws_b}, 同属{gid}但对立")
            else:
                # 有重叠, 但需检查重叠外是否还有对立词根
                only_a = kws_a - kws_b
                only_b = kws_b - kws_a
                if only_a and only_b:
                    return SemanticConflictResult(
                        True, severity=info["severity"], group_id=gid,
                        group_label=info["label"],
                        hit_words_a=sorted(kws_a), hit_words_b=sorted(kws_b),
                        reason=f"语义对立: A独有{only_a} vs B独有{only_b}")
                # 仅单侧独有(另一侧全包含) → 不判定为对立
        return SemanticConflictResult(
            False, reason=f"共同组{list(common_groups)}内为包含/同类词根, 非对立")

    def check_template_series(self, series_list: List[Dict],
                              pdf_name_field: str = "name",
                              zhiji_name_field: str = "note") -> List[Dict]:
        """
        批量校验模板的 series 列表(渲染前钩子)。

        Args:
          series_list: series 对象列表, 每项含 name(PDF系列名) 和 note(zhiji实际指标名)
          pdf_name_field: PDF系列名字段名
          zhiji_name_field: zhiji实际指标名字段名

        Returns:
          每项追加 semantic_check 结果
        """
        results = []
        for i, s in enumerate(series_list):
            name_a = s.get(pdf_name_field) or ""
            name_b = s.get(zhiji_name_field) or ""
            r = self.check_pair(name_a, name_b, context=f"series[{i}]")
            entry = dict(s)
            entry["semantic_check"] = r.to_dict()
            # 渲染管线集成: P0冲突 → 打红标, 禁止渲染
            if r.is_conflict and r.severity == "P0":
                entry["render_blocked"] = True
                entry["p0_red_tag"] = f"⚠️ P0语义冲突 {r.group_label}"
            results.append(entry)
        return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="V85 语义互斥黑名单校验")
    parser.add_argument("--pair", nargs=2, help="校验单对指标名 A B")
    parser.add_argument("--batch", help="批量校验 CSV 文件路径")
    parser.add_argument("--verify-cases", action="store_true",
                        help="自测: 验证能否识别 known_p0_cases_v85")
    args = parser.parse_args()

    checker = SemanticChecker()

    if args.verify_cases:
        cases = checker.blacklist["known_p0_cases_v85"]
        print(f"=== 自测: 验证 {len(cases)} 条 P0 案例 ===\n")
        passed = 0
        for c in cases:
            r = checker.check_pair(c["series"], c["zhiji_name"])
            status = "✅" if (r.is_conflict or c["group"] is None) else "❌"
            # INVALID/MISSING 案例无 group, 期望无冲突但有其他处理
            if c["group"] is None:
                status = "ℹ️ INVALID/MISSING(非语义冲突)"
            elif r.is_conflict:
                passed += 1
                status = f"✅ {r.severity} {r.group_id}"
            else:
                status = f"❌ 未识别冲突 (期望 {c['group']})"
            print(f"  {status}  {c['case_id']} | {c['series'][:25]:25s} → {c['zhiji_name'][:25]:25s}")
        print(f"\n  语义冲突组识别: {passed}/{sum(1 for c in cases if c['group'])} 通过")
        return

    if args.pair:
        a, b = args.pair
        r = checker.check_pair(a, b)
        print(f"文本A: {a}")
        print(f"文本B: {b}")
        print(f"结果:  {r}")
        print(f"详情:  {r.to_dict()}")
        return

    if args.batch:
        print(f"=== 批量校验: {args.batch} ===")
        with open(args.batch, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        # 自动识别列名
        series_col = next((c for c in rows[0].keys() if "系列名" in c or "指标名称" in c), None)
        zhiji_col = next((c for c in rows[0].keys() if "zhiji实际" in c or "实际指标" in c), None)
        if not series_col:
            series_col = rows[0].keys().__iter__().__next__()
        print(f"  系列名列: {series_col}, zhiji名列: {zhiji_col}")
        print(f"  总行数: {len(rows)}")
        p0_count = 0
        for row in rows:
            r = checker.check_pair(row.get(series_col, ""), row.get(zhiji_col or "", ""))
            if r.is_conflict:
                p0_count += 1
                print(f"  {r.severity} {row.get('模板ID', row.get('模板',''))} | "
                      f"{r.group_id} | {row.get(series_col,'')[:20]} → {row.get(zhiji_col or '', '')[:20]}")
        print(f"\n  冲突总数: {p0_count}")


if __name__ == "__main__":
    main()
