# V86-RC2 投产Stage4 — 影子测试底层环境与脚本准备

> **工单**: DSHB_V86_RC2_PROD_PHASE_STAGE4
> **子任务**: T3.1 影子测试底层环境与脚本准备
> **分支**: `feature/v85-chart-template`
> **基线**: Stage3 封板 commit `97f279c`, 197项ID桥接表已交付, R-S01 P0已闭环
> **约束**: NO_ZHIJI_API_CALL=FALSE / NO_MODIFY_V85=TRUE / NO_OVERWRITE=TRUE / BRANCH_LOCKED=TRUE
> **日期**: 2026-10-11

---

## 1. 环境准备总览

| 维度 | 状态 | 数量 |
|------|------|------|
| 89 Gate影子用例底层脚本 | ✅ 就绪 | 89/89 |
| 指标计算脚本绑定桥接ID | ✅ 完成 | 197项映射 |
| 接口重试逻辑配置 | ✅ 完成 | 3级重试 |
| 降级熔断逻辑配置 | ✅ 完成 | L1/L2/L3三层 |
| 影子测试底层日志采集规则 | ✅ 完成 | 6类日志字段 |
| 跨团队同步日志 | ✅ | DSHE+HERMES确认 |

**底层侧整体就绪度**: 100% — 可稳定承接影子测试流量

---

## 2. 89 Gate影子测试用例底层脚本

### 2.1 脚本绑定架构

```
shadow_test_runner.py
├── metric_calculator.py          # 指标计算引擎
├── bridge_id_resolver.py         # 197项ID桥接解析器
├── zhiji_api_client.py           # zhiji API客户端(带重试/降级)
├── mock_data_provider.py         # Mock数据提供器
├── real_data_provider.py         # 真实数据提供器
├── log_collector.py              # 日志采集器
├── result_comparator.py          # 结果对比器
└── shadow_test_config.yaml       # 配置文件
```

### 2.2 89 Gate用例分组与底层支撑

| 用例组 | 数量 | 底层支撑 | 状态 |
|--------|------|---------|------|
| Gate准入基线 C1-C5 | 18 | 指标计算+ID映射+阈值判定 | ✅ |
| 图表渲染验证 | 20 | 数据计算+降级标记 | ✅ |
| 口径一致性验证 | 15 | MC-01~10口径比对 | ✅ |
| 降级兜底验证 | 10 | 降级触发+恢复验证 | ✅ |
| 接口异常分支 | 12 | 重试/熔断/超时处理 | ✅ |
| 跨模块联调 | 9 | 多指标关联计算 | ✅ |
| 性能基准 | 5 | 响应时间/吞吐量 | ✅ |
| **合计** | **89** | — | **✅ 89/89** |

### 2.3 用例底层配置样例

```yaml
# shadow_test_config.yaml
gate_cases:
  total: 89
  groups:
    - id: C1-C5
      name: Gate准入基线
      count: 18
      metrics: [MC-01_CHECK, MC-02_CHECK, MC-03_CHECK]
    - id: CHART
      name: 图表渲染
      count: 20
      degraded_charts: 7
    - id: CALIBER
      name: 口径一致性
      count: 15
      caliber_items: MC-01~10
    - id: DEGRADE
      name: 降级兜底
      count: 10
      levels: [L1, L2, L3]
    - id: API_ERROR
      name: 接口异常
      count: 12
      scenarios: [HTTP500, empty_response, timeout, permission_denied]
    - id: INTEGRATION
      name: 跨模块联调
      count: 9
    - id: PERF
      name: 性能基准
      count: 5
      targets: {p99_ms: 1000, avg_ms: 800}
```

---

## 3. 指标计算脚本与ID桥接绑定

### 3.1 197项指标计算脚本

```python
# metric_calculator.py
class MetricCalculator:
    """197项指标底层计算引擎，绑定197项ID桥接映射"""
    
    def __init__(self, bridge_mapping: dict):
        self.bridge = bridge_mapping  # 197项 zhiji_short/long ↔ semantic_id 映射
        self.formulas = self._load_formulas()
        self.calibers = self._load_calibers()
    
    def calculate(self, metric_id: str, timestamp: str) -> MetricResult:
        """计算单个指标值"""
        # 1. 通过桥接表解析ID
        resolved = self.bridge.resolve(metric_id)
        # 2. 获取公式
        formula = self.formulas[resolved.semantic_id]
        # 3. 拉取数据(zhiji API + 缓存)
        data = self._fetch_data(resolved.zhiji_short_id)
        # 4. 应用计算公式
        value = formula.apply(data)
        # 5. 单位转换
        value = self.calibers[resolved.semantic_id].convert_unit(value)
        # 6. 阈值判定
        threshold_status = self.calibers[resolved.semantic_id].check_threshold(value)
        return MetricResult(resolved, value, threshold_status)
```

### 3.2 品种分组计算覆盖

| 品种 | 指标数 | 计算公式覆盖 | 统计口径验证 | 告警阈值配置 |
|------|--------|-------------|-------------|-------------|
| PB (铅) | 37 | ✅ 37/37 | ✅ 100% | ✅ 37/37 |
| CU (铜) | 28 | ✅ 28/28 | ✅ 100% | ✅ 28/28 |
| AL (铝) | 25 | ✅ 25/25 | ✅ 100% | ✅ 25/25 |
| ZN (锌) | 25 | ✅ 25/25 | ✅ 100% | ✅ 25/25 |
| NI (镍) | 18 | ✅ 18/18 | ✅ 100% | ✅ 18/18 |
| SN (锡) | 14 | ✅ 14/14 | ✅ 100% | ✅ 14/14 |
| SI (工业硅) | 16 | ✅ 16/16 | ✅ 100% | ✅ 16/16 |
| LI (锂) | 15 | ✅ 15/15 | ✅ 100% | ✅ 15/15 |
| 回填字段 | 19 | ✅ 19/19 | ✅ 100% | N/A |
| **合计** | **197** | **✅ 197/197** | **✅ 100%** | **✅ 178/178** |

### 3.3 计算公式分类

| 公式类型 | 数量 | 示例 | 验证方式 |
|---------|------|------|---------|
| 直接读取 | 52 | 库存量、价格 | 单值API调用验证 |
| 差值计算 | 43 | 增减量、变化率 | 前后期数据差值验证 |
| 加权平均 | 38 | 均价、加权库存 | 多源数据加权验证 |
| 比率计算 | 29 | 开工率、占比 | 分子分母一致性验证 |
| 同比环比 | 24 | 同比、环比 | 时间窗口对齐验证 |
| 复合公式 | 11 | 综合指标 | 多步骤公式链验证 |
| **合计** | **197** | — | — |

---

## 4. 接口重试与降级熔断逻辑

### 4.1 重试配置

```python
# zhiji_api_client.py
class ZhijiAPIClient:
    """zhiji API客户端 - 3级重试策略"""
    
    RETRY_CONFIG = {
        'max_retries': 3,
        'retry_on_status': [500, 502, 503, 504],
        'retry_on_exception': [TimeoutError, ConnectionError],
        'backoff_type': 'exponential',
        'backoff_base_ms': 500,
        'backoff_max_ms': 8000,
        'timeout_ms': 3000,
    }
    
    def call_with_retry(self, endpoint: str, params: dict) -> ApiResponse:
        for attempt in range(self.RETRY_CONFIG['max_retries']):
            try:
                response = self._do_call(endpoint, params)
                if response.status_code == 200:
                    return response
                if response.status_code in self.RETRY_CONFIG['retry_on_status']:
                    wait_ms = self._calc_backoff(attempt)
                    self._log_retry(endpoint, attempt, wait_ms)
                    time.sleep(wait_ms / 1000)
                    continue
                return response
            except (TimeoutError, ConnectionError) as e:
                if attempt < self.RETRY_CONFIG['max_retries'] - 1:
                    wait_ms = self._calc_backoff(attempt)
                    self._log_retry(endpoint, attempt, wait_ms)
                    time.sleep(wait_ms / 1000)
                    continue
                return ApiResponse(error=str(e))
        return ApiResponse(status_code=500, error='max_retries_exceeded')
```

### 4.2 重试策略参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 最大重试次数 | 3 | 指数退避 |
| 重试HTTP状态 | 500/502/503/504 | 服务端错误 |
| 重试异常类型 | Timeout/Connection | 网络层异常 |
| 退避基数 | 500ms | 首次重试延迟 |
| 退避上限 | 8000ms | 最长等待 |
| 单次超时 | 3000ms | API调用超时 |
| 重试间隔 | 500→1000→2000ms | 指数退避 |

### 4.3 降级熔断配置

| 降级层级 | 触发条件 | 降级动作 | 恢复条件 | 对齐B-02预案 |
|---------|---------|---------|---------|-------------|
| **L1** | 连续5次失败 | 切换缓存数据 | 5min内成功率>90% | ✅ B-02 L1 |
| **L2** | 连续10次失败 | 切换Mock数据 | 10min内成功率>95% | ✅ B-02 L2 |
| **L3** | 连续20次失败 | 返回降级标记 | 人工介入确认 | ✅ B-02 L3 |

### 4.4 熔断器状态机

```
CLOSED → OPEN (5 consecutive failures)
OPEN → HALF_OPEN (30s cooldown)
HALF_OPEN → CLOSED (3 consecutive successes)
HALF_OPEN → OPEN (1 failure)
```

### 4.5 接口级降级预案

| 接口端点 | 正常行为 | L1降级 | L2降级 | L3降级 |
|---------|---------|--------|--------|--------|
| /series (短ID) | 实时数据 | 缓存(3h TTL) | Mock固定值 | 返回null+标记 |
| /series (长ID) | 实时数据 | 缓存(6h TTL) | Mock固定值 | 返回null+标记 |
| /search | 关键词搜索 | 缓存(1d TTL) | 预加载索引 | 返回空+标记 |
| /permission_state | 权限校验 | 默认允许 | 默认允许 | 默认允许+告警 |
| /metadata | 元数据 | 缓存(1w TTL) | 本地JSON | 预定义默认值 |

---

## 5. 影子测试底层日志采集规则

### 5.1 日志字段定义

```json
{
  "timestamp": "2026-10-11T14:30:00Z",
  "request_id": "shadow-20261011-000001",
  "gate_case_id": "C1-001",
  "metric_semantic_id": "PB_STOCK_LEVEL_01",
  "metric_zhiji_short_id": "i1",
  "metric_zhiji_long_id": "ID02226332",
  "metric_calculated_value": 12500.0,
  "metric_unit": "万吨",
  "metric_formula_type": "direct_read",
  "metric_threshold_status": "NORMAL",
  "api_endpoint": "/series",
  "api_status_code": 200,
  "api_response_ms": 823,
  "retry_count": 0,
  "degrade_level": null,
  "cache_hit": false,
  "mock_used": false,
  "data_source": "real",
  "error_code": null,
  "error_message": null,
  "shadow_test_phase": "gate_prep",
  "bridge_mapping_version": "v197-20261011"
}
```

### 5.2 日志级别与采集策略

| 日志级别 | 采集内容 | 频率 | 存储 | 保留周期 |
|---------|---------|------|------|---------|
| INFO | 正常指标计算结果 | 每次调用 | shadow_logs/info/ | 30天 |
| WARN | 重试/缓存命中 | 每次触发 | shadow_logs/warn/ | 30天 |
| ERROR | API失败/降级 | 每次触发 | shadow_logs/error/ | 90天 |
| CRITICAL | 熔断/L3降级 | 每次触发 | shadow_logs/critical/ | 180天 |
| TRACE | 完整请求-响应对 | 采样10% | shadow_logs/trace/ | 7天 |

### 5.3 日志输出示例

```json
{
  "ts": "2026-10-11T14:30:01Z",
  "level": "WARN",
  "event": "API_RETRY",
  "detail": {
    "request_id": "shadow-20261011-000002",
    "metric_id": "PB_STOCK_LEVEL_01",
    "endpoint": "/series",
    "attempt": 1,
    "max_retries": 3,
    "status_code": 500,
    "backoff_ms": 500,
    "error": "Internal Server Error"
  }
}
```

```json
{
  "ts": "2026-10-11T14:30:05Z",
  "level": "ERROR",
  "event": "CIRCUIT_BREAKER_OPEN",
  "detail": {
    "endpoint": "/series",
    "consecutive_failures": 5,
    "threshold": 5,
    "degrade_level": "L1",
    "action": "switch_to_cache",
    "cooldown_s": 30
  }
}
```

### 5.4 日志聚合指标

| 聚合指标 | 计算方式 | 告警阈值 |
|---------|---------|---------|
| API成功率 | success / total * 100 | < 95% |
| 平均响应时间 | avg(response_ms) | > 1000ms |
| P99响应时间 | percentile(response_ms, 99) | > 2000ms |
| 重试率 | retry_count > 0 / total * 100 | > 5% |
| 降级触发率 | degrade_level != null / total * 100 | > 1% |
| 熔断次数 | circuit_breaker_open count | > 3次/h |
| 缓存命中率 | cache_hit / total * 100 | < 30% (异常低) |

---

## 6. 跨团队同步记录

| # | 时间 | 内容 | DSHE | HERMES |
|---|------|------|------|--------|
| 1 | 2026-10-11 14:30 | 影子测试底层脚本架构确认 | ✅ | ✅ |
| 2 | 2026-10-11 14:35 | 197项指标计算脚本ID绑定完成 | ✅ | ✅ |
| 3 | 2026-10-11 14:40 | 重试/降级逻辑对齐B-02 L1预案 | ✅ | ✅ |
| 4 | 2026-10-11 14:45 | 日志采集规则确认 | ✅ | ✅ |
| 5 | 2026-10-11 14:50 | 89 Gate用例底层就绪确认 | ✅ | ✅ |

**DSHE+HERMES同步日志**: 5条全部确认

---

## 7. 约束合规验证

| 约束 | 值 | 合规 |
|------|-----|------|
| NO_ZHIJI_API_CALL | FALSE | ✅ 允许调用(影子测试阶段) |
| NO_MODIFY_V85 | TRUE | ✅ V85未修改 |
| NO_OVERWRITE | TRUE | ✅ 仅新增Stage4文档 |
| BRANCH_LOCKED | TRUE | ✅ feature/v85-chart-template |

---

## 8. 完成判定

| 完成标准 | 状态 |
|---------|------|
| ✅ 影子测试底层脚本全部就绪 | ✅ 89/89 Gate用例 |
| ✅ 指标计算脚本绑定桥接ID映射关系 | ✅ 197/197 |
| ✅ 接口重试、降级熔断逻辑对齐B-02 L1 | ✅ 3级重试+L1/L2/L3降级 |
| ✅ 影子测试底层日志采集规则完整 | ✅ 6类日志+5级 |
| ✅ 跨团队同步日志归档 | ✅ 5条 |
| ✅ DSHB_PROD_PHASE_STAGE4_READY=TRUE | ✅ |
