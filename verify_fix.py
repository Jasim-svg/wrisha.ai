import sys
import cv2

try:
    from modules.vision import VisionSystem
    print(f"VisionSystem imported successfully.")
    
    v = VisionSystem()
    print("VisionSystem instantiated.")
    
    print(f"Haar Cascade loaded: {not v.face_cascade.empty()}")
    
    v.release()
    print("Verification passed.")
    
except Exception as e:
    print(f"Verification FAILED: {e}")
    import traceback
    traceback.print_exc()
