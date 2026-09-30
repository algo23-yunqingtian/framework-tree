# alias_lib_import_guide.md · 别名库落地导入实施方案

| 项目 | 值 |
|---|---|
| 任务 | DSHE-B_V85_ALIAS_LIB_FULL_EXECUTE_AUDIT_AND_REGRESSION_TEST |
| 数据来源 | `_stats_new.json` / `quality_regression_result.json` / `indicator_alias_library.csv` |
| 目标文件 | `data/indicators_v1.json`（**只读，本任务不修改**） |
| 目标键数 | indicators_v1 共 **1658** 键，别名库已覆盖 **1652** |
| 数据边界 | 本文件为**导入方案**，不执行写入；不修改任何源数据；不调用 zhiji API |

---

## 1. 导入分层（四层，按可入库性排序）

| 层 | 行数 | 占比 | relation | 入库方式 | 可否自动化 |
|---|---|---|---|---|---|
| **B1 = W1 可靠同义** | **2502** | 53.9% | synonym_merge | **批量自动入库** | ✅ |
| **B2 = W2 存疑** | **369** | 7.9% | canonical_conflict 165 + synonym_with_confusable_neighbor 204 | 人工复核后入库 | ❌ |
| **B3 = W3 明确错误** | **38** | 0.8% | confusable_warn 27 + synonym_with_confusable_neighbor 11 | **禁止入库**，转黑名单候选 | ❌（反向） |
| **B4 = W0 待注册** | **1734** | 37.3% | unregistered | 需先补 canonical 注册 | ⚠️ 半自动 |

**优先级总排序**：B1（收益最大、风险最低）→ B2（人工瓶颈，369 条）→ B4（依赖 canonical 注册）→ B3（不进库，走黑名单通道）。

---

## 2. B1 批量导入方案（2502 行）

### 2.1 前置校验（8 项门禁）

导入前必须全部通过：

| # | 门禁 | 判定 | 失败动作 |
|---|---|---|---|
| G1 | relation == `synonym_merge` | 严格相等 | 整批中止 |
| G2 | review_flag == `auto` | 严格相等 | 整批中止 |
| G3 | `canonical_key` 在 indicators_v1 中存在 | 键存在性检查 | 剔除该行，记录日志 |
| G4 | `canonical_key` 非空且非冲突 | 不含 `\|` 分隔符 | 剔除该行 |
| G5 | `blacklist_rule` 为空 | 无黑名单命中 | 整批中止（说明分层逻辑失效） |
| G6 | `risk_case_ids` 为空 | 不关联风险案例 | 剔除该行 |
| G7 | `confusable_neighbor_count` ≤ 2 | 混淆邻居数上限 | 降级至 B2 |
| G8 | `canonical_name` 与 indicators_v1 现有 name 一致 | 名称一致性 | 剔除该行 |

### 2.2 导入结构

`indicators_v1.json` 每个指标条目为字典，别名写入 `aliases` 数组（若无该字段则新建）：

```
{
  "<indicator_key>": {
    "name": "<canonical_name>",
    "unit": "<unit>",
    "variety": "<family>",
    "aliases": ["<alias_norm_1>", "<alias_norm_2>", ...]
  }
}
```

写入规则：
- 别名写入用 `alias_norm`（归一化形态），**不写** `alias_name`（原始形态），保证与匹配链路 `match_norm()` 口径一致；
- 按 canonical_key 聚合，同一 canonical 的多条别名写入同一数组；
- 去重：`alias_norm` 已存在于 `aliases` 中则跳过（幂等）；
- 不覆盖 `name` 字段（canonical 名保持不变）。

### 2.3 回滚

导入前生成快照：

```
cp data/indicators_v1.json data/indicators_v1.json.bak_before_alias_B1_<YYYYMMDD>
```

回滚即恢复快照。本任务 T4 约束禁止修改 `indicators_v1.json`，**快照与写入均需由有写权限的执行方（DSH-B）操作**。

---

## 3. B2 人工复核方案（369 行）

### 3.1 复核拆分

| 子类 | 行数 | 复核焦点 | 预估工时 |
|---|---|---|---|
| `canonical_conflict` | 165 | 多个 canonical 争用同一别名，需判定归属 | 每条约 3 分钟 → 约 8 小时 |
| `synonym_with_confusable_neighbor` | 204 | 同义但邻近存在混淆对，需确认是否会引发跨品种误配 | 每条约 2 分钟 → 约 7 小时 |

### 3.2 复核优先级排序

| 优先级 | 数量 | 特征 |
|---|---|---|
| P0_manual | **192** | 高混淆密度（`confusable_neighbor_count ≥ 3`）或跨品种族 |
| P1_manual | **215** | 混淆邻居 1–2 个，同族内 |

### 3.3 复核分族热点（应优先安排熟悉该品种的人员）

| 品种 | W2 行数 |
|---|---|
| ZN 锌 | 58 |
| NI 镍 | 52 |
| SI 硅 | 45 |
| CU 铜 | 44 |
| PB 铅 | 44 |
| SN 锡 | 39 |
| LI 锂 | 33 |
| AL 铝 | 26 |

该分布与高危混淆对热点（CU~ZN 47 / PB~ZN 35 / AL~CU 31 / NI~SN 27）完全对应，说明**锌/镍/硅/铜/铅**是复核资源投入的重点。

### 3.4 复核产出格式

每条复核结论写入 `data/alias_review_decisions.json`（新建文件）：

```json
[
  {
    "alias_id": "A-00123",
    "alias_norm": "加工费TC",
    "canonical_key": "TC",
    "decision": "merge | reject | reassign",
    "reassign_to": "wr241",
    "reviewer": "<name>",
    "reviewed_at": "2026-10-01",
    "reason": "加工费TC 与 TC加工费 为同一口径的不同表述"
  }
]
```

三态决策：
- `merge`：确认为同义，写入 `aliases`；
- `reject`：确认非同义，剔除并转黑名单候选（进入 B3 通道）；
- `reassign`：归属错误，改绑到 `reassign_to` 指定的 canonical。

---

## 4. B3 黑名单候选方案（38 行）

38 行（confusable_warn 27 + synonym_with_confusable_neighbor 11）**禁止写入 indicators_v1.json**，转为黑名单规则候选：

| 分族 | 行数 |
|---|---|
| LI 锂 | 11 |
| NI 镍 | 8 |
| CU 铜 | 5 |
| SN 锡 | 5 |
| ENTITY | 2 |
| SI 硅 | 2 |
| AL 铝 / LC / ZN / ENTITY\|ZN / 未识别 | 各 1 |

处置：
1. 逐条判定应归入 25 条现有黑名单中的哪条，或新增规则；
2. 新增规则的 pattern 必须 **≥ 2 字**（源脚本 `MIN_PATTERN_LEN=2`，BL-018/019/022 因单字被丢弃）；
3. 若 pattern 是更长 token 的子串（如「产量」⊂「生产量」），必须改为整词边界匹配 —— 本轮 lint 发现 33 条此类风险；
4. 黑名单修改权限在 DSH-B，本任务不修改。

---

## 5. B4 待注册方案（1734 行）

1734 行别名的 canonical 未在 indicators_v1 注册。处置分两步：

### 5.1 第一步：canonical 注册判定

| 判定 | 动作 |
|---|---|
| 别名对应的指标**确实存在**于业务口径 | 由 DSH-B 在 indicators_v1 新增 canonical key，然后走 B1 批量导入 |
| 别名对应的指标**已被废弃/合并** | 剔除该行，记录至 `data/alias_unregistered_rejected.json` |
| 无法判定 | 挂起，等待业务口径确认 |

### 5.2 第二步：注册后复用 B1 流程

新增 canonical 后，这 1734 行自动落入 B1 的 8 项门禁流程。

**预估**：1734 行是别名库中体量最大的待办项（37.3%），但依赖业务口径判定，**不可自动化**。建议按品种分批处理，优先 ZN/SI/SN（别名库中待注册量最大的三个族）。

---

## 6. 批量校验脚本设计

新增 `scripts/validate_alias_import.py`（由 DSH-B 实现，本任务不写入），职责：

| # | 校验项 | 输入 | 输出 |
|---|---|---|---|
| V1 | 别名库 CSV schema 完整性 | `indicator_alias_library.csv` | 缺失列/行数不符则中止 |
| V2 | alias_norm 归一化口径一致性 | 别名库 | 重新执行 `match_norm()` 比对，不一致则中止 |
| V3 | canonical_key 存在性 | 别名库 + indicators_v1.json | 缺失键列表 |
| V4 | 四层分层复算 | 别名库 | 复算 tier 与 `quality_tier` 列比对，不一致则中止 |
| V5 | 门禁 G1–G8 逐项检查 | B1 候选集 | 剔除清单 + 日志 |
| V6 | 幂等性检查 | indicators_v1.json + 别名库 | 已存在别名数 |
| V7 | 回归测试回放 | 41 负向 + 200 正向 | Recall 必须 = 100% |
| V8 | 快照生成 | indicators_v1.json | `.bak_before_alias_B1_<date>` |

**V7 是硬性门禁**：导入后必须重跑 `regression_test_report.md` 的测试集，Recall 下降即回滚。

---

## 7. 增量更新流程（S1–S9）

每次新增指标或修改别名库后执行：

| 步 | 动作 | 门禁 |
|---|---|---|
| S1 | 重新运行 `build_alias_library.py` | exit 0 |
| S2 | 对比新旧别名库行数与 relation 分布 | 行数变化需解释 |
| S3 | 运行 `verify_conclusions.py` 复核核心结论 | 结论A 仍 VERIFIED |
| S4 | 运行 B1 门禁 G1–G8 | 全部通过 |
| S5 | 快照 `indicators_v1.json` | 快照存在 |
| S6 | 写入 B1 别名 | V6 幂等检查 |
| S7 | 运行 `validate_alias_import.py` V1–V8 | 全部通过 |
| S8 | 重跑回归测试 41+200 | **Recall = 100%** |
| S9 | 更新 `STATUS.md` 变更记录 + git commit | 提交成功 |

**任一步骤失败即回滚 S5 快照，不进入下一步。**

---

## 8. 导入前后预期效果

| 指标 | 导入前（本轮实测） | 导入 B1 后（预估） |
|---|---|---|
| 正向集 auto-accept | 60/200 = **30.0%** | 预计 50%+ |
| 正向集 review | 43/200 = 21.5% | 预计 < 15% |
| 正向集 block | 97/200 = 48.5% | 预计 < 35% |
| R-07 别名库直查命中 | **0** | > 0 |
| 41 条风险 Recall | **100.0%** | **必须保持 100.0%** |

**预估的依据**：43 条正向 review 中多数为「品种中性目标」类（`variety_neutral_target_review`），别名库直查命中后应可直接 `accept`。此为预估，非实测 —— 需按 S7/S8 步骤实测确认。

---

## 9. 权限与边界

| 事项 | 本任务（DSH-E） | 需 DSH-B 执行 |
|---|---|---|
| 生成别名库 CSV | ✅ 已完成 | — |
| 生成导入方案 | ✅ 本文件 | — |
| 修改 `indicators_v1.json` | ❌ **禁止**（只读约束） | ✅ |
| 修改黑名单 | ❌ **禁止** | ✅ |
| 生成快照与回滚 | ❌ | ✅ |
| 人工复核决策 | ❌（仅给出排序与格式） | ✅ |
| 回归测试脚本 | ✅ 已完成 | ✅ 导入后重跑 |

---

## 10. 风险与回滚

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| B1 中存在被误分为 W1 的行 | 低（门禁 G1–G8 已过滤） | 引入错误别名 | V7 回归 + S8 Recall 门禁 |
| B2 人工复核积压 | 高（369 条，约 15 小时） | 别名库长期不完整 | 按品种分批，优先 ZN/NI/SI/CU/PB |
| B4 业务口径无法判定 | 高（1734 条） | 37.3% 别名库闲置 | 按族分批，接受长期挂起 |
| 导入后召回率下降 | 低 | 风险案例漏放 | **强制回滚**，V7/S8 为硬门禁 |
| 别名写入覆盖 canonical name | 极低（写入 aliases 数组，不动 name） | 指标语义变更 | 写入代码审查 |
| 单字 pattern 进入黑名单 | 中（B3 有 38 行） | 大面积误拦 | pattern ≥ 2 字硬校验 |

---

## 11. 局限

1. **B1 导入效果为预估**：30.0% → 50%+ 的 auto-accept 提升未经实测，需 S7/S8 验证。
2. **B2 工时时估基于经验值**：每条约 2–3 分钟，未做实际复核计时。
3. **B4 无法给出完成时间**：依赖业务口径判定，1734 条无明确 SLA。
4. **未验证 `aliases` 字段对现有匹配链路的兼容性**：需 DSH-B 确认 `match_norm`/Dice 链路读取 `aliases` 字段的方式。
5. **快照与回滚由 DSH-B 执行**，本任务不产生快照文件。
6. **不含价格数据、策略与 PnL**。
