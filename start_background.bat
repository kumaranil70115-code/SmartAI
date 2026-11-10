@echo off
title Smart AI Background Starter
cd /d "%~dp0"
echo Smart AI background mein shuru ho raha hai...

set "PYW_CMD=pythonw"
if exist "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" (
    set "PYW_CMD=%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"
)

start "" "%PYW_CMD%" app.py
ping 127.0.0.1 -n 3 >nul
start "" "http://127.0.0.1:8765"
echo Server background mein active hai (Koi CMD window open nahi rahegi).

