import argparse
import numpy as np
import scipy.io.wavfile as wav
from scipy.signal import butter, sosfiltfilt, find_peaks
import matplotlib.pyplot as plt
import pandas as pd
import math
import os

def apply_filter(data, low, high, fs):
    sos = butter(4, [low, high], fs=fs, btype='band', output='sos')
    return sosfiltfilt(sos, data)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("--v0", type=float, required=True)
    parser.add_argument("--expected_offsets", type=str, default="0,133,300")
    parser.add_argument("--shockwave-csv")
    parser.add_argument("--motion-event-summary-csv")
    parser.add_argument("--temp_c", type=float, default=28.33)
    args = parser.parse_args()

    fs, data = wav.read(args.audio)
    if data.dtype != np.float32:
        data = data.astype(np.float32) / (np.iinfo(data.dtype).max if data.dtype != np.float32 else 1.0)

    c = 331.3 * math.sqrt(1 + args.temp_c / 273.15)
    
    # Forensic Bands
    muzzle_band = apply_filter(data, 20, 300, fs)
    high_band = apply_filter(data, 3000, 12000, fs)
    
    sw_df = pd.read_csv(args.shockwave_csv) if args.shockwave_csv else None
    motion_df = pd.read_csv(args.motion_event_summary_csv) if args.motion_event_summary_csv else None
    
    offsets = [float(x) for x in args.expected_offsets.split(',')]
    results = []

    for idx, offset in enumerate(offsets):
        v_strike = args.v0 + (offset / 1000.0)
        origin = motion_df.iloc[idx]['Origin'] if motion_df is not None and idx < len(motion_df) else "Unknown"
        
        # --- V7 TEMPORAL FLOOR LOGIC ---
        # If shockwave data exists, we use it as an anchor, 
        # BUT we never allow the search to start before the visual impact (v_strike).
        t_sw = sw_df.iloc[idx]['TS'] if sw_df is not None and idx < len(sw_df) else 0
        search_start_ts = max(v_strike, t_sw)
        
        search_start = int(search_start_ts * fs)
        search_end = int((search_start_ts + 0.45) * fs)
        window_low = np.abs(muzzle_band[search_start : search_end])
        
        # Peak Detection
        peaks, props = find_peaks(window_low, height=np.max(window_low)*0.3, distance=int(0.05*fs))
        
        if len(peaks) > 0:
            best_peak = peaks[np.argmax(props['peak_heights'])]
            t_bang = search_start_ts + (best_peak / fs)
            lag_ms = (t_bang - v_strike) * 1000
            dist_m = (lag_ms / 1000.0) * c
            
            # Spectral Validation (Ratio Calculation)
            idx_b = int(t_bang * fs)
            check_win = int(0.01 * fs)
            l_en = np.sum(muzzle_band[idx_b : idx_b+check_win]**2)
            h_en = np.sum(high_band[idx_b : idx_b+check_win]**2)
            ratio = l_en / (h_en + 1e-9)
            
            status = "CONFIRMED_MUZZLE" if ratio > 2.0 else "NON_BALLISTIC_IMPULSE"
            sw_dist = sw_df.iloc[idx]['Dist_m'] if sw_df is not None and idx < len(sw_df) else 0
            delta = abs(dist_m - sw_dist) if sw_dist > 0 else 0

            results.append({
                "Strike": idx+1, "V0_Strike": round(v_strike, 4), "Bang_TS": round(t_bang, 4),
                "Lag_ms": round(lag_ms, 2), "Dist_m": round(dist_m, 2), "SW_Delta_m": round(delta, 2),
                "Status": status
            })

            # --- PLOTTING ---
            plt.figure(figsize=(12, 5))
            p_start, p_end = max(0, int((v_strike-0.1)*fs)), min(len(data), int((t_bang+0.2)*fs))
            x_axis = np.linspace((v_strike-0.1), (v_strike-0.1) + (p_end-p_start)/fs, p_end-p_start)
            
            plt.plot(x_axis, data[p_start:p_end], color='black', alpha=0.15, label="Raw Audio")
            plt.plot(x_axis, muzzle_band[p_start:p_end], color='darkorange', label="Muzzle (20-300Hz)")
            
            plt.axvline(v_strike, color='blue', linestyle='--', label=f"V0 Impact ({origin})")
            if t_sw > 0:
                plt.axvline(t_sw, color='green', linestyle=':', label="Shockwave (4a)")
            plt.axvline(t_bang, color='red', linewidth=2, label=f"Muzzle Arrival (Ratio: {ratio:.1f})")
            
            plt.title(f"Strike {idx+1} | {status} | Dist: {dist_m:.1f}m | SW Delta: {delta:.1f}m")
            plt.xlabel("Time (s)"); plt.ylabel("Amplitude"); plt.legend(loc='upper right'); plt.grid(True, alpha=0.2)
            plt.savefig(f"4b.check-bang-for-muzzleblast-forensic-triangulation-strike_{idx+1}.png"); plt.close()

    pd.DataFrame(results).to_csv(f"4b.check-bang-for-muzzleblast-{os.path.basename(args.audio)}.csv", index=False)
    print(f"V7 Success. Temporal Floor enforced for {len(results)} strikes.")

if __name__ == "__main__":
    main()