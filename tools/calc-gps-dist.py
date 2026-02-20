import json
import csv
import argparse
import math
from geopy.distance import geodesic

def calculate_3d_distance(p1, p2):
    # Horizontal distance (meters) using WGS-84 ellipsoid
    horizontal_dist = geodesic((p1['lat'], p1['lon']), (p2['lat'], p2['lon'])).meters
    # Vertical distance (meters)
    vertical_dist = p1['ele'] - p2['ele']
    # 3D Straight-line distance via Pythagorean theorem
    return math.sqrt(horizontal_dist**2 + vertical_dist**2)

def main():
    parser = argparse.ArgumentParser(description='Calculate 3D distances between two sets of GPS features.')
    parser.add_argument('-from', dest='from_file', required=True, help='Source JSON file')
    parser.add_argument('-to', dest='to_file', required=True, help='Target JSON file')
    parser.add_argument('-out', dest='out_file', required=True, help='Output CSV file')
    args = parser.parse_args()

    with open(args.from_file, 'r') as f:
        from_data = json.load(f)
    with open(args.to_file, 'r') as f:
        to_data = json.load(f)

    results = []

    for f1 in from_data:
        for f2 in to_data:
            dist_3d = calculate_3d_distance(f1, f2)
            results.append({
                'From_Feature': f1['Feature'],
                'To_Feature': f2['Feature'],
                'Distance_Meters': round(dist_3d, 3),
                'Lat_1': f1['lat'], 
                'Lon_1': f1['lon'],
                'Ele_1': f1['ele'],  # Added elevation
                'Lat_2': f2['lat'], 
                'Lon_2': f2['lon'],
                'Ele_2': f2['ele']   # Added elevation
            })

    if not results:
        print("No data processed.")
        return

    # Extract header from the first result item
    keys = results[0].keys()
    with open(args.out_file, 'w', newline='') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(results)

    print(f"Successfully processed {len(results)} pairs. Output saved to {args.out_file}")

if __name__ == "__main__":
    main()
