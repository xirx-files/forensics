import pandas as pd
import json
import argparse
import math

def calculate_speed_of_sound(temp_c):
    return 331.3 + 0.606 * temp_c

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpsConfig", required=True)
    parser.add_argument("--motion-summary-csv", required=True)
    parser.add_argument("--motion-detail-csv", required=True)
    parser.add_argument("--shockwave-csv", required=True)
    parser.add_argument("--bang-csv", required=True)
    parser.add_argument("--temp-c", type=float, default=30.0)
    args = parser.parse_args()

    # 1. Setup
    c = calculate_speed_of_sound(args.temp_c)
    with open(args.gpsConfig) as f: gps = json.load(f)
    
    # GT Distance Camera -> Target (Approx 5.95m)
    lat1, lon1 = gps['camera']['lat'], gps['camera']['lon']
    lat2, lon2 = gps['target']['lat'], gps['target']['lon']
    gt_dist = math.sqrt(((lon2-lon1)*91200)**2 + ((lat2-lat1)*111000)**2)

    # 2. Load & Filter 1-ORDER only
    b_df = pd.read_csv(args.bang_csv).query("Source_Type == '1-ORDER'")
    s_df = pd.read_csv(args.shockwave_csv).query("Type == '1-ORDER'")
    m_sum = pd.read_csv(args.motion_summary_csv)
    m_det = pd.read_csv(args.motion_detail_csv)

    # 3. Manual Causal Mapping (Based on your feedback)
    # Mapping indices based on the provided logs
    # Chain 1: ARC_FLASH (Bang 0) -> Summary 0
    # Chain 2: PETN (Bang 1) -> Shock 0 -> Summary 1
    # Chain 3: MUZZLE (Bang 2) -> Shock 1 -> Summary 2
    
    reconciled = []
    chains = [
        {"b_idx": 0, "s_idx": None, "m_idx": 0},
        {"b_idx": 1, "s_idx": 0,    "m_idx": 1},
        {"b_idx": 2, "s_idx": 1,    "m_idx": 2}
    ]

    for link in chains:
        bang = b_df.iloc[link['b_idx']]
        mot = m_sum.iloc[link['m_idx']]
        shock = s_df.iloc[link['s_idx']] if link['s_idx'] is not None else None
        
        # Pull high-res Origin from detail csv matching the summary V_Time
        origin_row = m_det.iloc[(m_det['V_Time'] - mot['V_Time']).abs().argsort()[:1]]
        v_origin = origin_row['Origin'].values[0] if not origin_row.empty else "UNKNOWN"

        # Corrected Distance Logic (Absolute Sound Flight Time)
        # flight_time = time sound took to reach camera from source
        flight_time = abs(bang['A_Time'] - mot['Onset_V_Time'])
        est_dist = flight_time * c
        
        # Mach Logic: lead time between Shock and Bang
        mach_dist = 0
        if shock is not None:
            # d = (c * delta_t) / (1 - 1/M); assuming M=2.0
            mach_dist = abs(bang['A_Time'] - shock['Time_s']) * c / 0.5

        reconciled.append({
            'Event_Type': bang['Classification'],
            'Shock_Time': shock['Time_s'] if shock is not None else None,
            'Onset_V_Time': mot['Onset_V_Time'],
            'Peak_V_Time': mot['V_Time'],
            'A_Time': bang['A_Time'],
            'TDOA_ms': shock['TDOA_ms'] if shock is not None else 0.0,
            'Visual_Origin': v_origin,
            'Est_Dist_m': round(est_dist, 3),
            'Dist_Error_m': round(est_dist - gt_dist, 3),
            'Mach_Est_Dist_m': round(mach_dist, 3),
            'Nature': mot['Nature']
        })

    pd.DataFrame(reconciled).to_csv("5.spatial-video-audio-reconciler.csv", index=False)
    print(f"Causal Chain Reconciled. GT Ref: {gt_dist:.2f}m")

if __name__ == "__main__":
    main()
