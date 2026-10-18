# Validates the executor's exact code path (FormulaArray -> Calculate -> CurrentArray -> Text).
# Uses only NON-Wind formulas, so zero Wind data calls are made.
$before = @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
$wb = $xl.Workbooks.Add()
$ws = $wb.Worksheets.Item(1)

Write-Host '--- TEST0: Worksheets.Add (no args) for fresh-sheet-per-instrument ---'
try {
  $n = [int]$wb.Worksheets.Count
  $newWs = $wb.Worksheets.Add()
  $n2 = [int]$wb.Worksheets.Count
  Write-Host ('  OK: sheets ' + $n + ' -> ' + $n2)
} catch {
  Write-Host ('  FAIL: ' + $_.Exception.Message)
}

function Test-Anchor($rngAddr, [string]$formula, [string]$lbl) {
  Write-Host ('--- ' + $lbl + ' ---')
  try { $ws.Cells.Clear() | Out-Null } catch { Write-Host ('  CLEAR_ERR=' + $_.Exception.Message) }
  $anchor = $ws.Range($rngAddr)
  try { $anchor.FormulaArray = $formula; Write-Host '  FormulaArray set OK' }
  catch { Write-Host ('  FORMULA_ERR=' + $_.Exception.Message) }
  try { $xl.Calculate() | Out-Null; Write-Host '  Calculate OK' }
  catch { Write-Host ('  CALC_ERR=' + $_.Exception.Message) }
  $rr = 0; $cc = 0
  try { $arr = $anchor.CurrentArray; $rr = [int]$arr.Rows.Count; $cc = [int]$arr.Columns.Count }
  catch { Write-Host ('  CURARRAY_ERR=' + $_.Exception.Message) }
  Write-Host ('  CurrentArray rows=' + $rr + ' cols=' + $cc)
  try { Write-Host ('  anchor.Text=[' + ([string]$anchor.Text) + ']') }
  catch { Write-Host ('  TEXT_ERR=' + $_.Exception.Message) }
  if ($rr -ge 1 -and $cc -ge 1) {
    $v2 = $null
    try { $v2 = $arr.Value2 } catch { Write-Host ('  VALUE2_ERR=' + $_.Exception.Message) }
    for ($r = 1; $r -le $rr; $r++) {
      $out = ''
      for ($c = 1; $c -le $cc; $c++) {
        $t = ''
        try { $t = [string]$ws.Cells.Item($r, $c).Text } catch { $t = '<read_err>' }
        $out += '  [' + $t + ']'
      }
      Write-Host ('  r' + $r + ':' + $out)
    }
  }
}

Test-Anchor 'A1' '={1,2,3;4,5,6}' 'TEST1: 2x3 constant array (mimics WSD grid)'
Test-Anchor 'A1' '=TRANSPOSE({1;2;3;4;5})' 'TEST2: transpose 5x1 -> 1x5'
Test-Anchor 'A1' '=SUM(1,2,3)' 'TEST3: scalar formula'
Test-Anchor 'A1' '=1/0' 'TEST4: divide by zero -> expect #DIV/0!'
Test-Anchor 'A1' '=TOTALLY_BOGUS_FN("X")' 'TEST5: unknown function -> expect #NAME?'

# cleanup
$wbc = [int]$xl.Workbooks.Count
for ($i = 1; $i -le $wbc; $i++) { try { $xl.Workbooks.Item($i).Close($false) | Out-Null } catch { } }
try { $xl.Quit() | Out-Null } catch { Write-Host ('QUIT_ERR=' + $_.Exception.Message) }
try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null } catch { }
[GC]::Collect(); [GC]::WaitForPendingFinalizers(); [GC]::Collect()
Start-Sleep -Seconds 3
$after = @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)
Write-Host ('EXCEL_ADDED=[' + (@($after | Where-Object { $_ -notin $before }) -join ',') + ']')
Write-Host ('PROTECTED_14644_ALIVE=' + [bool](Get-Process -Id 14644 -ErrorAction SilentlyContinue))
