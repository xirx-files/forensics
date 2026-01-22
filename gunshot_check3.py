import librosa
import numpy as np
import sys
import os

def analyze_shot_v3(file_path):
    try:
        # Load 0.5s of the audio at its native sample rate
        y, sr = librosa.load(file_path, sr=None, duration=0.5)
    except Exception as e:
        return f"Error loading file: {e}"
    
    # Check sample rate compatibility
    if sr < 44100:
        return "Error: Sample rate too low for effective forensic analysis."

    # 1. PEAK SHAPE (Temporal Analysis - Calibrated for SR limit)
    peak_idx = np.argmax(np.abs(y))
    # Define a small window around the peak
    window_ms = 2.0 # Check a 2ms window
    start_idx = max(0, peak_idx - int(window_ms * sr / 1000))
    rise_segment = np.abs(y[start_idx:peak_idx+1])
    
    # Calculate rise time (10% to 90% peak amplitude)
    peak_val = np.max(rise_segment)
    low_thresh, high_thresh = 0.1 * peak_val, 0.9 * peak_val
    
    # This calculation is tricky with consumer mics, let's use the actual sample duration
    # Time per sample is 1/sr (e.g., 1/44100 = 0.0227 ms)
    # A "perfect" 44.1k shot would jump instantly in 1 sample, but mics smear it over several.
    
    # Find indices where thresholds are crossed
    idx_low = np.where(rise_segment >= low_thresh)[0]
    idx_high = np.where(rise_segment >= high_thresh)[0]

    if idx_low.size > 0 and idx_high.size > 0:
        # Calculate sample difference between the *first* high threshold hit and the *last* low threshold hit before it
        # This is a more robust way to measure the "effective" rise time given SR limitations
        t_low_sample = idx_low[0]
        t_high_sample = idx_high[0]
        
        # If low index is after the high index, something is wrong with selection, default to a high number
        if t_low_sample > t_high_sample:
             rise_time_ms = 999.0
        else:
             rise_time_ms = (t_high_sample - t_low_sample) / sr * 1000.0
    else:
        rise_time_ms = 999.0 # Default if we can't find clear thresholds


    # 2. SPECTRAL BRICK-WALL (Frequency Analysis - Normalized for 44.1k limit)
    stft = np.abs(librosa.stft(y, n_fft=2048))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    avg_spectrum = np.mean(stft, axis=1)
    
    # Look for "Air" near the absolute Nyquist limit of 22050 Hz
    # We define a band from 18 kHz to 22.05 kHz
    high_freq_band_energy = np.sum(avg_spectrum[(freqs >= 18000) & (freqs <= 22050)])
    mid_freq_band_energy = np.sum(avg_spectrum[(freqs >= 1000) & (freqs < 18000)])

    # Ratio of high band to mid band energy. A real gun should have a full spectrum (high ratio).
    hf_ratio = high_freq_band_energy / mid_freq_band_energy if mid_freq_band_energy > 0 else 0

    # 3. DYNAMIC RANGE (Crest Factor - Normalized for typical recording levels)
    # A close mic recording might be compressed by the mic itself, reducing the crest factor
    rms = librosa.feature.rms(y=y)
    mean_rms = np.mean(rms)
    crest_factor = peak_val / mean_rms if mean_rms > 0 else 0

    # SCORING ENGINE (Revised Weighting)
    score = 0
    logs = []

    # Evidence 1: Rise Time
    # If the rise time is faster than a speaker (e.g., <2.5ms), it's likely real/physical
    if rise_time_ms < 2.5: 
        score += 50
        logs.append(f"[Score +50%] Sharp Rise: {rise_time_ms:.3f}ms. Within physical limits of blast propagation.")
    else:
        logs.append(f"[Score +0%] Slow Rise: {rise_time_ms:.3f}ms. Suspiciously slow, suggests speaker inertia or distance.")

    # Evidence 2: High Frequency Ratio (We expect high HF energy from a real blast)
    if hf_ratio > 0.05: # This threshold is lower than previous attempts, allowing for mic limitations
        score += 30
        logs.append(f"[Score +30%] Spectral Spread: High energy ratio ({hf_ratio:.2f}) near 22.05kHz limit.")
    else:
        logs.append(f"[Score +0%] Top-End Cutoff: Low energy ratio ({hf_ratio:.2f}). Indicates potential digital filtering or PA limits.")

    # Evidence 3: Crest Factor (Impulsivity)
    if crest_factor > 8: # Lowering the threshold because close-mic recordings often compress internally
        score += 20
        logs.append(f"[Score +20%] High Crest: {crest_factor:.1f}. Event is highly impulsive/dynamic.")
    else:
        logs.append(f"[Score +0%] Low Crest: {crest_factor:.1f}. Suggests heavy audio compression/limiting.")

    # If the score is 100, we force a confident message
    if score >= 90:
        confidence = "HIGH CONFIDENCE REAL EVENT"
    elif score >= 50:
         confidence = "AMBIGUOUS - MIXED EVIDENCE"
    else:
        confidence = "LOW CONFIDENCE REAL EVENT (Likely Fabricated/PA)"
        
    return score, logs, confidence

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python shot_check_v3.py <audio.wav>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    score, logs, confidence = analyze_shot_v3(file_path)
    
    print(f"\n--- Forensic Analysis for: {os.path.basename(file_path)} ---")
    print(f"Overall Confidence: **{confidence}**")
    print(f"Probability of REAL gunshot: {score}%")
    print("\nDetailed Evidence Log:")
    for l in logs: print(l)

