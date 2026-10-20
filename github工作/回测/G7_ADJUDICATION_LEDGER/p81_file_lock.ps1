#requires -Version 5.1
# ============================================================
# P81 File Lock Module
# Task: DSHD-TASK-040-WATCHER-FIX
# Token: DSHD-TASK040-TOKEN
# Mode: AUDIT_READ_ONLY | wind_api_calls=0
#
# Provides exclusive file locking with retry + timeout for
# PowerShell scripts that read/write shared files (cluster brief,
# tracking log, state JSONs).
#
# Safety:
#   - Zero Wind API calls
#   - Never modifies production data
#   - Read-only for all non-P80/P81 files
# ============================================================

# ============================================================
# Acquire-FileLock
# Acquires an exclusive file lock on the specified path.
# Returns: System.IO.FileStream (lock handle) or $null on failure
# ============================================================
function Acquire-FileLock {
    param(
        [string]$Path,
        [int]$TimeoutSec = 30,
        [int]$RetryDelayMs = 500
    )
    
    $elapsed = 0
    $lockHandle = $null
    
    while ($elapsed -lt $TimeoutSec) {
        try {
            $lockHandle = [System.IO.FileStream]::new(
                $Path,
                [System.IO.FileMode]::OpenOrCreate,
                [System.IO.FileAccess]::ReadWrite,
                [System.IO.FileShare]::None
            )
            return $lockHandle
        }
        catch {
            # Lock is held by another process, wait and retry
            Start-Sleep -Milliseconds $RetryDelayMs
            $elapsed = [int](($RetryDelayMs / 1000.0) * ([math]::Ceiling($elapsed / $RetryDelayMs)))
        }
    }
    
    # Timeout reached
    Write-Host "[FILELOCK-TIMEOUT] Cannot acquire lock on $Path after ${TimeoutSec}s" -ForegroundColor Yellow
    return $null
}

# ============================================================
# Release-FileLock
# Releases a file lock handle.
# ============================================================
function Release-FileLock {
    param($LockHandle)
    if ($null -ne $LockHandle) {
        try {
            $LockHandle.Close()
            $LockHandle.Dispose()
        }
        catch {
            Write-Host "[FILELOCK-ERROR] Cannot release lock: $_" -ForegroundColor Red
        }
    }
}

# ============================================================
# Write-FileWithLock
# Writes text content to a file with exclusive lock.
# Returns: $true on success, $false on failure.
# ============================================================
function Write-FileWithLock {
    param(
        [string]$Path,
        [string]$Text,
        [int]$TimeoutSec = 30
    )
    
    # Create parent directory if needed
    $dir = Split-Path -Path $Path -Parent
    if ($dir -and !(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    
    $lock = Acquire-FileLock -Path $Path -TimeoutSec $TimeoutSec
    if ($null -eq $lock) {
        Write-Host "[FILELOCK-FAIL] Write-FileWithLock: $Path" -ForegroundColor Red
        return $false
    }
    
    try {
        $enc = New-Object System.Text.UTF8Encoding($true)
        $bytes = $enc.GetBytes($Text)
        $lock.SetLength(0)
        $lock.Position = 0
        $lock.Write($bytes, 0, $bytes.Length)
        $lock.Flush()
        return $true
    }
    catch {
        Write-Host "[FILELOCK-ERROR] Write-FileWithLock $Path: $_" -ForegroundColor Red
        return $false
    }
    finally {
        Release-FileLock $lock
    }
}

# ============================================================
# Read-FileWithLock
# Reads text content from a file with exclusive lock.
# Returns: string content or $null on failure.
# ============================================================
function Read-FileWithLock {
    param(
        [string]$Path,
        [int]$TimeoutSec = 30
    )
    
    if (!(Test-Path $Path)) {
        return $null
    }
    
    $lock = Acquire-FileLock -Path $Path -TimeoutSec $TimeoutSec
    if ($null -eq $lock) {
        # Fallback: try reading without lock (shared read)
        try {
            $lock2 = [System.IO.FileStream]::new(
                $Path,
                [System.IO.FileMode]::Open,
                [System.IO.FileAccess]::Read,
                [System.IO.FileShare]::ReadWrite
            )
            try {
                $streamReader = New-Object System.IO.StreamReader($lock2)
                $content = $streamReader.ReadToEnd()
                return $content
            }
            finally {
                $lock2.Close()
            }
        }
        catch {
            Write-Host "[FILELOCK-FAIL] Read-FileWithLock: $Path (fallback also failed: $_)" -ForegroundColor Red
            return $null
        }
    }
    
    try {
        $enc = New-Object System.Text.UTF8Encoding($true)
        $streamReader = New-Object System.IO.StreamReader($lock, $enc)
        $content = $streamReader.ReadToEnd()
        return $content
    }
    catch {
        Write-Host "[FILELOCK-ERROR] Read-FileWithLock $Path: $_" -ForegroundColor Red
        return $null
    }
    finally {
        Release-FileLock $lock
    }
}

# ============================================================
# Append-FileWithLock
# Appends text content to a file with exclusive lock.
# Returns: $true on success, $false on failure.
# ============================================================
function Append-FileWithLock {
    param(
        [string]$Path,
        [string]$Text,
        [int]$TimeoutSec = 30
    )
    
    $lock = Acquire-FileLock -Path $Path -TimeoutSec $TimeoutSec
    if ($null -eq $lock) {
        Write-Host "[FILELOCK-FAIL] Append-FileWithLock: $Path" -ForegroundColor Red
        return $false
    }
    
    try {
        $enc = New-Object System.Text.UTF8Encoding($false)
        $bytes = $enc.GetBytes($Text)
        $lock.Position = $lock.Length
        $lock.Write($bytes, 0, $bytes.Length)
        $lock.Flush()
        return $true
    }
    catch {
        Write-Host "[FILELOCK-ERROR] Append-FileWithLock $Path: $_" -ForegroundColor Red
        return $false
    }
    finally {
        Release-FileLock $lock
    }
}

# ============================================================
# Get-MemoryUsageMB
# Returns current process memory usage in MB.
# ============================================================
function Get-MemoryUsageMB {
    try {
        $proc = Get-Process -Id $PID -ErrorAction Stop
        $memMB = $proc.WorkingSet64 / 1MB
        return [math]::Round($memMB, 1)
    }
    catch {
        return -1
    }
}

# ============================================================
# Check-MemoryThreshold
# Checks if current process memory exceeds threshold.
# Returns: $true if memory is within threshold, $false if exceeded.
# ============================================================
function Check-MemoryThreshold {
    param(
        [double]$ThresholdMB = 256.0
    )
    
    $memMB = Get-MemoryUsageMB
    if ($memMB -lt 0) {
        Write-Host "[MEMCHECK] Cannot determine memory usage" -ForegroundColor Yellow
        return $true  # Don't trigger restart on unknown memory
    }
    
    if ($memMB -gt $ThresholdMB) {
        Write-Host "[MEMCHECK] Memory usage ${memMB}MB exceeds threshold ${ThresholdMB}MB - soft restart recommended" -ForegroundColor Yellow
        return $false
    }
    
    return $true
}

# ============================================================
# Module metadata
# ============================================================
$Script:FileLockModule = @{
    module_name    = 'P81-FileLock'
    version        = '1.0.0'
    task           = 'DSHD-TASK-040-WATCHER-FIX'
    token          = 'DSHD-TASK040-TOKEN'
    wind_api_calls = 0
    gate           = 'CLOSED/HOLD'
    release_permit = 'NOT_ISSUED'
}

export-modulemember -function *