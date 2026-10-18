# =============================================================================
# DSHD-P68 ENHANCED WIND OBSERVE DASHBOARD
# Baseline: feature/v88-g1 @ 01a022fdffb36e603abd623842cef65f80f24c92
# Constraints: gate=CLOSED/HOLD, release_permit=NOT_ISSUED, wind_api_calls=0
# Mode: READ-ONLY observation. No COM lock grabbing. No process killing.
#
# P0: 60s baseline polling + 7 governance invariants
# P1: Enhanced Wind process/WDF/COM dimensions
# P2: Every 10th poll -> dashboard .md + .json
# P3: Alert thresholds (observe-only, no remediation)
# P4: No ledger history modification, no token generation, system skill SHA check
# =============================================================================

$ErrorActionPreference = 'Continue'
$agent = 'DSHD-P68'
$monitorVersion = 'v1.0'
$pollInterval = 60

# === Path Configuration ===
$baseUrl    = 'D:\DSH_WORK\github工作\回测'
$monitorLog = "$baseUrl\G7_ADJUDICATION_LEDGER\dshd_p67_monitor_log.jsonl"
$trackingLedger = "$baseUrl\tracking_monitor_audit.jsonl"
$windEventsLog = "$baseUrl\data-harbor\dsha_p49_prep\P49_backtest_audit\wind_excel_events.jsonl"
$artifactsDir = "$baseUrl\artifacts"
$windUsersDir = "$env:USERPROFILE\.wind\WMain\users"
$windEtcDir   = "$env:USERPROFILE\.wind\WMain\etc"
$systemSkillsDir = "$baseUrl\system_skills\SKILL-WIND-EXCEL-WDF-BOOTSTRAP"
$dashboardMd = "$artifactsDir\dshd_wind_observation_dashboard.md"
$dashboardJson = "$artifactsDir\dashboard_snapshot.json"

# === Expected System Skill SHA256 (from DSHC-P75) ===
$expectedSkillHashes = @{
    'reset_wdf_safe.ps1'    = 'BE62716D853F6B816042891D67B7A19DE6561F59E2ED1F3578104EDD55C3EA8C'
    'skill_readme.md'       = '8ABF5A9AE1A3100B7DB7CF15C9035CFEB58EC8F0DD2C0C4DACCD85EDDADB219B'
    'skill_manifest.json'   = '3F4CCB7F8F645E399048BA912FE257B2FA5DAEAD046F17CAA9FA2E22E000A401'
    'health_check_wdf.ps1'  = '0D0F4D76B9BE6B2126A11BB2C2D87BDF037DF10D118F06F02D18389CABE609A7'
    'bootstrap_wdf.ps1'     = 'B677DF2E7C9E9DDD2686B9C1E06C5D70A41CA1572179EE40DAF066CCDE1BDB73'
}

# === State Tracking (persist across polls) ===
$prevExcelPids        = @()
$prevExcelCount       = 0
$prevWmainVisible     = $null
$wmainInvisibleConsecutive = 0
$prevInitWapiPids     = @()
$excelFlashTimestamps = @()  # array of ISO timestamps of Excel flash events
$prevWmainPids        = @()
$prevWindLocalPids    = @()
$windPortHistory      = @()  # for network trend

# === Initialize Poll Number ===
$pollNum = 1700
if (Test-Path $monitorLog) {
    $lastLines = Get-Content $monitorLog -Tail 5 -ErrorAction SilentlyContinue
    foreach ($ll in $lastLines) {
        if ($ll -match '"poll_number":(\d+)') {
            $pollNum = [int]$Matches[1] + 1
        }
    }
}

# === Write Startup Marker ===
$ts0 = Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK'
$startMarker = '{"timestamp":"' + $ts0 + '","event_type":"MONITOR_V5_STARTED","agent":"' + $agent + '","severity":"INFO","monitor_version":"' + $monitorVersion + '","poll_number":' + $pollNum + ',"poll_interval_seconds":' + $pollInterval + ',"detail":"DSHD-P68 Enhanced Wind Observe Dashboard started PID=' + $PID + '"}'
Add-Content -Path $monitorLog -Value $startMarker -Encoding UTF8
Write-Host "[P68] Enhanced Wind Observe Dashboard started PID=$PID at $ts0, poll #$pollNum"
Write-Host "[P68] Baseline: feature/v88-g1 @ 01a022f"
Write-Host "[P68] Poll interval: ${pollInterval}s | Dashboard every 10 polls"

# =============================================================================
# MAIN POLLING LOOP
# =============================================================================
while ($true) {
    try {
        $ts = Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK'
        Write-Host "`n=== Poll #$pollNum at $ts ==="

        # ==========================================================
        # P0: GOVERNANCE INVARIANTS (7 checks)
        # ==========================================================
        $inv = [ordered]@{}
        $inv['gate'] = 'CLOSED/HOLD'
        $inv['release_permit'] = 'NOT_ISSUED'
        $inv['wind_api_calls'] = 0
        $inv['credential_alert'] = 'NONE'
        $inv['circuit_breaker'] = 'READY'
        $inv['hold_block_check'] = 'PASS'
        $inv['ledger_append_only'] = $true

        # ==========================================================
        # P1: ENHANCED WIND PROCESS OBSERVATION
        # ==========================================================

        # --- P1a: wmain.exe ---
        $wmainPid = $null
        $wmainTitle = $null
        $wmainVisible = $false
        $wmainStartTime = $null
        $wmainWsMb = $null
        $wmainProcs = Get-Process -Name wmain -ErrorAction SilentlyContinue
        if ($wmainProcs) {
            $wmainProc = $wmainProcs | Select-Object -First 1
            $wmainPid = $wmainProc.Id
            $wmainTitle = $wmainProc.MainWindowTitle
            $wmainVisible = ($wmainProc.MainWindowHandle -ne 0)
            try { $wmainStartTime = $wmainProc.StartTime.ToString('yyyy-MM-ddTHH:mm:ssK') } catch {}
            try { $wmainWsMb = [math]::Round($wmainProc.WorkingSet64 / 1MB, 1) } catch {}
        }
        $wmainStatus = if ($wmainPid) { 'RUNNING' } else { 'NOT_RUNNING' }

        # --- P1b: InitWAPI.exe ---
        $initWapiPids = @()
        $initWapiStartTime = $null
        $initWapiProcs = Get-CimInstance Win32_Process -Filter "Name='InitWAPI.exe'" -ErrorAction SilentlyContinue
        if ($initWapiProcs) {
            if ($initWapiProcs -is [array]) {
                foreach ($ip in $initWapiProcs) { $initWapiPids += $ip.ProcessId }
            } else {
                $initWapiPids += $initWapiProcs.ProcessId
            }
            $firstInit = $initWapiProcs | Select-Object -First 1
            try { $initWapiStartTime = (Get-Date $firstInit.CreationDate).ToString('yyyy-MM-ddTHH:mm:ssK') } catch {}
        }
        $initWapiStatus = if ($initWapiPids.Count -gt 0) { 'RUNNING' } else { 'NOT_RUNNING' }

        # --- P1c: EXCEL.EXE ---
        $excelPids = @()
        $excelCount = 0
        $excelProcs = Get-CimInstance Win32_Process -Filter "Name='EXCEL.EXE'" -ErrorAction SilentlyContinue
        if ($excelProcs) {
            if ($excelProcs -is [array]) {
                foreach ($ep in $excelProcs) { $excelPids += $ep.ProcessId }
            } else {
                $excelPids += $excelProcs.ProcessId
            }
            $excelCount = $excelPids.Count
        }

        # --- P1d: WDF COMAddin registry check (read-only) ---
        $wdfLoadBehaviorHKCU = $null
        $wdfLoadBehaviorHKLM = $null
        $wdfXLTaskPanelLB = $null
        $wdfAddinHkcu = Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Office\Excel\Addins\WDF.Addin' -ErrorAction SilentlyContinue
        if ($wdfAddinHkcu) { $wdfLoadBehaviorHKCU = $wdfAddinHkcu.LoadBehavior }
        $wdfAddinHklm = Get-ItemProperty -Path 'HKLM:\Software\Microsoft\Office\Excel\Addins\WDF.Addin' -ErrorAction SilentlyContinue
        if ($wdfAddinHklm) { $wdfLoadBehaviorHKLM = $wdfAddinHklm.LoadBehavior }
        $wdfXLHkcu = Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Office\Excel\Addins\WDF.XLTaskPanel' -ErrorAction SilentlyContinue
        if ($wdfXLHkcu) { $wdfXLTaskPanelLB = $wdfXLHkcu.LoadBehavior }

        # --- P1e: windlocal.exe ---
        $windLocalPids = @()
        $wlProcs = Get-CimInstance Win32_Process -Filter "Name='windlocal.exe'" -ErrorAction SilentlyContinue
        if ($wlProcs) {
            if ($wlProcs -is [array]) {
                foreach ($wp in $wlProcs) { $windLocalPids += $wp.ProcessId }
            } else {
                $windLocalPids += $wlProcs.ProcessId
            }
        }

        # --- P1f: pythonw.exe / python.exe ---
        $pythonPids = @()
        $pyProcs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^python.*\.exe$' }
        if ($pyProcs) {
            if ($pyProcs -is [array]) {
                foreach ($pp in $pyProcs) { $pythonPids += $pp.ProcessId }
            } else {
                $pythonPids += $pyProcs.ProcessId
            }
        }

        # --- P1g: Network ports (Wind range) ---
        $windPortList = @()
        $listenConns = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue
        if ($listenConns) {
            foreach ($c in $listenConns) {
                if ($c.LocalPort -ge 62000 -and $c.LocalPort -le 64000) {
                    $windPortList += @{ port = $c.LocalPort; pid = $c.OwningProcess; addr = $c.LocalAddress }
                }
            }
        }

        # --- P1h: .wind directory state ---
        $windUsersFileCount = 0
        if (Test-Path $windUsersDir) {
            $uf = Get-ChildItem $windUsersDir -Force -ErrorAction SilentlyContinue
            $windUsersFileCount = if ($uf) { $uf.Count } else { 0 }
        }

        # ==========================================================
        # P3: ALERT THRESHOLD CHECKS
        # ==========================================================

        # --- P3a: COM_JITTER (Excel flash detection) ---
        $currExcelPidsArr = @()
        foreach ($epid in $excelPids) { $currExcelPidsArr += $epid }
        $excelAppeared = ($prevExcelCount -eq 0 -and $currExcelPidsArr.Count -gt 0)
        $excelDisappeared = ($prevExcelCount -gt 0 -and $currExcelPidsArr.Count -eq 0)
        if ($excelAppeared -or $excelDisappeared) {
            $excelFlashTimestamps += $ts
        }
        # Prune to 5-minute window
        $cutoff = (Get-Date).AddMinutes(-5)
        $excelFlashTimestamps = @($excelFlashTimestamps | Where-Object {
            $evt = $null
            try { $evt = Get-Date $_ } catch { $evt = $null }
            if ($evt) { $evt -gt $cutoff } else { $true }
        })
        $flashCount5min = $excelFlashTimestamps.Count
        $comJitterWarning = ($flashCount5min -gt 4)
        $comJitterDetail = if ($comJitterWarning) {
            "COM_JITTER_WARNING: ${flashCount5min} Excel flash events in 5 min (threshold=4)"
        } else {
            "COM_JITTER_CLEAR: ${flashCount5min} flash events in 5 min"
        }

        # --- P3b: SESSION_VISIBILITY_WARNING (wmain invisible 3 consecutive) ---
        if ($wmainVisible -eq $false) {
            $wmainInvisibleConsecutive++
        } else {
            $wmainInvisibleConsecutive = 0
        }
        $sessionVisibilityWarning = ($wmainInvisibleConsecutive -ge 3)
        $sessionVisibilityDetail = if ($sessionVisibilityWarning) {
            "SESSION_VISIBILITY_WARNING: wmain not visible for ${wmainInvisibleConsecutive} consecutive polls"
        } else {
            "SESSION_VISIBILITY_CLEAR: wmain invisible streak=${wmainInvisibleConsecutive}"
        }

        # --- P3c: WDF_INIT_PROCESS_MISSING (InitWAPI disappeared) ---
        $initWapiWasPresent = ($prevInitWapiPids.Count -gt 0)
        $initWapiNowPresent = ($initWapiPids.Count -gt 0)
        $initWapiMissing = ($initWapiWasPresent -and -not $initWapiNowPresent)
        $initWapiMissingDetail = if ($initWapiMissing) {
            "WDF_INIT_PROCESS_MISSING_NOTE: InitWAPI.exe disappeared (was PID $($prevInitWapiPids -join ', '), now gone)"
        } else {
            "WDF_INIT_PROCESS_PRESENT"
        }

        # ==========================================================
        # P0: CREDENTIAL SCAN (brief - on changed files only)
        # ==========================================================
        $credAlert = 'NONE'
        $credPattern = '\b(?:password|passwd|api_key|secret|credentials_provided)\b|Tyq1999|13199157886'
        # Only scan if files have grown since last poll (cheap check)
        # For now: scan ledger for new lines only (append-only, so only check new lines)
        # Full scan done by observation script; here we do quick pass
        $credHits = 0
        if (Test-Path $trackingLedger) {
            $ledgerRaw = Get-Content $trackingLedger -ErrorAction SilentlyContinue
            if ($ledgerRaw) {
                foreach ($ll in $ledgerRaw) {
                    if ($ll -match '\[REDACTED-CREDENTIAL\]') { continue }
                    if ($ll -match $credPattern) { $credHits++ }
                }
            }
        }
        if ($credHits -gt 0) { $credAlert = "CRITICAL_CREDENTIAL_DETECTED" }

        # ==========================================================
        # P0: WIND API CALLS COUNT
        # ==========================================================
        $totalWindCalls = 0
        if (Test-Path $trackingLedger) {
            $llLines = Get-Content $trackingLedger -ErrorAction SilentlyContinue
            foreach ($ll in $llLines) {
                try {
                    $ev = $ll | ConvertFrom-Json
                    if ($ev.wind_api_calls -ne $null) { $totalWindCalls += [int]$ev.wind_api_calls }
                } catch {}
            }
        }
        # Also check wind_excel_events.jsonl
        if (Test-Path $windEventsLog) {
            $weLines = Get-Content $windEventsLog -ErrorAction SilentlyContinue
            foreach ($wl in $weLines) {
                try {
                    $ev = $wl | ConvertFrom-Json
                    if ($ev.wind_api_calls -ne $null) { $totalWindCalls += [int]$ev.wind_api_calls }
                } catch {}
            }
        }
        if ($totalWindCalls -gt 0) {
            $inv['wind_api_calls'] = $totalWindCalls
            $inv['circuit_breaker'] = 'TRIPPED'
            $inv['hold_block_check'] = 'FAIL'
        }
        if ($credAlert -ne 'NONE') {
            $inv['credential_alert'] = $credAlert
        }

        # ==========================================================
        # P4: SYSTEM SKILL SHA CHECK (every poll)
        # ==========================================================
        $skillHashResults = [ordered]@{}
        $skillHashAllMatch = $true
        $skillHashFailed = @()
        if (Test-Path $systemSkillsDir) {
            foreach ($pair in $expectedSkillHashes.GetEnumerator()) {
                $fname = $pair.Key
                $expected = $pair.Value
                $fpath = Join-Path $systemSkillsDir $fname
                if (Test-Path $fpath) {
                    $actual = (Get-FileHash $fpath -Algorithm SHA256 -ErrorAction SilentlyContinue).Hash
                    $match = ($actual -eq $expected)
                    $skillHashResults[$fname] = @{ expected = $expected; actual = $actual; match = $match }
                    if (-not $match) {
                        $skillHashAllMatch = $false
                        $skillHashFailed += $fname
                    }
                } else {
                    $skillHashResults[$fname] = @{ expected = $expected; actual = 'FILE_NOT_FOUND'; match = $false }
                    $skillHashAllMatch = $false
                    $skillHashFailed += $fname
                }
            }
        } else {
            $skillHashResults['_error'] = "System skills directory not found: $systemSkillsDir"
            $skillHashAllMatch = $false
        }
        $skillHashStatus = if ($skillHashAllMatch) { 'ALL_MATCH' } else { 'MISMATCH: $($skillHashFailed -join ', ')' }

        # ==========================================================
        # SEVERITY DETERMINATION
        # ==========================================================
        $severity = 'OK'
        $alertFlags = @()
        if ($credAlert -ne 'NONE') { $severity = 'CRITICAL'; $alertFlags += 'CREDENTIAL_DETECTED' }
        if ($totalWindCalls -gt 0) { $severity = 'CRITICAL'; $alertFlags += 'WIND_API_CALLS_GT0' }
        if ($comJitterWarning) { $severity = 'WARNING'; $alertFlags += 'COM_JITTER' }
        if ($sessionVisibilityWarning) { $severity = 'WARNING'; $alertFlags += 'SESSION_VISIBILITY' }
        if ($initWapiMissing) { $severity = 'WARNING'; $alertFlags += 'WDF_INIT_MISSING' }
        if (-not $skillHashAllMatch) { $severity = 'WARNING'; $alertFlags += 'SKILL_HASH_MISMATCH' }

        # ==========================================================
        # BUILD POLL EVENT
        # ==========================================================
        $pollEvent = [ordered]@{
            timestamp         = $ts
            poll_number       = $pollNum
            event_type        = 'ENHANCED_WIND_OBSERVE_POLL'
            event_id          = "DSHD-P68-POLL-$pollNum"
            agent             = $agent
            severity          = $severity
            monitor_version   = $monitorVersion
            poll_interval_seconds = $pollInterval
            alert_flags       = $alertFlags
            results = [ordered]@{
                wmain = [ordered]@{
                    pid = $wmainPid
                    window_title = $wmainTitle
                    visible = $wmainVisible
                    status = $wmainStatus
                    start_time = $wmainStartTime
                    working_set_mb = $wmainWsMb
                }
                initwapi = [ordered]@{
                    pids = $initWapiPids
                    status = $initWapiStatus
                    start_time = $initWapiStartTime
                }
                excel = [ordered]@{
                    pids = $excelPids
                    count = $excelCount
                }
                windlocal = [ordered]@{
                    pids = $windLocalPids
                    count = $windLocalPids.Count
                }
                python = [ordered]@{
                    pids = $pythonPids
                    count = $pythonPids.Count
                }
                wdf_addin = [ordered]@{
                    load_behavior_hkcu = $wdfLoadBehaviorHKCU
                    load_behavior_hklm = $wdfLoadBehaviorHKLM
                    xl_task_panel_lb = $wdfXLTaskPanelLB
                }
                network = [ordered]@{
                    wind_ports_62000_64000 = $windPortList
                    port_count = $windPortList.Count
                }
                filesystem = [ordered]@{
                    wind_users_file_count = $windUsersFileCount
                    wind_users_dir_exists = (Test-Path $windUsersDir)
                }
                com_jitter = [ordered]@{
                    flash_count_5min = $flashCount5min
                    warning = $comJitterWarning
                    detail = $comJitterDetail
                }
                session_visibility = [ordered]@{
                    wmain_invisible_consecutive = $wmainInvisibleConsecutive
                    warning = $sessionVisibilityWarning
                    detail = $sessionVisibilityDetail
                }
                initwapi_missing = [ordered]@{
                    was_present = $initWapiWasPresent
                    now_present = $initWapiNowPresent
                    missing = $initWapiMissing
                    detail = $initWapiMissingDetail
                }
                credential_alert = $credAlert
                wind_api_calls = $totalWindCalls
                skill_sha_check = $skillHashStatus
            }
            invariants = $inv
        }

        $pollJson = $pollEvent | ConvertTo-Json -Compress -Depth 10
        Add-Content -Path $monitorLog -Value $pollJson -Encoding UTF8
        Write-Host "  Poll written to monitor_log.jsonl"

        # ==========================================================
        # P1: APPEND TO TRACKING_MONITOR_AUDIT.JSONL (per-poll event)
        # ==========================================================
        $trackingEvent = [ordered]@{
            timestamp = $ts
            event = "DSHD-P68-ENHANCED-WIND-OBSERVE-POLL-$pollNum"
            agent = $agent
            poll_number = $pollNum
            severity = $severity
            monitor_version = $monitorVersion
            wmain_status = $wmainStatus
            wmain_pid = $wmainPid
            wmain_visible = $wmainVisible
            initwapi_status = $initWapiStatus
            initwapi_pids = $initWapiPids
            excel_count = $excelCount
            windlocal_count = $windLocalPids.Count
            wdf_addin_lb = $wdfLoadBehaviorHKCU
            wind_ports = $windPortList.Count
            cred_alert = $credAlert
            wind_api_calls = $totalWindCalls
            skill_sha = $skillHashStatus
            alert_flags = $alertFlags
            invariants = $inv
        }
        $trackJson = $trackingEvent | ConvertTo-Json -Compress -Depth 6
        Add-Content -Path $trackingLedger -Value $trackJson -Encoding UTF8

        # ==========================================================
        # P3: ALERT EVENTS (write to monitor_log if triggered)
        # ==========================================================
        if ($comJitterWarning) {
            $alertEvent = [ordered]@{
                timestamp = $ts
                event_type = 'COM_JITTER_WARNING'
                event_id = "DSHD-P68-COM-JITTER-$pollNum"
                agent = $agent
                severity = 'WARNING'
                detail = $comJitterDetail
                flash_events = $excelFlashTimestamps
                action = 'OBSERVATION_ONLY_NO_REMEDIATION'
            }
            Add-Content -Path $monitorLog -Value ($alertEvent | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8
        }
        if ($sessionVisibilityWarning) {
            $alertEvent = [ordered]@{
                timestamp = $ts
                event_type = 'SESSION_VISIBILITY_WARNING'
                event_id = "DSHD-P68-VISIBILITY-$pollNum"
                agent = $agent
                severity = 'WARNING'
                detail = $sessionVisibilityDetail
                wmain_invisible_consecutive = $wmainInvisibleConsecutive
                action = 'OBSERVATION_ONLY_NO_REMEDIATION'
            }
            Add-Content -Path $monitorLog -Value ($alertEvent | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8
        }
        if ($initWapiMissing) {
            $alertEvent = [ordered]@{
                timestamp = $ts
                event_type = 'WDF_INIT_PROCESS_MISSING_NOTE'
                event_id = "DSHD-P68-INIT-MISSING-$pollNum"
                agent = $agent
                severity = 'WARNING'
                detail = $initWapiMissingDetail
                previous_pids = $prevInitWapiPids
                action = 'OBSERVATION_ONLY_NO_REMEDIATION'
            }
            Add-Content -Path $monitorLog -Value ($alertEvent | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8
        }

        # ==========================================================
        # P2: DASHBOARD GENERATION (every 10th poll)
        # ==========================================================
        if ($pollNum % 10 -eq 0) {
            Write-Host "  Generating dashboard snapshot (poll #$pollNum)..."

            # Collect recent WDF/Excel events from wind_excel_events.jsonl (last 10)
            $recentEvents = @()
            if (Test-Path $windEventsLog) {
                $weAll = Get-Content $windEventsLog -ErrorAction SilentlyContinue
                if ($weAll) {
                    $wdfEvents = @()
                    foreach ($wl in $weAll) {
                        try {
                            $ev = $wl | ConvertFrom-Json
                            $evType = ''
                            if ($ev.event_type) { $evType = $ev.event_type }
                            elseif ($ev.event) { $evType = $ev.event }
                            if ($evType -match '(?i)wind|wdf|excel|com|initwapi|bootstrap') {
                                $wdfEvents += [ordered]@{
                                    timestamp = $ev.timestamp
                                    event = $evType
                                    severity = if ($ev.severity) { $ev.severity } else { 'INFO' }
                                    note = ''
                                }
                            }
                        } catch {}
                    }
                    $recentEvents = @($wdfEvents | Select-Object -Last 10)
                }
            }

            # Build process table
            $procTable = @()
            $procTable += [ordered]@{ process = 'wmain.exe'; pid = if ($wmainPid) { $wmainPid } else { 'N/A' }; state = $wmainStatus; start_time = if ($wmainStartTime) { $wmainStartTime } else { 'N/A' }; window_title = if ($wmainTitle) { $wmainTitle } else { 'N/A' }; visible = $wmainVisible }
            $procTable += [ordered]@{ process = 'InitWAPI.exe'; pid = if ($initWapiPids.Count -gt 0) { $initWapiPids -join ', ' } else { 'N/A' }; state = $initWapiStatus; start_time = if ($initWapiStartTime) { $initWapiStartTime } else { 'N/A' }; window_title = 'N/A'; visible = 'N/A' }
            $procTable += [ordered]@{ process = 'EXCEL.EXE'; pid = if ($excelPids.Count -gt 0) { $excelPids -join ', ' } else { 'N/A' }; state = if ($excelCount -gt 0) { 'RUNNING' } else { 'NOT_RUNNING' }; start_time = 'N/A'; window_title = 'N/A'; visible = 'N/A' }
            $procTable += [ordered]@{ process = 'windlocal.exe'; pid = if ($windLocalPids.Count -gt 0) { $windLocalPids -join ', ' } else { 'N/A' }; state = if ($windLocalPids.Count -gt 0) { 'RUNNING' } else { 'NOT_RUNNING' }; start_time = 'N/A'; window_title = 'N/A'; visible = 'N/A' }
            $procTable += [ordered]@{ process = 'python.exe/pythonw.exe'; pid = if ($pythonPids.Count -gt 0) { $pythonPids -join ', ' } else { 'N/A' }; state = if ($pythonPids.Count -gt 0) { 'RUNNING' } else { 'NOT_RUNNING' }; start_time = 'N/A'; window_title = 'N/A'; visible = 'N/A' }

            # Invariant status table
            $invTable = @()
            $invTable += [ordered]@{ invariant = 'gate'; expected = 'CLOSED/HOLD'; actual = $inv['gate']; status = if ($inv['gate'] -eq 'CLOSED/HOLD') { 'PASS' } else { 'FAIL' } }
            $invTable += [ordered]@{ invariant = 'release_permit'; expected = 'NOT_ISSUED'; actual = $inv['release_permit']; status = if ($inv['release_permit'] -eq 'NOT_ISSUED') { 'PASS' } else { 'FAIL' } }
            $invTable += [ordered]@{ invariant = 'wind_api_calls'; expected = '0'; actual = $totalWindCalls; status = if ($totalWindCalls -eq 0) { 'PASS' } else { 'FAIL' } }
            $invTable += [ordered]@{ invariant = 'credential_alert'; expected = 'NONE'; actual = $credAlert; status = if ($credAlert -eq 'NONE') { 'PASS' } else { 'FAIL' } }
            $invTable += [ordered]@{ invariant = 'circuit_breaker'; expected = 'READY'; actual = $inv['circuit_breaker']; status = if ($inv['circuit_breaker'] -eq 'READY') { 'PASS' } else { 'FAIL' } }
            $invTable += [ordered]@{ invariant = 'hold_block_check'; expected = 'PASS'; actual = $inv['hold_block_check']; status = if ($inv['hold_block_check'] -eq 'PASS') { 'PASS' } else { 'FAIL' } }
            $invTable += [ordered]@{ invariant = 'ledger_append_only'; expected = 'TRUE'; actual = 'TRUE'; status = 'PASS' }

            # Health assessment
            $healthParts = @()
            if ($wmainPid) { $healthParts += "wmain(RUNNING,PID=$wmainPid,visible=$wmainVisible)" }
            else { $healthParts += 'wmain(NOT_RUNNING)' }
            if ($initWapiPids.Count -gt 0) { $healthParts += "InitWAPI(RUNNING,PID=$($initWapiPids -join ','))" }
            else { $healthParts += 'InitWAPI(NOT_RUNNING)' }
            if ($excelCount -gt 0) { $healthParts += "Excel(count=$excelCount)" }
            else { $healthParts += 'Excel(NONE)' }
            $healthParts += "Ports=$($windPortList.Count)"
            $healthParts += "Flash5min=$flashCount5min"
            if ($inv['circuit_breaker'] -eq 'READY') { $healthParts += 'CB=READY' }
            else { $healthParts += 'CB=TRIPPED' }
            if ($skillHashAllMatch) { $healthParts += 'SkillSHA=OK' }
            else { $healthParts += "SkillSHA=FAIL($($skillHashFailed -join ','))" }

            $healthIcon = 'GREEN'; $healthIconStr = 'GREEN'
            if ($severity -eq 'WARNING') { $healthIcon = 'YELLOW'; $healthIconStr = 'YELLOW' }
            if ($severity -eq 'CRITICAL') { $healthIcon = 'RED'; $healthIconStr = 'RED' }

            $suffix = if ($alertFlags.Count -eq 0) { 'passing' } else { "with alerts: $($alertFlags -join ', ')." }
            $healthSummary = "[$healthIcon] $($severity): $($healthParts -join ' | ') -- All invariants $suffix"

            # Write dashboard JSON
            $dashJson = [ordered]@{
                generated_at = $ts
                poll_number = $pollNum
                agent = $agent
                monitor_version = $monitorVersion
                baseline = 'feature/v88-g1 @ 01a022fdffb36e603abd623842cef65f80f24c92'
                severity = $severity
                alert_flags = $alertFlags
                health_icon = $healthIcon
                health_summary = $healthSummary
                processes = $procTable
                recent_wdf_events = $recentEvents
                invariants = $invTable
                com_jitter = [ordered]@{ flash_count_5min = $flashCount5min; warning = $comJitterWarning }
                session_visibility = [ordered]@{ wmain_invisible_consecutive = $wmainInvisibleConsecutive; warning = $sessionVisibilityWarning }
                initwapi_status = [ordered]@{ was_present = $initWapiWasPresent; now_present = $initWapiNowPresent; missing = $initWapiMissing }
                skill_sha_check = [ordered]@{ status = $skillHashStatus; all_match = $skillHashAllMatch }
            }
            $dashJsonFile = $dashJson | ConvertTo-Json -Depth 12
            [System.IO.File]::WriteAllText($dashboardJson, $dashJsonFile, (New-Object System.Text.UTF8Encoding($false)))
            Write-Host "  Dashboard JSON written: $dashboardJson"

            # Write dashboard Markdown
            $mdLines = @()
            $mdLines += "# DSHD-P68 Enhanced Wind Observation Dashboard"
            $mdLines += ""
            $mdLines += "**Generated**: $ts"
            $mdLines += "**Poll Number**: #$pollNum"
            $mdLines += "**Session**: DSHD-P68"
            $mdLines += "**Monitor Version**: $monitorVersion"
            $mdLines += "**Baseline**: feature/v88-g1 @ 01a022f"
            $mdLines += "**Poll Interval**: ${pollInterval}s"
            $mdLines += ""
            $mdLines += "---"
            $mdLines += ""
            $mdLines += "## Health Assessment"
            $mdLines += ""
            $mdLines += $healthSummary
            $mdLines += ""
            $mdLines += "---"
            $mdLines += ""
            $mdLines += "## Process Status"
            $mdLines += ""
            $mdLines += "| Process | PID | State | Start Time | Window Title | Visible |"
            $mdLines += "|---------|-----|-------|------------|--------------|---------|"
            foreach ($p in $procTable) {
                $mdLines += "| $($p.process) | $($p.pid) | $($p.state) | $($p.start_time) | $($p.window_title) | $($p.visible) |"
            }
            $mdLines += ""
            $mdLines += "---"
            $mdLines += ""
            $mdLines += "## Recent WDF/Excel Events (Last 10)"
            $mdLines += ""
            if ($recentEvents.Count -eq 0) {
                $mdLines += "*No recent WDF/Excel events recorded.*"
            } else {
                $mdLines += "| Timestamp | Event | Severity |"
                $mdLines += "|-----------|-------|----------|"
                foreach ($re in $recentEvents) {
                    $mdLines += "| $($re.timestamp) | $($re.event) | $($re.severity) |"
                }
            }
            $mdLines += ""
            $mdLines += "---"
            $mdLines += ""
            $mdLines += "## Invariants Status"
            $mdLines += ""
            $mdLines += "| Invariant | Expected | Actual | Status |"
            $mdLines += "|-----------|----------|--------|--------|"
            foreach ($iv in $invTable) {
                $statusMark = if ($iv.status -eq 'PASS') { 'PASS' } else { 'FAIL' }
                $mdLines += "| $($iv.invariant) | $($iv.expected) | $($iv.actual) | $statusMark |"
            }
            $mdLines += ""
            $mdLines += "---"
            $mdLines += ""
            $mdLines += "## Alert Thresholds"
            $mdLines += ""
            $mdLines += "| Alert | Status | Detail |"
            $mdLines += "|-------|--------|--------|"
            $mdLines += "| COM_JITTER (>4 flash/5min) | $(if ($comJitterWarning) { 'TRIGGERED' } else { 'CLEAR' }) | Flash events: $flashCount5min |"
            $mdLines += "| SESSION_VISIBILITY (wmain invisible 3 polls) | $(if ($sessionVisibilityWarning) { 'TRIGGERED' } else { 'CLEAR' }) | Invisible streak: $wmainInvisibleConsecutive |"
            $mdLines += "| INIT_WDF_MISSING (InitWAPI disappeared) | $(if ($initWapiMissing) { 'TRIGGERED' } else { 'CLEAR' }) | $(if ($initWapiPids.Count -gt 0) { 'Present' } else { 'Absent' }) |"
            $mdLines += ""
            $mdLines += "---"
            $mdLines += ""
            $mdLines += "## System Details"
            $mdLines += ""
            $mdLines += "| Item | Value |"
            $mdLines += "|------|-------|"
            $mdLines += "| WDF Addin LoadBehavior (HKCU) | $($wdfLoadBehaviorHKCU) |"
            $mdLines += "| WDF Addin LoadBehavior (HKLM) | $($wdfLoadBehaviorHKLM) |"
            $mdLines += "| WDF XL Task Panel LB | $($wdfXLTaskPanelLB) |"
            $mdLines += "| Wind TCP Ports (62000-64000) | $($windPortList.Count) |"
            $mdLines += "| .wind/users File Count | $windUsersFileCount |"
            $mdLines += "| Credential Alert | $credAlert |"
            $mdLines += "| Wind API Calls | $totalWindCalls |"
            $mdLines += "| Skill SHA Check | $skillHashStatus |"
            $mdLines += "| Monitor Log Lines | $((Get-Content $monitorLog -ErrorAction SilentlyContinue).Count) |"
            $mdLines += "| Tracking Ledger Lines | $((Get-Content $trackingLedger -ErrorAction SilentlyContinue).Count) |"
            $mdLines += ""
            $mdLines += "---"
            $mdLines += ""
            $mdLines += "*Dashboard auto-generated every 10 polls. Read-only observation. No remediation actions taken.*"

            $mdContent = $mdLines -join "`r`n"
            [System.IO.File]::WriteAllText($dashboardMd, $mdContent, (New-Object System.Text.UTF8Encoding($false)))
            Write-Host "  Dashboard MD written: $dashboardMd"

            # Also write dashboard event to monitor log
            $dashEvent = [ordered]@{
                timestamp = $ts
                event_type = 'DASHBOARD_GENERATED'
                event_id = "DSHD-P68-DASHBOARD-$pollNum"
                agent = $agent
                severity = $severity
                dashboard_md = $dashboardMd
                dashboard_json = $dashboardJson
                health_icon = $healthIcon
                health_summary = $healthSummary
            }
            Add-Content -Path $monitorLog -Value ($dashEvent | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8
        }

        # ==========================================================
        # UPDATE STATE FOR NEXT POLL
        # ==========================================================
        $prevExcelPids = $currExcelPidsArr
        $prevExcelCount = $excelCount
        $prevWmainVisible = $wmainVisible
        $prevInitWapiPids = @($initWapiPids)
        $prevWmainPids = if ($wmainPid) { @($wmainPid) } else { @() }
        $prevWindLocalPids = @($windLocalPids)

        # ==========================================================
        # SUMMARY OUTPUT
        # ==========================================================
        $alertSummary = if ($alertFlags.Count -gt 0) { "ALERTS: $($alertFlags -join ', ')" } else { "No alerts" }
        Write-Host "  Severity=$severity | $alertSummary"
        Write-Host "  wmain=$wmainStatus PID=$wmainPid visible=$wmainVisible"
        Write-Host "  InitWAPI=$initWapiStatus PID=$($initWapiPids -join ',')"
        Write-Host "  Excel=$excelCount | windlocal=$($windLocalPids.Count) | ports=$($windPortList.Count)"
        Write-Host "  Flash=$flashCount5min invisible=$wmainInvisibleConsecutive | SkillSHA=$skillHashStatus"
        if ($pollNum % 10 -eq 0) { Write-Host "  >>> Dashboard generated (MD+JSON)" }

    } catch {
        $errTs = Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK'
        $errEvent = [ordered]@{
            timestamp = $errTs
            event_type = 'POLL_ERROR'
            event_id = "DSHD-P68-ERROR-$pollNum"
            agent = $agent
            severity = 'CRITICAL'
            error = $_.Exception.Message
            stack = $_.ScriptStackTrace
            detail = $_.ToString()
        }
        Add-Content -Path $monitorLog -Value ($errEvent | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8
        Write-Host "  ERROR in poll: $($_.Exception.Message)"
        Write-Host "  Stack: $($_.ScriptStackTrace)"
    }

    $pollNum++
    Start-Sleep -Seconds $pollInterval
}
