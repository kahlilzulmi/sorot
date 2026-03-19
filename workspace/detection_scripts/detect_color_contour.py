import cv2
import os
import numpy as np
import pandas as pd
import datetime
from tqdm import tqdm

# ==============================================================================
# 1. PARAMETER UNTUK TUNING
# ==============================================================================
BBOX_SIZE = 400 # Ukuran sisi bounding square (dalam piksel). Sesuaikan jika target bergerak sangat cepat.
MIN_AREA = 50    # Area minimum kontur agar dianggap sebagai target. Naikkan jika mendeteksi noise.

# ==============================================================================
# 2. FUNGSI-FUNGSI BANTU
# ==============================================================================

def nothing(x):
    pass

# Setup Trackbars for Tuning
cv2.namedWindow("Tuning")
cv2.createTrackbar("Threshold", "Tuning", 200, 255, nothing) # For Grayscale
cv2.createTrackbar("H Min", "Tuning", 80, 179, nothing)      # For Color
cv2.createTrackbar("H Max", "Tuning", 100, 179, nothing)
cv2.createTrackbar("S Min", "Tuning", 50, 255, nothing)
cv2.createTrackbar("V Min", "Tuning", 100, 255, nothing)

def detect_combined(frame):
    """
    Combines Grayscale Thresholding (for brightness/shape) 
    AND Color Thresholding (for specific hue).
    Returns the intersection of both masks.
    """
    # 1. Grayscale Thresholding (Bright spots)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    thresh_val = cv2.getTrackbarPos("Threshold", "Tuning")
    _, mask_gray = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)
    
    # 2. Color Thresholding (Cyan/Blue)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h_min = cv2.getTrackbarPos("H Min", "Tuning")
    h_max = cv2.getTrackbarPos("H Max", "Tuning")
    s_min = cv2.getTrackbarPos("S Min", "Tuning")
    v_min = cv2.getTrackbarPos("V Min", "Tuning")
    
    lower_color = np.array([h_min, s_min, v_min])
    upper_color = np.array([h_max, 255, 255])
    mask_color = cv2.inRange(hsv, lower_color, upper_color)
    
    # 3. Combine Masks (Intersection)
    # We want regions that are BOTH bright AND cyan
    combined_mask = cv2.bitwise_and(mask_gray, mask_color)
    
    # Clean up noise
    kernel = np.ones((3,3), np.uint8)
    combined_mask = cv2.erode(combined_mask, kernel, iterations=1)
    combined_mask = cv2.dilate(combined_mask, kernel, iterations=2)
    
    # 4. Find Contours
    contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    detected_center = None
    largest_contour = None
    
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest_contour) > MIN_AREA:
            # Use moments for centroid
            M = cv2.moments(largest_contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                detected_center = (cx, cy)
            else:
                # Fallback to bounding rect center
                x, y, w, h = cv2.boundingRect(largest_contour)
                detected_center = (x + w//2, y + h//2)
                
    return detected_center, combined_mask, largest_contour

def draw_crosshair(img, x, y, color):
    """Menggambar crosshair sederhana."""
    if x is not None and y is not None:
        cv2.line(img, (x-15, y), (x+15, y), color, 2)
        cv2.line(img, (x, y-15), (x, y+15), color, 2)
        
def draw_filled_circle(img, x, y, radius=75, color=(255, 255, 255)):
    """Menggambar lingkaran berisi warna putih agak transparan dari kontur yang telah dideteksi."""
    if x is not None and y is not None:
        cv2.circle(img, (int(x), int(y)), int(radius), color, -1)

def annotate_frame(img, frame_idx, position_xy):
    """Memberi anotasi pada frame di pojok kiri bawah."""
    height, _, _ = img.shape
    txt = f"Frame: {frame_idx} | Position: {position_xy}"
    cv2.putText(img, txt, (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

# ==============================================================================
# 3. SETUP UTAMA
# ==============================================================================
default_video = "2025-09-10_10-05-50.mkv"
input_video = input(f"Masukkan path video (default: {default_video}): ").strip().strip('"')
if not input_video:
    input_video = default_video

if not os.path.exists(input_video):
    print(f"Error: File video tidak ditemukan: {input_video}")
    exit()

timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
base_output_dir = f"output_detect_color_contour_{os.path.basename(input_video)}_{timestamp}"
output_video_path = os.path.join(base_output_dir, f"video_processed.mp4")
output_csv_path = os.path.join(base_output_dir, f"gaze_data.csv")
os.makedirs(base_output_dir, exist_ok=True)

vid = cv2.VideoCapture(input_video)
if not vid.isOpened():
    print(f"Error: Tidak bisa membuka file video: {input_video}")
    exit()

width = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = vid.get(cv2.CAP_PROP_FPS) if vid.get(cv2.CAP_PROP_FPS) > 0 else 30
total_frames = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

# ==============================================================================
# 4. PEMROSESAN UTAMA DENGAN VISUALISASI
# ==============================================================================
print("Memulai pemrosesan video dengan visualisasi real-time...")
print("Tekan 'q' pada jendela video untuk menghentikan proses.")

gaze_data = []
frame_index = 0

# Initialize tqdm
pbar = tqdm(total=total_frames, unit="frame")

# Loop Utama yang Direvisi Total
while True:
    success, frame = vid.read()
    if not success:
        break
    
    # --- TAHAP 1: DETEKSI OBJEK (COMBINED) ---
    detected_coords, binary_mask, detected_contour = detect_combined(frame)

    # --- TAHAP 2: SIMPAN DATA & VISUALISASI ---
    gaze_data.append({
        'frame': frame_index,
        'detected_x': detected_coords[0] if detected_coords else None,
        'detected_y': detected_coords[1] if detected_coords else None
    })
    
    viz_original = frame.copy()
    
    # Gambar Kontur (Kuning)
    if detected_contour is not None:
        cv2.drawContours(viz_original, [detected_contour], -1, (0, 255, 255), 2)
        
    # Gambar Titik Deteksi (Hijau)
    if detected_coords:
        draw_crosshair(viz_original, detected_coords[0], detected_coords[1], (0, 255, 0)) # Hijau
    
    annotate_frame(viz_original, frame_index, detected_coords)
    cv2.imshow('Original Video + Tracking', viz_original)
    
    # Jendela 2: Proses Deteksi (Mask)
    cv2.imshow('Combined Mask (Gray + Color)', binary_mask)
    
    out.write(viz_original)
    frame_index += 1
    
    # Update progress bar
    pbar.update(1)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("\nProses dihentikan oleh pengguna.")
        break

pbar.close()
print("\nPemrosesan selesai.")

# === PENYIMPANAN & PEMBERSIHAN ===
df = pd.DataFrame(gaze_data)
df.to_csv(output_csv_path, index=False)
print(f"Data CSV telah disimpan di: {output_csv_path}")

vid.release()
out.release()
cv2.destroyAllWindows()
print(f"Video dengan overlay telah disimpan di: {output_video_path}")