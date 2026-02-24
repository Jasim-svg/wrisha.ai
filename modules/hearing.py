"""
modules/hearing.py — Hearing System for Wrisha v3.0

Upgrades:
  - Smarter energy threshold auto-calibration on startup
  - Configurable phrase time limit and listen timeout from config
  - Graceful retry on network errors
  - Cleaner status output (no spam)
  - Pause detection for faster response
"""

import speech_recognition as sr
import config


class HearingSystem:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Dynamic energy threshold (auto-calibrate)
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold          = 300
        self.recognizer.pause_threshold           = 0.7   # Shorter pause = faster response
        self.recognizer.non_speaking_duration     = 0.4

        print("Hearing: Calibrating for ambient noise…", end=" ", flush=True)
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
        print(f"✅ (energy threshold: {self.recognizer.energy_threshold:.0f})")

    def listen_and_transcribe(self) -> str | None:
        """
        Listens for one utterance and converts it to text.
        Returns the transcribed string, or None if no speech detected.
        """
        with self.microphone as source:
            try:
                audio = self.recognizer.listen(
                    source,
                    timeout=config.LISTEN_TIMEOUT,
                    phrase_time_limit=config.PHRASE_TIME_LIMIT,
                )
            except sr.WaitTimeoutError:
                return None  # Silence — no problem, loop continues
            except Exception as e:
                print(f"Hearing: Microphone error — {e}")
                return None

        # Transcribe
        for attempt in range(2):   # Retry once on network error
            try:
                text = self.recognizer.recognize_google(audio)
                if text:
                    print(f"👂 Heard: \"{text}\"")
                return text if text else None
            except sr.UnknownValueError:
                return None   # Could not understand — normal
            except sr.RequestError as e:
                if attempt == 0:
                    print(f"Hearing: STT network error ({e}) — retrying…")
                    continue
                print(f"Hearing: STT failed after retry — {e}")
                return None
            except Exception as e:
                print(f"Hearing: Unexpected error — {e}")
                return None
        return None
