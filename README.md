# Wrisha.AI — Emotional Anime Girl AI Companion v3.0

A multimodal desktop AI companion with an anime-style animated avatar. She watches you through your webcam, listens to you speak, tracks your emotional state, remembers facts about you across sessions, and replies with a mood-modulated voice.

---

## Features

- **Vision** — webcam face detection + emotion recognition (FER/OpenCV)
- **Hearing** — microphone speech-to-text (SpeechRecognition)
- **Brain** — dual-provider AI: Gemini (primary) → DeepSeek (fallback)
- **Voice** — mood-modulated Edge TTS output (rate + pitch per emotion)
- **Avatar** — animated Pygame HUD with sprite, mood display, live subtitles
- **Memory** — persistent JSON long-term memory across restarts
- **Proactive** — speaks unprompted after idle timeout

---

## AI Brain — Provider Flow

```
User speaks
    │
    ▼
Brain.process()
    │
    ├─► Gemini (gemini-2.0-flash) ──► success → reply
    │       └── fail / no key
    │
    └─► DeepSeek (deepseek-v4-flash) ──► success → reply
            └── fail / no key
                    └── canned fallback text (no crash)
```

Provider selection is logged: `[brain] answered by gemini` or `[brain] answered by deepseek`.

---

## Setup

### 1. Clone and create environment

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure API keys

```bash
# Windows:
copy .env.example .env
# Mac/Linux:
cp .env.example .env
```

Open `.env` and fill in your keys:

```
GEMINI_API_KEY=your_gemini_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here
```

**Where to get keys (both free):**
- Gemini: [Google AI Studio](https://aistudio.google.com/) → Get API key
- DeepSeek: [DeepSeek Platform](https://platform.deepseek.com/) → API keys (new accounts get a free token grant)

You only need one key to run — the other acts as fallback.

### 3. Run

```bash
# Windows:
run.bat

# Mac/Linux:
bash run.sh

# or directly:
python main.py
```

---

## Security — Important

> **A Gemini API key was committed to this repo's git history in the past. That key is permanently compromised regardless of deletion. Rotate it immediately:**
> Go to [Google AI Studio](https://aistudio.google.com/) → Manage → Revoke the old key → Generate a new one → Put it only in `.env`.

Rules:
- **Never** put real keys in `config.py` or any tracked file.
- `.env` is in `.gitignore` — it will never be committed.
- `.env.example` has placeholder values only — it is safe to commit.

---

## Project Structure

```
wrisha.ai/
├── .env                  # real keys — gitignored
├── .env.example          # placeholder keys — committed
├── .gitignore
├── config.py             # loads secrets from env
├── main.py               # orchestrator
├── requirements.txt
├── run.bat / run.sh
├── modules/
│   ├── avatar.py
│   ├── brain.py          # uses provider layer
│   ├── hearing.py
│   ├── memory.py
│   ├── mood_engine.py
│   ├── vision.py
│   └── voice.py          # TTS temp files → .cache/
├── providers/            # multi-model layer
│   ├── base.py
│   ├── gemini_provider.py
│   ├── deepseek_provider.py
│   └── manager.py        # ordered fallback logic
└── tests/
    ├── test_gemini.py
    └── test_api.py
```

---

## Testing individual providers

```bash
# Test Gemini
python tests/test_gemini.py

# Test DeepSeek
python tests/test_api.py
```
