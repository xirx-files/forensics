import argparse

import cv2
import mediapipe as mp
import numpy as np
import csv
import math
from pathlib import Path



# # Use 3D distance to ignore rotation
# p1 = np.array([lms[468].x * image_width, lms[468].y * image_height, lms[468].z * image_width])
# p2 = np.array([lms[473].x * image_width, lms[473].y * image_height, lms[473].z * image_width])
# pixel_dist_3d = np.linalg.norm(p1 - p2)
# cm_per_pixel = 6.3 / pixel_dist_3d

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_holistic = mp.solutions.holistic

BG_COLOR = (192, 192, 192)

with mp_holistic.Holistic(
    static_image_mode=True,
    model_complexity=2,
    enable_segmentation=True,
    refine_face_landmarks=True) as holistic:

    parser = argparse.ArgumentParser(description="Process image files.")
    parser.add_argument("images", nargs="+", help="List of image files to process")
    args = parser.parse_args()

    for idx, file in enumerate(args.images):
        image = cv2.imread(file)
        if image is None: continue
        image_height, image_width, _ = image.shape
        results = holistic.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        # --- 1. Export annotated_coords.csv (Updated for Pixel Coordinates) ---
        coord_file = f"./{Path(file).stem}-coords.csv" # f'./tmp/annotated_coords_{idx}.csv'
        with open(coord_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["mediapipe_landmark_desc", "landmark_index", "x_px", "y_px"])
            
            def write_landmarks(landmarks, enum_class=None):
                if not landmarks: return
                for i, landmark in enumerate(landmarks.landmark):
                    desc = enum_class(i).name if enum_class else f"FACE_MESH_{i}"
                    # Multiply normalized values by image dimensions and round to nearest pixel
                    pixel_x = int(landmark.x * image_width)
                    pixel_y = int(landmark.y * image_height)
                    writer.writerow([desc, i, pixel_x, pixel_y])

            write_landmarks(results.pose_landmarks, mp_holistic.PoseLandmark)
            write_landmarks(results.face_landmarks)

        # --- 2. Export annotated_lengths.csv ---
        length_file = f"./{Path(file).stem}-lengths.csv" # f'./tmp/annotated_lengths_{idx}.csv'
        with open(length_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["id", "category", "mediapipe_length_desc", "from_landmark_index", "to_landmark_index", "pixel_length", "length_cm", "ratio", "alt_cm", "notes"])

            def write_connections(id, landmarks, connections, desc_prefix):
                if not landmarks or not connections: return
                lms = landmarks.landmark
                for start_idx, end_idx in connections:
                    # Calculate Euclidean distance in pixels
                    x1, y1 = lms[start_idx].x * image_width, lms[start_idx].y * image_height
                    x2, y2 = lms[end_idx].x * image_width, lms[end_idx].y * image_height
                    dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                    writer.writerow([id, desc_prefix.lower(), f"{desc_prefix}_{start_idx}_{end_idx}", start_idx, end_idx, dist])
                    id += 1
                return id

            id = write_connections(0, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS, "POSE")
            id = write_connections(id, results.face_landmarks, mp_holistic.FACEMESH_TESSELATION, "FACE")

        # --- Visualisation Logic ---
        annotated_image = image.copy()
        if results.segmentation_mask is not None:
            condition = np.stack((results.segmentation_mask,) * 3, axis=-1) > 0.1
            bg_image = np.zeros(image.shape, dtype=np.uint8)
            bg_image[:] = BG_COLOR
            annotated_image = np.where(condition, annotated_image, bg_image)

        mp_drawing.draw_landmarks(
            annotated_image, results.face_landmarks, mp_holistic.FACEMESH_TESSELATION,
            None, mp_drawing_styles.get_default_face_mesh_tesselation_style())
        mp_drawing.draw_landmarks(
            annotated_image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
        
        cv2.imwrite(f'./{Path(file).stem}-image.png', annotated_image) # f'./tmp/annotated_image{idx}.png'
