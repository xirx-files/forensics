#!/usr/bin/env python3
"""
Forensic Pose Measurement Generator – Accurate scaling using FaceMesh + Pose.
- Uses MediaPipe Holistic (Pose 0‑32 + FaceMesh 468).
- cm/px from (top of face mesh) to (lowest foot/ankle from pose).
- Outputs: transparent overlay, pose_model.csv, metrics.csv (all lengths in cm).
"""

import argparse
import cv2
import mediapipe as mp
import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# MediaPipe pose connections (full skeleton, indices 0‑32)
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

def get_holistic_data(image):
    """Return pose landmarks (33), face landmarks (468), image dimensions."""
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

def compute_cm_per_px(pose_lms, face_lms, subject_height_cm):
    """
    Use top of face mesh (minimum y) and bottom of pose (maximum y among feet/ankles).
    Returns cm_per_px and the pixel height used.
    """
    if face_lms:
        top_y = min(pt[1] for pt in face_lms)          # top of forehead/scalp
    else:
        # fallback: use nose (index 0) minus 10% of face width estimate
        nose_y = pose_lms[0][1] if len(pose_lms) > 0 else None
        if nose_y is None:
            raise RuntimeError("No face mesh and no nose landmark for height estimate.")
        # crude head height estimate (head ~ 1/8 of total height)
        top_y = nose_y - (subject_height_cm / 8) / (subject_height_cm / (max(pt[1] for pt in pose_lms) - nose_y))
        # simpler: just use nose as top (less accurate)
        # top_y = nose_y

    # bottom: max y among pose feet/ankle indices 27‑32
    foot_indices = [27, 28, 29, 30, 31, 32]
    foot_y = [pose_lms[i][1] for i in foot_indices if i < len(pose_lms)]
    bottom_y = max(foot_y) if foot_y else max(pt[1] for pt in pose_lms)

    pixel_height = bottom_y - top_y
    if pixel_height <= 0:
        raise ValueError(f"Invalid pixel height: {pixel_height} (top={top_y}, bottom={bottom_y})")
    cm_per_px = subject_height_cm / pixel_height
    return cm_per_px, pixel_height

def draw_pose_overlay(landmarks, width, height):
    """Transparent RGBA image with green skeleton."""
    overlay = np.zeros((height, width, 4), dtype=np.uint8)
    for a, b in POSE_CONNECTIONS:
        if a < len(landmarks) and b < len(landmarks):
            cv2.line(overlay, landmarks[a], landmarks[b], (0, 255, 0, 255), 2)
    for pt in landmarks:
        cv2.circle(overlay, pt, 4, (0, 255, 0, 255), -1)
    return overlay

def pixel_distance(pt1, pt2):
    return np.hypot(pt1[0] - pt2[0], pt1[1] - pt2[1])

def get_neck_width(face_lms, cm_per_px):
    """Use face mesh indices 130 (left neck) and 243 (right neck)."""
    left = 130
    right = 243
    if left < len(face_lms) and right < len(face_lms):
        dist_px = pixel_distance(face_lms[left], face_lms[right])
        return dist_px * cm_per_px
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--front-facing-subject-standing-img", required=True)
    parser.add_argument("--subject-height-cm", type=float, required=True)
    parser.add_argument("--gen-overlay", required=True)
    parser.add_argument("--gen-pose-model", required=True)
    parser.add_argument("--gen-pose-metrics", required=True)
    args = parser.parse_args()

    # Load image
    img = cv2.imread(args.front_facing_subject_standing_img)
    if img is None:
        raise FileNotFoundError(f"Cannot read: {args.front_facing_subject_standing_img}")

    # Get landmarks
    pose_lms, face_lms, w, h = get_holistic_data(img)
    print(f"Detected {len(pose_lms)} pose landmarks, {len(face_lms)} face landmarks.")

    # Compute scaling
    cm_per_px, px_height = compute_cm_per_px(pose_lms, face_lms, args.subject_height_cm)
    print(f"Pixel height (top-of-head to feet): {px_height} px")
    print(f"Scaling: {cm_per_px:.4f} cm/px")

    # 1. Save pose model CSV
    pose_df = pd.DataFrame([(i, x, y) for i, (x, y) in enumerate(pose_lms)],
                           columns=["landmark_index", "x_px", "y_px"])
    pose_df.to_csv(args.gen_pose_model, index=False)
    print(f"Saved {args.gen_pose_model}")

    # 2. Save overlay PNG
    overlay = draw_pose_overlay(pose_lms, w, h)
    cv2.imwrite(args.gen_overlay, overlay)
    print(f"Saved {args.gen_overlay}")

    # 3. Build metrics
    metrics = []

    def add_metric(name, value_cm):
        metrics.append({"measurement": name, "value_cm": round(value_cm, 2)})

    # 3a. All MediaPipe connections (raw index pairs)
    for a, b in POSE_CONNECTIONS:
        if a < len(pose_lms) and b < len(pose_lms):
            dist_cm = pixel_distance(pose_lms[a], pose_lms[b]) * cm_per_px
            key = tuple(sorted((a, b)))
            desc = CONNECTION_DESCRIPTIONS.get(key, f"connection_{a}_{b}")
            add_metric(f"{desc}[{a}-{b}]", dist_cm)

    # 3b. Shoulder width (11 = left shoulder, 12 = right shoulder)
    if 11 < len(pose_lms) and 12 < len(pose_lms):
        shoulder_cm = pixel_distance(pose_lms[11], pose_lms[12]) * cm_per_px
        add_metric("shoulder_width (11-12)", shoulder_cm)

    # 3c. Face width (3 = left ear, 7 = right ear)
    if 3 < len(pose_lms) and 7 < len(pose_lms):
        face_cm = pixel_distance(pose_lms[3], pose_lms[7]) * cm_per_px
        add_metric("face_width_ear_to_ear (3-7)", face_cm)

    # 3d. Neck width (from face mesh)
    if face_lms:
        neck_cm = get_neck_width(face_lms, cm_per_px)
        if neck_cm:
            add_metric("neck_width_facemesh_130_243", neck_cm)
        else:
            # fallback heuristic
            if "shoulder_width (11-12)" in [m["measurement"] for m in metrics]:
                shoulder_val = next(m["value_cm"] for m in metrics if m["measurement"] == "shoulder_width (11-12)")
                add_metric("neck_width_estimated (0.32*shoulder)", shoulder_val * 0.32)
    else:
        print("Warning: No face mesh – neck width not measured.")

    # Save metrics CSV
    pd.DataFrame(metrics).to_csv(args.gen_pose_metrics, index=False)
    print(f"Saved {args.gen_pose_metrics}")
    print("Done.")

if __name__ == "__main__":
    main()