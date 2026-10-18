# Diagnostic 4: read the OLE add-in model (ProgId/Description) instead of Name.
$before = @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
try { [void]$xl.Workbooks.Add() } catch { }
Start-Sleep -Seconds 4
$coll = $xl.COMAddIns
$cnt = 0; try { $cnt = $coll.Count } catch { }
Write-Host ('COMADDINS_COUNT=' + $cnt)
$found = @()
for ($i = 1; $i -le $cnt; $i++) {
  $a = $coll.Item($i)
  $prog = ''; try { $prog = [string]$a.ProgId } catch { }
  $desc = ''; try { $desc = [string]$a.Description } catch { }
  $guid = ''; try { $guid = [string]$a.Guid } catch { }
  $conn = $null; try { $conn = [bool]$a.Connect } catch { }
  $obj  = $null; try { $obj = [bool]([System.Reflection.Missing]::Value -ne $a.Object) } catch { $obj = '<obj_err>' }
  Write-Host ('  ITEM' + $i + ' progid=[' + $prog + '] desc=[' + $desc + '] guid=[' + $guid + '] connect=' + $conn + ' hasobject=' + $obj)
  if ($prog -match 'WDF|Wind' -or $desc -match 'WDF|Wind') { $found += ($prog + ' | ' + $desc) }
}
Write-Host ('WDF_MATCHES=' + $found.Count + ' :: ' + ($found -join ' ;; '))

$wbBefore = 0; try { $wbBefore = $xl.Workbooks.Count } catch { }
for ($i = 1; $i -le $wbBefore; $i++) { try { $xl.Workbooks.Item($i).Close($false) | Out-Null } catch { } }
try { $xl.Quit() | Out-Null } catch { }
try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null } catch { }
[GC]::Collect(); [GC]::WaitForPendingFinalizers(); [GC]::Collect()
Start-Sleep -Seconds 3
$after = @(Get-Process EXCEL -ErrorAction SilentlyContinue | ForEach-Object { $_.Id } | Sort-Object -Unique)
Write-Host ('EXCEL_ADDED=[' + (@($after | Where-Object { $_ -notin $before }) -join ',') + ']')
Write-Host ('PROTECTED_14644_ALIVE=' + [bool](Get-Process -Id 14644 -ErrorAction SilentlyContinue))
