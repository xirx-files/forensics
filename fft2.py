import numpy as np
from scipy.io import wavfile
import csv

# 1. Load your 1-second 44.1kHz audio
fs, data = wavfile.read('original_event_audio.wav')
if len(data.shape) > 1: 
    data = data[:, 0]  # Mono conversion

# 2. Configure for Audacity Alignment
window_size = 1024 
hop_size = window_size // 2  # 50% Overlap
hann_window = np.hanning(window_size) # Matches Audacity default

# Calculate total possible windows with overlap
num_windows = (len(data) - window_size) // hop_size + 1
output_file = 'forensic_event_analysis_aligned.csv'

with open(output_file, 'w', newline='') as f_out:
    writer = csv.writer(f_out)
    writer.writerow(['Index', 'Timestamp (s)', 'Peak Frequency (Hz)', 'Potential Event'])

    for i in range(num_windows):
        start = i * hop_size
        end = start + window_size
        segment = data[start:end]
        
        # Apply Hann window to match Audacity spectral weighting
        windowed_segment = segment * hann_window
        
        # Calculate Peak Frequency (Hz)
        fft_result = np.fft.rfft(windowed_segment)
        freqs = np.fft.rfftfreq(window_size, 1/fs)
        peak_hz = freqs[np.argmax(np.abs(fft_result))]
        
        # 3. Forensic Classification Logic (Unchanged)
        event_label = "Ambient/Speech"
        if peak_hz < 100:
            event_label = "FIREWORK/MORTAR (Sub-Bass Thump)"
        elif 100 <= peak_hz <= 400:
            event_label = "LARGE EXPLOSION (Low Frequency)"
        elif 500 <= peak_hz <= 1500:
            event_label = "GUNSHOT (9mm/Rifle Spectral Peak)"
        elif peak_hz > 4000:
            event_label = "SHARP CRACK/ASPIRATION (High Frequency)"
        
        # 4. Center the timestamp for visual alignment
        # (Start + Half-Window) / Sample Rate
        timestamp = (start + (window_size / 2)) / fs
        
        writer.writerow([i + 1, f"{timestamp:.4f}", f"{peak_hz:.2f}", event_label])

print(f"Classification complete. {num_windows} indices saved to {output_file}")
