"""
Game Wizard Module
Configuration wizard and launcher for the eye-controlled math quiz game.

Author: Eye Tracker Research Project
Date: November 2025
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pygame
import cv2
import os
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
import numpy as np

from utils.logger import log_info, log_warning, log_error
from utils.config_manager import load_config, save_config
from utils.localization import get_text
from modules.game_engine import (
    init_virtual_camera,
    detect_gaze_hough,
    KalmanGazeFilter,
    GameButton,
    GameSessionRecorder,
    AdaptiveParameterLearner,
    load_questions_from_excel,
    get_default_questions,
    get_roi_at_position,
    calculate_screen_layout
)


# ============================================================================
# GAME WIZARD CLASS
# ============================================================================

class GameWizard:
    """Configuration wizard for the math quiz game."""
    
    def __init__(self, parent):
        """
        Initialize game wizard.
        
        Args:
            parent: Parent Tkinter window
        """
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title(get_text("game.title"))
        self.window.geometry("800x600")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - 400
        y = (self.window.winfo_screenheight() // 2) - 300
        self.window.geometry(f'800x600+{x}+{y}')
        
        # Make modal
        self.window.transient(parent)
        self.window.grab_set()
        
        # Load configuration
        self.config = load_config()
        
        # Game configuration
        self.game_mode = 'tutorial'  # 'tutorial' or 'main'
        self.participant_id = ""
        self.use_custom_questions = False
        self.custom_questions_file = None
        self.camera_index = 0
        self.detection_params = self.config.get('game', {}).get('detection_params', {
            'param1': 50,
            'param2': 13,
            'minRadius': 65,
            'maxRadius': 80
        })
        self.hover_duration = 3.0
        self.color_scheme = 'dark'  # 'dark' or 'light'
        self.enable_debug = False
        
        # Setup UI
        self.setup_ui()
        
        log_info("Game wizard opened")
    
    def setup_ui(self):
        """Setup the wizard UI."""
        # Header
        header_frame = ttk.Frame(self.window)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(
            header_frame,
            text=get_text("game.title"),
            font=('Arial', 16, 'bold')
        ).pack(anchor=tk.W)
        
        ttk.Label(
            header_frame,
            text=get_text("game.description"),
            font=('Arial', 9),
            foreground='gray'
        ).pack(anchor=tk.W)
        
        # Main content with tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Tab 1: Basic Settings
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="Basic Settings")
        self.create_basic_settings(basic_frame)
        
        # Tab 2: Questions
        questions_frame = ttk.Frame(notebook)
        notebook.add(questions_frame, text="Questions")
        self.create_questions_settings(questions_frame)
        
        # Tab 3: Advanced Settings
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="Advanced")
        self.create_advanced_settings(advanced_frame)
        
        # Bottom buttons
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(
            button_frame,
            text=get_text("common.cancel"),
            command=self.cancel
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            button_frame,
            text=get_text("game.start_game"),
            command=self.start_game,
            style='Accent.TButton'
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Test Camera",
            command=self.test_camera
        ).pack(side=tk.RIGHT)
    
    def create_basic_settings(self, parent):
        """Create basic settings tab."""
        # Participant ID
        id_frame = ttk.LabelFrame(parent, text="Participant Information", padding=20)
        id_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(id_frame, text="Participant ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.participant_id_var = tk.StringVar(value="P001")
        ttk.Entry(id_frame, textvariable=self.participant_id_var, width=30).grid(row=0, column=1, sticky=tk.W, pady=5, padx=10)
        
        # Game Mode
        mode_frame = ttk.LabelFrame(parent, text="Game Mode", padding=20)
        mode_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.mode_var = tk.StringVar(value='tutorial')
        
        ttk.Radiobutton(
            mode_frame,
            text=get_text("game.tutorial_mode") + " (2 questions, not recorded)",
            variable=self.mode_var,
            value='tutorial'
        ).pack(anchor=tk.W, pady=5)
        
        ttk.Radiobutton(
            mode_frame,
            text=get_text("game.main_mode") + " (Full game, recorded)",
            variable=self.mode_var,
            value='main'
        ).pack(anchor=tk.W, pady=5)
        
        # Color Scheme
        color_frame = ttk.LabelFrame(parent, text="Visual Settings", padding=20)
        color_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(color_frame, text="Color Scheme:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.color_var = tk.StringVar(value='dark')
        color_combo = ttk.Combobox(
            color_frame,
            textvariable=self.color_var,
            values=['dark', 'light'],
            state='readonly',
            width=15
        )
        color_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=10)
        
        # Hover Duration
        ttk.Label(color_frame, text="Hover Duration (seconds):").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.hover_var = tk.DoubleVar(value=3.0)
        hover_scale = ttk.Scale(
            color_frame,
            from_=1.0,
            to=5.0,
            variable=self.hover_var,
            orient=tk.HORIZONTAL
        )
        hover_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=10)
        
        self.hover_label = ttk.Label(color_frame, text="3.0")
        self.hover_label.grid(row=1, column=2, sticky=tk.W, pady=5)
        
        def update_hover_label(val):
            self.hover_label.config(text=f"{float(val):.1f}")
        
        hover_scale.config(command=update_hover_label)
    
    def create_questions_settings(self, parent):
        """Create questions settings tab."""
        # Default vs Custom
        source_frame = ttk.LabelFrame(parent, text="Question Source", padding=20)
        source_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.question_source_var = tk.StringVar(value='default')
        
        ttk.Radiobutton(
            source_frame,
            text="Use Default Questions",
            variable=self.question_source_var,
            value='default',
            command=self.update_question_source
        ).pack(anchor=tk.W, pady=5)
        
        ttk.Radiobutton(
            source_frame,
            text="Load from Excel File",
            variable=self.question_source_var,
            value='excel',
            command=self.update_question_source
        ).pack(anchor=tk.W, pady=5)
        
        # Excel file selection
        self.excel_frame = ttk.Frame(source_frame)
        self.excel_frame.pack(fill=tk.X, pady=10)
        
        self.excel_path_var = tk.StringVar()
        ttk.Entry(
            self.excel_frame,
            textvariable=self.excel_path_var,
            state='readonly',
            width=50
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.browse_button = ttk.Button(
            self.excel_frame,
            text=get_text("wizard.browse"),
            command=self.browse_excel,
            state=tk.DISABLED
        )
        self.browse_button.pack(side=tk.LEFT)
        
        # Question preview
        preview_frame = ttk.LabelFrame(parent, text="Question Preview", padding=20)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.question_text = tk.Text(preview_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        self.question_text.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(
            preview_frame,
            text="Preview Questions",
            command=self.preview_questions
        ).pack(pady=10)
    
    def create_advanced_settings(self, parent):
        """Create advanced settings tab."""
        # Camera Settings
        camera_frame = ttk.LabelFrame(parent, text="Camera Settings", padding=20)
        camera_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(camera_frame, text="Virtual Camera Index:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.camera_index_var = tk.IntVar(value=0)
        ttk.Spinbox(
            camera_frame,
            from_=0,
            to=5,
            textvariable=self.camera_index_var,
            width=10
        ).grid(row=0, column=1, sticky=tk.W, pady=5, padx=10)
        
        # Detection Parameters
        detection_frame = ttk.LabelFrame(parent, text="Detection Parameters", padding=20)
        detection_frame.pack(fill=tk.X, padx=10, pady=10)
        
        params = [
            ('param1', 'Canny Threshold', 10, 100, 50),
            ('param2', 'Accumulator Threshold', 5, 30, 13),
            ('minRadius', 'Min Radius', 30, 100, 65),
            ('maxRadius', 'Max Radius', 50, 150, 80)
        ]
        
        self.param_vars = {}
        
        for i, (key, label, min_val, max_val, default) in enumerate(params):
            ttk.Label(detection_frame, text=f"{label}:").grid(row=i, column=0, sticky=tk.W, pady=5)
            
            var = tk.IntVar(value=self.detection_params.get(key, default))
            self.param_vars[key] = var
            
            scale = ttk.Scale(
                detection_frame,
                from_=min_val,
                to=max_val,
                variable=var,
                orient=tk.HORIZONTAL
            )
            scale.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=5, padx=10)
            
            value_label = ttk.Label(detection_frame, text=str(default))
            value_label.grid(row=i, column=2, sticky=tk.W, pady=5)
            
            def make_update(lbl, v):
                def update(val):
                    lbl.config(text=str(int(float(val))))
                return update
            
            scale.config(command=make_update(value_label, var))
        
        detection_frame.columnconfigure(1, weight=1)
        
        # Debug Mode
        debug_frame = ttk.LabelFrame(parent, text="Debug Options", padding=20)
        debug_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.debug_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            debug_frame,
            text=get_text("game.debug_mode") + " - Toggle with F12 during game",
            variable=self.debug_var
        ).pack(anchor=tk.W, pady=5)
        
        # Adaptive Learning
        self.adaptive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            debug_frame,
            text="Enable Adaptive Parameter Learning",
            variable=self.adaptive_var
        ).pack(anchor=tk.W, pady=5)
    
    def update_question_source(self):
        """Update question source UI based on selection."""
        if self.question_source_var.get() == 'excel':
            self.browse_button.config(state=tk.NORMAL)
        else:
            self.browse_button.config(state=tk.DISABLED)
    
    def browse_excel(self):
        """Browse for Excel file."""
        filename = filedialog.askopenfilename(
            parent=self.window,
            title="Select Questions Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if filename:
            self.excel_path_var.set(filename)
            self.custom_questions_file = filename
            log_info(f"Custom questions file selected: {filename}")
    
    def preview_questions(self):
        """Preview loaded questions."""
        self.question_text.config(state=tk.NORMAL)
        self.question_text.delete('1.0', tk.END)
        
        try:
            if self.question_source_var.get() == 'excel' and self.custom_questions_file:
                questions = load_questions_from_excel(self.custom_questions_file)
                mode = 'main'
            else:
                all_questions = get_default_questions()
                mode = self.mode_var.get()
                questions = all_questions.get(mode, [])
            
            if questions:
                self.question_text.insert('1.0', f"Questions for {mode.upper()} mode:\n\n")
                for i, q in enumerate(questions, 1):
                    self.question_text.insert(tk.END, f"{i}. {q['soal']}\n")
                    self.question_text.insert(tk.END, f"   Answer: {q['jawaban'].upper()}\n\n")
            else:
                self.question_text.insert('1.0', "No questions loaded.")
                
        except Exception as e:
            self.question_text.insert('1.0', f"Error loading questions: {str(e)}")
            log_error(f"Error previewing questions: {str(e)}")
        
        self.question_text.config(state=tk.DISABLED)
    
    def test_camera(self):
        """Test virtual camera connection."""
        camera_index = self.camera_index_var.get()
        
        test_window = tk.Toplevel(self.window)
        test_window.title("Camera Test")
        test_window.geometry("400x300")
        
        status_label = ttk.Label(test_window, text="Testing camera...", font=('Arial', 11))
        status_label.pack(pady=20)
        
        result_text = tk.Text(test_window, height=10, width=50)
        result_text.pack(padx=20, pady=10)
        
        def run_test():
            cap = init_virtual_camera(camera_index)
            
            if cap is None:
                result_text.insert(tk.END, f"✗ Failed to open camera at index {camera_index}\n\n")
                result_text.insert(tk.END, "Troubleshooting:\n")
                result_text.insert(tk.END, "1. Make sure OBS Virtual Camera is running\n")
                result_text.insert(tk.END, "2. Try different camera indices (0-5)\n")
                result_text.insert(tk.END, "3. Check OBS Studio settings\n")
                status_label.config(text="✗ Camera test failed", foreground='red')
                return
            
            # Test frame capture
            ret, frame = cap.read()
            if not ret:
                result_text.insert(tk.END, f"✗ Camera opened but failed to read frame\n")
                status_label.config(text="✗ Camera test failed", foreground='red')
                cap.release()
                return
            
            # Test detection
            result_text.insert(tk.END, f"✓ Camera opened successfully\n")
            result_text.insert(tk.END, f"  Resolution: {frame.shape[1]}x{frame.shape[0]}\n\n")
            
            params = {key: var.get() for key, var in self.param_vars.items()}
            detection = detect_gaze_hough(frame, params)
            
            if detection:
                result_text.insert(tk.END, f"✓ Gaze detection working\n")
                result_text.insert(tk.END, f"  Center: {detection['center']}\n")
                result_text.insert(tk.END, f"  Radius: {detection['radius']}\n")
            else:
                result_text.insert(tk.END, f"⚠ No gaze detected in current frame\n")
                result_text.insert(tk.END, f"  (This is normal if not looking at camera)\n")
            
            result_text.insert(tk.END, f"\n✓ Camera test completed successfully!\n")
            status_label.config(text="✓ Camera test passed", foreground='green')
            
            cap.release()
        
        thread = threading.Thread(target=run_test)
        thread.daemon = True
        thread.start()
    
    def start_game(self):
        """Start the game with current settings."""
        # Validate settings
        if self.question_source_var.get() == 'excel' and not self.custom_questions_file:
            messagebox.showwarning(
                get_text("common.warning"),
                "Please select an Excel file or use default questions."
            )
            return
        
        # Save current settings to config
        game_config = {
            'detection_params': {key: var.get() for key, var in self.param_vars.items()},
            'hover_duration': self.hover_var.get(),
            'color_scheme': self.color_var.get(),
            'camera_index': self.camera_index_var.get(),
            'enable_debug': self.debug_var.get(),
            'enable_adaptive': self.adaptive_var.get()
        }
        
        self.config['game'] = game_config
        save_config(self.config)
        
        log_info(f"Starting game: mode={self.mode_var.get()}, participant={self.participant_id_var.get()}")
        
        # Close wizard
        self.window.destroy()
        
        # Launch game in separate thread
        game_thread = threading.Thread(
            target=run_game_main_loop,
            args=(
                self.mode_var.get(),
                self.participant_id_var.get(),
                self.custom_questions_file,
                game_config
            )
        )
        game_thread.daemon = True
        game_thread.start()
    
    def cancel(self):
        """Cancel and close wizard."""
        if messagebox.askokcancel(
            get_text("common.warning"),
            get_text("wizard.confirm_cancel")
        ):
            self.window.destroy()
            log_info("Game wizard cancelled")


# ============================================================================
# GAME MAIN LOOP
# ============================================================================

def run_game_main_loop(
    mode: str,
    participant_id: str,
    custom_questions_file: Optional[str],
    game_config: Dict[str, Any]
):
    """
    Main game loop (runs in separate thread).
    
    Args:
        mode: 'tutorial' or 'main'
        participant_id: Participant identifier
        custom_questions_file: Path to Excel file or None
        game_config: Game configuration dictionary
    """
    try:
        log_info(f"Initializing game: mode={mode}, participant={participant_id}")
        
        # Initialize Pygame
        pygame.init()
        
        # Get screen info
        info = pygame.display.Info()
        screen_width = info.current_w
        screen_height = info.current_h
        
        # Create fullscreen window
        screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
        pygame.display.set_caption(get_text("game.title"))
        
        # Initialize camera
        camera_index = game_config.get('camera_index', 0)
        cap = init_virtual_camera(camera_index)
        
        if cap is None:
            log_error("Failed to initialize camera")
            messagebox.showerror("Error", "Failed to open virtual camera. Please check OBS Virtual Camera.")
            pygame.quit()
            return
        
        # Load questions
        if custom_questions_file:
            questions = load_questions_from_excel(custom_questions_file)
            if not questions:
                log_warning("Failed to load custom questions, using defaults")
                questions = get_default_questions()[mode]
        else:
            questions = get_default_questions()[mode]
        
        # Initialize game components
        kalman_filter = KalmanGazeFilter()
        detection_params = game_config.get('detection_params', {})
        hover_duration = game_config.get('hover_duration', 3.0)
        color_scheme = game_config.get('color_scheme', 'dark')
        enable_debug = game_config.get('enable_debug', False)
        
        # Color schemes
        if color_scheme == 'dark':
            colors = {
                "latar": (20, 20, 20),
                "teks_soal": (220, 220, 220),
                "teks_biasa": (255, 255, 255),
                "tombol": (50, 50, 50),
                "hover": (80, 80, 80),
                "outline": (150, 150, 150)
            }
        else:
            colors = {
                "latar": (235, 235, 235),
                "teks_soal": (10, 10, 10),
                "teks_biasa": (0, 0, 0),
                "tombol": (200, 200, 200),
                "hover": (170, 170, 170),
                "outline": (100, 100, 100)
            }
        
        # Create session directory (only for main mode)
        recorder = None
        if mode == 'main':
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            session_dir = os.path.join("Sessions", f"game_{participant_id}_{timestamp}")
            recorder = GameSessionRecorder(session_dir, participant_id)
        
        # Calculate layout
        layout = calculate_screen_layout((screen_width, screen_height), mode)
        
        # Create fonts
        font_large = pygame.font.Font(None, 60)
        font_medium = pygame.font.Font(None, 40)
        font_small = pygame.font.Font(None, 30)
        
        # Game state
        clock = pygame.time.Clock()
        running = True
        frame_count = 0
        show_debug = enable_debug
        
        # Game state
        current_question = -1  # -1 means start screen, >= 0 means question index
        score = 0
        game_state = "start"  # "start", "question", "feedback", "results", "exit"
        feedback_timer = 0
        feedback_message = ""
        feedback_correct = False
        
        # Create buttons using layout data
        start_btn_data = layout['start_button']
        start_button = GameButton(
            start_btn_data[0], start_btn_data[1], 
            start_btn_data[2], start_btn_data[3],
            get_text("game.button_start"),
            'start'
        )
        
        correct_btn_data = layout['correct_button']
        benar_button = GameButton(
            correct_btn_data[0], correct_btn_data[1],
            correct_btn_data[2], correct_btn_data[3],
            get_text("game.button_true"),
            'correct'
        )
        
        wrong_btn_data = layout['wrong_button']
        salah_button = GameButton(
            wrong_btn_data[0], wrong_btn_data[1],
            wrong_btn_data[2], wrong_btn_data[3],
            get_text("game.button_false"),
            'wrong'
        )
        
        exit_btn_data = layout['exit_button']
        exit_button = GameButton(
            exit_btn_data[0], exit_btn_data[1],
            exit_btn_data[2], exit_btn_data[3],
            get_text("game.button_exit"),
            'exit'
        )
        
        # Additional button for navigation (not in initial layout)
        next_button = GameButton(
            screen_width // 2 - 150, screen_height - 150,
            300, 100,
            get_text("game.button_next"),
            'start'
        )
        
        log_info("Game loop starting")
        
        # Main game loop
        while running:
            dt = clock.tick(60) / 1000.0  # Delta time in seconds
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_F12:
                        show_debug = not show_debug
                        log_info(f"Debug overlay: {'ON' if show_debug else 'OFF'}")
            
            # Read camera frame
            ret, frame = cap.read()
            if not ret:
                log_warning("Failed to read camera frame")
                continue
            
            # Detect gaze
            detection = detect_gaze_hough(frame, detection_params)
            gaze_pos = None
            roi = None
            raw_gaze = None
            
            if detection:
                raw_gaze = detection['center']
                gaze_pos = kalman_filter.update(raw_gaze)
                
                # Determine ROI based on game state
                if game_state == "question":
                    all_buttons = [benar_button, salah_button]
                elif game_state == "results":
                    all_buttons = [exit_button]
                else:  # start screen
                    all_buttons = [start_button]
                
                roi = get_roi_at_position(
                    gaze_pos,
                    layout['question_rect'],
                    all_buttons,
                    (screen_width, screen_height)
                )
                
                # Record gaze data for main mode
                if recorder and game_state == "question" and current_question >= 0:
                    recorder.record_gaze(
                        gaze_pos,
                        roi,
                        frame_count,
                        raw_gaze
                    )
            
            # Clear screen
            screen.fill(colors['latar'])
            
            # ============ STATE: START SCREEN ============
            if game_state == "start":
                # Title
                title_text = get_text("game.title_screen")
                title_surf = font_large.render(title_text, True, colors['teks_biasa'])
                title_rect = title_surf.get_rect(center=(screen_width // 2, screen_height // 4))
                screen.blit(title_surf, title_rect)
                
                # Instructions
                if mode == 'tutorial':
                    instr_text = get_text("game.tutorial_instructions")
                else:
                    instr_text = get_text("game.main_instructions")
                
                instr_surf = font_medium.render(instr_text, True, colors['teks_biasa'])
                instr_rect = instr_surf.get_rect(center=(screen_width // 2, screen_height // 2 - 50))
                screen.blit(instr_surf, instr_rect)
                
                # Draw start button
                start_button.draw(screen, colors, font_medium)
                
                # Update and check if start button activated
                start_button.update_hover(gaze_pos, hover_duration)
                if start_button.is_clicked(hover_duration):
                    log_info("Start button activated")
                    current_question = 0
                    game_state = "question"
                    recorder.start_question(current_question, questions[current_question]['question']) if recorder else None
                    start_button.reset_hover()
            
            # ============ STATE: QUESTION ============
            elif game_state == "question" and current_question < len(questions):
                q = questions[current_question]
                
                # Question text
                q_text = f"{get_text('game.question_label')} {current_question + 1}/{len(questions)}"
                q_surf = font_medium.render(q_text, True, colors['teks_soal'])
                q_rect = q_surf.get_rect(center=(screen_width // 2, layout['question_y']))
                screen.blit(q_surf, q_rect)
                
                # Question content
                question_surf = font_large.render(q['question'], True, colors['teks_soal'])
                question_rect = question_surf.get_rect(center=(screen_width // 2, screen_height // 2))
                screen.blit(question_surf, question_rect)
                
                # Score display
                score_text = f"{get_text('game.score_label')}: {score}"
                score_surf = font_small.render(score_text, True, colors['teks_biasa'])
                screen.blit(score_surf, (20, 20))
                
                # Draw answer buttons
                benar_button.draw(screen, colors, font_medium)
                salah_button.draw(screen, colors, font_medium)
                
                # Update button hover states
                benar_button.update_hover(gaze_pos, hover_duration)
                salah_button.update_hover(gaze_pos, hover_duration)
                
                # Check button activation
                if benar_button.is_clicked(hover_duration):
                    user_answer = True
                    correct_answer = q['answer']
                    is_correct = (user_answer == correct_answer)
                    
                    if is_correct:
                        score += 1
                        feedback_message = get_text("game.feedback_correct")
                        feedback_correct = True
                    else:
                        feedback_message = get_text("game.feedback_wrong")
                        feedback_correct = False
                    
                    # Calculate response time
                    if recorder and recorder.current_question_start_time:
                        response_time = time.time() - recorder.current_question_start_time
                        recorder.end_question('benar', is_correct, response_time)
                    
                    log_info(f"Question {current_question + 1}: User={user_answer}, Correct={correct_answer}, Result={is_correct}")
                    
                    game_state = "feedback"
                    feedback_timer = 2.0  # 2 seconds
                    benar_button.reset_hover()
                    salah_button.reset_hover()
                
                elif salah_button.is_clicked(hover_duration):
                    user_answer = False
                    correct_answer = q['answer']
                    is_correct = (user_answer == correct_answer)
                    
                    if is_correct:
                        score += 1
                        feedback_message = get_text("game.feedback_correct")
                        feedback_correct = True
                    else:
                        feedback_message = get_text("game.feedback_wrong")
                        feedback_correct = False
                    
                    # Calculate response time
                    if recorder and recorder.current_question_start_time:
                        response_time = time.time() - recorder.current_question_start_time
                        recorder.end_question('salah', is_correct, response_time)
                    
                    log_info(f"Question {current_question + 1}: User={user_answer}, Correct={correct_answer}, Result={is_correct}")
                    
                    game_state = "feedback"
                    feedback_timer = 2.0  # 2 seconds
                    benar_button.reset_hover()
                    salah_button.reset_hover()
            
            # ============ STATE: FEEDBACK ============
            elif game_state == "feedback":
                # Show feedback message
                if feedback_correct:
                    feedback_color = (50, 200, 50)  # Green
                else:
                    feedback_color = (200, 50, 50)  # Red
                
                feedback_surf = font_large.render(str(feedback_message), True, feedback_color)
                feedback_rect = feedback_surf.get_rect(center=(screen_width // 2, screen_height // 2))
                screen.blit(feedback_surf, feedback_rect)
                
                # Countdown timer
                feedback_timer -= dt
                if feedback_timer <= 0:
                    current_question += 1
                    if current_question >= len(questions):
                        game_state = "results"
                    else:
                        game_state = "question"
                        # Start recording next question
                        if recorder:
                            recorder.start_question(current_question, questions[current_question]['question'])
            
            # ============ STATE: RESULTS ============
            elif game_state == "results":
                # Title
                result_title = get_text("game.results_title")
                title_surf = font_large.render(str(result_title), True, colors['teks_biasa'])
                title_rect = title_surf.get_rect(center=(screen_width // 2, screen_height // 3))
                screen.blit(title_surf, title_rect)
                
                # Score
                score_text = f"{get_text('game.final_score')}: {score}/{len(questions)}"
                score_surf = font_medium.render(score_text, True, colors['teks_soal'])
                score_rect = score_surf.get_rect(center=(screen_width // 2, screen_height // 2))
                screen.blit(score_surf, score_rect)
                
                # Percentage
                percentage = (score / len(questions)) * 100
                percent_text = f"{percentage:.1f}%"
                percent_surf = font_medium.render(percent_text, True, colors['teks_soal'])
                percent_rect = percent_surf.get_rect(center=(screen_width // 2, screen_height // 2 + 60))
                screen.blit(percent_surf, percent_rect)
                
                # Exit button
                exit_button.draw(screen, colors, font_medium)
                
                # Update and check exit button
                exit_button.update_hover(gaze_pos, hover_duration)
                if exit_button.is_clicked(hover_duration):
                    log_info("Exit button activated")
                    running = False
            
            # Debug overlay
            if show_debug:
                debug_y = 10
                debug_texts = [
                    f"FPS: {int(clock.get_fps())}",
                    f"Frame: {frame_count}",
                    f"Question: {current_question + 1}/{len(questions)}" if current_question >= 0 else "Start Screen",
                    f"Gaze: {gaze_pos}" if gaze_pos else "No gaze",
                    f"Score: {score}"
                ]
                
                for text in debug_texts:
                    surf = font_small.render(text, True, (255, 255, 0))
                    screen.blit(surf, (10, debug_y))
                    debug_y += 35
            
            # Update display
            pygame.display.flip()
            clock.tick(60)
            frame_count += 1
        
        # Cleanup
        cap.release()
        pygame.quit()
        
        # Save session data
        if recorder:
            files_saved = recorder.save()
            log_info(f"Session data saved: {files_saved}")
        
        log_info("Game ended")
        
    except Exception as e:
        log_error(f"Error in game loop: {str(e)}")
        pygame.quit()
        messagebox.showerror("Error", f"Game error: {str(e)}")


# ============================================================================
# LAUNCHER FUNCTION
# ============================================================================

def launch_game_wizard(parent):
    """
    Launch the game configuration wizard.
    
    Args:
        parent: Parent Tkinter window
    """
    wizard = GameWizard(parent)
    return wizard


if __name__ == "__main__":
    # Test code
    root = tk.Tk()
    root.withdraw()
    launch_game_wizard(root)
    root.mainloop()
