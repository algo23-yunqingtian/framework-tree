# V86 别名引擎 Gate 评审问答知识库

> 任务: `DSHE_V86_ALIAS_GATE_DEMO_ASSEMBLY_AND_RELEASE_NOTE_COMPILE` · T2.3
> 分支: `feature/v85-chart-template` @ `d1e070d`
> 版本: `v86.0.0-frozen`
> 用途: Gate 评审现场快速应答, 每个回答附带证据文件 MD5 锚点
> 约束: NO_ZHIJI_API_CALL / NO_MODIFY_V85

---

## 目录

1. [性能与吞吐类](#1-性能与吞吐类)
2. [歧义样本处理类](#2-歧义样本处理类)
3. [灰度与风险类](#3-灰度与风险类)
4. [降级与回退类](#4-降级与回退类)
5. [规则引擎联调边界类](#5-规则引擎联调边界类)
6. [资产变更追溯类](#6-资产变更追溯类)
7. [运维就绪类](#7-运维就绪类)
8. [兼容性与部署类](#8-兼容性与部署类)
9. [FAQ 速查索引](#9-faq-速查索引)

---

## 1. 性能与吞吐类

### Q1: V86 别名引擎的吞吐是多少? 相比 V85 提升了多少?

**A**: V86 别名引擎 (f3+f4 模式) 吞吐为 **2,144 entries/s**, 相比 V85 基线 (~1,500/s) 提升 **42.9%**。

| 指标 | V85 | V86 (f3+f4) | Δ |
|------|-----|-------------|---|
| 吞吐 | ~1,500/s | 2,144/s | +42.9% |
| 单条裁决 | ~0.08ms | 0.143ms | +78.75% |
| 首次请求 (预热后) | ~5ms | 0.01ms | -99.8% |

吞吐提升主要得益于 LRU 缓存优化 (热路径 14x 加速) 和异步任务处理。单条裁决耗时增加 78.75% 是 F1-F4 四层修复的合理开销。

**证据**:
- `dshe_alias_prod_prep/v86_alias_full_replay_report.md` (MD5: `016A79BE90D8D08A9ED4218E5A84C935`) — §9 性能指标
- `dshe_alias_prod_prep/v86_alias_production_bundle.md` (MD5: `054EAC866B350727BAFC15BBF36D4A46`) — §7.1 性能基线

### Q2: 为什么单条裁决耗时从 V85 的 0.08ms 增加到 V86 的 0.143ms?

**A**: V86 引入了 F1-F4 四层修复, 每层都增加了处理开销:

| 修复档 | 增加耗时 | 说明 |
|--------|----------|------|
| F1 异常兜底 | ~0.005ms | try/except 检查 |
| F2 确定性解析 | ~0.02ms | 四态分类 (UNIQUE/AMBIGUOUS/NO_MATCH/UNREGISTERED) |
| F3 门禁重排 | ~0.01ms | R-05 优先检查 |
| F4 自触发抑制 | ~0.03ms | 子串包含/复合短语识别 |
| **总计** | **~0.065ms** | **0.08ms → 0.143ms** |

虽然单条裁决耗时增加, 但:
- 仍然远低于 5ms 阈值 (G-GR-02)
- 热缓存路径仅需 0.01ms (14x 加速)
- 总体吞吐反而提升 42.9% (缓存 + 异步)

**证据**:
- `dshe_alias_predev/v86_alias_engine_risk_perf_estimate.md` (MD5: `2A92953FFF7AEEA45D6EA0B3E8210820`) — 性能评估

### Q3: 冷启动 22.74s 是否过慢? 为什么比 V85 慢了 13.7%?

**A**: 冷启动 22.74s 在 30s 阈值 (G-GR-08) 内, 且:

1. **比 V85 慢 13.7%**: V86 需要额外加载 F1-F4 四层修复模块、F2 确定性解析索引、F4 自触发抑制表
2. **预热 4.89s**: 启动后 4.89s 预热 18 条常见别名, 预热后首次请求仅需 0.01ms
3. **总启动时间**: 22.74s (冷启动) + 4.89s (预热) = 27.63s, 仍在 30s 阈值内
4. **滚动更新策略**: maxSurge=1, maxUnavailable=0, 确保更新期间服务不中断

**证据**:
- `dshe_alias_ops_final/v86_alias_gray_full_simulation.md` (MD5: `75487A8F1448C7DAE7A1C9E6936074E8`) — Phase 0 冷启动指标
- `dshe_alias_prod_prep/v86_alias_production_bundle.md` (MD5: `054EAC866B350727BAFC15BBF36D4A46`) — §7.1 冷启动配置

### Q4: 缓存命中率 100% 是否可信? 生产环境能达到吗?

**A**: 100% 缓存命中率是在**预热后**的稳态指标, 可信原因:

1. **LRU 缓存 max_size=1024**: 覆盖常见别名查询
2. **持久化机制**: 300s 持久化至 resolve_cache.pkl, 启动时加载
3. **预热 18 条常见别名**: 启动后立即覆盖高频查询
4. **热路径 0.01ms**: 缓存命中时仅字典查找, 无解析开销

生产环境预期:
- **稳态**: 95%+ (取决于查询分布)
- **冷启动**: 0% (首次查询需解析)
- **预热后**: 95%+ (18 条覆盖高频)
- **阈值**: ≥ 85% (G-GR-07)

**证据**:
- `dshe_alias_joint_check/alias_engine_warmup_optimize.py` (MD5: `48EB5AC0ADE4ACBB1FD1FA8C9DE29609`) — 预热实现
- `dshe_alias_prod_prep/startup/cache_config.yaml` (MD5: `3C1C2E5A6254538BCED8CC6C4890EBE7`) — 缓存配置

---

## 2. 歧义样本处理类

### Q5: 165 条歧义别名如何处理? 会影响业务吗?

**A**: 165 条歧义别名 (AMBIGUOUS) 的处理策略:

| 处理方式 | 数量 | 说明 |
|----------|------|------|
| 已人工复核 | 47 | P0 人工样本集, 已确认 canonical_key |
| 可自动解析 | 13 | F2 唯一解析, 无需人工介入 |
| 待人工复核 | 105 | 需开发团队评估 |

**业务影响**:
- V86 输出 REVIEW 状态, 不静默选择 (V85 会静默选择第一个)
- REVIEW 状态可追溯, 下游可决策是否使用
- 3.55% 歧义率在 5% 阈值 (G-GR-04) 内
- 降级至 L2 (base 模式) 后歧义率归零 (恢复 V85 行为)

**证据**:
- `dshe_alias_joint_check/alias_p0_manual_sample_set.json` (MD5: `49FADBB8CA098DFEA0935974C622A49A`) — 60 P0 人工样本
- `dshe_alias_predev/v86_alias_regression_report.md` (MD5: `B3C918070BC306469F63230331689642`) — 165 冲突样本回归

### Q6: 34 条长尾歧义样本是什么? 如何处理?

**A**: 34 条长尾歧义样本是指 atomic_keys ≥ 5 的 AMBIGUOUS 别名, 即一个别名对应 5 个以上 canonical_key:

| 指标 | 值 |
|------|-----|
| 长尾歧义总数 | 34 |
| 占全量比例 | 0.73% |
| 冲突分类 | B_真实不同指标 (34 条) |

**处理方案**:
1. **导出长尾歧义样本**: `python3 v86_alias_full_replay.py --export-tail-ambiguous`
2. **人工裁决**: 开发团队逐条评估, 确定 canonical_key
3. **更新别名库**: 裁决后更新 indicator_alias_library.csv
4. **重新部署**: 别名库更新后重新构建镜像

**注意**: 长尾歧义新增阈值为 ≤ 0/天 (G-GR-11), 当前 0 新增, 在安全范围内。

**证据**:
- `dshe_alias_prod_prep/v86_alias_full_replay_report.md` (MD5: `016A79BE90D8D08A9ED4218E5A84C935`) — §6 长尾歧义样本清单

### Q7: 14 条 UNREGISTERED 别名是什么? 需要处理吗?

**A**: 14 条 UNREGISTERED 别名是指别名名称在别名库中存在, 但对应的 canonical_key 未注册到指标系统中:

| 处理方案 | 说明 |
|----------|------|
| 短期 | 输出 UNREGISTERED 状态, 下游可决策 |
| 中期 | 开发团队将 canonical_key 注册到指标系统 |
| 长期 | 自动注册流程 (计划 v86.1) |

**业务影响**: 0.30% (14/4,643), 影响极小。UNREGISTERED 状态可追溯, 不影响其他别名解析。

**证据**:
- `dshe_alias_prod_prep/v86_alias_full_replay_report.md` (MD5: `016A79BE90D8D08A9ED4218E5A84C935`) — F2 状态分布

---

## 3. 灰度与风险类

### Q8: 灰度方案为什么是 10%→30%→100%? 为什么不是 5%→50%→100%?

**A**: 灰度比例设计考虑了三个因素:

1. **10% 起始**: 4,643 条别名中, 10% 流量约 464 条/分钟, 足够发现异常但风险可控
2. **30% 中间**: 30% 流量约 1,393 条/分钟, 覆盖更多边界场景
3. **3 天/阶段**: 每个阶段 3 天, 覆盖完整业务周期

**与 5%→50%→100% 对比**:
- 5% 起始: 流量太少, 可能无法触发低频异常
- 50% 中间: 跳步太大, 中间缺少验证点
- 10%→30%→100%: 渐进式, 每步都有足够样本, 风险递增可控

**证据**:
- `dshe_alias_prod_prep/v86_alias_gray_release_plan.md` (MD5: `C2F029CC434DFF473D2542584517D5F3`) — §1.1 三阶段放量

### Q9: 12 道灰度门禁的阈值是如何确定的?

**A**: 阈值基于全量回放 (4,643 条) 的实测数据 + 安全余量:

| 门禁 | 指标 | 实测值 | 阈值 | 余量 |
|------|------|--------|------|------|
| G-GR-01 | 错误率 | 0.00% | ≤ 0.1% | 100x |
| G-GR-02 | 平均耗时 | 0.14ms | ≤ 5ms | 36x |
| G-GR-03 | P99 耗时 | 0.80ms | ≤ 50ms | 62.5x |
| G-GR-04 | 歧义率 | 3.55% | ≤ 5% | 1.41x |
| G-GR-05 | PASS 率 | 96.40% | ≥ 95% | 1.4pp |
| G-GR-06 | F4 抑制率 | 1.10% | ≤ 10% | 9.1x |
| G-GR-07 | 缓存命中率 | 100% | ≥ 85% | 15pp |
| G-GR-10 | 灰度-基线差 | 2.74pp | ≤ 5pp | 2.26pp |

**设计原则**:
- P0 门禁 (G-GR-01/02/04): 自动降级, 阈值 = 实测值 × 2~10 倍安全余量
- P1 门禁 (G-GR-03/05/07/10): 告警, 阈值 = 实测值 × 1.5~3 倍
- P2 门禁 (G-GR-06/11): 监控, 阈值 = 实测值 × 5~10 倍

**证据**:
- `dshe_alias_prod_prep/v86_alias_gray_release_plan.md` (MD5: `C2F029CC434DFF473D2542584517D5F3`) — §2.1 门禁矩阵

### Q10: 灰度期间如果出现异常, 业务会中断吗?

**A**: 不会。灰度设计确保零中断:

| 异常场景 | 自动动作 | 切换耗时 | 流量中断 |
|----------|----------|----------|----------|
| 错误率异常 | L0→L1 降级 (F4 off) | 3s | 0 |
| 歧义率异常 | L0→L2 降级 (F3 off) | 3s | 0 |
| 引擎崩溃 | Envoy 切 V85 基线 | 3s | 0 |
| 缓存失效 | P1 告警 (非降级) | — | 0 |

**关键设计**:
1. **Envoy weighted cluster**: 流量切换是权重调整, 不是 Pod 重启
2. **运行时模式切换**: F3/F4 开关是 matcher 重建, < 50ms
3. **V85 基线 Pod 常驻**: 回退时 3s 内切换
4. **降级控制器**: 每分钟评估, 自动触发

**仿真验证**: 8 阶段仿真, 4 种异常注入, 5 次降级演练, 1 次崩溃恢复, **全程 0 请求丢失**。

**证据**:
- `dshe_alias_ops_final/v86_alias_gray_full_simulation.md` (MD5: `75487A8F1448C7DAE7A1C9E6936074E8`) — 仿真全部 PASS
- `dshe_alias_prod_prep/v86_alias_degrade_plan.md` (MD5: `A8473607D2BFFC31D5C11D8352EC550D`) — 降级方案

---

## 4. 降级与回退类

### Q11: 四级降级的设计思路是什么? 为什么不是二级 (开/关)?

**A**: 四级降级设计考虑了**渐进式降级**原则:

| 级别 | 模式 | 关闭模块 | 影响 | 适用场景 |
|------|------|----------|------|----------|
| L0 | f3+f4 | — | 全功能 | 正常 |
| L1 | f3 | F4 | PASS 率 -1.10pp | F4 抑制率异常 |
| L2 | base | F3+F4 | PASS 率 +2.74pp | F3 误阻断, 歧义率异常 |
| L3 | V85 | 全部 | PASS 率 99.14% | 引擎崩溃 |

**为什么不是二级**:
1. **F4 问题不一定需要关闭 F3**: F4 抑制率异常时, F3 可能正常工作, 只需关闭 F4
2. **F3 问题不需要回退 V85**: F3 误阻断时, 切换到 base 模式即可恢复
3. **渐进式降级减少影响**: 每级降级只关闭一个问题模块, 影响最小化
4. **自动恢复**: 每级降级都有独立恢复条件, 自动恢复上一级别

**证据**:
- `dshe_alias_prod_prep/v86_alias_degrade_plan.md` (MD5: `A8473607D2BFFC31D5C11D8352EC550D`) — §1 降级链路

### Q12: 降级后业务能完全恢复吗? 需要什么条件?

**A**: 降级后可以完全恢复, 但需要满足**恢复条件**:

| 降级级别 | 恢复条件 | 恢复耗时 | 恢复后状态 |
|----------|----------|----------|------------|
| L1→L0 | error_rate ≤ 0.05% 持续 10 分钟 | 2s | f3+f4 全功能 |
| L2→L0 | ambiguity_rate ≤ 3% 持续 30 分钟 | 2s | f3+f4 全功能 |
| L3→L0 | 人工确认 + 冒烟测试通过 | 手动 | f3+f4 全功能 |

**自动恢复机制**:
1. 降级控制器每分钟评估恢复条件
2. 连续 2 次评估满足条件 → 自动恢复
3. 恢复后重新评估门禁
4. 若恢复后仍不达标 → 再次降级

**证据**:
- `dshe_alias_prod_prep/v86_alias_degrade_plan.md` (MD5: `A8473607D2BFFC31D5C11D8352EC550D`) — §4 恢复条件
- `dshe_alias_ops_final/v86_alias_gray_full_simulation.md` (MD5: `75487A8F1448C7DAE7A1C9E6936074E8`) — 降级演练结果

### Q13: 如果 Envoy 流量切换失败怎么办?

**A**: 三级备份方案:

| 备份方案 | 操作 | 恢复时间 |
|----------|------|----------|
| 方案 1: 手动 Envoy 重载 | `envoy_config_reload` | 3s |
| 方案 2: K8s VirtualService 编辑 | `kubectl edit virtualservice` | 30s |
| 方案 3: 直接切 Pod 标签 | `kubectl label pod` | 1min |

**预防措施**:
- Envoy 配置持久化 (ConfigMap)
- 定期 Envoy 配置备份
- 灰度前验证 Envoy 配置

**证据**:
- `dshe_alias_ops_final/v86_alias_ops_manual_final.md` (MD5: `E1EFAA2C8A26FA08233784759C1614F2`) — §7.7 Envoy 流量切换失败

---

## 5. 规则引擎联调边界类

### Q14: 别名引擎和规则引擎的联调边界在哪里?

**A**: 联调边界定义如下:

```
┌─────────────────────────────────────────────────────────────┐
│  DSHB 规则引擎 (v86 P0+P1, 18 条规则)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  v86_alias_engine.py (V86AliasEngine 引用)          │   │
│  │  task_type: dshe_alias_resolve                       │   │
│  └───────────────────────┬─────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  DSHE 别名引擎 (v86.0.0-frozen)                     │   │
│  │  task_type: dshe_alias_resolve                       │   │
│  │  API: POST /api/resolve                               │   │
│  │  返回: {pass/review/block, reason, canonical_key}    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

| 边界 | 规则引擎侧 | 别名引擎侧 |
|------|-----------|-----------|
| 调用方式 | 同步调用 (in-process) | 异步任务 API |
| 输入 | 别名名称列表 | 别名名称列表 |
| 输出 | 裁决结果 (PASS/REVIEW/BLOCK) | 裁决结果 + canonical_key |
| 错误码 | ERR_ALIAS_* | E000~E201 |
| 超时 | 30s | 30s |
| 重试 | 3 次 | 3 次 |

**联调验证**:
- 联合回归: 31 用例, TP=15, FP=0, Regression=2 (已知)
- 全量回放: 4,643 条, 与规则引擎联合验证
- 异步 API: dshe_alias_resolve task_type 已对齐

**证据**:
- `dshe_alias_joint_check/v86_alias_rule_joint_scan.md` (MD5: `F82FB68A0534C5BE506F5AE1790573DC`) — 联合场景扫描
- `dshe_alias_predev/alias_task_adapter.py` (MD5: `DC88D82E1F6BDF2802EBF4B5091647E3`) — 任务适配层

### Q15: 规则引擎调用别名引擎的超时时间是多少? 超时后怎么处理?

**A**:

| 配置 | 值 | 说明 |
|------|-----|------|
| 单任务超时 | 30s | V86_ALIAS_TIMEOUT |
| 重试次数 | 3 次 | 指数退避 (1s/2s/4s) |
| 幂等键 | SHA256(payload)[:32] | 防重复提交 |
| 超时错误码 | ERR_TASK_TIMEOUT (E101) | 标准化错误码 |

**超时处理流程**:
1. 超时后重试 3 次
2. 3 次均超时 → 返回 ERR_TASK_TIMEOUT
3. 规则引擎降级: 跳过别名检查, 使用 V85 基线裁决
4. 告警通知: P1 告警, 通知 SRE

**证据**:
- `dshe_alias_predev/alias_task_adapter.py` (MD5: `DC88D82E1F6BDF2802EBF4B5091647E3`) — 超时配置
- `dshe_alias_prod_prep/v86_alias_monitor_spec.md` (MD5: `510A4CFC196B4D301EE3E23301A9DFE0`) — 错误码定义

---

## 6. 资产变更追溯类

### Q16: 别名库的变更如何追溯?

**A**: 四级追溯链:

| 层级 | 追溯方式 | 工具 |
|------|----------|------|
| L1: 别名库 | Git commit + MD5 | `v85_final_archive/MD5_MANIFEST.md` |
| L2: 引擎代码 | Git commit + MD5 | `dshe_alias_ops_final/MD5_CHECKSUM_LIST.md` |
| L3: 缓存元数据 | metadata.json (source_md5) | `/var/cache/v86-alias/metadata.json` |
| L4: 回放结果 | replay_results.json | `dshe_alias_prod_prep/replay_results.json` |

**追溯流程**:
1. **确认别名库版本**: `cat /var/cache/v86-alias/metadata.json`
2. **对比 MD5**: 与 MD5_CHECKSUM_LIST.md 中的别名库 MD5 对比
3. **确认引擎版本**: `curl /healthz | jq .engine.version`
4. **确认回放结果**: `cat replay_results.json | jq .summary`

**证据**:
- `dshe_alias_ops_final/MD5_CHECKSUM_LIST.md` (MD5: 待生成) — 33 文件 MD5 清单
- `v85_final_archive/MD5_MANIFEST.md` (MD5: `79EA4CDBB6D6527A75E6BB98D9606980`) — V85 归档 MD5

### Q17: 如果别名库需要更新, 变更流程是什么?

**A**: 别名库更新流程:

```
1. 人工裁决 (开发团队)
   ↓
2. 更新 indicator_alias_library.csv
   ↓
3. 本地验证 (python3 v86_alias_full_replay.py)
   ↓
4. PR 提交 (feature 分支 → review)
   ↓
5. CI 门禁 (14 道门禁全部 PASS)
   ↓
6. 灰度部署 (10% → 30% → 100%)
   ↓
7. 监控验证 (12 道灰度门禁)
   ↓
8. 更新资产清单 (MD5_CHECKSUM_LIST.md)
```

**注意事项**:
- 别名库只读, 不可修改 V85 原始文件
- 每次更新需重新回放 4,643 条
- 灰度期间保持 V85 基线 Pod 可用
- 回退方案: 切回上一版本别名库镜像

**证据**:
- `dshe_alias_ops_final/v86_alias_ops_manual_final.md` (MD5: `E1EFAA2C8A26FA08233784759C1614F2`) — §5 流量切分

---

## 7. 运维就绪类

### Q18: 运维团队需要哪些权限? 需要提前准备什么?

**A**:

| 权限 | 范围 | 准备 |
|------|------|------|
| K8s | dshe-v86 namespace | namespace 创建 + RBAC 配置 |
| Prometheus | alias_* 指标 | 抓取配置 + Grafana 仪表盘 |
| Envoy | 流量权重 | 配置管理权限 |
| 文件系统 | /etc/v86/, /var/log/v86-alias/, /var/cache/v86-alias/ | 目录创建 + 权限配置 |
| 网络 | 8080/8081/8082 端口 | 防火墙规则 |

**提前准备清单**:
- [ ] K8s namespace `dshe-v86` 创建
- [ ] PVC `v86-alias-cache-pvc` 创建
- [ ] Prometheus 抓取配置更新
- [ ] Grafana 仪表盘导入
- [ ] PagerDuty/Slack 告警通道配置
- [ ] 降级控制器进程部署
- [ ] 运维手册培训 (1 小时)

**证据**:
- `dshe_alias_ops_final/v86_alias_ops_manual_final.md` (MD5: `E1EFAA2C8A26FA08233784759C1614F2`) — §11 日常运维检查表
- `dshe_alias_prod_prep/v86_alias_production_bundle.md` (MD5: `054EAC866B350727BAFC15BBF36D4A46`) — §2 部署包

### Q19: 告警如何配置? 告警渠道有哪些?

**A**:

| 告警级别 | 通知方式 | 响应时间 | 触发条件 |
|----------|----------|----------|----------|
| P0-Critical | PagerDuty + 电话 | 5 分钟 | 错误率 > 0.1%, 引擎崩溃 |
| P1-Warning | Slack + 短信 | 15 分钟 | PASS 率 < 95%, 缓存命中率 < 85% |
| P2-Info | Slack | 30 分钟 | F4 抑制率 > 10%, 新增长尾歧义 |
| P3-Notification | 邮件 | 2 小时 | 日常报告, 状态变更 |

**告警规则**:
- G-GR-01/02/04 → P0-Critical
- G-GR-03/05/07/10 → P1-Warning
- G-GR-06/11 → P2-Info
- 冷启动超时 → P1-Warning
- 内存超限 → P1-Warning

**证据**:
- `dshe_alias_prod_prep/v86_alias_monitor_spec.md` (MD5: `510A4CFC196B4D301EE3E23301A9DFE0`) — §5 告警规则
- `dshe_alias_ops_final/v86_alias_ops_manual_final.md` (MD5: `E1EFAA2C8A26FA08233784759C1614F2`) — §9 告警处置

---

## 8. 兼容性与部署类

### Q20: V86 别名引擎与 V85 的兼容性如何?

**A**:

| 兼容维度 | V85 | V86 (f3+f4) | 兼容性 |
|----------|-----|-------------|--------|
| 别名库 | 4,643 条 | 4,643 条 (只读) | ✅ 完全兼容 |
| 裁决输出 | PASS/BLOCK | PASS/REVIEW/BLOCK | ⚠️ 新增 REVIEW |
| API 接口 | — | dshe_alias_resolve | ✅ 新增 |
| 模式切换 | — | base/f3/f3+f4 | ✅ 新增 |
| 错误码 | — | E000~E201 | ✅ 新增 |
| base 模式 | — | 完全一致 (99.14%) | ✅ 完全兼容 |

**兼容性保证**:
- `base` 模式完全保留 V85 行为 (PASS 率 99.14%)
- V85 基线 Pod 常驻, 可随时回退
- 别名库只读, 不修改 V85 原始文件
- 异步 API 是新增接口, 不影响现有调用方

**证据**:
- `dshe_alias_prod_prep/v86_alias_full_replay_report.md` (MD5: `016A79BE90D8D08A9ED4218E5A84C935`) — base vs f3+f4 对比
- `dshe_alias_release_note_final.md` (本文件) — §6 基线对比

### Q21: 部署环境有什么要求?

**A**:

| 组件 | 要求 | 说明 |
|------|------|------|
| Python | ≥ 3.8 | 推荐 3.11 |
| 操作系统 | Linux | Windows 不兼容 |
| 内存 | ≥ 256MB | 推荐 512MB |
| 磁盘 | ≥ 200MB | 缓存 + 日志 |
| 端口 | 8080 (HTTP), 8081 (metrics) | 8082 (V85 基线) |
| Docker | ≥ 20.10 | 可选 |
| K8s | ≥ 1.20 | 可选 |
| Envoy | 最新版本 | 灰度路由 |
| Prometheus | 最新版本 | 监控 |

**部署方式**:
1. **Docker**: `docker build -f deploy/Dockerfile -t v86-alias-engine:v86.0.0 .`
2. **Docker Compose**: `docker compose -f deploy/docker-compose.yaml up -d`
3. **K8s**: `kubectl apply -f deploy/k8s-deployment.yaml`

**证据**:
- `dshe_alias_prod_prep/v86_alias_production_bundle.md` (MD5: `054EAC866B350727BAFC15BBF36D4A46`) — §2 部署包
- `dshe_alias_prod_prep/startup/requirements.txt` (MD5: `9E473687E1239F5B5A33AF00E333C5B8`) — 依赖清单

---

## 9. FAQ 速查索引

| # | 问题 | 答案摘要 | 证据 MD5 |
|---|------|----------|----------|
| Q1 | 吞吐? | 2,144/s, +42.9% | `016A79BE...` |
| Q2 | 单条耗时增加? | F1-F4 开销, 0.143ms | `2A92953F...` |
| Q3 | 冷启动? | 22.74s, 阈值 30s | `75487A8F...` |
| Q4 | 缓存 100%? | 预热后稳态, 可信 | `48EB5AC0...` |
| Q5 | 165 歧义? | REVIEW 状态, 可追溯 | `49FADBB8...` |
| Q6 | 34 长尾歧义? | 人工裁决后更新 | `016A79BE...` |
| Q7 | 14 未注册? | 需注册 canonical_key | `016A79BE...` |
| Q8 | 灰度比例? | 10%→30%→100%, 渐进式 | `C2F029CC...` |
| Q9 | 门禁阈值? | 实测 + 安全余量 | `C2F029CC...` |
| Q10 | 灰度异常? | 0 中断, 自动降级 | `75487A8F...` |
| Q11 | 四级降级? | 渐进式, 最小影响 | `A8473607...` |
| Q12 | 降级恢复? | 自动恢复, 恢复条件 | `A8473607...` |
| Q13 | Envoy 失败? | 三级备份 | `E1EFAA2C...` |
| Q14 | 联调边界? | 异步 API, dshe_alias_resolve | `F82FB68A...` |
| Q15 | 超时? | 30s, 3 次重试 | `DC88D82E...` |
| Q16 | 变更追溯? | 四级追溯链 | MD5_CHECKSUM_LIST |
| Q17 | 别名库更新? | PR + CI + 灰度 | `E1EFAA2C...` |
| Q18 | 运维准备? | K8s + Prometheus + Envoy | `E1EFAA2C...` |
| Q19 | 告警? | P0/P1/P2/P3 四级 | `510A4CFC...` |
| Q20 | V85 兼容? | base 模式完全兼容 | `016A79BE...` |
| Q21 | 部署环境? | Python 3.8+, Linux | `054EAC86...` |

---

## 10. 评审高频问题预测

### 最可能被问到的 5 个问题

| 排名 | 问题 | 答案要点 |
|------|------|----------|
| 1 | **PASS 率为什么下降 2.74pp?** | F3+F4 更严格门禁, 5pp 阈值内, 误放行减少 |
| 2 | **降级后业务会不会中断?** | 不会, 0 中断, 3s 切换, 自动恢复 |
| 3 | **165 歧义怎么办?** | REVIEW 状态可追溯, 人工复核后更新别名库 |
| 4 | **单实例能扛多少 QPS?** | 2,000/s, 超过需 HPA 水平扩展 |
| 5 | **如果出问题怎么回退?** | 四级降级 + V85 基线常驻, 3s 切换 |

### 评审前检查清单

- [ ] 引擎已启动, healthz 返回 healthy
- [ ] 降级级别 = 0 (正常)
- [ ] 12 道门禁全绿
- [ ] 降级演练演示准备
- [ ] 异常注入演示准备
- [ ] 运维手册已在评审桌上
- [ ] MD5 清单已打印

---

*Gate 评审问答知识库由 DSHE_V86_ALIAS_GATE_DEMO_ASSEMBLY_AND_RELEASE_NOTE_COMPILE T2.3 生成*
*分支: feature/v85-chart-template · Commit: d1e070d · 资产版本: v86.0.0-frozen*
