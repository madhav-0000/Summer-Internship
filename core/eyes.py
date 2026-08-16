import time
import numpy as np

class EyeTracker:
    """
    Calculates Eye Aspect Ratio (EAR) and determines if eyes are closed.
    Uses real-time duration (seconds) instead of frame counts so the closure
    threshold is accurate at any camera FPS.
    """
    # MediaPipe Face Mesh landmark indices for eyes
    # Left eye: 33 (left corner), 160, 158 (top), 133 (right corner), 153, 144 (bottom)
    # Right eye: 362 (left corner), 385, 387 (top), 263 (right corner), 373, 380 (bottom)
    LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]

    def __init__(self, ear_threshold=0.25, ear_frames=15, closure_duration_seconds=1):
        self.ear_threshold = ear_threshold
        self.ear_frames = ear_frames  # Kept for backward compatibility (not used for timing)
        self.closure_duration_seconds = closure_duration_seconds  # Real-time closure window
        self.closure_frames = 0       # Still tracked (used by main.py reset logic)
        self.alarm_on = False
        self._event_fired = False     # Tracks whether the rising-edge event has been reported
        self._closure_start = None    # Timestamp when eyes first closed below threshold

    def get_eye_landmarks(self, face_landmarks, frame_w, frame_h, indices):
        """Extracts (x, y) pixel coordinates for the specified landmarks."""
        coords = []
        for i in indices:
            lm = face_landmarks.landmark[i]
            x, y = int(lm.x * frame_w), int(lm.y * frame_h)
            coords.append(np.array([x, y]))
        return coords

    def calculate_ear(self, eye_coords):
        """Computes the Eye Aspect Ratio given 6 coordinate points."""
        v1 = np.linalg.norm(eye_coords[1] - eye_coords[5])
        v2 = np.linalg.norm(eye_coords[2] - eye_coords[4])
        h = np.linalg.norm(eye_coords[0] - eye_coords[3])
        # Avoid division by zero
        if h == 0:
            h = 1e-6
        return (v1 + v2) / (2.0 * h)

    def process(self, face_landmarks, frame_w, frame_h):
        """
        Calculates the average EAR for both eyes and updates closure state.

        Returns (ear, is_closure_event, is_closure_ongoing).

        is_closure_event:   True on the single frame when continuous eye closure
                            first exceeds closure_duration_seconds (rising edge — fires once per closure).
        is_closure_ongoing: True while eyes remain closed after the event was logged.
        """
        left_eye = self.get_eye_landmarks(face_landmarks, frame_w, frame_h, self.LEFT_EYE_INDICES)
        right_eye = self.get_eye_landmarks(face_landmarks, frame_w, frame_h, self.RIGHT_EYE_INDICES)

        left_ear = self.calculate_ear(left_eye)
        right_ear = self.calculate_ear(right_eye)

        avg_ear = (left_ear + right_ear) / 2.0

        is_closure_event = False
        is_closure_ongoing = False

        if avg_ear < self.ear_threshold:
            self.closure_frames += 1  # Still count frames for external reset logic
            now = time.time()
            if self._closure_start is None:
                self._closure_start = now  # Eyes just closed — start the clock
            elapsed = now - self._closure_start
            if elapsed >= self.closure_duration_seconds:
                is_closure_ongoing = True
                if not self._event_fired:
                    is_closure_event = True
                    self._event_fired = True
        else:
            # Eyes are open — reset everything
            self.closure_frames = 0
            self._closure_start = None
            self._event_fired = False

        return avg_ear, is_closure_event, is_closure_ongoing
