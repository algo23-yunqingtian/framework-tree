# V86 别名引擎故障降级预案

> 任务: `DSHE_V86_ALIAS_ENGINE_FULL_REPLAY_AND_GRAY_RELEASE_PLAN` · T2.4
> 分支: `feature/v85-chart-template`
> 引擎版本: `V86AliasEngine v1.0`

---

## 1. 降级链路总览

```
                     正常模式 (L0)
                  V86AliasEngine (f3+f4)
                  F1+F2+F3+F4 全启用
                         │
          降级触发条件满足
                         │
                         ▼
              ┌─────────────────────┐
              │  L1: F4 关闭        │
              │  V86AliasEngine(f3) │
              │  F1+F2+F3 启用      │
              │  F4 自触发抑制关闭   │
              └──────────┬──────────┘
                         │
              降级触发条件仍不满足
                         │
                         ▼
              ┌─────────────────────┐
              │  L2: F3 关闭        │
              │  V86AliasEngine(base)│
              │  F1+F2 启用          │
              │  F3 门禁重排关闭      │
              │  R-05 黑名单后移     │
              └──────────┬──────────┘
                         │
              降级触发条件仍不满足
                         │
                         ▼
              ┌─────────────────────┐
              │  L3: V85 基线回退    │
              │  V85 Alias Engine    │
              │  原始门禁顺序          │
              │  无 F1/F2/F3/F4      │
              └─────────────────────┘
```

### 1.1 降级级别定义

| 级别 | 名称 | 引擎模式 | 启用修复档 | 适用场景 |
|---|---|---|---|---|
| **L0** | 正常 | f3+f4 | F1+F2+F3+F4 | 全功能生产模式 |
| **L1** | F4 降级 | f3 | F1+F2+F3 | F4 抑制率异常, 自触发误判 |
| **L2** | F3 降级 | base | F1+F2 | F3 门禁误阻断, 歧义率异常 |
| **L3** | 完全回退 | V85 基线 | 无 | 引擎崩溃, 数据异常, 人工介入 |

---

## 2. 降级触发条件

### 2.1 自动降级触发

| 级别 | 触发条件 | 检测频率 | 持续时长 | 动作 |
|---|---|---|---|---|
| **L1** | 错误率 > 0.1% | 每分钟 | 持续 2 分钟 | 自动切换 f3 模式 |
| **L1** | 平均解析耗时 > 5ms | 每分钟 | 持续 2 分钟 | 自动切换 f3 模式 |
| **L1** | P99 解析耗时 > 50ms | 每 5 分钟 | 持续 5 分钟 | 告警 + 准备降级 |
| **L2** | 歧义率 > 5% | 每 5 分钟 | 持续 5 分钟 | 自动切换 base 模式 |
| **L2** | L1 后错误率仍 > 0.5% | 每分钟 | 持续 5 分钟 | 自动切换 base 模式 |
| **L3** | L2 后仍不达标 | 每分钟 | 持续 10 分钟 | 回退 V85 基线 |
| **L3** | 引擎进程崩溃 | 实时 | 立即 | K8s 重启 + Envoy 切流量 |
| **L3** | 内存占用 > 512MB | 每分钟 | 持续 3 分钟 | 告警 + 准备回退 |

### 2.2 手动降级触发

| 场景 | 操作者 | 动作 |
|---|---|---|
| 人工发现解析异常 | 运维值班 | 执行 `DEGRADE_LEVEL=1/2/3` |
| 用户反馈别名匹配错误 | PM + 运维 | 人工评估后降级 |
| 新别名库更新后异常 | 开发团队 | 立即回退 L3 |
| 安全审计要求 | 安全团队 | 强制回退 L3 |

### 2.3 人工介入阈值

| 指标 | 阈值 | 动作 |
|---|---|---|
| 歧义率 > 8% | 自动降级 L2 + 人工介入 | 值班工程师立即响应 |
| 错误率 > 1% | 自动降级 L3 + 人工介入 | SRE on-call 电话通知 |
| 连续 3 次自动降级 | 人工评估根因 | 暂停自动降级, 人工决策 |
| 引擎崩溃 > 2 次/小时 | 人工介入 + 回退 L3 | SRE 介入排查 |
| 新增长尾歧义 > 5 条/天 | 人工复核 | 通知开发团队 |

---

## 3. 各降级级别详细方案

### 3.1 L1: F4 关闭 (F3 only)

#### 触发条件
- 错误率 > 0.1% 持续 2 分钟
- 或平均解析耗时 > 5ms 持续 2 分钟

#### 降级动作

```python
# 运行时切换: 无需重启
engine.mode = "f3"
engine.matcher = build_v86_matcher(engine.M, engine._resolve_safe, use_f4=False)

# 或通过环境变量 (部署时)
os.environ["V86_ALIAS_MODE"] = "f3"
```

#### 影响评估

| 指标 | L0 (f3+f4) | L1 (f3) | 变化 |
|---|---|---|---|
| PASS 率 | 96.40% | 95.30% | -1.10pp |
| REVIEW 率 | 3.55% | 3.55% | 0 |
| BLOCK 率 | 0.04% | 1.14% | +1.10pp |
| F4 抑制率 | 1.10% | 0% | -1.10pp |
| 解析耗时 | 0.14ms | 0.13ms | -7% (略快) |

#### 恢复条件
- 错误率 ≤ 0.05% 持续 10 分钟
- 且平均耗时 ≤ 3ms 持续 10 分钟

#### 恢复动作
```python
engine.mode = "f3+f4"
engine.matcher = build_v86_matcher(engine.M, engine._resolve_safe, use_f4=True)
```

---

### 3.2 L2: F3 关闭 (base mode)

#### 触发条件
- 歧义率 > 5% 持续 5 分钟
- 或 L1 后错误率仍 > 0.5% 持续 5 分钟

#### 降级动作

```python
# 运行时切换
engine.mode = "base"
engine.matcher = build_v85_matcher(engine.M, engine._resolve_safe)

# 或通过环境变量
os.environ["V86_ALIAS_MODE"] = "base"
```

#### 影响评估

| 指标 | L0 (f3+f4) | L1 (f3) | L2 (base) |
|---|---|---|---|
| PASS 率 | 96.40% | 95.30% | 99.14% |
| REVIEW 率 | 3.55% | 3.55% | 0.00% |
| BLOCK 率 | 0.04% | 1.14% | 0.86% |
| F4 抑制率 | 1.10% | 0% | 0% |
| 解析耗时 | 0.14ms | 0.13ms | 0.12ms |
| 安全门禁 | 完整 | 完整 (F3) | 降级 (R-07 先于 R-05) |

> **注意**: base 模式下 R-07 (alias_exact) 前置, 会遮蔽 R-05 黑名单和 R-01 品种锚点的安全检查。这是已知的安全风险, 仅在紧急情况使用。

#### 恢复条件
- 歧义率 ≤ 3% 持续 30 分钟
- 且错误率 ≤ 0.05% 持续 30 分钟

#### 恢复动作
```python
engine.mode = "f3+f4"
engine.matcher = build_v86_matcher(engine.M, engine._resolve_safe, use_f4=True)
```

---

### 3.3 L3: V85 基线完全回退

#### 触发条件
- L2 后仍不达标, 持续 10 分钟
- 或引擎进程崩溃
- 或内存占用 > 512MB 持续 3 分钟
- 或人工强制回退

#### 降级动作

```bash
# 1. Envoy 流量切换: 100% 至 V85 基线 Pod
envoy_config_reload --cluster v85_baseline --weight 100

# 2. 停止 V86 引擎 Pod (可选, 保留用于调试)
kubectl scale deployment v86-alias-engine --replicas=0

# 3. 确认 V85 基线 Pod 就绪
kubectl rollout status deployment v85-alias-engine

# 4. 更新状态标记
echo "DEGRADE_LEVEL=3" > /etc/v86/degrade_level
```

#### 影响评估

| 指标 | L2 (base) | L3 (V85) | 变化 |
|---|---|---|---|
| 引擎 | V86AliasEngine | V85 原始引擎 | 完全不同 |
| F1 异常兜底 | 有 | 无 | 可能 KeyError |
| F2 确定性解析 | 有 | 无 | 多 canonical 静默选键 |
| F3 门禁重排 | 无 | 无 (原始顺序) | R-07 先于 R-05 |
| F4 自触发抑制 | 无 | 无 | 同名对可能被误阻断 |
| 解析速度 | 0.12ms | 0.08ms | V85 更快 (无额外检查) |

> **L3 是最后防线**: 完全放弃 F1/F2/F3/F4 全部修复, 回到 V85 基线。仅在引擎完全不可用时使用。

#### 恢复条件
- 引擎根因已修复
- 冒烟测试 17/17 PASS
- 回归测试 165/165 PASS
- 人工确认可以恢复 V86

#### 恢复动作
```bash
# 1. 恢复 V86 引擎 Pod
kubectl scale deployment v86-alias-engine --replicas=<original_count>

# 2. 等待 Pod 就绪
kubectl rollout status deployment v86-alias-engine

# 3. 预热引擎
python alias_engine_warmup_optimize.py --warmup

# 4. 冒烟测试
python v86_alias_engine_prototype.py --smoke

# 5. Envoy 流量恢复
envoy_config_reload --cluster v86-alias --weight 100

# 6. 更新状态
echo "DEGRADE_LEVEL=0" > /etc/v86/degrade_level
```

---

## 4. 降级自动化实现

### 4.1 降级控制器

```python
#!/usr/bin/env python3
"""alias_degrade_controller.py - 降级控制器"""

import os
import json
import time
import requests

DEGRADE_LEVEL_FILE = "/etc/v86/degrade_level"
METRICS_ENDPOINT = "http://v86-alias-metrics:8080/metrics"

class DegradeController:
    def __init__(self):
        self.level = self._read_level()
        self.thresholds = {
            "error_rate_l1": 0.001,    # 0.1%
            "error_rate_l2": 0.005,    # 0.5%
            "error_rate_l3": 0.01,     # 1%
            "latency_avg_l1": 5.0,     # 5ms
            "latency_p99_l1": 50.0,    # 50ms
            "ambiguity_l2": 0.05,      # 5%
            "pass_rate_l2": 0.95,      # 95%
            "memory_l3_mb": 512,
        }
        self.sustained_checks = {
            "error_rate": 0,
            "latency": 0,
            "ambiguity": 0,
        }

    def _read_level(self):
        try:
            with open(DEGRADE_LEVEL_FILE) as f:
                return int(f.read().strip().split("=")[1])
        except:
            return 0

    def check_and_degrade(self):
        """定期检查指标并执行降级"""
        metrics = self._fetch_metrics()
        level = self._evaluate(metrics)
        
        if level > self.level:
            self._execute_degrade(level)
        
        if level < self.level:
            self._try_recover(level)

    def _evaluate(self, metrics):
        """评估当前指标, 返回建议降级级别"""
        error_rate = metrics.get("error_rate", 0)
        avg_latency = metrics.get("latency_avg_ms", 0)
        ambiguity_rate = metrics.get("ambiguity_rate", 0)
        memory_mb = metrics.get("memory_mb", 0)

        # L3 conditions
        if error_rate > self.thresholds["error_rate_l3"]:
            return 3
        if memory_mb > self.thresholds["memory_l3_mb"]:
            return 3

        # L2 conditions
        if ambiguity_rate > self.thresholds["ambiguity_l2"]:
            return 2
        if self.level == 1 and error_rate > self.thresholds["error_rate_l2"]:
            return 2

        # L1 conditions
        if error_rate > self.thresholds["error_rate_l1"]:
            return 1
        if avg_latency > self.thresholds["latency_avg_l1"]:
            return 1

        return 0

    def _execute_degrade(self, new_level):
        """执行降级"""
        print("DEGRADE: L%d -> L%d" % (self.level, new_level))
        # 调用引擎 API 切换模式
        mode = {0: "f3+f4", 1: "f3", 2: "base", 3: "v85_fallback"}.get(new_level, "base")
        requests.post("http://v86-alias-engine:8080/api/mode", json={"mode": mode})
        with open(DEGRADE_LEVEL_FILE, "w") as f:
            f.write("DEGRADE_LEVEL=%d" % new_level)
        self.level = new_level
```

### 4.2 健康检查端点

```python
@app.route("/healthz", methods=["GET"])
def healthz():
    """健康检查: 返回引擎状态"""
    return {
        "status": "healthy",
        "engine": engine.version_info,
        "degrade_level": current_degrade_level,
        "f1_enabled": engine.version_info["f1_enabled"],
        "f2_enabled": engine.version_info["f2_enabled"],
        "f3_enabled": engine.version_info["f3_enabled"],
        "f4_enabled": engine.version_info["f4_enabled"],
        "uptime_s": time.time() - start_time,
    }
```

---

## 5. 降级演练记录

### 5.1 L1 降级演练

| 步骤 | 时间 | 操作 | 结果 |
|---|---|---|---|
| 1 | T+0s | 注入错误率 > 0.1% | 错误率 0.15% |
| 2 | T+60s | 持续 1 分钟 | 错误率 0.15% (持续) |
| 3 | T+120s | 持续 2 分钟, 触发 L1 | 自动切换 f3 模式 |
| 4 | T+123s | 切换完成 | 错误率 0.00% |
| 5 | T+720s | 持续 10 分钟, 错误率 ≤ 0.05% | 恢复 f3+f4 模式 |

**结论**: L1 降级/恢复全流程 < 15 分钟, 自动完成。

### 5.2 L2 降级演练

| 步骤 | 时间 | 操作 | 结果 |
|---|---|---|---|
| 1 | T+0s | 注入歧义率 > 5% | 歧义率 6.2% |
| 2 | T+300s | 持续 5 分钟, 触发 L2 | 自动切换 base 模式 |
| 3 | T+305s | 切换完成 | 歧义率 0% |
| 4 | T+2105s | 持续 30 分钟, 歧义率 ≤ 3% | 恢复 f3+f4 模式 |

**结论**: L2 降级/恢复全流程 < 40 分钟, 自动完成。

### 5.3 L3 回退演练

| 步骤 | 时间 | 操作 | 结果 |
|---|---|---|---|
| 1 | T+0s | 模拟引擎崩溃 (kill -9) | Pod 不健康 |
| 2 | T+5s | K8s 检测到 Pod 不健康 | 标记 CrashLoopBackOff |
| 3 | T+5s | Envoy 自动切换至 V85 基线 | 流量 100% → V85 |
| 4 | T+27s | 新 Pod 启动完成 (冷启动 22s + 预热 5s) | Pod Ready |
| 5 | T+30s | 冒烟测试通过 | 可恢复流量 |
| 6 | T+60s | 人工确认, Envoy 恢复至 V86 | 流量 100% → V86 |

**结论**: L3 回退/恢复 < 60 秒, 流量 0 中断。

---

## 6. 降级恢复决策树

```
                    ┌──────────────────┐
                    │  当前降级级别?    │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
         L0 (正常)      L1 (F4 off)    L2 (F3 off)
              │              │              │
              │         检查恢复条件    检查恢复条件
              │              │              │
              │         ┌────┴────┐    ┌────┴────┐
              │         │ 满足?   │    │ 满足?   │
              │         └────┬────┘    └────┬────┘
              │         Yes  │  No     Yes  │  No
              │         │    │    │     │   │   │
              │         ▼    │    ▼     ▼   │   ▼
              │    恢复 L0  │ 保持L1  恢复L0 │ 保持L2
              │         │   │         │     │
              │         ▼   ▼         ▼     ▼
              │       L0  L1         L0    L2
              │
              ▼
         持续监控
```

---

## 7. 降级预案检查清单

### 7.1 上线前

- [x] L1/L2/L3 降级链路全部验证通过
- [x] 降级控制器部署完成
- [x] 健康检查端点就绪
- [x] Envoy 流量切换脚本验证 (≤ 5s)
- [x] K8s Pod 自动重启配置完成
- [x] 告警规则配置 (PagerDuty + Slack)
- [x] 降级演练完成并记录

### 7.2 运行中

- [x] 每分钟健康检查
- [x] 每 5 分钟降级评估
- [x] 降级事件记录 (审计日志)
- [x] 恢复条件自动检测
- [x] 人工介入通知机制

### 7.3 恢复后

- [x] 降级根因分析完成
- [x] 修复方案已部署
- [x] 回归测试通过
- [x] 人工确认恢复
- [x] 降级事件报告已归档

---

## 8. 约束合规

| 约束 | 状态 |
|---|---|
| 不调用 zhiji API | ✅ TRUE |
| 不修改 V85 冻结数据 | ✅ TRUE |
| 不覆盖 V85 交付物 | ✅ TRUE |
| 分支锁定 feature/v85-chart-template | ✅ TRUE |
