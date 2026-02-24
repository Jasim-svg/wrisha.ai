"""
modules/memory.py — Persistent Long-Term Memory for Wrisha.AI v3.0

Stores and retrieves facts about the user across sessions.
Facts are saved to a JSON file and injected into every brain prompt,
giving Wrisha true long-term memory.
"""

import json
import os
import datetime
import config


class Memory:
    """
    Manages Wrisha's long-term, persistent memory about the user.

    Schema of wrisha_memory.json:
    {
        "user_name": null,
        "first_met": "2024-01-01T12:00:00",
        "last_seen": "2024-01-01T12:00:00",
        "total_sessions": 1,
        "facts": [
            "User likes coffee in the morning",
            "User's name is Alex",
            ...
        ]
    }
    """

    def __init__(self):
        self.filepath = config.MEMORY_FILE
        self.max_facts = config.MAX_MEMORY_FACTS
        self._data = self._load()
        # Update last seen
        self._data["last_seen"] = datetime.datetime.now().isoformat()
        self._data["total_sessions"] = self._data.get("total_sessions", 0) + 1
        self._save()

    # ─── Private Helpers ────────────────────────────────────────

    def _load(self) -> dict:
        """Load memory from disk, or create a fresh one."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                print(f"Memory: Loaded {len(data.get('facts', []))} facts from disk.")
                return data
            except (json.JSONDecodeError, IOError) as e:
                print(f"Memory: Could not load memory file ({e}). Starting fresh.")
        return {
            "user_name": None,
            "first_met": datetime.datetime.now().isoformat(),
            "last_seen": None,
            "total_sessions": 0,
            "facts": [],
        }

    def _save(self):
        """Persist current memory to disk."""
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Memory: Could not save memory ({e}).")

    # ─── Public API ─────────────────────────────────────────────

    @property
    def user_name(self) -> str | None:
        return self._data.get("user_name")

    @user_name.setter
    def user_name(self, name: str):
        self._data["user_name"] = name
        self._save()

    @property
    def facts(self) -> list[str]:
        return self._data.get("facts", [])

    @property
    def total_sessions(self) -> int:
        return self._data.get("total_sessions", 1)

    @property
    def first_met(self) -> str:
        return self._data.get("first_met", "unknown")

    def add_fact(self, fact: str):
        """Add a new fact. Trims to max_facts oldest entries."""
        fact = fact.strip()
        if not fact or fact in self._data["facts"]:
            return
        self._data["facts"].append(fact)
        # Trim to max
        if len(self._data["facts"]) > self.max_facts:
            self._data["facts"] = self._data["facts"][-self.max_facts:]
        self._save()
        print(f"Memory: Stored new fact → '{fact}'")

    def add_facts(self, facts: list[str]):
        for f in facts:
            self.add_fact(f)

    def get_prompt_block(self) -> str:
        """
        Returns a formatted memory block to inject into the Gemini system prompt.
        """
        lines = []
        if self.user_name:
            lines.append(f"The user's name is {self.user_name}.")
        lines.append(f"You have met the user {self.total_sessions} times.")
        if self._data.get("last_seen"):
            try:
                last = datetime.datetime.fromisoformat(self._data["last_seen"])
                delta = datetime.datetime.now() - last
                if delta.days > 0:
                    lines.append(f"You last spoke {delta.days} day(s) ago.")
                else:
                    lines.append("You spoke earlier today.")
            except Exception:
                pass
        if self.facts:
            lines.append("Things you remember about the user:")
            for i, fact in enumerate(self.facts[-10:], 1):   # last 10 facts
                lines.append(f"  {i}. {fact}")
        return "\n".join(lines) if lines else ""

    def extract_facts_from_text(self, text: str, gemini_chat) -> list[str]:
        """
        Asks Gemini to extract memorable facts from the user's message.
        Returns a list of concise fact strings (may be empty).
        """
        if not text or not gemini_chat:
            return []
        try:
            extraction_prompt = (
                f"Extract any personal facts about the user from this message that Wrisha should remember long-term. "
                f"Examples: name, job, hobbies, preferences, family, location. "
                f"Reply with a JSON list of short fact strings, or an empty list [] if nothing notable. "
                f"Message: \"{text}\""
            )
            resp = gemini_chat.send_message(extraction_prompt)
            raw = resp.text.strip()
            # Strip markdown code fences if present
            raw = raw.replace("```json", "").replace("```", "").strip()
            facts = json.loads(raw)
            if isinstance(facts, list):
                return [str(f) for f in facts if f]
        except Exception as e:
            print(f"Memory: Fact extraction error ({e})")
        return []
