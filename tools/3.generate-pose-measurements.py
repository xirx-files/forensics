#!/usr/bin/env python3
"""
Forensic Pose Measurement Generator
- Extracts MediaPipe pose landmarks (0-32) from a front-facing standing image.
- Computes scaling factor based on provided subject height (cm) and vertical span of landmarks.
- Generates a transparent overlay PNG with the pose skeleton.
- Saves a CSV with landmark pixel coordinates.
- Saves a CSV with body segment lengths (cm) including standard connections, shoulder width,
  face width (ear-to-ear), and neck width (estimated as half shoulder width).
"""

import argparse
import csv
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import pandas as pd

# MediaPipe pose connections (complete skeleton)
POSE_CONNECTIONS = frozenset([
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8), (9, 10),
    (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20), (11, 23),
    (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28), (27, 29),
    (28, 30), (29, 31), (30, 32), (27, 31), (28, 32)
])

CONNECTION_DESCRIPTIONS = {
    (15,21): "Left lateral body line (pinky to hip)",
    (16,20): "Right hand span (pinky to thumb)",
    (18,20): "Right index to thumb",
    (3,7): "Head width (ear to ear)",
    (14,16): "Right hand (wrist to pinky)",
    (23,25): "Left shin / calf",
    (28,30): "Right foot length (heel to foot index)",
    (11,23): "Left torso lateral line (elbow to knee)",
    (27,31): "Left foot length (heel to big toe)",
    (6,8): "Right cheek line (eye to mouth)",
    (15,17): "Left hand span (pinky to index)",
    (24,26): "Right shin / calf",
    (16,22): "Right lateral body line (pinky to hip)",
    (4,5): "Left mouth to right inner eye",
    (5,6): "Right eye width (inner to outer)",
    (29,31): "Left toe span (foot index to big toe)",
    (12,24): "Right torso lateral line (elbow to knee)",
    (23,24): "Knee width (inter-knee distance)",
    (0,1): "Nose to left inner eye",
    (9,10): "Shoulder width",
    (1,2): "Left eye width (inner to outer)",
    (0,4): "Nose to left mouth",
    (11,13): "Left forearm",
    (30,32): "Right toe span (foot index to big toe)",
    (28,32): "Right foot length (heel to big toe)",
    (15,19): "Left hand span (pinky to thumb)",
    (16,18): "Right hand span (pinky to index)",
    (25,27): "Left ankle to heel",
    (26,28): "Right ankle to heel",
    (12,14): "Right forearm",
    (17,19): "Left thumb-index span",
    (2,3): "Left eye to ear (temple)",
    (11,12): "Elbow width (inter-elbow distance)",
    (27,29): "Left foot length (heel to foot index)",
    (13,15): "Left hand (wrist to pinky)",
}

# Landmark indices for custom metrics
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_EAR = 3
RIGHT_EAR = 7
LEFT_EYE = 2
RIGHT_EYE = 5

def get_pose_landmarks(image):
    """Run MediaPipe Pose on an image, return landmark list and dimensions."""
    mp_pose = mp.solutions.pose
    with mp_pose.Pose(static_image_mode=True, model_complexity=2) as pose:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)
        if not results.pose_landmarks:
            raise RuntimeError("No pose landmarks detected in the image.")
        h, w = image.shape[:2]
        landmarks = []
        for lm in results.pose_landmarks.landmark:
            x_px = int(lm.x * w)
            y_px = int(lm.y * h)
            landmarks.append((x_px, y_px))
        return landmarks, w, h

def compute_cm_per_px(landmarks, subject_height_cm):
    """Compute cm per pixel using the vertical span of all pose landmarks."""
    y_coords = [pt[1] for pt in landmarks]
    y_min = min(y_coords)
    y_max = max(y_coords)
    pixel_height = y_max - y_min
    if pixel_height <= 0:
        raise ValueError("Invalid landmark vertical span (zero or negative).")
    cm_per_px = subject_height_cm / pixel_height
    return cm_per_px

def draw_pose_overlay(landmarks, width, height):
    """Create transparent RGBA image with pose skeleton."""
    overlay = np.zeros((height, width, 4), dtype=np.uint8)
    # Draw connections
    for a, b in POSE_CONNECTIONS:
        if a < len(landmarks) and b < len(landmarks):
            pt_a = landmarks[a]
            pt_b = landmarks[b]
            # Skip if either point is missing (e.g., (-1,-1) but not used here)
            cv2.line(overlay, pt_a, pt_b, (0, 255, 0, 255), 2)
    # Draw landmark points
    for pt in landmarks:
        cv2.circle(overlay, pt, 4, (0, 255, 0, 255), -1)
    return overlay

def pixel_distance(pt1, pt2):
    """Euclidean distance in pixels between two points."""
    return np.hypot(pt1[0] - pt2[0], pt1[1] - pt2[1])

def main():
    parser = argparse.ArgumentParser(description="Generate pose measurements from a single front-facing image.")
    parser.add_argument("--front-facing-subject-standing-img", required=True,
                        help="Input image file (e.g., test.jpg)")
    parser.add_argument("--subject-height-cm", type=float, required=True,
                        help="Actual subject height in centimeters")
    parser.add_argument("--gen-overlay", required=True,
                        help="Output PNG file for the pose skeleton overlay")
    parser.add_argument("--gen-pose-model", required=True,
                        help="Output CSV for landmark pixel coordinates")
    parser.add_argument("--gen-pose-metrics", required=True,
                        help="Output CSV for body measurements (cm)")
    args = parser.parse_args()

    # 1. Load image and extract landmarks
    img = cv2.imread(args.front_facing_subject_standing_img)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {args.front_facing_subject_standing_img}")
    landmarks, width, height = get_pose_landmarks(img)
    if len(landmarks) < 33:
        print(f"Warning: Only {len(landmarks)} landmarks detected (expected 33). Some measurements may be missing.")

    # 2. Compute scaling factor
    cm_per_px = compute_cm_per_px(landmarks, args.subject_height_cm)
    print(f"Scaling: {cm_per_px:.4f} cm/pixel")

    # 3. Save pose model CSV (landmark_index, x_px, y_px)
    pose_data = []
    for idx, (xp, yp) in enumerate(landmarks):
        pose_data.append({"landmark_index": idx, "x_px": xp, "y_px": yp})
    pose_df = pd.DataFrame(pose_data)
    pose_df.to_csv(args.gen_pose_model, index=False)
    print(f"Saved pose model to {args.gen_pose_model}")

    # 4. Generate overlay image (transparent background + green skeleton)
    overlay = draw_pose_overlay(landmarks, width, height)
    cv2.imwrite(args.gen_overlay, overlay)
    print(f"Saved overlay to {args.gen_overlay}")

    # 5. Compute all connection lengths (in cm)
    metrics = []
    # Useful helper
    def add_metric(name, value_cm):
        metrics.append({"measurement": name, "value_cm": round(value_cm, 2)})

    # Standard connections from MediaPipe
    for a, b in POSE_CONNECTIONS:
        if a < len(landmarks) and b < len(landmarks):
            dist_px = pixel_distance(landmarks[a], landmarks[b])
            dist_cm = dist_px * cm_per_px
            conn_key = tuple(sorted((a, b)))
            description = CONNECTION_DESCRIPTIONS.get(conn_key, f"connection_{a}_{b}")
            add_metric(f"{description}[{a}-{b}]", dist_cm)

    # Shoulder-to-shoulder width (left 11 -> right 12)
    if LEFT_SHOULDER < len(landmarks) and RIGHT_SHOULDER < len(landmarks):
        sh_dist_px = pixel_distance(landmarks[LEFT_SHOULDER], landmarks[RIGHT_SHOULDER])
        sh_dist_cm = sh_dist_px * cm_per_px
        add_metric("shoulder_width", sh_dist_cm)

    # Face width: prefer ear-to-ear (3–7), fallback to eye distance (2–5)
    if LEFT_EAR < len(landmarks) and RIGHT_EAR < len(landmarks):
        face_px = pixel_distance(landmarks[LEFT_EAR], landmarks[RIGHT_EAR])
        face_cm = face_px * cm_per_px
        add_metric("face_width", face_cm)
    elif LEFT_EYE < len(landmarks) and RIGHT_EYE < len(landmarks):
        face_px = pixel_distance(landmarks[LEFT_EYE], landmarks[RIGHT_EYE])
        face_cm = face_px * cm_per_px
        add_metric("face_width", face_cm)
        print("Warning: Ear landmarks missing; face width approximated as interpupillary distance.")
    else:
        print("Warning: Cannot compute face width (missing ear/eye landmarks).")

    # Neck width: heuristic (half of shoulder width)
    if "shoulder_width" in [m["measurement"] for m in metrics]:
        shoulder_val = next(m["value_cm"] for m in metrics if m["measurement"] == "shoulder_width")
        neck_cm = shoulder_val * 0.5
        add_metric("neck_width", neck_cm)
    else:
        print("Warning: Cannot compute neck width (shoulder width missing).")

    # Save metrics CSV
    metrics_df = pd.DataFrame(metrics)
    metrics_df.to_csv(args.gen_pose_metrics, index=False)
    print(f"Saved metrics to {args.gen_pose_metrics}")

    print("Done.")

if __name__ == "__main__":
    main()