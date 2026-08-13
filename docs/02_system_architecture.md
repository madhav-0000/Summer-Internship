# System Architecture

## High-Level Overview
The Drowsiness Detection System captures a continuous webcam feed, extracts facial landmarks in real-time, computes geometric ratios to identify specific driver states (eyes closed, yawning, nodding off, distracted), and sounds an audio alarm when those states persist or repeat beyond configured thresholds.

A two-tier **escalation system** prevents false positives: a single drowsiness signal is not enough to trigger an alarm — it must occur a minimum number of times within a rolling time window before the alert arms.

All time-based thresholds (eye closure duration, yawn duration, head droop duration, mirror-check grace period) are measured in **real seconds** using `time.time()`, not frame counts. This ensures consistent behaviour at any camera FPS.

## Component Flow

```
Webcam
  │
  ▼
VideoStream (core/video.py)
  │  Reads frames at native camera resolution
  │
  ▼
[Mirror flip + scale-to-fit display]
  │
  ▼
MotionDetector (core/motion.py)
  │  Reads JSON mock file / serial GPS / Always-On fallback
  │
  ├──► [NOT in motion] → Clear all trackers, show STANDBY screen
  │
  └──► [In motion] → FaceMeshDetector (core/mesh.py)
                         │
                         ├──► [No landmarks] → Distraction counter ↑
                         │
                         └──► [Landmarks found]
                                  │
                                  ├── Yaw Index check
                                  │     ├── < threshold → Normal forward gaze
                                  │     ├── > threshold, < 4s → MIRROR CHECK (no penalty)
                                  │     └── > threshold, ≥ 4s → Distraction counter ↑
                                  │
                                  ├── EyeTracker (core/eyes.py)
                                  │     └── EAR < 0.25 for ≥ 2s → eye_closure event
                                  │
                                  ├── MouthTracker (core/mouth.py)
                                  │     └── MAR > 0.6 for ≥ 1s → yawn event
                                  │
                                  └── HeadPoseEstimator (core/pose.py)
                                        └── Pitch < 0.62 for ≥ 1.5s AND EAR ≤ 0.30
                                              → head_nod event
                                  │
                                  ▼
                         AlertEscalation (core/alert_escalation.py)
                           Sliding-window event counter per category
                           Arms when N events occur in T seconds
                           Disarms after cooldown with no new events
                                  │
                                  ▼
                         AudioAlert (core/alerts.py)
                           Non-blocking pygame alarm
```

## Module Descriptions

| Module | Responsibility |
| :--- | :--- |
| `main.py` | Entry point: integrates all components, draws the HUD overlay, handles keyboard input |
| `core/video.py` | Webcam capture via OpenCV; requests a preferred resolution from the camera driver |
| `core/motion.py` | Determines if the vehicle is in motion via JSON mock, serial GPS/OBD-II, or Always-On fallback |
| `core/mesh.py` | Initializes and runs MediaPipe Face Mesh, returns 468 3D facial landmarks per frame |
| `core/eyes.py` | Computes EAR; uses real-time duration to filter out blinks vs. sustained closure |
| `core/mouth.py` | Computes MAR; uses real-time duration to filter out talking/coughing vs. genuine yawns |
| `core/pose.py` | Computes pitch ratio; uses real-time duration + EAR correlation to filter false nods |
| `core/alert_escalation.py` | Two-tier escalation: counts timestamped events in a sliding window, arms/disarms alarm |
| `core/alerts.py` | Non-blocking `pygame` audio mixer for alarm playback |

## Key Design Decisions

### Time-Based vs. Frame-Based Detection
All duration thresholds were migrated from frame counts to `time.time()` measurements. This means the 2-second eye closure window is always 2 real seconds whether the camera runs at 15 FPS or 30 FPS.

### Two-Tier Escalation (No Single-Event Alarms)
A single drowsy event never triggers the alarm immediately. The `AlertEscalation` class maintains a `deque` of event timestamps per category. An event expires and is removed automatically once it falls outside the rolling window. This handles the "4th yawn removes the 1st" sliding-window behaviour naturally.

### EAR-Correlated Nod Detection
Head droop is correlated with partial eye closure (`EAR ≤ NOD_EAR_CORRELATION`). A person resting their chin on their hand will have a drooping pitch ratio but fully open eyes — this correlation prevents that false positive.

### Yaw Grace Period
Brief sideways glances (≤ 4 seconds) are treated as mirror checks with no distraction penalty. Only sustained sideways looks count as distraction events.

### Reverse Mode
When the driver engages reverse gear, they are expected to look backward. `reverse_mode = True` suppresses face-loss distraction alerts. A full-width amber banner is drawn at the top of the frame. The mode auto-disables after 120 seconds as a safety net.

### Display Scaling
All HUD drawing happens on the native-resolution camera frame. The final frame is scaled down proportionally (preserving aspect ratio) to fit within 700px height before being passed to `cv2.imshow`. This avoids both quality loss from pre-scaling and window cropping from an oversized frame.
