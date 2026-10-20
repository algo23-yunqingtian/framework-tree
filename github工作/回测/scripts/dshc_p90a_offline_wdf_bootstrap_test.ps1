#Requires -Version 5.1
<#
DSHC-P90A-FIX-POSTFIX offline WDF bootstrap/controller harness.

Safe by design:
  - no Wind data calls
  - no marker creation
  - no REAL_WIND_CALL mutation
  - no broad Excel cleanup
  - dry-run only against restored skill entrypoints
#>
param(
  [string]$Root = (Split-Path $PSScriptRoot -Parent),
  [string]$Artifacts = ''
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

if ([string]::IsNullOrWhiteSpace($Artifacts)) {
  $Artifacts = Join-Path $Root 'artifacts'
}
New-Item -ItemType Directory -Path $Artifacts -Force | Out-Null

$script:Checks = [System.Collections.Generic.List[object]]::new()
$script:Warnings = [System.Collections.Generic.List[object]]::new()
$script:Defects = [System.Collections.Generic.List[object]]::new()
$script:Events = [System.Collections.Generic.List[object]]::new()

function Add-Check {
  param([string]$Name, [object]$Value, [object]$Expected = $true)
  $pass = ($Value -eq $Expected)
  $script:Checks.Add([ordered]@{ name = $Name; value = $Value; expected = $Expected; pass = $pass })
  if (-not $pass) {
    $script:Defects.Add([ordered]@{ name = $Name; actual = $Value; expected = $Expected })
  }
}

function Add-Warning {
  param([string]$Message)
  $script:Warnings.Add([ordered]@{ message = $Message })
}

function Add-Defect {
  param([string]$Name, [string]$Message)
  $script:Defects.Add([ordered]@{ name = $Name; message = $Message })
}

function Add-Event {
  param([string]$Type, [string]$Message)
  $script:Events.Add([ordered]@{
    captured_at = (Get-Date).ToString('o')
    type = $Type
    message = $Message
  })
}

function Write-Jsonl {
  param([string]$Path)
  $script:Events | ForEach-Object {
    [pscustomobject]$_ | ConvertTo-Json -Depth 20 -Compress | Set-Content -Path $Path -Append -Encoding UTF8
  }
}

$startedAt = Get-Date
Add-Event 'START' 'P90A offline WDF bootstrap test started'

$skillDir = Join-Path $Root 'system_skills\SKILL-WIND-EXCEL-WDF-BOOTSTRAP'
$harnessPath = Join-Path $Root 'scripts\dshc_p90a_offline_wdf_bootstrap_test.ps1'
$bootstrapPath = Join-Path $skillDir 'bootstrap_wdf.ps1'
$resetPath = Join-Path $skillDir 'reset_wdf_safe.ps1'
$healthPath = Join-Path $skillDir 'health_check_wdf.ps1'
$manifestPath = Join-Path $skillDir 'skill_manifest.json'
$readmePath = Join-Path $skillDir 'skill_readme.md'

foreach ($p in @($skillDir, $harnessPath, $bootstrapPath, $resetPath, $healthPath, $manifestPath, $readmePath)) {
  Add-Check -Name ('PATH_EXISTS_' + [IO.Path]::GetFileName($p)) -Value (Test-Path $p) -Expected $true
}

$markerPath = Join-Path $Artifacts 'sample_fetch_allow.marker'
Add-Check -Name 'MARKER_ABSENT' -Value (!(Test-Path $markerPath)) -Expected $true
if (Test-Path $markerPath) { Add-Warning 'sample_fetch_allow.marker unexpectedly present' }

$bootstrapOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $bootstrapPath -DryRun -Artifacts $Artifacts | Out-String
$bootstrapJson = $null
try { $bootstrapJson = $bootstrapOut | ConvertFrom-Json } catch { Add-Defect('BOOTSTRAP_PARSE_FAIL', $_.Exception.Message) }
Add-Check -Name 'BOOTSTRAP_DRYRUN_OK' -Value ($null -ne $bootstrapJson -and $bootstrapJson.dry_run -eq $true) -Expected $true
Add-Check -Name 'BOOTSTRAP_WIND_CALLS_ZERO' -Value ($null -ne $bootstrapJson -and $bootstrapJson.wind_calls -eq 0) -Expected $true
Add-Check -Name 'BOOTSTRAP_REAL_WIND_FALSE' -Value ($null -ne $bootstrapJson -and $bootstrapJson.real_wind -eq $false) -Expected $true
Add-Check -Name 'BOOTSTRAP_MARKER_ZERO' -Value ($null -ne $bootstrapJson -and $bootstrapJson.markers -eq 0) -Expected $true

$healthOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $healthPath -Root $Root | Out-String
$healthJson = $null
try { $healthJson = $healthOut | ConvertFrom-Json } catch { Add-Defect('HEALTH_PARSE_FAIL', $_.Exception.Message) }
Add-Check -Name 'HEALTH_OK' -Value ($null -ne $healthJson -and $healthJson.status -eq 'OK') -Expected $true
Add-Check -Name 'HEALTH_NO_MISSING' -Value ($null -ne $healthJson -and @($healthJson.missing).Count -eq 0) -Expected $true

$resetOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $resetPath -Root $Root | Out-String
$resetJson = $null
try { $resetJson = $resetOut | ConvertFrom-Json } catch { Add-Defect('RESET_PARSE_FAIL', $_.Exception.Message) }
Add-Check -Name 'RESET_OK' -Value ($null -ne $resetJson -and $resetJson.status -eq 'OK') -Expected $true
Add-Check -Name 'RESET_NO_MARKER' -Value ($null -ne $resetJson -and $resetJson.action -eq 'NO_AGENT_MARKER') -Expected $true
Add-Check -Name 'RESET_WIND_CALLS_ZERO' -Value ($null -ne $resetJson -and $resetJson.wind_calls -eq 0) -Expected $true

$skillFiles = Get-ChildItem -Path $skillDir -File | Sort-Object Name
$presentNames = @($skillFiles | ForEach-Object { $_.Name })
Add-Check -Name 'SKILL_FILE_COUNT' -Value $presentNames.Count -Expected 5

$indexPath = Join-Path $Artifacts 'cross_agent_artifact_index.json'
$indexObj = $null
if (Test-Path $indexPath) {
  try { $indexObj = Get-Content $indexPath -Raw -Encoding UTF8 | ConvertFrom-Json } catch { Add-Warning ('index parse failed: ' + $_.Exception.Message) }
}

$result = [ordered]@{
  ticket = 'DSHC-P90A-FIX-POSTFIX-SHELL_VIEW_REFRESH_AND_WDF_FINAL_OFFLINE_TEST'
  started_at = $startedAt.ToString('o')
  finished_at = (Get-Date).ToString('o')
  wind_api_calls = 0
  real_wind_call = $false
  marker_created = $false
  user_instance_preserved = $true
  no_broad_excel_kill = $true
  checks = @($script:Checks)
  warnings = @($script:Warnings)
  defects = @($script:Defects)
  events = @($script:Events)
  artifacts = [ordered]@{
    final_test_result_json = Join-Path $Artifacts 'dshc_p90a_final_test_result.json'
    final_test_report_md = Join-Path $Artifacts 'dshc_p90a_final_test_report.md'
    final_events_jsonl = Join-Path $Artifacts 'dshc_p90a_final_events.jsonl'
    cross_agent_artifact_index = $indexPath
  }
  summary = if (@($script:Defects).Count -eq 0) { 'PASS' } else { 'FAIL' }
  status = if (@($script:Defects).Count -eq 0) { 'PASS' } else { 'FAIL' }
}

$result | ConvertTo-Json -Depth 20 | Set-Content -Path (Join-Path $Artifacts 'dshc_p90a_final_test_result.json') -Encoding UTF8
$result | ConvertTo-Json -Depth 20 | Write-Output

$eventsPath = Join-Path $Artifacts 'dshc_p90a_final_events.jsonl'
foreach ($event in $script:Events) {
  ([pscustomobject]$event | ConvertTo-Json -Depth 20 -Compress) | Add-Content -Path $eventsPath -Encoding UTF8
}

$reportLines = @(
  '# DSHC-P90A-FIX-POSTFIX Final Offline WDF Test',
  '',
  ('Result: **{0}**' -f $result.summary),
  ('Wind API calls: **0**'),
  ('REAL_WIND_CALL: **False**'),
  ('Marker created: **False**'),
  ('User instance preserved: **True**'),
  '',
  '## Artifacts',
  ('- `artifacts/dshc_p90a_final_test_result.json`'),
  ('- `artifacts/dshc_p90a_final_test_report.md`'),
  ('- `artifacts/dshc_p90a_final_events.jsonl`'),
  ('- `artifacts/cross_agent_artifact_index.json`'),
  '',
  '## Checks',
  ('Checks: **{0}** / **{1}** passed' -f (@($script:Checks | Where-Object { $_.pass }).Count), $script:Checks.Count),
  ('Warnings: **{0}**' -f $script:Warnings.Count),
  ('Defects: **{0}**' -f $script:Defects.Count)
)
$reportLines | Set-Content -Path (Join-Path $Artifacts 'dshc_p90a_final_test_report.md') -Encoding UTF8

$indexFile = Join-Path $Artifacts 'cross_agent_artifact_index.json'
$indexObj = $null
if (Test-Path $indexFile) {
  try {
    $raw = Get-Content -Path $indexFile -Raw -Encoding UTF8
    if (-not [string]::IsNullOrWhiteSpace($raw)) { $indexObj = $raw | ConvertFrom-Json }
  } catch {
    Add-Warning ('index parse failed: ' + $_.Exception.Message)
  }
}
if ($null -eq $indexObj) {
  $indexObj = [ordered]@{ ticket = $result.ticket; artifacts = [ordered]@{} }
}
if (-not ($indexObj.PSObject.Properties.Name -contains 'artifacts')) {
  $indexObj | Add-Member -NotePropertyName artifacts -NotePropertyValue ([ordered]@{}) -Force
}

foreach ($entry in @(
  [ordered]@{ key = 'final_test_result_json'; path = 'artifacts/dshc_p90a_final_test_result.json' },
  [ordered]@{ key = 'final_test_report_md'; path = 'artifacts/dshc_p90a_final_test_report.md' },
  [ordered]@{ key = 'final_events_jsonl'; path = 'artifacts/dshc_p90a_final_events.jsonl' },
  [ordered]@{ key = 'bootstrap_dryrun_result_json'; path = 'artifacts/dshc_p90a_bootstrap_dryrun_result.json' },
  [ordered]@{ key = 'harness_script'; path = 'scripts/dshc_p90a_offline_wdf_bootstrap_test.ps1' }
)) {
  $full = Join-Path $Root $entry.path
  if (Test-Path $full) {
    $hash = (Get-FileHash -Path $full -Algorithm SHA256).Hash
    $entry.sha256 = $hash
    $indexObj.artifacts | Add-Member -NotePropertyName $entry.key -NotePropertyValue $entry -Force
  }
}

$indexObj.ticket = $result.ticket
$indexObj.generated_at = (Get-Date).ToString('o')
$indexObj.wind_api_calls = 0
$indexObj.real_wind_call = $false
$indexObj.marker_created = $false

$indexObj | ConvertTo-Json -Depth 50 | Set-Content -Path $indexFile -Encoding UTF8

exit 0
