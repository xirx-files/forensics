#!/usr/bin/env python3
"""
Forensic Frame-by-Frame Artifact Generator V3
- Processes entire video once with MediaPipe Holistic (tracking + interpolation)
- For each event: extracts baseline (onset - 0.033s), onset, and peak frames
- Draws pose using MediaPipe connection specs (full skeleton, hands, optional face mesh)
- Saves a horizontal strip (3 frames) and a CSV of landmark coordinates (pixel & normalized)
- Supports --skip-posing to disable landmark drawing
"""

import cv2
import pandas as pd
import numpy as np
import argparse
from pathlib import Path
import mediapipe as mp

mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# ----------------------------------------------------------------------
# 1. Sequential video processing (MediaPipe with tracking)
# ----------------------------------------------------------------------
def process_video_sequential(video_path, fps=None):
    """
    Run MediaPipe Holistic on every frame.
    Returns:
        frame_landmarks: list of dicts, each with keys 'face','pose','left_hand','right_hand'
                         mapping landmark index -> (x_px, y_px)
        frame_widths, frame_heights: lists of frame dimensions (for normalization)
        fps: actual video fps (auto-detected if not provided)
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

            # Extract landmarks as pixel coordinates
            frame_dict = {}
            if results.face_landmarks:
                frame_dict['face'] = {
                    i: (int(lm.x * w), int(lm.y * h))
                    for i, lm in enumerate(results.face_landmarks.landmark)
                }
            if results.pose_landmarks:
                frame_dict['pose'] = {
                    i: (int(lm.x * w), int(lm.y * h))
                    for i, lm in enumerate(results.pose_landmarks.landmark)
                }
            if results.left_hand_landmarks:
                frame_dict['left_hand'] = {
                    i: (int(lm.x * w), int(lm.y * h))
                    for i, lm in enumerate(results.left_hand_landmarks.landmark)
                }
            if results.right_hand_landmarks:
                frame_dict['right_hand'] = {
                    i: (int(lm.x * w), int(lm.y * h))
                    for i, lm in enumerate(results.right_hand_landmarks.landmark)
                }
            frame_landmarks.append(frame_dict)

    cap.release()
    return frame_landmarks, frame_widths, frame_heights, fps


# ----------------------------------------------------------------------
# 2. Interpolation helpers (same as V2)
# ----------------------------------------------------------------------
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
    for part in l0:
        if part in l1:
            interp[part] = {}
            for k in l0[part]:
                if k in l1[part]:
                    x = l0[part][k][0] * (1 - alpha) + l1[part][k][0] * alpha
                    y = l0[part][k][1] * (1 - alpha) + l1[part][k][1] * alpha
                    interp[part][k] = (int(x), int(y))
    return interp


def get_landmarks_for_frame(frame_landmarks, frame_idx, neighbor_range=10):
    """
    Return landmarks for a specific frame.
    If the frame has no landmarks, interpolate from nearest valid frames within range.
    """
    if frame_idx < len(frame_landmarks) and frame_landmarks[frame_idx]:
        return frame_landmarks[frame_idx]

    # Find nearest valid frames before and after
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
# 3. Custom drawing using MediaPipe connection specs
# ----------------------------------------------------------------------
def draw_pose_custom(frame, landmarks, draw_face=True, draw_pose=True, draw_hands=True,
                     full_face_mesh=False):
    """
    Draw landmarks on a copy of the frame using MediaPipe's predefined connections.
    - full_face_mesh: if True, draw all FACEMESH_CONTOURS (dense). If False, only draw key points.
    """
    annotated = frame.copy()
    h, w = annotated.shape[:2]

    # ----- Pose (skeleton) -----
    if draw_pose and 'pose' in landmarks:
        pose_lm = landmarks['pose']
        # Draw connections
        for a, b in mp_holistic.POSE_CONNECTIONS:
            if a in pose_lm and b in pose_lm:
                cv2.line(annotated, pose_lm[a], pose_lm[b], (0, 255, 0), 2)
        # Draw landmark points
        for pt in pose_lm.values():
            cv2.circle(annotated, pt, 3, (0, 255, 0), -1)

    # ----- Hands -----
    if draw_hands:
        # Left hand
        if 'left_hand' in landmarks:
            hand_lm = landmarks['left_hand']
            for a, b in mp_holistic.HAND_CONNECTIONS:
                if a in hand_lm and b in hand_lm:
                    cv2.line(annotated, hand_lm[a], hand_lm[b], (0, 255, 255), 2)
            for pt in hand_lm.values():
                cv2.circle(annotated, pt, 2, (0, 255, 255), -1)
        # Right hand
        if 'right_hand' in landmarks:
            hand_lm = landmarks['right_hand']
            for a, b in mp_holistic.HAND_CONNECTIONS:
                if a in hand_lm and b in hand_lm:
                    cv2.line(annotated, hand_lm[a], hand_lm[b], (0, 255, 255), 2)
            for pt in hand_lm.values():
                cv2.circle(annotated, pt, 2, (0, 255, 255), -1)

    # ----- Face -----
    if draw_face and 'face' in landmarks:
        face_lm = landmarks['face']
        if full_face_mesh:
            # Draw dense face mesh contours (many lines – may be slow)
            for a, b in mp_holistic.FACEMESH_CONTOURS:
                if a in face_lm and b in face_lm:
                    cv2.line(annotated, face_lm[a], face_lm[b], (255, 0, 0), 1)
        else:
            # Just draw key points (e.g., eyes, nose, mouth)
            key_indices = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 33, 133, 362, 263, 61, 291, 13, 14}
            for idx in key_indices:
                if idx in face_lm:
                    cv2.circle(annotated, face_lm[idx], 2, (255, 0, 0), -1)

    return annotated


# ----------------------------------------------------------------------
# 4. Main routine
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Forensic FBF artifact generator V3 (sequential processing + interpolation)"
    )
    parser.add_argument("--motion-summary", required=True,
                        help="CSV from identify-impact-events (must have Key_Event#, Onset_V_Time, V_Time)")
    parser.add_argument("--video", required=True,
                        help="Original cropped video file")
    parser.add_argument("--output-dir", required=True,
                        help="Directory to save strips and CSV files")
    parser.add_argument("--scale-cm", type=float, default=10,
                        help="Length of scale bar in cm (used only if --m-per-px is given)")
    parser.add_argument("--m-per-px", type=float,
                        help="Meters per pixel (from calibration). If provided, adds scale bar.")
    parser.add_argument("--fps", type=float,
                        help="Override video FPS (otherwise auto-detected)")
    parser.add_argument("--skip-posing", action="store_true",
                        help="Skip drawing landmarks (output raw frames with text only)")
    parser.add_argument("--full-face-mesh", action="store_true",
                        help="Draw full dense face mesh (slower, but more detailed)")
    parser.add_argument("--interpolation-range", type=int, default=10,
                        help="Max frames to search for valid landmarks before/after for interpolation")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(exist_ok=True, parents=True)

    # ---- Load motion summary ----
    df = pd.read_csv(args.motion_summary)
    required_cols = ['Key_Event#', 'Onset_V_Time', 'V_Time']
    if not all(c in df.columns for c in required_cols):
        print("Error: CSV must contain columns: Key_Event#, Onset_V_Time, V_Time")
        return

    # ---- Process video sequentially to get landmarks for all frames ----
    print("Processing entire video with MediaPipe Holistic (tracking mode)...")
    frame_landmarks, frame_widths, frame_heights, fps = process_video_sequential(args.video, args.fps)
    print(f"Processed {len(frame_landmarks)} frames at {fps:.2f} FPS.")

    # ---- Re-open video for frame extraction ----
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f"Error: Cannot open video {args.video}")
        return

    # ---- Process each event ----
    for idx, row in df.iterrows():
        event_id = int(row['Key_Event#'])
        onset_time = row['Onset_V_Time']
        peak_time = row['V_Time']
        baseline_time = onset_time - 0.033   # one frame before onset (approx)

        frames_info = []       # will hold three annotated frames
        all_landmark_rows = [] # for CSV export

        for label, t in [('baseline', baseline_time), ('onset', onset_time), ('peak', peak_time)]:
            # Seek to closest frame
            target_frame = int(round(t * fps))
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            if not ret:
                print(f"Event {event_id}: Cannot read frame at {t}s ({label})")
                continue

            h, w = frame.shape[:2]

            # Get landmarks (interpolated if necessary)
            landmarks = get_landmarks_for_frame(frame_landmarks, target_frame, args.interpolation_range)

            # Create canvas with white header (like V1)
            label_h = 60
            canvas = np.ones((h + label_h, w, 3), dtype=np.uint8) * 255
            canvas[label_h:h+label_h, 0:w] = frame

            # Add timestamp text
            cv2.putText(canvas, f"{label.upper()} {t:.4f}s", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

            # Draw pose (if not skipped)
            if not args.skip_posing:
                if landmarks is None:
                    cv2.putText(canvas, "NO POSE DATA", (20, 80),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    annotated_frame = canvas
                else:
                    # Draw on the frame region only (skip the white header)
                    frame_region = canvas[label_h:h+label_h, 0:w]
                    drawn_frame = draw_pose_custom(frame_region, landmarks,
                                                    draw_face=True,
                                                    draw_pose=True,
                                                    draw_hands=True,
                                                    full_face_mesh=args.full_face_mesh)
                    canvas[label_h:h+label_h, 0:w] = drawn_frame
                    annotated_frame = canvas

                    # Collect landmark coordinates for CSV
                    for part, lm_dict in landmarks.items():
                        for idx_px, (x, y) in lm_dict.items():
                            all_landmark_rows.append({
                                'event_id': event_id,
                                'frame': label,
                                'part': part,
                                'landmark_index': idx_px,
                                'x_px': x,
                                'y_px': y,
                                'x_norm': x / w,
                                'y_norm': y / h
                            })
            else:
                annotated_frame = canvas   # no drawing, only text

            # Add scale bar if calibration provided
            if args.m_per_px and args.scale_cm:
                bar_px = int(args.scale_cm / 100 / args.m_per_px)
                if bar_px > 10:
                    h_canvas, w_canvas = annotated_frame.shape[:2]
                    cv2.rectangle(annotated_frame, (10, h_canvas-20), (10+bar_px, h_canvas-5),
                                  (255, 255, 0), -1)
                    cv2.putText(annotated_frame, f"{args.scale_cm} cm", (15, h_canvas-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

            frames_info.append(annotated_frame)

        # Save horizontal strip if we have all three frames
        if len(frames_info) == 3:
            strip = np.hstack(frames_info)
            strip_path = out_dir / f"event_{event_id}_strip.jpg"
            cv2.imwrite(str(strip_path), strip)
            print(f"Saved {strip_path}")

            # Save CSV with landmark coordinates
            if all_landmark_rows and not args.skip_posing:
                csv_path = out_dir / f"event_{event_id}_landmarks.csv"
                pd.DataFrame(all_landmark_rows).to_csv(csv_path, index=False)
                print(f"Saved landmarks for event {event_id} to {csv_path}")
        else:
            print(f"Event {event_id}: missing frames, skipping strip generation.")

    cap.release()
    print("Done.")


if __name__ == "__main__":
    main()