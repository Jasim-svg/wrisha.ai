"""
modules/vision.py — Vision System for Wrisha v3.0

Upgrades:
  - Real facial emotion detection using FER library
  - Eye-contact estimation
  - Face distance / proximity detection (shy response trigger)
  - Temporal emotion smoothing (no flicker)
  - Rich HUD overlay on debug window
"""

import cv2
import numpy as np
import time
import config

# Try importing FER; gracefully fall back to Haar-only if unavailable
try:
    from fer import FER
    _FER_AVAILABLE = True
    print("Vision: ✅ FER (Facial Expression Recognition) loaded")
except ImportError:
    _FER_AVAILABLE = False
    print("Vision: ⚠ FER not available — install 'fer' + 'tensorflow' for real emotion detection")


# Mapping FER labels → Wrisha emotion set
_FER_TO_WRISHA = {
    "happy":    "happy",
    "sad":      "sad",
    "angry":    "angry",
    "surprised":"excited",
    "fear":     "shy",
    "disgust":  "angry",
    "neutral":  "neutral",
}


class VisionSystem:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Vision: ⚠ Webcam not available — emotion detection disabled")

        # Haar cascade (always available as fallback)
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        # FER detector
        self.fer_detector = FER(mtcnn=False) if _FER_AVAILABLE else None

        # Temporal smoothing buffer
        self._emotion_buffer  = ["neutral"] * config.EMOTION_SMOOTH_FRAMES
        self._last_emotion    = "neutral"
        self._face_detected   = False
        self._face_proximity  = 0.0    # 0.0 (far) → 1.0 (very close)
        self._eye_contact     = False
        self._fps             = 0.0
        self._last_time       = time.time()

    # ─── Frame Capture ───────────────────────────────────────────

    def get_frame(self):
        if not self.cap.isOpened():
            return None
        success, frame = self.cap.read()
        if not success:
            return None
        return cv2.flip(frame, 1)   # Mirror

    # ─── Analysis ────────────────────────────────────────────────

    def analyze_face(self, frame) -> dict:
        """
        Detects face and emotion. Returns rich result dict.
        """
        if frame is None:
            return self._empty_result()

        # FPS tracking
        now  = time.time()
        self._fps = 1.0 / max(now - self._last_time, 0.001)
        self._last_time = now

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = frame.shape[:2]

        # ── Face detection (Haar) ─────────────────────────────────
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )
        self._face_detected = len(faces) > 0

        raw_emotion = "neutral"
        confidence  = 0.0

        if self._face_detected:
            x, y, fw, fh = faces[0]

            # Proximity (face width relative to frame)
            self._face_proximity = fw / w

            # Eye contact heuristic: face is roughly centered horizontally
            face_center_x = x + fw / 2
            self._eye_contact = abs(face_center_x - w / 2) < (w * 0.15)

            # ── FER emotion detection ─────────────────────────────
            if self.fer_detector is not None:
                try:
                    face_roi = frame[y:y+fh, x:x+fw]
                    result   = self.fer_detector.detect_emotions(face_roi)
                    if result:
                        emotions   = result[0]["emotions"]
                        top_label  = max(emotions, key=emotions.get)
                        confidence = emotions[top_label]
                        raw_emotion = _FER_TO_WRISHA.get(top_label, "neutral")
                except Exception:
                    raw_emotion = "listening"
            else:
                raw_emotion = "happy" if self._face_proximity > 0.15 else "neutral"
                confidence  = 0.8

            # Draw HUD on frame
            self._draw_hud(frame, faces[0], raw_emotion, confidence)

        # ── Temporal smoothing ─────────────────────────────────────
        self._emotion_buffer.pop(0)
        self._emotion_buffer.append(raw_emotion)
        # Most common in buffer
        from collections import Counter
        smoothed = Counter(self._emotion_buffer).most_common(1)[0][0]
        self._last_emotion = smoothed

        # Close-proximity trigger → shy
        if self._face_proximity > config.FACE_CLOSE_THRESHOLD:
            smoothed = "shy"

        return {
            "emotion":       smoothed,
            "raw_emotion":   raw_emotion,
            "confidence":    round(confidence, 2),
            "face_detected": self._face_detected,
            "eye_contact":   self._eye_contact,
            "proximity":     round(self._face_proximity, 2),
        }

    # ─── HUD Rendering ──────────────────────────────────────────

    def _draw_hud(self, frame, face_rect, emotion: str, conf: float):
        x, y, fw, fh = face_rect
        h, w = frame.shape[:2]

        # Face bounding box
        color = (0, 220, 130)
        cv2.rectangle(frame, (x, y), (x+fw, y+fh), color, 2)

        # Emotion label above box
        label = f"{emotion.upper()} {conf*100:.0f}%"
        cv2.putText(frame, label, (x, max(y-10, 15)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Eye contact indicator
        ec_color = (0, 255, 0) if self._eye_contact else (0, 120, 255)
        ec_label = "EYE CONTACT" if self._eye_contact else "LOOKING AWAY"
        cv2.putText(frame, ec_label, (10, h - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, ec_color, 2)

        # FPS
        cv2.putText(frame, f"FPS: {self._fps:.1f}", (w - 110, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

        # Proximity bar
        bar_w  = int(self._face_proximity * w * 2)
        bar_w  = min(bar_w, w - 20)
        cv2.rectangle(frame, (10, h - 20), (10 + bar_w, h - 10), (130, 0, 220), -1)
        cv2.putText(frame, "PROXIMITY", (10, h - 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 150, 255), 1)

    def _empty_result(self):
        return {
            "emotion": "neutral", "raw_emotion": "neutral",
            "confidence": 0.0, "face_detected": False,
            "eye_contact": False, "proximity": 0.0,
        }

    def release(self):
        if self.cap.isOpened():
            self.cap.release()
