import math

def calculate_haversine(coord1, coord2):
    """
    Calculates the great-circle distance between two points 
    on the Earth in meters.
    """
    # Earth radius in meters
    R = 6371000 
    
    lat1, lon1 = map(math.radians, coord1)
    lat2, lon2 = map(math.radians, coord2)
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def main():
    # 1. Local array of feature labels
    labels = ["1.mp4", "2.MOV", "4.mp4", "13.mp4", 
              "16.mp4", "17.mp4", "12.mp4", "3.mp4", 
              "5.mp4", "6.mp4", "7.mp4", "8.mp4",

              "Subjec Mic", "Audience Mic", 
              "FL", "CL", "CR", "FR"]
    
    # 2. Local multi-dim array of GPS coordinates (Decimal Degrees)
    coords = [
        [40.2775366, -111.7139629],
        [40.2775, -111.7138],
        [40.2776284, -111.7135264],
        [40.2775244, -111.7139668],
        [40.2777484, -111.7140053],
        [40.2775749, -111.7140454],
        [40.2775221, -111.7135551],
        [40.2775581, -111.7138573],
        [40.2774731, -111.7138948],
        [40.2776030, -111.7137271],
        [40.2776557, -111.7140866],
        [40.2777456, -111.7139853],

        [40.2775277, -111.7140278],
        [40.2775405, -111.7139906],

        [40.2774964, -111.7139576], 
        [40.2775244, -111.7139802], 
        [40.2775541, -111.7140064],
        [40.2775742, -111.7140322]
    ]

    # Output Markdown Table Header
    print(f"| Connection | Distance (m) |")
    print(f"| :--- | :--- |")

    # Iterate through all unique combinations
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            dist = calculate_haversine(coords[i], coords[j])
            print(f"| {labels[i]} to {labels[j]} | {dist:.2f} m |")

if __name__ == "__main__":
    main()
