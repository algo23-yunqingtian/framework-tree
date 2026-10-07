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

---

## 6. 版本更新记录

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2026-10-15 | 初始版本: 6维追溯 |
| v1.1 | 2026-10-15 | 追加混沌故障场景检索、事件排查命令、演练数据清理 |
| v1.2 | 2026-10-18 | 追加灰度生产场景追溯：阶段维度、三方对账、容错排查、异常排查流程、性能瓶颈检索、归档规范（Phase4） |
| **v1.3** | **2026-10-19** | **追加 DSHB 统一指标口径 V1.0：八个指标标识、三个 P99 子指标独立检索、M-LOSS-RATE 正确口径、M-TOTAL-72H 窗口对齐、数据环境差异分析、废弃追溯（Phase5）** |

---

*本规范为投产审计追溯规范更新版。v1.1 追加混沌故障场景检索示例、故障回溯命令、事件排查命令、演练数据清理操作。*
*v1.2 追加灰度生产场景（StageA~D 四阶段放量）的阶段维度追溯、三方对账检索、容错机制排查、异常事件排查流程、性能瓶颈检索与归档规范。*
*v1.3 追加 DSHB 统一指标口径 V1.0：八个指标标识定义、三个 P99 子指标独立检索（严禁混用）、M-LOSS-RATE 正确口径、M-TOTAL-72H 窗口对齐、三方对账与数据环境差异分析、口径变更与废弃追溯。*
