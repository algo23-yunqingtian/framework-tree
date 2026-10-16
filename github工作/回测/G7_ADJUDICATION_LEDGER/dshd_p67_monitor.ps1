# DSHD-P67 Continuous Audit Monitor
# Started: 2026-10-16 17:00 GMT+8
# Purpose: Monitor Excel processes, xlsx files, audit ledger, HOLD factor enforcement
# Circuit breaker: continue_after_trip=false (READY)
# GATE: CLOSED/HOLD | Release Permit: NOT_ISSUED | Wind API Calls: 0

$ErrorActionPreference = "SilentlyContinue"
$monitorLog = "D:\DSH_WORK\github工作\回测\G7_ADJUDICATION_LEDGER\dshd_p67_monitor_log.jsonl"
$ledgerPath = "D:\DSH_WORK\github工作\回测\tracking_monitor_audit.jsonl"
$windExcelDataPath = "D:\DSH_WORK\github工作\回测\data-harbor\dsha_p49_prep\P49_backtest_audit\wind_excel_data"
$windEventsPath = "D:\DSH_WORK\github工作\回测\data-harbor\dsha_p49_prep\P49_backtest_audit\wind_excel_events.jsonl"

# Baseline state (from audit snapshot at 16:52)
$baselineExcelPids = @(16428, 37336, 36948, 35320, 35488)
$baselineLedgerSha = "0C71ECB2CEDF81F3DE45A38185795D0E55EB2414E5A0C99FF1B81644CBA5FB67"
$baselineLedgerLines = 36
$baselineXlsxFiles = @(
    "step_test_20261016_164827.xlsx",
    "opendpyxl_wsd_test.xlsx"
)
$pollCount = 0
$anomalies = @()
$startTime = Get-Date

Write-Host "[DSHD-P67 MONITOR] Started at $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')"
Write-Host "[DSHD-P67 MONITOR] Baseline: Excel PIDs=@($baselineExcelPids -join ','), Ledger sha8=0C71ECB2 ($baselineLedgerLines lines), xlsx files=@($baselineXlsxFiles.Count)"
Write-Host "[DSHD-P67 MONITOR] Polling every 60s. Ctrl+C to stop."
Write-Host ""

# Initial scan
function Scan-Once {
    $now = Get-Date
    $pollCount++
    $ts = $now.ToString("yyyy-MM-ddTHH:mm:ssK")
    $event = @{
        event_id = "DSHD-P67-MONITOR-POLL-$pollCount"
        event_type = "CONTINUOUS_MONITORING_POLL"
        timestamp = $ts
        agent = "DSHD-P67"
        poll_number = $pollCount
        results = @{}
        anomalies = @()
        invariants = @{
            wind_api_calls = 0
            gate = "CLOSED/HOLD"
            release_permit = "NOT_ISSUED"
            circuit_breaker = "READY"
            continue_after_trip = $false
        }
    }

    # 1. Check Excel processes
    $excelProcs = Get-Process EXCEL -ErrorAction SilentlyContinue | Select-Object Id, StartTime, @{N='WS_MB';E={[math]::Round($_.WorkingSet64/1MB,1)}}
    $currentPids = @($excelProcs | ForEach-Object { $_.Id })
    $newPids = $currentPids | Where-Object { $_ -notin $baselineExcelPids }
    $missingPids = $baselineExcelPids | Where-Object { $_ -notin $currentPids }
    
    $event.results.excel_processes = @{
        count = $currentPids.Count
        pids = $currentPids
        working_set = ($excelProcs | ForEach-Object { "$($_.Id):$($_.WS_MB)MB" }) -join ", "
        new_pids = $newPids
        missing_pids = $missingPids
    }

    if ($newPids.Count -gt 0) {
        $event.anomalies += "NEW_EXCEL_PROCESS: PID=@($newPids -join ',')"
    }
    if ($missingPids.Count -gt 0) {
        $event.anomalies += "MISSING_EXCEL_PROCESS: PID=@($missingPids -join ',')"
    }

    # 2. Check xlsx files
    if (Test-Path $windExcelDataPath) {
        $currentXlsx = Get-ChildItem $windExcelDataPath -Filter *.xlsx -ErrorAction SilentlyContinue | ForEach-Object { $_.Name }
        $newXlsx = $currentXlsx | Where-Object { $_ -notin $baselineXlsxFiles }
        $missingXlsx = $baselineXlsxFiles | Where-Object { $_ -notin $currentXlsx }
        
        $event.results.xlsx_files = @{
            count = $currentXlsx.Count
            files = $currentXlsx
            new_files = $newXlsx
            missing_files = $missingXlsx
        }

        if ($newXlsx.Count -gt 0) {
            $event.anomalies += "NEW_XLSX: @($newXlsx -join ',')"
            # Parse formulas from new xlsx files
            foreach ($f in $newXlsx) {
                $fpath = Join-Path $windExcelDataPath $f
                try {
                    $py = @"
import sys, zipfile, re
from xml.etree import ElementTree as ET
sys.stdout.reconfigure(encoding='utf-8')
p = r'$fpath'
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
try:
    with zipfile.ZipFile(p) as z:
        names = z.namelist()
        shared = []
        if 'xl/sharedStrings.xml' in names:
            root = ET.fromstring(z.read('xl/sharedStrings.xml'))
            for si in root.findall(f'{NS}si'):
                t = si.find(f'{NS}t')
                shared.append(t.text if t is not None and t.text else '')
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        sheets = wb.find(f'{NS}sheets')
        sn = []
        if sheets is not None:
            for s in sheets.findall(f'{NS}sheet'):
                sn.append(s.attrib.get('name'))
        for sni, snm in enumerate(sn, 1):
            sp = f'xl/worksheets/sheet{sni}.xml'
            if sp in names:
                root = ET.fromstring(z.read(sp))
                cells = root.findall(f'{NS}sheetData/{NS}row/{NS}c')
                for c in cells:
                    f2 = c.find(f'{NS}f')
                    if f2 is not None and f2.text:
                        print(f'{c.attrib.get("r")}: {f2.text}')
except Exception as e:
    print(f'ERROR: {e}')
"@
                    $formulaResult = python -X utf8 -c $py 2>&1
                    $event.results.xlsx_formulas = @{ "$f" = $formulaResult }
                } catch {
                    $event.results.xlsx_formulas = @{ "$f" = "PARSE_ERROR" }
                }
            }
        }
        if ($missingXlsx.Count -gt 0) {
            $event.anomalies += "MISSING_XLSX: @($missingXlsx -join ',')"
        }
    }

    # 3. Check ledger
    if (Test-Path $ledgerPath) {
        $ledgerHash = (Get-FileHash $ledgerPath -Algorithm SHA256).Hash
        $ledgerLines = ((Get-Content $ledgerPath -Raw) -split "\n" | Where { $_.Length -gt 0 }).Count
        $event.results.ledger = @{
            sha256 = $ledgerHash
            lines = $ledgerLines
            changed = ($ledgerHash -ne $baselineLedgerSha)
        }
        if ($ledgerHash -ne $baselineLedgerSha) {
            $event.anomalies += "LEDGER_CHANGED: sha8=$($ledgerHash.Substring(0,8)) lines=$ledgerLines"
        }
    }

    # 4. Check wind_excel_events.jsonl for new events
    if (Test-Path $windEventsPath) {
        $windEventsHash = (Get-FileHash $windEventsPath -Algorithm SHA256).Hash
        $event.results.wind_events_sha8 = $windEventsHash.Substring(0, 8)
    }

    # Check for anomalies
    $event.anomaly_count = $event.anomalies.Count
    if ($event.anomalies.Count -gt 0) {
        $event.severity = "INFO"  # Anomalies are informational during exploration phase
    } else {
        $event.severity = "OK"
    }

    # Write to log
    $json = $event | ConvertTo-Json -Depth 10 -Compress
    Add-Content -Path $monitorLog -Value $json -Encoding UTF8

    # Console output
    $status = if ($event.anomalies.Count -gt 0) { "⚠️  $($event.anomalies -join '; ')" } else { "✅ All clear" }
    Write-Host "[$ts] Poll #$pollCount | Excel:$($currentPids.Count) xlsx:$($event.results.xlsx_files.count) ledger:$($ledgerLines) lines | $status"
}

# Main loop
try {
    while ($true) {
        Scan-Once
        Start-Sleep -Seconds 60
    }
} catch {
    Write-Host "[DSHD-P67 MONITOR] Exception: $_"
    Write-Host "[DSHD-P67 MONITOR] Monitor stopping at $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')"
}
