import argparse
import librosa
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import librosa.display
from scipy.signal import butter, sosfilt

def parse_range(range_str):
    return [float(x) for x in range_str.split('-')]

def get_onset(y, sr, time_range, freq_band):
    start_s, end_s = time_range
    # Slice the signal to the search segment
    start_idx, end_idx = int(start_s * sr), int(end_s * sr)
    y_seg = y[start_idx:end_idx]
    
    # Filter for the specific frequency band
    y_filt = librosa.effects.preemphasis(y_seg) # Enhances high freqs for sibilance
    S = np.abs(librosa.stft(y_filt))
    freqs = librosa.fft_frequencies(sr=sr)
    
    # Mask frequencies outside the band
    mask = (freqs >= freq_band[0]) & (freqs <= freq_band[1])
    S_band = S[mask, :]
    
    # Detect the peak onset in this band
    onset_env = librosa.onset.onset_strength(S=S_band, sr=sr)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
    
    if len(onset_frames) > 0:
        # Return first detected onset relative to the file start
        return start_s + librosa.frames_to_time(onset_frames[0], sr=sr)
    return None

def bandpass_filter_sos(data, lowcut, highcut, fs, order=4): # Lower order is safer
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    # Use output='sos' instead of 'ba'
    sos = butter(order, [low, high], btype='band', output='sos')
    return sosfilt(sos, data)

# Normalization helper to ensure all signals are visible on one axis
def norm_sig_safe(data):
    # Remove NaNs/Infs before plotting
    clean_data = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)
    max_val = np.max(np.abs(clean_data))
    return clean_data / (max_val + 1e-9) if max_val > 0 else clean_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True, help="Best mono WAV file")
    parser.add_argument("--violence-srch-seg", default="0-0.522")
    parser.add_argument("--bang-srch-seg", default="0.828-1.4")
    parser.add_argument("--shockwave-csv", help="CSV containing identified shockwaves eg. 4.identify-shockwaves-if-present-0.824.csv")

    args = parser.parse_args()

    # Load audio (mono for analysis)
    y, sr = librosa.load(args.audio, sr=None, mono=False)
    if y.ndim > 1:
        raise RuntimeError("Audio should be best mono for analysis. Please ensure the input file is mono and try again.")

    # Define frequency bands (Hz)
    violence_band = [3000, 7000]
    bang_band = [50, 300]
    
    # Detect Onsets
    violence_onset = get_onset(y, sr, parse_range(args.violence_srch_seg), violence_band)
    bang_srch_seg = parse_range(args.bang_srch_seg)
    bang_onset = get_onset(y, sr, bang_srch_seg, bang_band)
    if args.shockwave_csv:
        sw_df = pd.read_csv(args.shockwave_csv)
        order_1 = sw_df[sw_df['Type'] == '1-ORDER']
        if not order_1.empty:
            first_shockwave = order_1['Time_s'].min()
            while bang_onset and first_shockwave < bang_onset:
                # Shift search window to start after the shockwave
                bang_srch_seg = (first_shockwave, bang_srch_seg[1])
                bang_onset = get_onset(y, sr, bang_srch_seg, bang_band)
                if bang_onset:
                    # Check if the new onset is still before the next shockwave
                    next_shockwave = order_1[order_1['Time_s'] > first_shockwave]['Time_s'].min()
                    if next_shockwave and bang_onset < next_shockwave:
                        break  # Found a valid bang onset
                    else:
                        first_shockwave = next_shockwave  # Move to the next shockwave
                else:
                    break  # No more onsets found
    
    # 1. Save CSV
    df = pd.DataFrame([{
        'filename': args.audio,
        'violence_sibilance_timestamp': violence_onset,
        'bang_onset_timestamp': bang_onset,
        'lag_ms': (bang_onset - violence_onset) * 1000 if violence_onset and bang_onset else None
    }])
    df.to_csv('4.capture-key-sequence-onsets.csv', index=False)
    
    # Generate Plot

    # 1. Prepare Data
    time_ax = np.linspace(0, len(y) / sr, len(y))
    v_audio = bandpass_filter_sos(y, violence_band[0], violence_band[1], sr)
    b_audio = bandpass_filter_sos(y, bang_band[0], bang_band[1], sr)

    # 2. Setup Figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

    # 3. Top Pane: Normalized Waveform Backdrop
    time_ax = np.linspace(0, len(y) / sr, len(y))

    # Plotting everything normalized to [-1, 1] range
    ax1.plot(time_ax, norm_sig_safe(y), color='grey', alpha=0.3, label='Raw Audio (Backdrop)')
    ax1.plot(time_ax, norm_sig_safe(v_audio), color='cyan', linewidth=1.0, label='Violence Band (3-7kHz)')
    ax1.plot(time_ax, norm_sig_safe(b_audio), color='red', linewidth=1.0, label='Bang Band (50-300Hz)')

    # Force Y-axis to standard audio range to fix the 1e305 scale issue
    ax1.set_ylim(-1.1, 1.1)
    ax1.set_ylabel("Normalized Amplitude")

    # 4. Bottom Pane: Spectrogram
    D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
    librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='linear', ax=ax2, cmap='magma')
    ax2.set_ylim(0, 8000)

    # 5. Onset Markers & Text Labels
    onsets = [
        {'t': violence_onset, 'c': 'cyan', 'lbl': 'VIOLENCE'},
        {'t': bang_onset, 'c': 'red', 'lbl': 'BANG'}
    ]

    for o in onsets:
        if o['t']:
            for ax in [ax1, ax2]:
                ax.axvline(o['t'], color=o['c'], linestyle='--', alpha=0.8)
            # Place text label in top pane
            ax1.text(o['t'], 0.7, o['lbl'], color='black', fontweight='bold', 
                    rotation=90, bbox=dict(facecolor=o['c'], alpha=0.6))

    # 6. Final Polish
    ax1.legend(loc='upper right')
    plt.xlim(max(0, violence_onset - 0.1), bang_onset + 0.3)
    plt.tight_layout()
    plt.savefig('4.capture-key-sequence-onsets.png', dpi=300)

    print("Forensic markers captured successfully.")

if __name__ == "__main__":
    main()
