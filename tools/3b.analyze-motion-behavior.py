import cv2
import numpy as np
import argparse
import csv
from scipy.ndimage import gaussian_filter

def analyze_impact_signature(flow, epicenter):
    """
    Analyzes the symmetry and distribution of motion vectors around the epicenter.
    """
    h, w = flow.shape[:2]
    ex, ey = map(int, epicenter)
    
    # Extract local neighborhood (e.g., 60x60 pixels)
    y_min, y_max = max(0, ey-30), min(h, ey+30)
    x_min, x_max = max(0, ex-30), min(w, ex+30)
    local_flow = flow[y_min:y_max, x_min:x_max]
    
    u = local_flow[..., 0]
    v = local_flow[..., 1]
    
    # 1. RADIAL DIVERGENCE (Explosion/Device Check)
    # Measures if vectors are pointing away from the center in all directions
    yy, xx = np.mgrid[y_min:y_max, x_min:x_max]
    dx = xx - ex
    dy = yy - ey
    
    # Normalized alignment: flow dot radius-vector
    alignment = (u * dx + v * dy) / (np.sqrt(u**2 + v**2) * np.sqrt(dx**2 + dy**2) + 1e-9)
    radial_score = np.mean(alignment) # > 0.5 suggests an outward burst
    
    # 2. VECTOR UNIDIRECTIONALITY (Projectile Check)
    # Measures if all vectors are moving in the same direction (transverse impulse)
    mean_u, mean_v = np.mean(u), np.mean(v)
    consistency = np.sqrt(mean_u**2 + mean_v**2) / (np.mean(np.sqrt(u**2 + v**2)) + 1e-9)
    
    return radial_score, consistency

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("-t0", type=float, required=True, help="Detected visual onset")
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.video)
    cap.set(cv2.CAP_PROP_POS_MSEC, args.t0 * 1000)
    
    ret, frame1 = cap.read()
    ret, frame2 = cap.read()
    if not ret: return

    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    
    # Compute flow at t0
    flow = cv2.calcOpticalFlowFarneback(gray1, gray2, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    
    # Using your existing epicenter logic
    du_dx = np.gradient(flow[..., 0], axis=1)
    dv_dy = np.gradient(flow[..., 1], axis=0)
    div = du_dx + dv_dy
    ke = 0.5 * (flow[..., 0]**2 + flow[..., 1]**2)
    metric = gaussian_filter(div, sigma=3) * np.sqrt(gaussian_filter(ke, sigma=3) + 1e-6)
    
    # Find Epicenter
    # idx = np.unravel_index(np.argmax(metric), metric.shape)
    # epicenter = (idx[1], idx)
    
    # radial, consistent = analyze_impact_signature(flow, epicenter)

    # Find Epicenter (row, col) from the metric map
    idx = np.unravel_index(np.argmax(metric), metric.shape)
    
    # Correctly assign (x, y) coordinates
    epicenter = idx # (idx[5], idx) 
    
    radial, consistent = analyze_impact_signature(flow, epicenter)

    # CLASSIFICATION LOGIC
    results = []
    # Project-context: "black shards flying out" and "necklace Swang around" [2]
    # Ballistic impact typically shows high consistency (linear impulse)
    if consistent > 0.7:
        conclusion = "Linear Kinetic Impulse (Consistent with Projectile)"
        theory = "Theories 1, 3, 4, 5"
    # Single-point detonation (Theory 7) shows high radial divergence [3, 4]
    elif radial > 0.4:
        conclusion = "Divergent Kinetic Burst (Consistent with On-Body Device)"
        theory = "Theory 7"
    # Logic for hand-localized motion (Theory 6)
    else:
        conclusion = "Localized Extremity Response"
        theory = "Theory 6 (Electrocution) or Reaction"

    print(f"Impact Signature: {conclusion}")
    print(f"Applicable Theories: {theory}")

if __name__ == "__main__":
    main()