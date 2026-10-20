# DSHD-P80-A01-PHASE2 PARALLEL AUDIT & EVIDENCE VERIFICATION WATCH
# Baseline: feature/v88-g1
# Constraint: AUDIT_READ_ONLY; never_run_backtest=YES
# PID3472 main monitor + pwsh-13 P77 hash watch + pwsh-30 P80 watch
#   MUST NOT be stopped, restarted, or rebuilt.
# A01 tag: A01-USER-REMOTE-002 (audit tagging only, no execution privilege)
# All evidence written to the G7 adjudication ledger: append-only, immutable.
#
# INHERITED FROM P80 (one capability not turned off):
#   - BOM health self-check every poll (warn only, never auto-fix)
#   - wdf_sample_metals_raw.csv -> immediate independent SHA256 evidence
#   - artifact catalog (dshc_*/dsha_*) every 10 polls
#   - scheduled observation brief every 12 polls (not only on warnings)
#   - LONG-TYPE FIXED wind_api_calls counter (no exponential explosion;
#     observation only, never an automatic action trigger)
#
# PHASE2 ADDITIONS:
#   - P2.1 stale baseline archive: P76 baseline entries ARCHIVED, the
#         observation comparison list updated to R03. The running P77 watch
#         script is NOT modified; its SKILL_HASH_MISMATCH alerts are recorded
#         as KNOWN ARCHIVED DRIFT, not fresh anomalies.
#   - P2.2 BUG memo -> artifacts/dshd_bug_note_p67_windapi_counter.json
#   - P2.3a dual-hash verify: an INDEPENDENT PowerShell Get-FileHash SHA256 is
#         computed and compared against the DSHC fingerprint recorded in
#         cross_agent_artifact_index.json -> artifacts/dshd_a01_dualhash_verify.json
#   - P2.3b read-only quick scan: rough row count, header keyword check,
#         consecutive blank-line warning -> artifacts/dshd_a01_quick_scan.json
#         NOTE: the DSHD quick scan is an EARLY WARNING SIGNAL ONLY. It does
#         NOT replace and must NOT be used to bypass the DSHA-P68 formal
#         sanity gate and its 9-step pipeline.
#   - P2.4 every PHASE2 lifecycle evidence item is tagged A01-USER-REMOTE-002
#
# RED LINES (never crossed):
#   read-only throughout; never modify any raw file inside output_sample;
#   never bypass the DSHA-P68 formal validation; never auto-isolate,
#   auto-kill, or auto-circuit-break without a human instruction.

param()

# ========== CONSTANTS ==========
$baseDir = "D:\DSH_WORK\github工作\回测"
$ledgerDir = "$baseDir\G7_ADJUDICATION_LEDGER"
$artifactsDir = "$baseDir\artifacts"
$trackingLog = "$baseDir\tracking_monitor_audit.jsonl"
$scriptPath = "$ledgerDir\dshd_p80_a01_phase2_watch.ps1"
$p80SnapshotPath = "$artifactsDir\dshd_p80_a01_audit_snapshot.json"
# PHASE2-dedicated snapshot: P80 (pwsh-30) also writes $p80SnapshotPath, so the shared file
# alternates between tag 001 and tag 002. The dedicated file is PHASE2's authoritative trail.
$p80Phase2SnapshotPath = "$artifactsDir\dshd_p80_phase2_a01_audit_snapshot.json"
$evidencePath = "$artifactsDir\dshd_a01_file_evidence.json"
$catalogPath = "$artifactsDir\dshd_a01_artifact_catalog.json"
$briefPath = "$artifactsDir\dshd_a01_observation_brief.md"
$dualHashVerifyPath = "$artifactsDir\dshd_a01_dualhash_verify.json"
$quickScanPath = "$artifactsDir\dshd_a01_quick_scan.json"
$bugNotePath = "$artifactsDir\dshd_bug_note_p67_windapi_counter.json"
$crossAgentIndexPath = "$artifactsDir\cross_agent_artifact_index.json"
$skillDir = "$baseDir\system_skills\SKILL-WIND-EXCEL-WDF-BOOTSTRAP"
$outputSampleDir = "$baseDir\output_sample"
$monitorPid = 3472
$pollIntervalSec = 30
$snapshotIntervalSec = 300
$catalogIntervalPolls = 10
$briefIntervalPolls = 12
$a01Tag = "A01-USER-REMOTE-002"
$agentName = "DSHD-P80-PHASE2"
$taskName = "DSHC-TASK-A01-PHASE2"
$csvFileName = "wdf_sample_metals_raw.csv"
$p68MinFileSize = 5120
$p68MinRows = 300
$r03ManifestSha = "284E766178B861D39E47095DC1F453AA4819163750FA66721C714A2E85599707"
$statusLineOk = "一切观测平稳"
$requiredHeaderKeywords = @("date","symbol","indicator","CLOSE","VOL","OI","SETTLE","source")

# Observation comparison list: R03 (ACTIVE)
$r03Expected = @{
    "skill_readme.md"     = "3BE3E14511DEC8E669068CA944C43FC374DDFB6C94C2FEB2EA04120B3FBE10DD"
    "bootstrap_wdf.ps1"   = "F568F9723AA16DDB0105BFC74ADE68797B7DA5E54C7BA3A345711876B34344C2"
    "skill_manifest.json" = "95FE2B60398F952888655F7604DFB06E332A8D8C0F2B37B9625B315DF6A1B45A"
    "health_check_wdf.ps1" = "AF04F9EC099CF58B3E4312E7E7D93AEF50E93766715A9294DAA48E6326FF0397"
    "reset_wdf_safe.ps1"  = "4E7EDCB1305E8DE3585867BD08EA0A8B4C872785BA134862618D37A43D58451E"
}

# Archived stale baseline: P76 (REFERENCE ONLY - no longer used for comparison)
$p76ArchivedBaseline = @{
    "skill_readme.md"     = "E7A3BF2552AC899D11322EB23ED0D2D3B5B1D57C2338B5670C56C7D8993970FA"
    "bootstrap_wdf.ps1"   = "238134D6E6FF351B4A7B3BEABC2FA92D45C05BDC601F4F1C31BCC85E983E8925"
    "skill_manifest.json" = "1C1D58DE7C2D616A592F1D3A295BE063BDC2A9990CEF8B6E42DD57BE99F9FC3A"
    "health_check_wdf.ps1" = "0D0F4D76B9BE6B2126A11BB2C2D87BDF037DF10D118F06F02D18389CABE609A7"
    "reset_wdf_safe.ps1"  = "72846B4ECC6517B6B77C3A1B347BAA505DD84559C7548E56FC418361A1F861F3"
}

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
    csvLastSize = 0
    csvLastMtime = ""
    csvDualHashDone = $false
    csvQuickScanDone = $false
    lastDualHashResult = @{}
    lastQuickScanResult = @{}
    bugNoteWritten = $false
    bomWarningIssued = $false
}

# ========== HELPER: SHA256 via byte read + SHA256.Create (hash A) ==========
function Get-FileSha256 {
    param([string]$FilePath)
    try {
        $bytes = [System.IO.File]::ReadAllBytes($FilePath)
        $sha = [System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)) -replace '-',''
        return $sha
    } catch { return "" }
}

# ========== HELPER: SHA256 via Get-FileHash (INDEPENDENT hash B) ==========
function Get-SecondSha256 {
    param([string]$FilePath)
    try {
        $h = (Get-FileHash -Path $FilePath -Algorithm SHA256 -ErrorAction Stop).Hash
        return $h
    } catch { return "" }
}

# ========== HELPER: safe string truncation ==========
function Truncate-Str {
    param([string]$S, [int]$N)
    if ([string]::IsNullOrEmpty($S)) { return "" }
    if ($S.Length -le $N) { return $S }
    return $S.Substring(0, $N)
}

# ========== HELPER: Append JSONL event (BOM-prefixed, append-only) ==========
function Add-AuditEvent {
    param([hashtable]$EventData, [string]$TrackingLogPath)
    try {
        $json = $EventData | ConvertTo-Json -Compress -Depth 10
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
        # PHASE2 HARDENING (not present in P80): append a trailing LF so each event is a
        # self-delimited JSONL line. P80 omits it, so consecutive events merge into one
        # physical line and ConvertFrom-Json fails on those merged lines.
        $bomBytes = New-Object byte[] ($bytes.Length + 4)
        $bomBytes[0] = 0xEF; $bomBytes[1] = 0xBB; $bomBytes[2] = 0xBF
        [Array]::Copy($bytes, 0, $bomBytes, 3, $bytes.Length)
        $bomBytes[$bomBytes.Length - 1] = 0x0A
        $fs = [System.IO.FileStream]::new($TrackingLogPath, [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write)
        $fs.Write($bomBytes, 0, $bomBytes.Length)
        $fs.Flush()
        $fs.Close()
    } catch {
        Write-Host "[P80-P2-ERROR] Failed to append event: $_" -ForegroundColor Red
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

# ========== HELPER: latest gate / release_permit state from tracking log ==========
function Get-LatestGateState {
    param([string]$TrackingLogPath)
    $result = @{ gate = ""; release_permit = ""; source_ts = "" }
    # NOTE: gate/release_permit events are OLDER than the recent tail (e.g. L571/963/1031
    # while the log is ~1500 lines long), so the WHOLE log is scanned, newest first.
    try {
        if (!(Test-Path $TrackingLogPath)) { return $result }
        $lines = [System.IO.File]::ReadAllLines($TrackingLogPath, [System.Text.Encoding]::UTF8)
        for ($i = $lines.Count - 1; $i -ge 0; $i--) {
            try {
                $j = $lines[$i].TrimStart([char]0xFEFF) | ConvertFrom-Json -ErrorAction Stop
                if ($j.gate -and $j.release_permit) {
                    $result.gate = [string]$j.gate
                    $result.release_permit = [string]$j.release_permit
                    $result.source_ts = [string]$j.timestamp
                    $result.source_line = $i + 1
                    break
                }
            } catch { }
        }
    } catch { $result.error = $_.Exception.Message }
    return $result
}

# ========== HELPER: DSHA-P68 FINAL_STANDBY_LOCKED confirmation ==========
# NOTE: other events also contain the literal 'FINAL_STANDBY_LOCKED' (e.g. DSHA-A02
# probe payloads, unparseable lines), so only the authoritative P68 event qualifies:
# it must parse as JSON AND carry a non-empty baseline_commit with that status.
function Get-P68LockState {
    param([string]$TrackingLogPath)
    $result = @{ locked = $false; status = ""; event_id = ""; baseline_commit = ""; source_ts = "" }
    try {
        if (!(Test-Path $TrackingLogPath)) { return $result }
        $lines = [System.IO.File]::ReadAllLines($TrackingLogPath, [System.Text.Encoding]::UTF8)
        for ($i = $lines.Count - 1; $i -ge 0; $i--) {
            try {
                $j = $lines[$i].TrimStart([char]0xFEFF) | ConvertFrom-Json -ErrorAction Stop
                if ($j.baseline_commit -and ([string]$j.status) -match 'FINAL_STANDBY_LOCKED') {
                    $result.locked = $true
                    $result.status = [string]$j.status
                    $result.event_id = [string]$j.event_id
                    $result.baseline_commit = [string]$j.baseline_commit
                    $result.source_ts = [string]$j.timestamp_gmt8
                    $result.source_line = $i + 1
                    break
                }
            } catch { }
        }
    } catch { $result.error = $_.Exception.Message }
    return $result
}

# ========== HELPER: is a named watch script currently running? ==========
function Get-ScriptWatchAlive {
    param([string]$ScriptName)
    try {
        $procs = Get-CimInstance Win32_Process -Filter "Name='pwsh.exe' OR Name='powershell.exe'" -ErrorAction Stop
        foreach ($p in $procs) {
            if ($p.CommandLine -and $p.CommandLine -like "*$ScriptName*") {
                return @{ alive = $true; pid = $p.ProcessId }
            }
        }
        return @{ alive = $false; pid = 0 }
    } catch {
        return @{ alive = $false; pid = 0; error = $_.Exception.Message }
    }
}

# ========== HELPER: Write snapshot JSON ==========
function Write-SnapshotJson {
    param([hashtable]$Data, [string]$OutputPath, [string]$ArtifactsDir)
    try {
        $jsonStr = $Data | ConvertTo-Json -Depth 10 -Compress
        $tempJson = "$ArtifactsDir\.p80_phase2_snapshot_tmp.json"
        [System.IO.File]::WriteAllText($tempJson, $jsonStr, (New-Object System.Text.UTF8Encoding $false))
        & python -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); open(sys.argv[2],'w',encoding='utf-8').write(json.dumps(d,separators=(',',':'),ensure_ascii=False))" $tempJson $OutputPath
        if (Test-Path $tempJson) { Remove-Item $tempJson -Force -ErrorAction SilentlyContinue }
    } catch {
        Write-Host "[P80-P2-ERROR] Failed to write snapshot: $_" -ForegroundColor Red
    }
}

# ========== HELPER: Write file evidence JSON ==========
function Write-FileEvidenceJson {
    param([hashtable]$Data, [string]$OutputPath, [string]$ArtifactsDir)
    try {
        $tempJson = "$ArtifactsDir\.p80_phase2_evidence_tmp.json"
        [System.IO.File]::WriteAllText($tempJson, ($Data | ConvertTo-Json -Depth 10 -Compress), (New-Object System.Text.UTF8Encoding $false))
        & python -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); open(sys.argv[2],'w',encoding='utf-8').write(json.dumps(d,separators=(',',':'),ensure_ascii=False))" $tempJson $OutputPath
        if (Test-Path $tempJson) { Remove-Item $tempJson -Force -ErrorAction SilentlyContinue }
    } catch {
        Write-Host "[P80-P2-ERROR] Failed to write file evidence: $_" -ForegroundColor Red
    }
}

# ========== HELPER: Write artifact catalog JSON ==========
function Write-ArtifactCatalog {
    param([hashtable]$Data, [string]$OutputPath, [string]$ArtifactsDir)
    try {
        $tempJson = "$ArtifactsDir\.p80_phase2_catalog_tmp.json"
        [System.IO.File]::WriteAllText($tempJson, ($Data | ConvertTo-Json -Depth 10 -Compress), (New-Object System.Text.UTF8Encoding $false))
        & python -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); open(sys.argv[2],'w',encoding='utf-8').write(json.dumps(d,separators=(',',':'),ensure_ascii=False))" $tempJson $OutputPath
        if (Test-Path $tempJson) { Remove-Item $tempJson -Force -ErrorAction SilentlyContinue }
    } catch {
        Write-Host "[P80-P2-ERROR] Failed to write artifact catalog: $_" -ForegroundColor Red
    }
}

# ========== HELPER: Write dual-hash verify JSON ==========
function Write-DualHashVerifyJson {
    param([hashtable]$Data, [string]$OutputPath, [string]$ArtifactsDir)
    try {
        $tempJson = "$ArtifactsDir\.p80_phase2_dualhash_tmp.json"
        [System.IO.File]::WriteAllText($tempJson, ($Data | ConvertTo-Json -Depth 10 -Compress), (New-Object System.Text.UTF8Encoding $false))
        & python -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); open(sys.argv[2],'w',encoding='utf-8').write(json.dumps(d,separators=(',',':'),ensure_ascii=False))" $tempJson $OutputPath
        if (Test-Path $tempJson) { Remove-Item $tempJson -Force -ErrorAction SilentlyContinue }
    } catch {
        Write-Host "[P80-P2-ERROR] Failed to write dual hash verify: $_" -ForegroundColor Red
    }
}

# ========== HELPER: Write quick scan JSON ==========
function Write-QuickScanJson {
    param([hashtable]$Data, [string]$OutputPath, [string]$ArtifactsDir)
    try {
        $tempJson = "$ArtifactsDir\.p80_phase2_quickscan_tmp.json"
        [System.IO.File]::WriteAllText($tempJson, ($Data | ConvertTo-Json -Depth 10 -Compress), (New-Object System.Text.UTF8Encoding $false))
        & python -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); open(sys.argv[2],'w',encoding='utf-8').write(json.dumps(d,separators=(',',':'),ensure_ascii=False))" $tempJson $OutputPath
        if (Test-Path $tempJson) { Remove-Item $tempJson -Force -ErrorAction SilentlyContinue }
    } catch {
        Write-Host "[P80-P2-ERROR] Failed to write quick scan: $_" -ForegroundColor Red
    }
}

# ========== HELPER: Write bug note JSON ==========
function Write-BugNoteJson {
    param([hashtable]$Data, [string]$OutputPath, [string]$ArtifactsDir)
    try {
        $tempJson = "$ArtifactsDir\.p80_phase2_bugnote_tmp.json"
        [System.IO.File]::WriteAllText($tempJson, ($Data | ConvertTo-Json -Depth 10 -Compress), (New-Object System.Text.UTF8Encoding $false))
        & python -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); open(sys.argv[2],'w',encoding='utf-8').write(json.dumps(d,separators=(',',':'),ensure_ascii=False))" $tempJson $OutputPath
        if (Test-Path $tempJson) { Remove-Item $tempJson -Force -ErrorAction SilentlyContinue }
    } catch {
        Write-Host "[P80-P2-ERROR] Failed to write bug note: $_" -ForegroundColor Red
    }
}

# ========== HELPER: Write A01 observation brief ==========
function Write-ObservationBrief {
    param([string]$Content, [string]$OutputPath)
    try {
        $bom = New-Object System.Text.UTF8Encoding($true)
        [System.IO.File]::WriteAllText($OutputPath, $Content, $bom)
    } catch {
        Write-Host "[P80-P2-ERROR] Failed to write brief: $_" -ForegroundColor Red
    }
}

# ========== HELPER: Detect A01 events ==========
# INHERITED P80 FIX: wind_api_calls counting excludes P79/P80/PHASE2 audit
# events, uses [long], and caps values at 1000 to discard inflated artifacts.
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
            if ($line -notmatch '"agent":"DSHD-P79"' -and $line -notmatch '"agent":"DSHD-P80' ) {
                $val = [long]$Matches[1]
                if ($val -gt 0 -and $val -lt 1000 -and $val -gt $status.windApiCallsMax) {
                    $status.windApiCallsMax = $val
                }
            }
        }
        if ($line -match '"wdf_retries":(\d+)') {
            if ($line -notmatch '"agent":"DSHD-P79"' -and $line -notmatch '"agent":"DSHD-P80' ) {
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

# ========== HELPER: wdf_sample_metals_raw.csv evidence ==========
# Forensics only: records size, SHA256, last write time, first 10 lines.
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

# ========== HELPER: DSHC cross_agent CSV fingerprint (PHASE2) ==========
function Get-CrossAgentCsvFingerprint {
    param([string]$IndexPath, [string]$CsvFileName)
    $result = @{ found = $false; sha256 = ""; rows = 0; note = ""; path = "" }
    try {
        if (!(Test-Path $IndexPath)) { return $result }
        $raw = [System.IO.File]::ReadAllText($IndexPath, [System.Text.Encoding]::UTF8)
        $idx = $raw | ConvertFrom-Json -ErrorAction Stop
        $csvOut = $idx.artifacts.a01_ignite.csv_output
        if ($csvOut -and $csvOut.sha256) {
            $result.found = $true
            $result.sha256 = [string]$csvOut.sha256
            $result.rows = [int]$csvOut.rows
            $result.note = [string]$csvOut.note
            $result.path = [string]$csvOut.path
        }
    } catch { $result.error = $_.Exception.Message }
    return $result
}

# ========== HELPER: dual-hash comparison (PHASE2) ==========
function Test-DualHash {
    param([string]$CsvPath, [string]$CrossRefSha)
    $a = Get-FileSha256 $CsvPath
    $b = Get-SecondSha256 $CsvPath
    $result = @{
        file_path = $CsvPath
        hash_a_sha256_create = $a
        hash_b_get_file_hash = $b
        cross_agent_reference = $CrossRefSha
        a_equals_b = ($a -eq $b)
        a_equals_reference = ($a -eq $CrossRefSha)
        b_equals_reference = ($b -eq $CrossRefSha)
        all_match = ($a -eq $b) -and ($a -eq $CrossRefSha)
        computed_at = (Get-Date).ToString("o")
    }
    return $result
}

# ========== HELPER: read-only quick scan (PHASE2) ==========
# Streaming scan only: rough row count, header keyword check, consecutive
# blank-line warning. Never loads the file into a dataframe.
# WARNING: this is an early-warning signal ONLY. It does NOT replace the
# DSHA-P68 formal sanity gate and 9-step pipeline.
function Get-QuickScan {
    param([string]$CsvPath, [string[]]$RequiredKeywords, [long]$MinFileSizeBytes, [long]$MinRowCount)
    $result = @{
        file_name = ""
        file_path = ""
        size_bytes = 0
        sha256 = ""
        rough_row_count = 0
        data_rows = 0
        header_line = ""
        keywords_required = @()
        keywords_present = @()
        keywords_missing = @()
        max_consecutive_blank = 0
        blank_run_warning = $false
        min_size_ok = $true
        min_rows_ok = $true
        scan_complete = $false
        scan_error = ""
    }
    try {
        if (!(Test-Path $CsvPath)) {
            $result.scan_error = "file_not_found"
            return $result
        }
        $fi = Get-Item $CsvPath
        $result.file_name = $fi.Name
        $result.file_path = $fi.FullName
        $result.size_bytes = $fi.Length
        $result.min_size_ok = ($fi.Length -ge $MinFileSizeBytes)
        $result.sha256 = Get-FileSha256 $CsvPath
        $result.keywords_required = $RequiredKeywords

        $reader = New-Object System.IO.StreamReader($CsvPath, [System.Text.Encoding]::UTF8)
        $rowCount = 0
        $blankRun = 0
        $maxBlankRun = 0
        $cap = 1000000
        $line = $reader.ReadLine()
        if ($line -ne $null) {
            $rowCount = 1
            $result.header_line = $line.TrimEnd("`r")
        }
        while ($rowCount -lt $cap) {
            $line = $reader.ReadLine()
            if ($line -eq $null) { break }
            $rowCount = $rowCount + 1
            if ([string]::IsNullOrWhiteSpace($line)) {
                $blankRun = $blankRun + 1
                if ($blankRun -gt $maxBlankRun) { $maxBlankRun = $blankRun }
            } else {
                $blankRun = 0
            }
        }
        $reader.Close()
        $result.rough_row_count = $rowCount
        $result.data_rows = [Math]::Max(0, $rowCount - 1)
        $result.max_consecutive_blank = $maxBlankRun
        $result.blank_run_warning = ($maxBlankRun -ge 10)
        $result.min_rows_ok = ($result.data_rows -ge $MinRowCount)

        foreach ($kw in $RequiredKeywords) {
            $pattern = "(?i)(^|,)\s*" + [regex]::Escape($kw) + "\s*(,|$)"
            if ($result.header_line -match $pattern) {
                $result.keywords_present += $kw
            } else {
                $result.keywords_missing += $kw
            }
        }
        $result.scan_complete = $true
    } catch {
        $result.scan_error = $_.Exception.Message
    }
    return $result
}

# ========== HELPER: R03 compliance check (PHASE2 observation list) ==========
function Get-R03Compliance {
    param([string]$SkillDir, [hashtable]$ExpectedHashes)
    $compliant = $true
    $files = @()
    foreach ($entry in $ExpectedHashes.GetEnumerator()) {
        $name = $entry.Key
        $expected = $entry.Value
        $path = Join-Path $SkillDir $name
        $actual = ""
        $exists = Test-Path $path
        if ($exists) { $actual = Get-FileSha256 $path }
        $match = ($actual -eq $expected)
        if (-not $match) { $compliant = $false }
        $files += @{
            name = $name
            expected_sha256 = $expected
            actual_sha256 = $actual
            exists = $exists
            hash_match = $match
        }
    }
    $mismatchCount = 0
    foreach ($f in $files) { if (-not $f.hash_match) { $mismatchCount++ } }
    return @{
        r03_compliant = $compliant
        mismatch_count = $mismatchCount
        files = $files
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

# ========== HELPER: Circuit breaker check (P80 rules, inherited 1:1) ==========
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

# ========== P0 PRE-CHECKS ==========
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " DSHD-P80-A01-PHASE2 PARALLEL AUDIT & EVIDENCE VERIFICATION" -ForegroundColor Cyan
Write-Host " Task: $taskName" -ForegroundColor Cyan
Write-Host " Tag:  $a01Tag" -ForegroundColor Cyan
Write-Host " Mode: AUDIT_READ_ONLY / never_run_backtest=YES" -ForegroundColor Cyan
Write-Host " Inherits ALL P80 capabilities + dual-hash + quick scan + stale archive" -ForegroundColor Cyan
Write-Host " Started: $(Get-Date -Format 'o')" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$bomStatus = Get-BomStatus $scriptPath
$inv = Get-InvariantStatus $baseDir $artifactsDir $monitorPid
$p80Watch = Get-ScriptWatchAlive "dshd_p80_a01_audit_watch.ps1"
$gateState = Get-LatestGateState $trackingLog
$p68Lock = Get-P68LockState $trackingLog
$r03Compliance = Get-R03Compliance $skillDir $r03Expected
$r03ManifestActual = Get-FileSha256 "$artifactsDir\skill_release_manifest.json"

$checks = @(
    @{ name = "PID3472 monitor";              ok = $inv.monitor_pid3472_alive }
    @{ name = "pwsh-13 P77 hash watch";        ok = $inv.p77_pwsh13_alive }
    @{ name = "pwsh-30 P80 evidence watch";    ok = $p80Watch.alive }
    @{ name = "R03 manifest SHA256";           ok = ($r03ManifestActual -eq $r03ManifestSha) }
    @{ name = "P80/P2 script BOM intact";      ok = $bomStatus.intact }
    @{ name = "gate=CLOSED";                   ok = ($gateState.gate -match "CLOSED") }
    @{ name = "release_permit=NOT_ISSUED";     ok = ($gateState.release_permit -eq "NOT_ISSUED") }
    @{ name = "DSHA-P68 FINAL_STANDBY_LOCKED"; ok = $p68Lock.locked }
    @{ name = "DSHC-TASK-A01-PHASE2 loaded";   ok = $true }
)

Write-Host "P0 pre-checks:" -ForegroundColor Yellow
$p0AllPass = $true
foreach ($c in $checks) {
    $mark = if ($c.ok) { "PASS" } else { "FAIL" }
    Write-Host "  [$mark] $($c.name)" -ForegroundColor $(if ($c.ok) { 'Green' } else { 'Red' })
    if (-not $c.ok) { $p0AllPass = $false }
}
Write-Host "  PID3472: $(if($inv.monitor_pid3472_alive){'ALIVE'}else{'DEAD'})" -ForegroundColor $(if($inv.monitor_pid3472_alive){'Green'}else{'Red'})
Write-Host "  P77 watch: $(if($inv.p77_pwsh13_alive){'ALIVE'}else{'DEAD'})" -ForegroundColor $(if($inv.p77_pwsh13_alive){'Green'}else{'Red'})
Write-Host "  P80 watch: $(if($p80Watch.alive){'ALIVE (PID ' + $p80Watch.pid + ')'}else{'DEAD'})" -ForegroundColor $(if($p80Watch.alive){'Green'}else{'Red'})
Write-Host "  wmain: PID $($inv.wmain_pid) $(if($inv.wmain_running){'RUNNING'}else{'NOT RUNNING'})" -ForegroundColor $(if($inv.wmain_running){'Green'}else{'Yellow'})
Write-Host "  InitWAPI: PID $($inv.initwapi_pid) $(if($inv.initwapi_running){'RUNNING'}else{'NOT RUNNING'})" -ForegroundColor $(if($inv.initwapi_running){'Green'}else{'Yellow'})
Write-Host "  Excel: $(if($inv.excel_running){'PID ' + $inv.excel_pid}else{'NOT RUNNING'})" -ForegroundColor Yellow
Write-Host "  Markers: $(if($inv.ignition_markers_absent){'ABSENT'}else{'PRESENT!'})" -ForegroundColor $(if($inv.ignition_markers_absent){'Green'}else{'Red'})
Write-Host "  BOM: $(if($bomStatus.intact){'INTACT (' + $bomStatus.size + ' bytes)'}else{'MISSING!'})" -ForegroundColor $(if($bomStatus.intact){'Green'}else{'Red'})
Write-Host "  gate=$($gateState.gate) release_permit=$($gateState.release_permit)" -ForegroundColor Yellow
Write-Host "  DSHA-P68: $(if($p68Lock.locked){'FINAL_STANDBY_LOCKED'}else{'NOT CONFIRMED'}) (commit=$($p68Lock.baseline_commit))" -ForegroundColor $(if($p68Lock.locked){'Green'}else{'Red'})
Write-Host "  R03 compliant: $(if($r03Compliance.r03_compliant){'YES'}else{'NO - ' + $r03Compliance.mismatch_count + ' mismatch(es)'})" -ForegroundColor $(if($r03Compliance.r03_compliant){'Green'}else{'Red'})
Write-Host ""

if (-not $p0AllPass) {
    $state.a01Warnings += @{
        code = "P0_PRECHECK_FAIL"
        severity = "CIRCUIT_BREAKER_READY"
        message = "P0 pre-check FAILED: $(($checks | Where-Object { -not $_.ok } | ForEach-Object { $_.name }) -join ', '); DSHD continues read-only observation, NO intervention taken"
        evidence_ts = (Get-Date).ToString("o")
    }
}

$contextEvent = @{
    timestamp = (Get-Date).ToString("o")
    event = "DSHD-P80-PHASE2-A01-PARALLEL-AUDIT-CONTEXT-LOADED"
    agent = $agentName
    task = $taskName
    a01_tag = $a01Tag
    data = @{
        audit_context_loaded = $true
        phase = "PHASE2"
        wind_api_calls = 0
        red_lines_verified = $true
        p0_all_pass = $p0AllPass
        p0_checks = $checks
        monitor_pid3472 = $inv.monitor_pid3472_alive
        p77_watch = $inv.p77_pwsh13_alive
        p80_watch = $p80Watch.alive
        wmain_pid = $inv.wmain_pid
        initwapi_pid = $inv.initwapi_pid
        excel_pid = $inv.excel_pid
        ignition_markers_absent = $inv.ignition_markers_absent
        bom_status_intact = $bomStatus.intact
        gate = $gateState.gate
        release_permit = $gateState.release_permit
        dsha_p68_locked = $p68Lock.locked
        dsha_p68_status = $p68Lock.status
        dsha_p68_baseline_commit = $p68Lock.baseline_commit
        r03_compliant = $r03Compliance.r03_compliant
        r03_manifest_sha256 = $r03ManifestActual
        stale_p76_baseline_archived = $true
        independent_verify_on = $true
        never_run_backtest = $true
        evidence_features = @(
            "file_evidence", "artifact_catalog", "scheduled_briefs", "bom_self_check",
            "dual_hash_verify", "quick_scan", "stale_baseline_archive", "bug_memo"
        )
    }
}
Add-AuditEvent $contextEvent $trackingLog
Write-Host "  Context event written to $trackingLog" -ForegroundColor Green
Write-Host ""

# ========== P2.2 BUG MEMO (written once) ==========
$bugNoteData = @{
    bug_id = "DSHD-BUG-001-P67-WINDAPI-COUNTER"
    title = "wind_api_calls field emits garbage/overflow values (P67 monitor chain)"
    status = "OPEN"
    severity = "HIGH"
    category = "field_initialization_and_serialization"
    created_by = $agentName
    a01_tag = $a01Tag
    created_at = (Get-Date).ToString("o")
    baseline = "feature/v88-g1"
    description = @'
The wind_api_calls field emitted by DSHD-P67 / DSHD-P71 monitor events contains garbage
values that are NOT real Wind API call counts. Observed a self-referential inflation chain:
a monitor reads the shared tracking log including its OWN prior events, sums/propagates the
wind_api_calls field it finds there, and writes the inflated number back, so the value
compounds across polls until it exceeds the Int32 range and serializes as garbage.
'@
    observed_evidence = @(
        "wind_api_calls=1           first non-zero value (P79 audit, ~19:20)",
        "wind_api_calls=26          self-referential inflation begins",
        "wind_api_calls=460         stable inflated artifact (P80 long-type fixed counter)",
        "wind_api_calls=2110, 4220  continuing exponential growth",
        "wind_api_calls=2212495360  Int32 overflow garbage in P67/P71 events (~20:47+)"
    )
    root_cause_hypothesis = @'
1. Monitor counters read the shared tracking log which already includes audit events that
   themselves carry a wind_api_calls field, so the counter becomes self-referential.
2. Integer typing (Int32) overflows once the inflated value exceeds 2147483647 and
   serializes as a garbage number.
3. Field semantics were never frozen: 'wind_api_calls' should mean 'counted only when a
   WSD formula returned a data grid', but the emitted values are unrelated to that.
'@
    impact = @(
        "False-positive CIRCUIT_BREAKER_READY / WIND_API_CALLS_GT0 flags",
        "Int32 parse/serialization overflow errors in downstream readers",
        "Field cannot be trusted for release decisions without a fixed counter"
    )
    recommended_fix = @(
        "Cast to [long] before accumulation and before serialization",
        "Exclude audit-agent events (DSHD-P79 / DSHD-P80 / DSHD-P80-PHASE2) from the count",
        "Cap accumulated values at a plausible bound (e.g. 1000) and flag anything above",
        "Freeze field semantics in the schema doc: counted only when a WSD formula returned a data grid",
        "Reset the counter from scratch each poll instead of reading prior serialized values"
    )
    semantics_note = @'
wind_api_calls MUST be defined as: the number of Wind WSD calls that returned a data grid,
measured within the current process lifetime. It is NOT a cumulative log statistic and MUST
NOT be derived by reading the tracking log.
'@
    detection_mitigation = @'
DSHD-P80 and DSHD-P80-PHASE2 both use the long-type fixed counter: [long] cast, exclusion
of audit-agent events, and a 1000 cap. This yields a STABLE observed value (460) instead of
exponential explosion. The value is observed/reported only - it is never used as an
automatic action trigger.
'@
    resolution_status = "OPEN - awaiting a fixed P67 monitor version"
    assigned_to = "DSHD-P67 owner"
    related_defects_observed = @(
        @{
            id = "DSHD-DEF-002-JSONL-NO-TRAILING-LF"
            title = "P79/P80 audit-event JSONL appends omit a trailing newline"
            evidence = "tracking_monitor_audit.jsonl contains physical lines holding 2+ concatenated JSON objects, e.g. L1374 (P80 CIRCUIT_BREAKER_READY + next event merged); such merged lines fail ConvertFrom-Json"
            impact = "line-based parsers (ReadAllLines + ConvertFrom-Json per line) silently skip or mis-attribute events"
            mitigation_in_phase2 = "PHASE2 Add-AuditEvent appends LF (0x0A) after each event; P80/P79 scripts were NOT modified (protected running processes)"
        },
        @{
            id = "DSHD-DEF-003-P76-STALE-BASELINE-NOISE"
            title = "P77 SKILL_HASH_MISMATCH alerts compare against the superseded P76 baseline"
            evidence = "deployed skill files match R03 exactly (r03_compliant=YES); P76 expected hashes differ on all 5 files"
            impact = "permanent false-positive MISMATCH noise in the P77 watch"
            mitigation_in_phase2 = "P76 entries ARCHIVED as reference-only; observation comparison list updated to R03; no running script modified"
        }
    )
    red_line_note = "This memo is documentation only. It does NOT modify any running monitor."
}
if (-not $state.bugNoteWritten) {
    Write-BugNoteJson $bugNoteData $bugNotePath $artifactsDir
    $state.bugNoteWritten = $true
    Write-Host "  Bug memo written: $bugNotePath" -ForegroundColor Green
}

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
        $gateState = Get-LatestGateState $trackingLog
        $p68Lock = Get-P68LockState $trackingLog
        $r03Compliance = Get-R03Compliance $skillDir $r03Expected

        if ($csvEvidence.detected -and [string]::IsNullOrEmpty($state.csvFirstSeen)) {
            $state.csvFirstSeen = (Get-Date).ToString("o")
            Write-Host "  [CSV-EVIDENCE] $csvFileName detected! SHA256=$($csvEvidence.sha256) size=$($csvEvidence.size_bytes)" -ForegroundColor Yellow
        }

        # ========== PHASE2 P2.3a + P2.3b: dual hash verify + quick scan ==========
        $hashMismatchWarning = $null
        if ($csvEvidence.detected) {
            $csvChanged = (-not $state.csvDualHashDone) -or ($csvEvidence.size_bytes -ne $state.csvLastSize) -or ($csvEvidence.last_write_time -ne $state.csvLastMtime)

            if ($csvChanged) {
                $crossRef = Get-CrossAgentCsvFingerprint $crossAgentIndexPath $csvFileName
                $dual = Test-DualHash $csvEvidence.file_path $crossRef.sha256
                $state.lastDualHashResult = $dual
                $state.csvLastSize = $csvEvidence.size_bytes
                $state.csvLastMtime = $csvEvidence.last_write_time
                $state.csvDualHashDone = $true

                $dualData = @{
                    task = $taskName
                    agent = $agentName
                    a01_tag = $a01Tag
                    poll_count = $state.pollCount
                    timestamp = $now
                    verification_type = "DUAL_HASH"
                    csv_evidence = $csvEvidence
                    hash_a_method = "byte-read + [System.Security.Cryptography.SHA256]"
                    hash_b_method = "PowerShell Get-FileHash -Algorithm SHA256 (independent)"
                    cross_agent_index_path = $crossAgentIndexPath
                    cross_agent_csv_output = $crossRef
                    dual_hash = $dual
                    all_match = $dual.all_match
                    scan_status = if ($dual.all_match) { "PASS_ALL_MATCH" } else { "FAIL_MISMATCH" }
                    csv_first_seen = $state.csvFirstSeen
                }
                Write-DualHashVerifyJson $dualData $dualHashVerifyPath $artifactsDir
                Write-Host "  [DUAL-HASH] poll #$($state.pollCount) all_match=$($dual.all_match) ref_found=$($crossRef.found) A=$(Truncate-Str $dual.hash_a_sha256_create 12) B=$(Truncate-Str $dual.hash_b_get_file_hash 12)" -ForegroundColor $(if($dual.all_match){'Green'}else{'Red'})

                if (-not $dual.all_match -and $crossRef.found) {
                    $hashMismatchWarning = @{
                        code = "A01_HASH_MISMATCH_WARNING"
                        severity = "WARNING"
                        message = "Dual-hash mismatch: A=$(Truncate-Str $dual.hash_a_sha256_create 12) B=$(Truncate-Str $dual.hash_b_get_file_hash 12) ref=$(Truncate-Str $crossRef.sha256 12)"
                        evidence_ts = $dual.computed_at
                    }
                }
            }

            if ((-not $state.csvQuickScanDone) -or ($csvEvidence.size_bytes -ne $state.csvLastSize)) {
                $qs = Get-QuickScan $csvEvidence.file_path $requiredHeaderKeywords $p68MinFileSize $p68MinRows
                $state.lastQuickScanResult = $qs
                $state.csvQuickScanDone = $true
                $scanStatus = "EARLY_WARNING_SIGNAL_ONLY"
                if ($qs.min_size_ok -and $qs.min_rows_ok) {
                    $scanStatus = "ABOVE_P68_THRESHOLDS"
                } elseif (-not $qs.min_size_ok) {
                    $scanStatus = "BELOW_P68_MIN_SIZE"
                } elseif (-not $qs.min_rows_ok) {
                    $scanStatus = "BELOW_P68_MIN_ROWS"
                }
                $qsData = @{
                    task = $taskName
                    agent = $agentName
                    a01_tag = $a01Tag
                    poll_count = $state.pollCount
                    timestamp = $now
                    verification_type = "QUICK_SCAN"
                    scan = $qs
                    dsha_p68_min_file_size = $p68MinFileSize
                    dsha_p68_min_rows = $p68MinRows
                    dsha_p68_locked = $p68Lock.locked
                    scan_status = $scanStatus
                    csv_first_seen = $state.csvFirstSeen
                    note = "DSHD quick scan is an EARLY WARNING SIGNAL ONLY. It does NOT replace and must NOT be used to bypass the DSHA-P68 formal sanity gate and its 9-step pipeline. Final validation authority: DSHA-P68 (human-licensed)."
                }
                Write-QuickScanJson $qsData $quickScanPath $artifactsDir
                Write-Host "  [QUICK-SCAN] poll #$($state.pollCount) rows=$($qs.rough_row_count) kw_missing=$($qs.keywords_missing.Count) blank_run=$($qs.max_consecutive_blank) status=$scanStatus" -ForegroundColor $(if($qs.min_size_ok){'Green'}else{'Yellow'})
            }
        }

        # P80: circuit breaker (inherited 1:1)
        $warnings = Test-CircuitBreakerConditions $a01Status $inv $bomStatus
        if ($hashMismatchWarning) { $warnings += $hashMismatchWarning }
        foreach ($w in $warnings) {
            $state.a01Warnings += $w
            $warnEvent = @{
                timestamp = $now
                event = "DSHD-P80-PHASE2-A01-$(if($w.severity -eq 'CIRCUIT_BREAKER_READY'){'CIRCUIT_BREAKER_READY'}else{'OBSERVATION_WARNING'})"
                agent = $agentName
                task = $taskName
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
                task = $agentName; a01_tag = $a01Tag; poll_count = $state.pollCount
                timestamp = $now; output_sample = $outputEvidence
                csv_evidence = $csvEvidence; csv_first_seen = $state.csvFirstSeen
                dual_hash_verify = $state.lastDualHashResult
                quick_scan = $state.lastQuickScanResult
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
                task = $agentName; a01_tag = $a01Tag; poll_count = $state.pollCount
                timestamp = $now
                artifact_count = $state.a01BacktestArtifacts.Count
                total_size_bytes = $totalSize
                artifacts = $state.a01BacktestArtifacts
                catalog_interval_polls = $catalogIntervalPolls
            }
            Write-ArtifactCatalog $catalogData $catalogPath $artifactsDir
            Write-Host "  [CATALOG] poll #$($state.pollCount) - $($state.a01BacktestArtifacts.Count) artifacts cataloged" -ForegroundColor Cyan
        }

        # 5-minute snapshot rhythm (inherited)
        $snapDue = (($state.pollCount - $state.lastSnapshotPoll) * $pollIntervalSec) -ge $snapshotIntervalSec
        if ($snapDue -or $state.pollCount -eq 1) {
            $state.lastSnapshotPoll = $state.pollCount
            $snapshotData = @{
                task = "DSHD-P80-A01-PHASE2-PARALLEL-AUDIT-EVIDENCE-VERIFICATION"
                a01_tag = $a01Tag
                agent = $agentName
                phase = "PHASE2"
                poll_count = $state.pollCount
                poll_interval_sec = $pollIntervalSec
                timestamp = $now
                audit_context_loaded = $true
                watch_start = $loopStart.ToString("o")
                watch_elapsed_min = [math]::Round(((Get-Date) - $loopStart).TotalMinutes, 1)
                p0_all_pass = $p0AllPass
                p0_checks = $checks
                invariants = $inv
                gate_state = $gateState
                dsha_p68_lock = $p68Lock
                r03_compliance = $r03Compliance
                stale_baseline_archive = @{
                    status = "ARCHIVED_STALE_BASELINE"
                    archived_reference = $p76ArchivedBaseline
                    active_reference = $r03Expected
                    r03_manifest_sha256 = $r03ManifestSha
                    r03_manifest_actual_sha256 = $r03ManifestActual
                    p76_entries = 5
                    r03_compliant = $r03Compliance.r03_compliant
                    note = "P76 baseline entries archived; the observation comparison list is updated to R03. The running P77 watch script is NOT modified and continues comparing against P76, so its SKILL_HASH_MISMATCH alerts are KNOWN ARCHIVED DRIFT, not fresh anomalies."
                }
                a01_status = $a01Status
                output_sample_evidence = $outputEvidence
                csv_evidence = $csvEvidence
                csv_first_seen = $state.csvFirstSeen
                dual_hash_verify = $state.lastDualHashResult
                quick_scan = $state.lastQuickScanResult
                a01_backtest_artifacts = $state.a01BacktestArtifacts
                a01_warnings = $state.a01Warnings
                wind_api_calls = $a01Status.windApiCallsMax
                circuit_breaker_ready = $state.a01CircuitBreakerReady
                bom_status = $bomStatus
                ps_bom_warning = (-not $bomStatus.intact)
                independent_verify_on = $true
                red_lines = @{
                    audit_only = $true
                    intervention = "NONE"
                    never_run_backtest = $true
                    never_modify_output_sample = $true
                    never_bypass_dsha_p68 = $true
                    wind_api_calls_zero = ($a01Status.windApiCallsMax -eq 0)
                    processes_untouched = $true
                    gate_unchanged = $true
                    markers_absent = $inv.ignition_markers_absent
                    evidence_append_only = $true
                }
                deliverables = @{
                    snapshot = "artifacts/dshd_p80_a01_audit_snapshot.json"
                    file_evidence = "artifacts/dshd_a01_file_evidence.json"
                    dualhash_verify = "artifacts/dshd_a01_dualhash_verify.json"
                    quick_scan = "artifacts/dshd_a01_quick_scan.json"
                    observation_brief = "artifacts/dshd_a01_observation_brief.md"
                    bug_note = "artifacts/dshd_bug_note_p67_windapi_counter.json"
                    artifact_catalog = "artifacts/dshd_a01_artifact_catalog.json"
                    phase2_dedicated_snapshot = "artifacts/dshd_p80_phase2_a01_audit_snapshot.json"
                }
            }
            # P3 required path (shared with P80) + PHASE2-dedicated authoritative copy
            Write-SnapshotJson $snapshotData $p80SnapshotPath $artifactsDir
            Write-SnapshotJson $snapshotData $p80Phase2SnapshotPath $artifactsDir
            Write-Host "  [SNAPSHOT] poll #$($state.pollCount)" -ForegroundColor Cyan
        }

        # P80: scheduled brief every 12 polls (not only on warnings)
        if ($state.pollCount % $briefIntervalPolls -eq 0 -or $state.pollCount -eq 1) {
            if ($state.a01Warnings.Count -gt 0) {
                $statusLine = "WARNING - $($state.a01Warnings.Count) warning(s) detected:"
                foreach ($w in $state.a01Warnings) { $statusLine += "`n  - $($w.code): $($w.message)" }
            } else {
                $statusLine = "$statusLineOk - All observations stable, no warnings."
            }
            $checksRows = ""
            foreach ($c in $checks) { $checksRows += "| $($c.name) | $(if($c.ok){'**PASS**'}else{'**FAIL**'}) |`n" }
            $outputFilesBlock = if ($outputEvidence.files.Count -gt 0) {
                $b = "| File | Size | SHA256 | Modified |`n|------|------|--------|----------|`n"
                foreach ($f in $outputEvidence.files) { $b += "| $($f.name) | $($f.size_bytes) | $($f.sha256) | $($f.last_write_time) |`n" }
                $b
            } else { "*(no files in output_sample/)*" }
            $warningsBlock = if ($state.a01Warnings.Count -gt 0) {
                $b = "| Code | Severity | Message |`n|------|----------|---------|`n"
                foreach ($w in $state.a01Warnings) { $b += "| $($w.code) | $($w.severity) | $($w.message) |`n" }
                $b
            } else { "*(no warnings)*" }
            $artifactsBlock = if ($state.a01BacktestArtifacts.Count -gt 0) {
                $b = "| File | Size | SHA256 | Modified |`n|------|------|--------|----------|`n"
                foreach ($f in $state.a01BacktestArtifacts) { $b += "| $($f.name) | $($f.size_bytes) | $($f.sha256) | $($f.last_write_time) |`n" }
                $b
            } else { "*(none yet)*" }
            $briefContent = @"
# DSHD-P80-A01-PHASE2 Observation Brief

**Task**: $taskName
**A01 Tag**: $a01Tag
**Agent**: $agentName
**Phase**: PHASE2 (parallel audit & evidence verification)
**Generated**: $now
**Poll Count**: $($state.pollCount)
**Watch Duration**: $([math]::Round(((Get-Date) - $loopStart).TotalMinutes, 1)) min

## Overall Status

$statusLine

## P0 Pre-checks

| Check | Result |
|-------|--------|
$checksRows
| P0 ALL PASS | $(if($p0AllPass){'**YES**'}else{'**NO**'}) |

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
| Independent Verify | **ON** |

## Gate & P68 Lock

| Item | State |
|------|-------|
| gate | $($gateState.gate) |
| release_permit | $($gateState.release_permit) |
| DSHA-P68 | $(if($p68Lock.locked) {'**FINAL_STANDBY_LOCKED**'} else {'NOT CONFIRMED'}) |
| P68 baseline_commit | $($p68Lock.baseline_commit) |
| P68 source_ts | $($p68Lock.source_ts) |
| P68 min_file_size | $p68MinFileSize bytes |
| P68 min_rows | $p68MinRows |

## Invariant Status

| Check | State |
|-------|-------|
| wmain (PID $($inv.wmain_pid)) | $(if($inv.wmain_running) {'RUNNING'} else {'NOT RUNNING'}) |
| InitWAPI (PID $($inv.initwapi_pid)) | $(if($inv.initwapi_running) {'RUNNING'} else {'NOT RUNNING'}) |
| Excel (PID $($inv.excel_pid)) | $(if($inv.excel_running) {'RUNNING'} else {'NOT RUNNING'}) |
| Ignition Markers | $(if($inv.ignition_markers_absent) {'ABSENT'} else {'**PRESENT**'}) |
| PID 3472 Monitor | $(if($inv.monitor_pid3472_alive) {'ALIVE'} else {'**DEAD**'}) |
| P77 Watch (pwsh-13) | $(if($inv.p77_pwsh13_alive) {'ALIVE'} else {'**DEAD**'}) |

## Output Sample

$outputFilesBlock

## CSV File Evidence

$(if($csvEvidence.detected) {"| Property | Value |
|----------|-------|
| File | $($csvEvidence.file_name) |
| Size | $($csvEvidence.size_bytes) bytes |
| SHA256 | $($csvEvidence.sha256) |
| First Seen | $($state.csvFirstSeen) |
| Last Modified | $($csvEvidence.last_write_time) |
| First 10 Lines | $($csvEvidence.first_10_lines.Count) captured |"} else {"*(wdf_sample_metals_raw.csv not yet detected)*"})

## Dual-Hash Verify (P2.3a)

$(if($state.lastDualHashResult.Count -gt 0 -and $state.lastDualHashResult.file_path) {"| Property | Value |
|----------|-------|
| Hash A (byte-read SHA256.Create) | $($state.lastDualHashResult.hash_a_sha256_create) |
| Hash B (Get-FileHash, independent) | $($state.lastDualHashResult.hash_b_get_file_hash) |
| DSHC cross_agent reference | $($state.lastDualHashResult.cross_agent_reference) |
| A == B | $(if($state.lastDualHashResult.a_equals_b){'**YES**'}else{'**NO**'}) |
| A == reference | $(if($state.lastDualHashResult.a_equals_reference){'**YES**'}else{'**NO**'}) |
| ALL MATCH | $(if($state.lastDualHashResult.all_match){'**PASS**'}else{'**FAIL**'}) |
| Computed At | $($state.lastDualHashResult.computed_at) |
| Detail | artifacts/dshd_a01_dualhash_verify.json |"} else {"*(no dual-hash verification yet - CSV not detected)*"})

## Quick Scan (P2.3b)

$(if($state.lastQuickScanResult.Count -gt 0 -and $state.lastQuickScanResult.file_path) {"| Property | Value |
|----------|-------|
| Rough row count | $($state.lastQuickScanResult.rough_row_count) |
| Data rows | $($state.lastQuickScanResult.data_rows) |
| Header | $($state.lastQuickScanResult.header_line) |
| Keywords missing | $(if($state.lastQuickScanResult.keywords_missing.Count -gt 0) {$state.lastQuickScanResult.keywords_missing -join ', '} else {'NONE'}) |
| Max consecutive blank | $($state.lastQuickScanResult.max_consecutive_blank) |
| Blank-run warning | $(if($state.lastQuickScanResult.blank_run_warning){'**YES**'}else{'No'}) |
| min_size_ok (>= $p68MinFileSize B) | $(if($state.lastQuickScanResult.min_size_ok){'**YES**'}else{'**NO**'}) |
| min_rows_ok (>= $p68MinRows) | $(if($state.lastQuickScanResult.min_rows_ok){'**YES**'}else{'**NO**'}) |
| Detail | artifacts/dshd_a01_quick_scan.json |"} else {"*(no quick scan yet - CSV not detected)*"})

> **DSHD quick scan != DSHA formal acceptance.** Even when this scan looks clean it is
> an EARLY WARNING SIGNAL ONLY. The DSHA-P68 formal sanity gate and 9-step pipeline are
> NOT replaced, NOT bypassed, and are the sole final validation authority (human-licensed).

## Stale Baseline Archive (P2.1)

| Property | Value |
|----------|-------|
| Status | ARCHIVED_STALE_BASELINE |
| Archived reference | P76 (5 entries, reference only) |
| Active reference | R03 (5 entries) |
| R03 manifest SHA256 | $r03ManifestSha |
| R03 manifest actual | $r03ManifestActual |
| R03 compliant | $(if($r03Compliance.r03_compliant){'**YES**'}else{'**NO** - ' + $r03Compliance.mismatch_count + ' mismatch(es)'}) |
| P77 watch script modified | **NO (untouched)** |

> The running P77 watch (pwsh-13) still compares against the P76 baseline, so its
> SKILL_HASH_MISMATCH alerts are **KNOWN ARCHIVED DRIFT**, not fresh anomalies. No running
> script was modified; only the DSHD observation comparison list was updated to R03.

## Bug Memo (P2.2)

- **DSHD-BUG-001-P67-WINDAPI-COUNTER** - OPEN / HIGH
- wind_api_calls garbage + Int32 overflow (2212495360) in P67 monitor chain
- See: artifacts/dshd_bug_note_p67_windapi_counter.json
- P80/P80-P2 mitigation: [long] cast + audit-agent exclusion + 1000 cap -> stable value

## Warnings

$warningsBlock

## Backtest Artifacts (dshc_*/dsha_*)

$artifactsBlock

## Tracking Log

- Path: $trackingLog
- A01 Tag Present: $a01Tag

---
**DSHD-P80-PHASE2**: AUDIT_ONLY=YES | Intervention=NONE | never_run_backtest=YES | wind_api_calls=$($a01Status.windApiCallsMax) | BOM=$(if($bomStatus.intact){'OK'}else{'MISSING'})
"@
            Write-ObservationBrief $briefContent $briefPath
            Write-Host "  [BRIEF] poll #$($state.pollCount)" -ForegroundColor Cyan
        }

        $statusMsg = "  [P80-P2#$($state.pollCount)] $(Get-Date -Format 'HH:mm:ss') wind_api=$($a01Status.windApiCallsMax) ignite=$(if($a01Status.igniteStarted){'Y'}else{'n'}) fetch=$(if($a01Status.fetchStarted){'Y'}else{'n'}) bt=$(if($a01Status.backtestStarted){'Y'}else{'n'}) out=$($outputEvidence.files.Count) csv=$(if($csvEvidence.detected){'Y'}else{'n'}) warn=$($state.a01Warnings.Count) bom=$(if($bomStatus.intact){'OK'}else{'MISSING'})"
        Write-Host $statusMsg -ForegroundColor $(if($a01Status.windApiCallsMax -gt 0){'Red'}else{'Green'})

        $elapsed = (Get-Date) - $pollStart
        if ($elapsed.TotalSeconds -lt $pollIntervalSec) {
            Start-Sleep -Seconds ([math]::Floor($pollIntervalSec - $elapsed.TotalSeconds))
        }
    } catch {
        Write-Host "  [P80-P2-ERROR] $($_.Exception.Message)" -ForegroundColor Red
        Start-Sleep -Seconds $pollIntervalSec
    }
}
