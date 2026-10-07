# V86-RC2 灰度审计运维 SOP

> **适用环境**: V86-RC2 G1 灰度生产环境
> **版本**: v1.0
> **生成时间**: 2026-10-07 17:00
> **维护方**: HERMES
> **前置约束**: BRANCH_LOCKED=TRUE / NO_MODIFY_V85=TRUE / NO_ZHIJI_API_CALL=FALSE

---

## 0. 快速入口（30 秒判断你该做什么）

| 你遇到的情况 | 直接跳到 |
|-------------|---------|
| WAL 磁盘占用告警 / WAL 无法写入 | §1 |
| 事件丢失 / 计数对不上 | §2 |
| 检索超时 / 查询慢 | §3 |
| 重复事件 / 计数翻倍 | §4 |
| 审计链 SHA256 校验失败 | §5 |
| 告警风暴 / 告警漏报 | §6 |
| 灰度放量前后例行巡检 | §7 |

> **总原则**: 审计链路是证据链，**宁可保守降级也不能丢证据**。任何处置优先保证事件不丢失，其次才是性能。

---

## 1. WAL 异常处置

### 1.1 触发条件

| 级别 | 条件 |
|------|------|
| ⚠️ WARN | WAL 磁盘占用 > 20 GB（约 62.5%） |
| 🔴 CRITICAL | WAL 磁盘占用 > 25.6 GB（80%）或写入报错 |

### 1.2 处置步骤

```bash
# 步骤1: 确认 WAL 实际占用
df -h /var/lib/hermes/gray_gate_events.db
du -sh /var/lib/hermes/wal/

# 步骤2: 查看 checkpoint 是否正常执行
sqlite3 gray_gate_events.db "PRAGMA wal_checkpoint(PASSIVE);"
sqlite3 gray_gate_events.db "PRAGMA wal_pages; PRAGMA page_count;"

# 步骤3: 若 checkpoint 未清理，强制全量 checkpoint（业务低峰执行）
sqlite3 gray_gate_events.db "PRAGMA wal_checkpoint(TRUNCATE);"

# 步骤4: 若磁盘仍不足，归档历史事件
python3 ~/.hermes/scripts/archive_gray_events.py --before-days 7

# 步骤5: 观察 15 分钟，确认占用回落
watch -n 60 "df -h /var/lib/hermes/gray_gate_events.db | tail -1"
```

### 1.3 预防措施

- 每 6 小时自动 checkpoint（cron 已配置）
- 建立复合索引避免 WAL 日志膨胀（见 SOP 附录 A）
- 灰度放量每阶段结束巡检一次 WAL 增速

### 1.4 不可做的事

- ❌ 禁止直接删除 WAL 文件（会丢失未 checkpoint 的事件）
- ❌ 禁止在业务高峰期执行 TRUNCATE checkpoint
- ❌ 禁止把 DB 文件移出挂载点

---

## 2. 事件丢失处置

### 2.1 触发条件

事件丢失率 > 0.01%（工单 T6 验收阈值）

### 2.2 排查流程

```bash
# 步骤1: 定位丢失发生在哪一段链路
# 三方计数对比
sqlite3 gray_gate_events.db   "SELECT stage, COUNT(*) FROM gray_gate_events GROUP BY stage;"
# 对比 DSHB DEP 原始事件数 + DSHE 大盘接收数

# 步骤2: 区分丢失类型
#   a) 去重吸收（正常，非丢失）
sqlite3 gray_gate_events.db   "SELECT COUNT(*) FROM gray_gate_events WHERE dedup_count > 0;"
#   b) 写入失败（真实丢失，需定位）
sqlite3 gray_gate_events.db   "SELECT ts, run_id, decision FROM gray_gate_events WHERE wal_bytes = 0;"

# 步骤3: 若为写入失败，检查 WAL 与磁盘
sqlite3 gray_gate_events.db "PRAGMA integrity_check;"
dmesg | tail -20   # 检查磁盘 I/O 错误

# 步骤4: 补偿写入（从 DSHB 原始事件回流）
python3 ~/.hermes/scripts/replay_dep_events.py   --from-dshb --window "故障时间-5min" "--故障时间+5min"
```

### 2.3 归因判定表

| DEP 原始 − HERMES 持久化 | 归因 | 是否需处置 |
|--------------------------|------|-----------|
| = dedup_count 之和 | 去重吸收（正常） | ❌ 无需 |
| = 写入失败数 | 磁盘/进程异常 | ✅ 需补偿 |
| > 上述两者之和 | **未解释丢失（P0）** | 🔴 立即上报 |

### 2.4 红线

- 🔴 出现「未解释丢失」= P0 事件，**立即暂停灰度放量**，通知 DSHB/DSHE/Gate
- 🔴 禁止修改历史事件数据来"对齐"计数

---

## 3. 检索超时处置

### 3.1 触发条件

| 级别 | 条件 |
|------|------|
| ⚠️ WARN | 检索 P99 > 100ms |
| 🔴 CRITICAL | 检索 P99 > 200ms 或查询超时 |

### 3.2 处置步骤

```bash
# 步骤1: 检查单表行数（退化临界点 500 万行）
sqlite3 gray_gate_events.db "SELECT COUNT(*) FROM gray_gate_events;"

# 步骤2: 检查现有索引
sqlite3 gray_gate_events.db ".indexes gray_gate_events"

# 步骤3: 缺失复合索引 → 立即建立（见附录 A）
sqlite3 gray_gate_events.db <<'SQL'
CREATE INDEX IF NOT EXISTS idx_trace ON gray_gate_events(run_id, ts, seq);
CREATE INDEX IF NOT EXISTS idx_fault ON gray_gate_events(fault_code, ts);
CREATE INDEX IF NOT EXISTS idx_sev_ts ON gray_gate_events(severity, ts);
SQL

# 步骤4: 分析慢查询
EXPLAIN QUERY PLAN
SELECT * FROM gray_gate_events WHERE fault_code='C1' ORDER BY ts, seq;

# 步骤5: 行数超 500 万 → 归档冷数据
python3 ~/.hermes/scripts/archive_gray_events.py --before-days 7
```

### 3.3 索引清单（灰度环境必备）

见**附录 A**。

---

## 4. 重复事件处置

### 4.1 触发条件

`dedup_count` 异常增长，或同一 event_id 出现多行

### 4.2 排查步骤

```bash
# 步骤1: 检查是否有重复行（正常应为 0）
sqlite3 gray_gate_events.db   "SELECT event_id, COUNT(*) c FROM gray_gate_events GROUP BY event_id HAVING c > 1;"

# 步骤2: 检查 dedup_count 分布
sqlite3 gray_gate_events.db   "SELECT dedup_count, COUNT(*) FROM gray_gate_events GROUP BY dedup_count;"

# 步骤3: 若出现重复行，说明去重逻辑被绕过 → 检查写入路径
sqlite3 gray_gate_events.db   "SELECT run_id, ts, decision, seq FROM gray_gate_events WHERE event_id IN (SELECT event_id FROM gray_gate_events GROUP BY event_id HAVING COUNT(*)>1);"
```

### 4.3 修复

```bash
# 去重修复（保留 dedup_count 最大的那条）
python3 ~/.hermes/scripts/dedup_fix.py --db gray_gate_events.db --dry-run
python3 ~/.hermes/scripts/dedup_fix.py --db gray_gate_events.db --apply
```

### 4.4 根因

重复行通常来自：写入路径绕过 `gray_gate_event_persist_v11_enhance.py` 的 UPSERT 逻辑，
直接执行 INSERT。检查是否有旁路写入代码。

---

## 5. 审计链 SHA256 校验失败处置

### 5.1 触发条件

`curr_hash != SHA256(prev_hash || canonical)`

### 5.2 排查步骤

```bash
# 步骤1: 定位断裂点
python3 ~/.hermes/scripts/verify_sha256_chain.py   --db gray_gate_events.db --report-breakpoints

# 步骤2: 输出断裂位置后的所有事件（全部视为不可信）
sqlite3 gray_gate_events.db   "SELECT event_id, ts, seq, decision FROM gray_gate_events WHERE ts >= '断裂时间' ORDER BY ts, seq;"
```

### 5.3 处置红线

- 🔴 **SHA256 链断裂 = P0 事件**，意味着审计证据可能被篡改或损坏
- 🔴 **立即暂停灰度放量**，通知 Gate 委员会
- 🔴 **禁止修补历史链**（不能重算 hash 让它"看起来正常"）—— 必须保留断裂点作为证据
- ✅ 断裂点之后的事件需重新采集，标注 `drill_tag='rebuild'`

---

## 6. 告警风暴 / 告警漏报处置

### 6.1 告警风暴（误报过多）

```bash
# 步骤1: 统计告警分布
sqlite3 gray_gate_events.db   "SELECT severity, COUNT(*), ts FROM gray_gate_events GROUP BY severity, ts ORDER BY COUNT(*) DESC LIMIT 20;"

# 步骤2: 检查是否低于触发阈值仍触发
# CRITICAL 需 ≥3 并发才触发 F2；DEP 抖动需 ≥5 才触发 F5
sqlite3 gray_gate_events.db   "SELECT ts, COUNT(*) c FROM gray_gate_events WHERE severity='CRITICAL' GROUP BY ts HAVING c < 3;"

# 步骤3: 若为抖动型误报，提高抑制窗口（不改阈值，改聚合窗口）
```

### 6.2 告警漏报（真实故障未告警）

```bash
# 步骤1: 确认故障是否被记录
sqlite3 gray_gate_events.db   "SELECT * FROM gray_gate_events WHERE fault_code LIKE 'C%' OR fault_code LIKE 'CF%' ORDER BY ts;"

# 步骤2: 若故障有记录但无告警 → 检查告警生成路径
# 步骤3: 若是并发数未达阈值 → 这是设计行为，不是漏报
```

### 6.3 阈值调整权限

| 阈值 | 当前值 | 调整权限 |
|------|--------|---------|
| 审计吞吐告警 | 80 ev/s | HERMES + Gate 联签 |
| CRITICAL 并发 | ≥3 | HERMES + Gate 联签 |
| DEP 抖动并发 | ≥5 | HERMES + DEP + Gate 三方联签 |

**禁止 HERMES 单方调整阈值。**

---

## 7. 灰度放量例行巡检 SOP

### 7.1 每个放量阶段开始前（5 分钟）

```bash
# 1) WAL 磁盘与 checkpoint
df -h /var/lib/hermes/gray_gate_events.db
sqlite3 gray_gate_events.db "PRAGMA wal_checkpoint(PASSIVE); PRAGMA wal_pages;"

# 2) 数据库完整性
sqlite3 gray_gate_events.db "PRAGMA integrity_check;"   # 必须返回 ok

# 3) 索引完整性
sqlite3 gray_gate_events.db "PRAGMA quick_check;"

# 4) 审计链尾校验
python3 ~/.hermes/scripts/verify_sha256_chain.py --db gray_gate_events.db --tail-check 100

# 5) 基础计数基线（用于阶段结束对账）
sqlite3 gray_gate_events.db "SELECT COUNT(*) FROM gray_gate_events;"
```

### 7.2 放量期间（每 30 分钟）

```bash
# 1) WAL 增速（对比阶段开始值）
df -h /var/lib/hermes/gray_gate_events.db

# 2) 事件增量与丢失率
sqlite3 gray_gate_events.db "SELECT COUNT(*) FROM gray_gate_events WHERE ts > '阶段开始时间';"

# 3) 检索性能
time sqlite3 gray_gate_events.db "SELECT COUNT(*) FROM gray_gate_events WHERE fault_code IS NOT NULL;"

# 4) 告警计数
sqlite3 gray_gate_events.db   "SELECT severity, COUNT(*) FROM gray_gate_events WHERE ts > '阶段开始时间' GROUP BY severity;"
```

### 7.3 每个阶段结束后（15 分钟）

```bash
# 1) 三方对账（HERMES vs DSHB vs DSHE）
python3 ~/.hermes/scripts/triple_reconcile.py   --stage "StageX" --hermes-db gray_gate_events.db   --dshb-endpoint http://dshb:8080/events?since=阶段开始 --report md

# 2) SHA256 全链校验
python3 ~/.hermes/scripts/verify_sha256_chain.py --db gray_gate_events.db --full

# 3) 容错统计
sqlite3 gray_gate_events.db <<'SQL'
SELECT '去重', SUM(CASE WHEN dedup_count>0 THEN 1 ELSE 0 END) FROM gray_gate_events;
SELECT '截断', SUM(CASE WHEN payload_truncated=1 THEN 1 ELSE 0 END) FROM gray_gate_events;
SELECT '兜底', SUM(CASE WHEN dep_state='UNKNOWN' THEN 1 ELSE 0 END) FROM gray_gate_events;
SQL

# 4) 记录阶段基线快照
python3 ~/.hermes/scripts/phase_snapshot.py --stage "StageX" --output phase_snapshots/
```

### 7.4 巡检判定表

| 检查项 | 正常 | 需处置 |
|--------|------|--------|
| 数据库完整性 | `ok` | 任何非 ok |
| WAL 增速 | < 2 GB/小时 | > 3 GB/小时 |
| 事件丢失率 | < 0.01% | > 0.01% |
| 检索 P99 | < 100ms | > 200ms |
| SHA256 链 | 连续 | 任何断裂 |
| 重复行 | 0 | > 0 |

---

## 8. 复合索引运维（Phase5 新增）

> **对应风险**: B-01 检索线性扫描退化（P1）、B-02 索引空间膨胀（P2→P1）
> **配套脚本**: `phase5_index_deploy.py`、`phase5_index_baseline_validator.py`
> **配套文档**: `v86_rc2_hermes_phase5_index_deploy_sop.md`

### 8.1 索引清单（灰度/生产必备 5 个）

| 索引 | 定义 | 覆盖查询 | 必要性 |
|------|------|---------|--------|
| `idx_trace` | `(run_id, ts, seq)` | 主追溯：按 run 查时间窗内序列 | **核心** |
| `idx_fault` | `(fault_code, ts)` | 故障码检索（**当前退化点**） | **核心** |
| `idx_sev_ts` | `(severity, ts)` | CRITICAL 告警筛选 | **核心** |
| `idx_decision` | `(decision, ts)` | ROLLBACK/FUSE 决策追溯 | 次要 |
| `idx_drill` | `(drill_tag, ts)` | 灰度/混沌/演练分流 | 次要 |

### 8.2 上线流程（5 步）

```bash
SCRIPT=~/.hermes/scripts/phase5_index_deploy.py   # 实际部署路径按环境调整
DB=/var/lib/hermes/gray_gate_events.db

# 步骤1: 预检查（只读，可重复执行，失败则停止）
python3 $SCRIPT --db $DB --check

# 步骤2: 创建索引（脚本自动记录回滚点 *.idx_rollback）
python3 $SCRIPT --db $DB --create

# 步骤3: 验证索引生效（EXPLAIN QUERY PLAN 逐条确认命中）
python3 $SCRIPT --db $DB --verify

# 步骤4: 监控索引空间（B-02 膨胀评估）
python3 $SCRIPT --db $DB --size

# 步骤5: 观察 30 分钟检索性能，确认 P99 < 100ms
time sqlite3 $DB "SELECT COUNT(*) FROM gray_gate_events WHERE fault_code='C1';"
```

### 8.3 触发条件

| 级别 | 条件 | 动作 |
|------|------|------|
| 🔴 P1 | 检索 P99 > 200ms | **立即创建核心 3 索引**（idx_trace/idx_fault/idx_sev_ts） |
| ⚠️ P1 | 单表 > 500 万行（约 4.3h 后到达） | 建索引 + 归档冷数据 |
| ⚠️ P2 | 索引/数据比 > 30% | 精简为 3 个核心索引，移除次要索引 |
| ⚠️ P2 | 索引/数据比 15~30% | 纳入持续监控 |

### 8.4 回滚

```bash
# 回滚索引（DROP 全部 idx_* 索引）
python3 $SCRIPT --db $DB --rollback

# 回滚后必做校验
sqlite3 $DB "PRAGMA integrity_check; SELECT COUNT(*) FROM gray_gate_events;"
```

**回滚红线**:
- 🔴 回滚前确认 `*.idx_rollback` 回滚点文件存在（记录建索引前行数与索引清单）
- 🔴 回滚后必须校验数据完整性与行数未变化
- ✅ 回滚会恢复建索引前状态，不影响任何事件数据

### 8.5 B-02 索引膨胀持续监控

```bash
# 每周执行一次膨胀评估
python3 $SCRIPT --db $DB --size

# 判读标准
#   索引/数据 < 15%        → 正常
#   索引/数据 15% ~ 30%    → 可接受，持续监控
#   索引/数据 > 30%        → 需精简索引（保留 idx_trace/idx_fault/idx_sev_ts 三个核心）
```

> **实测基线**: 10 万行沙箱实测 5 索引合计占数据体积 **76.26%**（远超 30% 阈值），
> 外推 500 万行为索引 652.7 MB / 数据 855.86 MB。
> **上线建议**: 首次仅建 3 个核心索引，观察查询命中后再评估是否加建次要索引。

### 8.6 B-03 WAL 非线性增长长期监控

```bash
# 每 6 小时巡检 WAL 增速（灰度期间强制）
df -h /var/lib/hermes/gray_gate_events.db
sqlite3 $DB "PRAGMA wal_checkpoint(PASSIVE); PRAGMA wal_pages; PRAGMA page_count;"

# 判读
#   WAL 增速 < 2 GB/小时    → 正常
#   WAL 增速 > 3 GB/小时    → 检查 checkpoint 是否正常执行
#   72h 累计 > 25.6 GB (80%) → 🔴 执行 TRUNCATE checkpoint 并上报
```

**长期监控策略**:
1. 灰度期间每 6 小时巡检，全量阶段每 24 小时巡检
2. 每次巡检记录 WAL 累计量与增速，绘制趋势线
3. 增速异常（>1.5 倍基线）时执行 `PRAGMA wal_checkpoint(FULL)`
4. 对齐 DSHB Phase2 观察到的非线性增长案例（3.2→16.0 GB，+400%），
   防止 WAL 日志未及时 checkpoint 导致提前触阈值

---

## 附录 A：灰度环境必备索引

```sql
-- A1: 主追溯索引（run_id + 时间 + 序列）
CREATE INDEX IF NOT EXISTS idx_trace ON gray_gate_events(run_id, ts, seq);

-- A2: 故障码检索
CREATE INDEX IF NOT EXISTS idx_fault ON gray_gate_events(fault_code, ts);

-- A3: 严重度检索
CREATE INDEX IF NOT EXISTS idx_sev_ts ON gray_gate_events(severity, ts);

-- A4: 决策类型
CREATE INDEX IF NOT EXISTS idx_decision ON gray_gate_events(decision, ts);

-- A5: 演练标记
CREATE INDEX IF NOT EXISTS idx_drill ON gray_gate_events(drill_tag, ts);

-- 验证索引
PRAGMA index_info(idx_trace);
ANALYZE;
```

**索引建立时机**: 灰度放量前一次性建立；单表 >200 万行时执行 `ANALYZE` 刷新统计信息。

## 附录 B：紧急回滚

```bash
# 若审计链路出现不可恢复问题，回滚到阶段开始前的快照
sqlite3 gray_gate_events.db ".backup 'gray_gate_events.db.bak.阶段开始前'"
# 紧急恢复
sqlite3 gray_gate_events.db ".restore 'gray_gate_events.db.bak.阶段开始前'"
```

**回滚后必须**: ① 校验 SHA256 链完整性 ② 重新与 DSHB/DSHE 对账 ③ 记录回滚事件到审计链。

---

*本 SOP 由 HERMES 生成于 V86-RC2 Phase4 灰度审计批次，基于实际灰度验证数据编制。*
