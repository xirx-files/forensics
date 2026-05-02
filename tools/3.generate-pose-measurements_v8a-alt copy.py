import cv2
import mediapipe as mp
import numpy as np
import csv
import math

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_holistic = mp.solutions.holistic

IMAGE_FILES = [
    '../../analysis-considerations/features/CK-standing-1.png',
    '../../analysis-considerations/features/CK-half-body.jpg'
]
BG_COLOR = (192, 192, 192)

with mp_holistic.Holistic(
    static_image_mode=True,
    model_complexity=2,
    enable_segmentation=True,
    refine_face_landmarks=True) as holistic:
    
    for idx, file in enumerate(IMAGE_FILES):
        image = cv2.imread(file)
        if image is None: continue
        image_height, image_width, _ = image.shape
        results = holistic.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        # --- 1. Export annotated_coords.csv ---
        coord_file = f'./tmp/annotated_coords_{idx}.csv'
        with open(coord_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['mediapipe landmark desc', 'mediapipe landmark index', 'mediapipe x', 'mediapipe y'])
            
            # Helper to write landmark sets
            def write_landmarks(landmarks, enum_class=None):
                if not landmarks: return
                for i, landmark in enumerate(landmarks.landmark):
                    desc = enum_class(i).name if enum_class else f"FACE_MESH_{i}"
                    writer.writerow([desc, i, landmark.x, landmark.y])

            write_landmarks(results.pose_landmarks, mp_holistic.PoseLandmark)
            write_landmarks(results.face_landmarks) # FaceMesh doesn't have a simple 1:1 enum mapping in the same way

        # --- 2. Export annotated_lengths.csv ---
        length_file = f'./tmp/annotated_lengths_{idx}.csv'
        with open(length_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['mediapipe length desc', 'landmark from index', 'landmark to index', 'pixel_length'])

            def write_connections(landmarks, connections, desc_prefix):
                if not landmarks or not connections: return
                lms = landmarks.landmark
                for start_idx, end_idx in connections:
                    # Calculate Euclidean distance in pixels
                    x1, y1 = lms[start_idx].x * image_width, lms[start_idx].y * image_height
                    x2, y2 = lms[end_idx].x * image_width, lms[end_idx].y * image_height
                    dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                    writer.writerow([f"{desc_prefix}_{start_idx}_{end_idx}", start_idx, end_idx, dist])

            write_connections(results.pose_landmarks, mp_holistic.POSE_CONNECTIONS, "POSE")
            write_connections(results.face_landmarks, mp_holistic.FACEMESH_TESSELATION, "FACE")

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
        
        cv2.imwrite(f'./tmp/annotated_image{idx}.png', annotated_image)
