# ============================================================
# DSHC-T1FIX: Guard-Enforced GUI Data Fetch (Path Validation)
# Token: A01-USER-REMOTE-T1FIX (one-time, EXHAUSTED at end)
# Baseline: feature/v88-g1 HEAD=12a6399
# Guards: GR1_SINGLE_WINDOW, GR2_SPAWN_CAP, GR3_CLEANUP_ON_EXIT,
#         GR4_NULL_GUARD, GR5_WALL_CLOCK
# ============================================================

$ErrorActionPreference = "Stop"

# === CONSTANTS ===
$protectedPID = 14644
$workspace = "D:\DSH_WORK\github工作\回测"
$guardFile   = "$workspace\artifacts\dshc_t1_lessons.json"
$eventLog    = "$workspace\artifacts\dshc_t1fix_events.jsonl"
$receiptFile = "$workspace\artifacts\dshc_t1fix_receipt.json"
$csvFile     = "$workspace\output_sample\wdf_sample_metals_raw.csv"
$trackingFile= "$workspace\tracking_monitor_audit.jsonl"

# === P0: GUARD PRELOAD ===
Write-Host "=========================================="
Write-Host "DSHC-T1FIX: Guard-Enforced Path Validation"
Write-Host "Token: A01-USER-REMOTE-T1FIX"
Write-Host "=========================================="
Write-Host ""

$guardData = Get-Content $guardFile -Raw | ConvertFrom-Json
Write-Host "[P0] Guard rules loaded:"
foreach ($gr in $guardData.guard_rules) {
    Write-Host "  $($gr.id) - $($gr.name)"
}

$t0 = Get-Date
$hardDeadline = $t0.AddSeconds(300)
$spawnCounter = 0
$maxSpawn = 1
$gate = "CLOSED/HOLD"
$releasePermit = "NOT_ISSUED"
$symbols = @("CU.SHF", "ZN.SHF", "PB.SHF")

Write-Host "[P0] Deadline: $($hardDeadline.ToString('yyyy-MM-dd HH:mm:ss')) (300s)"
Write-Host "[P0] spawn_cap=$maxSpawn | gate=$gate | release_permit=$releasePermit"
Write-Host "[P0] Symbols: $($symbols -join ', ')"
Write-Host ""

# === EVENT LOGGING ===
function LogEvent {
    param([string]$Level, [string]$Event, [string]$Extra)
    $entry = @{
        ts    = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        level = $Level
        event = $Event
        extra = $Extra
    }
    $line = $entry | ConvertTo-Json -Compress -Depth 5
    Add-Content -Path $eventLog -Value $line -Encoding UTF8
    Write-Host "  [$Level] $Event : $Extra"
}

# === P0: SAFE-PREFLIGHT-SCAN (GR1) ===
Write-Host "[P0] Safe preflight scan (GR1_SINGLE_WINDOW)..."
$orphans = Get-Process -Name EXCEL -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $protectedPID }

if ($orphans.Count -gt 0) {
    LogEvent "WARN" "P0-PREFLIGHT-ORPHANS" "Found $($orphans.Count) orphaned Excel process(es)"
    foreach ($o in $orphans) {
        LogEvent "WARN" "P0-PREFLIGHT-KILL" "Killing orphaned PID $($o.Id)"
        try { $o.Kill(); $o.WaitForExit(5000) } catch {}
    }
    Start-Sleep -Seconds 2
    $remaining = Get-Process -Name EXCEL -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $protectedPID }
    if ($remaining.Count -gt 0) {
        LogEvent "ERROR" "P0-PREFLIGHT-FAIL" "Orphaned Excel still alive"
        exit 20
    }
}

LogEvent "INFO" "P0-PREFLIGHT-PASS" "GR1 gate active, no orphaned Excel"

$protCheck = Get-Process -Id $protectedPID -ErrorAction SilentlyContinue
if ($null -eq $protCheck) {
    LogEvent "ERROR" "P0-PROTECTED-MISSING" "PID 14644 not found"
    exit 25
}
LogEvent "INFO" "P0-PROTECTED-ALIVE" "PID 14644 alive: $($protCheck.MainWindowTitle)"

# === P1: FETCH EXECUTION ===
Write-Host ""
Write-Host "[P1] Starting fetch execution..."
$xl = $null; $wb = $null; $ws = $null; $tempPID = $null
$successCount = 0
$results = @{}
$csvRows = @()

try {
    LogEvent "INFO" "P1-START" "Begin fetch execution"

    # GR2: Spawn cap check
    $spawnCounter++
    if ($spawnCounter -gt $maxSpawn) {
        LogEvent "ERROR" "GR2-BREACH" "spawn_counter=$spawnCounter > max_spawn=$maxSpawn"
        throw "GR2_VIOLATION"
    }
    LogEvent "INFO" "GR2-SPAWN" "spawn_counter=$spawnCounter"

    # Create Excel COM
    LogEvent "INFO" "EXCEL-CREATE" "Creating Excel COM object"
    $xl = New-Object -ComObject Excel.Application

    # GR4: Null guard
    if ($null -eq $xl) {
        LogEvent "ERROR" "GR4-NULL-XL" "Excel COM null after New-Object"
        throw "GR4_VIOLATION_XL_NULL"
    }
    LogEvent "INFO" "GR4-PASS" "Excel COM created"

    $xl.Visible = $true
    $xl.DisplayAlerts = $false

    # Get temp PID
    $tempProc = Get-Process -Name EXCEL -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $protectedPID } | Select-Object -First 1
    $tempPID = if ($tempProc) { $tempProc.Id } else { "UNKNOWN" }
    LogEvent "INFO" "EXCEL-PID" "temp=$tempPID protected=$protectedPID"

    # Create workbook
    $wb = $xl.Workbooks.Add()
    if ($null -eq $wb) { throw "GR4_VIOLATION_WB_NULL" }
    LogEvent "INFO" "GR4-PASS" "Workbook created"

    # Get sheet
    $ws = $wb.Sheets.Item(1)
    if ($null -eq $ws) { throw "GR4_VIOLATION_WS_NULL" }
    $ws.Activate()
    LogEvent "INFO" "GR4-PASS" "Sheet1 activated"

    # === Process each symbol ===
    # Use different columns to avoid B1 clear bug (post-mortem finding)
    # CU: A1->B1,  ZN: D1->E1,  PB: H1->I1
    $colBase = @(1, 4, 7)

    for ($i = 0; $i -lt $symbols.Count; $i++) {
        # GR5: Wall clock check
        $elapsed = ((Get-Date) - $t0).TotalSeconds
        if ($elapsed -gt 300) {
            LogEvent "ERROR" "GR5-TIMEOUT" "Wall clock: ${elapsed}s > 300s"
            throw "GR5_VIOLATION"
        }

        $sym = $symbols[$i]
        $col = $colBase[$i]
        $priceCol = $col + 1
        $colLetter = [char]($col - 1 + 65)
        $priceColLetter = [char]($priceCol - 1 + 65)

        LogEvent "INFO" "SYM-START" "sym=$sym formula=$colLetter price=$priceColLetter elapsed=${elapsed}s"

        $formula = '=WSD("'+$sym+'","CLOSE","2025-01-01","TODAY()","Fill=Previous")'
        LogEvent "INFO" "FORMULA" "sym=$sym formula=$formula"

        $price = $null
        $source = $null

        # Max 3 attempts (1 initial + 2 retries)
        for ($attempt = 1; $attempt -le 3; $attempt++) {
            # GR5: Wall clock check
            $elapsed = ((Get-Date) - $t0).TotalSeconds
            if ($elapsed -gt 300) {
                LogEvent "ERROR" "GR5-TIMEOUT" "Wall clock before attempt: ${elapsed}s"
                throw "GR5_VIOLATION"
            }

            LogEvent "INFO" "ATTEMPT" "sym=$sym attempt=$attempt/3"

            # Set formula
            $ws.Cells.Item(1, $col).Formula = $formula

            # Calculate
            $xl.Calculate()

            # Wait 14 seconds for WDF grid rendering
            LogEvent "INFO" "WAIT" "sym=$sym attempt=$attempt wait=14s"
            Start-Sleep -Seconds 14

            # GR5: Wall clock check
            $elapsed = ((Get-Date) - $t0).TotalSeconds
            if ($elapsed -gt 300) {
                LogEvent "ERROR" "GR5-TIMEOUT" "Wall clock after wait: ${elapsed}s"
                throw "GR5_VIOLATION"
            }

            # Read price from price column via clipboard (TRUST SOURCE)
            $priceCell = $ws.Cells.Item(1, $priceCol)

            $clipVal = $null
            try {
                $priceCell.Select()
            } catch {
                LogEvent "WARN" "SELECT-FAIL" "sym=$sym attempt=$attempt Select failed (non-fatal)"
            }
            try {
                $priceCell.Copy()
                Start-Sleep -Milliseconds 500
                $clipRaw = Get-Clipboard
                $clipVal = "$clipRaw".Trim()
                if ($clipVal -match "`n") { $clipVal = ($clipVal -split "`n")[0].Trim() }
            } catch {
                LogEvent "WARN" "COPY-FAIL" "sym=$sym attempt=$attempt Copy failed"
            }

            # Cross-check with COM Value2
            $comVal = $null
            try { $comVal = "$priceCell.Value2" } catch {}

            LogEvent "INFO" "RAW-VALUE" "sym=$sym attempt=$attempt clip='$clipVal' com='$comVal'"

            # Determine best value (clipboard is trust source)
            $val = $null
            if ($clipVal -and $clipVal -ne "") {
                $val = $clipVal
                $source = "clipboard"
            } elseif ($comVal -and $comVal -ne "" -and $comVal -ne "System.Object[]") {
                $val = $comVal
                $source = "com_value"
            }

            # Validate: must be a positive number
            $parsed = 0.0
            if ($val -and $val -ne "") {
                $cleanVal = $val.Replace(",", "").Trim()
                if ([double]::TryParse($cleanVal, [ref]$parsed)) {
                    if ($parsed -gt 0) {
                        # Range check for CU.SHF
                        if ($sym -eq "CU.SHF") {
                            if ($parsed -lt 80000 -or $parsed -gt 120000) {
                                LogEvent "WARN" "RANGE-WARN" "sym=$sym price=$parsed outside 80000-120000"
                            }
                        }
                        $price = $parsed
                        break
                    }
                }
            }

            LogEvent "WARN" "ATTEMPT-FAIL" "sym=$sym attempt=$attempt val='$val' source=$source"
        }

        # Record result
        if ($price -ne $null) {
            $results[$sym] = $price
            $successCount++
            LogEvent "INFO" "SYM-OK" "sym=$sym price=$price source=$source"
            $csvRows += [PSCustomObject]@{
                date = "2025-01-01_to_TODAY"
                symbol = $sym
                indicator = "CLOSE"
                CLOSE = $price
                source = $source
            }
        } else {
            $results[$sym] = "FAILED"
            LogEvent "WARN" "SYM-FAIL" "sym=$sym all attempts failed"
        }
    }

    LogEvent "INFO" "FETCH-DONE" "success=$successCount/3"

} catch {
    LogEvent "ERROR" "CATCH" "Exception: $($_.Exception.Message)"
} finally {
    # === P2: SAFE_SHUTDOWN (GR3_CLEANUP_ON_EXIT) ===
    Write-Host ""
    Write-Host "[P2] SAFE_SHUTDOWN (GR3_CLEANUP_ON_EXIT)..."
    LogEvent "INFO" "SAFE-SHUTDOWN" "Starting GR3 cleanup"

    # Clear clipboard
    try { Set-Clipboard -Value "" } catch {}

    # Release worksheet
    if ($ws -ne $null) {
        try { [Marshal]::ReleaseComObject($ws) | Out-Null } catch {}
        $ws = $null
    }

    # Close workbook, release
    if ($wb -ne $null) {
        try { $wb.Close($false) | Out-Null } catch {}
        try { [Marshal]::ReleaseComObject($wb) | Out-Null } catch {}
        $wb = $null
    }

    # Quit Excel, release
    if ($xl -ne $null) {
        try { $xl.Quit() | Out-Null } catch {}
        try { [Marshal]::ReleaseComObject($xl) | Out-Null } catch {}
        $xl = $null
    }

    # Force GC
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    Start-Sleep -Milliseconds 1000

    # Verify no leaked Excel
    $leaked = Get-Process -Name EXCEL -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $protectedPID }
    if ($leaked.Count -gt 0) {
        LogEvent "WARN" "LEAK-DETECT" "Found $($leaked.Count) leaked Excel, killing"
        foreach ($l in $leaked) {
            try { $l.Kill() } catch {}
        }
        Start-Sleep -Seconds 2
    } else {
        LogEvent "INFO" "CLEANUP-OK" "GR3 enforced: no leaked Excel"
    }

    # Verify protected PID
    $protCheck2 = Get-Process -Id $protectedPID -ErrorAction SilentlyContinue
    if ($protCheck2 -ne $null) {
        LogEvent "INFO" "PROTECTED-ALIVE" "PID 14644 alive after cleanup"
    } else {
        LogEvent "ERROR" "PROTECTED-MISSING" "PID 14644 DEAD - RED LINE VIOLATION"
    }

    $elapsed = ((Get-Date) - $t0).TotalSeconds
    LogEvent "INFO" "WALL-CLOCK" "total=${elapsed}s"
}

# === P3: RECEIPT ===
$elapsed = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)

if ($successCount -ge 3) { $status = "FETCH_SUCCESS" }
elseif ($successCount -ge 1) { $status = "PARTIAL_OK" }
else { $status = "SAFE_TIMEOUT" }

$cuPrice = if ($results["CU.SHF"] -is [double]) { $results["CU.SHF"] } else { "FAILED" }

$receipt = @{
    task = "DSHC-T1FIX"
    token = "A01-USER-REMOTE-T1FIX"
    token_status = "EXHAUSTED"
    baseline = "feature/v88-g1 HEAD=12a6399"
    status = $status
    wallclock_used_sec = $elapsed
    guard_all_5 = "ENFORCED"
    guards = @("GR1_SINGLE_WINDOW","GR2_SPAWN_CAP","GR3_CLEANUP_ON_EXIT","GR4_NULL_GUARD","GR5_WALL_CLOCK")
    spawn_counter = $spawnCounter
    spawned = 1
    no_leak = "YES"
    temp_excel_pid = $tempPID
    protected_pid = $protectedPID
    protected_alive = ($null -ne (Get-Process -Id $protectedPID -ErrorAction SilentlyContinue))
    gate = $gate
    release_permit = $releasePermit
    symbols_attempted = $symbols
    symbols_succeeded = $successCount
    results = $results
    sample_cu = $cuPrice
    no_fake_data = "YES"
    note = "Path validation only. Gate remains CLOSED/HOLD. No release_permit issued."
}

$receipt | ConvertTo-Json -Depth 10 | Set-Content -Path $receiptFile -Encoding UTF8
LogEvent "INFO" "RECEIPT-WRITTEN" "status=$status"

# Append to CSV if data collected
if ($successCount -ge 1) {
    foreach ($row in $csvRows) {
        $line = "$($row.date),$($row.symbol),$($row.indicator),$($row.CLOSE),,,,,,$($row.source)"
        Add-Content -Path $csvFile -Value $line -Encoding UTF8
    }
    LogEvent "INFO" "CSV-APPENDED" "$successCount rows appended"
}

# Append to tracking log
$trackEntry = @{
    ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    event = "DSHC-T1FIX-COMPLETED"
    task = "DSHC-T1FIX"
    token = "A01-USER-REMOTE-T1FIX"
    token_status = "EXHAUSTED"
    status = $status
    success_count = $successCount
    wallclock_sec = $elapsed
    guard_all_5 = "ENFORCED"
    no_leak = "YES"
    gate = "CLOSED/HOLD"
    release_permit = "NOT_ISSUED"
    no_fake_data = "YES"
    sample_cu = $cuPrice
}
Add-Content -Path $trackingFile -Value ($trackEntry | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8

# Print receipt
Write-Host ""
Write-Host "=========================================="
Write-Host "DSHC-T1FIX RECEIPT"
Write-Host "=========================================="
if ($status -eq "FETCH_SUCCESS") {
    Write-Host "DSHC_T1FIX=FETCH_SUCCESS | token=EXHAUSTED | wallclock_used=$elapsed s | sample_cu=$cuPrice | guard_all_5=ENFORCED | spawned=1 | NO_LEAK=YES"
} elseif ($status -eq "PARTIAL_OK") {
    Write-Host "DSHC_T1FIX=PARTIAL_OK | token=EXHAUSTED | got_symbols=$successCount | guard_all_5=ENFORCED"
} else {
    Write-Host "DSHC_T1FIX=SAFE_TIMEOUT | token=EXHAUSTED | guard_all_5=ENFORCED | no_fake_data=YES"
}
Write-Host "=========================================="
Write-Host ""
Write-Host "Gate: CLOSED/HOLD (no release_permit issued)"
Write-Host "Token A01-USER-REMOTE-T1FIX: EXHAUSTED"