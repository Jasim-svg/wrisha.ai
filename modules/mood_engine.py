"""
modules/mood_engine.py — Smooth Mood Transition Engine for Wrisha.AI v3.0

Prevents jarring instant mood snaps by blending between mood states
over multiple frames. Provides the avatar with smooth interpolated values.
"""

import time
import config


# Priority of moods (higher = stronger — overrides lower in conflicts)
MOOD_PRIORITY = {
    "angry":    8,
    "excited":  7,
    "sad":      6,
    "loving":   5,
    "curious":  4,
    "shy":      4,
    "happy":    3,
    "peaceful": 2,
    "neutral":  1,
    "talking":  0,  # Not a base mood; overlaid when speaking
}

# How quickly (seconds) a mood fades to the next one
TRANSITION_SPEED = 1.5   # seconds for a full blend


class MoodEngine:
    """
    Manages smooth mood transitions between discrete mood states.

    Usage:
        engine = MoodEngine()
        engine.set_target("excited")
        current = engine.current   # string, blends toward target over time
        blend   = engine.blend     # 0.0 → 1.0 progress toward target
    """

    def __init__(self, initial_mood: str = "peaceful"):
        self._current     = initial_mood
        self._target      = initial_mood
        self._blend       = 1.0           # 1.0 = fully in target
        self._change_time = time.time()
        self._history     = [initial_mood]

    # ─── Properties ─────────────────────────────────────────────

    @property
    def current(self) -> str:
        """The mood we're currently blending FROM (display this for avatar)."""
        self._tick()
        if self._blend >= 0.5:
            return self._target
        return self._current

    @property
    def target(self) -> str:
        return self._target

    @property
    def blend(self) -> float:
        """0.0 = fully in previous mood, 1.0 = fully in target mood."""
        self._tick()
        return self._blend

    @property
    def display_mood(self) -> str:
        """Best mood string to use for UI / avatar rendering."""
        return self.current

    @property
    def history(self) -> list[str]:
        return list(self._history[-10:])

    # ─── Public API ─────────────────────────────────────────────

    def set_target(self, mood: str, force: bool = False):
        """
        Request a mood change.  If `force=True`, snap immediately.
        Otherwise, smoothly blend over TRANSITION_SPEED seconds.
        """
        mood = mood.lower().strip()
        # Validate
        if mood not in config.VALID_EMOTIONS:
            mood = "neutral"
        if mood == self._target and not force:
            return

        if force:
            self._current = mood
            self._target  = mood
            self._blend   = 1.0
        else:
            self._current     = self.current   # freeze current display state
            self._target      = mood
            self._blend       = 0.0
            self._change_time = time.time()

        self._history.append(mood)
        if len(self._history) > 50:
            self._history = self._history[-50:]

    def get_mood_emoji(self) -> str:
        """Returns an emoji matching the current mood for the HUD."""
        mapping = {
            "happy":    "😊",
            "sad":      "😢",
            "excited":  "🤩",
            "curious":  "🤔",
            "shy":      "🥺",
            "angry":    "😤",
            "loving":   "🥰",
            "peaceful": "😌",
            "neutral":  "😐",
            "talking":  "💬",
        }
        return mapping.get(self.current, "😊")

    def get_context_hint(self) -> str:
        """Short string describing mood context for brain prompt."""
        recent = [m for m in self.history[-5:] if m not in ("neutral", "talking")]
        if recent:
            return f"Your recent mood trajectory: {' → '.join(recent)}."
        return ""

    # ─── Internal ───────────────────────────────────────────────

    def _tick(self):
        """Update blend progress based on elapsed time."""
        if self._blend >= 1.0:
            return
        elapsed = time.time() - self._change_time
        self._blend = min(1.0, elapsed / TRANSITION_SPEED)
