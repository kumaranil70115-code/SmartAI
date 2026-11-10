@echo off
title Push Smart AI to GitHub (kumaranil70115-code)
color 0b
cd /d "%~dp0"

echo ==============================================================
echo     PUSHING SMART AI TO GITHUB: kumaranil70115-code/SmartAI
echo ==============================================================
echo.
echo Git push shuru ho raha hai...
echo (Agar browser popup aaye to 'Sign in with browser' dabayein)
echo.

git push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo GitHub par pehle ki files ko update karne ke liye push kar rahe hain...
    git push -u origin main --force
)

echo.
echo ==============================================================
echo    SUCCESS! SMART AI GITHUB PAR LIVE HO GAYA HAI!
echo ==============================================================
echo URL: https://github.com/kumaranil70115-code/SmartAI
echo ==============================================================
echo.
pause
