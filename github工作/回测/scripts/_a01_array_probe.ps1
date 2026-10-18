# Diagnostic: how do array formulas actually behave in this PS 5.1 + Office 16.0 setup?
$before = @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
$wb = $xl.Workbooks.Add()
$ws = $wb.Worksheets.Item(1)
$loc = '<err>'
try { $loc = [string]$xl.LanguageSettings.Item(1).LanguageID } catch { }
Write-Host ('LOCALE=' + $loc)
Write-Host ('APPVERSION=' + $xl.Version)

function Probe($rngAddr, [string]$prop, [string]$formula, [string]$lbl) {
  try { $ws.Cells.Clear() | Out-Null } catch { }
  Start-Sleep -Milliseconds 200
  $rng = $ws.Range($rngAddr)
  try {
    if ($prop -eq 'FormulaArray') { $rng.FormulaArray = $formula } else { $rng.Formula = $formula }
    $ok = 'OK'
  } catch { $ok = ('ERR=' + $_.Exception.Message) }
  try { $xl.Calculate() | Out-Null } catch { }
  $inArr = $null; $isArr = $null; $txt = $null; $caR = 0; $caC = 0
  try { $inArr = [bool]$rng.IsInArray } catch { $inArr = '<err>' }
  try { $isArr = [bool]$rng.FormulaArray -ne $null } catch { }
  try { $txt = [string]$rng.Text } catch { }
  try { $ca = $rng.CurrentArray; $caR = [int]$ca.Rows.Count; $caC = [int]$ca.Columns.Count } catch { }
  $stored = '<n/a>'; try { $stored = [string]$rng.Formula } catch { }
  Write-Host ('  ' + $lbl + '  set=' + $prop + ' => ' + $ok)
  Write-Host ('     stored.Formula=[' + $stored + ']  IsInArray=' + $inArr + '  Text=[' + $txt + ']  CurrentArray=' + $caR + 'x' + $caC)
  if ($caR -ge 1 -and $caC -ge 1) {
    try {
      $ca = $rng.CurrentArray
      for ($r = 1; $r -le $caR; $r++) {
        $out = ''
        for ($c = 1; $c -le $caC; $c++) { $out += ' [' + ([string]$ws.Cells.Item($r, $c).Text) + ']' }
        Write-Host ('     r' + $r + ':' + $out)
      }
    } catch { }
  }
}

Write-Host '--- A: FormulaArray with = prefix on single cell ---'
Probe 'A1' 'FormulaArray' '={1,2,3;4,5,6}' 'A'
Write-Host '--- B: FormulaArray WITHOUT = prefix on single cell ---'
Probe 'A1' 'FormulaArray' '{1,2,3;4,5,6}' 'B'
Write-Host '--- C: Formula (not FormulaArray) on single cell ---'
Probe 'A1' 'Formula' '={1,2,3;4,5,6}' 'C'
Write-Host '--- D: FormulaArray over a 2x3 range target ---'
Probe 'A1:C2' 'FormulaArray' '={1,2,3;4,5,6}' 'D'
Write-Host '--- E: FormulaArray over a 2x3 range target, no = prefix ---'
Probe 'A1:C2' 'FormulaArray' '{1,2,3;4,5,6}' 'E'
Write-Host '--- F: TRANSPOSE spill with FormulaArray single cell ---'
Probe 'A1' 'FormulaArray' '=TRANSPOSE({1;2;3;4;5})' 'F'
Write-Host '--- G: RAND() to confirm volatile calc runs ---'
Probe 'A1' 'Formula' '=RAND()' 'G'

# cleanup
$wbc = [int]$xl.Workbooks.Count
for ($i = 1; $i -le $wbc; $i++) { try { $xl.Workbooks.Item($i).Close($false) | Out-Null } catch { } }
try { $xl.Quit() | Out-Null } catch { }
try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null } catch { }
[GC]::Collect(); [GC]::WaitForPendingFinalizers(); [GC]::Collect()
Start-Sleep -Seconds 3
$after = @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)
Write-Host ('EXCEL_ADDED=[' + (@($after | Where-Object { $_ -notin $before }) -join ',') + ']')
Write-Host ('PROTECTED_14644_ALIVE=' + [bool](Get-Process -Id 14644 -ErrorAction SilentlyContinue))
