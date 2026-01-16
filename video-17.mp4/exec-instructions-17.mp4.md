exiftool ../../../17.mp4 > metadata-17.mp4.txt

ffprobe -v error -select_streams v:0 -show_entries frame=pts_time,pict_type -of csv=p=0 ../../../17.mp4 | awk -F',' '$1 >= 0.00 && $1 <= 2.00 {print $0}' > absolute_visual_timestamps-17.mp4.txt

ffmpeg -i ../../../17.mp4 -ss 0.000000 -t 00:00:02.0 -acodec pcm_s16le -ar 44100 original_event_audio.wav

sox original_event_audio.wav -n stat 2> sox_stats-17.mp4.txt
sox original_event_audio.wav -n stats 2>> sox_stats-17.mp4.txt

ffprobe -f lavfi -i "amovie=original_event_audio.wav,astats=metadata=1" -show_entries frame=pkt_pts_time:frame_tags=lavfi.astats.Overall.Peak_level -of csv=p=0 > frame_by_frame_audio_peaks-17.mp4.txt

python ../fft2.py