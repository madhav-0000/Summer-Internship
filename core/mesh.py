import cv2
import mediapipe as mp

class FaceMeshDetector:
    """
    A wrapper for MediaPipe's Face Mesh solution to extract 3D facial landmarks.
    """
    def __init__(self, max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=max_num_faces,
            refine_landmarks=refine_landmarks,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

    def process(self, frame):
        """
        Processes an image frame to detect facial landmarks.
        Args:
            frame: A BGR image frame from OpenCV.
        Returns:
            A NamedTuple containing the detected landmarks (if any).
        """
        # MediaPipe expects RGB images, so we convert from BGR (OpenCV default)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # To improve performance, optionally mark the image as not writeable to pass by reference.
        rgb_frame.flags.writeable = False
        results = self.face_mesh.process(rgb_frame)
        return results

    def close(self):
        """
        Closes the underlying MediaPipe instance.
        """
        self.face_mesh.close()
