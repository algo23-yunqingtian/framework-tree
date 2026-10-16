# DSHD-P67 Monitor v4.1 — Enhanced Authorization Surveillance (30s poll)
# Simplified for PS 5.1 compatibility with diagnostic output
$ErrorActionPreference = 'Continue'

$logFile   = "D:\DSH_WORK\github工作\回测\G7_ADJUDICATION_LEDGER\dshd_p67_monitor_log.jsonl"
$ledger    = "D:\DSH_WORK\github工作\回测\tracking_monitor_audit.jsonl"
$windLog   = "D:\DSH_WORK\github工作\回测\data-harbor\dsha_p49_prep\P49_backtest_audit\wind_excel_events.jsonl"
$windDir   = "D:\DSH_WORK\github工作\回测\data-harbor\dsha_p49_prep\P49_backtest_audit"
$windUsersDir = "$env:USERPROFILE\.wind\WMain\users"

Write-Host "[V4.1] Starting PID=$PID at $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')"

# Dynamic poll number
$pollNum = 500
try {
    $lastLines = Get-Content $logFile -Tail 5 -ErrorAction SilentlyContinue
    foreach ($ll in $lastLines) {
        if ($ll -match '"poll_number":(\d+)') { $pollNum = [int]$Matches[1] + 1 }
    }
} catch { Write-Host "[V4.1] Error reading poll number: $_" }

Write-Host "[V4.1] Starting poll number: $pollNum"

# Write startup marker
$ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"
$startMarker = '{"timestamp":"' + $ts + '","event_type":"MONITOR_V4_STARTED","agent":"DSHD-P67","severity":"INFO","monitor_version":"v4.1","poll_number":' + $pollNum + ',"detail":"v4.1 monitor started PID=' + $PID + '"}'
Add-Content -Path $logFile -Value $startMarker -Encoding UTF8
Write-Host "[V4.1] Startup marker written"

while ($true) {
    try {
        $ts = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"
        Write-Host "[V4.1] Poll $pollNum starting at $ts"

        # 1. Ledger
        $ledgerSha8 = ""; $ledgerLines = 0; $ledgerSize = 0; $ledgerRaw = ""
        if (Test-Path $ledger) {
            $ledgerSha8 = (Get-FileHash $ledger -Algorithm SHA256).Hash.Substring(0,8).ToUpper()
            $ledgerSize = (Get-Item $ledger).Length
            $ledgerRaw = Get-Content $ledger -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
            if ($ledgerRaw) { $ledgerLines = ($ledgerRaw -split "`n" | Where-Object { $_.Trim() -ne '' }).Count }
        }
        Write-Host "[V4.1] Ledger: SHA8=$ledgerSha8 Lines=$ledgerLines Size=$ledgerSize"

        # 2. Wind events
        $windEventsSha8 = ""; $windEventsLines = 0; $windEventsSize = 0
        $windApiCalls = 0
        if (Test-Path $windLog) {
            $windEventsSha8 = (Get-FileHash $windLog -Algorithm SHA256).Hash.Substring(0,8).ToUpper()
            $windEventsSize = (Get-Item $windLog).Length
            $weRaw = Get-Content $windLog -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
            if ($weRaw) {
                $weLines = $weRaw -split "`n" | Where-Object { $_.Trim() -ne '' }
                $windEventsLines = $weLines.Count
            }
        }
        Write-Host "[V4.1] Wind events: SHA8=$windEventsSha8 Lines=$windEventsLines"

        # 3. Ledger wind_api_calls
        $ledgerApiCalls = 0
        if ($ledgerLines -gt 0 -and $ledgerRaw) {
            $llLines = $ledgerRaw -split "`n" | Where-Object { $_.Trim() -ne '' }
            foreach ($ll in $llLines) {
                try { $ev = $ll | ConvertFrom-Json; if ($ev.wind_api_calls -ne $null) { $ledgerApiCalls += [int]$ev.wind_api_calls } } catch {}
            }
        }
        $totalWindCalls = [Math]::Max($windApiCalls, $ledgerApiCalls)

        # 4. Wind processes
        $windLocalPids = @(); $windInitPids = @(); $pipelineRunning = 0; $windScriptPids = @()
        $allProcs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue
        if ($allProcs) {
            foreach ($p in $allProcs) {
                $cmdline = $p.CommandLine; $pname = $p.Name
                if ($cmdline -match 'wind_data_pull_pipeline') { $pipelineRunning++ }
                if ($cmdline -match 'wind.*\.py|WindPy') { $windScriptPids += $p.ProcessId }
                if ($pname -match 'windlocal') { $windLocalPids += $p.ProcessId }
                if ($pname -match 'InitWAPI') { $windInitPids += $p.ProcessId }
            }
        }
        Write-Host "[V4.1] Wind procs: local=$($windLocalPids.Count) init=$($windInitPids.Count) script=$($windScriptPids.Count) pipeline=$pipelineRunning"

        # 5. .wind directory
        $windUsersFileCount = 0
        if (Test-Path $windUsersDir) {
            $windUsersFiles = Get-ChildItem $windUsersDir -ErrorAction SilentlyContinue
            $windUsersFileCount = if ($windUsersFiles) { $windUsersFiles.Count } else { 0 }
        }

        # 6. Listening ports (Wind range)
        $windPorts = @()
        $listenConns = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue
        if ($listenConns) {
            foreach ($c in $listenConns) {
                if ($c.LocalPort -ge 62000 -and $c.LocalPort -le 64000) {
                    $windPorts += @{ port = $c.LocalPort; pid = $c.OwningProcess }
                }
            }
        }

        # 7. Credential scan
        $credAlert = "NONE"; $credFiles = @(); $credLines = @()
        $credPattern = 'credentials_provided|password|passwd|api_key|token|secret|Tyq1999|13199157886'
        if ($ledgerRaw) {
            $allLedgerLines = $ledgerRaw -split "`n" | Where-Object { $_.Trim() -ne '' }
            for ($i = 0; $i -lt $allLedgerLines.Count; $i++) {
                if ($allLedgerLines[$i] -match $credPattern) {
                    $credAlert = "CRITICAL_CREDENTIAL_DETECTED"; $credFiles += "tracking_monitor_audit.jsonl"; $credLines += ($i + 1)
                }
            }
        }
        if ($weRaw) {
            $weAllLines = $weRaw -split "`n" | Where-Object { $_.Trim() -ne '' }
            for ($i = 0; $i -lt $weAllLines.Count; $i++) {
                if ($weAllLines[$i] -match $credPattern) {
                    $credAlert = "CRITICAL_CREDENTIAL_DETECTED"; $credFiles += "wind_excel_events.jsonl"; $credLines += ($i + 1)
                }
            }
        }
        Write-Host "[V4.1] Credential alert: $credAlert (files=$($credFiles -join ','), lines=$($credLines -join ','))"

        # 8. Circuit breaker
        $cbTripped = $false; $cbReason = ""
        if ($totalWindCalls -gt 0 -or $pipelineRunning -gt 0) {
            $cbTripped = $true
            $reasons = @()
            if ($totalWindCalls -gt 0) { $reasons += "wind_api_calls=$totalWindCalls" }
            if ($pipelineRunning -gt 0) { $reasons += "pipeline_active" }
            $cbReason = $reasons -join ";"
        }

        # 9. Severity
        if ($cbTripped) { $severity = "CRITICAL" }
        elseif ($credAlert -ne "NONE") { $severity = "CRITICAL" }
        elseif ($windLocalPids.Count -gt 0 -or $windInitPids.Count -gt 0) { $severity = "WARNING" }
        else { $severity = "OK" }

        # 10. Build event
        $event = @{
            timestamp = $ts
            poll_number = $pollNum
            event_type = "CONTINUOUS_MONITORING_POLL"
            event_id = "DSHD-P67-MONITOR-POLL-$pollNum"
            agent = "DSHD-P67"
            severity = $severity
            monitor_version = "v4.1"
            poll_interval_seconds = 30
            dsha_wind_py_test = ($windLocalPids.Count -gt 0 -or $windInitPids.Count -gt 0 -or $totalWindCalls -gt 0)
            results = @{
                ledger_sha8 = $ledgerSha8
                ledger_lines = $ledgerLines
                wind_events_sha8 = $windEventsSha8
                wind_events_lines = $windEventsLines
                wind_api_calls = $totalWindCalls
                pipeline_process_detected = ($pipelineRunning -gt 0)
                wind_script_processes = $windScriptPids.Count
                windlocal_pids = $windLocalPids
                initwapi_pids = $windInitPids
                wind_users_file_count = $windUsersFileCount
                wind_listening_ports = $windPorts
                credential_alert = $credAlert
            }
            invariants = @{
                release_permit = "NOT_ISSUED"
                gate = "CLOSED/HOLD"
                circuit_breaker = $(if ($cbTripped) { "TRIPPED" } else { "READY" })
                wind_api_calls = $totalWindCalls
            }
        }

        $json = $event | ConvertTo-Json -Compress -Depth 6
        Add-Content -Path $logFile -Value $json -Encoding UTF8
        Write-Host "[V4.1] Poll $pollNum written to log"

        # 11. Credential alert event
        if ($credAlert -ne "NONE") {
            $credEvent = @{
                timestamp = $ts
                event_type = "CREDENTIAL_ALERT_TRIGGERED"
                event_id = "DSHD-P67-MONITOR-CRED-ALERT-$pollNum"
                agent = "DSHD-P67"
                severity = "CRITICAL"
                monitor_version = "v4.1"
                details = @{
                    alert_type = $credAlert
                    affected_files = $credFiles
                    affected_lines = $credLines
                    escalation_target = "DSHC"
                }
            }
            Add-Content -Path $logFile -Value ($credEvent | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8
            Write-Host "[V4.1] Credential alert written"
        }

        # 12. Wind process event
        if ($windLocalPids.Count -gt 0 -or $windInitPids.Count -gt 0) {
            $procEvent = @{
                timestamp = $ts
                event_type = "WIND_PROCESS_DETECTED"
                event_id = "DSHD-P67-MONITOR-WIND-PROC-$pollNum"
                agent = "DSHD-P67"
                severity = "WARNING"
                monitor_version = "v4.1"
                details = @{
                    windlocal_pids = $windLocalPids
                    initwapi_pids = $windInitPids
                    wind_users_file_count = $windUsersFileCount
                    wind_listening_ports = $windPorts
                }
            }
            Add-Content -Path $logFile -Value ($procEvent | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8
            Write-Host "[V4.1] Wind process event written"
        }

        $pollNum++
    } catch {
        Write-Host "[V4.1] ERROR in poll loop: $_"
        Write-Host "[V4.1] Stack: $($_.ScriptStackTrace)"
    }

    Start-Sleep -Seconds 30
}
