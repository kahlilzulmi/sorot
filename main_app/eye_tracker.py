"""
Eye Tracker Research Software - Main Application

Integrated eye tracking research software with three main features:
1. Gaze Detection - Post-process recorded eye tracking videos
2. Math Quiz Game - Real-time eye-controlled game with recording
3. Stimulus Simulation - Generate/run stimulus protocols with tracking

This module is part of my Undergraduate Final Year Project 2025.

Author: Kahlil Gibran Al Zulmi
NRP: 5049221015
Medical Technology Study Program
Faculty of Medicine and Health
Institut Teknologi Sepuluh Nopember

Advisor: Prof. Dr. Ir. Adhi Dharma Wibawa, S.T., M.T.
Co-Advisor: dr. Zain Budi Syulthoni, Sp.KJ.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

# Add utils to path
sys.path.insert(0, os.path.dirname(__file__))

# Import utilities
from utils.config_manager import load_config, save_config, mark_system_check_complete
from utils.logger import init_logger, log_info, log_warning, close_logger
from utils.localization import load_translations, get_text, switch_language, get_available_languages

# Import modules
from modules.system_check import run_full_system_check, get_system_check_for_config
from modules.detection_wizard import launch_detection_wizard
from modules.game_wizard import launch_game_wizard


class EyeTrackerMainGUI:
    """Main GUI application for Eye Tracker Research Software."""
    
    def __init__(self, root):
        """Initialize the main GUI."""
        self.root = root
        self.config = load_config()
        self.current_language = self.config.get("language", "en")
        
        # Initialize logger
        init_logger(self.config["paths"]["logs_dir"])
        log_info("Application started")
        
        # Load translations
        load_translations(self.current_language)
        
        # Setup window
        self.root.title(get_text("app_title"))
        self.root.geometry(f"{self.config['ui']['window_width']}x{self.config['ui']['window_height']}")
        self.root.resizable(True, True)
        
        # Center window
        self.center_window()
        
        # Setup UI
        self.setup_ui()
        
        # Check if first run
        if self.config.get("first_run", True):
            self.show_first_run_dialog()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def setup_ui(self):
        """Setup the main user interface."""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header section
        self.create_header(main_container)
        
        # System status section
        self.create_system_status(main_container)
        
        # Feature buttons section
        self.create_feature_buttons(main_container)
        
        # Recent sessions section
        self.create_recent_sessions(main_container)
        
        # Bottom menu section
        self.create_bottom_menu(main_container)
        
    def create_header(self, parent):
        """Create header section with title and language switcher."""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Title
        title_label = ttk.Label(
            header_frame,
            text=get_text("app_title"),
            font=('Arial', 18, 'bold')
        )
        title_label.pack(side=tk.LEFT)
        
        # Subtitle
        subtitle_label = ttk.Label(
            header_frame,
            text=get_text("app_subtitle"),
            font=('Arial', 10)
        )
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Language switcher
        lang_frame = ttk.Frame(header_frame)
        lang_frame.pack(side=tk.RIGHT)
        
        ttk.Label(lang_frame, text="🌐", font=('Arial', 14)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.language_var = tk.StringVar(value=self.current_language)
        lang_menu = ttk.Combobox(
            lang_frame,
            textvariable=self.language_var,
            values=[code for code, _ in get_available_languages()],
            state='readonly',
            width=5
        )
        lang_menu.pack(side=tk.LEFT)
        lang_menu.bind('<<ComboboxSelected>>', self.change_language)
        
    def create_system_status(self, parent):
        """Create system status section."""
        status_frame = ttk.LabelFrame(
            parent,
            text=get_text("system_status.title"),
            padding=15
        )
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Status indicators
        system_check = self.config.get("system_check", {})
        
        status_items = [
            ("windows_ok", system_check.get("windows_version", "Not Checked")),
            ("tobii_ok", "Connected" if system_check.get("tobii_connected", False) else "Not Connected"),
            ("obs_ok", "Running" if system_check.get("obs_configured", False) else "Not Running"),
            ("ram_ok", f"{system_check.get('ram_available_gb', 0)} {get_text('system_status.ram_ok')}")
        ]
        
        for i, (key, value) in enumerate(status_items):
            row = i // 2
            col = i % 2
            
            # Status indicator
            indicator = "✓" if system_check.get("completed", False) and i < 3 else "○"
            color = "green" if indicator == "✓" else "gray"
            
            item_frame = ttk.Frame(status_frame)
            item_frame.grid(row=row, column=col, sticky=tk.W, padx=10, pady=5)
            
            ttk.Label(
                item_frame,
                text=indicator,
                font=('Arial', 14),
                foreground=color
            ).pack(side=tk.LEFT, padx=(0, 5))
            
            ttk.Label(
                item_frame,
                text=f"{get_text(f'system_status.{key}')}",
                font=('Arial', 10)
            ).pack(side=tk.LEFT)
            
            if value and value != "Not Checked":
                ttk.Label(
                    item_frame,
                    text=f"({value})",
                    font=('Arial', 9),
                    foreground="gray"
                ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Action buttons
        btn_frame = ttk.Frame(status_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(
            btn_frame,
            text=get_text("system_status.run_check"),
            command=self.run_system_check
        ).pack(side=tk.LEFT, padx=5)
        
        if not system_check.get("completed", False):
            ttk.Button(
                btn_frame,
                text=get_text("system_status.skip_setup"),
                command=self.skip_system_check
            ).pack(side=tk.LEFT, padx=5)
        
    def create_feature_buttons(self, parent):
        """Create three main feature buttons."""
        features_frame = ttk.Frame(parent)
        features_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Configure grid weights for equal sizing
        features_frame.grid_columnconfigure(0, weight=1)
        features_frame.grid_columnconfigure(1, weight=1)
        features_frame.grid_columnconfigure(2, weight=1)
        
        # Feature definitions
        features = [
            {
                "icon": "📹",
                "key": "detection",
                "title": get_text("menu.detection"),
                "desc": get_text("detection.description"),
                "command": self.launch_detection
            },
            {
                "icon": "🎮",
                "key": "game",
                "title": get_text("menu.game"),
                "desc": get_text("game.description"),
                "command": self.launch_game
            },
            {
                "icon": "🎯",
                "key": "stimulus",
                "title": get_text("menu.stimulus"),
                "desc": get_text("stimulus.description"),
                "command": self.launch_stimulus
            }
        ]
        
        for i, feature in enumerate(features):
            self.create_feature_card(features_frame, feature, i)
            
    def create_feature_card(self, parent, feature, column):
        """Create a feature card button."""
        card_frame = ttk.LabelFrame(parent, padding=15)
        card_frame.grid(row=0, column=column, padx=10, sticky=(tk.N, tk.S, tk.E, tk.W))
        
        # Icon
        ttk.Label(
            card_frame,
            text=feature["icon"],
            font=('Arial', 48)
        ).pack(pady=(0, 10))
        
        # Title
        ttk.Label(
            card_frame,
            text=feature["title"],
            font=('Arial', 14, 'bold')
        ).pack()
        
        # Description
        desc_label = ttk.Label(
            card_frame,
            text=feature["desc"],
            font=('Arial', 9),
            foreground="gray",
            wraplength=200,
            justify=tk.CENTER
        )
        desc_label.pack(pady=(5, 15))
        
        # Launch button
        ttk.Button(
            card_frame,
            text=get_text("wizard.next"),
            command=feature["command"],
            width=20
        ).pack()
        
    def create_recent_sessions(self, parent):
        """Create recent sessions list."""
        sessions_frame = ttk.LabelFrame(
            parent,
            text=get_text("database.title"),
            padding=15
        )
        sessions_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Header with View All button
        header = ttk.Frame(sessions_frame)
        header.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            header,
            text="Recent Sessions:",
            font=('Arial', 10, 'bold')
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            header,
            text="View All",
            command=self.view_all_sessions,
            width=10
        ).pack(side=tk.RIGHT)
        
        # Sessions list (placeholder)
        sessions_list = ttk.Frame(sessions_frame)
        sessions_list.pack(fill=tk.X)
        
        # TODO: Load actual recent sessions from database
        placeholder_sessions = [
            "• No recent sessions yet",
        ]
        
        for session in placeholder_sessions:
            ttk.Label(
                sessions_list,
                text=session,
                font=('Arial', 9),
                foreground="gray"
            ).pack(anchor=tk.W, pady=2)
        
    def create_bottom_menu(self, parent):
        """Create bottom menu bar."""
        menu_frame = ttk.Frame(parent)
        menu_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Menu buttons
        menu_items = [
            ("🎬", "obs", self.launch_obs_wizard),
            ("🪄", "improve_detection", self.launch_improve_detection),
            ("📊", "database", self.open_database),
            ("⚙️", "settings", self.open_settings),
            ("📖", "help", self.open_help),
            ("ℹ️", "about", self.open_about)
        ]
        
        for icon, key, command in menu_items:
            btn_text = f"{icon} {get_text(f'menu.{key}')}"
            ttk.Button(
                menu_frame,
                text=btn_text,
                command=command,
                width=15
            ).pack(side=tk.LEFT, padx=5)
        
    # Event handlers
    
    def change_language(self, event=None):
        """Handle language change."""
        new_lang = self.language_var.get()
        if new_lang != self.current_language:
            self.current_language = new_lang
            self.config["language"] = new_lang
            save_config(self.config)
            load_translations(new_lang)
            log_info(f"Language changed to: {new_lang}")
            
            # Show restart message
            messagebox.showinfo(
                get_text("common.info"),
                "Please restart the application for language changes to take full effect."
            )
    
    def show_first_run_dialog(self):
        """Show first run welcome dialog."""
        result = messagebox.askyesno(
            get_text("common.info"),
            get_text("messages.first_run") + "\n\n" + 
            "Would you like to run the system check now?"
        )
        
        if result:
            self.run_system_check()
        else:
            self.skip_system_check()
    
    def run_system_check(self):
        """Run system requirements check."""
        log_info("Running system check")
        
        # Create progress dialog
        progress_window = tk.Toplevel(self.root)
        progress_window.title("System Check")
        progress_window.geometry("500x400")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # Center the progress window
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - (250)
        y = (progress_window.winfo_screenheight() // 2) - (200)
        progress_window.geometry(f'500x400+{x}+{y}')
        
        # Progress label
        ttk.Label(
            progress_window,
            text="Running System Check...",
            font=('Arial', 14, 'bold')
        ).pack(pady=20)
        
        # Results text area
        results_text = tk.Text(progress_window, height=15, width=60, font=('Consolas', 9))
        results_text.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Redirect output to text widget
        class TextRedirector:
            def __init__(self, text_widget):
                self.text_widget = text_widget
            
            def write(self, string):
                self.text_widget.insert(tk.END, string)
                self.text_widget.see(tk.END)
                self.text_widget.update()
            
            def flush(self):
                pass
        
        # Temporarily redirect stdout
        import sys
        old_stdout = sys.stdout
        sys.stdout = TextRedirector(results_text)
        
        try:
            # Run the actual system check
            check_results = run_full_system_check()
            
            # Restore stdout
            sys.stdout = old_stdout
            
            # Save results to config
            config_data = get_system_check_for_config()
            mark_system_check_complete("config.json", config_data)
            
            # Reload config to update GUI
            self.config = load_config()
            
            # Update GUI status section
            self.root.after(100, self.refresh_ui)
            
            # Add close button
            button_frame = ttk.Frame(progress_window)
            button_frame.pack(pady=10)
            
            if check_results['overall_success']:
                ttk.Label(
                    button_frame,
                    text="✓ System check passed!",
                    font=('Arial', 11, 'bold'),
                    foreground='green'
                ).pack(pady=5)
            else:
                ttk.Label(
                    button_frame,
                    text="✗ Some requirements not met",
                    font=('Arial', 11, 'bold'),
                    foreground='orange'
                ).pack(pady=5)
            
            ttk.Button(
                button_frame,
                text="Close",
                command=progress_window.destroy
            ).pack()
            
        except Exception as e:
            sys.stdout = old_stdout
            log_warning(f"System check error: {str(e)}")
            results_text.insert(tk.END, f"\nError: {str(e)}\n")
            
            ttk.Button(
                progress_window,
                text="Close",
                command=progress_window.destroy
            ).pack(pady=10)
    
    def refresh_ui(self):
        """Refresh the UI to show updated system status."""
        # Destroy and recreate the UI to reflect new config
        for widget in self.root.winfo_children():
            widget.destroy()
        self.setup_ui()
        
    def skip_system_check(self):
        """Skip system check."""
        self.config["first_run"] = False
        save_config(self.config)
        log_info("System check skipped by user")
        
    def launch_detection(self):
        """Launch detection wizard."""
        log_info("Launching detection wizard")
        launch_detection_wizard(self.root)
        
    def launch_game(self):
        """Launch math quiz game."""
        log_info("Launching game")
        launch_game_wizard(self.root)
        
    def launch_stimulus(self):
        """Launch stimulus simulation."""
        log_info("Launching stimulus wizard")
        from modules.stimulus_wizard import launch_stimulus_wizard
        launch_stimulus_wizard(self.root)
    
    def launch_obs_wizard(self):
        """Launch OBS setup wizard."""
        log_info("Launching OBS wizard")
        from modules.obs_wizard import launch_obs_wizard
        launch_obs_wizard(self.root)
        
    def launch_improve_detection(self):
        """Launch improve detection wizard."""
        log_info("Launching improve detection wizard")
        from modules.improve_detection_wizard import launch_improve_detection_wizard
        launch_improve_detection_wizard(self.root)
        
    def view_all_sessions(self):
        """Open database viewer."""
        self.open_database()
        
    def open_settings(self):
        """Open settings dialog."""
        log_info("Opening settings")
        from modules.settings_dialog import launch_settings_dialog
        launch_settings_dialog(self.root, callback=self._on_settings_changed)
    
    def _on_settings_changed(self, new_config):
        """Handle settings changes."""
        self.config = new_config
        self.current_language = new_config.get("language", "en")
        log_info(f"Settings updated - Language: {self.current_language}")
        
    def open_database(self):
        """Open database manager."""
        log_info("Opening database viewer")
        from modules.database_viewer import launch_database_viewer
        launch_database_viewer(self.root)
        
    def open_help(self):
        """Open help documentation."""
        log_info("Opening help")
        messagebox.showinfo(
            get_text("menu.help"),
            "Help documentation:\n\n" +
            "Please refer to README.md and PROJECT_ARCHITECTURE.md\n" +
            "for detailed documentation.\n\n" +
            "User manual will be available soon."
        )
        
    def open_about(self):
        """Open about dialog."""
        log_info("Opening about")
        about_text = f"""{get_text("about.version")}

{get_text("about.author")}
{get_text("about.nrp")}

{get_text("about.program")}
{get_text("about.institution")}

{get_text("about.advisor")}
{get_text("about.co_advisor")}

{get_text("about.description")}

{get_text("about.copyright")}
"""
        messagebox.showinfo(get_text("menu.about"), about_text)
        
    def on_closing(self):
        """Handle window closing event."""
        if messagebox.askokcancel(
            get_text("common.warning"),
            get_text("messages.confirm_exit")
        ):
            log_info("Application closing")
            close_logger()
            self.root.destroy()


def main():
    """Main entry point."""
    # Create root window
    root = tk.Tk()
    
    # Create application
    app = EyeTrackerMainGUI(root)
    
    # Run main loop
    root.mainloop()


if __name__ == "__main__":
    main()