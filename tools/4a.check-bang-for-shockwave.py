import argparse
import numpy as np
import scipy.io.wavfile as wav
from scipy.signal import butter, sosfiltfilt
import csv

def apply_filter(data, low, high, fs):
    """4th order Butterworth zero-phase bandpass as per Locked Spec."""
    sos = butter(4, [low, high], fs=fs, btype='band', output='sos')
    return sosfiltfilt(sos, data)

def get_rms(signal, frame_len, hop):
    """Short-time RMS calculation as per source."""
    return np.array([np.sqrt(np.mean(signal[i:i+frame_len]**2)) 
                     for i in range(0, len(signal) - frame_len, hop)])

def detect_onset(rms_values, fs, hop, threshold_mult=60, hold_ms=6):
    """Locked Spec Onset Detector: Baseline (first 20ms) + 60*std, 6ms hold."""
    baseline_len = int(0.02 * fs / hop)
    baseline = rms_values[:baseline_len]
    threshold = np.mean(baseline) + (threshold_mult * np.std(baseline))
    
    hold_frames = int(hold_ms * (fs / 1000) / hop)
    for i in range(len(rms_values) - hold_frames):
        if np.all(rms_values[i:i+hold_frames] > threshold):
            return i * (hop / fs), threshold
    return None, threshold

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", default="mono_event_audio.wav")
    parser.add_argument("-st", "--start", type=float, required=True)
    args = parser.parse_args()
    
    output_file = '4a.check-bang-for-shockwave.csv'
    bang_timestamp = args.start  # Provided from your band analysis
    
    fs, data = wav.read(args.audio)
    if data.dtype != np.float32:
        data = data.astype(np.float32) / np.iinfo(data.dtype).max
    
    results = []
    
    # TEST 1: High-Frequency Presence (3-7 kHz)
    # Gunshots have ~25% energy here; explosions have ~2% [7]
    crack_band = apply_filter(data, 3000, 7000, fs)
    crack_rms = get_rms(crack_band, 128, 32)
    crack_time, threshold = detect_onset(crack_rms, fs, 32)
    
    has_hf = crack_time is not None
    results.append(["High-Frequency Transient", f"{crack_time if has_hf else 'N/A'}", "DETECTED" if has_hf else "ABSENT"])

    # TEST 2: Precedence Test (Crack must precede Bang)
    # A crack arrives first because V > c [3, 8]
    precedes = False
    if has_hf:
        precedes = crack_time < bang_timestamp
    results.append(["Precedence Test", f"{crack_time if has_hf else 'N/A'} < {bang_timestamp}", "PASS" if precedes else "FAIL"])

    # TEST 3: Salience Check (Locked Spec v2)
    # Measures the strength of the transient against the noise floor [9]
    salience = (np.max(crack_rms) - np.mean(crack_rms[:10])) / (np.std(crack_rms[:10]) + 1e-9)
    results.append(["Salience Score", f"{salience:.2f}", "HIGH" if salience > 100 else "LOW"])

    # TEST 4: Spectral Dominance (Energy Ratio)
    muzzle_band = apply_filter(data, 100, 800, fs)
    energy_hf = np.sum(crack_band**2)
    energy_lf = np.sum(muzzle_band**2)
    ratio = (energy_hf / (energy_lf + 1e-9)) * 100
    results.append(["HF/LF Energy Ratio", f"{ratio:.2f}%", "CONSISTENT" if ratio > 10 else "INCONSISTENT"])

    # CONCLUSION LOGIC
    is_shockwave = has_hf and precedes and salience > 50
    conclusion = "Shockwave Present (Supersonic Projectile)" if is_shockwave else "No Shockwave Detected"
    
    # Confidence Level
    if is_shockwave and ratio > 20: confidence = "High"
    elif is_shockwave: confidence = "Medium (Smeared/Clipped)"
    else: confidence = "High (Subsonic or Non-Ballistic)"

    # Write CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Test Suite", "Measured/Value", "Status"])
        writer.writerows(results)
        writer.writerow([])
        writer.writerow(["CONCLUSION", conclusion])
        writer.writerow(["CONFIDENCE", confidence])

    print(f"Analysis complete. Conclusion: {conclusion} ({confidence} confidence).")

if __name__ == "__main__":
    main()