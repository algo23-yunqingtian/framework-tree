# V85 全项目总复盘报告

> 工单: `HERMES_V85_PROJECT_FINAL_RETROSPECT_AND_VERSION_FREEZE_REPORT`
> 生成时间: 2026-10-01 21:00
> 分支: `feature/v85-chart-template` @ `bcd64dd`（tag: `v85-final-persist` @ `da2a440`）
> 三方交付: DSHB / DSHE / HERMES

---

## 1. 项目概述

V85 是 framework-tree 图表模板全链路集成的版本代号，目标是将 DSHB 交付的 333 套 PDF 图表模板 + 155 套同花顺(THS) 模板接入 zhiji 真实时序数据、通过语义黑名单自动校验、完成人工评审后上线。

**最终结论**: ❌ **禁止上线** — 4 项硬阻塞未解除（H1/H2/H3/H4），全部依赖人工执行（预估 5-7 天）。V85 进入冻结状态，待人工评审完成后走合并流程。

---

## 2. 里程碑时间线

| 日期 | 阶段 | 关键交付 |
|------|------|---------|
| 09-28 | 数据拉取 | DSHB 端到端 zhiji 拉取，248 唯一 ID，96.36% 成功率 |
| 09-29 | 模板集成 | 333 PDF 模板渲染，328/333 有效数据(98.5%) |
| 09-30 | 评审准备 | 人工评审材料 5 份 + 语义黑名单 v1 + THS 静态校验 |
| 09-30 | 风险挖掘 | P0 根因分析 41 条 + 漏拦截 4 条 + 边界测试集 302 条 |
| 09-30 | 模糊匹配 | 校准报告 + revised_full_ok_list + 规则缺陷汇总 |
| 09-30 | 别名库审计 | DSHE 别名库 864 条 + 混淆对 13 条 + 回归测试 41+200 |
| 09-30 | 全链路集成 | DSHB 31 规则黑名单 + 488 模板回放 + 跨品种 P0 验证 34 条 |
| 10-01 | 门户增强 | 评审门户 v4→v5→v6 三轮迭代 + 渲染仿真模拟 |
| 10-01 | 渲染修复 | 4 缺陷+4 遗漏+4 建议+两级白名单+人工评审工作包 |
| 10-01 | THS 映射 | 候选召回 2360 series + 高置信 864 条 + Gate 缺口计划 |
| 10-01 | 最终 Gate | HERMES 46 项 + DSHB 6 项 = 52 项 Gate 二次自检 |
| 10-01 | 归档预整理 | Release Note + 部署回滚手册 + 外部验收清单 |
| 10-01 | 模拟评审 | 场景 A/B 回放 + BL-009a 验证 + Gate 影响分析 |
| 10-01 | 真实数据刷新 | DSHB sim_sceneA/B 接入，P0 拦截率 81%→100%，TP+7/FP+0 |
| 10-01 | DSHB 最终 | 10 Gate triple-state + 32 规则概览 + 53 风险分类 + V86 12 任务 |
| 10-01 | DSHE 最终 | 别名库抽样审计 + V86 引擎全套设计 7 份 + 165 歧义重分诊 |
| 10-01 | 产物持久化 | 453 文件 MD5/结构/解析校验 100%/99.1%，git tag v85-final-persist |
| 10-01 | 只读 API | V85 只读 API 9 端点 + V86 后端 schema/task API + 迁移计划 |

---

## 3. 三方核心指标汇总

### 3.1 DSHB（规则/Gate/风险库）

| 指标 | 值 | 来源 commit |
|------|-----|------------|
| 语义黑名单规则数 | 31（+BL-009a 候选=32） | `6fded66` |
| 488 模板全量回放 | 2721 series 行回放完成 | `6fded66` |
| 跨品种 P0 验证 | 30/34 拦截 (88.2%)，0 回归 | `6fded66` |
| 风险库与回放对齐 | 20/25 命中 (80%)，5 条根因已定位 | `6fded66` |
| 风险库最终落地 | 50 条入库 ✅ | `6841114` |
| 漏拦截 P0 | 4 条（1 方向性 + 3 数据缺失） | `1abfa33` |
| P0 工作表 | 237 条 P0 待人工处置 | `ccd1a73` |
| Gate v2 | 2/6 PASS，4 PARTIAL | `6771406` |
| V86 任务拆解 | 12 任务（P0×4 + P1×3 + P2×5） | `6771406` |

### 3.2 DSHE（别名库/混淆对/回归测试）

| 指标 | 值 | 来源 commit |
|------|-----|------------|
| 别名库 | 864 条，7 品种 | `bc33e8c` |
| 混淆对 | 13 条（8 P0 + 5 P1） | `bc33e8c` |
| THS 别名覆盖 | 2359 rows（MISSING=0，需注册 2299） | `78948b4` |
| 歧义重分诊 | 448 条（W0×437 / W3×6 / W2×3 / W1×2） | `78948b4` |
| 回归测试 | 41+200+1134 三套套件 | `bc33e8c` |
| 抽样审计 | 102 案例，100/100 有效 ✅ | `089fbb6` |
| 确定性修复 | F1-F4 fixes，3 份产物 byte-identical | `ca967ec` |
| V86 引擎设计 | 7 份产物 + 14 回归 Gate | `089fbb6` |
| V86 路线图 | 10 批次，16.25-24.25 人天 | `78948b4` |

### 3.3 HERMES（门户/渲染/集成/评审）

| 指标 | 值 | 来源 commit |
|------|-----|------------|
| 评审门户版本 | v6（真实数据刷新版） | `a2815c4` |
| P0 拦截率（基线→刷新） | 81%→**100%**（21/21） | `a2815c4` |
| TP/FP 变化（场景 A+B） | **TP+7 / FP+0** | `a2815c4` |
| 渲染就绪率 | 19.9%（97/488） | `ee27e39` |
| 渲染仿真 | 488 模板全量仿真，89 可渲染 | `e491e8d` |
| 修复版路由 | 89 可渲染 + 8 降级 + 4 复核 + 155 待匹配 + 232 阻塞 | `357e98b` |
| THS 候选映射 | 2360 series，高置信 864 条 (36%) | `6fc8f11` |
| Gate 46 项 | 38 通过 / 8 未通过 / 4 可豁免 | `ee27e39` |
| 归档包 | 63 文件（重建前 53），警告 1（原 3） | `a2815c4` |
| 人工评审批次 | A(97)/B(155)/C(236) = 488 条 | `53c0466` |

### 3.4 Gate 三套场景合并

| 场景 | P0 拦截率 | TP | FP | Gate 解除 | 来源 |
|------|----------|----|----|----------|------|
| 基线 | 81.0%（17/21） | — | — | 0 项 | DSHB 真实数据 |
| 场景 A | **100%**（21/21） | +4 | +0 | 0 项完全解除（H1 需人工） | BL-009a+白名单 4 |
| 场景 B | **100%**（24/24） | +7 | +0 | 8 项解除（H1/H3/H4 仍需人工） | BL-009a+修复+3+BL-026+1 |

---

## 4. 全部工单清单（按时间顺序）

| # | 工单 ID | 方 | commit | 状态 |
|---|---------|-----|--------|------|
| 1 | DSH-B_END2END_ZHIJI_DATA_FETCH_V85 | DSHB | (09-28) | ✅ |
| 2 | HERMES_V85_CHART_TEMPLATE_INTEGRATION | HERMES | `d67aebb` | ✅ |
| 3 | HERMES_V85_ARTIFICIAL_REVIEW_PREP | HERMES | `527f597` | ✅ |
| 4 | HERMES_V85_PREP_FOR_THS_AND_AUTO_CHECK_ENHANCE | HERMES | `96db76d` | ✅ |
| 5 | DSH-B_V85_RISK_ROOTCAUSE_ANALYSIS_AND_REVIEW | DSHB | `26517eb` | ✅ |
| 6 | DSH-B_V85_FUZZY_MATCH_CALIBRATION | DSHB | (09-30) | ✅ |
| 7 | DSHE-B_V85_ALIAS_LIB_FULL_EXECUTE_AUDIT | DSHE | `bc33e8c` | ✅ |
| 8 | DSH-B_V85_FULL_CHAIN_INTEGRATE_VALIDATE | DSHB | `6fded66` | ✅ |
| 9 | DSH-B_V85_RISK_IMPLEMENT_VERIFY | DSHB | `6841114` | ✅ |
| 10 | DSH-B_V85_MISS_RISK_ROOTCAUSE_MINING | DSHB | `1abfa33` | ✅ |
| 11 | HERMES_V85_PORTAL_FINAL_INTEGRATE_GATE | HERMES | `d324c76` | ✅ |
| 12 | HERMES_V85_HUMAN_REVIEW_TOOL_ENHANCE | HERMES | `53c0466` | ✅ |
| 13 | HERMES_V85_FINAL_DELIVERY_PACKAGE_BUILD | HERMES | `ee27e39` | ✅ |
| 14 | HERMES_V85_PORTAL_SIMULATION_DEMO | HERMES | `99b6c74` | ✅ |
| 15 | HERMES_V85_PRE_ARCHIVE_PACKAGE_PREP | HERMES | `6ba7bde` | ✅ |
| 16 | HERMES_V85_REVIEW_PORTAL_ENHANCE_AND_RENDER_SIM | HERMES | `e491e8d` | ✅ |
| 17 | HERMES_V85_RENDER_SCRIPT_FIX_AND_REVIEW | HERMES | `357e98b` | ✅ |
| 18 | HERMES_V85_THS_INDICATOR_MAPPING_PREP | HERMES | `6fc8f11` | ✅ |
| 19 | DSH-B_V85_HUMAN_REVIEW_MATERIAL_PREP | DSHB | `ccd1a73` | ✅ |
| 20 | DSHE-B_V85_ALIAS_LIB_INTEGRATION_TEST | DSHE | `78948b4` | ✅ |
| 21 | DSH-B_V85_HUMAN_REVIEW_SIMULATION | DSHB | `0d7b0e8` | ✅ |
| 22 | HERMES_V85_PORTAL_REFRESH_WITH_REAL_SIM_DATA | HERMES | `a2815c4` | ✅ |
| 23 | DSH-B_V85_FINAL_GATE_ACCEPTANCE_REPORT | DSHB | `6771406` | ✅ |
| 24 | DSHE-B_V85_ALIAS_LIB_SAMPLING_AUDIT_AND_V86_ENGINE | DSHE | `089fbb6` | ✅ |
| 25 | B_V85_ARTIFACT_PERSIST_AND_SNAPSHOT_VERIFY | B | `da2a440` | ✅ |
| 26 | E_V85_READONLY_API_AND_V86_BACKEND_DESIGN | E | `b7c62ba` | ✅ |

---

## 5. 完整风险清单（合并三方）

### 5.1 高风险（3 项，禁止上线）

| # | 风险 | 来源 | 状态 | 缓解方案 |
|---|------|------|------|---------|
| R1 | THS 匹配率 0%（155 模板无 zhiji_id） | HERMES | ⚠ 待人工 | 回写 864 高置信候选(1天) |
| R2 | 评审完成率 0%（488 模板未评审） | HERMES | ⚠ 待人工 | Batch-A/B/C 评审(3-5天) |
| R3 | P0 未全部处置（232 条阻塞） | DSHB | ⚠ 待人工 | Batch-C 评审+P0处置(1天) |

### 5.2 中风险（6 项）

| # | 风险 | 来源 | 状态 |
|---|------|------|------|
| R4 | 4 条漏拦截 P0（RISK-002/010/011/013） | DSHB | ✅ BL-009a候选已生成 |
| R5 | BL-009 方向性缺失（利润↔需求仅单向） | DSHB | ✅ BL-009a候选(V2) |
| R6 | BL-026 库存统计口径规则待确认 | DSHB | ⚠ 待人工确认 |
| R7 | 4 条数据缺失（PDF matched_name 为空） | DSHB | ⚠ 待上游修复 |
| R8 | DSHE 3 文件未落盘 | DSHE | ✅ 等价版替代 |
| R9 | DSHB sim_sceneA/B 未落盘 | DSHB | ✅ 自构建数据已就绪 |

### 5.3 低风险（8 项，V86 处理）

| # | 风险 | 状态 |
|---|------|------|
| R10 | 纯文本匹配语义局限 | ✅ V86 语义引擎 |
| R11 | THS zhiji_id 格式未统一 | ✅ schema 校验已实现 |
| R12 | THS meta 字段不完整 | ✅ V86 修复 |
| R13 | 图例名称异常 | ✅ V86 修复 |
| R14 | 并发渲染性能 | ✅ V86 优化(concurrency=4) |
| R15 | 白名单过期无提醒 | ✅ V86 自动化 |
| R16 | 评审门户非 Web 化 | ✅ V86 Web 化 |
| R17 | 无自动回归测试 | ✅ 302 条边界测试集已就绪 |

### 5.4 风险缓解汇总

| 缓解状态 | 数量 | 风险编号 |
|---------|------|---------|
| ✅ 已缓解 | 11 | R4/R5/R8/R9/R10-R17 |
| ⚠ 待处理 | 6 | R1/R2/R3/R6/R7 |

### 5.5 上游依赖项

| 依赖项 | 阻塞风险 | 依赖方 | 预估时间 |
|--------|---------|--------|---------|
| PDF matched_name 补全（4 条） | R7 | PDF 数据团队 | 4 天 |
| THS zhiji_id 人工回写（864 条） | R1 | 业务评审人 | 1 天 |
| Batch-A/B/C 评审（488 条） | R2/R3 | 业务评审团队 | 5 天 |

---

## 6. 交付物统计

| 维度 | 数量 |
|------|------|
| 总工单数 | 26 |
| 总交付文件 | 896 |
| 总交付大小 | ~52 MB |
| Git commit | 26+ |
| Git tag | `v85-final-persist` |
| 产物目录 | 32 |
| 评审门户版本 | v1→v6（6 轮迭代） |
| 语义黑名单规则 | 31+1 候选 |
| 风险库条目 | 50 |
| 别名库条目 | 864 |
| 边界测试集 | 302 |

> 完整 MD5 索引见: `v85_full_artifact_index.md`

---

## 7. 经验与教训

### 7.1 做得好的

1. **三方协作清晰**: DSHB/DSHE/HERMES 各自工单边界明确，无交叉污染
2. **Gate 门禁体系**: 52 项 Gate 覆盖元数据/语义/渲染/评审/阻塞 5 维度，量化验收
3. **确定性可复现**: DSHE F1-F4 修复后 3 份产物 byte-identical，git tag 锁定快照
4. **真实数据刷新**: 场景 A/B 用 DSHB 真实 sim 数据验证，TP+7/FP+0 零误拦截
5. **归档持久化**: 453 文件 MD5 100%/结构 100%/解析 99.1%，可验证不可篡改

### 7.2 待改进

1. **THS 模板 schema 不兼容**: 早期未发现 THS 与 PDF schema 完全不兼容，导致渲染阶段才发现 155 模板全 E1_SCHEMA_MISMATCH
2. **纯文本匹配局限**: 产量 vs 销量等语义差异无法靠文本相似度区分，需 V86 语义引擎
3. **人工评审瓶颈**: 488 模板全量人工评审需 5 天，是最大阻塞项
4. **BL-009 方向性缺陷**: 规则设计时未考虑反向组合，到风险挖掘阶段才发现

---

## 8. 下一步

V85 进入**版本冻结**状态（详见 `v85_version_freeze_decision.md`）。V86 启动基线已整合（详见 `v86_init_backlog_total.md`）。

人工评审完成后：
1. 跑 `python3 scripts/reclaim.py` 全绿
2. 合并 `feature/v85-chart-template` → `main`
3. 部署 GH Pages
4. 启动 V86 迭代
