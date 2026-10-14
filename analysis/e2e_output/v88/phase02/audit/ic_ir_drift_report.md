# V88 Phase02 IC/IR 因子漂移基线报告

> 生成时间: 2026-10-14T21:50:16.769760
> 阶段: V88-Phase02
> 状态: 基线采集中 (等待全量数据入库)

---

## 1. 基线状态

- 建立时间: 2026-10-14T21:50:16.713337
- 指标总数: 0
- IC 最低阈值: 0.03
- IR 最低阈值: 0.5
- 漂移告警阈值: 0.5

## 2. 采集状态

- 数据源: api_cache.db (DSHB 采集入库)
- 采集频率: 每日 1 次
- 指标分类: 同花顺推荐 / 自研产业链 / 交叉引用
- 状态: 等待 DSHB 全量数据入库后启动首次基线计算

## 3. 漂移检测逻辑

1. IC = Spearman rank correlation (factor_value, forward_return)
2. IR = mean(IC_rolling) / std(IC_rolling)  (20 日滚动窗口)
3. 漂移告警: |IC_t - IC_baseline| / std(IC_baseline) > 0.5
4. 最低有效: IC ≥ 0.03, IR ≥ 0.5

## 4. 后续动作

- DSHB 数据入库后 (T+1d~T+3d) 启动首次基线计算
- 建立 146 项指标 IC/IR 基线值
- 区分同花顺推荐 vs 自研产业链指标分类
- 每日增量采集 + 漂移检测
