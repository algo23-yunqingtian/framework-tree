# V88 Phase03 P13 封签链路完整性复核 (seal_chain_v2_to_v6_check_P13.md)

> **TASK_ID**: V88_PHASE03_P13_HERMESHF_ASSET_INDEX_GAP_AUDIT
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1 | **生成**: 2026-10-20
> **源 commit**: 8765c21
> **结果**: L0~L4 全链路通过, 无断点

## 一、关于文件名 v2_to_v6 的说明

本文件名按工单命名为 `seal_chain_v2_to_v6_check_P13.md`, 但**实际校验范围是 v2~v5**:

- v6 封签仅在方案 B 中被提议, 且**方案 B 本轮未落地执行**
- 本轮无任何封签变更, v2/v3/v4/v5 四版原样保留
- 若后续执行方案 B 生成 v6, 需另立工单重新校验全链 (v2→v6)

**本轮封签版本数: 4 (v2, v3, v4, v5), 未生成 v6。**

## 二、单向校验链 L0~L4 完整性

| 层 | 校验动作 | 结果 | 判定 |
|:-:|----------|------|:---:|
| L0 | p18_delivery_ready.flag.SEAL_V3_SHA256 → asset_seal_v3.txt | 一致 | OK |
| L0' | pickup.flag ASSET_SEAL_V3_SHA256 → asset_seal_v3.txt | 一致 | OK |
| L0'' | pickup.flag ASSET_SEAL_V4_SHA256 → asset_seal_v4.txt | 一致 | OK |
| L0''' | pickup.flag ASSET_SEAL_V5_SHA256 → asset_seal_v5.txt | 一致 | OK |
| L1 | asset_seal_v2.txt 表 5 条 → 交付文件 | 5/5 一致 | OK |
| L2 | asset_seal_v3.txt 表 10 条 → 交付文件 | 10/10 一致 | OK |
| L2' | asset_seal_v4.txt 表 13 条 → 交付文件 | 13/13 一致 | OK |
| L3 | asset_index.lst 22 项 → 磁盘 md5+size | 22/22 一致 | OK |
| L4 | asset_seal_v5.txt 表 17 条 → 交付文件 | 17/17 一致 | OK |

（完整哈希值见 MD5_MANIFEST.md 各段与 asset_index.lst / 各版封签本体。
本文件是本轮 P13 交付物, 内嵌哈希会与后续封签形成循环依赖, 故仅记录校验结论。）

## 三、四版封签并存状态

| 封签 | 来源任务 | 表条目 | 一致性 | SHA256 列 | 状态 |
|------|---------|:---:|:---:|:---:|:---:|
| asset_seal_v2.txt | P17 | 5 | 5/5 | 截断 (12位+...) | 原样保留 |
| asset_seal_v3.txt | P18 | 10 | 10/10 | 完整 64 位 | 原样保留 |
| asset_seal_v4.txt | P11 | 13 | 13/13 | 完整 64 位 | 原样保留 |
| asset_seal_v5.txt | P12 | 17 | 17/17 | 完整 64 位 | 原样保留 |

**四版并存, 无覆盖, 无断裂。**

## 四、发现 3: v2 封签 SHA256 列为截断格式 (审计观察)

**v2 (P17) 的 SHA256 列全部为截断显示** (12 位 + `...`, 共 5 条), 无法直接做 SHA256 精确比对。

| 项 | v2 (P17) | v3/v4/v5 |
|----|:---:|:---:|
| SHA256 列格式 | 截断 | 完整 64 位 |
| SHA256 可校验 | 否 | 是 |
| MD5 列 | 完整 32 位 | 完整 32 位 |
| MD5 校验 | 5/5 一致 | 10/10 / 13/13 / 17/17 |

**判定: 非异常, 是 P17 历史格式特性。** 理由:

1. v2 为 P17 任务生成, 早于 P11/P12 的完整 SHA256 格式规范
2. MD5 列 32 位完整, 5/5 一致, 校验依然有效
3. 完整 SHA256 值记录在 MD5_MANIFEST.md 的 P17 段 (最外层权威源)
4. v2 未被本轮修改, 保持 P17 原样

**建议**: 后续若需统一格式, 可由专门工单补全 v2 的 SHA256 列 (属格式增强, 不改变校验结论)。
本轮不改动 v2 (符合 NO_MODIFY_LOCKED_SEAL)。

## 五、压缩包完整性

| 压缩包 | testzip 结果 |
|--------|:---:|
| delivery_package_v2.zip | OK 无损坏 |
| visual_asset_shturl.H.zip | OK 无损坏 |
| visual_asset_shturl.cc.zip | OK 无损坏 |

## 六、交付包冻结状态

| 项 | 值 |
|----|-----|
| hermes_dispatch/p18_delivery_ready.flag | 存在 |
| DELIVERY_PACKAGE_FROZEN | TRUE (不变) |
| C1 调度签收 | SATISFIED (PICKUP_COUNT=2) |

## 七、本轮 P13 交付物封签归属

本轮新增 4 份报告, **不在 v5 封签表内** (v5 生成于 P12, 本轮未重建 v5):

| 交付物 | 封签归属 |
|--------|---------|
| asset_gap_hash_check_P13.md | MD5_MANIFEST.md P13 段 (最外层) |
| asset_index_solution_P13.md | MD5_MANIFEST.md P13 段 (最外层) |
| seal_chain_v2_to_v6_check_P13.md | MD5_MANIFEST.md P13 段 (最外层) |
| hermes_constraint_P13.md | MD5_MANIFEST.md P13 段 (最外层) |

**设计依据 (避免循环依赖)**:
- 本轮工单要求"不产生任何封签变更", 故不重建 v5、不生成 v6
- 4 份报告作为 P13 交付物, 由最外层权威源 MD5_MANIFEST.md P13 段持有哈希
- 这是单向链最外层, 无循环依赖

## 八、复核结论

- L0~L4 全链路通过, 无断点
- 四版封签 (v2/v3/v4/v5) 原样保留, 表校验全部一致
- 22 项资产索引 22/22 一致
- 三个压缩包均无损坏
- 交付包冻结状态维持 (DELIVERY_PACKAGE_FROZEN)
- 发现 v2 SHA256 列为 P17 历史截断格式 (非异常, MD5 校验有效)
- **本轮未生成 v6, 未重建任何封签, 未修改任何封签内容**
- P13 交付物由 MD5_MANIFEST.md P13 段持有哈希 (最外层, 无循环依赖)

---

*V88 Phase03 P13 T2 | HERMEShf | 2026-10-20*