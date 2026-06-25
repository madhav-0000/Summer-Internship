# Video Stream Component

## File: `core/video.py`

### Concept Breakdown
The Video Stream component acts as the foundational layer of our application. It's responsible for acquiring the raw image data (frames) from the user's webcam, which will subsequently be fed into our detection algorithms.

We use **OpenCV (cv2)** for this because it provides a highly optimized, cross-platform interface for accessing camera hardware (`cv2.VideoCapture`). 

### Class: `VideoStream`
This class encapsulates the camera interaction so the rest of the application doesn't have to manage raw OpenCV calls directly.

#### `__init__(self, src=0)`
- **Input:** `src` (integer). Defaults to `0`, which tells OpenCV to open the default system camera (the built-in webcam).
- **Behavior:** Initializes the `cv2.VideoCapture` object. If the camera cannot be accessed, it raises a `ValueError` immediately, preventing the app from starting in a broken state.

#### `read(self)`
- **Input:** None.
- **Output:** Returns a single image frame (as a NumPy array) or `None` if the frame couldn't be read.
- **Behavior:** Calls the internal `self.stream.read()` method to pull the latest image from the camera buffer.

#### `release(self)`
- **Input:** None.
- **Behavior:** Frees the webcam resource. This is crucial when the application shuts down; otherwise, the camera light might stay on, and other apps wouldn't be able to use it.
