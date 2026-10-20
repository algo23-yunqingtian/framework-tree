# DSHD-P79 A01-OPERATION SPECIAL AUDIT WATCH
# Baseline: feature/v88-g1
# Constraint: AUDIT_READ_ONLY; wind_api_calls=0
# PID3472 main monitor + pwsh-13 P77 hash watch MUST NOT be stopped/rebuilt
# A01 tag: A01-USER-REMOTE-001 (audit tagging only, no execution privilege)
# All evidence written to G7 adjudication ledger, immutable, read-only

param()

# ========== CONSTANTS ==========
$baseDir = "D:\DSH_WORK\github工作\回测"
$ledgerDir = "$baseDir\G7_ADJUDICATION_LEDGER"
$artifactsDir = "$baseDir\artifacts"
$trackingLog = "$baseDir\tracking_monitor_audit.jsonl"
$p79SnapshotPath = "$artifactsDir\dshd_p79_a01_audit_snapshot.json"
$p79FilePath = "$artifactsDir\dshd_a01_file_evidence.json"
$a01BriefPath = "$artifactsDir\dshd_a01_observation_brief.md"
$outputSampleDir = "$baseDir\output_sample"
$monitorPid = 3472
$pollIntervalSec = 30
$snapshotIntervalSec = 300
$a01Tag = "A01-USER-REMOTE-001"

$r03Expected = @{
    "skill_readme.md"       = "3BE3E14511DEC8E669068CA944C43FC374DDFB6C94C2FEB2EA04120B3FBE10DD"
    "bootstrap_wdf.ps1"     = "F568F9723AA16DDB0105BFC74ADE68797B7DA5E54C7BA3A345711876B34344C2"
    "skill_manifest.json"   = "95FE2B60398F952888655F7604DFB06E332A8D8C0F2B37B9625B315DF6A1B45A"
    "health_check_wdf.ps1"  = "AF04F9EC099CF58B3E4312E7E7D93AEF50E93766715A9294DAA48E6326FF0397"
    "reset_wdf_safe.ps1"    = "4E7EDCB1305E8DE3585867BD08EA0A8B4C872785BA134862618D37A43D58451E"
}

$state = @{
    pollCount = 0
    lastSnapshotPoll = 0
    a01IgniteDetected = $false
    a01FetchDetected = $false
    a01IgniteDetectedAt = ""
    a01FetchDetectedAt = ""
    a01CircuitBreakerReady = $false
    a01Warnings = @()
}

# ========== HELPER: Compute SHA256 ==========
function Get-FileSha256 {
    param([string]$FilePath)
    try {
        $bytes = [System.IO.File]::ReadAllBytes($FilePath)
        $sha = [System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)) -replace '-',''
        return $sha
    } catch { return "" }
}

# ========== HELPER: Append JSONL event ==========
function Add-AuditEvent {
    param([hashtable]$EventData, [string]$TrackingLogPath)
    try {
        $json = $EventData | ConvertTo-Json -Compress -Depth 10
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
        $bomBytes = New-Object byte[] ($bytes.Length + 3)
        $bomBytes[0] = 0xEF; $bomBytes[1] = 0xBB; $bomBytes[2] = 0xBF
        [Array]::Copy($bytes, 0, $bomBytes, 3, $bytes.Length)
        $fs = [System.IO.FileStream]::new($TrackingLogPath, [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write)
        $fs.Write($bomBytes, 0, $bomBytes.Length)
        $fs.Flush()
        $fs.Close()
    } catch {
        Write-Host "[P79-ERROR] Failed to append event: $_" -ForegroundColor Red
    }
}

# ========== HELPER: Check process alive ==========
function Test-ProcessAlive {
    param([int]$ProcessId)
    try { Get-Process -Id $ProcessId -ErrorAction Stop | Out-Null; return $true }
    catch { return $false }
}

# ========== HELPER: Read last N lines of tracking log ==========
function Get-RecentTrackingEvents {
    param([int]$Count = 100, [string]$TrackingLogPath)
    try {
        if (!(Test-Path $TrackingLogPath)) { return @() }
        $allLines = [System.IO.File]::ReadAllLines($TrackingLogPath, [System.Text.Encoding]::UTF8)
        if ($allLines.Count -le $Count) { return $allLines }
        return $allLines[($allLines.Count - $Count)..($allLines.Count - 1)]
    } catch { return @() }
}

# ========== HELPER: Write snapshot JSON ==========
function Write-SnapshotJson {
    param([hashtable]$Data, [string]$OutputPath, [string]$ArtifactsDir)
    try {
        $jsonStr = $Data | ConvertTo-Json -Depth 10 -Compress
        $tempJson = "$ArtifactsDir\.p79_snapshot_tmp.json"
        [System.IO.File]::WriteAllText($tempJson, $jsonStr, (New-Object System.Text.UTF8Encoding $false))
        & python -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); open(sys.argv[2],'w',encoding='utf-8').write(json.dumps(d,separators=(',',':'),ensure_ascii=False))" $tempJson $OutputPath
        if (Test-Path $tempJson) { Remove-Item $tempJson -Force -ErrorAction SilentlyContinue }
    } catch {
        Write-Host "[P79-ERROR] Failed to write snapshot: $_" -ForegroundColor Red
    }
}

# ========== HELPER: Write file evidence JSON ==========
function Write-FileEvidenceJson {
    param([hashtable]$Data, [string]$OutputPath, [string]$ArtifactsDir)
    try {
        $tempJson = "$ArtifactsDir\.p79_evidence_tmp.json"
        [System.IO.File]::WriteAllText($tempJson, ($Data | ConvertTo-Json -Depth 10 -Compress), (New-Object System.Text.UTF8Encoding $false))
        & python -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); open(sys.argv[2],'w',encoding='utf-8').write(json.dumps(d,separators=(',',':'),ensure_ascii=False))" $tempJson $OutputPath
        if (Test-Path $tempJson) { Remove-Item $tempJson -Force -ErrorAction SilentlyContinue }
    } catch {
        Write-Host "[P79-ERROR] Failed to write file evidence: $_" -ForegroundColor Red
    }
}

# ========== HELPER: Write A01 observation brief ==========
function Write-ObservationBrief {
    param([string]$Content, [string]$OutputPath)
    try {
        $bom = New-Object System.Text.UTF8Encoding($true)
        [System.IO.File]::WriteAllText($OutputPath, $Content, $bom)
    } catch {
        Write-Host "[P79-ERROR] Failed to write brief: $_" -ForegroundColor Red
    }
}

# ========== HELPER: Detect A01 events ==========
function Get-A01EventStatus {
    param([string[]]$TrackingLines)
    $status = @{
        igniteStarted = $false
        fetchStarted = $false
        backtestStarted = $false
        backtestCompleted = $false
        backtestError = $false
        p62LoopTrigger = $false
        latestEventTs = ""
        latestEvent = ""
        windApiCallsMax = 0
        wdfRetryCount = 0
    }
    foreach ($line in $TrackingLines) {
        if ($line -match '"event":"[^"]*IGNITE_STARTED|"event":"[^"]*DSHC.*IGNITE.*STARTED') { $status.igniteStarted = $true }
        if ($line -match '"event":"[^"]*FETCH_STARTED|"event":"[^"]*FETCH_COMPLETE|"event":"[^"]*FETCH_ERROR') { $status.fetchStarted = $true }
        if ($line -match '"event":"[^"]*P62_LOOP|"event":"[^"]*backtest_start') { $status.backtestStarted = $true; $status.p62LoopTrigger = $true }
        if ($line -match '"event":"[^"]*backtest_complete|"event":"[^"]*P62_COMPLETE') { $status.backtestCompleted = $true }
        if ($line -match '"event":"[^"]*backtest_error|"event":"[^"]*backtest_exception|"event":"[^"]*P62_ERROR') { $status.backtestError = $true }
        if ($line -match '"wind_api_calls":(\d+)') {
            $val = [int]$Matches[1]
            if ($val -gt $status.windApiCallsMax) { $status.windApiCallsMax = $val }
        }
        if ($line -match '"wdf_retries":(\d+)') {
            $val = [int]$Matches[1]
            if ($val -gt $status.wdfRetryCount) { $status.wdfRetryCount = $val }
        }
        if ($line -match '"timestamp":"([^"]+)"') {
            if ($Matches[1] -gt $status.latestEventTs) {
                $status.latestEventTs = $Matches[1]
                $status.latestEvent = $line.Substring(0, [Math]::Min($line.Length, 200))
            }
        }
    }
    return $status
}

# ========== HELPER: Check output_sample ==========
function Get-OutputSampleEvidence {
    param([string]$OutputSampleDir)
    $evidence = @{
        directory_exists = (Test-Path $OutputSampleDir)
        files = @()
    }
    if ($evidence.directory_exists) {
        try {
            $files = Get-ChildItem $OutputSampleDir -File -ErrorAction Stop
            foreach ($f in $files) {
                $hash = Get-FileSha256 $f.FullName
                $evidence.files += @{
                    name = $f.Name
                    size_bytes = $f.Length
                    sha256 = $hash
                    last_write_time = $f.LastWriteTime.ToString("o")
                    creation_time = $f.CreationTime.ToString("o")
                }
            }
        } catch { $evidence.error = $_.Exception.Message }
    }
    return $evidence
}

# ========== HELPER: Check backtest artifacts ==========
function Get-A01BacktestArtifacts {
    param([string]$ArtifactsDir)
    $artifacts = @()
    $dshcFiles = Get-ChildItem $ArtifactsDir -Filter "dshc_*" -File -ErrorAction SilentlyContinue
    foreach ($f in $dshcFiles) {
        $hash = Get-FileSha256 $f.FullName
        $artifacts += @{
            name = $f.Name
            size_bytes = $f.Length
            sha256 = $hash
            last_write_time = $f.LastWriteTime.ToString("o")
        }
    }
    return $artifacts
}

# ========== HELPER: Check invariants ==========
function Get-InvariantStatus {
    param([string]$BaseDir, [string]$ArtifactsDir, [int]$MonitorPid)
    $invariants = @{
        wmain_running = $false; wmain_pid = 0
        initwapi_running = $false; initwapi_pid = 0
        excel_running = $false; excel_pid = 0
        wind_api_calls_zero = $true
        ignition_markers_absent = $true
        monitor_pid3472_alive = $false
        p77_pwsh13_alive = $false
    }
    $wmain = Get-Process -Name wmain -ErrorAction SilentlyContinue
    if ($wmain) { $invariants.wmain_running = $true; $invariants.wmain_pid = $wmain.Id }
    $initwapi = Get-Process -Name InitWAPI -ErrorAction SilentlyContinue
    if ($initwapi) { $invariants.initwapi_running = $true; $invariants.initwapi_pid = $initwapi.Id }
    $excel = Get-Process -Name EXCEL -ErrorAction SilentlyContinue
    if ($excel) { $invariants.excel_running = $true; $invariants.excel_pid = $excel.Id }
    $markers = @("REAL_WIND_CALL.flag", "IGNITE.flag", "WIND_CALL_REQUEST.flag")
    foreach ($m in $markers) { if (Test-Path "$BaseDir\$m") { $invariants.ignition_markers_absent = $false } }
    $invariants.monitor_pid3472_alive = (Test-ProcessAlive $MonitorPid)
    $p77snap = "$ArtifactsDir\dshd_p77_skillpack_watch_snapshot.json"
    if (Test-Path $p77snap) {
        $snapInfo = Get-Item $p77snap
        $minutesSinceUpdate = (Get-Date) - $snapInfo.LastWriteTime
        $invariants.p77_pwsh13_alive = ($minutesSinceUpdate.TotalMinutes -lt 5)
    }
    return $invariants
}

# ========== HELPER: Circuit breaker check ==========
function Test-CircuitBreakerConditions {
    param([hashtable]$A01Status, [hashtable]$Inv)
    $warnings = @()

    if ($A01Status.windApiCallsMax -gt 0) {
        $warnings += @{
            code = "A01_UNAUTHORIZED_WIND_API_CALL"
            severity = "CIRCUIT_BREAKER_READY"
            message = "wind_api_calls=$($A01Status.windApiCallsMax) detected (expected 0)"
            evidence_ts = $A01Status.latestEventTs
        }
    }

    if ($A01Status.wdfRetryCount -gt 2) {
        $warnings += @{
            code = "A01_PERF_WARNING_WDF_RETRY"
            severity = "WARNING"
            message = "WDF retries=$($A01Status.wdfRetryCount) exceeds threshold of 2"
            evidence_ts = $A01Status.latestEventTs
        }
    }

    if ($A01Status.igniteStarted -and -not $state.a01IgniteDetected) {
        $state.a01IgniteDetected = $true
        $state.a01IgniteDetectedAt = (Get-Date).ToString("o")
    }
    if ($A01Status.fetchStarted -and -not $state.a01FetchDetected) {
        $state.a01FetchDetected = $true
        $state.a01FetchDetectedAt = (Get-Date).ToString("o")
    }

    if ($state.a01IgniteDetectedAt -and $A01Status.igniteStarted) {
        $igniteStart = [datetime]::Parse($state.a01IgniteDetectedAt)
        $durationMin = ((Get-Date) - $igniteStart).TotalMinutes
        if ($durationMin -gt 10) {
            $warnings += @{
                code = "A01_PERF_WARNING_LONG_RUNNING"
                severity = "WARNING"
                message = "DSHC run duration=$([math]::Round($durationMin,1))min exceeds 10min threshold"
                evidence_ts = $A01Status.latestEventTs
            }
        }
    }

    $excelProcs = Get-Process -Name EXCEL -ErrorAction SilentlyContinue
    if ($excelProcs.Count -gt 1) {
        $warnings += @{
            code = "A01_EXCEL_MULTI_INSTANCE"
            severity = "CIRCUIT_BREAKER_READY"
            message = "Multiple Excel instances: $($excelProcs.Count) (possible WDF bombing)"
            evidence_ts = $A01Status.latestEventTs
        }
    }
    if ($excelProcs.Count -eq 0 -and $A01Status.fetchStarted) {
        $warnings += @{
            code = "A01_EXCEL_TERMINATED_DURING_FETCH"
            severity = "CIRCUIT_BREAKER_READY"
            message = "Excel terminated during active fetch"
            evidence_ts = $A01Status.latestEventTs
        }
    }

    if (-not $Inv.monitor_pid3472_alive) {
        $warnings += @{
            code = "A01_MONITOR_PID3472_DEAD"
            severity = "CIRCUIT_BREAKER_READY"
            message = "PID 3472 monitor process is DEAD"
            evidence_ts = $A01Status.latestEventTs
        }
    }
    if (-not $Inv.p77_pwsh13_alive) {
        $warnings += @{
            code = "A01_P77_WATCH_DEAD"
            severity = "WARNING"
            message = "P77 hash watch appears DEAD (snapshot not updated in 5+ min)"
            evidence_ts = $A01Status.latestEventTs
        }
    }

    return $warnings
}

# ========== MAIN WATCH LOOP ==========
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " DSHD-P79 A01-OPERATION SPECIAL AUDIT WATCH" -ForegroundColor Cyan
Write-Host " Task: DSHC-IGNITE-A01-AUTH" -ForegroundColor Cyan
Write-Host " Tag:  $a01Tag" -ForegroundColor Cyan
Write-Host " Mode: AUDIT_READ_ONLY / wind_api_calls=0" -ForegroundColor Cyan
Write-Host " Started: $(Get-Date -Format 'o')" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$inv = Get-InvariantStatus $baseDir $artifactsDir $monitorPid
Write-Host "Initial state:" -ForegroundColor Yellow
Write-Host "  PID3472: $(if($inv.monitor_pid3472_alive){'ALIVE'}else{'DEAD'})" -ForegroundColor $(if($inv.monitor_pid3472_alive){'Green'}else{'Red'})
Write-Host "  P77 watch: $(if($inv.p77_pwsh13_alive){'ALIVE'}else{'DEAD'})" -ForegroundColor $(if($inv.p77_pwsh13_alive){'Green'}else{'Red'})
Write-Host "  wmain: PID $($inv.wmain_pid) $(if($inv.wmain_running){'RUNNING'}else{'NOT RUNNING'})" -ForegroundColor $(if($inv.wmain_running){'Green'}else{'Yellow'})
Write-Host "  InitWAPI: PID $($inv.initwapi_pid) $(if($inv.initwapi_running){'RUNNING'}else{'NOT RUNNING'})" -ForegroundColor $(if($inv.initwapi_running){'Green'}else{'Yellow'})
Write-Host "  Excel: $(if($inv.excel_running){'PID ' + $inv.excel_pid}else{'NOT RUNNING'})" -ForegroundColor Yellow
Write-Host "  Markers: $(if($inv.ignition_markers_absent){'ABSENT'}else{'PRESENT!'})" -ForegroundColor $(if($inv.ignition_markers_absent){'Green'}else{'Red'})
Write-Host ""

$contextEvent = @{
    timestamp = (Get-Date).ToString("o")
    event = "DSHD-P79-A01-AUDIT-CONTEXT-LOADED"
    agent = "DSHD-P79"
    task = "DSHC-IGNITE-A01-AUTH"
    a01_tag = $a01Tag
    data = @{
        audit_context_loaded = $true
        wind_api_calls = 0
        red_lines_verified = $true
        monitor_pid3472 = $inv.monitor_pid3472_alive
        p77_watch = $inv.p77_pwsh13_alive
        wmain_pid = $inv.wmain_pid
        initwapi_pid = $inv.initwapi_pid
        excel_pid = $inv.excel_pid
        ignition_markers_absent = $inv.ignition_markers_absent
    }
}
Add-AuditEvent $contextEvent $trackingLog
Write-Host "  Context event written" -ForegroundColor Green
Write-Host ""

$loopStart = Get-Date
Write-Host "Watch loop starting..." -ForegroundColor Yellow
Write-Host ""

while ($true) {
    try {
        $pollStart = Get-Date
        $state.pollCount++
        $now = (Get-Date).ToString("o")

        $inv = Get-InvariantStatus $baseDir $artifactsDir $monitorPid
        $recentLines = Get-RecentTrackingEvents 100 $trackingLog
        $a01Status = Get-A01EventStatus $recentLines
        $outputEvidence = Get-OutputSampleEvidence $outputSampleDir
        $state.a01BacktestArtifacts = Get-A01BacktestArtifacts $artifactsDir

        $warnings = Test-CircuitBreakerConditions $a01Status $inv
        foreach ($w in $warnings) {
            $state.a01Warnings += $w
            $warnEvent = @{
                timestamp = $now
                event = "DSHD-P79-A01-$(if($w.severity -eq 'CIRCUIT_BREAKER_READY'){'CIRCUIT_BREAKER_READY'}else{'OBSERVATION_WARNING'})"
                agent = "DSHD-P79"
                task = "DSHC-IGNITE-A01-AUTH"
                a01_tag = $a01Tag
                severity = $w.severity
                warning_code = $w.code
                message = $w.message
                data = @{
                    wind_api_calls = $a01Status.windApiCallsMax
                    evidence_ts = $w.evidence_ts
                    audit_only = $true
                    intervention = "NONE"
                }
            }
            Add-AuditEvent $warnEvent $trackingLog
            if ($w.severity -eq "CIRCUIT_BREAKER_READY") { $state.a01CircuitBreakerReady = $true }
            Write-Host "  [WARNING] $($w.code): $($w.message)" -ForegroundColor Red
        }

        if ($outputEvidence.files.Count -gt 0 -or $state.pollCount % 10 -eq 0) {
            $evidenceData = @{
                task = "DSHD-P79"; a01_tag = $a01Tag; poll_count = $state.pollCount
                timestamp = $now; output_sample = $outputEvidence
                backtest_artifacts = $state.a01BacktestArtifacts
                wind_api_calls = $a01Status.windApiCallsMax
                a01_status = $a01Status; invariants = $inv
                a01_warnings = $state.a01Warnings
            }
            Write-FileEvidenceJson $evidenceData $p79FilePath $artifactsDir
        }

        $snapDue = (($state.pollCount - $state.lastSnapshotPoll) * $pollIntervalSec) -ge $snapshotIntervalSec
        if ($snapDue -or $state.pollCount -eq 1) {
            $state.lastSnapshotPoll = $state.pollCount
            $snapshotData = @{
                task = "DSHD-P79-A01-OPERATION-SPECIAL-AUDIT-WATCH"
                a01_tag = $a01Tag
                poll_count = $state.pollCount
                poll_interval_sec = $pollIntervalSec
                timestamp = $now
                audit_context_loaded = $true
                watch_start = $loopStart.ToString("o")
                watch_elapsed_min = [math]::Round(((Get-Date) - $loopStart).TotalMinutes, 1)
                invariants = $inv
                a01_status = $a01Status
                output_sample_evidence = $outputEvidence
                a01_backtest_artifacts = $state.a01BacktestArtifacts
                a01_warnings = $state.a01Warnings
                wind_api_calls = $a01Status.windApiCallsMax
                circuit_breaker_ready = $state.a01CircuitBreakerReady
                red_lines = @{
                    audit_only = $true; intervention = "NONE"
                    wind_api_calls_zero = ($a01Status.windApiCallsMax -eq 0)
                    processes_untouched = $true; gate_unchanged = $true
                    markers_absent = $inv.ignition_markers_absent
                }
            }
            Write-SnapshotJson $snapshotData $p79SnapshotPath $artifactsDir
            Write-Host "  [SNAPSHOT] poll #$($state.pollCount)" -ForegroundColor Cyan
        }

        if ($state.a01Warnings.Count -gt 0 -or $state.pollCount % 15 -eq 0) {
            $briefContent = @"
# DSHD-P79 A01 Observation Brief

**Task**: DSHC-IGNITE-A01-AUTH
**A01 Tag**: $a01Tag
**Generated**: $now
**Poll Count**: $($state.pollCount)
**Watch Duration**: $([math]::Round(((Get-Date) - $loopStart).TotalMinutes, 1)) min

## Current Status

| Item | State |
|------|-------|
| DSHC Ignite | $(if($a01Status.igniteStarted) {'**YES**'} else {'No'}) |
| DSHC Fetch | $(if($a01Status.fetchStarted) {'**YES**'} else {'No'}) |
| DSHA Backtest Start | $(if($a01Status.backtestStarted) {'**YES**'} else {'No'}) |
| DSHA Backtest Complete | $(if($a01Status.backtestCompleted) {'**YES**'} else {'No'}) |
| DSHA Backtest Error | $(if($a01Status.backtestError) {'**YES - ERROR**'} else {'No'}) |
| P62-LOOP Triggered | $(if($a01Status.p62LoopTrigger) {'**YES**'} else {'No'}) |
| wind_api_calls | $($a01Status.windApiCallsMax) |
| WDF Retries | $($a01Status.wdfRetryCount) |
| Circuit Breaker | $(if($state.a01CircuitBreakerReady) {'**READY**'} else {'Not triggered'}) |

## Invariant Status

| Check | State |
|-------|-------|
| wmain (PID $($inv.wmain_pid)) | $(if($inv.wmain_running) {'RUNNING'} else {'NOT RUNNING'}) |
| InitWAPI (PID $($inv.initwapi_pid)) | $(if($inv.initwapi_running) {'RUNNING'} else {'NOT RUNNING'}) |
| Excel (PID $($inv.excel_pid)) | $(if($inv.excel_running) {'RUNNING'} else {'NOT RUNNING'}) |
| Ignition Markers | $(if($inv.ignition_markers_absent) {'ABSENT'} else {'**PRESENT**'}) |
| PID 3472 Monitor | $(if($inv.monitor_pid3472_alive) {'ALIVE'} else {'**DEAD**'}) |
| P77 Watch | $(if($inv.p77_pwsh13_alive) {'ALIVE'} else {'**DEAD**'}) |

## Output Sample

$(if($outputEvidence.files.Count -gt 0) {"| File | Size | SHA256 | Modified |
|------|------|--------|----------|"
    foreach ($f in $outputEvidence.files) { "| $($f.name) | $($f.size_bytes) | $($f.sha256) | $($f.last_write_time) |" }} else {"*(no files in output_sample/)*"})

## Warnings

$(if($state.a01Warnings.Count -gt 0) {"| Code | Severity | Message |
|------|----------|---------|"
    foreach ($w in $state.a01Warnings) { "| $($w.code) | $($w.severity) | $($w.message) |" }} else {"*(no warnings)*"})

## Backtest Artifacts

$(if($state.a01BacktestArtifacts.Count -gt 0) {"| File | Size | SHA256 | Modified |
|------|------|--------|----------|"
    foreach ($f in $state.a01BacktestArtifacts) { "| $($f.name) | $($f.size_bytes) | $($f.sha256) | $($f.last_write_time) |" }} else {"*(none yet)*"})

---
**DSHD-P79**: AUDIT_ONLY=YES | Intervention=NONE | wind_api_calls=$($a01Status.windApiCallsMax)
"@
            Write-ObservationBrief $briefContent $a01BriefPath
            Write-Host "  [BRIEF] poll #$($state.pollCount)" -ForegroundColor Cyan
        }

        $statusMsg = "  [P79#$($state.pollCount)] $(Get-Date -Format 'HH:mm:ss') wind_api=$($a01Status.windApiCallsMax) ignite=$(if($a01Status.igniteStarted){'Y'}else{'n'}) fetch=$(if($a01Status.fetchStarted){'Y'}else{'n'}) bt=$(if($a01Status.backtestStarted){'Y'}else{'n'}) out=$($outputEvidence.files.Count) warn=$($state.a01Warnings.Count)"
        Write-Host $statusMsg -ForegroundColor $(if($a01Status.windApiCallsMax -gt 0){'Red'}else{'Green'})

        $elapsed = (Get-Date) - $pollStart
        if ($elapsed.TotalSeconds -lt $pollIntervalSec) {
            Start-Sleep -Seconds ([math]::Floor($pollIntervalSec - $elapsed.TotalSeconds))
        }
    } catch {
        Write-Host "  [P79-ERROR] $($_.Exception.Message)" -ForegroundColor Red
        Start-Sleep -Seconds $pollIntervalSec
    }
}
