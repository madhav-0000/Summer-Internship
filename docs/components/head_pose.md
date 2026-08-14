# Head Pose Estimator Component

## File: `core/pose.py`

### Concept Breakdown
This component applies a 2D geometric ratio to estimate the pitch (up and down tilt) of the driver's head. It is used to detect "nodding off" or head drooping.

### Class: `HeadPoseEstimator`
Tracks the pitch ratio across multiple frames to identify sustained drooping.

#### `__init__(self, pitch_threshold=0.7, pitch_frames=20, droop_duration_seconds=1.5)`
- **Configuration:** 
  - `pitch_threshold`: The ratio below which the head is considered to be drooping downwards.
  - `pitch_frames`: Kept for backward compatibility (not used for timing).
  - `droop_duration_seconds`: Real-time duration (seconds) the pitch must remain below the threshold before an event is triggered.
  - `droop_frames`: A counter that increments each frame the head is drooping (used by external reset logic).
  - `alarm_on`: A boolean flag indicating if the drowsiness condition (nodding off) is met.

#### `process(self, face_landmarks, frame_w, frame_h)`
- **Input:** The raw `face_landmarks` object from MediaPipe, and frame dimensions.
- **Output:** Returns a tuple `(pitch_ratio, is_nod_event, is_nod_ongoing)`.
- **Behavior:** 
  1. Extracts the Y coordinates of the top of the head, nose tip, and chin.
  2. Calculates the vertical distance from the nose to the top of the head (`d_top`).
  3. Calculates the vertical distance from the chin to the nose (`d_bottom`).
  4. Calculates the `pitch_ratio = d_bottom / d_top`.
  5. If the head nods down, `d_bottom` gets smaller and `d_top` gets larger, causing the ratio to fall below the threshold. If this persists continuously for `droop_duration_seconds`, it returns `is_nod_event = True` (on the rising edge) and `is_nod_ongoing = True`. Otherwise, it resets the clock.
