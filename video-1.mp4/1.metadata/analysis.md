# Metadata of 1.mp4

```bash
cd 1.metadata
```

## Authentication
```bash
$ python ../../tools/1.authenticate-media.py --input ../../../sources/archive.org/1.mp4 
Conducting forensic audit on ../../../sources/archive.org/1.mp4...
✓ SUCCESS: All authenticity thresholds passed.
```

```csv 1.authenticate-media.csv
Test/Metric,Value,Result Status
SHA-256 Hash,2a43ccfa0667bb1fe925e8f31775bc981980aaa01ef3665ab8c43f802d46eb71,VERIFIED
Encoder Signature,Unknown,PASS (Native/Unknown)
Video Codec,h264,INFO
Frame Rate,30/1,PASS
Freeze/Pause Detection,0 detected,PASS
Creation Metadata,Missing,WARNING
```


## Metadata

```bash
exiftool ../../sources/archive.org/1.mp4 > metadata.txt # follow up with \s+:\s(?=.) -> |
```

```text
ExifTool Version Number         : 12.57
File Name                       : 1.mp4
Directory                       : ../../../sources/archive.org
File Size                       : 2.2 MB
File Modification Date/Time     : 2025:12:13 19:42:21+11:00
File Access Date/Time           : 2026:01:17 19:46:04+11:00
File Inode Change Date/Time     : 2026:01:17 19:46:04+11:00
File Permissions                : -rw-r--r--
File Type                       : MP4
File Type Extension             : mp4
MIME Type                       : video/mp4
Major Brand                     : MP4 Base Media v1 [IS0 14496-12:2003]
Minor Version                   : 0.2.0
Compatible Brands               : isom, iso2, avc1, mp41
Movie Header Version            : 0
Create Date                     : 0000:00:00 00:00:00
Modify Date                     : 0000:00:00 00:00:00
Time Scale                      : 1000
Duration                        : 4.53 s
Preferred Rate                  : 1
Preferred Volume                : 100.00%
Preview Time                    : 0 s
Preview Duration                : 0 s
Poster Time                     : 0 s
Selection Time                  : 0 s
Selection Duration              : 0 s
Current Time                    : 0 s
Next Track ID                   : 3
Track Header Version            : 0
Track Create Date               : 0000:00:00 00:00:00
Track Modify Date               : 0000:00:00 00:00:00
Track ID                        : 1
Track Duration                  : 4.53 s
Track Layer                     : 0
Track Volume                    : 0.00%
Image Width                     : 886
Image Height                    : 1920
Graphics Mode                   : srcCopy
Op Color                        : 0 0 0
Compressor ID                   : avc1
Source Image Width              : 886
Source Image Height             : 1920
X Resolution                    : 72
Y Resolution                    : 72
Bit Depth                       : 24
Color Profiles                  : nclx
Color Primaries                 : BT.470 System B, G (historical)
Transfer Characteristics        : BT.601
Matrix Coefficients             : BT.470 System B, G (historical)
Buffer Size                     : 0
Max Bitrate                     : 3729615
Average Bitrate                 : 3729615
Video Frame Rate                : 30
Matrix Structure                : 1 0 0 0 1 0 0 0 1
Media Header Version            : 0
Media Create Date               : 0000:00:00 00:00:00
Media Modify Date               : 0000:00:00 00:00:00
Media Time Scale                : 48000
Media Duration                  : 4.44 s
Media Language Code             : und
Handler Description             : SoundHandler
Balance                         : 0
Audio Format                    : mp4a
Audio Channels                  : 2
Audio Bits Per Sample           : 16
Audio Sample Rate               : 48000
Handler Type                    : Metadata
Handler Vendor ID               : Apple
Media Data Size                 : 2186007
Media Data Offset               : 6329
Image Size                      : 886x1920
Megapixels                      : 1.7
Avg Bitrate                     : 3.86 Mbps
Rotation                        : 0
```

## Lossless Preperation

### Determine Start of Key-Sequence

```bash
$ python ../../tools/1.identify-quietest-timestamps.py --input ../../../sources/archive.org/1.mp4 --start 0.64
File SR: 48000Hz | Window: 480 samples (10ms)
Scanning from 0.64s for 0.2s...

Rank  | Absolute Timestamp   | Peak Level (dB)
--------------------------------------------------
1     | 0.780667             | -19.86         
2     | 0.770667             | -14.80         
3     | 0.750667             | -13.94         
4     | 0.760667             | -13.91         
5     | 0.740667             | -13.34 
```

Start Key-Sequence video clipping at 0.766667 b/c this is the prior video frame to 0.780667.


### Key-Sequence Acquisition

```bash
$ python ../../tools/1.clipped-media-preparation.py --input ../../../sources/archive.org/1.mp4 --start 0.766667  --duration 1.466667
--- Forensic Prep: 1.mp4 ---
Native Sample Rate: 48000Hz
✓ Saved Lossless Video: ../.bin/key-seq-video.mkv
✓ Saved Bit-Perfect Audio: ../.bin/key-seq-audio.wav
```

```bash
python ../../tools/1.verify-visual-audio-alignment.py  --v ../.bin/key-seq-video.mkv --a ../.bin/key-seq-audio.wav

ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 ../.bin/key-seq-video.mkv
# 1.467000
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 ../.bin/key-seq-audio.wav
# 1.464667
```


