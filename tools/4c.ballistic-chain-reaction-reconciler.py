import argparse
import pandas as pd
import math
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--v0", type=float, required=True)
    parser.add_argument("--nature-csv", required=True, help="4b.discern-nature output")
    parser.add_argument("--motion-csv", required=True)
    parser.add_argument("--temp_c", type=float, default=30.00)
    args = parser.parse_args()

    c = 331.3 * math.sqrt(1 + args.temp_c / 273.15)
    nature_df = pd.read_csv(args.nature_csv)
    motion_df = pd.read_csv(args.motion_csv)
    
    results = []
    for _, n_row in nature_df.iterrows():
        a_time = n_row['A_Time']
        
        # Match to nearest visual strike
        motion_df['Abs_TS'] = args.v0 + (motion_df['Offset(ms)'] / 1000.0)
        match = motion_df[(motion_df['Abs_TS'] <= a_time)].tail(1)
        
        if not match.empty:
            m_ts = match.iloc[0]['Abs_TS']
            lag_ms = (a_time - m_ts) * 1000
            dist_m = (lag_ms / 1000.0) * c
            
            # Forensic Integrity Check
            if n_row['Classification'] == 'PETN_RIG_DETONATION' and dist_m > 5:
                status = "PROBABLE_STAGED_EVENT"
                true_range = 0 # Sound and impact are co-located
            else:
                status = "VERIFIED_STRIKE"
                true_range = round(dist_m, 2)

            results.append({
                "Shot_ID": len(results) + 1,
                "A_Time": a_time,
                "Nature": n_row['Classification'],
                "Dist_m": round(dist_m, 2),
                "Status": status,
                "True_Range": true_range,
                "Origin": match.iloc[0]['Origin']
            })

    out_path = f"4c.reconciled-{os.path.basename(args.nature_csv)}"
    pd.DataFrame(results).to_csv(out_path, index=False)
    print(f"V12.2 Reconciler: Staged vs Kinetic differentiation complete.")

if __name__ == "__main__":
    main()
