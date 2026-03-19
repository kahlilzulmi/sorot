"""
================================================================================
GAZE POST-PROCESSOR MODULE
================================================================================
Post-processing engine for eye gaze detection using Hough Circle Transform.
Processes OBS recordings and syncs with advertisement video timeline.

Author: Auto-generated
Date: 2026-02-05
================================================================================
"""

import cv2
import numpy as np
import pandas as pd
import os
from datetime import datetime
from tqdm import tqdm


class GazePostProcessor:
    """Post-processing engine for gaze detection from recorded videos."""
    
    def __init__(self, session_dir, obs_video_path, ad_video_info, scenes, timestamps):
        """
        Initialize post-processor.
        
        Args:
            session_dir: Directory to save output
            obs_video_path: Path to OBS recording (user's face)
            ad_video_info: Dict with ad video metadata
            scenes: List of scene definitions with ROIs
            timestamps: List of {frame_num, ad_timestamp, start_time} for sync
        """
        self.session_dir = session_dir
        self.obs_video_path = obs_video_path
        self.ad_video_info = ad_video_info
        self.scenes = scenes
        self.timestamps = timestamps
        
        # Detection parameters (from detect_houghcircletransform.py)
        self.HOUGH_PARAM1 = 50
        self.HOUGH_PARAM2 = 13
        self.MIN_RADIUS = 70
        self.MAX_RADIUS = 75
        
        self.gaze_data = []
        self.processing_progress = 0
        
    def detect_gaze_hough(self, bgr_frame):
        """
        Detect gaze using Hough Circle Transform.
        Returns (x, y) coordinates or None if not detected.
        """
        gray_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
        gray_frame = cv2.medianBlur(gray_frame, 5)
        
        circles = cv2.HoughCircles(
            gray_frame,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=gray_frame.shape[0],
            param1=self.HOUGH_PARAM1,
            param2=self.HOUGH_PARAM2,
            minRadius=self.MIN_RADIUS,
            maxRadius=self.MAX_RADIUS
        )
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            circle = circles[0][0]
            center = (int(circle[0]), int(circle[1]))
            return center
        
        return None
    
    def map_gaze_to_video(self, gaze_x, gaze_y, obs_width, obs_height):
        """
        Map gaze coordinates from OBS recording to ad video resolution.
        
        The Tobii Ghost overlay shows the gaze position on the screen being recorded.
        We detect the comet in the OBS frame and need to map to ad video coordinates.
        
        This method assumes:
        1. OBS is recording the browser window showing the ad video
        2. The ad video might not fill the entire OBS frame (browser chrome, etc.)
        3. We need to preserve aspect ratios to avoid distortion
        
        For better accuracy, use calibration to establish the transformation matrix.
        """
        ad_width = self.ad_video_info['width']
        ad_height = self.ad_video_info['height']
        
        # Calculate aspect ratios
        obs_aspect = obs_width / obs_height
        ad_aspect = ad_width / ad_height
        
        # If aspect ratios match, use simple proportional scaling
        if abs(obs_aspect - ad_aspect) < 0.01:
            mapped_x = int(round(gaze_x * ad_width / obs_width))
            mapped_y = int(round(gaze_y * ad_height / obs_height))
        else:
            # Different aspect ratios - need to account for letterboxing/pillarboxing
            # Assume ad video is centered in OBS frame with letterbox/pillarbox
            
            if obs_aspect > ad_aspect:
                # OBS is wider - pillarboxing (black bars on sides)
                # Ad video height fills OBS height
                scale = obs_height / ad_height
                ad_width_in_obs = ad_width * scale
                offset_x = (obs_width - ad_width_in_obs) / 2
                
                # Map coordinates
                mapped_x = int(round((gaze_x - offset_x) * ad_width / ad_width_in_obs))
                mapped_y = int(round(gaze_y * ad_height / obs_height))
            else:
                # OBS is taller - letterboxing (black bars on top/bottom)
                # Ad video width fills OBS width
                scale = obs_width / ad_width
                ad_height_in_obs = ad_height * scale
                offset_y = (obs_height - ad_height_in_obs) / 2
                
                # Map coordinates
                mapped_x = int(round(gaze_x * ad_width / obs_width))
                mapped_y = int(round((gaze_y - offset_y) * ad_height / ad_height_in_obs))
        
        # Clamp to video bounds (handle out-of-bounds if user looked outside video area)
        mapped_x = max(0, min(ad_width - 1, mapped_x))
        mapped_y = max(0, min(ad_height - 1, mapped_y))
        
        return mapped_x, mapped_y
    
    def find_roi_at_position(self, scene, x, y):
        """Find which ROI contains the gaze point."""
        for roi in scene.get('rois', []):
            rx, ry, rw, rh = roi['x'], roi['y'], roi['width'], roi['height']
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                return roi['label']
        return 'background'
    
    def sync_timestamps(self, obs_frame_idx, obs_timestamp):
        """
        Sync OBS frame with ad video frame using timestamps.
        Returns ad_frame_num or None if out of sync.
        """
        # Find closest timestamp match
        if not self.timestamps:
            return None
        
        # Simple linear search for matching timestamp
        for ts_entry in self.timestamps:
            if abs(ts_entry['obs_timestamp'] - obs_timestamp) < 0.1:  # 100ms tolerance
                return ts_entry['ad_frame_num']
        
        return None
    
    def process(self, progress_callback=None):
        """
        Main processing pipeline.
        Returns dict with results summary.
        """
        print(f"\n{'='*80}")
        print("Starting Gaze Post-Processing...")
        print(f"{'='*80}")
        
        # Open OBS video
        obs_cap = cv2.VideoCapture(self.obs_video_path)
        if not obs_cap.isOpened():
            raise Exception(f"Cannot open OBS recording: {self.obs_video_path}")
        
        obs_width = int(obs_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        obs_height = int(obs_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        obs_fps = obs_cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(obs_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"OBS Video: {obs_width}x{obs_height} @ {obs_fps}fps, {total_frames} frames")
        print(f"Ad Video: {self.ad_video_info['width']}x{self.ad_video_info['height']}")
        
        # Process each frame
        frame_idx = 0
        detected_count = 0
        
        with tqdm(total=total_frames, desc="Processing Frames", unit="frame") as pbar:
            while True:
                ret, frame = obs_cap.read()
                if not ret:
                    break
                
                # Detect gaze in OBS frame
                gaze_pos = self.detect_gaze_hough(frame)
                
                # Calculate timestamp for this frame
                obs_timestamp = frame_idx / obs_fps
                
                # Sync with ad video timeline
                ad_frame_num = self.sync_timestamps(frame_idx, obs_timestamp)
                
                # Map to ad video coordinates
                gaze_x, gaze_y = None, None
                roi_label = 'background'
                scene_name = 'unknown'
                scene_custom_name = ''
                
                if gaze_pos and ad_frame_num is not None:
                    detected_count += 1
                    gaze_x, gaze_y = self.map_gaze_to_video(
                        gaze_pos[0], gaze_pos[1], obs_width, obs_height
                    )
                    
                    # Find current scene and ROI
                    for scene in self.scenes:
                        if scene['start_frame'] <= ad_frame_num <= scene['end_frame']:
                            scene_name = scene['name']
                            scene_custom_name = scene.get('custom_name', '')
                            roi_label = self.find_roi_at_position(scene, gaze_x, gaze_y)
                            break
                
                # Record data
                self.gaze_data.append({
                    'obs_frame': frame_idx,
                    'obs_timestamp': obs_timestamp,
                    'ad_frame': ad_frame_num,
                    'gaze_x': gaze_x,
                    'gaze_y': gaze_y,
                    'roi_label': roi_label,
                    'scene_name': scene_name,
                    'scene_custom_name': scene_custom_name,
                    'tracking_mode': 'Eye Tracking (OBS)'
                })
                
                frame_idx += 1
                self.processing_progress = int((frame_idx / total_frames) * 100)
                
                if progress_callback:
                    progress_callback(self.processing_progress)
                
                pbar.update(1)
        
        obs_cap.release()
        
        # Save gaze data to CSV
        df = pd.DataFrame(self.gaze_data)
        csv_path = os.path.join(self.session_dir, 'gaze_data_processed.csv')
        df.to_csv(csv_path, index=False)
        
        detection_rate = (detected_count / total_frames * 100) if total_frames > 0 else 0
        
        print(f"\n{'='*80}")
        print("Post-Processing Complete!")
        print(f"  Total Frames: {total_frames}")
        print(f"  Detected: {detected_count} ({detection_rate:.1f}%)")
        print(f"  Output: {csv_path}")
        print(f"{'='*80}\n")
        
        return {
            'success': True,
            'total_frames': total_frames,
            'detected_frames': detected_count,
            'detection_rate': detection_rate,
            'csv_path': csv_path,
            'gaze_data': self.gaze_data
        }
