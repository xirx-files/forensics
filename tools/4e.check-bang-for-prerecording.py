import numpy as np
import scipy.io.wavfile as wav
from scipy.signal import butter, sosfiltfilt
import csv
import argparse

def apply_filter(data, low, high, fs):
    """4th order Butterworth zero-phase bandpass as per Locked Spec."""
    sos = butter(4, [low, high], fs=fs, btype='band', output='sos')
    return sosfiltfilt(sos, data)

def get_rms(signal, frame_len, hop):
    """Short-time RMS calculation as per Locked Spec."""
    return np.array([np.sqrt(np.mean(signal[i:i+frame_len]**2)) 
                     for i in range(0, len(signal) - frame_len, hop)])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("-ct", "--crack_time", type=float, required=True, help="Detected Crack Timestamp")
    parser.add_argument("-bt", "--bang_time", type=float, required=True, help="Detected Bang Timestamp")
    args = parser.parse_args()

    fs, data = wav.read(args.audio)
    if data.dtype != np.float32:
        data = data.astype(np.float32) / np.iinfo(data.dtype).max
    
    results = []

    # 1. FREQUENCY CEILING TEST (PA Hardware Limitation)
    # Most PA systems roll off significantly above 10–15 kHz [3].
    # Real shockwaves have significant energy up to 17 kHz [4, 5].
    hf_band = apply_filter(data, 12000, 17000, fs)
    mid_band = apply_filter(data, 3000, 7000, fs)
    
    energy_hf = np.sum(hf_band**2)
    energy_mid = np.sum(mid_band**2)
    hf_ratio = (energy_hf / (energy_mid + 1e-9)) * 100
    
    # If ratio is extremely low (<1%), it suggests PA roll-off or playback.
    results.append(["HF Roll-off (>12kHz)", f"{hf_ratio:.2f}%", "CONSISTENT WITH PA" if hf_ratio < 2 else "CONSISTENT WITH LIVE SHOT"])

    # 2. CRACK-BANG SEPARATION (Delta Calculation)
    # In a playback, the Delta is FIXED in the recording [2].
    # In a real shot, Delta varies by microphone position [6, 7].
    delta_ms = (args.bang_time - args.crack_time) * 1000
    results.append(["Crack-Bang Delta", f"{delta_ms:.2f} ms", "REPORTED FOR COMPARISON"])

    # 3. TRANSIENT SHARPNESS (Rise Time Check)
    # PA systems cannot reproduce the sub-millisecond transient of a true N-wave [3].
    crack_segment = data[int(args.crack_time*fs):int((args.crack_time+0.005)*fs)]
    peak_idx = np.argmax(np.abs(crack_segment))
    # Calculate samples to reach 90% of peak from 10%
    threshold_low = 0.1 * np.max(np.abs(crack_segment))
    threshold_high = 0.9 * np.max(np.abs(crack_segment))
    
    try:
        start_idx = np.where(np.abs(crack_segment) >= threshold_low)
        end_idx = np.where(np.abs(crack_segment) >= threshold_high)
        rise_time_us = ((end_idx - start_idx) / fs) * 1000000
        results.append(["Transient Rise Time", f"{rise_time_us:.1f} us", "SMEARED (PA-LIKE)" if rise_time_us > 100 else "SHARP (BALLISTIC)"])
    except:
        results.append(["Transient Rise Time", "N/A", "FAIL"])

    # 4. TDOA CONVERGENCE LOGIC (Metadata Result)
    # Playback converges on ONE point (speaker); Live shot converges on TWO (muzzle + trajectory) [3].
    results.append(["TDOA Convergence", "Requires Multilateration", "PENDING CROSS-FILE ANALYSIS"])

    # CONCLUSION LOGIC
    # Playback is suspected if HF is cut off and transients are smeared.
    is_playback = hf_ratio < 2 and rise_time_us > 100
    if is_playback:
        conclusion = "Acoustic Signature Consistent with PA Playback"
        confidence = "Medium (Requires Delta comparison across files)"
    elif hf_ratio > 5:
        conclusion = "PA Playback Disproven (High-Frequency Content Exceeds PA Limits)"
        confidence = "High (Hardware Physics)"
    else:
        conclusion = "Ambiguous Signature"
        confidence = "Low"

    # Export to CSV
    output_file = '4e.check-bang-for-prerecording.csv'
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Test Suite", "Measured/Value", "Status"])
        writer.writerows(results)
        writer.writerow([])
        writer.writerow(["CONCLUSION", conclusion])
        writer.writerow(["CONFIDENCE", confidence])

    print(f"Analysis complete: {conclusion} ({confidence} confidence).")

if __name__ == "__main__":
    main()