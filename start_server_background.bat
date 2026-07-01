@echo off
REM Purchase Bot Server - Run in background
REM This keeps the bot running 24/7 on your laptop

echo.
echo ================================================================
echo  PURCHASE BOT - Starting in background mode
echo ================================================================
echo.

REM Activate local virtual environment
cd /d "%~dp0"
call venv\Scripts\activate.bat

REM Install dependencies if needed
echo [1/3] Installing dependencies...
python -m pip install -q -r requirements.txt

REM Create log file
if not exist "logs" mkdir logs
set LOGFILE=logs\server_%date:~-4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%.log

REM Start the server in a separate window
echo [2/3] Starting web server...
echo.
echo Server URL: http://localhost:8100
echo Logs: %LOGFILE%
echo.
echo [3/3] Opening browser...
timeout /t 2

REM Start server and log output
start "Purchase Bot Server" cmd /k "python -u server.py >> %LOGFILE% 2>&1"

REM Open browser
timeout /t 3
start http://localhost:8100

echo.
echo ================================================================
echo  Server started! Check the new window.
echo  To stop: Close the server window
echo ================================================================
echo.
pause
