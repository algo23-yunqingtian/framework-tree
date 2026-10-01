# V85 交付包 README

> **V85 图表模板风险管控与人工评审系统**
> 分支: `feature/v85-chart-template`
> 最新commit: 53c0466 (HERMES) / 1abfa33 (DSHB)
> 生成时间: 2026-10-01

---

## 版本简介

V85 是期货图表模板风险管控系统的最终交付版本，覆盖 488 个图表模板（PDF 333 + THS 155），9 个有色金属品种，实现从风险识别→黑名单校验→人工评审→Gate准入门禁的全链路管控。

---

## 核心能力

| 能力 | 说明 | 状态 |
|------|------|------|
| 图表模板集成 | 333套PDF模板接入zhiji数据渲染HTML | ✅ 328/333 (98.5%) |
| 语义黑名单 | 31条规则+409辅助+1候选(BL-009a) | ✅ |
| 风险库 | 50条独立风险(50字段)，DSHB v2版 | ✅ |
| 别名库 | 864条高置信别名(7品种) | ✅ |
| 混淆对 | 13条(8P0+5P1) | ✅ |
| 人工评审工具 | 批量导入导出+跨品种预警+Gate预校验 | ✅ |
| 评审门户 | V6验收总览(9面板) | ✅ |
| Gate准入门禁 | 46项HERMES + 6项DSHB v2 | ⚠ 4/5 BLOCKED |
| THS适配 | 155个THS模板适配转换 | ✅ |

---

## 使用前置条件

1. **分支**: `feature/v85-chart-template`（禁止合并main）
2. **Python**: 3.11+
3. **依赖文件**:
   - `data/indicators_v1.json` (只读)
   - `data/tree_config.json` (只读)
   - `ths_adapted_all.json` (只读)
4. **约束**:
   - 不调用zhiji API
   - 不修改源模板
   - 仅新增文件

---

## Gate 验收状态

| Gate | 状态 | 说明 |
|------|------|------|
| H1 THS匹配率≥80% | ❌ BLOCKED | 0% (待人工回写864候选) |
| H2 P0全部处置 | ❌ BLOCKED | 232阻塞 (待Batch-C评审) |
| H3 渲染就绪率≥50% | ❌ BLOCKED | 19.9% (依赖H1+H4) |
| H4 评审完成率≥90% | ❌ BLOCKED | 0% (待人工3-5天) |
| H5 DSHB风险库落地 | ✅ PASS | 50条v2已落地 |
| DSHB G-01~G-06 | ⚠ PARTIAL | G-02/G-04 PASS, G-01/G-03/G-05/G-06 PARTIAL |

**结论: ❌ 禁止上线 — 4项硬阻塞未解除**

---

## 已知限制

| 限制 | 说明 |
|------|------|
| THS匹配率0% | 155模板无zhiji_id，需人工回写 |
| 评审完成率0% | 488模板待人工评审3-5天 |
| BL-009方向性缺失 | V2已定位，BL-009a候选已生成 |
| 4条漏拦截P0 | 3条数据缺失+1条方向性 |
| DSHE部分未落盘 | 3个文件未交付(等价版可用) |

---

## V86 规划

| 优先级 | 迭代项 |
|--------|--------|
| P0 | THS回填+全量评审+BL-009a启用 |
| P1 | 4条漏拦截处置+就绪率提升 |
| P2 | 并发渲染+白名单过期提醒 |
| P3 | 评审门户Web化+自动回归测试 |

---

## 文件目录导读

```
analysis/e2e_output/v85/
├── hermes_v85_final_delivery/          # V85最终交付包(本轮)
│   ├── enhanced_review_portal_v6_final.md  # V6验收门户
│   ├── v85_delivery_readme.md              # 本文件
│   ├── v85_full_delivery_manifest_v2.md    # 全交付清单
│   ├── delivery_package_check.py           # 自检脚本
│   ├── v85_gate_final_acceptance_report.md # Gate报告
│   ├── v85_archive_folder_tree.md          # 归档目录树
│   └── v85_demo_overview.md                # 演示文档
├── hermes_human_review_tool/            # 人工评审工具
│   ├── batch_export_import_v2.py           # 批量工具v2
│   ├── gate_pre_check.py                   # Gate预校验
│   ├── review_batches_v6/                  # 评审批次v6
│   └── v85_p0_risk_human_workbook.csv      # P0风险工作表
├── hermes_portal_gate_final/            # 门户v5+Gate
│   ├── indicator_alias_library.csv         # 别名库864条
│   ├── high_risk_confusion_pairs.csv       # 混淆对13条
│   └── mapping_fill_helper_v2.py           # 回写工具
├── dshb_full_integrate/                 # DSHB全链路整合
│   ├── semantic_blacklist_v85_final.json   # 黑名单31规则
│   ├── full_488_template_playback_result.csv  # 488回放2721行
│   └── cross_variety_p0_validation.csv     # 34 P0验证
└── miss_risk_mining/                    # DSHB漏检风险挖掘
    ├── unified_indicator_risk_db_v2.csv    # 风险库v2(50条)
    ├── dsh_gate_self_check_v2.md           # Gate v2(6项)
    └── blacklist_extend_candidate_v2.json  # BL-009a候选
```
