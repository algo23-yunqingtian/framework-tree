# Phase03 准入门禁检查清单

> **TASK_ID**: V88_PHASE03_P11_HERMESHF_P10_PHASE03_ADMISSION_GATE_PREP / T1
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **固化时刻**: 2026-10-17T15:50 +0800
> **用途**: Phase03 → Phase04 准入判定的权威清单。Key A 出现后，HERMEShf 按此清单逐项校验，全 PASS 才考虑签发 Key B。

---

## 0. 准入门禁触发总流程

```
[外部] Key A (WIND_DATA_LINK_ONLINE.flag) 出现
   ↓
[HERMEShf] 运行 official_trigger_arbiter.py
   ↓
5 项预检 (本清单 §1)
   ↓
 全 PASS → 人工决策是否签发 Key B
   ↓ (是)
Key B (HERMES_TRIGGER_AUTHORIZED.flag) 签发
   ↓
[DSHB/DSHE] 校验双钥匙 → Phase04 点火
```

**铁律**：HERMEShf **永不自动签发** Key B。Key B 是人工决策产物，5 项预检全 PASS 仅是必要条件，不是充分条件。

---

## 1. 5 项预检（仲裁器内置）

| # | 预检 ID | 校验内容 | 通过标准 | 阻断判定 | 证据文件 |
|:-:|---------|----------|----------|:--------:|----------|
| #1 | P0-13-CLOSED | 168h 噪声观测快照存在 | `noise_168h_final_snapshot.json` 存在 | 缺失=阻断 | `phase03/p2/dshb/p013_watch_prep/final_archive/` |
| #2 | BASELINE-SWITCH-FREE | 基线无静默切换 | seal 文档含"无静默切换"+"✅ NO" | 缺失关键字=阻断 | `phase03_summary/phase03_summary_asset_re_seal.md` |
| #3 | PHASE03-BLOCKERS-ZERO | Phase03 阻断清零 | dashboard 含"全部阻断清零"+"🔴 FAIL"+"**0**" | 阻断数>0=阻断 | `phase03_summary/global_gate_dashboard.md` |
| #4 | NO-PREMATUROUS-MERGE | DSHB 基线合并未提前执行 | `v88-long-stable-baseline.json` 不存在 | 文件存在=阻断 | 仓库根 |
| #5 | DSHE-AUTO-COMMIT-OFF | DSHE 自动提交已关闭 | hook 源码匹配 `^AUTO_COMMIT_MODE\s*=\s*False\b` | 模式不匹配=阻断 | `opt_hooks/blocker_monitor_hook_snippet.py` |

**判定规则**：5/5 PASS → 准入预检层通过；任一 FAIL → 阻断，**禁止签发 Key B**。

---

## 2. 准入前置条件（仲裁器外，HERMEShf 人工核验）

| # | 维度 | 通过标准 | 当前状态 | 阻断判定 |
|:-:|------|----------|:--------:|:--------:|
| A1 | 风险台账清零 | R-V88-P6/P7/P8-001 全 RESOLVED | ✅ 3/3 闭环 | 否 |
| A2 | 三方 Agent 就绪 | HERMEShf+DSHB+DSHE 状态 = *_AWAIT_DUAL_KEYS | ✅ 三方就绪 | 否 |
| A3 | 口径对齐 | MD 快照 + JSON 快照双源一致 + DSHB 24/24 + DSHE 9 slots | ✅ 0 冲突 | 否 |
| A4 | 资产封签 | cpu_compare + active_baseline + 引擎封印 v5 全 MATCH | ✅ 全匹配 | 否 |
| A5 | 网关规则 | FR-001~006 ACTIVE + FR-007~009 SEAL | ✅ | 否 |
| A6 | Phase03 门禁节点 | P0-12 WARN(豁免) + P0-13 CLOSED + P0-18/19 DONE | ✅ 0 阻断 | 否 |
| A7 | 仲裁器回归 | P8/P10 v2/P11 v3 三期一致，0 退化 | ✅ | 否 |
| A8 | 约束豁免 | C-1/C-2 ✅ + C-3/C-4/C-5 🟡待Phase04，0 阻断 | ✅ | 否 |

---

## 3. 准入判定逻辑（固化）

```
PHASE04_ADMISSION_DECISION =
    IF Key_A.present
    AND arbiter.run_5_point_safety_precheck().all_pass
    AND A1 AND A2 AND A3 AND A4 AND A5 AND A6 AND A7 AND A8
    AND human_decision == SIGN_KEY_B
THEN
    create HERMES_TRIGGER_AUTHORIZED.flag  (Key B)
    → PHASE04_ADMISSION_GRANTED
ELSE
    → PHASE03_PRE_ADMISSION_READY (维持等待)
    → 不签发 Key B
    → PHASE04_IGNITION = FROZEN (维持)
```

---

## 4. 阻断判定规则

### 4.1 硬阻断（任意一项触发即冻结）

| 触发条件 | 处置 |
|----------|------|
| 5 项预检任一 FAIL | 不签发 Key B，记录到风险台账，整改后重跑回归 |
| Key A 出现但预检 SOME FAIL | 同上 |
| 风险台账新增 HIGH/CRITICAL 项 | 整改闭环后再准入 |
| 三方状态标记不一致 | 等待三方同步 *_AWAIT_DUAL_KEYS |
| 口径冲突 > 0 | 等待 DSHB/DSHE 重对齐 |
| 资产封签 MD5 不匹配 | 等待资产重封签 |

### 4.2 软阻断（不阻断准入，但记入待办）

| 触发条件 | 处置 |
|----------|------|
| C-3 psutil 未部署 | Phase04 内推进 |
| C-4 基线合并待执行 | Key B 签发后执行 |
| C-5 manifest 自引用 | Phase04 内修复 |
| LEGACY-BUG-001 | 延期至 Phase04 |

### 4.3 豁免（已授信，不阻断）

| 项 | 豁免理由 |
|----|----------|
| P0-12 CPU 满载 WARN | 历史基线对比，已授信豁免 |
| P0-13 噪声 6.64% | < 8% 阈值，CLOSED |

---

## 5. 双钥匙状态矩阵

| Key A | Key B | AUTHORIZED | 仲裁器动作 |
|:-----:|:-----:|:----------:|------------|
| ❌ | ❌ | NO | OBSERVING，SKIP 预检，LOG_ONLY |
| ✅ | ❌ | NO | 跑 5 项预检；全 PASS → 等待人工签 Key B |
| ❌ | ✅ | NO | 异常态（Key B 不应先于 Key A），SKIP 预检，告警 |
| ✅ | ✅ | YES | Phase04 点火条件满足 |

**当前矩阵**：Key A ❌ / Key B ❌ → OBSERVING。

---

## 6. 准入触发条件汇总（Key A 出现后）

HERMEShf 收到 Key A 出现信号后，依次执行：

1. 运行 `python3 opt_auth_guard/official_trigger_arbiter.py`
2. 读取 5 项预检结果
3. 人工核验 §2 八项前置条件 (A1–A8)
4. 5/5 预检 PASS + 8/8 前置 PASS → 进入"是否签发 Key B"人工决策
5. 决策 SIGN → `touch HERMES_TRIGGER_AUTHORIZED.flag` → Phase04 点火
6. 决策 HOLD → 维持 ARBITER_ON_STANDBY，记录决策理由

---

## 7. 当前清单状态快照（P11 巡检时刻）

| 检查项 | 状态 |
|--------|:----:|
| §1 5 项预检（Key A 缺席，未触发） | ⏳ 待 Key A |
| §2 A1–A8 前置条件 | ✅ 8/8 |
| §3 准入判定逻辑 | ✅ 已固化 |
| §4 阻断规则 | ✅ 已定义 |
| §5 双钥匙矩阵 | ❌/❌ OBSERVING |
| §6 触发流程 | ✅ 已定义 |

**STATUS**: PHASE03_ADMISSION_CHECKLIST_FINALIZED_AWAIT_KEY_A

*Generated: 2026-10-17T15:50 +0800 | HERMEShf | V88 Phase03 P11 T1*
