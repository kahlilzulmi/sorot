"""
Database Viewer Module

This module provides a Tkinter UI for browsing, searching, and managing session data
from detection, game, and stimulus databases.

Author: Kahlil Gibran Al Zulmi
Institution: Institut Teknologi Sepuluh Nopember
Date: November 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from datetime import datetime
from typing import Dict, Any, Optional

from modules import database_manager as db
from utils.localization import get_text
from utils.logger import log_info, log_error


# ============================================================================
# DATABASE VIEWER WINDOW
# ============================================================================

class DatabaseViewer:
    """Main database viewer window with tabs for each session type."""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.current_session_type = "detection"
        self.current_sessions = []
        
    def launch(self):
        """Launch the database viewer window."""
        if self.window and tk.Toplevel.winfo_exists(self.window):
            self.window.lift()
            return
        
        # Create window
        self.window = tk.Toplevel(self.parent)
        self.window.title(get_text("database_viewer_title"))
        self.window.geometry("1000x700")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.window.winfo_screenheight() // 2) - (700 // 2)
        self.window.geometry(f"1000x700+{x}+{y}")
        
        # Create UI
        self._create_ui()
        
        # Load initial data
        self._load_sessions()
        
        log_info("Database viewer launched")
    
    def _create_ui(self):
        """Create the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text=get_text("database_viewer_title"),
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Tab control
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.detection_tab = self._create_detection_tab()
        self.game_tab = self._create_game_tab()
        self.stimulus_tab = self._create_stimulus_tab()
        
        self.notebook.add(self.detection_tab, text=get_text("detection_sessions"))
        self.notebook.add(self.game_tab, text=get_text("game_sessions"))
        self.notebook.add(self.stimulus_tab, text=get_text("stimulus_sessions"))
        
        # Bind tab change
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)
        
        # Statistics frame at bottom
        self._create_statistics_frame(main_frame)
        
        # Close button
        close_btn = ttk.Button(
            main_frame,
            text=get_text("button_close"),
            command=self.window.destroy
        )
        close_btn.pack(pady=(10, 0))
    
    def _create_detection_tab(self) -> ttk.Frame:
        """Create the detection sessions tab."""
        frame = ttk.Frame(self.notebook)
        
        # Search frame
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(search_frame, text=get_text("search_label")).pack(side=tk.LEFT, padx=(0, 5))
        
        self.detection_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.detection_search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            search_frame,
            text=get_text("button_search"),
            command=lambda: self._search_sessions("detection")
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            search_frame,
            text=get_text("button_refresh"),
            command=lambda: self._refresh_sessions("detection")
        ).pack(side=tk.LEFT)
        
        # Treeview
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Create treeview
        columns = ("ID", "Timestamp", "Video", "Methods", "Frames", "Detections", "Time")
        self.detection_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        vsb.config(command=self.detection_tree.yview)
        hsb.config(command=self.detection_tree.xview)
        
        # Configure columns
        self.detection_tree.heading("ID", text="ID")
        self.detection_tree.heading("Timestamp", text=get_text("timestamp_label"))
        self.detection_tree.heading("Video", text=get_text("video_label"))
        self.detection_tree.heading("Methods", text=get_text("methods_label"))
        self.detection_tree.heading("Frames", text=get_text("frames_label"))
        self.detection_tree.heading("Detections", text=get_text("detections_label"))
        self.detection_tree.heading("Time", text=get_text("time_label"))
        
        self.detection_tree.column("ID", width=50)
        self.detection_tree.column("Timestamp", width=150)
        self.detection_tree.column("Video", width=250)
        self.detection_tree.column("Methods", width=150)
        self.detection_tree.column("Frames", width=80)
        self.detection_tree.column("Detections", width=100)
        self.detection_tree.column("Time", width=80)
        
        # Grid layout
        self.detection_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind double-click
        self.detection_tree.bind("<Double-1>", lambda e: self._view_session_details("detection"))
        
        # Action buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(
            btn_frame,
            text=get_text("button_view_details"),
            command=lambda: self._view_session_details("detection")
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            btn_frame,
            text=get_text("button_export"),
            command=lambda: self._export_session("detection")
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            btn_frame,
            text=get_text("button_delete"),
            command=lambda: self._delete_session("detection")
        ).pack(side=tk.LEFT)
        
        return frame
    
    def _create_game_tab(self) -> ttk.Frame:
        """Create the game sessions tab."""
        frame = ttk.Frame(self.notebook)
        
        # Search frame
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(search_frame, text=get_text("participant_id_label")).pack(side=tk.LEFT, padx=(0, 5))
        
        self.game_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.game_search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            search_frame,
            text=get_text("button_search"),
            command=lambda: self._search_sessions("game")
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            search_frame,
            text=get_text("button_refresh"),
            command=lambda: self._refresh_sessions("game")
        ).pack(side=tk.LEFT)
        
        # Treeview
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        columns = ("ID", "Timestamp", "Participant", "Mode", "Questions", "Correct", "Score", "Time")
        self.game_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        vsb.config(command=self.game_tree.yview)
        hsb.config(command=self.game_tree.xview)
        
        # Configure columns
        self.game_tree.heading("ID", text="ID")
        self.game_tree.heading("Timestamp", text=get_text("timestamp_label"))
        self.game_tree.heading("Participant", text=get_text("participant_label"))
        self.game_tree.heading("Mode", text=get_text("mode_label"))
        self.game_tree.heading("Questions", text=get_text("questions_label"))
        self.game_tree.heading("Correct", text=get_text("correct_label"))
        self.game_tree.heading("Score", text=get_text("score_label"))
        self.game_tree.heading("Time", text=get_text("time_label"))
        
        self.game_tree.column("ID", width=50)
        self.game_tree.column("Timestamp", width=150)
        self.game_tree.column("Participant", width=150)
        self.game_tree.column("Mode", width=100)
        self.game_tree.column("Questions", width=80)
        self.game_tree.column("Correct", width=80)
        self.game_tree.column("Score", width=80)
        self.game_tree.column("Time", width=80)
        
        self.game_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.game_tree.bind("<Double-1>", lambda e: self._view_session_details("game"))
        
        # Action buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(
            btn_frame,
            text=get_text("button_view_details"),
            command=lambda: self._view_session_details("game")
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            btn_frame,
            text=get_text("button_export"),
            command=lambda: self._export_session("game")
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            btn_frame,
            text=get_text("button_delete"),
            command=lambda: self._delete_session("game")
        ).pack(side=tk.LEFT)
        
        return frame
    
    def _create_stimulus_tab(self) -> ttk.Frame:
        """Create the stimulus sessions tab."""
        frame = ttk.Frame(self.notebook)
        
        # Search frame
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(search_frame, text=get_text("protocol_label")).pack(side=tk.LEFT, padx=(0, 5))
        
        self.stimulus_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.stimulus_search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            search_frame,
            text=get_text("button_search"),
            command=lambda: self._search_sessions("stimulus")
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            search_frame,
            text=get_text("button_refresh"),
            command=lambda: self._refresh_sessions("stimulus")
        ).pack(side=tk.LEFT)
        
        # Treeview
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        columns = ("ID", "Timestamp", "Protocol", "Duration", "Resolution", "FPS", "Size", "Tasks")
        self.stimulus_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        vsb.config(command=self.stimulus_tree.yview)
        hsb.config(command=self.stimulus_tree.xview)
        
        # Configure columns
        self.stimulus_tree.heading("ID", text="ID")
        self.stimulus_tree.heading("Timestamp", text=get_text("timestamp_label"))
        self.stimulus_tree.heading("Protocol", text=get_text("protocol_label"))
        self.stimulus_tree.heading("Duration", text=get_text("duration_label"))
        self.stimulus_tree.heading("Resolution", text=get_text("resolution_label"))
        self.stimulus_tree.heading("FPS", text="FPS")
        self.stimulus_tree.heading("Size", text=get_text("size_label"))
        self.stimulus_tree.heading("Tasks", text=get_text("tasks_label"))
        
        self.stimulus_tree.column("ID", width=50)
        self.stimulus_tree.column("Timestamp", width=150)
        self.stimulus_tree.column("Protocol", width=150)
        self.stimulus_tree.column("Duration", width=100)
        self.stimulus_tree.column("Resolution", width=120)
        self.stimulus_tree.column("FPS", width=60)
        self.stimulus_tree.column("Size", width=100)
        self.stimulus_tree.column("Tasks", width=80)
        
        self.stimulus_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.stimulus_tree.bind("<Double-1>", lambda e: self._view_session_details("stimulus"))
        
        # Action buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(
            btn_frame,
            text=get_text("button_view_details"),
            command=lambda: self._view_session_details("stimulus")
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            btn_frame,
            text=get_text("button_export"),
            command=lambda: self._export_session("stimulus")
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            btn_frame,
            text=get_text("button_delete"),
            command=lambda: self._delete_session("stimulus")
        ).pack(side=tk.LEFT)
        
        return frame
    
    def _create_statistics_frame(self, parent):
        """Create the statistics display frame."""
        stats_frame = ttk.LabelFrame(parent, text=get_text("statistics_label"), padding="10")
        stats_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.stats_label = ttk.Label(stats_frame, text="", justify=tk.LEFT)
        self.stats_label.pack(anchor=tk.W)
        
        self._update_statistics()
    
    def _update_statistics(self):
        """Update the statistics display."""
        det_stats = db.get_detection_statistics()
        game_stats = db.get_game_statistics()
        stim_stats = db.get_stimulus_statistics()
        
        stats_text = (
            f"{get_text('detection_sessions')}: {det_stats.get('total_sessions', 0)} | "
            f"{get_text('game_sessions')}: {game_stats.get('total_sessions', 0)} | "
            f"{get_text('stimulus_sessions')}: {stim_stats.get('total_sessions', 0)}"
        )
        
        self.stats_label.config(text=stats_text)
    
    def _on_tab_change(self, event):
        """Handle tab change event."""
        tab_index = self.notebook.index(self.notebook.select())
        
        if tab_index == 0:
            self.current_session_type = "detection"
        elif tab_index == 1:
            self.current_session_type = "game"
        else:
            self.current_session_type = "stimulus"
        
        self._load_sessions()
    
    def _load_sessions(self):
        """Load sessions for the current tab."""
        session_type = self.current_session_type
        
        if session_type == "detection":
            sessions = db.get_detection_sessions()
            self._populate_detection_tree(sessions)
        elif session_type == "game":
            sessions = db.get_game_sessions()
            self._populate_game_tree(sessions)
        else:
            sessions = db.get_stimulus_sessions()
            self._populate_stimulus_tree(sessions)
        
        self.current_sessions = sessions
    
    def _populate_detection_tree(self, sessions):
        """Populate the detection treeview with sessions."""
        # Clear existing
        for item in self.detection_tree.get_children():
            self.detection_tree.delete(item)
        
        # Add sessions
        for session in sessions:
            import json
            methods = json.loads(session.get('methods_used', '[]'))
            methods_str = ', '.join(methods)
            
            self.detection_tree.insert('', tk.END, values=(
                session.get('session_id'),
                session.get('timestamp'),
                os.path.basename(session.get('video_path', '')),
                methods_str,
                session.get('frames_processed', 0),
                session.get('detections_count', 0),
                f"{session.get('processing_time_seconds', 0):.1f}s"
            ))
    
    def _populate_game_tree(self, sessions):
        """Populate the game treeview with sessions."""
        for item in self.game_tree.get_children():
            self.game_tree.delete(item)
        
        for session in sessions:
            self.game_tree.insert('', tk.END, values=(
                session.get('session_id'),
                session.get('timestamp'),
                session.get('participant_id'),
                session.get('mode'),
                session.get('total_questions', 0),
                session.get('correct_answers', 0),
                f"{session.get('score_percentage', 0):.1f}%",
                f"{session.get('total_time_seconds', 0):.1f}s"
            ))
    
    def _populate_stimulus_tree(self, sessions):
        """Populate the stimulus treeview with sessions."""
        for item in self.stimulus_tree.get_children():
            self.stimulus_tree.delete(item)
        
        for session in sessions:
            resolution = f"{session.get('resolution_width')}x{session.get('resolution_height')}"
            duration_min = session.get('duration_seconds', 0) / 60
            
            # Get task count
            stim_session = db.get_stimulus_session(session.get('session_id'))
            task_count = len(stim_session.get('tasks', [])) if stim_session else 0
            
            self.stimulus_tree.insert('', tk.END, values=(
                session.get('session_id'),
                session.get('timestamp'),
                session.get('protocol_name'),
                f"{duration_min:.1f}m",
                resolution,
                session.get('fps'),
                f"{session.get('file_size_mb', 0):.1f}MB",
                task_count
            ))
    
    def _search_sessions(self, session_type):
        """Search sessions based on current tab."""
        if session_type == "detection":
            search_term = self.detection_search_var.get()
            sessions = db.get_detection_sessions(search_term=search_term)
            self._populate_detection_tree(sessions)
        elif session_type == "game":
            participant_id = self.game_search_var.get()
            sessions = db.get_game_sessions(participant_id=participant_id)
            self._populate_game_tree(sessions)
        else:
            protocol = self.stimulus_search_var.get()
            sessions = db.get_stimulus_sessions(protocol_name=protocol)
            self._populate_stimulus_tree(sessions)
        
        self.current_sessions = sessions
    
    def _refresh_sessions(self, session_type):
        """Refresh the sessions list."""
        self._load_sessions()
        self._update_statistics()
        messagebox.showinfo(get_text("info"), get_text("sessions_refreshed"))
    
    def _get_selected_session_id(self, session_type) -> Optional[int]:
        """Get the selected session ID from the current tree."""
        if session_type == "detection":
            tree = self.detection_tree
        elif session_type == "game":
            tree = self.game_tree
        else:
            tree = self.stimulus_tree
        
        selection = tree.selection()
        if not selection:
            messagebox.showwarning(get_text("warning"), get_text("no_session_selected"))
            return None
        
        item = tree.item(selection[0])
        return int(item['values'][0])
    
    def _view_session_details(self, session_type):
        """View detailed information about a session."""
        session_id = self._get_selected_session_id(session_type)
        if not session_id:
            return
        
        # Get session data
        if session_type == "detection":
            session = db.get_detection_session(session_id)
        elif session_type == "game":
            session = db.get_game_session(session_id)
        else:
            session = db.get_stimulus_session(session_id)
        
        if not session:
            messagebox.showerror(get_text("error"), get_text("session_not_found"))
            return
        
        # Show details window
        SessionDetailsWindow(self.window, session, session_type)
    
    def _export_session(self, session_type):
        """Export session data to CSV."""
        session_id = self._get_selected_session_id(session_type)
        if not session_id:
            return
        
        # Ask for file location
        default_name = f"{session_type}_session_{session_id}.csv"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=default_name
        )
        
        if not file_path:
            return
        
        # Export
        success = False
        if session_type == "detection":
            success = db.export_detection_session_to_csv(session_id, file_path)
        elif session_type == "game":
            success = db.export_game_session_to_csv(session_id, file_path)
        else:
            success = db.export_stimulus_session_to_csv(session_id, file_path)
        
        if success:
            messagebox.showinfo(get_text("success"), get_text("export_successful"))
        else:
            messagebox.showerror(get_text("error"), get_text("export_failed"))
    
    def _delete_session(self, session_type):
        """Delete a session after confirmation."""
        session_id = self._get_selected_session_id(session_type)
        if not session_id:
            return
        
        # Confirm deletion
        confirm = messagebox.askyesno(
            get_text("confirm_delete"),
            get_text("confirm_delete_session")
        )
        
        if not confirm:
            return
        
        # Delete
        success = False
        if session_type == "detection":
            success = db.delete_detection_session(session_id)
        elif session_type == "game":
            success = db.delete_game_session(session_id)
        else:
            success = db.delete_stimulus_session(session_id)
        
        if success:
            messagebox.showinfo(get_text("success"), get_text("session_deleted"))
            self._load_sessions()
            self._update_statistics()
        else:
            messagebox.showerror(get_text("error"), get_text("delete_failed"))


# ============================================================================
# SESSION DETAILS WINDOW
# ============================================================================

class SessionDetailsWindow:
    """Window for displaying detailed session information."""
    
    def __init__(self, parent, session: Dict[str, Any], session_type: str):
        self.parent = parent
        self.session = session
        self.session_type = session_type
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title(get_text("session_details"))
        self.window.geometry("800x600")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.window.winfo_screenheight() // 2) - (600 // 2)
        self.window.geometry(f"800x600+{x}+{y}")
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the UI for session details."""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = f"{get_text('session_details')} - ID: {self.session.get('session_id')}"
        title_label = ttk.Label(main_frame, text=title, font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Text widget with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            font=("Courier", 10)
        )
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text.yview)
        
        # Populate with session data
        self._populate_details()
        
        # Make read-only
        self.text.config(state=tk.DISABLED)
        
        # Close button
        close_btn = ttk.Button(
            main_frame,
            text=get_text("button_close"),
            command=self.window.destroy
        )
        close_btn.pack(pady=(10, 0))
    
    def _populate_details(self):
        """Populate the text widget with session details."""
        import json
        
        details = ""
        
        if self.session_type == "detection":
            details = self._format_detection_details()
        elif self.session_type == "game":
            details = self._format_game_details()
        else:
            details = self._format_stimulus_details()
        
        self.text.insert("1.0", details)
    
    def _format_detection_details(self) -> str:
        """Format detection session details."""
        import json
        
        methods = json.loads(self.session.get('methods_used', '[]'))
        config = json.loads(self.session.get('config_json', '{}'))
        
        details = f"""
{get_text('detection_session_details')}
{'=' * 60}

{get_text('session_id_label')}: {self.session.get('session_id')}
{get_text('timestamp_label')}: {self.session.get('timestamp')}
{get_text('video_path_label')}: {self.session.get('video_path')}
{get_text('output_path_label')}: {self.session.get('output_path', 'N/A')}

{get_text('processing_info')}
{'-' * 60}
{get_text('methods_used_label')}: {', '.join(methods)}
{get_text('total_frames_label')}: {self.session.get('total_frames')}
{get_text('frames_processed_label')}: {self.session.get('frames_processed')}
{get_text('detections_count_label')}: {self.session.get('detections_count')}
{get_text('processing_time_label')}: {self.session.get('processing_time_seconds'):.2f}s

{get_text('notes_label')}: {self.session.get('notes', 'N/A')}

{get_text('results_summary')}
{'-' * 60}
"""
        
        results = self.session.get('results', [])
        if results:
            details += f"{get_text('total_results_label')}: {len(results)}\n\n"
            details += f"{'Frame':<10} {'Method':<15} {'Center X':<12} {'Center Y':<12} {'Radius':<10}\n"
            details += "-" * 60 + "\n"
            
            for r in results[:100]:  # Show first 100
                details += f"{r.get('frame_number', 0):<10} "
                details += f"{r.get('method', 'N/A'):<15} "
                details += f"{r.get('center_x', 0):<12.2f} "
                details += f"{r.get('center_y', 0):<12.2f} "
                details += f"{r.get('radius', 0):<10.2f}\n"
            
            if len(results) > 100:
                details += f"\n... ({len(results) - 100} more results)\n"
        
        return details
    
    def _format_game_details(self) -> str:
        """Format game session details."""
        import json
        
        config = json.loads(self.session.get('config_json', '{}'))
        
        details = f"""
{get_text('game_session_details')}
{'=' * 60}

{get_text('session_id_label')}: {self.session.get('session_id')}
{get_text('timestamp_label')}: {self.session.get('timestamp')}
{get_text('participant_id_label')}: {self.session.get('participant_id')}
{get_text('mode_label')}: {self.session.get('mode')}
{get_text('session_path_label')}: {self.session.get('session_path', 'N/A')}

{get_text('results_summary')}
{'-' * 60}
{get_text('total_questions_label')}: {self.session.get('total_questions')}
{get_text('correct_answers_label')}: {self.session.get('correct_answers')}
{get_text('score_percentage_label')}: {self.session.get('score_percentage'):.2f}%
{get_text('total_time_label')}: {self.session.get('total_time_seconds'):.2f}s

{get_text('notes_label')}: {self.session.get('notes', 'N/A')}

{get_text('question_results')}
{'-' * 60}
"""
        
        questions = self.session.get('questions', [])
        if questions:
            details += f"\n{'#':<5} {'Question':<50} {'Correct':<10} {'User':<10} {'Result':<10} {'Time':<10}\n"
            details += "-" * 95 + "\n"
            
            for q in questions:
                details += f"{q.get('question_index', 0) + 1:<5} "
                details += f"{q.get('question_text', '')[:47]:<50} "
                details += f"{q.get('correct_answer', 0):<10} "
                details += f"{q.get('user_answer', 0):<10} "
                result = "✓" if q.get('is_correct') else "✗"
                details += f"{result:<10} "
                details += f"{q.get('response_time_seconds', 0):.2f}s\n"
        
        return details
    
    def _format_stimulus_details(self) -> str:
        """Format stimulus session details."""
        import json
        
        config = json.loads(self.session.get('config_json', '{}'))
        
        details = f"""
{get_text('stimulus_session_details')}
{'=' * 60}

{get_text('session_id_label')}: {self.session.get('session_id')}
{get_text('timestamp_label')}: {self.session.get('timestamp')}
{get_text('protocol_name_label')}: {self.session.get('protocol_name')}
{get_text('video_path_label')}: {self.session.get('video_path')}

{get_text('video_info')}
{'-' * 60}
{get_text('duration_label')}: {self.session.get('duration_seconds', 0) / 60:.2f} minutes
{get_text('frame_count_label')}: {self.session.get('frame_count')}
{get_text('file_size_label')}: {self.session.get('file_size_mb'):.2f} MB
{get_text('generation_time_label')}: {self.session.get('generation_time_seconds'):.2f}s
{get_text('resolution_label')}: {self.session.get('resolution_width')}x{self.session.get('resolution_height')}
FPS: {self.session.get('fps')}

{get_text('notes_label')}: {self.session.get('notes', 'N/A')}

{get_text('tasks_list')}
{'-' * 60}
"""
        
        tasks = self.session.get('tasks', [])
        if tasks:
            details += f"\n{'#':<5} {'Type':<25} {'Duration':<12} {'Position':<20}\n"
            details += "-" * 62 + "\n"
            
            for task in tasks:
                details += f"{task.get('task_index', 0) + 1:<5} "
                details += f"{task.get('task_type', 'N/A'):<25} "
                details += f"{task.get('duration_seconds', 0):.2f}s{' ' * 6}"
                
                pos_x = task.get('position_x')
                pos_y = task.get('position_y')
                if pos_x is not None and pos_y is not None:
                    details += f"({pos_x:.0f}, {pos_y:.0f})\n"
                else:
                    details += "N/A\n"
        
        return details


# ============================================================================
# LAUNCHER FUNCTION
# ============================================================================

def launch_database_viewer(parent):
    """Launch the database viewer window."""
    viewer = DatabaseViewer(parent)
    viewer.launch()


if __name__ == "__main__":
    # Test code
    root = tk.Tk()
    root.withdraw()
    
    launch_database_viewer(root)
    
    root.mainloop()
