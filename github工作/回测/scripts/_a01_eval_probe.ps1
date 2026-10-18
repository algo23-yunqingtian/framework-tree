# Diagnostic: can Eval / ExecuteExcel4Macro return a full array from a single expression?
$before = @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
$wb = $xl.Workbooks.Add()
$ws = $wb.Worksheets.Item(1)
try { $xl.WorkbookBuildImmediate = $false } catch { }

function Show-Grid([string]$lbl, $grid) {
  Write-Host ('  ' + $lbl + ' -> type=' + $grid.GetType().Name)
  if ($null -eq $grid) { return }
  if ($grid -is [System.Array]) {
    $rd = $grid.Rank
    if ($rd -ge 2) {
      $rows = $grid.GetLength(0); $cols = $grid.GetLength(1)
      Write-Host ('    dim=' + $rd + ' ' + $rows + 'x' + $cols)
      for ($r = 0; $r -lt $rows -and $r -lt 5; $r++) {
        $out = ''
        for ($c = 0; $c -lt $cols; $c++) { $out += ' [' + ([string]$grid.GetValue($r, $c)) + ']' }
        Write-Host ('    r' + $r + ':' + $out)
      }
    } else {
      Write-Host ('    len=' + $grid.Length + ' :: ' + (($grid | ForEach-Object { [string]$_ }) -join '; '))
    }
  } else {
    Write-Host ('    scalar=[' + ([string]$grid) + ']')
  }
}

Write-Host '=== 1. Eval with a multi-cell array formula ==='
foreach ($f in @('TRANSPOSE({1;2;3;4;5})', 'SUM(1:1)', 'RAND()', 'A1')) {
  try { Show-Grid ('Eval[' + $f + ']' ) $xl.Eval($f) }
  catch { Write-Host ('  Eval[' + $f + '] ERR=' + $_.Exception.Message) }
}

Write-Host '=== 2. ExecuteExcel4Macro with {=} array form ==='
foreach ($f in @('{=TRANSPOSE({1;2;3;4;5})}', '{=SUM(1:1)}', '{=RAND()}')) {
  try { Show-Grid ('E4M[' + $f + ']') $xl.ExecuteExcel4Macro($f) }
  catch { Write-Host ('  E4M[' + $f + '] ERR=' + $_.Exception.Message) }
}

Write-Host '=== 3. Evaluate (for comparison) ==='
foreach ($f in @('TRANSPOSE({1;2;3;4;5})', 'SUM(1:1)')) {
  try { Show-Grid ('Evalua[' + $f + ']') $xl.Evaluate($f) }
  catch { Write-Host ('  Evalua[' + $f + '] ERR=' + $_.Exception.Message) }
}

Write-Host '=== 4. Two-step helper grid on a 2x3 target ==='
try { $ws.Cells.Clear() | Out-Null } catch { }
try { $ws.Range('A1:C2').Formula = '=B1' } catch { Write-Host ('  STEP1 ERR=' + $_.Exception.Message) }
$anchor = $ws.Range('B1')
try { $anchor.FormulaArray = '={1,2,3;4,5,6}' } catch { Write-Host ('  STEP2 ERR=' + $_.Exception.Message) }
try { $xl.Calculate() | Out-Null } catch { }
try {
  $g = $ws.Range('A1:C2').Value2
  Show-Grid 'helperGrid.Value2' $g
} catch { Write-Host ('  GRID ERR=' + $_.Exception.Message) }
foreach ($a in @('A1','A2','B1','B2','C1','C2')) {
  try { Write-Host ('    ' + $a + ' text=[' + ([string]$ws.Range($a).Text) + ']') } catch { }
}

Write-Host '=== 5. Does WSD exist as a named function in this workbook? ==='
try {
  $hasName = $false
  try { $nm = $xl.WorkbookNames; $hasName = $nm.Count -gt 0 } catch { }
  Write-Host ('  WorkbookNames.Count check ok (not authoritative for add-in UDFs)')
} catch { }
try { Show-Grid 'Eval[WSD(...)] shape probe' $xl.Eval('1+1') } catch { Write-Host ('  ERR=' + $_.Exception.Message) }

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
