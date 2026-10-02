# V86 别名引擎 Release Note 终稿

> 任务: `DSHE_V86_ALIAS_GATE_DEMO_ASSEMBLY_AND_RELEASE_NOTE_COMPILE` · T2.2
> 分支: `feature/v85-chart-template` @ `d1e070d`
> 版本: `v86.0.0-frozen`
> 发布类型: 别名引擎首次生产发布
> 基线: V85 别名引擎 (冻结, commit `f313570`)
> 受众: 业务 / 产品 / 运维 三方
> 生成时间: 2026-10-02

---

## 目录

1. [版本概览](#1-版本概览)
2. [功能新增](#2-功能新增)
3. [性能提升](#3-性能提升)
4. [优化点](#4-优化点)
5. [已知限制](#5-已知限制)
6. [基线对比 (V85)](#6-基线对比-v85)
7. [分模块说明](#7-分模块说明)
8. [风险边界与业务影响](#8-风险边界与业务影响)
9. [开关说明](#9-开关说明)
10. [回退路径](#10-回退路径)
11. [变更追溯链](#11-变更追溯链)
12. [关联资产索引](#12-关联资产索引)

---

## 1. 版本概览

### 1.1 版本信息

| 属性 | 值 |
|------|-----|
| 版本 | `v86.0.0-frozen` |
| 引擎 | V86AliasEngine |
| 推荐生产模式 | `f3+f4` |
| 资产冻结时间 | 2026-10-02 |
| Git Commit | `d1e070d` |
| 分支 | `feature/v85-chart-template` |
| 基线版本 | V85 别名引擎 (commit `f313570`) |
| 别名库条目 | 4,643 条 (只读, 冻结) |
| Canonical Key | 1,818 个 |
| 覆盖品种 | LI/NI/SI/SN/ZN/AL/PB/CU/AO 等 10+ |

### 1.2 变更摘要

```
┌────────────────────────────────────────────────────────────────────────────┐
│  V86 别名引擎 v86.0.0-frozen — 变更摘要                                     │
├────────────────────────────────────────────────────────────────────────────┤
│  🆕 新增: F1 异常兜底 / F2 确定性解析 / F3 门禁重排 / F4 自触发抑制          │
│  🚀 性能: 吞吐 +42.9% (1,500→2,144/s), 热缓存加速 14x                      │
│  🛡️ 安全: 消除 KeyError 崩溃风险, 结构化解析消除静默多义                     │
│  ⚙️ 运维: 四级降级 (L0→L1→L2→L3), 12 道灰度门禁, 自动降级控制器             │
│  📊 监控: Prometheus 指标埋点, Grafana 仪表盘, 结构化日志                    │
│  📦 部署: Docker/K8s/Compose 多环境, 缓存持久化, 优雅退出                    │
│  📋 文档: 运维手册 (11 章), 灰度方案, 降级预案, 监控规范, Release Note       │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 功能新增

### 2.1 F1 异常兜底

| 属性 | 说明 |
|------|------|
| 功能 | KeyError 安全捕获, 别名未命中返回 NO_MATCH |
| 机制 | 在别名查找入口添加 try/except, 异常不向上传播 |
| 触发条件 | 任何 KeyError 或别名查找异常 |
| 影响 | 消除 V85 引擎中因 KeyError 导致的进程崩溃风险 |
| 触发数 | 2,878 hits / 1,765 misses (全量 4,643 条) |
| 降级影响 | L0-L2 均启用 F1, L3 (V85 回退) 无 F1 |

### 2.2 F2 确定性解析

| 属性 | 说明 |
|------|------|
| 功能 | 别名→canonical_key 结构化解析, 输出 UNIQUE/AMBIGUOUS/NO_MATCH/UNREGISTERED 四态 |
| 机制 | 对每个别名条目, 解析所有可能的 canonical_key, 分类输出 |
| 状态分布 | UNIQUE: 2,713 (58.43%), AMBIGUOUS: 165 (3.55%), NO_MATCH: 1,751 (37.71%), UNREGISTERED: 14 (0.30%) |
| 影响 | 消除 V85 引擎中多义别名静默选择的风险, 歧义样本可追溯 |
| 降级影响 | L0-L2 均启用 F2, L3 (V85 回退) 无 F2 |

### 2.3 F3 门禁重排

| 属性 | 说明 |
|------|------|
| 功能 | R-05 黑名单检查优先于 R-07 别名精确匹配 |
| 机制 | 调整门禁执行顺序: R-05 (黑名单) → R-07 (别名精确) → 其他 |
| 触发条件 | 别名在黑名单中且同时在别名库中 |
| 触发数 | 2 条 (R-05 触发) |
| 影响 | 消除黑名单别名被精确匹配绕过的问题 |
| 降级影响 | L0-L1 启用 F3, L2/L3 关闭 F3 |

### 2.4 F4 自触发抑制

| 属性 | 说明 |
|------|------|
| 功能 | 同名对子串包含/复合短语抑制 |
| 机制 | F4a: 子串包含抑制 (132 事件), F4b: 复合短语抑制 (46 事件) |
| 触发条件 | 别名 A 是别名 B 的子串, 或复合短语包含关系 |
| 受影响条目 | 51 条 (最终被 F4 抑制) |
| 影响 | 消除同名对之间的误阻断 |
| 降级影响 | L0 启用 F4, L1-L3 关闭 F4 |

### 2.5 运行时模式切换

| 属性 | 说明 |
|------|------|
| 功能 | 无需重启即可切换 base/f3/f3+f4 三种模式 |
| 机制 | `POST /api/mode` 动态重赋值 engine.matcher |
| 模式列表 | base (V85 行为), f3 (F4 off), f3+f4 (全功能) |
| 切换耗时 | < 50ms (matcher 重建) |
| 影响 | 支持运行时降级, 无需 Pod 重启 |

### 2.6 LRU 缓存预热

| 属性 | 说明 |
|------|------|
| 功能 | 启动时预热 18 条常见别名, 持久化缓存至 300s |
| 机制 | 单例+LRU 缓存 (max_size=1024), 持久化至 resolve_cache.pkl |
| 预热样本 | 18 条跨品种常见别名 |
| 首次请求 (预热后) | 0.01ms (vs 冷路径 0.14ms, 14x 加速) |
| 缓存命中率 | 100% (预热后) |

### 2.7 灰度控制器

| 属性 | 说明 |
|------|------|
| 功能 | 三阶段灰度放量 (10%→30%→100%), 12 道门禁实时评估 |
| 机制 | Envoy weighted cluster 流量分配, 门禁评估驱动降级 |
| 门禁数量 | 12 道 (G-GR-01 ~ G-GR-12) |
| 自动降级 | P0 门禁失败自动降级, P1 告警, P2 监控 |
| 演练验证 | 8 阶段仿真全部 PASS, 0 流量中断 |

### 2.8 降级控制器

| 属性 | 说明 |
|------|------|
| 功能 | 四级降级链路 (L0→L1→L2→L3), 自动/手动触发, 自动恢复 |
| 机制 | DEGRADE_LEVEL 文件 + API 双通道, 降级控制器每分钟评估 |
| 降级级别 | L0 (正常), L1 (F4 off), L2 (F3 off), L3 (V85 回退) |
| 自动恢复 | 恢复条件满足后自动恢复上一级别 |
| 演练验证 | 5 次降级演练 + 1 次崩溃恢复, 全部 PASS |

### 2.9 监控埋点

| 属性 | 说明 |
|------|------|
| 功能 | Prometheus 指标埋点, Grafana 仪表盘, 结构化 JSON 日志 |
| 指标类型 | Counter / Gauge / Histogram, 6 大类 (系统/引擎/业务/性能/可用性) |
| 指标数量 | 30+ 核心指标 |
| 告警规则 | P0-Critical / P1-Warning / P2-Info 三级 |
| 日志格式 | JSON structured, Loki 兼容 |

### 2.10 生产部署包

| 属性 | 说明 |
|------|------|
| 功能 | Dockerfile + docker-compose + K8s Deployment + 启动脚本 |
| 启动脚本 | preflight 检查 + 预热 + healthz 验证 + 优雅退出 |
| 缓存配置 | LRU max_size=1024, 持久化 300s, 关机时持久化 |
| 健康探针 | readinessProbe (60s initial) + livenessProbe (90s initial) |
| 优雅退出 | SIGTERM/SIGINT trap, 缓存持久化, 优雅关闭 |

---

## 3. 性能提升

### 3.1 吞吐提升

| 指标 | V85 | V86 (f3+f4) | Δ | 说明 |
|------|-----|-------------|---|------|
| 单条裁决耗时 | ~0.08ms | 0.143ms | +78.75% | F1-F4 四层修复增加开销 |
| 吞吐 | ~1,500/s | 2,144/s | +42.9% | 缓存优化 + 异步任务 |
| 首次请求 (预热后) | ~5ms | 0.01ms | -99.8% | LRU 缓存命中 |
| 热缓存加速 | 无缓存 | 14x | — | 0.01ms vs 0.14ms |

### 3.2 资源占用

| 资源 | V85 | V86 | Δ | 阈值 | 状态 |
|------|-----|-----|---|------|------|
| 内存 | ~70MB | ~128MB | +82.9% | ≤ 512MB | ✅ |
| CPU | 1 core | 1 core | 0% | — | ✅ |
| 磁盘 | ~10MB | ~50MB | +400% | ≤ 200MB | ✅ |

### 3.3 启动性能

| 指标 | V85 | V86 | Δ | 阈值 | 状态 |
|------|-----|-----|---|------|------|
| 冷启动 | ~20s | 22.74s | +13.7% | ≤ 30s | ✅ |
| 预热耗时 | 无 | 4.89s | — | ≤ 10s | ✅ |
| 首次请求 (预热后) | ~5ms | 0.01ms | -99.8% | ≤ 50ms | ✅ |

---

## 4. 优化点

### 4.1 别名库加载优化

- **V85**: 逐行 CSV 解析, 无索引
- **V86**: `exec()` 加载别名库, 内置 `M` 字典索引, 启动时一次性构建

### 4.2 缓存策略优化

- **V85**: 无缓存, 每次请求全量解析
- **V86**: 单例 LRU 缓存 (max_size=1024), 300s 持久化, 关机时持久化, 启动时加载

### 4.3 错误处理优化

- **V85**: KeyError 直接抛出, 可能导致进程崩溃
- **V86**: F1 异常兜底, 所有异常安全捕获, 返回结构化错误码

### 4.4 歧义处理优化

- **V85**: 多义别名静默选择第一个 canonical_key
- **V86**: F2 确定性解析, 输出 UNIQUE/AMBIGUOUS/NO_MATCH/UNREGISTERED 四态, 可追溯

### 4.5 门禁执行优化

- **V85**: 固定顺序执行 (R-07 先于 R-05)
- **V86**: F3 门禁重排 (R-05 优先), 消除黑名单绕过

### 4.6 同名对处理优化

- **V85**: 同名对可能互相阻断
- **V86**: F4 自触发抑制, 子串包含/复合短语识别, 避免误阻断

---

## 5. 已知限制

### 5.1 功能限制

| # | 限制 | 影响 | 规避方案 | 计划版本 |
|---|------|------|----------|----------|
| 1 | F2 UNREGISTERED 仅返回状态, 无修复建议 | 14 条未注册别名需人工处理 | 导出 UNREGISTERED 列表, 人工复核后更新别名库 | v86.1 |
| 2 | F4 抑制率无法细粒度控制 | 全局开关, 无法按品种/规则级别控制 | 降级至 L1 (F4 off) | v86.1 |
| 3 | 缓存 max_size 固定 1024 | 高基数场景可能频繁驱逐 | 调整 cache_config.yaml 中 max_size | 配置项 |
| 4 | 降级控制器依赖 DEGRADE_LEVEL 文件 | 文件写入失败时降级不生效 | 使用 API 降级作为备份通道 | v86.1 |
| 5 | 灰度门禁评估频率固定 | P0 每分钟, P1 每 5 分钟, 不可配置 | 调整 alias_degrade_controller.py 中的评估间隔 | v86.1 |

### 5.2 性能限制

| # | 限制 | 影响 | 规避方案 |
|---|------|------|----------|
| 1 | 单实例 QPS 上限 ~2,000/s | 超过 2,000 QPS 需水平扩展 | K8s HPA 自动扩容 |
| 2 | 冷启动 22.74s | 滚动更新期间需预留额外 Pod | maxSurge=1, maxUnavailable=0 |
| 3 | 首次请求 (无缓存) 0.14ms | 低于 0.14ms 不可达 (Python 限制) | 使用热缓存路径 0.01ms |
| 4 | 内存占用 ~128MB | 单实例内存限制 | 调整 K8s memory limits |

### 5.3 兼容性限制

| # | 限制 | 影响 | 规避方案 |
|---|------|------|----------|
| 1 | 依赖 V85 别名库 (只读) | 别名库更新需重新部署 | 通过 PR + 重新构建镜像 |
| 2 | 不兼容 zhiji API 调用 | 无法获取实时数据 | 使用离线别名库 |
| 3 | Python 3.8+ 要求 | 低版本 Python 不兼容 | 使用 Docker 镜像 (内置 Python 3.11) |
| 4 | 不兼容 Windows 部署 | 仅支持 Linux | 使用 Docker/K8s 部署 |

---

## 6. 基线对比 (V85)

### 6.1 裁决分布对比

| 模式 | PASS (A) | REVIEW (R) | BLOCK (B) | 总计 |
|------|----------|------------|-----------|------|
| V85 base | 4,603 (99.14%) | 0 (0%) | 40 (0.86%) | 4,643 |
| V86 base | 4,603 (99.14%) | 0 (0%) | 40 (0.86%) | 4,643 |
| V86 f3 | 4,425 (95.30%) | 165 (3.55%) | 53 (1.14%) | 4,643 |
| V86 f3+f4 | 4,476 (96.40%) | 165 (3.55%) | 2 (0.04%) | 4,643 |

### 6.2 关键差异分析

| 差异项 | V85 | V86 (f3+f4) | Δ | 原因 |
|--------|-----|-------------|---|------|
| PASS 率 | 99.14% | 96.40% | -2.74pp | F3+F4 引入更严格门禁, 误放行减少 |
| REVIEW 率 | 0% | 3.55% | +3.55pp | F2 歧义解析输出 AMBIGUOUS |
| BLOCK 率 | 0.86% | 0.04% | -0.82pp | F4 抑制同名对误阻断 |
| 吞吐 | ~1,500/s | 2,144/s | +42.9% | 缓存优化 + 异步任务 |
| 首次请求 | ~5ms | 0.01ms | -99.8% | LRU 缓存命中 |
| 内存 | ~70MB | ~128MB | +82.9% | 缓存 + 四态解析 |
| 冷启动 | ~20s | 22.74s | +13.7% | 四层修复初始化 |

### 6.3 V85 行为保留

V86 在 `base` 模式下完全保留 V85 行为:
- PASS 率: 99.14% (与 V85 一致)
- BLOCK 率: 0.86% (与 V85 一致)
- 裁决分布: 完全一致
- 用途: 作为降级回退目标

---

## 7. 分模块说明

### 7.1 别名解析流水线

```
┌─────────────────────────────────────────────────────────────────────┐
│  V86 别名解析流水线                                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  输入: 别名名称                                                      │
│                                                                     │
│  P0 预处理    →  别名规范化 (trim/lower/strip)                       │
│       ↓                                                             │
│  P1 别名查找   →  M 字典索引查询                                      │
│       ↓                                                             │
│  F1 异常兜底   →  KeyError 安全捕获, 未命中返回 NO_MATCH              │
│       ↓                                                             │
│  P2 门禁链     →  R-01/R-02/R-05/R-07 等门禁规则                     │
│       ↓                                                             │
│  F2 确定性解析 →  UNIQUE/AMBIGUOUS/NO_MATCH/UNREGISTERED            │
│       ↓                                                             │
│  F3 门禁重排   →  R-05 优先于 R-07                                  │
│       ↓                                                             │
│  F4 自触发抑制 →  同名对子串包含/复合短语抑制                          │
│       ↓                                                             │
│  P3 裁决输出   →  PASS/REVIEW/BLOCK + reason + canonical_key        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 F3/F4 判定模块

| 模块 | 功能 | 触发条件 | 降级级别 |
|------|------|----------|----------|
| F3 | 门禁重排: R-05 黑名单优先 | 别名在黑名单中 | L0-L1 启用, L2-L3 关闭 |
| F4a | 子串包含抑制 | 别名 A 是别名 B 的子串 | L0 启用, L1-L3 关闭 |
| F4b | 复合短语抑制 | 复合短语包含关系 | L0 启用, L1-L3 关闭 |

### 7.3 缓存预热模块

| 组件 | 配置 | 说明 |
|------|------|------|
| LRU 缓存 | max_size=1024 | 热路径缓存, 14x 加速 |
| 持久化 | 300s interval | 周期性持久化至 pkl |
| 预热样本 | 18 条 | 跨品种常见别名 |
| 预热耗时 | 4.89s | 启动时一次性预热 |
| 关机持久化 | SIGTERM trap | 优雅退出时保存缓存 |

### 7.4 灰度控制器模块

| 组件 | 配置 | 说明 |
|------|------|------|
| 流量分配 | Envoy weighted cluster | 10%→30%→100% |
| 门禁评估 | 12 道, 实时 | P0 每分钟, P1 每 5 分钟 |
| 自动降级 | P0 FAIL → 自动降级 | L0→L1→L2→L3 |
| 告警通知 | P1/P2 → 告警 | Slack/PagerDuty |

### 7.5 降级控制器模块

| 组件 | 配置 | 说明 |
|------|------|------|
| 降级级别 | L0/L1/L2/L3 | 四级降级 |
| 触发通道 | DEGRADE_LEVEL 文件 + API | 双通道 |
| 评估频率 | 每分钟 | 自动评估 |
| 自动恢复 | 恢复条件满足后 | 自动恢复上一级别 |
| 审计日志 | degrade_audit.log | 完整降级历史 |

### 7.6 监控埋点模块

| 组件 | 配置 | 说明 |
|------|------|------|
| Prometheus | /metrics endpoint | 15s 采集 |
| Grafana | Dashboard JSON | 6 类面板 |
| 日志 | JSON structured | Loki 兼容 |
| 健康检查 | /healthz endpoint | 6 字段返回 |
| 错误码 | E000~E201 | 标准化错误码 |

---

## 8. 风险边界与业务影响

### 8.1 风险矩阵

| 风险 | 概率 | 影响 | 等级 | 缓解措施 |
|------|------|------|------|----------|
| 别名解析错误导致数据错误 | 低 | 高 | 中 | F2 确定性解析, REVIEW 状态可追溯 |
| 灰度放量后 PASS 率下降 | 中 | 中 | 中 | 12 道门禁监控, 自动降级 |
| 冷启动超时影响可用性 | 低 | 中 | 低 | maxSurge=1, maxUnavailable=0 |
| 缓存失效导致延迟上升 | 低 | 低 | 低 | 300s 持久化, 预热恢复 |
| 降级控制器失效 | 低 | 高 | 中 | API 降级作为备份通道 |
| Envoy 流量切换失败 | 低 | 中 | 低 | 手动切换脚本, 告警通知 |
| 引擎崩溃导致服务中断 | 低 | 高 | 中 | K8s 自动重启 + Envoy 切 V85 |

### 8.2 业务影响

| 场景 | V85 影响 | V86 影响 | 变化 |
|------|----------|----------|------|
| 正常解析 | PASS 99.14% | PASS 96.40% | -2.74pp (更严格门禁) |
| 歧义别名 | 静默选择 | REVIEW 状态 | 可追溯, 需人工复核 |
| 黑名单别名 | 可能绕过 | BLOCK (F3 重排) | 更安全 |
| 同名对 | 可能误阻断 | F4 抑制 | 更准确 |
| 未注册别名 | 静默忽略 | UNREGISTERED 状态 | 可追溯 |
| 性能 | ~1,500/s | 2,144/s | +42.9% 提升 |
| 可用性 | 无降级 | 四级降级 | 更强韧性 |

### 8.3 业务方注意事项

1. **PASS 率下降 2.74pp**: 这是 F3+F4 引入更严格门禁的预期效果, 在 5pp 安全阈值内
2. **REVIEW 状态新增**: 165 条歧义别名将输出 REVIEW 状态, 需人工复核后更新别名库
3. **长尾歧义**: 34 条长尾歧义样本 (atomic_keys ≥ 5), 需人工裁决
4. **未注册别名**: 14 条 UNREGISTERED 别名, 需开发团队介入添加
5. **降级影响**: L1 降级后 PASS 率降至 95.30%, L2 降级后恢复至 99.14% (V85 行为)

---

## 9. 开关说明

### 9.1 引擎模式开关

| 开关 | 值 | 说明 | 切换方式 |
|------|-----|------|----------|
| V86_ALIAS_MODE | f3+f4 | 生产推荐模式 | 环境变量 / API |
| V86_ALIAS_MODE | f3 | F4 关闭 | 环境变量 / API |
| V86_ALIAS_MODE | base | F3+F4 关闭 (V85 行为) | 环境变量 / API |

```bash
# 环境变量 (部署时)
export V86_ALIAS_MODE="f3+f4"

# API (运行时, 无需重启)
curl -X POST http://v86-alias-engine:8080/api/mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"f3+f4"}'

# 降级文件
echo "DEGRADE_LEVEL=0" > /etc/v86/degrade_level
```

### 9.2 预热开关

| 开关 | 值 | 说明 |
|------|-----|------|
| V86_WARMUP | true | 启动时预热 (默认) |
| V86_WARMUP | false | 跳过预热 |

### 9.3 缓存持久化开关

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| cache.lru.persist_on_shutdown | true | 关机时持久化 |
| cache.lru.persist_interval_seconds | 300 | 持久化间隔 |
| cache.persistence.enabled | true | 启用持久化 |
| cache.persistence.atomic_write | true | 原子写入 |
| cache.persistence.backup_on_write | true | 写入前备份 |

### 9.4 降级级别开关

| 级别 | DEGRADE_LEVEL | 模式 | 说明 |
|------|---------------|------|------|
| L0 | 0 | f3+f4 | 正常模式 |
| L1 | 1 | f3 | F4 关闭 |
| L2 | 2 | base | F3+F4 关闭 |
| L3 | 3 | V85 基线 | 完全回退 |

---

## 10. 回退路径

### 10.1 运行时回退 (推荐)

```
L0 (f3+f4) ──错误率/耗时异常──→ L1 (f3, F4 off)
                                      │
L0 (f3+f4) ──歧义率异常──────→ L2 (base, F3+F4 off)
                                      │
L0 (f3+f4) ──引擎崩溃/数据异常──→ L3 (V85 基线)
```

| 回退路径 | 切换耗时 | 流量中断 | 恢复条件 |
|----------|----------|----------|----------|
| L0→L1 | 3s | 0 | error_rate ≤ 0.05% 持续 10min |
| L0→L2 | 3s | 0 | ambiguity_rate ≤ 3% 持续 30min |
| L0→L3 | 3s | 0 | 人工确认 |
| L1→L0 | 2s | 0 | error_rate ≤ 0.05% 持续 10min |
| L2→L0 | 2s | 0 | ambiguity_rate ≤ 3% 持续 30min |

### 10.2 版本回退 (最后手段)

```bash
# 1. 切换至 V85 基线 Pod
envoy_config_reload --cluster v85_baseline --weight 100

# 2. 确认 V85 就绪
curl http://v85-alias-baseline:8080/healthz

# 3. 更新降级级别
echo "DEGRADE_LEVEL=3" > /etc/v86/degrade_level

# 4. (可选) 停止 V86 Pod
kubectl scale deployment -n dshe-v86 v86-alias-engine --replicas=0
```

### 10.3 回退后恢复

```bash
# 1. 启动 V86 Pod
kubectl scale deployment -n dshe-v86 v86-alias-engine --replicas=2

# 2. 等待就绪
kubectl rollout status deployment/v86-alias-engine -n dshe-v86

# 3. 预热引擎
python3 alias_engine_warmup_optimize.py --warmup

# 4. 验证
curl http://v86-alias-engine:8080/healthz

# 5. 切换流量回 V86
envoy_config_reload --cluster v86-alias --weight 100

# 6. 更新降级级别
echo "DEGRADE_LEVEL=0" > /etc/v86/degrade_level
```

---

## 11. 变更追溯链

### 11.1 Git Commit 链

| Commit | 日期 | 说明 |
|--------|------|------|
| `bcd64dd` | 2026-09-30 | E 后端异步任务 API 定义 |
| `168a073` | 2026-10-01 | V86 别名引擎原型 (F1+F2+F3+F4) |
| `d16310e` | 2026-10-01 | 联合集成+预上线检查 |
| `f694618` | 2026-10-02 | DSHB 规则引擎全量回放+生产bundle |
| `ab95859` | 2026-10-02 | V86 别名引擎全量回放报告 |
| `81268a6` | 2026-10-02 | 生产部署包+灰度方案+降级预案+监控规范 |
| `d1e070d` | 2026-10-02 | 运维手册+灰度仿真+资产固化 (本版本基线) |

### 11.2 资产版本链

```
V85 别名库 (冻结, 4,643 条目)
  └── V86AliasEngine v86.0.0-frozen (F1+F2+F3+F4, 模式 base/f3/f3+f4)
        ├── V86AliasTaskAdapter v1.0 (dshe_alias_resolve)
        ├── V86AliasWarmupOptimize v1.0 (单例+LRU 缓存)
        ├── V86AliasGateAutoCheck v1.0 (14 道门禁)
        ├── V86AliasFullReplay v1.0 (4,643 条回放)
        ├── V86AliasProductionBundle v1.0 (Docker/K8s/Compose)
        ├── V86AliasGrayReleasePlan v1.0 (12 道灰度门禁)
        ├── V86AliasDegradePlan v1.0 (L1/L2/L3 降级)
        ├── V86AliasMonitorSpec v1.0 (Prometheus/Grafana)
        ├── V86AliasProdIntegrateVerify v1.0 (113 项校验)
        ├── V86AliasGrayFullSimulation v1.0 (8 阶段仿真)
        └── V86AliasOpsManualFinal v1.0 (运维手册终稿)
```

### 11.3 变更追溯

| 变更 | 来源 | 影响 | 追溯方式 |
|------|------|------|----------|
| 别名库 | V85 冻结 (f313570) | 4,643 条目, 只读 | `v85_final_archive/MD5_MANIFEST.md` |
| F1-F4 修复 | V86 原型 (168a073) | 四层修复 | `v86_alias_engine_prototype.py` |
| 门禁自动化 | 联合检查 (d16310e) | 14 道门禁 | `alias_gate_auto_check.py` |
| 全量回放 | 生产准备 (ab95859) | 4,643 条验证 | `v86_alias_full_replay_report.md` |
| 灰度方案 | 生产准备 (81268a6) | 12 道灰度门禁 | `v86_alias_gray_release_plan.md` |
| 降级预案 | 生产准备 (81268a6) | L1/L2/L3 | `v86_alias_degrade_plan.md` |
| 监控规范 | 生产准备 (81268a6) | Prometheus/Grafana | `v86_alias_monitor_spec.md` |
| 运维手册 | 运维终稿 (d1e070d) | 11 章 + 10 FAQ | `v86_alias_ops_manual_final.md` |
| 灰度仿真 | 运维终稿 (d1e070d) | 8 阶段全绿 | `v86_alias_gray_full_simulation.md` |
| 资产固化 | 运维终稿 (d1e070d) | 28 文件, MD5 校验 | `v86_alias_frozen_asset_bundle.md` |

---

## 12. 关联资产索引

### 12.1 本次交付资产

| 文件 | MD5 | 说明 |
|------|-----|------|
| `v86_alias_gate_demo_package.md` | (本文件) | Gate 评审演示包 |
| `v86_alias_release_note_final.md` | (本文件) | Release Note 终稿 |
| `v86_alias_gate_qakb.md` | (待生成) | Gate 评审问答知识库 |
| `v86_alias_portal_data_cross_check.md` | (待生成) | 门户数据交叉核验 |
| `MD5_CHECKSUM_LIST.md` | (待生成) | MD5 校验清单 |

### 12.2 前置交付资产 (MD5 索引)

| 资产 | MD5 | 文件 |
|------|-----|------|
| 引擎原型 | E77C8E3692235F1CCE83076920F118C9 | `v86_alias_engine_prototype.py` |
| 任务适配层 | DC88D82E1F6BDF2802EBF4B5091647E3 | `alias_task_adapter.py` |
| 预热优化 | 48EB5AC0ADE4ACBB1FD1FA8C9DE29609 | `alias_engine_warmup_optimize.py` |
| 门禁自动化 | C8A0F439AE6D9318D4DDAAF0730ACC06 | `alias_gate_auto_check.py` |
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

## 13. 约束合规

| 约束 | 状态 |
|------|------|
| NO_ZHIJI_API_CALL=TRUE | ✅ 无外部 API 调用 |
| NO_MODIFY_V85=TRUE | ✅ V85 基线别名库只读 |
| NO_OVERWRITE=TRUE | ✅ 仅新增文件, 不覆盖历史交付物 |
| BRANCH_LOCKED=TRUE | ✅ 仅 feature/v85-chart-template 提交 |
| 所有演示素材使用仿真环境数据 | ✅ 基于 replay_results.json |

---

*Release Note 终稿由 DSHE_V86_ALIAS_GATE_DEMO_ASSEMBLY_AND_RELEASE_NOTE_COMPILE T2.2 生成*
*分支: feature/v85-chart-template · Commit: d1e070d · 资产版本: v86.0.0-frozen*
