import numpy as np

class EyeTracker:
    """
    Calculates Eye Aspect Ratio (EAR) and determines if eyes are closed.
    """
    # MediaPipe Face Mesh landmark indices for eyes
    # Left eye: 33 (left corner), 160, 158 (top), 133 (right corner), 153, 144 (bottom)
    # Right eye: 362 (left corner), 385, 387 (top), 263 (right corner), 373, 380 (bottom)
    LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]

    def __init__(self, ear_threshold=0.25, ear_frames=20):
        self.ear_threshold = ear_threshold
        self.ear_frames = ear_frames
        self.closure_frames = 0
        self.alarm_on = False

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
        Returns the computed EAR and a boolean indicating if an alert should trigger.
        """
        left_eye = self.get_eye_landmarks(face_landmarks, frame_w, frame_h, self.LEFT_EYE_INDICES)
        right_eye = self.get_eye_landmarks(face_landmarks, frame_w, frame_h, self.RIGHT_EYE_INDICES)

        left_ear = self.calculate_ear(left_eye)
        right_ear = self.calculate_ear(right_eye)

        avg_ear = (left_ear + right_ear) / 2.0

        if avg_ear < self.ear_threshold:
            self.closure_frames += 1
            if self.closure_frames >= self.ear_frames:
                self.alarm_on = True
        else:
            self.closure_frames = 0
            self.alarm_on = False

        return avg_ear, self.alarm_on
