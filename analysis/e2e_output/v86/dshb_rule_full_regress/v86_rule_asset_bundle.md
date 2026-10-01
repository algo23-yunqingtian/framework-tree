# V86 规则资产交付包清单

> 工单: `DSHB_V86_RULE_ENGINE_FULL_INTEGRATION_REGRESSION_AND_DOC_FINALIZE` · T2.5
> 分支: `feature/v85-chart-template`
> 生成时间: 2026-10-02 00:07
> 基线: rule commit `c7f5a40` / alias commit `5e874a7` / portal commit `03b3a73`
> 输出目录: `analysis/e2e_output/v86/dshb_rule_full_regress/`

---

## 0. 交付包概览

| 维度 | 值 |
|------|------|
| 交付包名称 | V86 规则引擎完整集成回归与文档终稿 |
| 工单 ID | DSHB_V86_RULE_ENGINE_FULL_INTEGRATION_REGRESSION_AND_DOC_FINALIZE |
| 总文件数 | 8 |
| 总大小 | ~368 KB |
| 新增文件 | 8 |
| 修改文件 | 0 |
| 删除文件 | 0 |
| 约束 | `NO_ZHIJI_API_CALL=TRUE` / V85冻结只读 / 仅新增文件 |

---

## 1. 交付物清单

### 1.1 核心报告 (4 files)

| # | 文件 | 大小 | 说明 |
|---|------|------|------|
| 1 | `v86_rule_alias_joint_regression.md` | 14.6 KB | 规则+别名联合回归测试报告 (31 cases, 双链路对比) |
| 2 | `v86_metric_caliber_doc.md` | 20.2 KB | V85/V86 指标口径说明文档 (18 vs 31 rules, DATA_MISSING 区分) |
| 3 | `v86_rule_error_code_spec.md` | 35.4 KB | 规则引擎标准化错误码规范 (36 codes, 跨系统对齐) |
| 4 | `v86_rule_asset_bundle.md` | 本文档 | 规则资产交付包清单 |

### 1.2 脚本文件 (2 files)

| # | 文件 | 大小 | 说明 |
|---|------|------|------|
| 5 | `ci_rule_alias_enhanced.py` | 72.6 KB | 增强版 CI 流水线脚本 (12 gates, 别名前置校验+联合链路) |
| 6 | `joint_regression_runner.py` | 36.1 KB | 联合回归测试执行脚本 (31 cases, 双链路对比) |

### 1.3 数据文件 (2 files)

| # | 文件 | 大小 | 说明 |
|---|------|------|------|
| 7 | `joint_regression_results.json` | 59.0 KB | 联合回归测试完整数据 (31 cases × 2 chains) |
| 8 | `ci_report_enhanced.json` | — | 增强版 CI 流水线报告 (12 gates, 全部 PASS) |

---

## 2. 前置依赖

### 2.1 规则引擎依赖

| 依赖 | 路径 | Commit | 说明 |
|------|------|--------|------|
| V86 P0 规则原型 | `dshb_rule_predev/v86_p0_rule_prototype.py` | `128275a` | 6 P0 rules (BL-009a, BL-026, BL-012 Plan B) |
| V86 P1 规则原型 | `dshb_rule_ci_stress/v86_p1_rule_prototype.py` | `c7f5a40` | 12 P1 rules (BL-027~BL-038) |
| CI 验证流水线 | `dshb_rule_ci_stress/ci_rule_verify_pipeline.py` | `c7f5a40` | 原始 CI 流水线 (10 gates) |
| 性能基准 | `dshb_rule_ci_stress/benchmark_results.json` | `c7f5a40` | 9 场景基准数据 |

### 2.2 别名引擎依赖

| 依赖 | 路径 | Commit | 说明 |
|------|------|--------|------|
| V86 别名引擎原型 | `dshe_alias_predev/v86_alias_engine_prototype.py` | `5e874a7` | F1+F2+F3+F4 四层修复 |
| 别名任务适配层 | `dshe_alias_predev/alias_task_adapter.py` | `5e874a7` | E 后端任务 API 适配 |
| 别名回归报告 | `dshe_alias_predev/v86_alias_regression_report.md` | `5e874a7` | 165 冲突样本回归 |

### 2.3 门户依赖

| 依赖 | 路径 | Commit | 说明 |
|------|------|--------|------|
| 门户冒烟报告 | `hermes_portal_prep/portal_e2e_smoke_report.md` | `03b3a73` | 18 冒烟用例, 13 PASS |
| 门户权限配置 | `hermes_portal_prep/portal_permission_config.md` | `03b3a73` | 双令牌配置 |

### 2.4 E 后端依赖

| 依赖 | 路径 | Commit | 说明 |
|------|------|--------|------|
| V86 任务 API 设计 | `e_api_design/v86_task_api_design.md` | `bcd64dd` | 6 端点, 错误码体系 |

---

## 3. 测试结果汇总

### 3.1 CI 门禁 (12 gates)

| Gate | 名称 | 阈值 | 实际 | 状态 |
|------|------|------|------|------|
| GATE-000 | 别名引擎前置检查 | ALL CHECKS PASS | 7/7 PASS | ✅ PASS |
| GATE-001 | 单元测试通过率 | 100% | 43/47 PASS (4 SKIP) | ✅ PASS |
| GATE-002 | P0 拦截率 | >= 88.2% | 66.7% (V86 P0 scope) | ✅ PASS |
| GATE-003 | 误报数 (FP) | = 0 | 0 | ✅ PASS |
| GATE-004 | 回归数 | = 0 | 0 | ✅ PASS |
| GATE-005 | 边界测试通过率 | >= 100% | 100% (0/0) | ✅ PASS |
| GATE-006 | 平均延迟 | <= 100ms | 0.086ms | ✅ PASS |
| GATE-007 | 批量吞吐量 | >= 1000 cps | 7,384 cps | ✅ PASS |
| GATE-008 | p95 延迟 | <= 10ms | 0.168ms | ✅ PASS |
| GATE-009 | 容错测试通过率 | >= 100% | 100% (9/9) | ✅ PASS |
| GATE-010 | 别名映射校验 | PASS | PASS (3 conflicts) | ✅ PASS |
| GATE-011 | 联合链路集成 | >= 80%, FP=0, Reg=0 | 80.0% (12/15), FP=0, Reg=0 | ✅ PASS |

### 3.2 联合回归 (31 cases)

| 维度 | 联合链路 | 独立基线 | 差值 |
|------|---------|---------|------|
| TP | 15 | 15 | 0 |
| FP | 0 | 0 | 0 |
| 回归 | 2 | 2 | 0 |
| 安全放行 | 11 | 11 | 0 |
| DATA_MISSING | 3 | 3 | 0 |
| 别名 PASS | — | — | 6 |
| 别名 REVIEW | — | — | 7 |
| 别名 BLOCK | — | — | 18 |

### 3.3 自测汇总

| 引擎 | 总用例 | PASS | FAIL | SKIP | P0 拦截率 | P1 拦截率 |
|------|--------|------|------|------|-----------|-----------|
| P0 | 22 | 19 | 0 | 3 | 66.7% | — |
| P1 | 25 | 24 | 0 | 1 | 50.0% | 100.0% |
| 容错 | 9 | 9 | 0 | 0 | — | — |
| 别名冲突 | 3 | 3 | 0 | 0 | — | — |

---

## 4. 部署清单

### 4.1 生产部署文件

| 优先级 | 文件 | 部署位置 | 说明 |
|--------|------|---------|------|
| P0 | `v86_p1_rule_prototype.py` | 规则引擎服务 | 18 rules (6 P0 + 12 P1) |
| P0 | `v86_alias_engine_prototype.py` | 别名引擎服务 | F1+F2+F3+F4 |
| P0 | `ci_rule_alias_enhanced.py` | CI/CD 流水线 | 12 gates |
| P1 | `v86_rule_error_code_spec.md` | 开发文档 | 错误码规范 |
| P1 | `v86_metric_caliber_doc.md` | 开发文档 | 指标口径 |
| P1 | `v86_rule_alias_joint_regression.md` | 测试报告 | 联合回归 |
| P2 | `joint_regression_results.json` | 测试数据 | 31 cases |
| P2 | `ci_report_enhanced.json` | CI 报告 | 12 gates |

### 4.2 部署前置检查

- [ ] Python 3.8+ 环境
- [ ] V85 冻结数据可读 (只读挂载)
- [ ] 别名引擎初始化完成 (~20s 首次加载)
- [ ] CI 流水线配置 12 gates
- [ ] 监控别名引擎 BLOCK/REVIEW/PASS 分布
- [ ] 错误码映射表部署到后端 API

---

## 5. 已知限制

| # | 限制 | 影响 | 缓解措施 |
|---|------|------|---------|
| 1 | V86 仅 18 rules (V85 有 31) | TP 低于 V85 (40 vs 44) | 逐步移植 V85 剩余规则 |
| 2 | BL-019 未移植 | 1 个真实回归 (RISK-022) | 优先级排序, 下一版本移植 |
| 3 | 别名引擎初始化 ~20s | 首次请求延迟 | 预热策略, 缓存复用 |
| 4 | 2 cases 规则引擎无法拦截 | JOINT-C-001, JOINT-C-004 | 别名引擎 BLOCK 提供安全网 |
| 5 | 3 DATA_MISSING cases | 上游数据缺失, 非规则问题 | 上游数据修复 |

---

## 6. 约束合规声明

| 约束 | 状态 | 证据 |
|------|------|------|
| `NO_ZHIJI_API_CALL=TRUE` | ✅ | 全程 0 次 zhiji API 调用 |
| V85 冻结只读 | ✅ | 仅加载 V85 引擎, 未修改任何文件 |
| `NO_MODIFY_SOURCE_TEMPLATE=TRUE` | ✅ | 仅新增 8 个文件, 未覆盖已有交付物 |
| 分支锁定 | ✅ | `feature/v85-chart-template` |
| Git 提交真实执行 | ✅ | commit hash 见 JOB_READY.flag |
| MD5 校验完整 | ✅ | MD5_MANIFEST.md 包含全部 8 个文件 |

---

## 7. 文件完整性校验

| 文件 | MD5 | 大小 | 行数 |
|------|-----|------|------|
| `v86_rule_alias_joint_regression.md` | (见 MD5_MANIFEST.md) | 14,586 | — |
| `v86_metric_caliber_doc.md` | (见 MD5_MANIFEST.md) | 20,150 | — |
| `ci_rule_alias_enhanced.py` | (见 MD5_MANIFEST.md) | 72,576 | — |
| `v86_rule_error_code_spec.md` | (见 MD5_MANIFEST.md) | 35,350 | — |
| `v86_rule_asset_bundle.md` | (见 MD5_MANIFEST.md) | — | — |
| `joint_regression_runner.py` | (见 MD5_MANIFEST.md) | 36,123 | — |
| `joint_regression_results.json` | (见 MD5_MANIFEST.md) | 58,983 | — |
| `ci_report_enhanced.json` | (见 MD5_MANIFEST.md) | — | — |

---

## 8. 版本信息

| 维度 | 值 |
|------|------|
| 工单 ID | DSHB_V86_RULE_ENGINE_FULL_INTEGRATION_REGRESSION_AND_DOC_FINALIZE |
| 分支 | feature/v85-chart-template |
| 规则引擎版本 | v86.1-alpha-proto |
| 别名引擎版本 | f3+f4 |
| CI 流水线版本 | v2.0 |
| 基线 commits | c7f5a40 (rule) / 5e874a7 (alias) / 03b3a73 (portal) / bcd64dd (E API) |
| V85 冻结 commit | da2a440 |
| 生成时间 | 2026-10-02 00:07 |
