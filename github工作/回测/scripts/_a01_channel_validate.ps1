# A01 channel validation: one WSD call via Application.Evaluate to confirm the WDF
# add-in returns a real data grid. One isolated background Excel, foreground Excel untouched.
$before = @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)
Write-Host ('EXCEL_BEFORE=[' + ($before -join ',') + ']')

$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
$wb = $xl.Workbooks.Add()
$t1 = Get-Date
Write-Host ('AGENT_PID=' + (@((Get-Process EXCEL -ErrorAction SilentlyContinue | Where-Object { $_.Id -notin $before }).Id) -join ','))

$expr = 'WSD("CU.SHF","CLOSE;VOL;OI;SETTLE","2025-01-01","2026-10-17", "Fill=Previous")'
Write-Host ('EXPR=' + $expr)
Write-Host '--- Evaluate ---'
$res = $null
try {
  $res = $xl.Evaluate($expr)
  $el = [int]((Get-Date) - $t1).TotalMilliseconds
  Write-Host ('EVAL_OK elapsed_ms=' + $el + ' type=' + $res.GetType().Name)
} catch {
  Write-Host ('EVAL_ERR=' + $_.Exception.Message)
}

if ($null -ne $res -and $res -is [System.Array]) {
  if ($res.Rank -ge 2) {
    $rows = [int]$res.GetLength(0); $cols = [int]$res.GetLength(1)
    Write-Host ('GRID=' + $rows + 'x' + $cols)
    $maxr = [Math]::Min(5, $rows); $maxe = [Math]::Min(5, $rows)
    for ($r = 0; $r -lt $maxr; $r++) {
      $out = ''
      for ($c = 0; $c -lt $cols; $c++) { $out += '  [' + ([string]$res.GetValue($r, $c)) + ']' }
      Write-Host ('  r' + $r + ':' + $out)
    }
    if ($rows -gt 5) { Write-Host ('  ... (' + ($rows - 5) + ' more rows)') }
  } else {
    Write-Host ('FLAT len=' + $res.Length)
    $show = @($res | Select-Object -First 6)
    Write-Host ('  first6=[' + (($show | ForEach-Object { [string]$_ }) -join ' | ') + ']')
  }
} elseif ($null -ne $res) {
  Write-Host ('SCALAR=[' + ([string]$res) + ']')
}

# cleanup
$wbc = [int]$xl.Workbooks.Count
for ($i = 1; $i -le $wbc; $i++) { try { $xl.Workbooks.Item($i).Close($false) | Out-Null } catch { } }
try { $xl.Quit() | Out-Null } catch { Write-Host ('QUIT_ERR=' + $_.Exception.Message) }
try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null } catch { }
[GC]::Collect(); [GC]::WaitForPendingFinalizers(); [GC]::Collect()
Start-Sleep -Seconds 3
$after = @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)
Write-Host ('EXCEL_AFTER=[' + ($after -join ',') + ']')
Write-Host ('PROTECTED_14644_ALIVE=' + [bool](Get-Process -Id 14644 -ErrorAction SilentlyContinue))
