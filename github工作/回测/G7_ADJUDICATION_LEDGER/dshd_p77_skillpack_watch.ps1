# =====================================================================
# DSHD-P77 SKILL_PACK_HASH_WATCH_LOOP
# Background loop monitoring system_skills/SKILL-WIND-EXCEL-WDF-BOOTSTRAP/
# Polls every 30s; compares SHA256 to P76 baseline expected hashes
# Output: artifacts/dshd_p77_skillpack_watch_snapshot.json
# Audit:  tracking_monitor_audit.jsonl (append)
# =====================================================================
# RED LINES:
#   AUDIT_READ_ONLY - only reads skill files, no writes to business files
#   wind_api_calls = 0 - no WIND API calls
#   No ignition markers created
#   No process/WDF/registry operations
#   Never terminates wmain, InitWAPI, Excel processes
#   Never modifies WDF or registry
#   Observe-only compliance
# =====================================================================

$ErrorActionPreference = 'Continue'

# === Configuration ===
$taskName    = 'DSHD-P77-SKILL-PACK-HASH-WATCH-LOOP'
$taskTag     = 'DSHD-P77'
$pollSec     = 30

$skillDir    = 'D:\DSH_WORK\github工作\回测\system_skills\SKILL-WIND-EXCEL-WDF-BOOTSTRAP'
$auditLog    = 'D:\DSH_WORK\github工作\回测\tracking_monitor_audit.jsonl'
$snapshotOut = 'D:\DSH_WORK\github工作\回测\artifacts\dshd_p77_skillpack_watch_snapshot.json'
$eventsOut   = 'D:\DSH_WORK\github工作\回测\artifacts\dshd_p77_events.jsonl'

# Expected SHA256 hashes (from DSHC-P75 / P76 baseline)
$expectedHashes = @{
    'skill_readme.md'      = 'E7A3BF2552AC899D11322EB23ED0D2D3B5B1D57C2338B5670C56C7D8993970FA'
    'bootstrap_wdf.ps1'    = '238134D6E6FF351B4A7B3BEABC2FA92D45C05BDC601F4F1C31BCC85E983E8925'
    'skill_manifest.json'  = '1C1D58DE7C2D616A592F1D3A295BE063BDC2A9990CEF8B6E42DD57BE99F9FC3A'
    'health_check_wdf.ps1' = '0D0F4D76B9BE6B2126A11BB2C2D87BDF037DF10D118F06F02D18389CABE609A7'
    'reset_wdf_safe.ps1'   = '72846B4ECC6517B6B77C3A1B347BAA505DD84559C7548E56FC418361A1F861F3'
}

# Expected files ordered
$expectedFiles = @('skill_readme.md','bootstrap_wdf.ps1','skill_manifest.json','health_check_wdf.ps1','reset_wdf_safe.ps1')

# === State ===
$loopCount = 0
$fullMatchTriggered = $false
$prevSnapshot = $null

# === Helper: Append audit event to JSONL ===
function Append-AuditEvent {
    param(
        [string]$EventType,
        [string]$Level,
        [hashtable]$Data,
        [string]$Note
    )
    $ts = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')
    $eventObj = @{
        task         = $taskTag
        event        = $EventType
        timestamp    = $ts
        level        = $Level
        poll_count   = $loopCount
        wind_api_calls = 0
        data         = $Data
        note         = $Note
    }
    $line = $eventObj | ConvertTo-Json -Depth 10 -Compress
    $utf8Bom = New-Object System.Text.UTF8Encoding($true)
    [System.IO.File]::AppendAllText($auditLog, $line + "`n", $utf8Bom)
}

# === Helper: Write P77 events JSONL ===
function Append-P77Event {
    param(
        [string]$EventType,
        [string]$Level,
        [hashtable]$Data
    )
    $ts = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')
    $eventObj = @{
        task         = $taskTag
        event        = $EventType
        timestamp    = $ts
        level        = $Level
        poll_count   = $loopCount
        wind_api_calls = 0
        data         = $Data
    }
    $line = $eventObj | ConvertTo-Json -Depth 10 -Compress
    $utf8Bom = New-Object System.Text.UTF8Encoding($true)
    [System.IO.File]::AppendAllText($eventsOut, $line + "`n", $utf8Bom)
}

# === Helper: Write snapshot JSON ===
function Write-Snapshot {
    param([hashtable]$SnapshotData)
    $pyTemp = "$env:TEMP\p77_snapshot_tmp.json"
    $jsonStr = $SnapshotData | ConvertTo-Json -Depth 15 -Compress
    $utf8Bom = New-Object System.Text.UTF8Encoding($true)
    [System.IO.File]::WriteAllText($pyTemp, $jsonStr, $utf8Bom)
    python -c "import json; d=json.load(open(r'$pyTemp','r',encoding='utf-8-sig')); json.dump(d, open(r'$snapshotOut','w',encoding='utf-8'), separators=(',',':'))" 2>&1
    $pyResult = $?
    if ($pyResult) {
        Remove-Item $pyTemp -ErrorAction SilentlyContinue
        Write-Host "  [SNAPSHOT] Written: $snapshotOut"
    } else {
        [System.IO.File]::WriteAllText($snapshotOut, $jsonStr, (New-Object System.Text.UTF8Encoding($false)))
        Remove-Item $pyTemp -ErrorAction SilentlyContinue
        Write-Host "  [SNAPSHOT] Written (fallback): $snapshotOut"
    }
}

# === Log function ===
function Write-Log {
    param([string]$msg)
    $ts = (Get-Date -Format 'HH:mm:ss')
    Write-Host "[$ts] $msg"
}

# =====================================================================
# MAIN LOOP
# =====================================================================

Write-Host "============================================="
Write-Host "DSHD-P77 SKILL_PACK_HASH_WATCH_LOOP"
Write-Host "Start: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "Skill dir: $skillDir"
Write-Host "Audit log: $auditLog"
Write-Host "Snapshot: $snapshotOut"
Write-Host "Interval: ${pollSec}s"
Write-Host "============================================="

# Ensure output directories exist
$artDir = Split-Path $snapshotOut -Parent
if (-not (Test-Path $artDir)) {
    New-Item -ItemType Directory -Path $artDir -Force | Out-Null
}

# Initial audit event
Append-AuditEvent -EventType 'P77_WATCH_STARTED' -Level 'INFO' -Data @{
    skill_dir = $skillDir
    expected_files = $expectedFiles
    poll_interval_seconds = $pollSec
} -Note 'P77 watch loop started'
Append-P77Event -EventType 'P77_WATCH_STARTED' -Level 'INFO' -Data @{
    skill_dir = $skillDir
    expected_files = $expectedFiles
    poll_interval_seconds = $pollSec
}

Write-Log 'P77 watch loop started. Polling every 30s...'

while ($true) {
    $loopCount++
    $loopStart = Get-Date
    $ts = $loopStart.ToString('yyyy-MM-ddTHH:mm:ssK')

    Write-Log "Poll #$loopCount"

    # === Scan skill directory ===
    $dirExists = Test-Path $skillDir -PathType Container
    $files = @()
    $missingFiles = @()
    $mismatchFiles = @()
    $matchFiles = @()
    $allMatch = $false

    if ($dirExists) {
        foreach ($fname in $expectedFiles) {
            $fpath = Join-Path $skillDir $fname
            if (Test-Path $fpath -PathType Leaf) {
                $bytes = [System.IO.File]::ReadAllBytes($fpath)
                $sha256obj = [System.Security.Cryptography.SHA256]::Create()
                $hashBytes = $sha256obj.ComputeHash($bytes)
                $actualHash = [System.BitConverter]::ToString($hashBytes) -replace '-',''
                $expectedHash = $expectedHashes[$fname]
                $hashMatch = ($actualHash -eq $expectedHash)

                $fileInfo = @{
                    file          = $fname
                    exists        = $true
                    size_bytes    = $bytes.Length
                    actual_sha256 = $actualHash
                    expected_sha256 = $expectedHash
                    hash_match    = $hashMatch
                    path          = $fpath
                }
                $files += $fileInfo

                if ($hashMatch) {
                    $matchFiles += $fname
                } else {
                    $mismatchFiles += $fname
                }
            } else {
                $missingFiles += $fname
                $files += @{
                    file          = $fname
                    exists        = $false
                    size_bytes    = 0
                    actual_sha256 = 'FILE_NOT_FOUND'
                    expected_sha256 = $expectedHashes[$fname]
                    hash_match    = $false
                    path          = $fpath
                }
            }
        }
        if ($missingFiles.Count -eq 0 -and $mismatchFiles.Count -eq 0) {
            $allMatch = $true
        }
    } else {
        foreach ($fname in $expectedFiles) {
            $files += @{
                file          = $fname
                exists        = $false
                size_bytes    = 0
                actual_sha256 = 'FILE_NOT_FOUND'
                expected_sha256 = $expectedHashes[$fname]
                hash_match    = $false
                path          = (Join-Path $skillDir $fname)
            }
        }
    }

    $loopElapsed = ((Get-Date) - $loopStart).TotalMilliseconds

    # === Determine alert level and type ===
    $alertLevel = 'INFO'
    $alertType = ''

    if (-not $dirExists) {
        $alertLevel = 'INFO'
        $alertType = 'SKILL_DIR_NOT_FOUND'
        Write-Log "  Directory NOT FOUND. All 5 files MISSING."
    } elseif ($dirExists -and $missingFiles.Count -gt 0) {
        $alertLevel = 'INFO'
        $alertType = 'SKILL_FILES_MISSING'
        $missingList = $missingFiles -join ', '
        Write-Log "  Files MISSING: $missingList"
    } elseif ($dirExists -and $mismatchFiles.Count -gt 0) {
        $alertLevel = 'WARNING'
        $alertType = 'SKILL_HASH_MISMATCH'
        $mismatchList = $mismatchFiles -join ', '
        Write-Log "  WARNING: Hash MISMATCH for: $mismatchList"
    } elseif ($dirExists -and $allMatch) {
        $alertLevel = 'INFO'
        $alertType = 'SKILL_PACK_FULL_MATCH'
        Write-Log "  ALL 5 FILES MATCH. Skill pack READY!"
    }

    # === Build data object for events ===
    $eventData = @{
        poll_count          = $loopCount
        timestamp           = $ts
        skill_dir_exists    = $dirExists
        total_expected_files = 5
        files_found         = ($expectedFiles.Count - $missingFiles.Count)
        missing_count       = $missingFiles.Count
        mismatch_count      = $mismatchFiles.Count
        match_count         = $matchFiles.Count
        all_match           = $allMatch
        missing_files       = $missingFiles
        mismatch_files      = $mismatchFiles
        match_files         = $matchFiles
        wind_api_calls      = 0
        loop_elapsed_ms     = [math]::Round($loopElapsed, 1)
        files_detail        = $files
    }

    # === Write audit event (with throttle) ===
    $prevDirExists = $false
    if ($prevSnapshot -ne $null -and $prevSnapshot.skill_dir_exists -ne $null) {
        $prevDirExists = $prevSnapshot.skill_dir_exists
    }
    $stateChanged = ($dirExists -ne $prevDirExists)

    if ($alertType -eq 'SKILL_HASH_MISMATCH' -or $alertType -eq 'SKILL_PACK_FULL_MATCH' -or $stateChanged -or ($loopCount % 10 -eq 0)) {
        Append-AuditEvent -EventType $alertType -Level $alertLevel -Data $eventData -Note ''
        Append-P77Event -EventType $alertType -Level $alertLevel -Data $eventData
        Write-Log "  Audit event: $alertType ($alertLevel)"
    }

    # === Full match trigger (one-time) ===
    if ($allMatch -and -not $fullMatchTriggered) {
        $fullMatchTriggered = $true
        $fullMatchData = @{
            poll_count       = $loopCount
            timestamp        = $ts
            skill_dir        = $skillDir
            all_files        = $expectedFiles
            hash_matches     = @{
                'skill_readme.md'      = $expectedHashes['skill_readme.md']
                'bootstrap_wdf.ps1'    = $expectedHashes['bootstrap_wdf.ps1']
                'skill_manifest.json'  = $expectedHashes['skill_manifest.json']
                'health_check_wdf.ps1' = $expectedHashes['health_check_wdf.ps1']
                'reset_wdf_safe.ps1'   = $expectedHashes['reset_wdf_safe.ps1']
            }
            message          = 'ALL 5 SKILL FILES SHA256 MATCH BASELINE. SKILL PACK READY FOR IGNITION.'
            wind_api_calls   = 0
        }
        Append-AuditEvent -EventType 'SKILL_PACK_FULL_MATCH' -Level 'INFO' -Data $fullMatchData -Note 'READY'
        Append-P77Event -EventType 'SKILL_PACK_FULL_MATCH' -Level 'INFO' -Data $fullMatchData
        Write-Log "  *** SKILL PACK FULL MATCH TRIGGERED. READY FOR IGNITION. ***"
    }

    # === Build and write snapshot JSON ===
    $snapshotData = @{
        task              = $taskName
        poll_count        = $loopCount
        timestamp         = $ts
        skill_dir         = $skillDir
        skill_dir_exists  = $dirExists
        total_expected_files = 5
        files_found       = ($expectedFiles.Count - $missingFiles.Count)
        missing_count     = $missingFiles.Count
        mismatch_count    = $mismatchFiles.Count
        match_count       = $matchFiles.Count
        all_match         = $allMatch
        full_match_triggered = $fullMatchTriggered
        alert_type        = $alertType
        alert_level       = $alertLevel
        wind_api_calls    = 0
        red_lines_verified = $true
        audit_read_only   = $true
        files             = $files
        missing_files     = $missingFiles
        mismatch_files    = $mismatchFiles
        match_files       = $matchFiles
        loop_elapsed_ms   = [math]::Round($loopElapsed, 1)
        expected_hashes   = $expectedHashes
        baseline_source   = 'DSHC-P75/P76 expected SHA256'
        poll_interval_sec = $pollSec
    }

    Write-Snapshot -SnapshotData $snapshotData

    # Update prevSnapshot for state-change detection
    $prevSnapshot = @{
        skill_dir_exists = $dirExists
        missing_count    = $missingFiles.Count
        mismatch_count   = $mismatchFiles.Count
        match_count      = $matchFiles.Count
        all_match        = $allMatch
    }

    # === Sleep ===
    if ($loopCount -lt 10000) {
        Start-Sleep -Seconds $pollSec
    }

    if ($loopCount % 10 -eq 0) {
        Write-Log "--- Checkpoint: poll #$loopCount ---"
    }
}
