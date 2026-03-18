import subprocess
import argparse
import sys

def verify_crop_integrity(original_mkv, cropped_mkv, crop_string):
    """
    Compares the original (cropped on-the-fly) to the processed crop.
    PSNR 'inf' means they are mathematically identical.
    """
    print(f"--- Forensic Crop Integrity Audit ---")
    print(f"Target Crop: {crop_string}")
    
    # ffmpeg compares two inputs. We crop the original to match the 2nd input.
    # psnr filter outputs results to stderr.
    cmd = [
        "ffmpeg", "-i", original_mkv, "-i", cropped_mkv,
        "-filter_complex", f"[0:v]{crop_string}[orig_cropped];[orig_cropped][1:v]psnr",
        "-f", "null", "-"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Forensic Check: In FFV1 lossless, PSNR must be 'inf' (infinite)
    if "average:inf" in result.stderr.lower():
        print("✓ SUCCESS: Crop is mathematically LOSSLESS.")
        print("Result: PSNR = Infinite (0.0 MSE)")
        return True
    else:
        print("✗ FAILURE: Pixel data has been altered during cropping.")
        # Extract the actual PSNR value for the report
        for line in result.stderr.splitlines():
            if "PSNR" in line: print(f"Actual {line}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--orig", required=True, help="Full-frame MKV (key-seq-video.mkv)")
    parser.add_argument("--crop_file", required=True, help="Cropped MKV (key-seq-video-cropped.mkv)")
    parser.add_argument("--params", default="crop=350:520:0:940", help="Crop parameters used")
    args = parser.parse_args()

    if not verify_crop_integrity(args.orig, args.crop_file, args.params):
        sys.exit(1)
