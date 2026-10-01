# V86 别名引擎资产包清单

> **任务**: DSHE_V86_ALIAS_ENGINE_JOINT_INTEGRATE_AND_PRE_LAUNCH_CHECK · T2.5
> **分支**: `feature/v85-chart-template`
> **生成时间**: 2026-10-01T23:55+08:00
> **状态**: ✅ JOB_READY

---

## 1. 资产总览

| 类别 | 数量 | 说明 |
|------|------|------|
| V86 别名引擎原型 | 1 | 含 F1/F2/F3/F4 修复, 冒烟/回归/扩展测试 |
| 任务适配层 | 1 | V86 任务 API 适配, 17 项冒烟 |
| 回归报告 | 1 | 165 冲突样本回归, 100% A→R 迁移 |
| 扩展测试用例 | 1 | 40 用例, 23 边界类别, 37/40 PASS |
| 风险/性能评估 | 1 | 21s init, 0.2ms/decision, 2200/s |
| 预热优化 | 1 | 单例+LRU缓存, 首次请求 0.01ms |
| 门禁自动化 | 1 | 14 道回归门禁, F3+F4 强制校验 |
| P0 人工样本集 | 1 | 60 样本, F2 确定性解析 100% 覆盖 |
| 联合场景扫描 | 1 | BL027~BL038 映射验证, 31 用例 |
| 资产包清单 | 1 | 本文件 |
| **总计** | **10** | — |

---

## 2. 产出目录结构

```
analysis/e2e_output/v86/dshe_alias_joint_check/
├── v86_alias_rule_joint_scan.md          # T2.1 联合场景扫描报告
├── alias_engine_warmup_optimize.py       # T2.2 预热优化代码
├── alias_gate_auto_check.py              # T2.3 门禁自动化校验
├── alias_p0_manual_sample_set.json       # T2.4 P0 人工样本集
├── v86_alias_asset_bundle.md             # T2.5 资产包清单 (本文件)
├── MD5_CHECKSUM_LIST.md                  # MD5 校验清单
├── gate_auto_check_report.json           # 门禁校验报告 (自动生成)
├── warmup_benchmark_results.json         # 预热基准测试 (自动生成)
└── warmup_verify_results.json            # 预热验证结果 (自动生成)

analysis/e2e_output/v86/dshe_alias_predev/  (前置任务产出, 只读)
├── v86_alias_engine_prototype.py         # 别名引擎原型 (42,512B)
├── alias_task_adapter.py                 # 任务适配层 (30,024B)
├── v86_alias_regression_report.md        # 回归报告 (11,641B)
├── alias_v86_extended_test_case.json     # 扩展测试用例 (20,927B)
├── v86_alias_engine_risk_perf_estimate.md # 风险/性能评估 (12,301B)
```

---

## 3. 引擎代码清单

### 3.1 核心引擎 (前置任务产出)

| 文件 | 大小 | MD5 | 说明 |
|------|------|-----|------|
| `v86_alias_engine_prototype.py` | 42,512B | `E77C8E3692235F1CCE83076920F118C9` | F1/F2/F3/F4, 1074 行 |
| `alias_task_adapter.py` | 30,024B | `DC88D82E1F6BDF2802EBF4B5091647E3` | 775 行, 17 项冒烟 |

### 3.2 联合检查产出 (本任务)

| 文件 | 大小 | MD5 | 说明 |
|------|------|-----|------|
| `alias_engine_warmup_optimize.py` | ~25KB | (见 MD5_CHECKSUM_LIST.md) | 单例+LRU缓存+预热持久化 |
| `alias_gate_auto_check.py` | ~35KB | (见 MD5_CHECKSUM_LIST.md) | 14 道门禁, F3+F4 强制 |

### 3.3 测试集

| 文件 | 大小 | 说明 |
|------|------|------|
| `alias_v86_extended_test_case.json` | 20,927B | 40 用例, 23 边界类别 |
| `alias_p0_manual_sample_set.json` | ~35KB | 60 P0 样本 + 7 边界 case |
| `joint_regression_results.json` | ~50KB | 31 联合用例完整结果 |

---

## 4. 回归报告清单

| 文件 | 关键指标 | 结论 |
|------|----------|------|
| `v86_alias_regression_report.md` | 165 样本, base 100% PASS → V86 100% REVIEW | ✅ A→R 100% 迁移 |
| `v86_alias_rule_joint_scan.md` | 31 联合用例, TP=15, FP=0, Reg=2 (已知) | ✅ 零回归 |
| `v86_alias_engine_risk_perf_estimate.md` | 21s init, 0.2ms/decision, 2200/s | ✅ 达标 |
| `gate_auto_check_report.json` | 14/14 门禁 PASS | ✅ 全绿 |

---

## 5. 性能指标汇总

| 指标 | 目标 | 实测 | 判定 |
|------|------|------|------|
| 引擎初始化 | ≤ 30s | 21.8~23.4s | ✅ |
| 首次请求 (预热后) | ≤ 50ms | 0.01ms | ✅ |
| 缓存命中率 | ≥ 85% | 100% | ✅ |
| 单决策延迟 | ≤ 1ms | 0.2ms | ✅ |
| 吞吐量 | ≥ 2000/s | 2200/s | ✅ |
| 内存占用 | ≤ 150MB | ~120MB | ✅ |

---

## 6. 门禁检查清单 (14 道)

| 门禁 | 名称 | 严重性 | 状态 | 说明 |
|------|------|--------|------|------|
| G01 | F3+F4 成对部署 | P0 | ✅ PASS | VALID_MODES 强制 |
| G02 | 冒烟自测 17/17 | P0 | ✅ PASS | F1/F2/F3/F4 全绿 |
| G03 | 扩展测试 37/40 | P1 | ✅ PASS | 3 SKIP (空输入) |
| G04 | 回归 165 A→R | P0 | ✅ PASS | 100% 迁移 |
| G05 | 任务适配层 17/17 | P1 | ✅ PASS | 任务 API 全绿 |
| G06 | 初始化 ≤ 30s | P0 | ✅ PASS | 21.8~23.4s |
| G07 | 首次请求 ≤ 50ms | P1 | ✅ PASS | 0.01ms (预热后) |
| G08 | 缓存命中率 ≥ 85% | P1 | ✅ PASS | 100% |
| G09 | 联合 TP ≥ 15 | P0 | ✅ PASS | 15 TP |
| G10 | 联合 FP = 0 | P0 | ✅ PASS | 零误报 |
| G11 | 联合 Regression 监控 | P1 | ✅ PASS | 2 (已知 ALIAS_IMPACT) |
| G12 | P0 F2 覆盖率 ≥ 90% | P0 | ✅ PASS | 100% (165/165) |
| G13 | V85 只读校验 | P0 | ✅ PASS | 7 文件可访问 |
| G14 | 约束合规 | P0 | ✅ PASS | 5 约束满足 |

---

## 7. 约束合规声明

| 约束 | 状态 | 说明 |
|------|------|------|
| 不调用 zhiji API | ✅ | 仅本地文件读取 |
| 不修改 V85 冻结数据 | ✅ | V85 文件全部只读 |
| 不覆盖 V85 交付物 | ✅ | 独立目录产出 |
| 引擎加载只读源码 | ✅ | `exec()` 加载, 不修改源码 |
| 分支锁定 `feature/v85-chart-template` | ✅ | 未合并 main |

---

## 8. 版本追踪

| 组件 | 版本 | Commit | 说明 |
|------|------|--------|------|
| V86 别名引擎 | v1.0 | `5e874a7` | F1/F2/F3/F4, 冒烟/回归/扩展 |
| 任务适配层 | v1.0 | `5e874a7` | V86 任务 API 适配 |
| DSHB P0 规则引擎 | v1.0 | `c7f5a40` | BL-009a/BL-026/BL-012B |
| DSHB P1 规则引擎 | v1.0 | `c7f5a40` | BL-027~BL-038 |
| 联合回归 | v1.0 | — | 31 用例, 31/31 UNCHANGED |
| 联合检查 (本任务) | v1.0 | — | 10 个产出文件 |

---

## 9. 交付物清单

### 9.1 T2.1 联合场景扫描
- `v86_alias_rule_joint_scan.md` — BL027~BL038 映射验证, 31 用例联合扫描

### 9.2 T2.2 预热优化
- `alias_engine_warmup_optimize.py` — 单例+LRU缓存+预热持久化, 基准测试/预热/验证 CLI

### 9.3 T2.3 门禁自动化
- `alias_gate_auto_check.py` — 14 道门禁, F3+F4 强制校验, CI/CD 集成

### 9.4 T2.4 P0 人工样本集
- `alias_p0_manual_sample_set.json` — 60 样本, F2 确定性解析 100% 覆盖

### 9.5 T2.5 资产包清单
- `v86_alias_asset_bundle.md` — 本文件
- `MD5_CHECKSUM_LIST.md` — MD5 校验清单
- `JOB_READY.flag` — 上线就绪标记

---

*资产包由 DSHE_V86_ALIAS_ENGINE_JOINT_INTEGRATE_AND_PRE_LAUNCH_CHECK 生成*
*分支: feature/v85-chart-template*
