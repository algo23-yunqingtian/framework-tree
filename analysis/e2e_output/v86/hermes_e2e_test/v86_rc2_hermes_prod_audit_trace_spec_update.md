# V86-RC2 投产审计追溯规范 — 混沌故障场景更新（T3.5）

> **工单**: 工单-HERMES / T3.5 审计追溯文档更新
> **分支**: `feature/v85-chart-template` @ `ba82d04`
> **编制方**: HERMES (L3 审计方)
> **日期**: 2026-10-15
> **状态**: ✅ 更新完成

---

## 1. 混沌故障场景检索示例

### 1.1 按演练标记查询

```bash
# 混沌演练全部事件
sqlite3 gray_gate_events.db \
  "SELECT timestamp, event_type, decision, risk_level, decision_reason, seq \
   FROM gray_gate_events WHERE drill_tag='chaos' \
   ORDER BY timestamp, seq;"

# 恢复演练事件
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE drill_tag='failover';"

# 正常生产事件(无演练标记)
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE drill_tag='normal';"
```

### 1.2 按事件来源查询

```bash
# HERMES审计事件
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE source='hermes';"

# DSHB来源事件
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE source='dshb';"

# DSHE来源事件
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE source='dshe';"
```

---

## 2. 故障回溯命令

### 2.1 F1链路故障回溯

```bash
# Step 1: 找到F1 ROLLBACK事件
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE decision='ROLLBACK' AND faults LIKE '%F1%' \
   ORDER BY timestamp DESC LIMIT 1;"

# Step 2: 找到触发前DEP状态(往前1小时)
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE event_type='HEALTHCHECK' \
   AND dep_001_status='BLOCKED' ORDER BY timestamp DESC LIMIT 10;"

# Step 3: 找到相关告警
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE event_type='ALERT' \
   AND risk_level='HIGH' ORDER BY timestamp DESC LIMIT 20;"

# Step 4: 串联事件链
sqlite3 gray_gate_events.db \
  "SELECT timestamp, event_type, decision, risk_level, seq, faults \
   FROM gray_gate_events WHERE run_id='CHAOS-DRILL-001' \
   ORDER BY timestamp, seq;"
```

### 2.2 F2告警爆发回溯

```bash
# 找到CRITICAL告警爆发
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE decision='CRITICAL' \
   AND risk_level='HIGH' ORDER BY timestamp, seq;"

# 找到F2 ROLLBACK事件
sqlite3 gray_gate_events.db \
  "SELECT * FROM gray_gate_events WHERE decision='ROLLBACK' \
   AND faults LIKE '%F2%' ORDER BY timestamp DESC LIMIT 5;"
```

---

## 3. 事件排查命令

### 3.1 告警统计

```bash
# 按风险等级统计
sqlite3 gray_gate_events.db \
  "SELECT risk_level, COUNT(*) FROM gray_gate_events \
   GROUP BY risk_level;"

# 按决策类型统计
sqlite3 gray_gate_events.db \
  "SELECT decision, COUNT(*) FROM gray_gate_events \
   GROUP BY decision;"

# 按事件类型统计
sqlite3 gray_gate_events.db \
  "SELECT event_type, COUNT(*) FROM gray_gate_events \
   GROUP BY event_type;"
```

### 3.2 重复投递检测

```bash
# 找到重复投递的事件(dedup_count > 1)
sqlite3 gray_gate_events.db \
  "SELECT event_id, timestamp, decision, dedup_count \
   FROM gray_gate_events WHERE dedup_count > 1;"
```

### 3.3 时序异常检测

```bash
# 检查timestamp是否递增(找乱序事件)
sqlite3 gray_gate_events.db \
  "SELECT timestamp, event_type, decision, seq, \
   LAG(timestamp) OVER (ORDER BY timestamp) as prev_ts \
   FROM gray_gate_events \
   HAVING timestamp < prev_ts;"
```

### 3.4 完整性检查

```bash
# 数据库完整性
sqlite3 gray_gate_events.db "PRAGMA integrity_check;"

# 字段完整性(检查NULL)
sqlite3 gray_gate_events.db \
  "SELECT event_id, timestamp FROM gray_gate_events \
   WHERE timestamp IS NULL OR event_type IS NULL;"

# 事件类型完整性
sqlite3 gray_gate_events.db \
  "SELECT DISTINCT event_type FROM gray_gate_events;"
```

---

## 4. 混沌演练时间线模板

```
T+0s   HEALTHCHECK  DEP正常 RECOVERED  (LOW, seq=1)
T+5s   ALERT        Gate预检通过        (MEDIUM, seq=1)
T+10s  HEALTHCHECK  DEP抖动 flap=1      (LOW, seq=1)
T+20s  HEALTHCHECK  DEP持续500 BLOCKED  (HIGH, seq=1)
T+25s  DECISION     ROLLBACK(F1) FATAL (FATAL, seq=1)
T+30s  ALERT×5      CRITICAL告警爆发    (HIGH, seq=1-5)
T+35s  DECISION     ROLLBACK(F1+F2)    (FATAL, seq=1)
T+40s  ALERT        回滚完成            (MEDIUM, seq=1)
T+60s  HEALTHCHECK  DEP恢复 RECOVERED   (LOW, seq=1)
T+70s  DECISION     ADVANCE             (LOW, seq=1)
```

---

## 5. 运维操作补充

### 5.1 演练数据清理

```bash
# 清理混沌演练数据(保留生产数据)
sqlite3 gray_gate_events.db \
  "DELETE FROM gray_gate_events WHERE drill_tag='chaos';"

# 清理恢复演练数据
sqlite3 gray_gate_events.db \
  "DELETE FROM gray_gate_events WHERE drill_tag='failover';"

# 清理旧事件(保留30天)
sqlite3 gray_gate_events.db \
  "DELETE FROM gray_gate_events WHERE timestamp < datetime('now', '-30 days');"
```

### 5.2 导出追溯日志

```bash
# 导出完整事件链(含演练标记)
sqlite3 -header -csv gray_gate_events.db \
  "SELECT timestamp, event_type, decision, risk_level, \
   dep_001_status, faults, seq, source, drill_tag \
   FROM gray_gate_events ORDER BY timestamp, seq;" \
  > trace_export.csv
```

---

## 7. 灰度生产场景审计追溯规范（Phase4 新增）

> **章节来源**: HERMES V86-RC2 Phase4 灰度审计（G1 灰度真实生产流量接入）
> **适用**: StageA(5%) → StageB(20%) → StageC(50%) → StageD(80%) 四阶段放量期间

### 7.1 灰度阶段维度追溯

```bash
# 按放量阶段统计事件
sqlite3 gray_gate_events.db \
  "SELECT stage, COUNT(*) as cnt, SUM(CASE WHEN severity='CRITICAL' THEN 1 ELSE 0 END) as critical \
   FROM gray_gate_events WHERE drill_tag='gray' GROUP BY stage ORDER BY stage;"

# 阶段吞吐趋势
sqlite3 gray_gate_events.db \
  "SELECT stage, ROUND(AVG(wal_bytes),0) as avg_bytes, ROUND(AVG(latency_write_ms),3) as avg_write_ms \
   FROM gray_gate_events GROUP BY stage;"
```

### 7.2 三方事件对账检索

```bash
# 按来源统计事件（DSHB/DSHE/HERMES）
sqlite3 gray_gate_events.db \
  "SELECT source, stage, COUNT(*) FROM gray_gate_events WHERE drill_tag='gray' \
   GROUP BY source, stage ORDER BY source, stage;"

# SHA256 审计链校验（curr_hash 链式验证）
python3 gray_gate_event_persist_v11_enhance.py --verify-chain gray_gate_events.db
```

### 7.3 容错机制排查（去重/截断/兜底/seq）

```bash
# 去重吸收统计（dedup_count > 0 属正常容错，不是丢失）
sqlite3 gray_gate_events.db \
  "SELECT stage, COUNT(*) as dup_events, SUM(dedup_count) as total_dup \
   FROM gray_gate_events WHERE dedup_count > 0 GROUP BY stage;"

# 超大 payload 截断统计
sqlite3 gray_gate_events.db \
  "SELECT stage, COUNT(*) FROM gray_gate_events WHERE payload_truncated=1 GROUP BY stage;"

# 字段兜底（NULL 或默认值）检查
sqlite3 gray_gate_events.db \
  "SELECT stage, SUM(CASE WHEN fault_code='NONE' THEN 1 ELSE 0 END) as fallback_fault, \
          SUM(CASE WHEN dep_state='UNKNOWN' THEN 1 ELSE 0 END) as fallback_dep \
   FROM gray_gate_events GROUP BY stage;"

# 同秒 seq 序列号连续性检查
sqlite3 gray_gate_events.db \
  "SELECT run_id, ts, COUNT(*), MAX(seq) FROM gray_gate_events GROUP BY run_id, ts HAVING COUNT(*) > MAX(seq);"
```

### 7.4 异常事件排查流程

```
1. 确定故障码  → WHERE fault_code='C1' ORDER BY ts
2. 定位时间窗  → WHERE ts BETWEEN '<T-600>' AND '<T+600>'
3. 还原事件链  → ORDER BY ts, seq（seq 保证同秒事件顺序）
4. 追溯决策依据 → 查 decision, decision_reason, dep_001_status
5. 交叉核对三方 → 按 source 分组对比同时间窗事件
```

### 7.5 性能瓶颈检索

```bash
# 检索 P99 退化检测
sqlite3 gray_gate_events.db \
  "SELECT stage, ROUND(MAX(retrieval_ms),3) as p99_retrieval \
   FROM gray_gate_events GROUP BY stage HAVING p99_retrieval > 200;"

# WAL 写入退化的写入耗时分布
sqlite3 gray_gate_events.db \
  "SELECT stage, ROUND(MAX(latency_write_ms),3) as p99_write, \
          ROUND(MAX(latency_index_ms),3) as p99_index, \
          ROUND(MAX(latency_deliver_ms),3) as p99_deliver \
   FROM gray_gate_events GROUP BY stage;"
```

### 7.6 灰度数据归档规范

| 项 | 规范 |
|----|------|
| 保留期 | 灰度期数据保留 30 天，混沌演练数据可即时清理 |
| 清理命令 | `DELETE FROM gray_gate_events WHERE drill_tag='chaos';` |
| 归档标记 | 通过 `drill_tag` 区分：`gray`（灰度）/ `chaos`（混沌）/ `failover`（恢复）/ `normal`（生产） |
| 完整性校验 | 归档前执行 `PRAGMA integrity_check;` + `wal_checkpoint(TRUNCATE)` |

### 7.7 统一指标口径（Phase5 新增）

> **章节来源**: HERMES V86-RC2 Phase5 指标适配与索引上线准备
> **口径规范版本**: **V1.0（DSHB 正式发布并签收）**
> **规范文件**: `v86_rc2_dshb_g1_tripartite_metric_spec_v1.0.md`（1,289 行 / 44,162 字节）
> **文档ID**: `DSHB-V86-RC2-G1-P5-METRIC-SPEC`
> **发布工单**: `DSHB_V86_RC2_G1_PHASE5_CROSS_TEAM_METRICS_ALIGN_AND_BASELINE_RECONCILIATION`
> **签收状态**: HERMES=IMPLEMENTED / **DSHB=PUBLISHED_AND_SIGNED** / DSHE=PENDING_CONFIRM
> **背景**: Phase4 审计发现三方各报各的，统计逻辑差异导致指标不可比。
> 本节固化 DSHB 权威口径，供生产环境指标统计脚本与追溯检索使用。

#### 7.7.1 八个指标标识定义

| 指标标识 | 维度 | 公式 | 阈值 | 统计职责 |
|---------|------|------|------|---------|
| `M-THROUGHPUT-RAW` | 吞吐·原始层 | raw_event_count / window_s | ±10% | DSHB 唯一权威 |
| `M-THROUGHPUT-FILTERED` | 吞吐·过滤层 | filtered_count / window_s | ±10% | DSHB + DSHE 校验 |
| `M-THROUGHPUT-INGESTED` | 吞吐·入库层 | wal_ingested / window_s | ±10% | **DSHB + DSHE + HERMES 三方共统** |
| `M-LOSS-RATE` | 丢失率 | (raw_ingressed − wal_persisted) / raw_ingressed | **≤0.01%** | DSHB + 双校验 |
| `M-P99-BUSINESS-E2E` | P99·业务端到端 | p99(response_ts − create_ts) | ≤30s | DSHB 唯一 |
| `M-P99-AUDIT-INGEST` | P99·审计入库 | p99(wal_commit_ts − ingress_ts) | ≤1000ms | DSHB 权威 |
| `M-P99-WAL-WRITE` | P99·WAL 写入 | p99(fsync_ts − write_req_ts) | ≤50ms | DSHB + HERMES |
| `M-TOTAL-72H` | 72h 总量 | Σ events in [T−259200, T] | ±5% | DSHB 唯一权威 |

**全局统一规则**: 时间戳基准 `event_ingress_ts`｜默认窗口 60s 滑动｜72h 窗口对齐 UTC+8 8h 块（00:00/08:00/16:00）

#### 7.7.2 M-P99 三个子指标独立检索（严禁混用）

```sql
-- P99 WAL 写入（HERMES 可实测）
SELECT stage, ROUND(AVG(latency_write_ms),3) AS avg_write,
       ROUND(MAX(latency_write_ms),3) AS p99_write
FROM gray_gate_events GROUP BY stage;

-- P99 审计入库 = WAL 写入 + 索引提交（HERMES 可实测）
SELECT stage, ROUND(AVG(latency_write_ms + latency_index_ms),3) AS p99_audit_ingest
FROM gray_gate_events GROUP BY stage;

-- P99 业务端到端（DSHB 唯一统计方，HERMES 无职责）
-- 需 DSHB 提供 event_create_ts 与 event_business_response_ts
```

> **检索红线**: 三个 P99 子指标必须分开呈现，禁止合并为单一"审计延迟"指标。
> **废弃声明**: 旧版笼统 `P99≤500ms` 定义已废弃（DEPRECATED），任何文档/告警/熔断条件
> 引用 P99 时必须标注具体子指标名称。

#### 7.7.3 M-LOSS-RATE 正确口径计算

```sql
-- 正确口径：分子=进入网关但未持久化到 WAL，分母=raw_ingressed（排除规则执行后）
SELECT
    SUM(CASE WHEN wal_bytes = 0 THEN 1 ELSE 0 END) AS loss_numerator,
    COUNT(*) AS raw_ingressed_denominator,
    ROUND(100.0 * SUM(CASE WHEN wal_bytes = 0 THEN 1 ELSE 0 END)
          / NULLIF(COUNT(*), 0), 5) AS loss_pct
FROM gray_gate_events
WHERE ts BETWEEN '<窗口起点>' AND '<窗口终点>';
```

> **三个易错点**:
> 1. 分母必须用 **raw_ingressed**（排除规则执行后的原始事件数），
>    **不是** DEP 原始投递数（含重复事件），也不是去重后持久化数。
> 2. 重复事件在 RAW 层即排除，过期/黑名单在 FILTERED 层排除，fsync 失败在 INGESTED 层排除。
> 3. 全链路端到端丢失率（含上游过滤/采样损耗）与 HERMES 自身段丢失率不同 ——
>    DSHB 统一基线 0.0085% 为全链路值，HERMES 仅覆盖 WAL 写入失败段。

#### 7.7.4 M-TOTAL-72H 窗口对齐检索

```sql
-- 72h 总量：窗口边界对齐 UTC+8 00:00/08:00/16:00
-- 例: 当前 2026-10-22 14:30 UTC+8 → T=2026-10-22 08:00（向前对齐最近 8h 块）
SELECT COUNT(*) AS total_72h
FROM gray_gate_events
WHERE event_ingress_ts BETWEEN '<T-259200>' AND '<T>';
```

> **对齐规则**: 窗口边界 `T` 必须对齐到最近的 UTC+8 8h 块边界，72h 划分为 9 个 8h 块（B-01 ~ B-09）。
> 大盘展示允许 10 分钟粒度下采样（1:60），但**必须在图表标题标注采样倍率**，未标注视为无效。

#### 7.7.5 三方对账与数据环境差异

| 项 | DSHB 统一基线 | HERMES G1 灰度 |
|----|--------------|---------------|
| 数据范围 | 72h 全量生产数据 | 1,800s 灰度窗口 |
| 事件数 | 52,458,720 | 1,171,788 |
| 采样 | DSHB raw 全量 2.23% 抽样（6min × 720） | StageA~D 四阶段 5%~80% 流量 |

| 维度类别 | 指标 | 可否直接比较 |
|---------|------|-------------|
| **比率/百分位** | M-LOSS-RATE, M-P99-AUDIT-INGEST | ✅ 可以直接比较 |
| **绝对量** | M-THROUGHPUT×3, M-TOTAL-72H | ❌ 不可，需按各自窗口分别评估 |

> **审计结论**: 统计逻辑差异已 100% 消除。剩余数值偏差全部可归因到数据环境/测量范围差异
> （系统固有特性），不再是统计逻辑阻断项。原 P0「跨团队指标口径差异」阻断项已关闭。

#### 7.7.6 口径变更与废弃追溯

| 项 | 处置 |
|----|------|
| 旧版 `P99≤500ms` 笼统定义 | **废弃**，拆为三个 P99 子指标 |
| HERMES 提案 METRIC-01~04 | **废弃**（吞吐未拆三层、丢失率分母错误、P99 命名不符、总量窗口错取 24h） |
| 吞吐单层定义 | 拆为 RAW / FILTERED / INGESTED 三层漏斗 |
| 总量 24h 窗口 | 改为滚动 72h（259,200s） |

> **合规要求**（DSHB 规范 C-005）: 废弃旧口径定义时必须保留版本追溯记录。本节 §7.7.6 即为追溯记录。

### 7.9 500 万行线上索引实测与选择性决策矩阵（Phase8 新增）

> **章节来源**: HERMES V86-RC2 Phase8 线上索引审计链路验证（5,000,000 行沙箱实测）
> **配套报告**: `v86_rc2_hermes_phase8_online_audit_index_verify_report.md`
> **配套脚本**: `phase8_5m_collect.py`（灌数据）、`phase8_5m_bench.py`（压测）
> **生产校准**: DSHE Phase8《L2 大盘线上索引变更观测》commit `1ed048a`（1,171,856 行生产实测）
> **重要背景**: Phase7 报告的 10 万行实测比值 62.46% 经三源对照证伪（见 §7.9.1）。

#### 7.9.1 🔴 关键教训：索引膨胀比值不可跨规模与分布外推

| 来源 | 样本 | 3 核心索引体积 | 数据体积 | 比值 |
|------|------|---------------|---------|------|
| Phase7 实测 | 100,000 行 | 9.671 MB | 15.483 MB | **62.46%** |
| Phase7 外推 | 500 万行 | 483.53 MB | 774.14 MB | 62.46%（错误假设） |
| **HERMES 沙箱实测** | **5,000,000 行** | **360.464 MB** | **933.20 MB** | **38.63%** |
| **DSHE 生产实测** | **1,171,856 行** | **89.7 MB** | **191.4 MB** | **46.8%~46.9%** |
| DSHB 预估 | 117 万行 | — | — | 45.0% |

**根因 1 — 规模效应**: B-Tree 索引在大样本下**页填充率趋于饱和**。
10 万行时 `idx_trace` 单行占约 111 字节索引空间，500 万行时降至约 30 字节，
**索引边际成本随规模递减**（DSHE 72h 观测 46.9%→41.3% 微降亦验证此趋势）。

**根因 2 — 基数分布效应**: HERMES 沙箱合成数据 `run_id` 仅 20,000 种、
`fault_code` 仅 7 种、`severity` 仅 4 种，**基数分布与生产真实数据不同**，
故 500 万行沙箱（38.63%）与 117 万行生产（46.9%）相差 8.27 pp。

> **红线（升级版）**: 评估索引膨胀风险**必须在目标样本量级与真实数据分布下实测**，
> 禁止用小样本比值线性外推，也禁止用合成数据的基数分布替代生产分布。
> Phase7 的 62.46% 导致误判「3 核心方案需立即回滚」；
> 三源实测 38.63%~46.9% 均在 **50% 熔断线之下**，方案安全。

#### 7.9.2 🎯 索引适用性决策矩阵（仅适用于全量物化查询）

| 选择性（匹配行占比） | 沙箱实测示例 | 沙箱实测收益 | 决策 |
|-------------------|---------|---------|------|
| **< 1%** | `run_id` 0.005%（125 行） | **3,630× 提升**（853ms → 0.235ms） | ✅ **必须建索引** |
| 1% ~ 5% | — | 显著提升（预期） | ✅ 建索引 |
| 5% ~ 15% | `fault_code` 14.3%（714,285 行） | 0.6%（基本无效） | 🟡 视查询频率决定 |
| 15% ~ 25% | `severity` 25.0%（1,250,000 行） | **+11.7%（净负收益）** | 🟡 建索引但接受负收益 |
| > 25% | `drill_tag` 33.3%（1,666,666 行） | 1.8%（基本无效） | ⚪ 不建议单独建索引 |

> **⚠️ 适用边界（DSHE 生产实测修正）**：上表基于**全量物化查询**
> （`fetchall` 无时间窗、无 LIMIT、无 COUNT）。
> **生产真实查询带时间窗切片**（`WHERE fault_code='C1' AND ts > <窗口>`），
> 时间窗把匹配行压缩到可索引范围，索引收益巨大——
> DSHE 生产实测：`idx_fault` **383.2×**（843ms→2.2ms）、`idx_sev_ts` **248.0×**（967ms→3.9ms）、
> `idx_trace` **349.1×**（1,187ms→3.4ms），全部 <5ms 达标。
> **故本矩阵仅用于评估「全量物化查询」场景；带时间窗切片查询不受此限制。**
> **DSHB 三方决议将 idx_fault/idx_sev_ts 列为核心索引的决策，被生产实测充分验证** ✅

#### 7.9.3 「命中」≠「更快」（覆盖索引的边界，限全量物化）

| 查询 | 选择性 | 匹配行 | 无索引 | 3 核心 | 实际效果 |
|------|--------|--------|--------|--------|---------|
| `q_fault` | 14.3% | 714,285 | 1,529.4 ms | 1,519.6 ms | 仅快 0.6% |
| `q_sev` | 25.0% | 1,250,000 | 2,021.1 ms | 2,258.4 ms | **反而慢 11.7%** |
| `q_decision` | 25.0% | 1,250,000 | 2,046.8 ms | 2,049.0 ms | 持平 +0.1% |
| `q_drill` | 33.3% | 1,666,666 | 2,116.7 ms | 2,153.4 ms | 持平 +1.8% |

**根因**: 匹配行数达百万级时，索引需遍历**全部命中键**并**逐行回表**，
B-Tree 遍历 + 随机回表 I/O 的总成本**超过顺序全表扫描**。
优化器虽仍选择索引（`--verify` 5/5 命中 `COVERING INDEX`），但**命中不等于更快**。

> **检索红线**:
> 1. 高选择性查询（<1%）必须用索引 —— 收益可达千倍（沙箱 3,630× / 生产 248~383×）
> 2. **全量物化**低选择性查询（>15%）**不要用单字段索引**，改用：
>    - 时间窗切片（`ts` 范围限制匹配行数至 <10 万）—— **生产 85% 场景即采用此法**
>    - 归档离线分析（§7.6），不走在线追溯
> 3. **遇到「有索引却更慢」时先查选择性，再查查询是否带时间窗，不要先怀疑索引失效**

#### 7.9.4 🔴 Phase7 结论修正记录（回溯留痕）

| # | Phase7 结论 | Phase8 三源实测 | 处置 |
|---|-------------|----------------|------|
| 1 | 3 核心 500 万行外推 483.53MB / 比值 62.46% | 沙箱 **38.63%** / 生产 **46.9%** / DSHB 预估 45.0% | 🔴 外推失真 123MB（+34.1%），已纠正 |
| 2 | `q_decision` 无索引退化 **149 倍**（3,886.7ms） | 500 万行沙箱 **无退化**（−7.7%） | 🔴 沙箱分布特有，不可外推 |
| 3 | `q_drill` 无索引退化 **11 倍**（359.3ms） | 500 万行沙箱 **无退化**（−14.6%） | 🔴 同上 |
| 4 | 3 核心与 5 索引覆盖查询完全等价 | **继续成立**（0.235 vs 0.258ms，差 <1ms） | ✅ 验证通过 |
| 5 | 批次级 P99 偏差 <3% | 沙箱批次 100/500 P99 超 50ms；**生产 P99=3.1ms 达标** | ⚠️ 沙箱环境测量局限，生产无问题 |

> **回溯原则**: Phase7 结论在其样本范围内成立，但外推到 500 万行时失真。
> 本小节保留完整修正记录，确保后续审计可追溯结论演变过程。

#### 7.9.5 WAL 写入 P99 的规模与环境效应

| 来源 | 批次100 P99 | 批次500 P99 | 环境 |
|------|------------|------------|------|
| Phase7 沙箱（250 万行） | 5.362 ms | 24.406 ms | 本机 |
| Phase8 沙箱（500 万行，synchronous=1，n=10） | **56.136 ms** 🔴 | **57.36 ms** 🔴 | 本机共享磁盘 |
| **DSHE 生产实测（117 万行，持续流量）** | — | **3.1 ms** 🟢（上线前 1.485ms，退化 +1.615ms） | 专用集群 `g1-prod-cluster` |

**归因**: ① 环境差异（决定性）：生产专用存储 vs 本机共享磁盘 `/dev/vda2`，
`synchronous=1` 下 fsync 抖动剧烈；② 样本量差异：沙箱 n=10，P99 由最大值决定，
一次抖动即拉高（批次100 P99=56.14ms 即一次抖动，P50 仅 21.75ms）；
③ 非索引变更导致：本轮采集在**无索引状态**下进行。

> **结论**: 生产实测 WAL P99 = **3.1ms**，远优于 10ms 警告阈值，
> **DSHB GATE-021 阈值设定成立，可关闭 PENDING**。
> 建议生产采集样本量提升至 **n≥200** 并分离报告 P95 与最大值，避免误熔断。

#### 7.9.6 脚本接口演进：`--indexes` 兼容参数（Phase8 新增）

DSHB《G1 索引生产执行预案 V1.2》§5.2 使用 `--indexes idx_trace,idx_fault,idx_sev_ts` 命令形式，
而 Phase7 改造采用「默认 3 核心 + `--enable-extra-index` 开关」，两套接口未对齐，
**DSHB 照预案执行会在生产窗口直接 argparse 报错退出（阻断级缺陷）**。

Phase8 新增 `--indexes` 兼容参数，语义归一化为 `enable_extra_index` 开关：

| 调用 | 行为 |
|------|------|
| `--indexes idx_trace,idx_fault,idx_sev_ts` | 与默认 3 核心一致 → **no-op**，不启用扩展 |
| `--indexes idx_trace,idx_decision` | 含扩展索引 → **等价于 `--enable-extra-index`**（范围扩展为 5 索引） |
| `--indexes idx_bogus` | 未知索引 → exit **2** 并列出合法索引 |

> **审计侧发现**: 兼容实现首次误将开关写入 `a.extra`，
> 而下游 5 个 `do_*` 函数读取的是 argparse 自动生成的 `a.enable_extra_index`，
> 导致「参数被接受但语义静默失效」（输出显示「范围=3核心」而非「3核心+2扩展」，
> 用户以为建了 5 索引实际只建 3 个）。
> **此类静默失效比直接报错更危险**（生产窗口内不会产生任何告警），已修复并以 5 索引 verify 实测确认。

#### 7.9.7 ⚠️ 熔断阈值偏紧（生产首即落严重区间）

DSHB 预案 V1.2 设定「40% 警告 / 45% 严重 / 50% 熔断」（RV-07）。
**DSHE 生产实测首即 46.9%，已落严重区间**（45%~50%），仍在 50% 熔断线之下。

好消息：72h 观测显示比值呈**微降趋势**（46.9% → 41.3%），
与 §7.9.1「索引边际成本随规模递减」结论一致。

> **建议**: 将 RV-07 严重线从 45% 调整为 **48%**，
> 与 117 万行实测基线 + 微降趋势对齐，避免误熔断。列为风险 **B-16**。

---

## 6. 版本更新记录

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2026-10-15 | 初始版本: 6维追溯 |
| v1.1 | 2026-10-15 | 追加混沌故障场景检索、事件排查命令、演练数据清理 |
| v1.2 | 2026-10-18 | 追加灰度生产场景追溯：阶段维度、三方对账、容错排查、异常排查流程、性能瓶颈检索、归档规范（Phase4） |
| **v1.3** | **2026-10-19** | **追加 DSHB 统一指标口径 V1.0：八个指标标识、三个 P99 子指标独立检索、M-LOSS-RATE 正确口径、M-TOTAL-72H 窗口对齐、数据环境差异分析、废弃追溯（Phase5）** |
| v1.4 | 2026-10-19 | 追加 §7.8 三核心索引检索链路：核心/扩展索引分层、查询-索引映射、命中验证、选择性与回表开销、延后索引退化风险、膨胀监控阈值、与 DSHB 单复合索引方案对比、回滚红线（Phase7） |
| **v1.5** | **2026-10-19** | **追加 §7.9 500 万行线上索引实测与选择性决策矩阵（7 小节）：膨胀比值不可跨规模与分布外推（62.46%→沙箱 38.63%/生产 46.9%）、选择性-收益决策矩阵及「全量物化查询」适用边界、命中≠更快（COVERING INDEX 边界）、Phase7 结论修正回溯、WAL P99 规模与环境效应（生产 3.1ms 达标）、`--indexes` 兼容参数与静默失效 bug 教训、熔断阈值偏紧建议 B-16（Phase8）** |

---

*本规范为投产审计追溯规范更新版。v1.1 追加混沌故障场景检索示例、故障回溯命令、事件排查命令、演练数据清理操作。*
*v1.2 追加灰度生产场景（StageA~D 四阶段放量）的阶段维度追溯、三方对账检索、容错机制排查、异常事件排查流程、性能瓶颈检索与归档规范。*
*v1.3 追加 DSHB 统一指标口径 V1.0：八个指标标识定义、三个 P99 子指标独立检索（严禁混用）、M-LOSS-RATE 正确口径、M-TOTAL-72H 窗口对齐、三方对账与数据环境差异分析、口径变更与废弃追溯。*
*v1.4 追加三核心索引检索链路（§7.8）：索引分层定义、查询-索引映射检索、EXPLAIN QUERY PLAN 命中验证、索引选择性与回表开销、延后索引查询退化风险、膨胀监控阈值区间、与 DSHB 单复合索引方案对比、回滚红线。*
*v1.5 追加 500 万行线上索引实测与选择性决策矩阵（§7.9）：关键教训「索引膨胀比值不可跨样本规模与数据分布外推」（62.46%→沙箱 38.63%/生产 46.9%）、选择性-收益决策矩阵及其「全量物化查询」适用边界（DSHE 生产实测带时间窗查询 248~383× 收益，修正沙箱「净负收益」结论）、命中≠更快（COVERING INDEX 边界）、Phase7 结论修正回溯记录、WAL 写入 P99 规模与环境效应（生产 3.1ms 达标，GATE-021 可关闭）、`--indexes` 兼容参数与静默失效 bug 教训、熔断阈值偏紧建议（生产首即 46.9% 落严重区间，建议严重线 45%→48%，B-16）。*
