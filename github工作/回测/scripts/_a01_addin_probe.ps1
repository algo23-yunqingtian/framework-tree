# Diagnostic: does the WDF add-in appear in COMAddIns of a COM-automated Excel?
# No Wind data calls, no WSD formula. Creates and quits ONE isolated background Excel.
$before = @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)
Write-Host ('EXCEL_BEFORE=[' + ($before -join ',') + ']')

$rb = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Office\Excel\Addins\WDF.Addin' -ErrorAction Stop
Write-Host ('HKLM WDF.Addin LoadBehavior=' + $rb.LoadBehavior)
$rc = Get-ItemProperty 'HKCU:\SOFTWARE\Microsoft\Office\Excel\Addins\WDF.Addin' -ErrorAction Stop
Write-Host ('HKCU WDF_PATH=' + $rc.WDF_PATH + ' LoadBehavior=' + $rc.LoadBehavior)

$t0 = Get-Date
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
Write-Host ('AGENT_PID=' + (@((Get-Process EXCEL -ErrorAction SilentlyContinue | Where-Object { $_.Id -notin $before }).Id) -join ','))
try { [void]$xl.Workbooks.Add() } catch { Write-Host ('WORKBOOK_ADD_ERR=' + $_.Exception.Message) }

for ($k = 0; $k -lt 5; $k++) {
  $names = @(); $cnt = 0
  try { $coll = $xl.COMAddIns; $cnt = $coll.Count; $names = @($coll | ForEach-Object { $_.Name }) }
  catch { Write-Host ('COMADDINS_ACCESS_ERR=' + $_.Exception.Message) }
  $wdf = @($names | Where-Object { $_ -match 'WDF' })
  $el = [int]((Get-Date) - $t0).TotalSeconds
  Write-Host ('  t+' + $el + 's  COMAddIns.Count=' + $cnt + '  names=[' + ($names -join ';') + ']  wdf=' + $wdf.Count)
  if ($wdf.Count -gt 0) { break }
  Start-Sleep -Seconds 3
}

$unloaded = @($xl.COMAddIns | Where-Object { $_.Name -match 'WDF' -and ($_.Loaded -ne $true) })
Write-Host ('UNLOADED_WDF_COUNT=' + $unloaded.Count)
foreach ($a in $unloaded) {
  try { [void]$a.Load(); Write-Host ('  EXPLICIT_LOADED=' + $a.Name) }
  catch { Write-Host ('  LOAD_ERR=' + $a.Name + ' :: ' + $_.Exception.Message) }
}

Write-Host '--- full addin detail ---'
foreach ($a in $xl.COMAddIns) {
  $lb = 0; try { $lb = $a.LoadBehavior } catch { }
  $ld = $null; try { $ld = $a.Loaded } catch { }
  Write-Host ('  ADDIN name=' + $a.Name + ' loadbehavior=' + $lb + ' loaded=' + $ld)
}

try { $xl.Workbooks | ForEach-Object { try { $_.Close($false) } catch { } } } catch { }
try { $xl.Quit() } catch { Write-Host ('QUIT_ERR=' + $_.Exception.Message) }
try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null } catch { }
Start-Sleep -Seconds 2
$after = @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)
Write-Host ('EXCEL_AFTER=[' + ($after -join ',') + ']')
Write-Host ('EXCEL_ADDED=[' + (@($after | Where-Object { $_ -notin $before }) -join ',') + ']')
Write-Host ('EXCEL_REMOVED=[' + (@($before | Where-Object { $_ -notin $after }) -join ',') + ']')
