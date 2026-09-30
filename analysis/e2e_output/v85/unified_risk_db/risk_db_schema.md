# 统一指标风险数据库 — 字段说明文档

**生成时间**: 2026-09-30 21:16:49
**任务**: DSH-B_THS_MATCH_FINALIZE_AND_UNIFY_RISK_DB
**数据库文件**: `unified_indicator_risk_db.csv`
**黑名单版本**: v85-bl021-fixed (25 rules)

---

## 1. 文件结构

| 文件 | 说明 |
|------|------|
| unified_indicator_risk_db.csv | 统一指标风险库，PDF+THS合并，含去重标记 |
| unified_risk_summary_report.md | 风险汇总分析报告 |
| risk_db_schema.md | 本文档 — 字段说明 |
| semantic_blacklist_fixed.json | 修复后黑名单规则（25条） |

## 2. CSV字段定义

| # | 字段名 | 类型 | 说明 |
|---|--------|------|------|
| 1 | id | string | 唯一标识符，格式 `RISK-NNN`，按来源+严重度+模板ID排序 |
| 2 | source | enum | 来源：`PDF`（PDF周报模板）或 `THS`（同花顺模板） |
| 3 | template_id | string | 模板ID，如 `TPL-LC-054` 或 `THS-NI-2.3` |
| 4 | variety | string | 品种代码，如 `AL`(铝), `LC`(碳酸锂), `NI`(镍), `SI`(工业硅), `SN`(锡), `ZN`(锌) |
| 5 | indicator_name | string | 指标名称/系列名 |
| 6 | indicator_title | string | 图表标题或指标标题 |
| 7 | risk_level | enum | 风险等级：`P0`(语义冲突阻塞) / `P1`(高风险人工复核) / `P2`(低风险提示) |
| 8 | risk_category | string | 风险类别：`品种口径`, `供需口径`, `库存口径`, `经济口径`, `贸易口径`, `基本面口径`, `成本口径` |
| 9 | conflict_type | string | 冲突类型：`跨品种`(跨品种匹配) / `口径冲突`(统计口径冲突) / `互斥`(互斥关系) / `警告` |
| 10 | conflict_reason | string | 冲突原因描述，包含规则ID |
| 11 | blacklist_id | string | 触发的黑名单规则ID，如 `BL-005`, `BL-022` |
| 12 | blacklist_rule_name | string | 黑名单规则名称 |
| 13 | matched_name | string | 匹配到的指标名称（知几指标库中的名称） |
| 14 | verify_status | string | 校验状态（THS专有）：`VALID` / `FILLED` / `INVALID` / `MISSING` |
| 15 | is_duplicate | enum | 是否标记为重复：`YES` / `NO` |
| 16 | duplicate_of | string | 重复标记指向的原始条目，格式 `来源:模板ID` |

## 3. 风险等级定义

### P0 — 语义冲突阻塞（Blocking Conflict）
- 不同品种之间的指标匹配（如锡指标匹配到镍数据）
- 统计口径互斥的匹配（如产量匹配到销量）
- 场内库存与非仓单库存互斥匹配
- **影响**: 阻塞图表模板发布，必须人工确认或修正

### P1 — 高风险人工复核（High Risk Review）
- 库存天数与库存量混用（衍生指标与绝对值混用）
- 利润与产量混用（不同维度经济指标）
- **影响**: 不阻塞发布，但建议人工复核确认

### P2 — 低风险提示（Low Risk Warning）
- 价格与利润混用
- 升贴水与价格混用
- 供需平衡与价格混用
- **影响**: 仅做提示，不建议处理

## 4. 数据来源说明

### PDF来源
- 来自 `fuzzy_match_fix/revised_full_ok_list.md`
- 13条因口径冲突被降级的PDF模板条目
- 原始FULL_OK模板327个，降级13个，修订后314个FULL_OK

### THS来源
- 来自 `tonghuashun_recheck_fixed/ths_updated_match_stat.csv`
- 基于BL-021修复版黑名单（移除裸`'金'`关键词）重新扫描
- 20条P0冲突 + 17条P1/P2警告

## 5. 黑名单规则索引

| 规则ID | 规则名称 | 类别 | 严重度 |
|--------|----------|------|--------|
| BL-001 | 产量与消费量互斥 | 供需口径 | P0 |
| BL-002 | 产量与销量互斥 | 供需口径 | P0 |
| BL-003 | 销量与产量互斥 | 供需口径 | P0 |
| BL-004 | 消费量与销量互斥 | 供需口径 | P1 |
| BL-005 | 场内库存与非仓单库存互斥 | 库存口径 | P0 |
| BL-006 | 场内库存与社会库存互斥 | 库存口径 | P0 |
| BL-007 | 非仓单库存与社会库存互斥 | 库存口径 | P1 |
| BL-008 | 出口与国内销量互斥 | 贸易口径 | P0 |
| BL-009 | 利润与需求互斥 | 经济口径 | P0 |
| BL-010 | 库存与产能开工互斥 | 供需口径 | P0 |
| BL-011 | 价格与库存互斥 | 基本面口径 | P1 |
| BL-012 | 库存天数与库存量互斥 | 库存口径 | P1 |
| BL-013 | 加工费与完全成本互斥 | 成本口径 | P1 |
| BL-014 | 供需平衡与价格互斥 | 基本面口径 | P2 |
| BL-015 | 国内销量与出口互斥(反向) | 贸易口径 | P0 |
| BL-016 | 利润与产量互斥 | 经济口径 | P1 |
| BL-017 | 价格与利润互斥 | 基本面口径 | P2 |
| BL-018 | 跨品种匹配禁止 | 品种口径 | P0 |
| BL-019 | 硅与铜跨品种禁止 | 品种口径 | P0 |
| BL-020 | 硅与苯乙烯跨品种禁止 | 品种口径 | P0 |
| BL-021 | 硅与黄金跨品种禁止 | 品种口径 | P0 |
| BL-022 | 镍与铜跨品种禁止 | 品种口径 | P0 |
| BL-023 | 升贴水与价格互斥 | 基本面口径 | P2 |
| BL-024 | 出库量与库存互斥 | 库存口径 | P1 |
| BL-025 | 消费量与产量互斥(反向) | 供需口径 | P0 |

## 6. 去重规则

去重键 = `(indicator_name, variety, blacklist_id)`
- 相同指标名称 + 相同品种 + 相同黑名单规则 = 标记为重复
- 重复条目保留在CSV中，通过 `is_duplicate=YES` 和 `duplicate_of` 字段标记
- 独立条目 `is_duplicate=NO`，`duplicate_of` 为空

## 7. 约束声明

- NO_SOURCE_MODIFICATION: 不修改原始模板、indicators_v1、GT、匹配规则
- NO_GT_MODIFICATION: 不修改GT标注
- NO_RULE_MODIFICATION: 不修改匹配规则（仅使用固定黑名单）
- NO_ZHIJI_API_CALL: 不调用知几接口，仅静态文本扫描与数据合并
- READ_ONLY + APPEND_ONLY: 只新增文件，禁止覆盖仓库已有历史产物

---
**生成工具**: build_unified_risk_db.py
