#!/usr/bin/env python3
"""
Forensic Frame-by-Frame Artifact Generator V4
- Extracts pose landmarks (MediaPipe indices 0-32) using sequential tracking + interpolation.
- Saves pose_model.csv with event_id, frame, landmark_index, x_px, y_px.
- Generates horizontal strip images (baseline, onset, peak) WITHOUT pose overlay.
- Strip images include timestamp text and optional scale bar.
"""

import cv2
import pandas as pd
import numpy as np
import argparse
from pathlib import Path
import mediapipe as mp
import json

mp_holistic = mp.solutions.holistic

# ----------------------------------------------------------------------
# 1. Sequential video processing for pose landmarks (tracking + interpolation)
# ----------------------------------------------------------------------
def process_video_sequential(video_path, fps=None, out_dir):
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
    forensic_log = []

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

            # motion data
            # Structure the data for LLM ingestion
            frame_data = {
                "frame_index": int(cap.get(cv2.CAP_PROP_POS_FRAMES)),
                "timestamp_ms": cap.get(cv2.CAP_PROP_POS_MSEC),
                "pose_3d": None,
                "face_3d": None
            }

            # Pose World Landmarks are essential for "falling back" 
            # as they provide a metric 3D space (X, Y, Z in meters)
            if results.pose_world_landmarks:
                frame_data["pose_3d"] = [
                    {"x": lm.x, "y": lm.y, "z": lm.z, "vis": lm.visibility} 
                    for lm in results.pose_world_landmarks.landmark
                ]

            # Face landmarks capture the "face to sky" rotation
            if results.face_landmarks:
                frame_data["face_3d"] = [
                    {"x": lm.x, "y": lm.y, "z": lm.z} 
                    for lm in results.face_landmarks.landmark
                ]

            forensic_log.append(frame_data)            
            with open(f"{out_dir}/movement-analysis.json", 'w') as f:
                json.dump(forensic_log, f, indent=2)


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

# ----------------------------------------------------------------------
# 2. Strip image generation (no pose overlay)
# ----------------------------------------------------------------------
def add_scale_bar(image, scale_bar_cm, m_per_px):
    """Draw a scale bar on the bottom-left corner of the image."""
    h, w = image.shape[:2]
    bar_px = int(scale_bar_cm / 100 / m_per_px) if m_per_px else 0
    if bar_px > 10:
        cv2.rectangle(image, (10, h - 20), (10 + bar_px, h - 5), (255, 255, 0), -1)
        cv2.putText(image, f"{scale_bar_cm} cm", (15, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    return image

def generate_strip_frame(frame, label, timestamp, scale_bar_cm=None, m_per_px=None):
    """
    Create a single frame with white header, timestamp, and optional scale bar.
    No pose drawing.
    """
    h, w = frame.shape[:2]
    label_h = 60
    canvas = np.ones((h + label_h, w, 3), dtype=np.uint8) * 255
    canvas[label_h:h + label_h, 0:w] = frame
    cv2.putText(canvas, f"{label.upper()} {timestamp:.4f}s", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    if scale_bar_cm and m_per_px:
        canvas = add_scale_bar(canvas, scale_bar_cm, m_per_px)
    return canvas

# ----------------------------------------------------------------------
# 3. Main
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Extract pose landmarks and generate strips (no pose overlay).")
    parser.add_argument("--motion-summary", required=True,
                        help="CSV from identify-impact-events (must have Key_Event#, Onset_V_Time, V_Time)")
    parser.add_argument("--video", required=True,
                        help="Original cropped video file")
    parser.add_argument("--output-dir", required=True,
                        help="Directory to save pose_model.csv and event strips")
    parser.add_argument("--scale-cm", type=float, default=10,
                        help="Length of scale bar in cm (used only if --m-per-px is given)")
    parser.add_argument("--m-per-px", type=float,
                        help="Meters per pixel (from calibration). If provided, adds scale bar.")
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

    # ------------------------------------------------------------------
    # Step 1: Process video sequentially to get pose landmarks for all frames
    # ------------------------------------------------------------------
    print("Processing entire video with MediaPipe Holistic (tracking mode)...")
    frame_landmarks, _, _, fps = process_video_sequential(args.video, args.fps, out_dir)
    print(f"Processed {len(frame_landmarks)} frames at {fps:.2f} FPS.")

    # ------------------------------------------------------------------
    # Step 2: Build pose_model.csv
    # ------------------------------------------------------------------
    pose_rows = []
    for idx, row in df.iterrows():
        event_id = int(row['Key_Event#'])
        onset_time = row['Onset_V_Time']
        peak_time = row['V_Time']
        baseline_time = onset_time - (1/fps)   # one frame before onset

        for label, t in [('baseline', baseline_time), ('onset', onset_time), ('peak', peak_time)]:
            frame_idx = int(round(t * fps))
            landmarks = get_landmarks_for_frame(frame_landmarks, frame_idx, args.interpolation_range)

            if landmarks is None:
                print(f"Event {event_id}: No landmarks and cannot interpolate for {label}")
                continue

            for lm_idx, (x, y) in landmarks.items():
                pose_rows.append({
                    'event_id': event_id,
                    'frame': label,
                    'landmark_index': lm_idx,
                    'x_px': x,
                    'y_px': y
                })

    if pose_rows:
        csv_path = out_dir / "pose_model.csv"
        pd.DataFrame(pose_rows).to_csv(csv_path, index=False)
        print(f"Saved pose_model.csv with {len(pose_rows)} landmark records.")
    else:
        print("No landmarks extracted. pose_model.csv not created.")

    # ------------------------------------------------------------------
    # Step 3: Generate strip images (no pose overlay)
    # ------------------------------------------------------------------
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"Error: Cannot open video {args.video}")
        return

    for idx, row in df.iterrows():
        event_id = int(row['Key_Event#'])
        onset_time = row['Onset_V_Time']
        peak_time = row['V_Time']
        baseline_time = onset_time - (1/fps)   # one frame before onset

        frames_info = []
        for label, t in [('baseline', baseline_time), ('onset', onset_time), ('peak', peak_time)]:
            frame_idx = int(round(t * fps))
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                print(f"Event {event_id}: Cannot read frame at {t}s ({label})")
                continue
            canvas = generate_strip_frame(frame, label, t, args.scale_cm, args.m_per_px)
            frames_info.append(canvas)

        if len(frames_info) == 3:
            strip = np.hstack(frames_info)
            strip_path = out_dir / f"event_{event_id}_strip.jpg"
            cv2.imwrite(str(strip_path), strip)
            print(f"Saved strip: {strip_path}")
        else:
            print(f"Event {event_id}: missing frames, skipping strip generation.")

    cap.release()
    print("Done.")

if __name__ == "__main__":
    main()