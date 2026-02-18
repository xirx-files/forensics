import argparse
import numpy as np
import librosa
from scipy.signal import butter, sosfiltfilt

def design_filter(cutoff, sr, btype, order=4):
    """24dB roll-off = 4th order Butterworth filter."""
    nyquist = 0.5 * sr
    normal_cutoff = cutoff / nyquist
    sos = butter(order, normal_cutoff, btype=btype, output='sos')
    return sos

def find_quietest_window(audio_segment, sr, window_size_sec=0.1):
    """Finds the 100ms window with the lowest RMS within the provided segment."""
    win_len = int(window_size_sec * sr)
    hop_len = win_len // 4  # 75% overlap for precision
    
    # Calculate RMS for each frame
    rms_frames = librosa.feature.rms(y=audio_segment, frame_length=win_len, hop_length=hop_len)[0]
    
    # Find the index of the minimum RMS value
    min_idx = np.argmin(rms_frames)
    min_rms = rms_frames[min_idx]
    
    # Calculate the timestamp relative to the start of the audio_segment
    window_start_time = (min_idx * hop_len) / sr
    return min_rms, window_start_time

def analyze_audio(file_path, hpf_freq, lpf_freq, threshold_mult, start_time):
    # 1. Load Audio
    y, sr = librosa.load(file_path, sr=None, mono=True)
    start_sample = int(start_time * sr)
    y_search = y[start_sample:] # Search from the specified start time

    # 2 & 3. Apply Filters (24dB roll-off)
    sos_hp = design_filter(hpf_freq, sr, 'highpass')
    y_filt = sosfiltfilt(sos_hp, y_search)
    sos_lp = design_filter(lpf_freq, sr, 'lowpass')
    y_filt = sosfiltfilt(sos_lp, y_filt)

    # 4 & 5. Find Quietest 100ms Baseline in the search segment
    baseline_rms, relative_win_start = find_quietest_window(y_filt, sr)
    threshold = baseline_rms * threshold_mult
    abs_win_start = start_time + relative_win_start
    
    print(f"--- Forensic Analysis Result ---")
    print(f"Filter Range: {hpf_freq}Hz - {lpf_freq}Hz")
    print(f"Quietest 100ms Baseline found at: {abs_win_start:.6f}s")
    print(f"Baseline RMS: {baseline_rms:.6f} | Detection Threshold: {threshold:.6f}")

    # 6. Seek position where threshold is exceeded
    exceeds = np.where(np.abs(y_filt) > threshold)[0]

    if len(exceeds) > 0:
        # Get the first sample that exceeds threshold
        detection_sample = exceeds[0]
        detection_time = start_time + (detection_sample / sr)
        print(f"\n[!] ONSET DETECTED")
        print(f"Timestamp: {detection_time:.6f} seconds")
    else:
        print("\n[-] No signal exceeded the threshold in this range.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", default="mono_event_audio.wav")
    parser.add_argument("-hpf", type=float, required=True)
    parser.add_argument("-lpf", type=float, required=True)
    parser.add_argument("-tm", "--threshold_mult", type=float, default=5.0)
    parser.add_argument("-st", "--start", type=float, default=0.0)
    args = parser.parse_args()
    
    analyze_audio(args.audio, args.hpf, args.lpf, args.threshold_mult, args.start)
