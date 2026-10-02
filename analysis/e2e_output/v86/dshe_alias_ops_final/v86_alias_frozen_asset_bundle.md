# V86 别名资产固化包清单 + MD5 校验

> 任务: `DSHE_V86_ALIAS_PROD_INTEGRATE_ADAPT_GRAY_SIMULATION_AND_OPS_MANUAL_FINAL` · T2.4
> 分支: `feature/v85-chart-template`
> 基线 Commit: `81268a6`
> 资产冻结时间: 2026-10-02
> 资产版本: `v86.0.0-frozen`

---

## 1. 资产包总览

| 类别 | 文件数 | 总大小 | 状态 |
|------|--------|--------|------|
| V86 别名引擎代码 | 2 | 72,536B | ✅ 已固化 |
| V86 任务适配层 | 1 | 30,024B | ✅ 已固化 |
| V86 测试用例集 | 1 | 20,927B | ✅ 已固化 |
| V86 回归报告 | 1 | 11,641B | ✅ 已固化 |
| V86 性能评估 | 1 | 12,301B | ✅ 已固化 |
| V86 预热优化 | 1 | 21,479B | ✅ 已固化 |
| V86 门禁自动化 | 1 | 33,372B | ✅ 已固化 |
| V86 P0 人工样本集 | 1 | 57,873B | ✅ 已固化 |
| V86 联合场景扫描 | 1 | 9,167B | ✅ 已固化 |
| V86 资产包清单 | 1 | 6,704B | ✅ 已固化 |
| V86 全量回放脚本 | 1 | 25,076B | ✅ 已固化 |
| V86 全量回放报告 | 1 | 6,580B | ✅ 已固化 |
| V86 生产部署包 | 1 | 17,385B | ✅ 已固化 |
| V86 灰度上线方案 | 1 | 13,218B | ✅ 已固化 |
| V86 故障降级预案 | 1 | 14,871B | ✅ 已固化 |
| V86 监控指标规范 | 1 | 17,364B | ✅ 已固化 |
| 生产启动脚本 | 1 | 2,063B | ✅ 已固化 |
| 依赖清单 | 1 | 232B | ✅ 已固化 |
| 缓存配置模板 | 1 | 579B | ✅ 已固化 |
| Dockerfile | 1 | 857B | ✅ 已固化 |
| 灰度仿真脚本 | 1 | 29,140B | ✅ 已固化 |
| 灰度仿真结果 | 1 | 25,039B | ✅ 已固化 |
| 集成适配校验报告 | 1 | 21,750B | ✅ 已固化 |
| 灰度仿真演练记录 | 1 | 17,072B | ✅ 已固化 |
| 运维手册终稿 | 1 | 29,923B | ✅ 已固化 |
| 资产固化包清单 | 1 | — (本文件) | ✅ 已固化 |
| MD5 校验清单 | 1 | — (见 MD5_CHECKSUM_LIST.md) | ✅ 已固化 |
| **总计** | **28** | **~538,137B** | **✅ 全部固化** |

---

## 2. 别名库资产

### 2.1 V85 别名库 (只读冻结)

| 属性 | 值 |
|------|-----|
| 来源 | V85 别名引擎基线库 |
| 条目数 | 4,643 条 |
| 去重 canonical_key | 1,818 个 |
| 覆盖品种 | LI/NI/SI/SN/ZN/AL/PB/CU/AO 等 10+ |
| 读取方式 | `exec()` 加载, 只读 |
| MD5 | 见 V85 MD5_MANIFEST.md |
| 冻结状态 | ✅ 只读, 不可修改 |

### 2.2 V86 别名库映射规则

| 规则 | 说明 | 版本 |
|------|------|------|
| F1 异常兜底 | KeyError 安全捕获, 别名未命中返回 NO_MATCH | v86.0.0 |
| F2 确定性解析 | 别名→canonical_key 唯一/歧义/未匹配分类 | v86.0.0 |
| F3 门禁重排 | R-05 黑名单优先于 R-07 别名精确匹配 | v86.0.0 |
| F4 自触发抑制 | 同名对子串包含/复合短语抑制 | v86.0.0 |
| 模式切换 | base / f3 / f3+f4 三档 | v86.0.0 |
| 运行时降级 | L0→L1→L2→L3 四级降级 | v86.0.0 |

### 2.3 V86 别名库性能基线

| 指标 | 值 |
|------|-----|
| 引擎初始化 (f3+f4) | 22,739ms |
| 单条裁决耗时 | 0.143ms |
| 吞吐 | 2,144 entries/s |
| 缓存命中率 | 100% |
| 内存占用 | ~128MB |
| F2 UNIQUE | 2,713 (58.43%) |
| F2 AMBIGUOUS | 165 (3.55%) |
| F2 NO_MATCH | 1,751 (37.71%) |
| F2 UNREGISTERED | 14 (0.30%) |
| F3 R-05 触发 | 2 |
| F4a 抑制 | 132 |
| F4b 抑制 | 46 |
| 长尾歧义 | 34 |

---

## 3. 样本集资产

### 3.1 P0 人工样本集

| 属性 | 值 |
|------|-----|
| 文件 | `alias_p0_manual_sample_set.json` |
| 样本数 | 60 条 |
| F2 覆盖率 | 100% (165/165 AMBIGUOUS 样本) |
| 人工复核 | 47 条 |
| 可自动解析 | 13 条 |

### 3.2 扩展测试用例集

| 属性 | 值 |
|------|-----|
| 文件 | `alias_v86_extended_test_case.json` |
| 用例数 | 40 条 |
| 边界类别 | 23 种 |
| 通过 | 37/40 |
| 跳过 | 3 (空输入) |

### 3.3 联合回归样本集

| 属性 | 值 |
|------|-----|
| 文件 | `joint_regression_results.json` |
| 联合用例 | 31 条 |
| TP (真阳性) | 15 |
| FP (假阳性) | 0 |
| Regression | 2 (已知 ALIAS_IMPACT) |

### 3.4 全量回放样本集

| 属性 | 值 |
|------|-----|
| 文件 | `replay_results.json` |
| 条目数 | 4,643 |
| base PASS | 4,603 (99.14%) |
| f3+f4 PASS | 4,476 (96.40%) |
| f3+f4 REVIEW | 165 (3.55%) |
| f3+f4 BLOCK | 2 (0.04%) |

---

## 4. 生产部署资产

### 4.1 部署包文件

| 文件 | 大小 | MD5 | 说明 |
|------|------|-----|------|
| `v86_alias_engine_prototype.py` | 42,512B | `E77C8E3692235F1CCE83076920F118C9` | 核心引擎 |
| `alias_task_adapter.py` | 30,024B | `DC88D82E1F6BDF2802EBF4B5091647E3` | 任务适配层 |
| `alias_engine_warmup_optimize.py` | 21,479B | `48EB5AC0ADE4ACBB1FD1FA8C9DE29609` | 预热优化 |
| `alias_gate_auto_check.py` | 33,372B | `C8A0F439AE6D9318D4DDAAF0730ACC06` | 门禁自动化 |
| `v86_alias_full_replay.py` | 25,076B | `421B93B765967E533496F7FFF53A18A6` | 全量回放 |
| `start_alias_engine.sh` | 2,063B | `7DD3228347632DED8A1202B6B34CB939` | 启动脚本 |
| `requirements.txt` | 232B | `9E473687E1239F5B5A33AF00E333C5B8` | 依赖清单 |
| `cache_config.yaml` | 579B | `3C1C2E5A6254538BCED8CC6C4890EBE7` | 缓存配置 |
| `Dockerfile` | 857B | `243470C4EAD5D9C63CF325861585ED47` | Docker 构建 |

### 4.2 部署方式

| 方式 | 配置文件 | 状态 |
|------|----------|------|
| 本地 | `start_alias_engine.sh` + `requirements.txt` | ✅ 已验证 |
| Docker | `deploy/Dockerfile` | ✅ 已验证 |
| Docker Compose | `deploy/docker-compose.yaml` | ✅ 已验证 |
| Kubernetes | `deploy/k8s-deployment.yaml` | ✅ 已验证 |

---

## 5. 运维资产

### 5.1 灰度仿真

| 文件 | 大小 | MD5 | 说明 |
|------|------|-----|------|
| `gray_simulation_runner.py` | 29,140B | `139C3A4C01ADD90536078759370F6324` | 仿真脚本 |
| `gray_simulation_results.json` | 25,039B | `C584460D50C1D6D0AE16D8C7EC7C9AC9` | 仿真结果 |
| `v86_alias_gray_full_simulation.md` | 17,072B | `75487A8F1448C7DAE7A1C9E6936074E8` | 仿真报告 |

### 5.2 运维手册

| 文件 | 大小 | MD5 | 说明 |
|------|------|-----|------|
| `v86_alias_ops_manual_final.md` | 29,923B | `E1EFAA2C8A26FA08233784759C1614F2` | 运维手册终稿 |
| `v86_alias_prod_integrate_verify_report.md` | 21,750B | `C6273225803A593469122E90068B81EF` | 集成校验报告 |

### 5.3 降级预案

| 文件 | 大小 | MD5 | 说明 |
|------|------|-----|------|
| `v86_alias_degrade_plan.md` | 14,871B | `A8473607D2BFFC31D5C11D8352EC550D` | 降级预案 |

### 5.4 监控规范

| 文件 | 大小 | MD5 | 说明 |
|------|------|-----|------|
| `v86_alias_monitor_spec.md` | 17,364B | `510A4CFC196B4D301EE3E23301A9DFE0` | 监控规范 |

---

## 6. 变更追溯链

### 6.1 Git Commit 链

| Commit | 日期 | 说明 |
|--------|------|------|
| `81268a6` | 2026-10-02 | 别名引擎全量回放+生产bundle+灰度/降级方案 (base) |
| `ab95859` | 2026-10-02 | 别名引擎全量回放报告 (前序) |
| `68517fb` | 2026-10-01 | DSHB 规则引擎全集成 |
| `f694618` | 2026-10-02 | DSHB 规则引擎全量回放+生产bundle |
| `d16310e` | 2026-10-01 | V86 别名引擎联合集成+预上线检查 |
| `168a073` | 2026-10-01 | V86 别名引擎原型+回归 |
| `c7f5a40` | 2026-10-01 | DSHB 规则引擎压力测试+CI |
| `9f23568` | 2026-10-01 | DSHB 规则引擎全集成 |
| `bcd64dd` | 2026-09-30 | E 后端异步任务 API 定义 |

### 6.2 资产版本链

```
V85 别名库 (冻结, 4643 条目)
  └── V86AliasEngine v1.0 (F1+F2+F3+F4, 模式 base/f3/f3+f4)
        ├── V86AliasTaskAdapter v1.0 (dshe_alias_resolve)
        ├── V86AliasWarmupOptimize v1.0 (单例+LRU 缓存)
        ├── V86AliasGateAutoCheck v1.0 (14 道门禁)
        ├── V86AliasFullReplay v1.0 (4643 条回放)
        ├── V86AliasProductionBundle v1.0 (Docker/K8s/Compose)
        ├── V86AliasGrayReleasePlan v1.0 (12 道灰度门禁)
        ├── V86AliasDegradePlan v1.0 (L1/L2/L3 降级)
        ├── V86AliasMonitorSpec v1.0 (Prometheus/Grafana)
        ├── V86AliasProdIntegrateVerify v1.0 (113 项校验)
        ├── V86AliasGrayFullSimulation v1.0 (8 阶段仿真)
        └── V86AliasOpsManualFinal v1.0 (运维手册终稿)
```

### 6.3 关联资产 (DSHB 规则引擎)

| 资产 | Commit | 说明 |
|------|--------|------|
| DSHB 规则引擎生产包 | `f694618` | P0+P1 规则, 18 条规则 |
| DSHB 规则引擎回滚方案 | `f694618` | 双策略回滚 |
| DSHB 规则引擎资源评估 | `f694618` | CPU/内存/磁盘评估 |
| DSHB 规则引擎监控规范 | `f694618` | Prometheus 指标 |
| DSHB 联合回放结果 | `f694618` | 联合数据集回放 |

---

## 7. 冻结声明

### 7.1 冻结信息

| 属性 | 值 |
|------|-----|
| 资产版本 | `v86.0.0-frozen` |
| 冻结时间 | 2026-10-02 |
| 冻结 Commit | `81268a6` |
| 分支 | `feature/v85-chart-template` |
| 冻结人 | AI Agent |
| 变更追溯 | Git commit history |

### 7.2 冻结范围

| 范围 | 状态 |
|------|------|
| V86 别名引擎代码 (F1/F2/F3/F4) | ✅ 已冻结 |
| V86 任务适配层 | ✅ 已冻结 |
| V86 测试用例集 | ✅ 已冻结 |
| V85 别名库 (只读) | ✅ 已冻结 (不可修改) |
| V86 生产部署包 | ✅ 已冻结 |
| V86 灰度/降级/监控方案 | ✅ 已冻结 |
| V86 运维手册 | ✅ 已冻结 |
| DSHB 规则引擎 (关联) | ✅ 已冻结 |

### 7.3 变更控制

| 变更类型 | 流程 | 审批 |
|----------|------|------|
| 别名库更新 | V86 别名库变更 PR | 开发团队 + SRE |
| 引擎代码修改 | feature 分支 → PR → review | 开发团队 |
| 配置修改 | ConfigMap PR | SRE |
| 紧急修复 | 热修复分支 → 快速 review | SRE + 开发团队 |
| 降级/回退 | 运维手册操作 | SRE |

### 7.4 解冻条件

资产解冻需满足以下条件:
- [ ] V86 别名引擎上线运行 72 小时无 P0 告警
- [ ] 全量回放 4,643 条 PASS
- [ ] 14 道门禁全部 PASS
- [ ] 3 次降级演练全部通过
- [ ] 运维手册验收完成
- [ ] SRE + 开发团队签字确认

---

## 8. 约束合规

| 约束 | 状态 |
|------|------|
| NO_ZHIJI_API_CALL=TRUE | ✅ 无外部 API 调用 |
| NO_MODIFY_SOURCE_TEMPLATE=TRUE | ✅ V85 只读加载 |
| NO_MODIFY_V85_FROZEN_FILES=TRUE | ✅ V85 文件未修改 |
| 不覆盖已有交付物 | ✅ 独立输出目录 `dshe_alias_ops_final/` |
| 分支锁定 feature/v85-chart-template | ✅ 未合并 main |

---

*资产固化包由 DSHE_V86_ALIAS_PROD_INTEGRATE_ADAPT_GRAY_SIMULATION_AND_OPS_MANUAL_FINAL T2.4 生成*
*分支: feature/v85-chart-template · Commit: 81268a6*
*资产版本: v86.0.0-frozen · 冻结时间: 2026-10-02*
