
import re

print("--- Running Regex Diagnostic ---")

# Define the file path and the regex
file_path = 'video-1.mp4/exec-instructions-1.mp4.md'
regex = r'ffmpeg -i .* -ss ([\d\.]+) '

# Read the content of the file
try:
    with open(file_path, 'r') as f:
        content = f.read()

    print(f"--- Content of {file_path} ---")
    print(repr(content)) # Use repr to see hidden characters
    print("--- End Content ---")

    # Perform the regex search
    match = re.search(regex, content)

    print(f"\n--- Regex Details ---")
    print(f"Regex: {repr(regex)}")
    print(f"Match object: {match}")
    if match:
        print(f"Match group 1: {match.group(1)}")
    else:
        print("No match found.")

except FileNotFoundError:
    print(f"Error: Could not find the file at {file_path}")

print("\n--- Diagnostic Complete ---")
