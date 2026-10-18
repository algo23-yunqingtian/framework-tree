# V88 Phase03 P12 资产哈希重算与新版封签校验 (reseal_verification_P12.md)

> **TASK_ID**: V88_PHASE03_P12_HERMESHF_TEXT_NORMALIZE_RESEAL_AND_DISPATCH_PICKUP_JOB
> **AGENT**: HERMEShf | **生成**: 2026-10-20
> **结果**: L0~L4 全链路通过

## 一、单向封签校验链 (L0~L4)

| 层 | 校验动作 | 结果 | 判定 |
|:-:|----------|------|:---:|
| L0 | p18_delivery_ready.flag.SEAL_V3_SHA256 → asset_seal_v3.txt | 一致 | OK |
| L0' | asset_seal_v2/v3/v4/v5 四版封签并存 | 均存在 | OK |
| L1 | asset_seal_v3.txt 表 10 条 → 交付文件 sha256 | 10/10 | OK |
| L2 | asset_seal_v4.txt 表 13 条 → 交付文件 sha256 | 13/13 | OK |
| L3 | asset_index.lst 22 项 → 磁盘 md5+sha256+size | 22/22 | OK |
| L4 | asset_seal_v5.txt 表 → 交付文件 sha256 | 16/16 | OK |

（完整哈希值见 MD5_MANIFEST.md P12 段与 asset_index.lst / asset_seal_v5.txt 本体。
本文件是 v5 封签对象之一，内嵌哈希会形成循环依赖，故仅记录校验结论。）

## 二、22 项资产哈希重算

| 项 | 值 |
|----|-----|
| 重算资产数 | 22 (web_asset/ 10 + github_pages/ 12) |
| asset_index.lst vs 磁盘 MD5 | 22/22 一致 |
| asset_index.lst 条目数 | 22 (保持不变) |
| 前缀残留 (visual_asset_pkg) | 0 |
| 换行符状态 | HTML/MD 全部 LF; PNG 二进制未动 |
| 只读权限 | 0444 文件 / 0555 目录 |

## 三、索引缺口发现（需 DSHE 决策）

**asset_index.lst 有 22 条，但挂载目录实际含 23 个文件**，存在 1 项索引缺口：

| 未被索引的文件 | 位置 | 状态 |
|----------------|------|:---:|
| `github_pages/wiki_admission_gate.md` | github_pages/ 顶层 | **未在 asset_index.lst 中** |

**关键事实**:
1. 该文件存在于 `visual_asset_shturl.H.zip` 压缩包内（zip 含 29 条目，含此项）
2. 磁盘 github_pages/ 有 13 个文件，而 asset_index.lst 只索引其中 12 个
3. 其余 11 项 github_pages 文件与 10 项 web_asset 文件均已正确索引

**本轮处理决策（保守）**:
- **未修改 asset_index.lst** —— 该文件被 asset_seal_v3.txt (P17/P18 封签) 锁定哈希，
  修改会破坏 v3 封签链，违反 NO_OVERWRITE 约束（实测验证：首次尝试改 3→4 列格式
  导致 v3 表从 10/10 降为 9/10，已立即回退到 HEAD 版本并复核 10/10）
- 缺口仅在本报告与 MD5_MANIFEST P12 段中记录，**交 DSHE 决策**：
  - 方案 A: 该文件属交付资产 → 需重开 P17 封签流程，扩容 asset_index.lst 至 23 条并生成 v6
  - 方案 B: 该文件属文档附件、非可视化资产 → 从 github_pages/ 挂载点移出或加入排除清单

**该缺口不影响本次 22 项资产封签的完整性**，22/22 哈希一致。

## 四、封签层级 (v2/v3/v4/v5 四版并存)

| 封签 | 来源 | 封签范围 | 状态 |
|------|------|----------|:---:|
| asset_seal_v2.txt | P17 | P17 交付内容 | 原样保留 |
| asset_seal_v3.txt | P18 | P18 交付内容 (10 条, 含 asset_index.lst) | 原样保留 |
| asset_seal_v4.txt | P11 | P11 交付内容 (13 条) | 原样保留 |
| **asset_seal_v5.txt** | **P12 (本轮)** | **P12 重算后全部交付内容 (16 条)** | **新增** |

**v5 不覆盖 v2/v3/v4**, 四版并存, 历史交付物哈希可逐版追溯。

## 五、循环依赖规避

```
asset_seal_v5.txt        ← 封签除自身与 v2/v3/v4 外的全部交付文件
  ↓ v5 的哈希由最外层持有
pickup.flag + MD5_MANIFEST.md P12 段
```

- reseal_verification_P12.md 与 hermes_constraint_P12.md 为同级 v5 封签对象,
  故二者均不含任何哈希值, 仅记录校验结论
- pickup.flag 持有 v5 的 SHA256 (v5 不封签 hermes_dispatch/, 无循环)

## 六、校验结论

- L0~L4 全链路通过
- 22 项资产哈希 22/22 一致, asset_index.lst 保持不变 (v3 封签保护)
- v2/v3/v4 原样保留, v5 新增不覆盖 (四版并存)
- 索引缺口 1 项 (github_pages/wiki_admission_gate.md) 已记录, 交 DSHE 决策

---

*V88 Phase03 P12 T2 | HERMEShf | 2026-10-20*
