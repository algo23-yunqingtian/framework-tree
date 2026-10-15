#!/usr/bin/env python3
"""
V88 Phase03 P1 — T1: 新增70项派生指标抽样回测 & DQA扩展校验

Sample backtest of 70 derived indicators (20% = 14 sampled).
Checks: time series continuity, null rate, extreme value jumps.
Generates extended DQA check rules (EDQA-01 to EDQA-06).

Output: post_fix_watcher/extended_dqa_result.md
"""

import sqlite3
import math
import random
import statistics
import os
from datetime import datetime, timedelta
from collections import OrderedDict

# ── Configuration ──────────────────────────────────────────────────────────
DB_PATH = r'D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v88\phase03\p0\phase03_test.db'
OUTPUT_DIR = r'D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v88\phase03\p1\dshb\post_fix_watcher'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'extended_dqa_result.md')
RANDOM_SEED = 42
SAMPLE_RATIO = 0.20
GAP_THRESHOLD_DAYS = 90
SIGMA_THRESHOLD = 3.0
NULL_THRESHOLD = 0.05      # 5%
STALE_COUNT_THRESHOLD = 3   # 3+ consecutive same values
STALE_STREAK_CHECK = 3

print(f"[T1] Starting V88 Phase03 P1 T1 Sample Backtest")
print(f"[T1] DB: {DB_PATH}")
print(f"[T1] Seed: {RANDOM_SEED}, Sample ratio: {SAMPLE_RATIO}")

# ── Step 1: Query all derived indicators ───────────────────────────────────
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
    SELECT indicator_id, COUNT(*) as cnt, MIN(date), MAX(date)
    FROM series_cache
    WHERE source='derived'
    GROUP BY indicator_id
    ORDER BY indicator_id
""")
all_indicators = cur.fetchall()
print(f"[T1] Found {len(all_indicators)} derived indicators")

# ── Step 2: Sample 20% (14 indicators) ─────────────────────────────────────
random.seed(RANDOM_SEED)
sample_size = int(len(all_indicators) * SAMPLE_RATIO)  # 14
# Use random.sample for reproducibility
sampled = random.sample(all_indicators, sample_size)
sampled.sort(key=lambda x: x[0])  # sort by indicator_id for consistent output
sampled_ids = [r[0] for r in sampled]
print(f"[T1] Sampled {sample_size} indicators: {sampled_ids}")

# ── Step 3: Per-indicator analysis ─────────────────────────────────────────
def parse_date(s):
    """Parse YYYY-MM-DD string to datetime.date."""
    return datetime.strptime(s, '%Y-%m-%d').date()

def analyze_indicator(indicator_id):
    """Full analysis of one indicator: continuity, nulls, extremes, DQA rules."""
    cur.execute("""
        SELECT date, value FROM series_cache
        WHERE source='derived' AND indicator_id=?
        ORDER BY date
    """, (indicator_id,))
    rows = cur.fetchall()

    if not rows:
        return None

    n = len(rows)
    dates = [r[0] for r in rows]
    values = [r[1] for r in rows]

    # Basic stats
    date_min = dates[0]
    date_max = dates[-1]
    date_range_str = f"{date_min} ~ {date_max}"

    # Null rate
    null_count = sum(1 for v in values if v is None)
    null_pct = (null_count / n) * 100 if n > 0 else 0
    non_null_values = [v for v in values if v is not None]

    # Value range stats
    if non_null_values:
        v_min = min(non_null_values)
        v_max = max(non_null_values)
        v_mean = statistics.mean(non_null_values)
        v_std = statistics.pstdev(non_null_values) if len(non_null_values) > 1 else 0.0
    else:
        v_min = v_max = v_mean = v_std = None

    # Time series continuity: count gaps > 90 days
    gaps_gt_90 = 0
    gap_details = []
    for i in range(1, len(dates)):
        d1 = parse_date(dates[i-1])
        d2 = parse_date(dates[i])
        delta_days = (d2 - d1).days
        if delta_days > GAP_THRESHOLD_DAYS:
            gaps_gt_90 += 1
            gap_details.append((dates[i-1], dates[i], delta_days))

    # Extreme value jumps: |delta| > 3*std
    extreme_jumps = 0
    jump_details = []
    if v_std and v_std > 0:
        for i in range(1, len(values)):
            if values[i-1] is not None and values[i] is not None:
                delta = values[i] - values[i-1]
                if abs(delta) > SIGMA_THRESHOLD * v_std:
                    extreme_jumps += 1
                    jump_details.append((dates[i-1], dates[i], values[i-1], values[i], delta))

    # EDQA-01: Stale consecutive points (3+ same values)
    stale_runs = []
    run_start = 0
    run_len = 1
    for i in range(1, len(values)):
        if values[i] is not None and values[i-1] is not None and values[i] == values[i-1]:
            run_len += 1
        else:
            if run_len >= STALE_COUNT_THRESHOLD:
                stale_runs.append((dates[run_start], dates[run_start + run_len - 1], run_len, values[run_start] if run_start < len(values) else None))
            run_start = i - 1
            run_len = 1
    # Check trailing run
    if run_len >= STALE_COUNT_THRESHOLD:
        stale_runs.append((dates[run_start], dates[run_start + run_len - 1], run_len, values[run_start] if run_start < len(values) else None))
    stale_violations = len(stale_runs) > 0

    # EDQA-05: Monotonic series (always increasing or decreasing)
    monotonic = True
    if len(values) < 3:
        monotonic = False
    else:
        for i in range(1, len(values)):
            if values[i] is not None and values[i-1] is not None:
                if values[i] > values[i-1] and values[i] < values[i-1]:
                    monotonic = False
                    break
                # Check direction changes
                if i >= 2 and values[i-2] is not None:
                    d1 = values[i-1] - values[i-2]
                    d2 = values[i] - values[i-1]
                    if d1 > 0 and d2 < 0:
                        monotonic = False
                        break
                    if d1 < 0 and d2 > 0:
                        monotonic = False
                        break
    # More robust: check all diffs are >= 0 or all <= 0
    monotonic_inc = True
    monotonic_dec = True
    for i in range(1, len(values)):
        if values[i] is not None and values[i-1] is not None:
            if values[i] < values[i-1]:
                monotonic_inc = False
            if values[i] > values[i-1]:
                monotonic_dec = False
    monotonic = monotonic_inc or monotonic_dec

    # EDQA-06: Zero-variance series
    zero_variance = (v_std is not None and v_std == 0)

    # ── Verdict logic ──
    issues = []
    if null_pct > NULL_THRESHOLD * 100:
        issues.append(f"EDQA-03 (null_rate={null_pct:.1f}%)")
    if gaps_gt_90 > 0:
        issues.append(f"EDQA-02 (gaps>90d: {gaps_gt_90})")
    if extreme_jumps > 0:
        issues.append(f"EDQA-04 (extreme_jumps: {extreme_jumps})")
    if stale_violations:
        issues.append(f"EDQA-01 (stale_runs: {len(stale_runs)})")
    if monotonic:
        issues.append("EDQA-05 (monotonic)")
    if zero_variance:
        issues.append("EDQA-06 (zero_variance)")

    if not issues:
        verdict = "PASS"
    elif len(issues) <= 2:
        verdict = "WARN"
    else:
        verdict = "FAIL"

    return {
        'indicator_id': indicator_id,
        'rows': n,
        'date_range': date_range_str,
        'date_min': date_min,
        'date_max': date_max,
        'null_count': null_count,
        'null_pct': null_pct,
        'gaps_gt_90': gaps_gt_90,
        'gap_details': gap_details,
        'extreme_jumps': extreme_jumps,
        'jump_details': jump_details,
        'v_min': v_min,
        'v_max': v_max,
        'v_mean': v_mean,
        'v_std': v_std,
        'stale_runs': stale_runs,
        'stale_violations': stale_violations,
        'monotonic': monotonic,
        'zero_variance': zero_variance,
        'issues': issues,
        'verdict': verdict,
    }

print(f"\n[T1] Analyzing {len(sampled)} indicators...")
results = []
for i, (iid, cnt, dmin, dmax) in enumerate(sampled):
    print(f"  [{i+1}/{len(sampled)}] {iid} ({cnt} rows, {dmin}~{dmax})")
    result = analyze_indicator(iid)
    if result:
        results.append(result)
        print(f"       Verdict: {result['verdict']} | nulls={result['null_count']} gaps={result['gaps_gt_90']} jumps={result['extreme_jumps']} monotonic={result['monotonic']} zero_var={result['zero_variance']}")

conn.close()

# ── Step 4: Aggregate DQA rule results ─────────────────────────────────────
rule_results = {
    'EDQA-01': {'name': 'Stale consecutive points (3+ same values)', 'total_violations': 0, 'violators': []},
    'EDQA-02': {'name': 'Time gap > 90 days', 'total_violations': 0, 'violators': []},
    'EDQA-03': {'name': 'Null ratio > 5%', 'total_violations': 0, 'violators': []},
    'EDQA-04': {'name': 'Extreme jump > 3-sigma consecutive', 'total_violations': 0, 'violators': []},
    'EDQA-05': {'name': 'Monotonic series (always inc/dec)', 'total_violations': 0, 'violators': []},
    'EDQA-06': {'name': 'Zero-variance series', 'total_violations': 0, 'violators': []},
}

for r in results:
    iid = r['indicator_id']
    if r['stale_violations']:
        rule_results['EDQA-01']['total_violations'] += 1
        rule_results['EDQA-01']['violators'].append(iid)
    if r['gaps_gt_90'] > 0:
        rule_results['EDQA-02']['total_violations'] += 1
        rule_results['EDQA-02']['violators'].append(iid)
    if r['null_pct'] > NULL_THRESHOLD * 100:
        rule_results['EDQA-03']['total_violations'] += 1
        rule_results['EDQA-03']['violators'].append(iid)
    if r['extreme_jumps'] > 0:
        rule_results['EDQA-04']['total_violations'] += 1
        rule_results['EDQA-04']['violators'].append(iid)
    if r['monotonic']:
        rule_results['EDQA-05']['total_violations'] += 1
        rule_results['EDQA-05']['violators'].append(iid)
    if r['zero_variance']:
        rule_results['EDQA-06']['total_violations'] += 1
        rule_results['EDQA-06']['violators'].append(iid)

# ── Step 5: Generate Markdown report ───────────────────────────────────────
verdict_counts = {'PASS': 0, 'WARN': 0, 'FAIL': 0}
for r in results:
    verdict_counts[r['verdict']] = verdict_counts.get(r['verdict'], 0) + 1

total = len(results)
pass_n = verdict_counts.get('PASS', 0)
warn_n = verdict_counts.get('WARN', 0)
fail_n = verdict_counts.get('FAIL', 0)

if fail_n == 0 and warn_n == 0:
    overall = "PASS"
elif fail_n == 0:
    overall = "WARN"
else:
    overall = "FAIL"

md_lines = []
md_lines.append("# V88 Phase03 P1 — 新增70项派生指标抽样回测 & DQA扩展校验报告")
md_lines.append("")
md_lines.append(f"> **Task**: T1 (20% sample backtest of 70 derived indicators)")
md_lines.append(f"> **DB**: `{DB_PATH}`")
md_lines.append(f"> **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
md_lines.append("")

# Section 1: Sampling overview
md_lines.append("## 1. 抽样概况")
md_lines.append("")
md_lines.append("| 指标 | 值 |")
md_lines.append("|------|-----|")
md_lines.append(f"| 总派生指标 | {len(all_indicators)} |")
md_lines.append(f"| 抽样比例 | {int(SAMPLE_RATIO*100)}% |")
md_lines.append(f"| 抽样数量 | {sample_size} |")
md_lines.append(f"| 随机种子 | {RANDOM_SEED} |")
md_lines.append(f"| 抽样指标清单 | {', '.join(sampled_ids)} |")
md_lines.append("")

# Section 2: Per-indicator results
md_lines.append("## 2. 逐指标检查结果")
md_lines.append("")
md_lines.append("| indicator_id | rows | date_range | null_cnt | null_% | gaps>90d | extreme_jumps | monotonic | zero_var | verdict |")
md_lines.append("|-------------|------|------------|----------|--------|----------|---------------|-----------|----------|---------|")

for r in results:
    mon_str = "✅" if r['monotonic'] else "—"
    zv_str = "✅" if r['zero_variance'] else "—"
    md_lines.append(
        f"| `{r['indicator_id']}` "
        f"| {r['rows']} "
        f"| {r['date_range']} "
        f"| {r['null_count']} "
        f"| {r['null_pct']:.1f}% "
        f"| {r['gaps_gt_90']} "
        f"| {r['extreme_jumps']} "
        f"| {mon_str} "
        f"| {zv_str} "
        f"| **{r['verdict']}** |"
    )

md_lines.append("")

# Detailed issues section
has_issues = any(r['issues'] for r in results)
if has_issues:
    md_lines.append("### 问题详情")
    md_lines.append("")
    for r in results:
        if r['issues']:
            md_lines.append(f"**`{r['indicator_id']}`** (verdict: {r['verdict']}):")
            for iss in r['issues']:
                md_lines.append(f"  - ⚠️ {iss}")
            md_lines.append("")

# Section 3: Extended DQA rules
md_lines.append("## 3. 扩展DQA规则执行结果")
md_lines.append("")
md_lines.append("| 规则 | 名称 | 结果 | 说明 |")
md_lines.append("|------|------|------|------|")

rule_descriptions = {
    'EDQA-01': '连续3+相同值（疑似数据停滞）',
    'EDQA-02': '时间间隔>90天（数据缺口）',
    'EDQA-03': '空值率>5%（数据不完整）',
    'EDQA-04': '极端跳变>3σ（异常波动）',
    'EDQA-05': '单调序列（一直升/降，缺乏波动）',
    'EDQA-06': '零方差序列（数据无变化）',
}

for code in ['EDQA-01', 'EDQA-02', 'EDQA-03', 'EDQA-04', 'EDQA-05', 'EDQA-06']:
    rr = rule_results[code]
    violators_str = ', '.join(rr['violators']) if rr['violators'] else '无'
    if rr['total_violations'] == 0:
        result_str = "✅ 全部通过"
    elif rr['total_violations'] <= 3:
        result_str = f"⚠️ {rr['total_violations']}/{total} 违规"
    else:
        result_str = f"🔴 {rr['total_violations']}/{total} 违规"
    md_lines.append(
        f"| {code} | {rule_descriptions[code]} "
        f"| {result_str} "
        f"| 违规指标: {violators_str} |"
    )

md_lines.append("")

# Rule definitions detail
md_lines.append("### 规则定义")
md_lines.append("")
md_lines.append("| 规则 | 检查逻辑 | 阈值 |")
md_lines.append("|------|---------|------|")
md_lines.append(f"| EDQA-01 | 连续相同值检测（跳过NULL） | ≥ {STALE_COUNT_THRESHOLD} 个连续相同点 |")
md_lines.append(f"| EDQA-02 | 相邻数据点时间间隔 | > {GAP_THRESHOLD_DAYS} 天 |")
md_lines.append(f"| EDQA-03 | NULL值占总数据点数比例 | > {NULL_THRESHOLD*100}% |")
md_lines.append(f"| EDQA-04 | 相邻值差值绝对值 / 标准差 | > {SIGMA_THRESHOLD}σ |")
md_lines.append(f"| EDQA-05 | 所有非NULL值严格单调递增或递减 | 序列全程单调 |")
md_lines.append(f"| EDQA-06 | 序列标准差 | = 0 |")
md_lines.append("")

# Section 4: Summary
md_lines.append("## 4. 总结")
md_lines.append("")
md_lines.append(f"- **PASS**: {pass_n}/{total}")
md_lines.append(f"- **WARN**: {warn_n}/{total}")
md_lines.append(f"- **FAIL**: {fail_n}/{total}")
md_lines.append(f"- **Overall**: **{overall}**")
md_lines.append("")

if overall == "PASS":
    md_lines.append("✅ **所有抽样指标均通过扩展DQA校验，数据质量良好。**")
elif overall == "WARN":
    md_lines.append("⚠️ **部分指标存在轻微质量问题，建议关注上述违规指标。**")
else:
    md_lines.append("🔴 **存在严重数据质量问题，需立即排查修复。**")

md_lines.append("")
md_lines.append("---")
md_lines.append(f"*Report generated by t1_sample_backtest.py | Seed={RANDOM_SEED} | Sample={sample_size}/{len(all_indicators)}*")

report_text = '\n'.join(md_lines)

# Write report
os.makedirs(OUTPUT_DIR, exist_ok=True)
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(report_text)

print(f"\n[T1] ✅ Report written to: {OUTPUT_FILE}")
print(f"[T1] Summary: PASS={pass_n} WARN={warn_n} FAIL={fail_n} | Overall={overall}")
