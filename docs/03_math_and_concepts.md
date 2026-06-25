# Mathematical Concepts

## 1. Eye Aspect Ratio (EAR)
The EAR is an elegant mathematical approximation used to determine if a person's eyes are open or closed based purely on geometric distances.

**Formula:**
`EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)`

**How it works:**
- We extract 6 specific landmarks surrounding each eye.
- `p1` and `p4` represent the horizontal corners (left and right edges) of the eye.
- `p2`, `p3` represent the top eyelid, and `p5`, `p6` represent the bottom eyelid.
- The numerator `(||p2-p6|| + ||p3-p5||)` calculates the vertical distance between the upper and lower eyelids.
- The denominator `(2 * ||p1-p4||)` calculates the horizontal width of the eye, scaled by 2 to balance the equation.
- When the eye closes, the vertical distance drops to nearly zero, while the horizontal width remains relatively constant. Therefore, the EAR value plummets. We use a threshold (usually around 0.20 to 0.25) to classify the eye as closed.

### MediaPipe Landmark Indices
We use the following specific indices from the 468 MediaPipe Face Mesh:
- **Left Eye:** `[33, 160, 158, 133, 153, 144]`
- **Right Eye:** `[362, 385, 387, 263, 373, 380]`

## 2. Mouth Aspect Ratio (MAR)
Similar to the EAR, the Mouth Aspect Ratio is a simple geometric calculation used to detect yawning.

**Formula:**
`MAR = ||p2-p4|| / ||p1-p3||`

**How it works:**
- We extract 4 specific landmarks around the inner lips.
- `p1` and `p3` represent the left and right corners of the mouth.
- `p2` and `p4` represent the top and bottom of the inner lips.
- The numerator `||p2-p4||` calculates the vertical distance (mouth opening height).
- The denominator `||p1-p3||` calculates the horizontal width of the mouth.
- Unlike eyes (which close), a yawn causes the vertical distance of the mouth to increase significantly compared to its horizontal width, making the MAR value spike. We use a threshold (usually around 0.6) to classify the mouth state as yawning.

### MediaPipe Landmark Indices
For the inner lips:
- **Left Corner:** `78`
- **Right Corner:** `308`
- **Top:** `13`
- **Bottom:** `14`

## 3. Head Pitch Ratio
To avoid computationally heavy 3D matrix projections, we use a fast 2D approximation to estimate if the driver's head is drooping forward (nodding off).

**Formula:**
`Pitch Ratio = ||chin_y - nose_y|| / ||nose_y - top_head_y||`

**How it works:**
- We extract 3 vertical anchor points: Top of the head (`p1`), Nose tip (`p2`), and Chin (`p3`).
- We look specifically at the Y-coordinates (vertical axis).
- `d_top = p2_y - p1_y` (Distance from top of head to nose).
- `d_bottom = p3_y - p2_y` (Distance from nose to chin).
- `Pitch Ratio = d_bottom / d_top`.
- When looking straight ahead, the ratio is relatively stable. When the driver nods their head forward (droops), the chin tucks inward and the top of the head rolls forward. In a 2D camera projection, this makes `d_bottom` appear smaller and `d_top` appear larger, causing the Pitch Ratio to drop significantly. We use a threshold (around 0.5 to 0.6) to detect this state.

### MediaPipe Landmark Indices
We use the following central vertical landmarks:
- **Top of Head (Forehead):** `10`
- **Nose Tip:** `1`
- **Chin:** `152`

## 4. Distraction & Occlusion Detection
While mathematical ratios like EAR and MAR handle the active geometry of the face, they rely on the face being visible. 

**The Challenge:**
If the driver turns their head 90 degrees away from the camera (extreme profile view) or if a hand covers the face (e.g., adjusting glasses), the MediaPipe Face Mesh model drops the detection entirely because it can no longer map the necessary 468 points.

**The Solution:**
Instead of silently failing, we use the *absence* of data as an indicator.
- We maintain a rolling counter `no_face_frames`.
- Each frame that MediaPipe returns empty (`results.multi_face_landmarks` is None), we increment the counter.
- If a face is found, the counter is reset to zero.
- If the counter exceeds the `DISTRACTION_FRAMES` threshold (typically ~30 frames or 1.5 seconds), the system deduces that the camera is either blocked or the driver is looking completely away from the road, triggering a `DISTRACTED / CAMERA BLOCKED` alarm.
