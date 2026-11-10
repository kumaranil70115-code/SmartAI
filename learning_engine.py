"""
Smart AI - Autonomous Self-Learning & Feedback Memory Engine
-----------------------------------------------------------
Yeh engine users ke 1-5 Star ratings, feedback aur corrections ko
permanently save karta hai, aur har naye sawaal mein AI ko pehle se
behtar banata hai taaki AI apni purani galtiyon ko dobara na dohraye.
"""

from __future__ import annotations
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MEMORY_FILE = ROOT / "learning_memory.json"

DEFAULT_MEMORY = {
    "total_ratings": 0,
    "average_rating": 5.0,
    "star_counts": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
    "learned_rules": [
        {
            "id": "rule_init_1",
            "topic": "Autonomous Actions",
            "rule": "Jab user bole 'tum khud se naya version update karo' ya koi action bole, to direct execute karein bina 'mere paas permission nahi hai' kahe.",
            "created_at": "2026-11-08"
        },
        {
            "id": "rule_init_2",
            "topic": "Speaking Speed & Turn-Taking",
            "rule": "Jawab bolne mein aasan, seedhe shabdon mein dein taaki aawaz crystal-clear sunai de.",
            "created_at": "2026-11-08"
        }
    ],
    "feedbacks": []
}

def load_memory() -> dict:
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure all keys exist
                for k, v in DEFAULT_MEMORY.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception:
            pass
    save_memory(DEFAULT_MEMORY)
    return dict(DEFAULT_MEMORY)

def save_memory(data: dict) -> bool:
    try:
        temp_file = ROOT / f"learning_memory_{int(time.time()*1000)}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        temp_file.replace(MEMORY_FILE)
        return True
    except Exception as exc:
        print(f"Error saving learning memory: {exc}")
        return False

def record_feedback(rating: int, query: str = "", response: str = "", feedback_text: str = "", tags: list | None = None) -> dict:
    """
    User ka Star Rating aur Feedback record karta hai aur
    AI ke liye naya self-learning rule create karta hai.
    """
    rating = max(1, min(5, int(rating or 5)))
    data = load_memory()

    data["total_ratings"] = data.get("total_ratings", 0) + 1
    star_str = str(rating)
    if "star_counts" not in data:
        data["star_counts"] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    data["star_counts"][star_str] = data["star_counts"].get(star_str, 0) + 1

    # Recalculate average rating
    total_stars = sum(int(s) * count for s, count in data["star_counts"].items())
    data["average_rating"] = round(total_stars / data["total_ratings"], 1)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    fb_id = f"fb_{int(time.time() * 1000)}"

    entry = {
        "id": fb_id,
        "rating": rating,
        "query": (query or "").strip()[:500],
        "response_snippet": (response or "").strip()[:300],
        "feedback": (feedback_text or "").strip()[:500],
        "tags": tags or [],
        "created_at": now_str
    }

    if "feedbacks" not in data:
        data["feedbacks"] = []
    data["feedbacks"].insert(0, entry)
    # Keep last 150 feedbacks
    data["feedbacks"] = data["feedbacks"][:150]

    # AUTONOMOUS LEARNING LOGIC:
    # If user gave low rating (<= 3) or provided improvement text,
    # generate a permanent self-learning rule for future responses!
    rule_created = None
    if feedback_text and len(feedback_text.strip()) > 3:
        clean_fb = feedback_text.strip()
        topic = (query or "General Query").strip()[:60]
        rule_text = f"Sawaal '{topic}' ke baare mein user correction: {clean_fb}"
        rule_id = f"rule_{int(time.time())}"
        rule_obj = {
            "id": rule_id,
            "topic": topic,
            "rule": rule_text,
            "created_at": now_str
        }
        data["learned_rules"].insert(0, rule_obj)
        data["learned_rules"] = data["learned_rules"][:50]
        rule_created = rule_obj

    save_memory(data)

    return {
        "success": True,
        "id": fb_id,
        "rating": rating,
        "average_rating": data["average_rating"],
        "total_ratings": data["total_ratings"],
        "rule_created": rule_created,
        "message": "Feedback safalta se save ho gaya. Smart AI ne ise yaad kar liya hai!"
    }

def get_learning_context() -> str:
    """
    Returns dynamic prompt context containing learned rules
    to inject into Gemini / Codex / Antigravity calls.
    """
    data = load_memory()
    rules = data.get("learned_rules", [])
    if not rules:
        return ""

    rule_lines = []
    for r in rules[:8]:  # Top 8 most recent / relevant rules
        rule_lines.append(f"• {r.get('rule', '')}")

    context = (
        "\n[SMART AI CONTINUOUS SELF-LEARNING & USER FEEDBACK MEMORY]:\n"
        "Aapne pichle user feedback aur ratings se yeh niyam sikhe hain. "
        "In galtiyon ko bilkul mat dohrana aur user ke anusar behtar jawab dena:\n"
        + "\n".join(rule_lines) + "\n"
    )
    return context

def get_learning_stats() -> dict:
    data = load_memory()
    return {
        "total_ratings": data.get("total_ratings", 0),
        "average_rating": data.get("average_rating", 5.0),
        "star_counts": data.get("star_counts", {}),
        "learned_rules": data.get("learned_rules", []),
        "recent_feedbacks": data.get("feedbacks", [])[:30]
    }

def delete_learned_rule(rule_id: str) -> bool:
    data = load_memory()
    initial_len = len(data.get("learned_rules", []))
    data["learned_rules"] = [r for r in data.get("learned_rules", []) if r.get("id") != rule_id]
    if len(data["learned_rules"]) != initial_len:
        save_memory(data)
        return True
    return False

def clear_all_learning() -> bool:
    save_memory(dict(DEFAULT_MEMORY))
    return True

