import argparse
import numpy as np
import scipy.io.wavfile as wav
import pandas as pd
import matplotlib.pyplot as plt
import math
import os

def apply_filter(data, low, high, fs):
    sos = butter(4, [low, high], fs=fs, btype='band', output='sos')
    return sosfiltfilt(sos, data)

from scipy.signal import butter, sosfiltfilt

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("--v0", type=float, required=True)
    parser.add_argument("--motion-csv", required=True)
    parser.add_argument("--shockwave-csv", required=True)
    parser.add_argument("--muzzle-csv", required=True)
    parser.add_argument("--temp_c", type=float, default=28.33)
    args = parser.parse_args()

    c = 331.3 * math.sqrt(1 + args.temp_c / 273.15)
    fs, data = wav.read(args.audio)
    if data.dtype != np.float32:
        data = data.astype(np.float32) / (np.iinfo(data.dtype).max if data.dtype != np.float32 else 1.0)

    # Load and Pre-process
    motion_df = pd.read_csv(args.motion_csv)
    motion_df['Abs_TS'] = args.v0 + (motion_df['Offset(ms)'] / 1000.0)
    sw_df = pd.read_csv(args.shockwave_csv)
    muz_df = pd.read_csv(args.muzzle_csv)
    muzzle_band = apply_filter(data, 20, 300, fs)

    true_shots = muz_df['A_Time'].unique()
    allocated_motion = set()
    chain_report = []
    map_points = []

    for shot_idx, m_ts in enumerate(sorted(true_shots)):
        m_ratio = muz_df[muz_df['A_Time'] == m_ts]['Ratio'].iloc[0]
        
        # 1. TEMPORAL CAUSALITY: Find strikes within 500ms BEFORE muzzle arrival
        # 2. UNIQUENESS: Exclude strikes already claimed by previous shots
        candidates = motion_df[(motion_df['Abs_TS'] <= m_ts) & 
                               (motion_df['Abs_TS'] > m_ts - 0.5) &
                               (~motion_df['Abs_TS'].isin(allocated_motion))].copy()
        
        if candidates.empty: continue
        
        primary_ts = candidates['Abs_TS'].min()
        true_dist = (m_ts - primary_ts) * c
        
        for _, row in candidates.iterrows():
            allocated_motion.add(row['Abs_TS'])
            is_primary = (row['Abs_TS'] == primary_ts)
            
            chain_report.append({
                "Shot_ID": shot_idx + 1, "Muzzle_TS": m_ts, "Visual_TS": row['Abs_TS'],
                "Dist_m": round((m_ts - row['Abs_TS']) * c, 2), "Ratio": m_ratio,
                "Classification": "PRIMARY_STRIKE" if is_primary else "CHAIN_REACTION",
                "True_Range": round(true_dist, 2) if is_primary else "N/A"
            })
            
            if is_primary:
                map_points.append({"id": shot_idx+1, "r": true_dist, "origin": row['Origin']})

        # --- DETAILED PLOT ---
        plt.figure(figsize=(12, 5))
        p_start, p_end = int((primary_ts-0.15)*fs), int((m_ts+0.1)*fs)
        x = np.linspace(primary_ts-0.15, primary_ts-0.15 + (p_end-p_start)/fs, p_end-p_start)
        
        plt.plot(x, data[p_start:p_end], color='grey', alpha=0.3, label="Raw Audio")
        plt.plot(x, muzzle_band[p_start:p_end], color='darkorange', alpha=0.8, label="Muzzle (20-300Hz)")
        
        # depiction of Shockwaves from 4a
        linked_sw = sw_df[(sw_df['TS'] > primary_ts - 0.2) & (sw_df['TS'] < m_ts)]
        for s_ts in linked_sw['TS']:
            plt.axvline(s_ts, color='cyan', linestyle=':', alpha=0.6, label="Shockwave (4a)")
            
        plt.axvline(primary_ts, color='red', linewidth=2, label=f"Primary Strike ({true_dist:.1f}m)")
        plt.axvline(m_ts, color='blue', linewidth=2, label=f"Muzzle Arrival (Ratio: {m_ratio:.1f})")
        
        plt.title(f"Shot {shot_idx+1} Ballistic Reconciliation | Dist: {true_dist:.1f}m")
        plt.legend(loc='upper right', fontsize='small'); plt.grid(True, alpha=0.2)
        plt.savefig(f"4c.shot_{shot_idx+1}_reconciliation.png"); plt.close()

    # --- TRIANGULATION MAP ---
    if map_points:
        plt.figure(figsize=(7, 7))
        plt.scatter(0, 0, color='green', marker='X', s=100, label='Camera (Mic)')
        for p in map_points:
            # Map "West (Behind)" to 270 degrees in world space
            angle = np.radians(270) 
            plt.scatter(p['r']*np.cos(angle), p['r']*np.sin(angle), s=100, label=f"Shooter {p['id']} ({p['r']:.1f}m)")
            circle = plt.Circle((0,0), p['r'], color='grey', fill=False, linestyle='--', alpha=0.3)
            plt.gca().add_artist(circle)
        
        plt.xlim(-150, 150); plt.ylim(-150, 150); plt.gca().set_aspect('equal')
        plt.title("Forensic Triangulation: Local World Coordinates"); plt.legend(); plt.grid(True, alpha=0.3)
        plt.savefig("4c.shooter_triangulation_map.png"); plt.close()

    pd.DataFrame(chain_report).to_csv(f"4c.final-reconciled-report-{os.path.basename(args.audio)}.csv", index=False)
    print("V10.5 Complete. Unique Causality Enforced. Map Generated.")

if __name__ == "__main__":
    main()
