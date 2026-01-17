import csv
import re

input_file = 'gunshot_flatness_analysis.txt'
output_file = 'gunshot_spread_clean.csv'

# Regular expressions to find the timestamp and spread values
time_re = re.compile(r'pts_time:(\d+\.\d+|\d+)')
spread_re = re.compile(r'lavfi\.aspectralstats\.\d+\.spread=(\d+\.\d+)')

data_rows = []

with open(input_file, 'r') as f:
    current_time = None
    frame_spread_values = []
    
    for line in f:
        line = line.strip()
        
        # 1. Detect a new frame and extract the timestamp
        if 'pts_time:' in line:
            # If we already have data from a previous frame, save it first
            if current_time is not None and frame_spread_values:
                avg_spread = sum(frame_spread_values) / len(frame_spread_values)
                data_rows.append([current_time, avg_spread])
            
            # Reset for the new frame
            time_match = time_re.search(line)
            current_time = time_match.group(1) if time_match else None
            frame_spread_values = []
            
        # 2. Extract spread values (one for each channel)
        flat_match = spread_re.search(line)
        if flat_match:
            frame_spread_values.append(float(flat_match.group(1)))

    # Save the final frame
    if current_time is not None and frame_spread_values:
        avg_spread = sum(frame_spread_values) / len(frame_spread_values)
        data_rows.append([current_time, avg_spread])

# Write to CSV
with open(output_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Timestamp', 'spread'])
    writer.writerows(data_rows)

print(f"Successfully processed {len(data_rows)} frames into {output_file}")
