# Diagnostic 2: identify the surviving Excel process + fix COMAddIns property access.
$before = @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)
Write-Host '=== BEFORE ==='
Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object {
  $st = $_.StartTime.ToString('HH:mm:ss')
  $cw = ''; try { $cw = $_.MainWindowTitle } catch { }
  $pp = 0; try { $pp = (Get-CimInstance Win32_Process -Filter ('ProcessId=' + $_.Id)).ParentProcessId } catch { }
  Write-Host ('  PID=' + $_.Id + ' start=' + $st + ' parent=' + $pp + ' title=[' + $cw + ']')
}
Write-Host ('MY_PID=' + $PID)

$t0 = Get-Date
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
$appPid = $null
try { $appPid = (Get-Process -Id ([int]$xl.Hwnd)).Id } catch { }
Write-Host ('AGENT_APP_PID=' + $appPid + ' hwnd=' + $xl.Hwnd)
try { [void]$xl.Workbooks.Add() } catch { Write-Host ('WORKBOOK_ADD_ERR=' + $_.Exception.Message) }

Write-Host '=== AFTER CREATE + WB ADD (t+5s) ==='
Start-Sleep -Seconds 5
Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object {
  $st = $_.StartTime.ToString('HH:mm:ss')
  $cw = ''; try { $cw = $_.MainWindowTitle } catch { }
  $pp = 0; try { $pp = (Get-CimInstance Win32_Process -Filter ('ProcessId=' + $_.Id)).ParentProcessId } catch { }
  Write-Host ('  PID=' + $_.Id + ' start=' + $st + ' parent=' + $pp + ' title=[' + $cw + ']')
}

Write-Host '=== COMAddIns via .Item(i) ==='
$coll = $xl.COMAddIns
$cnt = 0; try { $cnt = $coll.Count } catch { }
Write-Host ('COUNT=' + $cnt)
for ($i = 1; $i -le $cnt; $i++) {
  $a = $null; try { $a = $coll.Item($i) } catch { Write-Host ('  ITEM' + $i + ' ERR=' + $_.Exception.Message); continue }
  $nm = ''; try { $nm = $a.Name } catch { $nm = '<NAME_ERR>' }
  $lb = 0; try { $lb = $a.LoadBehavior } catch { }
  $ld = $null; try { $ld = $a.Loaded } catch { }
  Write-Host ('  ITEM' + $i + ' name=' + $nm + ' lb=' + $lb + ' loaded=' + $ld)
}

Write-Host '=== CLEANUP ==='
$wbBefore = 0; try { $wbBefore = $xl.Workbooks.Count } catch { }
Write-Host ('WORKBOOKS_OPEN=' + $wbBefore)
for ($i = 1; $i -le $wbBefore; $i++) {
  try { $xl.Workbooks.Item($i).Close($false) | Out-Null; Write-Host ('  CLOSED WB' + $i) }
  catch { Write-Host ('  CLOSE_ERR=' + $_.Exception.Message) }
}
$wbAfter = 0; try { $wbAfter = $xl.Workbooks.Count } catch { }
Write-Host ('WORKBOOKS_AFTER_CLOSE=' + $wbAfter)
try { $xl.Quit() | Out-Null; Write-Host 'QUIT_OK' } catch { Write-Host ('QUIT_ERR=' + $_.Exception.Message) }
try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null } catch { }
$gc1 = [GC]::Collect(); [GC]::WaitForPendingFinalizers()
[GC]::Collect()
Start-Sleep -Seconds 4
Write-Host '=== AFTER QUIT ==='
Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object {
  $st = $_.StartTime.ToString('HH:mm:ss')
  $cw = ''; try { $cw = $_.MainWindowTitle } catch { }
  $pp = 0; try { $pp = (Get-CimInstance Win32_Process -Filter ('ProcessId=' + $_.Id)).ParentProcessId } catch { }
  Write-Host ('  PID=' + $_.Id + ' start=' + $st + ' parent=' + $pp + ' title=[' + $cw + ']')
}
$after = @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)
Write-Host ('EXCEL_REMOVED=[' + (@($before | Where-Object { $_ -notin $after }) -join ',') + ']')
Write-Host ('EXCEL_ADDED=[' + (@($after | Where-Object { $_ -notin $before }) -join ',') + ']')
