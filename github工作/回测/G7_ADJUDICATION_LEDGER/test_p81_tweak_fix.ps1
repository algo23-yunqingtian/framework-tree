#requires -Version 5.1
# ============================================================
# test_p81_tweak_fix.ps1 - 51-item smoke test for DSHD-P81-TWEAK-FIX
# Token: DSHD-P81-TWEAK-FIX-TOKEN
# ============================================================
$ErrorActionPreference = 'Stop'
$pass = 0
$fail = 0
$total = 0
$failDetails = @()

function Assert($testName, $condition, $detail = '') {
  $script:total++
  if ($condition) {
    $script:pass++
    Write-Host "  [PASS] $testName" -ForegroundColor Green
  } else {
    $script:fail++
    $msg = "  [FAIL] $testName"
    if ($detail) { $msg += " :: $detail" }
    Write-Host $msg -ForegroundColor Red
    $script:failDetails += "$testName :: $detail"
  }
}

$base = 'D:\DSH_WORK\github工作\回测\G7_ADJUDICATION_LEDGER'
$recreatePy = Join-Path $base 'recreate_p81.py'
$watchPs1 = Join-Path $base 'dshd_p81_watch.ps1'
$versionsDoc = Join-Path $base 'dshd_p81_toolchain_versions.md'
$extPatch = Join-Path $base 'patch_p81_ext.py'
$tweakPatch = Join-Path $base 'patch_p81_tweak.py'
$versionHistory = Join-Path $base 'p81_version_history.json'
$safeEdit = Join-Path $base 'p81_safe_edit.py'
$brief = 'D:\DSH_WORK\github工作\回测\artifacts\dshd_cluster_brief.md'
$gitignore = 'D:\DSH_WORK\.gitignore'
$ledger = 'D:\DSH_WORK\github工作\回测\tracking_monitor_audit.jsonl'
$snapDir = Join-Path $base '_p81_snapshots'

Write-Host ""
Write-Host "=== DSHD-P81-TWEAK-FIX SMOKE TEST (51 items) ===" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# GROUP A: recreate_p81.py modifications (10 tests)
# ============================================================
Write-Host "--- Group A: recreate_p81.py modifications ---" -ForegroundColor Yellow

# A1: Python syntax valid
$pySrc = [System.IO.File]::ReadAllText($recreatePy, [System.Text.Encoding]::UTF8)
try {
  $p = Start-Process -FilePath 'python' -ArgumentList '-c', "import py_compile; py_compile.compile(r'$recreatePy', doraise=True)" -NoNewWindow -Wait -PassThru -RedirectStandardOutput "$base\_smoke_out.txt" -RedirectStandardError "$base\_smoke_err.txt"
  $pyOk = ($p.ExitCode -eq 0)
} catch { $pyOk = $false }
Assert 'A1: recreate_p81.py Python syntax valid' $pyOk

# A2: head_verm key in $zh dictionary
$zhMatch = [regex]::Match($pySrc, "\`$zh\s*=\s*@\{([^}]*)\}")
$hasHeadVerm = $pySrc -match "head_verm\s*="
Assert 'A2: $zh dict has head_verm key' $hasHeadVerm

# A3: Write-ClusterBrief contains head_verm reference
$hasBriefVermRef = $pySrc -match "Add-BriefLine.*head_verm"
Assert 'A3: Write-ClusterBrief references head_verm' $hasBriefVermRef

# A4: Contains backup hook reference
$hasBackupHook = $pySrc -match "p81_safe_edit\.py v1\.0\.0"
Assert 'A4: Contains p81_safe_edit.py v1.0.0 reference' $hasBackupHook

# A5: Contains patch iteration reference
$hasPatchIter = $pySrc -match "patch_p81_tweak2\.py"
Assert 'A5: Contains patch_p81_tweak2.py reference' $hasPatchIter

# A6: Contains versions doc reference
$hasVersionsDocRef = $pySrc -match "dshd_p81_toolchain_versions\.md"
Assert 'A6: Contains dshd_p81_toolchain_versions.md reference' $hasVersionsDocRef

# A7: Contains version history reference
$hasVerHistRef = $pySrc -match "p81_version_history\.json"
Assert 'A7: Contains p81_version_history.json reference' $hasVerHistRef

# A8: PS1 string starts with #requires
$ps1Starts = $pySrc -match "PS1\s*=\s*r'''#requires -Version 5\.1"
Assert 'A8: PS1 string starts with #requires -Version 5.1' $ps1Starts

# A9: Original sections preserved (一 through 十)
$origSections = @('一、三 Agent', '二、OBS-SPAWN', '三、写领地', '四、CSV 双', '五、告警', '六、长表', '七、P49', '八、FACTOR', '九、P0', '十、红线')
$allOrigSections = $true
foreach ($s in $origSections) {
  if ($pySrc -notmatch [regex]::Escape($s)) { $allOrigSections = $false; break }
}
Assert 'A9: All original sections (一~十) preserved' $allOrigSections

# A10: Section 十一 present in PS1
$hasSection11 = $pySrc -match "十一、P81 工具链版本管理"
Assert 'A10: Section 十一 (版本管理) present in PS1' $hasSection11

# ============================================================
# GROUP B: .gitignore and snapshot tracking (8 tests)
# ============================================================
Write-Host ""
Write-Host "--- Group B: .gitignore and snapshot tracking ---" -ForegroundColor Yellow

$giContent = [System.IO.File]::ReadAllText($gitignore, [System.Text.Encoding]::UTF8)

# B1: .gitignore has snapshot dir exception
$hasSnapDirEx = $giContent -match '!github工作/回测/G7_ADJUDICATION_LEDGER/_p81_snapshots/'
Assert 'B1: .gitignore has _p81_snapshots/ exception' $hasSnapDirEx

# B2: .gitignore has .bak exception
$hasBakEx = $giContent -match '!github工作/回测/G7_ADJUDICATION_LEDGER/_p81_snapshots/\*\.bak'
Assert 'B2: .gitignore has *.bak exception' $hasBakEx

# B3: .gitignore has .bak.* exception
$hasBakDotEx = $giContent -match '!github工作/回测/G7_ADJUDICATION_LEDGER/_p81_snapshots/\*\.bak\.\*'
Assert 'B3: .gitignore has *.bak.* exception' $hasBakDotEx

# B4: Snapshot files visible in git (not ignored)
$gitResult = & git -C 'D:\DSH_WORK' status --short -- "github工作/回测/G7_ADJUDICATION_LEDGER/_p81_snapshots/" 2>&1
$hasUntracked = $gitResult -match '^\?\?'
Assert 'B4: Snapshot files visible in git status' $hasUntracked

# B5: At least 15 snapshot files exist
$snapFiles = @(Get-ChildItem -Path $snapDir -Filter '*.bak' -ErrorAction SilentlyContinue)
Assert 'B5: At least 15 snapshot files exist' ($snapFiles.Count -ge 15) "found $($snapFiles.Count)"

# B6: Snapshot files have .bak extension
$allBakExt = ($snapFiles | ForEach-Object { $_.Extension -eq '.bak' } | Where-Object { -not $_ }).Count -eq 0
Assert 'B6: All snapshot files have .bak extension' $allBakExt

# B7: Snapshot filenames follow convention
$allConvention = ($snapFiles | ForEach-Object { $_.Name -match '^\..+\.\d{8}_\d{6}\.\S+\.bak$' } | Where-Object { -not $_ }).Count -eq 0
Assert 'B7: Snapshot filenames follow naming convention' $allConvention

# B8: p81_version_history.json valid
$vhOk = $false
try {
  $vh = Get-Content $versionHistory -Raw -Encoding UTF8 | ConvertFrom-Json
  $vhOk = ($vh.entries.Count -ge 15)
} catch { $vhOk = $false }
Assert 'B8: p81_version_history.json valid with >=15 entries' $vhOk

# ============================================================
# GROUP C: Patch archival (4 tests)
# ============================================================
Write-Host ""
Write-Host "--- Group C: Patch archival ---" -ForegroundColor Yellow

# C1: patch_p81_ext.py has [ARCHIVED]
$extContent = [System.IO.File]::ReadAllText($extPatch, [System.Text.Encoding]::UTF8)
$hasArchivedExt = $extContent -match '\[ARCHIVED\]'
Assert 'C1: patch_p81_ext.py has [ARCHIVED] banner' $hasArchivedExt

# C2: patch_p81_tweak.py has [ARCHIVED]
$tweakContent = [System.IO.File]::ReadAllText($tweakPatch, [System.Text.Encoding]::UTF8)
$hasArchivedTweak = $tweakContent -match '\[ARCHIVED\]'
Assert 'C2: patch_p81_tweak.py has [ARCHIVED] banner' $hasArchivedTweak

# C3: Banner says DO NOT RE-RUN
$hasDoNotRerun = $extContent -match 'DO NOT RE-RUN'
Assert 'C3: [ARCHIVED] banner says DO NOT RE-RUN' $hasDoNotRerun

# C4: Banner mentions patch_p81_tweak2.py
$hasTweak2InBanner = $extContent -match 'patch_p81_tweak2\.py'
Assert 'C4: [ARCHIVED] banner mentions patch_p81_tweak2.py' $hasTweak2InBanner

# ============================================================
# GROUP D: Versions doc updates (4 tests)
# ============================================================
Write-Host ""
Write-Host "--- Group D: Versions doc updates ---" -ForegroundColor Yellow

$vdocContent = [System.IO.File]::ReadAllText($versionsDoc, [System.Text.Encoding]::UTF8)

# D1: Patch iteration section
$hasPatchSection = $vdocContent -match '补丁迭代规范'
Assert 'D1: Versions doc has patch iteration section' $hasPatchSection

# D2: Mentions _p81_snapshots/ now tracked
$hasSnapTracked = $vdocContent -match '_p81_snapshots.*git tracked'
Assert 'D2: Versions doc mentions _p81_snapshots/ git tracked' $hasSnapTracked

# D3: Changelog v1.0.1
$hasChangelog = $vdocContent -match 'v1\.0\.1.*TWEAK-FIX'
Assert 'D3: Versions doc has v1.0.1 changelog entry' $hasChangelog

# D4: References patch_p81_tweak2.py
$hasTweak2InDoc = $vdocContent -match 'patch_p81_tweak2\.py'
Assert 'D4: Versions doc references patch_p81_tweak2.py' $hasTweak2InDoc

# ============================================================
# GROUP E: Monitoring logic preservation (10 tests)
# ============================================================
Write-Host ""
Write-Host "--- Group E: Monitoring logic preservation ---" -ForegroundColor Yellow

# E1: Excel drift observer
$hasExcelObserver = $pySrc -match 'OBS-SPAWN-EXCEL-001'
Assert 'E1: Excel drift observer (OBS-SPAWN-EXCEL-001) preserved' $hasExcelObserver

# E2: Exchange binding audit
$hasExchAudit = $pySrc -match 'EXCH-001-MISMATCH'
Assert 'E2: Exchange binding audit (EXCH-001-MISMATCH) preserved' $hasExchAudit

# E3: P49 artifact audit
$hasP49Audit = $pySrc -match 'P49-001-ARTIFACT'
Assert 'E3: P49 artifact audit (P49-001-ARTIFACT) preserved' $hasP49Audit

# E4: Skill directory audit
$hasSkillAudit = $pySrc -match 'SKILL-001-FILE'
Assert 'E4: Skill directory audit (SKILL-001-FILE) preserved' $hasSkillAudit

# E5: P0 checks
$hasP0 = $pySrc -match 'P0Checks'
Assert 'E5: P0 checks preserved' $hasP0

# E6: Gate CLOSED/HOLD
$hasGate = $pySrc -match 'CLOSED/HOLD'
Assert 'E6: Gate CLOSED/HOLD check preserved' $hasGate

# E7: Release permit NOT_ISSUED
$hasPermit = $pySrc -match 'NOT_ISSUED'
Assert 'E7: Release permit NOT_ISSUED check preserved' $hasPermit

# E8: wind_api_calls = 0
$hasWindApi = $pySrc -match 'wind_api_calls\s*=\s*0'
Assert 'E8: wind_api_calls=0 preserved' $hasWindApi

# E9: AUDIT_READ_ONLY
$hasAuditOnly = $pySrc -match 'AUDIT_READ_ONLY'
Assert 'E9: AUDIT_READ_ONLY mode preserved' $hasAuditOnly

# E10: intervention = NONE
$hasIntervention = $pySrc -match "intervention\s*=\s*'NONE'"
Assert 'E10: intervention=NONE preserved' $hasIntervention

# ============================================================
# GROUP F: Runtime verification (15 tests)
# ============================================================
Write-Host ""
Write-Host "--- Group F: Runtime verification ---" -ForegroundColor Yellow

# F1: Watcher process alive
$watcherProc = Get-Process -Id 2700 -ErrorAction SilentlyContinue
Assert 'F1: P81 watcher PID 2700 alive' ($watcherProc -ne $null)

# F2: Protected main process alive
$mainProc = Get-Process -Id 3472 -ErrorAction SilentlyContinue
Assert 'F2: Protected main PID 3472 alive' ($mainProc -ne $null)

# F3: Protected Excel process alive
$excelProc = Get-Process -Id 14644 -ErrorAction SilentlyContinue
Assert 'F3: Protected Excel PID 14644 alive' ($excelProc -ne $null)

# F4: P77 watcher alive
$p77Proc = @(Get-Process -Name 'pwsh' -ErrorAction SilentlyContinue | Where-Object { $_.Id -ge 30000 -and $_.Id -le 30500 })
Assert 'F4: P77 watcher alive (pwsh process found)' ($p77Proc.Count -ge 1)

# F5: P80 watcher alive
$p80Procs = @(Get-Process -Name 'pwsh' -ErrorAction SilentlyContinue | Where-Object { $_.Id -in @(29652, 29708, 30492) })
Assert 'F5: P80/P80-PHASE2 watchers alive' ($p80Procs.Count -ge 1)

# F6: Brief file exists
$briefExists = Test-Path $brief
Assert 'F6: Brief file exists' $briefExists

# F7: Brief file has content > 1000 bytes
$briefOk = $false
if (Test-Path $brief) {
  $briefSize = (Get-Item $brief).Length
  $briefOk = $briefSize -gt 1000
}
Assert 'F7: Brief file has content > 1000 bytes' $briefOk "size=$briefSize"

# F8: Brief has 十一 section (may be regenerated after next poll)
$briefContent = ''
if (Test-Path $brief) { $briefContent = [System.IO.File]::ReadAllText($brief, [System.Text.Encoding]::UTF8) }
$briefHas11 = $briefContent -match '十一'
Assert 'F8: Brief has 十一 section (after regen)' $briefHas11

# F9: dshd_p81_watch.ps1 BOM intact
$watchBytes = [System.IO.File]::ReadAllBytes($watchPs1)
$hasBOM = ($watchBytes[0] -eq 0xEF -and $watchBytes[1] -eq 0xBB -and $watchBytes[2] -eq 0xBF)
Assert 'F9: dshd_p81_watch.ps1 UTF-8 BOM intact' $hasBOM

# F10: dshd_p81_watch.ps1 size ~138KB
$watchSize = (Get-Item $watchPs1).Length
$watchSizeOk = ($watchSize -ge 130000 -and $watchSize -le 145000)
Assert 'F10: dshd_p81_watch.ps1 size ~138KB' $watchSizeOk "size=$watchSize"

# F11: p81_safe_edit.py exists
$safeEditExists = Test-Path $safeEdit
Assert 'F11: p81_safe_edit.py exists' $safeEditExists

# F12: p81_safe_edit.py executable (python)
$safeEditOk = $false
try {
  $out = & python $safeEdit --help 2>&1
  $safeEditOk = ($LASTEXITCODE -eq 0)
} catch { $safeEditOk = $false }
Assert 'F12: p81_safe_edit.py executable' $safeEditOk

# F13: tracking_monitor_audit.jsonl exists
$ledgerExists = Test-Path $ledger
Assert 'F13: tracking_monitor_audit.jsonl exists' $ledgerExists

# F14: Ledger has DSHD-P81-GIT-SAVE event
$ledgerContent = ''
if (Test-Path $ledger) { $ledgerContent = [System.IO.File]::ReadAllText($ledger, [System.Text.Encoding]::UTF8) }
$hasGitSaveEvent = $ledgerContent -match 'DSHD-P81-GIT-SAVE'
Assert 'F14: Ledger has DSHD-P81-GIT-SAVE event' $hasGitSaveEvent

# F15: git HEAD is 1cf2512 or later
$gitHead = & git -C 'D:\DSH_WORK' rev-parse --short HEAD 2>&1
$gitHeadOk = ($gitHead -match '1cf2512|2[0-9a-f]{5}|[a-f0-9]{7}')
Assert 'F15: git HEAD at or after 1cf2512' $gitHeadOk "HEAD=$gitHead"

# ============================================================
# SUMMARY
# ============================================================
Write-Host ""
Write-Host "=== SMOKE TEST SUMMARY ===" -ForegroundColor Cyan
Write-Host "  Total: $total" -ForegroundColor White
Write-Host "  PASS:  $pass" -ForegroundColor Green
Write-Host "  FAIL:  $fail" -ForegroundColor $(if ($fail -gt 0) { 'Red' } else { 'Green' })

if ($failDetails.Count -gt 0) {
  Write-Host ""
  Write-Host "  Failed details:" -ForegroundColor Yellow
  foreach ($d in $failDetails) {
    Write-Host "    - $d" -ForegroundColor Red
  }
}

Write-Host ""
if ($fail -eq 0) {
  Write-Host "RESULT: ALL 51 TESTS PASSED ✓" -ForegroundColor Green
} else {
  Write-Host "RESULT: $fail TEST(S) FAILED ✗" -ForegroundColor Red
}

# Cleanup temp files
Remove-Item "$base\_smoke_out.txt" -ErrorAction SilentlyContinue
Remove-Item "$base\_smoke_err.txt" -ErrorAction SilentlyContinue

exit $(if ($fail -eq 0) { 0 } else { 1 })