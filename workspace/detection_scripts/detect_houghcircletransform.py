import cv2
import os
import numpy as np
import pandas as pd
import datetime
from tqdm import tqdm

# ==============================================================================
# 1. PARAMETER UTAMA UNTUK TUNING
# ==============================================================================
# --- Parameter untuk Hough Circle Transform ---
# (Ini adalah "kenop" utama Anda sekarang)

# Threshold atas untuk edge detector internal. Tidak perlu sering diubah.
HOUGH_PARAM1 = 50
# Threshold akumulator. Ini yang paling penting.
# TURUNKAN jika lingkaran tidak terdeteksi. NAIKKAN jika terlalu banyak lingkaran palsu.
HOUGH_PARAM2 = 13
# Rentang radius lingkaran (dalam piksel) yang akan dideteksi.
# Diatur sesuai feedback Anda untuk akurasi maksimal.
MIN_RADIUS = 70
MAX_RADIUS = 75

# ==============================================================================
# 2. FUNGSI-FUNGSI BANTU
# ==============================================================================

### FUNGSI DETEKSI FINAL: Menggunakan Hough Circle Transform ###
def detect_gaze_circle_hough(bgr_frame):
    """
    Mendeteksi 'lingkaran sejati' menggunakan Hough Circle Transform.
    Fokus untuk menemukan "bola"-nya, bukan "api"-nya.
    """
    # 1. Pre-processing
    gray_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
    # Median Blur sangat efektif untuk menghilangkan noise sambil menjaga tepi lingkaran
    gray_frame = cv2.medianBlur(gray_frame, 5)

    # 2. Deteksi Lingkaran dengan Hough Transform
    circles = cv2.HoughCircles(
        gray_frame,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=gray_frame.shape[0], # Jarak min antar lingkaran (set besar agar hanya 1)
        param1=HOUGH_PARAM1,
        param2=HOUGH_PARAM2,
        minRadius=MIN_RADIUS,
        maxRadius=MAX_RADIUS
    )

    # 3. Proses hasil
    if circles is not None:
        # Konversi koordinat dan radius ke integer
        circles = np.uint16(np.around(circles))
        # Ambil lingkaran pertama yang ditemukan
        circle = circles[0][0]
        center = (int(circle[0]), int(circle[1]))
        radius = int(circle[2])
        # Kembalikan informasi lingkaran yang ditemukan
        circle_info = {"center": center, "radius": radius}
        return circle_info, gray_frame # Kembalikan gray image untuk visualisasi

    return None, gray_frame

def draw_crosshair(img, x, y, color):
    """Menggambar crosshair sederhana."""
    if x is not None and y is not None:
        cv2.line(img, (x-15, y), (x+15, y), color, 2)
        cv2.line(img, (x, y-15), (x, y+15), color, 2)

def annotate_frame(img, frame_idx, position_xy):
    """Memberi anotasi pada frame di pojok kiri bawah."""
    height, _, _ = img.shape
    txt = f"Frame: {frame_idx} | Detected: {position_xy}"
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
base_output_dir = f"output_detect_houghcircletransform_{os.path.basename(input_video)}_{timestamp}"
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
print("Memulai pemrosesan video dengan deteksi Hough Circle (Full Frame)...")
print("Tekan 'q' pada jendela video untuk menghentikan proses.")

gaze_data = []
frame_index = 0

# Initialize tqdm
pbar = tqdm(total=total_frames, unit="frame")

# Loop Utama Final (disederhanakan tanpa Bounding Box)
while True:
    success, frame = vid.read()
    if not success:
        break

    # --- TAHAP 1: DETEKSI LINGKARAN DI SELURUH FRAME ---
    circle_info, viz_process_img = detect_gaze_circle_hough(frame)

    detected_coords = None
    if circle_info:
        # Jika ada deteksi, gunakan koordinatnya
        detected_coords = circle_info["center"]

    # --- TAHAP 3: SIMPAN DATA & VISUALISASI ---
    gaze_data.append({
        'frame': frame_index,
        'detected_x': detected_coords[0] if detected_coords else None,
        'detected_y': detected_coords[1] if detected_coords else None
    })

    viz_original = frame.copy()

    # Gambar Titik Deteksi Mentah (Hijau) - jika ada
    if detected_coords:
        draw_crosshair(viz_original, detected_coords[0], detected_coords[1], (0, 255, 0))
        
        # Gambar Lingkaran Deteksi (Putih Transparan)
        overlay = viz_original.copy()
        cv2.circle(overlay, detected_coords, circle_info["radius"], (255, 255, 255), 3)
        viz_original = cv2.addWeighted(overlay, 0.7, viz_original, 0.3, 0)

    annotate_frame(viz_original, frame_index, detected_coords)
    cv2.imshow('Original Video + Tracking', viz_original)

    # Jendela 2: Proses Deteksi (Grayscale)
    viz_process_color = cv2.cvtColor(viz_process_img, cv2.COLOR_GRAY2BGR)
    if circle_info:
        # Gambar lingkaran yang terdeteksi di jendela proses
        cv2.circle(viz_process_color, circle_info["center"], circle_info["radius"], (0, 255, 0), 2)
        draw_crosshair(viz_process_color, circle_info["center"][0], circle_info["center"][1], (0, 0, 255))
    cv2.imshow('Detection Process (Grayscale)', viz_process_color)

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

