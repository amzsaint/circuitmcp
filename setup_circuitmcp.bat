@echo off
REM Setup script for CircuitMCP on Windows
REM Installs all requirements and configures the environment

echo ======================================================
echo     CircuitMCP Setup Script for Windows
echo ======================================================
echo This script will install CircuitMCP and all dependencies.
echo.

REM Check Python version
echo Checking Python version...
python --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python not found. Please install Python 3.9 or higher.
    exit /b 1
)

REM Check if Python version is 3.9 or higher
for /f "tokens=2" %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

if %PYTHON_MAJOR% LSS 3 (
    echo Error: Python 3.9 or higher is required.
    exit /b 1
)

if %PYTHON_MAJOR% EQU 3 (
    if %PYTHON_MINOR% LSS 9 (
        echo Error: Python 3.9 or higher is required.
        exit /b 1
    )
)

echo Python version: %PYTHON_VERSION%
echo.

REM Ask about NGSpice
echo NGSpice is required for circuit simulation.
echo Please download and install NGSpice from: http://ngspice.sourceforge.net/download.html
echo Press any key when NGSpice is installed...
pause > nul

REM Ask about virtual environment
echo.
set /p CREATE_VENV=Would you like to create a virtual environment? (y/n): 

if /i "%CREATE_VENV%"=="y" (
    echo Creating virtual environment...
    
    REM Check if pip is installed
    pip --version > nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo Error: pip not found. Please install pip.
        exit /b 1
    )
    
    pip install virtualenv
    
    if exist "venv" (
        echo Virtual environment already exists. Activating it...
    ) else (
        python -m virtualenv venv
        echo Virtual environment created.
    )
    
    REM Activate virtual environment
    call venv\Scripts\activate.bat
    echo Virtual environment activated.
)

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

REM Install CircuitMCP in development mode
echo Installing CircuitMCP in development mode...
pip install -e .

REM Check if UVX exists and install CircuitMCP with UVX if available
where uvx > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Installing CircuitMCP with UVX...
    uvx install -y "%CD%"
    echo CircuitMCP installed with UVX.
) else (
    echo UVX not found. Skipping UVX installation.
    echo To install with UVX later, run: uvx install git+https://github.com/amzsaint/circuitmcp.git
)

REM Create schematics directory if it doesn't exist
if not exist "schematics" mkdir schematics

REM Run a simple test to verify installation
echo Running a simple test to verify installation...
python -c "from circuitmcp import Circuit, mcp; print('Circuit class imported successfully'); print(f'Version: {mcp.__version__ if hasattr(mcp, \"__version__\") else \"0.1.0\"}')"

REM Check if the test was successful
if %ERRORLEVEL% EQU 0 (
    echo CircuitMCP installation successful!
) else (
    echo There was an issue with the CircuitMCP installation.
    exit /b 1
)

REM Print usage instructions
echo ======================================================
echo CircuitMCP has been successfully installed.
echo ======================================================
echo To use CircuitMCP:
echo   1. Run the server:
echo      circuitmcp-server
echo.
echo   2. In Python:
echo      from circuitmcp import mcp, Circuit
echo.
echo   3. With Claude Desktop:
echo      examples\claude_desktop_demo.sh
echo      (Note: You may need to run this script using Git Bash on Windows)
echo.
echo   4. Run the example:
echo      python examples\uvx_demo.py
echo.
echo ======================================================

if /i "%CREATE_VENV%"=="y" (
    echo Note: You're using a virtual environment. To use CircuitMCP in the future, activate it with:
    echo   venv\Scripts\activate.bat
)

echo ======================================================

REM Keep the window open if double-clicked
echo.
echo Setup complete. Press any key to exit...
pause > nul 