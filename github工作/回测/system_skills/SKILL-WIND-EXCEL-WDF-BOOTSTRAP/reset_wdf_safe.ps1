#Requires -Version 5.1
<#
SKILL-WIND-EXCEL-WDF-BOOTSTRAP / reset_wdf_safe.ps1

Safe reset helper for the WDF/Excel controller test chain.
The script is intentionally conservative:
  - does not touch wmain or InitWAPI
  - does not broad-kill Excel by process name
  - only acts on an explicit agent PID marker, if present
  - never creates markers or fires Wind data requests
#>
param(
  [switch]$StopExcel,
  [string]$Root = (Split-Path $PSScriptRoot -Parent),
  [string]$AgentMarkerPath = ''
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

if ([string]::IsNullOrWhiteSpace($AgentMarkerPath)) {
  $Artifacts = Join-Path $Root 'artifacts'
  $AgentMarkerPath = Join-Path $Artifacts 'agent_excel_pid.json'
}

$result = [ordered]@{
  script = 'system_skills/SKILL-WIND-EXCEL-WDF-BOOTSTRAP/reset_wdf_safe.ps1'
  requested_stop_excel = [bool]$StopExcel.IsPresent
  wind_calls = 0
  status = 'OK'
  note = 'Safe reset smoke entrypoint.'
}

if (Test-Path $AgentMarkerPath) {
  try {
    $marker = Get-Content $AgentMarkerPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $agentPid = $null
    if ($marker.PSObject.Properties.Name -contains 'pid') { $agentPid = [int]$marker.pid }
    elseif ($marker.PSObject.Properties.Name -contains 'agent_excel_pids') {
      $agentPid = [int]($marker.agent_excel_pids | Select-Object -First 1)
    }
    if ($agentPid) {
      $proc = Get-Process -Id $agentPid -ErrorAction SilentlyContinue
      if ($proc -and $proc.ProcessName -eq 'EXCEL') {
        if ([bool]$StopExcel.IsPresent) {
          $proc | Stop-Process -Force -ErrorAction SilentlyContinue
        }
        $result['action'] = 'AGENT_PID_TARGETED'
        $result['pid'] = $agentPid
      }
    }
  } catch {
    $result['action'] = 'MARKER_PARSE_SKIPPED'
    $result['error'] = $_.Exception.Message
  }
  if (Test-Path $AgentMarkerPath) {
    Remove-Item $AgentMarkerPath -Force -ErrorAction SilentlyContinue
    $result['marker_cleared'] = $true
  }
} else {
  $result['action'] = 'NO_AGENT_MARKER'
  $result['note'] = 'No agent marker present; no Excel process was targeted.'
}

$result | ConvertTo-Json -Depth 20
exit 0
