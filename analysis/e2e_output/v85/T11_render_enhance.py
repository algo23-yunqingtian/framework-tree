#!/usr/bin/env python3
"""
工单 HERMES_RENDER_ENHANCE_V85_20260928 — T2/T3/T4 一体
绘图增强改造 + 看板二次优化 + 增强回执

约束:
- 全程不调用 zhiji API，复用本地缓存 (零额度消耗)
- 不修改 indicators_v1.json / 匹配规则 / GT 基准
- 渲染异常只记录不中断
- REVIEW_SKIP 保留，人工结论列保持空白，禁止自动绑 ID
"""
import csv, json, os, hashlib, datetime, re

WORK_DIR = '/home/ubuntu/analysis/temp/ind_compare_result'
REPO = '/home/ubuntu/framework-tree/analysis/e2e_output/v85'
BOARD_PATH = os.path.join(WORK_DIR, 'v8_fix_fp_output/fp32_v85_cleaned_board.csv')
MAPPING_PATH = os.path.join(REPO, 'meta_check/unit_convert_mapping.json')  # 55-ID 完整版
WARN_PATH = os.path.join(REPO, 'meta_check/meta_warning_list.json')
CACHE_DIR = '/home/ubuntu/.hermes/scripts/zhiji_cache'
RENDER_DIR = os.path.join(WORK_DIR, 'v85_end2end_output', 'renders_enhanced')
OUTPUT_DIR = os.path.join(WORK_DIR, 'v85_end2end_output')
BOARD_OUT = os.path.join(OUTPUT_DIR, 'fp32_v85_meta_enhanced_board.csv')
RECEIPT_PATH = os.path.join(OUTPUT_DIR, 'render_enhance_receipt.json')
SUMMARY_PATH = os.path.join(OUTPUT_DIR, 'final_e2e_summary.md')

os.makedirs(RENDER_DIR, exist_ok=True)

# ===== 加载输入 =====
with open(BOARD_PATH, encoding='utf-8-sig') as f:
    board_rows = list(csv.DictReader(f))
with open(MAPPING_PATH) as f:
    unit_mapping = json.load(f)  # {zhiji_id: {zhiji_unit, meta_unit, data_latest, ...}}
with open(WARN_PATH) as f:
    warn_data = json.load(f)

# 构建 zhiji_id -> warning 信息索引
warn_by_id = {w['zhiji_id']: w for w in warn_data['warnings']}

# 停更阈值（与质检一致）
STALE_DAYS = warn_data.get('stale_threshold_days', 90)
TODAY = datetime.date.today()

def days_since(date_str):
    try:
        d = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        return (TODAY - d).days
    except Exception:
        return None

# ===== 列常量 =====
ZHJI_ID_COL = '候选ID(v8_id)'
CHART_COL = '图表短名(PDF)'
IDX_COL = 'idx'
CAND_UNIT_COL = '候选单位'
API_UNIT_COL = '时序单位(API)'
UNIT_MATCH_COL = '单位匹配'
REDUNDANT_COL = '冗余标记'

# ===== 单位换算表（吨/万吨 量级换算）=====
UNIT_FACTOR = {
    ('吨', '万吨'): 10000.0,
    ('万吨', '吨'): 0.0001,
}

def get_conversion(board_unit, api_unit):
    """返回换算因子，无映射返回 1.0"""
    if board_unit and api_unit and (board_unit, api_unit) in UNIT_FACTOR:
        return UNIT_FACTOR[(board_unit, api_unit)]
    return 1.0

# ===== 加载 zhiji 缓存 =====
series_by_id = {}
for fname in os.listdir(CACHE_DIR):
    if fname.startswith('series_') and fname.endswith('.json'):
        try:
            with open(os.path.join(CACHE_DIR, fname)) as fh:
                data = json.load(fh)
                zid = data.get('id', '')
                if zid:
                    series_by_id[zid] = data
        except Exception:
            pass

print(f"[T2] zhiji 缓存索引: {len(series_by_id)} unique IDs (零API调用)")

# ===== matplotlib =====
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import matplotlib.dates as mdates
print(f"[T2] matplotlib {matplotlib.__version__}")

# 中文字体
plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def parse_dt(s):
    """把日期字符串解析成 datetime，失败返回 None"""
    for fmt in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d'):
        try:
            return datetime.datetime.strptime(s.strip(), fmt)
        except Exception:
            continue
    return None

# ===== 渲染 =====
render_results = []
total_effective = 0
unit_convert_success = 0
stale_warn_count = 0

def add_watermark(fig, ax, kind):
    """
    kind='stale'  -> 黄色停更水印
    kind='unit'   -> 红色单位复核标记
    """
    if kind == 'stale':
        fig.text(0.5, 0.5, '停更 · 数据陈旧', fontsize=24, color='#e6c200',
                 alpha=0.18, ha='center', va='center', fontweight='bold',
                 rotation=18)
    elif kind == 'unit':
        fig.text(0.5, 0.5, '单位冲突 · 待人工复核', fontsize=22, color='#cc0000',
                 alpha=0.15, ha='center', va='center', fontweight='bold',
                 rotation=18)

for i, r in enumerate(board_rows):
    zid = r.get(ZHJI_ID_COL, '')
    chart_name = r.get(CHART_COL, '')
    idx_val = r.get(IDX_COL, '')

    # --- T2.4: 跳过冗余废弃行 ---
    if r.get(REDUNDANT_COL, '') == '【冗余废弃】':
        render_results.append({
            'idx': idx_val, 'chart_name': chart_name, 'zhiji_id': zid,
            'status': '跳过(冗余废弃)', 'data_points': 0,
            'unit_convert_status': 'N/A', 'stale_warning': False
        })
        continue

    total_effective += 1

    # --- 缓存命中 ---
    if zid not in series_by_id:
        render_results.append({
            'idx': idx_val, 'chart_name': chart_name, 'zhiji_id': zid,
            'status': '跳过(无缓存时序数据)', 'data_points': 0,
            'unit_convert_status': 'N/A', 'stale_warning': False
        })
        continue

    series = series_by_id[zid]
    points = series.get('points', [])

    if not points:
        render_results.append({
            'idx': idx_val, 'chart_name': chart_name, 'zhiji_id': zid,
            'status': '跳过(缓存无数据点)', 'data_points': 0,
            'unit_convert_status': 'N/A', 'stale_warning': False
        })
        continue

    # --- 解析日期+数值（保留有效点）---
    dt_objs = []
    values = []
    raw_dates = []
    for p in points:
        dstr = p.get('date', '')
        val = p.get('value', '')
        if val in (None, '', '-'):
            continue
        try:
            v = float(val)
        except (ValueError, TypeError):
            continue
        dt = parse_dt(dstr)
        if dt is None:
            continue
        dt_objs.append(dt)
        values.append(v)
        raw_dates.append(dstr)

    if len(values) < 2:
        render_results.append({
            'idx': idx_val, 'chart_name': chart_name, 'zhiji_id': zid,
            'status': '跳过(有效数据点不足)', 'data_points': len(values),
            'unit_convert_status': 'N/A', 'stale_warning': False
        })
        continue

    # --- 单位判定 ---
    board_unit = r.get(CAND_UNIT_COL, '').strip()
    api_unit_cache = series.get('unit', '').strip()
    api_unit_board = r.get(API_UNIT_COL, '').strip()
    api_unit = api_unit_cache if api_unit_cache else api_unit_board

    unit_match = True
    if board_unit and api_unit and board_unit != api_unit:
        unit_match = False

    # --- T2.1: 单位换算 + 坐标轴/图例同步 ---
    conversion_factor = get_conversion(board_unit, api_unit)
    converted = values
    display_unit = board_unit if board_unit else api_unit  # 图表最终显示单位 = 看板单位
    unit_convert_status = '无冲突'
    if not unit_match and conversion_factor != 1.0:
        converted = [v * conversion_factor for v in values]
        unit_convert_success += 1
        unit_convert_status = f'已换算(看板{board_unit}←API{api_unit}×{conversion_factor})'
    elif not unit_match and conversion_factor == 1.0:
        unit_convert_status = f'单位冲突无换算映射(看板{board_unit}/API{api_unit})'

    # --- T2.3: 时间轴交集对齐（单序列：取自身首尾；多指标同图场景此单序列即交集边界）---
    # 用真实日期对齐 x 轴，消除单侧空白区间
    t_min = dt_objs[0]
    t_max = dt_objs[-1]
    # 用 mdates 让 x 轴真实时间刻度，自动贴合首尾
    x_plot = mdates.date2num([d.toordinal() for d in dt_objs])

    # --- T2.2: 停更判定 ---
    stale_flag = False
    stale_detail = ''
    data_latest = series.get('data_latest') or (series.get('points', [{}])[-1].get('date') if points else '')
    if data_latest:
        ds = days_since(str(data_latest)[:10])
        if ds is not None and ds > STALE_DAYS:
            stale_flag = True
            stale_detail = f'停更{ds}天(最后更新{str(data_latest)[:10]})'
            stale_warn_count += 1

    # --- 渲染 ---
    safe_name = re.sub(r'[/:\\：*?"<>|]', '_', chart_name)[:35]
    png_filename = f"{zid}_{safe_name}.png"
    png_path = os.path.join(RENDER_DIR, png_filename)

    try:
        fig, ax = plt.subplots(figsize=(12.1, 3.74), dpi=100)
        ax.plot(x_plot, converted, linewidth=0.9, color='#1f77b4', marker='.', markersize=2.5)

        # 标题（单位同步显示换算后单位）
        title = f"{chart_name}"
        if unit_match:
            title += f" ({display_unit})"
        else:
            title += f" (换算→{display_unit})"
        ax.set_title(title, fontsize=10, fontweight='bold')

        # Y 轴单位标注（换算后）
        ax.set_ylabel(f"{display_unit}", fontsize=9)
        if not unit_match and conversion_factor != 1.0:
            ax.set_ylabel(f"{display_unit} (API{api_unit}×{conversion_factor})", fontsize=9, color='#cc0000')

        # X 轴真实时间刻度
        ax.set_xlim(mdates.date2num(t_min), mdates.date2num(t_max))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=8))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=7)

        ax.grid(True, alpha=0.3, linestyle='--')

        # --- 水印叠加（先停更后单位，单位在最上层醒目）---
        add_watermark(fig, ax, 'stale' if stale_flag else 'none') if False else None
        if stale_flag:
            add_watermark(fig, ax, 'stale')
        if not unit_match:
            add_watermark(fig, ax, 'unit')

        # 单位冲突提示条
        if not unit_match:
            if conversion_factor != 1.0:
                warn_txt = f"【告警】单位换算: API={api_unit} → 看板={display_unit} (×{conversion_factor})  已换算"
            else:
                warn_txt = f"【告警】单位冲突: 看板={board_unit}, API={api_unit}  无换算映射 待人工复核"
            ax.text(0.5, 0.92, warn_txt, transform=ax.transAxes, ha='center', va='top',
                    fontsize=8, color='#cc0000',
                    bbox=dict(boxstyle='round', facecolor='#fff3cd', alpha=0.6, edgecolor='#cc0000'))

        # 停更提示条
        if stale_flag:
            ax.text(0.5, 0.80, f"【停更】{stale_detail}", transform=ax.transAxes,
                    ha='center', va='top', fontsize=8, color='#8a7000',
                    bbox=dict(boxstyle='round', facecolor='#fff9c4', alpha=0.6, edgecolor='#e6c200'))

        # 数据摘要
        summary = f"数据点: {len(values)} | 范围: {raw_dates[0]}~{raw_dates[-1]}"
        ax.text(0.01, 0.02, summary, transform=ax.transAxes, fontsize=7, alpha=0.7)

        plt.tight_layout()
        plt.savefig(png_path, bbox_inches='tight', dpi=100)
        plt.close()

        png_md5 = hashlib.md5(open(png_path, 'rb').read()).hexdigest()

        render_results.append({
            'idx': idx_val, 'chart_name': chart_name, 'zhiji_id': zid,
            'status': '渲染成功', 'data_points': len(values),
            'board_unit': board_unit, 'api_unit': api_unit,
            'display_unit': display_unit, 'unit_match': unit_match,
            'conversion_factor': conversion_factor, 'unit_convert_status': unit_convert_status,
            'stale_warning': stale_flag, 'stale_detail': stale_detail,
            'data_latest': str(data_latest)[:10] if data_latest else '',
            'png_path': png_path, 'png_md5': png_md5,
            'date_range': f"{raw_dates[0]}~{raw_dates[-1]}"
        })
        flags = []
        if not unit_match: flags.append(f"单位换算×{conversion_factor}")
        if stale_flag: flags.append("停更告警")
        flag_str = (' | ' + '+'.join(flags)) if flags else ''
        print(f"  [OK] {zid} {chart_name[:24]:<26} | {len(values):>4}点 | 显示={display_unit}{flag_str}")

    except Exception as e:
        # T5.4: 渲染异常只记录不中断
        render_results.append({
            'idx': idx_val, 'chart_name': chart_name, 'zhiji_id': zid,
            'status': f'渲染失败(已记录不中断): {str(e)[:120]}',
            'data_points': len(values), 'unit_convert_status': unit_convert_status,
            'stale_warning': stale_flag
        })
        print(f"  [FAIL] {zid} {chart_name[:24]:<26} | {str(e)[:50]}")

# ===== 汇总统计 =====
success = sum(1 for x in render_results if x['status'] == '渲染成功')
skipped = sum(1 for x in render_results if '跳过' in x['status'])
failed = sum(1 for x in render_results if x['status'].startswith('渲染失败'))
redundant_skipped = sum(1 for x in render_results if '冗余' in x['status'])

receipt = {
    'work_order': 'HERMES_RENDER_ENHANCE_V85_20260928',
    'task': 'T4_render_enhance',
    'timestamp': datetime.datetime.now().isoformat(),
    'total_rows': len(board_rows),
    'effective_rows': total_effective,
    'render_success': success,
    'render_skipped': skipped,
    'render_failed': failed,
    'redundant_skipped': redundant_skipped,
    'unit_convert_success': unit_convert_success,
    'stale_warning_count': stale_warn_count,
    'stale_threshold_days': STALE_DAYS,
    'zhiji_cache_ids': len(series_by_id),
    'api_calls_made': 0,
    'results': render_results
}
with open(RECEIPT_PATH, 'w', encoding='utf-8') as f:
    json.dump(receipt, f, ensure_ascii=False, indent=2)

print(f"\n[T4 汇总]")
print(f"  总行: {len(board_rows)} | 有效: {total_effective} | 成功: {success} | 跳过: {skipped} | 失败: {failed}")
print(f"  单位换算成功: {unit_convert_success} | 停更告警: {stale_warn_count} | 跳过冗余: {redundant_skipped}")
print(f"  回执: {RECEIPT_PATH}")
