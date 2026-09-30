#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ths_render_prep_script.py — 同花顺批量渲染任务编排脚本

工单: HERMES_THS_RENDER_PREP_AND_PORTAL_FINAL_INTEGRATE
任务: T2.4 渲染前置检查脚本（仅任务编排，不执行zhiji时序拉取）

功能:
  1) 读取 chart_risk_bound_all.json 和 ths_render_task_list.json
  2) 按风险等级分组：可直接渲染 / 人工复核后渲染 / 阻塞不渲染
  3) 生成完整渲染任务清单，附带图表元数据、指标风险标签、失败处理策略
  4) 前置检查：验证渲染前置条件（不调用zhiji接口，不拉时序数据）

约束(T4):
  - 仅任务编排，不执行实际渲染
  - 不调用 zhiji 接口，不拉时序数据
  - 不修改原始 ths_adapted_all.json、PDF 原始模板
  - indicators_v1.json、tree_config.json 保持只读不改动

用法:
  python3 ths_render_prep_script.py --bound chart_risk_bound_all.json --tasks ths_render_task_list.json --out .
  python3 ths_render_prep_script.py --check  # 仅前置检查
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class RenderTaskOrchestrator:
    """渲染任务编排器"""

    # 渲染分级策略
    RENDER_STRATEGIES = {
        "can_render": {
            "label": "可直接渲染",
            "color": "green",
            "action": "立即执行渲染",
            "failure_strategy": "重试3次, 间隔5秒, 失败后标记为RENDER_FAILED",
        },
        "review_first": {
            "label": "人工复核后渲染",
            "color": "yellow",
            "action": "等待人工复核确认后执行渲染",
            "failure_strategy": "记录复核结论, 人工决定是否重试",
        },
        "blocked": {
            "label": "阻塞不渲染",
            "color": "red",
            "action": "禁止渲染, 需修复风险后重新评估",
            "failure_strategy": "不执行渲染, 记录阻塞原因",
        },
    }

    def __init__(self, bound_path: str, task_list_path: str):
        with open(bound_path, encoding="utf-8") as f:
            self.bound = json.load(f)
        with open(task_list_path, encoding="utf-8") as f:
            self.task_list = json.load(f)

        # 构建 template_id → bound entry 索引
        self.bound_index = {}
        for t in self.bound.get("templates", []):
            self.bound_index[t["template_id"]] = t

    def preflight_check(self) -> Dict[str, Any]:
        """渲染前置检查（不调用zhiji接口）"""
        checks = {
            "input_files": {},
            "template_counts": {},
            "risk_distribution": {},
            "blocking_issues": [],
            "ready_to_render": False,
        }

        # 1. 输入文件检查
        checks["input_files"]["chart_risk_bound_all"] = {
            "exists": len(self.bound.get("templates", [])) > 0,
            "template_count": len(self.bound.get("templates", [])),
        }
        checks["input_files"]["ths_render_task_list"] = {
            "exists": len(self.task_list.get("groups", {}).get("can_render", [])) >= 0,
            "summary": self.task_list.get("summary", {}),
        }

        # 2. 模板计数
        stats = self.bound.get("statistics", {})
        checks["template_counts"] = {
            "pdf_total": stats.get("pdf_total", 0),
            "ths_total": stats.get("ths_total", 0),
            "grand_total": stats.get("total_templates", 0),
        }

        # 3. 风险分布
        checks["risk_distribution"] = {
            "P0": stats.get("total_p0", 0),
            "P1": stats.get("total_p1", 0),
            "with_risk": stats.get("total_with_risk", 0),
            "by_variety": self.bound.get("variety_distribution", {}),
        }

        # 4. 阻塞项
        blocked = self.task_list.get("groups", {}).get("blocked", [])
        for b in blocked:
            checks["blocking_issues"].append({
                "template_id": b["template_id"],
                "source": b["source"],
                "risk_level": b["risk_level"],
                "strategy": b["strategy"],
            })

        # 5. 渲染就绪判定
        summary = self.task_list.get("summary", {})
        checks["ready_to_render"] = summary.get("can_render", 0) > 0
        checks["render_queue_size"] = summary.get("can_render", 0)
        checks["review_queue_size"] = summary.get("review_first", 0)
        checks["blocked_count"] = summary.get("blocked", 0)

        return checks

    def generate_task_manifest(self) -> Dict[str, Any]:
        """生成完整渲染任务清单（含元数据、风险标签、失败处理策略）"""
        manifest = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "task_id": "HERMES_THS_RENDER_PREP_AND_PORTAL_FINAL_INTEGRATE",
            "description": "同花顺批量渲染任务清单 — 按风险等级分组，附带图表元数据、指标风险标签、失败处理策略",
            "constraint": "仅任务编排，不执行zhiji时序拉取，不调用zhiji接口",
            "strategies": self.RENDER_STRATEGIES,
            "summary": self.task_list.get("summary", {}),
            "render_groups": {},
        }

        for group_key, strategy in self.RENDER_STRATEGIES.items():
            group_tasks = self.task_list.get("groups", {}).get(group_key, [])
            enriched_tasks = []
            for t in group_tasks:
                # 关联 bound 数据
                bound_entry = self.bound_index.get(t["template_id"], {})

                task = {
                    "task_id": f"RENDER-{t['source']}-{t['template_id']}",
                    "source": t["source"],
                    "template_id": t["template_id"],
                    "variety": t.get("variety", ""),
                    "risk_level": t["risk_level"],
                    "risk_tags": {
                        "p0_count": t.get("p0", 0),
                        "p1_count": t.get("p1", 0),
                        "blocked_count": t.get("blocked", 0),
                    },
                    "render_strategy": strategy["action"],
                    "failure_strategy": strategy["failure_strategy"],
                    "status": "PENDING",
                    "metadata": {
                        "series_count": bound_entry.get("series_count", 0),
                        "chart_type": bound_entry.get("chart_type", ""),
                        "title": bound_entry.get("title", ""),
                    },
                    "preflight": {
                        "zhiji_data_required": True,  # 渲染时需要zhiji时序数据（但本脚本不拉取）
                        "zhiji_ids_status": self._check_zhiji_ids_status(bound_entry),
                        "render_prerequisites": [
                            "zhiji series data fetched",
                            "chart template validated",
                            "semantic check passed",
                        ],
                    },
                }
                enriched_tasks.append(task)

            manifest["render_groups"][group_key] = {
                "label": strategy["label"],
                "color": strategy["color"],
                "task_count": len(enriched_tasks),
                "tasks": enriched_tasks,
            }

        return manifest

    def _check_zhiji_ids_status(self, bound_entry: Dict) -> Dict:
        """检查模板内 zhiji_id 状态（静态检查，不调用API）"""
        series_risks = bound_entry.get("series_risks", [])
        total = len(series_risks)
        valid = sum(1 for s in series_risks if s.get("zhiji_id") and str(s.get("zhiji_id", "")).startswith("ID"))
        missing = sum(1 for s in series_risks if not s.get("zhiji_id"))
        invalid = sum(1 for s in series_risks if s.get("zhiji_id") and not str(s.get("zhiji_id", "")).startswith("ID"))
        return {
            "total_series": total,
            "valid_ids": valid,
            "missing_ids": missing,
            "invalid_ids": invalid,
        }

    def generate_csv_export(self) -> str:
        """生成可导出的 CSV 任务清单摘要"""
        lines = ["task_id,source,template_id,variety,risk_level,p0,p1,blocked,strategy,status"]
        for group_key in self.RENDER_STRATEGIES:
            group_tasks = self.task_list.get("groups", {}).get(group_key, [])
            strategy = self.RENDER_STRATEGIES[group_key]
            for t in group_tasks:
                lines.append(
                    f"RENDER-{t['source']}-{t['template_id']},"
                    f"{t['source']},{t['template_id']},{t.get('variety','')},"
                    f"{t['risk_level']},{t.get('p0',0)},{t.get('p1',0)},{t.get('blocked',0)},"
                    f"\"{strategy['action']}\",PENDING"
                )
        return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="同花顺批量渲染任务编排")
    parser.add_argument("--bound", required=True, help="chart_risk_bound_all.json 路径")
    parser.add_argument("--tasks", required=True, help="ths_render_task_list.json 路径")
    parser.add_argument("--out", default=".", help="输出目录")
    parser.add_argument("--check", action="store_true", help="仅前置检查")
    args = parser.parse_args()

    orch = RenderTaskOrchestrator(args.bound, args.tasks)

    print("=== 渲染前置检查 ===")
    preflight = orch.preflight_check()
    print(f"  模板总数: {preflight['template_counts']['grand_total']} (PDF:{preflight['template_counts']['pdf_total']} THS:{preflight['template_counts']['ths_total']})")
    print(f"  可直接渲染: {preflight['render_queue_size']}")
    print(f"  人工复核: {preflight['review_queue_size']}")
    print(f"  阻塞: {preflight['blocked_count']}")
    print(f"  渲染就绪: {'✅' if preflight['ready_to_render'] else '❌'}")
    if preflight["blocking_issues"]:
        print(f"  阻塞项明细 (前5):")
        for b in preflight["blocking_issues"][:5]:
            print(f"    {b['template_id']} [{b['source']}] {b['strategy']}")

    if args.check:
        return

    # 生成完整任务清单
    manifest = orch.generate_task_manifest()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = out_dir / "ths_render_task_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 渲染任务清单: {manifest_path} ({os.path.getsize(manifest_path)} bytes)")

    csv_path = out_dir / "ths_render_task_summary.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(orch.generate_csv_export())
    print(f"✅ CSV摘要: {csv_path}")


if __name__ == "__main__":
    main()
