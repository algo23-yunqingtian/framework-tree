# p81_safe_edit.ps1 - PowerShell wrapper for p81_safe_edit.py
# =====================================================================
# DSHD-P81-GIT-SAVE-TOKEN
# Thin wrapper so PS-native agents don't have to remember the Python CLI.
#
# Usage:
#   .\p81_safe_edit.ps1 snapshot recreate_p81.py -Agent DSHD-P81 -Reason 'pre-edit tweak'
#   .\p81_safe_edit.ps1 restore  dshd_p81_watch.ps1 -From recreate_p81.py.20261019_132000.DSHD-P81
#   .\p81_safe_edit.ps1 list     [-File recreate_p81.py]
#   .\p81_safe_edit.ps1 check    recreate_p81.py dshd_p81_watch.ps1
#   .\p81_safe_edit.ps1 history  [-File recreate_p81.py]
#
# The Python script is the source of truth.  This wrapper only re-dispatches.
# =====================================================================

param(
    [Parameter(Position=0, Mandatory=$true)]
    [ValidateSet('snapshot','restore','list','check','history')]
    [string]$Action,

    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$Args_,

    [string]$Agent = 'DSHD-P81',
    [string]$Reason = '',
    [string]$From = '',
    [string]$File = '',
    [switch]$Ledger
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$py   = Join-Path $here 'p81_safe_edit.py'

if (-not (Test-Path $py)) {
    Write-Error "p81_safe_edit.py not found at $py"
    exit 2
}

$pyArgs = @($Action)

switch ($Action) {
    'snapshot' {
        foreach ($f in $Args_) { $pyArgs += $f }
        if ($Agent  -ne '') { $pyArgs += '--agent'; $pyArgs += $Agent }
        if ($Reason -ne '') { $pyArgs += '--reason'; $pyArgs += $Reason }
        if ($Ledger)        { $pyArgs += '--ledger' }
    }
    'restore' {
        if ($Args_.Count -lt 1) { Write-Error "restore requires <file> as first positional arg"; exit 2 }
        $pyArgs += $Args_[0]
        if ($From -eq '')       { Write-Error "restore requires -From SNAPSHOT_ID"; exit 2 }
        $pyArgs += '--from'; $pyArgs += $From
        if ($Agent  -ne '') { $pyArgs += '--agent'; $pyArgs += $Agent }
        if ($Reason -ne '') { $pyArgs += '--reason'; $pyArgs += $Reason }
        if ($Ledger)        { $pyArgs += '--ledger' }
    }
    'list' {
        if ($Args_.Count -gt 0) { $pyArgs += $Args_[0] }
        elseif ($File -ne '')   { $pyArgs += $File }
    }
    'check' {
        if ($Args_.Count -eq 0 -and $File -ne '') { $pyArgs += $File }
        else { foreach ($f in $Args_) { $pyArgs += $f } }
    }
    'history' {
        if ($Args_.Count -gt 0) { $pyArgs += $Args_[0] }
        elseif ($File -ne '')   { $pyArgs += $File }
    }
}

# Execute python and return the exit code.
& python @pyArgs
$exitCode = $LASTEXITCODE
exit $exitCode
