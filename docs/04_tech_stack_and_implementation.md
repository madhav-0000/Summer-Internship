# Technology Stack & Detailed Implementation Guide

## Overview
This document outlines the specific technologies, programming languages, libraries, and mathematical concepts used to implement the Real-Time Driver Drowsiness Detection System. The project prioritizes a mathematical/geometric approach over heavy Deep Learning models to ensure high performance (high FPS) on standard local hardware.

## Core Technology Stack

- **Programming Language:** Python 3.8+ (Chosen for its rich ecosystem of computer vision and mathematical libraries).
- **Environment:** Local Windows machine execution (can be adapted for Mac/Linux).
- **Hardware Requirement:** Standard USB or integrated Webcam.

## Dependencies & Libraries

1. **OpenCV (`opencv-python`)**
   - **Purpose:** Video streaming and image processing.
   - **Usage:** Capturing frames from the webcam, converting color spaces (BGR to RGB), rendering text and bounding boxes on the video feed, and displaying the final output window.
2. **MediaPipe (`mediapipe`)**
   - **Purpose:** Facial landmark detection.
   - **Usage:** Utilizing the `Face Mesh` solution to extract 468 3D facial landmarks from each frame in real-time. This provides the raw coordinate data needed for all subsequent mathematical calculations.
3. **NumPy (`numpy`)**
   - **Purpose:** High-performance mathematical operations.
   - **Usage:** Calculating Euclidean distances between facial landmarks, computing aspect ratios (EAR, MAR), and managing arrays of coordinate data efficiently.
4. **Pygame (`pygame`) or Playsound**
   - **Purpose:** Audio alert generation.
   - **Usage:** Playing a "beep" or alarm sound when a drowsiness threshold is breached. Pygame's mixer is often preferred as it allows for asynchronous audio playback without blocking the main OpenCV video processing thread.
5. **PySerial (`pyserial`) [Optional]**
   - **Purpose:** Communication with physical serial port hardware.
   - **Usage:** Reading speed data or GPS strings (NMEA format) from a connected microcontroller, OBD-II reader, or GPS sensor.

## Feature Implementation Details

### 1. Video Streaming & Face Mesh Integration
- **Implementation:** 
  - `cv2.VideoCapture(0)` initializes the webcam.
  - Each frame is read in a `while` loop, converted from BGR (OpenCV default) to RGB, and passed to `mediapipe.solutions.face_mesh`.
  - The model outputs an array of normalized coordinates (x, y, z) for 468 points on the face.

### 2. Eye Closure Detection (EAR - Eye Aspect Ratio)
- **Implementation:**
  - **Landmarks Used:** Specific points around the left and right eyes (e.g., points 33, 133, 159, 145, etc.).
  - **Math:** The EAR formula calculates the ratio of the distances between the vertical eye landmarks and the horizontal eye landmarks. 
  - **Logic:** When the eyes close, the EAR value drops significantly. If `EAR < EAR_THRESHOLD` continuously for `closure_duration_seconds` (1.5s), an eye closure event is logged.

### 3. Yawn Detection (MAR - Mouth Aspect Ratio)
- **Implementation:**
  - **Landmarks Used:** Specific points on the inner or outer lips (e.g., points 13, 14, 78, 308).
  - **Math:** Similar to EAR, the MAR formula calculates the ratio of the vertical distance between the top and bottom lips to the horizontal distance between the corners of the mouth.
  - **Logic:** During a yawn, the MAR value spikes. If `MAR > MAR_THRESHOLD` continuously for `yawn_duration_seconds` (1.0s), a yawn event is logged.

### 4. Head Drooping Detection (Pose Estimation)
- **Implementation:**
  - **Landmarks Used:** The tip of the nose, the chin, and points on the sides of the face.
  - **Math:** By comparing the 2D or 3D positions of the nose relative to the chin and eyes, we can estimate the pitch (up/down tilt) of the head. Simple geometric distances or a Perspective-n-Point (PnP) algorithm can be used.
  - **Logic:** If the calculated head pitch angle drops below a certain `PITCH_THRESHOLD` (indicating the head is falling forward) continuously for `droop_duration_seconds` (1.5s), a head nod event is logged.

### 5. Alert System
- **Implementation:**
  - **Logic:** The `AlertEscalation` system monitors timestamped events from the trackers.
  - **Action:** If any category accumulates enough events within a sliding time window (e.g., 2 eye closures in 45 seconds), the alarm is armed and a separate thread or asynchronous call invokes the audio playback using `pygame.mixer.Sound.play()`.

### 6. Vehicle Motion & Standby System
- **Implementation:**
  - **Logic:** Periodically reads vehicle status to determine if the vehicle is in motion. If the vehicle is stationary, face detection is suspended (saving power and CPU) and the screen dims to a standby overlay.
  - **Math/Parsing:** Converts NMEA GPVTG and GPRMC coordinates and speeds (knots/kmh) from USB-serial GPS modules, or processes raw key-value pairs (`SPEED=X`).
  - **Fallback:** Defaults to safety "Always On" mode if no motion detection device is configured or connected.

## Configuration & Tuning
All thresholds (`EAR_THRESHOLD`, `MAR_THRESHOLD`, `PITCH_THRESHOLD`) and motion detection settings (`MOTION_CONFIG_PATH`, `MOTION_SERIAL_PORT`) will be exposed as configurable constants at the top of the main script. This allows for easy calibration based on different camera angles, lighting conditions, individual user facial structures, and hardware COM ports.
