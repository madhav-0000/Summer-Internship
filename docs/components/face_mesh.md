# Face Mesh Component

## File: `core/mesh.py`

### Concept Breakdown
The Face Mesh component is responsible for analyzing an image and locating key facial features. We use **MediaPipe Face Mesh**, a lightweight machine learning solution by Google.

Unlike heavy deep learning models that try to "understand" everything in a scene, Face Mesh is heavily optimized just to output coordinates. It estimates 468 3D landmarks on a human face in real-time. Because it only does math to plot these coordinates (and we only use a handful of them), it runs very fast on standard CPUs.

### Class: `FaceMeshDetector`
This class abstracts the setup and execution of the MediaPipe pipeline.

#### `__init__(self, ...)`
- **Behavior:** Initializes `mp.solutions.face_mesh.FaceMesh`. 
- **Configuration:** 
  - `max_num_faces=1`: We assume one driver per vehicle. Restricting this to 1 face saves significant processing power.
  - `refine_landmarks=True`: Gives us extra, highly accurate landmarks around the eyes and lips, which is essential for our EAR and MAR calculations.
  - `min_detection_confidence` / `min_tracking_confidence`: Set to `0.5` by default to balance accuracy with speed.

#### `process(self, frame)`
- **Input:** `frame` (A raw BGR image array from OpenCV).
- **Output:** A `results` object containing the detected face landmarks (`results.multi_face_landmarks`).
- **Behavior:**
  - MediaPipe expects images in RGB format, but OpenCV reads them in BGR format. The first step is to use `cv2.cvtColor` to convert the color channels.
  - We set the image flag `writeable = False` to pass it by reference, saving memory and processing time.
  - The frame is passed into `self.face_mesh.process()`, which calculates and returns the landmark coordinates.

#### `close(self)`
- **Behavior:** Properly releases the MediaPipe resources when the app shuts down.
