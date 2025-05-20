# PowerShell setup script for CircuitMCP
# Installs all requirements and configures the environment

# Define colors for output
$Green = 'Green'
$Yellow = 'Yellow'
$Blue = 'Cyan'
$Red = 'Red'
$ResetColor = 'White'

# Print header
Write-Host "======================================================" -ForegroundColor $Blue
Write-Host "     CircuitMCP Setup Script (PowerShell)              " -ForegroundColor $Blue
Write-Host "======================================================" -ForegroundColor $Blue
Write-Host "This script will install CircuitMCP and all dependencies." -ForegroundColor $Green
Write-Host ""

# Function to check command existence
function Test-CommandExists {
    param ($command)
    $exists = $null -ne (Get-Command $command -ErrorAction SilentlyContinue)
    return $exists
}

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor $Yellow
if (Test-CommandExists "python") {
    $pythonVersion = & python --version 2>&1
    $pythonVersion = $pythonVersion -replace "Python ", ""
    Write-Host "Python version: $pythonVersion" -ForegroundColor $Green
    
    # Check if Python version is 3.9 or higher
    $versionParts = $pythonVersion.Split(".")
    $majorVersion = [int]$versionParts[0]
    $minorVersion = [int]$versionParts[1]
    
    if (($majorVersion -lt 3) -or (($majorVersion -eq 3) -and ($minorVersion -lt 9))) {
        Write-Host "Error: Python 3.9 or higher is required." -ForegroundColor $Red
        exit 1
    }
} else {
    Write-Host "Error: Python not found. Please install Python 3.9 or higher." -ForegroundColor $Red
    exit 1
}

# Ask about NGSpice
Write-Host "NGSpice is required for circuit simulation." -ForegroundColor $Yellow
Write-Host "Please download and install NGSpice from: http://ngspice.sourceforge.net/download.html" -ForegroundColor $Yellow
Write-Host "Press any key when NGSpice is installed..." -ForegroundColor $Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Ask about virtual environment
Write-Host ""
$createVenv = Read-Host "Would you like to create a virtual environment? (y/n)"
if ($createVenv -eq "y" -or $createVenv -eq "Y") {
    Write-Host "Creating virtual environment..." -ForegroundColor $Yellow
    
    # Check if pip is installed
    if (-not (Test-CommandExists "pip")) {
        Write-Host "Error: pip not found. Please install pip." -ForegroundColor $Red
        exit 1
    }
    
    pip install virtualenv
    
    if (Test-Path "venv") {
        Write-Host "Virtual environment already exists. Activating it..." -ForegroundColor $Yellow
    } else {
        python -m virtualenv venv
        Write-Host "Virtual environment created." -ForegroundColor $Green
    }
    
    # Activate virtual environment
    & .\venv\Scripts\Activate.ps1
    Write-Host "Virtual environment activated." -ForegroundColor $Green
}

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor $Yellow
pip install -r requirements.txt

# Install CircuitMCP in development mode
Write-Host "Installing CircuitMCP in development mode..." -ForegroundColor $Yellow
pip install -e .

# Check if UVX exists and install CircuitMCP with UVX if available
if (Test-CommandExists "uvx") {
    Write-Host "Installing CircuitMCP with UVX..." -ForegroundColor $Yellow
    uvx install -y (Get-Location)
    Write-Host "CircuitMCP installed with UVX." -ForegroundColor $Green
} else {
    Write-Host "UVX not found. Skipping UVX installation." -ForegroundColor $Yellow
    Write-Host "To install with UVX later, run: uvx install git+https://github.com/amzsaint/circuitmcp.git" -ForegroundColor $Yellow
}

# Create schematics directory if it doesn't exist
if (-not (Test-Path "schematics")) {
    New-Item -ItemType Directory -Path "schematics" | Out-Null
}

# Run a simple test to verify installation
Write-Host "Running a simple test to verify installation..." -ForegroundColor $Yellow
$testResult = $null
try {
    $testResult = python -c "from circuitmcp import Circuit, mcp; print('Circuit class imported successfully'); print(f'Version: {mcp.__version__ if hasattr(mcp, \"__version__\") else \"0.1.0\"}')"
    $testSuccess = $true
} catch {
    $testSuccess = $false
}

# Check if the test was successful
if ($testSuccess) {
    Write-Host "CircuitMCP installation successful!" -ForegroundColor $Green
} else {
    Write-Host "There was an issue with the CircuitMCP installation." -ForegroundColor $Red
    exit 1
}

# Print usage instructions
Write-Host "======================================================" -ForegroundColor $Blue
Write-Host "CircuitMCP has been successfully installed." -ForegroundColor $Green
Write-Host "======================================================" -ForegroundColor $Blue
Write-Host "To use CircuitMCP:" -ForegroundColor $Yellow
Write-Host "  1. Run the server:" -ForegroundColor $Blue
Write-Host "     circuitmcp-server" -ForegroundColor $Green
Write-Host ""
Write-Host "  2. In Python:" -ForegroundColor $Blue
Write-Host "     from circuitmcp import mcp, Circuit" -ForegroundColor $Green
Write-Host ""
Write-Host "  3. With Claude Desktop:" -ForegroundColor $Blue
Write-Host "     .\examples\claude_desktop_demo.sh" -ForegroundColor $Green
Write-Host "     (Note: You may need to run this script using Git Bash on Windows)" -ForegroundColor $Yellow
Write-Host ""
Write-Host "  4. Run the example:" -ForegroundColor $Blue
Write-Host "     python examples\uvx_demo.py" -ForegroundColor $Green
Write-Host ""
Write-Host "======================================================" -ForegroundColor $Blue

if ($createVenv -eq "y" -or $createVenv -eq "Y") {
    Write-Host "Note: You're using a virtual environment. To use CircuitMCP in the future, activate it with:" -ForegroundColor $Yellow
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor $Green
}

Write-Host "======================================================" -ForegroundColor $Blue

# Keep the window open if script was executed directly
Write-Host ""
Write-Host "Setup complete. Press any key to exit..." -ForegroundColor $Green
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 