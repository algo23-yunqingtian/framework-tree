#requires -Version 5.1
# Smoke test for the P81-EXT rules. Dot-sources the constant+function head of the
# regenerated script (everything before the main loop), then exercises the new
# rules against the live files. Read-only: opens nothing for write.
$ErrorActionPreference = 'Continue'
$scriptPath = Join-Path $PSScriptRoot 'dshd_p81_watch.ps1'
Write-Host ("scriptPath={0} exists={1}" -f $scriptPath, (Test-Path $scriptPath))
$src = [System.IO.File]::ReadAllText($scriptPath, [System.Text.Encoding]::UTF8)
$marker = '# ---------------- MAIN LOOP'
$idx = $src.IndexOf($marker)
if ($idx -lt 0) { Write-Host "FATAL: main-loop marker not found"; exit 1 }
$head = $src.Substring(0, $idx)
Invoke-Expression $head
Write-Host ("LOADED scriptVersion={0} extToken={1} registryProducts={2} suffixes={3} expectedP49={4} monitoredPaths={5} csvPathExists={6} p49DirExists={7}" -f $scriptVersion, $extTokenName, $productExchange.Count, ($exchangeSuffixes -join ','), $p49ExpectedFiles.Count, $monitoredPaths.Count, (Test-Path $csvPath), (Test-Path $p49Dir))

"=== Test-ExchangeBinding ==="
foreach ($sym in @('CU.SHF','ZN.SHF','AL.SHF','SN.SHF','NI.SHF','PB.SHF','LC.SHF','LC.GFE','LC.DCE','SI.GFE','FOO.SHF','LC','LC.G')) {
  $r = Test-ExchangeBinding $sym
  Write-Host ("  {0,-8} -> {1,-18} expected={2,-5} actual={3,-5} ok={4,-5} | {5}" -f $sym, $r.verdict, $r.expected_exchange, $r.actual_exchange, $r.ok, $r.detail)
}

Write-Host ""
Write-Host "=== Get-QuickScan (format-aware keywords) ==="
$qs = Get-QuickScan $csvPath
Write-Host ("  format_kind={0} rows={1} status={2} missing_kw=[{3}] exists={4} bytes={5}" -f $qs.format_kind, $qs.data_rows, $qs.scan_status, ($qs.keywords_missing -join ','), $qs.exists, $qs.size_bytes)

Write-Host ""
Write-Host "=== Get-LongTableAudit (live CSV) ==="
$lt = Get-LongTableAudit $csvPath
Write-Host ("  exists={0} format={1} header={2} cols={3} rows={4}" -f $lt.exists, $lt.format, $lt.header, $lt.header_column_count, $lt.data_rows)
Write-Host ("  dup_keys={0} malformed={1} blank_key={2} bad_date={3} non_numeric={4}" -f $lt.duplicate_key_count, $lt.malformed_row_count, $lt.blank_key_field_count, $lt.bad_date_count, $lt.non_numeric_value_count)
Write-Host ("  symbols={0} indicators={1} sources={2} datemin={3} datemax={4} valmin={5} valmax={6}" -f $lt.distinct_symbol_count, $lt.distinct_indicator_count, $lt.distinct_source_count, $lt.date_min, $lt.date_max, $lt.value_min, $lt.value_max)
Write-Host ("  symbols=[{0}]" -f ($lt.symbols -join ','))
Write-Host ("  indicators=[{0}]" -f ($lt.indicators -join ','))
Write-Host ("  sources=[{0}]" -f ($lt.sources -join ','))
Write-Host ("  exch_ok={0} exch_mismatch={1} exch_unknown={2} exch_info={3}" -f $lt.exchange_ok_count, $lt.exchange_mismatch_count, $lt.exchange_unknown_count, $lt.exchange_info_count)
Write-Host ("  whitelist_violations=[{0}] whitelist_absent=[{1}] watchlist_present=[{2}]" -f ($lt.symbols_not_whitelisted -join ','), ($lt.whitelist_absent -join ','), ($lt.watchlist_present -join ','))
Write-Host ("  ind_missing=[{0}] ind_unexpected=[{1}]" -f ($lt.indicators_missing -join ','), ($lt.indicators_unexpected -join ','))
Write-Host ("  sym_row_counts={0}" -f ($lt.symbol_row_counts | ConvertTo-Json -Compress -Depth 4))
Write-Host ("  ind_row_counts={0}" -f ($lt.indicator_row_counts | ConvertTo-Json -Compress -Depth 4))
foreach ($b in $lt.symbol_exchange_bindings) {
  Write-Host ("  BIND {0,-9} actual={1,-5} expected={2,-5} verdict={3}" -f $b.symbol, $b.actual_exchange, $b.expected_exchange, $b.verdict)
}
Write-Host ("  AUDIT_STATUS={0}" -f $lt.audit_status)

Write-Host ""
Write-Host "=== Get-ExchangeAttributionAudit (dshc_* scan) ==="
$at = Get-ExchangeAttributionAudit
Write-Host ("  files_scanned={0} symbol_tokens={1} mismatches={2} unknown_exch={3} status={4}" -f $at.files_scanned, $at.symbol_tokens_total, $at.mismatch_count, $at.unknown_exchange_count, $at.audit_status)
Write-Host ("  distinct_symbols=[{0}]" -f ($at.distinct_symbols -join ','))
Write-Host ("  no_data_symbols=[{0}]" -f ($at.no_data_symbols -join ','))
foreach ($m in $at.mismatches) {
  Write-Host ("  MISMATCH {0} [{1}] no_data={2} files=[{3}]" -f $m.symbol, $m.verdict, $m.no_data_present_in_files, ($m.files -join ','))
  Write-Host ("    detail={0}" -f $m.detail)
}

Write-Host ""
Write-Host "=== Get-P49Audit (baseline: no previous state) ==="
$p49a = Get-P49Audit $null
Write-Host ("  exists={0} files={1} expected={2} bytes={3}" -f $p49a.exists, $p49a.file_count, $p49a.expected_file_count, $p49a.total_bytes)
Write-Host ("  missing=[{0}] unexpected=[{1}] undermin=[{2}]" -f ($p49a.missing_files -join ','), ($p49a.unexpected_files -join ','), ($p49a.under_min_size_files -join ','))
Write-Host ("  manifest_status={0} agent={1} token={2} gate={3} permit={4}" -f $p49a.manifest_status, $p49a.manifest_agent, $p49a.manifest_token, $p49a.manifest_gate, $p49a.manifest_release_permit)
Write-Host ("  manifest_lc_gfe={0} symbols_run={1} wind_calls={2} real_wind={3} offline={4} csv_untouched={5}" -f $p49a.manifest_lc_gfe, $p49a.manifest_symbols_run, $p49a.manifest_wind_api_calls, $p49a.manifest_real_wind_call, $p49a.manifest_offline_only, $p49a.manifest_csv_not_modified)
Write-Host ("  hash_changed=[{0}] added=[{1}] removed=[{2}] exch_col_mismatch={3}" -f ($p49a.hash_changed_files -join ','), ($p49a.added_files -join ','), ($p49a.removed_files -join ','), $p49a.exchange_column_mismatch_count)
Write-Host ("  AUDIT_STATUS={0}" -f $p49a.audit_status)
foreach ($f in $p49a.files) {
  Write-Host ("  FILE {0,-28} {1,8}B  {2}  exp={3} chg={4}" -f $f.relative_path, $f.size_bytes, $f.sha256, $f.expected, $f.change)
}
foreach ($r in $p49a.exchange_column_rows) {
  Write-Host ("  EXCHCOL {0,-9} col={1,-26} derived={2,-5} norm={3,-5} verdict={4,-10} col_matches={5}" -f $r.symbol, $r.exchange_column, $r.derived_suffix, $r.normalized_suffix, $r.binding_verdict, $r.column_matches_suffix)
}

Write-Host ""
Write-Host "=== Get-P49Audit (second pass with previous state -> UNCHANGED) ==="
$p49b = Get-P49Audit $p49a.state_snapshot
$u = 0; $c = 0
foreach ($f in $p49b.files) { if ($f.change -eq 'UNCHANGED') { $u++ } elseif ($f.change -eq 'HASH_CHANGED') { $c++ } }
Write-Host ("  files={0} unchanged={1} hash_changed={2} added=[{3}] removed=[{4}] status={5}" -f $p49b.file_count, $u, $c, ($p49b.added_files -join ','), ($p49b.removed_files -join ','), $p49b.audit_status)

Write-Host ""
Write-Host "=== JSON round-trip check (ConvertTo-Json depth 14) ==="
$probe = @{
  long_table_audit = $lt
  attribution_audit = $at
  p49_artifact_audit = $p49a
}
$js = $probe | ConvertTo-Json -Depth 14 -Compress
$back = $js | ConvertFrom-Json
Write-Host ("  json_bytes={0} back.p49.exists={1} back.lt.status={2} back.at.mismatches={3}" -f $js.Length, $back.p49_artifact_audit.exists, $back.long_table_audit.audit_status, $back.attribution_audit.mismatch_count)
Write-Host "SMOKE_TEST_DONE"
