import numpy as np
import scipy.io.wavfile as wav
from scipy.signal import butter, sosfiltfilt
import csv
import argparse

def apply_filter(data, low, high, fs):
    """4th order Butterworth zero-phase bandpass as per Locked Spec."""
    sos = butter(4, [low, high], fs=fs, btype='band', output='sos')
    return sosfiltfilt(sos, data)

def get_rms(signal, frame_len, hop):
    """Short-time RMS calculation as per Locked Spec."""
    return np.array([np.sqrt(np.mean(signal[i:i+frame_len]**2)) 
                     for i in range(0, len(signal) - frame_len, hop)])

def detect_onset(rms_values, fs, hop, threshold_mult=6, hold_ms=6):
    """Locked Spec Onset Detector: Baseline (0-20ms) + 6*std, 6ms hold."""
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
    parser.add_argument("-ct", "--crack_time", type=float, help="Timestamp of shockwave if detected")
    args = parser.parse_args()

    fs, data = wav.read(args.audio)
    if data.dtype != np.float32:
        data = data.astype(np.float32) / np.iinfo(data.dtype).max
    
    results = []
    
    # 1. INDEPENDENT BANG DETECTION (Locked Spec: 50-300 Hz)
    bang_band = apply_filter(data, 50, 300, fs)
    bang_rms = get_rms(bang_band, 256, 64)
    bang_time, threshold = detect_onset(bang_rms, fs, 64, threshold_mult=6)
    
    has_bang = bang_time is not None
    results.append(["Low-Frequency Onset", f"{bang_time:.6f}" if has_bang else "N/A", "DETECTED" if has_bang else "ABSENT"])

    # 2. GEOMETRIC RECONCILIATION
    if args.crack_time and has_bang:
        precedes = args.crack_time < bang_time
        status = "PASS" if precedes else "FAIL (Possible Echo)"
        results.append(["Precedence Test", f"{args.crack_time} < {bang_time}", status])
    elif args.crack_time:
        results.append(["Precedence Test", "N/A", "ABSENT (Shockwave Only)"])
    else:
        results.append(["Precedence Test", "N/A", "SKIPPED (No Crack Provided)"])

    # 3. ENERGY RATIO (Diagnostic even without onset)
    # Using the window around the expected bang (or whole clip if missing)
    he_band = apply_filter(data, 20, 100, fs)
    muzzle_band = apply_filter(data, 100, 500, fs)
    energy_he = np.sum(he_band**2)
    energy_muzzle = np.sum(muzzle_band**2)
    he_ratio = (energy_he / (energy_he + energy_muzzle + 1e-9)) * 100
    results.append(["HE/Muzzle Energy Ratio", f"{he_ratio:.2f}%", "CONSISTENT WITH GUNSHOT" if he_ratio < 25 else "SUSPECT EXPLOSION"])

    # CONCLUSION LOGIC
    if has_bang:
        conclusion = "Muzzle Blast Present"
        confidence = "High" if he_ratio < 10 else "Medium (Clipped)"
    elif args.crack_time:
        conclusion = "Shockwave Only (Muzzle Shadowed or Distant)"
        confidence = "Medium (Physically Plausible)"
    else:
        conclusion = "Muzzle Blast Not Confirmed"
        confidence = "High"

    # Export to CSV
    output_file = '4b.check-bang-for-muzzleblast.csv'
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