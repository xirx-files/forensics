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

parser = argparse.ArgumentParser()
parser.add_argument("images", nargs="+")
parser.add_argument("--subject-lengths", help="CSV file with manual measurements")
args = parser.parse_args()

subject_measures = load_subject_lengths(args.subject_lengths)

with mp_holistic.Holistic(static_image_mode=True, model_complexity=2) as holistic:
    for file in args.images:
        image = cv2.imread(file)
        if image is None: continue
        results = holistic.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if not results.pose_world_landmarks: continue

        world_lms = results.pose_world_landmarks.landmark

        # --- 3D LENGTHS & VALIDATION ---
        l3d_file = f"./{Path(file).stem}-3D-lengths.csv"
        with open(l3d_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Connection", "from_index", "to_index", "est_meters", "manual_cm", "error_cm"])
            
            for name, data in subject_measures.items():
                p1, p2 = world_lms[data['from']], world_lms[data['to']]
                est_m = calculate_3d_dist(p1, p2)
                error = (est_m * 100) - data['pref_cm']
                writer.writerow([name, data['from'], data['to'], f"{est_m:.4f}", data['pref_cm'], f"{error:.2f}"])

        # --- 3D JOINT ANGLES ---
        angle_file = f"./{Path(file).stem}-3D-angles.csv"
        with open(angle_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Joint", "Point_A", "Vertex_B", "Point_C", "Angle_Deg"])
            
            angles_to_calc = [
                ("Left Elbow", 11, 13, 15), ("Right Elbow", 12, 14, 16),
                ("Left Shoulder", 23, 11, 13), ("Right Shoulder", 24, 12, 14),
                ("Left Knee", 23, 25, 27), ("Right Knee", 24, 26, 28)
            ]
            for name, a, b, c in angles_to_calc:
                deg = calculate_3d_angle(world_lms[a], world_lms[b], world_lms[c])
                writer.writerow([name, a, b, c, f"{deg:.2f}"])

        print(f"Processed forensic data for {file}")
