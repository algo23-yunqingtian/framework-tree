# DATA QUALITY CHECKLIST — 数据质量常态化检查项
## DSHC-DATA-INCREMENT-PIPELINE | 2026-10-19

> **Status:** PREPARED — Rules frozen. Checklist applies to all V2/V3 longtable assets.
> **Scope:** 9 instruments × 6 indicators × daily frequency, long-format CSV.

---

## 1. 字段规则 (Field Rules) — CRITICAL

| # | 检查项 | 规则 | 严重性 | 处置 |
|---|--------|------|--------|------|
| F-01 | **volume 小写** | WSD 查询字段必须为 `volume` (lowercase)，禁止写成 `vol` | **FATAL** | `vol` 返回 0 行；`volume` 返回完整数据。DSHC-VOL-FULL-COLLECT 已确认修复 |
| F-02 | **指标大写** | 其余指标必须大写: `CLOSE`, `HIGH`, `LOW`, `OI`, `SETTLE` | ERROR | WSD 字段名大小写敏感 |
| F-03 | **CSV indicator 列** | CSV 长表中 indicator 列使用 `VOL` (uppercase)，对应 WSD 字段 `volume` | WARN | 这是正常的映射差异，非错误 |
| F-04 | **字段顺序** | 推荐顺序: CLOSE, HIGH, LOW, OI, SETTLE, VOL | INFO | 不影响数据正确性 |
| F-05 | **CSV 表头** | 长表必须为: `date,symbol,indicator,value,source` (5列) | **FATAL** | 宽表需要转换为长表后才能用于校验 |
| F-06 | **value 类型** | value 列必须为数值 (float)，禁止 NaN/Inf/空值 | ERROR | 空值 = 数据缺失，上报 |

### 1.1 WSD 字段配置表

| CSV indicator | WSD 查询字段 | 大小写 | 说明 |
|---------------|-------------|--------|------|
| `CLOSE` | `CLOSE` | 大写 | 收盘价 |
| `HIGH` | `HIGH` | 大写 | 最高价 |
| `LOW` | `LOW` | 大写 | 最低价 |
| `OI` | `OI` | 大写 | 持仓量 |
| `SETTLE` | `SETTLE` | 大写 | 结算价 |
| `VOL` | `volume` | ⚠️ 小写 | 成交量 — `vol` 无效 |

---

## 2. 品种黑白名单 (Instrument Black/Whitelist) — CRITICAL

| # | 检查项 | 规则 | 严重性 | 处置 |
|---|--------|------|--------|------|
| B-01 | **白名单 (9品种)** | 仅允许: AL.SHF, CU.SHF, HC.SHF, NI.SHF, PB.SHF, RB.SHF, SN.SHF, ZN.SHF, LC.GFE | **FATAL** | 不在白名单的品种直接拒绝 |
| B-02 | **LC.SHF 永久黑名单** | LC.SHF 已标记为 INVALID，Wind 上无数据，所有指标返回 0 行 | **FATAL** | 自动拦截，不发起查询，不写入分片 |
| B-03 | **LC.GFE 唯一有效绑定** | LC.GFE 是唯一有效的 LC 系列绑定 (GFE 交易所) | WARN | 已确认 BOUND_OK，432行 × 6指标全可用 |
| B-04 | **交易所后缀校验** | SHFE 品种必须为 `.SHF`，GFE 品种必须为 `.GFE` | ERROR | 后缀错误 = 交易所绑定不匹配 |

### 2.1 交易所绑定表

| 品种 | 交易所 | 后缀 | 状态 | 说明 |
|------|--------|------|------|------|
| AL.SHF | SHFE | .SHF | ✅ VALID | 沪铝 |
| CU.SHF | SHFE | .SHF | ✅ VALID | 沪铜 |
| HC.SHF | SHFE | .SHF | ✅ VALID | 热轧卷板 |
| NI.SHF | SHFE | .SHF | ✅ VALID | 沪镍 |
| PB.SHF | SHFE | .SHF | ✅ VALID | 沪铅 |
| RB.SHF | SHFE | .SHF | ✅ VALID | 螺纹钢 |
| SN.SHF | SHFE | .SHF | ✅ VALID | 沪锡 |
| ZN.SHF | SHFE | .SHF | ✅ VALID | 沪锌 |
| LC.GFE | GFE | .GFE | ✅ VALID | 碳酸锂 (唯一有效 LC) |
| ~~LC.SHF~~ | ~~SHFE~~ | ~~.SHF~~ | ❌ **INVALID** | **永久黑名单** — Wind 上无数据 |

---

## 3. 完整性校验 (Completeness) — CRITICAL

| # | 检查项 | 规则 | 严重性 | 处置 |
|---|--------|------|--------|------|
| C-01 | **6指标齐全** | 每只品种每日必须 6 个指标齐全: CLOSE, HIGH, LOW, OI, SETTLE, VOL | **FATAL** | 缺少任何指标 = 数据不完整，需补采 |
| C-02 | **无空行** | 每行必须有完整 5 列: date, symbol, indicator, value, source | ERROR | 空行直接删除 |
| C-03 | **无零值异常** | VOL/OI 不应为 0 (除非休市)；CLOSE/SETTLE/HIGH/LOW 不应为 0 或负值 | WARN | 零值可能是数据错误，需人工确认 |
| C-04 | **日期连续** | 交易日日期不应有断档 (节假日除外) | WARN | 断档需确认是否数据缺失 |
| C-05 | **source 标签** | 每行 source 列必须非空 (推荐: `WDF-GUI`) | WARN | 缺失来源标识 |

### 3.1 预期数据规模

| 维度 | 值 | 说明 |
|------|-----|------|
| 品种数 | 9 | 白名单品种 |
| 指标数 | 6 | CLOSE, HIGH, LOW, OI, SETTLE, VOL |
| 交易日 | 432 | 2025-01-02 → 2026-10-19 |
| 预期总行数 | 23,328 | 9 × 6 × 432 |
| V1 长表行数 | 7,362 | 6 SHFE 金属 × 4 指标 × 308 日 |
| V2 长表行数 | 23,328 | 9 品种 × 6 指标 × 432 日 |

---

## 4. 防重复 (Deduplication)

| # | 检查项 | 规则 | 严重性 | 处置 |
|---|--------|------|--------|------|
| D-01 | **主键唯一** | (date, symbol, indicator) 三元组内不允许重复 | WARN | 保留首行，上报重复 |
| D-02 | **增量防重** | 合并时按 (date, symbol) 去重，避免重复拉取 | ERROR | 增量脚本自动去重 |
| D-03 | **断点续传** | 从 last_date 开始查询，确保不遗漏不重复 | INFO | 增量脚本自动处理 |

---

## 5. 数据溯源 (Data Provenance)

| # | 检查项 | 规则 | 严重性 | 处置 |
|---|--------|------|--------|------|
| P-01 | **SHA 快照** | 每次增量运行必须生成 SHA256 快照 | ERROR | 无快照 = 无法追溯 |
| P-02 | **审计日志** | 每次运行必须写入 tracking_monitor_audit.jsonl | ERROR | 无审计 = 无法回溯 |
| P-03 | **manifest 升级** | 每次增量运行必须更新 data_asset_manifest.json | ERROR | 无更新 = 台账不完整 |
| P-04 | **分片保留** | 原始增量分片文件必须保留，不删除 | WARN | 分片是审计追溯的基础 |
| P-05 | **V2 只读** | 原始 V2 长表禁止修改 | **FATAL** | 修改 V2 = 数据污染 |

---

## 6. 红线清单 (Red Lines)

| 红线 | 值 | 状态 |
|------|-----|------|
| WIND_API_CALLS | 0 (仅增量拉取阶段) | ✅ 已固化 |
| OFFLINE_ONLY | True (校验/合并阶段) | ✅ 已固化 |
| AUTO_BACKTEST | DENIED | ✅ 已固化 |
| RELEASE_PERMIT | NOT_ISSUED | ✅ 已固化 |
| GATE | CLOSED/HOLD | ✅ 已固化 |
| V1_FROZEN | True | ✅ 已固化 |
| F01_A06_UNCHANGED | True | ✅ 已固化 |
| LC_SHF_PERMANENTLY_BLACKLISTED | True | ✅ 已固化 |
| CSV_READONLY | True (V2 只读) | ✅ 已固化 |

---

## 7. 检查项总览

| 类别 | 检查项数 | FATAL | ERROR | WARN | INFO |
|------|----------|-------|-------|------|------|
| 字段规则 | 6 | 2 | 2 | 1 | 1 |
| 品种黑白名单 | 4 | 2 | 1 | 1 | — |
| 完整性校验 | 5 | 1 | 1 | 3 | — |
| 防重复 | 3 | — | 1 | 1 | 1 |
| 数据溯源 | 5 | 1 | 3 | 1 | — |
| **合计** | **23** | **6** | **8** | **7** | **2** |

---

*DSHC-DATA-INCREMENT-PIPELINE · DATA_QUALITY_CHECKLIST · v1.0.0 · 2026-10-19*
*Gate: CLOSED/HOLD · Release: NOT_ISSUED · V1 FROZEN · F01/A06 UNCHANGED*
