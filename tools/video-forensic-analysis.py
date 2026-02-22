import cv2
import numpy as np
import argparse
from pathlib import Path
from scipy.ndimage import gaussian_filter

def add_overlay_suffix(x):
    p = Path(x)
    # p.with_name replaces the entire filename (stem + suffix)
    # p.stem is 'hello' or 'test'
    return str(p.with_name(f"{p.stem}-kenetic-overlay.mp4"))

class ForensicEpicenterDetector:
    def __init__(self, output_dir: str = './'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def compute_features(self, flow):
        u, v = flow[..., 0], flow[..., 1]
        du_dx = np.gradient(u, axis=1)
        dv_dy = np.gradient(v, axis=0)
        divergence = du_dx + dv_dy
        kinetic_energy = 0.5 * (u**2 + v**2)
        return {'divergence': divergence, 'kinetic_energy': kinetic_energy}

    def detect_epicenter(self, flow):
        features = self.compute_features(flow)
        metric = gaussian_filter(features['divergence'], sigma=3) * \
                 np.sqrt(gaussian_filter(features['kinetic_energy'], sigma=3) + 1e-6)
        
        threshold = np.percentile(metric, 98)
        mask = metric > threshold
        if not np.any(mask): return None
        
        h, w = flow.shape[:2]
        yy, xx = np.mgrid[:h, :w]
        weights = metric[mask] / (np.sum(metric[mask]) + 1e-9)
        return np.sum(xx[mask] * weights), np.sum(yy[mask] * weights)

    def analyze_video(self, video_path: str, use_timestamp: bool, font_scale: float):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_path = str(self.output_dir / add_overlay_suffix(video_path))
        out = cv2.VideoWriter(out_path, fourcc, fps, (w, h))

        # 1. Insert Blank Zero Frame for Audio Sync (Frame 1 / 0.000000s)
        blank_frame = np.zeros((h, w, 3), dtype=np.uint8)
        sync_text = "0.000000" if use_timestamp else "Frame: 1"
        cv2.putText(blank_frame, f"SYNC: {sync_text}", (w//4, h//2), 
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 2)
        out.write(blank_frame)

        ret, prev_frame = cap.read()
        if not ret: return
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        
        frame_idx = 2 
        while True:
            ret, frame = cap.read()
            if not ret: break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            
            epicenter = self.detect_epicenter(flow)
            vis_frame = frame.copy()

            # Vector Overlay
            step = 20
            y, x = np.mgrid[step//2:h:step, step//2:w:step].reshape(2, -1).astype(int)
            fx, fy = flow[y, x].T
            for i in range(len(x)):
                cv2.arrowedLine(vis_frame, (x[i], y[i]), 
                                (int(x[i] + fx[i]), int(y[i] + fy[i])), 
                                (0, 255, 0), 1, tipLength=0.3)

            if epicenter:
                ex, ey = map(int, epicenter)
                cv2.drawMarker(vis_frame, (ex, ey), (0, 0, 255), cv2.MARKER_TILTED_CROSS, 30, 3)

            # Metadata Overlay Logic
            if use_timestamp:
                label = f"{ (frame_idx - 1) / fps:.6f}"
            else:
                label = f"Frame: {frame_idx}"
            
            cv2.putText(vis_frame, label, (20, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 255), 2)
            
            out.write(vis_frame)
            prev_gray = gray
            frame_idx += 1

        cap.release()
        out.release()
        print(f"Analysis complete: {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Forensic Kinetic Analysis")
    parser.add_argument("video", help="Path to input video")
    parser.add_argument("-i", "--index", action="store_true", help="Display Frame Index (Default)")
    parser.add_argument("-t", "--timestamp", action="store_true", help="Display Timestamp (x.yyyyyy)")
    parser.add_argument("-fs", "--fontScale", type=float, default=0.8, help="Font scale for overlay")
    
    args = parser.parse_args()
    
    # Default to index if timestamp isn't explicitly requested
    use_ts = args.timestamp
    
    detector = ForensicEpicenterDetector()
    detector.analyze_video(args.video, use_ts, args.fontScale)
