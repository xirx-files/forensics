import argparse
import pandas as pd
import math
import os
from pyproj import Geod

def main():
    parser = argparse.ArgumentParser(description="Forensic Geospatial Projector V12")
    parser.add_argument("--reconciled-csv", required=True)
    parser.add_argument("--cam-lat", type=float, required=True)
    parser.add_argument("--cam-lon", type=float, required=True)
    parser.add_argument("--cam-ele", type=float, required=True, help="1402.79m for this site")
    parser.add_argument("--cam-bearing", type=float, default=270, help="Azimuth to shooter")
    args = parser.parse_args()

    geod = Geod(ellps='WGS84')
    df = pd.read_csv(args.reconciled_csv)
    
    results = []
    # Project only Primary Strikes (Actual Shooter Locations)
    primaries = df[df['Classification'] == 'PRIMARY_STRIKE']

    for _, row in primaries.iterrows():
        # Calculate GPS: travel True_Range from Cam along Bearing
        lon2, lat2, _ = geod.fwd(args.cam_lon, args.cam_lat, args.cam_bearing, row['True_Range'])
        
        results.append({
            "Shot_ID": row['Shot_ID'],
            "Dist_m": row['True_Range'],
            "Lat": round(lat2, 8),
            "Lon": round(lon2, 8),
            "Alt_m": args.cam_ele,
            "S_M_Interval": row.get('S_M_Interval_ms', "N/A"),
            "Ratio": row['Ratio']
        })

    out_df = pd.DataFrame(results)
    out_path = f"4d.final-world-map-{os.path.basename(args.reconciled_csv)}"
    out_df.to_csv(out_path, index=False)
    
    print(f"--- 4D GEOSPATIAL PROJECTOR SUCCESS ---")
    print(f"Map coordinates generated for {len(results)} shooter candidates.")

if __name__ == "__main__":
    main()
