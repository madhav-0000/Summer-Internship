import time
import numpy as np

class MouthTracker:
    """
    Calculates Mouth Aspect Ratio (MAR) and determines if the driver is yawning.

    Uses real-time duration so a yawn must be held continuously for at least
    `yawn_duration_seconds` before it's counted as a drowsy yawn event.
    Short mouth-opens (talking, coughing, sneezing) are naturally filtered out.
    """
    # MediaPipe Face Mesh landmark indices for inner lips
    # Left corner: 78, Right corner: 308
    # Top: 13, Bottom: 14
    INNER_LIP_INDICES = [78, 13, 308, 14]

    def __init__(self, mar_threshold=0.6, mar_frames=15, yawn_duration_seconds=1.0):
        self.mar_threshold = mar_threshold
        self.mar_frames = mar_frames          # Kept for backward-compatibility (not used for timing)
        self.yawn_duration_seconds = yawn_duration_seconds  # Minimum continuous open-mouth time
        self.yawn_frames = 0                  # Still tracked (used by main.py reset logic)
        self.alarm_on = False
        self._event_fired = False             # Tracks whether the rising-edge event has been reported
        self._yawn_start = None              # Timestamp when mouth first opened above threshold

    def get_mouth_landmarks(self, face_landmarks, frame_w, frame_h):
        coords = []
        for i in self.INNER_LIP_INDICES:
            lm = face_landmarks.landmark[i]
            x, y = int(lm.x * frame_w), int(lm.y * frame_h)
            coords.append(np.array([x, y]))
        return coords

    def calculate_mar(self, mouth_coords):
        """
        Computes the Mouth Aspect Ratio.
        mouth_coords: [left_corner, top, right_corner, bottom]
        """
        # Vertical distance
        v = np.linalg.norm(mouth_coords[1] - mouth_coords[3])
        # Horizontal distance
        h = np.linalg.norm(mouth_coords[0] - mouth_coords[2])
        if h == 0:
            h = 1e-6
        return v / h

    def process(self, face_landmarks, frame_w, frame_h):
        """
        Returns (mar, is_yawn_event, is_yawn_ongoing).

        is_yawn_event:   True on the single frame when the yawn first exceeds
                         yawn_duration_seconds (rising edge — fires once per yawn).
        is_yawn_ongoing: True while the yawn continues after the event was logged.

        Short mouth-opens under yawn_duration_seconds are ignored entirely.
        """
        mouth_coords = self.get_mouth_landmarks(face_landmarks, frame_w, frame_h)
        mar = self.calculate_mar(mouth_coords)

        is_yawn_event = False
        is_yawn_ongoing = False

        if mar > self.mar_threshold:
            self.yawn_frames += 1  # Still counted for external reset logic
            now = time.time()
            if self._yawn_start is None:
                self._yawn_start = now  # Mouth just opened — start timing
            elapsed = now - self._yawn_start
            if elapsed >= self.yawn_duration_seconds:
                is_yawn_ongoing = True
                if not self._event_fired:
                    is_yawn_event = True  # Rising edge: this yawn has now qualified
                    self._event_fired = True
        else:
            # Mouth closed — reset everything
            self.yawn_frames = 0
            self._yawn_start = None
            self._event_fired = False

        return mar, is_yawn_event, is_yawn_ongoing
