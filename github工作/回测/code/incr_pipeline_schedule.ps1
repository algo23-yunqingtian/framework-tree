# ============================================================================
# DSHC-DATA-INCR-SCHEDULE-ROLLBACK · Windows 任务计划程序注册脚本
# 工单: DSHC-DATA-INCR-SCHEDULE-ROLLBACK
# 令牌: DSHC-DATA-INCR-SCHEDULE-TOKEN
#
# 功能: 注册增量管道每日定时任务 (周一至周五 15:30)
# 用法: .\code\incr_pipeline_schedule.ps1 [-Register] [-Unregister] [-Status]
# ============================================================================

param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("register", "unregister", "status")]
    [string]$Action = "status"
)

$ErrorActionPreference = "Stop"

# 任务名称
$TaskName = "DSHC-IncrPipelineDaily"

# 脚本路径 (相对于项目根目录)
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ScriptPath = Join-Path $ProjectRoot "code\incr_pipeline_daily.py"

# Python 路径
$PythonExe = "python"

# 执行参数
$Arguments = "--execute"

# 触发时间 (周一至周五 15:30)
$TriggerTime = "15:30"
$DaysOfWeek = @("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")

# 锁定文件路径
$LockFile = Join-Path $ProjectRoot "artifacts\backtest_archive\data_assets\.pipeline_lock"

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
    Write-Host "=== Registering Task: $TaskName ===" -ForegroundColor Cyan

    if (-not (Check-Prerequisites)) {
        Write-Host "Prerequisites check failed. Aborting." -ForegroundColor Red
        exit 1
    }

    # 如果任务已存在, 先删除
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "Task already exists. Removing..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }

    # 创建触发器 (周一至周五 15:30)
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
        -At "15:30"

    # 创建设置 (单实例)
    $settings = New-ScheduledTaskSettingsSet `
        -DontStopOnIdleEnd `
        -StartWhenAvailable `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -MultipleInstances IgnoreNew `
        -ExecutionTimeLimit (New-TimeSpan -Hours 1)

    # 创建执行动作
    $action = New-ScheduledTaskAction -Execute $PythonExe `
        -Argument $Arguments `
        -WorkingDirectory $ProjectRoot

    # 注册任务
    Register-ScheduledTask `
        -TaskName $TaskName `
        -TaskPath "\DSHC" `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "DSHC增量数据管道每日采集+合并+校验 (周一至周五15:30)" `
        -User "SYSTEM" `
        -RunLevel Highest `
        -Force

    Write-Host ""
    Write-Host "Task registered successfully!" -ForegroundColor Green
    Write-Host "  Name:    $TaskName"
    Write-Host "  Script:  $ScriptPath"
    Write-Host "  Args:    $Arguments"
    Write-Host "  Trigger: Weekdays 15:30"
    Write-Host "  Single:  Instance (IgnoreNew)"
    Write-Host "  Lock:    $LockFile"
    Write-Host ""
}

# ------------------------------------------------------------------
# 注销任务
# ------------------------------------------------------------------
function Unregister-Task {
    Write-Host "=== Unregistering Task: $TaskName ===" -ForegroundColor Cyan
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Task removed: $TaskName" -ForegroundColor Green
    }
    else {
        Write-Host "Task not found: $TaskName" -ForegroundColor Yellow
    }
}

# ------------------------------------------------------------------
# 查看状态
# ------------------------------------------------------------------
function Get-TaskStatus {
    Write-Host "=== Task Status: $TaskName ===" -ForegroundColor Cyan
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
        Write-Host "Task not registered." -ForegroundColor Yellow
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
        Write-Host "Usage: .\incr_pipeline_schedule.ps1 [-Action register|unregister|status]"
        Write-Host ""
        Write-Host "Actions:"
        Write-Host "  register    - 注册每日定时任务 (周一至周五15:30)"
        Write-Host "  unregister  - 注销定时任务"
        Write-Host "  status      - 查看任务状态 (默认)"
    }
}
