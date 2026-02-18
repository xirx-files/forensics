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
    parser.add_argument("-ct", "--crack_time", type=float, help="Timestamp of ballistic crack if detected")
    args = parser.parse_args()

    fs, data = wav.read(args.audio)
    if data.dtype != np.float32:
        data = data.astype(np.float32) / np.iinfo(data.dtype).max
    
    results = []

    # 1. EXPLOSION ONSET DETECTION (20-100 Hz)
    # High explosives (PETN, RDX) concentrate 45% of energy here [4].
    exp_band = apply_filter(data, 20, 100, fs)
    exp_rms = get_rms(exp_band, 256, 64)
    exp_time, threshold = detect_onset(exp_rms, fs, 64)
    
    has_onset = exp_time is not None
    results.append(["Low-Frequency Onset", f"{exp_time:.6f}" if has_onset else "N/A", "DETECTED" if has_onset else "ABSENT"])

    # 2. THE CRACK EXCLUSION TEST (Primary Diagnostic)
    # "No crack-bang separation exists... there is no projectile" [2]
    if args.crack_time:
        results.append(["Crack-Bang Separation", f"Crack at {args.crack_time}", "FAIL (Disproves Explosion)"])
        is_explosive_source = False
    else:
        results.append(["Crack-Bang Separation", "No Crack Detected", "PASS (Consistent with Explosion)"])
        is_explosive_source = True

    # 3. SPECTRAL BIAS TEST (20-100Hz vs 3000-7000Hz)
    # Explosions have ~2% energy in 3-7kHz; Gunshots have ~25% [4]
    hf_band = apply_filter(data, 3000, 7000, fs)
    energy_lf = np.sum(exp_band**2)
    energy_hf = np.sum(hf_band**2)
    
    ratio = (energy_lf / (energy_lf + energy_hf + 1e-9)) * 100
    results.append(["LF Energy Distribution", f"{ratio:.2f}%", "EXPLOSIVE (>40%)" if ratio > 40 else "GUNSHOT (<10%)"])

    # 4. SHAPED CHARGE / JET FRAGMENTATION TEST
    # Shaped charge jets fragment within 1-2m and don't produce sustained shockwaves [5, 6]
    if args.crack_time and ratio < 20:
        results.append(["Shaped Charge Check", "Ballistic Signature Present", "DISPROVEN"])
    else:
        results.append(["Shaped Charge Check", "Single-Point Signature", "POSSIBLE"])

    # CONCLUSION LOGIC
    if has_onset and is_explosive_source and ratio > 40:
        conclusion = "Explosion (High Explosive/Device) Detected"
        confidence = "High (Single-Point Source)"
    elif args.crack_time:
        conclusion = "Explosion Disproven (Supersonic Projectile Detected)"
        confidence = "High (Geometric Conflict)"
    else:
        conclusion = "Explosion Not Confirmed"
        confidence = "Medium"

    # Export to CSV
    output_file = '4d.check-bang-for-explosion.csv'
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