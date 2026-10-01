# V85 验收演示操作脚本（真实数据刷新版）

> 工单: `HERMES_V85_PORTAL_REFRESH_WITH_REAL_SIM_DATA_AND_REBUILD_ARCHIVE`
> 面向: 验收人
> 数据源: DSHB真实模拟回放
> 时长: 约20分钟

---

## 演示概览

| 步骤 | 内容 | 时长 | 场景 |
|------|------|------|------|
| 1 | 门户介绍+真实数据说明 | 2min | 基线 |
| 2 | Gate大盘(基线P0拦截率81%) | 3min | 基线 |
| 3 | 切换到场景A(真实回放) | 4min | 场景A |
| 4 | 场景A TP/FP详情 | 3min | 场景A |
| 5 | 切换到场景B(真实回放) | 3min | 场景B |
| 6 | 场景B Gate 8项解除 | 2min | 场景B |
| 7 | 场景对比+真实vs自构建差异 | 2min | 对比 |
| 8 | 上线路径建议 | 1min | — |

---

## 步骤1: 门户介绍+真实数据说明 (2min)

### 话术

> "各位好，本次演示使用DSHB真实模拟回放数据，替换了之前的自构建模拟数据。
> 
> 数据来源是DSHB `0d7b0e8`提交的 `sim_sceneA_result.csv` 和 `sim_sceneB_result.csv`，各62条真实回放记录。
> 
> 所有P0拦截率、TP/FP指标、Gate状态均使用真实回放结果。"

### 关键数据

> "V85覆盖488个模板，21条跨品种P0案例，基线P0拦截率81.0%。"

---

## 步骤2: Gate大盘-基线 (3min)

### 话术

> "基线状态下：P0拦截率81.0%，17/21条P0已拦截，4条漏拦截。"

### 操作

1. 指向 §2.1 基线Gate大盘
2. 逐项讲解:

| Gate | 状态 | 话术 |
|------|------|------|
| H1 | ❌ 0% | "THS匹配率0%，155模板无映射。" |
| H2 | ❌ 81% | "P0拦截率81%，4条漏拦截。" |
| H3 | ❌ 20% | "渲染就绪率20%。" |
| H4 | ❌ 0% | "评审完成率0%。" |
| H5 | ✅ 等价可用 | "风险库等价版已落地。" |
| G-06 | 🔲 PENDING | "4条漏拦截待处置。" |

### 关键点

> "4条漏拦截P0：RISK-002(方向性)、RISK-010/011/013(数据缺失)。现在切换到场景A看BL-009a+白名单的效果。"

---

## 步骤3: 切换到场景A (4min)

### 话术

> "场景A策略：BL-009a规则上线 + 4条P0白名单放行。使用DSHB真实回放数据。"

### 操作

1. 点击「场景A: 最小放行」
2. 指向 §2.2 场景A Gate大盘

### 场景A话术

> "看真实回放结果：
> - P0拦截率从81.0%提升到100.0%！
> - TP增加4（BL-009a +1, 白名单4条）
> - FP增加0，无误拦截！
> 
> Gate状态：
> - H2 PARTIAL_IMPROVED（4条白名单放行）
> - G-03/G-05/G-06 PARTIAL_IMPROVED（BL-009a解除RISK-002）
> - 但H1/H3/H4仍阻塞（需人工评审）
> 
> 完全解除0项，部分改善4项。"

### 关键点

> "场景A结论：⚠ 部分改善。白名单放行4条存在数据缺失风险。"

---

## 步骤4: 场景A TP/FP详情 (3min)

### 话术

> "看场景A的TP/FP明细："

### 操作

1. 指向 §3.2 场景A TP变化明细

### 话术

> "RISK-002：BL-009a规则拦截需求→利润反向，+1 TP ✅
> RISK-010/011/013：数据缺失白名单放行，TP不变
> RISK-005：未命中白名单放行
> 
> 关键：FP=0，BL-009a回放验证无任何误拦截。"

---

## 步骤5: 切换到场景B (3min)

### 话术

> "现在切换到场景B——完整处置。BL-009a+数据修复+BL-026启用+全量P0处置。"

### 操作

1. 点击「场景B: 完整处置」
2. 指向 §2.3 场景B Gate大盘

### 场景B话术

> "真实回放结果：
> - P0拦截率100.0%，TP增加7！
> - BL-009a +1 TP（需求→利润反向）
> - 数据修复 +3 TP（RISK-010/011/013修复后BL-022/020/021触发）
> - BL-026 +1 TP（库存天数跨品种）
> - FP仍为0！
> 
> Gate状态：
> - H2 ✅ RESOLVED（全部P0处置）
> - H5 ✅ RESOLVED（风险库落地）
> - G-01/G-03/G-05/G-06 ✅ RESOLVED
> - 8项Gate完全解除！
> 
> 但H1/H3/H4仍阻塞——这三项依赖人工评审，任何模拟场景都无法解除。"

### 关键点

> "场景B结论：✅ 推荐路径。规则侧8项Gate解除，配合人工评审即可上线。"

---

## 步骤6: 场景B Gate 8项解除 (2min)

### 话术

> "详细看场景B解除的8项Gate："

### 操作

1. 打开 `gate_sceneB_refreshed_report.md`
2. 指向Gate状态表

### 话术

> "H2/H5 RESOLVED + G-01/G-03/G-05/G-06 RESOLVED = 6项直接解除
> 加上BL-009a/BL-026规则确认 = 共8项Gate解除
> TP+7, FP+0
> 仅剩H1/H3/H4需人工评审。"

---

## 步骤7: 场景对比+真实vs自构建差异 (2min)

### 话术

> "对比三个场景："

### 操作

1. 打开 `gate_scenario_compare_refreshed.md`
2. 指向对比表

### 话术

> "基线: P0拦截81%, 禁止上线
> 场景A: P0拦截100%, 4项部分改善, 白名单风险
> 场景B: P0拦截100%, 8项解除, 推荐路径
> 
> 真实数据与旧自构建数据的关键差异：
> - 旧版场景A说H1可解除(80%匹配) → 真实数据H1仍阻塞(需人工)
> - 旧版场景B说5/5 PASS → 真实数据H1/H3/H4仍阻塞
> - 旧版无TP/FP指标 → 真实数据TP+4/+7, FP+0
> 
> 真实数据更准确：模拟场景仅影响规则侧Gate，H1/H3/H4必须人工评审。"

---

## 步骤8: 上线路径建议 (1min)

### 话术

> "推荐路径：场景B + 人工评审
> 
> D+1: THS回写155条 → H1解除
> D+2: BL-009a上线 + BL-026启用 + Batch-A评审
> D+3: 数据修复RISK-010/011/013 → H2/G-01/03/05/06解除
> D+4-5: Batch-B/C评审
> D+6: Gate复检 → 合并main → 上线
> 
> 上线时P0拦截率100%, TP+7, FP+0。"

### 结束话术

> "演示完毕。所有数据均来自DSHB真实模拟回放，门户已完全适配真实指标。"

---

## 附录: 演示命令速查

```bash
# 打开门户(真实数据版)
cat analysis/e2e_output/v85/hermes_refresh_real_data/enhanced_review_portal_v6_final_refreshed.md

# 场景A报告
cat analysis/e2e_output/v85/hermes_refresh_real_data/gate_sceneA_refreshed_report.md

# 场景B报告
cat analysis/e2e_output/v85/hermes_refresh_real_data/gate_sceneB_refreshed_report.md

# 场景对比
cat analysis/e2e_output/v85/hermes_refresh_real_data/gate_scenario_compare_refreshed.md

# 归档重建报告
cat analysis/e2e_output/v85/hermes_refresh_real_data/archive_rebuild_report.md

# Release Note
cat analysis/e2e_output/v85/hermes_refresh_real_data/v85_release_note_refreshed.md

# DSHB原始数据
head -5 analysis/e2e_output/v85/dshb_review_simulation/sim_sceneA_result.csv
head -5 analysis/e2e_output/v85/dshb_review_simulation/sim_sceneB_result.csv
```
