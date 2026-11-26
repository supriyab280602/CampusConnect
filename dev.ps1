$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$PythonExe = Join-Path $BackendDir "venv\Scripts\python.exe"
$BackendScript = Join-Path $BackendDir "run.py"
$HealthUrl = "http://127.0.0.1:5000/api/v1/health"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Virtual environment python not found at $PythonExe"
    exit 1
}

if (-not (Test-Path $BackendScript)) {
    Write-Error "Backend entrypoint not found at $BackendScript"
    exit 1
}

# Prevent launching a duplicate backend process if port 5000 is already in use
$ExistingListener = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($ExistingListener) {
    Write-Error "Port 5000 is already in use by PID $($ExistingListener.OwningProcess). Stop the existing process before running dev.ps1."
    exit 1
}

$BackendStdout = [System.IO.Path]::GetTempFileName()
$BackendStderr = [System.IO.Path]::GetTempFileName()
$BackendProc = $null

function Stop-BackendProcess {
    if ($script:BackendProc -and -not $script:BackendProc.HasExited) {
        Write-Host "`nStopping Backend server (PID $($script:BackendProc.Id))..." -ForegroundColor Yellow
        & taskkill /PID $script:BackendProc.Id /T /F 2>$null | Out-Null
        if (-not $script:BackendProc.HasExited) {
            Stop-Process -Id $script:BackendProc.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Remove-Item -Path $script:BackendStdout, $script:BackendStderr -Force -ErrorAction SilentlyContinue
}

try {
    Write-Host "Starting CampusConnect Backend (http://127.0.0.1:5000)..." -ForegroundColor Cyan
    $BackendProc = Start-Process `
        -FilePath $PythonExe `
        -ArgumentList "`"$BackendScript`"" `
        -WorkingDirectory $BackendDir `
        -RedirectStandardOutput $BackendStdout `
        -RedirectStandardError $BackendStderr `
        -PassThru `
        -NoNewWindow

    # Wait for backend health endpoint before starting frontend
    $BackendReady = $false
    for ($i = 0; $i -lt 30; $i++) {
        if ($BackendProc.HasExited) {
            $ErrText = (Get-Content -Path $BackendStderr -Raw -ErrorAction SilentlyContinue)
            $OutText = (Get-Content -Path $BackendStdout -Raw -ErrorAction SilentlyContinue)
            Write-Error "Backend exited prematurely with code $($BackendProc.ExitCode).`nSTDERR:`n$ErrText`nSTDOUT:`n$OutText"
            exit 1
        }

        try {
            $Health = Invoke-RestMethod -Uri $HealthUrl -Method Get -TimeoutSec 2 -ErrorAction Stop
            if ($Health.success -eq $true -and $Health.data.status -eq "healthy") {
                $BackendReady = $true
                break
            }
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }

    if (-not $BackendReady) {
        $ErrText = (Get-Content -Path $BackendStderr -Raw -ErrorAction SilentlyContinue)
        Write-Error "Backend failed to become healthy at $HealthUrl within 15 seconds.`nSTDERR:`n$ErrText"
        exit 1
    }

    Write-Host "Backend is healthy at $HealthUrl" -ForegroundColor Cyan
    Write-Host "Starting CampusConnect Frontend (http://localhost:5173)..." -ForegroundColor Green

    Push-Location $RootDir
    try {
        npm --prefix $FrontendDir run dev
    } finally {
        Pop-Location
    }
} finally {
    Stop-BackendProcess
}
