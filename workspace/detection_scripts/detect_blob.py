# Import libraries
import cv2
import os
import numpy as np
import pandas as pd
import datetime
from tqdm import tqdm

# === FUNGSI-FUNGSI BANTU (HELPER FUNCTIONS) ===

def refine_blob_center_geometric(gray_img, keypoint, threshold_value=180):
    """
    Refine blob center by finding the geometric centroid of the thresholded blob area.
    """
    x, y = int(keypoint.pt[0]), int(keypoint.pt[1])
    radius = int(keypoint.size / 2) + 5
    mask = np.zeros_like(gray_img)
    cv2.circle(mask, (x, y), radius, (255), -1)
    masked_gray = cv2.bitwise_and(gray_img, gray_img, mask=mask)
    _, binary_blob = cv2.threshold(masked_gray, threshold_value, 255, cv2.THRESH_BINARY)
    moments = cv2.moments(binary_blob)
    if moments['m00'] != 0:
        cx = int(moments['m10'] / moments['m00'])
        cy = int(moments['m01'] / moments['m00'])
        return cx, cy
    return x, y

def draw_crosshair(img, x, y, color, label=None, style='+'):
    """Draw crosshair at (x, y) with optional label"""
    if x is None or y is None:
        return
    if style == '+':
        cv2.line(img, (x-8, y), (x+8, y), color, 2)
        cv2.line(img, (x, y-8), (x, y+8), color, 2)
    elif style == '*':
        cv2.line(img, (x-10, y), (x+10, y), color, 2)
        cv2.line(img, (x, y-10), (x, y+10), color, 2)
        cv2.line(img, (x-7, y-7), (x+7, y+7), color, 2)
        cv2.line(img, (x-7, y+7), (x+7, y-7), color, 2)
    if label:
        cv2.putText(img, label, (x+15, y-15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def annotate_frame(img, frame_idx, raw_xy, refined_xy):
    """Annotate frame with index and coordinates at the bottom-left."""
    height, _, _ = img.shape
    txt = f"Frame {frame_idx} | Raw: {raw_xy} | Refined: {refined_xy}"
    cv2.putText(img, txt, (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

# === MANAJEMEN FILE & DIREKTORI ===
input_video = input(f"Masukkan path video: ").strip().strip('"')

if not os.path.exists(input_video):
    print(f"Error: File video tidak ditemukan: {input_video}")
    exit()

timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
base_output_dir = f"output_detect_blob_{os.path.basename(input_video)}_{timestamp}"

output_video_path = os.path.join(base_output_dir, f"video_processed.mp4")
output_csv_path = os.path.join(base_output_dir, f"gaze_data.csv")

os.makedirs(base_output_dir, exist_ok=True)

# === PERSIAPAN VIDEO & BLOB DETECTOR ===
vid = cv2.VideoCapture(input_video)
if not vid.isOpened():
    print(f"Error: Tidak bisa membuka file video: {input_video}")
    exit()

# Dapatkan properti video untuk output
width = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = vid.get(cv2.CAP_PROP_FPS)
if fps == 0: fps = 60 # Fallback
total_frames = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))

# Inisialisasi video writer untuk output
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

# Inisialisasi Blob Detector
params = cv2.SimpleBlobDetector_Params()

# 1. Thresholding (Penting untuk warna biru/gelap yang dikonversi ke grayscale)
params.minThreshold = 10
params.maxThreshold = 255

# 2. Filter by Color (Cari blob terang di latar gelap)
params.filterByColor = True
params.blobColor = 255 

# 3. Filter by Area
params.filterByArea = True
params.minArea = 30
params.maxArea = 5000

# 4. Filter by Shape (Matikan convexity karena cincin tidak convex)
params.filterByCircularity = False 
params.filterByConvexity = False
params.filterByInertia = False

detector = cv2.SimpleBlobDetector_create(params)

# === PEMROSESAN UTAMA (STREAMING FRAME PER FRAME) ===
print("Memulai pemrosesan video secara streaming...")
gaze_data = []
frame_index = 0

# Initialize tqdm
pbar = tqdm(total=total_frames, unit="frame")

### PERUBAHAN UTAMA: Loop digabung menjadi satu untuk efisiensi memori ###
while True:
    success, frame = vid.read()
    if not success:
        break # Akhir dari video

    # Proses setiap frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    keypoints = detector.detect(gray)
    
    overlay_frame = frame.copy()
    
    raw_x, raw_y = None, None
    refined_x, refined_y = None, None
    
    if keypoints:
        kp = keypoints[0]
        raw_x, raw_y = int(kp.pt[0]), int(kp.pt[1])
        refined_x, refined_y = refine_blob_center_geometric(gray, kp)
        
        draw_crosshair(overlay_frame, raw_x, raw_y, (0,0,255), label='Raw', style='+')
        draw_crosshair(overlay_frame, refined_x, refined_y, (0,255,0), label='Refined', style='*')

    annotate_frame(overlay_frame, frame_index, (raw_x, raw_y), (refined_x, refined_y))
    
    gaze_data.append({
        'frame': frame_index,
        'raw_x': raw_x, 'raw_y': raw_y,
        'refined_x': refined_x, 'refined_y': refined_y
    })
    
    # Langsung tulis frame yang sudah diproses ke video output
    out.write(overlay_frame)
    
    frame_index += 1
    # Update progress bar
    pbar.update(1)

pbar.close()
print("\nPemrosesan selesai.")

# === PENYIMPANAN & PEMBERSIHAN ===
# Simpan data CSV
df = pd.DataFrame(gaze_data)
df.to_csv(output_csv_path, index=False)
print(f"Data CSV telah disimpan di: {output_csv_path}")

# Release semua resource
vid.release()
out.release()
print(f"Video dengan overlay telah disimpan di: {output_video_path}")