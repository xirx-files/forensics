#!/usr/bin/env python3
"""
Forensic MediaPipe Holistic 3D Analysis for Impact Events

Outputs:
- pose_3d_landmarks.csv: 2D/3D landmarks for every frame (or event windows)
- joint_kinematics.csv: joint angles and angular velocities per frame
- reflex_events.csv: per-event reflex detection (peak angular velocity, latency)

Usage:
    python 3.generate-mediapipe-analysis-data.py \\
        --video ../bin/key-seq-video-cropped.mkv \\
        --motion-summary 3.identify-impact-events-motion-summary.csv \\
        --output-dir ./3d_analysis \\
        --fps 30 --landmark-confidence 0.5
"""

import cv2
import numpy as np
import pandas as pd
import argparse
from pathlib import Path
import mediapipe as mp

mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Joint indices for MediaPipe Pose (33 landmarks)
# https://google.github.io/mediapipe/solutions/pose.html
LANDMARK_NAMES = {
    0: "nose", 1: "left_eye_inner", 2: "left_eye", 3: "left_eye_outer",
    4: "right_eye_inner", 5: "right_eye", 6: "right_eye_outer",
    7: "left_ear", 8: "right_ear", 9: "mouth_left", 10: "mouth_right",
    11: "left_shoulder", 12: "right_shoulder", 13: "left_elbow", 14: "right_elbow",
    15: "left_wrist", 16: "right_wrist", 17: "left_pinky", 18: "right_pinky",
    19: "left_index", 20: "right_index", 21: "left_thumb", 22: "right_thumb",
    23: "left_hip", 24: "right_hip", 25: "left_knee", 26: "right_knee",
    27: "left_ankle", 28: "right_ankle", 29: "left_heel", 30: "right_heel",
    31: "left_foot_index", 32: "right_foot_index"
}
# Inverse mapping for name -> index
LANDMARK_NAME_TO_IDX = {v: k for k, v in LANDMARK_NAMES.items()}

# Define joint angle definitions: (point_a, point_b, point_c) where angle at point_b
# Points can be integer indices or landmark names (e.g., "nose")
JOINT_ANGLES = {
    # Neck angle: angle between vertical (0,1,0) and vector from mid-shoulder to nose
    "neck": {
        "type": "relative_to_vertical",
        "p1": "mid_shoulder",  # computed as average of left/right shoulder
        "p2": "nose"
    },
    # Left shoulder abduction: angle between upper arm and torso
    "left_shoulder": {
        "type": "three_points",
        "p1": 11,  # shoulder
        "p2": 13,  # elbow
        "p3": 23   # hip
    },
    "right_shoulder": {
        "type": "three_points",
        "p1": 12,
        "p2": 14,
        "p3": 24
    },
    # Elbow flexion
    "left_elbow": {
        "type": "three_points",
        "p1": 11,
        "p2": 13,
        "p3": 15
    },
    "right_elbow": {
        "type": "three_points",
        "p1": 12,
        "p2": 14,
        "p3": 16
    },
    # Hip flexion
    "left_hip": {
        "type": "three_points",
        "p1": 23,
        "p2": 25,
        "p3": 11
    },
    "right_hip": {
        "type": "three_points",
        "p1": 24,
        "p2": 26,
        "p3": 12
    }
}

def angle_between_vectors(v1, v2):
    """Compute angle in degrees between two vectors."""
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return np.degrees(np.arccos(cos_angle))

def get_landmark_point(landmarks, point_spec):
    """
    Retrieve a landmark point (x,y,z) from the landmarks list.
    point_spec can be:
        - integer index (0-32)
        - string name (e.g., "nose")
        - "mid_shoulder" (special computed point)
    Returns a tuple (x, y, z) or None if not available.
    """
    if point_spec == "mid_shoulder":
        left = get_landmark_point(landmarks, 11)   # left_shoulder
        right = get_landmark_point(landmarks, 12)  # right_shoulder
        if left is None or right is None:
            return None
        return ((left[0] + right[0]) / 2,
                (left[1] + right[1]) / 2,
                (left[2] + right[2]) / 2)
    if isinstance(point_spec, str):
        idx = LANDMARK_NAME_TO_IDX.get(point_spec)
        if idx is None:
            return None
        point_spec = idx
    # Now point_spec should be an integer index
    if point_spec < 0 or point_spec >= len(landmarks):
        return None
    lm = landmarks[point_spec]
    if lm is None:
        return None
    return (lm[0], lm[1], lm[2])  # x_norm, y_norm, z

def compute_joint_angle(landmarks, joint_def, image_width, image_height):
    """
    Compute angle for a given joint definition.
    landmarks: list of (x, y, z, visibility, x_px, y_px) for all 33 points
    Returns angle in degrees (0-180) or NaN if missing landmarks.
    """
    if joint_def["type"] == "three_points":
        p1 = get_landmark_point(landmarks, joint_def["p1"])
        p2 = get_landmark_point(landmarks, joint_def["p2"])
        p3 = get_landmark_point(landmarks, joint_def["p3"])
        if p1 is None or p2 is None or p3 is None:
            return np.nan
        v1 = np.array([p1[0] - p2[0], p1[1] - p2[1], p1[2] - p2[2]])
        v2 = np.array([p3[0] - p2[0], p3[1] - p2[1], p3[2] - p2[2]])
        return angle_between_vectors(v1, v2)
    elif joint_def["type"] == "relative_to_vertical":
        # Neck angle: angle between vertical (0,1,0) and vector from p1 to p2
        p1 = get_landmark_point(landmarks, joint_def["p1"])
        p2 = get_landmark_point(landmarks, joint_def["p2"])
        if p1 is None or p2 is None:
            return np.nan
        vec = np.array([p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]])
        vertical = np.array([0, 1, 0])
        return angle_between_vectors(vec, vertical)
    else:
        return np.nan

def process_video(video_path, motion_summary_df, output_dir, fps_override, min_detection_conf, min_tracking_conf):
    """Main processing function."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video: {video_path}")
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if fps_override:
        video_fps = fps_override
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Video: {total_frames} frames, {video_fps:.2f} fps, {width}x{height}")
    
    # Prepare output CSVs
    pose_rows = []       # each row: frame_idx, timestamp, landmark_idx, x_norm, y_norm, z, visibility, x_px, y_px
    kinematics_rows = [] # frame_idx, timestamp, joint_name, angle_deg, angular_velocity_deg_s
    
    # We'll process frame by frame
    frame_data = []      # list of dict: {'frame_idx':, 'timestamp':, 'landmarks': list of 33 tuples or None}
    
    with mp_holistic.Holistic(
        static_image_mode=False,
        model_complexity=2,
        enable_segmentation=False,   # speed up
        refine_face_landmarks=True,  
        min_detection_confidence=min_detection_conf,
        min_tracking_confidence=min_tracking_conf
    ) as holistic:
        
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            timestamp = frame_idx / video_fps
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = holistic.process(rgb)
            
            # Extract pose landmarks (33)
            landmark_list = [None] * 33
            if results.pose_landmarks:
                for i, lm in enumerate(results.pose_landmarks.landmark):
                    x_norm = lm.x
                    y_norm = lm.y
                    z = lm.z
                    vis = lm.visibility
                    x_px = int(x_norm * width)
                    y_px = int(y_norm * height)
                    landmark_list[i] = (x_norm, y_norm, z, vis, x_px, y_px)
                    # Save to pose_rows
                    pose_rows.append({
                        'frame_idx': frame_idx,
                        'timestamp': timestamp,
                        'landmark_idx': i,
                        'x_norm': x_norm,
                        'y_norm': y_norm,
                        'z': z,
                        'visibility': vis,
                        'x_px': x_px,
                        'y_px': y_px
                    })
            else:
                # No pose detected, still record empty row? We'll skip to save space
                pass
            
            frame_data.append({
                'frame_idx': frame_idx,
                'timestamp': timestamp,
                'landmarks': landmark_list
            })
            
            frame_idx += 1
            if frame_idx % 100 == 0:
                print(f"Processed {frame_idx}/{total_frames} frames")
    
    cap.release()
    print(f"Extracted {len(pose_rows)} landmark records.")
    
    # Save pose_3d_landmarks.csv
    pose_df = pd.DataFrame(pose_rows)
    pose_df.to_csv(output_dir / 'pose_3d_landmarks.csv', index=False)
    print(f"Saved pose_3d_landmarks.csv")
    
    # Compute joint angles for each frame
    prev_angles = {}
    for frame in frame_data:
        frame_idx = frame['frame_idx']
        timestamp = frame['timestamp']
        landmarks = frame['landmarks']
        
        # For each joint, compute angle
        angles = {}
        for joint_name, joint_def in JOINT_ANGLES.items():
            angle = compute_joint_angle(landmarks, joint_def, width, height)
            angles[joint_name] = angle
        
        # Compute angular velocity (difference from previous frame)
        angular_velocities = {}
        if frame_idx > 0 and prev_angles:
            dt = 1.0 / video_fps
            for joint_name in angles:
                if not np.isnan(angles[joint_name]) and not np.isnan(prev_angles.get(joint_name, np.nan)):
                    vel = (angles[joint_name] - prev_angles[joint_name]) / dt
                    angular_velocities[joint_name] = vel
                else:
                    angular_velocities[joint_name] = np.nan
        
        # Save kinematics per joint
        for joint_name in angles:
            kinematics_rows.append({
                'frame_idx': frame_idx,
                'timestamp': timestamp,
                'joint_name': joint_name,
                'angle_deg': angles[joint_name],
                'angular_velocity_deg_s': angular_velocities.get(joint_name, np.nan)
            })
        
        prev_angles = angles.copy()
    
    kinematics_df = pd.DataFrame(kinematics_rows)
    kinematics_df.to_csv(output_dir / 'joint_kinematics.csv', index=False)
    print(f"Saved joint_kinematics.csv")
    
    # Detect reflex events based on motion summary
    if motion_summary_df is not None:
        reflex_rows = []
        for idx, row in motion_summary_df.iterrows():
            event_id = row['Key_Event#']
            onset_time = row['Onset_V_Time']
            peak_time = row['V_Time']
            # baseline = onset_time - 1/video_fps (one frame before onset)
            baseline_time = onset_time - (1.0 / video_fps)
            
            # Define window around onset: from baseline to peak
            start_time = baseline_time
            end_time = peak_time
            # Get kinematics within window
            window_kinematics = kinematics_df[(kinematics_df['timestamp'] >= start_time) & 
                                              (kinematics_df['timestamp'] <= end_time)]
            
            for joint_name in JOINT_ANGLES.keys():
                joint_data = window_kinematics[window_kinematics['joint_name'] == joint_name]
                if joint_data.empty:
                    continue
                # Find max angular velocity (absolute value)
                vel_series = joint_data['angular_velocity_deg_s'].abs()
                max_vel = vel_series.max()
                if np.isnan(max_vel):
                    continue
                # Time of max velocity relative to onset
                max_vel_time = joint_data.loc[vel_series.idxmax(), 'timestamp']
                latency_ms = (max_vel_time - onset_time) * 1000.0
                # Direction: positive vs negative (flexion vs extension)
                vel_direction = 'positive' if joint_data.loc[vel_series.idxmax(), 'angular_velocity_deg_s'] > 0 else 'negative'
                
                reflex_rows.append({
                    'event_id': event_id,
                    'joint_name': joint_name,
                    'max_angular_velocity_deg_s': max_vel,
                    'latency_from_onset_ms': latency_ms,
                    'direction': vel_direction
                })
        
        reflex_df = pd.DataFrame(reflex_rows)
        reflex_df.to_csv(output_dir / 'reflex_events.csv', index=False)
        print(f"Saved reflex_events.csv")
    
    print("Analysis complete.")

def main():
    parser = argparse.ArgumentParser(description="Generate 3D pose analysis for forensic impact events")
    parser.add_argument("--video", required=True, help="Cropped video file (MKV/MP4)")
    parser.add_argument("--motion-summary", required=True, help="CSV from identify-impact-events (columns: Key_Event#, Onset_V_Time, V_Time)")
    parser.add_argument("--output-dir", required=True, help="Directory to save CSV outputs")
    parser.add_argument("--fps", type=float, help="Override video FPS (if auto-detection fails)")
    parser.add_argument("--landmark-confidence", type=float, default=0.5, help="Min detection confidence for MediaPipe")
    parser.add_argument("--tracking-confidence", type=float, default=0.5, help="Min tracking confidence")
    args = parser.parse_args()
    
    out_dir = Path(args.output_dir)
    out_dir.mkdir(exist_ok=True, parents=True)
    
    # Load motion summary
    motion_df = pd.read_csv(args.motion_summary)
    required_cols = ['Key_Event#', 'Onset_V_Time', 'V_Time']
    if not all(c in motion_df.columns for c in required_cols):
        raise ValueError(f"motion-summary CSV must contain columns: {required_cols}")
    
    process_video(args.video, motion_df, out_dir, args.fps, 
                  args.landmark_confidence, args.tracking_confidence)

if __name__ == "__main__":
    main()