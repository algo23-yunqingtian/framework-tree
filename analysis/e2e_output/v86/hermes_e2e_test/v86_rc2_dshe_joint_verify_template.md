# V86-RC2 双维度联合抽样校验报告模板

> **Task:** DSHE_V86_RC2_PROD_PHASE_DEP_WATCHER / T3.5
> **Generated:** 2026-10-15
> **Branch:** `feature/v85-chart-template`
> **Output Dir:** `analysis/e2e_output/v86/hermes_e2e_test/`
> **Status:** ✅ T3.5 COMPLETE — 联合校验报告模板已固化，可自动生成标准化报告
> **Template ID:** DSHE-JOINT-VERIFY-TEMPLATE-V1.0

---

## 模板使用说明

### 自动化生成

```bash
# 方法1: 自动模式（DEP恢复后自动触发）
python3 dep_recovery_auto_verify.py --auto

# 方法2: 手动模式（带参数）
python3 dep_recovery_auto_verify.py --manual --true-count 5 --total 178

# 方法3: Dry run
python3 dep_recovery_auto_verify.py --dry-run
```

### 自动填充字段

| 字段 | 来源 | 自动填充 |
|------|------|---------|
| 快照ID/MD5 | 桥接快照JSON | ✅ |
| 快照生成时间 | 桥接快照JSON | ✅ |
| 桥接总条目 | 桥接快照JSON | ✅ |
| data_fetchable=TRUE | 桥接快照JSON | ✅ |
| data_fetchable=FALSE | 桥接快照JSON | ✅ |
| 抽样清单 | 分层抽样算法 | ✅ |
| UI渲染结果 | 双维度校验引擎 | ✅ |
| data_fetchable状态 | 桥接快照JSON | ✅ |
| 联合校验结果 | 双维度计算 | ✅ |
| 误判率统计 | 计算引擎 | ✅ |
| MD5汇总 | 计算引擎 | ✅ |
| 跨链路一致性 | 计算引擎 | ✅ |

### 手动填充字段

| 字段 | 说明 |
|------|------|
| 报告标题日期 | 自动生成 |
| HERMES预审结论 | HERMES团队填写 |
| Gate评审结论 | Gate评审组填写 |
| 跨团队同步记录 | 负责人填写 |
| 签字/审批 | 相关负责人 |

---

## 报告正文模板

### 报告元数据

```
报告ID: DSHE-JOINT-VERIFY-{YYYYMMDD}-{NNN}
任务: DSHE_V86_RC2_PROD_PHASE_DEP_WATCHER / T3.3
模式: {AUTO_RECOVERY | DEPENDENCY_BLOCK}
生成时间: {YYYY-MM-DD HH:MM:SS}
快照版本: {SNAPSHOT_ID}
快照MD5: {MD5}
快照生成时间: {GENERATED_AT}
分支: feature/v85-chart-template
```

---

### 1. 依赖恢复状态

| 指标 | 值 |
|------|-----|
| 桥接总条目 | {TOTAL_ENTRIES} |
| data_fetchable=TRUE | {TRUE_COUNT} ({TRUE_PERCENT}%) |
| data_fetchable=FALSE | {FALSE_COUNT} ({FALSE_PERCENT}%) |
| 恢复率 | {RECOVERY_RATE}% |

**{RECOVERY_STATUS}**

---

### 2. 抽样策略

| 维度 | 值 |
|------|-----|
| 抽样总量 | {SAMPLE_SIZE} 项 |
| 抽样率 | {SAMPLE_RATE}% |
| 品种覆盖 | {PRODUCT_COUNT} 种 ({PRODUCTS_LIST}) |
| P0高风险 | {P0_COUNT} 项 (抽样率≥40%) |
| P1中风险 | {P1_COUNT} 项 (抽样率~50%) |
| P2低风险 | {P2_COUNT} 项 (抽样率~27%) |
| 映射方法覆盖 | {MAPPING_METHODS} |

---

### 3. 抽样清单

| # | indicator_id | display_name | product | risk | mapping_method | data_fetchable |
|---|-------------|-------------|---------|------|---------------|---------------|
| {ROW_NUMBER} | {INDICATOR_ID} | {DISPLAY_NAME} | {PRODUCT} | {RISK} | {MAPPING_METHOD} | {TRUE/FALSE} |
| ... | ... | ... | ... | ... | ... | ... |

---

### 4. 维度1: UI渲染校验

| 指标 | 值 |
|------|-----|
| 校验总项 | {UI_TOTAL} |
| PASS | {UI_PASS} ({UI_PASS_RATE}%) |
| FAIL | {UI_FAIL} ({UI_FAIL_RATE}%) |
| 渲染异常 | {UI_ANOMALY} |
| 标签不匹配 | {UI_LABEL_MISMATCH} |

#### UI渲染异常明细

| indicator_id | display_name | 异常类型 | 严重程度 | 描述 |
|-------------|-------------|---------|---------|------|
| {INDICATOR_ID} | {DISPLAY_NAME} | {ANOMALY_TYPE} | {SEVERITY} | {DESCRIPTION} |

---

### 5. 维度2: data_fetchable状态校验

| 指标 | 值 |
|------|-----|
| data_fetchable=TRUE | {FETCH_TRUE} |
| data_fetchable=FALSE | {FETCH_FALSE} |
| DEPENDENCY_BLOCK触发 | {FETCH_BLOCKED} |
| 纳入PASS统计 | {FETCH_INCLUDED} |
| 排除PASS统计 | {FETCH_EXCLUDED} |

---

### 6. 联合校验汇总

| 指标 | 值 |
|------|-----|
| 联合校验总项 | {JOINT_TOTAL} |
| FULLY_AVAILABLE_PASS | {FULLY_AVAILABLE} ({FULLY_AVAILABLE_RATE}%) |
| DEPENDENCY_BLOCK | {DEPENDENCY_BLOCK} ({DEPENDENCY_BLOCK_RATE}%) |
| RENDER_ANOMALY | {RENDER_ANOMALY} ({RENDER_ANOMALY_RATE}%) |
| 状态误判 | {MISJUDGE} |
| 误判率 | {MISJUDGE_RATE}% |

---

### 7. 联合校验明细

| # | indicator_id | display_name | product | risk | UI | data_fetchable | 联合状态 |
|---|-------------|-------------|---------|------|-----|---------------|---------|
| {ROW_NUMBER} | {INDICATOR_ID} | {DISPLAY_NAME} | {PRODUCT} | {RISK} | {UI_PASS/FAIL} | {TRUE/FALSE} | {JOINT_STATUS} |
| ... | ... | ... | ... | ... | ... | ... | ... |

---

### 8. 品种分布

| 品种 | 抽样项 | FULLY_AVAILABLE | DEPENDENCY_BLOCK | 可用率 |
|------|--------|----------------|-----------------|--------|
| {PRODUCT} | {COUNT} | {AVAILABLE} | {BLOCKED} | {RATE}% |
| ... | ... | ... | ... | ... |

---

### 9. 误判分析

```
{MISJUDGE_ANALYSIS}
```

{MISJUDGE_DETAILS}

---

### 10. 跨链路一致性校验

| 链路 | 校验项 | 结果 |
|------|--------|------|
| zhiji→DSHB | 字段传递完整性 | {RESULT_1} |
| DSHB→DSHE | 字段传递一致性 | {RESULT_2} |
| DSHE→HERMES | 审计数据完整性 | {RESULT_3} |
| 端到端 | 延迟 | {RESULT_4} |

---

### 11. MD5校验汇总

| # | 文件 | MD5 | 大小 | 校验 |
|---|------|-----|------|------|
| {ROW_NUMBER} | {FILE_NAME} | `{MD5}` | {SIZE} B | {PASS/FAIL} |
| ... | ... | ... | ... | ... |

**MD5校验**: {MD5_PASS}/{MD5_TOTAL} PASS ({MD5_RATE}%)

---

### 12. 结论

```
{CONCLUSION}
```

#### 判定标准

| 条件 | 值 | 判定 |
|------|-----|------|
| 误判率 | {MISJUDGE_RATE}% | {PASS/FAIL} (阈值: 0%) |
| 渲染异常 | {RENDER_ANOMALY} 项 | {PASS/FAIL} (阈值: 0) |
| 字段丢失 | {FIELD_LOSS} 项 | {PASS/FAIL} (阈值: 0) |
| 数据延迟 | {MAX_DELAY}s | {PASS/FAIL} (阈值: 300s) |
| 跨链路一致性 | {CONSISTENCY_RATE}% | {PASS/FAIL} (阈值: 100%) |

#### 综合结论

{OVERALL_CONCLUSION}

---

### 13. HERMES预审确认

| 检查项 | 结论 | 审核人 | 日期 |
|--------|------|--------|------|
| 双维度校验完整性 | {PENDING/PASS/FAIL} | {REVIEWER} | {DATE} |
| 误判率 | {PENDING/PASS/FAIL} | {REVIEWER} | {DATE} |
| 跨链路一致性 | {PENDING/PASS/FAIL} | {REVIEWER} | {DATE} |
| 约束合规 | {PENDING/PASS/FAIL} | {REVIEWER} | {DATE} |
| 报告格式 | {PENDING/PASS/FAIL} | {REVIEWER} | {DATE} |

---

### 14. 跨团队同步记录

| # | 团队 | 同步内容 | 确认 | 时间 |
|---|------|---------|------|------|
| {ROW_NUMBER} | {TEAM} | {CONTENT} | {CONFIRM} | {TIME} |
| ... | ... | ... | ... | ... |

---

### 15. 签字/审批

| 角色 | 签字 | 日期 |
|------|------|------|
| 报告生成 | (自动) | {DATE} |
| HERMES预审 | {SIGNATURE} | {DATE} |
| Gate评审 | {SIGNATURE} | {DATE} |
| 运维确认 | {SIGNATURE} | {DATE} |

---

### 16. 约束合规

| 约束 | 值 | 合规 |
|------|-----|------|
| `JOB_READY` | FALSE | {COMPLIANT} |
| `NO_ZHIJI_API_CALL` | FALSE (允许) | {COMPLIANT} |
| `NO_MODIFY_V85` | TRUE | {COMPLIANT} |
| `NO_OVERWRITE` | TRUE | {COMPLIANT} |
| `BRANCH_LOCKED` | TRUE | {COMPLIANT} |

---

### 17. 附件清单

| # | 文件 | 大小 | MD5 |
|---|------|------|-----|
| {ROW_NUMBER} | {FILE_NAME} | {SIZE} B | `{MD5}` |
| ... | ... | ... | ... |

---

*Template Generated: 2026-10-15*
*Task: DSHE_V86_RC2_PROD_PHASE_DEP_WATCHER / T3.5*
*Branch: feature/v85-chart-template*
*Template ID: DSHE-JOINT-VERIFY-TEMPLATE-V1.0*
*Status: T3.5 COMPLETE — 联合校验报告模板已固化*
