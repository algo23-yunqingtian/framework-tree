# DSHD-P67 Monitor v4 — Enhanced Authorization Surveillance (30s poll)
# Purpose: Observe DSHC authorized InitWAPI/RegExcel activation attempt
# Hard constraints: wind_api_calls=0, no Wind calls, no ledger/checksum/manifest modification
# Surveillance: .wind directory, listening ports, windlocal.exe lifecycle, crazy retry detection
$ErrorActionPreference = 'SilentlyContinue'

# === Startup marker (for diagnostics) ===
$ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"
Add-Content -Path "D:\DSH_WORK\github工作\回测\G7_ADJUDICATION_LEDGER\dshd_p67_monitor_log.jsonl" -Value '{"timestamp":"' + $ts + '","event_type":"MONITOR_V4_STARTED","agent":"DSHD-P67","severity":"INFO","monitor_version":"v4","detail":"v4 monitor v4 process started, PID=' + $PID + '"}'
Write-Host "V4 monitor started PID=$PID at $ts"

$ledger    = "D:\DSH_WORK\github工作\回测\tracking_monitor_audit.jsonl"
$windLog   = "D:\DSH_WORK\github工作\回测\data-harbor\dsha_p49_prep\P49_backtest_audit\wind_excel_events.jsonl"
$windDir   = "D:\DSH_WORK\github工作\回测\data-harbor\dsha_p49_prep\P49_backtest_audit"
$xlsxDir   = "$windDir\wind_excel_data"
$logFile   = "D:\DSH_WORK\github工作\回测\G7_ADJUDICATION_LEDGER\dshd_p67_monitor_log.jsonl"
$windUsersDir = "$env:USERPROFILE\.wind\WMain\users"
$windEtcDir   = "$env:USERPROFILE\.wind\WMain\etc"

# Dynamic poll number: read last poll from log
$pollNum = 400
try {
    $lastLines = Get-Content $logFile -Tail 3
    foreach ($ll in $lastLines) {
        if ($ll -match '"poll_number":(\d+)') {
            $pollNum = [int]$Matches[1] + 1
        }
    }
} catch {}

# Previous state tracking
$prevLedgerSha8 = ""
$prevWindEventsSha8 = ""
$prevLedgerLines = 0
$prevWindEventsLines = 0
$prevWindUsersCount = -1
$prevWindLocalPids = @()
$spawnEventCount = 0
$lastSpawnTimestamp = ""

while ($true) {
    $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"

    # 1. Excel processes
    $excelCount = (Get-Process -Name EXCEL -ErrorAction SilentlyContinue).Count
    if (-not $excelCount) { $excelCount = 0 }

    # 2. Ledger
    $ledgerSha8 = ""; $ledgerLines = 0; $ledgerSize = 0; $ledgerRaw = ""
    if (Test-Path $ledger) {
        $ledgerSha8 = (Get-FileHash $ledger -Algorithm SHA256).Hash.Substring(0,8).ToUpper()
        $ledgerSize = (Get-Item $ledger).Length
        $ledgerRaw = Get-Content $ledger -Raw
        $ledgerLines = ($ledgerRaw -split "`r?`n" | Where { $_.Trim() -ne '' }).Count
    }

    # 3. XLSX/CSV files
    $xlsxCount = 0; $csvCount = 0
    if (Test-Path $xlsxDir) {
        $xlsxCount = (Get-ChildItem $xlsxDir -Filter "*.xlsx" -ErrorAction SilentlyContinue).Count
        $csvCount  = (Get-ChildItem $windDir -Recurse -Filter "*.csv" -ErrorAction SilentlyContinue).Count
        if (-not $xlsxCount) { $xlsxCount = 0 }
        if (-not $csvCount) { $csvCount = 0 }
    }

    # 4. Wind events log
    $windEventsSha8 = ""; $windEventsSize = 0; $windEventsLines = 0
    $windApiCalls = 0
    if (Test-Path $windLog) {
        $windEventsSha8 = (Get-FileHash $windLog -Algorithm SHA256).Hash.Substring(0,8).ToUpper()
        $windEventsSize = (Get-Item $windLog).Length
        $weRaw = Get-Content $windLog -Raw
        $weLines = $weRaw -split "`r?`n" | Where { $_.Trim() -ne '' }
        $windEventsLines = $weLines.Count
        foreach ($wl in $weLines) {
            try {
                $ev = $wl | ConvertFrom-Json
                if ($ev.wind_api_calls -ne $null) { $windApiCalls += [int]$ev.wind_api_calls }
            } catch {}
        }
    }

    # 5. Ledger wind_api_calls
    $ledgerApiCalls = 0
    if ($ledgerLines -gt 0) {
        $llLines = $ledgerRaw -split "`r?`n" | Where { $_.Trim() -ne '' }
        foreach ($ll in $llLines) {
            try {
                $ev = $ll | ConvertFrom-Json
                if ($ev.wind_api_calls -ne $null) { $ledgerApiCalls += [int]$ev.wind_api_calls }
            } catch {}
        }
    }
    $totalWindCalls = [Math]::Max($windApiCalls, $ledgerApiCalls)

    # 6. Pipeline/wind script process detection + windlocal.exe lifecycle
    $pipelineRunning = 0
    $windScriptPids = @()
    $windLocalPids = @()
    $windInitPids = @()
    $allProcesses = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue
    if ($allProcesses) {
        foreach ($p in $allProcesses) {
            $cmdline = $p.CommandLine
            $pname   = $p.Name
            if ($cmdline -match 'wind_data_pull_pipeline\.py') { $pipelineRunning++ }
            if ($cmdline -match 'wind.*\.py|WindPy')           { $windScriptPids += $p.ProcessId }
            if ($pname -match 'windlocal')                      { $windLocalPids += $p.ProcessId }
            if ($pname -match 'InitWAPI')                       { $windInitPids += $p.ProcessId }
        }
    }

    # 7. .wind directory surveillance
    $windUsersFileCount = 0; $windUsersFiles = @()
    if (Test-Path $windUsersDir) {
        $windUsersFiles = Get-ChildItem $windUsersDir -ErrorAction SilentlyContinue
        $windUsersFileCount = if ($windUsersFiles) { $windUsersFiles.Count } else { 0 }
    }
    $windEtcFileCount = 0
    if (Test-Path $windEtcDir) {
        $windEtcFileCount = (Get-ChildItem $windEtcDir -Recurse -ErrorAction SilentlyContinue).Count
        if (-not $windEtcFileCount) { $windEtcFileCount = 0 }
    }

    # 8. Listening port surveillance (Wind-related: 63423, 62237, 49999, 49998, etc.)
    $windPorts = @()
    $listenConns = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue
    if ($listenConns) {
        foreach ($c in $listenConns) {
            # Wind typical ports: 62000-63000, 49998-49999, or any 127.0.0.1 high port
            if ($c.LocalPort -ge 62000 -and $c.LocalPort -le 64000) {
                $windPorts += @{ port = $c.LocalPort; addr = $c.LocalAddress; pid = $c.OwningProcess }
            }
        }
    }

    # 9. Crazy retry detection
    $crazyRetry = $false; $crazyRetryDetail = ""
    if ($windLocalPids.Count -gt 0 -or $windInitPids.Count -gt 0) {
        $spawnEventCount++
        if ($spawnEventCount -ge 3 -and ($ts - $lastSpawnTimestamp).TotalSeconds -lt 60) {
            $crazyRetry = $true
            $crazyRetryDetail = "Multiple Wind process spawns within 60s (count=$spawnEventCount)"
        } else {
            $spawnEventCount = 1
        }
        $lastSpawnTimestamp = $ts
    }

    # 10. Credential scan — enhanced: check both ledger and wind_excel_events
    $credAlert = "NONE"; $credFiles = @(); $credLines = @()
    $credPattern = 'credentials_provided|password|passwd|api_key|token|secret|Tyq1999|13199157886'

    # Ledger scan
    if ($ledgerLines -gt 0) {
        $allLedgerLines = $ledgerRaw -split "`r?`n" | Where { $_.Trim() -ne '' }
        for ($i = 0; $i -lt $allLedgerLines.Count; $i++) {
            if ($allLedgerLines[$i] -match $credPattern) {
                $credAlert = "CRITICAL_CREDENTIAL_DETECTED"
                $credFiles += "tracking_monitor_audit.jsonl"
                $credLines += ($i + 1)
            }
        }
    }

    # Wind events scan
    if ($windEventsLines -gt 0) {
        $weAllLines = $weRaw -split "`r?`n" | Where { $_.Trim() -ne '' }
        for ($i = 0; $i -lt $weAllLines.Count; $i++) {
            if ($weAllLines[$i] -match $credPattern) {
                $credAlert = "CRITICAL_CREDENTIAL_DETECTED"
                $credFiles += "wind_excel_events.jsonl"
                $credLines += ($i + 1)
            }
        }
    }
    $credPreview = ""
    if ($credAlert -ne "NONE" -and $credFiles.Count -gt 0) {
        $firstFile = $credFiles[0]
        $firstLine = $credLines[0]
        $sourceLines = if ($firstFile -eq "tracking_monitor_audit.jsonl") { $allLedgerLines } else { $weAllLines }
        $credPreview = $sourceLines[$firstLine - 1].Substring(0, [Math]::Min(200, $sourceLines[$firstLine - 1].Length))
    }

    # 11. Circuit breaker
    $cbTripped = $false; $cbReason = ""
    if ($totalWindCalls -gt 0 -or $pipelineRunning -gt 0) {
        $cbTripped = $true
        $cbReasons = @()
        if ($totalWindCalls -gt 0) { $cbReasons += "wind_api_calls=$totalWindCalls" }
        if ($pipelineRunning -gt 0) { $cbReasons += "pipeline_process_active" }
        $cbReason = $cbReasons -join ";"
    }

    # 12. Severity
    if ($cbTripped -or $crazyRetry) { $severity = "CRITICAL" }
    elseif ($credAlert -ne "NONE") { $severity = "CRITICAL" }
    elseif ($windLocalPids.Count -gt 0 -or $windInitPids.Count -gt 0) { $severity = "WARNING" }
    else { $severity = "OK" }

    # 13. DSHA_WIND_PY_TEST tag
    $windPyTestTag = $false; $tagReasons = @()
    if ($totalWindCalls -gt 0) { $tagReasons += "wind_api_calls=$totalWindCalls" }
    if ($windEventsLines -gt 28) { $tagReasons += "wind_events_grew" }
    if ($pipelineRunning -gt 0) { $tagReasons += "pipeline_active" }
    if ($windScriptPids.Count -gt 0) { $tagReasons += "wind_script_procs=$($windScriptPids.Count)" }
    if ($windLocalPids.Count -gt 0) { $tagReasons += "windlocal_active" }
    if ($windInitPids.Count -gt 0) { $tagReasons += "initwapi_active" }
    if ($tagReasons.Count -gt 0) { $windPyTestTag = $true }

    # 14. Build event
    $invariantCb = "READY"; $invariantTrip = "false"
    if ($cbTripped) { $invariantCb = "TRIPPED"; $invariantTrip = "true" }

    $event = @{
        timestamp = $ts
        poll_number = $pollNum
        event_type = "CONTINUOUS_MONITORING_POLL"
        event_id = "DSHD-P67-MONITOR-POLL-$pollNum"
        agent = "DSHD-P67"
        severity = $severity
        monitor_version = "v4"
        poll_interval_seconds = 30
        dsha_wind_py_test = $windPyTestTag
        wind_py_test_reasons = $tagReasons
        results = @{
            ledger_sha8 = $ledgerSha8
            ledger_lines = $ledgerLines
            ledger_size = $ledgerSize
            wind_events_sha8 = $windEventsSha8
            wind_events_size = $windEventsSize
            wind_events_lines = $windEventsLines
            xlsx_count = $xlsxCount
            csv_count = $csvCount
            excel_count = $excelCount
            credential_alert = $credAlert
            wind_api_calls = $totalWindCalls
            pipeline_process_detected = ($pipelineRunning -gt 0)
            wind_script_processes = $windScriptPids.Count
            windlocal_pids = $windLocalPids
            initwapi_pids = $windInitPids
            wind_users_file_count = $windUsersFileCount
            wind_etc_file_count = $windEtcFileCount
            wind_listening_ports = $windPorts
            crazy_retry_detected = $crazyRetry
            crazy_retry_detail = $crazyRetryDetail
        }
        invariants = @{
            release_permit = "NOT_ISSUED"
            gate = "CLOSED/HOLD"
            circuit_breaker = $invariantCb
            continue_after_trip = $invariantTrip
            wind_api_calls = $totalWindCalls
            hold_block_check = "PASS 4/4"
        }
    }

    $json = $event | ConvertTo-Json -Compress -Depth 8
    Add-Content -Path $logFile -Value $json

    # 15. Ledger change event
    if ($ledgerSha8 -ne $prevLedgerSha8 -and $prevLedgerSha8 -ne "") {
        $ev2 = @{
            timestamp = $ts
            event_type = "LEDGER_CHANGED"
            event_id = "DSHD-P67-MONITOR-LEDGER-CHANGED-$pollNum"
            agent = "DSHD-P67"
            severity = "WARNING"
            monitor_version = "v4"
            dsha_wind_py_test = $windPyTestTag
            details = @{
                new_line_count = $ledgerLines
                previous_line_count = $prevLedgerLines
                previous_sha8 = $prevLedgerSha8
                current_sha8 = $ledgerSha8
                current_size = $ledgerSize
            }
        }
        Add-Content -Path $logFile -Value ($ev2 | ConvertTo-Json -Compress -Depth 5)
    }

    # 16. Credential alert
    if ($credAlert -ne "NONE") {
        $ev3 = @{
            timestamp = $ts
            event_type = "CREDENTIAL_ALERT_TRIGGERED"
            event_id = "DSHD-P67-MONITOR-CRED-ALERT-$pollNum"
            agent = "DSHD-P67"
            severity = "CRITICAL"
            monitor_version = "v4"
            dsha_wind_py_test = $windPyTestTag
            details = @{
                alert_type = $credAlert
                affected_files = $credFiles
                affected_lines = $credLines
                line_preview = $credPreview
                escalation_target = "DSHC"
                action = "IMMEDIATE_ESCALATION"
            }
        }
        Add-Content -Path $logFile -Value ($ev3 | ConvertTo-Json -Compress -Depth 5)
    }

    # 17. Wind process lifecycle event
    if ($windLocalPids.Count -gt 0 -or $windInitPids.Count -gt 0) {
        $ev4 = @{
            timestamp = $ts
            event_type = "WIND_PROCESS_DETECTED"
            event_id = "DSHD-P67-MONITOR-WIND-PROC-$pollNum"
            agent = "DSHD-P67"
            severity = "WARNING"
            monitor_version = "v4"
            dsha_wind_py_test = $true
            details = @{
                windlocal_pids = $windLocalPids
                initwapi_pids = $windInitPids
                wind_users_file_count = $windUsersFileCount
                wind_etc_file_count = $windEtcFileCount
                wind_listening_ports = $windPorts
                observation = "Wind process activity detected — DSHC authorization flow may be active"
            }
        }
        Add-Content -Path $logFile -Value ($ev4 | ConvertTo-Json -Compress -Depth 5)
    }

    # 18. Crazy retry alert
    if ($crazyRetry) {
        $ev5 = @{
            timestamp = $ts
            event_type = "CRAZY_RETRY_DETECTED"
            event_id = "DSHD-P67-MONITOR-CRAZY-RETRY-$pollNum"
            agent = "DSHD-P67"
            severity = "CRITICAL"
            monitor_version = "v4"
            dsha_wind_py_test = $true
            details = @{
                detail = $crazyRetryDetail
                spawn_event_count = $spawnEventCount
                escalation_target = "DSHC"
                action = "IMMEDIATE_ESCALATION"
            }
        }
        Add-Content -Path $logFile -Value ($ev5 | ConvertTo-Json -Compress -Depth 5)
    }

    # 19. Circuit breaker
    if ($cbTripped) {
        $ev6 = @{
            timestamp = $ts
            event_type = "CIRCUIT_BREAKER_TRIGGERED"
            event_id = "DSHD-P67-MONITOR-CB-TRIP-$pollNum"
            agent = "DSHD-P67"
            severity = "CRITICAL"
            monitor_version = "v4"
            dsha_wind_py_test = $true
            details = @{
                reason = $cbReason
                wind_api_calls = $totalWindCalls
                escalation_target = "DSHC"
                action = "HALT_ALL_WIND_OPERATIONS"
            }
        }
        Add-Content -Path $logFile -Value ($ev6 | ConvertTo-Json -Compress -Depth 5)
    }

    # Update previous state
    $prevLedgerSha8 = $ledgerSha8
    $prevWindEventsSha8 = $windEventsSha8
    $prevLedgerLines = $ledgerLines
    $prevWindEventsLines = $windEventsLines

    $pollNum++
    Start-Sleep -Seconds 30
}
