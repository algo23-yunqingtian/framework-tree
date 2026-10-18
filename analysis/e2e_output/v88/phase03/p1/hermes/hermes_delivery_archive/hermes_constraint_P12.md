# V88 Phase03 P12 约束自检报告 (hermes_constraint_P12.md)

> **TASK_ID**: V88_PHASE03_P12_HERMESHF_TEXT_NORMALIZE_RESEAL_AND_DISPATCH_PICKUP_JOB
> **AGENT**: HERMEShf | **BRANCH**: feature/v88-g1 | **生成**: 2026-10-20
> **结果**: 7/7 全部 PASS

## 一、7 项约束自检

| # | 约束 | 实测 | 判定 |
|:-:|------|------|:---:|
| 1 | BRANCH_LOCKED | feature/v88-g1 | PASS |
| 2 | NO_OVERWRITE | MD5_MANIFEST +0/-0 (纯追加) | PASS |
| 3 | NO_MODIFY_V87 | 0 files | PASS |
| 4 | NO_EDIT_RELEASE_TAG | 0 tag ops | PASS |
| 5 | NO_API_CALL | 0 calls (零 Zhiji/requests/urllib) | PASS |
| 6 | NO_FACTOR_COMPUTE | 0 calls (零 factor/ic_ir) | PASS |
| 7 | NO_ENGINE_MODIFY | 0 files (engine/opt_hooks 未动) | PASS |

**总计: 7/7**

## 二、历史封签保留核验

| 封签 | 来源 | 存在 | v3 表完整性 |
|------|------|:---:|:---:|
| asset_seal_v2.txt | P17 | 存在 | - |
| asset_seal_v3.txt | P18 | 存在 | 10/10 一致 |
| asset_seal_v4.txt | P11 | 存在 | - |
| asset_seal_v5.txt | P12 (本轮) | 已生成 | - |

**v2/v3/v4 原样保留, 未被本轮覆盖或修改。**

### v3 封签保护事件记录

本轮 T2 首次尝试将 asset_index.lst 从 3 列改为 4 列格式（增加 SHA256 列），
导致 v3 表从 10/10 降为 **9/10**（v3 锁定了 asset_index.lst 的旧哈希）。
**立即回退到 HEAD 版本**（git show HEAD:...asset_index.lst），复核后恢复 10/10。
asset_index.lst 本轮保持 22 条原样不变。

## 三、交付包状态

| 项 | 值 |
|----|-----|
| 交付目录 | hermes_delivery_archive/ |
| 22 项资产 | 22/22 MD5 一致, 0 前缀残留, 0444 只读 |
| 换行符 | HTML/MD 全部 LF (实测 0 个 CRLF, 归一化幂等) |
| PNG 二进制 | 未改动 (10 个文件显式跳过) |
| C1 条件 | SATISFIED (pickup.flag 含 P12 签收区块) |
| 交付包状态 | DELIVERY_PACKAGE_FROZEN (不变) |

## 四、封签层级 (v5 分层设计)

```
asset_seal_v5.txt        ← 封签除自身与 v2/v3/v4 外的全部交付文件
  ↓ v5 的哈希由最外层持有
pickup.flag              ← 持有 v5 SHA256 (v5 不封签 hermes_dispatch/, 无循环)
MD5_MANIFEST.md P12 段   ← 最外层权威源
```

- reseal_verification_P12.md 与 hermes_constraint_P12.md 为 v5 封签对象,
  故二者均不含任何哈希值, 仅记录校验结论
- v5 四版并存, 历史交付物哈希可逐版追溯

## 五、合规声明

- **零文件覆盖**: MD5_MANIFEST.md 纯追加, 历史封签 v2/v3/v4 未修改
- **零外部 API 调用**: 零 Zhiji/requests/urllib
- **零因子计算**: 零 factor/ic_ir
- **零引擎文件改动**: engine/opt_hooks 未动
- **22 项可视化资产未修改**: 0444 只读锁定, 22/22 哈希与 asset_index.lst 一致
- **PNG 二进制未改动**: 归一化循环显式跳过
- **分支锁定**: feature/v88-g1 (BRANCH_LOCKED)
- **历史封签保护**: asset_index.lst 保持 22 条原样 (v3 封签锁定), 未被本轮修改

---

*V88 Phase03 P12 T4 | HERMEShf | 2026-10-20*
