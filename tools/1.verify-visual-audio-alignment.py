import subprocess
import os
import argparse
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile

def get_first_frame_pts(video_path):
    """Extracts the PTS of the first frame to ensure it starts at 0.0."""
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "frame=pts_time", "-of", "csv=p=0", 
        "-read_intervals", "%+#1", video_path
    ]
    return float(subprocess.check_output(cmd).decode().strip())

def generate_sync_visual(video_path, audio_path, output_img):
    """Generates a side-by-side verification of Frame 0 and Sample 0."""
    # 1. Extract First Frame
    frame_out = "frame_zero.png"
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path, "-frames:v", "1", "-q:v", "2", frame_out
    ], capture_output=True)

    # 2. Read Audio Data
    samplerate, data = wavfile.read(audio_path)
    if len(data.shape) > 1: data = data[:, 0] # Use Ch1
    
    # Take first 100ms for visual inspection
    duration = 0.1 
    samples_to_plot = int(samplerate * duration)
    time_axis = np.linspace(0, duration, samples_to_plot)
    audio_segment = data[:samples_to_plot]

    # 3. Check Video PTS
    v_pts = get_first_frame_pts(video_path)

    # 4. Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    
    # Image Plot
    img = plt.imread(frame_out)
    ax1.imshow(img)
    ax1.set_title(f"Video Frame 0\n(PTS: {v_pts:.6f}s)")
    ax1.axis('off')

    # Waveform Plot
    ax2.plot(time_axis, audio_segment, color='tab:blue')
    ax2.axvline(x=0, color='red', linestyle='--', label='Start of Audio')
    ax2.set_title(f"Audio Waveform (First 100ms)\nStart: 0.000000s")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Amplitude")
    ax2.legend()

    plt.tight_layout()
    plt.savefig(output_img)
    os.remove(frame_out)
    print(f"--- Alignment Verification Complete ---")
    print(f"Video Start PTS: {v_pts:.6f}")
    print(f"Audio Start:     0.000000 (File Start)")
    print(f"Sync Report Saved: {output_img}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--v", required=True, help="Path to clipped .mkv")
    parser.add_argument("--a", required=True, help="Path to clipped .wav")
    args = parser.parse_args()
    
    out_report = "./alignment_verification.png"
    generate_sync_visual(args.v, args.a, out_report)
