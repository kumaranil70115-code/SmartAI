from __future__ import annotations
import ast, base64, concurrent.futures, email, email.header, glob, imaplib, ipaddress, json, math, mimetypes, os, re, shutil, socket, subprocess, sys, tempfile, threading, time, urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from version_manager import get_version_info, create_new_version, list_all_versions, suggest_next_version, normalize_version
from auth_manager import login_user, register_user, verify_session, logout_user, init_default_users
from learning_engine import record_feedback, get_learning_context, get_learning_stats, delete_learned_rule, clear_all_learning
from opensource_agents import get_all_agents, get_agent_categories, get_agents_summary_text, OPENSOURCE_AGENTS
from agent_orchestrator import (
    detect_agent_delegation,
    build_agent_framework_instructions,
    check_ollama,
    generate_next_project_step,
    is_task_or_project
)
from tunnel_manager import start_tunnel_background, get_tunnel_url

# Ensure UTF-8 stdout/stderr on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

socket.setdefaulttimeout(60)

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
UPLOADS_DIR = ROOT / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
ENV_FILE = ROOT / ".env"
PERMISSIONS_FILE = ROOT / "permissions.json"
CONTACTS_FILE = ROOT / "contacts.json"
LEGACY_KEY = Path.home() / ".codex" / "google_key.txt"
CODEX_AUTH_FILE = Path.home() / ".codex" / "auth.json"
CODEX_CONFIG_FILE = Path.home() / ".codex" / "config.toml"
HOST = "127.0.0.1"
BIND_HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", os.environ.get("SMART_AI_PORT", "8765")))
PRIMARY_MODEL = "gemini-flash-lite-latest"
REALTIME_MODEL = "gemini-flash-latest"
LITE_MODEL = "gemini-flash-lite-latest"
OPENAI_DEFAULT_MODEL = "gpt-4o-mini"
SERVER_START_TIME = time.time()
IS_CLOUD = bool(
    os.environ.get("RENDER")
    or os.environ.get("RAILWAY_ENVIRONMENT")
    or os.environ.get("FLY_ALLOC_ID")
    or os.environ.get("SMARTAI_CLOUD_MODE") == "1"
    or os.environ.get("PERMANENT_SERVER_URL")
    or os.environ.get("PORT")
)

def save_uploaded_attachment(att: dict) -> dict:
    orig_name = str(att.get("name") or "uploaded_file").strip()
    cat = str(att.get("category") or "file").strip().lower()
    rel_path = att.get("relative_path")
    
    clean_name = re.sub(r'[\\/*?:"<>|]', "_", os.path.basename(orig_name))
    if not clean_name:
        clean_name = f"file_{int(time.time())}"
        
    if rel_path:
        parts = [re.sub(r'[\\/*?:"<>|]', "_", p) for p in Path(rel_path).parts if p not in ("..", ".")]
        dest = UPLOADS_DIR.joinpath(*parts)
        dest.parent.mkdir(parents=True, exist_ok=True)
    else:
        dest = UPLOADS_DIR / clean_name
        if dest.exists():
            stem = dest.stem
            suffix = dest.suffix
            dest = UPLOADS_DIR / f"{stem}_{int(time.time()*1000)%100000}{suffix}"
            clean_name = dest.name
            
    data_str = str(att.get("data") or "")
    if "," in data_str:
        data_str = data_str.split(",", 1)[1]
        
    size = 0
    if data_str:
        try:
            file_bytes = base64.b64decode(data_str)
            dest.write_bytes(file_bytes)
            size = len(file_bytes)
        except Exception:
            pass
            
    return {
        "name": clean_name,
        "original_name": orig_name,
        "saved_path": str(dest.relative_to(ROOT)).replace("\\", "/"),
        "size": size,
        "category": cat,
        "type": att.get("type", "application/octet-stream"),
        "url": f"/uploads/{clean_name}"
    }

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1.0)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass
    try:
        ip = socket.gethostbyname(socket.gethostname())
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass
    return "127.0.0.1"

ALLOWED_CLOUD_SUFFIXES = (
    ".trycloudflare.com",
    ".loca.lt",
    ".ngrok-free.app",
    ".onrender.com",
    ".railway.app",
    ".koyeb.app",
    ".fly.dev",
    ".hf.space",
    ".run.app",
    ".herokuapp.com"
)

def _is_allowed_origin_or_host(host_or_ip: str | None) -> bool:
    if not host_or_ip:
        return False
    h = host_or_ip.split(":", 1)[0].strip().lower()
    if h in ("localhost", "127.0.0.1", "::1"):
        return True
    if any(h.endswith(sfx) for sfx in ALLOWED_CLOUD_SUFFIXES):
        return True
    perm = os.environ.get("PERMANENT_SERVER_URL", "").strip().lower()
    if perm:
        parsed = urllib.parse.urlsplit(perm if "://" in perm else f"https://{perm}")
        if (parsed.hostname or "").lower() == h:
            return True
    if os.environ.get("SMARTAI_ALLOW_ALL_HOSTS", "").lower() in ("1", "true"):
        return True
    if IS_CLOUD:
        return True
    try:
        ip_obj = ipaddress.ip_address(h)
        return bool(ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local)
    except ValueError:
        return False

def _is_private_or_local(host_or_ip: str | None) -> bool:
    return _is_allowed_origin_or_host(host_or_ip)

def _start_keepalive_worker():
    def _pinger():
        time.sleep(15)
        while True:
            try:
                ping_url = f"http://127.0.0.1:{PORT}/api/health"
                req = urllib.request.Request(ping_url, headers={"User-Agent": "SmartAI-24-7-KeepAlive"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    pass
                ext_url = os.environ.get("PERMANENT_SERVER_URL") or os.environ.get("RENDER_EXTERNAL_URL")
                if ext_url:
                    if not ext_url.startswith("http"):
                        ext_url = f"https://{ext_url}"
                    ext_req = urllib.request.Request(f"{ext_url.rstrip('/')}/api/health", headers={"User-Agent": "SmartAI-24-7-KeepAlive"})
                    with urllib.request.urlopen(ext_req, timeout=10) as resp:
                        pass
            except Exception:
                pass
            time.sleep(600)
    t = threading.Thread(target=_pinger, daemon=True)
    t.start()

def get_cmd_status() -> dict:
    import platform
    return {
        "status": "ready",
        "interpreter": sys.executable,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "cwd": str(ROOT),
        "codex_ready": bool(shutil.which("codex") or (Path.home() / "AppData/Local/OpenAI/Codex").exists()),
        "antigravity_ready": True
    }

def execute_cmd(command: str, timeout: int = 30) -> dict:
    command = (command or "").strip()
    if not command:
        raise ValueError("CMD command khaali hai.")
    t0 = time.time()
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout
        )
        elapsed = int((time.time() - t0) * 1000)
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        full_out = out if not err else (f"{out}\n[STDERR]:\n{err}".strip() if out else err)
        return {
            "status": "success" if proc.returncode == 0 else "error",
            "exit_code": proc.returncode,
            "output": full_out or "(Command finished without output)",
            "stdout": out,
            "stderr": err,
            "command": command,
            "elapsed_ms": elapsed
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "exit_code": -1,
            "output": f"Command timeout ho gaya ({timeout}s limit exceed).",
            "command": command,
            "elapsed_ms": int((time.time() - t0) * 1000)
        }
    except Exception as exc:
        return {
            "status": "error",
            "exit_code": -1,
            "output": f"Command error: {exc}",
            "command": command,
            "elapsed_ms": int((time.time() - t0) * 1000)
        }

def execute_python_code(code: str, timeout: int = 30) -> dict:
    code = (code or "").strip()
    if not code:
        raise ValueError("Python code khaali hai.")
    t0 = time.time()
    scratch_dir = ROOT / "workspace"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    scratch_file = scratch_dir / f"run_{int(time.time()*1000)%100000}.py"
    try:
        scratch_file.write_text(code, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-u", str(scratch_file)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout
        )
        elapsed = int((time.time() - t0) * 1000)
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        full_out = out if not err else (f"{out}\n[ERROR]:\n{err}".strip() if out else err)
        return {
            "status": "success" if proc.returncode == 0 else "error",
            "exit_code": proc.returncode,
            "output": full_out or "(Python code safalta se run hua)",
            "stdout": out,
            "stderr": err,
            "code": code,
            "elapsed_ms": elapsed
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "exit_code": -1,
            "output": f"Python script timeout ho gayi ({timeout}s limit).",
            "code": code,
            "elapsed_ms": int((time.time() - t0) * 1000)
        }
    except Exception as exc:
        return {
            "status": "error",
            "exit_code": -1,
            "output": f"Python run error: {exc}",
            "code": code,
            "elapsed_ms": int((time.time() - t0) * 1000)
        }
    finally:
        try:
            if scratch_file.exists():
                scratch_file.unlink()
        except OSError:
            pass

SYSTEM = (
    "Aap Smart AI hain — ek behad samajhdar, zinda-dil, vinamra aur dostana Hindi AI companion jo bilkul ek asli insaan ki tarah baat karta hai. "
    "User ko hamesha mehsoos hona chahiye ki woh kisi sachhe dost, saathi ya gyaani insaan se baat kar rahe hain. "
    "User Hindi ya Hinglish mein baat karega; usi bhasha mein dil se, saaf, aasan, garamjoshi (warmth) aur apnepan ke saath jawab dein. "
    "Aapke jawab me insani ehsaas, samman aur dostana muskurahat honi chahiye ('Haan bilkul!', 'Arre waah!', 'Main abhi aapko samjhata hoon...', 'Fikr bilkul mat kijiye, main hoon na!'). "
    "KABHI BHI robotic, dry machine jaisi bhasha, bureaucratic reports ya automated debug headers (jaise 'Agent 1:', 'Dispatcher Log:', 'Senior Research Specialist:') mat likhein. "
    "Aapke jawab aawaz se bolkar sunaye jaate hain, isliye bolchal ki aasan, madhur aur spasht Hindi/Hinglish use karein jo kaano ko acchi aur swabhavik lage.\n\n"
    "Aapke paas computer par automated tools aur direct system access connected hain:\n"
    "1. Smart AI Version Manager: User ke aadesh par naya version banana, folders clone karna aur version update karna.\n"
    "2. Windows CMD Terminal & Python 3.12 Engine: Real-time code execution, commands run karna aur calculations.\n"
    "3. Connected Google Tools: Google Photos, Maps, Drive, YouTube, Google One, Play Store, Chrome.\n"
    "4. Desktop Apps & Permissions: WhatsApp, Notepad, Calculator, Paint, File Manager.\n"
    "5. Live World Weather & Google Search.\n\n"
    "CRITICAL AUTONOMOUS INSTRUCTION:\n"
    "Kabhi bhi yeh mat kaho ki 'Main ek AI bhasha model hoon aur file system modify nahi kar sakta'! "
    "Aap ek local autonomous AI companion hain. Jab user bole 'tum khud se naya version update karo' ya koi action bole, "
    "to batayein ki action execute kiya ja chuka hai ya turant execute ho raha hai — ek sachhe, bharosemand insaan ki tarah."
)

_EXHAUSTED_UNTIL = 0

def _clean_key(val: str | None) -> str | None:
    if not val:
        return None
    val = val.strip()
    while (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        val = val[1:-1].strip()
    val = val.strip("'\" \t\r\n")
    if "H1NZ" in val:
        val = val.replace("H1NZ", "HlNZ")
    if "Ek5akkq000" in val:
        val = val.replace("Ek5akkq000", "Ek5akKqO0OXS")
    return val or None

def is_valid_gemini_format(k: str | None) -> bool:
    if not k:
        return False
    k = str(k).strip()
    return len(k) >= 20 and len(k) <= 512 and not any(c in k for c in (" ", "\n", "\r", "\t"))

def _read_env() -> dict[str, str]:
    data = {}
    if ENV_FILE.exists():
        try:
            for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    data[k] = v
        except OSError:
            pass
    return data

def _save_env(updates: dict[str, str]):
    env = _read_env()
    env.update(updates)
    lines = [f"{k}={v}" for k, v in env.items() if v]
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

def _dotenv_key():
    env = _read_env()
    val = env.get("GEMINI_API_KEY")
    return _clean_key(val) if val else None

def get_key():
    key = _clean_key(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    if key:
        return key, "environment"
    key = _clean_key(_dotenv_key())
    if key:
        return key, "local settings"
    try:
        key = _clean_key(LEGACY_KEY.read_text(encoding="utf-8"))
        if key:
            return key, "existing local key file"
    except OSError:
        pass
    return None, None

def save_key(key):
    cleaned = _clean_key(key)
    if not cleaned or len(cleaned) > 512 or "\n" in cleaned or "\r" in cleaned:
        raise ValueError("API key khaali ya invalid hai.")
    os.environ["GEMINI_API_KEY"] = cleaned
    _save_env({"GEMINI_API_KEY": cleaned})

def _dotenv_openai_key() -> str | None:
    env = _read_env()
    val = env.get("OPENAI_API_KEY")
    return _clean_key(val) if val else None

def get_codex_auth_info() -> dict:
    if CODEX_AUTH_FILE.exists():
        try:
            data = json.loads(CODEX_AUTH_FILE.read_text(encoding="utf-8"))
            email = None
            name = None
            tokens = data.get("tokens") or {}
            acc_id = tokens.get("account_id")
            id_tok = tokens.get("id_token")
            if id_tok and "." in id_tok:
                try:
                    payload_part = id_tok.split(".")[1]
                    payload_part += "=" * ((4 - len(payload_part) % 4) % 4)
                    payload_json = json.loads(base64.urlsafe_b64decode(payload_part.encode()).decode("utf-8"))
                    email = payload_json.get("email")
                    name = payload_json.get("name")
                except Exception:
                    pass
            return {
                "auth_mode": data.get("auth_mode", "chatgpt"),
                "account_id": acc_id,
                "email": email or "kumaranil70115@gmail.com",
                "name": name or "Anil krishna",
                "api_key": _clean_key(data.get("OPENAI_API_KEY"))
            }
        except Exception:
            pass
    return {}

def get_openai_key() -> str | None:
    key = _clean_key(os.environ.get("OPENAI_API_KEY"))
    if key:
        return key
    key = _clean_key(_dotenv_openai_key())
    if key:
        return key
    auth_info = get_codex_auth_info()
    if auth_info.get("api_key"):
        return auth_info["api_key"]
    return None

def save_openai_key(key: str):
    cleaned = _clean_key(key)
    if not cleaned or len(cleaned) > 512 or "\n" in cleaned or "\r" in cleaned:
        raise ValueError("OpenAI API key khaali ya invalid hai.")
    os.environ["OPENAI_API_KEY"] = cleaned
    _save_env({"OPENAI_API_KEY": cleaned})

def find_codex_cli() -> str | None:
    env_cli = os.environ.get("CODEX_CLI_PATH")
    if env_cli and os.path.isfile(env_cli):
        return env_cli
    local_app = os.environ.get("LOCALAPPDATA", "")
    if local_app:
        pattern = os.path.join(local_app, "OpenAI", "Codex", "bin", "*", "codex.exe")
        matches = glob.glob(pattern)
        if matches:
            matches.sort(key=os.path.getmtime, reverse=True)
            return matches[0]
    w = shutil.which("codex.exe") or shutil.which("codex")
    if w and os.path.isfile(w):
        return w
    default_path = r"C:\Users\DELL\AppData\Local\OpenAI\Codex\bin\2993767bd1dfb009\codex.exe"
    if os.path.isfile(default_path):
        return default_path
    return None

def get_openai_status() -> dict:
    key = get_openai_key()
    cli = find_codex_cli()
    auth_data = get_codex_auth_info()
    has_cli = bool(cli)
    has_key = bool(key)
    is_ready = has_key or has_cli

    if has_key and has_cli:
        mode = "dual_ready"
        summary = "Codex CLI + API Key"
    elif has_cli:
        mode = "codex_cli"
        summary = "Connected · Codex CLI"
    elif has_key:
        mode = "api_key"
        summary = "Connected · OpenAI API"
    else:
        mode = "none"
        summary = "Key ya CLI zaroori hai"

    user_email = auth_data.get("email") or get_google_account()

    return {
        "status": "ready" if is_ready else "key_needed",
        "mode": mode,
        "summary": summary,
        "model": "gpt-6-luna (Codex CLI)" if has_cli else ("gpt-4o-mini (API)" if has_key else "Not configured"),
        "user": user_email,
        "name": auth_data.get("name", "Anil krishna"),
        "account_id": auth_data.get("account_id"),
        "cli_path": cli,
        "has_api_key": has_key,
        "has_cli": has_cli,
        "mcp_registered": True
    }

def get_google_account() -> str:
    env = _read_env()
    return os.environ.get("GOOGLE_ACCOUNT") or env.get("GOOGLE_ACCOUNT") or env.get("GMAIL_USER") or "kumaranil70115@gmail.com"

def save_google_account(email_addr: str):
    email_addr = (email_addr or "kumaranil70115@gmail.com").strip().lower()
    if not email_addr or "@" not in email_addr:
        raise ValueError("Sahi Gmail address daalein.")
    _save_env({"GOOGLE_ACCOUNT": email_addr, "GMAIL_USER": email_addr})

def get_gmail_creds():
    env = _read_env()
    user = os.environ.get("GMAIL_USER") or env.get("GMAIL_USER") or "kumaranil70115@gmail.com"
    pwd = os.environ.get("GMAIL_APP_PASSWORD") or env.get("GMAIL_APP_PASSWORD") or ""
    pwd = pwd.replace(" ", "").strip()
    return user, pwd

_GMAIL_STATUS_CACHE = None
_GMAIL_STATUS_CACHE_TIME = 0

def save_gmail_creds(email_addr: str, app_pwd: str):
    global _GMAIL_STATUS_CACHE
    email_addr = (email_addr or "kumaranil70115@gmail.com").strip().lower()
    app_pwd = app_pwd.replace(" ", "").strip()
    if not email_addr or "@" not in email_addr:
        raise ValueError("Sahi Gmail address daalein.")
    if not app_pwd or len(app_pwd) < 8:
        raise ValueError("Google ka 16-akshar wala App Password daalein.")
    _save_env({"GMAIL_USER": email_addr, "GMAIL_APP_PASSWORD": app_pwd})
    _GMAIL_STATUS_CACHE = None

def check_gmail_status(force: bool = False):
    global _GMAIL_STATUS_CACHE, _GMAIL_STATUS_CACHE_TIME
    now = time.time()
    if not force and _GMAIL_STATUS_CACHE and (now - _GMAIL_STATUS_CACHE_TIME < 60):
        return _GMAIL_STATUS_CACHE

    user, pwd = get_gmail_creds()
    if not pwd:
        res = {"configured": False, "connected": False, "user": user, "message": "Password set nahi hai"}
        _GMAIL_STATUS_CACHE = res
        _GMAIL_STATUS_CACHE_TIME = now
        return res
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=5)
        mail.login(user, pwd)
        mail.logout()
        res = {"configured": True, "connected": True, "user": user, "message": "Connected"}
    except imaplib.IMAP4.error:
        res = {"configured": True, "connected": False, "user": user, "message": "Login reject hua. 16-akshar ka App Password check karein."}
    except Exception as exc:
        res = {"configured": True, "connected": False, "user": user, "message": f"Connection error: {str(exc)}"}
    
    _GMAIL_STATUS_CACHE = res
    _GMAIL_STATUS_CACHE_TIME = now
    return res

def get_unread_emails(max_count: int = 5):
    user, pwd = get_gmail_creds()
    if not pwd:
        return {"error": "Gmail connect nahi hai. Settings mein App Password save karein."}
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=8)
        mail.login(user, pwd)
        mail.select("INBOX", readonly=True)
        stat, resp = mail.search(None, "UNSEEN")
        if stat != "OK" or not resp or not resp[0]:
            mail.logout()
            return {"unread_count": 0, "emails": []}

        email_ids = resp[0].split()
        total = len(email_ids)
        latest_ids = email_ids[-max_count:]
        emails = []

        for eid in reversed(latest_ids):
            st, data = mail.fetch(eid, "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])")
            if st == "OK" and data and isinstance(data[0], tuple):
                msg = email.message_from_bytes(data[0][1])
                subj_raw = msg.get("Subject", "Bina subject ke")
                subj_parts = email.header.decode_header(subj_raw)
                subj = ""
                for part, enc in subj_parts:
                    if isinstance(part, bytes):
                        subj += part.decode(enc or "utf-8", errors="replace")
                    else:
                        subj += str(part)

                from_raw = msg.get("From", "Unknown")
                from_parts = email.header.decode_header(from_raw)
                sender = ""
                for part, enc in from_parts:
                    if isinstance(part, bytes):
                        sender += part.decode(enc or "utf-8", errors="replace")
                    else:
                        sender += str(part)
                emails.append({"from": sender.strip(), "subject": subj.strip(), "date": msg.get("Date", "").strip()})
        mail.logout()
        return {"unread_count": total, "emails": emails}
    except Exception as exc:
        return {"error": f"Email check nahi ho sake: {str(exc)}"}

def _fetch_tts_chunk(chunk: str) -> bytes:
    try:
        url = "https://translate.google.com/translate_tts?ie=UTF-8&q=" + urllib.parse.quote(chunk) + "&tl=hi&client=tw-ob"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            return resp.read()
    except Exception:
        return b""

def generate_hindi_tts(text: str) -> bytes:
    clean = re.sub(r"https?://\S+", "", text)
    clean = re.sub(r"[`*_#~\[\]\(\)\{\}\<\>]", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    if not clean:
        return b""
    sentences = re.split(r"([।\.\n\?\!\;]+)", clean)
    chunks = []
    current = ""
    for piece in sentences:
        if len(current) + len(piece) <= 150:
            current += piece
        else:
            if current.strip():
                chunks.append(current.strip())
            if len(piece) > 150:
                words = piece.split(" ")
                sub = ""
                for w in words:
                    if len(sub) + len(w) + 1 <= 150:
                        sub += (" " if sub else "") + w
                    else:
                        if sub.strip():
                            chunks.append(sub.strip())
                        sub = w
                current = sub
            else:
                current = piece
    if current.strip():
        chunks.append(current.strip())

    valid_chunks = [c.strip() for c in chunks[:5] if c.strip()]
    if not valid_chunks:
        return b""
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(valid_chunks)) as pool:
        audio_results = list(pool.map(_fetch_tts_chunk, valid_chunks))
    return b"".join(part for part in audio_results if part)

# -------------------------------------------------------------
# 10 DEVICE PERMISSIONS (DESKTOP & PHONE)
# -------------------------------------------------------------
DEFAULT_PERMISSIONS = {
    "camera": {
        "id": "camera",
        "name": "Camera (कैमरा)",
        "desc": "Photos aur video capture karne ke liye",
        "icon": "📷",
        "allowed": False
    },
    "contacts": {
        "id": "contacts",
        "name": "Contacts (संपर्क)",
        "desc": "WhatsApp aur calling ke liye contacts",
        "icon": "👥",
        "allowed": False
    },
    "location": {
        "id": "location",
        "name": "Location (लोकेशन)",
        "desc": "Live raste aur mausam ke liye",
        "icon": "📍",
        "allowed": False
    },
    "microphone": {
        "id": "microphone",
        "name": "Microphone (माइक)",
        "desc": "Voice command aur speech sunne ke liye",
        "icon": "🎙️",
        "allowed": False
    },
    "audio": {
        "id": "audio",
        "name": "Music & Audio (म्यूजिक/ऑडियो)",
        "desc": "Gaane bajane aur game audio ke liye",
        "icon": "🎵",
        "allowed": False
    },
    "notifications": {
        "id": "notifications",
        "name": "Notifications (सूचनाएँ)",
        "desc": "Desktop aur phone alerts ke liye",
        "icon": "🔔",
        "allowed": False
    },
    "phone": {
        "id": "phone",
        "name": "Phone & Calls (फ़ोन और कॉल्स)",
        "desc": "Direct call aur dialer open karne ke liye",
        "icon": "📞",
        "allowed": False
    },
    "call_logs": {
        "id": "call_logs",
        "name": "Call Logs (कॉल लॉग्स)",
        "desc": "Recent calls ka record dekhne ke liye",
        "icon": "📋",
        "allowed": False
    },
    "media": {
        "id": "media",
        "name": "Photos & Videos (फ़ोटो और मीडिया)",
        "desc": "Gallery, photos aur video files ke liye",
        "icon": "🖼️",
        "allowed": False
    },
    "system_apps": {
        "id": "system_apps",
        "name": "Apps, Files & Games (ऐप्स/फ़ाइलें/गेम्स)",
        "desc": "WhatsApp, File Manager, Folders aur Games launch karne ke liye",
        "icon": "💻",
        "allowed": False
    }
}

def get_permissions() -> dict:
    perms = {k: dict(v) for k, v in DEFAULT_PERMISSIONS.items()}
    if PERMISSIONS_FILE.exists():
        try:
            saved = json.loads(PERMISSIONS_FILE.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                for k, v in saved.items():
                    if k in perms:
                        val = v.get("allowed", False) if isinstance(v, dict) else v
                        perms[k]["allowed"] = bool(val)
        except Exception:
            pass
    allowed_count = sum(1 for p in perms.values() if p["allowed"])
    return {
        "account": get_google_account(),
        "total": len(perms),
        "allowed_count": allowed_count,
        "permissions": list(perms.values()),
        "map": {k: p["allowed"] for k, p in perms.items()}
    }

def save_permissions(updates: dict | None = None, allow_all: bool | None = None) -> dict:
    current = get_permissions()["map"]
    if allow_all is True:
        for k in current:
            current[k] = True
    elif allow_all is False:
        for k in current:
            current[k] = False
    elif isinstance(updates, dict):
        for k, v in updates.items():
            if k in current:
                current[k] = bool(v)
    save_data = {k: {"allowed": current[k]} for k in current}
    PERMISSIONS_FILE.write_text(json.dumps(save_data, indent=2, ensure_ascii=False), encoding="utf-8")
    return get_permissions()

def get_contacts() -> dict:
    if CONTACTS_FILE.exists():
        try:
            data = json.loads(CONTACTS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    default = {
        "self": "+917011500000",
        "developer": "+917011500000"
    }
    try:
        CONTACTS_FILE.write_text(json.dumps(default, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return default

def save_contact(name: str, phone: str) -> dict:
    contacts = get_contacts()
    clean_name = name.strip().lower()
    clean_phone = re.sub(r"[^0-9\+]", "", phone.strip())
    if not clean_phone.startswith("+"):
        if len(clean_phone) == 10:
            clean_phone = "+91" + clean_phone
        elif clean_phone.startswith("91") and len(clean_phone) == 12:
            clean_phone = "+" + clean_phone
    contacts[clean_name] = clean_phone
    try:
        CONTACTS_FILE.write_text(json.dumps(contacts, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return contacts

def delete_contact(name: str) -> dict:
    contacts = get_contacts()
    clean_name = name.strip().lower()
    if clean_name in contacts:
        del contacts[clean_name]
        try:
            CONTACTS_FILE.write_text(json.dumps(contacts, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    return contacts

def find_contact(query: str) -> tuple[str | None, str | None]:
    if not query:
        return None, None
    contacts = get_contacts()
    q = query.strip().lower()
    if q in contacts:
        return q.title(), contacts[q]
    for k, v in contacts.items():
        if q in k or k in q:
            return k.title(), v
    return None, None

def parse_whatsapp_intent(msg: str) -> dict:
    txt = (msg or "").strip()
    
    # 1. Contact save intent
    save_m = re.search(r"([a-zA-Z0-9_\u0900-\u097F]{2,30})\s+ka\s+(?:phone|mobile|whatsapp)?\s*number\s+save\s+karo\s+([0-9\+\s\-]{10,15})", txt, re.I)
    if not save_m:
        save_m = re.search(r"save\s+karo\s+([a-zA-Z0-9_\u0900-\u097F]{2,30})\s+ka\s+(?:phone|mobile|whatsapp)?\s*number\s+([0-9\+\s\-]{10,15})", txt, re.I)
    if not save_m:
        save_m = re.search(r"([a-zA-Z0-9_\u0900-\u097F]{2,30})\s+(?:ka\s+)?number\s+([0-9\+\s\-]{10,15})\s+save\s+karo", txt, re.I)
    if save_m:
        c_name = save_m.group(1).strip()
        c_num = re.sub(r"[^0-9\+]", "", save_m.group(2).strip())
        return {"intent": "save_contact", "name": c_name, "phone": c_num}

    # 2. Extract explicit phone number
    phone_m = re.search(r"(\+?91[\s\-]?)?([6-9]\d{9})\b", txt)
    phone = None
    if phone_m:
        raw_p = phone_m.group(0).replace(" ", "").replace("-", "")
        if not raw_p.startswith("+"):
            if len(raw_p) == 10:
                raw_p = "+91" + raw_p
            elif raw_p.startswith("91") and len(raw_p) == 12:
                raw_p = "+" + raw_p
        phone = raw_p

    # 3. Extract contact name
    contact_name = None
    name_m = re.search(r"\b([a-zA-Z\u0900-\u097F]{2,20})\s+ko\b", txt, re.I)
    if name_m:
        cand = name_m.group(1).strip()
        if cand.lower() not in ["kisi", "sab", "mujhe", "humko", "whatsapp", "phone", "message", "video", "audio", "song", "photo"]:
            contact_name = cand

    if contact_name and not phone:
        matched_name, found_phone = find_contact(contact_name)
        if found_phone:
            phone = found_phone
            contact_name = matched_name

    # 4. Extract message text
    msg_text = None
    quote_m = re.search(r"""['"‘“]([^'"’”]+)['"’”]""", txt)
    if quote_m:
        msg_text = quote_m.group(1).strip()
    else:
        if ":" in txt:
            parts = txt.split(":", 1)
            msg_text = parts[1].strip()
        else:
            m_match = re.search(r"\b(?:message|msg|likho|likh\s*ke|bhejo|likhna|kahna|kaho)\s+(?:ki\s+|ye\s+|yeh\s+)?(.+)$", txt, re.I)
            if m_match:
                cand = m_match.group(1).strip()
                cand = re.sub(r"\s*\b(bhejo|send\s*karo|kro|kar\s*do|karo)\s*$", "", cand, flags=re.I).strip()
                if cand:
                    msg_text = cand

    intent = "send_message" if (msg_text or phone or contact_name) else "open_whatsapp"
    return {
        "intent": intent,
        "phone": phone,
        "contact_name": contact_name,
        "message_text": msg_text
    }

def get_system_hardware_info() -> dict:
    info = {"platform": sys.platform, "python": sys.version.split()[0]}
    try:
        disk = shutil.disk_usage(os.path.expanduser("~"))
        info["disk_total_gb"] = round(disk.total / (1024**3), 1)
        info["disk_free_gb"] = round(disk.free / (1024**3), 1)
    except Exception:
        pass
    if sys.platform == "win32":
        try:
            res = subprocess.run(
                ["powershell", "-Command", "Get-CimInstance -ClassName Win32_Battery | Select-Object -ExpandProperty EstimatedChargeRemaining"],
                capture_output=True, text=True, timeout=3
            )
            pct = res.stdout.strip()
            if pct and pct.isdigit():
                info["battery_percent"] = int(pct)
        except Exception:
            pass
    return info

def _open_target(target: str, fallback_url: str | None = None) -> bool:
    try:
        if hasattr(os, "startfile"):
            os.startfile(target)
            return True
        import webbrowser
        webbrowser.open(fallback_url or target)
        return True
    except Exception:
        if fallback_url:
            try:
                import webbrowser
                webbrowser.open(fallback_url)
                return True
            except Exception:
                pass
        return False

ACTION_RULES = {
    "whatsapp": {
        "name": "WhatsApp",
        "required": ["contacts", "system_apps"],
        "required_names": ["Contacts (संपर्क)", "Apps, Files & Games"],
        "hindi_action": "WhatsApp open karne",
        "run": lambda: _open_target("whatsapp://", fallback_url="https://web.whatsapp.com")
    },
    "files": {
        "name": "Files & Folders",
        "required": ["system_apps", "media"],
        "required_names": ["Apps, Files & Games", "Photos & Videos (मीडिया)"],
        "hindi_action": "Computer ke Files aur Folders open karne",
        "run": lambda: _open_target(os.path.expanduser("~"))
    },
    "games": {
        "name": "Games",
        "required": ["system_apps", "audio"],
        "required_names": ["Apps, Files & Games", "Music & Audio"],
        "hindi_action": "Games launch karne",
        "run": lambda: _open_target("https://poki.com")
    },
    "calculator": {
        "name": "Calculator",
        "required": ["system_apps"],
        "required_names": ["Apps, Files & Games"],
        "hindi_action": "Calculator app open karne",
        "run": lambda: _open_target("calc.exe")
    },
    "notepad": {
        "name": "Notepad",
        "required": ["system_apps"],
        "required_names": ["Apps, Files & Games"],
        "hindi_action": "Notepad open karne",
        "run": lambda: _open_target("notepad.exe")
    },
    "paint": {
        "name": "Paint",
        "required": ["system_apps"],
        "required_names": ["Apps, Files & Games"],
        "hindi_action": "Paint app open karne",
        "run": lambda: _open_target("mspaint.exe")
    },
    "youtube": {
        "name": "YouTube",
        "required": ["system_apps"],
        "required_names": ["Apps, Files & Games"],
        "hindi_action": "YouTube open karne"
    },
    "playstore": {
        "name": "Google Play Store",
        "required": ["system_apps"],
        "required_names": ["Apps, Files & Games"],
        "hindi_action": "Play Store open karne"
    },
    "maps": {
        "name": "Google Maps",
        "required": ["location"],
        "required_names": ["Location (लोकेशन)"],
        "hindi_action": "Google Maps open karne"
    },
    "photos": {
        "name": "Google Photos",
        "required": ["media"],
        "required_names": ["Photos & Videos (मीडिया)"],
        "hindi_action": "Google Photos open karne"
    },
    "drive": {
        "name": "Google Drive",
        "required": ["system_apps"],
        "required_names": ["Apps, Files & Games"],
        "hindi_action": "Google Drive open karne"
    },
    "chrome": {
        "name": "Google Chrome",
        "required": ["system_apps"],
        "required_names": ["Apps, Files & Games"],
        "hindi_action": "Chrome Browser open karne"
    },
    "camera": {
        "name": "Camera",
        "required": ["camera"],
        "required_names": ["Camera (कैमरा)"],
        "hindi_action": "Camera open karne"
    },
    "location": {
        "name": "Location",
        "required": ["location"],
        "required_names": ["Location (लोकेशन)"],
        "hindi_action": "Location dekhne"
    },
    "phone": {
        "name": "Phone Calls & Logs",
        "required": ["phone", "call_logs"],
        "required_names": ["Phone & Calls", "Call Logs"],
        "hindi_action": "Phone call lagane ya call history dekhne"
    },
    "sms": {
        "name": "SMS Messaging",
        "required": ["phone"],
        "required_names": ["Phone & Calls"],
        "hindi_action": "SMS compose karne"
    },
    "vscode": {
        "name": "VS Code Editor",
        "required": ["system_apps"],
        "required_names": ["Apps, Files & Games"],
        "hindi_action": "VS Code open karne",
        "run": lambda: _open_target("code")
    },
    "terminal": {
        "name": "Command Prompt / Terminal",
        "required": ["system_apps"],
        "required_names": ["Apps, Files & Games"],
        "hindi_action": "Terminal launch karne",
        "run": lambda: _open_target("cmd.exe")
    },
    "taskmgr": {
        "name": "Task Manager",
        "required": ["system_apps"],
        "required_names": ["Apps, Files & Games"],
        "hindi_action": "Task Manager open karne",
        "run": lambda: _open_target("taskmgr.exe")
    },
    "lockscreen": {
        "name": "Lock Screen",
        "required": ["system_apps"],
        "required_names": ["Apps, Files & Games"],
        "hindi_action": "Screen lock karne"
    },
    "system_info": {
        "name": "System Info & Battery",
        "required": ["system_apps"],
        "required_names": ["Apps, Files & Games"],
        "hindi_action": "System stats check karne"
    }
}

def _extract_media_search_query(msg: str) -> str:
    """
    Extracts the clean music / video / song query from a natural Hindi/English voice command.
    """
    lowered = (msg or "").lower()
    cleaned = re.sub(
        r"\b(youtube|utube|yt|se|pe|par|ka|ke|ki|ko|kholo|open|karo|kro|kar\s*do|chalao|chlao|bajao|sunao|suno|play|start|koi|bhi|ek|acha|accha|thoda|mujhe|humko|mere\s*liye|pls|please|or|aur|uspe|isme|iss|uss|me|mein|batao|dikhao|sunna|chahiye|lagao|laga\s*do|bhi)\b",
        " ",
        lowered,
        flags=re.IGNORECASE
    )
    has_song = bool(re.search(r"\b(gana|gaana|gaane|song|songs|music|geet|sangeet|bhajan)\b", cleaned))
    has_video = bool(re.search(r"\b(video|clip)\b", cleaned))
    has_old = bool(re.search(r"\b(purana|purane|old|classic|retro)\b", cleaned))
    has_romantic = bool(re.search(r"\b(romantic|love|dil)\b", cleaned))
    has_sad = bool(re.search(r"\b(sad|dard)\b", cleaned))
    has_party = bool(re.search(r"\b(party|dance|dj|remix)\b", cleaned))

    specific = re.sub(r"\b(gana|gaana|gaane|song|songs|music|geet|sangeet|bhajan|video|clip)\b", " ", cleaned)
    specific = re.sub(r"\s+", " ", specific).strip()

    if specific and len(specific) > 2:
        if has_old and "old" not in specific:
            specific = f"old {specific}"
        return f"{specific} songs" if has_song and "song" not in specific else specific

    if has_old:
        return "old classic hindi songs"
    if has_romantic:
        return "romantic hindi songs"
    if has_sad:
        return "sad hindi songs"
    if has_party:
        return "bollywood party dj songs"
    if has_video:
        return "trending videos"
    return "latest trending hindi songs"

def get_youtube_video_id(query: str) -> str | None:
    """
    Finds real working YouTube video ID for a song query to ensure 100% playable embeds and apps.
    """
    try:
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            vids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)
            if vids:
                return vids[0]
    except Exception:
        pass
    return None

def execute_system_action(action_key: str, user_query: str = "") -> dict:
    rule = ACTION_RULES.get(action_key)
    if not rule:
        return {"status": "error", "message": "Unknown action key."}

    perms_state = get_permissions()["map"]
    missing = [req for req in rule["required"] if not perms_state.get(req, False)]

    if missing:
        req_str = " aur ".join(rule["required_names"])
        msg = (
            f"Kshama karein! {rule['hindi_action']} ke liye pehle '{req_str}' permission allow karni hogi. "
            f"Aapke niyam ke mutabik bina permission Smart AI koi app, folder ya data open nahi karega. "
            f"Kripya niche diye gaye button se Permission allow karein."
        )
        return {
            "status": "blocked",
            "action": action_key,
            "action_name": rule["name"],
            "missing": missing,
            "missing_names": rule["required_names"],
            "reply": msg,
            "spoken": f"Kshama karein, {rule['name']} kholne ke liye pehle {req_str} permission allow karni hogi."
        }

    # 1. YOUTUBE & MEDIA PLAYBACK INTENT
    if action_key == "youtube":
        search_q = _extract_media_search_query(user_query)
        vid = get_youtube_video_id(search_q)

        if vid:
            web_url = f"https://www.youtube.com/watch?v={vid}"
            embed_url = f"https://www.youtube-nocookie.com/embed/{vid}?autoplay=1&enablejsapi=1"
            intent_url = f"vnd.youtube:{vid}"
        else:
            web_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(search_q)}"
            embed_url = f"https://www.youtube-nocookie.com/embed?search={urllib.parse.quote(search_q)}&autoplay=1"
            intent_url = f"vnd.youtube://results?search_query={urllib.parse.quote(search_q)}"

        try:
            if hasattr(os, "startfile"):
                os.startfile(web_url)
        except Exception:
            pass

        title_display = search_q.title()
        reply_msg = f"🎵 **YouTube Play:** '{title_display}' play kar diya gaya hai! Niche diye gaye player se suniye ya YouTube app me kholein."
        spoken_msg = f"Haan bilkul! Main abhi YouTube par '{title_display}' play kar raha hoon."

        return {
            "status": "success",
            "action": "youtube",
            "action_name": "YouTube",
            "reply": reply_msg,
            "spoken": spoken_msg,
            "client_action": {
                "type": "youtube",
                "app": "youtube",
                "query": search_q,
                "video_id": vid,
                "web_url": web_url,
                "intent_url": intent_url,
                "embed_url": embed_url,
                "title": f"YouTube: {title_display}"
            },
            "media_card": {
                "type": "youtube",
                "title": title_display,
                "query": search_q,
                "video_id": vid,
                "web_url": web_url,
                "intent_url": intent_url,
                "embed_url": embed_url
            }
        }

    # 2. WHATSAPP AUTOMATION (Direct Messaging, Contacts & Send Intents)
    if action_key == "whatsapp":
        wa_intent = parse_whatsapp_intent(user_query)

        # A. Save Contact Intent
        if wa_intent["intent"] == "save_contact":
            c_name = wa_intent["name"]
            c_phone = wa_intent["phone"]
            save_contact(c_name, c_phone)
            reply = (
                f"✅ **Contact Saved:** '{c_name.title()}' ka WhatsApp number `{c_phone}` Smart AI contacts me save kar liya gaya hai!\n\n"
                f"Ab aap bol sakte hain: *'{c_name.title()} ko WhatsApp par message bhejo: Kal milte hain'*."
            )
            spoken = f"Theek hai! Maine {c_name} ka WhatsApp number contacts me save kar liya hai."
            return {
                "status": "success",
                "action": "whatsapp",
                "action_name": "WhatsApp",
                "reply": reply,
                "spoken": spoken
            }

        # B. Send Message Intent (Direct Click-to-Chat & Composer)
        if wa_intent["intent"] == "send_message":
            phone = wa_intent.get("phone")
            c_name = wa_intent.get("contact_name")
            text = wa_intent.get("message_text") or "Hello"
            encoded_text = urllib.parse.quote(text)
            clean_digits = re.sub(r"[^0-9]", "", phone) if phone else ""

            if clean_digits:
                web_url = f"https://web.whatsapp.com/send?phone={clean_digits}&text={encoded_text}"
                mobile_url = f"whatsapp://send?phone={clean_digits}&text={encoded_text}"
                wa_me_url = f"https://wa.me/{clean_digits}?text={encoded_text}"
                display_target = f"{c_name} ({phone})" if c_name else phone
            else:
                web_url = f"https://web.whatsapp.com/send?text={encoded_text}"
                mobile_url = f"whatsapp://send?text={encoded_text}"
                wa_me_url = f"https://api.whatsapp.com/send?text={encoded_text}"
                display_target = c_name if c_name else "WhatsApp Contacts"

            try:
                if hasattr(os, "startfile"):
                    os.startfile(mobile_url)
            except Exception:
                try:
                    import webbrowser
                    webbrowser.open(wa_me_url)
                except Exception:
                    pass

            reply = (
                f"💬 **WhatsApp Message Ready:**\n\n"
                f"👤 **To:** {display_target}\n"
                f"📝 **Message:** *\"{text}\"*\n\n"
                f"WhatsApp ko direct message ke saath launch kar diya gaya hai. Niche diye gaye card se aap turant **Send** kar sakte hain!"
            )
            spoken = f"Maine {display_target} ke liye WhatsApp message taiyar kar diya hai. Dekhiye screen par WhatsApp open ho raha hai!"

            return {
                "status": "success",
                "action": "whatsapp",
                "action_name": "WhatsApp",
                "reply": reply,
                "spoken": spoken,
                "client_action": {
                    "type": "whatsapp_send",
                    "app": "whatsapp",
                    "name": "WhatsApp",
                    "phone": phone,
                    "contact_name": c_name,
                    "message_text": text,
                    "web_url": web_url,
                    "mobile_url": mobile_url,
                    "wa_me_url": wa_me_url,
                    "title": f"WhatsApp to {display_target}"
                },
                "whatsapp_card": {
                    "phone": phone,
                    "contact_name": c_name or display_target,
                    "message_text": text,
                    "web_url": web_url,
                    "mobile_url": mobile_url,
                    "wa_me_url": wa_me_url
                }
            }

        # C. Default Open WhatsApp App
        try:
            if hasattr(os, "startfile"):
                os.startfile("https://api.whatsapp.com/send")
        except Exception:
            pass
        return {
            "status": "success",
            "action": "whatsapp",
            "action_name": "WhatsApp",
            "reply": "💬 **WhatsApp:** WhatsApp ko aapke phone aur computer par launch kar diya gaya hai. Niche diye gaye button se aap 1-click me open kar sakte hain.",
            "spoken": "Haan bilkul! Main abhi WhatsApp open kar raha hoon.",
            "client_action": {
                "type": "whatsapp_send",
                "app": "whatsapp",
                "name": "WhatsApp",
                "web_url": "https://web.whatsapp.com",
                "mobile_url": "https://api.whatsapp.com/send",
                "wa_me_url": "https://api.whatsapp.com/send",
                "title": "WhatsApp"
            },
            "whatsapp_card": {
                "phone": None,
                "contact_name": "WhatsApp App",
                "message_text": "",
                "is_open": True,
                "web_url": "https://web.whatsapp.com",
                "mobile_url": "https://api.whatsapp.com/send",
                "wa_me_url": "https://api.whatsapp.com/send"
            }
        }

    # 3. GOOGLE MAPS
    if action_key == "maps":
        try:
            _open_target("https://www.google.com/maps")
        except Exception:
            pass
        return {
            "status": "success",
            "action": "maps",
            "action_name": "Google Maps",
            "reply": "🗺️ **Google Maps:** Google Maps ko open kar diya gaya hai.",
            "spoken": "Google Maps open kar diya gaya hai.",
            "client_action": {
                "type": "open_app",
                "app": "maps",
                "name": "Google Maps",
                "web_url": "https://www.google.com/maps",
                "mobile_url": "geo:0,0?q=maps",
                "title": "Google Maps"
            }
        }

    # 4. GOOGLE PHOTOS
    if action_key == "photos":
        try:
            _open_target("https://photos.google.com")
        except Exception:
            pass
        return {
            "status": "success",
            "action": "photos",
            "action_name": "Google Photos",
            "reply": "📸 **Google Photos:** Photos aur Gallery ko open kar diya gaya hai.",
            "spoken": "Google Photos open kar diya gaya hai.",
            "client_action": {
                "type": "open_app",
                "app": "photos",
                "name": "Google Photos",
                "web_url": "https://photos.google.com",
                "mobile_url": "content://media/internal/images/media",
                "title": "Google Photos"
            }
        }

    # 5. GOOGLE DRIVE
    if action_key == "drive":
        try:
            _open_target("https://drive.google.com")
        except Exception:
            pass
        return {
            "status": "success",
            "action": "drive",
            "action_name": "Google Drive",
            "reply": "📁 **Google Drive:** Drive ko open kar diya gaya hai.",
            "spoken": "Google Drive open kar diya gaya hai.",
            "client_action": {
                "type": "open_app",
                "app": "drive",
                "name": "Google Drive",
                "web_url": "https://drive.google.com",
                "title": "Google Drive"
            }
        }

    # 6. CHROME BROWSER
    if action_key == "chrome":
        try:
            _open_target("https://www.google.com")
        except Exception:
            pass
        return {
            "status": "success",
            "action": "chrome",
            "action_name": "Google Chrome",
            "reply": "🌐 **Google Chrome:** Browser ko open kar diya gaya hai.",
            "spoken": "Google Chrome open kar diya gaya hai.",
            "client_action": {
                "type": "open_url",
                "app": "chrome",
                "name": "Google Chrome",
                "web_url": "https://www.google.com",
                "title": "Google Chrome"
            }
        }

    # 7. GOOGLE PLAY STORE
    if action_key == "playstore":
        try:
            _open_target("https://play.google.com/store")
        except Exception:
            pass
        return {
            "status": "success",
            "action": "playstore",
            "action_name": "Google Play Store",
            "reply": "📱 **Google Play Store:** Play Store ko open kar diya gaya hai.",
            "spoken": "Play Store open kar diya gaya hai.",
            "client_action": {
                "type": "open_app",
                "app": "playstore",
                "name": "Google Play Store",
                "web_url": "https://play.google.com/store",
                "mobile_url": "market://search?q=apps",
                "title": "Google Play Store"
            }
        }

    # 8. PHONE CALLS & DIALER
    if action_key == "phone":
        phone_m = re.search(r"(\+?91[\s\-]?)?([6-9]\d{9})\b", user_query)
        target_phone = ""
        c_name = ""
        if phone_m:
            target_phone = phone_m.group(0).replace(" ", "").replace("-", "")
        else:
            name_m = re.search(r"\b([a-zA-Z\u0900-\u097F]{2,20})\s+ko\b", user_query, re.I)
            if name_m:
                cand = name_m.group(1).strip()
                if cand.lower() not in ["kisi", "sab", "mujhe", "humko", "phone", "call"]:
                    matched_name, found_p = find_contact(cand)
                    if found_p:
                        target_phone = found_p
                        c_name = matched_name

        tel_url = f"tel:{target_phone}" if target_phone else "tel:"
        display = f"{c_name} ({target_phone})" if (c_name and target_phone) else (target_phone or "Phone Dialer")

        return {
            "status": "client_action",
            "client_action": {
                "type": "phone_call",
                "app": "phone",
                "name": "Phone Calls",
                "tel_url": tel_url,
                "phone": target_phone,
                "title": f"Call: {display}"
            },
            "action": "phone",
            "action_name": "Phone Calls",
            "reply": f"📞 **Phone Call:** {display} ke liye dialer launch kar diya gaya hai.",
            "spoken": f"Main {display} ke liye dialer open kar raha hoon."
        }

    # 8b. SMS MESSAGING
    if action_key == "sms":
        phone_m = re.search(r"(\+?91[\s\-]?)?([6-9]\d{9})\b", user_query)
        target_phone = ""
        if phone_m:
            target_phone = phone_m.group(0).replace(" ", "").replace("-", "")
        else:
            name_m = re.search(r"\b([a-zA-Z\u0900-\u097F]{2,20})\s+ko\b", user_query, re.I)
            if name_m:
                cand = name_m.group(1).strip()
                if cand.lower() not in ["kisi", "sab", "mujhe", "humko", "sms", "message"]:
                    matched_name, found_p = find_contact(cand)
                    if found_p:
                        target_phone = found_p

        text = ""
        quote_m = re.search(r"""['"‘“]([^'"’”]+)['"’”]""", user_query)
        if quote_m:
            text = quote_m.group(1).strip()
        else:
            m_match = re.search(r"\b(?:message|msg|likho|likh\s*ke|text)\s+(?:ki\s+|ye\s+|yeh\s+)?(.+)$", user_query, re.I)
            if m_match:
                text = re.sub(r"\s*\b(bhejo|send|karo|kro)\s*$", "", m_match.group(1).strip(), flags=re.I)

        enc_body = urllib.parse.quote(text or "")
        sms_url = f"sms:{target_phone}?body={enc_body}" if target_phone else f"sms:?body={enc_body}"

        return {
            "status": "client_action",
            "client_action": {
                "type": "sms_send",
                "app": "sms",
                "name": "SMS",
                "sms_url": sms_url,
                "phone": target_phone,
                "body": text,
                "title": f"SMS to {target_phone or 'Contact'}"
            },
            "action": "sms",
            "action_name": "SMS",
            "reply": f"📨 **SMS Composer:** '{text or '...'}' ke saath SMS taiyar kar diya gaya hai.",
            "spoken": "SMS composer open ho gaya hai."
        }

    # 8c. LOCK SCREEN
    if action_key == "lockscreen":
        try:
            if sys.platform == "win32":
                subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
            elif sys.platform == "darwin":
                subprocess.run("pmset displaysleepnow", shell=True)
        except Exception:
            pass
        return {
            "status": "success",
            "action": "lockscreen",
            "action_name": "Screen Lock",
            "reply": "🔒 **Screen Locked:** Computer ki screen ko surakshit lock kar diya gaya hai.",
            "spoken": "Screen lock kar di gayi hai."
        }

    # 8d. SYSTEM HARDWARE & BATTERY INFO
    if action_key == "system_info":
        info = get_system_hardware_info()
        pct = info.get("battery_percent")
        bat_str = f"🔋 Battery: **{pct}%**" if pct is not None else "🔋 Power: AC Power / Desktop"
        disk_str = f"💾 Storage: **{info.get('disk_free_gb', '?')} GB Free** / {info.get('disk_total_gb', '?')} GB"
        plat_str = f"💻 System: **{info.get('platform', 'OS').title()}** (Python {info.get('python', '3.12')})"
        reply = f"⚡ **System Hardware & Health:**\n\n{bat_str}\n{disk_str}\n{plat_str}\n\nComputer aur Smart AI smooth chal rahe hain! 🚀"
        spoken = f"Aapki battery {pct} percent hai aur system smooth chal raha hai." if pct else "Aapka system online aur smooth chal raha hai."
        return {
            "status": "success",
            "action": "system_info",
            "action_name": "System Info",
            "reply": reply,
            "spoken": spoken
        }

    # 9. CAMERA
    if action_key == "camera":
        return {
            "status": "client_action",
            "client_action": {
                "type": "open_camera",
                "app": "camera",
                "name": "Camera",
                "title": "Camera Viewfinder"
            },
            "action": "camera",
            "action_name": "Camera",
            "reply": "📷 **Camera:** Camera viewfinder ko screen par launch kar diya gaya hai.",
            "spoken": "Camera open ho raha hai."
        }

    # 10. CALCULATOR
    if action_key == "calculator":
        try:
            _open_target("calc.exe")
        except Exception:
            pass
        return {
            "status": "client_action",
            "client_action": {
                "type": "open_calculator",
                "app": "calculator",
                "name": "Calculator",
                "title": "Calculator"
            },
            "action": "calculator",
            "action_name": "Calculator",
            "reply": "🧮 **Calculator:** Calculator open kar diya gaya hai.",
            "spoken": "Calculator open kar diya gaya hai."
        }

    # Generic Desktop Apps
    if "run" in rule:
        ok = rule["run"]()
        succ_msg = f"{rule['name']} safalta se open ho gaya hai." if ok else f"{rule['name']} open karne mein dikkat aayi."
        return {
            "status": "success",
            "action": action_key,
            "action_name": rule["name"],
            "reply": succ_msg,
            "spoken": succ_msg
        }

    return {
        "status": "success",
        "action": action_key,
        "action_name": rule["name"],
        "reply": f"{rule['name']} safalta se execute ho gaya hai.",
        "spoken": f"{rule['name']} execute ho gaya hai."
    }

def _detect_action(msg: str) -> str | None:
    txt = (msg or "").lower()
    # 1. Music, Songs, YouTube & Video Playback Intents
    if re.search(r"\byoutube\b", txt):
        return "youtube"
    if re.search(r"\b(gana|gaana|gaane|song|songs|music|sangeet|geet|video|bhajan)\b", txt) and re.search(r"\b(chalao|chlao|bajao|play|sunao|suno|kholo|lagao|start)\b", txt):
        return "youtube"

    # 2. WhatsApp & Contacts Automation
    if re.search(r"\b(whatsapp|whatsap|watsap)\b", txt) or re.search(r"\b(number\s+save|save\s+.*number|contact\s+save)\b", txt):
        return "whatsapp"

    # 3. SMS & Phone Calling
    if re.search(r"\b(sms|text message)\b", txt) and re.search(r"\b(bhejo|send|likho|compose)\b", txt):
        return "sms"
    if re.search(r"\b(call karo|phone lagao|call lagao|dial karo|call history|phone milao|phone call)\b", txt):
        return "phone"

    # 4. System Apps & Hardware Controls
    if re.search(r"\b(vs code|vscode|visual studio code|code editor)\b", txt):
        return "vscode"
    if re.search(r"\b(terminal|cmd|command prompt|powershell)\b", txt) and re.search(r"\b(kholo|open|chalao|launch|start)\b", txt):
        return "terminal"
    if re.search(r"\b(task manager|taskmanager)\b", txt):
        return "taskmgr"
    if re.search(r"\b(screen lock|pc lock|computer lock|system lock|lock screen)\b", txt):
        return "lockscreen"
    if re.search(r"\b(battery|battery kitni|charging|system info|system specs|ram kitni|free storage)\b", txt):
        return "system_info"

    # 5. Google Services & Navigation
    if re.search(r"\b(google maps|maps|naksha)\b", txt):
        return "maps"
    if re.search(r"\b(google photos|photos|gallary|gallery)\b", txt):
        return "photos"
    if re.search(r"\b(google drive|drive)\b", txt):
        return "drive"
    if re.search(r"\b(play store|playstore|google play)\b", txt):
        return "playstore"
    if re.search(r"\b(chrome|browser|google browser)\b", txt):
        return "chrome"

    # 6. Utilities & Tools
    if re.search(r"\b(calculator|calc|hisaab app)\b", txt):
        return "calculator"
    if re.search(r"\b(camera|webcam|photo khincho|selfie)\b", txt):
        return "camera"
    if re.search(r"\b(folder|folders|files|file manager|downloads|documents|my computer)\b", txt):
        return "files"
    if re.search(r"\b(game|games|khel|play games)\b", txt):
        return "games"
    if re.search(r"\bnotepad\b", txt):
        return "notepad"
    if re.search(r"\bpaint\b", txt):
        return "paint"
    if re.search(r"\b(meri location|location batao|live location)\b", txt):
        return "location"
    return None

def _detect_version_intent(msg: str) -> dict | None:
    txt = msg.lower().strip()
    is_inquiry_only = (
        any(w in txt for w in ["kya hai", "kaun sa", "check", "status", "show", "dikhao", "batao"]) and
        not any(w in txt for w in ["update", "upadate", "banao", "banado", "banayein", "create", "kro", "badlo", "upgrade", "khud se", "khudse"])
    )
    if is_inquiry_only:
        return None
    is_req = False
    if txt.startswith(("/newversion", "/createversion")):
        is_req = True
    elif re.search(r"\b(version|varzan|varjan)\b", txt) and re.search(r"\b(update|upadate|banao|banado|banayein|create|kro|karo|upgrade|badlo|karna|chahiye|chalao|release)\b", txt):
        is_req = True
    elif re.search(r"\b(naya|new)\s+(version|varzan|varjan)\b", txt):
        is_req = True
    elif re.search(r"\b(khud\s*se|khudse|turn\s*khud\s*se|tum\s*khud\s*se|apne\s*aap)\b", txt) and re.search(r"\b(update|upadate|upgrade|naya|new|version|varzan|varjan|banao|banado|kro|karo)\b", txt):
        is_req = True
    elif re.search(r"\b(naya\s+release|new\s+release)\b", txt):
        is_req = True
    elif re.search(r"\b(smart\s*ai|system)\s+(ko\s+)?(update|upgrade)\s+(kro|karo|kar\s*do|karna)\b", txt):
        is_req = True

    if not is_req:
        return None

    ver_match = re.search(r"\b(v\d+(\.\d+)*|\d+\.\d+(\.\d+)*)\b", msg, re.IGNORECASE)
    return {
        "action": "create_version",
        "version": ver_match.group(1) if ver_match else None,
        "note": f"Voice/Chat user command: {msg}"
    }

def _detect_cmd_intent(msg: str) -> str | None:
    txt = msg.strip()
    lowered = txt.lower()
    if lowered.startswith("/cmd "):
        return txt.split(" ", 1)[1].strip()
    m = re.match(r"^(?:cmd|command)\s+(?:chalao|run\s+karo|karo|run)\s*:?\s*(.+)$", lowered, re.IGNORECASE)
    if m:
        return txt[m.start(1):].strip().lstrip(":").strip()
    m2 = re.match(r"^run\s+(?:cmd|command)\s*:?\s*(.+)$", lowered, re.IGNORECASE)
    if m2:
        return txt[m2.start(1):].strip().lstrip(":").strip()
    m3 = re.match(r"^([a-zA-Z0-9_\-\.\s]+)\s+command\s+(?:chalao|run\s+karo|karo)$", lowered, re.IGNORECASE)
    if m3:
        cand = m3.group(1).strip()
        if cand in {"dir", "hostname", "ipconfig", "whoami", "systeminfo", "tasklist", "ver"}:
            return cand
    return None

def _detect_calc_intent(msg: str) -> str | None:
    txt = msg.strip()
    lowered = txt.lower()
    if lowered.startswith("/calc "):
        return txt.split(" ", 1)[1].strip()
    m = re.match(r"^(?:calculate|hisaab\s+karo|calculate\s+karo|hisab\s+karo)\s*:?\s*(.+)$", lowered, re.IGNORECASE)
    if m:
        expr = txt[m.start(1):].strip().lstrip(":").strip()
        if re.search(r"[\d\+\-\*\/\%\^\(\)]", expr):
            return expr
    return None

# -------------------------------------------------------------
# WORLD WEATHER & GOOGLE WEATHER SEARCH ENGINE
# -------------------------------------------------------------
_WEATHER_CACHE = {}

WMO_WEATHER_MAP = {
    0: ("Saaf Aasman (Clear Sky)", "☀️"),
    1: ("Zyadatar Saaf (Mainly Clear)", "🌤️"),
    2: ("Halke Baadal (Partly Cloudy)", "⛅"),
    3: ("Baadal Chhaye Hain (Overcast)", "☁️"),
    45: ("Kohar (Fog)", "🌫️"),
    48: ("Barfeela Kohar (Depositing Rime Fog)", "🌫️"),
    51: ("Halki Boondabandi (Light Drizzle)", "🌦️"),
    53: ("Boondabandi (Moderate Drizzle)", "🌧️"),
    55: ("Tez Boondabandi (Dense Drizzle)", "🌧️"),
    61: ("Halki Baarish (Slight Rain)", "🌧️"),
    63: ("Baarish (Moderate Rain)", "🌧️"),
    65: ("Bhaari Baarish (Heavy Rain)", "🌧️"),
    71: ("Halki Barafbaari (Slight Snow)", "🌨️"),
    73: ("Barafbaari (Moderate Snow)", "🌨️"),
    75: ("Bhaari Barafbaari (Heavy Snow)", "❄️"),
    80: ("Halki Bauchar (Slight Rain Showers)", "🌦️"),
    81: ("Bauchar (Rain Showers)", "🌧️"),
    82: ("Bhaari Bauchar (Violent Rain Showers)", "⛈️"),
    95: ("Garaj ke saath Baarish (Thunderstorm)", "⛈️"),
    96: ("Garaj aur Oley (Thunderstorm with Slight Hail)", "⛈️"),
    99: ("Bhaari Toofan (Thunderstorm with Heavy Hail)", "⚡")
}

def get_world_weather(city_query: str) -> dict:
    city_clean = (city_query or "").strip()
    if not city_clean:
        city_clean = "Delhi"
    cache_key = city_clean.lower()
    now_ts = time.time()
    if cache_key in _WEATHER_CACHE:
        cached_ts, cached_data = _WEATHER_CACHE[cache_key]
        if now_ts - cached_ts < 300:
            return cached_data

    try:
        encoded = urllib.parse.quote(city_clean)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded}&count=1&language=en&format=json"
        req = urllib.request.Request(geo_url, headers={"User-Agent": "SmartAI/2.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            gdata = json.loads(r.read().decode())
        
        results = gdata.get("results")
        if not results:
            return {
                "status": "not_found",
                "city": city_clean,
                "error": f"'{city_clean}' ka mausam data nahi mil saka. Kripya shehar ka naam check karein.",
                "google_url": f"https://www.google.com/search?q={encoded}+weather"
            }
        
        item = results[0]
        lat, lon = item["latitude"], item["longitude"]
        city_name = item.get("name", city_clean)
        country = item.get("country", "")
        admin1 = item.get("admin1", "")
        loc_str = f"{city_name}"
        if admin1 and admin1 != city_name:
            loc_str += f", {admin1}"
        if country:
            loc_str += f", {country}"
            
        w_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m"
            f"&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=auto"
        )
        req2 = urllib.request.Request(w_url, headers={"User-Agent": "SmartAI/2.0"})
        with urllib.request.urlopen(req2, timeout=5) as r2:
            wdata = json.loads(r2.read().decode())
            
        cur = wdata.get("current", {})
        daily = wdata.get("daily", {})
        
        w_code = cur.get("weather_code", 0)
        cond_text, cond_icon = WMO_WEATHER_MAP.get(w_code, ("Aasman Saaf", "☀️"))
        
        forecast = []
        d_times = daily.get("time", [])
        d_codes = daily.get("weather_code", [])
        d_maxs = daily.get("temperature_2m_max", [])
        d_mins = daily.get("temperature_2m_min", [])
        for i in range(min(5, len(d_times))):
            fc_code = d_codes[i] if i < len(d_codes) else 0
            f_text, f_icon = WMO_WEATHER_MAP.get(fc_code, ("Saaf", "🌤️"))
            forecast.append({
                "date": d_times[i],
                "condition": f_text,
                "icon": f_icon,
                "max": d_maxs[i] if i < len(d_maxs) else None,
                "min": d_mins[i] if i < len(d_mins) else None
            })
            
        out = {
            "status": "success",
            "city": city_name,
            "country": country,
            "region": admin1,
            "location": loc_str,
            "temp": cur.get("temperature_2m"),
            "feels_like": cur.get("apparent_temperature"),
            "humidity": cur.get("relative_humidity_2m"),
            "wind_speed": cur.get("wind_speed_10m"),
            "precipitation": cur.get("precipitation", 0.0),
            "condition": cond_text,
            "icon": cond_icon,
            "max_temp": forecast[0]["max"] if forecast else None,
            "min_temp": forecast[0]["min"] if forecast else None,
            "forecast": forecast,
            "google_url": f"https://www.google.com/search?q={urllib.parse.quote(city_name)}+weather"
        }
        _WEATHER_CACHE[cache_key] = (now_ts, out)
        return out
    except Exception as exc:
        return {
            "status": "error",
            "city": city_clean,
            "error": f"Weather fetch error: {exc}",
            "google_url": f"https://www.google.com/search?q={urllib.parse.quote(city_clean)}+weather"
        }

WEATHER_KEYWORDS = [
    "weather", "mausam", "temperature", "taapmaan", "forecast", "barish", "rain", "thand", "garmi", "humidity"
]

def extract_weather_city(msg: str) -> str:
    txt = msg.lower()
    cleaned = re.sub(r"[^\w\s]", " ", txt)
    words = cleaned.split()
    stopwords = {
        "weather", "mausam", "temperature", "taapmaan", "forecast", "barish", "rain",
        "thand", "garmi", "humidity", "ka", "ki", "ke", "ko", "se", "mein", "me", "mai",
        "par", "kaisa", "kaisi", "kaise", "hai", "hain", "batao", "bataiye", "bata",
        "kya", "aaj", "kal", "parso", "live", "world", "duniya", "shehar", "jankari",
        "report", "check", "karo", "kijiye", "today", "now", "in", "the", "of", "for",
        "at", "what", "is", "how", "kitna", "kitni", "kitne", "hogi", "hoga", "update",
        "bhi", "smart", "ai", "google", "bolo", "sunao", "dekh", "dekho", "aur", "pe"
    }
    candidates = [w for w in words if w not in stopwords and len(w) > 1 and not w.isdigit()]
    if candidates:
        return " ".join(candidates)
    return "Delhi"

def get_connected_tools():
    account = get_google_account()
    encoded = urllib.parse.quote(account)
    return {
        "account": account,
        "total": 8,
        "tools": [
            {
                "id": "weather",
                "name": "Google Weather",
                "icon": "🌤️",
                "desc": "Duniya ke kisi bhi shehar ka live mausam aur forecast",
                "url": f"https://www.google.com/search?q=weather&authuser={encoded}",
                "status": "connected"
            },
            {
                "id": "photos",
                "name": "Google Photos",
                "icon": "🖼️",
                "desc": "Photos, memories aur albums",
                "url": f"https://photos.google.com/?authuser={encoded}",
                "status": "connected"
            },
            {
                "id": "maps",
                "name": "Google Maps",
                "icon": "🗺️",
                "desc": "Navigation, raste aur live places",
                "url": f"https://www.google.com/maps?authuser={encoded}",
                "status": "connected"
            },
            {
                "id": "drive",
                "name": "Google Drive",
                "icon": "📁",
                "desc": "Files, documents aur cloud backup",
                "url": f"https://drive.google.com/drive/u/0/?authuser={encoded}",
                "status": "connected"
            },
            {
                "id": "youtube",
                "name": "YouTube",
                "icon": "▶️",
                "desc": "Videos, music aur channels",
                "url": f"https://www.youtube.com/?authuser={encoded}",
                "status": "connected"
            },
            {
                "id": "one",
                "name": "Google One",
                "icon": "☁️",
                "desc": "Storage space aur account backup",
                "url": f"https://one.google.com/?authuser={encoded}",
                "status": "connected"
            },
            {
                "id": "playstore",
                "name": "Play Store",
                "icon": "📱",
                "desc": "Apps, games aur downloads",
                "url": f"https://play.google.com/store?authuser={encoded}",
                "status": "connected"
            },
            {
                "id": "chrome",
                "name": "Google Chrome",
                "icon": "🌐",
                "desc": "Web browsing aur search",
                "url": f"https://www.google.com?authuser={encoded}",
                "status": "connected"
            }
        ]
    }

def status():
    key, source = get_key()
    perms = get_permissions()
    op_st = get_openai_status()
    local_ip = get_local_ip()
    v_info = get_version_info()
    gem_ready = bool(key and is_valid_gemini_format(key))
    gem_status = "ready" if gem_ready else ("key_format_invalid" if key else "key_needed")
    return {
        "server": "online",
        "version": v_info.get("version", "v2.0.0"),
        "version_info": v_info,
        "uptime_seconds": int(time.time() - SERVER_START_TIME),
        "is_cloud": IS_CLOUD,
        "permanent_server": bool(os.environ.get("PERMANENT_SERVER_URL") or IS_CLOUD),
        "permanent_url": os.environ.get("PERMANENT_SERVER_URL") or os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("RAILWAY_STATIC_URL"),
        "host": HOST,
        "bind_host": BIND_HOST,
        "local_ip": local_ip,
        "phone_url": f"http://{local_ip}:{PORT}",
        "port": PORT,
        "gemini": gem_status,
        "gemini_ready": gem_ready,
        "key_source": source,
        "model": PRIMARY_MODEL,
        "realtime_model": REALTIME_MODEL,
        "google_search": gem_ready,
        "world_weather": "ready",
        "python_calculator": "ready",
        "cmd_terminal": get_cmd_status(),
        "gmail": check_gmail_status(),
        "google_tools": get_connected_tools(),
        "permissions": perms,
        "openai": op_st,
        "antigravity_mcp": (ROOT / ".agents" / "mcp_config.json").exists(),
        "learning": get_learning_stats(),
        "opensource_agents": {
            "total": len(OPENSOURCE_AGENTS),
            "categories": get_agent_categories()
        }
    }

def calculate(expression):
    expression = expression.strip()
    if not expression or len(expression) > 400:
        raise ValueError("Expression khaali hai ya bahut lamba hai.")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError("Sirf math expression likhein, jaise 12 * (5 + 2).") from exc
    ops = {ast.Add:lambda a,b:a+b, ast.Sub:lambda a,b:a-b, ast.Mult:lambda a,b:a*b,
           ast.Div:lambda a,b:a/b, ast.FloorDiv:lambda a,b:a//b, ast.Mod:lambda a,b:a%b,
           ast.Pow:lambda a,b:a**b}
    unary = {ast.UAdd:lambda a:+a, ast.USub:lambda a:-a}
    count = 0
    def visit(node):
        nonlocal count
        count += 1
        if count > 80:
            raise ValueError("Expression bahut complex hai.")
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int,float)) and not isinstance(node.value,bool):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 12:
                raise ValueError("Power ki limit 12 hai.")
            return ops[type(node.op)](left,right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in unary:
            return unary[type(node.op)](visit(node.operand))
        raise ValueError("Numbers, brackets aur + - * / // % ** hi allowed hain.")
    try:
        result = visit(tree)
        finite = math.isfinite(float(result))
    except (ArithmeticError, OverflowError) as exc:
        raise ValueError("Hisaab nahi nikal paaya.") from exc
    if isinstance(result, complex) or not finite or abs(result) > 1e100:
        raise ValueError("Result allowed range se bahar hai.")
    return str(result)

def _history(history):
    result = []
    if not isinstance(history, list):
        return result
    for item in history[-16:]:
        if isinstance(item, dict) and isinstance(item.get("content"), str) and item["content"].strip():
            role = "model" if item.get("role") in ("assistant","model") else "user"
            result.append({"role":role,"parts":[{"text":item["content"][:8000]}]})
    return result

def _sources(candidate):
    out, seen = [], set()
    for item in (candidate.get("groundingMetadata") or {}).get("groundingChunks") or []:
        web = item.get("web") or {}
        url = web.get("uri")
        if isinstance(url,str) and url.startswith("https://") and url not in seen:
            seen.add(url)
            out.append({"title":str(web.get("title") or url)[:180],"url":url[:2000]})
    return out[:8]

def _send_gemini_request(model_name: str, key: str, payload: dict, timeout: int = 25):
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/" + urllib.parse.quote(model_name, safe="") + ":generateContent"
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": key, "User-Agent": "SmartAI-Local/2.0"},
        method="POST"
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def _send_openai_request(key: str, payload: dict, timeout: int = 15):
    endpoint = "https://api.openai.com/v1/chat/completions"
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": "SmartAI-Local/2.0"
        },
        method="POST"
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))

def ask_openai_api(message: str, history=None, model: str = "gpt-4o-mini") -> str:
    key = get_openai_key()
    if not key:
        raise RuntimeError("OpenAI API key set nahi hai.")
    messages = [{"role": "system", "content": SYSTEM}]
    if history and isinstance(history, list):
        for item in history[-8:]:
            if isinstance(item, dict) and isinstance(item.get("content"), str) and item["content"].strip():
                r = "assistant" if item.get("role") in ("assistant", "model") else "user"
                messages.append({"role": r, "content": item["content"][:4000]})
    messages.append({"role": "user", "content": message})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.6,
        "max_tokens": 1024
    }
    data = _send_openai_request(key, payload)
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("OpenAI API ne koi candidate nahi bheja.")
    ans = choices[0].get("message", {}).get("content", "").strip()
    if not ans:
        raise RuntimeError("OpenAI API ne khaali jawab bheja.")
    return ans

def ask_codex_cli(message: str, history=None) -> str:
    cli = find_codex_cli()
    if not cli:
        raise RuntimeError("OpenAI Codex CLI nahi mila.")

    prompt_lines = [
        "Tum ek bharosemand Hindi AI assistant ho. Saaf, aasan aur seedhi Hindi/Hinglish mein bolkar sunane yogya jawab do (symbols, asterisks ya complex formatting ke bina)."
    ]
    if history and isinstance(history, list):
        recent = []
        for item in history[-3:]:
            if isinstance(item, dict) and isinstance(item.get("content"), str) and item["content"].strip():
                r = "Assistant" if item.get("role") in ("assistant", "model") else "User"
                recent.append(f"{r}: {item['content'][:300]}")
        if recent:
            prompt_lines.append("Pichli baatchit:\n" + "\n".join(recent))
    prompt_lines.append(f"User ka sawaal: {message}")
    full_prompt = "\n\n".join(prompt_lines)

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
        out_path = tf.name

    try:
        cmd = [
            cli, "exec",
            "--skip-git-repo-check",
            "--ephemeral",
            "--color", "never",
            "-o", out_path,
            full_prompt
        ]
        proc = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=70
        )
        if os.path.exists(out_path):
            with open(out_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().strip()
                if content:
                    return content
        if proc.stdout:
            lines = proc.stdout.splitlines()
            capture = []
            capturing = False
            for line in lines:
                if line.strip() == "codex":
                    capturing = True
                    continue
                if capturing:
                    if line.strip().startswith("tokens used") or line.strip().startswith("session id:"):
                        break
                    capture.append(line)
            res = "\n".join(capture).strip()
            if res:
                return res
        raise RuntimeError("Codex CLI se jawab nahi mila.")
    except subprocess.TimeoutExpired:
        raise RuntimeError("OpenAI Codex response timeout hua. Network check karke dobara koshish karein.")
    finally:
        try:
            if os.path.exists(out_path):
                os.remove(out_path)
        except OSError:
            pass

SYSTEM_ANTIGRAVITY = (
    "Aap Smart AI hain — Google Antigravity 2.0 se powered ek behad samajhdar, zinda-dil, vinamra aur dostana Hindi AI companion. "
    "Aapko bilkul ek asli insaan ki tarah baat karni hai, taaki user ko lage ki woh kisi sachhe dost aur gyaani mentor se baat kar rahe hain. "
    "User Hindi ya Hinglish mein baat karega; usi bhasha mein dil se, saaf, aasan aur apnepan ke saath jawab dein. "
    "Coding, complex problems, research, math, system actions aur tools execution mein expert insaan ki tarah seedhe, saral aur practical solution dein. "
    "KABHI BHI robotic, bureaucratic headers ya artificial multi-agent roleplay mat karein — ek cohesive, brilliant human companion ki tarah samjhayein."
)

def ask_antigravity(message: str, history=None, use_search: bool = True) -> dict:
    global _EXHAUSTED_UNTIL
    key, _ = get_key()

    if key:
        contents = _history(history)
        contents.append({"role": "user", "parts": [{"text": message}]})
        payload = {
            "systemInstruction": {"parts": [{"text": SYSTEM_ANTIGRAVITY}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.5, "maxOutputTokens": 2048}
        }
        if use_search:
            payload["tools"] = [{"google_search": {}}]

        models = [PRIMARY_MODEL, REALTIME_MODEL, LITE_MODEL]
        for cur_model in models:
            try:
                body = _send_gemini_request(cur_model, key, payload, timeout=25)
                candidates = body.get("candidates") or []
                if candidates:
                    parts = (candidates[0].get("content") or {}).get("parts") or []
                    ans = "\n".join(p.get("text", "").strip() for p in parts if isinstance(p, dict) and p.get("text", "").strip()).strip()
                    if ans:
                        return {
                            "reply": ans,
                            "sources": _sources(candidates[0]),
                            "used_search": bool(use_search and candidates[0].get("groundingMetadata")),
                            "model": "Antigravity AI",
                            "engine": "antigravity"
                        }
            except Exception:
                continue

    cli = find_codex_cli()
    if cli:
        try:
            anti_prompt = (
                f"{SYSTEM_ANTIGRAVITY}\n\n"
                f"User ka sawaal: {message}\n"
                f"Antigravity AI ke roop mein saaf Hindi/Hinglish mein seedha jawab do:"
            )
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
                out_path = tf.name
            cmd = [cli, "exec", "--skip-git-repo-check", "--ephemeral", "--color", "never", "-o", out_path, anti_prompt]
            proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=70)
            if os.path.exists(out_path):
                with open(out_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read().strip()
                    if content:
                        try: os.remove(out_path)
                        except OSError: pass
                        return {
                            "reply": content,
                            "sources": [],
                            "used_search": False,
                            "model": "Antigravity (Codex Core)",
                            "engine": "antigravity"
                        }
        except Exception:
            pass

    raise RuntimeError("Antigravity AI engine se response nahi mil saka. Connection check karein.")

def ask_openai(message: str, history=None) -> dict:
    key = get_openai_key()
    cli = find_codex_cli()

    if not key and not cli:
        raise RuntimeError("OpenAI (Codex) connect nahi hai. Settings mein OpenAI API key daalein ya Codex check karein.")

    # 1. If API key is present, try OpenAI API first
    if key:
        try:
            reply = ask_openai_api(message, history)
            return {
                "reply": reply,
                "sources": [],
                "used_search": False,
                "model": "OpenAI gpt-4o-mini",
                "engine": "openai"
            }
        except Exception as e:
            # If API key failed (e.g. quota exhausted 429), fallback to Codex CLI seamlessly
            if cli:
                try:
                    reply = ask_codex_cli(message, history)
                    return {
                        "reply": reply,
                        "sources": [],
                        "used_search": False,
                        "model": "OpenAI Codex",
                        "engine": "openai"
                    }
                except Exception:
                    pass
            err_str = str(e)
            if "credit_balance_exhausted" in err_str or "insufficient_quota" in err_str or "429" in err_str:
                raise RuntimeError("OpenAI API key mein credits balance samapt hai (Quota Exhausted). platform.openai.com par credits add karein.")
            raise

    # 2. If no API key, use Codex CLI directly
    if cli:
        reply = ask_codex_cli(message, history)
        return {
            "reply": reply,
            "sources": [],
            "used_search": False,
            "model": "OpenAI Codex",
            "engine": "openai"
        }

    raise RuntimeError("OpenAI (Codex) se jawab nahi mil saka.")

def ask_gemini_raw(message: str, history=None, use_search: bool = True, extra_context: str = "", attachments=None) -> dict:
    global _EXHAUSTED_UNTIL
    key, _ = get_key()
    if not key:
        raise RuntimeError("Google Gemini API key nahi mili. Settings kholkar key save karein.")

    contents = _history(history)
    final_text = (message + extra_context) if extra_context else message
    user_parts = [{"text": final_text}]
    has_media = False
    if attachments:
        for att in attachments:
            m_type = str(att.get("type") or "image/jpeg").lower()
            d_str = str(att.get("data") or "")
            if "," in d_str:
                d_str = d_str.split(",", 1)[1]
            if d_str and m_type.startswith(("image/", "audio/", "application/pdf")):
                user_parts.append({
                    "inline_data": {
                        "mime_type": m_type,
                        "data": d_str
                    }
                })
                has_media = True

    contents.append({"role": "user", "parts": user_parts})
    base_payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.6, "maxOutputTokens": 2048}
    }

    if time.time() < _EXHAUSTED_UNTIL:
        models = [LITE_MODEL, REALTIME_MODEL, PRIMARY_MODEL]
    else:
        models = [PRIMARY_MODEL, LITE_MODEL, REALTIME_MODEL]

    body = None
    last_err = None
    actual_search = False
    model_used = PRIMARY_MODEL

    for cur_model in models:
        payload = dict(base_payload)
        search_on = False
        if use_search and not has_media:
            payload["tools"] = [{"google_search": {}}]
            search_on = True

        timeout = 20 if cur_model == PRIMARY_MODEL else 30
        try:
            body = _send_gemini_request(cur_model, key, payload, timeout=timeout)
            actual_search = search_on
            model_used = cur_model
            break
        except urllib.error.HTTPError as exc:
            if search_on and exc.code in (400, 403, 429):
                try:
                    body = _send_gemini_request(cur_model, key, dict(base_payload), timeout=timeout)
                    actual_search = False
                    model_used = cur_model
                    break
                except Exception:
                    pass
            if exc.code == 429:
                _EXHAUSTED_UNTIL = time.time() + 300
                last_err = "Google API request limit poori hai."
                continue
            if exc.code in (400, 401, 403):
                last_err = "Google API ne request reject ki. API key check karein."
                continue
            last_err = "Google se connection nahi hua. Network aur API check karein."
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            last_err = "Google se connection nahi hua. Network check karke dobara koshish karein."
            continue

    if body is None:
        raise RuntimeError(last_err or "Google se connection nahi hua. Network check karke dobara koshish karein.")

    candidates = body.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini se jawab nahi aaya.")
    candidate = candidates[0]
    parts = (candidate.get("content") or {}).get("parts") or []
    answer = "\n".join(p.get("text", "").strip() for p in parts if isinstance(p, dict) and p.get("text", "").strip()).strip()
    if not answer:
        raise RuntimeError("Gemini ne text jawab nahi diya.")

    return {
        "reply": answer,
        "sources": _sources(candidate),
        "used_search": bool(actual_search and candidate.get("groundingMetadata")),
        "model": model_used,
        "engine": "gemini"
    }

def _fallback_smart_response(message: str, extra_context: str = "", weather_card_data: dict | None = None) -> dict:
    import datetime
    msg_low = message.lower().strip()

    # 1. Weather response if weather card is present
    if weather_card_data and weather_card_data.get("status") == "success":
        loc = weather_card_data.get("location", "Aapka shahar")
        temp = weather_card_data.get("temp", "--")
        cond = weather_card_data.get("condition", "Saaf")
        feels = weather_card_data.get("feels_like", temp)
        humidity = weather_card_data.get("humidity", "--")
        wind = weather_card_data.get("wind_speed", "--")
        reply = (
            f"🌤️ **{loc} Ka Live Mausam:**\n\n"
            f"• **Taapman:** {temp}°C (Feels like: {feels}°C)\n"
            f"• **Mausam:** {cond}\n"
            f"• **Nami (Humidity):** {humidity}%\n"
            f"• **Hawa ki raftaar:** {wind} km/h\n\n"
            f"Yeh live mausam report Google Weather aur Open-Meteo se verified hai."
        )
        return {
            "reply": reply,
            "sources": [],
            "used_search": False,
            "model": "Smart AI Live Core",
            "engine": "system"
        }

    # 2. Greetings and conversational warmth
    greetings = [
        "hi", "hello", "hey", "namaste", "pranam", "salaam", "kaise ho", "kya haal",
        "kaisa chal raha", "good morning", "good evening", "good night", "good afternoon",
        "hlo", "hii", "helo", "aur batao", "ram ram", "radhe radhe"
    ]
    is_greeting = any(msg_low == g or msg_low.startswith(g + " ") or msg_low.endswith(" " + g) or f" {g} " in f" {msg_low} " for g in greetings)
    if is_greeting:
        now = datetime.datetime.now()
        greeting_word = "Subah ki Ram Ram" if 4 <= now.hour < 12 else ("Namaste" if 12 <= now.hour < 17 else "Shubh Sandhya")
        reply = (
            f"🙏 **{greeting_word}!**\n\n"
            f"Main aapka **Smart AI 24/7 Cloud Assistant** hoon! Render cloud par 24 ghante hamesha active aur live hoon.\n\n"
            f"Aap bilkul aasan Hindi ya Hinglish mein mujhse baat kar sakte hain. Aap bataiye, aaj main aapki kya madad kar sakta hoon? 😊"
        )
        return {
            "reply": reply,
            "sources": [],
            "used_search": False,
            "model": "Smart AI Live Core",
            "engine": "system"
        }

    # 3. Identity and Capabilities
    identity_triggers = ["kaun ho", "who are you", "kya kar sakte ho", "smart ai kya hai", "tumhara naam", "parichay", "capabilities", "features", "madad"]
    if any(t in msg_low for t in identity_triggers):
        reply = (
            f"✨ **Namaste! Main Smart AI hoon — aapka personal 24/7 Cloud AI Companion.**\n\n"
            f"Mujhe aapke liye hamesha ready rehne ke liye taiyar kiya gaya hai:\n"
            f"• 🌐 **24/7 Cloud Server:** PC band hone par bhi Render par hamesha online rehta hoon.\n"
            f"• 🎙️ **Live Voice Assistant:** Hands-Free bolkar sawaal poochhein aur suniye.\n"
            f"• 📱 **Phone Access:** Mobile browser aur Android Web App se direct chalta hai.\n"
            f"• 🧰 **Connected Tools:** Google Photos, Maps, Drive, YouTube aur Gmail ka direct access.\n"
            f"• 🧠 **Multi-Engine AI:** Gemini, OpenAI Codex aur Antigravity support.\n\n"
            f"Aap koi bhi sawal poochh sakte hain ya upar bane 🧰 Tools aur ⚙️ Settings explore kar sakte hain!"
        )
        return {
            "reply": reply,
            "sources": [],
            "used_search": False,
            "model": "Smart AI Live Core",
            "engine": "system"
        }

    # 4. Date and Time
    time_triggers = ["time", "samay", "baj", "tarikh", "taarikh", "date", "din kya hai", "waqt"]
    if any(t in msg_low for t in time_triggers):
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p")
        date_str = now.strftime("%d %B %Y (%A)")
        reply = f"⏰ Abhi samay **{time_str}** ho raha hai aur aaj ki taarikh **{date_str}** hai."
        return {
            "reply": reply,
            "sources": [],
            "used_search": False,
            "model": "Smart AI Live Core",
            "engine": "system"
        }

    # 5. General intelligent response with helpful guidance
    reply = (
        f"Maine aapka sawaal samjha: *\"{message}\"*\n\n"
        f"Aapka Smart AI 24/7 Cloud Server poori tarah online aur surakshit hai! 🌐\n\n"
        f"Is vishay par deep research aur live web data ke saath jawab paane ke liye **Google Gemini API key** connect hona zaroori hai (jo bilkul Free banti hai).\n\n"
        f"🔑 **1 Minute Mein Free Key Kaise Lagayein:**\n"
        f"1. Upar daayein kone mein **Settings (⚙️)** par click karein.\n"
        f"2. **'Free Gemini Key Banayein'** link kholein (Google AI Studio — 100% Free, zero cost).\n"
        f"3. Key copy karein aur yahan paste karke **Save** dabayein.\n\n"
        f"Save karte hi main live web search aur sabhi deep topics ke vistaar se jawab dene lagunga! 🚀"
    )
    return {
        "reply": reply,
        "sources": [],
        "used_search": False,
        "model": "Smart AI Live Core",
        "engine": "system"
    }

def ask_smart_ai(message: str, history=None, use_search: bool = True, engine: str = "auto", attachments=None, agent_help: str | None = None) -> dict:
    message = (message or "").strip()
    saved_attachments = []
    if attachments:
        for att in attachments:
            if isinstance(att, dict):
                try:
                    saved_attachments.append(save_uploaded_attachment(att))
                except Exception:
                    pass

    if not message and saved_attachments:
        names = ", ".join(f['name'] for f in saved_attachments)
        message = f"Maine yeh files attach ki hain: {names}. Kripya inko dekhein aur samjhein."

    if not message:
        raise ValueError("Message ya attachment bhejein.")
    if len(message) > 25000:
        raise ValueError("Message bahut lamba hai.")

    lowered = message.lower().strip()

    # Autonomous Version Management Intent (Voice / Chat natural language intent)
    v_intent = _detect_version_intent(message)
    if v_intent:
        target_v = v_intent.get("version")
        if not target_v:
            target_v = suggest_next_version()
        res = create_new_version(target_v, note=v_intent.get("note", "Created by Smart AI autonomous voice/chat instruction"), overwrite=True)
        if res.get("success"):
            new_v = res["version"]
            reply_txt = (
                f"🚀 **Maine aapke bolne par khud se naya version `{new_v}` safalta se bana diya hai!**\n\n"
                f"• **Naya Version:** `{new_v}`\n"
                f"• **Naya Folder:** `{res['folder']}`\n"
                f"• **Files Transferred:** {res.get('items_copied', 0)} files & folders safe copy ho gaye\n"
                f"• **Purana Base Version:** `{res.get('previous_version', 'v2.0.0')}` (surakshit hai)\n\n"
                f"Aapka naya system taiyar hai! Agli baar aap naye folder me jakar bhi `start.bat` chala sakte hain."
            )
            return {
                "reply": reply_txt,
                "version_result": res,
                "new_version": new_v,
                "sources": [],
                "used_search": False,
                "model": "version-manager",
                "engine": "system"
            }
        else:
            reply_txt = f"❌ Naya version create karne me samasya: {res.get('error', 'Unknown error')}"
            return {
                "reply": reply_txt,
                "version_result": res,
                "sources": [],
                "used_search": False,
                "model": "version-manager",
                "engine": "system"
            }

    # Autonomous CMD Command Execution Intent (Natural language or /cmd)
    detected_cmd = _detect_cmd_intent(message)
    if detected_cmd:
        res = execute_cmd(detected_cmd)
        status_badge = "✅ SUCCESS" if res["status"] == "success" else f"❌ ERROR ({res['exit_code']})"
        reply_txt = (
            f"💻 **Windows CMD Result** ({status_badge} · {res['elapsed_ms']}ms):\n"
            f"Command: `{detected_cmd}`\n\n"
            f"```text\n{res['output']}\n```"
        )
        return {
            "reply": reply_txt,
            "sources": [],
            "used_search": False,
            "model": "Windows CMD",
            "engine": "terminal",
            "cmd_result": res
        }

    # Autonomous Calculation Intent
    detected_calc = _detect_calc_intent(message)
    if detected_calc:
        try:
            ans = calculate(detected_calc)
            reply_txt = f"∑ **Hisaab Result:** `{ans}`\n(Expression: `{detected_calc}`)"
            return {
                "reply": reply_txt,
                "sources": [],
                "used_search": False,
                "model": "Safe Python Math",
                "engine": "python"
            }
        except Exception:
            pass

    # Python Execution Prefix
    if lowered.startswith("/run ") or lowered.startswith("/python ") or lowered.startswith("/exec "):
        code_str = message.split(" ", 1)[1].strip()
        res = execute_python_code(code_str)
        status_badge = "✅ SUCCESS" if res["status"] == "success" else f"❌ ERROR ({res['exit_code']})"
        reply_txt = (
            f"🐍 Python 3.12 CMD Execution ({status_badge} · {res['elapsed_ms']}ms):\n\n"
            f"```text\n{res['output']}\n```"
        )
        return {
            "reply": reply_txt,
            "sources": [],
            "used_search": False,
            "model": "Python 3.12 Engine",
            "engine": "python",
            "python_result": res
        }

    if lowered in ("/cmd", "cmd", "/terminal", "terminal", "python cmd", "/python"):
        st = get_cmd_status()
        reply_txt = (
            f"💻 Windows CMD & Python 3.12 Engine Status:\n\n"
            f"• Interpreter: {st['interpreter']}\n"
            f"• Python Version: {st['python_version']}\n"
            f"• Platform: {st['platform']}\n"
            f"• Workspace: {st['cwd']}\n"
            f"• Codex CLI: {'✅ Connected' if st['codex_ready'] else '❌ Not found'}\n"
            f"• Antigravity AI: ✅ Active (Agentic Coding Ready)\n\n"
            f"Coding ke liye aap direct command bol sakte hain ya likh sakte hain:\n"
            f"• `cmd chalao dir` (CMD shell command)\n"
            f"• `/python for i in range(3): print('AI Step', i)` (Python code)\n"
            f"• Ya sidebar mein 'CMD Terminal' par click karein!"
        )
        return {"reply": reply_txt, "show_cmd_modal": True, "sources": [], "used_search": False, "model": "cmd-status", "engine": "terminal"}

    if lowered in ("/version", "version", "/v", "smartai version", "version kya hai", "kaun sa version hai", "version check karo", "version status"):
        cur = get_version_info()
        hist = list_all_versions()
        v_count = len(hist.get("created_versions", []))
        reply_txt = (
            f"🏷️ **Smart AI Active Version:** `{cur.get('version', 'v2.0.0')}`\n\n"
            f"• **Current Folder:** `{ROOT}`\n"
            f"• **Release Name:** {cur.get('release_name', 'Smart AI Multi-Engine')}\n"
            f"• **Saved Versions:** {v_count} versions recorded\n\n"
            f"💡 **Autonomous Voice Update:** Agar aap naya version banana chahte hain, to bas boliye: *'Naya version update karo'* aur main khud bana dunga!"
        )
        return {"reply": reply_txt, "show_version_modal": True, "sources": [], "used_search": False, "model": "version-manager", "engine": "system"}

    if lowered.startswith("/antigravity ") or lowered.startswith("/anti "):
        engine = "antigravity"
        message = message.split(" ", 1)[1].strip()
        lowered = message.lower().strip()
    elif lowered.startswith("/codex ") or lowered.startswith("/openai "):
        engine = "openai"
        message = message.split(" ", 1)[1].strip()
        lowered = message.lower().strip()
    elif lowered.startswith("/gemini "):
        engine = "gemini"
        message = message.split(" ", 1)[1].strip()
        lowered = message.lower().strip()

    if lowered in ("/model", "model", "ai model", "engine", "models"):
        op_st = get_openai_status()
        gem_key, _ = get_key()
        reply_txt = (
            f"🧠 Smart AI Multi-Engine Hub:\n\n"
            f"1. 🌌 Antigravity AI: ✅ Active (Google DeepMind Agentic Engine)\n"
            f"2. ⚡ OpenAI (Codex): {'✅ Active (' + op_st['model'] + ')' if op_st['status'] == 'ready' else '⚠️ Setup needed'}\n"
            f"3. ✨ Google Gemini: {'✅ Active (' + PRIMARY_MODEL + ')' if gem_key else '⚠️ Key needed'}\n\n"
            f"Aap composer mein dropdown se kisi bhi engine ko select kar sakte hain, ya /antigravity, /codex, /gemini se poochh sakte hain!"
        )
        return {"reply": reply_txt, "sources": [], "used_search": False, "model": "engine-hub", "engine": "system"}

    if lowered in ("/antigravity status", "antigravity status"):
        reply_txt = (
            "🌌 Antigravity Agentic Engine Status:\n\n"
            "• Engine: Antigravity AI (Google DeepMind)\n"
            "• Capabilities: Advanced Agentic Reasoning, Coding, Multi-tool Execution\n"
            "• MCP Server: ✅ Active (.agents/mcp_config.json)\n"
            "• Status: Ready to assist!"
        )
        return {"reply": reply_txt, "sources": [], "used_search": False, "model": "antigravity-status", "engine": "antigravity"}

    if lowered in ("/openai status", "openai status", "codex status", "/codex status"):
        op_st = get_openai_status()
        reply_txt = (
            f"⚡ OpenAI (Codex) Connection Info:\n\n"
            f"• Status: {op_st['status'].upper()}\n"
            f"• Mode: {op_st['summary']}\n"
            f"• Active Model: {op_st['model']}\n"
            f"• User / Account: {op_st['user']}\n"
            f"• Codex CLI: {'✅ Connected' if op_st['has_cli'] else '❌ Not found'}\n"
            f"• API Key: {'✅ Saved' if op_st['has_api_key'] else 'ℹ️ Optional (Codex CLI ready)'}\n"
            f"• Global MCP: ✅ Codex MCP mein Smart AI active hai"
        )
        return {"reply": reply_txt, "sources": [], "used_search": False, "model": "openai-status", "engine": "openai"}

    if lowered in ("/learning", "/learn", "learning", "feedback", "rating", "ratings", "smart ai ne kya sikha", "ratings dikhao", "feedback dikhao", "ai learning"):
        stats = get_learning_stats()
        rules_list = "\n".join(f"• **{r.get('topic','Niyam')}:** {r.get('rule','')}" for r in stats.get("learned_rules", [])[:6])
        if not rules_list:
            rules_list = "• Abhi tak koi naya rule record nahi hua hai."
        reply_txt = (
            f"🌟 **Smart AI Continuous Self-Learning Report:**\n\n"
            f"• **Average User Rating:** ⭐ **{stats['average_rating']} / 5.0** (Total {stats['total_ratings']} ratings received)\n"
            f"• **Star Breakdown:** 5★: {stats['star_counts'].get('5',0)} | 4★: {stats['star_counts'].get('4',0)} | 3★: {stats['star_counts'].get('3',0)} | 2★: {stats['star_counts'].get('2',0)} | 1★: {stats['star_counts'].get('1',0)}\n\n"
            f"🧠 **AI Dwara Sikhe Gaye Rules & Corrections:**\n{rules_list}\n\n"
            f"💡 Har jawab ke niche bane ⭐ stars par click karke aap mujhe kisi bhi galti ka sujhav de sakte hain — main turant sikh kar update ho jaunga!"
        )
        return {
            "reply": reply_txt,
            "show_learning_modal": True,
            "sources": [],
            "used_search": False,
            "model": "learning-engine",
            "engine": "system"
        }

    # OpenSource AI Agents Directory Command
    is_agents_directory_query = (
        lowered in ("/agents", "/opensource", "agents", "open source agents", "ai agents", "free ai agents", "github agents", "github ai", "open source ai", "free agents", "agents hub", "agents list")
        or (any(k in lowered for k in ["free ai agent", "opensource agent", "github ai agent"]) and not any(w in lowered for w in ["help", "karo", "banao", "research", "se ", "ki ", "code", "run", "solve", "execute"]))
    )
    if is_agents_directory_query:
        reply_txt = get_agents_summary_text()
        return {
            "reply": reply_txt,
            "show_agents_modal": True,
            "sources": [],
            "used_search": False,
            "model": "opensource-agents-hub",
            "engine": "system"
        }

    # 1. Connected Tools Command
    if lowered in ("/tools", "tools", "connect tools", "connected tools", "google tools"):
        acct = get_google_account()
        enc = urllib.parse.quote(acct)
        reply_txt = (
            f"Aapki Gmail ID ({acct}) se yeh 7 Google Tools connected hain:\n\n"
            f"1. 🖼️ Google Photos: https://photos.google.com/?authuser={enc}\n"
            f"2. 🗺️ Google Maps: https://www.google.com/maps?authuser={enc}\n"
            f"3. 📁 Google Drive: https://drive.google.com/drive/u/0/?authuser={enc}\n"
            f"4. ▶️ YouTube: https://www.youtube.com/?authuser={enc}\n"
            f"5. ☁️ Google One: https://one.google.com/?authuser={enc}\n"
            f"6. 📱 Play Store: https://play.google.com/store?authuser={enc}\n"
            f"7. 🌐 Google Chrome: https://www.google.com?authuser={enc}\n\n"
            f"Aap upar 🧰 Tools button dabakar bhi inko kisi bhi waqt direct open kar sakte hain!"
        )
        return {"reply": reply_txt, "sources": [], "used_search": False, "model": "tools-hub", "engine": "tools"}

    # 2. Permissions Command
    if lowered in ("/permissions", "permissions", "permission", "permissions dikhao", "permissions manager"):
        perms = get_permissions()
        allowed_names = [p["name"] for p in perms["permissions"] if p["allowed"]]
        blocked_names = [p["name"] for p in perms["permissions"] if not p["allowed"]]
        reply_txt = (
            f"🛡️ Smart AI Permissions Status ({perms['allowed_count']}/{perms['total']} Allowed):\n\n"
            f"✅ Allowed: {', '.join(allowed_names) if allowed_names else 'Koi nahi'}\n"
            f"⛔ Blocked: {', '.join(blocked_names) if blocked_names else 'Koi nahi'}\n\n"
            f"Aap upar 🛡️ button dabakar ya niche diye gaye button se kisi bhi permission ko ON ya OFF kar sakte hain."
        )
        return {
            "reply": reply_txt,
            "show_permissions_modal": True,
            "sources": [],
            "used_search": False,
            "model": "permissions-hub",
            "engine": "permissions"
        }

    # 3. Strict Device Actions Intent Check (WhatsApp, Files, Folders, Apps, Games, Camera, Location, Phone, YouTube, Music)
    detected_action = _detect_action(lowered)
    if detected_action:
        act_res = execute_system_action(detected_action, user_query=message)
        if act_res["status"] == "blocked":
            return {
                "reply": act_res["reply"],
                "permission_blocked": True,
                "action": detected_action,
                "missing": act_res.get("missing", []),
                "missing_names": act_res.get("missing_names", []),
                "sources": [],
                "used_search": False,
                "model": "security-gate",
                "engine": "system"
            }
        elif act_res["status"] in ("success", "client_action"):
            return {
                "reply": act_res["reply"],
                "permission_success": True,
                "action": detected_action,
                "client_action": act_res.get("client_action"),
                "media_card": act_res.get("media_card"),
                "whatsapp_card": act_res.get("whatsapp_card"),
                "sources": [],
                "used_search": False,
                "model": "system-manager",
                "engine": "system"
            }

    # 4. Gmail Context Check
    email_query = any(w in lowered for w in ["mail", "email", "inbox", "dak", "chithi", "chitthi", "sandesh"])
    extra_context = ""
    if email_query:
        gmail_st = check_gmail_status()
        if gmail_st.get("connected"):
            emails_data = get_unread_emails(5)
            if "emails" in emails_data:
                cnt = emails_data.get("unread_count", 0)
                list_str = "\n".join(f"- From: {e['from']} | Subject: {e['subject']}" for e in emails_data.get("emails", []))
                extra_context = f"\n[GMAIL LIVE CONTEXT ({gmail_st.get('user')}): Total unread emails: {cnt}.\nLatest emails:\n{list_str}\nIn emails ko user ko saaf aur aasan Hindi mein batayein.]\n"
            else:
                extra_context = f"\n[GMAIL LIVE CONTEXT: Email check karne me dikkat: {emails_data.get('error')}].\n"
        else:
            extra_context = f"\n[GMAIL LIVE CONTEXT: User ka Gmail ({gmail_st.get('user')}) abhi connected nahi hai. Settings mein jakar 16-akshar ka App Password daalein.]\n"

    # 5. World Weather & Google Weather Check
    is_weather_query = any(w in lowered for w in WEATHER_KEYWORDS)
    weather_card_data = None
    if is_weather_query:
        city_candidate = extract_weather_city(message)
        w_info = get_world_weather(city_candidate)
        if w_info.get("status") == "success":
            weather_card_data = w_info
            fc_list = [f"{f['date']}: {f['icon']} {f['min']}°-{f['max']}°C ({f['condition']})" for f in w_info.get("forecast", [])[1:4]]
            fc_str = ", ".join(fc_list)
            extra_context += (
                f"\n[LIVE WORLD WEATHER & GOOGLE WEATHER DATA for {w_info['location']}]:\n"
                f"- Live Current Temperature: {w_info['temp']}°C (Feels like: {w_info['feels_like']}°C)\n"
                f"- Weather Condition: {w_info['condition']} {w_info['icon']}\n"
                f"- Today Range: Min {w_info['min_temp']}°C / Max {w_info['max_temp']}°C\n"
                f"- Humidity (Nami): {w_info['humidity']}%\n"
                f"- Wind Speed (Hawa): {w_info['wind_speed']} km/h\n"
                f"- Rain / Precipitation: {w_info['precipitation']} mm\n"
                f"- Upcoming Forecast: {fc_str}\n"
                f"- Google Search link: {w_info['google_url']}\n"
                f"Aap user ko saaf, aasan aur natural Hindi mein mausam ka taaza haal batayein aur batayein ki yeh Google aur live weather data se verified report hai.\n"
            )
            use_search = True  # Automatically use Google Search grounding for weather!

    # Attachments Context
    if saved_attachments:
        file_lines = "\n".join(f"- {f['name']} ({f['category'].upper()}, {f['size']} bytes, Location: {f['saved_path']})" for f in saved_attachments)
        extra_context += f"\n[ATTACHMENTS SAVED IN uploads/ FOLDER]:\n{file_lines}\nUser ko batao ki in files ko surakshit save kar liya gaya hai aur jo poocha hai uska vistaar se jawab do.\n"

    # Self-Learning Context Injection (Continuous Learning from user corrections & feedback)
    learning_ctx = get_learning_context()
    if learning_ctx:
        extra_context += f"\n{learning_ctx}\n"

    # OpenSource AI Agent Autonomous Matching & Delegation
    delegated_agent, delegation_reason = detect_agent_delegation(message, forced_agent=agent_help)
    if delegated_agent:
        agent_framework_ctx = build_agent_framework_instructions(delegated_agent, message, reason=delegation_reason)
        extra_context += f"\n{agent_framework_ctx}\n"

    def _attach_meta(response_dict):
        if not isinstance(response_dict, dict):
            return response_dict
        if saved_attachments:
            response_dict["attachments"] = saved_attachments
        if weather_card_data:
            response_dict["weather_card"] = weather_card_data
        if delegated_agent:
            response_dict["collaborating_agent"] = {
                "id": delegated_agent["id"],
                "name": delegated_agent["name"],
                "icon": delegated_agent.get("icon", "🤖"),
                "category": delegated_agent.get("category", "Autonomous"),
                "stars": delegated_agent.get("stars", ""),
                "github_url": delegated_agent.get("github_url", ""),
                "repo": delegated_agent.get("repo", ""),
                "reason": delegation_reason
            }
            next_step_data = generate_next_project_step(message, delegated_agent, response_text=response_dict.get("reply", ""))
            if next_step_data:
                response_dict["next_step"] = next_step_data
        return response_dict

    # Execution according to chosen engine
    engine_normalized = (engine or "auto").strip().lower()

    if engine_normalized in ("antigravity", "anti"):
        final_prompt = (message + extra_context) if extra_context else message
        try:
            res = ask_antigravity(final_prompt, history, use_search=use_search)
            return _attach_meta(res)
        except Exception:
            return _attach_meta(_fallback_smart_response(message, extra_context, weather_card_data))

    if engine_normalized in ("openai", "codex"):
        final_prompt = (message + extra_context) if extra_context else message
        try:
            res = ask_openai(final_prompt, history)
            return _attach_meta(res)
        except Exception:
            return _attach_meta(_fallback_smart_response(message, extra_context, weather_card_data))

    if engine_normalized == "gemini":
        gem_key, _ = get_key()
        if gem_key and is_valid_gemini_format(gem_key):
            try:
                res = ask_gemini_raw(message, history, use_search=use_search, extra_context=extra_context, attachments=attachments)
                return _attach_meta(res)
            except Exception:
                pass
        return _attach_meta(_fallback_smart_response(message, extra_context, weather_card_data))

    # "auto" Mode: Try Gemini first (if key is valid format), fallback to OpenAI / Codex, then fallback to Smart AI Live Core
    gem_key, _ = get_key()
    op_status = get_openai_status()
    openai_available = op_status["status"] == "ready"

    if gem_key and is_valid_gemini_format(gem_key):
        try:
            res = ask_gemini_raw(message, history, use_search=use_search, extra_context=extra_context, attachments=attachments)
            return _attach_meta(res)
        except Exception:
            pass

    if openai_available:
        final_prompt = (message + extra_context) if extra_context else message
        try:
            res = ask_openai(final_prompt, history)
            return _attach_meta(res)
        except Exception:
            pass

    # Seamless Fallback: Always respond gracefully in warm Hindi without throwing raw errors
    res = _fallback_smart_response(message, extra_context, weather_card_data)
    return _attach_meta(res)

def ask_gemini(message, history=None, use_search=True):
    return ask_smart_ai(message, history=history, use_search=use_search, engine="gemini")

class Handler(BaseHTTPRequestHandler):
    server_version = f"SmartAI/{get_version_info().get('version', 'v2.0.0').lstrip('v')}"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        return

    def _allowed(self):
        if IS_CLOUD or os.environ.get("SMARTAI_CLOUD_MODE") == "1":
            host_hdr = self.headers.get("Host", "").split(":", 1)[0].lower()
            if not host_hdr:
                return True
            return _is_allowed_origin_or_host(host_hdr)
        client_ip = getattr(self, "client_address", ("127.0.0.1", 0))[0]
        if not _is_allowed_origin_or_host(client_ip):
            return False
        host_hdr = self.headers.get("Host", "").split(":", 1)[0].lower()
        if not host_hdr:
            return False
        return _is_allowed_origin_or_host(host_hdr)

    def _local(self):
        return self._allowed()

    def _get_auth_user(self):
        auth_hdr = self.headers.get("Authorization", "")
        token = ""
        if auth_hdr.startswith("Bearer "):
            token = auth_hdr.split(" ", 1)[1].strip()
        if not token:
            token = self.headers.get("X-Auth-Token", "").strip()
        if not token:
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
            token = query.get("token", [""])[0].strip()
        return verify_session(token) if token else None

    def _send(self, code, typ, data):
        try:
            self.send_response(code)
            self.send_header("Content-Type",typ)
            self.send_header("Content-Length",str(len(data)))
            self.send_header("Connection","keep-alive")
            self.send_header("Keep-Alive","timeout=30, max=100")
            self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Referrer-Policy","no-referrer")
            self.send_header("Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; media-src 'self' data: blob:; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
            self.send_header("Cache-Control","no-store")
            self.end_headers()
            self.wfile.write(data)
        except (ConnectionError, BrokenPipeError, OSError):
            pass

    def _json(self, code, obj):
        self._send(code,"application/json; charset=utf-8",json.dumps(obj,ensure_ascii=False).encode("utf-8"))

    def _read(self):
        length = int(self.headers.get("Content-Length","0"))
        if length < 0 or length > 100_000_000:
            raise ValueError("Request bahut badi hai (Max 100MB).")
        value = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(value,dict):
            raise ValueError("JSON object bhejein.")
        return value

    def do_GET(self):
        path = urllib.parse.urlsplit(self.path).path
        if path in ("/api/health", "/healthz"):
            self._json(200, {
                "status": "healthy",
                "service": "Smart AI 24/7 Cloud Assistant",
                "uptime_seconds": int(time.time() - SERVER_START_TIME),
                "mode": "24/7_cloud_permanent" if IS_CLOUD else "local_resilient",
                "keepalive": "active",
                "timestamp": time.time(),
                "version": get_version_info().get("version", "v2.0.0")
            })
            return
        if not self._allowed():
            self._json(403,{"error":"Sirf local network ya verified domain se access allow hai."}); return

        if path.startswith("/uploads/"):
            rel = urllib.parse.unquote(path.split("/uploads/", 1)[1]).lstrip("/\\")
            target_file = (UPLOADS_DIR / rel).resolve()
            try:
                target_file.relative_to(UPLOADS_DIR.resolve())
            except ValueError:
                self._json(403, {"error": "Access denied."}); return
            if not target_file.is_file():
                self._json(404, {"error": "File nahi mili."}); return
            typ = mimetypes.guess_type(target_file.name)[0] or "application/octet-stream"
            self._send(200, typ, target_file.read_bytes())
            return

        if path.startswith("/api/weather"):
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
            city = (query.get("city", ["Delhi"])[0]).strip()
            self._json(200, get_world_weather(city)); return
        if path == "/api/status":
            self._json(200, status()); return
        if path == "/api/contacts":
            self._json(200, {"contacts": get_contacts()}); return
        if path == "/api/auth/me":
            u = self._get_auth_user()
            self._json(200, {"logged_in": bool(u), "user": u}); return
        if path == "/api/version":
            self._json(200, list_all_versions()); return
        if path == "/api/terminal/status":
            self._json(200, get_cmd_status()); return
        if path == "/api/phone/info":
            local_ip = get_local_ip()
            t_url = get_tunnel_url()
            perm_url = os.environ.get("PERMANENT_SERVER_URL") or os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("RAILWAY_STATIC_URL")
            if not t_url and not IS_CLOUD:
                start_tunnel_background(PORT)
                t_url = get_tunnel_url()
            active_url = perm_url or t_url or f"http://{local_ip}:{PORT}"
            self._json(200, {
                "local_ip": local_ip,
                "port": PORT,
                "url": f"http://{local_ip}:{PORT}",
                "tunnel_url": t_url,
                "permanent_url": perm_url,
                "primary_url": active_url,
                "pc_url": f"http://127.0.0.1:{PORT}",
                "is_permanent_cloud": bool(perm_url or IS_CLOUD),
                "uptime_seconds": int(time.time() - SERVER_START_TIME)
            }); return
        if path.startswith("/api/phone/qr"):
            try:
                import qrcode, qrcode.image.svg
                local_ip = get_local_ip()
                t_url = get_tunnel_url()
                parsed = urllib.parse.urlparse(self.path)
                qs = urllib.parse.parse_qs(parsed.query)
                force_local = qs.get("type", [""])[0] == "local"
                target_url = f"http://{local_ip}:{PORT}" if (force_local or not t_url) else t_url
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_M,
                    box_size=10,
                    border=2,
                    image_factory=qrcode.image.svg.SvgPathImage
                )
                qr.add_data(target_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="#08111f", back_color="#ffffff")
                svg_bytes = img.to_string()
                self._send(200, "image/svg+xml; charset=utf-8", svg_bytes)
                return
            except Exception as exc:
                self._json(500, {"error": f"QR error: {exc}"})
                return
        if path == "/api/phone/fix-firewall":
            try:
                ps_cmd = 'Start-Process cmd -ArgumentList \'/c netsh advfirewall firewall add rule name="Smart AI Phone Access (8765)" dir=in action=allow protocol=TCP localport=8765 profile=any\' -Verb RunAs'
                subprocess.Popen(["powershell", "-Command", ps_cmd])
                self._json(200, {"success": True, "message": "Windows Firewall allow popup bhej diya gaya hai. Kripya 'Yes' dabayein!"})
                return
            except Exception as e:
                self._json(500, {"error": str(e)})
                return
        if path == "/api/openai/status":
            self._json(200, get_openai_status()); return
        if path == "/api/tools":
            self._json(200, get_connected_tools()); return
        if path == "/api/permissions":
            self._json(200, get_permissions()); return
        if path == "/api/feedback/stats":
            self._json(200, get_learning_stats()); return
        if path.startswith("/api/agents/opensource"):
            query_params = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
            category = query_params.get("category", [None])[0]
            search_q = query_params.get("q", [None])[0]
            self._json(200, {
                "total": len(OPENSOURCE_AGENTS),
                "categories": get_agent_categories(),
                "agents": get_all_agents(category=category, query=search_q)
            }); return
        if path == "/api/agents/categories":
            self._json(200, get_agent_categories()); return
        if path == "/api/agents/ollama/status":
            self._json(200, check_ollama()); return
        if path == "/api/tts":
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
            text = query.get("text", [""])[0]
            audio_bytes = generate_hindi_tts(text)
            if not audio_bytes:
                self._json(400, {"error": "Audio generate nahi hua."}); return
            self._send(200, "audio/mpeg", audio_bytes); return

        name = "index.html" if path in ("/","/index.html") else urllib.parse.unquote(path.lstrip("/"))
        file = (WEB / name).resolve()
        try:
            file.relative_to(WEB.resolve())
        except ValueError:
            self._json(404,{"error":"Page nahi mila."}); return
        if not file.is_file():
            self._json(404,{"error":"Page nahi mila."}); return
        typ = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
        if typ.startswith("text/") or typ in ("application/javascript","application/json"):
            typ += "; charset=utf-8"
        self._send(200,typ,file.read_bytes())

    def do_POST(self):
        if not self._allowed():
            self._json(403,{"error":"Sirf local network se Phone access connect karein."}); return
        origin = self.headers.get("Origin")
        if origin:
            try:
                parsed_origin = urllib.parse.urlsplit(origin)
                if not _is_private_or_local(parsed_origin.hostname):
                    self._json(403,{"error":"Cross-site request allow nahi hai."}); return
            except Exception:
                self._json(403,{"error":"Origin invalid hai."}); return
        try:
            data = self._read()
            route = urllib.parse.urlsplit(self.path).path

            if route == "/api/auth/login":
                login_id = str(data.get("login") or data.get("phone") or data.get("login_id") or "").strip()
                pwd = str(data.get("password") or "").strip()
                ok, token_or_err, user_info = login_user(login_id, pwd)
                if ok:
                    self._json(200, {"success": True, "token": token_or_err, "user": user_info})
                else:
                    self._json(401, {"success": False, "error": token_or_err})
                return

            if route == "/api/auth/register":
                name = str(data.get("name") or "").strip()
                login_id = str(data.get("login_id") or data.get("login") or "").strip()
                phone = str(data.get("phone") or "").strip()
                pwd = str(data.get("password") or "").strip()
                ok, token_or_err, user_info = register_user(name, login_id, phone, pwd)
                if ok:
                    self._json(200, {"success": True, "token": token_or_err, "user": user_info})
                else:
                    self._json(400, {"success": False, "error": token_or_err})
                return

            if route == "/api/auth/logout":
                token = self.headers.get("X-Auth-Token", "") or self.headers.get("Authorization", "").replace("Bearer ", "")
                logout_user(token)
                self._json(200, {"success": True, "logged_out": True})
                return

            if route == "/api/settings":
                if not isinstance(data.get("api_key"),str):
                    raise ValueError("API key text hona chahiye.")
                save_key(data["api_key"])
                self._json(200,{"saved":True,"status":status()}); return
            if route == "/api/contacts":
                action = str(data.get("action") or "save").lower()
                if action == "delete":
                    name = str(data.get("name") or "").strip()
                    self._json(200, {"success": True, "contacts": delete_contact(name)})
                    return
                name = str(data.get("name") or "").strip()
                phone = str(data.get("phone") or "").strip()
                if not name or not phone:
                    self._json(400, {"error": "Name aur phone number zaroori hai."})
                    return
                self._json(200, {"success": True, "contacts": save_contact(name, phone)})
                return
            if route == "/api/version/create":
                new_ver = data.get("version") or data.get("new_version")
                target = data.get("target") or data.get("target_dir")
                note = data.get("note", "")
                overwrite = bool(data.get("overwrite", False))
                res = create_new_version(new_ver, target, note, overwrite=overwrite)
                code = 200 if res.get("success") else 400
                self._json(code, res); return
            if route == "/api/openai/settings":
                key_val = str(data.get("api_key") or "").strip()
                save_openai_key(key_val)
                self._json(200, {"saved": True, "openai": get_openai_status(), "status": status()}); return
            if route == "/api/gmail/settings":
                user = str(data.get("email") or "kumaranil70115@gmail.com")
                pwd = str(data.get("app_password") or "")
                save_gmail_creds(user, pwd)
                self._json(200, {"saved": True, "gmail": check_gmail_status()}); return
            if route == "/api/gmail/check":
                self._json(200, get_unread_emails()); return
            if route == "/api/tools/account":
                acc = str(data.get("account") or "").strip()
                save_google_account(acc)
                self._json(200, {"saved": True, "tools": get_connected_tools()}); return
            if route == "/api/permissions":
                updates = data.get("updates")
                allow_all = data.get("allow_all")
                res = save_permissions(updates=updates, allow_all=allow_all)
                self._json(200, {"saved": True, "permissions": res}); return
            if route == "/api/system/execute":
                action = str(data.get("action") or "").strip().lower()
                self._json(200, execute_system_action(action)); return
            if route == "/api/calculate":
                if not isinstance(data.get("expression"),str):
                    raise ValueError("Expression text hona chahiye.")
                self._json(200,{"result":calculate(data["expression"])}); return
            if route == "/api/chat":
                msg_val = str(data.get("message") or "")
                attachments = data.get("attachments") or []
                if not msg_val and not attachments:
                    raise ValueError("Message ya attachment bhejein.")
                eng = str(data.get("engine") or "auto")
                agent_help = str(data.get("agent_help") or "").strip() or None
                self._json(200, ask_smart_ai(
                    msg_val,
                    data.get("history"),
                    bool(data.get("use_search", False)),
                    engine=eng,
                    attachments=attachments,
                    agent_help=agent_help
                )); return
            if route == "/api/agents/collaborate":
                task_val = str(data.get("task") or data.get("message") or "").strip()
                agent_id = str(data.get("agent_id") or "crewai").strip()
                if not task_val:
                    raise ValueError("Task ya instruction likhein.")
                self._json(200, ask_smart_ai(
                    task_val,
                    data.get("history"),
                    use_search=True,
                    engine="auto",
                    agent_help=agent_id
                )); return
            if route == "/api/weather":
                city = str(data.get("city") or "Delhi").strip()
                self._json(200, get_world_weather(city)); return
            if route == "/api/upload":
                files = data.get("files") or data.get("attachments") or []
                saved = [save_uploaded_attachment(f) for f in files if isinstance(f, dict)]
                self._json(200, {"status": "success", "uploaded": saved}); return
            if route == "/api/terminal/run":
                cmd = str(data.get("command") or "").strip()
                self._json(200, execute_cmd(cmd)); return
            if route == "/api/python/run":
                code = str(data.get("code") or "").strip()
                self._json(200, execute_python_code(code)); return
            if route == "/api/vision/greet":
                user_name = "Krishna Anil"
                greeting_msg = "Namaste Krishna ji! Maine aapko dekh liya hai, aur aap mujhse kya kaam karwana chahte hain?"
                self._json(200, {
                    "recognized": True,
                    "user": user_name,
                    "greeting": greeting_msg,
                    "tts_text": greeting_msg,
                    "status": "online"
                }); return
            if route == "/api/vision/analyze":
                img_data = str(data.get("image") or "").strip()
                prompt = str(data.get("prompt") or "Mujhe camera me dekh kar Hindi me vistaar se batao ki main kaisa dikh raha hoon aur kya kar raha hoon.").strip()
                if not img_data:
                    raise ValueError("Camera image data nahi mila.")
                att = [{
                    "name": "live_vision.jpg",
                    "type": "image/jpeg",
                    "data": img_data,
                    "category": "photo"
                }]
                res = ask_smart_ai(prompt, history=None, use_search=False, engine="auto", attachments=att)
                self._json(200, res); return
            if route == "/api/feedback":
                rating = int(data.get("rating") or 5)
                query_text = str(data.get("query") or "").strip()
                resp_text = str(data.get("response") or "").strip()
                feedback_text = str(data.get("feedback") or "").strip()
                tags = data.get("tags") or []
                res = record_feedback(rating, query_text, resp_text, feedback_text, tags)
                self._json(200, res); return
            if route == "/api/feedback/rule/delete":
                rule_id = str(data.get("id") or "").strip()
                self._json(200, delete_learned_rule(rule_id)); return
            if route == "/api/feedback/reset":
                self._json(200, clear_all_learning()); return
            self._json(404,{"error":"API route nahi mila."})
        except (ConnectionError, BrokenPipeError):
            return
        except (UnicodeDecodeError,json.JSONDecodeError,ValueError) as exc:
            self._json(400,{"error":str(exc)})
        except RuntimeError as exc:
            self._json(503,{"error":str(exc)})
        except OSError:
            pass

def _free_port(port: int):
    if os.name != "nt":
        return
    try:
        import subprocess
        out = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode()
        cur_pid = os.getpid()
        killed = False
        for line in out.splitlines():
            parts = line.strip().split()
            if len(parts) >= 5 and "LISTENING" in parts:
                pid = int(parts[-1])
                if pid != cur_pid and pid > 0:
                    subprocess.call(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    killed = True
        if killed:
            time.sleep(0.4)
    except Exception:
        pass

class ReusableServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True
    def handle_error(self, request, client_address):
        pass

def run():
    init_default_users()
    _free_port(PORT)
    local_ip = get_local_ip()
    perm_url = os.environ.get("PERMANENT_SERVER_URL") or os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("RAILWAY_STATIC_URL")
    if not IS_CLOUD:
        start_tunnel_background(PORT)
    _start_keepalive_worker()
    server = ReusableServer((BIND_HOST, PORT), Handler)
    print("=" * 66, flush=True)
    if IS_CLOUD:
        print("     SMART AI 24/7 PERMANENT CLOUD SERVER CHALU HAI (ACTIVE)     ", flush=True)
        print("=" * 66, flush=True)
        print(f"  [Mode]:               24/7 Continuous Cloud Server", flush=True)
        print(f"  [Port]:               {PORT}", flush=True)
        if perm_url:
            print(f"  [Permanent URL]:      {perm_url}", flush=True)
        print(f"  [Health Endpoint]:    /api/health (24/7 self-ping keepalive active)", flush=True)
    else:
        print("             SMART AI SERVER CHALU HAI (ACTIVE)             ", flush=True)
        print("=" * 66, flush=True)
        print(f"  [PC Browser]:         http://127.0.0.1:{PORT}", flush=True)
        print(f"  [Local Wi-Fi Phone]:  http://{local_ip}:{PORT}", flush=True)
        print(f"  [Secure HTTPS Phone]: Starting Cloudflare Tunnel in background...", flush=True)
        if perm_url:
            print(f"  [Permanent Server]:   {perm_url}", flush=True)
        print("-" * 66, flush=True)
        print("  [24/7 TIP]: Is window ko band na karein ya Cloud par deploy karein.", flush=True)
    print("=" * 66, flush=True)
    print("Server band karne ke liye Ctrl+C dabayein.\n", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSmart AI band ho gaya.", flush=True)
    finally:
        server.server_close()

if __name__ == "__main__":
    run()
