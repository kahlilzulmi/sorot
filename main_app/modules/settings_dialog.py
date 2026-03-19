"""
Settings Dialog Module

Comprehensive settings interface with tabbed dialog for managing
all application configurations including UI preferences, detection
parameters, game settings, stimulus settings, file paths, and
advanced options.

Author: Kahlil Gibran Al Zulmi
NRP: 5049221015
Medical Technology Study Program - ITS
"""

import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
from typing import Dict, Any, Callable
import logging

from utils.config_manager import load_config, save_config, reset_to_defaults, get_default_config
from utils.localization import get_text


logger = logging.getLogger(__name__)


class SettingsDialog:
    """
    Multi-tab settings dialog for comprehensive application configuration.
    
    Features:
    - UI Preferences: Language, theme, fonts, colors
    - Detection Parameters: Method-specific parameters, Kalman filter settings
    - Game Settings: Timing, difficulty, camera settings
    - Stimulus Settings: Protocols, task parameters, video quality
    - File Paths: Configurable output directories
    - Advanced Options: Logging, performance, OBS integration
    """
    
    def __init__(self, parent: tk.Tk, config_path: str = "config.json", 
                 callback: Callable = None):
        """
        Initialize settings dialog.
        
        Args:
            parent: Parent window
            config_path: Path to configuration file
            callback: Optional callback function to call after saving settings
        """
        self.parent = parent
        self.config_path = config_path
        self.callback = callback
        
        # Load current configuration
        self.config = load_config(config_path)
        self.original_config = json.loads(json.dumps(self.config))  # Deep copy
        
        # Track modified state
        self.modified = False
        
        # Create dialog window
        self.dialog = None
        self.notebook = None
        
        # Store widget references for easy access
        self.widgets = {}
        
    def launch(self):
        """Launch the settings dialog."""
        try:
            # Create modal dialog
            self.dialog = tk.Toplevel(self.parent)
            self.dialog.title(get_text("settings", "dialog_title"))
            self.dialog.transient(self.parent)
            self.dialog.grab_set()
            
            # Set size and center
            dialog_width = 900
            dialog_height = 700
            screen_width = self.dialog.winfo_screenwidth()
            screen_height = self.dialog.winfo_screenheight()
            x = (screen_width - dialog_width) // 2
            y = (screen_height - dialog_height) // 2
            self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
            
            # Configure dialog close behavior
            self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
            
            # Create main container
            main_frame = ttk.Frame(self.dialog, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Create notebook (tabbed interface)
            self.notebook = ttk.Notebook(main_frame)
            self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            # Create tabs
            self._create_ui_tab()
            self._create_detection_tab()
            self._create_game_tab()
            self._create_stimulus_tab()
            self._create_paths_tab()
            self._create_advanced_tab()
            
            # Create button frame
            self._create_button_frame(main_frame)
            
            logger.info("Settings dialog launched")
            
        except Exception as e:
            logger.error(f"Error launching settings dialog: {e}")
            messagebox.showerror(
                get_text("common", "error"),
                f"Failed to launch settings: {str(e)}"
            )
    
    def _create_ui_tab(self):
        """Create UI preferences tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=get_text("settings", "tab_ui"))
        
        # Create scrollable frame
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Language settings
        lang_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "language"), padding=10)
        lang_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(lang_frame, text=get_text("settings", "select_language")).pack(anchor=tk.W)
        lang_var = tk.StringVar(value=self.config.get("language", "en"))
        self.widgets["language"] = lang_var
        
        lang_frame_inner = ttk.Frame(lang_frame)
        lang_frame_inner.pack(fill=tk.X, pady=5)
        ttk.Radiobutton(lang_frame_inner, text="English", variable=lang_var, 
                       value="en", command=self._mark_modified).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(lang_frame_inner, text="Bahasa Indonesia", variable=lang_var, 
                       value="id", command=self._mark_modified).pack(side=tk.LEFT, padx=5)
        
        # Theme settings
        theme_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "theme"), padding=10)
        theme_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(theme_frame, text=get_text("settings", "select_theme")).pack(anchor=tk.W)
        theme_var = tk.StringVar(value=self.config.get("ui", {}).get("theme", "light"))
        self.widgets["ui.theme"] = theme_var
        
        theme_frame_inner = ttk.Frame(theme_frame)
        theme_frame_inner.pack(fill=tk.X, pady=5)
        ttk.Radiobutton(theme_frame_inner, text=get_text("settings", "theme_light"), 
                       variable=theme_var, value="light", command=self._mark_modified).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(theme_frame_inner, text=get_text("settings", "theme_dark"), 
                       variable=theme_var, value="dark", command=self._mark_modified).pack(side=tk.LEFT, padx=5)
        
        # Window size settings
        window_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "window_size"), padding=10)
        window_frame.pack(fill=tk.X, padx=10, pady=5)
        
        width_frame = ttk.Frame(window_frame)
        width_frame.pack(fill=tk.X, pady=2)
        ttk.Label(width_frame, text=get_text("settings", "width")).pack(side=tk.LEFT)
        width_var = tk.IntVar(value=self.config.get("ui", {}).get("window_width", 1024))
        self.widgets["ui.window_width"] = width_var
        width_spin = ttk.Spinbox(width_frame, from_=800, to=2560, textvariable=width_var,
                                width=10, command=self._mark_modified)
        width_spin.pack(side=tk.RIGHT)
        
        height_frame = ttk.Frame(window_frame)
        height_frame.pack(fill=tk.X, pady=2)
        ttk.Label(height_frame, text=get_text("settings", "height")).pack(side=tk.LEFT)
        height_var = tk.IntVar(value=self.config.get("ui", {}).get("window_height", 768))
        self.widgets["ui.window_height"] = height_var
        height_spin = ttk.Spinbox(height_frame, from_=600, to=1440, textvariable=height_var,
                                 width=10, command=self._mark_modified)
        height_spin.pack(side=tk.RIGHT)
        
        # Font settings
        font_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "fonts"), padding=10)
        font_frame.pack(fill=tk.X, padx=10, pady=5)
        
        family_frame = ttk.Frame(font_frame)
        family_frame.pack(fill=tk.X, pady=2)
        ttk.Label(family_frame, text=get_text("settings", "font_family")).pack(side=tk.LEFT)
        family_var = tk.StringVar(value=self.config.get("ui", {}).get("font_family", "Arial"))
        self.widgets["ui.font_family"] = family_var
        family_combo = ttk.Combobox(family_frame, textvariable=family_var, 
                                   values=["Arial", "Calibri", "Segoe UI", "Tahoma", "Verdana"],
                                   width=15, state="readonly")
        family_combo.bind("<<ComboboxSelected>>", lambda e: self._mark_modified())
        family_combo.pack(side=tk.RIGHT)
        
        size_frame = ttk.Frame(font_frame)
        size_frame.pack(fill=tk.X, pady=2)
        ttk.Label(size_frame, text=get_text("settings", "font_size")).pack(side=tk.LEFT)
        size_var = tk.IntVar(value=self.config.get("ui", {}).get("font_size", 12))
        self.widgets["ui.font_size"] = size_var
        size_spin = ttk.Spinbox(size_frame, from_=8, to=24, textvariable=size_var,
                               width=10, command=self._mark_modified)
        size_spin.pack(side=tk.RIGHT)
    
    def _create_detection_tab(self):
        """Create detection parameters tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=get_text("settings", "tab_detection"))
        
        # Create scrollable frame
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Default method
        method_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "default_method"), padding=10)
        method_frame.pack(fill=tk.X, padx=10, pady=5)
        
        method_var = tk.StringVar(value=self.config.get("detection", {}).get("default_method", "hough"))
        self.widgets["detection.default_method"] = method_var
        
        methods = [
            ("hough", "Circular Hough Transform (CHT)"),
            ("blob", "Blob Detection"),
            ("contour", "Contour Analysis"),
            ("threshold", "Threshold-based"),
            ("dlib", "Dlib Facial Landmarks")
        ]
        
        for value, text in methods:
            ttk.Radiobutton(method_frame, text=text, variable=method_var, 
                          value=value, command=self._mark_modified).pack(anchor=tk.W, pady=2)
        
        # Processing settings
        proc_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "processing"), padding=10)
        proc_frame.pack(fill=tk.X, padx=10, pady=5)
        
        mode_frame = ttk.Frame(proc_frame)
        mode_frame.pack(fill=tk.X, pady=2)
        ttk.Label(mode_frame, text=get_text("settings", "processing_mode")).pack(side=tk.LEFT)
        mode_var = tk.StringVar(value=self.config.get("detection", {}).get("processing_mode", "auto"))
        self.widgets["detection.processing_mode"] = mode_var
        mode_combo = ttk.Combobox(mode_frame, textvariable=mode_var,
                                 values=["auto", "chunk", "full"],
                                 width=15, state="readonly")
        mode_combo.bind("<<ComboboxSelected>>", lambda e: self._mark_modified())
        mode_combo.pack(side=tk.RIGHT)
        
        chunk_frame = ttk.Frame(proc_frame)
        chunk_frame.pack(fill=tk.X, pady=2)
        ttk.Label(chunk_frame, text=get_text("settings", "chunk_size")).pack(side=tk.LEFT)
        chunk_var = tk.IntVar(value=self.config.get("detection", {}).get("chunk_size_frames", 1000))
        self.widgets["detection.chunk_size_frames"] = chunk_var
        chunk_spin = ttk.Spinbox(chunk_frame, from_=100, to=10000, increment=100,
                                textvariable=chunk_var, width=10, command=self._mark_modified)
        chunk_spin.pack(side=tk.RIGHT)
        
        # Kalman filter settings
        kalman_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "kalman_filter"), padding=10)
        kalman_frame.pack(fill=tk.X, padx=10, pady=5)
        
        process_frame = ttk.Frame(kalman_frame)
        process_frame.pack(fill=tk.X, pady=2)
        ttk.Label(process_frame, text=get_text("settings", "process_noise")).pack(side=tk.LEFT)
        process_var = tk.DoubleVar(value=self.config.get("detection", {}).get("kalman_process_noise", 0.1))
        self.widgets["detection.kalman_process_noise"] = process_var
        process_spin = ttk.Spinbox(process_frame, from_=0.01, to=1.0, increment=0.01,
                                  textvariable=process_var, width=10, command=self._mark_modified)
        process_spin.pack(side=tk.RIGHT)
        
        measure_frame = ttk.Frame(kalman_frame)
        measure_frame.pack(fill=tk.X, pady=2)
        ttk.Label(measure_frame, text=get_text("settings", "measurement_noise")).pack(side=tk.LEFT)
        measure_var = tk.DoubleVar(value=self.config.get("detection", {}).get("kalman_measurement_noise", 2.0))
        self.widgets["detection.kalman_measurement_noise"] = measure_var
        measure_spin = ttk.Spinbox(measure_frame, from_=0.1, to=10.0, increment=0.1,
                                  textvariable=measure_var, width=10, command=self._mark_modified)
        measure_spin.pack(side=tk.RIGHT)
        
        # Hough parameters
        hough_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "hough_params"), padding=10)
        hough_frame.pack(fill=tk.X, padx=10, pady=5)
        
        param1_frame = ttk.Frame(hough_frame)
        param1_frame.pack(fill=tk.X, pady=2)
        ttk.Label(param1_frame, text=get_text("settings", "param1")).pack(side=tk.LEFT)
        param1_var = tk.IntVar(value=self.config.get("detection", {}).get("hough_param1", 50))
        self.widgets["detection.hough_param1"] = param1_var
        ttk.Spinbox(param1_frame, from_=10, to=200, textvariable=param1_var,
                   width=10, command=self._mark_modified).pack(side=tk.RIGHT)
        
        param2_frame = ttk.Frame(hough_frame)
        param2_frame.pack(fill=tk.X, pady=2)
        ttk.Label(param2_frame, text=get_text("settings", "param2")).pack(side=tk.LEFT)
        param2_var = tk.IntVar(value=self.config.get("detection", {}).get("hough_param2", 13))
        self.widgets["detection.hough_param2"] = param2_var
        ttk.Spinbox(param2_frame, from_=5, to=100, textvariable=param2_var,
                   width=10, command=self._mark_modified).pack(side=tk.RIGHT)
        
        min_rad_frame = ttk.Frame(hough_frame)
        min_rad_frame.pack(fill=tk.X, pady=2)
        ttk.Label(min_rad_frame, text=get_text("settings", "min_radius")).pack(side=tk.LEFT)
        min_rad_var = tk.IntVar(value=self.config.get("detection", {}).get("hough_min_radius", 73))
        self.widgets["detection.hough_min_radius"] = min_rad_var
        ttk.Spinbox(min_rad_frame, from_=10, to=200, textvariable=min_rad_var,
                   width=10, command=self._mark_modified).pack(side=tk.RIGHT)
        
        max_rad_frame = ttk.Frame(hough_frame)
        max_rad_frame.pack(fill=tk.X, pady=2)
        ttk.Label(max_rad_frame, text=get_text("settings", "max_radius")).pack(side=tk.LEFT)
        max_rad_var = tk.IntVar(value=self.config.get("detection", {}).get("hough_max_radius", 75))
        self.widgets["detection.hough_max_radius"] = max_rad_var
        ttk.Spinbox(max_rad_frame, from_=10, to=200, textvariable=max_rad_var,
                   width=10, command=self._mark_modified).pack(side=tk.RIGHT)
        
        # Blob parameters
        blob_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "blob_params"), padding=10)
        blob_frame.pack(fill=tk.X, padx=10, pady=5)
        
        min_area_frame = ttk.Frame(blob_frame)
        min_area_frame.pack(fill=tk.X, pady=2)
        ttk.Label(min_area_frame, text=get_text("settings", "min_area")).pack(side=tk.LEFT)
        min_area_var = tk.IntVar(value=self.config.get("detection", {}).get("blob_min_area", 100))
        self.widgets["detection.blob_min_area"] = min_area_var
        ttk.Spinbox(min_area_frame, from_=10, to=5000, increment=10,
                   textvariable=min_area_var, width=10, command=self._mark_modified).pack(side=tk.RIGHT)
        
        max_area_frame = ttk.Frame(blob_frame)
        max_area_frame.pack(fill=tk.X, pady=2)
        ttk.Label(max_area_frame, text=get_text("settings", "max_area")).pack(side=tk.LEFT)
        max_area_var = tk.IntVar(value=self.config.get("detection", {}).get("blob_max_area", 1000))
        self.widgets["detection.blob_max_area"] = max_area_var
        ttk.Spinbox(max_area_frame, from_=10, to=5000, increment=10,
                   textvariable=max_area_var, width=10, command=self._mark_modified).pack(side=tk.RIGHT)
    
    def _create_game_tab(self):
        """Create game settings tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=get_text("settings", "tab_game"))
        
        # Create scrollable frame
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Camera settings
        camera_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "camera"), padding=10)
        camera_frame.pack(fill=tk.X, padx=10, pady=5)
        
        cam_id_frame = ttk.Frame(camera_frame)
        cam_id_frame.pack(fill=tk.X, pady=2)
        ttk.Label(cam_id_frame, text=get_text("settings", "camera_id")).pack(side=tk.LEFT)
        cam_id_var = tk.IntVar(value=self.config.get("game", {}).get("camera_id", 0))
        self.widgets["game.camera_id"] = cam_id_var
        ttk.Spinbox(cam_id_frame, from_=0, to=5, textvariable=cam_id_var,
                   width=10, command=self._mark_modified).pack(side=tk.RIGHT)
        
        # Timing settings
        timing_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "timing"), padding=10)
        timing_frame.pack(fill=tk.X, padx=10, pady=5)
        
        dwell_frame = ttk.Frame(timing_frame)
        dwell_frame.pack(fill=tk.X, pady=2)
        ttk.Label(dwell_frame, text=get_text("settings", "dwell_time")).pack(side=tk.LEFT)
        dwell_var = tk.DoubleVar(value=self.config.get("game", {}).get("dwell_time_seconds", 2.0))
        self.widgets["game.dwell_time_seconds"] = dwell_var
        ttk.Spinbox(dwell_frame, from_=0.5, to=5.0, increment=0.1,
                   textvariable=dwell_var, width=10, command=self._mark_modified).pack(side=tk.RIGHT)
        
        exit_frame = ttk.Frame(timing_frame)
        exit_frame.pack(fill=tk.X, pady=2)
        ttk.Label(exit_frame, text=get_text("settings", "exit_hover_time")).pack(side=tk.LEFT)
        exit_var = tk.DoubleVar(value=self.config.get("game", {}).get("exit_hover_seconds", 3.0))
        self.widgets["game.exit_hover_seconds"] = exit_var
        ttk.Spinbox(exit_frame, from_=1.0, to=10.0, increment=0.5,
                   textvariable=exit_var, width=10, command=self._mark_modified).pack(side=tk.RIGHT)
        
        # Display settings
        display_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "display"), padding=10)
        display_frame.pack(fill=tk.X, padx=10, pady=5)
        
        dark_var = tk.BooleanVar(value=self.config.get("game", {}).get("dark_mode", True))
        self.widgets["game.dark_mode"] = dark_var
        ttk.Checkbutton(display_frame, text=get_text("settings", "dark_mode"),
                       variable=dark_var, command=self._mark_modified).pack(anchor=tk.W, pady=2)
        
        fullscreen_var = tk.BooleanVar(value=self.config.get("game", {}).get("fullscreen", True))
        self.widgets["game.fullscreen"] = fullscreen_var
        ttk.Checkbutton(display_frame, text=get_text("settings", "fullscreen"),
                       variable=fullscreen_var, command=self._mark_modified).pack(anchor=tk.W, pady=2)
        
        # Adaptive settings
        adaptive_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "adaptive"), padding=10)
        adaptive_frame.pack(fill=tk.X, padx=10, pady=5)
        
        adaptive_var = tk.BooleanVar(value=self.config.get("game", {}).get("adaptive_params", True))
        self.widgets["game.adaptive_params"] = adaptive_var
        ttk.Checkbutton(adaptive_frame, text=get_text("settings", "enable_adaptive"),
                       variable=adaptive_var, command=self._mark_modified).pack(anchor=tk.W, pady=2)
        
        rate_frame = ttk.Frame(adaptive_frame)
        rate_frame.pack(fill=tk.X, pady=2)
        ttk.Label(rate_frame, text=get_text("settings", "adaptation_rate")).pack(side=tk.LEFT)
        rate_var = tk.DoubleVar(value=self.config.get("game", {}).get("adaptation_rate", 0.1))
        self.widgets["game.adaptation_rate"] = rate_var
        ttk.Spinbox(rate_frame, from_=0.01, to=1.0, increment=0.01,
                   textvariable=rate_var, width=10, command=self._mark_modified).pack(side=tk.RIGHT)
        
        # Question bank
        bank_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "question_bank"), padding=10)
        bank_frame.pack(fill=tk.X, padx=10, pady=5)
        
        bank_var = tk.StringVar(value=self.config.get("game", {}).get("question_bank", 
                                                                      "assets/templates/questions_template.xlsx"))
        self.widgets["game.question_bank"] = bank_var
        
        bank_entry_frame = ttk.Frame(bank_frame)
        bank_entry_frame.pack(fill=tk.X, pady=2)
        ttk.Entry(bank_entry_frame, textvariable=bank_var, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(bank_entry_frame, text=get_text("common", "browse"),
                  command=lambda: self._browse_file(bank_var, "Excel files", "*.xlsx")).pack(side=tk.RIGHT, padx=(5,0))
    
    def _create_stimulus_tab(self):
        """Create stimulus settings tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=get_text("settings", "tab_stimulus"))
        
        # Create scrollable frame
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Protocol settings
        protocol_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "protocol"), padding=10)
        protocol_frame.pack(fill=tk.X, padx=10, pady=5)
        
        protocol_var = tk.StringVar(value=self.config.get("stimulus", {}).get("default_protocol", "standard"))
        self.widgets["stimulus.default_protocol"] = protocol_var
        
        ttk.Radiobutton(protocol_frame, text=get_text("settings", "protocol_standard"),
                       variable=protocol_var, value="standard", command=self._mark_modified).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(protocol_frame, text=get_text("settings", "protocol_clinical"),
                       variable=protocol_var, value="clinical", command=self._mark_modified).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(protocol_frame, text=get_text("settings", "protocol_research"),
                       variable=protocol_var, value="research", command=self._mark_modified).pack(anchor=tk.W, pady=2)
        
        # Quality settings
        quality_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "quality"), padding=10)
        quality_frame.pack(fill=tk.X, padx=10, pady=5)
        
        threshold_frame = ttk.Frame(quality_frame)
        threshold_frame.pack(fill=tk.X, pady=2)
        ttk.Label(threshold_frame, text=get_text("settings", "quality_threshold")).pack(side=tk.LEFT)
        threshold_var = tk.DoubleVar(value=self.config.get("stimulus", {}).get("quality_threshold", 0.7))
        self.widgets["stimulus.quality_threshold"] = threshold_var
        ttk.Spinbox(threshold_frame, from_=0.0, to=1.0, increment=0.05,
                   textvariable=threshold_var, width=10, command=self._mark_modified).pack(side=tk.RIGHT)
        
        adaptation_var = tk.BooleanVar(value=self.config.get("stimulus", {}).get("adaptation_enabled", True))
        self.widgets["stimulus.adaptation_enabled"] = adaptation_var
        ttk.Checkbutton(quality_frame, text=get_text("settings", "enable_adaptation"),
                       variable=adaptation_var, command=self._mark_modified).pack(anchor=tk.W, pady=2)
        
        # Task duration settings
        duration_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "task_durations"), padding=10)
        duration_frame.pack(fill=tk.X, padx=10, pady=5)
        
        fixation_frame = ttk.Frame(duration_frame)
        fixation_frame.pack(fill=tk.X, pady=2)
        ttk.Label(fixation_frame, text=get_text("settings", "fixation_duration")).pack(side=tk.LEFT)
        fixation_var = tk.IntVar(value=self.config.get("stimulus", {}).get("fixation_duration", 5))
        self.widgets["stimulus.fixation_duration"] = fixation_var
        ttk.Spinbox(fixation_frame, from_=1, to=30, textvariable=fixation_var,
                   width=10, command=self._mark_modified).pack(side=tk.RIGHT)
        
        pursuit_frame = ttk.Frame(duration_frame)
        pursuit_frame.pack(fill=tk.X, pady=2)
        ttk.Label(pursuit_frame, text=get_text("settings", "pursuit_duration")).pack(side=tk.LEFT)
        pursuit_var = tk.IntVar(value=self.config.get("stimulus", {}).get("smooth_pursuit_duration", 10))
        self.widgets["stimulus.smooth_pursuit_duration"] = pursuit_var
        ttk.Spinbox(pursuit_frame, from_=1, to=60, textvariable=pursuit_var,
                   width=10, command=self._mark_modified).pack(side=tk.RIGHT)
        
        saccade_frame = ttk.Frame(duration_frame)
        saccade_frame.pack(fill=tk.X, pady=2)
        ttk.Label(saccade_frame, text=get_text("settings", "saccade_duration")).pack(side=tk.LEFT)
        saccade_var = tk.IntVar(value=self.config.get("stimulus", {}).get("saccade_duration_per_point", 3))
        self.widgets["stimulus.saccade_duration_per_point"] = saccade_var
        ttk.Spinbox(saccade_frame, from_=1, to=10, textvariable=saccade_var,
                   width=10, command=self._mark_modified).pack(side=tk.RIGHT)
        
        prep_frame = ttk.Frame(duration_frame)
        prep_frame.pack(fill=tk.X, pady=2)
        ttk.Label(prep_frame, text=get_text("settings", "preparation_duration")).pack(side=tk.LEFT)
        prep_var = tk.IntVar(value=self.config.get("stimulus", {}).get("preparation_duration", 3))
        self.widgets["stimulus.preparation_duration"] = prep_var
        ttk.Spinbox(prep_frame, from_=1, to=10, textvariable=prep_var,
                   width=10, command=self._mark_modified).pack(side=tk.RIGHT)
        
        # Target size settings
        size_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "target_size"), padding=10)
        size_frame.pack(fill=tk.X, padx=10, pady=5)
        
        target_range = self.config.get("stimulus", {}).get("target_size_range", [15, 40])
        
        min_size_frame = ttk.Frame(size_frame)
        min_size_frame.pack(fill=tk.X, pady=2)
        ttk.Label(min_size_frame, text=get_text("settings", "min_size")).pack(side=tk.LEFT)
        min_size_var = tk.IntVar(value=target_range[0])
        self.widgets["stimulus.target_size_min"] = min_size_var
        ttk.Spinbox(min_size_frame, from_=5, to=50, textvariable=min_size_var,
                   width=10, command=self._mark_modified).pack(side=tk.RIGHT)
        
        max_size_frame = ttk.Frame(size_frame)
        max_size_frame.pack(fill=tk.X, pady=2)
        ttk.Label(max_size_frame, text=get_text("settings", "max_size")).pack(side=tk.LEFT)
        max_size_var = tk.IntVar(value=target_range[1])
        self.widgets["stimulus.target_size_max"] = max_size_var
        ttk.Spinbox(max_size_frame, from_=10, to=100, textvariable=max_size_var,
                   width=10, command=self._mark_modified).pack(side=tk.RIGHT)
    
    def _create_paths_tab(self):
        """Create file paths tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=get_text("settings", "tab_paths"))
        
        # Create scrollable frame
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Output directories
        paths_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "output_paths"), padding=10)
        paths_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Database directory
        db_frame = ttk.Frame(paths_frame)
        db_frame.pack(fill=tk.X, pady=5)
        ttk.Label(db_frame, text=get_text("settings", "database_dir"), width=20).pack(side=tk.LEFT)
        db_var = tk.StringVar(value=self.config.get("paths", {}).get("database_dir", "Database"))
        self.widgets["paths.database_dir"] = db_var
        ttk.Entry(db_frame, textvariable=db_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(db_frame, text=get_text("common", "browse"),
                  command=lambda: self._browse_directory(db_var)).pack(side=tk.RIGHT)
        
        # Sessions directory
        sess_frame = ttk.Frame(paths_frame)
        sess_frame.pack(fill=tk.X, pady=5)
        ttk.Label(sess_frame, text=get_text("settings", "sessions_dir"), width=20).pack(side=tk.LEFT)
        sess_var = tk.StringVar(value=self.config.get("paths", {}).get("sessions_dir", "Sessions"))
        self.widgets["paths.sessions_dir"] = sess_var
        ttk.Entry(sess_frame, textvariable=sess_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(sess_frame, text=get_text("common", "browse"),
                  command=lambda: self._browse_directory(sess_var)).pack(side=tk.RIGHT)
        
        # Logs directory
        logs_frame = ttk.Frame(paths_frame)
        logs_frame.pack(fill=tk.X, pady=5)
        ttk.Label(logs_frame, text=get_text("settings", "logs_dir"), width=20).pack(side=tk.LEFT)
        logs_var = tk.StringVar(value=self.config.get("paths", {}).get("logs_dir", "Logs"))
        self.widgets["paths.logs_dir"] = logs_var
        ttk.Entry(logs_frame, textvariable=logs_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(logs_frame, text=get_text("common", "browse"),
                  command=lambda: self._browse_directory(logs_var)).pack(side=tk.RIGHT)
        
        # Assets directory
        assets_frame = ttk.Frame(paths_frame)
        assets_frame.pack(fill=tk.X, pady=5)
        ttk.Label(assets_frame, text=get_text("settings", "assets_dir"), width=20).pack(side=tk.LEFT)
        assets_var = tk.StringVar(value=self.config.get("paths", {}).get("assets_dir", "assets"))
        self.widgets["paths.assets_dir"] = assets_var
        ttk.Entry(assets_frame, textvariable=assets_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(assets_frame, text=get_text("common", "browse"),
                  command=lambda: self._browse_directory(assets_var)).pack(side=tk.RIGHT)
        
        # Info label
        info_label = ttk.Label(scrollable_frame, 
                              text=get_text("settings", "paths_info"),
                              wraplength=800,
                              foreground="gray")
        info_label.pack(padx=10, pady=10)
    
    def _create_advanced_tab(self):
        """Create advanced options tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=get_text("settings", "tab_advanced"))
        
        # Create scrollable frame
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # OBS integration settings
        obs_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "obs_integration"), padding=10)
        obs_frame.pack(fill=tk.X, padx=10, pady=5)
        
        auto_start_var = tk.BooleanVar(value=self.config.get("obs", {}).get("auto_start", False))
        self.widgets["obs.auto_start"] = auto_start_var
        ttk.Checkbutton(obs_frame, text=get_text("settings", "obs_auto_start"),
                       variable=auto_start_var, command=self._mark_modified).pack(anchor=tk.W, pady=2)
        
        camera_frame = ttk.Frame(obs_frame)
        camera_frame.pack(fill=tk.X, pady=5)
        ttk.Label(camera_frame, text=get_text("settings", "virtual_camera")).pack(side=tk.LEFT)
        camera_var = tk.StringVar(value=self.config.get("obs", {}).get("virtual_camera_name", "OBS Virtual Camera"))
        self.widgets["obs.virtual_camera_name"] = camera_var
        ttk.Entry(camera_frame, textvariable=camera_var).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5,0))
        
        # Report settings
        report_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "report_settings"), padding=10)
        report_frame.pack(fill=tk.X, padx=10, pady=5)
        
        branding_var = tk.BooleanVar(value=self.config.get("report", {}).get("include_branding", True))
        self.widgets["report.include_branding"] = branding_var
        ttk.Checkbutton(report_frame, text=get_text("settings", "include_branding"),
                       variable=branding_var, command=self._mark_modified).pack(anchor=tk.W, pady=2)
        
        author_frame = ttk.Frame(report_frame)
        author_frame.pack(fill=tk.X, pady=2)
        ttk.Label(author_frame, text=get_text("settings", "author_name")).pack(side=tk.LEFT)
        author_var = tk.StringVar(value=self.config.get("report", {}).get("author_name", 
                                                                          "Kahlil Gibran Al Zulmi"))
        self.widgets["report.author_name"] = author_var
        ttk.Entry(author_frame, textvariable=author_var).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5,0))
        
        footer_frame = ttk.Frame(report_frame)
        footer_frame.pack(fill=tk.X, pady=2)
        ttk.Label(footer_frame, text=get_text("settings", "footer_text")).pack(side=tk.LEFT)
        footer_var = tk.StringVar(value=self.config.get("report", {}).get("footer_text", 
                                                                          "Medical Technology Study Program - ITS"))
        self.widgets["report.footer_text"] = footer_var
        ttk.Entry(footer_frame, textvariable=footer_var).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5,0))
        
        # Performance settings
        perf_frame = ttk.LabelFrame(scrollable_frame, text=get_text("settings", "performance"), padding=10)
        perf_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(perf_frame, text=get_text("settings", "performance_info"),
                 wraplength=800, foreground="gray").pack(anchor=tk.W, pady=5)
        
        # Reset button
        reset_frame = ttk.Frame(scrollable_frame)
        reset_frame.pack(fill=tk.X, padx=10, pady=20)
        
        ttk.Button(reset_frame, text=get_text("settings", "reset_defaults"),
                  command=self._reset_to_defaults, style="Accent.TButton").pack()
    
    def _create_button_frame(self, parent):
        """Create dialog button frame."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X)
        
        # Left side - status label
        self.status_label = ttk.Label(button_frame, text="", foreground="gray")
        self.status_label.pack(side=tk.LEFT)
        
        # Right side - buttons
        ttk.Button(button_frame, text=get_text("common", "cancel"),
                  command=self._on_cancel).pack(side=tk.RIGHT, padx=(5,0))
        ttk.Button(button_frame, text=get_text("common", "apply"),
                  command=self._on_apply).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text=get_text("common", "ok"),
                  command=self._on_ok, style="Accent.TButton").pack(side=tk.RIGHT, padx=(0,5))
    
    def _mark_modified(self):
        """Mark configuration as modified."""
        if not self.modified:
            self.modified = True
            self.status_label.config(text=get_text("settings", "modified"), foreground="orange")
    
    def _browse_file(self, var, file_desc, pattern):
        """Browse for file."""
        filename = filedialog.askopenfilename(
            parent=self.dialog,
            title=get_text("common", "select_file"),
            filetypes=[(file_desc, pattern), ("All files", "*.*")]
        )
        if filename:
            var.set(filename)
            self._mark_modified()
    
    def _browse_directory(self, var):
        """Browse for directory."""
        directory = filedialog.askdirectory(
            parent=self.dialog,
            title=get_text("common", "select_directory")
        )
        if directory:
            var.set(directory)
            self._mark_modified()
    
    def _apply_settings(self) -> bool:
        """
        Apply settings from widgets to config.
        
        Returns:
            bool: True if successful
        """
        try:
            # Update config from widgets
            for key, widget in self.widgets.items():
                if "." in key:
                    section, field = key.split(".", 1)
                    if section not in self.config:
                        self.config[section] = {}
                    
                    # Handle special cases
                    if field == "target_size_min":
                        if "target_size_range" not in self.config[section]:
                            self.config[section]["target_size_range"] = [15, 40]
                        self.config[section]["target_size_range"][0] = widget.get()
                    elif field == "target_size_max":
                        if "target_size_range" not in self.config[section]:
                            self.config[section]["target_size_range"] = [15, 40]
                        self.config[section]["target_size_range"][1] = widget.get()
                    else:
                        self.config[section][field] = widget.get()
                else:
                    self.config[key] = widget.get()
            
            # Validate settings
            if not self._validate_settings():
                return False
            
            # Save configuration
            if save_config(self.config, self.config_path):
                self.modified = False
                self.status_label.config(text=get_text("settings", "saved"), foreground="green")
                logger.info("Settings saved successfully")
                
                # Call callback if provided
                if self.callback:
                    self.callback(self.config)
                
                return True
            else:
                messagebox.showerror(
                    get_text("common", "error"),
                    get_text("settings", "save_error")
                )
                return False
                
        except Exception as e:
            logger.error(f"Error applying settings: {e}")
            messagebox.showerror(
                get_text("common", "error"),
                f"Failed to apply settings: {str(e)}"
            )
            return False
    
    def _validate_settings(self) -> bool:
        """
        Validate settings before saving.
        
        Returns:
            bool: True if valid
        """
        # Validate window dimensions
        if self.config["ui"]["window_width"] < 800:
            messagebox.showwarning(
                get_text("common", "warning"),
                get_text("settings", "window_too_small")
            )
            return False
        
        # Validate Hough radii
        if self.config["detection"]["hough_min_radius"] >= self.config["detection"]["hough_max_radius"]:
            messagebox.showwarning(
                get_text("common", "warning"),
                get_text("settings", "invalid_radius_range")
            )
            return False
        
        # Validate blob areas
        if self.config["detection"]["blob_min_area"] >= self.config["detection"]["blob_max_area"]:
            messagebox.showwarning(
                get_text("common", "warning"),
                get_text("settings", "invalid_area_range")
            )
            return False
        
        # Validate target sizes
        target_range = self.config["stimulus"].get("target_size_range", [15, 40])
        if target_range[0] >= target_range[1]:
            messagebox.showwarning(
                get_text("common", "warning"),
                get_text("settings", "invalid_size_range")
            )
            return False
        
        return True
    
    def _reset_to_defaults(self):
        """Reset all settings to default values."""
        result = messagebox.askyesno(
            get_text("settings", "reset_defaults"),
            get_text("settings", "reset_confirm")
        )
        
        if result:
            # Reset config to defaults
            self.config = get_default_config()
            
            # Update all widgets
            for key, widget in self.widgets.items():
                if "." in key:
                    section, field = key.split(".", 1)
                    value = self.config.get(section, {}).get(field)
                    
                    # Handle special cases
                    if field == "target_size_min":
                        value = self.config.get(section, {}).get("target_size_range", [15, 40])[0]
                    elif field == "target_size_max":
                        value = self.config.get(section, {}).get("target_size_range", [15, 40])[1]
                else:
                    value = self.config.get(key)
                
                if value is not None:
                    widget.set(value)
            
            self._mark_modified()
            messagebox.showinfo(
                get_text("common", "success"),
                get_text("settings", "reset_success")
            )
    
    def _on_ok(self):
        """Handle OK button."""
        if self._apply_settings():
            self.dialog.destroy()
    
    def _on_apply(self):
        """Handle Apply button."""
        self._apply_settings()
    
    def _on_cancel(self):
        """Handle Cancel button."""
        if self.modified:
            result = messagebox.askyesnocancel(
                get_text("settings", "unsaved_changes"),
                get_text("settings", "save_before_close")
            )
            
            if result is None:  # Cancel
                return
            elif result:  # Yes
                if not self._apply_settings():
                    return
        
        self.dialog.destroy()
    
    def _on_close(self):
        """Handle window close button."""
        self._on_cancel()


def launch_settings_dialog(parent: tk.Tk, config_path: str = "config.json", 
                          callback: Callable = None):
    """
    Launch settings dialog.
    
    Args:
        parent: Parent window
        config_path: Path to configuration file
        callback: Optional callback function to call after saving settings
    """
    dialog = SettingsDialog(parent, config_path, callback)
    dialog.launch()


if __name__ == "__main__":
    # Test settings dialog
    root = tk.Tk()
    root.title("Settings Test")
    root.geometry("400x300")
    
    def test_callback(config):
        print("Settings saved!")
        print(f"Language: {config['language']}")
        print(f"Theme: {config['ui']['theme']}")
    
    ttk.Button(root, text="Open Settings", 
              command=lambda: launch_settings_dialog(root, callback=test_callback)).pack(pady=50)
    
    root.mainloop()
