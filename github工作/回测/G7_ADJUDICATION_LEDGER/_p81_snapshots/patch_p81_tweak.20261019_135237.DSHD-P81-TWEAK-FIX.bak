# -*- coding: utf-8 -*-
# patch_p81_tweak.py  -  DSHD-P81-TWEAK  (token DSHD-P81-TWEAK-TOKEN)
#
# 31 exact string replacements applied to recreate_p81.py (single source of
# truth generator for dshd_p81_watch.ps1).
#
#   1. quick_scan row-count alignment: data_rows excludes the CSV header,
#      matching long_table_audit. Legacy value kept as
#      data_rows_legacy_header_inclusive for back-trace.
#   2a. P49 post-seal mutation detector: once MANIFEST.status marks the
#       archive COMPLETE, any add / modify / delete / undeclared /
#       declared-missing entry raises P49-001-ARTIFACT-UNEXPECTED
#       continuously (warning_board.json + audit ledger).
#   2b. FACTOR_EXTRACT_V1 skill dir full-file hash snapshot monitor for
#       artifacts/skill_lib/factor_v1/.
#   4.  Exchange binding auto-clear contract for LC.SHF / LC.GFE.
#   3.  Everything else (exchange check, long-table integrity, 20s Excel fast
#       sampling, 5min main poll) untouched.
#
# The generator is BARE LF -> read/write with newline=''.
# NOT idempotent: aborts on any mismatch.

import io
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, 'recreate_p81.py')

P = []
def _dedent(s, n):
    if n == 0:
        return s
    return '\n'.join((l[n:] if len(l) >= n and l[:n] == ' ' * n else l)
                     for l in s.split('\n'))
def patch(pid, old, new, n=1, s=0):
    P.append((pid, _dedent(old, s), _dedent(new, s), n))

# ---------------------------------------------------------------- A: version
patch('A_version',
    "  $scriptVersion             = '1.1.0-EXT'",
    "  $scriptVersion             = '1.2.0-TWEAK'", s=2)

# --------------------------------------------------------------- B: tokens
patch('B_token',
    "  $extTokenName               = 'DSHD-P81-EXT-TOKEN'\n"
    "  $extTaskName                = 'DSHD-P81-EXT'",
    "  $extTokenName               = 'DSHD-P81-EXT-TOKEN'\n"
    "  $extTaskName                = 'DSHD-P81-EXT'\n"
    "  $tweakTokenName             = 'DSHD-P81-TWEAK-TOKEN'\n"
    "  $tweakTaskName              = 'DSHD-P81-TWEAK'", s=2)

# --------------------------------------------------- C: skill dir constants
patch('C_skilldir_path',
    "  $p49Dir                    = $artDir + '\\p49_backtest'",
    "  $p49Dir                    = $artDir + '\\p49_backtest'\n"
    "  $skillDir                  = $artDir + '\\skill_lib\\factor_v1'\n"
    "  $skillManifestPath         = $skillDir + '\\manifest.json'", s=2)

# ------------------------------------------------------ D: output path
patch('D_skilldir_outpath',
    "  $outP49                    = $artDir + '\\dshd_p81_ext_p49_artifact_audit.json'",
    "  $outP49                    = $artDir + '\\dshd_p81_ext_p49_artifact_audit.json'\n"
    "  $outSkill                  = $artDir + '\\dshd_p81_tweak_skill_audit.json'", s=2)

# --------------------------------------------- E: monitored paths +6 skill
patch('E_skilldir_monitored',
    "  @{p = $csvLongTwin;                                              owner = 'DSHA';              shared = $false}\n"
    ")",
    "  @{p = $csvLongTwin;                                              owner = 'DSHA';              shared = $false}\n"
    "  @{p = $skillDir + '\\manifest.json';                             owner = 'DSHC-SKILL-FACTOR01'; shared = $false}\n"
    "  @{p = $skillDir + '\\factor_extract_v1.py';                      owner = 'DSHC-SKILL-FACTOR01'; shared = $false}\n"
    "  @{p = $skillDir + '\\factor_definitions.json';                   owner = 'DSHC-SKILL-FACTOR01'; shared = $false}\n"
    "  @{p = $skillDir + '\\generate_aligned_csv.py';                   owner = 'DSHC-SKILL-FACTOR01'; shared = $false}\n"
    "  @{p = $skillDir + '\\data_sha256.txt';                           owner = 'DSHC-SKILL-FACTOR01'; shared = $false}\n"
    "  @{p = $skillDir + '\\README.md';                                 owner = 'DSHC-SKILL-FACTOR01'; shared = $false}\n"
    ")")

# --------------------------------------------------------- F1: brief sub
patch('F1_zh_sub',
    "  sub          = '\u9886\u5730\u5951\u7ea6\u56fa\u5316 \u00b7 Excel \u6f02\u79fb\u89c2\u6d4b\u5668 \u00b7 \u4ea4\u6613\u6240\u5f52\u5c5e\u6821\u9a8c \u00b7 P49 \u4ea7\u7269\u53ea\u8bfb\u5ba1\u8ba1'",
    "  sub          = '\u9886\u5730\u5951\u7ea6\u56fa\u5316 \u00b7 Excel \u6f02\u79fb\u89c2\u6d4b\u5668 \u00b7 \u4ea4\u6613\u6240\u5f52\u5c5e\u6821\u9a8c \u00b7 P49 \u4ea7\u7269\u53ea\u8bfb\u5ba1\u8ba1 \u00b7 Skill \u76ee\u5f55\u54c8\u5e0c\u76d1\u63a7'")

# ------------------------------------------------- F2: brief section heads
patch('F2_zh_heads',
    "  head_p49     = '\u4e03\u3001P49 \u56de\u6d4b\u4ea7\u7269\u53ea\u8bfb\u5ba1\u8ba1'\n"
    "  head_p0      = '\u516b\u3001P0 \u6821\u9a8c'\n"
    "  head_red     = '\u4e5d\u3001\u7ea2\u7ebf\u786e\u8ba4'",
    "  head_p49     = '\u4e03\u3001P49 \u56de\u6d4b\u4ea7\u7269\u53ea\u8bfb\u5ba1\u8ba1'\n"
    "  head_skill   = '\u516b\u3001FACTOR_EXTRACT_V1 Skill \u76ee\u5f55\u54c8\u5e0c\u76d1\u63a7'\n"
    "  head_p0      = '\u4e5d\u3001P0 \u6821\u9a8c'\n"
    "  head_red     = '\u5341\u3001\u7ea2\u7ebf\u786e\u8ba4'")

# --------------------------------------------------- G1: quick scan counters
patch('G1_quickscan_init',
    "  $exists = (Test-Path $CsvPath)\n"
    "  $size = 0; $roughLines = 0; $dataRows = 0\n"
    "  $maxBlank = 0; $header = ''; $headerCols = @()",
    "  $exists = (Test-Path $CsvPath)\n"
    "  $size = 0; $roughLines = 0; $dataRows = 0; $dataRowsHeaderInclusive = 0\n"
    "  $maxBlank = 0; $header = ''; $headerCols = @()\n"
    "  $rowCountConvention = 'DATA_ONLY_V2'")

# ---------------------------------------------- G2: quick scan header skip
patch('G2_quickscan_header_skip',
    "      } else {\n"
    "        $curBlank = 0\n"
    "        $dataRows++\n"
    "      }\n"
    "    }\n"
    "    if ($roughLines -ge 1) { $header = [string]$lines[0] }\n"
    "    if ($header.Length -gt 0) { $headerCols = @($header.Split(',')) }\n"
    "  }",
    "      } else {\n"
    "        $curBlank = 0\n"
    "        $dataRowsHeaderInclusive++\n"
    "      }\n"
    "    }\n"
    "    if ($roughLines -ge 1) { $header = [string]$lines[0] }\n"
    "    if ($header.Length -gt 0) { $headerCols = @($header.Split(',')) }\n"
    "  }\n"
    "  # TWEAK (DSHD-P81-TWEAK): row-count convention alignment.\n"
    "  # V1 legacy (kept for back-trace): every non-blank line counted as a data\n"
    "  #   row, which INCLUDES the CSV header. Observed 7363 for the 2026-10-19\n"
    "  #   long-format sample = 7362 data rows + 1 header line.\n"
    "  # V2 current (authoritative): the header line is excluded, so\n"
    "  #   quick_scan.data_rows == long_table_audit.data_rows == 7362.\n"
    "  # Both values are emitted so a v1 consumer can reproduce the old number.\n"
    "  $headerLineCount = 0\n"
    "  if ($header.Length -gt 0) { $headerLineCount = 1 }\n"
    "  $dataRows = $dataRowsHeaderInclusive - $headerLineCount")

# -------------------------------------------------- G3: quick scan return
patch('G3_quickscan_return',
    "    data_rows = $dataRows\n"
    "    header = $header",
    "    data_rows = $dataRows\n"
    "    data_rows_convention = $rowCountConvention\n"
    "    data_rows_legacy_header_inclusive = $dataRowsHeaderInclusive\n"
    "    header_line_count = $headerLineCount\n"
    "    header = $header")

# --------------------------------------------- H: p49 post-seal init fields
patch('H_p49_postseal_init',
    "    manifest_last_write = ''\n"
    "    total_bytes = 0",
    "    manifest_last_write = ''\n"
    "    manifest_sealed = $false\n"
    "    manifest_sealed_at = ''\n"
    "    post_seal_mutation = $false\n"
    "    post_seal_mutation_kinds = @()\n"
    "    post_seal_mutation_kinds_count = 0\n"
    "    post_seal_archive_modify_alert = $false\n"
    "    cold_start = ($null -eq $PrevState)\n"
    "    total_bytes = 0")

# ------------------------------------------- I: p49 post-seal computation
patch('I_p49_postseal_compute',
    "  $out.exchange_column_mismatch_count = $exMismatch\n"
    "  $out.state_snapshot = $curMap\n"
    "  if (($out.missing_files.Count -gt 0) -or ($out.removed_files.Count -gt 0)) { $out.audit_status = 'P49_ARTIFACT_SET_INCOMPLETE' }",
    "  $out.exchange_column_mismatch_count = $exMismatch\n"
    "  $out.state_snapshot = $curMap\n"
    "  # TWEAK (DSHD-P81-TWEAK): post-seal archive mutation detector.\n"
    "  # Once MANIFEST.status marks the archive COMPLETE (sealed), ANY add /\n"
    "  # modify / delete / undeclared / declared-missing entry inside the\n"
    "  # directory is a post-seal mutation. It raises the\n"
    "  # P49-001-ARTIFACT-UNEXPECTED umbrella label every poll until the\n"
    "  # archive is re-sealed clean. Granular codes (HASH-CHANGED /\n"
    "  # ARTIFACT-MISSING / ARTIFACT-REMOVED) keep firing alongside for detail.\n"
    "  # On a cold start (no previous snapshot) ADDED / REMOVED are suppressed\n"
    "  # because every file trivially looks new; undeclared and declared-missing\n"
    "  # entries are MANIFEST-derived and remain meaningful.\n"
    "  if ($out.manifest_status -match 'COMPLETE') {\n"
    "    $out.manifest_sealed = $true\n"
    "    $out.manifest_sealed_at = $out.manifest_last_write\n"
    "  }\n"
    "  if ($out.manifest_sealed) {\n"
    "    $kinds = @()\n"
    "    if ($out.unexpected_files.Count -gt 0) { $kinds += 'ADDED_UNDECLARED' }\n"
    "    if ((-not $out.cold_start) -and ($out.added_files.Count -gt 0)) { $kinds += 'ADDED' }\n"
    "    if ($out.hash_changed_files.Count -gt 0) { $kinds += 'MODIFIED' }\n"
    "    if ((-not $out.cold_start) -and ($out.removed_files.Count -gt 0)) { $kinds += 'REMOVED' }\n"
    "    if ($out.missing_files.Count -gt 0) { $kinds += 'DECLARED_MISSING' }\n"
    "    if ($kinds.Count -gt 0) {\n"
    "      $out.post_seal_mutation = $true\n"
    "      $out.post_seal_mutation_kinds = $kinds\n"
    "      $out.post_seal_archive_modify_alert = $true\n"
    "    }\n"
    "  }\n"
    "  $out.post_seal_mutation_kinds_count = $out.post_seal_mutation_kinds.Count\n"
    "  if ($out.post_seal_archive_modify_alert) { $out.audit_status = 'P49_POSTSEAL_MUTATION' }\n"
    "  elseif (($out.missing_files.Count -gt 0) -or ($out.removed_files.Count -gt 0)) { $out.audit_status = 'P49_ARTIFACT_SET_INCOMPLETE' }")

# ------------------------------------------- J: new Get-SkillDirAudit fn
patch('J_skilldir_fn',
    "function Get-TerritoryState {",
    "function Get-SkillDirAudit {\n"
    "  param($PrevState)\n"
    "  $dir = $skillDir\n"
    "  $out = @{\n"
    "    check = 'FACTOR_EXTRACT_V1_SKILL_DIR_HASH_AUDIT'\n"
    "    dir = 'artifacts/skill_lib/factor_v1'\n"
    "    mode = 'OBSERVATION_ONLY'\n"
    "    read_only = $true\n"
    "    wrote_anything = $false\n"
    "    auto_intervene = $false\n"
    "    exists = $false\n"
    "    file_count = 0\n"
    "    total_bytes = [long]0\n"
    "    manifest_path = 'artifacts/skill_lib/factor_v1/manifest.json'\n"
    "    manifest_readable = $false\n"
    "    manifest_last_write = ''\n"
    "    manifest_sha256 = ''\n"
    "    manifest_hash_changed = $false\n"
    "    declared_count = 0\n"
    "    declared_files = @()\n"
    "    undeclared_files = @()\n"
    "    declared_missing_files = @()\n"
    "    files = @()\n"
    "    added_files = @()\n"
    "    modified_files = @()\n"
    "    removed_files = @()\n"
    "    skill_id = ''\n"
    "    version = ''\n"
    "    previous_version = ''\n"
    "    skill_version_changed = $false\n"
    "    version_locked = $false\n"
    "    status = ''\n"
    "    locked_at = ''\n"
    "    locked_by = ''\n"
    "    skill_token = ''\n"
    "    skill_baseline = ''\n"
    "    iteration_policy = ''\n"
    "    next_version = ''\n"
    "    constraint_wind_api_calls = 0\n"
    "    constraint_offline_only = $false\n"
    "    constraint_f01_script_locked = $false\n"
    "    constraint_f01_script_version = ''\n"
    "    constraint_f01_script_params_only = $false\n"
    "    data_integrity_aligned_sha256 = ''\n"
    "    data_integrity_aligned_rows = 0\n"
    "    data_integrity_original_sha256 = ''\n"
    "    data_integrity_unique_dates = 0\n"
    "    original_csv_sha256_actual = ''\n"
    "    original_csv_sha256_match = $false\n"
    "    v1_frozen_violation = $false\n"
    "    v1_frozen_violation_files = @()\n"
    "    cold_start = ($null -eq $PrevState)\n"
    "    state_snapshot = @{}\n"
    "    audit_status = 'SKILL_ABSENT'\n"
    "    intervention = 'NONE'\n"
    "  }\n"
    "  if (-not (Test-Path $dir)) { return $out }\n"
    "  $out.exists = $true\n"
    "  $prevMap = @{}\n"
    "  if ($null -ne $PrevState) { foreach ($k in $PrevState.Keys) { $prevMap[$k] = $PrevState[$k] } }\n"
    "  $prevManifestHash = ''\n"
    "  $prevVersion = ''\n"
    "  if ($prevMap.ContainsKey('__META__manifest_sha256')) { $prevManifestHash = [string]$prevMap['__META__manifest_sha256'] }\n"
    "  if ($prevMap.ContainsKey('__META__version')) { $prevVersion = [string]$prevMap['__META__version'] }\n"
    "  $manifestPath = $dir + '\\manifest.json'\n"
    "  $declared = @()\n"
    "  if (Test-Path $manifestPath) {\n"
    "    try { $out.manifest_last_write = (Get-Item $manifestPath).LastWriteTime.ToString('yyyy-MM-ddTHH:mm:sszzz') } catch { }\n"
    "    $mh = Get-FileSha256 $manifestPath\n"
    "    if ($null -ne $mh) { $out.manifest_sha256 = $mh }\n"
    "    $m = Get-JsonSafe $manifestPath\n"
    "    if ($null -ne $m) {\n"
    "      $out.manifest_readable = $true\n"
    "      $out.skill_id = [string](Get-JsonProp $m 'skill_id' '')\n"
    "      $out.version = [string](Get-JsonProp $m 'version' '')\n"
    "      $out.version_locked = [bool](Get-JsonProp $m 'version_locked' $false)\n"
    "      $out.status = [string](Get-JsonProp $m 'status' '')\n"
    "      $out.locked_at = [string](Get-JsonProp $m 'locked_at' '')\n"
    "      $out.locked_by = [string](Get-JsonProp $m 'locked_by' '')\n"
    "      $out.skill_token = [string](Get-JsonProp $m 'token' '')\n"
    "      $out.skill_baseline = [string](Get-JsonProp $m 'baseline' '')\n"
    "      $out.iteration_policy = [string](Get-JsonProp $m 'iteration_policy' '')\n"
    "      $out.next_version = [string](Get-JsonProp $m 'next_version' '')\n"
    "      $cs = Get-JsonProp $m 'constraints' @{}\n"
    "      $out.constraint_wind_api_calls = [long](Get-JsonProp $cs 'wind_api_calls' 0)\n"
    "      $out.constraint_offline_only = [bool](Get-JsonProp $cs 'offline_only' $false)\n"
    "      $out.constraint_f01_script_locked = [bool](Get-JsonProp $cs 'f01_script_locked' $false)\n"
    "      $out.constraint_f01_script_version = [string](Get-JsonProp $cs 'f01_script_version' '')\n"
    "      $out.constraint_f01_script_params_only = [bool](Get-JsonProp $cs 'f01_script_params_only' $false)\n"
    "      $di = Get-JsonProp $m 'data_integrity' @{}\n"
    "      $out.data_integrity_aligned_sha256 = [string](Get-JsonProp $di 'aligned_csv_sha256' '')\n"
    "      $out.data_integrity_aligned_rows = [long](Get-JsonProp $di 'aligned_csv_rows' 0)\n"
    "      $out.data_integrity_original_sha256 = [string](Get-JsonProp $di 'original_csv_sha256' '')\n"
    "      $out.data_integrity_unique_dates = [long](Get-JsonProp $di 'unique_dates' 0)\n"
    "      $dl = Get-JsonProp $m 'files' @()\n"
    "      foreach ($df in $dl) {\n"
    "        $dn = [string](Get-JsonProp $df 'name' '')\n"
    "        if ($dn.Length -gt 0) { $declared += $dn; $out.declared_files += $dn }\n"
    "      }\n"
    "    }\n"
    "  }\n"
    "  $out.declared_count = $declared.Count\n"
    "  $out.previous_version = $prevVersion\n"
    "  if (($prevVersion.Length -gt 0) -and ($out.version -ne $prevVersion)) { $out.skill_version_changed = $true }\n"
    "  if (($prevManifestHash.Length -gt 0) -and ($out.manifest_sha256 -ne $prevManifestHash)) { $out.manifest_hash_changed = $true }\n"
    "  $ach = Get-FileSha256 $csvPath\n"
    "  if ($null -ne $ach) { $out.original_csv_sha256_actual = $ach }\n"
    "  if (($out.data_integrity_original_sha256.Length -gt 0) -and ($out.original_csv_sha256_actual.Length -gt 0)) {\n"
    "    $out.original_csv_sha256_match = ([string]$out.data_integrity_original_sha256).ToUpper().Equals(([string]$out.original_csv_sha256_actual).ToUpper())\n"
    "  }\n"
    "  $items = @(Get-ChildItem $dir -File -Recurse -ErrorAction SilentlyContinue)\n"
    "  $out.file_count = $items.Count\n"
    "  $curMap = @{}\n"
    "  $totalBytes = [long]0\n"
    "  $frozenViolations = @()\n"
    "  foreach ($it in $items) {\n"
    "    $rel = [string]$it.FullName\n"
    "    if ($rel.Length -gt $dir.Length) { $rel = $rel.Substring($dir.Length).TrimStart('\\\\') }\n"
    "    $sz = [long]$it.Length\n"
    "    $hash = ''\n"
    "    try { $hash = (Get-FileHash $it.FullName -Algorithm SHA256).Hash } catch { }\n"
    "    $isDeclared = $false\n"
    "    foreach ($e in $declared) { if ($e -eq $it.Name) { $isDeclared = $true } }\n"
    "    $changed = 'NEW'\n"
    "    if ($prevMap.ContainsKey($rel)) {\n"
    "      if ([string]$prevMap[$rel] -eq $hash) { $changed = 'UNCHANGED' }\n"
    "      else {\n"
    "        $changed = 'MODIFIED'\n"
    "        $out.modified_files += $rel\n"
    "        if ($isDeclared -and ($out.version_locked -eq $true)) { $frozenViolations += $rel }\n"
    "      }\n"
    "    } else {\n"
    "      $out.added_files += $rel\n"
    "    }\n"
    "    $row = @{relative_path = $rel; name = $it.Name; size_bytes = $sz; sha256 = $hash; last_write = $it.LastWriteTime.ToString('yyyy-MM-ddTHH:mm:sszzz'); declared = $isDeclared; change = $changed}\n"
    "    $out.files += $row\n"
    "    if (-not $isDeclared) { $out.undeclared_files += $rel }\n"
    "    $curMap[$rel] = $hash\n"
    "    $totalBytes += $sz\n"
    "  }\n"
    "  foreach ($k in $prevMap.Keys) {\n"
    "    if ([string]$k -like '__META__*') { continue }\n"
    "    if (-not $curMap.ContainsKey($k)) { $out.removed_files += $k }\n"
    "  }\n"
    "  foreach ($e in $declared) {\n"
    "    $found = $false\n"
    "    foreach ($f in $items) { if ($f.Name -eq $e) { $found = $true } }\n"
    "    if (-not $found) { $out.declared_missing_files += $e }\n"
    "  }\n"
    "  $out.total_bytes = $totalBytes\n"
    "  $out.v1_frozen_violation_files = $frozenViolations\n"
    "  $out.v1_frozen_violation = ($frozenViolations.Count -gt 0)\n"
    "  $curMap['__META__manifest_sha256'] = $out.manifest_sha256\n"
    "  $curMap['__META__version'] = $out.version\n"
    "  $out.state_snapshot = $curMap\n"
    "  if ($out.v1_frozen_violation) { $out.audit_status = 'SKILL_V1_FROZEN_VIOLATION' }\n"
    "  elseif (($out.modified_files.Count -gt 0) -or ($out.added_files.Count -gt 0) -or ($out.removed_files.Count -gt 0)) { $out.audit_status = 'SKILL_DIR_CHANGED' }\n"
    "  elseif ($out.manifest_hash_changed -or $out.skill_version_changed) { $out.audit_status = 'SKILL_MANIFEST_CHANGED' }\n"
    "  elseif ($out.declared_missing_files.Count -gt 0) { $out.audit_status = 'SKILL_DECLARED_MISSING' }\n"
    "  elseif ($out.undeclared_files.Count -gt 0) { $out.audit_status = 'SKILL_UNDECLARED_FILE' }\n"
    "  elseif ($out.status -match 'VERSION_LOCKED') { $out.audit_status = 'SKILL_VERSION_LOCKED_INTEGRITY_OK' }\n"
    "  else { $out.audit_status = 'SKILL_PRESENT_PARTIAL' }\n"
    "  return $out\n"
    "}\n"
    "\n"
    "function Get-TerritoryState {")

# ----------------------------------- K1: exchange audit auto-clear fields
patch('K1_exch_init',
    "    audit_status = 'ATTRIBUTION_EXCHANGE_CLEAN'\n"
    "    intervention = 'NONE'\n"
    "  }",
    "    audit_status = 'ATTRIBUTION_EXCHANGE_CLEAN'\n"
    "    intervention = 'NONE'\n"
    "    auto_clear_enabled = $true\n"
    "    lc_shf_verdict = ''\n"
    "    lc_shf_expected_exchange = ''\n"
    "    lc_gfe_verdict = ''\n"
    "    lc_gfe_expected_exchange = ''\n"
    "    lc_binding_repaired = $false\n"
    "    lc_repaired_via = ''\n"
    "  }")

# ----------------------------------------- K2: exchange audit LC verdicts
patch('K2_exch_lc_verdicts',
    "  if ($out.mismatch_count -gt 0) { $out.audit_status = 'ATTRIBUTED_EXCHANGE_ANOMALY' }\n"
    "  return $out\n"
    "}\n"
    "\n"
    "function Get-P49Audit {",
    "  # TWEAK (DSHD-P81-TWEAK): exchange binding auto-clear contract for LC.\n"
    "  # LC.SHF and LC.GFE are re-tested every poll. The binding is considered\n"
    "  # REPAIRED when LC.SHF is no longer among the mismatches AND LC.GFE now\n"
    "  # resolves as BOUND_OK. The EXCH-001-* labels are emitted conditionally\n"
    "  # from mismatch_count, so they drop off of warning_board.json\n"
    "  # automatically the moment DSHC fixes its config; the loop-side CLEARED\n"
    "  # event makes the transition itself auditable in the ledger.\n"
    "  $bShf = Test-ExchangeBinding 'LC.SHF'\n"
    "  $bGfe = Test-ExchangeBinding 'LC.GFE'\n"
    "  $out.lc_shf_verdict = $bShf.verdict\n"
    "  $out.lc_shf_expected_exchange = $bShf.expected_exchange\n"
    "  $out.lc_gfe_verdict = $bGfe.verdict\n"
    "  $out.lc_gfe_expected_exchange = $bGfe.expected_exchange\n"
    "  $lcShfStillBad = $false\n"
    "  foreach ($mm in $out.mismatches) {\n"
    "    if ($mm.symbol -eq 'LC.SHF') { $lcShfStillBad = $true }\n"
    "  }\n"
    "  if ((-not $lcShfStillBad) -and ($bGfe.verdict -eq 'BOUND_OK')) {\n"
    "    $out.lc_binding_repaired = $true\n"
    "    $out.lc_repaired_via = ('LC.GFE -> ' + $bGfe.expected_exchange + ' (BOUND_OK)')\n"
    "  }\n"
    "  if ($out.mismatch_count -gt 0) { $out.audit_status = 'ATTRIBUTED_EXCHANGE_ANOMALY' }\n"
    "  return $out\n"
    "}\n"
    "\n"
    "function Get-P49Audit {")

# --------------------------------------------------- L: script init vars
patch('L_init_vars',
    "  $prevP49 = $null\n"
    "  $p49CompleteReported = $false",
    "  $prevP49 = $null\n"
    "  $prevSkill = $null\n"
    "  $p49CompleteReported = $false\n"
    "  $p49PostSealFirstReported = $false\n"
    "  $p49PostSealMutationPolls = 0\n"
    "  $skillFirstReported = $false\n"
    "  $exchPrevMismatchCount = -1\n"
    "  $exchClearedReported = $false", s=2)

# ----------------------------------------------- M: per-poll null resets
patch('M_nulls',
    "    $longTableAudit = $null; $attribAudit = $null; $p49Audit = $null",
    "    $longTableAudit = $null; $attribAudit = $null; $p49Audit = $null; $skillAudit = $null", s=2)

# ---------------------------------------------------- N: per-poll calls
patch('N_calls',
    "    $p49Audit = Get-P49Audit $prevP49\n"
    "    $prevP49 = $p49Audit.state_snapshot",
    "    $p49Audit = Get-P49Audit $prevP49\n"
    "    $prevP49 = $p49Audit.state_snapshot\n"
    "    $skillAudit = Get-SkillDirAudit $prevSkill\n"
    "    $prevSkill = $skillAudit.state_snapshot\n"
    "    if ($p49Audit.post_seal_archive_modify_alert -eq $true) { $p49PostSealMutationPolls = ([int]$p49PostSealMutationPolls) + 1 } else { $p49PostSealMutationPolls = 0 }")

# ------------------------- O: warnings (umbrella + skill + cleared)
patch('O_warnings',
    "    if ($p49Audit.unexpected_files.Count -gt 0) {\n"
    "      $warnList += @{code = 'P49-001-ARTIFACT-UNEXPECTED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('artifacts/p49_backtest contains file(s) not in the declared expected set: ' + ($p49Audit.unexpected_files -join ',') + '; observation only, no intervention')}\n"
    "    }",
    "    # TWEAK (DSHD-P81-TWEAK): umbrella post-seal mutation label. Fires\n"
    "    # every poll for as long as the COMPLETE-sealed archive keeps\n"
    "    # mutating; the granular codes above carry the per-kind detail.\n"
    "    # Recorded to warning_board.json and to the audit ledger.\n"
    "    if ($p49Audit.post_seal_archive_modify_alert -eq $true) {\n"
    "      $warnList += @{code = 'P49-001-ARTIFACT-UNEXPECTED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('P49 archive sealed (MANIFEST.status=' + $p49Audit.manifest_status + ' at ' + $p49Audit.manifest_sealed_at + ') but mutated post-seal: kinds=' + ($p49Audit.post_seal_mutation_kinds -join ',') + '; continuous_alert_polls=' + $p49PostSealMutationPolls + '; cold_start=' + $p49Audit.cold_start + '; undeclared=' + ($p49Audit.unexpected_files -join ',') + '; modified=' + ($p49Audit.hash_changed_files -join ',') + '; removed=' + ($p49Audit.removed_files -join ',') + '; declared_missing=' + ($p49Audit.missing_files -join ',') + '; observation only, no intervention')}\n"
    "    } elseif ($p49Audit.unexpected_files.Count -gt 0) {\n"
    "      $warnList += @{code = 'P49-001-ARTIFACT-UNEXPECTED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('artifacts/p49_backtest contains file(s) not in the declared expected set: ' + ($p49Audit.unexpected_files -join ',') + '; observation only, no intervention')}\n"
    "    }\n"
    "    # ---------- TWEAK: FACTOR_EXTRACT_V1 skill dir hash warnings ----------\n"
    "    if ($skillAudit.exists -eq $false) {\n"
    "      $warnList += @{code = 'SKILL-001-DIR-ABSENT'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('artifacts/skill_lib/factor_v1 is absent; skill version monitoring idle; observation only')}\n"
    "    } else {\n"
    "      if ($skillAudit.skill_version_changed -eq $true) {\n"
    "        $warnList += @{code = 'SKILL-001-VERSION-CHANGED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('FACTOR_EXTRACT_V1 version changed from ' + $skillAudit.previous_version + ' to ' + $skillAudit.version + '; manifest.status=' + $skillAudit.status + '; observation only, no intervention')}\n"
    "      }\n"
    "      if ($skillAudit.manifest_hash_changed -eq $true) {\n"
    "        $warnList += @{code = 'SKILL-001-MANIFEST-CHANGED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('skill manifest.json hash changed (sha256=' + $skillAudit.manifest_sha256 + '); version=' + $skillAudit.version + '; version_locked=' + $skillAudit.version_locked + '; observation only')}\n"
    "      }\n"
    "      if ($skillAudit.v1_frozen_violation -eq $true) {\n"
    "        $warnList += @{code = 'SKILL-001-V1-FROZEN-VIOLATION'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('version_locked=true but declared V1 file(s) modified in place: ' + ($skillAudit.v1_frozen_violation_files -join ',') + '; iteration_policy=' + $skillAudit.iteration_policy + '; observation only, no intervention')}\n"
    "      }\n"
    "      if (($skillAudit.cold_start -eq $false) -and ($skillAudit.modified_files.Count -gt 0)) {\n"
    "        $warnList += @{code = 'SKILL-001-FILE-MODIFIED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('skill dir hash change since last poll: ' + ($skillAudit.modified_files -join ',') + '; read-only audit, no intervention')}\n"
    "      }\n"
    "      if (($skillAudit.cold_start -eq $false) -and ($skillAudit.added_files.Count -gt 0)) {\n"
    "        $warnList += @{code = 'SKILL-001-FILE-ADDED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('skill dir file(s) added since last poll: ' + ($skillAudit.added_files -join ',') + '; observation only')}\n"
    "      }\n"
    "      if (($skillAudit.cold_start -eq $false) -and ($skillAudit.removed_files.Count -gt 0)) {\n"
    "        $warnList += @{code = 'SKILL-001-FILE-REMOVED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('skill dir file(s) removed since last poll: ' + ($skillAudit.removed_files -join ',') + '; observation only')}\n"
    "      }\n"
    "      if ($skillAudit.undeclared_files.Count -gt 0) {\n"
    "        $warnList += @{code = 'SKILL-001-FILE-UNDECLARED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('skill dir contains file(s) not declared in manifest.json: ' + ($skillAudit.undeclared_files -join ',') + '; declared_count=' + $skillAudit.declared_count + '; observation only')}\n"
    "      }\n"
    "      if ($skillAudit.declared_missing_files.Count -gt 0) {\n"
    "        $warnList += @{code = 'SKILL-001-FILE-DECLARED-MISSING'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('manifest.json declares file(s) absent from the skill dir: ' + ($skillAudit.declared_missing_files -join ',') + '; observation only')}\n"
    "      }\n"
    "      if (($skillAudit.data_integrity_original_sha256.Length -gt 0) -and ($skillAudit.original_csv_sha256_match -eq $false)) {\n"
    "        $warnList += @{code = 'SKILL-001-DATA-SHA-MISMATCH'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('manifest data_integrity.original_csv_sha256=' + $skillAudit.data_integrity_original_sha256 + ' vs actual_csv_sha256=' + $skillAudit.original_csv_sha256_actual + '; observation only')}\n"
    "      }\n"
    "    }\n"
    "    # ---------- TWEAK: exchange binding auto-clear transition ----------\n"
    "    if (($exchPrevMismatchCount -gt 0) -and ($attribAudit.mismatch_count -eq 0)) {\n"
    "      $exchClearedReported = $true\n"
    "      $warnList += @{code = 'EXCH-001-ATTRIBUTED-MISMATCH-CLEARED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('DSHC exchange binding repaired: attributed mismatch count went ' + $exchPrevMismatchCount + ' -> 0; EXCH-001-MISMATCH / EXCH-001-ATTRIBUTED-MISMATCH labels auto-cleared from the board; LC.SHF verdict=' + $attribAudit.lc_shf_verdict + '; LC.GFE verdict=' + $attribAudit.lc_gfe_verdict + '; repaired=' + $attribAudit.lc_binding_repaired + '; observation only')}\n"
    "    }")

# ------------------------------- O2: persist previous mismatch count
patch('O2_exch_prev',
    "    # ---------- P0 checks ----------\n"
    "    $chk = @{\n",
    "    $exchPrevMismatchCount = $attribAudit.mismatch_count\n"
    "    # ---------- P0 checks ----------\n"
    "    $chk = @{\n")

# ----------------------------------------------- P: cluster board fields
patch('P_cluster_fields',
    "      p49_artifact_audit = $p49Audit\n"
    "      exchange_field_check = 'ON'\n"
    "      p49_artifact_audit_on = $true\n"
    "      p49_read_only = $true\n"
    "      gate_state = $trackState",
    "      p49_artifact_audit = $p49Audit\n"
    "      skill_dir_audit = $skillAudit\n"
    "      exchange_field_check = 'ON'\n"
    "      p49_artifact_audit_on = $true\n"
    "      p49_read_only = $true\n"
    "      skill_dir_hash_monitor_on = $true\n"
    "      skill_dir_read_only = $true\n"
    "      tweak_token = $tweakTokenName\n"
    "      tweak_task = $tweakTaskName\n"
    "      row_count_convention = $quickScan.data_rows_convention\n"
    "      gate_state = $trackState")

# ------------------------------------------------ Q: deliverables (x2)
patch('Q_deliverables',
    "        'artifacts/dshd_p81_ext_p49_artifact_audit.json'\n"
    "      )",
    "        'artifacts/dshd_p81_ext_p49_artifact_audit.json',\n"
    "        'artifacts/dshd_p81_tweak_skill_audit.json'\n"
    "      )",
    n=2)

# ------------------------------------------ R: warning board rule_ids
patch('R_board_rule_ids',
    "      rule_ids = @('OBS-SPAWN-EXCEL-001','OBS-SPAWN-EXCEL-001-TRANSIENT','A01_HASH_MISMATCH_WARNING','CONCURRENT_WRITE_CONFLICT','A01_CSV_BLANK_RUN','EXCH-001-MISMATCH','EXCH-001-UNKNOWN-EXCHANGE','EXCH-001-ATTRIBUTED-MISMATCH','CSVINT-001-DUP-KEY','CSVINT-001-STRUCTURE','CSVINT-002-SYMBOL-NOT-WHITELISTED','CSVINT-003-INDICATOR-MISSING','CSVINT-003-INDICATOR-UNEXPECTED','P49-001-ARTIFACT-MISSING','P49-001-ARTIFACT-REMOVED','P49-001-HASH-CHANGED','P49-001-FILE-BENEATH-MIN-SIZE','P49-001-EXCHANGE-COL-MISMATCH','P49-001-ARTIFACT-UNEXPECTED')",
    "      rule_ids = @('OBS-SPAWN-EXCEL-001','OBS-SPAWN-EXCEL-001-TRANSIENT','A01_HASH_MISMATCH_WARNING','CONCURRENT_WRITE_CONFLICT','A01_CSV_BLANK_RUN','EXCH-001-MISMATCH','EXCH-001-UNKNOWN-EXCHANGE','EXCH-001-ATTRIBUTED-MISMATCH','EXCH-001-ATTRIBUTED-MISMATCH-CLEARED','CSVINT-001-DUP-KEY','CSVINT-001-STRUCTURE','CSVINT-002-SYMBOL-NOT-WHITELISTED','CSVINT-003-INDICATOR-MISSING','CSVINT-003-INDICATOR-UNEXPECTED','P49-001-ARTIFACT-MISSING','P49-001-ARTIFACT-REMOVED','P49-001-HASH-CHANGED','P49-001-FILE-BENEATH-MIN-SIZE','P49-001-EXCHANGE-COL-MISMATCH','P49-001-ARTIFACT-UNEXPECTED','SKILL-001-DIR-ABSENT','SKILL-001-VERSION-CHANGED','SKILL-001-MANIFEST-CHANGED','SKILL-001-V1-FROZEN-VIOLATION','SKILL-001-FILE-MODIFIED','SKILL-001-FILE-ADDED','SKILL-001-FILE-REMOVED','SKILL-001-FILE-UNDECLARED','SKILL-001-FILE-DECLARED-MISSING','SKILL-001-DATA-SHA-MISMATCH')")

# ---------------------------------------------- S: skill audit writer
patch('S_skill_writer',
    "    Write-Utf8File $outP49 (($p49Out | ConvertTo-Json -Depth 14))",
    "    Write-Utf8File $outP49 (($p49Out | ConvertTo-Json -Depth 14))\n"
    "    $skillOut = @{\n"
    "      verification_type = 'FACTOR_EXTRACT_V1_SKILL_DIR_HASH_AUDIT'\n"
    "      task = $tweakTaskName\n"
    "      a01_tag = $a01Tag\n"
    "      agent = $agentName\n"
    "      token = $tweakTokenName\n"
    "      token_state = $tokenState\n"
    "      branch = $branch\n"
    "      timestamp = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')\n"
    "      poll_count = $pollNo\n"
    "      skill_dir_audit = $skillAudit\n"
    "      audit_only = $true\n"
    "      read_only = $true\n"
    "      dshd_wrote_skill_artifact = $false\n"
    "      dshd_modified_skill_artifact = $false\n"
    "      dshd_unlocked_skill_version = $false\n"
    "      intervention = 'NONE'\n"
    "      action_taken = 'RECORD_ONLY'\n"
    "    }\n"
    "    Write-Utf8File $outSkill (($skillOut | ConvertTo-Json -Depth 14))")

# ----------------------------------------------- T: snapshot fields
patch('T_snapshot_fields',
    "      p49_artifact_audit = $p49Audit\n"
    "      exchange_field_check = 'ON'\n"
    "      p49_artifact_audit_on = $true\n"
    "      p49_read_only = $true\n"
    "      csv_evidence = @{\n",
    "      p49_artifact_audit = $p49Audit\n"
    "      skill_dir_audit = $skillAudit\n"
    "      exchange_field_check = 'ON'\n"
    "      p49_artifact_audit_on = $true\n"
    "      p49_read_only = $true\n"
    "      skill_dir_hash_monitor_on = $true\n"
    "      skill_dir_read_only = $true\n"
    "      tweak_token = $tweakTokenName\n"
    "      tweak_task = $tweakTaskName\n"
    "      row_count_convention = $quickScan.data_rows_convention\n"
    "      csv_evidence = @{\n")

# ----------------------------------------------- U: poll event fields
patch('U_event_fields',
    "      p49_exchange_column_mismatches = $p49Audit.exchange_column_mismatch_count",
    "      p49_exchange_column_mismatches = $p49Audit.exchange_column_mismatch_count\n"
    "      p49_manifest_sealed = $p49Audit.manifest_sealed\n"
    "      p49_manifest_sealed_at = $p49Audit.manifest_sealed_at\n"
    "      p49_post_seal_mutation = $p49Audit.post_seal_mutation\n"
    "      p49_post_seal_mutation_kinds = $p49Audit.post_seal_mutation_kinds\n"
    "      p49_post_seal_archive_modify_alert = $p49Audit.post_seal_archive_modify_alert\n"
    "      p49_post_seal_alert_polls = $p49PostSealMutationPolls\n"
    "      p49_cold_start = $p49Audit.cold_start\n"
    "      tweak_token = $tweakTokenName\n"
    "      tweak_task = $tweakTaskName\n"
    "      row_count_convention = $quickScan.data_rows_convention\n"
    "      csv_data_rows_legacy_header_inclusive = $quickScan.data_rows_legacy_header_inclusive\n"
    "      csv_header_line_count = $quickScan.header_line_count\n"
    "      exchange_attrib_lc_shf_verdict = $attribAudit.lc_shf_verdict\n"
    "      exchange_attrib_lc_gfe_verdict = $attribAudit.lc_gfe_verdict\n"
    "      exchange_attrib_lc_binding_repaired = $attribAudit.lc_binding_repaired\n"
    "      exchange_attrib_auto_clear_enabled = $attribAudit.auto_clear_enabled\n"
    "      skill_dir_hash_monitor_on = $true\n"
    "      skill_dir_read_only = $true\n"
    "      skill_dir_exists = $skillAudit.exists\n"
    "      skill_dir_file_count = $skillAudit.file_count\n"
    "      skill_dir_total_bytes = $skillAudit.total_bytes\n"
    "      skill_dir_skill_id = $skillAudit.skill_id\n"
    "      skill_dir_version = $skillAudit.version\n"
    "      skill_dir_previous_version = $skillAudit.previous_version\n"
    "      skill_dir_version_locked = $skillAudit.version_locked\n"
    "      skill_dir_status = $skillAudit.status\n"
    "      skill_dir_manifest_sha256 = $skillAudit.manifest_sha256\n"
    "      skill_dir_manifest_hash_changed = $skillAudit.manifest_hash_changed\n"
    "      skill_dir_version_changed = $skillAudit.skill_version_changed\n"
    "      skill_dir_declared_count = $skillAudit.declared_count\n"
    "      skill_dir_undeclared_files = $skillAudit.undeclared_files.Count\n"
    "      skill_dir_declared_missing_files = $skillAudit.declared_missing_files.Count\n"
    "      skill_dir_files_added = $skillAudit.added_files.Count\n"
    "      skill_dir_files_modified = $skillAudit.modified_files.Count\n"
    "      skill_dir_files_removed = $skillAudit.removed_files.Count\n"
    "      skill_dir_v1_frozen_violation = $skillAudit.v1_frozen_violation\n"
    "      skill_dir_data_sha_match = $skillAudit.original_csv_sha256_match\n"
    "      skill_dir_audit_status = $skillAudit.audit_status")

# -------------------------------------------- V/W: brief signature + call
patch('V_brief_signature',
    "  param($SnapTs, $Agents, $ExcelRule, $TerritoryState, $DualHash, $QuickScan, $WarnList, $P0Checks, $P0Pass, $P0Total, $RedLines, $LongTableAudit, $ExchangeAudit, $P49Audit)",
    "  param($SnapTs, $Agents, $ExcelRule, $TerritoryState, $DualHash, $QuickScan, $WarnList, $P0Checks, $P0Pass, $P0Total, $RedLines, $LongTableAudit, $ExchangeAudit, $P49Audit, $SkillAudit)")

patch('W_brief_call',
    "    $brief = Write-ClusterBrief $pollTs $agents $excelRule $territoryState $dualHash $quickScan $warnList $p0Checks $p0Pass $p0Total $redLines $longTableAudit $attribAudit $p49Audit",
    "    $brief = Write-ClusterBrief $pollTs $agents $excelRule $territoryState $dualHash $quickScan $warnList $p0Checks $p0Pass $p0Total $redLines $longTableAudit $attribAudit $p49Audit $skillAudit")

# --------------------------------------------- X: brief skill section
patch('X_brief_skill_section',
    "  Add-BriefLine $L ([string]::Join(\"`n\", $p49Rows))\n"
    "  Add-BriefLine $L ''\n"
    "  Add-BriefLine $L ''\n"
    "  Add-BriefLine $L $zh['head_p0']",
    "  Add-BriefLine $L ([string]::Join(\"`n\", $p49Rows))\n"
    "  Add-BriefLine $L ''\n"
    "  Add-BriefLine $L ''\n"
    "  Add-BriefLine $L $zh['head_skill']\n"
    "  Add-BriefLine $L ''\n"
    "  Add-BriefLine $L '| \u6307\u6807 | \u503c |'\n"
    "  Add-BriefLine $L '|---|---|'\n"
    "  $r = ('| \u5ba1\u8ba1\u6a21\u5f0f | \u53ea\u8bfb (' + $SkillAudit.mode + ', auto_intervene=' + $SkillAudit.auto_intervene + ') |')\n"
    "  Add-BriefLine $L $r\n"
    "  $r = ('| \u76ee\u5f55\u5b58\u5728 | ' + $SkillAudit.exists + ' |')\n"
    "  Add-BriefLine $L $r\n"
    "  $r = ('| \u6587\u4ef6\u6570 / \u603b\u5b57\u8282 / manifest \u58f0\u660e\u6570 | ' + $SkillAudit.file_count + ' / ' + $SkillAudit.total_bytes + ' / ' + $SkillAudit.declared_count + ' |')\n"
    "  Add-BriefLine $L $r\n"
    "  $r = ('| skill_id / version | ' + $SkillAudit.skill_id + ' / ' + $SkillAudit.version + ' |')\n"
    "  Add-BriefLine $L $r\n"
    "  $r = ('| version_locked / status | ' + $SkillAudit.version_locked + ' / ' + $SkillAudit.status + ' |')\n"
    "  Add-BriefLine $L $r\n"
    "  $r = ('| locked_at / locked_by | ' + $SkillAudit.locked_at + ' / ' + $SkillAudit.locked_by + ' |')\n"
    "  Add-BriefLine $L $r\n"
    "  $r = ('| manifest \u6700\u540e\u5199\u5165 | ' + $SkillAudit.manifest_last_write + ' (readable=' + $SkillAudit.manifest_readable + ') |')\n"
    "  Add-BriefLine $L $r\n"
    "  $h0 = [string]$SkillAudit.manifest_sha256\n"
    "  if ($h0.Length -gt 16) { $h0 = $h0.Substring(0, 16) + '...' }\n"
    "  $r = ('| manifest SHA256 | ' + $h0 + ' (\u672c\u8f6e\u53d8\u66f4=' + $SkillAudit.manifest_hash_changed + ') |')\n"
    "  Add-BriefLine $L $r\n"
    "  $r = ('| version \u53d8\u66f4 | ' + $SkillAudit.previous_version + ' -> ' + $SkillAudit.version + ' (changed=' + $SkillAudit.skill_version_changed + ') |')\n"
    "  Add-BriefLine $L $r\n"
    "  $r = ('| \u58f0\u660e\u5916\u6587\u4ef6 / \u58f0\u660e\u7f3a\u5931 | ' + $SkillAudit.undeclared_files.Count + ' / ' + $SkillAudit.declared_missing_files.Count + ' |')\n"
    "  Add-BriefLine $L $r\n"
    "  $r = ('| \u672c\u8f6e \u65b0\u589e / \u4fee\u6539 / \u5220\u9664 (cold_start=' + $SkillAudit.cold_start + ') | ' + $skillAudit.added_files.Count + ' / ' + $SkillAudit.modified_files.Count + ' / ' + $SkillAudit.removed_files.Count + ' |')\n"
    "  Add-BriefLine $L $r\n"
    "  $r = ('| V1 \u51bb\u7ed3\u8fdd\u89c4 | ' + $SkillAudit.v1_frozen_violation + ' |')\n"
    "  Add-BriefLine $L $r\n"
    "  $r = ('| constraint wind_api_calls / offline_only | ' + $SkillAudit.constraint_wind_api_calls + ' / ' + $SkillAudit.constraint_offline_only + ' |')\n"
    "  Add-BriefLine $L $r\n"
    "  $r = ('| f01_script_locked / f01_script_version | ' + $SkillAudit.constraint_f01_script_locked + ' / ' + $SkillAudit.constraint_f01_script_version + ' |')\n"
    "  Add-BriefLine $L $r\n"
    "  $r = ('| manifest original_csv_sha256 \u4e0e\u5b9e\u9645 CSV \u4e00\u81f4 | ' + $SkillAudit.original_csv_sha256_match + ' |')\n"
    "  Add-BriefLine $L $r\n"
    "  $r = ('| skill \u5ba1\u8ba1\u7ed3\u8bba | ' + $SkillAudit.audit_status + ' |')\n"
    "  Add-BriefLine $L $r\n"
    "  Add-BriefLine $L ''\n"
    "  Add-BriefLine $L '| \u6587\u4ef6 | \u5b57\u8282 | SHA256 | \u5df2\u58f0\u660e | \u672c\u8f6e\u53d8\u5316 |'\n"
    "  Add-BriefLine $L '|---|---|---|---|---|'\n"
    "  $skRows = @()\n"
    "  foreach ($f in $SkillAudit.files) {\n"
    "    $h1 = [string]$f.sha256\n"
    "    if ($h1.Length -gt 16) { $h1 = $h1.Substring(0, 16) + '...' }\n"
    "    $r = ('| ' + $f.relative_path + ' | ' + $f.size_bytes + ' | ' + $h1 + ' | ' + $f.declared + ' | ' + $f.change + ' |')\n"
    "    $skRows += $r\n"
    "  }\n"
    "  if ($skRows.Count -eq 0) { $skRows += '| (\u7a7a\u76ee\u5f55) | - | - | - | - |' }\n"
    "  Add-BriefLine $L ([string]::Join(\"`n\", $skRows))\n"
    "  Add-BriefLine $L ''\n"
    "  Add-BriefLine $L $zh['head_p0']")

# -------------------------------------- Y: one-shot TWEAK ledger events
patch('Y_oneshot_events',
    "      Add-AuditEvent $auditLog $p49Evt\n"
    "      Write-Host ('[EXT] P49 BACKTEST COMPLETE OBSERVED | archive=' + $p49Audit.manifest_archive_id + ' files=' + $p49Audit.file_count + ' bytes=' + $p49Audit.total_bytes + ' snapshot=' + $p49Audit.state_snapshot.Count + ' status=' + $p49Audit.audit_status + ' audit_only=YES intervention=NONE')\n"
    "    }",
    "      Add-AuditEvent $auditLog $p49Evt\n"
    "      Write-Host ('[EXT] P49 BACKTEST COMPLETE OBSERVED | archive=' + $p49Audit.manifest_archive_id + ' files=' + $p49Audit.file_count + ' bytes=' + $p49Audit.total_bytes + ' snapshot=' + $p49Audit.state_snapshot.Count + ' status=' + $p49Audit.audit_status + ' audit_only=YES intervention=NONE')\n"
    "    }\n"
    "    # ---------- TWEAK: one-shot first observation of a post-seal mutation ----------\n"
    "    if (($p49Audit.post_seal_archive_modify_alert -eq $true) -and ($p49PostSealFirstReported -eq $false)) {\n"
    "      $p49PostSealFirstReported = $true\n"
    "      $psEvt = @{\n"
    "        timestamp = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')\n"
    "        event = 'DSHD-P81-TWEAK-P49-POSTSEAL-MUTATION-FIRSTOBS-00001'\n"
    "        event_type = 'p49_post_seal_mutation_first_observed'\n"
    "        agent = $agentName\n"
    "        task = $tweakTaskName\n"
    "        a01_tag = $a01Tag\n"
    "        token = $tweakTokenName\n"
    "        token_state = $tokenState\n"
    "        branch = $branch\n"
    "        poll_count = $pollNo\n"
    "        mode = 'AUDIT_READ_ONLY'\n"
    "        audit_only = $true\n"
    "        intervention = 'NONE'\n"
    "        no_kill_executed = $true\n"
    "        p49_archive_id = $p49Audit.manifest_archive_id\n"
    "        p49_manifest_status = $p49Audit.manifest_status\n"
    "        p49_manifest_sealed = $p49Audit.manifest_sealed\n"
    "        p49_manifest_sealed_at = $p49Audit.manifest_sealed_at\n"
    "        p49_manifest_last_write = $p49Audit.manifest_last_write\n"
    "        p49_cold_start = $p49Audit.cold_start\n"
    "        p49_dir = 'artifacts/p49_backtest'\n"
    "        p49_file_count = $p49Audit.file_count\n"
    "        p49_total_bytes = $p49Audit.total_bytes\n"
    "        p49_expected_source = $p49Audit.expected_source\n"
    "        p49_manifest_declared_files = $p49Audit.manifest_declared_files\n"
    "        post_seal_mutation_kinds = $p49Audit.post_seal_mutation_kinds\n"
    "        post_seal_mutation_kinds_count = $p49Audit.post_seal_mutation_kinds_count\n"
    "        p49_unexpected_files = $p49Audit.unexpected_files\n"
    "        p49_added_files = $p49Audit.added_files\n"
    "        p49_hash_changed_files = $p49Audit.hash_changed_files\n"
    "        p49_removed_files = $p49Audit.removed_files\n"
    "        p49_missing_files = $p49Audit.missing_files\n"
    "        p49_files = $p49Audit.files\n"
    "        p49_sha256_snapshot = $p49Audit.state_snapshot\n"
    "        p49_audit_status = $p49Audit.audit_status\n"
    "        continuous_alert_rule = 'P49-001-ARTIFACT-UNEXPECTED is re-emitted every poll while post_seal_archive_modify_alert is true'\n"
    "        p49_read_only_audit = $true\n"
    "        p49_wrote_anything = $false\n"
    "        dshd_ran_backtest = $false\n"
    "        dshd_modified_backtest_artifact = $false\n"
    "        dshd_bypasses_dsha_p68 = $false\n"
    "        dshd_fetches_for_dshc = $false\n"
    "        p0_all_pass = $p0AllPass\n"
    "        gate = $trackState.gate\n"
    "        release_permit = $trackState.release_permit\n"
    "        wind_api_calls = $trackState.wind_api_calls\n"
    "        circuit_breaker_ready = $false\n"
    "        circuit_breaker_executed = $false\n"
    "      }\n"
    "      Add-AuditEvent $auditLog $psEvt\n"
    "      Write-Host ('[TWEAK] P49 POST-SEAL MUTATION FIRST OBSERVED | kinds=' + ($p49Audit.post_seal_mutation_kinds -join ',') + ' files=' + $p49Audit.file_count + ' undeclared=' + $p49Audit.unexpected_files.Count + ' modified=' + $p49Audit.hash_changed_files.Count + ' audit_only=YES intervention=NONE')\n"
    "    }\n"
    "    # ---------- TWEAK: one-shot first observation of the skill dir baseline ----------\n"
    "    if (($skillAudit.exists -eq $true) -and ($skillFirstReported -eq $false)) {\n"
    "      $skillFirstReported = $true\n"
    "      $skEvt = @{\n"
    "        timestamp = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')\n"
    "        event = 'DSHD-P81-TWEAK-SKILL-DIR-FIRSTOBS-00001'\n"
    "        event_type = 'skill_dir_hash_baseline_first_observed'\n"
    "        agent = $agentName\n"
    "        task = $tweakTaskName\n"
    "        a01_tag = $a01Tag\n"
    "        token = $tweakTokenName\n"
    "        token_state = $tokenState\n"
    "        branch = $branch\n"
    "        poll_count = $pollNo\n"
    "        mode = 'AUDIT_READ_ONLY'\n"
    "        audit_only = $true\n"
    "        intervention = 'NONE'\n"
    "        no_kill_executed = $true\n"
    "        skill_dir = 'artifacts/skill_lib/factor_v1'\n"
    "        skill_dir_file_count = $skillAudit.file_count\n"
    "        skill_dir_total_bytes = $skillAudit.total_bytes\n"
    "        skill_dir_skill_id = $skillAudit.skill_id\n"
    "        skill_dir_version = $skillAudit.version\n"
    "        skill_dir_version_locked = $skillAudit.version_locked\n"
    "        skill_dir_status = $skillAudit.status\n"
    "        skill_dir_locked_at = $skillAudit.locked_at\n"
    "        skill_dir_locked_by = $skillAudit.locked_by\n"
    "        skill_dir_skill_token = $skillAudit.skill_token\n"
    "        skill_dir_baseline = $skillAudit.skill_baseline\n"
    "        skill_dir_iteration_policy = $skillAudit.iteration_policy\n"
    "        skill_dir_next_version = $skillAudit.next_version\n"
    "        skill_dir_manifest_sha256 = $skillAudit.manifest_sha256\n"
    "        skill_dir_manifest_last_write = $skillAudit.manifest_last_write\n"
    "        skill_dir_manifest_readable = $skillAudit.manifest_readable\n"
    "        skill_dir_declared_files = $skillAudit.declared_files\n"
    "        skill_dir_declared_count = $skillAudit.declared_count\n"
    "        skill_dir_undeclared_files = $skillAudit.undeclared_files\n"
    "        skill_dir_declared_missing_files = $skillAudit.declared_missing_files\n"
    "        skill_dir_constraint_wind_api_calls = $skillAudit.constraint_wind_api_calls\n"
    "        skill_dir_constraint_offline_only = $skillAudit.constraint_offline_only\n"
    "        skill_dir_constraint_f01_script_locked = $skillAudit.constraint_f01_script_locked\n"
    "        skill_dir_constraint_f01_script_version = $skillAudit.constraint_f01_script_version\n"
    "        skill_dir_constraint_f01_script_params_only = $skillAudit.constraint_f01_script_params_only\n"
    "        skill_dir_data_integrity_aligned_sha256 = $skillAudit.data_integrity_aligned_sha256\n"
    "        skill_dir_data_integrity_aligned_rows = $skillAudit.data_integrity_aligned_rows\n"
    "        skill_dir_data_integrity_original_sha256 = $skillAudit.data_integrity_original_sha256\n"
    "        skill_dir_data_integrity_unique_dates = $skillAudit.data_integrity_unique_dates\n"
    "        skill_dir_original_csv_sha256_actual = $skillAudit.original_csv_sha256_actual\n"
    "        skill_dir_original_csv_sha256_match = $skillAudit.original_csv_sha256_match\n"
    "        skill_dir_files = $skillAudit.files\n"
    "        skill_dir_sha256_snapshot = $skillAudit.state_snapshot\n"
    "        skill_dir_audit_status = $skillAudit.audit_status\n"
    "        cold_start = $skillAudit.cold_start\n"
    "        skill_dir_read_only_audit = $true\n"
    "        dshd_wrote_skill_artifact = $false\n"
    "        dshd_modified_skill_artifact = $false\n"
    "        dshd_unlocked_skill_version = $false\n"
    "        p0_all_pass = $p0AllPass\n"
    "        gate = $trackState.gate\n"
    "        release_permit = $trackState.release_permit\n"
    "        wind_api_calls = $trackState.wind_api_calls\n"
    "        circuit_breaker_ready = $false\n"
    "        circuit_breaker_executed = $false\n"
    "      }\n"
    "      Add-AuditEvent $auditLog $skEvt\n"
    "      Write-Host ('[TWEAK] SKILL DIR BASELINE OBSERVED | id=' + $skillAudit.skill_id + ' ver=' + $skillAudit.version + ' locked=' + $skillAudit.version_locked + ' files=' + $skillAudit.file_count + ' bytes=' + $skillAudit.total_bytes + ' declared=' + $skillAudit.declared_count + ' undeclared=' + $skillAudit.undeclared_files.Count + ' sha_match=' + $skillAudit.original_csv_sha256_match + ' audit_only=YES intervention=NONE')\n"
    "    }\n"
    "    # ---------- TWEAK: one-shot exchange binding cleared event ----------\n"
    "    if (($exchClearedReported -eq $true) -and ($exchPrevMismatchCount -gt 0) -and ($attribAudit.mismatch_count -eq 0)) {\n"
    "      $exchClearedReported = $false\n"
    "      $ceEvt = @{\n"
    "        timestamp = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')\n"
    "        event = 'DSHD-P81-TWEAK-EXCH-BINDING-CLEARED-00001'\n"
    "        event_type = 'exchange_binding_cleared'\n"
    "        agent = $agentName\n"
    "        task = $tweakTaskName\n"
    "        a01_tag = $a01Tag\n"
    "        token = $tweakTokenName\n"
    "        token_state = $tokenState\n"
    "        branch = $branch\n"
    "        poll_count = $pollNo\n"
    "        mode = 'AUDIT_READ_ONLY'\n"
    "        audit_only = $true\n"
    "        intervention = 'NONE'\n"
    "        no_kill_executed = $true\n"
    "        prev_mismatch_count = $exchPrevMismatchCount\n"
    "        current_mismatch_count = $attribAudit.mismatch_count\n"
    "        labels_auto_cleared = @('EXCH-001-MISMATCH','EXCH-001-ATTRIBUTED-MISMATCH')\n"
    "        files_scanned = $attribAudit.files_scanned\n"
    "        distinct_symbols = $attribAudit.distinct_symbols\n"
    "        no_data_symbols = $attribAudit.no_data_symbols\n"
    "        lc_shf_verdict = $attribAudit.lc_shf_verdict\n"
    "        lc_shf_expected_exchange = $attribAudit.lc_shf_expected_exchange\n"
    "        lc_gfe_verdict = $attribAudit.lc_gfe_verdict\n"
    "        lc_gfe_expected_exchange = $attribAudit.lc_gfe_expected_exchange\n"
    "        lc_binding_repaired = $attribAudit.lc_binding_repaired\n"
    "        lc_repaired_via = $attribAudit.lc_repaired_via\n"
    "        csv_exchange_mismatch_count = $longTableAudit.exchange_mismatch_count\n"
    "        csv_exchange_unknown_count = $longTableAudit.exchange_unknown_count\n"
    "        attribution_audit_status = $attribAudit.audit_status\n"
    "        gate = $trackState.gate\n"
    "        release_permit = $trackState.release_permit\n"
    "        wind_api_calls = $trackState.wind_api_calls\n"
    "      }\n"
    "      Add-AuditEvent $auditLog $ceEvt\n"
    "      Write-Host ('[TWEAK] EXCH BINDING CLEARED | mismatch=' + $exchPrevMismatchCount + ' -> 0 | LC.SHF=' + $attribAudit.lc_shf_verdict + ' LC.GFE=' + $attribAudit.lc_gfe_verdict + ' repaired=' + $attribAudit.lc_binding_repaired + ' labels_auto_cleared=YES')\n"
    "    }")

# ------------------------------------------------- Z: TWEAK Write-Host line
patch('Z_tweak_logline',
    "    Write-Host (\"[{0}] POLL {1:D3} EXT | longtable=",
    "    Write-Host (\"[{0}] POLL {1:D3} TWEAK | rows_conv={2} legacy_hdr_inc={3} hdr_line={4} | sealed={5} postseal={6} polls={7} kinds={8} | skill_ver={9} locked={10} files={11} undecl={12} mod={13} rem={14} sha_match={15} {16} | lc_shf={17} lc_gfe={18} cleared={19}\" -f (Get-Date).ToString('HH:mm:ss'), $pollNo, $quickScan.data_rows_convention, $quickScan.data_rows_legacy_header_inclusive, $quickScan.header_line_count, $p49Audit.manifest_sealed, $p49Audit.post_seal_archive_modify_alert, $p49PostSealMutationPolls, ($p49Audit.post_seal_mutation_kinds -join ','), $skillAudit.version, $skillAudit.version_locked, $skillAudit.file_count, $skillAudit.undeclared_files.Count, $skillAudit.modified_files.Count, $skillAudit.removed_files.Count, $skillAudit.original_csv_sha256_match, $skillAudit.audit_status, $attribAudit.lc_shf_verdict, $attribAudit.lc_gfe_verdict, $exchClearedReported)\n"
    "    Write-Host (\"[{0}] POLL {1:D3} EXT | longtable=")


def main():
    with io.open(GEN, 'r', encoding='utf-8', newline='') as fh:
        src = fh.read()
    before = len(src)
    for pid, old, new, n in P:
        c = src.count(old)
        if c != n:
            sys.stderr.write('ABORT %s: expected %d, found %d\n' % (pid, n, c))
            sys.exit(1)
        src = src.replace(old, new)
        sys.stderr.write('ok   %-24s (%d)\n' % (pid, c))
    with io.open(GEN, 'w', encoding='utf-8', newline='') as fh:
        fh.write(src)
    print('GEN_BYTES_BEFORE', before)
    print('GEN_BYTES_AFTER ', len(src))
    print('GEN_PATCHES     ', len(P))


if __name__ == '__main__':
    main()
