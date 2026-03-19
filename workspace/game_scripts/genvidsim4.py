import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import time
from tqdm import tqdm

print("Memulai proses pembuatan video stimulus (versi countdown)...")

# ==============================================================================
# 1. KONFIGURASI UTAMA
# ==============================================================================
# Spesifikasi Video
WIDTH, HEIGHT = 1920, 1080
FPS = 60
OUTPUT_FILENAME = "stimulus_video5_no_crosshair_white.mp4" # Ubah nama file output sesuai kebutuhan

# Tampilan
BACKGROUND_COLOR = (0, 0, 0)
TARGET_COLOR = (255, 255, 255)
CROSSHAIR_COLOR = (0, 0, 0)
TEXT_COLOR = (255, 255, 255)
OVERLAY_BG_COLOR = (0, 0, 0)
OVERLAY_ALPHA = 0.5
COUNTDOWN_COLOR = (255, 255, 255) # Putih untuk countdown visual

# Font
FONT_PATH = "arial.ttf"
try:
    FONT_INFO_TITLE = ImageFont.truetype(FONT_PATH, 28)
    FONT_INFO_CONTENT = ImageFont.truetype(FONT_PATH, 32)
    FONT_COORDS = ImageFont.truetype(FONT_PATH, 22)
    FONT_FULLSCREEN = ImageFont.truetype(FONT_PATH, 50)
except IOError:
    print(f"Error: File font '{FONT_PATH}' tidak ditemukan.")
    exit()

# Durasi (dalam detik)
DURASI_PERINTAH = 3
DURASI_PERSIAPAN = 3 # DURASI BARU: Diubah sesuai permintaan Anda
DURASI_BUKA_TUTUP = 5
DURASI_TUTORIAL = 8
DURASI_FIKSASI = 5
DURASI_GERAK_HALUS = 10
DURASI_SAKADIK_PER_TITIK = 3

# Inisialisasi Video Writer
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
video = cv2.VideoWriter(OUTPUT_FILENAME, fourcc, FPS, (WIDTH, HEIGHT))

# ==============================================================================
# 2. FUNGSI-FUNGSI BANTU (HELPER FUNCTIONS)
# ==============================================================================

def bgr_to_rgb(bgr_tuple):
    return (bgr_tuple[2], bgr_tuple[1], bgr_tuple[0])

def draw_text_pil(frame_bgr, text, position, font, color_bgr):
    pil_img = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    draw.text(position, text, font=font, fill=bgr_to_rgb(color_bgr))
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def draw_overlay_info(frame, instruction_text="", timer_text=""):
    overlay = frame.copy()
    cmd_box = (WIDTH - 450, 30, WIDTH - 30, 180)
    timer_box = (WIDTH - 450, HEIGHT - 120, WIDTH - 30, HEIGHT - 30)
    cv2.rectangle(overlay, (cmd_box[0], cmd_box[1]), (cmd_box[2], cmd_box[3]), OVERLAY_BG_COLOR, -1)
    cv2.rectangle(overlay, (timer_box[0], timer_box[1]), (timer_box[2], timer_box[3]), OVERLAY_BG_COLOR, -1)
    cv2.addWeighted(overlay, OVERLAY_ALPHA, frame, 1 - OVERLAY_ALPHA, 0, frame)
    frame = draw_text_pil(frame, "PERINTAH:", (cmd_box[0] + 15, cmd_box[1] + 10), FONT_INFO_TITLE, TEXT_COLOR)
    frame = draw_text_pil(frame, "SISA WAKTU:", (timer_box[0] + 15, timer_box[1] + 10), FONT_INFO_TITLE, TEXT_COLOR)
    y_text = cmd_box[1] + 45
    for line in instruction_text.split('\n'):
        frame = draw_text_pil(frame, line, (cmd_box[0] + 15, y_text), FONT_INFO_CONTENT, TEXT_COLOR)
        y_text += 35
    if timer_text:
        frame = draw_text_pil(frame, timer_text, (timer_box[0] + 15, timer_box[1] + 45), FONT_INFO_CONTENT, TEXT_COLOR)
    return frame

def draw_target_and_coords(frame, center_xy):
    cx, cy = int(center_xy[0]), int(center_xy[1])
    cv2.line(frame, (0, cy), (WIDTH, cy), CROSSHAIR_COLOR, 1)
    cv2.line(frame, (cx, 0), (cx, HEIGHT), CROSSHAIR_COLOR, 1)
    cv2.circle(frame, (cx, cy), 20, TARGET_COLOR, -1)
    cv2.circle(frame, (cx, cy), 5, BACKGROUND_COLOR, -1)
    coord_text = f"X: {cx}\nY: {cy}"
    frame = draw_text_pil(frame, coord_text, (30, 30), FONT_COORDS, TEXT_COLOR)
    return frame

def draw_pie_countdown(frame, center_xy, progress_ratio):
    cx, cy = int(center_xy[0]), int(center_xy[1])
    radius = 30
    start_angle = -90
    end_angle = start_angle + (360 * progress_ratio)
    cv2.ellipse(frame, (cx, cy), (radius, radius), 0, start_angle, end_angle, COUNTDOWN_COLOR, -1)
    return frame

def display_fullscreen_text(text, duration):
    total_frames = duration * FPS
    for _ in tqdm(range(total_frames), desc="Fullscreen Text"):
        frame = np.full((HEIGHT, WIDTH, 3), BACKGROUND_COLOR, dtype=np.uint8)
        lines = text.split('\n')
        total_text_height = sum([FONT_FULLSCREEN.getbbox(line)[3] for line in lines]) + (len(lines) - 1) * 10
        start_y = (HEIGHT - total_text_height) // 2
        current_y = start_y
        for line in lines:
            bbox = FONT_FULLSCREEN.getbbox(line)
            text_width = bbox[2] - bbox[0]
            pos_x = (WIDTH - text_width) // 2
            frame = draw_text_pil(frame, line, (pos_x, current_y), FONT_FULLSCREEN, TEXT_COLOR)
            current_y += bbox[3] + 10
        video.write(frame)

# ==============================================================================
# 3. FUNGSI-FUNGSI TUGAS (TASK FUNCTIONS)
# ==============================================================================

def run_task(instruction, task_func, task_duration, **kwargs):
    for _ in tqdm(range(DURASI_PERINTAH * FPS), desc="Instruction"):
        frame = np.full((HEIGHT, WIDTH, 3), BACKGROUND_COLOR, dtype=np.uint8)
        frame = draw_overlay_info(frame, instruction_text=instruction, timer_text="---")
        video.write(frame)
    task_func(task_duration, instruction_text=instruction, **kwargs)

def action_static_target(duration, instruction_text, position):
    for i in tqdm(range(duration * FPS), desc="Static Target"):
        frame = np.full((HEIGHT, WIDTH, 3), BACKGROUND_COLOR, dtype=np.uint8)
        sisa_waktu = duration - (i / FPS)
        timer_text = f"{sisa_waktu:.1f} s"
        frame = draw_target_and_coords(frame, position)
        frame = draw_overlay_info(frame, instruction_text=instruction_text, timer_text=timer_text)
        video.write(frame)

def action_smooth_pursuit(duration, instruction_text, path_x, path_y):
    # Fase Persiapan
    start_pos = (path_x[0], path_y[0])
    total_prepare_frames = int(DURASI_PERSIAPAN * FPS)
    for i in tqdm(range(total_prepare_frames), desc="Smooth Pursuit Prep"):
        frame = np.full((HEIGHT, WIDTH, 3), BACKGROUND_COLOR, dtype=np.uint8)
        frame = draw_target_and_coords(frame, start_pos)
        progress_ratio = 1 - (i / total_prepare_frames)
        frame = draw_pie_countdown(frame, start_pos, progress_ratio)
        frame = draw_overlay_info(frame, instruction_text=instruction_text, timer_text="Bersiap...")
        video.write(frame)

    # Fase Gerak
    total_move_frames = int(duration * FPS)
    for i in tqdm(range(total_move_frames), desc="Smooth Pursuit Move"):
        frame = np.full((HEIGHT, WIDTH, 3), BACKGROUND_COLOR, dtype=np.uint8)
        sisa_waktu = duration - (i / FPS)
        timer_text = f"{sisa_waktu:.1f} s"
        current_pos = (path_x[i], path_y[i])
        frame = draw_target_and_coords(frame, current_pos)
        frame = draw_overlay_info(frame, instruction_text=instruction_text, timer_text=timer_text)
        video.write(frame)

def action_saccades(duration, instruction_text, points, duration_per_point):
    for point in points:
        for i in tqdm(range(duration_per_point * FPS), desc="Saccade Point"):
            frame = np.full((HEIGHT, WIDTH, 3), BACKGROUND_COLOR, dtype=np.uint8)
            sisa_waktu = duration_per_point - (i / FPS)
            timer_text = f"{sisa_waktu:.1f} s"
            frame = draw_target_and_coords(frame, point)
            frame = draw_overlay_info(frame, instruction_text=instruction_text, timer_text=timer_text)
            video.write(frame)

# ==============================================================================
# 4. EKSEKUSI UTAMA & URUTAN VIDEO
# ==============================================================================
try:
    start_time = time.time()
    
    # Urutan eksekusi tetap sama
    print("Generating: Pembukaan...")
    display_fullscreen_text("Sesi Simulasi Eye Tracking\nakan Segera Dimulai", DURASI_BUKA_TUTUP)
    
    print("Generating: Tutorial...")
    margin = 150
    path_x = np.linspace(margin, WIDTH - margin, DURASI_TUTORIAL * FPS)
    path_y = np.full_like(path_x, HEIGHT // 2)
    run_task("TUTORIAL:\nIkuti pusat target.", action_smooth_pursuit, DURASI_TUTORIAL, path_x=path_x, path_y=path_y)
    
    print("Generating: Tugas Fiksasi...")
    center_point = (WIDTH // 2, HEIGHT // 2)
    run_task("TUGAS 1: FIKSASI\nTatap pusat target.", action_static_target, DURASI_FIKSASI, position=center_point)
    
    print("Generating: Tugas Gerak Halus...")
    path_x_ltr = np.linspace(margin, WIDTH - margin, int(DURASI_GERAK_HALUS * FPS))
    path_y_h = np.full_like(path_x_ltr, HEIGHT // 2)
    run_task("TUGAS 2a: HORIZONTAL\nKiri ke Kanan.", action_smooth_pursuit, DURASI_GERAK_HALUS, path_x=path_x_ltr, path_y=path_y_h)
    run_task("TUGAS 2b: HORIZONTAL\nKanan ke Kiri.", action_smooth_pursuit, DURASI_GERAK_HALUS, path_x=path_x_ltr[::-1], path_y=path_y_h)
    
    path_y_ttb = np.linspace(margin, HEIGHT - margin, int(DURASI_GERAK_HALUS * FPS))
    path_x_v = np.full_like(path_y_ttb, WIDTH // 2)
    run_task("TUGAS 3a: VERTIKAL\nAtas ke Bawah.", action_smooth_pursuit, DURASI_GERAK_HALUS, path_x=path_x_v, path_y=path_y_ttb)
    run_task("TUGAS 3b: VERTIKAL\nBawah ke Atas.", action_smooth_pursuit, DURASI_GERAK_HALUS, path_x=path_x_v, path_y=path_y_ttb[::-1])
    
    radius = (HEIGHT // 2) - margin
    t = np.linspace(0, 2 * np.pi * 2, int(DURASI_GERAK_HALUS * FPS))
    path_x_cw = center_point[0] + radius * np.cos(t)
    path_y_cw = center_point[1] + radius * np.sin(t)
    run_task("TUGAS 4a: MELINGKAR\nSearah Jarum Jam.", action_smooth_pursuit, DURASI_GERAK_HALUS, path_x=path_x_cw, path_y=path_y_cw)
    run_task("TUGAS 4b: MELINGKAR\nBerlawanan Arah.", action_smooth_pursuit, DURASI_GERAK_HALUS, path_x=path_x_cw, path_y=path_y_cw[::-1])
    
    print("Generating: Tugas Sakadik...")
    margin_sacc = 200
    points_structured = [ (margin_sacc, margin_sacc), (WIDTH - margin_sacc, margin_sacc), (WIDTH - margin_sacc, HEIGHT - margin_sacc), (margin_sacc, HEIGHT - margin_sacc), center_point ]
    run_task("TUGAS 5a: SAKADIK\nTERSTRUKTUR.", action_saccades, 0, points=points_structured, duration_per_point=DURASI_SAKADIK_PER_TITIK)
    
    points_random = [ (WIDTH - margin_sacc, margin_sacc), (margin_sacc, HEIGHT - margin_sacc), (WIDTH // 2, margin_sacc), (WIDTH - margin_sacc, HEIGHT // 2), center_point ]
    run_task("TUGAS 5b: SAKADIK\nACAK.", action_saccades, 0, points=points_random, duration_per_point=DURASI_SAKADIK_PER_TITIK)
    
    print("Generating: Penutup...")
    display_fullscreen_text("Sesi Selesai.\nTerima Kasih.", DURASI_BUKA_TUTUP)

    end_time = time.time()
    print("-" * 50)
    print("Video stimulus berhasil dibuat!")
    print(f"Nama File: {OUTPUT_FILENAME}")
    print(f"Resolusi: {WIDTH}x{HEIGHT} @ {FPS} FPS")
    print(f"Total waktu pembuatan: {end_time - start_time:.2f} detik")
    print("-" * 50)

finally:
    video.release()