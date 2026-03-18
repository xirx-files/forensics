# https://www.google.com/search?sourceid=chrome&udm=50&aep=42&q=write+a+python+script+which%3A%0A1.+accepts+a+%22world-coodinate-system_to_latlong_map.json%22+%28see+below%29+and+establishes+a+mapping+between+a+local+world+coordinate+system+and+actual+GPS+coordinate%0A2.+converts+the+%28X%2C+Y%29+entries+in+input.json+%28has+format+as+previous%29+to+%28lat%2C+long%29+entries+and+dump+as+output.json.+%0A3.+add+support+for+an+%22-r%22+cli+switch+to+reverse+the+direction+and+dump+%28x%2C+Y%29+from+the+%28lat%2C+long%29+input.+%0A4.+try+to+avoid+additional+python+library+dependencies&mstk=AUtExfAhDCC9bevZDGM-sNNftrpOuCsqXWRcsnccwqQZNUPs8CPHp0Jjp4SfTDmcIKRMPZCvIbX8nKouNiRtw2oSqCjhuKBD6lg2dFodj0PkLcKEjRN7mHqKvXYzMvdLlOsDvIZN2EEI-XzPIIgbV_vXObGzU0QJnTmh4JA&csuir=1&mtid=gIuKadLcIfmSseMPvafTyAk

import json
import argparse
import numpy as np
import sys
import matplotlib.pyplot as plt

def calculate_affine_transform(src_pts, dst_pts):
    # Augment source points: [x, y] -> [x, y, 1]
    A = np.c_[src_pts, np.ones(src_pts.shape[0])]
    
    # Solve for M in: A @ M.T = dst_pts
    # M_T will be (3, 2), so M will be (2, 3)
    M_T, _, _, _ = np.linalg.lstsq(A, dst_pts, rcond=None)
    
    predictions = A @ M_T
    errors = predictions - dst_pts
    rmse = np.sqrt(np.mean(np.sum(errors**2, axis=1)))
    
    return M_T.T, rmse, predictions

def visualize_errors(actual, predicted, labels):
    plt.figure(figsize=(10, 7))
    plt.scatter(actual[:, 1], actual[:, 0], c='blue', label='Actual GPS', zorder=3)
    plt.scatter(predicted[:, 1], predicted[:, 0], c='red', marker='x', label='Model Prediction', zorder=3)
    
    for i in range(len(actual)):
        plt.plot([actual[i, 1], predicted[i, 1]], [actual[i, 0], predicted[i, 0]], 'k--', alpha=0.3)
        plt.text(actual[i, 1], actual[i, 0], f" {labels[i]}", fontsize=8)

    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Coordinate Mapping Error Visualization')
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.gca().ticklabel_format(useOffset=False)
    plt.show()

def main():
    parser = argparse.ArgumentParser(description="Map World Coordinates to GPS.")
    parser.add_argument("-m", "--map_file", help="Path to mapping JSON")
    parser.add_argument("-i", "--input_file", help="Path to input JSON")
    parser.add_argument("-o", "--output_file", help="Path to output JSON", nargs='?', default="output.json")
    parser.add_argument("-r", "--reverse", action="store_true", help="Reverse: Lat/Lon -> X/Y")
    parser.add_argument("-v", "--visualize", action="store_true", help="Show visualization")
    args = parser.parse_args()

    try:
        with open(args.map_file, 'r') as f:
            mapping_data = json.load(f)
        with open(args.input_file, 'r') as f:
            input_data = json.load(f)
    except Exception as e:
        print(f"Error loading files: {e}")
        return

    # Extract reference points
    world_pts = np.array([[float(p['x']), float(p['y'])] for p in mapping_data])
    gps_pts = np.array([[float(p['lat']), float(p['lon'])] for p in mapping_data])
    labels = [p.get('Feature', f'Point {i}') for i, p in enumerate(mapping_data)]

    # 1. Calculate the Matrix
    if not args.reverse:
        M, rmse, preds = calculate_affine_transform(world_pts, gps_pts)
        src_keys, dst_keys = ['x', 'y'], ['lat', 'lon']
        unit = "Degrees"
    else:
        M, rmse, preds = calculate_affine_transform(gps_pts, world_pts)
        src_keys, dst_keys = ['lat', 'lon'], ['x', 'y']
        unit = "World Units"

    print(f"--- Mapping Model Status ---")
    print(f"RMSE: {rmse:.8f} {unit}")
    if not args.reverse:
        print(f"Approximate ground error: {rmse * 111000:.3f} meters")
    print("-" * 28)

    if args.visualize:
        visualize_errors(gps_pts if not args.reverse else world_pts, preds, labels)

    # 2. Transform the input data
    output_data = []
    for entry in input_data:
        # Create input vector [val1, val2, 1]
        try:
            v_in = np.array([float(entry[src_keys[0]]), float(entry[src_keys[1]]), 1.0])
            # v_out = M (2x3) @ v_in (3x1) = (2x1)
            v_out = M @ v_in
            
            output_data.append({
                dst_keys[0]: float(v_out[0]),
                dst_keys[1]: float(v_out[1])
            })
        except KeyError as e:
            print(f"Warning: Skipping entry, missing key {e}")

    with open(args.output_file, 'w') as f:
        json.dump(output_data, f, indent=4)
    
    print(f"Successfully processed {len(output_data)} entries to {args.output_file}")

if __name__ == "__main__":
    main()
