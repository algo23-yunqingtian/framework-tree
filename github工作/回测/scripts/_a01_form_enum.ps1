# Enumerate which WSD parameter forms the WDF add-in actually honours.
$before = @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)

Write-Host '=== registry identity of the add-in ==='
foreach ($k in @('HKLM:\SOFTWARE\Microsoft\Office\Excel\Addins\WDF.Addin','HKCU:\SOFTWARE\Microsoft\Office\Excel\Addins\WDF.Addin')) {
  try {
    $p = Get-ItemProperty $k
    Write-Host ('  ' + $k + ' :: ' + (($p.PSObject.Properties | ForEach-Object { $_.Name + '=' + $_.Value }) -join ' | '))
  } catch { Write-Host ('  ' + $k + ' :: <absent>') }
}
try {
  $dll = Get-Item 'D:\x64\WDF.dll'
  Write-Host ('  WDF.dll size=' + $dll.Length + ' sha256=' + ((Get-FileHash 'D:\x64\WDF.dll' -Algorithm SHA256).Hash))
} catch { }

$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
$wb = $xl.Workbooks.Add()
$ws = $wb.Worksheets.Item(1)
Write-Host ('AGENT_PID=' + (@((Get-Process EXCEL -ErrorAction SilentlyContinue | Where-Object { $_.Id -notin $before }).Id) -join ','))
try { $wb.Activate() | Out-Null; $ws.Activate() | Out-Null } catch { }

$tests = @(
  @{ a = 'A1'; b = 'A10'; f = '=WSD("CU.SHF","CLOSE","2025-01-02","2025-01-03")' },
  @{ a = 'B1'; b = 'B10'; f = '=WSD("CU.SHF",1,"2025-01-02","2025-01-03")' },
  @{ a = 'C1'; b = 'C10'; f = '=WSD("CU.SHF", "CLOSE","2025-01-02","2025-01-03")' },
  @{ a = 'D1'; b = 'D10'; f = '=WSD("CU.SHF","CLOSE;OPEN","2025-01-02","2025-01-03")' },
  @{ a = 'E1'; b = 'E10'; f = '=WSD("CU.SHF","Close","2025-01-02","2025-01-03")' },
  @{ a = 'F1'; b = 'F10'; f = '=WSD("CU.SHF","","2025-01-02","2025-01-03")' },
  @{ a = 'G1'; b = 'G10'; f = '=WSD("CU.SHF","HIGHEST","2025-01-02","2025-01-03")' },
  @{ a = 'H1'; b = 'H10'; f = '=WSD("CU.SHF","CLOSE","2025-01-01","2025-01-10")' }
)
foreach ($t in $tests) {
  try { $ws.Range($t.a).Formula = $t.f } catch { Write-Host ('  SET ' + $t.a + ' ERR=' + $_.Exception.Message) }
}
try { $xl.Calculate() | Out-Null } catch { }
$t0 = Get-Date
$deadline = (Get-Date).AddSeconds(50)
while ((Get-Date) -lt $deadline) {
  try { $xl.Calculate() | Out-Null } catch { }
  $allDone = $true
  foreach ($t in $tests) { try { if ([string]$ws.Range($t.a).Text -match 'Fetching') { $allDone = $false } } catch { } }
  Start-Sleep -Seconds 4
  if ($allDone) { Write-Host ('  ALL_RESOLVED t+' + [int]((Get-Date) - $t0).TotalSeconds + 's'); break }
}

Write-Host '=== RESULTS ==='
foreach ($t in $tests) {
  $a1 = ''; $v1 = '<err>'; $caR = 0; $caC = 0
  try { $a1 = [string]$ws.Range($t.a).Text } catch { }
  try { $v1 = [string]$ws.Range($t.a).Value2 } catch { }
  try { $caR = [int]$ws.Range($t.a).CurrentArray.Rows.Count } catch { }
  try { $caC = [int]$ws.Range($t.a).CurrentArray.Columns.Count } catch { }
  $b1 = ''
  try { $b1 = [string]$ws.Range($t.b).Text } catch { }
  $bv = '<err>'
  try { $bv = [string]$ws.Range($t.b).Value2 } catch { }
  Write-Host ('  ' + $t.f)
  Write-Host ('     ' + $t.a + ' text=[' + $a1 + '] value2=[' + $v1 + '] CurrentArray=' + $caR + 'x' + $caC)
  Write-Host ('     ' + $t.b + ' text=[' + $b1 + '] value2=[' + $bv + ']')
}

# cleanup
$wbc = [int]$xl.Workbooks.Count
for ($i = 1; $i -le $wbc; $i++) { try { $xl.Workbooks.Item($i).Close($false) | Out-Null } catch { } }
try { $xl.Quit() | Out-Null } catch { }
try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null } catch { }
[GC]::Collect(); [GC]::WaitForPendingFinalizers(); [GC]::Collect()
Start-Sleep -Seconds 3
Write-Host ('PROTECTED_14644_ALIVE=' + [bool](Get-Process -Id 14644 -ErrorAction SilentlyContinue))
