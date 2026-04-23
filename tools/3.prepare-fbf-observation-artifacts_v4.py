#!/usr/bin/env python3
"""
Forensic Frame-by-Frame Artifact Generator V4
- Extracts pose landmarks (MediaPipe indices 0-32) without drawing overlays.
- Saves a pose_model.csv with event_id, frame, landmark_index, x_px, y_px.
- Does NOT generate strip images or any visual output.
"""

import cv2
import pandas as pd
import numpy as np
import argparse
from pathlib import Path
import mediapipe as mp

mp_holistic = mp.solutions.holistic

def find_closest_frame(cap, target_time, fps):
    """Seek to frame closest to target_time (seconds). Returns frame, actual_time, frame_idx."""
    target_frame = int(round(target_time * fps))
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
    ret, frame = cap.read()
    if not ret:
        return None, None, None
    actual_time = target_frame / fps
    return frame, actual_time, target_frame

def extract_pose_landmarks(landmarks, h, w):
    """Convert normalized pose landmarks to pixel coordinates dict."""
    if not landmarks:
        return {}
    coords = {}
    for idx, lm in enumerate(landmarks.landmark):
        coords[idx] = (int(lm.x * w), int(lm.y * h))
    return coords

def process_video_sequential(video_path, fps=None):
    """
    Run MediaPipe Holistic on every frame (tracking mode) to get pose landmarks.
    Returns:
        frame_landmarks: list of dicts, each mapping landmark_index -> (x_px, y_px)
        frame_widths, frame_heights: lists of frame dimensions
        fps: actual video fps
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open video {video_path}")
    if fps is None:
        fps = cap.get(cv2.CAP_PROP_FPS)

    frame_landmarks = []
    frame_widths = []
    frame_heights = []

    with mp_holistic.Holistic(
        static_image_mode=False,
        model_complexity=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as holistic:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            h, w = frame.shape[:2]
            frame_widths.append(w)
            frame_heights.append(h)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = holistic.process(rgb)

            # Extract only pose landmarks
            frame_dict = {}
            if results.pose_landmarks:
                frame_dict = {
                    idx: (int(lm.x * w), int(lm.y * h))
                    for idx, lm in enumerate(results.pose_landmarks.landmark)
                }
            frame_landmarks.append(frame_dict)

    cap.release()
    return frame_landmarks, frame_widths, frame_heights, fps

def interpolate_landmarks(landmarks_list, indices, target_idx):
    """Linear interpolation between two landmark dicts (same structure)."""
    if len(landmarks_list) != 2:
        return None
    l0, l1 = landmarks_list[0], landmarks_list[1]
    idx0, idx1 = indices[0], indices[1]
    if idx1 - idx0 == 0:
        return l0
    alpha = (target_idx - idx0) / (idx1 - idx0)

    interp = {}
    for k in l0:
        if k in l1:
            x = l0[k][0] * (1 - alpha) + l1[k][0] * alpha
            y = l0[k][1] * (1 - alpha) + l1[k][1] * alpha
            interp[k] = (int(x), int(y))
    return interp

def get_landmarks_for_frame(frame_landmarks, frame_idx, neighbor_range=10):
    """
    Return landmarks for a specific frame.
    If the frame has no landmarks, interpolate from nearest valid frames.
    """
    if frame_idx < len(frame_landmarks) and frame_landmarks[frame_idx]:
        return frame_landmarks[frame_idx]

    before_idx = None
    after_idx = None
    for i in range(max(0, frame_idx - neighbor_range), frame_idx):
        if i < len(frame_landmarks) and frame_landmarks[i]:
            before_idx = i
            break
    for i in range(frame_idx + 1, min(len(frame_landmarks), frame_idx + neighbor_range + 1)):
        if i < len(frame_landmarks) and frame_landmarks[i]:
            after_idx = i
            break

    if before_idx is None or after_idx is None:
        return None
    return interpolate_landmarks(
        [frame_landmarks[before_idx], frame_landmarks[after_idx]],
        [before_idx, after_idx],
        frame_idx
    )

def main():
    parser = argparse.ArgumentParser(description="Extract pose landmarks without drawing overlays.")
    parser.add_argument("--motion-summary", required=True,
                        help="CSV from identify-impact-events (must have Key_Event#, Onset_V_Time, V_Time)")
    parser.add_argument("--video", required=True,
                        help="Original cropped video file")
    parser.add_argument("--output-dir", required=True,
                        help="Directory to save pose_model.csv")
    parser.add_argument("--fps", type=float,
                        help="Override video FPS (otherwise auto-detected)")
    parser.add_argument("--interpolation-range", type=int, default=10,
                        help="Max frames to search for valid landmarks before/after for interpolation")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(exist_ok=True, parents=True)

    # Load motion summary
    df = pd.read_csv(args.motion_summary)
    required_cols = ['Key_Event#', 'Onset_V_Time', 'V_Time']
    if not all(c in df.columns for c in required_cols):
        print("Error: CSV must contain columns: Key_Event#, Onset_V_Time, V_Time")
        return

    # Process video sequentially to get landmarks for all frames
    print("Processing entire video with MediaPipe Holistic (tracking mode)...")
    frame_landmarks, _, _, fps = process_video_sequential(args.video, args.fps)
    print(f"Processed {len(frame_landmarks)} frames at {fps:.2f} FPS.")

    # Build pose_model.csv rows
    rows = []
    for idx, row in df.iterrows():
        event_id = int(row['Key_Event#'])
        onset_time = row['Onset_V_Time']
        peak_time = row['V_Time']
        baseline_time = onset_time - 0.033   # one frame before onset

        for label, t in [('baseline', baseline_time), ('onset', onset_time), ('peak', peak_time)]:
            frame_idx = int(round(t * fps))
            landmarks = get_landmarks_for_frame(frame_landmarks, frame_idx, args.interpolation_range)

            if landmarks is None:
                print(f"Event {event_id}: No landmarks and cannot interpolate for {label}")
                continue

            for lm_idx, (x, y) in landmarks.items():
                rows.append({
                    'event_id': event_id,
                    'frame': label,
                    'landmark_index': lm_idx,
                    'x_px': x,
                    'y_px': y
                })

    if rows:
        csv_path = out_dir / "pose_model.csv"
        pd.DataFrame(rows).to_csv(csv_path, index=False)
        print(f"Saved pose_model.csv with {len(rows)} landmark records.")
    else:
        print("No landmarks extracted.")

if __name__ == "__main__":
    main()