from flask import Flask, render_template, request, jsonify, send_from_directory, Response
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import pandas as pd
import os
import json
import time
import datetime
import threading
from werkzeug.utils import secure_filename
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import glob

# Post-processing modules
from gaze_post_processor import GazePostProcessor
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


def _download_youtube_video(url):
    """Download a YouTube video and return the absolute mp4 path."""
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

    if not filename.endswith('.mp4'):
        filename = filename.rsplit('.', 1)[0] + '.mp4'

    return filename

print("=" * 80)
print("VIDEO ROI WEB APP - Flask + Vue.js")
print("=" * 80)

# ==============================================================================
# FLASK APP SETUP
# ==============================================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'video-roi-demo-secret'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max video upload
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Disable template caching
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable static file caching
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

def is_path_within_project(filepath):
    """Validate that a file path is within the project directory."""
    try:
        abs_path = os.path.abspath(filepath)
        return abs_path.startswith(SCRIPT_DIR)
    except:
        return False

def is_tobii_overlay_running():
    """Check if Tobii Ghost overlay (SSOverlay.exe) is running."""
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() == 'ssoverlay.exe':
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    except ImportError:
        # psutil not installed, try Windows tasklist command
        try:
            import subprocess
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq SSOverlay.exe'],
                capture_output=True,
                text=True,
                timeout=2
            )
            return 'SSOverlay.exe' in result.stdout
        except:
            # Cannot check, assume it might be running
            print("Warning: Cannot check if Tobii Ghost overlay is running (install psutil for better detection)")
            return None  # Unknown state

# Virtual camera
VIRTUAL_CAMERA_INDEX = 0

# Gaze detection params
HOUGH_PARAM1 = 50
HOUGH_PARAM2 = 13
MIN_RADIUS = 65
MAX_RADIUS = 80

# OBS settings
OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = ""

# Heatmap settings
HEATMAP_RESOLUTION = (192, 108)
GAUSSIAN_BLUR_RADIUS = 15

print("Flask app initialized.")
print(f"  - OBS control: {'Available' if OBS_AVAILABLE else 'Not available'}")
print(f"  - YouTube download: {'Available' if YTDLP_AVAILABLE else 'Not available'}")

# ==============================================================================
# GLOBAL STATE
# ==============================================================================

class AppState:
    """Global application state."""
    def __init__(self):
        self.current_video_path = None
        self.video_info = None
        self.scenes = []  # [{start_frame, end_frame, name, rois: []}]
        self.recording_active = False
        self.session_dir = None
        self.obs_controller = None
        self.current_workspace_file = None  # Track loaded workspace file
        self.last_updated = None  # Track last save timestamp
        
        # New post-processing architecture
        self.recording_timestamps = []  # [{ad_frame_num, ad_timestamp, obs_timestamp}]
        self.recording_start_time = None
        self.obs_recording_path = None
        self.participant_name = None
        self.processing_progress = 0
        self.processing_thread = None
        self.processing_status = 'Idle'
        self.processing_files = {}
        
        # Import mode data
        self.imported_gaze_data = None  # List of {frame_num, gaze_x, gaze_y} from imported CSV
        self.frame_offset = 0  # Frame offset between gaze data and video
        self.tracking_mode = 'Live Recording'  # 'Live Recording' or 'Imported Data'
        
        # Calibration
        self.calibration_H = None  # Homography matrix for gaze calibration

state = AppState()

# Test Eye Gaze state
class TestState:
    def __init__(self):
        self.active = False
        self.gaze_cap = None
        self.total_frames = 0
        self.detect_frames = 0
        self.roi_counts = defaultdict(int)

test_state = TestState()

# ==============================================================================
# OBS CONTROLLER
# ==============================================================================

class OBSController:
    def __init__(self):
        self.ws = None
        self.connected = False
        self.recording_path = None
        self.last_error = None
        self.recording_start_time = None  # Track when recording started
    
    def connect(self):
        if not OBS_AVAILABLE:
            self.last_error = "obs-websocket-py library not installed"
            return False
        try:
            self.ws = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
            self.ws.connect()
            self.connected = True
            self.last_error = None
            return True
        except Exception as e:
            self.last_error = str(e)
            print(f"OBS Connection Error: {e}")
            return False
    
    def disconnect(self):
        if self.ws and self.connected:
            try:
                self.ws.disconnect()
                self.connected = False
            except:
                pass
    
    def start_recording(self):
        if self.connected:
            try:
                self.ws.call(obs_requests.StartRecord())
                self.recording_start_time = time.time()  # Track start time
                return True
            except:
                return False
        return False
    
    def stop_recording(self, target_dir=None):
        """Stop recording and copy output file to project folder.
        
        Args:
            target_dir: Directory to copy recording to (usually session folder)
        """
        if self.connected:
            try:
                self.ws.call(obs_requests.StopRecord())
                # Wait a bit for file to be written
                time.sleep(1)
                # Find recording in Windows Videos folder
                external_path = self._find_latest_obs_recording()
                
                if external_path and target_dir:
                    # Copy to project folder
                    import shutil
                    filename = os.path.basename(external_path)
                    internal_path = os.path.join(target_dir, filename)
                    shutil.copy2(external_path, internal_path)
                    self.recording_path = internal_path
                    print(f"✓ OBS recording copied to project: {internal_path}")
                    # Optionally delete external file to save space
                    try:
                        os.remove(external_path)
                        print(f"  → Removed external file: {external_path}")
                    except:
                        pass
                else:
                    self.recording_path = external_path
                
                return True
            except Exception as e:
                print(f"Error stopping OBS recording: {e}")
                return False
        return False
    
    def _find_latest_obs_recording(self):
        """
        Find the OBS recording created during this session.
        Pattern: eyegaze-%CCYY-%MM-%DD %hh-%mm-%ss.mp4
        Only accepts files created after recording_start_time.
        """
        videos_folder = os.path.join(os.path.expanduser('~'), 'Videos')
        pattern = os.path.join(videos_folder, 'eyegaze-*.mp4')
        
        # Find all matching files
        files = glob.glob(pattern)
        if not files:
            return None
        
        # Filter files created after recording started (with 5-second tolerance)
        if self.recording_start_time:
            tolerance = 5  # Allow 5 seconds before start time for clock drift
            valid_files = [
                f for f in files 
                if os.path.getctime(f) >= (self.recording_start_time - tolerance)
            ]
            if not valid_files:
                print(f"Warning: No OBS recordings found created after {datetime.datetime.fromtimestamp(self.recording_start_time)}")
                return None
            files = valid_files
        
        # Get the most recent file from valid candidates
        latest_file = max(files, key=os.path.getctime)
        print(f"✓ Found OBS recording: {os.path.basename(latest_file)}")
        return latest_file

# ==============================================================================
# GAZE DETECTION
# ==============================================================================

def detect_gaze_hough(frame):
    """Detect gaze using Hough Circle Transform (adaptive radii)."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 1.5)

    h, w = gray.shape[:2]
    base = int(min(w, h) * 0.035)
    min_r = max(8, int(base * 0.6))
    max_r = max(min_r + 6, int(base * 1.8))
    min_dist = max(30, int(min(w, h) * 0.25))

    circles = cv2.HoughCircles(
        gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=min_dist,
        param1=HOUGH_PARAM1, param2=HOUGH_PARAM2,
        minRadius=min_r, maxRadius=max_r
    )

    if circles is not None and len(circles[0]) > 0:
        circle = np.uint16(np.around(circles[0, 0]))
        return (int(circle[0]), int(circle[1]))
    return None

def _get_normalized_rois():
    """Return ROIs normalized to [0,1] for the first scene (or empty)."""
    rois = []
    if not state.video_info or not state.scenes:
        return rois
    vw, vh = state.video_info['width'], state.video_info['height']
    scene = state.scenes[0]
    for idx, r in enumerate(scene.get('rois', []), start=1):
        rois.append({
            'id': idx,
            'name': r['label'],
            'color': '#%02x%02x%02x' % (255, 180, 0),
            'x': float(r['x']) / max(1, vw),
            'y': float(r['y']) / max(1, vh),
            'width': float(r['width']) / max(1, vw),
            'height': float(r['height']) / max(1, vh)
        })
    return rois

def _roi_hit(video_x, video_y):
    """Return (roi_name, roi_id) for point in video coordinates."""
    if not state.video_info or not state.scenes:
        return None, 0
    scene = state.scenes[0]
    for idx, r in enumerate(scene.get('rois', []), start=1):
        x, y, w, h = r['x'], r['y'], r['width'], r['height']
        if x <= video_x <= x + w and y <= video_y <= y + h:
            return r['label'], idx
    return None, 0

def _map_gaze_to_video(gx, gy, src_w, src_h):
    """Scale gaze from camera frame to video resolution."""
    if not state.video_info:
        return gx, gy
    dst_w, dst_h = state.video_info['width'], state.video_info['height']
    # If calibrated, use homography
    if state.calibration_H is not None:
        pt = np.array([gx, gy, 1.0], dtype=np.float32)
        H = state.calibration_H.astype(np.float32)
        mapped = H @ pt
        if mapped[2] != 0:
            mx = float(mapped[0] / mapped[2])
            my = float(mapped[1] / mapped[2])
        else:
            mx, my = float(mapped[0]), float(mapped[1])
        mx = max(0.0, min(mx, float(dst_w - 1)))
        my = max(0.0, min(my, float(dst_h - 1)))
        return int(round(mx)), int(round(my))
    if src_w <= 1 or src_h <= 1 or dst_w <= 1 or dst_h <= 1:
        return int(gx), int(gy)
    x_scaled = int(round(gx * (dst_w - 1) / (src_w - 1)))
    y_scaled = int(round(gy * (dst_h - 1) / (src_h - 1)))
    x_scaled = max(0, min(dst_w - 1, x_scaled))
    y_scaled = max(0, min(dst_h - 1, y_scaled))
    return x_scaled, y_scaled

def find_roi_at_position(rois, x, y):
    """Find ROI containing position."""
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
def test_gaze_page():
    """Serve the Eye Gaze Test page using current scene ROIs."""
    rois = _get_normalized_rois()
    return render_template('test_roi_gaze.html', rois=rois)

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
def api_test_reset():
    test_state.total_frames = 0
    test_state.detect_frames = 0
    test_state.roi_counts = defaultdict(int)
    return jsonify({'success': True})

@app.route('/api/gaze')
def api_test_gaze():
    """Return latest gaze detection and simple stats for test page."""
    if not test_state.active or not test_state.gaze_cap:
        return jsonify({'gaze': None, 'fps': 0, 'detection_rate': 0, 'total_frames': test_state.total_frames, 'stats': dict(test_state.roi_counts)})

    ret, frame = test_state.gaze_cap.read()
    if not ret:
        test_state.total_frames += 1
        return jsonify({'gaze': None, 'fps': 0, 'detection_rate': (100.0 * test_state.detect_frames / max(1, test_state.total_frames)), 'total_frames': test_state.total_frames, 'stats': dict(test_state.roi_counts)})

    fh, fw = frame.shape[:2]
    pos = detect_gaze_hough(frame)
    roi_name = None
    roi_id = 0
    if pos:
        test_state.detect_frames += 1
        # Map to video space to compute ROI hits
        vx, vy = _map_gaze_to_video(pos[0], pos[1], fw, fh)
        roi_name, roi_id = _roi_hit(vx, vy)
        if roi_name:
            test_state.roi_counts[roi_name] += 1

    test_state.total_frames += 1
    det_rate = 100.0 * test_state.detect_frames / max(1, test_state.total_frames)

    gaze_payload = None
    if pos:
        gaze_payload = {
            'x': pos[0],
            'y': pos[1],
            'frame_width': fw,
            'frame_height': fh,
            'roi': roi_name,
            'roi_id': roi_id
        }

    return jsonify({
        'gaze': gaze_payload,
        'fps': 0.0,
        'detection_rate': det_rate,
        'total_frames': test_state.total_frames,
        'stats': dict(test_state.roi_counts)
    })

@app.route('/api/save_results', methods=['POST'])
def api_test_save_results():
    """Save test stats to CSV in sessions folder."""
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    out_path = os.path.join(SESSIONS_FOLDER, f'test_gaze_stats_{ts}.csv')
    try:
        rows = [{'roi_label': k, 'count': v} for k, v in test_state.roi_counts.items()]
        df = pd.DataFrame(rows)
        df.to_csv(out_path, index=False)
        return jsonify({'success': True, 'filename': out_path})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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
                video_path = _download_youtube_video(youtube_url)
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


@app.route('/api/workspace/<path:filename>', methods=['GET'])
def get_workspace(filename):
    """Load a workspace JSON file from projects directory by filename."""
    workspace_name = secure_filename(os.path.basename(filename))

    if not workspace_name:
        return jsonify({'success': False, 'error': 'Invalid workspace filename'}), 400

    if not workspace_name.endswith('.json'):
        workspace_name += '.json'

    workspace_path = os.path.join(PROJECT_FOLDER, workspace_name)

    if not is_path_within_project(workspace_path):
        return jsonify({'success': False, 'error': 'Invalid workspace file path'}), 403

    if not os.path.exists(workspace_path):
        return jsonify({'success': False, 'error': f'Workspace not found: {workspace_name}'}), 404

    try:
        with open(workspace_path, 'r', encoding='utf-8') as workspace_file:
            workspace_data = json.load(workspace_file)
    except json.JSONDecodeError:
        return jsonify({'success': False, 'error': f'Invalid JSON in workspace file: {workspace_name}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to read workspace: {str(e)}'}), 500

    if not isinstance(workspace_data, dict) or 'video_info' not in workspace_data or 'scenes' not in workspace_data:
        return jsonify({'success': False, 'error': 'Invalid workspace format'}), 400

    state.current_workspace_file = workspace_path

    return jsonify({
        'success': True,
        'workspace_file': workspace_name,
        'workspace': workspace_data
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

@app.route('/api/import/auto-detect-gaze', methods=['POST'])
def auto_detect_gaze_import():
    """
    Auto-detect gaze coordinates from eye gaze video.
    Process the video frame-by-frame using Hough Circle Transform.
    """
    try:
        data = request.json
        gaze_video_filename = data.get('gaze_video_filename')
        stimulus_video_info = data.get('stimulus_video_info')
        
        if not gaze_video_filename or not stimulus_video_info:
            return jsonify({'success': False, 'error': 'Missing required parameters'})
        
        # Get full path to gaze video
        gaze_video_path = os.path.join(UPLOAD_FOLDER, gaze_video_filename)
        
        if not os.path.exists(gaze_video_path):
            return jsonify({'success': False, 'error': 'Gaze video file not found'})
        
        print(f"\n{'='*80}")
        print(f"AUTO-DETECTING GAZE FROM VIDEO: {gaze_video_filename}")
        print(f"{'='*80}")
        
        # Open gaze video
        cap = cv2.VideoCapture(gaze_video_path)
        if not cap.isOpened():
            return jsonify({'success': False, 'error': 'Cannot open gaze video'})
        
        gaze_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        gaze_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        gaze_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        stimulus_width = stimulus_video_info['width']
        stimulus_height = stimulus_video_info['height']
        
        print(f"Gaze video: {gaze_width}x{gaze_height}, {total_frames} frames @ {gaze_fps}fps")
        print(f"Stimulus video: {stimulus_width}x{stimulus_height}")
        
        # Process each frame
        gaze_data = []
        detected_count = 0
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect gaze position using Hough Circle Transform
            gaze_pos = detect_gaze_hough(frame)
            
            if gaze_pos:
                detected_count += 1
                # Map gaze coordinates from gaze video to stimulus video resolution
                # Simple proportional scaling
                mapped_x = int(round(gaze_pos[0] * stimulus_width / gaze_width))
                mapped_y = int(round(gaze_pos[1] * stimulus_height / gaze_height))
                
                # Clamp to stimulus video bounds
                mapped_x = max(0, min(stimulus_width - 1, mapped_x))
                mapped_y = max(0, min(stimulus_height - 1, mapped_y))
                
                gaze_data.append({
                    'frame': frame_idx,
                    'gaze_x': mapped_x,
                    'gaze_y': mapped_y,
                    'detection_confidence': 1.0
                })
            else:
                # No detection for this frame
                gaze_data.append({
                    'frame': frame_idx,
                    'gaze_x': None,
                    'gaze_y': None,
                    'detection_confidence': 0.0
                })
            
            frame_idx += 1
            
            # Progress logging every 100 frames
            if frame_idx % 100 == 0:
                print(f"Processed {frame_idx}/{total_frames} frames ({(frame_idx/total_frames)*100:.1f}%), detection rate: {(detected_count/frame_idx)*100:.1f}%")
        
        cap.release()
        
        detection_rate = (detected_count / total_frames * 100) if total_frames > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"AUTO-DETECTION COMPLETE!")
        print(f"  Total frames: {total_frames}")
        print(f"  Detected: {detected_count} ({detection_rate:.1f}%)")
        print(f"{'='*80}\n")
        
        return jsonify({
            'success': True,
            'gaze_data': gaze_data,
            'total_frames': total_frames,
            'total_points': detected_count,
            'detection_rate': detection_rate,
            'gaze_video_resolution': f"{gaze_width}x{gaze_height}",
            'stimulus_video_resolution': f"{stimulus_width}x{stimulus_height}"
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

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
        
        # Try OBS if available
        obs_started = False
        
        if OBS_AVAILABLE:
            try:
                # Check if Tobii Ghost overlay is running
                tobii_running = is_tobii_overlay_running()
                if tobii_running is False:
                    print("⚠ Tobii Ghost overlay (SSOverlay.exe) not detected")
                elif tobii_running is None:
                    print("⚠ Cannot verify Tobii Ghost overlay status - attempting OBS anyway")
                
                # Try to start OBS recording if Tobii is running or status is unknown
                if tobii_running is not False:
                    state.obs_controller = OBSController()
                    if state.obs_controller.connect() and state.obs_controller.start_recording():
                        obs_started = True
                        print("✓ OBS recording started successfully")
                        if tobii_running is None:
                            print("  Note: Tobii Ghost overlay status could not be verified")
            except Exception as obs_err:
                print(f"⚠ OBS start failed: {obs_err}")
        
        # Initialize recording state
        state.recording_timestamps = []
        state.recording_start_time = time.time()
        state.recording_active = True
        
        return jsonify({
            'success': True,
            'session_dir': state.session_dir,
            'participant_name': state.participant_name
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
    
    # Stop OBS and get recording path
    obs_file_found = False
    if state.obs_controller:
        try:
            state.obs_controller.stop_recording()
            state.obs_recording_path = state.obs_controller.recording_path
            if state.obs_recording_path and os.path.exists(state.obs_recording_path):
                obs_file_found = True
            state.obs_controller.disconnect()
        except Exception as e:
            print(f"Error stopping OBS: {e}")
            # Continue even if OBS fails - allow manual import
        finally:
            state.obs_controller = None
    
    # Save timestamp data
    if state.recording_timestamps:
        df = pd.DataFrame(state.recording_timestamps)
        csv_path = os.path.join(state.session_dir, 'recording_timestamps.csv')
        df.to_csv(csv_path, index=False)
    
    # If OBS recording not found automatically, suggest manual import
    if not obs_file_found:
        return jsonify({
            'success': True,
            'warning': 'OBS recording file not found automatically',
            'message': 'Please import the eyegaze-*.mp4 file manually using the "Import OBS Recording" button',
            'timestamps_recorded': len(state.recording_timestamps),
            'session_dir': state.session_dir,
            'ready_for_processing': False,
            'manual_import_required': True
        })
    
    return jsonify({
        'success': True,
        'timestamps_recorded': len(state.recording_timestamps),
        'obs_recording_path': state.obs_recording_path,
        'session_dir': state.session_dir,
        'ready_for_processing': True,
        'manual_import_required': False
    })

@app.route('/api/processing/start-post-processing', methods=['POST'])
def start_post_processing():
    """Start post-processing in background thread."""
    # Check if we have OBS recording data to process
    if not state.obs_recording_path or not state.session_dir:
        return jsonify({'error': 'No recording data available'}), 400
    
    if state.processing_thread and state.processing_thread.is_alive():
        return jsonify({'error': 'Processing already in progress'}), 400
    
    def process_worker():
        try:
            print("\n" + "="*80)
            print("Starting Post-Processing Pipeline...")
            print("="*80)
            
            state.processing_progress = 10
            state.processing_status = "Processing gaze detection..."
            
            # Create post-processor for OBS video
            processor = GazePostProcessor(
                session_dir=state.session_dir,
                obs_video_path=state.obs_recording_path,
                ad_video_info=state.video_info,
                scenes=state.scenes,
                timestamps=state.recording_timestamps
            )
            
            state.processing_progress = 20
            # Process video
            result = processor.process()
            
            if result['success']:
                state.processing_progress = 50
                state.processing_status = "Generating heatmaps..."
                
                # Generate heatmaps
                print("\nGenerating heatmaps...")
                heatmaps = generate_heatmaps_from_data(
                    result['gaze_data'],
                    state.session_dir,
                    state.current_video_path,
                    state.video_info,
                    state.scenes
                )
                
                state.processing_progress = 65
                state.processing_status = "Generating gaze trajectories..."
                
                # Generate gaze trajectories
                print("\nGenerating gaze trajectories...")
                trajectories = generate_gaze_trajectories(
                    result['gaze_data'],
                    state.session_dir,
                    state.current_video_path,
                    state.video_info,
                    state.scenes
                )
                
                state.processing_progress = 80
                state.processing_status = "Generating reports..."
                
                # Generate reports
                print("\nGenerating reports...")
                reporter = ReportGenerator(
                    session_dir=state.session_dir,
                    gaze_data=result['gaze_data'],
                    video_info=state.video_info,
                    scenes=state.scenes,
                    participant_name=state.participant_name or "Participant",
                    tracking_mode="Eye Tracking (OBS)"
                )
                
                excel_path = reporter.generate_excel_report()
                state.processing_progress = 90
                
                pdf_path = reporter.generate_pdf_report(heatmap_paths=heatmaps, trajectory_paths=trajectories)
                
                state.processing_progress = 100
                state.processing_status = "Complete!"
                state.processing_files = {
                    'excel': os.path.basename(excel_path) if excel_path else None,
                    'pdf': os.path.basename(pdf_path) if pdf_path else None,
                    'heatmaps': [h['filename'] for h in heatmaps],
                    'trajectories': [t['filename'] for t in trajectories]
                }
                
                print("\n" + "="*80)
                print("Post-Processing Complete!")
                print(f"Excel Report: {excel_path}")
                print(f"PDF Report: {pdf_path}")
                print(f"Heatmaps: {len(heatmaps)}")
                print(f"Trajectories: {len(trajectories)}")
                print("="*80 + "\n")
            else:
                print("Post-processing failed!")
                state.processing_progress = -1
                state.processing_status = "Failed: Processing returned unsuccessful"
                
        except Exception as e:
            print(f"Error in post-processing: {e}")
            import traceback
            traceback.print_exc()
            state.processing_progress = -1  # Error state
            state.processing_status = f"Error: {str(e)}"
    
    # Start processing in background
    state.processing_progress = 0
    state.processing_thread = threading.Thread(target=process_worker, daemon=True)
    state.processing_thread.start()
    
    return jsonify({'success': True, 'message': 'Post-processing started'})

@app.route('/api/processing/progress', methods=['GET'])
def get_processing_progress():
    """Get current post-processing progress with detailed status."""
    is_alive = state.processing_thread and state.processing_thread.is_alive()
    is_complete = state.processing_progress >= 100
    has_error = state.processing_progress < 0
    
    return jsonify({
        'progress': state.processing_progress,
        'status': getattr(state, 'processing_status', 'Initializing...'),
        'is_processing': is_alive,
        'complete': is_complete,
        'error': has_error,
        'files': getattr(state, 'processing_files', {}),
        'session_dir': state.session_dir
    })

@app.route('/api/reports/list', methods=['GET'])
def list_reports():
    """List available reports in session directory with file details."""
    if not state.session_dir or not os.path.exists(state.session_dir):
        return jsonify({'reports': [], 'session_dir': None})
    
    reports = []
    for filename in os.listdir(state.session_dir):
        if filename.endswith(('.xlsx', '.pdf', '.mp4', '.png', '.csv')):
            filepath = os.path.join(state.session_dir, filename)
            stat = os.stat(filepath)
            reports.append({
                'filename': filename,
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified': datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'type': os.path.splitext(filename)[1][1:]  # extension without dot
            })
    
    # Sort by type then name
    reports.sort(key=lambda x: (x['type'], x['filename']))
    
    return jsonify({
        'reports': reports,
        'session_dir': state.session_dir,
        'total_files': len(reports)
    })

@app.route('/api/reports/download/<filename>')
def download_report(filename):
    """Download a specific report file."""
    if not state.session_dir:
        return jsonify({'error': 'No session active'}), 404
    
    return send_from_directory(state.session_dir, filename, as_attachment=True)

@app.route('/api/processing/verify-completion', methods=['GET'])
def verify_processing_completion():
    """Verify that processing completed successfully by checking for required files."""
    if not state.session_dir or not os.path.exists(state.session_dir):
        return jsonify({
            'complete': False,
            'error': 'No session directory',
            'files_found': {}
        })
    
    # Check for expected files
    expected_files = {
        'excel': None,
        'pdf': None,
        'gaze_csv': None,
        'heatmaps': [],
        'trajectories': []
    }
    
    files_in_session = os.listdir(state.session_dir)
    
    for filename in files_in_session:
        if filename.endswith('.xlsx') and 'report_' in filename:
            expected_files['excel'] = filename
        elif filename.endswith('.pdf') and 'report_' in filename:
            expected_files['pdf'] = filename
        elif filename.endswith('.csv') and 'gaze_data' in filename:
            expected_files['gaze_csv'] = filename
        elif filename.startswith('Heatmap_') and filename.endswith('.png'):
            expected_files['heatmaps'].append(filename)
        elif filename.startswith('Trajectory_') and filename.endswith('.png'):
            expected_files['trajectories'].append(filename)
    
    # Determine if processing is complete
    is_complete = (
        expected_files['excel'] is not None and
        expected_files['pdf'] is not None and
        len(expected_files['heatmaps']) > 0 and
        len(expected_files['trajectories']) > 0
    )
    
    return jsonify({
        'complete': is_complete,
        'files_found': expected_files,
        'session_dir': state.session_dir,
        'total_files': len(files_in_session)
    })

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

def generate_heatmaps_from_data(gaze_data, session_dir, video_path, video_info, scenes):
    """Generate heatmaps for all scenes from processed gaze data."""
    df = pd.DataFrame(gaze_data)
    video_width = video_info['width']
    video_height = video_info['height']
    
    cap = cv2.VideoCapture(video_path)
    heatmaps = []
    
    for scene_idx, scene in enumerate(scenes):
        scene_frames = df[df['scene_name'] == scene['name']]
        
        if scene_frames.empty:
            continue
        
        # Filter valid gaze points (same as trajectory)
        valid_gaze = scene_frames[scene_frames['gaze_x'].notna() & scene_frames['gaze_y'].notna()].copy()
        
        if len(valid_gaze) < 1:
            continue
        
        # Create heatmap at full video resolution (like trajectory uses)
        heatmap = np.zeros((video_height, video_width), dtype=np.float32)
        
        for _, row in valid_gaze.iterrows():
            try:
                # Use coordinates directly (same as trajectory)
                gaze_x = float(row['gaze_x'])
                gaze_y = float(row['gaze_y'])
                
                # Clamp to video bounds
                gaze_x = max(0, min(gaze_x, video_width - 1))
                gaze_y = max(0, min(gaze_y, video_height - 1))
                
                # Convert to integer pixel coordinates
                px = int(round(gaze_x))
                py = int(round(gaze_y))
                
                # Accumulate gaze points
                heatmap[py, px] += 1
            except (ValueError, IndexError) as e:
                continue
        
        # Apply Gaussian blur for smooth heatmap
        heatmap = cv2.GaussianBlur(heatmap, (0, 0), GAUSSIAN_BLUR_RADIUS)
        
        # Normalize for better visualization
        if heatmap.max() > 0:
            heatmap = heatmap / heatmap.max()
        
        # Grab median frame
        median_frame_num = int((scene['start_frame'] + scene['end_frame']) // 2)
        background = None
        if cap and cap.isOpened():
            cap.set(cv2.CAP_PROP_POS_FRAMES, median_frame_num)
            ret_bg, frame_bg = cap.read()
            if ret_bg:
                background = cv2.cvtColor(frame_bg, cv2.COLOR_BGR2RGB)
        if background is None:
            background = np.zeros((video_height, video_width, 3), dtype=np.uint8)
        
        # Plot with consistent naming format
        custom_name = scene.get('custom_name') or scene['name']
        display_name = f"Heatmap - Scene {scene_idx + 1} - {custom_name}"
        filename_safe = f"Scene_{scene_idx + 1}_{custom_name}".replace(' ', '_').replace('/', '_')
        
        fig, ax = plt.subplots(figsize=(video_width / 100, video_height / 100), dpi=100)
        ax.imshow(background, alpha=0.7)
        ax.imshow(heatmap, cmap='jet', alpha=0.6, interpolation='bilinear')
        ax.set_title(display_name, fontsize=14, fontweight='bold')
        ax.axis('off')
        
        heatmap_path = os.path.join(session_dir, f"Heatmap_{filename_safe}.png")
        plt.savefig(heatmap_path, bbox_inches='tight', dpi=100)
        plt.close(fig)
        
        # Verify file was created
        if os.path.exists(heatmap_path):
            file_size = os.path.getsize(heatmap_path)
            print(f"✓ Heatmap saved: {os.path.basename(heatmap_path)} ({file_size} bytes, {len(valid_gaze)} gaze points)")
        else:
            print(f"✗ ERROR: Heatmap file not created: {heatmap_path}")
        
        heatmaps.append({
            'scene_index': scene_idx + 1,
            'scene_name': scene['name'],
            'scene_custom_name': scene.get('custom_name', ''),
            'display_name': display_name,
            'path': heatmap_path,
            'filename': os.path.basename(heatmap_path),
            'gaze_points_count': len(valid_gaze)
        })
    
    if cap:
        cap.release()
    
    return heatmaps

def generate_gaze_trajectories(gaze_data, session_dir, video_path, video_info, scenes):
    """
    Generate gaze trajectory visualizations showing saccadic movements and fixation points.
    
    Args:
        gaze_data: List of gaze data entries
        session_dir: Output directory
        video_path: Path to video file
        video_info: Video metadata
        scenes: Scene definitions
    
    Returns:
        List of trajectory visualization paths
    """
    df = pd.DataFrame(gaze_data)
    video_width = video_info['width']
    video_height = video_info['height']
    
    cap = cv2.VideoCapture(video_path)
    trajectories = []
    
    # Fixation detection parameters
    FIXATION_RADIUS = 50  # pixels
    FIXATION_MIN_DURATION = 3  # minimum frames to be considered a fixation
    
    for scene_idx, scene in enumerate(scenes):
        scene_frames = df[df['scene_name'] == scene['name']]
        
        if scene_frames.empty:
            continue
        
        # Filter valid gaze points
        valid_gaze = scene_frames[scene_frames['gaze_x'].notna() & scene_frames['gaze_y'].notna()].copy()
        
        if len(valid_gaze) < 2:
            continue
        
        # Detect fixations using spatial clustering
        fixations = []
        current_fixation = []
        
        for idx, row in valid_gaze.iterrows():
            gaze_x = float(row['gaze_x'])
            gaze_y = float(row['gaze_y'])
            
            if not current_fixation:
                current_fixation.append((gaze_x, gaze_y))
            else:
                # Check if point is within fixation radius
                fix_x = np.mean([p[0] for p in current_fixation])
                fix_y = np.mean([p[1] for p in current_fixation])
                distance = np.sqrt((gaze_x - fix_x)**2 + (gaze_y - fix_y)**2)
                
                if distance < FIXATION_RADIUS:
                    current_fixation.append((gaze_x, gaze_y))
                else:
                    # End current fixation if it meets minimum duration
                    if len(current_fixation) >= FIXATION_MIN_DURATION:
                        fixations.append({
                            'x': np.mean([p[0] for p in current_fixation]),
                            'y': np.mean([p[1] for p in current_fixation]),
                            'duration': len(current_fixation)
                        })
                    # Start new fixation
                    current_fixation = [(gaze_x, gaze_y)]
        
        # Add last fixation
        if len(current_fixation) >= FIXATION_MIN_DURATION:
            fixations.append({
                'x': np.mean([p[0] for p in current_fixation]),
                'y': np.mean([p[1] for p in current_fixation]),
                'duration': len(current_fixation)
            })
        
        # Get background frame
        median_frame_num = int((scene['start_frame'] + scene['end_frame']) // 2)
        background = None
        if cap and cap.isOpened():
            cap.set(cv2.CAP_PROP_POS_FRAMES, median_frame_num)
            ret_bg, frame_bg = cap.read()
            if ret_bg:
                background = cv2.cvtColor(frame_bg, cv2.COLOR_BGR2RGB)
        if background is None:
            background = np.zeros((video_height, video_width, 3), dtype=np.uint8)
        
        # Create trajectory visualization
        custom_name = scene.get('custom_name') or scene['name']
        display_name = f"Gaze Trajectory - Scene {scene_idx + 1} - {custom_name}"
        filename_safe = f"Scene_{scene_idx + 1}_{custom_name}".replace(' ', '_').replace('/', '_')
        
        fig, ax = plt.subplots(figsize=(video_width / 100, video_height / 100), dpi=100)
        ax.imshow(background, alpha=0.7)
        
        # Draw saccadic lines (trajectory paths)
        gaze_points = valid_gaze[['gaze_x', 'gaze_y']].values
        if len(gaze_points) > 1:
            ax.plot(gaze_points[:, 0], gaze_points[:, 1], 
                   color='cyan', linewidth=1.5, alpha=0.6, 
                   linestyle='-', marker='', label='Saccades')
        
        # Draw fixation points with size proportional to duration
        if fixations:
            fix_x = [f['x'] for f in fixations]
            fix_y = [f['y'] for f in fixations]
            fix_sizes = [f['duration'] * 10 for f in fixations]  # Scale for visibility
            
            ax.scatter(fix_x, fix_y, s=fix_sizes, c='red', alpha=0.7, 
                      edgecolors='yellow', linewidths=2, label='Fixations')
            
            # Number the fixations in order
            for i, fix in enumerate(fixations, 1):
                ax.text(fix['x'], fix['y'], str(i), 
                       color='white', fontsize=8, fontweight='bold',
                       ha='center', va='center')
        
        # Draw ROI boxes
        for roi in scene.get('rois', []):
            rect = plt.Rectangle((roi['x'], roi['y']), roi['width'], roi['height'],
                                fill=False, edgecolor='yellow', linewidth=2, linestyle='--')
            ax.add_patch(rect)
            ax.text(roi['x'], roi['y'] - 5, roi['label'],
                   color='yellow', fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))
        
        ax.set_title(display_name, fontsize=14, fontweight='bold')
        ax.axis('off')
        ax.legend(loc='upper right', fontsize=10)
        
        trajectory_path = os.path.join(session_dir, f"Trajectory_{filename_safe}.png")
        plt.savefig(trajectory_path, bbox_inches='tight', dpi=100)
        plt.close(fig)
        
        # Verify file was created
        if os.path.exists(trajectory_path):
            file_size = os.path.getsize(trajectory_path)
            print(f"✓ Trajectory saved: {os.path.basename(trajectory_path)} ({file_size} bytes)")
        else:
            print(f"✗ ERROR: Trajectory file not created: {trajectory_path}")
        
        trajectories.append({
            'scene_index': scene_idx + 1,
            'scene_name': scene['name'],
            'scene_custom_name': scene.get('custom_name', ''),
            'display_name': display_name,
            'path': trajectory_path,
            'filename': os.path.basename(trajectory_path),
            'fixation_count': len(fixations),
            'total_gaze_points': len(valid_gaze)
        })
    
    if cap:
        cap.release()
    
    return trajectories

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
            
            # If no frames found and scene_name column exists, try filtering by scene_name
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
            custom_name = scene.get('custom_name') or scene['name']
            display_name = f"Heatmap - Scene {scene_idx + 1} - {custom_name}"
            filename_safe = f"Scene_{scene_idx + 1}_{custom_name}".replace(' ', '_').replace('/', '_')
            
            fig = plt.figure(figsize=(video_width / 100, video_height / 100), dpi=100)
            plt.imshow(background)
            plt.imshow(heatmap_resized, cmap='jet', alpha=0.6, interpolation='bilinear')
            plt.title(display_name)
            plt.axis('off')
            
            heatmap_path = os.path.join(state.session_dir, f"Heatmap_{filename_safe}.png")
            plt.savefig(heatmap_path, bbox_inches='tight', dpi=100)
            plt.close(fig)
            
            heatmaps.append({
                'scene_index': scene_idx + 1,
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
        
        # If no frames found and scene_name column exists, try filtering by scene_name
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
            
            # If no frames found and scene_name column exists, try filtering by scene_name
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
            custom_name = scene.get('custom_name') or scene['name']
            filename_safe = f"Scene_{scene_idx + 1}_{custom_name}".replace(' ', '_').replace('/', '_')
            output_path = os.path.join(state.session_dir, f"Heatmap_Overlay_{filename_safe}.mp4")
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
def handle_connect():
    """Client connected."""
    print("WebSocket client connected")
    emit('status', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected."""
    print("WebSocket client disconnected")

@socketio.on('record_frame')
def handle_record_frame(data):
    """Record timestamp synchronization data (new post-processing architecture)."""
    if not state.recording_active:
        return
    
    ad_frame_num = data.get('frame_num')
    ad_timestamp = data.get('timestamp')  # Video playback timestamp
    
    # Calculate OBS recording timestamp
    obs_timestamp = time.time() - state.recording_start_time
    
    # Record sync data
    sync_entry = {
        'ad_frame_num': ad_frame_num,
        'ad_timestamp': ad_timestamp,
        'obs_timestamp': obs_timestamp
    }
    
    state.recording_timestamps.append(sync_entry)
    
    # Send acknowledgment to client
    emit('timestamp_recorded', {
        'ad_frame': ad_frame_num,
        'synced': True
    })

# ==============================================================================
# SETTINGS & DIAGNOSTICS
# ==============================================================================

@app.route('/settings')
def settings_page():
    """Serve settings and diagnostics page."""
    return render_template('settings.html')

@app.route('/api/settings/test-obs', methods=['POST'])
def test_obs_connection():
    """Test OBS WebSocket connection."""
    if not OBS_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'obs-websocket-py library not installed',
            'message': 'Please install: pip install obs-websocket-py'
        })
    
    try:
        test_ws = obsws(OBS_HOST, OBS_PORT, OBS_PASSWORD)
        test_ws.connect()
        
        # Get OBS version info
        version = test_ws.call(obs_requests.GetVersion())
        
        test_ws.disconnect()
        
        return jsonify({
            'success': True,
            'message': 'OBS connection successful',
            'obs_version': version.getObsVersion(),
            'websocket_version': version.getObsWebsocketVersion()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Connection failed: {str(e)}'
        })

@app.route('/api/settings/test-tobii', methods=['POST'])
def test_tobii_overlay():
    """Test if Tobii Ghost overlay is running."""
    result = is_tobii_overlay_running()
    
    if result is True:
        return jsonify({
            'success': True,
            'running': True,
            'message': 'Tobii Ghost overlay (SSOverlay.exe) is running'
        })
    elif result is False:
        return jsonify({
            'success': True,
            'running': False,
            'message': 'Tobii Ghost overlay (SSOverlay.exe) is NOT running'
        })
    else:
        return jsonify({
            'success': True,
            'running': None,
            'message': 'Unable to detect overlay status (install psutil for better detection)'
        })

@app.route('/api/settings/test-virtual-camera', methods=['POST'])
def test_virtual_camera():
    """Test if virtual camera is accessible."""
    try:
        cap = cv2.VideoCapture(VIRTUAL_CAMERA_INDEX)
        if not cap.isOpened():
            return jsonify({
                'success': False,
                'error': 'Virtual camera not accessible',
                'message': f'Cannot open camera index {VIRTUAL_CAMERA_INDEX}'
            })
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return jsonify({
                'success': False,
                'error': 'Cannot read from virtual camera',
                'message': 'Camera opened but no frame detected'
            })
        
        h, w = frame.shape[:2]
        return jsonify({
            'success': True,
            'message': 'Virtual camera is working',
            'resolution': f'{w}x{h}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Error testing camera: {str(e)}'
        })

@app.route('/api/settings/test-gaze-detection', methods=['POST'])
def test_gaze_detection():
    """Test gaze detection on current virtual camera frame."""
    try:
        cap = cv2.VideoCapture(VIRTUAL_CAMERA_INDEX)
        if not cap.isOpened():
            return jsonify({
                'success': False,
                'error': 'Virtual camera not accessible'
            })
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return jsonify({
                'success': False,
                'error': 'Cannot read frame from camera'
            })
        
        # Try detecting gaze
        gaze_pos = detect_gaze_hough(frame)
        
        if gaze_pos:
            fh, fw = frame.shape[:2]
            return jsonify({
                'success': True,
                'detected': True,
                'message': 'Gaze (Tobii comet) detected successfully!',
                'position': {'x': int(gaze_pos[0]), 'y': int(gaze_pos[1])},
                'frame_size': {'width': fw, 'height': fh}
            })
        else:
            return jsonify({
                'success': True,
                'detected': False,
                'message': 'No gaze marker detected in current frame'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Error during detection: {str(e)}'
        })

@app.route('/api/settings/list-videos-folder', methods=['GET'])
def list_videos_folder():
    """List eyegaze-*.mp4 files in user's Videos folder."""
    try:
        videos_folder = os.path.join(os.path.expanduser('~'), 'Videos')
        pattern = os.path.join(videos_folder, 'eyegaze-*.mp4')
        
        files = glob.glob(pattern)
        file_list = []
        
        for f in files:
            stat = os.stat(f)
            file_list.append({
                'filename': os.path.basename(f),
                'path': f,
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': datetime.datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                'modified': datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Sort by creation time (newest first)
        file_list.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({
            'success': True,
            'files': file_list,
            'videos_folder': videos_folder
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Error listing files: {str(e)}'
        })

@app.route('/api/settings/import-obs-recording', methods=['POST'])
def import_obs_recording():
    """Import an OBS recording file to session folder."""
    data = request.json
    source_path = data.get('file_path')
    
    if not source_path or not os.path.exists(source_path):
        return jsonify({
            'success': False,
            'error': 'File not found'
        })
    
    if not state.session_dir:
        # Create a temporary session if none exists
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        state.session_dir = os.path.join(SESSIONS_FOLDER, f"imported_session_{timestamp}")
        os.makedirs(state.session_dir, exist_ok=True)
    
    try:
        import shutil
        filename = os.path.basename(source_path)
        dest_path = os.path.join(state.session_dir, filename)
        
        # Copy file
        shutil.copy2(source_path, dest_path)
        
        # Store in state
        state.obs_recording_path = dest_path
        
        return jsonify({
            'success': True,
            'message': f'File imported successfully',
            'filename': filename,
            'destination': dest_path,
            'session_dir': state.session_dir
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Error importing file: {str(e)}'
        })

@app.route('/api/settings/list-obs-recordings', methods=['GET'])
def list_obs_recordings():
    """List available OBS recording files from Videos folder."""
    try:
        videos_folder = os.path.join(os.path.expanduser('~'), 'Videos')
        pattern = os.path.join(videos_folder, 'eyegaze-*.mp4')
        
        files = glob.glob(pattern)
        
        # Sort by creation time, newest first
        files_info = []
        for file_path in files:
            stat = os.stat(file_path)
            files_info.append({
                'path': file_path,
                'filename': os.path.basename(file_path),
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': datetime.datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            })
        
        files_info.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({
            'success': True,
            'files': files_info,
            'count': len(files_info),
            'videos_folder': videos_folder
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'files': []
        })

@app.route('/api/settings/update-config', methods=['POST'])
def update_config():
    """Update application configuration."""
    data = request.json
    
    global OBS_HOST, OBS_PORT, OBS_PASSWORD, VIRTUAL_CAMERA_INDEX
    global HOUGH_PARAM1, HOUGH_PARAM2, MIN_RADIUS, MAX_RADIUS
    global UPLOAD_FOLDER, SESSIONS_FOLDER, DOWNLOADED_FOLDER, PROJECT_FOLDER
    
    if 'obs_host' in data:
        OBS_HOST = data['obs_host']
    if 'obs_port' in data:
        OBS_PORT = int(data['obs_port'])
    if 'obs_password' in data:
        OBS_PASSWORD = data['obs_password']
    if 'virtual_camera_index' in data:
        VIRTUAL_CAMERA_INDEX = int(data['virtual_camera_index'])
    if 'hough_param1' in data:
        HOUGH_PARAM1 = int(data['hough_param1'])
    if 'hough_param2' in data:
        HOUGH_PARAM2 = int(data['hough_param2'])
    if 'min_radius' in data:
        MIN_RADIUS = int(data['min_radius'])
    if 'max_radius' in data:
        MAX_RADIUS = int(data['max_radius'])
    
    # Update folder paths
    if 'upload_folder' in data:
        new_path = data['upload_folder']
        if not os.path.isabs(new_path):
            new_path = os.path.join(SCRIPT_DIR, new_path)
        UPLOAD_FOLDER = new_path
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    if 'sessions_folder' in data:
        new_path = data['sessions_folder']
        if not os.path.isabs(new_path):
            new_path = os.path.join(SCRIPT_DIR, new_path)
        SESSIONS_FOLDER = new_path
        os.makedirs(SESSIONS_FOLDER, exist_ok=True)
    
    if 'downloaded_folder' in data:
        new_path = data['downloaded_folder']
        if not os.path.isabs(new_path):
            new_path = os.path.join(SCRIPT_DIR, new_path)
        DOWNLOADED_FOLDER = new_path
        os.makedirs(DOWNLOADED_FOLDER, exist_ok=True)
    
    if 'projects_folder' in data:
        new_path = data['projects_folder']
        if not os.path.isabs(new_path):
            new_path = os.path.join(SCRIPT_DIR, new_path)
        PROJECT_FOLDER = new_path
        os.makedirs(PROJECT_FOLDER, exist_ok=True)
    
    return jsonify({
        'success': True,
        'message': 'Settings updated',
        'current_settings': {
            'obs_host': OBS_HOST,
            'obs_port': OBS_PORT,
            'virtual_camera_index': VIRTUAL_CAMERA_INDEX,
            'hough_param1': HOUGH_PARAM1,
            'hough_param2': HOUGH_PARAM2,
            'min_radius': MIN_RADIUS,
            'max_radius': MAX_RADIUS,
            'upload_folder': UPLOAD_FOLDER,
            'sessions_folder': SESSIONS_FOLDER,
            'downloaded_folder': DOWNLOADED_FOLDER,
            'projects_folder': PROJECT_FOLDER
        }
    })

@app.route('/api/settings/get-config', methods=['GET'])
def get_config():
    """Get current application configuration."""
    return jsonify({
        'success': True,
        'settings': {
            'obs_host': OBS_HOST,
            'obs_port': OBS_PORT,
            'obs_password_set': bool(OBS_PASSWORD),
            'virtual_camera_index': VIRTUAL_CAMERA_INDEX,
            'hough_param1': HOUGH_PARAM1,
            'hough_param2': HOUGH_PARAM2,
            'min_radius': MIN_RADIUS,
            'max_radius': MAX_RADIUS,
            'upload_folder': UPLOAD_FOLDER,
            'sessions_folder': SESSIONS_FOLDER,
            'downloaded_folder': DOWNLOADED_FOLDER,
            'projects_folder': PROJECT_FOLDER
        }
    })

# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("Starting Flask server...")
    print("Open browser: http://localhost:5000")
    print("=" * 80 + "\n")
    
    # Local dev runner: Flask-SocketIO blocks Werkzeug unless explicitly allowed.
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False,
        allow_unsafe_werkzeug=True,
    )

