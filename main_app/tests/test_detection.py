"""
Test script for detection algorithms module.
Creates a synthetic test image and tests all 5 detection methods.
"""

import cv2
import numpy as np
from modules.detection_algorithms import (
    detect_hough_circle,
    detect_contour,
    detect_color,
    detect_combined,
    detect_blob,
    apply_kalman_filter,
    get_default_params
)


def create_test_image(width=640, height=480):
    """Create a synthetic test image with circular objects (simulated pupils)."""
    # Create blank image
    image = np.ones((height, width, 3), dtype=np.uint8) * 200  # Light gray background
    
    # Draw some "pupils" (dark circles)
    pupils = [
        (200, 200, 30),  # (x, y, radius)
        (440, 300, 25),
        (320, 380, 35)
    ]
    
    for x, y, r in pupils:
        # Draw dark pupil
        cv2.circle(image, (x, y), r, (20, 20, 20), -1)
        # Draw slight gradient for realism
        cv2.circle(image, (x-5, y-5), r//3, (40, 40, 40), -1)
    
    return image, pupils


def test_method(method_name, detect_func, image, ground_truth):
    """Test a single detection method."""
    print(f"\n{'='*60}")
    print(f"Testing: {method_name}")
    print(f"{'='*60}")
    
    # Get default parameters
    params = get_default_params(method_name.lower().replace(' ', '_').replace('-', '_'))
    
    # Run detection
    detections = detect_func(image, params)
    
    # Print results
    print(f"Ground truth pupils: {len(ground_truth)}")
    print(f"Detected: {len(detections)}")
    
    if detections:
        print("\nDetections:")
        for i, (x, y, r) in enumerate(detections, 1):
            print(f"  {i}. Center: ({x}, {y}), Radius: {r}")
            
            # Find closest ground truth
            min_dist = float('inf')
            closest_gt = None
            for gt_x, gt_y, gt_r in ground_truth:
                dist = np.sqrt((x - gt_x)**2 + (y - gt_y)**2)
                if dist < min_dist:
                    min_dist = dist
                    closest_gt = (gt_x, gt_y, gt_r)
            
            if closest_gt:
                print(f"     Closest GT: ({closest_gt[0]}, {closest_gt[1]}), Distance: {min_dist:.1f}px")
    else:
        print("No detections found.")
    
    # Create annotated image
    annotated = image.copy()
    
    # Draw ground truth in blue
    for x, y, r in ground_truth:
        cv2.circle(annotated, (x, y), r, (255, 0, 0), 2)
        cv2.putText(annotated, "GT", (x-10, y-r-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    
    # Draw detections in green
    for x, y, r in detections:
        cv2.circle(annotated, (x, y), r, (0, 255, 0), 2)
        cv2.circle(annotated, (x, y), 2, (0, 0, 255), 3)
    
    return detections, annotated


def main():
    """Main test function."""
    print("="*60)
    print("DETECTION ALGORITHMS TEST")
    print("="*60)
    
    # Create test image
    print("\nCreating synthetic test image with 3 pupils...")
    test_image, ground_truth = create_test_image()
    
    # Save original
    cv2.imwrite("test_original.png", test_image)
    print("✓ Saved: test_original.png")
    
    # Test each method
    methods = [
        ("Hough Circle", detect_hough_circle, "hough"),
        ("Contour-based", detect_contour, "contour"),
        ("Color-based", detect_color, "color"),
        ("Blob Detector", detect_blob, "blob"),
        ("Combined", detect_combined, "combined")
    ]
    
    all_results = {}
    
    for name, func, key in methods:
        detections, annotated = test_method(name, func, test_image, ground_truth)
        all_results[key] = detections
        
        # Save annotated image
        filename = f"test_{key}.png"
        cv2.imwrite(filename, annotated)
        print(f"✓ Saved: {filename}")
    
    # Test Kalman filtering
    print(f"\n{'='*60}")
    print("Testing Kalman Filter")
    print(f"{'='*60}")
    
    # Create trajectory (simulated detections over time)
    trajectory = [
        (100 + i*5, 100 + int(10*np.sin(i/5)), 25)
        for i in range(30)
    ]
    
    print(f"Input trajectory points: {len(trajectory)}")
    smoothed = apply_kalman_filter(trajectory)
    print(f"Smoothed trajectory points: {len(smoothed)}")
    
    # Visualize trajectory
    traj_image = np.ones((300, 500, 3), dtype=np.uint8) * 255
    
    # Draw original in red
    for i in range(len(trajectory) - 1):
        x1, y1, _ = trajectory[i]
        x2, y2, _ = trajectory[i + 1]
        cv2.line(traj_image, (x1, y1), (x2, y2), (0, 0, 255), 2)
    
    # Draw smoothed in green
    for i in range(len(smoothed) - 1):
        x1, y1, _ = smoothed[i]
        x2, y2, _ = smoothed[i + 1]
        cv2.line(traj_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    
    cv2.imwrite("test_kalman.png", traj_image)
    print("✓ Saved: test_kalman.png (red=original, green=smoothed)")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Ground truth pupils: {len(ground_truth)}")
    for name, _, key in methods:
        count = len(all_results[key])
        accuracy = (count / len(ground_truth) * 100) if ground_truth else 0
        print(f"{name:20s}: {count} detections ({accuracy:.0f}% recall)")
    
    print("\n✓ All tests complete!")
    print("Check the test_*.png files for visual results.")


if __name__ == "__main__":
    main()
