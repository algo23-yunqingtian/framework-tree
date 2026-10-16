# TRIGGER_RULES.md — 双钥匙触发器安全规则

> **TASK_ID**: V88_PHASE03_P5_HERMESHF_GLOBAL_COORDINATE_TRIGGER_GUARD / T4
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1
> **版本**: v1.0.0
> **生效时间**: 2026-10-17 UTC+8

---

## 1. 规则概述

本文件定义 HERMEShf 官方双钥匙触发器体系的安全规则。DSHB、DSHE 及所有下游 agent 必须遵守本规则，否则触发器逻辑将被判定为不安全并拒绝启动。

### 1.1 核心原则

> 🚨 **DSHB/DSHE 只做检测，只有收到 HERMES 的签名放行标记才允许全速启动因子任务。**

---

## 2. 双钥匙定义

### 钥匙 A: WIND_DATA_LINK_ONLINE.flag

| 属性 | 值 |
|------|---|
| 文件名 | `WIND_DATA_LINK_ONLINE.flag` |
| 文件路径 | 仓库根目录 (`framework-tree/WIND_DATA_LINK_ONLINE.flag`) |
| 放置方 | 外部系统或 DSHB（代表 Wind 数据源已就绪） |
| 验证方 | HERMEShf（通过 `official_trigger_arbiter.py`） |
| 当前状态 | ❌ 不存在 |

### 钥匙 B: HERMES_TRIGGER_AUTHORIZED.flag

| 属性 | 值 |
|------|---|
| 文件名 | `HERMES_TRIGGER_AUTHORIZED.flag` |
| 文件路径 | 仓库根目录 (`framework-tree/HERMES_TRIGGER_AUTHORIZED.flag`) |
| 放置方 | **仅 HERMEShf**（经过 5 项安全预检后手动放置） |
| 验证方 | DSHB、DSHE（通过 `official_trigger_arbiter.py`） |
| 当前状态 | ❌ 不存在 |

---

## 3. 联合判定规则

```
IF Key A EXISTS AND Key B EXISTS:
    → AUTHORIZED: 因子任务可启动
ELIF Key A EXISTS AND Key B ABSENT:
    → REFUSED: 仅有事实钥匙，缺少仲裁签名 → 仅打日志，拒绝启动
ELIF Key A ABSENT AND Key B EXISTS:
    → REFUSED: 仅有仲裁签名，缺少事实钥匙 → 异常状态，拒绝启动
ELSE (both absent):
    → REFUSED: 双钥匙均缺失 → 拒绝启动
```

**关键约束**:
1. **A 和 B 必须同时存在** — 缺一不可
2. **B 不可预先生成** — HERMES 只在 A 真实出现 + 5 项预检通过后生成 B
3. **A 不可伪造解锁** — 仅 A 存在（无 B）→ 仍拒绝启动
4. **DSHB/DSHE 不可自行生成 B** — 仅 HERMEShf 有签名权

---

## 4. HERMES 5 项安全预检

HERMES 在收到 Key A 后，运行以下 5 项预检，全部通过后才生成 Key B:

| # | 预检项 | 检查内容 | 通过条件 |
|:-:|--------|----------|----------|
| 1 | P0-13-CLOSED | P0-13 噪声基线 168h 是否完成 | `noise_168h_final_snapshot.json` 存在 |
| 2 | BASELINE-SWITCH-FREE | 是否有静默切换基线 | `phase03_summary_asset_re_seal.md` 验证通过 |
| 3 | PHASE03-BLOCKERS-ZERO | Phase03 阻断项是否为 0 | P0-12=WARN + P0-13=PASS = 0 阻断 |
| 4 | NO-PREMATUROUS-MERGE | 基线是否已被提前合并 | `v88-long-stable-baseline.json` 不存在 |
| 5 | DSHE-AUTO-COMMIT-OFF | DSHE 是否仍处于安全模式 | `AUTO_COMMIT_MODE=false` 确认 |

**5 项全部通过** → HERMES 手动创建 `HERMES_TRIGGER_AUTHORIZED.flag`

**任一失败** → HERMES 不生成 Key B，拒绝放行

---

## 5. DSHB/DSHE 遵从义务

### 5.1 DSHB 义务

1. DSHB 的 `wind_online_watcher.py` 可以放置 `WIND_DATA_LINK_ONLINE.flag`（钥匙 A）
2. DSHB 启动因子任务前，**必须**检查两把钥匙：
   ```python
   if not (os.path.exists(WIND_FLAG) and os.path.exists(HERMES_FLAG)):
       log("REFUSED: dual-key not satisfied")
       sys.exit(1)
   ```
3. DSHB **不得**自行创建 `HERMES_TRIGGER_AUTHORIZED.flag`
4. DSHB **不得**绕过双钥匙检查直接启动因子任务

### 5.2 DSHE 义务

1. DSHE 的因子运行时（`factor_runtime_rules_v1.yaml`）必须遵从双钥匙逻辑
2. DSHE 启动因子计算前，**必须**检查两把钥匙
3. DSHE **不得**自行创建 `HERMES_TRIGGER_AUTHORIZED.flag`
4. DSHE **不得**绕过双钥匙检查直接启动因子任务

---

## 6. 安全不变量

| # | 不变量 | 违规后果 |
|:-:|--------|----------|
| 1 | B 不可预先生成 | 视为安全漏洞 |
| 2 | A 不可单独解锁 | 拒绝启动 |
| 3 | HERMES 不自拉数据 | 违反 NO_ZHIJI_API_CALL |
| 4 | DSHB/DSHE 不自行生成 B | 视为伪造签名 |
| 5 | 任何钥匙缺失 → 拒绝 | 安全红线 |

---

## 7. 违规处置

| 违规类型 | 检测方式 | 处置 |
|----------|----------|------|
| 预生成 B | `official_trigger_arbiter.py` 检查 B 的时间戳早于 A | 🔴 安全告警，暂停所有因子任务 |
| 绕过双钥匙 | DSHB/DSHE 未检查直接启动 | 🔴 立即停止，HERMES 审计 |
| 伪造 A | A 的 MD5 不匹配已知值 | 🟡 人工确认数据源状态 |
| 伪造 B | B 的 MD5 不匹配 HERMES 签名 | 🔴 安全告警 |

---

## 8. 版本记录

| 版本 | 日期 | 变更 |
|:----:|------|------|
| v1.0.0 | 2026-10-17 | 初始版本，双钥匙规则定义 |

---

*Generated: 2026-10-17 UTC+8 | HERMEShf | DUAL-KEY SECURITY RULES v1.0.0*
