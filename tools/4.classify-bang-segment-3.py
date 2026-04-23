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
    win = np.abs(data[start_idx : start_idx + int(duration * fs)])
    if len(win) < 10: return 0
    head = np.mean(win[:int(0.01*fs)])
    tail = np.mean(win[-int(0.01*fs):])
    return head / (tail + 1e-9)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("--v0", type=float, required=True, help="Incident start time (s)")
    args = parser.parse_args()

    fs, data = wav.read(args.audio)
    if data.dtype != np.float32:
        data = data.astype(np.float32) / (np.iinfo(data.dtype).max if data.dtype != np.float32 else 1.0)

    # Spectral Band Definitions
    muzzle_band = apply_filter(data, 20, 250, fs)   # Low-end pressure
    mid_band = apply_filter(data, 600, 2500, fs)     # PA/Speaker/Mechanical
    hedm_band = apply_filter(data, 2500, 5000, fs)   # HEDM Shattering/Bristance
    high_band = apply_filter(data, 5000, 15000, fs)  # Sibilance/Electronic noise

    results = []
    search_start = int(args.v0 * fs)
    
    # Scan for all impulse peaks
    peaks, _ = find_peaks(np.abs(muzzle_band[search_start:]), 
                          height=np.max(np.abs(muzzle_band[search_start:]))*0.10, # Lowered threshold for sensitivity
                          distance=int(0.12*fs)) # Minimum 120ms between events

    for event_id, p in enumerate(peaks):
        t_abs = args.v0 + (p / fs)
        idx = int(t_abs * fs)
        win_len = int(0.02 * fs) # 20ms window

        # Energy Integrals
        e_low = np.sum(muzzle_band[idx : idx+win_len]**2)
        e_mid = np.sum(mid_band[idx : idx+win_len]**2)
        e_hedm = np.sum(hedm_band[idx : idx+win_len]**2)
        e_high = np.sum(high_band[idx : idx+win_len]**2)

        # Ratios
        m_ratio = e_low / (e_high + 1e-9)
        pa_ratio = e_mid / (e_low + 1e-9)
        h_ratio = e_hedm / (e_high + 1e-9)
        decay = get_envelope_decay(data, fs, idx)

        nature = []
        
        # 1. PRIORITY CHECK: HEDM (High Energy Density Materials)
        # Characteristic: High h_ratio (mid-high transients) + sharp decay
        if h_ratio > 12.0 and decay < 1.2:
            nature.append("HEDM_DETONATION")
        
        # 2. Standard Explosives (PETN)
        elif m_ratio > 5.0 and 0.5 <= decay < 3.0:
            nature.append("PETN_RIG_DETONATION")

        # 3. Electrical/Mechanical Failures
        if pa_ratio > 5.0:
            nature.append("ELECTRICAL_EQUIP_FAILURE")
        elif pa_ratio > 1.5:
            nature.append("PA_SYSTEM_GUNSHOT_SIM")

        # 4. Firearm Muzzle Blast
        if m_ratio > 10.0 and decay > 4.0:
            nature.append("GENUINE_MUZZLE_BLAST")

        # 5. Precursor/Trigger
        if m_ratio > 50.0 and decay < 0.5:
            nature.append("ARC_FLASH_TRIGGER")

        if not nature:
            nature.append("UNDETERMINED_IMPULSE")

        # Forensic Logic: 1-ORDER vs REFLECTION
        source_type = "1-ORDER"
        if results:
            prev = results[-1]
            time_diff = t_abs - prev["A_Time"]
            
            # Re-implementing the dual-variance forensic check
            m_var = abs(m_ratio - prev["Muzzle_Ratio"]) / (prev["Muzzle_Ratio"] + 1e-9)
            pa_var = abs(pa_ratio - prev["PA_Bias"]) / (prev["PA_Bias"] + 1e-9)
            
            # If timing is tight AND the spectrum is nearly identical (within 25%), it's a reflection
            if time_diff < 0.25 and (m_var < 0.25 and pa_var < 0.25):
                source_type = "REFLECTION"

        results.append({
            "Event_ID": event_id + 1,
            "A_Time": round(t_abs, 4),
            "Muzzle_Ratio": round(m_ratio, 2),
            "PA_Bias": round(pa_ratio, 2),
            "HEDM_Ratio": round(h_ratio, 2),
            "Decay_Factor": round(decay, 2),
            "Source_Type": source_type,
            "Classification": ";".join(nature)
        })

    # Save and Plot
    if results:
        df = pd.DataFrame(results)
        base_name = os.path.basename(args.audio)
        df.to_csv(f"forensic_report_{base_name}.csv", index=False)
        
        # Visualization
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
        time_axis = np.linspace(0, len(data)/fs, len(data))
        ax1.plot(time_axis, data, color='grey', alpha=0.3)
        
        for res in results:
            main_cls = res["Classification"].split(';')[0]
            color = CLASS_COLORS.get(main_cls, "black")
            ax1.axvline(res["A_Time"], color=color, linestyle='--', alpha=0.6)
            ax1.text(res["A_Time"], np.max(data)*0.7, f"E{res['Event_ID']}\n{main_cls}", 
                     rotation=90, color=color, fontsize=7, fontweight='bold')

        f, t_spec, Sxx = spectrogram(data, fs)
        ax2.pcolormesh(t_spec, f, 10 * np.log10(Sxx + 1e-9), shading='gouraud', cmap='magma')
        ax2.set_ylabel("Frequency (Hz)")
        ax2.set_ylim(0, 16000)
        plt.tight_layout()
        plt.savefig(f"forensic_plot_{base_name}.png")
        print(f"Report generated: {len(results)} events found.")
    else:
        print("No impulses detected.")

if __name__ == "__main__":
    main()
