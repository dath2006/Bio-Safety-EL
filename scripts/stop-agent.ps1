# Stop processes listening on the HACCP agent port (default 8000)
# Usage: .\scripts\stop-agent.ps1 [-Port 8000]

param([int]$Port = 8000)

Write-Host "Stopping listeners on port $Port..."

$pids = @(
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique
)

foreach ($procId in $pids) {
    if ($procId -and $procId -ne 0) {
        Write-Host "  Killing PID $procId"
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        taskkill /F /PID $procId 2>$null | Out-Null
    }
}

Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'main\.py|uvicorn' } |
    ForEach-Object {
        Write-Host "  Killing python PID $($_.ProcessId)"
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }

Start-Sleep -Seconds 2

$remaining = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($remaining) {
    Write-Host "WARNING: Port $Port still in use. Remaining PIDs:"
    $remaining | Select-Object OwningProcess -Unique | ForEach-Object { Write-Host "  PID $($_.OwningProcess)" }
    Write-Host "Try closing other terminals or reboot if processes are orphaned."
    exit 1
}

Write-Host "Port $Port is free."
