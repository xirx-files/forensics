import csv
import re

input_file = 'event-spectral-stats.txt'
output_file = 'event-centroid-peak-levl-db.csv'

# Regular expressions for timestamp, centroid, and peak amplitude
time_re = re.compile(r'pts_time:(\d+\.\d+|\d+)')
centroid_re = re.compile(r'lavfi\.aspectralstats\.\d+\.centroid=(\d+\.\d+)')
# This regex captures peak level (e.g., lavfi.astats.1.Peak_level=-3.010300)
peak_re = re.compile(r'lavfi\.astats\.\d+\.Peak_level=(-?\d+\.\d+)')

data_rows = []

with open(input_file, 'r') as f:
    current_time = None
    frame_centroid_values = []
    frame_peak_values = []
    
    for line in f:
        line = line.strip()
        
        # 1. Detect a new frame and extract the timestamp
        if 'pts_time:' in line:
            if current_time is not None and (frame_centroid_values or frame_peak_values):
                avg_centroid = sum(frame_centroid_values) / len(frame_centroid_values) if frame_centroid_values else 0
                # Use max peak amplitude across channels for onset detection
                max_peak = max(frame_peak_values) if frame_peak_values else -99.0
                data_rows.append([current_time, avg_centroid, max_peak])
            
            time_match = time_re.search(line)
            current_time = time_match.group(1) if time_match else None
            frame_centroid_values = []
            frame_peak_values = []
            
        # 2. Extract centroid values
        c_match = centroid_re.search(line)
        if c_match:
            frame_centroid_values.append(float(c_match.group(1)))

        # 3. Extract peak amplitude values
        p_match = peak_re.search(line)
        if p_match:
            frame_peak_values.append(float(p_match.group(1)))

    # Save the final frame
    if current_time is not None and (frame_centroid_values or frame_peak_values):
        avg_centroid = sum(frame_centroid_values) / len(frame_centroid_values) if frame_centroid_values else 0
        max_peak = max(frame_peak_values) if frame_peak_values else -99.0
        data_rows.append([current_time, avg_centroid, max_peak])

# Write to CSV
with open(output_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Timestamp', 'centroid', 'peak_level_db'])
    writer.writerows(data_rows)

print(f"Successfully processed {len(data_rows)} frames into {output_file}")
