# V86-RC2 SQLite WAL 生产运维手册（T3.2）

> **工单**: 工单-HERMES / T3.2 SQLite WAL 生产运维手册
> **分支**: `feature/v85-chart-template` @ `1b3c6f2`
> **编制方**: HERMES (L3 审计方)
> **日期**: 2026-10-15
> **状态**: 📋 手册定稿
>
> **载体**: `event_store_wal_v2.py` (STORE_VERSION=2.0.0-wal)
> **约束**: NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE

---

## 0. 概述

上一轮 HA 仿真实测发现 JSONL 直写存在 **O(n) 退化**（0 事件 0.5ms → 500 事件 2.5ms）。WAL v2 实现 SQLite WAL 模式迁移，实现：

| 特性 | JSONL (v1) | WAL (v2) |
|------|-----------|----------|
| 小数据延迟 | 极快 (~0.5ms) | 中等 (~1ms) |
| 大数据延迟 | 崩塌 (数千 ms) | **恒定 (~915ms)** |
| 崩溃安全 | ⚠️ 需 checkpoint | ✅ WAL 自动恢复 |
| 读写并发 | ❌ 串行 | ✅ 读者不阻塞写者 |
| 去重 | O(n) 全量扫描 | ✅ 索引操作 |

**切换阈值**: `WAL_SWITCH_THRESHOLD = 10000`（基于实测 O(n) 拐点）

---

## 1. WAL 模式配置

### 1.1 PRAGMA 参数

```python
PRAGMAS = {
    "journal_mode": "WAL",      # 预写日志, 读写并发
    "synchronous": "NORMAL",    # 每次 commit fsync, 崩溃安全
    "cache_size": -8000,        # 8MB 页缓存
    "temp_store": "MEMORY",     # 临时表内存化
    "wal_autocheckpoint": 100,  # 每 100 页自动 checkpoint
    "busy_timeout": 5000,       # 锁等待 5 秒
    "foreign_keys": "ON",       # 外键约束
}
```

### 1.2 关键配置说明

| 参数 | 值 | 含义 | 生产建议 |
|------|-----|------|----------|
| `journal_mode` | WAL | 预写日志模式 | 必须启用，提供崩溃安全和读写并发 |
| `synchronous` | NORMAL | 每次 commit fsync | 不要用 FULL（性能减半），不要用 OFF（断电丢数据） |
| `cache_size` | -8000 | 8MB 页缓存 | 生产环境建议 16~32MB（-16000 ~ -32000） |
| `temp_store` | MEMORY | 临时表内存化 | 保持 MEMORY，减少磁盘 I/O |
| `wal_autocheckpoint` | 100 | 每 100 页自动 checkpoint | 可调整：高写入负载降至 50，读多写少升至 200 |
| `busy_timeout` | 5000 | 锁等待 5 秒 | 高并发场景增至 10000ms |

### 1.3 设置 WAL 的正确顺序

> ⚠️ **关键教训（自测发现）**：`PRAGMA journal_mode=WAL` 必须在无事务状态下执行，且会隐式提交。

```python
# ✅ 正确顺序
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA journal_mode=WAL")  # 独立事务，隐式提交
conn.execute("PRAGMA synchronous=NORMAL")
conn.execute("PRAGMA cache_size=-8000")
conn.execute("PRAGMA temp_store=MEMORY")
conn.execute("PRAGMA wal_autocheckpoint=100")
conn.execute("PRAGMA busy_timeout=5000")
conn.execute("PRAGMA foreign_keys=ON")

# ❌ 错误顺序：在事务内设置 WAL
conn.execute("BEGIN")
conn.execute("PRAGMA journal_mode=WAL")  # 隐式提交，破坏事务！
```

---

## 2. 自动切换逻辑

### 2.1 切换条件

```python
# 当 JSONLStore 事件数达到阈值时，自动 flush 到 WALStore
WAL_SWITCH_THRESHOLD = 10000

def _maybe_switch(self):
    if self._event_count >= WAL_SWITCH_THRESHOLD:
        if not self._switched:
            self._do_switch()
```

### 2.2 切换流程

```
JSONL 事件数达到 10000
    │
    ▼
_do_switch()
    │
    ├── 1. 读取 JSONL 全部事件到内存
    ├── 2. 创建 WAL 数据库
    ├── 3. 设置 PRAGMA (WAL + NORMAL + 缓存)
    ├── 4. 批量 INSERT OR IGNORE (原子去重)
    ├── 5. 更新元数据 (storage_mode=WAL)
    ├── 6. 提交事务
    └── 7. 标记 switched=True
    │
    ▼
后续写入直接走 WAL
```

### 2.3 ⚠️ 自测发现的静默失败

上一轮自测发现 3 个静默失败问题（代码不报错但结果错误）：

| # | 问题 | 表现 | 修复 |
|---|------|------|------|
| 1 | `force_wal` 逻辑反转 | 自动切换永不触发 | `self.switched = bool(force_wal)` |
| 2 | `make_event` 随机破坏幂等 | 崩溃恢复后去重失效（count=20 而非 10） | `rule_key` 不可用 `random.choice` |
| 3 | `set_meta` 未 commit | 切换元数据为 None | 追加 `commit()` |

---

## 3. 故障恢复

### 3.1 进程崩溃（优雅处理）

**场景**: 审计器进程被 SIGKILL 或 OOM Killer 终止。

**恢复机制**:
- WAL 文件 (`*.db-wal`) 持久化在磁盘
- 下次 `open` 数据库时，SQLite 自动从 WAL 文件恢复未 checkpoint 的数据
- `synchronous=NORMAL` 保证每次 commit 已 fsync，不会丢失已提交事务

**验证**:
```bash
# 模拟进程崩溃
kill -9 <pid>

# 验证数据完整性
python3 -c "
from event_store_wal_v2 import WALStore
store = WALStore('/path/to/events.db')
print('events after crash:', store.stats()['total_events'])
"
```

### 3.2 断电恢复

**场景**: 服务器意外断电。

**恢复机制**:
- `synchronous=NORMAL`: 每次 commit 的 WAL 数据已 fsync 到磁盘
- 未 checkpoint 的数据在 WAL 文件中持久化
- 下次启动时 SQLite 自动重放 WAL

**风险**: 最后一次 commit 到断电之间如果有未 checkpoint 的数据，WAL 文件完整保存；如果有未 commit 的写入，数据丢失（这是任何数据库的固有行为）。

### 3.3 数据库损坏

**场景**: SQLite 数据库文件损坏（磁盘错误/文件截断）。

**恢复流程**:

```bash
# 1. 检查数据库完整性
sqlite3 events.db "PRAGMA integrity_check;"
# 期望: ok

# 2. 如果 integrity_check 失败，尝试从 WAL 恢复
#    先删除损坏的数据库，用备份恢复
cp events.db.bak events.db
sqlite3 events.db "PRAGMA integrity_check;"

# 3. 如果 WAL 文件损坏但主数据库完好
#    删除 WAL 文件，SQLite 会使用主数据库中的最后 checkpoint
rm events.db-wal
sqlite3 events.db "PRAGMA wal_checkpoint(TRUNCATE);"

# 4. 如果完全损坏，从最近备份恢复
#    备份策略见 §5
```

### 3.4 崩溃后去重保持

**关键验证**: 崩溃恢复后，去重逻辑必须仍然有效。

```python
# 崩溃前写入 10 条唯一事件
store.append_events([make_event(i) for i in range(10)])

# 模拟崩溃（直接删除进程句柄）
del store

# 重新打开
store = WALStore(db_path)
print(store.stats()['total_events'])  # 应为 10

# 再次写入相同的 10 条
store.append_events([make_event(i) for i in range(10)])
print(store.stats()['total_events'])  # 仍应为 10（去重生效）
```

---

## 4. WAL 文件归档与清理

### 4.1 WAL 文件生命周期

```
写入数据
    │
    ▼
WAL 文件增长 (*.db-wal)
    │
    ├── 每 100 页 → 自动 checkpoint → WAL 文件截断
    │
    └── 手动 checkpoint → PRAGMA wal_checkpoint(TRUNCATE)
         │
         ▼
    WAL 文件归零（所有数据已合并到主数据库）
```

### 4.2 自动 Checkpoint

`wal_autocheckpoint=100` 意味着每 100 个 WAL 页面（约 500KB）自动执行一次 checkpoint。

**Checkpoint 类型**:

| 类型 | 命令 | 行为 | 适用场景 |
|------|------|------|----------|
| PASSIVE | `PRAGMA wal_checkpoint(PASSIVE)` | 不等待读者，可能部分 checkpoint | 在线维护 |
| FULL | `PRAGMA wal_checkpoint(FULL)` | 等待所有读者释放锁 | 低流量时段 |
| TRUNCATE | `PRAGMA wal_checkpoint(TRUNCATE)` | checkpoint 后截断 WAL 文件到 0 | **推荐：每日定时** |

### 4.3 手动清理流程

```bash
# 日常清理（每日凌晨低流量时段）
sqlite3 /path/to/events.db "PRAGMA wal_checkpoint(TRUNCATE);"
# 输出: (0, 0, 0) 表示无活跃 WAL 帧

# 检查 WAL 文件大小
ls -lh /path/to/events.db-wal
# 如果 > 50MB，考虑增大 cache_size 或减少写入频率
```

### 4.4 归档策略

```bash
# 每日备份（生产环境）
BACKUP_DIR=/data/backups/hermes-audit
DATE=$(date +%Y%m%d)
sqlite3 /path/to/events.db ".backup ${BACKUP_DIR}/events_${DATE}.db"

# 保留最近 7 天备份
find ${BACKUP_DIR} -name "events_*.db" -mtime +7 -delete

# 验证备份完整性
sqlite3 ${BACKUP_DIR}/events_${DATE}.db "PRAGMA integrity_check;"
```

---

## 5. 监控指标

### 5.1 关键指标

| # | 指标 | 采集方式 | 告警阈值 | 严重度 |
|---|------|----------|----------|--------|
| M1 | WAL 文件大小 | `ls -l *.db-wal` | > 50MB | WARNING |
| M2 | 数据库完整性 | `PRAGMA integrity_check` | != `ok` | **CRITICAL** |
| M3 | Checkpoint 成功率 | `wal_checkpoint` 返回值 | busy > 0 | WARNING |
| M4 | 写入延迟 (p95) | 应用层埋点 | > 200ms | WARNING |
| M5 | 写入延迟 (p99) | 应用层埋点 | > 500ms | HIGH |
| M6 | 磁盘使用率 | `df -h` | > 85% | WARNING |
| M7 | 磁盘使用率 | `df -h` | > 95% | **CRITICAL** |
| M8 | 事件总数 | `stats()['total_events']` | — | INFO |
| M9 | 去重命中率 | `dedup_count / total_appended` | > 50% | INFO（可能重复上报） |
| M10 | 切换次数 | `switched` 标志 | — | INFO |

### 5.2 监控脚本

```bash
#!/bin/bash
# wal_monitor.sh — 每 5 分钟执行
DB=/path/to/events.db
WAL="${DB}-wal"
BACKUP="/var/log/hermes-wal-monitor.log"

# M1: WAL 文件大小
if [ -f "$WAL" ]; then
    WAL_SIZE=$(stat -c%s "$WAL" 2>/dev/null || echo 0)
    if [ "$WAL_SIZE" -gt 52428800 ]; then
        echo "$(date) WARNING: WAL size ${WAL_SIZE}B > 50MB" >> "$BACKUP"
    fi
fi

# M2: 完整性检查
INTEGRITY=$(sqlite3 "$DB" "PRAGMA integrity_check;" 2>/dev/null)
if [ "$INTEGRITY" != "ok" ]; then
    echo "$(date) CRITICAL: integrity_check=$INTEGRITY" >> "$BACKUP"
fi

# M4: 磁盘使用率
DISK_USAGE=$(df /path/to/ | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$DISK_USAGE" -gt 95 ]; then
    echo "$(date) CRITICAL: disk usage ${DISK_USAGE}%" >> "$BACKUP"
elif [ "$DISK_USAGE" -gt 85 ]; then
    echo "$(date) WARNING: disk usage ${DISK_USAGE}%" >> "$BACKUP"
fi

# 每日 checkpoint
HOURLY=$(date +%H)
if [ "$HOURLY" = "03" ] && [ "$(date +%M)" -lt "5" ]; then
    sqlite3 "$DB" "PRAGMA wal_checkpoint(TRUNCATE);" >> "$BACKUP" 2>&1
    echo "$(date) INFO: daily checkpoint complete" >> "$BACKUP"
fi
```

---

## 6. 告警触发条件

### 6.1 告警矩阵

| 级别 | 条件 | 动作 | 通知 |
|------|------|------|------|
| **CRITICAL** | 完整性检查失败 | 立即停止写入，触发备份恢复 | 人工介入 |
| **CRITICAL** | 磁盘使用率 > 95% | 暂停写入，执行清理 | 人工介入 |
| **HIGH** | 写入延迟 p99 > 500ms | 检查 WAL 大小，增大 cache_size | 值班通知 |
| **WARNING** | WAL 文件 > 50MB | 执行 TRUNCATE checkpoint | 值班通知 |
| **WARNING** | 磁盘使用率 > 85% | 执行归档清理 | 值班通知 |
| **INFO** | 去重命中率 > 50% | 检查是否有重复上报 | 日志记录 |

### 6.2 告警升级规则

```
INFO (日志记录)
    │ 持续 1 小时未恢复
    ▼
WARNING (值班通知)
    │ 持续 30 分钟未恢复
    ▼
HIGH (告警通知)
    │ 持续 15 分钟未恢复 或 出现 CRITICAL 条件
    ▼
CRITICAL (人工介入)
```

---

## 7. 性能调优

### 7.1 参数调优指南

| 场景 | cache_size | wal_autocheckpoint | busy_timeout | 说明 |
|------|-----------|-------------------|--------------|------|
| 低写入（< 100 事件/小时） | -8000 (8MB) | 100 | 5000 | 默认配置 |
| 中等写入（100~1000/小时） | -16000 (16MB) | 50 | 10000 | 减少 checkpoint 频率 |
| 高写入（> 1000/小时） | -32000 (32MB) | 20 | 15000 | 最大化写入吞吐 |
| 高并发读写 | -16000 (16MB) | 100 | 20000 | 增大锁等待 |

### 7.2 批量写入优化

```python
# ✅ 批量写入（推荐）
events = []
for event in incoming_events:
    events.append(normalize_event(event))
store.append_events(events)  # 一次 commit

# ❌ 逐条写入（每次 commit 都 fsync）
for event in incoming_events:
    store.append_events([normalize_event(event)])
```

### 7.3 Checkpoint 时机优化

| 时机 | 动作 | 原因 |
|------|------|------|
| 每日凌晨 3:00 | TRUNCATE checkpoint | 低流量时段，不影响在线 |
| 手动切换前 | FULL checkpoint | 确保 WAL 数据已合并 |
| 备份前 | PASSIVE checkpoint | 减少备份数据量 |
| 磁盘告警时 | TRUNCATE checkpoint | 释放磁盘空间 |

---

## 8. 容量规划

### 8.1 磁盘空间估算

| 参数 | 值 | 来源 |
|------|-----|------|
| 单事件平均大小 | ~500 bytes | 8 字段 + 元数据 |
| 每日事件量（中等负载） | ~10,000 条 | 审计包频率估算 |
| 每日 WAL 增量 | ~5 MB | 10,000 × 500B |
| 每日主数据库增量（checkpoint 后） | ~5 MB | 同上 |
| 7 天保留 | ~70 MB | 5MB × 14 |

**推荐配置**: 500MB 专用分区，预留 3x 余量。

### 8.2 事件保留策略

| 事件级别 | 保留期 | 归档策略 |
|----------|--------|----------|
| CRITICAL | 永久 | 不自动清理 |
| HIGH | 30 天 | 30 天后归档 |
| MEDIUM | 7 天 | 7 天后归档 |
| LOW / INFO | 2 天 | 2 天后自动清理 |

---

## 9. 故障处置 SOP

### 9.1 快速处置流程

```
故障发现
    │
    ├── CRITICAL (完整性失败/磁盘满)
    │       │
    │       ├── 1. 停止写入 (暂停审计调度器)
    │       ├── 2. 检查日志: tail -100 /var/log/hermes-audit.log
    │       ├── 3. 从备份恢复: sqlite3 backup.db ".recover" events.db
    │       ├── 4. 验证: PRAGMA integrity_check → ok
    │       └── 5. 恢复写入
    │
    ├── WARNING (WAL 过大/磁盘接近满)
    │       │
    │       ├── 1. 执行 TRUNCATE checkpoint
    │       ├── 2. 清理过期备份
    │       └── 3. 验证 WAL 文件已缩小
    │
    └── INFO (去重率异常/延迟偏高)
            │
            ├── 1. 检查是否有重复上报源
            ├── 2. 检查 cache_size 是否充足
            └── 3. 记录观察，暂不干预
```

### 9.2 恢复验证清单

恢复后逐项验证：

- [ ] `PRAGMA integrity_check` → `ok`
- [ ] `PRAGMA journal_mode` → `wal`
- [ ] 事件总数与预期一致
- [ ] 去重逻辑有效（重试写入相同事件，总数不变）
- [ ] 写入延迟恢复正常（< 200ms）
- [ ] 告警已清除

---

## 10. 与 JSONL 的兼容

### 10.1 兼容 API

WAL v2 与 v1 JSONL 版 API 完全兼容：

| API | v1 JSONL | v2 WAL | 说明 |
|-----|----------|--------|------|
| `normalize_event(e)` | ✅ | ✅ | 事件标准化 |
| `make_event_id(e)` | ✅ | ✅ | 8 字段 MD5 |
| `append_events(evs)` | ✅ | ✅ | 批量写入 |
| `query(**kwargs)` | ✅ | ✅ | 多维检索 |
| `stats()` | ✅ | ✅ | 统计信息 |

### 10.2 自动切换后的兼容

切换后，上层调用方**零改动**。JSONLStore 透明代理到 WALStore，API 不变。

### 10.3 ⚠️ 切换注意事项

| 注意事项 | 说明 |
|----------|------|
| 切换后去重语义 | WAL 用 `INSERT OR IGNORE`（event_id PRIMARY KEY），与 JSONL 全量扫描语义一致 |
| 切换后查询兼容 | WAL 用 SQL WHERE 条件，支持 JSONL 版不支持的复杂查询 |
| 切换后恢复兼容 | 崩溃恢复走 SQLite WAL 重放，比 JSONL checkpoint 更可靠 |

---

## 11. 生产部署检查清单

- [ ] WAL 模式已启用（`PRAGMA journal_mode` → `wal`）
- [ ] `synchronous=NORMAL`（非 FULL/OFF）
- [ ] `cache_size` 已根据负载调优（默认 8MB，高负载 16~32MB）
- [ ] 自动切换阈值已确认（默认 10000）
- [ ] Checkpoint 定时任务已配置（每日 03:00 TRUNCATE）
- [ ] 备份脚本已配置（每日 .backup，保留 7 天）
- [ ] 监控脚本已部署（WAL 大小 / 完整性 / 磁盘 / 延迟）
- [ ] 告警规则已配置（CRITICAL / HIGH / WARNING）
- [ ] 磁盘预留 3x 余量
- [ ] 故障处置 SOP 已培训

---

*本手册基于 `event_store_wal_v2.py` (v2.0.0-wal) 实测数据编制。所有阈值和参数均可在生产环境中根据实际负载调整，但调整前应在 staging 环境验证。*
