
import librosa
import numpy as np
import os
import csv
import warnings

def find_bang_onset(file_path):
    """
    Analyzes an audio file to find the precise onset of the main 'bang' event
    using a spectral flux-based onset detection algorithm.

    Args:
        file_path (str): Path to the audio file.

    Returns:
        float: The start time of the bang in seconds, or None if an error occurs.
    """
    try:
        # Suppress the UserWarning from librosa about audioread not being found
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            y, sr = librosa.load(file_path, sr=None)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

    # We expect the bang in the second half of the 2-second clip.
    # This helps avoid confusion with the "great" or "violence" events.
    start_sample = int(0.7 * sr) 
    y_focus = y[start_sample:]

    # Calculate a standard onset strength envelope
    onset_env = librosa.onset.onset_strength(y=y_focus, sr=sr)
    
    # Find the single most prominent onset in the envelope.
    # We use librosa's onset_detect which is great for percussive events.
    # We set wait=1 and pre/post_avg/max to find sharp, isolated peaks.
    # The `wait` parameter in samples ensures we only get one peak after the first.
    onsets = librosa.onset.onset_detect(
        onset_envelope=onset_env,
        sr=sr,
        units='samples',
        pre_max=10,
        post_max=10,
        pre_avg=10,
        post_avg=10,
        wait=10, # wait for 10 frames
        normalize=True
    )

    if len(onsets) == 0:
        # If no prominent onset is found, fall back to the max energy point as a guess
        peak_sample = np.argmax(onset_env)
        bang_sample_in_focus = peak_sample
        print(f"Warning: No distinct onset found for {os.path.basename(file_path)}. Falling back to max energy.")
    else:
        # The first and most prominent onset is our bang
        bang_sample_in_focus = onsets[0]

    # Convert the sample index back to the original audio clip's timeframe
    bang_sample_absolute = bang_sample_in_focus + start_sample
    bang_time_s = bang_sample_absolute / sr

    return bang_time_s


def main():
    """
    Processes all 'original_event_audio.wav' files, detects bang onsets,
    and saves the results to a CSV file.
    """
    video_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and (d.startswith('video-') or d.startswith('others'))]
    all_dirs = ['.']
    for d in video_dirs:
        if d == 'others':
            all_dirs.extend([os.path.join('others', od) for od in os.listdir('others') if os.path.isdir(os.path.join('others', od))])
        else:
            all_dirs.append(d)

    output_file = 'bang_onset_analysis.csv'
    
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['video_source', 'bang_start_time_s', 'error']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        print(f"Running improved onset detection...")
        for directory in sorted(all_dirs):
            audio_file = os.path.join(directory, 'original_event_audio.wav')
            
            if os.path.exists(audio_file):
                bang_start_time = find_bang_onset(audio_file)
                if bang_start_time is not None:
                    writer.writerow({'video_source': directory, 'bang_start_time_s': bang_start_time, 'error': None})
                else:
                    writer.writerow({'video_source': directory, 'error': 'Analysis failed'})
            elif 'video-' in directory:
                writer.writerow({'video_source': directory, 'error': 'original_event_audio.wav not found'})

    print(f"Analysis complete. New onset times saved to '{output_file}'")

if __name__ == "__main__":
    main()
