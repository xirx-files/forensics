import os
import re
import pandas as pd
import numpy as np
from scipy.optimize import minimize
import sys

# --- Constants ---
SPEED_OF_SOUND_MPS = 349.5 
SUBJECT_GPS = (40.2775277, -111.7140278)

# All 12 GPS Coordinates from README.md
VIDEO_COORDS_GPS = {
    'video-1.mp4': (40.2775366, -111.7139629), 'video-2.MOV': (40.2775, -111.7138),
    'video-4.mp4': (40.2776284, -111.7135264), 'video-13.mp4': (40.2775244, -111.7139668),
    'video-16.mp4': (40.2777484, -111.7140053), 'video-17.mp4': (40.2775749, -111.7140454),
    'video-12.mp4': (40.2775221, -111.7135551), 'video-3.mp4': (40.2775581, -111.7138573),
    'video-5.mp4': (40.2774731, -111.7138948), 'video-6.mp4': (40.2776030, -111.7137271),
    'video-7.mp4': (40.2776557, -111.7140866), 'video-8.mp4': (40.2777456, -111.7139853),
}

# All 12 Visual Time Zero values from README.md
VISUAL_TIME_ZERO = {
    'video-1.mp4': 1.733333, 'video-2.MOV': 8.456667, 'video-4.mp4': 3.366667,
    'video-13.mp4': 8.400000, 'video-16.mp4': 6.005489, 'video-17.mp4': 0.766667,
    'video-12.mp4': 3.016667, 'video-3.mp4': 14.105000, 'video-5.mp4': 3.666667,
    'video-6.mp4': 7.082778, 'video-7.mp4': 25.306667, 'video-8.mp4': 15.725000,
}

def gps_to_local_meters(lat, lon):
    lat_rad = np.deg2rad(SUBJECT_GPS[0])
    m_per_deg_lat = 111132.92 - 559.82 * np.cos(2 * lat_rad) + 1.175 * np.cos(4 * lat_rad)
    m_per_deg_lon = 111320 * np.cos(lat_rad)
    d_lat, d_lon = lat - SUBJECT_GPS[0], lon - SUBJECT_GPS[1]
    return d_lon * m_per_deg_lon, d_lat * m_per_deg_lat

VIDEO_COORDS_METERS = {name: gps_to_local_meters(lat, lon) for name, (lat, lon) in VIDEO_COORDS_GPS.items()}

def get_audio_clip_start_time(exec_file):
    if not os.path.exists(exec_file):
        return None
    try:
        with open(exec_file, 'r') as f:
            content = f.read()
            # Regex removed the trailing space, as identified in diagnostic
            match = re.search(r'ffmpeg -i .* -ss ([\d\.]+)', content) 
            if match:
                return float(match.group(1))
            else:
                return None
    except Exception:
        return None

def calculate_distances():
    try:
        onset_analysis_df = pd.read_csv('bang_onset_analysis.csv', index_col='video_source')
    except FileNotFoundError:
        print("Error: 'bang_onset_analysis.csv' not found.", file=sys.stderr)
        return []
    results = []
    for video_name, coords in VIDEO_COORDS_METERS.items():
        internal_name = video_name.replace('video-', '')
        exec_file = os.path.join(video_name, f'exec-instructions-{internal_name}.md')
        t_offset = get_audio_clip_start_time(exec_file)
        t_visual = VISUAL_TIME_ZERO.get(video_name)
        try:
            relative_bang_time = onset_analysis_df.loc[video_name]['bang_start_time_s']
        except KeyError:
            relative_bang_time = None
        if not all([t_offset is not None, t_visual is not None, relative_bang_time is not None]):
            print(f"Skipping {video_name}: Missing data.", file=sys.stderr)
            continue
        t_bang_absolute = t_offset + relative_bang_time
        delta_t = t_bang_absolute - t_visual
        if delta_t < 0:
            print(f"Warning: Negative delta_t ({delta_t:.4f}s) for {video_name}. Skipping.", file=sys.stderr)
            continue
        results.append({'video': video_name, 'x': coords[0], 'y': coords[1], 'dist_to_source': delta_t * SPEED_OF_SOUND_MPS})
    return results

def error_function(point, circles):
    x, y = point
    error = 0
    for circle in circles:
        cx, cy, r = circle
        error += (np.sqrt((x - cx)**2 + (y - cy)**2) - r)**2
    return error

def find_source_location(distances):
    if len(distances) < 3:
        print("Need at least 3 valid distance points to triangulate.", file=sys.stderr)
        return None
    circles = [(d['x'], d['y'], d['dist_to_source']) for d in distances]
    initial_guess = [np.mean([d['x'] for d in distances]), np.mean([d['y'] for d in distances])]
    result = minimize(error_function, initial_guess, args=(circles,), method='L-BFGS-B')
    return result.x

def main():
    distances = calculate_distances()
    if not distances:
        print("Could not calculate any valid distances. Exiting.", file=sys.stderr)
        return
    source_xy = find_source_location(distances)
    if source_xy is None:
        print("Failed to find a source location with the available data.", file=sys.stderr)
        return
        
    lat_rad = np.deg2rad(SUBJECT_GPS[0])
    m_per_deg_lat = 111132.92 - 559.82 * np.cos(2 * lat_rad) + 1.175 * np.cos(4 * lat_rad)
    m_per_deg_lon = 111320 * np.cos(lat_rad)
    d_lon, d_lat = source_xy[0] / m_per_deg_lon, source_xy[1] / m_per_deg_lat
    final_lat, final_lon = SUBJECT_GPS[0] + d_lat, SUBJECT_GPS[1] + d_lon
    
    # Print results in a parseable format
    print(f"Final_Lat: {final_lat:.7f}")
    print(f"Final_Lon: {final_lon:.7f}")
    print("Distances_Used:")
    for d in distances:
        print(f"  - {d['video']}: {d['dist_to_source']:.2f}")
    print(f"Source_XY: {source_xy[0]:.2f}, {source_xy[1]:.2f}")


if __name__ == '__main__':
    main()