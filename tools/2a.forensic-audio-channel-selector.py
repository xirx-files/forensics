# https://share.google/aimode/6whj3HlLmzDP9kS11
import re
import argparse
import subprocess
import csv
import os
import sys

def parse_astats(filepath):
    """Parses ffmpeg astats for forensic metrics and phase correlation."""
    with open(filepath, 'r') as f:
        text = f.read()

    data = {'channels': {}}
    curr = None
    metrics = {"Peak level dB": "peak", "RMS level dB": "rms", 
               "Noise floor dB": "noise", "Dynamic range": "dyn", "DC offset": "dc"}

    for line in text.splitlines():
        # Global Phase Correlation
        if "Multi-Channel Correlation" in line:
            data['correlation'] = float(line.split(":")[-1].strip())
            
        m = re.search(r"Channel: (\d+)", line)
        if m:
            curr = m.group(1)
            data['channels'][curr] = {}
            continue
        if curr and ":" in line:
            for label, key in metrics.items():
                if label in line:
                    data['channels'][curr][key] = float(line.split(":")[-1].strip())
    return data

def determine_winner(c1, c2):
    reasons = []
    p1, p2 = 0, 0
    # Logic: Higher points = better forensic candidate
    if abs(c1['dc']) < abs(c2['dc']): p1 += 1; reasons.append("C1 lower DC Offset")
    else: p2 += 1; reasons.append("C2 lower DC Offset")
    
    if c1['dyn'] > c2['dyn']: p1 += 2; reasons.append("C1 better Dynamic Range")
    else: p2 += 2; reasons.append("C2 better Dynamic Range")
    
    if c1['noise'] < c2['noise']: p1 += 1; reasons.append("C1 lower Noise Floor")
    else: p2 += 1; reasons.append("C2 lower Noise Floor")

    return ("1" if p1 >= p2 else "2"), "; ".join(reasons)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--astat", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--force-mono-merge", action="store_true")
    args = parser.parse_args()

    data = parse_astats(args.astat)
    corr = data.get('correlation', 0.0)
    c1, c2 = data['channels']["1"], data['channels']["2"]
    
    winner, logic = determine_winner(c1, c2)
    is_safe = corr >= 0.0

    print(f"\n--- FORENSIC AUDIT: {os.path.basename(args.input)} ---")
    print(f"Phase Correlation: {corr:.4f} ({'SAFE' if is_safe else 'DANGER - OUT OF PHASE'})")
    
    # Selection Logic
    if args.force_mono_merge and is_safe:
        mode = "MONO MERGE (FL+FR)"
        filter_str = "pan=mono|c0=c0+c1"
        print(f"ACTION: Applying Lossless Mono Merge (FL+FR) as requested and safe.")
    else:
        mode = f"SINGLE CHANNEL ({winner})"
        filter_str = f"pan=mono|c0=c{int(winner)-1}"
        if args.force_mono_merge:
            print("WARNING: --force-mono-merge ignored. Negative correlation detected; merge would destroy data.")
        print(f"ACTION: Extracting Channel {winner} (Logic: {logic})")

    # FFmpeg Execution
    cmd = ["ffmpeg", "-y", "-i", args.input, "-af", filter_str, "-c:a", "pcm_s16le", args.output]
    subprocess.run(cmd, capture_output=True, check=True)

    # CSV Logging
    with open("2a.forensic-audio-channel-selector.csv", 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([args.input, mode, corr, logic])

if __name__ == "__main__":
    main()
