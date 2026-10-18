# A01 final channel probe: is the Wind data service reachable at all from this Excel?
# Tests 3 minimal formulas. One isolated background Excel; foreground Excel untouched.
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

$tests = @(
  @{ rng = 'A1';  f = '=WSD("CU.SHF","CLOSE","2025-01-02","2025-01-03")' },
  @{ rng = 'D1';  f = '=WSD("CU.SHF","CLOSE","2025-01-01","2025-01-10")' },
  @{ rng = 'H1';  f = '=WS("CU.SHF",1)' },
  @{ rng = 'K1';  f = '=WSS("CU.SHF")' }
)
foreach ($t in $tests) {
  try { $ws.Range($t.rng).Formula = $t.f; Write-Host ('  SET ' + $t.rng + ' = ' + $t.f) }
  catch { Write-Host ('  SET ' + $t.rng + ' ERR=' + $_.Exception.Message) }
}
try { $xl.Calculate() | Out-Null } catch { }
$t0 = Get-Date
$deadline = (Get-Date).AddSeconds(60)
$poll = 0
while ((Get-Date) -lt $deadline) {
  $poll++
  try { $xl.Calculate() | Out-Null } catch { }
  $tot = [int]((Get-Date) - $t0).TotalSeconds
  $allDone = $true
  $parts = @()
  foreach ($t in $tests) {
    $tx = '<n/a>'; $v2 = $null
    try { $tx = [string]$ws.Range($t.rng).Text } catch { }
    try { $v2 = $ws.Range($t.rng).Value2 } catch { }
    $head = $tx; if ($head.Length -gt 30) { $head = $head.Substring(0, 30) }
    $parts += ($t.rng + '=[' + $head + ']')
    if ($tx -match 'Fetching|无法读取') { $allDone = $false }
  }
  Write-Host ('  poll' + $poll + ' t+' + $tot + 's  ' + ($parts -join '  '))
  if ($allDone) { Write-Host '  >>> ALL CELLS RESOLVED'; break }
  Start-Sleep -Seconds 5
}

Write-Host '=== FINAL VALUES ==='
foreach ($t in $tests) {
  $tx = ''; $v2 = '<err>'; $na = $false
  try { $tx = [string]$ws.Range($t.rng).Text } catch { }
  try { $v2 = [string]$ws.Range($t.rng).Value2 } catch { }
  Write-Host ('  ' + $t.rng + '  text=[' + $tx + ']  value2=[' + $v2 + ']')
}

# cleanup
$wbc = [int]$xl.Workbooks.Count
for ($i = 1; $i -le $wbc; $i++) { try { $xl.Workbooks.Item($i).Close($false) | Out-Null } catch { } }
try { $xl.Quit() | Out-Null } catch { Write-Host ('QUIT_ERR=' + $_.Exception.Message) }
try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null } catch { }
[GC]::Collect(); [GC]::WaitForPendingFinalizers(); [GC]::Collect()
Start-Sleep -Seconds 3
$after = @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)
Write-Host ('PROTECTED_14644_ALIVE=' + [bool](Get-Process -Id 14644 -ErrorAction SilentlyContinue))
