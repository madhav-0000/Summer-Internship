import numpy as np

class HeadPoseEstimator:
    """
    Estimates head pitch (up/down movement) to detect nodding off (drooping).
    """
    # MediaPipe Face Mesh landmarks for head pitch estimation
    TOP_OF_HEAD = 10
    NOSE_TIP = 1
    CHIN = 152

    def __init__(self, pitch_threshold=0.6, pitch_frames=20):
        self.pitch_threshold = pitch_threshold
        self.pitch_frames = pitch_frames
        self.droop_frames = 0
        self.alarm_on = False

    def process(self, face_landmarks, frame_w, frame_h):
        top = face_landmarks.landmark[self.TOP_OF_HEAD]
        nose = face_landmarks.landmark[self.NOSE_TIP]
        chin = face_landmarks.landmark[self.CHIN]

        # Get Y coordinates (pixel values)
        # In image coordinates, Y increases from top to bottom
        top_y = top.y * frame_h
        nose_y = nose.y * frame_h
        chin_y = chin.y * frame_h

        # Calculate vertical distances
        d_top = nose_y - top_y
        d_bottom = chin_y - nose_y

        if d_top <= 0:
            d_top = 1e-6

        # Ratio of bottom face height to top face height
        pitch_ratio = d_bottom / d_top

        # When looking down, d_bottom decreases and d_top increases, lowering the ratio
        if pitch_ratio < self.pitch_threshold:
            self.droop_frames += 1
            if self.droop_frames >= self.pitch_frames:
                self.alarm_on = True
        else:
            self.droop_frames = 0
            self.alarm_on = False

        return pitch_ratio, self.alarm_on
