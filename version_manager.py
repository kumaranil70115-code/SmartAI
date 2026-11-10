"""
Smart AI - Version & Release Manager
-----------------------------------
Aapke Smart AI project ko naya Version (v) aur naya Folder provide karne ka tool.
Purani files safe rehti hain aur naye folder me sabhi files copy hokar naye version
ke saath taiyar ho jaati hain.
"""

import os
import sys
import json
import shutil
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent

def get_version_info(base_dir=None):
    base = Path(base_dir) if base_dir else ROOT
    v_file = base / "version.json"
    if v_file.exists():
        try:
            with open(v_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "version": "v2.0.0",
        "version_name": "SmartAI v2.0.0",
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "release_name": "Smart AI Release",
        "history": []
    }

def normalize_version(v_str):
    if not v_str:
        return "v2.1.0"
    v_str = str(v_str).strip()
    if not v_str.lower().startswith("v"):
        v_str = "v" + v_str
    # replace invalid folder chars
    v_str = re.sub(r'[\/\\:\*\?"<>\|\s]', '', v_str)
    return v_str

def suggest_next_version(current_v=None, bump="minor"):
    if not current_v:
        info = get_version_info()
        current_v = info.get("version", "v2.0.0")
    
    clean = current_v.lstrip("vV")
    parts = clean.split(".")
    try:
        major = int(parts[0]) if len(parts) > 0 else 2
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        
        for _ in range(100):
            if bump == "major":
                major += 1
                candidate = f"v{major}.0.0"
            elif bump == "patch":
                patch += 1
                candidate = f"v{major}.{minor}.{patch}"
            else: # minor
                minor += 1
                candidate = f"v{major}.{minor}.0"

            # Check if this folder already exists
            target = ROOT.parent / f"SmartAI_{candidate}"
            if not target.exists():
                return candidate
        return f"v{major}.{minor}.0"
    except Exception:
        return "v2.1.0"

def get_ignore_patterns():
    def _ignore(src, names):
        ignored = set()
        for name in names:
            lower = name.lower()
            if name in {"__pycache__", ".refact", ".git", ".pytest_cache", "versions"}:
                ignored.add(name)
            elif lower.endswith(".pyc") or lower.endswith(".pyo") or lower.endswith(".tmp"):
                ignored.add(name)
        return ignored
    return _ignore

def create_new_version(new_version=None, target_dir=None, note="", overwrite=False):
    """
    Current SmartAI ki sabhi files ko naye version folder me copy karta hai,
    aur naye version number se update karta hai.
    """
    cur_info = get_version_info()
    current_version = cur_info.get("version", "v2.0.0")
    
    if not new_version:
        new_version = suggest_next_version(current_version, "minor")
    else:
        new_version = normalize_version(new_version)
        
    if not note:
        note = f"Smart AI update from {current_version} to {new_version}"
        
    # Determine target directory
    if target_dir:
        target_path = Path(target_dir).resolve()
    else:
        # Default: C:\Users\DELL\SmartAI_<version>
        parent = ROOT.parent
        folder_name = f"SmartAI_{new_version}"
        target_path = (parent / folder_name).resolve()
        
    # Same folder check
    if target_path == ROOT:
        return {
            "success": False,
            "error": "Naya folder current folder ke barabar nahi ho sakta. Kripya alag folder chunein."
        }
        
    if target_path.exists():
        if not overwrite:
            # Check if directory is non-empty
            if any(target_path.iterdir()):
                return {
                    "success": False,
                    "target_exists": True,
                    "target_path": str(target_path),
                    "error": f"Folder '{target_path.name}' pehle se maujood hai aur khaali nahi hai. Overwrite karein ya naya naam dein."
                }
        else:
            try:
                shutil.rmtree(target_path)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Existing folder delete nahi ho saka: {e}"
                }

    try:
        # Step 1: Copy tree from ROOT to target_path
        target_path.mkdir(parents=True, exist_ok=True)
        ignore_func = get_ignore_patterns()
        
        copied_count = 0
        for item in ROOT.iterdir():
            name = item.name
            if name in {"__pycache__", ".refact", ".git", ".pytest_cache", "versions"}:
                continue
            if name.endswith(".tmp") or name.endswith(".pyc"):
                continue
                
            dest_item = target_path / name
            if item.is_dir():
                shutil.copytree(item, dest_item, ignore=ignore_func, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest_item)
            copied_count += 1

        # Step 2: Update version.json in target folder
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history_list = cur_info.get("history", [])
        new_history_entry = {
            "version": new_version,
            "date": now_str,
            "folder": str(target_path),
            "note": note
        }
        # Copy history and append
        updated_history = list(history_list)
        updated_history.append(new_history_entry)
        
        target_version_data = {
            "version": new_version,
            "version_name": f"SmartAI {new_version}",
            "created_at": now_str,
            "release_name": f"Smart AI Release {new_version}",
            "description": f"Smart AI Assistant {new_version} - Base update from {current_version}",
            "base_version": current_version,
            "base_folder": str(ROOT),
            "note": note,
            "history": updated_history
        }
        
        with open(target_path / "version.json", "w", encoding="utf-8") as f:
            json.dump(target_version_data, f, indent=2, ensure_ascii=False)
            
        # Step 2b: Also update current ROOT version.json so the current active workspace reflects the new version
        root_v_file = ROOT / "version.json"
        if root_v_file.exists():
            try:
                with open(root_v_file, "r", encoding="utf-8") as f:
                    rdata = json.load(f)
                rdata["version"] = new_version
                rdata["version_name"] = f"SmartAI {new_version}"
                rdata["updated_at"] = now_str
                rdata["history"] = updated_history
                with open(root_v_file, "w", encoding="utf-8") as f:
                    json.dump(rdata, f, indent=2, ensure_ascii=False)
            except Exception:
                pass
                
        # Step 3: Update version_history.json in current ROOT to remember all created versions
        root_history_file = ROOT / "version_history.json"
        all_versions = []
        if root_history_file.exists():
            try:
                with open(root_history_file, "r", encoding="utf-8") as f:
                    all_versions = json.load(f)
            except Exception:
                all_versions = []
                
        all_versions.append({
            "version": new_version,
            "folder": str(target_path),
            "created_at": now_str,
            "note": note
        })
        with open(root_history_file, "w", encoding="utf-8") as f:
            json.dump(all_versions, f, indent=2, ensure_ascii=False)

        # Step 4: Update start.bat in the target folder with the new title
        target_start_bat = target_path / "start.bat"
        if target_start_bat.exists():
            try:
                content = target_start_bat.read_text(encoding="utf-8", errors="ignore")
                content = content.replace("Smart AI Assistant", f"Smart AI Assistant ({new_version})")
                target_start_bat.write_text(content, encoding="utf-8")
            except Exception:
                pass

        # Step 5: Create a VERSION_INFO.txt in the new folder
        info_txt = (
            f"==========================================================\n"
            f" SMART AI - RELEASE INFO ({new_version})\n"
            f"==========================================================\n"
            f"Version         : {new_version}\n"
            f"Folder          : {target_path}\n"
            f"Created At      : {now_str}\n"
            f"Base Version    : {current_version} ({ROOT})\n"
            f"Note            : {note}\n"
            f"==========================================================\n"
            f"Chalaane ke liye:\n"
            f"1. Is folder me 'start.bat' par double click karein.\n"
            f"2. Ya cmd me 'python app.py' chalaayein.\n"
            f"Browser me open hoga: http://127.0.0.1:8765\n"
            f"==========================================================\n"
        )
        (target_path / "VERSION_INFO.txt").write_text(info_txt, encoding="utf-8")

        return {
            "success": True,
            "version": new_version,
            "previous_version": current_version,
            "folder": str(target_path),
            "items_copied": copied_count,
            "created_at": now_str,
            "message": f"Smart AI {new_version} safalta se ban gaya hai!"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Naya version folder banane me truti: {str(e)}"
        }

def list_all_versions():
    cur = get_version_info()
    history_file = ROOT / "version_history.json"
    records = []
    if history_file.exists():
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            records = []
    return {
        "current_version": cur.get("version", "v2.0.0"),
        "current_folder": str(ROOT),
        "created_versions": records
    }

def interactive_cli():
    cur = get_version_info()
    current_v = cur.get("version", "v2.0.0")
    suggested = suggest_next_version(current_v, "minor")
    
    print("\n" + "=" * 60)
    print("        SMART AI - VERSION & UPDATE MANAGER")
    print("=" * 60)
    print(f"  Current Version : {current_v}")
    print(f"  Current Folder  : {ROOT}")
    print("=" * 60)
    
    # Input version
    print(f"\n[1/3] Naya version number kya dena chahte hain?")
    print(f"      (Enter dabayein default '{suggested}' ke liye)")
    v_in = input(f"Version [{suggested}]: ").strip()
    new_v = normalize_version(v_in if v_in else suggested)
    
    # Input folder choice
    default_dir = ROOT.parent / f"SmartAI_{new_v}"
    sub_dir = ROOT / "versions" / f"SmartAI_{new_v}"
    
    print(f"\n[2/3] Naya version kis folder me save karna hai?")
    print(f"  1. Parent folder me: {default_dir}  [Recommended]")
    print(f"  2. SmartAI ke andar: {sub_dir}")
    print(f"  3. Custom path type karein")
    choice = input("Option chunein [1/2/3] (Default 1): ").strip()
    
    if choice == "2":
        target = sub_dir
    elif choice == "3":
        c_path = input("Custom folder path daalein: ").strip()
        target = Path(c_path).resolve() if c_path else default_dir
    else:
        target = default_dir
        
    # Input note
    print(f"\n[3/3] Koi update note ya description likhna hai?")
    note_in = input("Update Note (Optional): ").strip()
    if not note_in:
        note_in = f"Update to {new_v}"
        
    print("\n" + "-" * 60)
    print(f"Naya Version  : {new_v}")
    print(f"Target Folder : {target}")
    print(f"Notes         : {note_in}")
    print("-" * 60)
    confirm = input("Kya aap continue karna chahte hain? (y/n) [y]: ").strip().lower()
    if confirm and confirm not in ("y", "yes", "haan"):
        print("Cancelled.")
        return
        
    overwrite = False
    if target.exists() and any(target.iterdir()):
        print(f"\nWarning: Target folder '{target}' pehle se maujood hai.")
        ov = input("Kya aap ise overwrite (replace) karna chahte hain? (y/n) [n]: ").strip().lower()
        if ov in ("y", "yes", "haan"):
            overwrite = True
        else:
            print("Operation radd kiya gaya.")
            return

    print("\nFiles copy aur version update ho raha hai... Kripya intezaar karein.")
    res = create_new_version(new_v, target, note_in, overwrite=overwrite)
    
    if res.get("success"):
        print("\n" + "=" * 60)
        print("  ✅ SAFALTA: NAYA VERSION BAN GAYA HAI!")
        print("=" * 60)
        print(f"  🏷️  Version       : {res['version']}")
        print(f"  📁  Naya Folder   : {res['folder']}")
        print(f"  📄  Files Copied  : {res['items_copied']} items")
        print(f"  🕒  Time          : {res['created_at']}")
        print("=" * 60)
        print("\nNaye version ko chalane ke liye:")
        print(f"1. Folder me jayein: cd /d \"{res['folder']}\"")
        print("2. 'start.bat' chalaayein.")
        
        op = input("\nKya aap abhi naye folder ko Windows Explorer me kholna chahte hain? (y/n) [y]: ").strip().lower()
        if not op or op in ("y", "yes", "haan"):
            os.system(f'explorer "{res["folder"]}"')
    else:
        print("\n❌ Error: " + res.get("error", "Unknown error"))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Smart AI Version Manager")
    parser.add_argument("--version", "-v", help="Naya version number (e.g. v2.1.0)")
    parser.add_argument("--target", "-t", help="Target folder path")
    parser.add_argument("--note", "-n", help="Version release note")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite if target folder exists")
    parser.add_argument("--list", action="store_true", help="List all created versions")
    args = parser.parse_args()
    
    if args.list:
        data = list_all_versions()
        print(json.dumps(data, indent=2))
    elif args.version:
        res = create_new_version(args.version, args.target, args.note or "", args.overwrite)
        print(json.dumps(res, indent=2))
        sys.exit(0 if res.get("success") else 1)
    else:
        interactive_cli()

