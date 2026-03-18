# Consolidation Analysis

```bash
cd ../5.consolidation-analysis
```

## Reconciler Analysis

```bash
$ python ../../tools/5.ballistic-chain-reaction-reconciler.py --motion-csv ../3.video-analysis/3.identify-impact-events-motion-summary.csv --nature-csv ../4.audio-analysis/4.discern-nature-of-bang-segment-key-seq-audio-preferred-channel.wav.csv
```

```csv 5.ballistic-chain-reaction-reconciler.csv
Shot_ID,A_Time,Nature,Dist_m,Status,True_Range,Origin
1,1.1335,PETN_RIG_DETONATION,36.16,PROBABLE_STAGED_EVENT,0.0,W (258°)
2,1.3174,GENUINE_MUZZLE_BLAST,44.88,VERIFIED_STRIKE,44.88,SW (241°)
```
