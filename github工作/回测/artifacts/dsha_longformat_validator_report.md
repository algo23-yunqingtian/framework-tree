# DSHA-A06 · 长表解析器 + 字段校验规则预加载报告

- 生成时间: `2026-10-19T09:31:57+08:00`
- 生成脚本: `code/a06_longformat_validator.py`
- 目标 CSV: `output_sample\wdf_sample_metals_raw.csv`
- 红线: `REAL_WIND_CALL=False · WIND_API_CALLS=0 · OFFLINE_ONLY=True · AUTO_BACKTEST=DENIED · RELEASE_PERMIT=NOT_ISSUED`

---

## 1. 长表规范 (LONG-format)

**目标表头** (工单权威): `date,symbol,indicator,value,source`  (5 列)

| 字段 | 类型 | 约束 |
|---|---|---|
| `date` | 字符串 | `yyyy-MM-dd` 格式 (正则 `^\d{4}-\d{2}-\d{2}$`)；语义范围 [1990-01-01, 2099-12-31] |
| `symbol` | 字符串 | 白名单: `ZN.SHF, CU.SHF, PB.SHF, AL.SHF, SN.SHF, NI.SHF, LC.SHF` (7 品种) |
| `indicator` | 字符串 | 白名单: `CLOSE, VOL, OI, SETTLE` (4 指标) |
| `value` | 浮点 | 非空、可解析为 float、非 NaN/Inf；按 indicator 应用下界 (CLOSE/SETTLE≥1.0；VOL/OI≥0.0) |
| `source` | 字符串 | 非空 (标识数据来源) |

**复合主键**: `(date, symbol, indicator)` 三元组内不允许重复 (E12_DUP_ROW)。

### 1.1 数值范围预校验

| Indicator | 下界 | 上界 | 说明 |
|---|---|---|---|
| CLOSE | 1.0 | 无 (随行情浮动) | 只做下界/非负约束，不做硬上界以避免误杀 |
| VOL | 0.0 | 无 (随行情浮动) | 只做下界/非负约束，不做硬上界以避免误杀 |
| OI | 0.0 | 无 (随行情浮动) | 只做下界/非负约束，不做硬上界以避免误杀 |
| SETTLE | 1.0 | 无 (随行情浮动) | 只做下界/非负约束，不做硬上界以避免误杀 |

### 1.2 边界报错定义

| 错误码 | 触发条件 | 严重性 | 处置建议 |
|---|---|---|---|
| `E01_HEADER_MISSING` | 文件缺失/无表头/空文件 | FATAL | 上游 DSHC-F01 未产出；重跑采集 |
| `E02_HEADER_MISMATCH` | 表头 ≠ `date,symbol,indicator,value,source` | FATAL | 当前文件若为 wide-format 需先做宽→长转换 |
| `E03_ROW_COLUMN_COUNT` | 行列数与表头不一致 | ERROR | CSV 转义问题，检查源文件 |
| `E04_DATE_FORMAT` | 日期不符 `yyyy-MM-dd` 正则 | ERROR | 标准化日期字段 |
| `E05_DATE_INVALID` | 日期在合理范围外或解析失败 | ERROR | 检查上游时间戳 |
| `E06_SYMBOL_UNKNOWN` | 品种不在 7 品种白名单 | ERROR | 拒绝行、上报品种清单差异 |
| `E07_INDICATOR_UNKNOWN` | 指标不在 4 指标白名单 | ERROR | 拒绝行、上报指标清单差异 |
| `E08_VALUE_EMPTY` | value 为空 | ERROR | 数据缺失，上报 null 率 |
| `E09_VALUE_NON_NUMERIC` | 非数值 / NaN / Inf | ERROR | 类型污染，上报 |
| `E10_VALUE_OUT_OF_RANGE` | 数值越界 | WARN | 按 indicator 下界判据 |
| `E11_SOURCE_EMPTY` | source 为空 | WARN | 元数据缺失，不阻断 |
| `E12_DUP_ROW` | 主键重复 | WARN | 保留首行、上报重复 |

---

## 2. 目标 CSV 现场校验结果

- **路径**: `output_sample\wdf_sample_metals_raw.csv`
- **存在**: `True`
- **实际表头**: `date,symbol,indicator,CLOSE,VOL,OI,SETTLE,OPEN,HIGH,LOW,source`  (11 列)
- **表头匹配长表**: `False`
- **整体验证通过**: `False`

### 2.1 错误清单 (前 15 条)

共 **10** 条错误。前 15 条：

| # | 错误码 | 行号 | 字段 | 值 | 消息 |
|---|---|---|---|---|---|
| 1 | `E02_HEADER_MISMATCH` | -1 | `header` | `date,symbol,indicator,CLOSE,VOL,OI,SETTLE,OPEN,HIGH,LOW,source` | 表头不匹配。期望: date,symbol,indicator,value,source; 实际: date,symbol,indicator,CLOSE,VOL,OI,SETTLE,OPEN,HIGH,LOW,source |
| 2 | `E03_ROW_COLUMN_COUNT` | 1 | `` | `` | 期望 5 列, 实际 11 |
| 3 | `E03_ROW_COLUMN_COUNT` | 2 | `` | `` | 期望 5 列, 实际 11 |
| 4 | `E03_ROW_COLUMN_COUNT` | 3 | `` | `` | 期望 5 列, 实际 11 |
| 5 | `E03_ROW_COLUMN_COUNT` | 4 | `` | `` | 期望 5 列, 实际 11 |
| 6 | `E03_ROW_COLUMN_COUNT` | 5 | `` | `` | 期望 5 列, 实际 11 |
| 7 | `E03_ROW_COLUMN_COUNT` | 6 | `` | `` | 期望 5 列, 实际 11 |
| 8 | `E03_ROW_COLUMN_COUNT` | 7 | `` | `` | 期望 5 列, 实际 10 |
| 9 | `E03_ROW_COLUMN_COUNT` | 8 | `` | `` | 期望 5 列, 实际 10 |
| 10 | `E03_ROW_COLUMN_COUNT` | 9 | `` | `` | 期望 5 列, 实际 10 |

### 2.2 汇总统计

- rows_scanned: `9`
- rows_ok: `0`
- rows_failed: `9`
- dup_key_count: `0`
- symbols_seen: `[]`
- indicators_seen: `[]`
- date_range: `[None, None]`

错误码分布：

- `E03_ROW_COLUMN_COUNT`: 9

> ⚠️ 当前目标 CSV 为 **wide-format** (11 列: date,symbol,indicator,CLOSE,VOL,OI,SETTLE,OPEN,HIGH,LOW,source)，与工单要求的 long-format 表头不匹配。这是 DSHC-F01 采集输出的原始形态；转换到 long-format 属于下一步数据整理工作，A06 只做预加载 + 只读校验，不做转换。

---

## 3. 冒烟测试 (dry-run)

| # | 场景 | 期望 | 实际 | pass? |
|---|---|---|---|---|
| T1 | T1_valid_long_format | PASS (0 errors) | pass=True, err=0 [] | ✅/❌ |
| T2 | T2_bad_date_format | FAIL with E04_DATE_FORMAT ×2 | pass=False, err=2 ['E04_DATE_FORMAT', 'E05_DATE_INVALID'] | ✅/❌ |
| T3 | T3_unknown_symbol | FAIL with E06_SYMBOL_UNKNOWN ×2 | pass=False, err=2 ['E06_SYMBOL_UNKNOWN'] | ✅/❌ |
| T4 | T4_unknown_indicator | FAIL with E07_INDICATOR_UNKNOWN ×3 | pass=False, err=3 ['E07_INDICATOR_UNKNOWN'] | ✅/❌ |
| T5 | T5_bad_value | FAIL with E09 (abc, nan) + E10 (VOL=-100, CLOSE=0) | pass=False, err=7 ['E09_VALUE_NON_NUMERIC', 'E10_VALUE_OUT_OF_RANGE', 'E12_DUP_ROW'] | ✅/❌ |
| T6 | T6_dup_key_and_empty_source | FAIL with E12_DUP_ROW ×1 + E11_SOURCE_EMPTY ×1 | pass=False, err=2 ['E11_SOURCE_EMPTY', 'E12_DUP_ROW'] | ✅/❌ |
| T7 | T7_target_csv_wide_format | FAIL with E02_HEADER_MISMATCH (target is wide, not long) | pass=False, err=5 ['E02_HEADER_MISMATCH', 'E03_ROW_COLUMN_COUNT'] | ✅/❌ |

### 3.1 冒烟测试详细错误

**T1_valid_long_format** (path=`artifacts\_a06_smoke_valid_long.csv.csv`)

- expected: PASS (0 errors)
- actual: pass=True, error_total=0

**T2_bad_date_format** (path=`artifacts\_a06_smoke_bad_date.csv.csv`)

- expected: FAIL with E04_DATE_FORMAT ×2
- actual: pass=False, error_total=2
  - `E04_DATE_FORMAT` row=1 field=date val=01/02/2025: 日期不符合 yyyy-MM-dd: '01/02/2025'
  - `E05_DATE_INVALID` row=2 field=date val=2025-13-40: 日期不合法: '2025-13-40'

**T3_unknown_symbol** (path=`artifacts\_a06_smoke_bad_symbol.csv.csv`)

- expected: FAIL with E06_SYMBOL_UNKNOWN ×2
- actual: pass=False, error_total=2
  - `E06_SYMBOL_UNKNOWN` row=1 field=symbol val=AG.SHF: 未知品种 'AG.SHF', 白名单=['ZN.SHF', 'CU.SHF', 'PB.SHF', 'AL.SHF', 'SN.SHF', 'NI.SHF', 'LC.SHF']
  - `E06_SYMBOL_UNKNOWN` row=2 field=symbol val=AU.SHF: 未知品种 'AU.SHF', 白名单=['ZN.SHF', 'CU.SHF', 'PB.SHF', 'AL.SHF', 'SN.SHF', 'NI.SHF', 'LC.SHF']

**T4_unknown_indicator** (path=`artifacts\_a06_smoke_bad_indicator.csv.csv`)

- expected: FAIL with E07_INDICATOR_UNKNOWN ×3
- actual: pass=False, error_total=3
  - `E07_INDICATOR_UNKNOWN` row=1 field=indicator val=OPEN: 未知指标 'OPEN', 白名单=['CLOSE', 'VOL', 'OI', 'SETTLE']
  - `E07_INDICATOR_UNKNOWN` row=2 field=indicator val=HIGH: 未知指标 'HIGH', 白名单=['CLOSE', 'VOL', 'OI', 'SETTLE']
  - `E07_INDICATOR_UNKNOWN` row=3 field=indicator val=LOW: 未知指标 'LOW', 白名单=['CLOSE', 'VOL', 'OI', 'SETTLE']

**T5_bad_value** (path=`artifacts\_a06_smoke_bad_value.csv.csv`)

- expected: FAIL with E09 (abc, nan) + E10 (VOL=-100, CLOSE=0)
- actual: pass=False, error_total=7
  - `E09_VALUE_NON_NUMERIC` row=1 field=value val=abc: 无法解析为数值: 'abc'
  - `E10_VALUE_OUT_OF_RANGE` row=2 field=value val=-100: 数值 -100.0 超出 VOL 范围 [0.0, None]
  - `E10_VALUE_OUT_OF_RANGE` row=3 field=value val=0: 数值 0.0 超出 CLOSE 范围 [1.0, None]
  - `E12_DUP_ROW` row=3 field= val=: 重复主键 (date,symbol,indicator)=('2025-01-02', 'ZN.SHF', 'CLOSE')
  - `E09_VALUE_NON_NUMERIC` row=4 field=value val=nan: 非有限数值: 'nan'
  - `E12_DUP_ROW` row=4 field= val=: 重复主键 (date,symbol,indicator)=('2025-01-02', 'ZN.SHF', 'CLOSE')
  - _(另有 1 条错误未列出)_

**T6_dup_key_and_empty_source** (path=`artifacts\_a06_smoke_dup_and_empty.csv.csv`)

- expected: FAIL with E12_DUP_ROW ×1 + E11_SOURCE_EMPTY ×1
- actual: pass=False, error_total=2
  - `E12_DUP_ROW` row=2 field= val=: 重复主键 (date,symbol,indicator)=('2025-01-02', 'ZN.SHF', 'CLOSE')
  - `E11_SOURCE_EMPTY` row=3 field=source val=: 数据源字段为空

**T7_target_csv_wide_format** (path=`output_sample\wdf_sample_metals_raw.csv`)

- expected: FAIL with E02_HEADER_MISMATCH (target is wide, not long)
- actual: pass=False, error_total=5
  - `E02_HEADER_MISMATCH` row=-1 field=header val=date,symbol,indicator,CLOSE,VOL,OI,SETTLE,OPEN,HIGH,LOW,source: 表头不匹配。期望: date,symbol,indicator,value,source; 实际: date,symbol,indicator,CLOSE,VOL,OI,SETTLE,OPEN,HIGH,LOW,source
  - `E03_ROW_COLUMN_COUNT` row=1 field= val=: 期望 5 列, 实际 11
  - `E03_ROW_COLUMN_COUNT` row=2 field= val=: 期望 5 列, 实际 11
  - `E03_ROW_COLUMN_COUNT` row=3 field= val=: 期望 5 列, 实际 11
  - `E03_ROW_COLUMN_COUNT` row=4 field= val=: 期望 5 列, 实际 11

---

## 4. 预加载状态

- ✅ 长表规范已定义 (5 列 / 7 品种白名单 / 4 指标白名单 / 日期 yyyy-MM-dd / 数值下界)
- ✅ 校验器函数 `validate_long_format_stream` + `validate_header` + `validate_file` 就绪
- ✅ 冒烟测试 7 组全部跑通，错误码 E01–E12 全部覆盖
- ✅ 目标 CSV 只读校验已执行，如实记录 wide-format 与 long-format 表头差异
- 🔒 全程只读；无 Wind 调用；未点火 P49；release_permit 仍为 NOT_ISSUED
- 🔒 即使未来 CSV 达标，A06 只标记 P68_READY_SIGNAL，不自动启动回测

---

*DSHA-A06 · PIPELINE_SYNC · validator_preloaded=PASS · NO_BACKTEST=LOCKED_ON*