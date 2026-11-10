"""
Smart AI - Curated Directory of Free GitHub Open-Source & Google AI Agents
--------------------------------------------------------------------------
Google DeepMind, Firebase, Microsoft, aur Open-Source community ke top 26
AI Agents shamil hain. Har agent ka GitHub link, stars count, category,
Hindi description aur install command integrated hai.
"""

from __future__ import annotations

OPENSOURCE_AGENTS = [
    # ------------------ GOOGLE AI AGENTS ------------------
    {
        "id": "google-genkit",
        "name": "Google Genkit",
        "icon": "⚡",
        "stars": "⭐ 10k+",
        "category": "Google AI",
        "repo": "firebase/genkit",
        "github_url": "https://github.com/firebase/genkit",
        "website_url": "https://firebase.google.com/docs/genkit",
        "license": "Open Source (Apache-2.0)",
        "clone_cmd": "npm install -g genkit",
        "desc": "Google ka official open-source AI agent framework. Production-grade multi-agent workflows, schema validation aur Google tool integration ke liye best hai.",
        "tags": ["Google Official", "Agent Framework", "TypeScript", "Node.js"]
    },
    {
        "id": "google-astra",
        "name": "Google Project Astra",
        "icon": "🌌",
        "stars": "⭐ Google DeepMind",
        "category": "Google AI",
        "repo": "google-deepmind",
        "github_url": "https://deepmind.google/technologies/gemini/project-astra/",
        "website_url": "https://deepmind.google/technologies/gemini/",
        "license": "Google DeepMind Ecosystem",
        "clone_cmd": "pip install google-genai",
        "desc": "Google DeepMind ka future multimodal universal agent. Real-time video dekh kar, screen samajh kar aur aawaz se turant faisle leta hai.",
        "tags": ["Google DeepMind", "Multimodal", "Vision", "Voice AI"]
    },
    {
        "id": "google-gemma",
        "name": "Google Gemma Agents",
        "icon": "💎",
        "stars": "⭐ 15k+",
        "category": "Google AI",
        "repo": "google-deepmind/gemma",
        "github_url": "https://github.com/google-deepmind/gemma",
        "website_url": "https://ai.google.dev/gemma",
        "license": "Open Weights (Free Commercial Use)",
        "clone_cmd": "ollama run gemma2",
        "desc": "Google DeepMind ka 100% free open-weights model family (Gemma 2, PaliGemma). Laptop par bina internet ke fast agentic tasks run karta hai.",
        "tags": ["Google DeepMind", "Open Weights", "Local LLM", "Free"]
    },

    # ------------------ TOP AUTONOMOUS & CODING AGENTS ------------------
    {
        "id": "openhands",
        "name": "OpenHands (OpenDevin)",
        "icon": "🙌",
        "stars": "⭐ 44k+",
        "category": "Coding & System",
        "repo": "All-Hands-AI/OpenHands",
        "github_url": "https://github.com/All-Hands-AI/OpenHands",
        "website_url": "https://all-hands.dev/",
        "license": "Open Source (MIT)",
        "clone_cmd": "docker run -it --pull=always -p 3000:3000 ghcr.io/all-hands-ai/openhands:main",
        "desc": "Devin AI ka open-source vikalp. Yeh autonomous software engineer internet browse karta hai, terminal commands chalata hai aur GitHub issues theek karta hai.",
        "tags": ["Autonomous Engineer", "Devin Alternative", "Docker", "Git"]
    },
    {
        "id": "autogen",
        "name": "Microsoft AutoGen",
        "icon": "💬",
        "stars": "⭐ 37k+",
        "category": "Multi-Agent",
        "repo": "microsoft/autogen",
        "github_url": "https://github.com/microsoft/autogen",
        "website_url": "https://microsoft.github.io/autogen/",
        "license": "Open Source (MIT)",
        "clone_cmd": "pip install autogen-agentchat",
        "desc": "Microsoft Research ka multi-agent conversation framework jisme multiple conversational agents aapas me baat-cheet karke code aur problem solve karte hain.",
        "tags": ["Microsoft", "Multi-Agent", "Conversational AI", "Python"]
    },
    {
        "id": "aider",
        "name": "Aider Pair Programmer",
        "icon": "👨‍💻",
        "stars": "⭐ 28k+",
        "category": "Coding & System",
        "repo": "paul-gauthier/aider",
        "github_url": "https://github.com/paul-gauthier/aider",
        "website_url": "https://aider.chat/",
        "license": "Open Source (Apache-2.0)",
        "clone_cmd": "pip install aider-chat",
        "desc": "Terminal me chalne wala AI Pair Programmer. Aapke local git repo ki multiple files ko automatically edit karta hai aur git commit banata hai.",
        "tags": ["Git", "Pair Programming", "Terminal", "Local Repo"]
    },
    {
        "id": "memgpt",
        "name": "MemGPT (Letta)",
        "icon": "🧠",
        "stars": "⭐ 15k+",
        "category": "Autonomous",
        "repo": "letta-ai/letta",
        "github_url": "https://github.com/letta-ai/letta",
        "website_url": "https://www.letta.com/",
        "license": "Open Source (Apache-2.0)",
        "clone_cmd": "pip install letta",
        "desc": "OS-style tiered virtual memory management wala agent. Yeh mahino purani baatein aur context bina context-limit bhare hamesha yaad rakhta hai.",
        "tags": ["Perpetual Memory", "OS Architecture", "Long-term Recall"]
    },
    {
        "id": "phidata",
        "name": "Phidata (Agno)",
        "icon": "🚀",
        "stars": "⭐ 19k+",
        "category": "Frameworks",
        "repo": "phidata-hq/phidata",
        "github_url": "https://github.com/phidata-hq/phidata",
        "website_url": "https://phidata.com/",
        "license": "Open Source (MIT)",
        "clone_cmd": "pip install phidata",
        "desc": "Memory, knowledge base aur 50+ tool integration ke sath multi-modal autonomous AI agents banane ka fast Python framework.",
        "tags": ["Multi-Modal", "Tools", "Fast", "Memory"]
    },
    {
        "id": "plandex",
        "name": "Plandex",
        "icon": "📐",
        "stars": "⭐ 12k+",
        "category": "Coding & System",
        "repo": "plandex-ai/plandex",
        "github_url": "https://github.com/plandex-ai/plandex",
        "website_url": "https://plandex.ai/",
        "license": "Open Source (AGPL-3.0)",
        "clone_cmd": "curl -sL https://plandex.ai/install.sh | bash",
        "desc": "Complex, multi-file software projects ke liye terminal AI coding engine. Version control aur branches ke sath bada code likhta hai.",
        "tags": ["Complex Codebases", "Terminal", "Multi-file"]
    },
    {
        "id": "gorilla",
        "name": "Gorilla (UC Berkeley)",
        "icon": "🦍",
        "stars": "⭐ 13k+",
        "category": "Workflows & Ops",
        "repo": "ShishirPatil/gorilla",
        "github_url": "https://github.com/ShishirPatil/gorilla",
        "website_url": "https://gorilla.cs.berkeley.edu/",
        "license": "Open Source (Apache-2.0)",
        "clone_cmd": "pip install gorilla-cli",
        "desc": "UC Berkeley ka tool-calling aur API agent jo 10,000+ real-world web APIs ko bina hallucination ke seamlessly integrate karta hai.",
        "tags": ["UC Berkeley", "API Calling", "Tool Use"]
    },

    # ------------------ ORIGINAL 16 POPULAR AGENTS ------------------
    {
        "id": "autogpt",
        "name": "AutoGPT",
        "icon": "🤖",
        "stars": "⭐ 168k+",
        "category": "Autonomous",
        "repo": "Significant-Gravitas/AutoGPT",
        "github_url": "https://github.com/Significant-Gravitas/AutoGPT",
        "website_url": "https://agpt.co/",
        "license": "Open Source (MIT)",
        "clone_cmd": "git clone https://github.com/Significant-Gravitas/AutoGPT.git",
        "desc": "Duniya ka sabse mashhoor autonomous AI agent framework. Goals ko chote tasks me todkar internet browse aur kaam poora karta hai.",
        "tags": ["Autonomous", "Web Browsing", "Python", "CLI"]
    },
    {
        "id": "crewai",
        "name": "CrewAI",
        "icon": "👥",
        "stars": "⭐ 28k+",
        "category": "Multi-Agent",
        "repo": "crewAIInc/crewAI",
        "github_url": "https://github.com/crewAIInc/crewAI",
        "website_url": "https://crewai.com/",
        "license": "Open Source (MIT)",
        "clone_cmd": "pip install crewai crewai-tools",
        "desc": "Multiple autonomous role-playing agents (Researcher, Writer, Coder) ki team banakar complex kaam karwane ka top framework.",
        "tags": ["Multi-Agent", "Team Collaboration", "LangChain Compatible"]
    },
    {
        "id": "open-interpreter",
        "name": "Open Interpreter",
        "icon": "💻",
        "stars": "⭐ 57k+",
        "category": "Coding & System",
        "repo": "openinterpreter/open-interpreter",
        "github_url": "https://github.com/openinterpreter/open-interpreter",
        "website_url": "https://openinterpreter.com/",
        "license": "Open Source (AGPL-3.0)",
        "clone_cmd": "pip install open-interpreter",
        "desc": "Aapke computer ke terminal, Python aur system apps ko natural voice/text se control karne wala open-source computer agent.",
        "tags": ["Coding", "System Automation", "Terminal", "Local Control"]
    },
    {
        "id": "ollama",
        "name": "Ollama",
        "icon": "🦙",
        "stars": "⭐ 115k+",
        "category": "Local LLM",
        "repo": "ollama/ollama",
        "github_url": "https://github.com/ollama/ollama",
        "website_url": "https://ollama.com/",
        "license": "Open Source (MIT)",
        "clone_cmd": "curl -fsSL https://ollama.com/install.sh | sh",
        "desc": "Llama 3, Mistral, Gemma aur DeepSeek models ko apne laptop par 100% free aur bina internet ke chalane ka best tool.",
        "tags": ["Local LLM", "Offline AI", "Privacy", "Zero Cost"]
    },
    {
        "id": "metagpt",
        "name": "MetaGPT",
        "icon": "🏢",
        "stars": "⭐ 46k+",
        "category": "Multi-Agent",
        "repo": "geekan/MetaGPT",
        "github_url": "https://github.com/geekan/MetaGPT",
        "website_url": "https://www.deepwisdom.ai/",
        "license": "Open Source (MIT)",
        "clone_cmd": "pip install metagpt",
        "desc": "Ek poori Software Company simulate karta hai: Product Manager PRD likhta hai, Architect design banata hai, aur Engineer code karta hai.",
        "tags": ["Software Company", "SOP", "Full-Stack Development"]
    },
    {
        "id": "chatdev",
        "name": "ChatDev",
        "icon": "🎮",
        "stars": "⭐ 26k+",
        "category": "Coding & System",
        "repo": "OpenBMB/ChatDev",
        "github_url": "https://github.com/OpenBMB/ChatDev",
        "website_url": "https://chatdev.online/",
        "license": "Open Source (Apache-2.0)",
        "clone_cmd": "git clone https://github.com/OpenBMB/ChatDev.git",
        "desc": "Virtual software development company jisme AI agents aapas me baat-cheet karke software, games aur apps banate hain.",
        "tags": ["Game Dev", "Conversational AI", "Python Apps"]
    },
    {
        "id": "dify",
        "name": "Dify AI",
        "icon": "⚡",
        "stars": "⭐ 63k+",
        "category": "Workflows & Ops",
        "repo": "langgenius/dify",
        "github_url": "https://github.com/langgenius/dify",
        "website_url": "https://dify.ai/",
        "license": "Open Source (Apache-2.0)",
        "clone_cmd": "git clone https://github.com/langgenius/dify.git",
        "desc": "Open-source visual LLM app orchestrator aur agent builder. Visual flowcharts se AI agents aur chatbots banayein.",
        "tags": ["Visual Agent Builder", "RAG", "Workflows", "API"]
    },
    {
        "id": "langgraph",
        "name": "LangGraph (LangChain)",
        "icon": "🕸️",
        "stars": "⭐ 16k+",
        "category": "Frameworks",
        "repo": "langchain-ai/langgraph",
        "github_url": "https://github.com/langchain-ai/langgraph",
        "website_url": "https://langchain-ai.github.io/langgraph/",
        "license": "Open Source (MIT)",
        "clone_cmd": "pip install -U langgraph",
        "desc": "Cyclic computational graphs ke jariye highly reliable, memory-aware multi-actor agent workflows banane ka modern framework.",
        "tags": ["Stateful Agents", "Human-in-the-loop", "Cyclic Graphs"]
    },
    {
        "id": "swe-agent",
        "name": "SWE-agent",
        "icon": "🔧",
        "stars": "⭐ 15k+",
        "category": "Coding & System",
        "repo": "princeton-nlp/SWE-agent",
        "github_url": "https://github.com/princeton-nlp/SWE-agent",
        "website_url": "https://swe-agent.com/",
        "license": "Open Source (MIT)",
        "clone_cmd": "git clone https://github.com/princeton-nlp/SWE-agent.git",
        "desc": "Princeton University ka autonomous AI agent jo GitHub repositories ke bug reports aur real issues ko khud theek karta hai.",
        "tags": ["Bug Fixing", "GitHub Issues", "Princeton NLP"]
    },
    {
        "id": "gpt-engineer",
        "name": "GPT-Engineer",
        "icon": "🏗️",
        "stars": "⭐ 53k+",
        "category": "Coding & System",
        "repo": "gpt-engineer-org/gpt-engineer",
        "github_url": "https://github.com/gpt-engineer-org/gpt-engineer",
        "website_url": "https://gptengineer.app/",
        "license": "Open Source (MIT)",
        "clone_cmd": "pip install gpt-engineer",
        "desc": "Sirf ek line ke prompt se poora software codebase, frontend aur backend structure generate karne wala agent.",
        "tags": ["App Generation", "Codebase Builder", "CLI"]
    },
    {
        "id": "smolagents",
        "name": "Smolagents (Hugging Face)",
        "icon": "🤗",
        "stars": "⭐ 13k+",
        "category": "Frameworks",
        "repo": "huggingface/smolagents",
        "github_url": "https://github.com/huggingface/smolagents",
        "website_url": "https://huggingface.co/docs/smolagents",
        "license": "Open Source (Apache-2.0)",
        "clone_cmd": "pip install smolagents",
        "desc": "Hugging Face ka ultra-lightweight library jo text actions ki jagah direct executable Python code ke sath agent chalata hai.",
        "tags": ["Code Agents", "Hugging Face", "Lightweight"]
    },
    {
        "id": "babyagi",
        "name": "BabyAGI",
        "icon": "👶",
        "stars": "⭐ 20k+",
        "category": "Autonomous",
        "repo": "yoheinakajima/babyagi",
        "github_url": "https://github.com/yoheinakajima/babyagi",
        "website_url": "https://babyagi.org/",
        "license": "Open Source (MIT)",
        "clone_cmd": "git clone https://github.com/yoheinakajima/babyagi.git",
        "desc": "Pioneering task-driven autonomous agent jo task creation, prioritization aur execution ka endless loop chalata hai.",
        "tags": ["Classic AGI", "Task Loop", "Vector Search"]
    },
    {
        "id": "superagi",
        "name": "SuperAGI",
        "icon": "🦸",
        "stars": "⭐ 16k+",
        "category": "Autonomous",
        "repo": "TransformerOptimus/SuperAGI",
        "github_url": "https://github.com/TransformerOptimus/SuperAGI",
        "website_url": "https://superagi.com/",
        "license": "Open Source (MIT)",
        "clone_cmd": "git clone https://github.com/TransformerOptimus/SuperAGI.git",
        "desc": "Open-source autonomous AI framework jisme custom tools, graphical user interface aur performance telemetry inbuilt hai.",
        "tags": ["Agent Dashboard", "Marketplace", "Docker Ready"]
    },
    {
        "id": "agentgpt",
        "name": "AgentGPT",
        "icon": "🌐",
        "stars": "⭐ 33k+",
        "category": "Autonomous",
        "repo": "reworkd/AgentGPT",
        "github_url": "https://github.com/reworkd/AgentGPT",
        "website_url": "https://agentgpt.reworkd.ai/",
        "license": "Open Source (GPL-3.0)",
        "clone_cmd": "git clone https://github.com/reworkd/AgentGPT.git",
        "desc": "Web browser ke andar hi autonomous AI agents configure karke deploy karne ka visually attractive open-source tool.",
        "tags": ["Browser UI", "Next.js", "Visual Agent"]
    },
    {
        "id": "camel-ai",
        "name": "CAMEL-AI",
        "icon": "🐫",
        "stars": "⭐ 7k+",
        "category": "Multi-Agent",
        "repo": "camel-ai/camel",
        "github_url": "https://github.com/camel-ai/camel",
        "website_url": "https://www.camel-ai.org/",
        "license": "Open Source (Apache-2.0)",
        "clone_cmd": "pip install camel-ai",
        "desc": "Communicative Agents for Mind Exploration — communicative multi-agent research aur complex social interactions ke liye.",
        "tags": ["Communicative Agents", "Role-Playing", "Research"]
    },
    {
        "id": "taskingai",
        "name": "TaskingAI",
        "icon": "🎯",
        "stars": "⭐ 5k+",
        "category": "Workflows & Ops",
        "repo": "TaskingAI/TaskingAI",
        "github_url": "https://github.com/TaskingAI/TaskingAI",
        "website_url": "https://tasking.ai/",
        "license": "Open Source (Apache-2.0)",
        "clone_cmd": "git clone https://github.com/TaskingAI/TaskingAI.git",
        "desc": "Unified BaaS for generative AI applications jisme multi-agent framework aur vector memory shamil hai.",
        "tags": ["BaaS", "Tool Integration", "Vector DB"]
    }
]

def get_all_agents(category: str | None = None, query: str | None = None) -> list[dict]:
    agents = list(OPENSOURCE_AGENTS)
    if category and category.lower() != "all":
        cat_low = category.lower().strip()
        agents = [a for a in agents if cat_low in a.get("category", "").lower()]
    if query:
        q_low = query.lower().strip()
        agents = [
            a for a in agents
            if q_low in a.get("name", "").lower()
            or q_low in a.get("desc", "").lower()
            or any(q_low in t.lower() for t in a.get("tags", []))
            or q_low in a.get("repo", "").lower()
        ]
    return agents

def get_agent_categories() -> list[str]:
    cats = ["All", "Google AI"]
    for a in OPENSOURCE_AGENTS:
        c = a.get("category", "")
        if c and c not in cats:
            cats.append(c)
    return cats

def get_agents_summary_text() -> str:
    total = len(OPENSOURCE_AGENTS)
    lines = [
        f"🤖 **Top {total} Free Open-Source & Google AI Agents (GitHub Linked):**\n",
        "Smart AI me Google DeepMind, Firebase, Microsoft aur top open-source community ke agents connected hain. Aap inka direct use kar sakte hain:\n"
    ]
    for idx, a in enumerate(OPENSOURCE_AGENTS, 1):
        lines.append(
            f"{idx}. {a['icon']} **[{a['name']}]({a['github_url']})** ({a['stars']}) - *{a['category']}*\n"
            f"   • {a['desc']}\n"
            f"   • Repo: [{a['repo']}]({a['github_url']}) | License: `{a['license']}`\n"
        )
    lines.append("💡 Upar bane 🤖 **Agents** button par click karke aap sabhi agents ka live interactive hub dekh sakte hain aur kisi bhi agent ki help se kaam shuru kar sakte hain!")
    return "\n".join(lines)
