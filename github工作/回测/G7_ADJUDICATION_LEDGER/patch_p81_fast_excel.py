# -*- coding: utf-8 -*-
"""Patch recreate_p81.py: add a 20s Excel fast-sampling sub-cadence so transient
spawns (e.g. the 08:48 'possible WDF bombing' seen by DSHD-P80) cannot fall
between the 5-minute polls. Observation-only: no kill, no intervention."""
import io

GEN = "D:\\DSH_WORK\\github\u5de5\u4f5c\\\u56de\u6d4b\\G7_ADJUDICATION_LEDGER\\recreate_p81.py"
src = io.open(GEN, encoding='utf-8').read()
orig = src

def rep(old, new, count=1):
    global src
    assert src.count(old) == count, "expected %d occurrence(s) of:\n%s\n|got %d" % (count, old[:120], src.count(old))
    src = src.replace(old, new, count)

# ---- A: fast-sampling constant ----
rep("$pollIntervalSec           = 300",
    "$pollIntervalSec           = 300\n"
    "$excelFastIntervalSec       = 20\n"
    "$fastBufferKeepMax          = 240")

# ---- B: fast buffer init ----
rep("$excelHistory = @()",
    "$excelHistory = @()\n$fastBuffer = @()")

# ---- C: merge fast samples into the rule at poll start ----
old_c = """    # ---------- Excel drift observer ----------
    $snaps = Get-ExcelSnapshot $dshcWindowStart
    $excelRule = Test-ExcelSpawnRule $snaps
"""
new_c = """    # ---------- Excel drift observer ----------
    $snaps = Get-ExcelSnapshot $dshcWindowStart
    $excelRule = Test-ExcelSpawnRule $snaps

    # merge fast Excel samples collected during the previous sleep window.
    # Rationale: a real transient did occur at 2026-10-19T08:48 (DSHD-P80 and
    # DSHD-P80-PHASE2 both raised CIRCUIT_BREAKER_READY 'Multiple Excel
    # instances: 2 (possible WDF bombing)') and it vanished inside one 5-minute
    # poll window. 20s sub-cadence closes that blind spot. Observation only.
    $fastSampleCount = 0
    $fastMaxTotal = 0
    $fastMaxNonProtWin = 0
    $fastTransientPids = @()
    $fastTransient = $false
    $fastRows = @()
    foreach ($fs in $fastBuffer) {
      if ($null -eq $fs) { continue }
      $fastSampleCount++
      if ($fs.total_excel -gt $fastMaxTotal) { $fastMaxTotal = $fs.total_excel }
      if ($fs.non_protected_in_task_window -gt $fastMaxNonProtWin) { $fastMaxNonProtWin = $fs.non_protected_in_task_window }
      foreach ($fp in $fs.non_protected_pids) { if ($null -ne $fp -and ($fastTransientPids -notcontains $fp)) { $fastTransientPids += $fp } }
      if ($fs.non_protected -gt 0) { $fastTransient = $true }
      $fastRows += @{
        ts = $fs.ts
        total_excel = $fs.total_excel
        non_protected = $fs.non_protected
        non_protected_in_task_window = $fs.non_protected_in_task_window
        non_protected_pids = $fs.non_protected_pids
        triggered = $fs.triggered
      }
    }
    $excelRule.fast_sample_count = $fastSampleCount
    $excelRule.fast_interval_sec = $excelFastIntervalSec
    $excelRule.fast_max_total_excel = $fastMaxTotal
    $excelRule.fast_max_non_protected_in_task_window = $fastMaxNonProtWin
    $excelRule.fast_transient_non_protected_seen = $fastTransient
    $excelRule.fast_transient_pids = $fastTransientPids
    $excelRule.fast_samples = $fastRows
    $excelRule.fast_transient_warning = ($fastMaxNonProtWin -gt $excelRule.threshold_gt)
    $excelRule.combined_trigger = ($excelRule.triggered -or $excelRule.fast_transient_warning)
    $excelRule.detection_caveat = ('poll cadence ' + $pollIntervalSec + 's is blind to transients shorter than ' + $excelFastIntervalSec + 's; fast sampler covers ' + $excelFastIntervalSec + 's granularity')
    $fastBuffer = @()
"""
rep(old_c, new_c)

# ---- D: transient warning ----
old_d = """    if ($excelRule.triggered) {
      $warnList += @{code = 'OBS-SPAWN-EXCEL-001'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('non-protected Excel spawned inside DSHC task window = ' + $excelRule.non_protected_in_task_window + ' > threshold ' + $excelRule.threshold_gt + '; observation only, no kill')}
    }
"""
new_d = old_d + """    if ($excelRule.fast_transient_warning) {
      $warnList += @{code = 'OBS-SPAWN-EXCEL-001-TRANSIENT'; severity = 'YELLOW'; ts = $pollTs.ToString('yyyy-MM-ddTHH:mm:sszzz'); detail = ('non-protected Excel inside DSHC window caught by ' + $excelFastIntervalSec + 's fast sampler (max=' + $excelRule.fast_max_non_protected_in_task_window + ' > threshold ' + $excelRule.threshold_gt + ', samples=' + $excelRule.fast_sample_count + ', pids=' + ($excelRule.fast_transient_pids -join ',') + '); survived only between polls; observation only, no kill')}
    }
"""
rep(old_d, new_d)

# ---- E: board rule_ids ----
rep("""rule_ids = @('OBS-SPAWN-EXCEL-001','A01_HASH_MISMATCH_WARNING','CONCURRENT_WRITE_CONFLICT','A01_CSV_BLANK_RUN')""",
    """rule_ids = @('OBS-SPAWN-EXCEL-001','OBS-SPAWN-EXCEL-001-TRANSIENT','A01_HASH_MISMATCH_WARNING','CONCURRENT_WRITE_CONFLICT','A01_CSV_BLANK_RUN')""")

# ---- F: replace single sleep with fast-sampling sleep ----
old_f = """  Start-Sleep -Seconds $pollIntervalSec
}"""
new_f = """  # sleep in fast-sampling steps so Excel spawn transients are observable.
  # Read-only: Get-ExcelSnapshot only reads process metadata, never touches a process.
  $sleepRemain = $pollIntervalSec
  while ($sleepRemain -gt 0) {
    $step = $excelFastIntervalSec
    if ($step -gt $sleepRemain) { $step = $sleepRemain }
    Start-Sleep -Seconds $step
    try {
      $fsSnaps = Get-ExcelSnapshot $dshcWindowStart
      $fsRule = Test-ExcelSpawnRule $fsSnaps
      $fsPids = @()
      foreach ($fsp in $fsSnaps) { if ($null -ne $fsp -and (-not $fsp.protected)) { $fsPids += [int]$fsp.pid } }
      $fastBuffer += @{
        ts = (Get-Date).ToString('yyyy-MM-ddTHH:mm:sszzz')
        total_excel = $fsRule.total_excel
        non_protected = $fsRule.non_protected_excel
        non_protected_in_task_window = $fsRule.non_protected_in_task_window
        triggered = $fsRule.triggered
        non_protected_pids = $fsPids
      }
      if ($fastBuffer.Count -gt $fastBufferKeepMax) { $fastBuffer = @($fastBuffer[($fastBuffer.Count - $fastBufferKeepMax)..($fastBuffer.Count - 1)]) }
    } catch { }
    $sleepRemain = $sleepRemain - $step
  }
}"""
rep(old_f, new_f)

# ---- G: brief rows for the fast sampler ----
old_g = """  $r = '| 保护 PID | ' + $ExcelRule.protected_pid + ' (' + $ExcelRule.protected_name + ') |'
  Add-BriefLine $L $r
"""
new_g = old_g + """  $r = '| 快采样间隔 (秒) | ' + $ExcelRule.fast_interval_sec + ' |'
  Add-BriefLine $L $r
  $r = ('| 快采样次数 / 观测到的 Excel 峰值 | ' + $ExcelRule.fast_sample_count + ' / ' + $ExcelRule.fast_max_total_excel + ' |')
  Add-BriefLine $L $r
  $r = '| 快采样中非保护且在窗口内峰值 | ' + $ExcelRule.fast_max_non_protected_in_task_window + ' |'
  Add-BriefLine $L $r
  $r = '| 快采样捕获的瞬时非保护 PID | ' + ($ExcelRule.fast_transient_pids -join ',') + ' |'
  Add-BriefLine $L $r
  $r = '| 合并触发判定 (定点 OR 快采样) | ' + $ExcelRule.combined_trigger + ' |'
  Add-BriefLine $L $r
"""
rep(old_g, new_g)

assert src != orig
io.open(GEN, 'w', encoding='utf-8', newline='').write(src)
print('PATCHED recreate_p81.py  delta=%d chars  size=%d' % (len(src) - len(orig), len(src)))
