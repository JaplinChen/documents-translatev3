param(
    [string]$RepoPath = (Get-Location).Path,
    [string]$Branch = 'main',
    [int]$IntervalSeconds = 60,
    [string]$LogPath = ''
)

if (-not $LogPath) {
    $LogPath = Join-Path $RepoPath 'logs/watch_update.log'
}

New-Item -ItemType Directory -Force -Path (Split-Path $LogPath) | Out-Null

$lockFile = Join-Path $RepoPath 'data/.update.lock'
$lastHashFile = Join-Path $RepoPath 'data/.last_update_hash'

function Write-Log([string]$message) {
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    "$ts $message" | Out-File -FilePath $LogPath -Append -Encoding utf8
}

function Git-Has-Changes {
    $status = git -C $RepoPath status --porcelain
    return -not [string]::IsNullOrWhiteSpace($status)
}

Write-Log "watch_update started. Repo=$RepoPath Branch=$Branch Interval=${IntervalSeconds}s"

while ($true) {
    try {
        if (Test-Path $lockFile) {
            Write-Log 'update lock exists, skip this cycle.'
        } elseif (Git-Has-Changes) {
            Write-Log 'working tree dirty, skip update.'
        } else {
            git -C $RepoPath fetch origin $Branch | Out-Null
            $remote = git -C $RepoPath rev-parse "origin/$Branch"
            $local = git -C $RepoPath rev-parse "HEAD"

            if ($remote -ne $local) {
                Set-Content -Path $lockFile -Value (Get-Date -Format o)
                Write-Log "update detected. local=$local remote=$remote"

                git -C $RepoPath pull origin $Branch | Out-Null
                docker compose -f (Join-Path $RepoPath 'docker-compose.yml') build
                docker compose -f (Join-Path $RepoPath 'docker-compose.yml') up -d

                Set-Content -Path $lastHashFile -Value $remote
                Write-Log "update complete. new=$remote"
                Remove-Item $lockFile -ErrorAction SilentlyContinue
            }
        }
    } catch {
        Write-Log ("error: " + $_.Exception.Message)
        Remove-Item $lockFile -ErrorAction SilentlyContinue
    }

    Start-Sleep -Seconds $IntervalSeconds
}
