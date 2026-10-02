# V86 别名引擎运维手册 (终稿)

> 任务: `DSHE_V86_ALIAS_PROD_INTEGRATE_ADAPT_GRAY_SIMULATION_AND_OPS_MANUAL_FINAL` · T2.3
> 分支: `feature/v85-chart-template`
> 版本: `v1.0-final`
> 适用角色: 一线运维 / SRE / 值班工程师
> 生成时间: 2026-10-02

---

## 目录

1. [快速参考 (应急单页)](#1-快速参考-应急单页)
2. [部署步骤](#2-部署步骤)
3. [配置修改](#3-配置修改)
4. [缓存预热与清理](#4-缓存预热与清理)
5. [流量切分与灰度控制](#5-流量切分与灰度控制)
6. [模块开关操作](#6-模块开关操作)
7. [故障排查](#7-故障排查)
8. [常见故障 FAQ](#8-常见故障-faq)
9. [告警处置手册](#9-告警处置手册)
10. [日志关键字速查](#10-日志关键字速查)
11. [日常运维检查表](#11-日常运维检查表)

---

## 1. 快速参考 (应急单页)

### 1.1 一键诊断

```bash
# 1. 检查服务状态
kubectl get pods -n dshe-v86 -l app=v86-alias-engine
curl -s http://v86-alias-engine:8080/healthz | python3 -m json.tool

# 2. 检查当前降级级别
cat /etc/v86/degrade_level  # DEGRADE_LEVEL=0 表示正常

# 3. 检查关键指标
curl -s http://v86-alias-engine:8081/metrics | grep -E "alias_(resolve|error|cache|verdict)"

# 4. 查看最近日志
kubectl logs -n dshe-v86 deploy/v86-alias-engine --tail=100
```

### 1.2 紧急降级命令

```bash
# L1 降级 (F4 off) — 错误率/耗时异常
echo "DEGRADE_LEVEL=1" > /etc/v86/degrade_level
curl -X POST http://v86-alias-engine:8080/api/mode -d '{"mode":"f3"}'

# L2 降级 (F3 off) — 歧义率异常
echo "DEGRADE_LEVEL=2" > /etc/v86/degrade_level
curl -X POST http://v86-alias-engine:8080/api/mode -d '{"mode":"base"}'

# L3 回退 (V85) — 引擎崩溃/数据异常
echo "DEGRADE_LEVEL=3" > /etc/v86/degrade_level
# Envoy 切流量至 V85 基线 Pod
envoy_config_reload --cluster v85_baseline --weight 100
```

### 1.3 紧急恢复命令

```bash
# 恢复正常模式
echo "DEGRADE_LEVEL=0" > /etc/v86/degrade_level
curl -X POST http://v86-alias-engine:8080/api/mode -d '{"mode":"f3+f4"}'

# 从 V85 恢复至 V86
envoy_config_reload --cluster v86-alias --weight 100
```

### 1.4 联系方式

| 角色 | 通知方式 | 响应时间 |
|------|----------|----------|
| P0-Critical | PagerDuty + 电话 | 5 分钟 |
| P1-Warning | Slack + 短信 | 15 分钟 |
| P2-Info | Slack | 30 分钟 |
| P3-Notification | 邮件 | 2 小时 |

---

## 2. 部署步骤

### 2.1 本地部署 (开发/测试)

```bash
# 1. 安装依赖
pip3 install -r startup/requirements.txt

# 2. 设置环境变量
export V86_ALIAS_MODE="f3+f4"
export V86_CACHE_DIR="/tmp/v86-alias-cache"
export V86_LOG_DIR="/tmp/v86-alias-log"

# 3. 运行预热
python3 alias_engine_warmup_optimize.py --warmup

# 4. 验证预热
python3 alias_engine_warmup_optimize.py --verify

# 5. 运行启动脚本
./startup/start_alias_engine.sh

# 6. 验证
curl http://localhost:8080/healthz
curl http://localhost:8081/metrics | head -20
```

### 2.2 Docker 部署

```bash
# 1. 构建镜像
docker build -f deploy/Dockerfile -t v86-alias-engine:v86.0.0 .

# 2. 运行容器
docker run -d \
  --name v86-alias-engine \
  -p 8080:8080 -p 8081:8081 \
  -e V86_ALIAS_MODE="f3+f4" \
  -v v86_cache:/var/cache/v86-alias \
  v86-alias-engine:v86.0.0

# 3. 查看日志
docker logs -f v86-alias-engine

# 4. 验证
curl http://localhost:8080/healthz
curl http://localhost:8081/metrics

# 5. 停止
docker stop v86-alias-engine
docker rm v86-alias-engine
```

### 2.3 Docker Compose 部署

```bash
# 1. 启动全部服务 (V86 + V85 基线)
docker compose -f deploy/docker-compose.yaml up -d

# 2. 查看状态
docker compose -f deploy/docker-compose.yaml ps

# 3. 验证
curl http://localhost:8080/healthz    # V86 引擎
curl http://localhost:8081/metrics     # V86 指标
curl http://localhost:8082/healthz    # V85 基线 (fallback)

# 4. 停止
docker compose -f deploy/docker-compose.yaml down
```

### 2.4 Kubernetes 部署

```bash
# 1. 创建 namespace
kubectl create namespace dshe-v86

# 2. 创建 PVC (缓存持久化)
kubectl apply -f deploy/pvc.yaml

# 3. 部署引擎
kubectl apply -f deploy/k8s-deployment.yaml

# 4. 创建 Service
kubectl apply -f deploy/service.yaml

# 5. 创建 ConfigMap (引擎配置)
kubectl apply -f deploy/configmap.yaml

# 6. 查看状态
kubectl get pods -n dshe-v86 -l app=v86-alias-engine
kubectl get svc -n dshe-v86

# 7. 验证
kubectl port-forward -n dshe-v86 pod/v86-alias-xxx 8080:8080
curl http://localhost:8080/healthz

# 8. 扩容
kubectl scale deployment -n dshe-v86 v86-alias-engine --replicas=3

# 9. 缩容
kubectl scale deployment -n dshe-v86 v86-alias-engine --replicas=1

# 10. 滚动更新
kubectl set image deployment/v86-alias-engine \
  -n dshe-v86 v86-alias=registry.local/v86-alias-engine:v86.0.1
```

### 2.5 部署后验证清单

```bash
# 1. 健康检查
curl -s http://v86-alias-engine:8080/healthz | python3 -c "
import sys,json
d=json.load(sys.stdin)
assert d['status']=='healthy'
assert d['degrade_level']==0
assert d['engine']['mode']=='f3+f4'
print('Health check: PASS')
"

# 2. 指标验证
curl -s http://v86-alias-engine:8081/metrics | grep -E "alias_(resolve|cache|verdict)"

# 3. 缓存验证
ls -la /var/cache/v86-alias/
cat /var/cache/v86-alias/metadata.json

# 4. 冒烟测试
python3 v86_alias_engine_prototype.py --smoke

# 5. 门禁校验
python3 alias_gate_auto_check.py --all
```

---

## 3. 配置修改

### 3.1 引擎模式切换

```bash
# 通过环境变量 (部署时)
export V86_ALIAS_MODE="f3"      # L1: F4 off
export V86_ALIAS_MODE="base"    # L2: F3 off
export V86_ALIAS_MODE="f3+f4"   # L0: 正常 (默认)

# 通过 API (运行时, 无需重启)
curl -X POST http://v86-alias-engine:8080/api/mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"f3+f4"}'

# 通过降级文件 (降级控制器读取)
echo "DEGRADE_LEVEL=1" > /etc/v86/degrade_level
```

### 3.2 缓存配置修改

**文件**: `/var/cache/v86-alias/cache_config.yaml` (或挂载的 ConfigMap)

```yaml
# 修改 LRU 缓存大小
cache:
  lru:
    max_size: 2048          # 增大缓存 (默认 1024)
    persist_interval_seconds: 600  # 减少持久化频率 (默认 300s)

# 修改预热样本
cache:
  warmup:
    samples:
      - "碳酸锂工厂库存天数"
      - "电解铜库存"
      # 添加新样本...
```

**重载配置 (无需重启)**:
```bash
# 发送 SIGHUP 信号重载配置
kill -HUP $(cat /var/run/v86-alias.pid)
```

### 3.3 环境变量修改

| 环境变量 | 默认值 | 修改方式 | 生效方式 |
|----------|--------|----------|----------|
| V86_ALIAS_MODE | f3+f4 | K8s env / shell export | 重启 Pod |
| V86_WARMUP | true | K8s env / shell export | 重启 Pod |
| V86_CACHE_DIR | /var/cache/v86-alias | K8s env | 重启 Pod |
| V86_LOG_DIR | /var/log/v86-alias | K8s env | 重启 Pod |
| V86_HEALTH_PORT | 8080 | K8s env | 重启 Pod |
| V86_METRICS_PORT | 8081 | K8s env | 重启 Pod |
| V86_INIT_TIMEOUT | 60 | K8s env | 重启 Pod |

**K8s 修改示例**:
```bash
# 修改 V86_ALIAS_MODE
kubectl set env deployment/v86-alias-engine \
  -n dshe-v86 V86_ALIAS_MODE=f3+f4

# 验证
kubectl get deployment -n dshe-v86 v86-alias-engine -o jsonpath='{.spec.template.spec.containers[0].env}'

# 等待滚动更新
kubectl rollout status deployment/v86-alias-engine -n dshe-v86
```

### 3.4 Prometheus 监控配置

```yaml
# /etc/prometheus/prometheus.yml
scrape_configs:
  - job_name: 'v86-alias'
    scrape_interval: 15s
    static_configs:
      - targets: ['v86-alias-engine:8081']
    metrics_path: /metrics
```

---

## 4. 缓存预热与清理

### 4.1 缓存预热

```bash
# 手动预热 (启动后)
python3 alias_engine_warmup_optimize.py --warmup

# 验证预热结果
python3 alias_engine_warmup_optimize.py --verify

# 预热报告
python3 alias_engine_warmup_optimize.py --benchmark

# 保存缓存
python3 alias_engine_warmup_optimize.py --save-cache
```

### 4.2 预热样本清单

| # | 样本 | 品种 | 类型 |
|---|------|------|------|
| 1 | 碳酸锂工厂库存天数 | LI | 常见别名 |
| 2 | 电解铜库存 | CU | 常见别名 |
| 3 | 锌锭库存 | ZN | 常见别名 |
| 4 | 锡锭库存 | SN | 常见别名 |
| 5 | 铅锭库存 | PB | 常见别名 |
| 6 | 工业铝库存 | AL | 常见别名 |
| 7 | GFEX：工业硅：主力合约：收盘价（日） | SI | 跨品种 |
| 8 | SHFE：沪铜：主力合约：收盘价（日） | CU | 跨品种 |
| 9 | 碳酸锂利润与需求分析 | LI | 边界 case |
| 10 | 锡厂库存天数（天） | SN | 边界 case |
| 11 | 工业硅：421#：成本：新疆（周） | SI | 复杂别名 |
| 12 | MHP：NI≥34%,CO≥2%：镍远期现货价格：中国主要港口（日） | NI | 复杂别名 |

### 4.3 缓存清理

```bash
# 清理当前缓存 (不删除历史)
python3 alias_engine_warmup_optimize.py --clear-cache

# 清理所有缓存 (包括历史备份)
rm -rf /var/cache/v86-alias/*.pkl

# 验证清理
ls -la /var/cache/v86-alias/
# 应只剩 metadata.json 和空目录
```

### 4.4 缓存持久化管理

```bash
# 查看缓存文件列表
ls -lh /var/cache/v86-alias/

# 查看缓存元数据
cat /var/cache/v86-alias/metadata.json | python3 -m json.tool

# 查看缓存大小
du -sh /var/cache/v86-alias/

# 手动触发持久化
python3 alias_engine_warmup_optimize.py --save-cache
```

### 4.5 缓存维护策略

| 操作 | 频率 | 命令 |
|------|------|------|
| 缓存持久化 | 自动 (300s) | — |
| 缓存清理 | 自动 (24h) | keep_last_n_files: 7 |
| 缓存大小监控 | 每 5 分钟 | `alias_cache_size` metric |
| 手动预热 | 按需 | `--warmup` |
| 手动保存 | 按需 | `--save-cache` |

---

## 5. 流量切分与灰度控制

### 5.1 流量比例调整 (Envoy)

```bash
# 查看当前流量分配
envoy_config_get --cluster v86_gray --cluster v85_baseline

# 调整至 10%:90%
envoy_config_reload --cluster v86_gray --weight 10 \
                     --cluster v85_baseline --weight 90

# 调整至 30%:70%
envoy_config_reload --cluster v86_gray --weight 30 \
                     --cluster v85_baseline --weight 70

# 全量切换 100%:0%
envoy_config_reload --cluster v86_gray --weight 100 \
                     --cluster v85_baseline --weight 0

# 紧急回退 0%:100%
envoy_config_reload --cluster v86_gray --weight 0 \
                     --cluster v85_baseline --weight 100
```

### 5.2 K8s 流量切分 (Istio/Service Mesh)

```yaml
# VirtualService: 10% 灰度
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: v86-alias-virtualservice
spec:
  hosts:
    - v86-alias-engine
  http:
    - route:
        - destination:
            host: v86-alias-gray
          weight: 10
        - destination:
            host: v85-alias-baseline
          weight: 90
```

```bash
# 应用配置
kubectl apply -f virtualservice.yaml

# 验证
kubectl get virtualservice -n dshe-v86

# 修改灰度比例至 30%
kubectl edit virtualservice v86-alias-virtualservice -n dshe-v86
```

### 5.3 灰度放量操作步骤

```
Phase 1 (10%):
  1. envoy_config_reload --v86_gray 10 --v85_baseline 90
  2. 监控 3 天, 门禁全部 PASS
  3. 确认无 P0 告警
  → 进入 Phase 2

Phase 2 (30%):
  4. envoy_config_reload --v86_gray 30 --v85_baseline 70
  5. 监控 3 天, 门禁全部 PASS
  6. 确认无 P0 告警
  → 进入 Phase 3

Phase 3 (100%):
  7. envoy_config_reload --v86_gray 100 --v85_baseline 0
  8. 监控 24 小时
  9. 确认无 P0 告警
  → 全量切换完成

回退:
  envoy_config_reload --v86_gray 0 --v85_baseline 100
```

### 5.4 流量标签 (自定义路由)

```bash
# 通过 HTTP Header 指定引擎模式
curl -H "X-Engine-Mode: f3+f4" http://v86-alias-engine:8080/resolve \
  -d '{"alias_names":["碳酸锂工厂库存天数"]}'

curl -H "X-Engine-Mode: base" http://v86-alias-engine:8080/resolve \
  -d '{"alias_names":["碳酸锂工厂库存天数"]}'

# 通过 X-Gray-Routing 标签强制路由
curl -H "X-Gray-Routing: v86-gray" http://v86-alias-engine:8080/resolve \
  -d '{"alias_names":["碳酸锂工厂库存天数"]}'
```

---

## 6. 模块开关操作

### 6.1 F3/F4 动态开关

```bash
# 关闭 F4 (降级至 f3 模式)
curl -X POST http://v86-alias-engine:8080/api/mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"f3"}'

# 关闭 F3 (降级至 base 模式)
curl -X POST http://v86-alias-engine:8080/api/mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"base"}'

# 恢复全功能
curl -X POST http://v86-alias-engine:8080/api/mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"f3+f4"}'

# 验证当前模式
curl -s http://v86-alias-engine:8080/healthz | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f\"Mode: {d['engine']['mode']}\")
print(f\"F3: {d['engine']['f3_enabled']}\")
print(f\"F4: {d['engine']['f4_enabled']}\")
"
```

### 6.2 降级级别管理

```bash
# 查看当前降级级别
cat /etc/v86/degrade_level  # DEGRADE_LEVEL=0

# 手动降级
echo "DEGRADE_LEVEL=1" > /etc/v86/degrade_level
# 降级控制器会在下次轮询时检测到变更

# 手动恢复
echo "DEGRADE_LEVEL=0" > /etc/v86/degrade_level

# 查看降级历史
tail -50 /var/log/v86-alias/degrade_audit.log
```

### 6.3 降级级别说明

| 级别 | 模式 | F1 | F2 | F3 | F4 | 适用场景 |
|------|------|----|----|----|----|----------|
| L0 | f3+f4 | ✅ | ✅ | ✅ | ✅ | 正常生产 |
| L1 | f3 | ✅ | ✅ | ✅ | ❌ | F4 抑制率异常 |
| L2 | base | ✅ | ✅ | ❌ | ❌ | F3 门禁误阻断 |
| L3 | V85 | ❌ | ❌ | ❌ | ❌ | 引擎崩溃/数据异常 |

### 6.4 模块状态查询

```bash
# 完整状态查询
curl -s http://v86-alias-engine:8080/healthz | python3 -m json.tool

# 输出示例:
# {
#   "status": "healthy",
#   "engine": {
#     "version": "v86.0.0",
#     "mode": "f3+f4",
#     "f1_enabled": true,
#     "f2_enabled": true,
#     "f3_enabled": true,
#     "f4_enabled": true
#   },
#   "degrade_level": 0,
#   "uptime_s": 3600.0
# }
```

---

## 7. 故障排查

### 7.1 服务不健康

**症状**: `/healthz` 返回 503 或超时

**排查步骤**:

```bash
# 1. 检查 Pod 状态
kubectl get pods -n dshe-v86 -l app=v86-alias-engine
kubectl describe pod -n dshe-v86 <pod-name>

# 2. 检查日志
kubectl logs -n dshe-v86 <pod-name> --tail=200

# 3. 检查资源
kubectl top pod -n dshe-v86 <pod-name>
# 确认 CPU/Memory 未超限

# 4. 检查探针
kubectl describe pod -n dshe-v86 <pod-name> | grep -A 20 "Readiness"

# 5. 检查 PVC
kubectl get pvc -n dshe-v86 v86-alias-cache-pvc
kubectl describe pvc -n dshe-v86 v86-alias-cache-pvc

# 6. 检查缓存目录
kubectl exec -n dshe-v86 <pod-name> -- ls -la /var/cache/v86-alias/

# 7. 检查端口
kubectl port-forward -n dshe-v86 <pod-name> 8080:8080
curl http://localhost:8080/healthz
```

**常见原因**:
| 原因 | 解决方案 |
|------|----------|
| 缓存目录不可写 | 检查 PVC 挂载和权限 |
| 内存超限 | 检查 `V86_CACHE_DIR` 路径, 清理缓存 |
| 端口被占用 | 检查其他服务是否占用 8080/8081 |
| 依赖缺失 | 检查 `requirements.txt` 安装情况 |

### 7.2 解析超时

**症状**: 平均耗时 > 5ms, P99 > 50ms

**排查步骤**:

```bash
# 1. 检查缓存命中率
curl -s http://v86-alias-engine:8081/metrics | grep alias_cache_hit_rate
# 若 < 85%, 缓存失效, 触发 L1 降级

# 2. 检查负载
curl -s http://v86-alias-engine:8081/metrics | grep alias_resolve_total
# 若 > 2000/s, 可能超过容量

# 3. 检查引擎模式
curl -s http://v86-alias-engine:8080/healthz | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f\"Mode: {d['engine']['mode']}\")
print(f\"F4: {d['engine']['f4_enabled']}\")
"

# 4. 检查日志
kubectl logs -n dshe-v86 <pod-name> | grep -i "timeout\|slow\|latency"
```

### 7.3 歧义率异常

**症状**: 歧义率 > 5%

**排查步骤**:

```bash
# 1. 检查歧义率
curl -s http://v86-alias-engine:8081/metrics | grep alias_ambiguous_rate

# 2. 检查长尾歧义
curl -s http://v86-alias-engine:8081/metrics | grep alias_tail_ambiguous_total

# 3. 检查引擎模式 (base 模式无歧义)
curl -s http://v86-alias-engine:8080/healthz | python3 -c "
import sys,json; d=json.load(sys.stdin)
print(f\"Mode: {d['engine']['mode']}\")
"

# 4. 若 f3+f4 模式歧义率高, 降级至 L2 (base)
echo "DEGRADE_LEVEL=2" > /etc/v86/degrade_level
```

### 7.4 错误率异常

**症状**: 错误率 > 0.1%

**排查步骤**:

```bash
# 1. 检查错误码分布
curl -s http://v86-alias-engine:8081/metrics | grep alias_error_total

# 2. 检查日志
kubectl logs -n dshe-v86 <pod-name> | grep -i "error\|exception\|traceback"

# 3. 检查最近错误
kubectl logs -n dshe-v86 <pod-name> --tail=50 | grep "ERROR"

# 4. 若错误率持续 > 0.1%, 降级至 L1
echo "DEGRADE_LEVEL=1" > /etc/v86/degrade_level
```

### 7.5 缓存异常

**症状**: 缓存命中率 < 85%, 或缓存文件损坏

**排查步骤**:

```bash
# 1. 检查缓存文件
ls -lh /var/cache/v86-alias/

# 2. 检查缓存完整性
python3 -c "
import pickle
with open('/var/cache/v86-alias/resolve_cache.pkl', 'rb') as f:
    data = pickle.load(f)
print(f'Cache entries: {len(data)}')
"

# 3. 若缓存损坏, 清除并重新预热
python3 alias_engine_warmup_optimize.py --clear-cache
python3 alias_engine_warmup_optimize.py --warmup
python3 alias_engine_warmup_optimize.py --save-cache

# 4. 检查磁盘空间
df -h /var/cache/v86-alias/
```

### 7.6 Pod 重启循环 (CrashLoopBackOff)

**症状**: Pod 反复重启, `CrashLoopBackOff`

**排查步骤**:

```bash
# 1. 查看重启次数
kubectl get pods -n dshe-v86 -l app=v86-alias-engine
# 检查 RESTARTS 列

# 2. 查看上次崩溃日志
kubectl logs -n dshe-v86 <pod-name> --previous --tail=200

# 3. 检查退出码
kubectl describe pod -n dshe-v86 <pod-name> | grep -A 5 "Last State"
# Exit Code 137 = OOM Kill
# Exit Code 1 = 应用错误

# 4. 若 OOM, 增加内存限制
kubectl set resources deployment/v86-alias-engine \
  -n dshe-v86 --limits=memory=1024Mi

# 5. 若应用错误, 检查日志并修复
```

### 7.7 Envoy 流量切换失败

**症状**: 灰度放量后流量未切换

**排查步骤**:

```bash
# 1. 检查 Envoy 配置
envoy_config_get --cluster v86_gray --cluster v85_baseline

# 2. 检查 Envoy 服务状态
curl -s http://envoy-admin:8000/healthcheck/healthcheck

# 3. 检查 Envoy 日志
kubectl logs -n istio-system envoy-<pod-name> | tail -50

# 4. 检查 VirtualService
kubectl get virtualservice -n dshe-v86 v86-alias-virtualservice -o yaml

# 5. 手动重载
envoy_config_reload --cluster v86_gray --weight 10
```

---

## 8. 常见故障 FAQ

### Q1: 服务启动失败, 提示 "Missing dependency"?

**A**: 依赖未安装或版本不兼容。
```bash
# 安装依赖
pip3 install -r startup/requirements.txt

# 检查版本
pip3 list | grep -E "uvicorn|fastapi|prometheus"

# 若镜像已构建, 检查 Dockerfile 层
docker run --rm v86-alias-engine:v86.0.0 pip3 list
```

### Q2: 冷启动超过 30 秒?

**A**: 检查引擎初始化耗时。
```bash
# 查看启动日志
kubectl logs -n dshe-v86 <pod-name> | grep "init"

# 若 > 30s, 可能是 CSV 解析问题
# 检查别名库文件大小
ls -lh /v85/indicator_alias_library.csv

# 检查磁盘 I/O
iostat -x 1
```

### Q3: 缓存命中率很低 (< 50%)?

**A**: 缓存未预热或缓存文件损坏。
```bash
# 预热缓存
python3 alias_engine_warmup_optimize.py --warmup
python3 alias_engine_warmup_optimize.py --verify

# 若预热后仍低, 检查缓存配置
cat /var/cache/v86-alias/cache_config.yaml

# 检查 LRU max_size 是否过小
# 默认 1024, 可调整至 2048
```

### Q4: 灰度放量后 PASS 率下降?

**A**: 检查灰度 vs 基线差异。
```bash
# 检查 PASS 率
curl -s http://v86-alias-engine:8081/metrics | grep alias_verdict_total

# 对比灰度 vs 基线
# 灰度 (f3+f4): PASS 96.40%
# 基线 (base): PASS 99.14%
# 差异 2.74pp 在 5pp 阈值内, 正常

# 若差异 > 5pp, 检查歧义率
curl -s http://v86-alias-engine:8081/metrics | grep alias_ambiguous_rate
```

### Q5: 如何确认 F4 抑制生效?

**A**: 检查 F4 抑制指标。
```bash
# F4 抑制计数
curl -s http://v86-alias-engine:8081/metrics | grep alias_f4_

# 输出:
# alias_f4_f4a_suppress_total 132
# alias_f4_f4b_suppress_total 46
# alias_f4_total_suppress_total 51

# 若 F4 抑制率异常 (> 10%), 降级至 L1
echo "DEGRADE_LEVEL=1" > /etc/v86/degrade_level
```

### Q6: 如何回退至 V85 基线?

**A**: L3 降级。
```bash
# 1. 切流量至 V85
envoy_config_reload --cluster v85_baseline --weight 100

# 2. 确认 V85 就绪
curl http://v85-alias-baseline:8080/healthz

# 3. 更新降级级别
echo "DEGRADE_LEVEL=3" > /etc/v86/degrade_level

# 4. (可选) 停止 V86 Pod
kubectl scale deployment -n dshe-v86 v86-alias-engine --replicas=0
```

### Q7: 如何确认别名库版本正确?

**A**: 检查缓存元数据。
```bash
# 查看缓存元数据
cat /var/cache/v86-alias/metadata.json | python3 -m json.tool

# 检查 source_md5
# 应与 MD5_CHECKSUM_LIST.md 中的别名库 MD5 一致
```

### Q8: 如何处理新增长尾歧义样本?

**A**: 人工复核。
```bash
# 1. 检查长尾歧义总数
curl -s http://v86-alias-engine:8081/metrics | grep alias_tail_ambiguous_total

# 2. 导出长尾歧义样本
python3 v86_alias_full_replay.py --export-tail-ambiguous

# 3. 人工复核后更新别名库
# (需要开发团队介入)
```

### Q9: 日志文件太大怎么办?

**A**: 检查日志级别和轮转。
```bash
# 检查日志大小
du -sh /var/log/v86-alias/

# 清理历史日志
find /var/log/v86-alias/ -name "engine_*.log" -mtime +7 -delete

# 调整日志级别 (减少输出)
export V86_LOG_LEVEL=WARNING
```

### Q10: 如何验证降级控制器正常工作?

**A**: 检查降级审计日志。
```bash
# 查看降级历史
tail -100 /var/log/v86-alias/degrade_audit.log

# 验证降级控制器进程
ps aux | grep degrade_controller

# 手动触发降级检查
python3 alias_degrade_controller.py --check-now
```

---

## 9. 告警处置手册

### 9.1 P0-Critical 告警

#### Alert: AliasEngineHighErrorRate (错误率 > 0.1%)

**处置步骤**:
1. 检查错误码分布:
   ```bash
   curl -s http://v86-alias-engine:8081/metrics | grep alias_error_total
   ```
2. 检查日志:
   ```bash
   kubectl logs -n dshe-v86 <pod-name> --tail=50 | grep ERROR
   ```
3. 执行 L1 降级:
   ```bash
   echo "DEGRADE_LEVEL=1" > /etc/v86/degrade_level
   ```
4. 监控恢复, 若 10 分钟后错误率 ≤ 0.05%, 恢复 L0:
   ```bash
   echo "DEGRADE_LEVEL=0" > /etc/v86/degrade_level
   ```
5. 若 L1 后仍不达标, 升级至 L2:
   ```bash
   echo "DEGRADE_LEVEL=2" > /etc/v86/degrade_level
   ```
6. 若 L2 后仍不达标, 升级至 L3 (V85 回退)

**预计恢复时间**: 5-15 分钟

#### Alert: AliasEngineHighAmbiguity (歧义率 > 5%)

**处置步骤**:
1. 检查歧义率:
   ```bash
   curl -s http://v86-alias-engine:8081/metrics | grep alias_ambiguous_rate
   ```
2. 执行 L2 降级:
   ```bash
   echo "DEGRADE_LEVEL=2" > /etc/v86/degrade_level
   ```
3. 等待 30 分钟, 确认歧义率 ≤ 3%
4. 恢复 L0:
   ```bash
   echo "DEGRADE_LEVEL=0" > /etc/v86/degrade_level
   ```

**预计恢复时间**: 10-40 分钟

#### Alert: AliasEngineDown (Pod 不健康)

**处置步骤**:
1. 检查 Pod 状态:
   ```bash
   kubectl get pods -n dshe-v86 -l app=v86-alias-engine
   kubectl describe pod -n dshe-v86 <pod-name>
   ```
2. 检查日志:
   ```bash
   kubectl logs -n dshe-v86 <pod-name> --previous --tail=100
   ```
3. 若 CrashLoopBackOff, 检查退出码:
   - Exit Code 137 = OOM → 增加内存
   - Exit Code 1 = 应用错误 → 检查日志
4. 若 V86 无法恢复, 切流量至 V85:
   ```bash
   envoy_config_reload --cluster v85_baseline --weight 100
   echo "DEGRADE_LEVEL=3" > /etc/v86/degrade_level
   ```
5. 修复后恢复:
   ```bash
   kubectl scale deployment -n dshe-v86 v86-alias-engine --replicas=2
   kubectl rollout status deployment/v86-alias-engine -n dshe-v86
   python3 alias_engine_warmup_optimize.py --warmup
   envoy_config_reload --cluster v86-alias --weight 100
   echo "DEGRADE_LEVEL=0" > /etc/v86/degrade_level
   ```

**预计恢复时间**: 5-30 分钟

### 9.2 P1-Warning 告警

#### Alert: AliasEngineLowCacheHitRate (缓存命中率 < 85%)

**处置步骤**:
1. 检查缓存状态:
   ```bash
   curl -s http://v86-alias-engine:8081/metrics | grep alias_cache
   ```
2. 检查缓存文件:
   ```bash
   kubectl exec -n dshe-v86 <pod-name> -- ls -la /var/cache/v86-alias/
   ```
3. 手动预热:
   ```bash
   python3 alias_engine_warmup_optimize.py --warmup
   ```
4. 若仍低, 检查 max_size 配置:
   ```yaml
   cache:
     lru:
       max_size: 2048  # 增大缓存
   ```
5. 重载配置:
   ```bash
   kill -HUP $(cat /var/run/v86-alias.pid)
   ```

**预计恢复时间**: 5-15 分钟

#### Alert: AliasEngineHighLatency (P99 > 50ms)

**处置步骤**:
1. 检查负载:
   ```bash
   curl -s http://v86-alias-engine:8081/metrics | grep alias_resolve_total
   ```
2. 检查引擎模式:
   ```bash
   curl -s http://v86-alias-engine:8080/healthz | python3 -c "
   import sys,json; d=json.load(sys.stdin); print(d['engine']['mode'])
   "
   ```
3. 若 > 2000 QPS, 扩容:
   ```bash
   kubectl scale deployment -n dshe-v86 v86-alias-engine --replicas=4
   ```
4. 若缓存命中率低, 预热缓存

**预计恢复时间**: 5-10 分钟

### 9.3 P2-Info 告警

#### Alert: AliasEngineHighF4Suppress (F4 抑制率 > 10%)

**处置步骤**:
1. 检查 F4 抑制指标:
   ```bash
   curl -s http://v86-alias-engine:8081/metrics | grep alias_f4
   ```
2. 监控, 非紧急
3. 若抑制率持续 > 10%, 考虑降级至 L1

**预计恢复时间**: 监控观察

#### Alert: AliasEngineNewTailAmbiguous (新增长尾歧义)

**处置步骤**:
1. 导出长尾歧义样本:
   ```bash
   python3 v86_alias_full_replay.py --export-tail-ambiguous
   ```
2. 通知开发团队人工复核
3. 更新别名库 (需开发介入)

**预计恢复时间**: 人工复核, 1-2 天

---

## 10. 日志关键字速查

### 10.1 关键日志事件

| 日志关键字 | 含义 | 严重级别 |
|------------|------|----------|
| `Shutting down` | 优雅退出开始 | INFO |
| `Shutdown complete` | 优雅退出完成 | INFO |
| `Warmup completed` | 预热完成 | INFO |
| `Warmup verification` | 预热验证 | INFO |
| `Cache persisted` | 缓存持久化 | INFO |
| `Cache loaded` | 缓存加载 | INFO |
| `Cache miss` | 缓存未命中 | DEBUG |
| `Cache hit` | 缓存命中 | DEBUG |
| `DEGRADE: L0 -> L1` | 降级至 L1 | WARN |
| `DEGRADE: L1 -> L0` | 恢复至 L0 | INFO |
| `engine.mode changed` | 模式切换 | WARN |
| `resolve_timeout` | 解析超时 | ERROR |
| `engine_init_failed` | 引擎初始化失败 | CRITICAL |
| `engine_crash` | 引擎崩溃 | CRITICAL |
| `OOM` | 内存溢出 | CRITICAL |
| `Traceback` | 异常堆栈 | ERROR |
| `KeyError` | 键错误 (F1 兜底) | WARN |
| `AMBIGUOUS` | 歧义解析 | WARN |
| `UNREGISTERED` | 未注册别名 | WARN |
| `BLACKLIST` | 黑名单阻断 | INFO |
| `f4_suppressed` | F4 抑制 | DEBUG |

### 10.2 常用日志查询

```bash
# 查看降级事件
kubectl logs -n dshe-v86 <pod-name> | grep "DEGRADE"

# 查看错误
kubectl logs -n dshe-v86 <pod-name> | grep -i "ERROR\|CRITICAL"

# 查看异常堆栈
kubectl logs -n dshe-v86 <pod-name> | grep -A 10 "Traceback"

# 查看缓存事件
kubectl logs -n dshe-v86 <pod-name> | grep -i "cache"

# 查看性能问题
kubectl logs -n dshe-v86 <pod-name> | grep -i "timeout\|slow\|latency"

# 查看 F4 抑制
kubectl logs -n dshe-v86 <pod-name> | grep "f4_suppressed"

# 查看预热
kubectl logs -n dshe-v86 <pod-name> | grep "warmup"

# 查看最近 50 行
kubectl logs -n dshe-v86 <pod-name> --tail=50

# 实时跟踪
kubectl logs -n dshe-v86 <pod-name> -f
```

---

## 11. 日常运维检查表

### 11.1 每日检查 (10 分钟)

- [ ] 健康检查: `curl http://v86-alias-engine:8080/healthz`
- [ ] 降级级别: `cat /etc/v86/degrade_level`
- [ ] 错误率: 查看 Grafana 仪表盘, < 0.1%
- [ ] PASS 率: 查看 Grafana 仪表盘, ≥ 95%
- [ ] 缓存命中率: 查看 Grafana 仪表盘, ≥ 85%
- [ ] Pod 状态: `kubectl get pods -n dshe-v86`
- [ ] 告警通知: 检查 PagerDuty/Slack 是否有未处理告警

### 11.2 每周检查 (30 分钟)

- [ ] 磁盘空间: `df -h /var/cache/v86-alias/`
- [ ] 缓存文件: `ls -lh /var/cache/v86-alias/`
- [ ] 缓存元数据: `cat /var/cache/v86-alias/metadata.json`
- [ ] 降级审计日志: `tail -100 /var/log/v86-alias/degrade_audit.log`
- [ ] 日志轮转: 清理 7 天前日志
- [ ] 全量回放: `python3 v86_alias_full_replay.py`
- [ ] 门禁校验: `python3 alias_gate_auto_check.py --all`

### 11.3 每月检查 (60 分钟)

- [ ] 冒烟测试: `python3 v86_alias_engine_prototype.py --smoke`
- [ ] 回归测试: 165 样本回归
- [ ] 预热性能: `python3 alias_engine_warmup_optimize.py --benchmark`
- [ ] 降级演练: L1/L2/L3 各一次
- [ ] 引擎崩溃恢复演练
- [ ] Envoy 流量切换演练
- [ ] 容量规划: QPS/内存/CPU/磁盘
- [ ] 告警规则验证
- [ ] 备份验证: 缓存文件 + 配置备份

### 11.4 每次部署后检查 (15 分钟)

- [ ] 健康检查通过
- [ ] 降级级别 = 0
- [ ] 缓存预热完成
- [ ] 14 道门禁全部 PASS
- [ ] 监控仪表盘正常
- [ ] 告警规则生效
- [ ] 回退方案就绪

---

## 12. 约束合规

| 约束 | 状态 |
|------|------|
| NO_ZHIJI_API_CALL=TRUE | ✅ 运维手册不含外部 API 调用 |
| NO_MODIFY_SOURCE_TEMPLATE=TRUE | ✅ 仅文档, 不修改代码 |
| NO_MODIFY_V85_FROZEN_FILES=TRUE | ✅ V85 文件未修改 |
| 不覆盖已有交付物 | ✅ 独立输出目录 `dshe_alias_ops_final/` |
| 分支锁定 feature/v85-chart-template | ✅ 未合并 main |

---

*运维手册由 DSHE_V86_ALIAS_PROD_INTEGRATE_ADAPT_GRAY_SIMULATION_AND_OPS_MANUAL_FINAL T2.3 生成*
*分支: feature/v85-chart-template · Commit: 81268a6*
*版本: v1.0-final · 适用角色: 一线运维 / SRE / 值班工程师*
