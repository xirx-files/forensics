import pandas as pd
import json
import argparse
import math
import re

def project_gps(lat, lon, dist_m, bearing_deg):
    """Calculates new GPS point based on distance and bearing."""
    R = 6378137.0 # Earth Radius
    brng = math.radians(bearing_deg)
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    
    lat2 = math.asin(math.sin(lat1) * math.cos(dist_m/R) +
                    math.cos(lat1) * math.sin(dist_m/R) * math.cos(brng))
    lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(dist_m/R) * math.cos(lat1),
                             math.cos(dist_m/R) - math.sin(lat1) * math.sin(lat2))
    return math.degrees(lat2), math.degrees(lon2)

def extract_bearing(origin_str):
    """Extracts numerical bearing from strings like 'SW (227°)'."""
    match = re.search(r'\((\d+\.?\d*)°\)', str(origin_str))
    return float(match.group(1)) if match else None

def main():
    parser = argparse.ArgumentParser(description="Forensic Triangulation & Conclusion")
    parser.add_argument("--gpsConfig", required=True)
    parser.add_argument("--reconciled-csv", required=True, help="5.spatial-video-audio-reconciler.csv")
    parser.add_argument("--temp-c", type=float, default=30.0)
    parser.add_argument("--mic-spacing", type=float, default=0.06, help="Standard mobile mic distance (m)")
    args = parser.parse_args()

    # 1. Load Environment & Config
    with open(args.gpsConfig) as f: gps = json.load(f)
    c = 331.3 + 0.606 * args.temp_c
    cam_lat, cam_lon = gps['camera']['lat'], gps['camera']['lon']
    
    df = pd.read_csv(args.reconciled_csv)
    conclusions = []

    print(f"--- FINAL FORENSIC TRIANGULATION ---")
    print(f"Reference Camera: {cam_lat}, {cam_lon}")

    for i, row in df.iterrows():
        bearing = extract_bearing(row['Visual_Origin'])
        dist = row['Est_Dist_m']
        
        # A. TDOA Angular Resolution (Portrait = Vertical Plane)
        # theta = arcsin( (c * TDOA) / d_mic )
        tdoa_s = row['TDOA_ms'] / 1000.0
        try:
            # Elevation/Incidence angle relative to lens axis
            angle_off_axis = math.degrees(math.asin(max(-1, min(1, (c * tdoa_s) / args.mic_spacing))))
        except ZeroDivisionError:
            angle_off_axis = 0.0

        # B. Projected Origin Coordinate
        origin_lat, origin_lon = (None, None)
        if bearing is not None and dist > 0:
            origin_lat, origin_lon = project_gps(cam_lat, cam_lon, dist, bearing)

        # C. Confidence Scoring
        # Higher score if Mach Distance and Est Distance converge
        confidence = 50 # Base
        if row['Mach_Est_Dist_m'] > 0:
            variance = abs(row['Mach_Est_Dist_m'] - dist) / dist
            confidence = min(100, 100 - (variance * 100))

        conclusions.append({
            'Event': i,
            'Classification': row['Classification'],
            'A_Time': row['A_Time'],
            'Origin_Lat': origin_lat,
            'Origin_Lon': origin_lon,
            'Elevation_Angle': round(angle_off_axis, 2),
            'Conf_Score': round(confidence, 1)
        })

    # 2. Generate Forensic Narrative
    final_df = pd.DataFrame(conclusions)
    final_df.to_csv("5.triangulate-and-conclude-media-forensics.csv", index=False)
    
    with open("5.triangulate-and-conclude-media-forensics.txt", "w") as f:
        f.write("FORENSIC CONCLUSION REPORT\n")
        f.write("==========================\n\n")
        for _, c_row in final_df.iterrows():
            f.write(f"EVENT {c_row['Event']} [{c_row['Classification']}]:\n")
            f.write(f"- Time: {c_row['A_Time']}s\n")
            f.write(f"- Projected Location: {c_row['Origin_Lat']}, {c_row['Origin_Lon']}\n")
            f.write(f"- Acoustic Elevation (Portrait): {c_row['Elevation_Angle']}°\n")
            f.write(f"- Confidence: {c_row['Conf_Score']}%\n\n")

    print(f"Triangulation complete. Summary written to 5.triangulate-and-conclude-media-forensics.txt")

if __name__ == "__main__":
    main()
