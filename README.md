# Smart AI Assistant

Local Hindi-first assistant with a browser chat, microphone input, spoken replies, Dual AI Engine (Google Gemini + OpenAI Codex), Google Search grounding, a restricted Python calculator, and an Antigravity/Codex MCP server.

## Start it

1. Install Python 3.10 or newer.
2. Double-click start.bat.
3. Use the browser tab at http://127.0.0.1:8765.
4. Allow microphone access in Chrome or Edge.

The web server binds to 127.0.0.1, so it is available only on this computer by default.

## AI Connections (Dual Engine)

### 1. OpenAI (Codex)
Smart AI connects directly to your local **OpenAI Codex CLI** installation (`~/.codex`) and active account (`kumaranil70115@gmail.com`).
- **Codex CLI Engine**: Built-in non-interactive execution with your existing logged-in account (no separate paid API key required).
- **OpenAI API Key**: Optionally save `OPENAI_API_KEY` in `.env` or via Settings (⚙️) for direct API completions (`gpt-4o`, `gpt-4o-mini`).
- **Model Switcher**: Switch between **🔄 Auto Dual**, **✨ Gemini 3.8**, and **⚡ OpenAI Codex** directly from the chat composer, or type `/codex <sawaal>` in chat.

### 2. Google Gemini
The app checks `GEMINI_API_KEY` or `GOOGLE_API_KEY` from `.env`, environment, or `~/.codex/google_key.txt`.
- In **Auto Dual** mode, Gemini 3.8 Flash answers with live Google Search grounding. If Gemini hits quota limits or network errors, it seamlessly falls back to OpenAI Codex.

## Python

Type `/calc 12 * (5 + 2)` to use the local Python calculator. It accepts numbers, brackets, and arithmetic operators only. It does not execute arbitrary Python scripts. For programming requests, the assistant can write code in the chat.

## Antigravity & OpenAI Codex MCP

- **Antigravity MCP**: `.agents/mcp_config.json`
- **Codex MCP**: Smart AI is registered in `~/.codex/config.toml` as `smart-ai`.
- Available MCP tools: `ask_smart_ai`, `ask_openai`, `python_calculate`, `smart_ai_server_status`, and `smart_ai_connections`.

## Version Control & Release Manager (New Version in New Folder)

Smart AI me Versioning aur safe Folder snapshot system shamil hai:
- **Current Version:** `v2.0.0` (Stated in `version.json`)
- **Jab bhi update karna ho:** Naya version banakar naya folder banaya ja sakta hai, jisse purani files safe rahengi aur naye folder me sabhi files identical copy hokar update ho jayengi.

### Naya Version Banane ke 3 Tareeqe:
1. **1-Click Batch File (Sabse aasan):**
   - SmartAI folder me `create_new_version.bat` par double-click karein.
   - Naya version (jaise `v2.1.0` ya `v3.0.0`) enter karein.
   - Naya folder jaise `C:\Users\DELL\SmartAI_v2.1.0` ban jayega.
2. **Web UI se:**
   - Topbar me 🏷️ icon par click karein ya Sidebar me "Smart AI Version" par click karein.
   - Naya version number likhkar **"Naya Version & Folder Banayein 🚀"** dabayein.
3. **Chat Command se:**
   - Chat me likhein: `/newversion v2.1.0` ya `/version`
