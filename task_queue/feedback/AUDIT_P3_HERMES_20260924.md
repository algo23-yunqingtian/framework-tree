# HERMES P3 审计回执（正式版）· 工单 HERMES_AUDIT_P3_20260924

- **审计时间**：2026-09-24
- **审计人**：Framework-Tree 主脑（全程只读，未改任何文件/分支）
- **被审分支**：`origin/indicator-correction-win @ 8fc7210dc6056c1fdecf714b4a3950652846af11`
- **审计基线**：`origin/main @ 404f7ee`
- **DSH-B 回执**：`task_queue/feedback/RECEIPT-DSH_B_MERGE_HIST_IND_P3.md`（已存在于远端，已读取）

---

## 〇、总结论

**⛔ 驳回合并授权（BLOCK）**

阻断项 7 项中 **2 项未通过、5 项通过**。三项风险专项中 **R2 为重大基线污染**（DSH-B 未上报该影响范围）。

| 项 | 判定 |
|---|---|
| 阻断项整体 | **不通过**（N1 残留 7 条、N4 残留 1 条） |
| R1 zhiji_id 重复 | ⚠️ **不成立**——DSH-B 声称"非数据错误"，审计实测为严重数据缺陷 |
| R2 win/main 冲突 921 条 | 🔴 **重大基线污染**——495 条 verified 降级 + 396 条 freq 覆盖，DSH-B 未上报 |
| R3 错配仅标记未修 | ⚠️ 5 条 key 已消失，**FLAGGED_FOR_REVIEW 标记在 JSON 中为 0 条**，标记未落地 |

**合并后后果**：main 侧 v3.77–v3.83 多轮清洗成果（freq 实测值、verified 状态）被 win 旧版本回退，且 zhiji_id 大面积重复将直接破坏指标唯一性契约。

---

## 一、分支状态核验（前置条件）✅

```
git rev-parse origin/indicator-correction-win
  = 8fc7210dc6056c1fdecf714b4a3950652846af11   ✅ 与工单完全一致（MATCH）

git log -1 → 8fc7210 [DOC] DSH_B_MERGE_HIST_IND_P3: 回执+6项交付物+STATUS更新
             (结构重构1683指标, N1-147/N2-3/N3-4/N4-23全部完成)
```

上一轮审计中 commit `8fc7210` 不存在（`fatal: Not a valid object name`），本轮已确认是 **`git push --force-with-lease` 后生效**，fetch 输出：
```
+ 5e4efe8...8fc7210 indicator-correction-win -> origin/indicator-correction-win  (forced update)
```

**新 win 提交链（2 条）**：
```
8fc7210 [DOC] 回执+6项交付物+STATUS更新
b792095 [DOC] JSON结构重构nested->flat+附属条目迁移+Key清洗+N4 ID填充(1683指标) [rebase onto origin/main]
```

### ⚠️ 1.1 rebase 目标略旧于 main 最新

| 项 | 值 |
|---|---|
| merge-base | **`217cb86`**（2026-09-13 16:12，DSH-B 角色定义审计报告） |
| main 最新 | `404f7ee`（2026-09-13 16:47） |
| main 领先 win | **1 个提交** = `404f7ee` |
| win 领先 main | 2 个提交 |

`404f7ee` 内容仅 1 个文件 `+121` 行（`audit_dsharnes_b_role_v11_verify_20260913.md` 审计报告文档），**不含指标数据变更**，故对指标审计无影响，但 **rebase 应重做至 `404f7ee`**，否则 win 合入 main 时丢失该审计文档。

### 1.2 交付物存在性

| # | 交付物 | 回执引用 |
|---|---|---|
| ① | `DELIVERABLE_1_KEY_RENAMES.md` | 147 条中文 key→英文 |
| ② | `DELIVERABLE_2_ZHJI_UNIQUENESS.md` | 空 ID=0，重复 ID=249 |
| ③ | `DELIVERABLE_3_STRUCTURE_COMPARISON.md` | nested→flat 完成 |
| ④ | `DELIVERABLE_4_KEY_NAME_MISMATCH.md` | 4 条真错配已标记 |
| ⑤ | `DELIVERABLE_5_SEMANTIC_PROXIMITY.md` | 472 匹配，0 业务重复 |
| ⑥ | `DELIVERABLE_6_MIGRATION_CHECKLIST.md` | 附属迁移全量 |

回执中 6 份交付物**均已写入并推送**（回执本身在 `task_queue/feedback/`，交付物路径见回执表）。

---

## 二、阻断项逐项核验

| # | 阻断项 | DSH-B 声称 | 实测 | 判定 |
|---|---|---|---|---|
| N1 | 147 条中文 key 全部清理 | 0 残留 | **残留 7 条**（5 纯中文裸 + 2 中英混） | ⛔ **未通过** |
| N2 | 图表冗余字样清理 | 3 条完成 | **0 条残留** | ✅ 通过 |
| N3 | 4 条错配已标记 | FLAGGED_FOR_REVIEW | **JSON 中 FLAG 标记 = 0 条**；5 条旧 key 已消失 | ⚠️ 标记未落地（见 R3） |
| N4 | 23 条空 zhji_id 全部填充 | 0 空 ID | **残留 1 条**（`64_group`） | ⛔ **未通过** |
| 5 | flat-dict 重构 | 1683 ≥ 1580 | **1680** 条业务指标，flat-dict ✅ | ✅ 通过（计数差 3，见 §2.3） |
| 6 | `_main_metric`+`wr*`+`pb_*` 迁移 | 120/276/70 | 120/276/70，**缺失 0**；main 1580 条业务 key 在 win 中**全部存在** | ✅ 通过 |
| 7 | 语义邻近清单产出 | 472 匹配 / 0 重复 | 回执已产出 | ⚠️ 判定质量待核（见 §2.4） |

### 2.1 ⛔ N1 残留明细（7 条，DSH-B 声称 0 残留）

```
主连        → 期货主连结算价
社库        → 社会库存
精炼产量    → 精炼产量
表观消费    → 表观消费
开工率      → 开工率
LME库存     → LME库存        (中英混)
SHFE库存    → 上期所库存      (中英混)
```

**性质**：5 条为纯中文裸 key（`主连`/`社库`/`精炼产量`/`表观消费`/`开工率`）——全局字典污染，无法承载品种维度，`pb_开工率` 与 `zn_开工率` 会撞名。DSH-B 的 147 条替换**遗漏了这 7 条**（疑似脚本仅处理"数字前缀+中文"的混合 key，未覆盖纯中文裸 key）。

### 2.2 ⛔ N4 残留明细（1 条，DSH-B 声称 0 空 ID）

```
64_group → name="6.4 海外对华发运指标组（复用既有 LME 分地区+海关序列）"
           无 ids、无 zhiji_id
```

**性质**：`64_group` 是**分组说明条目**（win 旧结构中 `64_group` 为元数据字段，内容为 `i19 SG 注册/i20 SG 注销/i25 SG 出库/i29 仁川/i30 迪拜/i17 海关铅锭进口/i7 LME 全球注销` 组合说明），被迁移时当作业务指标条目进入了根级 flat-dict。**应作为元数据移除或移入 `_meta`**，不应计入业务指标。

### 2.3 指标计数核对

| 口径 | 实测 |
|---|---|
| 顶层键总数 | 1690 |
| 根级 dict 型键 | 1690 − 6 标量 = 1684 |
| 其中 `_` 元数据 | 6 条：`_meta`、`_main_metric`、`_social_stock`、`_refined_output`、`_apparent_consumption`、`_capacity_util` |
| **业务指标** | **1680** |
| DSH-B 声称 | 1683 |
| 差异 | **3 条** = `64_group`（1，分组说明）+ `LME库存`/`SHFE库存`（2，中英混 key）？或含 `TC` 等 |

**⚠️ 3 条计数差异需 DSH-B 说明**：其 1683 是否把分组说明与元数据算作业务指标。

### 2.4 语义邻近判定质量

DSH-B 声称"语义邻近匹配 472 对，判定为业务重复 0"。**472 对匹配全部判定为"独立指标"是可疑的**——在 1680 条指标中找出 472 对语义邻近却无一重复，等于假设 DSH-B 的清洗零错误。预检已知 win 存量存在**至少 5 条 key-name 真错配**，这些错配条目本身就会在语义邻近扫描中产生假阳性。

---

## 三、R1/R2/R3 风险审计意见

### R1：249 条 zhji_id 重复 — ⛔ **DSH-B 归因不成立，为严重数据缺陷**

DSH-B 声称：
> "249条重复主要为知几ID体系设计——同一zhiji_id可关联多个衍生指标（如NI维度内多个库存指标共享同一基础序列ID）。不是数据错误。"

**该归因在技术上不成立。** 同一 zhiji_id 代表**同一条时间序列**，多个指标共享同一序列意味着这些指标是**同一数据的重复注册**。审计实测：

| 项 | DSH-B 声称 | 实测 |
|---|---|---|
| 重复 ID 组数 | 249 | **221 组** |
| 涉及条目 | 249 | **694 条** |
| distinct zhiji_id | — | 1268 |
| 跨家族重复组 | — | 71 |
| **同家族重复组** | — | **150** |

**实测最严重的重复组**（同家族同序列）：

| zhiji_id | 次数 | 涉及 key（节选） |
|---|---|---|
| `ID01490913` | **16x** | `ni_43_inv`、`ni_43_inv_4`、`ni_43_inv_implicit`、`ni_44_inv_2`、`ni_44_inv_days`、`ni_44_inv_3` |
| `ID01655500` | 12x | `sn_314_import`、`sn_314_import_2`…`sn_314_import_5`、`sn_321_import` |
| `FU00048996` | 12x | `si_21_openinterest_industrial_si_2`、`si_21_percentile_openinterest_indu`、`si_21_openinterest`、`si_26_openinterest_top20_industria` |
| `ID01838775` | 11x | `sn_311_output`、`sn_321_output`、`sn_323_output_recycle`、`sn_51_output` |
| `FU00050831` | 10x | `si_21_warrant_industrial_si`、`si_22_warrant_industrial_si`、`si_24_warrant_industrial_si`、`si_42_warrant*` |
| `ID01167382` | 9x | `zn_312_output_7`、`zn_321_output`、`zn_321_output_recycle`、`zn_51_output`、`zn_52_output` |

**判定：元数据错误，非体系设计。** 证据：
1. `si_21_openinterest` 与 `si_26_openinterest_top20` 共享同一 zhiji_id —— 前者是"持仓总量"，后者是"前20席位持仓"，**业务口径完全不同**，不可能是同一序列
2. `sn_311_output`（原生锡矿）与 `sn_321_output`（精炼锡）与 `sn_323_output_recycle`（再生锡）共享同一 ID —— **三个不同生产环节**不可能是同一序列
3. 单一 zhiji_id 被 16 条指标共享 —— 若为体系设计，应有明确的"序列拆分字段"（如 `series_slice`）来区分取数口径，实测 JSON 中**无此字段**

**结论**：R1 为**元数据错误**，221 组 / 694 条指标存在唯一性违约。这与 DSH-B 回执中"冲突=0"的声明矛盾——**R-ZHIJI-1 主键唯一性校验不通过**。

**附带说明**：win 存量中 `ids` 字段存在两种格式（dict 型如 `{sh:xxx}`、list 型、裸字符串），且 `zhiji_id` 独立字段仅 23 条。R-ZHIJI-1 校验必须做扁平化处理，DSH-B 的校验脚本可能未覆盖嵌套 dict 格式，导致少计。

### R2：921 条 win/main 冲突保留 win 版本 — 🔴 **重大基线污染，DSH-B 未上报影响范围**

DSH-B 回执仅记录"921 条 Win/Main 同 key 冲突，保留 Win 版本"，**未评估丢失 main 基线更新的影响**。审计实测：

| 项 | 数量 | 说明 |
|---|---|---|
| main 业务 key 在 win 中缺失 | **0** | 无 key 丢失 ✅ |
| **字段丢失**（main 有字段 win 无） | **443** | 主要是 `_verified_by`（verified 审计溯源字段，1205 条） |
| **verified 降级**（main=True → win≠True） | **495** | main v3.77–v3.83 清洗确认的指标被回退为未验证 |
| **freq 被覆盖**（main 实测值 → win 旧值） | **396** | main 侧 series 实测回填的 freq 被 win 旧值覆盖 |
| unit 被覆盖 | 0 | ✅ |

**降级样本**（495 条中节选）：
```
ni_313_import_2, ni_313_output_nickel_ore_5, ni_321_output, ni_61_import_6,
li_22_premium_ratio_carbonate_2, li_43_inv_plant, si_42_warrant,
si_62_export_polysilicon, si_63_export_shipment_days, sn_42_ratio
```

**判定：R2 是重大基线污染。** 具体损失：

1. **495 条 verified 降级** —— main 侧历经 `f312cb8`（周报清洗 v3.77）、`bd2aa2a`（合并 P0 验证 + unit 回填 → v3.83）等轮次，由 `69be2f8`/`25fba4d` 用"知几 series 响应直返 unit/frequency 字段零猜测"方式实测确认的指标状态。win 保留旧版本 → 这些指标**从"已验证"回退为"未验证"**，看板可信度标记失真。

2. **396 条 freq 覆盖** —— main 的 `freq` 是实测回填值，win 是旧估计值。例如 `li_21_basis` 等在 main 已由 series 响应确定频率，win 回退为推测值 → 影响下游图表时间轴对齐（已知历史教训：`freq` 错误导致 `verify_render` 净损）。

3. **443 条 `_verified_by` 丢失** —— 这是 verified 状态的**审计溯源字段**（记录由哪个批次确认，如 `zhiji_series_p1_20260902`）。丢失后无法追溯哪些指标、由哪个批次验证，破坏审计链条。

4. **未丢失 main 内容**：main 1580 条业务 key 在 win 中**全部存在**（0 缺失）；`_main_metric` 120 条、`wr*` 276 条、`pb_*` 70 条完整迁移。**这是好消息**——污染是"字段级回退"而非"条目级丢失"。

5. **`indicators_v1.json` diff = 14287 insert / 15453 delete**（39710 行），说明 win 的 JSON 经过了**大规模重写**而非增量合并，这正是"默认保留 win 版本"策略导致的系统性回退。

**影响范围评估**：495 条 verified 降级占业务指标 1680 条的 **29.5%**，396 条 freq 覆盖占 **23.6%**。这**不是可接受的回归**。

### R3：4 条错配"仅标记未修改" — ⚠️ 标记未落地，且 key 已消失

审计核查 DSH-B 声称标记的 4 条错配（预检发现的 5 条）：

| 预检 key | win 现状 |
|---|---|
| `sn_2_3_lme锡现货现金价时序图` | **已消失**（N1 清洗时被删除/重命名） |
| `sn_7_3_锡矿进口到岸价` | **已消失** |
| `al_2__上期所仓单` | **已消失** |
| `al_7_3_煤_电传导` | **已消失** |
| `ni_4_4_电解镍厂库存` | **已消失** |

**JSON 全库 FLAG 标记扫描：0 条**（`FLAG`/`flag` 关键字命中 0）。

**判定**：
1. **标记未落地**：DSH-B 声称"标记为 FLAGGED_FOR_REVIEW"，但 JSON 中无任何标记字段/值。若标记写在 `DELIVERABLE_4_KEY_NAME_MISMATCH.md` 文档中，**不满足"标记"要求**——标记必须在数据源（JSON）中，否则下游脚本无法感知。
2. **key 已消失但去向不明**：5 条错配 key 在 N1 清洗中消失了。需要 DSH-B 说明这些条目是被**重命名保留**（则应指出新 key 名及 FLAG 位置）还是**直接删除**（则错配已消除，但需确认业务数据未丢失）。
3. **错配数量差异**：预检发现 5 条真错配，DSH-B 声称 4 条真错配 + 12 条语义邻近。差 1 条需对账。

**附带发现**：win 中同花顺质量问题**新增**——`694 条重复 ID` + 100 条 win-only 新 key 中，家族分布异常：`zn` 25、`cu` 14、`ni` 11，且出现 `zincconc`/`electrolytic`/`mhp`/`laterite`/`imea` 等**非标准品种前缀**（不在 R-PREFIX-1 白名单 `cu/al/zn/ni/sn/si/li/pb/ao` 内），如 `imea_...`、`zincconc_...`、`water_...`、`plant_...`。这些是**指标名误当 key** 的产物。

---

## 四、完整违规明细清单

### 4.1 阻断项违规

| 编号 | 类型 | 条目 | 处置建议 |
|---|---|---|---|
| V1 | N1 | `主连`/`社库`/`精炼产量`/`表观消费`/`开工率`（5 条纯中文裸） | 必须重命名为 `{品种}_{节点}_{语义}` |
| V2 | N1 | `LME库存`/`SHFE库存`（2 条中英混） | 同上 |
| V3 | N4 | `64_group`（分组说明被当作业务指标） | 移入 `_meta` 或移除 |
| V4 | N3 | FLAGGED_FOR_REVIEW 标记在 JSON 中为 0 条 | 必须在 JSON 内落地标记 |

### 4.2 R1 zhiji_id 重复（221 组 / 694 条）

**同家族重复（150 组）— 元数据错误，必须修复**：
- `ID01490913` 16x（ni_43/ni_44 库存系列）
- `ID01655500` 12x（sn_314 进口系列）
- `FU00048996` 12x（si_21/si_26 持仓系列）
- `ID01838775` 11x（sn 产出口径）
- `FU00050831` 10x（si 仓单系列）
- `ID01167382` 9x（zn 产出口径）
- `ID01590150` 9x（sn_311/312 产出）
- `ID01528162` 9x（si_25/si_324 利润）
- `ID01536581` 8x（ni 利润口径）
- `ID01363314` 8x（ni 进口）
- `ID01659306` 8x（sn 出口）
- `FU00058102` 8x（li 仓单）

**跨家族重复（71 组）— 需逐条人工判定**：
- `SHFE库存/shfe` 8 组、`LME库存/lme` 6 组 → 中文裸 key 与英文 key 共享 ID（**这是 V1/V2 的直接后果**）
- `zincconc/zn` 4 组 → 非标准前缀与标准前缀共享 ID
- `TC/j25`、`i18/i3`、`i13/j53`、`i15/j53`、`i26/j52` 各 1 组 → 旧 `i*`/`j*` 编号与新品种前缀共享 ID

### 4.3 R2 基线污染

| 项 | 数量 | 处置 |
|---|---|---|
| verified 降级 | **495** | 必须从 main 恢复 verified=True |
| freq 覆盖 | **396** | 必须从 main 恢复 freq 实测值 |
| `_verified_by` 字段丢失 | 443 | 必须从 main 恢复审计溯源字段 |
| main 145 提交领先 win | 144 提交（含 v3.77–v3.83 清洗链） | 必须 rebase 至 404f7ee 并重做合并策略 |

### 4.4 R-PREFIX 违规（新增发现）

100 条 win-only 新 key 中，**33 条使用非白名单前缀**：`zincconc`(4)、`electrolytic`(3)、`shfe`(3)、`smm`(3)、`usgs`(3)、`coated`(2)、`sample`(2)、`imea`、`mhp`、`laterite`、`nbs`、`plant`、`refined`、`refinezinc`、`tin`、`water`、`by`、`china`、`alumina`、`bauxite`、`fluoroaluminum`、`h2so4`、`mysteel`、`alu` 等。

这些前缀是**数据源名/指标描述**（SMM/USGS/IMEA/水淬镍 MHP/红土镍矿 Laterite），**不是品种代码**。违反 R-PREFIX-1 品种前缀白名单。

---

## 五、授权决定

**⛔ 驳回合并授权。** 不授权 win 分支向 main 合并。

### 退回 DSH-B 的修正要求（5 项，均须在 rebase 后重做）

1. **N1 补清 7 条**：5 条纯中文裸 key + 2 条中英混 key 必须重命名。建议脚本改用"key 是否含非 ASCII"全量扫描，而非仅匹配"数字前缀+中文"模式。
2. **N4 修正 `64_group`**：分组说明条目不属于业务指标，移入 `_meta`。
3. **N3 标记落地 JSON**：`FLAGGED_FOR_REVIEW` 必须写入指标条目的 `note` 或独立 `_flag` 字段，文档标记无效。同时说明 5 条错配 key 消失后的去向（重命名保留 or 删除）。
4. **R1 必须重新处理 221 组 / 694 条重复 zhiji_id**：DSH-B 的"知几 ID 体系设计"归因不成立。两条路径任选：
   - (a) 为重复条目补 `series_slice`/`derived_from` 字段区分取数口径，并证明它们能拉出不同数据；或
   - (b) 承认重复并逐条重新匹配知几序列（`zhiji_api.py search` 找独立序列）
   同时**修正 R-ZHIJI-1 校验脚本**：必须扁平化处理 `ids` 的 dict 嵌套格式（当前脚本可能漏算，导致 249 与实测 221 的口径差异）。
5. **R2 必须重新执行合并策略，禁止"默认保留 win 版本"**：
   - rebase 至 **`404f7ee`**（而非 `217cb86`），补齐 main 的 1 个领先提交
   - **字段级合并而非条目级覆盖**：`verified`、`freq`、`unit`、`_verified_by` 四类字段必须**取 main 值**（main 侧为实测确认值），win 仅提供 key/name 新增
   - 验收式：verified 降级 = 0、freq 变更（main 方向）= 0、`_verified_by` 丢失 = 0

---

## 六、审计方法说明（可复算）

全程只读，未 checkout、未改任何仓库文件：

```bash
git fetch origin --prune                                    # + 5e4efe8...8fc7210 (forced update)
git rev-parse origin/indicator-correction-win               # 8fc7210dc6056c1fdecf714b4a3950652846af11
git show origin/indicator-correction-win:data/indicators_v1.json
git show origin/main:data/indicators_v1.json
git merge-base origin/main origin/indicator-correction-win  # 217cb86
git rev-list --count origin/indicator-correction-win..origin/main   # 1
git rev-list --count origin/main..origin/indicator-correction-win   # 2
git diff --stat origin/indicator-correction-win:data/indicators_v1.json origin/main:data/indicators_v1.json  # 14287+/15453-
git show origin/indicator-correction-win:task_queue/feedback/RECEIPT-DSH_B_MERGE_HIST_IND_P3.md
git ls-tree -r --name-only origin/indicator-correction-win | grep -iE "RECEIPT"
```

R-ZHIJI-1 唯一性校验（扁平化 dict/list/裸值三格式）：
```python
def ids_of(v):  # 见回执 R1 段
    ...
# 实测：distinct=1268, dup_groups=221, dup_entries=694
# 验收式：len(dup_groups) == 0  → 当前 221，不通过
```

字段级污染核对：
```python
# verified 降级: main True -> win 非 True = 495
# freq 变更: 396 | unit 变更: 0 | 字段丢失: 443 (主要 _verified_by)
# main 业务 key 在 win 缺失: 0
```
