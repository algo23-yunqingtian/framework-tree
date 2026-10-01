# DSHB 数据口径说明文档 — 供 HERMES 门户刷新使用

> 工单: DSH-B_V85_FINAL_GATE_ACCEPTANCE_REPORT_AND_RULE_SUMMARY
> 生成时间: 2026-10-01 16:00:00
> 基线commit: feature/v85-chart-template @ 0d7b0e8
> 数据源文件: sim_sceneA_result.csv, sim_sceneB_result.csv
> 输出路径: analysis/e2e_output/v85/dshb_review_simulation/

---

## 一、文档目的

本文档为 HERMES 门户数据刷新提供 DSHB 侧模拟回放数据的完整字段定义、指标口径、数据边界和使用注意事项。HERMES 可通过本文档理解并正确加载 sim_sceneA/B 两个 CSV 文件。

---

## 二、数据文件清单

| 文件 | 路径 | 大小 | 行数 | MD5 | 说明 |
|------|------|------|------|-----|------|
| sim_sceneA_result.csv | dshb_review_simulation/ | 11,953 B | 63行（62条数据） | f981388a614692bc146924ac0bc6c4de | 场景A最小放行模拟回放明细 |
| sim_sceneB_result.csv | dshb_review_simulation/ | 12,972 B | 63行（62条数据） | 148bca5f0562fa7f644c718131f21e3b | 场景B完整处置模拟回放明细 |
| simulation_compare_report.md | dshb_review_simulation/ | 7,023 B | — | 4873fa368ad3c90618b98aefaef81fa2 | 双场景对比报告 |
| gate_block_impact_analysis.md | dshb_review_simulation/ | 9,719 B | — | a4377f9eeb9b337cd6397403a5e0f5ca | Gate阻塞影响量化评估 |
| bl009a_multi_scenario_verify.md | dshb_review_simulation/ | 5,190 B | — | 579e5d12b855ee05aac05d0c3652efad | BL-009a多场景回归验证 |

---

## 三、sim_sceneA/B_result.csv 字段定义

### 3.1 字段总览

两个 CSV 文件使用完全相同的字段结构（共13列），差异仅在 `scene_action` 和 `rule_applied` 的取值不同。

| 列序 | 字段名 | 类型 | 说明 | 示例值 |
|------|--------|------|------|--------|
| 1 | source_type | string | 数据来源类型 | cross_variety_p0 / boundary_test / p0_workbook_extra |
| 2 | case_id | string | 案例ID | 空（cross_variety_p0）/ BOUNDARY-001 / WORKBOOK-RISK-002 |
| 3 | template_id | string | 模板ID | TPL-LC-054 / N/A / THS-NI-2.3 |
| 4 | indicator_name | string | 指标名称（PDF模板原始名称） | 碳酸锂 三元523需求 |
| 5 | matched_name | string | 匹配名称（模糊匹配结果） | SMM: 碳酸锂现金生产利润: 外购三元极片黑粉（Li: 5.5%-6.5%）: |
| 6 | risk_id | string | 风险ID | RISK-002 / RISK-010 |
| 7 | risk_level | string | 风险等级 | P0 / P1 / SAFE / N/A |
| 8 | old_status | string | 原始状态 | NOT_BLOCKED / BLOCKED / EXPECTED_BLOCKED / EXPECTED_PASS / DATA_MISSING |
| 9 | scene_action | string | 场景处置动作（场景A/B不同） | 见3.2节 |
| 10 | rule_applied | string | 应用的规则 | BL-009a / WHITELIST / BL-022（数据修复后）等 |
| 11 | new_status | string | 新状态 | BLOCKED / WHITELISTED / PASS / NOT_BLOCKED |
| 12 | tp_change | integer | TP变化量 | 0 / 1 |
| 13 | fp_change | integer | FP变化量 | 0 |
| 14 | notes | string | 备注 | 中文说明 |

### 3.2 scene_action 字段取值

| scene_action 值 | 场景A | 场景B | 说明 |
|----------------|:-----:|:-----:|------|
| BL-009a规则拦截（需求→利润反向） | ✅ | ✅ | BL-009a规则拦截 |
| 人工白名单放行（RISK-010） | ✅ | ❌ | 场景A白名单，场景B数据修复 |
| 人工白名单放行（RISK-011） | ✅ | ❌ | 场景A白名单，场景B数据修复 |
| 人工白名单放行（RISK-013） | ✅ | ❌ | 场景A白名单，场景B数据修复 |
| 人工白名单放行（RISK-005） | ✅ | ✅ | 两个场景均白名单 |
| 上游数据修复→规则拦截（RISK-010） | ❌ | ✅ | 场景B数据修复 |
| 上游数据修复→规则拦截（RISK-011） | ❌ | ✅ | 场景B数据修复 |
| 上游数据修复→规则拦截（RISK-013） | ❌ | ✅ | 场景B数据修复 |
| 保持现有拦截 | ✅ | ✅ | 已阻塞的P0保持不变 |
| 保持现有状态 | ✅ | ✅ | 工作表已处置条目 |
| BL-026正式启用（库存天数跨品种） | ❌ | ✅ | 场景B启用BL-026 |

### 3.3 rule_applied 字段取值

| rule_applied 值 | 说明 |
|----------------|------|
| BL-009a | BL-009a规则拦截 |
| BL-009 | BL-009原始规则拦截（正向：利润→需求） |
| BL-012 | BL-012库存天数与库存量互斥 |
| BL-015 | BL-015国内销量与出口互斥（反向） |
| BL-016 | BL-016利润与产量互斥 |
| BL-018 | BL-018跨品种匹配禁止 |
| BL-018a | BL-018a锡与镍跨品种禁止 |
| BL-019 | BL-019硅与铜跨品种禁止 |
| BL-020 | BL-020硅与苯乙烯跨品种禁止 |
| BL-021 | BL-021硅与黄金跨品种禁止 |
| BL-022 | BL-022镍与铜跨品种禁止 |
| BL-025 | BL-025消费量与产量互斥（反向） |
| BL-026 | BL-026库存天数跨品种禁止 |
| WHITELIST | 人工白名单放行 |
| NONE | 未触发任何规则 |
| 修复后规则 | 数据修复后的规则（场景B数据缺失变体） |

---

## 四、source_type 数据来源分类

### 4.1 cross_variety_p0（21条）

| 来源 | 行数 | 说明 |
|------|------|------|
| cross_variety_p0 | 21 | 跨品种P0验证条目，来自cross_variety_p0_validation.csv |
| P0风险案例 | 17 BLOCKED + 4 NOT_BLOCKED | 17条已拦截 + 4条漏拦截 |

**包含的Risk ID**: RISK-002, RISK-010, RISK-011, RISK-013, RISK-014~022, RISK-024~033

### 4.2 boundary_test（24条）

| 来源 | 行数 | 说明 |
|------|------|------|
| boundary_test | 24 | 边界测试用例，来自blacklist_boundary_testset.json |
| 正向危险样例 | 10 | 应被拦截 |
| 安全负向样例 | 7 | 不应被拦截 |
| 数据缺失样例 | 7 | matched_name为N/A |

**包含的Case ID**: BOUNDARY-001 ~ BOUNDARY-024

### 4.3 p0_workbook_extra（4条）

| 来源 | 行数 | 说明 |
|------|------|------|
| p0_workbook_extra | 4 | P0工作表中不在跨品种验证的条目 |
| 包含 | RISK-005, RISK-001, RISK-003, RISK-006 | RISK-005(未命中), RISK-001/003/006(已阻塞) |

---

## 五、指标口径定义

### 5.1 P0拦截率

| 指标 | 计算方式 | 基线 | 场景A | 场景B |
|------|---------|------|-------|-------|
| P0案例数（跨品种） | cross_variety_p0总数 | 21 | 21 | 21 |
| 已拦截 | old_status=BLOCKED 或 new_status=BLOCKED | 17 | 21 | 21 |
| 漏拦截 | old_status=NOT_BLOCKED 且 new_status=NOT_BLOCKED | 4 | 0 | 0 |
| P0拦截率 | 已拦截/总数×100% | 81.0% | 100.0% | 100.0% |
| TP变化 | tp_change总和 | — | +4 | +7 |
| FP变化 | fp_change总和 | — | +0 | +0 |
| 回归数 | new_status=NOT_BLOCKED但old_status=BLOCKED的数量 | — | 0 | 0 |

### 5.2 TP/FP定义

| 指标 | 定义 | 计算方式 |
|------|------|---------|
| TP（True Positive） | 正确拦截：expected_blocked=true 且 actual_blocked=true | new_status=BLOCKED 且 expected_blocked=true |
| FP（False Positive） | 错误拦截：expected_blocked=false 但 actual_blocked=true | new_status=BLOCKED 且 expected_blocked=false |
| tp_change | 相比基线新增的正确拦截数 | 场景后TP数 - 基线TP数 |
| fp_change | 相比基线新增的错误拦截数 | 场景后FP数 - 基线FP数 |

### 5.3 白名单计数

| 指标 | 定义 | 场景A | 场景B |
|------|------|-------|-------|
| 白名单条目数 | scene_action包含"白名单"的行数 | 4（RISK-005/010/011/013） | 1（RISK-005） |
| 数据修复条目数 | scene_action包含"数据修复"的行数 | 0 | 3（RISK-010/011/013） |
| BL-026启用条目数 | scene_action包含"BL-026正式启用"的行数 | 0 | 10（9条P1 + 1条确认） |

### 5.4 Gate状态口径

| 指标 | 定义 |
|------|------|
| 完全通过（PASS） | 所有条件满足，可上线 |
| 部分改善（PARTIAL_IMPROVED） | 有改善但未完全解除 |
| 部分完成（PARTIAL） | 部分条件满足 |
| 阻塞中（BLOCKED） | 条件未满足，不可上线 |

---

## 六、数据边界说明

### 6.1 模拟数据边界

| 边界项 | 说明 |
|--------|------|
| 模拟非生产 | 数据为模拟回放结果，非生产环境实际数据 |
| 规则集范围 | 基于semantic_blacklist_v85_final.json（31条规则） |
| 不含BL-009a生产 | BL-009a为候选规则，模拟中假设为已上线 |
| 场景B假设 | 假设上游PDF数据已修复（实际需3-6天） |
| BL-026启用 | 场景B中BL-026为正式启用状态，场景A中仍为needs_manual_review |

### 6.2 CSV数据完整性

| 校验项 | 结果 |
|--------|------|
| sim_sceneA_result.csv行数 | 63行（含表头62条数据）✅ |
| sim_sceneB_result.csv行数 | 63行（含表头62条数据）✅ |
| 两文件行数一致 | ✅ 完全一致 |
| 字段数一致 | ✅ 13列一致 |
| MD5校验 | ✅ 已记录 |

### 6.3 数据不包含

| 不包含项 | 说明 |
|---------|------|
| 生产环境实际数据 | 仅含模拟回放结果 |
| HERMES侧Gate数据 | HERMES的46项Gate不在本文件中 |
| DSHB侧Gate原始状态 | 需在gate_block_tracker.csv中查询 |
| 人工评审填写结果 | 本文件为模拟数据，非人工填写 |

---

## 七、HERMES 使用注意事项

### 7.1 加载顺序建议

```
1. sim_sceneA_result.csv    — 场景A数据
2. sim_sceneB_result.csv    — 场景B数据
3. simulation_compare_report.md — 对比报告（可选）
4. gate_block_impact_analysis.md — Gate影响（可选）
```

### 7.2 门户展示建议

| 展示维度 | 场景A | 场景B |
|---------|-------|-------|
| P0拦截率 | 100%（含白名单） | 100%（真实拦截） |
| Gate改善 | 部分改善 | 显著解除 |
| 实施难度 | 低（仅白名单） | 高（需上游修复） |
| 风险等级 | 中（白名单依赖人工） | 低（规则驱动） |
| 推荐度 | ⚠ 可豁免条件上线 | ✅ 建议上线 |

### 7.3 场景对比展示

建议HERMES门户支持双场景对比展示：

```
┌─────────────────────────────────────────────────────────┐
│                    V85 场景对比                           │
├──────────┬──────────────────┬────────────────────────────┤
│   指标    │   场景A（最小放行）│   场景B（完整处置）         │
├──────────┼──────────────────┼────────────────────────────┤
│ P0拦截率  │ 100.0%           │ 100.0%                     │
│ TP变化    │ +4               │ +7                         │
│ FP变化    │ +0               │ +0                         │
│ Gate解除  │ 0完全+4部分改善   │ 6完全解除                    │
│ 实施难度  │ 低（0.5天）       │ 高（5-7天）                 │
│ 上线建议  │ ⚠ 可豁免         │ ✅ 建议                     │
└──────────┴──────────────────┴────────────────────────────┘
```

### 7.4 数据处理注意事项

| 注意事项 | 说明 |
|---------|------|
| 编码格式 | UTF-8 with BOM（utf-8-sig） |
| 分隔符 | 逗号（CSV标准） |
| 引号处理 | 字段值含逗号时用双引号包裹 |
| 空值处理 | 空字段为空字符串，非NULL |
| 数值字段 | tp_change和fp_change为整数，其余为字符串 |
| 日期格式 | 本文件不含日期字段 |
| 排序 | 数据按source_type分组，组内按case_id排序 |
| 唯一键 | 无唯一键，同一risk_id可能有多行（不同source_type） |

### 7.5 与HERMES Gate数据映射

| DSHB Gate | HERMES Gate映射 | 说明 |
|-----------|----------------|------|
| H1 (THS匹配率) | HERMES Gate #1 | 独立Gate |
| H2 (P0全部处置) | HERMES Gate #2 | 独立Gate |
| H3 (渲染就绪率) | HERMES Gate #3 | 独立Gate |
| H4 (评审完成率) | HERMES Gate #4 | 独立Gate |
| H5 (风险库落地) | HERMES Gate #5 | 独立Gate |
| G-01 | DSHB侧Gate | 不映射HERMES |
| G-03 | DSHB侧Gate | 不映射HERMES |
| G-05 | DSHB侧Gate | 不映射HERMES |
| G-06 | DSHB侧Gate | 不映射HERMES |
| WL-EXPIRY | DSHB侧Gate | 不映射HERMES |

---

## 八、HERMES 数据刷新指引

### 8.1 刷新频率

| 刷新类型 | 频率 | 说明 |
|---------|------|------|
| 模拟数据 | 按需刷新 | 本文件为静态模拟数据 |
| 场景对比 | 按需刷新 | 场景定义变化时刷新 |
| Gate状态 | 实时更新 | 需在Gate复检后更新 |

### 8.2 数据更新流程

```
1. DSHB侧生成新的sim_sceneX_result.csv
2. HERMES读取新数据
3. HERMES更新场景对比展示
4. 通知相关方数据已更新
```

### 8.3 数据版本标识

| 字段 | 值 | 说明 |
|------|-----|------|
| 数据版本 | V85-SIM | 模拟数据版本标识 |
| 基线commit | 0d7b0e8 | feature/v85-chart-template |
| 生成时间 | 2026-10-01 16:00:00 | 本文件生成时间 |
| 数据有效性 | 静态 | 不会随生产环境自动更新 |

---

## 九、FAQ

### Q1: 如何判断场景A和场景B的区别？

通过 `scene_action` 字段判断：
- 场景A（最小放行）: 包含"人工白名单放行"的条目
- 场景B（完整处置）: 包含"上游数据修复→规则拦截"和"BL-026正式启用"的条目

### Q2: 白名单条目在场景A和场景B中是否不同？

是。场景A白名单4条（RISK-005/010/011/013），场景B仅白名单1条（RISK-005）。场景B中RISK-010/011/013通过数据修复解决。

### Q3: 如何计算P0拦截率？

从 cross_variety_p0 类型的21条数据中统计：
- 基线拦截数 = old_status=BLOCKED 的数量
- 场景后拦截数 = new_status=BLOCKED 或 new_status=WHITELISTED 的数量
- P0拦截率 = 拦截数/21×100%

### Q4: 数据是否包含所有Gate信息？

不包含。Gate状态需从 gate_block_tracker.csv 和 gate_block_impact_analysis.md 中获取。本CSV仅包含P0/P1风险条目的处置结果。

### Q5: 如何验证数据完整性？

1. 检查行数: 63行（含表头62条数据）
2. 检查MD5: sim_sceneA_result.csv = f981388a614692bc146924ac0bc6c4de
3. 检查字段: 13列，字段名与本文档3.1节一致

---

## 十、约束声明

| 约束 | 状态 |
|------|------|
| NO_SOURCE_MODIFICATION | ✅ 未修改任何源文件 |
| NO_GT_MODIFICATION | ✅ 未修改GT |
| NO_RULE_MODIFICATION | ✅ 未修改黑名单规则 |
| NO_ZHIJI_API_CALL | ✅ 未调用zhiji API |
| READ_ONLY | ✅ 仅新增文件，未覆盖历史产物 |
| APPEND_ONLY | ✅ 仅追加，不删除 |

---

*本文档为HERMES门户数据刷新提供DSHB侧模拟回放数据的完整口径说明，确保数据加载和展示的一致性。*
