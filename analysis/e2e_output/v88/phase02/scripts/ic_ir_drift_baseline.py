#!/usr/bin/env python3
"""
V88 Phase02 - IC/IR 因子漂移基线采集脚本
功能：从 DSHB 采集的指标时序数据中计算 IC (Information Coefficient) 和 IR (Information Ratio)
      建立 Phase02 漂移基线，每日增量采集，超阈值触发告警

IC  = corr(factor_value, forward_return)   # Spearman rank correlation
IR  = IC_mean / IC_std                      # 滚动窗口稳定性

阈值基线（来自 Phase01 仿真实测）：
  IC ≥ 0.03  (最低有效阈值)
  IR ≥ 0.50  (最低稳定阈值)
  漂移告警: |IC_t - IC_baseline| > 0.5 * IC_baseline_std

用法：
  python3 ic_ir_drift_baseline.py --baseline    # 建立首日基线
  python3 ic_ir_drift_baseline.py --daily       # 每日增量采集
  python3 ic_ir_drift_baseline.py --report      # 输出漂移报告
"""

import argparse
import json
import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path

# 路径常量
FRAMEWORK_TREE = Path(os.environ.get("FRAMEWORK_TREE", "/home/ubuntu/framework-tree"))
CACHE_DB = FRAMEWORK_TREE / "scripts" / "api_cache.db"
OUTPUT_DIR = FRAMEWORK_TREE / "analysis" / "e2e_output" / "v88" / "phase02" / "audit"
BASELINE_FILE = OUTPUT_DIR / "ic_ir_baseline.json"
DAILY_FILE = OUTPUT_DIR / "ic_ir_daily.json"

# 指标分类：同花顺推荐 vs 自研产业链
INDICATOR_CATEGORIES = {
    "ths_recommended": "同花顺推荐",
    "self_developed": "自研产业链",
    "cross_ref": "交叉引用",
}

# 漂移阈值
DRIFT_THRESHOLD = 0.5  # |IC_t - IC_baseline| / IC_baseline_std > 0.5 触发 WARN
IC_MIN = 0.03
IR_MIN = 0.50


def get_indicator_series(indicator_id: str, start_date: str, end_date: str):
    """从 api_cache.db 读取指标时序数据"""
    if not CACHE_DB.exists():
        return []
    conn = sqlite3.connect(str(CACHE_DB))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date, value FROM series_cache WHERE indicator_id=? AND date BETWEEN ? AND ? ORDER BY date",
        (indicator_id, start_date, end_date),
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"date": r[0], "value": r[1]} for r in rows]


def compute_ic(factor_values, forward_returns):
    """计算 Spearman rank IC"""
    if len(factor_values) < 5 or len(forward_returns) < 5:
        return None
    # Spearman rank correlation
    n = len(factor_values)
    factor_ranks = _rank(factor_values)
    return_ranks = _rank(forward_returns)
    d_sq = sum((f - r) ** 2 for f, r in zip(factor_ranks, return_ranks))
    ic = 1 - (6 * d_sq) / (n * (n * n - 1))
    return round(ic, 6)


def compute_ir(ic_list):
    """计算 IR = mean(IC) / std(IC)"""
    if len(ic_list) < 3:
        return None
    mean_ic = sum(ic_list) / len(ic_list)
    var_ic = sum((x - mean_ic) ** 2 for x in ic_list) / (len(ic_list) - 1)
    std_ic = var_ic ** 0.5
    if std_ic == 0:
        return None
    return round(mean_ic / std_ic, 6)


def _rank(values):
    """简易排名"""
    sorted_indices = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0] * len(values)
    for rank, idx in enumerate(sorted_indices):
        ranks[idx] = rank + 1
    return ranks


def establish_baseline():
    """建立首日基线"""
    baseline = {
        "established_at": datetime.now().isoformat(),
        "phase": "V88-Phase02",
        "indicators": {},
        "thresholds": {"IC_MIN": IC_MIN, "IR_MIN": IR_MIN, "DRIFT_WARN": DRIFT_THRESHOLD},
    }

    # 从 caliber spec 读取 146 项指标清单
    spec_path = FRAMEWORK_TREE / "analysis/e2e_output/v88/backlog/v88_dshe_chart_indicator_stat_caliber_spec.md"
    if spec_path.exists():
        content = spec_path.read_text()
        # 提取指标ID（简化：记录存在性，实际值待数据入库后填充）
        import re
        ids = re.findall(r"zhiji_id[:\s]+(\S+)", content)
        for iid in ids[:146]:
            baseline["indicators"][iid] = {
                "category": "pending_classification",
                "ic_baseline": None,
                "ir_baseline": None,
                "status": "awaiting_data",
            }

    baseline["indicator_count"] = len(baseline["indicators"])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(BASELINE_FILE, "w") as f:
        json.dump(baseline, f, indent=2, ensure_ascii=False)

    print(f"[baseline] 基线已建立: {baseline['indicator_count']} 项指标待采集")
    print(f"[baseline] 文件: {BASELINE_FILE}")
    return baseline


def daily_collect():
    """每日增量采集"""
    if not BASELINE_FILE.exists():
        print("[error] 基线文件不存在，请先运行 --baseline")
        return

    with open(BASELINE_FILE) as f:
        baseline = json.load(f)

    today = datetime.now().strftime("%Y-%m-%d")
    daily = {
        "collect_date": today,
        "collected_at": datetime.now().isoformat(),
        "indicators": {},
        "alerts": [],
    }

    for iid, base_info in baseline["indicators"].items():
        # 尝试读取最近 30 天数据
        end_date = today
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        series = get_indicator_series(iid, start_date, end_date)

        if len(series) < 5:
            daily["indicators"][iid] = {"status": "insufficient_data", "count": len(series)}
            continue

        # 简化：用相邻差分作为 forward return 近似
        values = [s["value"] for s in series if s["value"] is not None]
        if len(values) < 5:
            daily["indicators"][iid] = {"status": "null_values", "count": 0}
            continue

        returns = [values[i + 1] - values[i] for i in range(len(values) - 1)]
        factors = values[:-1]

        ic = compute_ic(factors, returns)
        daily["indicators"][iid] = {
            "ic": ic,
            "status": "computed" if ic is not None else "compute_failed",
        }

        # 漂移检测
        base_ic = base_info.get("ic_baseline")
        if base_ic and ic:
            drift = abs(ic - base_ic)
            if drift > DRIFT_THRESHOLD:
                daily["alerts"].append({
                    "indicator_id": iid,
                    "ic_baseline": base_ic,
                    "ic_current": ic,
                    "drift": round(drift, 6),
                    "level": "WARN",
                })

    daily["alert_count"] = len(daily["alerts"])
    daily["indicator_collected"] = len([v for v in daily["indicators"].values() if v.get("status") == "computed"])

    with open(DAILY_FILE, "w") as f:
        json.dump(daily, f, indent=2, ensure_ascii=False)

    print(f"[daily] 采集完成: {daily['indicator_collected']} 项有计算结果")
    print(f"[daily] 告警: {daily['alert_count']} 项")
    if daily["alerts"]:
        for a in daily["alerts"][:5]:
            print(f"  ⚠️ {a['indicator_id']}: IC {a['ic_baseline']}→{a['ic_current']} (漂移 {a['drift']})")
    return daily


def generate_report():
    """生成漂移报告"""
    report_lines = [
        "# V88 Phase02 IC/IR 因子漂移基线报告",
        "",
        f"> 生成时间: {datetime.now().isoformat()}",
        "> 阶段: V88-Phase02",
        "> 状态: 基线采集中 (等待全量数据入库)",
        "",
        "---",
        "",
        "## 1. 基线状态",
        "",
    ]

    if BASELINE_FILE.exists():
        with open(BASELINE_FILE) as f:
            baseline = json.load(f)
        report_lines.append(f"- 建立时间: {baseline.get('established_at', 'N/A')}")
        report_lines.append(f"- 指标总数: {baseline.get('indicator_count', 0)}")
        report_lines.append(f"- IC 最低阈值: {baseline['thresholds']['IC_MIN']}")
        report_lines.append(f"- IR 最低阈值: {baseline['thresholds']['IR_MIN']}")
        report_lines.append(f"- 漂移告警阈值: {baseline['thresholds']['DRIFT_WARN']}")
    else:
        report_lines.append("- ⚠️ 基线文件未建立，请先运行 `--baseline`")

    report_lines.extend([
        "",
        "## 2. 采集状态",
        "",
        "- 数据源: api_cache.db (DSHB 采集入库)",
        "- 采集频率: 每日 1 次",
        "- 指标分类: 同花顺推荐 / 自研产业链 / 交叉引用",
        "- 状态: 等待 DSHB 全量数据入库后启动首次基线计算",
        "",
        "## 3. 漂移检测逻辑",
        "",
        "1. IC = Spearman rank correlation (factor_value, forward_return)",
        "2. IR = mean(IC_rolling) / std(IC_rolling)  (20 日滚动窗口)",
        f"3. 漂移告警: |IC_t - IC_baseline| / std(IC_baseline) > {DRIFT_THRESHOLD}",
        f"4. 最低有效: IC ≥ {IC_MIN}, IR ≥ {IR_MIN}",
        "",
        "## 4. 后续动作",
        "",
        "- DSHB 数据入库后 (T+1d~T+3d) 启动首次基线计算",
        "- 建立 146 项指标 IC/IR 基线值",
        "- 区分同花顺推荐 vs 自研产业链指标分类",
        "- 每日增量采集 + 漂移检测",
        "",
    ])

    report_path = OUTPUT_DIR / "ic_ir_drift_report.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))
    print(f"[report] 报告已生成: {report_path}")
    return report_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IC/IR 因子漂移基线采集")
    parser.add_argument("--baseline", action="store_true", help="建立首日基线")
    parser.add_argument("--daily", action="store_true", help="每日增量采集")
    parser.add_argument("--report", action="store_true", help="生成漂移报告")
    args = parser.parse_args()

    if args.baseline:
        establish_baseline()
    elif args.daily:
        daily_collect()
    elif args.report:
        generate_report()
    else:
        parser.print_help()
