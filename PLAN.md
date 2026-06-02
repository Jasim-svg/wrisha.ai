# Wrisha.AI — Completion & Upgrade Spec

**Audience:** the coding agent implementing this.
**Repo:** `Jasim-svg/wrisha.ai` (Python desktop AI companion).
**Goal of this work order:** (1) make the app run again, (2) add a dual-provider brain (Gemini primary, DeepSeek fallback), (3) make it a clean, secrets-safe "live" project.

Read this whole document before writing code. Work phase by phase, in order. Do not skip Phase 0.

---

## 0. Context — what the project is and what's broken

Wrisha is a multimodal desktop AI companion (an anime-style character). The pipeline:

- `modules/vision.py` — webcam + facial-emotion detection (OpenCV / FER)
- `modules/hearing.py` — speech-to-text (SpeechRecognition)
- `modules/brain.py` — generates Wrisha's replies (currently Gemini-only)
- `modules/voice.py` — Edge TTS speech output, mood-modulated
- `modules/avatar.py` — animated pygame face that emotes + lip-syncs
- `modules/memory.py` — persistent JSON long-term memory
- `modules/mood_engine.py` — smooth mood-transition state machine

**The core bug:** the modules were upgraded to "v3" but `main.py` is still "v2" and is incompatible, so the app **crashes on startup**:

- `main.py` calls `Brain()` with no args, but `brain.py` now requires `Brain(memory, mood_engine)` → `TypeError: __init__() missing 2 required positional arguments`.
- `main.py` reads `brain.current_mood`, which no longer exists (mood now lives in `MoodEngine`).
- `main.py` never instantiates `Memory` or `MoodEngine`, and never uses `brain.proactive_message()` despite `config.IDLE_TIMEOUT_SECONDS` being defined.

So `memory.py`, `mood_engine.py`, and the proactive/idle feature are **built but not wired in**. Finishing that wiring is the baseline. The dual-provider brain is the upgrade.

**Capture the "before" first:** before changing anything, run the app and screenshot/record the startup `TypeError`. This is evidence for the project write-up. Then proceed.

---

## 1. Objectives (high level)

1. App launches and runs with no crashes.
2. Memory + smooth moods + proactive idle speech all work end to end.
3. Brain calls **Gemini first**, falls back to **DeepSeek** on any failure, with a safe canned reply if both fail.
4. **Zero secrets in the repo.** All keys live in `.env` (gitignored). A leaked key was committed in the past — this must never recur.
5. Repo is clean: no debug scripts, no committed audio temp files, tests organized, real README.

---

## 2. Hard constraints — do NOT break these

- **Do not change the public interfaces** of `vision.py`, `hearing.py`, `voice.py`, `avatar.py`. They are used by `main.py`. Their methods (see Appendix B) must keep working as-is. `voice.py` gets ONE small internal change (temp-file path) described in Phase 4 — nothing else.
- **Keep the `EMOTION|text` response contract.** Every brain reply is one line: a valid emotion, a `|`, then the text. `brain._parse_response()` already enforces this — keep it and make both providers feed into it.
- **Do not touch `assets/`** (avatar artwork).
- **Do not remove `memory.py` or `mood_engine.py`** — they are correct; wire them in, don't rewrite them (except the small `extract_facts_from_text` signature change in Phase 2).
- Target **Python 3.10+** (code already uses `X | None` type syntax).
- Preserve the persona config in `config.py` (PERSONA_*, VOICE_STYLES, VALID_EMOTIONS, etc.). Only the secret-handling parts of `config.py` change.

---

## 3. Target folder structure

```
wrisha.ai/
├── .env                      # REAL keys — gitignored, never committed
├── .env.example              # placeholder keys — committed, documents required vars
├── .gitignore                # NEW
├── README.md                 # NEW
├── PLAN.md                   # this file
├── requirements.txt          # UPDATED (add openai, python-dotenv)
├── run.bat                   # UPDATED
├── run.sh                    # NEW (optional, mac/linux)
├── config.py                 # UPDATED (loads secrets from env)
├── main.py                   # REWRITTEN (wires v3 modules + idle loop)
├── assets/                   # unchanged
├── modules/
│   ├── __init__.py
│   ├── avatar.py             # unchanged
│   ├── hearing.py            # unchanged
│   ├── vision.py             # unchanged
│   ├── voice.py              # 1 small change (temp path) — Phase 4
│   ├── memory.py             # 1 small change (extract signature) — Phase 2
│   ├── mood_engine.py        # unchanged
│   └── brain.py              # REFACTORED to use providers
├── providers/                # NEW — the multi-model layer
│   ├── __init__.py
│   ├── base.py               # Provider interface
│   ├── gemini_provider.py
│   ├── deepseek_provider.py
│   └── manager.py            # ordered fallback logic
├── tests/                    # NEW — moved test scripts live here
│   ├── test_api.py
│   └── test_gemini.py
└── .cache/                   # NEW, gitignored — runtime TTS temp files
```

**Delete from the repo entirely:** `debug_mp.py`, `debug_mp_2.py`, `verify_fix.py`, all root-level `speech_*.mp3`, `temp_speech.mp3`, and any committed `__pycache__/`.

---

## 4. Phase 0 — Security & secrets (DO THIS FIRST)

### 4.1 Rotate the leaked key (human step — flag this to the user, it cannot be skipped)
A Gemini key was committed to git history in the past. Deleting a key from a file does **not** un-leak it — anything ever pushed to a public repo is permanently compromised. The owner must:
- Go to Google AI Studio → revoke/delete the old Gemini key → generate a NEW one.
- Put the new key only in `.env` (never in tracked files).

Add a clear note in the README and PR description that the old key must be revoked.

### 4.2 `.gitignore` (create at repo root)
Must cover at least:
```
# secrets
.env
*.env
!.env.example

# python
__pycache__/
*.pyc
.venv/
venv/

# runtime artifacts
.cache/
speech_*.mp3
temp_speech.mp3
wrisha_memory.json

# os/editor
.DS_Store
.idea/
.vscode/
```
(`wrisha_memory.json` is per-user runtime data and should not be committed.)

### 4.3 `.env.example` (committed) and `.env` (gitignored)
`.env.example` documents every required variable with placeholder values:
```
# --- Gemini (primary) ---
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.0-flash

# --- DeepSeek (fallback) ---
DEEPSEEK_API_KEY=your_deepseek_key_here
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com

# --- Provider behavior ---
PROVIDER_ORDER=gemini,deepseek
PROVIDER_TIMEOUT=20
IDLE_TIMEOUT_SECONDS=35
```
`.env` is the real copy with real keys. It must be in `.gitignore`.

### 4.4 Refactor `config.py` to load from env
- At top of `config.py`: `from dotenv import load_dotenv; load_dotenv()` then read via `os.getenv(...)`.
- Replace the hardcoded `GEMINI_API_KEY` / `GEMINI_MODEL` literals with `os.getenv("GEMINI_API_KEY", "")` and `os.getenv("GEMINI_MODEL", "gemini-2.0-flash")`.
- Add: `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL` (default `deepseek-v4-flash`), `DEEPSEEK_BASE_URL` (default `https://api.deepseek.com`), `PROVIDER_ORDER` (default `"gemini,deepseek"`, parse to a list), `PROVIDER_TIMEOUT` (default `20`, int).
- Make `IDLE_TIMEOUT_SECONDS` read from env with the existing `35` default.
- **Never** put a real key as a default value.

### 4.5 (Recommended) prevent future leaks
- Add `gitleaks` or a simple pre-commit hook that blocks commits containing `AIza...`-style keys. Document it in the README. Optional but in keeping with "treat it like a live project."
- (Optional, advanced) scrubbing the old key from git history with `git filter-repo`/BFG is nice-to-have, but **rotation in 4.1 is the real fix** — do that regardless.

---

## 5. Phase 1 — Multi-provider brain layer

### 5.1 Dependencies
Add to `requirements.txt`: `openai>=1.0.0` (DeepSeek is OpenAI-API-compatible) and `python-dotenv>=1.0.0`. Keep `google-generativeai`.

### 5.2 Unified message format
All providers speak one internal format — OpenAI-style:
```python
messages = [
    {"role": "system",    "content": "..."},
    {"role": "user",      "content": "..."},
    {"role": "assistant", "content": "..."},
]
```
Each provider converts this to its own SDK's shape internally.

### 5.3 `providers/base.py`
```python
class BaseProvider:
    name: str = "base"
    def is_available(self) -> bool: ...        # True if its API key is configured
    def generate(self, messages: list[dict], timeout: int) -> str: ...
        # returns assistant text, or raises on failure
```

### 5.4 `providers/gemini_provider.py`
- Uses `google-generativeai`.
- Convert messages: pull the `system` entry into `system_instruction`; map `user`→`user`, `assistant`→`model`; build the `contents` list.
- `genai.configure(api_key=config.GEMINI_API_KEY)`, `GenerativeModel(config.GEMINI_MODEL, system_instruction=...)`, `.generate_content(contents)`, return `.text.strip()`.
- `is_available()` → key is non-empty and not a placeholder.
- Raise on empty/blocked response so the manager can fall through.

### 5.5 `providers/deepseek_provider.py`
- Uses the `openai` SDK pointed at DeepSeek:
```python
from openai import OpenAI
client = OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_BASE_URL)
resp = client.chat.completions.create(
    model=config.DEEPSEEK_MODEL,   # deepseek-v4-flash
    messages=messages,             # already OpenAI-shaped
    timeout=timeout,
)
return resp.choices[0].message.content.strip()
```
- `is_available()` → DeepSeek key present.
- Raise on empty response.

### 5.6 `providers/manager.py`
```python
class ProviderManager:
    def __init__(self):
        # build providers in config.PROVIDER_ORDER, keep only those is_available()
        self.last_provider = None
    def generate(self, messages, timeout=None) -> str:
        # try each provider in order:
        #   - on success with non-empty text: set self.last_provider, return text
        #   - on exception OR empty/whitespace text: log it, continue to next
        # if all fail: return ""  (Brain supplies a canned fallback line)
    def any_available(self) -> bool: ...
```
- Log which provider answered (e.g. `print(f"[brain] answered by {name}")`) — useful for the demo/write-up.
- A timeout or "Server Busy" from DeepSeek must be caught and treated as failure, not crash.

---

## 6. Phase 2 — Refactor `brain.py` to use the provider layer

Keep the persona, the system-prompt builder, the `EMOTION|text` parsing, name detection, history trimming, and `proactive_message()`. Change only **how text is generated**.

- `Brain.__init__(self, memory, mood_engine, provider_manager)`. (main.py will pass all three.) Keep backward-friendly: if `provider_manager` is None, construct a default one.
- Remove the Gemini-specific `start_chat` / `self.chat` stateful session. Instead, Brain maintains its own `messages` list:
  - index 0 = system prompt (rebuilt from `memory.get_prompt_block()` + `mood_engine.get_context_hint()` via the existing `_build_system_prompt`).
  - then the rolling window of prior user/assistant turns (respect `config.CONTEXT_WINDOW`).
- `process(user_text, user_emotion)`:
  1. Keep exit-word detection and the `[User looks <emotion>]` visual tag.
  2. Build `messages = [system] + history + [user turn]`.
  3. `content = provider_manager.generate(messages)`. If empty → use the existing fallback line (`"My thoughts got a little tangled…"`).
  4. `mood, text = self._parse_response(content)`; `mood_engine.set_target(mood)`.
  5. Run fact extraction (see below) and name detection; append turn to history; trim.
  6. Return `(text, mood, should_exit)`.
- **Mood lives in `mood_engine`, not Brain.** Anywhere old code referenced `brain.current_mood`, use `mood_engine.current`.

### Memory extraction refactor (small signature change in `memory.py`)
`memory.extract_facts_from_text` currently takes a Gemini `chat` object. Make it provider-agnostic:
```python
def extract_facts_from_text(self, text: str, generate_fn) -> list[str]:
    # generate_fn(messages: list[dict]) -> str
    # build a one-shot extraction prompt (system + user), call generate_fn,
    # strip ```json fences, json.loads, return list[str]
```
Brain calls it as `memory.extract_facts_from_text(user_text, provider_manager.generate)`. Keep it best-effort and wrapped in try/except so a failed extraction never breaks the reply.

---

## 7. Phase 3 — Rewrite `main.py` (wire everything + proactive idle loop)

Rewrite `main.py` so it:

1. Loads env (via importing `config`, which calls `load_dotenv()`).
2. Instantiates, in order: `Avatar`, `VisionSystem`, `HearingSystem`, `Memory`, `MoodEngine`, `ProviderManager`, then `Brain(memory, mood_engine, provider_manager)`, then `VoiceSystem`.
3. If `not provider_manager.any_available()`, print a clear warning that no API keys are set (app still runs in fallback-text mode — do not crash).
4. Keeps the existing threading model: a `hearing_worker` thread pushing transcripts to a `Queue`.
5. Main loop each frame:
   - Vision: `frame = vision.get_frame()`; if present, `emotion = vision.analyze_face(frame)["emotion"]`, show window, handle `q` to quit.
   - Pull `user_text` from the audio queue if any.
   - **If `user_text`:** reset `last_interaction = time.time()`; call `brain.process(user_text, emotion)`; if `should_exit`, speak the goodbye and break; else `voice.speak(text, mood)`.
   - **Proactive/idle:** if `provider/voice` not busy AND queue empty AND `time.time() - last_interaction > config.IDLE_TIMEOUT_SECONDS`: call `text, mood = brain.proactive_message()`, `voice.speak(text, mood)`, reset `last_interaction`.
   - Avatar: `avatar.update_expression(mood_engine.current, voice.is_busy())` then `avatar.draw()`.
   - Small `time.sleep(0.01)`.
6. Cleanup on exit: `stop_event.set()`, `vision.release()`, `cv2.destroyAllWindows()`, `avatar.quit()`.

No reference to `brain.current_mood` anywhere — always `mood_engine.current`.

---

## 8. Phase 4 — Repo hygiene

### 8.1 Stop polluting the repo with audio (`voice.py`, one change)
`voice.py` writes `speech_<ms>.mp3` into the current working directory. Change it to write into a dedicated cache dir:
- Create the dir once (e.g. `CACHE_DIR = ".cache"`, `os.makedirs(CACHE_DIR, exist_ok=True)`).
- `filename = os.path.join(CACHE_DIR, f"speech_{int(time.time()*1000)}.mp3")`.
- Update `_cleanup_old_files()` glob to `os.path.join(CACHE_DIR, "speech_*.mp3")`.
- `.cache/` is gitignored (Phase 0). Do not change any public method signatures.

### 8.2 Remove clutter (delete these files)
`debug_mp.py`, `debug_mp_2.py`, `verify_fix.py`, every root `speech_*.mp3`, `temp_speech.mp3`, committed `__pycache__/`.

### 8.3 Organize tests
Move `test_api.py` and `test_gemini.py` into `tests/`. Update them to read keys from env (no hardcoded keys). Add a `tests/__init__.py` if needed.

---

## 9. Phase 5 — requirements, run scripts, README

### 9.1 `requirements.txt`
Add `openai>=1.0.0` and `python-dotenv>=1.0.0`. Keep existing deps (opencv-python, pygame, SpeechRecognition, pyaudio, numpy, google-generativeai, edge-tts, requests, pillow, fer, tensorflow).

### 9.2 Run scripts
- `run.bat`: before launching, ensure it does not require a hardcoded key; it just runs `python main.py` (venv-aware as now). Add a check that `.env` exists and print a friendly message pointing to `.env.example` if not.
- Add `run.sh` (mac/linux equivalent), `chmod +x`.

### 9.3 `README.md`
Include: one-line description + a demo GIF placeholder, feature list (vision/hearing/brain/voice/avatar/memory/proactive), the dual-provider design (Gemini → DeepSeek fallback) with a small diagram or bullet flow, setup steps (`pip install -r requirements.txt`, copy `.env.example` → `.env`, add keys, `python main.py`), where to get free keys (Google AI Studio for Gemini; DeepSeek platform for the free-credit grant), and a **security note** that keys go in `.env` only and the old leaked key must be rotated.

---

## 10. Definition of Done (acceptance criteria — all must pass)

- [ ] App launches with no exceptions (the v2/v3 `TypeError` is gone).
- [ ] No secret values anywhere in tracked files; `git grep -i "AIza"` and a scan of `config.py` find nothing. `.env` is gitignored; `.env.example` is committed with placeholders.
- [ ] With only `GEMINI_API_KEY` set → Wrisha replies (Gemini path).
- [ ] With Gemini key removed/invalid but `DEEPSEEK_API_KEY` set → Wrisha still replies (fallback proven), and the log shows DeepSeek answered.
- [ ] With NO keys set → app still runs and shows the graceful fallback text, no crash.
- [ ] Memory persists across restarts: tell Wrisha your name, quit, relaunch, she recalls it (verified in `wrisha_memory.json` + her greeting).
- [ ] After `IDLE_TIMEOUT_SECONDS` of silence, Wrisha speaks unprompted (proactive message fires).
- [ ] Avatar mood follows `mood_engine.current` and animates while speaking.
- [ ] Repo contains no `debug_*.py`, no `verify_fix.py`, no committed `speech_*.mp3`/`temp_speech.mp3`, no committed `__pycache__/`; tests live in `tests/`.
- [ ] New runtime `.mp3` files are created in `.cache/`, not the repo root.
- [ ] `README.md` exists with setup + security notes.

---

## 11. Suggested commit sequence (small, reviewable PRs/commits)

1. `chore(security): add .gitignore, .env.example, load secrets from env` (Phase 0)
2. `feat(providers): add Gemini+DeepSeek provider layer with fallback` (Phase 1)
3. `refactor(brain): use provider manager; provider-agnostic memory extraction` (Phase 2)
4. `fix(main): wire memory + mood engine + proactive idle loop (app runs again)` (Phase 3)
5. `chore: move TTS temp files to .cache; remove debug/test clutter` (Phase 4)
6. `docs: README, run scripts, requirements` (Phase 5)

After each phase, run the app and confirm against the relevant acceptance criteria before moving on.

---

## Appendix A — Verified provider facts (as of mid-2026; confirm at build time)

- **DeepSeek API is OpenAI-compatible** — use the `openai` Python SDK with `base_url="https://api.deepseek.com"`. It also offers an Anthropic-compatible endpoint; we use the OpenAI one.
- **Current model:** `deepseek-v4-flash` (and `deepseek-v4-pro`). The older `deepseek-chat` / `deepseek-reasoner` aliases still work but are scheduled for deprecation around 2026-07-24 — use `deepseek-v4-flash` for new code.
- **DeepSeek free access:** new developer accounts receive a one-time grant of roughly 5M free tokens (a granted balance, not a perpetual monthly free tier). Treat it as evaluation/fallback budget; after it's used, billing is pay-as-you-go (cheap). The direct API can throttle ("Server Busy") at peak — exactly why it sits behind Gemini as the fallback.
- **Gemini free tier:** accessed via `google-generativeai`. Use a current free-tier flash model (default here `gemini-2.0-flash`); confirm the exact available free model in Google AI Studio at build time and set `GEMINI_MODEL` accordingly.
- **Keys:** Gemini from Google AI Studio; DeepSeek from the DeepSeek developer platform. Both go in `.env` only.

## Appendix B — Existing module interfaces (must keep working)

- `VisionSystem`: `get_frame()`, `analyze_face(frame) -> {"emotion": str, ...}`, `release()`
- `HearingSystem`: `listen_and_transcribe() -> str | None`
- `VoiceSystem`: `speak(text: str, mood: str = "neutral")`, `is_busy() -> bool`, `stop()`, `set_subtitle_callback(fn)`, `subtitle` (property)
- `Avatar`: `draw() -> bool`, `update_expression(mood: str, is_speaking: bool)`, `quit()`
- `Memory`: `user_name` (get/set), `facts`, `total_sessions`, `first_met`, `add_fact`, `add_facts`, `get_prompt_block()`, `extract_facts_from_text(text, generate_fn)` ← signature updated in Phase 2
- `MoodEngine`: `current`, `target`, `blend`, `display_mood`, `history`, `set_target(mood, force=False)`, `get_mood_emoji()`, `get_context_hint()`
- `Brain`: `__init__(memory, mood_engine, provider_manager)`, `process(user_text, user_emotion) -> (text, mood, should_exit)`, `proactive_message() -> (text, mood)`, `_parse_response(content) -> (mood, text)` (keep)
