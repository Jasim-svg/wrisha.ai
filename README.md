# Wrisha.AI — Emotional Anime Girl AI Companion v3.0

A multimodal desktop AI companion with an anime-style animated avatar. She watches you through your webcam, listens to you speak, tracks your emotional state, remembers facts about you across sessions, and replies with a mood-modulated voice — powered by a 5-provider AI brain with automatic fallback.

---

## Features

| Module | What it does |
|--------|-------------|
| **Vision** | Webcam face detection + facial emotion recognition (FER / OpenCV) |
| **Hearing** | Microphone speech-to-text (SpeechRecognition + PyAudio) |
| **Brain** | 5-provider AI chain with automatic fallback (see below) |
| **Voice** | Mood-modulated Edge TTS — rate + pitch change per emotion |
| **Avatar** | Animated Pygame HUD: sprite, mood display, live subtitles |
| **Memory** | Persistent JSON long-term memory across sessions |
| **Proactive** | Speaks unprompted when idle for `IDLE_TIMEOUT_SECONDS` |

---

## AI Brain — 5-Provider Fallback Chain

Every reply tries providers in order. The first one that succeeds is used. If all fail, a canned fallback line is returned — the app never crashes.

```
User speaks
    │
    ▼
Brain.process()
    │
    ├─► 1. Gemini          gemini-2.5-flash-lite   (Google AI — free tier)
    │         └── fail / no key
    ├─► 2. Grok            grok-3-mini             (xAI — free tier)
    │         └── fail / no key
    ├─► 3. OpenRouter      llama-3.3-70b:free      (free models pool)
    │         └── fail / no key
    ├─► 4. GitHub Models   gpt-4o-mini             (free with GitHub token)
    │         └── fail / no key
    └─► 5. DeepSeek        deepseek-v4-flash       (pay-as-you-go fallback)
                  └── fail / no key
                          └── canned reply — no crash
```

The console logs which provider answered: `[brain] answered by gemini`

You only need **one working key** to run. Add more keys for resilience.

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/Jasim-svg/wrisha.ai.git
cd wrisha.ai

python -m venv .venv

# Windows:
.venv\Scripts\activate
# Mac / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Add your API keys

You can place keys in either location — both are gitignored:

**Option A — root `.env`**
```bash
# Windows:
copy .env.example .env
# Mac / Linux:
cp .env.example .env
```
Then open `.env` and fill in your keys.

**Option B — `secrets/.env`** *(already gitignored by `secrets/.gitignore`)*
```bash
copy .env.example secrets\.env
```
`config.py` checks `secrets/.env` first, then falls back to root `.env`.

### 3. Where to get free API keys

| Provider | Link | Free tier |
|----------|------|-----------|
| **Gemini** | [Google AI Studio](https://aistudio.google.com/) | Free quota on `gemini-2.5-flash-lite` |
| **Grok** | [console.x.ai](https://console.x.ai/) | Free tier on `grok-3-mini` |
| **OpenRouter** | [openrouter.ai/keys](https://openrouter.ai/keys) | Free models (`:free` suffix) |
| **GitHub Models** | GitHub → Settings → Developer settings → PAT | Free with any GitHub account |
| **DeepSeek** | [platform.deepseek.com](https://platform.deepseek.com/) | Pay-as-you-go (very cheap) |

### 4. Run

```bash
# Windows:
run.bat

# Mac / Linux:
bash run.sh

# or directly:
python main.py
```

---

## Configuration (`secrets/.env` or `.env`)

```env
# --- Gemini (primary) ---
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.5-flash-lite

# --- Grok / xAI (fallback 1) ---
GROK_API_KEY=your_grok_key_here
GROK_MODEL=grok-3-mini

# --- OpenRouter (fallback 2, free models) ---
OPENROUTER_API_KEY=your_openrouter_key_here
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free

# --- GitHub Models (fallback 3) ---
GITHUB_TOKEN=your_github_token_here
GITHUB_MODEL=gpt-4o-mini

# --- DeepSeek (fallback 4) ---
DEEPSEEK_API_KEY=your_deepseek_key_here
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com

# --- Behavior ---
PROVIDER_ORDER=gemini,grok,openrouter,github,deepseek
PROVIDER_TIMEOUT=20
IDLE_TIMEOUT_SECONDS=35
```

Providers with missing or placeholder keys are silently skipped.

---

## Project Structure

```
wrisha.ai/
├── .env.example              # placeholder keys — safe to commit
├── .gitignore                # blocks .env, secrets/, .cache/, __pycache__/
├── config.py                 # loads all secrets from env (no hardcoded keys)
├── main.py                   # main orchestration loop
├── requirements.txt
├── run.bat                   # Windows launcher
├── run.sh                    # Mac/Linux launcher
│
├── modules/
│   ├── avatar.py             # Pygame animated HUD
│   ├── brain.py              # AI logic, uses provider layer
│   ├── hearing.py            # speech-to-text
│   ├── memory.py             # persistent JSON memory
│   ├── mood_engine.py        # smooth mood state machine
│   ├── vision.py             # webcam + emotion detection
│   └── voice.py              # Edge TTS (temp files → .cache/)
│
├── providers/                # multi-model fallback layer
│   ├── base.py               # BaseProvider interface
│   ├── manager.py            # ordered fallback logic
│   ├── gemini_provider.py    # google-genai SDK
│   ├── grok_provider.py      # openai SDK → api.x.ai
│   ├── openrouter_provider.py# openai SDK → openrouter.ai
│   ├── github_provider.py    # openai SDK → models.inference.ai.azure.com
│   └── deepseek_provider.py  # openai SDK → api.deepseek.com
│
├── tests/
│   ├── test_gemini.py        # verify Gemini key + model
│   └── test_api.py           # verify DeepSeek key + model
│
└── secrets/                  # gitignored — put .env here
    └── .gitignore
```

---

## Testing individual providers

```bash
# Gemini
python tests/test_gemini.py

# DeepSeek
python tests/test_api.py
```

---

## Security

- **All API keys** are loaded from environment variables via `python-dotenv`. No key ever touches a tracked file.
- `secrets/.env` and root `.env` are both gitignored.
- `config.py` defaults are all empty strings — not placeholder strings, not real keys.
- A pre-push check: run `git grep -i "AIza\|sk-\|gsk_\|github_pat\|sk-or-v1"` — it should return nothing.

> **Important:** If you previously had a key hardcoded in `config.py` and pushed it to a public repo, that key is permanently compromised regardless of deletion. Revoke it immediately at the provider's dashboard and generate a new one.
