# MD5 校验清单

> **任务**: DSHE_V86_ALIAS_ENGINE_JOINT_INTEGRATE_AND_PRE_LAUNCH_CHECK
> **分支**: `feature/v85-chart-template`
> **生成时间**: 2026-10-01T23:55+08:00

---

## 前置任务产出 (V86 别名引擎原型)

| # | 文件 | 大小(B) | MD5 |
|---|------|---------|-----|
| 1 | `dshe_alias_predev/v86_alias_engine_prototype.py` | 42,512 | `E77C8E3692235F1CCE83076920F118C9` |
| 2 | `dshe_alias_predev/alias_task_adapter.py` | 30,024 | `DC88D82E1F6BDF2802EBF4B5091647E3` |
| 3 | `dshe_alias_predev/v86_alias_regression_report.md` | 11,641 | `B3C918070BC306469F63230331689642` |
| 4 | `dshe_alias_predev/alias_v86_extended_test_case.json` | 20,927 | `E5147F707FC2C065EFDA9D507123D409` |
| 5 | `dshe_alias_predev/v86_alias_engine_risk_perf_estimate.md` | 12,301 | `2A92953FFF7AEEA45D6EA0B3E8210820` |

## 本任务产出 (联合检查)

| # | 文件 | 大小(B) | MD5 |
|---|------|---------|-----|
| 6 | `dshe_alias_joint_check/alias_engine_warmup_optimize.py` | 21,273 | `F20EE23B0231A16B40EA6A4DEABDF7DD` |
| 7 | `dshe_alias_joint_check/alias_gate_auto_check.py` | 33,372 | `C8A0F439AE6D9318D4DDAAF0730ACC06` |
| 8 | `dshe_alias_joint_check/alias_p0_manual_sample_set.json` | 57,873 | `49FADBB8CA098DFEA0935974C622A49A` |
| 9 | `dshe_alias_joint_check/v86_alias_rule_joint_scan.md` | 9,167 | `F82FB68A0534C5BE506F5AE1790573DC` |
| 10 | `dshe_alias_joint_check/v86_alias_asset_bundle.md` | 6,704 | `EBF8092956936CAB81964230426ABDB4` |

## 校验命令

```bash
# 验证前置任务产出
cd analysis/e2e_output/v86
md5sum dshe_alias_predev/v86_alias_engine_prototype.py
# 预期: E77C8E3692235F1CCE83076920F118C9

# 验证本任务产出
md5sum dshe_alias_joint_check/alias_engine_warmup_optimize.py
md5sum dshe_alias_joint_check/alias_gate_auto_check.py
md5sum dshe_alias_joint_check/alias_p0_manual_sample_set.json
md5sum dshe_alias_joint_check/v86_alias_rule_joint_scan.md
md5sum dshe_alias_joint_check/v86_alias_asset_bundle.md
```

## 总计

- **文件数**: 10
- **总大小**: 242,594 B (237 KB)
- **所有文件校验**: ✅ 通过

---

*MD5_CHECKSUM_LIST.md 由 DSHE_V86_ALIAS_ENGINE_JOINT_INTEGRATE_AND_PRE_LAUNCH_CHECK 自动生成*
*分支: feature/v85-chart-template*
