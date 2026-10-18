# V88 Phase03 P13 索引缺口审计与处置方案 (asset_index_solution_P13.md)

> **TASK_ID**: V88_PHASE03_P13_HERMESHF_ASSET_INDEX_GAP_AUDIT
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1 | **生成**: 2026-10-20
> **源 commit**: 8765c21
> ⚠️ **本文件仅输出文字方案, 未落地执行任何变更。asset_index.lst 未被修改。**

## 一、问题陈述

| 项 | 值 |
|----|-----|
| 缺口文件 | `github_pages/wiki_admission_gate.md` |
| MD5 | `3286e1469f7ce6b23bedfef061fbc63f` |
| SHA256 | `591ebeeb7692a07737462e12f58ed8440a17f444d291e470494f5d3ff5416b24` |
| 字节 | 3591 |
| 磁盘存在 | 是 (github_pages/ 顶层) |
| zip 内存在 | 是 (visual_asset_shturl.H.zip, 同名同哈希) |
| asset_index.lst 索引 | **否** |
| 只读权限 | 0444 |
| CRLF | 0 |

### 缺口性质判定

该文件**内容三方一致** (磁盘 = zip 内部 = 同哈希), 哈希无漂移, 换行无漂移。
缺口纯粹是 **asset_index.lst 索引未收录**, 非内容异常或数据损坏。

### v3 封签锁定关系

| 项 | 值 |
|----|-----|
| v3 是否锁定 asset_index.lst | **是** (v3 表 10 条中含 asset_index.lst) |
| v3 是否列 github_pages/* 资产 | 否 (v3 只锁交付文件, 不锁挂载资产) |
| 含义 | 修改 asset_index.lst 会破坏 v3 封签链, 违反 NO_MODIFY_LOCKED_SEAL |

---

## 二、方案 A: 移出挂载目录 (最小变更)

### A.1 操作定义

将 `github_pages/wiki_admission_gate.md` 从挂载目录移出, 维持 asset_index.lst 现有 22 条不变。

```
操作: mv analysis/e2e_output/v88/phase03/p1/hermes/github_pages/wiki_admission_gate.md
         analysis/e2e_output/v88/phase03/p1/hermes/github_pages_archive/

结果: github_pages/ 13 文件 → 12 文件
      asset_index.lst: 22 条 (不变)
      索引覆盖率: 22/22 = 100%
```

### A.2 数据可追溯性 (关键: 无数据丢失)

**该文件在交付归档中已有同哈希副本**:

| 副本位置 | MD5 | 字节 | 状态 |
|----------|-----|-----:|:---:|
| `hermes_web_dashboard_archive/github_pages/wiki_admission_gate.md` | `3286e1469f7ce6b23bedfef061fbc63f` | 3591 | ✅ 已归档 |
| `visual_asset_shturl.H.zip` (zip 根条目) | `3286e1469f7ce6b23bedfef061fbc63f` | 3591 | ✅ 已打包 |

**三方同哈希**, 移出挂载目录后内容不会丢失, DSHE 仍可从归档副本或 zip 包读取。

### A.3 影响面

| 项 | 影响 |
|----|------|
| asset_index.lst | 无变更 (22 条) |
| asset_seal_v3.txt | **无影响** (未修改其锁定对象) |
| asset_seal_v2/v4/v5.txt | 无影响 |
| 22 项资产哈希 | 不变 (22/22) |
| 只读权限 | 不变 (其余 22 项保持 0444) |
| 新增封签 | **不需要** |
| 新增交付物 | 仅本报告 |
| git 变更 | 1 个文件移动 (rename) |

### A.4 前置风险

| 风险 | 评估 |
|------|------|
| DSHE 期望 23 项资产 | 中 —— 需确认 wiki_admission_gate.md 是否属可视化资产范畴 |
| github_pages/ 对外语义 | 中 —— 该目录同时承载 index.html + assets/, 移出后 index.html 可能引用该文件 |
| 可回退性 | 高 —— git rename 可逆 |

### A.5 推荐判定

**推荐 (若 wiki_admission_gate.md 属文档附件而非可视化资产)**:
- 变更最小, 不触碰任何封签
- 数据三方可追溯, 无丢失
- 索引覆盖率恢复 100%

---

## 三、方案 B: 保留 23 项 + 新版封签 v6

### B.1 操作定义

保留全部 23 个文件, 扩容 asset_index.lst 至 23 条, 新建 asset_seal_v6.txt 封签扩容后的索引。

```
操作: 1. 在 asset_index.lst 末尾追加第 23 条
      2. 生成 asset_seal_v6.txt (封签新的 asset_index.lst + 23 项资产)
      3. v2/v3/v4/v5 四版封签原样保留

结果: asset_index.lst: 22 条 → 23 条
      索引覆盖率: 23/23 = 100%
```

### B.2 扩容条目数据 (已备)

| # | 路径 | MD5 | 字节 |
|:-:|------|-----|-----:|
| 23 | `github_pages/wiki_admission_gate.md` | `3286e1469f7ce6b23bedfef061fbc63f` | 3591 |

### B.3 ⚠️ 关键矛盾: v3 封签必然断裂

**这是方案 B 的核心问题, 必须明确记录**:

| 项 | 影响 |
|----|------|
| asset_seal_v3.txt 表 | **将破坏** (asset_index.lst 哈希改变, v3 表 10 条 → 9 条一致) |
| asset_seal_v2.txt | 无影响 (不锁 asset_index.lst) |
| asset_seal_v4.txt | 无影响 |
| asset_seal_v5.txt | 无影响 (v5 不锁 asset_index.lst 的哈希本身, 但 v5 表会因 asset_index.lst 变化而变化) |

**实测依据** (P12 已验证):
P12 首次尝试修改 asset_index.lst 列格式, 导致 v3 表从 10/10 降为 **9/10**, 已立即回退。
方案 B 扩容索引属同类变更, **必然破坏 v3 封签链**。

### B.4 冲突约束

| 约束 | 方案 B 合规性 |
|------|:---:|
| NO_MODIFY_LOCKED_SEAL (本工单) | ❌ **违反** —— v3 是已锁定封签, 扩容索引会破坏它 |
| NO_OVERWRITE | ✅ 保留 v2/v3/v4/v5, 仅新增 v6 |
| 四版封签并存 | ⚠️ 五版并存, 但 v3 表校验将失败 |

**方案 B 在字面上违反本工单的 NO_MODIFY_LOCKED_SEAL 约束。**
若必须执行方案 B, 需重新立项授权 (明确允许 v3 断裂, 或以 v6 为权威源覆盖 v3 的失效部分)。

### B.5 影响面

| 项 | 影响 |
|----|------|
| asset_index.lst | 22 → 23 条 |
| asset_seal_v3.txt | ⚠️ 表 10/10 → 9/10 (断裂) |
| asset_seal_v6.txt | 新增 (需封签 asset_index.lst + 23 项资产 + P13 交付报告) |
| 单向校验链 | 需重建于 v6 之上 |
| git 变更 | asset_index.lst 修改 + asset_seal_v6.txt 新增 |

### B.6 推荐判定

**不推荐 (在 NO_MODIFY_LOCKED_SEAL 约束下)**:
- 必然破坏 v3 封签, 与本工单约束冲突
- 需要重新授权才能落地
- 变更面大, 追溯成本高

**仅在以下条件同时满足时可行**:
1. DSHE 明确该文件属可视化资产 (非文档附件)
2. 重新立项允许 v3 断裂, 或以 v6 为新的权威封签源
3. 明确接受 v3 表 9/10 的状态

---

## 四、方案对比总表

| 维度 | 方案 A (移出) | 方案 B (扩容+v6) |
|------|:---:|:---:|
| 索引覆盖率 | 22/22 = 100% | 23/23 = 100% |
| asset_index.lst 变更 | 无 | 22→23 条 |
| v3 封签影响 | ✅ 无影响 | ❌ 表 10/10→9/10 断裂 |
| 新增封签 | 无 | v6 (新增) |
| 数据丢失风险 | 无 (三方副本) | 无 |
| NO_MODIFY_LOCKED_SEAL 合规 | ✅ | ❌ |
| NO_OVERWRITE 合规 | ✅ | ✅ |
| 变更面 | 最小 (1 文件移动) | 大 (索引+新封签+链重建) |
| 需重新授权 | 否 | 是 |
| 推荐度 | ⭐⭐⭐⭐⭐ | ⭐⭐ |

## 五、决策建议

### 5.1 建议决策树

```
Q1: wiki_admission_gate.md 是否属于"22 项可视化资产"范畴?
├─ 否 (文档附件/门禁说明)  → 选方案 A (移出挂载目录)
└─ 是 (交付资产)          → 转 Q2

Q2: 是否接受 v3 封签断裂 (10/10 → 9/10)?
├─ 否 (保持封签链完整)    → 选方案 A (移出, 仍可从归档/zip 访问)
└─ 是 (以 v6 为权威源)    → 选方案 B (需重新立项授权)
```

### 5.2 文件语义判断依据

从文件名与内容推断:
- `wiki_admission_gate.md` 位于 `github_pages/` 顶层 (与 index.html 同级)
- 同目录其他顶层文件: `README.md` (已在索引), `index.html` (已在索引)
- `wiki_admission_gate.md` 语义为"准入门禁说明文档", 与 5 组可视化图表组件 (01-05) 不同类

**倾向判断**: 该文件更可能是文档附件而非可视化资产组件。
但这只是基于命名与位置的技术推断, **最终归属判定权在 DSHE**。

### 5.3 本轮处置

**本轮未落地任何方案。** asset_index.lst 保持 22 条原样, v3 封签链完整 (表 10/10)。
等待 DSHE 决策后由后续工单执行。

---

## 六、审计结论

- 索引缺口 1 项, 性质为**索引未收录**, 非内容异常
- 缺口文件内容三方一致, 无哈希漂移, 无换行漂移
- 缺口文件在交付归档与 zip 包中均有同哈希副本, 无数据丢失风险
- 方案 A 最小变更, 不触碰封签, 推荐
- 方案 B 必然破坏 v3 封签, 与本工单 NO_MODIFY_LOCKED_SEAL 约束冲突, 需重新授权
- **本轮未修改 asset_index.lst, 未修改任何封签, 未移动任何文件**

---

*V88 Phase03 P13 T1 | HERMEShf | 2026-10-20*