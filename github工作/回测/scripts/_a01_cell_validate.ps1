# A01 channel validation 3: WSD is async and add-in-driven. Put the formula IN A CELL
# and poll the cell - Application.Evaluate only returns the placeholder.
$before = @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)
Write-Host ('EXCEL_BEFORE=[' + ($before -join ',') + ']')

$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
$wb = $xl.Workbooks.Add()
$ws = $wb.Worksheets.Item(1)
Write-Host ('AGENT_PID=' + (@((Get-Process EXCEL -ErrorAction SilentlyContinue | Where-Object { $_.Id -notin $before }).Id) -join ','))
try { $wb.Activate() | Out-Null } catch { }
try { $ws.Activate() | Out-Null } catch { }

$cells = @('A1','A100','K1')
$expr = '=WSD("CU.SHF","CLOSE;VOL;OI;SETTLE","2025-01-01","2026-10-17", "Fill=Previous")'
foreach ($rng in $cells) {
  try { $ws.Range($rng).Formula = $expr } catch { Write-Host ('  SET ' + $rng + ' ERR=' + $_.Exception.Message) }
}
try { $xl.Calculate() | Out-Null; Write-Host 'Calculate() done' } catch { Write-Host ('CALC ERR=' + $_.Exception.Message) }
$t0 = Get-Date

$deadline = (Get-Date).AddSeconds(75)
$poll = 0
while ((Get-Date) -lt $deadline) {
  $poll++
  $tot = [int]((Get-Date) - $t0).TotalSeconds
  try { $xl.Calculate() | Out-Null } catch { }
  $parts = @()
  foreach ($rng in $cells) {
    $tx = '<n/a>'; $caR = 0; $caC = 0; $ina = $null
    try { $tx = [string]$ws.Range($rng).Text } catch { }
    try { $ina = [bool]$ws.Range($rng).IsInArray } catch { }
    try { $ca = $ws.Range($rng).CurrentArray; $caR = [int]$ca.Rows.Count; $caC = [int]$ca.Cols } catch { try { $caC = [int]$ca.Columns.Count } catch { } }
    try { $caC = [int]$ws.Range($rng).CurrentArray.Columns.Count } catch { }
    try { $caR = [int]$ws.Range($rng).CurrentArray.Rows.Count } catch { }
    $head = $tx
    if ($tx.Length -gt 60) { $head = $tx.Substring(0, 60) }
    $parts += ($rng + '{text=[' + $head + '] InArray=' + $ina + ' CA=' + $caR + 'x' + $caC + '}')
  }
  Write-Host ('  poll' + $poll + ' t+' + $tot + 's  ' + ($parts -join '  '))
  $done = $false
  foreach ($rng in $cells) {
    try {
      $caR = [int]$ws.Range($rng).CurrentArray.Rows.Count
      $caC = [int]$ws.Range($rng).CurrentArray.Columns.Count
      if ($caR -ge 2 -and $caC -ge 2) { $done = $true }
    } catch { }
  }
  if ($done) { Write-Host '  >>> SPILLED GRID DETECTED'; break }
  Start-Sleep -Seconds 3
}

Write-Host '=== dump A1 CurrentArray ==='
try {
  $ca = $ws.Range('A1').CurrentArray
  $rr = [int]$ca.Rows.Count; $cc = [int]$ca.Columns.Count
  Write-Host ('  ' + $rr + 'x' + $cc)
  $v2 = $ca.Value2
  $maxr = [Math]::Min(6, $rr)
  for ($r = 1; $r -le $maxr; $r++) {
    $out = ''
    for ($c = 1; $c -le $cc; $c++) {
      $t = ''
      try { $t = [string]$ca.Item($r, $c).Text } catch { }
      $out += '  [' + $t + ']'
    }
    Write-Host ('  r' + $r + ':' + $out)
  }
} catch { Write-Host ('  DUMP ERR=' + $_.Exception.Message) }

# also try the async-completion API explicitly
try {
  $t = Get-Date
  $xl.CalculateUntilAsyncQueriesDone()
  Write-Host ('CalculateUntilAsyncQueriesDone OK in ' + [int]((Get-Date) - $t).TotalMilliseconds + 'ms')
} catch { Write-Host ('CalculateUntilAsyncQueriesDone ERR=' + $_.Exception.Message) }

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
