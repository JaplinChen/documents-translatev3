param(
    [int]$DebounceSeconds = 2
)

$root = Split-Path -Parent $PSScriptRoot

$ignorePatterns = @(
    "\\.git\\",
    "\\.worktrees\\",
    "\\node_modules\\",
    "\\dist\\",
    "\\build\\",
    "\\__pycache__\\",
    "\\.pytest_cache\\",
    "\\.venv\\",
    "\\data\\",
    "\\logs\\"
)

function Should-IgnorePath([string]$path) {
    foreach ($pattern in $ignorePatterns) {
        if ($path -match $pattern) { return $true }
    }
    return $false
}

$timer = New-Object System.Timers.Timer
$timer.Interval = [Math]::Max(500, $DebounceSeconds * 1000)
$timer.AutoReset = $false

Register-ObjectEvent -InputObject $timer -EventName Elapsed -Action {
    Write-Host "[auto-docker] 偵測到變更，開始重建容器..."
    try {
        docker compose up -d --build | Write-Host
        Write-Host "[auto-docker] 完成。"
    } catch {
        Write-Host "[auto-docker] 失敗：$($_.Exception.Message)"
    }
} | Out-Null

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $root
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

$handler = {
    if (Should-IgnorePath $EventArgs.FullPath) { return }
    $timer.Stop()
    $timer.Start()
}

Register-ObjectEvent -InputObject $watcher -EventName Changed -Action $handler | Out-Null
Register-ObjectEvent -InputObject $watcher -EventName Created -Action $handler | Out-Null
Register-ObjectEvent -InputObject $watcher -EventName Deleted -Action $handler | Out-Null
Register-ObjectEvent -InputObject $watcher -EventName Renamed -Action $handler | Out-Null

Write-Host "[auto-docker] 監聽中：$root"
Write-Host "[auto-docker] Debounce: ${DebounceSeconds}s"

while ($true) {
    Start-Sleep -Seconds 1
}
