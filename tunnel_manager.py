"""
Smart AI - Cloudflare Secure Phone Tunnel Manager
-------------------------------------------------
Automatically creates and maintains a secure, global HTTPS tunnel via cloudflared.exe
so any phone (Android/iPhone) can access Smart AI from anywhere 24/7.
"""

import subprocess
import threading
import time
import re
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLOUDFLARED_EXE = ROOT / "cloudflared.exe"

_tunnel_proc = None
_tunnel_url = None
_tunnel_lock = threading.Lock()
_tunnel_starting = False

def get_tunnel_url():
    global _tunnel_url, _tunnel_proc
    perm = os.environ.get("PERMANENT_SERVER_URL") or os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("RAILWAY_STATIC_URL")
    if perm:
        return perm if perm.startswith("http") else f"https://{perm}"
    if _tunnel_proc and _tunnel_proc.poll() is not None:
        _tunnel_url = None
    return _tunnel_url

def start_tunnel_background(port=8765):
    global _tunnel_proc, _tunnel_url, _tunnel_starting
    if _tunnel_url and _tunnel_proc and _tunnel_proc.poll() is None:
        return _tunnel_url

    if not CLOUDFLARED_EXE.exists():
        return None

    def _worker():
        global _tunnel_proc, _tunnel_url, _tunnel_starting
        with _tunnel_lock:
            if _tunnel_starting or (_tunnel_proc and _tunnel_proc.poll() is None):
                return
            _tunnel_starting = True

        try:
            cmd = [str(CLOUDFLARED_EXE), "tunnel", "--url", f"http://127.0.0.1:{port}"]
            creation_flags = 0x08000000 if os.name == "nt" else 0
            _tunnel_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                creationflags=creation_flags
            )
            while _tunnel_proc and _tunnel_proc.poll() is None:
                line = _tunnel_proc.stderr.readline()
                if not line:
                    break
                if not _tunnel_url:
                    m = re.search(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com", line)
                    if m:
                        _tunnel_url = m.group(0)
                        print(f"\n🌐 [SECURE HTTPS PHONE LINK READY]: {_tunnel_url}\n", flush=True)
        except Exception as e:
            print("Tunnel startup error:", e, flush=True)
        finally:
            _tunnel_url = None
            _tunnel_starting = False

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return None

def stop_tunnel():
    global _tunnel_proc, _tunnel_url
    if _tunnel_proc:
        try:
            _tunnel_proc.terminate()
            _tunnel_proc.wait(timeout=2)
        except Exception:
            try:
                _tunnel_proc.kill()
            except Exception:
                pass
        _tunnel_proc = None
        _tunnel_url = None
