# Eye Tracker Component

## File: `core/eyes.py`

### Concept Breakdown
This component applies the Eye Aspect Ratio (EAR) formula to the landmarks detected by the Face Mesh to track blink/closure states over time. It identifies prolonged eye closures (micro-sleeps) versus normal, quick blinks.

### Class: `EyeTracker`
Maintains the state of eye closures across multiple frames.

#### `__init__(self, ear_threshold=0.25, ear_frames=20, closure_duration_seconds=1.5)`
- **Configuration:** 
  - `ear_threshold`: The value below which the eye is considered closed.
  - `ear_frames`: Kept for backward compatibility (not used for timing).
  - `closure_duration_seconds`: Real-time duration (seconds) the EAR must remain below the threshold before an event is triggered.
  - `closure_frames`: A counter that increments each frame the eye is closed (used by external reset logic).
  - `alarm_on`: A boolean flag indicating if the drowsiness condition is met.

#### `get_eye_landmarks(self, face_landmarks, frame_w, frame_h, indices)`
- **Behavior:** Takes the normalized coordinates (from 0.0 to 1.0) provided by MediaPipe and multiplies them by the frame width and height to get exact pixel coordinates `(x, y)` on the image.

#### `calculate_ear(self, eye_coords)`
- **Behavior:** Executes the EAR mathematical formula (documented in `03_math_and_concepts.md`) using NumPy's Euclidean norm calculation (`np.linalg.norm`).

#### `process(self, face_landmarks, frame_w, frame_h)`
- **Input:** The raw `face_landmarks` object from MediaPipe, along with the dimensions of the video frame.
- **Output:** Returns a tuple `(avg_ear, is_closure_event, is_closure_ongoing)`.
- **Behavior:** 
  1. Extracts left and right eye coordinates based on predefined indices.
  2. Calculates individual EAR for both eyes.
  3. Averages the two EAR values for stability.
  4. If the average EAR is below the threshold, it measures the real-time duration of the closure. If the duration exceeds `closure_duration_seconds`, it returns `is_closure_event = True` (on the rising edge) and `is_closure_ongoing = True`. Otherwise, resets the clock.
