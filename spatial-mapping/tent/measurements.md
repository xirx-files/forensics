# Measurements for the "Prove Me Wrong" Tent

## Summary

| #  | Feature                                  | Editor Size (Pt) | Millimeters |  Ratio | Notes                  |
|----|------------------------------------------|------------------|-------------|--------|------------------------|
| 1  | East side view                           |                  |             |        |                        |
| 2  | Tent width                               | 1107.00          | 3961.80     | 3.58   |                        |
| 3  | Tent height                              | 738.00           | 2641.20     |        |                        |
| 4  | Banner height                            | 100.00           | 357.89      |        |                        |
| 5  |                                          |                  |             |        |                        |
| 6  | South side view                          |                  |             |        |                        |
| 7  | South side Tent width                    | 1218.00          | 3961.80     | 3.25   |                        |
| 8  | South side Tent height                   | 812.00           | 2641.20     |        |                        |
| 9  | North side Tent width                    | 605.00           | 3961.80     | 6.55   |                        |
| 10 | North side Tent height                   | 403.33           | 2641.20     |        |                        |
| 11 |                                          |                  |             |        |                        |
| 12 | South east side view                     |                  |             |        |                        |
| 13 | Tent height (wrt center)                 | 372.00           | 2641.20     | 7.10   |                        |
| 14 | Tent roof height (wrt center)            | 220.00           | 1562.00     |        | Preferred calculations |
| 15 |                                          |                  |             |        |                        |
| 16 |                                          |                  |             |        |                        |
| 17 | Elevated south side view                 |                  |             |        |                        |
| 18 | North side Tent height (wrt west facing) | 138.00           | 2641.20     | 19.14  |                        |
| 19 | HoF lower window height                  | 226.00           | 4325.44     |        |                        |
| 20 | Tent height (wrt center)                 | 143.00           | 2641.20     | 18.47  |                        |
| 21 | Tent roof height (wrt center)            | 83.00            | 1533.00     |        |                        |
| 22 |                                          |                  |             |        |                        |
| 23 | Tent + roof height                       |                  | 4203.20     |        |                        |

Table estimated measurements


| #  |                        | Editor Size (Pt)        | Millimeters |        |                  |  Ratio            | Base elevation (m) |
|----|------------------------|-------------------------|-------------|--------|------------------|-------------------|--------------------|
| 1  | Google Earth yardstick | 1102.00                 | 14700.00    |        |                  | 13.34             | 1401               |
| 2  |                        |                         |             |        |                  |                   |                    |
| 3  |                        | World-coordinate-system |             |        | Google-earth-GPS |                   |                    |
| 4  | Feature                | x                       | y           | z      | lat              | lon               | elevation          |
| 5  | North post             | 3181.00                 | 690.00      | 198.00 | 40.2775105023712 | -111.714059450445 | 1403.641198        |
| 6  | North-east post        | 3330.00                 | 690.00      | 198.00 | 40.2775266160513 | -111.714070000967 | 1403.641198        |
| 7  | East post              | 3330.00                 | 839.00      | 198.00 | 40.2775347506995 | -111.714049051243 | 1403.641198        |
| 8  | South-east post        | 3330.00                 | 988.00      | 198.00 | 40.2775428853477 | -111.714028101518 | 1403.641198        |
| 9  | South post             | 3181.00                 | 988.00      | 198.00 | 40.2775267716675 | -111.714017550996 | 1403.641198        |
| 10 | South-west post        | 3032.00                 | 988.00      | 198.00 | 40.2775106579874 | -111.714007000474 | 1403.641198        |
| 11 | West post              | 3032.00                 | 839.00      | 198.00 | 40.2775025233393 | -111.714027950199 | 1403.641198        |
| 12 | North-west post        | 3032.00                 | 690.00      | 198.00 | 40.2774943886911 | -111.714048899923 | 1403.641198        |

Table coordinate system cross-reference


```json tent-mapping.json
[
  {
    "Feature": "North post",
    "x": 3181.00,
    "y": 690.00
  },
  {
    "Feature": "North-east post",
    "x": 3330.00,
    "y": 690.00
  },
  {
    "Feature": "East post",
    "x": 3330.00,
    "y": 839.00
  },
  {
    "Feature": "South-east post",
    "x": 3330.00,
    "y": 988.00
  },
  {
    "Feature": "South post",
    "x": 3181.00,
    "y": 988.00
  },
  {
    "Feature": "South-west post",
    "x": 3032.00,
    "y": 988.00
  },
  {
    "Feature": "West post",
    "x": 3032.00,
    "y": 839.00
  },
  {
    "Feature": "North-west post",
    "x": 3032.00,
    "y": 690.00
  }
]
```

```bash
$ python ../tools/2.world-coordinate-system.py -v -m world-coordinate-system_to_gps_lamp-posts.json -i tent/tent-mapping.json -o tent/tent-mapping-out.json 
--- Mapping Model Status ---
RMSE: 0.00000129 Degrees
Approximate ground error: 0.143 meters
----------------------------
Successfully processed 8 entries to tent/tent-mapping-out.json
```

```json tent-mapping-out.json
[
    {
        "lat": 40.277510502371214,
        "lon": -111.714059450445
    },
    {
        "lat": 40.27752661605133,
        "lon": -111.714070000967
    },
    {
        "lat": 40.2775347506995,
        "lon": -111.7140490512427
    },
    {
        "lat": 40.277542885347664,
        "lon": -111.7140281015184
    },
    {
        "lat": 40.277526771667546,
        "lon": -111.7140175509964
    },
    {
        "lat": 40.27751065798743,
        "lon": -111.71400700047441
    },
    {
        "lat": 40.27750252333926,
        "lon": -111.71402795019871
    },
    {
        "lat": 40.27749438869109,
        "lon": -111.71404889992301
    }
]
```

## Process

1. Establish tent in context
2. Calculate banner sizes
3. Calculate tent height on the south side
4. Calculate tent roof top height
5. Calculate lower Hall of Flags building lower window

## 1. Stage overhead view
![stage-model.svg](../amphitheatre/stage-model.svg)
Figure stage-model.svg


### 2. East side view

![east-side-view-measurement.jpg](east-side-view-measurement.jpg)
Figure east-side-view-measurement.jpg


### 3. South side view

![south-side-view-measurement.jpg](south-side-view-measurement.jpg)
Figure south-side-view-measurement.jpg


### 4. South-East side view

![south-east-side-view-measurement.jpg](south-east-side-view-measurement.jpg)
Figure south-east-side-view-measurement.jpg


### 5. Elevated South side view

![elevated-south-side-view-measurement.jpg](elevated-south-side-view-measurement.jpg)
Figure elevated-south-side-view-measurement.jpg