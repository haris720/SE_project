@echo off
echo ========================================================================
echo  STARTING MICROSERVICES - Step by Step
echo ========================================================================
echo.

echo [1/3] Starting Trust Score AI Service (Port 8001)...
start "Trust Score Service" cmd /k "py -3.11 trust_score_service.py"
timeout /t 5 /nobreak > nul

echo [2/3] Starting Cost/Time Estimation Service (Port 8002)...
start "Cost Time Service" cmd /k "py -3.11 cost_time_service_api.py"
timeout /t 5 /nobreak > nul

echo [3/3] Starting API Gateway / Web Application (Port 3000)...
start "Web Application" cmd /k "py -3.11 web_app.py"
timeout /t 3 /nobreak > nul

echo.
echo ========================================================================
echo  ALL SERVICES STARTING IN SEPARATE WINDOWS
echo ========================================================================
echo.
echo Service URLs:
echo   - Trust Score AI: http://localhost:8001
echo   - Cost/Time Estimation: http://localhost:8002
echo   - Web Application: http://localhost:3000
echo.
echo Close the individual windows to stop each service
echo ========================================================================
echo.
pause
