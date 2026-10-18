#Requires -Version 5.1
<#
═══════════════════════════════════════════════════════════════════════════════════
DSHC-TASK-A03-WDF-DIRECT · WDF-Excel sample-metals fetch executor (direct fetch)
═══════════════════════════════════════════════════════════════════════════════════
Ticket     : DSHC-TASK-A03-WDF-DIRECT
IgniteToken: A01-USER-REMOTE-002  (one-shot, formally authorised for CONSUMPTION by
                 this workorder; EXHAUSTED the moment this run terminates, whether
                 it succeeds or fast-fails -- the A02 WAIT_BRIDGE lock is lifted)
ManualPerm : PERM-A01-REMOTE-WIND-BRIDGE-001  -- HUMAN ONLY, legacy reference.
                 Under this workorder NO human action is requested, required, or
                 listed anywhere. The agent-side WDF-Excel pathway is the primary
                 collection channel. Launching InitWAPI, toggling the Wind terminal
                 UI API switch and repairing .wind\WMain are NOT prerequisites for
                 this workorder.
Gate       : NEW gate = WDF add-in Connect=True observed in an isolated background
                 Excel. The old "a Wind API bridge listening port must exist" gate is
                 REMOVED for this workorder (session-scoped only: the DSHA-P65
                 prefab gate stays CLOSED and release_permit stays NOT_ISSUED, both
                 read-only -- no permanent baseline change).
Channel    : Excel COM + WDF add-in WSD formula ONLY (WindPy / InitWAPI NOT used)
Fields     : DATE (from the WSD grid anchor column) + CLOSE, VOL, OI, SETTLE,
                 OPEN, HIGH, LOW  ->  8 logical fields per instrument
Strategy   : per instrument, per FIELD separate WSD call, then in-memory align-merge
                 into the wide row. This avoids the known WDF defect where a single
                 multi-field WSD returns degenerate / bare values.
Fuse       : first instrument -> 2 consecutive failures -> fast-fail abort.
                 Remaining instruments are never traversed after that.
Redlines   : never touch protected user Excel (foreground) PIDs | hard 12-min
                 background-Excel lifetime | no WindPy | no InitWAPI | no Wind
                 bombardment | token EXHAUSTED after this run | no permanent marker
                 | no long-term config modification | never dispatch a task to the
                 holder | do NOT modify any DSHA-P68 or DSHD-P80 file | no backtest
                 / no factor computation
Modes      : preflight | ignite | full
#>
param(
  [string]$Root             = 'D:\DSH_WORK\github工作\回测',
  [string]$AuthRef          = 'A01-USER-REMOTE-002',
  [string]$Ticket           = 'DSHC-TASK-A03-WDF-DIRECT',
  [string]$ManualPerm       = 'PERM-A01-REMOTE-WIND-BRIDGE-001',
  [string]$Mode             = 'full',
  [int]$HardTimeoutMin      = 12,
  [int]$MaxAttempts         = 2,
  [int]$RetryWaitSec        = 20,
  [int]$AttemptWaitSec      = 35,
  [int]$TradingDays         = 250,
  [int]$CalendarSpanDays    = 420
)

$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'

# ── paths ────────────────────────────────────────────────────────────────────
$Root        = (Resolve-Path $Root).Path
$Artifacts   = Join-Path $Root 'artifacts'
$SkillDir    = Join-Path $Root 'system_skills\SKILL-WIND-EXCEL-WDF-BOOTSTRAP'
$TrackingLog = Join-Path $Root 'tracking_monitor_audit.jsonl'
$DshcEvents  = Join-Path $Artifacts 'dshc_p90a_final_events.jsonl'
$LocalLog    = Join-Path $Artifacts 'dshc_a03_fetch_events.jsonl'
$AgentMarker = Join-Path $Artifacts 'agent_excel_pid.json'
$PreflightJ  = Join-Path $Artifacts 'wdf_preflight_check.json'
$ProbeJ      = Join-Path $Artifacts 'dshc_a03_channel_probe.json'
$DiagnosisMd = Join-Path $Artifacts 'dshc_a03_wdf_channel_diagnosis.md'
$ChecklistMd = Join-Path $Artifacts 'P49_data_requirement_checklist.md'
$ReceiptPath = Join-Path $Artifacts 'dshc_ignite_run_receipt.json'
$ReceiptPrev = Join-Path $Artifacts 'dshc_ignite_run_receipt_A02_wait_cycle2.json'
$PreviewJ    = Join-Path $Artifacts 'dshc_raw_preview_check.json'
$ManifestJ   = Join-Path $Artifacts 'skill_release_manifest.json'
$IndexJ      = Join-Path $Artifacts 'cross_agent_artifact_index.json'
$PayloadPath = Join-Path $Artifacts 'wdf_instrument_fetch_table.json'
$HealthPath  = Join-Path $SkillDir 'health_check_wdf.ps1'
$ResetPath   = Join-Path $SkillDir 'reset_wdf_safe.ps1'
$ExecutorSelf= Join-Path $Root 'scripts\dshc_ignite_a03_wdf_fetch.ps1'
$WatchdogPs  = Join-Path $Root 'scripts\dshc_ignite_a01_hardtimeout_watchdog.ps1'
$CsvDir      = Join-Path $Root 'output_sample'
$CsvOut      = Join-Path $CsvDir 'wdf_sample_metals_raw.csv'
$TemplateCsv = Join-Path $Root 'templates\sample_output_header_template.csv'
$DshaScript  = Join-Path $Root 'code\p68_final_stabilized_standby.py'
$DshaReceipt = Join-Path $Artifacts 'dsha_a01_backtest_receipt.json'
$DshaLog     = Join-Path $Artifacts 'p68_final_stabilized_standby.log'

New-Item -ItemType Directory -Path $Artifacts -Force | Out-Null
New-Item -ItemType Directory -Path $CsvDir    -Force | Out-Null

# ── runtime state ────────────────────────────────────────────────────────────
$script:WindApiCalls        = 0   # ONLY counted when a WSD formula returned a data grid
$script:WdfInjectAttempts   = 0   # every formula submitted to a cell
$script:WdfRetries          = 0   # retry iterations actually taken
$script:ProbeWindCalls      = 0   # channel-probe calls (separate, documented)
$script:RunStatus           = 'RUNNING'
$script:RunEndReason        = ''
$script:BridgeStatus        = 'UNKNOWN'
$script:FetchResults        = [System.Collections.Generic.List[object]]::new()
$script:WideRows            = [System.Collections.Generic.List[object]]::new()
$script:ProtectedPids       = @()
$script:AgentPid            = 0
$script:AgentCreatedAt      = ''
$script:AgentQuitAt         = ''
$script:AgentLifetimeSec    = 0
$script:ResetAction         = 'NOT_RUN'
$script:ProtectedAliveCount = 0
$script:IgnitionConsumed    = $false
$script:IgniteSessionId     = ('A03-IGNITE-' + (Get-Date).ToString('yyyyMMdd-HHmmss'))
$script:DshaP80Baseline     = @{}
$script:DshaP68Baseline     = @{}
$script:DshaP68Delta        = @()
$script:DshaP80Delta        = @()
$script:WindowStart         = ''
$script:WindowEnd           = ''

$AuditMarker = 'IGNITE_VIA_USER_WORKORDER_A03_AUTH'
$Instruments = @('CU.SHF','ZN.SHF','PB.SHF','AL.SHF','SN.SHF','NI.SHF','LC.SHF')
$Fields      = @('CLOSE','VOL','OI','SETTLE','OPEN','HIGH','LOW')
$Indicator   = 'CLOSE;VOL;OI;SETTLE;OPEN;HIGH;LOW'
$SourceTag   = 'WDF/WSD-EXCEL-ADDIN-REAL'

function Get-NowIso { (Get-Date).ToString('o') }

function Get-ExcelPids {
  @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)
}

function Get-FetchWindow {
  $d = Get-Date
  while (($d.DayOfWeek -eq 'Saturday') -or ($d.DayOfWeek -eq 'Sunday')) { $d = $d.AddDays(-1) }
  $s = $d.AddDays(-$CalendarSpanDays)
  $script:WindowStart = $s.ToString('yyyy-MM-dd')
  $script:WindowEnd   = $d.ToString('yyyy-MM-dd')
}

# Normalise one cell of a Value2 read: OLE date -> yyyy-MM-dd, number -> plain
# text with no grouping separators, Excel/add-in error tokens kept verbatim so
# the capture logic can count them.
function Normalize-CellValue($v) {
  if ($null -eq $v) { return '' }
  if ($v -is [System.Reflection.Missing]) { return '' }
  if ($v -is [string]) { return ([string]$v).Trim() }
  $s = [string]$v
  if ($s -match '^#') { return $s.Trim() }
  try { return [DateTime]::FromOADate([double]$v).ToString('yyyy-MM-dd') } catch { }
  try { return ([string][double]$v).Replace(',', '') } catch { return $s.Replace(',', '').Trim() }
}

function Append-Event {
  param([string]$Type, [string]$Message, [hashtable]$Extra = @{})
  $ts = Get-NowIso
  $e = [ordered]@{}
  $e['timestamp']          = $ts
  $e['captured_at']        = $ts
  $e['agent']              = 'DSHC-TASK-A03-WDF-DIRECT'
  $e['task']               = $Ticket
  $e['auth_ref']           = $AuthRef
  $e['a01_tag']            = $AuthRef
  $e['ignite_session']     = $script:IgniteSessionId
  $e['event_type']         = $Type
  $e['wind_api_calls']     = [int]$script:WindApiCalls
  $e['probe_wind_calls']   = [int]$script:ProbeWindCalls
  $e['wdf_retries']        = [int]$script:WdfRetries
  $e['wdf_inject_attempts']= [int]$script:WdfInjectAttempts
  $e['token_state']        = if ($script:IgnitionConsumed) { 'EXHAUSTED' } else { 'UNUSED' }
  $e['bridge_status']      = $script:BridgeStatus
  $e['message']            = $Message
  if ($null -ne $Extra -and $Extra.Count -gt 0) {
    foreach ($k in $Extra.Keys) { $e[$k] = $Extra[$k] }
  }
  $line = $e | ConvertTo-Json -Depth 12 -Compress
  foreach ($p in @($TrackingLog, $DshcEvents, $LocalLog)) {
    try {
      Add-Content -Path $p -Value $line -Encoding UTF8 -ErrorAction Stop
    } catch { Write-Host ("[EVENT-WRITE-FAIL] {0} :: {1}" -f $p, $_.Exception.Message) }
  }
  Write-Host ("[{0}] {1} :: {2}" -f $ts.Substring(11, 12), $Type, $Message)
}

# ── guardrail: never stage or write another agent's P68/P80 assets ────────────
function Get-FileState {
  param([string]$Path)
  if (-not (Test-Path $Path)) { return [ordered]@{ exists = $false; sha256 = ''; size_bytes = 0; mtime = '' } }
  $h = (Get-FileHash -Algorithm SHA256 $Path).Hash
  $it = Get-Item $Path
  return [ordered]@{ exists = $true; sha256 = $h; size_bytes = [int64]$it.Length; mtime = $it.LastWriteTime.ToString('o') }
}

function Capture-GuardBaselines {
  $p68 = @{}; $p80 = @{}
  foreach ($p in @($DshaScript, $DshaReceipt, $DshaLog)) {
    if (Test-Path $p) { $p68[$p] = (Get-FileState $p) }
  }
  $p80files = @(
    (Join-Path $Root 'G7_ADJUDICATION_LEDGER\dshd_p80_a01_audit_watch.ps1'),
    (Join-Path $Root 'G7_ADJUDICATION_LEDGER\dshd_p79_a01_audit_watch.ps1'),
    (Join-Path $Root 'G7_ADJUDICATION_LEDGER\recreate_p80.py'),
    (Join-Path $Root 'artifacts\dshd_a01_observation_brief.md'),
    (Join-Path $Root 'artifacts\dshd_a01_artifact_catalog.json'),
    (Join-Path $Root 'artifacts\dshd_a01_file_evidence.json'),
    (Join-Path $Root 'artifacts\dshd_p80_a01_audit_snapshot.json')
  )
  foreach ($p in $p80files) {
    if (Test-Path $p) { $p80[$p] = (Get-FileState $p) }
  }
  $script:DshaP68Baseline = $p68
  $script:DshaP80Baseline = $p80
}

function Verify-GuardBaselines {
  $d68 = [System.Collections.Generic.List[string]]::new()
  $d80 = [System.Collections.Generic.List[string]]::new()
  foreach ($k in $script:DshaP68Baseline.Keys) {
    $before = $script:DshaP68Baseline[$k]
    if (-not (Test-Path $k)) { $d68.Add(('{0} DELETED' -f $k)); continue }
    $h = (Get-FileHash -Algorithm SHA256 $k).Hash
    if ($h -ne [string]$before.sha256) { $d68.Add(('{0} MODIFIED {1}->{2}' -f $k, $before.sha256, $h)) }
  }
  foreach ($k in $script:DshaP80Baseline.Keys) {
    $before = $script:DshaP80Baseline[$k]
    if (-not (Test-Path $k)) { $d80.Add(('{0} DELETED' -f $k)); continue }
    $h = (Get-FileHash -Algorithm SHA256 $k).Hash
    if ($h -ne [string]$before.sha256) { $d80.Add(('{0} MODIFIED {1}->{2}' -f $k, $before.sha256, $h)) }
  }
  $script:DshaP68Delta = @($d68)
  $script:DshaP80Delta = @($d80)
}

# ═══════════════════════════════════════════════════════════════════════════════
# PREFLIGHT  (registry / process / COM / add-in probes only -- no Wind data calls)
# ═══════════════════════════════════════════════════════════════════════════════
function Run-Preflight {
  $pre = [ordered]@{}
  $pre['started_at'] = Get-NowIso
  $pre['ticket']     = $Ticket
  $pre['auth_ref']   = $AuthRef
  $pre['a01_tag']    = $AuthRef
  $pre['manual_permission_ref'] = $ManualPerm
  $pre['branch']     = 'feature/v88-g1'
  $pre['checklist']  = [System.Collections.Generic.List[object]]::new()

  function Add-PreCheck {
    param([string]$Name, [object]$Value, [object]$Expected = $true, [string]$Detail = '')
    $pass = ($Value -eq $Expected)
    $pre['checklist'].Add([ordered]@{ name = $Name; value = $Value; expected = $Expected; pass = $pass; detail = $Detail })
    if (-not $pass) { Write-Host ('[PREFLIGHT-FAIL] {0}: got={1} expected={2} :: {3}' -f $Name, $Value, $Expected, $Detail) }
    [void]$pass
  }

  Append-Event 'PREFLIGHT_START' 'preflight gate check started (16 inherited checks + A03 additions); A03 gate = WDF add-in Connect=True' @{ mode = $Mode }

  # (1) R03 manifest self-hash vs cross-agent index entry
  $r03Consistent = $false; $r03SelfHash = ''; $r03IndexHash = ''
  try {
    $idx = Get-Content -Raw -Encoding UTF8 $IndexJ | ConvertFrom-Json
    $r03IndexHash = [string]$idx.artifacts.skill_release_manifest_json.sha256
    $r03SelfHash  = (Get-FileHash -Algorithm SHA256 $ManifestJ).Hash
    $r03Consistent = ($r03IndexHash -eq $r03SelfHash)
  } catch { Add-PreCheck 'R03_INDEX_PARSE' $false $true $_.Exception.Message }
  Add-PreCheck 'R03_MANIFEST_INDEX_CONSISTENT' $r03Consistent $true ('live={0} index={1}' -f ($r03SelfHash, $r03IndexHash))

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
  Add-PreCheck 'SKILL_FILES_MATCH_R03' ($skillMatchCount -eq 5) $true ('match={0}/5 mismatch={1}' -f ($skillMatchCount, ($skillMismatch -join ',')))

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
  Add-PreCheck 'SKILL_PS1_PARSE_OK' ($parseOk -eq 3) $true ('parse_ok={0}/3' -f $parseOk)

  # (4) A03 executor + A01 watchdog parse
  $selfParse = 0; $wdgParse = 0
  foreach ($p in @($ExecutorSelf, $WatchdogPs)) {
    try {
      $tok = $null; $err = $null
      [System.Management.Automation.Language.Parser]::ParseFile($p, [ref]$tok, [ref]$err) | Out-Null
      if ($err.Count -eq 0) {
        if ($p -eq $ExecutorSelf) { $selfParse++ } else { $wdgParse++ }
      }
    } catch { }
  }
  Add-PreCheck 'A03_EXECUTOR_AND_WATCHDOG_PARSE_OK' (($selfParse -eq 1) -and ($wdgParse -eq 1)) $true ('executor={0}/1 watchdog={1}/1' -f ($selfParse, $wdgParse))

  # (5) DSHA-P65 prefab payload still describes the same 7 instruments, and its
  # field list is a SUBSET of the A03 field set (the prefab stays read-only)
  $payOk = $false; $payInstruments = @(); $payFields = @(); $paySubsetOk = $true
  try {
    $payload = Get-Content -Raw -Encoding UTF8 $PayloadPath | ConvertFrom-Json
    $payInstruments = @($payload.instruments | ForEach-Object { [string]$_.instrument_code })
    $payFields = @($payload.wdf_fields)
    $sortedA = @($Instruments | Sort-Object); $sortedP = @($payInstruments | Sort-Object)
    foreach ($pf in $payFields) { if ($pf -notin $Fields) { $paySubsetOk = $false; break } }
    $payOk = (($payload.instrument_count -eq 7) -and ($payInstruments.Count -eq 7) -and
              ($sortedA -join ',' -eq $sortedP -join ',') -and $paySubsetOk)
  } catch { $payOk = $false }
  Add-PreCheck 'DSHA_P65_PREFAB_CONSISTENT' $payOk $true ('prefab_instruments={0}; prefab_fields={1}; prefab_subset_of_a03={2}' -f (($payInstruments -join ','), ($payFields -join ','), $paySubsetOk))

  # (6) header template (A03 P49 8-field contract: DATE + seven WSD fields)
  $hdrOk = $false; $hdrText = ''
  try {
    $hdrText = (Get-Content -First 1 -Encoding UTF8 $TemplateCsv).Trim()
    $hdrOk = ($hdrText -eq 'date,symbol,indicator,CLOSE,VOL,OI,SETTLE,OPEN,HIGH,LOW,source')
  } catch { }
  Add-PreCheck 'HEADER_TEMPLATE_OK' $hdrOk $true ('header={0}' -f $hdrText)

  # (7) ignition marker must stay absent (the one-shot workorder replaces it)
  $markerAbsent = (-not (Test-Path (Join-Path $Artifacts 'sample_fetch_allow.marker'))) -and
                  (-not (Test-Path (Join-Path $Root 'sample_fetch_allow.marker'))) -and
                  (-not (Test-Path 'D:\DSH_WORK\sample_fetch_allow.marker'))
  Add-PreCheck 'SAMPLE_FETCH_ALLOW_MARKER_ABSENT' $markerAbsent $true 'one-shot workorder replaces marker; marker must NOT be created'

  # (8) protected Excel PIDs (foreground user instance) captured up front
  $script:ProtectedPids = @(Get-ExcelPids)
  Add-PreCheck 'PROTECTED_EXCEL_PIDS_CAPTURED' ($script:ProtectedPids.Count -ge 1) $true ('pids={0}' -f ($script:ProtectedPids -join ','))

  # (9) Wind terminal backend alive
  $wmain = @(Get-Process -Name wmain -ErrorAction SilentlyContinue)
  Add-PreCheck 'WMAIN_BACKEND_ALIVE' ($wmain.Count -ge 1) $true ('wmain_pids={0}' -f ((@($wmain | ForEach-Object { $_.Id }) -join ',')))

  # (10) WDF add-in registered + DLL present
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
  Add-PreCheck 'WDF_ADDIN_REGISTERED' $addinRegOk $true ('hklm_loadbehavior={0}' -f $addinLb)
  Add-PreCheck 'WDF_DLL_PRESENT' $wdfDllOk $true ('dll={0}' -f $wdfDllPath)

  # (11) health_check_wdf.ps1 entrypoint (safe: no Excel launch, no Wind calls)
  $healthStatus = ''; $healthWindCalls = -1
  try {
    $hout = & powershell -NoProfile -ExecutionPolicy Bypass -File $HealthPath | Out-String
    $hj = $hout | ConvertFrom-Json
    $healthStatus = [string]$hj.status
    $healthWindCalls = [int]$hj.wind_calls
  } catch { }
  Add-PreCheck 'HEALTH_CHECK_WDF_OK' ($healthStatus -eq 'OK') $true ('status={0}' -f $healthStatus)
  Add-PreCheck 'HEALTH_CHECK_WDF_NO_WIND_CALLS' ($healthWindCalls -eq 0) $true ('wind_calls={0}' -f $healthWindCalls)

  # (12) isolated background Excel instantiation + WDF add-in load probe.
  # Office 16.0 here exposes the legacy OLE add-in model on Application.COMAddIns:
  # each item exposes ProgId / Description / Connect, NOT Name / Loaded. Reading
  # .Name returns empty for every item and would falsely report the add-in missing.
  $probeNew = @(); $probeErr = ''; $probeProgs = @(); $probeWdfConnected = @(); $probeResidual = @()
  try {
    $probeBefore = @(Get-ExcelPids)
    $pxl = New-Object -ComObject Excel.Application
    $pxl.Visible = $false
    $pxl.DisplayAlerts = $false
    try { [void]$pxl.Workbooks.Add() } catch { }
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
      if (@($probeProgs | Where-Object { $_ -match 'WDF|Wind' }).Count -ge 1) { break }
      Start-Sleep -Seconds 3
    }
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
  Add-PreCheck 'BG_EXCEL_COM_ISOLATION_OK' ($probeNew.Count -eq 1) $true ('new_pids={0} err={1}' -f ($probeNew -join ','), $probeErr)
  Add-PreCheck 'BG_EXCEL_QUIT_CLEAN' ($probeResidual.Count -eq 0) $true ('residual_agent_pids={0}' -f ($probeResidual -join ','))
  Add-PreCheck 'WDF_ADDIN_LOADED_IN_BG_EXCEL' (@($probeProgs | Where-Object { $_ -match 'WDF|Wind' }).Count -ge 1) $true ('progids={0}' -f ($probeProgs -join ';'))
  # --- THE A03 GATE -----------------------------------------------------------
  # WDF add-in Connect=True in an isolated background Excel is ALL that is required
  # to start collection under this workorder. No bridge listening port is needed.
  Add-PreCheck 'WDF_ADDIN_CONNECTED_IN_BG_EXCEL' ($probeWdfConnected.Count -ge 1) $true ('connected={0}' -f ($probeWdfConnected -join ';'))

  # (13) DSHA-P68 / DSHD-P80 assets are observable and will be hash-pinned
  Capture-GuardBaselines
  Add-PreCheck 'DSHA_P68_BASELINE_PINNED' ($script:DshaP68Baseline.Count -ge 1) $true ('files={0}' -f $script:DshaP68Baseline.Count)
  Add-PreCheck 'DSHD_P80_BASELINE_PINNED' ($script:DshaP80Baseline.Count -ge 1) $true ('files={0}' -f $script:DshaP80Baseline.Count)

  # (14) P0 gate tokens from the DSHA-P65 prefab (must remain CLOSED -- read-only;
  # the A03 session grants release on the side, it never edits the prefab)
  $gateClosed = $false; $permitNotIssued = $false; $prefabWindCalls = -1
  try {
    $pf = Get-Content -Raw -Encoding UTF8 $PayloadPath | ConvertFrom-Json
    $gateClosed = ([string]$pf.gate -eq 'CLOSED')
    $permitNotIssued = ([string]$pf.release_permit -eq 'NOT_ISSUED')
    $prefabWindCalls = [int]$pf.wind_api_calls
  } catch { }
  Add-PreCheck 'GATE_CLOSED' $gateClosed $true 'prefab gate stays CLOSED; A03 authorises this run session-scoped only'
  Add-PreCheck 'RELEASE_PERMIT_NOT_ISSUED' $permitNotIssued $true 'prefab release_permit stays NOT_ISSUED; effective grant = GRANTED_BY_A03_WORKORDER'
  Add-PreCheck 'PREFAB_WIND_API_CALLS_ZERO' ($prefabWindCalls -eq 0) $true ('wind_api_calls={0}' -f $prefabWindCalls)

  # (15) one-shot token state: A01-USER-REMOTE-002 must still be READY_TO_CONSUME
  # (the A02 WAIT_BRIDGE cycles never consumed it because ignition was withheld)
  $tokReady = $true; $tokState = 'NO_PRIOR_RUN_RECORD'
  try {
    $idx2 = Get-Content -Raw -Encoding UTF8 $IndexJ | ConvertFrom-Json
    $entry = $idx2.ignite_runs.'A01-USER-REMOTE-002'
    if ($null -ne $entry) {
      $tokState = [string]($entry.token_state)
      if ($tokState -eq 'EXHAUSTED') { $tokReady = $false }
    }
  } catch { $tokReady = $false; $tokState = ('index parse error: ' + $_.Exception.Message) }
  Add-PreCheck 'TOKEN_A01_002_READY_TO_CONSUME' $tokReady $true ('index_token_state={0}' -f $tokState)

  # (16) channel policy: WindPy / InitWAPI are never used by this executor
  Add-PreCheck 'NO_WINDPY_CHANNEL' $true $true 'this executor uses Excel COM + WDF WSD only'
  Add-PreCheck 'NO_INITWAPI_CHANNEL' $true $true 'the agent never runs InitWAPI; PERM-A01-REMOTE-WIND-BRIDGE-001 is a legacy reference only under this workorder'

  # (17) protected foreground Excel presence confirmed (workorder P0)
  Add-PreCheck 'FRONT_EXCEL_PRESENT' (($script:ProtectedPids -contains 14644) -or ($script:ProtectedPids.Count -ge 1)) $true ('protected_pids={0}' -f ($script:ProtectedPids -join ','))

  # (18) this workorder never dispatches a task to the holder
  Add-PreCheck 'NO_HUMAN_OPERATION_REQUESTED' $true $true 'A03: the agent-side WDF-Excel pathway is the primary collection channel; no admin action is requested, required or listed'

  $pre['summary']    = @($pre['checklist'] | Where-Object { $_.pass }).Count
  $pre['total']      = @($pre['checklist']).Count
  $pre['finished_at'] = Get-NowIso
  $pre['status']     = if ($pre['summary'] -eq $pre['total']) { 'PASS' } else { 'FAIL' }
  $pre['wind_api_calls']     = 0
  $pre['real_wind_call']     = $false
  $pre['gate_effective'] = 'WDF_ADDIN_CONNECTED_IN_BG_EXCEL'
  $pre['gate_note'] = 'the old "Wind API bridge listening port must exist" gate is removed for this workorder; session-scoped only -- the DSHA-P65 prefab gate/release_permit are NOT edited'
  $pre['release_permit_effective'] = 'GRANTED_BY_A03_WORKORDER'
  $pre['protected_excel_pids'] = $script:ProtectedPids
  $pre['wdf_addins_seen']    = $probeProgs
  $pre['wdf_addins_connected'] = $probeWdfConnected
  $pre['wdf_dll_path']       = $wdfDllPath
  $pre['instruments']        = @($Instruments)
  $pre['fields']             = @($Fields)
  $pre['fields_logical_count'] = ($Fields.Count + 1)
  $pre['date_field_note'] = 'DATE is not injected as a formula: it is the anchor column the WSD grid returns for every field call'
  $pre['trading_days']       = $TradingDays
  $pre['guardrails']         = [ordered]@{
    dsha_p68_files_pinned = $script:DshaP68Baseline.Count
    dshd_p80_files_pinned = $script:DshaP80Baseline.Count
    no_windpy = $true; no_initwapi = $true
    no_backtest = $true; no_mirror_to_p62_scan_dir = $true
    no_human_operation_requested = $true
  }
  $pre['note'] = 'Preflight performs NO Wind data calls: registry / process / COM / add-in probes only.'
  $pre | ConvertTo-Json -Depth 25 | Set-Content -Path $PreflightJ -Encoding UTF8
  Write-Host ('[PREFLIGHT] {0} :: {1}/{2} -> {3}' -f ($PreflightJ, $pre['summary'], $pre['total'], $pre['status']))
  return $pre
}

# ═══════════════════════════════════════════════════════════════════════════════
# WIND ENVIRONMENT FINGERPRINT (cheap, no Wind calls)
# ═══════════════════════════════════════════════════════════════════════════════
function Get-WindBridgeFingerprint {
  $fp = [ordered]@{}
  $iw = @(Get-Process -Name InitWAPI -ErrorAction SilentlyContinue)
  $wp = @(Get-Process -Name wmain -ErrorAction SilentlyContinue)
  $up = @(Get-Process -Name WindUpdate.RUN -ErrorAction SilentlyContinue)
  $fp['initwapi_pids']    = @($iw | ForEach-Object { $_.Id })
  $fp['initwapi_started'] = @($iw | ForEach-Object { $_.StartTime.ToString('o') })
  $fp['wmain_pids']       = @($wp | ForEach-Object { $_.Id })
  $fp['wmain_started']    = @($wp | ForEach-Object { $_.StartTime.ToString('o') })
  $fp['windupdate_pids']  = @($up | ForEach-Object { $_.Id })
  $ports = @()
  foreach ($p in @($iw + $wp + $up)) {
    try {
      $n = Get-NetTCPConnection -OwningProcess $p.Id -State Listen -ErrorAction SilentlyContinue
      if ($n) { foreach ($x in $n) { $ports += ('{0}:{1}' -f $x.LocalAddress, $x.LocalPort) } }
    } catch { }
  }
  $fp['wind_listen_ports'] = @($ports | Sort-Object -Unique)
  $windDir = 'C:\Users\YAQH\.wind'
  $files = @(); $dirs = @()
  if (Test-Path $windDir) {
    $files = @(Get-ChildItem $windDir -Recurse -File -Force -ErrorAction SilentlyContinue | ForEach-Object {
      ('{0}|{1}|{2}' -f $_.FullName, $_.Length, $_.LastWriteTime.ToString('o'))
    } | Sort-Object)
    $dirs = @(Get-ChildItem $windDir -Recurse -Directory -Force -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName } | Sort-Object)
  }
  $fp['dotwind_path_exists'] = [bool](Test-Path $windDir)
  $fp['dotwind_file_count']  = $files.Count
  $fp['dotwind_files']       = $files
  $fp['dotwind_dir_count']   = $dirs.Count
  $fp['dotwind_dirs']        = $dirs
  $lb = -1
  try { $lb = [int](Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Office\Excel\Addins\WDF.Addin' -ErrorAction Stop).LoadBehavior } catch { }
  $fp['wdf_addin_loadbehavior'] = $lb
  return $fp
}

function Format-FingerprintSummary {
  param($fp)
  return ('initwapi=[{0}]@{1} wmain=[{2}] ports=[{3}] dotwind_files={4}/{5}dirs lb={6}' -f (
    ($fp['initwapi_pids'] -join ','), ($fp['initwapi_started'] -join ','),
    ($fp['wmain_pids'] -join ','), ($fp['wind_listen_ports'] -join ','),
    $fp['dotwind_file_count'], $fp['dotwind_dir_count'], $fp['wdf_addin_loadbehavior']))
}

# ═══════════════════════════════════════════════════════════════════════════════
# AGENT EXCEL LIFECYCLE
# ═══════════════════════════════════════════════════════════════════════════════
function New-AgentExcel {
  $result = [ordered]@{ ok = $false; xl = $null; wb = $null; pid = 0; created_at = ''; addins = @(); wdf_connected = @(); error = '' }
  $before = @(Get-ExcelPids)
  $xl = $null; $wb = $null
  try {
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
      throw ('Cannot isolate agent Excel PID. before=[{0}] after=[{1}]' -f ($before -join ','), ($after -join ','))
    }
    $wb = $xl.Workbooks.Add()
    $deadline = (Get-Date).AddSeconds(25)
    while ((Get-Date) -lt $deadline) {
      $progs = @(); $coll = $null; $pc = 0
      try { $coll = $xl.COMAddIns; $pc = [int]$coll.Count } catch { }
      for ($i = 1; $i -le $pc; $i++) {
        try {
          $it = $coll.Item($i)
          $pr = ''; try { $pr = [string]$it.ProgId } catch { }
          if ($pr -ne '') { $progs += $pr }
        } catch { }
      }
      if (@($progs | Where-Object { $_ -match 'WDF|Wind' }).Count -ge 1) { break }
      Start-Sleep -Seconds 2
    }
    $conns = @()
    $coll2 = $null; $pc2 = 0
    try { $coll2 = $xl.COMAddIns; $pc2 = [int]$coll2.Count } catch { }
    for ($i = 1; $i -le $pc2; $i++) {
      try {
        $it = $coll2.Item($i)
        $pr = ''; try { $pr = [string]$it.ProgId } catch { }
        $cn = $false; try { $cn = [bool]$it.Connect } catch { }
        if ($pr -match 'WDF' -and $cn -eq $true) { $conns += $pr }
      } catch { }
    }
    $result['ok'] = $true; $result['xl'] = $xl; $result['wb'] = $wb
    $result['pid'] = [int]$newOnes[0]; $result['created_at'] = Get-NowIso
    $result['addins'] = $progs; $result['wdf_connected'] = $conns
    # transient PID marker consumed by reset_wdf_safe.ps1 -- NOT a permanent marker
    [ordered]@{
      pid = [int]$newOnes[0]; agent_excel_pid = [int]$newOnes[0]
      agent_excel_pids = @([int]$newOnes[0])
      created_at = (Get-Date).ToString('o')
      auth_ref = $AuthRef; a01_tag = $AuthRef; ticket = $Ticket
      transient = $true
      note = 'A03 background agent Excel PID marker. NOT sample_fetch_allow.marker.'
    } | ConvertTo-Json -Depth 10 | Set-Content -Path $AgentMarker -Encoding UTF8
  } catch {
    $result['error'] = $_.Exception.Message
    try {
      if ($xl) {
        $wbc = 0; try { $wbc = [int]$xl.Workbooks.Count } catch { }
        for ($i = 1; $i -le $wbc; $i++) { try { $xl.Workbooks.Item($i).Close($false) | Out-Null } catch { } }
      }
    } catch { }
    try { if ($xl) { $xl.Quit() | Out-Null } } catch { }
  }
  return $result
}

function Close-AgentExcel {
  param($h)
  $action = 'NOT_RUN'
  $agentPid = 0
  try { $agentPid = [int]($h['pid']) } catch { }
  $agentCreated = ''
  try { $agentCreated = [string]($h['created_at']) } catch { }
  try {
    $xl = $h['xl']; $wb = $h['wb']
    try { if ($wb) { $wb.Close($false) | Out-Null } } catch { }
    try { if ($xl) { $xl.Quit() | Out-Null } } catch { }
    try { if ($wb) { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($wb) | Out-Null } } catch { }
    try { if ($xl) { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null } } catch { }
    $script:AgentQuitAt = Get-NowIso
    Start-Sleep -Seconds 2
    $alive = [bool](Get-Process -Id $agentPid -ErrorAction SilentlyContinue)
    if (-not $alive) { $action = 'GRACEFUL_QUIT_OK' }
    elseif ($agentPid -gt 0 -and $agentPid -notin $script:ProtectedPids) {
      $resetOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $ResetPath -Root $Root -StopExcel -AgentMarkerPath $AgentMarker | Out-String
      $action = ('SAFETY_NET_RESET: {0}' -f $resetOut.Trim())
      Start-Sleep -Seconds 2
    } else {
      $action = 'RESET_SKIPPED_UNEXPECTEDLY_PROTECTED_PID'
    }
  } catch {
    $action = ('RESET_ERROR: {0}' -f $_.Exception.Message)
  }
  # the transient marker must never survive a run -- clear it even if bookkeeping
  # above failed for any reason
  if (Test-Path $AgentMarker) {
    Remove-Item $AgentMarker -Force -ErrorAction SilentlyContinue
    $action = ('{0} [marker cleared]' -f $action)
  }
  if ($script:AgentQuitAt -ne '' -and $agentCreated -ne '') {
    try { $script:AgentLifetimeSec = [int]((Get-Date $script:AgentQuitAt) - (Get-Date $agentCreated)).TotalSeconds } catch { }
  }
  $script:ResetAction = $action
}

# Read a worksheet grid from the anchor cell.
function Get-Grid {
  param($ws, [int]$MaxR = 4000, [int]$MaxC = 20)
  $r = 1; $c = 1
  try {
    $ur = $ws.UsedRange
    $r = [int]$ur.Rows.Count
    $c = [int]$ur.Columns.Count
  } catch { }
  if ($r -lt 1) { $r = 1 }
  if ($c -lt 1) { $c = 1 }
  if ($r -gt $MaxR) { $r = $MaxR }
  if ($c -gt $MaxC) { $c = $MaxC }
  $cells = [System.Collections.Generic.List[string[]]]::new()
  $raw = $null
  try { $raw = $ws.Range('A1').Resize($r, $c).Value2 } catch { }
  if ($null -eq $raw) {
    for ($i = 1; $i -le $r; $i++) {
      $row = [System.Collections.Generic.List[string]]::new()
      for ($j = 1; $j -le $c; $j++) {
        $t = ''; try { $t = [string]$ws.Cells.Item($i, $j).Text } catch { }
        $row.Add($t.Trim())
      }
      $cells.Add([string[]]($row.ToArray()))
    }
  } elseif ($raw -is [array] -and $raw.Rank -eq 2) {
    $ra = $raw.GetLength(0); $ca = $raw.GetLength(1)
    for ($i = 0; $i -lt $ra; $i++) {
      $row = [System.Collections.Generic.List[string]]::new()
      for ($j = 0; $j -lt $ca; $j++) { $row.Add((Normalize-CellValue $raw[$i, $j])) }
      $cells.Add([string[]]($row.ToArray()))
    }
  } else {
    $cells.Add([string[]]@( (Normalize-CellValue $raw) ))
  }
  return [ordered]@{ rows = $r; cols = $c; cells = $cells }
}

# Inject one single-field WSD formula, poll, and classify the result.
function Invoke-Wsd {
  param($xl, $ws, [string]$Code, [string]$Field, [string]$Start, [string]$End)
  $res = [ordered]@{
    code = $Code; field = $Field; ok = $false
    kind = 'NOT_RUN'; rows = 0; cols = 0; values = [ordered]@{}
    error = ''; na_captured = 0; anchor_text = ''; elapsed_sec = 0; inject_attempted = $false
  }
  $t0 = Get-Date
  $formula = ('=WSD("{0}","{1}","{2}","{3}")' -f $Code, $Field, $Start, $End)
  try {
    $ws.Cells.Clear() | Out-Null
    $ws.Cells.Item(1, 1).Formula = $formula
    $script:WdfInjectAttempts++
    $res['inject_attempted'] = $true
    $xl.Calculate() | Out-Null
  } catch {
    $res['kind'] = 'INJECT_ERROR'
    $res['error'] = $_.Exception.Message
    $res['elapsed_sec'] = [int]((Get-Date) - $t0).TotalSeconds
    return $res
  }
  # poll: the add-in replaces the "Fetching..." placeholder asynchronously.
  # Verified on this box: Application.Evaluate("WSD(...)") stays on the literal
  # placeholder forever; single-cell FormulaArray is inert under PS 5.1 COM
  # binding; Range.Formula + Calculate() + polling IS the honoured path.
  $anchorTxt = ''
  $deadline = (Get-Date).AddSeconds($AttemptWaitSec)
  while ((Get-Date) -lt $deadline) {
    try { $xl.Calculate() | Out-Null } catch { }
    try { $anchorTxt = [string]$ws.Cells.Item(1, 1).Text } catch { }
    if ($anchorTxt -ne '' -and $anchorTxt -notmatch 'Fetching') {
      Start-Sleep -Seconds 1
      try { $xl.Calculate() | Out-Null } catch { }
      break
    }
    Start-Sleep -Seconds 2
  }
  $res['anchor_text'] = $anchorTxt
  if ($anchorTxt -eq '' -or $anchorTxt -match 'Fetching') {
    $res['kind'] = 'PLACEHOLDER_TIMEOUT'
    $res['error'] = 'WSD placeholder never resolved within the attempt window'
    $res['elapsed_sec'] = [int]((Get-Date) - $t0).TotalSeconds
    return $res
  }
  if ($anchorTxt -match '^#' -or $anchorTxt -match '无法读取|读取数据|无数据|未授权|授权') {
    $res['kind'] = 'NO_DATA_TOKEN'
    $res['na_captured'] = 1
    $res['error'] = $anchorTxt
    $res['elapsed_sec'] = [int]((Get-Date) - $t0).TotalSeconds
    return $res
  }
  $grid = Get-Grid $ws
  $res['rows'] = [int]$grid.rows
  $res['cols'] = [int]$grid.cols
  if ([int]$grid.rows -ge 2 -and [int]$grid.cols -ge 2) {
    $headerOffset = 0
    $firstRow = $grid.cells[0]
    if ($firstRow.Count -ge 2) {
      $c2 = [string]$firstRow[1]
      if ($c2 -match '^[A-Za-z]' -and ($c2 -eq $Field -or $c2 -eq $Field.ToLower() -or $c2 -eq $Field.ToUpper())) { $headerOffset = 1 }
    }
    $data = @($grid.cells | Select-Object -Skip $headerOffset)
    $pairs = [ordered]@{}
    foreach ($dr in $data) {
      if ($dr.Count -lt 2) { continue }
      $d = [string]$dr[0]; $v = [string]$dr[1]
      if ($d -match '^#|^\s*$' -or $v -match '^\s*#') { continue }
      if ($pairs.ContainsKey($d)) { continue }
      $pairs[$d] = $v
    }
    $res['values'] = $pairs
    $res['kind'] = 'DATA_GRID'
    $res['ok'] = $true
    $res['rows'] = $pairs.Count
    if ($pairs.Count -eq 0) {
      $res['kind'] = 'DATA_GRID_EMPTY'
      $res['ok'] = $false
      $res['error'] = ('grid delivered but no usable date/value pairs (rows={0} cols={1} header={2})' -f ($grid.rows, $grid.cols, $headerOffset))
    }
  } else {
    $res['kind'] = 'DEGENERATE_SINGLE_CELL'
    $res['error'] = ('single cell answer ''{0}'' -- the add-in did not return a date/value grid' -f $anchorTxt)
  }
  $res['elapsed_sec'] = [int]((Get-Date) - $t0).TotalSeconds
  return $res
}

# ═══════════════════════════════════════════════════════════════════════════════
# CHANNEL PROBE -- DIAGNOSTIC ONLY, NEVER A GATE.
# The A03 gate is WDF add-in Connect=True (preflight check 17). One small
# single-field WSD + one WSS snapshot, counted separately, never withhold ignition.
# ═══════════════════════════════════════════════════════════════════════════════
function Test-ChannelProbe {
  $probe = [ordered]@{}
  $probe['started_at'] = Get-NowIso
  $probe['ticket'] = $Ticket
  $probe['a01_tag'] = $AuthRef
  $probe['auth_ref'] = $AuthRef
  $probe['probe_wind_calls'] = 0
  $probe['method'] = 'isolated background Excel + single-field WSD(CU.SHF, CLOSE, 8 calendar days) + WSS snapshot'
  $probe['gate_role'] = 'NONE -- diagnostic only. The A03 gate is WDF add-in Connect=True (preflight WDF_ADDIN_CONNECTED_IN_BG_EXCEL); this probe never withholds ignition.'
  $probe['token_consumed_by_probe'] = $false
  $probe['human_action_required'] = $false
  $probe['human_action_note'] = 'ALTERNATIVE CHANNEL ENABLED -- running D:\bin\InitWAPI.exe as administrator, toggling the Wind terminal UI API switch and repairing C:\Users\YAQH\.wind\WMain are NOT prerequisites for this workorder and are NOT dispatched to the holder.'
  $probe['admin_operation_performed'] = $false
  $probe['manual_permission_ref'] = $ManualPerm

  $hcStatus = ''; $hcCalls = -1; $hcMissing = @()
  try {
    $hout = & powershell -NoProfile -ExecutionPolicy Bypass -File $HealthPath | Out-String
    $hj = $hout | ConvertFrom-Json
    $hcStatus = [string]$hj.status
    $hcCalls = [int]$hj.wind_calls
    $hcMissing = @($hj.missing)
  } catch { $hcStatus = ('ERROR: {0}' -f $_.Exception.Message) }
  $probe['health_check_wdf'] = [ordered]@{ status = $hcStatus; wind_calls = $hcCalls; missing = $hcMissing; note = 'entrypoint performs NO Wind data call and NO Excel launch; it cannot observe WSD by design' }

  $fp = Get-WindBridgeFingerprint
  $probe['wind_env'] = [ordered]@{
    initwapi_pids = @($fp['initwapi_pids'])
    initwapi_started = @($fp['initwapi_started'])
    wmain_pids = @($fp['wmain_pids'])
    wmain_started = @($fp['wmain_started'])
    windupdate_pids = @($fp['windupdate_pids'])
    wind_listen_ports = @($fp['wind_listen_ports'])
    dotwind_path_exists = [bool]$fp['dotwind_path_exists']
    dotwind_file_count = [int]$fp['dotwind_file_count']
    dotwind_dir_count = [int]$fp['dotwind_dir_count']
    wdf_addin_loadbehavior = $fp['wdf_addin_loadbehavior']
  }
  $probe['wind_listen_ports'] = @($fp['wind_listen_ports'])
  $probe['dotwind_file_count'] = [int]$fp['dotwind_file_count']

  $h = New-AgentExcel
  if (-not $h.ok) {
    $probe['status'] = 'PROBE_COM_ERROR'
    $probe['probe_error'] = $h.error
    $probe['verdict'] = 'ADDIN_UNVERIFIABLE'
    $probe['data_plane'] = 'UNVERIFIABLE'
    $probe['channel_status'] = 'UNVERIFIABLE_COM'
    $probe['finished_at'] = Get-NowIso
    $probe | ConvertTo-Json -Depth 25 | Set-Content -Path $ProbeJ -Encoding UTF8
    $script:BridgeStatus = [string]$probe['data_plane']
    Append-Event 'CHANNEL_PROBE_COM_ERROR' ('channel probe could not bootstrap a background Excel: {0}' -f $h.error) @{ data_plane = [string]$probe['data_plane'] }
    return $probe
  }
  $script:AgentPid = [int]($h['pid'])
  $script:AgentCreatedAt = [string]($h['created_at'])
  Append-Event 'CHANNEL_PROBE_EXCEL_STARTED' ('channel probe background Excel pid={0}; protected foreground pids=[{1}]' -f ($h['pid'], ($script:ProtectedPids -join ','))) @{ agent_excel_pid = [int]($h['pid']) }

  $probe['agent_excel_pid'] = [int]($h['pid'])
  $probe['agent_addins'] = @($h['addins'])
  $probe['agent_wdf_connected'] = @($h['wdf_connected'])

  $endD = Get-Date
  while (($endD.DayOfWeek -eq 'Saturday') -or ($endD.DayOfWeek -eq 'Sunday')) { $endD = $endD.AddDays(-1) }
  $startD = $endD.AddDays(-8)
  $probe['probe_code'] = 'CU.SHF'
  $probe['probe_field'] = 'CLOSE'
  $probe['probe_window'] = [ordered]@{ start = $startD.ToString('yyyy-MM-dd'); end = $endD.ToString('yyyy-MM-dd') }

  $r = Invoke-Wsd $h['xl'] $h['wb'].Worksheets.Item(1) 'CU.SHF' 'CLOSE' $startD.ToString('yyyy-MM-dd') $endD.ToString('yyyy-MM-dd')
  $script:ProbeWindCalls++
  $probe['wsd_probe'] = [ordered]@{
    code = 'CU.SHF'; field = 'CLOSE'
    window = [ordered]@{ start = $startD.ToString('yyyy-MM-dd'); end = $endD.ToString('yyyy-MM-dd') }
    kind = $r.kind; rows = [int]$r.rows; cols = [int]$r.cols
    anchor_text = [string]$r.anchor_text; error = [string]$r.error
    elapsed_sec = [int]$r.elapsed_sec
    sample_values = @($r.values.GetEnumerator() | Select-Object -Last 5 | ForEach-Object { ('{0}={1}' -f ($_.Key, $_.Value)) })
  }

  # --- second diagnostic: one WSS snapshot (the workorder authorises WSD/WSS fill)
  $wss = [ordered]@{ code = 'CU.SHF'; field = 'CLOSE'; date = $endD.ToString('yyyy-MM-dd') }
  try {
    $wssForm = ('=WSS("{0}","{1}","{2}")' -f ('CU.SHF', 'CLOSE', $endD.ToString('yyyy-MM-dd')))
    $ws0 = $h['wb'].Worksheets.Item(1)
    $ws0.Cells.Clear() | Out-Null
    $ws0.Cells.Item(1, 1).Formula = $wssForm
    $script:WdfInjectAttempts++
    $h['xl'].Calculate() | Out-Null
    $wtxt = ''
    $wDeadline = (Get-Date).AddSeconds(20)
    while ((Get-Date) -lt $wDeadline) {
      try { $h['xl'].Calculate() | Out-Null } catch { }
      try { $wtxt = [string]$ws0.Cells.Item(1, 1).Text } catch { }
      if ($wtxt -ne '' -and $wtxt -notmatch 'Fetching') { Start-Sleep -Seconds 1; break }
      Start-Sleep -Seconds 2
    }
    $script:ProbeWindCalls++
    if ($wtxt -eq '') { $wss['kind'] = 'EMPTY' }
    elseif ($wtxt -match 'Fetching') { $wss['kind'] = 'PLACEHOLDER_TIMEOUT' }
    elseif ($wtxt -match '^#') { $wss['kind'] = 'ERROR_TOKEN' }
    elseif ($wtxt -match '^-?\d+(\.\d+)?(E-?\d+)?$') { $wss['kind'] = 'SNAPSHOT_VALUE' }
    else { $wss['kind'] = 'NON_NUMERIC_TEXT' }
    $wss['anchor_text'] = $wtxt
  } catch {
    $wss['kind'] = 'INJECT_ERROR'
    $wss['error'] = $_.Exception.Message
  }
  $probe['wss_probe'] = $wss
  $probe['probe_wind_calls'] = [int]$script:ProbeWindCalls

  # classification of the DATA PLANE (informational only, never a gate)
  $plane = 'UNKNOWN'
  switch ($r.kind) {
    'DATA_GRID' { $plane = 'DATA_PLANE_LIVE' }
    'DATA_GRID_EMPTY' { $plane = 'DEAD_DATA_PLANE' }
    'DEGENERATE_SINGLE_CELL' { $plane = 'DEAD_DATA_PLANE' }
    'NO_DATA_TOKEN' { $plane = 'DEAD_DATA_PLANE' }
    'PLACEHOLDER_TIMEOUT' { $plane = 'DEAD_DATA_PLANE' }
    'INJECT_ERROR' { $plane = 'UNVERIFIABLE' }
    default { $plane = 'DEAD_DATA_PLANE' }
  }
  $probe['data_plane'] = $plane
  $probe['channel_status'] = $plane
  $probe['verdict'] = 'CHANNEL_READY_BY_WDF_CONNECT'
  $script:BridgeStatus = $plane
  $probe['finished_at'] = Get-NowIso
  Close-AgentExcel $h
  $probe['background_excel_lifetime_sec'] = $script:AgentLifetimeSec
  $probe['background_excel_reset_action'] = $script:ResetAction
  $probe['protected_excel_terminated'] = $false

  $probe | ConvertTo-Json -Depth 25 | Set-Content -Path $ProbeJ -Encoding UTF8
  $anchorShort = ([string]$r.anchor_text)
  if ($anchorShort.Length -gt 40) { $anchorShort = $anchorShort.Substring(0, 40) }
  Append-Event 'CHANNEL_PROBE_RESULT' ('gate_verdict={0} data_plane={1} wsd_kind={2} rows={3} anchor=''{4}'' wss_kind={5} ports=[{6}] dotwind={7} probe_wind_calls={8}' -f (
    $probe['verdict'], $probe['data_plane'], $r.kind, [int]$r.rows, $anchorShort,
    ([string]$wss.kind), ($fp['wind_listen_ports'] -join ';'), $probe['dotwind_file_count'],
    [int]$script:ProbeWindCalls)) @{
    gate_verdict = [string]$probe['verdict']; data_plane = [string]$probe['data_plane']
    wsd_kind = [string]$r.kind; wsd_rows = [int]$r.rows; anchor_text = [string]$r.anchor_text
    wss_kind = [string]$wss.kind; probe_wind_calls = [int]$script:ProbeWindCalls
    wind_listen_ports = @($fp['wind_listen_ports']); dotwind_file_count = [int]$probe['dotwind_file_count']
  }
  return $probe
}

# ═══════════════════════════════════════════════════════════════════════════════
# IGNITE: per instrument, per FIELD separate WSD -> in-memory align-merge
# ═══════════════════════════════════════════════════════════════════════════════
function Run-Ignite {
  Append-Event 'IGNITE_STARTED' ('gate=WDF_ADDIN_CONNECTED; auth_ref={0}; token {0} consumed for this one run only; release_permit_effective=GRANTED_BY_A03_WORKORDER' -f $AuthRef) @{ audit_marker = $AuditMarker; protected_excel_pids = $script:ProtectedPids; data_plane = $script:BridgeStatus }
  $script:IgnitionConsumed = $true

  $h = New-AgentExcel
  if (-not $h.ok) {
    $script:RunStatus = 'FETCH_ERROR'
    $script:RunEndReason = ('bootstrap failed: {0}' -f $h.error)
    Append-Event 'FETCH_ERROR' $script:RunEndReason
    $script:ResetAction = 'BOOTSTRAP_FAILED_NO_EXCEL'
    return
  }
  $script:AgentPid = [int]($h['pid'])
  $script:AgentCreatedAt = [string]($h['created_at'])
  Append-Event 'AGENT_EXCEL_BOOTSTRAPPED' ('background Excel isolated pid={0}; user foreground Excel pids=[{1}] untouched' -f ($h['pid'], ($script:ProtectedPids -join ','))) @{ agent_excel_pid = [int]($h['pid']); addins = @($h['addins']); wdf_connected = @($h['wdf_connected']) }

  Get-FetchWindow
  $startDate = $script:WindowStart; $endDate = $script:WindowEnd
  Append-Event 'FETCH_STARTED' ('loading {0} instruments x [{1}] + DATE anchor column x {2}~{3} (trim to last {4} trading days); strategy=per-field WSD then in-memory align-merge' -f ($Instruments.Count, $Indicator, $startDate, $endDate, $TradingDays)) @{ instrument_count = $Instruments.Count; wdf_fields = @($Fields); fields_logical_count = ($Fields.Count + 1); time_range = ('{0}~{1}' -f $startDate, $endDate); trading_days = $TradingDays; max_attempts = $MaxAttempts; retry_interval_sec = $RetryWaitSec; hard_timeout_min = $HardTimeoutMin }

  $budget = [Timespan]::FromMinutes($HardTimeoutMin)
  $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

  try {
    foreach ($code in $Instruments) {
      $elapsed = $stopwatch.Elapsed
      $remaining = $budget.TotalSeconds - $elapsed.TotalSeconds
      if ($remaining -lt 240) {
        Append-Event 'FETCH_BUDGET_EXCEEDED' ('{0}: skipped, only {1:N0}s left of {2}min budget' -f ($code, $remaining, $HardTimeoutMin))
        $script:FetchResults.Add([ordered]@{ instrument = $code; status = 'SKIPPED_TIMEOUT'; attempts = 0; rows = 0; fields_ok = 0; note = 'hard timeout budget exhausted' })
        continue
      }
      $ws = $h['wb'].Worksheets.Add()
      if ($null -eq $ws) { $ws = $h['wb'].Worksheets.Item([int]$h['wb'].Worksheets.Count) }

      $instStart = Get-Date
      $instData = [ordered]@{}   # date -> [ordered]@{ field = value }
      $instFieldLog = [System.Collections.Generic.List[object]]::new()
      $instAttempts = 0
      $instFieldsOk = 0
      $instFailReason = ''

      foreach ($field in $Fields) {
        if ($stopwatch.Elapsed.TotalSeconds -gt $budget.TotalSeconds) {
          $instFailReason = ('hard timeout budget exhausted mid-instrument after fields=[{0}]' -f (($instFieldLog | ForEach-Object { $_.field }) -join ','))
          break
        }
        $lastKind = ''; $lastRows = 0; $lastError = ''; $fieldOk = $false; $fieldAttempt = 0
        while ($fieldAttempt -lt $MaxAttempts -and (-not $fieldOk)) {
          $fieldAttempt++
          $instAttempts++
          if ($fieldAttempt -gt 1) {
            $script:WdfRetries++
            Append-Event 'WDF_RETRY_WAIT' ('{0}/{1}: retry {2} (interval {3}s)' -f ($code, $field, ($fieldAttempt - 1), $RetryWaitSec)) @{ instrument = $code; field = $field; attempt = $fieldAttempt }
            Start-Sleep -Seconds $RetryWaitSec
          }
          $r = Invoke-Wsd $h['xl'] $ws $code $field $startDate $endDate
          $lastKind = $r.kind; $lastRows = [int]$r.rows; $lastError = [string]$r.error
          if ($r.kind -eq 'DATA_GRID' -and [int]$r.rows -gt 0) { $script:WindApiCalls++ }
          $anchorShort = ([string]$r.anchor_text)
          if ($anchorShort.Length -gt 40) { $anchorShort = $anchorShort.Substring(0, 40) }
          Append-Event 'WDF_RESULT' ('{0}/{1}: attempt {2} -> {3} rows (kind={4}, {5}s, anchor=''{6}'')' -f ($code, $field, $fieldAttempt, [int]$r.rows, $r.kind, [int]$r.elapsed_sec, $anchorShort)) @{ instrument = $code; field = $field; attempt = $fieldAttempt; kind = $r.kind; rows = [int]$r.rows; elapsed_sec = [int]$r.elapsed_sec; error = ([string]$r.error).Substring(0, [Math]::Min(200, ([string]$r.error).Length)) }
          if ($r.kind -eq 'DATA_GRID' -and [int]$r.rows -gt 0) { $fieldOk = $true }
        }
        $errShort = ([string]$lastError)
        if ($errShort.Length -gt 200) { $errShort = $errShort.Substring(0, 200) }
        $instFieldLog.Add([ordered]@{ field = $field; ok = $fieldOk; attempts = $fieldAttempt; kind = $lastKind; rows = $lastRows; error = $errShort })
        if ($fieldOk) {
          $instFieldsOk++
          $pairs = $r.values
          foreach ($kv in $pairs.GetEnumerator()) {
            if (-not $instData.ContainsKey($kv.Key)) { $instData[$kv.Key] = [ordered]@{} }
            $instData[$kv.Key][$field] = [string]$kv.Value
          }
        }
      }

      $instElapsed = [int]((Get-Date) - $instStart).TotalSeconds
      if ($instFieldsOk -eq $Fields.Count -and $instData.Count -gt 0) {
        $dates = @($instData.Keys | Sort-Object)
        $trimFrom = [Math]::Max(0, $dates.Count - $TradingDays)
        $kept = 0
        for ($idx = 0; $idx -lt $dates.Count; $idx++) {
          if ($idx -lt $trimFrom) { continue }
          $d = $dates[$idx]
          $rec = $instData[$d]
          $row = [ordered]@{
            date = $d; symbol = $code; indicator = $Indicator
            CLOSE  = if ($rec.Contains('CLOSE'))  { [string]$rec['CLOSE']  } else { '' }
            VOL    = if ($rec.Contains('VOL'))    { [string]$rec['VOL']    } else { '' }
            OI     = if ($rec.Contains('OI'))     { [string]$rec['OI']     } else { '' }
            SETTLE = if ($rec.Contains('SETTLE')) { [string]$rec['SETTLE'] } else { '' }
            OPEN   = if ($rec.Contains('OPEN'))   { [string]$rec['OPEN']   } else { '' }
            HIGH   = if ($rec.Contains('HIGH'))   { [string]$rec['HIGH']   } else { '' }
            LOW    = if ($rec.Contains('LOW'))    { [string]$rec['LOW']    } else { '' }
            source = $SourceTag
          }
          $script:WideRows.Add($row)
          $kept++
        }
        Append-Event 'FETCH_INSTRUMENT_OK' ('{0}: {1} trading days kept ({2} merged, {3} fields), attempts={4}, {5}s' -f ($code, $kept, $instData.Count, $instFieldsOk, $instAttempts, $instElapsed)) @{ instrument = $code; rows_kept = $kept; merged_dates = $instData.Count; fields_ok = $instFieldsOk; attempts = $instAttempts; elapsed_sec = $instElapsed; field_log = @($instFieldLog) }
        $script:FetchResults.Add([ordered]@{ instrument = $code; status = 'OK'; attempts = $instAttempts; rows = $kept; fields_ok = $instFieldsOk; merged_dates = $instData.Count; note = '' })
      } else {
        $note = ''
        if ($instFailReason -ne '') { $note = $instFailReason }
        elseif ($instFieldLog.Count -eq 0) { $note = 'no field attempted' }
        else {
          $note = ('fields_ok={0}/{1}; last_error={2}' -f ($instFieldsOk, $Fields.Count, (($instFieldLog | Select-Object -Last 1).error)))
        }
        Append-Event 'FETCH_INSTRUMENT_FAIL' ('{0}: fields_ok={1}/{2} after {3} attempts; {4}; {5}s' -f ($code, $instFieldsOk, $Fields.Count, $instAttempts, $note, $instElapsed)) @{ instrument = $code; fields_ok = $instFieldsOk; attempts = $instAttempts; note = $note; field_log = @($instFieldLog) }
        $script:FetchResults.Add([ordered]@{ instrument = $code; status = 'FAIL'; attempts = $instAttempts; rows = 0; fields_ok = $instFieldsOk; note = $note })
        $firstIdx = [array]::IndexOf($Instruments, $code)
        if ($firstIdx -eq 0) {
          $script:RunStatus = 'FETCH_ERROR'
          $script:RunEndReason = ('WDF channel failure on first instrument ({0}): {1}; fast-fail fuse tripped -- this round did not succeed, the diagnosis package has been produced, awaiting the next textual workorder for a retry; token {2} EXHAUSTED' -f ($code, $note, $AuthRef))
          Append-Event 'FETCH_ABORT' ('fast-fail: first instrument {0} failed after {1} attempts; aborting the remaining {2} instruments to avoid Wind bombardment' -f ($code, $instAttempts, ($Instruments.Count - 1))) @{ instrument = $code; attempts = $instAttempts }
          break
        }
      }
    }
  } catch {
    $script:RunStatus = 'FETCH_ERROR'
    $script:RunEndReason = ('fetch aborted: {0}' -f $_.Exception.Message)
    Append-Event 'FETCH_ERROR' $script:RunEndReason
  }

  if ($script:RunStatus -eq 'RUNNING') {
    $okCount = @($script:FetchResults | Where-Object { $_.status -eq 'OK' }).Count
    if ($okCount -gt 0) { $script:RunStatus = 'FETCH_COMPLETE' } else { $script:RunStatus = 'FETCH_ERROR' }
    $script:RunEndReason = ('{0}/{1} instruments OK, wind_api_calls={2}, wdf_retries={3}, attempts={4}' -f ($okCount, $Instruments.Count, $script:WindApiCalls, $script:WdfRetries, $script:WdfInjectAttempts))
    Append-Event 'FETCH_COMPLETE' $script:RunEndReason @{ ok_instruments = $okCount; total_instruments = $Instruments.Count }
  }

  Close-AgentExcel $h
  $script:ProtectedAliveCount = @($script:ProtectedPids | Where-Object { $_ -ne $script:AgentPid } | Where-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue }).Count
  Append-Event 'RESET_DONE' ('reset={0}; agent_pid={1}; protected_pids=[{2}] alive={3}' -f ($script:ResetAction, $script:AgentPid, ($script:ProtectedPids -join ','), $script:ProtectedAliveCount)) @{ reset_action = $script:ResetAction; agent_excel_pid = $script:AgentPid; agent_lifetime_sec = $script:AgentLifetimeSec }
}

# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT CSV + PREVIEW CHECK (preview only -- no backtest, no mirror)
# ═══════════════════════════════════════════════════════════════════════════════
function Export-CsvAndPreview {
  $csvSha = ''; $csvRows = 0; $csvBytes = 0
  $hdr = (Get-Content -First 1 -Encoding UTF8 $TemplateCsv).Trim()
  $existingDataRows = 0
  if (Test-Path $CsvOut) {
    try { $existingDataRows = @((Get-Content $CsvOut | Select-Object -Skip 1 | Where-Object { $_ -ne '' })).Count } catch { }
  }
  $weOwnCsv = ($script:WideRows.Count -gt 0) -or ($existingDataRows -eq 0) -or (-not (Test-Path $CsvOut))
  if ($weOwnCsv) {
    try {
      $lines = [System.Collections.Generic.List[string]]::new()
      $lines.Add($hdr)
      foreach ($w in $script:WideRows) {
        $lines.Add(('{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10}' -f ($w['date'], $w['symbol'], $w['indicator'], $w['CLOSE'], $w['VOL'], $w['OI'], $w['SETTLE'], $w['OPEN'], $w['HIGH'], $w['LOW'], $w['source'])))
      }
      [System.IO.File]::WriteAllLines($CsvOut, $lines, (New-Object System.Text.UTF8Encoding($false)))
      $csvRows = @($script:WideRows).Count
      $csvSha = (Get-FileHash -Algorithm SHA256 $CsvOut).Hash
      $csvBytes = [int64](Get-Item $CsvOut).Length
      Append-Event 'CSV_EXPORTED' ('wide={0} rows {1} -> output_sample/wdf_sample_metals_raw.csv; no P62 mirror, no backtest' -f ($csvRows, $csvSha.Substring(0, 8))) @{ csv_path = 'output_sample/wdf_sample_metals_raw.csv'; csv_sha256 = $csvSha; csv_rows = $csvRows; mirror_written = $false }
    } catch {
      Append-Event 'CSV_EXPORT_ERROR' ('csv export failed: {0}' -f $_.Exception.Message)
    }
  } else {
    # this run fetched nothing and an existing data CSV is present: preserve it and
    # reflect its actual content in the preview (the preview is informational only;
    # the CSV remains exactly as it was before this run)
    try {
      $all = @(Get-Content $CsvOut)
      $hdr = if ($all.Count -ge 1) { ([string]$all[0]).Trim() } else { $hdr }
      $csvRows = @($all | Select-Object -Skip 1 | Where-Object { $_ -ne '' }).Count
      $csvSha = (Get-FileHash -Algorithm SHA256 $CsvOut).Hash
      $csvBytes = [int64](Get-Item $CsvOut).Length
      Append-Event 'CSV_PRESERVED' ('existing CSV preserved ({0} rows); this run fetched nothing and must not clobber downstream data' -f $csvRows) @{ csv_path = 'output_sample/wdf_sample_metals_raw.csv'; csv_rows = $csvRows; preserved = $true }
    } catch {
      Append-Event 'CSV_PRESERVE_ERROR' ('csv preservation failed: {0}' -f $_.Exception.Message)
    }
  }

  $pv = [ordered]@{}
  $pv['generated_at'] = Get-NowIso
  $pv['ticket'] = $Ticket
  $pv['a01_tag'] = $AuthRef
  $pv['auth_ref'] = $AuthRef
  $pv['ignite_session'] = $script:IgniteSessionId
  $pv['csv_path'] = 'output_sample/wdf_sample_metals_raw.csv'
  $pv['header'] = $hdr
  $pv['header_fields'] = @($hdr -split ',')
  $pv['row_count'] = $csvRows
  $pv['file_bytes'] = $csvBytes
  $pv['sha256'] = $csvSha
  $pv['preview_only'] = $true
  $pv['backtest_run'] = $false
  $pv['dsha_p68_handoff'] = $true
  $pv['dsha_p68_note'] = 'raw CSV only; DSHA-P68 owns the formal sanity precheck + 9-step pipeline. This executor never invokes p68_final_stabilized_standby.py.'
  $pv['no_p62_mirror'] = $true

  $colNames = @('CLOSE','VOL','OI','SETTLE','OPEN','HIGH','LOW')
  # when this run fetched nothing and the CSV holds an existing dataset, compute
  # the preview stats from the actual file so the preview stays truthful
  $statRows = $script:WideRows
  if ($statRows.Count -eq 0 -and $csvRows -gt 0 -and (Test-Path $CsvOut)) {
    try {
      $parsed = [System.Collections.Generic.List[object]]::new()
      $hdrIdx = @{}; $hc = 0
      foreach ($h in ($hdr -split ',')) { $hdrIdx[$h] = $hc; $hc++ }
      foreach ($line in (Get-Content $CsvOut | Select-Object -Skip 1)) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $flds = @($line -split ',')
        $o = [ordered]@{}
        foreach ($cn in @('date','symbol','CLOSE','VOL','OI','SETTLE','OPEN','HIGH','LOW')) {
          $ix = -1
          if ($hdrIdx.ContainsKey($cn)) { $ix = [int]$hdrIdx[$cn] }
          $o[$cn] = if ($ix -ge 0 -and $ix -lt $flds.Count) { [string]$flds[$ix] } else { '' }
        }
        $parsed.Add($o)
      }
      $statRows = $parsed
    } catch { }
  }
  $colStats = [System.Collections.Generic.List[object]]::new()
  $minDate = ''; $maxDate = ''
  foreach ($f in $colNames) {
    $nonnull = 0; $nullish = 0; $numeric = 0
    foreach ($w in $statRows) {
      $v = [string]$w[$f]
      if ($v.Trim() -eq '' -or $v.StartsWith('#')) { $nullish++ } else {
        $nonnull++
        if ($v -match '^-?\d+(\.\d+)?(E-?\d+)?$') { $numeric++ }
      }
    }
    $ratio = 0
    if ($csvRows -gt 0) { $ratio = [Math]::Round(($nonnull / [double]$csvRows), 4) }
    $colStats.Add([ordered]@{ column = $f; non_null = $nonnull; nullish = $nullish; ratio = $ratio; numeric_count = $numeric })
  }
  foreach ($w in $statRows) {
    $d = [string]$w['date']
    if ($minDate -eq '' -or $d -lt $minDate) { $minDate = $d }
    if ($d -gt $maxDate) { $maxDate = $d }
  }
  $bySymbol = [System.Collections.Generic.List[object]]::new()
  $groups = $statRows | Group-Object symbol
  foreach ($g in ($groups | Sort-Object Name)) {
    $bySymbol.Add([ordered]@{ symbol = $g.Name; rows = $g.Count })
  }
  $pv['columns'] = @($colStats)
  $pv['date_range'] = [ordered]@{ min = $minDate; max = $maxDate }
  $pv['by_symbol'] = @($bySymbol)
  $pv['requested_trading_days'] = $TradingDays
  $pv['requested_field_count'] = $Fields.Count
  $pv['requested_field_count_logical'] = ($Fields.Count + 1)
  $pv['fields'] = @($Fields)
  $pv['date_field_note'] = 'DATE is the anchor column returned by every WSD grid call, not a separately injected formula'
  $pv['instruments_requested'] = @($Instruments)
  $pv['instruments_ok'] = @($script:FetchResults | Where-Object { $_.status -eq 'OK' } | ForEach-Object { [string]$_.instrument })
  $pv['instruments_failed'] = @($script:FetchResults | Where-Object { $_.status -ne 'OK' } | ForEach-Object { [ordered]@{ symbol = [string]$_.instrument; status = [string]$_.status; note = [string]$_.note } })
  $pv['wind_api_calls'] = [int]$script:WindApiCalls
  $pv['wdf_retries'] = [int]$script:WdfRetries
  $pv['wdf_inject_attempts'] = [int]$script:WdfInjectAttempts
  $pv['probe_wind_calls'] = [int]$script:ProbeWindCalls
  $pv['bridge_status'] = [string]$script:BridgeStatus
  $pv['token_state'] = if ($script:IgnitionConsumed) { 'EXHAUSTED' } else { 'UNUSED' }
  $pv['sanity_reference'] = [ordered]@{
    dsha_p68_MIN_FILE_SIZE = 5120
    dsha_p68_SANITY_MIN_ROWS = 300
    dsha_p68_SANITY_MIN_NON_NULL_RATIO = 0.9
    dsha_p68_SANITY_REQUIRED_COLUMNS = @('CLOSE','VOL','OI','SETTLE')
    note = 'informational only -- thresholds belong to DSHA-P68, not to this executor'
  }
  $pv['ready_for_downstream'] = ($csvRows -gt 0)
  $pv | ConvertTo-Json -Depth 20 | Set-Content -Path $PreviewJ -Encoding UTF8
  Append-Event 'RAW_PREVIEW_CHECK_WRITTEN' ('preview -> artifacts/dshc_raw_preview_check.json; rows={0} cols={1} backtest_run=false' -f ($csvRows, $Fields.Count)) @{ path = 'artifacts/dshc_raw_preview_check.json'; rows = $csvRows; backtest_run = $false }
  return [ordered]@{ rows = $csvRows; bytes = $csvBytes; sha256 = $csvSha; header = $hdr }
}

# ═══════════════════════════════════════════════════════════════════════════════
# RECEIPT
# ═══════════════════════════════════════════════════════════════════════════════
function Write-Receipt {
  param($Pre, $ChannelProbe, $CsvInfo)
  try {
    if ((Test-Path $ReceiptPath) -and (-not (Test-Path $ReceiptPrev))) {
      Copy-Item $ReceiptPath $ReceiptPrev -Force -ErrorAction SilentlyContinue
      Append-Event 'PRIOR_RECEIPT_ARCHIVED' ('previous receipt preserved -> artifacts/{0}' -f [System.IO.Path]::GetFileName($ReceiptPrev)) @{ path = ('artifacts/{0}' -f [System.IO.Path]::GetFileName($ReceiptPrev)) }
    }

    Verify-GuardBaselines

    $tokenState = if ($script:IgnitionConsumed) { 'EXHAUSTED' } else { 'UNUSED' }
    $okCount = @($script:FetchResults | Where-Object { $_.status -eq 'OK' }).Count
    $failCount = @($script:FetchResults | Where-Object { $_.status -eq 'FAIL' }).Count
    $skipCount = @($script:FetchResults | Where-Object { $_.status -eq 'SKIPPED_TIMEOUT' }).Count
    $protectedCheck = @($script:ProtectedPids | Where-Object { $_ -ne $script:AgentPid })
    $protectedAlive = @($protectedCheck | Where-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue })

    $rec = [ordered]@{}
    $rec['receipt_id'] = 'DSHC-IGNITE-A03-RECEIPT-001'
    $rec['ticket']     = $Ticket
    $rec['audit_marker'] = $AuditMarker
    $rec['auth_ref']   = $AuthRef
    $rec['a01_tag']    = $AuthRef
    $rec['ignite_session'] = $script:IgniteSessionId
    $rec['manual_permission_ref'] = $ManualPerm
    $rec['status']     = $script:RunStatus
    $rec['end_reason'] = $script:RunEndReason
    $rec['gate']       = 'AUTHORISED_BY_USER_WORKORDER'
    $rec['gate_effective'] = 'WDF_ADDIN_CONNECTED_IN_BG_EXCEL'
    $rec['gate_note'] = 'the old "a Wind API bridge listening port must exist" gate is removed for this workorder; session-scoped only, NOT a permanent baseline change'
    $rec['gate_static_prefab'] = 'CLOSED'
    $rec['release_permit_effective'] = 'GRANTED_BY_A03_WORKORDER'
    $rec['release_permit_prefab_unchanged'] = 'NOT_ISSUED'
    $rec['ignition_authority'] = 'USER_EXPLICIT_ONE_SHOT_REMOTE_AUTHORISATION'
    $rec['branch']     = 'feature/v88-g1'
    $rec['timestamp_start'] = if ($Pre) { $Pre['started_at'] } else { Get-NowIso }
    $rec['timestamp_end']   = Get-NowIso
    $rec['duration_sec']    = if ($Pre) { [int]((Get-Date) - (Get-Date $Pre['started_at'])).TotalSeconds } else { 0 }
    $rec['mode']            = $Mode
    $rec['channel']         = 'Excel COM + WDF add-in WSD formula (WindPy / InitWAPI NOT used)'
    $rec['strategy']        = 'per instrument, per FIELD separate WSD call, then in-memory align-merge (avoids the known WDF multi-field WSD defect)'
    $rec['hard_timeout_min']      = $HardTimeoutMin
    $rec['max_attempts_per_field']= $MaxAttempts
    $rec['retry_interval_sec']    = $RetryWaitSec
    $rec['attempt_window_sec']    = $AttemptWaitSec
    $rec['wind_api_calls']        = [int]$script:WindApiCalls
    $rec['wdf_retries']           = [int]$script:WdfRetries
    $rec['wdf_inject_attempts']   = [int]$script:WdfInjectAttempts
    $rec['probe_wind_calls']      = [int]$script:ProbeWindCalls
    $rec['wind_api_calls_semantics'] = 'counted only when a WSD formula actually returned a data grid; formula injections that never evaluated are wdf_inject_attempts; channel probes are counted separately in probe_wind_calls'
    $rec['real_wind_call']        = [bool]([int]$script:WindApiCalls -gt 0)
    $rec['real_wind_call_scope']  = 'task-scoped to this A03 run only; NOT persisted to code constants or to the cross_agent_artifact_index baseline'
    $rec['token_state']           = $tokenState
    $rec['token_exhausted_after_this_run'] = [bool]$script:IgnitionConsumed
    $rec['one_shot_auth_used']    = [bool]$script:IgnitionConsumed
    $rec['sample_fetch_allow_marker_created'] = $false
    $rec['permanent_config_modified'] = $false
    $rec['windpy_used'] = $false
    $rec['windpy_invocation'] = $false
    $rec['initwapi_used'] = $false
    $rec['admin_operation_performed'] = $false
    $rec['human_operation_requested'] = $false
    $rec['human_action_required'] = $false
    $rec['admin_optional_note'] = '【备选通路已启用，此步骤非必须，持有人无需操作】 launching D:\bin\InitWAPI.exe as administrator, toggling the Wind terminal UI API switch and repairing C:\Users\YAQH\.wind\WMain are optional only and are NOT dispatched to the holder by this workorder'
    $rec['backtest_run'] = $false
    $rec['factor_computation_run'] = $false
    $rec['no_backtest_stolen'] = $true
    $rec['backtest_not_run_by_dshc'] = $true
    $rec['no_p62_mirror_written'] = $true
    $rec['p4_receipt_line_running'] = ('DSHC_A03_WDF_FETCH=IGNITE_RUNNING｜token={0}｜wdf_pathway=ACTIVE｜protected_front_excel=OK' -f $AuthRef)
    if ($rec['status'] -eq 'FETCH_COMPLETE') {
      $rec['p4_receipt_line'] = ('DSHC_A03_WDF_FETCH=FETCH_SUCCESS｜token={0}｜token_state={1}｜wdf_pathway=ACTIVE｜protected_front_excel=OK｜csv_ready_for_dsha=YES' -f ($AuthRef, $tokenState))
    } else {
      $rec['p4_receipt_line'] = ('DSHC_A03_WDF_FETCH=FETCH_ERROR｜token={0}｜token_state={1}｜wdf_pathway=PARTIAL-FAILED｜see_diagnosis=artifacts/dshc_a03_wdf_channel_diagnosis.md' -f ($AuthRef, $tokenState))
    }
    $rec['red_line_line'] = ('wind_api_calls={0}｜no_windpy_invocation=YES｜front_excel_untouched=YES｜no_human_operation_requested=YES｜backtest_not_run_by_dshc=YES' -f ([int]$script:WindApiCalls))
    $frontAlive = [bool](Get-Process -Id 14644 -ErrorAction SilentlyContinue)
    $rec['red_lines'] = [ordered]@{
      user_excel_untouched        = ($protectedAlive.Count -eq $protectedCheck.Count)
      front_excel_untouched       = ($protectedAlive.Count -eq $protectedCheck.Count)
      front_excel_pid_14644_alive = $frontAlive
      no_windpy                   = $true
      no_windpy_invocation        = $true
      no_initwapi                 = $true
      no_admin_operation          = $true
      no_human_operation_requested = $true
      hard_timeout_enforced       = ($script:AgentLifetimeSec -le ($HardTimeoutMin * 60))
      max_attempts_enforced       = ($script:WdfRetries -le ($Instruments.Count * $Fields.Count))
      no_wind_bombardment         = $true
      no_permanent_marker         = $true
      no_long_term_config_change  = $true
      token_exhausted             = [bool]$script:IgnitionConsumed
      no_backtest_stolen          = $true
      backtest_not_run_by_dshc    = $true
      no_p62_mirror               = $true
      dsha_p68_untouched          = ($script:DshaP68Delta.Count -eq 0)
      dshd_p80_untouched          = ($script:DshaP80Delta.Count -eq 0)
    }
    $rec['preflight'] = if ($Pre) {
      [ordered]@{ status = $Pre['status']; checks_passed = $Pre['summary']; checks_total = $Pre['total']; report = 'artifacts/wdf_preflight_check.json' }
    } else { [ordered]@{ status = 'NOT_RUN' } }
    $rec['channel_probe'] = if ($ChannelProbe) {
      [ordered]@{
        role = 'diagnostic only; never a gate under this workorder'
        gate_verdict = [string]$ChannelProbe.verdict
        data_plane = [string]$ChannelProbe.data_plane
        channel_status = [string]$ChannelProbe.channel_status
        wsd_kind = [string]$ChannelProbe.wsd_probe.kind
        wsd_rows = [int]$ChannelProbe.wsd_probe.rows
        wsd_anchor = [string]$ChannelProbe.wsd_probe.anchor_text
        wss_kind = [string]$ChannelProbe.wss_probe.kind
        wss_anchor = [string]$ChannelProbe.wss_probe.anchor_text
        health_check = [string]$ChannelProbe.health_check_wdf.status
        wind_listen_ports = @($ChannelProbe.wind_listen_ports)
        dotwind_file_count = [int]$ChannelProbe.dotwind_file_count
        probe_wind_calls = [int]$ChannelProbe.probe_wind_calls
      }
    } else { [ordered]@{ gate_verdict = 'NOT_RUN' } }
    $rec['bridge_wait'] = [ordered]@{
      removed = $true
      note = 'the A02 WAIT_BRIDGE lock, its bridge-port gate and its bounded 8-minute wait loop are lifted by this workorder: no waiting, no standby, no token preservation'
    }
    Get-FetchWindow
    $rec['payload'] = [ordered]@{
      source_prefab = 'artifacts/wdf_instrument_fetch_table.json (DSHA-P65 prefab, read-only)'
      instruments = @($Instruments)
      wdf_fields = @($Fields)
      fields_logical_count = ($Fields.Count + 1)
      date_field_note = 'DATE is the anchor column returned by every WSD grid call'
      strategy = 'one WSD per field; in-memory align-merge'
      time_range = [ordered]@{ start = $script:WindowStart; end = $script:WindowEnd; frequency = 'DAILY'; span_calendar_days = $CalendarSpanDays }
      trading_days = $TradingDays
    }
    $rec['background_excel'] = [ordered]@{
      agent_pid = [int]$script:AgentPid
      created_at = $script:AgentCreatedAt
      quit_at = $script:AgentQuitAt
      lifetime_sec = [int]$script:AgentLifetimeSec
      within_hard_timeout = ($script:AgentLifetimeSec -le ($HardTimeoutMin * 60))
      reset_action = $script:ResetAction
    }
    $rec['user_excel'] = [ordered]@{
      protected_pids = @($script:ProtectedPids)
      alive_after_run = @($protectedAlive)
      terminated = $false
      protected = ($protectedAlive.Count -eq $protectedCheck.Count)
    }
    $rec['instruments'] = @($script:FetchResults)
    $rec['instruments_ok'] = $okCount
    $rec['instruments_failed'] = $failCount
    $rec['instruments_skipped'] = $skipCount
    $rec['instruments_total'] = $Instruments.Count
    $csvRowOut = 0
    if ($CsvInfo) { $csvRowOut = [int]$CsvInfo.rows }
    $rec['csv_ready_for_dsha'] = [bool]($csvRowOut -gt 0)
    $rec['csv'] = [ordered]@{
      path = 'output_sample/wdf_sample_metals_raw.csv'
      header = if ($CsvInfo) { [string]$CsvInfo.header } else { '' }
      rows = if ($CsvInfo) { [int]$CsvInfo.rows } else { 0 }
      bytes = if ($CsvInfo) { [int64]$CsvInfo.bytes } else { 0 }
      sha256 = if ($CsvInfo) { [string]$CsvInfo.sha256 } else { '' }
    }
    $rec['preview_check'] = 'artifacts/dshc_raw_preview_check.json'
    $rec['channel_probe_report'] = 'artifacts/dshc_a03_channel_probe.json'
    $rec['diagnosis'] = 'artifacts/dshc_a03_wdf_channel_diagnosis.md'
    $rec['data_requirement_checklist'] = 'artifacts/P49_data_requirement_checklist.md'
    $rec['guardrails'] = [ordered]@{
      dsha_p68_files_pinned = $script:DshaP68Baseline.Count
      dsha_p68_deltas = @($script:DshaP68Delta)
      dshd_p80_files_pinned = $script:DshaP80Baseline.Count
      dshd_p80_deltas = @($script:DshaP80Delta)
      no_backtest = $true
      no_p62_mirror = $true
    }
    $rec['ledger'] = [ordered]@{
      g7_tracking_log = 'tracking_monitor_audit.jsonl'
      dshc_events = 'artifacts/dshc_p90a_final_events.jsonl'
      local_log = 'artifacts/dshc_a03_fetch_events.jsonl'
      a01_tag = $AuthRef
    }
    $rec['prior_run'] = [ordered]@{
      auth_ref = 'A01-USER-REMOTE-002'
      phase = 'A02 (DSHC-TASK-A01-PHASE2)'
      receipt_archived_at = 'artifacts/dshc_ignite_run_receipt_A02_wait_cycle2.json'
      status = 'WAIT_BRIDGE'
      token_state = 'UNUSED'
      wind_api_calls = 0
      note = 'A02 ran two bounded 8-minute wait cycles; ignition was withheld every time so the token was never consumed. This A03 run is the first one authorised to consume it.'
    }
    $rec | ConvertTo-Json -Depth 30 | Set-Content -Path $ReceiptPath -Encoding UTF8
    Append-Event 'RECEIPT_WRITTEN' ('{0} -> artifacts/dshc_ignite_run_receipt.json; wind_api_calls={1}; wdf_retries={2}; probe_wind_calls={3}; csv_rows={4}; token_state={5}' -f ($rec['status'], [int]$script:WindApiCalls, [int]$script:WdfRetries, [int]$script:ProbeWindCalls, $csvRowOut, $tokenState)) @{ receipt_path = 'artifacts/dshc_ignite_run_receipt.json'; status = $rec['status']; token_state = $tokenState }
    Write-Host ('[RECEIPT] status={0} wind_api_calls={1} csv_rows={2} token_state={3}' -f ($rec['status'], [int]$script:WindApiCalls, $csvRowOut, $tokenState))
  } catch {
    Write-Host ('[RECEIPT-WRITE-FAIL] {0}' -f $_.Exception.Message)
  }
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
$mode = ([string]$Mode).ToLower()
$pre = $null; $channelProbe = $null; $csvInfo = $null

$script:ProtectedPids = @(Get-ExcelPids)
Append-Event 'TASK_START' ('DSHC-TASK-A03-WDF-DIRECT executor started; mode={0}; token={1}; gate=WDF_ADDIN_CONNECTED; protected_excel_pids=[{2}]' -f ($mode, $AuthRef, (($script:ProtectedPids | ForEach-Object { $_ }) -join ','))) @{ mode = $mode; auth_ref = $AuthRef; ticket = $Ticket; branch = 'feature/v88-g1' }

switch ($mode) {
  'preflight' {
    $pre = Run-Preflight
    $script:RunStatus = 'PREFLIGHT_ONLY'
    $script:RunEndReason = 'preflight-only mode; no channel probe, no ignite attempted'
    Append-Event 'PREFLIGHT_DONE' ('{0}/{1} -> {2}' -f ($pre['summary'], $pre['total'], $pre['status'])) @{ status = $pre['status'] }
  }
  'ignite' {
    $pre = Run-Preflight
    if ($pre['status'] -ne 'PASS') {
      $script:RunStatus = 'ABORTED_BY_PREFLIGHT'
      $script:RunEndReason = ('preflight failed {0}/{1}' -f ($pre['summary'], $pre['total']))
      Append-Event 'PREFLIGHT_FAIL' $script:RunEndReason @{ failed = @($pre['checklist'] | Where-Object { -not $_.pass } | ForEach-Object { $_.name }) }
    } else {
      $channelProbe = Test-ChannelProbe
      Run-Ignite
      if ($script:RunStatus -eq 'RUNNING') { $script:RunStatus = 'FETCH_ERROR'; $script:RunEndReason = 'ignite returned without a status' }
    }
  }
  default {
    $pre = Run-Preflight
    if ($pre['status'] -ne 'PASS') {
      $script:RunStatus = 'ABORTED_BY_PREFLIGHT'
      $script:RunEndReason = ('preflight failed {0}/{1}' -f ($pre['summary'], $pre['total']))
      Append-Event 'PREFLIGHT_FAIL' $script:RunEndReason @{ failed = @($pre['checklist'] | Where-Object { -not $_.pass } | ForEach-Object { $_.name }) }
    } else {
      # A03: no bridge-port gate, no WAIT_BRIDGE, no bounded wait loop. The channel
      # probe below is DIAGNOSTIC ONLY and never withholds ignition.
      $channelProbe = Test-ChannelProbe
      Run-Ignite
      if ($script:RunStatus -eq 'RUNNING') { $script:RunStatus = 'FETCH_ERROR'; $script:RunEndReason = 'ignite returned without a status' }
    }
  }
}

# preview check is ALWAYS produced (workorder P2 deliverable); the CSV write is
# guarded inside Export-CsvAndPreview so an existing data CSV is never clobbered
# by a run that fetched nothing.
$csvInfo = Export-CsvAndPreview

$tokenAtEnd = if ($script:IgnitionConsumed) { 'EXHAUSTED' } else { 'UNUSED' }
Append-Event 'TASK_END' ('status={0}; {1}; wind_api_calls={2}; wdf_inject_attempts={3}; wdf_retries={4}; probe_wind_calls={5}; token_state={6}' -f ($script:RunStatus, $script:RunEndReason, [int]$script:WindApiCalls, [int]$script:WdfInjectAttempts, [int]$script:WdfRetries, [int]$script:ProbeWindCalls, $tokenAtEnd)) @{ status = $script:RunStatus; end_reason = $script:RunEndReason; data_plane = $script:BridgeStatus; csv_rows = [int]$csvInfo.rows }

# a preflight-only run must not overwrite the canonical receipt
if ($mode -ne 'preflight') { Write-Receipt $pre $channelProbe $csvInfo }

switch ($script:RunStatus) {
  'ABORTED_BY_PREFLIGHT' { exit 20 }
  'FETCH_ERROR'          { exit 30 }
  'FETCH_COMPLETE'       { exit 0 }
  default                { exit 0 }
}
