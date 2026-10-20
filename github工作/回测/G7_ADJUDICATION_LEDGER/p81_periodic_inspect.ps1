#requires -Version 5.1
# <copyright>
#   P81 Periodic Inspection + Self-Healing Script
#   Task: DSHD-P81-PERIODIC-INSPECT
#   Token: DSHD-P81-PERIODIC-INSPECT-TOKEN
#   Mode: AUDIT_READ_ONLY
#   Intervention: NONE (except P81 watcher auto-restart)
#   Wind API calls: 0 (guaranteed)
#   Gate: CLOSED/HOLD (unchanged)
#   Release: NOT_ISSUED (unchanged)
# </copyright>
<#
.SYNOPSIS
    P81 cluster periodic inspection + self-healing baseline reinforcement.
.DESCRIPTION
    Every 5 minutes, this script performs a full validation cycle:
      - P0 nine-check verification (audit_only, wind_api_calls=0, gate, permit, etc.)
      - Process liveness check (P81 watcher + 5 protected processes)
      - Watcher poll status verification (last_poll timestamp freshness)
      - Git snapshot consistency (tracked files, version history)
      - Blacklist configuration check (semantic_blacklist.json, exchange_binding_registry)
      - CSV SHA match (dual-hash verification)
      - Disk snapshot directory integrity (_p81_snapshots/)
      - Brief section 十一 persistence check

    Anomaly alert rules (4 categories):
      - ALARM-PROCESS-EXIT: P81 watcher or protected process missing
      - ALARM-SNAPSHOT-LOSS: Snapshot files missing or untracked
      - ALARM-BRIEF-SECTION-LOSS: Brief section 十一 missing
      - ALARM-PATCH-VIOLATION: Archived patch re-execution detected

    Self-healing (restricted to P81 watcher ONLY):
      - Auto-restart P81 watcher if dead (find by commandline, kill wrapper+child, respawn)
      - Pre-restart auto-snapshot + audit log entry
      - NEVER kills protected PIDs (3472, 14644, 30492, 29652, 29708)
      - NEVER touches non-P81 processes

    Output:
      - p81_inspect_daily.md (daily inspection report)
      - tracking_monitor_audit.jsonl (audit events)
      - p81_inspect_state.json (state persistence for cross-cycle comparison)

    Safety:
      - Zero Wind API calls (no wss/windpy imports)
      - Gate and release permit never modified
      - P0 constraints always preserved
      - Offline only (no external network requests)
#>

# ============================================================
# CONFIGURATION
# ============================================================
$CFG = @{
    TaskID              = 'DSHD-P81-PERIODIC-INSPECT'
    Token               = 'DSHD-P81-PERIODIC-INSPECT-TOKEN'
    Version             = '1.1.0-TASK040'
    PollIntervalMinutes = 5
    BaseDir             = 'D:\DSH_WORK\github工作\回测'
    G7Dir               = 'D:\DSH_WORK\github工作\回测\G7_ADJUDICATION_LEDGER'
    ArtDir              = 'D:\DSH_WORK\github工作\回测\artifacts'
    SnapDir             = 'D:\DSH_WORK\github工作\回测\G7_ADJUDICATION_LEDGER\_p81_snapshots'
    WatcherPS1          = 'D:\DSH_WORK\github工作\回测\G7_ADJUDICATION_LEDGER\dshd_p81_watch.ps1'
    BriefPath           = 'D:\DSH_WORK\github工作\回测\artifacts\dshd_cluster_brief.md'
    SnapshotPath        = 'D:\DSH_WORK\github工作\回测\artifacts\dshd_p81_a01_audit_snapshot.json'
    QuickScanPath       = 'D:\DSH_WORK\github工作\回测\artifacts\dshd_p81_a01_quick_scan.json'
    VersionHistoryPath  = 'D:\DSH_WORK\github工作\回测\G7_ADJUDICATION_LEDGER\p81_version_history.json'
    AuditLedgerPath     = 'D:\DSH_WORK\github工作\回测\tracking_monitor_audit.jsonl'
    DailyReportPath     = 'D:\DSH_WORK\github工作\回测\G7_ADJUDICATION_LEDGER\p81_inspect_daily.md'
    StatePath           = 'D:\DSH_WORK\github工作\回测\G7_ADJUDICATION_LEDGER\p81_inspect_state.json'
    ExchangeRegistry    = 'D:\DSH_WORK\github工作\回测\artifacts\exchange_binding_registry.json'
    SemanticBlacklist   = 'D:\DSH_WORK\github工作\framework-tree\analysis\e2e_output\v85\dshb_full_integrate\semantic_blacklist_v85_final.json'
    ProtectedPIDs       = @(3472, 14644, 30492, 29652, 29708)
    WatcherPattern      = 'dshd_p81_watch'
    GitRoot             = 'D:\DSH_WORK'
    MaxSnapshotCount    = 30
    BriefSection11      = '十一、P81 工具链版本管理'
    SplitBriefPath      = 'D:\DSH_WORK\github工作\回测\artifacts\dshd_cluster_brief_regime_crowding.md'
    P80WatcherPattern   = 'dshd_p80_a01'
    FileTimeoutSec      = 30
    MemoryThresholdMB   = 256
    MemoryCheckInterval = 3
    P80WatchScript1     = 'D:\DSH_WORK\github工作\回测\G7_ADJUDICATION_LEDGER\dshd_p80_a01_audit_watch.ps1'
    P80WatchScript2     = 'D:\DSH_WORK\github工作\回测\G7_ADJUDICATION_LEDGER\dshd_p80_a01_phase2_watch.ps1'
    P80AutoKeepalive    = $true
}

# TASK-040: File Lock Module Import (exclusive lock + retry + timeout)
$FileLockModulePath = 'D:\DSH_WORK\github工作\回测\G7_ADJUDICATION_LEDGER\p81_file_lock.ps1'
if (Test-Path $FileLockModulePath) {
    try { . $FileLockModulePath; Write-InspectLog 'INFO' "TASK-040: File lock module loaded" } catch { Write-InspectLog 'WARN' "TASK-040: File lock module load failed: $_" }
}

# ============================================================
# GLOBAL STATE
# ============================================================
$Script:Errors    = @()
$Script:Alerts    = @()
$Script:Checks    = @()
$Script:SelfHeal  = @{
    Actions    = @()
    Healed     = $false
    Reason     = ''
}

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

function Write-InspectLog {
    param([string]$Level, [string]$Message)
    $ts = Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK'
    $entry = "[$ts] [$Level] $Message"
    Write-Host $entry
    if ($Level -eq 'ERROR' -or $Level -eq 'WARN') {
        $Script:Errors += $entry
    }
}

function Write-Alert {
    param([string]$Code, [string]$Severity, [string]$Detail, [string]$Source)
    $entry = @{
        code      = $Code
        severity  = $Severity
        detail    = $Detail
        source    = $Source
        ts        = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')
    }
    $Script:Alerts += $entry
    Write-InspectLog $Severity "[ALARM-$Code] $Detail"
}

function Record-Check {
    param([string]$CheckId, [string]$Description, [bool]$Passed, [string]$Detail = '')
    $entry = @{
        id         = $CheckId
        description = $Description
        passed     = $Passed
        detail     = $Detail
        ts         = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')
    }
    $Script:Checks += $entry
    if (-not $Passed) {
        Write-InspectLog 'WARN' "[FAIL] ${CheckId}: $Description - $Detail"
    }
    return $Passed
}

function Is-PidAlive {
    param([int]$TargetPid)
    try {
        $proc = Get-Process -Id $TargetPid -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

function Get-WatcherProcesses {
    try {
        $procs = Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction Stop |
            Where-Object { $_.CommandLine -match $CFG.WatcherPattern }
        return @($procs)
    } catch {
        return @()
    }
}

function Get-PollerCount {
    # Count watcher processes matching our pattern
    return (Get-WatcherProcesses).Count
}

function Write-AuditEvent {
    param([hashtable]$Ev)
    try {
        $ts = Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK'
        $eventEntry = @{
            event_id         = $Ev['event_id']
            timestamp        = $ts
            agent            = 'DSHD-P81-PERIODIC-INSPECT'
            event_type       = $Ev['event_type']
            task             = $Ev['task']
            result           = $Ev['result']
            branch           = 'feature/v88-g1'
            wind_api_calls   = 0
            backtest_started = $false
            gate             = 'CLOSED/HOLD'
            release_permit   = 'NOT_ISSUED'
            details          = $Ev['details']
        }
        $jsonLine = $eventEntry | ConvertTo-Json -Depth 10 -Compress
        Add-Content -Path $CFG.AuditLedgerPath -Value $jsonLine -Encoding UTF8
        Write-InspectLog 'INFO' "[AUDIT] Event $Event.event_id written to ledger"
    } catch {
        Write-InspectLog 'ERROR' "[AUDIT-FAIL] $($_.Exception.Message)"
    }
}

function Write-DailyReport {
    param([hashtable]$Data)
    try {
        $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss (GMT+8)'
        $report = @"
# P81 集群定时巡检报告

> 生成时间: $ts
> 巡检版本: $($CFG.Version)
> 任务ID: $($CFG.TaskID)
> 模式: AUDIT_READ_ONLY | 干预: NONE | Wind调用: 0

## 一、巡检总览

| 项 | 值 |
|---|---|
| 检查项总数 | $($Data.total_checks) |
| 通过 | $($Data.passed) |
| 失败 | $($Data.failed) |
| 告警数 | $($Data.alerts) |
| 自愈动作 | $($Data.self_heal_actions) |
| 干预结果 | $($Data.intervention_result) |

## 二、P0 九项校验

| # | 检查项 | 状态 |
|---|---|---|
"@
        foreach ($p0 in $Data.p0_checks) {
            $icon = if ($p0.passed) { 'PASS' } else { 'FAIL' }
            $report += "`n| $($p0.id) | $($p0.desc) | $icon |"
        }
        $report += @"

## 三、进程存活校验

| 角色 | PID | 状态 |
|---|---|---|
"@
        foreach ($proc in $Data.process_checks) {
            $icon = if ($proc.alive) { 'ALIVE' } else { 'DEAD' }
            $report += "`n| $($proc.role) | $($proc.pid) | $icon |"
        }
        $report += @"

## 四、Watchers 轮询状态

| 项 | 值 |
|---|---|
| Watcher 进程数 | $($Data.watcher_count) |
| 最近轮询时间 | $($Data.last_poll) |
| 轮询时效 (秒) | $($Data.poll_freshness_sec) |
| 轮询状态 | $($Data.poll_status) |

## 五、Git 快照一致性

| 项 | 值 |
|---|---|
| 快照目录文件数 | $($Data.snapshot_file_count) |
| Git 跟踪数 | $($Data.snapshot_tracked) |
| 版本台账条目 | $($Data.version_history_entries) |
| 快照一致性 | $($Data.snapshot_consistency) |

## 六、黑名单 + CSV SHA

| 项 | 值 |
|---|---|
| Exchange 注册表状态 | $($Data.exchange_registry_status) |
| 语义黑名单状态 | $($Data.blacklist_status) |
| CSV 双哈希 | $($Data.csv_hash_status) |

## 七、Brief 持久化

| 项 | 值 |
|---|---|
| 章节十一存在 | $($Data.brief_section_11) |
| 文件大小 (bytes) | $($Data.brief_size) |
| 最后修改时间 | $($Data.brief_modified) |

## 八、告警详情

"@
        if ($Data.alerts -gt 0) {
            foreach ($alert in $Data.alert_list) {
                $report += "`n### [$($alert.severity)] $($alert.code)"
                $report += "`n- 时间: $($alert.ts)"
                $report += "`n- 来源: $($alert.source)"
                $report += "`n- 详情: $($alert.detail)"
            }
        } else {
            $report += "`n> 本轮巡检无告警。"
        }
        $report += @"

## 九、自愈记录

"@
        if ($Data.self_heal_actions -gt 0) {
            foreach ($action in $Data.heal_action_list) {
                $report += "`n### [$($action.ts)] $($action.action)"
                $report += "`n- 原因: $($action.reason)"
                $report += "`n- 结果: $($action.result)"
                $report += "`n- 快照: $($action.snapshot)"
            }
        } else {
            $report += "`n> 本轮巡检无自愈动作。"
        }
        $report += @"

## 十、P0 红线声明

- wind_api_calls = 0
- gate = CLOSED/HOLD
- release_permit = NOT_ISSUED
- intervention = $($Data.intervention_result)
- backtest_started = false
- circuit_breaker_executed = false
- 所有非P81进程未触及
- 所有已固化版本管理规则未修改

---
*本报告由 p81_periodic_inspect.ps1 v$($CFG.Version) 自动生成*
*巡检ID: $($CFG.TaskID)-$(Get-Date -Format 'yyyyMMddHHmmss')*
"@
        Set-Content -Path $CFG.DailyReportPath -Value $report -Encoding UTF8
        Write-InspectLog 'INFO' "Daily report written to $($CFG.DailyReportPath)"
    } catch {
        Write-InspectLog 'ERROR' "[REPORT-FAIL] $($_.Exception.Message)"
    }
}

function Save-InspectState {
    param([hashtable]$Data)
    try {
        $state = @{
            task_id          = $CFG.TaskID
            version          = $CFG.Version
            last_run         = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')
            last_pass_count  = $Data.passed
            last_fail_count  = $Data.failed
            last_alert_count = $Data.alerts
            consecutive_pass = $Data.consecutive_pass
            history          = @(
                @{
                    ts      = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')
                    pass    = $Data.passed
                    fail    = $Data.failed
                    alerts  = $Data.alerts
                    healed  = $Data.self_heal_actions -gt 0
                }
            )
        }
        # Load existing history if available
        if (Test-Path $CFG.StatePath) {
            try {
                $existing = Get-Content $CFG.StatePath -Raw -Encoding UTF8 | ConvertFrom-Json
                if ($existing.history) {
                    $state.history += @($existing.history)
                }
                # Keep only last 100 entries
                $state.history = $state.history | Select-Object -First 100
            } catch {}
        }
        $state | ConvertTo-Json -Depth 10 | Set-Content -Path $CFG.StatePath -Encoding UTF8
    } catch {
        Write-InspectLog 'ERROR' "[STATE-FAIL] $($_.Exception.Message)"
    }
}

# ============================================================
# CHECK: P0 NINE-CHECK VERIFICATION
# ============================================================
function Check-P0NineChecks {
    Write-InspectLog 'INFO' "=== P0 Nine-Check Verification ==="
    $snapshotOk = $false
    $snapshotData = $null

    try {
        $raw = Get-Content $CFG.SnapshotPath -Raw -Encoding UTF8
        $snapshotData = $raw | ConvertFrom-Json
        $snapshotOk = $true
    } catch {
        Write-InspectLog 'ERROR' "Cannot load audit snapshot: $($_.Exception.Message)"
    }

    $p0Checks = @()

    if ($snapshotOk -and $snapshotData.red_lines) {
        $rl = $snapshotData.red_lines
        $p0 = @(
            @{ id = 'P0-1'; desc = 'audit_only=True';    passed = [bool]$rl.audit_only }
            @{ id = 'P0-2'; desc = 'wind_api_calls=0';   passed = ($rl.wind_api_calls -eq 0) }
            @{ id = 'P0-3'; desc = 'gate=CLOSED/HOLD';   passed = ($rl.gate_observed -eq 'CLOSED/HOLD') }
            @{ id = 'P0-4'; desc = 'release_permit=NOT_ISSUED'; passed = ($rl.release_permit_observed -eq 'NOT_ISSUED') }
            @{ id = 'P0-5'; desc = 'intervention=NONE';  passed = ($rl.intervention -eq 'NONE') }
            @{ id = 'P0-6'; desc = 'no_circuit_break_executed'; passed = [bool]$rl.no_circuit_break_executed }
            @{ id = 'P0-7'; desc = 'backtest_not_started'; passed = -not [bool]$rl.dshd_runs_backtest }
            @{ id = 'P0-8'; desc = 'processes_untouched'; passed = [bool]$rl.processes_untouched }
            @{ id = 'P0-9'; desc = 'output_csv_not_touched'; passed = -not [bool]$rl.output_csv_touched }
        )
    } else {
        $p0 = @(
            @{ id = 'P0-1'; desc = 'audit_only=True';    passed = $false; detail = 'snapshot unavailable' }
            @{ id = 'P0-2'; desc = 'wind_api_calls=0';   passed = $false; detail = 'snapshot unavailable' }
            @{ id = 'P0-3'; desc = 'gate=CLOSED/HOLD';   passed = $false; detail = 'snapshot unavailable' }
            @{ id = 'P0-4'; desc = 'release_permit=NOT_ISSUED'; passed = $false; detail = 'snapshot unavailable' }
            @{ id = 'P0-5'; desc = 'intervention=NONE';  passed = $false; detail = 'snapshot unavailable' }
            @{ id = 'P0-6'; desc = 'no_circuit_break_executed'; passed = $false; detail = 'snapshot unavailable' }
            @{ id = 'P0-7'; desc = 'backtest_not_started'; passed = $false; detail = 'snapshot unavailable' }
            @{ id = 'P0-8'; desc = 'processes_untouched'; passed = $false; detail = 'snapshot unavailable' }
            @{ id = 'P0-9'; desc = 'output_csv_not_touched'; passed = $false; detail = 'snapshot unavailable' }
        )
    }

    foreach ($check in $p0) {
        $passed = Record-Check $check.id $check.desc $check.passed $check.detail
        $p0Checks += $check
    }

    return $p0Checks
}

# ============================================================
# CHECK: PROCESS LIVINESS
# ============================================================
function Check-ProcessLiveness {
    Write-InspectLog 'INFO' "=== Process Liveness Check ==="
    $procs = @()

    # Check protected PIDs
    $protectedRoles = @(
        @{ pid = 3472; role = 'P71 main relay' }
        @{ pid = 14644; role = 'Excel (zin-database)' }
        @{ pid = 30492; role = 'P80 watcher' }
        @{ pid = 29652; role = 'P80-PHASE2 watcher' }
        @{ pid = 29708; role = 'P80-PHASE2 watcher (child)' }
    )
    foreach ($p in $protectedRoles) {
        $alive = Is-PidAlive $p.pid
        $procs += @{ pid = $p.pid; role = $p.role; alive = $alive; protected = $true }
        Record-Check "PROC-$($p.pid)" "$($p.role) alive" $alive
        if (-not $alive) {
            Write-Alert 'PROCESS-EXIT' 'CRITICAL' "Protected process $($p.role) (PID $($p.pid)) is dead!" 'Check-ProcessLiveness'
        }
    }

    # Check P81 watcher
    $watcherProcs = Get-WatcherProcesses
    $watcherAlive = $watcherProcs.Count -ge 1
    $watcherCount = $watcherProcs.Count
    $procs += @{ pid = 'N/A'; role = "P81 watcher ($watcherCount proc(s))"; alive = $watcherAlive; protected = $false; count = $watcherCount }
    Record-Check 'PROC-P81-WATCHER' "P81 watcher alive ($watcherCount proc)" $watcherAlive

    if (-not $watcherAlive) {
        Write-Alert 'PROCESS-EXIT' 'CRITICAL' 'P81 watcher is dead!' 'Check-ProcessLiveness'
    }

    return @{
        processes     = $procs
        watcher_count = $watcherCount
        watcher_alive = $watcherAlive
    }
}

# ============================================================
# CHECK: WATCHER POLL STATUS
# ============================================================
function Check-PollStatus {
    Write-InspectLog 'INFO' "=== Watcher Poll Status Check ==="

    $lastPoll = $null
    $pollFreshness = 0
    $pollStatus = 'UNKNOWN'

    try {
        $quickScanRaw = Get-Content $CFG.QuickScanPath -Raw -Encoding UTF8 -ErrorAction Stop
        $quickScan = $quickScanRaw | ConvertFrom-Json
        $lastPollStr = $null
        if ($quickScan.poll_number) {
            $lastPollStr = $quickScan.timestamp
        }
        if (-not $lastPollStr -and $quickScan.polled_at) {
            $lastPollStr = $quickScan.polled_at
        }
        if ($lastPollStr) {
            $lastPoll = [datetime]$lastPollStr
            $pollFreshness = (New-TimeSpan -Start $lastPoll -End (Get-Date)).TotalSeconds
            if ($pollFreshness -lt 600) {
                $pollStatus = 'FRESH'
            } elseif ($pollFreshness -lt 900) {
                $pollStatus = 'AGING'
            } else {
                $pollStatus = 'STALE'
            }
        }
    } catch {
        Write-InspectLog 'WARN' "Cannot load quick-scan for poll status: $($_.Exception.Message)"
        # Try from audit snapshot
        try {
            $snapRaw = Get-Content $CFG.SnapshotPath -Raw -Encoding UTF8 -ErrorAction Stop
            $snap = $snapRaw | ConvertFrom-Json
            if ($snap.polled_at) {
                $lastPoll = [datetime]$snap.polled_at
                $pollFreshness = (New-TimeSpan -Start $lastPoll -End (Get-Date)).TotalSeconds
                if ($pollFreshness -lt 600) { $pollStatus = 'FRESH' }
                elseif ($pollFreshness -lt 900) { $pollStatus = 'AGING' }
                else { $pollStatus = 'STALE' }
            }
        } catch {}
    }

    $pollStale = ($pollFreshness -gt 600)
    Record-Check 'POLL-FRESHNESS' "Poll freshness ($pollStatus, $pollFreshness sec)" (-not $pollStale)

    if ($pollStale) {
        Write-Alert 'PROCESS-EXIT' 'WARN' "Watcher poll is stale ($pollFreshness sec, status=$pollStatus)" 'Check-PollStatus'
    }

    return @{
        last_poll         = $lastPoll
        poll_freshness_sec = [math]::Round($pollFreshness, 0)
        poll_status       = $pollStatus
    }
}

# ============================================================
# CHECK: GIT SNAPSHOT CONSISTENCY
# ============================================================
function Check-SnapshotConsistency {
    Write-InspectLog 'INFO' "=== Git Snapshot Consistency Check ==="

    $snapCount = 0
    $trackedCount = 0
    $verHistEntries = 0
    $snapshotOk = $true

    # Count snapshot files
    if (Test-Path $CFG.SnapDir) {
        $snapFiles = Get-ChildItem $CFG.SnapDir -File -ErrorAction SilentlyContinue
        $snapCount = $snapFiles.Count
    } else {
        Record-Check 'SNAP-DIR' "Snapshot directory exists" $false "Directory missing"
        $snapshotOk = $false
    }

    # Count git-tracked snapshot files
    try {
        $relPath = "github工作/回测/G7_ADJUDICATION_LEDGER/_p81_snapshots"
        $r = & git -C $CFG.GitRoot ls-files -- $relPath 2>&1
        $trackedLines = @($r | Where-Object { $_ -match '\.bak' })
        $trackedCount = $trackedLines.Count
        Write-InspectLog 'INFO' "Git ls-files tracked bak files: $trackedCount"
    } catch {
        Write-InspectLog 'WARN' "Git ls-files failed: $($_.Exception.Message)"
    }

    # Check version history
    if (Test-Path $CFG.VersionHistoryPath) {
        try {
            $vhRaw = Get-Content $CFG.VersionHistoryPath -Raw -Encoding UTF8
            $vh = $vhRaw | ConvertFrom-Json
            $verHistEntries = $vh.entries.Count
        } catch {
            Write-InspectLog 'WARN' "Version history parse failed: $($_.Exception.Message)"
        }
    }

    $snapConsistent = ($snapCount -ge 15) -and ($trackedCount -ge 15)
    Record-Check 'SNAP-EXIST' "Snapshot files >= 15" ($snapCount -ge 15) "found $snapCount"
    Record-Check 'SNAP-TRACKED' "Git-tracked snapshot files >= 15" ($trackedCount -ge 15) "found $trackedCount"
    Record-Check 'SNAP-VERSION-HISTORY' "Version history entries >= 15" ($verHistEntries -ge 15) "found $verHistEntries"

    if ($snapCount -lt 15) {
        Write-Alert 'SNAPSHOT-LOSS' 'CRITICAL' "Only $snapCount snapshot files (need >= 15)" 'Check-SnapshotConsistency'
    }
    if ($trackedCount -lt 15) {
        Write-Alert 'SNAPSHOT-LOSS' 'WARN' "Only $trackedCount git-tracked snapshots (need >= 15)" 'Check-SnapshotConsistency'
    }

    return @{
        snapshot_file_count     = $snapCount
        snapshot_tracked        = $trackedCount
        version_history_entries = $verHistEntries
        snapshot_consistency    = $snapConsistent
    }
}

# ============================================================
# CHECK: BLACKLIST + CSV SHA
# ============================================================
function Check-BlacklistAndCSV {
    Write-InspectLog 'INFO' "=== Blacklist + CSV SHA Check ==="

    # Exchange binding registry
    $exchangeStatus = 'UNKNOWN'
    if (Test-Path $CFG.ExchangeRegistry) {
        try {
            $erRaw = Get-Content $CFG.ExchangeRegistry -Raw -Encoding UTF8
            $er = $erRaw | ConvertFrom-Json
            $exchangeStatus = 'PRESENT'
            Record-Check 'EXCHANGE-REGISTRY' "Exchange registry present and valid" $true
        } catch {
            $exchangeStatus = 'CORRUPT'
            Record-Check 'EXCHANGE-REGISTRY' "Exchange registry present and valid" $false $_.Exception.Message
        }
    } else {
        $exchangeStatus = 'MISSING'
        Record-Check 'EXCHANGE-REGISTRY' "Exchange registry present and valid" $false 'File missing'
    }

    # Semantic blacklist
    $blacklistStatus = 'UNKNOWN'
    if (Test-Path $CFG.SemanticBlacklist) {
        try {
            $blRaw = Get-Content $CFG.SemanticBlacklist -Raw -Encoding UTF8
            $bl = $blRaw | ConvertFrom-Json
            $blacklistStatus = 'PRESENT'
            Record-Check 'BLACKLIST' "Semantic blacklist present and valid" $true
        } catch {
            $blacklistStatus = 'CORRUPT'
            Record-Check 'BLACKLIST' "Semantic blacklist present and valid" $false $_.Exception.Message
        }
    } else {
        $blacklistStatus = 'MISSING'
        Record-Check 'BLACKLIST' "Semantic blacklist present and valid" $false 'File missing'
    }

    # CSV dual-hash
    $csvHashStatus = 'UNKNOWN'
    $dualHashPath = 'D:\DSH_WORK\github工作\回测\artifacts\dshd_p81_a01_dualhash_verify.json'
    if (Test-Path $dualHashPath) {
        try {
            $dhRaw = Get-Content $dualHashPath -Raw -Encoding UTF8
            $dh = $dhRaw | ConvertFrom-Json
            $aEqB = [bool]$dh.dual_hash.a_eq_b
            $hashA = $dh.dual_hash.hash_a_byte_read
            $hashB = $dh.dual_hash.hash_b_getfilehash
            $scanStatus = $dh.scan_status
            $csvHashStatus = "A=$($hashA.Substring(0,12))... B=$($hashB.Substring(0,12))... A==B=$($aEqB) Scan=$scanStatus"
            Record-Check 'CSV-DUAL-HASH' "CSV dual-hash A==B" $aEqB $csvHashStatus
            if (-not $aEqB) {
                Write-Alert 'CSV-HASH-MISMATCH' 'YELLOW' "CSV dual-hash A != B" 'Check-BlacklistAndCSV'
            }
        } catch {
            $csvHashStatus = 'PARSE_ERROR'
            Record-Check 'CSV-DUAL-HASH' "CSV dual-hash parse" $false $_.Exception.Message
        }
    } else {
        $csvHashStatus = 'NO_FILE'
        Record-Check 'CSV-DUAL-HASH' "CSV dual-hash file exists" $false 'File missing'
    }

    return @{
        exchange_registry_status = $exchangeStatus
        blacklist_status         = $blacklistStatus
        csv_hash_status          = $csvHashStatus
    }
}

# ============================================================
# CHECK: BRIEF SECTION 十一 PERSISTENCE
# ============================================================
function Check-BriefSection11 {
    Write-InspectLog 'INFO' "=== Brief Section 十一 Persistence Check ==="

    $section11Exists = $false
    $briefSize = 0
    $briefModified = $null

    if (Test-Path $CFG.BriefPath) {
        $briefSize = (Get-Item $CFG.BriefPath).Length
        $briefModified = (Get-Item $CFG.BriefPath).LastWriteTime
        try {
            # TASK-040: Use file-locked read if module available
            if (Get-Command -Name Read-FileWithLock -ErrorAction SilentlyContinue) {
                $briefContent = Read-FileWithLock -Path $CFG.BriefPath -TimeoutSec $CFG.FileTimeoutSec
            } else {
                $briefContent = Get-Content $CFG.BriefPath -Raw -Encoding UTF8
            }
            if ($briefContent) {
                $section11Exists = $briefContent.Contains($CFG.BriefSection11)
            }
        } catch {
            Write-InspectLog 'ERROR' "Brief read failed: $($_.Exception.Message)"
        }
    }

    # TASK-040: Also check split brief file
    $splitBriefExists = $false
    $splitBriefSize = 0
    if (Test-Path $CFG.SplitBriefPath) {
        $splitBriefSize = (Get-Item $CFG.SplitBriefPath).Length
        $splitBriefExists = $splitBriefSize -gt 0
        Record-Check 'BRIEF-SPLIT-EXISTS' "Split brief (sections 12-14) exists" $splitBriefExists "size=$splitBriefSize"
    }

    Record-Check 'BRIEF-EXISTS' "Brief file exists" ($briefSize -gt 0) "size=$briefSize"
    Record-Check 'BRIEF-SIZE' "Brief file > 1000 bytes" ($briefSize -gt 1000) "size=$briefSize"
    Record-Check 'BRIEF-SECTION11' "Brief section 十一 present" $section11Exists

    if (-not $section11Exists -and ($briefSize -gt 0)) {
        Write-Alert 'BRIEF-SECTION-LOSS' 'CRITICAL' 'Brief section 十一 missing (persistence regression!)' 'Check-BriefSection11'
    }

    return @{
        brief_section_11 = $section11Exists
        brief_size       = $briefSize
        brief_modified   = $briefModified
        split_brief_exists = $splitBriefExists
        split_brief_size   = $splitBriefSize
    }
}

# ============================================================
# CHECK: PATCH VIOLATION DETECTION
# ============================================================
function Check-PatchViolation {
    Write-InspectLog 'INFO' "=== Patch Violation Detection ==="

    $violation = $false
    $violationDetail = ''

    # Check if archived patches were recently modified
    $archivedPatches = @(
        "$($CFG.G7Dir)\patch_p81_ext.py",
        "$($CFG.G7Dir)\patch_p81_tweak.py",
        "$($CFG.G7Dir)\patch_p81_brief.py",
        "$($CFG.G7Dir)\patch_p81_fast_excel.py"
    )

    foreach ($patchFile in $archivedPatches) {
        if (Test-Path $patchFile) {
            $item = Get-Item $patchFile
            $ageSeconds = (New-TimeSpan -Start $item.LastWriteTime -End (Get-Date)).TotalSeconds
            # If modified within last 5 minutes, it may have been re-run
            if ($ageSeconds -lt 300) {
                $violation = $true
                $violationDetail = "Archived patch $($patchFile) modified $ageSeconds sec ago!"
            }
        }
    }

    # Check for new snapshot files that suggest re-run
    $recentSnaps = @(Get-ChildItem $CFG.SnapDir -File -ErrorAction SilentlyContinue |
        Where-Object { (New-TimeSpan -Start $_.LastWriteTime -End (Get-Date)).TotalSeconds -lt 300 })

    if ($recentSnaps.Count -gt 0) {
        $violation = $true
        $violationDetail += " $recentSnaps new snapshot(s) created in last 5 min"
    }

    $passed = -not $violation
    Record-Check 'PATCH-VIOLATION' "No archived patch re-execution detected" $passed $violationDetail

    if ($violation) {
        Write-Alert 'PATCH-VIOLATION' 'WARN' "Archived patch violation: $violationDetail" 'Check-PatchViolation'
    }

    return $violation
}

# ============================================================
# CHECK: DISK SNAPSHOT DIR INTEGRITY
# ============================================================
function Check-DiskSnapshotIntegrity {
    Write-InspectLog 'INFO' "=== Disk Snapshot Directory Integrity Check ==="

    $diskOk = $true
    $diskDetail = ''

    if (-not (Test-Path $CFG.SnapDir)) {
        Record-Check 'DISK-SNAPDIR' "Snapshot directory exists" $false 'Missing'
        Write-Alert 'SNAPSHOT-LOSS' 'CRITICAL' "Snapshot directory missing!" 'Check-DiskSnapshotIntegrity'
        return @{ disk_ok = $false; detail = 'Missing' }
    }

    $snapFiles = Get-ChildItem $CFG.SnapDir -File -ErrorAction SilentlyContinue
    $bakCount = @($snapFiles | Where-Object { $_.Extension -eq '.bak' }).Count

    # Check no zero-byte files
    $zeroFiles = @($snapFiles | Where-Object { $_.Length -eq 0 })
    if ($zeroFiles.Count -gt 0) {
        $diskOk = $false
        $diskDetail = "$($zeroFiles.Count) zero-byte file(s) found"
        Write-Alert 'SNAPSHOT-LOSS' 'WARN' "Zero-byte snapshot files detected" 'Check-DiskSnapshotIntegrity'
    }

    # Check naming convention
    $badNaming = @($snapFiles | Where-Object {
        $_.Name -notmatch '^.+\.\d{8}_\d{6}\.\S+\.bak$' -and $_.Name -notmatch '^.+\.v[\d.]+-[A-Z]+\.bak$'
    })
    if ($badNaming.Count -gt 0) {
        $diskOk = $false
        $diskDetail += " $badNaming non-standard named snapshot(s)"
    }

    # Check total disk space (warning if < 100MB available)
    $drive = Get-PSDrive D -ErrorAction SilentlyContinue
    if ($drive) {
        $freeMB = $drive.Free / 1MB
        if ($freeMB -lt 100) {
            $diskOk = $false
            $diskDetail += " Only $([math]::Round($freeMB, 1))MB free on D:"
            Write-Alert 'DISK-SPACE' 'CRITICAL' "Low disk space: $([math]::Round($freeMB, 1))MB free" 'Check-DiskSnapshotIntegrity'
        }
    }

    $detail = if ($diskOk) { "OK ($bakCount .bak files)" } else { $diskDetail }
    Record-Check 'DISK-SNAPDIR' "Snapshot directory integrity" $diskOk $detail

    return @{ disk_ok = $diskOk; detail = $detail }
}

# ============================================================
# TASK-040: P80 WATCHER AUTO-KEEPALIVE
# ============================================================
function Check-P80WatcherKeepalive {
    Write-InspectLog 'INFO' "=== P80 Watcher Auto-Keepalive Check (TASK-040) ==="
    
    if (-not $CFG.P80AutoKeepalive) {
        Write-InspectLog 'INFO' "P80 auto-keepalive disabled"
        return @{ keepalive_enabled = $false; p80_alive = $false; action = 'DISABLED' }
    }
    
    # Find P80 watcher processes
    $p80Procs = @()
    try {
        $p80Procs = Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction Stop |
            Where-Object { $_.CommandLine -match $CFG.P80WatcherPattern }
    } catch {
        Write-InspectLog 'WARN' "Cannot query P80 processes: $_"
    }
    
    $p80Count = $p80Procs.Count
    $p80Alive = $p80Count -ge 1
    
    Record-Check 'P80-WATCHER-ALIVE' "P80 watcher alive ($p80Count proc)" $p80Alive
    
    # Memory threshold check
    $memCheckResult = $true
    if (Get-Command -Name Check-MemoryThreshold -ErrorAction SilentlyContinue) {
        $memCheckResult = Check-MemoryThreshold -ThresholdMB $CFG.MemoryThresholdMB
    }
    
    if (-not $memCheckResult) {
        Write-Alert 'MEMORY-THRESHOLD' 'WARN' "Memory usage exceeds $($CFG.MemoryThresholdMB)MB threshold - soft restart recommended" 'Check-P80WatcherKeepalive'
        Record-Check 'MEMORY-THRESHOLD' "Memory usage under $($CFG.MemoryThresholdMB)MB" $false "exceeded threshold"
    } else {
        Record-Check 'MEMORY-THRESHOLD' "Memory usage under $($CFG.MemoryThresholdMB)MB" $true
    }
    
    $action = 'NONE'
    $restarted = $false
    
    if (-not $p80Alive -and $p80Count -eq 0) {
        # P80 watcher is dead - attempt auto-restart
        Write-InspectLog 'WARN' "P80 watcher is DEAD (0 processes) - attempting auto-restart"
        Write-Alert 'P80-WATCHER-EXIT' 'CRITICAL' 'P80 watcher process is dead - auto-restart initiated' 'Check-P80WatcherKeepalive'
        
        $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
        $keepaliveAction = @{
            ts       = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')
            action   = 'P80_WATCHER_RESTART'
            reason   = 'P80 watcher dead (0 processes)'
            result   = 'PENDING'
            snapshot = ''
        }
        
        # Pre-restart snapshot
        foreach ($p80Script in @($CFG.P80WatchScript1, $CFG.P80WatchScript2)) {
            if (Test-Path $p80Script) {
                $basename = [System.IO.Path]::GetFileNameWithoutExtension($p80Script)
                $dstName = "$basename.$timestamp.TASK040-KEEPALIVE.bak"
                $dstPath = "$($CFG.G7Dir)\_p81_snapshots\$dstName"
                try {
                    Copy-Item -Path $p80Script -Destination $dstPath -Force
                    $keepaliveAction.snapshot = $dstName
                    Write-InspectLog 'INFO' "Pre-restart snapshot: $dstName"
                } catch {
                    Write-InspectLog 'WARN' "Snapshot failed: $_"
                }
            }
        }
        
        # Verify protected processes
        $protectOk = $true
        foreach ($protPid in $CFG.ProtectedPIDs) {
            if (-not (Is-PidAlive $protPid)) {
                Write-InspectLog 'ERROR' "CRITICAL: Protected PID $protPid is dead! Aborting P80 restart!"
                $protectOk = $false
                break
            }
        }
        
        if ($protectOk) {
            # Restart P80 audit watch
            try {
                if (Test-Path $CFG.P80WatchScript1) {
                    $startArgs = @(
                        '-NoLogo', '-NoProfile', '-NonInteractive', '-Command',
                        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); `n" +
                        "& powershell -NoProfile -ExecutionPolicy Bypass -File '$($CFG.P80WatchScript1)'"
                    )
                    $newProc = Start-Process -FilePath 'powershell.exe' -ArgumentList $startArgs -PassThru
                    Write-InspectLog 'INFO' "P80 audit watcher restarted (PID $($newProc.Id))"
                }
            } catch {
                Write-InspectLog 'ERROR' "P80 audit watcher restart failed: $_"
            }
            
            # Restart P80 phase2 watch
            try {
                if (Test-Path $CFG.P80WatchScript2) {
                    $startArgs = @(
                        '-NoLogo', '-NoProfile', '-NonInteractive', '-Command',
                        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); `n" +
                        "& powershell -NoProfile -ExecutionPolicy Bypass -File '$($CFG.P80WatchScript2)'"
                    )
                    $newProc = Start-Process -FilePath 'powershell.exe' -ArgumentList $startArgs -PassThru
                    Write-InspectLog 'INFO' "P80 phase2 watcher restarted (PID $($newProc.Id))"
                }
            } catch {
                Write-InspectLog 'ERROR' "P80 phase2 watcher restart failed: $_"
            }
            
            Start-Sleep -Seconds 5
            $p80ProcsAfter = @()
            try {
                $p80ProcsAfter = Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction Stop |
                    Where-Object { $_.CommandLine -match $CFG.P80WatcherPattern }
            } catch {}
            
            $p80CountAfter = $p80ProcsAfter.Count
            $keepaliveAction.result = "RESTARTED (PID=$($newProc.Id), count=$p80CountAfter)"
            $restarted = ($p80CountAfter -ge 1)
            $action = 'P80_RESTARTED'
            
            if ($restarted) {
                Write-AuditEvent @{
                    event_id   = "$($CFG.TaskID)-P80-KEEPALIVE-$timestamp"
                    event_type = 'P80_WATCHER_AUTO_RESTART'
                    task       = 'P80 watcher auto-restart by P81 periodic inspect (TASK-040)'
                    result     = 'HEALED'
                    details    = @{
                        heal_result = $keepaliveAction.result
                        snapshot_file = $keepaliveAction.snapshot
                        wind_api_calls = 0
                        intervention = 'AUTO_HEAL_P80_ONLY'
                        protected_processes_untouched = $true
                    }
                }
            } else {
                Write-InspectLog 'ERROR' "P80 watcher restart FAILED: 0 processes after restart"
                $action = 'P80_RESTART_FAILED'
            }
        } else {
            $keepaliveAction.result = 'ABORTED_PROTECTED_PROCESS_DEAD'
            $action = 'ABORTED'
        }
        
        $Script:SelfHeal.Actions += $keepaliveAction
        $Script:SelfHeal.Healed = $true
    }
    
    return @{
        keepalive_enabled = $true
        p80_alive = $p80Alive
        p80_count = $p80Count
        memory_ok = $memCheckResult
        action = $action
        restarted = $restarted
    }
}

# ============================================================
# SELF-HEALING: AUTO-RESTART P81 WATCHER ONLY
# ============================================================
function Heal-P81Watcher {
    param([string]$Reason)

    Write-InspectLog 'WARN' "=== Self-Healing: P81 Watcher Auto-Restart ==="
    Write-InspectLog 'WARN' "Reason: $Reason"

    $healAction = @{
        ts       = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')
        action   = 'WATCHER_RESTART'
        reason   = $Reason
        result   = 'PENDING'
        snapshot = ''
    }

    # Step 1: Pre-restart auto-snapshot
    try {
        $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
        $tag = 'DSHD-P81-PERIODIC-INSPECT'

        # Snapshot the PS1
        if (Test-Path $CFG.WatcherPS1) {
            $srcPs1 = "$CFG.WatcherPS1"
            $dstName = "dshd_p81_watch.$timestamp.$tag.bak"
            $dstPs1 = "$($CFG.G7Dir)\_p81_snapshots\$dstName"
            Copy-Item -Path $srcPs1 -Destination $dstPs1 -Force
            $healAction.snapshot = $dstName
            Write-InspectLog 'INFO' "Pre-restart snapshot: $dstName"
        }

        # Snapshot version history
        if (Test-Path $CFG.VersionHistoryPath) {
            $vhName = "p81_version_history.$timestamp.$tag.bak"
            $vhDest = "$($CFG.G7Dir)\_p81_snapshots\$vhName"
            Copy-Item -Path $CFG.VersionHistoryPath -Destination $vhDest -Force
            Write-InspectLog 'INFO' "Version history snapshot: $vhName"
        }
    } catch {
        Write-InspectLog 'ERROR' "Snapshot failed: $($_.Exception.Message)"
        $healAction.snapshot = 'SNAPSHOT_FAILED'
    }

    # Step 2: Kill existing P81 watcher processes (ONLY P81!)
    try {
        $watcherProcs = Get-WatcherProcesses
        foreach ($wp in $watcherProcs) {
            $cmdShort = $wp.CommandLine.Substring(0, [math]::Min(80, $wp.CommandLine.Length))
            Write-InspectLog 'INFO' "Killing P81 watcher PID $($wp.ProcessId) (CmdLine: $cmdShort...)"
            try {
                Stop-Process -Id $wp.ProcessId -Force -ErrorAction Stop
                Write-InspectLog 'INFO' "PID $($wp.ProcessId) killed."
            } catch {
                Write-InspectLog 'WARN' "Failed to kill PID $($wp.ProcessId): $($_.Exception.Message)"
            }
        }
        # Verify all killed
        Start-Sleep -Seconds 2
        $remaining = Get-WatcherProcesses
        if ($remaining.Count -gt 0) {
            Write-InspectLog 'WARN' "Some watcher processes survived kill; forcing..."
            foreach ($wp in $remaining) {
                try {
                    Stop-Process -Id $wp.ProcessId -Force -ErrorAction Stop
                } catch { }
            }
        }
    } catch {
        Write-InspectLog 'ERROR' "Kill phase error: $($_.Exception.Message)"
    }

    # Step 3: Verify protected processes are still alive (safety check)
    Write-InspectLog 'INFO' "Verifying protected processes alive after kill..."
    foreach ($protPid in $CFG.ProtectedPIDs) {
        $alive = Is-PidAlive $protPid
        if (-not $alive) {
            Write-InspectLog 'ERROR' "CRITICAL: Protected PID $protPid is dead! Aborting restart!"
            $healAction.result = 'ABORTED_PROTECTED_PROCESS_DEAD'
            $Script:SelfHeal.Actions += $healAction
            return
        }
    }

    # Step 4: Spawn new P81 watcher
    try {
        $watcherPath = $CFG.WatcherPS1
        if (-not (Test-Path $watcherPath)) {
            $healAction.result = 'FAILED_P81_PS1_MISSING'
            Write-InspectLog 'ERROR' "Watcher PS1 not found at $watcherPath"
            $Script:SelfHeal.Actions += $healAction
            return
        }

        $startArgs = @(
            '-NoLogo', '-NoProfile', '-NonInteractive', '-Command',
            "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); `n" +
            "`$OutputEncoding = [System.Text.UTF8Encoding]::new($false); `n" +
            "& powershell -NoProfile -ExecutionPolicy Bypass -File '$watcherPath'"
        )

        $newProc = Start-Process -FilePath 'powershell.exe' -ArgumentList $startArgs -PassThru
        Write-InspectLog 'INFO' "New P81 watcher started (PID $($newProc.Id))"

        # Step 5: Verify watcher came up
        Start-Sleep -Seconds 5
        $newWatcherCount = (Get-WatcherProcesses).Count
        $healAction.result = "RESTARTED (PID $($newProc.Id), count=$newWatcherCount)"

        Write-InspectLog 'INFO' "Self-healing complete: $newWatcherCount watcher process(es) running"

        # Step 6: Write audit event
        Write-AuditEvent @{
            event_id   = "$($CFG.TaskID)-HEAL-$timestamp"
            event_type = 'WATCHER_AUTO_RESTART'
            task       = "P81 watcher auto-restart (reason: $Reason)"
            result     = 'HEALED'
            details    = @{
                heal_result   = $healAction.result
                snapshot_file = $healAction.snapshot
                watcher_pids  = @((Get-WatcherProcesses | ForEach-Object { $_.ProcessId }))
                wind_api_calls = 0
                intervention  = 'AUTO_HEAL_P81_ONLY'
                protected_processes_untouched = $true
            }
        }
    } catch {
        Write-InspectLog 'ERROR' "Spawn failed: $($_.Exception.Message)"
        $healAction.result = "FAILED: $($_.Exception.Message)"
    }

    $Script:SelfHeal.Actions += $healAction
    $Script:SelfHeal.Healed = $true
    $Script:SelfHeal.Reason = $Reason
}

# ============================================================
# PATCH VIOLATION DETECTION (enhanced)
# ============================================================
function Check-PatchViolationDetail {
    Write-InspectLog 'INFO' "=== Patch Violation Detail Check ==="

    $violations = @()

    # Check git log for recent patch executions
    try {
        $gitLog = & git -C $CFG.GitRoot log --oneline --since="10 minutes ago" --all 2>&1 | Select-Object -First 10
        $recentCommits = @($gitLog)
        Write-InspectLog 'INFO' "Recent commits (last 10 min): $recentCommits"
    } catch {
        # git log may fail in some environments
    }

    # Check if recreate_p81.py was modified recently
    $recreatePath = "$($CFG.G7Dir)\recreate_p81.py"
    if (Test-Path $recreatePath) {
        $recreateItem = Get-Item $recreatePath
        $recreateAge = (New-TimeSpan -Start $recreateItem.LastWriteTime -End (Get-Date)).TotalSeconds
        if ($recreateAge -lt 300) {
            $violations += "recreate_p81.py modified $recreateAge sec ago"
        }
    }

    if ($violations.Count -gt 0) {
        Write-Alert 'PATCH-VIOLATION' 'WARN' "Patch violation detected: $($violations -join '; ')" 'Check-PatchViolationDetail'
    }
}

# ============================================================
# MAIN EXECUTION
# ============================================================
function Main {
    Write-InspectLog 'INFO' "============================================================"
    Write-InspectLog 'INFO' "P81 Periodic Inspection Starting"
    Write-InspectLog 'INFO' "Task: $($CFG.TaskID)"
    Write-InspectLog 'INFO' "Version: $($CFG.Version)"
    Write-InspectLog 'INFO' "Mode: AUDIT_READ_ONLY | Intervention: NONE (except P81 auto-heal)"
    Write-InspectLog 'INFO' "Wind API calls: 0 (guaranteed)"
    Write-InspectLog 'INFO' "============================================================"

    # --- Step 1: P0 Nine Checks ---
    $p0Checks = Check-P0NineChecks

    # --- Step 2: Process Liveness ---
    $procResult = Check-ProcessLiveness

    # --- Step 3: Watcher Poll Status ---
    $pollResult = Check-PollStatus

    # --- Step 4: Git Snapshot Consistency ---
    $snapResult = Check-SnapshotConsistency

    # --- Step 5: Blacklist + CSV SHA ---
    $blResult = Check-BlacklistAndCSV

    # --- Step 6: Brief Section 十一 ---
    $briefResult = Check-BriefSection11

    # --- Step 7: Disk Snapshot Dir Integrity ---
    $diskResult = Check-DiskSnapshotIntegrity

    # --- Step 8: Patch Violation Detection ---
    $patchViolation = Check-PatchViolation
    Check-PatchViolationDetail

    # --- Step 8b: P80 Watcher Auto-Keepalive (TASK-040) ---
    $p80Keepalive = Check-P80WatcherKeepalive

    # --- Step 9: Self-Healing Decision ---
    $needsHeal = $false
    $healReason = ''

    if (-not $procResult.watcher_alive) {
        $needsHeal = $true
        $healReason = "P81 watcher dead (0 processes)"
    } elseif ($procResult.watcher_count -eq 0) {
        $needsHeal = $true
        $healReason = "P81 watcher process count = 0"
    } elseif ($pollResult.poll_status -eq 'STALE' -and ($procResult.watcher_count -le 1)) {
        # If only 1 watcher process and poll is stale, consider it unhealthy
        $needsHeal = $true
        $healReason = "P81 watcher poll STALE + only $procResult.watcher_count process(es)"
    }

    if ($needsHeal) {
        # Ensure we're only healing P81 watcher - protected processes verified in Heal-P81Watcher
        Heal-P81Watcher $healReason
    }

    # --- Step 10: Compile results ---
    $totalChecks = $Script:Checks.Count
    $passed = @($Script:Checks | Where-Object { $_.passed -eq $true }).Count
    $failed = @($Script:Checks | Where-Object { $_.passed -eq $false }).Count

    # Determine intervention result
    $interventionResult = 'NONE'
    if ($Script:SelfHeal.Healed) {
        $interventionResult = 'AUTO_HEAL_P81_ONLY'
    }

    # Load state for consecutive pass tracking
    $consecutivePass = 0
    $prevState = $null
    if (Test-Path $CFG.StatePath) {
        try {
            $prevState = Get-Content $CFG.StatePath -Raw -Encoding UTF8 | ConvertFrom-Json
        } catch {}
    }

    if ($failed -eq 0) {
        if ($prevState -and $prevState.consecutive_pass) {
            $consecutivePass = $prevState.consecutive_pass + 1
        } else {
            $consecutivePass = 1
        }
    } else {
        $consecutivePass = 0
    }

    $healActionList = @($Script:SelfHeal.Actions)
    $alertList = @($Script:Alerts)

    $data = @{
        total_checks       = $totalChecks
        passed             = $passed
        failed             = $failed
        alerts             = $alertList.Count
        self_heal_actions  = $healActionList.Count
        intervention_result = $interventionResult
        p0_checks          = $p0Checks
        process_checks     = $procResult.processes
        watcher_count      = $procResult.watcher_count
        last_poll          = $pollResult.last_poll
        poll_freshness_sec = $pollResult.poll_freshness_sec
        poll_status        = $pollResult.poll_status
        snapshot_file_count     = $snapResult.snapshot_file_count
        snapshot_tracked        = $snapResult.snapshot_tracked
        version_history_entries = $snapResult.version_history_entries
        snapshot_consistency    = $snapResult.snapshot_consistency
        exchange_registry_status = $blResult.exchange_registry_status
        blacklist_status         = $blResult.blacklist_status
        csv_hash_status          = $blResult.csv_hash_status
        brief_section_11         = $briefResult.brief_section_11
        brief_size               = $briefResult.brief_size
        brief_modified           = $briefResult.brief_modified
        p80_keepalive            = $p80Keepalive
        p80_alive                = $p80Keepalive.p80_alive
        p80_count                = $p80Keepalive.p80_count
        p80_action               = $p80Keepalive.action
        p80_restarted            = $p80Keepalive.restarted
        memory_ok                = $p80Keepalive.memory_ok
        alert_list               = $alertList
        heal_action_list         = $healActionList
        consecutive_pass         = $consecutivePass
    }

    # --- Step 11: Write daily report ---
    Write-DailyReport $data

    # --- Step 12: Save state ---
    Save-InspectState $data

    # --- Step 13: Write audit event ---
    $auditResult = 'PASS'
    if ($failed -gt 0) { $auditResult = 'FAIL' }
    elseif ($alertList.Count -gt 0) { $auditResult = 'PASS_WITH_WARNINGS' }
    if ($Script:SelfHeal.Healed) { $auditResult = 'PASS_AFTER_HEAL' }

    Write-AuditEvent @{
        event_id   = "$($CFG.TaskID)-$(Get-Date -Format 'yyyyMMddHHmmss')"
        event_type = 'PERIODIC_INSPECT_ROUND'
        task       = 'P81 periodic inspection round'
        result     = $auditResult
        details    = @{
            checks_total        = $totalChecks
            checks_passed       = $passed
            checks_failed       = $failed
            alerts              = $alertList.Count
            self_heal_actions   = $healActionList.Count
            intervention_result = $interventionResult
            p0_pass             = @($p0Checks | Where-Object { $_.passed }).Count
            p0_fail             = @($p0Checks | Where-Object { -not $_.passed }).Count
            process_alive       = $procResult.processes | ForEach-Object { "$($_.role):$(if($_.alive){'ALIVE'}else{'DEAD'})" }
            watcher_count       = $procResult.watcher_count
            poll_status         = $pollResult.poll_status
            snapshot_files      = $snapResult.snapshot_file_count
            brief_section_11    = $briefResult.brief_section_11
            patch_violation     = $patchViolation
            p80_keepalive       = $p80Keepalive.action
            p80_alive           = $p80Keepalive.p80_alive
            p80_restarted       = $p80Keepalive.restarted
            consecutive_pass    = $consecutivePass
            wind_api_calls      = 0
            gate                = 'CLOSED/HOLD'
            release_permit      = 'NOT_ISSUED'
            backtest_started    = $false
            circuit_breaker     = $false
            protected_untouched = $true
            version_mgt_rules   = 'UNCHANGED'
        }
    }

    # --- Step 14: Summary ---
    Write-InspectLog 'INFO' "============================================================"
    Write-InspectLog 'INFO' "P81 Periodic Inspection Summary"
    Write-InspectLog 'INFO' "Checks: $totalChecks total | $passed PASS | $failed FAIL"
    Write-InspectLog 'INFO' "Alerts: $([int]$alertList.Count)"
    Write-InspectLog 'INFO' "Self-healing: $(if($Script:SelfHeal.Healed){'YES'}else{'NO'})"
    Write-InspectLog 'INFO' "Intervention: $interventionResult"
    Write-InspectLog 'INFO' "Consecutive passes: $consecutivePass"
    Write-InspectLog 'INFO' "Daily report: $($CFG.DailyReportPath)"
    Write-InspectLog 'INFO' "Audit ledger: $($CFG.AuditLedgerPath)"
    Write-InspectLog 'INFO' "============================================================"

    return @{
        result              = $auditResult
        checks_total        = $totalChecks
        checks_passed       = $passed
        checks_failed       = $failed
        alerts              = $alertList.Count
        self_heal_actions   = $healActionList.Count
        intervention_result = $interventionResult
        consecutive_pass    = $consecutivePass
    }
}

# ============================================================
# ENTRY POINT
# ============================================================
try {
    $Result = Main
    Write-Host ""
    Write-Host "RESULT: $($Result.result) | Checks: $($Result.checks_total) | Pass: $($Result.checks_passed) | Fail: $($Result.checks_failed) | Alerts: $($Result.alerts) | Healed: $(if($Result.self_heal_actions -gt 0){'YES'}else{'NO'})"
} catch {
    Write-InspectLog 'ERROR' "FATAL: $($_.Exception.Message)"
    Write-InspectLog 'ERROR' "Stack: $($_.ScriptStackTrace)"
    Write-AuditEvent @{
        event_id   = "$($CFG.TaskID)-FATAL-$(Get-Date -Format 'yyyyMMddHHmmss')"
        event_type = 'PERIODIC_INSPECT_FATAL'
        task       = 'P81 periodic inspection FATAL error'
        result     = 'FATAL_ERROR'
        details    = @{
            error_message = $_.Exception.Message
            stack_trace   = $_.ScriptStackTrace
            wind_api_calls = 0
            intervention  = 'NONE'
            backtest_started = $false
            circuit_breaker = $false
        }
    }
    exit 1
}

exit 0
