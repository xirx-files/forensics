import argparse
import pandas as pd
import math
import os

def main():
    parser = argparse.ArgumentParser(description="AO Reconciler V12.3 - Staged Event Detection")
    parser.add_argument("--v0", type=float, required=True, help="Marker: Event reference point")
    parser.add_argument("--nature-csv", required=True, help="Output from 4b.discern-nature")
    parser.add_argument("--shockwave-csv", help="Optional 4a Shockwave data")
    parser.add_argument("--temp_c", type=float, default=30.00)
    args = parser.parse_args()

    c = 331.3 * math.sqrt(1 + args.temp_c / 273.15)
    nature_df = pd.read_csv(args.nature_csv)
    sw_df = pd.read_csv(args.shockwave_csv) if args.shockwave_csv else None
    
    results = []

    for idx, n_row in nature_df.iterrows():
        m_ts = n_row['A_Time']
        # Distance relative to v0 marker
        lag_ms = (m_ts - args.v0) * 1000
        dist_m = (lag_ms / 1000.0) * c
        
        # --- SHOCKWAVE & NATURE CORRELATION ---
        sw_status = "NONE"
        if sw_df is not None:
            valid_sw = sw_df[(sw_df['TS'] < m_ts) & (sw_df['TS'] > m_ts - 0.3)]
            if not valid_sw.empty:
                sw_status = "SUPERSONIC_PRECURSOR"

        # --- FORENSIC LOGIC: STAGED VS KINETIC ---
        nature = n_row['Classification']
        true_range = round(dist_m, 2)
        forensic_status = "VERIFIED_PRIMARY_PATH"

        # Rule 1: PETN with significant lag = Staged/Synchronised
        if nature == "PETN_RIG_DETONATION" and dist_m > 5.0:
            forensic_status = "STAGED_EVENT_SYNC_ERROR"
            # In a staged event, the 'True Range' of the shooter is technically 0 
            # (it's an on-body device), but we keep dist_m for the map offset.
        
        # Rule 2: Electrocution/PA Sim has no physical range
        elif "PA_SYSTEM" in nature or "ELECTROCUTION" in nature:
            forensic_status = "ARTIFICIAL_IMPULSE"
            true_range = 0.0

        results.append({
            "Shot_ID": idx + 1,
            "Muzzle_TS": round(m_ts, 4),
            "S_M_Interval_ms": n_row.get('S_M_Interval_ms', 0), # Legacy support
            "Nature": nature,
            "SW_Context": sw_status,
            "Dist_m": round(dist_m, 2),
            "Status": forensic_status,
            "True_Range": true_range,
            "Ratio": n_row['Muzzle_Ratio']
        })

    out_path = f"4c.ao-reconciled-{os.path.basename(args.nature_csv)}"
    pd.DataFrame(results).to_csv(out_path, index=False)
    print(f"V12.3: Reconciled {len(results)} events. Forensic Status: {forensic_status}")

if __name__ == "__main__":
    main()
