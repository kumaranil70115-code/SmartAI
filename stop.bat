@echo off
title Smart AI Stopper
cd /d "%~dp0"
echo Smart AI Server band kiya ja raha hai...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8765 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo Smart AI safalta se band ho gaya.
pause

