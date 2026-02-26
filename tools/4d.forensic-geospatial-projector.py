import argparse
import pandas as pd
import math
import os
from pyproj import Geod

def main():
    parser = argparse.ArgumentParser(description="Forensic 3D Projector V13")
    parser.add_argument("--reconciled-csv", required=True)
    parser.add_argument("--cam-lat", type=float, required=True)
    parser.add_argument("--cam-lon", type=float, required=True)
    parser.add_argument("--cam-ele", type=float, required=True)
    parser.add_argument("--cam-bearing", type=float, default=270, help="West (Behind)")
    args = parser.parse_args()

    geod = Geod(ellps='WGS84')
    df = pd.read_csv(args.reconciled_csv)
    
    # Map the varied column names from different reconciler versions
    # We look for 'VERIFIED_STRIKE' or 'PRIMARY_STRIKE' or 'PROBABLE_STAGED_EVENT'
    valid_statuses = ['VERIFIED_STRIKE', 'PRIMARY_STRIKE', 'PROBABLE_STAGED_EVENT']
    
    # Identify the status column (handles 'Status' or 'Classification')
    status_col = 'Status' if 'Status' in df.columns else 'Classification'
    
    results = []
    # Project all confirmed primary events
    primaries = df[df[status_col].isin(valid_statuses)]

    for _, row in primaries.iterrows():
        # Use True_Range if available, else fallback to Dist_m
        r_val = row['True_Range'] if 'True_Range' in row and row['True_Range'] > 0 else row['Dist_m']
        
        # Calculate horizontal projection
        lon2, lat2, _ = geod.fwd(args.cam_lon, args.cam_lat, args.cam_bearing, r_val)
        
        results.append({
            "Shot_ID": row['Shot_ID'],
            "Nature": row.get('Nature', 'Unknown'),
            "Range_m": round(r_val, 2),
            "Lat": round(lat2, 8),
            "Lon": round(lon2, 8),
            "Alt_m": round(args.cam_ele, 2),
            "Forensic_Status": row[status_col]
        })

    out_df = pd.DataFrame(results)
    out_path = f"4d.final-map-coords-{os.path.basename(args.reconciled_csv)}"
    out_df.to_csv(out_path, index=False)
    
    print(f"--- V13 PROJECTOR SUCCESS ---")
    for r in results:
        print(f"Shot {r['Shot_ID']} ({r['Nature']}): {r['Lat']}, {r['Lon']} at {r['Range_m']}m")

if __name__ == "__main__":
    main()
