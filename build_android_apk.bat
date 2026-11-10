@echo off
title Smart AI - Android APK ^& Google Play Store Builder
color 0b
cd /d "%~dp0"

echo ======================================================================
echo        SMART AI - ANDROID APK ^& GOOGLE PLAY STORE SETUP HUB
echo ======================================================================
echo.
echo Is tool se aap Smart AI ko Android Phone ke liye APK bana sakte hain
echo aur Google Play Store par publish karne ke liye AAB bundle generate
echo kar sakte hain!
echo.
echo ----------------------------------------------------------------------
echo  CHOOSE AN OPTION:
echo ----------------------------------------------------------------------
echo  [1] 1-Click PWABuilder (Play Store Signed APK ^& AAB - Recommended)
echo  [2] Google Bubblewrap CLI se Local Android APK Build karein
echo  [3] Direct Phone par Bina Play Store ke 1-Click App Install karein (PWA)
echo  [4] Google Play Store Step-by-Step Publishing Guide dekhein
echo  [5] Exit
echo ----------------------------------------------------------------------
echo.

set /p choice="Apna option number chunein (1-5): "

if "%choice%"=="1" goto pwabuilder
if "%choice%"=="2" goto bubblewrap
if "%choice%"=="3" goto direct_phone
if "%choice%"=="4" goto playstore_guide
if "%choice%"=="5" goto end
goto menu_retry

:pwabuilder
cls
echo ======================================================================
echo          OPTION 1: PWABUILDER (OFFICIAL PLAY STORE GENERATOR)
echo ======================================================================
echo.
echo PWABuilder (Microsoft ^& Google Official Tool) Smart AI ke manifest
echo aur service worker ko scan karke direct Google Play Store (.aab) aur
echo Android APK package download karwa deta hai!
echo.
echo Step 1: Agar aapka Smart AI local network par hai, to aap
echo         ngrok / cloudflare tunnel ya local URL use karein.
echo Step 2: Browser me PWABuilder open ho raha hai...
echo Step 3: Wahan URL daalkar 'Package for Stores' -> 'Google Play' dabayein.
echo.
pause
start https://www.pwabuilder.com/
goto end

:bubblewrap
cls
echo ======================================================================
echo         OPTION 2: GOOGLE BUBBLEWRAP CLI (LOCAL APK BUILD)
echo ======================================================================
echo.
echo Checking Node.js installation...
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js aapke computer par install nahi hai.
    echo Kripya pehle https://nodejs.org se Node.js install karein.
    pause
    goto end
)
echo [OK] Node.js mil gaya.
echo.
echo Installing / Updating Google Bubblewrap CLI (@bubblewrap/cli)...
call npm install -g @bubblewrap/cli
echo.
echo Bubblewrap initialization shuru ho raha hai...
echo Isme manifest URL pucha jayega (e.g. http://127.0.0.1:8765/manifest.json)
echo.
call bubblewrap init --manifest="http://127.0.0.1:8765/manifest.json"
echo.
echo APK build command: bubblewrap build
pause
goto end

:direct_phone
cls
echo ======================================================================
echo     OPTION 3: DIRECT PHONE INSTALL (PLAY STORE KI TARAH NATIVE APP)
echo ======================================================================
echo.
echo Smart AI me PWA (Progressive Web App) poori tarah enabled hai!
echo Kisi bhi Android phone par Play Store jaisa chalane ke liye:
echo.
echo 1. Phone ko computer wale Wi-Fi se jodiye.
echo 2. Phone ke Chrome browser me URL kholiye:
for /f "tokens=4" %%a in ('route print ^| findstr 0.0.0.0 ^| findstr /v "0.0.0.0\>"') do (
    set "MY_IP=%%a"
)
echo    http://10.32.102.171:8765
echo 3. Chrome ke 3-dots (⋮) par tap karke "Install app" dabayein!
echo 4. App aapke phone ki home screen aur app drawer me aa jayega.
echo.
start http://127.0.0.1:8765/#phone-modal
pause
goto end

:playstore_guide
cls
echo ======================================================================
echo     OPTION 4: GOOGLE PLAY STORE PUBLISHING GUIDE (KAISE KAREIN)
echo ======================================================================
echo.
echo Google Play Store par Smart AI daalne ke zaroori steps:
echo.
echo 1. Google Play Console Account:
echo    - https://play.google.com/console par jayein ($25 one-time registration).
echo.
echo 2. App Bundle (.aab) Taiyar Karein:
echo    - PWABuilder (Option 1) ya Bubblewrap (Option 2) se .aab file generate karein.
echo.
echo 3. Digital Asset Links (assetlinks.json):
echo    - Google Play Console se SHA-256 fingerprint copy karke
echo      Smart AI ke web/.well-known/assetlinks.json me daal dein.
echo.
echo 4. Store Listing:
echo    - Title: Smart AI - Multi-Engine Personal Assistant
echo    - Short Description: Hindi-first voice AI assistant with OpenSource Agents
echo    - Screenshots: Phone aur tablet ke screenshots upload karein.
echo.
echo 5. Publish:
echo    - 'Submit for review' dabayein. 24-48 ghanto me Play Store par live ho jayega!
echo.
pause
goto end

:menu_retry
echo Galat choice! Kripya 1 se 5 ke beech chunein.
pause
goto end

:end
echo.
echo Dhanyawaad! Smart AI Setup taiyar hai.

