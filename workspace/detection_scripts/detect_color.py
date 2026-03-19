# Import libraries
import cv2
import os
import numpy as np
import pandas as pd
import datetime
from tqdm import tqdm

def intensity_weighted_center(gray_img, mask=None):
    """Compute intensity-weighted centroid"""
    if mask is not None:
        masked = cv2.bitwise_and(gray_img, gray_img, mask=mask)
    else:
        masked = gray_img
    moments = cv2.moments(masked)
    if moments['m00'] != 0:
        cx = int(moments['m10'] / moments['m00'])
        cy = int (moments['m01'] / moments['m00'])
        return cx, cy
    return None, None

def brightest_area_center(gray_img, area_size=20):
    """Find center of brightest area in grayscale image"""
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(gray_img)
    x, y = maxLoc
    # Refine by averaging in a small window
    x1, y1 = max(0, x-area_size//2), max(0, y-area_size//2)
    x2, y2 = min(gray_img.shape[1], x+area_size//2), min(gray_img.shape[0], y+area_size//2)
    roi = gray_img[y1:y2, x1:x2]
    if roi.size > 0:
        moments = cv2.moments(roi)
        if moments['m00'] != 0:
            cx = int(moments['m10'] / moments['m00']) + x1
            cy = int(moments['m01'] / moments['m00']) + y1
            return cx, cy
        return x, y
    
def draw_crosshair(img, x, y, color, label=None, style='+'):
    """Draw crosshair at (x, y) with optional label"""
    if x is None or y is None:
        return
    # Draw crosshair
    if style == '+':
        cv2.line(img, (x-8, y), (x+8, y), color, 2)
        cv2.line(img, (x, y-8), (x, y+8), color, 2)
    if style == '*':
        cv2.line(img, (x-8, y), (x+8, y), color, 2)
        cv2.line(img, (x, y-8), (x, y+8), color, 2)
        cv2.line(img, (x-6, y-6), (x+6, y+6), color, 1)
        cv2.line(img, (x-6, y+6), (x+6, y-6), color, 1)
    if label:
        cv2.putText(img, label, (x+10, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
def annotate_frame(img, frame_idx, raw_xy, refined_xy):
    """Annotate frame with index and coordinates."""
    txt = f"Frame {frame_idx} | Raw: {raw_xy} | Refined: {refined_xy}"
    cv2.putText(img, txt, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)

# === FILE MANAGEMENT ===
# Load input video
default_video = r"Eyegaze\eyegaze-2025-11-05 13-18-06.mp4"
input_video = input(f"Masukkan path video (default: {default_video}): ").strip().strip('"')
if not input_video:
    input_video = default_video

if not os.path.exists(input_video):
    print(f"Error: File video tidak ditemukan: {input_video}")
    exit()

# Timestamp
current_time = datetime.datetime.now()
timestamp = current_time.strftime("%Y-%m-%d_%H-%M-%S")

# Sanitize input video filename for output paths
input_filename = os.path.basename(input_video)
input_name_no_ext = os.path.splitext(input_filename)[0]

base_output_dir = f"output_detect_color_{input_name_no_ext}_{timestamp}"
output_video_path = os.path.join(base_output_dir, f"video_processed.mp4")
output_csv_path = os.path.join(base_output_dir, f"gaze_data.csv")

os.makedirs(base_output_dir, exist_ok=True)

# === VIDEO SETUP ===
vid = cv2.VideoCapture(input_video)
if not vid.isOpened():
    print(f"Error: Tidak bisa membuka file video: {input_video}")
    exit()

width = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = vid.get(cv2.CAP_PROP_FPS)
if fps == 0: fps = 30
total_frames = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))

# Output Video Writer
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

# === STEP 2: COLOR DETECTION SETUP ===
print("Setting up Color Detector (Cyan/Blue-ish)...")

# Initial HSV values for Cyan/Blue-ish "ball"
# Cyan is around 90 in OpenCV's HSV (0-180 scale)
# We want to target the "thin cyan ball" inside the fire
h_min, s_min, v_min = 80, 50, 200  # High Value (brightness) for the "ball"
h_max, s_max, v_max = 100, 255, 255

def nothing(x):
    pass

# Create a window for trackbars
cv2.namedWindow("Color Tuning")
cv2.createTrackbar("H Min", "Color Tuning", h_min, 179, nothing)
cv2.createTrackbar("S Min", "Color Tuning", s_min, 255, nothing)
cv2.createTrackbar("V Min", "Color Tuning", v_min, 255, nothing)
cv2.createTrackbar("H Max", "Color Tuning", h_max, 179, nothing)
cv2.createTrackbar("S Max", "Color Tuning", s_max, 255, nothing)
cv2.createTrackbar("V Max", "Color Tuning", v_max, 255, nothing)

# === PROCESSING LOOP ===
print("Starting streaming processing...")
gaze_data = []
skipped_frames = []
frame_index = 0

pbar = tqdm(total=total_frames, unit="frame")

while True:
    success, frame = vid.read()
    if not success:
        break

    # Get current trackbar positions
    h_min = cv2.getTrackbarPos("H Min", "Color Tuning")
    s_min = cv2.getTrackbarPos("S Min", "Color Tuning")
    v_min = cv2.getTrackbarPos("V Min", "Color Tuning")
    h_max = cv2.getTrackbarPos("H Max", "Color Tuning")
    s_max = cv2.getTrackbarPos("S Max", "Color Tuning")
    v_max = cv2.getTrackbarPos("V Max", "Color Tuning")

    # Convert to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Create Mask
    lower_bound = np.array([h_min, s_min, v_min])
    upper_bound = np.array([h_max, s_max, v_max])
    mask = cv2.inRange(hsv, lower_bound, upper_bound)
    
    # Morphological operations to remove noise (the "fire" might be noise if we want the ball)
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=2)
    
    # Find Contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    detected_x, detected_y = None, None
    
    if contours:
        # Find the largest contour (assuming the ball is the most significant cyan object)
        # Or we could look for the most "circular" one if the fire is irregular
        largest_contour = max(contours, key=cv2.contourArea)
        
        if cv2.contourArea(largest_contour) > 10: # Minimum area filter
            M = cv2.moments(largest_contour)
            if M["m00"] != 0:
                detected_x = int(M["m10"] / M["m00"])
                detected_y = int(M["m01"] / M["m00"])
                
                # Draw contour and center
                cv2.drawContours(frame, [largest_contour], -1, (0, 255, 0), 2)
                draw_crosshair(frame, detected_x, detected_y, (0, 0, 255), label="Ball", style='*')

    if detected_x is None:
        skipped_frames.append(frame_index)
        # Fallback: use previous known position or center? 
        # For now, let's leave as None or 0
        if gaze_data:
             # Simple hold last value
             detected_x = gaze_data[-1]['detected_x']
             detected_y = gaze_data[-1]['detected_y']
        else:
             detected_x, detected_y = 0, 0

    # Annotate
    annotate_frame(frame, frame_index, (detected_x, detected_y), "Color")
    
    # Show Mask for Tuning
    cv2.imshow("Mask (White = Detected)", mask)
    cv2.imshow("Result", frame)
    
    # Write to output video
    out.write(frame)
    
    # Save Data
    gaze_data.append({
        'frame': frame_index,
        'detected_x': detected_x,
        'detected_y': detected_y
    })
    
    frame_index += 1
    pbar.update(1)
    
    # Wait key for tuning
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

pbar.close()
print("\nProcessing finished.")

if skipped_frames:
    print(f"Skipped frames: {len(skipped_frames)}")

# Save CSV
df = pd.DataFrame(gaze_data)
df.to_csv(output_csv_path, index=False)
print(f"Data CSV saved in: {output_csv_path}")

vid.release()
out.release()
cv2.destroyAllWindows()
print(f"Video saved in: {output_video_path}")