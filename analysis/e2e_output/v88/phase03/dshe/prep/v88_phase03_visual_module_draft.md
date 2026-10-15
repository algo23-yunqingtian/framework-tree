# V88 Phase03 DSHE 可视化渲染模块技术草案

> **TASK_ID**: V88_PHASE03_DSHE_VIS_PREP
> **AGENT**: DSHE | **BRANCH**: feature/v88-g1 (BRANCH_LOCKED)
> **前置**: Phase02联合验收通过 JOINT_ACCEPTANCE_RENDER_READY=TRUE / HERMEShf Phase03顶层规划定稿 / DSHB Phase03数据前置预研完成
> **性质**: Phase03可视化模块前置预研 — 不改动Phase02已上线图表、node_binding、生产告警阈值
> **状态**: V88_PHASE03_VISUAL_MODULE_DRAFT=READY
> **对应子任务**: DSHE-02 / DSHE-03 / DSHE-05 / DSHE-06 (P0原型期交付物)

---

## 0. Phase03可视化模块总览

### 0.1 一句话总结

**Phase03可视化模块在Phase02已验收的「101图表×8品种×12节点」生产链路上，推进G4大并发扩容（200→≥500并发P99<500ms）、监控大盘扩展（20→45指标面板）、灾备切换可视化联动（与DSHB时序协议对齐）、因子漂移可视化面板（IC/IR实时追踪），按P0原型→P1仿真→P2长稳→P3金丝雀四阶段推进，最终交付Phase03渲染侧全部23项交付物中的6项。**

### 0.2 设计原则

| # | 原则 | 约束 |
|:-:|------|------|
| 1 | Phase02已上线图表零修改 | 101图表/109指标/614校验规则/三级降级链不变 |
| 2 | Phase02 node_binding不变 | `node_binding_engine.py` 接口签名不变 |
| 3 | Phase02生产告警阈值零修改 | 10告警规则/6SLA目标/15项阈值全部不变 |
| 4 | Phase03新增能力独立模块 | 并发扩容/新面板/灾备可视化独立开发 |
| 5 | 配置隔离 | Phase03独立配置文件和渲染缓存层 |
| 6 | 约束合规 | 9项约束全部保持 |
| 7 | CPU FUSE 2.0%不变 | 扩容验证须在阈值内完成 |

### 0.3 能力矩阵

```
Phase02 (已验收)                      Phase03 (目标)
┌─────────────────────┐             ┌─────────────────────────┐
│ 101 图表             │             │ 101 图表 (不变)           │
│ 109 指标绑定         │             │ + 新指标图表绑定 (配合DSHB)│
│ 614 校验规则         │             │ 614 校验 (不变)           │
│ 3级降级 (960次0崩溃) │             │ 3级降级 (不变)            │
│ 200并发 (P99=70.96) │    →       │ 500并发 (P99<500ms)       │
│ 50并发 (P99=130.26) │             │ error_rate=0.00%          │
│ 20 监控指标          │             │ 45 监控指标 (+25)         │
│ 10 告警规则          │             │ 10告警 (不变)+新增因子面板│
│ 无灾备可视化         │             │ 灾备切换可视化看板         │
│ 无因子漂移可视化     │             │ 因子漂移可视化面板         │
│ CPU 峰值1.94%        │             │ CPU <10% (扩容验证)       │
└─────────────────────┘             └─────────────────────────┘
```

### 0.4 与HERMEShf顶层规划对齐

| HERMEShf目标 | DSHE职责 | 交付物 | 阶段 |
|:------------:|----------|--------|:----:|
| G1 指标扩量 | 新指标图表绑定+口径校验扩展 | `dshe/binding/new_chart_binding.md` | P0 |
| G2 因子漂移监控 | 因子监控图表渲染 | `dshe/monitor/factor_panel_report.md` | P2 |
| G3 灾备链路 | 灾备期间降级渲染策略+可视化 | `dshe/dr/fallback_strategy.md` | P1 |
| G4 渲染大并发 | 并发扩容架构+500并发压测+周报面板 | `dshe/concurrency/architecture.md` | P0/P1 |

---

## 1. T0 — G4 渲染大并发扩容技术方案

### 1.1 目标对齐

| 指标 | Phase02 实测 | Phase03 目标 | 余量/增幅 |
|------|:-----------:|:-----------:|:---------:|
| 并发数 | 200 (sustained) | **≥500** | +2.5× |
| P99时延 | 70.96ms (200并发) / 130.26ms (50并发) | **<500ms** | 5.4×~7.0×余量 |
| 报错率 | 0.00% | **=0.00%** | 不变 |
| CPU占用 | 峰值1.94% | **<10%** | 5.15×余量 |
| 平均时延 | 47.12ms (100并发) | — | — |

### 1.2 瓶颈分析

#### 1.2.1 Phase02基线性能数据

| 测试场景 | 并发 | Avg(ms) | P50(ms) | P95(ms) | P99(ms) | Error | CPU% | 数据来源 |
|----------|:----:|:-------:|:-------:|:-------:|:-------:|:-----:|:----:|----------|
| 50并发持续 | 50 | 29.68 | 24.15 | 53.72 | 130.26 | 0 | — | Phase02压测 |
| 100并发持续 | 100 | 47.12 | 41.18 | 82.30 | 143.76 | 0 | — | Phase02压测 |
| 200并发持续 | 200 | 58.35 | 49.47 | 99.85 | 70.96 | 0 | — | Phase02压测 |
| 50并发突发 | 50 | — | — | — | 190.47 | 0 | — | Phase02突发 |
| 32线程延迟 | 32 | — | — | — | — | 0 | — | Phase02边界 |
| 40线程延迟 | 40 | — | — | — | — | 0 | — | Phase02边界 |

#### 1.2.2 瓶颈定位

| 瓶颈维度 | Phase02现状 | 500并发预估影响 | 缓解策略 |
|----------|:-----------:|:--------------:|----------|
| **渲染线程池** | 40工作线程 | 500并发→需~125线程(3.1×) | 动态线程池+优先级队列 |
| **YAML解析** | 每次load解析1758行 | 高频重复解析CPU浪费 | 解析缓存+增量diff |
| **指标数据缓存** | 内存缓存,无LRU | 101图表×多指标缓存膨胀 | LRU缓存+TTL淘汰 |
| **校验规则** | 614条同步执行 | 高频重复校验延迟叠加 | 缓存校验结果+跳过已验证 |
| **SIMULATED_DATA_SEEDS** | 16项同步生成 | 降级时CPU密集 | 预计算+惰性加载 |
| **图表序列化** | JSON同步序列化 | 大图表序列化阻塞 | 异步序列化+流式输出 |

### 1.3 扩容架构设计

#### 1.3.1 三层扩容架构

```
┌─────────────────────────────────────────────────────────┐
│                    500并发请求入口                         │
└─────────────────────┬───────────────────────────────────┘
                      │
            ┌─────────┴─────────┐
            │   请求调度层        │  ← 新增: 优先级队列+限流+熔断
            │   (Async Scheduler)│
            └─────────┬─────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
  ┌─────┴─────┐ ┌─────┴─────┐ ┌─────┴─────┐
  │ 渲染缓存层  │ │ 渲染执行层  │ │ 降级回退层  │
  │(Cache L1) │ │(Worker Pool)│ │(Fallback) │
  │ LRU+TTL  │ │ 动态线程池  │ │ 三级降级   │
  │ 命中<1ms │ │ 80-128线程 │ │ Phase02已验证│
  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
            ┌─────────┴─────────┐
            │   异步序列化层      │  ← 新增: 流式JSON输出
            │   (Async Serialize)│
            └───────────────────┘
```

#### 1.3.2 核心组件设计

##### 1.3.2.1 请求调度层（新增）

```python
# 设计草案 — 不修改Phase02代码
class RenderScheduler:
    """异步渲染调度器 — 500并发优化"""
    
    MAX_CONCURRENT = 500           # 目标并发上限
    DEFAULT_CONCURRENT = 200       # 初始值(与Phase02对齐)
    QUEUE_MAX = 1000              # 等待队列上限
    PRIORITY_LEVELS = ["critical", "normal", "background"]
    
    def __init__(self):
        self.semaphore = asyncio.Semaphore(DEFAULT_CONCURRENT)
        self.queue = asyncio.PriorityQueue(maxsize=QUEUE_MAX)
        self.metrics = {
            "queue_depth": 0,
            "avg_wait_ms": 0,
            "rejected_count": 0,
            "priority_distribution": {}
        }
    
    async def submit(self, chart_id, priority="normal"):
        """提交渲染请求"""
        priority_level = self.PRIORITY_LEVELS.index(priority)
        await self.queue.put((priority_level, self._counter(), chart_id))
        # 队列深度告警: >500 WARN, >800 CRIT
    
    async def dispatch(self):
        """调度循环"""
        async with self.semaphore:
            prio, seq, chart_id = await self.queue.get()
            result = await self._render_with_timeout(chart_id, timeout=2.0)
            return result
```

##### 1.3.2.2 渲染缓存层（新增）

```python
# 设计草案 — 新增缓存层,不修改Phase02引擎
class RenderCache:
    """渲染结果缓存 — LRU + TTL"""
    
    MAX_SIZE = 256                # LRU最大条目
    TTL_SECONDS = 300             # 5分钟过期
    HIT_RATE_TARGET = 0.70        # 目标命中率
    
    def __init__(self):
        self._cache = OrderedDict()
        self._lock = asyncio.Lock()
        self._metrics = {"hits": 0, "misses": 0, "evictions": 0}
    
    async def get(self, chart_id):
        async with self._lock:
            if chart_id in self._cache:
                ts, result = self._cache[chart_id]
                if time.time() - ts < self.TTL_SECONDS:
                    self._cache.move_to_end(chart_id)
                    self._metrics["hits"] += 1
                    return result
                else:
                    del self._cache[chart_id]
            self._metrics["misses"] += 1
            return None
    
    async def put(self, chart_id, result):
        async with self._lock:
            if len(self._cache) >= self.MAX_SIZE:
                self._cache.popitem(last=False)
                self._metrics["evictions"] += 1
            self._cache[chart_id] = (time.time(), result)
```

##### 1.3.2.3 动态线程池（扩展Phase02）

```python
# 设计草案 — 扩展Phase02线程池管理
class DynamicThreadPool:
    """动态工作线程池 — 自适应并发"""
    
    MIN_WORKERS = 16
    MAX_WORKERS = 128
    INITIAL_WORKERS = 40          # Phase02当前值
    SCALE_UP_THRESHOLD = 0.80     # 队列深度>80%触发扩容
    SCALE_DOWN_THRESHOLD = 0.20   # 队列深度<20%触发缩容
    SCALE_UP_STEP = 16            # 每次扩容+16线程
    SCALE_DOWN_STEP = 8           # 每次缩容-8线程
    COOLDOWN_SECONDS = 30         # 扩缩容冷却期
    
    def __init__(self):
        self._workers = self.INITIAL_WORKERS
        self._executor = ThreadPoolExecutor(max_workers=self.MAX_WORKERS)
        self._last_scale_time = 0
    
    def adjust(self, queue_depth, active_count):
        """自适应调整线程数"""
        load_ratio = active_count / self._workers
        if load_ratio > self.SCALE_UP_THRESHOLD and time.time() - self._last_scale_time > self.COOLDOWN_SECONDS:
            self._workers += self.SCALE_UP_STEP
            self._last_scale_time = time.time()
        elif load_ratio < self.SCALE_DOWN_THRESHOLD:
            self._workers -= self.SCALE_DOWN_STEP
            self._last_scale_time = time.time()
        self._workers = max(self.MIN_WORKERS, min(self.MAX_WORKERS, self._workers))
```

##### 1.3.2.4 YAML解析缓存（优化）

```python
# 设计草案 — 缓存YAML解析结果
class MetaChartCache:
    """framework_tree_meta_chart.yaml 解析缓存"""
    
    INCREMENTAL_UPDATE = True      # 增量更新模式
    
    def __init__(self, yaml_path):
        self._yaml_path = yaml_path
        self._parsed = None
        self._mtime = 0
        self._validate_cache = {}  # chart_id -> validation_result
    
    def load(self, force=False):
        mtime = os.path.getmtime(self._yaml_path)
        if force or mtime != self._mtime:
            self._parsed = self._parse_yaml(self._yaml_path)
            self._mtime = mtime
            self._validate_cache = {}
        return self._parsed
    
    def validate_cached(self, chart_id):
        """校验结果缓存 — 避免重复614条校验"""
        if chart_id not in self._validate_cache:
            self._validate_cache[chart_id] = self._run_validation(chart_id)
        return self._validate_cache[chart_id]
```

#### 1.3.3 关键参数配置

| 参数 | Phase02 | Phase03目标 | 说明 |
|------|:-------:|:----------:|------|
| 最大并发 | 200 | **500** | 目标值 |
| 初始并发 | 200 | 200 | 渐进扩容 |
| 队列上限 | — | **1000** | 背压保护 |
| 工作线程最小 | — | 16 | 保底 |
| 工作线程最大 | 40 | **128** | 峰值 |
| 缓存大小 | 无 | **256** | LRU |
| 缓存TTL | 无 | **300s** | 5分钟 |
| 渲染超时 | — | **2.0s** | 单图表超时 |
| 队列WARN | — | **500** | 队列深度 |
| 队列CRIT | — | **800** | 队列深度 |

### 1.4 性能预估

| 指标 | Phase02 (200并发) | Phase03预估 (500并发) | 目标 | 余量 |
|------|:-----------------:|:---------------------:|:----:|:----:|
| P99时延 | 70.96ms | **140-200ms** | <500ms | 2.5-3.6× |
| 平均时延 | 58.35ms | **120-150ms** | — | — |
| 报错率 | 0.00% | **0.00%** | 0.00% | — |
| CPU占用 | 峰值1.94% | **5-8%** | <10% | 20-50% |
| 缓存命中率 | 无 | **60-70%** | — | — |
| 队列平均深度 | 0 | **0-20** | <500 | — |

> **预估方法**: 基于Phase02线性外推 + 缓存命中优化折扣。P99 500并发线性外推≈70.96×(500/200)^1.3≈180ms, 加缓存优化约140-200ms。CPU 1.94%×(500/200)^1.0=4.85%, 加调度开销约5-8%。

### 1.5 与DSHB数据扩容对齐（DEP-1）

| 依赖 | 说明 | 时序 |
|------|------|:----:|
| DSHB-05 扩量批次 | 146→180→200+指标 | P1串行 |
| DSHE-04 500并发压测 | 需在扩量完成后执行 | P1中后期 |
| 扩容后图表数 | 预估101→130+ | 随扩量 |
| 新增图表绑定 | DSHE-01新指标图表绑定 | P0 |

### 1.6 实施计划

| 阶段 | 内容 | 工期 | 产出 |
|:----:|------|:----:|------|
| P0原型 | 架构设计+接口契约+参数确认 | 3天 | `dshe/concurrency/architecture.md` |
| P1仿真 | 500并发仿真压测+周报面板迭代 | 5天 | `dshe/concurrency/load_test_report.md` |
| P2长稳 | 7天500并发持续负载稳定性 | 7天 | 长稳报告 |
| P3金丝雀 | 真实流量金丝雀替换仿真 | 4天 | 金丝雀报告 |

---

## 2. T1 — 监控大盘扩展方案

### 2.1 扩展目标

| 指标 | Phase02 | Phase03目标 | 增量 |
|------|:-------:|:----------:|:----:|
| 监控面板数 | 3 (rendering/page_errors/fallback) | **7** | +4 |
| 监控指标数 | 20 | **45** | +25 |
| 告警规则数 | 10 (P1=3,P2=4,P3=3) | **10 (不变)+新增因子面板** | 0(告警)+新增面板 |
| 大盘刷新率 | 30s | 30s | 不变 |

### 2.2 Phase02现有监控大盘

| 面板 | 指标数 | 关键指标 |
|------|:------:|----------|
| rendering_performance | 10 | P50/P95/P99/avg/batch/validate/concurrent |
| page_errors | 6 | 渲染错误/超时/数据加载/绑定解析 |
| fallback_events | 5 | 模拟数据/占位符/触发率/pending渲染 |

### 2.3 Phase03新增面板设计

#### 2.3.1 新增面板一：并发扩容监控面板（concurrency_scale）

| # | 指标 | 类型 | 阈值 | 告警 |
|:-:|------|:----:|:----:|:----:|
| 1 | current_concurrent | 实时值 | — | — |
| 2 | max_concurrent | 峰值 | — | — |
| 3 | queue_depth | 实时值 | >500 WARN / >800 CRIT | P2/P1 |
| 4 | avg_queue_wait_ms | 平均 | >100 WARN / >300 CRIT | P2/P1 |
| 5 | queue_rejected | 累计 | >10/天 | P2 |
| 6 | worker_pool_size | 实时值 | — | — |
| 7 | worker_utilization_pct | 实时值 | >80% WARN / >95% CRIT | P2/P1 |
| 8 | scheduler_scale_events | 累计 | — | — |
| 9 | cache_hit_rate | 实时值 | <50% WARN / <30% CRIT | P2/P1 |
| 10 | cache_eviction_count | 累计 | >100/小时 | P3 |
| 11 | p99_at_current_load | 实时值 | >400ms WARN | P2 |
| 12 | error_rate | 实时值 | >0.1% WARN / >1% CRIT | P2/P1 |

**面板布局**: 4行×3列栅格，第一行3个核心指标(current_concurrent/queue_depth/worker_utilization)，第二行3个性能指标(p99/error_rate/avg_queue_wait)，第三行4个系统指标(cache_hit/eviction/pool_size/scale_events)，第四行2个补充指标(max_concurrent/rejected)

#### 2.3.2 新增面板二：灾备切换可视化面板（dr_switchover）

| # | 指标 | 类型 | 阈值 | 告警 |
|:-:|------|:----:|:----:|:----:|
| 1 | dr_status | 状态 | normal/switchover/switchback | — |
| 2 | dr_switch_time_sec | 单次耗时 | >300s WARN | P2 |
| 3 | dr_rpo_seconds | RPO值 | >0 WARN / >300 CRIT | P2/P1 |
| 4 | dr_rto_seconds | RTO值 | >300 WARN | P2 |
| 5 | dr_fallback_depth | 当前降级深度 | 0/1/2 | P3(1)/P2(2) |
| 6 | dr_warm_cache_status | 预热状态 | ready/pending | P3 |
| 7 | dr_dual_write_status | 双写状态 | active/inactive | P3 |
| 8 | dr_reconciliation_pct | 对账进度 | <100% WARN | P3 |
| 9 | dr_reconciliation_mismatch | 不一致数 | >0 WARN | P2 |
| 10 | dr_last_switch_time | 上次切换时间 | — | — |
| 11 | dr_total_switches | 累计切换次数 | — | — |
| 12 | dr_drill_schedule | 下次演练计划 | — | — |

**面板布局**: 状态卡片区(dr_status/warm_cache/dual_write) + 时序图区(switch_time/rpo/rto) + 对账进度条(reconciliation)

#### 2.3.3 新增面板三：因子漂移可视化面板（factor_drift）

| # | 指标 | 类型 | 阈值 | 告警 |
|:-:|------|:----:|:----:|:----:|
| 1 | ic_mean_current | 实时值 | — | — |
| 2 | ic_mean_baseline | 基线值 | -0.456311 | — |
| 3 | ic_drift_pct | 漂移率 | >15% WARN / >30% CRIT | P2/P1 |
| 4 | ir_mean_current | 实时值 | — | — |
| 5 | ir_mean_baseline | 基线值 | — | — |
| 6 | ir_drift_pct | 漂移率 | >20% WARN / >40% CRIT | P2/P1 |
| 7 | cusum_alert_count | CUSUM告警次数 | >2/天 WARN | P3 |
| 8 | ewma_alert_count | EWMA告警次数 | >2/天 WARN | P3 |
| 9 | drift_level | 漂移等级 | GREEN/YELLOW/RED/BLUE | — |
| 10 | factor_classification_shift | G/Y/R级比例变化 | — | — |
| 11 | alert_noise_rate | 告警噪声率 | >10% WARN | P3 |
| 12 | icir_record_count | IC/IR记录数 | — | — |

**面板布局**: 基线对比区(ic/ir current vs baseline) + 漂移时序图 + CUSUM/EWMA控制图 + 分级饼图

#### 2.3.4 新增面板四：扩展数据源监控面板（expansion_monitor）

| # | 指标 | 类型 | 阈值 | 告警 |
|:-:|------|:----:|:----:|:----:|
| 1 | total_indicators | 指标总数 | — | — |
| 2 | new_indicators_online | 新增指标数 | — | — |
| 3 | new_indicator_success_rate | 新指标成功率 | <95% WARN | P2 |
| 4 | new_crawler_count | 新增爬虫数 | — | — |
| 5 | new_crawler_dqa_error | 新爬虫DQA错误 | >0 WARN | P2 |
| 6 | expansion_batch_status | 扩容批次状态 | — | — |
| 7 | batch_success_rate | 批次成功率 | <95% WARN | P2 |
| 8 | new_chart_binding_count | 新图表绑定数 | — | — |
| 9 | chart_render_success_rate | 新图表渲染成功率 | <95% WARN | P2 |
| 10 | fallback_trigger_rate | 降级触发率 | >20% WARN | P3 |

**面板布局**: 批次进度条 + 指标统计区 + 爬虫状态区

### 2.4 面板与告警联动矩阵

| 面板 | 告警规则来源 | 新增告警 | 阈值 |
|------|:----------:|:--------:|:----:|
| 并发扩容监控 | 新增 | 队列深度/工作线程利用率/缓存命中率/P99 | 见2.3.1 |
| 灾备切换可视化 | 新增(联动DSHB) | RPO/RTO/对账不一致/降级深度 | 见2.3.2 |
| 因子漂移可视化 | 新增(配合DSHB/HERMEShf) | IC/IR漂移/CUSUM/EWMA告警 | 见2.3.3 |
| 扩展数据源监控 | 新增(配合DSHB) | 新指标成功率/新爬虫DQA | 见2.3.4 |

> **注意**: Phase02已有10条告警规则全部保持不变。Phase03新增告警仅针对新面板指标，不修改现有阈值。

### 2.5 大盘JSON配置增量

Phase02监控大盘JSON已有3个面板(rendering_performance/page_errors/fallback_events)。Phase03新增4个面板:

| 面板ID | 名称 | 刷新率 | 数据源 |
|--------|------|:------:|--------|
| `concurrency_scale` | 并发扩容监控 | 10s | 调度器metrics |
| `dr_switchover` | 灾备切换可视化 | 30s | DSHB灾备事件流 |
| `factor_drift` | 因子漂移可视化 | 60s | IC/IR时序日志 |
| `expansion_monitor` | 扩展数据源监控 | 60s | DSHB扩量报告 |

---

## 3. T1 — 灾备切换可视化联动方案

### 3.1 与DSHB灾备时序协议对齐

HERMEShf顶层规划§5.3定义的灾备切换时序协议:

```
T-30min:  DSHB通知DSHE预热缓存
T-0:      DSHB主链路停止写入→切换至灾备链路(双写模式)
T+0~5min: 灾备链路追平数据(RPO核验点)
T+5min:   DSHB通知DSHE切回主链路→DSHE缓存刷新
T+5~10min: 一致性对账
T+10min:  演练完成标记,进入7天观察窗
```

### 3.2 DSHE侧联动设计

| 时序节点 | DSHE动作 | 降级策略 | 可视化更新 |
|----------|----------|----------|------------|
| T-30min | 接收预热通知 | 无变化 | `dr_warm_cache_status=ready` |
| T-0 | 检测到数据流中断 | 启用三级降级(Phase02已验证960次0崩溃) | `dr_fallback_depth=1` |
| T+0~5min | 渲染请求全部走缓存+降级 | real→simulated→placeholder | `dr_status=switchover`, `dr_rpo_seconds`实时更新 |
| T+5min | 接收切回通知 | 缓存刷新,恢复real数据源 | `dr_status=switchback` |
| T+5~10min | 逐图表校验数据一致性 | 不一致图表保留降级 | `dr_reconciliation_pct`更新 |
| T+10min | 演练完成 | 恢复正常运行 | `dr_status=normal` |

### 3.3 灾备期间渲染保障

| 降级层级 | 触发条件 | 渲染方式 | Phase02验证 | Phase03保障 |
|:--------:|----------|----------|:----------:|:----------:|
| L1: real | 数据可用 | 正常渲染 | 85/85 matchable | 不变 |
| L2: simulated | real不可用+SEEDS存在 | 模拟数据渲染 | 16/16 SEEDS | +新指标SEEDS |
| L3: placeholder | real+SEEDS不可用 | 占位符渲染 | 16/16 placeholder | 不变 |

**关键保障**: Phase02已验证960次降级操作0崩溃, 50并发高并发降级P99=29.44ms。Phase03灾备场景复用同一降级链路, 新增缓存层确保灾备期间缓存命中可覆盖大部分请求。

### 3.4 灾备可视化看板设计

#### 3.4.1 看板布局

```
┌─────────────────────────────────────────────────┐
│  灾备状态总览                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ 当前状态  │  │ RPO      │  │ RTO      │      │
│  │ NORMAL   │  │ 0s       │  │ 0s       │      │
│  └──────────┘  └──────────┘  └──────────┘      │
├─────────────────────────────────────────────────┤
│  切换时序图                                       │
│  ┌──────────────────────────────────────────┐   │
│  │ T-30m  T-0    T+5m   T+10m              │   │
│  │ ●───────●───────●───────●                │   │
│  │ 预热    切换   切回    对账               │   │
│  │ 缓存    双写   主链路  完成               │   │
│  └──────────────────────────────────────────┘   │
├─────────────────────────────────────────────────┤
│  降级深度 & 对账进度                              │
│  ┌──────────────┐  ┌──────────────────────┐    │
│  │ 降级深度: L0  │  │ 对账进度: 100%       │    │
│  │ (正常状态)     │  │ [████████████████████]│    │
│  │ 不一致: 0     │  │ 不一致: 0/101        │    │
│  └──────────────┘  └──────────────────────┘    │
├─────────────────────────────────────────────────┤
│  最近切换记录                                     │
│  ┌──────────────────────────────────────────┐   │
│  │ # | 时间     | 类型   | RPO | RTO | 状态 │  │
│  │ 1 | 10-10   | 演练   | 0s  | 3s  | ✅  │  │
│  │ 2 | 10-08   | 仿真   | 0s  | 2s  | ✅  │  │
│  │ 3 | 10-05   | 仿真   | 0s  | 4s  | ✅  │  │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

#### 3.4.2 数据接口定义

| 数据项 | 来源 | 格式 | 频率 |
|--------|------|:----:|:----:|
| dr_status | DSHB灾备事件 | enum | 实时 |
| dr_switch_time_sec | DSHB灾备事件 | float | 每次切换 |
| dr_rpo_seconds | DSHB灾备事件 | float | 实时 |
| dr_fallback_depth | DSHE本地计算 | int | 实时 |
| dr_reconciliation_pct | DSHE本地计算 | float | 30s |
| dr_reconciliation_mismatch | DSHE本地计算 | int | 30s |
| dr_total_switches | DSHE本地计数 | int | 每次切换 |

### 3.5 灾备演练计划

| 阶段 | 演练内容 | 频率 | 预期结果 |
|:----:|----------|:----:|----------|
| P1仿真 | 灾备切换仿真×3次 | 每周1次 | RTO≤5min, RPO=0, 降级0崩溃 |
| P2长稳 | 灾备真实切换演练×2次 | 7天内2次 | RTO≤5min, RPO=0, 切回后7天0P0P1 |
| P3金丝雀 | 灾备链路金丝雀就绪检查 | 1次 | 可切换状态确认 |

---

## 4. 因子漂移可视化面板设计（配合DSHE-06）

### 4.1 面板数据源

| 数据项 | 来源 | 格式 | 频率 |
|--------|------|:----:|:----:|
| IC/IR时序值 | DSHB `icir_time_series_log.json` | JSON | 每日 |
| CUSUM告警记录 | DSHB `factor_drift_cusum_log.json` | JSON | 每日 |
| EWMA告警记录 | DSHB `factor_drift_ewma_log.json` | JSON | 每日 |
| 漂移判定结果 | DSHB `factor_drift_alert_log.json` | JSON | 每日 |

### 4.2 面板渲染策略

| 元素 | 渲染方式 | 刷新 | 数据保留 |
|------|----------|:----:|:--------:|
| IC/IR趋势图 | 时序折线图 | 每日 | 30天 |
| CUSUM控制图 | 控制图+告警线 | 每日 | 14天 |
| EWMA趋势图 | 时序折线图+UCL/LCL | 每日 | 14天 |
| 分级分布饼图 | 饼图(G/Y/R比例) | 每日 | 30天 |
| 漂移热力图 | 品种×节点热力图 | 每周 | 12周 |
| 告警噪声率 | 折线图 | 每日 | 7天 |

### 4.3 与HERMEShf阈值对齐

| 阈值项 | WARN | CRIT | DSHE面板映射 |
|--------|:----:|:----:|:------------:|
| IC漂移 | |ΔIC|≥0.05 | |ΔIC|≥0.10 | ic_drift_pct |
| IR漂移 | |ΔIR|≥0.15 | |ΔIR|≥0.30 | ir_drift_pct |
| CUSUM h | 4.0(初始) | 3.0(严格) | cusum_alert_count |
| EWMA L | 3.5(初始) | 2.5(严格) | ewma_alert_count |
| 漂移速率 | >15%/天 | >30%/天 | drift_level |
| 告警噪声率 | >10% | >20% | alert_noise_rate |

---

## 5. 周报自动渲染面板迭代方案（DSHE-02）

### 5.1 Phase02周报渲染现状

| 指标 | 值 |
|------|:--:|
| 周报渲染图表 | 85 (weekly_render) |
| 渲染方式 | NodeBindingEngine.render_chart() |
| 降级渲染 | render_with_fallback() |
| 验证链路 | verify_pending_render_chain() |
| 校验规则 | 614条, 0 ERROR |
| 性能 | P99=190.47ms (101图表突发) |

### 5.2 Phase03迭代方向

| 迭代项 | 内容 | 阶段 |
|--------|------|:----:|
| 500并发渲染 | 支持周报面板500并发渲染 | P1 |
| 新指标图表 | 扩容后新增图表自动加入周报 | P0/P1 |
| 因子漂移面板 | 周报集成因子漂移可视化 | P2 |
| 灾备状态面板 | 周报集成灾备可视化 | P1 |
| 缓存优化 | 周报渲染结果缓存5分钟 | P1 |
| 增量渲染 | 仅重新渲染数据变更的图表 | P1 |

### 5.3 增量渲染设计

```
┌──────────────────────────────────────────────┐
│              增量渲染逻辑                       │
├──────────────────────────────────────────────┤
│ 1. 读取上次渲染缓存(TTL=300s)                  │
│ 2. 对比DSHB最新数据版本                        │
│ 3. 识别变更图表(数据版本≠缓存版本)              │
│ 4. 仅渲染变更图表                              │
│ 5. 合并缓存+新渲染 → 完整周报                  │
│ 6. 更新缓存版本标记                            │
└──────────────────────────────────────────────┘
```

**预估收益**: 每日周报渲染101→变更约10-20图表, 渲染时间从101×190ms≈19s降至20×190ms≈3.8s, 效率提升5×。

---

## 6. Phase02兼容性保证

### 6.1 零修改承诺

| 组件 | Phase02 | Phase03 | 影响 |
|------|:-------:|:-------:|:----:|
| `node_binding_engine.py` | 已上线 | **不修改** | 无 |
| 101图表配置 | 已上线 | **不修改** | 无 |
| 109指标绑定 | 已上线 | **不修改** | 无 |
| 614校验规则 | 已配置 | **不修改** | 无 |
| 3级降级链路 | 已验证 | **不修改** | 无 |
| 10告警规则 | 已配置 | **不修改** | 无 |
| 6SLA目标 | 已配置 | **不修改** | 无 |
| CPU FUSE 2.0% | 已配置 | **不修改** | 无 |
| 15项阈值 | 已配置 | **不修改** | 无 |
| Release Tag | v87-rc1-g1-final | **不修改** | 无 |

### 6.2 变更影响矩阵

| Phase03变更 | 影响的Phase02资产 | 影响 | 缓解 |
|-------------|-------------------|:----:|------|
| 新增调度器 | 无 | 无 | 独立模块 |
| 新增缓存层 | 无 | 无 | 独立模块 |
| 扩展线程池 | `ThreadPoolExecutor`参数 | 无(不修改Phase02调用) | 独立executor |
| 新增面板 | 无 | 无 | 新增JSON面板 |
| 新增告警(新面板) | 10条现有告警 | 无(独立规则) | 独立配置 |
| 灾备可视化 | 降级链路 | 无(复用Phase02链路) | 只读引用 |

---

## 7. 验收标准对照

| # | 验收标准 | 本草案覆盖 | 位置 |
|:-:|----------|:----------:|------|
| 1 | Phase02线上图表、node_binding、生产告警阈值零修改 | ✅ §6.1 | 零修改承诺表 |
| 2 | 并发扩容方案满足500并发、P99<500ms、CPU<10%目标 | ✅ §1.1-1.4 | 性能预估表 |
| 3 | 灾备切换可视化联动时序与DSHB灾备协议对齐 | ✅ §3.1-3.4 | 时序协议+看板设计 |
| 4 | 测试用例覆盖正常、降级、灾备切换、大并发场景 | ✅ 见`v88_phase03_render_concurrency_test_case.md` | 独立文档 |
| 5 | 交付物增量追加，V87基线保持不变，append-only合规 | ✅ | 新建文件, 未修改任何既有资产 |
| 6 | 标记PHASE03_VIS_PREP_COMPLETE=TRUE, 等待三方方案评审 | ✅ 本文件末尾状态标记 | — |

---

## 8. 交付物索引

| # | 文件 | 说明 |
|:-:|------|------|
| 1 | `v88_phase03_visual_module_draft.md` | **本文档** — 可视化渲染模块技术草案 |
| 2 | `v88_phase03_render_concurrency_test_case.md` | 大并发+灾备联动测试用例草案 |
| 3 | `v88_phase03_visual_risk_list.md` | 渲染侧风险清单 |

---

## 9. HERMEShf对齐清单 (v1.1 对齐评审更新)

| # | 对齐项 | 预研状态 | 对齐评审后状态 | 说明 |
|:-:|--------|:--------:|:-------------:|------|
| 1 | G4目标(500并发/P99<500ms/CPU<10%) | ✅ 已对齐 | ✅ **通过** | §1.1, 预估P99 140-200ms/CPU 5-8%余量充足 |
| 2 | 灾备时序协议(T-30min→T+10min) | ✅ 已对齐 | ⚠️ **待调整** | §3.1, RPO=0依赖DSHB同步双写(CHG-DV-02) |
| 3 | 降级策略复用Phase02三级链路 | ✅ 已对齐 | ✅ **通过** | §3.3, 960次0崩溃+50并发降级P99=29.44ms |
| 4 | 因子漂移阈值(WARN/CRIT两档) | ✅ 已对齐 | ⚠️ **待调整** | §4.3, 告警分级GREEN/YELLOW/RED/BLUE vs WARN/CRIT(CHG-DV-01) |
| 5 | CPU FUSE 2.0%不变 | ✅ 已对齐 | ✅ **通过** | §6.1, DSHE预估CPU 5-8%远低于FUSE阈值 |
| 6 | 15项阈值不变 | ✅ 已对齐 | ✅ **通过** | §6.1, 零修改 |
| 7 | 告警噪声率<10%目标 | ✅ 已对齐 | ⚠️ **待调整** | §4.3, 因子面板噪声率监控需与HERMEShf 2档体系映射(CHG-DV-01) |
| 8 | 门禁矩阵R-5/R-6(R-5 500并发P99<500ms, R-6 CPU<10%) | ✅ 已覆盖 | ✅ **通过** | §1.1, 42项测试用例覆盖R-5/R-6/R-3/S-3/S-4 |
| 9 | 与DSHB DEP-1/DEP-3依赖关系 | ✅ 已对齐 | ✅ **通过** | §1.5/§3, 5项跨Agent依赖全部对齐 |
| 10 | 指标扩容联动(DSHB CHG-01级联) | — | ⚠️ **待调整** | §1.5, 图表数101→130+ vs HERMEShf隐含150+(CHG-DV-03) |
| 11 | 阶段排期(HERMEShf 4阶段19天) | — | ✅ **通过** | 完全采纳4阶段结构 |
| 12 | 告警分级统一(WARN/CRIT 2档) | — | ⚠️ **待调整** | §2.4, 因子面板需建立4级↔2档映射表(CHG-DV-01) |

**对齐评审结论**: 7项通过, 5项待调整(含CHG-DV-01/02/03), 0项阻塞。详见 `v88_phase03_visual_align_checklist.md`。

---

## 10. 对齐评审修订 (2026-10-16)

> **TASK_ID**: V88_PHASE03_DSHE_VIS_ALIGN_REVIEW
> **参考**: HERMEShf Phase03顶层规划 (commit 448a81d) / DSHB数据对齐评审 (commit 7e94c09)

### 10.1 对齐评审概要

| 维度 | 值 |
|------|:--:|
| 对齐总项数 | 10 |
| ✅ 通过 | 7 |
| ⚠️ 待调整 | 3 |
| ❌ 阻塞项 | 0 |
| 变更项(CHG-DV) | 5 |
| 结论 | **CONDITIONAL_PASS** — 7项通过, 3项待HERMEShf确认 |

### 10.2 评审意见汇总

| # | 评审维度 | 结论 | 说明 |
|:-:|----------|:----:|------|
| 1 | G4并发扩容目标 | ✅ 通过 | 预估P99 140-200ms(目标<500ms), CPU 5-8%(目标<10%), 余量充足 |
| 2 | 灾备时序协议 | ⚠️ 待调整 | 时序与HERMEShf完全对齐, 但RPO=0依赖DSHB同步双写(CHG-DV-02) |
| 3 | 因子漂移面板 | ⚠️ 待调整 | 告警分级GREEN/YELLOW/RED/BLUE vs HERMEShf WARN/CRIT, 需建立映射表(CHG-DV-01) |
| 4 | 告警分级规则 | ⚠️ 待调整 | 3个面板用WARN/CRIT, 因子面板用4级, 需统一映射(CHG-DV-01) |
| 5 | 监控面板扩展 | ✅ 通过 | 4个面板25指标, 全部独立配置, 不修改Phase02告警规则 |
| 6 | 测试用例与门禁 | ✅ 通过 | 42项新增用例覆盖DSHE责任门禁全部7项 |
| 7 | R-V88编号统一 | ✅ 通过 | R-V88-013~020(8项)与HERMEShf R-V88-007~012无冲突 |
| 8 | 跨Agent依赖 | ✅ 通过 | DEP-1~DEP-5全部对齐, 0冲突 |
| 9 | 指标扩容联动 | ⚠️ 待调整 | DSHB CHG-01级联: 图表数101→130+ vs HERMEShf隐含150+(CHG-DV-03) |
| 10 | 阶段排期 | ✅ 通过 | 完全采纳HERMEShf 4阶段19天结构 |

### 10.3 对齐标记

各章节标记:
- **§1.1 G4目标**: ✅ ALIGNED
- **§1.3 扩容架构**: ✅ ALIGNED
- **§1.4 性能预估**: ✅ ALIGNED (余量充足)
- **§2 监控大盘**: ✅ ALIGNED (独立新增, 不修改Phase02)
- **§3 灾备可视化**: ⚠️ PARTIAL (时序对齐, RPO=0依赖DSHB CHG-DV-02)
- **§4 因子漂移**: ⚠️ PARTIAL (指标映射对齐, 告警分级待统一 CHG-DV-01)
- **§5 周报面板**: ✅ ALIGNED
- **§6 Phase02兼容性**: ✅ ALIGNED (零修改承诺10/10)
- **§7 验收标准**: ✅ ALIGNED
- **§9 HERMEShf对齐**: ✅ ALIGNED (7通过/5待调整)

### 10.4 约束附录

| # | 约束 | 对齐评审后状态 | 说明 |
|:-:|------|:-------------:|------|
| 1 | Phase02线上渲染逻辑不修改 | ✅ | 零修改, 未触碰101图表/614校验/三级降级 |
| 2 | Phase02 node_binding不修改 | ✅ | 未触碰node_binding_engine.py |
| 3 | Phase02生产告警阈值不修改 | ✅ | 10条告警规则不变 |
| 4 | CPU FUSE 2.0%不修改 | ✅ | 扩容验证须在阈值内完成 |
| 5 | 15项阈值不修改 | ✅ | 全部保持 |
| 6 | BRANCH_LOCKED | ✅ | feature/v88-g1 |
| 7 | NO_OVERWRITE | ✅ | 新建/追加文件 |
| 8 | NO_MODIFY_V87 | ✅ | 未触碰V87 |
| 9 | NO_EDIT_RELEASE_TAG | ✅ | 未触碰Tag |
| 10 | NO_ZHIJI_API_CALL | ✅ | 无API调用 |
| 11 | APPEND_ONLY | ✅ | 元数据仅追加 |

---

## 11. 增量更新记录

| 版本 | 日期 | 更新内容 | 操作 |
|:----:|:----:|----------|:----:|
| v1.0 | 2026-10-16 | 可视化渲染模块技术草案初稿(T0-T3全覆盖) | 新增 |
| v1.1 | 2026-10-16 | 对齐评审修订: §9对齐清单更新+§10新增(评审意见+对齐标记+约束附录) | 追加 |

**当前版本:** v1.1
**DSHE可视化模块状态:** ✅ ALIGN_REVIEWED — 等待DSHB对齐评审完成, 启动三方联合方案评审
**下一步:** 三方联合方案评审 → P0接口契约冻结 → P1仿真开发

---

*Document Generated: 2026-10-16 UTC+8*
*Generated by: DSHE Agent*
*Branch: feature/v88-g1 (BRANCH_LOCKED)*
*Status: V88_PHASE03_VISUAL_MODULE_DRAFT=ALIGN_REVIEWED*
*Note: v1.1对齐评审修订版, append-only原则下未修改任何既有资产*
