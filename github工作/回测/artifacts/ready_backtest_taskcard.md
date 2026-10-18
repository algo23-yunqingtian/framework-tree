# 🔥 点火就绪任务卡片 — DSHA-P65

> **任务**: WDF_FETCH_PAYLOAD_PRE_ASSEMBLY → BACKTEST_READY
> **生成时间**: 2026-10-18 17:22:14 GMT+8
> **状态**: STATIC_STANDBY — 等待DSHC点火
> **REAL_WIND_CALL**: False | **WIND_API_CALLS**: 0
> **Gate**: CLOSED | **Release Permit**: NOT_ISSUED

---

## 📊 标的清单 (7种大宗商品)

| 代码 | 名称 | WSD公式 |
|------|------|---------|
| `CU.SHF` | 沪铜 | =WSD("CU.SHF","CLOSE;VOL;OI;SETTLE","2025-01-01","2026-10-17","Fill=Previous") |
| `ZN.SHF` | 沪锌 | =WSD("ZN.SHF","CLOSE;VOL;OI;SETTLE","2025-01-01","2026-10-17","Fill=Previous") |
| `LC.SHF` | 铝铜比价(铝-沪铜) | =WSD("LC.SHF","CLOSE;VOL;OI;SETTLE","2025-01-01","2026-10-17","Fill=Previous") |
| `PB.SHF` | 沪铅 | =WSD("PB.SHF","CLOSE;VOL;OI;SETTLE","2025-01-01","2026-10-17","Fill=Previous") |
| `SN.SHF` | 沪锡 | =WSD("SN.SHF","CLOSE;VOL;OI;SETTLE","2025-01-01","2026-10-17","Fill=Previous") |
| `NI.SHF` | 沪镍 | =WSD("NI.SHF","CLOSE;VOL;OI;SETTLE","2025-01-01","2026-10-17","Fill=Previous") |
| `AL.SHF` | 沪铝 | =WSD("AL.SHF","CLOSE;VOL;OI;SETTLE","2025-01-01","2026-10-17","Fill=Previous") |

## ⏰ 时间窗口

| 参数 | 值 |
|------|-----|
| 开始 | 2025-01-01 |
| 结束 | 2026-10-17 |
| 频率 | 日频 (DAILY) |
| 预估交易日 | ~430 |
| 采集字段 | CLOSE, VOL, OI, SETTLE |

## 🧬 F007 参数基线

| 参数 | 值 | 锁定状态 |
|------|-----|----------|
| window_days | 60 | ✅ 基准锚点 (35~100验证范围) |
| f19_weight | frozen | 🔒 DSHC锁定 |
| f20_weight | frozen | 🔒 DSHC锁定 |
| cf003_weight | frozen | 🔒 DSHC锁定 |
| decay_factor | frozen | 🔒 DSHC锁定 |
| min_trading_days | 61 | 60 + 1 (窗口+1) |

## ⚙️ 回测开关

| 开关 | 当前值 | 说明 |
|------|--------|------|
| REAL_WIND_CALL | False | 点火后由DSHC设为True |
| WIND_API_CALLS | 0 | 本脚本不触发任何Wind请求 |
| sample_fetch_allow.marker | ❌ 不存在 | 等待点火创建 |
| WDF_ENV_READY.token | ❌ 不存在 | 等待WDF链路验证 |

## 📁 输出路径

| 用途 | 路径 |
|------|------|
| WDF取数配置 | `artifacts/wdf_instrument_fetch_table.json` |
| 字段映射校验 | `artifacts/wdf_to_factor_column_mapping_verify.json` |
| CSV表头模板 | `templates/sample_output_header_template.csv` |
| Dry-Run回执 | `artifacts/dsha_p65_dryrun_check.json` |
| 回测归档目录 | `artifacts/backtest_archive/` |
| 报告模板目录 | `artifacts/report_templates/` |
| 净值曲线 | `artifacts/backtest_archive/{run_id}/net_value_curve.png` |
| IC时序图 | `artifacts/backtest_archive/{run_id}/ic_series.png` |

## 🔴 点火触发条件

> **注意**: 这只是任务卡片文档，**不等于已经触发回测**。
> 真正触发仍然等待以下条件之一：
> 1. `artifacts/sample_output/` 目录出现真实CSV文件
> 2. 创建 `sample_fetch_allow.marker` 点火触发器
> 3. DSHC设置 `REAL_WIND_CALL=True` 并创建 `WDF_ENV_READY.token`

## 📋 因子覆盖状态

| 因子 | 状态 | 所需额外数据源 |
|------|------|---------------|
| F19 (热钱持仓) | HOLD | OI, OI_change (WDF ✅) |
| F20 (关注度) | HOLD | sentiment_score, search_volume (⚠️ 外部源) |
| CF003 (投机情绪) | HOLD | exchange_oi, long_oi, short_oi (⚠️ 外部源) |
| G1 (IC阈值) | CONDITIONAL_PASS | IC_score, returns (派生) |
| G3 (ICIR阈值) | HOLD | rolling_ICIR, IC_std (派生) |
| G7 (泄漏比) | CONDITIONAL_PASS | leakage_score, info_score (派生) |
| F007 (合成因子) | CONDITIONAL_PASS | F19/F20/CF003 scores (下游合成) |

---

**STATIC_STANDBY** — 等待DSHC点火 (创建marker + 设置REAL_WIND_CALL=True + 执行WSS小样采集)
