# Start HACCP Agent API (Phase 1)
# Usage: .\scripts\start-agent.ps1 [-Ingest]

param([switch]$Ingest)

$Root = Split-Path -Parent $PSScriptRoot
$AgentDir = Join-Path $Root "apps\agent"
$Port = 8000

function Stop-ListenersOnPort {
    param([int]$TargetPort)

    $pids = @(
        Get-NetTCPConnection -LocalPort $TargetPort -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    )

    foreach ($procId in $pids) {
        if ($procId -and $procId -ne 0) {
            Write-Host "Stopping process on port ${TargetPort}: PID $procId"
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }

    if ($pids.Count -gt 0) {
        Start-Sleep -Seconds 2
    }
}

Set-Location $AgentDir

Stop-ListenersOnPort -TargetPort $Port

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
    .\.venv\Scripts\pip install -r requirements.txt -q
}

if ($Ingest) {
    Write-Host "Ingesting regulatory documents..."
    .\.venv\Scripts\python scripts\ingest.py
}

Write-Host "Starting FastAPI agent on http://localhost:${Port}"
Write-Host "API docs: http://localhost:${Port}/docs"
$env:AGENT_RELOAD = "false"
.\.venv\Scripts\python main.py
