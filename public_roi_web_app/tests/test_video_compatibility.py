"""
Test Video File Compatibility with OpenCV
This script checks if your video file can be opened by OpenCV.
"""

import cv2
import os
import sys

def test_video_file(video_path):
    """Test if a video file can be opened by OpenCV"""
    
    print("\n" + "=" * 70)
    print("VIDEO FILE COMPATIBILITY CHECKER")
    print("=" * 70)
    
    # Check if file exists
    if not os.path.exists(video_path):
        print(f"❌ ERROR: File not found: {video_path}")
        return False
    
    # Get file info
    file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
    file_ext = os.path.splitext(video_path)[1].lower()
    
    print(f"\nFile Information:")
    print(f"  Path: {video_path}")
    print(f"  Name: {os.path.basename(video_path)}")
    print(f"  Format: {file_ext}")
    print(f"  Size: {file_size:.2f} MB")
    
    # Try to open with OpenCV
    print(f"\nTesting OpenCV compatibility...")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"❌ FAILED: OpenCV cannot open this file")
        print(f"\n" + "-" * 70)
        print("SOLUTIONS:")
        print("-" * 70)
        
        if file_ext == '.mkv':
            print("\n1. Convert MKV to MP4 (RECOMMENDED):")
            print("   Using FFmpeg:")
            output_name = video_path.replace('.mkv', '_converted.mp4')
            print(f"   ffmpeg -i \"{video_path}\" -c:v libx264 -c:a aac \"{output_name}\"")
            print(f"\n   Or use online converters like CloudConvert or Convertio")
            
        print("\n2. Install K-Lite Codec Pack (Windows):")
        print("   Download from: https://codecguide.com/download_kl.htm")
        print("   This adds codec support to Windows and OpenCV")
        
        print("\n3. Rebuild OpenCV with FFmpeg support:")
        print("   pip uninstall opencv-python")
        print("   pip install opencv-python-headless")
        
        cap.release()
        return False
    
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    codec = int(cap.get(cv2.CAP_PROP_FOURCC))
    
    # Decode codec
    codec_str = "".join([chr((codec >> 8 * i) & 0xFF) for i in range(4)])
    
    print(f"✅ SUCCESS: OpenCV can open this file!")
    print(f"\nVideo Properties:")
    print(f"  Resolution: {width} x {height}")
    print(f"  FPS: {fps:.2f}")
    print(f"  Total Frames: {frame_count}")
    print(f"  Duration: {duration:.2f} seconds")
    print(f"  Codec: {codec_str}")
    
    # Try to read first frame
    ret, frame = cap.read()
    if ret:
        print(f"  First Frame: {frame.shape}")
        print(f"\n✅ Video is fully compatible with the validation tool!")
    else:
        print(f"\n⚠️  Warning: Could not read first frame")
        print(f"    The file might be corrupted or have unsupported codec")
    
    cap.release()
    return ret


def main():
    print("\nThis script tests if your video file is compatible with OpenCV")
    print("(which is used by the ROI analysis tool)")
    
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = input("\nEnter video file path: ").strip().strip('"')
    
    if not video_path:
        print("No file path provided. Exiting.")
        return
    
    success = test_video_file(video_path)
    
    print("\n" + "=" * 70)
    if success:
        print("✅ Your video file is ready to use with validation_points.py")
    else:
        print("❌ Please convert your video file before using validation_points.py")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
