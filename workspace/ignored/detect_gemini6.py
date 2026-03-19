import cv2
import os
import numpy as np
import pandas as pd
import datetime

# ==============================================================================
# 1. PARAMETER UNTUK TUNING
# ==============================================================================
BBOX_SIZE = 400 # Ukuran sisi bounding square (dalam piksel). Sesuaikan jika target bergerak sangat cepat.
MIN_AREA = 50    # Area minimum kontur agar dianggap sebagai target. Naikkan jika mendeteksi noise.

# ==============================================================================
# 2. FUNGSI-FUNGSI BANTU
# ==============================================================================

### FUNGSI DETEKSI BARU: Logika Dua Langkah (Sensitif -> Kuat) ###
def detect_gaze_with_ellipse_fitting(bgr_frame_roi, min_area=50):
    """
    Mendeteksi gaze dengan logika dua langkah yang adaptif:
    1. Coba deteksi dengan sensitivitas tinggi untuk garis tipis (fiksasi).
    2. Jika gagal, coba lagi dengan pembersihan noise yang lebih kuat untuk target bergerak.
    """
    hsv_roi = cv2.cvtColor(bgr_frame_roi, cv2.COLOR_BGR2HSV)
    
    # --- STRATEGI 1: Pengaturan Sangat Sensitif untuk Garis Tipis ---
    lower_cyan_sensitive = np.array([80, 40, 40]) # S dan V lebih rendah
    upper_cyan_sensitive = np.array([100, 255, 255])
    mask_sensitive = cv2.inRange(hsv_roi, lower_cyan_sensitive, upper_cyan_sensitive)
    
    # Gunakan kernel yang lebih kecil dan nonaktifkan MORPH_OPEN
    kernel_small = np.ones((3,3), np.uint8)
    mask_sensitive = cv2.dilate(mask_sensitive, kernel_small, iterations=1)
    
    contours, _ = cv2.findContours(mask_sensitive, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest_contour) >= min_area and len(largest_contour) >= 5:
            ellipse = cv2.fitEllipse(largest_contour)
            cx, cy = int(ellipse[0][0]), int(ellipse[0][1])
            # Visualisasikan elips pada mask untuk debugging
            cv2.ellipse(mask_sensitive, ellipse, (255, 255, 255), 2)
            return (cx, cy), mask_sensitive, largest_contour

    # --- STRATEGI 2: Jika Strategi 1 Gagal, Gunakan Pengaturan Kuat (Lama) ---
    # Ini akan berjalan jika tidak ada kontur valid yang ditemukan di atas
    # (Pengaturan ini lebih baik untuk membersihkan 'ekor' saat target bergerak)
    lower_cyan_robust = np.array([80, 50, 20])
    upper_cyan_robust = np.array([100, 255, 255])
    mask_robust = cv2.inRange(hsv_roi, lower_cyan_robust, upper_cyan_robust)
    
    kernel_open = np.ones((5,5), np.uint8)
    kernel_dilate = np.ones((7,7), np.uint8)
    mask_robust = cv2.morphologyEx(mask_robust, cv2.MORPH_OPEN, kernel_open, iterations=1)
    mask_robust = cv2.dilate(mask_robust, kernel_dilate, iterations=2)
    mask_robust = cv2.morphologyEx(mask_robust, cv2.MORPH_CLOSE, kernel_open, iterations=1)
    
    contours, _ = cv2.findContours(mask_robust, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None, mask_robust, None # Kembalikan mask terakhir untuk visualisasi

    largest_contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest_contour) < min_area or len(largest_contour) < 5:
        return None, mask_robust, None
        
    ellipse = cv2.fitEllipse(largest_contour)
    cx, cy = int(ellipse[0][0]), int(ellipse[0][1])
    cv2.ellipse(mask_robust, ellipse, (255, 255, 255), 2)
    # Kembalikan juga kontur terbesar untuk dianalisis
    return (cx, cy), mask_robust, largest_contour

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
input_video = input(f"Masukkan path video: ").strip().strip('"')
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

### PERUBAHAN DI SINI: Inisialisasi Kalman Filter ###
kalman = cv2.KalmanFilter(4, 2) # 4 state (x, y, dx, dy), 2 measurement (x, y)
kalman.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
kalman.transitionMatrix = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)
kalman.processNoiseCov = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32) * 5
kalman.measurementNoiseCov = np.array([[1, 0], [0, 1]], np.float32) * 0.1
kalman_initialized = False

# ==============================================================================
# 4. PEMROSESAN UTAMA DENGAN VISUALISASI
# ==============================================================================
print("Memulai pemrosesan video dengan visualisasi real-time...")
print("Tekan 'q' pada jendela video untuk menghentikan proses.")

gaze_data = []
frame_index = 0
bbox = None 

# Loop Utama yang Direvisi Total
while True:
    success, frame = vid.read()
    if not success:
        break
    
    # --- TAHAP 1: DETEKSI OBJEK ---
    detected_coords_roi, binary_viz, detected_contour_roi = None, np.zeros((100, 100), dtype=np.uint8), None
    roi_origin = (0, 0)
    
    if bbox:
        x1, y1 = max(0, bbox[0] - BBOX_SIZE // 2), max(0, bbox[1] - BBOX_SIZE // 2)
        x2, y2 = min(width, bbox[0] + BBOX_SIZE // 2), min(height, bbox[1] + BBOX_SIZE // 2)
        roi_origin = (x1, y1)
        if y1 < y2 and x1 < x2:
            roi_bgr = frame[y1:y2, x1:x2]
            detected_coords_roi, binary_viz, detected_contour_roi = detect_gaze_with_ellipse_fitting(roi_bgr, MIN_AREA)
    else:
        detected_coords_roi, binary_viz, detected_contour_roi = detect_gaze_with_ellipse_fitting(frame, MIN_AREA)

    # --- TAHAP 2: KALKULASI & PREDIKSI ---
    
    # Prediksi dasar dari Kalman Filter
    prediction = kalman.predict()
    predicted_coords = (int(prediction[0,0]), int(prediction[1,0]))
    
    # Inisialisasi variabel untuk frame ini
    final_detected_coords = None
    nudged_coords = predicted_coords # Secara default, prediksi yang di-nudge sama dengan prediksi dasar
    
    if detected_coords_roi:
        # Konversi koordinat deteksi mentah ke frame penuh
        final_detected_coords = (detected_coords_roi[0] + roi_origin[0], detected_coords_roi[1] + roi_origin[1])
        
        # Inisialisasi atau koreksi Kalman Filter dengan deteksi mentah
        measurement = np.array([[np.float32(final_detected_coords[0])], [np.float32(final_detected_coords[1])]])
        if not kalman_initialized:
            kalman.statePost = np.array([measurement[0,0], measurement[1,0], 0, 0], np.float32)
            kalman_initialized = True
        else:
            kalman.correct(measurement)
        
        # --- LOGIKA TRIPWIRE & NUDGE ---
        if detected_contour_roi is not None:
            # Pindahkan kontur dari koordinat ROI ke koordinat frame penuh
            contour_full_frame = detected_contour_roi + roi_origin
            
            # 1. Cari lingkaran "tripwire" yang pas
            (geom_center_x, geom_center_y), radius = cv2.minEnclosingCircle(contour_full_frame)
            geom_center_full = (geom_center_x, geom_center_y)
            
            # 2. Hitung vektor dari pusat geometris ke pusat deteksi (yang menunjuk ke ekor)
            vec_x = final_detected_coords[0] - geom_center_full[0]
            vec_y = final_detected_coords[1] - geom_center_full[1]
            
            # 3. "Dorong" prediksi Kalman ke arah berlawanan dari vektor (menuju kepala)
            NUDGE_FACTOR = 1.0 # Anda bisa tuning nilai ini
            nudged_x = predicted_coords[0] - (vec_x * NUDGE_FACTOR)
            nudged_y = predicted_coords[1] - (vec_y * NUDGE_FACTOR)
            nudged_coords = (int(nudged_x), int(nudged_y))
            

    # Perbarui bbox untuk frame berikutnya berdasarkan prediksi yang sudah di-nudge
    if final_detected_coords:
        bbox = nudged_coords
    else:
        bbox = None
        
    # --- TAHAP 3: SIMPAN DATA & VISUALISASI ---
    gaze_data.append({
        'frame': frame_index,
        'detected_x': final_detected_coords[0] if final_detected_coords else None,
        'detected_y': final_detected_coords[1] if final_detected_coords else None,
        'predicted_x': nudged_coords[0],
        'predicted_y': nudged_coords[1]
    })
    
    viz_original = frame.copy()
    
    # Gambar Bounding Box Pencarian (Biru)
    if bbox:
        x1_b, y1_b = max(0, bbox[0] - BBOX_SIZE // 2), max(0, bbox[1] - BBOX_SIZE // 2)
        x2_b, y2_b = min(width, bbox[0] + BBOX_SIZE // 2), min(height, bbox[1] + BBOX_SIZE // 2)
        cv2.rectangle(viz_original, (x1_b, y1_b), (x2_b, y2_b), (255, 100, 0), 2) # Biru
        
    # Gambar Titik Deteksi Mentah (Hijau)
    if final_detected_coords:
        draw_crosshair(viz_original, final_detected_coords[0], final_detected_coords[1], (0, 255, 0)) # Hijau
    
    # Gambar Lingkaran "Tripwire" (Ungu)
    if detected_contour_roi is not None:
        contour_full_frame = detected_contour_roi + roi_origin
        (geom_center_x, geom_center_y), radius = cv2.minEnclosingCircle(contour_full_frame)
        # Gambar lingkaran "tripwire"
        cv2.circle(viz_original, (int(geom_center_x), int(geom_center_y)), int(radius), (255, 0, 255), 1) # Ungu tipis
        
    # Gambar Lingkaran Prediksi Akhir (Putih)
    overlay = viz_original.copy()
    cv2.circle(overlay, nudged_coords, 75, (255, 255, 255), -1) # Putih
    viz_original = cv2.addWeighted(overlay, 0.6, viz_original, 0.4, 0)
    
    annotate_frame(viz_original, frame_index, final_detected_coords)
    cv2.imshow('Original Video + Tracking', viz_original)
    
    # Jendela 2: Proses Deteksi
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

print("\nPemrosesan selesai.")

# === PENYIMPANAN & PEMBERSIHAN ===
df = pd.DataFrame(gaze_data)
df.to_csv(output_csv_path, index=False)
print(f"Data CSV telah disimpan di: {output_csv_path}")

vid.release()
out.release()
cv2.destroyAllWindows()
print(f"Video dengan overlay telah disimpan di: {output_video_path}")