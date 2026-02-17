import numpy as np
import scipy.io.wavfile as wav
import csv
import os

def assert_authenticity(file_path):
    results = []
    
    # Load the audio file
    try:
        sample_rate, data = wav.read(file_path)
    except Exception as e:
        return [["File Load", f"Error: {str(e)}"]]

    # Ensure data is floating point for analysis
    if data.dtype != np.float32:
        data = data.astype(np.float32) / np.iinfo(data.dtype).max

    # 1. Sample Rate Verification
    # Sources indicate 44.1kHz or 48kHz are expected for these phone recordings [6, 7].
    results.append(["Sample Rate Check", f"{sample_rate}Hz", "PASS" if sample_rate in (44100, 48000) else "FAIL"])

    # 2. Clipping Detection
    # MEMS microphones in phones often clip at ~120dB [2, 8].
    # This test detects if the signal reaches the digital ceiling (0 dBFS), which destroys waveform detail [9, 10].
    clipping_threshold = 0.99
    clipped_samples = np.sum(np.abs(data) >= clipping_threshold)
    clipping_percent = (clipped_samples / len(data)) * 100
    results.append(["Clipping Analysis", f"{clipping_percent:.4f}% clipped", "WARNING" if clipping_percent > 0.1 else "PASS"])

    # 3. DC Offset Test
    # Significant DC offset can indicate hardware malfunction or poor digital editing/splicing.
    dc_offset = np.mean(data)
    results.append(["DC Offset", f"{dc_offset:.6f}", "PASS" if abs(dc_offset) < 0.01 else "FAIL"])

    # 4. Silence/Dropout Detection
    # Detects absolute digital silence which may indicate "cuts" or obfuscation [11].
    # In a live amphitheatre with 3000 people, true digital silence is forensicly suspicious [6, 12].
    silence_threshold = 1e-5
    silent_frames = np.sum(np.abs(data) < silence_threshold)
    silence_percent = (silent_frames / len(data)) * 100
    results.append(["Digital Silence Check", f"{silence_percent:.2f}% silent", "FAIL" if silence_percent > 5.0 else "PASS"])

    # 5. Peak-to-RMS Ratio (AGC Indicator)
    # AGC destroys amplitude relationships between impulses and reflections [3].
    # A very low ratio in a high-SPL event (like a bang) suggests aggressive compression [3, 8].
    peak = np.max(np.abs(data))
    rms = np.sqrt(np.mean(data**2))
    crest_factor = peak / rms if rms > 0 else 0
    results.append(["Crest Factor (AGC Test)", f"{crest_factor:.2f}", "PASS" if crest_factor > 3.0 else "SUSPECT AGC"])

    return results

def main():
    input_file = "original_event_audio.wav"
    output_file = "1.assert-audio-authenticity.csv"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    test_results = assert_authenticity(input_file)

    with open(output_file, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Test Name", "Measured Value", "Result Status"])
        writer.writerows(test_results)

    print(f"Authenticity suite complete. Results exported to {output_file}")

if __name__ == "__main__":
    main()