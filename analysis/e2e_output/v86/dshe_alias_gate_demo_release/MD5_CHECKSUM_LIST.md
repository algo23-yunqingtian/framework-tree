# V86 别名引擎 Gate 演示 + Release Note — MD5 校验清单

> 任务: `DSHE_V86_ALIAS_GATE_DEMO_ASSEMBLY_AND_RELEASE_NOTE_COMPILE` · T2.5
> 分支: `feature/v85-chart-template`
> 基线 Commit: `d1e070d`
> 资产版本: `v86.0.0-frozen`
> 生成时间: 2026-10-02

---

## V86 别名引擎 — Gate 演示+Release Note 产出 (dshe_alias_gate_demo_release)

| MD5 | 大小 (B) | 文件 |
|-----|----------|------|
| F144F7E66017340C17F7E0C53838F12D | 33,335 | `dshe_alias_gate_demo_release/v86_alias_gate_demo_package.md` |
| 56771CA9E1D1680C4438818DF2F95E48 | 26,018 | `dshe_alias_gate_demo_release/v86_alias_release_note_final.md` |
| BD79A43B9B331E7DC357BE58634D1A4D | 23,581 | `dshe_alias_gate_demo_release/v86_alias_gate_qakb.md` |
| E20C84994378121B35F78A58E90B6413 | 20,162 | `dshe_alias_gate_demo_release/v86_alias_portal_data_cross_check.md` |
| — | — | `dshe_alias_gate_demo_release/MD5_CHECKSUM_LIST.md` (本文件) |

## 全局

| MD5 | 大小 (B) | 文件 |
|-----|----------|------|
| 78F283B5A2F40191167E31355704E033 | 7,938 | `JOB_READY.flag` |

---

## 校验命令

```bash
# 从 dshe_alias_gate_demo_release 目录验证
cd analysis/e2e_output/v86/dshe_alias_gate_demo_release
# 使用 MD5_CHECKSUM_LIST.md 中的 MD5 列表
```

---

## 汇总

| 类别 | 文件数 | 总大小 |
|------|--------|--------|
| Gate 演示包 | 1 | 33,335B |
| Release Note | 1 | 26,018B |
| Gate 问答知识库 | 1 | 23,581B |
| 门户交叉核验 | 1 | 20,162B |
| MD5 清单 | 1 | — |
| JOB_READY.flag | 1 | 7,938B |
| **总计** | **6** | **~111,034B** |

---

## 前置交付资产索引 (MD5)

| 资产 | MD5 | 文件 |
|------|-----|------|
| 引擎原型 | E77C8E3692235F1CCE83076920F118C9 | `v86_alias_engine_prototype.py` |
| 任务适配层 | DC88D82E1F6BDF2802EBF4B5091647E3 | `alias_task_adapter.py` |
| 预热优化 | 48EB5AC0ADE4ACBB1FD1FA8C9DE29609 | `alias_engine_warmup_optimize.py` |
| 门禁自动化 | C8A0F439AE6D9318D4DDAAF0730ACC06 | `alias_gate_auto_check.py` |
| P0 人工样本集 | 49FADBB8CA098DFEA0935974C622A49A | `alias_p0_manual_sample_set.json` |
| 联合场景扫描 | F82FB68A0534C5BE506F5AE1790573DC | `v86_alias_rule_joint_scan.md` |
| 全量回放 | 421B93B765967E533496F7FFF53A18A6 | `v86_alias_full_replay.py` |
| 回放报告 | 016A79BE90D8D08A9ED4218E5A84C935 | `v86_alias_full_replay_report.md` |
| 生产部署包 | 054EAC866B350727BAFC15BBF36D4A46 | `v86_alias_production_bundle.md` |
| 灰度方案 | C2F029CC434DFF473D2542584517D5F3 | `v86_alias_gray_release_plan.md` |
| 降级预案 | A8473607D2BFFC31D5C11D8352EC550D | `v86_alias_degrade_plan.md` |
| 监控规范 | 510A4CFC196B4D301EE3E23301A9DFE0 | `v86_alias_monitor_spec.md` |
| 集成校验 | C6273225803A593469122E90068B81EF | `v86_alias_prod_integrate_verify_report.md` |
| 灰度仿真 | 75487A8F1448C7DAE7A1C9E6936074E8 | `v86_alias_gray_full_simulation.md` |
| 运维手册 | E1EFAA2C8A26FA08233784759C1614F2 | `v86_alias_ops_manual_final.md` |
| 仿真脚本 | 139C3A4C01ADD90536078759370F6324 | `gray_simulation_runner.py` |
| 仿真结果 | C584460D50C1D6D0AE16D8C7EC7C9AC9 | `gray_simulation_results.json` |

---

*MD5 清单由 DSHE_V86_ALIAS_GATE_DEMO_ASSEMBLY_AND_RELEASE_NOTE_COMPILE T2.5 生成*
*分支: feature/v85-chart-template · Commit: d1e070d · 资产版本: v86.0.0-frozen*
