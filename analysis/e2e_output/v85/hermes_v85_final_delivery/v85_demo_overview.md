# V85 版本验收演示文档

> 工单: `HERMES_V85_FINAL_DELIVERY_PACKAGE_BUILD_AND_ACCEPTANCE_PORTAL`
> 面向: 验收人
> 日期: 2026-10-01

---

## 1. 核心能力演示要点

### 1.1 风险管控链路

```
模板(488) → 风险识别(50条) → 黑名单校验(31规则) → 人工评审(3批次) → Gate准入(46项)
```

### 1.2 关键数据

| 能力 | 数据 | 演示命令 |
|------|------|---------|
| 模板渲染 | 328/333 PDF模板渲染成功(98.5%) | `ls output/v85_chart_online_test/*.html \| wc -l` |
| 黑名单规则 | 31条最终版+1候选 | `python3 -c "import json; d=json.load(open('dshb_full_integrate/semantic_blacklist_v85_final.json')); print(len(d['rules']))"` |
| 风险库 | 50条(50字段)v2版 | `wc -l miss_risk_mining/unified_indicator_risk_db_v2.csv` |
| 别名库 | 864条(7品种) | `wc -l hermes_portal_gate_final/indicator_alias_library.csv` |
| 混淆对 | 13条(8P0+5P1) | `wc -l hermes_portal_gate_final/high_risk_confusion_pairs.csv` |
| 回放结果 | 2721条series | `wc -l dshb_full_integrate/full_488_template_playback_result.csv` |
| P0风险 | 34条(30阻塞+4未阻塞) | `wc -l hermes_human_review_tool/v85_p0_risk_human_workbook.csv` |

### 1.3 工具演示

| 工具 | 演示命令 |
|------|---------|
| Gate预校验 | `python3 hermes_human_review_tool/gate_pre_check.py` |
| 批量导出 | `python3 hermes_human_review_tool/batch_export_import_v2.py --export-batch batch_A --out /tmp/demo.csv` |
| 交付包自检 | `python3 hermes_v85_final_delivery/delivery_package_check.py` |

---

## 2. 关键截图索引

| 截图 | 位置 | 说明 |
|------|------|------|
| V6验收门户 | `enhanced_review_portal_v6_final.md` §1-9 | 9面板总览 |
| Gate状态大盘 | §2 | 5项硬阻塞进度条 |
| 风险库总览 | §3 | 50条风险分类 |
| 别名库质量 | §4 | 864条按品种分布 |
| 评审进度 | §6 | 488模板3批次进度 |
| V86迭代入口 | §8 | 12项规划 |

---

## 3. 风险边界说明

### 3.1 上线限制

**❌ 当前禁止上线**

4项硬阻塞未解除：
1. THS匹配率0%（需人工回写864候选）
2. P0未全部处置（232阻塞）
3. 渲染就绪率19.9%（目标≥50%）
4. 评审完成率0%（需人工3-5天）

### 3.2 可豁免项

4项可临时豁免：zhiji_id格式、meta字段、图例名称、G-06漏拦截。

### 3.3 已知局限

- 纯文本匹配无法区分产量vs销量语义差异
- BL-009方向性缺失（V2已定位，BL-009a候选已生成）
- 4条漏拦截P0（3条数据缺失+1条方向性）

---

## 4. 人工评审剩余工作量

| 批次 | 数量 | 预估工时 | 优先级 |
|------|------|---------|--------|
| Batch-A (可直接+高置信) | 97 | 1天 | P0 |
| Batch-B (THS待匹配) | 155 | 2天 | P1 |
| Batch-C (阻塞/复核/降级) | 236 | 1天 | P2 |
| P0风险处置 | 34 | 0.5天 | P0 |
| THS回填 | 864候选 | 1天 | P0 |
| **合计** | **488+34+864** | **5-7天** | |

---

## 5. 上线建议

### 5.1 上线路径

```
D+1: THS回写864高置信候选 → H1解除
D+2: Batch-A评审(97) + P0风险处置(34)
D+3-4: Batch-B评审(155)
D+5: Batch-C评审(236) → H2解除
D+6: Gate复检 → 全绿 → 合并main → 上线
```

### 5.2 上线前检查清单

- [ ] H1 THS匹配率≥80%
- [ ] H2 P0全部处置
- [ ] H3 渲染就绪率≥50%
- [ ] H4 评审完成率≥90%
- [ ] H5 风险库已落地 ✅
- [ ] Gate 46项全绿
- [ ] DSHB G-01~G-06全绿
- [ ] delivery_package_check.py PASS
- [ ] MD5校验通过
- [ ] Git tag v85-final 已打

### 5.3 上线后监控

- 白名单过期提醒（自动化）
- 评审结果回写验证
- 渲染就绪率持续≥50%
- P0风险零回归
