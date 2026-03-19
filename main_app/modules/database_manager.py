"""
Database Manager Module

This module provides SQLite database management for storing and retrieving session data
from detection, game, and stimulus modules.

Author: Kahlil Gibran Al Zulmi
Institution: Institut Teknologi Sepuluh Nopember
Date: November 2025
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from utils.logger import log_info, log_warning, log_error


# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

DATABASE_DIR = "databases"
DETECTION_DB = os.path.join(DATABASE_DIR, "detection_sessions.db")
GAME_DB = os.path.join(DATABASE_DIR, "game_sessions.db")
STIMULUS_DB = os.path.join(DATABASE_DIR, "stimulus_sessions.db")


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_databases():
    """Initialize all database files and create tables if they don't exist."""
    try:
        # Create database directory
        os.makedirs(DATABASE_DIR, exist_ok=True)
        
        # Initialize each database
        init_detection_db()
        init_game_db()
        init_stimulus_db()
        
        log_info("All databases initialized successfully")
        return True
    except Exception as e:
        log_error(f"Error initializing databases: {str(e)}")
        return False


def init_detection_db():
    """Initialize detection sessions database."""
    conn = sqlite3.connect(DETECTION_DB)
    cursor = conn.cursor()
    
    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            video_path TEXT NOT NULL,
            output_path TEXT,
            methods_used TEXT,
            total_frames INTEGER,
            frames_processed INTEGER,
            detections_count INTEGER,
            processing_time_seconds REAL,
            config_json TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Detection results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detection_results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            frame_number INTEGER NOT NULL,
            method TEXT NOT NULL,
            center_x REAL,
            center_y REAL,
            radius REAL,
            confidence REAL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    
    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_session_timestamp 
        ON sessions(timestamp)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_results_session 
        ON detection_results(session_id)
    """)
    
    conn.commit()
    conn.close()
    log_info("Detection database initialized")


def init_game_db():
    """Initialize game sessions database."""
    conn = sqlite3.connect(GAME_DB)
    cursor = conn.cursor()
    
    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            participant_id TEXT NOT NULL,
            mode TEXT NOT NULL,
            total_questions INTEGER,
            correct_answers INTEGER,
            score_percentage REAL,
            total_time_seconds REAL,
            session_path TEXT,
            config_json TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Question results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS question_results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            question_index INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            correct_answer INTEGER NOT NULL,
            user_answer INTEGER NOT NULL,
            is_correct INTEGER NOT NULL,
            response_time_seconds REAL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    
    # Gaze data table (optional, for detailed analysis)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gaze_data (
            gaze_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            question_index INTEGER,
            timestamp_offset REAL,
            frame_number INTEGER,
            gaze_x REAL,
            gaze_y REAL,
            roi TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    
    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_game_session_timestamp 
        ON sessions(timestamp)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_game_participant 
        ON sessions(participant_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_question_session 
        ON question_results(session_id)
    """)
    
    conn.commit()
    conn.close()
    log_info("Game database initialized")


def init_stimulus_db():
    """Initialize stimulus sessions database."""
    conn = sqlite3.connect(STIMULUS_DB)
    cursor = conn.cursor()
    
    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            protocol_name TEXT NOT NULL,
            video_path TEXT NOT NULL,
            duration_seconds REAL,
            frame_count INTEGER,
            file_size_mb REAL,
            generation_time_seconds REAL,
            resolution_width INTEGER,
            resolution_height INTEGER,
            fps INTEGER,
            config_json TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            task_index INTEGER NOT NULL,
            task_type TEXT NOT NULL,
            duration_seconds REAL,
            position_x REAL,
            position_y REAL,
            parameters_json TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    
    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_stimulus_timestamp 
        ON sessions(timestamp)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_stimulus_protocol 
        ON sessions(protocol_name)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tasks_session 
        ON tasks(session_id)
    """)
    
    conn.commit()
    conn.close()
    log_info("Stimulus database initialized")


# ============================================================================
# DETECTION SESSION CRUD
# ============================================================================

def add_detection_session(
    video_path: str,
    output_path: str,
    methods_used: List[str],
    total_frames: int,
    frames_processed: int,
    detections_count: int,
    processing_time: float,
    config: Dict[str, Any],
    notes: str = ""
) -> int:
    """
    Add a new detection session to the database.
    
    Returns:
        session_id: ID of the newly created session
    """
    try:
        conn = sqlite3.connect(DETECTION_DB)
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        methods_json = json.dumps(methods_used)
        config_json = json.dumps(config)
        
        cursor.execute("""
            INSERT INTO sessions (
                timestamp, video_path, output_path, methods_used,
                total_frames, frames_processed, detections_count,
                processing_time_seconds, config_json, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, video_path, output_path, methods_json,
            total_frames, frames_processed, detections_count,
            processing_time, config_json, notes
        ))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        log_info(f"Added detection session: {session_id}")
        return session_id
    except Exception as e:
        log_error(f"Error adding detection session: {str(e)}")
        return -1


def add_detection_results(
    session_id: int,
    results: List[Dict[str, Any]]
):
    """Add detection results for a session."""
    try:
        conn = sqlite3.connect(DETECTION_DB)
        cursor = conn.cursor()
        
        for result in results:
            cursor.execute("""
                INSERT INTO detection_results (
                    session_id, frame_number, method,
                    center_x, center_y, radius, confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                result.get('frame_number'),
                result.get('method'),
                result.get('center_x'),
                result.get('center_y'),
                result.get('radius'),
                result.get('confidence', 1.0)
            ))
        
        conn.commit()
        conn.close()
        
        log_info(f"Added {len(results)} detection results for session {session_id}")
        return True
    except Exception as e:
        log_error(f"Error adding detection results: {str(e)}")
        return False


def get_detection_sessions(
    limit: int = 100,
    offset: int = 0,
    search_term: str = None
) -> List[Dict[str, Any]]:
    """Get list of detection sessions."""
    try:
        conn = sqlite3.connect(DETECTION_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM sessions"
        params = []
        
        if search_term:
            query += " WHERE video_path LIKE ? OR notes LIKE ?"
            params = [f"%{search_term}%", f"%{search_term}%"]
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        sessions = [dict(row) for row in rows]
        conn.close()
        
        return sessions
    except Exception as e:
        log_error(f"Error getting detection sessions: {str(e)}")
        return []


def get_detection_session(session_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific detection session with results."""
    try:
        conn = sqlite3.connect(DETECTION_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get session
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        session = dict(row)
        
        # Get results
        cursor.execute("""
            SELECT * FROM detection_results 
            WHERE session_id = ? 
            ORDER BY frame_number
        """, (session_id,))
        
        results = [dict(row) for row in cursor.fetchall()]
        session['results'] = results
        
        conn.close()
        return session
    except Exception as e:
        log_error(f"Error getting detection session: {str(e)}")
        return None


def delete_detection_session(session_id: int) -> bool:
    """Delete a detection session and all related data."""
    try:
        conn = sqlite3.connect(DETECTION_DB)
        cursor = conn.cursor()
        
        # Delete results first (foreign key constraint)
        cursor.execute("DELETE FROM detection_results WHERE session_id = ?", (session_id,))
        
        # Delete session
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        
        conn.commit()
        conn.close()
        
        log_info(f"Deleted detection session: {session_id}")
        return True
    except Exception as e:
        log_error(f"Error deleting detection session: {str(e)}")
        return False


# ============================================================================
# GAME SESSION CRUD
# ============================================================================

def add_game_session(
    participant_id: str,
    mode: str,
    total_questions: int,
    correct_answers: int,
    total_time: float,
    session_path: str,
    config: Dict[str, Any],
    notes: str = ""
) -> int:
    """Add a new game session to the database."""
    try:
        conn = sqlite3.connect(GAME_DB)
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        config_json = json.dumps(config)
        
        cursor.execute("""
            INSERT INTO sessions (
                timestamp, participant_id, mode, total_questions,
                correct_answers, score_percentage, total_time_seconds,
                session_path, config_json, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, participant_id, mode, total_questions,
            correct_answers, score_percentage, total_time,
            session_path, config_json, notes
        ))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        log_info(f"Added game session: {session_id}")
        return session_id
    except Exception as e:
        log_error(f"Error adding game session: {str(e)}")
        return -1


def add_game_question_results(
    session_id: int,
    questions: List[Dict[str, Any]]
):
    """Add question results for a game session."""
    try:
        conn = sqlite3.connect(GAME_DB)
        cursor = conn.cursor()
        
        for q in questions:
            cursor.execute("""
                INSERT INTO question_results (
                    session_id, question_index, question_text,
                    correct_answer, user_answer, is_correct,
                    response_time_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                q.get('question_index'),
                q.get('question_text'),
                q.get('correct_answer'),
                q.get('user_answer'),
                q.get('is_correct', False),
                q.get('response_time')
            ))
        
        conn.commit()
        conn.close()
        
        log_info(f"Added {len(questions)} question results for session {session_id}")
        return True
    except Exception as e:
        log_error(f"Error adding question results: {str(e)}")
        return False


def get_game_sessions(
    limit: int = 100,
    offset: int = 0,
    participant_id: str = None,
    mode: str = None
) -> List[Dict[str, Any]]:
    """Get list of game sessions with optional filters."""
    try:
        conn = sqlite3.connect(GAME_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM sessions WHERE 1=1"
        params = []
        
        if participant_id:
            query += " AND participant_id LIKE ?"
            params.append(f"%{participant_id}%")
        
        if mode:
            query += " AND mode = ?"
            params.append(mode)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        sessions = [dict(row) for row in rows]
        conn.close()
        
        return sessions
    except Exception as e:
        log_error(f"Error getting game sessions: {str(e)}")
        return []


def get_game_session(session_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific game session with question results."""
    try:
        conn = sqlite3.connect(GAME_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get session
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        session = dict(row)
        
        # Get question results
        cursor.execute("""
            SELECT * FROM question_results 
            WHERE session_id = ? 
            ORDER BY question_index
        """, (session_id,))
        
        questions = [dict(row) for row in cursor.fetchall()]
        session['questions'] = questions
        
        conn.close()
        return session
    except Exception as e:
        log_error(f"Error getting game session: {str(e)}")
        return None


def delete_game_session(session_id: int) -> bool:
    """Delete a game session and all related data."""
    try:
        conn = sqlite3.connect(GAME_DB)
        cursor = conn.cursor()
        
        # Delete question results
        cursor.execute("DELETE FROM question_results WHERE session_id = ?", (session_id,))
        
        # Delete gaze data if exists
        cursor.execute("DELETE FROM gaze_data WHERE session_id = ?", (session_id,))
        
        # Delete session
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        
        conn.commit()
        conn.close()
        
        log_info(f"Deleted game session: {session_id}")
        return True
    except Exception as e:
        log_error(f"Error deleting game session: {str(e)}")
        return False


# ============================================================================
# STIMULUS SESSION CRUD
# ============================================================================

def add_stimulus_session(
    protocol_name: str,
    video_path: str,
    duration: float,
    frame_count: int,
    file_size_mb: float,
    generation_time: float,
    resolution: Tuple[int, int],
    fps: int,
    tasks: List[Dict[str, Any]],
    config: Dict[str, Any],
    notes: str = ""
) -> int:
    """Add a new stimulus session to the database."""
    try:
        conn = sqlite3.connect(STIMULUS_DB)
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config_json = json.dumps(config)
        
        cursor.execute("""
            INSERT INTO sessions (
                timestamp, protocol_name, video_path, duration_seconds,
                frame_count, file_size_mb, generation_time_seconds,
                resolution_width, resolution_height, fps,
                config_json, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, protocol_name, video_path, duration,
            frame_count, file_size_mb, generation_time,
            resolution[0], resolution[1], fps,
            config_json, notes
        ))
        
        session_id = cursor.lastrowid
        
        # Add tasks
        for idx, task in enumerate(tasks):
            params_json = json.dumps(task.get('parameters', {}))
            
            cursor.execute("""
                INSERT INTO tasks (
                    session_id, task_index, task_type,
                    duration_seconds, position_x, position_y,
                    parameters_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, idx, task.get('type'),
                task.get('duration', 0),
                task.get('position_x'),
                task.get('position_y'),
                params_json
            ))
        
        conn.commit()
        conn.close()
        
        log_info(f"Added stimulus session: {session_id}")
        return session_id
    except Exception as e:
        log_error(f"Error adding stimulus session: {str(e)}")
        return -1


def get_stimulus_sessions(
    limit: int = 100,
    offset: int = 0,
    protocol_name: str = None
) -> List[Dict[str, Any]]:
    """Get list of stimulus sessions."""
    try:
        conn = sqlite3.connect(STIMULUS_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM sessions WHERE 1=1"
        params = []
        
        if protocol_name:
            query += " AND protocol_name LIKE ?"
            params.append(f"%{protocol_name}%")
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        sessions = [dict(row) for row in rows]
        conn.close()
        
        return sessions
    except Exception as e:
        log_error(f"Error getting stimulus sessions: {str(e)}")
        return []


def get_stimulus_session(session_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific stimulus session with tasks."""
    try:
        conn = sqlite3.connect(STIMULUS_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get session
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        session = dict(row)
        
        # Get tasks
        cursor.execute("""
            SELECT * FROM tasks 
            WHERE session_id = ? 
            ORDER BY task_index
        """, (session_id,))
        
        tasks = [dict(row) for row in cursor.fetchall()]
        session['tasks'] = tasks
        
        conn.close()
        return session
    except Exception as e:
        log_error(f"Error getting stimulus session: {str(e)}")
        return None


def delete_stimulus_session(session_id: int) -> bool:
    """Delete a stimulus session and all related data."""
    try:
        conn = sqlite3.connect(STIMULUS_DB)
        cursor = conn.cursor()
        
        # Delete tasks
        cursor.execute("DELETE FROM tasks WHERE session_id = ?", (session_id,))
        
        # Delete session
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        
        conn.commit()
        conn.close()
        
        log_info(f"Deleted stimulus session: {session_id}")
        return True
    except Exception as e:
        log_error(f"Error deleting stimulus session: {str(e)}")
        return False


# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

def export_detection_session_to_csv(session_id: int, output_path: str) -> bool:
    """Export detection session data to CSV."""
    try:
        session = get_detection_session(session_id)
        if not session:
            return False
        
        # Export results
        results = session.get('results', [])
        if results:
            df = pd.DataFrame(results)
            df.to_csv(output_path, index=False)
            log_info(f"Exported detection session {session_id} to {output_path}")
            return True
        
        return False
    except Exception as e:
        log_error(f"Error exporting detection session: {str(e)}")
        return False


def export_game_session_to_csv(session_id: int, output_path: str) -> bool:
    """Export game session data to CSV."""
    try:
        session = get_game_session(session_id)
        if not session:
            return False
        
        # Export question results
        questions = session.get('questions', [])
        if questions:
            df = pd.DataFrame(questions)
            df.to_csv(output_path, index=False)
            log_info(f"Exported game session {session_id} to {output_path}")
            return True
        
        return False
    except Exception as e:
        log_error(f"Error exporting game session: {str(e)}")
        return False


def export_stimulus_session_to_csv(session_id: int, output_path: str) -> bool:
    """Export stimulus session data to CSV."""
    try:
        session = get_stimulus_session(session_id)
        if not session:
            return False
        
        # Export tasks
        tasks = session.get('tasks', [])
        if tasks:
            df = pd.DataFrame(tasks)
            df.to_csv(output_path, index=False)
            log_info(f"Exported stimulus session {session_id} to {output_path}")
            return True
        
        return False
    except Exception as e:
        log_error(f"Error exporting stimulus session: {str(e)}")
        return False


# ============================================================================
# STATISTICS FUNCTIONS
# ============================================================================

def get_detection_statistics() -> Dict[str, Any]:
    """Get statistics for all detection sessions."""
    try:
        conn = sqlite3.connect(DETECTION_DB)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM sessions")
        total_sessions = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(detections_count) FROM sessions")
        total_detections = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT AVG(processing_time_seconds) FROM sessions")
        avg_processing_time = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_sessions': total_sessions,
            'total_detections': total_detections,
            'avg_processing_time': avg_processing_time
        }
    except Exception as e:
        log_error(f"Error getting detection statistics: {str(e)}")
        return {}


def get_game_statistics() -> Dict[str, Any]:
    """Get statistics for all game sessions."""
    try:
        conn = sqlite3.connect(GAME_DB)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM sessions")
        total_sessions = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(score_percentage) FROM sessions")
        avg_score = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(DISTINCT participant_id) FROM sessions")
        unique_participants = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_sessions': total_sessions,
            'avg_score_percentage': avg_score,
            'unique_participants': unique_participants
        }
    except Exception as e:
        log_error(f"Error getting game statistics: {str(e)}")
        return {}


def get_stimulus_statistics() -> Dict[str, Any]:
    """Get statistics for all stimulus sessions."""
    try:
        conn = sqlite3.connect(STIMULUS_DB)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM sessions")
        total_sessions = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(duration_seconds) FROM sessions")
        total_duration = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(file_size_mb) FROM sessions")
        total_size = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_sessions': total_sessions,
            'total_duration_seconds': total_duration,
            'total_file_size_mb': total_size
        }
    except Exception as e:
        log_error(f"Error getting stimulus statistics: {str(e)}")
        return {}


# ============================================================================
# INITIALIZATION ON MODULE IMPORT
# ============================================================================

# Initialize databases when module is imported
init_databases()


if __name__ == "__main__":
    # Test code
    print("Database Manager Test")
    print("=" * 50)
    
    # Initialize
    init_databases()
    print("✓ Databases initialized")
    
    # Get statistics
    det_stats = get_detection_statistics()
    game_stats = get_game_statistics()
    stim_stats = get_stimulus_statistics()
    
    print(f"\nDetection: {det_stats.get('total_sessions', 0)} sessions")
    print(f"Game: {game_stats.get('total_sessions', 0)} sessions")
    print(f"Stimulus: {stim_stats.get('total_sessions', 0)} sessions")
