# Forensic Audit: 1.mp4
**Report Generated:** 2026-02-26 10:16:51
**Forensic Standard:** Locked Spec v2 (Ballistic-Kinematic Reconciliation)

## 1. PRIMARY SENSOR DATA
- **Reference T0 (v0):** 0.967s
- **Site Elevation:** 1402.79m (MSL)
- **Ambient Temp:** 30.0°C (c ≈ 349.03 m/s)
- **Camera GPS:** 40.27753, -111.71407224 (Baseline)

## 2. CHRONOLOGICAL EVENT AUDIT
The following timeline represents the validated sequence of physical and acoustic impulses.

|   Timestamp | Event                          | Details                                                                                                                                                                 |
|------------:|:-------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|      0.8667 | Shockwave Precursor            | Supersonic arrival (HF Ratio: 5881.36)                                                                                                                                  |
|      0.8973 | Shockwave Precursor            | Supersonic arrival (HF Ratio: 77.04)                                                                                                                                    |
|      0.9217 | Shockwave Precursor            | Supersonic arrival (HF Ratio: 366.55)                                                                                                                                   |
|      0.967  | Visual Impact (Event 0)        | Direct Kinetic Transfer. Origin: West (Behind)                                                                                                                          |
|      1.1255 | Acoustic: PETN_RIG_DETONATION  | Verdict: STAGED BALLISTIC EVENT. Non-causal delay of 158.5ms identified. Body moved at 0.967s, but PETN_RIG_DETONATION sound arrived at 1.1255s. Mimics 55.2m distance. |
|      1.267  | Visual Impact (Event 2)        | Kinetic Strike. Origin: West (Behind)                                                                                                                                   |
|      1.3094 | Acoustic: GENUINE_MUZZLE_BLAST | Verdict: REAL KINETIC EVENT. Causal delay of 42.4ms. Sharp decay (4.37) confirms a genuine muzzle blast at 14.8m.                                                       |

## 3. BALLISTIC DISCRIMINATION & VERDICT

### EVENT 01: STAGED BALLISTIC SIMULATION
- **Verification:** **FAIL** (Non-Causal Delay)
- **Acoustic Signature:** Acoustic: PETN_RIG_DETONATION
- **Calculated Range:** 55.20m
- **Geospatial Origin:** `40.27753, -111.71407224`
- **Expert Finding:** The 158.5ms interval between the kinetic impact (0.967s) and the acoustic impulse (1.1255s) represents a **synthetic delay**. Because the sound is classified as a PETN device (on-body), the 55m lag is mathematically incompatible with a direct-path discharge.

### EVENT 02: GENUINE KINETIC DISCHARGE
- **Verification:** **PASS** (Causal Time-of-Flight)
- **Acoustic Signature:** Acoustic: GENUINE_MUZZLE_BLAST
- **Calculated Range:** 14.76m
- **Geospatial Origin:** `40.27753, -111.71414302`
- **Expert Finding:** Physical causality confirmed. The 42.4ms lag between the visual strike (1.267s) and the muzzle blast (1.3094s) is consistent with a shooter located at a true range of 14.76m.

## 4. CONSOLIDATED GEOSPATIAL SUMMARY

| Target | Classification | Latitude | Longitude | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| Shot 1 | Staged (PETN) | 40.27753 | -111.71407224 | High (Logic Gap) |
| Shot 2 | Kinetic (Muzzle) | 40.27753 | -111.71414302 | High (Causal) |

***
**End of Audit: 1.mp4**
