@echo off
echo Starting AI Market Range Analyzer API...
echo.

REM Activate virtual environment if exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Start API
python main.py api

pause
