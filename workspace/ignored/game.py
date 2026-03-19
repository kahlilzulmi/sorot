import cv2
import numpy as np
import time
import mss
import pygetwindow as gw
import pygame

# ==============================================================================
# 1. PARAMETER UTAMA UNTUK TUNING
# ==============================================================================
### PERUBAHAN DI SINI: Tentukan nomor indeks kamera Anda ###
# 0 biasanya webcam internal. Coba 1, 2, dst. jika OBS bukan yang pertama.
# Anda bisa menemukan indeks yang benar dengan menjalankan skrip ini; ia akan mencetak daftar kamera.
INDEX_KAMERA_VIRTUAL = 0

# --- Parameter untuk Hough Circle Transform ---
HOUGH_PARAM1 = 50
HOUGH_PARAM2 = 13
MIN_RADIUS = 70
MAX_RADIUS = 75

# --- Pengaturan Game ---
DURASI_HOVER_UNTUK_KLIK = 4.0
DURASI_HOVER_KELUAR = 2.0

# --- Skema Warna (Pygame menggunakan format RGB) ---
WARNA_DARK = {
    "latar": (20, 20, 20), "teks_soal": (220, 220, 220), "teks_biasa": (255, 255, 255),
    "tombol": (50, 50, 50), "hover": (80, 80, 80), "outline": (150, 150, 150),
}
WARNA_LIGHT = {
    "latar": (235, 235, 235), "teks_soal": (10, 10, 10), "teks_biasa": (0, 0, 0),
    "tombol": (200, 200, 200), "hover": (170, 170, 170), "outline": (100, 100, 100),
}
WARNA_PROGRESS = (0, 255, 0)
WARNA_BENAR = (0, 180, 0)
WARNA_SALAH = (255, 0, 0)
WARNA_CURSOR = (255, 255, 0)
WARNA_KELUAR = (150, 10, 10)

# --- Konten Soal ---
SOAL_MATEMATIKA = [
    {"soal": "8 x 7 = 56", "jawaban": "benar"}, {"soal": "125 + 275 = 400", "jawaban": "benar"},
    {"soal": "99 - 19 = 70", "jawaban": "salah"}, {"soal": "36 / 6 = 6", "jawaban": "benar"},
    {"soal": "5^2 = 20", "jawaban": "salah"}, {"soal": "7 x 7 = 49", "jawaban": "benar"},
]

# ==============================================================================
# 2. FUNGSI DETEKSI & KALMAN FILTER (Logika OpenCV tetap di sini)
# ==============================================================================

def detect_gaze_circle_hough(bgr_frame):
    gray_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
    gray_frame = cv2.medianBlur(gray_frame, 5)
    circles = cv2.HoughCircles(
        gray_frame, cv2.HOUGH_GRADIENT, dp=1, minDist=1000,
        param1=HOUGH_PARAM1, param2=HOUGH_PARAM2, minRadius=MIN_RADIUS, maxRadius=MAX_RADIUS
    )
    if circles is not None:
        circle = np.uint16(np.around(circles[0, 0]))
        return {"center": (int(circle[0]), int(circle[1])), "radius": int(circle[2])}
    return None

kalman = cv2.KalmanFilter(4, 2)
kalman.measurementMatrix = np.array([[1,0,0,0],[0,1,0,0]], np.float32)
kalman.transitionMatrix = np.array([[1,0,1,0],[0,1,0,1],[0,0,1,0],[0,0,0,1]], np.float32)
kalman.processNoiseCov = np.array([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]], np.float32) * 0.1
kalman.measurementNoiseCov = np.array([[1,0],[0,1]], np.float32) * 1.0
kalman_initialized = False

# ==============================================================================
# 3. FUNGSI GAME & VISUALISASI (Menggunakan Pygame)
# ==============================================================================

def draw_button_pygame(screen, button_key, is_hovered, hover_progress, warna, font):
    btn = TOMBOL[button_key]
    rect = pygame.Rect(btn["pos"][0], btn["pos"][1], btn["size"][0], btn["size"][1])
    btn_color = warna["hover"] if is_hovered else warna["tombol"]
    if button_key == "keluar": btn_color = WARNA_KELUAR
    
    pygame.draw.rect(screen, btn_color, rect)
    pygame.draw.rect(screen, warna["outline"], rect, 2)

    text_surf = font.render(btn["teks"], True, warna["teks_biasa"])
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)

    if is_hovered and hover_progress > 0:
        progress_width = int(rect.width * hover_progress)
        progress_color = WARNA_SALAH if button_key == "keluar" else WARNA_PROGRESS
        pygame.draw.rect(screen, progress_color, (rect.left, rect.bottom - 10, progress_width, 10))

def is_point_in_rect(point, rect_pos, rect_size):
    return rect_pos[0] <= point[0] <= rect_pos[0] + rect_size[0] and \
           rect_pos[1] <= point[1] <= rect_pos[1] + rect_size[1]

# ==============================================================================
# 4. SETUP UTAMA & LOOP GAME
# ==============================================================================

# Inisialisasi Pygame
pygame.init()
pygame.font.init()

# Setup layar fullscreen yang adaptif
screen_info = pygame.display.Info()
LEBAR_LAYAR, TINGGI_LAYAR = screen_info.current_w, screen_info.current_h
screen = pygame.display.set_mode((LEBAR_LAYAR, TINGGI_LAYAR), pygame.FULLSCREEN)
pygame.display.set_caption("Game Matematika Eye-Tracker")

# Setup Font Pygame
font_soal = pygame.font.SysFont('Arial', 80)
font_jawaban = pygame.font.SysFont('Arial', 30)
font_skor = pygame.font.SysFont('Arial', 40)
font_tombol_normal = pygame.font.SysFont('Arial', 50)
font_tombol_keluar = pygame.font.SysFont('Arial', 30)
font_final = pygame.font.SysFont('Arial', 60)

# Menyesuaikan posisi tombol dengan resolusi layar
TOMBOL = {
    "benar": {"teks": "BENAR", "pos": (LEBAR_LAYAR - 400, TINGGI_LAYAR * 0.4), "size": (300, 150)},
    "salah": {"teks": "SALAH", "pos": (LEBAR_LAYAR - 400, TINGGI_LAYAR * 0.6), "size": (300, 150)},
    "keluar": {"teks": "KELUAR", "pos": (LEBAR_LAYAR // 2 - 125, 40), "size": (250, 80)},
}
POSISI_AWAL_SOAL_Y = TINGGI_LAYAR * 0.2
JARAK_ANTAR_SOAL = 150

### PERUBAHAN DI SINI: Setup penangkapan dari Kamera Virtual ###
# Hapus mss dan pygetwindow
cap = cv2.VideoCapture(INDEX_KAMERA_VIRTUAL)
if not cap.isOpened():
    print(f"ERROR: Tidak bisa membuka kamera dengan indeks {INDEX_KAMERA_VIRTUAL}.")
    print("Pastikan OBS Virtual Camera sudah berjalan.")
    # Fallback ke simulasi mouse jika kamera gagal
    use_mouse_fallback = True
    print("PERINGATAN: Fallback ke simulasi mouse.")
else:
    use_mouse_fallback = False
    print("Kamera virtual berhasil terdeteksi.")
    cv2.namedWindow("Eye Tracker Feed (from OBS)", cv2.WINDOW_NORMAL)

# Inisialisasi state game
history_soal, current_question_index, score = [], 0, 0
mode_gelap = True
hovered_button_key, hover_start_time = None, 0
game_running = True
clock = pygame.time.Clock()

while game_running:
    # --- TAHAP 1: EVENT HANDLING ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT: game_running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q: game_running = False
            if event.key == pygame.K_b: mode_gelap = not mode_gelap

    # --- TAHAP 2: TANGKAP & DETEKSI GAZE ---
    gaze_pos = pygame.mouse.get_pos() # Default ke mouse
    
    if not use_mouse_fallback:
        success, img_bgr = cap.read()
        if success:
            # Balik gambar secara horizontal karena webcam biasanya terbalik
            img_bgr = cv2.flip(img_bgr, 1)
            
            # Tampilkan feed di jendela debug
            cv2.imshow("Eye Tracker Feed (from OBS)", img_bgr)
            
            circle_info = detect_gaze_circle_hough(img_bgr)
            if circle_info:
                # Sesuaikan koordinat dari resolusi kamera ke resolusi layar
                cam_width, cam_height = img_bgr.shape[1], img_bgr.shape[0]
                detected_x = int(circle_info["center"][0] * (LEBAR_LAYAR / cam_width))
                detected_y = int(circle_info["center"][1] * (TINGGI_LAYAR / cam_height))
                
                measurement = np.array([[np.float32(detected_x)], [np.float32(detected_y)]])
                if not kalman_initialized:
                    kalman.statePost = np.array([measurement[0,0], measurement[1,0], 0, 0], np.float32)
                    kalman_initialized = True
                else:
                    kalman.correct(measurement)
        if kalman_initialized:
            prediction = kalman.predict()
            gaze_pos = (int(prediction[0,0]), int(prediction[1,0]))

    # --- TAHAP 3: LOGIKA GAME ---
    # (Tidak ada perubahan di sini)
    currently_hovering = None
    for key, btn in TOMBOL.items():
        if is_point_in_rect(gaze_pos, btn["pos"], btn["size"]):
            currently_hovering = key
            break
    
    if currently_hovering:
        if currently_hovering != hovered_button_key:
            hovered_button_key, hover_start_time = currently_hovering, time.time()
        
        click_duration = DURASI_HOVER_KELUAR if hovered_button_key == "keluar" else DURASI_HOVER_UNTUK_KLIK
        if time.time() - hover_start_time >= click_duration:
            if hovered_button_key == "keluar": game_running = False
            elif current_question_index < len(SOAL_MATEMATIKA):
                is_correct = (SOAL_MATEMATIKA[current_question_index]["jawaban"] == hovered_button_key)
                if is_correct: score += 1
                history_soal.append({
                    "soal": SOAL_MATEMATIKA[current_question_index]["soal"],
                    "jawaban_diberikan": hovered_button_key.upper(), "benar": is_correct
                })
                current_question_index += 1
            hovered_button_key, hover_start_time = None, 0
    else:
        hovered_button_key, hover_start_time = None, 0


    # --- TAHAP 4: GAMBAR SEMUA ELEMEN ---
    # (Tidak ada perubahan di sini)
    warna = WARNA_DARK if mode_gelap else WARNA_LIGHT
    screen.fill(warna["latar"])

    # Gambar riwayat
    for i, item in enumerate(history_soal):
        y_pos = POSISI_AWAL_SOAL_Y + (i * JARAK_ANTAR_SOAL)
        soal_surf = font_soal.render(f"{i+1}. {item['soal']}", True, warna["teks_soal"])
        screen.blit(soal_surf, (100, y_pos))
        
        warna_jawaban = WARNA_BENAR if item["benar"] else WARNA_SALAH
        jawaban_surf = font_jawaban.render(f"Jawaban Anda: {item['jawaban_diberikan']}", True, warna_jawaban)
        screen.blit(jawaban_surf, (150, y_pos + 80))

    # Gambar soal saat ini atau layar akhir
    y_pos = POSISI_AWAL_SOAL_Y + (len(history_soal) * JARAK_ANTAR_SOAL)
    if current_question_index < len(SOAL_MATEMATIKA):
        soal_surf = font_soal.render(f"{current_question_index+1}. {SOAL_MATEMATIKA[current_question_index]['soal']}", True, warna["teks_soal"])
        screen.blit(soal_surf, (100, y_pos))
    else:
        final1_surf = font_final.render("PERMAINAN SELESAI!", True, warna["teks_soal"])
        final2_surf = font_skor.render(f"Skor Akhir: {score} / {len(SOAL_MATEMATIKA)}", True, WARNA_PROGRESS)
        screen.blit(final1_surf, (100, y_pos))
        screen.blit(final2_surf, (100, y_pos + 80))

    # Gambar tombol
    for key in TOMBOL:
        if key in ["benar", "salah"] and current_question_index >= len(SOAL_MATEMATIKA): continue
        is_hovered = (key == hovered_button_key)
        progress = 0
        if is_hovered:
            click_duration = DURASI_HOVER_KELUAR if key == "keluar" else DURASI_HOVER_UNTUK_KLIK
            progress = (time.time() - hover_start_time) / click_duration
        
        font_tombol = font_tombol_keluar if key == "keluar" else font_tombol_normal
        draw_button_pygame(screen, key, is_hovered, progress, warna, font_tombol)
    
    # Gambar kursor gaze
    pygame.draw.circle(screen, WARNA_CURSOR, gaze_pos, 15, 2)
    pygame.draw.line(screen, WARNA_CURSOR, (gaze_pos[0]-15, gaze_pos[1]), (gaze_pos[0]+15, gaze_pos[1]), 2)
    pygame.draw.line(screen, WARNA_CURSOR, (gaze_pos[0], gaze_pos[1]-15), (gaze_pos[0], gaze_pos[1]+15), 2)
    
    # Update layar
    pygame.display.flip()
    
    # Cek input keyboard (termasuk untuk jendela OpenCV)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'): 
        game_running = False

    clock.tick(60)

pygame.quit()
if not use_mouse_fallback:
    cap.release()
cv2.destroyAllWindows()
print("Game ditutup.")

