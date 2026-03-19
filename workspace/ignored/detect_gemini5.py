import cv2
import os
import numpy as np
import pandas as pd
import datetime

# ==============================================================================
# 1. PARAMETER UNTUK TUNING
# ==============================================================================
BBOX_SIZE = 250  # Ukuran sisi bounding square (dalam piksel). Sesuaikan jika target bergerak sangat cepat.
MIN_AREA = 70    # Area minimum kontur agar dianggap sebagai target. Naikkan jika mendeteksi noise.

# ==============================================================================
# 2. FUNGSI-FUNGSI BANTU
# ==============================================================================

### FUNGSI DETEKSI UNIVERSAL BARU ###
### FUNGSI DETEKSI BARU: HSV Masking + Filter Bentuk (Circularitas) ###
def detect_gaze_hsv_with_shape_filter(bgr_frame_roi, min_area=50):
    """
    Mendeteksi gaze dengan HSV masking dan memfilter kontur berdasarkan circularity.
    Ini mengatasi masalah "ekor" yang lebih terang dan bentuk outline/solid.
    """
    # 1. Konversi ROI ke HSV
    hsv_roi = cv2.cvtColor(bgr_frame_roi, cv2.COLOR_BGR2HSV)
    
    # 2. Definisikan rentang warna biru/cyan di HSV
    # Parameter ini MUNGKIN perlu di-tuning lebih lanjut!
    # [H_low, S_low, V_low] dan [H_high, S_high, V_high]
    # Hue: Biru/Cyan biasanya antara 80-100
    # Saturation: Dari pudar hingga pekat
    # Value: Dari gelap hingga terang
    lower_cyan = np.array([80, 50, 50]) # S_low & V_low diturunkan agar lebih toleran pada bagian tipis/redup
    upper_cyan = np.array([100, 255, 255])
    
    # 3. Buat mask berdasarkan rentang warna
    mask = cv2.inRange(hsv_roi, lower_cyan, upper_cyan)
    
    # 4. (Opsional) Bersihkan mask dari noise kecil
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1) # Hapus noise
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1) # Tutup celah
    
    # 5. Cari kontur dari mask yang sudah bersih
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None, mask # Kembalikan mask meskipun tidak ada kontur

    # 6. Filter kontur berdasarkan area dan circularity
    best_contour = None
    max_circularity = 0.0
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area: # Abaikan kontur yang terlalu kecil
            continue
        
        # Hitung circularity dan pilih yang paling bulat/lonjong
        circularity = calculate_circularity(contour)
        
        # Filter circularity: 0.2 adalah contoh, sesuaikan jika bentuknya sangat lonjong
        # Semakin mendekati 1.0, semakin bulat sempurna
        if circularity > 0.2 and circularity > max_circularity: 
            max_circularity = circularity
            best_contour = contour

    if best_contour is None:
        return None, mask

    # 7. Hitung titik tengah (sentroid) dari kontur terbaik
    moments = cv2.moments(best_contour)
    if moments['m00'] != 0:
        cx = int(moments['m10'] / moments['m00'])
        cy = int(moments['m01'] / moments['m00'])
        return (cx, cy), mask
        
    return None, mask

def calculate_circularity(contour):
    """Menghitung circularity ratio dari sebuah kontur."""
    area = cv2.contourArea(contour)
    if area == 0:
        return 0
    perimeter = cv2.arcLength(contour, True)
    if perimeter == 0:
        return 0
    circularity = 4 * np.pi * area / (perimeter * perimeter)
    return circularity

def draw_crosshair(img, x, y, color):
    """Menggambar crosshair sederhana."""
    if x is not None and y is not None:
        cv2.line(img, (x-15, y), (x+15, y), color, 2)
        cv2.line(img, (x, y-15), (x, y+15), color, 2)

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
    exit() # Ganti dengan nama file video Anda
    
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
base_output_dir = f"output_{os.path.basename(input_video)}_{timestamp}"
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
bbox = None # Variabel untuk menyimpan posisi bounding box

### GANTI SELURUH LOOP 'WHILE' ANDA DENGAN YANG DI BAWAH INI ###
while True:
    success, frame = vid.read()
    if not success:
        break

    # --- LOGIKA TRACKING-BY-DETECTION ---
    
    # 1. Tentukan Region of Interest (ROI) dan panggil fungsi deteksi
    if bbox:
        # Jika BBOX ADA: definisikan koordinat dan cari di dalam ROI
        x1, y1 = max(0, bbox[0] - BBOX_SIZE // 2), max(0, bbox[1] - BBOX_SIZE // 2)
        x2, y2 = min(width, bbox[0] + BBOX_SIZE // 2), min(height, bbox[1] + BBOX_SIZE // 2)
        
        roi_bgr = frame[y1:y2, x1:x2]
        roi_origin = (x1, y1)
        
        # Panggil deteksi PADA ROI
        detected_coords_roi, binary_viz = detect_gaze_hsv_with_shape_filter(roi_bgr)
    else:
        # Jika BBOX TIDAK ADA: cari di seluruh frame
        roi_origin = (0, 0)
        
        # Panggil deteksi PADA SELURUH FRAME
        detected_coords_roi, binary_viz = detect_gaze_hsv_with_shape_filter(frame)

    # 2. Perbarui Posisi & Bounding Box
    final_coords = None
    if detected_coords_roi:
        # Konversi koordinat ROI kembali ke koordinat frame penuh
        final_coords = (detected_coords_roi[0] + roi_origin[0], detected_coords_roi[1] + roi_origin[1])
        bbox = final_coords # Bounding box untuk frame berikutnya akan berpusat di sini
    else:
        bbox = None # Kehilangan jejak, akan mencari di seluruh frame berikutnya

    # --- SIMPAN DATA & VISUALISASI ---
    gaze_data.append({'frame': frame_index, 'x': final_coords[0] if final_coords else None, 'y': final_coords[1] if final_coords else None})
    
    # Jendela 1: Video Asli + Tracking Info
    viz_original = frame.copy()
    if bbox:
        # Gambar bounding square untuk frame BERIKUTNYA
        x1_b, y1_b = max(0, bbox[0] - BBOX_SIZE // 2), max(0, bbox[1] - BBOX_SIZE // 2)
        x2_b, y2_b = min(width, bbox[0] + BBOX_SIZE // 2), min(height, bbox[1] + BBOX_SIZE // 2)
        cv2.rectangle(viz_original, (x1_b, y1_b), (x2_b, y2_b), (255, 0, 0), 2)
        
    if final_coords:
        draw_crosshair(viz_original, final_coords[0], final_coords[1], (0, 255, 0))
    
    annotate_frame(viz_original, frame_index, final_coords)
    cv2.imshow('Original Video + Tracking', viz_original)
    
    # Jendela 2: Proses Deteksi (Citra Biner)
    binary_viz_color = cv2.cvtColor(binary_viz, cv2.COLOR_GRAY2BGR)
    if detected_coords_roi:
        draw_crosshair(binary_viz_color, detected_coords_roi[0], detected_coords_roi[1], (0, 0, 255))
    cv2.imshow('Detection Process (Binary)', binary_viz_color)
    
    out.write(viz_original)
    
    frame_index += 1
    print(f"Memproses frame {frame_index}/{total_frames}", end='\r')

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("\nProses dihentikan oleh pengguna.")
        break

# === PENYIMPANAN & PEMBERSIHAN ===
df = pd.DataFrame(gaze_data)
df.to_csv(output_csv_path, index=False)
print(f"Data CSV telah disimpan di: {output_csv_path}")

vid.release()
out.release()
cv2.destroyAllWindows()
print(f"Video dengan overlay telah disimpan di: {output_video_path}")