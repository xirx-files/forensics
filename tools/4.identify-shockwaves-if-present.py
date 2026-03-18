import argparse
import numpy as np
import scipy.io.wavfile as wav
from scipy.signal import butter, sosfiltfilt, find_peaks, correlate, spectrogram
import pandas as pd
import matplotlib.pyplot as plt
import os

def apply_filter(data, low, high, fs):
    sos = butter(4, [low, high], fs=fs, btype='band', output='sos')
    return sosfiltfilt(sos, data)

def calculate_tdoa(ch1, ch2, fs):
    corr = correlate(ch1, ch2, mode='full')
    lags = np.arange(-len(ch1) + 1, len(ch1))
    return lags[np.argmax(corr)] / fs

def analyze_shockwave_v9(win, fs):
    if len(win) < 10: return 0.0, 0.0, 0.0, 0.0
    p_max, p_min = np.max(win), np.abs(np.min(win))
    sym = p_max / (p_min + 1e-9)
    pk_idx = np.argmax(np.abs(win))
    rise_ms = (pk_idx / fs) * 1000
    energy = np.sum(win**2)
    sym_score = max(0, 100 - (abs(1.0 - sym) * 40))
    rise_score = max(0, 100 - (rise_ms * 100)) 
    return sym, rise_ms, round((sym_score * 0.5) + (rise_score * 0.5), 1), energy

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio-mono-best-channel", required=True)
    parser.add_argument("--audio-stereo-clean", required=True)
    parser.add_argument("--v0", type=float, required=True)
    parser.add_argument("--mit", type=float, default=0.060, help="(Minimum Inter-arrival Time): Enforces a \"dead time\" after a detected peak. If a second peak occurs within this window, it is treated as part of the same ballistic event")
    parser.add_argument("--aed", type=float, default=0.25, help="(Automated Energy Decay): Calculates the energy ratio between the current peak and the preceding \"1-ORDER\" peak. If the energy drops significantly, it is flagged as a secondary arrival regardless of the TDOA")
    args = parser.parse_args()

    fs, d_m = wav.read(args.audio_mono_best_channel)
    fs_s, d_s = wav.read(args.audio_stereo_clean)
    
    mono = d_m.astype(np.float32) / (np.iinfo(d_m.dtype).max if d_m.dtype != np.float32 else 1.0)
    stereo = d_s.astype(np.float32) / (np.iinfo(d_s.dtype).max if d_s.dtype != np.float32 else 1.0)

    sw_band = apply_filter(mono, 4000, 16000, fs)
    sig_abs = np.abs(sw_band)
    
    # Thresholding
    win_size = int(0.02 * fs)
    steps = np.arange(0, len(sig_abs), win_size)
    mad = np.array([np.mean(sig_abs[i:i+win_size]) for i in steps])
    thresh = np.interp(np.arange(len(sig_abs)), steps, mad) * 6.5

    v0_idx = int(args.v0 * fs)
    all_peaks, _ = find_peaks(sig_abs, height=thresh, distance=int(0.005 * fs))
    valid_peaks = all_peaks[all_peaks >= v0_idx]

    st_ch0 = apply_filter(stereo[:, 0], 4000, 16000, fs)
    st_ch1 = apply_filter(stereo[:, 1], 4000, 16000, fs)
    
    classified_results = []
    last_primary_time, last_primary_energy = -1.0, -1.0

    for p in valid_peaks:
        t_curr = p / fs
        w_len, w_start = int(0.005 * fs), p - int(0.0005 * fs)
        sym, rise, conf, energy = analyze_shockwave_v9(sw_band[w_start : w_start + w_len], fs)
        if conf < 25.0: continue
        
        tdoa = calculate_tdoa(st_ch0[w_start:w_start+w_len], st_ch1[w_start:w_start+w_len], fs)
        
        is_refractory = (last_primary_time > 0 and (t_curr - last_primary_time) < args.mit)
        energy_ratio = energy / last_primary_energy if last_primary_energy > 0 else 1.0
        
        # We only allow label demotion, not promotion
        label = "1-ORDER"
        if is_refractory:
            label = "[REFLECTION/DECAY]"
        elif last_primary_energy > 0 and energy_ratio < args.aed:
            label = "[REFLECTION/DECAY]"
        else:
            last_primary_time, last_primary_energy = t_curr, energy

        classified_results.append({
            "Time_s": t_curr, "TDOA_ms": tdoa*1000, "Conf": conf, 
            "Type": label, "Energy_Ratio": round(energy_ratio, 3)
        })

    # --- CSV SAVE ---
    df_audio = pd.DataFrame(classified_results)
    df_audio.to_csv(f"4.identify-shockwaves-if-present.csv", index=False)
    # print(f"\nV1 Forensic Classification Complete.\n{df_audio}")
    print(f"\nV1 Forensic Classification (MIT={args.mit}s, AED={args.aed})")
    print(f"\n{df_audio}")

    # --- PLOT ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    time_ax = np.linspace(0, len(mono)/fs, len(mono))
    
    ax1.plot(time_ax, mono, color='grey', alpha=0.3, label='Raw Audio (Backdrop)')
    ax1.plot(time_ax, sw_band, color='#9400D3', linewidth=0.8, label='Shockwave Band (4-16kHz)')
    ax1.plot(time_ax, thresh, 'r--', alpha=0.5, label='Adaptive Threshold')
    
    f, t_spec, Sxx = spectrogram(sw_band, fs, nperseg=64, noverlap=48)
    ax2.pcolormesh(t_spec, f, 10 * np.log10(Sxx + 1e-11), shading='gouraud', cmap='magma')
    ax2.set_ylim(4000, 16000)

    for r in classified_results:
        color = '#00FF00' if r['Type'] == "1-ORDER" else '#FFFF00'
        for ax in [ax1, ax2]: ax.axvline(r['Time_s'], color=color, linestyle='--', alpha=0.8)
        ax1.text(r['Time_s'], 0.5, f"{r['Type']}\n{r['Conf']}%", color='black', 
                 fontweight='bold', rotation=90, bbox=dict(facecolor=color, alpha=0.5))

    ax1.legend(loc='upper right')
    plt.xlim(args.v0 - 0.05, args.v0 + 0.5)
    plt.xlabel("Time (s)")
    plt.tight_layout()
    plt.savefig(f"4.identify-shockwaves-if-present.png", dpi=300)

if __name__ == "__main__":
    main()
