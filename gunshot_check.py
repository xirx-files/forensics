import librosa
import numpy as np
import sys
import os

def analyze_shot(file_path):
    # Load 0.5s of the audio at its native sample rate
    try:
        y, sr = librosa.load(file_path, sr=None, duration=0.5)
    except Exception as e:
        return f"Error loading file: {e}"

    # 1. RISE TIME ANALYSIS (Peak Shape)
    # Real gunshots reach peak amplitude in < 0.5ms. Speakers are much slower.
    peak_idx = np.argmax(np.abs(y))
    # Look at the 5ms before the peak
    start_idx = max(0, peak_idx - int(0.005 * sr))
    rise_segment = np.abs(y[start_idx:peak_idx+1])
    
    # Calculate how many samples it takes to go from 10% to 90% peak amplitude
    peak_val = np.max(rise_segment)
    threshold_low = 0.1 * peak_val
    threshold_high = 0.9 * peak_val
    
    indices = np.where(rise_segment >= threshold_low)[0]
    if len(indices) > 0:
        low_idx = indices[0]
        high_idx = np.where(rise_segment >= threshold_high)[0][0]
        rise_time_ms = ((high_idx - low_idx) / sr) * 1000
    else:
        rise_time_ms = 999

    # 2. SPECTRAL CUTOFF (Frequency Range)
    # PA systems typically have a "brick wall" at 20kHz.
    # We check for energy above 20kHz if the sample rate allows.
    stft = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)
    avg_spectrum = np.mean(stft, axis=1)
    
    high_freq_energy = np.sum(avg_spectrum[freqs > 18000])
    total_energy = np.sum(avg_spectrum)
    hf_ratio = high_freq_energy / total_energy if total_energy > 0 else 0

    # 3. SPECTRAL CENTROID (Consistency/Brightness)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    mean_centroid = np.mean(centroid)

    # PROBABILITY SCORING
    score = 0
    reasons = []

    # Score Rise Time: Real gunshots are extremely fast (< 1.5ms for standard mics)
    if rise_time_ms < 1.5:
        score += 40
        reasons.append(f"Fast rise time ({rise_time_ms:.2f}ms) matches physical blast.")
    else:
        reasons.append(f"Slow rise time ({rise_time_ms:.2f}ms) suggests speaker inertia.")

    # Score High Frequencies: Real gunshots have ultrasonic content
    if hf_ratio > 0.02 and sr > 44100:
        score += 30
        reasons.append("Significant energy above 18kHz detected (Rare for PA systems).")
    else:
        reasons.append("Low high-frequency energy; consistent with speaker 'brick-wall' limits.")

    # Score Centroid: Gunshots are 'bright' (high centroid)
    if mean_centroid > 3000:
        score += 30
        reasons.append(f"High spectral brightness ({mean_centroid:.0f}Hz) typical of muzzle blast.")

    return score, reasons

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python shot_check.py <path_to_wav>")
        sys.exit(1)

    file_path = sys.argv[1]
    probability, findings = analyze_shot(file_path)
    
    print(f"\n--- Forensic Analysis for: {os.path.basename(file_path)} ---")
    print(f"Probability of REAL gunshot: {probability}%")
    print("\nEvidence Log:")
    for f in findings:
        print(f" - {f}")
