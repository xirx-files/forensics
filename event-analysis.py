import librosa
import numpy as np
import os

def analyze_audio_events(file_path):
    """
    Analyzes a 2-second audio file to find gaps between three distinct events.
    """
    # Load audio (sr=None preserves native sampling rate)
    try:
        y, sr = librosa.load(file_path, sr=None)
    except Exception as e:
        return f"Error loading {file_path}: {e}"

    # Use librosa to detect non-silent intervals (events)
    # top_db is the threshold; adjust based on crowd noise levels
    intervals = librosa.effects.split(y, top_db=25)

    # We expect 3 events: "violence", "great", and "bang"
    if len(intervals) < 3:
        return "Insufficient events detected"

    # Define events (Start and End in seconds)
    event1_end = intervals[0][1] / sr
    event2_start = intervals[1][0] / sr
    event2_end = intervals[1][1] / sr
    event3_start = intervals[2][0] / sr

    # Gap A: Between "violence" and "great"
    gap_a_start = event1_end
    gap_a_end = event2_start
    gap_a_dur = gap_a_end - gap_a_start

    # Gap B: Between "great" and "bang"
    gap_b_start = event2_end
    gap_b_end = event3_start
    gap_b_dur = gap_b_end - gap_b_start

    return {
        "A": (gap_a_start, gap_a_end, gap_a_dur),
        "B": (gap_b_start, gap_b_end, gap_b_dur)
    }

def main():
    filename = "original_event_audio.wav"
    
    # Header for Markdown Table
    print("| Gap Type | Start Position (s) | End Position (s) | Duration (s) |")
    print("| :--- | :--- | :--- | :--- |")

    # This example targets the local file; logic can be looped for all 17 directories
    results = analyze_audio_events(filename)

    if isinstance(results, dict):
        a = results["A"]
        b = results["B"]
        print(f"| White-Noise A | {a[0]:.6f} | {a[1]:.6f} | {a[2]:.6f} |")
        print(f"| White-Noise B | {b[0]:.6f} | {b[1]:.6f} | {b[2]:.6f} |")
    else:
        print(f"| Error | - | - | {results} |")

if __name__ == "__main__":
    main()
