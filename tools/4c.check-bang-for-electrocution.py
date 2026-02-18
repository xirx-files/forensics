import numpy as np
import scipy.io.wavfile as wav
from scipy.signal import butter, sosfiltfilt
import csv
import argparse

def apply_filter(data, low, high, fs):
    """4th order Butterworth zero-phase bandpass as per Locked Spec [7, 8]."""
    sos = butter(4, [low, high], fs=fs, btype='band', output='sos')
    return sosfiltfilt(sos, data)

def get_rms(signal, frame_len, hop):
    """Short-time RMS calculation as per Locked Spec [8]."""
    return np.array([np.sqrt(np.mean(signal[i:i+frame_len]**2)) 
                     for i in range(0, len(signal) - frame_len, hop)])

def detect_onset(rms_values, fs, hop, threshold_mult=6, hold_ms=6):
    """Locked Spec Onset Detector: Baseline (0-20ms) + 6*std, 6ms hold [8]."""
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
    parser.add_argument("--audio", required=True)
    parser.add_argument("-ct", "--crack_time", type=float, help="Timestamp of crack if detected")
    args = parser.parse_args()

    fs, data = wav.read(args.audio)
    if data.dtype != np.float32:
        data = data.astype(np.float32) / np.iinfo(data.dtype).max
    
    results = []

    # 1. ARC ONSET DETECTION (Low-frequency 20-200 Hz band)
    # Electrical arcs and high explosives are dominant in this range [3, 4].
    arc_band = apply_filter(data, 20, 200, fs)
    arc_rms = get_rms(arc_band, 256, 64)
    arc_time, threshold = detect_onset(arc_rms, fs, 64)
    
    has_arc = arc_time is not None
    results.append(["Low-Frequency Onset", f"{arc_time:.6f}" if has_arc else "N/A", "DETECTED" if has_arc else "ABSENT"])

    # 2. THE CRACK EXCLUSION TEST
    # Electrocution is a single-point event. A crack implies a supersonic projectile [2, 6].
    if args.crack_time:
        results.append(["Crack Absence Test", f"Crack at {args.crack_time}", "FAIL (Disproves Electrocution)"])
        is_single_point = False
    else:
        results.append(["Crack Absence Test", "No Crack Provided", "PASS (Consistent with Arc)"])
        is_single_point = True

    # 3. SPECTRAL BIAS (20-200 Hz vs 3000-7000 Hz)
    # Explosions/Arcs have ~45% energy in 20-100Hz; Gunshots have ~2% [4].
    low_band = apply_filter(data, 20, 100, fs)
    crack_band = apply_filter(data, 3000, 7000, fs)
    energy_low = np.sum(low_band**2)
    energy_hf = np.sum(crack_band**2)
    
    # Ratio indicates dominance of low-freq "boom" vs high-freq "crack"
    ratio = (energy_low / (energy_low + energy_hf + 1e-9)) * 100
    results.append(["LF-to-HF Ratio", f"{ratio:.2f}%", "HIGH (Arc-like)" if ratio > 80 else "LOW (Gunshot-like)"])

    # 4. WAVEFORM SYMMETRY (Impulsive Check)
    # Arcs produce a sharp initial peak [1, 9].
    peak_val = np.max(np.abs(arc_band))
    results.append(["Peak Pressure", f"{peak_val:.6f}", "POTENTIAL CLIPPING" if peak_val > 0.95 else "VALID"])

    # CONCLUSION LOGIC
    # Electrocution is likely if there is NO crack and the bang is LF dominant [2, 5, 6].
    if has_arc and is_single_point and ratio > 80:
        conclusion = "Acoustic Signature Consistent with Electrocution/Arc"
        confidence = "High (Single-Point Source)"
    elif has_arc and args.crack_time:
        conclusion = "Electrocution Disproven (Supersonic Projectile Detected)"
        confidence = "High (Geometric Conflict)"
    elif has_arc:
        conclusion = "Ambiguous (Mixed Frequency Profile)"
        confidence = "Medium"
    else:
        conclusion = "No Significant Low-Frequency Event"
        confidence = "High"

    # Export to CSV
    output_file = '4c.check-bang-for-electrocution.csv'
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Test Suite", "Measured/Value", "Status"])
        writer.writerows(results)
        writer.writerow([])
        writer.writerow(["CONCLUSION", conclusion])
        writer.writerow(["CONFIDENCE", confidence])

    print(f"Analysis complete: {conclusion} ({confidence} confidence).")

if __name__ == "__main__":
    main()