# https://share.google/aimode/qb6pY5MMada7M6wUi
# please provide a report on how the following cli execution result can be understood in laymans terms by a reviewer

import cv2
import numpy as np
import argparse
import csv
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter

def get_kinematic_stats(flow, epicenter, window_size=40):
    """Calculates local motion statistics around the identified epicenter."""
    h, w = flow.shape[:2]
    ey, ex = epicenter
    y_min, y_max = max(0, ey-window_size), min(h, ey+window_size)
    x_min, x_max = max(0, ex-window_size), min(w, ex+window_size)
    local_flow = flow[y_min:y_max, x_min:x_max]
    u, v = local_flow[..., 0], local_flow[..., 1]
    mag = np.sqrt(u**2 + v**2)
    dv_dx, du_dy = np.gradient(v, axis=1), np.gradient(u, axis=0)
    curl = np.mean(dv_dx - du_dy)
    mean_u, mean_v, mean_mag = np.mean(u), np.mean(v), np.mean(mag)
    con = np.sqrt(mean_u**2 + mean_v**2) / (mean_mag + 1e-9)
    return mean_mag, con, curl, mean_u, mean_v

def get_origin_label(view, con, u, v):
    """Determines spatial origin based on vector direction and view perspective."""
    if con <= 0.60: return "N/A"
    if view == 'east':
        if abs(u) > abs(v): return "South" if u > 0 else "North"
        else: return "West (Behind)" if v < 0 else "East (Front)"
    return "N/A"

def draw_motion_overlay(frame, flow, step=16):
    """Overlays optical flow vectors (arrows) onto the image frame."""
    h, w = frame.shape[:2]
    y, x = np.mgrid[step/2:h:step, step/2:w:step].reshape(2, -1).astype(int)
    fx, fy = flow[y, x].T
    lines = np.vstack([x, y, x+fx, y+fy]).T.reshape(-1, 2, 2)
    lines = np.int32(lines + 0.5)
    vis = frame.copy()
    cv2.polylines(vis, lines, 0, (0, 255, 0), 1, cv2.LINE_AA)
    for (x1, y1), (_x2, _y2) in lines:
        cv2.circle(vis, (x1, y1), 1, (0, 255, 0), -1)
    return vis

def generate_heatmap(frame, flow):
    """Generates a kinetic energy heatmap overlaid on the frame."""
    mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    mag_norm = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
    mag_norm = np.uint8(mag_norm)
    heatmap = cv2.applyColorMap(mag_norm, cv2.COLORMAP_JET)
    return cv2.addWeighted(frame, 0.6, heatmap, 0.4, 0)

def main():
    parser = argparse.ArgumentParser(description="Forensic Motion & Kinetic Analysis")
    parser.add_argument("--video", required=True)
    parser.add_argument("-t0", type=float, required=True, help="Start time in seconds")
    parser.add_argument("-view", choices=['east', 'north', 'south'], default='east')
    parser.add_argument("-fs", "--fontScale", type=float, default=0.8, help="Font scale for overlay")
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    dt = 1.0 / fps
    cap.set(cv2.CAP_PROP_POS_MSEC, (args.t0 - 0.05) * 1000)
    
    ret, prev_frame = cap.read()
    if not ret: 
        print("Error: Video file not found or unreadable.")
        return
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    
    frames_data = []
    processed_buffers = [] 
    prev_vel, prev_accel = 0, 0

    # 1. Main Kinematic Processing Loop
    with open("3b.analyze-motion-behavior.csv", mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Offset(ms)', 'Vel', 'Accel', 'Jerk', 'Curl', 'Type', 'Origin'])
        writer.writeheader()

        for i in range(int(fps * 0.6)):
            ret, frame = cap.read()
            if not ret: break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            
            # Kinetic energy based epicenter detection
            ke = 0.5 * (flow[..., 0]**2 + flow[..., 1]**2)
            epi = np.unravel_index(np.argmax(gaussian_filter(ke, sigma=2)), ke.shape)
            vel, con, curl, u, v = get_kinematic_stats(flow, epi)
            
            ms = (i / fps) * 1000
            accel = (vel - prev_vel) / dt
            jerk = (accel - prev_accel) / dt
            m_type = "KINETIC" if accel > 200 or (ms == 0 and vel > 3) else ""
            origin = get_origin_label(args.view, con, u, v)

            row = {'Offset(ms)': round(ms, 2), 'Vel': round(vel, 2), 'Accel': round(accel, 2), 
                   'Jerk': round(jerk, 2), 'Curl': round(curl, 4), 'Type': m_type, 'Origin': origin}
            writer.writerow(row)
            
            frames_data.append({**row, 'index': i})
            processed_buffers.append((frame.copy(), flow.copy()))
            prev_vel, prev_accel, prev_gray = vel, accel, gray

    # 2. Forensic Event Identification
    events = []
    if frames_data:
        # Event 0 is always the initial frame of the window
        events.append(frames_data[0]) 
        for i in range(1, len(frames_data)-1):
            if frames_data[i]['Vel'] > frames_data[i-1]['Vel'] and \
               frames_data[i]['Vel'] > frames_data[i+1]['Vel'] and \
               frames_data[i]['Vel'] > 5.0:
                events.append(frames_data[i])

    # 3. CSV Summary & Event Visualizations (Overlay + Heatmap)
    summary_path = "3b.analyze-motion-behavior-forensic-event-summary.csv"
    with open(summary_path, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Event Number', 'Offset(ms)', 'Velocity', 'Accel', 'Jerk', 'Nature', 'Origin'])
        writer.writeheader()
        
        for idx, e in enumerate(events):
            # Detailed Forensic Classification
            if e['Offset(ms)'] < 20: 
                cat = "Direct Kinetic Transfer (Initial Impact/Shockwave)"
            elif e['Offset(ms)'] < 150 and e['Accel'] > 150:
                cat = "Secondary Kinetic Strike or High-Velocity Reflex"
            elif e['Accel'] > 250:
                cat = "Physically Impossible Human Move (External Force Override)"
            else:
                cat = "Voluntary Muscular Effort (Staged/Defense)"

            writer.writerow({
                'Event Number': idx, 'Offset(ms)': e['Offset(ms)'], 'Velocity': e['Vel'], 
                'Accel': e['Accel'], 'Jerk': e['Jerk'], 'Nature': cat, 'Origin': e['Origin']
            })

            # Visualization Logic
            frame_idx = e['index']
            if frame_idx < len(processed_buffers):
                event_img, event_flow = processed_buffers[frame_idx]
                
                # Create the Vector Overlay and the Heatmap
                overlay_img = draw_motion_overlay(event_img, event_flow)
                heatmap_img = generate_heatmap(event_img, event_flow)
                
                # Combine them side-by-side
                combined = np.hstack((overlay_img, heatmap_img))
                
                # Annotations
                text_lines = [
                    f"EVENT {idx} | {e['Offset(ms)']}ms | {cat}",
                    f"Vel: {e['Vel']} | Accel: {e['Accel']} | Origin: {e['Origin']}"
                ]
                for line_idx, line in enumerate(text_lines):
                    y_pos = 50 + (line_idx * int(40 * args.fontScale))
                    cv2.putText(combined, line, (40, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 
                                args.fontScale, (255, 255, 255), 3, cv2.LINE_AA)
                    cv2.putText(combined, line, (40, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 
                                args.fontScale, (0, 0, 255), 1, cv2.LINE_AA)
                
                out_name = f"3b.analyze-motion-behavior-peak-motion-overlay-event-{idx}.jpg"
                cv2.imwrite(out_name, combined)

    # 4. Kinematic Profile Visualization
    ms_axis = [f['Offset(ms)'] for f in frames_data]
    plt.figure(figsize=(12, 6))
    plt.plot(ms_axis, [f['Vel'] for f in frames_data], label='Velocity', color='blue', lw=2)
    plt.plot(ms_axis, [f['Accel'] for f in frames_data], label='Acceleration', color='red', alpha=0.4)
    for e in events:
        plt.axvline(x=e['Offset(ms)'], color='orange', linestyle='--', alpha=0.6)
        plt.text(e['Offset(ms)'], e['Vel'], f" E{events.index(e)}", color='black', fontweight='bold')
    plt.title(f"Forensic Motion Profile (View: {args.view.upper()})")
    plt.xlabel("Offset (ms)")
    plt.ylabel("Magnitude")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig("3b.kinematic-profile.png")

    print(f"\nAnalysis complete.")
    print(f"- Reports: 3b.analyze-motion-behavior.csv, {summary_path}")
    print(f"- Visuals: 3b.kinematic-profile.png, {len(events)} event overlay(s) generated.")

if __name__ == "__main__":
    main()
