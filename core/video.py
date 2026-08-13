import cv2

class VideoStream:
    """
    A simple wrapper for OpenCV's VideoCapture to read frames from a webcam.
    """
    def __init__(self, src=0, width=640, height=480):
        self.stream = cv2.VideoCapture(src)
        if not self.stream.isOpened():
            raise ValueError(f"Unable to open video source {src}")
        # Set explicit resolution to avoid camera feed being cut or misaligned
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

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
