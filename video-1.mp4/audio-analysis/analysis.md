# Audio Analysis

## Preferred channel assessment

```bash
ffmpeg -i ../../sources/archive.org/1.mp4 -af astats -f null - 2> 1.mp4.astat.txt
ffmpeg -i ./key-seq-audio.wav -af astats -f null - 2> key-seq-audio.wav.astat.txt

python ../tools/2a.analyze_audio.py < original_event_audio.astat.txt 
```

