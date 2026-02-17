exiftool ../../sources/archive.org-ks/1.mp4 > metadata.txt

ffprobe -v error -select_streams v:0 -show_entries frame=pts_time,pict_type -of csv=p=0 ../../sources/archive.org-ks/1.mp4 | awk -F',' '$1 >= 0.766 && $1 <= 2.233333 {print $0}' > absolute-timestamps-visual-timestamps.txt

ffmpeg -i ../../sources/archive.org-ks/1.mp4 -ss 0.766667 -to 2.233333 -acodec pcm_s16le -ar 44100 original_event_audio.wav

ffmpeg -i ../../sources/archive.org-ks/1.mp4 -ss 0.766667 -to 2.233333 -c:v libx264 -crf 18 -c:a copy original_event_video.mp4

sox original_event_audio.wav -n stat 2> sox_stats.txt
sox original_event_audio.wav -n stats 2>> sox_stats.txt

ffprobe -f lavfi -i "amovie=original_event_audio.wav,astats=metadata=1,aspectralstats,ametadata=mode=print:file=event-spectral-stats.txt" -show_frames

python ../tools/gen-event-centroid-peak-levl-db.py