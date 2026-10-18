#Requires -Version 5.1
<#
DSHC-IGNITE-A01 · hard-timeout watchdog
Enforces the 12-minute maximum background-Excel lifetime mandated by
DSHC-IGNITE-A01-AUTH. If the agent Excel is still alive past the deadline,
the watchdog runs reset_wdf_safe.ps1 -StopExcel, which only ever terminates
the PID recorded in the transient agent PID marker. The protected foreground
user Excel PIDs are verified alive and excluded before anything is stopped.
This watchdog never creates sample_fetch_allow.marker and never fires Wind calls.
#>
param(
  [string]$Root = 'D:\DSH_WORK\github工作\回测',
  [int]$HardTimeoutMin = 12
)
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
$Root        = (Resolve-Path $Root).Path
$Artifacts   = Join-Path $Root 'artifacts'
$Marker      = Join-Path $Artifacts 'agent_excel_pid.json'
$ResetPath   = Join-Path $Root 'system_skills\SKILL-WIND-EXCEL-WDF-BOOTSTRAP\reset_wdf_safe.ps1'
$TrackingLog = Join-Path $Root 'tracking_monitor_audit.jsonl'
$DshcEvents  = Join-Path $Artifacts 'dshc_p90a_final_events.jsonl'
$LocalLog    = Join-Path $Artifacts 'dshc_ignite_a01_events.jsonl'

function Emit {
  param([string]$Type, [string]$Message, [hashtable]$Extra = @{})
  $ts = (Get-Date).ToString('o')
  $e = [ordered]@{}
  $e['timestamp'] = $ts; $e['captured_at'] = $ts
  $e['agent'] = 'DSHC-IGNITE-A01-WATCHDOG'; $e['auth_ref'] = 'A01-USER-REMOTE-001'
  $e['event_type'] = $Type; $e['wind_api_calls'] = 0; $e['real_wind_call'] = $false
  $e['message'] = $Message
  if ($Extra.Count -gt 0) { foreach ($k in $Extra.Keys) { $e[$k] = $Extra[$k] } }
  $line = $e | ConvertTo-Json -Depth 10 -Compress
  foreach ($p in @($TrackingLog, $DshcEvents, $LocalLog)) {
    try { Add-Content -Path $p -Value $line -Encoding UTF8 } catch { }
  }
  Write-Host ("[{0}] {1} :: {2}" -f $ts.Substring(11, 12), $Type, $Message)
}

# protected foreground Excel PIDs = every Excel present BEFORE the marker is written
$protectedPids = @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)

Emit 'WATCHDOG_ARMED' ("hard timeout {0}min armed; protected foreground Excel pids=[{1}]" -f $HardTimeoutMin, ($protectedPids -join ',')) @{ protected_excel_pids = $protectedPids; hard_timeout_min = $HardTimeoutMin }

$deadline = $null
while ($null -eq $deadline) {
  if (Test-Path $Marker) {
    try {
      $m = Get-Content $Marker -Raw -Encoding UTF8 | ConvertFrom-Json
      if ($m -and ($m.PSObject.Properties.Name -contains 'created_at')) {
        $deadline = (Get-Date [string]$m.created_at).AddMinutes($HardTimeoutMin)
        break
      }
    } catch { }
  }
  Start-Sleep -Seconds 5
}

$waitSec = [int]($deadline - (Get-Date)).TotalSeconds
Emit 'WATCHDOG_DEADLINE' ("deadline={0} ({1}s from now)" -f $deadline.ToString('o'), $waitSec) @{ deadline = $deadline.ToString('o') }
if ($waitSec -gt 0) { Start-Sleep -Seconds $waitSec }

Emit 'HARD_TIMEOUT_REACHED' "12-minute background-Excel lifetime budget exhausted; checking agent Excel" @{ hard_timeout_min = $HardTimeoutMin }

$agentPid = 0; $agentAlive = $false
try {
  if (Test-Path $Marker) {
    $m = Get-Content $Marker -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($m.PSObject.Properties.Name -contains 'pid') { $agentPid = [int]$m.pid }
    elseif ($m.PSObject.Properties.Name -contains 'agent_excel_pids') { $agentPid = [int]($m.agent_excel_pids | Select-Object -First 1) }
  }
} catch { }

if ($agentPid -gt 0) {
  $proc = Get-Process -Id $agentPid -ErrorAction SilentlyContinue
  $agentAlive = ($null -ne $proc)
}

if (-not $agentAlive) {
  Emit 'HARD_TIMEOUT_NO_ACTION' ("agent Excel pid={0} already exited; nothing to kill; protected foreground pids=[{1}] untouched" -f $agentPid, ($protectedPids -join ',')) @{ agent_excel_pid = $agentPid; action_taken = $false }
} elseif ($agentPid -in $protectedPids) {
  Emit 'HARD_TIMEOUT_ABORT_UNSAFE' ("REFUSING to kill pid={0}: it is a protected foreground Excel pid, not the agent" -f $agentPid) @{ agent_excel_pid = $agentPid; action_taken = $false; reason = 'PROTECTED_PID' }
} else {
  $resetOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $ResetPath -Root $Root -StopExcel -AgentMarkerPath $Marker | Out-String
  Start-Sleep -Seconds 3
  $stillAlive = [bool](Get-Process -Id $agentPid -ErrorAction SilentlyContinue)
  $protectedAfter = @($protectedPids | Where-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue })
  Emit 'HARD_TIMEOUT_RESET_FORCED' ("agent Excel pid={0} force-reset via reset_wdf_safe.ps1; still_alive={1}; protected foreground alive=[{2}]" -f $agentPid, $stillAlive, ($protectedAfter -join ',')) @{ agent_excel_pid = $agentPid; still_alive = $stillAlive; reset_output = $resetOut; protected_excel_alive = $protectedAfter }
}

$markerCleared = -not (Test-Path $Marker)
Emit 'WATCHDOG_DONE' ("watchdog finished; marker_cleared={0}" -f $markerCleared) @{ marker_cleared = $markerCleared }
exit 0
