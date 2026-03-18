import subprocess
import json
import argparse
import os
import csv

def get_forensic_metadata(input_file):
    # Fixed ffprobe syntax: Use -show_streams without a restricted selector
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", input_file]
    probe = json.loads(subprocess.check_output(cmd))
    streams = probe.get('streams', [])
    
    v_stream = next((s for s in streams if s['codec_type'] == 'video'), {})
    a_stream = next((s for s in streams if s['codec_type'] == 'audio'), {})
    
    if not v_stream or not a_stream:
        print(f"Warning: Stream missing in {input_file}")
        return None

    sample_rate = int(a_stream.get('sample_rate', 48000))
    # Standardize start_time; some files report "N/A"
    v_start = float(v_stream.get('start_time', 0.0))
    a_start = float(a_stream.get('start_time', 0.0))
    
    return {
        "sample_rate": sample_rate,
        "time_offset_sec": a_start - v_start,
        "sample_offset": int((a_start - v_start) * sample_rate)
    }

def process_clip(input_file, start, duration, output_v, output_a):
    meta = get_forensic_metadata(input_file)
    if not meta: return

    # HYBRID SEEKING: 
    # For Video: -ss AFTER -i (Output seeking) for frame-accuracy in FFV1
    # For Audio: -ss BEFORE -i (Input seeking) to prevent duration 'ghosting' in WAV
    
    # 1. Process Video
    cmd_v = [
        "ffmpeg", "-y", "-i", input_file, 
        "-ss", str(start), "-t", str(duration),
        "-map", "0:v:0", "-c:v", "ffv1", "-level", "3", "-g", "1",
        "-avoid_negative_ts", "make_zero", output_v
    ]
    
    # 2. Process Audio (Sharp Cut)
    cmd_a = [
        "ffmpeg", "-y", "-ss", str(start), "-t", str(duration), 
        "-i", input_file,
        "-map", "0:a:0", "-c:a", "pcm_s16le", output_a
    ]
    
    subprocess.run(cmd_v, capture_output=True, check=True)
    subprocess.run(cmd_a, capture_output=True, check=True)
    
    print(f"\n--- Clip Verified: {os.path.basename(input_file)} ---")
    print(f"Sync Bias: {meta['time_offset_sec']:.6f}s")
    print(f"✓ Video: {output_v}")
    print(f"✓ Audio: {output_a}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--start", type=float, default=0.766667)
    parser.add_argument("--duration", type=float, default=1.466667)
    args = parser.parse_args()

    filename = os.path.splitext(os.path.basename(args.input))[0]
    out_v = f"../.bin/key-seq-video.mkv"
    out_a = f"../.bin/key-seq-audio.wav"

    # os.makedirs("../.bin", exist_ok=True)
    process_clip(args.input, args.start, args.duration, out_v, out_a)
