import os
import json
import time

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

class MotionDetector:
    """
    Detects if the vehicle is in motion.
    
    Supports:
    1. A mock file 'motion_device.json' for testing/simulation.
    2. A physical hardware serial port connection (e.g. GPS or OBD-II reader) that
       transmits NMEA GPS data (speed in knots/kmh) or simple raw "SPEED=X" lines.
    3. Fallback to 'Always On' (safety mode) if no device is detected or attached.
    """
    def __init__(self, config_path="motion_device.json", serial_port=None, baudrate=9600):
        self.config_path = config_path
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.serial_conn = None
        self.last_check_time = 0
        self.check_interval = 0.2  # Check status 5 times a second
        self.cached_in_motion = True
        self.device_attached_type = "none"

        # Attempt to open serial connection if configured
        if self.serial_port and SERIAL_AVAILABLE:
            try:
                # Open with a short timeout to prevent blocking the main camera loop
                self.serial_conn = serial.Serial(self.serial_port, self.baudrate, timeout=0.05)
                print(f"[INFO] Connected to serial motion sensor on {self.serial_port}")
                self.device_attached_type = "serial"
            except Exception as e:
                print(f"[WARNING] Could not open serial port {self.serial_port}: {e}")

    def is_device_attached(self) -> bool:
        """
        Determines if a motion sensor device is currently attached.
        
        Returns:
            True if either serial port is open, or a valid mock file is configured.
            False otherwise.
        """
        if self.serial_conn and self.serial_conn.is_open:
            self.device_attached_type = "serial"
            return True
            
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    is_attached = data.get("device_attached", False)
                    if is_attached:
                        self.device_attached_type = "mock_file"
                        return True
            except Exception:
                pass
                
        self.device_attached_type = "none"
        return False

    def _parse_nmea_speed(self, nmea_sentence: str) -> float:
        """
        Parses speed from common NMEA sentences: GPRMC, GNVTG, GPVTG, etc.
        Returns speed in km/h, or -1.0 if not parsed.
        """
        # Clean checksum if present
        clean_sentence = nmea_sentence.split('*')[0]
        parts = clean_sentence.split(',')
        if len(parts) < 2:
            return -1.0
            
        sentence_type = parts[0]
        
        # VTG sentence: Track made good and ground speed
        # Example: $GPVTG,054.7,T,,M,015.0,N,028.0,K*4E
        # Index 7 is speed in km/h (preceded by 'K')
        if "VTG" in sentence_type and len(parts) >= 8:
            try:
                if parts[8] == 'K':
                    return float(parts[7])
                elif parts[6] == 'N': # speed in knots
                    return float(parts[5]) * 1.852
            except ValueError:
                pass

        # RMC sentence: Recommended minimum specific GPS/Transit data
        # Example: $GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A
        # Index 7 is speed in knots
        if "RMC" in sentence_type and len(parts) >= 8:
            try:
                # Speed in knots -> convert to km/h
                speed_knots = float(parts[7])
                return speed_knots * 1.852
            except ValueError:
                pass
                
        return -1.0

    def _read_serial_speed(self) -> float:
        """
        Reads lines from the serial port and attempts to parse speed.
        Supports:
        - NMEA GPS sentences (starts with '$')
        - Raw speed text (e.g. "SPEED=15.5")
        Returns:
            The parsed speed in km/h if successful, or None if no speed reading was found.
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            return None
            
        try:
            # Read all available lines up to the buffer limit
            while self.serial_conn.in_waiting > 0:
                line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                    
                # 1. NMEA GPS sentence handling
                if line.startswith('$'):
                    speed = self._parse_nmea_speed(line)
                    if speed >= 0:
                        return speed
                
                # 2. Raw key-value parsing (e.g. "SPEED=12.5")
                elif "SPEED=" in line:
                    try:
                        speed_str = line.split("SPEED=")[1]
                        # Remove non-numeric characters except decimal point
                        clean_speed = "".join(c for c in speed_str if c.isdigit() or c == '.')
                        return float(clean_speed)
                    except (ValueError, IndexError):
                        pass
        except Exception as e:
            print(f"[WARNING] Error reading from serial device: {e}")
            
        return None

    def is_in_motion(self) -> bool:
        """
        Checks if the car is currently in motion.
        
        Returns:
            True if vehicle is in motion, or if no device is attached (safety default).
            False if a device is attached and vehicle is stopped.
        """
        now = time.time()
        # Rate limit checks to minimize CPU and disk/serial overhead
        if now - self.last_check_time < self.check_interval:
            return self.cached_in_motion
            
        self.last_check_time = now

        # Fallback: No device attached -> Always On
        if not self.is_device_attached():
            self.cached_in_motion = True
            return True

        # Mode 1: Real Hardware Serial Device
        if self.device_attached_type == "serial":
            speed = self._read_serial_speed()
            if speed is not None:
                # If speed > 1.0 km/h, consider vehicle in motion (ignoring minor sensor noise)
                self.cached_in_motion = speed > 1.0
                return self.cached_in_motion
            # If no new serial line, return last cached state
            return self.cached_in_motion

        # Mode 2: Mock File Device
        if self.device_attached_type == "mock_file":
            try:
                if os.path.exists(self.config_path):
                    with open(self.config_path, 'r') as f:
                        data = json.load(f)
                        in_motion = data.get("in_motion", True)
                        speed = data.get("speed", 0.0)
                        
                        # In motion if explicitly flagged OR speed is positive
                        self.cached_in_motion = in_motion or (speed > 1.0)
                        return self.cached_in_motion
            except Exception as e:
                # If error reading file, fall back to safe True
                pass

        self.cached_in_motion = True
        return True
