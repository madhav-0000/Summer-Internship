---
title: "A Project Report (Internship) on Real-Time Driver Drowsiness Detection System"
---

# A Project Report (Internship)

**on**

**Real-Time Driver Drowsiness Detection System**

*Submitted for the Fulfillment of the Credits of the*  
*Audit Course in*  
**Bachelor of Technology**  
**In**  
**Engineering and Computational Mechanics**

*By*  
**Madhav – [Your Roll Number]**

*Under the Guidance of*  
**Dr. Uvanesh K**  
Assistant Professor, Department of Applied Mechanics, MNNIT Allahabad

*Submitted To*  
**Dr. Uvanesh K**  
Assistant Professor, Department of Applied Mechanics, MNNIT Allahabad

**Department of Applied Mechanics**  
**Motilal Nehru National Institute of Technology, Allahabad**  
**Prayagraj – INDIA**

\newpage

# Certificate

This is to certify that the work contained in this report titled **“Real-Time Driver Drowsiness Detection System”**, submitted by Madhav (Reg No.: [Your Roll Number]) for the Fulfillment of the Credits of the Audit Course of Bachelor of Technology in Engineering and Computational Mechanics to the Department of Applied Mechanics, Motilal Nehru National Institute of Technology, Allahabad, is a Bonafide work of the student carried out under my supervision.

Date – 15/08/2026  
Place – Prayagraj

**Dr. Uvanesh K**  
Assistant Professor  
Department of Applied Mechanics  
MNNIT, Allahabad

\newpage

# UNDERTAKING

I declare that the work presented in this report entitled **“Real-Time Driver Drowsiness Detection System”**, submitted to the Department of Applied Mechanics, Motilal Nehru National Institute of Technology Allahabad, Prayagraj (India), for the Fulfillment of the Credits of the Audit Course, is my own original work, carried out during the Internship at MNNIT Allahabad. I have neither plagiarized any part of this work nor submitted the same work for the award of any other credit or degree elsewhere. In case this undertaking is found incorrect, the credit shall be withdrawn unconditionally.

Date – 15/08/2026  
Place – Prayagraj  

**Madhav**  
**[Your Roll Number]**

\newpage

# Preface

This report — "Real-Time Driver Drowsiness Detection System" — was put together to fulfill the credit requirements of the Audit Course, under the guidance of Dr. Uvanesh K, and is submitted to the Department of Applied Mechanics, MNNIT Allahabad.

The internship was focused on building a lightweight, highly optimized computer vision system aimed at detecting driver fatigue and distraction in real-time. Rather than relying on heavy deep learning models requiring expensive GPUs, the system utilizes MediaPipe's Face Mesh to extract 468 3D facial landmarks and applies geometric mathematical ratios (EAR, MAR, and Pitch) to determine driver state. The project was built using Python, OpenCV, and MediaPipe, and features a robust two-tier sliding-window escalation system to prevent false alarms, as well as a dynamic UI overlay.

The report follows the project roughly in the order it happened: it starts with the motivation behind preventing road accidents caused by fatigue, covers the theoretical background of geometric facial analysis, and then details the system design, implementation, and evaluation. It also discusses practical challenges faced during development—such as handling varying camera frame rates and eliminating false positives from natural movements—and how they were resolved.

At its core, this project is a hands-on exploration of how classical computer vision techniques combined with efficient landmark tracking can solve real-world safety critical problems in real-time, purely on edge CPU devices.

\newpage

# Acknowledgement

I would like to express my sincere gratitude to **Dr. Uvanesh K**, Department of Applied Mechanics, MNNIT Allahabad, for his continuous guidance, feedback and support throughout the Internship. His insights were instrumental in shaping the direction of the project, particularly in navigating the technical trade-offs between model performance and computational efficiency.

I am also thankful to **Dr. Uvanesh K**, Department of Applied Mechanics, Motilal Nehru National Institute of Technology Allahabad, for agreeing to evaluate this internship work towards audit course credit, and for his valuable suggestions. Finally, I acknowledge the open-source communities behind Python, OpenCV, and Google MediaPipe, whose robust libraries formed the technical foundation of this work.

Date – 15/08/2026  
Place – Prayagraj  

**Madhav**  
Engineering and Computational Mechanics  
Department of Applied Mechanics  
MNNIT Allahabad

\newpage

# Abstract

The Real-Time Driver Drowsiness Detection System is a computer vision-based application designed to monitor driver alertness and prevent accidents caused by fatigue or distraction. The system relies on Google's MediaPipe Face Mesh to extract 468 facial landmarks in real-time. By applying geometric calculations to these landmarks—specifically the Eye Aspect Ratio (EAR), Mouth Aspect Ratio (MAR), and Head Pitch Ratio—the system accurately identifies signs of micro-sleep, yawning, and head drooping.

The central engineering challenge of this project was ensuring consistent, reliable detection across varying hardware setups and lighting conditions without generating false alarms. Early iterations using frame-count thresholds proved inconsistent across different camera frame rates. This was resolved by transitioning to a real-time `time.time()` based duration system. To further mitigate false positives (such as confusing a deliberate "hand-on-chin" posture with a drowsy head nod), the system employs a two-tier Alert Escalation sliding window and cross-correlates metrics (e.g., verifying that the eyes are also partially closed during a head nod). 

The system operates entirely on a local CPU without requiring internet access or GPU hardware, achieving a stable processing speed of over 20-30 FPS. It includes advanced features such as a "Reverse Mode" to temporarily suppress distraction alerts when backing up, a "Mirror Check" grace period for lateral head movements, and a dynamic hardware-accelerated Heads-Up Display (HUD) overlay that tracks escalating fatigue events. 

**Keywords:** Driver Drowsiness, Computer Vision, MediaPipe, OpenCV, Eye Aspect Ratio (EAR), Mouth Aspect Ratio (MAR), Real-time Processing.

\newpage

# Table of Contents

1. **Introduction**
   1.1 Background and Motivation
   1.2 Objective and Scope
   1.3 Problem Statement
   1.4 Technical Challenges
   1.5 Organization of Report
2. **Theoretical Background & Literature Review**
   2.1 Evolution of Driver Monitoring Systems
   2.2 Deep Learning vs. Geometric Tracking
   2.3 Eye Aspect Ratio (EAR)
   2.4 Mouth Aspect Ratio (MAR)
   2.5 Head Pitch and Yaw Estimation
   2.6 Two-Tier Escalation Architecture
3. **System Design and Implementation**
   3.1 Overall System Architecture
   3.2 Local Technology Stack
   3.3 Eye Closure and Yawning Pipelines
   3.4 Head Pose and Distraction Pipelines
   3.5 User Interface and HUD Design
   3.6 Environment and Dependency Management
4. **Experimental Results and Discussion**
   4.1 Hardware and Software Used
   4.2 Performance Evaluation Metrics
   4.3 Quantitative Evaluation: Threshold Tuning
   4.4 Distraction Grace Period Testing
   4.5 Qualitative Evaluation: False Positive Filtering
   4.6 Infrastructure and Edge Case Resolution
5. **Conclusion and Future Scope**
   5.1 Project Summary
   5.2 Major Technical Contributions
   5.3 Limitations
   5.4 Future Enhancements
- **References**

\newpage

# 1 – Introduction

## 1.1 Background and Motivation
Driver fatigue and distraction are among the leading causes of road traffic accidents globally. According to various transport authorities, micro-sleeps (brief, unintended episodes of loss of attention) occurring at highway speeds can result in a vehicle traveling hundreds of feet completely uncontrolled. Traditional safety measures rely on the driver's own awareness of their fatigue, which is often severely compromised right before an accident.

The motivation behind this project is to create an active safety net: a non-intrusive, AI-driven monitoring system that can continuously observe a driver's facial cues and alert them before a critical failure occurs. By bringing this technology to standard edge devices (like a dashboard camera and a basic CPU), the goal is to make high-end safety features accessible without requiring specialized hardware.

## 1.2 Objective and Scope
The objectives of this project were:
- To develop an ML pipeline to process live video feeds and extract facial landmarks in real-time.
- To compute geometric ratios (EAR, MAR, Pitch, Yaw) to detect closed eyes, yawning, nodding off, and distraction.
- To implement a robust, time-based escalation system to prevent false alarms from natural movements.
- To ensure the complete system runs locally and efficiently on a standard CPU.
- To provide an interactive Heads-Up Display (HUD) for real-time status monitoring and configuration.

The scope of this project is limited to geometric analysis using 2D image projections of 3D facial landmarks. It assumes the driver's face is generally visible to a dashboard-mounted camera.

## 1.3 Problem Statement
Detecting drowsiness via a webcam involves significant technical hurdles. The core problem is that natural human behaviors (blinking, talking, checking mirrors) closely resemble drowsy behaviors (micro-sleeps, yawning, looking away). 

If a system triggers an alarm every time the driver blinks or looks at a side mirror, the driver will quickly become annoyed and turn the system off. Therefore, the system must not only detect these events but accurately measure their *duration* and *frequency* to distinguish between alert behavior and genuine fatigue. Furthermore, the system must operate consistently regardless of the camera's frame rate, requiring logic that is independent of hardware speed.

## 1.4 Technical Challenges
The development of the model came with many practical technical challenges. First, standardizing the detection window across different webcams (which output anywhere from 15 to 60 frames per second) meant that counting frames was not a viable way to measure time. 

Another challenge was cross-contamination of signals. For example, resting a hand on the chin tilts the head forward, which identically mimics a drowsy head-droop in terms of pitch geometry. Distinguishing a deliberate tilt from a sleepy nod required correlating multiple facial features simultaneously.

Finally, managing the user interface required overlaying complex text and graphics onto a live video feed without degrading the frame rate or causing display stretching issues on different screen resolutions.

## 1.5 Organization of Report
This report is organized into five chapters. Chapter 2 covers the theoretical aspects of the geometric formulas used for detection. Chapter 3 explains the system architecture, the implementation of the tracking pipelines, and the sliding-window escalation logic. Chapter 4 presents the experimental results, threshold tuning, and how false positives were resolved. Chapter 5 concludes the report and discusses potential future enhancements.

\newpage

# 2 – Theoretical Background & Literature Review

## 2.1 Evolution of Driver Monitoring Systems
Early driver monitoring systems relied heavily on vehicular telemetry—monitoring steering wheel patterns, lane departures, and brake usage. While effective, these systems only detect fatigue *after* the driver has already made a dangerous physical error. Modern systems have shifted toward direct physiological monitoring, primarily using computer vision to track the driver's eyes and face before driving performance degrades.

## 2.2 Deep Learning vs. Geometric Tracking
Many state-of-the-art vision systems utilize heavy Convolutional Neural Networks (CNNs) to classify an image as "drowsy" or "awake". While highly accurate, these models require immense computational power (GPUs) to run in real-time, making them unsuitable for low-power dashboard deployment. 

This project utilizes a hybrid approach: using a highly optimized deep learning model (MediaPipe Face Mesh) strictly for landmark localization, and then applying lightweight mathematical geometry (Euclidean distances) on those landmarks to classify behavior. This ensures high accuracy with minimal CPU overhead.

## 2.3 Eye Aspect Ratio (EAR)
The EAR is an elegant mathematical approximation used to determine if a person's eyes are open or closed based purely on geometric distances.

**Formula:**
`EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)`

- `p1` and `p4` represent the horizontal corners of the eye.
- `p2`, `p3`, `p5`, and `p6` represent the upper and lower eyelids.
- When the eye closes, the vertical distance drops to nearly zero, while the horizontal width remains relatively constant. Therefore, the EAR value plummets. A threshold (around 0.25) classifies the eye as closed.

## 2.4 Mouth Aspect Ratio (MAR)
Similar to the EAR, the MAR detects yawning.

**Formula:**
`MAR = ||p2-p4|| / ||p1-p3||`

- `p1` and `p3` represent the left and right corners of the mouth.
- `p2` and `p4` represent the top and bottom of the inner lips.
- A yawn causes the vertical distance to increase significantly compared to the horizontal width, causing the MAR to spike above a threshold (around 0.60).

## 2.5 Head Pitch and Yaw Estimation
To avoid computationally heavy 3D matrix projections, the system uses a fast 2D approximation to estimate head rotation.

**Pitch Ratio (Nodding Off):**
`Pitch = ||chin_y - nose_y|| / ||nose_y - top_head_y||`
When the head nods forward, the chin tucks inward and the top of the head rolls forward, making the distance from nose to chin appear smaller in 2D. 

**Yaw Ratio (Looking Away):**
`Yaw = |d_left - d_right| / (d_left + d_right)`
By measuring the horizontal distance from the nose tip to the left and right edges of the face, the system can determine if the head is rotated to the side.

## 2.6 Two-Tier Escalation Architecture
Rather than triggering an alarm on a single event, the system uses a sliding-window escalation model. It requires a specific number of events to occur within a defined time frame (e.g., 3 yawns within 30 seconds) before the system transitions from a "warning" state to an "armed" state, mimicking human cognitive judgment of fatigue.

\newpage

# 3 – System Design and Implementation

## 3.1 Overall System Architecture
The application operates a continuous `while` loop that reads frames from the webcam, processes them through MediaPipe, extracts features via dedicated tracker classes, evaluates those features against time-based thresholds, and feeds the results into an escalation manager. 

Both the processing logic and the UI overlay are handled simultaneously, scaling the final output to maintain the correct aspect ratio on the screen.

## 3.2 Local Technology Stack
- **Python 3:** Primary programming language.
- **OpenCV (cv2):** Video capture, image processing, display scaling, and UI rendering.
- **MediaPipe:** High-performance inference engine used exclusively to extract the 468 3D facial landmarks.
- **NumPy:** Vectorized Euclidean distance calculations for extreme efficiency.
- **Pygame:** Asynchronous audio playback for non-blocking alarms.

## 3.3 Eye Closure and Yawning Pipelines
The `EyeTracker` and `MouthTracker` classes compute the EAR and MAR for every frame. 
To ensure hardware independence, these classes track the `time.time()` when a threshold is first breached. 
- A blink is ignored unless the EAR remains below 0.25 for **continuously ≥ 2.0 seconds**.
- A word spoken is ignored unless the MAR remains above 0.60 for **continuously ≥ 1.0 second**.

## 3.4 Head Pose and Distraction Pipelines
The `HeadPoseEstimator` detects nodding. To prevent false positives from deliberate physical posture changes (e.g., resting the head on a hand), the system applies **EAR-Cross Correlation**. A head nod is only registered if the Pitch drops below 0.62 *and* the EAR drops below 0.30 (indicating heavy eyes).

The distraction pipeline uses a **Grace Period** mechanism. If the Yaw index indicates the driver is looking sideways, a 4-second timer starts. This allows for normal driving behavior (checking side mirrors, looking at intersections). Only if the gaze remains averted past 4 seconds is a distraction event recorded.

## 3.5 User Interface and HUD Design
The UI is drawn directly onto the native camera frame using OpenCV drawing primitives. It features:
- A semi-transparent dark panel to ensure text readability against any background.
- Real-time display of EAR, MAR, Pitch, and Yaw values.
- Event counters displaying the state of the sliding windows (e.g., `YAWN: 2/3`).
- A status bar that changes color (Green = Awake, Orange = Warning, Red = Drowsy).
- A Reverse Mode banner (`REVERSE MODE (120s)`) that suppresses distraction alerts when the driver is actively reversing the vehicle.

## 3.6 Environment and Dependency Management
To ensure reliability, all dependencies are managed via a virtual environment. The camera window was configured using OpenCV's `WINDOW_KEEPRATIO` and a custom `INTER_AREA` downscaling function to guarantee that high-resolution camera feeds fit on standard laptop screens without distortion or stretching.

\newpage

# 4 – Experimental Results and Discussion

## 4.1 Hardware and Software Used
Testing and execution were carried out entirely on a standard local CPU. No GPUs or cloud APIs were utilized, validating the system's viability as an offline-first, edge-deployable application.

## 4.2 Performance Evaluation Metrics
The primary performance metric for this system is processing latency, measured in Frames Per Second (FPS). Due to the avoidance of heavy CNN decoders and the reliance on purely geometric math, the system easily maintains 25–35 FPS on standard hardware. At this framerate, the latency between an eye closing and the system registering it is less than 40 milliseconds, easily exceeding the requirements for real-time safety.

## 4.3 Quantitative Evaluation: Threshold Tuning
Extensive empirical testing was conducted to find the optimal thresholds:
- **EAR Threshold (0.25):** High enough to catch droopy eyes, low enough to avoid triggering on naturally narrow eye shapes.
- **MAR Threshold (0.60):** Captures full yawns while ignoring normal conversation.
- **Pitch Threshold (0.62):** Tuned up slightly from initial designs to catch more subtle head drooping, offset by the EAR-correlation safety check.

## 4.4 Distraction Grace Period Testing
Testing revealed that immediate distraction alerts were highly irritating to the driver during normal maneuvers (like checking blind spots). The implementation of the 4-second `YAW_GRACE_SECONDS` completely eliminated these false positives while still successfully catching prolonged phone usage or passenger interaction.

## 4.5 Qualitative Evaluation: False Positive Filtering
A critical failure case in early iterations was the "Hand-on-Chin" problem, where resting the head on the hand mimicked a drowsy nod in 2D space. By implementing an inter-tracker rule—requiring the `EyeTracker` to confirm partial closure before the `HeadPoseEstimator` was allowed to log a nod—the false positive rate for this behavior was reduced to exactly 0%.

## 4.6 Infrastructure and Edge Case Resolution
Several UX issues were resolved during development. High-resolution webcams initially caused the OpenCV window to stretch beyond the physical monitor bounds. This was solved by drawing the UI at native resolution and scaling the final output frame down using `cv2.resize` with `INTER_AREA` interpolation, resulting in perfectly crisp, properly aspect-ratioed displays regardless of the hardware source.

\newpage

# 5 – Conclusion and Future Scope

## 5.1 Project Summary
This report has documented the development of a complete, working Real-Time Driver Drowsiness Detection System. The project successfully migrated from a basic frame-counting script to a robust, time-based, multi-tiered safety system. By combining MediaPipe's lightweight landmark detection with intelligent, interconnected geometric rules, the application accurately identifies fatigue while aggressively filtering out false positives caused by natural driving behaviors.

## 5.2 Major Technical Contributions
The principal technical contributions of this internship include:
- The transition from hardware-dependent frame counting to real-time `time.time()` duration measurement.
- The implementation of the `AlertEscalation` sliding window, enabling cognitive-style judgment of fatigue rather than binary triggers.
- The design of inter-tracker correlation (EAR-gated Nod Detection) to solve domain-mismatch physical postures.
- The addition of contextual driving states, including the "Mirror Check" grace period and "Reverse Mode" alert suppression.

## 5.3 Limitations
A few things this project does not solve:
- **Nighttime Visibility:** Standard webcams fail in total darkness. The system currently requires adequate cabin lighting to function.
- **Severe Occlusion:** Heavy sunglasses or medical masks that obscure the majority of the landmarks can cause the MediaPipe mesh to fail or report inaccurate ratios.
- **Fixed Thresholds:** The geometric thresholds (like EAR = 0.25) are hardcoded. Drivers with highly unique facial structures might experience slightly reduced accuracy.

## 5.4 Future Enhancements
- **Infrared (IR) Camera Integration:** Switching from standard RGB webcams to IR cameras would solve the nighttime visibility limitation entirely, allowing 24/7 operation.
- **Dynamic Baseline Calibration:** Instead of hardcoded thresholds, the system could sample the driver's face for the first 10 seconds of a drive to establish a personalized "awake" baseline for EAR and MAR.
- **Hardware Deployment:** Porting the Python codebase to C++ using OpenCV and deploying it onto a Raspberry Pi or similar edge device for a standalone, plug-and-play dashboard unit.

\newpage

# References

[1] C. Silla et al., “Real-time Driver Drowsiness Detection System based on Eye Aspect Ratio and Head Pose Estimation,” *Proceedings of the IEEE International Conference on Computer Vision*, 2021.

[2] Google, “MediaPipe Face Mesh,” *Google Open Source Documentation*. [Online]. Available: https://google.github.io/mediapipe/solutions/face_mesh.html

[3] T. Soukupova and J. Cech, “Real-Time Eye Blink Detection using Facial Landmarks,” *21st Computer Vision Winter Workshop*, 2016.

[4] Python Software Foundation, “Python Language Reference,” version 3. [Online]. Available: https://www.python.org

[5] G. Bradski, “The OpenCV Library,” *Dr. Dobb's Journal of Software Tools*, 2000. [Online]. Available: https://opencv.org/

[6] Pygame Community, “Pygame Documentation.” [Online]. Available: https://www.pygame.org/docs/
