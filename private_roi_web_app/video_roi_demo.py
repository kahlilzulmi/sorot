"""
================================================================================
VIDEO ROI DEMO - Advertisement Eye Tracking Analysis Tool
================================================================================

GUI tool for analyzing eye gaze data on advertisement videos with:
- Manual scene splitting and ROI definition
- Real-time gaze recording via virtual camera
- Auto OBS recording control
- Post-processing: overlay video, bar charts, heatmaps

Author: Auto-generated
Date: 2026-01-06
================================================================================
"""

import cv2
import numpy as np
import pandas as pd
import os
import sys
import json
import time
import datetime
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle as MPLRectangle
import threading

# OBS WebSocket imports
try:
    from obswebsocket import obsws, requests as obs_requests
    OBS_AVAILABLE = True
except ImportError:
    OBS_AVAILABLE = False
    print("Warning: obswebsocket not installed. OBS auto-control disabled.")
    print("Install with: pip install obs-websocket-py")

# yt-dlp for YouTube downloads
try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False
    print("Warning: yt-dlp not installed. YouTube download disabled.")
    print("Install with: pip install yt-dlp")

print("=" * 80)
print("VIDEO ROI DEMO - Advertisement Eye Tracking Analysis")
print("=" * 80)

# ==============================================================================
# CONSTANTS
# ==============================================================================

# Virtual camera index (same as game3_with_recording.py)
VIRTUAL_CAMERA_INDEX = 0

# Downloaded videos directory
DOWNLOADED_VIDEOS_DIR = "downloaded_videos"

# Eye gaze detection parameters (Hough Circle Transform)
HOUGH_PARAM1 = 50
HOUGH_PARAM2 = 13
MIN_RADIUS = 70
MAX_RADIUS = 75

# OBS WebSocket settings
OBS_HOST = "localhost"
OBS_PORT_GAZE_ONLY = 4455  # OBS instance for eye gaze only (virtual camera source)
OBS_PORT_COMBINED = 4456   # OBS instance for combined view (recording)
OBS_PASSWORD = ""  # Leave empty if no password set

# OBS Scene names
OBS_SCENE_GAZE_ONLY = "Eye Gaze Only"  # Scene with only eye tracking camera
OBS_SCENE_COMBINED = "Combined View"   # Scene with both video and gaze

# Video processing settings
PREVIEW_WIDTH = 1280
PREVIEW_HEIGHT = 720
HEATMAP_RESOLUTION = (192, 108)  # 1920x1080 / 10
GAUSSIAN_BLUR_RADIUS = 15

# Color schemes (RGB for CV2, reverse for matplotlib)
COLOR_ROI_ACTIVE = (0, 255, 255)  # Cyan
COLOR_ROI_INACTIVE = (128, 128, 128)  # Gray
COLOR_GAZE_CURSOR = (0, 255, 0)  # Green
# ===== COORDINATE MAPPING =====

def map_gaze_to_video(gaze_xy, src_w, src_h, dst_w, dst_h):
    """Map gaze from source (camera) resolution to destination (video) resolution.
    Uses proportional scaling with rounding and clamping.
    """
    if gaze_xy is None:
        return None
    x, y = gaze_xy
    if src_w <= 1 or src_h <= 1 or dst_w <= 1 or dst_h <= 1:
        return (max(0, min(dst_w - 1, int(x))), max(0, min(dst_h - 1, int(y))))
    x_scaled = int(round(x * (dst_w - 1) / (src_w - 1)))
    y_scaled = int(round(y * (dst_h - 1) / (src_h - 1)))
    x_scaled = max(0, min(dst_w - 1, x_scaled))
    y_scaled = max(0, min(dst_h - 1, y_scaled))
    return (x_scaled, y_scaled)

COLOR_BAR_BG = (0, 0, 0)  # Black
BAR_CHART_ALPHA = 0.7
BAR_CHART_HEIGHT = 200
BAR_CHART_MARGIN = 20

print("Configuration loaded.")
print(f"  - Virtual camera index: {VIRTUAL_CAMERA_INDEX}")
print(f"  - Heatmap resolution: {HEATMAP_RESOLUTION}")
print(f"  - OBS control: {'Enabled' if OBS_AVAILABLE else 'Disabled'}")
print(f"  - YouTube download: {'Enabled' if YTDLP_AVAILABLE else 'Disabled'}")

# ==============================================================================
# UTILITY CLASSES
# ==============================================================================

class ROI:
    """Rectangle ROI with label."""
    def __init__(self, x, y, width, height, label, scene_idx):
        self.x = int(x)
        self.y = int(y)
        self.width = int(width)
        self.height = int(height)
        self.label = label
        self.scene_idx = scene_idx
        self.angle = 0  # For rotation (future feature)
    
    def contains_point(self, px, py):
        """Check if point is inside ROI."""
        return self.x <= px <= self.x + self.width and \
               self.y <= py <= self.y + self.height
    
    def to_dict(self):
        """Serialize to dictionary."""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'label': self.label,
            'scene_idx': self.scene_idx,
            'angle': self.angle
        }
    
    @staticmethod
    def from_dict(data):
        """Deserialize from dictionary."""
        roi = ROI(data['x'], data['y'], data['width'], data['height'], 
                  data['label'], data['scene_idx'])
        roi.angle = data.get('angle', 0)
        return roi


class Scene:
    """Video scene with start/end frames."""
    def __init__(self, start_frame, end_frame, name):
        self.start_frame = int(start_frame)
        self.end_frame = int(end_frame)
        self.name = name
        self.rois = []  # List of ROI objects
    
    def add_roi(self, roi):
        """Add ROI to this scene."""
        self.rois.append(roi)
    
    def remove_roi(self, roi):
        """Remove ROI from this scene."""
        if roi in self.rois:
            self.rois.remove(roi)
    
    def contains_frame(self, frame_num):
        """Check if frame is within scene range."""
        return self.start_frame <= frame_num <= self.end_frame
    
    def to_dict(self):
        """Serialize to dictionary."""
        return {
            'start_frame': self.start_frame,
            'end_frame': self.end_frame,
            'name': self.name,
            'rois': [roi.to_dict() for roi in self.rois]
        }
    
    @staticmethod
    def from_dict(data):
        """Deserialize from dictionary."""
        scene = Scene(data['start_frame'], data['end_frame'], data['name'])
        scene.rois = [ROI.from_dict(roi_data) for roi_data in data['rois']]
        return scene


print("Utility classes loaded.")

# ==============================================================================
# GAZE DETECTION FUNCTIONS
# ==============================================================================

def detect_gaze_hough(frame):
    """
    Detect eye gaze using Hough Circle Transform.
    Returns (x, y) tuple or None if not detected.
    Adaptive to frame size to improve robustness.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 1.5)

    h, w = gray.shape[:2]
    # Adaptive radii based on frame size (iris/pupil rough proportion)
    base = int(min(w, h) * 0.035)  # ~3.5% of min dimension
    min_r = max(8, int(base * 0.6))
    max_r = max(min_r + 6, int(base * 1.8))

    # Distance between circle centers; we only need one, keep reasonable
    min_dist = max(30, int(min(w, h) * 0.25))

    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=min_dist,
        param1=HOUGH_PARAM1,
        param2=HOUGH_PARAM2,
        minRadius=min_r,
        maxRadius=max_r
    )

    if circles is not None and len(circles[0]) > 0:
        circle = np.uint16(np.around(circles[0, 0]))
        return (int(circle[0]), int(circle[1]))

    return None


# Initialize Kalman Filter for smooth gaze tracking (same as game3_with_recording.py)
kalman = cv2.KalmanFilter(4, 2)
kalman.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
kalman.transitionMatrix = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)
kalman.processNoiseCov = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32) * 0.03
kalman.measurementNoiseCov = np.array([[1, 0], [0, 1]], np.float32) * 5.0
kalman_initialized = False


def apply_kalman_filter(gaze_pos):
    """Apply Kalman filter to smooth gaze position (no internal gating)."""
    global kalman_initialized
    if not kalman_initialized:
        kalman.statePost = np.array([[float(gaze_pos[0])], [float(gaze_pos[1])], [0.0], [0.0]], np.float32)
        kalman_initialized = True
        return gaze_pos

    kalman.predict()
    measurement = np.array([[float(gaze_pos[0])], [float(gaze_pos[1])]], np.float32)
    estimate = kalman.correct(measurement)
    return (int(estimate[0][0]), int(estimate[1][0]))

def reset_kalman():
    """Reset Kalman filter state at start of recording."""
    global kalman_initialized, kalman
    kalman_initialized = False
    # Reinitialize state covariance by recreating filter matrices (keeps tuned covariances)
    kalman.statePost = np.zeros((4,1), np.float32)


def find_roi_at_position(rois, x, y):
    """
    Find which ROI contains the given position.
    Returns ROI object or None.
    """
    for roi in rois:
        if roi.contains_point(x, y):
            return roi
    return None


print("Gaze detection functions loaded.")

# ==============================================================================
# OBS WEBSOCKET CONTROLLER
# ==============================================================================

class OBSController:
    """Controls OBS via WebSocket for auto recording and virtual camera."""
    
    def __init__(self, host=OBS_HOST, port=OBS_PORT_GAZE_ONLY, password=OBS_PASSWORD, name="OBS"):
        self.host = host
        self.port = port
        self.password = password
        self.name = name  # Friendly name for logging
        self.ws = None
        self.connected = False
    
    def connect(self):
        """Connect to OBS WebSocket."""
        if not OBS_AVAILABLE:
            print("OBS WebSocket library not available")
            return False
        
        try:
            self.ws = obsws(self.host, self.port, self.password)
            self.ws.connect()
            self.connected = True
            print(f"✓ Connected to {self.name} at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to {self.name}: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from OBS."""
        if self.ws and self.connected:
            try:
                self.ws.disconnect()
                self.connected = False
                print(f"✓ Disconnected from {self.name}")
            except:
                pass
    
    def start_recording(self):
        """Start OBS recording."""
        if not self.connected:
            return False
        
        try:
            self.ws.call(obs_requests.StartRecord())
            print(f"✓ {self.name} recording started")
            return True
        except Exception as e:
            print(f"✗ Failed to start {self.name} recording: {e}")
            return False
    
    def stop_recording(self):
        """Stop OBS recording."""
        if not self.connected:
            return False
        
        try:
            self.ws.call(obs_requests.StopRecord())
            print(f"✓ {self.name} recording stopped")
            return True
        except Exception as e:
            print(f"✗ Failed to stop {self.name} recording: {e}")
            return False
    
    def is_recording(self):
        """Check if OBS is currently recording."""
        if not self.connected:
            return False
        
        try:
            response = self.ws.call(obs_requests.GetRecordStatus())
            return response.getOutputActive()
        except:
            return False
    
    def start_virtual_camera(self):
        """Start OBS virtual camera output."""
        if not self.connected:
            return False
        
        try:
            self.ws.call(obs_requests.StartVirtualCam())
            print(f"✓ {self.name} virtual camera started")
            return True
        except Exception as e:
            print(f"✗ Failed to start {self.name} virtual camera: {e}")
            return False
    
    def stop_virtual_camera(self):
        """Stop OBS virtual camera output."""
        if not self.connected:
            return False
        
        try:
            self.ws.call(obs_requests.StopVirtualCam())
            print(f"✓ {self.name} virtual camera stopped")
            return True
        except Exception as e:
            print(f"✗ Failed to stop {self.name} virtual camera: {e}")
            return False
    
    def is_virtual_camera_active(self):
        """Check if virtual camera is active."""
        if not self.connected:
            return False
        
        try:
            response = self.ws.call(obs_requests.GetVirtualCamStatus())
            return response.getOutputActive()
        except:
            return False
    
    def set_current_scene(self, scene_name):
        """Switch to a specific OBS scene."""
        if not self.connected:
            return False
        
        try:
            self.ws.call(obs_requests.SetCurrentProgramScene(sceneName=scene_name))
            print(f"✓ {self.name} switched to scene: {scene_name}")
            return True
        except Exception as e:
            print(f"✗ Failed to switch {self.name} scene: {e}")
            return False
    
    def get_current_scene(self):
        """Get current active scene name."""
        if not self.connected:
            return None
        
        try:
            response = self.ws.call(obs_requests.GetCurrentProgramScene())
            return response.getCurrentProgramSceneName()
        except:
            return None
    
    def get_scene_list(self):
        """Get list of all available scenes."""
        if not self.connected:
            return []
        
        try:
            response = self.ws.call(obs_requests.GetSceneList())
            return [scene['sceneName'] for scene in response.getScenes()]
        except:
            return []
    
    def set_source_visibility(self, scene_name, source_name, visible):
        """Show or hide a specific source in a scene."""
        if not self.connected:
            return False
        
        try:
            self.ws.call(obs_requests.SetSceneItemEnabled(
                sceneName=scene_name,
                sceneItemId=source_name,
                sceneItemEnabled=visible
            ))
            status = "visible" if visible else "hidden"
            print(f"✓ {self.name} source '{source_name}' set to {status}")
            return True
        except Exception as e:
            print(f"✗ Failed to set {self.name} source visibility: {e}")
            return False


print("OBS controller loaded.")

# ==============================================================================
# SESSION DATA MANAGER
# ==============================================================================

class SessionManager:
    """Manages session data: video, scenes, ROIs, gaze recordings."""
    
    def __init__(self):
        self.video_path = None
        self.video_cap = None
        self.total_frames = 0
        self.fps = 30.0
        self.width = 0
        self.height = 0
        
        self.scenes = []  # List of Scene objects
        self.gaze_data = []  # List of {frame, timestamp, x, y, roi_label, scene_name}
        
        self.output_dir = None
        self.recording_active = False
        self.session_start_time = None
    
    def load_video(self, path):
        """Load video file and extract properties."""
        if self.video_cap:
            self.video_cap.release()
        
        self.video_path = path
        self.video_cap = cv2.VideoCapture(path)
        
        if not self.video_cap.isOpened():
            raise ValueError(f"Cannot open video: {path}")
        
        self.total_frames = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.video_cap.get(cv2.CAP_PROP_FPS)
        self.width = int(self.video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"✓ Video loaded: {os.path.basename(path)}")
        print(f"  - Resolution: {self.width}x{self.height}")
        print(f"  - FPS: {self.fps:.2f}")
        print(f"  - Total frames: {self.total_frames}")
        
        return True
    
    def get_frame(self, frame_num):
        """Get specific frame from video."""
        if not self.video_cap:
            return None
        
        self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = self.video_cap.read()
        
        return frame if ret else None
    
    def add_scene(self, start_frame, end_frame, name):
        """Add new scene."""
        scene = Scene(start_frame, end_frame, name)
        self.scenes.append(scene)
        self.scenes.sort(key=lambda s: s.start_frame)
        return scene
    
    def get_scene_at_frame(self, frame_num):
        """Get scene containing given frame."""
        for scene in self.scenes:
            if scene.contains_frame(frame_num):
                return scene
        return None
    
    def save_project(self, filepath):
        """Save project configuration to JSON."""
        data = {
            'video_path': self.video_path,
            'total_frames': self.total_frames,
            'fps': self.fps,
            'width': self.width,
            'height': self.height,
            'scenes': [scene.to_dict() for scene in self.scenes]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Project saved: {filepath}")
    
    def load_project(self, filepath):
        """Load project configuration from JSON."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.load_video(data['video_path'])
        self.scenes = [Scene.from_dict(s) for s in data['scenes']]
        
        print(f"✓ Project loaded: {filepath}")
    
    def start_recording_session(self):
        """Start new recording session."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.output_dir = f"ad_session_{timestamp}"
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.gaze_data = []
        self.recording_active = True
        self.session_start_time = time.time()
        
        print(f"✓ Recording session started: {self.output_dir}")
    
    def stop_recording_session(self):
        """Stop recording session."""
        self.recording_active = False
        print(f"✓ Recording session stopped")
    
    def record_gaze_frame(self, frame_num, gaze_x, gaze_y):
        """Record single gaze data point."""
        if not self.recording_active:
            return
        
        timestamp = time.time() - self.session_start_time
        scene = self.get_scene_at_frame(frame_num)
        scene_name = scene.name if scene else "unknown"
        
        # Find which ROI contains gaze
        roi_label = "background"
        if scene:
            roi = find_roi_at_position(scene.rois, gaze_x, gaze_y)
            if roi:
                roi_label = roi.label
        
        self.gaze_data.append({
            'frame': frame_num,
            'timestamp': timestamp,
            'x': gaze_x,
            'y': gaze_y,
            'roi_label': roi_label,
            'scene_name': scene_name
        })
    
    def save_gaze_data(self):
        """Save gaze data to CSV."""
        if not self.output_dir or not self.gaze_data:
            return
        
        df = pd.DataFrame(self.gaze_data)
        csv_path = os.path.join(self.output_dir, "gaze_data.csv")
        df.to_csv(csv_path, index=False)
        
        print(f"✓ Gaze data saved: {csv_path} ({len(self.gaze_data)} frames)")
    
    def cleanup(self):
        """Release resources."""
        if self.video_cap:
            self.video_cap.release()


print("Session manager loaded.")

# ==============================================================================
# POST-PROCESSING FUNCTIONS
# ==============================================================================

def generate_heatmap(gaze_data, video_width, video_height, scene_name, output_path):
    """
    Generate heatmap for a specific scene.
    
    Args:
        gaze_data: List of gaze data points filtered for this scene
        video_width, video_height: Video dimensions
        scene_name: Scene name for title
        output_path: Path to save heatmap image
    """
    if len(gaze_data) == 0:
        print(f"  Warning: No gaze data for scene '{scene_name}'")
        return
    
    # Create heatmap grid
    heatmap = np.zeros(HEATMAP_RESOLUTION, dtype=np.float32)
    
    # Scale gaze coordinates to heatmap resolution
    scale_x = HEATMAP_RESOLUTION[0] / video_width
    scale_y = HEATMAP_RESOLUTION[1] / video_height
    
    for point in gaze_data:
        hm_x = int(point['x'] * scale_x)
        hm_y = int(point['y'] * scale_y)
        
        # Bounds check
        hm_x = max(0, min(HEATMAP_RESOLUTION[0] - 1, hm_x))
        hm_y = max(0, min(HEATMAP_RESOLUTION[1] - 1, hm_y))
        
        heatmap[hm_y, hm_x] += 1
    
    # Apply Gaussian blur
    heatmap = cv2.GaussianBlur(heatmap, (GAUSSIAN_BLUR_RADIUS, GAUSSIAN_BLUR_RADIUS), 0)
    
    # Normalize
    if heatmap.max() > 0:
        heatmap = heatmap / heatmap.max()
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot heatmap with 'hot' colormap
    im = ax.imshow(heatmap, cmap='hot', interpolation='bilinear', aspect='auto')
    
    ax.set_title(f"Gaze Heatmap - {scene_name}", fontsize=14, fontweight='bold')
    ax.axis('off')
    
    # Colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Gaze Density', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    print(f"  ✓ Heatmap saved: {output_path}")


def generate_roi_statistics(gaze_data, scenes, output_dir):
    """
    Calculate and save ROI statistics.
    
    Args:
        gaze_data: List of all gaze data points
        scenes: List of Scene objects
        output_dir: Output directory path
    """
    df = pd.DataFrame(gaze_data)
    
    # Group by scene and ROI
    stats = []
    
    for scene in scenes:
        scene_data = df[df['scene_name'] == scene.name]
        total_frames = len(scene_data)
        
        if total_frames == 0:
            continue
        
        # Count frames per ROI
        roi_counts = scene_data['roi_label'].value_counts()
        
        for roi_label, count in roi_counts.items():
            percentage = (count / total_frames) * 100
            duration = count / scene.end_frame - scene.start_frame + 1
            
            stats.append({
                'scene': scene.name,
                'roi_label': roi_label,
                'frame_count': count,
                'percentage': percentage,
                'total_scene_frames': total_frames
            })
    
    stats_df = pd.DataFrame(stats)
    csv_path = os.path.join(output_dir, "roi_statistics.csv")
    stats_df.to_csv(csv_path, index=False)
    
    print(f"  ✓ ROI statistics saved: {csv_path}")
    
    return stats_df


def create_overlay_video_with_bar_chart(session_manager, output_path, progress_callback=None):
    """
    Create video with gaze cursor overlay and animated bar chart.
    
    Args:
        session_manager: SessionManager instance
        output_path: Path for output video
        progress_callback: Function to call with progress (0-100)
    """
    print("\n" + "=" * 80)
    print("CREATING OVERLAY VIDEO WITH BAR CHART")
    print("=" * 80)
    
    if not session_manager.gaze_data:
        print("Error: No gaze data to process")
        return False
    
    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, session_manager.fps, 
                          (session_manager.width, session_manager.height))
    
    # Create gaze data lookup by frame
    gaze_by_frame = {}
    for gaze_point in session_manager.gaze_data:
        gaze_by_frame[gaze_point['frame']] = gaze_point
    
    # Initialize ROI counters per scene
    roi_counters = defaultdict(lambda: defaultdict(int))
    
    total_gaze_frames = len(session_manager.gaze_data)
    processed = 0
    
    # Get start and end frames from gaze data
    start_frame = min(gaze_by_frame.keys())
    end_frame = max(gaze_by_frame.keys())
    
    for frame_num in range(start_frame, end_frame + 1):
        # Read original frame
        frame = session_manager.get_frame(frame_num)
        if frame is None:
            continue
        
        # Get scene
        scene = session_manager.get_scene_at_frame(frame_num)
        
        if frame_num in gaze_by_frame:
            gaze_point = gaze_by_frame[frame_num]
            gaze_x, gaze_y = int(gaze_point['x']), int(gaze_point['y'])
            roi_label = gaze_point['roi_label']
            scene_name = gaze_point['scene_name']
            
            # Update ROI counter
            roi_counters[scene_name][roi_label] += 1
            
            # Draw gaze cursor
            cv2.circle(frame, (gaze_x, gaze_y), 15, COLOR_GAZE_CURSOR, 2)
            cv2.line(frame, (gaze_x - 15, gaze_y), (gaze_x + 15, gaze_y), COLOR_GAZE_CURSOR, 2)
            cv2.line(frame, (gaze_x, gaze_y - 15), (gaze_x, gaze_y + 15), COLOR_GAZE_CURSOR, 2)
            
            # Draw ROIs for current scene
            if scene:
                for roi in scene.rois:
                    color = COLOR_ROI_ACTIVE if roi.label == roi_label else COLOR_ROI_INACTIVE
                    cv2.rectangle(frame, (roi.x, roi.y), 
                                (roi.x + roi.width, roi.y + roi.height), color, 2)
                    cv2.putText(frame, roi.label, (roi.x, roi.y - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Draw bar chart overlay (bottom left)
            if scene:
                draw_bar_chart_overlay(frame, roi_counters[scene_name], scene.rois)
            
            processed += 1
            if progress_callback and processed % 10 == 0:
                progress = int((processed / total_gaze_frames) * 100)
                progress_callback(progress)
        
        out.write(frame)
    
    out.release()
    
    print(f"✓ Overlay video saved: {output_path}")
    return True


def draw_bar_chart_overlay(frame, roi_counter, rois):
    """
    Draw bar chart overlay on frame (bottom-left corner).
    
    Args:
        frame: Video frame (numpy array)
        roi_counter: Dict {roi_label: count}
        rois: List of ROI objects for current scene
    """
    if not roi_counter:
        return
    
    h, w = frame.shape[:2]
    
    # Bar chart dimensions
    chart_x = BAR_CHART_MARGIN
    chart_y = h - BAR_CHART_HEIGHT - BAR_CHART_MARGIN
    chart_width = 400
    chart_height = BAR_CHART_HEIGHT
    
    # Semi-transparent background
    overlay = frame.copy()
    cv2.rectangle(overlay, (chart_x, chart_y), 
                 (chart_x + chart_width, chart_y + chart_height), 
                 COLOR_BAR_BG, -1)
    cv2.addWeighted(overlay, BAR_CHART_ALPHA, frame, 1 - BAR_CHART_ALPHA, 0, frame)
    
    # Draw bars
    total_count = sum(roi_counter.values())
    roi_labels = [roi.label for roi in rois] + ['background']
    num_rois = len(roi_labels)
    
    if num_rois == 0:
        return
    
    bar_height = (chart_height - 40) // num_rois
    max_bar_width = chart_width - 150
    
    for i, roi_label in enumerate(roi_labels):
        count = roi_counter.get(roi_label, 0)
        percentage = (count / total_count * 100) if total_count > 0 else 0
        
        bar_x = chart_x + 120
        bar_y = chart_y + 20 + i * bar_height
        bar_w = int((percentage / 100) * max_bar_width)
        
        # Draw bar
        color = COLOR_ROI_ACTIVE if roi_label != 'background' else COLOR_ROI_INACTIVE
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_height - 10), color, -1)
        
        # Draw label and percentage
        cv2.putText(frame, roi_label, (chart_x + 10, bar_y + bar_height // 2),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"{percentage:.1f}%", (bar_x + bar_w + 10, bar_y + bar_height // 2),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)


print("Post-processing functions loaded.")

# ==============================================================================
# MAIN GUI APPLICATION
# ==============================================================================

class VideoROIDemoGUI:
    """Main GUI application."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Video ROI Demo - Advertisement Eye Tracking")
        self.root.geometry("1400x900")
        
        # Initialize components
        self.session = SessionManager()
        self.obs_gaze = OBSController(port=OBS_PORT_GAZE_ONLY, name="OBS-GazeOnly")
        self.obs_combined = OBSController(port=OBS_PORT_COMBINED, name="OBS-Combined")
        
        # GUI state
        self.current_frame_num = 0
        self.current_scene_idx = 0
        self.selected_roi = None
        self.roi_drawing = False
        self.roi_start_pos = None
        self.playing = False
        self.play_thread = None
        
        # Virtual camera for gaze tracking
        self.gaze_cap = None
        self.last_gaze_pos = None  # Track last known gaze position
        self.gaze_detection_failures = 0  # Count consecutive failures
        self.detection_count = 0  # Track detections for Kalman stabilization
        self.frame_width = 1920  # Camera frame width
        self.frame_height = 1080  # Camera frame height
        # Gaze detection diagnostics
        self._det_success = 0
        self._det_total = 0
        
        # Setup GUI
        self.setup_gui()
        
        # Try to connect to OBS instances
        if OBS_AVAILABLE:
            print("\nConnecting to OBS instances...")
            self.obs_gaze.connect()
            self.obs_combined.connect()
            
            # Set initial scenes
            if self.obs_gaze.connected:
                self.obs_gaze.set_current_scene(OBS_SCENE_GAZE_ONLY)
            if self.obs_combined.connected:
                self.obs_combined.set_current_scene(OBS_SCENE_COMBINED)
    
    def setup_gui(self):
        """Setup all GUI components."""
        
        # ===== TOP MENU =====
        menu_frame = tk.Frame(self.root, bg='#2b2b2b', height=50)
        menu_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Button(menu_frame, text="📁 Load Video", command=self.load_video, 
                 font=('Arial', 11), bg='#4a4a4a', fg='white', padx=15, pady=5).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(menu_frame, text="� YouTube", command=self.download_youtube, 
                 font=('Arial', 11), bg='#e91e63', fg='white', padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(menu_frame, text="�💾 Save Project", command=self.save_project,
                 font=('Arial', 11), bg='#4a4a4a', fg='white', padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(menu_frame, text="📂 Load Project", command=self.load_project,
                 font=('Arial', 11), bg='#4a4a4a', fg='white', padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Label(menu_frame, text="", bg='#2b2b2b', width=5).pack(side=tk.LEFT)
        
        self.record_btn = tk.Button(menu_frame, text="⏺ START RECORDING", command=self.toggle_recording,
                                    font=('Arial', 12, 'bold'), bg='#d32f2f', fg='white', padx=20, pady=5)
        self.record_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Label(menu_frame, text="", bg='#2b2b2b', width=5).pack(side=tk.LEFT)
        
        tk.Button(menu_frame, text="🎬 Process Results", command=self.process_results,
                 font=('Arial', 11), bg='#388e3c', fg='white', padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Label(menu_frame, text="|", bg='#2b2b2b', fg='#666', font=('Arial', 14)).pack(side=tk.LEFT, padx=10)
        
        # OBS Controls
        tk.Label(menu_frame, text="OBS:", bg='#2b2b2b', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        self.vcam_btn = tk.Button(menu_frame, text="📹 Start VCam", command=self.toggle_virtual_camera,
                                   font=('Arial', 10), bg='#1976d2', fg='white', padx=10, pady=5)
        self.vcam_btn.pack(side=tk.LEFT, padx=2)
        
        # ===== MAIN CONTENT AREA =====
        content_frame = tk.Frame(self.root)
        content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Video preview
        left_panel = tk.Frame(content_frame, bg='#1e1e1e')
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Video canvas
        self.video_canvas = tk.Canvas(left_panel, bg='black', width=PREVIEW_WIDTH, height=PREVIEW_HEIGHT)
        self.video_canvas.pack(side=tk.TOP, padx=5, pady=5)
        
        # Bind mouse events for ROI drawing
        self.video_canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.video_canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.video_canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # Video controls
        controls_frame = tk.Frame(left_panel, bg='#2b2b2b')
        controls_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        self.play_pause_btn = tk.Button(controls_frame, text="▶️ Play", command=self.toggle_playback,
                                        font=('Arial', 10), padx=10)
        self.play_pause_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Button(controls_frame, text="⏮ Prev Frame", command=lambda: self.seek_frame(-1),
                 font=('Arial', 10), padx=10).pack(side=tk.LEFT, padx=5)
        
        tk.Button(controls_frame, text="⏭ Next Frame", command=lambda: self.seek_frame(1),
                 font=('Arial', 10), padx=10).pack(side=tk.LEFT, padx=5)
        
        # Frame slider
        slider_frame = tk.Frame(left_panel, bg='#2b2b2b')
        slider_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        tk.Label(slider_frame, text="Frame:", bg='#2b2b2b', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        self.frame_slider = tk.Scale(slider_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                     command=self.on_slider_change, bg='#3b3b3b', fg='white',
                                     highlightthickness=0, troughcolor='#1e1e1e')
        self.frame_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.frame_label = tk.Label(slider_frame, text="0 / 0", bg='#2b2b2b', fg='white',
                                    font=('Arial', 10), width=12)
        self.frame_label.pack(side=tk.LEFT, padx=5)
        
        # Right panel - Scene & ROI editor
        right_panel = tk.Frame(content_frame, bg='#2b2b2b', width=350)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH)
        right_panel.pack_propagate(False)
        
        # Scene editor
        scene_frame = tk.LabelFrame(right_panel, text="SCENES", bg='#2b2b2b', fg='white',
                                   font=('Arial', 11, 'bold'), padx=10, pady=10)
        scene_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scene list
        self.scene_listbox = tk.Listbox(scene_frame, bg='#1e1e1e', fg='white', font=('Arial', 10),
                                       selectmode=tk.SINGLE, height=8)
        self.scene_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)
        self.scene_listbox.bind('<<ListboxSelect>>', self.on_scene_select)
        
        # Scene controls
        scene_ctrl_frame = tk.Frame(scene_frame, bg='#2b2b2b')
        scene_ctrl_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        tk.Button(scene_ctrl_frame, text="➕ Add Scene", command=self.add_scene,
                 font=('Arial', 9), bg='#4caf50', fg='white', padx=10).pack(side=tk.LEFT, padx=2)
        
        tk.Button(scene_ctrl_frame, text="✂️ Split Here", command=self.split_scene,
                 font=('Arial', 9), bg='#ff9800', fg='white', padx=10).pack(side=tk.LEFT, padx=2)
        
        tk.Button(scene_ctrl_frame, text="🗑 Delete", command=self.delete_scene,
                 font=('Arial', 9), bg='#f44336', fg='white', padx=10).pack(side=tk.LEFT, padx=2)
        
        # ROI editor
        roi_frame = tk.LabelFrame(right_panel, text="ROIs", bg='#2b2b2b', fg='white',
                                 font=('Arial', 11, 'bold'), padx=10, pady=10)
        roi_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tk.Label(roi_frame, text="Draw ROI: Click & drag on video", bg='#2b2b2b', fg='#aaa',
                font=('Arial', 9, 'italic')).pack(side=tk.TOP, pady=5)
        
        # ROI list
        self.roi_listbox = tk.Listbox(roi_frame, bg='#1e1e1e', fg='white', font=('Arial', 10),
                                      selectmode=tk.SINGLE, height=6)
        self.roi_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)
        self.roi_listbox.bind('<<ListboxSelect>>', self.on_roi_select)
        
        # ROI label entry
        label_frame = tk.Frame(roi_frame, bg='#2b2b2b')
        label_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        tk.Label(label_frame, text="Label:", bg='#2b2b2b', fg='white', font=('Arial', 10)).pack(side=tk.LEFT)
        self.roi_label_entry = tk.Entry(label_frame, bg='#1e1e1e', fg='white', font=('Arial', 10))
        self.roi_label_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.roi_label_entry.bind('<Return>', lambda e: self.update_roi_label())
        
        tk.Button(label_frame, text="✓", command=self.update_roi_label,
                 font=('Arial', 9), bg='#4caf50', fg='white', padx=5).pack(side=tk.LEFT)
        
        # ROI delete button
        tk.Button(roi_frame, text="🗑 Delete ROI", command=self.delete_roi,
                 font=('Arial', 9), bg='#f44336', fg='white', padx=10).pack(side=tk.TOP, pady=5)
        
        # Status bar
        self.status_label = tk.Label(self.root, text="Ready. Load a video to begin.", bg='#1e1e1e',
                                     fg='#4caf50', font=('Arial', 10), anchor=tk.W, padx=10, pady=5)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_status(self, message, color='#4caf50'):
        """Update status bar message."""
        self.status_label.config(text=message, fg=color)
        self.root.update_idletasks()
    
    def load_video(self):
        """Load video file."""
        filepath = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            self.session.load_video(filepath)
            
            # Update slider
            self.frame_slider.config(to=self.session.total_frames - 1)
            self.current_frame_num = 0
            
            # Create default scene (entire video)
            if not self.session.scenes:
                self.session.add_scene(0, self.session.total_frames - 1, "Scene 1")
            
            self.refresh_scene_list()
            self.render_frame()
            self.update_status(f"Video loaded: {os.path.basename(filepath)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load video:\n{e}")
    
    def download_youtube(self):
        """Download video from YouTube URL."""
        if not YTDLP_AVAILABLE:
            messagebox.showerror("Not Available", 
                               "yt-dlp is not installed.\n\n"
                               "Install with: pip install yt-dlp")
            return
        
        # Input dialog for URL
        url = tk.simpledialog.askstring("YouTube Download", 
                                       "Enter YouTube URL:",
                                       parent=self.root)
        if not url:
            return
        
        # Validate URL
        if not ('youtube.com' in url or 'youtu.be' in url):
            messagebox.showwarning("Invalid URL", "Please enter a valid YouTube URL")
            return
        
        # Create download directory
        os.makedirs(DOWNLOADED_VIDEOS_DIR, exist_ok=True)
        
        # Show progress dialog
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Downloading from YouTube")
        progress_window.geometry("500x150")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        tk.Label(progress_window, text="Downloading video...", 
                font=('Arial', 11)).pack(pady=10)
        
        progress_label = tk.Label(progress_window, text="Initializing...", 
                                 font=('Arial', 10), fg='#666')
        progress_label.pack(pady=5)
        
        progress_bar = ttk.Progressbar(progress_window, mode='indeterminate', length=400)
        progress_bar.pack(pady=10)
        progress_bar.start()
        
        # Download in thread
        def download_thread():
            try:
                # yt-dlp options
                ydl_opts = {
                    'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
                    'outtmpl': os.path.join(DOWNLOADED_VIDEOS_DIR, '%(title)s.%(ext)s'),
                    'merge_output_format': 'mp4',
                    'quiet': False,
                    'no_warnings': False,
                    'progress_hooks': [lambda d: self._download_progress_hook(d, progress_label)]
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    video_path = ydl.prepare_filename(info)
                    
                    # Ensure .mp4 extension
                    if not video_path.endswith('.mp4'):
                        base = os.path.splitext(video_path)[0]
                        video_path = base + '.mp4'
                
                # Close progress window and load video
                self.root.after(0, progress_window.destroy)
                self.root.after(100, lambda: self._load_downloaded_video(video_path))
                
            except Exception as e:
                self.root.after(0, progress_window.destroy)
                self.root.after(0, lambda: messagebox.showerror("Download Failed", 
                                                                f"Failed to download video:\n{e}"))
                self.root.after(0, lambda: self.update_status("Download failed", '#f44336'))
        
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
    
    def _download_progress_hook(self, d, progress_label):
        """Update download progress label."""
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'N/A')
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            
            msg = f"Progress: {percent} | Speed: {speed} | ETA: {eta}"
            self.root.after(0, lambda: progress_label.config(text=msg))
        
        elif d['status'] == 'finished':
            self.root.after(0, lambda: progress_label.config(text="Download complete! Processing..."))
    
    def _load_downloaded_video(self, video_path):
        """Load downloaded video after download completes."""
        if os.path.exists(video_path):
            try:
                self.session.load_video(video_path)
                
                # Update slider
                self.frame_slider.config(to=self.session.total_frames - 1)
                self.current_frame_num = 0
                
                # Create default scene
                if not self.session.scenes:
                    self.session.add_scene(0, self.session.total_frames - 1, "Scene 1")
                
                self.refresh_scene_list()
                self.render_frame()
                self.update_status(f"✓ YouTube video loaded: {os.path.basename(video_path)}", '#4caf50')
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load downloaded video:\n{e}")
        else:
            messagebox.showerror("Error", f"Downloaded file not found:\n{video_path}")
    
    def render_frame(self):
        """Render current frame to canvas."""
        if not self.session.video_cap:
            return
        
        frame = self.session.get_frame(self.current_frame_num)
        if frame is None:
            return
        
        # Resize for preview
        frame_resized = cv2.resize(frame, (PREVIEW_WIDTH, PREVIEW_HEIGHT))
        
        # Draw ROIs for current scene
        scene = self.session.get_scene_at_frame(self.current_frame_num)
        if scene:
            scale_x = PREVIEW_WIDTH / self.session.width
            scale_y = PREVIEW_HEIGHT / self.session.height
            
            for roi in scene.rois:
                x1 = int(roi.x * scale_x)
                y1 = int(roi.y * scale_y)
                x2 = int((roi.x + roi.width) * scale_x)
                y2 = int((roi.y + roi.height) * scale_y)
                
                color = COLOR_ROI_ACTIVE if roi == self.selected_roi else COLOR_ROI_INACTIVE
                cv2.rectangle(frame_resized, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame_resized, roi.label, (x1, y1 - 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Convert to PhotoImage
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        photo = ImageTk.PhotoImage(image=img)
        
        # Update canvas
        self.video_canvas.delete("all")
        self.video_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        self.video_canvas.image = photo  # Keep reference
        
        # Update frame label
        self.frame_label.config(text=f"{self.current_frame_num} / {self.session.total_frames - 1}")


    print("Main GUI application (Part 1) loaded.")

    # ===== EVENT HANDLERS =====
    
    def on_slider_change(self, value):
        """Handle frame slider change."""
        self.current_frame_num = int(value)
        self.render_frame()
    
    def seek_frame(self, delta):
        """Seek frame by delta."""
        new_frame = self.current_frame_num + delta
        new_frame = max(0, min(self.session.total_frames - 1, new_frame))
        self.current_frame_num = new_frame
        self.frame_slider.set(new_frame)
        self.render_frame()
    
    def toggle_playback(self):
        """Toggle play/pause."""
        self.playing = not self.playing
        
        if self.playing:
            self.play_pause_btn.config(text="⏸ Pause")
            # Hide cursor during playback
            self.canvas.config(cursor="none")
            self.playback_loop()  # Call directly, not in thread
        else:
            self.play_pause_btn.config(text="▶️ Play")
            # Show cursor when paused
            self.canvas.config(cursor="arrow")
    
    def playback_loop(self):
        """Playback loop (scheduled with after)."""
        if not self.playing:
            return
        
        if self.current_frame_num < self.session.total_frames - 1:
            self.current_frame_num += 1
            self.frame_slider.set(self.current_frame_num)
            self.render_frame()
            
            # If recording, also record gaze for this frame
            if self.session.recording_active:
                self.record_gaze_for_frame()
            
            # Schedule next frame
            delay_ms = int(1000.0 / self.session.fps)
            self.root.after(delay_ms, self.playback_loop)
        else:
            # End of video
            self.playing = False
            self.play_pause_btn.config(text="▶️ Play")
    
    def on_canvas_press(self, event):
        """Handle canvas mouse press for ROI drawing."""
        scene = self.session.get_scene_at_frame(self.current_frame_num)
        if not scene:
            messagebox.showwarning("No Scene", "Please create a scene first")
            return
        
        self.roi_drawing = True
        self.roi_start_pos = (event.x, event.y)
    
    def on_canvas_drag(self, event):
        """Handle canvas mouse drag."""
        if not self.roi_drawing or not self.roi_start_pos:
            return
        
        # Visual feedback (could draw temporary rectangle here)
        pass
    
    def on_canvas_release(self, event):
        """Handle canvas mouse release to create ROI."""
        if not self.roi_drawing or not self.roi_start_pos:
            return
        
        self.roi_drawing = False
        
        # Calculate ROI coordinates (scale back to original video resolution)
        scale_x = self.session.width / PREVIEW_WIDTH
        scale_y = self.session.height / PREVIEW_HEIGHT
        
        x1 = int(min(self.roi_start_pos[0], event.x) * scale_x)
        y1 = int(min(self.roi_start_pos[1], event.y) * scale_y)
        x2 = int(max(self.roi_start_pos[0], event.x) * scale_x)
        y2 = int(max(self.roi_start_pos[1], event.y) * scale_y)
        
        width = x2 - x1
        height = y2 - y1
        
        # Minimum size check
        if width < 20 or height < 20:
            return
        
        # Create ROI
        scene = self.session.get_scene_at_frame(self.current_frame_num)
        if scene:
            roi_num = len(scene.rois) + 1
            label = f"ROI_{roi_num}"
            roi = ROI(x1, y1, width, height, label, self.current_scene_idx)
            scene.add_roi(roi)
            
            self.refresh_roi_list()
            self.render_frame()
            self.update_status(f"ROI '{label}' created")
    
    def on_scene_select(self, event):
        """Handle scene selection."""
        selection = self.scene_listbox.curselection()
        if not selection:
            return
        
        self.current_scene_idx = selection[0]
        scene = self.session.scenes[self.current_scene_idx]
        
        # Jump to scene start
        self.current_frame_num = scene.start_frame
        self.frame_slider.set(self.current_frame_num)
        
        self.refresh_roi_list()
        self.render_frame()
    
    def on_roi_select(self, event):
        """Handle ROI selection."""
        selection = self.roi_listbox.curselection()
        if not selection:
            self.selected_roi = None
            return
        
        roi_idx = selection[0]
        scene = self.session.scenes[self.current_scene_idx]
        self.selected_roi = scene.rois[roi_idx]
        
        self.roi_label_entry.delete(0, tk.END)
        self.roi_label_entry.insert(0, self.selected_roi.label)
        
        self.render_frame()
    
    # ===== SCENE MANAGEMENT =====
    
    def refresh_scene_list(self):
        """Refresh scene listbox."""
        self.scene_listbox.delete(0, tk.END)
        for i, scene in enumerate(self.session.scenes):
            duration = (scene.end_frame - scene.start_frame) / self.session.fps
            self.scene_listbox.insert(tk.END, f"{scene.name} [{scene.start_frame}-{scene.end_frame}] ({duration:.1f}s)")
    
    def add_scene(self):
        """Add new scene."""
        if not self.session.video_cap:
            messagebox.showwarning("No Video", "Please load a video first")
            return
        
        # Simple dialog for scene name and range
        name = tk.simpledialog.askstring("Scene Name", "Enter scene name:", initialvalue=f"Scene {len(self.session.scenes) + 1}")
        if not name:
            return
        
        start = tk.simpledialog.askinteger("Start Frame", "Enter start frame:", initialvalue=self.current_frame_num, minvalue=0, maxvalue=self.session.total_frames - 1)
        if start is None:
            return
        
        end = tk.simpledialog.askinteger("End Frame", "Enter end frame:", initialvalue=self.session.total_frames - 1, minvalue=start, maxvalue=self.session.total_frames - 1)
        if end is None:
            return
        
        self.session.add_scene(start, end, name)
        self.refresh_scene_list()
        self.update_status(f"Scene '{name}' added")
    
    def split_scene(self):
        """Split current scene at current frame."""
        if self.current_scene_idx >= len(self.session.scenes):
            return
        
        scene = self.session.scenes[self.current_scene_idx]
        
        if self.current_frame_num <= scene.start_frame or self.current_frame_num >= scene.end_frame:
            messagebox.showwarning("Invalid Split", "Cannot split at scene boundaries")
            return
        
        # Create new scene
        new_scene = Scene(self.current_frame_num, scene.end_frame, f"{scene.name}_B")
        scene.end_frame = self.current_frame_num - 1
        scene.name = f"{scene.name}_A"
        
        self.session.scenes.insert(self.current_scene_idx + 1, new_scene)
        self.refresh_scene_list()
        self.update_status(f"Scene split at frame {self.current_frame_num}")
    
    def delete_scene(self):
        """Delete selected scene."""
        if self.current_scene_idx >= len(self.session.scenes):
            return
        
        scene = self.session.scenes[self.current_scene_idx]
        
        if messagebox.askyesno("Confirm Delete", f"Delete scene '{scene.name}'?"):
            self.session.scenes.pop(self.current_scene_idx)
            self.refresh_scene_list()
            self.refresh_roi_list()
            self.render_frame()
            self.update_status(f"Scene '{scene.name}' deleted", '#ff9800')
    
    # ===== ROI MANAGEMENT =====
    
    def refresh_roi_list(self):
        """Refresh ROI listbox for current scene."""
        self.roi_listbox.delete(0, tk.END)
        
        if self.current_scene_idx >= len(self.session.scenes):
            return
        
        scene = self.session.scenes[self.current_scene_idx]
        for roi in scene.rois:
            self.roi_listbox.insert(tk.END, f"{roi.label} [{roi.width}x{roi.height}]")
    
    def update_roi_label(self):
        """Update selected ROI label."""
        if not self.selected_roi:
            return
        
        new_label = self.roi_label_entry.get().strip()
        if new_label:
            self.selected_roi.label = new_label
            self.refresh_roi_list()
            self.render_frame()
            self.update_status(f"ROI label updated to '{new_label}'")
    
    def delete_roi(self):
        """Delete selected ROI."""
        if not self.selected_roi:
            return
        
        scene = self.session.scenes[self.current_scene_idx]
        scene.remove_roi(self.selected_roi)
        
        self.selected_roi = None
        self.refresh_roi_list()
        self.render_frame()
        self.update_status("ROI deleted", '#ff9800')
    
    # ===== RECORDING =====
    
    def toggle_recording(self):
        """Toggle recording session."""
        if not self.session.recording_active:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Start recording session."""
        if not self.session.video_cap:
            messagebox.showwarning("No Video", "Please load a video first")
            return
        
        if not self.session.scenes:
            messagebox.showwarning("No Scenes", "Please define at least one scene")
            return
        
        # Open virtual camera
        try:
            self.gaze_cap = cv2.VideoCapture(VIRTUAL_CAMERA_INDEX)
            if not self.gaze_cap.isOpened():
                raise ValueError("Cannot open virtual camera")
        except Exception as e:
            messagebox.showerror("Camera Error", f"Failed to open virtual camera:\n{e}")
            return
        
        # Start OBS virtual camera (gaze only) and recording (combined)
        if self.obs_gaze.connected:
            self.obs_gaze.start_virtual_camera()
        
        if self.obs_combined.connected:
            self.obs_combined.start_recording()
        
        # Start session
        self.session.start_recording_session()
        
        # Reset gaze tracking
        self.last_gaze_pos = None
        self.gaze_detection_failures = 0
        self.detection_count = 0
        reset_kalman()
        self._det_success = 0
        self._det_total = 0
        
        # Hide mouse cursor during recording
        self.root.config(cursor="none")
        
        # Update UI
        self.record_btn.config(text="⏹ STOP RECORDING", bg='#ff5722')
        self.update_status("Recording started - Press STOP when done", '#ff5722')
        
        # Start playback (which will trigger record_gaze_for_frame on each frame)
        if not self.playing:
            self.toggle_playback()
    
    def record_gaze_for_frame(self):
        """Record gaze data for current playback frame (synced with video)."""
        if not self.session.recording_active or not self.gaze_cap:
            return
        
        # Read gaze from virtual camera
        ret, gaze_frame = self.gaze_cap.read()
        
        current_gaze = None
        frame_info = f"Frame {self.current_frame_num}"
        
        if ret:
            # Detect actual frame size
            self.frame_height, self.frame_width = gaze_frame.shape[:2]
            
            # Try to detect gaze position
            detected_pos = detect_gaze_hough(gaze_frame)
            
            if detected_pos:
            self._det_success += 1
                # Validate coordinates are in reasonable range
                if 0 <= detected_pos[0] <= self.frame_width and 0 <= detected_pos[1] <= self.frame_height:
                    # Apply Kalman filter for smoothing (after 5 frames)
                    self.detection_count += 1
                    if self.detection_count < 5:
                        # Use raw detection for first 5 frames
                        current_gaze = detected_pos
                    else:
                        # Use Kalman-filtered position
                        current_gaze = apply_kalman_filter(detected_pos)
                    
                    self.last_gaze_pos = current_gaze
                    self.gaze_detection_failures = 0
                    # print(f"✓ {frame_info}: Detected at {current_gaze}")
                else:
                    # Invalid coordinates - use fallback
                    if self.last_gaze_pos:
                        current_gaze = self.last_gaze_pos
                        self.gaze_detection_failures += 1
                        # print(f"! {frame_info}: Invalid coords {detected_pos}, using fallback {current_gaze}")
            else:
                # Detection failed - use last known position if available
                if self.last_gaze_pos:
                    current_gaze = self.last_gaze_pos
                    self.gaze_detection_failures += 1
                    # print(f"! {frame_info}: Detection failed, using fallback {current_gaze}")
                    
                    # Log warning if failures persist
                    if self.gaze_detection_failures == 10:
                        print("⚠ Warning: Gaze detection struggling - using last known position")
                    elif self.gaze_detection_failures == 50:
                        print("⚠ Warning: 50+ frames without gaze detection!")
        else:
            # Virtual camera read failed - use fallback if available
            if self.last_gaze_pos:
                current_gaze = self.last_gaze_pos
                self.gaze_detection_failures += 1
                # print(f"! {frame_info}: Virtual camera read failed, using fallback")
        
        # Update total frames seen for detection diagnostics
        self._det_total += 1
        if self._det_total % 60 == 0:
            rate = (self._det_success / self._det_total * 100.0) if self._det_total else 0.0
            print(f"📈 Gaze detection rate: {self._det_success}/{self._det_total} ({rate:.1f}%)")
            if rate < 10.0:
                print("⚠ Very low detection rate. Check lighting, face positioning, and VIRTUAL_CAMERA_INDEX.\n   - Current VIRTUAL_CAMERA_INDEX:", VIRTUAL_CAMERA_INDEX, "(try 1..3)\n   - Also try adjusting HOUGH params in settings if needed.")
        
        # ALWAYS record gaze data for frame continuity in overlay
        # If we have current_gaze, record it
        # If not but we have last_gaze_pos, record that
        # Otherwise record center of frame as last resort
        if current_gaze:
            # Map from camera frame to video frame resolution
            mapped = map_gaze_to_video(
                current_gaze,
                self.frame_width, self.frame_height,
                self.session.width, self.session.height
            )
            self.session.record_gaze_frame(self.current_frame_num, mapped[0], mapped[1])
            # print(f"✓ Recording: {frame_info} -> ({current_gaze[0]}, {current_gaze[1]})")
        elif self.last_gaze_pos:
            # Fallback: use last known position
            mapped = map_gaze_to_video(
                self.last_gaze_pos,
                self.frame_width, self.frame_height,
                self.session.width, self.session.height
            )
            self.session.record_gaze_frame(self.current_frame_num, mapped[0], mapped[1])
            # print(f"→ Recording fallback: {frame_info} -> {self.last_gaze_pos}")
        else:
            # Last resort: record center of frame and persist as last known
            center_x = self.session.width // 2
            center_y = self.session.height // 2
            self.last_gaze_pos = (center_x, center_y)
            self.session.record_gaze_frame(self.current_frame_num, center_x, center_y)
            # print(f"◆ Recording center: {frame_info} -> ({center_x}, {center_y})")
    
    def stop_recording(self):
        """Stop recording session."""
        # Restore mouse cursor
        self.root.config(cursor="arrow")
        
        self.session.stop_recording_session()
        
        # Stop OBS instances
        if self.obs_gaze.connected:
            self.obs_gaze.stop_virtual_camera()
        
        if self.obs_combined.connected:
            self.obs_combined.stop_recording()
        
        # Release camera
        if self.gaze_cap:
            self.gaze_cap.release()
            self.gaze_cap = None
        
        # Reset gaze tracking
        self.last_gaze_pos = None
        self.gaze_detection_failures = 0
        
        # Save gaze data
        self.session.save_gaze_data()
        
        # Log final statistics
        if self.session.gaze_data:
            total_frames = self.current_frame_num - self.session.gaze_data[0]['frame'] + 1
            recorded_frames = len(self.session.gaze_data)
            coverage = (recorded_frames / total_frames * 100) if total_frames > 0 else 0
            print(f"📊 Gaze coverage: {recorded_frames}/{total_frames} frames ({coverage:.1f}%)")
        
        # Update UI
        self.record_btn.config(text="⏺ START RECORDING", bg='#d32f2f')
        self.update_status(f"Recording stopped - {len(self.session.gaze_data)} frames captured", '#4caf50')
        
        # Stop playback
        if self.playing:
            self.toggle_playback()
    
    # ===== POST-PROCESSING =====
    
    def process_results(self):
        """Process recording results."""
        if not self.session.output_dir or not self.session.gaze_data:
            messagebox.showwarning("No Data", "Please record a session first")
            return
        
        # Confirm
        if not messagebox.askyesno("Process Results", 
                                   f"Process {len(self.session.gaze_data)} gaze frames?\n"
                                   "This will generate heatmaps, overlay video, and statistics."):
            return
        
        self.update_status("Processing... This may take a few minutes", '#ff9800')
        
        # Run in thread to avoid freezing GUI
        thread = threading.Thread(target=self._process_results_thread, daemon=True)
        thread.start()
    
    def _process_results_thread(self):
        """Process results in background thread."""
        try:
            df = pd.DataFrame(self.session.gaze_data)
            
            # Generate heatmaps per scene
            for scene in self.session.scenes:
                scene_data = df[df['scene_name'] == scene.name].to_dict('records')
                if scene_data:
                    heatmap_path = os.path.join(self.session.output_dir, f"heatmap_{scene.name}.png")
                    generate_heatmap(scene_data, self.session.width, self.session.height, 
                                   scene.name, heatmap_path)
            
            # Generate ROI statistics
            generate_roi_statistics(self.session.gaze_data, self.session.scenes, self.session.output_dir)
            
            # Generate overlay video
            video_path = os.path.join(self.session.output_dir, "overlay_video.mp4")
            create_overlay_video_with_bar_chart(self.session, video_path, 
                                               progress_callback=lambda p: self.update_status(f"Creating video... {p}%", '#ff9800'))
            
            self.root.after(0, lambda: self.update_status(f"✓ Processing complete! Results in: {self.session.output_dir}", '#4caf50'))
            self.root.after(0, lambda: messagebox.showinfo("Complete", f"Processing complete!\n\nResults saved to:\n{self.session.output_dir}"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Processing failed:\n{e}"))
            self.root.after(0, lambda: self.update_status("Processing failed", '#f44336'))
    
    # ===== PROJECT MANAGEMENT =====
    
    def save_project(self):
        """Save project configuration."""
        if not self.session.video_cap:
            messagebox.showwarning("No Project", "Please load a video first")
            return
        
        filepath = filedialog.asksaveasfilename(
            title="Save Project",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                self.session.save_project(filepath)
                self.update_status(f"Project saved: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save project:\n{e}")
    
    def load_project(self):
        """Load project configuration."""
        filepath = filedialog.askopenfilename(
            title="Load Project",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                self.session.load_project(filepath)
                
                # Update UI
                self.frame_slider.config(to=self.session.total_frames - 1)
                self.current_frame_num = 0
                self.refresh_scene_list()
                self.render_frame()
                self.update_status(f"Project loaded: {os.path.basename(filepath)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load project:\n{e}")
    
    def toggle_virtual_camera(self):
        """Toggle virtual camera on gaze-only OBS."""
        if not self.obs_gaze.connected:
            messagebox.showwarning("Not Connected", "OBS-GazeOnly is not connected.")
            return
        
        is_active = self.obs_gaze.is_virtual_camera_active()
        
        if is_active:
            if self.obs_gaze.stop_virtual_camera():
                self.vcam_btn.config(text="📹 Start VCam", bg='#1976d2')
                self.update_status("Virtual camera stopped", '#ff9800')
        else:
            if self.obs_gaze.start_virtual_camera():
                self.vcam_btn.config(text="📹 Stop VCam", bg='#f44336')
                self.update_status("Virtual camera started - Outputting eye gaze only", '#4caf50')
    
    def on_close(self):
        """Handle window close."""
        if self.session.recording_active:
            if messagebox.askyesno("Recording Active", "Recording is active. Stop and exit?"):
                self.stop_recording()
            else:
                return
        
        # Disconnect all OBS instances
        self.obs_gaze.disconnect()
        self.obs_combined.disconnect()
        self.session.cleanup()
        self.root.destroy()


print("Main GUI application (Part 2) loaded.")

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoROIDemoGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    
    print("\n" + "=" * 80)
    print("GUI READY - Starting application")
    print("=" * 80 + "\n")
    
    root.mainloop()
