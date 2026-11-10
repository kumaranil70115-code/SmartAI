@echo off
title Smart AI Assistant
cd /d "%~dp0"
echo ===================================================
echo           Smart AI Assistant Launching...
echo ===================================================

set "PY_CMD=python"
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
)

start "Smart AI Server (PC & Phone)" "%PY_CMD%" -u app.py
ping 127.0.0.1 -n 3 >nul
start "" "http://127.0.0.1:8765"
