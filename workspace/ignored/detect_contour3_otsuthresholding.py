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
def detect_gaze_universal(roi_gray):
    """
    Mendeteksi gaze menggunakan Otsu's Thresholding yang adaptif terhadap kecerahan.
    Bekerja untuk bentuk solid maupun outline dengan warna apa pun.
    Mengembalikan koordinat dan citra biner untuk visualisasi.
    """
    # Otsu's Binarization secara otomatis menemukan threshold terbaik.
    _, binary_img = cv2.threshold(roi_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Sedikit proses pembersihan untuk menghilangkan noise
    kernel = np.ones((5,5),np.uint8)
    binary_img = cv2.morphologyEx(binary_img, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None, binary_img # Kembalikan gambar biner meskipun tidak ada kontur

    largest_contour = max(contours, key=cv2.contourArea)
    
    if cv2.contourArea(largest_contour) < MIN_AREA:
        return None, binary_img

    moments = cv2.moments(largest_contour)
    if moments['m00'] != 0:
        cx = int(moments['m10'] / moments['m00'])
        cy = int(moments['m01'] / moments['m00'])
        return (cx, cy), binary_img
        
    return None, binary_img

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

# ==============================================================================
# 4. PEMROSESAN UTAMA DENGAN VISUALISASI
# ==============================================================================
print("Memulai pemrosesan video dengan visualisasi real-time...")
print("Tekan 'q' pada jendela video untuk menghentikan proses.")

gaze_data = []
frame_index = 0
bbox = None # Variabel untuk menyimpan posisi bounding box

while True:
    success, frame = vid.read()
    if not success:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # --- LOGIKA TRACKING-BY-DETECTION ---
    
    # 1. Tentukan Region of Interest (ROI)
    if bbox:
        x1, y1 = max(0, bbox[0] - BBOX_SIZE // 2), max(0, bbox[1] - BBOX_SIZE // 2)
        x2, y2 = min(width, bbox[0] + BBOX_SIZE // 2), min(height, bbox[1] + BBOX_SIZE // 2)
        roi_gray = gray[y1:y2, x1:x2]
        roi_origin = (x1, y1)
    else:
        # Jika bbox belum ada (awal atau setelah kehilangan jejak), cari di seluruh frame
        roi_gray = gray
        roi_origin = (0, 0)

    # 2. Deteksi Gaze di dalam ROI
    detected_coords_roi, binary_viz = detect_gaze_universal(roi_gray)
    
    # 3. Perbarui Posisi & Bounding Box
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
        cv2.rectangle(viz_original, (x1_b, y1_b), (x2_b, y2_b), (255, 0, 0), 2) # Kotak biru
        
    if final_coords:
        draw_crosshair(viz_original, final_coords[0], final_coords[1], (0, 255, 0)) # Titik hijau
    
    annotate_frame(viz_original, frame_index, final_coords)
    cv2.imshow('Original Video + Tracking', viz_original)
    
    # Jendela 2: Proses Deteksi (Citra Biner)
    # Ubah citra biner menjadi 3 channel agar bisa diberi warna
    binary_viz_color = cv2.cvtColor(binary_viz, cv2.COLOR_GRAY2BGR)
    if detected_coords_roi:
        # Gambar titik deteksi di dalam citra biner
        draw_crosshair(binary_viz_color, detected_coords_roi[0], detected_coords_roi[1], (0, 0, 255)) # Titik merah
    cv2.imshow('Detection Process (Binary)', binary_viz_color)
    
    # Tulis ke video output
    out.write(viz_original)
    
    frame_index += 1
    print(f"Memproses frame {frame_index}/{total_frames}", end='\r')

    # Tunggu tombol 'q' untuk keluar
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