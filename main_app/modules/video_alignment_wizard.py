"""
Video Alignment Wizard GUI

User interface for synchronizing and aligning multiple eye tracking videos.

Author: Kahlil Gibran Al Zulmi
NRP: 5049221015
Institution: Institut Teknologi Sepuluh Nopember
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
from typing import List, Optional, Dict
import threading
import os

from modules.video_alignment import VideoAlignmentEngine, VideoInfo
from utils.localization import get_text
from utils.logger import get_logger

logger = get_logger(__name__)


class VideoAlignmentWizard:
    """
    Wizard for aligning multiple videos.
    """
    
    def __init__(self, parent, lang: str = 'en'):
        self.parent = parent
        self.lang = lang
        self.window = None
        self.engine = VideoAlignmentEngine()
        
        # Wizard state
        self.current_page = 0
        self.video_paths: List[str] = []
        self.video_captures: List[cv2.VideoCapture] = []
        self.current_frames: List[int] = []
        self.playing = False
        self.sync_method = tk.StringVar(value='manual')
        
        # UI components
        self.canvas_list: List[tk.Canvas] = []
        self.photo_images: List[ImageTk.PhotoImage] = []
        self.frame_sliders: List[ttk.Scale] = []
        self.time_labels: List[ttk.Label] = []
        
    def launch(self):
        """Launch the alignment wizard."""
        self.window = tk.Toplevel(self.parent)
        self.window.title(get_text("alignment.title", lang=self.lang))
        self.window.geometry("1200x800")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.window.winfo_screenheight() // 2) - (800 // 2)
        self.window.geometry(f"1200x800+{x}+{y}")
        
        # Make modal
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Create main container
        self.container = ttk.Frame(self.window, padding="10")
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Show first page
        self._show_page_load_videos()
        
    def _show_page_load_videos(self):
        """Page 1: Load multiple videos."""
        self._clear_container()
        
        # Title
        title = ttk.Label(
            self.container,
            text=get_text("alignment.load_videos", lang=self.lang),
            font=("Arial", 16, "bold")
        )
        title.pack(pady=10)
        
        # Instructions
        instructions = ttk.Label(
            self.container,
            text=get_text("alignment.load_instructions", lang=self.lang),
            wraplength=1100
        )
        instructions.pack(pady=5)
        
        # Video list frame
        list_frame = ttk.LabelFrame(
            self.container,
            text=get_text("alignment.video_list", lang=self.lang),
            padding="10"
        )
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create listbox with scrollbar
        scroll_frame = ttk.Frame(list_frame)
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(scroll_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.video_listbox = tk.Listbox(
            scroll_frame,
            yscrollcommand=scrollbar.set,
            height=15
        )
        self.video_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.video_listbox.yview)
        
        # Buttons frame
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            btn_frame,
            text=get_text("alignment.add_videos", lang=self.lang),
            command=self._add_videos
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text=get_text("alignment.remove_video", lang=self.lang),
            command=self._remove_video
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text=get_text("alignment.clear_all", lang=self.lang),
            command=self._clear_videos
        ).pack(side=tk.LEFT, padx=5)
        
        # Navigation buttons
        nav_frame = ttk.Frame(self.container)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        ttk.Button(
            nav_frame,
            text=get_text("button.cancel", lang=self.lang),
            command=self.window.destroy
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            nav_frame,
            text=get_text("button.next", lang=self.lang),
            command=self._on_videos_loaded
        ).pack(side=tk.RIGHT, padx=5)
        
    def _add_videos(self):
        """Add videos to list."""
        paths = filedialog.askopenfilenames(
            title=get_text("alignment.select_videos", lang=self.lang),
            filetypes=[
                (get_text("file.video_files", lang=self.lang), "*.mp4 *.avi *.mkv *.mov"),
                (get_text("file.all_files", lang=self.lang), "*.*")
            ]
        )
        
        for path in paths:
            if path not in self.video_paths:
                self.video_paths.append(path)
                filename = os.path.basename(path)
                self.video_listbox.insert(tk.END, filename)
                
    def _remove_video(self):
        """Remove selected video from list."""
        selection = self.video_listbox.curselection()
        if selection:
            idx = selection[0]
            self.video_listbox.delete(idx)
            del self.video_paths[idx]
            
    def _clear_videos(self):
        """Clear all videos."""
        self.video_listbox.delete(0, tk.END)
        self.video_paths.clear()
        
    def _on_videos_loaded(self):
        """Proceed to alignment method selection."""
        if len(self.video_paths) < 2:
            messagebox.showwarning(
                get_text("warning", lang=self.lang),
                get_text("alignment.need_two_videos", lang=self.lang)
            )
            return
        
        # Load videos into engine
        if not self.engine.load_videos(self.video_paths):
            messagebox.showerror(
                get_text("error", lang=self.lang),
                get_text("alignment.load_failed", lang=self.lang)
            )
            return
        
        # Initialize current frames
        self.current_frames = [0] * len(self.video_paths)
        
        # Open video captures for preview
        self.video_captures = [cv2.VideoCapture(path) for path in self.video_paths]
        
        self._show_page_select_method()
        
    def _show_page_select_method(self):
        """Page 2: Select alignment method."""
        self._clear_container()
        
        # Title
        title = ttk.Label(
            self.container,
            text=get_text("alignment.select_method", lang=self.lang),
            font=("Arial", 16, "bold")
        )
        title.pack(pady=10)
        
        # Method frame
        method_frame = ttk.LabelFrame(
            self.container,
            text=get_text("alignment.alignment_method", lang=self.lang),
            padding="20"
        )
        method_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Manual alignment
        manual_radio = ttk.Radiobutton(
            method_frame,
            text=get_text("alignment.manual_method", lang=self.lang),
            variable=self.sync_method,
            value='manual'
        )
        manual_radio.pack(anchor=tk.W, pady=5)
        
        manual_desc = ttk.Label(
            method_frame,
            text=get_text("alignment.manual_desc", lang=self.lang),
            wraplength=1000
        )
        manual_desc.pack(anchor=tk.W, padx=30, pady=2)
        
        # Flash synchronization
        flash_radio = ttk.Radiobutton(
            method_frame,
            text=get_text("alignment.flash_method", lang=self.lang),
            variable=self.sync_method,
            value='flash'
        )
        flash_radio.pack(anchor=tk.W, pady=5)
        
        flash_desc = ttk.Label(
            method_frame,
            text=get_text("alignment.flash_desc", lang=self.lang),
            wraplength=1000
        )
        flash_desc.pack(anchor=tk.W, padx=30, pady=2)
        
        # Audio synchronization
        audio_radio = ttk.Radiobutton(
            method_frame,
            text=get_text("alignment.audio_method", lang=self.lang),
            variable=self.sync_method,
            value='audio'
        )
        audio_radio.pack(anchor=tk.W, pady=5)
        
        audio_desc = ttk.Label(
            method_frame,
            text=get_text("alignment.audio_desc", lang=self.lang),
            wraplength=1000
        )
        audio_desc.pack(anchor=tk.W, padx=30, pady=2)
        
        # Motion synchronization
        motion_radio = ttk.Radiobutton(
            method_frame,
            text=get_text("alignment.motion_method", lang=self.lang),
            variable=self.sync_method,
            value='motion'
        )
        motion_radio.pack(anchor=tk.W, pady=5)
        
        motion_desc = ttk.Label(
            method_frame,
            text=get_text("alignment.motion_desc", lang=self.lang),
            wraplength=1000
        )
        motion_desc.pack(anchor=tk.W, padx=30, pady=2)
        
        # Navigation buttons
        nav_frame = ttk.Frame(self.container)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        ttk.Button(
            nav_frame,
            text=get_text("button.back", lang=self.lang),
            command=self._show_page_load_videos
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            nav_frame,
            text=get_text("button.next", lang=self.lang),
            command=self._on_method_selected
        ).pack(side=tk.RIGHT, padx=5)
        
    def _on_method_selected(self):
        """Proceed based on selected method."""
        method = self.sync_method.get()
        
        if method == 'manual':
            self._show_page_manual_alignment()
        else:
            self._perform_auto_alignment(method)
            
    def _perform_auto_alignment(self, method: str):
        """Perform automatic alignment."""
        # Show progress dialog
        progress_window = tk.Toplevel(self.window)
        progress_window.title(get_text("alignment.aligning", lang=self.lang))
        progress_window.geometry("400x150")
        progress_window.transient(self.window)
        progress_window.grab_set()
        
        ttk.Label(
            progress_window,
            text=get_text("alignment.auto_aligning", lang=self.lang),
            font=("Arial", 12)
        ).pack(pady=20)
        
        progress_bar = ttk.Progressbar(
            progress_window,
            mode='indeterminate'
        )
        progress_bar.pack(pady=10, padx=20, fill=tk.X)
        progress_bar.start()
        
        def align_thread():
            try:
                success = self.engine.auto_align(method)
                
                progress_window.after(0, lambda: progress_bar.stop())
                progress_window.after(0, lambda: progress_window.destroy())
                
                if success:
                    self.window.after(0, lambda: messagebox.showinfo(
                        get_text("success", lang=self.lang),
                        get_text("alignment.auto_success", lang=self.lang)
                    ))
                    self.window.after(0, self._show_page_review)
                else:
                    self.window.after(0, lambda: messagebox.showerror(
                        get_text("error", lang=self.lang),
                        get_text("alignment.auto_failed", lang=self.lang)
                    ))
                    self.window.after(0, self._show_page_manual_alignment)
                    
            except Exception as e:
                logger.error(f"Auto alignment error: {e}")
                progress_window.after(0, lambda: progress_bar.stop())
                progress_window.after(0, lambda: progress_window.destroy())
                self.window.after(0, lambda: messagebox.showerror(
                    get_text("error", lang=self.lang),
                    str(e)
                ))
        
        thread = threading.Thread(target=align_thread, daemon=True)
        thread.start()
        
    def _show_page_manual_alignment(self):
        """Page 3: Manual alignment with video previews."""
        self._clear_container()
        
        # Title
        title = ttk.Label(
            self.container,
            text=get_text("alignment.manual_alignment", lang=self.lang),
            font=("Arial", 16, "bold")
        )
        title.pack(pady=10)
        
        # Instructions
        instructions = ttk.Label(
            self.container,
            text=get_text("alignment.manual_instructions", lang=self.lang),
            wraplength=1100
        )
        instructions.pack(pady=5)
        
        # Video preview frame
        preview_frame = ttk.Frame(self.container)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create preview for each video
        num_videos = len(self.video_paths)
        cols = 2 if num_videos <= 4 else 3
        rows = (num_videos + cols - 1) // cols
        
        self.canvas_list = []
        self.frame_sliders = []
        self.time_labels = []
        
        for i, video_path in enumerate(self.video_paths):
            row = i // cols
            col = i % cols
            
            video_frame = ttk.LabelFrame(
                preview_frame,
                text=f"Video {i+1}: {os.path.basename(video_path)}",
                padding="5"
            )
            video_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # Canvas for video display
            canvas = tk.Canvas(video_frame, width=350, height=200, bg='black')
            canvas.pack()
            self.canvas_list.append(canvas)
            
            # Time label
            time_label = ttk.Label(video_frame, text="00:00:00 / 00:00:00")
            time_label.pack()
            self.time_labels.append(time_label)
            
            # Frame slider
            video_info = self.engine.videos[i]
            slider = ttk.Scale(
                video_frame,
                from_=0,
                to=video_info.frame_count - 1,
                orient=tk.HORIZONTAL,
                command=lambda val, idx=i: self._on_slider_change(idx, val)
            )
            slider.pack(fill=tk.X, pady=5)
            self.frame_sliders.append(slider)
        
        # Configure grid weights
        for i in range(cols):
            preview_frame.columnconfigure(i, weight=1)
        for i in range(rows):
            preview_frame.rowconfigure(i, weight=1)
        
        # Control buttons
        control_frame = ttk.Frame(self.container)
        control_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            control_frame,
            text="▶ " + get_text("alignment.play", lang=self.lang),
            command=self._toggle_play
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text=get_text("alignment.sync_here", lang=self.lang),
            command=self._mark_sync_point
        ).pack(side=tk.LEFT, padx=5)
        
        # Navigation buttons
        nav_frame = ttk.Frame(self.container)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        ttk.Button(
            nav_frame,
            text=get_text("button.back", lang=self.lang),
            command=self._show_page_select_method
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            nav_frame,
            text=get_text("button.next", lang=self.lang),
            command=self._on_manual_alignment_done
        ).pack(side=tk.RIGHT, padx=5)
        
        # Update initial frames
        self._update_all_frames()
        
    def _on_slider_change(self, video_idx: int, value):
        """Handle slider value change."""
        frame_num = int(float(value))
        self.current_frames[video_idx] = frame_num
        self._update_frame(video_idx)
        
    def _update_frame(self, video_idx: int):
        """Update single video frame display."""
        if video_idx >= len(self.video_captures):
            return
        
        cap = self.video_captures[video_idx]
        frame_num = self.current_frames[video_idx]
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        
        if ret:
            # Resize for display
            frame = cv2.resize(frame, (350, 200))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PhotoImage
            image = Image.fromarray(frame)
            photo = ImageTk.PhotoImage(image=image)
            
            # Update canvas
            canvas = self.canvas_list[video_idx]
            canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            
            # Keep reference
            if video_idx < len(self.photo_images):
                self.photo_images[video_idx] = photo
            else:
                self.photo_images.append(photo)
            
            # Update time label
            video_info = self.engine.videos[video_idx]
            current_time = frame_num / video_info.fps
            total_time = video_info.duration
            
            time_text = f"{self._format_time(current_time)} / {self._format_time(total_time)}"
            self.time_labels[video_idx].config(text=time_text)
            
    def _update_all_frames(self):
        """Update all video frames."""
        for i in range(len(self.video_paths)):
            self._update_frame(i)
            
    def _format_time(self, seconds: float) -> str:
        """Format time as HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        
    def _toggle_play(self):
        """Toggle playback of all videos."""
        self.playing = not self.playing
        if self.playing:
            self._play_videos()
            
    def _play_videos(self):
        """Play all videos synchronously."""
        if not self.playing:
            return
        
        # Advance all frames
        for i in range(len(self.video_paths)):
            self.current_frames[i] += 1
            video_info = self.engine.videos[i]
            
            if self.current_frames[i] >= video_info.frame_count:
                self.current_frames[i] = 0
                
            self.frame_sliders[i].set(self.current_frames[i])
        
        self._update_all_frames()
        
        # Schedule next frame
        fps = self.engine.videos[0].fps
        delay = int(1000 / fps)
        self.window.after(delay, self._play_videos)
        
    def _mark_sync_point(self):
        """Mark current frames as synchronization point."""
        self.engine.add_alignment_point(
            video_indices=list(range(len(self.video_paths))),
            frame_numbers=self.current_frames.copy(),
            event_type='manual'
        )
        
        messagebox.showinfo(
            get_text("success", lang=self.lang),
            get_text("alignment.sync_point_added", lang=self.lang)
        )
        
    def _on_manual_alignment_done(self):
        """Finish manual alignment."""
        if not self.engine.alignment_points:
            messagebox.showwarning(
                get_text("warning", lang=self.lang),
                get_text("alignment.need_sync_point", lang=self.lang)
            )
            return
        
        # Calculate offsets
        self.engine.calculate_time_offsets()
        self._show_page_review()
        
    def _show_page_review(self):
        """Page 4: Review and export."""
        self._clear_container()
        
        # Stop playback
        self.playing = False
        
        # Title
        title = ttk.Label(
            self.container,
            text=get_text("alignment.review", lang=self.lang),
            font=("Arial", 16, "bold")
        )
        title.pack(pady=10)
        
        # Alignment info
        info_frame = ttk.LabelFrame(
            self.container,
            text=get_text("alignment.alignment_info", lang=self.lang),
            padding="10"
        )
        info_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Display time offsets
        ttk.Label(
            info_frame,
            text=get_text("alignment.time_offsets", lang=self.lang),
            font=("Arial", 12, "bold")
        ).pack(anchor=tk.W, pady=5)
        
        for i, offset in enumerate(self.engine.time_offsets):
            video_name = os.path.basename(self.video_paths[i])
            offset_text = f"Video {i+1} ({video_name}): {offset:.3f}s"
            ttk.Label(info_frame, text=offset_text).pack(anchor=tk.W, padx=20)
        
        # Export options
        export_frame = ttk.LabelFrame(
            self.container,
            text=get_text("alignment.export_options", lang=self.lang),
            padding="10"
        )
        export_frame.pack(fill=tk.X, pady=10)
        
        # Layout selection
        ttk.Label(
            export_frame,
            text=get_text("alignment.layout", lang=self.lang)
        ).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.layout_var = tk.StringVar(value='grid')
        layout_combo = ttk.Combobox(
            export_frame,
            textvariable=self.layout_var,
            values=['grid', 'horizontal', 'vertical'],
            state='readonly'
        )
        layout_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Export buttons
        button_frame = ttk.Frame(export_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(
            button_frame,
            text=get_text("alignment.export_video", lang=self.lang),
            command=self._export_aligned_video
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text=get_text("alignment.save_alignment", lang=self.lang),
            command=self._save_alignment
        ).pack(side=tk.LEFT, padx=5)
        
        # Navigation buttons
        nav_frame = ttk.Frame(self.container)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        ttk.Button(
            nav_frame,
            text=get_text("button.back", lang=self.lang),
            command=self._show_page_manual_alignment
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            nav_frame,
            text=get_text("button.finish", lang=self.lang),
            command=self._finish
        ).pack(side=tk.RIGHT, padx=5)
        
    def _export_aligned_video(self):
        """Export aligned videos as composite."""
        output_dir = filedialog.askdirectory(
            title=get_text("alignment.select_output", lang=self.lang)
        )
        
        if not output_dir:
            return
        
        layout = self.layout_var.get()
        
        # Show progress
        progress_window = tk.Toplevel(self.window)
        progress_window.title(get_text("alignment.exporting", lang=self.lang))
        progress_window.geometry("400x150")
        progress_window.transient(self.window)
        progress_window.grab_set()
        
        ttk.Label(
            progress_window,
            text=get_text("alignment.export_progress", lang=self.lang),
            font=("Arial", 12)
        ).pack(pady=20)
        
        progress_bar = ttk.Progressbar(
            progress_window,
            mode='indeterminate'
        )
        progress_bar.pack(pady=10, padx=20, fill=tk.X)
        progress_bar.start()
        
        def export_thread():
            try:
                output_path = self.engine.export_aligned_videos(
                    output_dir=output_dir,
                    layout=layout
                )
                
                progress_window.after(0, lambda: progress_bar.stop())
                progress_window.after(0, lambda: progress_window.destroy())
                
                if output_path:
                    self.window.after(0, lambda: messagebox.showinfo(
                        get_text("success", lang=self.lang),
                        f"{get_text('alignment.export_success', lang=self.lang)}\n{output_path}"
                    ))
                else:
                    self.window.after(0, lambda: messagebox.showerror(
                        get_text("error", lang=self.lang),
                        get_text("alignment.export_failed", lang=self.lang)
                    ))
                    
            except Exception as e:
                logger.error(f"Export error: {e}")
                progress_window.after(0, lambda: progress_bar.stop())
                progress_window.after(0, lambda: progress_window.destroy())
                self.window.after(0, lambda: messagebox.showerror(
                    get_text("error", lang=self.lang),
                    str(e)
                ))
        
        thread = threading.Thread(target=export_thread, daemon=True)
        thread.start()
        
    def _save_alignment(self):
        """Save alignment configuration."""
        output_path = filedialog.asksaveasfilename(
            title=get_text("alignment.save_config", lang=self.lang),
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if output_path:
            if self.engine.save_alignment(output_path):
                messagebox.showinfo(
                    get_text("success", lang=self.lang),
                    get_text("alignment.save_success", lang=self.lang)
                )
            else:
                messagebox.showerror(
                    get_text("error", lang=self.lang),
                    get_text("alignment.save_failed", lang=self.lang)
                )
                
    def _finish(self):
        """Close wizard."""
        # Release video captures
        for cap in self.video_captures:
            if cap.isOpened():
                cap.release()
        
        self.window.destroy()
        
    def _clear_container(self):
        """Clear all widgets from container."""
        for widget in self.container.winfo_children():
            widget.destroy()
