import numpy as np

class MouthTracker:
    """
    Calculates Mouth Aspect Ratio (MAR) and determines if the driver is yawning.
    """
    # MediaPipe Face Mesh landmark indices for inner lips
    # Left corner: 78, Right corner: 308
    # Top: 13, Bottom: 14
    INNER_LIP_INDICES = [78, 13, 308, 14]

    def __init__(self, mar_threshold=0.6, mar_frames=15):
        self.mar_threshold = mar_threshold
        self.mar_frames = mar_frames
        self.yawn_frames = 0
        self.alarm_on = False

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
        mouth_coords = self.get_mouth_landmarks(face_landmarks, frame_w, frame_h)
        mar = self.calculate_mar(mouth_coords)

        if mar > self.mar_threshold:
            self.yawn_frames += 1
            if self.yawn_frames >= self.mar_frames:
                self.alarm_on = True
        else:
            self.yawn_frames = 0
            self.alarm_on = False

        return mar, self.alarm_on
