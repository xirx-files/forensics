exiftool ../../../2.MOV > metadata-2.MOV.txt

ffprobe -v error -select_streams v:0 -show_entries frame=pts_time,pict_type -of csv=p=0 ../../../2.MOV | awk -F',' '$1 >= 7.60 && $1 <= 9.60 {print $0}' > absolute_visual_timestamps-2.MOV.txt

ffmpeg -i ../../../2.MOV -ss 7.605000 -t 00:00:02.0 -acodec pcm_s16le -ar 44100 original_event_audio.wav

sox original_event_audio.wav -n stat 2> sox_stats-2.MOV.txt
sox original_event_audio.wav -n stats 2>> sox_stats-2.MOV.txt

ffprobe -f lavfi -i "amovie=original_event_audio.wav,astats=metadata=1" -show_entries frame=pkt_pts_time:frame_tags=lavfi.astats.Overall.Peak_level -of csv=p=0 > frame_by_frame_audio_peaks-2.MOV.txt

python ../fft2.py