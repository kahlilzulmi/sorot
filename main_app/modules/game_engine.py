"""
Game Engine Module
Eye-controlled math quiz game with real-time tracking and recording.

Features:
- Real-time gaze detection using Tobii Eye Tracker + OBS Virtual Camera
- Math quiz questions with eye-controlled buttons
- Tutorial and main game modes
- Session recording with detailed analytics
- F12 debug overlay toggle
- Excel question import support
- Adaptive parameter learning

Author: Eye Tracker Research Project
Date: November 2025
"""

import cv2
import numpy as np
import pygame
import pandas as pd
import time
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

from utils.logger import log_info, log_warning, log_error
from utils.config_manager import load_config, save_config


# ============================================================================
# GAZE DETECTION
# ============================================================================

def detect_gaze_hough(frame: np.ndarray, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Detect gaze position using Hough Circle Transform.
    
    Args:
        frame: BGR frame from camera
        params: Detection parameters (param1, param2, minRadius, maxRadius)
        
    Returns:
        Dictionary with 'center' (x, y) and 'radius', or None if not detected
    """
    if params is None:
        params = {
            'param1': 50,
            'param2': 13,
            'minRadius': 65,
            'maxRadius': 80,
            'blur_kernel': 5
        }
    
    # Convert to grayscale and apply blur
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, params.get('blur_kernel', 5))
    
    # Detect circles
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
    """Kalman filter for smoothing gaze trajectories."""
    
    def __init__(self):
        """Initialize Kalman filter for 2D gaze tracking."""
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
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 5.0
        
        self.initialized = False
    
    def update(self, measurement: Tuple[int, int]) -> Tuple[int, int]:
        """
        Update filter with new measurement.
        
        Args:
            measurement: (x, y) gaze position
            
        Returns:
            Filtered (x, y) position
        """
        measurement_array = np.array([[measurement[0]], [measurement[1]]], dtype=np.float32)
        
        if not self.initialized:
            # Initialize state
            self.kf.statePost = np.array([
                [measurement[0]],
                [measurement[1]],
                [0],
                [0]
            ], dtype=np.float32)
            self.initialized = True
            return measurement
        
        # Predict
        prediction = self.kf.predict()
        
        # Correct
        estimated = self.kf.correct(measurement_array)
        
        return (int(estimated[0][0]), int(estimated[1][0]))
    
    def reset(self):
        """Reset the filter."""
        self.initialized = False


# ============================================================================
# BUTTON AND UI ELEMENTS
# ============================================================================

class GameButton:
    """Represents a clickable button in the game."""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, button_type: str):
        """
        Initialize button.
        
        Args:
            x, y: Top-left position
            width, height: Button dimensions
            text: Button label
            button_type: 'correct', 'wrong', 'start', 'exit'
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.button_type = button_type
        self.hover_time = 0.0
        self.hover_progress = 0.0
        self.is_hovered = False
        self.last_hover_update = time.time()
    
    def update_hover(self, gaze_pos: Optional[Tuple[int, int]], hover_duration: float):
        """
        Update hover state based on gaze position.
        
        Args:
            gaze_pos: Current gaze (x, y) or None
            hover_duration: Duration required for click
        """
        current_time = time.time()
        dt = current_time - self.last_hover_update
        self.last_hover_update = current_time
        
        if gaze_pos and self.rect.collidepoint(gaze_pos):
            self.is_hovered = True
            self.hover_time += dt
            self.hover_progress = min(1.0, self.hover_time / hover_duration)
        else:
            self.is_hovered = False
            # Decay hover time
            self.hover_time = max(0, self.hover_time - dt * 2)
            self.hover_progress = min(1.0, self.hover_time / hover_duration)
    
    def is_clicked(self, hover_duration: float) -> bool:
        """Check if button was clicked (hover completed)."""
        return self.hover_time >= hover_duration
    
    def reset_hover(self):
        """Reset hover state."""
        self.hover_time = 0.0
        self.hover_progress = 0.0
        self.is_hovered = False
    
    def draw(self, screen: pygame.Surface, colors: Dict[str, Tuple[int, int, int]], font: pygame.font.Font):
        """
        Draw button on screen.
        
        Args:
            screen: Pygame surface
            colors: Color scheme dictionary
            font: Font for text
        """
        # Determine button color
        if self.button_type == 'correct':
            base_color = (0, 180, 0)  # Green
        elif self.button_type == 'wrong':
            base_color = (255, 0, 0)  # Red
        elif self.button_type == 'start':
            base_color = (0, 150, 255)  # Blue
        elif self.button_type == 'exit':
            base_color = (150, 10, 10)  # Dark red
        else:
            base_color = colors['tombol']
        
        # Apply hover effect
        if self.is_hovered:
            hover_color = colors['hover']
            # Blend colors based on hover progress
            final_color = tuple(
                int(base_color[i] * (1 - self.hover_progress * 0.3) + hover_color[i] * (self.hover_progress * 0.3))
                for i in range(3)
            )
        else:
            final_color = base_color
        
        # Draw button background
        pygame.draw.rect(screen, final_color, self.rect, border_radius=10)
        pygame.draw.rect(screen, colors['outline'], self.rect, 3, border_radius=10)
        
        # Draw hover progress bar
        if self.hover_progress > 0:
            progress_rect = pygame.Rect(
                self.rect.x,
                self.rect.bottom - 8,
                int(self.rect.width * self.hover_progress),
                8
            )
            pygame.draw.rect(screen, (0, 255, 0), progress_rect, border_radius=4)
        
        # Draw text
        text_surf = font.render(self.text, True, colors['teks_biasa'])
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)


# ============================================================================
# QUESTION MANAGEMENT
# ============================================================================

def load_questions_from_excel(file_path: str) -> List[Dict[str, str]]:
    """
    Load questions from Excel file.
    
    Expected columns: 'question' (or 'soal'), 'answer' (or 'jawaban')
    Answer should be 'benar'/'salah' or 'correct'/'wrong'
    
    Args:
        file_path: Path to Excel file
        
    Returns:
        List of question dictionaries
    """
    try:
        df = pd.read_excel(file_path)
        
        # Detect column names
        question_col = None
        answer_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'question' in col_lower or 'soal' in col_lower:
                question_col = col
            if 'answer' in col_lower or 'jawaban' in col_lower:
                answer_col = col
        
        if not question_col or not answer_col:
            log_error(f"Could not find question/answer columns in {file_path}")
            return []
        
        questions = []
        for _, row in df.iterrows():
            question_text = str(row[question_col]).strip()
            answer_text = str(row[answer_col]).strip().lower()
            
            # Normalize answer
            if answer_text in ['benar', 'correct', 'true', 'yes', '1']:
                answer = 'benar'
            elif answer_text in ['salah', 'wrong', 'false', 'no', '0']:
                answer = 'salah'
            else:
                log_warning(f"Unknown answer '{answer_text}' for question '{question_text}'")
                continue
            
            questions.append({
                'soal': question_text,
                'jawaban': answer
            })
        
        log_info(f"Loaded {len(questions)} questions from {file_path}")
        return questions
        
    except Exception as e:
        log_error(f"Error loading questions from Excel: {str(e)}")
        return []


def get_default_questions() -> Dict[str, List[Dict[str, str]]]:
    """
    Get default question sets for tutorial and main game.
    
    Returns:
        Dictionary with 'tutorial' and 'main' question lists
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


# ============================================================================
# ROI DETECTION
# ============================================================================

def get_roi_at_position(
    gaze_pos: Tuple[int, int],
    question_text_rect: pygame.Rect,
    buttons: List[GameButton],
    screen_size: Tuple[int, int]
) -> str:
    """
    Determine which ROI (Region of Interest) the gaze is at.
    
    Args:
        gaze_pos: Gaze (x, y) position
        question_text_rect: Rectangle for question text area
        buttons: List of game buttons
        screen_size: (width, height) of screen
        
    Returns:
        ROI name: 'question_text', 'button_benar', 'button_salah', 'button_exit', 'background'
    """
    # Check question text area
    if question_text_rect.collidepoint(gaze_pos):
        return 'question_text'
    
    # Check buttons
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


# ============================================================================
# SESSION DATA RECORDER
# ============================================================================

class GameSessionRecorder:
    """Records game session data for analysis."""
    
    def __init__(self, session_dir: str, session_id: str, participant_id: str = "Unknown"):
        """
        Initialize recorder.
        
        Args:
            session_dir: Directory to save session data
            session_id: Unique session identifier
            participant_id: Participant identifier
        """
        self.session_dir = session_dir
        self.session_id = session_id
        self.participant_id = participant_id
        self.gaze_data = []
        self.question_data = []
        self.session_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.session_start_time = time.time()
        self.current_question_index = -1
        self.current_question_start_time = None
        
        # Create session directory
        os.makedirs(session_dir, exist_ok=True)
        
        log_info(f"Game session recorder initialized: {session_dir}")
    
    def start_question(self, question_index: int, question_text: str):
        """Mark the start of a new question."""
        self.current_question_index = question_index
        self.current_question_start_time = time.time()
        
        log_info(f"Question {question_index + 1} started: {question_text}")
    
    def record_gaze(
        self,
        gaze_pos: Tuple[int, int],
        roi: str,
        frame_number: int,
        raw_gaze: Optional[Tuple[int, int]] = None
    ):
        """
        Record a gaze data point.
        
        Args:
            gaze_pos: Filtered gaze position
            roi: ROI name where gaze is located
            frame_number: Current frame number
            raw_gaze: Raw (unfiltered) gaze position
        """
        timestamp = time.time() - self.session_start_time
        
        self.gaze_data.append({
            'timestamp': timestamp,
            'frame_number': frame_number,
            'gaze_x': gaze_pos[0],
            'gaze_y': gaze_pos[1],
            'raw_gaze_x': raw_gaze[0] if raw_gaze else gaze_pos[0],
            'raw_gaze_y': raw_gaze[1] if raw_gaze else gaze_pos[1],
            'roi': roi,
            'question_index': self.current_question_index
        })
    
    def end_question(self, answer_given: str, is_correct: bool, response_time: float):
        """
        Mark the end of a question.
        
        Args:
            answer_given: 'benar' or 'salah'
            is_correct: Whether answer was correct
            response_time: Time taken to answer
        """
        if self.current_question_index >= 0:
            self.question_data.append({
                'question_index': self.current_question_index,
                'answer_given': answer_given,
                'is_correct': is_correct,
                'response_time': response_time,
                'timestamp': time.time() - self.session_start_time
            })
            
            log_info(f"Question {self.current_question_index + 1} ended: "
                    f"{'Correct' if is_correct else 'Wrong'} in {response_time:.2f}s")
    
    def save(self) -> Dict[str, str]:
        """
        Save session data to files.
        
        Returns:
            Dictionary with paths to saved files
        """
        files_saved = {}
        
        # Save gaze data
        if self.gaze_data:
            gaze_df = pd.DataFrame(self.gaze_data)
            gaze_path = os.path.join(self.session_dir, "gaze_data.csv")
            gaze_df.to_csv(gaze_path, index=False)
            files_saved['gaze_data'] = gaze_path
            log_info(f"Gaze data saved: {gaze_path} ({len(self.gaze_data)} points)")
        
        # Save question data
        if self.question_data:
            question_df = pd.DataFrame(self.question_data)
            question_path = os.path.join(self.session_dir, "question_data.csv")
            question_df.to_csv(question_path, index=False)
            files_saved['question_data'] = question_path
            log_info(f"Question data saved: {question_path} ({len(self.question_data)} questions)")
        
        # Save session summary
        summary = {
            'participant_id': self.participant_id,
            'session_dir': self.session_dir,
            'start_time': datetime.fromtimestamp(self.session_start_time).isoformat(),
            'duration': time.time() - self.session_start_time,
            'total_questions': len(self.question_data),
            'correct_answers': sum(1 for q in self.question_data if q['is_correct']),
            'total_gaze_points': len(self.gaze_data)
        }
        
        summary_path = os.path.join(self.session_dir, "session_summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            for key, value in summary.items():
                f.write(f"{key}: {value}\n")
        files_saved['summary'] = summary_path
        
        log_info(f"Session summary saved: {summary_path}")
        
        return files_saved


# ============================================================================
# ADAPTIVE PARAMETER LEARNING
# ============================================================================

class AdaptiveParameterLearner:
    """
    Learns and adapts detection parameters based on session performance.
    Uses simple moving average and confidence scoring.
    """
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize learner with config file."""
        self.config_path = config_path
        self.config = load_config(config_path)
        
        # Get current game parameters
        self.game_params = self.config.get('game', {}).get('detection_params', {})
        if not self.game_params:
            self.game_params = {
                'param1': 50,
                'param2': 13,
                'minRadius': 65,
                'maxRadius': 80
            }
        
        self.session_stats = []
    
    def record_session_performance(
        self,
        detection_rate: float,
        avg_detection_confidence: float,
        false_positive_rate: float
    ):
        """
        Record session performance metrics.
        
        Args:
            detection_rate: Percentage of frames with successful detection (0-1)
            avg_detection_confidence: Average confidence score (0-1)
            false_positive_rate: Estimated false positive rate (0-1)
        """
        self.session_stats.append({
            'detection_rate': detection_rate,
            'confidence': avg_detection_confidence,
            'false_positive_rate': false_positive_rate,
            'timestamp': time.time()
        })
        
        log_info(f"Session performance recorded: DR={detection_rate:.2f}, "
                f"Conf={avg_detection_confidence:.2f}, FPR={false_positive_rate:.2f}")
    
    def update_parameters(self) -> Dict[str, Any]:
        """
        Update parameters based on recent session performance.
        
        Returns:
            Updated parameters dictionary
        """
        if len(self.session_stats) < 3:
            log_info("Not enough sessions for parameter adaptation")
            return self.game_params
        
        # Get recent stats (last 5 sessions)
        recent_stats = self.session_stats[-5:]
        
        avg_detection_rate = np.mean([s['detection_rate'] for s in recent_stats])
        avg_confidence = np.mean([s['confidence'] for s in recent_stats])
        
        # Adaptive logic
        updated_params = self.game_params.copy()
        
        # If detection rate is low, try to be more lenient
        if avg_detection_rate < 0.7:
            updated_params['param2'] = max(10, updated_params.get('param2', 13) - 1)
            log_info(f"Low detection rate, decreased param2 to {updated_params['param2']}")
        
        # If detection rate is very high, try to be more strict
        elif avg_detection_rate > 0.95:
            updated_params['param2'] = min(20, updated_params.get('param2', 13) + 1)
            log_info(f"High detection rate, increased param2 to {updated_params['param2']}")
        
        # Update config
        if 'game' not in self.config:
            self.config['game'] = {}
        self.config['game']['detection_params'] = updated_params
        save_config(self.config, self.config_path)
        
        self.game_params = updated_params
        return updated_params
    
    def get_current_parameters(self) -> Dict[str, Any]:
        """Get current detection parameters."""
        return self.game_params.copy()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def init_virtual_camera(camera_index: int = 0) -> Optional[cv2.VideoCapture]:
    """
    Initialize OBS Virtual Camera.
    
    Args:
        camera_index: Camera device index
        
    Returns:
        VideoCapture object or None if failed
    """
    try:
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            log_error(f"Failed to open virtual camera at index {camera_index}")
            return None
        
        # Set properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        
        log_info(f"Virtual camera initialized: index={camera_index}")
        return cap
        
    except Exception as e:
        log_error(f"Error initializing virtual camera: {str(e)}")
        return None


def calculate_screen_layout(
    screen_size: Tuple[int, int],
    mode: str = 'main'
) -> Dict[str, Any]:
    """
    Calculate layout positions for game elements.
    
    Args:
        screen_size: (width, height) of screen
        mode: 'tutorial' or 'main' or 'start'
        
    Returns:
        Dictionary with positions and sizes
    """
    width, height = screen_size
    
    # Question text area (top center)
    question_rect = pygame.Rect(
        width // 4,
        height // 6,
        width // 2,
        height // 5
    )
    
    # Button dimensions
    button_width = 300
    button_height = 100
    button_y = height * 2 // 3
    
    # Correct button (left)
    correct_button = (width // 3 - button_width // 2, button_y, button_width, button_height)
    
    # Wrong button (right)
    wrong_button = (2 * width // 3 - button_width // 2, button_y, button_width, button_height)
    
    # Exit button (bottom right corner)
    exit_button = (width - button_width - 30, height - button_height - 30, button_width, button_height)
    
    # Start button (center, for start screen)
    start_button = (width // 2 - button_width // 2, height // 2, button_width, button_height)
    
    # Next button (center bottom, for navigation)
    next_button = (width // 2 - button_width // 2, height - button_height - 30, button_width, button_height)
    
    return {
        'question_rect': question_rect,
        'question_y': height // 4,  # Y position for question text
        'correct_button': correct_button,
        'wrong_button': wrong_button,
        'benar_button': correct_button,  # Alias
        'salah_button': wrong_button,  # Alias
        'exit_button': exit_button,
        'start_button': start_button,
        'next_button': next_button
    }


if __name__ == "__main__":
    # Test code
    print("Game Engine Module")
    print("Functions available:")
    print("- detect_gaze_hough()")
    print("- KalmanGazeFilter")
    print("- GameButton")
    print("- GameSessionRecorder")
    print("- AdaptiveParameterLearner")
    print("- load_questions_from_excel()")
    print("- get_default_questions()")
