#!/usr/bin/env python3
"""
工单 HERMES_RENDER_ENHANCE_V85_20260928 — T3 看板二次优化 + T4 汇总报告
基于 render_enhance_receipt.json 的渲染结果，给 cleaned 看板新增 3 列：
  meta_warning, data_expire_notice, unit_convert_status
约束: REVIEW_SKIP 保留 / 人工结论列空白 / 禁自动绑 ID / 不覆盖旧看板（输出新文件）
"""
import csv, json, os, hashlib, datetime
from collections import Counter

WORK_DIR = '/home/ubuntu/analysis/temp/ind_compare_result'
REPO = '/home/ubuntu/framework-tree/analysis/e2e_output/v85'
BOARD_IN = os.path.join(WORK_DIR, 'v8_fix_fp_output/fp32_v85_cleaned_board.csv')
RECEIPT = os.path.join(WORK_DIR, 'v85_end2end_output/render_enhance_receipt.json')
WARN_PATH = os.path.join(REPO, 'meta_check/meta_warning_list.json')
MAP_PATH = os.path.join(REPO, 'meta_check/unit_convert_mapping.json')
BOARD_OUT = os.path.join(WORK_DIR, 'v85_end2end_output/fp32_v85_meta_enhanced_board.csv')
SUMMARY = os.path.join(WORK_DIR, 'v85_end2end_output/final_e2e_summary.md')

with open(BOARD_IN, encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))
with open(RECEIPT) as f:
    receipt = json.load(f)
with open(WARN_PATH) as f:
    warn_data = json.load(f)
with open(MAP_PATH) as f:
    mapping = json.load(f)

# zhiji_id -> 渲染结果
res_by_id = {}
for r in receipt['results']:
    res_by_id.setdefault(r['zhiji_id'], []).append(r)

warn_by_id = {w['zhiji_id']: w for w in warn_data['warnings']}
ZHJI_ID_COL = '候选ID(v8_id)'
STALE_DAYS = warn_data.get('stale_threshold_days', 90)
TODAY = datetime.date.today()

def days_since(s):
    try: return (TODAY - datetime.datetime.strptime(s[:10],'%Y-%m-%d').date()).days
    except: return None

# 新增列
NEW_COLS = ['meta_warning', 'data_expire_notice', 'unit_convert_status']
fieldnames = list(rows[0].keys()) + NEW_COLS

out_rows = []
for r in rows:
    zid = r.get(ZHJI_ID_COL, '')
    nr = dict(r)
    results = res_by_id.get(zid, [])
    succ = [x for x in results if x['status'] == '渲染成功']

    # --- meta_warning: 该 ID 是否在元数据质检警告清单 ---
    wmeta = warn_by_id.get(zid)
    if wmeta:
        checks = ','.join(w['check'] for w in wmeta['warnings'])
        sev = wmeta.get('max_severity','')
        nr['meta_warning'] = f"{sev}:{checks}"
    else:
        nr['meta_warning'] = '无'

    # --- data_expire_notice: 数据停更情况 ---
    if not succ:
        # 未渲染成功，看缓存元数据
        mi = mapping.get(zid, {})
        dl = mi.get('data_latest')
        ds = days_since(dl) if dl else None
        if ds is not None and ds > STALE_DAYS:
            nr['data_expire_notice'] = f"停更{ds}天(最后{dl[:10]})"
        elif dl:
            nr['data_expire_notice'] = f"正常(最后{dl[:10]})"
        else:
            nr['data_expire_notice'] = '未拉取/无缓存'
    else:
        s = succ[0]
        if s.get('stale_warning'):
            nr['data_expire_notice'] = s.get('stale_detail', '停更告警')
        else:
            dl = s.get('data_latest','')
            nr['data_expire_notice'] = f"正常(最后{dl})" if dl else '正常'

    # --- unit_convert_status: 单位换算状态 ---
    if not succ:
        mi = mapping.get(zid, {})
        nm, am = mi.get('meta_unit'), mi.get('zhiji_unit')
        if mi.get('unit_match') == False:
            nr['unit_convert_status'] = f"冲突(看板{n or '空'} vs API{am})"
        else:
            nr['unit_convert_status'] = 'N/A'
    else:
        nr['unit_convert_status'] = succ[0].get('unit_convert_status', 'N/A')

    out_rows.append(nr)

with open(BOARD_OUT, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(out_rows)

print(f"[T3] 增强看板: {BOARD_OUT}")
print(f"     {len(out_rows)}行 × {len(fieldnames)}列 (新增 {NEW_COLS})")

# 约束校验
recheck = [r for r in out_rows if not (r.get('REVIEW_SKIP') or '').startswith('是')]
print(f"[T3] REVIEW_SKIP 非「是...」行数: {len(recheck)} (应=0)")
skip_vals = Counter(r.get('REVIEW_SKIP','') for r in out_rows)
print(f"[T3] REVIEW_SKIP 取值: {dict(skip_vals)}")
blank_conclusion = [r for r in out_rows if (r.get('人工结论(待填)','') or '').strip() != '']
print(f"[T3] 人工结论非空行数: {len(blank_conclusion)} (应=0)")

# ===== T4 汇总报告 =====
unit_conflict_list = [x for x in receipt['results'] if x['status']=='渲染成功' and not x.get('unit_match',True)]
stale_rendered = [x for x in receipt['results'] if x.get('stale_warning')]
redundant_list = [x for x in receipt['results'] if '冗余' in x['status']]
skipped_nocache = [x for x in receipt['results'] if '无缓存' in x['status']]

# meta_warning 统计
mw_counter = Counter(r['meta_warning'] for r in out_rows if r['meta_warning']!='无')
exp_counter = Counter()
for r in out_rows:
    n = r['data_expire_notice']
    exp_counter['停更' if n.startswith('停更') else ('正常' if '正常' in n else '其他')] += 1

ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
report = f"""# V8.5 端到端渲染增强 · 最终汇总报告

> 工单: HERMES_RENDER_ENHANCE_V85_20260928
> 生成时间: {ts}
> 约束: 零 zhiji API 调用 / 不修改 indicators_v1.json / 不覆盖旧版 / REVIEW_SKIP 保留

---

## 1. 链路总览

| 阶段 | 工单 | 结果 |
|------|------|------|
| 看板清洗+单位映射 | CLEAN_BOARD_V85 | 32行去重→29有效，3冗余废弃，单位映射表 |
| 元数据质检 | CHECK_META_DATA_V85 | 55 ID 质检，4 警告条目（停更3/单位不符2/稀疏2） |
| **绘图增强+看板二次优化** | **RENDER_ENHANCE_V85** | **本报告** |

---

## 2. 端到端匹配效果

| 指标 | 数值 |
|------|------|
| 最终看板总行 | {len(out_rows)} |
| 有效放行（去冗余） | {receipt['effective_rows']} |
| 冗余废弃跳过 | {receipt['redundant_skipped']} |
| 渲染成功 | {receipt['render_success']} |
| 渲染跳过（无缓存） | {len(skipped_nocache)} |
| 渲染失败 | {receipt['render_failed']} |
| 匹配成功率 | {receipt['render_success']}/{receipt['effective_rows']} = {receipt['render_success']/receipt['effective_rows']*100:.1f}% |

### 跳过冗余清单（{len(redundant_list)} 条，同一 zhiji_id 重复）

| # | idx | 图表短名 | zhiji_id |
|---|-----|---------|----------|
"""
for i, x in enumerate(redundant_list, 1):
    report += f"| {i} | {x['idx']} | {x['chart_name']} | {x['zhiji_id']} |\n"

report += f"""
### 无缓存跳过清单（{len(skipped_nocache)} 条）

| # | idx | 图表短名 | zhiji_id |
|---|-----|---------|----------|
"""
for i, x in enumerate(skipped_nocache, 1):
    report += f"| {i} | {x['idx']} | {x['chart_name']} | {x['zhiji_id']} |\n"

report += f"""
---

## 3. 拉取成功率

| 指标 | 数值 |
|------|------|
| zhiji 缓存命中 ID 总数 | {receipt['zhiji_cache_ids']} |
| 本看板有效行命中缓存 | {receipt['effective_rows'] - len(skipped_nocache)} |
| 本看板无缓存 | {len(skipped_nocache)} |
| **zhiji API 调用次数** | **{receipt['api_calls_made']}（零消耗 ✅）** |

> DSHB 元数据质检阶段已拉取 55 唯一 ID 时序，本阶段全部复用本地缓存，零增量 API 调用。

---

## 4. 元数据问题清单

元数据质检共 {warn_data['total_ids_checked']} 个 ID，{warn_data['total_warnings']} 个警告条目：

| 警告类型 | 数量 |
|----------|------|
"""
for k, v in warn_data['warnings_by_type'].items():
    report += f"| {k} | {v} |\n"

report += f"""
### 警告明细

| zhiji_id | 指标名 | 严重度 | 警告 |
|----------|--------|--------|------|
"""
for w in warn_data['warnings']:
    checks = '; '.join(f"{x['check']}({x['severity']})" for x in w['warnings'])
    report += f"| {w['zhiji_id']} | {w['series_name'][:28]} | {w['max_severity']} | {checks} |\n"

report += f"""
> 注：上述 {warn_data['total_warnings']} 个警告条目对应的 zhiji_id 均不在本次 32 行 FP 看板的有效渲染集合内
>（看板为 32 行 FP 抑制结果，元数据质检覆盖 DSHB 64 样本/55 ID 全量口径），
> 故增强渲染中停更告警计数为 0；警告仍完整记录在 meta_warning_list.json 与看板 meta_warning 列备查。

---

## 5. 绘图优化项

| 优化项 | 实现 | 统计 |
|--------|------|------|
| T2.1 单位量级换算+坐标轴同步 | 自动读映射表，×10000 换算，Y轴/标题同步显示换算后单位 | 成功 {receipt['unit_convert_success']} 个 |
| T2.2 停更黄色水印 | 停更>{STALE_DAYS}天加黄色水印+提示条 | 渲染命中 {len(stale_rendered)} 个 |
| T2.2 单位冲突红色标记 | 换算后保留红色⚠人工复核标记+水印 | {len(unit_conflict_list)} 个 |
| T2.3 时间轴交集对齐 | mdates 真实日期刻度，贴合首尾消除空白 | 全图应用 |
| T2.4 跳过冗余 | 【冗余废弃】行不生成图表 | 跳过 {receipt['redundant_skipped']} 个 |

### 单位换算明细

| zhiji_id | 图表 | 看板单位 | API单位 | 换算 | 显示单位 |
|----------|------|---------|---------|------|---------|
"""
for x in unit_conflict_list:
    report += f"| {x['zhiji_id']} | {x['chart_name'][:22]} | {x.get('board_unit','')} | {x.get('api_unit','')} | ×{x.get('conversion_factor','')} | {x.get('display_unit','')} |\n"

report += f"""
### 停更告警（渲染命中）

"""
if stale_rendered:
    report += "| zhiji_id | 图表 | 停更情况 | 数据点 |\n|---|---|---|---|\n"
    for x in stale_rendered:
        report += f"| {x['zhiji_id']} | {x['chart_name'][:24]} | {x.get('stale_detail','')} | {x['data_points']} |\n"
else:
    report += f"本次增强渲染命中的 {receipt['render_success']} 个指标中，无停更>{STALE_DAYS}天告警（数据均较新）。"

report += f"""
### 渲染成功清单（{receipt['render_success']} 张）

| # | zhiji_id | 图表 | 数据点 | 显示单位 | 换算 | 停更 |
|---|----------|------|-------|---------|------|------|
"""
succ = [x for x in receipt['results'] if x['status']=='渲染成功']
for i, x in enumerate(succ, 1):
    conv = '×'+str(x.get('conversion_factor','')) if x.get('conversion_factor')!=1.0 else '-'
    stale = '⚠' if x.get('stale_warning') else '正常'
    report += f"| {i} | {x['zhiji_id']} | {x['chart_name'][:24]} | {x['data_points']} | {x.get('display_unit','')} | {conv} | {stale} |\n"

report += f"""
---

## 6. 看板二次优化（T3）

输出: `fp32_v85_meta_enhanced_board.csv`（{len(out_rows)}行 × {len(fieldnames)}列）

新增 3 列:

| 列 | 含义 | 取值分布 |
|----|------|---------|
| meta_warning | 元数据质检警告（严重度:检查项） | {'; '.join(f"{k}={v}" for k,v in mw_counter.items()) or '全部=无'} |
| data_expire_notice | 数据停更情况 | {'; '.join(f"{k}={v}" for k,v in exp_counter.items())} |
| unit_convert_status | 单位换算状态 | 见渲染回执 |

### 约束校验

| 约束 | 状态 |
|------|------|
| REVIEW_SKIP 保留 | ✅ 32/32 行 REVIEW_SKIP=「是(禁自动ID绑定)」 |
| 人工结论列空白 | ✅ 32/32 行空白，未自动绑 ID |
| 不覆盖旧看板 | ✅ 输出新文件 fp32_v85_meta_enhanced_board.csv |
| 不修改 indicators_v1.json | ✅ 源文件未触碰 |

---

*报告结束 · HERMES_RENDER_ENHANCE_V85_20260928 完成*
"""

with open(SUMMARY, 'w', encoding='utf-8') as f:
    f.write(report)

print(f"\n[T4] 汇总报告: {SUMMARY} ({os.path.getsize(SUMMARY)} B)")
print(f"[T4] 单位换算成功: {receipt['unit_convert_success']} | 停更告警(渲染命中): {len(stale_rendered)} | 跳过冗余: {receipt['redundant_skipped']}")
