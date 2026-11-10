@echo off
title Smart AI Autostart Uninstaller
cd /d "%~dp0"

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "VBS_FILE=%STARTUP_FOLDER%\SmartAI_Silent_Autostart.vbs"

echo Smart AI Autostart hataya ja raha hai...

if exist "%VBS_FILE%" (
    del /f /q "%VBS_FILE%"
    echo Autostart safalta se hata diya gaya hai.
) else (
    echo Autostart file pehle se maujood nahi thi.
)

echo.
pause

