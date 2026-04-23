# Forensic Impulse Classification and Acoustic Analysis Script
import argparse
import numpy as np
import scipy.io.wavfile as wav
from scipy.signal import butter, sosfiltfilt, find_peaks, spectrogram
import matplotlib.pyplot as plt
import pandas as pd
import os

# --- Configuration ---
CLASS_COLORS = {
    "ARC_FLASH_TRIGGER": "blue",
    "ELECTRICAL_EQUIP_FAILURE": "cyan",
    "PETN_RIG_DETONATION": "purple",
    "HEDM_DETONATION": "magenta", 
    "GENUINE_MUZZLE_BLAST": "red",
    "PA_SYSTEM_GUNSHOT_SIM": "orange",
    "UNDETERMINED_IMPULSE": "green"
}

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
    parser.add_argument("--v0", type=float, required=True, help="Start Marker: Skip pre-event audio")
    args = parser.parse_args()

    fs, data = wav.read(args.audio)
    if data.dtype != np.float32:
        data = data.astype(np.float32) / (np.iinfo(data.dtype).max if data.dtype != np.float32 else 1.0)

    # Locked Spec v2: Band Definition
    muzzle_band = apply_filter(data, 20, 250, fs)   # Primary Muzzle Pressure
    mid_band = apply_filter(data, 600, 2500, fs)    # PA System/Speaker Range
    hedm_band = apply_filter(data, 2500, 5000, fs) # HEDM Bristance Range
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
        e_hedm = np.sum(hedm_band[idx : idx+win_len]**2)
        e_mid = np.sum(mid_band[idx : idx+win_len]**2)
        e_high = np.sum(high_band[idx : idx+win_len]**2)
        
        # Ratios
        m_ratio = e_low / (e_high + 1e-9)   # Low vs High (Gunshot signature)
        pa_ratio = e_mid / (e_low + 1e-9)   # Mid vs Low (Speaker/PA signature)
        h_ratio = e_hedm / (e_high + 1e-9)  # HEDM Signature
        decay = get_envelope_decay(data, fs, idx) # Decay (Natural vs Electronic)

        # --- Classification Logic (Locked Spec v2) ---
        nature = []
        # 1. ARC_FLASH: Inverse decay precursor (The Trigger)
        if m_ratio > 50.0 and decay < 0.5:
            nature.append("ARC_FLASH_TRIGGER")

        # 2. TRANSFORMER/CAP_FAILURE: Massive Mid-range dominance (PA_Bias > 5.0)
        # Identifies 60Hz harmonics and resonant 'screams' in electrical gear.
        if pa_ratio > 5.0:
            nature.append("ELECTRICAL_EQUIP_FAILURE")
        elif pa_ratio > 1.5:
            nature.append("PA_SYSTEM_GUNSHOT_SIM")

        # 3. PETN_RIG: High pressure + Medium sustain vs HEDM
        if h_ratio > 15.0 and decay < 1.0:
            nature.append("HEDM_DETONATION")
        elif m_ratio > 5.0 and decay >= 0.5 and decay < 3.0:
            nature.append("PETN_RIG_DETONATION")

        # 4. GENUINE_MUZZLE: High Low-Freq, Low Mid-Freq (PA_Bias < 1.0)
        if m_ratio > 10.0 and decay > 4.0:
            nature.append("GENUINE_MUZZLE_BLAST")

        if not nature:
            nature.append("UNDETERMINED_IMPULSE")

        # --- Logic: 1-ORDER vs REFLECTION ---
        source_type = "1-ORDER" # Default for first event
        if len(results) > 0:
            prev = results[-1]
            time_diff = t_abs - prev["A_Time"]
            
            # If it happens very quickly (<150ms) AND the spectral signature is 
            # nearly identical (within 20% variance), it's likely a reflection.
            # If the signature changes significantly, it's a new strike (1-ORDER).
            m_var = abs(m_ratio - prev["Muzzle_Ratio"]) / (prev["Muzzle_Ratio"] + 1e-9)
            pa_var = abs(pa_ratio - prev["PA_Bias"]) / (prev["PA_Bias"] + 1e-9)
            
            if time_diff < 0.25 and (m_var < 0.25 and pa_var < 0.25):
                source_type = "REFLECTION"
            else:
                source_type = "1-ORDER"

        results.append({
            "A_Time": round(t_abs, 4),
            "Muzzle_Ratio": round(m_ratio, 2),
            "HEDM_Ratio": round(h_ratio, 2),
            "PA_Bias": round(pa_ratio, 2),
            "e_low": round(e_low, 2),
            "e_mid": round(e_mid, 2),
            "e_high": round(e_high, 2),
            "Decay_Factor": round(decay, 2),
            "Source_Type": source_type,
            "Classification": ";".join(nature)
        })

    # Visualization
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    time_axis = np.linspace(0, len(data)/fs, len(data))
    
    # Plot 1: Waveforms
    ax1.plot(time_axis, data, color='grey', alpha=0.3, label="Raw Audio")
    for res in results:
        color = CLASS_COLORS.get(res["Classification"], "grey")
        # Overlay the band that triggered the classification for visual confirmation
        # band_data = None
        if res["Classification"].find("GENUINE_MUZZLE_BLAST") > -1: band_data = muzzle_band
        elif res["Classification"].find("PA_SYSTEM_GUNSHOT_SIM") > -1: band_data = mid_band
        else: band_data = high_band
        ax1.plot(time_axis, band_data, color=color, linewidth=0.8, label=res["Classification"])
        
        ax1.axvline(res["A_Time"], color=color, linestyle='--', alpha=0.8)
        ax1.text(res["A_Time"], np.max(data), res["Classification"].replace(';','\n'), rotation=90, color=color, fontsize=8)
        ax2.axvline(res["A_Time"], color=color, linestyle='--', alpha=0.8)

    ax1.set_title("Forensic Impulse Classification")
    ax1.legend(loc='upper right')
    ax1.set_ylabel("Amplitude")

    # Plot 2: Spectrogram
    f, t_spec, Sxx = spectrogram(data, fs)
    ax2.pcolormesh(t_spec, f, 10 * np.log10(Sxx + 1e-9), shading='gouraud', cmap='magma')
    ax2.set_ylabel("Frequency (Hz)")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylim(0, 16000)

    plt.tight_layout()
    plt.savefig(f"4.classify-bang-segment-{os.path.basename(args.audio)}.png")
    pd.DataFrame(results).to_csv(f"4.classify-bang-segment-{os.path.basename(args.audio)}.csv", index=False)
    print(f"Forensic Impulse Analysis: {len(results)} classifications in csv and Multiview Plot generated.")

if __name__ == "__main__":
    main()
