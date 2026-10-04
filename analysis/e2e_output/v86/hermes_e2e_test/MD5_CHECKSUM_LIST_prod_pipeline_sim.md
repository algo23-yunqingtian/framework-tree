# MD5 校验清单 — V86-RC2 三级流水线仿真 + Gate 预审 + 审计规则验证

> **工单**: 工单-HERMES / T3.1~T3.4 产物
> **分支**: `feature/v85-chart-template`
> **生成日期**: 2026-10-06
> **约束**: NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE

---

## 1. 本轮新增产物（4 份）

| 文件 | MD5 | 字节 |
|------|-----|------|
| `v86_rc2_hermes_pipeline_e2e_simulation_report.md` | `67b386cc4649f765ecc97c341722bb06` | 13783 |
| `v86_rc2_hermes_gate_simulation_report.md` | `17056c46b05c2d6fb0a6df4bd6144b4e` | 11929 |
| `v86_rc2_hermes_audit_rule_validation_report.md` | `fc06c13696e66261ea3332e382bc10b2` | 14279 |
| `v86_rc2_hermes_dep_gate_logic_verify.md` | `e9bf5269a7bacb3af08325f5a6a74399` | 12850 |

> MD5 计算命令：`md5sum <文件>`（在 `hermes_e2e_test/` 目录下）

---

## 2. 旧产物零覆盖验证（NO_OVERWRITE=TRUE 自证）

上轮（commit `fd429f4`）5 份核心规范文档的 MD5，本轮交付前后逐条比对，**全部一致**，
证明本轮未改动任何既有归档产物：

| 文件 | 上轮 MD5（fd429f4） | 本轮实测 MD5 | 是否一致 |
|------|---------------------|-------------|---------|
| `v86_rc2_hermes_audit_canonical_spec.md` | `0634790f4500267837414daa333d6ec4` | `0634790f4500267837414daa333d6ec4` | ✅ |
| `v86_rc2_hermes_cross_agent_pipeline_spec.md` | `77b12c635050f7d78546a46e0f394277` | `77b12c635050f7d78546a46e0f394277` | ✅ |
| `v86_rc2_hermes_external_dependency_management_spec.md` | `583b1b47f8d86f8dbf3226b396aabfb9` | `583b1b47f8d86f8dbf3226b396aabfb9` | ✅ |
| `v86_rc2_hermes_gate_review_revised_spec.md` | `598b0f42332fa2b0e21fe9a8bc17c7d0` | `598b0f42332fa2b0e21fe9a8bc17c7d0` | ✅ |
| `v86_rc2_hermes_agent_collaboration_summary.md` | `39baa0118d81913d69dfccc15ccfe452` | `39baa0118d81913d69dfccc15ccfe452` | ✅ |

**零覆盖结论**：5/5 一致 → NO_OVERWRITE 约束满足。本轮仅新增，未改动既有文档。

---

## 3. V85 基线零改动验证（NO_MODIFY_V85=TRUE 自证）

本轮仅新增 `analysis/e2e_output/v86/hermes_e2e_test/` 下的 .md 文档，
未触碰 V85 业务代码目录（`scripts/`、`data/`、`*.html`、`chart_kits.py`）。

验证命令：
```bash
git status -s | grep -E '\.(html|py|js)$|data/'   # 应无 V85 业务文件变更
```

---

## 4. 状态标记

```
HERMES_PROD_PHASE_PIPELINE_SIM_DONE=TRUE
```

**标记依据（T5 完成标准全部满足）**：
- ✅ 三级流水线 4 类场景 E2E 仿真全部完成（T3.1）
- ✅ Gate G01~G10 仿真验证完成，G-09/G-10 强制拦截生效（T3.2）
- ✅ 审计规则可成功拦截旧口径混淆提交，告警输出清晰（T3.3）
- ✅ DEP_BLOCK 分类与 Gate 判定逻辑验证无误（T3.4）
- ✅ 会话交接文档更新完成（T3.5）
- ✅ 全部产物入库，MD5 校验 PASS

---

*本清单由 HERMES 生成于 V86-RC2 三级流水线仿真 + Gate 预审 + 审计规则验证完成后。*
