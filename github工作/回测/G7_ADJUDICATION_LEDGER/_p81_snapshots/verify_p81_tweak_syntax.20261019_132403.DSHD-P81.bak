$ErrorActionPreference = 'Stop'
$ErrorActionPreference = 'SilentlyContinue'
$p = Join-Path $PSScriptRoot 'dshd_p81_watch.ps1'
$src = [System.IO.File]::ReadAllText($p, [System.Text.Encoding]::UTF8)
$tok = $null
$err = $null
$ast = $null
$ast = [System.Management.Automation.Language.Parser]::ParseInput($src, [ref]$tok, [ref]$err)
Write-Host ("PARSE_ERRORS {0}" -f $err.Count)
if ($err.Count -gt 0) {
    foreach ($e in $err) {
        $ln = $e.Extent.StartLineNumber
        $col = $e.Extent.StartColumnNumber
        Write-Host ("  L{0}:{1} [{2}] {3}" -f $ln, $col, $e.CategoryInfo.Reason, $e.Message)
    }
}
Write-Host ("TOKENS {0}" -f $tok.Count)
Write-Host ("FUNCS  {0}" -f (($ast.FindAll({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst]}, $true)).Count))
$funcs = $ast.FindAll({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst]}, $true) | ForEach-Object { $_.Name } | Sort-Object
Write-Host ("NEW_FN  {0}" -f ($funcs -contains 'Get-SkillDirAudit'))
Write-Host "ALL_FNS:"
$funcs | ForEach-Object { Write-Host ("  {0}" -f $_) }
