#!/usr/bin/env bash
#===============================================================================
# DSHE V87 RC1 G1 — 上线首7天前端指标采集脚本
#
# 工单: V87_RC1_G1_PREP_7DAY_DSHE
# 阶段: PREP_POST_RELEASE_7DAY
# 日期: 2028-05-10
# 编制方: DSHE (L2展示层)
# 前置: FINAL_GATE_PASS (DSHE终审 22/22 Gate PASS, 100/100, 三方3/3 GO)
# 约束: BRANCH_LOCKED=TRUE | NO_OVERWRITE=TRUE | NO_MODIFY_V85=TRUE
#       NO_EDIT_RELEASE_TAG_ASSET=TRUE | NO_ZHIJI_API_CALL=TRUE
#
# 用途: 采集3项重点关注项 + 5项核心指标的持续监控数据
#   关注项: Query P99偏高(18.6%) / 首屏加载接近阈值(9.2%) / 02-03负载敏感
#   核心指标: Render P99 / Query P99 / 首屏加载耗时 / 冷启动报错 / 渲染抖动计数
#
# 基线参考: V87-RC1-G1-BASELINE-FRONTEND-20280509
#   Render P99:   1.173s (基线1.12s)
#   Query P99:    49.8ms (基线42ms)
#   首屏加载P99:  3.220s (基线2.95s)
#   冷启动报错:   0次
#   渲染抖动:     0.005% (1次/19270)
#
# 使用方法:
#   Day1-2: ./frontend_7day_collector_script.sh --intensity high --duration 48h
#   Day3-4: ./frontend_7day_collector_script.sh --intensity medium --duration 48h
#   Day5-7: ./frontend_7day_collector_script.sh --intensity low --duration 72h
#
# 输出:
#   - 指标时序数据: /tmp/dshe_v87_collector/  (CSV)
#   - 告警事件:     /tmp/dshe_v87_collector/alerts/
#   - 状态报告:     /tmp/dshe_v87_collector/status_report_YYYYMMDD.txt
#
# 约束: 只读采集, 不修改任何基线资产/配置文件/Release Tag
#===============================================================================

set -euo pipefail

#===============================================================================
# 配置区域 — 基线值与阈值定义
#===============================================================================

# 脚本版本与元数据
SCRIPT_VERSION="1.0.0"
SCRIPT_NAME="frontend_7day_collector_script.sh"
SCRIPT_DATE="2028-05-10"
TASK_ID="V87_RC1_G1_PREP_7DAY_DSHE"
AGENT="DSHE"
BRANCH="feature/v87-rc1-g1"
BASELINE_ID="V87-RC1-G1-BASELINE-FRONTEND-20280509"

# 输出目录
OUTPUT_DIR="/tmp/dshe_v87_collector"
ALERT_DIR="${OUTPUT_DIR}/alerts"
LOG_DIR="${OUTPUT_DIR}/logs"
REPORT_DIR="${OUTPUT_DIR}/reports"

# 采集模式参数(可命令行覆盖)
COLLECT_INTENSITY="${COLLECT_INTENSITY:-high}"  # high|medium|low
COLLECT_DURATION="${COLLECT_DURATION:-48}"       # 小时
DAY_PHASE="${DAY_PHASE:-1}"                       # 1|2|3|4|5|6|7

#===============================================================================
# 基线值定义 (Phase36预检实测终确值)
#===============================================================================

# --- 关注项基线 (Phase36 3项关注项) ---
BASELINE_QUERY_P99_MS=49.8          # Query P99 (ms)
BASELINE_QUERY_P99_THRESHOLD_P3=50.4    # P3告警: 基线+10% (50.4ms)
BASELINE_QUERY_P99_THRESHOLD_P2=63.0    # P2告警: 基线+30% (63ms)
BASELINE_QUERY_P99_THRESHOLD_P1=84.0    # P1告警: 基线+60% (84ms)

BASELINE_FPL_P99_S=3.220            # 首屏加载P99 (s)
BASELINE_FPL_P99_THRESHOLD_P3=3.25   # P3告警: 基线+10%边界 (3.25s)
BASELINE_FPL_P99_THRESHOLD_P2=3.55   # P2告警: 基线+20% (3.55s)
BASELINE_FPL_P99_THRESHOLD_P1=4.40   # P1告警: 基线+50% (4.40s)

BASELINE_LOAD_INDEX_0203=523        # 02:00-03:00 负载指数峰值
BASELINE_LOAD_INDEX_P3=550          # P3告警阈值
BASELINE_LOAD_INDEX_P2=600          # P2告警阈值
BASELINE_LOAD_INDEX_P1=700          # P1告警阈值

# --- 核心指标基线 ---
BASELINE_RENDER_P99_S=1.173         # Render P99 (s)
BASELINE_RENDER_P99_THRESHOLD_P3=1.23    # P3: +5%
BASELINE_RENDER_P99_THRESHOLD_P2=1.46    # P2: +25%
BASELINE_RENDER_P99_THRESHOLD_P1=2.34    # P1: +100%

BASELINE_COLD_START_ERROR=0          # 冷启动报错次数
BASELINE_COLD_START_THRESHOLD_P3=1    # P3: >0
BASELINE_COLD_START_THRESHOLD_P2=5    # P2: >5
BASELINE_COLD_START_THRESHOLD_P1=20   # P1: >20

BASELINE_RENDER_JITTER_RATE=0.005    # 渲染抖动率 (%)
BASELINE_RENDER_JITTER_THRESHOLD_P3=0.01  # P3: >0.01%
BASELINE_RENDER_JITTER_THRESHOLD_P2=0.1   # P2: >0.1%
BASELINE_RENDER_JITTER_THRESHOLD_P1=1.0   # P1: >1%

BASELINE_SUCCESS_RATE=100            # 成功率 (%)
BASELINE_ERROR_RATE=0                # 错误率 (%)
BASELINE_TIMEOUT_RATE=0              # 超时率 (%)

# --- PDF渲染基线 ---
BASELINE_PDF_RENDER_P99_MS=113      # PDF渲染P99 (ms)
BASELINE_PDF_SUCCESS_RATE=100       # PDF导出成功率 (%)
BASELINE_PDF_REGRESSION=0           # PDF回归数

# --- 索引膨胀基线 ---
BASELINE_INDEX_D60_DAYS=12          # D60 (天)
BASELINE_INDEX_D60_THRESHOLD_P3=15  # P3: >15天
BASELINE_INDEX_D60_THRESHOLD_P2=20  # P2: >20天
BASELINE_INDEX_D60_THRESHOLD_P1=25  # P1: >25天
BASELINE_INDEX_D60_MARGIN_PCT=150   # 安全余量

BASELINE_INDEX_D90_DAYS=35          # D90 (天)
BASELINE_INDEX_D90_THRESHOLD_P3=45  # P3: >45天
BASELINE_INDEX_D90_THRESHOLD_P2=60  # P2: >60天
BASELINE_INDEX_D90_THRESHOLD_P1=80  # P1: >80天
BASELINE_INDEX_D90_MARGIN_PCT=157

BASELINE_INDEX_D365_DAYS=365        # D365 (天)
BASELINE_INDEX_D365_THRESHOLD_P3=390
BASELINE_INDEX_D365_THRESHOLD_P2=430
BASELINE_INDEX_D365_THRESHOLD_P1=480
BASELINE_INDEX_D365_MARGIN_PCT=100

BASELINE_INDEX_CURRENT_MB=11.75     # 当前索引体积 (MB)
BASELINE_INDEX_DAILY_GROWTH=0.006   # 日增长率 (%/day)

# --- 缓存基线 ---
BASELINE_CACHE_HIT_RATE=95          # 缓存命中率 (%)
BASELINE_CACHE_P3=90                # P3: <90%
BASELINE_CACHE_P2=80                # P2: <80%
BASELINE_CACHE_P1=70                # P1: <70%

#===============================================================================
# 采集间隔定义 (按强度分档)
#===============================================================================

# 高强度(Day1-2): 30秒粒度
INTERVAL_HIGH=30        # 秒
# 中强度(Day3-4): 5分钟粒度
INTERVAL_MEDIUM=300     # 秒
# 低强度(Day5-7): 15分钟粒度
INTERVAL_LOW=900        # 秒

# 各指标独立采集间隔
INTERVAL_RENDER_P99=""       # 核心渲染延迟 (与强度绑定)
INTERVAL_QUERY_P99=""        # 核心查询延迟 (与强度绑定)
INTERVAL_FPL_P99=""          # 首屏加载 (与强度绑定)
INTERVAL_PDF_RENDER=""       # PDF渲染 (与强度绑定)
INTERVAL_COLD_START=3600     # 冷启动报错 (每小时)
INTERVAL_RENDER_JITTER=3600  # 渲染抖动 (每小时)
INTERVAL_INDEX_BLOAT=86400   # 索引膨胀 (每天)
INTERVAL_CACHE_HIT=300       # 缓存命中率 (5分钟)
INTERVAL_LOAD_INDEX=300      # 负载指数 (5分钟)
INTERVAL_SUCCESS_RATE=""     # 成功率 (与强度绑定)
INTERVAL_ERROR_RATE=""       # 错误率 (与强度绑定)

#===============================================================================
# 告警定义 — P1/P2/P3 三级升级规则
#===============================================================================

declare -A ALERT_DEFINITIONS=(
    ["ALERT_RENDER_P99_P3"]="Render P99 > 1.23s (基线+5%)"
    ["ALERT_RENDER_P99_P2"]="Render P99 > 1.46s (基线+25%)"
    ["ALERT_RENDER_P99_P1"]="Render P99 > 2.34s (基线+100%)"
    ["ALERT_QUERY_P99_P3"]="Query P99 > 50.4ms (基线+10%)"
    ["ALERT_QUERY_P99_P2"]="Query P99 > 63ms (基线+30%)"
    ["ALERT_QUERY_P99_P1"]="Query P99 > 84ms (基线+60%)"
    ["ALERT_FPL_P99_P3"]="首屏加载P99 > 3.25s (基线+10%边界)"
    ["ALERT_FPL_P99_P2"]="首屏加载P99 > 3.55s (基线+20%)"
    ["ALERT_FPL_P99_P1"]="首屏加载P99 > 4.40s (基线+50%)"
    ["ALERT_SUCCESS_RATE_P3"]="成功率 < 99.9%"
    ["ALERT_SUCCESS_RATE_P2"]="成功率 < 99%"
    ["ALERT_SUCCESS_RATE_P1"]="成功率 < 95%"
    ["ALERT_ERROR_RATE_P3"]="错误率 > 0.1%"
    ["ALERT_ERROR_RATE_P2"]="错误率 > 1%"
    ["ALERT_ERROR_RATE_P1"]="错误率 > 5%"
    ["ALERT_TIMEOUT_RATE_P3"]="超时率 > 0.1%"
    ["ALERT_TIMEOUT_RATE_P2"]="超时率 > 1%"
    ["ALERT_TIMEOUT_RATE_P1"]="超时率 > 5%"
    ["ALERT_COLD_START_P3"]="冷启动报错 > 0次"
    ["ALERT_COLD_START_P2"]="冷启动报错 > 5次"
    ["ALERT_COLD_START_P1"]="冷启动报错 > 20次"
    ["ALERT_RENDER_JITTER_P3"]="渲染抖动率 > 0.01%"
    ["ALERT_RENDER_JITTER_P2"]="渲染抖动率 > 0.1%"
    ["ALERT_RENDER_JITTER_P1"]="渲染抖动率 > 1%"
    ["ALERT_PDF_RENDER_P99_P3"]="PDF渲染P99 > 124ms (基线+10%)"
    ["ALERT_PDF_RENDER_P99_P2"]="PDF渲染P99 > 152ms (基线+30%)"
    ["ALERT_PDF_RENDER_P99_P1"]="PDF渲染P99 > 226ms (基线+100%)"
    ["ALERT_PDF_REGRESSION_P3"]="PDF回归 > 0"
    ["ALERT_PDF_REGRESSION_P2"]="PDF回归 > 3"
    ["ALERT_PDF_REGRESSION_P1"]="PDF回归 > 10"
    ["ALERT_INDEX_D60_P3"]="D60 > 15天"
    ["ALERT_INDEX_D60_P2"]="D60 > 20天"
    ["ALERT_INDEX_D60_P1"]="D60 > 25天"
    ["ALERT_INDEX_D90_P3"]="D90 > 45天"
    ["ALERT_INDEX_D90_P2"]="D90 > 60天"
    ["ALERT_INDEX_D90_P1"]="D90 > 80天"
    ["ALERT_INDEX_D365_P3"]="D365 > 390天"
    ["ALERT_INDEX_D365_P2"]="D365 > 430天"
    ["ALERT_INDEX_D365_P1"]="D365 > 480天"
    ["ALERT_CACHE_HIT_P3"]="缓存命中率 < 90%"
    ["ALERT_CACHE_HIT_P2"]="缓存命中率 < 80%"
    ["ALERT_CACHE_HIT_P1"]="缓存命中率 < 70%"
    ["ALERT_LOAD_INDEX_P3"]="02-03负载指数 > 550"
    ["ALERT_LOAD_INDEX_P2"]="02-03负载指数 > 600"
    ["ALERT_LOAD_INDEX_P1"]="02-03负载指数 > 700"
)

#===============================================================================
# 升级策略定义
#===============================================================================

declare -A UPGRADE_STRATEGIES=(
    ["P1_ANY"]="启动全量回滚(ROLLBACK-01) SLA<5min"
    ["P2_SUSTAINED_30MIN"]="启动部分回滚(ROLLBACK-02/03) SLA<15min"
    ["P3_MULTI_TRIGGER"]="升级至P2评估 SLA<15min"
    ["QUERY_P99_SUSTAINED_1H"]="缓存预热+索引优化 SLA<30min"
    ["FPL_SUSTAINED_1H"]="CDN预热+资源预加载 SLA<30min"
    ["RENDER_JITTER_SUSTAINED_1H"]="缓存扩容+渲染优化 SLA<30min"
)

#===============================================================================
# 函数定义
#===============================================================================

log() {
    local level="$1"
    shift
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] $*" | tee -a "${LOG_DIR}/collector_$(date '+%Y%m%d').log"
}

log_info()  { log "INFO"  "$@"; }
log_warn()  { log "WARN"  "$@"; }
log_error() { log "ERROR" "$@"; }
log_alert() { log "ALERT" "$@"; }

initialize_directories() {
    mkdir -p "${OUTPUT_DIR}" "${ALERT_DIR}" "${LOG_DIR}" "${REPORT_DIR}"
    mkdir -p "${OUTPUT_DIR}/render_p99"
    mkdir -p "${OUTPUT_DIR}/query_p99"
    mkdir -p "${OUTPUT_DIR}/fpl_p99"
    mkdir -p "${OUTPUT_DIR}/pdf_render"
    mkdir -p "${OUTPUT_DIR}/cold_start"
    mkdir -p "${OUTPUT_DIR}/render_jitter"
    mkdir -p "${OUTPUT_DIR}/index_bloat"
    mkdir -p "${OUTPUT_DIR}/cache_hit"
    mkdir -p "${OUTPUT_DIR}/load_index"
}

get_sample_interval() {
    case "${COLLECT_INTENSITY}" in
        high)   echo "${INTERVAL_HIGH}" ;;
        medium) echo "${INTERVAL_MEDIUM}" ;;
        low)    echo "${INTERVAL_LOW}" ;;
        *)      echo "${INTERVAL_MEDIUM}" ;;
    esac
}

get_day_phase_label() {
    case "${DAY_PHASE}" in
        1|2) echo "Day${DAY_PHASE} (高强度/30s粒度)" ;;
        3|4) echo "Day${DAY_PHASE} (中强度/5min粒度)" ;;
        5|6|7) echo "Day${DAY_PHASE} (低强度/15min粒度)" ;;
        *)     echo "Day${DAY_PHASE}" ;;
    esac
}

# --- 指标采集函数 ---

collect_render_p99() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local value
    # 模拟采集Render P99 — 生产环境替换为真实监控API
    value=$(get_metric_value "render_p99" "${BASELINE_RENDER_P99_S}")
    local file="${OUTPUT_DIR}/render_p99/render_p99_$(date '+%Y%m%d').csv"
    echo "${timestamp},${value}" >> "${file}"
    check_threshold "render_p99" "${value}" \
        "${BASELINE_RENDER_P99_THRESHOLD_P3}" \
        "${BASELINE_RENDER_P99_THRESHOLD_P2}" \
        "${BASELINE_RENDER_P99_THRESHOLD_P1}" \
        "Render P99"
}

collect_query_p99() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local value
    value=$(get_metric_value "query_p99" "${BASELINE_QUERY_P99_MS}")
    local file="${OUTPUT_DIR}/query_p99/query_p99_$(date '+%Y%m%d').csv"
    echo "${timestamp},${value}" >> "${file}"
    check_threshold "query_p99" "${value}" \
        "${BASELINE_QUERY_P99_THRESHOLD_P3}" \
        "${BASELINE_QUERY_P99_THRESHOLD_P2}" \
        "${BASELINE_QUERY_P99_THRESHOLD_P1}" \
        "Query P99"
}

collect_fpl_p99() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local value
    value=$(get_metric_value "fpl_p99" "${BASELINE_FPL_P99_S}")
    local file="${OUTPUT_DIR}/fpl_p99/fpl_p99_$(date '+%Y%m%d').csv"
    echo "${timestamp},${value}" >> "${file}"
    check_threshold "fpl_p99" "${value}" \
        "${BASELINE_FPL_P99_THRESHOLD_P3}" \
        "${BASELINE_FPL_P99_THRESHOLD_P2}" \
        "${BASELINE_FPL_P99_THRESHOLD_P1}" \
        "首屏加载P99"
}

collect_pdf_render() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local render_p99
    local success_rate
    local regression
    render_p99=$(get_metric_value "pdf_render_p99" "${BASELINE_PDF_RENDER_P99_MS}")
    success_rate=$(get_metric_value "pdf_success_rate" "${BASELINE_PDF_SUCCESS_RATE}")
    regression=$(get_metric_value "pdf_regression" "${BASELINE_PDF_REGRESSION}")
    local file="${OUTPUT_DIR}/pdf_render/pdf_render_$(date '+%Y%m%d').csv"
    echo "${timestamp},${render_p99},${success_rate},${regression}" >> "${file}"
    check_threshold "pdf_render_p99" "${render_p99}" \
        124 152 226 "PDF渲染P99"
    check_regression_alert "${regression}"
}

collect_cold_start() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local error_count
    error_count=$(get_metric_value "cold_start_error" "${BASELINE_COLD_START_ERROR}")
    local file="${OUTPUT_DIR}/cold_start/cold_start_$(date '+%Y%m%d').csv"
    echo "${timestamp},${error_count}" >> "${file}"
    check_count_alert "cold_start" "${error_count}" \
        "${BASELINE_COLD_START_THRESHOLD_P3}" \
        "${BASELINE_COLD_START_THRESHOLD_P2}" \
        "${BASELINE_COLD_START_THRESHOLD_P1}" \
        "冷启动报错"
}

collect_render_jitter() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local jitter_count
    local render_count
    local jitter_rate
    jitter_count=$(get_metric_value "render_jitter_count" 0)
    render_count=$(get_metric_value "render_total_count" 100)
    jitter_rate=$(awk "BEGIN {printf \"%.4f\", (${jitter_count}/${render_count})*100}")
    local file="${OUTPUT_DIR}/render_jitter/render_jitter_$(date '+%Y%m%d').csv"
    echo "${timestamp},${jitter_count},${render_count},${jitter_rate}" >> "${file}"
    check_threshold "render_jitter_rate" "${jitter_rate}" \
        "${BASELINE_RENDER_JITTER_THRESHOLD_P3}" \
        "${BASELINE_RENDER_JITTER_THRESHOLD_P2}" \
        "${BASELINE_RENDER_JITTER_THRESHOLD_P1}" \
        "渲染抖动率"
}

collect_index_bloat() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local d60 d90 d365 current_mb daily_growth cusum_p
    d60=$(get_metric_value "index_d60" "${BASELINE_INDEX_D60_DAYS}")
    d90=$(get_metric_value "index_d90" "${BASELINE_INDEX_D90_DAYS}")
    d365=$(get_metric_value "index_d365" "${BASELINE_INDEX_D365_DAYS}")
    current_mb=$(get_metric_value "index_current_mb" "${BASELINE_INDEX_CURRENT_MB}")
    daily_growth=$(get_metric_value "index_daily_growth" "${BASELINE_INDEX_DAILY_GROWTH}")
    cusum_p=$(get_metric_value "index_cusum_p" 0.82)
    local file="${OUTPUT_DIR}/index_bloat/index_bloat_$(date '+%Y%m%d').csv"
    echo "${timestamp},${current_mb},${d60},${d90},${d365},${daily_growth},${cusum_p}" >> "${file}"
    check_index_alert "D60" "${d60}" \
        "${BASELINE_INDEX_D60_THRESHOLD_P3}" \
        "${BASELINE_INDEX_D60_THRESHOLD_P2}" \
        "${BASELINE_INDEX_D60_THRESHOLD_P1}"
    check_index_alert "D90" "${d90}" \
        "${BASELINE_INDEX_D90_THRESHOLD_P3}" \
        "${BASELINE_INDEX_D90_THRESHOLD_P2}" \
        "${BASELINE_INDEX_D90_THRESHOLD_P1}"
    check_index_alert "D365" "${d365}" \
        "${BASELINE_INDEX_D365_THRESHOLD_P3}" \
        "${BASELINE_INDEX_D365_THRESHOLD_P2}" \
        "${BASELINE_INDEX_D365_THRESHOLD_P1}"
}

collect_cache_hit() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local hit_rate
    hit_rate=$(get_metric_value "cache_hit_rate" "${BASELINE_CACHE_HIT_RATE}")
    local file="${OUTPUT_DIR}/cache_hit/cache_hit_$(date '+%Y%m%d').csv"
    echo "${timestamp},${hit_rate}" >> "${file}"
    # 缓存命中率是反向阈值: 低于阈值告警
    if (( $(echo "${hit_rate} < ${BASELINE_CACHE_P3}" | bc -l) )); then
        local severity="P3"
        if (( $(echo "${hit_rate} < ${BASELINE_CACHE_P1}" | bc -l) )); then
            severity="P1"
        elif (( $(echo "${hit_rate} < ${BASELINE_CACHE_P2}" | bc -l) )); then
            severity="P2"
        fi
        trigger_alert "ALERT_CACHE_HIT_${severity}" "缓存命中率 ${hit_rate}% < ${BASELINE_CACHE_P3}% (阈值)" "${severity}"
    fi
}

collect_load_index() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local load_index
    load_index=$(get_metric_value "load_index_0203" "${BASELINE_LOAD_INDEX_0203}")
    local file="${OUTPUT_DIR}/load_index/load_index_0203_$(date '+%Y%m%d').csv"
    echo "${timestamp},${load_index}" >> "${file}"
    check_threshold "load_index" "${load_index}" \
        "${BASELINE_LOAD_INDEX_P3}" \
        "${BASELINE_LOAD_INDEX_P2}" \
        "${BASELINE_LOAD_INDEX_P1}" \
        "02-03负载指数"
}

# --- 工具函数 ---

get_metric_value() {
    local metric_name="$1"
    local baseline="$2"
    # 生产环境: 替换为实际监控API调用
    # curl -s "http://metrics-api/v1/${metric_name}" | jq '.value'
    # 当前为模拟模式: 返回基线值+微噪声
    awk "BEGIN {
        srand();
        noise = rand() * 0.05;  # ±5%噪声
        val = ${baseline} + (${baseline} * noise);
        printf \"%.4f\", val;
    }"
}

check_threshold() {
    local metric_name="$1"
    local value="$2"
    local p3_threshold="$3"
    local p2_threshold="$4"
    local p1_threshold="$5"
    local metric_label="$6"

    if (( $(echo "${value} > ${p1_threshold}" | bc -l) )); then
        trigger_alert "ALERT_${metric_name^^}_P1" "${metric_label} ${value} > ${p1_threshold} (P1)" "P1"
    elif (( $(echo "${value} > ${p2_threshold}" | bc -l) )); then
        trigger_alert "ALERT_${metric_name^^}_P2" "${metric_label} ${value} > ${p2_threshold} (P2)" "P2"
    elif (( $(echo "${value} > ${p3_threshold}" | bc -l) )); then
        trigger_alert "ALERT_${metric_name^^}_P3" "${metric_label} ${value} > ${p3_threshold} (P3)" "P3"
    fi
}

check_count_alert() {
    local metric_name="$1"
    local count="$2"
    local p3_threshold="$3"
    local p2_threshold="$4"
    local p1_threshold="$5"
    local metric_label="$6"

    if (( ${count} > ${p1_threshold} )); then
        trigger_alert "ALERT_${metric_name^^}_P1" "${metric_label} ${count} > ${p1_threshold} (P1)" "P1"
    elif (( ${count} > ${p2_threshold} )); then
        trigger_alert "ALERT_${metric_name^^}_P2" "${metric_label} ${count} > ${p2_threshold} (P2)" "P2"
    elif (( ${count} > ${p3_threshold} )); then
        trigger_alert "ALERT_${metric_name^^}_P3" "${metric_label} ${count} > ${p3_threshold} (P3)" "P3"
    fi
}

check_index_alert() {
    local metric_label="$1"
    local value="$2"
    local p3_threshold="$3"
    local p2_threshold="$4"
    local p1_threshold="$5"

    if (( $(echo "${value} > ${p1_threshold}" | bc -l) )); then
        trigger_alert "ALERT_INDEX_${metric_label}_P1" "索引膨胀${metric_label} ${value}天 > ${p1_threshold}天 (P1)" "P1"
    elif (( $(echo "${value} > ${p2_threshold}" | bc -l) )); then
        trigger_alert "ALERT_INDEX_${metric_label}_P2" "索引膨胀${metric_label} ${value}天 > ${p2_threshold}天 (P2)" "P2"
    elif (( $(echo "${value} > ${p3_threshold}" | bc -l) )); then
        trigger_alert "ALERT_INDEX_${metric_label}_P3" "索引膨胀${metric_label} ${value}天 > ${p3_threshold}天 (P3)" "P3"
    fi
}

check_regression_alert() {
    local regression="$1"
    if (( ${regression} > 10 )); then
        trigger_alert "ALERT_PDF_REGRESSION_P1" "PDF回归 ${regression} > 10 (P1)" "P1"
    elif (( ${regression} > 3 )); then
        trigger_alert "ALERT_PDF_REGRESSION_P2" "PDF回归 ${regression} > 3 (P2)" "P2"
    elif (( ${regression} > 0 )); then
        trigger_alert "ALERT_PDF_REGRESSION_P3" "PDF回归 ${regression} > 0 (P3)" "P3"
    fi
}

trigger_alert() {
    local alert_id="$1"
    local description="$2"
    local severity="$3"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local alert_file="${ALERT_DIR}/alert_${severity}_$(date '+%Y%m%d_%H%M%S')_${alert_id}.json"

    cat > "${alert_file}" <<ALERT_EOF
{
  "alert_id": "${alert_id}",
  "description": "${description}",
  "severity": "${severity}",
  "timestamp": "${timestamp}",
  "metric_name": "${alert_id%%_P*}",
  "baseline_reference": "${BASELINE_ID}",
  "upgrade_strategy": "${UPGRADE_STRATEGIES[P${severity#P}_ANY]:-待评估}",
  "action_required": "${UPGRADE_STRATEGIES[P${severity#P}_ANY]:-待评估}",
  "sla_minutes": $([ "${severity}" = "P1" ] && echo 5 || echo $([ "${severity}" = "P2" ] && echo 15 || echo 30)),
  "source_script": "${SCRIPT_NAME}",
  "source_version": "${SCRIPT_VERSION}",
  "task_id": "${TASK_ID}",
  "agent": "${AGENT}",
  "branch": "${BRANCH}",
  "day_phase": "${DAY_PHASE}",
  "intensity": "${COLLECT_INTENSITY}"
}
ALERT_EOF

    log_alert "[${severity}] ${description} (SLA: ${UPGRADE_STRATEGIES[P${severity#P}_ANY]:-待评估})"
}

print_status_report() {
    local report_file="${REPORT_DIR}/status_report_$(date '+%Y%m%d_%H%M%S').txt"
    local interval
    interval=$(get_sample_interval)

    cat > "${report_file}" <<REPORT_EOF
===============================================================================
DSHE V87 RC1 G1 — 上线首7天前端指标采集状态报告
===============================================================================
脚本版本:       ${SCRIPT_VERSION}
任务ID:         ${TASK_ID}
Agent:          ${AGENT}
分支:           ${BRANCH}
基线ID:         ${BASELINE_ID}
采集日期:       $(date '+%Y-%m-%d %H:%M:%S')
采集强度:       ${COLLECT_INTENSITY} (${interval}s粒度)
采集时长:       ${COLLECT_DURATION}h
Day阶段:        $(get_day_phase_label)

===============================================================================
基线值参考 (Phase36终确值)
===============================================================================
指标                   基线值       P3告警       P2告警       P1告警
----                   ----       ----         ----         ----
Render P99             ${BASELINE_RENDER_P99_S}s    >1.23s       >1.46s       >2.34s
Query P99              ${BASELINE_QUERY_P99_MS}ms    >50.4ms      >63ms        >84ms
首屏加载P99            ${BASELINE_FPL_P99_S}s    >3.25s       >3.55s       >4.40s
PDF渲染P99             ${BASELINE_PDF_RENDER_P99_MS}ms   >124ms       >152ms       >226ms
冷启动报错             ${BASELINE_COLD_START_ERROR}次       >0           >5           >20
渲染抖动率             ${BASELINE_RENDER_JITTER_RATE}%     >0.01%       >0.1%        >1%
D60                    ${BASELINE_INDEX_D60_DAYS}天      >15天        >20天        >25天
D90                    ${BASELINE_INDEX_D90_DAYS}天      >45天        >60天        >80天
D365                   ${BASELINE_INDEX_D365_DAYS}天      >390天       >430天       >480天
缓存命中率             ${BASELINE_CACHE_HIT_RATE}%      <90%         <80%         <70%
02-03负载指数          ${BASELINE_LOAD_INDEX_0203}     >550         >600         >700

===============================================================================
升级策略
===============================================================================
P1告警(任一项):     ${UPGRADE_STRATEGIES[P1_ANY]}
P2告警(持续>30min): ${UPGRADE_STRATEGIES[P2_SUSTAINED_30MIN]}
P3告警(多项同时):   ${UPGRADE_STRATEGIES[P3_MULTI_TRIGGER]}
Query P99>50.4ms>1h: ${UPGRADE_STRATEGIES[QUERY_P99_SUSTAINED_1H]}
首屏加载>3.25s>1h:   ${UPGRADE_STRATEGIES[FPL_SUSTAINED_1H]}
渲染抖动>0.01%>1h:   ${UPGRADE_STRATEGIES[RENDER_JITTER_SUSTAINED_1H]}

===============================================================================
输出目录
===============================================================================
主输出:           ${OUTPUT_DIR}
告警:             ${ALERT_DIR}
日志:             ${LOG_DIR}
报告:             ${REPORT_DIR}
渲染P99:          ${OUTPUT_DIR}/render_p99/
查询P99:          ${OUTPUT_DIR}/query_p99/
首屏P99:          ${OUTPUT_DIR}/fpl_p99/
PDF渲染:          ${OUTPUT_DIR}/pdf_render/
冷启动:           ${OUTPUT_DIR}/cold_start/
渲染抖动:         ${OUTPUT_DIR}/render_jitter/
索引膨胀:         ${OUTPUT_DIR}/index_bloat/
缓存命中:         ${OUTPUT_DIR}/cache_hit/
负载指数:         ${OUTPUT_DIR}/load_index/

===============================================================================
约束合规
===============================================================================
BRANCH_LOCKED=TRUE          ✅ 未切换分支
NO_OVERWRITE=TRUE           ✅ 不覆盖冻结基线
NO_MODIFY_V85=TRUE          ✅ 不修改V85
NO_EDIT_RELEASE_TAG_ASSET=TRUE  ✅ 不编辑Release Tag
NO_ZHIJI_API_CALL=TRUE      ✅ 不调用知几API
只读采集:                ✅ 不修改任何配置/基线/Tag

===============================================================================
报告结束
===============================================================================
REPORT_EOF

    log_info "状态报告已输出: ${report_file}"
    cat "${report_file}"
}

#===============================================================================
# 主采集循环
#===============================================================================

main() {
    local interval
    interval=$(get_sample_interval)
    local total_seconds=$((COLLECT_DURATION * 3600))
    local elapsed_seconds=0
    local sample_count=0
    local alert_count=0

    log_info "========================================================================="
    log_info "DSHE V87 RC1 G1 — 前端7天采集脚本 v${SCRIPT_VERSION}"
    log_info "任务ID: ${TASK_ID}"
    log_info "基线: ${BASELINE_ID}"
    log_info "采集强度: ${COLLECT_INTENSITY} (${interval}s粒度)"
    log_info "采集时长: ${COLLECT_DURATION}h"
    log_info "Day阶段: $(get_day_phase_label)"
    log_info "========================================================================="

    # 初始化目录
    initialize_directories

    # 输出状态报告
    print_status_report

    # 启动采集循环
    log_info "开始采集循环: 间隔${interval}s, 预计${total_seconds}s"

    while (( ${elapsed_seconds} < ${total_seconds} )); do
        local iteration_start
        iteration_start=$(date +%s)

        sample_count=$((sample_count + 1))

        # --- 与强度绑定的核心指标采集 ---
        collect_render_p99
        collect_query_p99
        collect_fpl_p99
        collect_pdf_render

        # --- 固定间隔指标采集 ---
        if (( ${sample_count} % 1 == 0 )); then
            collect_cache_hit
            collect_load_index
        fi

        # --- 每小时采集 ---
        if (( ${sample_count} % ((3600 / interval)) == 0 )); then
            collect_cold_start
            collect_render_jitter
        fi

        # --- 每天采集 ---
        if (( ${sample_count} % ((86400 / interval)) == 0 )); then
            collect_index_bloat
        fi

        # --- 计算实际耗时 ---
        local actual_elapsed
        actual_elapsed=$(( $(date +%s) - iteration_start ))
        local sleep_time=$((interval - actual_elapsed))
        if (( ${sleep_time} > 0 )); then
            sleep ${sleep_time}
        fi

        elapsed_seconds=$((elapsed_seconds + interval))

        # 每100次采样输出一次进度
        if (( ${sample_count} % 100 == 0 )); then
            local progress_pct
            progress_pct=$(awk "BEGIN {printf \"%.1f\", (${elapsed_seconds}/${total_seconds})*100}")
            log_info "采集进度: ${sample_count}次采样 (${progress_pct}%) | 告警: ${alert_count}"
        fi
    done

    # 采集完成汇总
    log_info "========================================================================="
    log_info "采集完成: ${sample_count}次采样, ${alert_count}次告警"
    log_info "输出目录: ${OUTPUT_DIR}"
    log_info "告警目录: ${ALERT_DIR}"
    log_info "日志目录: ${LOG_DIR}"
    log_info "========================================================================="

    # 输出最终状态报告
    print_status_report
}

#===============================================================================
# 命令行参数解析
#===============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --intensity)
                COLLECT_INTENSITY="$2"
                shift 2
                ;;
            --duration)
                COLLECT_DURATION="${2%h}"
                shift 2
                ;;
            --day)
                DAY_PHASE="$2"
                shift 2
                ;;
            --help|-h)
                cat <<HELP_EOF
用法: ${SCRIPT_NAME} [选项]

选项:
  --intensity <high|medium|low>  采集强度 (默认: high)
    high   = 30秒粒度 (Day1-2 高强度)
    medium = 5分钟粒度 (Day3-4 中强度)
    low    = 15分钟粒度 (Day5-7 低强度)
  --duration <N>h               采集时长(小时, 默认: 48)
  --day <N>                      Day阶段 (1-7, 默认: 1)
  --help                         显示帮助

示例:
  Day1-2:   ${SCRIPT_NAME} --intensity high --duration 48 --day 1
  Day3-4:   ${SCRIPT_NAME} --intensity medium --duration 48 --day 3
  Day5-7:   ${SCRIPT_NAME} --intensity low --duration 72 --day 5

基线参考: ${BASELINE_ID}
输出目录: ${OUTPUT_DIR}
HELP_EOF
                exit 0
                ;;
            *)
                log_warn "未知参数: $1 (忽略)"
                shift
                ;;
        esac
    done
}

#===============================================================================
# 入口
#===============================================================================

parse_args "$@"
main "$@"