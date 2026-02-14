import cv2
import numpy as np
import json

def solve_camera_location_generic(world_points, image_points, img_size):
    obj_pts = np.array(world_points, dtype=np.float64).reshape(-1, 3)
    img_pts = np.array(image_points, dtype=np.float64).reshape(-1, 2)
    
    width, height = img_size
    focal_length = width 
    center = (width / 2, height / 2)
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]
    ], dtype=np.float64)
    
    dist_coeffs = np.zeros((4, 1))

    # solvePnPGeneric returns (number_of_solutions, rvecs, tvecs, errors)
    # Using SQPNP for best results with 3+ points
    num_sol, rvecs, tvecs, errors = cv2.solvePnPGeneric(
        obj_pts, 
        img_pts, 
        camera_matrix, 
        dist_coeffs, 
        flags=cv2.SOLVEPNP_SQPNP
    )

    if num_sol == 0:
        return None

    results = []
    for i in range(num_sol):
        rmat, _ = cv2.Rodrigues(rvecs[i])
        camera_position = -np.matrix(rmat).T * np.matrix(tvecs[i])
        results.append({
            "pos": np.array(camera_position).flatten(),
            "error": errors[i][0]
        })
    
    # Sort results by reprojection error (lowest first)
    return sorted(results, key=lambda x: x['error'])

# Load data
with open('camera-coords-query.json', 'r') as f:
    data = json.load(f)

landmarks_grid = data['landmarks_grid']
photo_data = data['photo1']
img_size = (photo_data['width'], photo_data['height'])

photo1_pixels = []
photo1_world = []

for landmark_name, pixels in photo_data['points'].items():
    if landmark_name in landmarks_grid:
        photo1_pixels.append(pixels)
        photo1_world.append(landmarks_grid[landmark_name])

print(f"Using {len(photo1_world)} landmarks for forensic analysis...")

solutions = solve_camera_location_generic(photo1_world, photo1_pixels, img_size)

if solutions:
    for idx, sol in enumerate(solutions):
        p = sol['pos']
        print(f"Solution {idx+1} (Error: {sol['error']:.4f}):")
        print(f"   Camera World Pos (X, Y, Z): {p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f}\n")
else:
    print("Solver failed to find a solution.")
