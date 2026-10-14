#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V88 Phase01 DSHB P0 - 6项Pending指标备选数据源离线仿真
TASK_ID: V88_PHASE01_DSHB_P0_PENDING_INDEX_PREP
BRANCH: feature/v88-g1
NO_ZHIJI_API_CALL: TRUE
"""

import numpy as np
from datetime import datetime, timedelta
import json, sys, os

np.random.seed(42)
SIM_YEARS = 3
SIM_START = datetime(2025, 1, 1)
TDPY = 252
TOTAL_DAYS = SIM_YEARS * TDPY

dates = []
d = SIM_START
while len(dates) < TOTAL_DAYS:
    if d.weekday() < 5:
        dates.append(d)
    d += timedelta(days=1)
dates = dates[:TOTAL_DAYS]


def _interp_smooth(base, noise_ratio, lag, freq):
    """生成与base相关的替代数据"""
    n = max(2, TOTAL_DAYS // freq + 1)
    xp = np.arange(n, dtype=np.float64) * freq
    low_signal = np.cumsum(np.random.normal(0, 1, n))
    smoothed = np.interp(np.arange(TOTAL_DAYS), xp, low_signal)
    bs = np.convolve(base, np.ones(min(10, TOTAL_DAYS)) / min(10, TOTAL_DAYS), mode='same')
    bs = (bs - bs.mean()) / (bs.std() + 1e-8)
    bs = bs * smoothed.std() + smoothed.mean()
    alpha = 1.0 - noise_ratio
    mixed = alpha * bs + (1 - alpha) * smoothed
    mixed += np.random.normal(0, noise_ratio * mixed.std() + 1e-6, TOTAL_DAYS)
    if lag > 0 and lag < TOTAL_DAYS:
        shifted = np.zeros(TOTAL_DAYS)
        shifted[lag:] = mixed[:-lag]
    else:
        shifted = mixed.copy()
    shifted[shifted < 0] = 0
    return shifted


def _gen_smm_smelter(commodity):
    base = np.zeros(TOTAL_DAYS)
    if commodity == 'CU':
        for _ in range(3):
            s = np.random.randint(0, max(1, TOTAL_DAYS - 40))
            d = np.random.randint(14, 30)
            e = min(s + d, TOTAL_DAYS)
            l = e - s
            if l > 0:
                base[s:e] += np.random.uniform(2.5, 4.5) * (1 - np.linspace(0, 0.3, l))
        base += np.random.normal(0, 0.5, TOTAL_DAYS)
    elif commodity == 'NI':
        for _ in range(2):
            s = np.random.randint(0, max(1, TOTAL_DAYS - 30))
            d = np.random.randint(10, 25)
            e = min(s + d, TOTAL_DAYS)
            l = e - s
            if l > 0:
                base[s:e] += np.random.uniform(1.0, 2.5) * (1 - np.linspace(0, 0.4, l))
        base += np.random.normal(0, 0.3, TOTAL_DAYS)
    elif commodity == 'SI':
        ws, we = 200, min(245, TOTAL_DAYS)
        wl = we - ws
        if wl > 0:
            base[ws:we] += np.random.uniform(0.5, 1.5) * np.exp(-np.linspace(0, 2, wl) / 5)
        s = np.random.randint(0, max(1, TOTAL_DAYS - 20))
        d = np.random.randint(5, 15)
        e = min(s + d, TOTAL_DAYS)
        l = e - s
        if l > 0:
            base[s:e] += np.random.uniform(0.2, 0.8)
        base += np.random.normal(0, 0.2, TOTAL_DAYS)
    base[base < 0] = 0
    return base


def _gen_smm_spot(commodity):
    if commodity == 'CU':
        pv = np.cumsum(np.random.normal(0, 1, TOTAL_DAYS)) / 30
        base = 120 + 15 * (1 + 0.5 * np.abs(pv))
    elif commodity == 'LC':
        pv = np.cumsum(np.random.normal(0, 1.5, TOTAL_DAYS)) / 20
        base = 60 + 12 * (1 + 0.8 * np.abs(pv))
    elif commodity == 'SI':
        season = np.sin(np.linspace(0, 2 * np.pi * SIM_YEARS, TOTAL_DAYS))
        base = 45 + 8 * (1 + 0.3 * season)
    base += np.random.exponential(5, TOTAL_DAYS)
    base[base < 5] = 5
    return base


def _calc_ic(smm, alt):
    """
    IC: Spearman rank correlation between aligned alternative and SMM baseline.
    Rolling window of 30 points, step 5, with lag alignment.
    """
    window = 30
    step = 5
    ics = []
    for i in range(0, TOTAL_DAYS - window, step):
        aw = alt[i:i + window].astype(np.float64)
        sw = smm[i:i + window].astype(np.float64)
        try:
            ra = np.argsort(np.argsort(aw))
            rs = np.argsort(np.argsort(sw))
            if ra.std() > 1e-8 and rs.std() > 1e-8:
                c = np.corrcoef(ra, rs)[0, 1]
                ics.append(0 if np.isnan(c) else c)
            else:
                ics.append(0)
        except:
            ics.append(0)
    return np.array(ics)


def _calc_ir(ic):
    s = ic.std()
    return ic.mean() / s if s > 1e-8 else 0


def _classify(ic_mean, ir):
    if ic_mean >= 0.30 and ir >= 2.0:
        return "[G] 可直接替换"
    elif ic_mean >= 0.15:
        return "[Y] 仅可做参考替代"
    else:
        return "[R] 无法替代"


def _sep(title=""):
    print("\n" + "=" * 78)
    if title:
        print("  " + title)
    print("=" * 78)


smelter_cfgs = {
    'A1': {'lag': 30, 'noise_ratio': 0.25, 'freq': 30, 'name': '交易所产量反推法'},
    'A2': {'lag': 60, 'noise_ratio': 0.35, 'freq': 60, 'name': '上市公司财报法'},
    'A3': {'lag': 15, 'noise_ratio': 0.20, 'freq': 15, 'name': '行业协会统计法'},
    'A4': {'lag': 45, 'noise_ratio': 0.30, 'freq': 45, 'name': '海关进出口反推法'},
    'A5': {'lag': 7, 'noise_ratio': 0.12, 'freq': 7, 'name': '自建综合模型法'},
}

spot_cfgs = {
    'B1': {'lag': 1, 'noise_ratio': 0.20, 'freq': 1, 'name': '期货成交量代理法'},
    'B2': {'lag': 1, 'noise_ratio': 0.40, 'freq': 1, 'name': 'Baidu搜索指数法'},
    'B3': {'lag': 7, 'noise_ratio': 0.25, 'freq': 7, 'name': '产业链开工率反推法'},
    'B4': {'lag': 30, 'noise_ratio': 0.35, 'freq': 30, 'name': '海关进出口数据法'},
    'B5': {'lag': 3, 'noise_ratio': 0.15, 'freq': 3, 'name': '自建综合模型法'},
}


def _simulate(ind_id, commodity, name, smm, alt_cfgs):
    _sep("指标: {} ({})".format(ind_id, name))
    results = {}
    for ak, ac in alt_cfgs.items():
        alt_data = _interp_smooth(smm, ac['noise_ratio'], ac['lag'], ac['freq'])
        ic = _calc_ic(smm, alt_data)
        im, ist = float(ic.mean()), float(ic.std())
        ipr = float(np.mean(ic > 0))
        itt = im / (ist / np.sqrt(len(ic))) if ist > 1e-8 else 0
        ir = _calc_ir(ic)
        bp = float((alt_data.mean() - smm.mean()) / (smm.mean() + 1e-8) * 100)
        mae = float(np.mean(np.abs(alt_data - smm)))
        sb = np.where(smm != 0, smm, 1)
        mp = min(float(np.mean(np.abs((alt_data - smm) / sb)) * 100), 200.0)
        cl = _classify(im, ir)
        results[ak] = {'IC_mean': round(im, 4), 'IC_std': round(ist, 4),
                        'IC_pos_rate': round(ipr, 4), 'IC_t': round(itt, 4),
                        'IR': round(ir, 4), 'Bias_pct': round(bp, 2),
                        'MAE': round(mae, 2), 'MAPE_pct': round(mp, 2),
                        'classification': cl, 'name': ac['name']}
        print("  {} {} | IC={:+.4f} | Std={:.4f} | Pos={:.1f}% | IR={:+.4f} | Bias={:+.1f}% | MAPE={:.1f}%".format(
            ak, ac['name'], im, ist, ipr * 100, ir, bp, mp))
    print("  --- 替代可行性 ---")
    for ak, r in results.items():
        print("  {}: {}".format(ak, r['classification']))
    return results


def main():
    print("=" * 78)
    print("  V88 Phase01 DSHB P0 - 6项Pending指标备选数据源离线仿真")
    print("  TASK_ID: V88_PHASE01_DSHB_P0_PENDING_INDEX_PREP")
    print("  BRANCH: feature/v88-g1")
    print("  仿真模式: 完全离线 | 零外部API调用 | 合成数据")
    print("=" * 78)
    print("  {}年 / {}交易日 / {} ~ {}".format(SIM_YEARS, TOTAL_DAYS, SIM_START.date(), dates[-1].date()))
    print("  随机种子: 42")

    all_results = {}

    print("\n" + "#" * 78)
    print("  类别1: 冶炼检修量化损失")
    print("#" * 78)
    for ind_id, (comm, nm, node) in {
        'CU_SMELTER_MAINTENANCE': ('CU', '铜冶炼检修量化损失', 's7'),
        'NI_SMELTER_MAINTENANCE': ('NI', '镍冶炼检修量化损失', 's7'),
        'SI_SMELTER_MAINTENANCE': ('SI', '硅冶炼检修量化损失', 's7'),
    }.items():
        smm = _gen_smm_smelter(comm)
        r = _simulate(ind_id, comm, nm, smm, smelter_cfgs)
        all_results[ind_id] = {'name': nm, 'commodity': comm, 'node': node,
            'smm_stats': {'mean': round(float(smm.mean()), 2), 'std': round(float(smm.std()), 2),
                          'min': round(float(smm.min()), 2), 'max': round(float(smm.max()), 2)},
            'results': r}

    print("\n" + "#" * 78)
    print("  类别2: 现货询盘成交活跃度")
    print("#" * 78)
    for ind_id, (comm, nm, node) in {
        'CU_SPOT_INQUIRY_FREQ': ('CU', '铜现货报价频次', 'c1'),
        'LC_SPOT_INQUIRY_FREQ': ('LC', '碳酸锂现货询盘成交活跃度', 'd2'),
        'SI_SPOT_INQUIRY_FREQ': ('SI', '工业硅现货报价频次', 'c1'),
    }.items():
        smm = _gen_smm_spot(comm)
        r = _simulate(ind_id, comm, nm, smm, spot_cfgs)
        all_results[ind_id] = {'name': nm, 'commodity': comm, 'node': node,
            'smm_stats': {'mean': round(float(smm.mean()), 2), 'std': round(float(smm.std()), 2),
                          'min': round(float(smm.min()), 2), 'max': round(float(smm.max()), 2)},
            'results': r}

    # Summary
    _sep("仿真汇总统计")
    gr, yr, rr = [], [], []
    for iid, d2 in all_results.items():
        for ak, r in d2['results'].items():
            c = r['classification']
            if '[G]' in c: gr.append((iid, ak, r))
            elif '[Y]' in c: yr.append((iid, ak, r))
            else: rr.append((iid, ak, r))

    print("\n  [G] 可直接替换: {} 个方案".format(len(gr)))
    for iid, ak, r in gr:
        print("    {} -> {} | IC={:+.4f} | IR={:+.4f}".format(iid, ak, r['IC_mean'], r['IR']))
    print("\n  [Y] 仅可做参考替代: {} 个方案".format(len(yr)))
    for iid, ak, r in yr:
        print("    {} -> {} | IC={:+.4f} | IR={:+.4f}".format(iid, ak, r['IC_mean'], r['IR']))
    print("\n  [R] 无法替代: {} 个方案".format(len(rr)))
    for iid, ak, r in rr:
        print("    {} -> {} | IC={:+.4f} | IR={:+.4f}".format(iid, ak, r['IC_mean'], r['IR']))

    print("\n  --- 每指标最佳备选推荐 ---")
    recs = {}
    for iid, d2 in all_results.items():
        ba, bs, br = None, -999, None
        for ak, r in d2['results'].items():
            sc = r['IR'] * 0.5 + r['IC_mean'] * 0.3 + r['IC_pos_rate'] * 0.2
            if sc > bs:
                bs, ba, br = sc, ak, r
        recs[iid] = {'best_alternative': ba, 'score': round(bs, 4),
                      'classification': br['classification'],
                      'IC_mean': br['IC_mean'], 'IR': br['IR']}
        print("  {} -> {} (score={:.4f}) | {}".format(iid, ba, bs, br['classification']))

    op = os.path.join(os.path.dirname(__file__), 'pending_index_simulation_results.json')
    out = {
        'task_id': 'V88_PHASE01_DSHB_P0_PENDING_INDEX_PREP',
        'branch': 'feature/v88-g1',
        'date': datetime.now().strftime('%Y-%m-%d'),
        'years': SIM_YEARS, 'days': TOTAL_DAYS, 'seed': 42,
        'no_external_api': True, 'no_zhiji_api_call': True,
        'results': all_results,
        'summary': {'replaceable': len(gr), 'reference_only': len(yr), 'not_replaceable': len(rr),
                    'total': len(gr) + len(yr) + len(rr)},
        'recommendations': recs,
    }
    with open(op, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("\n  结果已保存: {}".format(op))
    print("  " + "=" * 78)
    print("  完成 | 6x5=30组 | [G]:{} [Y]:{} [R]:{}".format(len(gr), len(yr), len(rr)))
    print("  " + "=" * 78)
    return out


if __name__ == '__main__':
    main()
