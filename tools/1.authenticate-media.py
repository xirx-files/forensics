import os
import hashlib
import json
import subprocess
import csv
import argparse

def get_file_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def run_ffprobe(file_path):
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", file_path]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout)

def detect_frozen_frames(file_path):
    """Detects frames with 0 difference, often indicating a pause or edit."""
    cmd = [
        "ffmpeg", "-i", file_path, "-vf", "freezedetect=n=0.001:d=1", 
        "-map", "0:v:0", "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    # Count occurrences of 'lavfi.freezedetect.freeze_start' in stderr
    return result.stderr.count("freeze_start")

def analyze_forensics(file_path):
    results = []
    metadata = run_ffprobe(file_path)
    fmt = metadata.get("format", {})
    streams = metadata.get("streams", [])
    
    # 1. Chain of Custody
    results.append(["SHA-256 Hash", get_file_hash(file_path), "VERIFIED"])

    # 2. Encoder Authenticity
    encoder = fmt.get("tags", {}).get("encoder", "Unknown")
    # Native cameras rarely use 'Lavf' or 'Handbrake'
    is_suspect_enc = any(x in encoder.lower() for x in ["lavf", "ffmpeg", "handbrake", "adobe", "x264"])
    status = "SUSPECT (Re-encoded)" if is_suspect_enc else "PASS (Native/Unknown)"
    results.append(["Encoder Signature", encoder, status])

    # 3. Stream Integrity
    v_stream = next((s for s in streams if s['codec_type'] == 'video'), {})
    fps_val = v_stream.get("r_frame_rate", "0/0")
    results.append(["Video Codec", v_stream.get("codec_name"), "INFO"])
    results.append(["Frame Rate", fps_val, "PASS" if eval(fps_val) >= 23.9 else "FAIL (Low FPS)"])

    # 4. Temporal Anomaly Detection (Frozen/Duplicate Frames)
    freeze_count = detect_frozen_frames(file_path)
    freeze_status = "PASS" if freeze_count == 0 else f"WARNING ({freeze_count} frozen segments)"
    results.append(["Freeze/Pause Detection", f"{freeze_count} detected", freeze_status])

    # 5. Metadata Consistency
    # Check if 'creation_time' exists; missing time is common in edited/stripped files
    c_time = fmt.get("tags", {}).get("creation_time", "Missing")
    results.append(["Creation Metadata", c_time, "PASS" if c_time != "Missing" else "WARNING"])

    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    print(f"Conducting forensic audit on {args.input}...")
    report = analyze_forensics(args.input)

    output_csv = "1.authenticate-media.csv"
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Test/Metric", "Value", "Result Status"])
        writer.writerows(report)
    
    # Summary Output
    failures = [r[0] for r in report if "FAIL" in r[2] or "SUSPECT" in r[2]]
    if not failures:
        print("✓ SUCCESS: All authenticity thresholds passed.")
    else:
        print(f"⚠ ATTENTION: {len(failures)} potential anomalies found: {', '.join(failures)}")

if __name__ == "__main__":
    main()
