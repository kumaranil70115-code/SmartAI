"""
Smart AI - Authentication & User Security Manager
-------------------------------------------------
Users can sign in using Login ID (Username/Email) OR Phone Number with Password.
Protects Smart AI from unauthorized usage when shared or made public.
"""

import os
import sys
import json
import time
import secrets
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
USERS_FILE = ROOT / "users.json"

def _hash_pwd(password: str, salt: str = "smart_ai_secure_salt_2026") -> str:
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

def _load_data() -> dict:
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return init_default_users()

def _save_data(data: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def init_default_users() -> dict:
    """
    Initializes default admin user if users.json doesn't exist.
    """
    default_pwd_hash = _hash_pwd("smartai123")
    data = {
        "users": [
            {
                "id": "user_admin_001",
                "name": "Krishna Anil",
                "login_id": "kumaranil70115@gmail.com",
                "phone": "7011500000",
                "password_hash": default_pwd_hash,
                "role": "admin",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        ],
        "sessions": {}
    }
    _save_data(data)
    return data

def login_user(identifier: str, password: str):
    """
    Identifier can be either Login ID (email/username) OR Phone number.
    """
    identifier = str(identifier or "").strip().lower()
    password = str(password or "").strip()
    
    if not identifier or not password:
        return False, "Login ID/Phone aur Password dono likhna zaroori hai.", None
        
    data = _load_data()
    users = data.get("users", [])
    
    matched_user = None
    for u in users:
        u_login = str(u.get("login_id") or "").strip().lower()
        u_phone = str(u.get("phone") or "").strip()
        if identifier == u_login or identifier == u_phone:
            matched_user = u
            break
            
    if not matched_user:
        return False, "Yeh Login ID ya Phone Number registered nahi hai. Kripya Sign Up karein.", None
        
    pwd_hash = _hash_pwd(password)
    if pwd_hash != matched_user.get("password_hash"):
        return False, "Galat Password! Kripya sahi password daalein.", None
        
    # Generate session token (valid for 30 days)
    token = secrets.token_hex(24)
    sessions = data.get("sessions", {})
    sessions[token] = {
        "user_id": matched_user["id"],
        "name": matched_user["name"],
        "login_id": matched_user.get("login_id"),
        "phone": matched_user.get("phone"),
        "role": matched_user.get("role", "user"),
        "created_at": time.time(),
        "expires_at": time.time() + (30 * 86400)
    }
    data["sessions"] = sessions
    _save_data(data)
    
    user_info = {
        "id": matched_user["id"],
        "name": matched_user["name"],
        "login_id": matched_user.get("login_id"),
        "phone": matched_user.get("phone"),
        "role": matched_user.get("role", "user")
    }
    return True, token, user_info

def register_user(name: str, identifier: str, phone: str, password: str):
    """
    Register a new user with Login ID or Phone number.
    """
    name = str(name or "Smart AI User").strip()
    identifier = str(identifier or "").strip().lower()
    phone = str(phone or "").strip()
    password = str(password or "").strip()
    
    if not identifier and not phone:
        return False, "Login ID (Email/Username) ya Phone Number me se koi ek zaroori hai.", None
    if not password or len(password) < 4:
        return False, "Password kam se kam 4 akshar ka hona chahiye.", None
        
    data = _load_data()
    users = data.get("users", [])
    
    for u in users:
        u_login = str(u.get("login_id") or "").strip().lower()
        u_phone = str(u.get("phone") or "").strip()
        if identifier and u_login == identifier:
            return False, f"Login ID '{identifier}' pehle se registered hai. Sign In karein.", None
        if phone and u_phone == phone:
            return False, f"Phone Number '{phone}' pehle se registered hai. Sign In karein.", None
            
    new_id = f"user_{int(time.time())}_{secrets.token_hex(4)}"
    pwd_hash = _hash_pwd(password)
    
    new_user = {
        "id": new_id,
        "name": name,
        "login_id": identifier,
        "phone": phone,
        "password_hash": pwd_hash,
        "role": "user",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    users.append(new_user)
    data["users"] = users
    _save_data(data)
    
    # Auto login after register
    return login_user(identifier if identifier else phone, password)

def verify_session(token: str):
    """
    Verifies session token. Returns user profile if valid, else None.
    """
    if not token:
        return None
    token = str(token).strip()
    data = _load_data()
    sessions = data.get("sessions", {})
    sess = sessions.get(token)
    if not sess:
        return None
        
    if time.time() > sess.get("expires_at", 0):
        del sessions[token]
        data["sessions"] = sessions
        _save_data(data)
        return None
        
    return {
        "user_id": sess.get("user_id"),
        "name": sess.get("name"),
        "login_id": sess.get("login_id"),
        "phone": sess.get("phone"),
        "role": sess.get("role", "user")
    }

def logout_user(token: str) -> bool:
    if not token:
        return False
    data = _load_data()
    sessions = data.get("sessions", {})
    if token in sessions:
        del sessions[token]
        data["sessions"] = sessions
        _save_data(data)
        return True
    return False

if __name__ == "__main__":
    init_default_users()
    print("auth_manager initialized. Default user created.")

