#!/usr/bin/env python3
"""
OpenPose Body_25 pose estimation for video analysis.
Outputs:
- pose_3d_landmarks.csv: 2D keypoints per frame
- joint_kinematics.csv: joint angles and angular velocities
- reflex_events.csv: event-based reflex detection
"""

import sys
import cv2
import numpy as np
import pandas as pd
import argparse
from pathlib import Path
import math
from scipy.signal import savgol_filter

# Add OpenPose Python bindings path
sys.path.append('/home/ash/prj/openpose/build/python')
from openpose import pyopenpose as op

# ============================================================================
# BODY_25 Keypoint Index Map
# ============================================================================
#                            **25 Keypoints Index Map**
#
#    0: "nose",          12: "right_shoulder",  24: "right_ear",
#    1: "neck",          13: "right_elbow",     --------------------------------------------------
#    2: "right_shoulder",14: "right_wrist",     The mapping order can be extracted from the
#    3: "right_elbow",   15: "left_hip",        C++/Python API (getPoseBodyPartMapping)[reference:1].
#    4: "right_wrist",   16: "left_knee",
#    5: "left_shoulder", 17: "left_ankle",
#    6: "left_elbow",    18: "right_hip",
#    7: "left_wrist",    19: "right_knee",
#    8: "right_hip",     20: "right_ankle",
#    9: "right_knee",    21: "left_heel",
#   10: "right_ankle",   22: "right_heel",
#   11: "left_hip",      23: "left_foot_index",
#                        24: "right_foot_index"

# Named indices for readability
LANDMARK_NAMES = {
    0: "nose", 1: "neck", 2: "right_shoulder", 3: "right_elbow", 4: "right_wrist",
    5: "left_shoulder", 6: "left_elbow", 7: "left_wrist", 8: "right_hip", 9: "right_knee",
    10: "right_ankle", 11: "left_hip", 12: "left_knee", 13: "left_ankle", 14: "right_eye",
    15: "left_eye", 16: "right_ear", 17: "left_ear", 18: "left_big_toe", 19: "left_small_toe",
    20: "left_heel", 21: "right_big_toe", 22: "right_small_toe", 23: "right_heel", 24: "background"
}

LANDMARK_IDX = {v: k for k, v in LANDMARK_NAMES.items() if k < 25}

# Joint angle definitions (three-point system)
JOINT_ANGLES = {
    "left_elbow": {"p1": "left_shoulder", "p2": "left_elbow", "p3": "left_wrist"},
    "right_elbow": {"p1": "right_shoulder", "p2": "right_elbow", "p3": "right_wrist"},
    "left_shoulder": {"p1": "left_hip", "p2": "left_shoulder", "p3": "left_elbow"},
    "right_shoulder": {"p1": "right_hip", "p2": "right_shoulder", "p3": "right_elbow"},
    "left_hip": {"p1": "left_shoulder", "p2": "left_hip", "p3": "left_knee"},
    "right_hip": {"p1": "right_shoulder", "p2": "right_hip", "p3": "right_knee"},
    "left_knee": {"p1": "left_hip", "p2": "left_knee", "p3": "left_ankle"},
    "right_knee": {"p1": "right_hip", "p2": "right_knee", "p3": "right_ankle"},
}

def get_landmark_point(landmarks, key, img_width, img_height):
    """Extract (x, y, confidence) for a given keypoint by name or index."""
    if isinstance(key, str):
        idx = LANDMARK_IDX.get(key, None)
        if idx is None:
            return None
    else:
        idx = key
    if idx < 0 or idx >= len(landmarks):
        return None
    x = landmarks[idx * 3]
    y = landmarks[idx * 3 + 1]
    conf = landmarks[idx * 3 + 2]
    return (x, y, conf)

def compute_angle(landmarks, joint_def, img_width, img_height):
    """Calculate 2D joint angle using cosine law."""
    p1 = get_landmark_point(landmarks, joint_def["p1"], img_width, img_height)
    p2 = get_landmark_point(landmarks, joint_def["p2"], img_width, img_height)
    p3 = get_landmark_point(landmarks, joint_def["p3"], img_width, img_height)
    if any(p is None for p in [p1, p2, p3]):
        return np.nan, np.nan
    # Filter low-confidence detections
    if p1[2] < 0.3 or p2[2] < 0.3 or p3[2] < 0.3:
        return np.nan, np.nan
    
    def angle_between(p_a, p_b, p_c):
        ba = np.array([p_a[0] - p_b[0], p_a[1] - p_b[1]])
        bc = np.array([p_c[0] - p_b[0], p_c[1] - p_b[1]])
        dot = np.dot(ba, bc)
        norm = np.linalg.norm(ba) * np.linalg.norm(bc)
        if norm == 0:
            return np.nan
        cos_angle = dot / norm
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        return np.degrees(np.arccos(cos_angle))
    
    angle = angle_between(p1, p2, p3)
    return angle, p2[2]  # return angle and confidence at joint

def process_video(video_path, motion_summary_df, output_dir, video_fps=None,
                  min_detection_conf=0.5, min_tracking_conf=0.5):
    """Main processing loop."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS) if video_fps is None else video_fps
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # OpenPose configuration
    params = {
        "model_folder": "/home/ash/prj/openpose/models/",
        "model_pose": "BODY_25",
        "net_resolution": "-1x368",
        "keypoint_scale": 0,  # 0 = pixel coordinates
        "num_gpu": 0,          # set to 1 if using GPU
        "num_gpu_start": 0,
    }
    op_wrapper = op.WrapperPython()
    op_wrapper.configure(params)
    op_wrapper.start()
    
    frame_landmarks = {}   # {frame_idx: {idx: (x, y, conf)}}
    frame_angles = {}      # {frame_idx: {joint_name: angle}}
    kinematics_rows = []
    prev_angles = None
    
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        timestamp = frame_idx / fps
        datum = op.Datum()
        datum.cvInputData = frame
        op_wrapper.emplaceAndPop([datum])
        
        # Extract pose keypoints (first person)
        pose_keypoints = np.array(datum.poseKeypoints)
        frame_landmarks[frame_idx] = {}
        landmarks_dict = {}
        if pose_keypoints is not None and len(pose_keypoints) > 0:
            person = pose_keypoints[0]  # shape (25, 3)
            for idx in range(25):
                x = person[idx, 0]
                y = person[idx, 1]
                conf = person[idx, 2]
                frame_landmarks[frame_idx][idx] = (x, y, conf)
                landmarks_dict[idx] = (x, y, conf)
            
            # Joint angle calculation
            angles = {}
            for joint_name, joint_def in JOINT_ANGLES.items():
                angle, conf_joint = compute_angle(person, joint_def, width, height)
                angles[joint_name] = angle if not np.isnan(angle) else np.nan
                # Store kinematics row
                kinematics_rows.append({
                    'frame_idx': frame_idx,
                    'timestamp': timestamp,
                    'joint_name': joint_name,
                    'angle_deg': angle,
                    'angular_velocity_deg_s': np.nan,  # computed in next step
                })
            frame_angles[frame_idx] = angles
            
            # Temporal smoothing of angles
            if len(kinematics_rows) > 2:
                for joint_name in JOINT_ANGLES.keys():
                    # Use Savitzky-Golay filter for smoothing (window=5, polyorder=2)
                    joint_rows = [row for row in kinematics_rows if row['joint_name'] == joint_name]
                    if len(joint_rows) >= 5:
                        angles_series = np.array([row['angle_deg'] for row in joint_rows[-5:]])
                        # Only apply if enough valid values
                        if np.sum(~np.isnan(angles_series)) >= 3:
                            smoothed = savgol_filter(angles_series, 5, 2, mode='interp')
                            for i, row in enumerate(joint_rows[-5:]):
                                row['angle_deg'] = smoothed[i]
        
        prev_angles = angles if 'angles' in locals() else None
        frame_idx += 1
        if frame_idx % 100 == 0:
            print(f"Processed frame {frame_idx}")
    
    cap.release()
    
    # Angular velocity calculation
    kinematics_df = pd.DataFrame(kinematics_rows)
    for joint_name in JOINT_ANGLES.keys():
        mask = kinematics_df['joint_name'] == joint_name
        angles = kinematics_df.loc[mask, 'angle_deg'].values
        dt = 1.0 / fps
        vel = np.gradient(angles, dt)
        kinematics_df.loc[mask, 'angular_velocity_deg_s'] = vel
    
    # Save outputs
    pose_df = []
    for frame_idx, lm_dict in frame_landmarks.items():
        for idx, (x, y, conf) in lm_dict.items():
            pose_df.append({
                'frame_idx': frame_idx,
                'landmark_idx': idx,
                'landmark_name': LANDMARK_NAMES.get(idx, f"unknown_{idx}"),
                'x_px': x,
                'y_px': y,
                'visibility': conf,
                'timestamp': frame_idx / fps,
            })
    pose_df = pd.DataFrame(pose_df)
    pose_df.to_csv(output_dir / 'pose_3d_landmarks.csv', index=False)
    kinematics_df.to_csv(output_dir / 'joint_kinematics.csv', index=False)
    
    # Reflex detection (adapted from your MediaPipe version)
    if motion_summary_df is not None:
        reflex_rows = []
        for _, row in motion_summary_df.iterrows():
            event_id = row['Key_Event#']
            onset_time = row['Onset_V_Time']
            peak_time = row['V_Time']
            baseline_time = onset_time - (1.0 / fps)
            window_kinematics = kinematics_df[(kinematics_df['timestamp'] >= baseline_time) &
                                              (kinematics_df['timestamp'] <= peak_time)]
            for joint_name in JOINT_ANGLES.keys():
                joint_data = window_kinematics[window_kinematics['joint_name'] == joint_name]
                if joint_data.empty:
                    continue
                vel_series = joint_data['angular_velocity_deg_s'].abs()
                max_vel = vel_series.max()
                if np.isnan(max_vel):
                    continue
                max_vel_time = joint_data.loc[vel_series.idxmax(), 'timestamp']
                latency_ms = (max_vel_time - onset_time) * 1000.0
                vel_direction = 'positive' if joint_data.loc[vel_series.idxmax(),
                                    'angular_velocity_deg_s'] > 0 else 'negative'
                reflex_rows.append({
                    'event_id': event_id,
                    'joint_name': joint_name,
                    'max_angular_velocity_deg_s': max_vel,
                    'latency_from_onset_ms': latency_ms,
                    'direction': vel_direction
                })
        reflex_df = pd.DataFrame(reflex_rows)
        reflex_df.to_csv(output_dir / 'reflex_events.csv', index=False)
    
    print(f"Files saved in {output_dir}")
    op_wrapper.stop()

def main():
    parser = argparse.ArgumentParser(description="OpenPose 2D analysis for impact events")
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--motion-summary", required=True, help="CSV with columns: Key_Event#, Onset_V_Time, V_Time")
    parser.add_argument("--output-dir", required=True, help="Directory to save output CSV files")
    parser.add_argument("--fps", type=float, help="Override video FPS")
    parser.add_argument("--landmark-confidence", type=float, default=0.5, help="Minimum detection confidence")
    parser.add_argument("--tracking-confidence", type=float, default=0.5, help="Minimum tracking confidence")
    args = parser.parse_args()
    
    out_dir = Path(args.output_dir)
    out_dir.mkdir(exist_ok=True, parents=True)
    
    motion_df = pd.read_csv(args.motion_summary)
    required_cols = ['Key_Event#', 'Onset_V_Time', 'V_Time']
    if not all(c in motion_df.columns for c in required_cols):
        raise ValueError(f"Motion summary CSV must contain columns: {required_cols}")
    
    process_video(args.video, motion_df, out_dir, args.fps,
                 args.landmark_confidence, args.tracking_confidence)

if __name__ == "__main__":
    main()