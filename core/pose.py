import time
import numpy as np

class HeadPoseEstimator:
    """
    Estimates head pitch (up/down movement) to detect nodding off (drooping).

    Uses three facial landmarks to compute a pitch ratio:
        pitch_ratio = d_bottom / d_top
    where:
        d_top    = vertical distance from top-of-head landmark to nose tip
        d_bottom = vertical distance from nose tip to chin

    When the head droops forward (drowsy nod), d_top increases and d_bottom
    decreases, so pitch_ratio FALLS. A reading below pitch_threshold for a
    sustained period triggers the nod event.

    Uses real-time duration (seconds) instead of frame counts so the detection
    window is accurate at any camera FPS.
    """
    # MediaPipe Face Mesh landmarks for head pitch estimation
    TOP_OF_HEAD = 10
    NOSE_TIP = 1
    CHIN = 152

    def __init__(self, pitch_threshold=0.6, pitch_frames=20, droop_duration_seconds=1.5):
        self.pitch_threshold = pitch_threshold
        self.pitch_frames = pitch_frames           # Kept for backward-compatibility (not used for timing)
        self.droop_duration_seconds = droop_duration_seconds  # Sustained droop time to confirm nod
        self.droop_frames = 0                      # Still counted for external reset logic
        self.alarm_on = False
        self._event_fired = False                  # Tracks whether the rising-edge event has been reported
        self._droop_start = None                   # Timestamp when head first drooped below threshold

    def process(self, face_landmarks, frame_w, frame_h):
        """
        Estimates head pitch and detects nodding off.

        Returns (pitch_ratio, is_nod_event, is_nod_ongoing).

        is_nod_event:   True on the single frame when sustained drooping first
                        exceeds droop_duration_seconds (rising edge — fires once per nod).
        is_nod_ongoing: True while the head remains drooped after the event was logged.
        """
        top  = face_landmarks.landmark[self.TOP_OF_HEAD]
        nose = face_landmarks.landmark[self.NOSE_TIP]
        chin = face_landmarks.landmark[self.CHIN]

        # Y coordinates (increases top → bottom in image space)
        top_y  = top.y  * frame_h
        nose_y = nose.y * frame_h
        chin_y = chin.y * frame_h

        d_top    = nose_y - top_y    # top-of-head  →  nose
        d_bottom = chin_y - nose_y   # nose         →  chin

        if d_top <= 0:
            d_top = 1e-6

        pitch_ratio = d_bottom / d_top

        is_nod_event   = False
        is_nod_ongoing = False

        if pitch_ratio < self.pitch_threshold:
            self.droop_frames += 1  # Still counted for external reset logic
            now = time.time()
            if self._droop_start is None:
                self._droop_start = now  # Head just drooped — start the clock
            elapsed = now - self._droop_start
            if elapsed >= self.droop_duration_seconds:
                is_nod_ongoing = True
                if not self._event_fired:
                    is_nod_event = True
                    self._event_fired = True
        else:
            # Head lifted — reset
            self.droop_frames = 0
            self._droop_start = None
            self._event_fired = False

        return pitch_ratio, is_nod_event, is_nod_ongoing
