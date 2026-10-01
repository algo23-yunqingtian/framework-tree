# V85 归档包重建差异报告

> 工单: `HERMES_V85_PORTAL_REFRESH_WITH_REAL_SIM_DATA_AND_REBUILD_ARCHIVE`
> 生成时间: 2026-10-01
> 脚本: `enhanced_archive_builder.py` (更新后)

---

## 1. 重建前后对比

| 指标 | 重建前 | 重建后 | 变化 |
|------|--------|--------|------|
| 已复制文件 | 53 | 63 | +10 |
| 跳过文件 | 3 | 3 | 不变 |
| 依赖警告 | 3 | 1 | -2 ✅ |
| 缺失文件 | 0 | 0 | 不变 |
| 总判定 | PASS | PASS | 不变 |

---

## 2. 依赖警告消除

| 依赖项 | 重建前 | 重建后 | 说明 |
|--------|--------|--------|------|
| DSHB sim_sceneA_result.csv | ⚠ 未落盘 | ✅ 已存在 | DSHB 0d7b0e8 已交付 |
| DSHB sim_sceneB_result.csv | ⚠ 未落盘 | ✅ 已存在 | DSHB 0d7b0e8 已交付 |
| DSHB dshb_final_gate_acceptance.md | ⚠ 未落盘 | ⚠ 仍缺失 | 等价版Gate v2替代 |

---

## 3. 新增文件清单

| # | 文件 | 来源 |
|---|------|------|
| 1 | dshb_review_simulation/sim_sceneA_result.csv | DSHB 0d7b0e8 |
| 2 | dshb_review_simulation/sim_sceneB_result.csv | DSHB 0d7b0e8 |
| 3 | dshb_review_simulation/simulation_compare_report.md | DSHB 0d7b0e8 |
| 4 | dshb_review_simulation/gate_block_impact_analysis.md | DSHB 0d7b0e8 |
| 5 | dshb_review_simulation/bl009a_multi_scenario_verify.md | DSHB 0d7b0e8 |
| 6 | dshb_review_simulation/review_consistency_check.py | DSHB 0d7b0e8 |
| 7 | dshb_review_simulation/review_consistency_guide.md | DSHB 0d7b0e8 |
| 8 | dshb_review_simulation/build_review_simulation.py | DSHB 0d7b0e8 |
| 9 | dshb_review_simulation/MD5_MANIFEST.md | DSHB 0d7b0e8 |
| 10 | dshb_review_simulation/human_review_faq.md | DSHB 0d7b0e8 |

---

## 4. MD5清单更新

MD5清单已从53项更新为63项，新增10项DSHB真实模拟产出的MD5校验。

---

## 5. 脚本更新说明

### 5.1 ARCHIVE_TREE新增

```python
'dshb_review_simulation': [
    'sim_sceneA_result.csv',
    'sim_sceneB_result.csv',
    'simulation_compare_report.md',
    'gate_block_impact_analysis.md',
    'bl009a_multi_scenario_verify.md',
    'review_consistency_check.py',
    'review_consistency_guide.md',
    'build_review_simulation.py',
    'MD5_MANIFEST.md',
    'human_review_faq.md',
],
```

### 5.2 依赖路径更新

```python
# 旧路径
'dshb_simulation/sim_sceneA_result.csv'
'dshb_simulation/sim_sceneB_result.csv'
'dshb_full_integrate_extra/dshb_final_gate_acceptance.md'

# 新路径
'dshb_review_simulation/sim_sceneA_result.csv'
'dshb_review_simulation/sim_sceneB_result.csv'
'dshb_full_integrate/dsh_final_gate_acceptance.md'
```

---

## 6. 重建结论

```
┌─────────────────────────────────────────────────┐
│  归档包重建报告                                   │
├─────────────────────────────────────────────────┤
│  文件: 53 → 63 (+10)                             │
│  警告: 3 → 1 (-2, sim场景文件已消除)              │
│  缺失: 0                                         │
│  总判定: ✅ PASS                                  │
│  剩余警告: dshb_final_gate_acceptance.md仍缺失     │
│  (等价版: DSHB Gate v2自检dsh_gate_self_check_v2) │
└─────────────────────────────────────────────────┘
```
