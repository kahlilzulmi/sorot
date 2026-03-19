"""
Detection Wizard Module
Multi-step Tkinter wizard for video-based eye/pupil detection.

Steps:
1. Video Selection - Choose input video file
2. Method Selection - Select detection methods to use
3. Parameter Tuning - Adjust parameters with real-time preview
4. Processing Options - Configure output and processing settings
5. Video Alignment - Optional frame-by-frame alignment tool
6. Processing - Run detection and show progress
7. Results - View and save results

Author: Eye Tracker Research Project
Date: November 2025
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
from PIL import Image, ImageTk
import numpy as np

from utils.logger import log_info, log_warning, log_error
from utils.config_manager import load_config, save_config
from utils.localization import get_text
from modules.detection_algorithms import (
    process_video_single_method,
    process_video_parallel,
    process_frame_with_method,
    get_default_params,
    detect_hough_circle,
    detect_contour,
    detect_color,
    detect_combined,
    detect_blob
)


# ============================================================================
# DETECTION WIZARD CLASS
# ============================================================================

class DetectionWizard:
    """Multi-step wizard for video-based eye detection."""
    
    def __init__(self, parent):
        """
        Initialize the detection wizard.
        
        Args:
            parent: Parent Tkinter window
        """
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title(get_text("detection.wizard_title"))
        self.window.geometry("900x700")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - 450
        y = (self.window.winfo_screenheight() // 2) - 350
        self.window.geometry(f'900x700+{x}+{y}')
        
        # Make modal
        self.window.transient(parent)
        self.window.grab_set()
        
        # Load configuration
        self.config = load_config()
        
        # Wizard state
        self.current_step = 0
        self.total_steps = 7
        
        # Data storage
        self.video_paths = []  # Support multiple videos
        self.video_path = None  # Keep for backward compatibility
        self.video_info = {}
        self.selected_methods = []
        self.method_params = {}
        self.processing_options = {
            'apply_kalman': True,
            'parallel_processing': False,
            'save_annotated': True,
            'save_raw_data': True
        }
        self.alignment_config = None  # Store alignment configuration
        self.alignment_offsets = {}
        self.results = {}
        
        # Preview
        self.preview_frame = None
        self.preview_frame_num = 0
        self.video_capture = None
        
        # Setup UI
        self.setup_ui()
        
        log_info("Detection wizard opened")
    
    def setup_ui(self):
        """Setup the wizard UI."""
        # Header
        header_frame = ttk.Frame(self.window)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(
            header_frame,
            text=get_text("detection.wizard_title"),
            font=('Arial', 16, 'bold')
        ).pack(anchor=tk.W)
        
        # Progress bar
        progress_frame = ttk.Frame(self.window)
        progress_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=self.total_steps - 1,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X)
        
        self.step_label = ttk.Label(
            progress_frame,
            text=self.get_step_text(0),
            font=('Arial', 9)
        )
        self.step_label.pack(anchor=tk.W, pady=5)
        
        # Main content area
        self.content_frame = ttk.Frame(self.window)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Navigation buttons
        nav_frame = ttk.Frame(self.window)
        nav_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.back_button = ttk.Button(
            nav_frame,
            text=get_text("wizard.back"),
            command=self.go_back,
            state=tk.DISABLED
        )
        self.back_button.pack(side=tk.LEFT)
        
        self.cancel_button = ttk.Button(
            nav_frame,
            text=get_text("common.cancel"),
            command=self.cancel_wizard
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        self.next_button = ttk.Button(
            nav_frame,
            text=get_text("wizard.next"),
            command=self.go_next
        )
        self.next_button.pack(side=tk.RIGHT)
        
        # Show first step
        self.show_step(0)
    
    def get_step_text(self, step: int) -> str:
        """Get the text description for a step."""
        steps = [
            get_text("wizard.step_video_selection"),
            get_text("wizard.step_method_selection"),
            get_text("wizard.step_parameter_tuning"),
            get_text("wizard.step_processing_options"),
            get_text("wizard.step_video_alignment"),
            get_text("wizard.step_processing"),
            get_text("wizard.step_results")
        ]
        return f"{get_text('wizard.step')} {step + 1}/{self.total_steps}: {steps[step]}"
    
    def show_step(self, step: int):
        """Display the specified wizard step."""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Update progress
        self.current_step = step
        self.progress_var.set(step)
        self.step_label.config(text=self.get_step_text(step))
        
        # Update navigation buttons
        self.back_button.config(state=tk.NORMAL if step > 0 else tk.DISABLED)
        
        if step == self.total_steps - 1:
            self.next_button.config(text=get_text("wizard.finish"))
        else:
            self.next_button.config(text=get_text("wizard.next"))
        
        # Show appropriate step content
        step_methods = [
            self.show_video_selection,
            self.show_method_selection,
            self.show_parameter_tuning,
            self.show_processing_options,
            self.show_video_alignment,
            self.show_processing,
            self.show_results
        ]
        
        step_methods[step]()
    
    # ========================================================================
    # STEP 1: VIDEO SELECTION
    # ========================================================================
    
    def show_video_selection(self):
        """Step 1: Select video file(s)."""
        ttk.Label(
            self.content_frame,
            text=get_text("wizard.video_selection_title"),
            font=('Arial', 12, 'bold')
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Multi-video selection option
        multi_frame = ttk.Frame(self.content_frame)
        multi_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(
            multi_frame,
            text=get_text("wizard.video_selection_mode"),
            font=('Arial', 10)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.multi_video_var = tk.BooleanVar(value=len(self.video_paths) > 1)
        ttk.Checkbutton(
            multi_frame,
            text=get_text("wizard.load_multiple_videos"),
            variable=self.multi_video_var,
            command=self._toggle_multi_video_mode
        ).pack(side=tk.LEFT)
        
        # Video selection controls
        select_frame = ttk.Frame(self.content_frame)
        select_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            select_frame,
            text=get_text("wizard.add_video"),
            command=self._add_video
        ).pack(side=tk.LEFT, padx=5)
        
        if len(self.video_paths) > 0:
            ttk.Button(
                select_frame,
                text=get_text("wizard.remove_selected"),
                command=self._remove_video
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                select_frame,
                text=get_text("wizard.clear_all"),
                command=self._clear_videos
            ).pack(side=tk.LEFT, padx=5)
        
        # Videos list
        list_frame = ttk.LabelFrame(
            self.content_frame,
            text=get_text("wizard.selected_videos"),
            padding=10
        )
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create listbox with scrollbar
        scroll_frame = ttk.Frame(list_frame)
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(scroll_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.videos_listbox = tk.Listbox(
            scroll_frame,
            yscrollcommand=scrollbar.set,
            height=8
        )
        self.videos_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.videos_listbox.yview)
        
        # Populate listbox
        for video_path in self.video_paths:
            filename = os.path.basename(video_path)
            self.videos_listbox.insert(tk.END, filename)
        
        # Video info display for selected video
        self.video_info_frame = ttk.LabelFrame(
            self.content_frame,
            text=get_text("wizard.video_info"),
            padding=10
        )
        self.video_info_frame.pack(fill=tk.X, pady=10)
        
        if self.video_paths:
            self.video_path = self.video_paths[0]  # Set first as current
            self.load_video_info()
            self.display_video_info()
        
        # Bind selection event
        self.videos_listbox.bind('<<ListboxSelect>>', self._on_video_select)
    
    def _toggle_multi_video_mode(self):
        """Toggle between single and multiple video mode."""
        if not self.multi_video_var.get() and len(self.video_paths) > 1:
            # Keep only first video
            self.video_paths = self.video_paths[:1]
            self.show_video_selection()
    
    def _add_video(self):
        """Add video(s) to the list."""
        if self.multi_video_var.get():
            # Multiple selection
            filetypes = [
                (get_text("wizard.video_files"), "*.mp4 *.avi *.mkv *.mov"),
                (get_text("common.all_files"), "*.*")
            ]
            
            filenames = filedialog.askopenfilenames(
                parent=self.window,
                title=get_text("wizard.select_videos"),
                filetypes=filetypes
            )
            
            if filenames:
                for filename in filenames:
                    if filename not in self.video_paths:
                        self.video_paths.append(filename)
                
                # Refresh display
                self.show_step(0)
                log_info(f"Added {len(filenames)} videos")
        else:
            # Single selection
            self.browse_video()
    
    def _remove_video(self):
        """Remove selected video from list."""
        selection = self.videos_listbox.curselection()
        if selection:
            idx = selection[0]
            removed_path = self.video_paths.pop(idx)
            log_info(f"Removed video: {removed_path}")
            self.show_step(0)
    
    def _clear_videos(self):
        """Clear all videos."""
        if messagebox.askyesno(
            get_text("common.confirm"),
            get_text("wizard.confirm_clear_videos")
        ):
            self.video_paths.clear()
            self.video_path = None
            self.video_info = {}
            self.show_step(0)
            log_info("Cleared all videos")
    
    def _on_video_select(self, event):
        """Handle video selection in listbox."""
        selection = self.videos_listbox.curselection()
        if selection:
            idx = selection[0]
            self.video_path = self.video_paths[idx]
            self.load_video_info()
            self.display_video_info()
    
    def browse_video(self):
        """Open file dialog to select single video."""
        filetypes = [
            (get_text("wizard.video_files"), "*.mp4 *.avi *.mkv *.mov"),
            (get_text("common.all_files"), "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            parent=self.window,
            title=get_text("wizard.select_video"),
            filetypes=filetypes
        )
        
        if filename:
            if not self.video_paths:
                self.video_paths.append(filename)
            else:
                self.video_paths[0] = filename
            
            self.video_path = filename
            self.load_video_info()
            self.show_step(0)  # Refresh display
            log_info(f"Video selected: {filename}")
    
    def load_video_info(self):
        """Load video metadata."""
        if not self.video_path:
            return
        
        try:
            cap = cv2.VideoCapture(self.video_path)
            
            self.video_info = {
                'fps': int(cap.get(cv2.CAP_PROP_FPS)),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / int(cap.get(cv2.CAP_PROP_FPS)),
                'size_mb': os.path.getsize(self.video_path) / (1024 * 1024)
            }
            
            # Read first frame for preview
            ret, frame = cap.read()
            if ret:
                self.preview_frame = frame
                self.preview_frame_num = 0
            
            cap.release()
            log_info(f"Video info loaded: {self.video_info}")
            
        except Exception as e:
            log_error(f"Error loading video info: {str(e)}")
            messagebox.showerror(
                get_text("common.error"),
                f"Failed to load video: {str(e)}"
            )
    
    def display_video_info(self):
        """Display video information."""
        for widget in self.video_info_frame.winfo_children():
            widget.destroy()
        
        if not self.video_info:
            ttk.Label(
                self.video_info_frame,
                text=get_text("wizard.no_video_selected")
            ).pack()
            return
        
        # Info grid
        info_frame = ttk.Frame(self.video_info_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        info_items = [
            (get_text("wizard.resolution"), f"{self.video_info['width']}x{self.video_info['height']}"),
            (get_text("wizard.fps"), f"{self.video_info['fps']} fps"),
            (get_text("wizard.duration"), f"{self.video_info['duration']:.2f} seconds"),
            (get_text("wizard.frame_count"), f"{self.video_info['frame_count']} frames"),
            (get_text("wizard.file_size"), f"{self.video_info['size_mb']:.2f} MB")
        ]
        
        for i, (label, value) in enumerate(info_items):
            ttk.Label(
                info_frame,
                text=f"{label}:",
                font=('Arial', 9, 'bold')
            ).grid(row=i, column=0, sticky=tk.W, padx=5, pady=3)
            
            ttk.Label(
                info_frame,
                text=value
            ).grid(row=i, column=1, sticky=tk.W, padx=5, pady=3)
        
        # Preview thumbnail
        if self.preview_frame is not None:
            preview_frame = ttk.LabelFrame(
                self.video_info_frame,
                text=get_text("wizard.preview"),
                padding=5
            )
            preview_frame.pack(side=tk.RIGHT, padx=10)
            
            # Resize frame for thumbnail
            scale = 200 / self.preview_frame.shape[1]
            width = 200
            height = int(self.preview_frame.shape[0] * scale)
            
            resized = cv2.resize(self.preview_frame, (width, height))
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            photo = ImageTk.PhotoImage(image=img)
            
            label = ttk.Label(preview_frame, image=photo)
            label.image = photo  # Keep reference
            label.pack()
    
    # ========================================================================
    # STEP 2: METHOD SELECTION
    # ========================================================================
    
    def show_method_selection(self):
        """Step 2: Select detection methods."""
        ttk.Label(
            self.content_frame,
            text=get_text("wizard.method_selection_title"),
            font=('Arial', 12, 'bold')
        ).pack(anchor=tk.W, pady=(0, 10))
        
        ttk.Label(
            self.content_frame,
            text=get_text("wizard.method_selection_desc"),
            wraplength=800
        ).pack(anchor=tk.W, pady=(0, 20))
        
        # Method checkboxes
        self.method_vars = {}
        
        methods = [
            ('hough', get_text("detection.method_hough"), 
             get_text("detection.method_hough_desc")),
            ('contour', get_text("detection.method_contour"),
             get_text("detection.method_contour_desc")),
            ('color', get_text("detection.method_color"),
             get_text("detection.method_color_desc")),
            ('blob', get_text("detection.method_blob"),
             get_text("detection.method_blob_desc")),
            ('combined', get_text("detection.method_combined"),
             get_text("detection.method_combined_desc"))
        ]
        
        for method_key, method_name, method_desc in methods:
            method_frame = ttk.LabelFrame(
                self.content_frame,
                text=method_name,
                padding=10
            )
            method_frame.pack(fill=tk.X, pady=5)
            
            var = tk.BooleanVar(value=method_key in self.selected_methods)
            self.method_vars[method_key] = var
            
            ttk.Checkbutton(
                method_frame,
                text=method_desc,
                variable=var
            ).pack(anchor=tk.W)
        
        # Quick select buttons
        button_frame = ttk.Frame(self.content_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            button_frame,
            text=get_text("wizard.select_all"),
            command=self.select_all_methods
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text=get_text("wizard.select_none"),
            command=self.select_no_methods
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            button_frame,
            text=get_text("wizard.select_recommended"),
            command=self.select_recommended_methods
        ).pack(side=tk.LEFT, padx=5)
    
    def select_all_methods(self):
        """Select all detection methods."""
        for var in self.method_vars.values():
            var.set(True)
    
    def select_no_methods(self):
        """Deselect all methods."""
        for var in self.method_vars.values():
            var.set(False)
    
    def select_recommended_methods(self):
        """Select recommended methods (combined + one other)."""
        self.select_no_methods()
        self.method_vars['combined'].set(True)
        self.method_vars['hough'].set(True)
    
    def get_selected_methods(self) -> List[str]:
        """Get list of selected methods."""
        return [method for method, var in self.method_vars.items() if var.get()]
    
    # ========================================================================
    # STEP 3: PARAMETER TUNING
    # ========================================================================
    
    def show_parameter_tuning(self):
        """Step 3: Tune detection parameters with preview."""
        ttk.Label(
            self.content_frame,
            text=get_text("wizard.parameter_tuning_title"),
            font=('Arial', 12, 'bold')
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Get selected methods
        self.selected_methods = self.get_selected_methods()
        
        if not self.selected_methods:
            ttk.Label(
                self.content_frame,
                text=get_text("wizard.no_methods_selected"),
                foreground='red'
            ).pack(anchor=tk.W, pady=20)
            return
        
        # Split into left (parameters) and right (preview)
        paned = ttk.PanedWindow(self.content_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left: Parameters
        param_frame = ttk.Frame(paned)
        paned.add(param_frame, weight=1)
        
        # Method selector
        method_select_frame = ttk.Frame(param_frame)
        method_select_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(
            method_select_frame,
            text=get_text("wizard.current_method") + ":",
            font=('Arial', 9, 'bold')
        ).pack(side=tk.LEFT, padx=5)
        
        self.current_method_var = tk.StringVar(value=self.selected_methods[0])
        method_combo = ttk.Combobox(
            method_select_frame,
            textvariable=self.current_method_var,
            values=self.selected_methods,
            state='readonly',
            width=15
        )
        method_combo.pack(side=tk.LEFT, padx=5)
        method_combo.bind('<<ComboboxSelected>>', lambda e: self.load_method_parameters())
        
        # Parameters scroll area
        param_canvas = tk.Canvas(param_frame, highlightthickness=0)
        param_scrollbar = ttk.Scrollbar(param_frame, orient=tk.VERTICAL, command=param_canvas.yview)
        self.param_container = ttk.Frame(param_canvas)
        
        self.param_container.bind(
            '<Configure>',
            lambda e: param_canvas.configure(scrollregion=param_canvas.bbox('all'))
        )
        
        param_canvas.create_window((0, 0), window=self.param_container, anchor=tk.NW)
        param_canvas.configure(yscrollcommand=param_scrollbar.set)
        
        param_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        param_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right: Preview
        preview_frame = ttk.LabelFrame(paned, text=get_text("wizard.preview"), padding=10)
        paned.add(preview_frame, weight=1)
        
        # Preview controls
        control_frame = ttk.Frame(preview_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            control_frame,
            text=get_text("wizard.update_preview"),
            command=self.update_preview
        ).pack(side=tk.LEFT, padx=5)
        
        self.frame_scale_var = tk.IntVar(value=0)
        ttk.Scale(
            control_frame,
            from_=0,
            to=self.video_info.get('frame_count', 100) - 1,
            variable=self.frame_scale_var,
            orient=tk.HORIZONTAL,
            command=lambda v: self.seek_frame(int(float(v)))
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.frame_label = ttk.Label(control_frame, text="Frame: 0")
        self.frame_label.pack(side=tk.LEFT, padx=5)
        
        # Preview canvas
        self.preview_canvas = tk.Canvas(preview_frame, bg='black', width=400, height=300)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Load initial parameters
        self.load_method_parameters()
        self.update_preview()
    
    def load_method_parameters(self):
        """Load parameters for current method."""
        for widget in self.param_container.winfo_children():
            widget.destroy()
        
        method = self.current_method_var.get()
        default_params = get_default_params(method)
        
        # Initialize if not exists
        if method not in self.method_params:
            self.method_params[method] = default_params.copy()
        
        # Create sliders for each parameter
        self.param_widgets = {}
        
        for i, (param_name, default_value) in enumerate(default_params.items()):
            param_frame = ttk.Frame(self.param_container)
            param_frame.pack(fill=tk.X, pady=5, padx=5)
            
            # Label
            ttk.Label(
                param_frame,
                text=param_name.replace('_', ' ').title() + ":",
                font=('Arial', 9, 'bold'),
                width=20
            ).pack(side=tk.LEFT)
            
            # Value label
            value_var = tk.StringVar(value=str(self.method_params[method].get(param_name, default_value)))
            value_label = ttk.Label(param_frame, textvariable=value_var, width=10)
            value_label.pack(side=tk.RIGHT, padx=5)
            
            # Determine range based on parameter type and value
            if isinstance(default_value, int):
                if default_value <= 10:
                    from_val, to_val = 1, 20
                elif default_value <= 100:
                    from_val, to_val = 10, 200
                else:
                    from_val, to_val = default_value // 2, default_value * 2
            elif isinstance(default_value, float):
                if default_value < 1.0:
                    from_val, to_val = 0.1, 1.0
                else:
                    from_val, to_val = 0.5, default_value * 2
            else:
                continue
            
            # Slider
            current_val = self.method_params[method].get(param_name, default_value)
            var = tk.DoubleVar(value=current_val)
            
            def make_update_func(pname, pvar, vvar):
                def update(val):
                    if isinstance(default_params[pname], int):
                        val = int(float(val))
                    else:
                        val = float(val)
                    self.method_params[method][pname] = val
                    vvar.set(str(val))
                return update
            
            scale = ttk.Scale(
                param_frame,
                from_=from_val,
                to=to_val,
                variable=var,
                orient=tk.HORIZONTAL,
                command=make_update_func(param_name, var, value_var)
            )
            scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            self.param_widgets[param_name] = (var, value_var, scale)
        
        # Reset button
        ttk.Button(
            self.param_container,
            text=get_text("wizard.reset_defaults"),
            command=lambda: self.reset_parameters(method)
        ).pack(pady=10)
    
    def reset_parameters(self, method: str):
        """Reset parameters to defaults."""
        default_params = get_default_params(method)
        self.method_params[method] = default_params.copy()
        self.load_method_parameters()
        self.update_preview()
    
    def seek_frame(self, frame_num: int):
        """Seek to specific frame."""
        self.preview_frame_num = frame_num
        self.frame_label.config(text=f"Frame: {frame_num}")
        
        if self.video_path and os.path.exists(self.video_path):
            cap = cv2.VideoCapture(self.video_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            if ret:
                self.preview_frame = frame
            cap.release()
        
        self.update_preview()
    
    def update_preview(self):
        """Update preview with current parameters."""
        if self.preview_frame is None:
            return
        
        method = self.current_method_var.get()
        params = self.method_params.get(method, {})
        
        # Run detection on preview frame
        detections, annotated = process_frame_with_method(
            self.preview_frame,
            method,
            params
        )
        
        # Resize for display
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            scale = min(canvas_width / annotated.shape[1], canvas_height / annotated.shape[0])
            new_width = int(annotated.shape[1] * scale)
            new_height = int(annotated.shape[0] * scale)
            
            resized = cv2.resize(annotated, (new_width, new_height))
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            photo = ImageTk.PhotoImage(image=img)
            
            self.preview_canvas.delete('all')
            self.preview_canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=photo,
                anchor=tk.CENTER
            )
            self.preview_canvas.image = photo  # Keep reference
            
            # Show detection count
            self.preview_canvas.create_text(
                10, 10,
                text=f"Detections: {len(detections)}",
                anchor=tk.NW,
                fill='yellow',
                font=('Arial', 12, 'bold')
            )
    
    # ========================================================================
    # STEP 4: PROCESSING OPTIONS
    # ========================================================================
    
    def show_processing_options(self):
        """Step 4: Configure processing options."""
        ttk.Label(
            self.content_frame,
            text=get_text("wizard.processing_options_title"),
            font=('Arial', 12, 'bold')
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Options
        options_frame = ttk.LabelFrame(
            self.content_frame,
            text=get_text("wizard.options"),
            padding=20
        )
        options_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Kalman filter
        self.kalman_var = tk.BooleanVar(value=self.processing_options['apply_kalman'])
        ttk.Checkbutton(
            options_frame,
            text=get_text("wizard.apply_kalman_filter"),
            variable=self.kalman_var
        ).pack(anchor=tk.W, pady=5)
        
        ttk.Label(
            options_frame,
            text=get_text("wizard.kalman_desc"),
            foreground='gray',
            wraplength=700
        ).pack(anchor=tk.W, padx=20, pady=(0, 10))
        
        # Parallel processing
        self.parallel_var = tk.BooleanVar(value=self.processing_options['parallel_processing'])
        parallel_check = ttk.Checkbutton(
            options_frame,
            text=get_text("wizard.parallel_processing"),
            variable=self.parallel_var
        )
        parallel_check.pack(anchor=tk.W, pady=5)
        
        # Only enable if multiple methods selected
        if len(self.selected_methods) < 2:
            parallel_check.config(state=tk.DISABLED)
            self.parallel_var.set(False)
        
        ttk.Label(
            options_frame,
            text=get_text("wizard.parallel_desc"),
            foreground='gray',
            wraplength=700
        ).pack(anchor=tk.W, padx=20, pady=(0, 10))
        
        # Save annotated video
        self.save_annotated_var = tk.BooleanVar(value=self.processing_options['save_annotated'])
        ttk.Checkbutton(
            options_frame,
            text=get_text("wizard.save_annotated_video"),
            variable=self.save_annotated_var
        ).pack(anchor=tk.W, pady=5)
        
        # Save raw data
        self.save_raw_var = tk.BooleanVar(value=self.processing_options['save_raw_data'])
        ttk.Checkbutton(
            options_frame,
            text=get_text("wizard.save_raw_data"),
            variable=self.save_raw_var
        ).pack(anchor=tk.W, pady=5)
        
        # Output directory
        output_frame = ttk.LabelFrame(
            self.content_frame,
            text=get_text("wizard.output_directory"),
            padding=20
        )
        output_frame.pack(fill=tk.X, pady=10)
        
        self.output_dir_var = tk.StringVar(
            value=self.config.get('paths', {}).get('sessions_dir', 'Sessions')
        )
        
        ttk.Entry(
            output_frame,
            textvariable=self.output_dir_var,
            width=60
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            output_frame,
            text=get_text("wizard.browse"),
            command=self.browse_output_dir
        ).pack(side=tk.LEFT)
    
    def browse_output_dir(self):
        """Browse for output directory."""
        dirname = filedialog.askdirectory(
            parent=self.window,
            title=get_text("wizard.select_output_directory"),
            initialdir=self.output_dir_var.get()
        )
        
        if dirname:
            self.output_dir_var.set(dirname)
    
    # ========================================================================
    # STEP 5: VIDEO ALIGNMENT (Optional)
    # ========================================================================
    
    def show_video_alignment(self):
        """Step 5: Optional video alignment tool for multiple videos."""
        ttk.Label(
            self.content_frame,
            text=get_text("wizard.video_alignment_title"),
            font=('Arial', 12, 'bold')
        ).pack(anchor=tk.W, pady=(0, 10))
        
        ttk.Label(
            self.content_frame,
            text=get_text("wizard.alignment_desc"),
            wraplength=800,
            foreground='gray'
        ).pack(anchor=tk.W, pady=(0, 20))
        
        # Check if multiple videos are loaded
        has_multiple_videos = len(self.video_paths) > 1
        
        if not has_multiple_videos:
            # Single video - skip alignment
            info_frame = ttk.Frame(self.content_frame)
            info_frame.pack(fill=tk.X, pady=10)
            
            ttk.Label(
                info_frame,
                text="ℹ️ " + get_text("wizard.single_video_detected"),
                foreground='blue',
                font=('Arial', 10)
            ).pack(anchor=tk.W)
            
            ttk.Label(
                info_frame,
                text=get_text("wizard.alignment_skip_info"),
                wraplength=800,
                foreground='gray'
            ).pack(anchor=tk.W, pady=(5, 0))
            
            # Skip button
            ttk.Button(
                self.content_frame,
                text=get_text("wizard.skip_alignment"),
                command=lambda: self.show_step(self.current_step + 1)
            ).pack(pady=20)
        else:
            # Multiple videos - show alignment options
            options_frame = ttk.LabelFrame(
                self.content_frame,
                text=get_text("wizard.alignment_options"),
                padding=20
            )
            options_frame.pack(fill=tk.BOTH, expand=True, pady=10)
            
            # Display loaded videos
            ttk.Label(
                options_frame,
                text=f"{get_text('wizard.videos_loaded')}: {len(self.video_paths)}",
                font=('Arial', 10, 'bold')
            ).pack(anchor=tk.W, pady=(0, 5))
            
            videos_list_frame = ttk.Frame(options_frame)
            videos_list_frame.pack(fill=tk.X, pady=10)
            
            for i, video_path in enumerate(self.video_paths[:5]):  # Show first 5
                filename = os.path.basename(video_path)
                ttk.Label(
                    videos_list_frame,
                    text=f"  {i+1}. {filename}",
                    foreground='gray'
                ).pack(anchor=tk.W, pady=2)
            
            if len(self.video_paths) > 5:
                ttk.Label(
                    videos_list_frame,
                    text=f"  ... and {len(self.video_paths) - 5} more",
                    foreground='gray',
                    font=('Arial', 9, 'italic')
                ).pack(anchor=tk.W, pady=2)
            
            # Alignment method selection
            ttk.Label(
                options_frame,
                text=get_text("wizard.alignment_method_label"),
                font=('Arial', 10, 'bold')
            ).pack(anchor=tk.W, pady=(10, 5))
            
            self.alignment_method_var = tk.StringVar(value='skip')
            
            methods = [
                ('skip', get_text('wizard.alignment_skip')),
                ('manual', get_text('wizard.alignment_manual')),
                ('flash', get_text('wizard.alignment_flash')),
                ('audio', get_text('wizard.alignment_audio')),
                ('motion', get_text('wizard.alignment_motion'))
            ]
            
            for value, label in methods:
                ttk.Radiobutton(
                    options_frame,
                    text=label,
                    variable=self.alignment_method_var,
                    value=value
                ).pack(anchor=tk.W, padx=20, pady=2)
            
            # Launch alignment wizard button
            button_frame = ttk.Frame(options_frame)
            button_frame.pack(fill=tk.X, pady=(20, 0))
            
            ttk.Button(
                button_frame,
                text=get_text("wizard.launch_alignment_tool"),
                command=self._launch_alignment_wizard,
                width=25
            ).pack(side=tk.LEFT, padx=5)
            
            # Show alignment status
            self.alignment_status_label = ttk.Label(
                options_frame,
                text=get_text("wizard.alignment_not_configured") if not self.alignment_config else get_text("wizard.alignment_configured"),
                foreground='orange' if not self.alignment_config else 'green',
                font=('Arial', 10)
            )
            self.alignment_status_label.pack(anchor=tk.W, pady=(10, 0))
    
    def _launch_alignment_wizard(self):
        """Launch the video alignment wizard."""
        method = self.alignment_method_var.get()
        
        if method == 'skip':
            messagebox.showinfo(
                get_text("common.info"),
                get_text("wizard.alignment_skipped_message")
            )
            return
        
        try:
            from modules.video_alignment_wizard import VideoAlignmentWizard
            
            # Create alignment wizard
            config = load_config()
            lang = config.get('language', 'en')
            
            wizard = VideoAlignmentWizard(self.window, lang)
            
            # Pre-load videos
            if self.video_paths:
                wizard.video_paths = self.video_paths.copy()
                wizard.engine.load_videos(self.video_paths)
                wizard.current_frames = [0] * len(self.video_paths)
                wizard.video_captures = [cv2.VideoCapture(path) for path in self.video_paths]
            
            # Set method
            wizard.sync_method.set(method)
            
            # Launch wizard
            wizard.launch()
            
            # Wait for wizard to close
            self.window.wait_window(wizard.window)
            
            # Get alignment configuration
            if wizard.engine.alignment_points:
                self.alignment_config = {
                    'time_offsets': wizard.engine.time_offsets,
                    'alignment_points': wizard.engine.alignment_points,
                    'sync_method': wizard.engine.sync_method
                }
                
                self.alignment_status_label.config(
                    text=get_text("wizard.alignment_configured"),
                    foreground='green'
                )
                
                messagebox.showinfo(
                    get_text("common.success"),
                    get_text("wizard.alignment_success_message")
                )
            
        except Exception as e:
            log_error(f"Error launching alignment wizard: {e}")
            messagebox.showerror(
                get_text("common.error"),
                f"{get_text('wizard.alignment_error')}: {str(e)}"
            )
    
    # ========================================================================
    # STEP 6: PROCESSING
    # ========================================================================
    
    def show_processing(self):
        """Step 6: Run detection processing."""
        ttk.Label(
            self.content_frame,
            text=get_text("wizard.processing_title"),
            font=('Arial', 12, 'bold')
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Progress display
        self.processing_progress_frame = ttk.LabelFrame(
            self.content_frame,
            text=get_text("wizard.progress"),
            padding=20
        )
        self.processing_progress_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.processing_status_label = ttk.Label(
            self.processing_progress_frame,
            text=get_text("wizard.ready_to_process"),
            font=('Arial', 10)
        )
        self.processing_status_label.pack(pady=10)
        
        self.processing_progress = ttk.Progressbar(
            self.processing_progress_frame,
            mode='indeterminate'
        )
        self.processing_progress.pack(fill=tk.X, pady=10)
        
        self.processing_log = tk.Text(
            self.processing_progress_frame,
            height=15,
            font=('Consolas', 9),
            state=tk.DISABLED
        )
        self.processing_log.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Start button
        self.start_processing_button = ttk.Button(
            self.content_frame,
            text=get_text("wizard.start_processing"),
            command=self.start_processing
        )
        self.start_processing_button.pack(pady=10)
        
        # Disable next button until processing complete
        self.next_button.config(state=tk.DISABLED)
    
    def start_processing(self):
        """Start the detection processing."""
        self.start_processing_button.config(state=tk.DISABLED)
        self.back_button.config(state=tk.DISABLED)
        self.processing_progress.start()
        
        # Update options from UI
        self.processing_options['apply_kalman'] = self.kalman_var.get()
        self.processing_options['parallel_processing'] = self.parallel_var.get()
        self.processing_options['save_annotated'] = self.save_annotated_var.get()
        self.processing_options['save_raw_data'] = self.save_raw_var.get()
        
        # Create output directory
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        video_name = os.path.splitext(os.path.basename(self.video_path))[0]
        session_dir = os.path.join(
            self.output_dir_var.get(),
            f"detection_{video_name}_{timestamp}"
        )
        os.makedirs(session_dir, exist_ok=True)
        
        self.log_processing(f"Created session directory: {session_dir}")
        
        # Run processing in thread
        thread = threading.Thread(
            target=self.run_processing_thread,
            args=(session_dir,)
        )
        thread.daemon = True
        thread.start()
    
    def log_processing(self, message: str):
        """Add message to processing log."""
        self.processing_log.config(state=tk.NORMAL)
        self.processing_log.insert(tk.END, f"{message}\n")
        self.processing_log.see(tk.END)
        self.processing_log.config(state=tk.DISABLED)
    
    def run_processing_thread(self, session_dir: str):
        """Run processing in background thread."""
        try:
            self.log_processing(f"Processing video: {self.video_path}")
            self.log_processing(f"Methods: {', '.join(self.selected_methods)}")
            
            if self.processing_options['parallel_processing'] and len(self.selected_methods) > 1:
                self.log_processing("Using parallel processing...")
                
                # Run parallel processing
                results = process_video_parallel(
                    self.video_path,
                    session_dir,
                    self.selected_methods,
                    self.method_params,
                    self.processing_options['apply_kalman']
                )
                
                self.results = results
                
            else:
                self.log_processing("Using sequential processing...")
                
                # Run each method sequentially
                results = {}
                for method in self.selected_methods:
                    self.log_processing(f"Processing with {method} method...")
                    
                    output_path = os.path.join(
                        session_dir,
                        f"output_{method}.mp4"
                    )
                    
                    result = process_video_single_method(
                        self.video_path,
                        output_path,
                        method,
                        self.method_params.get(method),
                        self.processing_options['apply_kalman']
                    )
                    
                    results[method] = result
                    self.log_processing(f"✓ {method}: {result['detection_rate']*100:.1f}% detection rate")
                
                self.results = results
            
            self.log_processing("\n✓ Processing complete!")
            log_info(f"Detection processing complete: {session_dir}")
            
            # Enable next button
            self.window.after(0, lambda: self.next_button.config(state=tk.NORMAL))
            self.window.after(0, self.processing_progress.stop)
            
        except Exception as e:
            error_msg = f"Error during processing: {str(e)}"
            log_error(error_msg)
            self.log_processing(f"\n✗ {error_msg}")
            self.window.after(0, self.processing_progress.stop)
            self.window.after(
                0,
                lambda: messagebox.showerror(
                    get_text("common.error"),
                    error_msg
                )
            )
    
    # ========================================================================
    # STEP 7: RESULTS
    # ========================================================================
    
    def show_results(self):
        """Step 7: Display processing results."""
        ttk.Label(
            self.content_frame,
            text=get_text("wizard.results_title"),
            font=('Arial', 12, 'bold')
        ).pack(anchor=tk.W, pady=(0, 10))
        
        if not self.results:
            ttk.Label(
                self.content_frame,
                text=get_text("wizard.no_results"),
                foreground='red'
            ).pack(pady=20)
            return
        
        # Results summary
        summary_frame = ttk.LabelFrame(
            self.content_frame,
            text=get_text("wizard.summary"),
            padding=20
        )
        summary_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create results table
        columns = ('method', 'frames', 'detections', 'rate', 'avg_per_frame')
        tree = ttk.Treeview(summary_frame, columns=columns, show='headings', height=len(self.results))
        
        tree.heading('method', text=get_text("wizard.method"))
        tree.heading('frames', text=get_text("wizard.frames_detected"))
        tree.heading('detections', text=get_text("wizard.total_detections"))
        tree.heading('rate', text=get_text("wizard.detection_rate"))
        tree.heading('avg_per_frame', text=get_text("wizard.avg_per_frame"))
        
        for method, result in self.results.items():
            if result.get('success'):
                tree.insert('', tk.END, values=(
                    method,
                    result['frames_with_detection'],
                    result['total_detections'],
                    f"{result['detection_rate']*100:.1f}%",
                    f"{result['avg_detections_per_frame']:.2f}"
                ))
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Action buttons
        action_frame = ttk.Frame(self.content_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            action_frame,
            text=get_text("wizard.open_output_folder"),
            command=self.open_output_folder
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            action_frame,
            text=get_text("wizard.view_videos"),
            command=self.view_output_videos
        ).pack(side=tk.LEFT, padx=5)
    
    def open_output_folder(self):
        """Open the output folder in file explorer."""
        if self.results:
            first_result = next(iter(self.results.values()))
            if 'output_path' in first_result:
                output_dir = os.path.dirname(first_result['output_path'])
                os.startfile(output_dir)
    
    def view_output_videos(self):
        """View output videos."""
        # TODO: Implement video viewer
        messagebox.showinfo(
            get_text("common.info"),
            get_text("wizard.video_viewer_not_implemented")
        )
    
    # ========================================================================
    # NAVIGATION
    # ========================================================================
    
    def go_next(self):
        """Go to next step or finish."""
        if self.current_step == self.total_steps - 1:
            # Finish wizard
            self.finish_wizard()
        else:
            # Validate current step
            if self.validate_current_step():
                self.show_step(self.current_step + 1)
    
    def go_back(self):
        """Go to previous step."""
        if self.current_step > 0:
            self.show_step(self.current_step - 1)
    
    def validate_current_step(self) -> bool:
        """Validate current step before proceeding."""
        if self.current_step == 0:
            # Video selection
            if not self.video_path or not os.path.exists(self.video_path):
                messagebox.showwarning(
                    get_text("common.warning"),
                    get_text("wizard.please_select_video")
                )
                return False
        
        elif self.current_step == 1:
            # Method selection
            self.selected_methods = self.get_selected_methods()
            if not self.selected_methods:
                messagebox.showwarning(
                    get_text("common.warning"),
                    get_text("wizard.please_select_method")
                )
                return False
        
        return True
    
    def cancel_wizard(self):
        """Cancel and close wizard."""
        if messagebox.askokcancel(
            get_text("common.warning"),
            get_text("wizard.confirm_cancel")
        ):
            self.cleanup()
            self.window.destroy()
            log_info("Detection wizard cancelled")
    
    def finish_wizard(self):
        """Finish wizard."""
        self.cleanup()
        self.window.destroy()
        log_info("Detection wizard completed")
    
    def cleanup(self):
        """Cleanup resources."""
        if self.video_capture:
            self.video_capture.release()


# ============================================================================
# LAUNCHER FUNCTION
# ============================================================================

def launch_detection_wizard(parent):
    """
    Launch the detection wizard.
    
    Args:
        parent: Parent Tkinter window
    """
    wizard = DetectionWizard(parent)
    return wizard


if __name__ == "__main__":
    # Test code
    root = tk.Tk()
    root.withdraw()
    launch_detection_wizard(root)
    root.mainloop()
