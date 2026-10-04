# V86-RC2 双维度联合抽样校验报告模板 V2 (审计对齐版)

> **Task:** DSHE_V86_RC2_PROD_PHASE_L2_AUDIT_ALIGN / T3.4
> **Generated:** 2026-10-15
> **Branch:** `feature/v85-chart-template`
> **Status:** ✅ T3.4 COMPLETE — 模板已升级，对齐HERMES审计字段，可直接提交L3预审
> **Template ID:** DSHE-JOINT-VERIFY-TEMPLATE-V2.0
> **升级依据:** V1.0 → V2.0 新增审计溯源字段、独立调用链证据索引、双桥接率指标、风险分类标记

---

## V1.0 → V2.0 变更摘要

| 变更项 | V1.0 | V2.0 | 说明 |
|--------|------|------|------|
| 审计元数据 | ❌ 无 | ✅ 新增第0节 | 审计指纹/运行ID/会话ID/独立调用声明 |
| 双桥接率 | ❌ 无 | ✅ 新增 | 元数据完成率 + 真实有效桥接率 |
| 独立调用链 | ❌ 无 | ✅ 新增第5节 | DSHE独立zhiji调用，DSHB复用标记 |
| 审计证据索引 | ❌ 无 | ✅ 新增第10节 | 证据包路径/调用数/trace ID索引 |
| 风险分类标记 | ❌ 无 | ✅ 新增 | DEPENDENCY_BLOCK单独分类+Gate不豁免 |
| COMPLETED定义 | 单一证据 | 双证据 | 元数据+真实可取 |
| DSHB复用声明 | ❌ 无 | ✅ 全篇标记 | 审计硬规则: 禁止复用 |
| 审计追踪trace | ❌ 无 | ✅ 每条携带 | 独立调用链证据指纹 |

---

## 模板使用说明

### 自动化生成

```bash
# 方法1: 自动模式（DEP恢复后自动触发）
python3 dep_recovery_auto_verify_v2.py --auto

# 方法2: 自动模式（带快照参数）
python3 dep_recovery_auto_verify_v2.py --auto --true-count 5 --total 178

# 方法3: 手动模式
python3 dep_recovery_auto_verify_v2.py --manual

# 方法4: Dry run
python3 dep_recovery_auto_verify_v2.py --dry-run

# 方法5: 仅审计检查
python3 dep_recovery_auto_verify_v2.py --audit-only
```

### 自动填充字段 (V2新增)

| 字段 | 来源 | 自动填充 | V2新增 |
|------|------|---------|--------|
| 审计指纹 | AuditCallChain | ✅ | ✅ |
| 运行ID | AuditCallChain | ✅ | ✅ |
| 会话ID | AuditCallChain | ✅ | ✅ |
| DSHB复用标记 | 全篇 | ✅ | ✅ |
| 元数据完成率 | 计算引擎 | ✅ | ✅ |
| 真实有效桥接率 | 计算引擎 | ✅ | ✅ |
| 独立调用链证据 | payload_evidence/ | ✅ | ✅ |
| 审计追踪trace ID | 每个调用 | ✅ | ✅ |
| COMPLETED双证据 | 计算引擎 | ✅ | ✅ |
| DEP分类标记 | 计算引擎 | ✅ | ✅ |
| 证据包路径 | 文件路径 | ✅ | ✅ |
| 证据调用数 | 计算引擎 | ✅ | ✅ |

### 手动填充字段

| 字段 | 说明 |
|------|------|
| HERMES预审结论 | HERMES团队填写 |
| Gate评审结论 | Gate评审组填写 |
| 跨团队同步记录 | 负责人填写 |
| 签字/审批 | 相关负责人 |
| 退回处理记录 | HERMES退回时填写 |

---

## 报告正文模板

### 报告元数据

```
报告ID: DSHE-JOINT-VERIFY-{YYYYMMDD}-{NNN}
任务: DSHE_V86_RC2_PROD_PHASE_L2_AUDIT_ALIGN / T3.4
模式: {AUTO_RECOVERY | DEPENDENCY_BLOCK}
生成时间: {YYYY-MM-DD HH:MM:SS}
快照版本: {SNAPSHOT_ID}
快照MD5: {MD5}
快照生成时间: {GENERATED_AT}
分支: feature/v85-chart-template
模板ID: DSHE-JOINT-VERIFY-TEMPLATE-V2.0
审计指纹: {AUDIT_FINGERPRINT}
DSHB复用: ❌ FALSE (独立调用链路)
```

---

### 0. 审计元数据 [V2新增]

| 字段 | 值 |
|------|-----|
| 审计指纹 | `{AUDIT_FINGERPRINT}` |
| 运行ID | `{RUN_ID}` |
| 会话ID | `{SESSION_ID}` |
| 独立调用 | ✅ DSHE直接调用zhiji API |
| DSHB复用 | ❌ 禁止 (审计硬规则) |
| 独立调用链证据 | `{EVIDENCE_PACKAGE_PATH}` |
| 证据调用数 | `{EVIDENCE_CALL_COUNT}` |

---

### 1. 依赖恢复状态 [V2新增双指标]

| 指标 | 值 |
|------|-----|
| 桥接总条目 | {TOTAL_ENTRIES} |
| data_fetchable=TRUE | {TRUE_COUNT} ({TRUE_PERCENT}%) |
| data_fetchable=FALSE | {FALSE_COUNT} ({FALSE_PERCENT}%) |
| 快照恢复率 | {RECOVERY_RATE}% |
| **元数据完成率** | **{METADATA_COMPLETION_RATE}%** |
| **真实有效桥接率** | **{EFFECTIVE_BRIDGE_RATE}%** |

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

### 3. 抽样清单 [V2新增trace ID]

| # | indicator_id | display_name | product | risk | short_id | data_fetchable | trace_id |
|---|-------------|-------------|---------|------|---------|---------------|---------|
| {ROW_NUMBER} | {INDICATOR_ID} | {DISPLAY_NAME} | {PRODUCT} | {RISK} | {SHORT_ID} | {TRUE/FALSE} | `{TRACE_ID}` |
| ... | ... | ... | ... | ... | ... | ... | ... |

---

### 4. 维度1: 元数据完整性校验 [V2新增]

| 指标 | 值 |
|------|-----|
| 校验总项 | {META_TOTAL} |
| 完整 | {META_COMPLETE} ({META_COMPLETE_RATE}%) |
| 不完整 | {META_INCOMPLETE} ({META_INCOMPLETE_RATE}%) |
| 平均完整率 | {META_AVG_RATE}% |

#### 不完整字段明细

| indicator_id | 缺失字段 | 完整率 |
|-------------|---------|--------|
| {INDICATOR_ID} | {MISSING_FIELDS} | {COMPLETENESS_RATE}% |

---

### 5. 维度2: 独立zhiji调用校验 [V2核心变更]

> ⚠️ **V2核心变更**: DSHE直接调用zhiji API，不复用DSHB结果

| 指标 | 值 |
|------|-----|
| 独立调用总项 | {FETCH_TOTAL} |
| 独立获取成功 | {FETCH_OK} ({FETCH_OK_RATE}%) |
| 独立获取失败 | {FETCH_FAIL} ({FETCH_FAIL_RATE}%) |
| DSHB复用 | ❌ FALSE |
| 原始payload持久化 | ✅ 全部 |

---

### 6. 联合校验汇总 [V2双维度指标]

| 指标 | 值 |
|------|-----|
| 联合校验总项 | {JOINT_TOTAL} |
| FULLY_AVAILABLE_PASS | {FULLY_AVAILABLE} ({EFFECTIVE_BRIDGE_RATE}%) |
| DEPENDENCY_BLOCK | {DEPENDENCY_BLOCK} ({DEP_BLOCK_RATE}%) |
| RENDER_ANOMALY | {RENDER_ANOMALY} ({ANOMALY_RATE}%) |
| 状态误判 | {MISJUDGE} |
| 误判率 | {MISJUDGE_RATE}% |

#### V2 双维度指标

| 指标 | 值 | 说明 |
|------|-----|------|
| 元数据完成率 | {METADATA_COMPLETION_RATE}% | 快照元数据字段完整率 |
| 真实有效桥接率 | {EFFECTIVE_BRIDGE_RATE}% | DSHE独立zhiji调用成功率 |
| COMPLETED (双证据) | {COMPLETED_COUNT}/{TOTAL_COUNT} | 元数据+真实可取 |
| DEPENDENCY_BLOCK (非内部缺陷) | {DEPENDENCY_BLOCK} | 外部依赖阻塞，Gate不豁免 |
| DSHB复用 | ❌ {DSHB_REUSE} | 审计硬规则: 独立调用 |
| 审计追踪调用数 | {AUDIT_TRACE_COUNT} | 独立调用链证据 |

---

### 7. 联合校验明细 [V2新增COMPLETED+trace]

| # | indicator_id | product | risk | 元数据 | 独立zhiji | COMPLETED | 联合状态 | 分类 | trace_id |
|---|-------------|---------|------|--------|----------|-----------|---------|------|---------|
| {ROW_NUMBER} | {INDICATOR_ID} | {PRODUCT} | {RISK} | {META_PASS/FAIL} {META_RATE}% | {FETCH_PASS/FAIL} {FETCH_STATUS} | {COMPLETED_Y/N} | {JOINT_STATUS} | {CATEGORY} | `{TRACE_ID}` |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

---

### 8. 品种分布 [V2新增异常分类]

| 品种 | 抽样项 | FULLY_AVAILABLE | DEPENDENCY_BLOCK | 异常 | 有效桥接率 |
|------|--------|----------------|-----------------|------|-----------|
| {PRODUCT} | {COUNT} | {AVAILABLE} | {BLOCKED} | {ANOMALY} | {RATE}% |
| ... | ... | ... | ... | ... | ... |

---

### 9. 误判分析

```
{MISJUDGE_ANALYSIS}
```

{MISJUDGE_DETAILS}

---

### 10. 审计证据索引 [V2新增]

| 证据项 | 值 |
|--------|-----|
| 审计指纹 | `{AUDIT_FINGERPRINT}` |
| 运行ID | `{RUN_ID}` |
| 独立调用总数 | {EVIDENCE_CALL_COUNT} |
| 证据包文件 | `{EVIDENCE_PACKAGE_FILE}` |
| 证据目录 | `.payload_evidence/` |
| DSHB复用 | ❌ FALSE (审计硬规则) |
| 原始payload保存 | ✅ 每个调用独立保存 |

---

### 11. MD5校验汇总

| # | 文件 | MD5 | 大小 | 校验 |
|---|------|-----|------|------|
| {ROW_NUMBER} | {FILE_NAME} | `{MD5}` | {SIZE} B | {PASS/FAIL} |
| ... | ... | ... | ... | ... |

**MD5校验**: {MD5_PASS}/{MD5_TOTAL} PASS ({MD5_RATE}%)

---

### 12. 结论 [V2新增]

#### 判定标准

| 条件 | 值 | 判定 | 阈值 |
|------|-----|------|------|
| 误判率 | {MISJUDGE_RATE}% | {PASS/FAIL} | 0% |
| 渲染异常 | {RENDER_ANOMALY} 项 | {PASS/FAIL} | 0 |
| 字段丢失 | {FIELD_LOSS} 项 | {PASS/FAIL} | 0 |
| 数据延迟 | {MAX_DELAY}s | {PASS/FAIL} | 300s |
| 跨链路一致性 | {CONSISTENCY_RATE}% | {PASS/FAIL} | 100% |
| 元数据完成率 | {METADATA_COMPLETION_RATE}% | {PASS/FAIL} | ≥95% |
| 真实有效桥接率 | {EFFECTIVE_BRIDGE_RATE}% | {PASS/FAIL} | 100% (恢复) | [OLD_CALIBER - METADATA_ONLY, HERMES_INVALID]
| DSHB复用 | {DSHB_REUSE} | {PASS/FAIL} | FALSE |

#### 综合结论

{OVERALL_CONCLUSION}

---

### 13. HERMES预审确认

| 检查项 | 结论 | 审核人 | 日期 |
|--------|------|--------|------|
| 双维度校验完整性 | {PENDING/PASS/FAIL} | {REVIEWER} | {DATE} |
| 误判率 | {PENDING/PASS/FAIL} | {REVIEWER} | {DATE} |
| 元数据完成率 | {PENDING/PASS/FAIL} | {REVIEWER} | {DATE} |
| 真实有效桥接率 | {PENDING/PASS/FAIL} | {REVIEWER} | {DATE} |
| 独立调用链证据 | {PENDING/PASS/FAIL} | {REVIEWER} | {DATE} |
| DSHB复用 | {PENDING/PASS/FAIL} | {REVIEWER} | {DATE} |
| 审计溯源完整性 | {PENDING/PASS/FAIL} | {REVIEWER} | {DATE} |
| 约束合规 | {PENDING/PASS/FAIL} | {REVIEWER} | {DATE} |
| 报告格式 | {PENDING/PASS/FAIL} | {REVIEWER} | {DATE} |

---

### 14. 跨团队同步记录

| # | 团队 | 同步内容 | 确认 | 时间 |
|---|------|---------|------|------|
| {ROW_NUMBER} | {TEAM} | {CONTENT} | {CONFIRM} | {TIME} |
| ... | ... | ... | ... | ... |

---

### 15. 退回处理记录 [V2新增]

| 项目 | 值 |
|------|-----|
| 退回状态 | {NOT_RETURNED / RETURNED / INVALIDATED} |
| 退回原因 | {RETURN_REASON} |
| 退回时间 | {RETURN_TIME} |
| 退回方 | {RETURN_BY} |
| 新报告ID | {NEW_REPORT_ID} |

---

### 16. 签字/审批

| 角色 | 签字 | 日期 |
|------|------|------|
| 报告生成 | (自动) | {DATE} |
| HERMES预审 | {SIGNATURE} | {DATE} |
| Gate评审 | {SIGNATURE} | {DATE} |
| 运维确认 | {SIGNATURE} | {DATE} |

---

### 17. 约束合规 [V2新增]

| 约束 | 值 | 合规 |
|------|-----|------|
| `JOB_READY` | FALSE | {COMPLIANT} |
| `NO_ZHIJI_API_CALL` | FALSE (允许) | {COMPLIANT} |
| `NO_MODIFY_V85` | TRUE | {COMPLIANT} |
| `NO_OVERWRITE` | TRUE | {COMPLIANT} |
| `BRANCH_LOCKED` | TRUE | {COMPLIANT} |
| `L2_INDEPENDENT_CALL_CHAIN` | TRUE (必须) | {COMPLIANT} |
| `NO_DSHB_REUSE` | TRUE (审计硬规则) | {COMPLIANT} |
| `AUDIT_TRACEABILITY` | TRUE (必须) | {COMPLIANT} |

---

### 18. 附件清单

| # | 文件 | 大小 | MD5 | 类型 |
|---|------|------|-----|------|
| {ROW_NUMBER} | {FILE_NAME} | {SIZE} B | `{MD5}` | {TYPE} |
| ... | ... | ... | ... | ... |

**附件类型:**
- 独立调用链证据包 (evidence_package_*.json)
- 原始payload目录 (.payload_evidence/)
- 抽样清单 (sample_list)
- E2E演练日志 (dryrun_shturl)
- L2交付物规范 (l2_deliverable_spec)

---

*Template Generated: 2026-10-15*
*Task: DSHE_V86_RC2_PROD_PHASE_L2_AUDIT_ALIGN / T3.4*
*Branch: feature/v85-chart-template*
*Template ID: DSHE-JOINT-VERIFY-TEMPLATE-V2.0*
*Status: T3.4 COMPLETE — 模板已升级，对齐HERMES审计字段*
*Previous Version: DSHE-JOINT-VERIFY-TEMPLATE-V1.0*
*Upgrade: V1.0 → V2.0 (审计溯源+独立调用链+双桥接率+风险分类)*
