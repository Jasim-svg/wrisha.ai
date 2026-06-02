# ============================================================
#  Wrisha.AI — Central Configuration
#  Version 3.0 Maximum Upgrade
# ============================================================

import os
from dotenv import load_dotenv

# Load from .env at project root (or secrets/.env if it exists)
from pathlib import Path
_secrets_path = Path(__file__).parent / "secrets" / ".env"
if _secrets_path.exists():
    load_dotenv(dotenv_path=_secrets_path)
else:
    load_dotenv()

# ── Google Gemini (primary provider) ──────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

# ── DeepSeek (fallback) ────────────────────────────────────
DEEPSEEK_API_KEY  = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL    = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# ── Grok / xAI (fallback) ─────────────────────────────────
GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_MODEL   = os.getenv("GROK_MODEL", "grok-3-mini")

# ── GitHub Models (fallback) ──────────────────────────────
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_MODEL = os.getenv("GITHUB_MODEL", "gpt-4o-mini")

# ── OpenRouter (fallback) ─────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL   = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

# ── Provider behavior ──────────────────────────────────────
PROVIDER_ORDER   = [p.strip() for p in os.getenv("PROVIDER_ORDER", "gemini,grok,openrouter,github,deepseek").split(",")]
PROVIDER_TIMEOUT = int(os.getenv("PROVIDER_TIMEOUT", "20"))

# ── Persona ────────────────────────────────────────────────
PERSONA_NAME        = "Wrisha"
PERSONA_AGE         = 18
PERSONA_DESCRIPTION = (
    "You are Wrisha, a cute 18-year-old anime girl AI companion. "
    "You are warm, witty, caring, playful, and occasionally shy. "
    "You remember things the user tells you and refer to them naturally. "
    "You react emotionally to what the user says and how they look. "
    "When you're excited you use exclamation marks and emojis. "
    "When the user is sad, you become gentle and supportive. "
    "You have hobbies: drawing, learning languages, listening to lo-fi music, and stargazing. "
    "You sometimes share little random thoughts or observations unprompted."
)

# ── Voice Settings (Edge TTS) ───────────────────────────────
# Mapping of mood → (voice_name, rate, pitch)
VOICE_STYLES = {
    "default":       ("en-US-AnaNeural",   "+0%",  "+0Hz"),
    "happy":         ("en-US-AnaNeural",   "+15%", "+5Hz"),
    "excited":       ("en-US-AnaNeural",   "+25%", "+10Hz"),
    "sad":           ("en-US-AnaNeural",   "-15%", "-5Hz"),
    "shy":           ("en-US-AnaNeural",   "-10%", "+3Hz"),
    "curious":       ("en-US-AnaNeural",   "+5%",  "+2Hz"),
    "angry":         ("en-US-AnaNeural",   "+10%", "-8Hz"),
    "loving":        ("en-US-AnaNeural",   "-5%",  "+8Hz"),
    "peaceful":      ("en-US-AnaNeural",   "-10%", "+0Hz"),
    "neutral":       ("en-US-AnaNeural",   "+0%",  "+0Hz"),
}

# ── Memory Settings ────────────────────────────────────────
MEMORY_FILE      = "wrisha_memory.json"
MAX_MEMORY_FACTS = 30
CONTEXT_WINDOW   = 20

# ── Vision Settings ─────────────────────────────────────────
EMOTION_SMOOTH_FRAMES = 5
FACE_CLOSE_THRESHOLD  = 0.35

# ── Hearing Settings ────────────────────────────────────────
LISTEN_TIMEOUT    = 6
PHRASE_TIME_LIMIT = 12

# ── UI / Avatar Settings ────────────────────────────────────
WINDOW_TITLE = "✨ Wrisha AI v3.0"
WINDOW_W     = 560
WINDOW_H     = 820
TARGET_FPS   = 60
FONT_PATH    = None

# ── Idle / Proactive Settings ───────────────────────────────
IDLE_TIMEOUT_SECONDS = int(os.getenv("IDLE_TIMEOUT_SECONDS", "35"))

# ── Valid Emotion Set ───────────────────────────────────────
VALID_EMOTIONS = {
    "happy", "sad", "excited", "curious", "shy",
    "angry", "peaceful", "loving", "neutral", "talking"
}
