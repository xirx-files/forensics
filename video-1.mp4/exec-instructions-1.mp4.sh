exiftool ../../sources/archive.org-ks/1.mp4 > metadata-1.mp4.txt

ffprobe -v error -select_streams v:0 -show_entries frame=pts_time,pict_type -of csv=p=0 ../../sources/archive.org-ks/1.mp4 | awk -F',' '$1 >= 0.766 && $1 <= 0.966 {print $0}' > absolute_visual_timestamps-1.mp4.txt

ffmpeg -i ../../sources/archive.org-ks/1.mp4 -ss 0.766667 -t 00:00:02.0 -acodec pcm_s16le -ar 44100 original_event_audio.wav

sox original_event_audio.wav -n stat 2> sox_stats-1.mp4.txt
sox original_event_audio.wav -n stats 2>> sox_stats-1.mp4.txt

ffprobe -f lavfi -i "amovie=original_event_audio.wav,astats=metadata=1" -show_entries frame=pkt_pts_time:frame_tags=lavfi.astats.Overall.Peak_level -of csv=p=0 > frame_by_frame_audio_peaks-1.mp4.txt

# ffprobe -f lavfi -i "amovie=original_event_audio.wav,aspectralstats,ametadata=mode=add:key=flatness:value=lavfi.aspectstats.Overall.Flatness" \
# -show_entries frame=pkt_pts_time:frame_tags=flatness \
# -of csv=p=0 > gunshot_flatness_analysis.txt

# ffprobe -f lavfi -i "amovie=original_event_audio.wav,aspectralstats=win_size=256,ametadata=mode=print:file=gunshot_highres_analysis.txt" -show_frames > /dev/null 2>&1

ffprobe -f lavfi -i "amovie=original_event_audio.wav,aspectralstats=win_size=128" \
-show_entries frame=pkt_pts_time:frame_tags=lavfi.aspectstats.Overall.Crest,lavfi.aspectstats.Overall.Entropy \
-of csv=p=0 > gunshot_validation.txt
