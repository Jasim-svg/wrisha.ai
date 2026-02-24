"""
modules/voice.py — Voice System for Wrisha v3.0

Upgrades:
  - Emotion-modulated TTS: different rate/pitch per mood via SSML
  - Auto-cleanup of old speech_*.mp3 files on startup + after playback
  - Subtitle callback so avatar can display what's being said
  - Thread-safe: generates in thread, plays non-blocking
"""

import edge_tts
import asyncio
import pygame
import os
import glob
import time
import threading
import config


class VoiceSystem:
    def __init__(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self._current_file    = None
        self._subtitle_text   = ""
        self._subtitle_cb     = None       # Optional callback: fn(text)
        self._lock            = threading.Lock()

        # Clean up leftover speech files from previous sessions
        self._cleanup_old_files()
        print("Voice: ✅ Edge TTS ready")

    # ─── Public API ──────────────────────────────────────────────

    def set_subtitle_callback(self, fn):
        """Register a function to be called with the current subtitle text."""
        self._subtitle_cb = fn

    def speak(self, text: str, mood: str = "neutral"):
        """Non-blocking: generates TTS in background and plays."""
        if not text:
            return
        t = threading.Thread(target=self._speak_worker, args=(text, mood), daemon=True)
        t.start()

    def is_busy(self) -> bool:
        return pygame.mixer.music.get_busy()

    def stop(self):
        pygame.mixer.music.stop()
        self._subtitle_text = ""
        if self._subtitle_cb:
            self._subtitle_cb("")

    @property
    def subtitle(self) -> str:
        return self._subtitle_text

    # ─── Internal ────────────────────────────────────────────────

    def _speak_worker(self, text: str, mood: str):
        voice, rate, pitch = self._get_voice_style(mood)
        filename = f"speech_{int(time.time() * 1000)}.mp3"

        # Generate audio
        try:
            asyncio.run(self._generate_audio(text, filename, voice, rate, pitch))
        except Exception as e:
            print(f"Voice: TTS generation error — {e}")
            return

        # Set subtitle before playing
        self._subtitle_text = text
        if self._subtitle_cb:
            self._subtitle_cb(text)

        # Wait for any current audio to finish gracefully
        timeout = time.time() + 8
        while self.is_busy() and time.time() < timeout:
            time.sleep(0.05)

        # Play
        with self._lock:
            try:
                old_file = self._current_file
                pygame.mixer.music.unload()
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()
                self._current_file = filename

                # Schedule deletion of old file
                if old_file and os.path.exists(old_file):
                    threading.Thread(
                        target=self._delayed_delete, args=(old_file, 5), daemon=True
                    ).start()

            except Exception as e:
                print(f"Voice: Playback error — {e}")

        # Clear subtitle after speech ends
        def _clear_sub():
            while self.is_busy():
                time.sleep(0.1)
            self._subtitle_text = ""
            if self._subtitle_cb:
                self._subtitle_cb("")

        threading.Thread(target=_clear_sub, daemon=True).start()

    async def _generate_audio(self, text: str, filename: str,
                               voice: str, rate: str, pitch: str):
        communicate = edge_tts.Communicate(
            text, voice, rate=rate, pitch=pitch
        )
        await communicate.save(filename)

    def _get_voice_style(self, mood: str) -> tuple[str, str, str]:
        """Return (voice_name, rate, pitch) for mood."""
        styles = config.VOICE_STYLES
        entry  = styles.get(mood, styles["default"])
        return entry  # (voice, rate, pitch)

    def _cleanup_old_files(self):
        """Delete all speech_*.mp3 files left from previous runs."""
        old_files = glob.glob("speech_*.mp3")
        for f in old_files:
            try:
                os.remove(f)
            except OSError:
                pass
        if old_files:
            print(f"Voice: Cleaned up {len(old_files)} old speech file(s)")

    @staticmethod
    def _delayed_delete(filepath: str, delay_seconds: float):
        """Delete a file after a delay (gives pygame time to release handle)."""
        time.sleep(delay_seconds)
        try:
            os.remove(filepath)
        except OSError:
            pass
