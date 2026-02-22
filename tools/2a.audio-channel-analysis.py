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
