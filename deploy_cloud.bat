@echo off
title Smart AI - 24/7 Permanent Cloud Deployment Assistant
color 0a
cd /d "%~dp0"

echo ======================================================================
echo       SMART AI - 24/7 PERMANENT CLOUD SERVER DEPLOYMENT HUB
echo ======================================================================
echo.
echo Is tool se Smart AI aapke computer se nikal kar 24-GHANTE ONLINE
echo rehne wale Permanent Cloud Server par deploy ho jayega!
echo.
echo Faayde:
echo  1. Computer/Laptop band hone par bhi Smart AI 24/7 chalu rahega.
echo  2. Duniya me koi bhi Play Store ya phone se anytime access kar sakta hai.
echo  3. 100% Free SSL HTTPS certificate aur permanent domain milega.
echo  4. Auto-Keepalive engine se server kabhi sleep/idle nahi hoga.
echo.
echo ----------------------------------------------------------------------
echo  CHOOSE CLOUD DEPLOYMENT OPTION:
echo ----------------------------------------------------------------------
echo  [1] Render.com (100% Free 24/7 Web Service - Sabse Aasan & Recommended)
echo  [2] Railway.app (1-Click Instant Cloud Deployment)
echo  [3] Docker Container (Local Server ya VPS par chalaane ke liye)
echo  [4] UptimeRobot 24/7 Free Ping Setup (Sleep Rokne ke liye 100% Guarantee)
echo  [5] Cloud Server Health Check Test (Live Ping Test)
echo  [6] Full 24/7 Deployment Step-by-Step Guide Kholein
echo  [7] Exit
echo ----------------------------------------------------------------------
echo.

set /p choice="Apna option number chunein (1-7): "

if "%choice%"=="1" goto render_deploy
if "%choice%"=="2" goto railway_deploy
if "%choice%"=="3" goto docker_deploy
if "%choice%"=="4" goto uptimerobot
if "%choice%"=="5" goto healthcheck
if "%choice%"=="6" goto guide
if "%choice%"=="7" goto end
goto end

:render_deploy
cls
echo ======================================================================
echo          RENDER.COM 24/7 PERMANENT SERVER DEPLOYMENT
echo ======================================================================
echo.
echo Render.com par Smart AI 100% Free 24/7 chalu rehta hai!
echo.
echo Zaroori Files Taiyar Hain:
echo  - render.yaml (Blueprint config)
echo  - requirements.txt (Dependencies)
echo  - app.py (Auto-Keepalive + Cloud detection enabled)
echo.
echo STEPS:
echo  1. Agar code GitHub par nahi hai, to GitHub par naya repository banayein
echo     aur yeh code push karein (git add . ^&^& git commit -m "24/7" ^&^& git push)
echo  2. https://render.com par free sign-up karein.
echo  3. 'New' -> 'Web Service' -> apna GitHub repo select karein.
echo  4. Runtime: Python 3
echo     Build Command: pip install -r requirements.txt
echo     Start Command: python app.py
echo  5. Environment Variables me:
echo     GEMINI_API_KEY = (Aapki Gemini API Key)
echo     SMARTAI_CLOUD_MODE = 1
echo  6. 'Create Web Service' dabayein!
echo.
echo 2 minute me aapko permanent URL mil jayega, jaise:
echo https://smart-ai-assistant.onrender.com
echo.
pause
start https://dashboard.render.com/select-repo?type=web
goto end

:railway_deploy
cls
echo ======================================================================
echo         RAILWAY.APP 24/7 PERMANENT CLOUD DEPLOYMENT
echo ======================================================================
echo.
echo Railway.app par 1-click me Dockerfile aur Procfile detect ho jata hai!
echo.
echo STEPS:
echo  1. https://railway.app par login karein.
echo  2. 'New Project' -> 'Deploy from GitHub repo' select karein.
echo  3. Variables me GEMINI_API_KEY add karein.
echo  4. Deploy ho jane par 'Settings' -> 'Generate Domain' dabayein!
echo.
pause
start https://railway.app/new
goto end

:docker_deploy
cls
echo ======================================================================
echo        DOCKER 24/7 LOCAL / VPS CONTAINER
echo ======================================================================
echo.
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker aapke system par install nahi hai.
    pause
    goto end
)
echo Docker container build ho raha hai...
docker build -t smartai-247 .
echo Container start ho raha hai (Port 8765)...
docker run -d -p 8765:8765 --name smartai --restart=always smartai-247
echo.
echo [OK] Docker container background me 24/7 chalu ho gaya hai!
pause
goto end

:uptimerobot
cls
echo ======================================================================
echo    UPTIMEROBOT 24/7 FREE PING SETUP (ZERO DOWNTIME GUARANTEE)
echo ======================================================================
echo.
echo Render free tier 15 minute bina request ke sleep me ja sakta hai.
echo Isko 24/7 jagaye rakhne ke liye UptimeRobot (100% Free) use karein!
echo.
echo STEPS:
echo  1. https://uptimerobot.com par free account banayein.
echo  2. 'Add New Monitor' dabayein.
echo  3. Monitor Type: HTTP(s)
echo  4. Friendly Name: Smart AI 24/7
echo  5. URL: Aapka permanent URL + /api/health
echo     (Jaise: https://smart-ai-assistant.onrender.com/api/health)
echo  6. Monitoring Interval: 5 minutes
echo  7. 'Create Monitor' dabayein!
echo.
echo Ab UptimeRobot har 5 minute me Smart AI ko ping karega,
echo jisse aapka server 24/7/365 KABHI BHI BAND NAHI HOGA!
echo.
pause
start https://uptimerobot.com/
goto end

:healthcheck
cls
echo ======================================================================
echo        LIVE CLOUD SERVER 24/7 HEALTH CHECK TEST
echo ======================================================================
echo.
set /p TEST_URL="Check karne ke liye Server URL daalein (e.g. https://smart-ai-assistant.onrender.com): "
if "%TEST_URL%"=="" (
    echo URL nahi diya gaya. Local health test kar rahe hain...
    set "TEST_URL=http://127.0.0.1:8765"
)
echo.
echo Pinging %TEST_URL%/api/health ...
echo.
python -c "
import urllib.request, json, sys
url = '%TEST_URL%'.rstrip('/') + '/api/health'
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'SmartAI-Test'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
        print('========================================================')
        print('  HEALTH CHECK STATUS: 200 OK (SERVER ACTIVE & ONLINE!) ')
        print('========================================================')
        print('  Service:   ', data.get('service'))
        print('  Mode:      ', data.get('mode'))
        print('  Uptime:    ', data.get('uptime_seconds'), 'seconds')
        print('  KeepAlive: ', data.get('keepalive'))
        print('========================================================')
except Exception as e:
    print('[FAIL] Server se connect nahi ho paya:', e)
"
pause
goto end

:guide
start DEPLOYMENT_24_7_GUIDE.md
goto end

:end
echo.
echo Smart AI Cloud Deployment Assistant complete.
