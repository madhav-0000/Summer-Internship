# System Architecture

## High-Level Overview
The Drowsiness Detection System captures a continuous webcam feed, extracts facial landmarks in real-time, computes geometric ratios to identify specific states (eyes closed, yawning, nodding off), and plays an audio alert if these states persist beyond configured thresholds.

## Component Flow
1. **Video Stream**: Captures frames from the webcam.
2. **Motion Detector**: Checks if the vehicle is in motion. If stationary, suspends Face Mesh and tracking to enter standby mode. If in motion, proceeds to frame processing.
3. **Face Mesh Engine**: Processes the frame using MediaPipe to detect 468 3D facial landmarks.
4. **Trackers**:
   - **Eye Tracker**: Uses landmarks around the eyes to calculate the Eye Aspect Ratio (EAR).
   - **Mouth Tracker**: Uses landmarks around the lips to calculate the Mouth Aspect Ratio (MAR).
   - **Head Pose Estimator**: Uses nose, chin, and other anchor points to calculate head pitch.
5. **Alert System**: Monitors the trackers' states over successive frames. If conditions are met (e.g., EAR < threshold for N frames), triggers a sound via `pygame`.

## Proposed Code Structure
- `main.py`: The entry point that integrates all components into the main processing loop.
- `core/`: Contains the tracker and detection logic.
  - `video.py`: Handles webcam operations.
  - `motion.py`: Detects vehicle speed and motion state (standby control).
  - `mesh.py`: Initializes and runs MediaPipe Face Mesh.
  - `eyes.py`: EAR calculation.
  - `mouth.py`: MAR calculation.
  - `pose.py`: Head pitch estimation.
  - `alerts.py`: Handles audio alerts.
- `docs/`: Comprehensive project documentation.
  - `components/`: Sub-folder documenting individual components (e.g., `motion_detector.md`, `eye_tracker.md`, etc.).
