#!/bin/bash
# V86 Alias Engine - Production Startup Script
# Task: DSHE_V86_ALIAS_ENGINE_FULL_REPLAY_AND_GRAY_RELEASE_PLAN · T2.2

set -euo pipefail

ENGINE_MODE="${V86_ALIAS_MODE:-f3+f4}"
INIT_TIMEOUT="${V86_INIT_TIMEOUT:-60}"
WARMUP="${V86_WARMUP:-true}"
HEALTH_PORT="${V86_HEALTH_PORT:-8080}"
METRICS_PORT="${V86_METRICS_PORT:-8081}"
CACHE_DIR="${V86_CACHE_DIR:-/var/cache/v86-alias}"
LOG_DIR="${V86_LOG_DIR:-/var/log/v86-alias}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(cd "$ENGINE_DIR/../.." && pwd)"

mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/engine_$(date +%Y%m%d).log"

log() {
    local level="$1"; shift
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [$level] $*" | tee -a "$LOG_FILE"
}

preflight() {
    log INFO "=== V86 Alias Engine Startup ==="
    log INFO "Mode: $ENGINE_MODE"
    log INFO "Repo: $REPO_ROOT"
    command -v python3 >/dev/null || { log ERROR "python3 not found"; exit 1; }
    log INFO "Pre-flight checks passed"
}

warmup_engine() {
    if [ "$WARMUP" != "true" ]; then
        log INFO "Warmup skipped"
        return
    fi
    log INFO "Starting engine warmup..."
    local warmup_script="$ENGINE_DIR/alias_engine_warmup_optimize.py"
    if [ -f "$warmup_script" ]; then
        local t0=$(date +%s)
        python3 "$warmup_script" --warmup 2>&1 | while read line; do log INFO "  $line"; done
        local t1=$(date +%s)
        log INFO "Warmup completed in $((t1 - t0))s"
    fi
}

main() {
    preflight
    export V86_ALIAS_MODE="$ENGINE_MODE"
    export V86_CACHE_DIR="$CACHE_DIR"
    warmup_engine
    log INFO "Starting V86 Alias Engine (mode=$ENGINE_MODE)..."
    cd "$REPO_ROOT"
    exec python3 -m uvicorn v86_alias_service:app \
        --host 0.0.0.0 --port "$HEALTH_PORT" \
        --log-level info 2>&1 | tee -a "$LOG_FILE"
}

cleanup() {
    log INFO "Shutting down..."
    python3 "$ENGINE_DIR/alias_engine_warmup_optimize.py" --save-cache 2>/dev/null || true
    log INFO "Shutdown complete"
    exit 0
}
trap cleanup SIGTERM SIGINT
main "$@"
