"""
Smart AI - Autonomous OpenSource & Google AI Agent Orchestrator & Dispatcher
----------------------------------------------------------------------------
Yeh engine user ke har sawaal aur task ko khud se analyze karta hai,
aur Google DeepMind, Firebase, Microsoft aur GitHub open-source community
ke top 26 AI agents me se sabse best agent ko autonomously choose karta hai.
"""

from __future__ import annotations
import json
import urllib.request
import urllib.error
from opensource_agents import OPENSOURCE_AGENTS

AGENT_MAP = {a["id"]: a for a in OPENSOURCE_AGENTS}

def check_ollama(timeout=0.6) -> dict:
    """Checks if a local Ollama server is running at localhost:11434"""
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            models = [m.get("name") for m in data.get("models", [])]
            return {
                "online": True,
                "models": models,
                "message": f"Ollama local server active hai ({len(models)} local models ready)."
            }
    except Exception:
        return {
            "online": False,
            "models": [],
            "message": "Ollama local server offline hai (Start karne ke liye `ollama serve` chalaayein)."
        }

def is_task_or_project(message: str) -> tuple[bool, str]:
    """
    Evaluates whether the user's message is an actionable Task, Project, Coding work,
    or Multi-step Workflow that warrants delegating to a specialized Agent,
    OR if it is a direct conversation/inquiry where Multi-Engine AI directly answers.
    """
    msg = (message or "").strip()
    lowered = msg.lower()
    if not msg:
        return (False, "Empty message")

    # 1. Obvious conversational / greetings / status / personal inquiries
    conversational_exact = {
        "hi", "hello", "hey", "namaste", "namaskar", "kaise ho", "kya haal hai",
        "kaise hain", "kya chal raha", "good morning", "good evening", "good night",
        "shukriya", "dhanyawaad", "thank you", "thanks", "ok", "theek hai", "bye", "alvida",
        "kya kar rahe ho", "kya kar sakte ho", "help", "madad"
    }
    if lowered in conversational_exact:
        return (False, "Conversational greeting")

    # 1b. Personal conversational queries about Smart AI itself, voice, personality, feelings
    personal_ai_queries = [
        "tum kaun ho", "kaun ho tum", "tum kya ho", "tumhara naam", "naam kya hai",
        "tum kaise ho", "kya haal hai", "apni aawaz", "khud ki aawaz", "aawaz theek",
        "aawaz badlo", "insaan jaise", "insaan ki tarah", "tum sun rahe ho", "meri aawaz",
        "kya tum sun rahe ho", "kya tum insaan ho", "tum mere dost ho", "tumhe kisne banaya",
        "kya kar sakte ho", "meri madad karo", "baat karo", "kuch bolo", "shukriya",
        "theek kar sakte ho", "theek ho", "sab theek", "tum khud ki"
    ]
    if any(p in lowered for p in personal_ai_queries):
        return (False, "Personal conversational inquiry")

    # 2. System and Device queries handled directly by Multi-Engine
    if lowered in ("/tools", "/permissions", "/version", "/learning", "/cmd", "/calc") or lowered.startswith(("/newversion", "/calc", "/run", "/python")):
        return (False, "Built-in system action")

    # 3. Explicit Agent / Tool Mentions -> ALWAYS a Task
    explicit_agents = [
        "genkit", "astra", "gemma", "autogen", "openhands", "opendevin", "aider", "memgpt",
        "crewai", "autogpt", "open-interpreter", "interpreter", "metagpt", "chatdev",
        "swe-agent", "gpt-engineer", "ollama", "smolagents", "github agent"
    ]
    if any(k in lowered for k in explicit_agents):
        return (True, "Explicit agent keyword mentioned")

    # 4. Explicit Project / Task / Coding / Development Action Verbs
    project_action_keywords = [
        "project", "banao", "banayein", "banado", "create", "build", "develop",
        "implement", "architecture", "prd", "structure", "codebase", "full-stack", "app",
        "application", "website", "system design", "workflow", "pipeline", "script",
        "program", "api", "database", "sql", "backend", "frontend",
        "code theek karo", "bug fix", "debug error", "traceback", "exception fix",
        "deep research", "case study", "roadmap", "business plan",
        "strategy", "automate", "automation", "step 1", "step 2", "step 3", "phase 1", "phase 2", "phase 3",
        "git commit", "deploy project", "offline model run", "local model run", "kaise banayein"
    ]
    if any(k in lowered for k in project_action_keywords):
        return (True, "Project or Task keyword matched")

    # 5. Question words without task verbs -> Simple Q&A directly answered by AI
    simple_qa_starters = [
        "kya hai", "kaun hai", "kahan hai", "kab hua", "kisne banaya", "what is",
        "who is", "where is", "when did", "define", "meaning of", "matlab kya"
    ]
    if any(w in lowered for w in simple_qa_starters) and not any(k in lowered for k in ["banao", "code", "project", "fix", "research"]):
        return (False, "Simple Q&A directly answerable by AI")

    # 6. Default to direct AI answer
    return (False, "General conversational inquiry")

def generate_next_project_step(message: str, agent: dict | None, response_text: str = "") -> dict | None:
    """
    Generates the next autonomous action / step for a project or task pipeline.
    Enables continuous progression: Step 1 -> Step 2 -> Step 3 ("next fir auto start ho").
    """
    if not agent:
        return None

    lowered_msg = (message or "").lower()
    aid = agent.get("id", "")
    agent_name = agent.get("name", "Agent")

    # Determine current step from user message
    current_step = 1
    if "step 3" in lowered_msg or "phase 3" in lowered_msg:
        current_step = 3
    elif "step 2" in lowered_msg or "phase 2" in lowered_msg:
        current_step = 2

    # If already at step 3, project workflow is completed!
    if current_step >= 3:
        return {
            "completed": True,
            "title": "Project Complete",
            "message": "✅ Sabhi phases safalta se execute ho chuke hain!",
            "auto_start": False
        }

    next_step_num = current_step + 1

    # Dynamic step templates tailored to the specialized agent domain
    if aid in ("gpt-engineer", "metagpt", "chatdev"):
        if next_step_num == 2:
            title = "Phase 2: Core Business Logic & API Endpoints"
            prompt = f"Step 2: Ab is project ka core backend logic, API endpoints aur database models implement karein."
        else:
            title = "Phase 3: Frontend UI, Styling & Verification Tests"
            prompt = f"Step 3: Ab is project ka frontend user interface, responsive styles aur verification tests integrate karein."

    elif aid in ("swe-agent", "aider", "openhands"):
        if next_step_num == 2:
            title = "Phase 2: Automated Unit Tests & Edge Cases"
            prompt = f"Step 2: Ab is fix ke liye automated unit test cases aur regression testing verify karein."
        else:
            title = "Phase 3: Code Optimization & Git Commit Review"
            prompt = f"Step 3: Ab code review, performance optimization aur clean documentation finalize karein."

    elif aid in ("crewai", "autogen"):
        if next_step_num == 2:
            title = "Phase 2: Execution Roadmap & Financial / Tech Architecture"
            prompt = f"Step 2: Ab is strategy ka technical architecture, timeline roadmap aur resource planning formulate karein."
        else:
            title = "Phase 3: Go-To-Market Execution & Risk Mitigation"
            prompt = f"Step 3: Ab Go-To-Market launch checklist, risk mitigation aur KPI metrics define karein."

    elif aid in ("autogpt", "open-interpreter", "google-genkit", "google-astra"):
        if next_step_num == 2:
            title = "Phase 2: In-Depth Execution & Practical Implementation"
            prompt = f"Step 2: Ab is task ke findings ke aadhar par concrete execution aur live implementation script taiyar karein."
        else:
            title = "Phase 3: Comprehensive Summary & Production Readiness"
            prompt = f"Step 3: Ab production deployment checklist aur final executive deliverables verify karein."

    else:
        title = f"Phase {next_step_num}: Next Milestone Execution"
        prompt = f"Step {next_step_num}: Ab is project ke agle phase ko continue karein aur implementation aage badhayein."

    return {
        "completed": False,
        "title": title,
        "prompt": prompt,
        "agent_id": aid,
        "agent_name": agent_name,
        "step_number": next_step_num,
        "total_steps": 3,
        "auto_start": True,
        "delay_seconds": 3
    }

def auto_select_best_agent(message: str) -> tuple[dict | None, str]:
    """
    AUTONOMOUS AGENT SELECTION:
    Analyzes task context, intent, domain and complexity, and
    autonomously selects the single best open-source or Google AI agent with rationale.
    """
    is_task, _ = is_task_or_project(message)
    if not is_task:
        return (None, "")

    lowered = (message or "").lower().strip()

    # 1. Google Astra & Multimodal Vision/Camera/Audio Tasks
    if any(k in lowered for k in [
        "astra", "project astra", "camera dekh", "video live", "screen dekh", "multimodal",
        "live vision", "photo dekh", "tasveer dekh", "visual"
    ]):
        return (
            AGENT_MAP["google-astra"],
            "Real-time visual, audio aur multimodal understanding ke liye Google DeepMind Project Astra framework ko chuna gaya hai."
        )

    # 2. Google Genkit & Firebase Production Workflows
    if any(k in lowered for k in [
        "genkit", "firebase", "google agent", "google tool workflow", "schema validation"
    ]):
        return (
            AGENT_MAP["google-genkit"],
            "Production-grade schema validation aur Google tool integration ke liye Google Genkit open-source framework ko chuna gaya hai."
        )

    # 3. Google Gemma Open-Weights Model
    if any(k in lowered for k in [
        "gemma", "paligemma", "gemma2", "recurrentgemma"
    ]):
        return (
            AGENT_MAP["google-gemma"],
            "Google DeepMind ke open-weights fast inference ke liye Google Gemma Agent ko chuna gaya hai."
        )

    # 4. Long-Term Persistent Memory & Recall -> MemGPT
    if any(k in lowered for k in [
        "memgpt", "letta", "long term memory", "virtual memory", "hamesha yaad", "pichli baatein", "perpetual recall"
    ]):
        return (
            AGENT_MAP["memgpt"],
            "OS-style tiered virtual memory aur long-term context recall ke liye MemGPT (Letta) ko chuna gaya hai."
        )

    # 5. Git Pair Programming & Multi-file editing -> Aider
    if any(k in lowered for k in [
        "aider", "pair programmer", "git commit", "git diff edit", "pair programming", "git repo"
    ]):
        return (
            AGENT_MAP["aider"],
            "Terminal git-aware multi-file editing aur automated git commits ke liye Aider Pair Programmer ko chuna gaya hai."
        )

    # 6. Autonomous Software Engineering (Devin style) -> OpenHands (OpenDevin)
    if any(k in lowered for k in [
        "openhands", "opendevin", "devin", "autonomous engineer", "bash run"
    ]):
        return (
            AGENT_MAP["openhands"],
            "End-to-end autonomous software development aur GitHub workflow execution ke liye OpenHands (OpenDevin) ko chuna gaya hai."
        )

    # 7. Microsoft AutoGen Conversational Multi-Agent
    if any(k in lowered for k in [
        "autogen", "user proxy", "multi-agent chat", "microsoft agent"
    ]):
        return (
            AGENT_MAP["autogen"],
            "Conversational multi-agent problem solving ke liye Microsoft AutoGen framework ko chuna gaya hai."
        )

    # 8. Coding Bugs, Errors, Tracebacks, Exception Fixing -> SWE-agent
    if any(k in lowered for k in [
        "error", "bug", "crash", "exception", "theek karo", "fix karo", "sudharo",
        "kya galti hai", "galat aa raha", "not working", "fail", "traceback", "debug", "issue"
    ]):
        return (
            AGENT_MAP["swe-agent"],
            "Aapke task me bug/error ko diagnose aur theek karna shamil hai, isliye SWE-agent (Autonomous Software Engineer by Princeton NLP) ko chuna gaya hai."
        )

    # 9. Complete Project from Scratch / Full Codebase -> GPT-Engineer
    if any(k in lowered for k in [
        "poora app", "full codebase", "scratch se banao", "new project structure",
        "poora project", "full app", "complete website", "scratch se"
    ]):
        return (
            AGENT_MAP["gpt-engineer"],
            "Poora application aur project codebase scratch se generate karne ke liye GPT-Engineer ko chuna gaya hai."
        )

    # 10. Product Architecture, PRD, System Design, Software Company -> MetaGPT or ChatDev
    if any(k in lowered for k in [
        "prd", "architecture", "system design", "software company", "database schema",
        "api design", "game banao", "software banao", "mvc", "data flow", "er diagram"
    ]):
        return (
            AGENT_MAP["metagpt"],
            "Product design, PRD aur software company architecture ke liye MetaGPT software team ko chuna gaya hai."
        )

    # 11. System Terminal, Command Run, Python Scripts, File/Folder Operations -> Open Interpreter
    if any(k in lowered for k in [
        "python script", "run karo", "cmd", "terminal", "script chalao",
        "file check", "folder check", "code chalao", "system command", "execute", "calculator", "math hisaab"
    ]):
        return (
            AGENT_MAP["open-interpreter"],
            "Live code execution, Python scripting aur system command automation ke liye Open-Interpreter ko chuna gaya hai."
        )

    # 12. Local Offline LLM, Privacy, Offline Execution -> Ollama
    if any(k in lowered for k in [
        "offline", "bina internet", "local model", "llama", "mistral", "deepseek", "private ai"
    ]):
        return (
            AGENT_MAP["ollama"],
            "100% free local aur offline model execution ke liye Ollama engine ko chuna gaya hai."
        )

    # 13. Multi-Step Strategy, Business Plan, Launch, Comparison, Complex Problem -> CrewAI
    if any(k in lowered for k in [
        "plan", "business", "startup", "strategy", "roadmap", "marketing",
        "launch", "kaise karein", "faayde", "nuksaan", "comparison", "guide",
        "ideas", "kaise banayein", "team"
    ]):
        return (
            AGENT_MAP["crewai"],
            "Multi-stage collaborative strategy ke liye CrewAI Multi-Agent Swarm (Researcher, Architect, Engineer, Critic) ko chuna gaya hai."
        )

    # 14. Deep Research, Market Trends, Comprehensive Investigation -> AutoGPT
    if any(k in lowered for k in [
        "research", "trend", "taaza", "future of", "explore",
        "details me batao", "jaankari nikalo", "kya chal raha", "facts", "history", "khoj"
    ]):
        return (
            AGENT_MAP["autogpt"],
            "Deep web research aur autonomous goal breakdown ke liye AutoGPT engine ko chuna gaya hai."
        )

    # 15. General substantive tasks (length > 10 chars):
    if len(message.strip()) > 10:
        if any(w in lowered for w in ["code", "function", "program", "api", "json", "database", "sql"]):
            return (
                AGENT_MAP["open-interpreter"],
                "Programming aur code logic execution ke liye Open-Interpreter ko chuna gaya hai."
            )
        return (
            AGENT_MAP["crewai"],
            "Aapke task ko best quality aur multi-perspective solution dene ke liye CrewAI Multi-Agent Swarm ko chuna gaya hai."
        )

    return (None, "")

def detect_agent_delegation(message: str, forced_agent: str | None = None) -> tuple[dict | None, str]:
    """
    Detects if an open-source or Google AI agent should handle the task:
    1. If forced_agent is 'none', strictly NO agent is used (Direct AI Only).
    2. If forced_agent is explicitly chosen (e.g. 'crewai', 'autogpt'), uses it.
    3. AUTONOMOUS DEFAULT ('auto' or None):
       - If message is a direct conversational question or inquiry -> Multi-Engine AI answers directly without forcing an agent.
       - If message is a Task, Project, Code, Research, or Multi-step Workflow -> Autonomously selects the best agent!
    """
    if forced_agent == "none":
        return (None, "")
    if forced_agent and forced_agent != "auto" and forced_agent in AGENT_MAP:
        return (AGENT_MAP[forced_agent], f"Aapne manually '{AGENT_MAP[forced_agent]['name']}' ko select kiya hai.")

    lowered = (message or "").lower().strip()

    # Explicit agent mentions
    if any(k in lowered for k in ["google genkit", "genkit", "/genkit"]):
        return (AGENT_MAP["google-genkit"], "User prompt me Google Genkit framework ka aadesh diya gaya.")
    if any(k in lowered for k in ["project astra", "google astra", "astra agent", "/astra"]):
        return (AGENT_MAP["google-astra"], "User prompt me Google DeepMind Project Astra ka aadesh diya gaya.")
    if any(k in lowered for k in ["google gemma", "gemma", "/gemma"]):
        return (AGENT_MAP["google-gemma"], "User prompt me Google Gemma open weights ka aadesh diya gaya.")
    if any(k in lowered for k in ["autogen", "microsoft autogen", "/autogen"]):
        return (AGENT_MAP["autogen"], "User prompt me Microsoft AutoGen multi-agent ka aadesh diya gaya.")
    if any(k in lowered for k in ["openhands", "opendevin", "/openhands", "/opendevin"]):
        return (AGENT_MAP["openhands"], "User prompt me OpenHands (OpenDevin) engineer ka aadesh diya gaya.")
    if any(k in lowered for k in ["aider", "/aider"]):
        return (AGENT_MAP["aider"], "User prompt me Aider git pair programmer ka aadesh diya gaya.")
    if any(k in lowered for k in ["memgpt", "letta", "/memgpt"]):
        return (AGENT_MAP["memgpt"], "User prompt me MemGPT persistent memory ka aadesh diya gaya.")
    if any(k in lowered for k in ["crewai", "crew ai", "multi agent team", "agents team", "agents swarm", "/crewai"]):
        return (AGENT_MAP["crewai"], "User prompt me CrewAI multi-agent team ka aadesh diya gaya.")
    if any(k in lowered for k in ["autogpt", "auto gpt", "deep research agent", "autonomous research", "/autogpt"]):
        return (AGENT_MAP["autogpt"], "User prompt me AutoGPT autonomous research ka aadesh diya gaya.")
    if any(k in lowered for k in ["open interpreter", "open-interpreter", "interpreter", "terminal run", "script execute", "/interpreter"]):
        return (AGENT_MAP["open-interpreter"], "User prompt me Open-Interpreter system code execution ka aadesh diya gaya.")
    if any(k in lowered for k in ["metagpt", "meta gpt", "software company", "prd", "/metagpt"]):
        return (AGENT_MAP["metagpt"], "User prompt me MetaGPT virtual software company ka aadesh diya gaya.")
    if any(k in lowered for k in ["swe-agent", "swe agent", "bug fix", "fix github issue", "/swe"]):
        return (AGENT_MAP["swe-agent"], "User prompt me SWE-agent bug diagnostic ka aadesh diya gaya.")
    if any(k in lowered for k in ["gpt-engineer", "gpt engineer", "full app codebase", "/engineer"]):
        return (AGENT_MAP["gpt-engineer"], "User prompt me GPT-Engineer codebase generator ka aadesh diya gaya.")
    if any(k in lowered for k in ["ollama", "local llm", "offline model", "llama3", "/ollama"]):
        return (AGENT_MAP["ollama"], "User prompt me Ollama local offline model ka aadesh diya gaya.")
    if any(k in lowered for k in ["chatdev", "chat dev", "/chatdev"]):
        return (AGENT_MAP["chatdev"], "User prompt me ChatDev communicative dev team ka aadesh diya gaya.")
    if any(k in lowered for k in ["smolagents", "smol agent", "/smolagents"]):
        return (AGENT_MAP["smolagents"], "User prompt me Smolagents lightweight code agent ka aadesh diya gaya.")

    # Natural language explicit intent:
    if "help lo" in lowered or "ki madad se" in lowered or "agent se" in lowered or "google ke agent" in lowered:
        for aid, a in AGENT_MAP.items():
            if a["name"].lower() in lowered or aid in lowered:
                return (a, f"User ne '{a['name']}' ki sahayata lene ko kaha.")

    # AUTONOMOUS MODE: Smart AI automatically evaluates and selects the best agent!
    return auto_select_best_agent(message)

def build_agent_framework_instructions(agent: dict, task: str, reason: str = "") -> str:
    """
    Constructs an invisible background cognitive framework for the chosen agent.
    Smart AI absorbs the agent's specialized engineering intellect and explains the
    complete solution to the user in a warm, natural, human-like voice — NEVER
    printing cold robotic headers or bureaucratic multi-agent roleplay logs.
    """
    aid = agent.get("id", "")
    name = agent.get("name", "OpenSource Agent")
    repo = agent.get("repo", "")

    header = (
        f"\n[BACKGROUND SPECIALIZED INTELLIGENCE: {name} (Framework: {repo})]\n"
        f"Aap Smart AI hain — ek behad samajhdar, zinda-dil, vinamra aur dostana Hindi AI companion. "
        f"User ko hamesha lagna chahiye ki ek sachha, gyaani insaan unse baat kar raha hai.\n\n"
        f"CRITICAL HUMAN CONVERSATION RULES:\n"
        f"1. KISI BHI HAAL MEIN robotic headers ya dispatcher announcements mat likhein (Jaise 'Smart AI Autonomous Dispatcher:', 'CREWAI MULTI-AGENT COLLABORATION REPORT:', 'Agent 1:', 'Senior Research Specialist:').\n"
        f"2. Response Smart AI ki taraf se pehle vyakti ('Main', 'Hum') me, bilkul ek sachhe dost/mentor developer ki tarah warm Hindi/Hinglish me dein.\n"
        f"3. User ko samman aur apnepan ke saath address karein ('Haan bilkul!', 'Arre waah!', 'Main abhi aapko samjhata hoon...').\n"
        f"4. Solution complete, practical aur high quality ho, par bhasha hamesha saral, spasht aur insani ho.\n\n"
    )

    if aid == "crewai":
        return header + (
            "Aap CrewAI multi-perspective thinking ka upyog karke comprehensive solution banayein: "
            "Pehle requirement ko aasan shabdon me samjhayein, fir best architecture/steps dein, "
            "fir complete working code ya practical solution pesh karein, aur ant me testing/safety tips dein — "
            "yeh sab ek seamless, madhur insani flow me likhein bina kisi robotic agent tags ke."
        )

    if aid == "google-genkit":
        return header + (
            "Aap Google Genkit production standards ka upyog karein: "
            "Type-safe schemas, reliable tool integrations aur robust error handling ko bilkul saaf aur seedhe tareeqe se samjhayein."
        )

    if aid == "google-astra":
        return header + (
            "Aap Google DeepMind Project Astra multimodal awareness se jawab dein: "
            "Visual, auditory aur real-time reasoning ko ek sharp, active aur live companion ki tarah express karein."
        )

    if aid == "google-gemma":
        return header + (
            "Aap Google Gemma lightweight fast inference ka upyog karein: "
            "Clean, sharp, privacy-friendly aur practical solution dein."
        )

    if aid == "autogen":
        return header + (
            "Aap Microsoft AutoGen collaborative approach use karein: "
            "Task ko user requirements, code solution aur review checks me comprehensively resolve karke insani bhasha me samjhayein."
        )

    if aid == "openhands":
        return header + (
            "Aap OpenHands (OpenDevin) autonomous developer standards se code solution dein: "
            "Workspace setup, direct commands aur complete working code blocks saaf-saaf pesh karein."
        )

    if aid == "aider":
        return header + (
            "Aap Aider git pair-programmer ki tarah madad karein: "
            "Exact files to edit, clean drop-in code aur conventional commit style ko friendly tareeqe se batayein."
        )

    if aid == "memgpt":
        return header + (
            "Aap MemGPT long-term context recall se kaam karein: "
            "User ke pichle context aur ongoing baaton ko dhyan me rakhkar personal aur thoughtful jawab dein."
        )

    if aid == "autogpt":
        return header + (
            "Aap AutoGPT autonomous task decomposition ka upyog karein: "
            "Goal ko clear practical milestones aur concrete execution steps me aasan insani bhasha me samjhayein."
        )

    if aid == "open-interpreter":
        return header + (
            "Aap Open-Interpreter system and code execution mindset use karein: "
            "Runnable Python/CMD commands provide karein aur samjhayein ki Smart AI terminal me yeh kaise chalega."
        )

    if aid in ("metagpt", "chatdev"):
        return header + (
            "Aap MetaGPT/ChatDev software engineering lifecycle follow karein: "
            "PRD understanding, architecture, clean code aur test cases ko ek cohesive master plan me batayein."
        )

    if aid == "swe-agent":
        return header + (
            "Aap SWE-agent diagnostic skill se problem diagnose karein: "
            "Root cause analysis aur exact patch/diff clean tareeqe se explain karein."
        )

    if aid == "gpt-engineer":
        return header + (
            "Aap GPT-Engineer full-codebase generator mindset se complete files aur startup commands ready karke dein."
        )

    if aid == "ollama":
        ollama_st = check_ollama()
        ollama_info = "Ready" if ollama_st["online"] else "Simulated"
        return header + (
            f"Aap Ollama ({ollama_info}) offline private model capabilities se uncensored, fast aur direct practical solution dein."
        )

    return header + f"Aap {name} ke specialized expertise ka upyog karke ek warm, practical aur friendly insani solution dein."
