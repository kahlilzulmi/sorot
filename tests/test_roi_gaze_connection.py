"""
================================================================================
ROI & EYE GAZE CONNECTION TEST
================================================================================

Test script to verify:
1. Eye gaze detection from virtual camera
2. ROI hit detection
3. Visual feedback of gaze-to-ROI mapping
4. Real-time statistics

Press 'q' to quit, 's' to save test results
================================================================================
"""

import cv2
import numpy as np
import time
from collections import defaultdict
import json

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Virtual camera index
VIRTUAL_CAMERA_INDEX = 0

# Test video settings
TEST_VIDEO_PATH = None  # Set to video path or leave None for test pattern
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

# Eye gaze detection parameters (same as main app)
HOUGH_PARAM1 = 50
HOUGH_PARAM2 = 13
MIN_RADIUS = 65
MAX_RADIUS = 80

# Test ROIs (can be modified)
TEST_ROIS = [
    {'name': 'Top-Left', 'x': 100, 'y': 100, 'width': 300, 'height': 200, 'color': (0, 255, 255)},
    {'name': 'Top-Right', 'x': 880, 'y': 100, 'width': 300, 'height': 200, 'color': (255, 0, 255)},
    {'name': 'Center', 'x': 440, 'y': 260, 'width': 400, 'height': 200, 'color': (255, 255, 0)},
    {'name': 'Bottom-Left', 'x': 100, 'y': 420, 'width': 300, 'height': 200, 'color': (0, 255, 0)},
    {'name': 'Bottom-Right', 'x': 880, 'y': 420, 'width': 300, 'height': 200, 'color': (255, 128, 0)},
]

# ==============================================================================
# GAZE DETECTION
# ==============================================================================

def detect_gaze_hough(frame):
    """
    Detect eye gaze using Hough Circle Transform.
    Returns (x, y) tuple or None if not detected.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    
    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=1000,
        param1=HOUGH_PARAM1,
        param2=HOUGH_PARAM2,
        minRadius=MIN_RADIUS,
        maxRadius=MAX_RADIUS
    )
    
    if circles is not None:
        circle = np.uint16(np.around(circles[0, 0]))
        return (int(circle[0]), int(circle[1]))
    
    return None


def find_roi_at_gaze(rois, gaze_x, gaze_y):
    """
    Find which ROI contains the gaze position.
    Returns ROI dict or None.
    """
    for roi in rois:
        if (roi['x'] <= gaze_x <= roi['x'] + roi['width'] and
            roi['y'] <= gaze_y <= roi['y'] + roi['height']):
            return roi
    return None

# ==============================================================================
# VISUALIZATION
# ==============================================================================

def create_test_pattern(width, height):
    """Create a test pattern with grid and labels."""
    frame = np.ones((height, width, 3), dtype=np.uint8) * 30
    
    # Draw grid
    grid_spacing = 100
    for x in range(0, width, grid_spacing):
        cv2.line(frame, (x, 0), (x, height), (60, 60, 60), 1)
    for y in range(0, height, grid_spacing):
        cv2.line(frame, (0, y), (width, y), (60, 60, 60), 1)
    
    # Add center crosshair
    cv2.line(frame, (width//2 - 50, height//2), (width//2 + 50, height//2), (100, 100, 100), 2)
    cv2.line(frame, (width//2, height//2 - 50), (width//2, height//2 + 50), (100, 100, 100), 2)
    
    # Add title
    cv2.putText(frame, "ROI & GAZE CONNECTION TEST", (width//2 - 250, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (200, 200, 200), 2)
    
    return frame


def draw_rois(frame, rois, active_roi=None):
    """Draw all ROIs on frame, highlight active one."""
    for roi in rois:
        color = roi['color']
        thickness = 4 if roi == active_roi else 2
        
        # Draw rectangle
        cv2.rectangle(frame, 
                     (roi['x'], roi['y']), 
                     (roi['x'] + roi['width'], roi['y'] + roi['height']),
                     color, thickness)
        
        # Draw label background
        label = roi['name']
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.rectangle(frame,
                     (roi['x'], roi['y'] - label_size[1] - 10),
                     (roi['x'] + label_size[0] + 10, roi['y']),
                     color, -1)
        
        # Draw label text
        cv2.putText(frame, label, (roi['x'] + 5, roi['y'] - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)


def draw_gaze_cursor(frame, gaze_x, gaze_y):
    """Draw gaze cursor at position."""
    # Outer circle
    cv2.circle(frame, (gaze_x, gaze_y), 20, (0, 255, 0), 2)
    # Inner dot
    cv2.circle(frame, (gaze_x, gaze_y), 5, (0, 255, 0), -1)
    # Crosshair
    cv2.line(frame, (gaze_x - 15, gaze_y), (gaze_x + 15, gaze_y), (0, 255, 0), 2)
    cv2.line(frame, (gaze_x, gaze_y - 15), (gaze_x, gaze_y + 15), (0, 255, 0), 2)


def draw_statistics(frame, stats, fps, detection_rate):
    """Draw statistics overlay."""
    h, w = frame.shape[:2]
    
    # Semi-transparent background
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, h - 220), (400, h - 10), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    
    # Title
    cv2.putText(frame, "STATISTICS", (20, h - 190),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # FPS and detection rate
    cv2.putText(frame, f"FPS: {fps:.1f}", (20, h - 160),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 100), 1)
    cv2.putText(frame, f"Detection: {detection_rate:.1f}%", (20, h - 135),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 255, 100), 1)
    
    # ROI hit counts
    y_pos = h - 105
    cv2.putText(frame, "ROI Hits:", (20, y_pos),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    
    y_pos += 25
    for roi_name, count in sorted(stats.items(), key=lambda x: -x[1]):
        cv2.putText(frame, f"  {roi_name}: {count}", (20, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        y_pos += 20


def draw_status(frame, status_text, color=(255, 255, 255)):
    """Draw status message at top."""
    cv2.putText(frame, status_text, (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

# ==============================================================================
# MAIN TEST
# ==============================================================================

def main():
    print("=" * 80)
    print("ROI & GAZE CONNECTION TEST")
    print("=" * 80)
    print(f"Virtual Camera Index: {VIRTUAL_CAMERA_INDEX}")
    print(f"Number of Test ROIs: {len(TEST_ROIS)}")
    print("\nControls:")
    print("  q - Quit test")
    print("  s - Save test results")
    print("  r - Reset statistics")
    print("=" * 80)
    
    # Open virtual camera
    print("\nOpening virtual camera...")
    gaze_cap = cv2.VideoCapture(VIRTUAL_CAMERA_INDEX)
    if not gaze_cap.isOpened():
        print("❌ ERROR: Cannot open virtual camera!")
        print(f"   Make sure OBS virtual camera is running on index {VIRTUAL_CAMERA_INDEX}")
        return
    
    print("✓ Virtual camera opened successfully")
    
    # Statistics
    roi_hits = defaultdict(int)
    total_frames = 0
    detected_frames = 0
    last_gaze_pos = None
    
    # FPS calculation
    fps = 0.0
    fps_start_time = time.time()
    fps_frame_count = 0
    
    # Create window
    cv2.namedWindow('ROI & Gaze Connection Test', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('ROI & Gaze Connection Test', WINDOW_WIDTH, WINDOW_HEIGHT)
    
    print("\n✓ Test started! Look at different ROIs with your eyes.")
    print("  Press 'q' to quit\n")
    
    while True:
        # Create base frame (test pattern or video)
        if TEST_VIDEO_PATH:
            # TODO: Load from video if path provided
            base_frame = create_test_pattern(WINDOW_WIDTH, WINDOW_HEIGHT)
        else:
            base_frame = create_test_pattern(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Read gaze from virtual camera
        ret, gaze_frame = gaze_cap.read()
        
        current_gaze = None
        active_roi = None
        status_text = ""
        status_color = (255, 255, 255)
        
        if ret:
            total_frames += 1
            
            # Detect gaze position
            detected_gaze = detect_gaze_hough(gaze_frame)
            
            if detected_gaze:
                current_gaze = detected_gaze
                last_gaze_pos = detected_gaze
                detected_frames += 1
                
                # Check which ROI is being looked at
                active_roi = find_roi_at_gaze(TEST_ROIS, current_gaze[0], current_gaze[1])
                
                if active_roi:
                    roi_hits[active_roi['name']] += 1
                    status_text = f"Looking at: {active_roi['name']}"
                    status_color = active_roi['color']
                else:
                    roi_hits['Background'] += 1
                    status_text = "Looking at: Background"
                    status_color = (100, 100, 100)
                    
            else:
                # Use last known position
                if last_gaze_pos:
                    current_gaze = last_gaze_pos
                    status_text = "Gaze detection failed - using last position"
                    status_color = (255, 128, 0)
                else:
                    status_text = "No gaze detected yet"
                    status_color = (255, 0, 0)
        else:
            status_text = "Camera read error!"
            status_color = (0, 0, 255)
        
        # Draw ROIs
        draw_rois(base_frame, TEST_ROIS, active_roi)
        
        # Draw gaze cursor
        if current_gaze:
            draw_gaze_cursor(base_frame, current_gaze[0], current_gaze[1])
        
        # Calculate FPS
        fps_frame_count += 1
        if fps_frame_count >= 10:
            fps_end_time = time.time()
            fps = fps_frame_count / (fps_end_time - fps_start_time)
            fps_start_time = time.time()
            fps_frame_count = 0
        
        # Calculate detection rate
        detection_rate = (detected_frames / total_frames * 100) if total_frames > 0 else 0
        
        # Draw statistics
        draw_statistics(base_frame, roi_hits, fps, detection_rate)
        
        # Draw status
        draw_status(base_frame, status_text, status_color)
        
        # Show frame
        cv2.imshow('ROI & Gaze Connection Test', base_frame)
        
        # Handle keyboard input
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            print("\n⏹ Test stopped by user")
            break
        elif key == ord('s'):
            # Save results
            results = {
                'total_frames': total_frames,
                'detected_frames': detected_frames,
                'detection_rate': detection_rate,
                'roi_hits': dict(roi_hits),
                'fps': fps,
                'test_rois': TEST_ROIS
            }
            
            filename = f"test_results_{int(time.time())}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n💾 Results saved to: {filename}")
            
        elif key == ord('r'):
            # Reset statistics
            roi_hits.clear()
            total_frames = 0
            detected_frames = 0
            print("\n🔄 Statistics reset")
    
    # Cleanup
    gaze_cap.release()
    cv2.destroyAllWindows()
    
    # Print final statistics
    print("\n" + "=" * 80)
    print("FINAL STATISTICS")
    print("=" * 80)
    print(f"Total Frames: {total_frames}")
    print(f"Detected Frames: {detected_frames}")
    print(f"Detection Rate: {detection_rate:.1f}%")
    print(f"Average FPS: {fps:.1f}")
    print("\nROI Hit Counts:")
    
    if roi_hits:
        for roi_name, count in sorted(roi_hits.items(), key=lambda x: -x[1]):
            percentage = (count / total_frames * 100) if total_frames > 0 else 0
            print(f"  {roi_name:20s}: {count:6d} hits ({percentage:5.1f}%)")
    else:
        print("  No ROI hits recorded")
    
    print("=" * 80)
    print("✓ Test completed successfully")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
