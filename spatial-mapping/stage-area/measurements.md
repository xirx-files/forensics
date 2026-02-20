# Measurements for the stage area

## Summary

| #  | Feature                                     | Editor Size (Pt) | Millimeters |  Ratio | Notes                                         |
|----|---------------------------------------------|------------------|-------------|--------|-----------------------------------------------|
| 1  | South side view                             |                  |             |        |                                               |
| 2  | Tent height (south side)                    | 812.00           | 2641.20     | 3.25   |                                               |
| 3  | Barricade height (south side)               | 323.00           | 1118.00     | 3.46   |                                               |
| 4  | Center south speaker height                 | 685.00           | 2370.99     |        |                                               |
| 5  | Tent height (north side)                    | 403.33           | 2641.20     | 6.55   |                                               |
| 6  | Barricade height (north side)               | 161.00           | 1118.00     | 6.94   |                                               |
| 7  | Center north speaker height                 | 370.00           | 2569.32     |        |                                               |
| 8  | Center south speaker tripod base            | 257.00           | 889.55      |        | Use AVG                                       |
| 9  | Center north speaker tripod base            | 130.00           | 902.73      |        | 897.19                                        |
| 10 | Tent width (south side)                     | 1218.00          | 3961.80     | 3.25   |                                               |
| 11 | Center south speaker setfront               | 500.00           | 1626.35     |        |                                               |
| 12 | Tent width (north side)                     | 605.00           | 3961.80     | 6.55   |                                               |
| 13 | Center north speaker setfront               | 216.00           | 1414.46     |        |                                               |
| 14 | Tent width (b/n north/south)                | 873.00           | 3961.80     | 4.54   |                                               |
| 15 | Audience microphone setfront                | 252.00           | 1143.61     |        |                                               |
| 16 | Barricade height (near mic)                 | 222.00           | 1118.00     | 5.04   |                                               |
| 17 | Audience microphone stand                   | 272.00           | 1369.80     |        | Need to cross reference with a pre-bang event |
| 18 |                                             |                  |             |        |                                               |
| 19 | Center south speaker facing north east view |                  |             |        |                                               |
| 20 | Barricade height (north side)               | 311.00           | 1118.00     | 3.59   | Using standard height of barricade            |
| 21 | Center south speaker tripod base            | 250.00           | 898.71      |        | Use AVG                                       |
| 22 | Center south speaker height                 | 657.00           | 2361.82     |        | 2366.41                                       |
| 23 | Barricade height (south side)               | 467.00           | 1118.00     | 2.39   |                                               |
| 24 | South speaker tripod base                   | 375.00           | 897.75      |        |                                               |
| 25 | South speaker height                        | 1237.00          | 2961.38     |        |                                               |
| 26 |                                             |                  |             |        |                                               |
| 27 | North speaker facing south west view        |                  |             |        |                                               |
| 28 | Speaker tripod base                         | 155.00           | 897.19      | 5.79   | using height from previous calc               |
| 29 | North speaker height                        | 472.00           | 2732.08     |        |                                               |
| 30 |                                             |                  |             |        |                                               |
| 31 | Central speakers facing north east view     |                  |             |        |                                               |
| 32 | Barricade height (north side)               | 166.00           | 1118.00     | 6.73   |                                               |
| 33 | Speaker tripod base                         | 134.00           | 897.19      | 6.70   | Use AVG                                       |
| 34 | Center north speaker height                 | 365.00           | 2458.25     |        | 2513.78                                       |
| 35 |                                             |                  |             |        |                                               |
| 36 | South speaker facing south view             |                  |             |        |                                               |
| 37 | barricade height                            | 351.00           | 1118.00     | 3.19   | Use AVG                                       |
| 38 | South speaker height                        | 927.00           | 2952.67     |        | 2957.02                                       |

Table estimated measurements



| # |                           | P-n-P                   | Millimeters |        |                  |  Ratio            | Base elevation (m) |
|---|---------------------------|-------------------------|-------------|--------|------------------|-------------------|--------------------|
| 1 | Google Earth yardstick    | 1102.00                 | 14700.00    |        |                  | 13.34             | 1401               |
| 2 |                           |                         |             |        |                  |                   |                    |
| 3 |                           | World-coordinate-system |             |        | Google-earth-GPS |                   |                    |
| 4 | Feature                   | x                       | y           | z      | lat              | lon               | elevation          |
| 5 | North speaker             | 3533.00                 | 950.00      | 204.81 | 40.2775627642768 | -111.714047818602 | 1403.732083        |
| 6 | Center north speaker      | 3316.00                 | 1084.00     | 188.45 | 40.2775466124262 | -111.714013612385 | 1403.513785        |
| 7 | Center south speaker      | 3025.00                 | 1110.00     | 177.40 | 40.2775165615533 | -111.713989351347 | 1403.366405        |
| 8 | South speaker             | 2763.00                 | 1142.00     | 221.68 | 40.2774899744697 | -111.713966300153 | 1403.957025        |
| 9 | Audience microphone stand | 3181.00                 | 1074.00     | 102.69 | 40.2775314668336 | -111.714005459209 | 1402.369802        |

Table coordinate system cross-reference

```json stage-area-mapping.json
[
    {
        "Feature": "North speaker",
        "x": 3533.00, 
        "y": 950.00
    },
    {
        "Feature": "Center north speaker",
        "x": 3316.00, 
        "y": 1084.00
    },
    {
        "Feature": "Center south speaker",
        "x": 3025.00, 
        "y": 1110.00
    },
    {
        "Feature": "South speaker",
        "x": 2763.00, 
        "y": 1142.00
    },
    {
        "Feature": "CK microphone",
        "x": 3180.00, 
        "y": 873.00
    },
    {
        "Feature": "Audience microphone stand",
        "x": 3181.00, 
        "y": 1074.00
    }
]
```

```bash
$ python ../tools/world-coordinate-system.py -v world-coordinate-system_to_gps_lamp-posts.json stage-area/stage-area-mapping.json  stage-area/stage-area-mapping-out.json 
--- Mapping Model Status ---
RMSE: 0.00000129 Degrees
Approximate ground error: 0.143 meters
----------------------------
Successfully processed 6 entries to stage-area/stage-area-mapping-out.json
```

```json stage-area-mapping-out.json
[
    {
        "lat": 40.27756276427676,
        "lon": -111.7140478186022
    },
    {
        "lat": 40.27754661242621,
        "lon": -111.71401361238523
    },
    {
        "lat": 40.2775165615533,
        "lon": -111.71398935134677
    },
    {
        "lat": 40.277489974469745,
        "lon": -111.71396630015255
    },
    {
        "lat": 40.277520385102314,
        "lon": -111.71403364943782
    },
    {
        "lat": 40.2775314668336,
        "lon": -111.71400545920922
    }
]
```

## Process

1. Calculate barricade height
2. Calculate speaker tripod stand height
3. Calculate central north, south speaker heights & audience microphone stand height
4. Calculate north & south speaker heights


## 1. Stage overhead view
![stage-model.svg](../amphitheatre/stage-model.svg)
Figure stage-model.svg


### 2. South side view
![south-side-view-measurement.jpg](south-side-view-measurement.jpg)
Figure south-side-view-measurement.jpg


### 3. Center south speaker facing north east view
![center-south-speaker-facing-north-east-view-measurement.jpg](center-south-speaker-facing-north-east-view-measurement.jpg)
Figure center-south-speaker-facing-north-east-view-measurement.jpg


### 4. North speaker facing south west view

![north-speaker-facing-south-west-view-measurement.jpg](north-speaker-facing-south-west-view-measurement.jpg)
Figure north-speaker-facing-south-west-view-measurement.jpg


### 5. Central speakers facing north east view

![central-speakers-facing-north-east-view-measurement.jpg](central-speakers-facing-north-east-view-measurement.jpg)
Figure central-speakers-facing-north-east-view-measurement.jpg


### 6. South speaker facing south view

![south-speaker-facing-south-view-measurement.jpg](south-speaker-facing-south-view-measurement.jpg)
Figure south-speaker-facing-south-view-measurement.jpg

