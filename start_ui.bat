@echo off
setlocal EnableDelayedExpansion

title Purchase Bot UI
echo.
echo  ==========================================
echo   🛒  Purchase Bot — Web UI Setup
echo  ==========================================
echo.

:: ── locate ourselves ──────────────────────────────────────────────────────
set "BOT_DIR=%~dp0"
cd /d "%BOT_DIR%"

:: ── find uv or python ─────────────────────────────────────────────────────
where uv >nul 2>&1
if %ERRORLEVEL% == 0 (
    set "USE_UV=1"
    echo [OK] uv found
) else (
    set "USE_UV=0"
    where python >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [ERR] Neither uv nor python found on PATH.
        echo       Install Python from https://python.org and try again.
        pause & exit /b 1
    )
    echo [OK] python found
)

:: ── create local venv if missing ──────────────────────────────────────────
if not exist "venv\Scripts\python.exe" (
    echo [..] Creating virtual environment...
    if "%USE_UV%"=="1" (
        uv venv venv --quiet
    ) else (
        python -m venv venv
    )
    if %ERRORLEVEL% NEQ 0 (
        echo [ERR] Failed to create venv.
        pause & exit /b 1
    )
    echo [OK] Virtual environment created
)

set "PYTHON=venv\Scripts\python.exe"

:: ── install / sync dependencies ───────────────────────────────────────────
echo [..] Installing dependencies...
if "%USE_UV%"=="1" (
    uv pip install -r requirements.txt ^
        --python venv\Scripts\python.exe ^
        --index-url https://pypi.ci.artifacts.walmart.com/artifactory/api/pypi/external-pypi/simple ^
        --allow-insecure-host pypi.ci.artifacts.walmart.com ^
        --quiet
) else (
    venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
)
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Some packages may not have installed — continuing anyway.
)
echo [OK] Dependencies ready

:: ── launch ────────────────────────────────────────────────────────────────
echo.
echo  Starting Purchase Bot UI at http://localhost:8100
echo  Press Ctrl+C to stop.
echo.
"%PYTHON%" server.py

pause
