#requires -Version 5.1
# Smoke test for DSHD-P81-TWEAK. Dot-sources the constant+function head of the
# regenerated script (everything before the main loop), then exercises the four
# TWEAK tasks against the live files. Read-only: opens nothing for write.
$ErrorActionPreference = 'Continue'
$scriptPath = Join-Path $PSScriptRoot 'dshd_p81_watch.ps1'
$src = [System.IO.File]::ReadAllText($scriptPath, [System.Text.Encoding]::UTF8)
$idx = $src.IndexOf('# ---------------- MAIN LOOP')
if ($idx -lt 0) { Write-Host "FATAL: main-loop marker not found"; exit 1 }
$head = $src.Substring(0, $idx)
Invoke-Expression $head

$fail = 0
function Check($label, $cond) {
  if ($cond) { Write-Host ("  PASS  {0}" -f $label) }
  else { Write-Host ("  FAIL  {0}" -f $label); $script:fail = $script:fail + 1 }
}

Write-Host ("LOADED version={0} tweakToken={1} tweakTask={2} monitoredPaths={3}" -f $scriptVersion, $tweakTokenName, $tweakTaskName, $monitoredPaths.Count)
$skillHits = @($monitoredPaths | Where-Object { $_.p -like ('*' + [char]92 + 'skill_lib*' + [char]92 + 'factor_v1*') })
Write-Host ("SKILL_MONITORED_PATHS={0} (owner={1})" -f $skillHits.Count, (@($skillHits | Select-Object -First 1).owner))
Check 'monitoredPaths grew from 19 to 25' ($monitoredPaths.Count -eq 25)
Check '6 skill files monitored' ($skillHits.Count -eq 6)
Check 'all skill paths owner=DSHC-SKILL-FACTOR01' (@($skillHits | Where-Object { $_.owner -ne 'DSHC-SKILL-FACTOR01' }).Count -eq 0)

Write-Host ""
Write-Host "=== TASK 1: quick_scan row-count convention ==="
$qs = Get-QuickScan $csvPath
$lt = Get-LongTableAudit $csvPath
Write-Host ("  qs.data_rows(V2)={0} qs.data_rows_legacy_header_inclusive={1} qs.header_line_count={2} qs.data_rows_convention={3}" -f $qs.data_rows, $qs.data_rows_legacy_header_inclusive, $qs.header_line_count, $qs.data_rows_convention)
Write-Host ("  lt.data_rows={0}" -f $lt.data_rows)
Check 'convention is DATA_ONLY_V2' ($qs.data_rows_convention -eq 'DATA_ONLY_V2')
Check 'V2 == long_table_audit rows (7362)' ($qs.data_rows -eq $lt.data_rows)
Check 'legacy header-inclusive == V2 + 1' ($qs.data_rows_legacy_header_inclusive -eq ($qs.data_rows + 1))
Check 'header_line_count == 1' ($qs.header_line_count -eq 1)

Write-Host ""
Write-Host "=== TASK 2a: P49 post-seal mutation detector ==="
$p49a = Get-P49Audit $null
Write-Host ("  cold_start={0} sealed={1} sealed_at={2} manifest_status={3}" -f $p49a.cold_start, $p49a.manifest_sealed, $p49a.manifest_sealed_at, $p49a.manifest_status)
Write-Host ("  post_seal_mutation={0} alert={1} kinds=[{2}] undeclared=[{3}]" -f $p49a.post_seal_mutation, $p49a.post_seal_archive_modify_alert, ($p49a.post_seal_mutation_kinds -join ','), ($p49a.unexpected_files -join ','))
Write-Host ("  audit_status={0}" -f $p49a.audit_status)
Check 'manifest sealed detected' ($p49a.manifest_sealed -eq $true)
Check 'post-seal alert raised' ($p49a.post_seal_archive_modify_alert -eq $true)
Check 'kinds contains ADDED_UNDECLARED' (@($p49a.post_seal_mutation_kinds) -contains 'ADDED_UNDECLARED')
Check '5 undeclared artifacts' ($p49a.unexpected_files.Count -eq 5)
Check 'audit_status == P49_POSTSEAL_MUTATION' ($p49a.audit_status -eq 'P49_POSTSEAL_MUTATION')
$p49b = Get-P49Audit $p49a.state_snapshot
Write-Host ("  --- pass 2 --- cold_start={0} added=[{1}] modified=[{2}] removed=[{3}] alert={4} kinds=[{5}]" -f $p49b.cold_start, ($p49b.added_files -join ','), ($p49b.hash_changed_files -join ','), ($p49b.removed_files -join ','), $p49b.post_seal_archive_modify_alert, ($p49b.post_seal_mutation_kinds -join ','))
Check 'pass2 has no spurious added' ($p49b.added_files.Count -eq 0)
Check 'pass2 has no spurious modified' ($p49b.hash_changed_files.Count -eq 0)
Check 'pass2 has no spurious removed' ($p49b.removed_files.Count -eq 0)
Check 'alert persists across polls' ($p49b.post_seal_archive_modify_alert -eq $true)

Write-Host ""
Write-Host "=== TASK 2b: skill dir hash monitor ==="
$sk = Get-SkillDirAudit $null
Write-Host ("  exists={0} files={1} bytes={2} manifest_readable={3} cold_start={4}" -f $sk.exists, $sk.file_count, $sk.total_bytes, $sk.manifest_readable, $sk.cold_start)
Write-Host ("  skill_id={0} version={1} version_locked={2} status={3}" -f $sk.skill_id, $sk.version, $sk.version_locked, $sk.status)
Write-Host ("  manifest_sha256={0}" -f $sk.manifest_sha256)
Write-Host ("  declared_count={0} undeclared=[{1}]" -f $sk.declared_count, ($sk.undeclared_files -join ','))
Write-Host ("  constraint wind_api_calls={0} offline_only={1} f01_locked={2} f01_ver={3}" -f $sk.constraint_wind_api_calls, $sk.constraint_offline_only, $sk.constraint_f01_script_locked, $sk.constraint_f01_script_version)
Write-Host ("  manifest data_integrity.original_csv_sha256=[{0}]" -f $sk.data_integrity_original_sha256)
Write-Host ("  manifest data_integrity.aligned_csv_rows={0}" -f $sk.data_integrity_aligned_rows)
Write-Host ("  actual raw CSV sha256=[{0}]" -f $sk.original_csv_sha256_actual)
Write-Host ("  original_csv_sha256_match={0}" -f $sk.original_csv_sha256_match)
Write-Host ("  v1_frozen_violation={0} snapshot_entries={1} audit_status={2}" -f $sk.v1_frozen_violation, $sk.state_snapshot.Count, $sk.audit_status)
Check 'skill dir exists' ($sk.exists -eq $true)
Check '17 files inventoried' ($sk.file_count -eq 17)
Check 'skill_id == FACTOR_EXTRACT_V1' ($sk.skill_id -eq 'FACTOR_EXTRACT_V1')
Check 'version == 1.0.0' ($sk.version -eq '1.0.0')
Check 'version_locked == true' ($sk.version_locked -eq $true)
Check 'status == VERSION_LOCKED' ($sk.status -eq 'VERSION_LOCKED')
Check 'manifest hash captured (64 hex)' ($sk.manifest_sha256 -match '^[0-9A-F]{64}$')
Check '4 declared files' ($sk.declared_count -eq 4)
Check '13 undeclared files' ($sk.undeclared_files.Count -eq 13)
Check 'no declared file missing' ($sk.declared_missing_files.Count -eq 0)
Check 'constraints: wind_api_calls == 0' ($sk.constraint_wind_api_calls -eq 0)
Check 'constraints: offline_only == true' ($sk.constraint_offline_only -eq $true)
Check 'f01_script_locked == true' ($sk.constraint_f01_script_locked -eq $true)
Check 'data_integrity.original_csv_sha256 populated' ($sk.data_integrity_original_sha256.Length -eq 64)
Check 'data_integrity.aligned_csv_rows == 7362' ($sk.data_integrity_aligned_rows -eq 7362)
Check 'aligned_csv_rows matches long_table rows' ($sk.data_integrity_aligned_rows -eq $lt.data_rows)
Check 'manifest-declared CSV sha256 matches actual file' ($sk.original_csv_sha256_match -eq $true)
Check 'no V1 frozen violation' ($sk.v1_frozen_violation -eq $false)
Check 'cold start -> SKILL_BASELINE_ESTABLISHED' ($sk.audit_status -eq 'SKILL_BASELINE_ESTABLISHED')
$sk2 = Get-SkillDirAudit $sk.state_snapshot
Write-Host ("  --- pass 2 --- cold_start={0} added=[{1}] modified=[{2}] removed=[{3}] manifest_hash_changed={4} version_changed={5} status={6}" -f $sk2.cold_start, ($sk2.added_files -join ','), ($sk2.modified_files -join ','), ($sk2.removed_files -join ','), $sk2.manifest_hash_changed, $sk2.skill_version_changed, $sk2.audit_status)
Check 'pass2 no spurious added' ($sk2.added_files.Count -eq 0)
Check 'pass2 no spurious modified' ($sk2.modified_files.Count -eq 0)
Check 'pass2 no spurious removed' ($sk2.removed_files.Count -eq 0)
Check 'pass2 no manifest hash change' ($sk2.manifest_hash_changed -eq $false)
Check 'pass2 no version change' ($sk2.skill_version_changed -eq $false)

Write-Host ""
Write-Host "=== TASK 4: exchange binding auto-clear contract ==="
$at = Get-ExchangeAttributionAudit
Write-Host ("  auto_clear_enabled={0} mismatch_count={1}" -f $at.auto_clear_enabled, $at.mismatch_count)
Write-Host ("  lc_shf_verdict={0} (expected_exchange={1})" -f $at.lc_shf_verdict, $at.lc_shf_expected_exchange)
Write-Host ("  lc_gfe_verdict={0} (expected_exchange={1})" -f $at.lc_gfe_verdict, $at.lc_gfe_expected_exchange)
Write-Host ("  lc_binding_repaired={0} lc_repaired_via=[{1}]" -f $at.lc_binding_repaired, $at.lc_repaired_via)
Check 'auto_clear_enabled == true' ($at.auto_clear_enabled -eq $true)
Check 'LC.SHF still MISMATCH' ($at.lc_shf_verdict -eq 'MISMATCH')
Check 'LC.SHF expected exchange is GFE' ($at.lc_shf_expected_exchange -eq 'GFE')
Check 'LC.GFE BOUND_OK' ($at.lc_gfe_verdict -eq 'BOUND_OK')
Check 'LC.GFE expected exchange is GFE' ($at.lc_gfe_expected_exchange -eq 'GFE')
Check 'binding not yet repaired (LC.SHF still bad)' ($at.lc_binding_repaired -eq $false)
Check '1 mismatch counted (LC.SHF)' ($at.mismatch_count -eq 1)
foreach ($s in @('SI.GFE','PS.GFE','LC.DCE')) {
  $b = Test-ExchangeBinding $s
  Write-Host ("  BIND {0,-8} expected={1,-5} actual={2,-5} verdict={3}" -f $s, $b.expected_exchange, $b.actual_exchange, $b.verdict)
}

Write-Host ""
Write-Host "=== brief renderer wiring + full render ==="
$ri = $src.IndexOf('function Write-ClusterBrief')
Write-Host ("  indexOf(function Write-ClusterBrief)={0}; src_len={1}; head_len={2}" -f $ri, $src.Length, ([string]$head).Length)
$pnames = @()
if ($ri -gt 0) {
  $seg = $src.Substring($ri, 700)
  $pi = $seg.IndexOf('param(')
  if ($pi -gt 0) {
    $tail = $seg.Substring($pi)
    $lnEnd = $tail.IndexOf("`n")
    if ($lnEnd -gt 0) { $pline = $tail.Substring(0, $lnEnd) } else { $pline = $tail }
  }
  Write-Host ("  param_line={0}" -f $pline)
  $pnames = @([regex]::Matches([string]$pline, '\$([A-Za-z_][A-Za-z0-9_]*)') | ForEach-Object { $_.Groups[1].Value })
}
Write-Host ("  params({0})=[{1}]" -f $pnames.Count, ($pnames -join ','))
Check 'Write-ClusterBrief param line located' ($ri -gt 0)
Check 'Write-ClusterBrief accepts $SkillAudit' ($pnames -contains 'SkillAudit')
Check 'Write-ClusterBrief has 15 params' ($pnames.Count -eq 15)

$ts = Get-Date
$trackState = Get-TrackingState $auditLog
$snaps = @(Get-ExcelSnapshot $ts)
$excelRule = Test-ExcelSpawnRule $snaps
$agents = Get-ClusterAgents $trackState $excelRule 1 $ts
$territoryState = Get-TerritoryState $monitoredPaths $null
$dualHash = Get-DualHash $csvPath
$redLines = Get-RedLineStatus $trackState $trackState.wind_api_calls
$warnList = @(
  @{code = 'P49-001-ARTIFACT-UNEXPECTED'; severity = 'YELLOW'; ts = $ts.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = 'smoke-test synthetic post-seal alert'}
  @{code = 'EXCH-001-ATTRIBUTED-MISMATCH'; severity = 'YELLOW'; ts = $ts.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = 'smoke-test synthetic LC.SHF mismatch'}
)
$brief = Write-ClusterBrief $ts $agents $excelRule $territoryState $dualHash $qs $warnList @{p0_all=$true} 1 1 $redLines $lt $at $p49a $sk
$bl = [string]$brief
Write-Host ("  brief_len={0} chars" -f $bl.Length)
Check 'brief renders without error' ($bl.Length -gt 0)
Check 'brief contains skill section head' ($bl -match 'FACTOR_EXTRACT_V1')
Check 'brief shows skill version 1.0.0' ($bl -match '1\.0\.0')
Check 'brief shows skill audit status' ($bl -match $sk.audit_status)
Check 'brief shows manifest sha256' ($bl -match $sk.manifest_sha256.Substring(0,16))
Check 'brief shows csv sha match verdict' ($bl -match ([string]$sk.original_csv_sha256_match))
Check 'brief keeps P0 section' ($bl -match 'P0')
$huizh = [string][char]0x7EA2 + [char]0x7EBF
$huizc = [string][char]0x4EA4 + [char]0x6613 + [char]0x6240
Check 'brief keeps red-line section' ($bl -match $huizh)
Check 'brief keeps exchange section' ($bl -match $huizc)
Check 'brief keeps P49 section' ($bl -match 'P49')
$en = [char]0x3001
$headCnt = ([regex]::Matches($bl, [regex]::Escape($en))).Count
Write-Host ("  section_head_marker_count={0} (expect 10)" -f $headCnt)
Check 'all 10 section heads present' ($headCnt -eq 10)

Write-Host ""
Write-Host ("RESULT fails={0}" -f $fail)
if ($fail -gt 0) { exit 1 } else { exit 0 }
