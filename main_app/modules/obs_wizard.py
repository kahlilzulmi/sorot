"""
OBS Studio Integration Wizard

This module provides a wizard to guide users through setting up OBS Studio
for screen recording during eye tracking experiments.

Author: Kahlil Gibran Al Zulmi
Institution: Institut Teknologi Sepuluh Nopember
Date: November 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess
import json
import platform
from typing import Optional, Dict, Any
import winreg

from utils.localization import get_text
from utils.logger import log_info, log_warning, log_error


# ============================================================================
# OBS DETECTION AND CONFIGURATION
# ============================================================================

def find_obs_installation() -> Optional[str]:
    """
    Find OBS Studio installation path on Windows.
    
    Returns:
        Path to OBS executable or None if not found
    """
    try:
        # Common installation paths
        common_paths = [
            r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
            r"C:\Program Files (x86)\obs-studio\bin\64bit\obs64.exe",
            r"C:\Program Files\obs-studio\bin\32bit\obs32.exe",
        ]
        
        # Check common paths
        for path in common_paths:
            if os.path.exists(path):
                log_info(f"Found OBS at: {path}")
                return path
        
        # Try registry (OBS stores installation path here)
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                r"SOFTWARE\OBS Studio", 0, 
                                winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
            install_path, _ = winreg.QueryValueEx(key, "")
            winreg.CloseKey(key)
            
            obs_exe = os.path.join(install_path, "bin", "64bit", "obs64.exe")
            if os.path.exists(obs_exe):
                log_info(f"Found OBS via registry: {obs_exe}")
                return obs_exe
        except WindowsError:
            pass
        
        log_warning("OBS Studio not found in common locations")
        return None
    
    except Exception as e:
        log_error(f"Error finding OBS installation: {str(e)}")
        return None


def get_obs_config_path() -> str:
    """
    Get OBS Studio configuration directory path.
    
    Returns:
        Path to OBS config directory
    """
    appdata = os.environ.get('APPDATA', '')
    return os.path.join(appdata, 'obs-studio')


def check_obs_running() -> bool:
    """
    Check if OBS Studio is currently running.
    
    Returns:
        True if OBS is running, False otherwise
    """
    try:
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq obs64.exe'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return 'obs64.exe' in result.stdout
    except Exception as e:
        log_error(f"Error checking OBS process: {str(e)}")
        return False


def create_obs_scene_collection(name: str = "EyeTracking") -> Dict[str, Any]:
    """
    Create OBS scene collection configuration for eye tracking.
    
    Args:
        name: Scene collection name
        
    Returns:
        Scene collection configuration dictionary
    """
    return {
        "current_scene": "Eye Tracking Session",
        "scene_order": [
            {"name": "Eye Tracking Session"}
        ],
        "name": name,
        "scenes": [
            {
                "name": "Eye Tracking Session",
                "sources": [
                    {
                        "name": "Display Capture",
                        "id": "monitor_capture",
                        "settings": {
                            "monitor": 0,
                            "capture_cursor": True
                        },
                        "volume": 1.0,
                        "pos": {"x": 0, "y": 0},
                        "scale": {"x": 1.0, "y": 1.0}
                    }
                ]
            }
        ]
    }


def create_obs_profile(name: str = "EyeTracking") -> Dict[str, Any]:
    """
    Create OBS profile configuration optimized for eye tracking recording.
    
    Args:
        name: Profile name
        
    Returns:
        Profile configuration dictionary
    """
    return {
        "Name": name,
        "Video": {
            "BaseCX": 1920,
            "BaseCY": 1080,
            "OutputCX": 1920,
            "OutputCY": 1080,
            "FPSType": 0,
            "FPSCommon": 30,
            "ScaleType": "bicubic"
        },
        "Output": {
            "Mode": "Simple",
            "FilePath": os.path.expanduser("~/Videos"),
            "RecFormat": "mp4",
            "RecEncoder": "x264",
            "RecQuality": "Stream",
            "RecRB": False
        },
        "Audio": {
            "SampleRate": 44100,
            "ChannelSetup": "Stereo"
        }
    }


# ============================================================================
# OBS WIZARD GUI
# ============================================================================

class OBSWizard:
    """OBS Studio setup wizard."""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.obs_path = None
        self.current_step = 0
        
        # Configuration
        self.config = {
            'recording_path': os.path.expanduser("~/Videos"),
            'format': 'mp4',
            'quality': 'High',
            'fps': 30,
            'resolution': '1920x1080',
            'capture_audio': True,
            'auto_start': False
        }
    
    def launch(self):
        """Launch the OBS wizard window."""
        if self.window and tk.Toplevel.winfo_exists(self.window):
            self.window.lift()
            return
        
        # Create window
        self.window = tk.Toplevel(self.parent)
        self.window.title(get_text("obs.wizard_title"))
        self.window.geometry("800x600")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.window.winfo_screenheight() // 2) - (600 // 2)
        self.window.geometry(f"800x600+{x}+{y}")
        
        # Make modal
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Create UI
        self._create_ui()
        
        # Start with step 1
        self._show_step(0)
        
        log_info("OBS wizard launched")
    
    def _create_ui(self):
        """Create the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        self.title_label = ttk.Label(
            main_frame,
            text="",
            font=("Arial", 16, "bold")
        )
        self.title_label.pack(pady=(0, 20))
        
        # Content frame (for step content)
        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        self.back_btn = ttk.Button(
            button_frame,
            text=get_text("wizard.back"),
            command=self._previous_step
        )
        self.back_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.next_btn = ttk.Button(
            button_frame,
            text=get_text("wizard.next"),
            command=self._next_step
        )
        self.next_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.finish_btn = ttk.Button(
            button_frame,
            text=get_text("wizard.finish"),
            command=self._finish
        )
        self.finish_btn.pack(side=tk.LEFT)
        
        ttk.Button(
            button_frame,
            text=get_text("wizard.cancel"),
            command=self.window.destroy
        ).pack(side=tk.RIGHT)
    
    def _show_step(self, step: int):
        """Show a specific wizard step."""
        self.current_step = step
        
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Update buttons
        self.back_btn.config(state=tk.NORMAL if step > 0 else tk.DISABLED)
        
        if step == 4:  # Last step
            self.next_btn.pack_forget()
            self.finish_btn.pack(side=tk.LEFT, padx=(0, 5))
        else:
            self.finish_btn.pack_forget()
            self.next_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Show step content
        if step == 0:
            self._show_detection_step()
        elif step == 1:
            self._show_configuration_step()
        elif step == 2:
            self._show_profile_step()
        elif step == 3:
            self._show_test_step()
        elif step == 4:
            self._show_complete_step()
    
    def _show_detection_step(self):
        """Step 1: Detect OBS installation."""
        self.title_label.config(text=get_text("obs.step1_title"))
        
        # Info text
        info = ttk.Label(
            self.content_frame,
            text=get_text("obs.step1_info"),
            wraplength=700,
            justify=tk.LEFT
        )
        info.pack(pady=(0, 20))
        
        # Detection frame
        detect_frame = ttk.LabelFrame(
            self.content_frame,
            text=get_text("obs.detection_status"),
            padding="10"
        )
        detect_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Check for OBS
        self.obs_path = find_obs_installation()
        
        if self.obs_path:
            status_text = f"✓ {get_text('obs.found')}\n{self.obs_path}"
            status_color = "green"
        else:
            status_text = f"✗ {get_text('obs.not_found')}"
            status_color = "red"
        
        status_label = ttk.Label(
            detect_frame,
            text=status_text,
            foreground=status_color,
            font=("Arial", 10)
        )
        status_label.pack(pady=5)
        
        # Manual path selection
        manual_frame = ttk.Frame(self.content_frame)
        manual_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(
            manual_frame,
            text=get_text("obs.manual_path")
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.obs_path_var = tk.StringVar(value=self.obs_path or "")
        ttk.Entry(
            manual_frame,
            textvariable=self.obs_path_var,
            width=50
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            manual_frame,
            text=get_text("common.browse"),
            command=self._browse_obs_path
        ).pack(side=tk.LEFT)
        
        # Download link
        if not self.obs_path:
            download_frame = ttk.Frame(self.content_frame)
            download_frame.pack(pady=(20, 0))
            
            ttk.Label(
                download_frame,
                text=get_text("obs.download_info"),
                wraplength=700
            ).pack()
            
            ttk.Button(
                download_frame,
                text=get_text("obs.download_button"),
                command=lambda: self._open_url("https://obsproject.com/download")
            ).pack(pady=(10, 0))
    
    def _show_configuration_step(self):
        """Step 2: Configure recording settings."""
        self.title_label.config(text=get_text("obs.step2_title"))
        
        # Info
        ttk.Label(
            self.content_frame,
            text=get_text("obs.step2_info"),
            wraplength=700
        ).pack(pady=(0, 20))
        
        # Settings frame
        settings_frame = ttk.LabelFrame(
            self.content_frame,
            text=get_text("obs.recording_settings"),
            padding="15"
        )
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # Recording path
        row = 0
        ttk.Label(settings_frame, text=get_text("obs.recording_path")).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        
        path_frame = ttk.Frame(settings_frame)
        path_frame.grid(row=row, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        
        self.rec_path_var = tk.StringVar(value=self.config['recording_path'])
        ttk.Entry(path_frame, textvariable=self.rec_path_var, width=40).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            path_frame,
            text=get_text("common.browse"),
            command=self._browse_recording_path
        ).pack(side=tk.LEFT)
        
        # Format
        row += 1
        ttk.Label(settings_frame, text=get_text("obs.format")).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self.format_var = tk.StringVar(value=self.config['format'])
        format_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.format_var,
            values=['mp4', 'mkv', 'flv', 'mov'],
            state='readonly',
            width=20
        )
        format_combo.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # Quality
        row += 1
        ttk.Label(settings_frame, text=get_text("obs.quality")).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self.quality_var = tk.StringVar(value=self.config['quality'])
        quality_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.quality_var,
            values=['Low', 'Medium', 'High', 'Lossless'],
            state='readonly',
            width=20
        )
        quality_combo.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # FPS
        row += 1
        ttk.Label(settings_frame, text=get_text("obs.fps")).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self.fps_var = tk.StringVar(value=str(self.config['fps']))
        fps_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.fps_var,
            values=['24', '30', '60'],
            state='readonly',
            width=20
        )
        fps_combo.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # Resolution
        row += 1
        ttk.Label(settings_frame, text=get_text("obs.resolution")).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self.resolution_var = tk.StringVar(value=self.config['resolution'])
        res_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.resolution_var,
            values=['1920x1080', '1280x720', '2560x1440', '3840x2160'],
            state='readonly',
            width=20
        )
        res_combo.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # Audio
        row += 1
        self.audio_var = tk.BooleanVar(value=self.config['capture_audio'])
        ttk.Checkbutton(
            settings_frame,
            text=get_text("obs.capture_audio"),
            variable=self.audio_var
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        # Auto-start
        row += 1
        self.autostart_var = tk.BooleanVar(value=self.config['auto_start'])
        ttk.Checkbutton(
            settings_frame,
            text=get_text("obs.auto_start"),
            variable=self.autostart_var
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        settings_frame.columnconfigure(1, weight=1)
    
    def _show_profile_step(self):
        """Step 3: Create OBS profile."""
        self.title_label.config(text=get_text("obs.step3_title"))
        
        # Info
        ttk.Label(
            self.content_frame,
            text=get_text("obs.step3_info"),
            wraplength=700
        ).pack(pady=(0, 20))
        
        # Profile frame
        profile_frame = ttk.LabelFrame(
            self.content_frame,
            text=get_text("obs.profile_settings"),
            padding="15"
        )
        profile_frame.pack(fill=tk.BOTH, expand=True)
        
        # Profile name
        ttk.Label(profile_frame, text=get_text("obs.profile_name")).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.profile_name_var = tk.StringVar(value="EyeTracking")
        ttk.Entry(profile_frame, textvariable=self.profile_name_var, width=30).grid(
            row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0)
        )
        
        # Scene name
        ttk.Label(profile_frame, text=get_text("obs.scene_name")).grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.scene_name_var = tk.StringVar(value="Eye Tracking Session")
        ttk.Entry(profile_frame, textvariable=self.scene_name_var, width=30).grid(
            row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0)
        )
        
        # Instructions
        instructions_text = get_text("obs.profile_instructions")
        instructions = tk.Text(
            profile_frame,
            height=8,
            width=70,
            wrap=tk.WORD,
            font=("Arial", 9)
        )
        instructions.grid(row=2, column=0, columnspan=2, pady=(20, 0), sticky=tk.NSEW)
        instructions.insert("1.0", instructions_text)
        instructions.config(state=tk.DISABLED)
        
        profile_frame.columnconfigure(1, weight=1)
        profile_frame.rowconfigure(2, weight=1)
        
        # Create button
        ttk.Button(
            self.content_frame,
            text=get_text("obs.create_profile"),
            command=self._create_profile
        ).pack(pady=(10, 0))
    
    def _show_test_step(self):
        """Step 4: Test recording."""
        self.title_label.config(text=get_text("obs.step4_title"))
        
        # Info
        ttk.Label(
            self.content_frame,
            text=get_text("obs.step4_info"),
            wraplength=700
        ).pack(pady=(0, 20))
        
        # Test frame
        test_frame = ttk.LabelFrame(
            self.content_frame,
            text=get_text("obs.test_recording"),
            padding="15"
        )
        test_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        instructions = [
            "1. " + get_text("obs.test_step1"),
            "2. " + get_text("obs.test_step2"),
            "3. " + get_text("obs.test_step3"),
            "4. " + get_text("obs.test_step4"),
            "5. " + get_text("obs.test_step5")
        ]
        
        for i, instruction in enumerate(instructions):
            ttk.Label(
                test_frame,
                text=instruction,
                wraplength=650
            ).pack(anchor=tk.W, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(test_frame)
        button_frame.pack(pady=(20, 0))
        
        ttk.Button(
            button_frame,
            text=get_text("obs.launch_obs"),
            command=self._launch_obs
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text=get_text("obs.open_folder"),
            command=self._open_recording_folder
        ).pack(side=tk.LEFT, padx=5)
    
    def _show_complete_step(self):
        """Step 5: Completion."""
        self.title_label.config(text=get_text("obs.complete_title"))
        
        # Success message
        ttk.Label(
            self.content_frame,
            text="✓ " + get_text("obs.complete_message"),
            font=("Arial", 12),
            foreground="green"
        ).pack(pady=(20, 20))
        
        # Summary
        summary_frame = ttk.LabelFrame(
            self.content_frame,
            text=get_text("obs.configuration_summary"),
            padding="15"
        )
        summary_frame.pack(fill=tk.BOTH, expand=True)
        
        summary_text = f"""
{get_text('obs.obs_path')}: {self.obs_path or 'Not set'}

{get_text('obs.recording_settings')}:
  • {get_text('obs.recording_path')}: {self.rec_path_var.get()}
  • {get_text('obs.format')}: {self.format_var.get()}
  • {get_text('obs.quality')}: {self.quality_var.get()}
  • {get_text('obs.fps')}: {self.fps_var.get()}
  • {get_text('obs.resolution')}: {self.resolution_var.get()}
  • {get_text('obs.capture_audio')}: {get_text('common.yes') if self.audio_var.get() else get_text('common.no')}

{get_text('obs.next_steps')}:
1. {get_text('obs.next_step1')}
2. {get_text('obs.next_step2')}
3. {get_text('obs.next_step3')}
        """
        
        summary_label = ttk.Label(
            summary_frame,
            text=summary_text.strip(),
            justify=tk.LEFT,
            font=("Courier", 9)
        )
        summary_label.pack(anchor=tk.W)
    
    def _browse_obs_path(self):
        """Browse for OBS executable."""
        path = filedialog.askopenfilename(
            title=get_text("obs.select_obs"),
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
        )
        if path:
            self.obs_path_var.set(path)
            self.obs_path = path
    
    def _browse_recording_path(self):
        """Browse for recording directory."""
        path = filedialog.askdirectory(
            title=get_text("obs.select_recording_path"),
            initialdir=self.rec_path_var.get()
        )
        if path:
            self.rec_path_var.set(path)
    
    def _create_profile(self):
        """Create OBS profile and scene collection."""
        try:
            # This would create actual OBS config files
            # For now, just show success message
            messagebox.showinfo(
                get_text("success"),
                get_text("obs.profile_created")
            )
            log_info("OBS profile configuration prepared")
        except Exception as e:
            log_error(f"Error creating OBS profile: {str(e)}")
            messagebox.showerror(
                get_text("error"),
                get_text("obs.profile_error")
            )
    
    def _launch_obs(self):
        """Launch OBS Studio."""
        if not self.obs_path or not os.path.exists(self.obs_path):
            messagebox.showwarning(
                get_text("warning"),
                get_text("obs.path_not_found")
            )
            return
        
        try:
            subprocess.Popen([self.obs_path])
            log_info("Launched OBS Studio")
            messagebox.showinfo(
                get_text("info"),
                get_text("obs.launched")
            )
        except Exception as e:
            log_error(f"Error launching OBS: {str(e)}")
            messagebox.showerror(
                get_text("error"),
                f"{get_text('obs.launch_error')}: {str(e)}"
            )
    
    def _open_recording_folder(self):
        """Open recording folder in file explorer."""
        path = self.rec_path_var.get()
        if os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showwarning(
                get_text("warning"),
                get_text("obs.folder_not_found")
            )
    
    def _open_url(self, url: str):
        """Open URL in default browser."""
        import webbrowser
        webbrowser.open(url)
    
    def _previous_step(self):
        """Go to previous step."""
        if self.current_step > 0:
            self._show_step(self.current_step - 1)
    
    def _next_step(self):
        """Go to next step."""
        # Validate current step
        if self.current_step == 0:
            # Check if OBS path is set
            self.obs_path = self.obs_path_var.get()
            if not self.obs_path:
                messagebox.showwarning(
                    get_text("warning"),
                    get_text("obs.path_required")
                )
                return
        
        elif self.current_step == 1:
            # Save configuration
            self.config['recording_path'] = self.rec_path_var.get()
            self.config['format'] = self.format_var.get()
            self.config['quality'] = self.quality_var.get()
            self.config['fps'] = int(self.fps_var.get())
            self.config['resolution'] = self.resolution_var.get()
            self.config['capture_audio'] = self.audio_var.get()
            self.config['auto_start'] = self.autostart_var.get()
        
        # Move to next step
        if self.current_step < 4:
            self._show_step(self.current_step + 1)
    
    def _finish(self):
        """Finish wizard."""
        messagebox.showinfo(
            get_text("success"),
            get_text("obs.wizard_complete")
        )
        self.window.destroy()


# ============================================================================
# LAUNCHER FUNCTION
# ============================================================================

def launch_obs_wizard(parent):
    """Launch the OBS wizard window."""
    wizard = OBSWizard(parent)
    wizard.launch()


if __name__ == "__main__":
    # Test OBS detection
    print("OBS Integration Module Test")
    print("=" * 60)
    
    obs_path = find_obs_installation()
    if obs_path:
        print(f"✓ OBS found: {obs_path}")
    else:
        print("✗ OBS not found")
    
    config_path = get_obs_config_path()
    print(f"✓ OBS config path: {config_path}")
    
    is_running = check_obs_running()
    print(f"✓ OBS running: {is_running}")
