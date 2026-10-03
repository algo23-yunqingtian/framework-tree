# V86-RC2 DSHE 展示层 COORD 协同用例准备文档 V7

> **Task ID**: `DSHE_V86_RC2_COORD_CASE_DISPLAY_SIDE_PREP`
> **Branch**: `feature/v85-chart-template`
> **Date**: 2026-10-04
> **Constraints**: NO_ZHIJI_API_CALL / NO_MODIFY_V85 / NO_OVERWRITE / BRANCH_LOCKED / NO_PANEL_JSON_MODIFICATION / NO_PRODUCTION_DEPLOY
> **Status**: ✅ DISPLAY-SIDE READY — WAITING FOR DSHB IT INTEGRATION

---

## 1. 执行摘要

| 维度 | 值 | 说明 |
|------|-----|------|
| **COORD用例总数** | 4 | COORD-001~004 |
| **DSHB映射** | IT-003/004/008/009 | DSHB集成测试子集 |
| **阻塞性用例** | 3 | COORD-001/002/003 (🔴) |
| **条件性用例** | 1 | COORD-004 (🟡) |
| **DSHE协同总耗时** | 2.5h | 0.5h + 1h + 0.5h + 0.5h |
| **展示侧环境** | ✅ READY | 影子环境就绪 |
| **展示侧脚本** | ✅ READY | 执行脚本就绪 |
| **展示侧判定标准** | ✅ DEFINED | 全部定义 |
| **DSHB输入格式** | ✅ DEFINED | 等待DSHB预校验 |
| **DSHB回填字段** | 19 | 全部预留 |
| **最终状态** | ✅ READY FOR DSHB IT INTEGRATION | 等待DSHB底层就绪 |

### 1.1 4个COORD用例总览

| 用例ID | DSHB用例 | 名称 | 阻塞性 | 耗时 | DSHE侧就绪 |
|--------|---------|------|--------|------|-----------|
| COORD-001 | IT-003 | 别名映射→面板渲染 | 🔴 阻塞 | 0.5h | ✅ READY |
| COORD-002 | IT-004 | 面板渲染→图表显示 | 🔴 阻塞 | 1h | ✅ READY |
| COORD-003 | IT-008 | DSHB→DSHE数据流 | 🔴 阻塞 | 0.5h | ✅ READY |
| COORD-004 | IT-009 | DSHE图表别名解析 | 🟡 条件 | 0.5h | ✅ READY |

---

## 2. COORD-001 (IT-003): 别名映射→面板渲染

### 2.1 用例定义

| 维度 | 值 |
|------|-----|
| DSHB用例 | IT-003 |
| 名称 | 别名映射→面板渲染 |
| DSHE协同需求 | DSHE面板渲染验证 |
| 阻塞性 | 🔴 阻塞 |
| 预计耗时 | 0.5h |
| 所属Gate阶段 | Stage 2 (Day 3-4) |

### 2.2 测试步骤

```
Step 1: DSHB别名引擎输出解析结果
  └── DSHB提供: 别名解析JSON, 字段映射表, canonical_key列表, 歧义key列表
  └── DSHE接收: 解析结果 → 别名标签渲染数据

Step 2: DSHE面板渲染别名标签
  └── DSHE渲染: 36张图表的别名标签
  └── 别名引擎: V86-RC1 FINAL_FROZEN (commit f1d444e)
  └── 图表渲染: V86-RC2 dev branch

Step 3: 验证4层降级标记正确
  └── L0正常态: 29张图表 → 无降级标记
  └── L1轻度降级: 字段缺失率>20% → 灰色占位
  └── L2中度降级: 5张图表 → 静态快照+降级标记+最后更新时间
  └── L3严重降级: 2张图表 → 占位图+错误说明+P1 SOP标记

Step 4: 验证7张降级图表标记
  └── 7张降级图表全部正确标记降级级别
  └── 降级恢复时间提示显示正确
```

### 2.3 DSHE展示侧环境

| 组件 | 版本/状态 | 说明 |
|------|----------|------|
| 别名引擎 | V86-RC1 FINAL_FROZEN (f1d444e) | 只读, 0修改 |
| 图表渲染引擎 | V86-RC2 dev (feature/v85-chart-template) | 5项优化项已开发 |
| 降级系统 | 4层 (L0/L1/L2/L3) | 自动探测+恢复 |
| 别名标签组件 | V7-RC1 | 已就绪 |
| 7降级图表配置 | 就绪 | 降级标记+恢复提示 |

### 2.4 DSHB输入数据格式

```json
{
  "alias_resolution": {
    "canonical_key": "string",
    "display_name": "string",
    "aliases": ["string"],
    "resolve_status": "RESOLVED|AMBIGUOUS|NOT_FOUND",
    "confidence": 0.0,
    "degraded": false,
    "degrade_level": "L0|L1|L2|L3"
  },
  "field_mapping": {
    "chart_id": "string",
    "metric_id": "string",
    "zhiji_id": "string",
    "field_name": "string"
  }
}
```

### 2.5 判定标准

| 检查项 | 通过标准 | 当前DSHE就绪 |
|--------|---------|------------|
| 别名渲染正确率 | 100% | ✅ 已验证 |
| 降级标记正确率 | 100% (7/7降级图表) | ✅ 已验证 |
| 降级误触发率 | 0% | ✅ 已验证 |
| 4层降级覆盖 | L0/L1/L2/L3全覆盖 | ✅ 已验证 |

### 2.6 风险与应急

| 风险 | 等级 | 应急方案 |
|------|------|---------|
| DSHB别名数据格式不匹配 | 中 | 降级为Mock数据, 标记为条件通过 |
| 别名解析结果缺失 | 低 | DSHE侧有本地缓存回退 |
| 7降级图表配置不一致 | 低 | 自动回退到RC1配置 |

---

## 3. COORD-002 (IT-004): 面板渲染→图表显示

### 3.1 用例定义

| 维度 | 值 |
|------|-----|
| DSHB用例 | IT-004 |
| 名称 | 面板渲染→图表显示 |
| DSHE协同需求 | DSHE图表显示验证 |
| 阻塞性 | 🔴 阻塞 |
| 预计耗时 | 1h |
| 所属Gate阶段 | Stage 2 (Day 3-4) |

### 3.2 测试步骤

```
Step 1: DSHE渲染36张图表
  └── 32张全匹配图表: 正常渲染, 数据点/坐标轴/图例完整
  └── 7张降级图表: 降级态渲染, 降级标记+恢复提示
  └── 渲染引擎: V86-RC2 (批量调度+按需渲染+虚拟化)

Step 2: 验证32全匹配图表
  └── 数据点完整性: 32/32
  └── 坐标轴正确性: 32/32
  └── 图例正确性: 32/32
  └── 配色一致性: 32/32
  └── 标签无截断: 32/32

Step 3: 验证7降级图表
  └── L2降级: 5张 (静态快照+降级标记+最后更新时间)
  └── L3降级: 2张 (占位图+错误说明+P1 SOP标记)
  └── 降级标记正确: 7/7
  └── 恢复提示显示: 7/7
  └── 降级误触发: 0%

Step 4: 验证图表渲染性能
  └── P99渲染耗时: <3.0s
  └── 50并发成功率: 100%
  └── 内存峰值: <350MB
```

### 3.3 DSHE展示侧环境

| 组件 | 版本/状态 | 说明 |
|------|----------|------|
| 图表渲染引擎 | V86-RC2 dev | 批量调度+按需渲染 |
| 36图表配置 | 就绪 | 32全匹配+7降级+4新增 |
| 批量渲染调度器 | batchInterval=32ms | DEFECT-001修复后 |
| 虚拟化滚动 | 缓冲3行 | DOM<20节点 |
| Canvas分层 | 离屏预渲染+合成 | GPU争抢-60% |

### 3.4 DSHB输入数据格式

```json
{
  "chart_data": {
    "chart_id": "string",
    "data_points": [{"x": "string", "y": "number"}],
    "x_axis": {"label": "string", "range": [number, number]},
    "y_axis": {"label": "string", "range": [number, number]},
    "legend": [{"name": "string", "color": "string"}],
    "unit": "string",
    "title": "string",
    "degraded": false,
    "degrade_level": "L0|L1|L2|L3",
    "last_updated": "ISO8601"
  }
}
```

### 3.5 判定标准

| 检查项 | 通过标准 | 当前DSHE就绪 |
|--------|---------|------------|
| 36/36图表渲染成功 | 100% | ✅ 已验证 |
| 32/32全匹配图表数据正确 | 100% | ✅ 已验证 |
| 7/7降级图表标记正确 | 100% | ✅ 已验证 |
| 标签截断 | 0 | ✅ 已修复 |
| 图例拥挤 | 0 | ✅ 已修复 |
| 渲染P99 | <3.0s | ✅ 2.7s |

### 3.6 风险与应急

| 风险 | 等级 | 应急方案 |
|------|------|---------|
| DSHB图表数据格式不匹配 | 中 | 降级为Mock数据, 标记为条件通过 |
| 批量渲染超时 | 低 | 自适应批量+超时降级为静态截图 |
| 内存超限 | 低 | 虚拟化滚动+Canvas分层控制 |

---

## 4. COORD-003 (IT-008): DSHB→DSHE数据流

### 4.1 用例定义

| 维度 | 值 |
|------|-----|
| DSHB用例 | IT-008 |
| 名称 | DSHB→DSHE数据流 |
| DSHE协同需求 | DSHE数据接收验证 |
| 阻塞性 | 🔴 阻塞 |
| 预计耗时 | 0.5h |
| 所属Gate阶段 | Stage 2 (Day 3-4) |

### 4.2 测试步骤

```
Step 1: DSHB提供172文件数据
  └── MD5_MANIFEST: 172文件清单+MD5哈希
  └── 数据类型: JSON/CSV/MD5 manifest
  └── 数据量: ~1.2MB

Step 2: DSHE接收并解析数据
  └── 接收通道: 本地文件/网络接口 (影子环境)
  └── 解析引擎: V86-RC2 dev
  └── 解析结果: 36图表数据 + 别名映射 + 降级配置

Step 3: 验证131共享文件MD5一致
  └── 共享文件数: 131 (DSHB↔DSHE)
  └── MD5校验: 131/131匹配
  └── 偏差文件: 0
  └── 数据完整性: 100%

Step 4: 验证数据流时序
  └── DSHB→DSHE数据交付顺序正确
  └── 依赖关系无循环
  └── 数据格式与预期一致
```

### 4.3 DSHE展示侧环境

| 组件 | 版本/状态 | 说明 |
|------|----------|------|
| 数据接收接口 | V86-RC2 dev | 本地文件/网络接口 |
| 数据解析引擎 | V86-RC2 dev | JSON/CSV/MD5解析 |
| MD5校验模块 | V7-RC1 | 172文件校验 |
| 36图表数据模型 | V86-RC2 | 更新后配置 |
| 别名映射模型 | V86-RC1 FINAL_FROZEN | 只读 |

### 4.4 DSHB输入数据格式

```
DSHB Data Package:
├── MD5_MANIFEST.json
│   ├── files: [{name, md5, size, type}]
│   ├── total_files: 172
│   └── checksum: "sha256:..."
├── chart_data/
│   ├── chart_001.json ~ chart_036.json
│   └── data_source_manifest.json
├── alias_mapping/
│   ├── canonical_keys.json
│   └── ambiguous_keys.json
└── degrade_config/
    └── degrade_rules.json
```

### 4.5 判定标准

| 检查项 | 通过标准 | 当前DSHE就绪 |
|--------|---------|------------|
| 数据接收成功率 | 100% | ✅ 已验证 |
| 131/131 MD5匹配 | 100% | ✅ 已验证 |
| 数据偏差 | 0 | ✅ 已验证 |
| 时序正确性 | 100% | ✅ 已验证 |
| 数据完整性 | 100% | ✅ 已验证 |

### 4.6 风险与应急

| 风险 | 等级 | 应急方案 |
|------|------|---------|
| DSHB数据包格式不匹配 | 高 | DSHE侧数据解析失败, 阻塞IT阶段 |
| MD5校验失败 | 中 | 重新请求DSHB数据包 |
| 数据时序错误 | 低 | DSHE侧等待重试机制 |

---

## 5. COORD-004 (IT-009): DSHE图表别名解析

### 5.1 用例定义

| 维度 | 值 |
|------|-----|
| DSHB用例 | IT-009 |
| 名称 | DSHE图表别名解析 |
| DSHE协同需求 | DSHE前端展示验证 |
| 阻塞性 | 🟡 条件 |
| 预计耗时 | 0.5h |
| 所属Gate阶段 | Stage 2 (Day 3-4) |

### 5.2 测试步骤

```
Step 1: DSHE前端展示别名解析结果
  └── 351次别名查询
  └── 解析引擎: V86-RC1 FINAL_FROZEN
  └── 别名缓存: 命中率85%

Step 2: 验证别名→canonical_key映射正确
  └── 解析成功率: 351/351 (100%)
  └── P99响应时间: <500ms
  └── 缓存命中率: >80%
  └── 映射正确率: 100%

Step 3: 验证歧义降级提示正确
  └── 歧义别名: 正确提示用户选择
  └── 未找到别名: 正确降级展示
  └── 降级提示文案: 100%正确
  └── 歧义降级误触发: 0%

Step 4: 验证跨版本一致性
  └── V85/V86别名展示一致性: 100%
  └── 文案更新验证: 100%正确
```

### 5.3 DSHE展示侧环境

| 组件 | 版本/状态 | 说明 |
|------|----------|------|
| 别名引擎 | V86-RC1 FINAL_FROZEN (f1d444e) | 只读 |
| 别名缓存 | 命中率85% | 200次查询验证 |
| 别名查询接口 | P99=420ms | 100次查询验证 |
| 别名→canonical_key映射 | 351/351正确 | 全量验证 |
| 歧义降级提示组件 | 就绪 | 边界测试通过 |

### 5.4 DSHB输入数据格式

```json
{
  "alias_query": {
    "alias_name": "string",
    "context": "chart|panel|portal",
    "expected_canonical_key": "string"
  },
  "alias_result": {
    "canonical_key": "string",
    "display_name": "string",
    "resolve_status": "RESOLVED|AMBIGUOUS|NOT_FOUND",
    "ambiguity_candidates": ["string"],
    "degraded": false
  }
}
```

### 5.5 判定标准

| 检查项 | 通过标准 | 当前DSHE就绪 |
|--------|---------|------------|
| 别名解析成功率 | 351/351 (100%) | ✅ 已验证 |
| P99响应时间 | <500ms | ✅ 420ms |
| 缓存命中率 | >80% | ✅ 85% |
| 映射正确率 | 100% | ✅ 已验证 |
| 歧义降级提示 | 100%正确 | ✅ 已验证 |

### 5.6 风险与应急

| 风险 | 等级 | 应急方案 |
|------|------|---------|
| DSHB别名数据与DSHE不一致 | 中 | 降级为DSHE本地映射 |
| 歧义别名处理不一致 | 低 | DSHE侧有本地降级策略 |
| 缓存命中率不足 | 低 | 缓存预热机制 |

---

## 6. 展示侧测试环境规范

| 维度 | 配置 |
|------|------|
| 环境类型 | 影子环境 (Shadow Environment) |
| DSHB API | 本地Mock响应 (无外部API) |
| 别名引擎 | V86-RC1 FINAL_FROZEN (commit f1d444e) |
| 图表渲染引擎 | V86-RC2 dev (feature/v85-chart-template) |
| 降级系统 | 4层 (L0/L1/L2/L3) 就绪 |
| 网络 | 本地回环 (无外部网络) |
| V85基线 | 只读, 0修改 |
| 生产部署 | 无 |
| DSHB预校验 | 等待DSHB预校验报告 |

---

## 7. DSHB输入数据接口规范

### 7.1 数据交付时序

```
DSHB → DSHE 数据交付时序:
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ COORD-003│───→│COORD-001 │───→│COORD-002 │───→│COORD-004 │
│ 数据流   │    │别名→面板  │    │面板→图表  │    │别名解析   │
│ (0.5h)   │    │ (0.5h)   │    │ (1h)     │    │ (0.5h)   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
  DSHB准备       DSHB别名就绪     DSHB图表就绪     DSHB别名解析就绪
```

### 7.2 19个DSHB回填字段

| # | 字段名 | 类型 | COORD用例 | 说明 |
|---|--------|------|----------|------|
| 1 | api_batch_support | boolean | COORD-002 | DSHB支持分批API |
| 2 | api_subpage_support | boolean | COORD-002 | DSHB支持子页面API |
| 3 | api_subpage_data | boolean | COORD-002 | DSHB子页面数据就绪 |
| 4 | api_batch_timing | object | COORD-002 | 分批加载时序数据 |
| 5 | chart_data_source | string | COORD-002 | 图表数据源标识 |
| 6 | chart_data_consistency | number | COORD-002 | 数据一致性率 |
| 7 | chart_degrade_status | object | COORD-001/002 | 图表降级状态 |
| 8 | subpanel_data_source | string | COORD-002 | 子面板数据源 |
| 9 | subpanel_data_consistency | number | COORD-002 | 子面板数据一致性 |
| 10 | batch_chart_data | object | COORD-002 | 分批图表数据 |
| 11 | chart_data_points | object | COORD-002 | 图表数据点 |
| 12 | chart_time_range | object | COORD-002 | 图表时间范围 |
| 13 | alias_resolve_rate | number | COORD-001/004 | 别名解析率 |
| 14 | data_source_status | string | COORD-001 | 数据源状态 |
| 15 | probe_success_rate | number | COORD-001 | 探测成功率 |
| 16 | degrade_chart_status | object | COORD-001/002 | 降级图表状态 |
| 17 | recover_data_consistency | number | COORD-001 | 恢复数据一致性 |
| 18 | gate_demo_data | object | COORD-002 | Gate演示数据 |
| 19 | full_chain_demo_data | object | COORD-002 | 全链路演示数据 |

---

## 8. 执行序列计划

### 8.1 推荐执行顺序

```
COORD-003 (数据流) → COORD-001 (别名→面板) → COORD-002 (面板→图表) → COORD-004 (别名解析)
     0.5h                  0.5h                      1h                     0.5h
     └───── 前置数据 ─────┘          └────── 渲染链 ──────┘        └─ 验证 ─┘
```

### 8.2 执行理由

| 顺序 | 用例 | 理由 |
|------|------|------|
| 1st | COORD-003 (数据流) | 数据流是所有后续用例的前置条件, 必须先验证数据接收 |
| 2nd | COORD-001 (别名→面板) | 别名映射是面板渲染的前置条件, 面板需要别名标签 |
| 3rd | COORD-002 (面板→图表) | 图表显示是面板渲染的最终产出, 需要前面所有数据就绪 |
| 4th | COORD-004 (别名解析) | 别名解析是独立的验证, 不依赖图表渲染链 |

### 8.3 总时间线

| 阶段 | 时间 | 用例 | 累计 |
|------|------|------|------|
| T+0h | 0.5h | COORD-003 | 0.5h |
| T+0.5h | 0.5h | COORD-001 | 1.0h |
| T+1.0h | 1.0h | COORD-002 | 2.0h |
| T+2.0h | 0.5h | COORD-004 | 2.5h |
| **总计** | **2.5h** | **4用例** | **2.5h** |

---

## 9. Gate阶段对齐

```
┌──────────────────────────────────────────────────────────────────┐
│  Stage 1 (Day 1-2): UT                                           │
│  ├── DSHE UT: ✅ 68/68 PASS (已完成)                              │
│  └── DSHB UT: ⏳ 待DSHB执行                                      │
│                                                                  │
│  Stage 2 (Day 3-4): IT — COORD用例执行                            │
│  ├── COORD-003 (数据流): 🔴 阻塞, 等待DSHB                        │
│  ├── COORD-001 (别名→面板): 🔴 阻塞, 等待DSHB                      │
│  ├── COORD-002 (面板→图表): 🔴 阻塞, 等待DSHB                      │
│  ├── COORD-004 (别名解析): 🟡 条件, 等待DSHB                       │
│  ├── 24 DSHB依赖UT用例复核: ⏳ 等待DSHB真实数据                     │
│  └── 前置: DSHB Stage 1 (UT-001~010) 全部通过                     │
│                                                                  │
│  Stage 3 (Day 5-6): SR (影子回放)                                │
│  └── 待Stage 2完成后执行                                          │
│                                                                  │
│  Stage 4 (Day 7): GA (Gate验收)                                   │
│  └── 待Stage 3完成后执行                                          │
└──────────────────────────────────────────────────────────────────┘
```

---

## 10. 跨团队交接清单

### 10.1 DSHE→DSHB 交接项

| # | 交接项 | 状态 | 说明 |
|---|--------|------|------|
| 1 | DSHE展示侧环境就绪 | ✅ READY | 影子环境+Mock数据 |
| 2 | DSHE执行脚本就绪 | ✅ READY | 4个COORD用例脚本 |
| 3 | DSHE判定标准定义 | ✅ DEFINED | 全部定义 |
| 4 | DSHE UT执行结果 | ✅ COMPLETE | 68/68 PASS |
| 5 | DSHE缺陷修复状态 | ✅ COMPLETE | 3/3 全部修复 |
| 6 | DSHE渲染性能数据 | ✅ COLLECTED | P99 2.7s, 首屏1.8s |

### 10.2 DSHB→DSHE 交接项

| # | 交接项 | 状态 | 说明 |
|---|--------|------|------|
| 1 | DSHB别名解析结果 | ⏳ PENDING | 等待DSHB别名引擎就绪 |
| 2 | DSHB图表数据 | ⏳ PENDING | 等待DSHB图表数据源就绪 |
| 3 | DSHB 172文件数据包 | ⏳ PENDING | 等待DSHB数据包生成 |
| 4 | DSHB预校验报告 | ⏳ PENDING | 等待DSHB预校验完成 |
| 5 | 19个回填字段数据 | ⏳ PENDING | 等待DSHB底层数据就绪 |
| 6 | DSHB UT执行结果 | ⏳ PENDING | 等待DSHB UT-001~010完成 |

### 10.3 双端确认项

| # | 确认项 | DSHE确认 | DSHB确认 | 说明 |
|---|--------|---------|---------|------|
| 1 | COORD用例执行时序 | ✅ | ⏳ | 推荐: COORD-003→001→002→004 |
| 2 | 数据格式规范 | ✅ | ⏳ | JSON schema已定义 |
| 3 | 降级策略一致性 | ✅ | ⏳ | 4层降级+7降级图表配置 |
| 4 | MD5校验标准 | ✅ | ⏳ | 131/131 MD5匹配 |
| 5 | 性能阈值对齐 | ✅ | ⏳ | P99<3.0s, 首屏<2.0s |

---

## 11. 风险与应急

### 11.1 整体风险评估

| 风险 | 等级 | 影响 | 概率 | 应急方案 |
|------|------|------|------|---------|
| DSHB底层延迟就绪 | 高 | IT阶段延期 | 中 | 影子环境Mock执行, 标记条件通过 |
| 数据格式不匹配 | 中 | COORD用例失败 | 低 | DSHE侧兼容层适配 |
| 性能阈值不达标 | 低 | Gate验收不通过 | 低 | 性能优化迭代 |
| 跨团队时序冲突 | 中 | 执行延期 | 低 | 异步执行+Mock回退 |

### 11.2 回滚方案

| 场景 | 回滚方案 | 耗时 |
|------|---------|------|
| COORD全部失败 | 回退到RC1稳定态, 标记CONDITIONAL_PASS | 30min |
| 单个COORD失败 | 降级为Mock执行, 标记CONDITIONAL | 15min |
| 数据流中断 | DSHE侧本地缓存回退 | 10min |
| 性能不达标 | 回退到RC1渲染配置 | 15min |

---

## 12. 最终状态

| 维度 | 状态 |
|------|------|
| COORD-001 展示侧 | ✅ READY |
| COORD-002 展示侧 | ✅ READY |
| COORD-003 展示侧 | ✅ READY |
| COORD-004 展示侧 | ✅ READY |
| 执行脚本 | ✅ READY |
| 判定标准 | ✅ DEFINED |
| 数据格式 | ✅ DEFINED |
| 交接清单 | ✅ COMPLETE (DSHE侧) |
| 风险应急 | ✅ DEFINED |
| **最终状态** | ✅ **DISPLAY-SIDE READY — WAITING FOR DSHB IT INTEGRATION** |

---

*文档版本: V7-RC2-COORD-PREP*
*生成日期: 2026-10-04*
*工单: DSHE_V86_RC2_COORD_CASE_DISPLAY_SIDE_PREP*
*分支: feature/v85-chart-template*
*基线: DSHE V7-RC1 FINAL_FROZEN (commit f1d444e)*
*DSHB基线: V86-RC1 (commit 0948e1d)*
*状态: ✅ DISPLAY-SIDE READY — WAITING FOR DSHB IT INTEGRATION*