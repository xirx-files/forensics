import cv2
import numpy as np
import json

# Your "eyeball" estimate for the UVU courtyard scene
ESTIMATED_POS = np.array([3130, 1270, 120])

def solve_with_constraints(world_points, image_points, img_size, f_val):
    obj_pts = np.array(world_points, dtype=np.float64).reshape(-1, 3)
    img_pts = np.array(image_points, dtype=np.float64).reshape(-1, 2)
    
    width, height = img_size
    center = (width / 2, height / 2)
    camera_matrix = np.array([[f_val, 0, center[0]], [0, f_val, center[1]], [0, 0, 1]], dtype=np.float64)
    
    num_sol, rvecs, tvecs, errors = cv2.solvePnPGeneric(
        obj_pts, img_pts, camera_matrix, np.zeros((4, 1)), flags=cv2.SOLVEPNP_SQPNP
    )

    if num_sol > 0:
        valid_sols = []
        for i in range(num_sol):
            rmat, _ = cv2.Rodrigues(rvecs[i])
            pos = -np.matrix(rmat).T * np.matrix(tvecs[i])
            pos = np.array(pos).flatten()
            
            # Distance from your manual estimate to this solution
            dist_from_guess = np.linalg.norm(pos - ESTIMATED_POS)
            
            valid_sols.append({
                "pos": pos, 
                "error": errors[i][0], 
                "f": f_val, 
                "dist_diff": dist_from_guess
            })
        
        # Sort by lowest reprojection error
        return sorted(valid_sols, key=lambda x: x['error'])[0]
    return None

# [Loading logic for photo1_world, photo1_pixels remains same as previous]
# Load data
with open('camera-coords-query.json', 'r') as f:
    data = json.load(f)

landmarks_grid = data['wcs']
photo_data = data['photo']
img_size = (photo_data['width'], photo_data['height'])
photo1_pixels = []
photo1_world = []
for name, pixels in photo_data['points'].items():
    if name in landmarks_grid:
        photo1_pixels.append(pixels)
        photo1_world.append(landmarks_grid[name])

# Iterating while prioritizing your estimate
best_constrained = {"error": float('inf')}
for f in np.linspace(img_size[1]*1.5, img_size[1]*4.0, 400): # Start at 1.5x height for telephoto
    res = solve_with_constraints(photo1_world, photo1_pixels, img_size, f)
    # Only consider solutions within a reasonable radius of your estimate
    if res and res['dist_diff'] < 500: # 500mm/unit radius
        if res['error'] < best_constrained['error']:
            best_constrained = res

if best_constrained['error'] != float('inf'):
    p = best_constrained['pos']
    print(f"Verified Solution Found near {ESTIMATED_POS}:")
    print(f"   Optimized F: {best_constrained['f']:.2f} | Error: {best_constrained['error']:.2f}")
    print(f"   Final World Pos (X, Y, Z): {p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f}")
