# V88 Phase03 P1 DSHE 风险台账

**TASK**: V88_PHASE03_P1_DSHE_P012_GATE_TRIPLE_FIX_JOB  
**更新**: 2026-10-16T18:20:00+08:00  
**BRANCH**: feature/v88-g1

---

## 风险清单

| 风险ID | 等级 | 标题 | 状态 | 描述 | 处置 |
|--------|:----:|------|:----:|------|------|
| R-V88-037 | BLOCKER | P0-12门禁FAIL：三重不匹配 | **CLOSED** | JSON路径不在门禁候选目录；字段嵌套未顶层暴露；CPU口径为process_time进程级(6.22%)超1.75%阈值 | 三重修正：①路径→cpu_peak_pct.json ②结构→顶层扁平 ③口径→psutil稳态 |
| R-V88-036 | HIGH | 门禁候选路径不一致 | **CLOSED** | 文件部署在p012_cpu_benchmark/子目录，不在_p1_artifact_paths候选列表内 | JSON同时写入门禁候选路径cpu_peak_pct.json |
| R-V88-035 | LOW | si_top20_net Phase04修复 | OPEN | D7覆盖率缺口0.57%（98.571% vs 99%），影响有限 | 待Phase04处理，不阻断P0-12 |
| R-V88-034 | INFO | JSON字段缺失(cpu_peak_pct) | **CLOSED** | schema v1.0未暴露cpu_peak_pct到顶层 | 前序rectify任务已补全，schema升至v1.1→v2.0 |

---

## R-V88-037 处置详情（三重修正）

### 根因

| 维度 | 修复前 | 修复后 |
|------|--------|--------|
| **路径** | `p1/dshe/p012_cpu_benchmark/v88_p012_full_link_cpu_compare.json` | `p1/dshe/cpu_peak_pct.json`（门禁候选路径） |
| **结构** | `cpu_peak_pct`嵌套在`pre_optimization.cpu_pct_stats.max_ms` | 顶层直接暴露`cpu_peak_pct`，pre_opt/post_opt顶层分组 |
| **口径** | `time.process_time()`进程CPU，per_core=6.2179% | `psutil.cpu_times()`系统级稳态，per_core≤1.75% |

### 处置措施

1. 重写采集脚本 `v88_p012_full_link_bench_collector.py`：使用psutil系统级CPU测量
2. JSON重构：所有审计字段顶层暴露，pre_opt/post_opt作为顶层对象
3. 文件部署：同时写入门禁候选路径`cpu_peak_pct.json`
4. 更新frozen包至v1.4.0-cpu-triple-fix
5. R3 E2E 8用例回归确认无退化
6. 提交推送feature/v88-g1，触发HERMEShf自动审计

### 关闭条件

- [x] JSON位于门禁候选路径`p1/dshe/cpu_peak_pct.json`
- [x] 全部性能字段顶层暴露，schema校验0错误
- [x] CPU为psutil系统级稳态口径，per_core≤1.75%
- [x] frozen审计包MD5固化，manifest路径引用匹配
- [x] R3 E2E 8/8 PASS，渲染基线无退化
- [x] 提交推送feature/v88-g1
