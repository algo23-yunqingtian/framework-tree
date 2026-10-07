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

## 8. 复合索引运维（Phase5 新增 / Phase7 分层更新）
### 8.0 索引分层（Phase7 新增 / Phase8 生产校准）

灰度环境索引分为**两层**，由 `phase5_index_deploy.py` 统一管理：

| 层 | 索引 | 首次上线 | 查询用途 |
|----|------|---------|---------|
| **基础（3 核心）** | `idx_trace` / `idx_fault` / `idx_sev_ts` | ✅ 必须 | 审计追溯 / 故障回放 / 链路追踪 |
| **扩展（2 个）** | `idx_decision` / `idx_drill` | ⏸️ 延后 | 决策筛选 / 演练复盘 |

```bash
python3 phase5_index_deploy.py --db <DB> --create                      # 仅 3 核心（默认）
python3 phase5_index_deploy.py --db <DB> --create --enable-extra-index # 5 索引
python3 phase5_index_deploy.py --db <DB> --create --indexes idx_trace,idx_fault,idx_sev_ts  # Phase8 兼容形式
```

#### 8.0.1 膨胀数据（三源实测，Phase8 校准）

| 来源 | 样本 | 3 核心 | 5 索引 | 3 核心比值 |
|------|------|--------|--------|-----------|
| Phase7 沙箱（10 万行） | 100,000 | 9.671 MB | 16.22 MB | **62.46%**（小样本假象） |
| Phase7 外推 | 500 万行 | 483.53 MB | — | 62.46%（❌ 错误外推） |
| **HERMES 沙箱（500 万行）** | 5,000,000 | **360.464 MB** | **591.188 MB** | **38.63%** |
| **DSHE 生产实测** | 1,171,856 | **89.7 MB** | — | **46.9%**（72h 微降至 41.3%） |

> **🔴 Phase8 更正**: Phase7 的 62.46% 与 483.53MB 为**小样本假象**。
> 三源实测比值在 **38.63%~46.9%** 区间，均低于 **50% 熔断线**，3 核心方案安全。
> **索引膨胀比值不可跨样本规模与数据分布外推**（见追溯规范 §7.9.1）。
> 生产 46.9% 距 40% 警告线之上、50% 熔断线之下，**B-02 为 MITIGATED（受控缓解）而非 CLOSED**，
> 须按 §9.2 持续监控。

#### 8.0.2 膨胀监控阈值（四档，Phase8 生产校准后调整）

| 区间 | 状态 | 动作 | 频率 |
|------|------|------|------|
| < 15% | 🟢 正常 | 常规巡检 | 每周 |
| 15% ~ 30% | 🟡 可接受 | 记录趋势 | 每两周 |
| 30% ~ 45% | 🟠 警告 | 每 6 小时巡检，准备精简方案 | 每 6 小时 |
| **45% ~ 50%** | 🔴 **严重（生产首即落此区间）** | **立即评估索引范围，准备回滚** | **每日 + 实时** |
| **> 50%** | ⛔ **熔断** | **立即回滚**（约 15 min） | — |

> **⚠️ B-16 阈值建议**: DSHB 预案 V1.2 设严重线 45%，生产实测首即 46.9%。
> 建议严重线调整为 **48%**，与实测基线 + 微降趋势对齐。

### 8.1 创建复合索引

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

## 9. 生产索引上线观测与审计检索异常排查（Phase8 新增）

> **对应工单**: `HERMES_V86_RC2_HERMES_PHASE8_ONLINE_INDEX_TRACE_AUDIT_VERIFY`
> **上游预案**: DSHB《G1 索引生产执行预案 V1.2》（02:00–04:00 UTC 窗口）
> **生产实测**: DSHE Phase8《L2 大盘线上索引变更观测》commit `1ed048a`
> **配套报告**: `v86_rc2_hermes_phase8_online_audit_index_verify_report.md`
> **对应风险**: B-02 索引膨胀（生产实测 46.9%，处严重区间）、B-16 熔断阈值偏紧

### 9.1 生产变更窗口执行清单（02:00–04:00 UTC）

> **命令接口规范（Phase8 更新）**: 生产命令统一使用 `--indexes` 参数（与 DSHB 预案 V1.2 对齐）。
> Phase8 已新增该参数的兼容实现，省略时等价于默认 3 核心。
> **DSHE 生产实测已验证该命令可正常执行**（创建 3 核心耗时 16.0 min，含 ANALYZE + checkpoint）。

```bash
SCRIPT=/var/lib/hermes/scripts/phase5_index_deploy.py
DB=/var/lib/hermes/gray_gate_events.db
IDX='idx_trace,idx_fault,idx_sev_ts'    # 仅 3 核心，不含 idx_decision/idx_drill

# ---- 窗口 T-10min：前置检查 ----
python3 $SCRIPT --db $DB --check                          # 期望 exit 0
python3 $SCRIPT --db $DB --size                           # 记录基线比值
sqlite3 $DB "PRAGMA integrity_check; SELECT COUNT(*) FROM gray_gate_events;"

# ---- 窗口 T+0min：创建 3 核心索引 ----
python3 $SCRIPT --db $DB --create --indexes $IDX          # 期望 exit 0
# 输出 "ℹ️ --indexes=... 与默认 3 核心范围一致（no-op）" 为预期行为，无需干预
# 生产实测: idx_trace 6min → idx_fault 3min → idx_sev_ts 5min + ANALYZE/checkpoint 1min = 16.0min

# ---- 窗口 T+15min：命中验证 + 存储复核 ----
python3 $SCRIPT --db $DB --verify --indexes $IDX          # 期望 3/3 命中
python3 $SCRIPT --db $DB --size --indexes $IDX            # 生产实测 ~46.9%

# ---- 窗口 T+20min：审计追溯链路回归（3 条核心查询，均带时间窗）----
sqlite3 $DB "SELECT COUNT(*) FROM gray_gate_events WHERE run_id='<当前run>' AND ts > '<窗口起点>' ORDER BY seq;"
sqlite3 $DB "SELECT event_id, ts FROM gray_gate_events WHERE fault_code='C1' AND ts > '<窗口起点>' LIMIT 100;"
sqlite3 $DB "SELECT event_id, ts FROM gray_gate_events WHERE severity='CRITICAL' AND ts > '<窗口起点>' LIMIT 100;"

# ---- 窗口 T+25min：回滚可逆性演练 ----
python3 $SCRIPT --db $DB --rollback --indexes $IDX        # 期望 exit 0 + integrity=ok + 行数不变
python3 $SCRIPT --db $DB --create --indexes $IDX          # 重建
python3 $SCRIPT --db $DB --verify --indexes $IDX          # 确认恢复 3/3
```

### 9.2 观测指标与判定阈值

| 指标 | 观测方式 | 阈值 | 生产实测（DSHE Phase8） | 触发动作 |
|------|---------|------|----------------------|---------|
| 索引/数据比值 | `--size` | <15% 正常 / 15~30% 可接受 / 30~40% 警告 / **40~45% 观察 / 45~50% 严重** / **>50% 熔断** | **46.9%**（72h 微降至 41.3%） | 超 45% 评估；>50% 回滚 |
| WAL 写入 P99 | `M-P99-WAL-WRITE` | **≤10ms 警告 / ≤20ms 严重 / ≤50ms 熔断** | **3.1ms**（上线前 1.485ms，+1.615ms） | 超 10ms 检查 fsync 抖动 |
| 查询 P99 | 各索引查询 | ≤50ms（DSHB 目标） | idx_trace **3.4ms** / idx_fault **2.2ms** / idx_sev_ts **3.9ms** | 超 100ms 触发 AL-002 |
| 索引创建耗时 | `--create` 输出 | ~12 min（DSHB 预估 117 万行） | **16.0 min（+33.3%）** | 超 120s/索引告警不中断 |
| 回滚耗时 | `--rollback` 输出 | ~15 min | — | 超时立即上报 |
| 审计事件丢失 | `integrity_check` + 行数校验 | 0 丢失 | **100% 完整** | 任何丢失立即中止窗口 |

> **⚠️ 阈值调整建议（B-16）**: DSHB 预案 V1.2 原设「40 警告 / 45 严重 / 50 熔断」。
> 生产实测首即 46.9%，**已落严重区间**。建议将严重线从 45% 调整为 **48%**，
> 与 117 万行实测基线 + 72h 微降趋势（46.9%→41.3%）对齐，避免误熔断。
> **B-02 不关闭**，须持续监控。

### 9.3 审计检索异常排查四步法

**症状**: 索引上线后审计追溯查询变慢或返回异常。

```bash
# 步骤1：确认索引是否命中（区分「索引失效」与「索引命中但慢」）
python3 $SCRIPT --db $DB --verify --indexes $IDX
#   输出「USING INDEX/COVERING INDEX」= 已命中
#   输出「SCAN gray_gate_events」      = 索引失效，转步骤2

# 步骤2：索引失效排查
sqlite3 $DB "ANALYZE; EXPLAIN QUERY PLAN SELECT * FROM gray_gate_events WHERE run_id='x';"
sqlite3 $DB "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';"

# 步骤3：索引命中但慢 → 先查查询形态，再查选择性（顺序不可颠倒）
#   判定A — 查询是否带时间窗切片？
#     带时间窗 → 正常，生产实测 248~383× 收益，应 <5ms
#     不带时间窗 → 转判定B
#   判定B — 选择性（按追溯规范 §7.9.2 决策矩阵，仅适用全量物化）：
#     <1%    → 索引应生效，收紧 ts 时间窗 ≤1 小时
#     1~15%  → 索引收益有限，属正常
#     >15%   → **索引净负收益，属预期行为，非故障** → 改用时间窗切片或离线归档

# 步骤4：确认审计链路完整性（索引变更不应影响）
sqlite3 $DB "PRAGMA integrity_check; SELECT COUNT(*) FROM gray_gate_events;
             PRAGMA table_info(gray_gate_events);"
#   三项校验：integrity=ok / 行数与回滚前一致 / 22 列结构未变
```

> **Phase8 关键教训（两步排查顺序不可颠倒）**:
> 1. **先查查询形态（是否带时间窗），再查选择性** —— DSHE 生产实测显示带时间窗查询
>    `idx_fault` 383.2×、`idx_sev_ts` 248.0× 收益，而 HERMES 沙箱的全量物化查询测出「净负收益」。
>    **同一索引、同一表，因查询形态不同结论完全相反**。
> 2. **「索引命中 ≠ 查询更快」仅适用于全量物化查询**。
>    遇到「有索引却更慢」时，**不要先怀疑索引失效**，先确认查询是否带时间窗切片。

### 9.4 生产上线后持续监控（DSHE 72h 实测基线）

| # | 事项 | 生产实测基线 |
|---|------|-------------|
| 1 | 72h 线上事件量 | 1,194,312 事件 / 36 检查点 |
| 2 | 指标稳定性 | CV = 0.0035（极低方差） |
| 3 | 索引膨胀趋势 | **46.9% → 41.3%（微降）** |
| 4 | 告警抑制率 | 1,287 样本 / 76.2% / Wilson CI [74.8%, 77.6%] |
| 5 | INDEX-HIT 准确率 | 99.98% |
| 6 | 16 指标连续性 | 158,400 点 / 0 缺失 |
| 7 | DSHB/HERMES 跨团队对账 | **12/12 对齐（100%）** |
| 8 | 新增缺陷 | **0** |
| 9 | 状态机 | 4/4 稳定 |
| 10 | 告警验证 | 5 活跃（3 核心）+ 2 预留零误报 |

### 9.5 延后索引迭代决策（G1 灰度 StageB 20% 后）

| 项 | 决策依据 |
|----|---------|
| **禁止依据** | ❌ Phase7 的「149× 退化」结论（沙箱分布特有，不可外推） |
| **禁止依据** | ❌ HERMES 沙箱的「低选择性净负收益」结论（仅适用全量物化查询） |
| **正确依据** | ✅ 生产真实查询模式统计（混合查询占 85%，均带时间窗） |
| **正确依据** | ✅ 生产真实字段匹配占比 |
| **正确依据** | ✅ 启用后对索引/数据比值的影响（当前 41.3%，启用 2 索引将升至 ~63%，逼近 50% 熔断线） |
| **建议时点** | 待比值降至 40% 以下再评估，或先统一表结构定义（HERMES 多独立索引 vs DSHB 单复合索引） |

### 9.6 与 §8 的关系

- **§8** 定义索引分层（3 核心 + 2 扩展）与分层运维流程，适用于**灰度/沙箱环境**
- **§9** 定义**生产变更窗口**内的观测、验证与异常排查，是 §8 在生产环境的执行补充
- 两者共用 `phase5_index_deploy.py` 的 5 个模式，§9 统一使用 `--indexes` 参数形式

---

## 附录 A：灰度环境索引（Phase7 分层：3 核心 + 2 扩展）

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

**版本记录**:
- **v1.0**（Phase4）: 灰度审计 SOP 首版，含 WAL 审计 + 异常排查三步法
- **v1.1**（Phase5）: 新增 §8 复合索引运维、异常排查第四步「索引退化」
- **v1.2**（Phase7）: §8 索引分层（3 核心 + 2 扩展）、`--enable-extra-index` 开关、延后索引退化风险、四档膨胀阈值、Phase5 膨胀数据更正（76.26% → 104.76%）
- **v1.3**（Phase8）: 新增 §9 生产索引上线观测（02:00–04:00 UTC 窗口清单、`--indexes` 命令规范、观测阈值 + DSHE 生产实测基线、检索异常排查四步法、持续监控 10 项、延后索引迭代决策依据）、§8.0 三源实测膨胀校准、四档阈值新增「45~50% 严重」区间、B-16 阈值调整建议

---

*本 SOP 由 HERMES 生成于 V86-RC2 Phase4 灰度审计批次，基于实际灰度验证数据编制。
v1.3（Phase8）关键教训：① 膨胀比值不可跨样本规模与数据分布外推；
② 同一索引因查询形态不同结论完全相反（沙箱全量物化净负收益 vs 生产带时间窗 248~383× 收益）；
③ 排查顺序不可颠倒——先查查询形态再查选择性；
④ 「参数被接受但语义静默失效」比直接报错更危险。*
