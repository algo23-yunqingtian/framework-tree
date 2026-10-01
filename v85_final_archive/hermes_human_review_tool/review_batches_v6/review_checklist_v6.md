# 人工评审核对清单 v6 (Review Checklist v6)

> 工单: `HERMES_V85_HUMAN_REVIEW_TOOL_ENHANCE_AND_BATCH_DATA_PREP`
> 适用批次: Batch-A / Batch-B / Batch-C (v6)
> v6新增: RISK-ID关联核验(§11) + Gate阻塞标记核验(§12) + DSHB不一致风险核验(§13)

---

## 使用说明

1. 按批次逐一评审，每评完一条在CSV中填写评审结果
2. v6新增字段: risk_id / disposal_suggestion / gate_blocked / inconsistent_risk / human_review_result
3. 全部核对完成后运行 `gate_pre_check.py` 一键Gate预校验

---

## 一~八（同v5，略）

> v5原有§1-8保持不变，详见 `review_batches_v5/review_checklist_v5.md`

## 九、别名核验项

- [ ] **9.1** 别名库匹配结果已查看（alias_match字段）
- [ ] **9.2** 别名推荐指标已核对（alias_recommendation字段）
- [ ] **9.3** 别名相似度≥70分时确认匹配合理
- [ ] **9.4** 别名与原始指标名语义一致
- [ ] **9.5** 别名对应zhiji_id有效

## 十、混淆指标核验项

- [ ] **10.1** 混淆对命中结果已查看
- [ ] **10.2** P0混淆对已确认处置
- [ ] **10.3** P1混淆对已人工评估
- [ ] **10.4** BL-021修复的3条误报已确认
- [ ] **10.5** 高危混淆对不在白名单中

## 十一、RISK-ID关联核验（v6新增）

- [ ] **11.1** 该模板关联的RISK-ID已查看（risk_id字段）
- [ ] **11.2** RISK-ID对应的P0风险已在工作表中处置
- [ ] **11.3** 处置结论与评审决策一致（修复→REJECTED+替换 / 白名单→WHITELISTED / 观察→保留）
- [ ] **11.4** 34条P0风险全部有处置结论
- [ ] **11.5** RISK-005白名单放行已确认

## 十二、Gate阻塞标记核验（v6新增）

- [ ] **12.1** gate_blocked字段已查看（YES=阻塞/NO=未阻塞）
- [ ] **12.2** YES的条目已完成处置或白名单
- [ ] **12.3** 处置后gate_blocked应变为NO
- [ ] **12.4** Gate预校验脚本已运行（`python3 gate_pre_check.py`）
- [ ] **12.5** 5项硬阻塞当前状态已确认

## 十三、DSHB不一致风险核验（v6新增）

- [ ] **13.1** inconsistent_risk字段已查看
- [ ] **13.2** 5条无法命中的风险已人工分析
- [ ] **13.3** BL-009反向匹配缺失已记录（V86迭代）
- [ ] **13.4** BL-026待确认规则已评估
- [ ] **13.5** 风险库一致性20/25(80%)已知

---

## 评审结果 CSV 格式

```csv
template_id,source,reviewer,review_time,decision,remark,risk_id,disposal_suggestion,gate_blocked,human_review_result
TPL-LC-091,PDF,张三,2026-10-01 15:00:00,修复,替换产量指标,RISK-006,阻塞待处置,YES,REPLACE
THS-NI-2.3,THS,李四,2026-10-01 15:05:00,观察,BL-022已拦截,RISK-014,阻塞待处置,YES,OBSERVE
TPL-AO-001,PDF,王五,2026-10-01 15:10:00,通过,可直接渲染,,,NO,APPROVED
```

## 批次说明

| 批次 | 范围 | 数量 | 文件 | v6新增字段 |
|------|------|------|------|-----------|
| Batch-A | 可直接+高置信 | 97 | batch_A_review_v6.csv | risk_id, disposal_suggestion, gate_blocked, inconsistent_risk, human_review_result |
| Batch-B | THS待匹配 | 155 | batch_B_review_v6.csv | 同上 |
| Batch-C | 阻塞/复核/降级 | 236 | batch_C_review_v6.csv | 同上 |
