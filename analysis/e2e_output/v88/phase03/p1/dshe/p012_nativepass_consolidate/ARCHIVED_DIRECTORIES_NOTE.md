# 旧豁免材料归档说明

> **TASK_ID**: V88_PHASE03_P1_DSHE_P012_NATIVE_PASS_CONSOLIDATE_AND_SYNC_JOB / T0
> **AGENT**: DSHE | **BRANCH**: feature/v88-g1
> **生成时间**: 2026-10-16T20:39 UTC+8

---

## 1. 归档操作

| 目录 | 原路径 | 归档后路径 | 操作类型 |
|------|--------|-----------|:--------:|
| CPU 阈值豁免材料 | `p012_cpu_exception/` | `p012_cpu_exception_ARCHIVED/` | 重命名 |
| 跨 Agent 对齐材料 | `cross_align/` | `cross_align_ARCHIVED/` | 重命名 |

---

## 2. 归档原因

P0-12 门禁已从**豁免路径**转为**原生 PASS 路径**：

1. **原豁免路径**（已废弃）：
   - `cpu_peak_pct=99.4871%`（`time.process_time()` 进程级口径）
   - 申请 FAIL→WARN 豁免（R-V88-034 = EXEMPTION_REQUESTED）
   - 等待 HERMEShf 审批

2. **新原生 PASS 路径**（当前有效）：
   - `cpu_peak_pct=0.0654%`（`psutil.cpu_times()` 系统级稳态口径）
   - 三重修正：路径 + 结构 + 口径全部修复
   - 无需豁免，直接通过 P0-12 门禁（0.0654% ≤ 1.75%）
   - R3 E2E 8/8 PASS，4 轮独立验证可复现

---

## 3. 保留说明

- **不物理删除**：所有历史文件完整保留在归档目录中
- **可追溯**：旧豁免申请材料可通过 git 历史追溯（commits `b1987a4`, `8523a19`）
- **新基线**：当前有效的 P0-12 交付物统一存放于 `p012_nativepass_consolidate/`

---

## 4. 影响范围

| 受影响项 | 状态 |
|----------|------|
| R-V88-034 状态 | `EXEMPTION_REQUESTED` → `CLOSED` |
| HERMEShf 豁免审计工单 | 无需处理（不再需要审批） |
| 跨 Agent SOP | 旧 `cross_agent_exemption_sop.md` 已废弃，新 `cross_agent_post_nativepass_sop.md` 已生效 |
| 基线导出 | 已刷新为 v1.4.0-cpu-triple-fix 基线 |

---

*Generated: 2026-10-16 UTC+8 | DSHE | 旧豁免材料归档说明*
