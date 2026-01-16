# Forensic Audio Analysis: Triangulation of Acoustic Event

## 1. Objective
To determine the geographic origin of a loud "bang" event captured on multiple video recording devices during an outdoor event.

## 2. Methodology: Time Difference of Arrival (TDOA)

The primary method used for this analysis is Time Difference of Arrival (TDOA), a technique for locating a sound source by measuring the time it takes for the sound to reach different receivers at known locations.

The core formula is:
```
Distance_to_Source = (Time_Sound_Heard - Time_Event_Seen) * Speed_of_Sound
```
This time difference, or `delta_t`, allows us to calculate the distance from each recording device to the sound's origin.

The analysis requires three key data points for each recording device:
1.  **Device Location:** The precise GPS coordinates of the recording device.
2.  **Visual Time Zero (VTZ):** A precise timestamp from the video file marking the exact moment the bang event was visible (e.g., an impact or flash).
3.  **Audio Arrival Time:** A precise timestamp marking when the bang sound was captured by the device's microphone.

With the calculated distances from several distinct device locations, a mathematical process called **Multilateration** is used to find the single geographic coordinate that best satisfies all measured distances, thereby revealing the source of the sound.

---

## 3. Data Analysis and Preparation

### Step 1: High-Precision Audio Onset Detection

To find the audio arrival time with maximum accuracy, a dedicated analysis script (`onset_analysis.py`) was developed. This script uses a spectral flux algorithm (`librosa.onset.onset_detect`), which is highly effective at identifying the precise start of percussive, non-speech sounds like a bang.

The script produced the following onset times for the bang within each 2-second audio clip:

| Video Source | Bang Start Time (seconds into clip) |
| :--- | :--- |
| video-1.mp4 | 0.7348 |
| video-2.MOV | 0.7348 |
| video-4.mp4 | 0.7464 |
| video-13.mp4 | 0.8857 |
| video-16.mp4 | 0.8857 |
| video-17.mp4 | 0.8625 |
*(Showing only data for the 6 videos with known GPS coordinates)*

### Step 2: Data Consolidation

The final TDOA calculation was performed by a script (`tdoa_analysis.py`) that consolidated data from three sources:
- **Device GPS & VTZ:** Provided in `README.md`.
- **Audio Clip Offset:** Parsed from `exec-instructions-*.md` files (the `-ss` value in the `ffmpeg` command).
- **Audio Onset Time:** The high-precision values from `bang_onset_analysis.csv` (table above).

---

## 4. TDOA Calculation and Results

### Example Calculation: `video-4.mp4`

To illustrate the process, here is the step-by-step calculation for `video-4.mp4`:

1.  **Visual Time Zero (`t_visual`):**
    - From `README.md`: `3.366667` s

2.  **Audio Clip Offset (`t_offset`):**
    - From `exec-instructions-4.mp4.md`: `2.633333` s

3.  **Relative Bang Onset (`t_bang_relative`):**
    - From the table above: `0.746417` s

4.  **Absolute Bang Time (`t_bang_absolute`):**
    - `t_bang_absolute = t_offset + t_bang_relative`
    - `t_bang_absolute = 2.633333 + 0.746417 = 3.379750` s

5.  **Time Delay (`delta_t`):**
    - `delta_t = t_bang_absolute - t_visual`
    - `delta_t = 3.379750 - 3.366667 = 0.013083` s

6.  **Calculated Distance:**
    - `Distance = delta_t * Speed_of_Sound` (using 349.5 m/s from project `README.md`)
    - `Distance = 0.013083 * 349.5 = 4.57` meters

### Triangulation Results

This calculation was repeated for all 6 videos.

- **Data Quality Issues:** `video-1.mp4` and `video-2.MOV` were automatically excluded because their source data produced a negative `delta_t` (implying sound arrived before the visual event), indicating an unresolvable error in their provided VTZ or audio offset times.

The final triangulation was performed using the 4 valid data points:

| Video Source | Calculated Distance to Source |
| :--- | :--- |
| video-4.mp4 | 4.57 meters |
| video-13.mp4 | 6.66 meters |
| video-16.mp4 | 123.12 meters |
| video-17.mp4 | 33.50 meters |

A numerical solver was used to find the coordinate that best fit these four distances.

- **Estimated Location (Local XY): `(x = 41.99m, y = -18.11m)`**
  *(This is relative to the subject, who is at (0, 0))*

---

## 5. Final Result: GPS Coordinate of Source

The local XY coordinate was converted back to geographic coordinates.

- **Subject's Location (Origin):** `40.2775277° N, -111.7140278° W`
- **Estimated Offset:** `+41.99` meters East, `-18.11` meters South

#### The final estimated GPS coordinate for the source of the bang is:

-   **Latitude:** `40.2773648° N`
-   **Longitude:** `-111.7135359° W`

In Degrees, Minutes, Seconds format:
-   **40° 16' 38.513" N**
-   **111° 42' 48.729" W**
