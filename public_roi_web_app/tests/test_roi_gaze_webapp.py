"""
================================================================================
ROI & GAZE CONNECTION TEST - WEB APP
================================================================================

Web-based test application for ROI and eye gaze connection testing.
Features:
- Full-screen browser interface
- Real-time gaze tracking visualization
- ROI hit detection with live statistics
- Mirrors main app functionality

Run: python test_roi_gaze_webapp.py
Then open: http://localhost:5001
Press F11 for full-screen mode
================================================================================
"""

from flask import Flask, render_template, Response, jsonify, request
import cv2
import numpy as np
import json
import time
import threading
from collections import defaultdict
import base64

app = Flask(__name__)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

VIRTUAL_CAMERA_INDEX = 0
PORT = 5001

# Eye gaze detection parameters
HOUGH_PARAM1 = 50
HOUGH_PARAM2 = 13
MIN_RADIUS = 65
MAX_RADIUS = 80

# Frame resolution (will be detected from camera)
FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080

# Test ROIs (normalized coordinates 0-1)
TEST_ROIS = [
    {'id': 1, 'name': 'Top-Left', 'x': 0.05, 'y': 0.1, 'width': 0.25, 'height': 0.25, 'color': '#00FFFF'},
    {'id': 2, 'name': 'Top-Right', 'x': 0.70, 'y': 0.1, 'width': 0.25, 'height': 0.25, 'color': '#FF00FF'},
    {'id': 3, 'name': 'Center', 'x': 0.35, 'y': 0.35, 'width': 0.30, 'height': 0.30, 'color': '#FFFF00'},
    {'id': 4, 'name': 'Bottom-Left', 'x': 0.05, 'y': 0.65, 'width': 0.25, 'height': 0.25, 'color': '#00FF00'},
    {'id': 5, 'name': 'Bottom-Right', 'x': 0.70, 'y': 0.65, 'width': 0.25, 'height': 0.25, 'color': '#FF8000'},
]

# Global state
gaze_cap = None
current_gaze = None
last_gaze_pos = None
roi_stats = defaultdict(int)
total_frames = 0
detected_frames = 0
is_running = False
gaze_thread = None
fps = 0.0
detection_count = 0  # Track stable detections before using Kalman

# ==============================================================================
# GAZE DETECTION
# ==============================================================================

def detect_gaze_hough(frame):
    """Detect eye gaze using Hough Circle Transform."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    
    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=1000,
        param1=HOUGH_PARAM1,
        param2=HOUGH_PARAM2,
        minRadius=MIN_RADIUS,
        maxRadius=MAX_RADIUS
    )
    
    if circles is not None:
        circle = np.uint16(np.around(circles[0, 0]))
        return (int(circle[0]), int(circle[1]))
    
    return None


# Initialize Kalman Filter for smooth gaze tracking
kalman = cv2.KalmanFilter(4, 2)
kalman.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
kalman.transitionMatrix = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)
kalman.processNoiseCov = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32) * 0.03
kalman.measurementNoiseCov = np.array([[1, 0], [0, 1]], np.float32) * 5.0
kalman_initialized = False


def apply_kalman_filter(gaze_pos):
    """Apply Kalman filter to smooth gaze position."""
    global kalman_initialized, detection_count
    
    # Don't use Kalman for first few frames to avoid initialization issues
    detection_count += 1
    if detection_count < 5:
        return gaze_pos
    
    if not kalman_initialized:
        kalman.statePost = np.array([[float(gaze_pos[0])], [float(gaze_pos[1])], [0.0], [0.0]], np.float32)
        kalman_initialized = True
        print(f"✓ Kalman filter initialized with position: {gaze_pos}")
    
    # Predict next state
    prediction = kalman.predict()
    
    # Correct with measurement
    measurement = np.array([[float(gaze_pos[0])], [float(gaze_pos[1])]], np.float32)
    kalman.correct(measurement)
    
    smoothed = (int(prediction[0][0]), int(prediction[1][0]))
    return smoothed


def find_roi_at_gaze(gaze_x, gaze_y, frame_width, frame_height):
    """Find which ROI contains the gaze position."""
    for roi in TEST_ROIS:
        # Convert normalized coordinates to pixel coordinates
        x = int(roi['x'] * frame_width)
        y = int(roi['y'] * frame_height)
        w = int(roi['width'] * frame_width)
        h = int(roi['height'] * frame_height)
        
        if x <= gaze_x <= x + w and y <= gaze_y <= y + h:
            return roi
    return None


def gaze_detection_loop():
    """Continuous gaze detection loop."""
    global current_gaze, last_gaze_pos, roi_stats, total_frames, detected_frames, is_running, fps, FRAME_WIDTH, FRAME_HEIGHT, detection_count
    
    fps_start = time.time()
    fps_counter = 0
    
    print(f"✓ Gaze detection loop started")
    
    while is_running:
        if gaze_cap is None or not gaze_cap.isOpened():
            time.sleep(0.1)
            continue
        
        ret, frame = gaze_cap.read()
        if not ret:
            time.sleep(0.01)
            continue
        
        # Detect actual frame size
        frame_height, frame_width = frame.shape[:2]
        FRAME_WIDTH = frame_width
        FRAME_HEIGHT = frame_height
        
        total_frames += 1
        fps_counter += 1
        
        # Detect gaze
        detected_gaze = detect_gaze_hough(frame)
        
        if detected_gaze:
            # Validate coordinates are in reasonable range
            if 0 <= detected_gaze[0] <= frame_width and 0 <= detected_gaze[1] <= frame_height:
                # Apply Kalman filter for smoothing (after stabilization)
                smoothed_gaze = apply_kalman_filter(detected_gaze)
                
                current_gaze = {
                    'x': smoothed_gaze[0],
                    'y': smoothed_gaze[1],
                    'timestamp': time.time(),
                    'raw_x': detected_gaze[0],
                    'raw_y': detected_gaze[1],
                    'frame_width': frame_width,
                    'frame_height': frame_height,
                    'detection_stable': detection_count >= 5
                }
                last_gaze_pos = smoothed_gaze
                detected_frames += 1
                
                # Check ROI hit
                active_roi = find_roi_at_gaze(smoothed_gaze[0], smoothed_gaze[1], frame_width, frame_height)
                
                if active_roi:
                    roi_stats[active_roi['name']] += 1
                    current_gaze['roi'] = active_roi['name']
                    current_gaze['roi_id'] = active_roi['id']
                else:
                    roi_stats['Background'] += 1
                    current_gaze['roi'] = 'Background'
                    current_gaze['roi_id'] = 0
        else:
            # Use last known position
            if last_gaze_pos:
                current_gaze = {
                    'x': last_gaze_pos[0],
                    'y': last_gaze_pos[1],
                    'timestamp': time.time(),
                    'fallback': True,
                    'frame_width': frame_width,
                    'frame_height': frame_height
                }
        
        # Calculate FPS
        if fps_counter >= 30:
            fps_end = time.time()
            fps = fps_counter / (fps_end - fps_start)
            fps_start = time.time()
            fps_counter = 0
        
        time.sleep(0.005)  # Slightly faster loop


def start_gaze_detection():
    """Start gaze detection in background thread."""
    global gaze_cap, is_running, gaze_thread, detection_count
    
    if gaze_cap is None:
        gaze_cap = cv2.VideoCapture(VIRTUAL_CAMERA_INDEX)
        gaze_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        gaze_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        if not gaze_cap.isOpened():
            print(f"❌ Failed to open virtual camera at index {VIRTUAL_CAMERA_INDEX}")
            return False
    
    if not is_running:
        is_running = True
        detection_count = 0  # Reset detection count
        gaze_thread = threading.Thread(target=gaze_detection_loop, daemon=True)
        gaze_thread.start()
        print("✓ Gaze detection started")
    
    return True


def stop_gaze_detection():
    """Stop gaze detection."""
    global gaze_cap, is_running
    
    is_running = False
    if gaze_thread:
        gaze_thread.join(timeout=1.0)
    
    if gaze_cap:
        gaze_cap.release()
        gaze_cap = None
    
    print("✓ Gaze detection stopped")


# ==============================================================================
# FLASK ROUTES
# ==============================================================================

@app.route('/')
def index():
    """Serve the main test page."""
    return render_template('test_roi_gaze.html', rois=TEST_ROIS)


@app.route('/api/start', methods=['POST'])
def api_start():
    """Start gaze detection."""
    success = start_gaze_detection()
    return jsonify({'success': success})


@app.route('/api/stop', methods=['POST'])
def api_stop():
    """Stop gaze detection."""
    stop_gaze_detection()
    return jsonify({'success': True})


@app.route('/api/reset', methods=['POST'])
def api_reset():
    """Reset statistics."""
    global roi_stats, total_frames, detected_frames
    roi_stats.clear()
    total_frames = 0
    detected_frames = 0
    return jsonify({'success': True})


@app.route('/api/gaze')
def api_gaze():
    """Get current gaze data."""
    detection_rate = (detected_frames / total_frames * 100) if total_frames > 0 else 0
    
    return jsonify({
        'gaze': current_gaze,
        'stats': dict(roi_stats),
        'total_frames': total_frames,
        'detected_frames': detected_frames,
        'detection_rate': detection_rate,
        'fps': fps,
        'is_running': is_running
    })


@app.route('/api/save_results', methods=['POST'])
def api_save_results():
    """Save test results to file."""
    results = {
        'timestamp': time.time(),
        'total_frames': total_frames,
        'detected_frames': detected_frames,
        'detection_rate': (detected_frames / total_frames * 100) if total_frames > 0 else 0,
        'roi_stats': dict(roi_stats),
        'fps': fps,
        'test_rois': TEST_ROIS
    }
    
    filename = f"test_results_{int(time.time())}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    return jsonify({'success': True, 'filename': filename})


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("ROI & GAZE CONNECTION TEST - WEB APP")
    print("=" * 80)
    print(f"Virtual Camera Index: {VIRTUAL_CAMERA_INDEX}")
    print(f"Port: {PORT}")
    print(f"Number of Test ROIs: {len(TEST_ROIS)}")
    print("\nStarting server...")
    print(f"\n✓ Open browser to: http://localhost:{PORT}")
    print("  Press F11 in browser for full-screen mode")
    print("  Press Ctrl+C to stop server")
    print("=" * 80 + "\n")
    
    try:
        app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n\n⏹ Server stopped by user")
        stop_gaze_detection()
