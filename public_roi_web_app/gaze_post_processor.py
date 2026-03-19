"""
================================================================================
Gaze Data Post-Processor
================================================================================

Generic gaze data processing and synchronization module for SOROT.
Handles data alignment, ROI mapping, and export formatting.

Author: Kahlil Gibran Al Zulmi
Date: 2026-02-18
================================================================================
"""

from typing import Dict, List, Optional, Any
import os
import pandas as pd
import numpy as np
from datetime import datetime
from tqdm import tqdm


class GazePostProcessor:
    """Generic post-processing engine for gaze data synchronization and ROI mapping.
    
    This processor handles:
    - Timestamp synchronization between gaze and video timelines
    - Coordinate mapping to video resolution
    - ROI hit detection
    - Data export formatting
    
    Note: This is a data processor, not a gaze detector. Gaze coordinates
    should come from external sources (CSV import, mouse tracking, or
    pre-processed eye tracking data).
    """
    
    def __init__(
        self, 
        session_dir: str, 
        obs_video_path: Optional[str], 
        ad_video_info: Dict[str, Any], 
        scenes: List[Dict[str, Any]], 
        timestamps: List[Dict[str, Any]]
    ) -> None:
        """Initialize post-processor.
        
        Args:
            session_dir: Directory to save output files.
            obs_video_path: Path to recorded video (may be None for mouse-only mode).
            ad_video_info: Dict with video metadata (width, height, fps, etc.).
            scenes: List of scene definitions with ROIs.
            timestamps: List of {frame_num, ad_timestamp, obs_timestamp} for sync.
        """
        self.session_dir = session_dir
        self.obs_video_path = obs_video_path
        self.ad_video_info = ad_video_info
        self.scenes = scenes
        self.timestamps = timestamps
        
        self.gaze_data: List[Dict[str, Any]] = []
        self.processing_progress: int = 0
        
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
        Simple proportional scaling.
        """
        ad_width = self.ad_video_info['width']
        ad_height = self.ad_video_info['height']
        
        # Proportional mapping
        mapped_x = int(round(gaze_x * (ad_width - 1) / (obs_width - 1)))
        mapped_y = int(round(gaze_y * (ad_height - 1) / (obs_height - 1)))
        
        # Clamp to video bounds
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
