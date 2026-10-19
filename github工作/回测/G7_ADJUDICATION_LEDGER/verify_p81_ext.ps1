#requires -Version 5.1
# Verify P81-EXT results after poll 1. Read-only.
$ErrorActionPreference = 'Continue'
$base = Join-Path (Split-Path $PSScriptRoot -Parent) ''
$ledger = Join-Path $base 'tracking_monitor_audit.jsonl'
$artDir = Join-Path $base 'artifacts'
$lines = [System.IO.File]::ReadAllLines($ledger, [System.Text.Encoding]::UTF8)

Write-Host "=== ledger: $($lines.Count) lines ==="
$p81 = 0
for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i] -match 'DSHD-P81') { $p81++ } }
Write-Host "  lines mentioning DSHD-P81: $p81"

Write-Host ""
Write-Host "=== last 3 DSHD-P81 events ==="
$c = 0
for ($i = $lines.Count - 1; $i -ge 0 -and $c -lt 3; $i--) {
  $l = $lines[$i]
  if ($l -notmatch 'DSHD-P81') { continue }
  try {
    $o = $l | ConvertFrom-Json
    Write-Host ("  line{0} [{1}] {2} type={3} poll={4}" -f ($i + 1), $o.timestamp, $o.event, $o.event_type, $o.poll_count)
    $c++
  } catch { Write-Host ("  line{0} UNPARSEABLE" -f ($i + 1)) }
}

Write-Host ""
Write-Host "=== P49 completion event detail ==="
for ($i = $lines.Count - 1; $i -ge 0; $i--) {
  try {
    $o = $lines[$i] | ConvertFrom-Json
  } catch { continue }
  if ($o.event -ne 'DSHD-P81-EXT-P49-BACKTEST-COMPLETE-OBSERVED-00001') { continue }
  Write-Host ("  FOUND at line " + ($i + 1))
  Write-Host ("  timestamp={0} task={1} token={2} a01={3} poll={4}" -f $o.timestamp, $o.task, $o.token, $o.a01_tag, $o.poll_count)
  Write-Host ("  archive={0} status={1} lc_gfe={2} symbols_run={3}" -f $o.p49_archive_id, $o.p49_manifest_status, $o.p49_manifest_lc_gfe, $o.p49_manifest_symbols_run)
  Write-Host ("  wind_calls={0} real_wind={1} offline={2} csv_untouched={3}" -f $o.p49_manifest_wind_api_calls, $o.p49_manifest_real_wind_call, $o.p49_manifest_offline_only, $o.p49_manifest_csv_not_modified)
  Write-Host ("  files={0} bytes={1} audit_status={2} expected_source={3}" -f $o.p49_file_count, $o.p49_total_bytes, $o.p49_audit_status, $o.p49_expected_source)
  Write-Host ("  manifest_last_write={0}" -f $o.p49_manifest_last_write)
  $unexp = @($o.p49_unexpected_files)
  Write-Host ("  unexpected_count={0}" -f $unexp.Count)
  foreach ($u in $unexp) { Write-Host ("    - {0}" -f $u) }
  Write-Host ("  snapshot_hashes={0}" -f $o.p49_sha256_snapshot.PSObject.Properties.Count)
  Write-Host ("  audit_only={0} intervention={1} no_kill={2} dshd_ran_backtest={3}" -f $o.audit_only, $o.intervention, $o.no_kill_executed, $o.dshd_ran_backtest)
  Write-Host ("  gate={0} permit={1} wind_api_calls={2} p0_all_pass={3}" -f $o.gate, $o.release_permit, $o.wind_api_calls, $o.p0_all_pass)
  break
}

Write-Host ""
Write-Host "=== last poll event (DSHD-P81-CLUSTER-WATCH-POLL) ==="
for ($i = $lines.Count - 1; $i -ge 0; $i--) {
  try { $o = $lines[$i] | ConvertFrom-Json } catch { continue }
  if ($o.event -notmatch '^DSHD-P81-CLUSTER-WATCH-POLL-') { continue }
  Write-Host ("  FOUND at line " + ($i + 1))
  Write-Host ("  [{0}] poll={1} p0={2}/{3} wind={4} gate={5} permit={6}" -f $o.timestamp, $o.poll_count, $o.p0_checks_passed, $o.p0_checks_total, $o.wind_api_calls, $o.gate, $o.release_permit)
  Write-Host ("  csv: rows={0} bytes={1} quick={2} longtable={3}" -f $o.csv_rows, $o.csv_bytes, $o.csv_quick_scan_status, $o.long_table_audit_status)
  Write-Host ("  longtable detail: dup={0} malformed={1} badkey={2} baddate={3} nonnum={4} syms={5} ind={6}" -f $o.long_table_duplicate_keys, $o.long_table_malformed_rows, $o.long_table_blank_key_fields, $o.long_table_bad_dates, $o.long_table_non_numeric_values, $o.long_table_symbols, $o.long_table_indicators)
  Write-Host ("  exchange: ok={0} mismatch={1} unknown={2} attr_files={3} attr_mismatch={4}" -f $o.exchange_bound_ok, $o.exchange_mismatch_count, $o.exchange_unknown_count, $o.exchange_attrib_files_scanned, $o.exchange_attrib_mismatch_count)
  Write-Host ("  whitelist_vio={0} ind_missing={1}" -f $o.symbol_whitelist_violations, $o.indicator_missing_count)
  Write-Host ("  p49: exists={0} files={1} miss={2} rm={3} chg={4} und={5} exchcol={6} status={7}" -f $o.p49_dir_exists, $o.p49_file_count, $o.p49_missing_files, $o.p49_removed_files, $o.p49_hash_changed_files, $o.p49_unexpected_files, $o.p49_exchange_column_mismatches, $o.p49_audit_status)
  Write-Host ("  ext_token={0} ext_task={1} audit_only={2} intervention={3}" -f $o.ext_token, $o.ext_task, $o.audit_only, $o.intervention)
  $w = @($o.warnings)
  Write-Host ("  warnings_count={0}" -f $w.Count)
  foreach ($x in $w) { Write-Host ("    - [{0}] {1}: {2}" -f $x.severity, $x.code, $x.detail) }
  break
}

Write-Host ""
Write-Host "=== warning board ==="
$wbPath = Join-Path $artDir 'dshd_p81_warning_board.json'
if (Test-Path $wbPath) {
  $wb = Get-Content $wbPath -Raw -Encoding UTF8 | ConvertFrom-Json
  Write-Host ("  updated_at={0} labels_this_poll={1} total_labels={2}" -f $wb.updated_at, $wb.labels_this_poll, $wb.total_labels)
  $wb.labels | ForEach-Object { Write-Host ("  - [{0}] {1} poll={2}: {3}" -f $_.severity, $_.code, $_.poll_count, $_.detail) }
}

Write-Host ""
Write-Host "=== territory contract ==="
$tcPath = Join-Path $artDir 'dshd_write_territory_contract_v1.json'
if (Test-Path $tcPath) {
  $tc = Get-Content $tcPath -Raw -Encoding UTF8 | ConvertFrom-Json
  Write-Host ("  contract_status={0} enforcement={1} territories={2} interception={3} auto_kill={4} auto_circuit_break={5}" -f $tc.contract_status, $tc.enforcement_mode, $tc.territory_count, $tc.interception_enabled, $tc.auto_kill_enabled, $tc.auto_circuit_break_enabled)
  $cw = $tc.concurrent_write_scan
  Write-Host ("  monitored_paths={0} conflicts={1} action_on_conflict={2}" -f $cw.monitored_path_count, $cw.conflict_count, $cw.action_on_conflict)
}

Write-Host ""
Write-Host "=== unparseable-line sweep (full ledger) ==="
$bad = 0
$suspect = @()
for ($i = 0; $i -lt $lines.Count; $i++) {
  if ($lines[$i].Length -eq 0) { continue }
  try { $null = $lines[$i] | ConvertFrom-Json } catch {
    $bad++
    if ($suspect.Count -lt 5) { $suspect += ("line{0}: {1}" -f ($i + 1), ($lines[$i].Substring(0, [Math]::Min(160, $lines[$i].Length)))) }
  }
}
Write-Host ("  total_lines={0} unparseable={1}" -f $lines.Count, $bad)
foreach ($s in $suspect) { Write-Host ("    {0}" -f $s) }

Write-Host ""
Write-Host "VERIFY_DONE"
