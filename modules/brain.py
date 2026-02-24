"""
modules/brain.py — AI Brain for Wrisha v3.0

Connects to Google Gemini with:
  - Rich persona and backstory
  - Persistent memory injection
  - Sliding window conversation context (last 20 turns)
  - Emotion-aware response style
  - Proactive idle messages
  - Extended emotion set
  - Robust response parsing
"""

import google.generativeai as genai
import random
import time
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

# ── System Prompt Builder ─────────────────────────────────────────────────────
def _build_system_prompt(memory: Memory, mood_engine: MoodEngine) -> str:
    mem_block   = memory.get_prompt_block()
    mood_hint   = mood_engine.get_context_hint()
    valid_set   = ", ".join(sorted(config.VALID_EMOTIONS - {"talking"}))

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
    """
    Wrisha's AI brain powered by Google Gemini.
    """

    def __init__(self, memory: Memory, mood_engine: MoodEngine):
        self.memory      = memory
        self.mood_engine = mood_engine
        self.model       = None
        self.chat        = None
        self._history    = []          # list of (role, text) tuples for context

        # Try connecting to Gemini
        api_key = config.GEMINI_API_KEY
        if not api_key or "YOUR_API_KEY" in api_key:
            print("Brain: WARNING — Gemini API Key not set. Using fallback mode.")
            return

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(config.GEMINI_MODEL)
            self._start_chat()
            print(f"Brain: ✅ Gemini connected ({config.GEMINI_MODEL})")
        except Exception as e:
            print(f"Brain: ❌ Connection error — {e}")
            self.model = None

    # ─── Chat Management ────────────────────────────────────────

    def _start_chat(self):
        """Start (or restart) a Gemini chat session with system context."""
        sys_prompt = _build_system_prompt(self.memory, self.mood_engine)
        self.chat = self.model.start_chat(history=[
            {"role": "user",  "parts": sys_prompt},
            {"role": "model", "parts": "understood|Sure! I'm ready. Let's talk! 💫"},
        ])

    def _refresh_system_prompt(self):
        """Rebuild system context after memory updates."""
        if self.model:
            try:
                self._start_chat()
            except Exception as e:
                print(f"Brain: refresh error — {e}")

    # ─── Main Processing ────────────────────────────────────────

    def process(self, user_text: str, user_emotion: str) -> tuple[str, str, bool]:
        """
        Process user input and return (response_text, target_mood, should_exit).
        """
        should_exit   = False
        target_mood   = self.mood_engine.current
        response_text = ""

        if not user_text:
            return "", target_mood, False

        # ── Exit detection ───────────────────────────────────────
        text_lower = user_text.lower().strip()
        exit_words = {"exit", "bye", "goodbye", "quit", "close", "see you"}
        if any(w in text_lower for w in exit_words):
            name = f", {self.memory.user_name}!" if self.memory.user_name else "!"
            return f"Aww, goodbye{name} I'll miss you! Come back soon~ 💕", "sad", True

        if not self.model:
            return self._fallback(user_text, user_emotion), "neutral", False

        # ── Build prompt ─────────────────────────────────────────
        visual_tag   = f"[User looks {user_emotion}] " if user_emotion not in ("neutral", "listening", "") else ""
        full_prompt  = f"{visual_tag}User: {user_text}"

        # ── Send to Gemini ───────────────────────────────────────
        try:
            response  = self.chat.send_message(full_prompt)
            content   = response.text.strip()
            target_mood, response_text = self._parse_response(content)

            # ── Memory extraction (async-lite: non-blocking best-effort) ──
            try:
                new_facts = self.memory.extract_facts_from_text(user_text, self.chat)
                if new_facts:
                    self.memory.add_facts(new_facts)
                    self._refresh_system_prompt()
            except Exception:
                pass

            # ── Name detection ───────────────────────────────────
            if not self.memory.user_name:
                name = self._detect_name(user_text)
                if name:
                    self.memory.user_name = name
                    self._refresh_system_prompt()

            self._history.append(("user",  user_text))
            self._history.append(("model", response_text))
            # Trim history
            if len(self._history) > config.CONTEXT_WINDOW * 2:
                self._history = self._history[-(config.CONTEXT_WINDOW * 2):]

        except Exception as e:
            print(f"Brain: Gemini error — {e}")
            response_text = "My thoughts got a little tangled… can you say that again? 😅"
            target_mood   = "sad"

        self.mood_engine.set_target(target_mood)
        return response_text, target_mood, should_exit

    # ─── Proactive / Idle ───────────────────────────────────────

    def proactive_message(self) -> tuple[str, str]:
        """Returns (response_text, mood) for an unprompted idle message."""
        line = random.choice(_IDLE_LINES)
        mood, text = self._parse_response(line)
        self.mood_engine.set_target(mood)
        return text, mood

    # ─── Helpers ────────────────────────────────────────────────

    def _parse_response(self, content: str) -> tuple[str, str]:
        """Parse 'EMOTION|text' response. Falls back gracefully."""
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
            "(Set your Gemini API key in config.py to unlock my full brain~)"
        )

    @staticmethod
    def _detect_name(text: str) -> str | None:
        """Very simple heuristic: 'my name is X' or 'I'm X' or 'call me X'."""
        import re
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
                # Filter out common false positives
                if candidate.lower() not in {"fine", "good", "well", "okay", "here", "back", "from", "not"}:
                    return candidate.capitalize()
        return None
