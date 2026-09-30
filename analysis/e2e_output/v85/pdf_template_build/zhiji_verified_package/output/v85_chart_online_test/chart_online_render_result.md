# V85 图表模板在线渲染汇总报告

> 工单: `HERMES_V85_CHART_TEMPLATE_INTEGRATION`  
> 分支: `feature/v85-chart-template`（测试环境，未合并 main）  
> 生成时间: 2026-09-30T13:30:01  
> DSHB 交付 commit: `4061dcf`

## 1. 输入包校验

| 文件 | 大小 | MD5 |
|---|---|---|
| pdf_web_chart_template_hermes_ready.json | 463,182B | `92371c0a5029e6090ff3ca117697eda7` |
| zhiji_verify_stat.csv | 39,551B | `dba27ff486b74d4eafc01e42853ae000` |
| hermes_readme.md | 22,610B | `2c35c68add61edf961a0285ad37d55e4` |
| run_log.txt | 290B | `bb66bf3533b8ef7ffe58093fc0c4385f` |

⚠️ 注: 工单 T1 指定的 `delivery_confirm.md` 未包含在 DSHB 交付 commit `4061dcf` 中，已以 commit 记录 + 全文件 MD5 实测值作为完整性凭证。

## 2. 渲染结果总览

| 指标 | 数值 |
|---|---|
| 模板总数 | 333 |
| FULL_OK 模板 | 327 |
| PART_OK 模板（已加红色告警） | 6 |
| 图表渲染成功（有有效数据） | 328 (98.5%) |
| 图表渲染失败（无有效数据） | 5 |
| series 总数 | 362 |
| series 有效（zhiji 拉取成功） | 355 (98.1%) |
| series INVALID（HTTP 500 无效ID） | 5 |
| series MISSING（缺失） | 2 |
| series FETCH_FAIL（拉取失败） | 0 |
| 视觉校验平均分 | 9.63 / 10 |

## 3. 按品种分布

| 品种 | 图表数 | 成功 | FULL_OK | PART_OK | 平均评分 |
|---|---|---|---|---|---|
| LC 碳酸锂 | 100 | 100 | 100 | 0 | 9.74 |
| AO 氧化铝 | 63 | 61 | 61 | 2 | 9.60 |
| SI 工业硅 | 48 | 46 | 45 | 3 | 9.29 |
| NI 镍 | 47 | 46 | 46 | 1 | 9.43 |
| AL 铝 | 38 | 38 | 38 | 0 | 9.92 |
| SN 锡 | 37 | 37 | 37 | 0 | 9.78 |

## 4. 按图表类型分布

| chart_type | 数量 | 平均评分 |
|---|---|---|
| 单折线 | 322 | 9.66 |
| 堆叠柱状 | 4 | 9.50 |
| 多折线 | 4 | 9.75 |
| 复合混合(折线+柱状) | 3 | 6.00 |

## 5. 视觉评分分布

| 评分区间 | 数量 | 占比 |
|---|---|---|
| 10分(满分) | 271 | 81.4% |
| 9分 | 43 | 12.9% |
| 7-8分 | 14 | 4.2% |
| 5-6分 | 0 | 0.0% |
| 0-4分 | 5 | 1.5% |

## 6. zhiji 拉取失败 ID（需人工处理）

无（全部可拉取 ID 均成功获取时序数据）

## 7. 渲染产物位置

```
/home/ubuntu/framework-tree/analysis/e2e_output/v85/pdf_template_build/zhiji_verified_package/output/v85_chart_online_test/
├── rendered/          (333 个图表 HTML)
├── chart_online_render_result.md
├── node_mapping_index.csv
├── node_index.json
├── visual_check_result.csv
├── failed_chart_list.md
└── online_readme.md
```

## 8. T5 完成标准验收

| # | 标准 | 结果 |
|---|---|---|
| 1 | 327套FULL_OK模板全部成功拉取zhiji时序并渲染 | ✅ 327套FULL_OK，327套渲染出有效数据 |
| 2 | 节点映射索引完整，可在Framework Tree对应节点访问图表 | ✅ 36个节点, 333个模板全部挂载 |
| 3 | 输出完整校验报告，标记异常图表 | ✅ visual_check_result.csv(333行) + failed_chart_list.md |
| 4 | 生成可人工复核的可视化页面，用于业务验收 | ✅ /home/ubuntu/framework-tree/analysis/e2e_output/v85/pdf_template_build/zhiji_verified_package/output/v85_chart_online_test/rendered/ 共333个HTML |
