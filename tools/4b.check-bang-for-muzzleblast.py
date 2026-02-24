import argparse
import numpy as np
import scipy.io.wavfile as wav
from scipy.signal import butter, sosfiltfilt, find_peaks
import pandas as pd
import math
import os

def apply_filter(data, low, high, fs):
    sos = butter(4, [low, high], fs=fs, btype='band', output='sos')
    return sosfiltfilt(sos, data)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("--v0", type=float, required=True, help="Marker: Skip speech/sibilance")
    parser.add_argument("--motion-csv", help="Optional: 3b Summary for Video-Assisted mode")
    parser.add_argument("--temp_c", type=float, default=28.33)
    args = parser.parse_args()

    fs, data = wav.read(args.audio)
    if data.dtype != np.float32:
        data = data.astype(np.float32) / (np.iinfo(data.dtype).max if data.dtype != np.float32 else 1.0)

    c = 331.3 * math.sqrt(1 + args.temp_c / 273.15)
    muzzle_band = apply_filter(data, 20, 300, fs)
    high_band = apply_filter(data, 3000, 12000, fs)
    
    results = []
    
    # --- MODE 1: VIDEO-ASSISTED (Independent Windowing) ---
    if args.motion_csv and os.path.exists(args.motion_csv):
        print(f"Entering Video-Assisted Mode (Source: {args.motion_csv})")
        motion_df = pd.read_csv(args.motion_csv)
        for idx, row in motion_df.iterrows():
            v_strike = args.v0 + (row['Offset(ms)'] / 1000.0)
            s_start, s_end = int(v_strike * fs), int((v_strike + 0.6) * fs)
            win = np.abs(muzzle_band[s_start : min(s_end, len(data))])
            
            peaks, props = find_peaks(win, height=np.max(win)*0.25, distance=int(0.04*fs))
            if len(peaks) > 0:
                best_p = peaks[np.argmax(props['peak_heights'])]
                t_bang = v_strike + (best_p / fs)
                
                # Spectral Analysis
                idx_b = int(t_bang * fs)
                l_en = np.sum(muzzle_band[idx_b:idx_b+441]**2)
                h_en = np.sum(high_band[idx_b:idx_b+441]**2)
                ratio = l_en / (h_en + 1e-9)
                
                results.append({
                    "Event": f"V-{idx}", "V_Time": round(v_strike, 4), "A_Time": round(t_bang, 4),
                    "Lag_ms": round((t_bang - v_strike)*1000, 2), "Dist_m": round((t_bang - v_strike)*c, 2),
                    "Ratio": round(ratio, 2), "Origin": row['Origin'], "Status": "VALIDATED_BY_MOTION"
                })

    # --- MODE 2: AUDIO-ONLY (Autonomous Discovery) ---
    else:
        print("Entering Audio-Only Mode (Autonomous Discovery)")
        # Scan from v0 to EOF
        search_data = np.abs(muzzle_band[int(args.v0 * fs):])
        # Peaks must be at least 150ms apart to filter amphitheatre reverb
        peaks, props = find_peaks(search_data, height=np.max(search_data)*0.2, distance=int(0.15*fs))
        
        for idx, p in enumerate(peaks):
            t_abs = args.v0 + (p / fs)
            idx_b = int(t_abs * fs)
            l_en = np.sum(muzzle_band[idx_b:idx_b+441]**2)
            h_en = np.sum(high_band[idx_b:idx_b+441]**2)
            ratio = l_en / (h_en + 1e-9)
            
            results.append({
                "Event": f"A-{idx}", "V_Time": "N/A", "A_Time": round(t_abs, 4),
                "Lag_ms": "N/A", "Dist_m": "N/A", "Ratio": round(ratio, 2),
                "Origin": "N/A", "Status": "ACOUSTIC_DISCOVERY"
            })

    # --- FINAL FORENSIC CLASSIFICATION ---
    df_results = pd.DataFrame(results)
    if not df_results.empty:
        # 2.2 is a conservative threshold for a 44.1kHz forensic capture
        df_results['Classification'] = df_results['Ratio'].apply(
            lambda r: "MUZZLE_BLAST" if r > 2.0 else ("EXPLOSIVE_OR_ELECTRONIC" if r > 1.2 else "MECHANICAL_IMPACT")
        )
    
    out_name = f"4b.check-bang-for-muzzleblast-{os.path.basename(args.audio)}.csv"
    df_results.to_csv(out_name, index=False)
    print(f"V10: Success. Generated {out_name} with {len(results)} candidate events.")

if __name__ == "__main__":
    main()
