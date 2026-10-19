# Diagnostic: Check WSD formula output and clipboard format
$ErrorActionPreference = "Continue"
$xl = $null; $wb = $null; $ws = $null
try {
    $xl = New-Object -ComObject Excel.Application
    $xl.Visible = $true
    $xl.DisplayAlerts = $false
    $wb = $xl.Workbooks.Add()
    $ws = $wb.Sheets.Item(1)
    $ws.Activate()
    
    Write-Host "=== DIAGNOSTIC: WSD formula + clipboard ==="
    
    # Test 1: WSD formula for ZN.SHF CLOSE
    $formula = '=WSD("ZN.SHF","CLOSE","2025-01-01","TODAY()","Fill=Previous")'
    Write-Host "Setting formula in A1: $formula"
    $ws.Cells.Item(1,1).Formula = $formula
    $xl.Calculate()
    Write-Host "Calculate done, waiting 14s..."
    Start-Sleep -Seconds 14
    
    # Check A1 value via COM
    $a1val = $ws.Cells.Item(1,1).Value2
    Write-Host "A1 COM Value2: $a1val"
    Write-Host "A1 type: $($a1val.GetType().FullName)"
    
    # Check B1 value via COM
    $b1val = $ws.Cells.Item(1,2).Value2
    Write-Host "B1 COM Value2: $b1val"
    Write-Host "B1 type: $($b1val.GetType().FullName)"
    
    # Check A2 value via COM
    $a2val = $ws.Cells.Item(2,1).Value2
    Write-Host "A2 COM Value2: $a2val"
    
    # Copy A1:B100 range
    Write-Host ""
    Write-Host "=== Copying A1:B100 ==="
    $range = $ws.Range("A1:B100")
    try { Set-Clipboard -Value "" } catch {}
    $range.Copy()
    Start-Sleep -Milliseconds 500
    
    $clipRaw = Get-Clipboard
    Write-Host "Clipboard type: $($clipRaw.GetType().FullName)"
    $clipText = "$clipRaw"
    Write-Host "Clipboard length: $($clipText.Length)"
    Write-Host "Clipboard first 500 chars:"
    $preview = $clipText.Substring(0, [Math]::Min(500, $clipText.Length))
    Write-Host $preview
    
    Write-Host ""
    Write-Host "=== Parsed lines ==="
    $lines = $clipText -split "`r?`n"
    Write-Host "Total lines: $($lines.Count)"
    foreach ($i in 0..([Math]::Min(5, $lines.Count-1))) {
        $line = $lines[$i].Trim()
        if ($line -eq "") { Write-Host "  [$i] EMPTY" }
        else { Write-Host "  [$i] '$line'" }
    }
    
} catch {
    Write-Host "ERROR: $_"
} finally {
    if ($ws) { try { [Marshal]::ReleaseComObject($ws) | Out-Null } catch {} }
    if ($wb) { try { $wb.Close($false) | Out-Null; [Marshal]::ReleaseComObject($wb) | Out-Null } catch {} }
    if ($xl) { try { $xl.Quit() | Out-Null; [Marshal]::ReleaseComObject($xl) | Out-Null } catch {} }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    Start-Sleep -Milliseconds 500
    # Kill leaked Excel
    $leaked = Get-Process -Name EXCEL -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne 14644 }
    if ($leaked.Count -gt 0) {
        Write-Host "Cleaning up $($leaked.Count) leaked Excel"
        foreach ($l in $leaked) { try { $l.Kill() } catch {} }
    }
}
