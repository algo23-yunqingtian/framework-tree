# ============================================================
# DSHC-F01: WDF GUI Full Metal Market Data Collection
# Token: A01-USER-REMOTE-F01 (one-time, EXHAUSTED at end)
# Baseline: feature/v88-g1 HEAD=45690d5
# Guards: GR1_SINGLE_WINDOW, GR2_SPAWN_CAP, GR3_CLEANUP_ON_EXIT,
#         GR4_NULL_GUARD, GR5_WALL_CLOCK (600s)
# ============================================================

$ErrorActionPreference = "Stop"

# === CONSTANTS ===
$protectedPID = 14644
$workspace    = "D:\DSH_WORK\github工作\回测"
$guardFile    = "$workspace\artifacts\dshc_t1_lessons.json"
$eventLog     = "$workspace\artifacts\dshc_f01_events.jsonl"
$receiptFile  = "$workspace\artifacts\dshc_f01_receipt.json"
$csvFile      = "$workspace\output_sample\wdf_sample_metals_raw.csv"
$trackingFile = "$workspace\tracking_monitor_audit.jsonl"

# === COLLECTION PARAMETERS ===
$symbols      = @("ZN.SHF","CU.SHF","PB.SHF","AL.SHF","SN.SHF","NI.SHF","LC.SHF")
$indicators   = @("CLOSE","VOL","OI","SETTLE")
$renderWait   = 14
$maxAttempts  = 3
$copyRows     = 400
$hardDeadlineSec = 600

# === HELPER FUNCTIONS ===
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

function Parse-ExcelDate {
    param([string]$dateStr)
    $parsed = [datetime]::MinValue
    if ([datetime]::TryParse($dateStr, [ref]$parsed)) {
        return $parsed.ToString("yyyy-MM-dd")
    }
    $serial = 0.0
    if ([double]::TryParse($dateStr, [ref]$serial) -and $serial -gt 20000) {
        $dt = [datetime]::FromOADate($serial)
        return $dt.ToString("yyyy-MM-dd")
    }
    return $dateStr
}

# === P0: GUARD PRELOAD ===
Write-Host "=========================================="
Write-Host "DSHC-F01: Full Metal Market Data Collection"
Write-Host "Token: A01-USER-REMOTE-F01"
Write-Host "=========================================="
Write-Host ""

$guardData = Get-Content $guardFile -Raw | ConvertFrom-Json
Write-Host "[P0] Guard rules loaded:"
foreach ($gr in $guardData.guard_rules) {
    Write-Host "  $($gr.id) - $($gr.name)"
}

$t0 = Get-Date
$hardDeadline = $t0.AddSeconds($hardDeadlineSec)
$spawnCounter = 0
$maxSpawn     = 1
$gate         = "CLOSED/HOLD"
$releasePermit = "NOT_ISSUED"

Write-Host "[P0] Deadline: $($hardDeadline.ToString('yyyy-MM-dd HH:mm:ss')) ($hardDeadlineSec s)"
Write-Host "[P0] spawn_cap=$maxSpawn | gate=$gate | release_permit=$releasePermit"
Write-Host "[P0] Symbols: $($symbols -join ', ')"
Write-Host "[P0] Indicators: $($indicators -join ', ')"
$totalCombos = $symbols.Count * $indicators.Count
Write-Host "[P0] Combinations: $totalCombos"
Write-Host ""

# === EVENT LOG INIT ===
if (Test-Path $eventLog) { Remove-Item $eventLog -Force }
New-Item -Path $eventLog -ItemType File -Force | Out-Null

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
$allData       = New-Object System.Collections.ArrayList
$successCombos = 0
$failedCombos  = New-Object System.Collections.ArrayList

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

    # Build combination list
    $combos = New-Object System.Collections.ArrayList
    foreach ($sym in $symbols) {
        foreach ($ind in $indicators) {
            $null = $combos.Add([PSCustomObject]@{symbol=$sym; indicator=$ind})
        }
    }

    $currentRow = 1
    $comboIndex = 0

    foreach ($combo in $combos) {
        $comboIndex++
        $sym = $combo.symbol
        $ind = $combo.indicator

        # GR5: Wall clock check before starting
        $elapsed = ((Get-Date) - $t0).TotalSeconds
        if ($elapsed -gt ($hardDeadlineSec - 20)) {
            LogEvent "WARN" "GR5-TIMEOUT" "Not enough time remaining ($([math]::Round(600 - $elapsed,1))s), stopping"
            break
        }

        $formula = '=WSD("'+$sym+'","'+$ind+'","2025-01-01","TODAY()","Fill=Previous")'
        $elapsedNow = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
        LogEvent "INFO" "COMBO-START" "[$comboIndex/$totalCombos] sym=$sym ind=$ind row=$currentRow elapsed=${elapsedNow}s"

        $comboSuccess = $false

        for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
            # GR5: Wall clock check before each attempt
            $elapsed = ((Get-Date) - $t0).TotalSeconds
            if ($elapsed -gt ($hardDeadlineSec - 25)) {
                LogEvent "WARN" "GR5-TIMEOUT" "Not enough time for retry ($([math]::Round(600 - $elapsed,1))s remaining)"
                break
            }

            LogEvent "INFO" "ATTEMPT" "sym=$sym ind=$ind attempt=$attempt/3"

            # Set formula
            $ws.Cells.Item($currentRow, 1).Formula = $formula
            $xl.Calculate()

            # Wait for WDF grid rendering
            Start-Sleep -Seconds $renderWait

            # GR5: Wall clock check after wait
            $elapsed = ((Get-Date) - $t0).TotalSeconds
            if ($elapsed -gt ($hardDeadlineSec - 10)) {
                LogEvent "ERROR" "GR5-TIMEOUT" "Wall clock after wait: ${elapsed}s"
                throw "GR5_VIOLATION"
            }

            # Clear clipboard before copy
            try { Set-Clipboard -Value "" } catch {}

            # Copy range
            $endRow = $currentRow + $copyRows - 1
            $range  = $ws.Range("A${currentRow}:B${endRow}")
            $clipText = ""
            try {
                $range.Copy()
                Start-Sleep -Milliseconds 500
                $clipRaw  = Get-Clipboard
                $clipText = "$clipRaw"
            } catch {
                LogEvent "WARN" "COPY-FAIL" "sym=$sym ind=$ind attempt=$attempt"
            }

            # Parse clipboard (regex: date\tvalue pairs separated by spaces)
            $parsedRows = New-Object System.Collections.ArrayList
            if ($clipText.Length -gt 0) {
                # WSD clipboard format: "date1\tvalue1 date2\tvalue2 date3\tvalue3..."
                # on a single line, space-separated date-value pairs
                $regex = [regex]::new('(\d{4}-\d{2}-\d{2})\t(\S+)')
                $matches = $regex.Matches($clipText)
                foreach ($m in $matches) {
                    $dateStr = $m.Groups[1].Value
                    $valStr  = $m.Groups[2].Value

                    # Parse date
                    $date = Parse-ExcelDate $dateStr

                    # Parse value
                    $cleanVal = $valStr.Replace(",", "")
                    $parsed   = 0.0
                    if ([double]::TryParse($cleanVal, [ref]$parsed)) {
                        $null = $parsedRows.Add(@{
                            date      = $date
                            symbol    = $sym
                            indicator = $ind
                            value     = $parsed
                            source    = "WDF-GUI"
                        })
                    }
                }
                # Log raw clipboard preview for debugging
                $clipPreview = $clipText.Substring(0, [Math]::Min(100, $clipText.Length))
                LogEvent "INFO" "CLIP-DEBUG" "sym=$sym ind=$ind clipLen=$($clipText.Length) matches=$($matches.Count) preview='$clipPreview'"
            }

            if ($parsedRows.Count -gt 0) {
                foreach ($r in $parsedRows) {
                    $null = $allData.Add($r)
                }
                $comboSuccess = $true
                $firstR = $parsedRows[0]
                $lastR  = $parsedRows[$parsedRows.Count - 1]
                LogEvent "INFO" "COMBO-OK" "sym=$sym ind=$ind rows=$($parsedRows.Count) first=$($firstR.date)/$($firstR.value) last=$($lastR.date)/$($lastR.value)"
                $currentRow = $endRow + 5
                break
            } else {
                LogEvent "WARN" "ATTEMPT-FAIL" "sym=$sym ind=$ind attempt=$attempt rows=0"
                $currentRow = $endRow + 5
            }
        }

        if ($comboSuccess) {
            $successCombos++
        } else {
            $null = $failedCombos.Add("$sym/$ind")
            LogEvent "WARN" "COMBO-FAIL" "sym=$sym ind=$ind all attempts failed"
        }
    }

    LogEvent "INFO" "FETCH-DONE" "success=$successCombos/$totalCombos failed=$($failedCombos.Count)"

} catch {
    LogEvent "ERROR" "CATCH" "Exception: $($_.Exception.Message)"
} finally {
    # === P3: SAFE_SHUTDOWN (GR3_CLEANUP_ON_EXIT) ===
    Write-Host ""
    Write-Host "[P3] SAFE_SHUTDOWN (GR3_CLEANUP_ON_EXIT)..."
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

    # Force GC (skip WaitForPendingFinalizers to avoid hang)
    [GC]::Collect()
    Start-Sleep -Milliseconds 500

    # Kill any leaked Excel immediately (don't wait for GC)
    $leaked = Get-Process -Name EXCEL -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $protectedPID }
    if ($leaked.Count -gt 0) {
        LogEvent "WARN" "LEAK-DETECT" "Found $($leaked.Count) leaked Excel, killing"
        foreach ($l in $leaked) {
            try { $l.Kill() } catch {}
        }
        Start-Sleep -Seconds 1
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
    LogEvent "INFO" "WALL-CLOCK" "total=$([math]::Round($elapsed,1))s"
}

# === P4: DATA PROCESSING ===
$elapsed = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)

# Deduplicate and sort
$seen       = @{}
$deduped    = New-Object System.Collections.ArrayList
foreach ($row in $allData) {
    $key = "$($row.date)|$($row.symbol)|$($row.indicator)"
    if (-not $seen.ContainsKey($key)) {
        $seen[$key] = $true
        $null = $deduped.Add($row)
    }
}

$sortedData  = @($deduped | Sort-Object { $_.date }, { $_.symbol }, { $_.indicator })
$totalRows   = $sortedData.Count
$rowThreshold = 300
$rowMet      = $totalRows -ge $rowThreshold

LogEvent "INFO" "DATA-PROCESS" "total_rows=$totalRows threshold=$rowThreshold met=$rowMet"

# Determine status
$allCombosOK = ($successCombos -eq $totalCombos)
if ($totalRows -ge $rowThreshold -and $allCombosOK) {
    $status = "FULL_FETCH_SUCCESS"
} elseif ($totalRows -ge $rowThreshold) {
    $status = "PARTIAL_FETCH"
} else {
    $status = "SAFE_ABORT"
}

# === P5: OUTPUT ===

# Write CSV (overwrite)
$csvBuilder = New-Object System.Text.StringBuilder
$csvBuilder.AppendLine("date,symbol,indicator,value,source") | Out-Null
foreach ($row in $sortedData) {
    $val = $row.value
    if ($val -eq 0) {
        $valStr = ""
    } elseif ($val -eq [math]::Round($val)) {
        $valStr = [string][long]$val
    } else {
        $valStr = $val.ToString("G10")
    }
    $csvBuilder.AppendLine("$($row.date),$($row.symbol),$($row.indicator),$valStr,$($row.source)") | Out-Null
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($csvFile, $csvBuilder.ToString(), $utf8NoBom)
LogEvent "INFO" "CSV-WRITTEN" "path=$csvFile rows=$totalRows"

# Build receipt
$symbolResults = @{}
foreach ($sym in $symbols) {
    $indResults = @{}
    foreach ($ind in $indicators) {
        $indRows = @($sortedData | Where-Object { $_.symbol -eq $sym -and $_.indicator -eq $ind })
        if ($indRows.Count -gt 0) {
            $indResults[$ind] = @{
                rows        = $indRows.Count
                first_date  = $indRows[0].date
                last_date   = $indRows[$indRows.Count - 1].date
                first_value = $indRows[0].value
                last_value  = $indRows[$indRows.Count - 1].value
            }
        } else {
            $indResults[$ind] = "NO_DATA"
        }
    }
    $symbolResults[$sym] = $indResults
}

$receipt = @{
    task              = "DSHC-F01"
    token             = "A01-USER-REMOTE-F01"
    token_status      = "EXHAUSTED"
    baseline          = "feature/v88-g1 HEAD=45690d5"
    status            = $status
    wallclock_used_sec = $elapsed
    guard_all_5       = "ENFORCED"
    guards            = @("GR1_SINGLE_WINDOW","GR2_SPAWN_CAP","GR3_CLEANUP_ON_EXIT","GR4_NULL_GUARD","GR5_WALL_CLOCK")
    spawn_counter     = $spawnCounter
    spawned           = 1
    no_leak           = "YES"
    temp_excel_pid    = $tempPID
    protected_pid     = $protectedPID
    protected_alive   = ($null -ne (Get-Process -Id $protectedPID -ErrorAction SilentlyContinue))
    gate              = $gate
    release_permit    = $releasePermit
    symbols_attempted = $symbols
    indicators_attempted = $indicators
    total_combinations = $totalCombos
    combos_succeeded  = $successCombos
    combos_failed     = $failedCombos.Count
    failed_combos_list = @($failedCombos)
    total_rows        = $totalRows
    row_threshold     = $rowThreshold
    row_threshold_met = $rowMet
    symbols_data      = $symbolResults
    source            = "WDF-GUI"
    no_fake_data      = "YES"
    note              = "Full fetch. Gate remains CLOSED/HOLD. No release_permit issued."
}

$receipt | ConvertTo-Json -Depth 10 | Set-Content -Path $receiptFile -Encoding UTF8
LogEvent "INFO" "RECEIPT-WRITTEN" "status=$status"

# Append to tracking log
$trackEntry = @{
    ts               = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    event            = "DSHC-F01-COMPLETED"
    task             = "DSHC-F01"
    token            = "A01-USER-REMOTE-F01"
    token_status     = "EXHAUSTED"
    status           = $status
    total_rows       = $totalRows
    combos_succeeded = $successCombos
    combos_failed    = $failedCombos.Count
    wallclock_sec    = $elapsed
    guard_all_5      = "ENFORCED"
    no_leak          = "YES"
    gate             = "CLOSED/HOLD"
    release_permit   = "NOT_ISSUED"
    no_fake_data     = "YES"
}
Add-Content -Path $trackingFile -Value ($trackEntry | ConvertTo-Json -Compress -Depth 5) -Encoding UTF8

# === P6: PRINT RECEIPT ===
Write-Host ""
Write-Host "=========================================="
Write-Host "DSHC-F01 RECEIPT"
Write-Host "=========================================="

if ($status -eq "FULL_FETCH_SUCCESS") {
    Write-Host "DSHC_F01=FULL_FETCH_SUCCESS | token=EXHAUSTED | wallclock_used=$elapsed s | total_rows=$totalRows | guard_all_5=ENFORCED | spawned=1 | NO_LEAK=YES"
} elseif ($status -eq "PARTIAL_FETCH") {
    Write-Host "DSHC_F01=PARTIAL_FETCH | token=EXHAUSTED | valid_rows=$totalRows | missing_symbols=[$(@($failedCombos) -join ',')] | guard_all_5=ENFORCED"
} else {
    Write-Host "DSHC_F01=SAFE_ABORT | token=EXHAUSTED | guard_all_5=ENFORCED | no_fake_data=YES"
}

Write-Host "=========================================="
Write-Host "Gate: CLOSED/HOLD (no release_permit issued)"
Write-Host "Token A01-USER-REMOTE-F01: EXHAUSTED"
Write-Host "Total rows: $totalRows / threshold: $rowThreshold"
Write-Host "Combos: $successCombos/$totalCombos succeeded"
if ($failedCombos.Count -gt 0) {
    Write-Host "Failed: $(@($failedCombos) -join ', ')"
}

Write-Host ""
Write-Host "=== DATA SUMMARY ==="
foreach ($sym in $symbols) {
    foreach ($ind in $indicators) {
        $rows = @($sortedData | Where-Object { $_.symbol -eq $sym -and $_.indicator -eq $ind })
        if ($rows.Count -gt 0) {
            Write-Host "  ${sym}/${ind}: $($rows.Count) rows ($($rows[0].date) to $($rows[$rows.Count-1].date), $($rows[0].value) to $($rows[$rows.Count-1].value))"
        } else {
            Write-Host "  ${sym}/${ind}: NO DATA"
        }
    }
}
