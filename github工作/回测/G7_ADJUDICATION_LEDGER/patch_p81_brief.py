# -*- coding: utf-8 -*-
"""Surgical patch of recreate_p81.py: rewrite Write-ClusterBrief to avoid the
PS 5.1 array-literal + comma precedence defect, fix (GMT+8), add $tokenMode."""
import io

GEN = "D:\\DSH_WORK\\github\u5de5\u4f5c\\\u56de\u6d4b\\G7_ADJUDICATION_LEDGER\\recreate_p81.py"

NEW_FUNC = '''function Add-BriefLine {
  param($Lines, $Text)
  [void]$Lines.Add([string]$Text)
}

function Write-ClusterBrief {
  param($SnapTs, $Agents, $ExcelRule, $TerritoryState, $DualHash, $QuickScan, $WarnList, $P0Checks, $P0Pass, $P0Total, $RedLines)

  # NOTE: build every row as a SCALAR variable first, then Add it.
  # Putting "'..' + $x + '..'" directly inside a comma-separated @(...) literal
  # re-associates the + under the comma and silently splits the row into 3 items.
  $L = New-Object System.Collections.ArrayList

  Add-BriefLine $L $zh['title']
  Add-BriefLine $L ''
  $r = ('生成时间: ' + $SnapTs.ToString('yyyy-MM-dd HH:mm:ss') + ' (GMT+8)')
  Add-BriefLine $L $r
  $r = ('token: ' + $tokenName + ' (' + $tokenMode + ') | auth_ref: ' + $a01Tag)
  Add-BriefLine $L $r
  $r = ('模式: ' + $zh['sub'])
  Add-BriefLine $L $r
  Add-BriefLine $L ''
  Add-BriefLine $L $zh['head_agent']
  Add-BriefLine $L ''
  Add-BriefLine $L '| Agent | 当前状态 | 最近回执 / 时间 | 重要 flag |'
  Add-BriefLine $L '|---|---|---|---|'
  $c = $Agents.dshc
  $d = $Agents.dsha
  $s = $Agents.dshd
  $r = '| DSHC | ' + $c.state + ' | ' + $c.last_receipt + ' @ ' + $c.last_receipt_ts + ' | wind_api_calls=' + $c.wind_api_calls + '; token_state=' + $c.token_state + '; root=' + $c.spawn_bug_root + '; guard_rules=' + $c.guard_rules_count + ' |'
  Add-BriefLine $L $r
  $r = '| DSHA | ' + $d.state + ' | ' + $d.last_receipt + ' @ ' + $d.last_receipt_ts + ' | P68=' + $d.p68_lock + ' commit=' + $d.p68_commit + '; gate=' + $d.gate + '; permit=' + $d.release_permit + ' |'
  Add-BriefLine $L $r
  $r = '| DSHD | ' + $s.state + ' | poll#' + $s.poll_count + ' @ ' + $s.poll_ts + ' | audit_only=YES; excel_observer=ON; tag=' + $s.a01_tag + ' |'
  Add-BriefLine $L $r
  Add-BriefLine $L ''
  Add-BriefLine $L $zh['head_excel']
  Add-BriefLine $L ''
  Add-BriefLine $L '| 指标 | 值 |'
  Add-BriefLine $L '|---|---|'
  $r = '| Excel 进程总数 | ' + $ExcelRule.total_excel + ' |'
  Add-BriefLine $L $r
  $r = '| 非保护 PID 数 | ' + $ExcelRule.non_protected_excel + ' |'
  Add-BriefLine $L $r
  $r = '| 非保护且落入 DSHC 任务窗口的 PID 数 | ' + $ExcelRule.non_protected_in_task_window + ' |'
  Add-BriefLine $L $r
  $r = '| 告警阈值 (> ) | ' + $ExcelRule.threshold_gt + ' |'
  Add-BriefLine $L $r
  $r = '| 触发黄色告警 | ' + $ExcelRule.triggered + ' |'
  Add-BriefLine $L $r
  $r = '| 自动 kill | ' + $ExcelRule.auto_kill + ' |'
  Add-BriefLine $L $r
  $r = '| 保护 PID | ' + $ExcelRule.protected_pid + ' (' + $ExcelRule.protected_name + ') |'
  Add-BriefLine $L $r
  Add-BriefLine $L ''
  Add-BriefLine $L $zh['head_territ']
  Add-BriefLine $L ''
  $r = ('契约状态: ACTIVE | 领地条目: ' + $TerritoryState.entry_count + ' | 扫描模式: ' + $TerritoryState.scan_mode)
  Add-BriefLine $L $r
  $r = ('并发写入冲突数: ' + $TerritoryState.conflict_count)
  Add-BriefLine $L $r
  Add-BriefLine $L ''
  $tcRows = @()
  foreach ($t in $TerritoryState.conflicts) {
    $r = ('- [' + $t.severity + '] ' + $t.code + ' :: ' + $t.relative_path + ' :: ' + $t.detail)
    $tcRows += $r
  }
  if ($tcRows.Count -eq 0) { $tcRows += '- 无冲突记录' }
  Add-BriefLine $L ([string]::Join("`n", $tcRows))
  Add-BriefLine $L ''
  Add-BriefLine $L $zh['head_csv']
  Add-BriefLine $L ''
  Add-BriefLine $L '| 项 | 值 |'
  Add-BriefLine $L '|---|---|'
  $r = '| hash A (字节读 SHA256) | ' + $DualHash.hash_a_byte_read + ' |'
  Add-BriefLine $L $r
  $r = '| hash B (Get-FileHash) | ' + $DualHash.hash_b_getfilehash + ' |'
  Add-BriefLine $L $r
  $r = '| A == B | ' + $DualHash.a_eq_b + ' |'
  Add-BriefLine $L $r
  $r = '| DSHC ref (A03 csv_output) | ' + $DualHash.ref_a03_csv_output + ' |'
  Add-BriefLine $L $r
  $r = '| 匹配 A03 引用 | ' + $DualHash.matches_ref_a03 + ' |'
  Add-BriefLine $L $r
  $r = '| 匹配 P80 历史观测 | ' + $DualHash.matches_ref_a01_prior + ' |'
  Add-BriefLine $L $r
  $r = '| 扫描结论 | ' + $DualHash.scan_status + ' |'
  Add-BriefLine $L $r
  $r = '| 告警码 | ' + $DualHash.mismatch_code + ' |'
  Add-BriefLine $L $r
  $r = ('| 文件大小 | ' + $QuickScan.size_bytes + ' B (P68 下限 ' + $QuickScan.min_size_required + ') |')
  Add-BriefLine $L $r
  $r = ('| 行数 / 数据行 | ' + $QuickScan.rough_lines + ' / ' + $QuickScan.data_rows + ' (P68 下限 ' + $QuickScan.min_rows_required + ') |')
  Add-BriefLine $L $r
  $r = '| 缺关键词 | ' + $QuickScan.keywords_missing_count + ' |'
  Add-BriefLine $L $r
  $r = '| 最大连续空行 | ' + $QuickScan.max_consecutive_blank + ' |'
  Add-BriefLine $L $r
  $r = '| Quick-Scan 结论 | ' + $QuickScan.scan_status + ' |'
  Add-BriefLine $L $r
  Add-BriefLine $L '| 熔断 | 未触发 (DSHA-P68 为唯一受理权威) |'
  Add-BriefLine $L ''
  Add-BriefLine $L $zh['head_board']
  Add-BriefLine $L ''
  if ($WarnList.Count -eq 0) {
    $r = ('**' + $zh['calm'] + '** （零告警标签）')
    Add-BriefLine $L $r
  } else {
    $wRows = @()
    foreach ($w in $WarnList) {
      $r = ('- [' + $w.severity + '] ' + $w.code + ' @ ' + $w.ts + ' :: ' + $w.detail)
      $wRows += $r
    }
    Add-BriefLine $L ([string]::Join("`n", $wRows))
  }
  Add-BriefLine $L ''
  Add-BriefLine $L $zh['head_p0']
  Add-BriefLine $L ''
  $r = ('P0 校验: ' + $P0Pass + '/' + $P0Total)
  Add-BriefLine $L $r
  $p0Rows = @()
  foreach ($k in $P0Checks.Keys) {
    $v = $P0Checks[$k]
    $mark = 'PASS'
    if ($v.result -eq $false) { $mark = 'FAIL' }
    $r = ('- [' + $mark + '] ' + $k + ' = ' + $v.detail)
    $p0Rows += $r
  }
  Add-BriefLine $L ([string]::Join("`n", $p0Rows))
  Add-BriefLine $L ''
  Add-BriefLine $L $zh['head_red']
  Add-BriefLine $L ''
  $r = ('- audit_only = ' + $RedLines.audit_only)
  Add-BriefLine $L $r
  $r = ('- processes_untouched = ' + $RedLines.processes_untouched + ' / no_kill_executed = ' + $RedLines.no_kill_executed)
  Add-BriefLine $L $r
  $r = ('- gate_unchanged = ' + $RedLines.gate_unchanged + ' (observed: ' + $RedLines.gate_observed + ')')
  Add-BriefLine $L $r
  $r = ('- release_permit_not_issued = ' + $RedLines.release_permit_not_issued + ' (observed: ' + $RedLines.release_permit_observed + ')')
  Add-BriefLine $L $r
  $r = ('- dshd_runs_backtest = ' + $RedLines.dshd_runs_backtest)
  Add-BriefLine $L $r
  $r = ('- dshd_fetches_for_dshc = ' + $RedLines.dshd_fetches_for_dshc)
  Add-BriefLine $L $r
  $r = ('- dshd_bypasses_dsha_p68 = ' + $RedLines.dshd_bypasses_dsha_p68)
  Add-BriefLine $L $r
  $r = ('- output_csv_touched = ' + $RedLines.output_csv_touched)
  Add-BriefLine $L $r
  $r = ('- intervention = ' + $RedLines.intervention)
  Add-BriefLine $L $r
  $r = ('- wind_api_calls = ' + $RedLines.wind_api_calls)
  Add-BriefLine $L $r
  Add-BriefLine $L ''

  return ([string]::Join("`n", ([string[]]$L.ToArray())))
}
'''

src = io.open(GEN, encoding='utf-8').read()

start = src.index('function Write-ClusterBrief {')
end_marker = '\n# ---------------- MAIN LOOP ----------------'
end = src.index(end_marker, start)

old = src[start:end]
print('REPLACING chars', start, '->', end, '(', len(old), 'chars )')

src = src[:start] + NEW_FUNC + src[end:]

# add $tokenMode constant and drop $tokenMode2
assert "$tokenState                = 'ACTIVE_AUDIT_READ_ONLY'" in src
src = src.replace(
    "$tokenState                = 'ACTIVE_AUDIT_READ_ONLY'",
    "$tokenState                = 'ACTIVE_AUDIT_READ_ONLY'\n$tokenMode                 = 'AUDIT_READ_ONLY'",
    1,
)
assert "$tokenMode2 = $tokenMode\n" in src
src = src.replace("$tokenMode2 = $tokenMode\n", "", 1)
assert "$tokenMode2" not in src

io.open(GEN, 'w', encoding='utf-8', newline='').write(src)
print('PATCHED recreate_p81.py  size=', len(src))
