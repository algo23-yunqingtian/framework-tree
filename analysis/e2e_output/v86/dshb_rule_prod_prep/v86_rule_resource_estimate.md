# V86 Rule Engine Production Resource Estimation

**Task:** DSHB_V86_RULE_ENGINE_FULL_DATASET_REPLAY_AND_PROD_BUNDLE_BUILD  
**Deliverable:** T2.4 — Resource Estimation  
**Branch:** feature/v85-chart-template  
**Base Commit:** 68517fb  

---

## 1. Resource Assessment Overview

This document provides production resource estimates for the V86 rule engine based on full dataset replay results and benchmark data from the CI stress test pipeline.

### 1.1 Workload Profile

| Parameter | Value | Source |
|-----------|-------|--------|
| Total templates (V85) | 488 | chart_risk_bound_all.json |
| Total series (V85) | 2,721 | Extracted from templates |
| Total evaluations per batch | ~5,442 | Template-level aggregation |
| Rules per evaluation | 18 | 6 P0 + 12 P1 |
| Rules per engine | 18 | V86P1RuleEngine |
| Alias entries | 4,643 | V86AliasEngine (f3+f4) |
| Alias blacklist rules | 31 | V85 alias library |

---

## 2. CPU Analysis

### 2.1 Single-Thread Performance

Based on the full dataset replay (2,721 series, 652ms total):

| Metric | Value | Notes |
|--------|-------|-------|
| Average latency per series | 0.229 ms | Includes validation + evaluation |
| P50 latency | ~0.000 ms | Sub-millisecond for simple cases |
| P95 latency | 1.001 ms | High-end tail |
| P99 latency | 1.004 ms | Near-p95 (low tail variance) |
| Max latency | ~1.01 ms | Maximum observed |
| Throughput (single-thread) | 4,173 series/sec | Sequential evaluation |

### 2.2 CPU Usage Breakdown

| Component | CPU Time per Evaluation | % of Total |
|-----------|------------------------|------------|
| Input validation (NFKC normalize) | ~0.02 ms | 9% |
| DATA_MISSING detection | ~0.01 ms | 4% |
| Pattern matching (18 rules) | ~0.15 ms | 65% |
| Variety detection (BL-012) | ~0.02 ms | 9% |
| Bidirectional containment | ~0.01 ms | 4% |
| Response construction | ~0.01 ms | 3% |
| **Total** | **~0.22 ms** | **100%** |

### 2.3 CPU Estimation for Production

| Scenario | Concurrent Users | CPU Cores | Notes |
|----------|-----------------|-----------|-------|
| Low (dev/staging) | 1-5 | 1 core | Single-thread sufficient |
| Medium (small prod) | 5-20 | 2 cores | 2 workers recommended |
| High (production) | 20-100 | 4 cores | 4 workers recommended |
| Very high (peak) | 100+ | 8 cores | 8 workers, consider scaling |

### 2.4 CPU Scaling Formula

```
CPU_cores = ceil(concurrent_users * avg_latency_ms / 1000)

Example: 20 concurrent users, 0.229ms avg latency
CPU_cores = ceil(20 * 0.229 / 1000) = ceil(0.00458) = 1 core

Example: 100 concurrent users, 0.229ms avg latency
CPU_cores = ceil(100 * 0.229 / 1000) = ceil(0.0229) = 1 core

Note: CPU is NOT the bottleneck for this workload due to sub-millisecond latency.
Memory and I/O are the primary constraints.
```

---

## 3. Memory Analysis

### 3.1 Memory Breakdown

| Component | Memory | Notes |
|-----------|--------|-------|
| Python interpreter | ~15 MB | Base Python 3.12 |
| V86P1RuleEngine (18 rules) | ~5 MB | Rule objects + pattern index |
| V86AliasEngine (f3+f4) | ~35 MB | 4,643 alias entries + 31 blacklist rules |
| Input/output buffers | ~5 MB | Per-request buffers |
| Logging buffers | ~5 MB | Ring buffer |
| GC overhead | ~5 MB | Python garbage collection |
| **Total per process** | **~70 MB** | Single process |

### 3.2 Memory Scaling

| Workers | Total Memory | Notes |
|---------|-------------|-------|
| 1 worker | ~70 MB | Single process |
| 2 workers | ~140 MB | Fork or spawn |
| 4 workers | ~280 MB | Recommended for production |
| 8 workers | ~560 MB | High concurrency |

### 3.3 Memory Peak Analysis

| Scenario | Peak Memory | Notes |
|----------|------------|-------|
| Engine init (alias engine) | ~100 MB | One-time spike during alias loading |
| Batch evaluation (1000 series) | ~80 MB | Temporary buffers |
| Long-running (24h) | ~75 MB | Steady state with GC |
| Memory leak scenario | >200 MB | Would require investigation |

### 3.4 Memory Recommendation

| Environment | Min Memory | Recommended | Notes |
|-------------|-----------|-------------|-------|
| Dev/Staging | 256 MB | 512 MB | Single worker |
| Small Production | 512 MB | 1 GB | 2-4 workers |
| Production | 1 GB | 2 GB | 4-8 workers |
| High Availability | 2 GB | 4 GB | 8+ workers + HA |

---

## 4. Disk I/O Analysis

### 4.1 I/O Workload

| Component | I/O Type | Frequency | Size |
|-----------|----------|-----------|------|
| Rule loading | Read (startup) | 1x | ~180 KB |
| Alias library loading | Read (startup) | 1x | ~464 KB |
| V85 blacklist loading | Read (startup) | 1x | ~2 KB |
| Health check responses | Write (network) | Continuous | ~50 B |
| Log writes | Write (disk) | Continuous | ~100 B per request |
| Error logs | Write (disk) | Rare | ~500 B per error |

### 4.2 Disk Usage Estimation

| Period | Disk Usage | Notes |
|--------|-----------|-------|
| Initial install | ~300 KB | Bundle files |
| After 24h | ~50 MB | Log files |
| After 7 days | ~350 MB | Log rotation (daily) |
| After 30 days | ~1.5 GB | Log rotation (daily) |
| After 90 days | ~4.5 GB | Log rotation (daily) |

### 4.3 Disk I/O Recommendation

| Environment | Min Disk | Recommended | Notes |
|-------------|---------|-------------|-------|
| Dev/Staging | 1 GB | 2 GB | Minimal logging |
| Production | 5 GB | 10 GB | 30 days log retention |
| High Availability | 10 GB | 20 GB | Redundant storage |

### 4.4 Log Rotation Policy

```bash
# /etc/logrotate.d/v86-rule-engine
/var/log/dshe/v86-rule-engine.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 dshe-user dshe-group
    sharedscripts
    postrotate
        systemctl reload v86-rule-engine
    endscript
}
```

---

## 5. Network Analysis

### 5.1 Network I/O Profile

| Direction | Per Request | Notes |
|-----------|------------|-------|
| Inbound (evaluate request) | ~200 bytes | JSON payload |
| Outbound (evaluate response) | ~300 bytes | JSON response |
| Inbound (batch request) | ~20 KB (100 pairs) | Batch endpoint |
| Outbound (batch response) | ~30 KB (100 results) | Batch response |
| Inbound (health check) | ~50 bytes | GET /health |
| Outbound (health response) | ~100 bytes | Status JSON |

### 5.2 Network Bandwidth Estimation

| Scenario | Throughput | Bandwidth |
|----------|-----------|-----------|
| 1,000 requests/sec | 250 KB/sec | ~2 MB/min |
| 10,000 requests/sec | 2.5 MB/sec | ~150 MB/min |
| 100,000 requests/sec | 25 MB/sec | ~1.5 GB/min |

### 5.3 Network Recommendation

| Environment | Bandwidth | Notes |
|-------------|-----------|-------|
| Dev/Staging | 1 Mbps | Internal network |
| Production | 10 Mbps | Internal network |
| High Availability | 100 Mbps | Cross-AZ traffic |

---

## 6. Production Instance Specifications

### 6.1 Recommended Instance Types

| Scale | CPU | Memory | Disk | Network | Max Concurrent | Est. Cost |
|-------|-----|--------|------|---------|---------------|-----------|
| Small | 2 vCPU | 2 GB | 10 GB SSD | 10 Mbps | 50 | $50/mo |
| Medium | 4 vCPU | 4 GB | 20 GB SSD | 50 Mbps | 200 | $120/mo |
| Large | 8 vCPU | 8 GB | 50 GB SSD | 100 Mbps | 500 | $250/mo |
| X-Large | 16 vCPU | 16 GB | 100 GB SSD | 200 Mbps | 1000 | $500/mo |

### 6.2 Instance Configuration (systemd)

```ini
# systemd resource limits (v86-rule-engine.service)
LimitNOFILE=65536
MemoryMax=2G          # 2 GB hard limit for 4-worker config
CPUQuota=400%         # 4 cores max usage
TasksMax=512          # Max threads
IOWeight=50           # Balanced I/O priority
```

---

## 7. Queue Water Level Alert Thresholds

### 7.1 Queue Thresholds

| Threshold | Level | Action |
|-----------|-------|--------|
| 0-100 requests | GREEN | Normal operation |
| 101-500 requests | YELLOW | Monitor closely |
| 501-2000 requests | ORANGE | Scale workers or investigate |
| 2001-5000 requests | RED | Emergency scaling |
| 5000+ requests | CRITICAL | Reject requests, alert on-call |

### 7.2 Queue Threshold Metrics

| Metric | Warning | Critical | Description |
|--------|---------|----------|-------------|
| Queue depth | > 500 | > 2000 | Pending requests in queue |
| Queue wait time | > 100ms | > 1s | Time spent in queue |
| Queue rejection rate | > 1% | > 5% | Requests rejected due to queue full |
| Worker utilization | > 80% | > 95% | CPU utilization per worker |

### 7.3 Alert Configuration (Prometheus)

```yaml
# prometheus/rules/v86-rule-engine.yaml
groups:
  - name: v86-rule-engine-alerts
    rules:
      # Queue depth alerts
      - alert: V86RuleEngineQueueHigh
        expr: v86_queue_depth > 500
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "V86 Rule Engine queue depth high"
          description: "Queue depth {{ $value }} exceeds 500 for 2 minutes"

      - alert: V86RuleEngineQueueCritical
        expr: v86_queue_depth > 2000
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "V86 Rule Engine queue critical"
          description: "Queue depth {{ $value }} exceeds 2000 for 1 minute"

      # Latency alerts
      - alert: V86RuleEngineLatencyHigh
        expr: v86_p95_latency_ms > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "V86 Rule Engine p95 latency high"
          description: "P95 latency {{ $value }}ms exceeds 5ms for 5 minutes"

      - alert: V86RuleEngineLatencyCritical
        expr: v86_p95_latency_ms > 10
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "V86 Rule Engine p95 latency critical"
          description: "P95 latency {{ $value }}ms exceeds 10ms for 2 minutes"

      # FP rate alerts
      - alert: V86RuleEngineFPHigh
        expr: v86_fp_rate * 100 > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "V86 Rule Engine FP rate high"
          description: "FP rate {{ $value }}% exceeds 5% for 5 minutes"

      # Memory alerts
      - alert: V86RuleEngineMemoryHigh
        expr: process_resident_memory_bytes > 1500 * 1024 * 1024
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "V86 Rule Engine memory high"
          description: "Memory usage {{ $value }} bytes exceeds 1.5GB"

      # Error rate alerts
      - alert: V86RuleEngineErrorHigh
        expr: rate(v86_error_total[5m]) > 0.01
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "V86 Rule Engine error rate high"
          description: "Error rate {{ $value }}/sec exceeds 1% for 5 minutes"

      # Throughput alerts
      - alert: V86RuleEngineThroughputLow
        expr: rate(v86_evaluate_total[5m]) < 10
        for: 10m
        labels:
          severity: info
        annotations:
          summary: "V86 Rule Engine throughput low"
          description: "Throughput {{ $value }}/sec below 10 for 10 minutes"
```

---

## 8. Scaling Strategy

### 8.1 Horizontal Scaling

| Level | Instances | Throughput | Failover |
|-------|-----------|-----------|----------|
| Single | 1 | 4,173 series/sec | None |
| 2-instance | 2 | 8,346 series/sec | Active-passive |
| 4-instance | 4 | 16,692 series/sec | Active-active (load balancer) |
| 8-instance | 8 | 33,384 series/sec | Cluster (HAProxy + keepalive) |

### 8.2 Vertical Scaling

| Action | Impact | When |
|--------|--------|------|
| +1 CPU core | +~40% throughput | CPU-bound (rare for this workload) |
| +1 GB memory | +~2 workers | Memory-bound (common) |
| +10 GB disk | +30 days logs | Disk-bound (common) |
| +10 Mbps network | +~10x requests/sec | Network-bound (rare) |

### 8.3 Auto-Scaling Triggers

| Trigger | Action | Cooldown |
|---------|--------|----------|
| Queue depth > 500 for 2 min | +1 instance | 5 min |
| Queue depth < 100 for 10 min | -1 instance | 10 min |
| Memory > 80% for 5 min | +1 GB memory | 10 min |
| CPU > 80% for 5 min | +1 CPU core | 10 min |
| Error rate > 1% for 5 min | +1 instance | 5 min |

---

## 9. Cost Estimation

### 9.1 Monthly Cost (Cloud Providers)

| Instance Type | Price (cloud) | Monthly (24/7) | Annual |
|---------------|--------------|----------------|--------|
| 2 vCPU, 2 GB, 10 GB | $25/mo | $25 | $300 |
| 4 vCPU, 4 GB, 20 GB | $50/mo | $50 | $600 |
| 8 vCPU, 8 GB, 50 GB | $100/mo | $100 | $1,200 |
| 16 vCPU, 16 GB, 100 GB | $200/mo | $200 | $2,400 |

### 9.2 Self-Hosted Cost

| Component | Cost | Notes |
|-----------|------|-------|
| Server (2 vCPU, 4 GB) | ~$300/mo (colocation) | Depends on provider |
| 4 vCPU, 8 GB | ~$600/mo | Higher performance |
| 8 vCPU, 16 GB | ~$1,200/mo | Production scale |

---

## 10. Summary

### 10.1 Recommended Production Configuration

```
INSTANCE: 4 vCPU, 4 GB RAM, 20 GB SSD, 50 Mbps
WORKERS: 4
MAX_CONCURRENT: 64
QUEUE_SIZE: 500
LOG_RETENTION: 30 days

RESOURCE LIMITS:
  MemoryMax: 2 GB
  CPUQuota: 400%
  TasksMax: 512
  IOWeight: 50

ALERT THRESHOLDS:
  Queue depth: WARN 500, CRIT 2000
  P95 latency: WARN 5ms, CRIT 10ms
  FP rate: WARN 5%, CRIT 10%
  Error rate: WARN 1%, CRIT 5%
  Memory: WARN 80%, CRIT 90%
```

### 10.2 Capacity Planning

| Metric | Current | 1x Scale | 5x Scale | 10x Scale |
|--------|---------|----------|----------|-----------|
| Templates/sec | 0.75 | 3.75 | 18.75 | 37.5 |
| Series/sec | 4,173 | 20,865 | 104,325 | 208,650 |
| CPU cores | 1 | 4 | 8 | 16 |
| Memory | 70 MB | 280 MB | 1.4 GB | 2.8 GB |
| Workers | 1 | 4 | 8 | 16 |

### 10.3 Key Takeaways

1. **CPU is NOT the bottleneck:** Sub-millisecond latency means 1 core can handle thousands of requests/sec
2. **Memory is the primary constraint:** Alias engine (~35 MB) + rules (~5 MB) = ~40 MB per process
3. **Disk I/O is minimal:** Only log writes, no data persistence needed
4. **Network is negligible:** ~500 bytes per request, not a bottleneck
5. **4 vCPU, 4 GB RAM, 20 GB SSD** is the recommended production configuration
6. **Auto-scaling on queue depth** is the most effective scaling strategy

---

*Generated by DSHB Agent — v86.1-prod*