# V88 Phase03-P0 图表绑定验证测试用例

> **TASK_ID**: V88_PHASE03_P0_R1_CHART_META_BINDING / T4
> **AGENT**: DSHE | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **前置**: T1告警映射表 / T2渲染引擎 / T3图表元配置 完成
> **性质**: P0原型验证 — 不改动Phase02已上线图表渲染逻辑
> **状态**: V88_PHASE03_P0_BINDING_TEST_CASES=READY

---

## 0. 验证范围

| 维度 | 值 |
|------|:--:|
| 测试用例总数 | 28 |
| P0必须通过 | 28 |
| P0可选 | 0 |
| 验证环境 | P0原型 (feature/v88-g1) |
| 数据源 | api_cache.db (3 rows) + SIMULATED_DATA_SEEDS |

---

## 1. 数据源区分验证 (TC-DS-01~06)

### TC-DS-01: source="real" 正常渲染

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 api_cache.db 有数据时, source="real" 正常返回 |
| **前置条件** | api_cache.db 存在且含至少1条记录 (AO:wr50) |
| **测试步骤** | 1. 构造 chart.indicators[0].indicator_id="AO_WR50" 2. 构造 mapping_table={"AO_WR50": "wr50"} 3. 调用 render_chart_p0() |
| **预期结果** | source="real", mapping_applied=True, render_data 含 points 数据 |
| **验证指标** | render_data[0].points 长度 > 0 |
| **预期时延** | <50ms (api_cache查询) |
| **Phase02兼容** | ✅ 不修改 _load_real_data() 原始逻辑 |

### TC-DS-02: source="real" 映射表为空

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证映射表为空时, fallback 到 simulated |
| **前置条件** | mapping_table = {} (DSHB未交付) |
| **测试步骤** | 1. 构造 chart.indicators[0].indicator_id="CU_PRICE_MAIN" 2. 调用 render_chart_p0() |
| **预期结果** | source="simulated", mapping_applied=False, render_data 含模拟数据 |
| **验证指标** | mapping_miss += 1, simulated_source += 1 |
| **Phase02兼容** | ✅ 与 Phase02 _load_real_data() 行为一致 (无数据时 fallback) |

### TC-DS-03: source="real" api_cache无此指标

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 api_cache 存在但无此指标时, fallback 到 simulated |
| **前置条件** | mapping_table={"CU_PRICE_MAIN": "cu_price_main"}, api_cache 无 cu_price_main |
| **测试步骤** | 1. 构造映射 2. 调用 render_chart_p0() |
| **预期结果** | source="simulated", mapping_applied=False |
| **验证指标** | simulated_source += 1 |

### TC-DS-04: source="simulated" 正常渲染

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证模拟数据渲染一致性 |
| **前置条件** | 无 api_cache 数据 |
| **测试步骤** | 1. 调用 render_chart_p0("cu_p1_ts_01") 2. 再次调用 (相同参数) |
| **预期结果** | source="simulated", 两次渲染结果 points 完全一致 (确定性种子) |
| **验证指标** | render_data 完全匹配, cache_hit=True (第二次) |

### TC-DS-05: source="placeholder" 渲染

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 pending_data 图表占位符渲染 |
| **前置条件** | chart.data_status="pending_data", use_simulated=False |
| **测试步骤** | 1. 调用 render_chart_p0("pending_chart_id", use_simulated=False) |
| **预期结果** | source="placeholder", render_data[0].placeholder=True, points=[] |
| **验证指标** | placeholder_source += 1 |

### TC-DS-06: pending_data + use_simulated=True

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 pending_data 图表模拟数据渲染 |
| **前置条件** | chart.data_status="pending_data", use_simulated=True |
| **测试步骤** | 1. 调用 render_chart_p0("pending_chart_id", use_simulated=True) |
| **预期结果** | source="simulated", render_data 含模拟数据 |

---

## 2. 降级链路验证 (TC-FB-01~05)

### TC-FB-01: 三级降级完整性

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 real→simulated→placeholder 三级降级链完整 |
| **测试步骤** | 1. 模拟api_cache有数据 → source="real" 2. 模拟api_cache无数据 → source="simulated" 3. pending_data → source="placeholder" |
| **预期结果** | 三级降级全部正常, 0 崩溃 |
| **Phase02兼容** | ✅ 降级链逻辑不变 |

### TC-FB-02: 降级时延对比

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证三级降级各自时延基线 |
| **测试步骤** | 分别渲染 real/simulated/placeholder, 记录 latency_ms |
| **预期结果** | real: <50ms, simulated: <10ms, placeholder: <5ms |

### TC-FB-03: 缓存命中降级恢复

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证缓存失效后, 重新从api_cache加载 |
| **测试步骤** | 1. 渲染图表 (cache_miss, 写入缓存) 2. 再次渲染 (cache_hit) 3. 手动 invalidate 缓存 4. 再次渲染 (cache_miss, 重新加载) |
| **预期结果** | 步骤2 cache_hit=True, 步骤4 cache_hit=False 但数据正确 |

### TC-FB-04: 映射表缺失降级

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 DSHB 映射表未交付时, 全量 fallback simulated |
| **测试步骤** | 1. mapping_table={} 2. 批量渲染 130 图表 |
| **预期结果** | 全部 source="simulated", 0 崩溃, 0 错误 |
| **验证指标** | simulated_source=130, real_source=0 |

### TC-FB-05: api_cache.db 不存在降级

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 api_cache.db 不存在时, 全量 fallback simulated |
| **测试步骤** | 1. 删除/重命名 api_cache.db 2. 批量渲染 |
| **预期结果** | 全部 source="simulated", 0 崩溃 |

---

## 3. 渲染时延验证 (TC-PF-01~05)

### TC-PF-01: 单图表渲染时延

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证单图表渲染时延基线 |
| **测试步骤** | 渲染 10 张不同图表, 记录 latency_ms |
| **预期结果** | avg < 20ms, P99 < 100ms |
| **门禁对齐** | R-5 (P99<500ms) — 余量充足 |

### TC-PF-02: 批量渲染时延

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 130 图表批量渲染总时延 |
| **测试步骤** | 调用 render_all_p0(), 记录总时延 |
| **预期结果** | 总时延 < 10s (130图表×avg<20ms + 缓存) |

### TC-PF-03: 缓存命中时延对比

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证缓存命中后时延降低 |
| **测试步骤** | 1. 首次渲染 (cache_miss) 2. 第二次渲染 (cache_hit) |
| **预期结果** | cache_hit 时延 < cache_miss 时延 × 0.1 (降低90%) |

### TC-PF-04: 并发渲染时延 (20并发)

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 20 并发渲染时延 |
| **测试步骤** | 使用 ThreadPoolExecutor(20) 并发渲染 20 张图表 |
| **预期结果** | P99 < 100ms, error_rate = 0.00% |

### TC-PF-05: 并发渲染时延 (50并发)

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 50 并发渲染时延 |
| **测试步骤** | 使用 ThreadPoolExecutor(50) 并发渲染 50 张图表 |
| **预期结果** | P99 < 200ms, error_rate = 0.00% |

---

## 4. 缓存命中率验证 (TC-CH-01~04)

### TC-CH-01: 缓存命中率基线

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证缓存命中率达到60-70%目标 |
| **测试步骤** | 1. 批量渲染 130 图表 (第一轮, cache_miss) 2. 再次批量渲染 (第二轮, cache_hit) 3. 计算命中率 |
| **预期结果** | 第二轮命中率 ≥ 85% (TTL内全部命中) |
| **门禁对齐** | CHG-DV-05 CPU FUSE联合缓解 |

### TC-CH-02: 缓存TTL过期验证

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 TTL=300s 过期后缓存失效 |
| **测试步骤** | 1. 渲染图表 (写入缓存) 2. 等待 TTL+1s 3. 再次渲染 (应 cache_miss) |
| **预期结果** | TTL过期后 cache_miss=True, 重新加载数据 |
| **验证指标** | 缓存大小不变 (旧条目被过期淘汰) |

### TC-CH-03: LRU淘汰验证

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 LRU 最大256条, 超出时淘汰最旧 |
| **测试步骤** | 1. 渲染 260 张不同图表 (模拟) 2. 检查缓存大小 3. 检查被淘汰的是最早渲染的 |
| **预期结果** | cache.size=256, 最早的4条被淘汰 |
| **验证指标** | evictions=4 |

### TC-CH-04: 缓存手动失效

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 cache.invalidate() 手动失效 |
| **测试步骤** | 1. 渲染图表 (写入缓存) 2. invalidate(chart_id) 3. 再次渲染 (cache_miss) |
| **预期结果** | 步骤3 cache_miss=True |

---

## 5. 图表元数据验证 (TC-MT-01~06)

### TC-MT-01: YAML格式校验

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 chart_meta_config.yaml 格式正确 |
| **测试步骤** | 1. 使用 yaml.safe_load() 解析 2. 验证所有必需字段存在 |
| **预期结果** | 解析成功, 0 错误 |
| **验证字段** | chart_id/tree_node_id/commodity/chart_type/title/indicators/data_status |

### TC-MT-02: 图表数量验证

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 130+ 图表配置完整 |
| **测试步骤** | 统计 charts[] 长度 |
| **预期结果** | len(charts) ≥ 130 |

### TC-MT-03: 指标映射字段验证

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证每个指标包含 mapping_real_indicator + real_data_status |
| **测试步骤** | 遍历 charts[].indicators[], 检查字段存在 |
| **预期结果** | 所有指标包含映射字段, real_data_status="pending_mapping" |

### TC-MT-04: 降级优先级验证

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 fallback_priority 字段存在且有效 |
| **测试步骤** | 遍历 indicators[], 检查 fallback_priority ∈ {1,2,3} |
| **预期结果** | 所有 matchable 指标 fallback_priority=1 |

### TC-MT-05: Phase02基线兼容验证

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 Phase02 101 图表配置未被修改 |
| **测试步骤** | 1. 加载 Phase02 YAML 2. 加载 Phase03-P0 YAML 3. 对比 101 张基线图表的 data_status/indicator_id |
| **预期结果** | 101 张基线图表配置完全一致 |

### TC-MT-06: 新增图表标记验证

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证新增图表包含 phase03_new=true 标记 |
| **测试步骤** | 遍历 charts[], 筛选 phase03_new=true |
| **预期结果** | 29 张新增图表, 0 张基线图表被标记 |

---

## 6. 告警映射验证 (TC-AL-01~04)

### TC-AL-01: 告警等级映射完整性

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 GREEN/YELLOW/RED/BLUE ↔ WARN/CRIT 双向映射完整 |
| **测试步骤** | 加载 alert_level_mapping.md, 验证 4×2=8 条映射全部存在 |
| **预期结果** | 8/8 映射完整 |

### TC-AL-02: 告警规则配置验证

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 4 面板 25 项告警规则配置完整 |
| **测试步骤** | 加载告警规则配置, 统计规则数 |
| **预期结果** | 因子漂移4项+并发8项+灾备7项+扩量6项=25项 |

### TC-AL-03: 告警消息格式验证

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证统一告警消息格式 JSON Schema 正确 |
| **测试步骤** | 构造告警消息, 验证所有必填字段存在 |
| **预期结果** | 15/15 字段存在 |

### TC-AL-04: 噪声率监控验证

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证噪声率管控方案指标定义完整 |
| **测试步骤** | 加载噪声率指标定义 |
| **预期结果** | 4项指标定义完整, 目标值<10% |

---

## 7. 约束合规验证 (TC-CC-01~03)

### TC-CC-01: Phase02零修改验证

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 Phase02 资产零修改 |
| **测试步骤** | 1. 检查 node_binding_engine.py MD5 不变 2. 检查 framework_tree_meta_chart.yaml MD5 不变 3. 检查 api_cache.db 未被修改 |
| **预期结果** | 0 修改 |

### TC-CC-02: V87基线不变验证

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 V87 基线未被修改 |
| **测试步骤** | 检查 v87-rc1-g1-final tag 对应文件未变 |
| **预期结果** | 0 修改 |

### TC-CC-03: CPU FUSE 不变验证

| 字段 | 值 |
|------|-----|
| **测试目的** | 验证 CPU FUSE 2.0% 阈值不变 |
| **测试步骤** | 检查所有配置文件中 CPU FUSE 相关值 |
| **预期结果** | CPU FUSE = 2.0%, 未修改 |

---

## 8. 验证结果汇总

| 分类 | 用例数 | 必须通过 | 预期通过 |
|------|:------:|:--------:|:--------:|
| 数据源区分 | 6 | 6 | 6 |
| 降级链路 | 5 | 5 | 5 |
| 渲染时延 | 5 | 5 | 5 |
| 缓存命中率 | 4 | 4 | 4 |
| 图表元数据 | 6 | 6 | 6 |
| 告警映射 | 4 | 4 | 4 |
| 约束合规 | 3 | 3 | 3 |
| **总计** | **28** | **28** | **28** |

---

## 9. 验证执行记录

> **执行时间**: P0 D1-D2 (等待 DSHB 映射表交付后执行全量验证)
> **当前状态**: 模板就绪, 待 DSHB 命名映射表交付后执行全量验证

| 字段 | 值 |
|------|-----|
| 验证版本 | v88-p0.0.1 |
| 执行环境 | P0 原型 (feature/v88-g1) |
| 执行状态 | PENDING_DSHB_DELIVERY |
| 映射表状态 | PENDING_DSHB_DELIVERY |
| api_cache状态 | 3 rows (AO:wr50/wr52/wr56), 0交集 |
| 预期全量验证 | DSHB P0-R0 映射表交付后 |
| 部分验证可用 | TC-FB-04/05 (降级验证), TC-PF-01/02 (时延), TC-CH-01~04 (缓存) |
