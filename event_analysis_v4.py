
import librosa
import numpy as np
import os
import csv

# --- Event Time Windows (from README.md) ---
# These windows help isolate the correct peak for each event.
EVENT_WINDOWS = {
    "violence": (0.0, 0.5),
    "great": (0.5, 0.8),
    "bang": (0.8, 1.2)
}

def find_event_boundaries(rms, times, window, noise_threshold):
    """
    Finds the start and end time of a single audio event within a given window.
    
    Args:
        rms (np.array): The RMS energy envelope of the audio.
        times (np.array): The timestamps corresponding to the RMS frames.
        window (tuple): The (start_time, end_time) window to search for the event.
        noise_threshold (float): The RMS level that defines silence.

    Returns:
        tuple: (start_time, end_time) of the event, or (None, None) if not found.
    """
    start_idx, end_idx = np.searchsorted(times, window)
    
    if start_idx == end_idx:
        return None, None # Window is empty

    event_segment = rms[start_idx:end_idx]
    
    # Find the peak of the event within the window
    peak_local_idx = np.argmax(event_segment)
    peak_global_idx = start_idx + peak_local_idx

    # Find the start of the event by searching backwards from the peak
    start_event_idx = peak_global_idx
    while start_event_idx > 0 and rms[start_event_idx] > noise_threshold:
        start_event_idx -= 1

    # Find the end of the event by searching forwards from the peak
    end_event_idx = peak_global_idx
    while end_event_idx < len(rms) - 1 and rms[end_event_idx] > noise_threshold:
        end_event_idx += 1
        
    return times[start_event_idx], times[end_event_idx]


def analyze_audio_gaps(file_path):
    """
    Analyzes an audio file to find the time gaps between the three key events.
    """
    try:
        y, sr = librosa.load(file_path, sr=None)
    except Exception as e:
        return {"error": f"Could not load file: {e}"}

    hop_length = 32  # Smaller hop for better time resolution
    rms = librosa.feature.rms(y=y, frame_length=256, hop_length=hop_length)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)

    # Define a noise threshold. We'll use a value slightly above the median RMS.
    # This is more robust than a fixed percentage of the max, which the bang would skew.
    noise_threshold = np.median(rms) * 1.5

    # Find boundaries for each event
    v_start, v_end = find_event_boundaries(rms, times, EVENT_WINDOWS["violence"], noise_threshold)
    g_start, g_end = find_event_boundaries(rms, times, EVENT_WINDOWS["great"], noise_threshold)
    b_start, b_end = find_event_boundaries(rms, times, EVENT_WINDOWS["bang"], noise_threshold)

    if not all([v_end, g_start, g_end, b_start]):
        return {"error": "Could not identify all event boundaries."}
        
    # Calculate the gaps based on the event boundaries
    gap_a = g_start - v_end
    gap_b = b_start - g_end

    return {
        "gap_a_ms": gap_a * 1000,
        "gap_b_ms": gap_b * 1000,
        "violence_end": v_end,
        "great_start": g_start,
        "great_end": g_end,
        "bang_start": b_start,
        "error": None
    }


def main():
    """
    Processes all 'original_event_audio.wav' files in the current directory
    and its subdirectories, saving the results to a CSV file.
    """
    video_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and (d.startswith('video-') or d.startswith('others'))]
    all_dirs = ['.'] # Include base directory
    for d in video_dirs:
        if d == 'others':
            all_dirs.extend([os.path.join('others', od) for od in os.listdir('others') if os.path.isdir(os.path.join('others', od))])
        else:
            all_dirs.append(d)

    output_file = 'event_gap_analysis.csv'
    
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['video_source', 'gap_a_ms', 'gap_b_ms', 'violence_end', 'great_start', 'great_end', 'bang_start', 'error']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for directory in sorted(all_dirs):
            audio_file = os.path.join(directory, 'original_event_audio.wav')
            
            if os.path.exists(audio_file):
                result = analyze_audio_gaps(audio_file)
                result['video_source'] = directory
                writer.writerow(result)
            elif 'video-' in directory: # Don't report missing for '.' or 'others'
                writer.writerow({'video_source': directory, 'error': 'original_event_audio.wav not found'})

    print(f"Analysis complete. Results saved to '{output_file}'")

if __name__ == "__main__":
    main()
