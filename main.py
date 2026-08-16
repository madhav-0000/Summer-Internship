import cv2
import time
from core.video import VideoStream
from core.mesh import FaceMeshDetector
from core.eyes import EyeTracker
from core.mouth import MouthTracker
from core.pose import HeadPoseEstimator
from core.alerts import AudioAlert
from core.motion import MotionDetector
from core.alert_escalation import AlertEscalation

# --- CONFIGURATION ---
# Eye Aspect Ratio thresholds
EAR_THRESHOLD = 0.25
EAR_FRAMES = 15

# Mouth Aspect Ratio thresholds
MAR_THRESHOLD = 0.6
MAR_FRAMES = 15

# Head Pitch ratio thresholds
PITCH_THRESHOLD = 0.62   # Raised from 0.55 → slightly more sensitive (fires on less head droop)
PITCH_FRAMES = 15
NOD_EAR_CORRELATION = 0.30  # Head nod only counts as drowsy if EAR is also below this value
                             # (filters out deliberate tilts like hand-on-chin where eyes stay open)

# Distraction / Face Lost thresholds
DISTRACTION_FRAMES = 15                # Frames of no-face before recording a distraction event (~0.75s at 20fps)
YAW_THRESHOLD = 0.35                   # Yaw ratio above which the driver is considered distracted (looking away)
YAW_GRACE_SECONDS = 4.0                # How long a sideways glance is tolerated before counting as distraction
                                       # Using real time so the window is accurate at any camera FPS

# --- ESCALATION CONFIGURATION ---
# How many events within what time window before the alarm arms.
# Once armed, every subsequent event triggers the alarm until cooldown expires.
ESCALATION_PROFILES = {
    "yawn":        {"events_required": 3, "window_seconds": 30, "cooldown_seconds": 60},
    "eye_closure": {"events_required": 2, "window_seconds": 45, "cooldown_seconds": 45},
    "head_nod":    {"events_required": 2, "window_seconds": 45, "cooldown_seconds": 45},
    "distraction": {"events_required": 2, "window_seconds": 60, "cooldown_seconds": 60},
}

# Reverse Mode Configuration
REVERSE_MODE_TIMEOUT = 120  # Auto-disable reverse mode after this many seconds (safety net)

# Motion Detection Configuration
MOTION_CONFIG_PATH = "motion_device.json"
MOTION_SERIAL_PORT = None  # Set to port name like 'COM3' or '/dev/ttyUSB0' if using physical GPS

def draw_text(frame, text, position, color=(0, 255, 0), scale=0.7, thickness=2):
    cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness)

def draw_badge(frame, text, top_left, color_bg, color_text=(255, 255, 255), padding=8, scale=0.65, thickness=2):
    """Draws a filled rectangular badge with centered text — used for prominent mode indicators."""
    (tw, th), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
    x, y = top_left
    # Draw filled background rectangle
    cv2.rectangle(frame, (x, y), (x + tw + padding * 2, y + th + padding * 2 + baseline), color_bg, -1)
    # Draw border
    cv2.rectangle(frame, (x, y), (x + tw + padding * 2, y + th + padding * 2 + baseline), (255, 255, 255), 1)
    # Draw text
    cv2.putText(frame, text, (x + padding, y + th + padding), cv2.FONT_HERSHEY_SIMPLEX, scale, color_text, thickness)

def main():
    print("[INFO] Starting video stream...")
    video_stream = VideoStream(src=0)
    
    print("[INFO] Initializing Face Mesh...")
    mesh_detector = FaceMeshDetector()
    
    print("[INFO] Initializing Trackers...")
    eye_tracker = EyeTracker(ear_threshold=EAR_THRESHOLD, ear_frames=EAR_FRAMES, closure_duration_seconds=1.0)
    mouth_tracker = MouthTracker(mar_threshold=MAR_THRESHOLD, mar_frames=MAR_FRAMES, yawn_duration_seconds=1.0)
    pose_tracker = HeadPoseEstimator(pitch_threshold=PITCH_THRESHOLD, pitch_frames=PITCH_FRAMES, droop_duration_seconds=1.5)
    alert_system = AudioAlert()
    motion_detector = MotionDetector(config_path=MOTION_CONFIG_PATH, serial_port=MOTION_SERIAL_PORT)
    escalation = AlertEscalation(profiles=ESCALATION_PROFILES)
    
    print("[INFO] System ready. Press 'q' to quit, 'm' to toggle motion override, 'r' to toggle reverse mode.")

    # Variables for FPS calculation
    pTime = 0
    no_face_frames = 0
    distraction_event_fired = False  # Rising-edge tracker for distraction events
    manual_motion_override = None  # None = sensor, True = force motion, False = force stopped
    reverse_mode = False
    reverse_mode_start = 0  # Timestamp when reverse mode was activated
    yaw_start_time = None  # Timestamp when the driver first looked sideways (None = looking forward)

    # WINDOW_KEEPRATIO prevents stretching when the window is resized
    cv2.namedWindow("Driver Drowsiness Detection", cv2.WINDOW_KEEPRATIO)
    cv2.moveWindow("Driver Drowsiness Detection", 100, 30)  # Keep away from screen edges

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
                        now = time.time()
                        if yaw_start_time is None:
                            yaw_start_time = now  # Start timing the sideways glance
                        elapsed = now - yaw_start_time
                        if elapsed <= YAW_GRACE_SECONDS:
                            # Brief sideways glance — treat as mirror check, suppress detection
                            status_text = "Status: MIRROR CHECK"
                            status_color = (0, 255, 255)  # Cyan
                        else:
                            # Sustained sideways look — count as distraction
                            face_lost_or_distracted = True
                            status_text = "Status: DISTRACTED (LOOKING AWAY)"
                            status_color = (0, 80, 255)  # Orange-red
                        break
                    else:
                        yaw_start_time = None  # Reset timer when looking forward

                    # 2. Eye Tracking
                    ear, eye_event, eye_ongoing = eye_tracker.process(face_landmarks, w, h)
                    draw_text(frame, f"EAR: {ear:.2f}", (10, 30))
                    
                    # 3. Mouth Tracking
                    mar, yawn_event, yawn_ongoing = mouth_tracker.process(face_landmarks, w, h)
                    draw_text(frame, f"MAR: {mar:.2f}", (10, 60))
                    
                    # 4. Head Pose Tracking
                    pitch, nod_event, nod_ongoing = pose_tracker.process(face_landmarks, w, h)
                    draw_text(frame, f"Pitch: {pitch:.2f}", (10, 90))

                    # Record events into escalation system (rising edge only)
                    if eye_event:
                        escalation.record_event("eye_closure")
                    if yawn_event:
                        escalation.record_event("yawn")
                    # Head nod only counts as drowsy if eyes are also partially closing.
                    # This filters out deliberate forward tilts (e.g. hand on chin, leaning forward)
                    # where the driver is still fully awake with eyes wide open.
                    if nod_event and ear <= NOD_EAR_CORRELATION:
                        escalation.record_event("head_nod")

                    # Alert Logic — only trigger if escalation says so
                    if eye_ongoing and escalation.should_alert("eye_closure"):
                        alarm_triggered = True
                        status_text = "Status: DROWSY (EYES CLOSED)"
                    elif yawn_ongoing and escalation.should_alert("yawn"):
                        alarm_triggered = True
                        status_text = "Status: DROWSY (YAWNING)"
                    elif nod_ongoing and escalation.should_alert("head_nod"):
                        alarm_triggered = True
                        status_text = "Status: DROWSY (NODDING OFF)"

                    # We only process the first detected face (driver)
                    break
            else:
                face_lost_or_distracted = True

            # Distraction Alert Counter Logic (converted to event-based)
            # In Reverse Mode, face-lost distraction is suppressed (driver is looking backward)
            if face_lost_or_distracted:
                if reverse_mode:
                    # Suppress distraction alerts in reverse mode
                    no_face_frames = 0
                    distraction_event_fired = False
                else:
                    no_face_frames += 1
                    if no_face_frames > DISTRACTION_FRAMES:
                        # Fire distraction event on rising edge
                        if not distraction_event_fired:
                            escalation.record_event("distraction")
                            distraction_event_fired = True
                        if escalation.should_alert("distraction"):
                            alarm_triggered = True
                            status_text = "Status: DISTRACTED / CAMERA BLOCKED"
            else:
                no_face_frames = 0
                distraction_event_fired = False
        else:
            # Standby mode when car is not in motion
            no_face_frames = 0
            distraction_event_fired = False
            yaw_start_time = None  # Reset grace timer
            # Reset trackers to avoid buffered triggers when resuming
            eye_tracker.closure_frames = 0
            eye_tracker.alarm_on = False
            eye_tracker._event_fired = False
            eye_tracker._closure_start = None  # Reset time-based closure timer
            mouth_tracker.yawn_frames = 0
            mouth_tracker.alarm_on = False
            mouth_tracker._event_fired = False
            mouth_tracker._yawn_start = None  # Reset time-based yawn timer
            pose_tracker.droop_frames = 0
            pose_tracker.alarm_on = False
            pose_tracker._event_fired = False
            pose_tracker._droop_start = None  # Reset time-based droop timer
            # Reset escalation state so we start fresh when car moves again
            escalation.reset()

            alert_system.stop()
            alarm_triggered = False
            status_text = "Status: STANDBY (CAR NOT IN MOTION)"
            status_color = (0, 165, 255) # Orange

            # Draw standby screen overlay
            cv2.rectangle(frame, (0, 0), (w, h), (15, 15, 15), -1)
            cv2.putText(frame, "SYSTEM STANDBY", (w // 2 - 130, h // 2 - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 2)
            cv2.putText(frame, "Car is stopped. Drowsiness detection suspended.", (w // 2 - 220, h // 2 + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        # Run escalation cooldown updates every frame
        if in_motion:
            for cat in ["yawn", "eye_closure", "head_nod", "distraction"]:
                escalation.update(cat)

        # Auto-disable reverse mode after timeout (safety net)
        if reverse_mode and (time.time() - reverse_mode_start) > REVERSE_MODE_TIMEOUT:
            reverse_mode = False
            print(f"[INFO] Reverse Mode auto-disabled after {REVERSE_MODE_TIMEOUT}s timeout.")

        if alarm_triggered:
            status_color = (0, 0, 255) # Red
            alert_system.play()
            draw_text(frame, "!!! WAKE UP !!!", (w // 2 - 100, h // 2), (0, 0, 255))
        else:
            # Only call stop if alert was actually running/triggered previously
            if in_motion:
                alert_system.stop()

        # ── Bottom bar: Status text ──────────────────────────────────────────────
        # Draw a semi-transparent dark strip at the bottom for readability
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, h - 40), (w, h), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        draw_text(frame, status_text, (10, h - 12), status_color, scale=0.65)

        # ── Reverse Mode badge (top-centre, highly visible) ──────────────────────
        if reverse_mode:
            remaining = max(0, int(REVERSE_MODE_TIMEOUT - (time.time() - reverse_mode_start)))
            badge_text = f"  REVERSE MODE  ({remaining}s)  "
            (bw, bh), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)
            bx = (w - bw) // 2
            # Filled orange banner across the top
            cv2.rectangle(frame, (0, 0), (w, bh + 20), (0, 100, 200), -1)
            cv2.putText(frame, badge_text, (bx, bh + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
        else:
            # Show a small unobtrusive "FORWARD" label when NOT in reverse
            draw_badge(frame, " FWD ", (w // 2 - 30, 8), (0, 140, 0), scale=0.55, thickness=1)

        # ── Motion Detector badge (top-left area, below metrics) ─────────────────
        motion_state_str = "IN MOTION" if in_motion else "STOPPED"
        if motion_source == "ALWAYS ON":
            motion_badge_text = f" MOTION: ALWAYS ON "
            motion_badge_color = (0, 140, 0)  # Dark green
        elif motion_source == "OVERRIDE":
            if in_motion:
                motion_badge_text = f" OVERRIDE: MOVING "
                motion_badge_color = (0, 120, 200)  # Blue
            else:
                motion_badge_text = f" OVERRIDE: STOPPED "
                motion_badge_color = (0, 80, 180)
        else:  # SENSOR
            if in_motion:
                motion_badge_text = f" SENSOR: {motion_state_str} "
                motion_badge_color = (0, 140, 0)
            else:
                motion_badge_text = f" SENSOR: {motion_state_str} "
                motion_badge_color = (0, 0, 160)
        draw_badge(frame, motion_badge_text, (10, 145), motion_badge_color, scale=0.55, thickness=1)

        # ── Escalation HUD (top-right, with semi-transparent background panel) ──
        if in_motion:
            hud_x = w - 185
            hud_y_start = 8
            hud_item_h = 28
            hud_items = 4
            hud_panel_h = hud_item_h * hud_items + 12
            # Dark background panel so labels are readable on any background colour
            hud_overlay = frame.copy()
            cv2.rectangle(hud_overlay, (hud_x - 8, hud_y_start),
                          (w - 4, hud_y_start + hud_panel_h), (20, 20, 20), -1)
            cv2.addWeighted(hud_overlay, 0.65, frame, 0.35, 0, frame)

            hud_y = hud_y_start + 24
            hud_labels = [
                ("YAWN", "yawn"),
                ("EYE",  "eye_closure"),
                ("NOD",  "head_nod"),
                ("DISTR","distraction"),
            ]
            for label, cat in hud_labels:
                count = escalation.get_event_count(cat)
                required = escalation.get_events_required(cat)
                armed = escalation.is_armed(cat)
                if armed:
                    hud_text = f"{label}: ARMED"
                    hud_color = (0, 80, 255)  # Red-orange
                elif count > 0:
                    hud_text = f"{label}: {count}/{required}"
                    hud_color = (0, 220, 255)  # Bright yellow
                else:
                    hud_text = f"{label}: {count}/{required}"
                    hud_color = (255, 255, 255)  # White — visible on dark panel
                draw_text(frame, hud_text, (hud_x, hud_y), hud_color, scale=0.6, thickness=1)
                hud_y += hud_item_h

        # ── FPS (moved to bottom-right, inside safe area) ─────────────────────────

        # Calculate & display FPS
        cTime = time.time()
        if cTime - pTime > 0:
            fps = 1 / (cTime - pTime)
            pTime = cTime
            draw_text(frame, f"FPS: {int(fps)}", (w - 95, h - 12), (255, 255, 0), scale=0.6, thickness=1)

        # Scale the frame to fit within the display while preserving exact aspect ratio.
        # All drawing happens on the native-resolution frame above; only the final display is scaled.
        MAX_DISPLAY_H = 700  # Leave room for Windows taskbar + title bar
        if h > MAX_DISPLAY_H:
            scale_f = MAX_DISPLAY_H / h
            display_frame = cv2.resize(frame, (int(w * scale_f), MAX_DISPLAY_H), interpolation=cv2.INTER_AREA)
        else:
            display_frame = frame

        # Show frame
        cv2.imshow("Driver Drowsiness Detection", display_frame)

        # Exit on 'q', toggle override on 'm', toggle reverse mode on 'r'
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
        elif key == ord("r"):
            reverse_mode = not reverse_mode
            if reverse_mode:
                reverse_mode_start = time.time()
                print(f"[INFO] Reverse Mode: ON (auto-disables in {REVERSE_MODE_TIMEOUT}s)")
            else:
                print("[INFO] Reverse Mode: OFF")

    print("[INFO] Cleaning up...")
    alert_system.stop()
    mesh_detector.close()
    video_stream.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
