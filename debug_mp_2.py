import mediapipe as mp
import sys

print(f"Python version: {sys.version}")

try:
    import mediapipe.python.solutions as solutions
    print("Success! Imported mediapipe.python.solutions")
    print(f"Face mesh available? {hasattr(solutions, 'face_mesh')}")
except ImportError as e:
    print(f"Failed to import mediapipe.python.solutions: {e}")

try:
    from mediapipe.python.solutions import face_mesh
    print("Success! Imported face_mesh directly")
except ImportError as e:
    print(f"Failed to import face_mesh directly: {e}")
