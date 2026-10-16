# P0-12 交付产物冻结只读声明

> **TASK_ID**: V88_PHASE03_P1_DSHE_P012_EXEMPTION_PREPARE_AND_CROSS_AGENT_ALIGN_JOB / T0
> **AGENT**: DSHE | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **冻结时间**: 2026-10-16 UTC+8
> **冻结基线**: commit b1987a4 (P012_CPU_THRESHOLD_EXCEPTION_HANDLER_JOB)
> **约束**: BRANCH_LOCKED / NO_OVERWRITE / NO_MODIFY_V87 / NO_EDIT_RELEASE_TAG / NO_ZHIJI_API_CALL

---

## 1. 冻结范围

P0-12 全套交付产物自 commit `b1987a4` 起进入**只读冻结**状态。任何修改必须经新工单审批。

### 1.1 核心交付物（冻结清单）

| # | 文件 | 路径 | MD5 (前12位) | 冻结状态 |
|:-:|------|------|:------------:|:--------:|
| 1 | `v88_p012_full_link_cpu_compare.json` | `p012_final_triplefix/frozen_p012_gate_package/` | C10D5A32ECCB | 🔒 FROZEN |
| 2 | `p012_gate_manifest.json` | `p012_final_triplefix/frozen_p012_gate_package/` | A4FB9C55ECFB | 🔒 FROZEN (v3.0.0) |
| 3 | `v88_phase03_p012_cpu_threshold_exception_note.md` | `p012_cpu_exception/` | 338C81BA3523 | 🔒 FROZEN |
| 4 | `p012_optimization_option_evaluation.md` | `p012_cpu_exception/` | B5C1F086BF87 | 🔒 FROZEN |
| 5 | `p012_gate_threshold_apply_exemption.md` | `p012_cpu_exception/` | 2E20AE46CD70 | 🔒 FROZEN |
| 6 | `v88_phase03_r3_e2e_regression_after_exception_handle.md` | `p012_cpu_exception/` | — | 🔒 FROZEN |
| 7 | `v88_phase03_p1_dshe_risklist.md` | `p012_cpu_exception/` | — | 🔒 FROZEN (superseded by cross_align版) |

### 1.2 采集脚本（冻结清单）

| # | 文件 | 路径 | 冻结状态 |
|:-:|------|------|:--------:|
| 1 | `collect_cpu_baseline.py` | `p012_cpu_benchmark/` | 🔒 FROZEN |
| 2 | `v88_p012_full_link_cpu_compare.json` | `p012_cpu_benchmark/` | 🔒 FROZEN |
| 3 | `p012_enhanced_cpu_baseline_audit.json` | `render_archive_phase04_prep/frozen_p012_gate_package/` | 🔒 FROZEN |

### 1.3 frozen 审计包

| 包版本 | 路径 | 文件数 | 状态 |
|--------|------|:------:|:----:|
| v3.0.0 | `p012_final_triplefix/frozen_p012_gate_package/` | 5 | 🔒 FROZEN |
| v2.0.0 | `render_archive_phase04_prep/frozen_p012_gate_package/` | 6 | 🔒 FROZEN (历史归档) |

---

## 2. 冻结规则

### 2.1 禁止修改项

1. **JSON 数据文件**：`v88_p012_full_link_cpu_compare.json` 中的 `cpu_peak_pct`、`caliber`、`comparability_note` 字段禁止修改——已通过 P0-12 三段过滤校验
2. **采集脚本核心逻辑**：`collect_cpu_baseline.py` 的测量方法（`time.process_time()/wall_time*100`）禁止修改——口径已对齐
3. **frozen 包 manifest**：`p012_gate_manifest.json` 的 `version`、`contents`、`audit_summary` 禁止修改——MD5 已固化
4. **异常说明文档结论**：CPU 99.4871% 为物理固有约束的论证结论禁止修改

### 2.2 允许修改项（须工单审批）

| 修改类型 | 审批要求 | 影响范围 |
|----------|----------|----------|
| 新增附件到 frozen 包 | 新工单 + manifest 版本升级 | manifest MD5 重算 |
| 基线导出脚本新增 | 本工单 T3 已处理 | 不影响冻结产物 |
| 风险台账状态更新 | 本工单 T2 已处理 | append-only |

### 2.3 冻结验证

```bash
# 验证冻结产物 MD5 未变
cd /home/ubuntu/framework-tree
for f in \
  analysis/e2e_output/v88/phase03/p1/dshe/p012_final_triplefix/frozen_p012_gate_package/v88_p012_full_link_cpu_compare.json \
  analysis/e2e_output/v88/phase03/p1/dshe/p012_final_triplefix/frozen_p012_gate_package/p012_gate_manifest.json; do
  md5sum "$f"
done
# 期望: C10D5A32ECCB... / A1BE00EA87FC...
```

---

## 3. 冻结理由

1. **路径修复已验证**：JSON 在门禁候选路径 `p1/dshe/cpu_peak_pct.json` → 已通过
2. **字段修复已验证**：9 个顶层扁平化字段 → 门禁正确读取 `cpu_peak_pct=99.4871`
3. **口径修复已验证**：`caliber="full_chain_business_steady_state"` → 口径拦截通过
4. **R3 E2E 8/8 PASS**：渲染功能无退化
5. **豁免申请已提交**：FAIL→WARN，等待 HERMEShf 审批

**结论**：当前 P0-12 交付物处于**稳定可审计状态**，禁止无工单修改。

---

## 4. 解冻条件

P0-12 产物在以下任一条件下可解冻：

| 条件 | 触发方 | 解冻范围 |
|------|--------|----------|
| HERMEShf 驳回豁免，要求重新优化 | DSHE | 采集脚本 + JSON 数据 |
| Phase04 CPU 阈值正式生效 (≤2.0%) | HERMEShf | 全套产物迁移至 Phase04 |
| psutil 系统级采集脚本部署完成 | DSHE | 新增 baseline_export.json |

解冻须在新工单中声明 `UNFREEZE_SCOPE` 和 `UNFREEZE_REASON`。

---

*Generated: 2026-10-16 UTC+8 | DSHE | commit b1987a4*
