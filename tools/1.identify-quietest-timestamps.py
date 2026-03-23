# Python Script for Detecting Quietest Audio Moments
import subprocess
import sys
import argparse

def get_sample_rate(file_path):
    """Retrieves the sample rate of the first audio stream."""
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=sample_rate",
        "-of", "default=noprint_wrappers=1:nokey=1", file_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error reading file: {result.stderr}")
        sys.exit(1)
    return int(result.stdout.strip())

def find_quietest_moments(file_path, start_from, duration, top_n=5):
    # 1. Get sample rate and calculate 10ms window (1/100th of a second)
    sample_rate = get_sample_rate(file_path)
    window_samples = int(sample_rate / 100)
    
    print(f"File SR: {sample_rate}Hz | Window: {window_samples} samples (10ms)")
    print(f"Scanning from {start_from}s for {duration}s...\n")

    # 2. Build the ffprobe command
    # Uses Peak_level to find the lowest "loudest" point in each 10ms slice
    lavfi_query = (
        f"amovie='{file_path}',atrim=start={start_from}:duration={duration},"
        f"asetpts=PTS-STARTPTS,asetnsamples=n={window_samples},astats=metadata=1:reset=1"
    )
    
    cmd = [
        "ffprobe", "-v", "error", "-f", "lavfi", "-i", lavfi_query,
        "-show_entries", "frame=pts_time:frame_tags=lavfi.astats.Overall.Peak_level",
        "-of", "csv=p=0"
    ]

    # 3. Execute and parse results
    process = subprocess.run(cmd, capture_output=True, text=True)
    lines = process.stdout.strip().split('\n')
    
    results = []
    for line in lines:
        if ',' in line:
            rel_ts, peak = line.split(',')
            # Convert peak to float, handle '-inf'
            peak_val = float('-inf') if 'inf' in peak else float(peak)
            results.append((float(rel_ts) + start_from, peak_val))

    # 4. Sort by Peak Level (ascending: -inf or most negative first)
    results.sort(key=lambda x: x[1])

    # 5. Output Top N
    print(f"{'Rank':<5} | {'Absolute Timestamp':<20} | {'Peak Level (dB)':<15}")
    print("-" * 50)
    for i, (abs_ts, peak) in enumerate(results[:top_n], 1):
        peak_str = f"{peak:.2f}" if peak != float('-inf') else "-inf"
        print(f"{i:<5} | {abs_ts:<20.6f} | {peak_str:<15}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find the quietest 10ms windows in a video segment.")
    parser.add_argument("--input", help="Path to the video file")
    parser.add_argument("--start", type=float, default=0.64, help="Start timestamp (seconds)")
    parser.add_argument("--duration", type=float, default=0.2, help="Duration to scan (seconds)")
    
    args = parser.parse_args()
    find_quietest_moments(args.input, args.start, args.duration)
