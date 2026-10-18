# A01 channel validation 2: WSD is async - it returns "Fetching..." then the cached result.
# Poll Application.Evaluate until the placeholder is replaced.
$before = @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)
Write-Host ('EXCEL_BEFORE=[' + ($before -join ',') + ']')

$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
$wb = $xl.Workbooks.Add()
Write-Host ('AGENT_PID=' + (@((Get-Process EXCEL -ErrorAction SilentlyContinue | Where-Object { $_.Id -notin $before }).Id) -join ','))

$expr = 'WSD("CU.SHF","CLOSE;VOL;OI;SETTLE","2025-01-01","2026-10-17", "Fill=Previous")'
$first = Get-Date
$deadline = (Get-Date).AddSeconds(120)
$poll = 0
while ((Get-Date) -lt $deadline) {
  $poll++
  $t = Get-Date
  try { $res = $xl.Evaluate($expr) } catch { Write-Host ('  poll' + $poll + ' EVAL_ERR=' + $_.Exception.Message); Start-Sleep -Seconds 3; continue }
  $el = [int]((Get-Date) - $t).TotalMilliseconds
  $shape = '<null>'
  if ($null -eq $res) { $shape = '<null>' }
  elseif ($res -is [string]) { $shape = ('String len=' + $res.Length + ' [' + $res.Substring(0, [Math]::Min(40, $res.Length)) + ']') }
  elseif ($res -is [System.Array]) {
    if ($res.Rank -ge 2) { $shape = ('Array2d ' + $res.GetLength(0) + 'x' + $res.GetLength(1)) } else { $shape = ('Array1d len=' + $res.Length) }
  }
  else { $shape = ('scalar ' + $res.GetType().Name + ' [' + ([string]$res) + ']') }
  $tot = [int]((Get-Date) - $first).TotalSeconds
  Write-Host ('  poll' + $poll + ' t+' + $tot + 's call_ms=' + $el + ' ' + $shape)
  if ($res -is [string] -and $res -notmatch 'Fetching') {
    Write-Host '  >>> PLACEHOLDER RESOLVED (string, not Fetching) - dumping:'
    $d = @($res -split "`n")
    foreach ($ln in $d | Select-Object -First 8) { Write-Host ('      | ' + $ln) }
    break
  }
  if ($res -is [System.Array] -and $res.Rank -ge 2) {
    Write-Host '  >>> ARRAY RESULT - dumping first rows:'
    $rows = [int]$res.GetLength(0); $cols = [int]$res.GetLength(1)
    $maxr = [Math]::Min(5, $rows)
    for ($r = 0; $r -lt $maxr; $r++) {
      $out = ''
      for ($c = 0; $c -lt $cols; $c++) { $out += '  [' + ([string]$res.GetValue($r, $c)) + ']' }
      Write-Host ('      r' + $r + ':' + $out)
    }
    Write-Host ('      ... total ' + $rows + 'x' + $cols)
    break
  }
  Start-Sleep -Seconds 3
}
Write-Host ('TOTAL_POLLS=' + $poll + ' TOTAL_SEC=' + [int]((Get-Date) - $first).TotalSeconds)

# cleanup
$wbc = [int]$xl.Workbooks.Count
for ($i = 1; $i -le $wbc; $i++) { try { $xl.Workbooks.Item($i).Close($false) | Out-Null } catch { } }
try { $xl.Quit() | Out-Null } catch { Write-Host ('QUIT_ERR=' + $_.Exception.Message) }
try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null } catch { }
[GC]::Collect(); [GC]::WaitForPendingFinalizers(); [GC]::Collect()
Start-Sleep -Seconds 3
$after = @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)
Write-Host ('PROTECTED_14644_ALIVE=' + [bool](Get-Process -Id 14644 -ErrorAction SilentlyContinue))
