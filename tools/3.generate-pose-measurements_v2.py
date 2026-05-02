#!/usr/bin/env python3
"""
Forensic Pose Measurement Generator – Full Body + Direct Neck Width
- Uses mediapipe Holistic (Pose + Face Mesh) and Selfie Segmentation for accurate scaling.
- Saves transparent skeleton overlay, landmark CSV, and measurement CSV (cm).
"""

import argparse
import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
from pathlib import Path

# ----------------------------------------------------------------------
# MediaPipe connections (complete skeleton)
# ----------------------------------------------------------------------
POSE_CONNECTIONS = frozenset([
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8), (9, 10),
    (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20), (11, 23),
    (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28), (27, 29),
    (28, 30), (29, 31), (30, 32), (27, 31), (28, 32)
])

# Descriptive names for every connection (for output CSV)
CONNECTION_DESCRIPTIONS = {
    (15,21): "Left lateral body line (pinky to hip)",
    (16,20): "Right hand span (pinky to thumb)",
    (18,20): "Right index to thumb",
    (3,7): "Face width (ear to ear)",
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
    (23,24): "Knee width (inter‑knee distance)",
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
    (17,19): "Left thumb‑index span",
    (2,3): "Left eye to ear (temple)",
    (11,12): "Elbow width (inter‑elbow distance)",
    (27,29): "Left foot length (heel to foot index)",
    (13,15): "Left hand (wrist to pinky)",
}

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def get_full_body_segmentation(image):
    """Return binary mask (0/255) of the person using MediaPipe Selfie Segmentation."""
    mp_selfie = mp.solutions.selfie_segmentation
    with mp_selfie.SelfieSegmentation(model_selection=0) as segmenter:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = segmenter.process(rgb)
        mask = (results.segmentation_mask > 0.1).astype(np.uint8) * 255
        return mask

def get_holistic_landmarks(image):
    """Return pose landmarks (33) and face landmarks (468)."""
    mp_holistic = mp.solutions.holistic
    with mp_holistic.Holistic(static_image_mode=True, model_complexity=2) as holistic:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = holistic.process(rgb)
        if not results.pose_landmarks:
            raise RuntimeError("No pose landmarks detected.")
        h, w = image.shape[:2]
        pose_lms = [(int(lm.x * w), int(lm.y * h)) for lm in results.pose_landmarks.landmark]
        face_lms = []
        if results.face_landmarks:
            face_lms = [(int(lm.x * w), int(lm.y * h)) for lm in results.face_landmarks.landmark]
        return pose_lms, face_lms, w, h

def compute_cm_per_px_from_mask(mask, subject_height_cm):
    """
    Get topmost and bottommost mask pixel to compute pixel height,
    then cm_per_px = subject_height_cm / pixel_height.
    """
    rows = np.any(mask, axis=1)
    if not np.any(rows):
        raise RuntimeError("Segmentation mask empty – cannot compute height.")
    y_indices = np.where(rows)[0]
    top_px = y_indices[0]
    bottom_px = y_indices[-1]
    pixel_height = bottom_px - top_px
    if pixel_height <= 0:
        raise RuntimeError("Invalid height from segmentation mask.")
    return subject_height_cm / pixel_height, top_px, bottom_px

def draw_pose_overlay(landmarks, width, height):
    """Create transparent RGBA image with green pose skeleton."""
    overlay = np.zeros((height, width, 4), dtype=np.uint8)
    for a, b in POSE_CONNECTIONS:
        if a < len(landmarks) and b < len(landmarks):
            pt_a = landmarks[a]
            pt_b = landmarks[b]
            cv2.line(overlay, pt_a, pt_b, (0, 255, 0, 255), 2)
    for pt in landmarks:
        cv2.circle(overlay, pt, 4, (0, 255, 0, 255), -1)
    return overlay

def pixel_distance(pt1, pt2):
    return np.hypot(pt1[0] - pt2[0], pt1[1] - pt2[1])

def get_neck_width_from_facemesh(face_lms, cm_per_px):
    """
    Use Face Mesh lateral neck points (indices 130 and 243) to measure neck width.
    Returns value in cm, or None if not available.
    """
    # Indices for left and right neck (base of throat area)
    left_neck = 130   # left side of neck
    right_neck = 243  # right side of neck
    if left_neck < len(face_lms) and right_neck < len(face_lms):
        dist_px = pixel_distance(face_lms[left_neck], face_lms[right_neck])
        return dist_px * cm_per_px
    return None

# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Generate forensic pose measurements.")
    parser.add_argument("--front-facing-subject-standing-img", required=True,
                        help="Input image file")
    parser.add_argument("--subject-height-cm", type=float, required=True,
                        help="Actual subject height in cm")
    parser.add_argument("--gen-overlay", required=True,
                        help="Output PNG for transparent skeleton overlay")
    parser.add_argument("--gen-pose-model", required=True,
                        help="Output CSV for landmark pixel coordinates")
    parser.add_argument("--gen-pose-metrics", required=True,
                        help="Output CSV for body measurements (cm)")
    args = parser.parse_args()

    # Read image
    img = cv2.imread(args.front_facing_subject_standing_img)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {args.front_facing_subject_standing_img}")
    h_img, w_img = img.shape[:2]

    # 1. Get scaling factor using Selfie Segmentation (full body mask)
    print("Computing full body height via segmentation...")
    mask = get_full_body_segmentation(img)
    cm_per_px, top_y, bottom_y = compute_cm_per_px_from_mask(mask, args.subject_height_cm)
    print(f"Subject pixel height: {bottom_y - top_y} px, scale: {cm_per_px:.4f} cm/px")

    # 2. Get pose and face landmarks
    pose_lms, face_lms, width, height = get_holistic_landmarks(img)
    if len(pose_lms) < 33:
        print(f"Warning: Only {len(pose_lms)} pose landmarks detected (expected 33).")

    # 3. Save pose model CSV (landmark_index, x_px, y_px)
    pose_data = [{"landmark_index": i, "x_px": x, "y_px": y} for i, (x, y) in enumerate(pose_lms)]
    pd.DataFrame(pose_data).to_csv(args.gen_pose_model, index=False)
    print(f"Saved pose model to {args.gen_pose_model}")

    # 4. Generate transparent overlay
    overlay = draw_pose_overlay(pose_lms, width, height)
    cv2.imwrite(args.gen_overlay, overlay)
    print(f"Saved overlay to {args.gen_overlay}")

    # 5. Compute all measurements
    metrics = []

    def add_metric(name, value_cm):
        metrics.append({"measurement": name, "value_cm": round(value_cm, 2)})

    # 5a. Standard pose connections (with descriptive names)
    for a, b in POSE_CONNECTIONS:
        if a < len(pose_lms) and b < len(pose_lms):
            dist_px = pixel_distance(pose_lms[a], pose_lms[b])
            dist_cm = dist_px * cm_per_px
            key = tuple(sorted((a, b)))
            desc = CONNECTION_DESCRIPTIONS.get(key, f"connection_{a}_{b}")
            add_metric(desc, dist_cm)

    # 5b. Shoulder width (using pose indices 11 and 12)
    if 11 < len(pose_lms) and 12 < len(pose_lms):
        shoulder_cm = pixel_distance(pose_lms[11], pose_lms[12]) * cm_per_px
        add_metric("Shoulder width", shoulder_cm)

    # 5c. Face width (ear-to-ear, indices 3 and 7)
    if 3 < len(pose_lms) and 7 < len(pose_lms):
        face_cm = pixel_distance(pose_lms[3], pose_lms[7]) * cm_per_px
        add_metric("Face width (ear to ear)", face_cm)

    # 5d. Neck width – direct from face mesh if possible, else heuristic
    neck_cm = None
    if face_lms:
        neck_cm = get_neck_width_from_facemesh(face_lms, cm_per_px)
    if neck_cm is None:
        # fallback: 0.32 * shoulder width (anthropometric)
        if "Shoulder width" in [m["measurement"] for m in metrics]:
            shoulder_val = next(m["value_cm"] for m in metrics if m["measurement"] == "Shoulder width")
            neck_cm = shoulder_val * 0.32
            add_metric("Neck width (estimated from shoulder width)", neck_cm)
        else:
            print("Warning: Could not compute neck width (no shoulder width available).")
    else:
        add_metric("Neck width (direct from face mesh)", neck_cm)

    # Save metrics CSV
    pd.DataFrame(metrics).to_csv(args.gen_pose_metrics, index=False)
    print(f"Saved metrics to {args.gen_pose_metrics}")

    print("Done.")

if __name__ == "__main__":
    main()