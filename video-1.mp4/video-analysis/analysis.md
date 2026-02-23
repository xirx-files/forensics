# Video Analysis

## Identify cropped video region for improved signal to noise ratio
1. open the key-seq-video.mp4 in video player and identify a candidate frame prior to impact
2. export frame as a still image
3. open drawing tool and outline an appropriate crop region using a bounding rectangle
4. note the top, left, width & height coordinates


![still-frame-uncropped.jpg](./still-frame-uncropped.jpg)
Figure still-frame-uncropped.jpg


![still-frame-cropped-region-outline.jpg](./still-frame-cropped-region-outline.jpg)
Figure still-frame-cropped-region-outline.jpg



## Test cropped footage

```bash
ffplay -i ../.bin/key-seq-video.mkv -vf "crop=350:520:0:940"
```


## Export a cropped focus region for improved signal to noise ration

```bash
ffmpeg -i ../.bin/key-seq-video.mkv \
  -vf "crop=350:520:0:940" \
  -c:v ffv1 -level 3 -g 1 \
  -c:a copy \
  ../.bin/key-seq-video-cropped.mkv
```

## Generate kinetic movement analysis video

```bash

python ../../tools/video-forensic-analysis.py ../.bin/key-seq-video-cropped.mkv -t -fs 0.5
ffmpeg -i ../.bin/key-seq-video-cropped-kenetic-overlay.mp4 -vf "setpts=15*PTS,fps=2,scale=480:-1:flags=lanczos" ./key-seq-video-cropped-kenetic-overlay.gif
```

![key-seq-video-cropped-kenetic-overlay.gif](./key-seq-video-cropped-kenetic-overlay.gif)
Figure key-seq-video-cropped-kenetic-overlay.gif


## Identifying Visual Time Zero (t~0~)

```bash
python ../../tools/3a.identify-visual-t0.py --video ../.bin/key-seq-video-cropped.mkv -st 0.567
```

```csv 3a.visual-motion-analysis.csv
FrameIndex,Timestamp,MotionMetric,Threshold,Status
18,0.600000,1.665965,10.249804,STABLE
19,0.633000,3.231421,10.249804,STABLE
20,0.667000,0.001586,10.249804,STABLE
21,0.700000,1.074298,10.249804,STABLE
22,0.733000,2.916995,10.249804,STABLE
23,0.767000,0.003735,10.249804,STABLE
24,0.800000,4.361578,10.249804,STABLE
25,0.833000,0.003041,10.249804,STABLE
26,0.867000,2.076575,10.249804,STABLE
27,0.900000,0.897609,10.249804,STABLE
28,0.933000,0.507605,10.249804,STABLE
29,0.967000,12.344831,10.249804,DEVIATION_DETECTED
30,1.000000,6.421370,10.249804,STABLE
31,1.033000,9.897811,10.249804,STABLE
32,1.067000,11.977600,10.249804,DEVIATION_DETECTED
33,1.100000,15.699114,10.249804,DEVIATION_DETECTED
34,1.133000,12.689017,10.249804,DEVIATION_DETECTED
35,1.167000,9.142685,10.249804,STABLE
36,1.200000,8.505435,10.249804,STABLE
37,1.233000,7.530118,10.249804,STABLE
38,1.267000,14.918163,10.249804,DEVIATION_DETECTED
39,1.300000,18.812845,10.249804,DEVIATION_DETECTED
40,1.333000,11.168832,10.249804,DEVIATION_DETECTED
41,1.367000,7.528182,10.249804,STABLE
42,1.400000,4.335780,10.249804,STABLE
43,1.433000,4.002197,10.249804,STABLE
```
Dataset 3a.visual-motion-analysis.csv 


## Motion & behavior analysis

```bash
python ../../tools/3b.analyze-motion-behavior.py --video ../.bin/key-seq-video-cropped.mkv -t0 0.967 -view east -fs 0.5

# Analysis complete.
# - Reports: 3b.analyze-motion-behavior.csv, 3b.analyze-motion-behavior-forensic-event-summary.csv
# - Visuals: 3b.kinematic-profile.png, 3 event overlay(s) generated.
```

```csv 3b.analyze-motion-behavior.csv
Offset(ms),Vel,Accel,Jerk,Curl,Type,Origin
0.0,6.98,209.36,6280.75,0.0367,KINETIC,West (Behind)
33.33,3.48,-104.91,-9428.06,-0.0248,,West (Behind)
66.67,4.38,27.09,3960.12,0.0743,,N/A
100.0,6.86,74.28,1415.54,-0.0544,,South
133.33,12.08,156.69,2472.28,-0.005,,West (Behind)
166.67,10.33,-52.48,-6275.0,0.072,,South
200.0,3.63,-201.18,-4461.17,0.0257,,West (Behind)
233.33,7.63,120.03,9636.4,-0.0351,,South
266.67,9.0,40.99,-2371.22,0.0111,,East (Front)
300.0,21.28,368.68,9830.83,-0.0161,KINETIC,West (Behind)
333.33,20.75,-16.06,-11542.28,0.0918,,West (Behind)
366.67,12.18,-257.23,-7234.95,0.0409,,West (Behind)
400.0,7.66,-135.51,3651.38,-0.1218,,South
433.33,5.9,-52.67,2485.22,-0.067,,South
466.67,7.51,48.14,3024.38,-0.0784,,South
```
Dataset 3b.analyze-motion-behavior.csv


```csv 3b.analyze-motion-behavior-forensic-event-summary.csv
Event Number,Offset(ms),Velocity,Accel,Jerk,Nature,Origin
0,0.0,6.98,209.36,6280.75,Direct Kinetic Transfer (Initial Impact/Shockwave),West (Behind)
1,133.33,12.08,156.69,2472.28,Secondary Kinetic Strike or High-Velocity Reflex,West (Behind)
2,300.0,21.28,368.68,9830.83,Physically Impossible Human Move (External Force Override),West (Behind)
```
Dataset 3b.analyze-motion-behavior-forensic-event-summary.csv


![3b.analyze-motion-behavior-peak-motion-overlay-event-0.jpg](./3b.analyze-motion-behavior-peak-motion-overlay-event-0.jpg)
Figure Event 0

![3b.analyze-motion-behavior-peak-motion-overlay-event-1.jpg](./3b.analyze-motion-behavior-peak-motion-overlay-event-1.jpg)
Figure Event 1

![3b.analyze-motion-behavior-peak-motion-overlay-event-2.jpg](./3b.analyze-motion-behavior-peak-motion-overlay-event-2.jpg)
Figure Event 2

![3b.kinematic-profile.png](./3b.kinematic-profile.png)
Figure Kinematic profile

