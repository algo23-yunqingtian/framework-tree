# ============================================================================
# DSHC-DATA-INCR-SCHEDULE-ROLLBACK · Windows 任务计划程序注册脚本
# 工单: DSHC-DATA-INCR-SCHEDULE-ROLLBACK + DSHC-TASK-012
# 令牌: DSHC-DATA-INCR-SCHEDULE-TOKEN + DSHC-TASK012-PARALLEL-ONLINE-TOKEN
#
# 功能: 注册增量管道每日定时任务 (周一至周五 15:30)
#       + 并行调度分支 (DSHC-TASK-012, 周一至周五 15:35)
#       双链路并行互不干扰
# 用法: .\code\incr_pipeline_schedule.ps1 [-Register] [-Unregister] [-Status]
#       .\code\incr_pipeline_schedule.ps1 -Register -Mode parallel
# ============================================================================

param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("register", "unregister", "status")]
    [string]$Action = "status",

    [Parameter(Mandatory = $false)]
    [ValidateSet("serial", "parallel", "dual")]
    [string]$Mode = "serial"
)

$ErrorActionPreference = "Stop"

# 任务名称
$TaskName = "DSHC-IncrPipelineDaily"
$ParallelTaskName = "DSHC-IncrPipelineParallel"

# 脚本路径 (相对于项目根目录)
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ScriptPath = Join-Path $ProjectRoot "code\incr_pipeline_daily.py"
$ParallelScriptPath = Join-Path $ProjectRoot "code\incr_pipeline_parallel_online.py"

# Python 路径
$PythonExe = "python"

# 执行参数
$Arguments = "--execute"
$ParallelArguments = "--parallel-run"

# 触发时间 (周一至周五 15:30 serial, 15:35 parallel)
$TriggerTime = "15:30"
$ParallelTriggerTime = "15:35"
$DaysOfWeek = @("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")

# 锁定文件路径
$LockFile = Join-Path $ProjectRoot "artifacts\backtest_archive\data_assets\.pipeline_lock"
$ParallelLockFile = Join-Path $ProjectRoot "artifacts\backtest_archive\data_assets\.parallel_global_lock"

# ------------------------------------------------------------------
# 检查环境
# ------------------------------------------------------------------
function Check-Prerequisites {
    Write-Host "=== DSHC Pipeline Schedule - Prerequisites ===" -ForegroundColor Cyan

    # 检查 Python
    try {
        $pyVer = & python --version 2>&1
        Write-Host "Python: $pyVer" -ForegroundColor Green
    }
    catch {
        Write-Host "ERROR: Python not found" -ForegroundColor Red
        return $false
    }

    # 检查脚本存在
    if (-not (Test-Path $ScriptPath)) {
        Write-Host "ERROR: Script not found: $ScriptPath" -ForegroundColor Red
        return $false
    }
    Write-Host "Script: $ScriptPath" -ForegroundColor Green

    # 检查调度配置
    $ConfigPath = Join-Path $ProjectRoot "artifacts\backtest_archive\data_assets\incr_pipeline_schedule_config.json"
    if (-not (Test-Path $ConfigPath)) {
        Write-Host "WARNING: Schedule config not found" -ForegroundColor Yellow
    }
    else {
        Write-Host "Config: $(Test-Path $ConfigPath)" -ForegroundColor Green
    }

    return $true
}

# ------------------------------------------------------------------
# 注册任务
# ------------------------------------------------------------------
function Register-Task {
    Write-Host "=== Registering Task: $TaskName (Mode: $Mode) ===" -ForegroundColor Cyan

    if (-not (Check-Prerequisites)) {
        Write-Host "Prerequisites check failed. Aborting." -ForegroundColor Red
        exit 1
    }

    # ── 串行任务 (DSHC-IncrPipelineDaily) ──
    if ($Mode -in @("serial", "dual")) {
        Register-SerialTask
    }

    # ── 并行任务 (DSHC-IncrPipelineParallel) ──
    if ($Mode -in @("parallel", "dual")) {
        Register-ParallelTask
    }
}

function Register-SerialTask {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "Serial task already exists. Removing..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }

    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
        -At "15:30"

    $settings = New-ScheduledTaskSettingsSet `
        -DontStopOnIdleEnd `
        -StartWhenAvailable `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -MultipleInstances IgnoreNew `
        -ExecutionTimeLimit (New-TimeSpan -Hours 1)

    $action = New-ScheduledTaskAction -Execute $PythonExe `
        -Argument $Arguments `
        -WorkingDirectory $ProjectRoot

    Register-ScheduledTask `
        -TaskName $TaskName `
        -TaskPath "\DSHC" `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "DSHC增量数据管道每日采集+合并+校验 (周一至周五15:30) [串行]" `
        -User "SYSTEM" `
        -RunLevel Highest `
        -Force

    Write-Host ""
    Write-Host "Serial task registered successfully!" -ForegroundColor Green
    Write-Host "  Name:    $TaskName"
    Write-Host "  Script:  $ScriptPath"
    Write-Host "  Args:    $Arguments"
    Write-Host "  Trigger: Weekdays 15:30"
    Write-Host "  Lock:    $LockFile"
    Write-Host ""
}

function Register-ParallelTask {
    $existing = Get-ScheduledTask -TaskName $ParallelTaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "Parallel task already exists. Removing..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $ParallelTaskName -Confirm:$false
    }

    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
        -At $ParallelTriggerTime

    $settings = New-ScheduledTaskSettingsSet `
        -DontStopOnIdleEnd `
        -StartWhenAvailable `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -MultipleInstances IgnoreNew `
        -ExecutionTimeLimit (New-TimeSpan -Hours 1)

    $action = New-ScheduledTaskAction -Execute $PythonExe `
        -Argument $ParallelArguments `
        -WorkingDirectory $ProjectRoot

    Register-ScheduledTask `
        -TaskName $ParallelTaskName `
        -TaskPath "\DSHC" `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "DSHC并行分片增量管道每日采集+合并+校验 (周一至周五15:35) [并行]" `
        -User "SYSTEM" `
        -RunLevel Highest `
        -Force

    Write-Host ""
    Write-Host "Parallel task registered successfully!" -ForegroundColor Green
    Write-Host "  Name:    $ParallelTaskName"
    Write-Host "  Script:  $ParallelScriptPath"
    Write-Host "  Args:    $ParallelArguments"
    Write-Host "  Trigger: Weekdays $ParallelTriggerTime"
    Write-Host "  Lock:    $ParallelLockFile"
    Write-Host ""
}

# ------------------------------------------------------------------
# 注销任务
# ------------------------------------------------------------------
function Unregister-Task {
    Write-Host "=== Unregistering Tasks (Mode: $Mode) ===" -ForegroundColor Cyan

    # ── 串行任务 ──
    if ($Mode -in @("serial", "dual")) {
        $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($existing) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Host "Serial task removed: $TaskName" -ForegroundColor Green
        }
        else {
            Write-Host "Serial task not found: $TaskName" -ForegroundColor Yellow
        }
    }

    # ── 并行任务 ──
    if ($Mode -in @("parallel", "dual")) {
        $existing = Get-ScheduledTask -TaskName $ParallelTaskName -ErrorAction SilentlyContinue
        if ($existing) {
            Unregister-ScheduledTask -TaskName $ParallelTaskName -Confirm:$false
            Write-Host "Parallel task removed: $ParallelTaskName" -ForegroundColor Green
        }
        else {
            Write-Host "Parallel task not found: $ParallelTaskName" -ForegroundColor Yellow
        }
    }
}

# ------------------------------------------------------------------
# 查看状态
# ------------------------------------------------------------------
function Get-TaskStatus {
    Write-Host "=== Task Status (Mode: $Mode) ===" -ForegroundColor Cyan

    # ── 串行任务状态 ──
    if ($Mode -in @("serial", "dual")) {
        Write-Host ""
        Write-Host "--- Serial Task: $TaskName ---"
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($task) {
            Write-Host "  Name:        $($task.TaskName)" -ForegroundColor Green
            Write-Host "  Path:        $($task.TaskPath)"
            Write-Host "  State:       $($task.State)"
            Write-Host "  Description: $($task.Description)"
            Write-Host ""
            Write-Host "  Triggers:"
            $task.Triggers | ForEach-Object {
                Write-Host "    - $($_.StartBoundary) ($($_.WeeksInterval))"
            }
            Write-Host ""
            Write-Host "  Actions:"
            $task.Actions | ForEach-Object {
                Write-Host "    - $($_.Execute) $($_.Arguments) (workdir: $($_.WorkingDirectory))"
            }
            Write-Host ""
            Write-Host "  Settings:"
            Write-Host "    MultipleInstances: $($task.Settings.MultipleInstances)"
            Write-Host "    ExecutionTimeLimit: $($task.Settings.ExecutionTimeLimit)"
        }
        else {
            Write-Host "Serial task not registered." -ForegroundColor Yellow
        }
    }

    # ── 并行任务状态 ──
    if ($Mode -in @("parallel", "dual")) {
        Write-Host ""
        Write-Host "--- Parallel Task: $ParallelTaskName ---"
        $task = Get-ScheduledTask -TaskName $ParallelTaskName -ErrorAction SilentlyContinue
        if ($task) {
            Write-Host "  Name:        $($task.TaskName)" -ForegroundColor Green
            Write-Host "  Path:        $($task.TaskPath)"
            Write-Host "  State:       $($task.State)"
            Write-Host "  Description: $($task.Description)"
            Write-Host ""
            Write-Host "  Triggers:"
            $task.Triggers | ForEach-Object {
                Write-Host "    - $($_.StartBoundary) ($($_.WeeksInterval))"
            }
            Write-Host ""
            Write-Host "  Actions:"
            $task.Actions | ForEach-Object {
                Write-Host "    - $($_.Execute) $($_.Arguments) (workdir: $($_.WorkingDirectory))"
            }
            Write-Host ""
            Write-Host "  Settings:"
            Write-Host "    MultipleInstances: $($task.Settings.MultipleInstances)"
            Write-Host "    ExecutionTimeLimit: $($task.Settings.ExecutionTimeLimit)"
        }
        else {
            Write-Host "Parallel task not registered." -ForegroundColor Yellow
        }
    }
}

# ------------------------------------------------------------------
# 主入口
# ------------------------------------------------------------------
switch ($Action) {
    "register"   { Register-Task }
    "unregister" { Unregister-Task }
    "status"     { Get-TaskStatus }
    default {
        Write-Host "Usage: .\incr_pipeline_schedule.ps1 [-Action register|unregister|status] [-Mode serial|parallel|dual]"
        Write-Host ""
        Write-Host "Actions:"
        Write-Host "  register    - 注册每日定时任务"
        Write-Host "  unregister  - 注销定时任务"
        Write-Host "  status      - 查看任务状态 (默认)"
        Write-Host ""
        Write-Host "Modes (default: serial):"
        Write-Host "  serial   - 仅注册串行任务 (DSHC-IncrPipelineDaily, 15:30)"
        Write-Host "  parallel - 仅注册并行任务 (DSHC-IncrPipelineParallel, 15:35)"
        Write-Host "  dual     - 同时注册串行+并行双链路 (互不干扰)"
    }
}
