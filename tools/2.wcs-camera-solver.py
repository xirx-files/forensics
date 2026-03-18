import json
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import least_squares

def project(params, wcs_points, img_w, img_h):
    """Global projection function to map WCS to Pixels."""
    tx, ty, tz, pitch, yaw, roll, f = params
    
    # Rotation Matrices
    Rx = np.array([[1, 0, 0], [0, np.cos(pitch), -np.sin(pitch)], [0, np.sin(pitch), np.cos(pitch)]])
    Ry = np.array([[np.cos(yaw), 0, np.sin(yaw)], [0, 1, 0], [-np.sin(yaw), 0, np.cos(yaw)]])
    Rz = np.array([[np.cos(roll), -np.sin(roll), 0], [np.sin(roll), np.cos(roll), 0], [0, 0, 1]])
    R = Rz @ Ry @ Rx
    
    # Transform
    cam_points = (wcs_points - [tx, ty, tz]) @ R.T
    
    # Perspective divide (Z is depth)
    z = cam_points[:, 2]
    z[np.abs(z) < 1e-6] = 1e-6
    
    xs = (f * cam_points[:, 0] / z) + (img_w / 2)
    ys = (f * cam_points[:, 1] / z) + (img_h / 2)
    return np.column_stack([xs, ys])

def solve_camera_location(data_file):
    with open(data_file, 'r') as f:
        data = json.load(f)

    labels = sorted(data['wcs'].keys())
    points_wcs = np.array([data['wcs'][k] for k in labels])
    points_img = np.array([data['photo']['points'][k] for k in labels])
    img_w, img_h = data['photo']['width'], data['photo']['height']
    
    # Initial guess: Camera at X=3000, Y=1000, Z=0 looking 'up' the Z axis
    initial_guess = [3000, 1000, 0, 0, 0, 0, 1000]

    res = least_squares(
        lambda p: (project(p, points_wcs, img_w, img_h) - points_img).ravel(),
        initial_guess,
        loss='soft_l1',
        f_scale=15.0
    )

    # Print Results
    final_proj = project(res.x, points_wcs, img_w, img_h)
    errors = np.linalg.norm(final_proj - points_img, axis=1)
    
    print(f"Refined Camera Pos: {res.x[:3]}")
    for i, label in enumerate(labels):
        status = "OUTLIER" if errors[i] > 50 else "OK"
        print(f"Point {label}: {errors[i]:7.2f}px [{status}]")
        
    return data, res.x

def visualize_all(data, params):
    labels = sorted(data['wcs'].keys())
    points_wcs = np.array([data['wcs'][k] for k in labels])
    points_img = np.array([data['photo']['points'][k] for k in labels])
    img_w, img_h = data['photo']['width'], data['photo']['height']
    proj_pts = project(params, points_wcs, img_w, img_h)

    fig = plt.figure(figsize=(15, 7))

    # Subplot 1: 2D Image Overlay (The Swimlane View)
    ax1 = fig.add_subplot(1, 2, 1)
    ax1.set_xlim(0, img_w); ax1.set_ylim(img_h, 0)
    ax1.set_title("Photo-Space Alignment")
    ax1.scatter(points_img[:,0], points_img[:,1], c='red', label='Measured')
    ax1.scatter(proj_pts[:,0], proj_pts[:,1], edgecolors='blue', facecolors='none', s=100, label='Projected')
    for i, txt in enumerate(labels):
        ax1.annotate(txt, (points_img[i,0], points_img[i,1]))

    # Subplot 2: 3D WCS View
    ax2 = fig.add_subplot(1, 2, 2, projection='3d')
    ax2.set_title("World-Coordinate View")
    ax2.scatter(points_wcs[:,0], points_wcs[:,1], points_wcs[:,2], c='green')
    ax2.scatter(params[0], params[1], params[2], c='magenta', s=100, marker='^', label='Camera')
    ax2.set_xlabel('X'); ax2.set_ylabel('Y'); ax2.set_zlabel('Z')
    
    plt.legend()
    plt.show()

if __name__ == "__main__":
    # data, best_params = solve_refined_camera('camera-coords-query.json') # solve_camera_location('camera-coords-query.json') #
    data, best_params = solve_camera_location('camera-coords-query.json')
    visualize_all(data, best_params)
