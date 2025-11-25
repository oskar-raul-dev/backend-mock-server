@echo off
REM Mock Server Startup Script for Windows CMD
REM Usage: start.bat <mock_name> [options]
REM Example: start.bat backend --port 8080 --log-level DEBUG
REM Help: start.bat --help

setlocal enabledelayedexpansion

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Check for help flag first
if "%~1"=="--help" goto :showhelp
if "%~1"=="-h" goto :showhelp

REM Get mock name (first argument)
set "MOCK_NAME=%~1"

REM Validate mock name
if "%MOCK_NAME%"=="" (
    echo Error: Mock name is required
    echo Usage: start.bat ^<mock_name^> [options]
    echo.
    echo Available mocks:
    for /d %%d in ("%SCRIPT_DIR%\mocks\*") do echo   %%~nxd
    echo.
    echo Use start.bat --help for more information
    exit /b 1
)

REM Check if mock directory exists
set "MOCK_DIR=%SCRIPT_DIR%\mocks\%MOCK_NAME%"
if not exist "%MOCK_DIR%" (
    echo Error: Mock directory not found: %MOCK_DIR%
    echo.
    echo Available mocks:
    for /d %%d in ("%SCRIPT_DIR%\mocks\*") do echo   %%~nxd
    exit /b 1
)

REM Shift arguments to remove mock name
shift

REM Build remaining arguments
set "EXTRA_ARGS="
:buildargs
if "%~1"=="" goto :endargs
set "EXTRA_ARGS=%EXTRA_ARGS% %1"
shift
goto :buildargs
:endargs

REM Activate virtual environment
if exist "%SCRIPT_DIR%\venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call "%SCRIPT_DIR%\venv\Scripts\activate.bat"
) else (
    echo Warning: Virtual environment not found. Run: python -m venv venv ^&^& pip install -r requirements.txt
)

REM Start the mock server
echo Starting mock server for '%MOCK_NAME%'...
echo Config directory: %MOCK_DIR%
echo.

cd /d "%SCRIPT_DIR%\server"
python main.py --config-dir "%MOCK_DIR%" --endpoints-file endpoints.py --config-file config.py %EXTRA_ARGS%
goto :eof

:showhelp
echo Mock Server Startup Script
echo.
echo Usage: start.bat ^<mock_name^> [options]
echo.
echo Arguments:
echo   mock_name    Name of the mock configuration directory in mocks/
echo.
echo Available mocks:
for /d %%d in ("%SCRIPT_DIR%\mocks\*") do echo   %%~nxd
echo.
echo Server options (passed to main.py):
echo.
REM Activate venv and show main.py help
if exist "%SCRIPT_DIR%\venv\Scripts\activate.bat" (
    call "%SCRIPT_DIR%\venv\Scripts\activate.bat"
)
cd /d "%SCRIPT_DIR%\server"
python main.py --help
exit /b 0
