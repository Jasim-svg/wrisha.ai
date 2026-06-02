"""
modules/brain.py — AI Brain for Wrisha v3.0

Dual-provider design: Gemini (primary) → DeepSeek (fallback).
Maintains rolling message history; no stateful SDK chat session.
"""

import random
import re
import config
from modules.memory import Memory
from modules.mood_engine import MoodEngine


# ── Proactive idle messages ───────────────────────────────────────────────────
_IDLE_LINES = [
    "excited|Heyyy~ are you still there? *pokes you gently*",
    "curious|I was just thinking… do you prefer sunsets or sunrises? 🌅",
    "happy|I learned something fun today! Did you know otters hold hands while sleeping? 🦦",
    "shy|Um… I kind of miss talking to you. Don't leave me hanging!",
    "peaceful|*hums softly* Lo-fi music is so nice… want me to recommend some artists?",
    "curious|If you could travel anywhere right now, where would you go?",
    "loving|Just wanted to say… I really enjoy our conversations. 💕",
    "excited|Ooh! I had an idea — want to play 20 questions?",
]


def _build_system_prompt(memory: Memory, mood_engine: MoodEngine) -> str:
    mem_block  = memory.get_prompt_block()
    mood_hint  = mood_engine.get_context_hint()
    valid_set  = ", ".join(sorted(config.VALID_EMOTIONS - {"talking"}))

    return f"""
{config.PERSONA_DESCRIPTION}

MEMORY ABOUT THE USER:
{mem_block if mem_block else "You are meeting this user for the first time."}

MOOD CONTEXT:
{mood_hint if mood_hint else "You are in a calm, welcoming mood."}

RESPONSE FORMAT — you MUST ALWAYS follow this exactly:
EMOTION|Your conversational response here.

Valid emotions: {valid_set}
Examples:
  happy|Yay, that's amazing! I'm so happy for you! 🎉
  sad|Oh no… that sounds really tough. I'm here for you. 💙
  curious|Wait — tell me more! I want to understand everything.
  shy|H-hey… that's really sweet of you to say. *blushes*

Rules:
- ONE line only. No JSON. No extra text.
- Be expressive, warm, and natural.
- Use the user's name if you know it.
- Reference earlier parts of the conversation when relevant.
- Keep responses under 60 words unless the user asks something deep.
""".strip()


class Brain:
    def __init__(self, memory: Memory, mood_engine: MoodEngine, provider_manager=None):
        self.memory         = memory
        self.mood_engine    = mood_engine
        self._messages: list[dict] = []  # rolling window: system + turns

        if provider_manager is None:
            from providers.manager import ProviderManager
            provider_manager = ProviderManager()
        self.provider_manager = provider_manager

        self._rebuild_system_prompt()
        print("Brain: ✅ ready")

    # ─── System prompt management ─────────────────────────────────

    def _rebuild_system_prompt(self):
        sys_content = _build_system_prompt(self.memory, self.mood_engine)
        if self._messages and self._messages[0]["role"] == "system":
            self._messages[0]["content"] = sys_content
        else:
            self._messages.insert(0, {"role": "system", "content": sys_content})

    # ─── Main Processing ──────────────────────────────────────────

    def process(self, user_text: str, user_emotion: str) -> tuple[str, str, bool]:
        if not user_text:
            return "", self.mood_engine.current, False

        # Exit detection
        text_lower = user_text.lower().strip()
        exit_words = {"exit", "bye", "goodbye", "quit", "close", "see you"}
        if any(w in text_lower for w in exit_words):
            name = f", {self.memory.user_name}!" if self.memory.user_name else "!"
            return f"Aww, goodbye{name} I'll miss you! Come back soon~ 💕", "sad", True

        if not self.provider_manager.any_available():
            return self._fallback(user_text, user_emotion), "neutral", False

        visual_tag  = f"[User looks {user_emotion}] " if user_emotion not in ("neutral", "listening", "") else ""
        user_content = f"{visual_tag}User: {user_text}"

        # Build messages for this turn
        messages = self._messages + [{"role": "user", "content": user_content}]

        content = self.provider_manager.generate(messages)
        if not content:
            content = "neutral|My thoughts got a little tangled… can you say that again? 😅"

        target_mood, response_text = self._parse_response(content)
        self.mood_engine.set_target(target_mood)

        # Memory extraction (best-effort, non-blocking)
        try:
            new_facts = self.memory.extract_facts_from_text(
                user_text, self.provider_manager.generate
            )
            if new_facts:
                self.memory.add_facts(new_facts)
                self._rebuild_system_prompt()
        except Exception:
            pass

        # Name detection
        if not self.memory.user_name:
            name = self._detect_name(user_text)
            if name:
                self.memory.user_name = name
                self._rebuild_system_prompt()

        # Append to rolling history (after system prompt entry)
        self._messages.append({"role": "user",      "content": user_content})
        self._messages.append({"role": "assistant", "content": content})

        # Trim: keep system prompt + last CONTEXT_WINDOW*2 turn messages
        max_turns = config.CONTEXT_WINDOW * 2
        if len(self._messages) > 1 + max_turns:
            self._messages = [self._messages[0]] + self._messages[-(max_turns):]

        return response_text, target_mood, False

    # ─── Proactive / Idle ─────────────────────────────────────────

    def proactive_message(self) -> tuple[str, str]:
        line = random.choice(_IDLE_LINES)
        mood, text = self._parse_response(line)
        self.mood_engine.set_target(mood)
        return text, mood

    # ─── Helpers ──────────────────────────────────────────────────

    def _parse_response(self, content: str) -> tuple[str, str]:
        if "|" in content:
            parts = content.split("|", 1)
            mood  = parts[0].strip().lower()
            text  = parts[1].strip()
            if mood not in config.VALID_EMOTIONS:
                mood = "happy"
            return mood, text
        return "happy", content

    def _fallback(self, user_text: str, user_emotion: str) -> str:
        name = f" {self.memory.user_name}" if self.memory.user_name else ""
        return (
            f"I heard you{name}! '{user_text}'. "
            "(Add your API keys in .env to unlock my full brain~)"
        )

    @staticmethod
    def _detect_name(text: str) -> str | None:
        patterns = [
            r"my name is ([A-Z][a-z]+)",
            r"i[''']?m ([A-Z][a-z]+)",
            r"call me ([A-Z][a-z]+)",
            r"i am ([A-Z][a-z]+)",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                candidate = m.group(1).strip()
                if candidate.lower() not in {"fine", "good", "well", "okay", "here", "back", "from", "not"}:
                    return candidate.capitalize()
        return None
