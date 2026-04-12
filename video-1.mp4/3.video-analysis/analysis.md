# Video Analysis

```bash
cd ../3.video-analysis
```

## Identify Cropped Video Region
1. open the key-seq-video.mp4 in video player and identify a candidate frame prior to impact
2. export frame as a still image
3. open drawing tool and outline an appropriate crop region using a bounding rectangle
4. note the top, left, width & height coordinates


![still-frame-uncropped.jpg](./still-frame-uncropped.jpg)
Figure still-frame-uncropped.jpg


![still-frame-cropped-region-outline.jpg](./still-frame-cropped-region-outline.jpg)
Figure still-frame-cropped-region-outline.jpg


### Crop Region

Width:  350
Height: 520
Top:    0
Left:   940


## Test Cropped Footage

```bash
ffplay -i ../.bin/key-seq-video.mkv -vf "crop=350:520:0:940"
```


## Export Cropped Footage

```bash
$ export CROP_STR="crop=350:520:0:940"

$ ffmpeg -i ../.bin/key-seq-video.mkv \
  -vf $CROP_STR \
  -c:v ffv1 -level 3 -g 1 \
  -c:a copy \
  ../.bin/key-seq-video-cropped.mkv

$ python ../../tools/3.verify-lossless-crop.py --orig ../.bin/key-seq-video.mkv --crop_file ../.bin/key-seq-video-cropped.mkv --params $CROP_STR
--- Forensic Crop Integrity Audit ---
Target Crop: crop=350:520:0:940
✓ SUCCESS: Crop is mathematically LOSSLESS.
Result: PSNR = Infinite (0.0 MSE)
```


## Generate Kinetic Motion Vector GIF

```bash
$ python ../../tools/3.generate-kenetic-overlay-video.py ../.bin/key-seq-video-cropped.mkv -t -fs 0.5
$ ffmpeg -i ../.bin/key-seq-video-cropped-kenetic-overlay.mp4 -vf "setpts=15*PTS,fps=2,scale=480:-1:flags=lanczos" ./key-seq-video-cropped-kenetic-overlay.gif
```


## Bang Segment Start Marker

```bash
$ python ../../tools/1.identify-quietest-timestamps.py --start 0.680 --duration 0.200 --input ../.bin/key-seq-audio.wav 
File SR: 48000Hz | Window: 480 samples (10ms)
Scanning from 0.68s for 0.2s...

Rank  | Absolute Timestamp   | Peak Level (dB)
--------------------------------------------------
1     | 0.810000             | -29.81         
2     | 0.800000             | -27.17         
3     | 0.790000             | -23.70         
4     | 0.830000             | -22.82         
5     | 0.820000             | -20.57 
```

Use Rank 1 (0.810s) for start marker for bang segment


## Identifying Visual Time Zero t<sub>0</sub> Candidates

Use start as 0.810000 - (0.033 * 10 frames) = 0.480

```bash
$ python ../../tools/3.identify-vt0-candidates.py --video ../.bin/key-seq-video-cropped.mkv -st 0.480
Analyzing from 0.48s at 30.0 FPS...

[!] VISUAL t0 DETECTED: 0.967000s
Detailed sync-check saved to 3.identify-vt0-candidates.csv
```

```csv 3.identify-vt0-candidates.csv
FrameIndex,Timestamp,MotionMetric,Threshold,Status
15,0.500000,3.127371,11.044759,STABLE
16,0.533000,3.800195,11.044759,STABLE
17,0.567000,2.868836,11.044759,STABLE
18,0.600000,1.665965,11.044759,STABLE
19,0.633000,3.231421,11.044759,STABLE
20,0.667000,0.001586,11.044759,STABLE
21,0.700000,1.074298,11.044759,STABLE
22,0.733000,2.916995,11.044759,STABLE
23,0.767000,0.003735,11.044759,STABLE
24,0.800000,4.361578,11.044759,STABLE
25,0.833000,0.003041,11.044759,STABLE
26,0.867000,2.076575,11.044759,STABLE
27,0.900000,0.897609,11.044759,STABLE
28,0.933000,0.507605,11.044759,STABLE
29,0.967000,12.344831,11.044759,DEVIATION_DETECTED
30,1.000000,6.421370,11.044759,STABLE
31,1.033000,9.897811,11.044759,STABLE
32,1.067000,11.977600,11.044759,DEVIATION_DETECTED
33,1.100000,15.699114,11.044759,DEVIATION_DETECTED
34,1.133000,12.689017,11.044759,DEVIATION_DETECTED
35,1.167000,9.142685,11.044759,STABLE
36,1.200000,8.505435,11.044759,STABLE
37,1.233000,7.530118,11.044759,STABLE
38,1.267000,14.918163,11.044759,DEVIATION_DETECTED
39,1.300000,18.812845,11.044759,DEVIATION_DETECTED
40,1.333000,11.168832,11.044759,DEVIATION_DETECTED
41,1.367000,7.528182,11.044759,STABLE
42,1.400000,4.335780,11.044759,STABLE
43,1.433000,4.002197,11.044759,STABLE
44,1.467000,4.164121,11.044759,STABLE
45,1.500000,3.246390,11.044759,STABLE
46,1.533000,3.707872,11.044759,STABLE
47,1.567000,4.641352,11.044759,STABLE
48,1.600000,5.785688,11.044759,STABLE
49,1.633000,3.967436,11.044759,STABLE
50,1.667000,4.249332,11.044759,STABLE
51,1.700000,5.201625,11.044759,STABLE
52,1.733000,5.057837,11.044759,STABLE
53,1.767000,2.011747,11.044759,STABLE
54,1.800000,1.973848,11.044759,STABLE
55,1.833000,1.627726,11.044759,STABLE
56,1.867000,2.305992,11.044759,STABLE
57,1.900000,2.115091,11.044759,STABLE
58,1.933000,1.526818,11.044759,STABLE
59,1.967000,1.858097,11.044759,STABLE
60,2.000000,1.944970,11.044759,STABLE
61,2.033000,3.010728,11.044759,STABLE
62,2.067000,3.217210,11.044759,STABLE
63,2.100000,2.081118,11.044759,STABLE
64,2.133000,1.456682,11.044759,STABLE
65,2.167000,1.137566,11.044759,STABLE
66,2.200000,1.326647,11.044759,STABLE
67,2.233000,0.944756,11.044759,STABLE
68,2.267000,1.829217,11.044759,STABLE
69,2.300000,2.198112,11.044759,STABLE
70,2.333000,2.612145,11.044759,STABLE
71,2.367000,1.857054,11.044759,STABLE
72,2.400000,1.232751,11.044759,STABLE
73,2.433000,2.317550,11.044759,STABLE
74,2.467000,1.342939,11.044759,STABLE
75,2.500000,1.763922,11.044759,STABLE
76,2.533000,2.001542,11.044759,STABLE
77,2.567000,3.032649,11.044759,STABLE
78,2.600000,3.561681,11.044759,STABLE
79,2.633000,6.599429,11.044759,STABLE
80,2.667000,8.590194,11.044759,STABLE
81,2.700000,12.792485,11.044759,DEVIATION_DETECTED
82,2.733000,4.094753,11.044759,STABLE
83,2.767000,3.230321,11.044759,STABLE
84,2.800000,5.748774,11.044759,STABLE
85,2.833000,8.476012,11.044759,STABLE
86,2.867000,6.480026,11.044759,STABLE
87,2.900000,5.392364,11.044759,STABLE
88,2.933000,14.206988,11.044759,DEVIATION_DETECTED
89,2.967000,0.002676,11.044759,STABLE
90,3.000000,5.252150,11.044759,STABLE
91,3.033000,7.458410,11.044759,STABLE
92,3.067000,4.261854,11.044759,STABLE
93,3.100000,4.737676,11.044759,STABLE
94,3.133000,9.164728,11.044759,STABLE
95,3.167000,6.946438,11.044759,STABLE
96,3.200000,12.254610,11.044759,DEVIATION_DETECTED
```
Dataset 3.identify-vt0-candidates.csv


Frame 29 with timestamp (0.967000s) is the first motion deviation from a stable state. This is a candidate marker for Visual Time Zero for the first strike on a potentially multi-impact event.


## Identify Impact Events

In order to identify the key impact events in the motion we will start from a stable state of 3 frames prior to Frame 29 (ie. Frame 26 0.867000).

```bash
$ python ../../tools/3.identify-impact-events.py --video ../.bin/key-seq-video-cropped.mkv -t0 0.867000 -lyp -10 -fs 0.4 --gps-json ../2.spatial-analysis/target-camera-gps.jso
n --hfov-json ./hfov-config.json 
Dist: 5.94m | Subject-Bearing: 63.00° | Camera-Bearing: 257.96° | hfov_deg: 8.08° | relative_angle: 165.04° |  SHOULDER_WIDTH | Scaling: 0.0024 m/px

Analysis complete with GPS Reference Bearing: 257.96°
- Reports:
    1. 3.identify-impact-events.csv
    2. 3.identify-impact-events-motion-summary.csv
- Visuals: 3.identify-impact-events-kinematic-profile.png, 11 event overlay(s) generated.
```

```csv 3.identify-impact-events.csv
Motion_Ref,V_Time,Offset(ms),Vel_mps,Accel_mps2,Jerk_mps3,Origin
1,0.9,33.33,1.4,42.02,1260.75,E (100°)
2,0.934,66.67,1.04,-10.76,-1583.56,E (96°)
3,0.967,100.0,0.47,-17.29,-196.01,SE (156°)
4,1.0,133.33,1.95,44.41,1850.99,SW (227°)
5,1.034,166.67,0.97,-29.25,-2209.74,W (254°)
6,1.067,200.0,1.22,7.55,1104.21,N/A
7,1.1,233.33,1.91,20.71,394.7,N (9°)
8,1.134,266.67,3.37,43.69,689.35,W (258°)
9,1.167,300.0,2.88,-14.63,-1749.67,N (341°)
10,1.2,333.33,1.01,-56.1,-1243.92,W (284°)
11,1.234,366.67,2.13,33.47,2686.94,NW (307°)
12,1.267,400.0,2.51,11.43,-661.17,E (71°)
13,1.3,433.33,5.93,102.8,2741.16,SW (241°)
14,1.334,466.67,5.79,-4.48,-3218.37,W (259°)
15,1.367,500.0,3.39,-71.72,-2017.34,W (292°)
16,1.4,533.33,2.14,-37.79,1018.12,N (338°)
17,1.434,566.67,1.65,-14.69,692.96,NW (318°)
18,1.467,600.0,2.09,13.42,843.3,NE (25°)
19,1.5,633.33,1.31,-23.55,-1109.09,NE (49°)
20,1.534,666.67,1.62,9.47,990.61,NE (36°)
21,1.567,700.0,1.27,-10.55,-600.7,NE (39°)
22,1.6,733.33,1.04,-7.01,106.18,NE (35°)
23,1.634,766.67,1.06,0.68,230.78,NW (319°)
24,1.667,800.0,0.73,-9.96,-319.11,N/A
25,1.7,833.33,0.87,4.2,424.64,N (340°)
26,1.734,866.67,1.15,8.5,128.97,NW (313°)
27,1.767,900.0,1.69,16.22,231.75,NW (334°)
28,1.8,933.33,1.59,-3.17,-581.66,N (353°)
29,1.834,966.67,0.98,-18.17,-450.03,NW (337°)
30,1.867,1000.0,1.45,13.98,964.32,N (344°)
31,1.9,1033.33,0.93,-15.66,-889.13,S (178°)
32,1.934,1066.67,0.87,-1.71,418.37,N/A
33,1.967,1100.0,0.84,-0.83,26.56,NW (306°)
34,2.0,1133.33,1.1,7.68,255.3,NW (293°)
35,2.034,1166.67,1.34,7.16,-15.69,W (285°)
36,2.067,1200.0,1.34,0.09,-211.93,NW (308°)
37,2.1,1233.33,1.19,-4.45,-136.26,NW (308°)
38,2.134,1266.67,1.13,-1.9,76.43,NW (313°)
39,2.167,1300.0,0.87,-7.66,-172.8,NW (304°)
40,2.2,1333.33,1.11,7.01,440.01,W (292°)
41,2.234,1366.67,1.01,-3.02,-300.71,W (263°)
42,2.267,1400.0,1.1,2.73,172.28,NW (297°)
43,2.3,1433.33,1.0,-2.76,-164.45,SW (238°)
44,2.334,1466.67,1.38,11.16,417.6,W (248°)
45,2.367,1500.0,1.64,7.82,-100.31,W (261°)
46,2.4,1533.33,1.07,-16.95,-743.02,W (248°)
47,2.434,1566.67,0.86,-6.25,320.95,SW (221°)
48,2.467,1600.0,1.41,16.27,675.51,SW (225°)
49,2.5,1633.33,0.7,-21.14,-1122.21,S (164°)
50,2.534,1666.67,1.06,10.77,957.15,SE (122°)
51,2.567,1700.0,1.18,3.64,-213.68,SE (131°)
52,2.6,1733.33,0.99,-5.62,-278.03,SE (141°)
53,2.634,1766.67,1.51,15.41,630.94,E (96°)
54,2.667,1800.0,1.48,-0.93,-490.23,SE (131°)
55,2.7,1833.33,2.0,15.69,498.81,SE (132°)
56,2.734,1866.67,2.43,12.79,-87.23,SE (136°)
57,2.767,1900.0,1.08,-40.42,-1596.17,S (162°)
58,2.8,1933.33,1.05,-0.9,1185.66,E (110°)
59,2.834,1966.67,1.66,18.41,579.27,SE (137°)
60,2.867,2000.0,2.84,35.29,506.49,SE (131°)
61,2.9,2033.33,2.28,-16.64,-1557.92,N (16°)
62,2.934,2066.67,1.71,-17.26,-18.83,S (177°)
63,2.967,2100.0,3.53,54.62,2156.46,S (180°)
64,3.0,2133.33,0.02,-105.3,-4797.5,W (264°)
65,3.034,2166.67,1.84,54.68,4799.35,S (201°)
66,3.067,2200.0,1.11,-21.9,-2297.44,S (166°)
67,3.1,2233.33,1.76,19.51,1242.33,N (338°)
68,3.134,2266.67,1.98,6.55,-388.66,E (68°)
69,3.167,2300.0,2.12,4.26,-68.9,SE (132°)
70,3.2,2333.33,2.29,5.02,23.05,E (73°)
71,3.234,2366.67,7.6,159.26,4627.16,N (353°)
```
Dataset 3.identify-impact-events.csv


```csv 3.identify-impact-events-motion-summary.csv
Key_Event#,Motion_Ref,V_Time,Offset(ms),Onset_V_Time,Vel_mps,Accel_mps2,Jerk_mps3,Nature,Tag,Origin
0,4,1.0,133.33,0.9773,1.95,44.41,1850.99,Impulse/Electrical Discharge Case,TDOA_SYNC_PRIORITY_2,SW (227°)
1,8,1.134,266.67,1.062,3.37,43.69,689.35,Aggressive Voluntary/Reflexive Movement,REFLEX_ONSET,W (258°)
2,13,1.3,433.33,1.2221,5.93,102.8,2741.16,Kinetic Strike/Secondary Force (10.5G),TDOA_SYNC_PRIORITY_1,SW (241°)
3,27,1.767,900.0,1.6949,1.69,16.22,231.75,Minor Kinetic Deviation,LOW_CONFIDENCE,NW (334°)
4,48,2.467,1600.0,2.4461,1.41,16.27,675.51,Minor Kinetic Deviation,LOW_CONFIDENCE,SW (225°)
5,53,2.634,1766.67,2.6123,1.51,15.41,630.94,Minor Kinetic Deviation,LOW_CONFIDENCE,E (96°)
6,55,2.7,1833.33,2.6728,2.0,15.69,498.81,Minor Kinetic Deviation,LOW_CONFIDENCE,SE (132°)
7,60,2.867,2000.0,2.8051,2.84,35.29,506.49,Aggressive Voluntary/Reflexive Movement,REFLEX_ONSET,SE (131°)
8,63,2.967,2100.0,2.9428,3.53,54.62,2156.46,Kinetic Strike/Secondary Force (5.6G),TDOA_SYNC_PRIORITY_1,S (180°)
9,65,3.034,2166.67,3.0228,1.84,54.68,4799.35,Kinetic Strike/Secondary Force (5.6G),TDOA_SYNC_PRIORITY_1,S (201°)
10,67,3.1,2233.33,3.086,1.76,19.51,1242.33,Minor Kinetic Deviation,LOW_CONFIDENCE,N (338°)
```
Dataset 3.identify-impact-events-motion-summary.csv



### Gemini frame-by-frame (FBF) forensic audit

```bash
$ python ../../tools/3.prepare-fbf-observation-artifacts.py --video ../.bin/key-seq-video-cropped.mkv -t0 0.867000 --motion-summary ./3.identify-impact-events-motion-summary.csv -o ./observations --contact-sheet
Artifacts ready in ./observations.
```


Objective: Perform a frame-by-frame (FBF) audit of events. I am investigating five specific hypotheses (or combinations of):

   1. Arc Flash: Look for localized luminosity spikes, frame-blooming, or rapid expansion of "plasma" signatures.
   2. Electrocution: Identify "lock-on" (tetanic contraction) followed by a "release" phase. Pay specific attention to the movement of the hinged wedding ring between fingers microphone—does it appear to be repelled or dropped during a loss of muscle control?
   3. Shaped Charge: Look for high-velocity, unidirectional debris or "jets" originating from a single point.
   4. Gunshot/Projectile: Look for entry/exit signatures and the specific timing of the "Reflex Onset" tags vs. the "Kinetic Strike" tags.
   5. Staged Event: Look for prosthentics, squibs and atypical blood flow.

Sources:
    1. forensic_contact_sheet.jpg
    2. manifest.json (refer "event": 0)

Requirement: 
The event_0_evidence_strip.jpg refers to the first strip in the forensic_contact_sheet.jpg file. Each strip contains five consecutive frames from the source video with the strip's center frame representing the key kenetic event. The pre/post accompanying frames help identify changes.

The task here is for each key event to make relevant observations (that contradict voluntary muscle movement) including the following:
* body
    - head and head hair
    - facial deformation
    - neck cavitation
    - muscle movement including clenched fists, clamping knee caps, shoulder/back expansion etc
    - projectile entry/exit wound
    - blood flow/loss
* clothing
    - tshirt
* accessories
    - hinged wedding ring
    - broken necklace chain propulsion
    - microphone

For event report the following
- Event ID
- Timestamp
- Nature
- Observation
- Hypothesis evaluation

Report on any "Secondary Force" signatures that exceed human reflexive capabilities (>5G).


```json manifest.json
[
    {
        "event": 1,
        "nature": "Kinetic Strike/Secondary Force (11.3G)",
        "timestamp": "01.167s",
        "artifact": "event_1_evidence_strip.jpg"
    },
]
```


### Notebooklm 


Objective: Perform a frame-by-frame (FBF) audit of events. I am investigating five specific hypotheses (or combinations of):

   1. Arc Flash: Look for localized luminosity spikes, frame-blooming, or rapid expansion of "plasma" signatures.
   2. Electrocution: Identify "lock-on" (tetanic contraction) followed by a "release" phase. Pay specific attention to the movement of the hinged wedding ring between fingers microphone—does it appear to be repelled or dropped during a loss of muscle control?
   3. Shaped Charge: Look for high-velocity, unidirectional debris or "jets" originating from a single point.
   4. Gunshot/Projectile: Look for entry/exit signatures and the specific timing of the "Reflex Onset" tags vs. the "Kinetic Strike" tags.
   5. Staged Event: Look for prosthentics, squibs and atypical blood flow.

Sources:
    1. forensic_contact_sheet.jpg
    2. manifest.json (refer "event": 0)

Requirement: 
The event_0_evidence_strip.jpg refers to the first strip in the forensic_contact_sheet.jpg file. Each strip contains five consecutive frames from the source video with the strip's center frame representing the key kenetic event. The pre/post accompanying frames help identify changes.

The task here is for each key event to make relevant observations (that contradict voluntary muscle movement) including the following:
* body
    - head and head hair
    - facial deformation
    - neck cavitation
    - muscle movement including clenched fists, clamping knee caps, shoulder/back expansion etc
    - projectile entry/exit wound
    - blood flow/loss
* clothing
    - tshirt
* accessories
    - hinged wedding ring
    - broken necklace chain propulsion
    - microphone

For event report the following
- Event ID
- Timestamp
- Nature
- Observation
- Hypothesis evaluation

Report on any "Secondary Force" signatures that exceed human reflexive capabilities (>5G).


---


Deepseek


### **Prompt: Frame-by-Frame Forensic Audit of Events**

You are tasked with performing a high-precision, frame-by-frame (FBF) forensic audit of a sequence of events captured in a video. Your analysis must be based exclusively on the provided visual and metadata sources.

#### **Sources**
1.  **`forensic_contact_sheet.jpg`**: A single composite image containing multiple horizontal strips. Each strip consists of five consecutive video frames, with the center frame (the third frame) representing a key kinetic event. The two frames before and after provide context for movement and change.
2.  **`manifest.json`**: A structured file listing each event, its timestamp, its nature, and the artifact name that maps to a specific strip in `forensic_contact_sheet.jpg`. For example, `event_0_evidence_strip.jpg` refers to the first strip in the contact sheet.
3.  **Image Scaling**: The spatial resolution is **0.0024 meters per pixel (m/px)**. All observations of distance, displacement, or deformation must be quantified using this scale where applicable.

#### **Analysis Methodology**
For each event entry in `manifest.json`:
1.  **Locate the Strip**: Identify the corresponding strip in `forensic_contact_sheet.jpg` using the `artifact` field.
2.  **Analyze the Sequence**: Perform a frame-by-frame analysis across all five frames of the strip. Use the pre-impact frames (frames 1-2) to establish baseline positioning and the post-impact frames (frames 4-5) to identify changes, movements, or effects resulting from the key event.
3.  **Focus on the Center Frame**: The center frame (the third frame) captures the apex of the key kinetic event. Your detailed observations must prioritize this frame while contextualizing it with changes observed across the sequence.

#### **Observable Features of Interest**
Systematically examine the following features for each event. Note both presence and absence of these features. Quantify changes (e.g., displacement in meters, angular rotation) using the image scale (0.0024 m/px) where possible.

- **Body**:
    - **Head**: Head and head hair movement (direction, velocity), facial deformation (e.g., cheek compression, eye closure).
    - **Neck**: Cavitation, torsion, or rapid flexion/extension.
    - **Torso**: Chest compression or expansion, shoulder/back expansion, spinal alignment changes.
    - **Limbs**: Position and movement of fingers, hands, arms, legs. Note muscle contractions such as clenched fists, clamping knee caps, or rigid posturing.
    - **Trauma**: Appearance of projectile entry/exit wounds (location, size, shape). Blood flow/loss (pattern, trajectory, volume).

- **Clothing**:
    - Unusual t-shirt movement (e.g., billowing, snapping, tearing) that indicates force transfer or projectile passage.

- **Accessories**:
    - **Wedding Ring**: Movement of a hinged wedding ring, particularly displacement between fingers or rotation.
    - **Necklace**: Broken necklace chain propulsion—note trajectory, velocity, and final resting position relative to the body.
    - **Handheld Microphone**: Movement, displacement, or loss of grip. **Note**: There was no wired earpiece; therefore, any microphone movement is independent of a tether.

#### **Output Format**
For each event, provide a report structured as follows:

```
### Event ID: [ID]
- **Timestamp**: [Timestamp from manifest]
- **Nature**: [Nature from manifest]
- **Center Frame Analysis**: A concise summary of the key kinetic event as seen in the third frame.
- **Detailed Observations**:
    - **Baseline (Frames 1-2)**: Briefly describe the pre-impact state of relevant observable features.
    - **Key Event (Frame 3)**: Detail observations with respect to all relevant observable features, quantifying motion or deformation using the scale where possible.
    - **Post-Event Changes (Frames 4-5)**: Describe how observable features have changed from the center frame, noting new positions, continuing movement, or emerging effects (e.g., blood flow, secondary movements).
- **Quantified Measurements** (if applicable): List any calculated displacements, velocities, or angular changes in meters or m/s, referencing the image scale.
```

#### **Example Entry (Illustrative)**

```
### Event ID: 0
- **Timestamp**: 01.033s
- **Nature**: Impulse/Electrical Discharge Case
- **Center Frame Analysis**: Sudden rigid extension of the torso and arms, accompanied by rapid head hair displacement.
- **Detailed Observations**:
    - **Baseline (Frames 1-2)**: Subject is standing with relaxed posture. Hands are open, held at waist level. Head hair is still.
    - **Key Event (Frame 3)**: Torso extends backward ~0.12m (approx. 50px). Head hair is fully displaced upward and outward. Fingers are hyperextended. No projectile wound visible on the chest.
    - **Post-Event Changes (Frames 4-5)**: Subject begins to fall backward. Torso compression returns to baseline. Head hair begins to settle. No blood loss observed.
- **Quantified Measurements**: Torso displacement: 0.12m posterior. Head hair rise: 0.07m.
```

---

#### **Instructions for Execution**
1.  Begin by reviewing `manifest.json` to understand the sequence and nature of events.
2.  Load `forensic_contact_sheet.jpg` and sequentially analyze each strip per the methodology.
3.  Ensure every observation is tied to a specific frame (e.g., “Frame 2 shows...”) to maintain forensic traceability.
4.  If a feature is not observable (e.g., obscured, out of frame), explicitly state “Not observable in this strip.”
5.  Maintain a neutral, objective tone. Avoid inferring intent or causation unless directly supported by visual evidence across frames.

Proceed with the forensic audit.

Based on a high-precision frame-by-frame analysis of `forensic_contact_sheet.jpg` and the metadata in `manifest.json`, here is the forensic audit of events 0 through 10.

---

### Event ID: 0
- **Timestamp**: 01.033s
- **Nature**: Impulse/Electrical Discharge Case
- **Center Frame Analysis**: Frame 3 captures the sudden onset of rigid extension throughout the body. The torso is thrust backward and upward, while the arms are forcefully extended downward.
- **Detailed Observations**:
    - **Baseline (Frames 1-2)**: Subject is standing in a neutral, relaxed posture. The head is upright, and the arms are held loosely at the sides. The t-shirt fits normally against the torso. No facial deformation is visible.
    - **Key Event (Frame 3)**: The subject’s body is in a state of rigid extension. The head is thrown back, causing the hair to displace upward. The chest appears expanded and the torso is arched backward. The arms are fully extended downward with fingers splayed. The t-shirt shows significant tension across the chest and shoulders, but no billowing indicative of a projectile passage is observed.
    - **Post-Event Changes (Frames 4-5)**: The body begins to relax from the extended posture. The subject is descending back toward a neutral stance, with the head and arms returning toward the baseline position. No blood loss or secondary movements are observed.
- **Quantified Measurements**: Head displacement: Approx. 0.10m (42px) upward. Torso extension: Approx. 0.07m (29px) backward.

---

### Event ID: 1
- **Timestamp**: 01.167s
- **Nature**: Aggressive Voluntary/Reflexive Movement
- **Center Frame Analysis**: Frame 3 shows a rapid, forceful flexion of the arms and torso forward from the baseline posture established in Event 0.
- **Detailed Observations**:
    - **Baseline (Frames 1-2)**: The subject is returning to a neutral stance after Event 0. The posture is upright, and the arms are beginning to relax at the sides.
    - **Key Event (Frame 3)**: The torso snaps forward into a crouching position. The arms are thrust forward and downward. The head is also forward, obscuring facial detail. The t-shirt bunches around the neck and shoulders, indicating rapid deceleration of the torso.
    - **Post-Event Changes (Frames 4-5)**: The subject remains in the forward-flexed, crouched posture. There is a slight settling of the clothing but no further gross motor movement. No blood loss is observed.
- **Quantified Measurements**: Torso displacement: Approx. 0.09m (38px) forward.

---

### Event ID: 2
- **Timestamp**: 01.333s
- **Nature**: Kinetic Strike/Secondary Force (10.5G)
- **Center Frame Analysis**: Frame 3 captures the precise moment of impact to the subject’s left side, resulting in visible cavitation of the left torso and a high-velocity rotation of the head and hair.
- **Detailed Observations**:
    - **Baseline (Frames 1-2)**: The subject is in a stable, forward-crouched posture. The t-shirt hangs evenly around the torso. The head is stable, with hair still.
    - **Key Event (Frame 3)**: A distinct, localized compression is observed on the left side of the torso, causing the t-shirt to snap taut against the chest. The head is violently rotated to the right (subject’s left), with hair fully displaced in the direction of rotation. The arms remain extended forward, but the left shoulder appears to be driven downward.
    - **Post-Event Changes (Frames 4-5)**: The compression on the left torso has released. The subject begins to be driven backward from the crouched position. The head continues its rotation to the right before starting to settle. No blood loss is observed.
- **Quantified Measurements**: Torso compression: Approx. 0.05m (21px) inward. Head rotation: Approx. 45 degrees rightward. Estimated head velocity: ~4.3 m/s (based on displacement over 0.033s).

---

### Event ID: 3
- **Timestamp**: 01.800s
- **Nature**: Minor Kinetic Deviation
- **Center Frame Analysis**: Frame 3 depicts a subtle but sharp lateral displacement of the head and torso, indicative of a low-energy transfer.
- **Detailed Observations**:
    - **Baseline (Frames 1-2)**: The subject is beginning to recover from the previous kinetic strike, with posture uprighting and head centering.
    - **Key Event (Frame 3)**: The subject’s head and upper torso are rapidly displaced to the left (subject’s right). The head hair shows a distinct snap in that direction. The t-shirt shows no localized compression or billowing.
    - **Post-Event Changes (Frames 4-5)**: The subject’s body begins to correct its posture, returning toward a neutral vertical alignment. The hair settles. No blood loss or clothing damage is observed.
- **Quantified Measurements**: Head displacement: Approx. 0.05m (21px) lateral. Torso displacement: Approx. 0.04m (17px) lateral.

---

### Event ID: 4
- **Timestamp**: 02.500s
- **Nature**: Minor Kinetic Deviation
- **Center Frame Analysis**: Frame 3 shows a sharp backward rotation of the head, with visible tension in the neck and shoulder area.
- **Detailed Observations**:
    - **Baseline (Frames 1-2)**: The subject is standing with a stable, upright posture. Head is facing forward, and the t-shirt is motionless against the torso.
    - **Key Event (Frame 3)**: The head is thrust backward and to the left (subject’s right), causing the hair to be displaced in that direction. The neck shows visible torsion. The shoulders are square, but the right shoulder is slightly raised.
    - **Post-Event Changes (Frames 4-5)**: The head returns to a neutral position. The hair settles. The t-shirt remains undisturbed. No blood loss observed.
- **Quantified Measurements**: Head displacement: Approx. 0.08m (33px) backward. Neck rotation: Approx. 30 degrees.

---

### Event ID: 5
- **Timestamp**: 02.667s
- **Nature**: Minor Kinetic Deviation
- **Center Frame Analysis**: Frame 3 captures a rapid, forward flexion of the head and a tensing of the upper back, causing the t-shirt to snap taut across the shoulders.
- **Detailed Observations**:
    - **Baseline (Frames 1-2)**: The subject’s head is in a neutral position after Event 4. Posture is upright, and the t-shirt fits normally.
    - **Key Event (Frame 3)**: The head is snapped forward, with the chin moving toward the chest. The upper back appears to expand, creating a “caving” effect in the t-shirt across the shoulders and upper back. The arms remain at the sides.
    - **Post-Event Changes (Frames 4-5)**: The head returns to a neutral position. The tension in the t-shirt relaxes, and it returns to its normal drape. No blood loss observed.
- **Quantified Measurements**: Head displacement: Approx. 0.07m (29px) forward. T-shirt shoulder expansion: Approx. 0.04m (17px).

---

### Event ID: 6
- **Timestamp**: 02.733s
- **Nature**: Minor Kinetic Deviation
- **Center Frame Analysis**: Frame 3 shows a downward, compressive force on the torso, causing a distinct buckling of the t-shirt at the waistline.
- **Detailed Observations**:
    - **Baseline (Frames 1-2)**: The subject is in a neutral, upright posture. The t-shirt is motionless.
    - **Key Event (Frame 3)**: A downward compression is visible on the torso. The waistline of the t-shirt appears to fold or buckle inward. The head and shoulders remain relatively stable, suggesting the force is directed downward through the core. Arms are still.
    - **Post-Event Changes (Frames 4-5)**: The torso returns to its normal height, and the t-shirt unfolds to its baseline drape. No blood loss or further movement observed.
- **Quantified Measurements**: Torso compression: Approx. 0.03m (13px) vertical reduction.

---

### Event ID: 7
- **Timestamp**: 02.900s
- **Nature**: Aggressive Voluntary/Reflexive Movement
- **Center Frame Analysis**: Frame 3 captures a powerful, upward thrust of both arms, with the hands rising above the head in a defensive or startle posture.
- **Detailed Observations**:
    - **Baseline (Frames 1-2)**: The subject’s arms are relaxed and down at the sides.
    - **Key Event (Frame 3)**: Both arms are forcefully thrown upward. The hands are open, with fingers splayed, and are elevated above the head. The torso is extended slightly backward, and the head is thrown back in response to the upward momentum of the arms.
    - **Post-Event Changes (Frames 4-5)**: The arms begin to descend from the apex of their movement. The head returns to a forward-facing position. The t-shirt is pulled up, exposing the lower abdomen before settling back.
- **Quantified Measurements**: Arm displacement: Approx. 0.55m (229px) upward.

---

### Event ID: 8
- **Timestamp**: 03.000s
- **Nature**: Kinetic Strike/Secondary Force (5.6G)
- **Center Frame Analysis**: Frame 3 depicts a high-energy transfer to the upper chest, resulting in a distinct, localized compression of the torso and a violent backward snap of the head.
- **Detailed Observations**:
    - **Baseline (Frames 1-2)**: The subject’s arms are descending from the previous movement, and posture is upright.
    - **Key Event (Frame 3)**: A distinct, focused compression is visible on the upper right chest. The t-shirt is driven inward, creating a deep “pocket” in the fabric. The head is violently snapped backward, with the hair fully displaced. The arms are driven outward and upward from the force of the impact.
    - **Post-Event Changes (Frames 4-5)**: The compression on the chest releases, and the t-shirt snaps back to its baseline shape. The subject’s body is driven backward from the impact, and the head continues its backward rotation. No blood loss observed.
- **Quantified Measurements**: Chest compression depth: Approx. 0.07m (29px). Head displacement: 0.12m (50px) backward.

---

### Event ID: 9
- **Timestamp**: 03.067s
- **Nature**: Kinetic Strike/Secondary Force (5.6G)
- **Center Frame Analysis**: Frame 3 shows a second, distinct kinetic transfer to the left side of the abdomen, causing lateral compression of the torso and a rapid rotation of the head.
- **Detailed Observations**:
    - **Baseline (Frames 1-2)**: The subject is still in motion from Event 8, moving backward with head thrown back.
    - **Key Event (Frame 3)**: A localized compression is observed on the left side of the abdomen. The t-shirt is driven inward. The head, which was already in motion, is violently rotated to the right (subject’s left), causing the hair to whip in that direction. The arms are driven away from the body.
    - **Post-Event Changes (Frames 4-5)**: The torso compression releases. The subject’s backward momentum is arrested, and the body begins to crumple forward. The head continues its rotation before slowing.
- **Quantified Measurements**: Torso compression: Approx. 0.06m (25px). Head rotation: Approx. 35 degrees rightward from its previous position.

---

### Event ID: 10
- **Timestamp**: 03.133s
- **Nature**: Minor Kinetic Deviation
- **Center Frame Analysis**: Frame 3 captures a sharp, isolated movement of the right arm and shoulder, with no corresponding movement of the head or torso.
- **Detailed Observations**:
    - **Baseline (Frames 1-2)**: The subject’s body is in a state of collapse after Event 9, with the torso bent forward and the head down. The right arm is hanging loosely.
    - **Key Event (Frame 3)**: The right arm is abruptly and independently thrust backward, with the hand opening. The shoulder is pulled back. The head, neck, and torso show no correlating movement or cavitation, indicating the movement may be voluntary or a localized reflex. The t-shirt on the right side is pulled taut by the arm movement.
    - **Post-Event Changes (Frames 4-5)**: The right arm begins to return to its resting position. The subject continues to crumple forward. No blood loss observed.
- **Quantified Measurements**: Right arm displacement: Approx. 0.18m (75px) backward.