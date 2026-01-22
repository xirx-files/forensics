import librosa
import numpy as np
import sys
import os

def calculate_relative_arrival_times(file_paths):
    # Load all audio files
    signals = []
    sample_rates = []
    
    for path in file_paths:
        try:
            y, sr = librosa.load(path, sr=None, duration=0.5)
            signals.append(y)
            sample_rates.append(sr)
        except Exception as e:
            print(f"Could not load {os.path.basename(path)}: {e}")
            continue
    
    if not signals:
        return "No valid audio files loaded."

    # Align all signals to the first one based on maximum amplitude peak
    # We find the *sample index* of the peak for all files
    peak_indices = [np.argmax(np.abs(s)) for s in signals]
    
    # The earliest arrival time will have the smallest index if aligned properly
    # However, since they are from different start times, we align them to the first file's peak time (T=0)
    
    # Let's align all audio files to a common global time index before comparison
    # This requires an assumed start point (e.g., beginning of the file)
    
    # A simpler method for this specific case: Assume the gunshot is the loudest event in the 0.5s clip
    
    # Calculate the time in milliseconds from the start of the 0.5s window
    peak_times_ms = [(idx / sr) * 1000 for idx, sr in zip(peak_indices, sample_rates)]
    
    # The minimum time is our T=0 reference point
    if not peak_times_ms: return "Error in peak calculation."
    reference_time = min(peak_times_ms)
    
    results = {}
    for i, path in enumerate(file_paths):
        relative_time = peak_times_ms[i] - reference_time
        # Round to nearest millisecond
        results[os.path.basename(path)] = f"{relative_time:.3f} ms"
        
    return results

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python multilateration_check.py <audio_file_1.wav> <audio_file_2.wav> ...")
        sys.exit(1)
    
    file_paths = sys.argv
    arrival_times = calculate_relative_arrival_times(file_paths)
    
    print("\n--- Relative Acoustic Arrival Times (T=0ms is first arrival) ---")
    print("This determines if sound came from a single point in space.")
    for filename, time in arrival_times.items():
        print(f"{filename}: {time}")
