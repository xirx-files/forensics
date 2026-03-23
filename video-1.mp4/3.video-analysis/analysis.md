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
$ python ../../tools/3.identify-impact-events.py --video ../.bin/key-seq-video-cropped.mkv -t0 0.867000 -lyp -10 -fs 0.4 --gps-json ../2.spatial-analysis/target-camera-gps.json --hfov
-json ../2.spatial-analysis/hfov-config.json 
Dist: 5.94m | Subject-Bearing: 63.00° | Camera-Bearing: 257.96° | hfov_deg: 20.28° | relative_angle: 165.04° |  SHOULDER_WIDTH | Scaling: 0.0061 m/px

Analysis complete with GPS Reference Bearing: 257.96°
- Reports:
    1. 3.identify-impact-events.csv
    2. 3.identify-impact-events-motion-summary.csv
- Visuals: 3.identify-impact-events-kinematic-profile.png, 18 event overlay(s) generated.
```

```csv 3.identify-impact-events.csv
Motion_Ref,V_Time,Offset(ms),Vel_mps,Accel_mps2,Jerk_mps3,Origin
1,0.9,33.33,3.55,106.38,3191.49,E (100°)
2,0.934,66.67,2.64,-27.24,-4008.66,E (96°)
3,0.967,100.0,1.18,-43.78,-496.19,SE (156°)
4,1.0,133.33,4.93,112.41,4685.64,SW (227°)
5,1.034,166.67,2.46,-74.05,-5593.79,W (254°)
6,1.067,200.0,3.09,19.12,2795.23,N/A
7,1.1,233.33,4.84,52.43,999.15,N (9°)
8,1.134,266.67,8.53,110.6,1745.04,W (258°)
9,1.167,300.0,7.29,-37.04,-4429.17,N (341°)
10,1.2,333.33,2.56,-142.01,-3148.9,W (284°)
11,1.234,366.67,5.38,84.72,6801.81,NW (307°)
12,1.267,400.0,6.35,28.93,-1673.72,E (71°)
13,1.3,433.33,15.02,260.23,6939.04,SW (241°)
14,1.334,466.67,14.65,-11.34,-8147.06,W (259°)
15,1.367,500.0,8.59,-181.56,-5106.75,W (292°)
16,1.4,533.33,5.41,-95.65,2577.31,N (338°)
17,1.434,566.67,4.17,-37.18,1754.18,NW (318°)
18,1.467,600.0,5.3,33.98,2134.74,NE (25°)
19,1.5,633.33,3.31,-59.61,-2807.58,NE (49°)
20,1.534,666.67,4.11,23.98,2507.65,NE (36°)
21,1.567,700.0,3.22,-26.71,-1520.63,NE (39°)
22,1.6,733.33,2.63,-17.75,268.77,NE (35°)
23,1.634,766.67,2.69,1.73,584.19,NW (319°)
24,1.667,800.0,1.85,-25.2,-807.81,N/A
25,1.7,833.33,2.2,10.63,1074.95,N (340°)
26,1.734,866.67,2.92,21.51,326.47,NW (313°)
27,1.767,900.0,4.29,41.07,586.66,NW (334°)
28,1.8,933.33,4.02,-8.01,-1472.43,N (353°)
29,1.834,966.67,2.49,-45.99,-1139.23,NW (337°)
30,1.867,1000.0,3.67,35.38,2441.1,N (344°)
31,1.9,1033.33,2.35,-39.64,-2250.77,S (178°)
32,1.934,1066.67,2.2,-4.34,1059.06,N/A
33,1.967,1100.0,2.13,-2.1,67.24,NW (306°)
34,2.0,1133.33,2.78,19.44,646.28,NW (293°)
35,2.034,1166.67,3.38,18.12,-39.71,W (285°)
36,2.067,1200.0,3.39,0.24,-536.49,NW (308°)
37,2.1,1233.33,3.02,-11.26,-344.93,NW (308°)
38,2.134,1266.67,2.86,-4.81,193.47,NW (313°)
39,2.167,1300.0,2.21,-19.39,-437.42,NW (304°)
40,2.2,1333.33,2.8,17.74,1113.86,W (292°)
41,2.234,1366.67,2.55,-7.64,-761.22,W (263°)
42,2.267,1400.0,2.78,6.9,436.11,NW (297°)
43,2.3,1433.33,2.54,-6.98,-416.3,SW (238°)
44,2.334,1466.67,3.49,28.26,1057.13,W (248°)
45,2.367,1500.0,4.15,19.8,-253.93,W (261°)
46,2.4,1533.33,2.72,-42.9,-1880.9,W (248°)
47,2.434,1566.67,2.19,-15.82,812.45,SW (221°)
48,2.467,1600.0,3.56,41.18,1710.0,SW (225°)
49,2.5,1633.33,1.78,-53.51,-2840.78,S (164°)
50,2.534,1666.67,2.69,27.25,2422.96,SE (122°)
51,2.567,1700.0,2.99,9.22,-540.92,SE (131°)
52,2.6,1733.33,2.52,-14.24,-703.81,SE (141°)
53,2.634,1766.67,3.82,39.0,1597.19,E (96°)
54,2.667,1800.0,3.74,-2.36,-1240.98,SE (131°)
55,2.7,1833.33,5.06,39.73,1262.7,SE (132°)
56,2.734,1866.67,6.14,32.37,-220.81,SE (136°)
57,2.767,1900.0,2.73,-102.32,-4040.59,S (162°)
58,2.8,1933.33,2.66,-2.27,3001.42,E (110°)
59,2.834,1966.67,4.21,46.61,1466.37,SE (137°)
60,2.867,2000.0,7.19,89.34,1282.14,SE (131°)
61,2.9,2033.33,5.78,-42.11,-3943.75,N (16°)
62,2.934,2066.67,4.33,-43.7,-47.65,S (177°)
63,2.967,2100.0,8.94,138.26,5458.92,S (180°)
64,3.0,2133.33,0.05,-266.56,-12144.53,W (264°)
65,3.034,2166.67,4.66,138.42,12149.2,S (201°)
66,3.067,2200.0,2.82,-55.44,-5815.81,S (166°)
67,3.1,2233.33,4.46,49.39,3144.87,N (338°)
68,3.134,2266.67,5.02,16.59,-983.86,E (68°)
69,3.167,2300.0,5.37,10.78,-174.43,SE (132°)
70,3.2,2333.33,5.8,12.72,58.35,E (73°)
71,3.234,2366.67,19.24,403.16,11713.33,N (353°)
```
Dataset 3.identify-impact-events.csv


```csv 3.identify-impact-events-motion-summary.csv
Key_Event#,Motion_Ref,V_Time,Offset(ms),Onset_V_Time,Vel_mps,Accel_mps2,Jerk_mps3,Nature,Tag,Origin
0,4,1.0,133.33,0.9767,4.93,112.41,4685.64,Kinetic Strike/Secondary Force (11.5G),TDOA_SYNC_PRIORITY_1,SW (227°)
1,8,1.134,266.67,1.0609,8.53,110.6,1745.04,Kinetic Strike/Secondary Force (11.3G),TDOA_SYNC_PRIORITY_1,W (258°)
2,13,1.3,433.33,1.2216,15.02,260.23,6939.04,Kinetic Strike/Secondary Force (26.5G),TDOA_SYNC_PRIORITY_1,SW (241°)
3,18,1.467,600.0,1.4522,5.3,33.98,2134.74,Impulse/Electrical Discharge Case,TDOA_SYNC_PRIORITY_2,NE (25°)
4,20,1.534,666.67,1.5251,4.11,23.98,2507.65,Impulse/Electrical Discharge Case,TDOA_SYNC_PRIORITY_2,NE (36°)
5,27,1.767,900.0,1.6921,4.29,41.07,586.66,Aggressive Voluntary/Reflexive Movement,REFLEX_ONSET,NW (334°)
6,30,1.867,1000.0,1.8535,3.67,35.38,2441.1,Impulse/Electrical Discharge Case,TDOA_SYNC_PRIORITY_2,N (344°)
7,34,2.0,1133.33,1.9733,2.78,19.44,646.28,Minor Kinetic Deviation,LOW_CONFIDENCE,NW (293°)
8,40,2.2,1333.33,2.186,2.8,17.74,1113.86,Minor Kinetic Deviation,LOW_CONFIDENCE,W (292°)
9,44,2.334,1466.67,2.3087,3.49,28.26,1057.13,Aggressive Voluntary/Reflexive Movement,REFLEX_ONSET,W (248°)
10,48,2.467,1600.0,2.4443,3.56,41.18,1710.0,Impulse/Electrical Discharge Case,TDOA_SYNC_PRIORITY_2,SW (225°)
11,50,2.534,1666.67,2.5234,2.69,27.25,2422.96,Impulse/Electrical Discharge Case,TDOA_SYNC_PRIORITY_2,SE (122°)
12,53,2.634,1766.67,2.6104,3.82,39.0,1597.19,Impulse/Electrical Discharge Case,TDOA_SYNC_PRIORITY_2,E (96°)
13,55,2.7,1833.33,2.6704,5.06,39.73,1262.7,Aggressive Voluntary/Reflexive Movement,REFLEX_ONSET,SE (132°)
14,60,2.867,2000.0,2.803,7.19,89.34,1282.14,Kinetic Strike/Secondary Force (9.1G),TDOA_SYNC_PRIORITY_1,SE (131°)
15,63,2.967,2100.0,2.9423,8.94,138.26,5458.92,Kinetic Strike/Secondary Force (14.1G),TDOA_SYNC_PRIORITY_1,S (180°)
16,65,3.034,2166.67,3.0225,4.66,138.42,12149.2,Kinetic Strike/Secondary Force (14.1G),TDOA_SYNC_PRIORITY_1,S (201°)
17,67,3.1,2233.33,3.0851,4.46,49.39,3144.87,Kinetic Strike/Secondary Force (5.0G),TDOA_SYNC_PRIORITY_1,N (338°)
```
Dataset 3.identify-impact-events-motion-summary.csv



### Generate Impact Events Contact Sheet

```bash
tail -n +2 3.identify-impact-events-motion-summary.csv | while IFS=',' read -r Key_Event Motion_Ref V_Time Offset Onset_V_Time Vel_mps Accel_mps2 Jerk_mps3 Nature Tag Origin; do
    
    input_img="3.identify-impact-events-motion-overlay-${Key_Event}.jpg"
    
    label_text="Event #${Key_Event} | Onset: ${Onset_V_Time}s | Time: ${V_Time}s | ${Nature} / ${Tag} | Vel: ${Vel_mps} | Accel: ${Accel_mps2} | Origin: ${Origin}"
    
    convert "$input_img" \
        -gravity South -background white -splice 0x20 \
        -annotate +0+2 "$label_text" miff:-
        done | montage - -tile 1x -geometry +0+0 3.identify-impact-events-motion-overlay-contact-sheet.jpg
```