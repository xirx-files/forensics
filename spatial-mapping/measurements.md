# Measurements for Perspective-n-Point (PnP) pose computation


## Summary

 
Table measurements


## Process

1. Establish a 2D GPS map for the scope of the world with placemarks from Google Earth
2. Export 2D map view and map to local World Co-ordinate System
3. Cross reference placemarks to local coordinate system
4. Test mapping resolution

1. Set the z-axis origin (ie. 0 value) to the elevation of the lower-level courtyard (1401m)
2. Scale all heights for the z-axis of the local model coordinate system



## 1. World Co-ordinate System Map

![google-earth-uvu-2d-mapping.jpg](amphitheatre/google-earth-uvu-2d-mapping.jpg)

Figure google-earth-uvu-2d-mapping.jpg with cross referenced placemarks


## 2. Cross-Referenced Map
![world-coordinate-system-mapping.jpg](world-coordinate-system-mapping.jpg)

Figure Cross-referenced map with local coordinates


## 3. JSON configuration

```json world-coordinate-system_to_gps_base-placemarks.json
[
  {
    "Feature": "Hall of Flags Roof South-side",
    "x": "704",
    "y": "55",
    "lat": "40.277209",
    "lon": "-111.713974"
  },
  {
    "Feature": "Hall of Flags Roof North-side",
    "x": "7510",
    "y": "40",
    "lat": "40.277943",
    "lon": "-111.714458"
  },
  {
    "Feature": "Courtyard lower-level West-side hatch",
    "x": "3428",
    "y": "784",
    "lat": "40.277544",
    "lon": "-111.714064"
  },
  {
    "Feature": "Courtyard upper-level East-side",
    "x": "3297",
    "y": "3266",
    "lat": "40.277664",
    "lon": "-111.713705"
  },
  {
    "Feature": "Woodbury Building Roof West-side",
    "x": "1277",
    "y": "4092",
    "lat": "40.277494",
    "lon": "-111.713453"
  }
]
```

```json world-coordinate-system_to_gps_lamp-posts.json
[
  {
    "Feature": "HoF North lamp post",
    "x": "5287",
    "y": "1051",
    "lat": "40.277759",
    "lon": "-111.714159"
  },
  {
    "Feature": "HoF South lamp post",
    "x": "1348",
    "y": "1255",
    "lat": "40.277342",
    "lon": "-111.71385"
  },
  {
    "Feature": "Woodbury North lamp post",
    "x": "3421",
    "y": "3928",
    "lat": "40.277713",
    "lon": "-111.713622"
  },
  {
    "Feature": "Woodbury South lamp post",
    "x": "2164",
    "y": "2637",
    "lat": "40.277508",
    "lon": "-111.713713"
  },
  {
    "Feature": "Sorrensen North lamp post",
    "x": "6605",
    "y": "2175",
    "lat": "40.277961",
    "lon": "-111.714092"
  }
]
```

## 4. Test resolution of mapper

```json test-case-input.json
[
    {
        "Feature": "Water feature center square",
        "x": 3882, 
        "y": 1916
    },
    {
        "Feature": "Water feature lamp post",
        "x": 4476, 
        "y": 2823
    },
    {
        "Feature": "Subject Facing Point",
        "x": 3180, 
        "y": 4319
    }
]
```

```bash
$ python ../tools/2.world-coordinate-system.py -v -m world-coordinate-system_to_gps_lamp-posts.json -i test-case-input.json -o output.json 
--- Mapping Model Status ---
RMSE: 0.00000129 Degrees
Approximate ground error: 0.143 meters
----------------------------
Successfully processed 3 entries to output.json
```

```json output.json
[
    {
        "lat": 40.27765324578341,
        "lon": -111.71393670919618
    },
    {
        "lat": 40.27776700183629,
        "lon": -111.7138512434923
    },
    {
        "lat": 40.27770851931429,
        "lon": -111.7135491343376
    }
]
```


# References

1. https://docs.opencv.org/4.x/d5/d1f/calib3d_solvePnP.html