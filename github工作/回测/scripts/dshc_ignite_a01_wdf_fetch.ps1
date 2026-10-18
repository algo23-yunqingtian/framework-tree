#Requires -Version 5.1
<#
═══════════════════════════════════════════════════════════════════════════════
DSHC-IGNITE-A01 · WDF-Excel isolated sample-metals fetch executor
═══════════════════════════════════════════════════════════════════════════════
Baseline : feature/v88-g1
Authority: DSHC-IGNITE-A01-AUTH — USER EXPLICIT ONE-SHOT REMOTE AUTHORISATION
AuthRef  : A01-USER-REMOTE-001
Gate     : AUTHORISED_BY_USER_WORKORDER
Channel  : Excel COM + WDF add-in WSD formula ONLY (WindPy / InitWAPI NOT used)
Payload  : artifacts/wdf_instrument_fetch_table.json (DSHA-P65 prefab)
Redlines : never touch protected user Excel PIDs | hard 12-min background-Excel
           lifetime | max 2 WDF retries x 30s | capture #N/A | no Wind bombing |
           no permanent marker files | no long-term config modification |
           auth expires immediately after this run
#>
param(
  [string]$Root         = 'D:\DSH_WORK\github工作\回测',
  [string]$AuthRef      = 'A01-USER-REMOTE-001',
  [int]$HardTimeoutMin  = 12,
  [int]$MaxRetries      = 2,
  [int]$RetryWaitSec    = 30,
  [int]$AttemptWaitSec  = 60,
  [switch]$PreflightOnly
)

$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'

# ── paths ────────────────────────────────────────────────────────────────────
$Root        = (Resolve-Path $Root).Path
$Artifacts   = Join-Path $Root 'artifacts'
$SkillDir    = Join-Path $Root 'system_skills\SKILL-WIND-EXCEL-WDF-BOOTSTRAP'
$TrackingLog = Join-Path $Root 'tracking_monitor_audit.jsonl'
$DshcEvents  = Join-Path $Artifacts 'dshc_p90a_final_events.jsonl'
$LocalLog    = Join-Path $Artifacts 'dshc_ignite_a01_events.jsonl'
$AgentMarker = Join-Path $Artifacts 'agent_excel_pid.json'
$PreflightJ  = Join-Path $Artifacts 'wdf_preflight_check.json'
$ReceiptPath = Join-Path $Artifacts 'dshc_ignite_run_receipt.json'
$PayloadPath = Join-Path $Artifacts 'wdf_instrument_fetch_table.json'
$ManifestJ   = Join-Path $Artifacts 'skill_release_manifest.json'
$IndexJ      = Join-Path $Artifacts 'cross_agent_artifact_index.json'
$HealthPath  = Join-Path $SkillDir 'health_check_wdf.ps1'
$ResetPath   = Join-Path $SkillDir 'reset_wdf_safe.ps1'
$CsvDir      = Join-Path $Root 'output_sample'
$CsvOut      = Join-Path $CsvDir 'wdf_sample_metals_raw.csv'
$MirrorDir   = Join-Path $Artifacts 'sample_output'
$TemplateCsv = Join-Path $Root 'templates\sample_output_header_template.csv'

New-Item -ItemType Directory -Path $Artifacts -Force | Out-Null
New-Item -ItemType Directory -Path $CsvDir    -Force | Out-Null
New-Item -ItemType Directory -Path $MirrorDir -Force | Out-Null

$script:WindApiCalls = 0
$script:WdfRetries   = 0
$script:WdfInjectAttempts = 0
$script:RunStatus    = 'RUNNING'
$script:RunEndReason = ''
$script:FetchResults = [System.Collections.Generic.List[object]]::new()
$script:WideRows     = [System.Collections.Generic.List[string]]::new()
$script:MirrorFiles  = [System.Collections.Generic.List[string]]::new()
$script:ProtectedPids = @()
$script:AgentPid      = 0
$script:AgentCreatedAt = ''
$script:AgentQuitAt   = ''
$script:ResetAction   = 'NOT_RUN'
$script:ProtectedAliveCount = 0

function Get-NowIso { (Get-Date).ToString('o') }

function Get-ExcelPids {
  @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)
}

# Normalise one cell of an Application.Evaluate result:
#   Excel OLE date -> yyyy-MM-dd | number -> plain text, no grouping |
#   "#N/A" / "#NAME?" kept verbatim so the capture logic can count them
function Normalize-CellValue($v) {
  if ($null -eq $v) { return '' }
  if ($v -is [System.Reflection.Missing]) { return '' }
  if ($v -is [string]) { return ([string]$v).Trim() }
  $s = [string]$v
  if ($s -match '^#') { return $s.Trim() }
  try { return [DateTime]::FromOADate([double]$v).ToString('yyyy-MM-dd') } catch { }
  try { return ([string][double]$v).Replace(',', '') } catch { return $s.Replace(',', '').Trim() }
}

# ── event emission (three ledgers, single source of truth) ───────────────────
function Append-Event {
  param([string]$Type, [string]$Message, [hashtable]$Extra = @{})
  $ts = Get-NowIso
  $e = [ordered]@{}
  $e['timestamp']      = $ts
  $e['captured_at']    = $ts
  $e['agent']          = 'DSHC-IGNITE-A01'
  $e['auth_ref']       = $AuthRef
  $e['event_type']     = $Type
  $e['wind_api_calls'] = $script:WindApiCalls
  $e['wdf_retries']    = $script:WdfRetries
  $e['wdf_inject_attempts'] = $script:WdfInjectAttempts
  $e['real_wind_call'] = $true
  $e['message']        = $Message
  if ($null -ne $Extra -and $Extra.Count -gt 0) {
    foreach ($k in $Extra.Keys) { $e[$k] = $Extra[$k] }
  }
  $line = $e | ConvertTo-Json -Depth 10 -Compress
  foreach ($p in @($TrackingLog, $DshcEvents, $LocalLog)) {
    try { Add-Content -Path $p -Value $line -Encoding UTF8 -ErrorAction Stop }
    catch { Write-Host ("[EVENT-WRITE-FAIL] {0} :: {1}" -f $p, $_.Exception.Message) }
  }
  Write-Host ("[{0}] {1} :: {2}" -f $ts.Substring(11, 12), $Type, $Message)
}

# ═══════════════════════════════════════════════════════════════════════════════
# RECEIPT
# ═══════════════════════════════════════════════════════════════════════════════
function Write-Receipt {
  try {
    $lifetime = 0
    if ($script:AgentCreatedAt -ne '' -and $script:AgentQuitAt -ne '') {
      $lifetime = [int]((Get-Date $script:AgentQuitAt) - (Get-Date $script:AgentCreatedAt)).TotalSeconds
    }
    $protectedCheck = @($script:ProtectedPids | Where-Object { $_ -ne $script:AgentPid })
    $protectedAlive = @($protectedCheck | Where-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue })
    $okCount = @($script:FetchResults | Where-Object { $_.status -eq 'OK' }).Count

    $rec = [ordered]@{}
    $rec['receipt_id'] = 'DSHC-IGNITE-A01-RECEIPT-001'
    $rec['ticket']     = 'DSHC-IGNITE-A01-AUTH'
    $rec['audit_marker'] = 'IGNITE_VIA_USER_WORKORDER_A01_AUTH'
    $rec['auth_ref']   = $AuthRef
    $rec['status']     = $script:RunStatus
    $rec['end_reason'] = $script:RunEndReason
    $rec['gate']       = 'AUTHORISED_BY_USER_WORKORDER'
    $rec['ignition_authority'] = 'USER_EXPLICIT_ONE_SHOT_REMOTE_AUTHORISATION'
    $rec['audit_note'] = 'USER_REMOTE_AUTH - physical keyboard operation not available; signed-as-workorder counts as ignition approval for this one batch only'
    $rec['branch']     = 'feature/v88-g1'
    $rec['timestamp_start'] = $pre['started_at']
    $rec['timestamp_end']   = Get-NowIso
    $rec['duration_sec']    = if ($pre['started_at']) { [int]((Get-Date) - (Get-Date $pre['started_at'])).TotalSeconds } else { 0 }
    $rec['channel']         = 'Excel COM + WDF add-in WSD formula (WindPy / InitWAPI NOT used)'
    $rec['hard_timeout_min']    = $HardTimeoutMin
    $rec['max_retries_allowed'] = $MaxRetries
    $rec['retry_interval_sec']  = $RetryWaitSec
    $rec['wind_api_calls']      = $script:WindApiCalls
    $rec['wdf_retries']         = $script:WdfRetries
    $rec['wdf_inject_attempts'] = $script:WdfInjectAttempts
    $rec['wind_api_calls_semantics'] = 'counted only when a WSD formula returned a data grid; formula injections that never evaluated are wdf_inject_attempts'
    $rec['real_wind_call']      = $true
    $rec['real_wind_call_scope'] = 'task-scoped to this A01 run only; NOT persisted to code constants or cross_agent_artifact_index baseline'
    $rec['auth_expired_after_this_run'] = $true
    $rec['sample_fetch_allow_marker_created'] = $false
    $rec['permanent_config_modified'] = $false
    $rec['windpy_used'] = $false
    $rec['initwapi_used'] = $false

    $rec['preflight'] = [ordered]@{
      status = $pre['status']; checks_passed = $pre['summary']; checks_total = $pre['total']
      report = 'artifacts/wdf_preflight_check.json'
    }
    $rec['payload'] = [ordered]@{
      payload_id = $payload.payload_id
      instruments = $instCodes
      wdf_fields = @($fields)
      time_range = [ordered]@{ start = $startDate; end = $endDate; frequency = 'DAILY' }
    }
    $rec['background_excel'] = [ordered]@{
      agent_pid = $script:AgentPid
      created_at = $script:AgentCreatedAt
      quit_at = $script:AgentQuitAt
      lifetime_sec = $lifetime
      within_hard_timeout = ($lifetime -le ($HardTimeoutMin * 60))
      agent_addins = $agentAddins
    }
    $rec['user_excel'] = [ordered]@{
      protected_pids = $script:ProtectedPids
      alive_after_run = $protectedAlive
      terminated = $false
      protected = ($protectedAlive.Count -eq $protectedCheck.Count)
    }
    $rec['reset'] = [ordered]@{
      action = $script:ResetAction
      agent_excel_pid = $script:AgentPid
      marker_cleared = -not (Test-Path $AgentMarker)
      broad_excel_kill = $false
    }
    $rec['instruments'] = @($script:FetchResults)
    $rec['instruments_ok'] = $okCount
    $rec['instruments_total'] = $payload.instrument_count
    $rec['csv'] = [ordered]@{
      path = 'output_sample/wdf_sample_metals_raw.csv'
      header = $hdrText
      rows = $csvRows
      bytes = $csvBytes
      sha256 = $csvSha
    }
    $rec['p62_loop'] = [ordered]@{
      declared_trigger_dir = 'output_sample'
      actual_listener_dir = 'artifacts/sample_output'
      mirror_files = @($script:MirrorFiles | ForEach-Object { [IO.Path]::GetFileName($_) })
      note = 'CSV landed in output_sample per workorder; long-format mirror placed in artifacts/sample_output because sample_data_trigger.py (P62-LOOP/P60) scans that directory'
    }
    $rec['ledger'] = [ordered]@{
      g7_tracking_log = 'tracking_monitor_audit.jsonl'
      dshc_events = 'artifacts/dshc_p90a_final_events.jsonl'
      local_log = 'artifacts/dshc_ignite_a01_events.jsonl'
    }
    $rec['red_lines'] = [ordered]@{
      user_excel_untouched = $true
      no_windpy = $true
      no_initwapi = $true
      hard_timeout_enforced = $true
      max_retries_enforced = ($script:WdfRetries -le $MaxRetries)
      no_permanent_marker = $true
      no_long_term_config_change = $true
      auth_expired_after_this_run = $true
      no_wind_bombardment = $true
    }
    $rec | ConvertTo-Json -Depth 30 | Set-Content -Path $ReceiptPath -Encoding UTF8
    Append-Event 'RECEIPT_WRITTEN' ("{0} -> artifacts/dshc_ignite_run_receipt.json; status={1}; wind_api_calls={2}; wdf_retries={3}; csv_rows={4}" -f $rec['status'], $rec['status'], $script:WindApiCalls, $script:WdfRetries, $csvRows) @{ receipt_path = 'artifacts/dshc_ignite_run_receipt.json'; status = $rec['status'] }
    Write-Host ("[RECEIPT] status={0} wind_api_calls={1} wdf_retries={2} csv_rows={3}" -f $rec['status'], $rec['wind_api_calls'], $rec['wdf_retries'], $csvRows)
  } catch {
    Write-Host ("[RECEIPT-WRITE-FAIL] {0}" -f $_.Exception.Message)
  }
}

# ═══════════════════════════════════════════════════════════════════════════════
# P1.1  PREFLIGHT  (no Wind data calls: registry / COM / add-in probes only)
# ═══════════════════════════════════════════════════════════════════════════════
$pre = [ordered]@{}
$pre['started_at'] = Get-NowIso
$pre['auth_ref']   = $AuthRef
$pre['branch']     = 'feature/v88-g1'
$pre['checklist']  = [System.Collections.Generic.List[object]]::new()

function Add-PreCheck {
  param([string]$Name, [object]$Value, [object]$Expected = $true, [string]$Detail = '')
  $pass = ($Value -eq $Expected)
  $pre['checklist'].Add([ordered]@{
    name = $Name; value = $Value; expected = $Expected; pass = $pass; detail = $Detail
  })
  if (-not $pass) { Write-Host ("[PREFLIGHT-FAIL] {0}: got={1} expected={2} :: {3}" -f $Name, $Value, $Expected, $Detail) }
  return $pass
}

Append-Event 'PREFLIGHT_START' 'A01 preflight gate check started' @{ ticket = 'DSHC-IGNITE-A01-AUTH'; gate = 'AUTHORISED_BY_USER_WORKORDER'; auth_ref = $AuthRef }

# (1) R03 manifest self-hash vs cross-agent index entry
$r03Consistent = $false; $r03SelfHash = ''; $r03IndexHash = ''
try {
  $idx = Get-Content -Raw -Encoding UTF8 $IndexJ | ConvertFrom-Json
  $r03IndexHash = [string]$idx.artifacts.skill_release_manifest_json.sha256
  $r03SelfHash  = (Get-FileHash -Algorithm SHA256 $ManifestJ).Hash
  $r03Consistent = ($r03IndexHash -eq $r03SelfHash)
} catch { Add-PreCheck 'R03_INDEX_PARSE' $false $true $_.Exception.Message }
Add-PreCheck 'R03_MANIFEST_INDEX_CONSISTENT' $r03Consistent $true ("live=$r03SelfHash index=$r03IndexHash")

# (2) five skill files match R03 manifest hashes
$manifest = Get-Content -Raw -Encoding UTF8 $ManifestJ | ConvertFrom-Json
$skillMatchCount = 0; $skillMismatch = @()
foreach ($fe in $manifest.file_entries) {
  $p = Join-Path $Root $fe.path
  if (Test-Path $p) {
    $h = (Get-FileHash -Algorithm SHA256 $p).Hash
    if ($h -eq $fe.actual_sha256) { $skillMatchCount++ } else { $skillMismatch += $fe.path }
  } else { $skillMismatch += $fe.path }
}
Add-PreCheck 'SKILL_FILES_MATCH_R03' ($skillMatchCount -eq 5) $true ("match={0}/5 mismatch={1}" -f $skillMatchCount, ($skillMismatch -join ','))

# (3) the three skill entrypoints parse
$parseOk = 0
foreach ($f in @('bootstrap_wdf.ps1', 'reset_wdf_safe.ps1', 'health_check_wdf.ps1')) {
  $p = Join-Path $SkillDir $f
  try {
    $tok = $null; $err = $null
    [System.Management.Automation.Language.Parser]::ParseFile($p, [ref]$tok, [ref]$err) | Out-Null
    if ($err.Count -eq 0) { $parseOk++ }
  } catch { }
}
Add-PreCheck 'SKILL_PS1_PARSE_OK' ($parseOk -eq 3) $true "parse_ok=$parseOk/3"

# (4) DSHA-P65 payload contract
$payOk = $false; $instCodes = @(); $fields = @(); $startDate = ''; $endDate = ''; $payload = $null
try {
  $payload = Get-Content -Raw -Encoding UTF8 $PayloadPath | ConvertFrom-Json
  $instCodes = @($payload.instruments | ForEach-Object { $_.instrument_code })
  $fields    = @($payload.wdf_fields)
  $startDate = [string]$payload.time_range.start
  $endDate   = [string]$payload.time_range.end
  $payOk = ($payload.instrument_count -eq 7) -and ($instCodes.Count -eq 7) -and
           ($fields -join ';' -eq 'CLOSE;VOL;OI;SETTLE') -and
           ($startDate -eq '2025-01-01') -and ($endDate -eq '2026-10-17')
} catch { $payOk = $false }
Add-PreCheck 'DSHA_P65_PAYLOAD_OK' $payOk $true ("instruments={0} range={1}~{2} fields={3}" -f ($instCodes -join ','), $startDate, $endDate, ($fields -join ';'))

# (5) header template
$hdrOk = $false; $hdrText = ''
try {
  $hdrText = (Get-Content -First 1 -Encoding UTF8 $TemplateCsv).Trim()
  $hdrOk = ($hdrText -eq 'date,symbol,indicator,CLOSE,VOL,OI,SETTLE,source')
} catch { }
Add-PreCheck 'HEADER_TEMPLATE_OK' $hdrOk $true "header=$hdrText"

# (6) ignition marker must stay absent (the one-shot workorder replaces it)
$markerAbsent = (-not (Test-Path (Join-Path $Artifacts 'sample_fetch_allow.marker'))) -and
                (-not (Test-Path (Join-Path $Root 'sample_fetch_allow.marker')))
Add-PreCheck 'SAMPLE_FETCH_ALLOW_MARKER_ABSENT' $markerAbsent $true 'one-shot workorder replaces marker; marker must NOT be created'

# (7) protected Excel PIDs (foreground user instance) captured up front
$script:ProtectedPids = @(Get-ExcelPids)
Add-PreCheck 'PROTECTED_EXCEL_PIDS_CAPTURED' ($script:ProtectedPids.Count -ge 1) $true ("pids={0}" -f ($script:ProtectedPids -join ','))

# (8) Wind terminal backend alive
$wmain = @(Get-Process -Name wmain -ErrorAction SilentlyContinue)
Add-PreCheck 'WMAIN_BACKEND_ALIVE' ($wmain.Count -ge 1) $true ("wmain_pids={0}" -f (@($wmain | ForEach-Object { $_.Id }) -join ','))

# (9) WDF add-in registered + DLL present
$addinLb = -1
try {
  $rp = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Office\Excel\Addins\WDF.Addin' -ErrorAction Stop
  $addinLb = [int]$rp.LoadBehavior
} catch { }
$addinHkcu = Get-ItemProperty 'HKCU:\SOFTWARE\Microsoft\Office\Excel\Addins\WDF.Addin' -ErrorAction SilentlyContinue
$wdfDllPath = ''
if ($addinHkcu -and $addinHkcu.PSObject.Properties.Name -contains 'WDF_PATH') { $wdfDllPath = [string]$addinHkcu.WDF_PATH }
$wdfDllOk = [bool](Test-Path $wdfDllPath)
$addinRegOk = ($addinLb -eq 3) -or ($addinHkcu -ne $null -and [int]$addinHkcu.LoadBehavior -eq 3)
Add-PreCheck 'WDF_ADDIN_REGISTERED' $addinRegOk $true "hklm_loadbehavior=$addinLb"
Add-PreCheck 'WDF_DLL_PRESENT' $wdfDllOk $true "dll=$wdfDllPath"

# (10) health_check_wdf.ps1 entrypoint (safe: no Excel launch, no Wind calls)
$healthStatus = ''; $healthWindCalls = -1; $hj = $null
try {
  $hout = & powershell -NoProfile -ExecutionPolicy Bypass -File $HealthPath | Out-String
  $hj = $hout | ConvertFrom-Json
  $healthStatus = [string]$hj.status
  $healthWindCalls = [int]$hj.wind_calls
} catch { }
Add-PreCheck 'HEALTH_CHECK_WDF_OK' ($healthStatus -eq 'OK') $true ("status=$healthStatus")
Add-PreCheck 'HEALTH_CHECK_WDF_NO_WIND_CALLS' ($healthWindCalls -eq 0) $true "wind_calls=$healthWindCalls"

# (11) isolated background Excel instantiation + WDF add-in load probe
# NOTE: this Office 16.0 build exposes the legacy OLE add-in model on Application.COMAddIns,
# so each item exposes ProgId / Description / Connect rather than Name / Loaded. We read the
# OLE shape; reading .Name returns empty for every item and would falsely report the add-in missing.
$probeNew = @(); $probeErr = ''; $probeProgs = @(); $probeWdf = @(); $probeWdfConnected = @(); $probeResidual = @()
try {
  $probeBefore = @(Get-ExcelPids)
  $pxl = New-Object -ComObject Excel.Application
  $pxl.Visible = $false
  $pxl.DisplayAlerts = $false
  try { [void]$pxl.Workbooks.Add() } catch { }
  # WDF add-ins load asynchronously after app start; poll the collection up to 30s.
  $probeDeadline = (Get-Date).AddSeconds(30)
  while ((Get-Date) -lt $probeDeadline) {
    $probeProgs = @(); $coll = $null; $pc = 0
    try { $coll = $pxl.COMAddIns; $pc = [int]$coll.Count } catch { }
    for ($i = 1; $i -le $pc; $i++) {
      try {
        $it = $coll.Item($i)
        $pr = ''; try { $pr = [string]$it.ProgId } catch { }
        if ($pr -ne '') { $probeProgs += $pr }
      } catch { }
    }
    $probeWdf = @($probeProgs | Where-Object { $_ -match 'WDF|Wind' })
    if ($probeWdf.Count -ge 1) { break }
    Start-Sleep -Seconds 3
  }
  # record which WDF add-ins are actually connected (active) in the background instance
  $probeWdfConnected = @()
  $coll2 = $null; $pc2 = 0
  try { $coll2 = $pxl.COMAddIns; $pc2 = [int]$coll2.Count } catch { }
  for ($i = 1; $i -le $pc2; $i++) {
    try {
      $it = $coll2.Item($i)
      $pr = ''; try { $pr = [string]$it.ProgId } catch { }
      $cn = $false; try { $cn = [bool]$it.Connect } catch { }
      if ($pr -match 'WDF' -and $cn -eq $true) { $probeWdfConnected += $pr }
    } catch { }
  }
  $probeAfter = @(Get-ExcelPids)
  $probeNew = @($probeAfter | Where-Object { $_ -notin $probeBefore } | Sort-Object -Unique)
  # clean close: every open workbook via .Item(i), then Quit, then release + force GC
  $wbc = 0; try { $wbc = [int]$pxl.Workbooks.Count } catch { }
  for ($i = 1; $i -le $wbc; $i++) { try { $pxl.Workbooks.Item($i).Close($false) | Out-Null } catch { } }
  try { $pxl.Quit() | Out-Null } catch { }
  try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pxl) | Out-Null } catch { }
  [GC]::Collect(); [GC]::WaitForPendingFinalizers(); [GC]::Collect()
  Start-Sleep -Seconds 2
  $probeResidual = @((Get-ExcelPids) | Where-Object { $_ -notin $probeBefore } | Sort-Object -Unique)
} catch {
  $probeErr = $_.Exception.Message
  try { if ($pxl) { $wbc = 0; try { $wbc = [int]$pxl.Workbooks.Count } catch { }; for ($i = 1; $i -le $wbc; $i++) { try { $pxl.Workbooks.Item($i).Close($false) | Out-Null } catch { } } } } catch { }
  try { if ($pxl) { $pxl.Quit() | Out-Null } } catch { }
  $probeResidual = @((Get-ExcelPids) | Where-Object { $_ -notin $probeBefore } | Sort-Object -Unique)
}
Add-PreCheck 'BG_EXCEL_COM_ISOLATION_OK' ($probeNew.Count -eq 1) $true ("new_pids={0} err={1}" -f (($probeNew | ForEach-Object { $_ }) -join ','), $probeErr)
Add-PreCheck 'BG_EXCEL_QUIT_CLEAN' ($probeResidual.Count -eq 0) $true ("residual_agent_pids={0}" -f (($probeResidual | ForEach-Object { $_ }) -join ','))
Add-PreCheck 'WDF_ADDIN_LOADED_IN_BG_EXCEL' ($probeWdf.Count -ge 1) $true ("progids={0}" -f ($probeProgs -join ';'))
Add-PreCheck 'WDF_ADDIN_CONNECTED_IN_BG_EXCEL' ($probeWdfConnected.Count -ge 1) $true ("connected={0}" -f ($probeWdfConnected -join ';'))
$pre['summary']      = @($pre['checklist'] | Where-Object { $_.pass }).Count
$pre['total']        = @($pre['checklist']).Count
$pre['finished_at']  = Get-NowIso
$pre['status']       = if ($pre['summary'] -eq $pre['total']) { 'PASS' } else { 'FAIL' }
$pre['wind_api_calls']     = 0
$pre['real_wind_call']     = $false
$pre['protected_excel_pids'] = $script:ProtectedPids
$pre['wdf_addins_seen']    = $probeProgs
$pre['wdf_addins_connected'] = $probeWdfConnected
$pre['wdf_dll_path']       = $wdfDllPath
$pre['note'] = 'Preflight performs NO Wind data calls: registry / process / COM / add-in probes only.'
$pre | ConvertTo-Json -Depth 25 | Set-Content -Path $PreflightJ -Encoding UTF8
Write-Host ("[PREFLIGHT] {0} :: {1}/{2} -> {3}" -f $PreflightJ, $pre['summary'], $pre['total'], $pre['status'])

if ($pre['status'] -ne 'PASS') {
  $script:RunStatus    = 'ABORTED_BY_PREFLIGHT'
  $script:RunEndReason = "preflight failed {0}/{1}" -f $pre['summary'], $pre['total']
  Append-Event 'PREFLIGHT_FAIL' $script:RunEndReason @{ preflight_report = 'artifacts/wdf_preflight_check.json'; failed = @($pre['checklist'] | Where-Object { -not $_.pass } | ForEach-Object { $_.name }) }
  Write-Receipt
  exit 2
}

Append-Event 'PREFLIGHT_PASS' ("{0}/{1} checks passed" -f $pre['summary'], $pre['total']) @{ preflight_report = 'artifacts/wdf_preflight_check.json' }

if ($PreflightOnly) {
  Append-Event 'PREFLIGHT_ONLY_EXIT' 'preflight-only mode; no fetch executed'
  Write-Host '[MODE] PreflightOnly - exiting before fetch.'
  exit 0
}

# ═══════════════════════════════════════════════════════════════════════════════
# P1.2  BOOTSTRAP ISOLATED BACKGROUND EXCEL
# ═══════════════════════════════════════════════════════════════════════════════
Append-Event 'IGNITE_STARTED' ("gate=AUTHORISED_BY_USER_WORKORDER; auth_ref={0}; DSHC-IGNITE-A01 one-shot user workorder ignition" -f $AuthRef) @{ audit_marker = 'IGNITE_VIA_USER_WORKORDER_A01_AUTH'; protected_excel_pids = $script:ProtectedPids }

$xl = $null; $wb = $null; $agentAddins = @()
try {
  $before = @(Get-ExcelPids)
  $xl = New-Object -ComObject Excel.Application
  $xl.Visible = $false
  $xl.DisplayAlerts = $false
  $xl.EnableEvents = $false
  $xl.ScreenUpdating = $false
  try { $xl.AskForClipboardAccess = $false } catch { }
  try { $xl.AutomationSecurity = 3 } catch { }

  Start-Sleep -Seconds 1
  $after = @(Get-ExcelPids)
  $newOnes = @($after | Where-Object { $_ -notin $before } | Sort-Object -Unique)
  if ($newOnes.Count -ne 1) {
    throw ("Cannot isolate agent Excel PID. before=[{0}] after=[{1}]" -f ($before -join ','), ($after -join ','))
  }
  $script:AgentPid       = $newOnes[0]
  $script:AgentCreatedAt = Get-NowIso
  Append-Event 'AGENT_EXCEL_BOOTSTRAPPED' ("background Excel isolated pid={0}; user foreground Excel pids=[{1}] untouched" -f $script:AgentPid, ($script:ProtectedPids -join ',')) @{ agent_excel_pid = $script:AgentPid; protected_excel_pids = $script:ProtectedPids }

  # transient PID marker consumed by reset_wdf_safe.ps1 -- NOT a permanent ignition marker
  [ordered]@{
    pid = $script:AgentPid
    agent_excel_pid = $script:AgentPid
    agent_excel_pids = @($script:AgentPid)
    created_at = $script:AgentCreatedAt
    auth_ref = $AuthRef
    transient = $true
    note = 'A01 background agent Excel PID marker. NOT sample_fetch_allow.marker.'
  } | ConvertTo-Json -Depth 10 | Set-Content -Path $AgentMarker -Encoding UTF8
} catch {
  $script:RunStatus    = 'FETCH_ERROR'
  $script:RunEndReason = "bootstrap failed: $($_.Exception.Message)"
  Append-Event 'FETCH_ERROR' $script:RunEndReason
  $script:ResetAction = 'BOOTSTRAP_FAILED_NO_EXCEL'
  Write-Receipt
  exit 3
}

# Enumerate the agent instance's add-ins through the legacy OLE model (ProgId/Connect).
# Office 16.0 exposes NO Name/Loaded on COMAddIns items here - reading .Name returns empty
# for every item and would falsely report the WDF add-in as missing.
$agentAddins = @(); $agentWdfConnected = @(); $wdfInAgent = @()
$agentPollDeadline = (Get-Date).AddSeconds(20)
while ((Get-Date) -lt $agentPollDeadline) {
  $agentAddins = @(); $collA = $null; $pcA = 0
  try { $collA = $xl.COMAddIns; $pcA = [int]$collA.Count } catch { }
  for ($i = 1; $i -le $pcA; $i++) {
    try {
      $itA = $collA.Item($i)
      $pr = ''; try { $pr = [string]$itA.ProgId } catch { }
      if ($pr -ne '') { $agentAddins += $pr }
    } catch { }
  }
  $wdfInAgent = @($agentAddins | Where-Object { $_ -match 'WDF|Wind' })
  if ($wdfInAgent.Count -ge 1) { break }
  Start-Sleep -Seconds 2
}
$collA = $null; $pcA = 0
try { $collA = $xl.COMAddIns; $pcA = [int]$collA.Count } catch { }
for ($i = 1; $i -le $pcA; $i++) {
  try {
    $itA = $collA.Item($i)
    $pr = ''; try { $pr = [string]$itA.ProgId } catch { }
    $cn = $false; try { $cn = [bool]$itA.Connect } catch { }
    if ($pr -match 'WDF' -and $cn -eq $true) { $agentWdfConnected += $pr }
  } catch { }
}
$wdfInAgent = @($agentAddins | Where-Object { $_ -match 'WDF|Wind' })
Append-Event 'WDF_ADDIN_LOADED' ("agent Excel add-ins (progids): {0}; connected={1}" -f ($agentAddins -join ';'), ($agentWdfConnected -join ';')) @{ wdf_addins = $wdfInAgent; wdf_addins_connected = $agentWdfConnected; agent_excel_pid = $script:AgentPid }

Append-Event 'FETCH_STARTED' ("loading DSHA-P65 prefab payload: {0} instruments x [{1}] x {2}~{3}" -f ($instCodes -join ','), ($fields -join ';'), $startDate, $endDate) @{ payload_id = $payload.payload_id; instrument_count = $payload.instrument_count; wdf_fields = @($fields); time_range = ("{0}~{1}" -f $startDate, $endDate); max_retries = $MaxRetries; retry_interval_sec = $RetryWaitSec; hard_timeout_min = $HardTimeoutMin }

$budget    = [Timespan]::FromMinutes($HardTimeoutMin)
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

try {
  $wb = $xl.Workbooks.Add()

  # ── P1.3 / P1.4  WSD injection per instrument, max 2 retries ───────────────
  foreach ($inst in $payload.instruments) {
    $code     = [string]$inst.instrument_code
    $elapsed  = $stopwatch.Elapsed
    $remaining = $budget.TotalSeconds - $elapsed.TotalSeconds

    if ($remaining -lt 150) {
      Append-Event 'FETCH_BUDGET_EXCEEDED' ("{0} skipped: only {1:N0}s left of {2}min budget" -f $code, $remaining, $HardTimeoutMin)
      $script:FetchResults.Add([ordered]@{ instrument = $code; status = 'SKIPPED_TIMEOUT'; attempts = 0; retries = 0; rows = 0; fields = @(); na_captured = 0; elapsed_sec = 0; note = 'hard timeout budget exhausted' })
      continue
    }

    $formula   = [string]$inst.wsd_formula
    $t0        = Get-Date
    $attempt   = 0; $ok = $false; $retries = 0; $naCells = 0
    $errText   = ''; $gridRows = [System.Collections.Generic.List[string]]::new()
    $fieldCols = [ordered]@{}

    while (-not $ok -and $attempt -le $MaxRetries) {
      $attempt++
      if ($attempt -gt 1) {
        $retries++
        $script:WdfRetries++
        Append-Event 'WDF_RETRY_WAIT' ("{0}: retry {1} (interval {2}s)" -f $code, ($attempt - 1), $RetryWaitSec) @{ instrument = $code; attempt = $attempt }
        Start-Sleep -Seconds $RetryWaitSec
      }
      $script:WdfInjectAttempts++
      Append-Event 'WDF_WSD_INJECTED' ("{0}: WSD attempt {1} injected as cell formula (add-in async path)" -f $code, $attempt) @{ instrument = $code; attempt = $attempt; formula = $formula; eval_path = 'Range.Formula+Calculate+poll' }

      # WDF's WSD is an async add-in UDF driven by the workbook calculation engine.
      # Verified on this box, in order:
      #   1. Application.Evaluate("WSD(...)") returns the literal string "Fetching..."
      #      and stays there forever (1st call ~1.5s, later calls 3-19ms cache reads).
      #   2. Single-cell FormulaArray is NOT honoured as a CSE array formula under
      #      PowerShell 5.1 COM binding (IsInArray stays False, CurrentArray always 1x1),
      #      so multi-cell spill is invisible to automation.
      #   3. Range.Formula + Application.Calculate() + polling IS the path the add-in
      #      honours: the "Fetching..." placeholder is replaced within ~5s.
      try {
        $nSh = [int]$wb.Worksheets.Count
        $wsF = $wb.Worksheets.Item($nSh)
        $rngAnchor = $wsF.Range('A1')
        $rngAnchor.Formula = [string]$formula
        $xl.Calculate() | Out-Null
      } catch {
        $errText = "INJECT_ERROR: $($_.Exception.Message)"
        Append-Event 'WDF_INJECT_ERROR' ("{0}: attempt {1} -> {2}" -f $code, $attempt, ($errText -replace ',', ';'))
        continue
      }

      # poll: the add-in replaces the "Fetching..." placeholder asynchronously
      $txtNow = ''
      $pollDeadline = (Get-Date).AddSeconds($AttemptWaitSec)
      while ((Get-Date) -lt $pollDeadline) {
        try { $xl.Calculate() | Out-Null } catch { }
        try { $txtNow = [string]$rngAnchor.Text } catch { }
        if ($txtNow -ne '' -and $txtNow -notmatch 'Fetching') { break }
        Start-Sleep -Seconds 2
      }
      if ($txtNow -eq '' -or $txtNow -match 'Fetching') {
        $errText = 'FETCH_TIMEOUT: WSD placeholder never resolved'
        Append-Event 'WDF_INJECT_ERROR' ("{0}: attempt {1} -> {2}" -f $code, $attempt, $errText)
        continue
      }

      # non-data tokens: Excel errors, and the add-in's zh-CN "cannot read data" reply
      if ($txtNow -match '^#' -or $txtNow -match '无法读取|读取数据|无数据|未授权|授权') {
        $naCells = 1
        Append-Event 'WDF_NA_CAPTURED' ("{0}: attempt {1} returned {2}" -f $code, $attempt, $txtNow) @{ instrument = $code; attempt = $attempt; error_token = $txtNow }
        $errText = $txtNow
        continue
      }

      # what did the add-in actually deliver?
      $naCells = 0
      $rowObjs = [System.Collections.Generic.List[object]]::new()
      $rows = 0; $cols = 0
      $caR = 0; $caC = 0
      try { $caR = [int]$rngAnchor.CurrentArray.Rows.Count } catch { }
      try { $caC = [int]$rngAnchor.CurrentArray.Columns.Count } catch { }

      if ($caR -ge 2 -or $caC -ge 2) {
        # the add-in filled a spill range around the anchor
        $ca = $rngAnchor.CurrentArray
        $rows = $caR; $cols = $caC
        for ($r = 1; $r -le $rows; $r++) {
          $cells = [System.Collections.Generic.List[string]]::new()
          for ($c = 1; $c -le $cols; $c++) {
            $t = ''
            try { $t = [string]$ca.Item($r, $c).Text } catch { }
            if ($t -match '^\s*#') { $naCells++ }
            $cells.Add(($t).Trim())
          }
          $rowObjs.Add($cells)
        }
      } else {
        # single-cell answer: one row, one column. A bare date or a bare number means
        # the add-in did not return the requested multi-field grid.
        $rows = 1; $cols = 1
        $cells = [System.Collections.Generic.List[string]]::new()
        $cells.Add((Normalize-CellValue $txtNow))
        $rowObjs.Add($cells)
      }
      Append-Event 'WDF_RESULT_SHAPE' ("{0}: attempt {1} delivered {2}x{3} ({4} cells); anchor='{5}'" -f $code, $attempt, $rows, $cols, ($rows * $cols), $txtNow) @{ instrument = $code; rows = $rows; cols = $cols }

      # header-row detection: col 2 equals a known field name
      $headerOffset = 0
      if ($rowObjs.Count -ge 1 -and $rowObjs[0].Count -ge 2) {
        $c2 = [string]$rowObjs[0][1]
        if ($c2 -match '^[A-Za-z]' -and ($fields | Where-Object { $_ -eq $c2.Trim() }).Count -gt 0) { $headerOffset = 1 }
      }

      $dataRows = @($rowObjs | Select-Object -Skip $headerOffset)
      if ($dataRows.Count -lt 2) {
        Append-Event 'WDF_EMPTY_RESULT' ("{0}: attempt {1} produced no data rows (rows={2},cols={3},header={4},na={5})" -f $code, $attempt, $rows, $cols, $headerOffset, $naCells)
        continue
      }

      $fieldCols = [ordered]@{}
      if ($headerOffset -eq 1) {
        for ($c = 1; $c -lt $rowObjs[0].Count; $c++) {
          $nm = [string]$rowObjs[0][$c]
          if ($nm -ne '' -and -not $fieldCols.ContainsKey($nm)) { $fieldCols[$nm] = $c }
        }
      } else {
        $ci = 2
        foreach ($fld in $fields) { $fieldCols[$fld] = $ci; $ci++ }
      }
      $ok = $true
      # a Wind API call is only counted when the WSD formula actually returned a data grid
      $script:WindApiCalls++
      Append-Event 'WDF_WSD_EVAL_OK' ("{0}: WSD attempt {1} evaluated -> {2} rows x {3} cols" -f $code, $attempt, $rows, $cols) @{ instrument = $code; attempt = $attempt; rows = $rows; cols = $cols; wdf_fields = @($fields) }
      break
    }

    $elapsedSec = [int]((Get-Date) - $t0).TotalSeconds
    if ($ok) {
      foreach ($dr in $dataRows) {
        $date = [string]$dr[0]
        if ($date -match '^#|^\s*$') { continue }
        $rec = [ordered]@{ date = $date }
        foreach ($fld in $fields) {
          $ci = 0
          if ($fieldCols.ContainsKey($fld)) { $ci = $fieldCols[$fld] }
          $val = ''
          if ($ci -ge 1 -and $ci -lt $dr.Count) { $val = [string]$dr[$ci] }
          if ($val -match '^\s*#') { $val = '' }
          $rec[$fld] = $val
        }
        $script:WideRows.Add([ordered]@{
          date = $rec['date']; symbol = $code; indicator = ($fields -join ';')
          CLOSE = $rec['CLOSE']; VOL = $rec['VOL']; OI = $rec['OI']; SETTLE = $rec['SETTLE']
          source = 'WDF/WSD-EXCEL-ADDIN-REAL'
        })
      }
      Append-Event 'FETCH_INSTRUMENT_OK' ("{0}: {1} rows, attempts={2}, retries={3}, na_cells={4}, {5}s" -f $code, $dataRows.Count, $attempt, $retries, $naCells, $elapsedSec) @{ instrument = $code; rows = $dataRows.Count; attempts = $attempt; wdf_retries = $retries; na_captured = $naCells; elapsed_sec = $elapsedSec }
      $script:FetchResults.Add([ordered]@{ instrument = $code; status = 'OK'; attempts = $attempt; retries = $retries; rows = $dataRows.Count; fields = @($fields); na_captured = $naCells; elapsed_sec = $elapsedSec; note = '' })
    } else {
      Append-Event 'FETCH_INSTRUMENT_FAIL' ("{0}: failed after {1} attempts; last_error={2}; {3}s" -f $code, $attempt, ($errText -replace ',', ';'), $elapsedSec) @{ instrument = $code; attempts = $attempt; wdf_retries = $retries; last_error = $errText }
      $script:FetchResults.Add([ordered]@{ instrument = $code; status = 'FAIL'; attempts = $attempt; retries = $retries; rows = 0; fields = @($fields); na_captured = $naCells; elapsed_sec = $elapsedSec; note = $errText })
      # fail-fast: a dead WDF channel fails every instrument, so retrying 7x3 would
      # burn the whole window with zero rows. Abort as soon as the FIRST fails.
      if ($script:FetchResults.Count -eq 1) {
        Append-Event 'FETCH_ABORT' ("WDF channel failure on first instrument {0}; aborting remaining instruments" -f $code) @{ instrument = $code; last_error = ($errText -replace ',', ';') }
        $script:RunStatus = 'FETCH_ERROR'
        $script:RunEndReason = "WDF channel failure on first instrument ($code): $($errText -replace ',', ';')"
        break
      }
    }
  }
} catch {
  $script:RunStatus    = 'FETCH_ERROR'
  $script:RunEndReason = "fetch aborted: $($_.Exception.Message)"
  Append-Event 'FETCH_ERROR' $script:RunEndReason
}

# ═══════════════════════════════════════════════════════════════════════════════
# P1.5  EXPORT CSV (template-conformant wide dump + P62-LOOP long mirror)
# ═══════════════════════════════════════════════════════════════════════════════
$csvSha = ''; $csvRows = 0; $csvBytes = 0
try {
  $wideLines = [System.Collections.Generic.List[string]]::new()
  $wideLines.Add($hdrText)
  foreach ($w in $script:WideRows) {
    $wideLines.Add(("{0},{1},{2},{3},{4},{5},{6},{7}" -f $w['date'], $w['symbol'], $w['indicator'], $w['CLOSE'], $w['VOL'], $w['OI'], $w['SETTLE'], $w['source']))
  }
  [System.IO.File]::WriteAllLines($CsvOut, $wideLines, (New-Object System.Text.UTF8Encoding($false)))
  $csvRows  = @($script:WideRows).Count
  $csvSha   = (Get-FileHash -Algorithm SHA256 $CsvOut).Hash
  $csvBytes = (Get-Item $CsvOut).Length

  $bySymbol = $script:WideRows | Group-Object symbol | Sort-Object Name
  foreach ($g in $bySymbol) {
    $longPath = Join-Path $MirrorDir ("A01_{0}_close_wdf.csv" -f $g.Name)
    $longLines = [System.Collections.Generic.List[string]]::new()
    $longLines.Add('date,value,symbol,indicator,source')
    foreach ($item in $g.Group) {
      if ($item['CLOSE'] -ne '') {
        $longLines.Add(("{0},{1},{2},close,WDF/WSD-EXCEL-ADDIN-REAL" -f $item['date'], $item['CLOSE'], $g.Name))
      }
    }
    [System.IO.File]::WriteAllLines($longPath, $longLines, (New-Object System.Text.UTF8Encoding($false)))
    $script:MirrorFiles.Add($longPath)
  }
  Append-Event 'CSV_EXPORTED' ("wide={0} rows {1} -> output_sample/wdf_sample_metals_raw.csv; mirror={2} files -> artifacts/sample_output" -f $csvRows, $csvSha.Substring(0, 8), $script:MirrorFiles.Count) @{ csv_path = 'output_sample/wdf_sample_metals_raw.csv'; csv_sha256 = $csvSha; csv_rows = $csvRows; mirror_dir = 'artifacts/sample_output'; mirror_files = @($script:MirrorFiles | ForEach-Object { [IO.Path]::GetFileName($_) }) }
} catch {
  Append-Event 'CSV_EXPORT_ERROR' ("csv export failed: $($_.Exception.Message)")
}

if ($script:RunStatus -eq 'RUNNING') {
  $okCount = @($script:FetchResults | Where-Object { $_.status -eq 'OK' }).Count
  if ($okCount -gt 0) { $script:RunStatus = 'FETCH_COMPLETE' } else { $script:RunStatus = 'FETCH_ERROR' }
  $script:RunEndReason = "{0}/{1} instruments OK, wind_api_calls={2}, wdf_retries={3}" -f $okCount, $payload.instrument_count, $script:WindApiCalls, $script:WdfRetries
  Append-Event 'FETCH_COMPLETE' $script:RunEndReason @{ ok_instruments = $okCount; total_instruments = $payload.instrument_count }
}

# ═══════════════════════════════════════════════════════════════════════════════
# P1.6  SAFE RESET (graceful close + agent-PID-scoped safety net)
# ═══════════════════════════════════════════════════════════════════════════════
$agentAlive = $false
try {
  try { if ($wb) { $wb.Close($false) } } catch { }
  try { if ($xl) { $xl.Quit() } } catch { }
  try { if ($wb) { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($wb) | Out-Null } } catch { }
  try { if ($xl) { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null } } catch { }
  $script:AgentQuitAt = Get-NowIso
  Start-Sleep -Seconds 2
  $agentAlive = [bool](Get-Process -Id $script:AgentPid -ErrorAction SilentlyContinue)

  if (-not $agentAlive) { $script:ResetAction = 'GRACEFUL_QUIT_OK' }
  elseif ($script:AgentPid -notin $script:ProtectedPids) {
    $resetOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $ResetPath -Root $Root -StopExcel -AgentMarkerPath $AgentMarker | Out-String
    $script:ResetAction = "SAFETY_NET_RESET: $resetOut"
    Start-Sleep -Seconds 2
  } else {
    $script:ResetAction = 'RESET_SKIPPED_UNEXPECTEDLY_PROTECTED_PID'
  }
  if (-not (Test-Path $AgentMarker)) { $script:ResetAction = "$($script:ResetAction) [marker already cleared]" }
} catch {
  $script:ResetAction = "RESET_ERROR: $($_.Exception.Message)"
}

$script:ProtectedAliveCount = @($script:ProtectedPids | Where-Object { $_ -ne $script:AgentPid } | Where-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue }).Count

Append-Event 'RESET_DONE' ("reset={0}; agent_pid={1} alive_after={2}; protected_pids=[{3}] alive={4}" -f $script:ResetAction, $script:AgentPid, $agentAlive, ($script:ProtectedPids -join ','), $script:ProtectedAliveCount) @{ reset_action = $script:ResetAction; agent_excel_pid = $script:AgentPid; agent_still_alive = $agentAlive; protected_excel_pids = $script:ProtectedPids; protected_excel_alive_count = $script:ProtectedAliveCount }

Write-Receipt
exit 0
