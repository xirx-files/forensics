import cv2
import numpy as np
import argparse
import csv
import json
import math
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

def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculates the bearing from point 1 to point 2 in degrees."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    d_lon = lon2 - lon1
    y = math.sin(d_lon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - \
        math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360) % 360

def get_gps_metadata(gps_file):
    with open(gps_file, 'r') as f:
        data = json.load(f)
    
    # Haversine distance
    R = 6371000  # Earth radius in meters
    lat1, lon1 = math.radians(data['camera']['lat']), math.radians(data['camera']['lon'])
    lat2, lon2 = math.radians(data['target']['lat']), math.radians(data['target']['lon'])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    # Bearing
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    bearing = (math.degrees(math.atan2(y, x)) + 360) % 360
    
    return distance, bearing

def get_pixel_calibration(distance_m, frame_width_px, hfov_deg=70):
    """Calculates meters per pixel at the target distance."""
    # Width of the field of view in meters at 'distance'
    fov_width_m = 2 * distance_m * math.tan(math.radians(hfov_deg / 2))
    return fov_width_m / frame_width_px

def get_origin_label(con, u, v, cam_to_target_bearing):
    if con <= 0.60: return "N/A"
    # Map pixel space to compass space
    # u+ (right) is +90 deg from bearing, v+ (down) is +180 (away)
    pixel_angle = math.degrees(math.atan2(v, u))
    motion_bearing = (cam_to_target_bearing + pixel_angle + 90) % 360
    
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = int((motion_bearing + 22.5) / 45) % 8
    return f"{directions[idx]} ({round(motion_bearing)}°)"

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

def classify_event(event_data):
    accel = event_data['Accel_mps2']
    jerk = event_data['Jerk_mps3']
    
    # Thresholds for Forensic Classification
    G_FORCE_THRESHOLD = 49.05  # ~5G
    SYNC_JERK_THRESHOLD = 1500  # High Jerk indicates instant energy transfer
    
    if accel > G_FORCE_THRESHOLD:
        nature = f"Kinetic Strike/Secondary Force ({accel/9.81:.1f}G)"
        tag = "TDOA_SYNC_PRIORITY_1"
    elif jerk > SYNC_JERK_THRESHOLD:
        nature = "Impulse/Electrical Discharge Case"
        tag = "TDOA_SYNC_PRIORITY_2"
    elif accel > 20:
        nature = "Aggressive Voluntary/Reflexive Movement"
        tag = "REFLEX_ONSET"
    else:
        nature = "Minor Kinetic Deviation"
        tag = "LOW_CONFIDENCE"
    return nature, tag
    
def get_adjusted_velocity(vel_m, relative_angle):
    projection_ratio = abs(math.sin(math.radians(relative_angle)))
    adjusted_vel = vel_m / max(projection_ratio, 0.1) 
    return adjusted_vel

def calc_relative_angle(subject_facing_bearing, cam_bearing):
    # The 'impact axis' of interest for lateral movement is 90 degrees 
    # offset from where the subject is facing.
    lateral_axis = (subject_facing_bearing + 90) % 360
    
    # Calculate the shortest angular difference between camera and lateral axis
    diff = abs(cam_bearing - lateral_axis)
    relative_angle = min(diff, 360 - diff)
    
    # If the camera is within 15 degrees of the lateral axis, it's high confidence lateral
    is_high_confidence = relative_angle < 15
    return relative_angle, is_high_confidence

def identify_impact_onsets(frames_data, accel_threshold=15.0, noise_floor=2.0):
    events = []
    for i in range(1, len(frames_data) - 1):
        curr = frames_data[i]
        prev = frames_data[i-1]
        nxt = frames_data[i+1]

        # 1. Detect Acceleration Peak
        if curr['Accel_mps2'] > prev['Accel_mps2'] and \
           curr['Accel_mps2'] > nxt['Accel_mps2'] and \
           curr['Accel_mps2'] > accel_threshold:
            
            # 2. Backtrack to find the floor frame
            idx = i
            while idx > 0 and frames_data[idx]['Accel_mps2'] > noise_floor:
                idx -= 1
            
            # 3. Linear Interpolation for Sub-Frame Accuracy
            # f0 is below noise_floor, f1 is above noise_floor
            f0, f1 = frames_data[idx], frames_data[idx + 1]
            accel_diff = f1['Accel_mps2'] - f0['Accel_mps2']
            
            if accel_diff > 0:
                # Ratio of how far between the frames the threshold was crossed
                fraction = (noise_floor - f0['Accel_mps2']) / accel_diff
                precise_onset_v_time = f0['V_Time'] + fraction * (f1['V_Time'] - f0['V_Time'])
            else:
                precise_onset_v_time = f0['V_Time']

            event_entry = curr.copy()
            event_entry['Onset_V_Time'] = round(precise_onset_v_time, 4)
            events.append(event_entry)

    # 4. Group Overlapping Onsets (Treat as multi-stage impact)
    return group_overlapping_events(events)

def group_overlapping_events(events, temporal_window=0.05):
    if not events: return []
    
    grouped_events = []
    # Sort by onset to ensure sequence
    events.sort(key=lambda x: x['Onset_V_Time'])
    
    current_group = [events[0]]
    
    for i in range(1, len(events)):
        # If the onset is within 50ms (adjustable) of the previous group's onset
        if events[i]['Onset_V_Time'] - current_group[0]['Onset_V_Time'] < temporal_window:
            current_group.append(events[i])
        else:
            grouped_events.append(current_group)
            current_group = [events[i]]
    grouped_events.append(current_group)
    
    # Process groups: return the primary (highest G) event but keep the metadata
    final_output = []
    for group in grouped_events:
        primary = max(group, key=lambda x: x['Accel_mps2'])
        primary['Is_Multi_Stage'] = len(group) > 1
        primary['Stage_Count'] = len(group)
        final_output.append(primary)
        
    return final_output

def main():
    parser = argparse.ArgumentParser(description="Forensic Motion & Kinetic Analysis")
    parser.add_argument("--video", required=True)
    parser.add_argument("-t0", type=float, required=True, help="Start time in seconds")
    parser.add_argument("-hfov", type=float, default=70, help="Camera Horizontal Field of View")
    parser.add_argument("-fs", "--fontScale", type=float, default=0.8, help="Font scale for overlay")
    parser.add_argument("--gps", required=True, help="Path to JSON with camera/target GPS")
    parser.add_argument("-sb", "--subjectBearing", type=float, default=63, required=True, help="Subject's Facing Bearing")
    # parser.add_argument("-lr", "--lateralRange", nargs=2, type=float, default=[18, 108], 
    #                 help="Camera bearing range [min, max] for Lateral HFOV basis")
    args = parser.parse_args()

    # 1. Spatial Calibration
    dist_m, bearing = get_gps_metadata(args.gps)
    cap = cv2.VideoCapture(args.video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    w_px = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    m_per_px = get_pixel_calibration(dist_m, w_px, args.hfov)
    dt = 1.0 / fps

    relative_angle, is_low_confidence = calc_relative_angle(args.subjectBearing, bearing)
    status = "LOW_CONFIDENCE (Longitudinal Gain)" if is_low_confidence else "HIGH_CONFIDENCE (Lateral Gain)"

    print(f"Dist: {dist_m:.2f}m | Subject-Bearing: {args.subjectBearing:.2f}° | Camera-Bearing: {bearing:.2f}° | relative_angle: {relative_angle:.2f}° |  {status} | Scaling: {m_per_px:.4f} m/px")

    cap.set(cv2.CAP_PROP_POS_MSEC, (args.t0 - 0.05) * 1000)
    ret, prev_frame = cap.read()
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    
    frames_data, processed_buffers = [], []
    prev_vel_m, prev_accel_m = 0, 0

    # 1. Main Kinematic Processing Loop
    with open("3.identify-impact-events.csv", mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Motion_Ref', 'V_Time', 'Offset(ms)', 'Vel_mps', 'Accel_mps2', 'Jerk_mps3', 'Origin'])
        writer.writeheader()

        for i in range(int(fps * 0.6)):
            ret, frame = cap.read()
            if not ret: break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            
            # Kinetic energy based epicenter detection
            ke = 0.5 * (flow[..., 0]**2 + flow[..., 1]**2)
            epi = np.unravel_index(np.argmax(gaussian_filter(ke, sigma=2)), ke.shape)
            vel_px, con, curl, u, v = get_kinematic_stats(flow, epi)
            
            # 2. Conversion to Metric
            vel_m = (vel_px * m_per_px) / dt
            vel_m = get_adjusted_velocity(vel_m, relative_angle)
            accel_m = (vel_m - prev_vel_m) / dt
            jerk_m = (accel_m - prev_accel_m) / dt # if i > 0 else 0
            ms = (i / fps) * 1000
            
            vt = (args.t0 + (i / fps))
            origin = get_origin_label(con, u, v, bearing)
            
            row = {
                'Motion_Ref': i,
                'V_Time': round(vt, 3), 
                'Offset(ms)': round(ms, 2), 
                'Vel_mps': round(vel_m, 2), 
                'Accel_mps2': round(accel_m, 2), 
                'Jerk_mps3': round(jerk_m, 2), # Derived via (accel_m - prev_accel_m) / dt
                'Origin': origin
            }            
            writer.writerow(row)
            
            frames_data.append({**row, 'index': i})
            processed_buffers.append((frame.copy(), flow.copy()))
            prev_accel_m, prev_vel_m, prev_gray = accel_m, vel_m, gray

    # 2. Forensic Event Identification (Metric-based)
    events = []

    if frames_data:
        events = identify_impact_onsets(frames_data)
        events = group_overlapping_events(events)

    # 3. CSV Summary & Event Visualizations (Overlay + Heatmap)
    summary_path = "3.identify-impact-events-motion-summary.csv"
    with open(summary_path, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Key_Event#', 'Motion_Ref', 'V_Time', 'Offset(ms)', 'Onset_V_Time', 'Vel_mps', 'Accel_mps2', 'Jerk_mps3', 'Nature', 'Tag', 'Origin'])
        writer.writeheader()
        
        for idx, e in enumerate(events):
            # Detailed Forensic Classification
            cat, tag = classify_event(e)
            writer.writerow({
                'Key_Event#': idx, 
                'Motion_Ref': e['Motion_Ref'], 
                'V_Time': e['V_Time'], 
                'Offset(ms)': e['Offset(ms)'], 
                'Onset_V_Time': e['Onset_V_Time'], 
                'Vel_mps': e['Vel_mps'], 
                'Accel_mps2': e['Accel_mps2'], 
                'Jerk_mps3': e['Jerk_mps3'], 
                'Nature': cat, 
                'Tag': tag,
                'Origin': e['Origin']
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
                    f"Key_Event# {idx} | {e['V_Time']}s | {cat}",
                    f"Vel: {e['Vel_mps']:.2f} | Accel: {e['Accel_mps2']:.2f} | Origin: {e['Origin']}"
                ]
                for line_idx, line in enumerate(text_lines):
                    y_pos = 50 + (line_idx * int(40 * args.fontScale))
                    cv2.putText(combined, line, (40, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 
                                args.fontScale, (255, 255, 255), 3, cv2.LINE_AA)
                    cv2.putText(combined, line, (40, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 
                                args.fontScale, (0, 0, 255), 1, cv2.LINE_AA)
                
                out_name = f"3.identify-impact-events-motion-overlay-{idx}.jpg"
                cv2.imwrite(out_name, combined)

    # 4. Kinematic Profile Visualization
    ms_axis = [f['V_Time'] for f in frames_data]
    plt.figure(figsize=(12, 6))
    plt.plot(ms_axis, [f['Vel_mps'] for f in frames_data], label='Velocity', color='blue', lw=2)
    plt.plot(ms_axis, [f['Accel_mps2'] for f in frames_data], label='Acceleration', color='red', alpha=0.4)
    for e in events:
        plt.axvline(x=e['V_Time'], color='orange', linestyle='--', alpha=0.6)
        plt.axvline(x=e['Onset_V_Time'], color='green', linestyle=':', linewidth=1.5, alpha=0.8)
        plt.text(e['V_Time'], e['Vel_mps'], f" E{events.index(e)}", color='black', fontweight='bold')
    plt.title(f"Forensic Motion Profile (Bearing: {round(bearing, 2)})")
    plt.xlabel("V_Time")
    plt.ylabel("Magnitude")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig("3.identify-impact-events-kinematic-profile.png")

    print(f"\nAnalysis complete with GPS Reference Bearing: {round(bearing, 2)}°")
    print(f"- Reports: {summary_path}")
    print(f"- Visuals: 3.identify-impact-events-kinematic-profile.png, {len(events)} event overlay(s) generated.")

if __name__ == "__main__":
    main()
