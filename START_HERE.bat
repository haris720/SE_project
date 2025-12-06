@echo off
cls
echo.
echo ========================================================================
echo          MICROSERVICES ARCHITECTURE - STARTUP SCRIPT
echo ========================================================================
echo.
echo This script will start all 3 microservices in separate windows:
echo   1. Trust Score AI Service (Port 8001)
echo   2. Cost/Time Estimation Service (Port 8002)
echo   3. API Gateway / Web Application (Port 3000)
echo.
echo ========================================================================
echo.

REM Check if Python 3.11 is available
py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.11 not found!
    echo Please install Python 3.11 from python.org
    pause
    exit /b 1
)

echo [CHECK] Python 3.11 found
echo.

REM Check if httpx is installed
py -3.11 -m pip show httpx >nul 2>&1
if errorlevel 1 (
    echo [WARNING] httpx not installed. Installing now...
    py -3.11 -m pip install httpx
    echo.
)

echo [1/3] Starting Trust Score AI Service on Port 8001...
echo        Window will open in 3 seconds...
timeout /t 3 /nobreak >nul
start "Trust Score AI Service - Port 8001" cmd /k "py -3.11 trust_score_service.py"
echo [DONE] Trust Score Service starting...
echo.

echo [2/3] Waiting 7 seconds for Trust Score service to initialize...
timeout /t 7 /nobreak >nul
echo.

echo [2/3] Starting Cost/Time Estimation Service on Port 8002...
echo        Window will open in 2 seconds...
timeout /t 2 /nobreak >nul
start "Cost Time Estimation Service - Port 8002" cmd /k "py -3.11 cost_time_service_api.py"
echo [DONE] Cost/Time Service starting...
echo.

echo [3/3] Waiting 7 seconds for Cost/Time service to initialize...
timeout /t 7 /nobreak >nul
echo.

echo [3/3] Starting API Gateway / Web Application on Port 3000...
echo        Window will open in 2 seconds...
timeout /t 2 /nobreak >nul
start "Web Application - Port 3000" cmd /k "py -3.11 web_app.py"
echo [DONE] Web Application starting...
echo.

echo ========================================================================
echo                    ALL SERVICES STARTED!
echo ========================================================================
echo.
echo Please wait 10-15 seconds for all services to fully initialize.
echo.
echo Three windows have been opened:
echo   1. Trust Score AI Service (Port 8001)
echo   2. Cost/Time Estimation Service (Port 8002)
echo   3. Web Application (Port 3000)
echo.
echo Check each window for status messages:
echo   - Look for: "Uvicorn running on http://0.0.0.0:XXXX"
echo   - Make sure there are NO errors
echo.
echo ========================================================================
echo                       ACCESS YOUR APPLICATION
echo ========================================================================
echo.
echo Once all services show "Uvicorn running...", open your browser:
echo.
echo        http://localhost:3000
echo.
echo ========================================================================
echo                          TROUBLESHOOTING
echo ========================================================================
echo.
echo If you see errors:
echo   1. Close all 3 service windows
echo   2. Run this script again
echo   3. Wait for each service to fully start
echo.
echo To stop all services:
echo   - Close the 3 command windows
echo   - OR run: Stop-Process -Name python -Force
echo.
echo ========================================================================
echo.
echo Press any key to open browser (make sure services are running first)...
pause >nul

start http://localhost:3000

echo.
echo Browser opened. Services are still running in separate windows.
echo.
pause
