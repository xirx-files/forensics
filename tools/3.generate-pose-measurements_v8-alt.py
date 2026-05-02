import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import argparse


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

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_holistic = mp.solutions.holistic

def pixel_dist(a, b):
    return np.hypot(a[0]-b[0], a[1]-b[1])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--front-facing-subject-standing-img", required=True)
    parser.add_argument("--cm-per-pixel", type=float, required=True)
    parser.add_argument("--gen-overlay", required=True)
    parser.add_argument("--gen-pose-model", required=True)
    parser.add_argument("--gen-pose-metrics", required=True)
    args = parser.parse_args()
    image = cv2.imread(args.front_facing_subject_standing_img)
    image_height, image_width, _ = image.shape

    # For static images:
    BG_COLOR = (192, 192, 192) # gray
    with mp_holistic.Holistic(
        static_image_mode=True,
        model_complexity=2,
        enable_segmentation=True,
        refine_face_landmarks=True) as holistic:

        # Convert the BGR image to RGB before processing.
        results = holistic.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        pose = [(int(lm.x*image_width), int(lm.y*image_height)) for lm in results.pose_landmarks.landmark]
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
        sh_cm = sh_px * args.cm_per_pixel
        add_metric("shoulder_width", sh_cm)
        print(f"Shoulder width: {sh_px:.1f} px = {sh_cm:.2f} cm")

        # Face width (ear to ear: 3 left, 6 right)
        face_px = pixel_dist(pose[3], pose[6])
        face_cm = face_px * args.cm_per_pixel
        add_metric("face_width_ear_to_ear", face_cm)
        print(f"Face width: {face_px:.1f} px = {face_cm:.2f} cm")

        # Neck width – forensic standard: 0.32 * shoulder width
        neck_cm = sh_cm * 0.32
        add_metric("neck_width", neck_cm, "(0.32*shoulder_width)")
        print(f"Neck width (estimated): {neck_cm:.2f} cm")

        # (Optional) Add all pose connections
        for (a,b), desc in DESCRIPTIONS.items():
            if a<len(pose) and b<len(pose):
                dist_cm = pixel_dist(pose[a], pose[b]) * args.cm_per_pixel
                add_metric(f"{desc} [{a}-{b}]", dist_cm)

        pd.DataFrame(metrics).to_csv(args.gen_pose_metrics, index=False)
        print(f"\nSaved metrics: {args.gen_pose_metrics}")
        print("Done.")

        annotated_image = image.copy()
        # Draw segmentation on the image.
        # To improve segmentation around boundaries, consider applying a joint
        # bilateral filter to "results.segmentation_mask" with "image".
        condition = np.stack((results.segmentation_mask,) * 3, axis=-1) > 0.1
        bg_image = np.zeros(image.shape, dtype=np.uint8)
        bg_image[:] = BG_COLOR
        annotated_image = np.where(condition, annotated_image, bg_image)
        # Draw pose, left and right hands, and face landmarks on the image.
        mp_drawing.draw_landmarks(
            annotated_image,
            results.face_landmarks,
            mp_holistic.FACEMESH_TESSELATION,
            landmark_drawing_spec=None,
            connection_drawing_spec=mp_drawing_styles
            .get_default_face_mesh_tesselation_style())
        mp_drawing.draw_landmarks(
            annotated_image,
            results.pose_landmarks,
            mp_holistic.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.
            get_default_pose_landmarks_style())
        cv2.imwrite(args.gen_overlay, annotated_image)
        print(f"Saved overlay: {args.gen_overlay}")
        print("Done.")
        
if __name__ == "__main__":
    main()        