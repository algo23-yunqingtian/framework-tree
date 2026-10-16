# 双钥匙触发器机制说明文档

> **TASK_ID**: V88_PHASE03_P5_HERMESHF_GLOBAL_COORDINATE_TRIGGER_GUARD / T4
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1
> **生成时间**: 2026-10-17 UTC+8

---

## 1. 设计动机

Phase04 因子任务需要 Wind 数据源上线作为前置条件。但单纯依赖一个 flag 文件存在即启动因子任务存在安全风险：任何 agent 都可以在仓库中放置 `WIND_DATA_LINK_ONLINE.flag` 来解锁因子任务，无需经过安全审查。

**双钥匙机制解决此问题**：即使 flag 文件被放置（钥匙 A），因子任务仍不会启动，除非 HERMEShf 经过安全审查后签发授权标记（钥匙 B）。

---

## 2. 架构图

```
外部系统 / DSHB                    HERMEShf                     DSHB/DSHE
     │                               │                              │
     │  放置 Key A:                    │  运行 5 项预检:              │
     │  WIND_DATA_LINK_ONLINE.flag    │  1. P0-13-CLOSED            │
     │  ──────────────────────────►   │  2. BASELINE-SWITCH-FREE    │  检查双钥匙
     │                               │  3. PHASE03-BLOCKERS-ZERO   │  ─────────►
     │                               │  4. NO-PREMATUROUS-MERGE    │
     │                               │  5. DSHE-AUTO-COMMIT-OFF    │
     │                               │  ─────────────►              │
     │                               │  全部通过:                    │
     │                               │  创建 Key B:                 │
     │                               │  HERMES_TRIGGER_AUTHORIZED   │
     │                               │  ───────────────────────►    │
     │                               │                              │
     │  (若 Key B 未生成)             │                              │
     │  ──────────────────────────►   │                              │
     │                               │                              │
     │                               │  因子任务启动条件:            │
     │                               │  Key A + Key B 同时存在     │
     │                               │  缺一不可 → 拒绝启动        │
```

---

## 3. 钥匙 A 详细说明

### 3.1 是什么

`WIND_DATA_LINK_ONLINE.flag` 是一个标记文件，表示 Wind 数据源连接已上线、数据可用。

### 3.2 谁放置

- 外部 Wind 连接测试 agent（如 DSHC）
- 或 DSHB（当确认数据源可用时）

### 3.3 为什么单独存在不够

任何 agent 都可以在仓库中放置这个文件。如果 DSHB/DSHE 仅检查 A 就启动因子任务，那么：

1. 一个恶意或错误的 agent 可以放置 A 来解锁因子任务
2. 没有安全审查环节
3. 无法验证前置条件（P0-13 闭合、基线未提前合并等）是否满足

**因此需要钥匙 B 作为安全闸门。**

---

## 4. 钥匙 B 详细说明

### 4.1 是什么

`HERMES_TRIGGER_AUTHORIZED.flag` 是 HERMEShf 的授权签名标记，表示 HERMEShf 已经：
1. 确认 Key A 真实存在
2. 运行了 5 项安全预检
3. 全部预检通过
4. 明确授权因子任务可以启动

### 4.2 谁可以放置

**仅 HERMEShf**。任何其他 agent 放置 B 都视为伪造签名。

### 4.3 放置条件

```
Key A 存在 + 5 项预检全部通过 → HERMEShf 手动创建 B
Key A 不存在 → HERMEShf 不运行预检，不创建 B
5 项预检任一失败 → HERMEShf 不创建 B
```

### 4.4 B 永远不会被预先生成

HERMEShf 不会提前创建 B。B 只会在 Key A 真实出现后才被生成。这是为了防止：

1. 提前授权导致绕过安全检查
2. 在条件未满足时解锁因子任务
3. 混淆审计追踪

---

## 5. 5 项安全预检

| # | 预检项 | 检查内容 | 检查方式 |
|:-:|--------|----------|----------|
| 1 | P0-13-CLOSED | P0-13 噪声基线 168h 观测是否完成 | 检查 `noise_168h_final_snapshot.json` 存在 |
| 2 | BASELINE-SWITCH-FREE | 是否有静默切换基线 | 检查 `phase03_summary_asset_re_seal.md` 验证结果 |
| 3 | PHASE03-BLOCKERS-ZERO | Phase03 阻断项是否清零 | P0-12=WARN + P0-13=PASS → 0 阻断 |
| 4 | NO-PREMATUROUS-MERGE | 基线是否被提前合并 | 检查 `v88-long-stable-baseline.json` 不存在 |
| 5 | DSHE-AUTO-COMMIT-OFF | DSHE 安全模式是否开启 | 检查 `AUTO_COMMIT_MODE=false` |

---

## 6. 联合判定逻辑

| Key A | Key B | 判定 | 动作 |
|:-----:|:-----:|:----:|------|
| ❌ | ❌ | REFUSED | 双钥匙均缺失，拒绝启动 |
| ✅ | ❌ | REFUSED | 仅有事实钥匙，缺少仲裁签名 → 仅打日志 |
| ❌ | ✅ | REFUSED | 仅有仲裁签名，缺少事实钥匙 → 异常 |
| ✅ | ✅ | AUTHORIZED | 双钥匙齐全 → 因子任务可启动 |

---

## 7. DSHB/DSHE 遵从注释

已在 `dshb_warmup_sanity_review.md` 和 `dshe_gate_prep_sanity_review.md` 中添加注释提醒：

```python
# ⚠️ DUAL-KEY CHECK REQUIRED
# 在启动因子任务前，必须检查两把钥匙:
#   Key A: WIND_DATA_LINK_ONLINE.flag (外部事实钥匙)
#   Key B: HERMES_TRIGGER_AUTHORIZED.flag (HERMEShf 仲裁签名)
# 仅有 A、缺少 B → 只能打日志、拒绝启动
# 参见: opt_auth_guard/TRIGGER_RULES.md
```

---

## 8. 不激活声明

> ⚠️ 本机制当前处于 **OBSERVING** 状态：
> - Key A 不存在（Wind 数据源未上线）
> - Key B 不存在（HERMES 未签发授权）
> - 因子任务未启动
> - Phase04 未激活

HERMEShf 不会主动创建 Key A 或 Key B。Key A 由外部系统或 DSHB 放置，Key B 仅在 Key A 出现且预检通过后由 HERMEShf 手动创建。

---

*Generated: 2026-10-17 UTC+8 | HERMEShf | DUAL-KEY MECHANISM EXPLAINER*
