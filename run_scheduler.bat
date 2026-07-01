@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo.
echo ================================================================
echo  PURCHASE BOT SCHEDULER - Running
echo ================================================================
echo.
echo This window monitors your purchase tasks and executes them.
echo.
echo To stop: Press CTRL+C
echo.
echo ================================================================
echo.
python main.py run --interval 60
pause
