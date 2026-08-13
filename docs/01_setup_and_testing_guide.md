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
- **Action:** Look straight at the camera and close your eyes. Keep them closed **continuously for at least 2 seconds**.
- **Expected Result:** The status changes to **"DROWSY (EYES CLOSED)"** and the alarm sounds. You need to trigger this **twice within 45 seconds** for the alarm to arm (the HUD shows `EYE: 1/2` → `EYE: 2/2` → `ARMED`).
- **Note:** A normal blink (< 2 seconds) is completely ignored.

### Test B: Yawn Detection
This feature watches your mouth to detect genuine drowsy yawns.
- **Action:** Open your mouth wide (as in a large yawn) and hold it open for **at least 1 full second**. Repeat this **3 times within 30 seconds**.
- **Expected Result:** Each qualifying yawn increments the HUD counter (`YAWN: 1/3`, `YAWN: 2/3`, `YAWN: 3/3 → ARMED`). On the **4th yawn**, the alarm fires.
- **Note:** Short mouth movements like talking or coughing (under 1 second) are filtered out entirely.

### Test C: Head Drooping (Nodding Off)
This feature tracks head pitch combined with eye state to detect genuine drowsy nods.
- **Action:** Slowly drop your chin towards your chest **while also letting your eyes become heavy / partially closed** (EAR ≤ 0.30). Hold for 1.5 seconds.
- **Expected Result:** The status changes to **"DROWSY (NODDING OFF)"**. Two such events within 45 seconds arm the alarm.
- **Note:** Tilting your head while your eyes are wide open (e.g., resting chin on hand) will **not** count, because the EAR correlation check filters it out.

### Test D: Distraction / Face Lost Detection
This feature detects if you look away from the road for too long.
- **Action:** Turn your head moderately (about 25–30 degrees) to the left or right and **hold it for more than 4 seconds**.
- **Expected Result:**
  - During the first **4 seconds**: status shows **"MIRROR CHECK"** — no penalty (this is the mirror-check grace period).
  - After **4 seconds**: status changes to **"DISTRACTED (LOOKING AWAY)"** and the distraction counter increments.
  - After **2 such events within 60 seconds**, the alarm arms and the next distraction triggers **"DISTRACTED / CAMERA BLOCKED"**.
- **Alternative test:** Cover your camera completely — face loss also increments the distraction counter after ~0.75 s.

### Test E: Reverse Mode
This feature suppresses distraction alerts when the driver is reversing.
- **Action:** With the app running, press the **`r`** key.
- **Expected Result:** A large **amber banner** appears at the top of the frame reading `REVERSE MODE (120s)` with a countdown timer. While active, looking away from the camera does not trigger distraction alerts.
- Press `r` again to deactivate (banner disappears, `FWD` badge returns).
- The mode also auto-disables after 120 seconds.

### Test F: Vehicle Motion & Standby Detection
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
