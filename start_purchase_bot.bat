@echo off
REM Purchase Bot Starter Script for Windows Task Scheduler
REM
REM Instructions:
REM 1. Edit the path below to match your installation directory
REM 2. Save this file as start_purchase_bot.bat
REM 3. Use Windows Task Scheduler to run this file at desired times

REM Set your purchase-bot directory here
set PURCHASE_BOT_DIR=C:\Users\r0v0038\Documents\puppy_workspace\purchase-bot

REM Navigate to the directory
cd /d %PURCHASE_BOT_DIR%

REM Run the scheduler
REM Swap to --dry-run to test without completing real purchases
python main.py run

REM Keep window open if there's an error
pause
