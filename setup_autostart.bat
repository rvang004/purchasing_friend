@echo off
REM Setup Purchase Bot to run on Windows startup
REM Run this as Administrator

echo.
echo ================================================================
echo  Setting up Purchase Bot to run at Windows startup
echo ================================================================
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must run as Administrator!
    echo.
    echo Right-click this file and select "Run as administrator"
    pause
    exit /b 1
)

set BOT_DIR=%~dp0
set BATCH_FILE=%BOT_DIR%start_server_background.bat
set TASK_NAME=PurchaseBot-Server

echo [1/2] Creating Windows Task...

REM Delete old task if it exists
taskkill /f /im cmd.exe /fi "windowtitle eq Purchase Bot Server" >nul 2>&1
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

REM Create new scheduled task to run at startup
schtasks /create /tn "%TASK_NAME%" ^
    /tr "%BATCH_FILE%" ^
    /sc onstart ^
    /ru "%USERNAME%" ^
    /rl highest ^
    /f

if %errorLevel% equ 0 (
    echo [OK] Task created successfully!
    echo.
    echo [2/2] Test: Starting bot now...
    timeout /t 2
    call "%BATCH_FILE%"
) else (
    echo [ERROR] Failed to create task
    pause
    exit /b 1
)

echo.
echo ================================================================
echo  Setup complete!
echo ================================================================
echo.
echo Your Purchase Bot will now:
echo  - Start automatically when you login
echo  - Run in a background window
echo  - Log all activity to logs\ folder
echo.
echo To stop the bot: Close the "Purchase Bot Server" window
echo To view logs: Check logs\ folder
echo To uninstall: Run 'schtasks /delete /tn PurchaseBot-Server /f'
echo.
pause
