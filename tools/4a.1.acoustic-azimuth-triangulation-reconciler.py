import argparse
import numpy as np
import pandas as pd
import math
import os

def calculate_azimuth(tdoa_ms, mic_baseline, c_ms):
    """
    Calculates the 2D angle (Azimuth) of the incoming shockwave.
    0° = Perpendicular to the camera face.
    +° = To the Right.
    -° = To the Left.
    """
    tdoa_s = tdoa_ms / 1000.0
    # Distance the wave traveled between mics
    delta_dist = tdoa_s * c_ms
    
    # Bound the ratio for arcsin (handle noise/clipping)
    ratio = delta_dist / mic_baseline
    if abs(ratio) > 1.0:
        ratio = np.sign(ratio)
        
    # Calculate angle in radians, then degrees
    angle_rad = math.asin(ratio)
    return math.degrees(angle_rad)

def map_to_global(local_angle, view_pos):
    """
    Maps the camera-relative angle to a global 'Subject-Centric' orientation.
    """
    offsets = {
        'east': 90.0,   # Camera is East of subject, looking West
        'north': 0.0,   # Camera is North of subject, looking South
        'south': 180.0, # Camera is South of subject, looking North
        'west': 270.0   # Camera is West of subject, looking East
    }
    base = offsets.get(view_pos, 0.0)
    return (base + local_angle) % 360

def main():
    parser = argparse.ArgumentParser(description="4c: Acoustic Shockwave Reconciler")
    parser.add_argument("--csv", required=True, help="Output from 4a.identify-shockwaves.py")
    parser.add_argument("--view", choices=['east', 'north', 'south', 'west'], required=True)
    parser.add_argument("--mic_dist", type=float, default=0.15, help="Distance between L/R mics in meters")
    parser.add_argument("--temp_c", type=float, default=30.0)
    args = parser.parse_args()

    # Calculate speed of sound based on air temperature
    c_ms = 331.3 * math.sqrt(1 + args.temp_c / 273.15)
    
    df = pd.read_csv(args.csv)
    if df.empty:
        print("No shockwave data found in CSV.")
        return

    reconciled_data = []
    
    for _, row in df.iterrows():
        # 1. Get Local Angle relative to camera lens
        local_azimuth = calculate_azimuth(row['TDOA_ms'], args.mic_dist, c_ms)
        
        # 2. Translate based on camera's cardinal position (The -view argument)
        global_heading = map_to_global(local_azimuth, args.view)
        
        reconciled_data.append({
            "Time_s": row['Time_s'],
            "TDOA_ms": row['TDOA_ms'],
            "Local_Azimuth": round(local_azimuth, 2),
            "Global_Heading": round(global_heading, 2),
            "Confidence": row['Conf'],
            "View_Context": args.view
        })

    out_df = pd.DataFrame(reconciled_data)
    out_name = args.csv.replace("4a.identify-shockwaves", "4a.1.acoustic-azimuth-triangulation-reconciler")
    out_df.to_csv(out_name, index=False)

    print(f"--- Reconciler: Orientation for {args.view.upper()} View ---")
    print(out_df[['Time_s', 'Local_Azimuth', 'Global_Heading', 'Confidence']])
    print(f"\nForensic Note: Global Heading {out_df['Global_Heading'].iloc[0]}° suggests shooter is on this vector.")

if __name__ == "__main__":
    main()
