import cv2
import time
from core.video import VideoStream
from core.mesh import FaceMeshDetector
from core.eyes import EyeTracker
from core.mouth import MouthTracker
from core.pose import HeadPoseEstimator
from core.alerts import AudioAlert
from core.motion import MotionDetector

# --- CONFIGURATION ---
# Eye Aspect Ratio thresholds
EAR_THRESHOLD = 0.25
EAR_FRAMES = 15

# Mouth Aspect Ratio thresholds
MAR_THRESHOLD = 0.6
MAR_FRAMES = 15

# Head Pitch ratio thresholds
PITCH_THRESHOLD = 0.55
PITCH_FRAMES = 15

# Distraction / Face Lost thresholds
DISTRACTION_FRAMES = 30
YAW_THRESHOLD = 0.35  # Yaw ratio above which the driver is considered distracted (looking away)

# Motion Detection Configuration
MOTION_CONFIG_PATH = "motion_device.json"
MOTION_SERIAL_PORT = None  # Set to port name like 'COM3' or '/dev/ttyUSB0' if using physical GPS

def draw_text(frame, text, position, color=(0, 255, 0)):
    cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

def main():
    print("[INFO] Starting video stream...")
    video_stream = VideoStream(src=0)
    
    print("[INFO] Initializing Face Mesh...")
    mesh_detector = FaceMeshDetector()
    
    print("[INFO] Initializing Trackers...")
    eye_tracker = EyeTracker(ear_threshold=EAR_THRESHOLD, ear_frames=EAR_FRAMES)
    mouth_tracker = MouthTracker(mar_threshold=MAR_THRESHOLD, mar_frames=MAR_FRAMES)
    pose_tracker = HeadPoseEstimator(pitch_threshold=PITCH_THRESHOLD, pitch_frames=PITCH_FRAMES)
    alert_system = AudioAlert()
    motion_detector = MotionDetector(config_path=MOTION_CONFIG_PATH, serial_port=MOTION_SERIAL_PORT)
    
    print("[INFO] System ready. Press 'q' to quit, 'm' to toggle motion override.")

    # Variables for FPS calculation
    pTime = 0
    no_face_frames = 0
    manual_motion_override = None  # None = sensor, True = force motion, False = force stopped

    while True:
        frame = video_stream.read()
        if frame is None:
            break

        # Mirror the webcam feed for a more natural view
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Determine motion state
        if manual_motion_override is not None:
            in_motion = manual_motion_override
            motion_source = "OVERRIDE"
        else:
            in_motion = motion_detector.is_in_motion()
            if motion_detector.is_device_attached():
                motion_source = f"SENSOR ({motion_detector.device_attached_type})"
            else:
                motion_source = "ALWAYS ON"

        alarm_triggered = False
        status_text = "Status: AWAKE"
        status_color = (0, 255, 0) # Green

        if in_motion:
            results = mesh_detector.process(frame)
            
            face_lost_or_distracted = False
            
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    # 1. Distraction Yaw Tracking
                    # Landmark 1 is the nose tip, 234 is the left face edge, 454 is the right face edge
                    nose = face_landmarks.landmark[1]
                    left_edge = face_landmarks.landmark[234]
                    right_edge = face_landmarks.landmark[454]
                    
                    d_left = abs(nose.x - left_edge.x)
                    d_right = abs(right_edge.x - nose.x)
                    
                    if (d_left + d_right) > 0:
                        yaw_index = abs(d_left - d_right) / (d_left + d_right)
                    else:
                        yaw_index = 0.0

                    draw_text(frame, f"Yaw: {yaw_index:.2f}", (10, 120))
                    
                    if yaw_index > YAW_THRESHOLD:
                        face_lost_or_distracted = True
                        break

                    # 2. Eye Tracking
                    ear, eye_alarm = eye_tracker.process(face_landmarks, w, h)
                    draw_text(frame, f"EAR: {ear:.2f}", (10, 30))
                    
                    # 3. Mouth Tracking
                    mar, mouth_alarm = mouth_tracker.process(face_landmarks, w, h)
                    draw_text(frame, f"MAR: {mar:.2f}", (10, 60))
                    
                    # 4. Head Pose Tracking
                    pitch, pose_alarm = pose_tracker.process(face_landmarks, w, h)
                    draw_text(frame, f"Pitch: {pitch:.2f}", (10, 90))

                    # Alert Logic
                    if eye_alarm:
                        alarm_triggered = True
                        status_text = "Status: DROWSY (EYES CLOSED)"
                    elif mouth_alarm:
                        alarm_triggered = True
                        status_text = "Status: DROWSY (YAWNING)"
                    elif pose_alarm:
                        alarm_triggered = True
                        status_text = "Status: DROWSY (NODDING OFF)"

                    # We only process the first detected face (driver)
                    break
            else:
                face_lost_or_distracted = True

            # Distraction Alert Counter Logic
            if face_lost_or_distracted:
                no_face_frames += 1
                if no_face_frames > DISTRACTION_FRAMES:
                    alarm_triggered = True
                    status_text = "Status: DISTRACTED / CAMERA BLOCKED"
            else:
                no_face_frames = 0
        else:
            # Standby mode when car is not in motion
            no_face_frames = 0
            # Reset trackers to avoid buffered triggers when resuming
            eye_tracker.closure_frames = 0
            eye_tracker.alarm_on = False
            mouth_tracker.yawn_frames = 0
            mouth_tracker.alarm_on = False
            pose_tracker.droop_frames = 0
            pose_tracker.alarm_on = False

            alert_system.stop()
            alarm_triggered = False
            status_text = "Status: STANDBY (CAR NOT IN MOTION)"
            status_color = (0, 165, 255) # Orange

            # Draw standby screen overlay
            cv2.rectangle(frame, (0, 0), (w, h), (15, 15, 15), -1)
            cv2.putText(frame, "SYSTEM STANDBY", (w // 2 - 130, h // 2 - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 2)
            cv2.putText(frame, "Car is stopped. Drowsiness detection suspended.", (w // 2 - 220, h // 2 + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        if alarm_triggered:
            status_color = (0, 0, 255) # Red
            alert_system.play()
            draw_text(frame, "!!! WAKE UP !!!", (w // 2 - 100, h // 2), (0, 0, 255))
        else:
            # Only call stop if alert was actually running/triggered previously
            if in_motion:
                alert_system.stop()

        # Display Status
        draw_text(frame, status_text, (10, h - 20), status_color)

        # Draw motion status info at bottom-right
        motion_state_str = "MOTION" if in_motion else "STOPPED"
        if motion_source == "ALWAYS ON":
            motion_display_text = f"Motion: {motion_source}"
            motion_color = (0, 255, 0)
        elif motion_source == "OVERRIDE":
            motion_display_text = f"Motion: {motion_source} ({motion_state_str})"
            motion_color = (0, 165, 255)
        else: # SENSOR
            motion_display_text = f"Motion: {motion_source} ({motion_state_str})"
            motion_color = (0, 255, 0) if in_motion else (0, 0, 255)
        draw_text(frame, motion_display_text, (w - 340, h - 20), motion_color)

        # Calculate FPS
        cTime = time.time()
        if cTime - pTime > 0:
            fps = 1 / (cTime - pTime)
            pTime = cTime
            draw_text(frame, f"FPS: {int(fps)}", (w - 100, 30), (255, 255, 0))

        # Show frame
        cv2.imshow("Driver Drowsiness Detection", frame)

        # Exit on 'q', toggle override on 'm'
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("m"):
            if manual_motion_override is None:
                manual_motion_override = True
                print("[INFO] Manual Override: FORCE MOTION")
            elif manual_motion_override is True:
                manual_motion_override = False
                print("[INFO] Manual Override: FORCE STANDBY")
            else:
                manual_motion_override = None
                print("[INFO] Manual Override: OFF (Auto)")

    print("[INFO] Cleaning up...")
    alert_system.stop()
    mesh_detector.close()
    video_stream.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
