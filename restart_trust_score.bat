@echo off
echo ========================================================================
echo  RESTARTING TRUST SCORE SERVICE WITH FIX
echo ========================================================================
echo.

echo Stopping any running Trust Score service...
taskkill /FI "WINDOWTITLE eq Trust Score*" /F >nul 2>&1

echo.
echo Starting Trust Score Service on Port 8001...
echo.

start "Trust Score AI Service - Port 8001 (FIXED)" cmd /k "py -3.11 trust_score_service.py"

echo.
echo ========================================================================
echo  Trust Score Service Restarted with Fix
echo ========================================================================
echo.
echo Wait 5-10 seconds for service to initialize, then refresh your browser.
echo.
pause
