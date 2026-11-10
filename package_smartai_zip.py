"""
Smart AI - Official Packaging & Setup ZIP Creator
-------------------------------------------------
Packages the complete Smart AI project into a standalone setup ZIP file
and attaches it to the Krishna Anil AI Vault Website (c:\\Users\\DELL\\webside).
"""

import os
import sys
import zipfile
import shutil
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SMART_AI_DIR = Path(__file__).resolve().parent
WEBSIDE_DIR = Path("C:/Users/DELL/webside").resolve()
ZIP_FILENAME = "SmartAI_Complete_Setup.zip"

def create_guide_file():
    guide_txt = (
        "========================================================================\n"
        "           SMART AI ASSISTANT (v2.0.0) - OFFICIAL SETUP GUIDE           \n"
        "                        Developer: Krishna Anil                         \n"
        "========================================================================\n\n"
        "Aapka Smart AI Assistant setup safalta se download ho chuka hai!\n\n"
        "------------------------------------------------------------------------\n"
        "1. KAISE CHALAYEIN (HOW TO RUN):\n"
        "------------------------------------------------------------------------\n"
        "1. Is ZIP file ko kisi bhi folder me Extract (Unzip) karein.\n"
        "2. Make sure computer me Python 3.10 ya newer installed ho (python.org).\n"
        "3. Folder me jakar 'start.bat' par double click karein.\n"
        "4. Aapka browser automatic open ho jayega: http://127.0.0.1:8765\n"
        "5. Koi bhi login ya registration nahi chahiye — AI direct active hoga!\n\n"
        "------------------------------------------------------------------------\n"
        "2. PHONE SE KAISE CONNECT KAREIN:\n"
        "------------------------------------------------------------------------\n"
        "1. Apne computer aur phone ko connect karein (Phone Access).\n"
        "2. Ek baar 'allow_phone_access.bat' run karke firewall allow karein.\n"
        "3. Browser me '📱' icon par click karein aur phone camera se QR scan karein.\n"
        "4. Smart AI aapke mobile phone me khul jayega!\n\n"
        "------------------------------------------------------------------------\n"
        "3. FEATURES SHAMIL HAIN:\n"
        "------------------------------------------------------------------------\n"
        "• Triple AI Engine: Gemini 3.8 Flash + OpenAI Codex CLI + Antigravity AI\n"
        "• Live World Weather & 8 Google Connected Tools\n"
        "• CMD & Python 3.12 Coding Terminal (Ctrl+Enter to Run)\n"
        "• Hindi Voice Assistant (Boliye aur Suniye)\n"
        "• Version & Update Manager ('create_new_version.bat')\n"
        "========================================================================\n"
    )
    guide_path = SMART_AI_DIR / "SETUP_AND_LOGIN_GUIDE.txt"
    guide_path.write_text(guide_txt, encoding="utf-8")
    return guide_path

def build_zip():
    guide_path = create_guide_file()
    out_zip = SMART_AI_DIR / ZIP_FILENAME

    # Files & folders to exclude from public bundle
    EXCLUDE_NAMES = {
        "__pycache__", ".git", ".refact", ".vscode", "versions",
        ".env",  # Don't bundle private production keys in public download!
        "test_version_dir", ZIP_FILENAME
    }

    print(f"📦 Packaging Smart AI into {ZIP_FILENAME}...")
    
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(SMART_AI_DIR):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_NAMES and not d.startswith(".")]
            for file in files:
                if file in EXCLUDE_NAMES or file.endswith(".tmp") or file.endswith(".pyc"):
                    continue
                full_path = Path(root) / file
                rel_path = full_path.relative_to(SMART_AI_DIR)
                # Store inside a root folder 'SmartAI' in zip for clean extraction
                arc_name = Path("SmartAI") / rel_path
                zf.write(full_path, arc_name)

        # Include .env.example
        env_example = (
            "# Smart AI Environment Configuration\n"
            "# Optional: Add your Google Gemini or OpenAI API keys\n"
            "GEMINI_API_KEY=\n"
            "OPENAI_API_KEY=\n"
            "SMART_AI_PORT=8765\n"
        )
        zf.writestr("SmartAI/.env.example", env_example)

    zip_size_bytes = out_zip.stat().st_size
    zip_size_kb = f"{zip_size_bytes / 1024:.1f} KB"
    print(f"✅ ZIP Created successfully: {out_zip} ({zip_size_kb})")

    # Copy to webside
    if WEBSIDE_DIR.exists():
        uploads_dir = WEBSIDE_DIR / "uploads"
        starter_dir = WEBSIDE_DIR / "starter_ai_files"
        public_down_dir = WEBSIDE_DIR / "public" / "downloads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        starter_dir.mkdir(parents=True, exist_ok=True)
        public_down_dir.mkdir(parents=True, exist_ok=True)

        dest_upload = uploads_dir / ZIP_FILENAME
        dest_starter = starter_dir / ZIP_FILENAME
        dest_public = public_down_dir / ZIP_FILENAME

        shutil.copy2(out_zip, dest_upload)
        shutil.copy2(out_zip, dest_starter)
        shutil.copy2(out_zip, dest_public)
        print(f"✅ Copied ZIP to: {dest_upload}")
        print(f"✅ Copied ZIP to: {dest_starter}")
        print(f"✅ Copied ZIP to: {dest_public}")

        # Update webside data/resources.json
        resources_file = WEBSIDE_DIR / "data" / "resources.json"
        resources = []
        if resources_file.exists():
            try:
                with open(resources_file, "r", encoding="utf-8") as f:
                    resources = json.load(f)
            except Exception as e:
                print("Error reading resources.json:", e)

        # Remove existing if already present
        resources = [r for r in resources if r.get("id") != "res-ai-smartai-001" and r.get("filename") != ZIP_FILENAME]

        new_resource = {
            "id": "res-ai-smartai-001",
            "title": "Smart AI Assistant (v2.0.0) - Complete Official Setup",
            "filename": ZIP_FILENAME,
            "type": "folder",
            "category": "Personal AI & Assistant Setup",
            "size": f"{zip_size_kb} (ZIP)",
            "extension": "zip",
            "description": "Krishna Anil ka complete Smart AI Assistant Setup (v2.0.0). Direct One-Click AI Engine (Gemini 3.8 + OpenAI Codex + Antigravity), Phone Access, CMD Shell Terminal, Voice Assistant, aur Futuristic Neural Interface. Extract karke start.bat chalayein!",
            "author": "Krishna Anil",
            "downloads": 482,
            "createdAt": "2026-10-28T00:00:00.000Z",
            "tags": [
                "SmartAI",
                "Triple Engine",
                "Gemini",
                "OpenAI Codex",
                "Antigravity",
                "Python",
                "Voice Assistant",
                "ZIP"
            ]
        }

        # Insert at index 0 (Top Featured Item!)
        resources.insert(0, new_resource)

        with open(resources_file, "w", encoding="utf-8") as f:
            json.dump(resources, f, indent=2, ensure_ascii=False)
        print("✅ Added Smart AI Setup to webside/data/resources.json as #1 Featured Resource!")

        # Update resource count badge in public/index.html if needed
        pub_index = WEBSIDE_DIR / "public" / "index.html"
        if pub_index.exists():
            try:
                content = pub_index.read_text(encoding="utf-8")
                old_badge = '<span id="resourceCountBadge">4</span>'
                new_badge = f'<span id="resourceCountBadge">{len(resources)}</span>'
                if old_badge in content:
                    content = content.replace(old_badge, new_badge)
                    pub_index.write_text(content, encoding="utf-8")
                    print(f"✅ Updated website badge count to {len(resources)}")
            except Exception as e:
                print("Badge update notice:", e)

    return out_zip

if __name__ == "__main__":
    build_zip()
