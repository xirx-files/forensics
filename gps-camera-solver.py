import cv2
import numpy as np
import json

def solve_camera_location(world_points, image_points, img_size):
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

    success, rvec, tvec = cv2.solvePnP(
        obj_pts, 
        img_pts, 
        camera_matrix, 
        dist_coeffs, 
        flags=cv2.SOLVEPNP_SQPNP
    )

    if not success:
        return None

    rmat, _ = cv2.Rodrigues(rvec)
    camera_position = -np.matrix(rmat).T * np.matrix(tvec)
    
    return np.array(camera_position).flatten()

# Load data from JSON file
with open('camera-coords-query.json', 'r') as f:
    data = json.load(f)

# Extracting values from JSON
landmarks_grid = data['landmarks_grid']
photo_data = data['photo1']
img_size = (photo_data['width'], photo_data['height'])

# Align world points with the order of pixel points provided in the JSON
photo1_pixels = []
photo1_world = []

for landmark_name, pixels in photo_data['points'].items():
    if landmark_name in landmarks_grid:
        photo1_pixels.append(pixels)
        photo1_world.append(landmarks_grid[landmark_name])

# Run Solver
cam_coords = solve_camera_location(photo1_world, photo1_pixels, img_size)

if cam_coords is not None:
    print(f"Camera Estimated World Position (X, Y, Z): {cam_coords[0]:.2f}, {cam_coords[1]:.2f}, {cam_coords[2]:.2f}")
else:
    print("PnP Solver failed to find a solution.")
