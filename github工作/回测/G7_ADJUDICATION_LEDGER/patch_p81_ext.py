# -*- coding: utf-8 -*-
# ============================================================
# [ARCHIVED] DSHD-P81-EXT patch — DO NOT RE-RUN
# ============================================================
# This patch is non-idempotent (contains assert src.count(old)==1 guards).
# Re-running will FAIL with assertion error.
#
# For incremental changes, create a NEW patch file:
#   patch_p81_tweak2.py  (for the next TWEAK iteration)
#
# This file is preserved for historical reference only.
# ============================================================
"""
DSHD-P81-EXT patch.
Extends recreate_p81.py with:
  1. exchange binding audit (product -> exchange suffix registry)
  2. long-table CSV primary-key / symbol-whitelist / indicator-list validation
  3. artifacts/p49_backtest/ read-only integrity + hash-change audit
  4. one-shot DSHD-P81-EXT-P49-BACKTEST-COMPLETE-OBSERVED audit event
AUDIT_READ_ONLY throughout: record only, never kill, never intervene.
"""
import io
import sys

GEN = r"D:\DSH_WORK\github工作\回测\G7_ADJUDICATION_LEDGER\recreate_p81.py"

NEW_FUNCS = r'''
function Test-ExchangeBinding {
  param([string]$Symbol)
  $product = ''
  $suffix = ''
  $expected = ''
  $ok = $false
  $verdict = 'EMPTY_SYMBOL'
  $detail = ''
  $sym = [string]$Symbol
  if ($sym.Length -gt 0) {
    $parts = @($sym.Split('.'))
    if ($parts.Count -eq 2) {
      $product = $parts[0].ToUpper()
      $suffix = $parts[1].ToUpper()
    } else {
      $verdict = 'MALFORMED_SYMBOL'
      $detail = ('symbol "' + $sym + '" is not PRODUCT.EXCHANGE (segments=' + $parts.Count + ')')
      return @{ok = $ok; product = $product; suffix = $suffix; expected_exchange = $expected; actual_exchange = $suffix; verdict = $verdict; detail = $detail}
    }
  }
  $knownSuffix = $false
  foreach ($s in $exchangeSuffixes) { if ($s -eq $suffix) { $knownSuffix = $true } }
  $inRegistry = $false
  if ($productExchange.ContainsKey($product)) { $inRegistry = $true; $expected = $productExchange[$product] }
  if (-not $knownSuffix) {
    $verdict = 'UNKNOWN_EXCHANGE'
    $detail = ('product ' + $product + ' uses unrecognized exchange suffix ' + $suffix + '; known=' + ($exchangeSuffixes -join ',') + '; no intervention')
  } elseif (-not $inRegistry) {
    $verdict = 'UNKNOWN_PRODUCT'
    $detail = ('product ' + $product + ' is absent from the DSHD exchange registry (suffix ' + $suffix + '); no intervention')
  } elseif ($expected -eq $suffix) {
    $ok = $true
    $verdict = 'BOUND_OK'
    $detail = ($product + ' correctly bound to ' + $suffix)
  } else {
    $verdict = 'MISMATCH'
    $detail = ($product + ' belongs to ' + $expected + ' but is bound to ' + $suffix + '; no intervention')
  }
  return @{ok = $ok; product = $product; suffix = $suffix; expected_exchange = $expected; actual_exchange = $suffix; verdict = $verdict; detail = $detail}
}

function Get-LongTableAudit {
  param([string]$CsvPath)
  $out = @{
    check = 'LONG_TABLE_PRIMARY_KEY_INTEGRITY'
    mode = 'OBSERVATION_ONLY'
    auto_intervene = $false
    exists = $false
    format = 'ABSENT'
    primary_key_columns = @('date','symbol','indicator')
    header = ''
    header_column_count = 0
    key_field_count_expected = 0
    data_rows = 0
    malformed_row_count = 0
    malformed_row_samples = @()
    blank_key_field_count = 0
    bad_date_count = 0
    non_numeric_value_count = 0
    duplicate_key_count = 0
    duplicate_key_samples = @()
    distinct_symbol_count = 0
    symbols = @()
    symbol_row_counts = @{}
    symbol_exchange_bindings = @()
    exchange_ok_count = 0
    exchange_mismatch_count = 0
    exchange_unknown_count = 0
    exchange_info_count = 0
    distinct_indicator_count = 0
    indicators = @()
    indicator_row_counts = @{}
    symbol_indicator_row_counts = @{}
    indicators_missing = @()
    indicators_unexpected = @()
    symbols_not_whitelisted = @()
    whitelist_absent = @()
    watchlist_present = @()
    distinct_source_count = 0
    sources = @()
    value_min = ''
    value_max = ''
    date_min = ''
    date_max = ''
    audit_status = 'CSV_ABSENT'
    intervention = 'NONE'
  }
  if (-not (Test-Path $CsvPath)) { return $out }
  $out.exists = $true
  $lines = @()
  try { $lines = @(Get-Content $CsvPath -Encoding UTF8) } catch { }
  if ($lines.Count -eq 0) { $out.audit_status = 'CSV_EMPTY'; return $out }
  $header = [string]$lines[0]
  $out.header = $header
  $cols = @($header.Split(','))
  $out.header_column_count = $cols.Count
  $out.key_field_count_expected = $cols.Count
  $colsTrim = @()
  foreach ($c in $cols) { $colsTrim += $c.Trim().ToLower() }
  $idxDate = -1; $idxSym = -1; $idxInd = -1; $idxVal = -1; $idxSrc = -1
  for ($i = 0; $i -lt $colsTrim.Count; $i++) {
    $cn = $colsTrim[$i]
    if ($cn -eq 'date') { $idxDate = $i }
    elseif ($cn -eq 'symbol') { $idxSym = $i }
    elseif ($cn -eq 'indicator') { $idxInd = $i }
    elseif ($cn -eq 'value') { $idxVal = $i }
    elseif ($cn -eq 'source') { $idxSrc = $i }
  }
  $isLong = $false
  if (($idxInd -ge 0) -and ($idxVal -ge 0)) { $isLong = $true }
  if ($isLong) { $out.format = 'LONG' } else { $out.format = 'WIDE_OR_UNKNOWN' }
  $seenKeys = @{}
  $symSet = @{}
  $indSet = @{}
  $srcSet = @{}
  $symTotal = @{}
  $indTotal = @{}
  $symIndTotal = @{}
  $valueNumMin = [double]::MaxValue
  $valueNumMax = [double]::MinValue
  for ($i = 1; $i -lt $lines.Count; $i++) {
    $ln = [string]$lines[$i]
    if ([string]::IsNullOrWhiteSpace($ln)) { continue }
    $out.data_rows = ([int]$out.data_rows) + 1
    $fp = @($ln.Split(','))
    if ($fp.Count -ne $cols.Count) {
      $out.malformed_row_count = ([int]$out.malformed_row_count) + 1
      if ($out.malformed_row_count -le 5) { $out.malformed_row_samples += ('L' + $i + ':' + $ln) }
      continue
    }
    $d = ''; $s = ''; $ind = ''; $val = ''; $src = ''
    if ($idxDate -ge 0 -and $idxDate -lt $fp.Count) { $d = $fp[$idxDate].Trim() }
    if ($idxSym -ge 0 -and $idxSym -lt $fp.Count) { $s = $fp[$idxSym].Trim() }
    if ($idxInd -ge 0 -and $idxInd -lt $fp.Count) { $ind = $fp[$idxInd].Trim() }
    if ($idxVal -ge 0 -and $idxVal -lt $fp.Count) { $val = $fp[$idxVal].Trim() }
    if ($idxSrc -ge 0 -and $idxSrc -lt $fp.Count) { $src = $fp[$idxSrc].Trim() }
    $blankKeys = 0
    if ($d.Length -eq 0) { $blankKeys = $blankKeys + 1 }
    if ($s.Length -eq 0) { $blankKeys = $blankKeys + 1 }
    if ($isLong -and $ind.Length -eq 0) { $blankKeys = $blankKeys + 1 }
    if ($blankKeys -gt 0) { $out.blank_key_field_count = ([int]$out.blank_key_field_count) + $blankKeys }
    if ($d.Length -gt 0) {
      $dtOk = $false
      if ($d -match '^\d{4}-\d{2}-\d{2}$') {
        try { [void][datetime]::ParseExact($d, 'yyyy-MM-dd', $null); $dtOk = $true } catch { }
      }
      if (-not $dtOk) {
        $out.bad_date_count = ([int]$out.bad_date_count) + 1
      } else {
        if (($out.date_min.Length -eq 0) -or ($d -lt $out.date_min)) { $out.date_min = $d }
        if ($d -gt $out.date_max) { $out.date_max = $d }
      }
    }
    if ($isLong -and $val.Length -gt 0) {
      if ($val -match '^-?\d+(\.\d+)?$') {
        $num = [double]0
        try { $num = [double]::Parse($val) } catch { }
        if ($num -lt $valueNumMin) { $valueNumMin = $num }
        if ($num -gt $valueNumMax) { $valueNumMax = $num }
      } else {
        $out.non_numeric_value_count = ([int]$out.non_numeric_value_count) + 1
      }
    }
    $keyParts = $d + '|' + $s
    if ($isLong) { $keyParts = $keyParts + '|' + $ind }
    if ($seenKeys.ContainsKey($keyParts)) {
      $out.duplicate_key_count = ([int]$out.duplicate_key_count) + 1
      if ($out.duplicate_key_samples.Count -lt 10) { $out.duplicate_key_samples += $keyParts }
    } else { $seenKeys[$keyParts] = $true }
    if ($s.Length -gt 0) {
      if (-not $symSet.ContainsKey($s)) { $symSet[$s] = $true; $out.symbols += $s }
      if ($symTotal.ContainsKey($s)) { $symTotal[$s] = ([long]$symTotal[$s]) + 1 } else { $symTotal[$s] = 1 }
    }
    if ($isLong -and $ind.Length -gt 0) {
      if (-not $indSet.ContainsKey($ind)) { $indSet[$ind] = $true; $out.indicators += $ind }
      if ($indTotal.ContainsKey($ind)) { $indTotal[$ind] = ([long]$indTotal[$ind]) + 1 } else { $indTotal[$ind] = 1 }
      $ck = $s + '|' + $ind
      if ($symIndTotal.ContainsKey($ck)) { $symIndTotal[$ck] = ([long]$symIndTotal[$ck]) + 1 } else { $symIndTotal[$ck] = 1 }
    }
    if ($src.Length -gt 0 -and (-not $srcSet.ContainsKey($src))) { $srcSet[$src] = $true; $out.sources += $src }
  }
  $out.distinct_symbol_count = $symSet.Count
  $out.distinct_indicator_count = $indSet.Count
  $out.distinct_source_count = $srcSet.Count
  $out.symbol_row_counts = $symTotal
  $out.indicator_row_counts = $indTotal
  $out.symbol_indicator_row_counts = $symIndTotal
  if ($valueNumMin -ne [double]::MaxValue) { $out.value_min = [string]$valueNumMin }
  if ($valueNumMax -ne [double]::MinValue) { $out.value_max = [string]$valueNumMax }
  foreach ($s in $out.symbols) {
    $b = Test-ExchangeBinding $s
    $b.symbol = $s
    $out.symbol_exchange_bindings += $b
    if ($b.verdict -eq 'MISMATCH') { $out.exchange_mismatch_count = ([int]$out.exchange_mismatch_count) + 1 }
    elseif ($b.verdict -eq 'UNKNOWN_EXCHANGE') { $out.exchange_unknown_count = ([int]$out.exchange_unknown_count) + 1 }
    elseif ($b.verdict -eq 'BOUND_OK') { $out.exchange_ok_count = ([int]$out.exchange_ok_count) + 1 }
    else { $out.exchange_info_count = ([int]$out.exchange_info_count) + 1 }
  }
  foreach ($s in $out.symbols) {
    $found = $false
    foreach ($w in $csvSymbolWhitelist) { if ($w -eq $s) { $found = $true } }
    if (-not $found) { $out.symbols_not_whitelisted += $s }
  }
  foreach ($w in $csvSymbolWhitelist) {
    $found = $false
    foreach ($s in $out.symbols) { if ($s -eq $w) { $found = $true } }
    if (-not $found) { $out.whitelist_absent += $w }
  }
  foreach ($w in $csvSymbolWatchlist) {
    foreach ($s in $out.symbols) { if ($s -eq $w) { $out.watchlist_present += $w } }
  }
  if ($isLong) {
    foreach ($e in $csvIndicatorExpected) {
      $found = $false
      foreach ($x in $out.indicators) { if ($x -eq $e) { $found = $true } }
      if (-not $found) { $out.indicators_missing += $e }
    }
    foreach ($x in $out.indicators) {
      $found = $false
      foreach ($e in $csvIndicatorExpected) { if ($e -eq $x) { $found = $true } }
      if (-not $found) { $out.indicators_unexpected += $x }
    }
  }
  $structBad = 0
  $structBad = $structBad + $out.malformed_row_count + $out.blank_key_field_count + $out.bad_date_count + $out.non_numeric_value_count + $out.duplicate_key_count
  if ($structBad -gt 0) { $out.audit_status = 'LONGTABLE_KEY_INTEGRITY_DEFECT' }
  elseif (($out.exchange_mismatch_count -gt 0) -or ($out.exchange_unknown_count -gt 0)) { $out.audit_status = 'EXCHANGE_BINDING_ANOMALY' }
  elseif (($out.symbols_not_whitelisted.Count -gt 0) -or ($out.indicators_missing.Count -gt 0) -or ($out.indicators_unexpected.Count -gt 0)) { $out.audit_status = 'LONGTABLE_SCHEMA_ANOMALY' }
  elseif (-not $isLong) { $out.audit_status = 'FORMAT_NOT_LONG' }
  else { $out.audit_status = 'LONGTABLE_AUDIT_OK' }
  return $out
}

function Get-ExchangeAttributionAudit {
  $out = @{
    check = 'DSHC_ATTRIBUTION_SYMBOL_EXCHANGE_SCAN'
    mode = 'OBSERVATION_ONLY'
    auto_intervene = $false
    owner_filter = 'dshc_* (json + jsonl under 2MB)'
    files_scanned = 0
    symbol_tokens_total = 0
    distinct_symbols = @()
    mismatches = @()
    mismatch_count = 0
    unknown_exchange_count = 0
    no_data_symbols = @()
    audit_status = 'ATTRIBUTION_EXCHANGE_CLEAN'
    intervention = 'NONE'
  }
  $files = @(Get-ChildItem $artDir -Filter 'dshc_*' -File -ErrorAction SilentlyContinue)
  $sel = @()
  foreach ($f in $files) {
    $ext = $f.Extension.ToLower()
    if ($ext -eq '.json') { $sel += $f }
    elseif (($ext -eq '.jsonl') -and ($f.Length -lt 2000000)) { $sel += $f }
  }
  $found = @{}
  $misMap = @{}
  $ndMap = @{}
  foreach ($f in $sel) {
    $out.files_scanned = ([int]$out.files_scanned) + 1
    $txt = ''
    try { $txt = [System.IO.File]::ReadAllText($f.FullName, [System.Text.Encoding]::UTF8) } catch { continue }
    $hasNoData = $false
    if ($txt -match 'NO_DATA') { $hasNoData = $true }
    $ms = [regex]::Matches($txt, '\b([A-Z]{1,3})\.([A-Z]{3,4})\b')
    foreach ($m in $ms) {
      $prod = $m.Groups[1].Value
      $sfx = $m.Groups[2].Value
      $sym = $prod + '.' + $sfx
      if (-not $found.ContainsKey($sym)) {
        $found[$sym] = $true
        $out.distinct_symbols += $sym
        $out.symbol_tokens_total = ([int]$out.symbol_tokens_total) + 1
      }
      $b = Test-ExchangeBinding $sym
      if (($b.verdict -eq 'MISMATCH') -or ($b.verdict -eq 'UNKNOWN_EXCHANGE')) {
        $mk = $sym + '|' + $b.verdict
        if (-not $misMap.ContainsKey($mk)) {
          $misMap[$mk] = $true
          $row = @{symbol = $sym; verdict = $b.verdict; detail = $b.detail; files = @($f.Name); no_data_present_in_files = $hasNoData}
          $out.mismatches += $row
          $out.mismatch_count = ([int]$out.mismatch_count) + 1
          if ($b.verdict -eq 'UNKNOWN_EXCHANGE') { $out.unknown_exchange_count = ([int]$out.unknown_exchange_count) + 1 }
        } else {
          foreach ($row in $out.mismatches) {
            if (($row.symbol -eq $sym) -and ($row.verdict -eq $b.verdict)) {
              if ($row.files -notcontains $f.Name) { $row.files += $f.Name }
              if ($hasNoData) { $row.no_data_present_in_files = $true }
            }
          }
        }
        if ($hasNoData -and (-not $ndMap.ContainsKey($sym))) { $ndMap[$sym] = $true; $out.no_data_symbols += $sym }
      }
    }
  }
  if ($out.mismatch_count -gt 0) { $out.audit_status = 'ATTRIBUTED_EXCHANGE_ANOMALY' }
  return $out
}

function Get-P49Audit {
  param($PrevState)
  $dir = $p49Dir
  $out = @{
    check = 'P49_BACKTEST_ARTIFACT_READ_ONLY_AUDIT'
    dir = 'artifacts/p49_backtest'
    mode = 'OBSERVATION_ONLY'
    read_only = $true
    wrote_anything = $false
    auto_intervene = $false
    exists = $false
    file_count = 0
    expected_file_count = $p49ExpectedFiles.Count
    total_bytes = 0
    files = @()
    missing_files = @()
    unexpected_files = @()
    under_min_size_files = @()
    hash_changed_files = @()
    added_files = @()
    removed_files = @()
    manifest_archive_id = ''
    manifest_agent = ''
    manifest_token = ''
    manifest_status = ''
    manifest_release_permit = ''
    manifest_gate = ''
    manifest_wind_api_calls = 0
    manifest_real_wind_call = $false
    manifest_csv_not_modified = $false
    manifest_offline_only = $false
    manifest_lc_gfe = ''
    manifest_symbols_run = 0
    exchange_column_rows = @()
    exchange_column_mismatch_count = 0
    state_snapshot = @{}
    audit_status = 'P49_ABSENT'
    intervention = 'NONE'
  }
  if (-not (Test-Path $dir)) { return $out }
  $out.exists = $true
  $items = @(Get-ChildItem $dir -File -Recurse -ErrorAction SilentlyContinue)
  $out.file_count = $items.Count
  $prevMap = @{}
  if ($null -ne $PrevState) {
    foreach ($k in $PrevState.Keys) { $prevMap[$k] = $PrevState[$k] }
  }
  $curMap = @{}
  $totalBytes = [long]0
  foreach ($it in $items) {
    $rel = [string]$it.FullName
    if ($rel.Length -gt $dir.Length) { $rel = $rel.Substring($dir.Length).TrimStart('\') }
    $sz = [long]$it.Length
    $hash = ''
    try { $hash = (Get-FileHash $it.FullName -Algorithm SHA256).Hash } catch { }
    $isExp = $false
    foreach ($e in $p49ExpectedFiles) { if ($e -eq $it.Name) { $isExp = $true } }
    $underMin = $false
    if ($sz -lt $p49MinFileSize) { $underMin = $true }
    $changed = 'NEW'
    if ($prevMap.ContainsKey($rel)) {
      if ([string]$prevMap[$rel] -eq $hash) { $changed = 'UNCHANGED' }
      else { $changed = 'HASH_CHANGED'; $out.hash_changed_files += $rel }
    } else {
      $out.added_files += $rel
    }
    $row = @{
      relative_path = $rel
      name = $it.Name
      size_bytes = $sz
      sha256 = $hash
      last_write = $it.LastWriteTime.ToString('yyyy-MM-ddTHH:mm:sszzz')
      expected = $isExp
      under_min_size = $underMin
      change = $changed
    }
    $out.files += $row
    if ($underMin) { $out.under_min_size_files += $rel }
    if (-not $isExp) { $out.unexpected_files += $rel }
    $curMap[$rel] = $hash
    $totalBytes += $sz
  }
  foreach ($k in $prevMap.Keys) { if (-not $curMap.ContainsKey($k)) { $out.removed_files += $k } }
  $out.total_bytes = $totalBytes
  foreach ($e in $p49ExpectedFiles) {
    $found = $false
    foreach ($f in $items) { if ($f.Name -eq $e) { $found = $true } }
    if (-not $found) { $out.missing_files += $e }
  }
  $manifestPath = $dir + '\MANIFEST.json'
  if (Test-Path $manifestPath) {
    $m = Get-JsonSafe $manifestPath
    if ($null -ne $m) {
      $out.manifest_archive_id = [string](Get-JsonProp $m 'archive_id' '')
      $out.manifest_agent = [string](Get-JsonProp $m 'agent' '')
      $out.manifest_token = [string](Get-JsonProp $m 'token' '')
      $out.manifest_status = [string](Get-JsonProp $m 'status' '')
      $out.manifest_release_permit = [string](Get-JsonProp $m 'release_permit' '')
      $out.manifest_gate = [string](Get-JsonProp $m 'gate' '')
      $safety = Get-JsonProp $m 'safety' @{}
      $out.manifest_wind_api_calls = [long](Get-JsonProp $safety 'wind_api_calls' 0)
      $out.manifest_real_wind_call = [bool](Get-JsonProp $safety 'real_wind_call' $false)
      $out.manifest_csv_not_modified = [bool](Get-JsonProp $safety 'csv_not_modified' $false)
      $out.manifest_offline_only = [bool](Get-JsonProp $safety 'offline_only' $false)
      $receipt = Get-JsonProp $m 'receipt' @{}
      $out.manifest_lc_gfe = [string](Get-JsonProp $receipt 'LC_GFE' '')
      $out.manifest_symbols_run = [int](Get-JsonProp $receipt 'symbols_run' 0)
    }
  }
  $spPath = $dir + '\symbol_performance.csv'
  $exMismatch = 0
  if (Test-Path $spPath) {
    $spLines = @()
    try { $spLines = @(Get-Content $spPath -Encoding UTF8) } catch { }
    for ($i = 1; $i -lt $spLines.Count; $i++) {
      $ln = [string]$spLines[$i]
      if ([string]::IsNullOrWhiteSpace($ln)) { continue }
      $fp = @($ln.Split(','))
      if ($fp.Count -lt 2) { continue }
      $sym = $fp[0].Trim()
      $exCol = $fp[1].Trim()
      $b = Test-ExchangeBinding $sym
      $suffixInCol = ''
      if ($exCol -match '\(([A-Za-z]{3,4})\)') { $suffixInCol = $Matches[1].ToUpper() }
      if ($exchangeAlias.ContainsKey($suffixInCol)) { $suffixInCol = $exchangeAlias[$suffixInCol] }
      $colMatch = $false
      if (($b.ok -eq $true) -and ($suffixInCol -eq $b.actual_exchange)) { $colMatch = $true }
      if (-not $colMatch) { $exMismatch = $exMismatch + 1 }
      $er = @{symbol = $sym; exchange_column = $exCol; derived_suffix = $b.actual_exchange; normalized_suffix = $suffixInCol; binding_verdict = $b.verdict; column_matches_suffix = $colMatch}
      $out.exchange_column_rows += $er
    }
  }
  $out.exchange_column_mismatch_count = $exMismatch
  $out.state_snapshot = $curMap
  if (($out.missing_files.Count -gt 0) -or ($out.removed_files.Count -gt 0)) { $out.audit_status = 'P49_ARTIFACT_SET_INCOMPLETE' }
  elseif ($out.hash_changed_files.Count -gt 0) { $out.audit_status = 'P49_ARTIFACT_HASH_CHANGED' }
  elseif ($exMismatch -gt 0) { $out.audit_status = 'P49_EXCHANGE_COLUMN_ANOMALY' }
  elseif ($out.under_min_size_files.Count -gt 0) { $out.audit_status = 'P49_FILE_BENEATH_MIN_SIZE' }
  elseif ($out.manifest_status -match 'BACKTEST_COMPLETE') { $out.audit_status = 'P49_BACKTEST_COMPLETE_INTEGRITY_OK' }
  else { $out.audit_status = 'P49_PRESENT_PARTIAL' }
  return $out
}

'''

def patches():
    p = []

    # ---- A: header banner ----
    p.append(("A_header",
        "# DSHD-P81-WATCH\n"
        "#   territory contract solidification + OBS-SPAWN-EXCEL-001\n"
        "#   drift observer + 3-agent cluster status board\n",
        "# DSHD-P81-WATCH (EXT)\n"
        "#   territory contract solidification + OBS-SPAWN-EXCEL-001\n"
        "#   drift observer + 3-agent cluster status board\n"
        "#   EXT : exchange binding audit (product -> exchange suffix)\n"
        "#         long-table CSV primary-key / whitelist / indicator validation\n"
        "#         artifacts/p49_backtest/ read-only integrity + hash audit\n"))

    # ---- B: version + EXT token ----
    p.append(("B_version",
        "$scriptVersion             = '1.0.0'",
        "$scriptVersion             = '1.1.0-EXT'"))
    p.append(("B_token",
        "$tokenName                 = 'DSHD-P81-TOKEN'",
        "$tokenName                 = 'DSHD-P81-TOKEN'\n"
        "$extTokenName               = 'DSHD-P81-EXT-TOKEN'\n"
        "$extTaskName                = 'DSHD-P81-EXT'"))

    # ---- C: new paths ----
    p.append(("C_paths",
        "$csvPath                   = $baseDir + '\\output_sample\\wdf_sample_metals_raw.csv'",
        "$csvPath                   = $baseDir + '\\output_sample\\wdf_sample_metals_raw.csv'\n"
        "$csvLongTwin               = $baseDir + '\\output_sample\\wdf_sample_metals_long.csv'\n"
        "$p49Dir                    = $artDir + '\\p49_backtest'"))

    # ---- D: exchange registry + whitelist + p49 rule constants ----
    p.append(("D_registry",
        "$refCsvSha256A01           = 'BEF26114CC1FCA4BDD40E911F888E7CA388DD150A1D48FD6C623D8FE07850895'",
        "$refCsvSha256A01           = 'BEF26114CC1FCA4BDD40E911F888E7CA388DD150A1D48FD6C623D8FE07850895'\n\n"
        "# --- EXT: exchange binding registry (product -> expected exchange suffix) ---\n"
        "# SHFE = 上期所 (Shanghai Futures Exchange); GFE = 广期所 (Guangzhou Futures Exchange)\n"
        "# LC (carbonate lithium) belongs to GFE. Observing only; never intervenes.\n"
        "$exchangeSuffixes          = @('SHF','GFE','DCE','CZCE','INE')\n"
        "$exchangeAlias             = @{ SHF='SHF'; SHFE='SHF'; GFE='GFE'; GZFE='GFE'; DCE='DCE'; DCEX='DCE'; CZCE='CZCE'; ZCE='CZCE'; INE='INE' }\n"
        "$productExchange           = @{\n"
        "  CU='SHF'; ZN='SHF'; PB='SHF'; AL='SHF'; SN='SHF'; NI='SHF'\n"
        "  AG='SHF'; AU='SHF'; RB='SHF'; HC='SHF'; WR='SHF'; FU='SHF'; BU='SHF'; RU='SHF'; SP='SHF'; AO='SHF'; SS='SHF'; BR='SHF'\n"
        "  LC='GFE'; SI='GFE'; PS='GFE'\n"
        "  A='DCE'; B='DCE'; C='DCE'; CS='DCE'; JD='DCE'; L='DCE'; M='DCE'; P='DCE'; PP='DCE'; V='DCE'; Y='DCE'; EG='DCE'; FB='DCE'; RR='DCE'; JM='DCE'; I='DCE'\n"
        "  CF='CZCE'; CY='CZCE'; FG='CZCE'; MA='CZCE'; OI='CZCE'; PF='CZCE'; PK='CZCE'; RI='CZCE'; RM='CZCE'; SA='CZCE'; SM='CZCE'; UR='CZCE'; AP='CZCE'; CJ='CZCE'; JR='CZCE'; LR='CZCE'; PM='CZCE'\n"
        "  SC='INE'; NR='INE'; LU='INE'; BC='INE'; EC='INE'; BS='INE'\n"
        "}\n"
        "$csvSymbolWhitelist        = @('AL.SHF','CU.SHF','NI.SHF','PB.SHF','SN.SHF','ZN.SHF')\n"
        "$csvSymbolWatchlist        = @('LC.GFE')\n"
        "$csvIndicatorExpected      = @('CLOSE','VOL','OI','SETTLE')\n\n"
        "# --- EXT: P49 backtest artifact audit (READ ONLY) ---\n"
        "$p49ExpectedFiles          = @('backtest_metrics.json','backtest_report.pdf','MANIFEST.json','pipeline_metadata.json','symbol_performance.csv','symbol_performance.md')\n"
        "$p49MinFileSize            = 1024"))

    # ---- E: monitored paths (territory) ----
    p.append(("E_paths_monitored",
        "  @{p = $artDir + '\\dsha_a02_plus_receipt.json';                  owner = 'DSHA';              shared = $false}\n)",
        "  @{p = $artDir + '\\dsha_a02_plus_receipt.json';                  owner = 'DSHA';              shared = $false}\n"
        "  @{p = $p49Dir + '\\MANIFEST.json';                               owner = 'DSHA-P49';          shared = $false}\n"
        "  @{p = $p49Dir + '\\pipeline_metadata.json';                      owner = 'DSHA-P49';          shared = $false}\n"
        "  @{p = $p49Dir + '\\backtest_metrics.json';                       owner = 'DSHA-P49';          shared = $false}\n"
        "  @{p = $p49Dir + '\\symbol_performance.csv';                      owner = 'DSHA-P49';          shared = $false}\n"
        "  @{p = $p49Dir + '\\symbol_performance.md';                       owner = 'DSHA-P49';          shared = $false}\n"
        "  @{p = $p49Dir + '\\backtest_report.pdf';                        owner = 'DSHA-P49';          shared = $false}\n"
        "  @{p = $csvLongTwin;                                              owner = 'DSHA';              shared = $false}\n)"))

    # ---- F: zh labels (renumber + add) ----
    p.append(("F_zh",
        "  sub          = '领地契约固化 · Excel 漂移观测器 · 三 Agent 状态看板'",
        "  sub          = '领地契约固化 · Excel 漂移观测器 · 交易所归属校验 · P49 产物只读审计'"))
    p.append(("F_zh_heads",
        "  head_p0      = '六、P0 校验'\n  head_red     = '七、红线确认'",
        "  head_exch    = '六、长表主键 + 品种白名单 + 交易所归属'\n"
        "  head_p49     = '七、P49 回测产物只读审计'\n"
        "  head_p0      = '八、P0 校验'\n  head_red     = '九、红线确认'"))

    # ---- G: new output paths ----
    p.append(("G_outpaths",
        "$outBoard                  = $artDir + '\\dshd_p81_warning_board.json'",
        "$outBoard                  = $artDir + '\\dshd_p81_warning_board.json'\n"
        "$outLongTable              = $artDir + '\\dshd_p81_ext_longtable_exchange_audit.json'\n"
        "$outP49                    = $artDir + '\\dshd_p81_ext_p49_artifact_audit.json'"))

    # ---- H: new functions ----
    p.append(("H_funcs",
        "function Get-TerritoryState {",
        NEW_FUNCS.lstrip("\n") + "function Get-TerritoryState {"))

    # ---- I: Get-QuickScan long-format aware keywords ----
    p.append(("I_quickscan",
        "  $keywords = @('date','symbol','indicator','CLOSE','VOL','OI','SETTLE','source')\n"
        "  $hLower = ''\n"
        "  if ($header.Length -gt 0) { $hLower = $header.ToLower() }\n"
        "  $missing = @()\n"
        "  foreach ($k in $keywords) {\n"
        "    if ($hLower -notmatch [regex]::Escape($k.ToLower())) { $missing += $k }\n"
        "  }",
        "  $keywords = @('date','symbol','indicator','value','source')\n"
        "  $hLower = ''\n"
        "  $isLongFormat = $false\n"
        "  if ($header.Length -gt 0) { $hLower = $header.ToLower() }\n"
        "  if (($hLower -match 'indicator') -and ($hLower -match '(^|,)value(,|$)')) { $isLongFormat = $true }\n"
        "  $missing = @()\n"
        "  foreach ($k in $keywords) {\n"
        "    if ((-not $isLongFormat) -and ($k -eq 'value')) { continue }\n"
        "    if ($hLower -notmatch [regex]::Escape($k.ToLower())) { $missing += $k }\n"
        "  }\n"
        "  # In long format the indicator names are row values, not header columns;\n"
        "  # they are validated by Get-LongTableAudit instead of by header keywords."))
    p.append(("I_quickscan_ret",
        "    scan_status = $status\n"
        "    p68_gate_is_authority = $true",
        "    scan_status = $status\n"
        "    format_kind = $(if ($isLongFormat) { 'LONG' } else { 'WIDE_OR_UNKNOWN' })\n"
        "    p68_gate_is_authority = $true"))

    # ---- J: main loop init ----
    p.append(("J_init",
        "$warnBoard = @()\n"
        "$excelHistory = @()\n"
        "$fastBuffer = @()",
        "$warnBoard = @()\n"
        "$excelHistory = @()\n"
        "$fastBuffer = @()\n"
        "$prevP49 = $null\n"
        "$p49CompleteReported = $false"))
    p.append(("J_nulls",
        "  $bomInfo = @{}\n  $watchStatus = @{}",
        "  $bomInfo = @{}\n  $watchStatus = @{}\n"
        "  $longTableAudit = $null; $attribAudit = $null; $p49Audit = $null"))

    # ---- K: call sites ----
    p.append(("K_calls",
        "    # ---------- CSV dual hash + quick scan ----------\n"
        "    $dualHash = Get-DualHash $csvPath\n"
        "    $quickScan = Get-QuickScan $csvPath\n",
        "    # ---------- CSV dual hash + quick scan ----------\n"
        "    $dualHash = Get-DualHash $csvPath\n"
        "    $quickScan = Get-QuickScan $csvPath\n\n"
        "    # ---------- EXT: long-table integrity + exchange binding + P49 artifact audit ----------\n"
        "    $longTableAudit = Get-LongTableAudit $csvPath\n"
        "    $attribAudit = Get-ExchangeAttributionAudit\n"
        "    $p49Audit = Get-P49Audit $prevP49\n"
        "    $prevP49 = $p49Audit.state_snapshot\n"))

    # ---- L: warnings ----
    WARN_BLOCK = (
        "    # ---------- EXT: long-table + exchange + P49 warnings (record only) ----------\n"
        "    foreach ($b in $longTableAudit.symbol_exchange_bindings) {\n"
        "      if ($b.verdict -eq 'MISMATCH') {\n"
        "        $warnList += @{code = 'EXCH-001-MISMATCH'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('CSV symbol ' + $b.symbol + ' :: ' + $b.detail)}\n"
        "      } elseif ($b.verdict -eq 'UNKNOWN_EXCHANGE') {\n"
        "        $warnList += @{code = 'EXCH-001-UNKNOWN-EXCHANGE'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('CSV symbol ' + $b.symbol + ' :: ' + $b.detail)}\n"
        "      }\n"
        "    }\n"
        "    foreach ($m in $attribAudit.mismatches) {\n"
        "      $warnList += @{code = 'EXCH-001-ATTRIBUTED-MISMATCH'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('DSHC artifact references ' + $m.symbol + ' (' + $m.verdict + ') :: ' + $m.detail + '; no_data_present=' + $m.no_data_present_in_files + '; files=' + ($m.files -join ',') + '; observation only, no intervention')}\n"
        "    }\n"
        "    if ($longTableAudit.duplicate_key_count -gt 0) {\n"
        "      $warnList += @{code = 'CSVINT-001-DUP-KEY'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('long-table duplicate primary keys (date|symbol|indicator) = ' + $longTableAudit.duplicate_key_count + '; samples=' + ($longTableAudit.duplicate_key_samples -join ';') + '; observation only')}\n"
        "    }\n"
        "    if (($longTableAudit.malformed_row_count -gt 0) -or ($longTableAudit.blank_key_field_count -gt 0) -or ($longTableAudit.bad_date_count -gt 0) -or ($longTableAudit.non_numeric_value_count -gt 0)) {\n"
        "      $warnList += @{code = 'CSVINT-001-STRUCTURE'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('malformed_rows=' + $longTableAudit.malformed_row_count + '; blank_key_fields=' + $longTableAudit.blank_key_field_count + '; bad_dates=' + $longTableAudit.bad_date_count + '; non_numeric_values=' + $longTableAudit.non_numeric_value_count + '; observation only')}\n"
        "    }\n"
        "    foreach ($s in $longTableAudit.symbols_not_whitelisted) {\n"
        "      $warnList += @{code = 'CSVINT-002-SYMBOL-NOT-WHITELISTED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('symbol ' + $s + ' is outside the DSHD whitelist: ' + ($csvSymbolWhitelist -join ','))}\n"
        "    }\n"
        "    if ($longTableAudit.indicators_missing.Count -gt 0) {\n"
        "      $warnList += @{code = 'CSVINT-003-INDICATOR-MISSING'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('expected indicator absent from long table: ' + ($longTableAudit.indicators_missing -join ','))}\n"
        "    }\n"
        "    if ($longTableAudit.indicators_unexpected.Count -gt 0) {\n"
        "      $warnList += @{code = 'CSVINT-003-INDICATOR-UNEXPECTED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('unexpected indicator present in long table: ' + ($longTableAudit.indicators_unexpected -join ','))}\n"
        "    }\n"
        "    if ($p49Audit.missing_files.Count -gt 0) {\n"
        "      $warnList += @{code = 'P49-001-ARTIFACT-MISSING'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('artifacts/p49_backtest missing expected file(s): ' + ($p49Audit.missing_files -join ','))}\n"
        "    }\n"
        "    if ($p49Audit.removed_files.Count -gt 0) {\n"
        "      $warnList += @{code = 'P49-001-ARTIFACT-REMOVED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('artifacts/p49_backtest file(s) removed since last poll: ' + ($p49Audit.removed_files -join ','))}\n"
        "    }\n"
        "    if ($p49Audit.hash_changed_files.Count -gt 0) {\n"
        "      $warnList += @{code = 'P49-001-HASH-CHANGED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('artifacts/p49_backtest hash change since last poll: ' + ($p49Audit.hash_changed_files -join ',') + '; read-only audit, no intervention')}\n"
        "    }\n"
        "    if ($p49Audit.under_min_size_files.Count -gt 0) {\n"
        "      $warnList += @{code = 'P49-001-FILE-BENEATH-MIN-SIZE'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('p49 artifact beneath ' + $p49MinFileSize + 'B: ' + ($p49Audit.under_min_size_files -join ',') + '; observation only')}\n"
        "    }\n"
        "    if ($p49Audit.exchange_column_mismatch_count -gt 0) {\n"
        "      $warnList += @{code = 'P49-001-EXCHANGE-COL-MISMATCH'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('p49 symbol_performance.csv exchange column disagrees with the symbol suffix on ' + $p49Audit.exchange_column_mismatch_count + ' row(s); observation only')}\n"
        "    }\n")
    p.append(("L_warnings",
        "    if ($quickScan.blank_alarm) {\n"
        "      $warnList += @{code = 'A01_CSV_BLANK_RUN'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('max consecutive blank lines = ' + $quickScan.max_consecutive_blank)}\n"
        "    }\n",
        "    if ($quickScan.blank_alarm) {\n"
        "      $warnList += @{code = 'A01_CSV_BLANK_RUN'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('max consecutive blank lines = ' + $quickScan.max_consecutive_blank)}\n"
        "    }\n" + WARN_BLOCK))

    # ---- M: cluster board fields ----
    p.append(("M_cluster",
        "      dual_hash = $dualHash\n"
        "      quick_scan = $quickScan\n"
        "      gate_state = $trackState",
        "      dual_hash = $dualHash\n"
        "      quick_scan = $quickScan\n"
        "      long_table_audit = $longTableAudit\n"
        "      exchange_binding_audit = $attribAudit\n"
        "      p49_artifact_audit = $p49Audit\n"
        "      exchange_field_check = 'ON'\n"
        "      p49_artifact_audit_on = $true\n"
        "      p49_read_only = $true\n"
        "      gate_state = $trackState"))
    p.append(("M_deliverables_cluster",
        "        'artifacts/dshd_p81_warning_board.json'\n"
        "      )\n"
        "    }\n"
        "    Write-Utf8File $outCluster (($cluster | ConvertTo-Json -Depth 14))",
        "        'artifacts/dshd_p81_warning_board.json',\n"
        "        'artifacts/dshd_p81_ext_longtable_exchange_audit.json',\n"
        "        'artifacts/dshd_p81_ext_p49_artifact_audit.json'\n"
        "      )\n"
        "    }\n"
        "    Write-Utf8File $outCluster (($cluster | ConvertTo-Json -Depth 14))"))

    # ---- N: write EXT outputs (after quick scan write) ----
    p.append(("N_write_ext",
        "    Write-Utf8File $outQuickScan (($qsOut | ConvertTo-Json -Depth 12))\n",
        "    Write-Utf8File $outQuickScan (($qsOut | ConvertTo-Json -Depth 12))\n\n"
        "    # ---------- EXT: write long-table + exchange audit ----------\n"
        "    $ltOut = @{\n"
        "      verification_type = 'LONG_TABLE_INTEGRITY_AND_EXCHANGE_BINDING'\n"
        "      task = $extTaskName\n"
        "      a01_tag = $a01Tag\n"
        "      agent = $agentName\n"
        "      token = $extTokenName\n"
        "      token_state = $tokenState\n"
        "      branch = $branch\n"
        "      timestamp = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')\n"
        "      poll_count = $pollNo\n"
        "      csv_path = 'output_sample/wdf_sample_metals_raw.csv'\n"
        "      csv_sha256 = $dualHash.hash_a_byte_read\n"
        "      csv_bytes = $quickScan.size_bytes\n"
        "      csv_data_rows = $quickScan.data_rows\n"
        "      exchange_field_check = 'ON'\n"
        "      exchange_suffixes_known = $exchangeSuffixes\n"
        "      exchange_registry_product_count = $productExchange.Count\n"
        "      symbol_whitelist = $csvSymbolWhitelist\n"
        "      symbol_watchlist = $csvSymbolWatchlist\n"
        "      indicator_expected = $csvIndicatorExpected\n"
        "      long_table_audit = $longTableAudit\n"
        "      attribution_audit = $attribAudit\n"
        "      audit_only = $true\n"
        "      intervention = 'NONE'\n"
        "      action_taken = 'RECORD_ONLY'\n"
        "    }\n"
        "    Write-Utf8File $outLongTable (($ltOut | ConvertTo-Json -Depth 14))\n"
        "    $p49Out = @{\n"
        "      verification_type = 'P49_BACKTEST_ARTIFACT_READ_ONLY_AUDIT'\n"
        "      task = $extTaskName\n"
        "      a01_tag = $a01Tag\n"
        "      agent = $agentName\n"
        "      token = $extTokenName\n"
        "      token_state = $tokenState\n"
        "      branch = $branch\n"
        "      timestamp = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')\n"
        "      poll_count = $pollNo\n"
        "      p49_artifact_audit = $p49Audit\n"
        "      audit_only = $true\n"
        "      read_only = $true\n"
        "      dshd_wrote_p49_artifact = $false\n"
        "      dshd_modified_p49_artifact = $false\n"
        "      dshd_ran_backtest = $false\n"
        "      intervention = 'NONE'\n"
        "      action_taken = 'RECORD_ONLY'\n"
        "    }\n"
        "    Write-Utf8File $outP49 (($p49Out | ConvertTo-Json -Depth 14))\n"))

    # ---- O: board rule_ids ----
    p.append(("O_board_rules",
        "      rule_ids = @('OBS-SPAWN-EXCEL-001','OBS-SPAWN-EXCEL-001-TRANSIENT','A01_HASH_MISMATCH_WARNING','CONCURRENT_WRITE_CONFLICT','A01_CSV_BLANK_RUN')",
        "      rule_ids = @('OBS-SPAWN-EXCEL-001','OBS-SPAWN-EXCEL-001-TRANSIENT','A01_HASH_MISMATCH_WARNING','CONCURRENT_WRITE_CONFLICT','A01_CSV_BLANK_RUN','EXCH-001-MISMATCH','EXCH-001-UNKNOWN-EXCHANGE','EXCH-001-ATTRIBUTED-MISMATCH','CSVINT-001-DUP-KEY','CSVINT-001-STRUCTURE','CSVINT-002-SYMBOL-NOT-WHITELISTED','CSVINT-003-INDICATOR-MISSING','CSVINT-003-INDICATOR-UNEXPECTED','P49-001-ARTIFACT-MISSING','P49-001-ARTIFACT-REMOVED','P49-001-HASH-CHANGED','P49-001-FILE-BENEATH-MIN-SIZE','P49-001-EXCHANGE-COL-MISMATCH')"))

    # ---- P: brief signature ----
    p.append(("P_brief_sig",
        "  param($SnapTs, $Agents, $ExcelRule, $TerritoryState, $DualHash, $QuickScan, $WarnList, $P0Checks, $P0Pass, $P0Total, $RedLines)",
        "  param($SnapTs, $Agents, $ExcelRule, $TerritoryState, $DualHash, $QuickScan, $WarnList, $P0Checks, $P0Pass, $P0Total, $RedLines, $LongTableAudit, $ExchangeAudit, $P49Audit)"))

    # ---- Q: brief new sections (before head_p0) ----
    BRIEF_NEW = (
        "  Add-BriefLine $L ''\n"
        "  Add-BriefLine $L $zh['head_exch']\n"
        "  Add-BriefLine $L ''\n"
        "  Add-BriefLine $L '| 指标 | 值 |'\n"
        "  Add-BriefLine $L '|---|---|'\n"
        "  $r = ('| 校验模式 | ' + $LongTableAudit.mode + ' (auto_intervene=' + $LongTableAudit.auto_intervene + ') |')\n"
        "  Add-BriefLine $L $r\n"
        "  $r = ('| 表格式 | ' + $LongTableAudit.format + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  $r = ('| 数据行数 | ' + $LongTableAudit.data_rows + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  $r = '| 主键 | date + symbol + indicator |'\n"
        "  Add-BriefLine $L $r\n"
        "  $r = ('| 主键重复数 | ' + $LongTableAudit.duplicate_key_count + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  $r = ('| 结构缺陷 (malformed / blank_key / bad_date / non_numeric) | ' + $LongTableAudit.malformed_row_count + ' / ' + $LongTableAudit.blank_key_field_count + ' / ' + $LongTableAudit.bad_date_count + ' / ' + $LongTableAudit.non_numeric_value_count + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  $r = ('| 日期区间 | ' + $LongTableAudit.date_min + ' -> ' + $LongTableAudit.date_max + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  $r = ('| 品种数 / 指标数 / 来源数 | ' + $LongTableAudit.distinct_symbol_count + ' / ' + $LongTableAudit.distinct_indicator_count + ' / ' + $LongTableAudit.distinct_source_count + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  $r = ('| 指标列表 | ' + ($LongTableAudit.indicators -join ', ') + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  $wlVio = '无'\n"
        "  if ($LongTableAudit.symbols_not_whitelisted.Count -gt 0) { $wlVio = ($LongTableAudit.symbols_not_whitelisted -join ',') }\n"
        "  $r = ('| 白名单外品种 | ' + $wlVio + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  $indMiss = '无'\n"
        "  if ($LongTableAudit.indicators_missing.Count -gt 0) { $indMiss = ($LongTableAudit.indicators_missing -join ',') }\n"
        "  $r = ('| 缺失指标 | ' + $indMiss + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  $r = ('| 交易所归属不匹配 / 未知交易所 | ' + $LongTableAudit.exchange_mismatch_count + ' / ' + $LongTableAudit.exchange_unknown_count + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  $r = ('| 长表审计结论 | ' + $LongTableAudit.audit_status + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  Add-BriefLine $L ''\n"
        "  Add-BriefLine $L '| 品种 | 实际交易所 | 应属交易所 | 结论 |'\n"
        "  Add-BriefLine $L '|---|---|---|---|'\n"
        "  $bindRows = @()\n"
        "  foreach ($b in $LongTableAudit.symbol_exchange_bindings) {\n"
        "    $r = ('| ' + $b.symbol + ' | ' + $b.actual_exchange + ' | ' + $b.expected_exchange + ' | ' + $b.verdict + ' |')\n"
        "    $bindRows += $r\n"
        "  }\n"
        "  Add-BriefLine $L ([string]::Join(\"`n\", $bindRows))\n"
        "  Add-BriefLine $L ''\n"
        "  $r = ('DSHC 归属档案扫描: 文件 ' + $ExchangeAudit.files_scanned + ' 个; 命中品种令牌 ' + $ExchangeAudit.symbol_tokens_total + ' 个; 交易所归属异常 ' + $ExchangeAudit.mismatch_count + ' 个')\n"
        "  Add-BriefLine $L $r\n"
        "  $amRows = @()\n"
        "  foreach ($m in $ExchangeAudit.mismatches) {\n"
        "    $r = ('- [' + $m.verdict + '] ' + $m.symbol + ' :: ' + $m.detail + ' :: NO_DATA=' + $m.no_data_present_in_files + ' :: files=' + ($m.files -join ','))\n"
        "    $amRows += $r\n"
        "  }\n"
        "  if ($amRows.Count -gt 0) { Add-BriefLine $L ([string]::Join(\"`n\", $amRows)) }\n"
        "  Add-BriefLine $L ''\n"
        "  Add-BriefLine $L $zh['head_p49']\n"
        "  Add-BriefLine $L ''\n"
        "  Add-BriefLine $L '| 指标 | 值 |'\n"
        "  Add-BriefLine $L '|---|---|'\n"
        "  $r = ('| 审计模式 | 只读 (' + $P49Audit.mode + ', auto_intervene=' + $P49Audit.auto_intervene + ') |')\n"
        "  Add-BriefLine $L $r\n"
        "  $r = ('| 目录存在 | ' + $P49Audit.exists + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  $r = ('| 文件数 / 期望数 / 总字节 | ' + $P49Audit.file_count + ' / ' + $P49Audit.expected_file_count + ' / ' + $P49Audit.total_bytes + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  $r = ('| MANIFEST 状态 | ' + $P49Audit.manifest_status + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  $r = ('| MANIFEST gate / release_permit | ' + $P49Audit.manifest_gate + ' / ' + $P49Audit.manifest_release_permit + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  $r = ('| MANIFEST LC_GFE | ' + $P49Audit.manifest_lc_gfe + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  $r = ('| wind_api_calls / real_wind_call | ' + $P49Audit.manifest_wind_api_calls + ' / ' + $P49Audit.manifest_real_wind_call + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  $p49Miss = '无'\n"
        "  if ($P49Audit.missing_files.Count -gt 0) { $p49Miss = ($P49Audit.missing_files -join ',') }\n"
        "  $r = ('| 缺失产物 | ' + $p49Miss + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  $p49Chg = '无'\n"
        "  if ($P49Audit.hash_changed_files.Count -gt 0) { $p49Chg = ($P49Audit.hash_changed_files -join ',') }\n"
        "  $r = ('| 本轮哈希变更 | ' + $p49Chg + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  $r = ('| exchange 列与品种后缀不一致行数 | ' + $P49Audit.exchange_column_mismatch_count + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  $r = ('| P49 审计结论 | ' + $P49Audit.audit_status + ' |')\n"
        "  Add-BriefLine $L $r\n"
        "  Add-BriefLine $L ''\n"
        "  Add-BriefLine $L '| 产物 | 字节 | SHA256 | 本轮变化 |'\n"
        "  Add-BriefLine $L '|---|---|---|---|'\n"
        "  $p49Rows = @()\n"
        "  foreach ($f in $P49Audit.files) {\n"
        "    $h = [string]$f.sha256\n"
        "    if ($h.Length -gt 16) { $h = $h.Substring(0, 16) + '...' }\n"
        "    $r = ('| ' + $f.relative_path + ' | ' + $f.size_bytes + ' | ' + $h + ' | ' + $f.change + ' |')\n"
        "    $p49Rows += $r\n"
        "  }\n"
        "  Add-BriefLine $L ([string]::Join(\"`n\", $p49Rows))\n"
        "  Add-BriefLine $L ''\n")
    p.append(("Q_brief_sections",
        "  Add-BriefLine $L ''\n"
        "  Add-BriefLine $L $zh['head_p0']\n"
        "  Add-BriefLine $L ''",
        BRIEF_NEW + "  Add-BriefLine $L ''\n"
        "  Add-BriefLine $L $zh['head_p0']\n"
        "  Add-BriefLine $L ''"))

    # ---- R: brief call site ----
    p.append(("R_brief_call",
        "    $brief = Write-ClusterBrief $pollTs $agents $excelRule $territoryState $dualHash $quickScan $warnList $p0Checks $p0Pass $p0Total $redLines",
        "    $brief = Write-ClusterBrief $pollTs $agents $excelRule $territoryState $dualHash $quickScan $warnList $p0Checks $p0Pass $p0Total $redLines $longTableAudit $attribAudit $p49Audit"))

    # ---- S: snapshot fields ----
    p.append(("S_snapshot",
        "      dual_hash = $dualHash\n"
        "      quick_scan = $quickScan\n"
        "      csv_evidence = @{",
        "      dual_hash = $dualHash\n"
        "      quick_scan = $quickScan\n"
        "      long_table_audit = $longTableAudit\n"
        "      exchange_binding_audit = $attribAudit\n"
        "      p49_artifact_audit = $p49Audit\n"
        "      exchange_field_check = 'ON'\n"
        "      p49_artifact_audit_on = $true\n"
        "      p49_read_only = $true\n"
        "      csv_evidence = @{"))
    p.append(("S_snap_deliverables",
        "        'artifacts/dshd_p81_warning_board.json'\n"
        "      )\n"
        "    }\n"
        "    Write-Utf8File $outSnapshot (($snap | ConvertTo-Json -Depth 14))",
        "        'artifacts/dshd_p81_warning_board.json',\n"
        "        'artifacts/dshd_p81_ext_longtable_exchange_audit.json',\n"
        "        'artifacts/dshd_p81_ext_p49_artifact_audit.json'\n"
        "      )\n"
        "    }\n"
        "    Write-Utf8File $outSnapshot (($snap | ConvertTo-Json -Depth 14))"))

    # ---- T: poll event fields ----
    p.append(("T_event",
        "      csv_quick_scan_status = $quickScan.scan_status\n"
        "      hash_mismatch = $dualHash.warning_raised",
        "      csv_quick_scan_status = $quickScan.scan_status\n"
        "      ext_token = $extTokenName\n"
        "      ext_task = $extTaskName\n"
        "      exchange_field_check = 'ON'\n"
        "      long_table_format = $longTableAudit.format\n"
        "      long_table_audit_status = $longTableAudit.audit_status\n"
        "      long_table_data_rows = $longTableAudit.data_rows\n"
        "      long_table_duplicate_keys = $longTableAudit.duplicate_key_count\n"
        "      long_table_malformed_rows = $longTableAudit.malformed_row_count\n"
        "      long_table_blank_key_fields = $longTableAudit.blank_key_field_count\n"
        "      long_table_bad_dates = $longTableAudit.bad_date_count\n"
        "      long_table_non_numeric_values = $longTableAudit.non_numeric_value_count\n"
        "      long_table_symbols = $longTableAudit.distinct_symbol_count\n"
        "      long_table_indicators = $longTableAudit.distinct_indicator_count\n"
        "      exchange_bound_ok = $longTableAudit.exchange_ok_count\n"
        "      exchange_mismatch_count = $longTableAudit.exchange_mismatch_count\n"
        "      exchange_unknown_count = $longTableAudit.exchange_unknown_count\n"
        "      exchange_attrib_files_scanned = $attribAudit.files_scanned\n"
        "      exchange_attrib_mismatch_count = $attribAudit.mismatch_count\n"
        "      symbol_whitelist_violations = $longTableAudit.symbols_not_whitelisted.Count\n"
        "      indicator_missing_count = $longTableAudit.indicators_missing.Count\n"
        "      p49_artifact_audit_on = $true\n"
        "      p49_read_only = $true\n"
        "      p49_dir_exists = $p49Audit.exists\n"
        "      p49_file_count = $p49Audit.file_count\n"
        "      p49_total_bytes = $p49Audit.total_bytes\n"
        "      p49_manifest_status = $p49Audit.manifest_status\n"
        "      p49_manifest_lc_gfe = $p49Audit.manifest_lc_gfe\n"
        "      p49_audit_status = $p49Audit.audit_status\n"
        "      p49_missing_files = $p49Audit.missing_files.Count\n"
        "      p49_removed_files = $p49Audit.removed_files.Count\n"
        "      p49_hash_changed_files = $p49Audit.hash_changed_files.Count\n"
        "      p49_exchange_column_mismatches = $p49Audit.exchange_column_mismatch_count\n"
        "      hash_mismatch = $dualHash.warning_raised"))

    # ---- U: one-shot P49 completion audit event ----
    P49_EVT = (
        "    # ---------- EXT: one-shot P49 backtest completion audit event ----------\n"
        "    if (($p49Audit.exists -eq $true) -and ($p49CompleteReported -eq $false) -and ($p49Audit.manifest_status -match 'BACKTEST_COMPLETE')) {\n"
        "      $p49CompleteReported = $true\n"
        "      $p49Evt = @{\n"
        "        timestamp = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')\n"
        "        event = 'DSHD-P81-EXT-P49-BACKTEST-COMPLETE-OBSERVED-00001'\n"
        "        event_type = 'p49_backtest_complete_observed'\n"
        "        agent = $agentName\n"
        "        task = $extTaskName\n"
        "        a01_tag = $a01Tag\n"
        "        token = $extTokenName\n"
        "        token_state = $tokenState\n"
        "        branch = $branch\n"
        "        poll_count = $pollNo\n"
        "        mode = 'AUDIT_READ_ONLY'\n"
        "        audit_only = $true\n"
        "        intervention = 'NONE'\n"
        "        no_kill_executed = $true\n"
        "        p49_archive_id = $p49Audit.manifest_archive_id\n"
        "        p49_manifest_agent = $p49Audit.manifest_agent\n"
        "        p49_manifest_token = $p49Audit.manifest_token\n"
        "        p49_manifest_status = $p49Audit.manifest_status\n"
        "        p49_manifest_gate = $p49Audit.manifest_gate\n"
        "        p49_manifest_release_permit = $p49Audit.manifest_release_permit\n"
        "        p49_manifest_lc_gfe = $p49Audit.manifest_lc_gfe\n"
        "        p49_manifest_symbols_run = $p49Audit.manifest_symbols_run\n"
        "        p49_manifest_wind_api_calls = $p49Audit.manifest_wind_api_calls\n"
        "        p49_manifest_real_wind_call = $p49Audit.manifest_real_wind_call\n"
        "        p49_manifest_offline_only = $p49Audit.manifest_offline_only\n"
        "        p49_manifest_csv_not_modified = $p49Audit.manifest_csv_not_modified\n"
        "        p49_dir = 'artifacts/p49_backtest'\n"
        "        p49_file_count = $p49Audit.file_count\n"
        "        p49_total_bytes = $p49Audit.total_bytes\n"
        "        p49_files = $p49Audit.files\n"
        "        p49_missing_files = $p49Audit.missing_files\n"
        "        p49_unexpected_files = $p49Audit.unexpected_files\n"
        "        p49_hash_changed_files = $p49Audit.hash_changed_files\n"
        "        p49_sha256_snapshot = $p49Audit.state_snapshot\n"
        "        p49_audit_status = $p49Audit.audit_status\n"
        "        p49_read_only_audit = $true\n"
        "        p49_wrote_anything = $false\n"
        "        dshd_ran_backtest = $false\n"
        "        dshd_modified_backtest_artifact = $false\n"
        "        dshd_bypasses_dsha_p68 = $false\n"
        "        dshd_fetches_for_dshc = $false\n"
        "        p0_all_pass = $p0AllPass\n"
        "        p0_checks_passed = $p0Pass\n"
        "        p0_checks_total = $p0Total\n"
        "        gate = $trackState.gate\n"
        "        release_permit = $trackState.release_permit\n"
        "        wind_api_calls = $trackState.wind_api_calls\n"
        "        circuit_breaker_ready = $false\n"
        "        circuit_breaker_executed = $false\n"
        "      }\n"
        "      Add-AuditEvent $auditLog $p49Evt\n"
        "      Write-Host ('[EXT] P49 BACKTEST COMPLETE OBSERVED | archive=' + $p49Audit.manifest_archive_id + ' files=' + $p49Audit.file_count + ' bytes=' + $p49Audit.total_bytes + ' snapshot=' + $p49Audit.state_snapshot.Count + ' status=' + $p49Audit.audit_status + ' audit_only=YES intervention=NONE')\n"
        "    }\n")
    p.append(("U_p49_event",
        "    Add-AuditEvent $auditLog $evt\n",
        "    Add-AuditEvent $auditLog $evt\n" + P49_EVT))

    # ---- V: Write-Host EXT line ----
    p.append(("V_who",
        "$dualHash.scan_status, $warnList.Count, $elapsedMs)",
        "$dualHash.scan_status, $warnList.Count, $elapsedMs)\n"
        "    Write-Host (\"[{0}] POLL {1:D3} EXT | longtable={2} rows={3} dup={4} malformed={5} badkey={6} baddate={7} nonnum={8} | syms={9} ind={10} | exch_ok={11} exch_mismatch={12} exch_unknown={13} attr_exch={14} | whitelist_vio={15} ind_miss={16} | p49={17} files={18} miss={19} chg={20} {21}\" -f (Get-Date).ToString('HH:mm:ss'), $pollNo, $longTableAudit.audit_status, $longTableAudit.data_rows, $longTableAudit.duplicate_key_count, $longTableAudit.malformed_row_count, $longTableAudit.blank_key_field_count, $longTableAudit.bad_date_count, $longTableAudit.non_numeric_value_count, $longTableAudit.distinct_symbol_count, $longTableAudit.distinct_indicator_count, $longTableAudit.exchange_ok_count, $longTableAudit.exchange_mismatch_count, $longTableAudit.exchange_unknown_count, $attribAudit.mismatch_count, $longTableAudit.symbols_not_whitelisted.Count, $longTableAudit.indicators_missing.Count, $p49Audit.exists, $p49Audit.file_count, $p49Audit.missing_files.Count, $p49Audit.hash_changed_files.Count, $p49Audit.audit_status)"))

    return p


def main():
    with io.open(GEN, 'r', encoding='utf-8') as f:
        src = f.read()
    orig = src
    for name, old, new in patches():
        n = src.count(old)
        if n != 1:
            print("ABORT: patch %s matched %d times (expected 1)" % (name, n))
            sys.exit(1)
        src = src.replace(old, new)
        print("applied %s" % name)
    with io.open(GEN, 'w', encoding='utf-8', newline='') as f:
        f.write(src)
    print("generator rewritten: %d -> %d chars" % (len(orig), len(src)))


if __name__ == '__main__':
    main()
