"""
Stimulus Wizard Module

This module provides a Tkinter-based wizard interface for configuring and generating
eye tracking stimulus videos.

Author: Kahlil Gibran Al Zulmi
Institution: Institut Teknologi Sepuluh Nopember
Date: November 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
from datetime import datetime
from typing import Dict, Any, Optional

from utils.logger import log_info, log_warning, log_error
from utils.config_manager import load_config, save_config
from utils.localization import get_text
from modules.stimulus_generator import (
    get_default_protocols,
    generate_stimulus_video
)


# ============================================================================
# STIMULUS WIZARD CLASS
# ============================================================================

class StimulusWizard:
    """Wizard for configuring and generating stimulus videos."""
    
    def __init__(self, parent):
        """
        Initialize stimulus wizard.
        
        Args:
            parent: Parent Tkinter window
        """
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title(get_text("stimulus.title"))
        self.window.geometry("800x700")
        self.window.resizable(False, False)
        
        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.window.winfo_screenheight() // 2) - (700 // 2)
        self.window.geometry(f"800x700+{x}+{y}")
        
        # Load configuration
        self.config = load_config()
        
        # Initialize variables
        self.selected_protocol = tk.StringVar(value="standard")
        self.output_directory = tk.StringVar(value=os.path.join(os.getcwd(), "stimulus_videos"))
        self.output_filename = tk.StringVar(value=f"stimulus_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
        
        # Protocol settings
        self.protocols = get_default_protocols()
        self.current_protocol = self.protocols["standard"].copy()
        
        # Create UI
        self.create_ui()
        
        log_info("Stimulus wizard opened")
    
    def create_ui(self):
        """Create wizard user interface."""
        # Title
        title_frame = ttk.Frame(self.window)
        title_frame.pack(fill=tk.X, padx=20, pady=10)
        
        title_label = ttk.Label(
            title_frame,
            text=get_text("stimulus.title"),
            font=("Arial", 16, "bold")
        )
        title_label.pack(anchor=tk.W)
        
        desc_label = ttk.Label(
            title_frame,
            text=get_text("stimulus.description"),
            font=("Arial", 10)
        )
        desc_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Separator
        ttk.Separator(self.window, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=10)
        
        # Main content with tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Tab 1: Protocol Selection
        self.protocol_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.protocol_tab, text=get_text("stimulus.select_protocol"))
        self.create_protocol_tab()
        
        # Tab 2: Settings
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text=get_text("common.settings"))
        self.create_settings_tab()
        
        # Tab 3: Tasks
        self.tasks_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.tasks_tab, text="Tasks")
        self.create_tasks_tab()
        
        # Bottom buttons
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.generate_btn = ttk.Button(
            button_frame,
            text=get_text("stimulus.generate_video"),
            command=self.generate_video,
            style="Accent.TButton"
        )
        self.generate_btn.pack(side=tk.RIGHT, padx=5)
        
        cancel_btn = ttk.Button(
            button_frame,
            text=get_text("common.cancel"),
            command=self.cancel
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)
    
    def create_protocol_tab(self):
        """Create protocol selection tab."""
        # Protocol selection
        protocol_frame = ttk.LabelFrame(self.protocol_tab, text=get_text("stimulus.select_protocol"))
        protocol_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        for protocol_key, protocol_data in self.protocols.items():
            rb = ttk.Radiobutton(
                protocol_frame,
                text=protocol_data['name'],
                variable=self.selected_protocol,
                value=protocol_key,
                command=self.on_protocol_changed
            )
            rb.pack(anchor=tk.W, padx=20, pady=5)
            
            # Description
            desc_label = ttk.Label(
                protocol_frame,
                text=f"  {protocol_data['description']}",
                font=("Arial", 9),
                foreground="gray"
            )
            desc_label.pack(anchor=tk.W, padx=40, pady=(0, 10))
        
        # Protocol details
        details_frame = ttk.LabelFrame(self.protocol_tab, text="Protocol Details")
        details_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(details_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.details_text = tk.Text(
            text_frame,
            height=10,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            font=("Courier", 9)
        )
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.details_text.yview)
        
        # Update details
        self.update_protocol_details()
    
    def create_settings_tab(self):
        """Create settings tab."""
        # Output settings
        output_frame = ttk.LabelFrame(self.settings_tab, text="Output Settings")
        output_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Output directory
        dir_frame = ttk.Frame(output_frame)
        dir_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(dir_frame, text="Output Directory:").pack(anchor=tk.W)
        
        dir_entry_frame = ttk.Frame(dir_frame)
        dir_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Entry(
            dir_entry_frame,
            textvariable=self.output_directory,
            width=50
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            dir_entry_frame,
            text=get_text("common.browse"),
            command=self.browse_output_directory
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Output filename
        filename_frame = ttk.Frame(output_frame)
        filename_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(filename_frame, text="Output Filename:").pack(anchor=tk.W)
        
        ttk.Entry(
            filename_frame,
            textvariable=self.output_filename,
            width=50
        ).pack(fill=tk.X, pady=(5, 0))
        
        # Video settings
        video_frame = ttk.LabelFrame(self.settings_tab, text="Video Settings")
        video_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        settings = self.current_protocol.get('settings', {})
        
        # Resolution
        res_frame = ttk.Frame(video_frame)
        res_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(res_frame, text="Resolution:").pack(side=tk.LEFT)
        
        self.width_var = tk.IntVar(value=settings.get('width', 1920))
        self.height_var = tk.IntVar(value=settings.get('height', 1080))
        
        ttk.Spinbox(
            res_frame,
            from_=640,
            to=3840,
            textvariable=self.width_var,
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(res_frame, text="×").pack(side=tk.LEFT)
        
        ttk.Spinbox(
            res_frame,
            from_=480,
            to=2160,
            textvariable=self.height_var,
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        # FPS
        fps_frame = ttk.Frame(video_frame)
        fps_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(fps_frame, text="FPS:").pack(side=tk.LEFT)
        
        self.fps_var = tk.IntVar(value=settings.get('fps', 60))
        
        ttk.Spinbox(
            fps_frame,
            from_=30,
            to=120,
            textvariable=self.fps_var,
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        # Colors
        color_frame = ttk.LabelFrame(self.settings_tab, text="Colors")
        color_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        ttk.Label(
            color_frame,
            text="Background: Black, Target: White, Text: White",
            font=("Arial", 9)
        ).pack(padx=10, pady=10)
    
    def create_tasks_tab(self):
        """Create tasks overview tab."""
        # Tasks list
        list_frame = ttk.Frame(self.tasks_tab)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(
            list_frame,
            text="Task Sequence:",
            font=("Arial", 11, "bold")
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Create treeview for tasks
        columns = ("Task", "Type", "Duration")
        self.tasks_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=15
        )
        
        for col in columns:
            self.tasks_tree.heading(col, text=col)
            if col == "Task":
                self.tasks_tree.column(col, width=50)
            elif col == "Type":
                self.tasks_tree.column(col, width=300)
            else:
                self.tasks_tree.column(col, width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=scrollbar.set)
        
        self.tasks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Summary
        summary_frame = ttk.Frame(self.tasks_tab)
        summary_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        self.summary_label = ttk.Label(
            summary_frame,
            text="",
            font=("Arial", 10, "bold")
        )
        self.summary_label.pack(anchor=tk.W)
        
        # Update tasks
        self.update_tasks_list()
    
    def on_protocol_changed(self):
        """Handle protocol selection change."""
        protocol_key = self.selected_protocol.get()
        self.current_protocol = self.protocols[protocol_key].copy()
        
        # Update settings
        settings = self.current_protocol.get('settings', {})
        self.width_var.set(settings.get('width', 1920))
        self.height_var.set(settings.get('height', 1080))
        self.fps_var.set(settings.get('fps', 60))
        
        # Update details and tasks
        self.update_protocol_details()
        self.update_tasks_list()
        
        log_info(f"Protocol changed to: {protocol_key}")
    
    def update_protocol_details(self):
        """Update protocol details text."""
        protocol_key = self.selected_protocol.get()
        protocol = self.protocols[protocol_key]
        
        self.details_text.delete(1.0, tk.END)
        
        details = f"Protocol: {protocol['name']}\n"
        details += f"Description: {protocol['description']}\n\n"
        
        settings = protocol.get('settings', {})
        details += f"Resolution: {settings.get('width', 1920)}×{settings.get('height', 1080)}\n"
        details += f"FPS: {settings.get('fps', 60)}\n"
        details += f"Margin: {settings.get('margin', 150)} px\n"
        details += f"Command Duration: {settings.get('command_duration', 3)} s\n"
        details += f"Prepare Duration: {settings.get('prepare_duration', 3)} s\n\n"
        
        tasks = protocol.get('tasks', [])
        details += f"Total Tasks: {len(tasks)}\n"
        
        # Calculate total duration
        total_duration = 0
        for task in tasks:
            duration = task.get('duration', 0)
            total_duration += duration
            
            # Add command duration for most tasks
            if task['type'] not in ['opening', 'closing']:
                total_duration += settings.get('command_duration', 3)
            
            # Add prepare duration for smooth pursuit tasks
            if 'smooth_' in task['type']:
                total_duration += settings.get('prepare_duration', 3)
        
        details += f"Estimated Duration: {total_duration // 60} min {total_duration % 60} sec\n"
        
        self.details_text.insert(1.0, details)
        self.details_text.config(state=tk.DISABLED)
    
    def update_tasks_list(self):
        """Update tasks list in treeview."""
        # Clear existing items
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
        
        # Add tasks
        tasks = self.current_protocol.get('tasks', [])
        for idx, task in enumerate(tasks, 1):
            task_type = task.get('type', 'unknown')
            duration = task.get('duration', 0)
            
            # Format task type
            type_display = task_type.replace('_', ' ').title()
            
            self.tasks_tree.insert(
                '',
                tk.END,
                values=(f"#{idx}", type_display, f"{duration}s")
            )
        
        # Update summary
        settings = self.current_protocol.get('settings', {})
        total_duration = 0
        for task in tasks:
            duration = task.get('duration', 0)
            total_duration += duration
            if task['type'] not in ['opening', 'closing']:
                total_duration += settings.get('command_duration', 3)
            if 'smooth_' in task['type']:
                total_duration += settings.get('prepare_duration', 3)
        
        self.summary_label.config(
            text=f"Total: {len(tasks)} tasks, ~{total_duration // 60}:{total_duration % 60:02d} duration"
        )
    
    def browse_output_directory(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.output_directory.get()
        )
        
        if directory:
            self.output_directory.set(directory)
    
    def generate_video(self):
        """Generate stimulus video."""
        try:
            # Validate inputs
            output_dir = self.output_directory.get()
            output_file = self.output_filename.get()
            
            if not output_file:
                messagebox.showerror(
                    get_text("common.error"),
                    "Please enter an output filename."
                )
                return
            
            if not output_file.endswith('.mp4'):
                output_file += '.mp4'
            
            # Create output directory if needed
            os.makedirs(output_dir, exist_ok=True)
            
            output_path = os.path.join(output_dir, output_file)
            
            # Check if file exists
            if os.path.exists(output_path):
                if not messagebox.askyesno(
                    get_text("common.warning"),
                    f"File '{output_file}' already exists. Overwrite?"
                ):
                    return
            
            # Update protocol settings
            self.current_protocol['settings']['width'] = self.width_var.get()
            self.current_protocol['settings']['height'] = self.height_var.get()
            self.current_protocol['settings']['fps'] = self.fps_var.get()
            
            # Disable generate button
            self.generate_btn.config(state=tk.DISABLED)
            
            # Create progress window
            self.create_progress_window()
            
            # Start generation in background thread
            thread = threading.Thread(
                target=self.generate_video_thread,
                args=(output_path,),
                daemon=True
            )
            thread.start()
            
        except Exception as e:
            log_error(f"Error starting video generation: {str(e)}")
            messagebox.showerror(
                get_text("common.error"),
                f"Error: {str(e)}"
            )
            self.generate_btn.config(state=tk.NORMAL)
    
    def create_progress_window(self):
        """Create progress dialog."""
        self.progress_window = tk.Toplevel(self.window)
        self.progress_window.title("Generating Video...")
        self.progress_window.geometry("400x150")
        self.progress_window.resizable(False, False)
        self.progress_window.transient(self.window)
        
        # Center window
        self.progress_window.update_idletasks()
        x = (self.progress_window.winfo_screenwidth() // 2) - 200
        y = (self.progress_window.winfo_screenheight() // 2) - 75
        self.progress_window.geometry(f"400x150+{x}+{y}")
        
        # Progress label
        self.progress_label = ttk.Label(
            self.progress_window,
            text="Initializing...",
            font=("Arial", 10)
        )
        self.progress_label.pack(pady=(20, 10))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.progress_window,
            mode='determinate',
            length=350
        )
        self.progress_bar.pack(pady=10)
        
        # Status label
        self.status_label = ttk.Label(
            self.progress_window,
            text="",
            font=("Arial", 9),
            foreground="gray"
        )
        self.status_label.pack(pady=(0, 20))
    
    def update_progress(self, current: int, total: int, message: str):
        """Update progress display."""
        if hasattr(self, 'progress_window') and self.progress_window.winfo_exists():
            progress = (current / total) * 100 if total > 0 else 0
            self.progress_bar['value'] = progress
            self.progress_label.config(text=f"Task {current}/{total}")
            self.status_label.config(text=message)
            self.progress_window.update()
    
    def generate_video_thread(self, output_path: str):
        """Background thread for video generation."""
        try:
            log_info(f"Starting video generation: {output_path}")
            
            # Generate video with progress callback
            result = generate_stimulus_video(
                self.current_protocol,
                output_path,
                progress_callback=self.update_progress
            )
            
            # Close progress window
            if hasattr(self, 'progress_window') and self.progress_window.winfo_exists():
                self.progress_window.destroy()
            
            # Show result
            if result.get('success'):
                duration = result.get('duration', 0)
                file_size = result.get('file_size_mb', 0)
                gen_time = result.get('generation_time', 0)
                
                message = f"Video generated successfully!\n\n"
                message += f"Output: {output_path}\n"
                message += f"Duration: {duration:.1f} seconds\n"
                message += f"Size: {file_size:.2f} MB\n"
                message += f"Generation time: {gen_time:.1f} seconds"
                
                self.window.after(0, lambda: messagebox.showinfo(
                    get_text("common.success"),
                    message
                ))
                
                log_info(f"Video generation successful: {output_path}")
                
                # Ask if user wants to open folder
                self.window.after(0, lambda: self.ask_open_folder(output_path))
            else:
                error_msg = result.get('error', 'Unknown error')
                self.window.after(0, lambda: messagebox.showerror(
                    get_text("common.error"),
                    f"Video generation failed:\n{error_msg}"
                ))
                log_error(f"Video generation failed: {error_msg}")
            
        except Exception as e:
            log_error(f"Error in video generation thread: {str(e)}")
            if hasattr(self, 'progress_window') and self.progress_window.winfo_exists():
                self.progress_window.destroy()
            self.window.after(0, lambda: messagebox.showerror(
                get_text("common.error"),
                f"Error generating video:\n{str(e)}"
            ))
        finally:
            # Re-enable generate button
            self.window.after(0, lambda: self.generate_btn.config(state=tk.NORMAL))
    
    def ask_open_folder(self, output_path: str):
        """Ask if user wants to open output folder."""
        if messagebox.askyesno(
            get_text("common.success"),
            "Video generated successfully!\n\nOpen output folder?"
        ):
            # Open folder in file explorer
            import subprocess
            output_dir = os.path.dirname(output_path)
            if os.name == 'nt':  # Windows
                os.startfile(output_dir)
            elif os.name == 'posix':  # Linux/Mac
                subprocess.Popen(['xdg-open', output_dir])
    
    def cancel(self):
        """Cancel and close wizard."""
        if messagebox.askyesno(
            get_text("common.warning"),
            get_text("wizard.confirm_cancel")
        ):
            self.window.destroy()
            log_info("Stimulus wizard cancelled")


# ============================================================================
# LAUNCHER FUNCTION
# ============================================================================

def launch_stimulus_wizard(parent):
    """
    Launch the stimulus configuration wizard.
    
    Args:
        parent: Parent Tkinter window
    """
    wizard = StimulusWizard(parent)
    return wizard


if __name__ == "__main__":
    # Test code
    root = tk.Tk()
    root.withdraw()
    launch_stimulus_wizard(root)
    root.mainloop()
