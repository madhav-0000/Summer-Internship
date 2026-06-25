import cv2

class VideoStream:
    """
    A simple wrapper for OpenCV's VideoCapture to read frames from a webcam.
    """
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        if not self.stream.isOpened():
            raise ValueError(f"Unable to open video source {src}")

    def read(self):
        """
        Reads a frame from the webcam.
        Returns: The frame as a numpy array, or None if reading fails.
        """
        ret, frame = self.stream.read()
        if not ret:
            return None
        return frame

    def release(self):
        """
        Releases the webcam resource.
        """
        self.stream.release()
