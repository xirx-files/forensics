import argparse
import cv2
import mediapipe as mp
import numpy as np
import csv
import math
from pathlib import Path

mp_holistic = mp.solutions.holistic

def calculate_3d_dist(p1, p2):
    return math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2 + (p2.z - p1.z)**2)


def calculate_3d_angle(a, b, c):
    """Calculates angle at joint B given points A, B, C using dot product."""
    ba = np.array([a.x - b.x, a.y - b.y, a.z - b.z])
    bc = np.array([c.x - b.x, c.y - b.y, c.z - b.z])
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return np.degrees(angle)


# Load Subject Lengths if provided
def load_subject_lengths(csv_path):
    lengths = {}
    if not csv_path: return lengths
    with open(csv_path, mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lengths[row['Connection']] = {
                'from': int(row['from_index']),
                'to': int(row['to_index']),
                'pref_cm': float(row['preferred_cm'])
            }
    return lengths


# Helper to create a virtual midpoint landmark
def get_midpoint(p1_idx, p2_idx):
    p1, p2 = world_lms[p1_idx], world_lms[p2_idx]
    class Point: pass
    p = Point()
    p.x, p.y, p.z = (p1.x + p2.x)/2, (p1.y + p2.y)/2, (p1.z + p2.z)/2
    return p


def export_landmark_coords(results, image_height, image_width, filename_stem):
    # --- 1. Export annotated_coords.csv (Updated for Pixel Coordinates) ---
    coord_file = f"{filename_stem}-coords.csv" 
    with open(coord_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["category", "mediapipe_landmark_desc", "landmark_index", "x_px", "y_px"])
        
        def write_landmarks(landmarks, enum_class, category):
            if not landmarks: return
            for i, landmark in enumerate(landmarks.landmark):
                desc = enum_class(i).name if enum_class else f"FACE_MESH_{i}"
                # Multiply normalized values by image dimensions and round to nearest pixel
                pixel_x = int(landmark.x * image_width)
                pixel_y = int(landmark.y * image_height)
                writer.writerow([category, desc, i, pixel_x, pixel_y])

        write_landmarks(results.pose_landmarks, mp_holistic.PoseLandmark, "POSE")
        write_landmarks(results.face_landmarks, None, "FACE")
        if results.left_hand_landmarks:
            write_landmarks(results.left_hand_landmarks, mp_holistic.HandLandmark, "LEFT_HAND")
        if results.right_hand_landmarks:
            write_landmarks(results.right_hand_landmarks, mp_holistic.HandLandmark, "RIGHT_HAND")


def export_landmark_lengths(results, image_height, image_width, filename_stem):
    # --- 2. Export annotated_lengths.csv ---
    length_file = f"{filename_stem}-lengths.csv" 
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
        if results.left_hand_landmarks:
            id = write_connections(id, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS, "LEFT_HAND")
        if results.right_hand_landmarks:
            id = write_connections(id, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS, "RIGHT_HAND")


def export_landmark_visual_overlay(results, filename_stem):
    # --- Visualisation Logic ---
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    BG_COLOR = (192, 192, 192)

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
    # Draw Left Hand
    if results.left_hand_landmarks:
        mp_drawing.draw_landmarks(
            annotated_image,
            results.left_hand_landmarks,
            mp_holistic.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style())
    # Draw Right Hand
    if results.right_hand_landmarks:
        mp_drawing.draw_landmarks(
            annotated_image,
            results.right_hand_landmarks,
            mp_holistic.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style())

    cv2.imwrite(f'{filename_stem}-image.png', annotated_image)


def export_landmark_3Dlengths(world_lms, filename_stem):
    # --- 3D LENGTHS & VALIDATION ---
    l3d_file = f"{filename_stem}-3D-lengths.csv"
    with open(l3d_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["mediapipe_connection", "from_index", "to_index", "est_meters", "manual_cm", "error_cm"])
        
        for name, data in subject_measures.items():
            from_idx = data['from']
            to_idx = data['to']
            if (from_idx >= len(world_lms) or to_idx >= len(world_lms)):
                print(f"Warning: Landmark indices for {name} are out of bounds. Skipping.")
                continue
            p1, p2 = world_lms[data['from']], world_lms[data['to']]
            est_m = calculate_3d_dist(p1, p2)
            error = (est_m * 100) - data['pref_cm']
            writer.writerow([name, data['from'], data['to'], f"{est_m:.4f}", data['pref_cm'], f"{error:.2f}"])


def export_landmark_3Dangles(world_lms, filename_stem):
    # --- 3D JOINT ANGLES (Enhanced for Forensic Reconstruction) ---
    angle_file = f"{filename_stem}-3D-angles.csv"

    # Pre-calculate Forensic Midpoints
    mid_shoulder = get_midpoint(11, 12)
    mid_hip      = get_midpoint(23, 24)
    mid_knee     = get_midpoint(25, 26)
    mid_ear      = get_midpoint(7, 8)

    with open(angle_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["mediapipe_joint_description", "point_a_x", "point_a_y", "point_a_z", "vertex_b_x", "vertex_b_y", "vertex_b_z", "point_c_x", "point_c_y", "point_c_z", "angle_deg"])
        
        # Standard Limb Angles
        standard_angles = [
            ("Left Elbow", world_lms[11], world_lms[13], world_lms[15]),
            ("Right Elbow", world_lms[12], world_lms[14], world_lms[16]),
            ("Left Knee", world_lms[23], world_lms[25], world_lms[27]),
            ("Right Knee", world_lms[24], world_lms[26], world_lms[28])
        ]

        # Forensic Posture Angles
        forensic_angles = [
            # Torso lean: angle between spine and thighs
            ("Torso_Lean_Forward_Back", mid_shoulder, mid_hip, mid_knee),
            
            # Head Lateral Tilt: Angle of head relative to shoulder line
            ("Head_Tilt_Lateral_Left", mid_ear, mid_shoulder, world_lms[11]),
            
            # Head Pitch: Is the nose dipped or raised relative to the spine
            ("Head_Pitch_Forward_Back", world_lms[0], mid_ear, mid_shoulder),

            # Torso Twist (Transverse): Mid-Shoulder to Mid-Hip relative to Right Shoulder
            # Helps determine if the chest was squared to the front or turned
            ("Torso_Twist_Orientation", world_lms[12], mid_shoulder, mid_hip)
        ]

        for name, pA, pB, pC in (standard_angles + forensic_angles):
            deg = calculate_3d_angle(pA, pB, pC)
            # writer.writerow([name, "calc", "calc", "calc", f"{deg:.2f}"])
            writer.writerow([name, pA.x, pA.y, pA.z, pB.x, pB.y, pB.z, pC.x, pC.y, pC.z, f"{deg:.2f}"])


parser = argparse.ArgumentParser()
parser.add_argument("images", nargs="+")
parser.add_argument("--subject-lengths", help="CSV file with manual measurements")
parser.add_argument("--output-dir", default="./pose-measurements", help="Directory to save output CSVs and images")
args = parser.parse_args()
out_dir = Path(args.output_dir)
out_dir.mkdir(exist_ok=True, parents=True)

subject_measures = load_subject_lengths(args.subject_lengths)

with mp_holistic.Holistic(static_image_mode=True, model_complexity=2) as holistic:
    for file in args.images:
        image = cv2.imread(file)
        filename_stem = out_dir /Path(file).stem
        if image is None: continue
        image_height, image_width, _ = image.shape
        results = holistic.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        export_landmark_coords(results, image_height, image_width, filename_stem)
        export_landmark_lengths(results, image_height, image_width, filename_stem)
        export_landmark_visual_overlay(results, filename_stem)

        if not results.pose_world_landmarks: continue
        world_lms = results.pose_world_landmarks.landmark

        export_landmark_3Dlengths(world_lms, filename_stem)
        export_landmark_3Dangles(world_lms, filename_stem)

        print(f"Processed forensic data for {file}")
