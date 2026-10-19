#requires -Version 5.1
# ============================================================
# DSHD-P81-WATCH (EXT)
#   territory contract solidification + OBS-SPAWN-EXCEL-001
#   drift observer + 3-agent cluster status board
#   EXT : exchange binding audit (product -> exchange suffix)
#         long-table CSV primary-key / whitelist / indicator validation
#         artifacts/p49_backtest/ read-only integrity + hash audit
#   auth_ref : A01-USER-REMOTE-003
#   token    : DSHD-P81-TOKEN  (one-shot)
#   mode     : AUDIT_READ_ONLY
#   RED LINES: never kill, never circuit-break, never fetch
#              for DSHC, never run backtest for DSHA.
#              observe + record ONLY.
# ============================================================
$ErrorActionPreference = 'Stop'

# ---------------- CONSTANTS ----------------
$scriptVersion             = '1.2.0-TWEAK'
$agentName                 = 'DSHD-P81'
$taskName                  = 'DSHD-P81-WATCH'
$a01Tag                    = 'A01-USER-REMOTE-003'
$tokenName                 = 'DSHD-P81-TOKEN'
$extTokenName               = 'DSHD-P81-EXT-TOKEN'
$extTaskName                = 'DSHD-P81-EXT'
$tweakTokenName             = 'DSHD-P81-TWEAK-TOKEN'
$tweakTaskName              = 'DSHD-P81-TWEAK'
$tokenState                = 'ACTIVE_AUDIT_READ_ONLY'
$tokenMode                 = 'AUDIT_READ_ONLY'
$branch                    = 'feature/v88-g1'

$baseDir                   = 'D:\DSH_WORK\github工作\回测'
$artDir                    = $baseDir + '\artifacts'
$g7Dir                     = $baseDir + '\G7_ADJUDICATION_LEDGER'
$auditLog                  = $baseDir + '\tracking_monitor_audit.jsonl'
$csvPath                   = $baseDir + '\output_sample\wdf_sample_metals_raw.csv'
$csvLongTwin               = $baseDir + '\output_sample\wdf_sample_metals_long.csv'
$p49Dir                    = $artDir + '\p49_backtest'
$skillDir                  = $artDir + '\skill_lib\factor_v1'
$skillManifestPath         = $skillDir + '\manifest.json'
$indexPath                 = $artDir + '\cross_agent_artifact_index.json'
$scriptPath                = $g7Dir + '\dshd_p81_watch.ps1'

$protectMainPid            = 3472
$protectExcelPid           = 14644
$protectMainName           = 'DSHD-P71-main-monitor'
$protectExcelName          = 'zin-database-front-excel'

$pollIntervalSec           = 300
$excelFastIntervalSec       = 20
$fastBufferKeepMax          = 240
$excelSpawnWarnThreshold   = 2
$p68MinFileSize            = 5120
$p68MinRows                = 300
$dshcWindowFallbackH       = 24
$boardKeepMax              = 300
$histKeepMax               = 120

$refCsvSha256A03           = '41EC38315397FB70CC30BB313B88C3965BB50B30A628A3422743A48026806A92'
$refCsvSha256A01           = 'BEF26114CC1FCA4BDD40E911F888E7CA388DD150A1D48FD6C623D8FE07850895'

# --- EXT: exchange binding registry (product -> expected exchange suffix) ---
# SHFE = 上期所 (Shanghai Futures Exchange); GFE = 广期所 (Guangzhou Futures Exchange)
# LC (carbonate lithium) belongs to GFE. Observing only; never intervenes.
$exchangeSuffixes          = @('SHF','GFE','DCE','CZCE','INE')
$exchangeAlias             = @{ SHF='SHF'; SHFE='SHF'; GFE='GFE'; GZFE='GFE'; DCE='DCE'; DCEX='DCE'; CZCE='CZCE'; ZCE='CZCE'; INE='INE' }
$productExchange           = @{
  CU='SHF'; ZN='SHF'; PB='SHF'; AL='SHF'; SN='SHF'; NI='SHF'
  AG='SHF'; AU='SHF'; RB='SHF'; HC='SHF'; WR='SHF'; FU='SHF'; BU='SHF'; RU='SHF'; SP='SHF'; AO='SHF'; SS='SHF'; BR='SHF'
  LC='GFE'; SI='GFE'; PS='GFE'
  A='DCE'; B='DCE'; C='DCE'; CS='DCE'; JD='DCE'; L='DCE'; M='DCE'; P='DCE'; PP='DCE'; V='DCE'; Y='DCE'; EG='DCE'; FB='DCE'; RR='DCE'; JM='DCE'; I='DCE'
  CF='CZCE'; CY='CZCE'; FG='CZCE'; MA='CZCE'; OI='CZCE'; PF='CZCE'; PK='CZCE'; RI='CZCE'; RM='CZCE'; SA='CZCE'; SM='CZCE'; UR='CZCE'; AP='CZCE'; CJ='CZCE'; JR='CZCE'; LR='CZCE'; PM='CZCE'
  SC='INE'; NR='INE'; LU='INE'; BC='INE'; EC='INE'; BS='INE'
}
$csvSymbolWhitelist        = @('AL.SHF','CU.SHF','NI.SHF','PB.SHF','SN.SHF','ZN.SHF')
$csvSymbolWatchlist        = @('LC.GFE')
$csvIndicatorExpected      = @('CLOSE','VOL','OI','SETTLE')

# --- EXT: P49 backtest artifact audit (READ ONLY) ---
$p49ExpectedFiles          = @('backtest_metrics.json','backtest_report.pdf','MANIFEST.json','pipeline_metadata.json','symbol_performance.csv','symbol_performance.md')
$p49MinFileSize            = 1024

# script-name watch list (protected peers, by script file name)
$watchScripts              = @(
  @{name = 'pwsh-13'; script = 'dshd_p77_skillpack_watch.ps1';  label = 'DSHD-P77-skillpack'}
  @{name = 'pwsh-30'; script = 'dshd_p80_a01_audit_watch.ps1';  label = 'DSHD-P80-a01'}
  @{name = 'pwsh-37'; script = 'dshd_p80_a01_phase2_watch.ps1'; label = 'DSHD-P80-PHASE2'}
  @{name = 'self' ; script = 'dshd_p81_watch.ps1';              label = 'DSHD-P81-watch'}
)

# monitored paths for the write-territory conflict scanner
$monitoredPaths            = @(
  @{p = $artDir + '\dshd_p80_a01_audit_snapshot.json';            owner = 'DSHD-P80';          shared = $true }
  @{p = $artDir + '\dshd_p80_phase2_a01_audit_snapshot.json';     owner = 'DSHD-P80-PHASE2';   shared = $false}
  @{p = $artDir + '\dshd_a01_dualhash_verify.json';               owner = 'DSHD-P80';          shared = $true }
  @{p = $artDir + '\dshd_a01_quick_scan.json';                    owner = 'DSHD-P80';          shared = $true }
  @{p = $artDir + '\dshd_a01_observation_brief.md';               owner = 'DSHD-P80';          shared = $true }
  @{p = $artDir + '\dshd_a01_artifact_catalog.json';              owner = 'DSHD-P80';          shared = $true }
  @{p = $artDir + '\dshd_a01_file_evidence.json';                 owner = 'DSHD-P80';          shared = $true }
  @{p = $artDir + '\dshc_postmortem_receipt.json';                owner = 'DSHC';              shared = $false}
  @{p = $artDir + '\dshc_t1_run_receipt.json';                    owner = 'DSHC';              shared = $false}
  @{p = $csvPath;                                                 owner = 'DSHC';              shared = $false}
  @{p = $indexPath;                                                owner = 'DSHC';              shared = $false}
  @{p = $artDir + '\dsha_a02_plus_receipt.json';                  owner = 'DSHA';              shared = $false}
  @{p = $p49Dir + '\MANIFEST.json';                               owner = 'DSHA-P49';          shared = $false}
  @{p = $p49Dir + '\pipeline_metadata.json';                      owner = 'DSHA-P49';          shared = $false}
  @{p = $p49Dir + '\backtest_metrics.json';                       owner = 'DSHA-P49';          shared = $false}
  @{p = $p49Dir + '\symbol_performance.csv';                      owner = 'DSHA-P49';          shared = $false}
  @{p = $p49Dir + '\symbol_performance.md';                       owner = 'DSHA-P49';          shared = $false}
  @{p = $p49Dir + '\backtest_report.pdf';                        owner = 'DSHA-P49';          shared = $false}
  @{p = $csvLongTwin;                                              owner = 'DSHA';              shared = $false}
  @{p = $skillDir + '\manifest.json';                             owner = 'DSHC-SKILL-FACTOR01'; shared = $false}
  @{p = $skillDir + '\factor_extract_v1.py';                      owner = 'DSHC-SKILL-FACTOR01'; shared = $false}
  @{p = $skillDir + '\factor_definitions.json';                   owner = 'DSHC-SKILL-FACTOR01'; shared = $false}
  @{p = $skillDir + '\generate_aligned_csv.py';                   owner = 'DSHC-SKILL-FACTOR01'; shared = $false}
  @{p = $skillDir + '\data_sha256.txt';                           owner = 'DSHC-SKILL-FACTOR01'; shared = $false}
  @{p = $skillDir + '\README.md';                                 owner = 'DSHC-SKILL-FACTOR01'; shared = $false}
)

# Chinese labels (kept out of function bodies per P80 encoding rule)
$zh = @{
  title        = 'DSHD-P81 集群状态简报'
  sub          = '领地契约固化 · Excel 漂移观测器 · 交易所归属校验 · P49 产物只读审计 · Skill 目录哈希监控'
  calm         = '一切观测平稳'
  head_agent   = '一、三 Agent 统一状态'
  head_excel   = '二、OBS-SPAWN-EXCEL-001 漂移观测'
  head_territ  = '三、写领地契约 + 并发写入冲突'
  head_csv     = '四、CSV 双 hash + Quick-Scan'
  head_board   = '五、告警看板'
  head_exch    = '六、长表主键 + 品种白名单 + 交易所归属'
  head_p49     = '七、P49 回测产物只读审计'
  head_skill   = '八、FACTOR_EXTRACT_V1 Skill 目录哈希监控'
  head_p0      = '九、P0 校验'
  head_red     = '十、红线确认'
  st_duty      = '审计值守'
  st_post      = '复盘已归档'
  st_preheat   = '预热待命'
  st_posting   = '复盘进行中'
  yes          = 'YES'
  no           = 'NO'
}

# output paths
$outTerritory              = $artDir + '\dshd_write_territory_contract_v1.json'
$outCluster                = $artDir + '\dshd_cluster_status_latest.json'
$outBrief                  = $artDir + '\dshd_cluster_brief.md'
$outSnapshot               = $artDir + '\dshd_p81_a01_audit_snapshot.json'
$outDualHash               = $artDir + '\dshd_p81_a01_dualhash_verify.json'
$outQuickScan              = $artDir + '\dshd_p81_a01_quick_scan.json'
$outBoard                  = $artDir + '\dshd_p81_warning_board.json'
$outLongTable              = $artDir + '\dshd_p81_ext_longtable_exchange_audit.json'
$outP49                    = $artDir + '\dshd_p81_ext_p49_artifact_audit.json'
$outSkill                  = $artDir + '\dshd_p81_tweak_skill_audit.json'

# ---------------- HELPER FUNCTIONS ----------------
function Get-JsonSafe {
  param([string]$Path)
  if (!(Test-Path $Path)) { return $null }
  try { return (Get-Content $Path -Raw -Encoding UTF8 | ConvertFrom-Json) } catch { return $null }
}

function Get-JsonProp {
  param($Obj, [string]$Name, $Default)
  if ($null -eq $Obj) { return $Default }
  $ps = $Obj.PSObject.Properties[$Name]
  if ($null -eq $ps) { return $Default }
  return $ps.Value
}

function Write-Utf8File {
  param([string]$Path, [string]$Text)
  $enc = New-Object System.Text.UTF8Encoding($true)
  [System.IO.File]::WriteAllText($Path, $Text, $enc)
}

function Add-AuditEvent {
  param([string]$LogPath, [hashtable]$Evt)
  $json = $Evt | ConvertTo-Json -Depth 10 -Compress
  $utf8 = New-Object System.Text.UTF8Encoding($false)
  $bytes = $utf8.GetBytes($json + "`n")
  $fs = New-Object System.IO.FileStream($LogPath, [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write)
  try { $fs.Write($bytes, 0, $bytes.Length) } finally { $fs.Close() }
}

function Get-FileSha256 {
  param([string]$Path)
  try {
    $alg = [System.Security.Cryptography.SHA256]::Create()
    $stream = [System.IO.File]::OpenRead($Path)
    $h = $alg.ComputeHash($stream)
    $stream.Close()
    $alg.Dispose()
    $sb = New-Object System.Text.StringBuilder
    foreach ($b in $h) { [void]$sb.Append(('{0:X2}' -f $b)) }
    return $sb.ToString()
  } catch { return $null }
}

function Get-SecondSha256 {
  param([string]$Path)
  try { return (Get-FileHash $Path -Algorithm SHA256).Hash } catch { return $null }
}

function Test-PidAlive {
  param([int]$ProcId)
  try { return ([bool](Get-Process -Id $ProcId -ErrorAction Stop)) } catch { return $false }
}

function Get-ScriptWatchAlive {
  param([string]$ScriptFile, [int]$MinAgeSec)
  # Peers are launched by two different invocation styles:
  #   -File "...\dshd_pNN.ps1"          (DSHD-P80-PHASE2, DSHD-P81)
  #   & "...\\dshd_pNN.ps1"             (DSHD-P77, DSHD-P79, DSHD-P80)
  # so we match the escaped script file name anywhere in the command line.
  # MinAgeSec filters out short-lived inline diagnostic shells that merely
  # mention a script name, so a peer can never be reported alive by accident.
  $alive = $false
  $pids = @()
  $now = Get-Date
  $rx = [regex]::Escape($ScriptFile)
  $selfId = [int]$PID
  $ageMap = @{}
  try {
    $gps = Get-Process -Name powershell -ErrorAction SilentlyContinue
    foreach ($g in @($gps)) {
      if ($null -eq $g) { continue }
      $st = $null
      try { $st = $g.StartTime } catch { }
      if ($null -ne $st) { $ageMap[[int]$g.Id] = $st }
    }
  } catch { }
  try {
    $cim = Get-CimInstance Win32_Process -Filter "Name LIKE 'powershell%'"
    foreach ($p in @($cim)) {
      if ($null -eq $p) { continue }
      $pid2 = [int]$p.ProcessId
      if ($pid2 -eq $selfId) { continue }
      $cl = $p.CommandLine
      if ($null -eq $cl) { continue }
      if ($cl -notmatch $rx) { continue }
      if ($ageMap.ContainsKey($pid2)) {
        $age = $now.Subtract($ageMap[$pid2]).TotalSeconds
        if ($age -lt $MinAgeSec) { continue }
      }
      $alive = $true
      $pids += $pid2
    }
  } catch { }
  return @{alive = $alive; pid_count = $pids.Count; pids = $pids}
}

function Get-BomStatus {
  param([string]$Path)
  try {
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    $hasBom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
    return @{has_bom = $hasBom; size_bytes = $bytes.Length}
  } catch { return @{has_bom = $null; size_bytes = $null} }
}

function Get-TrackingState {
  param([string]$LogPath)
  $gate = 'UNKNOWN'; $permit = 'UNKNOWN'
  $gateLineNo = 0; $permitLineNo = 0
  $windNow = [long]0; $windFound = $false
  $p68Lock = 'UNKNOWN'; $p68Commit = ''; $p68LineNo = 0
  $windGarbageHits = 0
  $total = 0
  try {
    $lines = Get-Content $LogPath -Encoding UTF8
    $total = $lines.Count
    for ($i = $total - 1; $i -ge 0; $i--) {
      $ln = $lines[$i]
      if ($null -eq $ln) { continue }
      $inTail = ($i -ge ($total - 500))
      if ($gate -eq 'UNKNOWN' -and $ln -match '"gate"\s*:\s*"([^"]+)"') {
        $gate = $Matches[1]; $gateLineNo = ($i + 1)
      }
      if ($permit -eq 'UNKNOWN' -and $ln -match '"release_permit"\s*:\s*"([^"]+)"') {
        $permit = $Matches[1]; $permitLineNo = ($i + 1)
      }
      if ($ln -match '"wind_api_calls"\s*:\s*(-?\d+)') {
        $v = [long]$Matches[1]
        if ((-not $windFound) -and ($v -lt 1000)) { $windNow = $v; $windFound = $true }
        if ($inTail -and ($v -ge 2147483648)) { $windGarbageHits++ }
      }
      if ($p68Lock -eq 'UNKNOWN' -and $ln -match 'FINAL_STANDBY_LOCKED' -and $ln -match '"baseline_commit"\s*:\s*"([0-9a-fA-F]+)"') {
        $p68Lock = 'FINAL_STANDBY_LOCKED'; $p68Commit = $Matches[1]; $p68LineNo = ($i + 1)
      }
    }
  } catch {
    $gate = 'PARSE_FAIL'; $permit = 'PARSE_FAIL'
  }
  return @{
    gate = $gate; release_permit = $permit
    gate_line_no = $gateLineNo; permit_line_no = $permitLineNo
    wind_api_calls = $windNow; wind_api_calls_found = $windFound
    wind_api_garbage_hits_tail500 = $windGarbageHits
    p68_lock = $p68Lock; p68_commit = $p68Commit; p68_line_no = $p68LineNo
    total_lines = $total
  }
}

function Get-DshcTaskWindow {
  param([string]$LogPath, [int]$FallbackHours)
  $start = $null; $end = $null; $hits = 0
  try {
    $lines = Get-Content $LogPath -Encoding UTF8
    for ($i = 0; $i -lt $lines.Count; $i++) {
      $ln = $lines[$i]
      if ($null -eq $ln) { continue }
      if ($ln -notmatch 'DSHC') { continue }
      if ($ln -match '"timestamp"\s*:\s*"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})') {
        $dt = [datetime]$Matches[1]
        $hits++
        if ($null -eq $start -or $dt -lt $start) { $start = $dt }
        if ($null -eq $end -or $dt -gt $end) { $end = $dt }
      }
    }
  } catch { }
  if ($null -eq $start) { $start = (Get-Date).AddHours(-$FallbackHours); $hits = 0 }
  if ($null -eq $end) { $end = (Get-Date) }
  return @{window_start = $start; window_end = $end; event_hits = $hits}
}

function Get-ExcelSnapshot {
  param([datetime]$TaskWindowStart)
  $out = @()
  $ps = $null
  try { $ps = Get-Process -Name EXCEL -ErrorAction Stop } catch { }
  if ($null -ne $ps) {
    $nowTs = Get-Date
    foreach ($p in $ps) {
      if ($null -eq $p) { continue }
      $st = $null
      try { $st = $p.StartTime } catch { }
      $main = ''
      try { $main = $p.MainModule.FileName } catch { }
      $prot = ($p.Id -eq $protectExcelPid)
      $inWin = $false
      if ($null -ne $st -and $null -ne $TaskWindowStart) { $inWin = ($st -ge $TaskWindowStart) }
      $ageMin = $null
      if ($null -ne $st) { $ageMin = [math]::Round($nowTs.Subtract($st).TotalMinutes, 1) }
      $out += [pscustomobject]@{
        pid = [int]$p.Id
        start_time = $(if ($null -ne $st) { $st.ToString('s') } else { '' })
        protected = $prot
        in_task_window = $inWin
        age_minutes = $ageMin
        main_module = $main
      }
    }
  }
  return $out
}

function Test-ExcelSpawnRule {
  param($Snaps)
  $total = 0; $nonProt = 0; $nonProtInWindow = 0
  $flaggedPids = @()
  foreach ($s in $Snaps) {
    if ($null -eq $s) { continue }
    $total++
    if (-not $s.protected) {
      $nonProt++
      if ($s.in_task_window) { $nonProtInWindow++; $flaggedPids += [int]$s.pid }
    }
  }
  $warn = ($nonProtInWindow -gt $excelSpawnWarnThreshold)
  $status = 'NORMAL'
  if ($warn) { $status = 'YELLOW_OBS_SPAWN_EXCEL_001' }
  return @{
    rule_id = 'OBS-SPAWN-EXCEL-001'
    total_excel = $total
    non_protected_excel = $nonProt
    non_protected_in_task_window = $nonProtInWindow
    threshold_gt = $excelSpawnWarnThreshold
    triggered = $warn
    status = $status
    protected_pid = $protectExcelPid
    protected_name = $protectExcelName
    observation_only = $true
    auto_kill = $false
    flagged_pids = $flaggedPids
  }
}

function Get-DualHash {
  param([string]$CsvPath)
  $exists = (Test-Path $CsvPath)
  $hashA = $null; $hashB = $null
  if ($exists) {
    $hashA = Get-FileSha256 $CsvPath
    $hashB = Get-SecondSha256 $CsvPath
  }
  $aEqB = ($null -ne $hashA -and $hashA -ceq $hashB)
  $eqRefA03 = ($null -ne $hashA -and $hashA -ceq $refCsvSha256A03)
  $eqRefA01 = ($null -ne $hashA -and $hashA -ceq $refCsvSha256A01)
  $scanStatus = 'CSV_ABSENT'
  if ($exists) {
    if ($aEqB -and $eqRefA03) { $scanStatus = 'PASS_ALL_MATCH' }
    elseif ($aEqB -and $eqRefA01) { $scanStatus = 'PASS_MATCH_PRIOR_OBSERVATION' }
    elseif ($aEqB) { $scanStatus = 'A_EQ_B_REF_STALE_MISMATCH' }
    else { $scanStatus = 'INTERNAL_HASH_DISAGREEMENT' }
  }
  $warn = ($scanStatus -match 'MISMATCH|DISAGREEMENT')
  $code = ''
  if ($warn) { $code = 'A01_HASH_MISMATCH_WARNING' }
  return @{
    exists = $exists
    hash_a_byte_read = $hashA
    hash_b_getfilehash = $hashB
    ref_a03_csv_output = $refCsvSha256A03
    ref_a01_prior_observation = $refCsvSha256A01
    a_eq_b = $aEqB
    matches_ref_a03 = $eqRefA03
    matches_ref_a01_prior = $eqRefA01
    scan_status = $scanStatus
    warning_raised = $warn
    mismatch_code = $code
    independent_verify = $true
  }
}

function Get-QuickScan {
  param([string]$CsvPath)
  $exists = (Test-Path $CsvPath)
  $size = 0; $roughLines = 0; $dataRows = 0; $dataRowsHeaderInclusive = 0
  $maxBlank = 0; $header = ''; $headerCols = @()
  $rowCountConvention = 'DATA_ONLY_V2'
  if ($exists) {
    try { $size = [int](Get-Item $CsvPath).Length } catch { }
    $lines = @()
    try { $lines = @(Get-Content $CsvPath -Encoding UTF8) } catch { }
    $roughLines = $lines.Count
    $curBlank = 0
    for ($i = 0; $i -lt $lines.Count; $i++) {
      $ln = $lines[$i]
      if ($null -eq $ln) { continue }
      if ([string]::IsNullOrWhiteSpace($ln)) {
        $curBlank++
        if ($curBlank -gt $maxBlank) { $maxBlank = $curBlank }
      } else {
        $curBlank = 0
        $dataRowsHeaderInclusive++
      }
    }
    if ($roughLines -ge 1) { $header = [string]$lines[0] }
    if ($header.Length -gt 0) { $headerCols = @($header.Split(',')) }
  }
  # TWEAK (DSHD-P81-TWEAK): row-count convention alignment.
  # V1 legacy (kept for back-trace): every non-blank line counted as a data
  #   row, which INCLUDES the CSV header. Observed 7363 for the 2026-10-19
  #   long-format sample = 7362 data rows + 1 header line.
  # V2 current (authoritative): the header line is excluded, so
  #   quick_scan.data_rows == long_table_audit.data_rows == 7362.
  # Both values are emitted so a v1 consumer can reproduce the old number.
  $headerLineCount = 0
  if ($header.Length -gt 0) { $headerLineCount = 1 }
  $dataRows = $dataRowsHeaderInclusive - $headerLineCount
  $keywords = @('date','symbol','indicator','value','source')
  $hLower = ''
  $isLongFormat = $false
  if ($header.Length -gt 0) { $hLower = $header.ToLower() }
  if (($hLower -match 'indicator') -and ($hLower -match '(^|,)value(,|$)')) { $isLongFormat = $true }
  $missing = @()
  foreach ($k in $keywords) {
    if ((-not $isLongFormat) -and ($k -eq 'value')) { continue }
    if ($hLower -notmatch [regex]::Escape($k.ToLower())) { $missing += $k }
  }
  # In long format the indicator names are row values, not header columns;
  # they are validated by Get-LongTableAudit instead of by header keywords.
  $minSizeOk = ($size -ge $p68MinFileSize)
  $minRowsOk = ($dataRows -ge $p68MinRows)
  $blankAlarm = ($maxBlank -ge 3)
  $status = 'CSV_ABSENT'
  if ($exists) {
    if ((-not $minSizeOk) -or (-not $minRowsOk)) { $status = 'BELOW_P68_MIN_SIZE' }
    elseif ($blankAlarm -or ($missing.Count -gt 0)) { $status = 'SCAN_ANOMALY' }
    else { $status = 'SCAN_OK_P68_GATE_STILL_AUTHORITY' }
  }
  $stillStub = ($exists -and ($dataRows -le 1))
  return @{
    exists = $exists
    size_bytes = $size
    rough_lines = $roughLines
    data_rows = $dataRows
    data_rows_convention = $rowCountConvention
    data_rows_legacy_header_inclusive = $dataRowsHeaderInclusive
    header_line_count = $headerLineCount
    header = $header
    header_column_count = $headerCols.Count
    header_columns = $headerCols
    keyword_count = $keywords.Count
    keywords_missing_count = $missing.Count
    keywords_missing = $missing
    max_consecutive_blank = $maxBlank
    blank_alarm = $blankAlarm
    min_size_required = $p68MinFileSize
    min_size_ok = $minSizeOk
    min_rows_required = $p68MinRows
    min_rows_ok = $minRowsOk
    still_stub_header_only = $stillStub
    scan_status = $status
    format_kind = $(if ($isLongFormat) { 'LONG' } else { 'WIDE_OR_UNKNOWN' })
    p68_gate_is_authority = $true
    dshd_bypasses_p68 = $false
    circuit_breaker_raised = $false
  }
}

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
    auto_clear_enabled = $true
    lc_shf_verdict = ''
    lc_shf_expected_exchange = ''
    lc_gfe_verdict = ''
    lc_gfe_expected_exchange = ''
    lc_binding_repaired = $false
    lc_repaired_via = ''
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
  # TWEAK (DSHD-P81-TWEAK): exchange binding auto-clear contract for LC.
  # LC.SHF and LC.GFE are re-tested every poll. The binding is considered
  # REPAIRED when LC.SHF is no longer among the mismatches AND LC.GFE now
  # resolves as BOUND_OK. The EXCH-001-* labels are emitted conditionally
  # from mismatch_count, so they drop off of warning_board.json
  # automatically the moment DSHC fixes its config; the loop-side CLEARED
  # event makes the transition itself auditable in the ledger.
  $bShf = Test-ExchangeBinding 'LC.SHF'
  $bGfe = Test-ExchangeBinding 'LC.GFE'
  $out.lc_shf_verdict = $bShf.verdict
  $out.lc_shf_expected_exchange = $bShf.expected_exchange
  $out.lc_gfe_verdict = $bGfe.verdict
  $out.lc_gfe_expected_exchange = $bGfe.expected_exchange
  $lcShfStillBad = $false
  foreach ($mm in $out.mismatches) {
    if ($mm.symbol -eq 'LC.SHF') { $lcShfStillBad = $true }
  }
  if ((-not $lcShfStillBad) -and ($bGfe.verdict -eq 'BOUND_OK')) {
    $out.lc_binding_repaired = $true
    $out.lc_repaired_via = ('LC.GFE -> ' + $bGfe.expected_exchange + ' (BOUND_OK)')
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
    expected_source = 'HARDCODED_FALLBACK'
    manifest_declared_count = 0
    manifest_declared_files = @()
    manifest_readable = $false
    manifest_last_write = ''
    manifest_sealed = $false
    manifest_sealed_at = ''
    post_seal_mutation = $false
    post_seal_mutation_kinds = @()
    post_seal_mutation_kinds_count = 0
    post_seal_archive_modify_alert = $false
    cold_start = ($null -eq $PrevState)
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
  # Parse MANIFEST first: MANIFEST.files[].path is the source of truth for which
  # files belong in the archive, so the expected set is derived rather than
  # hard-coded. Falls back to the hard-coded set when the manifest is unreadable.
  $declared = @()
  $manifestPath = $dir + '\MANIFEST.json'
  if (Test-Path $manifestPath) {
    try { $out.manifest_last_write = (Get-Item $manifestPath).LastWriteTime.ToString('yyyy-MM-ddTHH:mm:sszzz') } catch { }
    $m = Get-JsonSafe $manifestPath
    if ($null -ne $m) {
      $out.manifest_readable = $true
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
      $declaredList = Get-JsonProp $m 'files' @()
      foreach ($df in $declaredList) {
        $dp = [string](Get-JsonProp $df 'path' '')
        if ($dp.Length -eq 0) { continue }
        $dn = $dp
        if ($dn -match '\\') { $dn = $dn.Substring($dn.LastIndexOf('\') + 1) }
        if ($dn -match '/') { $dn = $dn.Substring($dn.LastIndexOf('/') + 1) }
        $declared += $dn
        $out.manifest_declared_files += $dp
      }
    }
  }
  if ($declared.Count -gt 0) {
    $out.expected_file_count = $declared.Count
    $out.expected_source = 'MANIFEST.files[].path'
  } else {
    $declared = $p49ExpectedFiles
    $out.expected_source = 'HARDCODED_FALLBACK'
  }
  $out.manifest_declared_count = $declared.Count
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
    foreach ($e in $declared) { if ($e -eq $it.Name) { $isExp = $true } }
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
  foreach ($e in $declared) {
    $found = $false
    foreach ($f in $items) { if ($f.Name -eq $e) { $found = $true } }
    if (-not $found) { $out.missing_files += $e }
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
  # TWEAK (DSHD-P81-TWEAK): post-seal archive mutation detector.
  # Once MANIFEST.status marks the archive COMPLETE (sealed), ANY add /
  # modify / delete / undeclared / declared-missing entry inside the
  # directory is a post-seal mutation. It raises the
  # P49-001-ARTIFACT-UNEXPECTED umbrella label every poll until the
  # archive is re-sealed clean. Granular codes (HASH-CHANGED /
  # ARTIFACT-MISSING / ARTIFACT-REMOVED) keep firing alongside for detail.
  # On a cold start (no previous snapshot) ADDED / REMOVED are suppressed
  # because every file trivially looks new; undeclared and declared-missing
  # entries are MANIFEST-derived and remain meaningful.
  if ($out.manifest_status -match 'COMPLETE') {
    $out.manifest_sealed = $true
    $out.manifest_sealed_at = $out.manifest_last_write
  }
  if ($out.manifest_sealed) {
    $kinds = @()
    if ($out.unexpected_files.Count -gt 0) { $kinds += 'ADDED_UNDECLARED' }
    if ((-not $out.cold_start) -and ($out.added_files.Count -gt 0)) { $kinds += 'ADDED' }
    if ($out.hash_changed_files.Count -gt 0) { $kinds += 'MODIFIED' }
    if ((-not $out.cold_start) -and ($out.removed_files.Count -gt 0)) { $kinds += 'REMOVED' }
    if ($out.missing_files.Count -gt 0) { $kinds += 'DECLARED_MISSING' }
    if ($kinds.Count -gt 0) {
      $out.post_seal_mutation = $true
      $out.post_seal_mutation_kinds = $kinds
      $out.post_seal_archive_modify_alert = $true
    }
  }
  $out.post_seal_mutation_kinds_count = $out.post_seal_mutation_kinds.Count
  if ($out.post_seal_archive_modify_alert) { $out.audit_status = 'P49_POSTSEAL_MUTATION' }
  elseif (($out.missing_files.Count -gt 0) -or ($out.removed_files.Count -gt 0)) { $out.audit_status = 'P49_ARTIFACT_SET_INCOMPLETE' }
  elseif ($out.hash_changed_files.Count -gt 0) { $out.audit_status = 'P49_ARTIFACT_HASH_CHANGED' }
  elseif ($out.unexpected_files.Count -gt 0) { $out.audit_status = 'P49_UNDECLARED_ARTIFACT' }
  elseif ($exMismatch -gt 0) { $out.audit_status = 'P49_EXCHANGE_COLUMN_ANOMALY' }
  elseif ($out.under_min_size_files.Count -gt 0) { $out.audit_status = 'P49_FILE_BENEATH_MIN_SIZE' }
  elseif ($out.manifest_status -match 'BACKTEST_COMPLETE') { $out.audit_status = 'P49_BACKTEST_COMPLETE_INTEGRITY_OK' }
  else { $out.audit_status = 'P49_PRESENT_PARTIAL' }
  return $out
}

function Get-SkillDirAudit {
  param($PrevState)
  $dir = $skillDir
  $out = @{
    check = 'FACTOR_EXTRACT_V1_SKILL_DIR_HASH_AUDIT'
    dir = 'artifacts/skill_lib/factor_v1'
    mode = 'OBSERVATION_ONLY'
    read_only = $true
    wrote_anything = $false
    auto_intervene = $false
    exists = $false
    file_count = 0
    total_bytes = [long]0
    manifest_path = 'artifacts/skill_lib/factor_v1/manifest.json'
    manifest_readable = $false
    manifest_last_write = ''
    manifest_sha256 = ''
    manifest_hash_changed = $false
    declared_count = 0
    declared_files = @()
    undeclared_files = @()
    declared_missing_files = @()
    files = @()
    added_files = @()
    modified_files = @()
    removed_files = @()
    skill_id = ''
    version = ''
    previous_version = ''
    skill_version_changed = $false
    version_locked = $false
    status = ''
    locked_at = ''
    locked_by = ''
    skill_token = ''
    skill_baseline = ''
    iteration_policy = ''
    next_version = ''
    constraint_wind_api_calls = 0
    constraint_offline_only = $false
    constraint_f01_script_locked = $false
    constraint_f01_script_version = ''
    constraint_f01_script_params_only = $false
    data_integrity_aligned_sha256 = ''
    data_integrity_aligned_rows = 0
    data_integrity_original_sha256 = ''
    data_integrity_unique_dates = 0
    original_csv_sha256_actual = ''
    original_csv_sha256_match = $false
    v1_frozen_violation = $false
    v1_frozen_violation_files = @()
    cold_start = ($null -eq $PrevState)
    state_snapshot = @{}
    audit_status = 'SKILL_ABSENT'
    intervention = 'NONE'
  }
  if (-not (Test-Path $dir)) { return $out }
  $out.exists = $true
  $prevMap = @{}
  if ($null -ne $PrevState) { foreach ($k in $PrevState.Keys) { $prevMap[$k] = $PrevState[$k] } }
  $prevManifestHash = ''
  $prevVersion = ''
  if ($prevMap.ContainsKey('__META__manifest_sha256')) { $prevManifestHash = [string]$prevMap['__META__manifest_sha256'] }
  if ($prevMap.ContainsKey('__META__version')) { $prevVersion = [string]$prevMap['__META__version'] }
  $manifestPath = $dir + '\manifest.json'
  $declared = @()
  if (Test-Path $manifestPath) {
    try { $out.manifest_last_write = (Get-Item $manifestPath).LastWriteTime.ToString('yyyy-MM-ddTHH:mm:sszzz') } catch { }
    $mh = Get-FileSha256 $manifestPath
    if ($null -ne $mh) { $out.manifest_sha256 = $mh }
    $m = Get-JsonSafe $manifestPath
    if ($null -ne $m) {
      $out.manifest_readable = $true
      $out.skill_id = [string](Get-JsonProp $m 'skill_id' '')
      $out.version = [string](Get-JsonProp $m 'version' '')
      $out.version_locked = [bool](Get-JsonProp $m 'version_locked' $false)
      $out.status = [string](Get-JsonProp $m 'status' '')
      $out.locked_at = [string](Get-JsonProp $m 'locked_at' '')
      $out.locked_by = [string](Get-JsonProp $m 'locked_by' '')
      $out.skill_token = [string](Get-JsonProp $m 'token' '')
      $out.skill_baseline = [string](Get-JsonProp $m 'baseline' '')
      $out.iteration_policy = [string](Get-JsonProp $m 'iteration_policy' '')
      $out.next_version = [string](Get-JsonProp $m 'next_version' '')
      $cs = Get-JsonProp $m 'constraints' @{}
      $out.constraint_wind_api_calls = [long](Get-JsonProp $cs 'wind_api_calls' 0)
      $out.constraint_offline_only = [bool](Get-JsonProp $cs 'offline_only' $false)
      $out.constraint_f01_script_locked = [bool](Get-JsonProp $cs 'f01_script_locked' $false)
      $out.constraint_f01_script_version = [string](Get-JsonProp $cs 'f01_script_version' '')
      $out.constraint_f01_script_params_only = [bool](Get-JsonProp $cs 'f01_script_params_only' $false)
      $di = Get-JsonProp $m 'data_integrity' @{}
      $out.data_integrity_aligned_sha256 = [string](Get-JsonProp $di 'aligned_csv_sha256' '')
      $out.data_integrity_aligned_rows = [long](Get-JsonProp $di 'aligned_csv_rows' 0)
      $out.data_integrity_original_sha256 = [string](Get-JsonProp $di 'original_csv_sha256' '')
      $out.data_integrity_unique_dates = [long](Get-JsonProp $di 'unique_dates' 0)
      $dl = Get-JsonProp $m 'files' @()
      foreach ($df in $dl) {
        $dn = [string](Get-JsonProp $df 'name' '')
        if ($dn.Length -gt 0) { $declared += $dn; $out.declared_files += $dn }
      }
    }
  }
  $out.declared_count = $declared.Count
  $out.previous_version = $prevVersion
  if (($prevVersion.Length -gt 0) -and ($out.version -ne $prevVersion)) { $out.skill_version_changed = $true }
  if (($prevManifestHash.Length -gt 0) -and ($out.manifest_sha256 -ne $prevManifestHash)) { $out.manifest_hash_changed = $true }
  $ach = Get-FileSha256 $csvPath
  if ($null -ne $ach) { $out.original_csv_sha256_actual = $ach }
  if (($out.data_integrity_original_sha256.Length -gt 0) -and ($out.original_csv_sha256_actual.Length -gt 0)) {
    $out.original_csv_sha256_match = ([string]$out.data_integrity_original_sha256).ToUpper().Equals(([string]$out.original_csv_sha256_actual).ToUpper())
  }
  $items = @(Get-ChildItem $dir -File -Recurse -ErrorAction SilentlyContinue)
  $out.file_count = $items.Count
  $curMap = @{}
  $totalBytes = [long]0
  $frozenViolations = @()
  foreach ($it in $items) {
    $rel = [string]$it.FullName
    if ($rel.Length -gt $dir.Length) { $rel = $rel.Substring($dir.Length).TrimStart('\\') }
    $sz = [long]$it.Length
    $hash = ''
    try { $hash = (Get-FileHash $it.FullName -Algorithm SHA256).Hash } catch { }
    $isDeclared = $false
    foreach ($e in $declared) { if ($e -eq $it.Name) { $isDeclared = $true } }
    $changed = 'NEW'
    if ($prevMap.ContainsKey($rel)) {
      if ([string]$prevMap[$rel] -eq $hash) { $changed = 'UNCHANGED' }
      else {
        $changed = 'MODIFIED'
        $out.modified_files += $rel
        if ($isDeclared -and ($out.version_locked -eq $true)) { $frozenViolations += $rel }
      }
    } else {
      $out.added_files += $rel
    }
    $row = @{relative_path = $rel; name = $it.Name; size_bytes = $sz; sha256 = $hash; last_write = $it.LastWriteTime.ToString('yyyy-MM-ddTHH:mm:sszzz'); declared = $isDeclared; change = $changed}
    $out.files += $row
    if (-not $isDeclared) { $out.undeclared_files += $rel }
    $curMap[$rel] = $hash
    $totalBytes += $sz
  }
  foreach ($k in $prevMap.Keys) {
    if ([string]$k -like '__META__*') { continue }
    if (-not $curMap.ContainsKey($k)) { $out.removed_files += $k }
  }
  foreach ($e in $declared) {
    $found = $false
    foreach ($f in $items) { if ($f.Name -eq $e) { $found = $true } }
    if (-not $found) { $out.declared_missing_files += $e }
  }
  $out.total_bytes = $totalBytes
  $out.v1_frozen_violation_files = $frozenViolations
  $out.v1_frozen_violation = ($frozenViolations.Count -gt 0)
  $curMap['__META__manifest_sha256'] = $out.manifest_sha256
  $curMap['__META__version'] = $out.version
  $out.state_snapshot = $curMap
  if ($out.v1_frozen_violation) { $out.audit_status = 'SKILL_V1_FROZEN_VIOLATION' }
  elseif ($out.cold_start -and ($out.modified_files.Count -eq 0) -and ($out.removed_files.Count -eq 0) -and ($out.added_files.Count -gt 0)) { $out.audit_status = 'SKILL_BASELINE_ESTABLISHED' }
  elseif (($out.modified_files.Count -gt 0) -or ($out.added_files.Count -gt 0) -or ($out.removed_files.Count -gt 0)) { $out.audit_status = 'SKILL_DIR_CHANGED' }
  elseif ($out.manifest_hash_changed -or $out.skill_version_changed) { $out.audit_status = 'SKILL_MANIFEST_CHANGED' }
  elseif ($out.declared_missing_files.Count -gt 0) { $out.audit_status = 'SKILL_DECLARED_MISSING' }
  elseif ($out.undeclared_files.Count -gt 0) { $out.audit_status = 'SKILL_UNDECLARED_FILE' }
  elseif ($out.status -match 'VERSION_LOCKED') { $out.audit_status = 'SKILL_VERSION_LOCKED_INTEGRITY_OK' }
  else { $out.audit_status = 'SKILL_PRESENT_PARTIAL' }
  return $out
}

function Get-TerritoryState {
  param($MonPaths, $PrevState)
  $entries = @()
  $conflicts = @()
  $nextState = @{}
  foreach ($mp in $MonPaths) {
    $p = $mp.p; $owner = $mp.owner; $shared = [bool]$mp.shared
    $exists = (Test-Path $p)
    $size = $null; $mtime = $null; $readonly = $null
    $tag = $null
    if ($exists) {
      try {
        $fi = Get-Item $p
        $size = [long]$fi.Length
        $mtime = $fi.LastWriteTime
        $readonly = $fi.IsReadOnly
      } catch { }
      $obj = Get-JsonSafe $p
      if ($null -ne $obj) {
        $tv = Get-JsonProp $obj 'a01_tag' $null
        if ($null -eq $tv) { $tv = Get-JsonProp $obj 'token' $null }
        if ($null -eq $tv) { $tv = Get-JsonProp $obj 'updated_by' $null }
        $tag = $tv
      }
    }
    $prev = $null
    if ($null -ne $PrevState) { $prev = $PrevState[$p] }
    $tagFlap = $false
    $mtimeAdvance = $false
    if ($null -ne $prev) {
      if ($null -ne $tag -and ($prev.tag -ne $tag)) { $tagFlap = $true }
      if ($null -ne $mtime -and ($mtime -gt $prev.mtime)) { $mtimeAdvance = $true }
    }
    $mtimeStr = ''
    if ($null -ne $mtime) { $mtimeStr = $mtime.ToString('s') }
    $entries += @{
      path = $p
      relative_path = $p.Replace($baseDir + '\', '')
      policy_owner = $owner
      known_shared_write = $shared
      exists = $exists
      size_bytes = $size
      last_write = $mtimeStr
      is_readonly = $readonly
      observed_agent_tag = $tag
      write_advanced_this_poll = $mtimeAdvance
    }
    if ($tagFlap) {
      $conflicts += @{
        path = $p
        relative_path = $p.Replace($baseDir + '\', '')
        code = 'CONCURRENT_WRITE_CONFLICT'
        severity = 'WARN'
        detail = 'same path observed with different agent tags across polls; multi-writer on shared artifact'
        from_tag = $prev.tag
        to_tag = $tag
        observation_only = $true
        action_taken = 'NONE'
      }
    }
    if ($mtimeAdvance -and (-not $shared) -and ($null -ne $prev)) {
      $conflicts += @{
        path = $p
        relative_path = $p.Replace($baseDir + '\', '')
        code = 'OWNER_PATH_MODIFIED_THIS_POLL'
        severity = 'INFO'
        detail = 'owner-exclusive path advanced this poll; expected owner=' + $owner
        observed_agent_tag = $tag
        observation_only = $true
        action_taken = 'NONE'
      }
    }
    $nextState[$p] = @{tag = $tag; mtime = $mtime; size = $size}
  }
  return @{
    entries = $entries
    conflicts = $conflicts
    conflict_count = $conflicts.Count
    entry_count = $entries.Count
    scan_mode = 'OBSERVATION_ONLY_NO_INTERCEPTION'
    scan_interception_enabled = $false
    next_state = $nextState
  }
}

function Get-ClusterAgents {
  param($TrackState, $ExcelRule, $PollNo, $SnapTs)
  $dshcReceipt = Get-JsonSafe ($artDir + '\dshc_postmortem_receipt.json')
  $t1Receipt = Get-JsonSafe ($artDir + '\dshc_t1_run_receipt.json')
  $dshaPlus = Get-JsonSafe ($artDir + '\dsha_a02_plus_receipt.json')
  $dshaReady = Get-JsonSafe ($artDir + '\dsha_a02_ready_receipt.json')

  $dshcStatus = 'UNKNOWN'; $dshcTs = ''; $dshcTokenState = ''
  $dshcRoot = ''; $dshcGuardRules = @(); $dshcSession = ''
  if ($null -ne $dshcReceipt) {
    $dshcStatus = [string](Get-JsonProp $dshcReceipt 'status' '')
    $dshcTs = [string](Get-JsonProp $dshcReceipt 'ts' '')
    $dshcTokenState = [string](Get-JsonProp $dshcReceipt 'token_state' '')
    $dshcRoot = [string](Get-JsonProp $dshcReceipt 'spawn_bug_root' '')
    $dshcSession = [string](Get-JsonProp $dshcReceipt 'session' '')
    $gr = Get-JsonProp $dshcReceipt 'guard_rules' @()
    if ($null -ne $gr) { foreach ($g in @($gr)) { if ($null -ne $g) { $dshcGuardRules += [string]$g } } }
  }
  $t1Status = ''
  if ($null -ne $t1Receipt) { $t1Status = [string](Get-JsonProp $t1Receipt 'status' '') }

  $dshaStatus = 'UNKNOWN'; $dshaTs = ''; $dshaVerdict = ''
  if ($null -ne $dshaPlus) {
    $dshaStatus = [string](Get-JsonProp $dshaPlus 'status' '')
    $dshaTs = [string](Get-JsonProp $dshaPlus 'ts' '')
    $dshaVerdict = [string](Get-JsonProp $dshaPlus 'verdict' '')
  }
  if (($null -eq $dshaPlus) -or ($dshaStatus -eq '')) {
    if ($null -ne $dshaReady) {
      $dshaStatus = [string](Get-JsonProp $dshaReady 'status' 'UNKNOWN')
      $dshaTs = [string](Get-JsonProp $dshaReady 'ts' '')
    }
  }

  $dshcLabel = $zh['st_posting']
  if ($dshcStatus -match 'COMPLETED|ARCHIVED|DONE') { $dshcLabel = $zh['st_post'] }
  $dshaLabel = $zh['st_preheat']
  if ($TrackState.p68_lock -eq 'FINAL_STANDBY_LOCKED') { $dshaLabel = 'FINAL_STANDBY_LOCKED' }

  return @{
    dshc = @{
      agent = 'DSHC'
      state = $dshcLabel
      state_raw = $dshcStatus
      session = $dshcSession
      last_receipt = 'artifacts/dshc_postmortem_receipt.json'
      last_receipt_ts = $dshcTs
      t1_run_status = $t1Status
      token_state = $dshcTokenState
      post_mortem_status = $dshcStatus
      spawn_bug_root = $dshcRoot
      guard_rules_count = $dshcGuardRules.Count
      guard_rules = $dshcGuardRules
      wind_api_calls = $TrackState.wind_api_calls
      post_mortem_in_progress = ($dshcStatus -match 'RUNNING|IN_PROGRESS')
    }
    dsha = @{
      agent = 'DSHA'
      state = $dshaLabel
      state_raw = $dshaStatus
      last_receipt = 'artifacts/dsha_a02_plus_receipt.json'
      last_receipt_ts = $dshaTs
      verdict = $dshaVerdict
      p68_lock = $TrackState.p68_lock
      p68_commit = $TrackState.p68_commit
      p68_line_no = $TrackState.p68_line_no
      gate = $TrackState.gate
      release_permit = $TrackState.release_permit
      backtest_started = $false
      dshd_runs_backtest = $false
    }
    dshd = @{
      agent = $agentName
      state = $zh['st_duty']
      previous_watchers = @('DSHD-P71','DSHD-P77','DSHD-P79','DSHD-P80','DSHD-P80-PHASE2')
      poll_count = $PollNo
      poll_ts = $SnapTs.ToString('yyyy-MM-ddTHH:mm:sszzz')
      token = $tokenName
      token_state = $tokenState
      a01_tag = $a01Tag
      wind_api_calls = $TrackState.wind_api_calls
      audit_only = $true
      intervention = 'NONE'
      auto_kill = $false
      excel_spawn_observer = $ExcelRule
    }
  }
}

function Get-RedLineStatus {
  param($TrackState, $WindApiCalls)
  $gate = [string]$TrackState.gate
  $permit = [string]$TrackState.release_permit
  $gateUnchanged = ($gate -match 'CLOSED')
  $permitHeld = ($permit -match 'NOT_ISSUED')
  return @{
    wind_api_calls = $WindApiCalls
    audit_only = $true
    processes_untouched = $true
    no_kill_executed = $true
    no_circuit_break_executed = $true
    gate_unchanged = $gateUnchanged
    gate_observed = $gate
    release_permit_observed = $permit
    release_permit_not_issued = $permitHeld
    dshd_runs_backtest = $false
    dshd_fetches_for_dshc = $false
    dshd_bypasses_dsha_p68 = $false
    ignition_marker_touched = $false
    output_csv_touched = $false
    intervention = 'NONE'
  }
}

function Build-TerritoryContract {
  param($PollNo, $TerritoryState, $SnapTs)
  $territories = @(
    @{
      id = 'T1'; relative_path = 'tracking_monitor_audit.jsonl'
      policy = 'APPEND_ONLY'
      exclusive_owner = $null
      allowed_appenders = @('DSHD-P67','DSHD-P71','DSHD-P77','DSHD-P79','DSHD-P80','DSHD-P80-PHASE2','DSHD-P81','DSHC','DSHA')
      forbidden = @('TRUNCATE','REWRITE','DELETE','LINE_RENUMBER')
      newline_contract = 'each event object terminated by LF (0x0A); multi-object physical lines are a defect'
    }
    @{
      id = 'T2'; relative_path = 'cross_agent_artifact_index.json'
      policy = 'OWNER_EXCLUSIVE'
      exclusive_owner = 'DSHC'
      allowed_appenders = @()
      forbidden = @('DSHD_ANY_WRITE','DSHA_ANY_WRITE','DSHC-DSHD_SHARED')
    }
    @{
      id = 'T3'; relative_path = 'output_sample/wdf_sample_metals_raw.csv'
      policy = 'OWNER_EXCLUSIVE'
      exclusive_owner = 'DSHC'
      allowed_appenders = @()
      forbidden = @('DSHD_ANY_WRITE','DSHA_ANY_WRITE','AUDIT_AGENT_ANY_WRITE')
      note = 'DSHD computes hashes only; never writes this file'
    }
    @{
      id = 'T4'; pattern = 'artifacts/dshc_*.json'
      policy = 'OWNER_EXCLUSIVE'
      exclusive_owner = 'DSHC'
      allowed_appenders = @()
      forbidden = @('DSHD_ANY_WRITE','DSHA_ANY_WRITE')
    }
    @{
      id = 'T5'; pattern = 'artifacts/dsha_*.json'
      policy = 'OWNER_EXCLUSIVE'
      exclusive_owner = 'DSHA'
      allowed_appenders = @()
      forbidden = @('DSHD_ANY_WRITE','DSHC_ANY_WRITE')
    }
    @{
      id = 'T6'; pattern = 'artifacts/dshd_*.json'
      policy = 'NAME_PREFIX_EXCLUSIVE'
      exclusive_owner = 'DSHD-FAMILY'
      allowed_appenders = @()
      forbidden = @('NON_DSHD_PREFIX_WRITE')
      known_shared_exception = @('artifacts/dshd_p80_a01_audit_snapshot.json')
      known_shared_exception_detail = 'written by both DSHD-P80 (tag A01-USER-REMOTE-001) and DSHD-P80-PHASE2 (tag A01-USER-REMOTE-002); observed as CONCURRENT_WRITE_CONFLICT, recorded only'
    }
    @{
      id = 'T7'; pattern = 'scripts/*'
      policy = 'HUMAN_LICENSOR_ONLY'
      exclusive_owner = 'HOLDER'
      allowed_appenders = @()
      forbidden = @('AGENT_ANY_WRITE')
    }
    @{
      id = 'T8'; pattern = 'ignition markers / release_permit'
      policy = 'HUMAN_LICENSE_ONLY'
      exclusive_owner = 'HOLDER'
      allowed_appenders = @()
      forbidden = @('AGENT_ANY_WRITE')
      note = 'DSHC ignition and DSHA backtest are human-licensed only; DSHD watches and records'
    }
  )
  $contract = @{
    contract_id = 'DSHD-WRITE-TERRITORY-CONTRACT-V1'
    version = '1.0'
    contract_status = 'ACTIVE'
    issued_by = $agentName
    task = $taskName
    a01_tag = $a01Tag
    token = $tokenName
    token_state = $tokenState
    branch = $branch
    issued_at = $SnapTs.ToString('yyyy-MM-ddTHH:mm:sszzz')
    poll_count = $PollNo
    mode = 'AUDIT_READ_ONLY'
    enforcement_mode = 'OBSERVATION_ONLY'
    interception_enabled = $false
    auto_block_enabled = $false
    auto_kill_enabled = $false
    auto_circuit_break_enabled = $false
    territory_count = $territories.Count
    territories = $territories
    protection_list = @(
      @{pid = $protectMainPid; role = $protectMainName; never_kill = $true}
      @{pid = $protectExcelPid; role = $protectExcelName; never_kill = $true}
      @{role = 'DSHD-P77 (pwsh-13)'; script = 'dshd_p77_skillpack_watch.ps1'; never_kill = $true}
      @{role = 'DSHD-P79'; script = 'dshd_p79_a01_audit_watch.ps1'; never_kill = $true}
      @{role = 'DSHD-P80 (pwsh-30)'; script = 'dshd_p80_a01_audit_watch.ps1'; never_kill = $true}
      @{role = 'DSHD-P80-PHASE2 (pwsh-37)'; script = 'dshd_p80_a01_phase2_watch.ps1'; never_kill = $true}
      @{role = 'DSHD-P81 (self)'; script = 'dshd_p81_watch.ps1'; never_kill = $true}
    )
    concurrent_write_scan = @{
      enabled = $true
      monitored_path_count = $TerritoryState.entry_count
      conflict_count = $TerritoryState.conflict_count
      conflicts = $TerritoryState.conflicts
      action_on_conflict = 'RECORD_ONLY'
      blocking_enabled = $false
    }
    rules_observed = @(
      @{rule_id = 'OBS-SPAWN-EXCEL-001'; origin = 'DSHC-POST-MORTEM-T1 guard GR1/GR2/GR3'; mode = 'OBSERVATION_ONLY'; auto_kill = $false}
    )
    red_lines = @{
      audit_only = $true
      no_kill = $true
      no_intervention = $true
      no_dshc_fetch_proxy = $true
      no_dsha_backtest_proxy = $true
      do_not_disturb_post_mortem_t1 = $true
      observe_and_record_only = $true
    }
  }
  return $contract
}

function Add-BriefLine {
  param($Lines, $Text)
  [void]$Lines.Add([string]$Text)
}

function Write-ClusterBrief {
  param($SnapTs, $Agents, $ExcelRule, $TerritoryState, $DualHash, $QuickScan, $WarnList, $P0Checks, $P0Pass, $P0Total, $RedLines, $LongTableAudit, $ExchangeAudit, $P49Audit, $SkillAudit)

  # NOTE: build every row as a SCALAR variable first, then Add it.
  # Putting "'..' + $x + '..'" directly inside a comma-separated @(...) literal
  # re-associates the + under the comma and silently splits the row into 3 items.
  $L = New-Object System.Collections.ArrayList

  Add-BriefLine $L $zh['title']
  Add-BriefLine $L ''
  $r = ('生成时间: ' + $SnapTs.ToString('yyyy-MM-dd HH:mm:ss') + ' (GMT+8)')
  Add-BriefLine $L $r
  $r = ('token: ' + $tokenName + ' (' + $tokenMode + ') | auth_ref: ' + $a01Tag)
  Add-BriefLine $L $r
  $r = ('模式: ' + $zh['sub'])
  Add-BriefLine $L $r
  Add-BriefLine $L ''
  Add-BriefLine $L $zh['head_agent']
  Add-BriefLine $L ''
  Add-BriefLine $L '| Agent | 当前状态 | 最近回执 / 时间 | 重要 flag |'
  Add-BriefLine $L '|---|---|---|---|'
  $c = $Agents.dshc
  $d = $Agents.dsha
  $s = $Agents.dshd
  $r = '| DSHC | ' + $c.state + ' | ' + $c.last_receipt + ' @ ' + $c.last_receipt_ts + ' | wind_api_calls=' + $c.wind_api_calls + '; token_state=' + $c.token_state + '; root=' + $c.spawn_bug_root + '; guard_rules=' + $c.guard_rules_count + ' |'
  Add-BriefLine $L $r
  $r = '| DSHA | ' + $d.state + ' | ' + $d.last_receipt + ' @ ' + $d.last_receipt_ts + ' | P68=' + $d.p68_lock + ' commit=' + $d.p68_commit + '; gate=' + $d.gate + '; permit=' + $d.release_permit + ' |'
  Add-BriefLine $L $r
  $r = '| DSHD | ' + $s.state + ' | poll#' + $s.poll_count + ' @ ' + $s.poll_ts + ' | audit_only=YES; excel_observer=ON; tag=' + $s.a01_tag + ' |'
  Add-BriefLine $L $r
  Add-BriefLine $L ''
  Add-BriefLine $L $zh['head_excel']
  Add-BriefLine $L ''
  Add-BriefLine $L '| 指标 | 值 |'
  Add-BriefLine $L '|---|---|'
  $r = '| Excel 进程总数 | ' + $ExcelRule.total_excel + ' |'
  Add-BriefLine $L $r
  $r = '| 非保护 PID 数 | ' + $ExcelRule.non_protected_excel + ' |'
  Add-BriefLine $L $r
  $r = '| 非保护且落入 DSHC 任务窗口的 PID 数 | ' + $ExcelRule.non_protected_in_task_window + ' |'
  Add-BriefLine $L $r
  $r = '| 告警阈值 (> ) | ' + $ExcelRule.threshold_gt + ' |'
  Add-BriefLine $L $r
  $r = '| 触发黄色告警 | ' + $ExcelRule.triggered + ' |'
  Add-BriefLine $L $r
  $r = '| 自动 kill | ' + $ExcelRule.auto_kill + ' |'
  Add-BriefLine $L $r
  $r = '| 保护 PID | ' + $ExcelRule.protected_pid + ' (' + $ExcelRule.protected_name + ') |'
  Add-BriefLine $L $r
  $r = '| 快采样间隔 (秒) | ' + $ExcelRule.fast_interval_sec + ' |'
  Add-BriefLine $L $r
  $r = ('| 快采样次数 / 观测到的 Excel 峰值 | ' + $ExcelRule.fast_sample_count + ' / ' + $ExcelRule.fast_max_total_excel + ' |')
  Add-BriefLine $L $r
  $r = '| 快采样中非保护且在窗口内峰值 | ' + $ExcelRule.fast_max_non_protected_in_task_window + ' |'
  Add-BriefLine $L $r
  $r = '| 快采样捕获的瞬时非保护 PID | ' + ($ExcelRule.fast_transient_pids -join ',') + ' |'
  Add-BriefLine $L $r
  $r = '| 合并触发判定 (定点 OR 快采样) | ' + $ExcelRule.combined_trigger + ' |'
  Add-BriefLine $L $r
  Add-BriefLine $L ''
  Add-BriefLine $L $zh['head_territ']
  Add-BriefLine $L ''
  $r = ('契约状态: ACTIVE | 领地条目: ' + $TerritoryState.entry_count + ' | 扫描模式: ' + $TerritoryState.scan_mode)
  Add-BriefLine $L $r
  $r = ('并发写入冲突数: ' + $TerritoryState.conflict_count)
  Add-BriefLine $L $r
  Add-BriefLine $L ''
  $tcRows = @()
  foreach ($t in $TerritoryState.conflicts) {
    $r = ('- [' + $t.severity + '] ' + $t.code + ' :: ' + $t.relative_path + ' :: ' + $t.detail)
    $tcRows += $r
  }
  if ($tcRows.Count -eq 0) { $tcRows += '- 无冲突记录' }
  Add-BriefLine $L ([string]::Join("`n", $tcRows))
  Add-BriefLine $L ''
  Add-BriefLine $L $zh['head_csv']
  Add-BriefLine $L ''
  Add-BriefLine $L '| 项 | 值 |'
  Add-BriefLine $L '|---|---|'
  $r = '| hash A (字节读 SHA256) | ' + $DualHash.hash_a_byte_read + ' |'
  Add-BriefLine $L $r
  $r = '| hash B (Get-FileHash) | ' + $DualHash.hash_b_getfilehash + ' |'
  Add-BriefLine $L $r
  $r = '| A == B | ' + $DualHash.a_eq_b + ' |'
  Add-BriefLine $L $r
  $r = '| DSHC ref (A03 csv_output) | ' + $DualHash.ref_a03_csv_output + ' |'
  Add-BriefLine $L $r
  $r = '| 匹配 A03 引用 | ' + $DualHash.matches_ref_a03 + ' |'
  Add-BriefLine $L $r
  $r = '| 匹配 P80 历史观测 | ' + $DualHash.matches_ref_a01_prior + ' |'
  Add-BriefLine $L $r
  $r = '| 扫描结论 | ' + $DualHash.scan_status + ' |'
  Add-BriefLine $L $r
  $r = '| 告警码 | ' + $DualHash.mismatch_code + ' |'
  Add-BriefLine $L $r
  $r = ('| 文件大小 | ' + $QuickScan.size_bytes + ' B (P68 下限 ' + $QuickScan.min_size_required + ') |')
  Add-BriefLine $L $r
  $r = ('| 行数 / 数据行 | ' + $QuickScan.rough_lines + ' / ' + $QuickScan.data_rows + ' (P68 下限 ' + $QuickScan.min_rows_required + ') |')
  Add-BriefLine $L $r
  $r = '| 缺关键词 | ' + $QuickScan.keywords_missing_count + ' |'
  Add-BriefLine $L $r
  $r = '| 最大连续空行 | ' + $QuickScan.max_consecutive_blank + ' |'
  Add-BriefLine $L $r
  $r = '| Quick-Scan 结论 | ' + $QuickScan.scan_status + ' |'
  Add-BriefLine $L $r
  Add-BriefLine $L '| 熔断 | 未触发 (DSHA-P68 为唯一受理权威) |'
  Add-BriefLine $L ''
  Add-BriefLine $L $zh['head_board']
  Add-BriefLine $L ''
  if ($WarnList.Count -eq 0) {
    $r = ('**' + $zh['calm'] + '** （零告警标签）')
    Add-BriefLine $L $r
  } else {
    $wRows = @()
    foreach ($w in $WarnList) {
      $r = ('- [' + $w.severity + '] ' + $w.code + ' @ ' + $w.ts + ' :: ' + $w.detail)
      $wRows += $r
    }
    Add-BriefLine $L ([string]::Join("`n", $wRows))
  }
  Add-BriefLine $L ''
  Add-BriefLine $L $zh['head_exch']
  Add-BriefLine $L ''
  Add-BriefLine $L '| 指标 | 值 |'
  Add-BriefLine $L '|---|---|'
  $r = ('| 校验模式 | ' + $LongTableAudit.mode + ' (auto_intervene=' + $LongTableAudit.auto_intervene + ') |')
  Add-BriefLine $L $r
  $r = ('| 表格式 | ' + $LongTableAudit.format + ' |')
  Add-BriefLine $L $r
  $r = ('| 数据行数 | ' + $LongTableAudit.data_rows + ' |')
  Add-BriefLine $L $r
  $r = '| 主键 | date + symbol + indicator |'
  Add-BriefLine $L $r
  $r = ('| 主键重复数 | ' + $LongTableAudit.duplicate_key_count + ' |')
  Add-BriefLine $L $r
  $r = ('| 结构缺陷 (malformed / blank_key / bad_date / non_numeric) | ' + $LongTableAudit.malformed_row_count + ' / ' + $LongTableAudit.blank_key_field_count + ' / ' + $LongTableAudit.bad_date_count + ' / ' + $LongTableAudit.non_numeric_value_count + ' |')
  Add-BriefLine $L $r
  $r = ('| 日期区间 | ' + $LongTableAudit.date_min + ' -> ' + $LongTableAudit.date_max + ' |')
  Add-BriefLine $L $r
  $r = ('| 品种数 / 指标数 / 来源数 | ' + $LongTableAudit.distinct_symbol_count + ' / ' + $LongTableAudit.distinct_indicator_count + ' / ' + $LongTableAudit.distinct_source_count + ' |')
  Add-BriefLine $L $r
  $r = ('| 指标列表 | ' + ($LongTableAudit.indicators -join ', ') + ' |')
  Add-BriefLine $L $r
  $wlVio = '无'
  if ($LongTableAudit.symbols_not_whitelisted.Count -gt 0) { $wlVio = ($LongTableAudit.symbols_not_whitelisted -join ',') }
  $r = ('| 白名单外品种 | ' + $wlVio + ' |')
  Add-BriefLine $L $r
  $indMiss = '无'
  if ($LongTableAudit.indicators_missing.Count -gt 0) { $indMiss = ($LongTableAudit.indicators_missing -join ',') }
  $r = ('| 缺失指标 | ' + $indMiss + ' |')
  Add-BriefLine $L $r
  $r = ('| 交易所归属不匹配 / 未知交易所 | ' + $LongTableAudit.exchange_mismatch_count + ' / ' + $LongTableAudit.exchange_unknown_count + ' |')
  Add-BriefLine $L $r
  $r = ('| 长表审计结论 | ' + $LongTableAudit.audit_status + ' |')
  Add-BriefLine $L $r
  Add-BriefLine $L ''
  Add-BriefLine $L '| 品种 | 实际交易所 | 应属交易所 | 结论 |'
  Add-BriefLine $L '|---|---|---|---|'
  $bindRows = @()
  foreach ($b in $LongTableAudit.symbol_exchange_bindings) {
    $r = ('| ' + $b.symbol + ' | ' + $b.actual_exchange + ' | ' + $b.expected_exchange + ' | ' + $b.verdict + ' |')
    $bindRows += $r
  }
  Add-BriefLine $L ([string]::Join("`n", $bindRows))
  Add-BriefLine $L ''
  $r = ('DSHC 归属档案扫描: 文件 ' + $ExchangeAudit.files_scanned + ' 个; 命中品种令牌 ' + $ExchangeAudit.symbol_tokens_total + ' 个; 交易所归属异常 ' + $ExchangeAudit.mismatch_count + ' 个')
  Add-BriefLine $L $r
  $amRows = @()
  foreach ($m in $ExchangeAudit.mismatches) {
    $r = ('- [' + $m.verdict + '] ' + $m.symbol + ' :: ' + $m.detail + ' :: NO_DATA=' + $m.no_data_present_in_files + ' :: files=' + ($m.files -join ','))
    $amRows += $r
  }
  if ($amRows.Count -gt 0) { Add-BriefLine $L ([string]::Join("`n", $amRows)) }
  Add-BriefLine $L ''
  Add-BriefLine $L $zh['head_p49']
  Add-BriefLine $L ''
  Add-BriefLine $L '| 指标 | 值 |'
  Add-BriefLine $L '|---|---|'
  $r = ('| 审计模式 | 只读 (' + $P49Audit.mode + ', auto_intervene=' + $P49Audit.auto_intervene + ') |')
  Add-BriefLine $L $r
  $r = ('| 目录存在 | ' + $P49Audit.exists + ' |')
  Add-BriefLine $L $r
  $r = ('| 文件数 / 期望数 / 总字节 | ' + $P49Audit.file_count + ' / ' + $P49Audit.expected_file_count + ' / ' + $P49Audit.total_bytes + ' |')
  Add-BriefLine $L $r
  $r = ('| MANIFEST 状态 | ' + $P49Audit.manifest_status + ' |')
  Add-BriefLine $L $r
  $r = ('| MANIFEST 最后写入 | ' + $P49Audit.manifest_last_write + ' (readable=' + $P49Audit.manifest_readable + ') |')
  Add-BriefLine $L $r
  $r = ('| 声明产物来源 | ' + $P49Audit.expected_source + ' (' + $P49Audit.manifest_declared_count + ' 个) |')
  Add-BriefLine $L $r
  $r = ('| MANIFEST gate / release_permit | ' + $P49Audit.manifest_gate + ' / ' + $P49Audit.manifest_release_permit + ' |')
  Add-BriefLine $L $r
  $r = ('| MANIFEST LC_GFE | ' + $P49Audit.manifest_lc_gfe + ' |')
  Add-BriefLine $L $r
  $r = ('| wind_api_calls / real_wind_call | ' + $P49Audit.manifest_wind_api_calls + ' / ' + $P49Audit.manifest_real_wind_call + ' |')
  Add-BriefLine $L $r
  $p49Miss = '无'
  if ($P49Audit.missing_files.Count -gt 0) { $p49Miss = ($P49Audit.missing_files -join ',') }
  $r = ('| 缺失产物 | ' + $p49Miss + ' |')
  Add-BriefLine $L $r
  $p49Chg = '无'
  if ($P49Audit.hash_changed_files.Count -gt 0) { $p49Chg = ($P49Audit.hash_changed_files -join ',') }
  $r = ('| 本轮哈希变更 | ' + $p49Chg + ' |')
  Add-BriefLine $L $r
  $r = ('| exchange 列与品种后缀不一致行数 | ' + $P49Audit.exchange_column_mismatch_count + ' |')
  Add-BriefLine $L $r
  $r = ('| P49 审计结论 | ' + $P49Audit.audit_status + ' |')
  Add-BriefLine $L $r
  Add-BriefLine $L ''
  Add-BriefLine $L '| 产物 | 字节 | SHA256 | 本轮变化 |'
  Add-BriefLine $L '|---|---|---|---|'
  $p49Rows = @()
  foreach ($f in $P49Audit.files) {
    $h = [string]$f.sha256
    if ($h.Length -gt 16) { $h = $h.Substring(0, 16) + '...' }
    $r = ('| ' + $f.relative_path + ' | ' + $f.size_bytes + ' | ' + $h + ' | ' + $f.change + ' |')
    $p49Rows += $r
  }
  Add-BriefLine $L ([string]::Join("`n", $p49Rows))
  Add-BriefLine $L ''
  Add-BriefLine $L ''
  Add-BriefLine $L $zh['head_skill']
  Add-BriefLine $L ''
  Add-BriefLine $L '| 指标 | 值 |'
  Add-BriefLine $L '|---|---|'
  $r = ('| 审计模式 | 只读 (' + $SkillAudit.mode + ', auto_intervene=' + $SkillAudit.auto_intervene + ') |')
  Add-BriefLine $L $r
  $r = ('| 目录存在 | ' + $SkillAudit.exists + ' |')
  Add-BriefLine $L $r
  $r = ('| 文件数 / 总字节 / manifest 声明数 | ' + $SkillAudit.file_count + ' / ' + $SkillAudit.total_bytes + ' / ' + $SkillAudit.declared_count + ' |')
  Add-BriefLine $L $r
  $r = ('| skill_id / version | ' + $SkillAudit.skill_id + ' / ' + $SkillAudit.version + ' |')
  Add-BriefLine $L $r
  $r = ('| version_locked / status | ' + $SkillAudit.version_locked + ' / ' + $SkillAudit.status + ' |')
  Add-BriefLine $L $r
  $r = ('| locked_at / locked_by | ' + $SkillAudit.locked_at + ' / ' + $SkillAudit.locked_by + ' |')
  Add-BriefLine $L $r
  $r = ('| manifest 最后写入 | ' + $SkillAudit.manifest_last_write + ' (readable=' + $SkillAudit.manifest_readable + ') |')
  Add-BriefLine $L $r
  $h0 = [string]$SkillAudit.manifest_sha256
  if ($h0.Length -gt 16) { $h0 = $h0.Substring(0, 16) + '...' }
  $r = ('| manifest SHA256 | ' + $h0 + ' (本轮变更=' + $SkillAudit.manifest_hash_changed + ') |')
  Add-BriefLine $L $r
  $r = ('| version 变更 | ' + $SkillAudit.previous_version + ' -> ' + $SkillAudit.version + ' (changed=' + $SkillAudit.skill_version_changed + ') |')
  Add-BriefLine $L $r
  $r = ('| 声明外文件 / 声明缺失 | ' + $SkillAudit.undeclared_files.Count + ' / ' + $SkillAudit.declared_missing_files.Count + ' |')
  Add-BriefLine $L $r
  $r = ('| 本轮 新增 / 修改 / 删除 (cold_start=' + $SkillAudit.cold_start + ') | ' + $skillAudit.added_files.Count + ' / ' + $SkillAudit.modified_files.Count + ' / ' + $SkillAudit.removed_files.Count + ' |')
  Add-BriefLine $L $r
  $r = ('| V1 冻结违规 | ' + $SkillAudit.v1_frozen_violation + ' |')
  Add-BriefLine $L $r
  $r = ('| constraint wind_api_calls / offline_only | ' + $SkillAudit.constraint_wind_api_calls + ' / ' + $SkillAudit.constraint_offline_only + ' |')
  Add-BriefLine $L $r
  $r = ('| f01_script_locked / f01_script_version | ' + $SkillAudit.constraint_f01_script_locked + ' / ' + $SkillAudit.constraint_f01_script_version + ' |')
  Add-BriefLine $L $r
  $r = ('| manifest original_csv_sha256 与实际 CSV 一致 | ' + $SkillAudit.original_csv_sha256_match + ' |')
  Add-BriefLine $L $r
  $r = ('| skill 审计结论 | ' + $SkillAudit.audit_status + ' |')
  Add-BriefLine $L $r
  Add-BriefLine $L ''
  Add-BriefLine $L '| 文件 | 字节 | SHA256 | 已声明 | 本轮变化 |'
  Add-BriefLine $L '|---|---|---|---|---|'
  $skRows = @()
  foreach ($f in $SkillAudit.files) {
    $h1 = [string]$f.sha256
    if ($h1.Length -gt 16) { $h1 = $h1.Substring(0, 16) + '...' }
    $r = ('| ' + $f.relative_path + ' | ' + $f.size_bytes + ' | ' + $h1 + ' | ' + $f.declared + ' | ' + $f.change + ' |')
    $skRows += $r
  }
  if ($skRows.Count -eq 0) { $skRows += '| (空目录) | - | - | - | - |' }
  Add-BriefLine $L ([string]::Join("`n", $skRows))
  Add-BriefLine $L ''
  Add-BriefLine $L $zh['head_p0']
  Add-BriefLine $L ''
  $r = ('P0 校验: ' + $P0Pass + '/' + $P0Total)
  Add-BriefLine $L $r
  $p0Rows = @()
  foreach ($k in $P0Checks.Keys) {
    $v = $P0Checks[$k]
    $mark = 'PASS'
    if ($v.result -eq $false) { $mark = 'FAIL' }
    $r = ('- [' + $mark + '] ' + $k + ' = ' + $v.detail)
    $p0Rows += $r
  }
  Add-BriefLine $L ([string]::Join("`n", $p0Rows))
  Add-BriefLine $L ''
  Add-BriefLine $L $zh['head_red']
  Add-BriefLine $L ''
  $r = ('- audit_only = ' + $RedLines.audit_only)
  Add-BriefLine $L $r
  $r = ('- processes_untouched = ' + $RedLines.processes_untouched + ' / no_kill_executed = ' + $RedLines.no_kill_executed)
  Add-BriefLine $L $r
  $r = ('- gate_unchanged = ' + $RedLines.gate_unchanged + ' (observed: ' + $RedLines.gate_observed + ')')
  Add-BriefLine $L $r
  $r = ('- release_permit_not_issued = ' + $RedLines.release_permit_not_issued + ' (observed: ' + $RedLines.release_permit_observed + ')')
  Add-BriefLine $L $r
  $r = ('- dshd_runs_backtest = ' + $RedLines.dshd_runs_backtest)
  Add-BriefLine $L $r
  $r = ('- dshd_fetches_for_dshc = ' + $RedLines.dshd_fetches_for_dshc)
  Add-BriefLine $L $r
  $r = ('- dshd_bypasses_dsha_p68 = ' + $RedLines.dshd_bypasses_dsha_p68)
  Add-BriefLine $L $r
  $r = ('- output_csv_touched = ' + $RedLines.output_csv_touched)
  Add-BriefLine $L $r
  $r = ('- intervention = ' + $RedLines.intervention)
  Add-BriefLine $L $r
  $r = ('- wind_api_calls = ' + $RedLines.wind_api_calls)
  Add-BriefLine $L $r
  Add-BriefLine $L ''

  return ([string]::Join("`n", ([string[]]$L.ToArray())))
}

# ---------------- MAIN LOOP ----------------
$startTs = Get-Date
$pollNo = 0
$prevTerritory = $null
$warnBoard = @()
$excelHistory = @()
$fastBuffer = @()
$prevP49 = $null
$prevSkill = $null
$p49CompleteReported = $false
$p49PostSealFirstReported = $false
$p49PostSealMutationPolls = 0
$skillFirstReported = $false
$exchPrevMismatchCount = -1
$exchClearedReported = $false

Write-Host ("[{0}] {1} {2} v{3} START | tag={4} | token={5} | mode={6}" -f (Get-Date).ToString('HH:mm:ss'), $agentName, $taskName, $scriptVersion, $a01Tag, $tokenName, $tokenMode)

while ($true) {
  $pollNo++
  $pollTs = Get-Date
  $pollStart = Get-Date
  $pollErr = $false
  $errText = ''
  $agents = $null; $excelRule = $null; $territoryState = $null
  $dualHash = $null; $quickScan = $null; $trackState = $null
  $warnList = @(); $p0Checks = @{}; $p0Pass = 0
  $snaps = @(); $dshcWindow = $null
  $dshcWindowStart = $null; $dshcWindowEnd = $null; $dshcHits = 0
  $bomInfo = @{}
  $watchStatus = @{}
  $longTableAudit = $null; $attribAudit = $null; $p49Audit = $null; $skillAudit = $null
  $selfAlive = $true

  try {
    # ---------- P0: process + peer watcher liveness ----------
    $mainAlive = Test-PidAlive $protectMainPid
    $excelAlive = Test-PidAlive $protectExcelPid
    foreach ($w in $watchScripts) {
      $minAge = 120
      if ($w.name -eq 'self') { $minAge = 0 }
      $res = Get-ScriptWatchAlive $w.script $minAge
      $watchStatus[$w.name] = @{alive = $res.alive; pid_count = $res.pid_count; pids = $res.pids; label = $w.label; min_age_sec = $minAge}
      if ($w.name -eq 'self') { $selfAlive = $res.alive }
    }
    $bomInfo = Get-BomStatus $scriptPath

    # ---------- tracking log derived state ----------
    $trackState = Get-TrackingState $auditLog
    $dshcWindow = Get-DshcTaskWindow $auditLog $dshcWindowFallbackH
    $dshcWindowStart = $dshcWindow.window_start
    $dshcWindowEnd = $dshcWindow.window_end
    $dshcHits = $dshcWindow.event_hits

    # ---------- Excel drift observer ----------
    $snaps = Get-ExcelSnapshot $dshcWindowStart
    $excelRule = Test-ExcelSpawnRule $snaps

    # merge fast Excel samples collected during the previous sleep window.
    # Rationale: a real transient did occur at 2026-10-19T08:48 (DSHD-P80 and
    # DSHD-P80-PHASE2 both raised CIRCUIT_BREAKER_READY 'Multiple Excel
    # instances: 2 (possible WDF bombing)') and it vanished inside one 5-minute
    # poll window. 20s sub-cadence closes that blind spot. Observation only.
    $fastSampleCount = 0
    $fastMaxTotal = 0
    $fastMaxNonProtWin = 0
    $fastTransientPids = @()
    $fastTransient = $false
    $fastRows = @()
    foreach ($fs in $fastBuffer) {
      if ($null -eq $fs) { continue }
      $fastSampleCount++
      if ($fs.total_excel -gt $fastMaxTotal) { $fastMaxTotal = $fs.total_excel }
      if ($fs.non_protected_in_task_window -gt $fastMaxNonProtWin) { $fastMaxNonProtWin = $fs.non_protected_in_task_window }
      foreach ($fp in $fs.non_protected_pids) { if ($null -ne $fp -and ($fastTransientPids -notcontains $fp)) { $fastTransientPids += $fp } }
      if ($fs.non_protected -gt 0) { $fastTransient = $true }
      $fastRows += @{
        ts = $fs.ts
        total_excel = $fs.total_excel
        non_protected = $fs.non_protected
        non_protected_in_task_window = $fs.non_protected_in_task_window
        non_protected_pids = $fs.non_protected_pids
        triggered = $fs.triggered
      }
    }
    $excelRule.fast_sample_count = $fastSampleCount
    $excelRule.fast_interval_sec = $excelFastIntervalSec
    $excelRule.fast_max_total_excel = $fastMaxTotal
    $excelRule.fast_max_non_protected_in_task_window = $fastMaxNonProtWin
    $excelRule.fast_transient_non_protected_seen = $fastTransient
    $excelRule.fast_transient_pids = $fastTransientPids
    $excelRule.fast_samples = $fastRows
    $excelRule.fast_transient_warning = ($fastMaxNonProtWin -gt $excelRule.threshold_gt)
    $excelRule.combined_trigger = ($excelRule.triggered -or $excelRule.fast_transient_warning)
    $excelRule.detection_caveat = ('poll cadence ' + $pollIntervalSec + 's is blind to transients shorter than ' + $excelFastIntervalSec + 's; fast sampler covers ' + $excelFastIntervalSec + 's granularity')
    $fastBuffer = @()
    $histEntry = @{
      ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')
      total_excel = $excelRule.total_excel
      non_protected = $excelRule.non_protected_excel
      non_protected_in_window = $excelRule.non_protected_in_task_window
      triggered = $excelRule.triggered
    }
    $excelHistory += $histEntry
    if ($excelHistory.Count -gt $histKeepMax) { $excelHistory = @($excelHistory[($excelHistory.Count - $histKeepMax)..($excelHistory.Count - 1)]) }

    # ---------- territory conflict scan ----------
    $territoryState = Get-TerritoryState $monitoredPaths $prevTerritory
    $prevTerritory = $territoryState.next_state

    # ---------- CSV dual hash + quick scan ----------
    $dualHash = Get-DualHash $csvPath
    $quickScan = Get-QuickScan $csvPath

    # ---------- EXT: long-table integrity + exchange binding + P49 artifact audit ----------
    $longTableAudit = Get-LongTableAudit $csvPath
    $attribAudit = Get-ExchangeAttributionAudit
    $p49Audit = Get-P49Audit $prevP49
    $prevP49 = $p49Audit.state_snapshot
    $skillAudit = Get-SkillDirAudit $prevSkill
    $prevSkill = $skillAudit.state_snapshot
    if ($p49Audit.post_seal_archive_modify_alert -eq $true) { $p49PostSealMutationPolls = ([int]$p49PostSealMutationPolls) + 1 } else { $p49PostSealMutationPolls = 0 }

    # ---------- 3-agent board ----------
    $agents = Get-ClusterAgents $trackState $excelRule $pollNo $pollTs

    # ---------- warnings ----------
    if ($excelRule.triggered) {
      $warnList += @{code = 'OBS-SPAWN-EXCEL-001'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('non-protected Excel spawned inside DSHC task window = ' + $excelRule.non_protected_in_task_window + ' > threshold ' + $excelRule.threshold_gt + '; observation only, no kill')}
    }
    if ($excelRule.fast_transient_warning) {
      $warnList += @{code = 'OBS-SPAWN-EXCEL-001-TRANSIENT'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('non-protected Excel inside DSHC window caught by ' + $excelFastIntervalSec + 's fast sampler (max=' + $excelRule.fast_max_non_protected_in_task_window + ' > threshold ' + $excelRule.threshold_gt + ', samples=' + $excelRule.fast_sample_count + ', pids=' + ($excelRule.fast_transient_pids -join ',') + '); survived only between polls; observation only, no kill')}
    }
    if ($dualHash.warning_raised) {
      $warnList += @{code = $dualHash.mismatch_code; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('hash A==B but differs from DSHC cross_agent reference; reference likely stale (scan_status=' + $dualHash.scan_status + ')')}
    }
    foreach ($c in $territoryState.conflicts) {
      $warnList += @{code = $c.code; severity = $c.severity; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ($c.relative_path + ' :: ' + $c.detail + (': from=' + $c.from_tag + ' to=' + $c.to_tag))}
    }
    if ($quickScan.blank_alarm) {
      $warnList += @{code = 'A01_CSV_BLANK_RUN'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('max consecutive blank lines = ' + $quickScan.max_consecutive_blank)}
    }
    # ---------- EXT: long-table + exchange + P49 warnings (record only) ----------
    foreach ($b in $longTableAudit.symbol_exchange_bindings) {
      if ($b.verdict -eq 'MISMATCH') {
        $warnList += @{code = 'EXCH-001-MISMATCH'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('CSV symbol ' + $b.symbol + ' :: ' + $b.detail)}
      } elseif ($b.verdict -eq 'UNKNOWN_EXCHANGE') {
        $warnList += @{code = 'EXCH-001-UNKNOWN-EXCHANGE'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('CSV symbol ' + $b.symbol + ' :: ' + $b.detail)}
      }
    }
    foreach ($m in $attribAudit.mismatches) {
      $warnList += @{code = 'EXCH-001-ATTRIBUTED-MISMATCH'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('DSHC artifact references ' + $m.symbol + ' (' + $m.verdict + ') :: ' + $m.detail + '; no_data_present=' + $m.no_data_present_in_files + '; files=' + ($m.files -join ',') + '; observation only, no intervention')}
    }
    if ($longTableAudit.duplicate_key_count -gt 0) {
      $warnList += @{code = 'CSVINT-001-DUP-KEY'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('long-table duplicate primary keys (date|symbol|indicator) = ' + $longTableAudit.duplicate_key_count + '; samples=' + ($longTableAudit.duplicate_key_samples -join ';') + '; observation only')}
    }
    if (($longTableAudit.malformed_row_count -gt 0) -or ($longTableAudit.blank_key_field_count -gt 0) -or ($longTableAudit.bad_date_count -gt 0) -or ($longTableAudit.non_numeric_value_count -gt 0)) {
      $warnList += @{code = 'CSVINT-001-STRUCTURE'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('malformed_rows=' + $longTableAudit.malformed_row_count + '; blank_key_fields=' + $longTableAudit.blank_key_field_count + '; bad_dates=' + $longTableAudit.bad_date_count + '; non_numeric_values=' + $longTableAudit.non_numeric_value_count + '; observation only')}
    }
    foreach ($s in $longTableAudit.symbols_not_whitelisted) {
      $warnList += @{code = 'CSVINT-002-SYMBOL-NOT-WHITELISTED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('symbol ' + $s + ' is outside the DSHD whitelist: ' + ($csvSymbolWhitelist -join ','))}
    }
    if ($longTableAudit.indicators_missing.Count -gt 0) {
      $warnList += @{code = 'CSVINT-003-INDICATOR-MISSING'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('expected indicator absent from long table: ' + ($longTableAudit.indicators_missing -join ','))}
    }
    if ($longTableAudit.indicators_unexpected.Count -gt 0) {
      $warnList += @{code = 'CSVINT-003-INDICATOR-UNEXPECTED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('unexpected indicator present in long table: ' + ($longTableAudit.indicators_unexpected -join ','))}
    }
    if ($p49Audit.missing_files.Count -gt 0) {
      $warnList += @{code = 'P49-001-ARTIFACT-MISSING'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('artifacts/p49_backtest missing expected file(s): ' + ($p49Audit.missing_files -join ','))}
    }
    if ($p49Audit.removed_files.Count -gt 0) {
      $warnList += @{code = 'P49-001-ARTIFACT-REMOVED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('artifacts/p49_backtest file(s) removed since last poll: ' + ($p49Audit.removed_files -join ','))}
    }
    if ($p49Audit.hash_changed_files.Count -gt 0) {
      $warnList += @{code = 'P49-001-HASH-CHANGED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('artifacts/p49_backtest hash change since last poll: ' + ($p49Audit.hash_changed_files -join ',') + '; read-only audit, no intervention')}
    }
    if ($p49Audit.under_min_size_files.Count -gt 0) {
      $warnList += @{code = 'P49-001-FILE-BENEATH-MIN-SIZE'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('p49 artifact beneath ' + $p49MinFileSize + 'B: ' + ($p49Audit.under_min_size_files -join ',') + '; observation only')}
    }
    if ($p49Audit.exchange_column_mismatch_count -gt 0) {
      $warnList += @{code = 'P49-001-EXCHANGE-COL-MISMATCH'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('p49 symbol_performance.csv exchange column disagrees with the symbol suffix on ' + $p49Audit.exchange_column_mismatch_count + ' row(s); observation only')}
    }
    # TWEAK (DSHD-P81-TWEAK): umbrella post-seal mutation label. Fires
    # every poll for as long as the COMPLETE-sealed archive keeps
    # mutating; the granular codes above carry the per-kind detail.
    # Recorded to warning_board.json and to the audit ledger.
    if ($p49Audit.post_seal_archive_modify_alert -eq $true) {
      $warnList += @{code = 'P49-001-ARTIFACT-UNEXPECTED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('P49 archive sealed (MANIFEST.status=' + $p49Audit.manifest_status + ' at ' + $p49Audit.manifest_sealed_at + ') but mutated post-seal: kinds=' + ($p49Audit.post_seal_mutation_kinds -join ',') + '; continuous_alert_polls=' + $p49PostSealMutationPolls + '; cold_start=' + $p49Audit.cold_start + '; undeclared=' + ($p49Audit.unexpected_files -join ',') + '; modified=' + ($p49Audit.hash_changed_files -join ',') + '; removed=' + ($p49Audit.removed_files -join ',') + '; declared_missing=' + ($p49Audit.missing_files -join ',') + '; observation only, no intervention')}
    } elseif ($p49Audit.unexpected_files.Count -gt 0) {
      $warnList += @{code = 'P49-001-ARTIFACT-UNEXPECTED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('artifacts/p49_backtest contains file(s) not in the declared expected set: ' + ($p49Audit.unexpected_files -join ',') + '; observation only, no intervention')}
    }
    # ---------- TWEAK: FACTOR_EXTRACT_V1 skill dir hash warnings ----------
    if ($skillAudit.exists -eq $false) {
      $warnList += @{code = 'SKILL-001-DIR-ABSENT'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('artifacts/skill_lib/factor_v1 is absent; skill version monitoring idle; observation only')}
    } else {
      if ($skillAudit.skill_version_changed -eq $true) {
        $warnList += @{code = 'SKILL-001-VERSION-CHANGED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('FACTOR_EXTRACT_V1 version changed from ' + $skillAudit.previous_version + ' to ' + $skillAudit.version + '; manifest.status=' + $skillAudit.status + '; observation only, no intervention')}
      }
      if ($skillAudit.manifest_hash_changed -eq $true) {
        $warnList += @{code = 'SKILL-001-MANIFEST-CHANGED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('skill manifest.json hash changed (sha256=' + $skillAudit.manifest_sha256 + '); version=' + $skillAudit.version + '; version_locked=' + $skillAudit.version_locked + '; observation only')}
      }
      if ($skillAudit.v1_frozen_violation -eq $true) {
        $warnList += @{code = 'SKILL-001-V1-FROZEN-VIOLATION'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('version_locked=true but declared V1 file(s) modified in place: ' + ($skillAudit.v1_frozen_violation_files -join ',') + '; iteration_policy=' + $skillAudit.iteration_policy + '; observation only, no intervention')}
      }
      if (($skillAudit.cold_start -eq $false) -and ($skillAudit.modified_files.Count -gt 0)) {
        $warnList += @{code = 'SKILL-001-FILE-MODIFIED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('skill dir hash change since last poll: ' + ($skillAudit.modified_files -join ',') + '; read-only audit, no intervention')}
      }
      if (($skillAudit.cold_start -eq $false) -and ($skillAudit.added_files.Count -gt 0)) {
        $warnList += @{code = 'SKILL-001-FILE-ADDED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('skill dir file(s) added since last poll: ' + ($skillAudit.added_files -join ',') + '; observation only')}
      }
      if (($skillAudit.cold_start -eq $false) -and ($skillAudit.removed_files.Count -gt 0)) {
        $warnList += @{code = 'SKILL-001-FILE-REMOVED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('skill dir file(s) removed since last poll: ' + ($skillAudit.removed_files -join ',') + '; observation only')}
      }
      if ($skillAudit.undeclared_files.Count -gt 0) {
        $warnList += @{code = 'SKILL-001-FILE-UNDECLARED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('skill dir contains file(s) not declared in manifest.json: ' + ($skillAudit.undeclared_files -join ',') + '; declared_count=' + $skillAudit.declared_count + '; observation only')}
      }
      if ($skillAudit.declared_missing_files.Count -gt 0) {
        $warnList += @{code = 'SKILL-001-FILE-DECLARED-MISSING'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('manifest.json declares file(s) absent from the skill dir: ' + ($skillAudit.declared_missing_files -join ',') + '; observation only')}
      }
      if (($skillAudit.data_integrity_original_sha256.Length -gt 0) -and ($skillAudit.original_csv_sha256_match -eq $false)) {
        $warnList += @{code = 'SKILL-001-DATA-SHA-MISMATCH'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('manifest data_integrity.original_csv_sha256=' + $skillAudit.data_integrity_original_sha256 + ' vs actual_csv_sha256=' + $skillAudit.original_csv_sha256_actual + '; observation only')}
      }
    }
    # ---------- TWEAK: exchange binding auto-clear transition ----------
    if (($exchPrevMismatchCount -gt 0) -and ($attribAudit.mismatch_count -eq 0)) {
      $exchClearedReported = $true
      $warnList += @{code = 'EXCH-001-ATTRIBUTED-MISMATCH-CLEARED'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('DSHC exchange binding repaired: attributed mismatch count went ' + $exchPrevMismatchCount + ' -> 0; EXCH-001-MISMATCH / EXCH-001-ATTRIBUTED-MISMATCH labels auto-cleared from the board; LC.SHF verdict=' + $attribAudit.lc_shf_verdict + '; LC.GFE verdict=' + $attribAudit.lc_gfe_verdict + '; repaired=' + $attribAudit.lc_binding_repaired + '; observation only')}
    }

    $exchPrevMismatchCount = $attribAudit.mismatch_count
    # ---------- P0 checks ----------
    $chk = @{
      pid_3472 = @{result = $mainAlive; detail = $(if ($mainAlive) { 'ALIVE' } else { 'DEAD' })}
      excel_pid_14644 = @{result = $excelAlive; detail = $(if ($excelAlive) { 'ALIVE (protected)' } else { 'DEAD' })}
      pwsh_13_p77 = @{result = $watchStatus['pwsh-13'].alive; detail = ('pids=' + $watchStatus['pwsh-13'].pid_count)}
      pwsh_30_p80 = @{result = $watchStatus['pwsh-30'].alive; detail = ('pids=' + $watchStatus['pwsh-30'].pid_count)}
      pwsh_37_phase2 = @{result = $watchStatus['pwsh-37'].alive; detail = ('pids=' + $watchStatus['pwsh-37'].pid_count)}
      self_p81 = @{result = $selfAlive; detail = ('pids=' + $watchStatus['self'].pid_count)}
      gate_closed = @{result = ($trackState.gate -match 'CLOSED'); detail = $trackState.gate + ' (line ' + $trackState.gate_line_no + ')'}
      permit_not_issued = @{result = ($trackState.release_permit -match 'NOT_ISSUED'); detail = $trackState.release_permit + ' (line ' + $trackState.permit_line_no + ')'}
      script_bom_intact = @{result = $bomInfo.has_bom; detail = ('bom=' + $bomInfo.has_bom + ' size=' + $bomInfo.size_bytes)}
    }
    $p0Checks = $chk
    $p0Total = 0; $p0Pass = 0
    foreach ($k in $chk.Keys) {
      $p0Total++
      if ($chk[$k].result -eq $true) { $p0Pass++ }
    }
    $p0AllPass = ($p0Pass -eq $p0Total)

    $redLines = Get-RedLineStatus $trackState $trackState.wind_api_calls

    # ---------- write territory contract ----------
    $contract = Build-TerritoryContract $pollNo $territoryState $pollTs
    Write-Utf8File $outTerritory (($contract | ConvertTo-Json -Depth 12))

    # ---------- write cluster board ----------
    $cluster = @{
      contract_id = 'DSHD-CLUSTER-STATUS-BOARD-V1'
      version = '1.0'
      generated_at = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')
      agent = $agentName
      task = $taskName
      a01_tag = $a01Tag
      token = $tokenName
      token_state = $tokenState
      branch = $branch
      poll_count = $pollNo
      poll_interval_sec = $pollIntervalSec
      watch_started_at = $startTs.ToString('yyyy-MM-ddTHH:mm:sszzz')
      mode = 'AUDIT_READ_ONLY'
      p0_checks_passed = $p0Pass
      p0_checks_total = $p0Total
      p0_all_pass = $p0AllPass
      p0_checks = $p0Checks
      peer_watchers = $watchStatus
      process_protection = @{
        pid_3472 = @{alive = $mainAlive; role = $protectMainName; never_kill = $true}
        pid_14644 = @{alive = $excelAlive; role = $protectExcelName; never_kill = $true}
        self_script_bom = $bomInfo
      }
      agents = $agents
      dshc_task_window = @{
        start = $(if ($null -ne $dshcWindowStart) { $dshcWindowStart.ToString('s') } else { '' })
        end = $(if ($null -ne $dshcWindowEnd) { $dshcWindowEnd.ToString('s') } else { '' })
        dshc_event_hits = $dshcHits
        source = 'tracking_monitor_audit.jsonl (agent~=DSHC, min..max timestamp)'
      }
      excel_spawn_observer = $excelRule
      excel_snapshot = $snaps
      excel_history = $excelHistory
      territory_contract = @{
        contract_id = 'DSHD-WRITE-TERRITORY-CONTRACT-V1'
        contract_status = 'ACTIVE'
        contract_path = 'artifacts/dshd_write_territory_contract_v1.json'
        interception_enabled = $false
        monitored_path_count = $territoryState.entry_count
        conflict_count = $territoryState.conflict_count
        conflicts = $territoryState.conflicts
      }
      territory_scan = @{
        entries = $territoryState.entries
        conflict_count = $territoryState.conflict_count
        scan_mode = $territoryState.scan_mode
      }
      dual_hash = $dualHash
      quick_scan = $quickScan
      long_table_audit = $longTableAudit
      exchange_binding_audit = $attribAudit
      p49_artifact_audit = $p49Audit
      skill_dir_audit = $skillAudit
      exchange_field_check = 'ON'
      p49_artifact_audit_on = $true
      p49_read_only = $true
      skill_dir_hash_monitor_on = $true
      skill_dir_read_only = $true
      tweak_token = $tweakTokenName
      tweak_task = $tweakTaskName
      row_count_convention = $quickScan.data_rows_convention
      gate_state = $trackState
      warnings = $warnList
      warning_count = $warnList.Count
      red_lines = $redLines
      circuit_breaker_ready = $false
      circuit_breaker_executed = $false
      backtest_started = $false
      intervention = 'NONE'
      deliverables = @(
        'artifacts/dshd_write_territory_contract_v1.json',
        'artifacts/dshd_cluster_status_latest.json',
        'artifacts/dshd_cluster_brief.md',
        'artifacts/dshd_p81_a01_audit_snapshot.json',
        'artifacts/dshd_p81_a01_dualhash_verify.json',
        'artifacts/dshd_p81_a01_quick_scan.json',
        'artifacts/dshd_p81_warning_board.json',
        'artifacts/dshd_p81_ext_longtable_exchange_audit.json',
        'artifacts/dshd_p81_ext_p49_artifact_audit.json',
        'artifacts/dshd_p81_tweak_skill_audit.json'
      )
    }
    Write-Utf8File $outCluster (($cluster | ConvertTo-Json -Depth 14))

    # ---------- write dual hash ----------
    $dhOut = @{
      verification_type = 'DUAL_HASH_INDEPENDENT'
      task = $taskName
      a01_tag = $a01Tag
      agent = $agentName
      token = $tokenName
      timestamp = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')
      poll_count = $pollNo
      csv_path = 'output_sample/wdf_sample_metals_raw.csv'
      csv_first_seen = $(if ($dualHash.exists) { 'PRESENT' } else { 'ABSENT' })
      hash_a_method = 'System.Security.Cryptography.SHA256 over raw file bytes'
      hash_b_method = 'Get-FileHash -Algorithm SHA256 (independent)'
      dual_hash = $dualHash
      scan_status = $dualHash.scan_status
      all_match = $(($dualHash.a_eq_b -and $dualHash.matches_ref_a03))
      warning_raised = $dualHash.warning_raised
      mismatch_code = $dualHash.mismatch_code
      action_taken = 'NONE'
      audit_only = $true
    }
    Write-Utf8File $outDualHash (($dhOut | ConvertTo-Json -Depth 12))

    # ---------- write quick scan ----------
    $qsOut = @{
      verification_type = 'QUICK_SCAN_NON_AUTHORITATIVE'
      task = $taskName
      a01_tag = $a01Tag
      agent = $agentName
      token = $tokenName
      timestamp = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')
      poll_count = $pollNo
      csv_path = 'output_sample/wdf_sample_metals_raw.csv'
      quick_scan = $quickScan
      scan_status = $quickScan.scan_status
      p68_gate_is_authority = $true
      dshd_bypasses_p68 = $false
      circuit_breaker_raised = $false
      action_taken = 'NONE'
      audit_only = $true
    }
    Write-Utf8File $outQuickScan (($qsOut | ConvertTo-Json -Depth 12))

    # ---------- EXT: write long-table + exchange audit ----------
    $ltOut = @{
      verification_type = 'LONG_TABLE_INTEGRITY_AND_EXCHANGE_BINDING'
      task = $extTaskName
      a01_tag = $a01Tag
      agent = $agentName
      token = $extTokenName
      token_state = $tokenState
      branch = $branch
      timestamp = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')
      poll_count = $pollNo
      csv_path = 'output_sample/wdf_sample_metals_raw.csv'
      csv_sha256 = $dualHash.hash_a_byte_read
      csv_bytes = $quickScan.size_bytes
      csv_data_rows = $quickScan.data_rows
      exchange_field_check = 'ON'
      exchange_suffixes_known = $exchangeSuffixes
      exchange_registry_product_count = $productExchange.Count
      symbol_whitelist = $csvSymbolWhitelist
      symbol_watchlist = $csvSymbolWatchlist
      indicator_expected = $csvIndicatorExpected
      long_table_audit = $longTableAudit
      attribution_audit = $attribAudit
      audit_only = $true
      intervention = 'NONE'
      action_taken = 'RECORD_ONLY'
    }
    Write-Utf8File $outLongTable (($ltOut | ConvertTo-Json -Depth 14))
    $p49Out = @{
      verification_type = 'P49_BACKTEST_ARTIFACT_READ_ONLY_AUDIT'
      task = $extTaskName
      a01_tag = $a01Tag
      agent = $agentName
      token = $extTokenName
      token_state = $tokenState
      branch = $branch
      timestamp = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')
      poll_count = $pollNo
      p49_artifact_audit = $p49Audit
      audit_only = $true
      read_only = $true
      dshd_wrote_p49_artifact = $false
      dshd_modified_p49_artifact = $false
      dshd_ran_backtest = $false
      intervention = 'NONE'
      action_taken = 'RECORD_ONLY'
    }
    Write-Utf8File $outP49 (($p49Out | ConvertTo-Json -Depth 14))
    $skillOut = @{
      verification_type = 'FACTOR_EXTRACT_V1_SKILL_DIR_HASH_AUDIT'
      task = $tweakTaskName
      a01_tag = $a01Tag
      agent = $agentName
      token = $tweakTokenName
      token_state = $tokenState
      branch = $branch
      timestamp = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')
      poll_count = $pollNo
      skill_dir_audit = $skillAudit
      audit_only = $true
      read_only = $true
      dshd_wrote_skill_artifact = $false
      dshd_modified_skill_artifact = $false
      dshd_unlocked_skill_version = $false
      intervention = 'NONE'
      action_taken = 'RECORD_ONLY'
    }
    Write-Utf8File $outSkill (($skillOut | ConvertTo-Json -Depth 14))

    # ---------- warning board (accumulated) ----------
    foreach ($w in $warnList) {
      $wb = @{code = $w.code; severity = $w.severity; ts = $w.ts; detail = $w.detail; poll_count = $pollNo}
      $warnBoard += $wb
    }
    if ($warnBoard.Count -gt $boardKeepMax) { $warnBoard = @($warnBoard[($warnBoard.Count - $boardKeepMax)..($warnBoard.Count - 1)]) }
    $boardOut = @{
      board_id = 'DSHD-P81-WARNING-BOARD'
      a01_tag = $a01Tag
      agent = $agentName
      token = $tokenName
      updated_at = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')
      poll_count = $pollNo
      rule_ids = @('OBS-SPAWN-EXCEL-001','OBS-SPAWN-EXCEL-001-TRANSIENT','A01_HASH_MISMATCH_WARNING','CONCURRENT_WRITE_CONFLICT','A01_CSV_BLANK_RUN','EXCH-001-MISMATCH','EXCH-001-UNKNOWN-EXCHANGE','EXCH-001-ATTRIBUTED-MISMATCH','EXCH-001-ATTRIBUTED-MISMATCH-CLEARED','CSVINT-001-DUP-KEY','CSVINT-001-STRUCTURE','CSVINT-002-SYMBOL-NOT-WHITELISTED','CSVINT-003-INDICATOR-MISSING','CSVINT-003-INDICATOR-UNEXPECTED','P49-001-ARTIFACT-MISSING','P49-001-ARTIFACT-REMOVED','P49-001-HASH-CHANGED','P49-001-FILE-BENEATH-MIN-SIZE','P49-001-EXCHANGE-COL-MISMATCH','P49-001-ARTIFACT-UNEXPECTED','SKILL-001-DIR-ABSENT','SKILL-001-VERSION-CHANGED','SKILL-001-MANIFEST-CHANGED','SKILL-001-V1-FROZEN-VIOLATION','SKILL-001-FILE-MODIFIED','SKILL-001-FILE-ADDED','SKILL-001-FILE-REMOVED','SKILL-001-FILE-UNDECLARED','SKILL-001-FILE-DECLARED-MISSING','SKILL-001-DATA-SHA-MISMATCH')
      severity_levels = @('YELLOW')
      escalation = 'RECORD_ONLY_NO_INTERVENTION'
      auto_kill = $false
      total_labels = $warnBoard.Count
      labels_this_poll = $warnList.Count
      calm_message = $zh['calm']
      labels = $warnBoard
    }
    Write-Utf8File $outBoard (($boardOut | ConvertTo-Json -Depth 12))

    # ---------- observation brief (every poll) ----------
    $brief = Write-ClusterBrief $pollTs $agents $excelRule $territoryState $dualHash $quickScan $warnList $p0Checks $p0Pass $p0Total $redLines $longTableAudit $attribAudit $p49Audit $skillAudit
    Write-Utf8File $outBrief $brief

    # ---------- poll snapshot (P81 dedicated path) ----------
    $snap = @{
      snapshot_id = 'DSHD-P81-A01-AUDIT-SNAPSHOT'
      task = $taskName
      agent = $agentName
      phase = 'P81'
      a01_tag = $a01Tag
      token = $tokenName
      token_state = $tokenState
      branch = $branch
      poll_count = $pollNo
      poll_interval_sec = $pollIntervalSec
      timestamp = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')
      watch_started_at = $startTs.ToString('yyyy-MM-ddTHH:mm:sszzz')
      audit_context_loaded = $true
      independent_verify_on = $true
      p0_all_pass = $p0AllPass
      p0_checks = $p0Checks
      p0_checks_passed = $p0Pass
      p0_checks_total = $p0Total
      peer_watchers = $watchStatus
      process_protection = @{
        pid_3472_alive = $mainAlive
        pid_14644_alive = $excelAlive
        pid_3472_never_kill = $true
        pid_14644_never_kill = $true
      }
      bom_status = $bomInfo
      gate_state = $trackState
      dshc_task_window = @{
        start = $(if ($null -ne $dshcWindowStart) { $dshcWindowStart.ToString('s') } else { '' })
        end = $(if ($null -ne $dshcWindowEnd) { $dshcWindowEnd.ToString('s') } else { '' })
        event_hits = $dshcHits
      }
      territory_contract = @{
        contract_id = 'DSHD-WRITE-TERRITORY-CONTRACT-V1'
        status = 'ACTIVE'
        interception_enabled = $false
        conflict_count = $territoryState.conflict_count
      }
      excel_spawn_observer = $excelRule
      excel_snapshot = $snaps
      dual_hash = $dualHash
      quick_scan = $quickScan
      long_table_audit = $longTableAudit
      exchange_binding_audit = $attribAudit
      p49_artifact_audit = $p49Audit
      skill_dir_audit = $skillAudit
      exchange_field_check = 'ON'
      p49_artifact_audit_on = $true
      p49_read_only = $true
      skill_dir_hash_monitor_on = $true
      skill_dir_read_only = $true
      tweak_token = $tweakTokenName
      tweak_task = $tweakTaskName
      row_count_convention = $quickScan.data_rows_convention
      csv_evidence = @{
        path = 'output_sample/wdf_sample_metals_raw.csv'
        exists = $dualHash.exists
        size_bytes = $quickScan.size_bytes
        last_write = $(if ($dualHash.exists) { (Get-Item $csvPath).LastWriteTime.ToString('s') } else { '' })
      }
      a01_status = 'MONITOR_ENHANCED'
      a01_warnings = $warnList
      warning_count = $warnList.Count
      red_lines = $redLines
      circuit_breaker_ready = $false
      circuit_breaker_executed = $false
      backtest_started = $false
      intervention = 'NONE'
      deliverables = @(
        'artifacts/dshd_write_territory_contract_v1.json',
        'artifacts/dshd_cluster_status_latest.json',
        'artifacts/dshd_cluster_brief.md',
        'artifacts/dshd_p81_a01_audit_snapshot.json',
        'artifacts/dshd_p81_a01_dualhash_verify.json',
        'artifacts/dshd_p81_a01_quick_scan.json',
        'artifacts/dshd_p81_warning_board.json',
        'artifacts/dshd_p81_ext_longtable_exchange_audit.json',
        'artifacts/dshd_p81_ext_p49_artifact_audit.json',
        'artifacts/dshd_p81_tweak_skill_audit.json'
      )
    }
    Write-Utf8File $outSnapshot (($snap | ConvertTo-Json -Depth 14))

    # ---------- append audit event ----------
    $evt = @{
      timestamp = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')
      event = 'DSHD-P81-CLUSTER-WATCH-POLL-' + ($pollNo.ToString('D5'))
      event_type = 'audit_poll'
      agent = $agentName
      task = $taskName
      a01_tag = $a01Tag
      token = $tokenName
      token_state = $tokenState
      branch = $branch
      poll_count = $pollNo
      mode = 'AUDIT_READ_ONLY'
      gate = $trackState.gate
      release_permit = $trackState.release_permit
      wind_api_calls = $trackState.wind_api_calls
      wind_api_calls_found = $trackState.wind_api_calls_found
      wind_api_garbage_hits_tail500 = $trackState.wind_api_garbage_hits_tail500
      p68_lock = $trackState.p68_lock
      p68_commit = $trackState.p68_commit
      p0_all_pass = $p0AllPass
      p0_checks_passed = $p0Pass
      p0_checks_total = $p0Total
      pid_3472 = $mainAlive
      pid_14644 = $excelAlive
      pwsh_13 = $watchStatus['pwsh-13'].alive
      pwsh_30 = $watchStatus['pwsh-30'].alive
      pwsh_37 = $watchStatus['pwsh-37'].alive
      script_bom_intact = $bomInfo.has_bom
      territory_contract_active = $true
      territory_conflict_count = $territoryState.conflict_count
      excel_observer_rule = 'OBS-SPAWN-EXCEL-001'
      excel_total = $excelRule.total_excel
      excel_non_protected_in_window = $excelRule.non_protected_in_window
      excel_spawn_warning = $excelRule.triggered
      csv_sha256 = $dualHash.hash_a_byte_read
      csv_bytes = $quickScan.size_bytes
      csv_data_rows = $quickScan.data_rows
      csv_dual_hash_status = $dualHash.scan_status
      csv_quick_scan_status = $quickScan.scan_status
      ext_token = $extTokenName
      ext_task = $extTaskName
      exchange_field_check = 'ON'
      long_table_format = $longTableAudit.format
      long_table_audit_status = $longTableAudit.audit_status
      long_table_data_rows = $longTableAudit.data_rows
      long_table_duplicate_keys = $longTableAudit.duplicate_key_count
      long_table_malformed_rows = $longTableAudit.malformed_row_count
      long_table_blank_key_fields = $longTableAudit.blank_key_field_count
      long_table_bad_dates = $longTableAudit.bad_date_count
      long_table_non_numeric_values = $longTableAudit.non_numeric_value_count
      long_table_symbols = $longTableAudit.distinct_symbol_count
      long_table_indicators = $longTableAudit.distinct_indicator_count
      exchange_bound_ok = $longTableAudit.exchange_ok_count
      exchange_mismatch_count = $longTableAudit.exchange_mismatch_count
      exchange_unknown_count = $longTableAudit.exchange_unknown_count
      exchange_attrib_files_scanned = $attribAudit.files_scanned
      exchange_attrib_mismatch_count = $attribAudit.mismatch_count
      symbol_whitelist_violations = $longTableAudit.symbols_not_whitelisted.Count
      indicator_missing_count = $longTableAudit.indicators_missing.Count
      p49_artifact_audit_on = $true
      p49_read_only = $true
      p49_dir_exists = $p49Audit.exists
      p49_file_count = $p49Audit.file_count
      p49_total_bytes = $p49Audit.total_bytes
      p49_manifest_status = $p49Audit.manifest_status
      p49_manifest_lc_gfe = $p49Audit.manifest_lc_gfe
      p49_audit_status = $p49Audit.audit_status
      p49_missing_files = $p49Audit.missing_files.Count
      p49_removed_files = $p49Audit.removed_files.Count
      p49_hash_changed_files = $p49Audit.hash_changed_files.Count
      p49_unexpected_files = $p49Audit.unexpected_files.Count
      p49_expected_source = $p49Audit.expected_source
      p49_manifest_last_write = $p49Audit.manifest_last_write
      p49_exchange_column_mismatches = $p49Audit.exchange_column_mismatch_count
      p49_manifest_sealed = $p49Audit.manifest_sealed
      p49_manifest_sealed_at = $p49Audit.manifest_sealed_at
      p49_post_seal_mutation = $p49Audit.post_seal_mutation
      p49_post_seal_mutation_kinds = $p49Audit.post_seal_mutation_kinds
      p49_post_seal_archive_modify_alert = $p49Audit.post_seal_archive_modify_alert
      p49_post_seal_alert_polls = $p49PostSealMutationPolls
      p49_cold_start = $p49Audit.cold_start
      tweak_token = $tweakTokenName
      tweak_task = $tweakTaskName
      row_count_convention = $quickScan.data_rows_convention
      csv_data_rows_legacy_header_inclusive = $quickScan.data_rows_legacy_header_inclusive
      csv_header_line_count = $quickScan.header_line_count
      exchange_attrib_lc_shf_verdict = $attribAudit.lc_shf_verdict
      exchange_attrib_lc_gfe_verdict = $attribAudit.lc_gfe_verdict
      exchange_attrib_lc_binding_repaired = $attribAudit.lc_binding_repaired
      exchange_attrib_auto_clear_enabled = $attribAudit.auto_clear_enabled
      skill_dir_hash_monitor_on = $true
      skill_dir_read_only = $true
      skill_dir_exists = $skillAudit.exists
      skill_dir_file_count = $skillAudit.file_count
      skill_dir_total_bytes = $skillAudit.total_bytes
      skill_dir_skill_id = $skillAudit.skill_id
      skill_dir_version = $skillAudit.version
      skill_dir_previous_version = $skillAudit.previous_version
      skill_dir_version_locked = $skillAudit.version_locked
      skill_dir_status = $skillAudit.status
      skill_dir_manifest_sha256 = $skillAudit.manifest_sha256
      skill_dir_manifest_hash_changed = $skillAudit.manifest_hash_changed
      skill_dir_version_changed = $skillAudit.skill_version_changed
      skill_dir_declared_count = $skillAudit.declared_count
      skill_dir_undeclared_files = $skillAudit.undeclared_files.Count
      skill_dir_declared_missing_files = $skillAudit.declared_missing_files.Count
      skill_dir_files_added = $skillAudit.added_files.Count
      skill_dir_files_modified = $skillAudit.modified_files.Count
      skill_dir_files_removed = $skillAudit.removed_files.Count
      skill_dir_v1_frozen_violation = $skillAudit.v1_frozen_violation
      skill_dir_data_sha_match = $skillAudit.original_csv_sha256_match
      skill_dir_audit_status = $skillAudit.audit_status
      hash_mismatch = $dualHash.warning_raised
      warnings = $warnList
      warning_count = $warnList.Count
      circuit_breaker_ready = $false
      circuit_breaker_executed = $false
      audit_only = $true
      intervention = 'NONE'
      no_kill_executed = $true
      no_auto_retry = $true
      backtest_started = $false
      do_not_disturb_post_mortem_t1 = $true
      loop_elapsed_ms = 0
    }
    Add-AuditEvent $auditLog $evt
    # ---------- EXT: one-shot P49 backtest completion audit event ----------
    if (($p49Audit.exists -eq $true) -and ($p49CompleteReported -eq $false) -and ($p49Audit.manifest_status -match 'BACKTEST_COMPLETE')) {
      $p49CompleteReported = $true
      $p49Evt = @{
        timestamp = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')
        event = 'DSHD-P81-EXT-P49-BACKTEST-COMPLETE-OBSERVED-00001'
        event_type = 'p49_backtest_complete_observed'
        agent = $agentName
        task = $extTaskName
        a01_tag = $a01Tag
        token = $extTokenName
        token_state = $tokenState
        branch = $branch
        poll_count = $pollNo
        mode = 'AUDIT_READ_ONLY'
        audit_only = $true
        intervention = 'NONE'
        no_kill_executed = $true
        p49_archive_id = $p49Audit.manifest_archive_id
        p49_manifest_agent = $p49Audit.manifest_agent
        p49_manifest_token = $p49Audit.manifest_token
        p49_manifest_status = $p49Audit.manifest_status
        p49_manifest_gate = $p49Audit.manifest_gate
        p49_manifest_release_permit = $p49Audit.manifest_release_permit
        p49_manifest_lc_gfe = $p49Audit.manifest_lc_gfe
        p49_manifest_symbols_run = $p49Audit.manifest_symbols_run
        p49_manifest_wind_api_calls = $p49Audit.manifest_wind_api_calls
        p49_manifest_real_wind_call = $p49Audit.manifest_real_wind_call
        p49_manifest_offline_only = $p49Audit.manifest_offline_only
        p49_manifest_csv_not_modified = $p49Audit.manifest_csv_not_modified
        p49_dir = 'artifacts/p49_backtest'
        p49_file_count = $p49Audit.file_count
        p49_total_bytes = $p49Audit.total_bytes
        p49_files = $p49Audit.files
        p49_missing_files = $p49Audit.missing_files
        p49_unexpected_files = $p49Audit.unexpected_files
        p49_hash_changed_files = $p49Audit.hash_changed_files
        p49_expected_source = $p49Audit.expected_source
        p49_manifest_declared_files = $p49Audit.manifest_declared_files
        p49_manifest_last_write = $p49Audit.manifest_last_write
        p49_sha256_snapshot = $p49Audit.state_snapshot
        p49_audit_status = $p49Audit.audit_status
        p49_read_only_audit = $true
        p49_wrote_anything = $false
        dshd_ran_backtest = $false
        dshd_modified_backtest_artifact = $false
        dshd_bypasses_dsha_p68 = $false
        dshd_fetches_for_dshc = $false
        p0_all_pass = $p0AllPass
        p0_checks_passed = $p0Pass
        p0_checks_total = $p0Total
        gate = $trackState.gate
        release_permit = $trackState.release_permit
        wind_api_calls = $trackState.wind_api_calls
        circuit_breaker_ready = $false
        circuit_breaker_executed = $false
      }
      Add-AuditEvent $auditLog $p49Evt
      Write-Host ('[EXT] P49 BACKTEST COMPLETE OBSERVED | archive=' + $p49Audit.manifest_archive_id + ' files=' + $p49Audit.file_count + ' bytes=' + $p49Audit.total_bytes + ' snapshot=' + $p49Audit.state_snapshot.Count + ' status=' + $p49Audit.audit_status + ' audit_only=YES intervention=NONE')
    }
    # ---------- TWEAK: one-shot first observation of a post-seal mutation ----------
    if (($p49Audit.post_seal_archive_modify_alert -eq $true) -and ($p49PostSealFirstReported -eq $false)) {
      $p49PostSealFirstReported = $true
      $psEvt = @{
        timestamp = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')
        event = 'DSHD-P81-TWEAK-P49-POSTSEAL-MUTATION-FIRSTOBS-00001'
        event_type = 'p49_post_seal_mutation_first_observed'
        agent = $agentName
        task = $tweakTaskName
        a01_tag = $a01Tag
        token = $tweakTokenName
        token_state = $tokenState
        branch = $branch
        poll_count = $pollNo
        mode = 'AUDIT_READ_ONLY'
        audit_only = $true
        intervention = 'NONE'
        no_kill_executed = $true
        p49_archive_id = $p49Audit.manifest_archive_id
        p49_manifest_status = $p49Audit.manifest_status
        p49_manifest_sealed = $p49Audit.manifest_sealed
        p49_manifest_sealed_at = $p49Audit.manifest_sealed_at
        p49_manifest_last_write = $p49Audit.manifest_last_write
        p49_cold_start = $p49Audit.cold_start
        p49_dir = 'artifacts/p49_backtest'
        p49_file_count = $p49Audit.file_count
        p49_total_bytes = $p49Audit.total_bytes
        p49_expected_source = $p49Audit.expected_source
        p49_manifest_declared_files = $p49Audit.manifest_declared_files
        post_seal_mutation_kinds = $p49Audit.post_seal_mutation_kinds
        post_seal_mutation_kinds_count = $p49Audit.post_seal_mutation_kinds_count
        p49_unexpected_files = $p49Audit.unexpected_files
        p49_added_files = $p49Audit.added_files
        p49_hash_changed_files = $p49Audit.hash_changed_files
        p49_removed_files = $p49Audit.removed_files
        p49_missing_files = $p49Audit.missing_files
        p49_files = $p49Audit.files
        p49_sha256_snapshot = $p49Audit.state_snapshot
        p49_audit_status = $p49Audit.audit_status
        continuous_alert_rule = 'P49-001-ARTIFACT-UNEXPECTED is re-emitted every poll while post_seal_archive_modify_alert is true'
        p49_read_only_audit = $true
        p49_wrote_anything = $false
        dshd_ran_backtest = $false
        dshd_modified_backtest_artifact = $false
        dshd_bypasses_dsha_p68 = $false
        dshd_fetches_for_dshc = $false
        p0_all_pass = $p0AllPass
        gate = $trackState.gate
        release_permit = $trackState.release_permit
        wind_api_calls = $trackState.wind_api_calls
        circuit_breaker_ready = $false
        circuit_breaker_executed = $false
      }
      Add-AuditEvent $auditLog $psEvt
      Write-Host ('[TWEAK] P49 POST-SEAL MUTATION FIRST OBSERVED | kinds=' + ($p49Audit.post_seal_mutation_kinds -join ',') + ' files=' + $p49Audit.file_count + ' undeclared=' + $p49Audit.unexpected_files.Count + ' modified=' + $p49Audit.hash_changed_files.Count + ' audit_only=YES intervention=NONE')
    }
    # ---------- TWEAK: one-shot first observation of the skill dir baseline ----------
    if (($skillAudit.exists -eq $true) -and ($skillFirstReported -eq $false)) {
      $skillFirstReported = $true
      $skEvt = @{
        timestamp = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')
        event = 'DSHD-P81-TWEAK-SKILL-DIR-FIRSTOBS-00001'
        event_type = 'skill_dir_hash_baseline_first_observed'
        agent = $agentName
        task = $tweakTaskName
        a01_tag = $a01Tag
        token = $tweakTokenName
        token_state = $tokenState
        branch = $branch
        poll_count = $pollNo
        mode = 'AUDIT_READ_ONLY'
        audit_only = $true
        intervention = 'NONE'
        no_kill_executed = $true
        skill_dir = 'artifacts/skill_lib/factor_v1'
        skill_dir_file_count = $skillAudit.file_count
        skill_dir_total_bytes = $skillAudit.total_bytes
        skill_dir_skill_id = $skillAudit.skill_id
        skill_dir_version = $skillAudit.version
        skill_dir_version_locked = $skillAudit.version_locked
        skill_dir_status = $skillAudit.status
        skill_dir_locked_at = $skillAudit.locked_at
        skill_dir_locked_by = $skillAudit.locked_by
        skill_dir_skill_token = $skillAudit.skill_token
        skill_dir_baseline = $skillAudit.skill_baseline
        skill_dir_iteration_policy = $skillAudit.iteration_policy
        skill_dir_next_version = $skillAudit.next_version
        skill_dir_manifest_sha256 = $skillAudit.manifest_sha256
        skill_dir_manifest_last_write = $skillAudit.manifest_last_write
        skill_dir_manifest_readable = $skillAudit.manifest_readable
        skill_dir_declared_files = $skillAudit.declared_files
        skill_dir_declared_count = $skillAudit.declared_count
        skill_dir_undeclared_files = $skillAudit.undeclared_files
        skill_dir_declared_missing_files = $skillAudit.declared_missing_files
        skill_dir_constraint_wind_api_calls = $skillAudit.constraint_wind_api_calls
        skill_dir_constraint_offline_only = $skillAudit.constraint_offline_only
        skill_dir_constraint_f01_script_locked = $skillAudit.constraint_f01_script_locked
        skill_dir_constraint_f01_script_version = $skillAudit.constraint_f01_script_version
        skill_dir_constraint_f01_script_params_only = $skillAudit.constraint_f01_script_params_only
        skill_dir_data_integrity_aligned_sha256 = $skillAudit.data_integrity_aligned_sha256
        skill_dir_data_integrity_aligned_rows = $skillAudit.data_integrity_aligned_rows
        skill_dir_data_integrity_original_sha256 = $skillAudit.data_integrity_original_sha256
        skill_dir_data_integrity_unique_dates = $skillAudit.data_integrity_unique_dates
        skill_dir_original_csv_sha256_actual = $skillAudit.original_csv_sha256_actual
        skill_dir_original_csv_sha256_match = $skillAudit.original_csv_sha256_match
        skill_dir_files = $skillAudit.files
        skill_dir_sha256_snapshot = $skillAudit.state_snapshot
        skill_dir_audit_status = $skillAudit.audit_status
        cold_start = $skillAudit.cold_start
        skill_dir_read_only_audit = $true
        dshd_wrote_skill_artifact = $false
        dshd_modified_skill_artifact = $false
        dshd_unlocked_skill_version = $false
        p0_all_pass = $p0AllPass
        gate = $trackState.gate
        release_permit = $trackState.release_permit
        wind_api_calls = $trackState.wind_api_calls
        circuit_breaker_ready = $false
        circuit_breaker_executed = $false
      }
      Add-AuditEvent $auditLog $skEvt
      Write-Host ('[TWEAK] SKILL DIR BASELINE OBSERVED | id=' + $skillAudit.skill_id + ' ver=' + $skillAudit.version + ' locked=' + $skillAudit.version_locked + ' files=' + $skillAudit.file_count + ' bytes=' + $skillAudit.total_bytes + ' declared=' + $skillAudit.declared_count + ' undeclared=' + $skillAudit.undeclared_files.Count + ' sha_match=' + $skillAudit.original_csv_sha256_match + ' audit_only=YES intervention=NONE')
    }
    # ---------- TWEAK: one-shot exchange binding cleared event ----------
    if (($exchClearedReported -eq $true) -and ($exchPrevMismatchCount -gt 0) -and ($attribAudit.mismatch_count -eq 0)) {
      $exchClearedReported = $false
      $ceEvt = @{
        timestamp = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz')
        event = 'DSHD-P81-TWEAK-EXCH-BINDING-CLEARED-00001'
        event_type = 'exchange_binding_cleared'
        agent = $agentName
        task = $tweakTaskName
        a01_tag = $a01Tag
        token = $tweakTokenName
        token_state = $tokenState
        branch = $branch
        poll_count = $pollNo
        mode = 'AUDIT_READ_ONLY'
        audit_only = $true
        intervention = 'NONE'
        no_kill_executed = $true
        prev_mismatch_count = $exchPrevMismatchCount
        current_mismatch_count = $attribAudit.mismatch_count
        labels_auto_cleared = @('EXCH-001-MISMATCH','EXCH-001-ATTRIBUTED-MISMATCH')
        files_scanned = $attribAudit.files_scanned
        distinct_symbols = $attribAudit.distinct_symbols
        no_data_symbols = $attribAudit.no_data_symbols
        lc_shf_verdict = $attribAudit.lc_shf_verdict
        lc_shf_expected_exchange = $attribAudit.lc_shf_expected_exchange
        lc_gfe_verdict = $attribAudit.lc_gfe_verdict
        lc_gfe_expected_exchange = $attribAudit.lc_gfe_expected_exchange
        lc_binding_repaired = $attribAudit.lc_binding_repaired
        lc_repaired_via = $attribAudit.lc_repaired_via
        csv_exchange_mismatch_count = $longTableAudit.exchange_mismatch_count
        csv_exchange_unknown_count = $longTableAudit.exchange_unknown_count
        attribution_audit_status = $attribAudit.audit_status
        gate = $trackState.gate
        release_permit = $trackState.release_permit
        wind_api_calls = $trackState.wind_api_calls
      }
      Add-AuditEvent $auditLog $ceEvt
      Write-Host ('[TWEAK] EXCH BINDING CLEARED | mismatch=' + $exchPrevMismatchCount + ' -> 0 | LC.SHF=' + $attribAudit.lc_shf_verdict + ' LC.GFE=' + $attribAudit.lc_gfe_verdict + ' repaired=' + $attribAudit.lc_binding_repaired + ' labels_auto_cleared=YES')
    }

    $elapsedMs = [math]::Round((Get-Date).Subtract($pollStart).TotalMilliseconds, 1)
    Write-Host ("[{0}] POLL {1:D3} OK | p0={2}/{3} | wind={4} | gate={5} | permit={6} | excel=total{7}/np{8}/npwin{9} warn={10} | territory_conflicts={11} | csv={12}B rows={13} {14} | dual={15} | warns={16} | {17}ms" -f (Get-Date).ToString('HH:mm:ss'), $pollNo, $p0Pass, $p0Total, $trackState.wind_api_calls, $trackState.gate, $trackState.release_permit, $excelRule.total_excel, $excelRule.non_protected_excel, $excelRule.non_protected_in_task_window, $excelRule.triggered, $territoryState.conflict_count, $quickScan.size_bytes, $quickScan.data_rows, $quickScan.scan_status, $dualHash.scan_status, $warnList.Count, $elapsedMs)
    Write-Host ("[{0}] POLL {1:D3} TWEAK | rows_conv={2} legacy_hdr_inc={3} hdr_line={4} | sealed={5} postseal={6} polls={7} kinds={8} | skill_ver={9} locked={10} files={11} undecl={12} mod={13} rem={14} sha_match={15} {16} | lc_shf={17} lc_gfe={18} cleared={19}" -f (Get-Date).ToString('HH:mm:ss'), $pollNo, $quickScan.data_rows_convention, $quickScan.data_rows_legacy_header_inclusive, $quickScan.header_line_count, $p49Audit.manifest_sealed, $p49Audit.post_seal_archive_modify_alert, $p49PostSealMutationPolls, ($p49Audit.post_seal_mutation_kinds -join ','), $skillAudit.version, $skillAudit.version_locked, $skillAudit.file_count, $skillAudit.undeclared_files.Count, $skillAudit.modified_files.Count, $skillAudit.removed_files.Count, $skillAudit.original_csv_sha256_match, $skillAudit.audit_status, $attribAudit.lc_shf_verdict, $attribAudit.lc_gfe_verdict, $exchClearedReported)
    Write-Host ("[{0}] POLL {1:D3} EXT | longtable={2} rows={3} dup={4} malformed={5} badkey={6} baddate={7} nonnum={8} | syms={9} ind={10} | exch_ok={11} exch_mismatch={12} exch_unknown={13} attr_exch={14} | whitelist_vio={15} ind_miss={16} | p49={17} files={18} miss={19} chg={20} {21}" -f (Get-Date).ToString('HH:mm:ss'), $pollNo, $longTableAudit.audit_status, $longTableAudit.data_rows, $longTableAudit.duplicate_key_count, $longTableAudit.malformed_row_count, $longTableAudit.blank_key_field_count, $longTableAudit.bad_date_count, $longTableAudit.non_numeric_value_count, $longTableAudit.distinct_symbol_count, $longTableAudit.distinct_indicator_count, $longTableAudit.exchange_ok_count, $longTableAudit.exchange_mismatch_count, $longTableAudit.exchange_unknown_count, $attribAudit.mismatch_count, $longTableAudit.symbols_not_whitelisted.Count, $longTableAudit.indicators_missing.Count, $p49Audit.exists, $p49Audit.file_count, $p49Audit.missing_files.Count, $p49Audit.hash_changed_files.Count, $p49Audit.audit_status)
  }
  catch {
    $pollErr = $true
    $errText = $_.Exception.Message
    if ($errText.Length -gt 400) { $errText = $errText.Substring(0, 400) }
    Write-Host ("[{0}] POLL {1:D3} ERROR: {2}" -f (Get-Date).ToString('HH:mm:ss'), $pollNo, $errText)
    try {
      $errEvt = @{
        timestamp = (Get-Date).ToString('yyyy-MM-ddTHH:mm:sszzz')
        event = 'DSHD-P81-CLUSTER-WATCH-POLL-ERROR-' + ($pollNo.ToString('D5'))
        event_type = 'audit_poll_error'
        agent = $agentName
        task = $taskName
        a01_tag = $a01Tag
        token = $tokenName
        token_state = $tokenState
        branch = $branch
        poll_count = $pollNo
        mode = 'AUDIT_READ_ONLY'
        severity = 'ERROR'
        error = $errText
        audit_only = $true
        intervention = 'NONE'
        no_kill_executed = $true
        backtest_started = $false
      }
      Add-AuditEvent $auditLog $errEvt
    } catch { }
  }

  # sleep in fast-sampling steps so Excel spawn transients are observable.
  # Read-only: Get-ExcelSnapshot only reads process metadata, never touches a process.
  $sleepRemain = $pollIntervalSec
  while ($sleepRemain -gt 0) {
    $step = $excelFastIntervalSec
    if ($step -gt $sleepRemain) { $step = $sleepRemain }
    Start-Sleep -Seconds $step
    try {
      $fsSnaps = Get-ExcelSnapshot $dshcWindowStart
      $fsRule = Test-ExcelSpawnRule $fsSnaps
      $fsPids = @()
      foreach ($fsp in $fsSnaps) { if ($null -ne $fsp -and (-not $fsp.protected)) { $fsPids += [int]$fsp.pid } }
      $fastBuffer += @{
        ts = (Get-Date).ToString('yyyy-MM-ddTHH:mm:sszzz')
        total_excel = $fsRule.total_excel
        non_protected = $fsRule.non_protected_excel
        non_protected_in_task_window = $fsRule.non_protected_in_task_window
        triggered = $fsRule.triggered
        non_protected_pids = $fsPids
      }
      if ($fastBuffer.Count -gt $fastBufferKeepMax) { $fastBuffer = @($fastBuffer[($fastBuffer.Count - $fastBufferKeepMax)..($fastBuffer.Count - 1)]) }
    } catch { }
    $sleepRemain = $sleepRemain - $step
  }
}
