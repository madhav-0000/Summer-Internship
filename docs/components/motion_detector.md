# Motion Detector Component

## File: `core/motion.py`

### Concept Breakdown
The **Motion Detector** component acts as a gatekeeper for the driver drowsiness detection system. To optimize resource usage in automotive environments, safety tracking is only active when the vehicle is in motion. 

When the car stops, the system pauses heavy CPU-bound operations (such as MediaPipe Face Mesh landmark detection) and enters a low-resource standby mode. When the vehicle moves again, the system resumes safety tracking immediately.

To handle various hardware configurations, this module supports three operational modes:
1. **Mock File Simulation (`motion_device.json`):** Allows developers and testers to change the vehicle speed/state on-the-fly via a JSON file.
2. **Serial Hardware Interface:** Connects directly to real GPS or OBD-II sensors to retrieve live speed telemetry via NMEA sentences or raw text feeds.
3. **Always-On Fallback:** If no motion sensor (mock file or serial interface) is detected, the system defaults to "Always On" for maximum safety.

### Class: `MotionDetector`
Manages connections to sensors, parses incoming data streams, and caches motion states.

#### `__init__(self, config_path="motion_device.json", serial_port=None, baudrate=9600)`
- **Input:**
  - `config_path` (string): Path to the mock JSON configuration file.
  - `serial_port` (string/None): The serial port identifier (e.g. `'COM3'` or `'/dev/ttyUSB0'`) if a hardware device is attached.
  - `baudrate` (integer): Connection speed for serial telemetry.
- **Behavior:** Attempts to open a non-blocking serial interface if a port is configured. Otherwise, marks the state for mock file detection or fallback.

#### `is_device_attached(self) -> bool`
- **Output:** Returns `True` if a physical serial device is successfully opened OR if `motion_device.json` has `"device_attached": true`. Otherwise, returns `False`.

#### `is_in_motion(self) -> bool`
- **Output:** Returns `True` if the vehicle is moving or if no sensor is attached. Returns `False` if a sensor is attached but reports that the vehicle is stationary.
- **Behavior:** Rate-limits sensor reads (default 5Hz) to minimize CPU overhead.
  - Parses NMEA `$GPRMC` and `$GPVTG` standard GPS sentences for speed in knots/kmh.
  - Parses raw custom speed sentences formatted as `SPEED=X`.
  - Reads mock file configurations if file mode is active.

### Live Calibration & Simulation
To assist with testing in environments without GPS or vehicle interfaces, developers can use the runtime override:
- Pressing **`m`** on the keyboard inside the camera display window cycles between:
  - **`Auto-Detect`**: Uses the hardware or JSON sensor file.
  - **`Force Motion`**: Simulates the car moving (Safety Active).
  - **`Force Standby`**: Simulates the car stopped (Standby Mode).
