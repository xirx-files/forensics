import librosa
import numpy as np

def analyze_audio_spikes(file_path):
    # Load audio - sr=None keeps the original sampling rate for high precision
    y, sr = librosa.load(file_path, sr=None)
    
    # 1. Calculate RMS energy to create an "envelope" of the sound
    # Using a small hop_length for high temporal resolution (sub-millisecond)
    hop_length = 16 
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    times = librosa.frames_to_time(range(len(rms)), sr=sr, hop_length=hop_length)

    # 2. Find the 3 most prominent peaks (Violence, Great, Bang)
    # We use a distance constraint to ensure we don't pick 2 points on the same word
    # 0.05s (50ms) is a safe minimum distance between these events
    min_dist_frames = int(0.05 / (hop_length / sr))
    
    # Use scipy to find local maxima in the energy envelope
    from scipy.signal import find_peaks
    peaks, properties = find_peaks(rms, distance=min_dist_frames, prominence=np.max(rms)*0.1)

    # Sort peaks by time to ensure they are in order: Violence -> Great -> Bang
    peaks = sorted(peaks)

    if len(peaks) < 3:
        return f"Found {len(peaks)} peaks. Try lowering 'prominence' in find_peaks."

    # Identify the events (Start and End of each peak)
    # For these tiny gaps, we define the "Gap" as the time between peak boundaries
    event_times = times[peaks]
    
    # Gap A: Between "Violence" (Peak 0) and "Great" (Peak 1)
    gap_a_start = event_times[0]
    gap_a_end = event_times[1]
    
    # Gap B: Between "Great" (Peak 1) and "Bang" (Peak 2)
    gap_b_start = event_times[1]
    gap_b_end = event_times[2]

    return {
        "A": (gap_a_start, gap_a_end, gap_a_end - gap_a_start),
        "B": (gap_b_start, gap_b_end, gap_b_end - gap_b_start)
    }

def main():
    filename = "original_event_audio.wav"
    print("| Gap Type | Start Position (s) | End Position (s) | Duration (ms) |")
    print("| :--- | :--- | :--- | :--- |")

    res = analyze_audio_spikes(filename)
    
    if isinstance(res, dict):
        for key, label in [("A", "White-Noise A"), ("B", "White-Noise B")]:
            start, end, dur = res[key]
            # Output in ms for better visibility of the 0.097ms / 0.049ms targets
            print(f"| {label} | {start:.6f} | {end:.6f} | {dur*1000:.4f} ms |")
    else:
        print(f"| Error | - | - | {res} |")

if __name__ == "__main__":
    main()
