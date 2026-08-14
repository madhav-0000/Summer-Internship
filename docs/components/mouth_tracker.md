# Mouth Tracker Component

## File: `core/mouth.py`

### Concept Breakdown
This component applies the Mouth Aspect Ratio (MAR) formula to the landmarks of the inner lips. It is designed to identify when the driver opens their mouth unusually wide for a prolonged duration, which typically indicates a yawn.

### Class: `MouthTracker`
Maintains the state of yawns across multiple frames.

#### `__init__(self, mar_threshold=0.6, mar_frames=15, yawn_duration_seconds=1.0)`
- **Configuration:** 
  - `mar_threshold`: The value above which the mouth is considered open wide enough to be a yawn.
  - `mar_frames`: Kept for backward compatibility (not used for timing).
  - `yawn_duration_seconds`: Real-time duration (seconds) the MAR must remain above the threshold before an event is triggered.
  - `yawn_frames`: A counter that increments each frame the mouth is wide open (used by external reset logic).
  - `alarm_on`: A boolean flag indicating if the drowsiness condition (yawning) is met.

#### `get_mouth_landmarks(self, face_landmarks, frame_w, frame_h)`
- **Behavior:** Extracts the `(x, y)` pixel coordinates for the inner lip landmarks identified by MediaPipe.

#### `calculate_mar(self, mouth_coords)`
- **Behavior:** Executes the MAR mathematical formula (documented in `03_math_and_concepts.md`).

#### `process(self, face_landmarks, frame_w, frame_h)`
- **Input:** The raw `face_landmarks` object from MediaPipe, and frame dimensions.
- **Output:** Returns a tuple `(mar, is_yawn_event, is_yawn_ongoing)`.
- **Behavior:** 
  1. Extracts the mouth coordinates.
  2. Calculates the MAR.
  3. If the MAR is above the threshold, it measures the real-time duration of the yawn. If the duration exceeds `yawn_duration_seconds`, it returns `is_yawn_event = True` (on the rising edge) and `is_yawn_ongoing = True`. Otherwise, it resets the clock.
