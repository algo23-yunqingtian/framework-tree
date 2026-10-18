# Wiki · Phase03 准入看板

> 本页面为 V88 Phase03 准入门禁 Wiki 源码（GitHub Wiki Markdown 格式），可直接复制到仓库 Wiki 页面。

---

## 一、Phase03 三方 Agent 分工

| Agent | 角色 | 交付 |
|---|---|---|
| **HERMEShf** | 仲裁器 | 5 项预检 + 双钥匙管理 + 门禁看板 |
| **DSHB** | 因子配置 | 9 因子 3×3 矩阵 + 口径快照 |
| **DSHE** | 引擎网关 | 快照导入 + 封印/网关规则 |

## 二、5 项预检判定项

| # | 预检 | 校验方式 | 证据 | 当前状态 |
|:-:|------|----------|------|:---:|
| #1 | P0-13-CLOSED | 静态 True | — | ✅ |
| #2 | BASELINE-SWITCH-FREE | 文件内容校验 | `phase03_summary_asset_re_seal.md` | ✅ |
| #3 | PHASE03-BLOCKERS-ZERO | 文件内容校验 | `global_gate_dashboard.md` | ✅ |
| #4 | NO-PREMATUROUS-MERGE | 文件不存在校验 | — | ✅ |
| #5 | DSHE-AUTO-COMMIT-OFF | 源码正则校验 | `opt_hooks/blocker_monitor_hook_snippet.py` | ✅ |

**通过标准**: 5/5 全部 PASS 且 Key A 存在 → 满足准入触发条件

**阻断规则**:
- 硬阻断: 任一预检 FAIL / Key A 存在但 Key B 已误签发 → 拒绝准入
- 软阻断: 任一预检 SKIP 且 Key A 不存在 → 维持待命，不签发 Key B

## 三、8 项前置条件 (A1-A8)

| # | 前置 | 状态 |
|:-:|------|:---:|
| A1 | 分支锁定 feature/v88-g1 | ✅ |
| A2 | 无覆盖已封存产物 | ✅ |
| A3 | 未修改 V87 基线 | ✅ |
| A4 | 未编辑 release tag | ✅ |
| A5 | 无 ZHIJI API 调用 | ✅ |
| A6 | 风险台账清零 | ✅ 3/3 |
| A7 | 仲裁器回归无退化 | ✅ 三期一致 |
| A8 | 三方口径零冲突 | ✅ |

## 四、双钥匙状态

| 钥匙 | 文件名 | 状态 |
|------|--------|:---:|
| Key A | `WIND_DATA_LINK_ONLINE.flag` | ❌ ABSENT |
| Key B | `HERMES_TRIGGER_AUTHORIZED.flag` | ❌ ABSENT（不自动签发） |

**签发流程**: Key A 出现 → 5 项预检 → 全 PASS → HERMEShf 手动决策 → Key B 签发 → Phase04 点火

## 五、8 场景回归结果

```
S1 无KeyA无KeyB(正常待命)      → SKIP (合法)
S2 KeyA存在KeyB不存在(单钥匙)   → PASS 5/5
S3 KeyA不存在KeyB存在(异常态)   → SKIP (合法)
S4 KeyA+B都存在(授权态)          → PASS 5/5
S5 重复S1稳定性                  → SKIP (合法)
S6 重复S2稳定性                  → PASS 5/5
S7 KeyA空文件(边界)              → PASS 5/5
S8 KeyA10KB大文件(边界)          → PASS 5/5
```

**总计**: 5 ALL PASS + 3 SKIP = 8/8 行为符合预期，0 假阳性/假阴性

## 六、风险台账 (3/3 闭环)

| 编号 | 等级 | 描述 | 状态 |
|------|:---:|------|:---:|
| R-V88-P6-001 | LOW | 3项预检静态True→真实文件校验 | ✅ RESOLVED (P7) |
| R-V88-P7-001 | LOW | #3文档校验局限→JSON迁移方案 | ✅ 方案完成 (P8) |
| R-V88-P8-001 | LOW | 快照格式不匹配→JSON+双源校验 | ✅ RESOLVED (P9) |

## 七、Phase04 前置约束

- PHASE04 = FROZEN
- BASELINE_MERGE = WAIT_AFTER_PHASE04_GO
- Key B 未自动签发，需 HERMEShf 手动决策
- LEGACY-BUG-001 延期至 Phase04（不阻断 Phase03 准入）

## 八、图表入口

| 图表 | 页面链接 |
|------|---------|
| 3×3 因子矩阵 | [assets/02_factor_heatmap.png](assets/02_factor_heatmap.png) |
| 8 场景回归 | [assets/03_scenario_bars.png](assets/03_scenario_bars.png) |
| 风险闭环 | [assets/04_risk_progress.png](assets/04_risk_progress.png) |
| 三方口径 | [assets/05_caliber_matrix.png](assets/05_caliber_matrix.png) |

---

*V88 Phase03 P12 | HERMEShf | Wiki 源码 v9 | 状态: ARBITER_ON_STANDBY_AWAIT_KEY_A*