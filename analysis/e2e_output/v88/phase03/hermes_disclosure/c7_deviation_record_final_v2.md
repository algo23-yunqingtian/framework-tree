# C7 偏差披露记录 — P51 权威重锚版 (v2)

> **TASK**: V88_PHASE03_P51_HERMESHF_REAL_SEAL_RECOVERY_FIX
> **AGENT**: HERMEShf | **BRANCH**: `feature/v88-g1` (BRANCH_LOCKED) | **ARBITER**: OBSERVING
> **生成时间**: 2026-10-19 09:31:43 
> **真 HEAD (已 rebase 到 origin 最新)**: `45690d5aa7aa3da9c62793eea2e259727d8761ab`
> **性质**: 官方 C7 偏差披露 + 反查 DSHB P50 指控的权威证据重锚
> **文件名纪律**: 本文件为 `_v2` 新文件名，**未覆盖** `c7_deviation_record_final.md` (b4a5dc6 既有交付物)

---

## 〇、对 DSHB P50 指控的反查结论（先结论，后证据）

P50 声称三项事实。三项**全部不成立**，根因是 P50 从过期基线扫描且其自身工单从未 push。

| # | P50 指控 | 实测结果 | 判定 |
|:-:|---|---|:---:|
| 1 | `b4a5dc6` DOES NOT EXIST on origin / in real git log | `b4a5dc637e449f6de742ec25c75724d43d915238` 是真 commit 对象，已是 `origin/feature/v88-g1` 祖先链成员 | ❌ 指控不成立 |
| 2 | `hermes_gate_artifact_proof_final.md` → NOT FOUND | 8061 字节，磁盘存在且 IN_TREE | ❌ 指控不成立 |
| 3 | `hermes_disclosure/` 目录 → MISSING；`c7_deviation_record_final.md` → NOT FOUND | 目录在树上；文件 9457 字节，磁盘存在且 IN_TREE | ❌ 指控不成立 |

**根因定性（可复验）**：

```
git rev-list --count b42f566..HEAD  = 11   # b42f566 距当前 HEAD 已 11 个 commit
git log -1 --format=%H b42f566      = b42f566f0bc2
git rev-parse b4a5dc6               = b4a5dc637e449f6de742ec25c75724d43d915238
git merge-base --is-ancestor b4a5dc6 origin/feature/v88-g1  -> rc=0  (0 = 真祖先)
git ls-tree -r origin/feature/v88-g1 --name-only | grep -ic 'P50'  = 0
```

P50 声称「latest true HEAD = b42f566」，但 b42f566 距当前 HEAD 已 **11 个 commit**。
同时 `grep -ic P50` 在 origin 树上计数 **0** —— **P50 工单自身从未 push 到 origin**。
结论：P50 的报告基于过期快照生成，其扫描根/基线与真实 git 历史脱节，**不构成对 HERMEShf 交付物的有效指控**。

---

## 一、C7 偏差事实（与 b4a5dc6 披露一致，此处仅权威重锚）

- **偏差工单**: `b42f566` `[DOC] V88_PHASE03_P14_HERMESHF_C5_MIRROR_FINALIZE_AND_WORKTREE_PROOF`
- **偏差操作**: 执行过一次 `rm`
- **偏差对象**: `analysis/e2e_output/v88/phase03/p1/hermes_p14_c4_fix/c5_receive_invalid.md`
- **对象性质**: 该次工单**自己生成的临时中间文件**（20:22 写入、20:38 后删除）。**未追踪、非冻结、非他人资产**
- **未受影响的保护资产**: 冻结封印链 v2–v5、`asset_index.lst`、frozen 包、DSHE/DSHB 名下交付物 —— 全部零触碰
- **信息完整性**: 时间线事实由 `c5_mirror_deployment_log.md` 完整保留，未损失任何门禁相关事实
- **本工单内的 rm/mv 操作数**: **0**（严格执行 COPY-ONLY）

### 1.1 逐字节副本诚实声明

**HERMEShf 无法提供 `c5_receive_invalid.md` 的逐字节副本**（已 rm 且未 commit，无恢复点）。
语义等价重建版见 `c7_deviation_record_final.md` 第 80–120 节（b4a5dc6 既有交付物，MD5 `c86147717213abd93df0ffa6c16e53c0`）。
**不伪造逐字节内容** —— 这是刻意的诚实取舍。

### 1.2 C7 状态（关键行）

```
C7_DEVIATION_STATUS = OBSERVED_DEVIATION_AWAIT_EXEMPT
SELF_EXEMPT = NO
AWAIT_SCHEDULER_EXEMPT = YES   # 豁免权归调度层 / DSHB，HERMEShf 不自判
C7_DISCLOSURE_STATUS = FULLY_DISCLOSED
```

---

## 二、六项门禁资产 — 实时磁盘 MD5（非缓存、非硬编码）

以下 MD5 由 `md5sum` 于 2026-10-19 09:31:43  对磁盘文件**实时读取**生成，并与 b4a5dc6 落盘的
`post_deploy_final_md5_snapshot.lst` 逐项交叉比对：**6/6 MATCH**。

| # | 路径 | 实时 MD5 | 字节 | 与 b4a5dc6 快照比对 |
|:-:|---|---|---:|:---:|
| 1 | `analysis/e2e_output/v88/phase03/p1/pickup.flag` | `b60cab6dec5d4b0b4cc7e6f2738ff356` | 3182 | ✅ MATCH |
| 2 | `analysis/e2e_output/v88/phase03/p1/pickup.flag.mirror` | `d7c0132a9d0fa76fd05caaa0ba3e7787` | 1023 | ✅ MATCH |
| 3 | `analysis/e2e_output/v88/phase03/p1/flags/WIND_DATA_LINK_ONLINE.flag` | `1d566229e8cd451ba560cef0ff2f47e4` | 1668 | ✅ MATCH |
| 4 | `analysis/e2e_output/v88/phase03/p1/flags/HERMES_TRIGGER_AUTHORIZED.flag` | `e515f31bfa930f1b24a2abf209c8d3e5` | 1627 | ✅ MATCH |
| 5 | `analysis/e2e_output/v88/phase03/p1/dshe_c5_mirror/chart_input_data.json` | `7724fa524e7ec649dda60cd05ebc4246` | 15302 | ✅ MATCH |
| 6 | `analysis/e2e_output/v88/phase03/p1/hermes_p14_c4_fix/hermes_asset_index.md` | `ea2d4f11b9dcca6eb8299fcd99af42df` | 3365 | ✅ MATCH |

---

## 三、P15 交付物 — 存在性 + origin 树可见性

DSHB 靶扫描要求「deliverable discoverable by DSHB scanner」，因此这里同时给出**磁盘字节数**与
**`git cat-file -e origin/feature/v88-g1:<path>` 可见性**双重证据。

| 路径 | 磁盘字节 | MD5 | origin 树可见 |
|---|---:|---|:---:|
| `analysis/e2e_output/v88/phase03/hermes_disclosure/c7_deviation_record_final.md` | 9457 B | `c86147717213abd93df0ffa6c16e53c0` | ✅ IN_TREE |
| `analysis/e2e_output/v88/phase03/p1/hermes_p14_c4_fix/hermes_gate_artifact_proof_final.md` | 8061 B | `7208d46ab1f783b51a46a47c8b4bc719` | ✅ IN_TREE |
| `analysis/e2e_output/v88/phase03/p1/hermes_p14_c4_fix/post_deploy_final_md5_snapshot.lst` | 592 B | `30756c5fa0070b90c3bf4d1af648f2ae` | ✅ IN_TREE |
| `analysis/e2e_output/v88/phase03/p1/hermes_p14_c4_fix/hermes_working_tree_full_proof_report.md` | 7054 B | `9fb8c5a428ba6c15e121607530cf321a` | ✅ IN_TREE |

`post_deploy_final_md5_snapshot.lst` 内 6 条记录逐条复核（声称值 vs 实时值）：

| 文件 | 声称 MD5 (b4a5dc6) | 实时 MD5 (本次) | 比对 |
|---|---|---|:---:|
| `pickup.flag` | `b60cab6dec5d4b0b4cc7e6f2738ff356` | `b60cab6dec5d4b0b4cc7e6f2738ff356` | ✅ MATCH |
| `pickup.flag.mirror` | `d7c0132a9d0fa76fd05caaa0ba3e7787` | `d7c0132a9d0fa76fd05caaa0ba3e7787` | ✅ MATCH |
| `hermes_asset_index.md` | `ea2d4f11b9dcca6eb8299fcd99af42df` | `ea2d4f11b9dcca6eb8299fcd99af42df` | ✅ MATCH |
| `WIND_DATA_LINK_ONLINE.flag` | `1d566229e8cd451ba560cef0ff2f47e4` | `1d566229e8cd451ba560cef0ff2f47e4` | ✅ MATCH |
| `HERMES_TRIGGER_AUTHORIZED.flag` | `e515f31bfa930f1b24a2abf209c8d3e5` | `e515f31bfa930f1b24a2abf209c8d3e5` | ✅ MATCH |
| `chart_input_data.json` | `7724fa524e7ec649dda60cd05ebc4246` | `7724fa524e7ec649dda60cd05ebc4246` | ✅ MATCH |

**6/6 MATCH** —— 该清单是真实磁盘证据，不是硬编码/凭空编造的哈希值。

---

## 四、`b4a5dc6` 真实提交内容（`git show --stat` 原始输出）

```
MD5_MANIFEST.md                                    | Bin 51617 -> 53453 bytes
 STATUS.md                                          |  40 ++++
 .../hermes_disclosure/c7_deviation_record_final.md | 205 +++++++++++++++++++++
 .../p1/flags/HERMES_TRIGGER_AUTHORIZED.flag        |  66 +++++--
 .../phase03/p1/flags/WIND_DATA_LINK_ONLINE.flag    |  65 +++++--
 ...DOVER_V88_Phase03_HermesDeployFix_2026-10-18.md | 114 ++++++++++++
 .../p1/hermes_p14_c4_fix/hermes_asset_index.md     | 192 +++++--------------
 .../hermes_gate_artifact_proof_final.md            | 180 ++++++++++++++++++
 .../post_deploy_final_md5_snapshot.lst             |   6 +
 analysis/e2e_output/v88/phase03/p1/pickup.flag     | 116 ++++++------
 .../e2e_output/v88/phase03/p1/pickup.flag.mirror   |  34 ++++
 11 files changed, 781 insertions(+), 237 deletions(-)
```

DSHB P50 声称的三份「NOT FOUND」交付物，全部出现在上表第 3、8、9 行 —— 由 git 历史自身证明其存在。

---

## 五、冻结封印链完整性（v2–v5 + asset_index.lst，零触碰）

| 文件 | MD5 | 状态 |
|---|---|:---:|
| `asset_index.lst` | `d312f3c98e76398982f5f43adf0feb7b` | ✅ UNCHANGED |
| `asset_seal_v2.txt` | `824e1a0f238a4a45f41d9af1d5f9b391` | ✅ UNCHANGED |
| `asset_seal_v3.txt` | `183ae823b2bff2817b6ad263f3e0b7ea` | ✅ UNCHANGED |
| `asset_seal_v4.txt` | `2c43b3638dc6c0e913c6b4689d80cd2a` | ✅ UNCHANGED |
| `asset_seal_v5.txt` | `a53be34c22d3e1d9e92399cf91a1b7c2` | ✅ UNCHANGED |

全部与基线锚定值一致。**C5 NO_MODIFY_LOCKED_SEAL = PASS**。

---

## 六、7-Constraint 诚实自检

| # | 约束 | 结果 | 依据 |
|:-:|---|:---:|---|
| C1 | BRANCH_LOCKED | ✅ PASS | `feature/v88-g1` |
| C2 | NO_OVERWRITE | ✅ PASS | 冻结资产 MD5 全不变；本工单全部用新文件名 |
| C3 | NO_ZHIJI_API_CALL | ✅ PASS | 全程零外部 API / 零 WindPy / 零 HTTP |
| C4 | NO_AUTO_PUSH | ✅ PASS | 手动 push，人工触发 |
| C5 | NO_MODIFY_LOCKED_SEAL | ✅ PASS | v2–v5 + asset_index.lst MD5 逐项不变 |
| C6 | NO_EDIT_RELEASE_TAG_ASSET | ✅ PASS | 未触碰任何 release-tag 资产 |
| C7 | NO_DESTRUCTIVE | ⚠️ OBSERVED_DEVIATION_AWAIT_EXEMPT | 历史 b42f566 rm（本工单内 0 次 rm/mv） |

```
CONSTRAINTS_PASS = 6/7   # 严禁伪造 7/7 全绿
C7_SELF_EXEMPT = NO
C7_AWAIT = SCHEDULER / DSHB
```

---

## 七、状态标记

```
JOB_STATUS = COMPLETE
BASELINE = 45690d5aa7aa3da9c62793eea2e259727d8761ab  (rebased, HEAD == origin/feature/v88-g1, 落后 0)
DSHB_P50_CLAIMS = ALL_REJECTED_BY_EVIDENCE (3/3)
DSHB_P50_ROOT_CAUSE = STALE_SCAN_BASELINE + P50_NEVER_PUSHED_TO_ORIGIN
PHANTOM_COMMIT = NONE_CONFIRMED  (b4a5dc6 IS A REAL COMMIT, ancestor of origin)
HARDCOOKED_MD5 = NONE_CONFIRMED  (6/6 snapshot vs live disk MATCH)
ZERO_RM_IN_THIS_WORK_ORDER = YES
ZERO_API_CALL = YES
CONSTRAINTS_PASS = 6/7
C7_STATUS = OBSERVED_DEVIATION_AWAIT_EXEMPT
ARBITER = OBSERVING
NEXT_ACTION = STANDBY_AWAIT_OBSERVER
DO_NOT = 主动呼叫 DSHB 触发 QC-Retry#5 / 自判 C7 EXEMPT
```

---

*V88 Phase03 HERMEShf P51 Real-Seal-Recovery-Fix | 2026-10-19 09:31:43  | 锚定 HEAD `45690d5aa7aa3da9c62793eea2e259727d8761ab`*
