param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$UseSqlite
)

$ErrorActionPreference = "Stop"

$serverRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $serverRoot

try {
    if ($UseSqlite -or [string]::IsNullOrWhiteSpace($env:DATABASE_URL)) {
        $env:DATABASE_URL = "sqlite+pysqlite:///./runtime.db"
        Write-Host "[start_backend] DATABASE_URL is not set; using SQLite: $($env:DATABASE_URL)" -ForegroundColor Yellow
    }

    if ($env:CONDA_DEFAULT_ENV -ne "kpforu-server") {
        Write-Host "[start_backend] Current conda env is not kpforu-server (current: '$($env:CONDA_DEFAULT_ENV)')." -ForegroundColor Yellow
        Write-Host "[start_backend] Recommended: conda activate kpforu-server" -ForegroundColor Yellow
    }

    $preferredPython = "C:/Users/wwwsh/.conda/envs/kpforu-server/python.exe"
    $pythonCmd = $null
    if (Test-Path $preferredPython) {
        $pythonCmd = $preferredPython
    } elseif (Get-Command "python" -ErrorAction SilentlyContinue) {
        $pythonCmd = "python"
    }

    if (-not $pythonCmd) {
        throw "Python executable not found. Activate kpforu-server or update preferredPython in start_backend.ps1."
    }

    $pythonResolved = if ($pythonCmd -eq "python") { (Get-Command "python").Source } else { $pythonCmd }
    Write-Host "[start_backend] Python: $pythonResolved" -ForegroundColor Cyan
    Write-Host "[start_backend] Starting server on http://$BindHost`:$Port" -ForegroundColor Green

    & $pythonCmd -m uvicorn app.main:app --host $BindHost --port $Port
}
finally {
    Pop-Location
}
