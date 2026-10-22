# V3-EXT R02 官方汇总回测报告模板

## 1. 实验总览
- 任务ID: {{task_id}}
- 基线分支: {{baseline}}
- Commit: {{commit}}
- 版本标签: {{version_tag}}
- 实验目标: {{objective}}
- 范围边界: {{scope}}
- 隔离声明: {{isolation}}

## 2. 因子池总览表
- 主冻结因子 (BASE_FROZEN): {{base_frozen_factors}}
- A级观测因子 (A_OBS): {{a_obs_factors}}
- B级递补因子 (B_OBS): {{b_obs_factors}}
- C级淘汰清单 (C_REJECT): {{c_reject_factors}}
- 评级标准: {{rating_rules}}

## 3. 风控参数页
- LOCKDOWN梯度对比表: {{lockdown_gradient_table}}
- 拥挤阈值: {{crowding_thresholds}}
- 分位数参数: {{percentile_params}}
- MC触发频率: {{mc_trigger_freq}}

## 4. 回测基准设定
- 样本区间: {{sample_period}}
- 品种集合: {{symbols}}
- 手续费滑点: {{costs}}
- MC种子: {{mc_seeds}}
- 复现说明: {{reproducibility}}

## 5. 绩效汇总
- 全因子分层绩效表: {{performance_table}}
- IC时序: {{ic_timeseries}}
- 稳定性分析: {{stability_analysis}}
- 领先预警提前窗口: {{lead_warning_windows}}

## 6. 漏检与盲区分析
- SC4漏检覆盖: {{sc4_coverage}}
- 领先因子预警增益: {{lead_gain}}
- 误报代价: {{false_alert_cost}}
- 剩余盲区清单: {{remaining_blindspots}}

## 7. 压力边界校验
- 尾部压力: {{tail_stress}}
- 拥挤失效场景: {{crowding_failure}}
- 参数敏感性小结: {{sensitivity_summary}}

## 8. 约束边界说明
- 观测因子禁止并入主策略: {{obs_isolation_rule}}
- 仅用于预警观测: {{monitoring_only_rule}}

## 9. 制品审计附录
- 全文件SHA清单: {{sha_manifest}}
- 各Agent回执链接: {{agent_receipts}}
- 快照锚点: {{snapshot_anchors}}

## 10. 结论与迭代建议
- 结论: {{conclusions}}
- 下一轮迭代方向: {{next_steps}}
