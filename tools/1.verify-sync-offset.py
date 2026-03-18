import subprocess
import json
import argparse
import sys

def get_sync_offset(file_path):
    """
    Extracts start_time for video and audio streams and 
    calculates the leading/lagging sample offset.
    """
    # Correct syntax: Remove the restricted -select_streams a:v
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", file_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
    except Exception as e:
        print(f"Error probing file: {e}")
        sys.exit(1)

    # Extract stream metadata
    v_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
    a_stream = next((s for s in data['streams'] if s['codec_type'] == 'audio'), None)

    if not v_stream or not a_stream:
        print("Error: File must contain both a video and an audio stream.")
        sys.exit(1)

    v_start = float(v_stream.get('start_time', 0.0))
    a_start = float(a_stream.get('start_time', 0.0))
    sample_rate = int(a_stream.get('sample_rate', 48000))

    # Calculate differences
    # Positive offset means Audio starts AFTER Video (Video leads)
    # Negative offset means Audio starts BEFORE Video (Audio leads)
    time_offset = a_start - v_start
    sample_offset = int(time_offset * sample_rate)

    print(f"\n--- SYNC OFFSET ANALYSIS: {file_path} ---")
    print(f"Video Start Time: {v_start:.6f} s")
    print(f"Audio Start Time: {a_start:.6f} s")
    print(f"Sample Rate:      {sample_rate} Hz")
    print("-" * 40)
    
    if time_offset == 0:
        print("RESULT: Streams are perfectly aligned at the container level.")
    else:
        direction = "Lags (starts after)" if time_offset > 0 else "Leads (starts before)"
        print(f"RESULT: Audio {direction} Video by {abs(time_offset):.6f} seconds.")
        print(f"EXACT SAMPLE OFFSET: {abs(sample_offset)} samples")
    
    return sample_offset

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate exact AV sample offset.")
    parser.add_argument("--input", required=True, help="Path to the media file")
    args = parser.parse_args()
    get_sync_offset(args.input)
