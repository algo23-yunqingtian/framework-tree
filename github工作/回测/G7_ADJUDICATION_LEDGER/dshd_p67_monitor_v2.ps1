$ledger = "D:\DSH_WORK\github工作\回测\tracking_monitor_audit.jsonl"
$logFile = "D:\DSH_WORK\github工作\回测\G7_ADJUDICATION_LEDGER\dshd_p67_monitor_log.jsonl"
$xlsxDir = "D:\DSH_WORK\github工作\回测\data-harbor\dsha_p49_prep\P49_backtest_audit\wind_excel_data"
$pollNum = 17

while ($true) {
    $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"
    
    # Check Excel processes
    $excels = Get-Process -Name EXCEL -ErrorAction SilentlyContinue
    $excelCount = if ($excels) { $excels.Count } else { 0 }
    
    # Check ledger
    $ledgerSha8 = ""
    $ledgerLines = 0
    $ledgerSize = 0
    if (Test-Path $ledger) {
        $ledgerSha8 = (Get-FileHash $ledger -Algorithm SHA256).Hash.Substring(0,8)
        $ledgerSize = (Get-Item $ledger).Length
        $content = Get-Content $ledger -Raw
        $ledgerLines = ($content -split "`n" | Where { $_.Trim() -ne '' }).Count
    }
    
    # Check xlsx files
    $xlsxFiles = @()
    if (Test-Path $xlsxDir) {
        $xlsxFiles = Get-ChildItem $xlsxDir -Filter "*.xlsx" -ErrorAction SilentlyContinue
    }
    $xlsxCount = $xlsxFiles.Count
    
    # Check wind events
    $windEventsSha8 = ""
    $windEventsSize = 0
    $windEventsDir = "D:\DSH_WORK\github工作\回测\data-harbor\dsha_p49_prep\P49_backtest_audit"
    $windLog = Get-ChildItem $windEventsDir -Filter "wind_excel_events.jsonl" -ErrorAction SilentlyContinue
    if ($windLog) {
        $windEventsSha8 = (Get-FileHash $windLog.FullName -Algorithm SHA256).Hash.Substring(0,8)
        $windEventsSize = $windLog.Length
    }
    
    # Credential pattern scan (for new entries)
    $credAlert = "NONE"
    $credLine = 0
    if ($ledgerSize -gt 38166) {
        # File grew — check for new credentials
        $lines = $content -split "`n"
        $newLines = $lines | Select-Object -Last ($ledgerLines - 39)
        foreach ($nl in $newLines) {
            if ($nl -match 'credentials_provided|password|passwd|api_key|token|secret') {
                $credAlert = "CRITICAL_CREDENTIAL_DETECTED"
                $credLine = $nl
                break
            }
        }
    }
    
    # Build event
    $severity = if ($credAlert -ne "NONE") { "CRITICAL" } else { "OK" }
    $event = @{
        timestamp = $ts
        poll_number = $pollNum
        event_type = "CONTINUOUS_MONITORING_POLL"
        event_id = "DSHD-P67-MONITOR-POLL-$pollNum"
        agent = "DSHD-P67"
        severity = $severity
        results = @{
            ledger_sha8 = $ledgerSha8
            ledger_lines = $ledgerLines
            ledger_size = $ledgerSize
            wind_events_sha8 = $windEventsSha8
            wind_events_size = $windEventsSize
            xlsx_count = $xlsxCount
            excel_count = $excelCount
            credential_alert = $credAlert
        }
        invariants = @{
            release_permit = "NOT_ISSUED"
            gate = "CLOSED/HOLD"
            circuit_breaker = "READY"
            continue_after_trip = $false
            wind_api_calls = 0
        }
    }
    
    # Write to log
    $json = $event | ConvertTo-Json -Compress -Depth 5
    Add-Content -Path $logFile -Value $json
    
    # Detect anomalies
    if ($ledgerLines -gt 39) {
        $json2 = @{
            timestamp = $ts
            event_type = "LEDGER_CHANGED"
            event_id = "DSHD-P67-MONITOR-LEDGER-CHANGED-$pollNum"
            agent = "DSHD-P67"
            severity = "WARNING"
            details = @{
                new_line_count = $ledgerLines
                previous_line_count = 39
                previous_sha8 = "22B734F8"
                current_sha8 = $ledgerSha8
                current_size = $ledgerSize
            }
        } | ConvertTo-Json -Compress -Depth 5
        Add-Content -Path $logFile -Value $json2
    }
    
    if ($credAlert -ne "NONE") {
        $json3 = @{
            timestamp = $ts
            event_type = "CREDENTIAL_ALERT_TRIGGERED"
            event_id = "DSHD-P67-MONITOR-CRED-ALERT-$pollNum"
            agent = "DSHD-P67"
            severity = "CRITICAL"
            details = @{
                alert_type = $credAlert
                line_preview = ($credLine.Substring(0, [Math]::Min(200, $credLine.Length)))
                escalation_target = "DSHC"
            }
        } | ConvertTo-Json -Compress -Depth 5
        Add-Content -Path $logFile -Value $json3
    }
    
    $pollNum++
    Start-Sleep -Seconds 60
}
