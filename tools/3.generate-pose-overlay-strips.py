#!/usr/bin/env python3
"""
Generate pose overlay strips from pose_model.csv and existing event strips.
- Reads pose_model.csv (which can be manually corrected).
- For each event, creates three PNG images (baseline, onset, peak) with:
    - Transparent background
    - Pose wireframe overlay (MediaPipe connections)
- Also creates a combined horizontal strip with the overlays.
"""

import cv2
import pandas as pd
import numpy as np
import argparse
from pathlib import Path
import mediapipe as mp

# MediaPipe connections for the full skeleton
POSE_CONNECTIONS = frozenset([
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8), (9, 10),
    (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20), (11, 23),
    (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28), (27, 29),
    (28, 30), (29, 31), (30, 32), (27, 31), (28, 32)
])

def draw_pose_on_transparent(landmarks, width, height):
    """
    Create a transparent RGBA image with the pose wireframe.
    landmarks: dict mapping landmark_index -> (x_px, y_px)
    Returns: RGBA image (numpy array)
    """
    # Create transparent canvas
    img = np.zeros((height, width, 4), dtype=np.uint8)
    
    # Draw connections
    for a, b in POSE_CONNECTIONS:
        if a in landmarks and b in landmarks:
            pt_a = landmarks[a]
            pt_b = landmarks[b]
            cv2.line(img, pt_a, pt_b, (0, 255, 0, 255), 2)
    
    # Draw landmark points
    for pt in landmarks.values():
        cv2.circle(img, pt, 3, (0, 255, 0, 255), -1)
    
    return img

def overlay_pose_on_image(background_img, pose_img):
    """Overlay the transparent pose image onto the background image."""
    if background_img is None:
        return pose_img
    if background_img.shape[2] == 3:
        background_img = cv2.cvtColor(background_img, cv2.COLOR_BGR2BGRA)
    # Alpha blend
    alpha = pose_img[:, :, 3] / 255.0
    for c in range(3):
        background_img[:, :, c] = (1 - alpha) * background_img[:, :, c] + alpha * pose_img[:, :, c]
    return background_img

def main():
    parser = argparse.ArgumentParser(description="Generate pose overlay strips from pose_model.csv.")
    parser.add_argument("--pose-model", required=True,
                        help="CSV file with columns: event_id, frame, landmark_index, x_px, y_px")
    parser.add_argument("--strips-dir", required=True,
                        help="Directory containing event_*_strip.jpg images (from V3)")
    parser.add_argument("--output-dir", required=True,
                        help="Directory to save overlay PNGs and strips")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(exist_ok=True, parents=True)

    # Load pose model
    pose_df = pd.read_csv(args.pose_model)
    required_cols = ['event_id', 'frame', 'landmark_index', 'x_px', 'y_px']
    for col in required_cols:
        if col not in pose_df.columns:
            raise ValueError(f"pose_model.csv missing column: {col}")

    # Group by event_id and frame
    pose_data = {}
    for (event_id, frame), group in pose_df.groupby(['event_id', 'frame']):
        landmarks = {row['landmark_index']: (int(row['x_px']), int(row['y_px'])) for _, row in group.iterrows()}
        pose_data[(event_id, frame)] = landmarks

    # Process each event
    strip_dir = Path(args.strips_dir)
    strip_files = list(strip_dir.glob("event_*_strip.jpg"))
    if not strip_files:
        print(f"No event_*_strip.jpg files found in {strip_dir}")
        return

    for strip_path in strip_files:
        # Extract event_id from filename
        import re
        match = re.search(r'event_(\d+)_strip', strip_path.name)
        if not match:
            continue
        event_id = int(match.group(1))
        
        # Read the strip image (which contains baseline, onset, peak side by side)
        strip_img = cv2.imread(str(strip_path))
        if strip_img is None:
            print(f"Could not read {strip_path}")
            continue
        
        h, w = strip_img.shape[:2]
        frame_width = w // 3  # Each of the three frames is one-third of the strip
        
        # For each frame type, extract the region, overlay pose, and save
        overlay_imgs = []
        for i, frame_type in enumerate(['baseline', 'onset', 'peak']):
            # Extract the corresponding region from the strip
            x_start = i * frame_width
            x_end = (i + 1) * frame_width
            frame_region = strip_img[:, x_start:x_end]
            
            # Get landmarks for this event/frame
            landmarks = pose_data.get((event_id, frame_type), {})
            if landmarks:
                # Draw pose on transparent canvas (same size as frame_region)
                pose_canvas = draw_pose_on_transparent(landmarks, frame_width, h)
                # Overlay on the original frame region
                final_img = overlay_pose_on_image(frame_region.copy(), pose_canvas)
            else:
                final_img = frame_region.copy()
                cv2.putText(final_img, "NO POSE DATA", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Save individual overlay PNG (with alpha)
            out_path = out_dir / f"event_{event_id}_{frame_type}_overlay.png"
            cv2.imwrite(str(out_path), final_img)
            print(f"Saved {out_path}")
            overlay_imgs.append(final_img)
        
        # Create a combined strip with overlays
        if len(overlay_imgs) == 3:
            combined_strip = np.hstack(overlay_imgs)
            combined_path = out_dir / f"event_{event_id}_strip_overlay.png"
            cv2.imwrite(str(combined_path), combined_strip)
            print(f"Saved combined overlay strip: {combined_path}")

    print("Done.")

if __name__ == "__main__":
    main()