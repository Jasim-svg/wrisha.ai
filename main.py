import sys
sys.stdout.reconfigure(encoding='utf-8')

import cv2
import threading
import queue
import time

import config  # loads .env on import
from modules.vision import VisionSystem
from modules.hearing import HearingSystem
from modules.brain import Brain
from modules.voice import VoiceSystem
from modules.avatar import Avatar
from modules.memory import Memory
from modules.mood_engine import MoodEngine
from providers.manager import ProviderManager


def hearing_worker(hearing_system, audio_queue, stop_event):
    while not stop_event.is_set():
        text = hearing_system.listen_and_transcribe()
        if text:
            audio_queue.put(text)
        time.sleep(0.1)


def main():
    print("Wrisha AI v3.0 — initializing...")

    avatar       = Avatar()
    avatar.draw()

    memory          = Memory()
    mood_engine     = MoodEngine()
    vision          = VisionSystem()
    hearing         = HearingSystem()
    provider_manager = ProviderManager()
    brain           = Brain(memory, mood_engine, provider_manager)
    voice           = VoiceSystem()

    voice.set_subtitle_callback(avatar.set_subtitle)

    if not provider_manager.any_available():
        print("WARNING: No API keys are set. Wrisha will run in fallback-text mode.")

    print("System active. Press 'q' in the Vision window to quit.")

    audio_queue  = queue.Queue()
    stop_event   = threading.Event()
    last_interaction = time.time()

    h_thread = threading.Thread(
        target=hearing_worker,
        args=(hearing, audio_queue, stop_event),
        daemon=True,
    )
    h_thread.start()

    running      = True
    user_emotion = "neutral"

    while running:
        # 1. Vision
        frame = vision.get_frame()
        vision_result = {}
        if frame is not None:
            vision_result = vision.analyze_face(frame)
            user_emotion  = vision_result.get("emotion", "neutral")
            cv2.imshow("Vision Input", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                running = False
        else:
            user_emotion = "neutral"

        # 2. Audio input
        user_text = None
        if not audio_queue.empty():
            user_text = audio_queue.get()
            print(f"User: {user_text}")

        # 3. Brain — respond to user speech
        if user_text:
            last_interaction = time.time()
            response_text, target_mood, should_exit = brain.process(user_text, user_emotion)

            if should_exit:
                voice.speak(response_text, "sad")
                while voice.is_busy():
                    avatar.update_expression("sad", is_speaking=True)
                    avatar.draw()
                    time.sleep(0.1)
                running = False
                break

            if response_text:
                voice.speak(response_text, mood_engine.current)

        # 4. Proactive / idle message
        elif (
            not voice.is_busy()
            and audio_queue.empty()
            and (time.time() - last_interaction) > config.IDLE_TIMEOUT_SECONDS
        ):
            text, mood = brain.proactive_message()
            voice.speak(text, mood)
            last_interaction = time.time()

        # 5. Avatar
        avatar.update_expression(
            emotion=mood_engine.current,
            is_speaking=voice.is_busy(),
            user_emotion=user_emotion,
            mood_emoji=mood_engine.get_mood_emoji(),
            face_detected=vision_result.get("face_detected", False),
            eye_contact=vision_result.get("eye_contact", False),
        )
        avatar.update_stats({"memory_facts": len(memory.facts)})

        if not avatar.draw():
            running = False

        time.sleep(0.01)

    # Cleanup
    print("Shutting down...")
    stop_event.set()
    vision.release()
    cv2.destroyAllWindows()
    avatar.quit()


if __name__ == "__main__":
    main()
