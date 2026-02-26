import argparse
import numpy as np
import scipy.io.wavfile as wav
from scipy.signal import butter, sosfiltfilt, find_peaks, correlate
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

def analyze_shockwave_v7(win, fs):
    """Restored: Field-tolerant N-wave analysis."""
    if len(win) < 10: return 0.0, 0.0, 0.0
    p_max = np.max(win)
    p_min = np.abs(np.min(win))
    sym = p_max / (p_min + 1e-9)
    
    pk_idx = np.argmax(np.abs(win))
    rise_ms = (pk_idx / fs) * 1000
    
    # Confidence tuned for amphitheatre acoustics (Softened rise penalty)
    sym_score = max(0, 100 - (abs(1.0 - sym) * 40))
    # 0.5ms rise now yields ~50 points instead of 0
    rise_score = max(0, 100 - (rise_ms * 100)) 
    confidence = (sym_score * 0.5) + (rise_score * 0.5)
    
    return sym, rise_ms, round(confidence, 1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("--v0", type=float, required=True)
    args = parser.parse_args()

    fs, data = wav.read(args.audio)
    data = data.astype(np.float32) / (np.iinfo(data.dtype).max if data.dtype != np.float32 else 1.0)
    
    raw_ch0 = data[:, 0]
    sw_band = apply_filter(raw_ch0, 4000, 16000, fs)
    ch1_f = apply_filter(data[:, 1], 4000, 16000, fs)

    search_start = int(args.v0 * fs)
    sig_seg = np.abs(sw_band[search_start:])
    
    # Adaptive Threshold
    win_size = int(0.02 * fs)
    steps = np.arange(0, len(sig_seg), win_size)
    local_mad = np.array([np.mean(sig_seg[i:i+win_size]) for i in steps])
    thresh_curve = np.interp(np.arange(len(sig_seg)), steps, local_mad) * 7.5 # Adjusted to 7.5x MAD

    peaks, _ = find_peaks(sig_seg, height=thresh_curve, distance=int(0.015 * fs))
    
    results = []
    for p in peaks:
        idx = search_start + p
        w_len = int(0.005 * fs)
        w_start = idx - int(0.0005 * fs)
        ch0_w = sw_band[w_start : w_start + w_len]
        ch1_w = ch1_f[w_start : w_start + w_len]

        if len(ch0_w) < w_len: continue
        sym, rise, conf = analyze_shockwave_v7(ch0_w, fs)
        
        # Lowered threshold to 30% for field-recorded data
        if conf > 30.0: 
            tdoa = calculate_tdoa(ch0_w, ch1_w, fs)
            results.append({"Time_s": idx/fs, "TDOA_ms": tdoa*1000, "Rise": rise, "Sym": sym, "Conf": conf})

    # --- RESTORED DIAGNOSTICS & RAW WAVEFORM PLOTTING ---
    plt.figure(figsize=(15, 7))
    time_ax = np.linspace(0, len(raw_ch0)/fs, len(raw_ch0))
    
    plt.plot(time_ax, raw_ch0, color='#D3D3D3', label='Raw Audio (Grey)', alpha=0.5)
    plt.plot(time_ax, sw_band, color='#9400D3', label='Shockwave Band (Violet)', linewidth=0.7)
    
    # Plot the Adaptive Threshold on the diagnostic view
    diag_time = np.linspace(args.v0, args.v0 + len(sig_seg)/fs, len(sig_seg))
    plt.plot(diag_time, thresh_curve, color='red', linestyle='--', alpha=0.5, label='Adaptive Threshold')
    
    for r in results:
        plt.axvline(r['Time_s'], color='#00FF00', linestyle='--', linewidth=1.5)
        plt.text(r['Time_s'], 0.7, f"Conf: {r['Conf']}%", color='green', rotation=90, fontweight='bold')

    plt.xlim(args.v0 - 0.05, args.v0 + (len(sig_seg)/fs) + 0.1)
    plt.title(f"V7 Shockwave Forensic ID | Confidence Score & Diagnostic Plot")
    plt.xlabel("Seconds"); plt.ylabel("Amplitude"); plt.legend(loc='upper right'); plt.grid(True, alpha=0.1)
    plt.savefig(f"4a.diagnostics-{os.path.basename(args.audio)}.png", dpi=300)
    
    df = pd.DataFrame(results)
    df.to_csv(f"4a.identify-shockwaves-{os.path.basename(args.audio)}.csv", index=False)
    print(f"V7 complete. Found {len(df)} shockwaves.")
    if not df.empty: print(df)

if __name__ == "__main__":
    main()
