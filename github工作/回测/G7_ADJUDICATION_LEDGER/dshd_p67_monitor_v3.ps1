# DSHD-P67 Monitor v3 — Wind Py Test Specialized
$ErrorActionPreference = 'SilentlyContinue'

$ledger    = "D:\DSH_WORK\github工作\回测\tracking_monitor_audit.jsonl"
$logFile   = "D:\DSH_WORK\github工作\回测\G7_ADJUDICATION_LEDGER\dshd_p67_monitor_log.jsonl"
$xlsxDir   = "D:\DSH_WORK\github工作\回测\data-harbor\dsha_p49_prep\P49_backtest_audit\wind_excel_data"
$windDir   = "D:\DSH_WORK\github工作\回测\data-harbor\dsha_p49_prep\P49_backtest_audit"
$windLog   = "$windDir\wind_excel_events.jsonl"
$pipelineFile = "$windDir\wind_data_pull_pipeline.py"
$pollNum   = 42
$credBaselineLines = 39

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
    
    # 3. XLSX files
    $xlsxCount = 0
    if (Test-Path $xlsxDir) {
        $xlsxCount = (Get-ChildItem $xlsxDir -Filter "*.xlsx" -ErrorAction SilentlyContinue).Count
        if (-not $xlsxCount) { $xlsxCount = 0 }
    }
    
    # 4. Wind events
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
    
    # 6. Pipeline process detection
    $pipelineRunning = 0
    $windScriptPids = @()
    $pyProcesses = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue
    if ($pyProcesses) {
        foreach ($p in $pyProcesses) {
            if ($p.CommandLine -match 'wind_data_pull_pipeline\.py') { $pipelineRunning++ }
            if ($p.CommandLine -match 'wind.*\.py|WindPy') { $windScriptPids += $p.ProcessId }
        }
    }
    
    # 7. Credential scan
    $credAlert = "NONE"; $credPreview = ""
    if ($ledgerLines -gt $credBaselineLines) {
        $newCount = $ledgerLines - $credBaselineLines
        $allLines = $ledgerRaw -split "`r?`n" | Where { $_.Trim() -ne '' }
        $newLines = $allLines | Select-Object -Last $newCount
        foreach ($nl in $newLines) {
            if ($nl -match 'credentials_provided|password|passwd|api_key|token|secret|Tyq1999') {
                $credAlert = "CRITICAL_CREDENTIAL_DETECTED"
                $credPreview = $nl.Substring(0, [Math]::Min(200, $nl.Length))
                break
            }
        }
    }
    
    # 8. Circuit breaker
    $cbTripped = $false; $cbReason = ""
    if ($totalWindCalls -gt 0 -or $pipelineRunning -gt 0) {
        $cbTripped = $true
        $cbReasons = @()
        if ($totalWindCalls -gt 0) { $cbReasons += "wind_api_calls=$totalWindCalls" }
        if ($pipelineRunning -gt 0) { $cbReasons += "pipeline_process_active" }
        $cbReason = $cbReasons -join ";"
    }
    
    # 9. Severity
    if ($cbTripped) { $severity = "CRITICAL" }
    elseif ($credAlert -ne "NONE") { $severity = "CRITICAL" }
    elseif ($ledgerLines -gt $credBaselineLines) { $severity = "WARNING" }
    else { $severity = "OK" }
    
    # 10. DSHA_WIND_PY_TEST tag
    $windPyTestTag = $false; $tagReasons = @()
    if ($totalWindCalls -gt 0) { $tagReasons += "wind_api_calls=$totalWindCalls" }
    if ($windEventsLines -gt 28) { $tagReasons += "wind_events_grew" }
    if ($pipelineRunning -gt 0) { $tagReasons += "pipeline_active" }
    if ($windScriptPids.Count -gt 0) { $tagReasons += "wind_script_procs=$($windScriptPids.Count)" }
    if ($tagReasons.Count -gt 0) { $windPyTestTag = $true }
    
    # 11. Build event
    $invariantCb = "READY"; $invariantTrip = "false"
    if ($cbTripped) { $invariantCb = "TRIPPED"; $invariantTrip = "true" }
    
    $event = @{
        timestamp = $ts
        poll_number = $pollNum
        event_type = "CONTINUOUS_MONITORING_POLL"
        event_id = "DSHD-P67-MONITOR-POLL-$pollNum"
        agent = "DSHD-P67"
        severity = $severity
        monitor_version = "v3"
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
            excel_count = $excelCount
            credential_alert = $credAlert
            wind_api_calls = $totalWindCalls
            pipeline_process_detected = ($pipelineRunning -gt 0)
            wind_script_processes = $windScriptPids.Count
        }
        invariants = @{
            release_permit = "NOT_ISSUED"
            gate = "CLOSED/HOLD"
            circuit_breaker = $invariantCb
            continue_after_trip = $invariantTrip
            wind_api_calls = $totalWindCalls
        }
    }
    
    $json = $event | ConvertTo-Json -Compress -Depth 6
    Add-Content -Path $logFile -Value $json
    
    # 12. Ledger change event
    if ($ledgerLines -gt $credBaselineLines) {
        $ev2 = @{
            timestamp = $ts
            event_type = "LEDGER_CHANGED"
            event_id = "DSHD-P67-MONITOR-LEDGER-CHANGED-$pollNum"
            agent = "DSHD-P67"
            severity = "WARNING"
            dsha_wind_py_test = $windPyTestTag
            details = @{
                new_line_count = $ledgerLines
                previous_line_count = $credBaselineLines
                previous_sha8 = "22B734F8"
                current_sha8 = $ledgerSha8
                current_size = $ledgerSize
            }
        }
        Add-Content -Path $logFile -Value ($ev2 | ConvertTo-Json -Compress -Depth 5)
    }
    
    # 13. Credential alert
    if ($credAlert -ne "NONE") {
        $ev3 = @{
            timestamp = $ts
            event_type = "CREDENTIAL_ALERT_TRIGGERED"
            event_id = "DSHD-P67-MONITOR-CRED-ALERT-$pollNum"
            agent = "DSHD-P67"
            severity = "CRITICAL"
            dsha_wind_py_test = $windPyTestTag
            details = @{
                alert_type = $credAlert
                line_preview = $credPreview
                escalation_target = "DSHC"
                action = "IMMEDIATE_ESCALATION"
            }
        }
        Add-Content -Path $logFile -Value ($ev3 | ConvertTo-Json -Compress -Depth 5)
    }
    
    # 14. Circuit breaker
    if ($cbTripped) {
        $ev4 = @{
            timestamp = $ts
            event_type = "CIRCUIT_BREAKER_TRIGGERED"
            event_id = "DSHD-P67-MONITOR-CB-TRIP-$pollNum"
            agent = "DSHD-P67"
            severity = "CRITICAL"
            dsha_wind_py_test = $true
            details = @{
                reason = $cbReason
                wind_api_calls = $totalWindCalls
                escalation_target = "DSHC"
                action = "HALT_ALL_WIND_OPERATIONS"
            }
        }
        Add-Content -Path $logFile -Value ($ev4 | ConvertTo-Json -Compress -Depth 5)
    }
    
    $pollNum++
    Start-Sleep -Seconds 60
}