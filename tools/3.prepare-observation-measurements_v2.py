#!/usr/bin/env python3
"""
Automated measurement calculator – now auto‑generates rows for all events/frames.
Template is used only for measurement names, groups, and notes.
"""

import pandas as pd
import numpy as np
import argparse
from pathlib import Path
import re
import math

# ----------------------------------------------------------------------
# Geometry helpers (same as before)
# ----------------------------------------------------------------------
def distance_px(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def angle_deg(a, b, c):
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    dot = ba[0]*bc[0] + ba[1]*bc[1]
    norm_ba = math.hypot(*ba)
    norm_bc = math.hypot(*bc)
    if norm_ba == 0 or norm_bc == 0:
        return 0.0
    cos_angle = dot / (norm_ba * norm_bc)
    cos_angle = max(-1.0, min(1.0, cos_angle))
    return math.degrees(math.acos(cos_angle))

def horizontal_angle_deg(p1, p2):
    return math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))

def vertical_angle_deg(p1, p2):
    return math.degrees(math.atan2(p2[0] - p1[0], p2[1] - p1[1]))

# ----------------------------------------------------------------------
# Measurement functions (same as before, unchanged)
# ----------------------------------------------------------------------
def neck_width_cm(landmarks, cm_per_px, frame_type):
    face = landmarks.get('face', {})
    if 130 in face and 359 in face:
        dist_px = distance_px(face[130], face[359])
        return dist_px * cm_per_px
    pose = landmarks.get('pose', {})
    if 11 in pose and 12 in pose:
        dist_px = distance_px(pose[11], pose[12])
        return dist_px * cm_per_px * 0.6
    return None

def cheek_to_cheek_width_cm(landmarks, cm_per_px, frame_type):
    face = landmarks.get('face', {})
    if 172 in face and 397 in face:
        dist_px = distance_px(face[172], face[397])
        return dist_px * cm_per_px
    return None

def facial_deformation_width_cm(landmarks, cm_per_px, frame_type):
    return cheek_to_cheek_width_cm(landmarks, cm_per_px, frame_type)

def forward_tilt_cm(landmarks, cm_per_px, frame_type):
    pose = landmarks.get('pose', {})
    face = landmarks.get('face', {})
    if 1 in face and 11 in pose and 12 in pose:
        nose = face[1]
        shoulder_mid = ((pose[11][0] + pose[12][0])//2, (pose[11][1] + pose[12][1])//2)
        dist_px = abs(nose[0] - shoulder_mid[0])
        return dist_px * cm_per_px
    return None

def lateral_tilt_deg(landmarks, cm_per_px, frame_type):
    face = landmarks.get('face', {})
    pose = landmarks.get('pose', {})
    if 168 in face and 14 in face and 11 in pose and 12 in pose:
        head_vec = (face[14][0] - face[168][0], face[14][1] - face[168][1])
        neck_mid = ((pose[11][0] + pose[12][0])//2, (pose[11][1] + pose[12][1])//2)
        ref_up = (neck_mid[0], neck_mid[1] - 100)
        return angle_deg(neck_mid, ref_up, (neck_mid[0] + head_vec[0], neck_mid[1] + head_vec[1]))
    return None

def neck_cavitation_cm(landmarks, cm_per_px, frame_type):
    return 0.0

def humerus_angle_deg(landmarks, cm_per_px, frame_type, side='left'):
    pose = landmarks.get('pose', {})
    if side == 'left':
        shoulder = pose.get(11)
        elbow = pose.get(13)
    else:
        shoulder = pose.get(12)
        elbow = pose.get(14)
    if shoulder and elbow:
        return horizontal_angle_deg(shoulder, elbow)
    return None

def radius_angle_deg(landmarks, cm_per_px, frame_type, side='left'):
    pose = landmarks.get('pose', {})
    if side == 'left':
        shoulder = pose.get(11)
        elbow = pose.get(13)
        wrist = pose.get(15)
    else:
        shoulder = pose.get(12)
        elbow = pose.get(14)
        wrist = pose.get(16)
    if shoulder and elbow and wrist:
        return angle_deg(shoulder, elbow, wrist)
    return None

def distance_from_lap_cm(landmarks, cm_per_px, frame_type, side='left'):
    pose = landmarks.get('pose', {})
    if side == 'left':
        elbow = pose.get(13)
        hip = pose.get(23)
    else:
        elbow = pose.get(14)
        hip = pose.get(24)
    if elbow and hip:
        dist_px = abs(elbow[1] - hip[1])
        return dist_px * cm_per_px
    return None

def inter_knee_distance_cm(landmarks, cm_per_px, frame_type):
    pose = landmarks.get('pose', {})
    if 25 in pose and 26 in pose:
        dist_px = distance_px(pose[25], pose[26])
        return dist_px * cm_per_px
    return None

def tibia_angle_deg(landmarks, cm_per_px, frame_type, side='left'):
    pose = landmarks.get('pose', {})
    if side == 'left':
        knee = pose.get(25)
        ankle = pose.get(27)
    else:
        knee = pose.get(26)
        ankle = pose.get(28)
    if knee and ankle:
        return vertical_angle_deg(knee, ankle)
    return None

# ----------------------------------------------------------------------
# Dispatcher
# ----------------------------------------------------------------------
def compute_measurement(measurement_name, landmarks, cm_per_px, frame_type):
    name = measurement_name.lower()
    if name == 'neck_width_cm':
        return neck_width_cm(landmarks, cm_per_px, frame_type)
    if name == 'cheek_to_cheek_width_cm':
        return cheek_to_cheek_width_cm(landmarks, cm_per_px, frame_type)
    if name == 'facial_deformation_width_cm':
        return facial_deformation_width_cm(landmarks, cm_per_px, frame_type)
    if name == 'forward_tilt_cm':
        return forward_tilt_cm(landmarks, cm_per_px, frame_type)
    if name == 'lateral_tilt_deg':
        return lateral_tilt_deg(landmarks, cm_per_px, frame_type)
    if name == 'neck_cavitation_cm':
        return neck_cavitation_cm(landmarks, cm_per_px, frame_type)
    if name == 'inter_knee_distance_cm':
        return inter_knee_distance_cm(landmarks, cm_per_px, frame_type)
    if name.startswith('leftarm_humerus_angle_deg'):
        return humerus_angle_deg(landmarks, cm_per_px, frame_type, side='left')
    if name.startswith('rightarm_humerus_angle_deg'):
        return humerus_angle_deg(landmarks, cm_per_px, frame_type, side='right')
    if name.startswith('leftarm_radius_angle_deg'):
        return radius_angle_deg(landmarks, cm_per_px, frame_type, side='left')
    if name.startswith('rightarm_radius_angle_deg'):
        return radius_angle_deg(landmarks, cm_per_px, frame_type, side='right')
    if name.startswith('leftarm_distance_from_lap_cm'):
        return distance_from_lap_cm(landmarks, cm_per_px, frame_type, side='left')
    if name.startswith('rightarm_distance_from_lap_cm'):
        return distance_from_lap_cm(landmarks, cm_per_px, frame_type, side='right')
    if name.startswith('leftleg_tibia_angle_deg'):
        return tibia_angle_deg(landmarks, cm_per_px, frame_type, side='left')
    if name.startswith('rightleg_tibia_angle_deg'):
        return tibia_angle_deg(landmarks, cm_per_px, frame_type, side='right')
    return None

# ----------------------------------------------------------------------
# Main script (auto‑generates rows)
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Auto‑generate measurements for all events/frames.")
    parser.add_argument("--landmarks-dir", required=True, help="Directory containing event_*_landmarks.csv files")
    parser.add_argument("--template", required=True, help="Measurement template CSV (used only for schema)")
    parser.add_argument("--m-per-px", type=float, required=True, help="Calibration: meters per pixel")
    parser.add_argument("--output", default="observation-measurement.csv", help="Output CSV file name")
    args = parser.parse_args()

    cm_per_px = args.m_per_px * 100.0
    print(f"Calibration: {args.m_per_px} m/px → {cm_per_px:.4f} cm/px")

    # Load template for schema (measurement groups, names, notes)
    schema_df = pd.read_csv(args.template)
    required_cols = ['Measurement_Group', 'Measurement_Name', 'Notes']
    for col in required_cols:
        if col not in schema_df.columns:
            raise ValueError(f"Template missing column: {col}")
    # Optionally keep Event_ID and Frame_Type from template if present, but we will override
    schema = schema_df[['Measurement_Group', 'Measurement_Name', 'Notes']].drop_duplicates()

    # Load all landmark CSVs
    landmarks_dir = Path(args.landmarks_dir)
    landmark_files = list(landmarks_dir.glob("event_*_landmarks.csv"))
    if not landmark_files:
        print("No event_*_landmarks.csv files found.")
        return

    landmark_data = {}  # landmark_data[event_id][frame_type] = landmarks dict
    for lfile in landmark_files:
        match = re.search(r'event_(\d+)_landmarks', lfile.name)
        if not match:
            continue
        event_id = int(match.group(1))
        df_land = pd.read_csv(lfile)
        for frame_type, group in df_land.groupby('frame'):
            landmarks = {'face': {}, 'pose': {}, 'left_hand': {}, 'right_hand': {}}
            for _, row in group.iterrows():
                part = row['part']
                idx = int(row['landmark_index'])
                x = int(row['x_px'])
                y = int(row['y_px'])
                if part in landmarks:
                    landmarks[part][idx] = (x, y)
            if event_id not in landmark_data:
                landmark_data[event_id] = {}
            landmark_data[event_id][frame_type] = landmarks
    print(f"Loaded landmarks for {len(landmark_data)} events.")

    # Build output rows for every event, frame, and measurement
    output_rows = []
    for event_id, frames in landmark_data.items():
        for frame_type in frames.keys():
            landmarks = frames[frame_type]
            for _, row in schema.iterrows():
                meas_name = row['Measurement_Name']
                value = compute_measurement(meas_name, landmarks, cm_per_px, frame_type)
                out_row = {
                    'Event_ID': event_id,
                    'Frame_Type': frame_type,
                    'Measurement_Group': row['Measurement_Group'],
                    'Measurement_Name': meas_name,
                    'Value_cm': None,
                    'Value_deg': None,
                    'Notes': row['Notes']
                }
                if value is not None:
                    if meas_name.endswith('_cm') or 'width' in meas_name or 'distance' in meas_name:
                        out_row['Value_cm'] = round(value, 2)
                    elif meas_name.endswith('_deg') or 'angle' in meas_name:
                        out_row['Value_deg'] = round(value, 2)
                    else:
                        out_row['Value_cm'] = round(value, 2)
                output_rows.append(out_row)

    output_df = pd.DataFrame(output_rows)
    # Sort nicely
    output_df = output_df.sort_values(['Event_ID', 'Frame_Type', 'Measurement_Group', 'Measurement_Name'])
    output_df.to_csv(args.output, index=False)
    print(f"Saved measurements for {output_df['Event_ID'].nunique()} events to {args.output}")
    print("Note: Values for clench_score, wound descriptions, blood flow rate, etc. remain empty (they are not auto‑computed).")

if __name__ == "__main__":
    main()