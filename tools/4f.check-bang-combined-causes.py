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

def detect_onset_logic(rms_values, fs, hop, threshold, hold_ms=6):
    """Locked Spec Onset Detector with fixed 6ms hold condition."""
    hold_frames = int(hold_ms * (fs / 1000) / hop)
    for i in range(len(rms_values) - hold_frames):
        if np.all(rms_values[i:i+hold_frames] > threshold):
            return i * (hop / fs)
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("-t0", "--visual_onset", type=float, default=0.0, 
                        help="Visual onset of collar motion as per spec")
    args = parser.parse_args()

    fs, data = wav.read(args.audio)
    if data.dtype != np.float32:
        data = data.astype(np.float32) / np.iinfo(data.dtype).max
    
    # 1. DEFINE BASELINE (0-20ms after t0)
    # This isolates the direct sound path from environmental reflections [2, 7]
    t0_sample = int(args.visual_onset * fs)
    baseline_window = data[t0_sample : t0_sample + int(0.02 * fs)]
    
    results = []

    # 2. MUZZLE BLAST (BANG) DETECTION: 50-300 Hz [7-9]
    bang_band = apply_filter(data, 50, 300, fs)
    bang_rms = get_rms(bang_band, 256, 64) # 5.33ms frame, 1.33ms hop
    
    b_base_rms = get_rms(apply_filter(baseline_window, 50, 300, fs), 256, 64)
    b_threshold = np.mean(b_base_rms) + (6 * np.std(b_base_rms))
    
    bang_time = detect_onset_logic(bang_rms, fs, 64, b_threshold)
    has_bang = bang_time is not None
    results.append(["Muzzle Blast (Bang)", f"{bang_time:.6f}" if has_bang else "ABSENT"])

    # 3. MULTI-BAND CRACK DETECTION [1-3]
    # Scan three specific bands to find the most salient transient
    crack_bands = [(500, 1500), (1500, 3000), (3000, 7000)]
    best_crack_time = None
    max_salience = 0

    for low, high in crack_bands:
        f_data = apply_filter(data, low, high, fs)
        f_rms = get_rms(f_data, 128, 32) # 2.67ms frame, 0.67ms hop
        
        # Spec Threshold: baseline_mean + 60 (salience-weighted) [1]
        f_base_rms = get_rms(apply_filter(baseline_window, low, high, fs), 128, 32)
        f_mean = np.mean(f_base_rms)
        f_std = np.std(f_base_rms) + 1e-9
        f_threshold = f_mean + 60 # Using 60 as a fixed salience offset
        
        c_time = detect_onset_logic(f_rms, fs, 32, f_threshold)
        
        # Calculate Salience Score [1, 10]
        salience = (np.max(f_rms[:int(0.12*fs/32)]) - f_mean) / f_std
        
        if c_time and salience > max_salience:
            max_salience = salience
            best_crack_time = c_time

    has_crack = best_crack_time is not None
    results.append(["Shockwave (Crack)", f"{best_crack_time:.6f}" if has_crack else "ABSENT"])
    results.append(["Max Crack Salience", f"{max_salience:.2f}"])

    # 4. SPECTRAL ENERGY RATIO (Gunshot vs. Explosion) [11, 12]
    # Gunshots have ~25% energy in 3-7kHz; Explosions have ~2%
    lf_energy = np.sum(apply_filter(data, 20, 100, fs)**2)
    hf_energy = np.sum(apply_filter(data, 3000, 7000, fs)**2)
    ratio_hf = (hf_energy / (lf_energy + hf_energy + 1e-9)) * 100
    results.append(["3-7kHz Energy Ratio", f"{ratio_hf:.2f}%"])

    # 5. HARDWARE LIMIT CHECK (PA Playback Verification) [12]
    # Check 16-17 kHz band; PA speakers roll off above 10-15 kHz
    pa_limit_band = apply_filter(data, 16000, 17000, fs)
    pa_energy = np.sum(pa_limit_band**2)
    pa_status = "LIVE SHOT" if pa_energy > (hf_energy * 0.05) else "PA LIMIT"
    results.append(["PA Limit Status", pa_status])

    # CONCLUSION LOGIC
    if has_crack and has_bang and best_crack_time < bang_time:
        conclusion = "Confirmed Supersonic Gunshot (Trajectory + Muzzle)"
        confidence = "High"
    elif has_crack and pa_status == "LIVE SHOT":
        conclusion = "Likely Gunshot (Muzzle Shadowed/Distant)"
        confidence = "Medium"
    elif ratio_hf < 5:
        conclusion = "Low-Frequency Explosive Event (Theories 6, 7)"
        confidence = "High"
    else:
        conclusion = "Acoustic Event Ambiguous"
        confidence = "Low"

    # EXPORT CSV
    output_file = '4f.check-bang-combined-causes.csv'
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value", "Notes"])
        writer.writerows(results)
        writer.writerow([])
        writer.writerow(["FINAL CONCLUSION", conclusion])
        writer.writerow(["CONFIDENCE", confidence])

    print(f"Analysis complete. Conclusion: {conclusion}")

if __name__ == "__main__":
    main()