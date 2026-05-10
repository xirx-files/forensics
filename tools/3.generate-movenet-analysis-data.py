#!/usr/bin/env python3
import cv2
import numpy as np
import pandas as pd
import argparse
import tensorflow as tf
from pathlib import Path

# Load MoveNet Thunder model from TF Hub
# Note: Requires internet to download initially or a local path to the model
import tensorflow_hub as hub
movenet = hub.load("https://tfhub.dev/google/movenet/singlepose/thunder/4") # hub.load("https://tfhub.dev/google/movenet/singlepose/lightning/4") (196) # hub.load("https://tfhub.dev")
movenet_run = movenet.signatures['serving_default']

# MoveNet Keypoint mapping (17 points)
KEYPOINT_DICT = {
    0: "nose", 1: "left_eye", 2: "right_eye", 3: "left_ear", 4: "right_ear",
    5: "left_shoulder", 6: "right_shoulder", 7: "left_elbow", 8: "right_elbow",
    9: "left_wrist", 10: "right_wrist", 11: "left_hip", 12: "right_hip",
    13: "left_knee", 14: "right_knee", 15: "left_ankle", 16: "right_ankle"
}

def run_inference(image):
    """Runs MoveNet inference on a single BGR image."""
    input_image = tf.cast(tf.image.resize_with_pad(image, 256, 256), dtype=tf.int32)
    input_image = tf.expand_dims(input_image, axis=0)
    outputs = movenet_run(input_image)
    # Output shape: [1, 1, 17, 3] -> (y, x, score)
    return outputs['output_0'].numpy()[0][0]

def process_frame(frame, width, height):
    """Extracts MoveNet keypoints and scales to pixel coordinates."""
    keypoints = run_inference(frame)
    processed = []
    for i in range(17):
        y, x, conf = keypoints[i]
        processed.append({
            'landmark_idx': i,
            'name': KEYPOINT_DICT[i],
            'x_px': int(x * width),
            'y_px': int(y * height),
            'visibility': conf
        })
    return processed

def draw_movenet(frame, landmarks, threshold=0.3):
    """Draws MoveNet skeleton for visual verification."""
    # Simplified skeleton connections for MoveNet
    EDGES = [(5,6), (5,11), (6,12), (11,12), (5,7), (7,9), (6,8), (8,10), (11,13), (13,15), (12,14), (14,16)]
    
    pts = {lm['landmark_idx']: (lm['x_px'], lm['y_px'], lm['visibility']) for lm in landmarks}
    
    for start_idx, end_idx in EDGES:
        if pts[start_idx][2] > threshold and pts[end_idx][2] > threshold:
            cv2.line(frame, (pts[start_idx][0], pts[start_idx][1]), 
                     (pts[end_idx][0], pts[end_idx][1]), (0, 255, 0), 2)
    for idx, pt in pts.items():
        if pt[2] > threshold:
            cv2.circle(frame, (pt[0], pt[1]), 4, (0, 0, 255), -1)
    return frame

def main():
    parser = argparse.ArgumentParser()
    # Support for both Video and Image
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--video", help="Input video file")
    group.add_argument("--image", help="Input single image file")
    
    parser.add_argument("--output-dir", default="./movenet_analysis")
    parser.add_argument("--output-video", help="Path for overlay video")
    parser.add_argument("--output-image", help="Path for overlay image")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(exist_ok=True, parents=True)

    # --- IMAGE MODE ---
    if args.image:
        frame = cv2.imread(args.image)
        h, w = frame.shape[:2]
        landmarks = process_frame(frame, w, h)
        pd.DataFrame(landmarks).to_csv(out_dir / "image_landmarks.csv", index=False)
        
        if args.output_image:
            overlay = draw_movenet(frame.copy(), landmarks)
            cv2.imwrite(args.output_image, overlay)
            print(f"Saved: {args.output_image}")

    # --- VIDEO MODE ---
    elif args.video:
        cap = cv2.VideoCapture(args.video)
        w, h = int(cap.get(3)), int(cap.get(4))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        out_video = None
        if args.output_video:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out_video = cv2.VideoWriter(args.output_video, fourcc, fps, (w, h))

        all_rows = []
        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            landmarks = process_frame(frame, w, h)
            for lm in landmarks:
                lm['frame_idx'] = frame_idx
                all_rows.append(lm)
            
            if out_video:
                overlay = draw_movenet(frame, landmarks)
                out_video.write(overlay)
            
            frame_idx += 1
            if frame_idx % 50 == 0: print(f"Processed frame {frame_idx}")

        pd.DataFrame(all_rows).to_csv(out_dir / "pose_landmarks.csv", index=False)
        cap.release()
        if out_video: out_video.release()
        print(f"Video analysis complete. Results in {args.output_dir}")

if __name__ == "__main__":
    main()
