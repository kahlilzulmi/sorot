import cv2
import os
import numpy as np
import pandas as pd
import datetime

# ==============================================================================
# 1. PARAMETER UTAMA UNTUK TUNING
# ==============================================================================
# Ukuran area pencarian. Cukup besar untuk menangani lompatan sakadik.
BBOX_SIZE = 500
# Jarak maksimum (dalam piksel) dari prediksi agar deteksi dianggap valid.
# NAIKKAN nilai ini jika prediksi (lingkaran putih) gagal mengikuti gerakan cepat.
VALIDATION_RADIUS = 300

# --- Parameter untuk Hough Circle Transform ---
# Diatur sesuai feedback Anda untuk akurasi maksimal.
HOUGH_PARAM1 = 50
HOUGH_PARAM2 = 13
MIN_RADIUS = 70
MAX_RADIUS = 75

# ==============================================================================
# 2. FUNGSI-FUNGSI BANTU
# ==============================================================================

# (Fungsi detect_gaze_circle_hough, draw_crosshair, annotate_frame tetap sama
# seperti pada versi sebelumnya dan tidak perlu diubah)

def detect_gaze_circle_hough(bgr_frame):
    """
    Mendeteksi 'lingkaran sejati' menggunakan Hough Circle Transform.
    """
    gray_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
    gray_frame = cv2.medianBlur(gray_frame, 5)
    circles = cv2.HoughCircles(
        gray_frame, cv2.HOUGH_GRADIENT, dp=1, minDist=gray_frame.shape[0],
        param1=HOUGH_PARAM1, param2=HOUGH_PARAM2,
        minRadius=MIN_RADIUS, maxRadius=MAX_RADIUS
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
input_video = "2025-09-10_10-05-50.mkv" # Ganti dengan nama file video Anda
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

# Inisialisasi Kalman Filter (pengaturan diubah untuk keseimbangan antara halus dan responsif)
kalman = cv2.KalmanFilter(4, 2)
kalman.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
kalman.transitionMatrix = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)
# processNoiseCov: Seberapa percaya pada model gerakan. Nilai lebih tinggi = lebih responsif.
kalman.processNoiseCov = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32) * 1.0
# measurementNoiseCov: Seberapa percaya pada deteksi. Nilai lebih rendah = lebih percaya.
kalman.measurementNoiseCov = np.array([[1, 0], [0, 1]], np.float32) * 0.5
kalman_initialized = False

# ==============================================================================
# 4. PEMROSESAN UTAMA DENGAN VISUALISASI
# ==============================================================================
print("Memulai pemrosesan video dengan deteksi divalidasi...")
print("Tekan 'q' pada jendela video untuk menghentikan proses.")

gaze_data = []
frame_index = 0
bbox_center = None

# Loop Utama Final dengan ROI dan Gerbang Validasi
while True:
    success, frame = vid.read()
    if not success:
        break

    # --- TAHAP 1: PREDIKSI & PERSIAPAN DETEKSI ---
    prediction = kalman.predict()
    predicted_coords = (int(prediction[0,0]), int(prediction[1,0]))

    # Tentukan area pencarian (ROI) berdasarkan prediksi
    if not kalman_initialized:
        # Jika belum diinisialisasi, cari di seluruh frame
        roi_bgr = frame
        roi_origin = (0, 0)
    else:
        # Jika sudah berjalan, cari di dalam Bounding Box di sekitar prediksi
        bbox_center = predicted_coords
        x1, y1 = max(0, bbox_center[0] - BBOX_SIZE // 2), max(0, bbox_center[1] - BBOX_SIZE // 2)
        x2, y2 = min(width, bbox_center[0] + BBOX_SIZE // 2), min(height, bbox_center[1] + BBOX_SIZE // 2)
        roi_origin = (x1, y1)
        if y1 < y2 and x1 < x2:
            roi_bgr = frame[y1:y2, x1:x2]
        else:
            roi_bgr = frame # Fallback jika bbox aneh
            roi_origin = (0,0)


    # --- TAHAP 2: DETEKSI & VALIDASI ---
    circle_info, viz_process_img = detect_gaze_circle_hough(roi_bgr)

    detected_coords = None
    is_detection_valid = False
    if circle_info:
        detected_coords = (circle_info["center"][0] + roi_origin[0], circle_info["center"][1] + roi_origin[1])
        
        # Gerbang Validasi: Cek jarak antara deteksi dan prediksi
        distance = np.linalg.norm(np.array(detected_coords) - np.array(predicted_coords))
        if distance < VALIDATION_RADIUS:
            is_detection_valid = True

    # --- TAHAP 3: KOREKSI KALMAN FILTER ---
    if is_detection_valid:
        # Jika deteksi valid, koreksi filter
        measurement = np.array([[np.float32(detected_coords[0])], [np.float32(detected_coords[1])]])
        if not kalman_initialized:
            kalman.statePost = np.array([measurement[0,0], measurement[1,0], 0, 0], np.float32)
            kalman_initialized = True
        else:
            kalman.correct(measurement)

    # Posisi final yang akan digambar adalah state terakhir dari Kalman Filter
    final_coords = (int(kalman.statePost[0]), int(kalman.statePost[1]))

    # --- TAHAP 4: SIMPAN DATA & VISUALISASI ---
    gaze_data.append({
        'frame': frame_index,
        'detected_x': detected_coords[0] if is_detection_valid else None, # Hanya simpan deteksi yang valid
        'detected_y': detected_coords[1] if is_detection_valid else None,
        'predicted_x': final_coords[0],
        'predicted_y': final_coords[1]
    })

    viz_original = frame.copy()

    # Gambar Bounding Box Pencarian (Biru)
    if bbox_center:
        x1_b, y1_b = max(0, bbox_center[0] - BBOX_SIZE // 2), max(0, bbox_center[1] - BBOX_SIZE // 2)
        x2_b, y2_b = min(width, bbox_center[0] + BBOX_SIZE // 2), min(height, bbox_center[1] + BBOX_SIZE // 2)
        cv2.rectangle(viz_original, (x1_b, y1_b), (x2_b, y2_b), (255, 100, 0), 1)

    # Gambar Gerbang Validasi (Kuning)
    if kalman_initialized:
        cv2.circle(viz_original, predicted_coords, VALIDATION_RADIUS, (0, 255, 255), 1)

    # Gambar Titik Deteksi Mentah (Hijau) - jika valid
    if is_detection_valid:
        draw_crosshair(viz_original, detected_coords[0], detected_coords[1], (0, 255, 0))

    # Gambar Lingkaran Prediksi Akhir (Putih Transparan)
    overlay = viz_original.copy()
    predicted_radius = circle_info["radius"] if circle_info and is_detection_valid else 72
    cv2.circle(overlay, final_coords, predicted_radius, (255, 255, 255), 3)
    viz_original = cv2.addWeighted(overlay, 0.7, viz_original, 0.3, 0)

    annotate_frame(viz_original, frame_index, detected_coords if is_detection_valid else None)
    cv2.imshow('Original Video + Tracking', viz_original)

    # Jendela 2: Proses Deteksi
    viz_process_color = cv2.cvtColor(viz_process_img, cv2.COLOR_GRAY2BGR)
    if circle_info:
        cv2.circle(viz_process_color, circle_info["center"], circle_info["radius"], (0, 255, 0), 2)
        draw_crosshair(viz_process_color, circle_info["center"][0], circle_info["center"][1], (0, 0, 255))
    cv2.imshow('Detection Process (Grayscale)', viz_process_color)

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