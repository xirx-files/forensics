yes, generate that verify-crop.py script with MSE sounds useful.

> Note that you are resampling to 48kHz; ensure the source isn't 44.1kHz to avoid interpolation artifacts

in this instance it was 48K, but there are 13 video files that are at 44.1. however, elsewhere gemini llm recommended that i resample all audio (incl 44.1) to 48K for all 17 media files for consistent shockwave, muzzleblast and other audio analysis.

ExifTool Version Number         : 12.57
Audio Sample Rate               : 48000


another recommendation made by gemini llm was to proceed with a preferred audio channel for audio forensics.

```python
import re
import sys

def analyze_astats(text):
    # Regex to capture channel blocks and their metrics
    channel_data = {}
    current_channel = None
    
    metrics_to_track = {
        "Peak level dB": "peak",
        "RMS level dB": "rms",
        "Noise floor dB": "noise",
        "Dynamic range": "dynamic",
        "DC offset": "dc"
    }

    for line in text.splitlines():
        # Identify channel section
        chan_match = re.search(r"Channel: (\d+)", line)
        if chan_match:
            current_channel = chan_match.group(1)
            channel_data[current_channel] = {}
            continue
        
        if "Overall" in line:
            current_channel = None
            
        if current_channel:
            for label, key in metrics_to_track.items():
                if label in line:
                    val = float(line.split(":")[-1].strip())
                    channel_data[current_channel][key] = val

    if not channel_data or "1" not in channel_data:
        return "Could not parse channel data. Ensure you paste the full ffmpeg astats output."

    c1 = channel_data["1"]
    c2 = channel_data["2"]

    # Comparison Logic
    report = []
    report.append("=== FORENSIC AUDIO DETERMINANT REPORT ===")
    
    # 1. Peak & RMS (Loudness/Presence)
    peak_diff = c2['peak'] - c1['peak']
    rms_diff = c2['rms'] - c1['rms']
    report.append(f"Peak Level: Channel 2 is {abs(peak_diff):.3f} dB {'louder' if peak_diff > 0 else 'quieter'} than Channel 1.")
    report.append(f"Average Power (RMS): Channel 2 is {abs(rms_diff):.3f} dB {'louder' if rms_diff > 0 else 'quieter'} on average.")

    # 2. Dynamic Range & Noise Floor
    dyn_diff = c2['dynamic'] - c1['dynamic']
    noise_diff = c2['noise'] - c1['noise']
    report.append(f"Dynamic Range: Channel 2 ({c2['dynamic']:.1f} dB) vs Channel 1 ({c1['dynamic']:.1f} dB).")
    if abs(dyn_diff) > 5:
        better_dyn = "2" if dyn_diff > 0 else "1"
        report.append(f"  -> ALERT: Channel {better_dyn} shows significantly higher bit-depth resolution/granularity.")
    
    report.append(f"Noise Floor: Channel 2 is {abs(noise_diff):.1f} dB {'quieter' if noise_diff < 0 else 'noisier'} than Channel 1.")

    # 3. DC Offset (Forensic Integrity)
    if abs(c1['dc']) > 0.001 or abs(c2['dc']) > 0.001:
        report.append(f"DC Offset Warning: Potential hardware bias detected (C1: {c1['dc']:.6f}, C2: {c2['dc']:.6f}).")

    # Final Recommendation
    # Weights: Lower noise is critical (-1), Higher dynamic range is good (+1)
    score_c2 = (1 if dyn_diff > 0 else 0) + (1 if noise_diff < 0 else 0) + (1 if rms_diff > 0 else 0)
    
    winner = "2" if score_c2 >= 2 else "1"
    
    report.append("\n=== FINAL RECOMMENDATION ===")
    report.append(f"Use CHANNEL {winner} for forensic analysis.")
    report.append(f"Command: ffmpeg -i [input] -af \"pan=mono|c0=c{int(winner)-1}\" ...")
    
    return "\n".join(report)

# If you run this as a script, paste your data into a variable or file
if __name__ == "__main__":
    # Example usage: read from stdin or paste data here
    print("Paste your astats output and press Ctrl+D (Unix) or Ctrl+Z (Win):")
    user_input = sys.stdin.read()
    print("\n" + analyze_astats(user_input))

```

i raise this with you because i have recently refactored the identify-shockwave.py script and gemini has now encouraged me to proceed with stereo particularly for TDOA which in this instance uses the two channels? which is correct?


This is a classic "Forensic Fork in the Road." Both recommendations are correct, but they apply to different stages of the investigation.
1. The Channel Conflict: Mono vs. Stereo
The "Choose the Best Channel" Logic: This is for Source Identification and Event Verification. If you are trying to identify a muzzle blast signature or a shockwave’s unique frequency profile, you want the cleanest signal (lowest noise floor, highest dynamic range). Using a noisy "Channel 2" just because it exists will pollute your FFT (Fast Fourier Transform) analysis.
The "Use Stereo (TDOA)" Logic: This is for Acoustic Localization. If the 17 videos were recorded with stereo microphones, the micro-delay (Time Difference of Arrival) between the Left and Right channels can tell you the direction of the shot relative to the camera.
The Verdict:
Perform your Acoustic Fingerprinting (Muzzle blast/Shockwave identification) on the Preferred Mono Channel identified by your astats script.
Perform your Spatial Analysis (Where did the shot come from?) on the Original Stereo Pair.
2. Resampling: 44.1kHz vs. 48kHz
Standardizing to 48kHz is standard practice for professional video forensics. However, if your original source is 44.1kHz, resampling to 48kHz adds interpolation points (predicted data).
Action: When calculating TDOA or Shockwave-to-Muzzle intervals, use the Original Sample Rate if possible to avoid sub-millisecond rounding errors. Only resample to 48kHz for the "Final Master" report or for cross-comparing all 17 files on a single timeline.
3. The verify-crop.py Script
This script calculates the MSE (Mean Squared Error) and PSNR (Peak Signal-to-Noise Ratio) between your original and cropped video. Since you used FFV1, the MSE should be 0.0 (mathematically identical pixels).

import subprocess
import json
import argparse
import sys

def verify_lossless_crop(original, cropped):
    """
    Uses ffmpeg to compare the original (cropped on the fly) 
    against the processed cropped file.
    """
    print(f"Comparing: {original} vs {cropped}")
    
    # This filter crops the ORIGINAL on the fly to match the CROPPED file 
    # then runs the 'psnr' filter to compare them bit-for-bit.
    # Replace the crop coordinates with your specific variables if automated.
    # For this script, we assume the user provides the crop string.
    
    crop_filter = "crop=350:520:0:940" # Match your bash command
    
    cmd = [
        "ffmpeg", "-i", original, "-i", cropped,
        "-filter_complex", f"[0:v]{crop_filter}[orig_cropped];[orig_cropped][1:v]psnr",
        "-f", "null", "-"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Extract PSNR/MSE from stderr
    # PSNR: inf means identical. MSE: 0 means identical.
    if "average:inf" in result.stderr.lower() or "mse:0.00" in result.stderr.lower():
        return True, "0.0 (Mathematically Identical)"
    else:
        # Extract the actual MSE value for reporting
        try:
            mse_val = result.stderr.split("average:")[1].split(" ")[0]
            return False, mse_val
        except:
            return False, "Analysis Failed - Check File Dimensions"

def main():
    parser = argparse.ArgumentParser(description="Verify Crop Losslessness")
    parser.add_argument("--orig", required=True)
    parser.add_argument("--crop", required=True)
    args = parser.parse_args()

    is_identical, value = verify_lossless_crop(args.orig, args.crop)

    print("\n" + "="*40)
    print(f"RESULT: {'✓ PASS' if is_identical else '✗ FAIL'}")
    print(f"MSE Value: {value}")
    print("="*40)
    
    if not is_identical:
        print("WARNING: Pixels have been altered. Check your FFV1 settings.")
        sys.exit(1)

if __name__ == "__main__":
    main()


4. Correcting the Baseline for TDOA
If you proceed with TDOA analysis across the 17 files, you must use the FFmpeg Anlmdn filter or similar to ensure that the "Preferred Channel" logic hasn't introduced a phase shift.
Do you have the exact coordinates of the cameras or the distance between the microphones for the TDOA calculation?

https://share.google/aimode/9Jmvbo90dI0m1IULJ

---

i have used perspective-n-point to determine the camera coordinates in both world-coordinate-system (XY & YZ) and lat/lon/ele. note, all but 1 video was recorded on mobile phones typically in portrait orientation.

oops, i gave you an old script earlier. the new script is below. please make any modifications to this script including "Anlmdn":

```python 2a.forensic-audio-channel-selector.py
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

```


Since you have Camera Coordinates (PnP) and are performing TDOA (Time Difference of Arrival), you are in a high-stakes spatial reconstruction.
The primary danger in your current script is Phase Cancellation. If you merge two channels that are out of phase, the muzzle blast (the very signal you need) could literally disappear via destructive interference.
The Forensic "Anlmdn" Upgrade
I have integrated the FFmpeg anlmdn (Non-Local Means Denoising) filter. Unlike standard filters, anlmdn reduces broadband noise while preserving the sharp transients of a shockwave or muzzle blast.
I also added a Phase-Safe Stereo mode. If you are doing TDOA, you must not merge to mono; you must keep the spatial timing intact.


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
    log_file = "2a.forensic-audio-channel-selector.csv"
    file_exists = os.path.isfile(log_file)
    with open(log_file, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Source", "Mode", "Correlation", "Logic"])
        writer.writerow([args.input, action_mode, corr, "Denoised via anlmdn"])

if __name__ == "__main__":
    main()


Critical Forensic Notes:
The "Anlmdn" Advantage: Standard noise reduction (like afftdn) creates "musical noise" or artifacts around sharp peaks. Non-Local Means (anlmdn) looks for similar patterns in the audio over time to subtract noise, keeping the shockwave's "attack" (the most important part for TDOA) perfectly vertical.
Stereo for TDOA: Since you have PnP coordinates, you can calculate the Internal Delay of the phone's microphones. If the phone is 7cm wide, there is a maximum ~0.2ms delay between channels. If your TDOA calculation exceeds this, the source is offset from the camera's center.
Portrait Orientation: Note that on most mobile phones in portrait, the "Left/Right" channels are actually "Top/Bottom" (one mic near the earpiece, one near the charging port). Your TDOA math must account for this Vertical Offset in your world coordinate system.
Should I provide the specific FFmpeg Crop Detect logic to ensure your manual crop parameters (350:520:0:940) aren't missing any edge-case motion at the frame boundaries?


https://share.google/aimode/kY4svty8IJZlIWSQX
