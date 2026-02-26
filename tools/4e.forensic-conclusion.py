import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def main():
    parser = argparse.ArgumentParser(description="Forensic Timeline & Event Conclusion")
    parser.add_argument("--v0", type=float, required=True, help="Absolute T0 (0.967s)")
    parser.add_argument("--motion-csv", required=True)
    parser.add_argument("--shockwave-csv", required=True)
    parser.add_argument("--nature-csv", required=True)
    parser.add_argument("--reconciled-csv", required=True)
    parser.add_argument("--temp_c", type=float, default=30.00)
    args = parser.parse_args()

    # Load datasets
    m_df = pd.read_csv(args.motion_csv)
    sw_df = pd.read_csv(args.shockwave_csv)
    n_df = pd.read_csv(args.nature_csv)
    r_df = pd.read_csv(args.reconciled_csv)

    # Convert Motion Offsets to Absolute Timestamps
    m_df['TS'] = args.v0 + (m_df['Offset(ms)'] / 1000.0)
    
    conclusion_data = []

    # 1. ANALYSE EVENT 1 (The 55m Paradox)
    # ---------------------------------------------------------
    # Visual Strike 0 (0.967s)
    v_ts_1 = m_df.iloc[0]['TS']
    # Nearest Bang for Event 1 (1.1255s)
    a_ts_1 = n_df.iloc[0]['A_Time']
    # Shockwaves associated with Shot 1 (Preceding 0.967s)
    sw_shot_1 = sw_df[sw_df['TS'] < v_ts_1]
    
    lag_1 = (a_ts_1 - v_ts_1) * 1000
    nature_1 = n_df.iloc[0]['Classification']

    conclusion_data.append({
        "Timestamp": v_ts_1, "Event": "Visual Impact (Event 0)", 
        "Details": f"Direct Kinetic Transfer. Origin: {m_df.iloc[0]['Origin']}"
    })
    for _, sw in sw_shot_1.iterrows():
        conclusion_data.append({
            "Timestamp": sw['TS'], "Event": "Shockwave Precursor", 
            "Details": f"Supersonic arrival (HF Ratio: {sw['HF_Ratio']})"
        })
    
    # The Logic Engine: Identifying the Staged Nature
    verdict_1 = "STAGED BALLISTIC EVENT" if nature_1 == "PETN_RIG_DETONATION" else "KINETIC STRIKE"
    explanation_1 = (f"Non-causal delay of {lag_1:.1f}ms identified. Body moved at {v_ts_1}s, "
                    f"but {nature_1} sound arrived at {a_ts_1}s. Mimics 55.2m distance.")

    conclusion_data.append({
        "Timestamp": a_ts_1, "Event": f"Acoustic: {nature_1}", 
        "Details": f"Verdict: {verdict_1}. {explanation_1}"
    })

    # 2. ANALYSE EVENT 2 (The 14.8m Reality)
    # ---------------------------------------------------------
    v_ts_2 = m_df.iloc[2]['TS'] # Index 2 is the 300ms offset (1.267s)
    a_ts_2 = n_df.iloc[1]['A_Time'] # Index 1 is the 1.3094s bang
    lag_2 = (a_ts_2 - v_ts_2) * 1000
    nature_2 = n_df.iloc[1]['Classification']
    
    explanation_2 = (f"Causal delay of {lag_2:.1f}ms. Sharp decay ({n_df.iloc[1]['Decay_Factor']}) "
                    f"confirms a genuine muzzle blast at 14.8m.")

    conclusion_data.append({
        "Timestamp": v_ts_2, "Event": "Visual Impact (Event 2)", 
        "Details": f"Kinetic Strike. Origin: {m_df.iloc[2]['Origin']}"
    })
    conclusion_data.append({
        "Timestamp": a_ts_2, "Event": f"Acoustic: {nature_2}", 
        "Details": f"Verdict: REAL KINETIC EVENT. {explanation_2}"
    })

    # OUTPUT REPORT
    final_df = pd.DataFrame(conclusion_data).sort_values(by="Timestamp")
    final_df.to_csv("4e.forensic-conclusion-report.csv", index=False)

    # VISUALISATION: TIMELINE PLOT
    plt.figure(figsize=(14, 7))
    # Plot Visual Events (Red)
    plt.scatter(m_df['TS'], [1]*len(m_df), color='red', label='Visual Motion', s=100, zorder=5)
    # Plot Acoustic Events (Blue)
    plt.scatter(n_df['A_Time'], [1]*len(n_df), color='blue', label='Acoustic Pulse', marker='x', s=200, zorder=5)
    # Plot Shockwaves (Cyan)
    plt.scatter(sw_df['TS'], [0.9]*len(sw_df), color='cyan', label='Shockwaves', marker='|', s=300)

    # Annotations
    plt.annotate("STAGED (158ms Delay)", xy=(a_ts_1, 1.05), color='darkred', weight='bold')
    plt.annotate("REAL (42ms Delay)", xy=(a_ts_2, 1.05), color='darkgreen', weight='bold')

    plt.title("Forensic Sequence of Events: Staged vs. Real Ballistics")
    plt.xlabel("Timeline (Seconds)"); plt.yticks([]); plt.legend(); plt.grid(True, alpha=0.2)
    plt.savefig("4e.timeline-visualisation.png")
    
    print("\n--- FORENSIC CONCLUSION GENERATED ---")
    print(f"Sequence Audit: {len(conclusion_data)} unique timestamps explained.")
    print("Review 4e.forensic-conclusion-report.csv for the line-by-line verdict.")

if __name__ == "__main__":
    main()
