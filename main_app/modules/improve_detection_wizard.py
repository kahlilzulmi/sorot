"""
Improve Detection Wizard Module
Wizard to help users enhance eye detection accuracy in videos iteratively using Bayesian optimization.
Uses stimulus videos as ground truth to automatically tune detection parameters.

Steps:
1. Video & Stimulus Selection - Choose recorded video and corresponding stimulus
2. Method Selection - Select detection method to optimize
3. Optimization Settings - Configure optimization parameters and mode
4. Processing & Optimization - Run iterative optimization with Bayesian search
5. Results - View improvements, compare iterations, and save optimal parameters

Author: Eye Tracker Research Project
Date: 17 November 2025
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import os
import json
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from PIL import Image, ImageTk
import numpy as np
from tqdm import tqdm

from utils.logger import log_info, log_warning, log_error
from utils.config_manager import load_config, save_config
from utils.localization import get_text
from modules.detection_algorithms import (
    process_frame_with_method,
    get_default_params
)

# Try to import librosa for audio alignment
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    log_warning("librosa not installed. Audio alignment not available.")

# Try to import scikit-optimize for Bayesian optimization
try:
    from skopt import gp_minimize
    from skopt.space import Real, Integer
    from skopt.utils import use_named_args
    SKOPT_AVAILABLE = True
except ImportError:
    SKOPT_AVAILABLE = False
    log_warning("scikit-optimize not installed. Using grid search fallback.")


# ============================================================================
# GROUND TRUTH EXTRACTOR
# ============================================================================

class StimulusGroundTruthExtractor:
    """Extract ground truth gaze positions from stimulus generation code."""
    
    @staticmethod
    def generate_default_positions() -> Dict[int, Optional[Tuple[int, int]]]:
        """
        Generate default ground truth positions based on genvidsim4 structure.
        This is much faster than loading the actual video file.
        
        Returns:
            Dictionary mapping frame_number -> (x, y) position or None
        """
        # Configuration matching genvidsim4.py
        WIDTH, HEIGHT = 1920, 1080
        FPS = 60
        MARGIN = 150
        
        DURASI_BUKA_TUTUP = 5
        DURASI_PERINTAH = 3
        DURASI_PERSIAPAN = 3
        DURASI_TUTORIAL = 8
        DURASI_FIKSASI = 5
        DURASI_GERAK_HALUS = 10
        DURASI_SAKADIK_PER_TITIK = 3
        
        ground_truth = {}
        frame_num = 0
        
        # Helper function to add frames
        def add_frames(duration, position_func, is_moving=False):
            nonlocal frame_num
            total_frames = int(duration * FPS)
            for i in range(total_frames):
                if is_moving:
                    pos = position_func(i, total_frames)
                else:
                    pos = position_func()
                ground_truth[frame_num] = pos
                frame_num += 1
        
        # 1. Opening (fullscreen text - no target)
        add_frames(DURASI_BUKA_TUTUP, lambda: None)
        
        # 2. Tutorial - Command
        add_frames(DURASI_PERINTAH, lambda: None)
        
        # 2. Tutorial - Preparation countdown at start position
        start_x = MARGIN
        add_frames(DURASI_PERSIAPAN, lambda: (start_x, HEIGHT // 2))
        
        # 2. Tutorial - Horizontal movement (left to right)
        def tutorial_pos(i, total):
            progress = i / total
            x = MARGIN + progress * (WIDTH - 2 * MARGIN)
            return (int(x), HEIGHT // 2)
        add_frames(DURASI_TUTORIAL, tutorial_pos, is_moving=True)
        
        # 3. Task 1: Fixation at center - Command
        add_frames(DURASI_PERINTAH, lambda: None)
        # Fixation
        center = (WIDTH // 2, HEIGHT // 2)
        add_frames(DURASI_FIKSASI, lambda: center)
        
        # 4. Task 2a: Horizontal L->R - Command
        add_frames(DURASI_PERINTAH, lambda: None)
        # Preparation
        add_frames(DURASI_PERSIAPAN, lambda: (MARGIN, HEIGHT // 2))
        # Movement
        def horizontal_lr(i, total):
            progress = i / total
            x = MARGIN + progress * (WIDTH - 2 * MARGIN)
            return (int(x), HEIGHT // 2)
        add_frames(DURASI_GERAK_HALUS, horizontal_lr, is_moving=True)
        
        # 5. Task 2b: Horizontal R->L - Command
        add_frames(DURASI_PERINTAH, lambda: None)
        # Preparation
        add_frames(DURASI_PERSIAPAN, lambda: (WIDTH - MARGIN, HEIGHT // 2))
        # Movement
        def horizontal_rl(i, total):
            progress = i / total
            x = (WIDTH - MARGIN) - progress * (WIDTH - 2 * MARGIN)
            return (int(x), HEIGHT // 2)
        add_frames(DURASI_GERAK_HALUS, horizontal_rl, is_moving=True)
        
        # 6. Task 3a: Vertical T->B - Command
        add_frames(DURASI_PERINTAH, lambda: None)
        # Preparation
        add_frames(DURASI_PERSIAPAN, lambda: (WIDTH // 2, MARGIN))
        # Movement
        def vertical_tb(i, total):
            progress = i / total
            y = MARGIN + progress * (HEIGHT - 2 * MARGIN)
            return (WIDTH // 2, int(y))
        add_frames(DURASI_GERAK_HALUS, vertical_tb, is_moving=True)
        
        # 7. Task 3b: Vertical B->T - Command
        add_frames(DURASI_PERINTAH, lambda: None)
        # Preparation
        add_frames(DURASI_PERSIAPAN, lambda: (WIDTH // 2, HEIGHT - MARGIN))
        # Movement
        def vertical_bt(i, total):
            progress = i / total
            y = (HEIGHT - MARGIN) - progress * (HEIGHT - 2 * MARGIN)
            return (WIDTH // 2, int(y))
        add_frames(DURASI_GERAK_HALUS, vertical_bt, is_moving=True)
        
        # 8. Task 4a: Circular clockwise - Command
        add_frames(DURASI_PERINTAH, lambda: None)
        # Preparation
        radius = (HEIGHT // 2) - MARGIN
        add_frames(DURASI_PERSIAPAN, lambda: (center[0] + radius, center[1]))
        # Movement (2 full circles)
        def circular_cw(i, total):
            progress = i / total
            angle = progress * 4 * np.pi  # 2 full circles
            x = center[0] + radius * np.cos(angle)
            y = center[1] + radius * np.sin(angle)
            return (int(x), int(y))
        add_frames(DURASI_GERAK_HALUS, circular_cw, is_moving=True)
        
        # 9. Task 4b: Circular counter-clockwise - Command
        add_frames(DURASI_PERINTAH, lambda: None)
        # Preparation
        add_frames(DURASI_PERSIAPAN, lambda: (center[0] + radius, center[1]))
        # Movement (reverse)
        def circular_ccw(i, total):
            progress = i / total
            angle = -progress * 4 * np.pi  # 2 full circles reversed
            x = center[0] + radius * np.cos(angle)
            y = center[1] + radius * np.sin(angle)
            return (int(x), int(y))
        add_frames(DURASI_GERAK_HALUS, circular_ccw, is_moving=True)
        
        # 10. Task 5a: Saccadic structured - Command
        add_frames(DURASI_PERINTAH, lambda: None)
        # Points
        margin_sacc = 200
        points_structured = [
            (margin_sacc, margin_sacc),
            (WIDTH - margin_sacc, margin_sacc),
            (WIDTH - margin_sacc, HEIGHT - margin_sacc),
            (margin_sacc, HEIGHT - margin_sacc),
            center
        ]
        for point in points_structured:
            add_frames(DURASI_SAKADIK_PER_TITIK, lambda p=point: p)
        
        # 11. Task 5b: Saccadic random - Command
        add_frames(DURASI_PERINTAH, lambda: None)
        # Points
        points_random = [
            (WIDTH - margin_sacc, margin_sacc),
            (margin_sacc, HEIGHT - margin_sacc),
            (WIDTH // 2, margin_sacc),
            (WIDTH - margin_sacc, HEIGHT // 2),
            center
        ]
        for point in points_random:
            add_frames(DURASI_SAKADIK_PER_TITIK, lambda p=point: p)
        
        # 12. Closing (fullscreen text - no target)
        add_frames(DURASI_BUKA_TUTUP, lambda: None)
        
        valid_positions = len([v for v in ground_truth.values() if v is not None])
        log_info(f"Generated {valid_positions} ground truth positions ({frame_num} total frames)")
        return ground_truth
    
    @staticmethod
    def extract_from_genvidsim4(video_path: str) -> Dict[int, Optional[Tuple[int, int]]]:
        """
        Legacy method: Extract positions from stimulus video file.
        Note: Use generate_default_positions() instead for better performance.
        
        Args:
            video_path: Path to stimulus video (not actually used)
            
        Returns:
            Dictionary mapping frame_number -> (x, y) position or None
        """
        log_info("Using default position generation (video file not needed)")
        return StimulusGroundTruthExtractor.generate_default_positions()


# ============================================================================
# OPTIMIZATION ENGINE
# ============================================================================

class DetectionOptimizer:
    """Bayesian optimization engine for detection parameters."""
    
    def __init__(self, method: str, video_path: str, ground_truth: Dict[int, Optional[Tuple[int, int]]], 
                 time_offset: float = 0.0):
        self.method = method
        self.video_path = video_path
        self.ground_truth = ground_truth
        self.time_offset = time_offset  # Time offset in seconds
        self.iteration_history = []
        self.best_params = None
        self.best_score = float('inf')
        self.stop_optimization = False
        
    def calculate_accuracy(self, params: Dict[str, Any]) -> float:
        """
        Calculate detection accuracy against ground truth.
        
        Args:
            params: Detection parameters to test
            
        Returns:
            Average Euclidean distance error (lower is better)
        """
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            log_error(f"Cannot open video: {self.video_path}")
            return 10000.0
        
        # Get video FPS to calculate frame offset
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_offset = int(self.time_offset * video_fps)  # Convert time offset to frame offset
        
        errors = []
        frame_num = 0
        
        # Get total frames for progress tracking
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        valid_frames = len([k for k, v in self.ground_truth.items() if v is not None])
        
        # Create progress bar
        pbar = tqdm(total=valid_frames, desc="Processing frames", leave=False, 
                   disable=False, ncols=80, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}')
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Apply frame offset for alignment
            gt_frame_num = frame_num - frame_offset
            
            # Skip frames without ground truth or with None position or out of range
            if gt_frame_num < 0 or gt_frame_num not in self.ground_truth or self.ground_truth[gt_frame_num] is None:
                frame_num += 1
                continue
            
            gt_x, gt_y = self.ground_truth[gt_frame_num]
            
            # Detect with current parameters
            result = process_frame_with_method(frame, self.method, params)
            
            # Handle both tuple formats: (detections, frame) or just detections
            if isinstance(result, tuple) and len(result) == 2:
                detections, _ = result
            else:
                detections = result
            
            if detections:
                # Use first detection - should be (x, y, radius)
                detection = detections[0]
                det_x = detection[0]
                det_y = detection[1]
                
                # Calculate Euclidean distance error
                error = float(np.sqrt((det_x - gt_x)**2 + (det_y - gt_y)**2))
                errors.append(error)
            else:
                # Penalize missing detections heavily
                errors.append(1000.0)
            
            frame_num += 1
            pbar.update(1)
            
            if self.stop_optimization:
                break
        
        pbar.close()
        cap.release()
        
        if not errors:
            return 10000.0
        
        avg_error = np.mean(errors)
        return avg_error
    
    def optimize_bayesian(
        self,
        n_iterations: int = 10,
        convergence_check: int = 3,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Run Bayesian optimization to find optimal parameters.
        
        Args:
            n_iterations: Number of optimization iterations
            convergence_check: Stop if no improvement for N iterations
            progress_callback: Callback function(iteration, total, params, score)
            
        Returns:
            Dictionary with optimization results
        """
        if not SKOPT_AVAILABLE:
            return self.optimize_grid_search(n_iterations, progress_callback)
        
        # Define parameter search space based on method
        if self.method == "hough":
            space = [
                Integer(1, 15, name='blur_kernel'),
                Integer(10, 100, name='param1'),
                Integer(10, 50, name='param2'),
                Integer(10, 50, name='min_radius'),
                Integer(50, 150, name='max_radius')
            ]
        elif self.method == "contour":
            space = [
                Integer(1, 15, name='blur_kernel'),
                Integer(50, 255, name='threshold'),
                Real(0.5, 1.0, name='min_circularity')
            ]
        elif self.method == "color":
            space = [
                Integer(1, 15, name='blur_kernel'),
                Integer(20, 100, name='h_min'),
                Integer(100, 180, name='h_max')
            ]
        elif self.method == "blob":
            space = [
                Integer(10, 100, name='min_threshold'),
                Integer(100, 255, name='max_threshold'),
                Integer(5, 50, name='min_area')
            ]
        else:  # combined
            space = [
                Integer(1, 15, name='blur_kernel'),
                Integer(10, 100, name='hough_param1'),
                Integer(50, 255, name='threshold')
            ]
        
        no_improvement_count = 0
        
        # Create progress bar for iterations
        iteration_pbar = tqdm(total=n_iterations, desc="Optimization", 
                             leave=True, ncols=100, 
                             bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]')
        
        @use_named_args(space)
        def objective(**params_dict):
            nonlocal no_improvement_count
            
            if self.stop_optimization:
                return self.best_score
            
            # Convert to appropriate parameter format
            params = self._convert_params(params_dict)
            
            # Calculate error
            error = self.calculate_accuracy(params)
            
            # Store iteration
            self.iteration_history.append({
                'params': params.copy(),
                'error': error,
                'iteration': len(self.iteration_history) + 1
            })
            
            # Update best
            improved = False
            if error < self.best_score:
                self.best_score = error
                self.best_params = params.copy()
                no_improvement_count = 0
                improved = True
            else:
                no_improvement_count += 1
            
            # Check convergence
            if no_improvement_count >= convergence_check:
                log_info(f"Convergence reached after {len(self.iteration_history)} iterations")
                self.stop_optimization = True
            
            # Callback
            if progress_callback:
                progress_callback(
                    len(self.iteration_history),
                    n_iterations,
                    params,
                    error,
                    improved
                )
            
            # Update progress bar
            iteration_pbar.update(1)
            iteration_pbar.set_postfix({'error': f'{error:.2f}px', 'best': f'{self.best_score:.2f}px'})
            
            log_info(f"Iteration {len(self.iteration_history)}: Error = {error:.2f}, Improved: {improved}")
            
            return error
        
        # Run optimization
        try:
            # Note: gp_minimize may complete with fewer calls if we stop early via convergence
            result = gp_minimize(
                objective,
                space,
                n_calls=n_iterations,
                random_state=42,
                verbose=False
            )
        except ValueError as e:
            # Handle early convergence (when we stop before n_calls)
            if "not enough values" in str(e) or "n_calls" in str(e):
                log_info(f"Optimization stopped early due to convergence")
            else:
                log_error(f"Optimization error: {str(e)}")
        except Exception as e:
            log_error(f"Optimization error: {str(e)}")
        finally:
            iteration_pbar.close()
        
        return {
            'best_params': self.best_params,
            'best_error': self.best_score,
            'history': self.iteration_history,
            'converged': self.stop_optimization
        }
    
    def optimize_grid_search(
        self,
        n_iterations: int = 10,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Fallback grid search optimization when scikit-optimize is unavailable."""
        # Generate parameter grid
        param_grid = self._generate_param_grid(n_iterations)
        
        for i, params in enumerate(param_grid):
            if self.stop_optimization:
                break
            
            error = self.calculate_accuracy(params)
            
            improved = False
            self.iteration_history.append({
                'params': params.copy(),
                'error': error,
                'iteration': i + 1
            })
            
            if error < self.best_score:
                self.best_score = error
                self.best_params = params.copy()
                improved = True
            
            if progress_callback:
                progress_callback(i + 1, len(param_grid), params, error, improved)
            
            log_info(f"Iteration {i + 1}: Error = {error:.2f}")
        
        return {
            'best_params': self.best_params,
            'best_error': self.best_score,
            'history': self.iteration_history,
            'converged': False
        }
    
    def _convert_params(self, params_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Convert optimization parameters to detection algorithm format."""
        converted = {}
        for key, value in params_dict.items():
            # Ensure integers are integers
            if 'kernel' in key or 'radius' in key or 'param' in key or 'threshold' in key or 'area' in key:
                if 'h_min' in key or 'h_max' in key:
                    converted[key] = int(value)
                else:
                    converted[key] = int(value) if not isinstance(value, int) else value
            else:
                converted[key] = value
        
        # Ensure odd kernel size
        if 'blur_kernel' in converted:
            if converted['blur_kernel'] % 2 == 0:
                converted['blur_kernel'] += 1
        
        return converted
    
    def _generate_param_grid(self, n_points: int) -> List[Dict[str, Any]]:
        """Generate parameter grid for grid search."""
        default_params = get_default_params(self.method)
        grid = [default_params]
        
        # Add variations
        for i in range(min(n_points - 1, 9)):
            params = default_params.copy()
            if 'blur_kernel' in params:
                params['blur_kernel'] = 3 + (i % 3) * 4
            if 'param1' in params:
                params['param1'] = 30 + (i % 3) * 20
            if 'param2' in params:
                params['param2'] = 15 + (i % 3) * 10
            grid.append(params)
        
        return grid


# ============================================================================
# LAUNCHER FUNCTION
# ============================================================================

def launch_improve_detection_wizard(parent):
    """Launch the Improve Detection Wizard."""
    
    class SimpleImproveWizard:
        """Simplified Improve Detection Wizard."""
        
        def __init__(self, parent):
            self.parent = parent
            self.window = tk.Toplevel(parent)
            self.window.title("Improve Detection Wizard")
            self.window.geometry("800x600")
            
            # Center window
            self.window.update_idletasks()
            x = (self.window.winfo_screenwidth() // 2) - 400
            y = (self.window.winfo_screenheight() // 2) - 300
            self.window.geometry(f'800x600+{x}+{y}')
            
            self.window.transient(parent)
            self.window.grab_set()
            
            # Data
            self.recorded_video = None
            self.stimulus_video = None
            self.method = "hough"
            self.mode = "automatic"
            self.max_iter = 10
            self.tolerance = 5.0
            self.convergence_check = 3
            self.time_offset = 0.0  # Time offset from alignment
            
            self.ground_truth = None
            self.optimizer = None
            self.results = None
            
            self.setup_ui()
        
        def setup_ui(self):
            # Header
            header = ttk.Frame(self.window)
            header.pack(fill=tk.X, padx=20, pady=10)
            
            ttk.Label(
                header,
                text="🪄 Improve Detection Wizard",
                font=('Arial', 14, 'bold')
            ).pack(anchor=tk.W)
            
            ttk.Label(
                header,
                text="Optimize detection parameters using stimulus ground truth",
                font=('Arial', 9),
                foreground="gray"
            ).pack(anchor=tk.W)
            
            # Content
            content = ttk.Frame(self.window)
            content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # Video Selection
            vid_frame = ttk.LabelFrame(content, text="1. Select Recorded Video & Align", padding=10)
            vid_frame.pack(fill=tk.X, pady=5)
            
            # Recorded video
            rec_frame = ttk.Frame(vid_frame)
            rec_frame.pack(fill=tk.X, pady=2)
            ttk.Label(rec_frame, text="Recorded Video:", width=20).pack(side=tk.LEFT)
            self.rec_var = tk.StringVar()
            ttk.Entry(rec_frame, textvariable=self.rec_var, state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            ttk.Button(rec_frame, text="Browse", command=self.browse_recorded, width=10).pack(side=tk.LEFT)
            
            # Stimulus video for alignment
            stim_frame = ttk.Frame(vid_frame)
            stim_frame.pack(fill=tk.X, pady=2)
            ttk.Label(stim_frame, text="Stimulus Video:", width=20).pack(side=tk.LEFT)
            self.stim_var = tk.StringVar()
            ttk.Entry(stim_frame, textvariable=self.stim_var, state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            ttk.Button(stim_frame, text="Browse", command=self.browse_stimulus, width=10).pack(side=tk.LEFT)
            
            # Alignment controls
            align_frame = ttk.Frame(vid_frame)
            align_frame.pack(fill=tk.X, pady=5)
            ttk.Button(align_frame, text="🔊 Auto-Align (Audio)", command=self.auto_align_audio, width=20).pack(side=tk.LEFT, padx=2)
            ttk.Button(align_frame, text="👁️ Manual Align", command=self.manual_align, width=20).pack(side=tk.LEFT, padx=2)
            self.offset_label = ttk.Label(align_frame, text="Offset: 0.00s", foreground="blue")
            self.offset_label.pack(side=tk.LEFT, padx=10)
            
            # Info label
            info_frame = ttk.Frame(vid_frame)
            info_frame.pack(fill=tk.X, pady=5)
            ttk.Label(
                info_frame,
                text="ℹ️ Align your recorded video with stimulus timing for accurate optimization. Ground truth uses default pattern.",
                font=('Arial', 8),
                foreground="gray",
                wraplength=700
            ).pack(anchor=tk.W)
            
            # Method Selection
            method_frame = ttk.LabelFrame(content, text="2. Select Method", padding=10)
            method_frame.pack(fill=tk.X, pady=5)
            
            self.method_var = tk.StringVar(value="hough")
            methods = [("hough", "Hough Circle"), ("contour", "Contour"), ("color", "Color"), ("blob", "Blob")]
            for i, (val, text) in enumerate(methods):
                ttk.Radiobutton(method_frame, text=text, variable=self.method_var, value=val).pack(side=tk.LEFT, padx=10)
            
            # Settings
            settings_frame = ttk.LabelFrame(content, text="3. Optimization Settings", padding=10)
            settings_frame.pack(fill=tk.X, pady=5)
            
            # Mode
            mode_f = ttk.Frame(settings_frame)
            mode_f.pack(fill=tk.X, pady=2)
            ttk.Label(mode_f, text="Mode:", width=20).pack(side=tk.LEFT)
            self.mode_var = tk.StringVar(value="automatic")
            ttk.Radiobutton(mode_f, text="🚀 Quick (Auto)", variable=self.mode_var, value="automatic").pack(side=tk.LEFT, padx=5)
            ttk.Radiobutton(mode_f, text="👁️ Manual Review", variable=self.mode_var, value="manual").pack(side=tk.LEFT, padx=5)
            
            # Iterations
            iter_f = ttk.Frame(settings_frame)
            iter_f.pack(fill=tk.X, pady=2)
            ttk.Label(iter_f, text="Max Iterations:", width=20).pack(side=tk.LEFT)
            self.iter_var = tk.IntVar(value=10)
            ttk.Spinbox(iter_f, from_=3, to=50, textvariable=self.iter_var, width=10).pack(side=tk.LEFT, padx=5)
            
            # Tolerance
            tol_f = ttk.Frame(settings_frame)
            tol_f.pack(fill=tk.X, pady=2)
            ttk.Label(tol_f, text="Error Tolerance (%):", width=20).pack(side=tk.LEFT)
            self.tol_var = tk.DoubleVar(value=5.0)
            ttk.Spinbox(tol_f, from_=1.0, to=20.0, textvariable=self.tol_var, width=10, increment=0.5).pack(side=tk.LEFT, padx=5)
            
            # Results area
            results_frame = ttk.LabelFrame(content, text="4. Optimization Results", padding=10)
            results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            
            scroll = ttk.Scrollbar(results_frame)
            scroll.pack(side=tk.RIGHT, fill=tk.Y)
            
            self.log_text = tk.Text(results_frame, height=10, font=('Consolas', 9), yscrollcommand=scroll.set)
            self.log_text.pack(fill=tk.BOTH, expand=True)
            scroll.config(command=self.log_text.yview)
            
            # Buttons
            btn_frame = ttk.Frame(self.window)
            btn_frame.pack(fill=tk.X, padx=20, pady=10)
            
            ttk.Button(btn_frame, text="▶ Start Optimization", command=self.start_optimization).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="📊 View Results", command=self.show_results, state=tk.DISABLED).pack(side=tk.LEFT, padx=5)
            self.results_btn = btn_frame.winfo_children()[1]
            ttk.Button(btn_frame, text="Close", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
        
        def browse_recorded(self):
            filename = filedialog.askopenfilename(
                parent=self.window,
                title="Select Recorded Video",
                filetypes=[("Video Files", "*.mp4 *.avi *.mkv"), ("All Files", "*.*")]
            )
            if filename:
                self.recorded_video = filename
                self.rec_var.set(os.path.basename(filename))
        
        def browse_stimulus(self):
            filename = filedialog.askopenfilename(
                parent=self.window,
                title="Select Stimulus Video (for alignment)",
                filetypes=[("Video Files", "*.mp4 *.avi *.mkv"), ("All Files", "*.*")]
            )
            if filename:
                self.stimulus_video = filename
                self.stim_var.set(os.path.basename(filename))
        
        def auto_align_audio(self):
            """Automatically align videos using audio sync."""
            if not self.recorded_video or not self.stimulus_video:
                messagebox.showerror("Error", "Please select both recorded and stimulus videos first")
                return
            
            if not LIBROSA_AVAILABLE:
                messagebox.showerror("Error", "librosa library not installed.\nPlease install: pip install librosa soundfile")
                return
            
            self.log("🔊 Auto-aligning using audio...")
            
            def align_thread():
                try:
                    # Load audio from both videos
                    self.log("Loading audio from recorded video...")
                    y1, sr1 = librosa.load(self.recorded_video, duration=10.0)
                    
                    self.log("Loading audio from stimulus video...")
                    y2, sr2 = librosa.load(self.stimulus_video, duration=10.0)
                    
                    # Find onset frames (first significant audio event)
                    self.log("Detecting audio onsets...")
                    onset_frames1 = librosa.onset.onset_detect(y=y1, sr=sr1, units='frames')
                    onset_frames2 = librosa.onset.onset_detect(y=y2, sr=sr2, units='frames')
                    
                    if len(onset_frames1) > 0 and len(onset_frames2) > 0:
                        # Convert to time
                        time1 = librosa.frames_to_time(onset_frames1[0], sr=sr1)
                        time2 = librosa.frames_to_time(onset_frames2[0], sr=sr2)
                        
                        # Calculate offset (recorded - stimulus)
                        self.time_offset = time1 - time2
                        
                        self.window.after(0, lambda: self.offset_label.config(
                            text=f"Offset: {self.time_offset:.2f}s",
                            foreground="green"
                        ))
                        self.log(f"✓ Audio sync successful! Offset: {self.time_offset:.2f}s")
                        self.log(f"  Recorded onset at: {time1:.2f}s")
                        self.log(f"  Stimulus onset at: {time2:.2f}s")
                    else:
                        self.log("❌ Could not detect audio onsets in one or both videos")
                        self.window.after(0, lambda: messagebox.showwarning(
                            "Alignment Failed",
                            "Could not detect audio sync points.\nTry manual alignment instead."
                        ))
                        
                except Exception as e:
                    self.log(f"❌ Error during alignment: {str(e)}")
                    log_error(f"Auto-align error: {str(e)}")
                    self.window.after(0, lambda: messagebox.showerror(
                        "Error",
                        f"Audio alignment failed:\n{str(e)}"
                    ))
            
            thread = threading.Thread(target=align_thread, daemon=True)
            thread.start()
        
        def manual_align(self):
            """Open manual alignment dialog."""
            if not self.recorded_video or not self.stimulus_video:
                messagebox.showerror("Error", "Please select both recorded and stimulus videos first")
                return
            
            # Create manual alignment window
            align_win = tk.Toplevel(self.window)
            align_win.title("Manual Video Alignment")
            align_win.geometry("600x200")
            
            ttk.Label(align_win, text="Manual Alignment", font=('Arial', 12, 'bold')).pack(pady=10)
            
            # Offset controls
            offset_frame = ttk.Frame(align_win)
            offset_frame.pack(pady=20)
            
            ttk.Label(offset_frame, text="Time Offset (seconds):").pack(side=tk.LEFT, padx=5)
            
            offset_var = tk.DoubleVar(value=self.time_offset)
            offset_spinbox = ttk.Spinbox(offset_frame, from_=-60.0, to=60.0, 
                                        textvariable=offset_var, width=10, increment=0.1)
            offset_spinbox.pack(side=tk.LEFT, padx=5)
            
            info_text = """
Adjust the time offset to align the recorded video with the stimulus.
Positive values: Recorded video starts later (delay stimulus)
Negative values: Recorded video starts earlier (advance stimulus)
"""
            ttk.Label(align_win, text=info_text, font=('Arial', 8), justify=tk.LEFT).pack(pady=10)
            
            # Buttons
            btn_frame = ttk.Frame(align_win)
            btn_frame.pack(pady=10)
            
            def apply_offset():
                self.time_offset = offset_var.get()
                self.offset_label.config(
                    text=f"Offset: {self.time_offset:.2f}s",
                    foreground="green"
                )
                self.log(f"✓ Manual offset applied: {self.time_offset:.2f}s")
                align_win.destroy()
            
            ttk.Button(btn_frame, text="Apply", command=apply_offset).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Cancel", command=align_win.destroy).pack(side=tk.LEFT, padx=5)
        
        def log(self, msg):
            """Thread-safe logging to GUI text widget."""
            def _log():
                self.log_text.insert(tk.END, msg + "\n")
                self.log_text.see(tk.END)
            # Schedule GUI update in main thread
            self.window.after(0, _log)
        
        def start_optimization(self):
            if not self.recorded_video:
                messagebox.showerror("Error", "Please select a recorded video")
                return
            
            self.method = self.method_var.get()
            self.mode = self.mode_var.get()
            self.max_iter = self.iter_var.get()
            self.tolerance = self.tol_var.get()
            
            def optimize_thread():
                try:
                    self.log("=" * 60)
                    self.log("Starting optimization...")
                    self.log(f"Method: {self.method.upper()}")
                    self.log(f"Mode: {self.mode}")
                    self.log(f"Max iterations: {self.max_iter}")
                    self.log("=" * 60)
                    
                    # Generate ground truth
                    self.log("Generating ground truth positions from default stimulus pattern...")
                    self.ground_truth = StimulusGroundTruthExtractor.generate_default_positions()
                    valid_gt = len([v for v in self.ground_truth.values() if v is not None])
                    self.log(f"✓ Generated {valid_gt} ground truth positions")
                    
                    # Create optimizer
                    self.log("\\nInitializing optimizer...")
                    if self.time_offset != 0:
                        self.log(f"Using time offset: {self.time_offset:.2f}s")
                    self.optimizer = DetectionOptimizer(self.method, self.recorded_video, 
                                                       self.ground_truth, self.time_offset)
                    
                    # Run optimization
                    self.log("\\nRunning Bayesian optimization...")
                    self.results = self.optimizer.optimize_bayesian(
                        n_iterations=self.max_iter,
                        convergence_check=self.convergence_check,
                        progress_callback=self.progress_callback
                    )
                    
                    self.log("\\n" + "=" * 60)
                    self.log("✓ Optimization complete!")
                    self.log(f"Best error: {self.results['best_error']:.2f} pixels")
                    self.log(f"Total iterations: {len(self.results['history'])}")
                    self.log("=" * 60)
                    
                    # Enable results button
                    self.window.after(0, lambda: self.results_btn.config(state=tk.NORMAL))
                    
                except Exception as e:
                    self.log(f"\\nERROR: {str(e)}")
                    log_error(f"Optimization error: {str(e)}")
            
            thread = threading.Thread(target=optimize_thread, daemon=True)
            thread.start()
        
        def progress_callback(self, iteration, total, params, error, improved):
            marker = "✓" if improved else "•"
            self.log(f"{marker} Iter {iteration}/{total}: Error={error:.2f}px")
        
        def show_results(self):
            if not self.results:
                return
            
            # Create results window
            result_win = tk.Toplevel(self.window)
            result_win.title("Optimization Results")
            result_win.geometry("700x500")
            
            # Summary
            summary_frame = ttk.LabelFrame(result_win, text="Summary", padding=10)
            summary_frame.pack(fill=tk.X, padx=10, pady=5)
            
            history = self.results['history']
            initial_error = history[0]['error']
            best_error = self.results['best_error']
            improvement = ((initial_error - best_error) / initial_error) * 100
            converged_text = 'Yes' if self.results.get('converged') else 'No'
            
            summary_text = f"""
Method: {self.method.upper()}
Total Iterations: {len(history)}
Initial Error: {initial_error:.2f} pixels
Best Error: {best_error:.2f} pixels
Improvement: {improvement:.1f}%
Converged: {converged_text}
"""
            ttk.Label(summary_frame, text=summary_text, justify=tk.LEFT).pack()
            
            # Best parameters
            params_frame = ttk.LabelFrame(result_win, text="Optimal Parameters", padding=10)
            params_frame.pack(fill=tk.X, padx=10, pady=5)
            
            params_text = "\\n".join([f"{k}: {v}" for k, v in self.results['best_params'].items()])
            ttk.Label(params_frame, text=params_text, font=('Consolas', 9), justify=tk.LEFT).pack()
            
            # Buttons
            btn_frame = ttk.Frame(result_win)
            btn_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Button(btn_frame, text="💾 Save Parameters", command=self.save_params).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="📄 Export Report", command=self.export_report).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Close", command=result_win.destroy).pack(side=tk.RIGHT, padx=5)
        
        def save_params(self):
            if not self.results:
                return
            
            filename = filedialog.asksaveasfilename(
                parent=self.window,
                title="Save Optimal Parameters",
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
            )
            
            if filename:
                data = {
                    'method': self.method,
                    'optimal_parameters': self.results['best_params'],
                    'error': self.results['best_error'],
                    'timestamp': datetime.now().isoformat(),
                    'iterations': len(self.results['history'])
                }
                
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                
                messagebox.showinfo("Success", f"Parameters saved to:\\n{filename}")
        
        def export_report(self):
            if not self.results:
                return
            
            filename = filedialog.asksaveasfilename(
                parent=self.window,
                title="Export Report",
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w') as f:
                    f.write("=" * 70 + "\\n")
                    f.write("DETECTION OPTIMIZATION REPORT\\n")
                    f.write("=" * 70 + "\\n\\n")
                    
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
                    
                    f.write("OPTIMIZATION SETTINGS\\n")
                    f.write("-" * 70 + "\\n")
                    f.write(f"Method: {self.method.upper()}\\n")
                    f.write(f"Mode: {self.mode}\\n")
                    f.write(f"Max Iterations: {self.max_iter}\\n")
                    f.write(f"Tolerance: {self.tolerance}%\\n\\n")
                    
                    f.write("RESULTS\\n")
                    f.write("-" * 70 + "\\n")
                    history = self.results['history']
                    f.write(f"Total Iterations: {len(history)}\\n")
                    f.write(f"Initial Error: {history[0]['error']:.2f} pixels\\n")
                    f.write(f"Final Error: {self.results['best_error']:.2f} pixels\\n")
                    improvement = ((history[0]['error'] - self.results['best_error']) / history[0]['error']) * 100
                    f.write(f"Improvement: {improvement:.1f}%\\n\\n")
                    
                    f.write("OPTIMAL PARAMETERS\\n")
                    f.write("-" * 70 + "\\n")
                    for key, value in self.results['best_params'].items():
                        f.write(f"  {key}: {value}\\n")
                    f.write("\\n")
                    
                    f.write("ITERATION HISTORY\\n")
                    f.write("-" * 70 + "\\n")
                    f.write(f"{'Iter':<6} {'Error':<10}\\n")
                    f.write("-" * 70 + "\\n")
                    for h in history:
                        f.write(f"{h['iteration']:<6} {h['error']:<10.2f}\\n")
                
                messagebox.showinfo("Success", f"Report exported to:\\n{filename}")
    
    # Launch the wizard
    wizard = SimpleImproveWizard(parent)
    log_info("Improve Detection Wizard launched")


if __name__ == "__main__":
    # Test code
    root = tk.Tk()
    root.withdraw()
    launch_improve_detection_wizard(root)
    root.mainloop()

