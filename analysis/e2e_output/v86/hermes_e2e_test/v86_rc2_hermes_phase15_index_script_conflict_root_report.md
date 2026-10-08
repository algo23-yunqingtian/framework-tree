# V86-RC2 HERMES Phase15 — phase5_index_deploy.py 版本冲突根因报告

> **工单**: T1 定位 phase5_index_deploy.py 文件版本冲突，修复 argparse 参数
> **分支**: `feature/v85-chart-template` @ `786bbab`
> **编制方**: HERMES (L3 审计方)
> **日期**: 2026-10-08
> **状态**: ✅ 实测已修复（Phase8 commit `1cd3815` 闭环）

---

## 1. 工单描述的问题

工单 HERMES_V86_RC2_PHASE15 指出：

> "定位 phase5_index_deploy.py 文件版本冲突，执行 git 校验：核对 commit 1ed048a 文件大小、行数，确认 `--indexes` 参数存在性；基于当前 15700 字节版本重新生成 patch，修复 argparse 参数，验证脚本执行无报错、参数语义生效"

工单引用的关键证据：
- commit `1ed048a` 文件大小 15700 字节（工单声称）
- `--indexes` 参数可能缺失或语义静默失效

## 2. 实测核验（HEAD = `786bbab`，rebase 后）

### 2.1 文件基本状态

| 维度 | 工单声称 | 实测值 |
|------|---------|--------|
| commit | `1ed048a` | `1cd3815`（Phase8 HERMES 最终 commit，含 phase5 脚本） |
| 文件大小 | 15700 字节 | **19446 字节** |
| 文件行数 | 387 行（15700 字节版本） | **445 行** |
| `--indexes` 参数 | 可能缺失 | **存在**（第 400 行 `ap.add_argument("--indexes", ...)`） |
| `--enable-extra-index` | — | **存在**（第 397 行） |
| 冲突标记 | — | **0 处**（`<<<<<<<` 和 `>>>>>>>` 各 0 命中） |

### 2.2 argparse 参数语义实测（5 路径全覆盖）

| # | 命令 | 退出码 | 输出范围标签 | 判定 |
|---|------|--------|-------------|------|
| 1 | `--check`（默认） | 0 | `3核心 (idx_fault, idx_sev_ts, idx_trace)` | ✅ |
| 2 | `--check --indexes idx_trace,idx_fault,idx_sev_ts` | 0 | `3核心` + no-op 提示 | ✅ |
| 3 | `--check --indexes idx_trace,idx_decision` | 0 | `3核心+2扩展` + 等价提示 | ✅ |
| 4 | `--check --indexes idx_bogus` | **2** | `❌ 未知索引，中止` | ✅ |
| 5 | `--check --enable-extra-index` | 0 | `3核心+2扩展` | ✅ |

**退出码语义全部正确**：未知索引 exit 2（阻断），正常路径 exit 0。

### 2.3 根因分析：15700 字节版本的来源

Phase7 交接文档记录了"reset 后 patch 施加到已不存在的行号上"的踩坑事件（skill `session-handover-recovery` 陷阱清单 §1）：

> Phase7 commit `cb0fec5` 时 phase5_index_deploy.py 是 387 行/15700 字节（不含 Phase8 接口对齐代码）。
> Phase8 在 commit `1cd3815` 中追加了第 396-438 行（`--indexes` 参数 + 归一化逻辑），扩展到 445 行/19446 字节。
> 工单基于 Phase7 的旧基线（15700 字节）编写，但 Phase8 已修复。

**结论**：工单描述的"版本冲突、参数缺失、语义失效"在 Phase8 commit `1cd3815` 中已全部修复。当前 HEAD `786bbab` 实测 5 路径全 PASS，无残留缺陷。

## 3. skill 教训验证

本案例完美验证了 skill `session-handover-recovery` 的核心纪律：

> **"交接文档/工单的 P0 描述必须实测。文档说'待做'，实际可能已做——git log 是唯一真源。"**

工单将 Phase7 旧基线状态（15700 字节、参数缺失）误报为当前状态，但 Phase8 commit `1cd3815` 已修复。实测 5 路径全 PASS 后确认无需重做。

## 4. 状态标记

```
HERMES_PHASE15_INDEX_SCRIPT_CONFLICT_FIX_DONE=TRUE_VERIFIED_ALREADY_FIXED_IN_PHASE8
```

**说明**：Phase8 commit `1cd3815` 已修复，Phase15 实测确认无残留，标记 TRUE。

---

*本报告由 HERMES 生成于 Phase15 T1 核验。实测优先，不重做已修工作。*
