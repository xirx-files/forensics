exiftool ../../sources/archive.org-ks/1.mp4 > metadata-1.mp4.txt

ffprobe -v error -select_streams v:0 -show_entries frame=pts_time,pict_type -of csv=p=0 ../../sources/archive.org-ks/1.mp4 | awk -F',' '$1 >= 0.766 && $1 <= 0.966 {print $0}' > absolute_visual_timestamps-1.mp4.txt

ffmpeg -i ../../sources/archive.org-ks/1.mp4 -ss 0.766667 -t 00:00:02.0 -acodec pcm_s16le -ar 44100 original_event_audio.wav

sox original_event_audio.wav -n stat 2> sox_stats-1.mp4.txt
sox original_event_audio.wav -n stats 2>> sox_stats-1.mp4.txt

ffprobe -f lavfi -i "amovie=original_event_audio.wav,aspectralstats,ametadata=mode=print:file=event-spectral-stats.txt" -show_frames

python ../gen-event-centroid-data.py