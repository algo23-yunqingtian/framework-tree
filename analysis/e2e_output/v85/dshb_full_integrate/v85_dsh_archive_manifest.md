# V85 DSH侧归档清单 + MD5

**生成时间**: 2026-10-01 12:00:18
**任务**: DSH-B_V85_FULL_CHAIN_INTEGRATE_VALIDATE_AND_FINAL_GATE_PREP
**归档路径**: analysis/e2e_output/v85/dshb_full_integrate/
**文件总数**: 9

---

## 归档文件清单

| # | 文件名 | 大小 | MD5 |
|---|--------|------|-----|
| 1 | semantic_blacklist_v85_final.json | 64,798 B | `1e1bdf48a7734bce50df263ce4c3ef1a` |
| 2 | blacklist_change_log.md | 5,879 B | `e950ba3864b9e9059f17624f2432f3c8` |
| 3 | full_488_template_playback_result.csv | 433,488 B | `68dcb7cd9bd4355e7245bc10f06b0644` |
| 4 | inconsistent_risk_items.csv | 3,610 B | `1c94b0c22c19dfbe32c753fb110ed5c6` |
| 5 | inconsistent_risk_item.md | 2,754 B | `86bf6a4567fd9973f9db01e5897ad41f` |
| 6 | cross_variety_p0_validation.csv | 5,356 B | `d550bfb8de713dd9d137d66a05c4279c` |
| 7 | whitelist_approval_note.md | 4,467 B | `6cc5f7fa056c22043538099c005d856d` |
| 8 | dsh_gate_self_check.md | 5,097 B | `c12b3e1c428107338ea01fc58ffd6bd0` |
| 9 | build_full_integrate.py | 47,359 B | `f3f0a3e85b91eafcc3c76dff8b547f08` |

---

## 文件用途说明

| 文件名 | 用途 |
|--------|------|
| semantic_blacklist_v85_final.json | V85最终版语义黑名单（31条规则+409条DSHE辅助） |
| blacklist_change_log.md | 黑名单变更日志（记录每条新增/修改条目） |
| full_488_template_playback_result.csv | 488模板全量回放对比结果 |
| inconsistent_risk_items.csv | 风险库与规则一致性校验明细 |
| inconsistent_risk_item.md | 风险库与规则一致性分析报告 |
| cross_variety_p0_validation.csv | 34条跨品种P0案例拦截验证 |
| whitelist_approval_note.md | RISK-005白名单复核说明 |
| dsh_gate_self_check.md | DSHB侧Gate自检报告（5项硬性条件） |
| build_full_integrate.py | 构建脚本（可重复执行） |

---

## 归档完整性校验

| 校验项 | 结果 |
|--------|------|
| 文件数量 | 9个文件 |
| MD5校验 | 全部文件已计算MD5 |
| 编码 | UTF-8（CSV含BOM） |
| 约束声明 | NO_PRODUCTION_MODIFICATION=true |

---

**约束声明**: NO_PRODUCTION_MODIFICATION=true, NO_SOURCE_MODIFICATION=true, NO_GT_MODIFICATION=true, NO_ZHIJI_API_CALL=true
