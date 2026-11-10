# 🌐 Smart AI — 24/7 Permanent Cloud Server & Google Play Store Master Guide

> **Mubarak ho!** Smart AI ko ab poori tarah **Local Server se nikaal kar 24-Ghante Online rehne wale Permanent Cloud Server** par shift karne ke liye taiyar kar diya gaya hai. Ab aapka computer/laptop band hone par bhi Smart AI 24/7/365 online rahega aur Play Store se download karne par kisi bhi phone me bina rukawat chalega!

---

## 🚀 Part 1: Smart AI ko Permanent Cloud Server par Deploy Karein (100% Free)

Aapko kisi bhi paid server ki zaroorat nahi hai. Hum **Render.com** (Recommended) ya **Railway.app** par ise 2 minute me permanently host kar sakte hain.

### Option A: Render.com (Sabse Aasan & Free 24/7 Hosting)

1. **GitHub par Code Daalein:**
   - Agar aapka repository GitHub par hai, to commit karke push kar dein:
     ```bash
     git add .
     git commit -m "Smart AI 24/7 Permanent Cloud Server Update"
     git push origin main
     ```
   *(Agar GitHub repo nahi hai, to [GitHub.com](https://github.com) par free account banakar ek new private/public repo banayein aur code push karein).*

2. **Render.com par Account Kholein:**
   - [https://render.com](https://render.com) par jayein aur **Sign In with GitHub** karein.

3. **New Web Service Banayein:**
   - Dashboard me **New +** button dabakar **Web Service** chunein.
   - Apna **SmartAI** GitHub repository select karein.

4. **Settings Fill Karein (Auto-Detected):**
   - **Name:** `smart-ai-assistant`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py`
   - **Instance Type:** `Free`

5. **Environment Variables Add Karein:**
   - **Environment Variables** section me jaakar add karein:
     - `GEMINI_API_KEY`: *(Aapki Google Gemini API Key jo .env me hai)*
     - `SMARTAI_CLOUD_MODE`: `1`
     - `SMARTAI_KEEPALIVE`: `1`

6. **Deploy Dabayein:**
   - **Create Web Service** par click karein.
   - 2 minute me aapka backend live ho jayega aur aapko permanent HTTPS domain mil jayega:
     `https://smart-ai-assistant.onrender.com`

---

## ⏱️ Part 2: 24/7 Zero-Downtime KeepAlive Setup (Server Kabhi Sleep Nahi Hoga)

Render free tier me agar 15 minute koi request na aaye to server idle ho sakta hai. Humne Smart AI me **Auto-KeepAlive Ping Worker** pehle se built-in daal diya hai. Iske alawa 100% guarantee ke liye **UptimeRobot** connect karein:

1. [https://uptimerobot.com](https://uptimerobot.com) par free sign-up karein.
2. **Add New Monitor** button dabayein:
   - **Monitor Type:** `HTTP(s)`
   - **Friendly Name:** `Smart AI 24/7`
   - **URL (or IP):** `https://smart-ai-assistant.onrender.com/api/health`
   - **Monitoring Interval:** `5 minutes`
3. **Create Monitor** par click karein.
4. **Result:** UptimeRobot har 5 minute me Smart AI ke `/api/health` ko ping karega. Ab aapka server **24 ghante, 365 din kabhi band nahi hoga!**

---

## 📱 Part 3: Permanent Google Play Store Bundle (.AAB & .APK) Generate Karein

Ab jab aapka server permanent cloud domain par live ho gaya hai, to Play Store app ko is permanent domain se connect karein:

### Tarika 1: 1-Click Batch Builder Chalayein
1. Folder me jaakar **`build_permanent_playstore.bat`** par double click karein.
2. Apna Permanent Cloud URL daalein:
   `https://smart-ai-assistant.onrender.com`
3. **Option 1 (PWABuilder)** chunein:
   - PWABuilder website open hogi.
   - Aapka permanent URL paste karein.
   - **Package for Stores** -> **Google Play** -> **Generate Package** dabayein.
   - Aapko Signed **`.aab` (Google Play Store Bundle)** aur **`.apk` (Direct phone install)** mil jayega!

---

## 🌐 Part 4: Google Play Store par Publish Kaise Karein (Step-by-Step)

1. **Google Play Console Account:**
   - [https://play.google.com/console](https://play.google.com/console) par jayein ($25 one-time developer registration).

2. **Create App:**
   - Dashboard par **Create App** dabayein.
   - **App Name:** `Smart AI - 24/7 Hindi Voice Assistant`
   - **Default Language:** `Hindi (hi-IN)` ya `English (en-IN)`
   - **App or Game:** `App`
   - **Free or Paid:** `Free`

3. **Upload App Bundle (.aab):**
   - Left menu me **Production** -> **Releases** -> **Create new release** par jayein.
   - PWABuilder se mila hua **`.aab`** file drag and drop karein.

4. **Digital Asset Links (assetlinks.json):**
   - Play Console me **Setup** -> **App Integrity** / **App Signing** me jayein.
   - **SHA-256 certificate fingerprint** copy karein.
   - `build_permanent_playstore.bat` ka Option [3] chala kar fingerprint paste karein ya `web/.well-known/assetlinks.json` me update karke git push kar dein.
   - Isse aapka app phone par kholne par bina kisi browser URL bar ke direct native app ki tarah khulega!

5. **Store Listing & Screenshots:**
   - **Short Description:** `Hindi-first voice AI companion with Open-Source agents and background music.`
   - **Full Description:** `Smart AI aapka 24/7 personal digital companion hai jo voice commands se YouTube songs chala sakta hai, phone tasks control karta hai aur 10+ open-source AI agents se problem solve karta hai.`
   - Phone screenshots upload karein aur **Submit for review** daba dein.

---

## 🛠️ File Structure Summary:

| File Name | Purpose |
| :--- | :--- |
| `app.py` | 24/7 Cloud Engine with `$PORT` binding, Keepalive pinger, and `/api/health` |
| `Dockerfile` | Production container for cloud platforms & VPS |
| `render.yaml` | 1-Click Render.com Blueprint configuration |
| `Procfile` | Universal deployment file for Railway/Heroku/Dokku |
| `requirements.txt` | Cloud dependencies (`requests`, `gTTS`, `qrcode`, `pillow`, `dotenv`) |
| `build_permanent_playstore.bat` | Permanent Play Store AAB and APK generator |
| `deploy_cloud.bat` | 1-Click Interactive Cloud Deployment & Health Test Hub |
| `web/manifest.json` | High-res PWA manifest with Play Store category and icons |
| `web/icon-192.png` & `icon-512.png` | Official Play Store HD PNG app icons |
