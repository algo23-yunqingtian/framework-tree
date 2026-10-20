#Requires -Version 5.1
<#
SKILL-WIND-EXCEL-WDF-BOOTSTRAP / health_check_wdf.ps1

Lightweight health check for the WDF bootstrap skill folder.
This restored entrypoint is intentionally safe:
  - no Wind data calls
  - no marker creation
  - no Excel launch
#>
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$skillDir = $PSScriptRoot
$files = @('bootstrap_wdf.ps1','reset_wdf_safe.ps1','health_check_wdf.ps1','skill_manifest.json','skill_readme.md')
$present = @()
foreach ($f in $files) { if (Test-Path (Join-Path $skillDir $f)) { $present += $f } }

$result = [ordered]@{
  skill_dir = $skillDir
  present = $present
  missing = @($files | Where-Object { $_ -notin $present })
  wind_calls = 0
  status = if (@($files | Where-Object { $_ -notin $present }).Count -eq 0) { 'OK' } else { 'INCOMPLETE' }
}
$result | ConvertTo-Json -Depth 20
exit 0
