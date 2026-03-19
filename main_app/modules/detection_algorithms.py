"""
Eye Detection Algorithms Module
Implements 5 different eye/pupil detection methods and Kalman filtering.

Methods:
1. Hough Circle Transform - Geometric circle detection
2. Contour-based - Shape analysis and fitting
3. Color-based - Threshold and color segmentation
4. Combined - Hybrid approach using multiple methods
5. Blob Detector - SimpleBlobDetector with custom parameters

Author: Eye Tracker Research Project
Date: November 2025
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import concurrent.futures
from utils.logger import log_info, log_warning, log_error, log_debug


# ============================================================================
# KALMAN FILTER
# ============================================================================

def create_kalman_filter() -> cv2.KalmanFilter:
    """
    Create and initialize a Kalman filter for gaze smoothing.
    
    State vector: [x, y, vx, vy] (position and velocity)
    Measurement: [x, y] (observed position)
    
    Returns:
        cv2.KalmanFilter: Initialized Kalman filter
    """
    kf = cv2.KalmanFilter(4, 2)  # 4 state variables, 2 measurements
    
    # State transition matrix (predict next state)
    kf.transitionMatrix = np.array([
        [1, 0, 1, 0],  # x = x + vx
        [0, 1, 0, 1],  # y = y + vy
        [0, 0, 1, 0],  # vx = vx
        [0, 0, 0, 1]   # vy = vy
    ], dtype=np.float32)
    
    # Measurement matrix (map state to measurement)
    kf.measurementMatrix = np.array([
        [1, 0, 0, 0],  # measure x
        [0, 1, 0, 0]   # measure y
    ], dtype=np.float32)
    
    # Process noise covariance
    kf.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03
    
    # Measurement noise covariance
    kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 0.1
    
    # Initial state covariance
    kf.errorCovPost = np.eye(4, dtype=np.float32)
    
    return kf


def apply_kalman_filter(
    detections: List[Tuple[int, int, int]],
    min_detections: int = 3
) -> List[Tuple[int, int, int]]:
    """
    Apply Kalman filtering to smooth gaze trajectory.
    
    Args:
        detections: List of (x, y, radius) tuples
        min_detections: Minimum number of detections to apply filter
        
    Returns:
        List of smoothed (x, y, radius) tuples
    """
    if len(detections) < min_detections:
        log_debug(f"Not enough detections ({len(detections)}) for Kalman filtering")
        return detections
    
    kf = create_kalman_filter()
    smoothed = []
    
    # Initialize with first detection
    first_x, first_y, first_r = detections[0]
    kf.statePre = np.array([[first_x], [first_y], [0], [0]], dtype=np.float32)
    kf.statePost = np.array([[first_x], [first_y], [0], [0]], dtype=np.float32)
    
    for x, y, radius in detections:
        # Prediction step
        prediction = kf.predict()
        
        # Measurement step
        measurement = np.array([[x], [y]], dtype=np.float32)
        
        # Correction step
        corrected = kf.correct(measurement)
        
        # Extract smoothed position
        smoothed_x = int(corrected[0][0])
        smoothed_y = int(corrected[1][0])
        
        smoothed.append((smoothed_x, smoothed_y, radius))
    
    log_info(f"Applied Kalman filter to {len(detections)} detections")
    return smoothed


# ============================================================================
# METHOD 1: HOUGH CIRCLE TRANSFORM
# ============================================================================

def detect_hough_circle(
    frame: np.ndarray,
    params: Optional[Dict[str, Any]] = None
) -> List[Tuple[int, int, int]]:
    """
    Detect pupils/eyes using Hough Circle Transform.
    
    Args:
        frame: Input frame (BGR or grayscale)
        params: Detection parameters dict with keys:
            - dp: Inverse ratio of accumulator resolution (default: 1.2)
            - minDist: Minimum distance between circle centers (default: 50)
            - param1: Canny edge detector threshold (default: 50)
            - param2: Accumulator threshold (default: 30)
            - minRadius: Minimum circle radius (default: 10)
            - maxRadius: Maximum circle radius (default: 80)
            - blur_kernel: Gaussian blur kernel size (default: 5)
    
    Returns:
        List of (x, y, radius) tuples for detected circles
    """
    # Default parameters
    default_params = {
        'dp': 1.2,
        'minDist': 50,
        'param1': 50,
        'param2': 30,
        'minRadius': 10,
        'maxRadius': 80,
        'blur_kernel': 5
    }
    
    if params:
        default_params.update(params)
    
    # Convert to grayscale if needed
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame.copy()
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(
        gray,
        (default_params['blur_kernel'], default_params['blur_kernel']),
        0
    )
    
    # Detect circles using Hough Transform
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=default_params['dp'],
        minDist=default_params['minDist'],
        param1=default_params['param1'],
        param2=default_params['param2'],
        minRadius=default_params['minRadius'],
        maxRadius=default_params['maxRadius']
    )
    
    detections = []
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for circle in circles[0, :]:
            x, y, r = int(circle[0]), int(circle[1]), int(circle[2])
            detections.append((x, y, r))
    
    return detections


# ============================================================================
# METHOD 2: CONTOUR-BASED DETECTION
# ============================================================================

def detect_contour(
    frame: np.ndarray,
    params: Optional[Dict[str, Any]] = None
) -> List[Tuple[int, int, int]]:
    """
    Detect pupils/eyes using contour analysis and ellipse fitting.
    
    Args:
        frame: Input frame (BGR or grayscale)
        params: Detection parameters dict with keys:
            - threshold_value: Binary threshold value (default: 30)
            - min_area: Minimum contour area (default: 100)
            - max_area: Maximum contour area (default: 5000)
            - circularity_threshold: Min circularity 0-1 (default: 0.7)
            - blur_kernel: Gaussian blur kernel size (default: 5)
    
    Returns:
        List of (x, y, radius) tuples for detected pupils
    """
    # Default parameters
    default_params = {
        'threshold_value': 30,
        'min_area': 100,
        'max_area': 5000,
        'circularity_threshold': 0.7,
        'blur_kernel': 5
    }
    
    if params:
        default_params.update(params)
    
    # Convert to grayscale if needed
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame.copy()
    
    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(
        gray,
        (default_params['blur_kernel'], default_params['blur_kernel']),
        0
    )
    
    # Apply binary threshold (pupil is usually darker)
    _, binary = cv2.threshold(
        blurred,
        default_params['threshold_value'],
        255,
        cv2.THRESH_BINARY_INV
    )
    
    # Find contours
    contours, _ = cv2.findContours(
        binary,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )
    
    detections = []
    for contour in contours:
        area = cv2.contourArea(contour)
        
        # Filter by area
        if area < default_params['min_area'] or area > default_params['max_area']:
            continue
        
        # Calculate circularity
        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            continue
        
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        
        # Filter by circularity
        if circularity < default_params['circularity_threshold']:
            continue
        
        # Fit ellipse if contour has enough points
        if len(contour) >= 5:
            try:
                ellipse = cv2.fitEllipse(contour)
                center_x = int(ellipse[0][0])
                center_y = int(ellipse[0][1])
                radius = int((ellipse[1][0] + ellipse[1][1]) / 4)  # Average of axes / 2
                
                detections.append((center_x, center_y, radius))
            except:
                # If ellipse fitting fails, use moment-based center
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    radius = int(np.sqrt(area / np.pi))
                    detections.append((cx, cy, radius))
    
    return detections


# ============================================================================
# METHOD 3: COLOR-BASED DETECTION
# ============================================================================

def detect_color(
    frame: np.ndarray,
    params: Optional[Dict[str, Any]] = None
) -> List[Tuple[int, int, int]]:
    """
    Detect pupils/eyes using color segmentation in HSV space.
    
    Args:
        frame: Input frame (must be BGR)
        params: Detection parameters dict with keys:
            - lower_h, lower_s, lower_v: Lower HSV bounds (default: 0, 0, 0)
            - upper_h, upper_s, upper_v: Upper HSV bounds (default: 180, 255, 50)
            - min_area: Minimum blob area (default: 100)
            - max_area: Maximum blob area (default: 5000)
            - morph_kernel: Morphological operation kernel size (default: 5)
    
    Returns:
        List of (x, y, radius) tuples for detected pupils
    """
    # Default parameters (targeting dark pupils)
    default_params = {
        'lower_h': 0,
        'lower_s': 0,
        'lower_v': 0,
        'upper_h': 180,
        'upper_s': 255,
        'upper_v': 50,
        'min_area': 100,
        'max_area': 5000,
        'morph_kernel': 5
    }
    
    if params:
        default_params.update(params)
    
    # Convert to HSV
    if len(frame.shape) == 3:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    else:
        # Convert grayscale to BGR first, then to HSV
        bgr = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    
    # Define color range
    lower_bound = np.array([
        default_params['lower_h'],
        default_params['lower_s'],
        default_params['lower_v']
    ])
    upper_bound = np.array([
        default_params['upper_h'],
        default_params['upper_s'],
        default_params['upper_v']
    ])
    
    # Create mask
    mask = cv2.inRange(hsv, lower_bound, upper_bound)
    
    # Morphological operations to clean up mask
    kernel_size = default_params['morph_kernel']
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # Find contours in mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    detections = []
    for contour in contours:
        area = cv2.contourArea(contour)
        
        # Filter by area
        if area < default_params['min_area'] or area > default_params['max_area']:
            continue
        
        # Get bounding circle
        (x, y), radius = cv2.minEnclosingCircle(contour)
        
        detections.append((int(x), int(y), int(radius)))
    
    return detections


# ============================================================================
# METHOD 4: COMBINED DETECTION
# ============================================================================

def detect_combined(
    frame: np.ndarray,
    params: Optional[Dict[str, Any]] = None
) -> List[Tuple[int, int, int]]:
    """
    Combined detection using multiple methods with voting/consensus.
    
    Uses Hough Circle, Contour, and Color-based methods, then clusters
    nearby detections to find consensus.
    
    Args:
        frame: Input frame (BGR)
        params: Detection parameters dict with keys:
            - distance_threshold: Max distance for clustering (default: 30)
            - min_votes: Minimum votes to accept detection (default: 2)
            - Individual method params (hough_*, contour_*, color_*)
    
    Returns:
        List of (x, y, radius) tuples for detected pupils
    """
    # Default parameters
    default_params = {
        'distance_threshold': 30,
        'min_votes': 2
    }
    
    if params:
        default_params.update(params)
    
    # Extract method-specific params
    hough_params = {k[6:]: v for k, v in default_params.items() if k.startswith('hough_')}
    contour_params = {k[8:]: v for k, v in default_params.items() if k.startswith('contour_')}
    color_params = {k[6:]: v for k, v in default_params.items() if k.startswith('color_')}
    
    # Run all three detection methods
    hough_detections = detect_hough_circle(frame, hough_params if hough_params else None)
    contour_detections = detect_contour(frame, contour_params if contour_params else None)
    color_detections = detect_color(frame, color_params if color_params else None)
    
    # Combine all detections
    all_detections = hough_detections + contour_detections + color_detections
    
    if not all_detections:
        return []
    
    # Cluster detections by proximity
    clusters = []
    used = set()
    
    for i, (x1, y1, r1) in enumerate(all_detections):
        if i in used:
            continue
        
        cluster = [(x1, y1, r1)]
        used.add(i)
        
        for j, (x2, y2, r2) in enumerate(all_detections):
            if j in used:
                continue
            
            # Calculate distance
            distance = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
            
            if distance <= default_params['distance_threshold']:
                cluster.append((x2, y2, r2))
                used.add(j)
        
        clusters.append(cluster)
    
    # Filter clusters by minimum votes and average positions
    detections = []
    for cluster in clusters:
        if len(cluster) >= default_params['min_votes']:
            # Average position and radius
            avg_x = int(np.mean([x for x, y, r in cluster]))
            avg_y = int(np.mean([y for x, y, r in cluster]))
            avg_r = int(np.mean([r for x, y, r in cluster]))
            
            detections.append((avg_x, avg_y, avg_r))
    
    return detections


# ============================================================================
# METHOD 5: BLOB DETECTOR
# ============================================================================

def detect_blob(
    frame: np.ndarray,
    params: Optional[Dict[str, Any]] = None
) -> List[Tuple[int, int, int]]:
    """
    Detect pupils/eyes using SimpleBlobDetector with custom parameters.
    
    Args:
        frame: Input frame (BGR or grayscale)
        params: Detection parameters dict with keys:
            - min_threshold: Minimum threshold (default: 10)
            - max_threshold: Maximum threshold (default: 200)
            - min_area: Minimum blob area (default: 100)
            - max_area: Maximum blob area (default: 5000)
            - min_circularity: Minimum circularity 0-1 (default: 0.7)
            - min_convexity: Minimum convexity 0-1 (default: 0.8)
            - min_inertia_ratio: Minimum inertia ratio 0-1 (default: 0.5)
    
    Returns:
        List of (x, y, radius) tuples for detected blobs
    """
    # Default parameters
    default_params = {
        'min_threshold': 10,
        'max_threshold': 200,
        'min_area': 100,
        'max_area': 5000,
        'min_circularity': 0.7,
        'min_convexity': 0.8,
        'min_inertia_ratio': 0.5
    }
    
    if params:
        default_params.update(params)
    
    # Convert to grayscale if needed
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame.copy()
    
    # Setup SimpleBlobDetector parameters
    blob_params = cv2.SimpleBlobDetector_Params()
    
    # Threshold
    blob_params.minThreshold = default_params['min_threshold']
    blob_params.maxThreshold = default_params['max_threshold']
    
    # Filter by area
    blob_params.filterByArea = True
    blob_params.minArea = default_params['min_area']
    blob_params.maxArea = default_params['max_area']
    
    # Filter by circularity
    blob_params.filterByCircularity = True
    blob_params.minCircularity = default_params['min_circularity']
    
    # Filter by convexity
    blob_params.filterByConvexity = True
    blob_params.minConvexity = default_params['min_convexity']
    
    # Filter by inertia
    blob_params.filterByInertia = True
    blob_params.minInertiaRatio = default_params['min_inertia_ratio']
    
    # Create detector
    detector = cv2.SimpleBlobDetector_create(blob_params)
    
    # Detect blobs
    keypoints = detector.detect(gray)
    
    detections = []
    for kp in keypoints:
        x = int(kp.pt[0])
        y = int(kp.pt[1])
        radius = int(kp.size / 2)
        
        detections.append((x, y, radius))
    
    return detections


# ============================================================================
# VIDEO PROCESSING FUNCTIONS
# ============================================================================

def process_frame_with_method(
    frame: np.ndarray,
    method: str,
    params: Optional[Dict[str, Any]] = None,
    apply_kalman: bool = False
) -> Tuple[List[Tuple[int, int, int]], np.ndarray]:
    """
    Process a single frame with specified detection method.
    
    Args:
        frame: Input frame
        method: Detection method name ('hough', 'contour', 'color', 'combined', 'blob')
        params: Method-specific parameters
        apply_kalman: Whether to apply Kalman filtering (needs history)
    
    Returns:
        Tuple of (detections, annotated_frame)
    """
    # Dispatch to appropriate method
    method_map = {
        'hough': detect_hough_circle,
        'contour': detect_contour,
        'color': detect_color,
        'combined': detect_combined,
        'blob': detect_blob
    }
    
    if method not in method_map:
        log_error(f"Unknown detection method: {method}")
        return [], frame.copy()
    
    # Run detection
    detections = method_map[method](frame, params)
    
    # Annotate frame
    annotated = frame.copy()
    for x, y, r in detections:
        cv2.circle(annotated, (x, y), r, (0, 255, 0), 2)
        cv2.circle(annotated, (x, y), 2, (0, 0, 255), 3)
    
    return detections, annotated


def process_video_single_method(
    video_path: str,
    output_path: str,
    method: str,
    params: Optional[Dict[str, Any]] = None,
    apply_kalman: bool = True,
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Process entire video with a single detection method.
    
    Args:
        video_path: Path to input video
        output_path: Path to save annotated video
        method: Detection method name
        params: Method-specific parameters
        apply_kalman: Whether to apply Kalman filtering
        progress_callback: Optional callback(frame_num, total_frames, detections)
    
    Returns:
        Dictionary with processing results and statistics
    """
    log_info(f"Processing video: {video_path} with method: {method}")
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        log_error(f"Failed to open video: {video_path}")
        return {'success': False, 'error': 'Failed to open video'}
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Process frames
    all_detections = []
    frame_num = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect
        detections, annotated = process_frame_with_method(frame, method, params)
        all_detections.append(detections)
        
        # Write annotated frame
        out.write(annotated)
        
        frame_num += 1
        
        # Progress callback
        if progress_callback:
            progress_callback(frame_num, total_frames, detections)
    
    # Apply Kalman filtering if requested
    if apply_kalman and all_detections:
        # Flatten all detections
        flat_detections = [d for frame_dets in all_detections for d in frame_dets]
        if flat_detections:
            smoothed = apply_kalman_filter(flat_detections)
            log_info(f"Applied Kalman filtering to {len(flat_detections)} detections")
    
    # Cleanup
    cap.release()
    out.release()
    
    # Calculate statistics
    frames_with_detection = sum(1 for dets in all_detections if len(dets) > 0)
    total_detections = sum(len(dets) for dets in all_detections)
    
    results = {
        'success': True,
        'method': method,
        'total_frames': total_frames,
        'frames_with_detection': frames_with_detection,
        'detection_rate': frames_with_detection / total_frames if total_frames > 0 else 0,
        'total_detections': total_detections,
        'avg_detections_per_frame': total_detections / total_frames if total_frames > 0 else 0,
        'output_path': output_path
    }
    
    log_info(f"Video processing complete: {results}")
    return results


def process_video_parallel(
    video_path: str,
    output_dir: str,
    methods: List[str],
    params_dict: Optional[Dict[str, Dict[str, Any]]] = None,
    apply_kalman: bool = True,
    max_workers: int = 3
) -> Dict[str, Dict[str, Any]]:
    """
    Process video with multiple methods in parallel.
    
    Args:
        video_path: Path to input video
        output_dir: Directory to save output videos
        methods: List of method names to use
        params_dict: Dict mapping method names to their params
        apply_kalman: Whether to apply Kalman filtering
        max_workers: Maximum number of parallel workers
    
    Returns:
        Dictionary mapping method names to their results
    """
    import os
    
    log_info(f"Processing video with {len(methods)} methods in parallel")
    
    # Prepare output paths
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_paths = {
        method: os.path.join(output_dir, f"{video_name}_{method}.mp4")
        for method in methods
    }
    
    # Process methods in parallel
    results = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_method = {
            executor.submit(
                process_video_single_method,
                video_path,
                output_paths[method],
                method,
                params_dict.get(method) if params_dict else None,
                apply_kalman
            ): method
            for method in methods
        }
        
        # Collect results
        for future in concurrent.futures.as_completed(future_to_method):
            method = future_to_method[future]
            try:
                result = future.result()
                results[method] = result
                log_info(f"Completed processing with method: {method}")
            except Exception as e:
                log_error(f"Error processing with method {method}: {str(e)}")
                results[method] = {'success': False, 'error': str(e)}
    
    return results


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_default_params(method: str) -> Dict[str, Any]:
    """
    Get default parameters for a detection method.
    
    Args:
        method: Detection method name
        
    Returns:
        Dictionary of default parameters
    """
    defaults = {
        'hough': {
            'dp': 1.2,
            'minDist': 50,
            'param1': 50,
            'param2': 30,
            'minRadius': 10,
            'maxRadius': 80,
            'blur_kernel': 5
        },
        'contour': {
            'threshold_value': 30,
            'min_area': 100,
            'max_area': 5000,
            'circularity_threshold': 0.7,
            'blur_kernel': 5
        },
        'color': {
            'lower_h': 0,
            'lower_s': 0,
            'lower_v': 0,
            'upper_h': 180,
            'upper_s': 255,
            'upper_v': 50,
            'min_area': 100,
            'max_area': 5000,
            'morph_kernel': 5
        },
        'combined': {
            'distance_threshold': 30,
            'min_votes': 2
        },
        'blob': {
            'min_threshold': 10,
            'max_threshold': 200,
            'min_area': 100,
            'max_area': 5000,
            'min_circularity': 0.7,
            'min_convexity': 0.8,
            'min_inertia_ratio': 0.5
        }
    }
    
    return defaults.get(method, {})


def validate_detection(
    x: int,
    y: int,
    radius: int,
    frame_width: int,
    frame_height: int,
    min_radius: int = 5,
    max_radius: int = 100
) -> bool:
    """
    Validate that a detection is within reasonable bounds.
    
    Args:
        x, y: Detection center coordinates
        radius: Detection radius
        frame_width, frame_height: Frame dimensions
        min_radius, max_radius: Acceptable radius range
        
    Returns:
        True if detection is valid, False otherwise
    """
    # Check if within frame bounds
    if x < 0 or x >= frame_width or y < 0 or y >= frame_height:
        return False
    
    # Check radius
    if radius < min_radius or radius > max_radius:
        return False
    
    # Check if circle is fully within frame
    if x - radius < 0 or x + radius >= frame_width:
        return False
    if y - radius < 0 or y + radius >= frame_height:
        return False
    
    return True


if __name__ == "__main__":
    # Test code
    print("Detection Algorithms Module")
    print(f"Available methods: hough, contour, color, combined, blob")
    print(f"Use process_video_single_method() or process_video_parallel() for video processing")
