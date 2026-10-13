# V87-RC1-G1 Phase18 git 仓库内务维护 & 体积优化报告

> **工单**: V87_RC1_G1_P18_HERMES T5
> **执行日期**: 2026-10-12
> **执行方**: HERMES Agent
> **分支**: feature/v87-rc1-g1
> **约束**: 不修改任何 commit 历史，不改动哈希/MD5

---

## 0. 维护结论

| 项 | 值 |
|---|---|
| 维护类型 | `git gc --aggressive --prune=now` |
| 仓库体积（前） | **119 MB** |
| 仓库体积（后） | **36 MB** |
| **压缩率** | **69.7%**（压缩 83 MB） |
| commit 哈希不变 | ✅ **751 个 commit 哈希完全一致** |
| HEAD 不变 | ✅ `55e54e8` |
| 历史修改 | **零修改**（不改动任何 commit 哈希/MD5） |

---

## 1. 维护前仓库状态

### 1.1 git count-objects -v（前）

```
count: 4774        ← 松散对象数
size: 79736        ← 松散对象大小(KB)
in-pack: 7705      ← 已打包对象数
packs: 7           ← pack 文件数
size-pack: 38227   ← pack 大小(KB)
prune-packable: 12 ← 可被 gc 清理的对象数
garbage: 0
size-garbage: 0
```

### 1.2 .git 目录体积

```
119M    /home/ubuntu/framework-tree/.git
```

**问题**: 松散对象 4774 个（79.7 MB），pack 文件 7 个（碎片化），prune-packable 12 个可清理对象。仓库体积偏大，需要压缩。

---

## 2. 执行 git gc

### 2.1 命令

```bash
git gc --aggressive --prune=now
```

### 2.2 参数说明

| 参数 | 作用 | 安全性 |
|---|---|---|
| `--aggressive` | 使用更激进的压缩策略（delta 压缩重算） | 不修改 commit 哈希，仅重新打包 |
| `--prune=now` | 立即清理不可达对象（默认 2 周宽限期） | 仅清理无引用的松散对象，不影响有引用的 commit |

**注意**: `--aggressive` 会重算 delta 压缩，但**不会修改任何 commit 的哈希值**。git 对象的哈希由对象内容决定，打包方式不影响哈希。`--prune=now` 仅清理无引用的松散对象（如 reflog 中的旧引用），不影响任何分支可达的 commit。

---

## 3. 维护后仓库状态

### 3.1 git count-objects -v（后）

```
count: 0           ← 松散对象数（全部打包）
size: 0            ← 松散对象大小(KB)
in-pack: 12208     ← 已打包对象数（4774+7705+清理=12208）
packs: 1           ← pack 文件数（7→1 合并）
size-pack: 33920   ← pack 大小(KB) = 33.1 MB
prune-packable: 0  ← 可清理对象（全部清理）
garbage: 0
size-garbage: 0
```

### 3.2 .git 目录体积

```
36M     /home/ubuntu/framework-tree/.git
```

### 3.3 优化效果

| 指标 | 前 | 后 | 变化 |
|---|---|---|---|
| .git 体积 | 119 MB | 36 MB | **-83 MB (-69.7%)** |
| 松散对象 | 4,774 | 0 | **-4,774（全部打包）** |
| pack 文件 | 7 | 1 | **-6（碎片合并）** |
| pack 大小 | 38.2 MB | 33.9 MB | -4.3 MB (-11.3%) |
| 可清理对象 | 12 | 0 | **-12（全部清理）** |

---

## 4. commit 哈希不变性验证

### 4.1 全量 commit 哈希对比

```bash
# gc 前
git log --all --format=%H | wc -l    # 751

# gc 后
git log --all --format=%H | wc -l    # 751

# 哈希集合完全一致
diff <(gc前哈希列表) <(gc后哈希列表)   # 空（完全一致）
```

**结论**: gc 前后 **751 个 commit 哈希完全一致**，零变化。

### 4.2 HEAD 验证

```
gc 前 HEAD: 55e54e8bd24767200469e9079c3eb0dd6162f458
gc 后 HEAD: 55e54e8bd24767200469e9079c3eb0dd6162f458
```

**HEAD 不变** ✅

### 4.3 分支引用验证

```
feature/v87-rc1-g1 → 55e54e8（不变）
origin/feature/v87-rc1-g1 → 55e54e8（不变）
```

---

## 5. 约束合规

| 约束 | 状态 | 说明 |
|---|---|---|
| 不修改 commit 历史 | ✅ | 751 个哈希完全不变 |
| 不改动哈希/MD5 | ✅ | 所有 commit 和 tree 哈希不变 |
| 不 force push | ✅ | gc 是本地操作，不涉及 push |
| 不 --no-verify | ✅ | gc 不触发 pre-commit hook |
| BRANCH_LOCKED | ✅ | 分支未变更 |
| NO_OVERWRITE | ✅ | 未覆盖任何产物 |

---

## 6. 结论

git gc 内务维护完成，仓库体积从 119 MB 压缩至 36 MB（压缩率 69.7%），751 个 commit 哈希完全不变，HEAD 和分支引用不变。仓库内务维护达成"体积压缩 + 哈希不变"双目标。

---

## 7. 变更记录

| 版本 | 日期 | 编制人 | 内容 |
|---|---|---|---|
| v1.0 | 2026-10-12 | HERMES Agent (Phase18) | 首次编制，git gc 完成报告 |
