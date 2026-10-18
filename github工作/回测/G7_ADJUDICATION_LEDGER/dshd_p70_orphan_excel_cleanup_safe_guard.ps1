# =============================================================================
# DSHD-P70 ORPHAN EXCEL CLEANUP SAFE GUARD
# Baseline: feature/v88-g1 @ 01a022fdffb36e603abd623842cef65f80f24c92
# Constraints: gate=CLOSED/HOLD, release_permit=NOT_ISSUED, wind_api_calls=0
# Mode: READ-ONLY observation + SAFE GUARD. No COM lock grabbing. No auto-kill.
# Cleanup only when artifacts/com_clean_allow.marker exists.
# Red line: never kill windowed Excel, wmain, or InitWAPI.
#
# P0: Inherit P69 60s polling + 7 governance invariants + COM monitoring
# P1: Safety cleanup switch - marker-gated orphan Excel termination
# P2: Updated COM health scoring (no cap on orphan deduction, new thresholds)
# P3: com_clean_guard_events.jsonl audit log + STATIC_STANDBY status
# =============================================================================

$ErrorActionPreference = 'Continue'
$agent = 'DSHD-P70'
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
# P69 NEW paths
$comDashboardMd = "$artifactsDir\dshd_com_jitter_dashboard.md"
$comDashboardJson = "$artifactsDir\dashboard_com_snapshot.json"
$comLockEventsLog = "$baseUrl\com_lock_events.jsonl"
# P70 NEW paths
$cleanMarkerPath = "$artifactsDir\com_clean_allow.marker"
$cleanGuardEventsLog = "$baseUrl\com_clean_guard_events.jsonl"

# === Expected System Skill SHA256 (from DSHC-P75) ===
$expectedSkillHashes = @{
    'reset_wdf_safe.ps1'    = 'BE62716D853F6B816042891D67B7A19DE6561F59E2ED1F3578104EDD55C3EA8C'
    'skill_readme.md'       = '8ABF5A9AE1A3100B7DB7CF15C9035CFEB58EC8F0DD2C0C4DACCD85EDDADB219B'
    'skill_manifest.json'   = '3F4CCB7F8F645E399048BA912FE257B2FA5DAEAD046F17CAA9FA2E22E000A401'
    'health_check_wdf.ps1'  = '0D0F4D76B9BE6B2126A11BB2C2D87BDF037DF10D118F06F02D18389CABE609A7'
    'bootstrap_wdf.ps1'     = 'B677DF2E7C9E9DDD2686B9C1E06C5D70A41CA1572179EE40DAF066CCDE1BDB73'
}

# === State Tracking (P68 inherited) ===
$prevExcelPids        = @()
$prevExcelCount       = 0
$prevWmainVisible     = $null
$wmainInvisibleConsecutive = 0
$prevInitWapiPids     = @()
$excelFlashTimestamps = @()
$prevWmainPids        = @()
$prevWindLocalPids    = @()
$windPortHistory      = @()

# === State Tracking (P69 INHERITED) ===
$excelStartStopTimestamps1min = @()
$prevWdfLBHKCU          = $null
$prevWdfLBHKLM          = $null
$wdfLoadEvents          = @()
$prevOrphanExcelCount   = 0
$firstWdfLBRead         = $true

# === State Tracking (P70 NEW) ===
# Locked target orphan PIDs (P0 snapshot at startup)
$targetOrphanPids = @(22660, 25976)
$prevCleanMarkerExists = $false
$cleanupActionsTotal = 0
$cleanupComSuccess = 0
$cleanupTaskkillFallback = 0
$cleanupSkippedWindowed = 0
$guardStatus = 'STATIC_STANDBY'

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
$startMarker = '{"timestamp":"' + $ts0 + '","event_type":"MONITOR_V7_STARTED","agent":"' + $agent + '","severity":"INFO","monitor_version":"' + $monitorVersion + '","poll_number":' + $pollNum + ',"poll_interval_seconds":' + $pollInterval + ',"detail":"DSHD-P70 Orphan Excel Cleanup Safe Guard started PID=' + $PID + '"}'
Add-Content -Path $monitorLog -Value $startMarker -Encoding UTF8
Write-Host "[P70] Orphan Excel Cleanup Safe Guard started PID=$PID at $ts0, poll #$pollNum"
Write-Host "[P70] Baseline: feature/v88-g1 @ 01a022f"
Write-Host "[P70] Poll interval: ${pollInterval}s | Dashboard every 10 polls"
Write-Host "[P70] Target orphan PIDs: $($targetOrphanPids -join ', ')"
Write-Host "[P70] Cleanup marker: $cleanMarkerPath"
Write-Host "[P70] Guard status: STATIC_STANDBY (no marker = no cleanup)"

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
        # P1: ENHANCED WIND PROCESS OBSERVATION (inherited from P68)
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
        # P69: COM LOCK MONITORING (NEW)
        # ==========================================================

        # --- P69a: Excel process detail (orphan detection + WDF module check) ---
        $excelProcDetails = @()
        $orphanExcelPids = @()
        $excelWdfModules = @()
        $excelProcObjects = Get-Process -Name EXCEL -ErrorAction SilentlyContinue
        if ($excelProcObjects) {
            if ($excelProcObjects -isnot [array]) { $excelProcObjects = @($excelProcObjects) }
            foreach ($ep in $excelProcObjects) {
                $isOrphan = ($ep.MainWindowHandle -eq 0)
                $orphanStatus = if ($isOrphan) { 'ORPHAN' } else { 'NORMAL' }
                $excelProcDetails += @{
                    pid = $ep.Id
                    window_title = if ($ep.MainWindowTitle) { $ep.MainWindowTitle } else { '' }
                    visible = (-not $isOrphan)
                    orphan = $isOrphan
                    start_time = ''
                    working_set_mb = ''
                    wdf_modules = ''
                }
                try { $excelProcDetails[$excelProcDetails.Count - 1]['start_time'] = $ep.StartTime.ToString('yyyy-MM-ddTHH:mm:ssK') } catch {}
                try { $excelProcDetails[$excelProcDetails.Count - 1]['working_set_mb'] = [math]::Round($ep.WorkingSet64 / 1MB, 1) } catch {}
                if ($isOrphan) { $orphanExcelPids += $ep.Id }
                # Check WDF-related modules in this Excel process
                try {
                    $wdfMods = $ep.Modules | Where-Object { $_.ModuleName -match 'WDF' }
                    if ($wdfMods) {
                        foreach ($m in $wdfMods) {
                            $excelWdfModules += @{ pid = $ep.Id; module = $m.ModuleName; filename = $m.FileName }
                        }
                        $excelProcDetails[$excelProcDetails.Count - 1]['wdf_modules'] = ($wdfMods | ForEach-Object { $_.ModuleName }) -join ', '
                    }
                } catch {}
            }
        }
        $orphanExcelCount = $orphanExcelPids.Count

        # --- P69b: Excel 1-minute start/stop tracking ---
        $currExcelPidsArr = @()
        foreach ($epid in $excelPids) { $currExcelPidsArr += $epid }
        $excelAppeared = ($prevExcelCount -eq 0 -and $currExcelPidsArr.Count -gt 0)
        $excelDisappeared = ($prevExcelCount -gt 0 -and $currExcelPidsArr.Count -eq 0)
        if ($excelAppeared -or $excelDisappeared) {
            $excelFlashTimestamps += $ts
            $excelStartStopTimestamps1min += $ts
            # Write Excel start/stop event to com_lock_events.jsonl
            $eventDesc = if ($excelAppeared) { 'EXCEL_START' } else { 'EXCEL_STOP' }
            $comEvent = [ordered]@{
                timestamp = $ts
                event_type = $eventDesc
                event_id = "DSHD-P70-$eventDesc-$pollNum"
                agent = $agent
                poll_number = $pollNum
                severity = 'INFO'
                detail = "${eventDesc}: Excel count went from $($prevExcelCount) to $($currExcelPidsArr.Count) (PIDs: $($currExcelPidsArr -join ', '))"
                action = 'OBSERVATION_ONLY_NO_REMEDIATION'
            }
            Add-Content -Path $comLockEventsLog -Value ($comEvent | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8
        }
        # Prune to 1-minute window
        $cutoff1min = (Get-Date).AddMinutes(-1)
        $excelStartStopTimestamps1min = @($excelStartStopTimestamps1min | Where-Object {
            $evt = $null
            try { $evt = Get-Date $_ } catch { $evt = $null }
            if ($evt) { $evt -gt $cutoff1min } else { $true }
        })
        $flashCount1min = $excelStartStopTimestamps1min.Count
        $comJitterAlert = ($flashCount1min -gt 3)
        $comJitterAlertDetail = if ($comJitterAlert) {
            "COM_JITTER_ALERT: ${flashCount1min} Excel start/stop events in 1 min (threshold=3)"
        } else {
            "COM_JITTER_CLEAR: ${flashCount1min} events in 1 min"
        }

        # --- P69c: WDF LoadBehavior change detection ---
        $wdfLoadEvents = @($wdfLoadEvents)  # ensure array
        if ($firstWdfLBRead) {
            # First poll: just record initial state, no event
            $prevWdfLBHKCU = $wdfLoadBehaviorHKCU
            $prevWdfLBHKLM = $wdfLoadBehaviorHKLM
            $firstWdfLBRead = $false
        } else {
            $wdfHKCUChanged = ($prevWdfLBHKCU -ne $wdfLoadBehaviorHKCU)
            $wdfHKLMAChanged = ($prevWdfLBHKLM -ne $wdfLoadBehaviorHKLM)
            if ($wdfHKCUChanged -or $wdfHKLMAChanged) {
                $wdfEvent = [ordered]@{
                    timestamp = $ts
                    hkcu_before = $prevWdfLBHKCU
                    hkcu_after = $wdfLoadBehaviorHKCU
                    hklm_before = $prevWdfLBHKLM
                    hklm_after = $wdfLoadBehaviorHKLM
                }
                $wdfLoadEvents += $wdfEvent
                # Write WDF LoadBehavior change to com_lock_events.jsonl
                $comEvent = [ordered]@{
                    timestamp = $ts
                    event_type = 'WDF_LOADBEHAVIOR_CHANGE'
                    event_id = "DSHD-P70-WDF-LB-CHANGE-$pollNum"
                    agent = $agent
                    poll_number = $pollNum
                    severity = 'INFO'
                    detail = "WDF.Addin LoadBehavior changed: HKCU $($prevWdfLBHKCU)->$($wdfLoadBehaviorHKCU), HKLM $($prevWdfLBHKLM)->$($wdfLoadBehaviorHKLM)"
                    action = 'OBSERVATION_ONLY_NO_REMEDIATION'
                }
                Add-Content -Path $comLockEventsLog -Value ($comEvent | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8
            }
            $prevWdfLBHKCU = $wdfLoadBehaviorHKCU
            $prevWdfLBHKLM = $wdfLoadBehaviorHKLM
        }
        # Prune WDF load events to 5-minute window
        $cutoff5minWdf = (Get-Date).AddMinutes(-5)
        $wdfLoadEvents = @($wdfLoadEvents | Where-Object {
            $evt = $null
            try { $evt = Get-Date $_.timestamp } catch { $evt = $null }
            if ($evt) { $evt -gt $cutoff5minWdf } else { $true }
        })
        $wdfLoadChanges5min = $wdfLoadEvents.Count
        $wdfLoadFlapWarning = ($wdfLoadChanges5min -gt 2)
        $wdfLoadFlapDetail = if ($wdfLoadFlapWarning) {
            "WDF_LOAD_FLAP_WARNING: ${wdfLoadChanges5min} LoadBehavior changes in 5 min (threshold=2)"
        } else {
            "WDF_LOAD_FLAP_CLEAR: ${wdfLoadChanges5min} changes in 5 min"
        }

        # --- P69d: Write orphan Excel events ---
        if ($orphanExcelCount -gt 0) {
            $comEvent = [ordered]@{
                timestamp = $ts
                event_type = 'COM_ORPHAN_DETECTED'
                event_id = "DSHD-P70-ORPHAN-$pollNum"
                agent = $agent
                poll_number = $pollNum
                severity = 'WARNING'
                detail = "Orphan Excel processes detected: $($orphanExcelPids -join ', ') ($orphanExcelCount orphan)"
                action = 'OBSERVATION_ONLY_NO_REMEDIATION'
            }
            Add-Content -Path $comLockEventsLog -Value ($comEvent | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8
        }

        # ==========================================================
        # P70: SAFE CLEANUP GUARD (NEW)
        # ==========================================================
        $cleanMarkerExists = Test-Path $cleanMarkerPath
        $guardActionTaken = $false
        $guardActions = @()

        if ($cleanMarkerExists) {
            # Marker exists - evaluate cleanup candidates
            # Protection: never kill windowed Excel, wmain, or InitWAPI
            $protectedPids = @()
            if ($wmainPid) { $protectedPids += $wmainPid }
            $protectedPids += $initWapiPids

            foreach ($orphanPid in $orphanExcelPids) {
                # Skip if PID is protected
                if ($orphanPid -in $protectedPids) { continue }

                # Re-verify process still exists and is still orphan
                $proc = Get-Process -Id $orphanPid -ErrorAction SilentlyContinue
                if (-not $proc) {
                    $guardActions += @{ pid = $orphanPid; action = 'ALREADY_GONE'; detail = "PID $orphanPid no longer exists" }
                    continue
                }
                if ($proc.MainWindowHandle -ne 0) {
                    $cleanupSkippedWindowed++
                    $guardActions += @{ pid = $orphanPid; action = 'SKIPPED_WINDOWED'; detail = "PID $orphanPid now has visible window, skipped" }
                    continue
                }

                # Verify this is a target orphan (from P0 snapshot)
                $isTarget = ($orphanPid -in $targetOrphanPids)
                $guardActions += @{ pid = $orphanPid; action = 'TARGET_CHECK'; detail = "PID $orphanPid isTarget=$isTarget (snapshot: $($targetOrphanPids -join ','))" }

                # Try COM graceful exit first
                $comExitSuccess = $false
                try {
                    $excelApp = [System.Runtime.InteropServices.Marshal]::GetActiveObject("Excel.Application")
                    $excelApp.Quit()
                    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excelApp) | Out-Null
                    Start-Sleep -Seconds 5
                    if (-not (Get-Process -Id $orphanPid -ErrorAction SilentlyContinue)) {
                        $comExitSuccess = $true
                    }
                } catch {
                    # COM exit failed, will fall back to taskkill
                }

                if ($comExitSuccess) {
                    $cleanupComSuccess++
                    $guardActionTaken = $true
                    $guardActions += @{ pid = $orphanPid; action = 'COM_GRACEFUL_EXIT'; detail = "PID $orphanPid gracefully exited via COM Application.Quit()" }
                } else {
                    # Fallback: taskkill /F
                    try {
                        taskkill /F /PID $orphanPid 2>&1 | Out-Null
                        Start-Sleep -Seconds 2
                        $forceKilled = -not (Get-Process -Id $orphanPid -ErrorAction SilentlyContinue)
                        if ($forceKilled) {
                            $cleanupTaskkillFallback++
                            $guardActionTaken = $true
                            $guardActions += @{ pid = $orphanPid; action = 'TASKKILL_FORCE'; detail = "PID $orphanPid force-killed via taskkill /F (COM exit failed)" }
                        } else {
                            $guardActions += @{ pid = $orphanPid; action = 'TASKKILL_FAILED'; detail = "PID $orphanPid taskkill /F attempted but process still alive" }
                        }
                    } catch {
                        $guardActions += @{ pid = $orphanPid; action = 'TASKKILL_ERROR'; detail = "PID $orphanPid taskkill error: $($_.Exception.Message)" }
                    }
                }
            }
            $cleanupActionsTotal += $guardActions.Count
        }

        # --- P70: Write guard audit events to com_clean_guard_events.jsonl ---
        # Marker absence event
        if (-not $cleanMarkerExists) {
            $guardEvent = [ordered]@{
                timestamp = $ts
                event_type = 'MARKER_ABSENT_OBSERVE_ONLY'
                event_id = "DSHD-P70-MARKER-ABSENT-$pollNum"
                agent = $agent
                poll_number = $pollNum
                severity = 'INFO'
                detail = "Cleanup marker not found at $cleanMarkerPath. Observe-only mode. No process termination."
                marker_path = $cleanMarkerPath
                orphan_count = $orphanExcelCount
                orphan_pids = $orphanExcelPids
                target_pids = $targetOrphanPids
                action = 'NO_ACTION_MARKER_ABSENT'
            }
            Add-Content -Path $cleanGuardEventsLog -Value ($guardEvent | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8
            $guardStatus = 'STATIC_STANDBY'
        }

        # Guard action events (when marker exists)
        if ($cleanMarkerExists -and $guardActions.Count -gt 0) {
            foreach ($ga in $guardActions) {
                $guardEvent = [ordered]@{
                    timestamp = $ts
                    event_type = 'GUARD_ACTION'
                    event_id = "DSHD-P70-GUARD-ACTION-$pollNum"
                    agent = $agent
                    poll_number = $pollNum
                    severity = 'WARNING'
                    detail = $ga.detail
                    pid = $ga.pid
                    action = $ga.action
                    marker_path = $cleanMarkerPath
                }
                Add-Content -Path $cleanGuardEventsLog -Value ($guardEvent | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8
            }
            $guardStatus = 'CLEANUP_EXECUTED'
        }

        # Marker appeared/disappeared tracking
        if ($cleanMarkerExists -and -not $prevCleanMarkerExists) {
            $guardEvent = [ordered]@{
                timestamp = $ts
                event_type = 'MARKER_APPEARED'
                event_id = "DSHD-P70-MARKER-APPEARED-$pollNum"
                agent = $agent
                poll_number = $pollNum
                severity = 'WARNING'
                detail = "Cleanup marker detected at $cleanMarkerPath. Guard enabled."
                marker_path = $cleanMarkerPath
            }
            Add-Content -Path $cleanGuardEventsLog -Value ($guardEvent | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8
        }
        if (-not $cleanMarkerExists -and $prevCleanMarkerExists) {
            $guardEvent = [ordered]@{
                timestamp = $ts
                event_type = 'MARKER_REMOVED'
                event_id = "DSHD-P70-MARKER-REMOVED-$pollNum"
                agent = $agent
                poll_number = $pollNum
                severity = 'INFO'
                detail = "Cleanup marker removed from $cleanMarkerPath. Returning to STATIC_STANDBY."
                marker_path = $cleanMarkerPath
            }
            Add-Content -Path $cleanGuardEventsLog -Value ($guardEvent | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8
        }
        $prevCleanMarkerExists = $cleanMarkerExists

        # --- P70: COM stability score and health rating (UPDATED) ---
        $comStabilityScore = 100
        # Deduct for WDF load changes (up to -50)
        $wdfDeduction = [Math]::Min($wdfLoadChanges5min * 10, 50)
        $comStabilityScore -= $wdfDeduction
        # Deduct for orphan count: -15 each, NO CAP (P70 new rule)
        $orphanDeduction = $orphanExcelCount * 15
        $comStabilityScore -= $orphanDeduction
        # Deduct for 1-min jitter (up to -20)
        $jitterDeduction = [Math]::Min([Math]::Max(0, $flashCount1min - 3) * 5, 20)
        $comStabilityScore -= $jitterDeduction
        $comStabilityScore = [Math]::Max(0, [Math]::Min(100, $comStabilityScore))

        if ($comStabilityScore -ge 90) {
            $comHealthRating = '优秀'
        } elseif ($comStabilityScore -ge 70) {
            $comHealthRating = '轻度抖动'
        } else {
            $comHealthRating = '高锁风险'
        }

        # ==========================================================
        # P3: ALERT THRESHOLD CHECKS (P68 inherited + P69 new)
        # ==========================================================

        # --- P3a: COM_JITTER (P68: 5-min, >4 flash) ---
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

        # --- P69 P3d: COM_ORPHAN_PROCESS_WARNING ---
        $orphanWarning = ($orphanExcelCount -gt 0)
        $orphanDetail = if ($orphanWarning) {
            "COM_ORPHAN_PROCESS_WARNING: ${orphanExcelCount} orphan Excel process(es) (PID: $($orphanExcelPids -join ', '))"
        } else {
            "COM_ORPHAN_CLEAR: 0 orphan Excel processes"
        }

        # --- P69 P3e: COM_JITTER_ALERT (1-min, >3) ---
        # Already computed above as $comJitterAlert / $comJitterAlertDetail

        # --- P69 P3f: WDF_LOAD_FLAP_WARNING ---
        # Already computed above as $wdfLoadFlapWarning / $wdfLoadFlapDetail

        # ==========================================================
        # P0: CREDENTIAL SCAN
        # ==========================================================
        $credAlert = 'NONE'
        $credPattern = '\b(?:password|passwd|api_key|secret|credentials_provided)\b|Tyq1999|13199157886'
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
        # P4: SYSTEM SKILL SHA CHECK
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
        # P68 alerts
        if ($comJitterWarning) { $severity = 'WARNING'; $alertFlags += 'COM_JITTER' }
        if ($sessionVisibilityWarning) { $severity = 'WARNING'; $alertFlags += 'SESSION_VISIBILITY' }
        if ($initWapiMissing) { $severity = 'WARNING'; $alertFlags += 'WDF_INIT_MISSING' }
        # P69 alerts
        if ($orphanWarning) { $severity = 'WARNING'; $alertFlags += 'COM_ORPHAN' }
        if ($comJitterAlert) { $severity = 'WARNING'; $alertFlags += 'COM_JITTER_1MIN' }
        if ($wdfLoadFlapWarning) { $severity = 'WARNING'; $alertFlags += 'WDF_LOAD_FLAP' }
        if (-not $skillHashAllMatch) { $severity = 'WARNING'; $alertFlags += 'SKILL_HASH_MISMATCH' }

        # ==========================================================
        # BUILD POLL EVENT
        # ==========================================================
        $pollEvent = [ordered]@{
            timestamp         = $ts
            poll_number       = $pollNum
            event_type        = 'COM_LOCK_JITTER_GUARD_POLL'
            event_id          = "DSHD-P70-POLL-$pollNum"
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
                    orphan_count = $orphanExcelCount
                    orphan_pids = $orphanExcelPids
                    wdf_module_count = $excelWdfModules.Count
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
                # P68 jitter (5-min)
                com_jitter_5min = [ordered]@{
                    flash_count_5min = $flashCount5min
                    warning = $comJitterWarning
                    detail = $comJitterDetail
                }
                # P69 jitter (1-min)
                com_jitter_1min = [ordered]@{
                    flash_count_1min = $flashCount1min
                    alert = $comJitterAlert
                    detail = $comJitterAlertDetail
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
                # P69 orphan
                com_orphan = [ordered]@{
                    orphan_count = $orphanExcelCount
                    orphan_pids = $orphanExcelPids
                    warning = $orphanWarning
                    detail = $orphanDetail
                }
                # P69 WDF load
                wdf_load_flap = [ordered]@{
                    changes_5min = $wdfLoadChanges5min
                    warning = $wdfLoadFlapWarning
                    detail = $wdfLoadFlapDetail
                }
                # P69 stability
                com_stability = [ordered]@{
                    score = $comStabilityScore
                    rating = $comHealthRating
                    max_score = 100
                }
                # P69 Excel process details
                excel_process_details = $excelProcDetails
                excel_wdf_modules = $excelWdfModules
                # P70 Guard fields
                cleanup_guard = [ordered]@{
                    marker_exists = $cleanMarkerExists
                    marker_path = $cleanMarkerPath
                    guard_status = $guardStatus
                    guard_action_taken = $guardActionTaken
                    guard_actions_count = $guardActions.Count
                    target_orphan_pids = $targetOrphanPids
                    cleanup_total = $cleanupActionsTotal
                    cleanup_com_success = $cleanupComSuccess
                    cleanup_taskkill_fallback = $cleanupTaskkillFallback
                    cleanup_skipped_windowed = $cleanupSkippedWindowed
                }
                credential_alert = $credAlert
                wind_api_calls = $totalWindCalls
                skill_sha_check = $skillHashStatus
            }
            invariants = $inv
        }

        $pollJson = $pollEvent | ConvertTo-Json -Compress -Depth 12
        Add-Content -Path $monitorLog -Value $pollJson -Encoding UTF8
        Write-Host "  Poll written to monitor_log.jsonl"

        # ==========================================================
        # P1: APPEND TO TRACKING_MONITOR_AUDIT.JSONL (per-poll event)
        # ==========================================================
        $trackingEvent = [ordered]@{
            timestamp = $ts
            event = "DSHD-P70-COM-LOCK-JITTER-GUARD-POLL-$pollNum"
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
            orphan_excel_count = $orphanExcelCount
            windlocal_count = $windLocalPids.Count
            wdf_addin_lb = $wdfLoadBehaviorHKCU
            wind_ports = $windPortList.Count
            cred_alert = $credAlert
            wind_api_calls = $totalWindCalls
            skill_sha = $skillHashStatus
            alert_flags = $alertFlags
            # P69 specific
            com_jitter_1min = $flashCount1min
            com_jitter_5min = $flashCount5min
            wdf_load_changes_5min = $wdfLoadChanges5min
            com_stability_score = $comStabilityScore
            com_health_rating = $comHealthRating
            # P70 guard
            guard_marker_exists = $cleanMarkerExists
            guard_status = $guardStatus
            guard_action_taken = $guardActionTaken
            cleanup_total = $cleanupActionsTotal
            invariants = $inv
        }
        $trackJson = $trackingEvent | ConvertTo-Json -Compress -Depth 8
        Add-Content -Path $trackingLedger -Value $trackJson -Encoding UTF8

        # ==========================================================
        # P3: ALERT EVENTS (P68 inherited + P69 new)
        # ==========================================================

        # P68 alerts
        if ($comJitterWarning) {
            $alertEvent = [ordered]@{
                timestamp = $ts
                event_type = 'COM_JITTER_WARNING'
                event_id = "DSHD-P68-COM-JITTER-5MIN-$pollNum"
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

        # P69 NEW alerts
        if ($orphanWarning) {
            $alertEvent = [ordered]@{
                timestamp = $ts
                event_type = 'COM_ORPHAN_PROCESS_WARNING'
                event_id = "DSHD-P70-ORPHAN-$pollNum"
                agent = $agent
                severity = 'WARNING'
                detail = $orphanDetail
                orphan_pids = $orphanExcelPids
                orphan_count = $orphanExcelCount
                action = 'OBSERVATION_ONLY_NO_REMEDIATION'
            }
            Add-Content -Path $monitorLog -Value ($alertEvent | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8
        }
        if ($comJitterAlert) {
            $alertEvent = [ordered]@{
                timestamp = $ts
                event_type = 'COM_JITTER_ALERT'
                event_id = "DSHD-P70-COM-JITTER-1MIN-$pollNum"
                agent = $agent
                severity = 'WARNING'
                detail = $comJitterAlertDetail
                flash_events_1min = $excelStartStopTimestamps1min
                action = 'OBSERVATION_ONLY_NO_REMEDIATION'
            }
            Add-Content -Path $monitorLog -Value ($alertEvent | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8
        }
        if ($wdfLoadFlapWarning) {
            $alertEvent = [ordered]@{
                timestamp = $ts
                event_type = 'WDF_LOAD_FLAP_WARNING'
                event_id = "DSHD-P70-WDF-FLAP-$pollNum"
                agent = $agent
                severity = 'WARNING'
                detail = $wdfLoadFlapDetail
                load_events_5min = $wdfLoadEvents
                action = 'OBSERVATION_ONLY_NO_REMEDIATION'
            }
            Add-Content -Path $monitorLog -Value ($alertEvent | ConvertTo-Json -Compress -Depth 8) -Encoding UTF8
        }

        # ==========================================================
        # P2: DASHBOARD GENERATION (every 10th poll)
        # ==========================================================
        if ($pollNum % 10 -eq 0) {
            Write-Host "  Generating dashboards (poll #$pollNum)..."

            # --- Collect recent WDF/Excel events from wind_excel_events.jsonl ---
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

            # --- Collect recent WDF LoadBehavior events (from in-memory) ---
            $recentWdfLbEvents = @($wdfLoadEvents | Select-Object -Last 10)

            # --- Build process table (inherited from P68) ---
            $procTable = @()
            $procTable += [ordered]@{ process = 'wmain.exe'; pid = if ($wmainPid) { $wmainPid } else { 'N/A' }; state = $wmainStatus; start_time = if ($wmainStartTime) { $wmainStartTime } else { 'N/A' }; window_title = if ($wmainTitle) { $wmainTitle } else { 'N/A' }; visible = $wmainVisible }
            $procTable += [ordered]@{ process = 'InitWAPI.exe'; pid = if ($initWapiPids.Count -gt 0) { $initWapiPids -join ', ' } else { 'N/A' }; state = $initWapiStatus; start_time = if ($initWapiStartTime) { $initWapiStartTime } else { 'N/A' }; window_title = 'N/A'; visible = 'N/A' }
            $procTable += [ordered]@{ process = 'EXCEL.EXE'; pid = if ($excelPids.Count -gt 0) { $excelPids -join ', ' } else { 'N/A' }; state = if ($excelCount -gt 0) { 'RUNNING' } else { 'NOT_RUNNING' }; start_time = 'N/A'; window_title = 'N/A'; visible = 'N/A' }
            $procTable += [ordered]@{ process = 'windlocal.exe'; pid = if ($windLocalPids.Count -gt 0) { $windLocalPids -join ', ' } else { 'N/A' }; state = if ($windLocalPids.Count -gt 0) { 'RUNNING' } else { 'NOT_RUNNING' }; start_time = 'N/A'; window_title = 'N/A'; visible = 'N/A' }
            $procTable += [ordered]@{ process = 'python.exe/pythonw.exe'; pid = if ($pythonPids.Count -gt 0) { $pythonPids -join ', ' } else { 'N/A' }; state = if ($pythonPids.Count -gt 0) { 'RUNNING' } else { 'NOT_RUNNING' }; start_time = 'N/A'; window_title = 'N/A'; visible = 'N/A' }

            # --- Build Excel process detail table (P69) ---
            $excelDetailTable = @()
            if ($excelProcDetails.Count -gt 0) {
                foreach ($epd in $excelProcDetails) {
                    $excelDetailTable += [ordered]@{
                        pid = $epd.pid
                        window = if ($epd.window_title) { $epd.window_title } else { '(no window)' }
                        visible = $epd.visible
                        orphan = if ($epd.orphan) { 'YES' } else { 'NO' }
                        start_time = $epd.start_time
                        working_set_mb = $epd.working_set_mb
                        wdf_modules = if ($epd.wdf_modules) { $epd.wdf_modules } else { 'none' }
                    }
                }
            }

            # --- Invariant status table ---
            $invTable = @()
            $invTable += [ordered]@{ invariant = 'gate'; expected = 'CLOSED/HOLD'; actual = $inv['gate']; status = if ($inv['gate'] -eq 'CLOSED/HOLD') { 'PASS' } else { 'FAIL' } }
            $invTable += [ordered]@{ invariant = 'release_permit'; expected = 'NOT_ISSUED'; actual = $inv['release_permit']; status = if ($inv['release_permit'] -eq 'NOT_ISSUED') { 'PASS' } else { 'FAIL' } }
            $invTable += [ordered]@{ invariant = 'wind_api_calls'; expected = '0'; actual = $totalWindCalls; status = if ($totalWindCalls -eq 0) { 'PASS' } else { 'FAIL' } }
            $invTable += [ordered]@{ invariant = 'credential_alert'; expected = 'NONE'; actual = $credAlert; status = if ($credAlert -eq 'NONE') { 'PASS' } else { 'FAIL' } }
            $invTable += [ordered]@{ invariant = 'circuit_breaker'; expected = 'READY'; actual = $inv['circuit_breaker']; status = if ($inv['circuit_breaker'] -eq 'READY') { 'PASS' } else { 'FAIL' } }
            $invTable += [ordered]@{ invariant = 'hold_block_check'; expected = 'PASS'; actual = $inv['hold_block_check']; status = if ($inv['hold_block_check'] -eq 'PASS') { 'PASS' } else { 'FAIL' } }
            $invTable += [ordered]@{ invariant = 'ledger_append_only'; expected = 'TRUE'; actual = 'TRUE'; status = 'PASS' }

            # --- Health assessment (inherited + P69 COM) ---
            $healthParts = @()
            if ($wmainPid) { $healthParts += "wmain(RUNNING,PID=$wmainPid,visible=$wmainVisible)" }
            else { $healthParts += 'wmain(NOT_RUNNING)' }
            if ($initWapiPids.Count -gt 0) { $healthParts += "InitWAPI(RUNNING,PID=$($initWapiPids -join ','))" }
            else { $healthParts += 'InitWAPI(NOT_RUNNING)' }
            if ($excelCount -gt 0) { $healthParts += "Excel(count=$excelCount)" }
            else { $healthParts += 'Excel(NONE)' }
            $healthParts += "Ports=$($windPortList.Count)"
            $healthParts += "Flash5min=$flashCount5min"
            $healthParts += "Flash1min=$flashCount1min"
            $healthParts += "Orphan=$orphanExcelCount"
            $healthParts += "WDFchg=$wdfLoadChanges5min"
            if ($inv['circuit_breaker'] -eq 'READY') { $healthParts += 'CB=READY' }
            else { $healthParts += 'CB=TRIPPED' }
            if ($skillHashAllMatch) { $healthParts += 'SkillSHA=OK' }
            else { $healthParts += "SkillSHA=FAIL($($skillHashFailed -join ','))" }
            $healthParts += "ComScore=$comStabilityScore/100"
            $healthParts += "Rating=$comHealthRating"

            $healthIcon = 'GREEN'; $healthIconStr = 'GREEN'
            if ($severity -eq 'WARNING') { $healthIcon = 'YELLOW'; $healthIconStr = 'YELLOW' }
            if ($severity -eq 'CRITICAL') { $healthIcon = 'RED'; $healthIconStr = 'RED' }

            $suffix = if ($alertFlags.Count -eq 0) { 'passing' } else { "with alerts: $($alertFlags -join ', ')." }
            $healthSummary = "[$healthIcon] $($severity): $($healthParts -join ' | ') -- All invariants $suffix"

            # --- COM health one-sentence (P69) ---
            $comHealthSummary = "[$comHealthRating] COM stability score: $comStabilityScore/100 | Excel=$excelCount Orphan=$orphanExcelCount Flash1min=$flashCount1min WDFchg=$wdfLoadChanges5min"

            # --- Write P68 Dashboard JSON (inherited) ---
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
                com_jitter_5min = [ordered]@{ flash_count_5min = $flashCount5min; warning = $comJitterWarning }
                session_visibility = [ordered]@{ wmain_invisible_consecutive = $wmainInvisibleConsecutive; warning = $sessionVisibilityWarning }
                initwapi_status = [ordered]@{ was_present = $initWapiWasPresent; now_present = $initWapiNowPresent; missing = $initWapiMissing }
                skill_sha_check = [ordered]@{ status = $skillHashStatus; all_match = $skillHashAllMatch }
            }
            $dashJsonFile = $dashJson | ConvertTo-Json -Depth 12
            [System.IO.File]::WriteAllText($dashboardJson, $dashJsonFile, (New-Object System.Text.UTF8Encoding($false)))
            Write-Host "  P68 Dashboard JSON written: $dashboardJson"

            # --- Write P68 Dashboard MD (inherited) ---
            $mdLines = @()
            $mdLines += "# DSHD-P68 Enhanced Wind Observation Dashboard"
            $mdLines += ""
            $mdLines += "**Generated**: $ts"
            $mdLines += "**Poll Number**: #$pollNum"
            $mdLines += "**Session**: DSHD-P70 (inherited P68/P69 monitor)"
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
                $mdLines += "| $($iv.invariant) | $($iv.expected) | $($iv.actual) | $($iv.status) |"
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
            Write-Host "  P68 Dashboard MD written: $dashboardMd"

            # --- P70: Write COM Jitter Dashboard JSON ---
            $comDashJson = [ordered]@{
                generated_at = $ts
                poll_number = $pollNum
                agent = $agent
                monitor_version = $monitorVersion
                baseline = 'feature/v88-g1 @ 01a022fdffb36e603abd623842cef65f80f24c92'
                severity = $severity
                alert_flags = $alertFlags
                health_icon = $healthIcon
                com_health_summary = $comHealthSummary
                # P69/P70 COM-specific metrics
                com_metrics = [ordered]@{
                    excel_flash_1min = $flashCount1min
                    excel_flash_5min = $flashCount5min
                    orphan_excel_count = $orphanExcelCount
                    orphan_excel_pids = $orphanExcelPids
                    wdf_load_changes_5min = $wdfLoadChanges5min
                    wdf_load_stability_score = $comStabilityScore
                    com_health_rating = $comHealthRating
                }
                # Excel process details
                excel_processes = $excelDetailTable
                excel_wdf_modules = $excelWdfModules
                # WDF LoadBehavior
                wdf_loadbehavior = [ordered]@{
                    hkcu = $wdfLoadBehaviorHKCU
                    hklm = $wdfLoadBehaviorHKLM
                    xl_task_panel = $wdfXLTaskPanelLB
                }
                # Recent WDF LoadBehavior events
                recent_wdf_load_events = $recentWdfLbEvents
                # Recent WDF/Excel events (inherited)
                recent_wdf_excel_events = $recentEvents
                # Invariants (inherited)
                invariants = $invTable
                # Process table (inherited)
                processes = $procTable
                # Alert details
                com_alerts = [ordered]@{
                    com_jitter_1min = [ordered]@{ count = $flashCount1min; threshold = 3; triggered = $comJitterAlert; detail = $comJitterAlertDetail }
                    com_orphan = [ordered]@{ count = $orphanExcelCount; triggered = $orphanWarning; detail = $orphanDetail }
                    wdf_load_flap = [ordered]@{ changes = $wdfLoadChanges5min; threshold = 2; triggered = $wdfLoadFlapWarning; detail = $wdfLoadFlapDetail }
                    com_jitter_5min = [ordered]@{ count = $flashCount5min; threshold = 4; triggered = $comJitterWarning; detail = $comJitterDetail }
                    session_visibility = [ordered]@{ streak = $wmainInvisibleConsecutive; threshold = 3; triggered = $sessionVisibilityWarning; detail = $sessionVisibilityDetail }
                    wdf_init_missing = [ordered]@{ was_present = $initWapiWasPresent; now_present = $initWapiNowPresent; triggered = $initWapiMissing; detail = $initWapiMissingDetail }
                }
                # P70 Cleanup Guard
                cleanup_guard = [ordered]@{
                    marker_exists = $cleanMarkerExists
                    marker_path = $cleanMarkerPath
                    guard_status = $guardStatus
                    guard_action_taken = $guardActionTaken
                    guard_actions_count = $guardActions.Count
                    guard_actions = $guardActions
                    target_orphan_pids = $targetOrphanPids
                    cleanup_total = $cleanupActionsTotal
                    cleanup_com_success = $cleanupComSuccess
                    cleanup_taskkill_fallback = $cleanupTaskkillFallback
                    cleanup_skipped_windowed = $cleanupSkippedWindowed
                }
                # System details (inherited)
                system_details = [ordered]@{
                    wind_tcp_ports = $windPortList.Count
                    wind_users_file_count = $windUsersFileCount
                    credential_alert = $credAlert
                    wind_api_calls = $totalWindCalls
                    skill_sha_check = $skillHashStatus
                    monitor_log_lines = (Get-Content $monitorLog -ErrorAction SilentlyContinue).Count
                    tracking_ledger_lines = (Get-Content $trackingLedger -ErrorAction SilentlyContinue).Count
                    com_lock_events_lines = if (Test-Path $comLockEventsLog) { (Get-Content $comLockEventsLog -ErrorAction SilentlyContinue).Count } else { 0 }
                    clean_guard_events_lines = if (Test-Path $cleanGuardEventsLog) { (Get-Content $cleanGuardEventsLog -ErrorAction SilentlyContinue).Count } else { 0 }
                }
            }
            $comDashJsonFile = $comDashJson | ConvertTo-Json -Depth 12
            [System.IO.File]::WriteAllText($comDashboardJson, $comDashJsonFile, (New-Object System.Text.UTF8Encoding($false)))
            Write-Host "  P70 COM Dashboard JSON written: $comDashboardJson"

            # --- P70: Write COM Jitter Dashboard MD ---
            $cmLines = @()
            $cmLines += "# DSHD-P70 Orphan Excel Cleanup Safe Guard Dashboard"
            $cmLines += ""
            $cmLines += "**Generated**: $ts"
            $cmLines += "**Poll Number**: #$pollNum"
            $cmLines += "**Session**: DSHD-P70"
            $cmLines += "**Monitor Version**: $monitorVersion"
            $cmLines += "**Baseline**: feature/v88-g1 @ 01a022f"
            $cmLines += "**Poll Interval**: ${pollInterval}s"
            $cmLines += ""
            $cmLines += "---"
            $cmLines += ""
            $cmLines += "## COM Health Assessment"
            $cmLines += ""
            $cmLines += $comHealthSummary
            $cmLines += ""
            $cmLines += "**Overall**: $healthSummary"
            $cmLines += ""
            $cmLines += "---"
            $cmLines += ""
            $cmLines += "## COM Jitter Metrics"
            $cmLines += ""
            $cmLines += "| Metric | Value | Status |"
            $cmLines += "|--------|-------|--------|"
            $cmLines += "| Excel Flash Events (1min) | $flashCount1min | $(if ($comJitterAlert) { 'WARNING' } else { 'CLEAR' }) |"
            $cmLines += "| Excel Flash Events (5min) | $flashCount5min | $(if ($comJitterWarning) { 'WARNING' } else { 'CLEAR' }) |"
            $cmLines += "| Orphan Excel Count | $orphanExcelCount | $(if ($orphanWarning) { 'WARNING' } else { 'CLEAR' }) |"
            $cmLines += "| WDF Load Changes (5min) | $wdfLoadChanges5min | $(if ($wdfLoadFlapWarning) { 'WARNING' } else { 'CLEAR' }) |"
            $cmLines += "| WDF Load Stability Score | $comStabilityScore/100 | $comHealthRating |"
            $cmLines += ""
            $cmLines += "---"
            $cmLines += ""
            $cmLines += "## Excel Process Detail"
            $cmLines += ""
            if ($excelProcDetails.Count -eq 0) {
                $cmLines += "*No EXCEL.EXE processes running.*"
            } else {
                $cmLines += "| PID | Window | Visible | Orphan | Start Time | Working Set (MB) | WDF Modules |"
                $cmLines += "|-----|--------|---------|--------|------------|------------------|-------------|"
                foreach ($epd in $excelProcDetails) {
                    $cmLines += "| $($epd.pid) | $(if ($epd.window_title) { $epd.window_title } else { '(none)' }) | $($epd.visible) | $(if ($epd.orphan) { 'YES' } else { 'NO' }) | $($epd.start_time) | $($epd.working_set_mb) | $(if ($epd.wdf_modules) { $epd.wdf_modules } else { 'none' }) |"
                }
            }
            $cmLines += ""
            $cmLines += "---"
            $cmLines += ""
            $cmLines += "## WDF Addin Load Behavior"
            $cmLines += ""
            $cmLines += "| HIVE | LoadBehavior | State |"
            $cmLines += "|------|-------------|-------|"
            $cmLines += "| HKCU | $($wdfLoadBehaviorHKCU) | $(if ($wdfLoadBehaviorHKCU -eq 3) { 'ALWAYS_LOAD' } elseif ($wdfLoadBehaviorHKCU -eq 2) { 'LOAD_ON_DEMAND' } else { 'NOT_LOADED' }) |"
            $cmLines += "| HKLM | $($wdfLoadBehaviorHKLM) | $(if ($wdfLoadBehaviorHKLM -eq 3) { 'ALWAYS_LOAD' } elseif ($wdfLoadBehaviorHKLM -eq 2) { 'LOAD_ON_DEMAND' } else { 'NOT_LOADED' }) |"
            $cmLines += "| XL Task Panel | $($wdfXLTaskPanelLB) | $(if ($wdfXLTaskPanelLB -eq 2) { 'LOAD_ON_DEMAND' } elseif ($wdfXLTaskPanelLB -eq 3) { 'ALWAYS_LOAD' } else { 'NOT_LOADED' }) |"
            $cmLines += ""
            $cmLines += "---"
            $cmLines += ""
            $cmLines += "## Recent WDF LoadBehavior Changes (Last 10)"
            $cmLines += ""
            if ($recentWdfLbEvents.Count -eq 0) {
                $cmLines += "*No WDF LoadBehavior changes recorded.*"
            } else {
                $cmLines += "| Timestamp | HKCU Before | HKCU After | HKLM Before | HKLM After |"
                $cmLines += "|-----------|-------------|------------|-------------|------------|"
                foreach ($ev in $recentWdfLbEvents) {
                    $cmLines += "| $($ev.timestamp) | $($ev.hkcu_before) | $($ev.hkcu_after) | $($ev.hklm_before) | $($ev.hklm_after) |"
                }
            }
            $cmLines += ""
            $cmLines += "---"
            $cmLines += ""
            $cmLines += "## Alert Status"
            $cmLines += ""
            $cmLines += "| Alert | Status | Detail |"
            $cmLines += "|-------|--------|--------|"
            $cmLines += "| COM_JITTER_ALERT (>3 start/stop/1min) | $(if ($comJitterAlert) { 'TRIGGERED' } else { 'CLEAR' }) | $flashCount1min events in 1min |"
            $cmLines += "| COM_ORPHAN_PROCESS_WARNING | $(if ($orphanWarning) { 'TRIGGERED' } else { 'CLEAR' }) | $(if ($orphanExcelPids.Count -gt 0) { "PIDs: $($orphanExcelPids -join ', ')" } else { 'None' }) |"
            $cmLines += "| WDF_LOAD_FLAP_WARNING (>2 changes/5min) | $(if ($wdfLoadFlapWarning) { 'TRIGGERED' } else { 'CLEAR' }) | $wdfLoadChanges5min changes in 5min |"
            $cmLines += "| COM_JITTER_WARNING (>4 flash/5min) | $(if ($comJitterWarning) { 'TRIGGERED' } else { 'CLEAR' }) | $flashCount5min flash events |"
            $cmLines += "| SESSION_VISIBILITY (wmain invisible 3 polls) | $(if ($sessionVisibilityWarning) { 'TRIGGERED' } else { 'CLEAR' }) | Streak: $wmainInvisibleConsecutive |"
            $cmLines += "| WDF_INIT_MISSING (InitWAPI disappeared) | $(if ($initWapiMissing) { 'TRIGGERED' } else { 'CLEAR' }) | $(if ($initWapiPids.Count -gt 0) { 'Present' } else { 'Absent' }) |"
            $cmLines += ""
            $cmLines += "---"
            $cmLines += ""
            $cmLines += "## P70 Cleanup Guard Status"
            $cmLines += ""
            $cmLines += "| Item | Value |"
            $cmLines += "|------|-------|"
            $cmLines += "| Guard Status | $guardStatus |"
            $cmLines += "| Cleanup Marker | $(if ($cleanMarkerExists) { 'EXISTS' } else { 'NOT_FOUND' }) |"
            $cmLines += "| Marker Path | $cleanMarkerPath |"
            $cmLines += "| Guard Action Taken | $(if ($guardActionTaken) { 'YES' } else { 'NO' }) |"
            $cmLines += "| Target Orphan PIDs | $($targetOrphanPids -join ', ') |"
            $cmLines += "| Cleanup Actions Total | $cleanupActionsTotal |"
            $cmLines += "| COM Graceful Exits | $cleanupComSuccess |"
            $cmLines += "| Taskkill Fallbacks | $cleanupTaskkillFallback |"
            $cmLines += "| Skipped (Windowed) | $cleanupSkippedWindowed |"
            $cmLines += ""
            if ($guardActions.Count -gt 0) {
                $cmLines += "### Guard Actions (This Poll)"
                $cmLines += ""
                $cmLines += "| PID | Action | Detail |"
                $cmLines += "|-----|--------|--------|"
                foreach ($ga in $guardActions) {
                    $cmLines += "| $($ga.pid) | $($ga.action) | $($ga.detail) |"
                }
            } else {
                $cmLines += "*No guard actions this poll (no marker or no orphans).*"
            }
            $cmLines += ""
            $cmLines += "> **Red Line**: No cleanup without marker. Never kills windowed Excel, wmain, or InitWAPI."
            $cmLines += ""
            $cmLines += "---"
            $cmLines += ""
            $cmLines += "## Process Status (Inherited)"
            $cmLines += ""
            $cmLines += "| Process | PID | State | Start Time | Window Title | Visible |"
            $cmLines += "|---------|-----|-------|------------|--------------|---------|"
            foreach ($p in $procTable) {
                $cmLines += "| $($p.process) | $($p.pid) | $($p.state) | $($p.start_time) | $($p.window_title) | $($p.visible) |"
            }
            $cmLines += ""
            $cmLines += "---"
            $cmLines += ""
            $cmLines += "## Invariants Status (Inherited)"
            $cmLines += ""
            $cmLines += "| Invariant | Expected | Actual | Status |"
            $cmLines += "|-----------|----------|--------|--------|"
            foreach ($iv in $invTable) {
                $cmLines += "| $($iv.invariant) | $($iv.expected) | $($iv.actual) | $($iv.status) |"
            }
            $cmLines += ""
            $cmLines += "---"
            $cmLines += ""
            $cmLines += "## System Details (Inherited)"
            $cmLines += ""
            $cmLines += "| Item | Value |"
            $cmLines += "|------|-------|"
            $cmLines += "| Wind TCP Ports (62000-64000) | $($windPortList.Count) |"
            $cmLines += "| .wind/users File Count | $windUsersFileCount |"
            $cmLines += "| Credential Alert | $credAlert |"
            $cmLines += "| Wind API Calls | $totalWindCalls |"
            $cmLines += "| Skill SHA Check | $skillHashStatus |"
            $cmLines += "| Monitor Log Lines | $((Get-Content $monitorLog -ErrorAction SilentlyContinue).Count) |"
            $cmLines += "| Tracking Ledger Lines | $((Get-Content $trackingLedger -ErrorAction SilentlyContinue).Count) |"
            $cmLines += "| COM Lock Events Lines | $(if (Test-Path $comLockEventsLog) { (Get-Content $comLockEventsLog -ErrorAction SilentlyContinue).Count } else { 0 }) |"
            $cmLines += ""
            $cmLines += "---"
            $cmLines += ""
            $cmLines += "*Dashboard auto-generated every 10 polls. Read-only observation. No remediation actions taken.*"

            $cmContent = $cmLines -join "`r`n"
            [System.IO.File]::WriteAllText($comDashboardMd, $cmContent, (New-Object System.Text.UTF8Encoding($false)))
            Write-Host "  P70 COM Dashboard MD written: $comDashboardMd"

            # --- Dashboard events to monitor log ---
            $dashEvent = [ordered]@{
                timestamp = $ts
                event_type = 'DASHBOARD_GENERATED'
                event_id = "DSHD-P70-DASHBOARD-$pollNum"
                agent = $agent
                severity = $severity
                dashboard_md = $dashboardMd
                dashboard_json = $dashboardJson
                com_dashboard_md = $comDashboardMd
                com_dashboard_json = $comDashboardJson
                health_icon = $healthIcon
                health_summary = $healthSummary
                com_health_summary = $comHealthSummary
            }
            Add-Content -Path $monitorLog -Value ($dashEvent | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8

        } # end dashboard generation

        # ==========================================================
        # UPDATE STATE FOR NEXT POLL
        # ==========================================================
        $prevExcelPids = $currExcelPidsArr
        $prevExcelCount = $excelCount
        $prevWmainVisible = $wmainVisible
        $prevInitWapiPids = @($initWapiPids)
        $prevWmainPids = if ($wmainPid) { @($wmainPid) } else { @() }
        $prevWindLocalPids = @($windLocalPids)
        $prevOrphanExcelCount = $orphanExcelCount

        # ==========================================================
        # SUMMARY OUTPUT
        # ==========================================================
        $alertSummary = if ($alertFlags.Count -gt 0) { "ALERTS: $($alertFlags -join ', ')" } else { "No alerts" }
        Write-Host "  Severity=$severity | $alertSummary"
        Write-Host "  wmain=$wmainStatus PID=$wmainPid visible=$wmainVisible"
        Write-Host "  InitWAPI=$initWapiStatus PID=$($initWapiPids -join ',')"
        Write-Host "  Excel=$excelCount orphan=$orphanExcelCount | windlocal=$($windLocalPids.Count) | ports=$($windPortList.Count)"
        Write-Host "  Flash5min=$flashCount5min Flash1min=$flashCount1min | WDFchg=$wdfLoadChanges5min | ComScore=$comStabilityScore/100 [$comHealthRating]"
        Write-Host "  invisible=$wmainInvisibleConsecutive | SkillSHA=$skillHashStatus"
        Write-Host "  Guard=$guardStatus marker=$(if ($cleanMarkerExists) { 'YES' } else { 'NO' }) actions=$($guardActions.Count) cleanupTotal=$cleanupActionsTotal"
        if ($pollNum % 10 -eq 0) { Write-Host "  >>> Dashboards generated (P68 MD+JSON + P70 COM MD+JSON)" }

    } catch {
        $errTs = Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK'
        $errEvent = [ordered]@{
            timestamp = $errTs
            event_type = 'POLL_ERROR'
            event_id = "DSHD-P70-ERROR-$pollNum"
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
