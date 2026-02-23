import argparse
import numpy as np
import scipy.io.wavfile as wav
from scipy.signal import butter, sosfiltfilt
import matplotlib.pyplot as plt
import csv
import math
import os

def apply_filter(data, low, high, fs):
    sos = butter(4, [low, high], fs=fs, btype='band', output='sos')
    return sosfiltfilt(sos, data)

def get_rms(signal, frame_len, hop):
    return np.array([np.sqrt(np.mean(signal[i:i+frame_len]**2)) 
                     for i in range(0, len(signal) - frame_len, hop)])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("--v0", type=float, required=True)
    parser.add_argument("--expected_offsets", type=str, default="0,133,300")
    parser.add_argument("--temp_c", type=float, default=28.33)
    parser.add_argument("--v_bullet", type=float, default=850.0)
    args = parser.parse_args()

    fs, data = wav.read(args.audio)
    if data.dtype != np.float32:
        data = data.astype(np.float32) / (np.iinfo(data.dtype).max if data.dtype != np.float32 else 1.0)

    # Calculation Constants
    c = 331.3 * math.sqrt(1 + args.temp_c / 273.15)
    M = args.v_bullet / c
    theta_m = math.degrees(math.asin(1/M))

    # Signal Processing
    hf_band = apply_filter(data, 2500, 8000, fs)
    lf_band = apply_filter(data, 100, 1000, fs)
    
    hop = 16
    hf_rms = get_rms(hf_band, 64, hop)
    baseline_rms = hf_rms[:int(0.05 * fs / hop)]
    threshold = np.mean(baseline_rms) + (20 * np.std(baseline_rms))
    
    # Precision Scan: Focus on V0 precursor zone
    start_idx = max(0, int((args.v0 - 0.35) * fs / hop))
    
    raw_onsets = []
    i = start_idx
    while i < len(hf_rms) - 5:
        if hf_rms[i] > threshold:
            t_curr = i * (hop / fs)
            idx = int(t_curr * fs)
            
            # HIGH PRECISION WINDOW: 10ms (Forensic Standard for N-Wave)
            win_size = int(0.01 * fs) 
            h_en = np.sum(hf_band[idx : idx + win_size]**2)
            l_en = np.sum(lf_band[idx : idx + win_size]**2)
            ratio = (h_en / (l_en + 1e-9)) * 100
            
            if ratio > 8.0:
                raw_onsets.append((t_curr, ratio))
                i += int(0.02 * fs / hop) # 20ms lockout
            else: i += 1
        else: i += 1

    video_offsets = [float(x) for x in args.expected_offsets.split(',')]
    results = []
    
    for idx, (t_crack, ratio) in enumerate(raw_onsets):
        # Muzzle Bang Identification
        search_start, search_end = int(t_crack * fs), int((t_crack + 0.15) * fs)
        search_window = lf_band[search_start : search_end]
        t_bang = t_crack + (np.argmax(np.abs(search_window)) / fs)
        
        lag = t_bang - t_crack
        dist = lag * ((args.v_bullet * c) / (args.v_bullet - c))
        rel_v0 = (t_crack - args.v0) * 1000
        p_lead = min([v - rel_v0 for v in video_offsets if v - rel_v0 > -5], default=0)

        results.append({
            "Strike": idx+1, "TS": round(t_crack,4), "V0_Rel_ms": round(rel_v0,2), 
            "Precedence": round(p_lead,2), "HF_Ratio": round(ratio,2), 
            "Lag_ms": round(lag*1000,2), "Dist_m": round(dist,2),
            "Logic": f"Strike {idx+1}: High-Precision {ratio:.1f}% HF Ratio leads V0 by {p_lead:.1f}ms. Dist={dist:.1f}m."
        })

        # Forensic Output Graphs
        y_s, y_e = max(0, int((t_crack-0.01)*fs)), min(len(data), int((t_bang+0.02)*fs))
        y_slice = data[y_s:y_e]
        x_slice = np.linspace(t_crack-0.01, t_crack-0.01 + (len(y_slice)/fs), len(y_slice))
        
        plt.figure(figsize=(10,4))
        plt.plot(x_slice, y_slice, color='black', linewidth=0.7)
        plt.title(f"Strike {idx+1} | Lag: {lag*1000:.1f}ms | Mach ∠: {theta_m:.1f}°")
        plt.axvline(t_crack, color='g', label='Crack'); plt.axvline(t_bang, color='r', label='Bang')
        plt.xlabel("Time (s)"); plt.ylabel("Norm. Amplitude"); plt.legend(); plt.grid(True, alpha=0.15)
        plt.savefig(f"4a.check-bang-for-shockwave-strike_{idx+1}-analysis.png"); plt.close()

    csv_file = f"4a.check-bang-for-shockwave-{os.path.basename(args.audio)}.csv"
    with open(csv_file, 'w', newline='') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader(); writer.writerows(results)

    if results:
        plt.figure(figsize=(12,6))
        plt.plot(np.linspace(0, len(data)/fs, len(data)), hf_band, color='red', alpha=0.4)
        plt.xlim(results[0]['TS'] - 0.05, results[-1]['TS'] + 0.05)
        plt.title("Ballistic Sequence (10ms Window Precision View)")
        for r in results: plt.axvline(r['TS'], color='blue', linestyle='--')
        plt.savefig("4a.check-bang-for-shockwave-sequence_zoom_view.png"); plt.close()

    print(f"V13 Final Precision Success. Scanned {len(results)} strikes.")

if __name__ == "__main__":
    main()