# V86 别名引擎生产部署包

> 任务: `DSHE_V86_ALIAS_ENGINE_FULL_REPLAY_AND_GRAY_RELEASE_PLAN` · T2.2
> 分支: `feature/v85-chart-template`
> 引擎版本: `V86AliasEngine v1.0` · 模式 `f3+f4`

---

## 1. 部署包总览

### 1.1 文件清单

```
dshe_alias_prod_prep/
├── v86_alias_full_replay.py          # 全量回放脚本
├── v86_alias_full_replay_report.md    # 全量回放报告
├── replay_results.json                # 回放结果数据
├── v86_alias_production_bundle.md     # 本文件: 生产部署包说明
├── v86_alias_gray_release_plan.md     # 灰度上线方案
├── v86_alias_degrade_plan.md          # 故障降级预案
├── v86_alias_monitor_spec.md          # 监控指标规范
├── MD5_CHECKSUM_LIST.md               # MD5 校验清单
├── startup/
│   ├── start_alias_engine.sh          # 生产启动脚本
│   ├── requirements.txt               # 依赖清单
│   └── cache_config.yaml              # 缓存配置模板
└── deploy/
    ├── Dockerfile                     # 容器镜像构建
    ├── docker-compose.yaml            # 本地编排
    └── k8s-deployment.yaml            # K8s 部署模板
```

### 1.2 生产保留组件

| 组件 | 源文件 | 说明 | 保留 |
|---|---|---|---|
| 引擎核心 | `v86_alias_engine_prototype.py` | V86AliasEngine 类 | ✅ 保留 |
| 预热缓存 | `alias_engine_warmup_optimize.py` | 单例+LRU缓存 | ✅ 保留 |
| 门禁脚本 | `alias_gate_auto_check.py` | 14 道门禁 | ✅ 保留 |
| 任务适配器 | `alias_task_adapter.py` | 后端异步任务 API | ✅ 保留 |
| 全量回放 | `v86_alias_full_replay.py` | 4643 条回放 | ✅ 保留 |
| 启动脚本 | `startup/start_alias_engine.sh` | 生产启动 | ✅ 新增 |
| 依赖清单 | `startup/requirements.txt` | Python 依赖 | ✅ 新增 |
| 缓存配置 | `startup/cache_config.yaml` | 缓存持久化配置 | ✅ 新增 |
| 灰度方案 | `v86_alias_gray_release_plan.md` | 灰度上线方案 | ✅ 新增 |
| 降级预案 | `v86_alias_degrade_plan.md` | 故障降级方案 | ✅ 新增 |
| 监控规范 | `v86_alias_monitor_spec.md` | 监控指标规范 | ✅ 新增 |

### 1.3 调试代码剔除

| 代码 | 剔除 | 理由 |
|---|---|---|
| `--smoke` CLI 参数 | ✅ 保留 | 冒烟测试仍需要 |
| `--regression` CLI 参数 | ✅ 保留 | 回归测试仍需要 |
| `--run-tests` CLI 参数 | ✅ 保留 | 测试用例仍需要 |
| 调试打印 (print) | ❌ 保留 | 生产日志替代 |
| 临时测试文件 | ✅ 已剔除 | 仅保留正式交付物 |
| `__pycache__/` | ✅ 已剔除 | 构建时重新生成 |
| `.pyc` 文件 | ✅ 已剔除 | 构建时重新生成 |

---

## 2. 生产启动脚本

### 2.1 `startup/start_alias_engine.sh`

```bash
#!/bin/bash
# V86 Alias Engine - Production Startup Script
# Task: DSHE_V86_ALIAS_ENGINE_FULL_REPLAY_AND_GRAY_RELEASE_PLAN · T2.2

set -euo pipefail

# ---- Configuration ----
ENGINE_MODE="${V86_ALIAS_MODE:-f3+f4}"
INIT_TIMEOUT="${V86_INIT_TIMEOUT:-60}"
WARMUP="${V86_WARMUP:-true}"
HEALTH_PORT="${V86_HEALTH_PORT:-8080}"
METRICS_PORT="${V86_METRICS_PORT:-8081}"
CACHE_DIR="${V86_CACHE_DIR:-/var/cache/v86-alias}"
LOG_DIR="${V86_LOG_DIR:-/var/log/v86-alias}"
PID_FILE="/var/run/v86-alias.pid"

# ---- Path Resolution ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(cd "$ENGINE_DIR/../.." && pwd)"

# ---- Logging ----
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/engine_$(date +%Y%m%d).log"

log() {
    local level="$1"; shift
    local msg="[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [$level] $*"
    echo "$msg" | tee -a "$LOG_FILE"
}

# ---- Pre-flight Checks ----
preflight() {
    log INFO "=== V86 Alias Engine Startup ==="
    log INFO "Mode: $ENGINE_MODE"
    log INFO "Repo: $REPO_ROOT"
    
    # Check Python
    if ! command -v python3 &>/dev/null; then
        log ERROR "python3 not found"
        exit 1
    fi
    
    # Check disk space
    local cache_gb
    cache_gb=$(df -BG "$CACHE_DIR" 2>/dev/null | awk 'NR==2{print $4}' | tr -d 'G' || echo "10")
    if [ "$cache_gb" -lt 1 ]; then
        log WARN "Cache dir low disk space: ${cache_gb}GB"
    fi
    
    # Check dependencies
    local missing_deps=0
    while IFS= read -r dep; do
        dep_clean=$(echo "$dep" | tr -d '[:space:]' | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1)
        if [ -n "$dep_clean" ] && ! python3 -c "import $dep_clean" 2>/dev/null; then
            log ERROR "Missing dependency: $dep"
            missing_deps=1
        fi
    done < "$ENGINE_DIR/requirements.txt"
    if [ "$missing_deps" -eq 1 ]; then
        log ERROR "Install missing dependencies: pip3 install -r $ENGINE_DIR/requirements.txt"
        exit 1
    fi
    
    log INFO "Pre-flight checks passed"
}

# ---- Engine Warmup ----
warmup_engine() {
    if [ "$WARMUP" != "true" ]; then
        log INFO "Warmup skipped (V86_WARMUP=$WARMUP)"
        return
    fi
    
    log INFO "Starting engine warmup..."
    local warmup_script="$ENGINE_DIR/alias_engine_warmup_optimize.py"
    if [ -f "$warmup_script" ]; then
        local t0=$(date +%s%3N)
        python3 "$warmup_script" --warmup 2>&1 | while read line; do
            log INFO "  $line"
        done
        local t1=$(date +%s%3N)
        log INFO "Warmup completed in $((t1 - t0))ms"
        
        # Verify warmup
        python3 "$warmup_script" --verify 2>&1 | while read line; do
            log INFO "  $line"
        done
    else
        log WARN "Warmup script not found, skipping"
    fi
}

# ---- Health Check ----
healthcheck() {
    log INFO "Starting health check on port $HEALTH_PORT..."
    local retries=30
    local delay=2
    
    while [ $retries -gt 0 ]; do
        if curl -s "http://localhost:$HEALTH_PORT/healthz" | grep -q '"healthy"'; then
            log INFO "Health check passed"
            return 0
        fi
        retries=$((retries - 1))
        sleep $delay
    done
    
    log ERROR "Health check failed after $((30 * 2))s"
    return 1
}

# ---- Main ----
main() {
    preflight
    
    # Set environment
    export V86_ALIAS_MODE="$ENGINE_MODE"
    export V86_CACHE_DIR="$CACHE_DIR"
    
    # Run warmup
    warmup_engine
    
    # Start engine (foreground)
    log INFO "Starting V86 Alias Engine (mode=$ENGINE_MODE)..."
    cd "$REPO_ROOT"
    exec python3 -m uvicorn v86_alias_service:app \
        --host 0.0.0.0 \
        --port "$HEALTH_PORT" \
        --metrics-port "$METRICS_PORT" \
        --log-level info \
        2>&1 | tee -a "$LOG_FILE"
}

# ---- Signal Handling ----
cleanup() {
    log INFO "Shutting down V86 Alias Engine..."
    # Persist cache
    python3 "$ENGINE_DIR/alias_engine_warmup_optimize.py" --save-cache 2>/dev/null || true
    log INFO "Shutdown complete"
    exit 0
}

trap cleanup SIGTERM SIGINT

main "$@"
```

---

## 3. 依赖清单

### 3.1 `startup/requirements.txt`

```
# V86 Alias Engine - Production Dependencies
# Python >= 3.8

# Core (standard library, no external deps)
# The alias engine uses only Python standard library modules:
#   os, sys, json, time, datetime, hashlib, csv
#   collections, copy, pickle, tempfile, argparse
#   subprocess (for gate checks)

# Web framework (for health check & API service)
uvicorn>=0.23.0
fastapi>=0.100.0

# Metrics
prometheus-client>=0.17.0

# Cache persistence
# Uses Python pickle (standard library)
# No external cache library required

# Testing (dev only, not in production)
# pytest>=7.0.0  # commented out for production

# Optional: OpenTelemetry tracing
# opentelemetry-sdk>=1.19.0  # uncomment for tracing support
```

### 3.2 Python 标准库依赖

```
os
sys
json
time
datetime
hashlib
csv
collections
copy
pickle
tempfile
argparse
subprocess
```

### 3.3 外部依赖

| 包 | 版本 | 用途 | 生产必需 |
|---|---|---|---|
| `uvicorn` | ≥ 0.23.0 | ASGI Web Server | ✅ |
| `fastapi` | ≥ 0.100.0 | API Framework | ✅ |
| `prometheus-client` | ≥ 0.17.0 | Metrics Export | ✅ |

---

## 4. 缓存配置模板

### 4.1 `startup/cache_config.yaml`

```yaml
# V86 Alias Engine - Cache Configuration
# Task: DSHE_V86_ALIAS_ENGINE_FULL_REPLAY_AND_GRAY_RELEASE_PLAN · T2.2

cache:
  # LRU Cache
  lru:
    max_size: 1024              # Max entries in memory cache
    evict_policy: "lru"         # lru | fifo | lfu
    persist_path: "/var/cache/v86-alias/resolve_cache.pkl"
    persist_interval_seconds: 300  # Persist every 5 minutes
    persist_on_shutdown: true     # Persist when engine stops
    
  # Warmup
  warmup:
    enabled: true
    samples:
      # Common variety aliases
      - "碳酸锂工厂库存天数"
      - "电解铜库存"
      - "锌锭库存"
      - "锡锭库存"
      - "铅锭库存"
      - "工业铝库存"
      # Cross-variety aliases
      - "GFEX：工业硅：主力合约：收盘价（日）"
      - "SHFE：沪铜：主力合约：收盘价（日）"
      # Boundary cases
      - "碳酸锂利润与需求分析"
      - "锡厂库存天数（天）"
    verify_after_warmup: true
    fail_on_warmup_error: false
    
  # Cache Directory
  directory: "/var/cache/v86-alias"
  max_size_mb: 50
  cleanup_interval_hours: 24
  keep_last_n_files: 7

# Metrics
metrics:
  cache_hit_rate_threshold: 0.85
  cache_hit_rate_alert: 0.5
  cache_size_alert: 800
  cache_miss_alert_rate: 0.3

# Persistence
persistence:
  enabled: true
  format: "pickle"
  compression: false
  atomic_write: true
  backup_on_write: true
```

### 4.2 缓存目录结构

```
/var/cache/v86-alias/
├── resolve_cache.pkl              # 当前缓存 (LRU 1024 entries)
├── resolve_cache_20261002_000000.pkl  # 历史备份
├── resolve_cache_20261001_235500.pkl  # 历史备份
├── resolve_cache_20261001_235000.pkl  # 历史备份
└── metadata.json                  # 缓存元数据
```

### 4.3 缓存元数据

```json
{
  "engine_version": "v86.0.0",
  "mode": "f3+f4",
  "entries": 956,
  "max_size": 1024,
  "created_at": "2026-10-02T00:00:00Z",
  "updated_at": "2026-10-02T00:05:00Z",
  "hit_rate": 0.99,
  "source_md5": "E77C8E3692235F1CCE83076920F118C9",
  "checksum": "sha256:abc123..."
}
```

---

## 5. 容器化部署

### 5.1 `deploy/Dockerfile`

```dockerfile
# V86 Alias Engine - Production Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY startup/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY v86_alias_engine_prototype.py .
COPY alias_task_adapter.py .
COPY alias_engine_warmup_optimize.py .
COPY alias_gate_auto_check.py .
COPY v86_alias_full_replay.py .

# Copy V85 dependencies (read-only)
COPY --from=v85-base /v85/ /v85/

# Create cache directory
RUN mkdir -p /var/cache/v86-alias /var/log/v86-alias

# Copy startup script
COPY startup/start_alias_engine.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/start_alias_engine.sh

# Environment defaults
ENV V86_ALIAS_MODE=f3+f4
ENV V86_CACHE_DIR=/var/cache/v86-alias
ENV V86_LOG_DIR=/var/log/v86-alias
ENV V86_HEALTH_PORT=8080
ENV V86_METRICS_PORT=8081

# Health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=5 \
  CMD curl -f http://localhost:8080/healthz || exit 1

# Run startup script
ENTRYPOINT ["/usr/local/bin/start_alias_engine.sh"]
```

### 5.2 `deploy/docker-compose.yaml`

```yaml
version: '3.8'

services:
  v86-alias-engine:
    build:
      context: ..
      dockerfile: deploy/Dockerfile
    ports:
      - "8080:8080"   # Health check + API
      - "8081:8081"   # Metrics
    environment:
      - V86_ALIAS_MODE=f3+f4
      - V86_WARMUP=true
      - V86_CACHE_DIR=/var/cache/v86-alias
    volumes:
      - alias_cache:/var/cache/v86-alias
      - alias_logs:/var/log/v86-alias
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/healthz"]
      interval: 15s
      timeout: 5s
      start_period: 60s
      retries: 5
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
        reservations:
          memory: 128M
          cpus: '0.25'

  v86-alias-legacy:
    # V85 baseline engine for fallback
    build:
      context: ..
      dockerfile: deploy/Dockerfile.v85
    ports:
      - "8082:8080"
    environment:
      - V86_ALIAS_MODE=base
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/healthz"]
      interval: 15s
      timeout: 5s
      start_period: 60s
      retries: 5
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.5'

volumes:
  alias_cache:
    driver: local
  alias_logs:
    driver: local
```

### 5.3 `deploy/k8s-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metaData:
  name: v86-alias-engine
  labels:
    app: v86-alias-engine
    version: v86.0.0
spec:
  replicas: 2
  selector:
    matchLabels:
      app: v86-alias-engine
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metaData:
      labels:
        app: v86-alias-engine
    spec:
      containers:
        - name: v86-alias
          image: registry.local/v86-alias-engine:v86.0.0
          ports:
            - containerPort: 8080
              name: http
            - containerPort: 8081
              name: metrics
          env:
            - name: V86_ALIAS_MODE
              value: "f3+f4"
            - name: V86_WARMUP
              value: "true"
          resources:
            requests:
              memory: "128Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "1000m"
          readinessProbe:
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 60
            periodSeconds: 15
            timeoutSeconds: 5
            failureThreshold: 3
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 90
            periodSeconds: 30
            timeoutSeconds: 5
            failureThreshold: 3
          volumeMounts:
            - name: cache
              mountPath: /var/cache/v86-alias
            - name: logs
              mountPath: /var/log/v86-alias
      volumes:
        - name: cache
          persistentVolumeClaim:
            claimName: v86-alias-cache-pvc
        - name: logs
          emptyDir:
            sizeLimit: 1Gi
```

---

## 6. 部署流程

### 6.1 本地部署

```bash
# 1. 安装依赖
pip3 install -r startup/requirements.txt

# 2. 设置环境变量
export V86_ALIAS_MODE="f3+f4"
export V86_CACHE_DIR="/tmp/v86-alias-cache"

# 3. 运行预热
python3 alias_engine_warmup_optimize.py --warmup

# 4. 验证预热
python3 alias_engine_warmup_optimize.py --verify

# 5. 运行启动脚本
./startup/start_alias_engine.sh

# 6. 验证健康检查
curl http://localhost:8080/healthz

# 7. 验证指标
curl http://localhost:8081/metrics | grep alias_resolve
```

### 6.2 Docker 部署

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
```

### 6.3 Docker Compose 部署

```bash
# 1. 启动全部服务
docker compose -f deploy/docker-compose.yaml up -d

# 2. 查看状态
docker compose -f deploy/docker-compose.yaml ps

# 3. 验证
curl http://localhost:8080/healthz    # V86 engine
curl http://localhost:8082/healthz    # V85 fallback

# 4. 停止
docker compose -f deploy/docker-compose.yaml down
```

### 6.4 Kubernetes 部署

```bash
# 1. 创建 PVC (缓存持久化)
kubectl apply -f deploy/pvc.yaml

# 2. 部署引擎
kubectl apply -f deploy/k8s-deployment.yaml

# 3. 创建 Service
kubectl apply -f deploy/service.yaml

# 4. 查看状态
kubectl get pods -l app=v86-alias-engine

# 5. 验证
kubectl port-forward pod/v86-alias-xxx 8080:8080
curl http://localhost:8080/healthz
```

---

## 7. 生产配置检查清单

### 7.1 部署前

- [ ] Python 3.8+ 已安装
- [ ] 依赖已安装 (`pip install -r requirements.txt`)
- [ ] 缓存目录已创建 (`/var/cache/v86-alias`)
- [ ] 日志目录已创建 (`/var/log/v86-alias`)
- [ ] 环境变量已设置 (`V86_ALIAS_MODE`, `V86_CACHE_DIR`)
- [ ] 冒烟测试通过 (`python v86_alias_engine_prototype.py --smoke`)
- [ ] 14 道门禁全部 PASS (`python alias_gate_auto_check.py --all`)
- [ ] 全量回放完成 (4643 条无异常)

### 7.2 部署中

- [ ] 引擎冷启动 ≤ 30s
- [ ] 预热完成 (18 样本)
- [ ] 首次请求 ≤ 50ms
- [ ] 健康检查端点正常
- [ ] Metrics 端点正常
- [ ] 缓存持久化正常

### 7.3 部署后

- [ ] 灰度 10% 流量, 门禁全部 PASS
- [ ] 灰度 30% 流量, 门禁全部 PASS
- [ ] 100% 流量切换
- [ ] 监控仪表盘就绪
- [ ] 告警规则已配置
- [ ] 降级预案已验证

---

## 8. 约束合规

| 约束 | 状态 |
|---|---|
| 不调用 zhiji API | ✅ TRUE |
| 不修改 V85 冻结数据 | ✅ TRUE |
| 不覆盖 V85 交付物 | ✅ TRUE |
| 分支锁定 feature/v85-chart-template | ✅ TRUE |
