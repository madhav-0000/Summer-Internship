import cv2
import time
from core.video import VideoStream
from core.mesh import FaceMeshDetector
from core.eyes import EyeTracker
from core.mouth import MouthTracker
from core.pose import HeadPoseEstimator
from core.alerts import AudioAlert

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
    
    print("[INFO] System ready. Press 'q' to quit.")

    # Variables for FPS calculation
    pTime = 0
    no_face_frames = 0

    while True:
        frame = video_stream.read()
        if frame is None:
            break

        # Mirror the webcam feed for a more natural view
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        results = mesh_detector.process(frame)
        
        alarm_triggered = False
        status_text = "Status: AWAKE"
        status_color = (0, 255, 0) # Green

        if results.multi_face_landmarks:
            no_face_frames = 0
            for face_landmarks in results.multi_face_landmarks:
                # 1. Eye Tracking
                ear, eye_alarm = eye_tracker.process(face_landmarks, w, h)
                draw_text(frame, f"EAR: {ear:.2f}", (10, 30))
                
                # 2. Mouth Tracking
                mar, mouth_alarm = mouth_tracker.process(face_landmarks, w, h)
                draw_text(frame, f"MAR: {mar:.2f}", (10, 60))
                
                # 3. Head Pose Tracking
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
            no_face_frames += 1
            if no_face_frames > DISTRACTION_FRAMES:
                alarm_triggered = True
                status_text = "Status: DISTRACTED / CAMERA BLOCKED"

        if alarm_triggered:
            status_color = (0, 0, 255) # Red
            alert_system.play()
            draw_text(frame, "!!! WAKE UP !!!", (w // 2 - 100, h // 2), (0, 0, 255))
        else:
            alert_system.stop()

        # Display Status
        draw_text(frame, status_text, (10, h - 20), status_color)

        # Calculate FPS
        cTime = time.time()
        if cTime - pTime > 0:
            fps = 1 / (cTime - pTime)
            pTime = cTime
            draw_text(frame, f"FPS: {int(fps)}", (w - 100, 30), (255, 255, 0))

        # Show frame
        cv2.imshow("Driver Drowsiness Detection", frame)

        # Exit on 'q'
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    print("[INFO] Cleaning up...")
    alert_system.stop()
    mesh_detector.close()
    video_stream.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
