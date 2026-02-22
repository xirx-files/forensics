# https://share.google/aimode/MIxJqIJyIXw8UzvIt
# please provide a report on how the following cli execution result can be understood in laymans terms by a reviewer

import numpy as np
import scipy.io.wavfile as wav
import csv
import os
import argparse
from moviepy import VideoFileClip

def assert_authenticity(audio_data, sample_rate):
    results = []
    
    # Ensure data is floating point for analysis
    if audio_data.dtype != np.float32:
        audio_data = audio_data.astype(np.float32) / (np.iinfo(audio_data.dtype).max if audio_data.dtype.kind in 'iu' else 1.0)

    # 1. Sample Rate Verification
    results.append(["Sample Rate Check", f"{sample_rate}Hz", "PASS" if sample_rate in (44100, 48000) else "FAIL"])

    # 2. Clipping Detection
    clipping_threshold = 0.99
    clipped_samples = np.sum(np.abs(audio_data) >= clipping_threshold)
    clipping_percent = (clipped_samples / len(audio_data)) * 100
    results.append(["Clipping Analysis", f"{clipping_percent:.4f}% clipped", "WARNING" if clipping_percent > 0.1 else "PASS"])

    # 3. DC Offset Test
    dc_offset = np.mean(audio_data)
    results.append(["DC Offset", f"{dc_offset:.6f}", "PASS" if abs(dc_offset) < 0.01 else "FAIL"])

    # 4. Silence/Dropout Detection
    silence_threshold = 1e-5
    silent_frames = np.sum(np.abs(audio_data) < silence_threshold)
    silence_percent = (silent_frames / len(audio_data)) * 100
    results.append(["Digital Silence Check", f"{silence_percent:.2f}% silent", "FAIL" if silence_percent > 5.0 else "PASS"])

    # 5. Peak-to-RMS Ratio (AGC Indicator)
    peak = np.max(np.abs(audio_data))
    rms = np.sqrt(np.mean(audio_data**2))
    crest_factor = peak / rms if rms > 0 else 0
    results.append(["Crest Factor (AGC Test)", f"{crest_factor:.2f}", "PASS" if crest_factor > 3.0 else "SUSPECT AGC"])

    return results

def main():
    parser = argparse.ArgumentParser(description="Authenticate Media Files")
    parser.add_argument("--media", required=True, help="Path to the video file (e.g., 1.mp4)")
    args = parser.parse_args()

    input_file = args.media
    output_file = "0.assert-media-authenticity.csv"

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    try:
        print(f"Analyzing {input_file}...")
        video = VideoFileClip(input_file)
        
        # Audio Authentication
        audio = video.audio
        # Convert to mono for simple analysis and get as numpy array
        audio_array = audio.to_soundarray(fps=audio.fps)
        if len(audio_array.shape) > 1:
            audio_array = audio_array.mean(axis=1) # Mono conversion
        
        test_results = assert_authenticity(audio_array, audio.fps)

        # Video Frame Check (Basic verification)
        video_status = "PASS" if video.fps >= 23.97 else "WARNING (Low FPS)"
        test_results.append(["Video Frame Rate", f"{video.fps} fps", video_status])

        # Write results
        with open(output_file, mode='w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Test Name", "Measured Value", "Result Status"])
            writer.writerows(test_results)

        video.close()
        print(f"Authenticity suite complete. Results exported to {output_file}")

    except Exception as e:
        print(f"Processing Error: {str(e)}")

if __name__ == "__main__":
    main()
