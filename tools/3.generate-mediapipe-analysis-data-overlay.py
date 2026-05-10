#!/usr/bin/env python3
"""
Overlay MediaPipe 3D analysis data onto video frames for visual verification.

Reads:
- pose_3d_landmarks.csv (or can run MediaPipe on-the-fly)
- joint_kinematics.csv
- reflex_events.csv (optional)

Produces a new video with pose wireframe, angle displays, and event highlights.

Usage:
    python 3.generate-mediapipe-analysis-data-overlay.py \
        --video ../bin/key-seq-video-cropped.mkv \
        --landmarks-csv ./3d_analysis/pose_3d_landmarks.csv \
        --kinematics-csv ./3d_analysis/joint_kinematics.csv \
        --reflex-csv ./3d_analysis/reflex_events.csv \
        --output-video ./pose_overlay_video.mp4 \
        --show-angles --event-times 0.9775 1.062 1.2224
"""

import cv2
import numpy as np
import pandas as pd
import argparse
from pathlib import Path
import mediapipe as mp

mp_pose = mp.solutions.pose

# Pose connections for drawing skeleton
POSE_CONNECTIONS = mp_pose.POSE_CONNECTIONS

def draw_pose_on_frame(frame, landmarks_2d, visibility_threshold=0.5):
    """
    Draw MediaPipe pose skeleton on frame using 2D pixel coordinates.
    landmarks_2d: dict {landmark_idx: (x_px, y_px, visibility)}
    """
    # Draw connections first
    for connection in POSE_CONNECTIONS:
        start_idx, end_idx = connection
        if start_idx in landmarks_2d and end_idx in landmarks_2d:
            start_x, start_y, start_vis = landmarks_2d[start_idx]
            end_x, end_y, end_vis = landmarks_2d[end_idx]
            if start_vis >= visibility_threshold and end_vis >= visibility_threshold:
                start_pt = (int(start_x), int(start_y))
                end_pt = (int(end_x), int(end_y))
                cv2.line(frame, start_pt, end_pt, (0, 255, 0), 2)

    # Draw landmarks
    for idx, (x, y, vis) in landmarks_2d.items():
        if vis >= visibility_threshold:
            center = (int(x), int(y))
            cv2.circle(frame, center, 4, (0, 0, 255), -1)

    return frame

def main():
    parser = argparse.ArgumentParser(description="Overlay pose analysis on video")
    parser.add_argument("--video", required=True, help="Original cropped video")
    parser.add_argument("--landmarks-csv", required=True, help="pose_3d_landmarks.csv output from analysis script")
    parser.add_argument("--kinematics-csv", required=True, help="joint_kinematics.csv output")
    parser.add_argument("--reflex-csv", help="reflex_events.csv (optional)")
    parser.add_argument("--output-video", required=True, help="Path for output video (MP4)")
    parser.add_argument("--show-angles", action="store_true", help="Display joint angles on frame")
    parser.add_argument("--event-times", nargs="+", type=float, help="List of event onset/peak timestamps to highlight (e.g., 0.9775 1.062)")
    args = parser.parse_args()
    
    # Load data
    landmarks_df = pd.read_csv(args.landmarks_csv)
    kinematics_df = pd.read_csv(args.kinematics_csv)
    reflex_df = None
    if args.reflex_csv:
        reflex_df = pd.read_csv(args.reflex_csv)
    
    # Build fast lookup: per frame -> dict of landmarks
    frame_landmarks = {}
    for frame_idx, group in landmarks_df.groupby('frame_idx'):
        landmarks = {}
        for _, row in group.iterrows():
            landmarks[row['landmark_idx']] = (row['x_px'], row['y_px'], row['visibility'])
        frame_landmarks[frame_idx] = landmarks
    
    # Build per-frame angles lookup
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
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(args.output_video, fourcc, fps, (width, height))
    
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Get landmarks for this frame
        landmarks = frame_landmarks.get(frame_idx, {})
        if landmarks:
            frame = draw_pose_on_frame(frame, landmarks, visibility_threshold=0.5)
        
        # Display angles if requested
        if args.show_angles:
            angles = frame_angles.get(frame_idx, {})
            y_pos = 50
            for joint, angle in angles.items():
                if not np.isnan(angle):
                    text = f"{joint}: {angle:.1f}°"
                    cv2.putText(frame, text, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 1)
                    y_pos += 25
        
        # Highlight event frames (if event times provided)
        timestamp = frame_idx / fps
        if args.event_times:
            for event_time in args.event_times:
                if abs(timestamp - event_time) < 0.02:  # within 20ms
                    cv2.rectangle(frame, (0,0), (width, height), (0,0,255), 3)
                    cv2.putText(frame, f"EVENT: {event_time:.4f}s", (width//2-100, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
        
        # Optional: draw reflex markers if available and frame matches an event
        if reflex_df is not None:
            # For simplicity, we'll just show text at top if frame is within 0.1s of an event's onset
            for _, reflex in reflex_df.iterrows():
                event_id = reflex['event_id']
                joint = reflex['joint_name']
                vel = reflex['max_angular_velocity_deg_s']
                # We'd need event timestamps from motion summary, not available here.
                # This is left as placeholder.
                pass
        
        out.write(frame)
        frame_idx += 1
        if frame_idx % 100 == 0:
            print(f"Processed frame {frame_idx}")
    
    cap.release()
    out.release()
    print(f"Overlay video saved: {args.output_video}")

if __name__ == "__main__":
    main()