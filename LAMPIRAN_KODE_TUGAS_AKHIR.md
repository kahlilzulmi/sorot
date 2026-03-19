# LAMPIRAN KODE PROGRAM
# SISTEM DETEKSI TITIK PANDANG MATA DAN GAME MATEMATIKA INTERAKTIF

---

## Lampiran 1. Kode Pembanding Algoritma Deteksi Titik Pandang Mata

### 1.1 Kalman Filter untuk Smoothing Trajektori

```python
"""
Kalman Filter untuk merapikan trajektori deteksi gaze.
Menggunakan state vector [x, y, vx, vy] untuk melacak posisi dan kecepatan.
"""

import cv2
import numpy as np

def create_kalman_filter() -> cv2.KalmanFilter:
    """
    Membuat dan menginisialisasi Kalman filter untuk smoothing gaze.
    
    State vector: [x, y, vx, vy] (posisi dan kecepatan)
    Measurement: [x, y] (posisi yang diobservasi)
    
    Returns:
        cv2.KalmanFilter: Kalman filter yang sudah diinisialisasi
    """
    kf = cv2.KalmanFilter(4, 2)  # 4 state variables, 2 measurements
    
    # State transition matrix (prediksi state selanjutnya)
    kf.transitionMatrix = np.array([
        [1, 0, 1, 0],  # x = x + vx
        [0, 1, 0, 1],  # y = y + vy
        [0, 0, 1, 0],  # vx = vx
        [0, 0, 0, 1]   # vy = vy
    ], dtype=np.float32)
    
    # Measurement matrix (mapping state ke measurement)
    kf.measurementMatrix = np.array([
        [1, 0, 0, 0],  # measure x
        [0, 1, 0, 0]   # measure y
    ], dtype=np.float32)
    
    # Process noise covariance
    kf.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03
    
    # Measurement noise covariance
    kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 0.1
    
    # Initial state covariance
    kf.errorCovPost = np.eye(4, dtype=np.float32)
    
    return kf


def apply_kalman_filter(
    detections: List[Tuple[int, int, int]],
    min_detections: int = 3
) -> List[Tuple[int, int, int]]:
    """
    Menerapkan Kalman filtering untuk merapikan trajektori gaze.
    
    Args:
        detections: List dari tuple (x, y, radius)
        min_detections: Minimum jumlah deteksi untuk menerapkan filter
        
    Returns:
        List dari tuple (x, y, radius) yang sudah di-smooth
    """
    if len(detections) < min_detections:
        return detections
    
    kf = create_kalman_filter()
    smoothed = []
    
    # Inisialisasi dengan deteksi pertama
    first_x, first_y, first_r = detections[0]
    kf.statePre = np.array([[first_x], [first_y], [0], [0]], dtype=np.float32)
    kf.statePost = np.array([[first_x], [first_y], [0], [0]], dtype=np.float32)
    
    for x, y, radius in detections:
        # Prediction step
        prediction = kf.predict()
        
        # Measurement step
        measurement = np.array([[x], [y]], dtype=np.float32)
        
        # Correction step
        corrected = kf.correct(measurement)
        
        # Extract smoothed position
        smoothed_x = int(corrected[0][0])
        smoothed_y = int(corrected[1][0])
        
        smoothed.append((smoothed_x, smoothed_y, radius))
    
    return smoothed
```

### 1.2 Metode 1: Hough Circle Transform

```python
"""
Deteksi pupil/mata menggunakan Hough Circle Transform.
Metode ini mendeteksi lingkaran berdasarkan transformasi geometri.
"""

def detect_hough_circle(
    frame: np.ndarray,
    params: Optional[Dict[str, Any]] = None
) -> List[Tuple[int, int, int]]:
    """
    Deteksi pupil/mata menggunakan Hough Circle Transform.
    
    Args:
        frame: Input frame (BGR atau grayscale)
        params: Parameter deteksi dengan key:
            - dp: Inverse ratio dari resolusi accumulator (default: 1.2)
            - minDist: Jarak minimum antar pusat lingkaran (default: 50)
            - param1: Threshold Canny edge detector (default: 50)
            - param2: Threshold accumulator (default: 30)
            - minRadius: Radius minimum lingkaran (default: 10)
            - maxRadius: Radius maximum lingkaran (default: 80)
            - blur_kernel: Ukuran kernel Gaussian blur (default: 5)
    
    Returns:
        List dari tuple (x, y, radius) untuk lingkaran yang terdeteksi
    """
    # Parameter default
    default_params = {
        'dp': 1.2,
        'minDist': 50,
        'param1': 50,
        'param2': 30,
        'minRadius': 10,
        'maxRadius': 80,
        'blur_kernel': 5
    }
    
    if params:
        default_params.update(params)
    
    # Konversi ke grayscale jika perlu
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame.copy()
    
    # Terapkan Gaussian blur untuk mengurangi noise
    blurred = cv2.GaussianBlur(
        gray,
        (default_params['blur_kernel'], default_params['blur_kernel']),
        0
    )
    
    # Deteksi lingkaran menggunakan Hough Transform
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=default_params['dp'],
        minDist=default_params['minDist'],
        param1=default_params['param1'],
        param2=default_params['param2'],
        minRadius=default_params['minRadius'],
        maxRadius=default_params['maxRadius']
    )
    
    detections = []
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for circle in circles[0, :]:
            x, y, r = int(circle[0]), int(circle[1]), int(circle[2])
            detections.append((x, y, r))
    
    return detections
```

### 1.3 Metode 2: Contour-Based Detection

```python
"""
Deteksi pupil/mata menggunakan analisis kontur dan ellipse fitting.
Metode ini menganalisis bentuk kontur untuk menemukan pupil.
"""

def detect_contour(
    frame: np.ndarray,
    params: Optional[Dict[str, Any]] = None
) -> List[Tuple[int, int, int]]:
    """
    Deteksi pupil/mata menggunakan analisis kontur dan ellipse fitting.
    
    Args:
        frame: Input frame (BGR atau grayscale)
        params: Parameter deteksi dengan key:
            - threshold_value: Nilai threshold binary (default: 30)
            - min_area: Area kontur minimum (default: 100)
            - max_area: Area kontur maximum (default: 5000)
            - circularity_threshold: Circularity minimum 0-1 (default: 0.7)
            - blur_kernel: Ukuran kernel Gaussian blur (default: 5)
    
    Returns:
        List dari tuple (x, y, radius) untuk pupil yang terdeteksi
    """
    # Parameter default
    default_params = {
        'threshold_value': 30,
        'min_area': 100,
        'max_area': 5000,
        'circularity_threshold': 0.7,
        'blur_kernel': 5
    }
    
    if params:
        default_params.update(params)
    
    # Konversi ke grayscale jika perlu
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame.copy()
    
    # Terapkan Gaussian blur
    blurred = cv2.GaussianBlur(
        gray,
        (default_params['blur_kernel'], default_params['blur_kernel']),
        0
    )
    
    # Terapkan binary threshold (pupil biasanya lebih gelap)
    _, binary = cv2.threshold(
        blurred,
        default_params['threshold_value'],
        255,
        cv2.THRESH_BINARY_INV
    )
    
    # Cari kontur
    contours, _ = cv2.findContours(
        binary,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )
    
    detections = []
    for contour in contours:
        area = cv2.contourArea(contour)
        
        # Filter berdasarkan area
        if area < default_params['min_area'] or area > default_params['max_area']:
            continue
        
        # Hitung circularity
        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            continue
        
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        
        # Filter berdasarkan circularity
        if circularity < default_params['circularity_threshold']:
            continue
        
        # Fit ellipse jika kontur memiliki cukup titik
        if len(contour) >= 5:
            try:
                ellipse = cv2.fitEllipse(contour)
                center_x = int(ellipse[0][0])
                center_y = int(ellipse[0][1])
                radius = int((ellipse[1][0] + ellipse[1][1]) / 4)
                
                detections.append((center_x, center_y, radius))
            except:
                # Jika ellipse fitting gagal, gunakan center berbasis moment
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    radius = int(np.sqrt(area / np.pi))
                    detections.append((cx, cy, radius))
    
    return detections
```

### 1.4 Metode 3: Color-Based Detection

```python
"""
Deteksi pupil/mata menggunakan segmentasi warna di HSV space.
Metode ini menggunakan informasi warna untuk menemukan pupil.
"""

def detect_color(
    frame: np.ndarray,
    params: Optional[Dict[str, Any]] = None
) -> List[Tuple[int, int, int]]:
    """
    Deteksi pupil/mata menggunakan segmentasi warna di HSV space.
    
    Args:
        frame: Input frame (harus BGR)
        params: Parameter deteksi dengan key:
            - lower_hsv: Lower bound HSV (default: [0, 0, 0])
            - upper_hsv: Upper bound HSV (default: [180, 255, 50])
            - min_area: Area minimum (default: 100)
            - max_area: Area maximum (default: 5000)
            - blur_kernel: Ukuran kernel blur (default: 5)
    
    Returns:
        List dari tuple (x, y, radius) untuk pupil yang terdeteksi
    """
    # Parameter default untuk deteksi warna gelap (pupil)
    default_params = {
        'lower_hsv': np.array([0, 0, 0]),
        'upper_hsv': np.array([180, 255, 50]),
        'min_area': 100,
        'max_area': 5000,
        'blur_kernel': 5
    }
    
    if params:
        default_params.update(params)
    
    # Konversi ke HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Buat mask berdasarkan range warna
    mask = cv2.inRange(hsv, default_params['lower_hsv'], default_params['upper_hsv'])
    
    # Terapkan morfologi untuk membersihkan noise
    kernel = np.ones((default_params['blur_kernel'], default_params['blur_kernel']), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    # Cari kontur pada mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    detections = []
    for contour in contours:
        area = cv2.contourArea(contour)
        
        # Filter berdasarkan area
        if area < default_params['min_area'] or area > default_params['max_area']:
            continue
        
        # Hitung center dan radius
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            radius = int(np.sqrt(area / np.pi))
            detections.append((cx, cy, radius))
    
    return detections
```

### 1.5 Implementasi Pipeline Perbandingan

```python
"""
Pipeline untuk membandingkan performa berbagai algoritma deteksi.
"""

def compare_detection_algorithms(
    video_path: str,
    output_dir: str,
    algorithms: List[str] = ['hough', 'contour', 'color']
) -> pd.DataFrame:
    """
    Membandingkan performa berbagai algoritma deteksi pada video.
    
    Args:
        video_path: Path ke video input
        output_dir: Directory untuk menyimpan hasil
        algorithms: List nama algoritma yang akan dibandingkan
    
    Returns:
        DataFrame dengan hasil perbandingan
    """
    import time
    
    # Mapping algoritma ke fungsi
    algo_functions = {
        'hough': detect_hough_circle,
        'contour': detect_contour,
        'color': detect_color
    }
    
    cap = cv2.VideoCapture(video_path)
    results = {algo: [] for algo in algorithms}
    processing_times = {algo: [] for algo in algorithms}
    
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Test setiap algoritma
        for algo in algorithms:
            start_time = time.time()
            detections = algo_functions[algo](frame)
            end_time = time.time()
            
            processing_times[algo].append(end_time - start_time)
            results[algo].append({
                'frame': frame_count,
                'detections': len(detections),
                'positions': detections
            })
    
    cap.release()
    
    # Buat summary DataFrame
    summary_data = []
    for algo in algorithms:
        avg_time = np.mean(processing_times[algo])
        detection_rate = sum(1 for r in results[algo] if r['detections'] > 0) / frame_count
        
        summary_data.append({
            'Algorithm': algo,
            'Avg_Processing_Time_ms': avg_time * 1000,
            'Detection_Rate': detection_rate * 100,
            'Total_Frames': frame_count
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(os.path.join(output_dir, 'algorithm_comparison.csv'), index=False)
    
    return summary_df
```

---

## Lampiran 2. Kode Gim Matematika Sederhana

### 2.1 Deteksi Gaze untuk Game

```python
"""
Modul deteksi gaze untuk game interaktif menggunakan eye tracker.
"""

import cv2
import numpy as np

# Parameter Hough Circle Transform
HOUGH_PARAM1 = 50
HOUGH_PARAM2 = 13
MIN_RADIUS = 65
MAX_RADIUS = 80

def detect_gaze_hough(frame: np.ndarray, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Deteksi posisi gaze menggunakan Hough Circle Transform.
    
    Args:
        frame: Frame BGR dari kamera
        params: Parameter deteksi (param1, param2, minRadius, maxRadius)
        
    Returns:
        Dictionary dengan 'center' (x, y) dan 'radius', atau None jika tidak terdeteksi
    """
    if params is None:
        params = {
            'param1': HOUGH_PARAM1,
            'param2': HOUGH_PARAM2,
            'minRadius': MIN_RADIUS,
            'maxRadius': MAX_RADIUS,
            'blur_kernel': 5
        }
    
    # Konversi ke grayscale dan terapkan blur
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, params.get('blur_kernel', 5))
    
    # Deteksi lingkaran
    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=1000,
        param1=params.get('param1', 50),
        param2=params.get('param2', 13),
        minRadius=params.get('minRadius', 65),
        maxRadius=params.get('maxRadius', 80)
    )
    
    if circles is not None:
        circle = np.uint16(np.around(circles[0, 0]))
        return {
            'center': (int(circle[0]), int(circle[1])),
            'radius': int(circle[2])
        }
    
    return None


class KalmanGazeFilter:
    """Kalman filter untuk smoothing trajektori gaze dalam game."""
    
    def __init__(self):
        """Inisialisasi Kalman filter untuk tracking gaze 2D."""
        self.kf = cv2.KalmanFilter(4, 2)  # 4 state vars, 2 measurements
        
        # Measurement matrix
        self.kf.measurementMatrix = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ], dtype=np.float32)
        
        # Transition matrix
        self.kf.transitionMatrix = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        
        # Process noise covariance
        self.kf.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03
        
        # Measurement noise covariance
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 10.0
        
        # Error covariance
        self.kf.errorCovPost = np.eye(4, dtype=np.float32)
        
        self.initialized = False
    
    def update(self, gaze_pos: Tuple[int, int]) -> Tuple[int, int]:
        """
        Update Kalman filter dengan posisi gaze baru.
        
        Args:
            gaze_pos: Tuple (x, y) posisi gaze
            
        Returns:
            Tuple (x, y) posisi yang sudah di-smooth
        """
        if not self.initialized:
            # Inisialisasi state dengan posisi pertama
            self.kf.statePre = np.array([
                [gaze_pos[0]], [gaze_pos[1]], [0], [0]
            ], dtype=np.float32)
            self.kf.statePost = np.array([
                [gaze_pos[0]], [gaze_pos[1]], [0], [0]
            ], dtype=np.float32)
            self.initialized = True
            return gaze_pos
        
        # Predict
        prediction = self.kf.predict()
        
        # Update dengan measurement
        measurement = np.array([[gaze_pos[0]], [gaze_pos[1]]], dtype=np.float32)
        corrected = self.kf.correct(measurement)
        
        # Return corrected position
        return (int(corrected[0][0]), int(corrected[1][0]))
```

### 2.2 Game Button dengan Hover Detection

```python
"""
Kelas untuk tombol game dengan deteksi hover berbasis gaze.
"""

import pygame
from typing import Dict, Tuple

class GameButton:
    """Tombol game yang dapat diaktifkan dengan gaze."""
    
    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        button_type: str = 'normal',
        hover_duration: float = 3.0
    ):
        """
        Inisialisasi game button.
        
        Args:
            rect: pygame.Rect untuk posisi dan ukuran button
            text: Text yang ditampilkan pada button
            button_type: Tipe button ('correct', 'wrong', 'start', 'exit', 'normal')
            hover_duration: Durasi hover dalam detik untuk aktivasi
        """
        self.rect = rect
        self.text = text
        self.button_type = button_type
        self.hover_duration = hover_duration
        self.hover_start_time = None
        self.hover_progress = 0.0
        self.is_hovered = False
    
    def update_hover(self, gaze_pos: Tuple[int, int], current_time: float) -> bool:
        """
        Update status hover berdasarkan posisi gaze.
        
        Args:
            gaze_pos: Tuple (x, y) posisi gaze
            current_time: Waktu saat ini dalam detik
            
        Returns:
            True jika button diaktifkan (hover selesai), False jika tidak
        """
        # Cek apakah gaze ada di dalam button
        if self.rect.collidepoint(gaze_pos):
            if not self.is_hovered:
                # Mulai hover
                self.is_hovered = True
                self.hover_start_time = current_time
            else:
                # Update progress hover
                elapsed = current_time - self.hover_start_time
                self.hover_progress = min(elapsed / self.hover_duration, 1.0)
                
                # Cek apakah sudah mencapai durasi hover
                if self.hover_progress >= 1.0:
                    return True  # Button activated
        else:
            # Reset hover jika gaze keluar
            self.is_hovered = False
            self.hover_start_time = None
            self.hover_progress = 0.0
        
        return False
    
    def draw(
        self,
        screen: pygame.Surface,
        colors: Dict[str, Tuple[int, int, int]],
        font: pygame.font.Font
    ):
        """
        Gambar button di layar.
        
        Args:
            screen: Pygame surface
            colors: Dictionary skema warna
            font: Font untuk text
        """
        # Tentukan warna button berdasarkan tipe
        if self.button_type == 'correct':
            base_color = (0, 180, 0)  # Hijau
        elif self.button_type == 'wrong':
            base_color = (255, 0, 0)  # Merah
        elif self.button_type == 'start':
            base_color = (0, 150, 255)  # Biru
        elif self.button_type == 'exit':
            base_color = (150, 10, 10)  # Merah gelap
        else:
            base_color = colors['tombol']
        
        # Terapkan efek hover
        if self.is_hovered:
            hover_color = colors['hover']
            # Blend warna berdasarkan progress hover
            final_color = tuple(
                int(base_color[i] * (1 - self.hover_progress * 0.3) + 
                    hover_color[i] * (self.hover_progress * 0.3))
                for i in range(3)
            )
        else:
            final_color = base_color
        
        # Gambar background button
        pygame.draw.rect(screen, final_color, self.rect, border_radius=10)
        pygame.draw.rect(screen, colors['outline'], self.rect, 3, border_radius=10)
        
        # Gambar progress bar hover
        if self.hover_progress > 0:
            progress_rect = pygame.Rect(
                self.rect.x,
                self.rect.bottom - 8,
                int(self.rect.width * self.hover_progress),
                8
            )
            pygame.draw.rect(screen, (0, 255, 0), progress_rect, border_radius=4)
        
        # Gambar text
        text_surf = font.render(self.text, True, colors['teks_biasa'])
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
```

### 2.3 Question Management

```python
"""
Manajemen pertanyaan untuk game matematika.
"""

import pandas as pd
from typing import List, Dict

def get_default_questions() -> Dict[str, List[Dict[str, str]]]:
    """
    Dapatkan set pertanyaan default untuk tutorial dan game utama.
    
    Returns:
        Dictionary dengan list pertanyaan 'tutorial' dan 'main'
    """
    return {
        'tutorial': [
            {"soal": "1 + 1 = 2", "jawaban": "benar"},
            {"soal": "2 + 2 = 5", "jawaban": "salah"}
        ],
        'main': [
            {"soal": "8 × 7 = 56", "jawaban": "benar"},
            {"soal": "125 + 275 = 400", "jawaban": "benar"},
            {"soal": "99 - 19 = 70", "jawaban": "salah"},
            {"soal": "36 ÷ 6 = 6", "jawaban": "benar"},
            {"soal": "5² = 20", "jawaban": "salah"},
            {"soal": "7 × 7 = 49", "jawaban": "benar"},
            {"soal": "144 ÷ 12 = 12", "jawaban": "benar"},
            {"soal": "15 + 28 = 44", "jawaban": "salah"},
            {"soal": "200 - 85 = 115", "jawaban": "benar"},
            {"soal": "9 × 9 = 81", "jawaban": "benar"}
        ]
    }


def load_questions_from_excel(file_path: str) -> List[Dict[str, str]]:
    """
    Load pertanyaan dari file Excel.
    
    Expected columns: 'question' (atau 'soal'), 'answer' (atau 'jawaban')
    Answer harus 'benar'/'salah' atau 'correct'/'wrong'
    
    Args:
        file_path: Path ke file Excel
        
    Returns:
        List dictionary pertanyaan
    """
    try:
        df = pd.read_excel(file_path)
        
        # Deteksi nama kolom
        question_col = None
        answer_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'question' in col_lower or 'soal' in col_lower:
                question_col = col
            if 'answer' in col_lower or 'jawaban' in col_lower:
                answer_col = col
        
        if not question_col or not answer_col:
            print(f"Error: Tidak dapat menemukan kolom question/answer di {file_path}")
            return []
        
        questions = []
        for _, row in df.iterrows():
            question_text = str(row[question_col]).strip()
            answer_text = str(row[answer_col]).strip().lower()
            
            # Normalisasi jawaban
            if answer_text in ['benar', 'correct', 'true', 'yes', '1']:
                answer = 'benar'
            elif answer_text in ['salah', 'wrong', 'false', 'no', '0']:
                answer = 'salah'
            else:
                print(f"Warning: Jawaban tidak dikenali '{answer_text}' untuk soal '{question_text}'")
                continue
            
            questions.append({
                'soal': question_text,
                'jawaban': answer
            })
        
        print(f"Loaded {len(questions)} pertanyaan dari {file_path}")
        return questions
        
    except Exception as e:
        print(f"Error loading questions dari Excel: {str(e)}")
        return []
```

### 2.4 ROI Detection

```python
"""
Deteksi Region of Interest (ROI) untuk tracking gaze di game.
"""

import pygame
from typing import Tuple, List

def get_roi_at_position(
    gaze_pos: Tuple[int, int],
    question_text_rect: pygame.Rect,
    buttons: List[GameButton],
    screen_size: Tuple[int, int]
) -> str:
    """
    Tentukan ROI mana yang sedang dilihat oleh gaze.
    
    Args:
        gaze_pos: Posisi gaze (x, y)
        question_text_rect: Rectangle untuk area text pertanyaan
        buttons: List game buttons
        screen_size: (width, height) layar
        
    Returns:
        Nama ROI: 'question_text', 'button_benar', 'button_salah', 
                  'button_exit', 'button_start', 'background'
    """
    # Cek area text pertanyaan
    if question_text_rect.collidepoint(gaze_pos):
        return 'question_text'
    
    # Cek buttons
    for button in buttons:
        if button.rect.collidepoint(gaze_pos):
            if button.button_type == 'correct':
                return 'button_benar'
            elif button.button_type == 'wrong':
                return 'button_salah'
            elif button.button_type == 'exit':
                return 'button_exit'
            elif button.button_type == 'start':
                return 'button_start'
    
    return 'background'
```

### 2.5 Game Session Recorder

```python
"""
Recorder untuk merekam data session game untuk analisis.
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Any

class GameSessionRecorder:
    """Merekam data session game untuk analisis."""
    
    def __init__(self, session_dir: str, session_id: str, participant_id: str = "Unknown"):
        """
        Inisialisasi recorder.
        
        Args:
            session_dir: Directory untuk menyimpan data session
            session_id: Unique session identifier
            participant_id: Identifier partisipan
        """
        self.session_dir = session_dir
        self.session_id = session_id
        self.participant_id = participant_id
        
        # Buat directory jika belum ada
        os.makedirs(session_dir, exist_ok=True)
        
        # Data storage
        self.gaze_data = []
        self.question_data = []
        self.event_data = []
        
        # Session metadata
        self.session_start_time = datetime.now()
        self.session_metadata = {
            'session_id': session_id,
            'participant_id': participant_id,
            'start_time': self.session_start_time.isoformat()
        }
    
    def record_gaze(
        self,
        timestamp: float,
        gaze_x: int,
        gaze_y: int,
        roi: str,
        question_id: int = -1
    ):
        """
        Rekam data gaze point.
        
        Args:
            timestamp: Timestamp dalam detik
            gaze_x: Koordinat x gaze
            gaze_y: Koordinat y gaze
            roi: Region of Interest yang sedang dilihat
            question_id: ID pertanyaan saat ini (-1 jika tidak ada)
        """
        self.gaze_data.append({
            'timestamp': timestamp,
            'gaze_x': gaze_x,
            'gaze_y': gaze_y,
            'roi': roi,
            'question_id': question_id
        })
    
    def record_question(
        self,
        question_id: int,
        question_text: str,
        correct_answer: str,
        user_answer: str,
        is_correct: bool,
        response_time: float,
        start_time: float,
        end_time: float
    ):
        """
        Rekam data pertanyaan.
        
        Args:
            question_id: ID pertanyaan
            question_text: Text pertanyaan
            correct_answer: Jawaban yang benar
            user_answer: Jawaban user
            is_correct: Apakah jawaban benar
            response_time: Waktu respons dalam detik
            start_time: Waktu mulai pertanyaan
            end_time: Waktu selesai pertanyaan
        """
        self.question_data.append({
            'question_id': question_id,
            'question_text': question_text,
            'correct_answer': correct_answer,
            'user_answer': user_answer,
            'is_correct': is_correct,
            'response_time': response_time,
            'start_time': start_time,
            'end_time': end_time
        })
    
    def record_event(
        self,
        timestamp: float,
        event_type: str,
        event_data: Dict[str, Any]
    ):
        """
        Rekam event game.
        
        Args:
            timestamp: Timestamp dalam detik
            event_type: Tipe event (e.g., 'button_hover', 'button_click', 'question_start')
            event_data: Data tambahan untuk event
        """
        self.event_data.append({
            'timestamp': timestamp,
            'event_type': event_type,
            **event_data
        })
    
    def save_session(self):
        """Simpan semua data session ke file."""
        # Simpan gaze data
        if self.gaze_data:
            gaze_df = pd.DataFrame(self.gaze_data)
            gaze_path = os.path.join(self.session_dir, f'gaze_data_{self.session_id}.csv')
            gaze_df.to_csv(gaze_path, index=False)
            print(f"Gaze data saved to: {gaze_path}")
        
        # Simpan question data
        if self.question_data:
            question_df = pd.DataFrame(self.question_data)
            question_path = os.path.join(self.session_dir, f'question_data_{self.session_id}.csv')
            question_df.to_csv(question_path, index=False)
            print(f"Question data saved to: {question_path}")
        
        # Simpan event data
        if self.event_data:
            event_df = pd.DataFrame(self.event_data)
            event_path = os.path.join(self.session_dir, f'event_data_{self.session_id}.csv')
            event_df.to_csv(event_path, index=False)
            print(f"Event data saved to: {event_path}")
        
        # Simpan metadata
        metadata_path = os.path.join(self.session_dir, f'session_metadata_{self.session_id}.txt')
        with open(metadata_path, 'w') as f:
            for key, value in self.session_metadata.items():
                f.write(f"{key}: {value}\n")
        
        print(f"Session metadata saved to: {metadata_path}")
```

### 2.6 Main Game Loop

```python
"""
Main game loop untuk game matematika interaktif dengan eye tracking.
"""

import pygame
import cv2
import time
from typing import Dict, List

def run_math_game(
    camera_index: int = 0,
    questions: List[Dict[str, str]] = None,
    session_dir: str = './sessions'
) -> Dict[str, Any]:
    """
    Jalankan game matematika dengan eye tracking.
    
    Args:
        camera_index: Index kamera virtual (eye tracker)
        questions: List pertanyaan game
        session_dir: Directory untuk menyimpan session data
        
    Returns:
        Dictionary hasil session
    """
    # Inisialisasi Pygame
    pygame.init()
    screen_width, screen_height = 1920, 1080
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
    pygame.display.set_caption("Game Matematika Eye-Controlled")
    clock = pygame.time.Clock()
    font_large = pygame.font.Font(None, 80)
    font_medium = pygame.font.Font(None, 50)
    
    # Inisialisasi kamera
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("Error: Tidak dapat membuka kamera")
        return None
    
    # Inisialisasi Kalman filter
    kalman_filter = KalmanGazeFilter()
    
    # Load pertanyaan
    if questions is None:
        questions = get_default_questions()['main']
    
    # Inisialisasi recorder
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    recorder = GameSessionRecorder(session_dir, session_id)
    
    # Skema warna
    colors = {
        "latar": (20, 20, 20),
        "teks_soal": (220, 220, 220),
        "teks_biasa": (255, 255, 255),
        "tombol": (50, 50, 50),
        "hover": (80, 80, 80),
        "outline": (150, 150, 150)
    }
    
    # Setup buttons
    button_width, button_height = 300, 100
    button_y = screen_height - 200
    button_benar = GameButton(
        pygame.Rect(screen_width // 2 - button_width - 50, button_y, button_width, button_height),
        "BENAR",
        "correct"
    )
    button_salah = GameButton(
        pygame.Rect(screen_width // 2 + 50, button_y, button_width, button_height),
        "SALAH",
        "wrong"
    )
    button_exit = GameButton(
        pygame.Rect(50, 50, 150, 60),
        "KELUAR",
        "exit",
        hover_duration=3.0
    )
    
    buttons = [button_benar, button_salah, button_exit]
    
    # Game state
    current_question = 0
    question_start_time = time.time()
    game_running = True
    score = 0
    
    # Main game loop
    while game_running and current_question < len(questions):
        current_time = time.time()
        
        # Baca frame dari kamera
        ret, frame = cap.read()
        if not ret:
            print("Error: Tidak dapat membaca frame dari kamera")
            break
        
        # Deteksi gaze
        gaze_result = detect_gaze_hough(frame)
        gaze_pos = None
        
        if gaze_result:
            # Smooth dengan Kalman filter
            raw_gaze = gaze_result['center']
            gaze_pos = kalman_filter.update(raw_gaze)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_running = False
        
        # Clear screen
        screen.fill(colors["latar"])
        
        # Draw question
        question_obj = questions[current_question]
        question_text = font_large.render(question_obj['soal'], True, colors["teks_soal"])
        question_rect = question_text.get_rect(center=(screen_width // 2, screen_height // 2 - 100))
        screen.blit(question_text, question_rect)
        
        # Update and draw buttons
        if gaze_pos:
            # Rekam gaze data
            roi = get_roi_at_position(gaze_pos, question_rect, buttons, (screen_width, screen_height))
            recorder.record_gaze(current_time, gaze_pos[0], gaze_pos[1], roi, current_question)
            
            # Update button hover
            for button in buttons:
                if button.update_hover(gaze_pos, current_time):
                    # Button activated
                    if button.button_type == 'exit':
                        game_running = False
                    elif button.button_type in ['correct', 'wrong']:
                        # Process answer
                        user_answer = 'benar' if button.button_type == 'correct' else 'salah'
                        is_correct = user_answer == question_obj['jawaban']
                        response_time = current_time - question_start_time
                        
                        if is_correct:
                            score += 1
                        
                        # Record question data
                        recorder.record_question(
                            current_question,
                            question_obj['soal'],
                            question_obj['jawaban'],
                            user_answer,
                            is_correct,
                            response_time,
                            question_start_time,
                            current_time
                        )
                        
                        # Next question
                        current_question += 1
                        question_start_time = time.time()
                        
                        # Reset all button states
                        for btn in buttons:
                            btn.is_hovered = False
                            btn.hover_progress = 0.0
                            btn.hover_start_time = None
            
            # Draw gaze cursor
            pygame.draw.circle(screen, (255, 255, 0), gaze_pos, 15)
        
        # Draw all buttons
        for button in buttons:
            button.draw(screen, colors, font_medium)
        
        # Draw score
        score_text = font_medium.render(f"Skor: {score}/{current_question}", True, colors["teks_biasa"])
        screen.blit(score_text, (screen_width - 250, 50))
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    # Cleanup
    cap.release()
    recorder.save_session()
    pygame.quit()
    
    # Return results
    return {
        'session_id': session_id,
        'total_questions': len(questions),
        'score': score,
        'accuracy': score / len(questions) * 100 if questions else 0
    }


if __name__ == "__main__":
    # Jalankan game
    result = run_math_game(
        camera_index=0,  # Index kamera virtual Tobii
        session_dir='./game_sessions'
    )
    
    if result:
        print(f"\n=== HASIL GAME ===")
        print(f"Session ID: {result['session_id']}")
        print(f"Skor: {result['score']}/{result['total_questions']}")
        print(f"Akurasi: {result['accuracy']:.1f}%")
```

---

## Penjelasan Umum

### Lampiran 1: Pembanding Algoritma Deteksi
Kode pada Lampiran 1 mengimplementasikan tiga algoritma deteksi titik pandang mata:
1. **Hough Circle Transform**: Deteksi berbasis geometri lingkaran
2. **Contour-Based**: Analisis kontur dan ellipse fitting
3. **Color-Based**: Segmentasi warna di HSV space

Semua algoritma dilengkapi dengan Kalman Filter untuk smoothing trajektori dan mengurangi noise.

### Lampiran 2: Game Matematika
Kode pada Lampiran 2 mengimplementasikan game matematika interaktif yang dikontrol dengan eye tracking:
- Deteksi gaze menggunakan Hough Circle Transform
- Smoothing dengan Kalman Filter
- Sistem button dengan hover detection
- Recording session data untuk analisis
- ROI (Region of Interest) tracking

### Dependencies
```
opencv-python>=4.8.0
numpy>=1.24.0
pygame>=2.5.0
pandas>=2.0.0
matplotlib>=3.7.0
```

### Cara Penggunaan

**Untuk Pembanding Algoritma:**
```python
from detection_algorithms import compare_detection_algorithms

results = compare_detection_algorithms(
    video_path='path/to/video.mp4',
    output_dir='./output',
    algorithms=['hough', 'contour', 'color']
)
print(results)
```

**Untuk Game Matematika:**
```python
from game_engine import run_math_game, get_default_questions

questions = get_default_questions()['main']
result = run_math_game(
    camera_index=0,
    questions=questions,
    session_dir='./sessions'
)
```

---

**Catatan**: Kode ini merupakan bagian dari sistem eye tracking untuk Tugas Akhir dengan judul "Sistem Deteksi Titik Pandang Mata dan Game Matematika Interaktif". Untuk dokumentasi lengkap, lihat file dokumentasi di folder `docs/`.

---

**Tanggal**: Januari 2026  
**Author**: Eye Tracker Research Project
