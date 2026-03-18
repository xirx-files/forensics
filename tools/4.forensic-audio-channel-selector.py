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
        if "Multi-Channel Correlation" in line:
            try:
                data['correlation'] = float(line.split(":")[-1].strip())
            except:
                data['correlation'] = 0.0
            
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--astat", required=True, help="Path to astats.txt output")
    parser.add_argument("--input", required=True, help="Input MKV/WAV")
    parser.add_argument("--output", required=True, help="Output processed file")
    parser.add_argument("--mode", choices=['best-mono', 'stereo-clean'], default='best-mono', 
                        help="best-mono for blast ID, stereo-clean for TDOA")
    args = parser.parse_args()

    data = parse_astats(args.astat)
    corr = data.get('correlation', 0.0)
    c1, c2 = data['channels'].get("1"), data['channels'].get("2")
    
    if not c1 or not c2:
        print("Error: Could not find two channels in astat data.")
        sys.exit(1)

    # Forensic Denoising Filter (Non-Local Means)
    # s=7: strength, p=0.002: patch size, r=0.006: research size
    # These settings are optimized to keep 'clicks' (blasts) sharp while removing hiss.
    denoise_filter = "anlmdn=s=7:p=0.002:r=0.006"

    print(f"\n--- FORENSIC AUDIT: {os.path.basename(args.input)} ---")
    print(f"Phase Correlation: {corr:.4f} ({'SAFE' if corr >= 0 else 'DANGER - OUT OF PHASE'})")

    if args.mode == 'stereo-clean':
        # PRESERVE BOTH FOR TDOA
        action_mode = "STEREO (Denoised)"
        filter_str = f"{denoise_filter}"
        print("ACTION: Preserving Stereo for TDOA analysis. Applying anlmdn.")
    else:
        # SELECT BEST CHANNEL FOR BLAST IDENTIFICATION
        winner = "1" if (c1['dyn'] - c1['noise']) > (c2['dyn'] - c2['noise']) else "2"
        action_mode = f"MONO (Ch {winner})"
        filter_str = f"pan=mono|c0=c{int(winner)-1},{denoise_filter}"
        print(f"ACTION: Extracting Channel {winner} for Signal ID. Applying anlmdn.")

    # FFmpeg Execution - Preserving PCM 16-bit Lossless
    cmd = ["ffmpeg", "-y", "-i", args.input, "-af", filter_str, "-c:a", "pcm_s16le", args.output]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        print(f"✓ Processed: {args.output}")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg Error: {e.stderr.decode()}")

    # Log to CSV
    log_file = "4.forensic-audio-channel-selector.csv"
    file_exists = os.path.isfile(log_file)
    with open(log_file, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Source", "Mode", "Correlation", "Logic"])
        writer.writerow([args.output, action_mode, corr, "Denoised via anlmdn"])

if __name__ == "__main__":
    main()
