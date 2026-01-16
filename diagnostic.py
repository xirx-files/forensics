import os
import re

def get_audio_clip_start_time(exec_file):
    if not os.path.exists(exec_file):
        print(f"File does not exist: {exec_file}")
        return None
    try:
        with open(exec_file, 'r') as f:
            content = f.read()
            # Use a more flexible regex, removing the trailing space dependency
            match = re.search(r'ffmpeg -i .* -ss ([\d\.]+)', content)
            if match:
                return float(match.group(1))
            else:
                print(f"Regex did not match in file: {exec_file}")
                return None
    except Exception as e:
        print(f"Exception for file {exec_file}: {e}")
        return None

VIDEO_NAMES = [
    'video-1.mp4', 'video-2.MOV', 'video-4.mp4', 'video-13.mp4',
    'video-16.mp4', 'video-17.mp4', 'video-12.mp4', 'video-3.mp4',
    'video-5.mp4', 'video-6.mp4', 'video-7.mp4', 'video-8.mp4'
]

print("--- Running Full Diagnostic ---")
for video_name in VIDEO_NAMES:
    internal_name = video_name.replace('video-', '')
    exec_file_path = os.path.join(video_name, f'exec-instructions-{internal_name}.md')
    
    offset = get_audio_clip_start_time(exec_file_path)
    
    print(f"Result for '{exec_file_path}': {offset}")

print("--- Diagnostic Complete ---")