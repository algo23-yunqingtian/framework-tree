#!/usr/bin/env bash
# =============================================================================
# V86-RC2 L2 Panel One-Click Rollback Script
# Task:    DSHE_V86_RC2_L2_PANEL_REAL_DEP_GRAY_DEP_READY / T3.4
# Branch:  feature/v85-chart-template @ commit 1d5990b
# Version: 1.0.0 | Date: 2026-10-15 | Author: DSHE L2 Panel Team
#
# 4 rollback actions:
#   A-1: Alert Adapter → sandbox (--deploy-env sandbox)
#   A-2: Data source → mock (datasource_mode=mock)
#   A-3: Pause metric collection (metric_collector_enabled=false)
#   A-4: Enable alert silence (alert_silence_enabled=true)
#
# Does NOT touch DEP/Gate/audit/event store/DSHB services.
# Exit codes: 0=success 1=error 2=partial 3=precondition failed
# =============================================================================

set -euo pipefail

# === CONSTANTS ===
readonly SCRIPT_VERSION="1.0.0"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly TS_UTC="$(date -u -Iseconds)"
readonly EXIT_SUCCESS=0 EXIT_ERROR=1 EXIT_PARTIAL=2 EXIT_PRECOND_FAILED=3

# === CONFIG (env-overridable) ===
: "${ALERT_ADAPTER_CONFIG:=${SCRIPT_DIR}/alert_adapter_config.json}"
: "${PANEL_CONFIG:=${SCRIPT_DIR}/panel_config.json}"
: "${METRIC_COLLECTOR_CONFIG:=${SCRIPT_DIR}/metric_collector_config.json}"
: "${ALERT_SILENCE_CONFIG:=${SCRIPT_DIR}/alert_silence_config.json}"
: "${ROLLBACK_STATE_FILE:=${SCRIPT_DIR}/rollback_state.json}"
: "${ROLLBACK_LOG_FILE:=${SCRIPT_DIR}/rollback.log}"
: "${ROLLBACK_CONFIRM_TIMEOUT:=60}"

# === GLOBAL STATE ===
DRY_RUN=false FORCE=false VERIFY_ONLY=false VERBOSE=false
ROLLBACK_SCOPE="full"
SELECTED_ACTIONS=()
ACTION_RESULTS=()
TOTAL_ACTIONS=0 SUCCESS=0 FAILED=0 SKIPPED=0
EXIT_CODE=$EXIT_SUCCESS

# === ACTION TABLE (id -> config,field,target,type,desc) ===
declare -A ACT_CFG=(
  [1]="$ALERT_ADAPTER_CONFIG:deploy_env:sandbox:string"
  [2]="$PANEL_CONFIG:datasource_mode:mock:string"
  [3]="$METRIC_COLLECTOR_CONFIG:metric_collector_enabled:false:bool"
  [4]="$ALERT_SILENCE_CONFIG:alert_silence_enabled:true:bool"
)
declare -A ACT_DESC=(
  [1]="Switch Alert Adapter to sandbox"
  [2]="Switch data source to mock"
  [3]="Pause metric collection"
  [4]="Enable alert silence"
)

# === LOGGING ===
_log() { local level="$1"; shift; echo "[$(date -u -Iseconds)] [$level] $*" | tee -a "$ROLLBACK_LOG_FILE" 2>/dev/null; }
log_info()  { _log INFO  "$@"; }
log_warn()  { _log WARN  "$@"; }
log_error() { _log ERROR "$@"; }
log_debug() { $VERBOSE && _log DEBUG "$@" || true; }
log_ok()    { _log OK    "$@"; }
log_sep()   { _log ==== "================================================================"; }

# === HELP ===
usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]
  --rollback-scope SCOPE  full|partial|alert_only|datasource_only (default: full)
  --actions LIST          Comma-separated action IDs (partial scope only)
  --dry-run               Print plan without executing
  --force                 Skip confirmation prompt
  --verify-only           Only verify current state
  --verbose               Enable debug logging
  --help                  Show this help

Environment:
  ALERT_ADAPTER_CONFIG, PANEL_CONFIG, METRIC_COLLECTOR_CONFIG,
  ALERT_SILENCE_CONFIG, ROLLBACK_STATE_FILE, ROLLBACK_LOG_FILE,
  ROLLBACK_CONFIRM_TIMEOUT

Exit codes: 0=success 1=error 2=partial 3=precondition failed
EOF
}

# === ARGS ===
parse_args() {
  local show_help=false
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --rollback-scope) ROLLBACK_SCOPE="$2"; shift 2 ;;
      --actions)        IFS=',' read -ra SELECTED_ACTIONS <<< "$2"; shift 2 ;;
      --dry-run)        DRY_RUN=true; shift ;;
      --force)          FORCE=true; shift ;;
      --verify-only)    VERIFY_ONLY=true; shift ;;
      --verbose)        VERBOSE=true; shift ;;
      --help|-h)        show_help=true; shift ;;
      *)                log_error "Unknown option: $1"; usage; exit $EXIT_ERROR ;;
    esac
  done
  $show_help && { usage; exit $EXIT_SUCCESS; }

  # Resolve scope → action list
  case "$ROLLBACK_SCOPE" in
    full)          SELECTED_ACTIONS=(1 2 3 4) ;;
    alert_only)    SELECTED_ACTIONS=(1 4) ;;
    datasource_only) SELECTED_ACTIONS=(2 3) ;;
    partial)
      [[ ${#SELECTED_ACTIONS[@]} -eq 0 ]] && { log_error "partial requires --actions"; exit $EXIT_ERROR; }
      ;;
    *) log_error "Invalid scope: $ROLLBACK_SCOPE"; exit $EXIT_ERROR ;;
  esac

  TOTAL_ACTIONS=${#SELECTED_ACTIONS[@]}
  [[ $TOTAL_ACTIONS -eq 0 ]] && { log_error "No actions"; exit $EXIT_ERROR; }

  # Validate action IDs
  for a in "${SELECTED_ACTIONS[@]}"; do
    [[ -z "${ACT_CFG[$a]:-}" ]] && { log_error "Invalid action ID: $a"; exit $EXIT_ERROR; }
  done

  log_info "Init: $(basename "$0") v$SCRIPT_VERSION mode=$( $DRY_RUN && echo dry-run || $VERIFY_ONLY && echo verify || echo execute) scope=$ROLLBACK_SCOPE actions=${SELECTED_ACTIONS[*]} force=$FORCE verbose=$VERBOSE"
}

# === PRECONDITIONS ===
check_global_preconditions() {
  log_sep; log_info "Validating global preconditions..."; log_sep
  local ok=true

  command -v jq &>/dev/null || { log_error "jq not found"; PRECOND_ERR="Missing: jq"; ok=false; }

  local d
  for d in "$(dirname "$ROLLBACK_STATE_FILE")" "$(dirname "$ROLLBACK_LOG_FILE")"; do
    mkdir -p "$d" 2>/dev/null || { log_error "Cannot create dir: $d"; ok=false; }
  done

  touch "$ROLLBACK_LOG_FILE" 2>/dev/null || { log_error "Log not writable"; ok=false; }

  $ok && log_ok "Preconditions PASSED" || { log_error "Preconditions FAILED"; return $EXIT_PRECOND_FAILED; }
  return $EXIT_SUCCESS
}

check_action_precondition() {
  local aid="$1"
  local cfg_field="${ACT_CFG[$aid]}"
  local cfg_file="${cfg_field%%:*}"
  [[ -f "$cfg_file" ]] && { jq empty "$cfg_file" 2>/dev/null || { log_error "Precond fail A-$aid: invalid JSON: $cfg_file"; return $EXIT_PRECOND_FAILED; }; }
  log_debug "Precond OK A-$aid"
  return $EXIT_SUCCESS
}

# === JSON HELPERS ===
read_json() { [[ -f "$1" ]] && jq -r ".${2:-.} // \"NOT_SET\"" "$1" 2>/dev/null || echo "NOT_SET"; }
write_json() {
  local file="$1" field="$2" val="$3" type="$4" tmp="${1}.tmp.$$"
  local filter=""
  case "$type" in
    string) filter=".${field} = \"${val}\"" ;;
    bool)   filter=".${field} = ${val}" ;;
    number) filter=".${field} = ${val}" ;;
    *)      log_error "Invalid type: $type"; return 1 ;;
  esac
  if [[ -f "$file" ]]; then
    cp "$file" "${file}.bak" 2>/dev/null || true
    jq "$filter" "$file" > "$tmp" 2>/dev/null || { log_error "jq failed on $file"; rm -f "$tmp"; return 1; }
  else
    echo "{\"${field%.*}\": {\"${field##*.}\": ${type=bool|string:val}}" > "$tmp" 2>/dev/null || \
      echo "{\"${field%.*}\": {\"${field##*.}\": ${val}}}" > "$tmp" 2>/dev/null || true
  fi
  mv "$tmp" "$file" 2>/dev/null || { log_error "mv failed"; rm -f "$tmp"; return 1; }
  return 0
}

# === EXECUTE ONE ACTION ===
execute_action() {
  local aid="$1"
  local cfg_field="${ACT_CFG[$aid]}"
  local cfg_file="${cfg_field%%:*}"
  local rest="${cfg_field#*:}"
  local field="${rest%%:*}"
  local target="${rest#*:}"
  local type="${rest##*:}"
  local desc="${ACT_DESC[$aid]}"

  log_sep
  log_info "[A-$aid] $desc | file=$cfg_file field=$field -> $target"

  local current
  current=$(read_json "$cfg_file" "$field")
  log_info "[A-$aid] Current: '$current'"

  # Idempotent: already at target
  if [[ "$current" == "$target" ]]; then
    log_ok "[A-$aid] Already at target - skipped"
    ACTION_RESULTS+=("{\"action_id\":$aid,\"status\":\"skipped\",\"msg\":\"Already at target\",\"detail\":\"current=$current\"}")
    SKIPPED=$((SKIPPED+1))
    return 0
  fi

  # Dry-run
  if $DRY_RUN; then
    log_warn "[A-$aid] DRY-RUN: Would set $field from '$current' to '$target'"
    ACTION_RESULTS+=("{\"action_id\":$aid,\"status\":\"dry-run\",\"msg\":\"Would set to $target\",\"detail\":\"current=$current,target=$target\"}")
    SKIPPED=$((SKIPPED+1))
    return 0
  fi

  # Execute
  if write_json "$cfg_file" "$field" "$target" "$type"; then
    local new_val
    new_val=$(read_json "$cfg_file" "$field")
    if [[ "$new_val" == "$target" ]]; then
      log_ok "[A-$aid] SUCCESS: $field -> $target"
      ACTION_RESULTS+=("{\"action_id\":$aid,\"status\":\"success\",\"msg\":\"Changed to $target\",\"detail\":\"from=$current,to=$target\"}")
      SUCCESS=$((SUCCESS+1))
      return 0
    else
      log_error "[A-$aid] Verify fail: expected $target, got $new_val"
      ACTION_RESULTS+=("{\"action_id\":$aid,\"status\":\"failed\",\"msg\":\"Verify fail\",\"detail\":\"expected=$target,got=$new_val\"}")
      FAILED=$((FAILED+1))
      return 1
    fi
  else
    log_error "[A-$aid] Write failed"
    ACTION_RESULTS+=("{\"action_id\":$aid,\"status\":\"failed\",\"msg\":\"Write failed\",\"detail\":\"\"}")
    FAILED=$((FAILED+1))
    return 1
  fi
}

# === STATE FILE ===
init_state() {
  local sf="${ROLLBACK_STATE_FILE}.tmp.$$"
  jq -n --arg s "running" --arg t "$TS_UTC" --arg v "$SCRIPT_VERSION" --arg sc "$ROLLBACK_SCOPE" \
    --argjson a "[]" --argjson dr "$DRY_RUN" --argjson vo "$VERIFY_ONLY" --argjson f "$FORCE" \
    '{"history":[],"current":{"status":$s,"started_at":$t,"completed_at":null,"script_version":$v,"scope":$sc,"dry_run":($dr==true),"verify_only":($vo==true),"force":($f==true),"actions":[]}}' > "$sf"
  mv "$sf" "$ROLLBACK_STATE_FILE" 2>/dev/null || true
  log_debug "State init: $ROLLBACK_STATE_FILE"
}

finalize_state() {
  local final_status="completed" completed_at
  completed_at=$(date -u -Iseconds)
  [[ $FAILED -gt 0 ]] && [[ $SUCCESS -gt 0 ]] && final_status="partial_success" && EXIT_CODE=$EXIT_PARTIAL
  [[ $FAILED -gt 0 ]] && [[ $SUCCESS -eq 0 ]] && final_status="failed" && EXIT_CODE=$EXIT_ERROR
  [[ $DRY_RUN ]] && final_status="dry_run"

  local actions_json="[]"
  [[ ${#ACTION_RESULTS[@]} -gt 0 ]] && actions_json=$(printf '%s\n' "${ACTION_RESULTS[@]}" | jq -s .)

  jq --arg fs "$final_status" --arg ca "$completed_at" --argjson aj "$actions_json" \
    --argjson sc "$SUCCESS" --argjson fc "$FAILED" --argjson skc "$SKIPPED" --argjson tc "$TOTAL_ACTIONS" \
    '.current.status=$fs | .current.completed_at=$ca | .current.actions=$aj |
     .current.summary={"total":$tc,"success":$sc,"failed":$fc,"skipped":$skc} |
     .history += [.current] | del(.current)' "$ROLLBACK_STATE_FILE" > "${ROLLBACK_STATE_FILE}.tmp.$$" 2>/dev/null && \
    mv "${ROLLBACK_STATE_FILE}.tmp.$$" "$ROLLBACK_STATE_FILE" 2>/dev/null || true
  log_info "State finalized: status=$final_status success=$SUCCESS failed=$FAILED skipped=$SKIPPED"
}

# === VERIFY-ONLY ===
verify_only() {
  log_sep; log_info "=== VERIFY-ONLY ==="; log_sep
  local pass=0 fail=0 checks=12

  # V-01: deploy_env
  local v; v=$(read_json "$ALERT_ADAPTER_CONFIG" "deploy_env")
  [[ "$v" == "sandbox" ]] && { log_ok "V-01 PASS: deploy_env=sandbox"; pass=$((pass+1)); } || { log_warn "V-01 WARN: deploy_env=$v"; fail=$((fail+1)); }

  # V-02: datasource_mode
  v=$(read_json "$PANEL_CONFIG" "datasource_mode")
  [[ "$v" == "mock" ]] && { log_ok "V-02 PASS: datasource_mode=mock"; pass=$((pass+1)); } || { log_warn "V-02 WARN: datasource_mode=$v"; fail=$((fail+1)); }

  # V-03: metric_collector_enabled
  v=$(read_json "$METRIC_COLLECTOR_CONFIG" "metric_collector_enabled")
  [[ "$v" == "false" ]] && { log_ok "V-03 PASS: collector paused"; pass=$((pass+1)); } || { log_warn "V-03 WARN: collector=$v"; fail=$((fail+1)); }

  # V-04: alert_silence_enabled
  v=$(read_json "$ALERT_SILENCE_CONFIG" "alert_silence_enabled")
  [[ "$v" == "true" ]] && { log_ok "V-04 PASS: alert silence on"; pass=$((pass+1)); } || { log_warn "V-04 WARN: silence=$v"; fail=$((fail+1)); }

  # V-05: state file exists
  [[ -f "$ROLLBACK_STATE_FILE" ]] && { log_ok "V-05 PASS: state file exists"; pass=$((pass+1)); } || { log_warn "V-05 WARN: no state file"; fail=$((fail+1)); }

  # V-06: state has action records
  if [[ -f "$ROLLBACK_STATE_FILE" ]]; then
    local ac; ac=$(jq '.history[-1].actions | length // 0' "$ROLLBACK_STATE_FILE" 2>/dev/null || echo 0)
    [[ "$ac" -ge 1 ]] && { log_ok "V-06 PASS: $ac action records"; pass=$((pass+1)); } || { log_warn "V-06 WARN: 0 action records"; fail=$((fail+1)); }
  else
    log_warn "V-06 WARN: no state file"; fail=$((fail+1))
  fi

  # V-07: audit events
  local af="${SCRIPT_DIR}/audit_events_persist.json"
  [[ -f "$af" ]] && { log_ok "V-07 PASS: audit events=$(jq '.audit_events|length//0' "$af" 2>/dev/null || echo 0)"; pass=$((pass+1)); } || { log_warn "V-07 WARN: no audit file"; fail=$((fail+1)); }

  # V-08: evidence packages
  local ec; ec=$(ls -1 "${SCRIPT_DIR}"/evidence_package_*.json 2>/dev/null | wc -l)
  log_ok "V-08 PASS: evidence packages=$ec"; pass=$((pass+1))

  # V-09: panel config valid JSON
  if [[ -f "$PANEL_CONFIG" ]]; then
    jq empty "$PANEL_CONFIG" 2>/dev/null && { log_ok "V-09 PASS: panel config valid"; pass=$((pass+1)); } || { log_error "V-09 FAIL: invalid JSON"; fail=$((fail+1)); }
  else
    log_warn "V-09 WARN: no panel config"; fail=$((fail+1))
  fi

  # V-10: WAL log
  local wf="${SCRIPT_DIR}/event_store_wal_v2.log"
  [[ -f "$wf" ]] && { log_ok "V-10 PASS: WAL lines=$(wc -l < "$wf" 2>/dev/null || echo 0)"; pass=$((pass+1)); } || { log_warn "V-10 WARN: no WAL"; fail=$((fail+1)); }

  # V-11: log ERROR count
  local ec2; ec2=$(grep -c ERROR "$ROLLBACK_LOG_FILE" 2>/dev/null || echo 0)
  [[ "$ec2" -eq 0 ]] && { log_ok "V-11 PASS: no ERROR entries"; pass=$((pass+1)); } || { log_warn "V-11 WARN: $ec2 ERROR entries"; fail=$((fail+1)); }

  # V-12: overall
  [[ $fail -eq 0 ]] && { log_ok "V-12 PASS: all checks passed"; pass=$((pass+1)); } || { log_warn "V-12 WARN: $fail checks failed"; fail=$((fail+1)); }

  log_sep
  log_info "Verify: $pass/$checks passed"
  $([ $fail -eq 0 ] && return $EXIT_SUCCESS || return $EXIT_ERROR)
}

# === CONFIRM ===
confirm() {
  $FORCE && { log_info "Confirmation skipped (--force)"; return 0; }
  log_warn "=== ROLLBACK CONFIRMATION ==="
  for a in "${SELECTED_ACTIONS[@]}"; do log_warn "  [A-$a] ${ACT_DESC[$a]}"; done
  log_warn "Scope: $ROLLBACK_SCOPE | Log: $ROLLBACK_LOG_FILE | State: $ROLLBACK_STATE_FILE"
  local input
  read -r -t "$ROLLBACK_CONFIRM_TIMEOUT" -p "> Type ROLLBACK to confirm: " input || { log_error "Timeout"; return 1; }
  [[ "$input" == "ROLLBACK" ]] && { log_ok "Confirmed"; return 0; } || { log_error "Cancelled (got: $input)"; return 1; }
}

# === MAIN ===
main() {
  parse_args "$@"
  log_info "==== V86-RC2 L2 Panel Rollback v$SCRIPT_VERSION @ $TS_UTC ===="

  command -v jq &>/dev/null || { log_error "FATAL: jq required"; exit $EXIT_ERROR; }

  # Ensure log dir
  mkdir -p "$(dirname "$ROLLBACK_LOG_FILE")" 2>/dev/null || true
  mkdir -p "$(dirname "$ROLLBACK_STATE_FILE")" 2>/dev/null || true

  $VERIFY_ONLY && { verify_only; exit $?; }

  check_global_preconditions || { log_error "Preconditions failed"; init_state; finalize_state; exit $EXIT_PRECOND_FAILED; }

  init_state

  confirm || {
    jq '.current.status="cancelled" | .current.completed_at="$(date -u -Iseconds)"' "$ROLLBACK_STATE_FILE" > "${ROLLBACK_STATE_FILE}.tmp.$$" 2>/dev/null && mv "${ROLLBACK_STATE_FILE}.tmp.$$" "$ROLLBACK_STATE_FILE" 2>/dev/null || true
    log_error "Cancelled"; exit $EXIT_ERROR
  }

  log_sep; log_info "Executing rollback..."; log_sep
  local t_start t_end
  t_start=$(date +%s)

  for aid in "${SELECTED_ACTIONS[@]}"; do
    check_action_precondition "$aid" || { log_error "Precond fail A-$aid"; ACTION_RESULTS+=("{\"action_id\":$aid,\"status\":\"precond_failed\",\"msg\":\"Precond not met\",\"detail\":\"\"}"); FAILED=$((FAILED+1)); continue; }
    execute_action "$aid" || FAILED=$((FAILED+1))
  done

  t_end=$(date +%s)

  finalize_state

  # Summary
  log_sep
  log_info "==== ROLLBACK SUMMARY ===="
  log_info "Duration: $((t_end - t_start))s | Total: $TOTAL_ACTIONS | Success: $SUCCESS | Failed: $FAILED | Skipped: $SKIPPED"
  for r in "${ACTION_RESULTS[@]}"; do
    local id st msg
    id=$(echo "$r" | jq -r '.action_id'); st=$(echo "$r" | jq -r '.status'); msg=$(echo "$r" | jq -r '.msg')
    log_info "  [A-$id] $st: $msg"
  done
  log_info "Log: $ROLLBACK_LOG_FILE | State: $ROLLBACK_STATE_FILE"

  if [[ $EXIT_CODE -eq $EXIT_SUCCESS ]]; then log_ok "Rollback completed"; fi
  [[ $EXIT_CODE -eq $EXIT_PARTIAL ]] && { log_warn "Partial success - review failed actions"; }
  [[ $EXIT_CODE -eq $EXIT_ERROR ]]   && { log_error "Rollback failed - retry or manual"; }
  log_sep

  exit $EXIT_CODE
}

main "$@"
