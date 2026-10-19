# DSHA-P49 · 因子备选库清单 (Factor Candidate List)

> **文档ID**: DSHA-P49-PREP-FACTOR-LIB  
> **生成时间**: 2026-10-19  
> **基线**: `feature/v88-g1` HEAD=`19e80cb`  
> **令牌**: DSHA-P49-PREP-TOKEN  
> **状态**: PREPARED  
> **关联复盘**: TODO-02 (因子迭代任务)  
> **目标**: 扩充P49原始3因子(momentum_20d, spread_cs, oi_momentum_7d)的信号维度，提升策略Alpha

---

## 目录

- [1. P49 当前因子基线](#1-p49-当前因子基线)
- [2. 波动率因子族 (Volatility Factors)](#2-波动率因子族-volatility-factors)
- [3. 持仓量加速因子族 (OI Acceleration Factors)](#3-持仓量加速因子族-oi-acceleration-factors)
- [4. 跨品种价差因子族 (Cross-Commodity Spread Factors)](#4-跨品种价差因子族-cross-commodity-spread-factors)
- [5. 综合优先级矩阵](#5-综合优先级矩阵)
- [6. 预期信号组合方案](#6-预期信号组合方案)
- [7. 实现依赖与路线图](#7-实现依赖与路线图)

---

## 1. P49 当前因子基线

P49回测定义7个因子，实际信号使用其中3个。

### 1.1 因子定义

| # | 因子ID | 定义 | 计算公式 | 数据源 | 有效行/品种 | 策略中使用 |
|---|--------|------|----------|--------|------------|-----------|
| F01 | `spread_cs` | 收盘-结算价差 | `close - settle` | CLOSE, SETTLE | 400/400 | ✅ 信号 |
| F02 | `oi_level` | 持仓量水平 | `oi` | OI | 400/400 | ❌ 未用 |
| F03 | `oi_change_1d` | 持仓量日变化 | `oi.diff(1)` | OI | 400/400 | ❌ 未用 |
| F04 | `oi_change_rate_7d` | 持仓量7日变化率 | `oi.pct_change(7)` | OI | 400/400 | ❌ 未用 |
| F05 | `spread_pct` | 价差率(%) | `(close - settle) / close * 100` | CLOSE, SETTLE | 400/400 | ❌ 未用 |
| F06 | `contract_switch_flag` | 主力合约切换标记 | `abs(oi.diff(1)) > rolling_mean * 3` | OI | 400/400 | ❌ 未用 |
| F07 | `momentum_20d` | 20日价格动量 | `close.pct_change(20)` | CLOSE | 380/400 | ✅ 信号 |

### 1.2 信号生成公式

```
signal = (momentum_norm + spread_norm + oi_momentum_norm) / 3
```

其中:
- `momentum_norm` = z-score归一化(rolling 20d mean)
- `spread_norm` = z-score归一化(spread_cs)
- `oi_momentum_norm` = z-score归一化(oi.pct_change(7))

### 1.3 策略执行规则

```
if signal > 0 → Long(+1)
if signal < 0 → Short(-1)
if signal = 0 → Flat(0)
```

**问题**: 3因子等权复合，信号维度不足，胜率44.7%，P/L=0.92，全品种负收益。

---

## 2. 波动率因子族 (Volatility Factors)

波动率因子捕捉市场波动状态，辅助判断信号可靠性和仓位管理。

### F08 · 已实现波动率 (Realized Volatility)

| 项目 | 值 |
|------|-----|
| **因子ID** | `realized_vol_20d` |
| **定义** | 20日滚动标准差×√252 年化 |
| **公式** | `daily_ret.std(20) * sqrt(252)` |
| **输入数据** | CLOSE (已有) |
| **依赖关系** | 无 |
| **预期效果** | 高波动期降低仓位, 低波动期提高仓位; 过滤噪声信号 |
| **实现复杂度** | ⭐ 低 |
| **优先级** | 🟡 P1 |
| **建议窗口** | 20日 (与momentum一致) |
| **阈值参考** | 年化波动率 > 40% 视为高波动 |

```python
# 伪代码
daily_return = close.pct_change()
realized_vol_20d = daily_return.rolling(20).std() * math.sqrt(252)
```

### F09 · 波动率变化率 (Volatility Change Rate)

| 项目 | 值 |
|------|-----|
| **因子ID** | `vol_regime_change` |
| **定义** | 当前波动率相对于5日均值的变化率 |
| **公式** | `realized_vol_20d.pct_change(5)` |
| **输入数据** | CLOSE (已有) |
| **依赖关系** | 依赖F08 |
| **预期效果** | 捕捉波动率急升/急降拐点, 作为风险预警 |
| **实现复杂度** | ⭐ 低 |
| **优先级** | 🟡 P1 |
| **建议窗口** | 20日(内层) + 5日(外层) |
| **阈值参考** | 变化率 > +50% 视为波动率急升 |

```python
# 伪代码
vol_regime_change = realized_vol_20d.pct_change(5)
```

### F10 · ATR百分比 (ATR Percentage)

| 项目 | 值 |
|------|-----|
| **因子ID** | `atr_pct_14` |
| **定义** | 14日真实波幅 / 收盘价 × 100 |
| **公式** | `(TR_14 / close) * 100`, 其中 `TR = max(high-low, abs(high-prev_close), abs(low-prev_close))` |
| **输入数据** | CLOSE (已有), HIGH/LOW (需补充) |
| **依赖关系** | 需补充HIGH/LOW数据 |
| **预期效果** | 更精确衡量波动区间, 动态止损失效 |
| **实现复杂度** | ⭐⭐ 中 (需HIGH/LOW) |
| **优先级** | 🟢 P2 (数据不足) |
| **建议窗口** | 14日 (标准ATR周期) |

```python
# 伪代码 (需HIGH/LOW)
tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
atr_14 = tr.rolling(14).mean()
atr_pct_14 = atr_14 / close * 100
```

### F11 · 波动率目标仓位 (Vol Target Position)

| 项目 | 值 |
|------|-----|
| **因子ID** | `vol_target_weight` |
| **定义** | 基于目标年化波动率的动态仓位 |
| **公式** | `weight = min(max_cap, target_vol / realized_vol_20d)` |
| **输入数据** | CLOSE (已有) |
| **依赖关系** | 依赖F08 |
| **预期效果** | 高波动降低仓位, 低波动提高仓位, 实现等风险预算 |
| **实现复杂度** | ⭐⭐ 中 |
| **优先级** | 🟡 P1 |
| **目标波动率** | 15% (年化) |
| **仓位上限** | 100% (全仓) |

```python
# 伪代码
target_vol = 0.15
max_cap = 1.0
vol_target_weight = np.clip(target_vol / realized_vol_20d, 0, max_cap)
```

---

## 3. 持仓量加速因子族 (OI Acceleration Factors)

持仓量加速因子捕捉资金流入/流出的二阶导数信号，反映市场情绪变化的加速度。

### F12 · 持仓量变化加速 (OI Change Acceleration)

| 项目 | 值 |
|------|-----|
| **因子ID** | `oi_change_accel_7d` |
| **定义** | 7日持仓量变化率的加速度 |
| **公式** | `(oi_change_rate_7d - oi_change_rate_7d.shift(7))` |
| **输入数据** | OI (已有) |
| **依赖关系** | 依赖P49现有F04 |
| **预期效果** | 捕捉持仓变化加速/减速拐点, 反映资金情绪转向 |
| **实现复杂度** | ⭐ 低 |
| **优先级** | 🟡 P1 |
| **建议窗口** | 7日 (与OI动量一致) |
| **信号逻辑** | accel > 0 → 多头加速; accel < 0 → 空头加速 |

```python
# 伪代码
oi_change_rate_7d = oi.pct_change(7)
oi_change_accel_7d = oi_change_rate_7d.diff(7)
```

### F13 · 持仓量斜率 (OI Slope)

| 项目 | 值 |
|------|-----|
| **因子ID** | `oi_slope_14d` |
| **定义** | 14日持仓量线性回归斜率 |
| **公式** | `linreg(oi[t-14:t], t)[slope]` |
| **输入数据** | OI (已有) |
| **依赖关系** | 无 |
| **预期效果** | 平滑持仓趋势方向, 避免单日噪声 |
| **实现复杂度** | ⭐ 低 |
| **优先级** | 🟡 P1 |
| **建议窗口** | 14日 |
| **信号逻辑** | slope > 0 → 持仓上升(看涨); slope < 0 → 持仓下降(看跌) |

```python
# 伪代码
from scipy.stats import linregress
def oi_slope(series, window=14):
    slopes = []
    for i in range(len(series)):
        if i >= window - 1:
            window_data = series.iloc[i-window+1:i+1]
            if not window_data.isna().any():
                t = np.arange(window)
                slope, _, _, _, _ = linregress(t, window_data.values)
                slopes.append(slope)
            else:
                slopes.append(np.nan)
        else:
            slopes.append(np.nan)
    return pd.Series(slopes, index=series.index)
oi_slope_14d = oi_slope(oi, 14)
```

### F14 · 持仓量占比偏离 (OI Deviation from MA)

| 项目 | 值 |
|------|-----|
| **因子ID** | `oi_deviation_from_ma20` |
| **定义** | 当前持仓量与20日均值的偏离度 |
| **公式** | `(oi - oi.rolling(20).mean()) / oi.rolling(20).std()` |
| **输入数据** | OI (已有) |
| **依赖关系** | 无 |
| **预期效果** | 检测持仓异常偏离, 捕捉主力建仓/平仓动作 |
| **实现复杂度** | ⭐ 低 |
| **优先级** | 🟢 P2 |
| **建议窗口** | 20日 |
| **阈值参考** | z > 2 视为异常建仓, z < -2 视为异常平仓 |

```python
# 伪代码
oi_ma20 = oi.rolling(20).mean()
oi_std20 = oi.rolling(20).std()
oi_deviation_from_ma20 = (oi - oi_ma20) / oi_std20
```

---

## 4. 跨品种价差因子族 (Cross-Commodity Spread Factors)

跨品种因子利用6个SHFE金属品种间的相对关系，构建配对交易和相对强弱信号。

### F15 · 跨品种相对强弱 (Cross-Sectional Momentum)

| 项目 | 值 |
|------|-----|
| **因子ID** | `cross_sectional_momentum_20d` |
| **定义** | 品种20日动量在6品种横截面中的标准化排名 |
| **公式** | `rank(momentum_20d, across symbols) / 6 * 2 - 1` |
| **输入数据** | CLOSE (6品种, 已有) |
| **依赖关系** | 依赖F07 (momentum_20d) |
| **预期效果** | 做多强品种, 做空弱品种, 实现市场中性 |
| **实现复杂度** | ⭐⭐ 中 |
| **优先级** | 🟡 P1 |
| **建议窗口** | 20日 |
| **信号逻辑** | 排名靠前的品种做多, 排名靠后的品种做空 |

```python
# 伪代码 (横截面标准化)
# 按日期分组, 计算每个品种在该日6品种中的排名
momentum_df = df.groupby('date')['momentum_20d'].transform(
    lambda x: (x.rank() - 1) / (len(x) - 1) * 2 - 1
)
# momentum_df: 每日6品种的相对强弱 (-1 到 +1)
cross_sectional_momentum_20d = momentum_df
```

### F16 · 跨品种配对价差 (Pair Spread)

| 项目 | 值 |
|------|-----|
| **因子ID** | `pair_spread_cu_zn` |
| **定义** | 铜-锌配对价差 (CU/ZN) |
| **公式** | `close_cu / close_zn - 1` (或 z-score标准化后之差) |
| **输入数据** | CLOSE (CU, ZN, 已有) |
| **依赖关系** | 无 |
| **预期效果** | 均值回归套利, 配对交易 |
| **实现复杂度** | ⭐⭐ 中 |
| **优先级** | 🟢 P2 |
| **配对选择** | CU-ZN (同板块), CU-PB (同板块) |
| **阈值参考** | z > +2 做空CU做多ZN; z < -2 做多CU做空ZN |

```python
# 伪代码 (以CU-ZN为例)
ratio = close_cu / close_zn
ratio_ma20 = ratio.rolling(20).mean()
ratio_std20 = ratio.rolling(20).std()
pair_spread_z = (ratio - ratio_ma20) / ratio_std20
```

### F17 · 品种间相关性变化 (Correlation Regime Change)

| 项目 | 值 |
|------|-----|
| **因子ID** | `cross_corr_change` |
| **定义** | CU与其余5品种的相关性变化 |
| **公式** | `corr(close_cu, close_other, 20d).pct_change(10)` |
| **输入数据** | CLOSE (6品种, 已有) |
| **依赖关系** | 无 |
| **预期效果** | 相关性突变预示市场结构变化, 作为风险预警 |
| **实现复杂度** | ⭐⭐⭐ 高 |
| **优先级** | 🟢 P2 |
| **建议窗口** | 20日(内层) + 10日(外层) |

```python
# 伪代码
# 计算CU与每个品种的相关性, 然后取平均值
cross_corr = {}
for sym in ['ZN.SHF', 'PB.SHF', 'AL.SHF', 'NI.SHF', 'SN.SHF']:
    cross_corr[sym] = close_cu.rolling(20).corr(close[sym])
avg_cross_corr = pd.DataFrame(cross_corr).mean(axis=1)
cross_corr_change = avg_cross_corr.pct_change(10)
```

### F18 · 品种动量离散度 (Momentum Dispersion)

| 项目 | 值 |
|------|-----|
| **因子ID** | `momentum_dispersion` |
| **定义** | 6品种动量的横截面标准差 |
| **公式** | `std(momentum_20d, across 6 symbols) per day` |
| **输入数据** | CLOSE (6品种, 已有) |
| **依赖关系** | 依赖F07 |
| **预期效果** | 高离散度=品种分化严重=机会多; 低离散度=趋势统一=风险低 |
| **实现复杂度** | ⭐ 低 |
| **优先级** | 🟢 P2 |
| **建议窗口** | 20日 |

```python
# 伪代码
momentum_dispersion = df.groupby('date')['momentum_20d'].std().reset_index()
# 将离散度作为整体市场状态指标
# dispersion > 2std → 品种分化大, 适合配对交易
# dispersion < 0.5std → 品种趋同, 适合统一方向
```

---

## 5. 综合优先级矩阵

| 因子ID | 名称 | 数据需求 | 复杂度 | 预期效果 | 依赖项 | 优先级 | 实现难度 | 风险 |
|--------|------|----------|--------|----------|--------|--------|----------|------|
| F08 | 已实现波动率 | CLOSE ✅ | ⭐ 低 | 高 | 无 | 🟡 P1 | 1h | 低 |
| F09 | 波动率变化率 | CLOSE ✅ | ⭐ 低 | 中 | F08 | 🟡 P1 | 0.5h | 低 |
| F10 | ATR百分比 | CLOSE+HIGH+LOW ❌ | ⭐⭐ 中 | 高 | HIGH/LOW数据 | 🟢 P2 | 需采集 | 中 |
| F11 | 波动率目标仓位 | CLOSE ✅ | ⭐⭐ 中 | 高 | F08 | 🟡 P1 | 2h | 中 |
| F12 | OI变化加速 | OI ✅ | ⭐ 低 | 高 | F04 | 🟡 P1 | 0.5h | 低 |
| F13 | OI斜率 | OI ✅ | ⭐ 低 | 高 | 无 | 🟡 P1 | 1h | 低 |
| F14 | OI偏离度 | OI ✅ | ⭐ 低 | 中 | 无 | 🟢 P2 | 0.5h | 低 |
| F15 | 跨品种相对强弱 | CLOSE ✅ (6品种) | ⭐⭐ 中 | 高 | F07 | 🟡 P1 | 2h | 中 |
| F16 | 配对价差 | CLOSE ✅ (CU+ZN) | ⭐⭐ 中 | 高 | 无 | 🟢 P2 | 2h | 中 |
| F17 | 相关性变化 | CLOSE ✅ (6品种) | ⭐⭐⭐ 高 | 中 | 无 | 🟢 P2 | 4h | 高 |
| F18 | 动量离散度 | CLOSE ✅ (6品种) | ⭐ 低 | 中 | F07 | 🟢 P2 | 0.5h | 低 |

**P1优先级因子 (6个)**: F08, F09, F11, F12, F13, F15  
**P2优先级因子 (5个)**: F10, F14, F16, F17, F18

---

## 6. 预期信号组合方案

### 方案A: 保守增强 (在P49基础上最小改动)

```
signal_A = (momentum_20d + spread_cs + oi_momentum_7d + realized_vol_signal) / 4

其中:
  realized_vol_signal = -realized_vol_20d_normalized  # 波动率越低, 信号越强(负相关)
```

- 保留P49原始3因子
- 新增波动率因子(反向加权: 低波动期增强信号)
- 保持等权
- 预计效果: 波动率异常期的噪声信号被过滤

### 方案B: 均衡增强 (增加OI维度)

```
signal_B = (momentum_20d + spread_cs + oi_momentum_7d + oi_change_accel + oi_slope) / 5

其中:
  oi_change_accel = oi_change_accel_7d  # 持仓加速
  oi_slope = oi_slope_14d                # 持仓趋势
```

- 保留P49原始3因子
- 新增2个OI因子, 增强持仓量维度
- 预计效果: 捕捉资金流入流出加速信号

### 方案C: 全面增强 (加入跨品种)

```
signal_C = (momentum_20d + spread_cs + oi_momentum_7d 
           + realized_vol_signal + oi_change_accel 
           + cross_sectional_momentum) / 6

其中:
  realized_vol_signal = -realized_vol_20d_normalized
  cross_sectional_momentum = cross_sectional_momentum_20d
```

- 3个价格因子 + 2个持仓因子 + 1个波动率因子
- 引入横截面相对强弱
- 预计效果: 多维度信号互补, 但需优化权重

### 方案D: 市场中性配对 (仅用于配对交易)

```
pair_signal = cross_sectional_momentum_20d  # 横截面排名信号
pair_weights = -pair_signal * vol_target_weight  # 波动率目标仓位
```

- 做多强品种, 做空弱品种
- 波动率目标仓位管理
- 市场中性, 无方向性风险
- 预计效果: 与P49方向策略互补

---

## 7. 实现依赖与路线图

### 7.1 数据依赖

| 因子 | 需要数据 | 当前可用 | 缺口 |
|------|----------|----------|------|
| F08-F09, F11 | CLOSE | ✅ 400行/品种 | 无 |
| F10 | CLOSE, HIGH, LOW | ✅ CLOSE, ❌ HIGH/LOW | HIGH/LOW数据 |
| F12, F13, F14 | OI | ✅ 400行/品种 | 无 |
| F15-F18 | CLOSE (6品种) | ✅ 6×400行 | 无 |

**数据修复阻塞项**: 
- F10 (ATR) 需补充HIGH/LOW数据 → 依赖DSHC采集脚本扩展
- 所有因子需VOL修复 → 依赖TODO-01

### 7.2 实现路线图

```
Phase 1 (立即可做, 仅CLOSE+OI):
  └─ F08 (波动率), F09 (波动率变化率), F11 (波动率目标)
  └─ F12 (OI加速), F13 (OI斜率)
  └─ F15 (跨品种相对强弱), F18 (动量离散度)
  实现耗时: ~6h
  预期效果: 因子从3维扩展至9维, 信号维度+200%

Phase 2 (需补充数据):
  └─ F10 (ATR百分比) → 需HIGH/LOW数据
  └─ F14 (OI偏离度), F16 (配对价差) → 立即可做但优先级低
  实现耗时: ~3h
  预期效果: 进一步精细化波动率和OI信号

Phase 3 (高级因子):
  └─ F17 (相关性变化) → 计算复杂度较高
  └─ 因子权重优化 (非等权) → 需历史数据回归
  实现耗时: ~4h
  预期效果: 最优信号组合
```

### 7.3 预期效果估算

| 优化项 | 当前值 | 预期改善 | 置信度 |
|--------|--------|----------|--------|
| 因子维度 | 3 | 9 | — |
| 胜率 | 44.7% | 50-55% | ⭐⭐ |
| 盈亏比 | 0.92 | 1.1-1.3 | ⭐⭐ |
| 年化收益 | -37.7% | -5% ~ +15% | ⭐ |
| 最大回撤 | -42.1% | -20% ~ -30% | ⭐⭐ |

> **注**: 预期改善基于因子增强文献的统计推断，实际效果需通过实验组回测验证。置信度: ⭐⭐⭐=高, ⭐⭐=中, ⭐=低。

---

## 附录A: 因子实现代码草稿

以下代码片段可作为FACTOR_EXTRACT_V1 Skill的参考实现。

### 波动率因子

```python
def extract_volatility_factors(df: pd.DataFrame) -> pd.DataFrame:
    """从对齐数据中提取波动率因子"""
    df = df.copy()
    for sym in df['symbol'].unique():
        mask = df['symbol'] == sym
        close = df.loc[mask, 'close']
        
        daily_ret = close.pct_change()
        
        # F08: 已实现波动率
        df.loc[mask, 'realized_vol_20d'] = daily_ret.rolling(20).std() * math.sqrt(252)
        
        # F09: 波动率变化率
        df.loc[mask, 'vol_regime_change'] = df.loc[mask, 'realized_vol_20d'].pct_change(5)
        
        # F11: 波动率目标仓位
        target_vol = 0.15
        df.loc[mask, 'vol_target_weight'] = np.clip(
            target_vol / df.loc[mask, 'realized_vol_20d'], 0, 1.0
        )
    return df
```

### OI加速因子

```python
def extract_oi_acceleration_factors(df: pd.DataFrame) -> pd.DataFrame:
    """从对齐数据中提取持仓量加速因子"""
    df = df.copy()
    for sym in df['symbol'].unique():
        mask = df['symbol'] == sym
        oi = df.loc[mask, 'oi']
        
        # F12: OI变化加速
        oi_change_rate_7d = oi.pct_change(7)
        df.loc[mask, 'oi_change_accel_7d'] = oi_change_rate_7d.diff(7)
        
        # F13: OI斜率 (简化线性回归)
        oi_values = oi.values
        slopes = []
        for i in range(len(oi_values)):
            if i >= 13:
                window = oi_values[i-13:i+1]
                if not np.any(np.isnan(window)):
                    t = np.arange(14)
                    slope = np.polyfit(t, window, 1)[0]
                    slopes.append(slope)
                else:
                    slopes.append(np.nan)
            else:
                slopes.append(np.nan)
        df.loc[mask, 'oi_slope_14d'] = slopes
    return df
```

### 跨品种因子

```python
def extract_cross_sectional_factors(df: pd.DataFrame) -> pd.DataFrame:
    """从对齐数据中提取跨品种因子"""
    df = df.copy()
    
    # F15: 跨品种相对强弱 (横截面标准化)
    df['cross_sectional_momentum_20d'] = df.groupby('date')['momentum_20d'].transform(
        lambda x: (x.rank() - 1) / (len(x) - 1) * 2 - 1
    )
    
    # F18: 动量离散度
    dispersion = df.groupby('date')['momentum_20d'].std().reset_index()
    dispersion.columns = ['date', 'momentum_dispersion']
    df = df.merge(dispersion, on='date', how='left')
    
    return df
```

---

## 附录B: 与复盘文档TODO-02的对应关系

| 复盘TODO子任务 | 对应因子 | 状态 |
|---------------|----------|------|
| 2.1 波动率因子实现 | F08, F09, F10, F11 | 因子定义 ✅ |
| 2.2 跨品种相对强弱因子 | F15, F16, F17, F18 | 因子定义 ✅ |
| 2.3 持仓量变化加速因子 | F12, F13, F14 | 因子定义 ✅ |
| 2.4 价差率动量因子 | spread_pct_momentum (基于F05) | 待补充 |
| 2.5 周度调仓机制 | — (参数配置) | 见optimization_params.json |
| 2.6 信号阈值过滤 | — (参数配置) | 见optimization_params.json |
| 2.7 波动率目标仓位 | F11 | 因子定义 ✅ |
| 2.8 回撤控制策略 | — (参数配置) | 见optimization_params.json |
| 2.9 品种权重上限 | — (参数配置) | 见optimization_params.json |
| 2.10 优化后重新回测 | — (执行) | 依赖以上全部完成 |

---

> **回执关联**: DSHA_P49_PREP  
> **下一步**: FACTOR_EXTRACT_V1 Skill就绪后，基于本清单实现因子提取模块
