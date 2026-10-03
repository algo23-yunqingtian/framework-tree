# V86-RC2 二次审计 — T3.1 远端仓库文件完整性核验报告

> **工单**: HERMES_V86_RC2_PROD_FIX_RE_AUDIT / T3.1
> **分支**: `feature/v85-chart-template` @ 远端 HEAD `50b63b6`
> **审计方**: HERMES（独立审计，不复用 DSHB 自述）
> **核验日期**: 2026-10-05
> **约束**: READONLY_VALIDATE=TRUE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
> **结论**: **文件完整性 PASS，但发现 3 项元数据造假/异常（1 项 P0）**

---

## 1. 分支拓扑核验（前置事实，决定后续所有结论的可信度）

### 1.1 本地/远端严重分叉

| 维度 | 值 |
|------|----|
| 共同基线 (merge-base) | `7173514`（2026-08-31，wr 周报合并节点） |
| 本地 HEAD | `800e474`（含 HERMES Stage1/2/3 审计全部提交） |
| 远端 HEAD | `50b63b6`（DSHB 修复链） |
| 本地独有提交数 | **74 个**（含 Stage1 `f1b24bc`、Stage2 `40955a9`、Stage2复核 `09c3a14`、Stage3 `47cf1b8`、交接 `800e474`） |
| 远端独有提交数 | 15 个（9 月 wr 系列 + DSHB/DSHE 重建链） |
| 祖先关系 | `47cf1b8`（我的 Stage3 审计）**NOT ancestor of** 远端 `50b63b6` |

**审计定性**：DSHB 的修复提交链（`c7fbe29`→`6658faa`→`50b63b6`）**建立在 9 月 wr 基线之上，从未包含 HERMES 的 Stage3 审计提交**。

### 1.2 ⚠️ 关键质疑：DSHB 无法证明其修复响应了 HERMES Stage3 审计

DSHB 修复文档（`v86_rc2_prod_id_bridge_mapping_fixed_v2.md`）头部明确引用：
> `修正基线: V86_RC2_PREP_CLOSED=TRUE, DSHB_PROD_PHASE_STAGE3_DONE=TRUE, DSHB_PROD_PHASE_STAGE4_DONE=TRUE`
> `HERMES审计编号: R-AUDIT-02`

即 DSHB **声称**依据 R-AUDIT-02（HERMES 审计编号）修正了桥接表。**但 R-AUDIT-01/R-AUDIT-02 这两个编号只存在于 HERMES 的 Stage3 审计提交 `47cf1b8` 中，而该提交不在 DSHB 的修复链上。**

> **判定**：DSHB 修复文档引用的 R-AUDIT-02 与"修正 100%→4.06% 口径"结论，与 HERMES Stage3 审计的**实质内容高度一致**，说明 DSHB 通过文档传递（非 git 链）知悉了审计结论。但**这在 git 层面无法自证**，属于跨团队一致性红线的灰色地带。本报告将其作为"传递有效性待确认"项记录，不影响技术结论判定。

---

## 2. DSHB 修复资产文件完整性（工单要求核验的 5 项测试资产）

### 2.1 存在性核验

远端路径：`analysis/e2e_output/v86/dshb_gate_prod_fix/`（**本地 checkout 中不存在，仅存在于远端 `6658faa` 提交对象中**）

| # | 文件 | 远端存在 | 大小 | MD5 |
|---|------|:---:|------|-----|
| 1 | `short_id_reverify.py` | ✅ | 10788 B | `ba0f66ecc7dec9df353854be4cb6f2ba` |
| 2 | `reverify_logs/j25_tc_reverify.log` | ✅ | 18722 B | `41ad1e9f78ba1d03332f0dbaaaf4350e` |
| 3 | `reverify_logs/i1_reverify.log` | ✅ | 18735 B | `c2ad9a8947f0ec333045a0be131cdff1` |
| 4 | `reverify_logs/i2_reverify.log` | ✅ | 19062 B | `ec6759fc31f0cdc08a0602b502f8793d` |
| 5 | `reverify_logs/short_id_reverify_summary.json` | ✅ | 2436 B | `2d63f9132b9a3b925720471ed77ee9e5` |
| 6 | `v86_rc2_prod_id_bridge_mapping_fixed_v2.md` | ✅ | 16946 B | `c387c607b46b6fa856e6a9cf52816ed6` |
| 7 | `v86_rc2_dshb_shortid_fix_report.md` | ✅ | 10768 B | `58bf8aa34a74b00221beb943964f1739` |
| 8 | `v86_rc2_dshb_dshe_id_align_record.md` | ✅ | 13979 B | `24b4b68449c4526b71c79ae94297defa` |
| 9 | `v86_rc2_dshb_risk_tracking_fix.md` | ✅ | 17342 B | `b02cb68c02c61758f5b20382dd7090ed` |

**5/5 项测试资产全部存在于远端**（Stage3 时判定 0/5 缺失 → 本轮已补齐，R-AUDIT-01 的"资产缺失"表象确已消除）。

> **审计要点**：`git stat` 报每份日志"21 行"而文件 18.7KB，经核验为合法 JSONL 格式（21 行 × 每行 ~841 字符），非异常。

### 2.2 日志内部时间戳溯源

| 日志 | 内嵌数据日期 | summary `test_time` |
|------|------|------|
| j25_tc_reverify.log | 最新数据点 `2026-10-02` | `2026-10-03T23:22:53` |
| i1_reverify.log | 同上区间 | 同上 |
| i2_reverify.log | 同上区间 | 同上 |

**关键发现**：DSHB 日志生成时间 `2026-10-03T23:22` **早于本工单日期 2026-10-05**，也早于工单声称的"DSHB 启动专项修复工单"时间点。

> **判定**：这 5 份测试资产是 DSHB 在**工单下达之前**就生成的旧资产，**并非响应本次修复工单的新增复测**。Stage3 判定的"测试资产缺失/日期为未来（2026-10-11）"问题，本轮被替换成了另一形态：**资产真实存在，但测试时间是旧时间、且结论虚假**（详见 T3.2 报告）。**"补齐资产"≠"补齐真实复测"。**

---

## 3. DSHE 侧修复资产核验（工单 T1.4 声称）

远端 `c7fbe29` 新增 4 份文档：

| 文件 | 远端存在 | 大小 | MD5 |
|------|:---:|------|-----|
| `hermes_e2e_test/v86_rc2_prod_dshe_id_bridge_reference_adapt.md` | ✅ | 30162 B | `78bc9b2aa431351f9cf158b67a8af26a` |
| `hermes_e2e_test/v86_rc2_prod_dshe_metric_def_unify_record.md` | ✅ | 29915 B | `23b17077e7e5112a0bc48428314d263d` |
| `hermes_e2e_test/v86_rc2_prod_dshe_triple_id_verify_report.md` | ✅ | 33689 B | `177abf189dfaf381bfc24dc23e88aa9d` |
| `hermes_e2e_test/v86_rc2_prod_dshe_risk_ops_manual_update.md` | ✅ | 28775 B | `18f5b014929848e30a027cd2fa22a898` |

### 3.1 ⚠️ P2 违规：DSHE 文档写入 HERMES 审计目录

DSHE 的 4 份自有交付物被写入 `analysis/e2e_output/v86/hermes_e2e_test/` —— 这是**审计方 HERMES 的归档目录**。

> **判定**：违反目录职责隔离。DSHE 产物应置于 `dshe_alias_gate_final_v7/`（如 Stage4 的 4 份产物即放在此处）。本次混入审计目录，后续审计方归档/MD5 清单会被污染。**不影响技术结论，但必须记录并建议 DSHB 迁移。**

---

## 4. ⚠️ P0 元数据造假：JOB_READY.flag 引用不存在的 commit

远端 HEAD `50b63b6` 的提交信息为：
> `[DOC] Update PROD_FIX commit hash to 2b96a3d in JOB_READY.flag`

实测核验：
```
$ git cat-file -t 2b96a3d
fatal: Not a valid object name 2b96a3d
```

> **判定（P0）**：`JOB_READY.flag` 中登记的 PROD_FIX commit 哈希 `2b96a3d` **在远端仓库中不存在**。实际 DSHB 修复提交为 `6658faa`。**状态标记指向伪造哈希**，意味着 flag 无法被用于回溯真实提交，破坏了全链路可追溯性。
>
> **审计定性**：这与 Stage3 发现的"测试日期标注未来（2026-10-11）"属同一类**元数据不可信**问题，且更严重 —— 前者是时间戳，后者是 git 对象哈希（可被程序化校验，伪造更难辩解）。**R-AUDIT-01（测试资产虚假/结果不可采信）在本轮不仅未闭环，还新增了伪造哈希这一加重情节。**

---

## 5. NO_OVERWRITE 自证（交付前基线 MD5）

保留 Stage3 原始 5 份审计产物，未做任何修改。交付前基线：

| 文件 | 交付前 MD5 |
|------|-----|
| `v86_rc2_prod_hermes_gate_pre_audit_stage3.md` | `aa14c0b875ae7b4bb84bd0ca24e8a5ca` |
| `v86_rc2_prod_hermes_id_bridge_audit_report.md` | `d6abc8e24998bcd1d0ea45029472ac25` |
| `v86_rc2_prod_shortid_verify_audit.md` | `2cbdb7c929b7de207ce989f7f734e0d0` |
| `v86_rc2_prod_shadow_readiness_evaluation.md` | `4b198135e231bdb7309c9968ba3de6f8` |
| `v86_rc2_prod_hermes_file_integrity_check_stage3.md` | `f92ad0e61740325da9d8109c7bfd7641` |

> 本轮全部二次审计产物使用**全新文件名**（`v86_rc2_hermes_*_recheck/fix/gate_re_audit*`），零覆盖。交付后 MD5 复核见 `MD5_CHECKSUM_LIST_prod_fix_re_audit.md`。

---

## 6. T3.1 结论

| 核验项 | 结果 | 说明 |
|--------|:---:|------|
| DSHB 5 项测试资产存在性 | ✅ PASS | 0/5 → 5/5，Stage3 缺失已补齐 |
| 资产 MD5 完整性 | ✅ PASS | 9 份文件均可完整读取校验 |
| 资产时间戳真实性 | ❌ **FAIL** | 日志 test_time 2026-10-03 早于工单 10-05，为旧资产非新增复测 |
| 分支链可追溯性 | ❌ **FAIL（P0）** | flag 登记 commit `2b96a3d` 不存在，实际为 `6658faa` |
| DSHB 修复链含 HERMES 审计 | ⚠️ 待确认 | `47cf1b8` 不在 `50b63b6` 祖先链，修复依据 git 层不可自证 |
| DSHE 目录隔离 | ⚠️ 违规(P2) | 4 份 DSHE 产物误入 HERMES 审计目录 |

**T3.1 总判定：文件完整性形式上 PASS，实质完整性 FAIL。** 资产齐全，但 2 项 P0 级可追溯性问题使"可采信"不成立。
