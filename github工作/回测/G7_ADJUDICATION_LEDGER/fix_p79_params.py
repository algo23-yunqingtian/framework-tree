#!/usr/bin/env python3
"""Fix P79 script: define all paths at top level, pass as parameters to functions."""
import re

path = r"D:\DSH_WORK\github工作\回测\G7_ADJUDICATION_LEDGER\dshd_p79_a01_audit_watch.ps1"

with open(path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Define all paths as constants at the top (after param())
# They're already defined there. The issue is functions using Chinese char literals.
# Strategy: Replace all function-internal Chinese char paths with parameter references.

# Add parameters to Get-InvariantStatus
content = content.replace(
    'function Get-InvariantStatus {\n    $invariants = @{',
    'function Get-InvariantStatus {\n    param([string]$BaseDir, [string]$ArtifactsDir, [int]$MonitorPid)\n    $invariants = @{',
    1
)

# Replace $script:baseDir and $baseDir references inside Get-InvariantStatus
# Actually, let me just replace the garbled literal paths with parameter names
# The function currently has:
#   foreach ($m in $markers) { if (Test-Path "D:\DSH_WORK\github工作\回测\$m") { ...
#   $p77snap = "D:\DSH_WORK\github工作\回测\artifacts\dshd_p77_skillpack_watch_snapshot.json"
#   $invariants.monitor_pid3472_alive = (Test-ProcessAlive 3472)

# Replace the baseDir reference
content = content.replace(
    'if (Test-Path "D:\\DSH_WORK\\github工作\\回测\\$m")',
    'if (Test-Path "$BaseDir\\$m")',
    1
)

# Replace the P77 snapshot path
content = content.replace(
    '$p77snap = "D:\\DSH_WORK\\github工作\\回测\\artifacts\\dshd_p77_skillpack_watch_snapshot.json"',
    '$p77snap = "$ArtifactsDir\\dshd_p77_skillpack_watch_snapshot.json"',
    1
)

# Replace the monitor PID
content = content.replace(
    '$invariants.monitor_pid3472_alive = (Test-ProcessAlive 3472)',
    '$invariants.monitor_pid3472_alive = (Test-ProcessAlive $MonitorPid)',
    1
)

# Now update the call sites of Get-InvariantStatus
# Initial state call
content = content.replace(
    '$inv = Get-InvariantStatus\nWrite-Host "Initial state:"',
    '$inv = Get-InvariantStatus $baseDir $artifactsDir $monitorPid\nWrite-Host "Initial state:"',
    1
)

# In the watch loop
content = content.replace(
    '$inv = Get-InvariantStatus\n\n        # 2. A01 events',
    '$inv = Get-InvariantStatus $baseDir $artifactsDir $monitorPid\n\n        # 2. A01 events',
    1
)

# Also fix Add-AuditEvent - pass tracking log path as param
content = content.replace(
    'function Add-AuditEvent {\n    param([hashtable]$EventData)',
    'function Add-AuditEvent {\n    param([hashtable]$EventData, [string]$TrackingLogPath)',
    1
)

content = content.replace(
    '$fs = [System.IO.FileStream]::new("D:\\DSH_WORK\\github工作\\回测\\tracking_monitor_audit.jsonl", [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write)',
    '$fs = [System.IO.FileStream]::new($TrackingLogPath, [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write)',
    1
)

# Update Add-AuditEvent call sites
content = content.replace(
    'Add-AuditEvent $contextEvent',
    'Add-AuditEvent $contextEvent $trackingLog',
    1
)

# Find all other Add-AuditEvent calls and add the param
content = re.sub(r'Add-AuditEvent (\$warnEvent)', r'Add-AuditEvent \1 $trackingLog', content)

# Fix Get-RecentTrackingEvents - pass tracking log path
content = content.replace(
    'function Get-RecentTrackingEvents {\n    param([int]$Count = 100)',
    'function Get-RecentTrackingEvents {\n    param([int]$Count = 100, [string]$TrackingLogPath)',
    1
)

content = content.replace(
    'if (!(Test-Path "D:\\DSH_WORK\\github工作\\回测\\tracking_monitor_audit.jsonl")) { return @() }',
    'if (!(Test-Path $TrackingLogPath)) { return @() }',
    1
)

content = content.replace(
    '$allLines = [System.IO.File]::ReadAllLines("D:\\DSH_WORK\\github工作\\回测\\tracking_monitor_audit.jsonl", [System.Text.Encoding]::UTF8)',
    '$allLines = [System.IO.File]::ReadAllLines($TrackingLogPath, [System.Text.Encoding]::UTF8)',
    1
)

# Update Get-RecentTrackingEvents call sites
content = re.sub(r'Get-RecentTrackingEvents (\d+)', r'Get-RecentTrackingEvents \1 $trackingLog', content)

# Fix Write-SnapshotJson - pass artifacts dir
content = content.replace(
    'function Write-SnapshotJson {\n    param([hashtable]$Data, [string]$OutputPath)',
    'function Write-SnapshotJson {\n    param([hashtable]$Data, [string]$OutputPath, [string]$ArtifactsDir)',
    1
)

content = content.replace(
    '$tempJson = "D:\\DSH_WORK\\github工作\\回测\\artifacts\\.p79_snapshot_tmp.json"',
    '$tempJson = "$ArtifactsDir\\.p79_snapshot_tmp.json"',
    1
)

# Update Write-SnapshotJson call site
content = content.replace(
    'Write-SnapshotJson $snapshotData $p79SnapshotPath',
    'Write-SnapshotJson $snapshotData $p79SnapshotPath $artifactsDir',
    1
)

# Fix Write-FileEvidenceJson - pass artifacts dir
content = content.replace(
    'function Write-FileEvidenceJson {\n    param([hashtable]$Data, [string]$OutputPath)',
    'function Write-FileEvidenceJson {\n    param([hashtable]$Data, [string]$OutputPath, [string]$ArtifactsDir)',
    1
)

content = content.replace(
    '$tempJson = "D:\\DSH_WORK\\github工作\\回测\\artifacts\\.p79_evidence_tmp.json"',
    '$tempJson = "$ArtifactsDir\\.p79_evidence_tmp.json"',
    1
)

# Update Write-FileEvidenceJson call site
content = content.replace(
    'Write-FileEvidenceJson $evidenceData $p79FilePath',
    'Write-FileEvidenceJson $evidenceData $p79FilePath $artifactsDir',
    1
)

# Fix Get-OutputSampleEvidence - pass output dir
content = content.replace(
    'function Get-OutputSampleEvidence {\n    $evidence = @{',
    'function Get-OutputSampleEvidence {\n    param([string]$OutputSampleDir)\n    $evidence = @{',
    1
)

content = content.replace(
    'directory_exists = (Test-Path "D:\\DSH_WORK\\github工作\\回测\\output_sample")',
    'directory_exists = (Test-Path $OutputSampleDir)',
    1
)

content = content.replace(
    '$files = Get-ChildItem "D:\\DSH_WORK\\github工作\\回测\\output_sample" -File -ErrorAction Stop',
    '$files = Get-ChildItem $OutputSampleDir -File -ErrorAction Stop',
    1
)

# Update Get-OutputSampleEvidence call site
content = content.replace(
    '$outputEvidence = Get-OutputSampleEvidence',
    '$outputEvidence = Get-OutputSampleEvidence $outputSampleDir',
    1
)

# Fix Get-A01BacktestArtifacts - pass artifacts dir
content = content.replace(
    'function Get-A01BacktestArtifacts {\n    $artifacts = @()',
    'function Get-A01BacktestArtifacts {\n    param([string]$ArtifactsDir)\n    $artifacts = @()',
    1
)

content = content.replace(
    '$dshcFiles = Get-ChildItem "D:\\DSH_WORK\\github工作\\回测\\artifacts" -Filter "dshc_*" -File -ErrorAction SilentlyContinue',
    '$dshcFiles = Get-ChildItem $ArtifactsDir -Filter "dshc_*" -File -ErrorAction SilentlyContinue',
    1
)

# Update Get-A01BacktestArtifacts call site
content = content.replace(
    '$state.a01BacktestArtifacts = Get-A01BacktestArtifacts',
    '$state.a01BacktestArtifacts = Get-A01BacktestArtifacts $artifactsDir',
    1
)

with open(path, 'w', encoding='utf-8-sig') as f:
    f.write(content)

print(f"Fixed: {path}")
print(f"Size: {len(content)} bytes")