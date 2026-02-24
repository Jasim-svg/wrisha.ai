import cv2
import threading
import queue
import time
import os

from modules.vision import VisionSystem
from modules.hearing import HearingSystem
from modules.brain import Brain
from modules.voice import VoiceSystem
from modules.avatar import Avatar

def hearing_worker(hearing_system, audio_queue, stop_event):
    while not stop_event.is_set():
        text = hearing_system.listen_and_transcribe()
        if text:
            audio_queue.put(text)
        time.sleep(0.1)

def main():
    print("Version 2.0 Initaizing...")
    
    avatar = Avatar()
    avatar.draw() # Show initial screen
    
    vision = VisionSystem()
    hearing = HearingSystem()
    brain = Brain() # Connects to Gemini
    voice = VoiceSystem() # Connects to Edge TTS
    
    print("System active. Press 'q' in Vision window to quit.")
    
    audio_queue = queue.Queue()
    stop_event = threading.Event()
    
    h_thread = threading.Thread(target=hearing_worker, args=(hearing, audio_queue, stop_event))
    h_thread.daemon = True
    h_thread.start()
    
    running = True
    
    while running:
        # 1. Vision Update
        frame = vision.get_frame()
        if frame is not None:
            vision_result = vision.analyze_face(frame)
            user_emotion = vision_result.get("emotion", "neutral")
            
            # Show debug view
            cv2.imshow("Vision Input", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                running = False
        else:
            user_emotion = "neutral"

        # 2. Check Audio Input
        user_text = None
        if not audio_queue.empty():
            user_text = audio_queue.get()
            print(f"User: {user_text}")

        # 3. Brain Processing
        # Only process if we have input OR meaningful change?
        # To avoid spamming Gemini, we only call process if there is text.
        # But V1 had emotion-only triggers.
        # For V2 with API cost/limits (even free tier has limits), let's strictly reply to TEXT 
        # OR if emotion is heavily sustained (not implemented). 
        # Let's stick to Text triggers for the Brain to be safe, plus occasional random?
        # Actually, let's keep the logic simple: verify if brain wants to react.
        
        response_text = ""
        target_mood = brain.current_mood
        should_exit = False
        
        if user_text:
             response_text, target_mood, should_exit = brain.process(user_text, user_emotion)
        
        if should_exit:
            voice.speak(response_text)
            # Wait for speech to finish before closing?
            while voice.is_busy():
                avatar.update_expression("sad", is_speaking=True)
                avatar.draw()
                time.sleep(0.1)
            running = False
            break

        # 4. Voice Output Trigger
        if response_text:
            voice.speak(response_text)
            # We do NOT block here. We let the loop continue so avatar animates.
        
        # 5. Avatar Update Logic
        # Check if speaking
        is_speaking = voice.is_busy()
        
        # Update Avatar
        # Use brain's current mood, unless we are speaking, then maybe we override?
        # Brain.process updates self.current_mood.
        avatar.update_expression(brain.current_mood, is_speaking)
        
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
