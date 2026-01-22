import librosa
import numpy as np
import sys

def analyze_shot_v2(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None, duration=0.5)
    except Exception as e:
        return f"Error: {e}"

    # --- 1. PEAK SHAPE (Temporal Analysis) ---
    peak_idx = np.argmax(np.abs(y))
    # Check 5ms window around peak
    start_idx = max(0, peak_idx - int(0.005 * sr))
    rise_segment = np.abs(y[start_idx:peak_idx+1])
    
    # Calculate rise time (10% to 90% peak)
    peak_val = np.max(rise_segment)
    low_thresh, high_thresh = 0.1 * peak_val, 0.9 * peak_val
    
    try:
        t_low = np.where(rise_segment >= low_thresh)[0][0]
        t_high = np.where(rise_segment >= high_thresh)[0][0]
        rise_time_ms = ((t_high - t_low) / sr) * 1000
    except IndexError:
        rise_time_ms = 999

    # --- 2. SPECTRAL BRICK-WALL (Frequency Analysis) ---
    stft = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)
    avg_spectrum = np.mean(stft, axis=1)
    
    # Look for "Air" (High Frequency Content) near the limit of 44.1k (approx 21k)
    upper_limit = (sr / 2) - 1000 
    hf_energy = np.sum(avg_spectrum[freqs > upper_limit])
    total_energy = np.sum(avg_spectrum)
    hf_ratio = hf_energy / total_energy if total_energy > 0 else 0

    # --- 3. DYNAMIC RANGE (Crest Factor) ---
    # Real shots have extreme peaks vs their average tail
    crest_factor = peak_val / np.sqrt(np.mean(y**2))

    # SCORING ENGINE
    score = 0
    logs = []

    # Evidence: Rise Time
    # Adjusted: 44.1k can't see faster than 1 sample (0.02ms), 
    # but a speaker driver usually takes >1.0ms to move.
    if rise_time_ms < 0.8:
        score += 45
        logs.append(f"[CONFIRMED] Sharp Rise: {rise_time_ms:.3f}ms. Too fast for most PA drivers.")
    elif rise_time_ms < 1.5:
        score += 20
        logs.append(f"[POSSIBLE] Moderate Rise: {rise_time_ms:.3f}ms. Ambiguous for 44.1k.")
    else:
        logs.append(f"[CRITICAL] Slow Rise: {rise_time_ms:.3f}ms. Highly indicative of speaker inertia.")

    # Evidence: Spectral Energy
    # Real gunshots have "white noise" qualities that fill the whole 44.1k bucket.
    if hf_ratio > 0.005:
        score += 30
        logs.append(f"[CONFIRMED] Spectral Spread: High energy up to {sr/2}Hz limit.")
    else:
        logs.append(f"[WARNING] Top-End Cutoff: Missing energy near {sr/2}Hz. Typical of digital filters.")

    # Evidence: Crest Factor (Punch)
    if crest_factor > 10:
        score += 25
        logs.append(f"[CONFIRMED] High Crest: {crest_factor:.1f}. Event is highly impulsive.")
    else:
        logs.append(f"[WARNING] Low Crest: {crest_factor:.1f}. Suggests audio compression/limiting.")

    return score, logs

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python shot_check_v2.py <audio.wav>")
        sys.exit(1)
    
    score, logs = analyze_shot_v2(sys.argv[1])
    print(f"\nFORENSIC REPORT: {score}% Probability of Real Gunshot")
    for l in logs: print(l)
