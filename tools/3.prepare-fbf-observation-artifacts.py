import cv2
import pandas as pd
import numpy as np
import argparse
from pathlib import Path
import json

def prepare_forensic_artifacts(video_path, t0, summary_csv, output_dir="gemini-artifacts", contact_sheet=False):
    out_path = Path(output_dir)
    out_path.mkdir(exist_ok=True, parents=True)
    
    df = pd.read_csv(summary_csv)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    start_frame_idx = int((t0 - 0.05) * fps) + 1 
    evidence_log = []
    all_strips = []

    for idx, row in df.iterrows():
        event_id = int(row['Key_Event#'])
        peak_ref = int(row['Motion_Ref'])
        frame_indices = range(peak_ref - 2, peak_ref + 3)
        
        strip_frames = []
        for f_idx in frame_indices:
            absolute_f_idx = start_frame_idx + f_idx
            cap.set(cv2.CAP_PROP_POS_FRAMES, absolute_f_idx)
            ret, frame = cap.read()
            if not ret: continue
            
            # Calculate timestamp
            timestamp_sec = absolute_f_idx / fps
            # timestamp_str = f"{int(timestamp_sec // 60)}m{timestamp_sec % 60:05.2f}s"
            timestamp_str = f"{timestamp_sec % 60:06.3f}s"
            
            # 1. Create whitespace area above frame
            h, w, c = frame.shape
            label_h = 60
            canvas = np.ones((h + label_h, w, c), dtype=np.uint8) * 255
            canvas[label_h:h + label_h, 0:w] = frame
            
            # 2. Place label in whitespace using timestamp
            label = f"E{event_id} | {timestamp_str} | {row['Nature']}"
            cv2.putText(canvas, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            
            strip_frames.append(canvas)

        if not strip_frames: continue

        # Horizontal strip for this event
        event_strip = np.hstack(strip_frames)
        
        if contact_sheet:
            all_strips.append(event_strip)
        strip_filename = out_path / f"event_{event_id}_evidence_strip.jpg"
        cv2.imwrite(str(strip_filename), event_strip)
        
        evidence_log.append({
            "event": event_id,
            "nature": row['Nature'],
            "timestamp": timestamp_str,
            "artifact": str(strip_filename.name)
        })

    # 3. Handle vertical stacking for contact sheet
    if contact_sheet and all_strips:
        contact_sheet_img = np.vstack(all_strips)
        sheet_filename = out_path / "forensic_contact_sheet.jpg"
        cv2.imwrite(str(sheet_filename), contact_sheet_img)
        
        # evidence_log = [{
        #     "type": "contact_sheet",
        #     "artifact": str(sheet_filename.name),
        #     "event_count": len(all_strips)
        # }]

    with open(out_path / "manifest.json", "w") as f:
        json.dump(evidence_log, f, indent=4)

    print(f"Artifacts ready in {output_dir}.")

def main():
    parser = argparse.ArgumentParser(description="Forensic Motion & Kinetic Analysis")
    parser.add_argument("--video", required=True)
    parser.add_argument("-t0", type=float, required=True, help="Start time in seconds")
    parser.add_argument("--motion-summary", required=True)
    parser.add_argument("-o", "--output-dir", required=True)
    parser.add_argument("--contact-sheet", action="store_true", help="Stack all strips vertically into one image")
    args = parser.parse_args()

    prepare_forensic_artifacts(
        args.video, args.t0, args.motion_summary, 
        args.output_dir, args.contact_sheet
    )

if __name__ == "__main__":
    main()
