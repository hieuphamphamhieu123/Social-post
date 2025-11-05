@echo off
echo ================================================================================
echo Restarting Python API and Testing Market Range Updates
echo ================================================================================
echo.

echo [1/3] Stopping any existing Python API processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [2/3] Starting Python API server...
cd ai_market_analyzer
start "AI Market API" cmd /k "python main.py"
echo Waiting for API to start...
timeout /t 5 /nobreak >nul

echo.
echo [3/3] Running test script...
cd ..
python test_market_range_updates.py

echo.
echo ================================================================================
echo Test Complete! Check results above.
echo ================================================================================
pause
