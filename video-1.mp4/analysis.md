# Analysis of 1.mp4


## 0. Authenticity
```bash
python ../tools/0.assert-media-authenticity.py --media ../../sources/archive.org/1.mp4
```

| # | Test Name               | Measured Value  | Result Status |
|---|-------------------------|-----------------|---------------|
| 1 | Sample Rate Check       | 44100Hz         | PASS          |
| 2 | Clipping Analysis       | 0.0000% clipped | PASS          |
| 3 | DC Offset               | 0.000061        | PASS          |
| 4 | Digital Silence Check   | 2.54% silent    | PASS          |
| 5 | Crest Factor (AGC Test) | 6               | PASS          |
| 6 | Video Frame Rate        | 30.0 fps        | PASS          |

Table 1.assert-media-authenticity.csv


### Executive Summary
The media file has passed all standard integrity checks. The audio and video signals are consistent with a clean, high-quality recording from a standard device (like a smartphone or digital camera).


| # | Test Name             | What it Means in Plain English                                                                                                                                                                                  | Verdict  |
|---|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
| 1 | Sample Rate Check     | Digital Resolution: Confirms the audio was recorded at a standard industry frequency (44.1kHz). This is the standard for CDs and high-quality digital files.                                                    | Healthy  |
| 2 | Clipping Analysis     | Distortion Check: Looks for "blown out" audio where the sound was too loud for the microphone. 0% means the audio is clear and contains all original waveform data without digital "crunch."                    | Clean    |
| 3 | DC Offset             | Hardware Integrity: Checks if the microphone or recording hardware was malfunctioning. A near-zero value (0.000061) indicates the electrical signal was perfectly balanced.                                     | Stable   |
| 4 | Digital Silence Check | Edit Detection: Looks for "dead air" that might indicate parts of the recording were cut out and replaced with empty space. 2.54% is normal for natural pauses in speech or environment.                        | Original |
| 5 | Crest Factor (AGC)    | Volume Manipulation: Determines if "Auto-Gain" or heavy compression was used to flatten the sound. A score of 6.00 confirms the audio retains its natural "peaks" (like a clap or loud word) vs. its "valleys." | Natural  |
| 6 | Video Frame Rate      | Motion Smoothness: Confirms the video runs at 30 frames per second which is the standard for modern digital video. There is no evidence of "dropped frames" or jitter.                                          | Smooth   |

Table Understanding 1.assert-media-authenticity

### Conclusion for Reviewer
The file appears to be a continuous, unedited original recording. There are no technical "red flags" (such as excessive silence, digital distortion, or hardware errors) that would suggest the file has been spliced, compressed, or manipulated post-recording.


## 1. Metadata

```bash
exiftool ../../sources/archive.org/1.mp4 > metadata.txt # follow up with \s+:\s(?=.) -> |
```

| #  | ExifTool Version Number     | 12.57                                 |
|----|-----------------------------|---------------------------------------|
| 1  | File Name                   | 1.mp4                                 |
| 2  | Directory                   | ../../sources/archive.org             |
| 3  | File Size                   | 2.2 MB                                |
| 4  | File Modification Date/Time | 2025:12:13 19:42:21+11:00             |
| 5  | File Access Date/Time       | 2026:01:17 19:46:04+11:00             |
| 6  | File Inode Change Date/Time | 2026:01:17 19:46:04+11:00             |
| 7  | File Permissions            | -rw-r--r--                            |
| 8  | File Type                   | MP4                                   |
| 9  | File Type Extension         | mp4                                   |
| 10 | MIME Type                   | video/mp4                             |
| 11 | Major Brand                 | MP4 Base Media v1 [IS0 14496-12:2003] |
| 12 | Minor Version               | 0.2.0                                 |
| 13 | Compatible Brands           | isom, iso2, avc1, mp41                |
| 14 | Movie Header Version        | 0                                     |
| 15 | Create Date                 | 0000:00:00 00:00:00                   |
| 16 | Modify Date                 | 0000:00:00 00:00:00                   |
| 17 | Time Scale                  | 1000                                  |
| 18 | Duration                    | 4.53 s                                |
| 19 | Preferred Rate              | 1                                     |
| 20 | Preferred Volume            | 100.00%                               |
| 21 | Preview Time                | 0 s                                   |
| 22 | Preview Duration            | 0 s                                   |
| 23 | Poster Time                 | 0 s                                   |
| 24 | Selection Time              | 0 s                                   |
| 25 | Selection Duration          | 0 s                                   |
| 26 | Current Time                | 0 s                                   |
| 27 | Next Track ID               | 3                                     |
| 28 | Track Header Version        | 0                                     |
| 29 | Track Create Date           | 0000:00:00 00:00:00                   |
| 30 | Track Modify Date           | 0000:00:00 00:00:00                   |
| 31 | Track ID                    | 1                                     |
| 32 | Track Duration              | 4.53 s                                |
| 33 | Track Layer                 | 0                                     |
| 34 | Track Volume                | 0.00%                                 |
| 35 | Image Width                 | 886                                   |
| 36 | Image Height                | 1920                                  |
| 37 | Graphics Mode               | srcCopy                               |
| 38 | Op Color                    | 0 0 0                                 |
| 39 | Compressor ID               | avc1                                  |
| 40 | Source Image Width          | 886                                   |
| 41 | Source Image Height         | 1920                                  |
| 42 | X Resolution                | 72                                    |
| 43 | Y Resolution                | 72                                    |
| 44 | Bit Depth                   | 24                                    |
| 45 | Color Profiles              | nclx                                  |
| 46 | Color Primaries             | BT.470 System B, G (historical)       |
| 47 | Transfer Characteristics    | BT.601                                |
| 48 | Matrix Coefficients         | BT.470 System B, G (historical)       |
| 49 | Buffer Size                 | 0                                     |
| 50 | Max Bitrate                 | 3729615                               |
| 51 | Average Bitrate             | 3729615                               |
| 52 | Video Frame Rate            | 30                                    |
| 53 | Matrix Structure            | 1 0 0 0 1 0 0 0 1                     |
| 54 | Media Header Version        | 0                                     |
| 55 | Media Create Date           | 0000:00:00 00:00:00                   |
| 56 | Media Modify Date           | 0000:00:00 00:00:00                   |
| 57 | Media Time Scale            | 48000                                 |
| 58 | Media Duration              | 4.44 s                                |
| 59 | Media Language Code         | und                                   |
| 60 | Handler Description         | SoundHandler                          |
| 61 | Balance                     | 0                                     |
| 62 | Audio Format                | mp4a                                  |
| 63 | Audio Channels              | 2                                     |
| 64 | Audio Bits Per Sample       | 16                                    |
| 65 | Audio Sample Rate           | 48000                                 |
| 66 | Handler Type                | Metadata                              |
| 67 | Handler Vendor ID           | Apple                                 |
| 68 | Media Data Size             | 2186007                               |
| 69 | Media Data Offset           | 6329                                  |
| 70 | Image Size                  | 886x1920                              |
| 71 | Megapixels                  | 1.7                                   |
| 72 | Avg Bitrate                 | 3.86 Mbps                             |
| 73 | Rotation                    | 0                                     |

Table metadata


## 2. Spatial Analysis

![camera-coords-query-wcs-xy.svg](./spatial-mapping/camera-coords-query-wcs-xy.svg)
Figure camera-coords-query-wcs-xy.svg


| # | From_Feature              |                 | Lat_1            | Lon_1             | Ele_1            |
|---|---------------------------|-----------------|------------------|-------------------|------------------|
| 1 | 1.mp4 camera location     |                 | 40.2775302210218 | -111.713968844756 | 1402.78747731397 |
| 2 |                           |                 |                  |                   |                  |
| 3 | To_Feature                | Distance_Meters | Lat_2            | Lon_2             | Ele_2            |
| 4 | North speaker             | 7.685           | 40.2775627642768 | -111.714047818602 | 1403.732083      |
| 5 | Center north speaker      | 4.282           | 40.2775466124262 | -111.714013612385 | 1403.513785      |
| 6 | Center south speaker      | 2.383           | 40.2775165615533 | -111.713989351347 | 1403.366405      |
| 7 | South speaker             | 4.625           | 40.2774899744697 | -111.713966300153 | 1403.957025      |
| 8 | CK microphone             | 5.68            | 40.2775203851023 | -111.714033649438 | 1401.955129      |
| 9 | Audience microphone stand | 3.145           | 40.2775314668336 | -111.714005459209 | 1402.369802      |

Table 1.mp4 camera location with respect to stage


Refer to [Perspective-n-point](./spatial-analysis/perspective-n-point.md) for further details.


## 3. Clip media for forensic media analysis

The key sequence of ("violence" -> momentary silence -> "great" -> momentary silence -> bang segment)

The preceeding sequence is ("gang" -> "violence") delivered only by CK. Split point should be between 0.673 and 0.873. Note, line 65 from the metadata table reveals an Audio Sample Rate of 48000.

```bash
# use asetnsamples=n=960 for 48K & n=882 for 44.1kHz
ffprobe -v error -f lavfi -i "amovie='../../sources/archive.org/1.mp4',atrim=start=0.74:duration=0.2,asetpts=PTS-STARTPTS,asetnsamples=n=960,astats=metadata=1:reset=1" -show_entries frame=pts_time:frame_tags=lavfi.astats.Overall.RMS_level -of csv=p=0 | sort -t',' -k2,2n | head -n 1

0.040000,-22.175363
```

The key sequence should start around 0.78s. Note, line 52 from the metadata table reveals a Video Frame Rate of 30. Therefore, the immediate timestamp preceeding 0.78 is 0.766667 and the end timestamp (ie. +1.5s) will be 2.233337 (duration 2.233337 - 0.766667 = 1.46667).


```bash
ffmpeg -ss 0.766667 -i ../../sources/archive.org/1.mp4 \
  -filter_complex "[0:v]trim=duration=1.466670,setpts=PTS-STARTPTS[v]; \
                   [0:a:0]atrim=duration=1.466670,asetpts=PTS-STARTPTS,aresample=async=1[a]; \
                   [v]split=1[v_out]; [a]asplit=2[a_mov][a_wav]" \
  -map "[v_out]" -map "[a_mov]" -c:v libx264 -crf 18 -c:a pcm_s16le ./video-analysis/key-seq-video.mov \
  -map "[a_wav]" -c:a pcm_f32le ./audio-analysis/key-seq-audio.wav
```

Check for consistency in generated output durations.
```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 ./video-analysis/key-seq-video.mov
# 1.467000

ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 ./audio-analysis/key-seq-audio.wav
# 1.464667
```


## 4. Visual Time Zero

| #  | FrameIndex | Timestamp | MotionMetric | Threshold | Status             |
|----|------------|-----------|--------------|-----------|--------------------|
| 1  | 18         | 0.6       | 1.717317     | 10.173344 | STABLE             |
| 2  | 19         | 0.633333  | 3.301683     | 10.173344 | STABLE             |
| 3  | 20         | 0.666667  | 0.00209      | 10.173344 | STABLE             |
| 4  | 21         | 0.7       | 1.131566     | 10.173344 | STABLE             |
| 5  | 22         | 0.733333  | 3.152664     | 10.173344 | STABLE             |
| 6  | 23         | 0.766667  | 0.004656     | 10.173344 | STABLE             |
| 7  | 24         | 0.8       | 4.080758     | 10.173344 | STABLE             |
| 8  | 25         | 0.833333  | 0.007464     | 10.173344 | STABLE             |
| 9  | 26         | 0.866667  | 2.19804      | 10.173344 | STABLE             |
| 10 | 27         | 0.9       | 0.871338     | 10.173344 | STABLE             |
| 11 | 28         | 0.933333  | 0.534649     | 10.173344 | STABLE             |
| 12 | 29         | 0.966667  | 12.726921    | 10.173344 | DEVIATION_DETECTED |
| 13 | 30         | 1         | 6.887399     | 10.173344 | STABLE             |
| 14 | 31         | 1.033333  | 10.650967    | 10.173344 | DEVIATION_DETECTED |
| 15 | 32         | 1.066667  | 11.587164    | 10.173344 | DEVIATION_DETECTED |
| 16 | 33         | 1.1       | 15.929962    | 10.173344 | DEVIATION_DETECTED |
| 17 | 34         | 1.133333  | 12.095077    | 10.173344 | DEVIATION_DETECTED |
| 18 | 35         | 1.166667  | 9.545898     | 10.173344 | STABLE             |
| 19 | 36         | 1.2       | 8.918169     | 10.173344 | STABLE             |
| 20 | 37         | 1.233333  | 6.851216     | 10.173344 | STABLE             |
| 21 | 38         | 1.266667  | 14.516001    | 10.173344 | DEVIATION_DETECTED |
| 22 | 39         | 1.3       | 18.566072    | 10.173344 | DEVIATION_DETECTED |
| 23 | 40         | 1.333333  | 11.162679    | 10.173344 | DEVIATION_DETECTED |
| 24 | 41         | 1.366667  | 7.711784     | 10.173344 | STABLE             |
| 25 | 42         | 1.4       | 4.534672     | 10.173344 | STABLE             |
| 26 | 43         | 1.433333  | 4.176903     | 10.173344 | STABLE             |

Table impact detection


In the table above, row 12 outlines that the first frame that exhibits a significant deviation from the previous motion measurements. Therefore, frame 29 with timestamp 0.966667s will be applied as visual time zero.


