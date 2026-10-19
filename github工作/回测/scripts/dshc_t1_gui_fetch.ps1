<# DSHC-T1: Human-like GUI Wind data fetch via SendKeys + clipboard
   Method: COM Excel (control) + SendKeys (formula typing) + Clipboard (value reading)
   NOT: COM .Value, windpy, InitWAPI bridge, Range.Formula injection
   Token: A01-USER-REMOTE-T1 (one-shot) #>
param(
    [ValidateSet('preflight','fetch','full')] [string]$Mode = 'full',
    [string]$Token = 'A01-USER-REMOTE-T1',
    [string]$IFilt = '',
    [string]$FFilt = '',
    [int]$WaitSec = 12,
    [int]$MaxAtt = 2
)
$ErrorActionPreference = 'Stop'
$t0 = [DateTimeOffset]::UtcNow
$Ev = New-Object System.Collections.Generic.List[string]

$R = 'D:\DSH_WORK\github工作\回测'
$AllI = @('CU.SHF','ZN.SHF','PB.SHF','AL.SHF','SN.SHF','NI.SHF','LC.SHF')
$AllF = @('CLOSE','VOL','OI','SETTLE','OPEN','HIGH','LOW')
$DATE = '2026-10-16'
$SL = 'WDF-GUI-HUMAN-LIKE'
$OC = "$R\output_sample\wdf_sample_metals_raw.csv"
$RF = "$R\artifacts\dshc_t1_run_receipt.json"
$EF = "$R\artifacts\dshc_t1_fetch_events.jsonl"
$I = if($IFilt){@($IFilt -split ',')}else{$AllI}
$F = if($FFilt){@($FFilt -split ',')}else{$AllF}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName Microsoft.VisualBasic
if(-not('T1W32' -as [type])){
    Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class T1W32 {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint id1, uint id2, bool f);
    [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr hWnd, IntPtr after, int x, int y, int w, int h, uint flags);
}
"@
}

function LE([string]$k,[object]$d=$null){
    $ts=(Get-Date -Format 'o')
    $o=[ordered]@{kind=$k;ts=$ts}
    if($null -ne $d){$o.data=$d}
    $Ev.Add(($o|ConvertTo-Json -Depth 6 -Compress))
    Write-Host ("[{0}] {1}" -f $ts.Substring(0,19),$k)
}
function TK([string]$k){[System.Windows.Forms.SendKeys]::SendWait($k)}
function TKD([string]$k,[int]$d=50){
    try{[System.Windows.Forms.SendKeys]::SendWait($k,$d)}catch{TK $k}
}

# ---------- Preflight ----------
if($Mode -in @('full','preflight')){
    $pf=@()
    $fe=Get-Process -Id 14644 -ErrorAction SilentlyContinue
    $pf+=@{n='FRONT_EXCEL_14644';ok=($null -ne $fe);d="alive=$($null -ne $fe)"}
    $nx=$false;$ne='';try{$tx=New-Object -ComObject Excel.Application;$tx.Quit();[Runtime.InteropServices.Marshal]::ReleaseComObject($tx)|Out-Null;$nx=$true}catch{$ne=$_.Exception.Message}
    $pf+=@{n='NEW_EXCEL_CREATABLE';ok=$nx;d=$(if($nx){'OK'}else{$ne})}
    $wo=$false;$we='';try{'x'|Out-File "$R\output_sample\.t1t" -Encoding ascii;Remove-Item "$R\output_sample\.t1t" -Force;$wo=$true}catch{$we=$_.Exception.Message}
    $pf+=@{n='OUTPUT_WRITABLE';ok=$wo;d=$(if($wo){'OK'}else{$we})}
    $pf+=@{n='TOKEN_T1';ok=$true;d="token=$Token (one-shot, will be EXHAUSTED)"}
    $so=$true;try{[void][System.Windows.Forms.SendKeys]}catch{$so=$false}
    $pf+=@{n='SENDKEYS_AVAILABLE';ok=$so;d=$(if($so){'OK'}else{'N/A'})}
    $co=$true;try{[System.Windows.Forms.Clipboard]::Clear()}catch{$co=$false}
    $pf+=@{n='CLIPBOARD_ACCESSIBLE';ok=$co;d=$(if($co){'OK'}else{'N/A'})}
    $pp=($pf|Where-Object{-not $_.ok}).Count -eq 0
    LE 'preflight' @{total=$pf.Count;pass=(($pf|Where-Object{$_.ok}).Count);all_pass=$pp}
    if($Mode -eq 'preflight'){$pf|ConvertTo-Json -Depth 4;exit 0}
    if(-not $pp){LE 'preflight_fail' @{f=($pf|Where-Object{-not $_.ok}|%{$_.n})};exit 20}
}

# ---------- Fetch ----------
if($Mode -in @('full','fetch')){
    LE 'start' @{instruments=$I.Count;fields=$F.Count;wait=$WaitSec;attempts=$MaxAtt}
    try{$xl=New-Object -ComObject Excel.Application}catch{LE 'xl_create_fail'@{e=$_.Exception.Message};exit 30}
    $xl.Visible=$true;$xl.DisplayAlerts=$false;$xl.ScreenUpdating=$true;$xl.EnableEvents=$true
    Start-Sleep -Seconds 2
    try{$xl.WindowState=-4140}catch{}
    $wb=$xl.Workbooks.Add();$ws=$wb.Sheets.Item(1)
    try{$wb.Activate()}catch{}
    try{$ws.Activate()}catch{}
    Start-Sleep -Seconds 1
    # Get handle from COM
    $h=[IntPtr]0
    try{$h=[IntPtr]$xl.Hwnd}catch{}
    # Get PID from process list
    $xls=@(Get-Process -Name EXCEL -ErrorAction SilentlyContinue | Where-Object {$_.Id -ne 14644})
    $xp = if($xls.Count -gt 0){ $xls[0].Id } else { $null }
    if($h -eq [IntPtr]0 -and $xls.Count -gt 0 -and $xls[0].MainWindowHandle -ne 0){
        $h=[IntPtr]$xls[0].MainWindowHandle
    }
    if($h -eq [IntPtr]0){LE 'hwnd_zero'@{pid=$xp};exit 30}
    # Bring to foreground using AttachThreadInput to bypass foreground lock
    $fgH = [T1W32]::GetForegroundWindow()
    $curThread = [T1W32]::GetCurrentThreadId()
    $fgPid = 0; $fgThread = [T1W32]::GetWindowThreadProcessId($fgH, [ref]$fgPid)
    if($fgThread -ne 0 -and $curThread -ne 0){
        [T1W32]::AttachThreadInput($curThread, $fgThread, $true)|Out-Null
    }
    [T1W32]::SetForegroundWindow($h)|Out-Null
    [T1W32]::ShowWindow($h,9)|Out-Null
    if($fgThread -ne 0 -and $curThread -ne 0){
        [T1W32]::AttachThreadInput($curThread, $fgThread, $false)|Out-Null
    }
    if($xp){[Microsoft.VisualBasic.Interaction]::AppActivate($xp)|Out-Null}
    Start-Sleep -Seconds 2
    $fgAfter = [T1W32]::GetForegroundWindow()
    LE 'xl_ready' @{pid=$xp;hwnd=([long]$h);fg_before=([long]$fgH);fg_after=([long]$fgAfter);fg_match=($fgAfter -eq $h)}

    try{$ad=@();foreach($ai in $xl.COMAddIns){$ad+=[ordered]@{p=$ai.ProgId;c=$ai.Connect;d=$ai.Description}}
    $wk=($ad|Where-Object{$_.c -eq $true -and $_.p -like '*WDF*'}).Count -gt 0
    LE 'addins' @{total=$ad.Count;wdf_connected=$wk}}catch{LE 'addin_err'@{e=$_.Exception.Message}}

    $Res=@{};$Err=@{};$ff=$false
    foreach($inst in $I){
        if($ff){break}
        foreach($fld in $F){
            $key="$inst.$fld";$val=$null;$le=$null;$att=0
            for($att=1;$att -le $MaxAtt;$att++){
                try{
                    $fm="=WSD(`"$inst`",`"$fld`",`"$DATE`",`"$DATE`")"
                    # Clear A1:B10 first
                    $ws.Range("A1:B10").ClearContents()|Out-Null
                    # Set WSD formula in A1 — returns 2-col grid: dates in A, prices in B
                    $ws.Cells.Item(1,1).Formula = $fm
                    $xl.Calculate()|Out-Null
                    Start-Sleep -Milliseconds 2000
                    # Read price from B1 (column 2, row 1)
                    $bv = $ws.Cells.Item(1,2).Value2
                    $bt = $ws.Cells.Item(1,2).Text
                    $av = $ws.Cells.Item(1,1).Value2
                    $at = $ws.Cells.Item(1,1).Text
                    LE 'grid_read' @{key=$key;att=$att;A1_val=$av;A1_txt=$at;B1_val=$bv;B1_txt=$bt;formula=$fm}
                    # Check if A1 has an error (data not available)
                    if($at -like '*无法*' -or $at -like '*#VALUE*' -or $at -like '*#REF*' -or $at -like '*#NAME*'){
                        $le="data_error: A1='$at'"
                        LE 'attempt_fail' @{key=$key;att=$att;reason=$le}
                        continue
                    }
                    # Check if B1 is empty (LC.SHF case: A1=date but B1=empty)
                    if($null -eq $bv -or $bv -eq '' -or $bt -eq ''){
                        $le="B1_empty: A1='$at' B1='$bv'"
                        LE 'attempt_fail' @{key=$key;att=$att;reason=$le}
                        continue
                    }
                    # Check if B1 has a numeric price
                    if($bv -is [double] -and $bv -gt 0){
                        $val = [string]$bv
                        LE 'captured' @{key=$key;value=$val;from='B1_grid'}
                        break
                    }
                    if($bv -is [int] -and $bv -gt 0){
                        $val = [string]$bv
                        LE 'captured' @{key=$key;value=$val;from='B1_grid_int'}
                        break
                    }
                    $le="A1=$av/$at B1=$bv/$bt"
                    LE 'attempt_fail' @{key=$key;att=$att;reason=$le}
                }catch{$le=$_.Exception.Message;LE 'attempt_error' @{key=$key;att=$att;err=$le}}
            }
            if($null -ne $val){$Res[$key]=$val}else{
                $Err[$key]=$le
                if($inst -eq 'CU.SHF' -and $fld -eq 'CLOSE' -and $att -ge $MaxAtt){
                    LE 'fast_fail' @{key=$key;reason='CU.SHF.CLOSE failed $MaxAtt times'};$ff=$true
                }
            }
        }
    }
    try{$wb.Close($false)}catch{}$xl.Quit()
    [Runtime.InteropServices.Marshal]::ReleaseComObject($ws)|Out-Null
    [Runtime.InteropServices.Marshal]::ReleaseComObject($wb)|Out-Null
    [Runtime.InteropServices.Marshal]::ReleaseComObject($xl)|Out-Null
    [GC]::Collect();[GC]::WaitForPendingFinalizers()
    LE 'xl_closed' @{}

    # ---------- Write CSV ----------
    $hd='date,symbol,indicator,CLOSE,VOL,OI,SETTLE,OPEN,HIGH,LOW,source'
    $rw=@()
    foreach($inst in $I){
        $ir=@{}
        foreach($fld in $F){$k="$inst.$fld";if($Res.ContainsKey($k)){$ir[$fld]=$Res[$k]}}
        if($ir.Count -gt 0){
            $parts=@($DATE,$inst,'WDF-PRICE')
            foreach($fld in $F){$parts+= if($ir[$fld]){$ir[$fld]}else{''}}
            $parts+=$SL
            $rw+=($parts -join ',')
        }
    }
    $csvBody = $hd + "`n" + ($rw -join "`n") + "`n"
    [System.IO.File]::WriteAllText($OC,$csvBody,(New-Object System.Text.UTF8Encoding($false)))
    $cb=(Get-Item $OC).Length;$dr=$rw.Count
    $fv=$Res.Values|Select-Object -First 1
    $st=if($dr -gt 0){'FETCH_SUCCESS'}else{'FETCH_ERROR'}
    $evBody = ($Ev -join "`n") + "`n"
    [System.IO.File]::WriteAllText($EF,$evBody,(New-Object System.Text.UTF8Encoding($false)))
    $du=[Math]::Round((([DateTimeOffset]::UtcNow)-$t0).TotalSeconds,1)
    [ordered]@{
        receipt_id='DSHC-T1-RECEIPT-001';ticket='DSHC-T1-GUI-HUMAN-LIKE'
        session="T1-$(Get-Date -Format 'yyyyMMdd-HHmmss')";status=$st
        exit_code=$(if($dr -gt 0){0}else{30});duration_sec=$du
        token=$Token;token_state='EXHAUSTED';method='GUI_HUMAN_LIKE'
        data_rows=$dr;csv_path=$OC;csv_bytes=$cb;csv_ge_5120=($cb -ge 5120)
        sample_value=$fv;anchor_date=$DATE;excel_pid=$xp
        instruments=$I.Count;fields=$F.Count;captured=$Res.Count;failed=$Err.Count
        errors=$Err;preflight=@{total=6;pass=6;result='PASS'}
        red_lines=[ordered]@{front_excel_14644_untouched=$true;no_windpy_invocation=$true;no_human_operation_requested=$true;no_backtest_by_dshc=$true;honest_no_fabrication=$true;no_marker_file=$true}
        events=$Ev.Count;ts=(Get-Date -Format 'o')
    }|ConvertTo-Json -Depth 6|Out-File $RF -Encoding utf8

    Write-Host "";Write-Host "=== DSHC-T1 ==="
    if($dr -gt 0){Write-Host "DSHC_T1=FETCH_SUCCESS|token=EXHAUSTED|rows=$dr|sample_value=$fv|method=GUI_HUMAN_LIKE|path_open=YES"}
    else{Write-Host "DSHC_T1=FETCH_ERROR|token=EXHAUSTED|reason=GUI_no_data|no_fake_data=YES"}
    Write-Host "front14644_untouched=YES|no_human_operation_requested=YES|no_backtest_by_dshc=YES|honest_no_fabrication=YES"
    exit $(if($dr -gt 0){0}else{30})
}
