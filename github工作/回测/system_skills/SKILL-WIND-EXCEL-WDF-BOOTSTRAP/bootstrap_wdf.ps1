#Requires -Version 5.1
<#
SKILL-WIND-EXCEL-WDF-BOOTSTRAP / bootstrap_wdf.ps1

Offline bootstrap entrypoint for the WDF/Excel controller test chain.
This restored entrypoint is intentionally safe:
  - dry-run only by default
  - no Wind data calls
  - no marker creation
  - no REAL_WIND_CALL mutation
  - no Excel launch in dry-run mode
#>
param(
  [switch]$DryRun,
  [string]$Artifacts = ''
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$Root = Split-Path $PSScriptRoot -Parent
$Artifacts = if ([string]::IsNullOrWhiteSpace($Artifacts)) { Join-Path $Root 'artifacts' } else { $Artifacts }
if (!(Test-Path $Artifacts)) { New-Item -ItemType Directory -Path $Artifacts -Force | Out-Null }

$result = [ordered]@{
  script      = 'system_skills/SKILL-WIND-EXCEL-WDF-BOOTSTRAP/bootstrap_wdf.ps1'
  dry_run     = [bool]$DryRun.IsPresent
  wind_calls  = 0
  markers     = 0
  tokens      = 0
  real_wind   = $false
  status      = 'OK'
  note        = 'Restored safe bootstrap entrypoint for P90A offline validation.'
}

if ([bool]$DryRun.IsPresent) {
  $result['action'] = 'DRY_RUN_ONLY_NO_LIVE_STARTUP'
}

$result | ConvertTo-Json -Depth 20 | Set-Content -Path (Join-Path $Artifacts 'dshc_p90a_bootstrap_dryrun_result.json') -Encoding UTF8
Write-Output (($result | ConvertTo-Json -Depth 20))
exit 0
