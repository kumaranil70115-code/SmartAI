@echo off
title Smart AI Permanent Autostart Installer
color 0b
cd /d "%~dp0"

echo =============================================================
echo        SMART AI PERMANENT AUTOSTART SETUP (PC AND LAPTOP)
echo =============================================================
echo.
echo Is script se Smart AI aapke computer / laptop par PERMANENT ho
echo jayega aur Windows chalu hote hi background mein automatically
echo shuru ho jayega bina kisi black command window ke!
echo.

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "VBS_FILE=%STARTUP_FOLDER%\SmartAI_Silent_Autostart.vbs"
set "SMARTAI_DIR=%~dp0"

echo [1/2] Windows Startup script generate ho raha hai...

(
    echo Set WshShell = CreateObject^("WScript.Shell"^)
    echo WshShell.CurrentDirectory = "%SMARTAI_DIR%"
    echo WshShell.Run "pythonw.exe app.py", 0, False
) > "%VBS_FILE%"

if exist "%VBS_FILE%" (
    echo [2/2] SUCCESS! Autostart script save ho gaya:
    echo       "%VBS_FILE%"
    echo.
    echo =============================================================
    echo    MUBARAK HO! SMART AI AB PERMANENT HO GAYA HAI!
    echo =============================================================
    echo - Ab aapka computer / laptop jab bhi on hoga, Smart AI
    echo   background mein silently chalu ho jayega.
    echo - Aap apne phone, laptop ya kisi bhi browser me:
    echo   http://localhost:8765 kholkar direct use kar sakte hain.
    echo - Band karne ke liye aap 'stop.bat' chala sakte hain.
    echo - Autostart hatane ke liye 'uninstall_autostart.bat' chala sakte hain.
    echo =============================================================
) else (
    echo [ERROR] Autostart script save nahi ho saka.
)

echo.
pause
