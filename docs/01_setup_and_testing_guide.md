# Testing Guide: Complete Step-by-Step Instructions

This guide is designed for complete beginners. It will walk you through exactly how to start the Driver Drowsiness Detection System from scratch and how to test each of its features. 

## Step 1: Open Your Terminal
First, you need to open a command-line interface (terminal) on your computer.
- **On Windows:** Press the `Windows Key`, type `cmd` or `PowerShell`, and hit `Enter`.
- **On Mac:** Press `Command + Space`, type `Terminal`, and hit `Enter`.

## Step 2: Navigate to the Project Folder
You need to tell your terminal to look inside the folder where the project is saved. Use the `cd` (change directory) command. 
If your project is saved in a folder called `research internship` on your `C:` drive, type the following command and hit `Enter`:
```bash
cd "C:\research internship"
```

## Step 3: Activate the Virtual Environment (If Applicable)
The virtual environment holds all the necessary code libraries for the program to run. You must activate it before starting the program.

Run the command for your operating system:
- **On Windows (Command Prompt):**
  ```cmd
  venv\Scripts\activate.bat
  ```
- **On Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **On Mac/Linux:**
  ```bash
  source venv/bin/activate
  ```
*(You will know it worked successfully if you see `(venv)` appear at the very beginning of your terminal prompt line.)*

## Step 4: Install Required Libraries
Before running the program, you need to install the code libraries it depends on. Type the following command and hit `Enter`:
```bash
pip install -r requirements.txt
```
*(Wait for the installation to finish. You will see text scrolling by as it downloads.)*

## Step 5: Run the Application
Now that you are in the correct folder and the environment is active, you can start the program. Type this command and hit `Enter`:
```bash
python main.py
```
A new window should pop up showing your webcam feed. You will see a green 3D mesh drawn over your face and numbers (like EAR, MAR, Pitch) updating in the corner.

---

## Step 6: How to Test the Features

Once the video window is open and running, you can perform the following actions to ensure the system detects drowsiness correctly.

### Test A: Eye Closure Detection (Micro-sleep)
This feature monitors your eyes to see if you fall asleep.
- **Action:** Look straight at the camera and close your eyes. Keep them closed for at least 1 to 2 seconds.
- **Expected Result:** The text on the screen should change to **"DROWSY (EYES CLOSED)"** and you should hear a continuous beep sound. Open your eyes to stop the alarm.
- **Troubleshooting:** If the alarm triggers when you just blink normally, you can open the `main.py` file in a text editor and increase the `EAR_FRAMES` number to make it wait longer before alarming.

### Test B: Yawn Detection
This feature watches your mouth to detect wide yawns.
- **Action:** Open your mouth wide, as if you are letting out a large, tired yawn, and hold it open for about a second.
- **Expected Result:** The text on the screen should change to **"DROWSY (YAWNING)"** and the alarm will sound.
- **Troubleshooting:** If talking normally triggers a yawn alarm, open `main.py` and increase the `MAR_THRESHOLD` number slightly so it is less sensitive.

### Test C: Head Drooping (Nodding Off)
This feature tracks the angle of your head to see if you are nodding off.
- **Action:** Start by looking straight forward. Slowly drop your chin down towards your chest, mimicking falling asleep at the wheel.
- **Expected Result:** As your head tilts down, the text should change to **"DROWSY (NODDING OFF)"** and the alarm will sound.
- **Troubleshooting:** If looking down at your keyboard triggers this alarm by mistake, open `main.py` and decrease the `PITCH_THRESHOLD` number so it requires a more extreme head drop.

### Test D: Distraction / Face Lost Detection
This feature detects if you look away from the road (e.g. at a phone or passenger) or if your camera is blocked (e.g., by a hand over your face).
- **Action:** Look straight at the camera, then turn your head moderately (about 25 to 30 degrees) to the left or right, simulating looking away from the road. Hold this position for 1.5 seconds. Alternatively, cover your face completely with your hand.
- **Expected Result:** The "Yaw" value shown on the screen will rise above `0.35` (or face landmarks will be lost). The status text will change to **"Status: DISTRACTED / CAMERA BLOCKED"** and the alarm will sound. Returning your gaze to the road will immediately clear the alert.
- **Troubleshooting:** If the alarm triggers too easily when you scan your mirrors, you can open `main.py` and increase `YAW_THRESHOLD` slightly (e.g. to `0.40`) or increase the `DISTRACTION_FRAMES` count.

### Test E: Vehicle Motion & Standby Detection
This feature optimizes safety checks by only running the camera face mesh processing when the vehicle is actively driving, and entering standby when stopped.

**Method 1: Using the JSON File Simulation (Mock Mode)**
- **Action:**
  1. Open `motion_device.json` in a text editor.
  2. Change `"in_motion"` to `false` and `"speed"` to `0.0`. Save the file.
  3. Start the application. You will see the video feed replaced by a dark screen with the text **"SYSTEM STANDBY"** and a bottom status indicating **"Status: STANDBY (CAR NOT IN MOTION)"** (colored orange). Face landmark detection is now suspended to save CPU resources.
  4. While the application is running, change `"in_motion"` to `true` (or `"speed"` to `20.0`) in `motion_device.json` and save the file.
- **Expected Result:** Within a fraction of a second, the system will wake up, resume video landmarks tracking, and change its state back to **"Status: AWAKE"** (colored green).

**Method 2: Using the Keyboard Toggle Override**
- **Action:**
  1. While the camera window is open and active, press the **`m`** key on your keyboard.
- **Expected Result:**
  - First press: Activates **`Motion: OVERRIDE (MOTION)`** (forces tracking on).
  - Second press: Activates **`Motion: OVERRIDE (STOPPED)`** (forces system standby, suspending face mesh).
  - Third press: Returns to **`Motion: SENSOR`** (auto-detects via the mock file or physical port).

**Method 3: Real Hardware Interface (No Code Modification Needed)**
- **Action:**
  1. Connect your physical serial sensor device (e.g. USB GPS module or OBD-II reader) to the system.
  2. Open `main.py` and set `MOTION_SERIAL_PORT` to your device's connection port (e.g. `'COM3'` on Windows or `'/dev/ttyUSB0'` on Linux).
  3. Start the application. The system will automatically detect the serial device, read incoming speed data (supporting standard NMEA sentences like GPRMC/GPVTG or raw `SPEED=X` lines), and transition between standby and tracking modes automatically as the vehicle moves.
  4. If no device is attached or the mock configuration file is deleted, the system safely defaults to **"Always On"** mode to ensure safety is never compromised.

> [!TIP]
> **Check the Performance:** Look at the "FPS" number in the top corner of the video window. A smooth, real-time experience usually means an FPS of 20 or higher.

## Step 7: Stop the Application
When you are completely finished testing, make sure you have clicked on the video window (so it is highlighted) and press the `q` key on your keyboard. This will safely close the window and stop the program.

To exit the virtual environment in your terminal, simply type this command and hit `Enter`:
```bash
deactivate
```
