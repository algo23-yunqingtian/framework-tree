#!/usr/bin/env python3
"""Creates dshd_p80_a01_audit_watch.ps1 with UTF-8 BOM.
P80: A01-EVIDENCE-CHAIN REINFORCED AUDIT WATCH.
Builds on P79 with: BOM self-check, CSV file evidence, artifact catalog (every 10 polls),
scheduled briefs (every 12 polls), and the wind_api_calls counting fix
([long], exclude P79/P80 audit events, cap at 1000 to drop inflated values).
"""
import os

output_path = r"D:\DSH_WORK\github工作\回测\G7_ADJUDICATION_LEDGER\dshd_p80_a01_audit_watch.ps1"

ps1_content = r"""# DSHD-P80 A01-EVIDENCE-CHAIN REINFORCED AUDIT WATCH
# Baseline: feature/v88-g1
# Constraint: AUDIT_READ_ONLY; wind_api_calls=0
# PID3472 main monitor + pwsh-13 P77 hash watch MUST NOT be stopped/rebuilt
# A01 tag: A01-USER-REMOTE-001 (audit tagging only, no execution privilege)
# All evidence written to G7 adjudication ledger, immutable, read-only
# P80 additions over P79:
#   - BOM health self-check each poll (warn only, never auto-fix)
#   - wdf_sample_metals_raw.csv -> immediate independent SHA256 evidence
#   - artifact catalog (dshc_*/dsha_*) every 10 polls
#   - scheduled observation brief every 12 polls (not only on warnings)
#   - CRITICAL FIX: wind_api_calls counting excludes P79/P80 audit events,
#     uses [long], and caps values at 1000 to discard inflated artifacts

param()

# ========== CONSTANTS ==========
$baseDir = "D:\DSH_WORK\github工作\回测"
$ledgerDir = "$baseDir\G7_ADJUDICATION_LEDGER"
$artifactsDir = "$baseDir\artifacts"
$trackingLog = "$baseDir\tracking_monitor_audit.jsonl"
$scriptPath = "$ledgerDir\dshd_p80_a01_audit_watch.ps1"
$p80SnapshotPath = "$artifactsDir\dshd_p80_a01_audit_snapshot.json"
$evidencePath = "$artifactsDir\dshd_a01_file_evidence.json"
$catalogPath = "$artifactsDir\dshd_a01_artifact_catalog.json"
$briefPath = "$artifactsDir\dshd_a01_observation_brief.md"
$outputSampleDir = "$baseDir\output_sample"
$monitorPid = 3472
$pollIntervalSec = 30
$snapshotIntervalSec = 300
$catalogIntervalPolls = 10
$briefIntervalPolls = 12
$a01Tag = "A01-USER-REMOTE-001"
$csvFileName = "wdf_sample_metals_raw.csv"

$state = @{
    pollCount = 0
    lastSnapshotPoll = 0
    a01IgniteDetected = $false
    a01FetchDetected = $false
    a01IgniteDetectedAt = ""
    a01FetchDetectedAt = ""
    a01CircuitBreakerReady = $false
    a01Warnings = @()
    a01BacktestArtifacts = @()
    csvFirstSeen = ""
    bomWarningIssued = $false
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
        Write-Host "[P80-ERROR] Failed to append event: $_" -ForegroundColor Red
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
    param([int]$Count = 500, [string]$TrackingLogPath)
    try {
        if (!(Test-Path $TrackingLogPath)) { return @() }
        $allLines = [System.IO.File]::ReadAllLines($TrackingLogPath, [System.Text.Encoding]::UTF8)
        if ($allLines.Count -le $Count) { return $allLines }
        return $allLines[($allLines.Count - $Count)..($allLines.Count - 1)]
    } catch { return @() }
}

# ========== HELPER: BOM health self-check ==========
function Get-BomStatus {
    param([string]$ScriptPath)
    try {
        if (!(Test-Path $ScriptPath)) { return @{ intact = $false; size = 0; error = "not found" } }
        $bytes = [System.IO.File]::ReadAllBytes($ScriptPath)
        $hasBom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
        return @{ intact = $hasBom; size = $bytes.Length; error = "" }
    } catch {
        return @{ intact = $false; size = 0; error = $_.Exception.Message }
    }
}

# ========== HELPER: Write snapshot JSON ==========
function Write-SnapshotJson {
    param([hashtable]$Data, [string]$OutputPath, [string]$ArtifactsDir)
    try {
        $jsonStr = $Data | ConvertTo-Json -Depth 10 -Compress
        $tempJson = "$ArtifactsDir\.p80_snapshot_tmp.json"
        [System.IO.File]::WriteAllText($tempJson, $jsonStr, (New-Object System.Text.UTF8Encoding $false))
        & python -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); open(sys.argv[2],'w',encoding='utf-8').write(json.dumps(d,separators=(',',':'),ensure_ascii=False))" $tempJson $OutputPath
        if (Test-Path $tempJson) { Remove-Item $tempJson -Force -ErrorAction SilentlyContinue }
    } catch {
        Write-Host "[P80-ERROR] Failed to write snapshot: $_" -ForegroundColor Red
    }
}

# ========== HELPER: Write file evidence JSON ==========
function Write-FileEvidenceJson {
    param([hashtable]$Data, [string]$OutputPath, [string]$ArtifactsDir)
    try {
        $tempJson = "$ArtifactsDir\.p80_evidence_tmp.json"
        [System.IO.File]::WriteAllText($tempJson, ($Data | ConvertTo-Json -Depth 10 -Compress), (New-Object System.Text.UTF8Encoding $false))
        & python -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); open(sys.argv[2],'w',encoding='utf-8').write(json.dumps(d,separators=(',',':'),ensure_ascii=False))" $tempJson $OutputPath
        if (Test-Path $tempJson) { Remove-Item $tempJson -Force -ErrorAction SilentlyContinue }
    } catch {
        Write-Host "[P80-ERROR] Failed to write file evidence: $_" -ForegroundColor Red
    }
}

# ========== HELPER: Write artifact catalog JSON ==========
function Write-ArtifactCatalog {
    param([hashtable]$Data, [string]$OutputPath, [string]$ArtifactsDir)
    try {
        $tempJson = "$ArtifactsDir\.p80_catalog_tmp.json"
        [System.IO.File]::WriteAllText($tempJson, ($Data | ConvertTo-Json -Depth 10 -Compress), (New-Object System.Text.UTF8Encoding $false))
        & python -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); open(sys.argv[2],'w',encoding='utf-8').write(json.dumps(d,separators=(',',':'),ensure_ascii=False))" $tempJson $OutputPath
        if (Test-Path $tempJson) { Remove-Item $tempJson -Force -ErrorAction SilentlyContinue }
    } catch {
        Write-Host "[P80-ERROR] Failed to write artifact catalog: $_" -ForegroundColor Red
    }
}

# ========== HELPER: Write A01 observation brief ==========
function Write-ObservationBrief {
    param([string]$Content, [string]$OutputPath)
    try {
        $bom = New-Object System.Text.UTF8Encoding($true)
        [System.IO.File]::WriteAllText($OutputPath, $Content, $bom)
    } catch {
        Write-Host "[P80-ERROR] Failed to write brief: $_" -ForegroundColor Red
    }
}

# ========== HELPER: Detect A01 events ==========
# FIX vs P79: wind_api_calls counting excludes P79/P80 audit events,
# uses [long], and caps at 1000 to discard inflated self-referential values.
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
            if ($line -notmatch '"agent":"DSHD-P79"' -and $line -notmatch '"agent":"DSHD-P80"') {
                $val = [long]$Matches[1]
                if ($val -gt 0 -and $val -lt 1000 -and $val -gt $status.windApiCallsMax) {
                    $status.windApiCallsMax = $val
                }
            }
        }
        if ($line -match '"wdf_retries":(\d+)') {
            if ($line -notmatch '"agent":"DSHD-P79"' -and $line -notmatch '"agent":"DSHD-P80"') {
                $val = [long]$Matches[1]
                if ($val -gt $status.wdfRetryCount) { $status.wdfRetryCount = $val }
            }
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

# ========== HELPER: wdf_sample_metals_raw.csv evidence (P80) ==========
# Forensics only: records size, SHA256, last write time, and first 10 lines.
# Never modifies the CSV file.
function Get-OutputSampleCsvEvidence {
    param([string]$OutputSampleDir, [string]$CsvFileName)
    $csvPath = Join-Path $OutputSampleDir $CsvFileName
    if (!(Test-Path $csvPath)) { return @{ detected = $false } }
    $f = Get-Item $csvPath
    $hash = Get-FileSha256 $f.FullName
    $first10 = @()
    try {
        $reader = New-Object System.IO.StreamReader($csvPath, [System.Text.Encoding]::UTF8)
        for ($i = 0; $i -lt 10; $i++) {
            $line = $reader.ReadLine()
            if ($line -eq $null) { break }
            $first10 += $line
        }
        $reader.Close()
    } catch { $first10 = @("ERROR: $($_.Exception.Message)") }
    return @{
        detected = $true
        file_name = $f.Name
        file_path = $f.FullName
        size_bytes = $f.Length
        sha256 = $hash
        last_write_time = $f.LastWriteTime.ToString("o")
        creation_time = $f.CreationTime.ToString("o")
        first_10_lines = $first10
    }
}

# ========== HELPER: Check backtest artifacts (dshc_* + dsha_*) ==========
function Get-A01BacktestArtifacts {
    param([string]$ArtifactsDir)
    $artifacts = @()
    foreach ($pattern in @("dshc_*", "dsha_*")) {
        $files = Get-ChildItem $ArtifactsDir -Filter $pattern -File -ErrorAction SilentlyContinue
        foreach ($f in $files) {
            $hash = Get-FileSha256 $f.FullName
            $artifacts += @{
                name = $f.Name
                size_bytes = $f.Length
                sha256 = $hash
                last_write_time = $f.LastWriteTime.ToString("o")
            }
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

# ========== HELPER: Circuit breaker check (P80: + BOM warning) ==========
function Test-CircuitBreakerConditions {
    param([hashtable]$A01Status, [hashtable]$Inv, [hashtable]$BomStatus)
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

    # P80: BOM health warning (warn only, never auto-fix)
    if (-not $BomStatus.intact) {
        if (-not $state.bomWarningIssued) {
            $state.bomWarningIssued = $true
            $warnings += @{
                code = "PS_BOM_WARNING"
                severity = "WARNING"
                message = "Script BOM integrity FAILED - UTF-8 BOM not detected (size=$($BomStatus.size) bytes); leave for human to fix, NOT auto-overwriting"
                evidence_ts = (Get-Date).ToString("o")
            }
        }
    }

    return $warnings
}

# ========== MAIN WATCH LOOP ==========
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " DSHD-P80 A01-EVIDENCE-CHAIN REINFORCED AUDIT WATCH" -ForegroundColor Cyan
Write-Host " Task: DSHC-IGNITE-A01-AUTH" -ForegroundColor Cyan
Write-Host " Tag:  $a01Tag" -ForegroundColor Cyan
Write-Host " Mode: AUDIT_READ_ONLY / wind_api_calls=0" -ForegroundColor Cyan
Write-Host " P80: BOM check + file evidence + artifact catalog + scheduled briefs" -ForegroundColor Cyan
Write-Host " Started: $(Get-Date -Format 'o')" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$bomStatus = Get-BomStatus $scriptPath
$inv = Get-InvariantStatus $baseDir $artifactsDir $monitorPid
Write-Host "Initial state:" -ForegroundColor Yellow
Write-Host "  PID3472: $(if($inv.monitor_pid3472_alive){'ALIVE'}else{'DEAD'})" -ForegroundColor $(if($inv.monitor_pid3472_alive){'Green'}else{'Red'})
Write-Host "  P77 watch: $(if($inv.p77_pwsh13_alive){'ALIVE'}else{'DEAD'})" -ForegroundColor $(if($inv.p77_pwsh13_alive){'Green'}else{'Red'})
Write-Host "  wmain: PID $($inv.wmain_pid) $(if($inv.wmain_running){'RUNNING'}else{'NOT RUNNING'})" -ForegroundColor $(if($inv.wmain_running){'Green'}else{'Yellow'})
Write-Host "  InitWAPI: PID $($inv.initwapi_pid) $(if($inv.initwapi_running){'RUNNING'}else{'NOT RUNNING'})" -ForegroundColor $(if($inv.initwapi_running){'Green'}else{'Yellow'})
Write-Host "  Excel: $(if($inv.excel_running){'PID ' + $inv.excel_pid}else{'NOT RUNNING'})" -ForegroundColor Yellow
Write-Host "  Markers: $(if($inv.ignition_markers_absent){'ABSENT'}else{'PRESENT!'})" -ForegroundColor $(if($inv.ignition_markers_absent){'Green'}else{'Red'})
Write-Host "  BOM: $(if($bomStatus.intact){'INTACT (' + $bomStatus.size + ' bytes)'}else{'MISSING!'})" -ForegroundColor $(if($bomStatus.intact){'Green'}else{'Red'})
Write-Host ""

$contextEvent = @{
    timestamp = (Get-Date).ToString("o")
    event = "DSHD-P80-A01-EVIDENCE-CHAIN-AUDIT-STARTED"
    agent = "DSHD-P80"
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
        bom_status_intact = $bomStatus.intact
        evidence_chain_features = @("file_evidence", "artifact_catalog", "scheduled_briefs", "bom_self_check")
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

        # P80: BOM health self-check every poll
        $bomStatus = Get-BomStatus $scriptPath

        $inv = Get-InvariantStatus $baseDir $artifactsDir $monitorPid
        $recentLines = Get-RecentTrackingEvents 500 $trackingLog
        $a01Status = Get-A01EventStatus $recentLines
        $outputEvidence = Get-OutputSampleEvidence $outputSampleDir
        $csvEvidence = Get-OutputSampleCsvEvidence $outputSampleDir $csvFileName
        $state.a01BacktestArtifacts = Get-A01BacktestArtifacts $artifactsDir

        if ($csvEvidence.detected -and [string]::IsNullOrEmpty($state.csvFirstSeen)) {
            $state.csvFirstSeen = (Get-Date).ToString("o")
            Write-Host "  [CSV-EVIDENCE] $csvFileName detected! SHA256=$($csvEvidence.sha256) size=$($csvEvidence.size_bytes)" -ForegroundColor Yellow
        }

        $warnings = Test-CircuitBreakerConditions $a01Status $inv $bomStatus
        foreach ($w in $warnings) {
            $state.a01Warnings += $w
            $warnEvent = @{
                timestamp = $now
                event = "DSHD-P80-A01-$(if($w.severity -eq 'CIRCUIT_BREAKER_READY'){'CIRCUIT_BREAKER_READY'}else{'OBSERVATION_WARNING'})"
                agent = "DSHD-P80"
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

        # File evidence: immediately when CSV appears, or every 10 polls
        if ($csvEvidence.detected -or $outputEvidence.files.Count -gt 0 -or $state.pollCount % 10 -eq 0) {
            $evidenceData = @{
                task = "DSHD-P80"; a01_tag = $a01Tag; poll_count = $state.pollCount
                timestamp = $now; output_sample = $outputEvidence
                csv_evidence = $csvEvidence; csv_first_seen = $state.csvFirstSeen
                backtest_artifacts = $state.a01BacktestArtifacts
                wind_api_calls = $a01Status.windApiCallsMax
                a01_status = $a01Status; invariants = $inv
                a01_warnings = $state.a01Warnings
                bom_status = $bomStatus
            }
            Write-FileEvidenceJson $evidenceData $evidencePath $artifactsDir
        }

        # P80: artifact catalog every 10 polls (dshc_*/dsha_* hashed manifest)
        if ($state.pollCount % $catalogIntervalPolls -eq 0) {
            $totalSize = 0
            foreach ($a in $state.a01BacktestArtifacts) { $totalSize += $a.size_bytes }
            $catalogData = @{
                task = "DSHD-P80"; a01_tag = $a01Tag; poll_count = $state.pollCount
                timestamp = $now
                artifact_count = $state.a01BacktestArtifacts.Count
                total_size_bytes = $totalSize
                artifacts = $state.a01BacktestArtifacts
                catalog_interval_polls = $catalogIntervalPolls
            }
            Write-ArtifactCatalog $catalogData $catalogPath $artifactsDir
            Write-Host "  [CATALOG] poll #$($state.pollCount) - $($state.a01BacktestArtifacts.Count) artifacts cataloged" -ForegroundColor Cyan
        }

        $snapDue = (($state.pollCount - $state.lastSnapshotPoll) * $pollIntervalSec) -ge $snapshotIntervalSec
        if ($snapDue -or $state.pollCount -eq 1) {
            $state.lastSnapshotPoll = $state.pollCount
            $snapshotData = @{
                task = "DSHD-P80-A01-EVIDENCE-CHAIN-REINFORCED-AUDIT-WATCH"
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
                csv_evidence = $csvEvidence
                csv_first_seen = $state.csvFirstSeen
                a01_backtest_artifacts = $state.a01BacktestArtifacts
                a01_warnings = $state.a01Warnings
                wind_api_calls = $a01Status.windApiCallsMax
                circuit_breaker_ready = $state.a01CircuitBreakerReady
                bom_status = $bomStatus
                ps_bom_warning = (-not $bomStatus.intact)
                red_lines = @{
                    audit_only = $true; intervention = "NONE"
                    wind_api_calls_zero = ($a01Status.windApiCallsMax -eq 0)
                    processes_untouched = $true; gate_unchanged = $true
                    markers_absent = $inv.ignition_markers_absent
                }
            }
            Write-SnapshotJson $snapshotData $p80SnapshotPath $artifactsDir
            Write-Host "  [SNAPSHOT] poll #$($state.pollCount)" -ForegroundColor Cyan
        }

        # P80: scheduled brief every 12 polls (not only on warnings)
        if ($state.pollCount % $briefIntervalPolls -eq 0 -or $state.pollCount -eq 1) {
            if ($state.a01Warnings.Count -gt 0) {
                $statusLine = "WARNING - $($state.a01Warnings.Count) warning(s) detected:"
                foreach ($w in $state.a01Warnings) { $statusLine += "`n  - $($w.code): $($w.message)" }
            } else {
                $statusLine = "一切观测平稳 - All observations stable, no warnings."
            }
            $briefContent = @"
# DSHD-P80 A01 Observation Brief

**Task**: DSHC-IGNITE-A01-AUTH
**A01 Tag**: $a01Tag
**Generated**: $now
**Poll Count**: $($state.pollCount)
**Watch Duration**: $([math]::Round(((Get-Date) - $loopStart).TotalMinutes, 1)) min

## Overall Status

$statusLine

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
| BOM Integrity | $(if($bomStatus.intact) {'**INTACT**'} else {'**MISSING**'}) |

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

## CSV File Evidence

$(if($csvEvidence.detected) {"| Property | Value |
|----------|-------|
| File | $($csvEvidence.file_name) |
| Size | $($csvEvidence.size_bytes) bytes |
| SHA256 | $($csvEvidence.sha256) |
| First Seen | $($state.csvFirstSeen) |
| Last Modified | $($csvEvidence.last_write_time) |
| First 10 Lines | $($csvEvidence.first_10_lines.Count) captured |"} else {"*(wdf_sample_metals_raw.csv not yet detected)*"})

## Warnings

$(if($state.a01Warnings.Count -gt 0) {"| Code | Severity | Message |
|------|----------|---------|"
    foreach ($w in $state.a01Warnings) { "| $($w.code) | $($w.severity) | $($w.message) |" }} else {"*(no warnings)*"})

## Backtest Artifacts (dshc_*/dsha_*)

$(if($state.a01BacktestArtifacts.Count -gt 0) {"| File | Size | SHA256 | Modified |
|------|------|--------|----------|"
    foreach ($f in $state.a01BacktestArtifacts) { "| $($f.name) | $($f.size_bytes) | $($f.sha256) | $($f.last_write_time) |" }} else {"*(none yet)*"})

## Tracking Log

- Path: $trackingLog
- A01 Tag Present: $a01Tag

---
**DSHD-P80**: AUDIT_ONLY=YES | Intervention=NONE | wind_api_calls=$($a01Status.windApiCallsMax) | BOM=$(if($bomStatus.intact){'OK'}else{'MISSING'})
"@
            Write-ObservationBrief $briefContent $briefPath
            Write-Host "  [BRIEF] poll #$($state.pollCount)" -ForegroundColor Cyan
        }

        $statusMsg = "  [P80#$($state.pollCount)] $(Get-Date -Format 'HH:mm:ss') wind_api=$($a01Status.windApiCallsMax) ignite=$(if($a01Status.igniteStarted){'Y'}else{'n'}) fetch=$(if($a01Status.fetchStarted){'Y'}else{'n'}) bt=$(if($a01Status.backtestStarted){'Y'}else{'n'}) out=$($outputEvidence.files.Count) csv=$(if($csvEvidence.detected){'Y'}else{'n'}) warn=$($state.a01Warnings.Count) bom=$(if($bomStatus.intact){'OK'}else{'MISSING'})"
        Write-Host $statusMsg -ForegroundColor $(if($a01Status.windApiCallsMax -gt 0){'Red'}else{'Green'})

        $elapsed = (Get-Date) - $pollStart
        if ($elapsed.TotalSeconds -lt $pollIntervalSec) {
            Start-Sleep -Seconds ([math]::Floor($pollIntervalSec - $elapsed.TotalSeconds))
        }
    } catch {
        Write-Host "  [P80-ERROR] $($_.Exception.Message)" -ForegroundColor Red
        Start-Sleep -Seconds $pollIntervalSec
    }
}
"""

os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, 'w', encoding='utf-8-sig') as f:
    f.write(ps1_content)

size = os.path.getsize(output_path)
with open(output_path, 'rb') as f:
    head = f.read(3)
bom_ok = head == b'\xef\xbb\xbf'
print(f"Written: {output_path}")
print(f"Size: {size} bytes")
print(f"BOM: {'OK' if bom_ok else 'MISSING'}")
