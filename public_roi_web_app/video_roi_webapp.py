from typing import Optional, Dict, List, Tuple, Any, Union
import os
import sys
import json
import time
import datetime
import threading
import glob
import traceback
import subprocess
from collections import defaultdict

import cv2
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle as MatplotlibRectangle

from flask import Flask, render_template, request, jsonify, send_from_directory, Response
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename

# Post-processing modules
from report_generator import ReportGenerator

# OBS WebSocket
try:
    from obswebsocket import obsws, requests as obs_requests
    OBS_AVAILABLE = True
except ImportError:
    OBS_AVAILABLE = False

# yt-dlp
try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False


def download_youtube_video(video_url: str) -> str:
    """Download a YouTube video and return the absolute mp4 file path.
    
    Args:
        video_url: YouTube video URL to download.
        
    Returns:
        Absolute path to the downloaded MP4 file.
        
    Raises:
        ImportError: If yt-dlp library is not available.
        RuntimeError: If download fails or file cannot be found.
    """
    if not YTDLP_AVAILABLE:
        raise ImportError("yt-dlp library not available. Install with: pip install yt-dlp")
    
    try:
        download_options = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(DOWNLOADED_FOLDER, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'quiet': False,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(download_options) as youtube_downloader:
            video_info = youtube_downloader.extract_info(video_url, download=True)
            downloaded_filename = youtube_downloader.prepare_filename(video_info)

        # Ensure the file has .mp4 extension
        if not downloaded_filename.endswith('.mp4'):
            downloaded_filename = downloaded_filename.rsplit('.', 1)[0] + '.mp4'
        
        if not os.path.exists(downloaded_filename):
            raise RuntimeError(f"Downloaded file not found: {downloaded_filename}")

        return downloaded_filename
    except Exception as error:
        raise RuntimeError(f"Failed to download YouTube video: {str(error)}")

print("=" * 80)
print("SOROT - System for Optimized Region of Interest Tracking")
print("=" * 80)

# ==============================================================================
# FLASK APP SETUP
# ==============================================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'video-roi-demo-secret'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max video upload
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Get absolute path to script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Constants - use absolute paths relative to script directory
UPLOAD_FOLDER = os.path.join(SCRIPT_DIR, 'uploaded_videos')
DOWNLOADED_FOLDER = os.path.join(SCRIPT_DIR, 'downloaded_videos')
SESSIONS_FOLDER = os.path.join(SCRIPT_DIR, 'sessions')
PROJECT_FOLDER = os.path.join(SCRIPT_DIR, 'projects')

for folder in [UPLOAD_FOLDER, DOWNLOADED_FOLDER, SESSIONS_FOLDER, PROJECT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

def is_path_within_project(filepath: str) -> bool:
    """Validate that a file path is within the project directory.
    
    This security check prevents path traversal attacks by ensuring
    all file operations stay within the application's root directory.
    
    Args:
        filepath: Path to validate (can be relative or absolute).
        
    Returns:
        True if the path is within project directory, False otherwise.
    """
    try:
        absolute_path = os.path.abspath(filepath)
        return absolute_path.startswith(SCRIPT_DIR)
    except (OSError, ValueError) as error:
        print(f"Path validation error: {error}")
        return False

# ==============================================================================
# CONFIGURATION CONSTANTS
# ==============================================================================

# Virtual Camera Configuration
VIRTUAL_CAMERA_INDEX: int = 0  # OpenCV camera index for eye tracking device

# Gaze Detection Parameters (Hough Circle Transform)
HOUGH_PARAM1: int = 50  # Gradient value for Canny edge detector
HOUGH_PARAM2: int = 13  # Accumulator threshold for circle detection
MIN_RADIUS: int = 65  # Minimum iris/pupil radius in pixels
MAX_RADIUS: int = 80  # Maximum iris/pupil radius in pixels

# OBS Studio WebSocket Configuration
OBS_HOST: str = "localhost"  # OBS WebSocket server host
OBS_PORT: int = 4455  # OBS WebSocket server port
OBS_PASSWORD: str = ""  # OBS WebSocket password (empty for no auth)

# Heatmap Visualization Settings
HEATMAP_RESOLUTION: Tuple[int, int] = (192, 108)  # Internal heatmap resolution (width, height)
GAUSSIAN_BLUR_RADIUS: int = 15  # Gaussian blur sigma for heatmap smoothing

print("Flask app initialized.")
print(f"  - OBS control: {'Available' if OBS_AVAILABLE else 'Not available'}")
print(f"  - YouTube download: {'Available' if YTDLP_AVAILABLE else 'Not available'}")

# ==============================================================================
# GLOBAL STATE
# ==============================================================================

class AppState:
    """Global application state manager for the video ROI analysis session.
    
    This class maintains all state information including video data, scenes,
    ROI definitions, recording status, and post-processing data.
    
    Attributes:
        current_video_path: Absolute path to the currently loaded video file.
        video_info: Dictionary containing video metadata (width, height, fps, etc.).
        scenes: List of scene definitions, each containing start/end frames and ROIs.
        recording_active: Boolean flag indicating if recording is currently active.
        session_dir: Directory path for current session data and outputs.
        obs_controller: Instance of OBSController for OBS Studio integration.
        current_workspace_file: Path to currently loaded workspace JSON file.
        last_updated: ISO timestamp of last workspace save.
        recording_timestamps: List of frame synchronization data for post-processing.
        recording_start_time: Unix timestamp when recording started.
        obs_recording_path: Path to OBS recording file.
        participant_name: Name/identifier of current participant.
        processing_progress: Current post-processing progress (0-100).
        processing_thread: Background thread for post-processing operations.
        use_mouse_fallback: Flag indicating mouse tracking fallback mode.
        mouse_gaze_data: List of mouse position gaze data in fallback mode.
        imported_gaze_data: Pre-recorded gaze data imported from CSV.
        frame_offset: Frame offset for synchronizing imported gaze data.
        tracking_mode: Current tracking mode ('Live Recording', 'Mouse Tracking', 'Imported Data').
        calibration_H: Homography matrix for gaze-to-video coordinate mapping.
    """
    
    def __init__(self) -> None:
        # Video state
        self.current_video_path: Optional[str] = None
        self.video_info: Optional[Dict[str, Any]] = None
        self.scenes: List[Dict[str, Any]] = []  
        
        # Recording state
        self.recording_active: bool = False
        self.session_dir: Optional[str] = None
        self.obs_controller: Optional['OBSController'] = None
        
        # Workspace state
        self.current_workspace_file: Optional[str] = None
        self.last_updated: Optional[str] = None
        
        # Post-processing architecture
        self.recording_timestamps: List[Dict[str, Any]] = []
        self.recording_start_time: Optional[float] = None
        self.obs_recording_path: Optional[str] = None
        self.participant_name: Optional[str] = None
        self.processing_progress: int = 0
        self.processing_thread: Optional[threading.Thread] = None
        
        # Mouse tracking fallback
        self.use_mouse_fallback: bool = False
        self.mouse_gaze_data: List[Dict[str, Any]] = []
        
        # Import mode data
        self.imported_gaze_data: Optional[List[Dict[str, Any]]] = None
        self.frame_offset: int = 0
        self.tracking_mode: str = 'Live Recording'
        
        # Calibration data
        self.calibration_H: Optional[np.ndarray] = None

state = AppState()

class TestState:
    """State manager for eye gaze testing and calibration operations.
    
    This class tracks the state of gaze detection testing, including
    frame counts, detection rates, ROI hit statistics, and calibration data.
    
    Attributes:
        active: Flag indicating if gaze testing is currently active.
        gaze_cap: OpenCV VideoCapture object for reading from virtual camera.
        total_frames: Total number of frames processed during testing.
        detect_frames: Number of frames where gaze was successfully detected.
        roi_counts: Dictionary mapping ROI labels to hit counts.
        cal_targets: List of calibration target coordinates (video space).
        cal_camera_pts: List of corresponding camera space coordinates.
    """
    
    def __init__(self) -> None:
        self.active: bool = False
        self.gaze_cap: Optional[cv2.VideoCapture] = None
        self.total_frames: int = 0
        self.detect_frames: int = 0
        self.roi_counts: Dict[str, int] = defaultdict(int)
        
        # Calibration data
        self.cal_targets: List[Dict[str, float]] = []
        self.cal_camera_pts: List[Dict[str, float]] = []

test_state = TestState()

# ==============================================================================
# OBS CONTROLLER
# ==============================================================================

class OBSController:
    """Controller for OBS Studio WebSocket integration.
    
    Manages connection to OBS Studio via WebSocket protocol, handles recording
    start/stop operations, and locates recorded video files.
    
    Attributes:
        ws: OBS WebSocket connection instance.
        connected: Flag indicating active connection to OBS.
        recording_path: Path to the most recent recording file.
        last_error: Last error message encountered during operations.
        recording_start_time: Unix timestamp when recording started.
    """
    
    def __init__(self) -> None:
        self.ws: Optional[Any] = None
        self.connected: bool = False
        self.recording_path: Optional[str] = None
        self.last_error: Optional[str] = None
        self.recording_start_time: Optional[float] = None
    
    def connect(self) -> bool:
        """Establish connection to OBS Studio via WebSocket.
        
        Returns:
            True if connection successful, False otherwise.
        """
        if not OBS_AVAILABLE:
            self.last_error = "obs-websocket-py library not installed"
            print(f"OBS Connection Failed: {self.last_error}")
            return False
        
        try:
            self.ws = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
            self.ws.connect()
            self.connected = True
            self.last_error = None
            print(f"✓ Connected to OBS Studio at {OBS_HOST}:{OBS_PORT}")
            return True
        except Exception as error:
            self.last_error = str(error)
            print(f"OBS Connection Error: {error}")
            return False
    
    def disconnect(self) -> None:
        """Close connection to OBS Studio gracefully."""
        if self.ws and self.connected:
            try:
                self.ws.disconnect()
                self.connected = False
                print("✓ Disconnected from OBS Studio")
            except Exception as error:
                print(f"Warning: Error during OBS disconnect: {error}")
    
    def start_recording(self) -> bool:
        """Start OBS recording session.
        
        Returns:
            True if recording started successfully, False otherwise.
        """
        if not self.connected:
            self.last_error = "Not connected to OBS Studio"
            return False
        
        try:
            self.ws.call(obs_requests.StartRecord())
            self.recording_start_time = time.time()
            print(f"✓ OBS recording started at {datetime.datetime.now().strftime('%H:%M:%S')}")
            return True
        except Exception as error:
            self.last_error = f"Failed to start recording: {str(error)}"
            print(f"OBS Recording Error: {self.last_error}")
            return False
    
    def stop_recording(self, target_dir: Optional[str] = None) -> bool:
        """Stop OBS recording and optionally copy to project folder.
        
        Args:
            target_dir: Directory to copy recording to (usually session folder).
                       If None, keeps recording in default location.
        
        Returns:
            True if recording stopped successfully, False otherwise.
        """
        if not self.connected:
            self.last_error = "Not connected to OBS Studio"
            return False
        
        try:
            self.ws.call(obs_requests.StopRecord())
            print("✓ OBS recording stopped")
            
            # Wait briefly for file to be written to disk
            time.sleep(1)
            
            # Locate the recording file
            external_path = self._find_latest_obs_recording()
            
            if external_path and target_dir:
                # Copy to project folder for archival
                import shutil
                recording_filename = os.path.basename(external_path)
                internal_path = os.path.join(target_dir, recording_filename)
                
                shutil.copy2(external_path, internal_path)
                self.recording_path = internal_path
                print(f"✓ OBS recording copied to project: {internal_path}")
                
                # Optionally delete external file to save disk space
                try:
                    os.remove(external_path)
                    print(f"  → Removed external file: {external_path}")
                except OSError as delete_error:
                    print(f"  ⚠ Could not delete external file: {delete_error}")
            else:
                self.recording_path = external_path
            
            return True
            
        except Exception as error:
            self.last_error = f"Failed to stop recording: {str(error)}"
            print(f"OBS Recording Error: {self.last_error}")
            traceback.print_exc()
            return False
    
    def _find_latest_obs_recording(self) -> Optional[str]:
        """Find the OBS recording created during this session.
        
        Locates recording files matching the pattern 'eyegaze-*.mp4' in the
        user's Videos folder, filtering by creation time to find the recording
        from the current session.
        
        Returns:
            Absolute path to the latest OBS recording, or None if not found.
        """
        videos_folder = os.path.join(os.path.expanduser('~'), 'Videos')
        pattern = os.path.join(videos_folder, 'eyegaze-*.mp4')
        
        # Find all matching recording files
        matching_files = glob.glob(pattern)
        if not matching_files:
            print("⚠ No OBS recordings found matching pattern 'eyegaze-*.mp4'")
            return None
        
        # Filter files created after recording started (with tolerance for clock drift)
        if self.recording_start_time:
            clock_drift_tolerance_seconds = 5
            valid_files = [
                file_path for file_path in matching_files 
                if os.path.getctime(file_path) >= (self.recording_start_time - clock_drift_tolerance_seconds)
            ]
            
            if not valid_files:
                start_time_str = datetime.datetime.fromtimestamp(self.recording_start_time).strftime('%Y-%m-%d %H:%M:%S')
                print(f"⚠ No OBS recordings found created after {start_time_str}")
                return None
            
            matching_files = valid_files
        
        # Get the most recent file from valid candidates
        latest_file = max(matching_files, key=os.path.getctime)
        print(f"✓ Found OBS recording: {os.path.basename(latest_file)}")
        return latest_file

# ==============================================================================
# GAZE DETECTION
# ==============================================================================

def detect_gaze_hough(frame: np.ndarray) -> Optional[Tuple[int, int]]:
    """Detect gaze position using Hough Circle Transform with adaptive parameters.
    
    This function detects circular iris patterns in the input frame using
    OpenCV's HoughCircles algorithm with dynamically calculated parameters
    based on frame dimensions.
    
    Args:
        frame: Input BGR image frame from camera (numpy array).
        
    Returns:
        Tuple of (x, y) coordinates of detected gaze center, or None if no detection.
        
    Note:
        Uses global constants HOUGH_PARAM1, HOUGH_PARAM2 for sensitivity tuning.
        Adapts min/max radius and minimum distance based on frame size.
    """
    try:
        # Convert to grayscale and apply Gaussian blur for noise reduction
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred_frame = cv2.GaussianBlur(gray_frame, (7, 7), 1.5)

        frame_height, frame_width = blurred_frame.shape[:2]
        
        # Calculate adaptive circle detection parameters
        base_dimension = int(min(frame_width, frame_height) * 0.035)
        min_radius = max(8, int(base_dimension * 0.6))
        max_radius = max(min_radius + 6, int(base_dimension * 1.8))
        min_distance = max(30, int(min(frame_width, frame_height) * 0.25))

        # Detect circles (iris/pupil)
        detected_circles = cv2.HoughCircles(
            blurred_frame, 
            cv2.HOUGH_GRADIENT, 
            dp=1.2, 
            minDist=min_distance,
            param1=HOUGH_PARAM1, 
            param2=HOUGH_PARAM2,
            minRadius=min_radius, 
            maxRadius=max_radius
        )

        if detected_circles is not None and len(detected_circles[0]) > 0:
            # Take the first (strongest) detection
            circle_coords = np.uint16(np.around(detected_circles[0, 0]))
            gaze_x = int(circle_coords[0])
            gaze_y = int(circle_coords[1])
            return (gaze_x, gaze_y)
        
        return None
        
    except (cv2.error, ValueError) as error:
        print(f"Gaze detection error: {error}")
        return None

def get_normalized_rois() -> List[Dict[str, Union[int, str, float]]]:
    """Get ROIs from first scene with coordinates normalized to [0, 1] range.
    
    Normalizes ROI pixel coordinates to 0-1 range for resolution-independent
    representation. Useful for scaling ROIs across different display sizes.
    
    Returns:
        List of ROI dictionaries with normalized coordinates, or empty list
        if no video/scenes are loaded.
    """
    normalized_rois: List[Dict[str, Union[int, str, float]]] = []
    
    if not state.video_info or not state.scenes:
        return normalized_rois
    
    video_width = state.video_info['width']
    video_height = state.video_info['height']
    first_scene = state.scenes[0]
    
    for roi_index, roi_data in enumerate(first_scene.get('rois', []), start=1):
        normalized_rois.append({
            'id': roi_index,
            'name': roi_data['label'],
            'color': '#%02x%02x%02x' % (255, 180, 0),
            'x': float(roi_data['x']) / max(1, video_width),
            'y': float(roi_data['y']) / max(1, video_height),
            'width': float(roi_data['width']) / max(1, video_width),
            'height': float(roi_data['height']) / max(1, video_height)
        })
    
    return normalized_rois

def find_roi_hit(video_x: float, video_y: float) -> Tuple[Optional[str], int]:
    """Find which ROI (if any) contains the given video coordinates.
    
    Args:
        video_x: X coordinate in video pixel space.
        video_y: Y coordinate in video pixel space.
        
    Returns:
        Tuple of (roi_label, roi_id) if point is inside an ROI,
        or (None, 0) if point is not in any ROI.
    """
    if not state.video_info or not state.scenes:
        return None, 0
    
    first_scene = state.scenes[0]
    
    for roi_index, roi_data in enumerate(first_scene.get('rois', []), start=1):
        roi_x = roi_data['x']
        roi_y = roi_data['y']
        roi_width = roi_data['width']
        roi_height = roi_data['height']
        
        # Check if point is within ROI bounds
        if (roi_x <= video_x <= roi_x + roi_width and 
            roi_y <= video_y <= roi_y + roi_height):
            return roi_data['label'], roi_index
    
    return None, 0

def map_gaze_to_video_coordinates(gaze_x: float, gaze_y: float, 
                                   camera_width: int, camera_height: int) -> Tuple[int, int]:
    """Transform gaze coordinates from camera space to video space.
    
    Applies either homography transform (if calibrated) or simple scaling
    to map gaze coordinates from camera frame to video frame.
    
    Args:
        gaze_x: Gaze X coordinate in camera frame.
        gaze_y: Gaze Y coordinate in camera frame.
        camera_width: Width of camera frame in pixels.
        camera_height: Height of camera frame in pixels.
        
    Returns:
        Tuple of (video_x, video_y) coordinates in video pixel space.
        
    Note:
        Uses state.calibration_H homography matrix if available for accurate
        perspective transformation. Falls back to linear scaling otherwise.
    """
    if not state.video_info:
        return int(gaze_x), int(gaze_y)
    
    video_width = state.video_info['width']
    video_height = state.video_info['height']
    
    # Use homography transformation if calibrated
    if state.calibration_H is not None:
        try:
            # Convert to homogeneous coordinates
            point_homogeneous = np.array([gaze_x, gaze_y, 1.0], dtype=np.float32)
            homography_matrix = state.calibration_H.astype(np.float32)
            
            # Apply transformation
            transformed_point = homography_matrix @ point_homogeneous
            
            # Convert back from homogeneous coordinates
            if transformed_point[2] != 0:
                mapped_x = float(transformed_point[0] / transformed_point[2])
                mapped_y = float(transformed_point[1] / transformed_point[2])
            else:
                mapped_x = float(transformed_point[0])
                mapped_y = float(transformed_point[1])
            
            # Clamp to video bounds
            mapped_x = max(0.0, min(mapped_x, float(video_width - 1)))
            mapped_y = max(0.0, min(mapped_y, float(video_height - 1)))
            
            return int(round(mapped_x)), int(round(mapped_y))
            
        except (ValueError, np.linalg.LinAlgError) as error:
            print(f"Homography transformation error: {error}. Falling back to scaling.")
    
    # Fallback: Simple linear scaling
    if camera_width <= 1 or camera_height <= 1 or video_width <= 1 or video_height <= 1:
        return int(gaze_x), int(gaze_y)
    
    scaled_x = int(round(gaze_x * (video_width - 1) / (camera_width - 1)))
    scaled_y = int(round(gaze_y * (video_height - 1) / (camera_height - 1)))
    
    # Clamp to video bounds
    scaled_x = max(0, min(video_width - 1, scaled_x))
    scaled_y = max(0, min(video_height - 1, scaled_y))
    
    return scaled_x, scaled_y

def find_roi_at_position(rois: List[Dict[str, Any]], x: float, y: float) -> str:
    """Find which ROI contains the given position.
    
    Args:
        rois: List of ROI definition dictionaries.
        x: X coordinate to check.
        y: Y coordinate to check.
        
    Returns:
        ROI label if position is inside an ROI, 'background' otherwise.
    """
    for roi in rois:
        if (roi['x'] <= x <= roi['x'] + roi['width'] and 
            roi['y'] <= y <= roi['y'] + roi['height']):
            return roi['label']
    
    return 'background'

# ==============================================================================
# FLASK ROUTES
# ==============================================================================

@app.route('/')
def index():
    """Serve main page."""
    return render_template('index.html')

@app.route('/test-gaze')
def test_gaze_page() -> str:
    """Serve the Eye Gaze Test page using current scene ROIs.
    
    Returns:
        Rendered HTML template with ROI data.
    """
    normalized_rois = get_normalized_rois()
    return render_template('test_roi_gaze.html', rois=normalized_rois)

# ===== CALIBRATION ENDPOINTS =====

@app.route('/api/calibration/start', methods=['POST'])
def api_calibration_start():
    """Start a 4-point calibration at video corners."""
    if not state.video_info:
        return jsonify({'success': False, 'error': 'No video loaded'}), 400
    w, h = state.video_info['width'], state.video_info['height']
    # Targets: TL, TR, BR, BL corners
    targets = [
        {'x': 0, 'y': 0},
        {'x': w - 1, 'y': 0},
        {'x': w - 1, 'y': h - 1},
        {'x': 0, 'y': h - 1},
    ]
    # Reset homography and test state collections
    state.calibration_H = None
    test_state.cal_targets = targets
    test_state.cal_camera_pts = []
    return jsonify({'success': True, 'targets': targets, 'video_width': w, 'video_height': h})

@app.route('/api/calibration/submit', methods=['POST'])
def api_calibration_submit():
    """Submit one calibration correspondence: camera -> target video coord."""
    data = request.json or {}
    idx = int(data.get('index', 0))
    cam_x = float(data.get('camera_x', 0))
    cam_y = float(data.get('camera_y', 0))
    if not hasattr(test_state, 'cal_targets') or idx < 0 or idx >= len(test_state.cal_targets):
        return jsonify({'success': False, 'error': 'Invalid calibration index'}), 400
    test_state.cal_camera_pts.append({'x': cam_x, 'y': cam_y})
    # When we have 4 points, compute homography
    if len(test_state.cal_camera_pts) >= 4:
        src = np.array([[p['x'], p['y']] for p in test_state.cal_camera_pts], dtype=np.float32)
        dst = np.array([[p['x'], p['y']] for p in test_state.cal_targets], dtype=np.float32)
        try:
            H, mask = cv2.findHomography(src, dst, method=0)
            if H is not None:
                state.calibration_H = H
                return jsonify({'success': True, 'calibrated': True})
            else:
                return jsonify({'success': False, 'error': 'Homography failed'}), 500
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    return jsonify({'success': True, 'next_index': len(test_state.cal_camera_pts)})

@app.route('/api/start', methods=['POST'])
def api_test_start():
    """Start test gaze capture from virtual camera."""
    if test_state.active:
        return jsonify({'success': True})
    try:
        test_state.gaze_cap = cv2.VideoCapture(VIRTUAL_CAMERA_INDEX)
        if not test_state.gaze_cap.isOpened():
            test_state.gaze_cap = None
            return jsonify({'success': False, 'error': 'Cannot open virtual camera'}), 500
        test_state.active = True
        test_state.total_frames = 0
        test_state.detect_frames = 0
        test_state.roi_counts = defaultdict(int)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def api_test_stop():
    """Stop test gaze capture."""
    try:
        if test_state.gaze_cap:
            test_state.gaze_cap.release()
        test_state.gaze_cap = None
        test_state.active = False
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def api_test_reset() -> Response:
    """Reset test gaze statistics.
    
    Returns:
        JSON success response.
    """
    test_state.total_frames = 0
    test_state.detect_frames = 0
    test_state.roi_counts = defaultdict(int)
    return jsonify({'success': True})

@app.route('/api/gaze')
def api_test_gaze() -> Response:
    """Return latest gaze detection and statistics for test page.
    
    Returns:
        JSON response with gaze coordinates, detection rate, and ROI statistics.
    """
    if not test_state.active or not test_state.gaze_cap:
        return jsonify({
            'gaze': None, 
            'fps': 0, 
            'detection_rate': 0, 
            'total_frames': test_state.total_frames, 
            'stats': dict(test_state.roi_counts)
        })

    frame_read_success, camera_frame = test_state.gaze_cap.read()
    if not frame_read_success:
        test_state.total_frames += 1
        detection_rate = 100.0 * test_state.detect_frames / max(1, test_state.total_frames)
        return jsonify({
            'gaze': None, 
            'fps': 0, 
            'detection_rate': detection_rate, 
            'total_frames': test_state.total_frames, 
            'stats': dict(test_state.roi_counts)
        })

    frame_height, frame_width = camera_frame.shape[:2]
    gaze_position = detect_gaze_hough(camera_frame)
    roi_label = None
    roi_identifier = 0
    
    if gaze_position:
        test_state.detect_frames += 1
        # Map gaze from camera space to video space
        video_x, video_y = map_gaze_to_video_coordinates(
            gaze_position[0], gaze_position[1], frame_width, frame_height
        )
        roi_label, roi_identifier = find_roi_hit(video_x, video_y)
        
        if roi_label:
            test_state.roi_counts[roi_label] += 1

    test_state.total_frames += 1
    detection_rate = 100.0 * test_state.detect_frames / max(1, test_state.total_frames)

    gaze_payload = None
    if gaze_position:
        gaze_payload = {
            'x': gaze_position[0],
            'y': gaze_position[1],
            'frame_width': frame_width,
            'frame_height': frame_height,
            'roi': roi_label,
            'roi_id': roi_identifier
        }

    return jsonify({
        'gaze': gaze_payload,
        'fps': 0.0,
        'detection_rate': detection_rate,
        'total_frames': test_state.total_frames,
        'stats': dict(test_state.roi_counts)
    })

@app.route('/api/save_results', methods=['POST'])
def api_test_save_results() -> Response:
    """Save test gaze statistics to CSV file in sessions folder.
    
    Returns:
        JSON response with filename on success, error message on failure.
    """
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(SESSIONS_FOLDER, f'test_gaze_stats_{timestamp}.csv')
    
    try:
        statistics_rows = [
            {'roi_label': roi_name, 'count': hit_count} 
            for roi_name, hit_count in test_state.roi_counts.items()
        ]
        stats_dataframe = pd.DataFrame(statistics_rows)
        stats_dataframe.to_csv(output_path, index=False)
        
        return jsonify({'success': True, 'filename': output_path})
    except (OSError, pd.errors.EmptyDataError) as error:
        return jsonify({'success': False, 'error': str(error)})

@app.route('/api/video-info')
def get_video_info():
    """Get current video information."""
    if not state.video_info:
        return jsonify({'error': 'No video loaded'}), 404
    return jsonify(state.video_info)

@app.route('/api/scenes', methods=['GET', 'POST'])
def handle_scenes():
    """Get or update scenes."""
    if request.method == 'GET':
        return jsonify(state.scenes)
    
    elif request.method == 'POST':
        state.scenes = request.json
        return jsonify({'success': True})

@app.route('/api/upload-video', methods=['POST'])
def upload_video():
    """Handle video file upload."""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    # Validate path is within project
    if not is_path_within_project(filepath):
        return jsonify({'error': 'Invalid file path'}), 400
    
    file.save(filepath)
    
    # Load video info
    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        return jsonify({'error': 'Cannot open video'}), 400
    
    video_info = {
        'path': filepath,
        'filename': filename,
        'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        'fps': cap.get(cv2.CAP_PROP_FPS),
        'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS)
    }
    cap.release()
    
    state.current_video_path = filepath
    state.video_info = video_info
    
    # Create default scene
    state.scenes = [{
        'start_frame': 0,
        'end_frame': video_info['total_frames'] - 1,
        'name': 'Scene 1',
        'rois': []
    }]
    
    return jsonify(video_info)

@app.route('/api/upload-gaze-video', methods=['POST'])
def upload_gaze_video():
    """Handle gaze video file upload for dual-video mode."""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    filename = secure_filename('gaze_' + file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    # Validate path is within project
    if not is_path_within_project(filepath):
        return jsonify({'error': 'Invalid file path'}), 400
    
    file.save(filepath)
    
    return jsonify({
        'success': True,
        'path': f'/video/{filename}',
        'filename': filename
    })

@app.route('/api/import-gaze-data', methods=['POST'])
def import_gaze_data():
    """Handle gaze data import (pre-parsed from frontend)."""
    data = request.json
    
    if not data or 'gaze_data' not in data:
        return jsonify({'success': False, 'message': 'No gaze data provided'}), 400
    
    gaze_data = data['gaze_data']
    frame_offset = int(data.get('frame_offset', 0))
    
    if not gaze_data or len(gaze_data) == 0:
        return jsonify({'success': False, 'message': 'Empty gaze data'}), 400
    
    try:
        # Validate data structure
        required_keys = ['frame_num', 'gaze_x', 'gaze_y']
        if not all(key in gaze_data[0] for key in required_keys):
            return jsonify({
                'success': False,
                'message': 'Invalid gaze data format'
            }), 400
        
        # Apply frame offset if not already applied
        if frame_offset != 0:
            for point in gaze_data:
                point['frame_num'] = point['frame_num'] + frame_offset
        
        # Store in session state
        state.imported_gaze_data = gaze_data
        state.frame_offset = frame_offset
        state.tracking_mode = 'Imported Data'
        
        frame_nums = [p['frame_num'] for p in gaze_data]
        
        return jsonify({
            'success': True,
            'gaze_points': len(gaze_data),
            'frame_offset': frame_offset,
            'frame_range': [min(frame_nums), max(frame_nums)]
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error processing gaze data: {str(e)}'
        }), 400

@app.route('/video/<path:filename>')
def serve_video(filename):
    """Serve video file with range support for seeking."""
    # URL decode the filename (Flask does this automatically, but be explicit)
    from urllib.parse import unquote
    filename = unquote(filename)
    
    # Check both folders with absolute paths
    upload_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, filename))
    download_path = os.path.abspath(os.path.join(DOWNLOADED_FOLDER, filename))
    
    if os.path.exists(upload_path):
        return send_from_directory(os.path.abspath(UPLOAD_FOLDER), filename)
    elif os.path.exists(download_path):
        return send_from_directory(os.path.abspath(DOWNLOADED_FOLDER), filename)
    else:
        return jsonify({'error': f'Video file not found: {filename}'}), 404

@app.route('/api/import-workspace', methods=['POST'])
def import_workspace():
    """Import workspace and validate video file exists."""
    data = request.json
    
    if not data or 'video_info' not in data or 'scenes' not in data:
        return jsonify({'error': 'Invalid workspace format'}), 400
    
    video_info = data['video_info']
    filename = video_info.get('filename', '')
    
    # Check if video exists in either folder, otherwise auto re-download if URL is present
    upload_path = os.path.join(UPLOAD_FOLDER, filename)
    download_path = os.path.join(DOWNLOADED_FOLDER, filename)
    video_path = None
    auto_downloaded = False

    if os.path.exists(upload_path):
        video_path = upload_path
    elif os.path.exists(download_path):
        video_path = download_path
    else:
        youtube_url = data.get('youtube_url')
        if youtube_url and YTDLP_AVAILABLE:
            try:
                video_path = download_youtube_video(youtube_url)
                auto_downloaded = True
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Video not found and auto-download failed: {str(e)}'
                }), 404
        else:
            return jsonify({
                'success': False,
                'error': f'Video file not found: {filename}',
                'needs_download': bool(youtube_url)
            }), 404
    
    # Validate path is within project
    if not is_path_within_project(video_path):
        return jsonify({
            'success': False,
            'error': 'Video path is outside project directory'
        }), 403

    # Refresh video metadata from the actual file on disk
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return jsonify({
            'success': False,
            'error': f'Cannot open video file: {video_path}'
        }), 400

    video_info = {
        'path': video_path,
        'filename': os.path.basename(video_path),
        'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        'fps': cap.get(cv2.CAP_PROP_FPS),
        'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS)
    }
    cap.release()

    # Update state
    state.current_video_path = video_path
    state.video_info = video_info
    state.scenes = data['scenes']
    
    # Track workspace file if provided (use basename only, full path will be in PROJECT_FOLDER)
    if 'workspace_file' in data and data['workspace_file']:
        workspace_basename = os.path.basename(data['workspace_file'])
        state.current_workspace_file = os.path.join(PROJECT_FOLDER, workspace_basename)
    state.last_updated = datetime.datetime.now().isoformat()
    
    return jsonify({
        'success': True,
        'video_path': video_path,
        'workspace_file': data.get('workspace_file', 'Unknown'),
        'last_updated': state.last_updated,
        'downloaded_from_url': auto_downloaded,
        'video_info': video_info,
        'scenes': state.scenes
    })

@app.route('/api/save-workspace', methods=['POST'])
def save_workspace():
    """Save workspace to file (overwrite existing or create new)."""
    data = request.json
    
    if not data or 'video_info' not in data or 'scenes' not in data:
        return jsonify({'error': 'Invalid workspace format'}), 400
    
    # Get workspace file from request (sent by frontend) or use current state
    requested_file = data.get('workspace_file')
    
    # Determine file path
    if requested_file:
        # Frontend sent a specific file to save to
        workspace_file = os.path.join(PROJECT_FOLDER, requested_file)
        if not workspace_file.endswith('.json'):
            workspace_file += '.json'
    elif state.current_workspace_file and os.path.exists(state.current_workspace_file):
        # Save to existing file
        workspace_file = state.current_workspace_file
    else:
        # Create new file with timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        workspace_file = os.path.join(PROJECT_FOLDER, f'workspace_{timestamp}.json')
    
    state.current_workspace_file = workspace_file
    
    # Validate path is within project
    if not is_path_within_project(workspace_file):
        return jsonify({'error': 'Invalid workspace file path'}), 400
    
    # Update timestamp
    state.last_updated = datetime.datetime.now().isoformat()
    data['last_updated'] = state.last_updated
    
    # Save to file
    try:
        with open(workspace_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'workspace_file': os.path.basename(workspace_file),
            'last_updated': state.last_updated
        })
    except Exception as e:
        return jsonify({'error': f'Failed to save workspace: {str(e)}'}), 500

@app.route('/api/save-workspace-as', methods=['POST'])
def save_workspace_as():
    """Save workspace with a new name (Save As functionality)."""
    data = request.json
    
    if not data or 'video_info' not in data or 'scenes' not in data:
        return jsonify({'error': 'Invalid workspace format'}), 400
    
    filename = data.get('filename', '').strip()
    if not filename:
        # Generate default name if none provided
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'workspace_{timestamp}.json'
    elif not filename.endswith('.json'):
        filename += '.json'
    
    # Create full path
    workspace_file = os.path.join(PROJECT_FOLDER, filename)
    
    # Check if file already exists
    if os.path.exists(workspace_file):
        return jsonify({
            'error': f'File "{filename}" already exists. Please choose a different name.'
        }), 400
    
    # Validate path is within project
    if not is_path_within_project(workspace_file):
        return jsonify({'error': 'Invalid workspace file path'}), 400
    
    # Update state and save
    state.current_workspace_file = workspace_file
    state.last_updated = datetime.datetime.now().isoformat()
    data['last_updated'] = state.last_updated
    
    try:
        with open(workspace_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'workspace_file': os.path.basename(workspace_file),
            'last_updated': state.last_updated
        })
    except Exception as e:
        return jsonify({'error': f'Failed to save workspace: {str(e)}'}), 500

@app.route('/api/export-scenes-rois', methods=['POST'])
def export_scenes_rois():
    """
    Export scenes and ROIs data to CSV or JSON format with normalized coordinates.
    
    Expected JSON payload:
    {
        "scenes": [...],  // Scenes array with ROIs
        "video_info": {...},  // Video metadata (width, height, fps, total_frames)
        "format": "csv" or "json",  // Export format
        "filename": "export_name",  // Optional custom filename
        "include_normalized": true,  // Include normalized (0-1) coordinates
        "include_timestamps": true  // Include timestamp calculations
    }
    
    Returns downloadable file with structured data.
    """
    try:
        data = request.json
        
        if not data or 'scenes' not in data or 'video_info' not in data:
            return jsonify({'error': 'Missing required fields: scenes and video_info'}), 400
        
        scenes = data['scenes']
        video_info = data['video_info']
        export_format = data.get('format', 'csv').lower()
        filename = data.get('filename', 'scenes_rois_export')
        include_normalized = data.get('include_normalized', True)
        include_timestamps = data.get('include_timestamps', True)
        
        # Validate format
        if export_format not in ['csv', 'json']:
            return jsonify({'error': 'Invalid format. Use "csv" or "json"'}), 400
        
        # Get video dimensions and fps
        video_width = video_info.get('width', 1920)
        video_height = video_info.get('height', 1080)
        fps = video_info.get('fps', 30.0)
        total_frames = video_info.get('total_frames', 0)
        
        if export_format == 'csv':
            # Export as CSV
            rows = []
            
            for scene_idx, scene in enumerate(scenes):
                scene_name = scene.get('name', f'Scene_{scene_idx}')
                scene_custom_name = scene.get('custom_name', '')
                start_frame = scene.get('start_frame', 0)
                end_frame = scene.get('end_frame', 0)
                duration_frames = end_frame - start_frame + 1
                
                # Calculate timestamps
                start_time = start_frame / fps if fps > 0 else 0
                end_time = end_frame / fps if fps > 0 else 0
                duration_seconds = duration_frames / fps if fps > 0 else 0
                
                # Process ROIs
                rois = scene.get('rois', [])
                
                if not rois:
                    # Scene without ROIs - export scene info only
                    row = {
                        'scene_index': scene_idx,
                        'scene_name': scene_name,
                        'scene_custom_name': scene_custom_name,
                        'start_frame': start_frame,
                        'end_frame': end_frame,
                        'duration_frames': duration_frames,
                        'roi_count': 0
                    }
                    
                    if include_timestamps:
                        row.update({
                            'start_time_sec': round(start_time, 3),
                            'end_time_sec': round(end_time, 3),
                            'duration_sec': round(duration_seconds, 3)
                        })
                    
                    rows.append(row)
                else:
                    # Export each ROI as a separate row
                    for roi_idx, roi in enumerate(rois):
                        row = {
                            'scene_index': scene_idx,
                            'scene_name': scene_name,
                            'scene_custom_name': scene_custom_name,
                            'start_frame': start_frame,
                            'end_frame': end_frame,
                            'duration_frames': duration_frames,
                            'roi_index': roi_idx,
                            'roi_label': roi.get('label', f'ROI_{roi_idx}'),
                            'roi_x': roi.get('x', 0),
                            'roi_y': roi.get('y', 0),
                            'roi_width': roi.get('width', 0),
                            'roi_height': roi.get('height', 0),
                            'roi_center_x': roi.get('x', 0) + roi.get('width', 0) / 2,
                            'roi_center_y': roi.get('y', 0) + roi.get('height', 0) / 2,
                        }
                        
                        if include_timestamps:
                            row.update({
                                'start_time_sec': round(start_time, 3),
                                'end_time_sec': round(end_time, 3),
                                'duration_sec': round(duration_seconds, 3)
                            })
                        
                        if include_normalized:
                            row.update({
                                'roi_x_norm': round(roi.get('x', 0) / video_width, 4),
                                'roi_y_norm': round(roi.get('y', 0) / video_height, 4),
                                'roi_width_norm': round(roi.get('width', 0) / video_width, 4),
                                'roi_height_norm': round(roi.get('height', 0) / video_height, 4),
                                'roi_center_x_norm': round((roi.get('x', 0) + roi.get('width', 0) / 2) / video_width, 4),
                                'roi_center_y_norm': round((roi.get('y', 0) + roi.get('height', 0) / 2) / video_height, 4),
                            })
                        
                        # Add color tag if available
                        if 'color_tag' in roi:
                            row['roi_color'] = roi['color_tag']
                        
                        rows.append(row)
            
            # Convert to DataFrame and CSV
            df = pd.DataFrame(rows)
            
            # Create export directory if not exists
            export_dir = os.path.join(os.getcwd(), 'exports')
            os.makedirs(export_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            export_filename = f"{filename}_{timestamp}.csv"
            export_path = os.path.join(export_dir, export_filename)
            
            # Save CSV
            df.to_csv(export_path, index=False, encoding='utf-8')
            
            return jsonify({
                'success': True,
                'format': 'csv',
                'filename': export_filename,
                'path': export_path,
                'rows': len(rows),
                'scenes': len(scenes),
                'total_rois': sum(len(s.get('rois', [])) for s in scenes)
            })
            
        else:  # JSON format
            # Export as structured JSON
            export_data = {
                'metadata': {
                    'export_date': datetime.datetime.now().isoformat(),
                    'video_info': {
                        'filename': video_info.get('filename', ''),
                        'width': video_width,
                        'height': video_height,
                        'fps': fps,
                        'total_frames': total_frames,
                        'duration_seconds': round(total_frames / fps, 3) if fps > 0 else 0
                    },
                    'scene_count': len(scenes),
                    'total_roi_count': sum(len(s.get('rois', [])) for s in scenes)
                },
                'scenes': []
            }
            
            for scene_idx, scene in enumerate(scenes):
                scene_name = scene.get('name', f'Scene_{scene_idx}')
                scene_custom_name = scene.get('custom_name', '')
                start_frame = scene.get('start_frame', 0)
                end_frame = scene.get('end_frame', 0)
                duration_frames = end_frame - start_frame + 1
                
                # Calculate timestamps
                start_time = start_frame / fps if fps > 0 else 0
                end_time = end_frame / fps if fps > 0 else 0
                duration_seconds = duration_frames / fps if fps > 0 else 0
                
                scene_export = {
                    'index': scene_idx,
                    'name': scene_name,
                    'custom_name': scene_custom_name,
                    'frames': {
                        'start': start_frame,
                        'end': end_frame,
                        'duration': duration_frames
                    }
                }
                
                if include_timestamps:
                    scene_export['timestamps'] = {
                        'start_sec': round(start_time, 3),
                        'end_sec': round(end_time, 3),
                        'duration_sec': round(duration_seconds, 3),
                        'start_formatted': format_timestamp(start_time),
                        'end_formatted': format_timestamp(end_time)
                    }
                
                # Process ROIs
                rois_export = []
                for roi_idx, roi in enumerate(scene.get('rois', [])):
                    roi_x = roi.get('x', 0)
                    roi_y = roi.get('y', 0)
                    roi_width = roi.get('width', 0)
                    roi_height = roi.get('height', 0)
                    
                    roi_export = {
                        'index': roi_idx,
                        'label': roi.get('label', f'ROI_{roi_idx}'),
                        'coordinates': {
                            'x': roi_x,
                            'y': roi_y,
                            'width': roi_width,
                            'height': roi_height,
                            'center_x': roi_x + roi_width / 2,
                            'center_y': roi_y + roi_height / 2,
                            'x2': roi_x + roi_width,
                            'y2': roi_y + roi_height
                        }
                    }
                    
                    if include_normalized:
                        roi_export['coordinates_normalized'] = {
                            'x': round(roi_x / video_width, 4),
                            'y': round(roi_y / video_height, 4),
                            'width': round(roi_width / video_width, 4),
                            'height': round(roi_height / video_height, 4),
                            'center_x': round((roi_x + roi_width / 2) / video_width, 4),
                            'center_y': round((roi_y + roi_height / 2) / video_height, 4),
                            'x2': round((roi_x + roi_width) / video_width, 4),
                            'y2': round((roi_y + roi_height) / video_height, 4)
                        }
                    
                    # Add color tag if available
                    if 'color_tag' in roi:
                        roi_export['color'] = roi['color_tag']
                    
                    rois_export.append(roi_export)
                
                scene_export['rois'] = rois_export
                scene_export['roi_count'] = len(rois_export)
                
                export_data['scenes'].append(scene_export)
            
            # Create export directory if not exists
            export_dir = os.path.join(os.getcwd(), 'exports')
            os.makedirs(export_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            export_filename = f"{filename}_{timestamp}.json"
            export_path = os.path.join(export_dir, export_filename)
            
            # Save JSON
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return jsonify({
                'success': True,
                'format': 'json',
                'filename': export_filename,
                'path': export_path,
                'scenes': len(scenes),
                'total_rois': export_data['metadata']['total_roi_count']
            })
    
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

def format_timestamp(seconds):
    """Format seconds as HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    else:
        return f"{minutes:02d}:{secs:06.3f}"

@app.route('/api/thumbnail')
def get_thumbnail():
    """Generate and serve a thumbnail for a specific video frame."""
    try:
        video_filename = request.args.get('video', '')
        frame_num = int(request.args.get('frame', 0))
        
        if not video_filename:
            return jsonify({'error': 'No video specified'}), 400
        
        # Find video path
        video_path = None
        upload_path = os.path.join(UPLOAD_FOLDER, video_filename)
        download_path = os.path.join(DOWNLOADED_FOLDER, video_filename)
        
        if os.path.exists(upload_path):
            video_path = upload_path
        elif os.path.exists(download_path):
            video_path = download_path
        else:
            return jsonify({'error': 'Video not found'}), 404
        
        # Validate path is within project
        if not is_path_within_project(video_path):
            return jsonify({'error': 'Invalid video path'}), 403
        
        # Extract frame
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return jsonify({'error': 'Could not read frame'}), 500
        
        # Resize to thumbnail size (160x90 for 16:9 aspect ratio)
        thumbnail = cv2.resize(frame, (160, 90), interpolation=cv2.INTER_AREA)
        
        # Convert to JPEG
        _, buffer = cv2.imencode('.jpg', thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        # Return as image
        response = Response(buffer.tobytes(), mimetype='image/jpeg')
        response.headers['Cache-Control'] = 'public, max-age=3600'
        return response
        
    except Exception as e:
        print(f"Thumbnail generation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-youtube', methods=['POST'])
def download_youtube():
    """Download video from YouTube URL."""
    if not YTDLP_AVAILABLE:
        return jsonify({'error': 'yt-dlp not installed'}), 400
    
    data = request.json
    url = data.get('url', '')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    try:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(DOWNLOADED_FOLDER, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'quiet': False,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Ensure .mp4 extension
            if not filename.endswith('.mp4'):
                filename = filename.rsplit('.', 1)[0] + '.mp4'
        
        # Validate path is within project
        if not is_path_within_project(filename):
            return jsonify({'error': 'Downloaded video path is outside project directory'}), 403
        
        # Load video info
        cap = cv2.VideoCapture(filename)
        if not cap.isOpened():
            return jsonify({'error': 'Downloaded file cannot be opened'}), 400
        
        video_info = {
            'path': filename,
            'filename': os.path.basename(filename),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS)
        }
        cap.release()
        
        state.current_video_path = filename
        state.video_info = video_info
        
        # Create default scene
        state.scenes = [{
            'start_frame': 0,
            'end_frame': video_info['total_frames'] - 1,
            'name': 'Scene 1',
            'rois': []
        }]
        
        return jsonify(video_info)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recording/check-devices', methods=['GET'])


@app.route('/api/recording/start', methods=['POST'])
def start_recording():
    """Start recording session with OBS (new post-processing architecture)."""
    try:
        if state.recording_active:
            return jsonify({'error': 'Recording already active'}), 400

        if not state.current_video_path or not state.video_info:
            return jsonify({'error': 'No video loaded. Please load a video before recording.'}), 400

        # Get participant name from request (handle missing Content-Type)
        data = request.get_json(force=True, silent=True) or {}
        state.participant_name = data.get('participant_name', 'Participant')

        # Create session directory
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        state.session_dir = os.path.join(SESSIONS_FOLDER, f"session_{timestamp}_{state.participant_name}")
        os.makedirs(state.session_dir, exist_ok=True)
        
        # Save project state
        project_data = {
            'video_path': state.current_video_path,
            'video_info': state.video_info,
            'scenes': state.scenes,
            'participant_name': state.participant_name,
            'timestamp': timestamp
        }
        with open(os.path.join(state.session_dir, 'project.json'), 'w') as f:
            json.dump(project_data, f, indent=2)
        
        # Mouse tracking is ALWAYS available as a standalone recording method
        # Try OBS if available, but silently fall back to mouse tracking on ANY failure
        state.use_mouse_fallback = True  # Default to mouse tracking (no dependencies)
        obs_started = False
        
        if OBS_AVAILABLE:
            try:
                # Attempt to start OBS recording
                state.obs_controller = OBSController()
                if state.obs_controller.connect() and state.obs_controller.start_recording():
                    obs_started = True
                    state.use_mouse_fallback = False
                    print("✓ OBS recording started successfully (external gaze tracking)")
                else:
                    print("⚠ OBS connection failed - falling back to mouse tracking")
            except Exception as obs_err:
                print(f"⚠ OBS start failed: {obs_err}")
                # Fall back to mouse tracking on any error
                state.use_mouse_fallback = True
        
        if state.use_mouse_fallback:
            state.obs_controller = None
            print("✓ Recording with MOUSE TRACKING (standalone mode)")
        
        # Initialize recording state
        state.recording_timestamps = []
        state.mouse_gaze_data = []
        state.recording_start_time = time.time()
        state.recording_active = True
        
        return jsonify({
            'success': True,
            'session_dir': state.session_dir,
            'participant_name': state.participant_name,
            'use_mouse_fallback': state.use_mouse_fallback,
            'warning': 'Using mouse tracking fallback (OBS not available)' if state.use_mouse_fallback else None
        })
        
    except Exception as e:
        print(f"Error in start_recording: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Recording start failed: {str(e)}'}), 500

@app.route('/api/recording/stop', methods=['POST'])
def stop_recording():
    """Stop recording session and prepare for post-processing."""
    if not state.recording_active:
        return jsonify({'error': 'No active recording'}), 400
    
    state.recording_active = False
    
    # Handle OBS or mouse fallback mode
    if state.use_mouse_fallback:
        # Save mouse gaze data directly
        if state.mouse_gaze_data:
            df = pd.DataFrame(state.mouse_gaze_data)
            # Rename 'ad_frame' to 'frame_num' for consistency with heatmap generation
            if 'ad_frame' in df.columns:
                df.rename(columns={'ad_frame': 'frame_num'}, inplace=True)
            # Add tracking mode metadata column
            df['tracking_mode'] = 'Mouse Tracking'
            csv_path = os.path.join(state.session_dir, 'gaze_data.csv')
            df.to_csv(csv_path, index=False)
            print(f"Mouse gaze data saved: {len(state.mouse_gaze_data)} entries")
        
        return jsonify({
            'success': True,
            'use_mouse_fallback': True,
            'gaze_entries_recorded': len(state.mouse_gaze_data),
            'session_dir': state.session_dir,
            'ready_for_processing': True,
            'skip_video_processing': True  # No video to process
        })
    else:
        # Stop OBS and get recording path
        if state.obs_controller:
            try:
                state.obs_controller.stop_recording()
                state.obs_recording_path = state.obs_controller.recording_path
                state.obs_controller.disconnect()
            except Exception as e:
                print(f"Error stopping OBS: {e}")
                return jsonify({'error': f'Failed to stop OBS: {str(e)}'}), 500
            finally:
                state.obs_controller = None
        
        # Save timestamp data
        if state.recording_timestamps:
            df = pd.DataFrame(state.recording_timestamps)
            csv_path = os.path.join(state.session_dir, 'recording_timestamps.csv')
            df.to_csv(csv_path, index=False)
        
        if not state.obs_recording_path or not os.path.exists(state.obs_recording_path):
            return jsonify({
                'error': 'OBS recording file not found. Please check OBS settings.',
                'expected_pattern': 'eyegaze-*.mp4 in Videos folder'
            }), 404
        
        return jsonify({
            'success': True,
            'use_mouse_fallback': False,
            'timestamps_recorded': len(state.recording_timestamps),
            'obs_recording_path': state.obs_recording_path,
            'session_dir': state.session_dir,
            'ready_for_processing': True
        })

@app.route('/api/processing/start-post-processing', methods=['POST'])
def start_post_processing():
    """Start post-processing in background thread."""
    # Check if we have data to process (either OBS recording or mouse data)
    if state.use_mouse_fallback:
        # For mouse mode, check session directory and mouse data
        if not state.session_dir or not state.mouse_gaze_data:
            return jsonify({'error': 'No mouse tracking data available'}), 400
    else:
        # For OBS mode, check recording path
        if not state.obs_recording_path or not state.session_dir:
            return jsonify({'error': 'No recording data available'}), 400
    
    if state.processing_thread and state.processing_thread.is_alive():
        return jsonify({'error': 'Processing already in progress'}), 400
    
    def process_worker():
        try:
            print("\n" + "="*80)
            print("Starting Post-Processing Pipeline...")
            print("="*80)
            
            # Check if using mouse fallback (no video processing needed)
            if state.use_mouse_fallback:
                print("Using mouse fallback mode - skipping video processing")
                # Mouse data already saved in stop_recording
                gaze_csv = os.path.join(state.session_dir, 'gaze_data.csv')
                if not os.path.exists(gaze_csv):
                    print("Error: No mouse gaze data found")
                    state.processing_progress = -1
                    return
                
                df = pd.read_csv(gaze_csv)
                
                # Transform mouse data to match expected format
                gaze_data = []
                for _, row in df.iterrows():
                    # Determine scene name (use custom name if available)
                    scene_name = row.get('scene_custom_name') if row.get('scene_custom_name') else row.get('scene_name', 'Unknown')
                    
                    # Handle both 'ad_frame' and 'frame_num' column names for backward compatibility
                    frame_num = int(row.get('frame_num', row.get('ad_frame', 0)))
                    
                    gaze_data.append({
                        'frame_num': frame_num,
                        'gaze_x': float(row['gaze_x']),
                        'gaze_y': float(row['gaze_y']),
                        'scene_name': scene_name,
                        'roi': row.get('roi_label', 'Outside ROI')
                    })
                
                result = {'success': True, 'gaze_data': gaze_data}
                print(f"Processed {len(gaze_data)} mouse tracking gaze points")
            
            if result['success']:
                # Generate heatmaps
                print("\nGenerating heatmaps...")
                heatmaps = generate_heatmaps_from_data(
                    result['gaze_data'],
                    state.session_dir,
                    state.current_video_path,
                    state.video_info,
                    state.scenes
                )
                
                # Generate gaze trajectories
                print("\nGenerating gaze trajectories...")
                trajectories = generate_gaze_trajectories(
                    result['gaze_data'],
                    state.session_dir,
                    state.current_video_path,
                    state.video_info,
                    state.scenes
                )
                
                # Generate reports
                print("\nGenerating reports...")
                tracking_mode = "Mouse Tracking" if state.use_mouse_fallback else "Eye Tracking (OBS)"
                reporter = ReportGenerator(
                    session_dir=state.session_dir,
                    gaze_data=result['gaze_data'],
                    video_info=state.video_info,
                    scenes=state.scenes,
                    participant_name=state.participant_name or "Participant",
                    tracking_mode=tracking_mode
                )
                
                excel_path = reporter.generate_excel_report()
                pdf_path = reporter.generate_pdf_report(heatmap_paths=heatmaps, trajectory_paths=trajectories)
                
                state.processing_progress = 100
                print("\n" + "="*80)
                print("Post-Processing Complete!")
                print(f"Excel Report: {excel_path}")
                print(f"PDF Report: {pdf_path}")
                print("="*80 + "\n")
            else:
                print("Post-processing failed!")
                
        except Exception as e:
            print(f"Error in post-processing: {e}")
            import traceback
            traceback.print_exc()
            state.processing_progress = -1  # Error state
    
    # Start processing in background
    state.processing_progress = 0
    state.processing_thread = threading.Thread(target=process_worker, daemon=True)
    state.processing_thread.start()
    
    return jsonify({'success': True, 'message': 'Post-processing started'})

@app.route('/api/processing/progress', methods=['GET'])
def get_processing_progress():
    """Get current post-processing progress."""
    return jsonify({
        'progress': state.processing_progress,
        'is_processing': state.processing_thread and state.processing_thread.is_alive(),
        'complete': state.processing_progress >= 100,
        'error': state.processing_progress < 0
    })

@app.route('/api/reports/list', methods=['GET'])
def list_reports():
    """List available reports in session directory."""
    if not state.session_dir or not os.path.exists(state.session_dir):
        return jsonify({'reports': []})
    
    reports = []
    for filename in os.listdir(state.session_dir):
        if filename.endswith(('.xlsx', '.pdf', '.mp4', '.png')):
            filepath = os.path.join(state.session_dir, filename)
            reports.append({
                'filename': filename,
                'path': filepath,
                'size': os.path.getsize(filepath),
                'modified': datetime.datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
            })
    
    return jsonify({'reports': reports})

@app.route('/api/reports/download/<filename>')
def download_report(filename):
    """Download a specific report file."""
    if not state.session_dir:
        return jsonify({'error': 'No session active'}), 404
    
    return send_from_directory(state.session_dir, filename, as_attachment=True)

@app.route('/api/generate-reports-from-import', methods=['POST'])
def generate_reports_from_import():
    """Generate reports from imported gaze data."""
    if not state.imported_gaze_data:
        return jsonify({'error': 'No imported gaze data available'}), 400
    
    if not state.current_video_path or not state.video_info:
        return jsonify({'error': 'No video loaded'}), 400
    
    if not state.scenes:
        return jsonify({'error': 'No scenes defined'}), 400
    
    try:
        # Create session directory
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        session_name = f"import_session_{timestamp}"
        session_dir = os.path.join(SESSIONS_FOLDER, session_name)
        os.makedirs(session_dir, exist_ok=True)
        state.session_dir = session_dir
        
        # Convert imported gaze data to formatted gaze data with ROI analysis
        formatted_gaze_data = []
        
        for gaze_point in state.imported_gaze_data:
            frame_num = gaze_point['frame_num']
            gaze_x = gaze_point['gaze_x']
            gaze_y = gaze_point['gaze_y']
            
            # Determine which scene this frame belongs to
            scene_name = None
            for scene in state.scenes:
                if scene['start_frame'] <= frame_num < scene['end_frame']:
                    scene_name = scene.get('custom_name') or scene['name']
                    break
            
            if not scene_name:
                continue
            
            # Check which ROI the gaze point falls into
            roi_name = None
            for scene in state.scenes:
                if scene.get('custom_name', scene['name']) == scene_name:
                    for roi in scene.get('rois', []):
                        x, y, w, h = roi['x'], roi['y'], roi['width'], roi['height']
                        if x <= gaze_x < x + w and y <= gaze_y < y + h:
                            roi_name = roi['label']
                            break
                    break
            
            formatted_gaze_data.append({
                'frame_num': frame_num,
                'gaze_x': gaze_x,
                'gaze_y': gaze_y,
                'scene_name': scene_name,
                'roi': roi_name or 'Outside ROI'
            })
        
        # Save gaze data CSV
        df = pd.DataFrame(formatted_gaze_data)
        csv_path = os.path.join(session_dir, 'imported_gaze_data.csv')
        df.to_csv(csv_path, index=False)
        
        # Generate heatmaps
        print("Generating heatmaps...")
        heatmaps = generate_heatmaps_from_data(
            formatted_gaze_data,
            session_dir,
            state.current_video_path,
            state.video_info,
            state.scenes
        )
        
        # Generate trajectories
        print("Generating trajectories...")
        trajectories = generate_gaze_trajectories(
            formatted_gaze_data,
            session_dir,
            state.current_video_path,
            state.video_info,
            state.scenes
        )
        
        # Generate reports
        print("Generating reports...")
        reporter = ReportGenerator(
            session_dir=session_dir,
            gaze_data=formatted_gaze_data,
            video_info=state.video_info,
            scenes=state.scenes,
            participant_name="Imported Data",
            tracking_mode=f"Imported Data (Offset: {state.frame_offset} frames)"
        )
        
        excel_path = reporter.generate_excel_report()
        pdf_path = reporter.generate_pdf_report(heatmap_paths=heatmaps, trajectory_paths=trajectories)
        
        return jsonify({
            'success': True,
            'session_dir': session_dir,
            'excel_report': os.path.basename(excel_path),
            'pdf_report': os.path.basename(pdf_path),
            'gaze_points_processed': len(formatted_gaze_data)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Report generation failed: {str(e)}'}), 500

def generate_heatmaps_from_data(
    gaze_data: List[Dict[str, Any]], 
    session_dir: str, 
    video_path: str, 
    video_info: Dict[str, Any], 
    scenes: List[Dict[str, Any]]
) -> List[Dict[str, str]]:
    """Generate heatmap visualizations for all scenes from processed gaze data.
    
    Creates attention heatmaps showing where participants looked most frequently
    in each scene. Uses Gaussian blur for smooth visualization.
    
    Args:
        gaze_data: List of gaze point dictionaries with frame_num, gaze_x, gaze_y, scene_name.
        session_dir: Output directory for saving heatmap images.
        video_path: Path to source video file.
        video_info: Video metadata dict with width, height, fps.
        scenes: List of scene definitions with start/end frames and ROIs.
        
    Returns:
        List of heatmap metadata dictionaries with paths and filenames.
        
    Note:
        Uses vectorized NumPy operations for performance optimization.
        Heatmaps are normalized and overlaid on median frame from each scene.
    """
    try:
        gaze_dataframe = pd.DataFrame(gaze_data)
        video_width = video_info['width']
        video_height = video_info['height']
        
        video_capture = cv2.VideoCapture(video_path)
        if not video_capture.isOpened():
            print(f"Warning: Could not open video file: {video_path}")
            return []
        
        heatmap_metadata: List[Dict[str, str]] = []
        
        for scene in scenes:
            try:
                # Filter gaze data for current scene
                scene_gaze_data = gaze_dataframe[gaze_dataframe['scene_name'] == scene['name']]
                
                if scene_gaze_data.empty:
                    print(f"No gaze data for scene: {scene['name']}")
                    continue
                
                # Initialize heatmap array
                heatmap_array = np.zeros(HEATMAP_RESOLUTION, dtype=np.float32)
                
                # OPTIMIZATION: Vectorized heatmap accumulation
                valid_gaze_mask = scene_gaze_data['gaze_x'].notna() & scene_gaze_data['gaze_y'].notna()
                valid_gaze_points = scene_gaze_data[valid_gaze_mask]
                
                if len(valid_gaze_points) > 0:
                    # Extract and clamp coordinates
                    gaze_x_coords = np.clip(
                        valid_gaze_points['gaze_x'].values.astype(float),
                        0.0, 
                        float(video_width) - 0.001
                    )
                    gaze_y_coords = np.clip(
                        valid_gaze_points['gaze_y'].values.astype(float),
                        0.0, 
                        float(video_height) - 0.001
                    )
                    
                    # Vectorized scaling to heatmap resolution
                    scaled_x = np.clip(
                        np.round(gaze_x_coords * (HEATMAP_RESOLUTION[0] - 1) / (video_width - 1)).astype(int),
                        0,
                        HEATMAP_RESOLUTION[0] - 1
                    )
                    scaled_y = np.clip(
                        np.round(gaze_y_coords * (HEATMAP_RESOLUTION[1] - 1) / (video_height - 1)).astype(int),
                        0,
                        HEATMAP_RESOLUTION[1] - 1
                    )
                    
                    # Accumulate gaze points (vectorized)
                    np.add.at(heatmap_array, (scaled_y, scaled_x), 1)
                
                # Apply Gaussian blur for smooth visualization
                blurred_heatmap = cv2.GaussianBlur(heatmap_array, (0, 0), GAUSSIAN_BLUR_RADIUS)
                resized_heatmap = cv2.resize(
                    blurred_heatmap, 
                    (video_width, video_height), 
                    interpolation=cv2.INTER_LINEAR
                )
                
                # Extract background frame from scene median
                median_frame_number = int((scene['start_frame'] + scene['end_frame']) // 2)
                background_frame = None
                
                if video_capture.isOpened():
                    video_capture.set(cv2.CAP_PROP_POS_FRAMES, median_frame_number)
                    frame_read_success, video_frame = video_capture.read()
                    if frame_read_success:
                        background_frame = cv2.cvtColor(video_frame, cv2.COLOR_BGR2RGB)
                
                if background_frame is None:
                    background_frame = np.zeros((video_height, video_width, 3), dtype=np.uint8)
                
                # Create visualization
                display_name = scene.get('custom_name') or scene['name']
                filename_safe_name = display_name.replace(' ', '_').replace('/', '_')
                
                fig = plt.figure(figsize=(video_width / 100, video_height / 100), dpi=100)
                plt.imshow(background_frame)
                plt.imshow(resized_heatmap, cmap='jet', alpha=0.6, interpolation='bilinear')
                plt.title(f"Heatmap - {display_name}", fontsize=14, fontweight='bold')
                plt.axis('off')
                
                heatmap_output_path = os.path.join(session_dir, f"heatmap_{filename_safe_name}.png")
                plt.savefig(heatmap_output_path, bbox_inches='tight', dpi=100)
                plt.close(fig)
                
                heatmap_metadata.append({
                    'scene_name': scene['name'],
                    'scene_custom_name': scene.get('custom_name', ''),
                    'display_name': display_name,
                    'path': heatmap_output_path,
                    'filename': os.path.basename(heatmap_output_path)
                })
                
                print(f"  ✓ Generated heatmap for {display_name}")
                
            except Exception as scene_error:
                print(f"  ⚠ Error generating heatmap for scene {scene.get('name', 'unknown')}: {scene_error}")
                continue
        
        video_capture.release()
        return heatmap_metadata
        
    except Exception as error:
        print(f"Critical error in heatmap generation: {error}")
        traceback.print_exc()
        return []

def generate_gaze_trajectories(
    gaze_data: List[Dict[str, Any]], 
    session_dir: str, 
    video_path: str, 
    video_info: Dict[str, Any], 
    scenes: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Generate gaze trajectory visualizations showing saccadic movements and fixations.
    
    Creates scanpath visualizations displaying eye movement patterns, including
    rapid saccades (jumps) and fixation points (sustained attention areas).
    
    Args:
        gaze_data: List of gaze point dictionaries.
        session_dir: Output directory for saving trajectory visualizations.
        video_path: Path to source video file.
        video_info: Video metadata dict with width, height.
        scenes: List of scene definitions.
        
    Returns:
        List of trajectory metadata with paths, filenames, and statistics.
        
    Note:
        Fixation detection uses spatial clustering with configurable radius
        and minimum duration thresholds for robust identification.
    """
    # Fixation detection constants
    FIXATION_RADIUS_PIXELS = 50  # Maximum distance for points in same fixation
    FIXATION_MIN_FRAMES = 3  # Minimum frames to classify as fixation
    
    try:
        gaze_dataframe = pd.DataFrame(gaze_data)
        video_width = video_info['width']
        video_height = video_info['height']
        
        video_capture = cv2.VideoCapture(video_path)
        if not video_capture.isOpened():
            print(f"Warning: Could not open video file: {video_path}")
            return []
        
        trajectory_metadata: List[Dict[str, Any]] = []
        
        for scene in scenes:
            try:
                # Filter gaze data for current scene
                scene_gaze_data = gaze_dataframe[gaze_dataframe['scene_name'] == scene['name']]
                
                if scene_gaze_data.empty:
                    print(f"No gaze data for scene: {scene['name']}")
                    continue
                
                # Extract valid gaze points
                valid_gaze_mask = scene_gaze_data['gaze_x'].notna() & scene_gaze_data['gaze_y'].notna()
                valid_gaze_data = scene_gaze_data[valid_gaze_mask].copy()
                
                if len(valid_gaze_data) < 2:
                    print(f"Insufficient gaze points for trajectory in scene: {scene['name']}")
                    continue
                
                # FIXATION DETECTION: Spatial clustering algorithm
                fixations: List[Dict[str, Any]] = []
                current_fixation_points: List[Tuple[float, float]] = []
                
                for _, gaze_row in valid_gaze_data.iterrows():
                    gaze_x = float(gaze_row['gaze_x'])
                    gaze_y = float(gaze_row['gaze_y'])
                    
                    if not current_fixation_points:
                        # Start new fixation cluster
                        current_fixation_points.append((gaze_x, gaze_y))
                    else:
                        # Calculate centroid of current fixation
                        fixation_center_x = np.mean([pt[0] for pt in current_fixation_points])
                        fixation_center_y = np.mean([pt[1] for pt in current_fixation_points])
                        
                        # Calculate Euclidean distance to fixation center
                        distance_to_center = np.sqrt(
                            (gaze_x - fixation_center_x)**2 + (gaze_y - fixation_center_y)**2
                        )
                        
                        if distance_to_center < FIXATION_RADIUS_PIXELS:
                            # Point belongs to current fixation
                            current_fixation_points.append((gaze_x, gaze_y))
                        else:
                            # Save current fixation if it meets minimum duration
                            if len(current_fixation_points) >= FIXATION_MIN_FRAMES:
                                fixations.append({
                                    'x': np.mean([pt[0] for pt in current_fixation_points]),
                                    'y': np.mean([pt[1] for pt in current_fixation_points]),
                                    'duration': len(current_fixation_points)
                                })
                            # Start new fixation cluster
                            current_fixation_points = [(gaze_x, gaze_y)]
                
                # Process final fixation
                if len(current_fixation_points) >= FIXATION_MIN_FRAMES:
                    fixations.append({
                        'x': np.mean([pt[0] for pt in current_fixation_points]),
                        'y': np.mean([pt[1] for pt in current_fixation_points]),
                        'duration': len(current_fixation_points)
                    })
                
                # Extract background frame
                median_frame_number = int((scene['start_frame'] + scene['end_frame']) // 2)
                background_frame = None
                
                if video_capture.isOpened():
                    video_capture.set(cv2.CAP_PROP_POS_FRAMES, median_frame_number)
                    frame_read_success, video_frame = video_capture.read()
                    if frame_read_success:
                        background_frame = cv2.cvtColor(video_frame, cv2.COLOR_BGR2RGB)
                
                if background_frame is None:
                    background_frame = np.zeros((video_height, video_width, 3), dtype=np.uint8)
                
                # Create trajectory visualization
                display_name = scene.get('custom_name') or scene['name']
                filename_safe_name = display_name.replace(' ', '_').replace('/', '_')
                
                fig, ax = plt.subplots(figsize=(video_width / 100, video_height / 100), dpi=100)
                ax.imshow(background_frame, alpha=0.7)
                
                # Draw saccadic lines (eye movement paths)
                gaze_coordinates = valid_gaze_data[['gaze_x', 'gaze_y']].values
                if len(gaze_coordinates) > 1:
                    ax.plot(
                        gaze_coordinates[:, 0], gaze_coordinates[:, 1], 
                        color='cyan', linewidth=1.5, alpha=0.6, 
                        linestyle='-', marker='', label='Saccades'
                    )
                
                # Draw fixation points (size proportional to duration)
                if fixations:
                    fixation_x = [fix['x'] for fix in fixations]
                    fixation_y = [fix['y'] for fix in fixations]
                    fixation_sizes = [fix['duration'] * 10 for fix in fixations]  # Scale for visibility
                    
                    ax.scatter(
                        fixation_x, fixation_y, s=fixation_sizes, c='red', alpha=0.7, 
                        edgecolors='yellow', linewidths=2, label='Fixations'
                    )
                    
                    # Label fixations with sequence numbers
                    for fixation_index, fixation in enumerate(fixations, 1):
                        ax.text(
                            fixation['x'], fixation['y'], str(fixation_index), 
                            color='white', fontsize=8, fontweight='bold',
                            ha='center', va='center'
                        )
                
                # Draw ROI bounding boxes
                for roi in scene.get('rois', []):
                    roi_rectangle = MatplotlibRectangle(
                        (roi['x'], roi['y']), roi['width'], roi['height'],
                        fill=False, edgecolor='yellow', linewidth=2, linestyle='--'
                    )
                    ax.add_patch(roi_rectangle)
                    ax.text(
                        roi['x'], roi['y'] - 5, roi['label'],
                        color='yellow', fontsize=10, fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7)
                    )
                
                ax.set_title(f"Gaze Trajectory - {display_name}", fontsize=14, fontweight='bold')
                ax.axis('off')
                ax.legend(loc='upper right', fontsize=10)
                
                trajectory_output_path = os.path.join(session_dir, f"trajectory_{filename_safe_name}.png")
                plt.savefig(trajectory_output_path, bbox_inches='tight', dpi=100)
                plt.close(fig)
                
                trajectory_metadata.append({
                    'scene_name': scene['name'],
                    'scene_custom_name': scene.get('custom_name', ''),
                    'display_name': display_name,
                    'path': trajectory_output_path,
                    'filename': os.path.basename(trajectory_output_path),
                    'fixation_count': len(fixations),
                    'total_gaze_points': len(valid_gaze_data)
                })
                
                print(f"  ✓ Generated trajectory for {display_name} ({len(fixations)} fixations)")
                
            except Exception as scene_error:
                print(f"  ⚠ Error generating trajectory for scene {scene.get('name', 'unknown')}: {scene_error}")
                continue
        
        video_capture.release()
        return trajectory_metadata
        
    except Exception as error:
        print(f"Critical error in trajectory generation: {error}")
        traceback.print_exc()
        return []

@app.route('/api/processing/generate-heatmaps', methods=['POST'])
def generate_heatmaps():
    """Generate heatmaps for all scenes (post-processing architecture)."""
    try:
        if not state.session_dir:
            return jsonify({'error': 'No session directory'}), 400
        
        # Load gaze data from CSV file
        gaze_csv = os.path.join(state.session_dir, 'gaze_data.csv')
        if not os.path.exists(gaze_csv):
            return jsonify({'error': 'No gaze data file found. Run post-processing first.'}), 400
        
        df = pd.read_csv(gaze_csv)
        if df.empty:
            return jsonify({'error': 'No gaze data'}), 400
        
        video_width = state.video_info['width']
        video_height = state.video_info['height']
        
        # Open video once to grab median frames for backgrounds
        cap = cv2.VideoCapture(state.current_video_path)
        
        heatmaps = []
        
        for scene_idx, scene in enumerate(state.scenes):
            # Try filtering by frame_num first (for OBS mode and imported data)
            scene_frames = df[(df['frame_num'] >= scene['start_frame']) & 
                              (df['frame_num'] <= scene['end_frame'])]
            
            # If no frames found and scene_name column exists, try filtering by scene_name (for mouse tracking mode)
            if scene_frames.empty and 'scene_name' in df.columns:
                # Try matching by scene custom_name first, then by scene name
                scene_match_name = scene.get('custom_name') or scene['name']
                scene_frames = df[df['scene_name'] == scene_match_name]
                
                # If still empty, try the other name
                if scene_frames.empty:
                    alternate_name = scene['name'] if scene.get('custom_name') else scene.get('custom_name', '')
                    if alternate_name:
                        scene_frames = df[df['scene_name'] == alternate_name]
            
            if scene_frames.empty:
                continue
            
            # Create heatmap
            heatmap = np.zeros(HEATMAP_RESOLUTION, dtype=np.float32)
            
            for _, row in scene_frames.iterrows():
                try:
                    if pd.notna(row['gaze_x']) and pd.notna(row['gaze_y']):
                        # Clamp coordinates to valid range
                        gaze_x = float(row['gaze_x'])
                        gaze_y = float(row['gaze_y'])
                        
                        # Ensure coordinates are within video bounds (with safety margin)
                        gaze_x = max(0.0, min(gaze_x, float(video_width) - 0.001))
                        gaze_y = max(0.0, min(gaze_y, float(video_height) - 0.001))
                        
                        # Scale to heatmap resolution with rounding
                        x_scaled = int(round(gaze_x * (HEATMAP_RESOLUTION[0] - 1) / (video_width - 1)))
                        y_scaled = int(round(gaze_y * (HEATMAP_RESOLUTION[1] - 1) / (video_height - 1)))
                        
                        # Final safety clamp
                        x_scaled = max(0, min(x_scaled, HEATMAP_RESOLUTION[0] - 1))
                        y_scaled = max(0, min(y_scaled, HEATMAP_RESOLUTION[1] - 1))
                        
                        heatmap[y_scaled, x_scaled] += 1
                except (ValueError, IndexError) as e:
                    # Skip invalid gaze points
                    continue
            
            # Apply Gaussian blur
            heatmap = cv2.GaussianBlur(heatmap, (0, 0), GAUSSIAN_BLUR_RADIUS)

            # Resize heatmap to video resolution for correct scaling on screen
            heatmap_resized = cv2.resize(heatmap, (video_width, video_height), interpolation=cv2.INTER_LINEAR)

            # Grab median frame of the scene to use as semi-transparent background
            median_frame_num = int((scene['start_frame'] + scene['end_frame']) // 2)
            background = None
            if cap and cap.isOpened():
                cap.set(cv2.CAP_PROP_POS_FRAMES, median_frame_num)
                ret_bg, frame_bg = cap.read()
                if ret_bg:
                    background = cv2.cvtColor(frame_bg, cv2.COLOR_BGR2RGB)
            if background is None:
                background = np.zeros((video_height, video_width, 3), dtype=np.uint8)

            # Plot with video-sized canvas and transparent heatmap overlay
            display_name = scene.get('custom_name') or scene['name']
            filename_safe = (scene.get('custom_name') or scene['name']).replace(' ', '_').replace('/', '_')
            
            fig = plt.figure(figsize=(video_width / 100, video_height / 100), dpi=100)
            plt.imshow(background)
            plt.imshow(heatmap_resized, cmap='jet', alpha=0.6, interpolation='bilinear')
            plt.title(f"Heatmap - {display_name}")
            plt.axis('off')
            
            heatmap_path = os.path.join(state.session_dir, f"heatmap_{filename_safe}.png")
            plt.savefig(heatmap_path, bbox_inches='tight', dpi=100)
            plt.close(fig)
            
            heatmaps.append({
                'scene_name': scene['name'],
                'scene_custom_name': scene.get('custom_name', ''),
                'display_name': display_name,
                'path': heatmap_path,
                'filename': os.path.basename(heatmap_path)
            })
        
        if cap:
            cap.release()
        
        return jsonify({'heatmaps': heatmaps})
    
    except Exception as e:
        print(f"Error in generate_heatmaps: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Heatmap generation failed: {str(e)}'}), 500

@app.route('/api/processing/roi-statistics', methods=['POST'])
def generate_roi_statistics():
    """Generate ROI viewing statistics."""
    if not state.session_dir:
        return jsonify({'error': 'No session directory'}), 400
    
    # Load gaze data from CSV file
    gaze_csv = os.path.join(state.session_dir, 'gaze_data.csv')
    if not os.path.exists(gaze_csv):
        return jsonify({'error': 'No gaze data file found. Run post-processing first.'}), 400
    
    df = pd.read_csv(gaze_csv)
    if df.empty:
        return jsonify({'error': 'No gaze data'}), 400
    
    stats = []
    
    for scene_idx, scene in enumerate(state.scenes):
        # Try filtering by frame_num first
        scene_frames = df[(df['frame_num'] >= scene['start_frame']) & 
                          (df['frame_num'] <= scene['end_frame'])]
        
        # If no frames found and scene_name column exists, try filtering by scene_name (for mouse tracking mode)
        if scene_frames.empty and 'scene_name' in df.columns:
            scene_match_name = scene.get('custom_name') or scene['name']
            scene_frames = df[df['scene_name'] == scene_match_name]
            
            if scene_frames.empty:
                alternate_name = scene['name'] if scene.get('custom_name') else scene.get('custom_name', '')
                if alternate_name:
                    scene_frames = df[df['scene_name'] == alternate_name]
        
        if scene_frames.empty:
            continue
        
        roi_counts = scene_frames['roi_label'].value_counts()
        total = len(scene_frames)
        
        for roi in scene['rois']:
            count = roi_counts.get(roi['label'], 0)
            percentage = (count / total * 100) if total > 0 else 0
            
            display_name = scene.get('custom_name') or scene['name']
            
            stats.append({
                'scene': scene['name'],
                'custom_name': scene.get('custom_name', ''),
                'display_name': display_name,
                'roi_label': roi['label'],
                'gaze_count': int(count),
                'percentage': round(percentage, 2),
                'total_frames': int(total)
            })
    
    # Save statistics
    stats_df = pd.DataFrame(stats)
    stats_path = os.path.join(state.session_dir, 'roi_statistics.csv')
    stats_df.to_csv(stats_path, index=False)
    
    return jsonify({'statistics': stats, 'file': stats_path})

@app.route('/api/process_roi', methods=['POST'])
def process_roi():
    """
    Process ROI regions from video frames and return statistics.
    
    Expected JSON payload:
    {
        "video_path": "path/to/video.mp4",
        "rois": [
            {"x": 100, "y": 100, "width": 200, "height": 150, "label": "ROI1"},
            ...
        ],
        "gaze_data": [  // Optional
            {"frame": 0, "x": 250, "y": 200},
            ...
        ],
        "start_frame": 0,  // Optional
        "end_frame": null,  // Optional, null = all frames
        "analysis_type": "both"  // 'intensity', 'gaze_hits', or 'both'
    }
    
    Returns per-frame statistics including mean pixel intensity and gaze hit counts.
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'video_path' not in data or 'rois' not in data:
            return jsonify({'error': 'Missing required fields: video_path and rois'}), 400
        
        video_path = data['video_path']
        rois = data['rois']
        gaze_data = data.get('gaze_data', [])
        start_frame = data.get('start_frame', 0)
        end_frame = data.get('end_frame', None)
        analysis_type = data.get('analysis_type', 'both')
        
        # Validate video path
        if not os.path.exists(video_path):
            # Try relative to uploaded_videos directory
            video_path = os.path.join(UPLOAD_FOLDER, video_path)
            if not os.path.exists(video_path):
                return jsonify({'error': f'Video file not found: {video_path}'}), 404
        
        # Validate ROIs
        if not isinstance(rois, list) or len(rois) == 0:
            return jsonify({'error': 'ROIs must be a non-empty list'}), 400
        
        for roi in rois:
            required_keys = ['x', 'y', 'width', 'height', 'label']
            if not all(key in roi for key in required_keys):
                return jsonify({'error': f'Each ROI must have: {required_keys}'}), 400
        
        # Convert gaze_data to dictionary for fast lookup
        gaze_dict = {}
        if gaze_data:
            for gaze in gaze_data:
                frame_num = gaze.get('frame', gaze.get('frame_num', -1))
                if frame_num >= 0:
                    if frame_num not in gaze_dict:
                        gaze_dict[frame_num] = []
                    gaze_dict[frame_num].append({
                        'x': gaze.get('x', gaze.get('gaze_x', 0)),
                        'y': gaze.get('y', gaze.get('gaze_y', 0))
                    })
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return jsonify({'error': 'Failed to open video file'}), 500
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Set frame range
        if end_frame is None or end_frame > total_frames:
            end_frame = total_frames - 1
        
        if start_frame < 0 or start_frame > end_frame:
            cap.release()
            return jsonify({'error': 'Invalid frame range'}), 400
        
        # Jump to start frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Process frames
        results = []
        frame_count = start_frame
        
        while frame_count <= end_frame:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_result = {
                'frame': frame_count,
                'timestamp': frame_count / fps if fps > 0 else 0,
                'rois': []
            }
            
            # Process each ROI
            for roi in rois:
                roi_result = {
                    'label': roi['label'],
                    'x': roi['x'],
                    'y': roi['y'],
                    'width': roi['width'],
                    'height': roi['height']
                }
                
                # Extract ROI region from frame
                x, y, w, h = roi['x'], roi['y'], roi['width'], roi['height']
                
                # Ensure ROI is within frame bounds
                frame_h, frame_w = frame.shape[:2]
                x1 = max(0, min(x, frame_w - 1))
                y1 = max(0, min(y, frame_h - 1))
                x2 = max(0, min(x + w, frame_w))
                y2 = max(0, min(y + h, frame_h))
                
                if x2 <= x1 or y2 <= y1:
                    # Invalid ROI bounds
                    roi_result['error'] = 'ROI out of bounds'
                    frame_result['rois'].append(roi_result)
                    continue
                
                roi_crop = frame[y1:y2, x1:x2]
                
                # Calculate mean pixel intensity
                if analysis_type in ['intensity', 'both']:
                    # RGB means
                    mean_b, mean_g, mean_r = cv2.mean(roi_crop)[:3]
                    roi_result['mean_intensity'] = {
                        'r': round(mean_r, 2),
                        'g': round(mean_g, 2),
                        'b': round(mean_b, 2),
                        'avg': round((mean_r + mean_g + mean_b) / 3, 2)
                    }
                    
                    # Grayscale mean
                    gray_crop = cv2.cvtColor(roi_crop, cv2.COLOR_BGR2GRAY)
                    roi_result['mean_intensity']['gray'] = round(np.mean(gray_crop), 2)
                
                # Check gaze hits
                if analysis_type in ['gaze_hits', 'both'] and frame_count in gaze_dict:
                    hits = 0
                    for gaze in gaze_dict[frame_count]:
                        gx, gy = gaze['x'], gaze['y']
                        if x <= gx <= x + w and y <= gy <= y + h:
                            hits += 1
                    roi_result['gaze_hits'] = hits
                    roi_result['gaze_total'] = len(gaze_dict[frame_count])
                
                frame_result['rois'].append(roi_result)
            
            results.append(frame_result)
            frame_count += 1
        
        cap.release()
        
        # Calculate summary statistics
        summary = {
            'total_frames_processed': len(results),
            'start_frame': start_frame,
            'end_frame': frame_count - 1,
            'fps': fps,
            'roi_summaries': []
        }
        
        # Aggregate stats per ROI
        for roi in rois:
            roi_summary = {
                'label': roi['label'],
                'total_gaze_hits': 0,
                'avg_intensity': {'r': 0, 'g': 0, 'b': 0, 'gray': 0, 'avg': 0}
            }
            
            intensity_sum = {'r': 0, 'g': 0, 'b': 0, 'gray': 0, 'avg': 0}
            valid_frames = 0
            
            for frame_result in results:
                for roi_result in frame_result['rois']:
                    if roi_result['label'] == roi['label']:
                        if 'gaze_hits' in roi_result:
                            roi_summary['total_gaze_hits'] += roi_result['gaze_hits']
                        
                        if 'mean_intensity' in roi_result:
                            for key in intensity_sum:
                                intensity_sum[key] += roi_result['mean_intensity'][key]
                            valid_frames += 1
            
            # Calculate averages
            if valid_frames > 0:
                for key in intensity_sum:
                    roi_summary['avg_intensity'][key] = round(intensity_sum[key] / valid_frames, 2)
            
            summary['roi_summaries'].append(roi_summary)
        
        return jsonify({
            'success': True,
            'summary': summary,
            'frames': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/processing/overlay-video', methods=['POST'])
def create_overlay_video():
    """Create overlay video with ROI boxes, gaze point, and ROI label."""
    if not state.session_dir or not state.current_video_path:
        return jsonify({'error': 'No session or video'}), 400
    
    # Load gaze data from CSV file
    gaze_csv = os.path.join(state.session_dir, 'gaze_data.csv')
    if not os.path.exists(gaze_csv):
        return jsonify({'error': 'No gaze data file found. Run post-processing first.'}), 400
    
    df = pd.read_csv(gaze_csv)
    if df.empty:
        return jsonify({'error': 'No gaze data'}), 400
    
    # Open input video
    cap = cv2.VideoCapture(state.current_video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Output video
    output_path = os.path.join(state.session_dir, 'overlay_video.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_num = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Find current scene for this frame
        current_scene = None
        for scene in state.scenes:
            if scene['start_frame'] <= frame_num <= scene['end_frame']:
                current_scene = scene
                break
        
        # Draw ROI boxes for current scene
        if current_scene and 'rois' in current_scene:
            for roi in current_scene['rois']:
                # Draw ROI rectangle
                x, y, w, h = int(roi['x']), int(roi['y']), int(roi['width']), int(roi['height'])
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 0), 2)  # Yellow boxes
                
                # Draw ROI label
                label = roi['label']
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                cv2.rectangle(frame, (x, y - 25), (x + label_size[0] + 5, y), (255, 255, 0), -1)
                cv2.putText(frame, label, (x + 3, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        # Find gaze data for this frame with interpolation for missing frames
        frame_data = df[df['frame_num'] == frame_num]
        gaze_x, gaze_y = None, None
        
        if not frame_data.empty:
            # Exact frame data exists
            row = frame_data.iloc[0]
            if pd.notna(row['gaze_x']) and pd.notna(row['gaze_y']):
                gaze_x = int(row['gaze_x'])
                gaze_y = int(row['gaze_y'])
        else:
            # Interpolate from any previous frames (hold last known position across gap)
            nearby_data = df[df['frame_num'] <= frame_num]
            nearby_data = nearby_data.sort_values('frame_num', ascending=False)
            
            if not nearby_data.empty:
                # Use most recent known gaze position from any previous frame
                for _, row in nearby_data.iterrows():
                    if pd.notna(row['gaze_x']) and pd.notna(row['gaze_y']):
                        gaze_x = int(row['gaze_x'])
                        gaze_y = int(row['gaze_y'])
                        break  # Found most recent valid gaze point
        
        # Draw gaze point if available
        if gaze_x is not None and gaze_y is not None:
            # Clamp to frame bounds
            gaze_x = max(0, min(gaze_x, width - 1))
            gaze_y = max(0, min(gaze_y, height - 1))
            
            # Only draw if within bounds
            if 0 <= gaze_x < width and 0 <= gaze_y < height:
                cv2.circle(frame, (gaze_x, gaze_y), 30, (0, 0, 255), 3)  # Red outer circle
                cv2.circle(frame, (gaze_x, gaze_y), 5, (0, 255, 0), -1)   # Green center dot
                
                # Draw ROI label if gaze is in ROI
                if current_scene and 'rois' in current_scene:
                    for roi in current_scene['rois']:
                        x, y, w, h = roi['x'], roi['y'], roi['width'], roi['height']
                        if x <= gaze_x <= x + w and y <= gaze_y <= y + h:
                            # Draw current ROI label near gaze point
                            label = f"ROI: {roi['label']}"
                            cv2.putText(frame, label, (gaze_x + 10, gaze_y - 10), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                            break
        
        out.write(frame)
        frame_num += 1
    
    cap.release()
    out.release()
    
    return jsonify({
        'success': True,
        'output_path': output_path,
        'filename': os.path.basename(output_path)
    })

@app.route('/api/processing/overlay-heatmap-video', methods=['POST'])
def create_overlay_heatmap_video():
    """Create per-scene videos with transparent heatmap overlay on original video."""
    if not state.session_dir or not state.current_video_path:
        return jsonify({'error': 'No session or video'}), 400
    
    try:
        # Load gaze data from CSV file
        gaze_csv = os.path.join(state.session_dir, 'gaze_data.csv')
        if not os.path.exists(gaze_csv):
            return jsonify({'error': 'No gaze data file found. Run post-processing first.'}), 400
        
        df = pd.read_csv(gaze_csv)
        if df.empty:
            return jsonify({'error': 'No gaze data'}), 400
        
        video_width = state.video_info['width']
        video_height = state.video_info['height']
        
        # Open input video
        cap = cv2.VideoCapture(state.current_video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        output_videos = []
        
        # Process each scene
        for scene_idx, scene in enumerate(state.scenes):
            # Try filtering by frame_num first (for OBS mode and imported data)
            scene_frames = df[(df['frame_num'] >= scene['start_frame']) & 
                              (df['frame_num'] <= scene['end_frame'])]
            
            # If no frames found and scene_name column exists, try filtering by scene_name (for mouse tracking mode)
            if scene_frames.empty and 'scene_name' in df.columns:
                scene_match_name = scene.get('custom_name') or scene['name']
                scene_frames = df[df['scene_name'] == scene_match_name]
                
                if scene_frames.empty:
                    alternate_name = scene['name'] if scene.get('custom_name') else scene.get('custom_name', '')
                    if alternate_name:
                        scene_frames = df[df['scene_name'] == alternate_name]
            
            if scene_frames.empty:
                continue
            
            # Create heatmap
            heatmap = np.zeros(HEATMAP_RESOLUTION, dtype=np.float32)
            
            for _, row in scene_frames.iterrows():
                try:
                    if pd.notna(row['gaze_x']) and pd.notna(row['gaze_y']):
                        gaze_x = float(row['gaze_x'])
                        gaze_y = float(row['gaze_y'])
                        
                        gaze_x = max(0.0, min(gaze_x, float(video_width) - 0.001))
                        gaze_y = max(0.0, min(gaze_y, float(video_height) - 0.001))
                        
                        x_scaled = int(round(gaze_x * (HEATMAP_RESOLUTION[0] - 1) / (video_width - 1)))
                        y_scaled = int(round(gaze_y * (HEATMAP_RESOLUTION[1] - 1) / (video_height - 1)))
                        
                        x_scaled = max(0, min(x_scaled, HEATMAP_RESOLUTION[0] - 1))
                        y_scaled = max(0, min(y_scaled, HEATMAP_RESOLUTION[1] - 1))
                        
                        heatmap[y_scaled, x_scaled] += 1
                except (ValueError, IndexError):
                    continue
            
            # Apply Gaussian blur
            heatmap = cv2.GaussianBlur(heatmap, (0, 0), GAUSSIAN_BLUR_RADIUS)
            
            # Normalize heatmap to 0-255 for display
            heatmap_normalized = cv2.normalize(heatmap, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            
            # Resize heatmap to match video frame
            heatmap_resized = cv2.resize(heatmap_normalized, (width, height), interpolation=cv2.INTER_LINEAR)
            
            # Apply jet colormap (rainbow/thermal)
            heatmap_colored = cv2.applyColorMap(heatmap_resized, cv2.COLORMAP_JET)
            
            # Create output video for this scene
            display_name = scene.get('custom_name') or scene['name']
            filename_safe = (scene.get('custom_name') or scene['name']).replace(' ', '_').replace('/', '_')
            output_path = os.path.join(state.session_dir, f"heatmap_overlay_{filename_safe}.mp4")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # Re-open video and process frames for this scene
            cap.set(cv2.CAP_PROP_POS_FRAME_COUNT, 0)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            frame_num = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Only process frames in this scene
                if frame_num < scene['start_frame'] or frame_num > scene['end_frame']:
                    frame_num += 1
                    continue
                
                # Blend heatmap overlay (50% transparent) with original frame
                overlay = cv2.addWeighted(frame, 0.5, heatmap_colored, 0.5, 0)
                
                # Draw ROI boxes on the overlay
                for roi in scene['rois']:
                    x, y, w, h = int(roi['x']), int(roi['y']), int(roi['width']), int(roi['height'])
                    cv2.rectangle(overlay, (x, y), (x + w, y + h), (255, 255, 0), 2)
                    
                    # Draw ROI label
                    label = roi['label']
                    label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                    cv2.rectangle(overlay, (x, y - 25), (x + label_size[0] + 5, y), (255, 255, 0), -1)
                    cv2.putText(overlay, label, (x + 3, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                
                out.write(overlay)
                frame_num += 1
            
            out.release()
            
            output_videos.append({
                'scene_name': scene['name'],
                'scene_custom_name': scene.get('custom_name', ''),
                'display_name': display_name,
                'path': output_path,
                'filename': os.path.basename(output_path)
            })
        
        cap.release()
        
        return jsonify({'videos': output_videos})
    
    except Exception as e:
        print(f"Error in create_overlay_heatmap_video: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Heatmap overlay video generation failed: {str(e)}'}), 500

# ==============================================================================
# WEBSOCKET HANDLERS
# ==============================================================================

@socketio.on('connect')
def handle_websocket_connect() -> None:
    """Handle WebSocket client connection event.
    
    Emits status message to confirm successful connection to client.
    """
    print("✓ WebSocket client connected")
    emit('status', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_websocket_disconnect() -> None:
    """Handle WebSocket client disconnection event."""
    print("✓ WebSocket client disconnected")

@socketio.on('record_frame')
def handle_record_frame(data: Dict[str, Any]) -> None:
    """Record frame timestamp synchronization data for post-processing.
    
    Synchronizes advertisement video playback with OBS recording timestamps
    to enable accurate gaze data alignment during post-processing.
    
    Args:
        data: Dictionary containing:
            - frame_num: Current frame number in advertisement video
            - timestamp: Video playback timestamp in seconds
    """
    if not state.recording_active:
        return
    
    try:
        ad_frame_number = data.get('frame_num')
        ad_playback_timestamp = data.get('timestamp')
        
        if ad_frame_number is None or ad_playback_timestamp is None:
            print("⚠ Invalid frame sync data received")
            return
        
        # Calculate OBS recording timestamp (relative to recording start)
        obs_recording_timestamp = time.time() - state.recording_start_time
        
        # Store synchronization entry
        sync_entry = {
            'ad_frame_num': int(ad_frame_number),
            'ad_timestamp': float(ad_playback_timestamp),
            'obs_timestamp': obs_recording_timestamp
        }
        
        state.recording_timestamps.append(sync_entry)
        
        # Send acknowledgment to client
        emit('timestamp_recorded', {
            'ad_frame': ad_frame_number,
            'synced': True
        })
        
    except (ValueError, TypeError) as error:
        print(f"⚠ Error recording frame sync: {error}")

@socketio.on('record_mouse_gaze')
def handle_record_mouse_gaze(data: Dict[str, Any]) -> None:
    """Record mouse position as gaze data in fallback mode.
    
    When eye tracking hardware is unavailable, mouse position serves as
    a fallback gaze proxy for ROI interaction analysis.
    
    Args:
        data: Dictionary containing:
            - frame_num: Current video frame number
            - mouse_x: Mouse X coordinate in video pixel space
            - mouse_y: Mouse Y coordinate in video pixel space
            - roi_label: Label of ROI under mouse cursor
            - scene_name: Name of current scene
            - scene_custom_name: Custom scene name (optional)
    """
    if not state.recording_active or not state.use_mouse_fallback:
        return
    
    try:
        ad_frame_number = data.get('frame_num')
        mouse_x_coord = data.get('mouse_x')
        mouse_y_coord = data.get('mouse_y')
        roi_label = data.get('roi_label', 'background')
        scene_name = data.get('scene_name', 'unknown')
        scene_custom_name = data.get('scene_custom_name', '')
        
        if ad_frame_number is None or mouse_x_coord is None or mouse_y_coord is None:
            print("⚠ Invalid mouse gaze data received")
            return
        
        # Record mouse position as gaze proxy
        gaze_entry = {
            'ad_frame': int(ad_frame_number),
            'gaze_x': float(mouse_x_coord),
            'gaze_y': float(mouse_y_coord),
            'roi_label': str(roi_label),
            'scene_name': str(scene_name),
            'scene_custom_name': str(scene_custom_name),
            'timestamp': time.time() - state.recording_start_time
        }
        
        state.mouse_gaze_data.append(gaze_entry)
        
    except (ValueError, TypeError) as error:
        print(f"⚠ Error recording mouse gaze: {error}")

# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("Starting Flask server...")
    print("Open browser: http://localhost:5000")
    print("=" * 80 + "\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)

