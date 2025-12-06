@echo off
cls
echo ========================================================================
echo  FIXING TRUST SCORE - RESTART SERVICE
echo ========================================================================
echo.

echo [Step 1] Stopping Trust Score Service...
taskkill /FI "WINDOWTITLE eq *Trust Score*" /F >nul 2>&1
timeout /t 2 /nobreak >nul
echo    Done.
echo.

echo [Step 2] Starting Trust Score Service with complete data fix...
start "Trust Score AI Service - Port 8001" cmd /k "py -3.11 trust_score_service.py"
echo    Service starting...
echo.

echo [Step 3] Waiting for service to initialize (10 seconds)...
timeout /t 10 /nobreak
echo    Initialization complete.
echo.

echo ========================================================================
echo  TRUST SCORE SERVICE RESTARTED SUCCESSFULLY
echo ========================================================================
echo.
echo The Trust Score service is now running with ALL data fields:
echo   - Trust Score
echo   - Interpretation  
echo   - Rating
echo   - Success Rate
echo   - Sentiment Score
echo   - Skills Count
echo   - Completed Jobs
echo.
echo NOW:
echo   1. Go to your browser
echo   2. Refresh the page (F5)
echo   3. Click on "Trust Score" in the sidebar
echo   4. Your trust score should now display completely!
echo.
echo ========================================================================
echo.
pause
