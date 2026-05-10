#!/usr/bin/env python3
"""
Generate overlay video with OpenPose skeleton and joint angles.
"""

import cv2
import numpy as np
import pandas as pd
import argparse
from pathlib import Path

# BODY_25 connection pairs (limbs) for skeleton drawing
CONNECTIONS = [
    (0,1),   # nose -> neck
    (1,8),   # neck -> right_hip        (spine)
    (1,11),  # neck -> left_hip         (spine)
    (1,2),   # neck -> right_shoulder
    (1,5),   # neck -> left_shoulder
    (2,3),   # right_shoulder -> right_elbow
    (3,4),   # right_elbow -> right_wrist
    (5,6),   # left_shoulder -> left_elbow
    (6,7),   # left_elbow -> left_wrist
    (8,9),   # right_hip -> right_knee
    (9,10),  # right_knee -> right_ankle
    (11,12), # left_hip -> left_knee
    (12,13), # left_knee -> left_ankle
    (1,0),   # neck -> nose
    (0,14),  # nose -> right_eye      (approximate)
    (0,15),  # nose -> left_eye       (approximate)
    (14,16), # right_eye -> right_ear
    (15,17), # left_eye -> left_ear
    (18,20), # left_big_toe -> left_heel
    (21,23), # right_big_toe -> right_heel
]

def draw_openpose_skeleton(frame, landmarks, visibility_threshold=0.5):
    """Draw OpenPose skeleton overlay."""
    # Draw connections (limbs)
    for (start_idx, end_idx) in CONNECTIONS:
        if start_idx in landmarks and end_idx in landmarks:
            x1, y1, conf1 = landmarks[start_idx]
            x2, y2, conf2 = landmarks[end_idx]
            if conf1 >= visibility_threshold and conf2 >= visibility_threshold:
                cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
    
    # Draw keypoints as circles
    for _, (x, y, conf) in landmarks.items():
        if conf >= visibility_threshold:
            cv2.circle(frame, (int(x), int(y)), 4, (0, 0, 255), -1)
    
    return frame

def main():
    parser = argparse.ArgumentParser(description="Overlay OpenPose analysis on video")
    parser.add_argument("--video", required=True, help="Cropped video file")
    parser.add_argument("--landmarks-csv", required=True, help="pose_3d_landmarks.csv from OpenPose analysis")
    parser.add_argument("--kinematics-csv", required=True, help="joint_kinematics.csv")
    parser.add_argument("--reflex-csv", help="reflex_events.csv (optional)")
    parser.add_argument("--output-video", required=True, help="Output MP4 path")
    parser.add_argument("--show-angles", action="store_true", help="Display joint angles")
    parser.add_argument("--event-times", nargs="+", type=float, help="Timestamps to highlight")
    args = parser.parse_args()
    
    # Load data
    landmarks_df = pd.read_csv(args.landmarks_csv)
    kinematics_df = pd.read_csv(args.kinematics_csv if args.kinematics_csv else args.landmarks_csv)
    
    # Build lookup tables
    frame_landmarks = {}
    for frame_idx, group in landmarks_df.groupby('frame_idx'):
        landmarks = {}
        for _, row in group.iterrows():
            landmarks[int(row['landmark_idx'])] = (row['x_px'], row['y_px'], row['visibility'])
        frame_landmarks[frame_idx] = landmarks
    
    frame_angles = {}
    for frame_idx, group in kinematics_df.groupby('frame_idx'):
        angles = {row['joint_name']: row['angle_deg'] for _, row in group.iterrows()}
        frame_angles[frame_idx] = angles
    
    # Open video
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise IOError(f"Cannot open video: {args.video}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(args.output_video, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
    
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        landmarks = frame_landmarks.get(frame_idx, {})
        if landmarks:
            frame = draw_openpose_skeleton(frame, landmarks)
        
        if args.show_angles:
            angles = frame_angles.get(frame_idx, {})
            y_pos = 50
            for joint, angle in angles.items():
                if not np.isnan(angle):
                    cv2.putText(frame, f"{joint}: {angle:.1f}°", (10, y_pos),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 1)
                    y_pos += 25
        
        timestamp = frame_idx / fps
        if args.event_times:
            for et in args.event_times:
                if abs(timestamp - et) < 0.02:
                    cv2.rectangle(frame, (0,0), (width, height), (0,0,255), 3)
                    cv2.putText(frame, f"EVENT: {et:.4f}s", (width//2-100, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
        
        out.write(frame)
        frame_idx += 1
        if frame_idx % 100 == 0:
            print(f"Processed frame {frame_idx}")
    
    cap.release()
    out.release()
    print(f"Overlay saved: {args.output_video}")

if __name__ == "__main__":
    main()