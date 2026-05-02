#!/usr/bin/env python3
"""
Forensic Pose Measurement - Debug Version
Prints pixel and cm values for critical measurements.
"""

import argparse
import cv2
import mediapipe as mp
import numpy as np
import pandas as pd

mp_holistic = mp.solutions.holistic

POSE_CONNECTIONS = frozenset([
    (0,1),(1,2),(2,3),(3,7),(0,4),(4,5),(5,6),(6,8),(9,10),
    (11,12),(11,13),(13,15),(15,17),(15,19),(15,21),(17,19),
    (12,14),(14,16),(16,18),(16,20),(16,22),(18,20),(11,23),
    (12,24),(23,24),(23,25),(24,26),(25,27),(26,28),(27,29),
    (28,30),(29,31),(30,32),(27,31),(28,32)
])

def get_landmarks(image):
    with mp_holistic.Holistic(static_image_mode=True, model_complexity=2) as holistic:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = holistic.process(rgb)
        if not results.pose_landmarks:
            raise RuntimeError("No pose landmarks")
        h, w = image.shape[:2]
        pose = [(int(lm.x*w), int(lm.y*h)) for lm in results.pose_landmarks.landmark]
        face = []
        if results.face_landmarks:
            face = [(int(lm.x*w), int(lm.y*h)) for lm in results.face_landmarks.landmark]
        return pose, face, w, h

def compute_scaling(pose, subject_height_cm):
    """Estimate top-of-head using nose + anthropometric ratio."""
    # Nose is index 0
    nose_y = pose[0][1]
    # Heuristic: head height ~ 1/8 of total body height
    # Body height in pixels = (bottom_y - nose_y) * (8/7)? Actually simpler:
    # Use lowest foot/ankle (max y among indices 27-32)
    foot_y = max(pose[i][1] for i in [27,28,29,30,31,32] if i < len(pose))
    # Estimate top of head ~ nose_y - (foot_y - nose_y) * (1/7)   (since head ~1/8, torso+legs~7/8)
    est_top_y = nose_y - (foot_y - nose_y) / 7
    pixel_height = foot_y - est_top_y
    cm_per_px = subject_height_cm / pixel_height
    return cm_per_px, pixel_height, est_top_y, foot_y

def pixel_dist(a,b):
    return np.hypot(a[0]-b[0], a[1]-b[1])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--front-facing-subject-standing-img", required=True)
    parser.add_argument("--subject-height-cm", type=float, required=True)
    parser.add_argument("--gen-overlay", required=True)
    parser.add_argument("--gen-pose-model", required=True)
    parser.add_argument("--gen-pose-metrics", required=True)
    args = parser.parse_args()

    img = cv2.imread(args.front_facing_subject_standing_img)
    if img is None:
        raise FileNotFoundError(args.front_facing_subject_standing_img)

    pose, face, w, h = get_landmarks(img)
    print(f"Pose landmarks: {len(pose)}, Face landmarks: {len(face)}")

    # Scaling
    cm_px, px_h, top_y, bot_y = compute_scaling(pose, args.subject_height_cm)
    print(f"Estimated top-of-head y: {top_y:.1f} px")
    print(f"Lowest foot/ankle y: {bot_y:.1f} px")
    print(f"Pixel height: {px_h:.1f} px")
    print(f"Scale: {cm_px:.4f} cm/px\n")

    # Overlay
    overlay = np.zeros((h, w, 4), dtype=np.uint8)
    for a,b in POSE_CONNECTIONS:
        if a<len(pose) and b<len(pose):
            cv2.line(overlay, pose[a], pose[b], (0,255,0,255), 2)
    for pt in pose:
        cv2.circle(overlay, pt, 4, (0,255,0,255), -1)
    cv2.imwrite(args.gen_overlay, overlay)
    print(f"Saved overlay: {args.gen_overlay}")

    # Pose model CSV
    pose_df = pd.DataFrame([(i, x, y) for i,(x,y) in enumerate(pose)],
                           columns=["landmark_index","x_px","y_px"])
    pose_df.to_csv(args.gen_pose_model, index=False)
    print(f"Saved pose model: {args.gen_pose_model}")

    # Metrics
    metrics = []
    def add_metric(name, val_cm):
        metrics.append({"measurement": name, "value_cm": round(val_cm,2)})

    # 1) Shoulder width (11,12)
    sh_px = pixel_dist(pose[11], pose[12])
    sh_cm = sh_px * cm_px
    add_metric("shoulder_width (11-12)", sh_cm)
    print(f"Shoulder width: {sh_px:.1f} px = {sh_cm:.2f} cm")

    # 2) Face width (3,6)
    face_px = pixel_dist(pose[3], pose[6])   # left ear (3) to right ear (6)
    face_cm = face_px * cm_px
    add_metric("face_width_ear_to_ear (3-6)", face_cm)
    print(f"Face width: {face_px:.1f} px = {face_cm:.2f} cm")

    # 3) Neck width (face mesh indices 130 & 243)
    neck_cm = None
    if len(face) > 243:
        neck_px = pixel_dist(face[130], face[243])
        neck_cm = neck_px * cm_px
        add_metric("neck_width_facemesh_130_243", neck_cm)
        print(f"Neck width (face mesh): {neck_px:.1f} px = {neck_cm:.2f} cm")
    else:
        # fallback
        neck_cm = sh_cm * 0.32
        add_metric("neck_width_estimated (0.32*shoulder)", neck_cm)
        print(f"Neck width (estimated): {neck_cm:.2f} cm")

    # 4) All pose connections (optional – comment out if too many)
    for a,b in POSE_CONNECTIONS:
        if a<len(pose) and b<len(pose):
            dist_cm = pixel_dist(pose[a], pose[b]) * cm_px
            add_metric(f"conn_{a}_{b}", dist_cm)

    pd.DataFrame(metrics).to_csv(args.gen_pose_metrics, index=False)
    print(f"\nSaved metrics: {args.gen_pose_metrics}")
    print("Done.")

if __name__ == "__main__":
    main()