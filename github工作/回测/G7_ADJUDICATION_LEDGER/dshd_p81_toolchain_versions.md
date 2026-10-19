# DSHD-P81 工具链版本管理

**生成时间**: 2026-10-19 13:24:03 (GMT+8)  
**任务**: DSHD-P81-GIT-SAVE  
**令牌**: DSHD-P81-GIT-SAVE-TOKEN  
**基线**: feature/v88-g1 HEAD=43a03df  
**模式**: AUDIT_READ_ONLY | wind_api_calls=0 | intervention=NONE  

> 本文件为 P81 监控工具链的**永久版本管理文档**。  
> 与 `dshd_cluster_brief.md`（每 5 分钟由 watcher 重生成、会覆盖动态内容）不同，  
> 本文件是静态的、版本化的、不会因 watcher 轮询而被修改。  
> SHA 快照真源：`G7_ADJUDICATION_LEDGER/p81_version_history.json`。

---

## 一、Tracked / Untracked 文件区分规则

### 1.1 Tracked（已入库，受 git 保护）

以下文件在 `DSHD-P81-GIT-SAVE` commit 之后纳入 git 跟踪：

| 文件 | 角色 | v1.2.0-TWEAK SHA256 |
|---|---|---|
| `recreate_p81.py` | 生成器（Python, LF） | 5e58f67584a11af3… |
| `recreate_p81.tweak_snapshot.py` | 生成器快照 | 5e58f67584a11af3… |
| `dshd_p81_watch.ps1` | 活跃 PS1（UTF-8 BOM） | 28897f43b7cd7dfd… |
| `dshd_p81_watch.v1.2.0-TWEAK.ps1` | PS1 快照 | 28897f43b7cd7dfd… |
| `patch_p81_ext.py` | EXT 补丁（非幂等） | 02ca5a7a48561f17… |
| `patch_p81_tweak.py` | TWEAK 补丁（非幂等） | 5fb39d3d70ef39eb… |
| `patch_p81_brief.py` | 简报补丁 | 8f2d4f0f5564e596… |
| `patch_p81_fast_excel.py` | 快采样补丁 | 06b31f780a8ca232… |
| `test_p81_ext.ps1` | EXT 冒烟测试 | 4767a43bbb964c8b… |
| `test_p81_tweak.ps1` | TWEAK 冒烟测试 | ae5ebb89593d9521… |
| `verify_p81_ext.ps1` | EXT 语法检查 | 746139f351b56081… |
| `verify_p81_tweak_syntax.ps1` | TWEAK 语法检查 | 03b97daacf21f8fe… |
| `p81_safe_edit.py` | **备份钩子（新增）** | 49865908a40fd3c2… |
| `p81_safe_edit.ps1` | 钩子 PS1 包装器（新增） | ed7e160775b83a33… |
| `p81_version_history.json` | SHA 版本台账（新增） | a9ba54473bd77e1f… |

### 1.2 Untracked（不入库，`.gitignore` 已覆盖）

| 文件 | 原因 |
|---|---|
| `_p81_snapshots/*.bak` | 本地快照备份，由 `.gitignore` 的 `*.bak` 规则忽略 |
| `artifacts/dshd_p81_watch_*.json` | watcher 运行时快照（动态） |
| `dshd_p81_watch.log` | watcher 日志 |
| `tracking_monitor_audit.jsonl` | 全集群共享审计账本（被多个 agent 追加） |
| `artifacts/dshd_cluster_brief.md` | watcher 每 5 分钟重生成 |

### 1.3 判定规则

```
git status --short  # 查看 tracked/untracked 状态
```

- `M` 开头 = tracked 且已修改
- `??` = untracked（新增）
- 无输出 = 文件被 `.gitignore` 忽略

---

## 二、快照与 .bak 备份机制

### 2.1 触发时机

**后续修改 P81 工具链文件前，必须先执行备份钩子：**

```powershell
# 单文件备份
python p81_safe_edit.py snapshot recreate_p81.py --agent DSHD-P81 --reason "pre-edit tweak"

# 多文件批量备份
python p81_safe_edit.py snapshot recreate_p81.py dshd_p81_watch.ps1 --agent DSHD-P81

# 写入审计账本
python p81_safe_edit.py snapshot recreate_p81.py --agent DSHD-P81 --ledger
```

### 2.2 快照文件命名

```
_p81_snapshots/<name>.<YYYYMMDD_HHMMSS>.<agent>.bak
```

示例：
```
_p81_snapshots/recreate_p81.20261019_132403.DSHD-P81.bak
```

- 同秒多次快照自动加 PID 后缀去重
- `.bak` 扩展名被 `.gitignore` 忽略，不污染 git status
- 快照文件与原始文件**不在同一目录**（避免混乱）

### 2.3 SHA 版本台账

所有快照记录写入 `p81_version_history.json`：

```json
{
  "_meta": {
    "created_at": "2026-10-19T13:24:03+0800",
    "script_version": "v1.0.0",
    "task": "DSHD-P81-GIT-SAVE",
    "token": "DSHD-P81-GIT-SAVE-TOKEN",
    "protected_files": [...],
    "snapshot_dir": "D:\\...\\_p81_snapshots"
  },
  "entries": [
    {
      "snapshot_id": "recreate_p81.20261019_132403.DSHD-P81",
      "file": "recreate_p81.py",
      "action": "PRE_EDIT_SNAPSHOT",
      "agent": "DSHD-P81",
      "reason": "DSHD-P81-GIT-SAVE: baseline snapshot",
      "timestamp": "2026-10-19T13:24:03+0800",
      "pre_edit": {
        "sha256": "5e58f67584a11af3...",
        "size_bytes": 136511,
        "mtime": "2026-10-19T12:46:40+0800"
      },
      "snapshot_file": "D:\\...\\_p81_snapshots\\recreate_p81.20261019_132403.DSHD-P81.bak",
      "snapshot_sha256": "5e58f67584a11af3...",
      "snapshot_size_bytes": 136511
    }
  ]
}
```

### 2.4 保护清单

`p81_safe_edit.py` 只允许备份以下 15 个文件（硬编码 `P81_PROTECTED` 集合）：

```
recreate_p81.py
recreate_p81.tweak_snapshot.py
dshd_p81_watch.ps1
dshd_p81_watch.v1.2.0-TWEAK.ps1
patch_p81_ext.py
patch_p81_tweak.py
patch_p81_brief.py
patch_p81_fast_excel.py
test_p81_ext.ps1
test_p81_tweak.ps1
verify_p81_ext.ps1
verify_p81_tweak_syntax.ps1
p81_safe_edit.py
p81_safe_edit.ps1
p81_version_history.json
```

**尝试备份清单外的文件会被拒绝**（exit code 2），例如：
```
$ python p81_safe_edit.py snapshot dshd_p67_monitor_log.jsonl
{"file": "dshd_p67_monitor_log.jsonl", "ok": false, "error": "file 'dshd_p67_monitor_log.jsonl' is not in the P81_PROTECTED list. Refusing."}
```

---

## 三、版本回滚操作指引

### 3.1 查看可用快照

```powershell
# 列出所有快照
python p81_safe_edit.py history

# 列出某文件的所有快照
python p81_safe_edit.py history recreate_p81.py

# 简化版
python p81_safe_edit.py list recreate_p81.py
```

### 3.2 回滚到指定版本

```powershell
# 语法
python p81_safe_edit.py restore <file> --from <snapshot_id> --agent <label> --reason <text>

# 示例：回滚 recreate_p81.py 到基线快照
python p81_safe_edit.py restore recreate_p81.py \
  --from recreate_p81.20261019_132403.DSHD-P81 \
  --agent DSHD-P81 \
  --reason "rollback to v1.2.0-TWEAK baseline" \
  --ledger
```

**回滚流程**：
1. 钩子自动对当前文件做 **pre-restore 快照**（防止回滚失败无法恢复）
2. 从 `_p81_snapshots/` 复制 `.bak` 文件覆盖目标
3. 校验 SHA256 匹配
4. 记录 `RESTORE` 事件到 `p81_version_history.json`
5. 可选写入审计账本

### 3.3 回滚验证

```powershell
# 验证回滚后文件 SHA 与快照一致
python p81_safe_edit.py check recreate_p81.py

# 输出应包含回滚前的 SHA（即快照的 SHA）
{"file": "recreate_p81.py", "ok": true, "exists": true, "sha256": "5e58f67584a11af3...", ...}
```

### 3.4 回滚到 git commit

如果本地快照丢失，可以从 git 恢复：

```bash
# 查看文件历史
git log --oneline -- G7_ADJUDICATION_LEDGER/recreate_p81.py

# 恢复到指定 commit
git checkout <commit_hash> -- G7_ADJUDICATION_LEDGER/recreate_p81.py

# 恢复所有 P81 文件到指定 commit
git checkout <commit_hash> -- G7_ADJUDICATION_LEDGER/recreate_p81.py \
    G7_ADJUDICATION_LEDGER/dshd_p81_watch.ps1 \
    G7_ADJUDICATION_LEDGER/patch_p81_tweak.py
```

---

## 四、完整操作示例

### 4.1 安全修改流程

```powershell
# 1. 备份当前版本
python p81_safe_edit.py snapshot recreate_p81.py --agent DSHD-P81 --reason "pre-tweak-3"

# 2. 编辑文件（用任意编辑器）
# ... 修改 recreate_p81.py ...

# 3. 重生成 PS1
python recreate_p81.py

# 4. 语法检查
powershell -File verify_p81_tweak_syntax.ps1

# 5. 冒烟测试
powershell -File test_p81_tweak.ps1

# 6. 提交
git add G7_ADJUDICATION_LEDGER/recreate_p81.py G7_ADJUDICATION_LEDGER/dshd_p81_watch.ps1
git commit -m "[DSHD-P81-TWEAK-3] 新增 XX 功能"
```

### 4.2 回滚流程

```powershell
# 1. 查看可用快照
python p81_safe_edit.py history recreate_p81.py

# 2. 选择 snapshot_id 并回滚
python p81_safe_edit.py restore recreate_p81.py \
  --from recreate_p81.20261019_132403.DSHD-P81 \
  --agent DSHD-P81 \
  --reason "revert to v1.2.0-TWEAK"

# 3. 验证
python p81_safe_edit.py check recreate_p81.py
```

---

## 五、红线与约束

### 5.1 钩子本身的红线

- ✅ 只读：snapshot/check/list/history 只读
- ✅ 写入仅限 `_p81_snapshots/` 和 `p81_version_history.json`
- ✅ 拒绝备份 P81_PROTECTED 清单外的文件
- ✅ 无网络调用（wind_api_calls = 0）
- ✅ 不修改业务 CSV、因子数据、回测结果、MANIFEST、skill 制品
- ✅ 不 kill 任何非 P81 进程

### 5.2 版本管理红线

- ❌ 不允许直接编辑 P81 工具链文件而不先 snapshot
- ❌ 不允许删除 `_p81_snapshots/` 中的 `.bak` 文件
- ❌ 不允许清空 `p81_version_history.json`
- ❌ 不允许将 `_p81_snapshots/` 加入 git 跟踪

---

## 六、相关文件

| 文件 | 用途 |
|---|---|
| `p81_safe_edit.py` | 备份钩子主程序（Python CLI） |
| `p81_safe_edit.ps1` | 备份钩子 PS1 包装器 |
| `p81_version_history.json` | SHA 版本台账（真源） |
| `_p81_snapshots/` | 快照备份目录（gitignored） |
| `artifacts/dshd_cluster_brief.md` | watcher 动态简报（每 5 分钟重生成） |
| `tracking_monitor_audit.jsonl` | 全集群审计账本 |

---

## 七、变更记录

| 日期 | 版本 | 说明 |
|---|---|---|
| 2026-10-19 | v1.0.0 | 初始版本：备份钩子 + 版本台账 + 回滚指引 |
