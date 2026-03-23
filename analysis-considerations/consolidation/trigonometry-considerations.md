please write the script for 6.triangulate-and-conclude-media-forensics.py

This script acts as the final forensic aggregator. It takes the reconciled data from all 17 files (or a single reference file) and projects the acoustic and visual findings onto a 3D geospatial plane. It specifically calculates TDOA Angular Elevation for your portrait-oriented footage and uses Spherical Trigonometry to determine the GPS coordinates of the origin of fire/impact.

import pandas as pdimport jsonimport argparseimport mathimport re
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
    parser.add_argument("--reconciled-csv", required=True, help="5.spatial-video-audio-reconciler.csv")
    parser.add_argument("--gpsConfig", required=True)
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
    final_df.to_csv("6.final-spatial-analysis.csv", index=False)
    
    with open("6.forensic-conclusion.txt", "w") as f:
        f.write("FORENSIC CONCLUSION REPORT\n")
        f.write("==========================\n\n")
        for _, c_row in final_df.iterrows():
            f.write(f"EVENT {c_row['Event']} [{c_row['Classification']}]:\n")
            f.write(f"- Time: {c_row['A_Time']}s\n")
            f.write(f"- Projected Location: {c_row['Origin_Lat']}, {c_row['Origin_Lon']}\n")
            f.write(f"- Acoustic Elevation (Portrait): {c_row['Elevation_Angle']}°\n")
            f.write(f"- Confidence: {c_row['Conf_Score']}%\n\n")

    print(f"Triangulation complete. Summary written to 6.forensic-conclusion.txt")
if __name__ == "__main__":
    main()

Key Logic Implementation:

* Vertical TDOA: Since your orientation is portrait, the script treats the TDOA_ms as a Vertical Elevation Angle (above/below the lens axis). This is crucial for verifying if the "Origin" was at ground level or an elevated position in the amphitheatre.
* Confidence Convergence: It compares the standard Est_Dist_m (Acoustic flight time) against the Mach_Est_Dist_m (Shockwave lead time). If they align, the confidence score increases, validating the supersonic nature of the event.
* Geospatial Projection: It uses the Haversine inverse formula to convert your visual bearings and distances into absolute GPS coordinates.

Next Steps: Since you have 17 files, you should run this script on the consolidated output of all reconciled CSVs to see if the projected GPS points cluster around a single sniper/trigger position.
Do you want to add a clustering algorithm (like DBSCAN) to automatically group these 17 projected origins into a single "Probable Shooter Location"?


https://share.google/aimode/isXbVS89pILHIzmiY

---