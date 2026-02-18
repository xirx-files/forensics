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
    """Short-time RMS calculation for onset detection."""
    return np.array([np.sqrt(np.mean(signal[i:i+frame_len]**2)) 
                     for i in range(0, len(signal) - frame_len, hop)])

def detect_onset(rms_values, fs, hop, threshold_mult=6, hold_ms=6, is_crack=False):
    """
    Locked Spec Onset Detector. 
    Uses a 0-20ms baseline to isolate direct sound from reflections.
    """
    baseline_len = int(0.02 * fs / hop)
    baseline = rms_values[:baseline_len]
    b_mean = np.mean(baseline)
    b_std = np.std(baseline)
    
    # Spec [3]: Bang uses 6*std; Crack uses +60 (salience-based)
    threshold = b_mean + (60 if is_crack else 6 * b_std)
    
    hold_frames = int(hold_ms * (fs / 1000) / hop)
    for i in range(len(rms_values) - hold_frames):
        if np.all(rms_values[i:i+hold_frames] > threshold):
            return i * (hop / fs), threshold
    return None, threshold

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", default="mono_event_audio.wav")
    args = parser.parse_args()

    fs, data = wav.read(args.audio)
    if data.dtype != np.float32:
        data = data.astype(np.float32) / np.iinfo(data.dtype).max
    
    results = []

    # 1. SHOCKWAVE ANALYSIS (Theories 1, 3, 4, 5)
    # Scanning high-frequency bands for N-wave signature [4]
    crack_band = apply_filter(data, 3000, 7000, fs)
    crack_rms = get_rms(crack_band, 128, 32)
    crack_time, _ = detect_onset(crack_rms, fs, 32, is_crack=True)
    has_crack = crack_time is not None

    # 2. MUZZLE BLAST ANALYSIS (Theories 1-5, 8)
    # Scanning low-frequency band (50-300 Hz) [5]
    bang_band = apply_filter(data, 50, 300, fs)
    bang_rms = get_rms(bang_band, 256, 64)
    bang_time, _ = detect_onset(bang_rms, fs, 64)
    has_bang = bang_time is not None

    # 3. SPECTRAL DIAGNOSTICS
    # Energy Ratios to distinguish Gunshots from Explosions/Arcs [6]
    he_band = apply_filter(data, 20, 100, fs)
    muzzle_band = apply_filter(data, 100, 500, fs)
    energy_he = np.sum(he_band**2)
    energy_muzzle = np.sum(muzzle_band**2)
    he_ratio = (energy_he / (energy_he + energy_muzzle + 1e-9)) * 100

    # PA Roll-off check (>12kHz) for Playback Theory [7, 8]
    pa_check_band = apply_filter(data, 12000, 17000, fs)
    energy_pa_range = np.sum(pa_check_band**2)
    hf_total_energy = np.sum(crack_band**2)
    pa_ratio = (energy_pa_range / (hf_total_energy + 1e-9)) * 100

    # 4. DATA LOGGING
    results.append(["Shockwave (Crack) Onset", f"{crack_time:.6f}" if has_crack else "ABSENT", "PASS" if has_crack else "FAIL"])
    results.append(["Muzzle Blast (Bang) Onset", f"{bang_time:.6f}" if has_bang else "ABSENT", "PASS" if has_bang else "FAIL"])
    
    if has_crack and has_bang:
        delta = (bang_time - crack_time) * 1000
        results.append(["Crack-Bang Delta", f"{delta:.2f} ms", "GEOMETRY DEPENDENT"])
        precedence = crack_time < bang_time
        results.append(["Precedence Test", "Crack precedes Bang", "VALID" if precedence else "INVALID"])
    
    results.append(["HE/Muzzle Ratio", f"{he_ratio:.2f}%", "GUNSHOT" if he_ratio < 25 else "EXPLOSIVE/ARC"])
    results.append(["PA Limit Ratio (>12kHz)", f"{pa_ratio:.2f}%", "LIVE SHOT" if pa_ratio > 2 else "PA PLAYBACK"])

    # 5. COMBINED CONCLUSION LOGIC
    confidence = "High"
    if has_crack and has_bang and pa_ratio > 2:
        conclusion = "Confirmed Supersonic Gunshot (Theories 1, 3, 4, or 5)"
    elif has_bang and not has_crack:
        if he_ratio > 40:
            conclusion = "Explosion or Shaped Charge (Theory 7)"
        else:
            conclusion = "Subsonic Shot or Blank (Theory 2)"
    elif has_crack and pa_ratio < 1:
        conclusion = "Acoustic Playback via PA (Theory 8)"
        confidence = "Medium (Requires TDOA check)"
    else:
        conclusion = "Acoustic Event Ambiguous"
        confidence = "Low (Clipped/Smeared)"

    # 6. EXPORT TO CSV
    output_file = '4f.check-bang-combined-causes.csv'
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Test Name", "Measured Value", "Status"])
        writer.writerows(results)
        writer.writerow([])
        writer.writerow(["FINAL CONCLUSION", conclusion])
        writer.writerow(["CONFIDENCE LEVEL", confidence])

    print(f"Combined assessment complete. Conclusion: {conclusion}")

if __name__ == "__main__":
    main()