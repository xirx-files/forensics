import numpy as np
import scipy.io.wavfile as wav
from scipy.signal import butter, sosfiltfilt
import csv
import argparse

def apply_bandpass(data, low, high, fs, order=4):
    """4th order Butterworth bandpass (zero-phase) as per source [3, 4]."""
    sos = butter(order, [low, high], fs=fs, btype='band', output='sos')
    return sosfiltfilt(sos, data)

def get_rms(signal, frame_len, hop):
    """Short-time RMS calculation as per source [2, 4]."""
    return np.array([np.sqrt(np.mean(signal[i:i+frame_len]**2)) 
                     for i in range(0, len(signal) - frame_len, hop)])

def detect_onset(rms_values, fs, hop, threshold_mult=6, baseline_end_sec=0.02):
    """Onset detection logic: baseline_mean + N * baseline_std [2, 5]."""
    baseline_frames = int((baseline_end_sec * fs) / hop)
    baseline = rms_values[:baseline_frames]
    threshold = np.mean(baseline) + (threshold_mult * np.std(baseline))
    
    for i, val in enumerate(rms_values):
        if val > threshold:
            return i * (hop / fs)
    return None

def main():
    parser = argparse.ArgumentParser(description="Segment Audio into Key Events Sequence")
    parser.add_argument("--audio", type=str, default='mono_event_audio.wav', help="Path to input audio (mono, 48kHz/44.1kHz, PCM float)")
    parser.add_argument("-btt", "--bangTimeThresholdMult", type=float, default=6, help="Onset detection threshold multiplier for bang detection (Default: 6)")
    parser.add_argument("-vtt", "--violenceTimeThresholdMult", type=float, default=10, help="Onset detection threshold multiplier for violence detection (Default: 10)")
    args = parser.parse_args()

    input_file = args.audio # 'mono_event_audio.wav'
    output_file = '2.segment-audio-into-key-events-sequence.csv'
    
    # 1. Load Audio (Locked Spec: Mono, 48kHz/44.1kHz, PCM float) [6, 7]
    fs, data = wav.read(input_file)
    if data.dtype != np.float32:
        data = data.astype(np.float32) / np.iinfo(data.dtype).max
    
    duration = len(data) / fs

    # 2. Forensic Band Analysis
    # Bang Detection: 50-300 Hz (Low-frequency pressure arrival) [2]
    bang_data = apply_bandpass(data, 50, 300, fs)
    bang_rms = get_rms(bang_data, 256, 64)
    bang_time = detect_onset(bang_rms, fs, 64, threshold_mult=args.bangTimeThresholdMult)
    
    # Sibilance Detection: 3000-7000 Hz ("ess" phonetics in "violence") [1, 8]
    sib_data = apply_bandpass(data, 3000, 7000, fs)
    sib_rms = get_rms(sib_data, 128, 32)
    # Finding the 'violence' peak (assuming it occurs before the bang)
    violence_time = detect_onset(sib_rms, fs, 32, threshold_mult=args.violenceTimeThresholdMult)

    # 3. Define Intervals (Logical placeholders for sequencing) [1]
    # Based on Source [1], sequence is: Violence -> Silence_1 -> Great -> Silence_2 -> Bang
    events = []
    
    # violence (Sibilance peak to end of speech)
    events.append(["violence", violence_time, violence_time + 0.6])
    
    # silence_1 (Interval between public figure and questioner)
    events.append(["silence_1", violence_time + 0.61, violence_time + 1.0])
    
    # great (Questioner response)
    events.append(["great", violence_time + 1.01, bang_time - 0.5])
    
    # silence_2 (Interval before the bang)
    events.append(["silence_2", bang_time - 0.49, bang_time - 0.01])
    
    # bang segment (Locked Spec window: 0-220ms relative to onset) [3]
    events.append(["bang", bang_time, bang_time + 0.22])

    # 4. Noise Reduction Preference Logic
    # Compare RMS of silence_1 vs silence_2 to find the cleaner sample [1]
    def get_segment_rms(start, end):
        seg = data[int(start*fs):int(end*fs)]
        return np.sqrt(np.mean(seg**2)) if len(seg) > 0 else float('inf')

    rms_s1 = get_segment_rms(events[1][1], events[1][2])
    rms_s2 = get_segment_rms(events[3][1], events[3][2])
    preferred_nr = "silence_1" if rms_s1 < rms_s2 else "silence_2"

    # 5. Export to CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Event Name", "Start Interval (s)", "End Interval (s)", "Preferred NR Sample"])
        for e in events:
            is_preferred = "YES" if e == preferred_nr else "NO"
            writer.writerow([e[0], f"{e[1]:.6f}", f"{e[2]:.6f}", is_preferred])

    print(f"Segmentation complete. Preferred NR: {preferred_nr}. Output: {output_file}")

if __name__ == "__main__":
    main()