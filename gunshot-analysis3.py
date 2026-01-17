import csv
import re

input_file = 'gunshot_flatness_analysis.txt'
output_file = 'gunshot_centroid_clean.csv'

# Regular expressions to find the timestamp and centroid values
time_re = re.compile(r'pts_time:(\d+\.\d+|\d+)')
centroid_re = re.compile(r'lavfi\.aspectralstats\.\d+\.centroid=(\d+\.\d+)')

data_rows = []

with open(input_file, 'r') as f:
    current_time = None
    frame_centroid_values = []
    
    for line in f:
        line = line.strip()
        
        # 1. Detect a new frame and extract the timestamp
        if 'pts_time:' in line:
            # If we already have data from a previous frame, save it first
            if current_time is not None and frame_centroid_values:
                avg_centroid = sum(frame_centroid_values) / len(frame_centroid_values)
                data_rows.append([current_time, avg_centroid])
            
            # Reset for the new frame
            time_match = time_re.search(line)
            current_time = time_match.group(1) if time_match else None
            frame_centroid_values = []
            
        # 2. Extract centroid values (one for each channel)
        flat_match = centroid_re.search(line)
        if flat_match:
            frame_centroid_values.append(float(flat_match.group(1)))

    # Save the final frame
    if current_time is not None and frame_centroid_values:
        avg_centroid = sum(frame_centroid_values) / len(frame_centroid_values)
        data_rows.append([current_time, avg_centroid])

# Write to CSV
with open(output_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Timestamp', 'centroid'])
    writer.writerows(data_rows)

print(f"Successfully processed {len(data_rows)} frames into {output_file}")
