import cv2
import numpy as np
import argparse
import csv
from pathlib import Path
from scipy.ndimage import gaussian_filter

def calculate_motion_metric(prev_gray, gray):
    """Computes the forensic motion metric using Farneback Optical Flow."""
    # Farneback parameters as used in video-forensic-analysis.py
    flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    
    u, v = flow[..., 0], flow[..., 1]
    du_dx = np.gradient(u, axis=1)
    dv_dy = np.gradient(v, axis=0)
    
    # Feature extraction [1]
    divergence = du_dx + dv_dy
    kinetic_energy = 0.5 * (u**2 + v**2)
    
    # Metric logic [2]: Weighted Divergence * sqrt(Kinetic Energy)
    metric = gaussian_filter(divergence, sigma=3) * \
             np.sqrt(gaussian_filter(kinetic_energy, sigma=3) + 1e-6)
    
    # Return the 99th percentile as a robust 'peak motion' value for this frame
    return np.percentile(np.abs(metric), 99)

def main():
    parser = argparse.ArgumentParser(description="Automated Visual t0 Identification")
    parser.add_argument("--video", required=True, help="Path to focused_event_video.mp4 or forensic_sync_output.mp4")
    parser.add_argument("-st", "--start_time", type=float, required=True, 
                        help="Start time for analysis (e.g., silence_2 mark)")
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Seek to start time
    cap.set(cv2.CAP_PROP_POS_MSEC, args.start_time * 1000)
    
    ret, prev_frame = cap.read()
    if not ret:
        print("Error: Could not read video at start time.")
        return
        
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    frame_results = []
    
    print(f"Analyzing from {args.start_time}s...")

    # 1. GENERATE MOTION DATA
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        motion_val = calculate_motion_metric(prev_gray, gray)
        frame_results.append((timestamp, motion_val))
        prev_gray = gray

    # 2. ANALYZE DATA FOR t0 (Significant Deviation)
    # Baseline: First 10 frames of the search window (assumed pre-impact)
    # Extract only the MotionMetric values (index 1) for baseline analysis
    motion_values = [r[1] for r in frame_results]

    # Establish the baseline (noise floor) from the first 10 frames
    baseline = motion_values[:10]
    threshold = np.mean(baseline) + (6 * np.std(baseline))

    t0_timestamp = None
    for ts, val in frame_results:
        if val > threshold:
            t0_timestamp = ts
            break

    # 3. EXPORT RESULTS
    output_csv = "3a.visual-motion-analysis.csv"
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "MotionMetric", "Threshold"])
        for ts, val in frame_results:
            writer.writerow([f"{ts:.6f}", f"{val:.6f}", f"{threshold:.6f}"])

    if t0_timestamp:
        print(f"\n[!] VISUAL t0 DETECTED")
        print(f"Timestamp: {t0_timestamp:.6f} seconds")
        print(f"Results saved to {output_csv}")
    else:
        print("\n[-] No significant visual impact detected.")

if __name__ == "__main__":
    main()