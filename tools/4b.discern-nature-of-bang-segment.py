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

def get_envelope_decay(data, fs, start_idx, duration=0.05):
    """Locked Spec v2: Measures energy decay over 50ms to find reverb/echo."""
    win = np.abs(data[start_idx : start_idx + int(duration * fs)])
    if len(win) < 10: return 0
    # Ratio of first 10ms to last 10ms
    head = np.mean(win[:int(0.01*fs)])
    tail = np.mean(win[-int(0.01*fs):])
    return head / (tail + 1e-9)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("--v0", type=float, required=True, help="Marker: Skip pre-event audio")
    args = parser.parse_args()

    fs, data = wav.read(args.audio)
    if data.dtype != np.float32:
        data = data.astype(np.float32) / (np.iinfo(data.dtype).max if data.dtype != np.float32 else 1.0)

    # Locked Spec v2: Band Definition
    muzzle_band = apply_filter(data, 20, 250, fs)   # Primary Muzzle Pressure
    mid_band = apply_filter(data, 600, 2500, fs)    # PA System/Speaker Range
    high_band = apply_filter(data, 5000, 15000, fs) # Sibilance/Electrocution Zap
    
    results = []
    
    # Discovery Logic (Simplified to Unified Scan)
    search_start = int(args.v0 * fs)
    # distance=0.15s (150ms) to ignore 1st-order amphitheatre reflections
    peaks, _ = find_peaks(np.abs(muzzle_band[search_start:]), 
                          height=np.max(np.abs(muzzle_band[search_start:]))*0.15, 
                          distance=int(0.15*fs))
    
    for p in peaks:
        t_abs = args.v0 + (p / fs)
        idx = int(t_abs * fs)
        
        # Spectral Energy Calculations (Locked Spec v2)
        win_len = int(0.02 * fs) # 20ms analysis window
        e_low = np.sum(muzzle_band[idx : idx+win_len]**2)
        e_mid = np.sum(mid_band[idx : idx+win_len]**2)
        e_high = np.sum(high_band[idx : idx+win_len]**2)
        
        # Ratios
        m_ratio = e_low / (e_high + 1e-9)   # Low vs High (Gunshot signature)
        pa_ratio = e_mid / (e_low + 1e-9)   # Mid vs Low (Speaker/PA signature)
        decay = get_envelope_decay(data, fs, idx) # Decay (Natural vs Electronic)

        # --- Classification Logic (Locked Spec v2) ---
        if m_ratio > 10.0 and decay > 4.0:
            nature = "GENUINE_MUZZLE_BLAST" # High Low-Freq, Sharp Decay
        elif pa_ratio > 1.5:
            nature = "PA_SYSTEM_GUNSHOT_SIM" # Mid-freq bias (Speaker transducer limit)
        elif e_high > (e_low * 2.0) and decay < 2.0:
            nature = "ELECTROCUTION_ZAP"     # High-freq sustained pulse
        elif m_ratio > 5.0 and decay < 3.0:
            nature = "PETN_RIG_DETONATION"   # Explosive (Longer sustain than muzzle)
        else:
            nature = "UNDETERMINED_IMPULSE"

        results.append({
            "A_Time": round(t_abs, 4),
            "Muzzle_Ratio": round(m_ratio, 2),
            "PA_Bias": round(pa_ratio, 2),
            "Decay_Factor": round(decay, 2),
            "Classification": nature,
            "Dist_m": "N/A" # Defer to 4c Reconciler
        })

    df = pd.DataFrame(results)
    out_name = f"4b.discern-nature-{os.path.basename(args.audio)}.csv"
    df.to_csv(out_name, index=False)
    print(f"V11: Forensic Classification complete. Nature identified for {len(results)} pulses.")

if __name__ == "__main__":
    main()
