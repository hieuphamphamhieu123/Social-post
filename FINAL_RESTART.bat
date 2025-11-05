@echo off
echo ================================================================================
echo FINAL RESTART - Updated Formula with Variance
echo ================================================================================
echo.

echo [Step 1] Stopping all Python processes...
taskkill /F /IM python.exe 2>nul
timeout /t 3 /nobreak >nul

echo.
echo [Step 2] Starting API with new formula...
cd ai_market_analyzer
start "AI Market API - FINAL" cmd /k "python main.py"

echo.
echo [Step 3] Waiting 10 seconds for API to initialize...
timeout /t 10 /nobreak

echo.
echo [Step 4] Running verification test...
cd ..
python test_market_range_updates.py

echo.
echo ================================================================================
echo Test Complete! Check results above.
echo The market range should now be changing every second!
echo ================================================================================
pause
