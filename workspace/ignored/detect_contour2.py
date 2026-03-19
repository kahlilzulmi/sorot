# Import libraries
import cv2
import os
import numpy as np
import pandas as pd
import datetime

# === FUNGSI-FUNGSI BANTU (HELPER FUNCTIONS) ===

### PERUBAHAN DI SINI: Fungsi deteksi kontur disempurnakan dengan pre-processing ###
def detect_gaze_from_contour(gray_img, min_area=50, threshold_value=60):
    """
    Detects the gaze point by finding the largest contour after pre-processing.
    This version is enhanced to detect thin and faint outlines.
    """
    # 1. Pre-processing: Haluskan gambar untuk mengurangi noise
    blurred_img = cv2.GaussianBlur(gray_img, (5, 5), 0)
    
    # 2. Thresholding dengan nilai lebih rendah agar lebih sensitif
    _, thresh = cv2.threshold(blurred_img, threshold_value, 255, cv2.THRESH_BINARY)
    
    # 3. Pre-processing: Tebalkan garis hasil threshold untuk memastikan kontur solid
    kernel = np.ones((5,5),np.uint8)
    dilated_img = cv2.dilate(thresh, kernel, iterations = 1)
    
    # 4. Cari semua kontur pada gambar yang sudah diproses
    contours, _ = cv2.findContours(dilated_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None, None

    # 5. Filter kontur dan pilih yang terbesar
    largest_contour = max(contours, key=cv2.contourArea)
    
    if cv2.contourArea(largest_contour) < min_area:
        return None, None

    # 6. Hitung titik tengah (sentroid) dari kontur terbesar
    moments = cv2.moments(largest_contour)
    if moments['m00'] != 0:
        cx = int(moments['m10'] / moments['m00'])
        cy = int(moments['m01'] / moments['m00'])
        return cx, cy
        
    return None, None

def draw_crosshair(img, x, y, color, label=None):
    """Draw a simple crosshair at (x, y)"""
    if x is None or y is None:
        return
    cv2.line(img, (x-12, y), (x+12, y), color, 2)
    cv2.line(img, (x, y-12), (x, y+12), color, 2)
    if label:
        cv2.putText(img, label, (x+15, y-15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def annotate_frame(img, frame_idx, position_xy):
    """Annotate frame with index and coordinates at the bottom-left."""
    height, _, _ = img.shape
    txt = f"Frame {frame_idx} | Position: {position_xy}"
    cv2.putText(img, txt, (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

# === MANAJEMEN FILE & DIREKTORI ===
input_video = "2025-09-10_10-05-50.mkv" # Ganti dengan nama file video Anda
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
base_output_dir = f"output_{os.path.basename(input_video)}_{timestamp}"

output_video_path = os.path.join(base_output_dir, f"video_processed.mp4")
output_csv_path = os.path.join(base_output_dir, f"gaze_data.csv")

os.makedirs(base_output_dir, exist_ok=True)

# === PERSIAPAN VIDEO ===
vid = cv2.VideoCapture(input_video)
if not vid.isOpened():
    print(f"Error: Tidak bisa membuka file video: {input_video}")
    exit()

width = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = vid.get(cv2.CAP_PROP_FPS)
if fps == 0: fps = 60
total_frames = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

# === PEMROSESAN UTAMA (STREAMING FRAME PER FRAME) ===
print("Memulai pemrosesan video dengan deteksi kontur...")
gaze_data = []
frame_index = 0

while True:
    success, frame = vid.read()
    if not success:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    cx, cy = detect_gaze_from_contour(gray)
    
    overlay_frame = frame.copy()
    
    if cx is not None and cy is not None:
        draw_crosshair(overlay_frame, cx, cy, (0, 255, 0), label='Detected')

    annotate_frame(overlay_frame, frame_index, (cx, cy))
    
    gaze_data.append({
        'frame': frame_index,
        'x': cx,
        'y': cy,
    })
    
    out.write(overlay_frame)
    
    frame_index += 1
    print(f"Memproses frame {frame_index}/{total_frames}", end='\r')

print("\nPemrosesan selesai.")

# === PENYIMPANAN & PEMBERSIHAN ===
df = pd.DataFrame(gaze_data)
df.to_csv(output_csv_path, index=False)
print(f"Data CSV telah disimpan di: {output_csv_path}")

vid.release()
out.release()
print(f"Video dengan overlay telah disimpan di: {output_csv_path}")