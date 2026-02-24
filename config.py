# ============================================================
#  Wrisha.AI — Central Configuration
#  Version 3.0 Maximum Upgrade
# ============================================================

# ── Google Gemini ──────────────────────────────────────────
GEMINI_API_KEY = "REMOVED"
GEMINI_MODEL   = "gemini-2.0-flash"          # Best free-tier model

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
MEMORY_FILE     = "wrisha_memory.json"
MAX_MEMORY_FACTS = 30          # Max facts stored in long-term memory
CONTEXT_WINDOW   = 20          # Last N exchanges kept in short-term context

# ── Vision Settings ─────────────────────────────────────────
EMOTION_SMOOTH_FRAMES = 5      # Frames to average for stable emotion read
FACE_CLOSE_THRESHOLD  = 0.35   # Face width / frame width ratio → "too close" → shy

# ── Hearing Settings ────────────────────────────────────────
LISTEN_TIMEOUT        = 6      # Seconds before giving up listening
PHRASE_TIME_LIMIT     = 12     # Max seconds for a single phrase

# ── UI / Avatar Settings ────────────────────────────────────
WINDOW_TITLE  = "✨ Wrisha AI v3.0"
WINDOW_W      = 560
WINDOW_H      = 820
TARGET_FPS    = 60
FONT_PATH     = None           # None = pygame default; set to .ttf path to use custom font

# ── Idle / Proactive Settings ───────────────────────────────
IDLE_TIMEOUT_SECONDS  = 35     # How long without input before Wrisha speaks unprompted

# ── Valid Emotion Set ───────────────────────────────────────
VALID_EMOTIONS = {
    "happy", "sad", "excited", "curious", "shy",
    "angry", "peaceful", "loving", "neutral", "talking"
}
