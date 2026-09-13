# PB 5步流水线 · 入库脚本目录

> **约束声明**: 以下材料为入库准备，暂不执行PB完整流水线、不生成新PB指标。
> 等待后续通知再启动。

---

## 5步流水线概览

| 步骤 | 脚本 | 说明 |
|---|---|---|
| Step1 | `scripts/step1_adapt_driver.py` | 节点适配驱动 |
| Step2 | `scripts/step2_cache_load.py` | 缓存加载 |
| Step3 | `scripts/step3_verify_search.py` → `step3_verify_merge.py` → `step3_verify_refine.py` | 验证→合并→精炼 |
| Step4 | `scripts/step4_build_pages.py` (待创建) | 页面构建 |
| Step5 | `scripts/step5_audit.py` (待创建) | 质量审计 |

## 三类差异比对清单

| 差异类型 | 文件 | 说明 |
|---|---|---|
| A vs A 自对比 | `_r2_r4_fix.py` 已清除62张 | A vs A = 同名指标左右轴相同 |
| 跨品种串台 | `build_chart_registry.py` R1已修复 | ⚪→🟢待人工确认 |
| 图表名幻觉 | `task3_hallucination_clean.py` 已清理363条 | 62图表名+45派生+18跨品种 |

## 防图表名/数据源幻觉约束 prompt

```
[CONSTRAINT_PROMPT]
- 禁止生成"图名称"列包含的图表标题条目
- 禁止生成"派生形态"（环比/同比/分位数等）
- 禁止生成跨品种引用（如CU指标出现在AL页面）
- 所有指标必须从 indicators_v1.json 已注册列表选取
- 数据源必须通过知几 API 验证有连续时序数据
```

## PB现有指标核查结果

- 总计: 91条人工指标（i*/j*前缀）
- _nodes标注: 91/91 缺失（None）
- 缺陷登记: `docs/R2_R4_Fix_Report.md`