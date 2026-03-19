import cv2
import numpy as np
import time
import pygame
import pandas as pd
import datetime
import os
import matplotlib.pyplot as plt

# region PARAMETER UTAMA
# ==============================================================================
# 1. PARAMETER UTAMA UNTUK TUNING
# ==============================================================================
INDEX_KAMERA_VIRTUAL = 0

# --- Plotting Parameters ---
HIST_BINS = 30
HIST_COLOR = 'green'
HIST_ALPHA = 0.7
GAZE_SCATTER_COLOR = 'blue'
GAZE_SCATTER_ALPHA = 0.5
GAZE_SCATTER_SIZE = 10
PLOT_FIGURE_SIZE = (10, 6)

# --- Parameter untuk Hough Circle Transform ---
HOUGH_PARAM1 = 50
HOUGH_PARAM2 = 13
MIN_RADIUS = 65
MAX_RADIUS = 80

# --- Pengaturan Game ---
DURASI_HOVER_UNTUK_KLIK = 3.0
DURASI_HOVER_KELUAR = 3.0

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
WARNA_MULAI = (0, 150, 255)

# --- Soal Latihan (Trial) - Tidak direkam ---
SOAL_LATIHAN = [
    {"soal": "1 + 1 = 2", "jawaban": "benar"},
    {"soal": "2 + 2 = 5", "jawaban": "salah"}
]

# --- Soal Utama (Main) - Direkam ---
SOAL_MATEMATIKA = [
    {"soal": "8 x 7 = 56", "jawaban": "benar"},
    {"soal": "125 + 275 = 400", "jawaban": "benar"},
    {"soal": "99 - 19 = 70", "jawaban": "salah"},
    {"soal": "36 / 6 = 6", "jawaban": "benar"},
    {"soal": "5² = 20", "jawaban": "salah"},
    {"soal": "7 x 7 = 49", "jawaban": "benar"},
]
# endregion

# region DETEKSI HOUGH & KALMAN FILTER
# ==============================================================================
# 2. FUNGSI DETEKSI & KALMAN FILTER
# ==============================================================================

def detect_gaze_circle_hough(bgr_frame):
    """Deteksi lingkaran menggunakan Hough Circle Transform"""
    gray_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
    gray_frame = cv2.medianBlur(gray_frame, 5)
    circles = cv2.HoughCircles(
        gray_frame, cv2.HOUGH_GRADIENT, dp=1, minDist=1000,
        param1=HOUGH_PARAM1, param2=HOUGH_PARAM2, 
        minRadius=MIN_RADIUS, maxRadius=MAX_RADIUS
    )
    if circles is not None:
        circle = np.uint16(np.around(circles[0, 0]))
        return {"center": (int(circle[0]), int(circle[1])), "radius": int(circle[2])}
    return None

# Inisialisasi Kalman Filter
kalman = cv2.KalmanFilter(4, 2)
kalman.measurementMatrix = np.array([[1,0,0,0],[0,1,0,0]], np.float32)
kalman.transitionMatrix = np.array([[1,0,1,0],[0,1,0,1],[0,0,1,0],[0,0,0,1]], np.float32)
kalman.processNoiseCov = np.array([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]], np.float32) * 0.03
kalman.measurementNoiseCov = np.array([[1,0],[0,1]], np.float32) * 5.0
kalman_initialized = False

# endregion

# region GAME & VISUALISASI
# ==============================================================================
# 3. FUNGSI GAME & VISUALISASI
# ==============================================================================

# region Timeline Plot
def save_area_timeline_plot(gaze_df, output_dir):
    """
    1. Line graph showing time (x-axis) vs area (y-axis) with vertical dashed lines separating questions.
    Areas: question_text, background, button_benar, button_salah
    """
    fps = 60  # Assuming 60 FPS
    
    # Prepare data
    gaze_df = gaze_df.copy()
    gaze_df['time_seconds'] = gaze_df['timestamp']
    
    # Map ROI to simplified categories
    def map_roi(roi):
        if roi == 'question_text':
            return 'Question'
        elif roi == 'background':
            return 'Background'
        elif roi == 'button_benar':
            return 'Button Correct'
        elif roi == 'button_salah':
            return 'Button Wrong'
        else:
            return 'Background'
    
    gaze_df['area_category'] = gaze_df['roi'].apply(map_roi)
    
    # Create numeric encoding for areas (for line plot)
    area_encoding = {
        'Question': 3,
        'Button Correct': 2,
        'Button Wrong': 1,
        'Background': 0
    }
    gaze_df['area_numeric'] = gaze_df['area_category'].map(area_encoding)
    
    # Create plot
    plt.figure(figsize=(16, 6))
    
    # Plot line for each area
    colors = {
        'Question': '#FFB347',      # Light orange
        'Background': '#808080',     # Gray
        'Button Correct': '#90EE90', # Light green
        'Button Wrong': '#FFB6C1'    # Light red/pink
    }
    
    for area in ['Question', 'Button Correct', 'Button Wrong', 'Background']:
        area_data = gaze_df[gaze_df['area_category'] == area]
        if len(area_data) > 0:
            plt.scatter(area_data['time_seconds'], area_data['area_numeric'], 
                       c=colors[area], label=area, alpha=0.6, s=10)
    
    # Add vertical dashed lines for question transitions
    unique_questions = sorted(gaze_df['question_index'].unique())
    question_times = []
    for q_idx in unique_questions:
        q_data = gaze_df[gaze_df['question_index'] == q_idx]
        if len(q_data) > 0:
            start_time = q_data['time_seconds'].min()
            question_times.append((q_idx, start_time))
    
    for q_idx, start_time in question_times[1:]:  # Skip first question (starts at 0)
        plt.axvline(x=start_time, color='black', linestyle='--', alpha=0.5, linewidth=1.5)
        plt.text(start_time, 3.5, f'Q{q_idx+1}', ha='center', fontsize=9, 
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
    
    # Add Q1 label at the beginning
    if question_times:
        plt.text(question_times[0][1], 3.5, f'Q{question_times[0][0]+1}', ha='left', fontsize=9,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
    
    plt.yticks([0, 1, 2, 3], ['Background', 'Button Wrong', 'Button Correct', 'Question'])
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.ylabel('Area', fontsize=12)
    plt.title('Gaze Area Over Time - Question Sections', fontsize=14, fontweight='bold')
    plt.legend(loc='upper right', fontsize=10)
    plt.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    
    timeline_path = os.path.join(output_dir, "area_timeline.png")
    plt.savefig(timeline_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Area timeline tersimpan: {timeline_path}")
# endregion

# region Histogram per Question Area
def save_question_area_histogram(gaze_df, output_dir):
    """
    2. Histogram showing duration per area for each question.
    X-axis: Questions (with sub-bars for each area)
    Y-axis: Two versions - percentage (%) and seconds
    Areas: question_text (light orange), background (gray), button_benar (light green), button_salah (light red)
    """
    fps = 60  # Assuming 60 FPS
    
    # Map ROI to categories
    def map_roi(roi):
        if roi == 'question_text':
            return 'Question'
        elif roi == 'background':
            return 'Background'
        elif roi == 'button_benar':
            return 'Button Correct'
        elif roi == 'button_salah':
            return 'Button Wrong'
        else:
            return 'Background'
    
    gaze_df = gaze_df.copy()
    gaze_df['area_category'] = gaze_df['roi'].apply(map_roi)
    
    # Get unique questions
    unique_questions = sorted([q for q in gaze_df['question_index'].unique() if q < len(SOAL_MATEMATIKA)])
    
    if len(unique_questions) == 0:
        return
    
    # Calculate durations for each question and area
    question_data = []
    for q_idx in unique_questions:
        q_data = gaze_df[gaze_df['question_index'] == q_idx]
        total_frames = len(q_data)
        total_seconds = total_frames / fps
        
        area_counts = q_data['area_category'].value_counts()
        
        question_data.append({
            'question': f'Q{q_idx + 1}',
            'question_idx': q_idx,
            'Question_seconds': area_counts.get('Question', 0) / fps,
            'Background_seconds': area_counts.get('Background', 0) / fps,
            'Button_Correct_seconds': area_counts.get('Button Correct', 0) / fps,
            'Button_Wrong_seconds': area_counts.get('Button Wrong', 0) / fps,
            'total_seconds': total_seconds,
            'Question_pct': (area_counts.get('Question', 0) / total_frames * 100) if total_frames > 0 else 0,
            'Background_pct': (area_counts.get('Background', 0) / total_frames * 100) if total_frames > 0 else 0,
            'Button_Correct_pct': (area_counts.get('Button Correct', 0) / total_frames * 100) if total_frames > 0 else 0,
            'Button_Wrong_pct': (area_counts.get('Button Wrong', 0) / total_frames * 100) if total_frames > 0 else 0,
        })
    
    df = pd.DataFrame(question_data)
    
    # Define colors
    colors = {
        'Question': '#FFB347',      # Light orange
        'Background': '#808080',     # Gray
        'Button_Correct': '#90EE90', # Light green
        'Button_Wrong': '#FFB6C1'    # Light red/pink
    }
    
    # --- Plot 1: Percentage ---
    fig, ax = plt.subplots(figsize=(14, 6))
    
    x = np.arange(len(df))
    width = 0.2
    
    ax.bar(x - 1.5*width, df['Question_pct'], width, label='Question Area', color=colors['Question'])
    ax.bar(x - 0.5*width, df['Background_pct'], width, label='Background', color=colors['Background'])
    ax.bar(x + 0.5*width, df['Button_Correct_pct'], width, label='Button Correct', color=colors['Button_Correct'])
    ax.bar(x + 1.5*width, df['Button_Wrong_pct'], width, label='Button Wrong', color=colors['Button_Wrong'])
    
    ax.set_xlabel('Question', fontsize=12)
    ax.set_ylabel('Percent Time Allocated (%)', fontsize=12)
    ax.set_title('Gaze Duration per Area by Question (Percentage)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(df['question'])
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    pct_path = os.path.join(output_dir, "area_duration_percentage.png")
    plt.savefig(pct_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Area duration (percentage) tersimpan: {pct_path}")
    
    # --- Plot 2: Seconds ---
    fig, ax = plt.subplots(figsize=(14, 6))
    
    ax.bar(x - 1.5*width, df['Question_seconds'], width, label='Question Area', color=colors['Question'])
    ax.bar(x - 0.5*width, df['Background_seconds'], width, label='Background', color=colors['Background'])
    ax.bar(x + 0.5*width, df['Button_Correct_seconds'], width, label='Button Correct', color=colors['Button_Correct'])
    ax.bar(x + 1.5*width, df['Button_Wrong_seconds'], width, label='Button Wrong', color=colors['Button_Wrong'])
    
    ax.set_xlabel('Question', fontsize=12)
    ax.set_ylabel('Duration (seconds)', fontsize=12)
    ax.set_title('Gaze Duration per Area by Question (Seconds)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(df['question'])
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    sec_path = os.path.join(output_dir, "area_duration_seconds.png")
    plt.savefig(sec_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Area duration (seconds) tersimpan: {sec_path}")
    
    # Save data as CSV
    csv_path = os.path.join(output_dir, "area_duration_data.csv")
    df.to_csv(csv_path, index=False)
    print(f"✓ Area duration data tersimpan: {csv_path}")

#endregion


# region Histogram per Gaze Trajectory
def save_gaze_trajectory_histograms(gaze_df, output_dir):
    """
    3. Gaze position trajectory vs area histogram.
    Shows distribution of gaze points relative to the target area boundaries.
    Creates combined histograms for X and Y positions for each question showing all areas.
    """
    unique_questions = sorted([q for q in gaze_df['question_index'].unique() if q < len(SOAL_MATEMATIKA)])
    
    if len(unique_questions) == 0:
        return
    
    # Create subdirectory for trajectory plots
    trajectory_dir = os.path.join(output_dir, "gaze_trajectories")
    os.makedirs(trajectory_dir, exist_ok=True)
    
    # Process each question
    for q_idx in unique_questions:
        q_data = gaze_df[gaze_df['question_index'] == q_idx].copy()
        
        if len(q_data) == 0:
            continue
        
        # Create a 3x2 subplot (3 areas × 2 axes)
        fig, axes = plt.subplots(3, 2, figsize=(16, 12))
        fig.suptitle(f'Q{q_idx + 1}: Gaze Position Distribution vs Area Boundaries', 
                     fontsize=16, fontweight='bold', y=0.995)
        
        # Calculate Y position for this question
        y_pos = POSISI_AWAL_SOAL_Y + (q_idx * JARAK_ANTAR_SOAL)
        
        # --- Row 1: Question Text Area Analysis ---
        question_gaze = q_data[q_data['roi'] == 'question_text']
        
        if len(question_gaze) > 0:
            # Estimate question area bounds
            q_text = q_data['question_text'].iloc[0]
            estimated_text_width = len(q_text) * 35
            soal_rect_width = min(estimated_text_width, LEBAR_LAYAR - 400)
            
            question_bounds = {
                'x_min': 100,
                'x_max': 100 + soal_rect_width,
                'y_min': y_pos - 10,
                'y_max': y_pos + 80
            }
            
            # X-axis histogram
            axes[0, 0].hist(question_gaze['gaze_x'], bins=30, color='#FFB347', alpha=0.7, edgecolor='black')
            axes[0, 0].axvline(question_bounds['x_min'], color='red', linestyle='--', linewidth=2, label='Area Boundary')
            axes[0, 0].axvline(question_bounds['x_max'], color='red', linestyle='--', linewidth=2)
            axes[0, 0].set_xlabel('X Position (pixels)', fontsize=10)
            axes[0, 0].set_ylabel('Frequency', fontsize=10)
            axes[0, 0].set_title('Question Area - X Distribution', fontweight='bold', fontsize=11)
            axes[0, 0].legend(fontsize=9)
            axes[0, 0].grid(True, alpha=0.3)
            
            # Y-axis histogram
            axes[0, 1].hist(question_gaze['gaze_y'], bins=30, color='#FFB347', alpha=0.7, edgecolor='black')
            axes[0, 1].axvline(question_bounds['y_min'], color='red', linestyle='--', linewidth=2, label='Area Boundary')
            axes[0, 1].axvline(question_bounds['y_max'], color='red', linestyle='--', linewidth=2)
            axes[0, 1].set_xlabel('Y Position (pixels)', fontsize=10)
            axes[0, 1].set_ylabel('Frequency', fontsize=10)
            axes[0, 1].set_title('Question Area - Y Distribution', fontweight='bold', fontsize=11)
            axes[0, 1].legend(fontsize=9)
            axes[0, 1].grid(True, alpha=0.3)
        else:
            axes[0, 0].text(0.5, 0.5, 'No data', ha='center', va='center', transform=axes[0, 0].transAxes)
            axes[0, 1].text(0.5, 0.5, 'No data', ha='center', va='center', transform=axes[0, 1].transAxes)
            axes[0, 0].set_title('Question Area - X Distribution', fontweight='bold', fontsize=11)
            axes[0, 1].set_title('Question Area - Y Distribution', fontweight='bold', fontsize=11)
        
        # --- Row 2: Button Correct (Benar) Analysis ---
        button_benar_gaze = q_data[q_data['roi'] == 'button_benar']
        
        if len(button_benar_gaze) > 0:
            btn_benar = TOMBOL['benar']
            benar_bounds = {
                'x_min': btn_benar['pos'][0],
                'x_max': btn_benar['pos'][0] + btn_benar['size'][0],
                'y_min': btn_benar['pos'][1],
                'y_max': btn_benar['pos'][1] + btn_benar['size'][1]
            }
            
            # X-axis histogram
            axes[1, 0].hist(button_benar_gaze['gaze_x'], bins=20, color='#90EE90', alpha=0.7, edgecolor='black')
            axes[1, 0].axvline(benar_bounds['x_min'], color='red', linestyle='--', linewidth=2, label='Button Boundary')
            axes[1, 0].axvline(benar_bounds['x_max'], color='red', linestyle='--', linewidth=2)
            axes[1, 0].set_xlabel('X Position (pixels)', fontsize=10)
            axes[1, 0].set_ylabel('Frequency', fontsize=10)
            axes[1, 0].set_title('Button Correct - X Distribution', fontweight='bold', fontsize=11)
            axes[1, 0].legend(fontsize=9)
            axes[1, 0].grid(True, alpha=0.3)
            
            # Y-axis histogram
            axes[1, 1].hist(button_benar_gaze['gaze_y'], bins=20, color='#90EE90', alpha=0.7, edgecolor='black')
            axes[1, 1].axvline(benar_bounds['y_min'], color='red', linestyle='--', linewidth=2, label='Button Boundary')
            axes[1, 1].axvline(benar_bounds['y_max'], color='red', linestyle='--', linewidth=2)
            axes[1, 1].set_xlabel('Y Position (pixels)', fontsize=10)
            axes[1, 1].set_ylabel('Frequency', fontsize=10)
            axes[1, 1].set_title('Button Correct - Y Distribution', fontweight='bold', fontsize=11)
            axes[1, 1].legend(fontsize=9)
            axes[1, 1].grid(True, alpha=0.3)
        else:
            axes[1, 0].text(0.5, 0.5, 'No data', ha='center', va='center', transform=axes[1, 0].transAxes)
            axes[1, 1].text(0.5, 0.5, 'No data', ha='center', va='center', transform=axes[1, 1].transAxes)
            axes[1, 0].set_title('Button Correct - X Distribution', fontweight='bold', fontsize=11)
            axes[1, 1].set_title('Button Correct - Y Distribution', fontweight='bold', fontsize=11)
        
        # --- Row 3: Button Wrong (Salah) Analysis ---
        button_salah_gaze = q_data[q_data['roi'] == 'button_salah']
        
        if len(button_salah_gaze) > 0:
            btn_salah = TOMBOL['salah']
            salah_bounds = {
                'x_min': btn_salah['pos'][0],
                'x_max': btn_salah['pos'][0] + btn_salah['size'][0],
                'y_min': btn_salah['pos'][1],
                'y_max': btn_salah['pos'][1] + btn_salah['size'][1]
            }
            
            # X-axis histogram
            axes[2, 0].hist(button_salah_gaze['gaze_x'], bins=20, color='#FFB6C1', alpha=0.7, edgecolor='black')
            axes[2, 0].axvline(salah_bounds['x_min'], color='red', linestyle='--', linewidth=2, label='Button Boundary')
            axes[2, 0].axvline(salah_bounds['x_max'], color='red', linestyle='--', linewidth=2)
            axes[2, 0].set_xlabel('X Position (pixels)', fontsize=10)
            axes[2, 0].set_ylabel('Frequency', fontsize=10)
            axes[2, 0].set_title('Button Wrong - X Distribution', fontweight='bold', fontsize=11)
            axes[2, 0].legend(fontsize=9)
            axes[2, 0].grid(True, alpha=0.3)
            
            # Y-axis histogram
            axes[2, 1].hist(button_salah_gaze['gaze_y'], bins=20, color='#FFB6C1', alpha=0.7, edgecolor='black')
            axes[2, 1].axvline(salah_bounds['y_min'], color='red', linestyle='--', linewidth=2, label='Button Boundary')
            axes[2, 1].axvline(salah_bounds['y_max'], color='red', linestyle='--', linewidth=2)
            axes[2, 1].set_xlabel('Y Position (pixels)', fontsize=10)
            axes[2, 1].set_ylabel('Frequency', fontsize=10)
            axes[2, 1].set_title('Button Wrong - Y Distribution', fontweight='bold', fontsize=11)
            axes[2, 1].legend(fontsize=9)
            axes[2, 1].grid(True, alpha=0.3)
        else:
            axes[2, 0].text(0.5, 0.5, 'No data', ha='center', va='center', transform=axes[2, 0].transAxes)
            axes[2, 1].text(0.5, 0.5, 'No data', ha='center', va='center', transform=axes[2, 1].transAxes)
            axes[2, 0].set_title('Button Wrong - X Distribution', fontweight='bold', fontsize=11)
            axes[2, 1].set_title('Button Wrong - Y Distribution', fontweight='bold', fontsize=11)
        
        plt.tight_layout()
        combined_path = os.path.join(trajectory_dir, f"q{q_idx + 1}_trajectory_combined.png")
        plt.savefig(combined_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"✓ Q{q_idx + 1} combined trajectory tersimpan: {combined_path}")
    
    print(f"✓ All trajectory histograms saved in: {trajectory_dir}")
# endregion

# region Fungsi Bantuan Pygame
def draw_button_pygame(screen, button_key, is_hovered, hover_progress, warna, font):
    """Menggambar tombol dengan efek hover"""
    btn = TOMBOL[button_key]
    rect = pygame.Rect(btn["pos"][0], btn["pos"][1], btn["size"][0], btn["size"][1])
    
    # Pilih warna tombol
    if button_key == "keluar":
        btn_color = WARNA_KELUAR
    elif button_key == "mulai":
        btn_color = WARNA_MULAI
    else:
        btn_color = warna["hover"] if is_hovered else warna["tombol"]
    
    pygame.draw.rect(screen, btn_color, rect)
    pygame.draw.rect(screen, warna["outline"], rect, 2)

    text_surf = font.render(btn["teks"], True, warna["teks_biasa"])
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)

    # Progress bar untuk hover
    if is_hovered and hover_progress > 0:
        progress_width = int(rect.width * hover_progress)
        if button_key == "keluar":
            progress_color = WARNA_SALAH
        elif button_key == "mulai":
            progress_color = WARNA_BENAR
        else:
            progress_color = WARNA_PROGRESS
        pygame.draw.rect(screen, progress_color, (rect.left, rect.bottom - 10, progress_width, 10))

def is_point_in_rect(point, rect_pos, rect_size):
    """Cek apakah titik berada di dalam rectangle"""
    return rect_pos[0] <= point[0] <= rect_pos[0] + rect_size[0] and \
           rect_pos[1] <= point[1] <= rect_pos[1] + rect_size[1]

def get_roi_name(gaze_pos, current_soal_y_pos, question_text=""):
    """Identifikasi ROI (Region of Interest) dari posisi gaze"""
    # Cek tombol
    for key, btn in TOMBOL.items():
        if is_point_in_rect(gaze_pos, btn["pos"], btn["size"]):
            return f"button_{key}"
    
    # Cek area soal - shrink to hug the text
    # Estimate text width and height based on font size
    soal_rect_height = 80  # Reduced from 100 to hug text better
    estimated_text_width = len(question_text) * 35  # Approximate character width
    soal_rect_width = min(estimated_text_width, LEBAR_LAYAR - 400)
    
    if current_soal_y_pos - 10 <= gaze_pos[1] <= current_soal_y_pos + soal_rect_height:
        if 100 <= gaze_pos[0] <= 100 + soal_rect_width:
            return "question_text"
    
    return "background"
# endregion
# endregion

# region MAIN SETUP & LOOP GAME
# ==============================================================================
# 4. SETUP UTAMA & LOOP GAME
# ==============================================================================

# Inisialisasi Pygame
pygame.init()
pygame.font.init()

# Setup layar fullscreen
screen_info = pygame.display.Info()
LEBAR_LAYAR, TINGGI_LAYAR = screen_info.current_w, screen_info.current_h
screen = pygame.display.set_mode((LEBAR_LAYAR, TINGGI_LAYAR), pygame.NOFRAME)
pygame.display.set_caption("Game Matematika Eye-Tracker")

# Setup Font
font_soal = pygame.font.SysFont('Arial', 64)
font_jawaban = pygame.font.SysFont('Arial', 28)
font_skor = pygame.font.SysFont('Arial', 36)
font_tombol_normal = pygame.font.SysFont('Arial', 50)
font_tombol_keluar = pygame.font.SysFont('Arial', 30)
font_final = pygame.font.SysFont('Arial', 60)
font_instruksi = pygame.font.SysFont('Arial', 28)

# Posisi tombol (akan ditambah tombol MULAI)
TOMBOL = {
    "benar": {"teks": "BENAR", "pos": (LEBAR_LAYAR - 300, TINGGI_LAYAR * 0.25), "size": (300, 150)},
    "salah": {"teks": "SALAH", "pos": (LEBAR_LAYAR - 300, TINGGI_LAYAR * 0.75), "size": (300, 150)},
    "keluar": {"teks": "KELUAR", "pos": (LEBAR_LAYAR // 2 - 125, 0), "size": (250, 80)},
    "mulai": {"teks": "MULAI", "pos": (LEBAR_LAYAR // 2 - 150, TINGGI_LAYAR // 2 + 100), "size": (300, 100)},
}
POSISI_AWAL_SOAL_Y = TINGGI_LAYAR * 0.1
JARAK_ANTAR_SOAL = 125

# Setup kamera virtual
cap = cv2.VideoCapture(INDEX_KAMERA_VIRTUAL)
if cap.isOpened():
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    use_mouse_fallback = False
    print("Kamera virtual berhasil terdeteksi.")
else:
    print(f"ERROR: Tidak bisa membuka kamera dengan indeks {INDEX_KAMERA_VIRTUAL}.")
    print("PERINGATAN: Fallback ke simulasi mouse.")
    use_mouse_fallback = True

# Setup output directory untuk data gaze
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
output_dir = f"game_session_{timestamp}"
os.makedirs(output_dir, exist_ok=True)

# Inisialisasi state game
game_state = "trial"  # States: "trial" -> "waiting_start" -> "main" -> "finished"
history_soal = []
current_question_index = 0
score = 0
mode_gelap = True
hovered_button_key = None
hover_start_time = 0
game_running = True
clock = pygame.time.Clock()

# Data gaze recording
gaze_data = []
frame_counter = 0
session_start_time = time.time()
recording_active = False  # Hanya aktif saat mode "main"

print(f"\n{'='*60}")
print("MULAI GAME MATEMATIKA EYE-TRACKER")
print(f"{'='*60}")
print(f"Mode: LATIHAN ({len(SOAL_LATIHAN)} soal)")
print("Setelah latihan selesai, tekan MULAI untuk memulai sesi utama.")
print(f"{'='*60}\n")
# endregion

# region MAIN GAME LOOP
# ==============================================================================
# 5. MAIN GAME LOOP
# ==============================================================================

while game_running:
    frame_start_time = time.time()
    
    # --- TAHAP 1: EVENT HANDLING ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                game_running = False
            if event.key == pygame.K_b:
                mode_gelap = not mode_gelap

    # --- TAHAP 2: TANGKAP & DETEKSI GAZE ---
    gaze_pos = pygame.mouse.get_pos()
    detected_coords = None
    
    if not use_mouse_fallback:
        success, img_bgr = cap.read()
        if success:
            circle_info = detect_gaze_circle_hough(img_bgr)
            if circle_info:
                detected_coords = circle_info["center"]
                measurement = np.array([[np.float32(detected_coords[0])], 
                                      [np.float32(detected_coords[1])]])
                if not kalman_initialized:
                    kalman.statePost = np.array([measurement[0,0], measurement[1,0], 0, 0], np.float32)
                    kalman_initialized = True
                else:
                    kalman.correct(measurement)
        
        if kalman_initialized:
            prediction = kalman.predict()
            gaze_pos = (int(prediction[0,0]), int(prediction[1,0]))

    # --- TAHAP 3: LOGIKA HOVER & KLIK ---
    currently_hovering = None
    
    # Tentukan tombol mana yang aktif berdasarkan game_state
    active_buttons = []
    if game_state == "trial":
        active_buttons = ["benar", "salah", "keluar"]
    elif game_state == "waiting_start":
        active_buttons = ["mulai", "keluar"]
    elif game_state == "main":
        if current_question_index < len(SOAL_MATEMATIKA):
            active_buttons = ["benar", "salah", "keluar"]
        else:
            active_buttons = ["keluar"]
    elif game_state == "finished":
        active_buttons = ["keluar"]
    
    for key in active_buttons:
        btn = TOMBOL[key]
        if is_point_in_rect(gaze_pos, btn["pos"], btn["size"]):
            currently_hovering = key
            break
    
    # Handle hover logic
    if currently_hovering:
        if currently_hovering != hovered_button_key:
            hovered_button_key = currently_hovering
            hover_start_time = time.time()
        
        # Cek durasi hover untuk "klik"
        click_duration = DURASI_HOVER_KELUAR if hovered_button_key == "keluar" else DURASI_HOVER_UNTUK_KLIK
        if time.time() - hover_start_time >= click_duration:
            # Handle klik berdasarkan tombol dan state
            if hovered_button_key == "keluar":
                game_running = False
            
            elif hovered_button_key == "mulai" and game_state == "waiting_start":
                # Mulai sesi utama dengan recording
                game_state = "main"
                current_question_index = 0
                history_soal = []
                score = 0
                recording_active = True
                session_start_time = time.time()
                print(f"\n{'='*60}")
                print("SESI UTAMA DIMULAI - RECORDING AKTIF")
                print(f"{'='*60}\n")
            
            elif hovered_button_key in ["benar", "salah"]:
                if game_state == "trial":
                    # Proses jawaban latihan
                    correct_answer = SOAL_LATIHAN[current_question_index]["jawaban"]
                    is_correct = (correct_answer == hovered_button_key)
                    if is_correct:
                        score += 1
                    history_soal.append({
                        "soal": SOAL_LATIHAN[current_question_index]["soal"],
                        "jawaban_diberikan": hovered_button_key.upper(),
                        "jawaban_benar": correct_answer.upper(),
                        "benar": is_correct
                    })
                    current_question_index += 1
                    
                    # Jika latihan selesai, pindah ke waiting_start
                    if current_question_index >= len(SOAL_LATIHAN):
                        game_state = "waiting_start"
                        current_question_index = 0
                        print(f"\nLatihan selesai! Skor: {score}/{len(SOAL_LATIHAN)}")
                        print("Lihat tombol MULAI untuk memulai sesi utama.\n")
                
                elif game_state == "main":
                    # Proses jawaban sesi utama
                    correct_answer = SOAL_MATEMATIKA[current_question_index]["jawaban"]
                    is_correct = (correct_answer == hovered_button_key)
                    if is_correct:
                        score += 1
                    history_soal.append({
                        "soal": SOAL_MATEMATIKA[current_question_index]["soal"],
                        "jawaban_diberikan": hovered_button_key.upper(),
                        "jawaban_benar": correct_answer.upper(),
                        "benar": is_correct,
                        "timestamp": time.time() - session_start_time
                    })
                    current_question_index += 1
                    
                    # Jika semua soal utama selesai
                    if current_question_index >= len(SOAL_MATEMATIKA):
                        game_state = "finished"
                        recording_active = False
                        print(f"\n{'='*60}")
                        print("SESI UTAMA SELESAI!")
                        print(f"Skor Akhir: {score}/{len(SOAL_MATEMATIKA)}")
                        print(f"{'='*60}\n")
            
            # Reset hover state setelah klik
            hovered_button_key = None
            hover_start_time = 0
    else:
        hovered_button_key = None
        hover_start_time = 0

    # --- TAHAP 4: RECORD GAZE DATA (Hanya saat recording_active) ---
    if recording_active:
        # Tentukan posisi soal saat ini untuk ROI detection
        current_soal_y_pos = POSISI_AWAL_SOAL_Y + (len(history_soal) * JARAK_ANTAR_SOAL)
        current_question_text = SOAL_MATEMATIKA[current_question_index]["soal"] if current_question_index < len(SOAL_MATEMATIKA) else ""
        
        roi_name = get_roi_name(gaze_pos, current_soal_y_pos, current_question_text)
        
        gaze_data.append({
            'frame': frame_counter,
            'timestamp': time.time() - session_start_time,
            'question_index': current_question_index,
            'question_text': SOAL_MATEMATIKA[current_question_index]["soal"] if current_question_index < len(SOAL_MATEMATIKA) else "FINISHED",
            'gaze_x': gaze_pos[0],
            'gaze_y': gaze_pos[1],
            'detected_x': detected_coords[0] if detected_coords else None,
            'detected_y': detected_coords[1] if detected_coords else None,
            'roi': roi_name,
            'hovered_button': hovered_button_key if hovered_button_key else "none",
            'hover_duration': time.time() - hover_start_time if hovered_button_key else 0
        })
    
    frame_counter += 1

    # --- TAHAP 5: RENDER GAME ---
    warna = WARNA_DARK if mode_gelap else WARNA_LIGHT
    screen.fill(warna["latar"])
    

    # Render berdasarkan game_state
    if game_state == "trial":
        # Tampilkan history soal latihan
        for i, item in enumerate(history_soal):
            y_pos = POSISI_AWAL_SOAL_Y + (i * JARAK_ANTAR_SOAL)
            soal_surf = font_soal.render(f"{i+1}. {item['soal']}", True, warna["teks_soal"])
            screen.blit(soal_surf, (100, y_pos))
            
            warna_jawaban = WARNA_BENAR if item["benar"] else WARNA_SALAH
            if item["benar"]:
                jawaban_text = f"Jawaban Anda: {item['jawaban_diberikan']} itu BENAR"
            else:
                jawaban_text = f"Jawaban Anda: {item['jawaban_diberikan']} itu SALAH (Seharusnya: {item['jawaban_benar']})"
            jawaban_surf = font_jawaban.render(jawaban_text, True, warna_jawaban)
            screen.blit(jawaban_surf, (150, y_pos + 60))
        
        # Tampilkan soal latihan saat ini
        if current_question_index < len(SOAL_LATIHAN):
            y_pos = POSISI_AWAL_SOAL_Y + (len(history_soal) * JARAK_ANTAR_SOAL)
            soal_surf = font_soal.render(f"{current_question_index+1}. {SOAL_LATIHAN[current_question_index]['soal']}", True, warna["teks_soal"])
            screen.blit(soal_surf, (100, y_pos))
            
            # Instruksi
            instruksi_surf = font_instruksi.render("MODE LATIHAN - Arahkan mata ke tombol jawaban", True, WARNA_PROGRESS)
            screen.blit(instruksi_surf, (100, 50))
            
            # Debug: tampilkan area soal dan jawaban
            pygame.draw.rect(screen, (100, 100, 255), (50, y_pos - 20, LEBAR_LAYAR - 350, 100), 2)
    
    elif game_state == "waiting_start":
        # Layar transisi
        title_surf = font_final.render("LATIHAN SELESAI!", True, WARNA_BENAR)
        screen.blit(title_surf, (LEBAR_LAYAR // 2 - 300, TINGGI_LAYAR // 2 - 200))
        
        score_surf = font_skor.render(f"Skor Latihan: {score}/{len(SOAL_LATIHAN)}", True, warna["teks_soal"])
        screen.blit(score_surf, (LEBAR_LAYAR // 2 - 200, TINGGI_LAYAR // 2 - 100))
        
        instruksi1 = font_instruksi.render("Arahkan mata ke tombol MULAI", True, WARNA_MULAI)
        instruksi2 = font_instruksi.render("untuk memulai sesi utama (dengan recording)", True, warna["teks_soal"])
        screen.blit(instruksi1, (LEBAR_LAYAR // 2 - 350, TINGGI_LAYAR // 2 - 20))
        screen.blit(instruksi2, (LEBAR_LAYAR // 2 - 420, TINGGI_LAYAR // 2 + 30))
    
    elif game_state == "main":
        # Tampilkan history soal utama
        for i, item in enumerate(history_soal):
            y_pos = POSISI_AWAL_SOAL_Y + (i * JARAK_ANTAR_SOAL)
            soal_surf = font_soal.render(f"{i+1}. {item['soal']}", True, warna["teks_soal"])
            screen.blit(soal_surf, (100, y_pos))
            
            warna_jawaban = WARNA_BENAR if item["benar"] else WARNA_SALAH
            if item["benar"]:
                jawaban_text = f"Jawaban Anda: {item['jawaban_diberikan']} itu BENAR"
            else:
                jawaban_text = f"Jawaban Anda: {item['jawaban_diberikan']} itu SALAH (Seharusnya: {item['jawaban_benar']})"
            jawaban_surf = font_jawaban.render(jawaban_text, True, warna_jawaban)
            screen.blit(jawaban_surf, (150, y_pos + 60))
        
        # Tampilkan soal saat ini
        if current_question_index < len(SOAL_MATEMATIKA):
            y_pos = POSISI_AWAL_SOAL_Y + (len(history_soal) * JARAK_ANTAR_SOAL)
            soal_surf = font_soal.render(f"{current_question_index+1}. {SOAL_MATEMATIKA[current_question_index]['soal']}", True, warna["teks_soal"])
            screen.blit(soal_surf, (100, y_pos))
            
            # Indicator recording
            rec_surf = font_instruksi.render("● REC", True, WARNA_SALAH)
            screen.blit(rec_surf, (LEBAR_LAYAR - 200, 100))
    
    elif game_state == "finished":
        final1_surf = font_final.render("PERMAINAN SELESAI!", True, warna["teks_soal"])
        final2_surf = font_skor.render(f"Skor Akhir: {score} / {len(SOAL_MATEMATIKA)}", True, WARNA_PROGRESS)
        screen.blit(final1_surf, (LEBAR_LAYAR // 2 - 350, TINGGI_LAYAR // 2 - 100))
        screen.blit(final2_surf, (LEBAR_LAYAR // 2 - 250, TINGGI_LAYAR // 2))
        
        # Info data tersimpan
        info_surf = font_instruksi.render(f"Data gaze tersimpan di: {output_dir}", True, WARNA_BENAR)
        screen.blit(info_surf, (LEBAR_LAYAR // 2 - 400, TINGGI_LAYAR // 2 + 100))

    # Render tombol yang aktif
    for key in active_buttons:
        is_hovered = (key == hovered_button_key)
        progress = 0
        if is_hovered:
            click_duration = DURASI_HOVER_KELUAR if key == "keluar" else DURASI_HOVER_UNTUK_KLIK
            progress = (time.time() - hover_start_time) / click_duration
        
        font_tombol = font_tombol_keluar if key == "keluar" else font_tombol_normal
        draw_button_pygame(screen, key, is_hovered, progress, warna, font_tombol)

    # Render cursor gaze
    pygame.draw.circle(screen, WARNA_CURSOR, gaze_pos, 15, 2)
    pygame.draw.line(screen, WARNA_CURSOR, (gaze_pos[0]-15, gaze_pos[1]), (gaze_pos[0]+15, gaze_pos[1]), 2)
    pygame.draw.line(screen, WARNA_CURSOR, (gaze_pos[0], gaze_pos[1]-15), (gaze_pos[0], gaze_pos[1]+15), 2)

    pygame.display.flip()
    clock.tick(60)
# endregion
# region CLEANUP & SAVE DATA
# ==============================================================================
# 6. CLEANUP & SAVE DATA
# ==============================================================================

print(f"\n{'='*60}")
print("MENYIMPAN DATA...")
print(f"{'='*60}\n")

# Simpan gaze data
if gaze_data:
    gaze_df = pd.DataFrame(gaze_data)
    gaze_csv_path = os.path.join(output_dir, "gaze_data.csv")
    gaze_df.to_csv(gaze_csv_path, index=False)
    print(f"✓ Gaze data tersimpan: {gaze_csv_path}")
    print(f"  Total frames recorded: {len(gaze_data)}")

# Simpan hasil jawaban
if history_soal:
    results_df = pd.DataFrame(history_soal)
    results_csv_path = os.path.join(output_dir, "quiz_results.csv")
    results_df.to_csv(results_csv_path, index=False)
    print(f"✓ Quiz results tersimpan: {results_csv_path}")
    print(f"  Skor: {score}/{len(SOAL_MATEMATIKA)}")

# Simpan metadata session
metadata = {
    'session_timestamp': timestamp,
    'total_questions': len(SOAL_MATEMATIKA),
    'score': score,
    'accuracy': score / len(SOAL_MATEMATIKA) if len(SOAL_MATEMATIKA) > 0 else 0,
    'total_frames': frame_counter,
    'recording_duration_seconds': time.time() - session_start_time if recording_active or game_state == "finished" else 0,
    'screen_resolution': f"{LEBAR_LAYAR}x{TINGGI_LAYAR}",
    'camera_index': INDEX_KAMERA_VIRTUAL,
    'use_mouse_fallback': use_mouse_fallback
}

# Simpan statistik secara diagram data gaze terhadap soal dan tombol
if gaze_data:
    gaze_df = pd.DataFrame(gaze_data)
    save_area_timeline_plot(gaze_df, output_dir)  # 1. Line graph: time vs area
    save_question_area_histogram(gaze_df, output_dir)  # 2. Histogram: question vs area duration
    save_gaze_trajectory_histograms(gaze_df, output_dir)  # 3. Gaze trajectory vs area boundaries

metadata_df = pd.DataFrame([metadata])
metadata_csv_path = os.path.join(output_dir, "session_metadata.csv")
metadata_df.to_csv(metadata_csv_path, index=False)
print(f"✓ Metadata tersimpan: {metadata_csv_path}")

print(f"\n{'='*60}")
print("GAME SELESAI")
print(f"{'='*60}\n")

# Cleanup
pygame.quit()
if not use_mouse_fallback:
    cap.release()
cv2.destroyAllWindows()
# endregion