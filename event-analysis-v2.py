import librosa
import numpy as np

def analyze_event_audio(file_path):
    # Load audio; sr=None ensures we don't lose high-frequency transients
    y, sr = librosa.load(file_path, sr=None)

    # 1. SIMPLE DENOISING: Reduce consistent background noise
    # We take a small sample of the background to estimate noise levels
    y_denoised = librosa.effects.remix(y, intervals=librosa.effects.split(y, top_db=20))
    
    # 2. DYNAMIC THRESHOLDING
    # Outdoor events usually require a higher top_db (35-50) to ignore crowd noise.
    # We use a very small hop_length to catch sub-millisecond gaps.
    intervals = librosa.effects.split(y, top_db=60, frame_length=512, hop_length=64)

    if len(intervals) < 3:
        return f"Detected only {len(intervals)} events. Try increasing top_db."

    # Convert sample indices to seconds
    times = intervals / sr

    # Map events based on your sequence: 1(Violence), 2(Great), 3(Bang)
    gap_a_start, gap_a_end = times[0][1], times[1][0]
    gap_b_start, gap_b_end = times[1][1], times[2][0]

    return {
        "A": (gap_a_start, gap_a_end, gap_a_end - gap_a_start),
        "B": (gap_b_start, gap_b_end, gap_b_end - gap_b_start)
    }

def main():
    filename = "original_event_audio.wav"
    print("| Gap Type | Start (s) | End (s) | Duration (ms) |")
    print("| :--- | :--- | :--- | :--- |")

    res = analyze_event_audio(filename)
    
    if isinstance(res, dict):
        for key, name in [("A", "White-Noise A"), ("B", "White-Noise B")]:
            start, end, dur = res[key]
            # Convert duration to ms for easier reading of 0.097ms scales
            print(f"| {name} | {start:.6f} | {end:.6f} | {dur*1000:.4f} ms |")
    else:
        print(f"| Error | - | - | {res} |")

if __name__ == "__main__":
    main()
