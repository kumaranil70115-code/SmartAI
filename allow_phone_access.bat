@echo off
title Smart AI - Allow Phone Access (Firewall Fix)
cd /d "%~dp0"
echo ========================================================
echo       SMART AI - PHONE ACCESS FIREWALL SETUP
echo ========================================================
echo.
echo Phone par 'Reload' ya 'Connection Timed Out' error ko 
echo theek karne ke liye Windows Firewall permission di ja rahi hai...
echo.
echo Kripya samne aane wale popup me 'Yes' dabayein.
echo.

powershell -Command "Start-Process cmd -ArgumentList '/c netsh advfirewall firewall add rule name=\"Smart AI Phone Access (8765)\" dir=in action=allow protocol=TCP localport=8765 profile=any & echo. & echo SUCCESS: Port 8765 phone access ke liye allow ho gaya hai! & echo Ab phone par Chrome reload karein. & pause' -Verb RunAs"

echo.
echo Process complete.

