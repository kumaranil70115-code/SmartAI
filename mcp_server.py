from __future__ import annotations
import json, sys, urllib.error, urllib.request

if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
if hasattr(sys.stderr, "reconfigure"):
    try: sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

from app import ask_antigravity, ask_gemini, ask_openai, ask_smart_ai, calculate, status

VERSION = "2025-06-18"

def send(value):
    sys.stdout.write(json.dumps(value,ensure_ascii=False,separators=(",",":")) + "\n")
    sys.stdout.flush()

def result(request_id,text,error=False):
    send({"jsonrpc":"2.0","id":request_id,"result":{"content":[{"type":"text","text":text}],"isError":error}})

def call(name,args):
    if name == "ask_smart_ai":
        question = args.get("question","")
        if not isinstance(question,str) or not question.strip():
            raise ValueError("question khaali nahi ho sakta.")
        engine = args.get("engine", "auto")
        response = ask_smart_ai(question,[],bool(args.get("google_search",True)), engine=engine)
        text = response["reply"]
        for source in response.get("sources", []):
            text += "\n\nSource: " + source["title"] + " — " + source["url"]
        return text
    if name == "ask_antigravity":
        question = args.get("question","")
        if not isinstance(question,str) or not question.strip():
            raise ValueError("question khaali nahi ho sakta.")
        response = ask_antigravity(question, [])
        return response["reply"]
    if name == "ask_openai" or name == "ask_codex":
        question = args.get("question","")
        if not isinstance(question,str) or not question.strip():
            raise ValueError("question khaali nahi ho sakta.")
        response = ask_openai(question, [])
        return response["reply"]
    if name == "python_calculate":
        return calculate(args.get("expression",""))
    if name == "smart_ai_server_status":
        try:
            with urllib.request.urlopen("http://127.0.0.1:8765/api/status",timeout=2) as response:
                return response.read().decode("utf-8")
        except (urllib.error.URLError,TimeoutError):
            return '{"server":"offline"}'
    if name == "smart_ai_connections":
        return json.dumps(status(),ensure_ascii=False,indent=2)
    raise ValueError("MCP tool nahi mila.")

TOOLS = [
 {"name":"ask_smart_ai","description":"Hindi-first assistant; Antigravity, Gemini aur OpenAI Codex multi-engine support.","inputSchema":{"type":"object","properties":{"question":{"type":"string"},"google_search":{"type":"boolean"},"engine":{"type":"string","enum":["auto","antigravity","gemini","openai"]}},"required":["question"]}},
 {"name":"ask_antigravity","description":"Google Antigravity agentic AI model se Hindi/Hinglish mein seedha poochhein.","inputSchema":{"type":"object","properties":{"question":{"type":"string"}},"required":["question"]}},
 {"name":"ask_openai","description":"OpenAI (Codex) AI model se Hindi/Hinglish mein seedha sawaal poochhein.","inputSchema":{"type":"object","properties":{"question":{"type":"string"}},"required":["question"]}},
 {"name":"python_calculate","description":"Restricted Python arithmetic; arbitrary Python script nahi chalaata.","inputSchema":{"type":"object","properties":{"expression":{"type":"string"}},"required":["expression"]}},
 {"name":"smart_ai_server_status","description":"Smart AI local HTTP server ka status dekhein.","inputSchema":{"type":"object","properties":{}}},
 {"name":"smart_ai_connections","description":"Antigravity, Gemini, OpenAI Codex, Google Search aur Python readiness dekhein.","inputSchema":{"type":"object","properties":{}}}
]

def handle(msg):
    method, request_id = msg.get("method"), msg.get("id")
    if method == "notifications/initialized": return
    if method == "initialize":
        send({"jsonrpc":"2.0","id":request_id,"result":{"protocolVersion":VERSION,"capabilities":{"tools":{}},"serverInfo":{"name":"smart-ai-assistant","version":"1.0.0"}}}); return
    if method == "ping":
        send({"jsonrpc":"2.0","id":request_id,"result":{}}); return
    if method == "tools/list":
        send({"jsonrpc":"2.0","id":request_id,"result":{"tools":TOOLS}}); return
    if method == "tools/call":
        args = msg.get("params") or {}
        try: result(request_id,call(args.get("name",""),args.get("arguments") or {}))
        except Exception as exc: result(request_id,str(exc),True)
        return
    if request_id is not None:
        send({"jsonrpc":"2.0","id":request_id,"error":{"code":-32601,"message":"Method not found"}})

def main():
    for line in sys.stdin:
        try:
            value = json.loads(line)
            if isinstance(value,dict): handle(value)
        except Exception as exc:
            print("MCP request error: " + str(exc),file=sys.stderr,flush=True)

if __name__ == "__main__":
    main()

