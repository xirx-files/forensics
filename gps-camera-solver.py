import cv2
import numpy as np

def solve_camera_location(world_points, image_points, img_size):
    """
    Estimates camera GPS (in metric grid) from 3+ landmarks.
    world_points: List of (x, y, 0) coordinates in meters.
    image_points: List of (u, v) pixel coordinates from the photo.
    img_size: (width, height) of the photo.
    """
    # 1. Define Intrinsic Camera Matrix (Guess if metadata is missing)
    # Assume focal length is roughly equal to image width
    focal_length = img_size[0]
    center = (img_size[0] / 2, img_size[1] / 2)
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]
    ], dtype="double")
    
    # Assume no lens distortion
    dist_coeffs = np.zeros((4, 1))

    # 2. Solve PnP
    # Note: solvePnP is more accurate with 4+ points, but works with 3
    success, rvec, tvec = cv2.solvePnP(
        np.array(world_points, dtype="double"),
        np.array(image_points, dtype="double"),
        camera_matrix,
        dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE
    )

    if not success:
        return None

    # 3. Convert Camera Pose to World Coordinates
    # solvePnP gives position of world origin in camera frame. 
    # We need position of camera in world frame.
    rmat, _ = cv2.Rodrigues(rvec)
    camera_position = -np.matrix(rmat).T * np.matrix(tvec)
    
    return camera_position # This returns [X, Y, Z] in meters

# EXAMPLE USAGE FOR ONE PHOTO
# Replace these with your actual 9 known landmark GPS converted to meters
landmarks_grid = {
    "tent_leg_1": [10.5, 20.0, 0],
    "speaker_pole_A": [45.2, -10.5, 0],
    "mic_stand": [0.0, 0.0, 0]
}

# Photo 1: Pixel coordinates of these three landmarks
photo1_pixels = [
    [450, 600],  # tent_leg_1
    [1200, 550], # speaker_pole_A
    [800, 900]   # mic_stand
]
photo1_world = [landmarks_grid["tent_leg_1"], landmarks_grid["speaker_pole_A"], landmarks_grid["mic_stand"]]

cam_coords = solve_camera_location(photo1_world, photo1_pixels, (1920, 1080))
print(f"Camera 1 Estimated World Position (X, Y): {cam_coords[0]}, {cam_coords[1]}")
