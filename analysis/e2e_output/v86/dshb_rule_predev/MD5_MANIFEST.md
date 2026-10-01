# V86 规则预研与BL回归测试交付物 MD5 校验清单

> 任务: DSHB_V86_RULE_ENGINE_PREDEV_AND_BL_REGRESSION_TEST
> 分支: feature/v85-chart-template
> 生成时间: 2026-10-01 22:00:00
> 基线commit: 6771406 (V85 Gate验收)
> B快照commit: da2a440 (V85持久快照)

---

## 交付物清单

| # | 文件 | 大小 | MD5 |
|---|------|------|-----|
| 1 | v86_bl_rule_regression_report.md | 20835 B | A589D347B95BFBC3C78AB9D3FF1E7AF8 |
| 2 | v86_p0_rule_prototype.py | 54747 B | ED099DCAD31B48503CE2197C27E80522 |
| 3 | v86_rule_test_suite.json | 26062 B | 45A7A06A135A03126BEE621E0907AD30 |
| 4 | v85_v86_rule_compare.py | 23770 B | FE746B2DB5EED241DCFE49723DE0EF29 |
| 5 | v86_rule_task_adapter.md | 18315 B | 5304A0A5ACD028371A95E9040563C790 |
| 6 | comparison_report.json | 2192 B | 7694694B19161BE027D202A2950CAB26 |

---

## 交付物摘要

| # | 交付物 | 说明 |
|---|--------|------|
| 1 | BL规则回归测试报告 | BL-009a/BL-026全量回归，P0拦截率88.2%→100%，0FP，0回归 |
| 2 | V86 P0规则原型代码 | 4项P0规则(BL-009a/BL-026/BL-012B/PDF修复)，22条自测全部通过 |
| 3 | 规则单元测试用例集 | 48条用例，13个测试组，覆盖全部4项P0规则 |
| 4 | V85/V86指标对比脚本 | 自动读取V85快照，与V86引擎对比，输出差异汇总 |
| 5 | 规则任务接入后端API适配文档 | 对接E的task_api_design，定义入参/出参/错误码/任务类型 |
| 6 | 对比结果报告 | 62条case对比，4项规则改动影响追踪 |

---

## 文件路径

```
analysis/e2e_output/v86/dshb_rule_predev/
├── v86_bl_rule_regression_report.md    (Deliverable 1)
├── v86_p0_rule_prototype.py            (Deliverable 2)
├── v86_rule_test_suite.json            (Deliverable 3)
├── v85_v86_rule_compare.py             (Deliverable 4)
├── v86_rule_task_adapter.md            (Deliverable 5)
├── comparison_report.json              (附加产出)
└── MD5_MANIFEST.md                     (本文档)
```

---

## 约束合规

- ✅ NO_ZHIJI_API_CALL=TRUE — 未调用任何zhiji API
- ✅ NO_MODIFY_SOURCE_TEMPLATE=TRUE — 未修改任何V85冻结文件
- ✅ V85核心规则只读 — 仅新增V86原型代码
- ✅ V86原型代码独立隔离 — 不覆盖V85生产逻辑
- ✅ 分支锁定 feature/v85-chart-template
- ✅ 对接E的V86 task_api_design (commit bcd64dd)

---

*本文档由DSHB Agent自动生成，用于V86规则预研交付物完整性校验。*
