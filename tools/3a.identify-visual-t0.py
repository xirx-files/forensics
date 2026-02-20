import cv2
import numpy as np
import argparse
import csv
from pathlib import Path
from scipy.ndimage import gaussian_filter

def calculate_motion_metric(prev_gray, gray):
    """Computes the forensic motion metric using Farneback Optical Flow."""
    flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    u, v = flow[..., 0], flow[..., 1]
    du_dx = np.gradient(u, axis=1)
    dv_dy = np.gradient(v, axis=0)
    
    # Feature extraction: Divergence weighted by Kinetic Energy
    divergence = du_dx + dv_dy
    kinetic_energy = 0.5 * (u**2 + v**2)
    metric = gaussian_filter(divergence, sigma=3) * \
             np.sqrt(gaussian_filter(kinetic_energy, sigma=3) + 1e-6)
    
    return np.percentile(np.abs(metric), 99)

def main():
    parser = argparse.ArgumentParser(description="Visual t0 Sync Check")
    parser.add_argument("--video", required=True)
    parser.add_argument("-st", "--start_time", type=float, required=True)
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Seek to start time
    cap.set(cv2.CAP_PROP_POS_MSEC, args.start_time * 1000)
    
    ret, prev_frame = cap.read()
    if not ret: return
        
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    frame_results = []
    
    # 1. GENERATE MOTION DATA
    print(f"Analyzing from {args.start_time}s at {fps} FPS...")
    current_frame_idx = int(args.start_time * fps)

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        current_frame_idx += 1
        timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        motion_val = calculate_motion_metric(prev_gray, gray)
        frame_results.append([current_frame_idx, timestamp, motion_val])
        prev_gray = gray

    # 2. CALCULATE 6-SIGMA THRESHOLD (Baseline: first 10 frames)
    motion_only = [row[2] for row in frame_results]
    baseline = motion_only[:10]
    b_mean = np.mean(baseline)
    b_std = np.std(baseline)
    threshold = b_mean + (6 * b_std)
    
    # 3. EXPORT SYNC CHECK CSV
    output_csv = "3a.visual-motion-analysis.csv"
    t0_timestamp = None
    
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["FrameIndex", "Timestamp", "MotionMetric", "Threshold", "Status"])
        
        for row in frame_results:
            idx, ts, val = row
            status = "STABLE"
            if val > threshold:
                status = "DEVIATION_DETECTED"
                if t0_timestamp is None:
                    t0_timestamp = ts
            
            writer.writerow([idx, f"{ts:.6f}", f"{val:.6f}", f"{threshold:.6f}", status])

    if t0_timestamp:
        print(f"\n[!] VISUAL t0 DETECTED: {t0_timestamp:.6f}s")
        print(f"Detailed sync-check saved to {output_csv}")
    else:
        print("\n[-] No motion deviation detected above noise floor.")

if __name__ == "__main__":
    main()