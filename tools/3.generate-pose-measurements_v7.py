#!/usr/bin/env python3
"""
Forensic Pose Measurement Generator – robust height scaling (handles cropped head)
- Uses MediaPipe Holistic (Pose + Face Mesh)
- If head is fully visible → full height scaling
- If head cropped → scaling via nose‑to‑foot * 0.92 (anthropometric ratio)
- Neck width = 0.32 × shoulder width (forensic standard)
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

# After computing cm_px, define a mapping dictionary
DESCRIPTIONS = {
    (11,12): "shoulder_width",
    (3,6): "face_width_ear_to_ear",
    (11,13): "left_forearm",
    (12,14): "right_forearm",
    (13,15): "left_hand_wrist_to_pinky",
    (14,16): "right_hand_wrist_to_pinky",
    (15,17): "left_hand_pinky_to_index",
    (16,18): "right_hand_pinky_to_index",
    (15,19): "left_hand_pinky_to_thumb",
    (16,20): "right_hand_pinky_to_thumb",
    (17,19): "left_thumb_index_span",
    (18,20): "right_thumb_index_span",
    (11,23): "left_torso_lateral",
    (12,24): "right_torso_lateral",
    (23,25): "left_shin",
    (24,26): "right_shin",
    (25,27): "left_ankle_to_heel",
    (26,28): "right_ankle_to_heel",
    (27,29): "left_foot_heel_to_foot_index",
    (28,30): "right_foot_heel_to_foot_index",
    (27,31): "left_foot_heel_to_big_toe",
    (28,32): "right_foot_heel_to_big_toe",
    (29,31): "left_toe_span",
    (30,32): "right_toe_span",
    (23,24): "knee_width",
    (0,1): "nose_to_left_inner_eye",
    (1,2): "left_eye_width",
    (2,3): "left_eye_to_ear",
    (0,4): "nose_to_left_mouth",
    (4,5): "left_mouth_to_right_inner_eye",
    (5,6): "right_eye_width",
    (6,8): "right_cheek_line",
}
def get_holistic_data(image):
    with mp_holistic.Holistic(static_image_mode=True, model_complexity=2) as holistic:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = holistic.process(rgb)
        if not results.pose_landmarks:
            raise RuntimeError("No pose landmarks detected.")
        h, w = image.shape[:2]
        pose = [(int(lm.x*w), int(lm.y*h)) for lm in results.pose_landmarks.landmark]
        face = []
        if results.face_landmarks:
            face = [(int(lm.x*w), int(lm.y*h)) for lm in results.face_landmarks.landmark]
        return pose, face, w, h

def compute_cm_per_px_robust(pose, face, subject_height_cm, img_h):
    """
    Returns (cm_per_px, method_used, pixel_height_used)
    method_used: 'full_body' or 'nose_to_foot_ratio'
    """
    # Get lowest foot/ankle (indices 27-32)
    foot_y = max(pose[i][1] for i in [27,28,29,30,31,32] if i < len(pose))

    # Try full body using face mesh top (true top of head)
    if face:
        top_y = min(pt[1] for pt in face)   # highest point on forehead/scalp
        if top_y >= 0 and top_y < img_h:
            pixel_height = foot_y - top_y
            if pixel_height > 0:
                return subject_height_cm / pixel_height, 'full_body', pixel_height

    # Fallback: use nose (index 0) to foot, assume nose-to-foot = 0.92 * total height
    # (head height ~8% of total)
    nose_y = pose[0][1]
    nose_to_foot_px = foot_y - nose_y
    pixel_height = nose_to_foot_px / 0.92
    cm_per_px = subject_height_cm / pixel_height
    return cm_per_px, 'nose_to_foot_ratio (head cropped)', pixel_height

def pixel_dist(a, b):
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
    h_img, w_img = img.shape[:2]

    pose, face, w, h = get_holistic_data(img)
    print(f"Pose: {len(pose)} landmarks, Face: {len(face)} landmarks")

    # Scaling
    cm_px, method, px_height = compute_cm_per_px_robust(pose, face, args.subject_height_cm, h_img)
    print(f"Scaling method: {method}")
    print(f"Pixel height used: {px_height:.1f} px")
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
    def add_metric(name, val_cm, note=""):
        full_name = f"{name} {note}".strip()
        metrics.append({"measurement": full_name, "value_cm": round(val_cm,2)})

    # Shoulder width (11,12)
    sh_px = pixel_dist(pose[11], pose[12])
    sh_cm = sh_px * cm_px
    add_metric("shoulder_width", sh_cm)
    print(f"Shoulder width: {sh_px:.1f} px = {sh_cm:.2f} cm")

    # Face width (ear to ear: 3 left, 6 right)
    face_px = pixel_dist(pose[3], pose[6])
    face_cm = face_px * cm_px
    add_metric("face_width_ear_to_ear", face_cm)
    print(f"Face width: {face_px:.1f} px = {face_cm:.2f} cm")

    # Neck width – forensic standard: 0.32 * shoulder width
    neck_cm = sh_cm * 0.32
    add_metric("neck_width", neck_cm, "(0.32*shoulder_width)")
    print(f"Neck width (estimated): {neck_cm:.2f} cm")

    # (Optional) Add all pose connections
    for (a,b), desc in DESCRIPTIONS.items():
        if a<len(pose) and b<len(pose):
            dist_cm = pixel_dist(pose[a], pose[b]) * cm_px
            add_metric(f"{desc}[{a}-{b}]", dist_cm)

    pd.DataFrame(metrics).to_csv(args.gen_pose_metrics, index=False)
    print(f"\nSaved metrics: {args.gen_pose_metrics}")
    print("Done.")

if __name__ == "__main__":
    main()