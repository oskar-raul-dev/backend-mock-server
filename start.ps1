# Mock Server Startup Script for Windows PowerShell
# Usage: .\start.ps1 <mock_name> [options]
# Example: .\start.ps1 backend --port 8080 --log-level DEBUG
# Help: .\start.ps1 --help

param(
    [Parameter(Position=0)]
    [string]$MockName,

    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$ExtraArgs
)

$ErrorActionPreference = "Stop"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Function to list available mocks
function Get-AvailableMocks {
    $mocks = Get-ChildItem -Path "$ScriptDir\mocks" -Directory -ErrorAction SilentlyContinue
    if ($mocks) {
        $mocks | ForEach-Object { Write-Host "  $($_.Name)" }
    } else {
        Write-Host "  (none found)"
    }
}

# Check for help flag
if ($MockName -eq "--help" -or $MockName -eq "-h" -or ($ExtraArgs -contains "--help") -or ($ExtraArgs -contains "-h")) {
    Write-Host "Mock Server Startup Script"
    Write-Host ""
    Write-Host "Usage: .\start.ps1 <mock_name> [options]"
    Write-Host ""
    Write-Host "Arguments:"
    Write-Host "  mock_name    Name of the mock configuration directory in mocks/"
    Write-Host ""
    Write-Host "Available mocks:"
    Get-AvailableMocks
    Write-Host ""
    Write-Host "Server options (passed to main.py):"
    Write-Host ""

    # Activate venv and show main.py help
    $VenvActivate = Join-Path $ScriptDir "venv\Scripts\Activate.ps1"
    if (Test-Path $VenvActivate) {
        & $VenvActivate
    }
    Set-Location "$ScriptDir\server"
    python main.py --help
    exit 0
}

# Validate mock name
if ([string]::IsNullOrEmpty($MockName)) {
    Write-Host "Error: Mock name is required" -ForegroundColor Red
    Write-Host "Usage: .\start.ps1 <mock_name> [options]"
    Write-Host ""
    Write-Host "Available mocks:"
    Get-AvailableMocks
    Write-Host ""
    Write-Host "Use .\start.ps1 --help for more information"
    exit 1
}

# Check if mock directory exists
$MockDir = Join-Path $ScriptDir "mocks\$MockName"
if (-not (Test-Path $MockDir -PathType Container)) {
    Write-Host "Error: Mock directory not found: $MockDir" -ForegroundColor Red
    Write-Host ""
    Write-Host "Available mocks:"
    Get-AvailableMocks
    exit 1
}

# Activate virtual environment
$VenvActivate = Join-Path $ScriptDir "venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    Write-Host "Activating virtual environment..."
    & $VenvActivate
} else {
    Write-Host "Warning: Virtual environment not found. Run: python -m venv venv; pip install -r requirements.txt" -ForegroundColor Yellow
}

# Start the mock server
Write-Host "Starting mock server for '$MockName'..." -ForegroundColor Cyan
Write-Host "Config directory: $MockDir"
Write-Host ""

Set-Location "$ScriptDir\server"

# Build arguments array
$Arguments = @(
    "main.py",
    "--config-dir", $MockDir,
    "--endpoints-file", "endpoints.py",
    "--config-file", "config.py"
)

# Add extra arguments if provided
if ($ExtraArgs) {
    $Arguments += $ExtraArgs
}

# Run python with all arguments
& python $Arguments
