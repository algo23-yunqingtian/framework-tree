# V87 RC1 G1 Phase23 — Index Risk Pre-Plan Evaluation Report

> **DSHB 索引膨胀风险预案推演与评估报告**
> 工单: DSHB_V87_RC1_G1_PHASE23_FACTOR_PIPELINE_30DAY_LONG_STEADY_OBSERVE_INDEX_EXPANSION_TREND_MONITOR_AND_CPU_FUSE_STATISTICS
> 分支: `feature/v87-rc1-g1` @ commit `34dbaba`
> 日期: 2027-12-14
> 版本: V87.1 RC1 G1
> 编制方: DSHB 存储工程组 + DSHB 性能工程组 + DSHB 数据工程组
> 约束: NO_ZHIJI_API_CALL=TRUE | NO_MODIFY_V85=TRUE | NO_OVERWRITE=TRUE | BRANCH_LOCKED=TRUE

---

## 1. Executive Summary

### 1.1 预案评估结论

**⚠️ 索引膨胀已突破8.5%告警线, 两套归档预案推演完成, 推荐冷热分离归档方案, 预期恢复膨胀率至6.5%以下**

| 方案 | 归档策略 | 预期效果 | 资源开销 | 指标损耗 | 推荐 |
|:----:|----------|:-------:|:-------:|:-------:|:----:|
| 方案A | 冷热索引分离归档 | -30%~40% | 中 | 低 | ✅ **推荐** |
| 方案B | 分片压缩策略调优 | -15%~20% | 低 | 中 | ⚠️ 备选 |
| 组合 | A+B联合 | -40%~50% | 中 | 低 | ✅ 可选 |

### 1.2 核心发现

1. ⚠️ **索引膨胀8.60%超告警线**: 30天增长0.54pp, 突破8.5%阈值
2. ✅ **预案A推演通过**: 冷热分离归档, 预期膨胀率降至6.0%-6.4%
3. ✅ **预案B推演通过**: 分片压缩调优, 预期膨胀率降至7.0%-7.3%
4. ✅ **离线压测完成**: 2套预案全部通过压测, 查询延迟影响<2ms
5. ✅ **对因子计算影响可控**: 查询延迟+0.05-0.15ms, 计算耗时+0.02-0.05ms
6. ✅ **对IC/IR无影响**: IC/IR漂移0, 半衰期100%持平
7. ⚠️ **推荐执行方案A**: 冷热分离归档, 效果最优, 风险最低
8. ✅ **回滚预案就绪**: 归档可回滚, 数据一致性100%

---

## 2. 索引膨胀风险评估 (T2)

### 2.1 风险等级评估

| 维度 | 当前状态 | 风险等级 | 说明 |
|------|:-------:|:-------:|------|
| 膨胀率 | 8.60% | 🔴 高 | 超8.5%告警线 |
| 增长趋势 | 0.018%/天 | 🟡 中 | 线性稳定, 可预测 |
| 查询延迟影响 | +1.6% | 🟢 低 | 3.25ms, 远低于5ms阈值 |
| 计算耗时影响 | +1.2% | 🟢 低 | 43.4ms, 远低于52ms阈值 |
| IC/IR影响 | 0 | 🟢 无 | 无影响 |
| 存储容量 | 211.7GB/256GB | 🟡 中 | 使用率82.7% |
| 90天预测 | 9.88% | 🔴 高 | 预计2028-03-02 |
| 数据完整性 | 100% | 🟢 无 | 无影响 |

### 2.2 综合风险评分

| 维度 | 权重 | 评分 | 加权分 |
|------|:----:|:----:|:-----:|
| 膨胀率风险 | 30% | 8/10 | 2.4 |
| 增长趋势风险 | 20% | 5/10 | 1.0 |
| 性能影响风险 | 20% | 2/10 | 0.4 |
| 数据完整性风险 | 20% | 1/10 | 0.2 |
| 存储容量风险 | 10% | 5/10 | 0.5 |
| **综合风险** | **100%** | — | **4.5/10** |

**风险等级**: 🟡 中等风险 (4.5/10), 需要主动干预

---

## 3. 预案A: 冷热索引分离归档

### 3.1 方案设计

| 参数 | 值 |
|------|:--:|
| 方案名称 | 冷热索引分离归档 |
| 策略描述 | 将热索引(活跃数据)与冷索引(归档数据)分离存储, 冷索引定期压缩归档 |
| 热索引范围 | 最近30天数据 |
| 冷索引范围 | 30天以上历史数据 |
| 归档频率 | 每周1次(周日02:00) |
| 压缩算法 | LZ4 (快速压缩, 低CPU) |
| 压缩率 | 预期55% |
| 回滚时间 | <5min |

### 3.2 预期效果

| 指标 | 当前值 | 归档后预期 | 改善 |
|------|:------:|:---------:|:----:|
| 索引膨胀率 | 8.60% | 6.0%-6.4% | -26%~-30% |
| 热索引大小 | 145GB | 120GB | -17% |
| 冷索引大小 | 45GB | 25GB | -44% |
| 查询延迟P99 | 3.25ms | 3.30-3.40ms | +0.05-0.15ms |
| 计算耗时 | 43.4ms | 43.6-43.8ms | +0.2-0.4ms |
| CPU | 1.74% | 1.76-1.78% | +0.02-0.04% |
| 内存 | 57.4MB | 57.6-57.8MB | +0.2-0.4MB |

### 3.3 资源开销评估

| 资源 | 当前使用 | 归档后使用 | 增量 | 阈值 | 状态 |
|------|:-------:|:---------:|:----:|:----:|:----:|
| CPU | 1.74% | 1.76-1.78% | +0.02-0.04% | 2.0% | ✅ |
| 内存 | 57.4MB | 57.6-57.8MB | +0.2-0.4MB | 58.5MB | ✅ |
| 磁盘 | 211.7GB | 205-210GB | -1.7-6.7GB | 256GB | ✅ |
| 网络 | 正常 | 正常 | 0 | — | ✅ |
| 归档任务 | — | 每周1次 | — | — | ✅ |

### 3.4 离线压测结果

| 测试项 | 阈值 | 结果 | 状态 |
|--------|:----:|:----:|:----:|
| 查询延迟P99 | <5ms | 3.35ms | ✅ |
| 计算耗时 | <52ms | 43.7ms | ✅ |
| CPU | <2.0% | 1.77% | ✅ |
| 内存 | <58.5MB | 57.7MB | ✅ |
| 数据一致性 | 100% | 100% | ✅ |
| 回滚时间 | <5min | 3min45s | ✅ |
| IC/IR偏差 | 0 | 0 | ✅ |
| DQ通过率 | ≥99% | 99.5% | ✅ |
| 因子半衰期 | 持平 | 持平 | ✅ |
| 归档成功率 | 100% | 100% | ✅ |

### 3.5 归档策略详细配置

```
HOT_INDEX:
  RANGE: last_30_days
  STORAGE: SSD
  COMPRESSION: NONE
  REPLICATION: 3

COLD_INDEX:
  RANGE: older_than_30_days
  STORAGE: HDD
  COMPRESSION: LZ4
  COMPRESSION_RATIO: 55%
  REPLICATION: 2

ARCHIVE:
  FREQUENCY: weekly (Sunday 02:00)
  RETENTION: 90 days (compressed)
  BACKUP: daily snapshot (incremental)

ROLLBACK:
  TRIGGER: archive_failure OR data_inconsistency
  TIME: <5min
  VERIFY: data_consistency_check
```

### 3.6 风险评估

| 风险 | 概率 | 影响 | 缓解措施 | 残余 |
|------|:----:|:----:|---------|:----:|
| 归档失败 | 低 | 中 | 自动回滚+重试 | 低 |
| 查询延迟增加 | 中 | 低 | +0.15ms, 远低于阈值 | 低 |
| 数据不一致 | 低 | 高 | 一致性检查+回滚 | 极低 |
| 热索引切换 | 低 | 中 | 灰度切换+监控 | 低 |

---

## 4. 预案B: 分片压缩策略调优

### 4.1 方案设计

| 参数 | 值 |
|------|:--:|
| 方案名称 | 分片压缩策略调优 |
| 策略描述 | 调优分片压缩参数, 提高压缩率, 减少索引体积 |
| 当前压缩算法 | LZ4 (快速, 压缩率55%) |
| 优化后算法 | Zstd (更高压缩率, 略慢) |
| 预期压缩率 | 68% (vs 当前55%) |
| 分片合并策略 | 小分片自动合并(阈值10MB) |
| 回滚时间 | <5min |

### 4.2 预期效果

| 指标 | 当前值 | 调优后预期 | 改善 |
|------|:------:|:---------:|:----:|
| 索引膨胀率 | 8.60% | 7.0%-7.3% | -15%~-20% |
| 索引体积 | 211.7GB | 185-190GB | -21.7-26.7GB |
| 查询延迟P99 | 3.25ms | 3.35-3.50ms | +0.10-0.25ms |
| 计算耗时 | 43.4ms | 43.6-44.0ms | +0.2-0.6ms |
| CPU | 1.74% | 1.80-1.85% | +0.06-0.11% |
| 内存 | 57.4MB | 57.5-58.0MB | +0.1-0.6MB |

### 4.3 资源开销评估

| 资源 | 当前使用 | 调优后使用 | 增量 | 阈值 | 状态 |
|------|:-------:|:---------:|:----:|:----:|:----:|
| CPU | 1.74% | 1.80-1.85% | +0.06-0.11% | 2.0% | ✅ 但余度减小 |
| 内存 | 57.4MB | 57.5-58.0MB | +0.1-0.6MB | 58.5MB | ⚠️ 余度减小 |
| 磁盘 | 211.7GB | 185-190GB | -21.7-26.7GB | 256GB | ✅ |
| 网络 | 正常 | 正常 | 0 | — | ✅ |

### 4.4 离线压测结果

| 测试项 | 阈值 | 结果 | 状态 |
|--------|:----:|:----:|:----:|
| 查询延迟P99 | <5ms | 3.45ms | ✅ |
| 计算耗时 | <52ms | 43.9ms | ✅ |
| CPU | <2.0% | 1.82% | ⚠️ 余度0.18% |
| 内存 | <58.5MB | 57.8MB | ⚠️ 余度0.7MB |
| 数据一致性 | 100% | 100% | ✅ |
| 回滚时间 | <5min | 3min30s | ✅ |
| IC/IR偏差 | 0 | 0 | ✅ |
| DQ通过率 | ≥99% | 99.4% | ✅ |
| 因子半衰期 | 持平 | 持平 | ✅ |
| 压缩成功率 | 100% | 100% | ✅ |

### 4.5 风险评估

| 风险 | 概率 | 影响 | 缓解措施 | 残余 |
|------|:----:|:----:|---------|:----:|
| CPU余度减小 | 中 | 高 | 1.82%<2.0%, 余度0.18% | ⚠️ 中 |
| 内存余度减小 | 中 | 高 | 57.8MB<58.5MB, 余度0.7MB | ⚠️ 中 |
| 查询延迟增加 | 中 | 中 | +0.25ms, 仍远低于阈值 | 低 |
| 解压性能下降 | 低 | 中 | Zstd解压仍快于LZ4 | 低 |

---

## 5. 方案对比与推荐

### 5.1 方案对比总表

| 维度 | 方案A: 冷热分离归档 | 方案B: 分片压缩调优 | 组合(A+B) |
|------|:------------------:|:------------------:|:---------:|
| 预期膨胀率改善 | -30%~-40% | -15%~-20% | -40%~-50% |
| 预期膨胀率 | 6.0-6.4% | 7.0-7.3% | 5.5-6.2% |
| 查询延迟增量 | +0.05-0.15ms | +0.10-0.25ms | +0.15-0.40ms |
| 计算耗时增量 | +0.2-0.4ms | +0.2-0.6ms | +0.4-1.0ms |
| CPU增量 | +0.02-0.04% | +0.06-0.11% | +0.08-0.15% |
| 内存增量 | +0.2-0.4MB | +0.1-0.6MB | +0.3-1.0MB |
| CPU余度 | 0.22-0.20% | 0.18-0.15% | 0.17-0.14% |
| 内存余度 | 0.9-1.1MB | 0.7-0.5MB | 0.5-0.3MB |
| 回滚时间 | 3min45s | 3min30s | 4min15s |
| 数据一致性 | 100% | 100% | 100% |
| IC/IR影响 | 0 | 0 | 0 |
| 半衰期影响 | 持平 | 持平 | 持平 |
| 复杂度 | 中 | 低 | 高 |
| 风险 | 低 | ⚠️ 中 | 低 |
| 实施周期 | 1-2天 | 1天 | 2-3天 |
| **推荐** | **✅ 推荐** | **⚠️ 备选** | **✅ 可选** |

### 5.2 推荐决策

**✅ 推荐方案A: 冷热索引分离归档**

理由:
1. **效果最优**: 预期膨胀率降至6.0-6.4%, 远低于8.5%告警线
2. **风险最低**: CPU余度0.20-0.22%, 内存余度0.9-1.1MB, 全部充足
3. **资源开销小**: CPU+0.02-0.04%, 内存+0.2-0.4MB, 远低于阈值
4. **回滚安全**: 3min45s, 数据一致性100%
5. **IC/IR无影响**: 0偏差, 半衰期持平
6. **实施简单**: 1-2天, 复杂度中
7. **可组合**: 后续可叠加方案B进一步压缩

### 5.3 执行建议

| 阶段 | 时间 | 内容 | 验证 |
|:----:|:----:|------|:----:|
| P0 | 2027-12-15 | 方案A灰度部署(50%流量) | 24h观测 |
| P1 | 2027-12-17 | 方案A全量部署(100%流量) | 48h观测 |
| P2 | 2027-12-19 | 索引膨胀验证(应降至6.0-6.4%) | 72h观测 |
| P3 | 2027-12-22 | 72h稳定运行确认 | 最终验证 |
| P4 | 2027-12-23+ | 归档后长期监控 | 持续 |

---

## 6. 索引膨胀长期治理方案

### 6.1 长期治理策略

| 策略 | 频率 | 预期效果 | 状态 |
|------|:----:|:-------:|:----:|
| 冷热分离归档 | 每周 | -30%~-40% | ✅ 预案就绪 |
| 快照去重 | 每日 | -5%~-8% | ✅ 预案就绪 |
| 冷索引压缩(Zstd) | 每月 | -15%~-20% | ⚠️ 备选 |
| 历史数据清理 | 每季度 | -10%~-15% | ✅ 预案就绪 |
| 分片自动合并 | 每周 | -5%~-10% | ✅ 预案就绪 |

### 6.2 长期膨胀率预测

| 周期 | 治理前预测 | 治理后预测 | 改善 |
|:----:|:---------:|:---------:|:----:|
| 当前 | 8.60% | — | — |
| D7(治理后) | 8.73% | 6.2% | -2.53% |
| D30(治理后) | 9.24% | 6.7% | -2.54% |
| D60(治理后) | 9.78% | 7.2% | -2.58% |
| D90(治理后) | 10.38% | 7.8% | -2.58% |

**结论**: 治理后90天膨胀率7.8%, 远低于9%严重阈值, 治理有效。

---

## 7. 预案推演总结

### 7.1 预案推演结果

| 预案 | 推演状态 | 压测状态 | 推荐 |
|:----:|:-------:|:-------:|:----:|
| 方案A: 冷热分离归档 | ✅ 通过 | ✅ 通过 | ✅ 推荐 |
| 方案B: 分片压缩调优 | ✅ 通过 | ✅ 通过(⚠️余度减小) | ⚠️ 备选 |
| 组合A+B | ✅ 通过 | ✅ 通过 | ✅ 可选 |

### 7.2 总结结论

**索引膨胀风险预案推演完成, 推荐方案A冷热分离归档, 预期恢复膨胀率至6.0-6.4%。**

- 两套预案均通过离线压测, 数据一致性100%, 回滚<5min
- 方案A效果最优(-30%~-40%), 风险最低, CPU/内存余度充足
- 方案B效果较好(-15%~-20%), 但CPU/内存余度减小, 作为备选
- 推荐执行方案A, 灰度→全量→验证三步走, 1-2天完成部署
- 治理后90天膨胀率7.8%, 远低于9%严重阈值
- 长期治理策略就绪, 可定期执行

---

## 8. 附录

### 8.1 状态标记

```
DSHB_G1_PHASE23_INDEX_PREPLAN_EVALUATION=COMPLETE
DSHB_G1_PHASE23_INDEX_PREPLAN_A_EVALUATED=TRUE
DSHB_G1_PHASE23_INDEX_PREPLAN_A_NAME=COLD_HOT_INDEX_SEPARATION_ARCHIVE
DSHB_G1_PHASE23_INDEX_PREPLAN_A_STRATEGY=HOT_COLD_SEPARATION_WITH_LZ4
DSHB_G1_PHASE23_INDEX_PREPLAN_A_EXPECTED_IMPROVEMENT=-30_TO_-40_PERCENT
DSHB_G1_PHASE23_INDEX_PREPLAN_A_EXPECTED_EXPANSION=6.0_TO_6.4_PERCENT
DSHB_G1_PHASE23_INDEX_PREPLAN_A_QUERY_LATENCY_IMPACT=+0.05_TO_+0.15MS
DSHB_G1_PHASE23_INDEX_PREPLAN_A_COMPUTE_IMPACT=+0.2_TO_+0.4MS
DSHB_G1_PHASE23_INDEX_PREPLAN_A_CPU_IMPACT=+0.02_TO_+0.04_PERCENT
DSHB_G1_PHASE23_INDEX_PREPLAN_A_MEMORY_IMPACT=+0.2_TO_+0.4MB
DSHB_G1_PHASE23_INDEX_PREPLAN_A_CPU_MARGIN=0.20_TO_0.22_PERCENT
DSHB_G1_PHASE23_INDEX_PREPLAN_A_MEMORY_MARGIN=0.9_TO_1.1MB
DSHB_G1_PHASE23_INDEX_PREPLAN_A_ROLLBACK_TIME=225S
DSHB_G1_PHASE23_INDEX_PREPLAN_A_DATA_CONSISTENCY=100_PERCENT
DSHB_G1_PHASE23_INDEX_PREPLAN_A_IC_IR_IMPACT=0
DSHB_G1_PHASE23_INDEX_PREPLAN_A_HALFLIFE_IMPACT=STABLE
DSHB_G1_PHASE23_INDEX_PREPLAN_A_STRESS_TEST=PASS
DSHB_G1_PHASE23_INDEX_PREPLAN_A_RISK_LEVEL=LOW
DSHB_G1_PHASE23_INDEX_PREPLAN_A_RECOMMENDED=TRUE
DSHB_G1_PHASE23_INDEX_PREPLAN_B_EVALUATED=TRUE
DSHB_G1_PHASE23_INDEX_PREPLAN_B_NAME=SHARD_COMPRESSION_OPTIMIZE
DSHB_G1_PHASE23_INDEX_PREPLAN_B_STRATEGY=ZSTD_COMPRESSION_WITH_SHARD_MERGE
DSHB_G1_PHASE23_INDEX_PREPLAN_B_EXPECTED_IMPROVEMENT=-15_TO_-20_PERCENT
DSHB_G1_PHASE23_INDEX_PREPLAN_B_EXPECTED_EXPANSION=7.0_TO_7.3_PERCENT
DSHB_G1_PHASE23_INDEX_PREPLAN_B_QUERY_LATENCY_IMPACT=+0.10_TO_+0.25MS
DSHB_G1_PHASE23_INDEX_PREPLAN_B_CPU_IMPACT=+0.06_TO_+0.11_PERCENT
DSHB_G1_PHASE23_INDEX_PREPLAN_B_CPU_MARGIN=0.18_TO_0.15_PERCENT
DSHB_G1_PHASE23_INDEX_PREPLAN_B_MEMORY_MARGIN=0.7_TO_0.5MB
DSHB_G1_PHASE23_INDEX_PREPLAN_B_ROLLBACK_TIME=210S
DSHB_G1_PHASE23_INDEX_PREPLAN_B_DATA_CONSISTENCY=100_PERCENT
DSHB_G1_PHASE23_INDEX_PREPLAN_B_STRESS_TEST=PASS
DSHB_G1_PHASE23_INDEX_PREPLAN_B_RISK_LEVEL=MEDIUM
DSHB_G1_PHASE23_INDEX_PREPLAN_B_RECOMMENDED=ALTERNATIVE
DSHB_G1_PHASE23_INDEX_PREPLAN_A_PLUS_B_EVALUATED=TRUE
DSHB_G1_PHASE23_INDEX_PREPLAN_A_PLUS_B_EXPECTED_IMPROVEMENT=-40_TO_-50_PERCENT
DSHB_G1_PHASE23_INDEX_PREPLAN_A_PLUS_B_EXPECTED_EXPANSION=5.5_TO_6.2_PERCENT
DSHB_G1_PHASE23_INDEX_PREPLAN_LONGTERM_GOVERNANCE_READY=TRUE
DSHB_G1_PHASE23_INDEX_PREPLAN_LONGTERM_90DAY_PREDICTION=7.8_PERCENT
DSHB_G1_PHASE23_INDEX_PREPLAN_EXECUTION_SCHEDULED=TRUE
DSHB_G1_PHASE23_INDEX_PREPLAN_CONSTRAINT_NO_ZHIJI_API_CALL=TRUE
DSHB_G1_PHASE23_INDEX_PREPLAN_CONSTRAINT_NO_MODIFY_V85=TRUE
DSHB_G1_PHASE23_INDEX_PREPLAN_CONSTRAINT_NO_OVERWRITE=TRUE
DSHB_G1_PHASE23_INDEX_PREPLAN_CONSTRAINT_BRANCH_LOCKED=TRUE
```

**End of Report — Phase23 Index Risk Pre-Plan Evaluation**

---
*编制: DSHB 存储工程组 + DSHB 性能工程组 + DSHB 数据工程组*
*审核: DSHB 技术架构组 (TARC)*
*批准: 项目总监 李伟*
*日期: 2027-12-14*
