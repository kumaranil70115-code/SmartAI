@echo off
title Smart AI - Version ^& Update Manager
cd /d "%~dp0"

echo ===================================================
echo        SMART AI - VERSION ^& UPDATE MANAGER
echo ===================================================
echo.
set "PY_CMD=python"
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
)

"%PY_CMD%" version_manager.py
echo.
pause

