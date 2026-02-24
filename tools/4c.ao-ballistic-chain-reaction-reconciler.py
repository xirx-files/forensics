import argparse
import numpy as np
import pandas as pd
import math
import os

def main():
    parser = argparse.ArgumentParser(description="AO Reconciler V12.1 - Temporal Guardrails")
    parser.add_argument("--muzzle-csv", required=True)
    parser.add_argument("--shockwave-csv", help="Optional 4a Shockwave data")
    parser.add_argument("--v0", type=float, required=True)
    parser.add_argument("--temp_c", type=float, default=28.33)
    args = parser.parse_args()

    c = 331.3 * math.sqrt(1 + args.temp_c / 273.15)
    df_muzzle = pd.read_csv(args.muzzle_csv)
    sw_df = pd.read_csv(args.shockwave_csv) if args.shockwave_csv else None
    
    results = []

    for idx, row in df_muzzle.iterrows():
        m_ts = row['A_Time']
        dist_m = (m_ts - args.v0) * c
        
        s_m_interval_ms = 0
        sw_status = "NONE_DETECTED"

        if sw_df is not None:
            # Look for shockwaves in the valid window (max 300ms before muzzle)
            valid_sw = sw_df[(sw_df['TS'] < m_ts) & (sw_df['TS'] > m_ts - 0.3)]
            if not valid_sw.empty:
                s_ts = valid_sw.iloc[-1]['TS']
                s_m_interval_ms = (m_ts - s_ts) * 1000
                sw_status = "SUPERSONIC_CONFIRMED"
            else:
                sw_status = "SUBSONIC_OR_NO_SW"

        results.append({
            "Shot_ID": idx + 1,
            "Muzzle_TS": round(m_ts, 4),
            "S_M_Interval_ms": round(s_m_interval_ms, 2),
            "Dist_m": round(dist_m, 2),
            "Ratio": row['Ratio'],
            "Classification": sw_status,
            "True_Range": round(dist_m, 2)
        })

    out_path = f"4c.ao-final-reconciled-report-{os.path.basename(args.muzzle_csv)}"
    pd.DataFrame(results).to_csv(out_path, index=False)
    print(f"--- AO-RECONCILER 12.1 SUCCESS ---")
    print(f"Shot 1: {results[0]['Classification']} | Shot 2: {results[1]['Classification']}")

if __name__ == "__main__":
    main()
