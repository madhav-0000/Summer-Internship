# Alert System Component

## File: `core/alerts.py`

### Concept Breakdown
The Alert System is responsible for providing immediate auditory feedback to the driver if any of the trackers (Eye, Mouth, or Head Pose) detect a persistent dangerous state. 

### Class: `AudioAlert`
Manages playing and stopping the warning sound.

#### `__init__(self, sound_path="assets/alert.wav")`
- **Behavior:** Attempts to initialize the `pygame.mixer` to play a custom `.wav` file located in the `assets/` directory. 
- **Fallback:** If `pygame` fails to load, or if the `alert.wav` file is missing, it automatically falls back to using the built-in Windows beep via the `winsound` module. This ensures the safety feature works even without external assets.

#### `play(self)`
- **Behavior:** Triggers the alert. If using PyGame, it loops the sound continuously. If using the Windows fallback, it plays a 1-second 2500Hz beep. It uses the `is_playing` flag to ensure the PyGame sound isn't repeatedly triggered on every frame, which would cause an unpleasant overlapping audio glitch.

#### `stop(self)`
- **Behavior:** Halts the audio playback if it was previously started. This is called by the main application loop when the driver's state returns to normal (e.g., eyes open, yawn finishes, head lifts up).
