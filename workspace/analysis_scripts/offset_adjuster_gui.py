"""
Simple GUI to manually adjust offset between detected and ground truth data.
Allows real-time preview with video overlay.
"""

import cv2
import numpy as np
import pandas as pd
import os
import sys

# Configuration
GT_CSV = "../stimulus_ground_truth_trimmed.csv"
DETECTION_RESULTS_DIR = "output/detection_results"
VIDEO_DIR = "Eyegaze/rapi"

# Global state
current_offset = 0
current_frame_idx = 0
gt_df = None
detected_df = None
video_cap = None
current_method = ""
current_variant = ""
total_frames = 0
playing = False
video_fps = 30.0  # Will be updated from actual video
gt_fps = 60.0     # GT generated at 60 FPS
detected_df = None
current_method = "color"
current_variant = "varian1"
video_cap = None
total_frames = 0
playing = False

def calculate_preview_error(offset):
    """Calculate error with given offset for preview."""
    detected_temp = detected_df.copy()
    detected_temp['frame_adjusted'] = detected_temp['frame'] - offset
    
    merged = pd.merge(gt_df, detected_temp, left_on='frame', right_on='frame_adjusted', how='inner')
    merged_valid = merged[merged['gt_x_px'].notna()].copy()
    
    if len(merged_valid) == 0:
        return float('inf'), 0
    
    merged_valid['euclidean_error'] = np.sqrt(
        (merged_valid['x'] - merged_valid['gt_x_px'])**2 +
        (merged_valid['y'] - merged_valid['gt_y_px'])**2
    )
    
    return merged_valid['euclidean_error'].mean(), len(merged_valid)

def nothing(x):
    pass

def draw_crosshair(img, x, y, color, size=20):
    """Draw crosshair at position."""
    if x is not None and y is not None:
        x, y = int(x), int(y)
        cv2.line(img, (x-size, y), (x+size, y), color, 2)
        cv2.line(img, (x, y-size), (x, y+size), color, 2)
        cv2.circle(img, (x, y), size//2, color, 2)

def get_frame_data(frame_num, offset):
    """Get GT and detected data for a specific frame.
    
    Video and detection are always synced (same frame number).
    Offset shifts GT to align with detection.
    Maps video frame to GT via TIMESTAMP to handle FPS mismatch.
    """
    global video_fps, gt_fps
    
    # Get detected data for this frame (always matches video frame)
    det_row = detected_df[detected_df['frame'] == frame_num]
    if len(det_row) == 0:
        det_pos = None
        is_interpolated = True
    else:
        det_pos = (det_row.iloc[0]['x'], det_row.iloc[0]['y'])
        is_interpolated = det_row.iloc[0]['is_interpolated']
    
    # Calculate timestamp of video frame
    video_timestamp = frame_num / video_fps
    
    # Add offset as time shift (in seconds)
    offset_seconds = offset / video_fps
    gt_timestamp = video_timestamp + offset_seconds
    
    # Map timestamp to GT frame number
    gt_frame = int(round(gt_timestamp * gt_fps))
    
    # Get GT data at calculated frame
    gt_row = gt_df[gt_df['frame'] == gt_frame]
    if len(gt_row) == 0 or pd.isna(gt_row.iloc[0]['gt_x_px']):
        gt_pos = None
    else:
        gt_pos = (gt_row.iloc[0]['gt_x_px'], gt_row.iloc[0]['gt_y_px'])
    
    # Calculate error
    error = None
    if gt_pos and det_pos:
        error = np.sqrt((det_pos[0] - gt_pos[0])**2 + (det_pos[1] - gt_pos[1])**2)
    
    return gt_pos, det_pos, is_interpolated, error, gt_frame

def render_frame(frame_num, offset):
    """Render video frame with overlays."""
    global video_cap
    
    # Force video to exact frame position with double-check
    current_pos = int(video_cap.get(cv2.CAP_PROP_POS_FRAMES))
    if current_pos != frame_num:
        video_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        # Verify seek succeeded
        actual_pos = int(video_cap.get(cv2.CAP_PROP_POS_FRAMES))
        if actual_pos != frame_num:
            print(f"Warning: Seek failed. Wanted {frame_num}, got {actual_pos}")
    
    ret, frame = video_cap.read()
    
    if not ret or frame is None:
        # Create blank frame if video read fails
        print(f"Warning: Cannot read frame {frame_num}")
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    
    # Resize if needed for display
    display_frame = cv2.resize(frame, (960, 540))
    
    # Get data
    gt_pos, det_pos, is_interpolated, error, gt_frame = get_frame_data(frame_num, offset)
    
    # Draw frame info
    cv2.rectangle(display_frame, (0, 0), (960, 130), (0, 0, 0), -1)
    cv2.putText(display_frame, f"Video/Det: Frame {frame_num} @ {frame_num/video_fps:.3f}s | GT: Frame {gt_frame} @ {gt_frame/gt_fps:.3f}s", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
    
    # Draw GT position (red)
    if gt_pos:
        draw_crosshair(display_frame, gt_pos[0]/2, gt_pos[1]/2, (0, 0, 255), 15)
        cv2.putText(display_frame, "GT", (int(gt_pos[0]/2)+20, int(gt_pos[1]/2)-20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    # Draw detected position (green if good, yellow if interpolated)
    if det_pos:
        color = (0, 165, 255) if is_interpolated else (0, 255, 0)
        draw_crosshair(display_frame, det_pos[0]/2, det_pos[1]/2, color, 15)
        label = "DET (interp)" if is_interpolated else "DET"
        cv2.putText(display_frame, label, (int(det_pos[0]/2)+20, int(det_pos[1]/2)+25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    # Get phase info
    gt_row = gt_df[gt_df['frame'] == frame_num]
    phase_name = gt_row.iloc[0]['phase'] if len(gt_row) > 0 else "Unknown"
    has_gt = not pd.isna(gt_row.iloc[0]['gt_x_px']) if len(gt_row) > 0 else False
    
    cv2.putText(display_frame, f"Phase: {phase_name}", (10, 55),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    status_color = (0, 255, 0) if has_gt else (0, 0, 255)
    status_text = "GT Available" if has_gt else "No GT (instruction/prep phase)"
    cv2.putText(display_frame, status_text, (10, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)
    
    cv2.putText(display_frame, f"Offset: {offset} frames ({offset/60*1000:.1f} ms)", (10, 105),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    
    if error is not None:
        color = (0, 255, 0) if error <= 11.04 else (0, 0, 255)
        cv2.putText(display_frame, f"Error: {error:.1f} px", (10, 125),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # Legend
    cv2.rectangle(display_frame, (0, 460), (960, 540), (0, 0, 0), -1)
    cv2.putText(display_frame, "RED = Ground Truth (shifted by offset) | GREEN = Detected | YELLOW = Interpolated", 
                (10, 485), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    cv2.putText(display_frame, "Adjust offset until red GT and green DET crosshairs align",
                (10, 505), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    cv2.putText(display_frame, "Space=Play | Left/Right=Frame | +/-=Offset | Home=FirstGT | S=Save | Q=Quit",
                (10, 525), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    
    return display_frame

def main():
    global current_offset, gt_df, detected_df, current_method, current_variant
    global video_cap, total_frames, current_frame_idx, playing, video_fps, gt_fps
    
    # Load ground truth
    if not os.path.exists(GT_CSV):
        print(f"Error: Ground truth CSV not found: {GT_CSV}")
        return
    
    gt_df = pd.read_csv(GT_CSV)
    print("Ground truth loaded.")
    
    # List available detection results
    if not os.path.exists(DETECTION_RESULTS_DIR):
        print(f"Error: Detection results directory not found: {DETECTION_RESULTS_DIR}")
        return
    
    files = [f for f in os.listdir(DETECTION_RESULTS_DIR) if f.endswith('.csv')]
    if not files:
        print("No detection result files found.")
        return
    
    print("\nAvailable detection results:")
    for i, f in enumerate(files):
        print(f"  {i+1}. {f}")
    
    choice = input("\nSelect file number: ").strip()
    try:
        selected_file = files[int(choice) - 1]
        parts = selected_file.replace('.csv', '').split('_')
        current_method = parts[0]
        current_variant = parts[1]
    except:
        print("Invalid selection. Using default: color_varian1.csv")
        selected_file = "color_varian1.csv"
    
    detected_csv = os.path.join(DETECTION_RESULTS_DIR, selected_file)
    detected_df = pd.read_csv(detected_csv)
    print(f"\nLoaded: {selected_file}")
    
    # Load video
    video_path = os.path.join(VIDEO_DIR, f"{current_variant}.mp4")
    if not os.path.exists(video_path):
        print(f"Error: Video not found: {video_path}")
        return
    
    video_cap = cv2.VideoCapture(video_path)
    total_frames = int(video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_fps = video_cap.get(cv2.CAP_PROP_FPS)
    gt_fps = 60.0  # GT was generated at 60 FPS
    
    print(f"Loaded video: {video_path} ({total_frames} frames @ {video_fps} FPS)")
    print(f"Ground truth: {len(gt_df)} frames @ {gt_fps} FPS")
    
    if abs(video_fps - gt_fps) > 0.1:
        print(f"\n⚠️  FPS MISMATCH DETECTED: Video={video_fps} FPS, GT={gt_fps} FPS")
        print(f"    Using timestamp-based mapping to handle FPS difference.")
    
    # Find first valid GT frame
    first_valid_frame = int(gt_df[gt_df['gt_x_px'].notna()].iloc[0]['frame'])
    print(f"First valid GT data at frame: {first_valid_frame}")
    print(f"(Opening/instruction phases have no target, starting at TUTORIAL)")
    
    # Create window
    window_name = f"Offset Adjuster - {current_method}_{current_variant}"
    cv2.namedWindow(window_name)
    
    # Set initial trackbar positions BEFORE loop
    cv2.createTrackbar("Frame", window_name, first_valid_frame, total_frames-1, nothing)
    cv2.createTrackbar("Offset", window_name, 300, 600, nothing)
    
    print("\nControls:")
    print("  Frame slider: Jump to frame")
    print("  Offset slider: -300 to +300 frames")
    print("  Space: Play/Pause")
    print("  Left/Right arrows: Previous/Next frame")
    print("  +/-: Increase/Decrease offset by 1")
    print("  Home: Jump to first valid GT frame")
    print("  S: Save offset")
    print("  Q: Quit")
    
    current_frame_idx = first_valid_frame
    playing = False
    
    # Wait for window to be ready
    cv2.waitKey(1)
    
    while True:
        # Render frame with current position
        display = render_frame(current_frame_idx, current_offset)
        cv2.imshow(window_name, display)
        
        # Handle playback
        if playing:
            current_frame_idx += 1
            if current_frame_idx >= total_frames:
                current_frame_idx = 0
                playing = False
            cv2.setTrackbarPos("Frame", window_name, current_frame_idx)
            key = cv2.waitKey(33) & 0xFF  # ~30 FPS
        else:
            key = cv2.waitKey(1) & 0xFF
        
        # Get trackbar positions AFTER waitKey (window must be ready)
        trackbar_frame = cv2.getTrackbarPos("Frame", window_name)
        offset_raw = cv2.getTrackbarPos("Offset", window_name)
        current_offset = offset_raw - 300
        
        # Update frame if trackbar moved
        if trackbar_frame != current_frame_idx and not playing:
            current_frame_idx = trackbar_frame
        
        if key == ord('q'):
            break
        elif key == ord(' '):  # Space
            playing = not playing
        elif key == 81 or key == 2:  # Left arrow
            current_frame_idx = max(0, current_frame_idx - 1)
            cv2.setTrackbarPos("Frame", window_name, current_frame_idx)
        elif key == 83 or key == 3:  # Right arrow
            current_frame_idx = min(total_frames - 1, current_frame_idx + 1)
            cv2.setTrackbarPos("Frame", window_name, current_frame_idx)
        elif key == ord('+') or key == ord('='):
            offset_raw = min(600, offset_raw + 1)
            cv2.setTrackbarPos("Offset", window_name, offset_raw)
        elif key == ord('-') or key == ord('_'):
            offset_raw = max(0, offset_raw - 1)
            cv2.setTrackbarPos("Offset", window_name, offset_raw)
        elif key == ord('h') or key == 0:  # Home key
            current_frame_idx = first_valid_frame
            cv2.setTrackbarPos("Frame", window_name, current_frame_idx)
            print(f"Jumped to first valid GT frame: {first_valid_frame}")
        elif key == ord('s'):
            # Calculate overall metrics for save
            mean_error, valid_frames = calculate_preview_error(current_offset)
            delay_ms = (current_offset / 60.0) * 1000
            
            save_file = f"offset_{current_method}_{current_variant}.txt"
            with open(save_file, 'w') as f:
                f.write(f"offset_frames={current_offset}\n")
                f.write(f"delay_ms={delay_ms:.2f}\n")
                f.write(f"mean_error={mean_error:.2f}\n")
            print(f"\n✓ Saved to: {save_file}")
            print(f"  Offset: {current_offset} frames")
            print(f"  Delay: {delay_ms:.2f} ms")
            print(f"  Mean Error: {mean_error:.2f} px")
    
    video_cap.release()
    cv2.destroyAllWindows()
    print("\nDone.")

if __name__ == "__main__":
    main()
