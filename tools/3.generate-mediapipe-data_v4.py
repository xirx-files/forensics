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


# Load Subject's key measurements if provided
def load_key_measurements(csv_path):
    lengths = {}
    if not csv_path: return lengths
    with open(csv_path, mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lengths[row['mediapipe_connection']] = {
                'from': int(row['from_index']),
                'to': int(row['to_index']),
                'length_m': float(row['manual_calc_length_m'])
            }
    return lengths


# Helper to create a virtual midpoint landmark
def get_midpoint(world_lms, p1_idx, p2_idx):
    p1, p2 = world_lms[p1_idx], world_lms[p2_idx]
    class Point: pass
    p = Point()
    p.x, p.y, p.z = (p1.x + p2.x)/2, (p1.y + p2.y)/2, (p1.z + p2.z)/2
    return p


def export_landmark_coords(results, image_height, image_width, filename_stem, pose_only=False):
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
        if (pose_only): return
        write_landmarks(results.face_landmarks, None, "FACE")
        if results.left_hand_landmarks:
            write_landmarks(results.left_hand_landmarks, mp_holistic.HandLandmark, "LEFT_HAND")
        if results.right_hand_landmarks:
            write_landmarks(results.right_hand_landmarks, mp_holistic.HandLandmark, "RIGHT_HAND")


def export_landmark_lengths(results, image_height, image_width, filename_stem, pose_only=False):
    # --- 2. Export annotated_lengths.csv ---
    length_file = f"{filename_stem}-lengths.csv" 
    with open(length_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["id", "category", "mediapipe_length_desc", "from_landmark_index", "to_landmark_index", "pixel_length", "length_m", "ratio", "alt_m", "notes"])

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
        if (pose_only): return
        id = write_connections(id, results.face_landmarks, mp_holistic.FACEMESH_TESSELATION, "FACE")
        if results.left_hand_landmarks:
            id = write_connections(id, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS, "LEFT_HAND")
        if results.right_hand_landmarks:
            id = write_connections(id, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS, "RIGHT_HAND")


def export_landmark_visual_overlay(results, filename_stem, pose_only=False):
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
        annotated_image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
        landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
    if (pose_only): return
    mp_drawing.draw_landmarks(
        annotated_image, results.face_landmarks, mp_holistic.FACEMESH_TESSELATION,
        None, mp_drawing_styles.get_default_face_mesh_tesselation_style())
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


def export_landmark_3Dlengths(key_measurements, world_lms, filename_stem):
    # --- 3D LENGTHS & VALIDATION ---
    l3d_file = f"{filename_stem}-3D-lengths.csv"
    with open(l3d_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["mediapipe_connection", "from_index", "to_index", "world_lms_est_m", "manual_m", "error_m"])
        
        for name, data in key_measurements.items():
            from_idx = data['from']
            to_idx = data['to']
            if (from_idx >= len(world_lms) or to_idx >= len(world_lms)):
                print(f"Warning: Landmark indices for {name} are out of bounds. Skipping.")
                continue
            p1, p2 = world_lms[data['from']], world_lms[data['to']]
            est_m = calculate_3d_dist(p1, p2)
            error = est_m - data['length_m']
            writer.writerow([name, data['from'], data['to'], f"{est_m:.4f}", data['length_m'], f"{error:.2f}"])


def export_landmark_3Dangles(world_lms, filename_stem):
    # --- 3D JOINT ANGLES (Enhanced for Forensic Reconstruction) ---
    angle_file = f"{filename_stem}-3D-angles.csv"

    # Pre-calculate Forensic Midpoints
    mid_shoulder = get_midpoint(world_lms, 11, 12)
    mid_hip      = get_midpoint(world_lms, 23, 24)
    mid_knee     = get_midpoint(world_lms, 25, 26)
    mid_ear      = get_midpoint(world_lms, 7, 8)

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

            # Torso Twist (Transverse): Mid-Shoulder to Mid-Hip relative to Left Shoulder
            # Helps determine if the chest was squared to the front or turned
            ("Torso_Twist_Orientation_Left", world_lms[11], mid_shoulder, mid_hip)
        ]

        for name, pA, pB, pC in (standard_angles + forensic_angles):
            deg = calculate_3d_angle(pA, pB, pC)
            writer.writerow([name, pA.x, pA.y, pA.z, pB.x, pB.y, pB.z, pC.x, pC.y, pC.z, f"{deg:.2f}"])


def recalibrate_2D_landmarks(results, image_height, image_width, recalib_csv):
    # --- Optional: Recalibrate 2D landmarks using finetuned CSV ---
    if not recalib_csv: return
    recalib_data = {}
    with open(recalib_csv, mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row['category'], int(row['landmark_index']))
            recalib_data[key] = (int(row['x_px']), int(row['y_px']))

    def apply_recalibration(landmarks, category):
        if not landmarks: return
        for i, landmark in enumerate(landmarks.landmark):
            key = (category, i)
            if key in recalib_data:
                x_px, y_px = recalib_data[key]
                landmark.x = x_px / image_width
                landmark.y = y_px / image_height

    apply_recalibration(results.pose_landmarks, "POSE")
    apply_recalibration(results.face_landmarks, "FACE")
    if results.left_hand_landmarks:
        apply_recalibration(results.left_hand_landmarks, "LEFT_HAND")
    if results.right_hand_landmarks:
        apply_recalibration(results.right_hand_landmarks, "RIGHT_HAND")


def reconstruct_3D_from_2D(results, image_height, image_width, key_measurements):
    def reposition_z_coordinates(p1, p2, connection_len_m):
        pass

    if not results.pose_world_landmarks: return
    world_lms = results.pose_world_landmarks.landmark
    for name, data in key_measurements.items():
        from_idx = data['from']
        to_idx = data['to']
        manual_m = data['length_m']
        if (from_idx >= len(world_lms) or to_idx >= len(world_lms)):
            print(f"Warning: Landmark indices for {name} are out of bounds. Skipping.")
            continue
        p1, p2 = world_lms[data['from']], world_lms[data['to']]
        reposition_z_coordinates(p1, p2, manual_m)


parser = argparse.ArgumentParser()
parser.add_argument("images", nargs="+")
parser.add_argument("--key-measurements", help="Key manual measurements CSV file that will be used for validating 3D length estimates. Must have columns: mediapipe_connection, from_index, to_index, manual_calc_length_m")
parser.add_argument("--recalibrate-2D", help="Recalibrate 2D landmark coordinates using finetuned CSV file with columns: mediapipe_landmark_desc, landmark_index, x_px, y_px")
parser.add_argument("--pose-only", action="store_true", help="Generate only pose landmarks data (default: False)")
parser.add_argument("--gen-coords", action="store_true", help="Generate annotated-coords.csv with pixel coordinates for all landmarks (default: False)")
parser.add_argument("--gen-lengths", action="store_true", help="Generate annotated-lengths.csv with 2D length estimates common mediapipe connections (default: False)")
parser.add_argument("--gen-image", action="store_true", help="Generate annotated-image.png with visual overlay of landmarks & connections (default: False)")
parser.add_argument("--gen-3D-lengths", action="store_true", help="Generate annotated-3D-lengths.csv with 3D length estimates for all key measurements (default: False)")
parser.add_argument("--gen-3D-angles", action="store_true", help="Generate annotated-3D-angles.csv with 3D angle estimates for all key postures (default: False)")
parser.add_argument("--gen-all", action="store_true", help="Generate all annotated files (default: False)")

parser.add_argument("--output-dir", default="./pose-measurements", help="Directory to save output CSVs and images")
args = parser.parse_args()
out_dir = Path(args.output_dir)
out_dir.mkdir(exist_ok=True, parents=True)

key_measurements = load_key_measurements(args.key_measurements)

with mp_holistic.Holistic(static_image_mode=True, model_complexity=2) as holistic:
    for file in args.images:
        image = cv2.imread(file)
        filename_stem = out_dir /Path(file).stem
        if image is None: continue
        image_height, image_width, _ = image.shape
        results = holistic.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if args.recalibrate_2D:
            recalibrate_2D_landmarks(results, image_height, image_width, args.recalibrate_2D)   

        if (args.gen_coords or args.gen_all):
            export_landmark_coords(results, image_height, image_width, filename_stem, args.pose_only)
        if (args.gen_lengths or args.gen_all):
            export_landmark_lengths(results, image_height, image_width, filename_stem, args.pose_only)
        if (args.gen_image or args.gen_all):
            export_landmark_visual_overlay(results, filename_stem, args.pose_only)

        if not results.pose_world_landmarks: continue
        world_lms = results.pose_world_landmarks.landmark

        if (args.gen_3D_lengths or args.gen_all):
            export_landmark_3Dlengths(key_measurements, world_lms, filename_stem)
        if (args.gen_3D_angles or args.gen_all):
            export_landmark_3Dangles(world_lms, filename_stem)

        print(f"Processed forensic data for {file}")
