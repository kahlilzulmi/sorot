"""
Video Alignment Module

Synchronizes and aligns multiple eye tracking videos for comparison analysis.
Supports temporal alignment, spatial registration, and multi-video playback.

Author: Kahlil Gibran Al Zulmi
NRP: 5049221015
Institution: Institut Teknologi Sepuluh Nopember
"""

import os
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from pathlib import Path

from utils.config_manager import load_config
from utils.localization import get_text
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class VideoInfo:
    """Information about a video file."""
    path: str
    fps: float
    frame_count: int
    width: int
    height: int
    duration: float
    creation_time: Optional[datetime] = None
    metadata: Dict[str, Any] = None


@dataclass
class AlignmentPoint:
    """Synchronization point across multiple videos."""
    video_indices: List[int]
    frame_numbers: List[int]
    timestamp: float
    event_type: str  # 'manual', 'audio_peak', 'flash', 'motion'
    confidence: float = 1.0


class VideoAlignmentEngine:
    """
    Engine for aligning multiple videos temporally and spatially.
    """
    
    def __init__(self):
        self.config = get_config()
        self.videos: List[VideoInfo] = []
        self.alignment_points: List[AlignmentPoint] = []
        self.time_offsets: List[float] = []  # Time offset for each video
        self.sync_method: str = 'manual'  # manual, audio, flash, motion
        
    def load_videos(self, video_paths: List[str]) -> bool:
        """
        Load multiple videos and extract metadata.
        
        Args:
            video_paths: List of paths to video files
            
        Returns:
            True if all videos loaded successfully
        """
        self.videos = []
        
        for path in video_paths:
            try:
                info = self._get_video_info(path)
                if info:
                    self.videos.append(info)
                    logger.info(f"Loaded video: {path}")
                else:
                    logger.error(f"Failed to load video: {path}")
                    return False
            except Exception as e:
                logger.error(f"Error loading video {path}: {e}")
                return False
        
        # Initialize time offsets (all start at 0)
        self.time_offsets = [0.0] * len(self.videos)
        
        return len(self.videos) > 0
    
    def _get_video_info(self, video_path: str) -> Optional[VideoInfo]:
        """
        Extract video metadata.
        
        Args:
            video_path: Path to video file
            
        Returns:
            VideoInfo object or None if failed
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return None
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        # Try to get creation time from file
        creation_time = None
        try:
            stat = os.stat(video_path)
            creation_time = datetime.fromtimestamp(stat.st_ctime)
        except:
            pass
        
        cap.release()
        
        return VideoInfo(
            path=video_path,
            fps=fps,
            frame_count=frame_count,
            width=width,
            height=height,
            duration=duration,
            creation_time=creation_time,
            metadata={}
        )
    
    def add_alignment_point(
        self,
        video_indices: List[int],
        frame_numbers: List[int],
        event_type: str = 'manual'
    ) -> None:
        """
        Add a synchronization point across videos.
        
        Args:
            video_indices: Indices of videos to sync
            frame_numbers: Frame numbers at sync point for each video
            event_type: Type of sync event
        """
        # Calculate timestamp from first video
        timestamp = frame_numbers[0] / self.videos[video_indices[0]].fps
        
        point = AlignmentPoint(
            video_indices=video_indices,
            frame_numbers=frame_numbers,
            timestamp=timestamp,
            event_type=event_type
        )
        
        self.alignment_points.append(point)
        logger.info(f"Added alignment point: {event_type} at frames {frame_numbers}")
    
    def calculate_time_offsets(self) -> bool:
        """
        Calculate time offsets for each video based on alignment points.
        
        Returns:
            True if successful
        """
        if not self.alignment_points:
            logger.warning("No alignment points defined")
            return False
        
        # Use first alignment point as reference
        ref_point = self.alignment_points[0]
        
        for i, video_idx in enumerate(ref_point.video_indices):
            if video_idx < len(self.videos):
                # Calculate time offset to align this video with reference
                frame_time = ref_point.frame_numbers[i] / self.videos[video_idx].fps
                self.time_offsets[video_idx] = ref_point.timestamp - frame_time
        
        logger.info(f"Calculated time offsets: {self.time_offsets}")
        return True
    
    def get_synchronized_frame_numbers(self, target_time: float) -> List[int]:
        """
        Get frame numbers for all videos at a given synchronized time.
        
        Args:
            target_time: Target time in seconds (synchronized timeline)
            
        Returns:
            List of frame numbers, one per video
        """
        frame_numbers = []
        
        for i, video in enumerate(self.videos):
            # Adjust time by offset
            video_time = target_time - self.time_offsets[i]
            
            # Convert to frame number
            frame_num = int(video_time * video.fps)
            
            # Clamp to valid range
            frame_num = max(0, min(frame_num, video.frame_count - 1))
            
            frame_numbers.append(frame_num)
        
        return frame_numbers
    
    def detect_flash_sync(
        self,
        threshold: int = 200,
        min_flash_duration: float = 0.05,
        max_flash_duration: float = 0.5
    ) -> bool:
        """
        Automatically detect flash synchronization points.
        
        Args:
            threshold: Brightness threshold for flash detection
            min_flash_duration: Minimum flash duration in seconds
            max_flash_duration: Maximum flash duration in seconds
            
        Returns:
            True if flash points detected successfully
        """
        flash_frames = []
        
        for video in self.videos:
            cap = cv2.VideoCapture(video.path)
            
            # Search first 10 seconds for flash
            max_frames = int(10 * video.fps)
            flash_frame = None
            
            for frame_num in range(max_frames):
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Convert to grayscale and check brightness
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                mean_brightness = np.mean(gray)
                
                if mean_brightness > threshold:
                    # Check if flash duration is valid
                    flash_start = frame_num
                    flash_end = frame_num
                    
                    # Count consecutive bright frames
                    while flash_end < max_frames:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        if np.mean(gray) <= threshold:
                            break
                        flash_end += 1
                    
                    flash_duration = (flash_end - flash_start) / video.fps
                    
                    if min_flash_duration <= flash_duration <= max_flash_duration:
                        flash_frame = flash_start
                        break
            
            cap.release()
            
            if flash_frame is not None:
                flash_frames.append(flash_frame)
            else:
                logger.warning(f"No flash detected in {video.path}")
                return False
        
        if len(flash_frames) == len(self.videos):
            # Add alignment point
            self.add_alignment_point(
                video_indices=list(range(len(self.videos))),
                frame_numbers=flash_frames,
                event_type='flash'
            )
            return True
        
        return False
    
    def detect_audio_sync(
        self,
        min_amplitude: float = 0.5,
        search_duration: float = 10.0
    ) -> bool:
        """
        Automatically detect audio synchronization points (e.g., clap, beep).
        
        Args:
            min_amplitude: Minimum audio amplitude to detect
            search_duration: Duration to search in seconds
            
        Returns:
            True if audio sync points detected successfully
        """
        try:
            import librosa
            
            audio_peaks = []
            
            for video in self.videos:
                try:
                    # Load audio from video
                    y, sr = librosa.load(video.path, duration=search_duration)
                    
                    # Find peaks in audio signal
                    onset_frames = librosa.onset.onset_detect(
                        y=y,
                        sr=sr,
                        units='frames'
                    )
                    
                    if len(onset_frames) > 0:
                        # Convert to video frame number
                        audio_time = librosa.frames_to_time(onset_frames[0], sr=sr)
                        video_frame = int(audio_time * video.fps)
                        audio_peaks.append(video_frame)
                    else:
                        logger.warning(f"No audio peak detected in {video.path}")
                        return False
                        
                except Exception as e:
                    logger.error(f"Error analyzing audio for {video.path}: {e}")
                    return False
            
            if len(audio_peaks) == len(self.videos):
                self.add_alignment_point(
                    video_indices=list(range(len(self.videos))),
                    frame_numbers=audio_peaks,
                    event_type='audio_peak'
                )
                return True
            
            return False
            
        except ImportError:
            logger.warning("librosa not installed. Audio sync not available.")
            return False
    
    def detect_motion_sync(
        self,
        threshold: float = 50.0,
        search_duration: float = 10.0
    ) -> bool:
        """
        Detect synchronization based on motion events.
        
        Args:
            threshold: Motion detection threshold
            search_duration: Duration to search in seconds
            
        Returns:
            True if motion sync points detected successfully
        """
        motion_frames = []
        
        for video in self.videos:
            cap = cv2.VideoCapture(video.path)
            
            max_frames = int(search_duration * video.fps)
            motion_frame = None
            
            # Read first frame
            ret, prev_frame = cap.read()
            if not ret:
                cap.release()
                continue
            
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            
            for frame_num in range(1, max_frames):
                ret, frame = cap.read()
                if not ret:
                    break
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Calculate frame difference
                diff = cv2.absdiff(gray, prev_gray)
                motion_magnitude = np.mean(diff)
                
                if motion_magnitude > threshold:
                    motion_frame = frame_num
                    break
                
                prev_gray = gray
            
            cap.release()
            
            if motion_frame is not None:
                motion_frames.append(motion_frame)
            else:
                logger.warning(f"No motion detected in {video.path}")
                return False
        
        if len(motion_frames) == len(self.videos):
            self.add_alignment_point(
                video_indices=list(range(len(self.videos))),
                frame_numbers=motion_frames,
                event_type='motion'
            )
            return True
        
        return False
    
    def auto_align(self, method: str = 'flash') -> bool:
        """
        Automatically align videos using specified method.
        
        Args:
            method: Alignment method ('flash', 'audio', 'motion')
            
        Returns:
            True if alignment successful
        """
        self.sync_method = method
        
        if method == 'flash':
            success = self.detect_flash_sync()
        elif method == 'audio':
            success = self.detect_audio_sync()
        elif method == 'motion':
            success = self.detect_motion_sync()
        else:
            logger.error(f"Unknown alignment method: {method}")
            return False
        
        if success:
            return self.calculate_time_offsets()
        
        return False
    
    def export_aligned_videos(
        self,
        output_dir: str,
        start_time: float = 0.0,
        end_time: Optional[float] = None,
        layout: str = 'grid'  # 'grid', 'horizontal', 'vertical'
    ) -> Optional[str]:
        """
        Export aligned videos as a single composite video.
        
        Args:
            output_dir: Output directory
            start_time: Start time in synchronized timeline
            end_time: End time in synchronized timeline (None = end of shortest)
            layout: Layout arrangement
            
        Returns:
            Path to output video or None if failed
        """
        if not self.videos:
            logger.error("No videos loaded")
            return None
        
        # Determine output dimensions
        if layout == 'grid':
            cols = int(np.ceil(np.sqrt(len(self.videos))))
            rows = int(np.ceil(len(self.videos) / cols))
            
            max_width = max(v.width for v in self.videos)
            max_height = max(v.height for v in self.videos)
            
            output_width = cols * max_width
            output_height = rows * max_height
            
        elif layout == 'horizontal':
            max_height = max(v.height for v in self.videos)
            output_width = sum(v.width for v in self.videos)
            output_height = max_height
            
        elif layout == 'vertical':
            max_width = max(v.width for v in self.videos)
            output_width = max_width
            output_height = sum(v.height for v in self.videos)
        
        else:
            logger.error(f"Unknown layout: {layout}")
            return None
        
        # Determine duration
        if end_time is None:
            # Use shortest video
            min_duration = min(
                v.duration + offset 
                for v, offset in zip(self.videos, self.time_offsets)
            )
            end_time = min_duration
        
        duration = end_time - start_time
        
        # Create output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            output_dir,
            f"aligned_videos_{timestamp}.mp4"
        )
        
        # Open all video captures
        caps = [cv2.VideoCapture(v.path) for v in self.videos]
        
        # Set up output video writer
        fps = self.videos[0].fps
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (output_width, output_height))
        
        try:
            current_time = start_time
            
            while current_time < end_time:
                # Get synchronized frame numbers
                frame_numbers = self.get_synchronized_frame_numbers(current_time)
                
                # Read frames
                frames = []
                for i, (cap, frame_num) in enumerate(zip(caps, frame_numbers)):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                    ret, frame = cap.read()
                    
                    if ret:
                        # Resize if needed
                        if layout == 'grid':
                            frame = cv2.resize(frame, (max_width, max_height))
                        elif layout == 'horizontal':
                            frame = cv2.resize(frame, (self.videos[i].width, max_height))
                        elif layout == 'vertical':
                            frame = cv2.resize(frame, (max_width, self.videos[i].height))
                        
                        frames.append(frame)
                    else:
                        # Use black frame if read failed
                        if layout == 'grid':
                            frames.append(np.zeros((max_height, max_width, 3), dtype=np.uint8))
                        elif layout == 'horizontal':
                            frames.append(np.zeros((max_height, self.videos[i].width, 3), dtype=np.uint8))
                        elif layout == 'vertical':
                            frames.append(np.zeros((self.videos[i].height, max_width, 3), dtype=np.uint8))
                
                # Compose frame
                if layout == 'grid':
                    composite = np.zeros((output_height, output_width, 3), dtype=np.uint8)
                    for i, frame in enumerate(frames):
                        row = i // cols
                        col = i % cols
                        y = row * max_height
                        x = col * max_width
                        composite[y:y+max_height, x:x+max_width] = frame
                        
                elif layout == 'horizontal':
                    composite = np.hstack(frames)
                    
                elif layout == 'vertical':
                    composite = np.vstack(frames)
                
                out.write(composite)
                
                current_time += 1.0 / fps
            
            logger.info(f"Exported aligned video to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting aligned videos: {e}")
            return None
            
        finally:
            # Clean up
            for cap in caps:
                cap.release()
            out.release()
    
    def save_alignment(self, output_path: str) -> bool:
        """
        Save alignment configuration to JSON file.
        
        Args:
            output_path: Path to output JSON file
            
        Returns:
            True if successful
        """
        try:
            data = {
                'videos': [
                    {
                        'path': v.path,
                        'fps': v.fps,
                        'frame_count': v.frame_count,
                        'duration': v.duration
                    }
                    for v in self.videos
                ],
                'time_offsets': self.time_offsets,
                'alignment_points': [
                    {
                        'video_indices': p.video_indices,
                        'frame_numbers': p.frame_numbers,
                        'timestamp': p.timestamp,
                        'event_type': p.event_type,
                        'confidence': p.confidence
                    }
                    for p in self.alignment_points
                ],
                'sync_method': self.sync_method
            }
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved alignment to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving alignment: {e}")
            return False
    
    def load_alignment(self, input_path: str) -> bool:
        """
        Load alignment configuration from JSON file.
        
        Args:
            input_path: Path to input JSON file
            
        Returns:
            True if successful
        """
        try:
            with open(input_path, 'r') as f:
                data = json.load(f)
            
            # Load videos
            video_paths = [v['path'] for v in data['videos']]
            if not self.load_videos(video_paths):
                return False
            
            # Load time offsets
            self.time_offsets = data['time_offsets']
            
            # Load alignment points
            self.alignment_points = [
                AlignmentPoint(
                    video_indices=p['video_indices'],
                    frame_numbers=p['frame_numbers'],
                    timestamp=p['timestamp'],
                    event_type=p['event_type'],
                    confidence=p.get('confidence', 1.0)
                )
                for p in data['alignment_points']
            ]
            
            self.sync_method = data.get('sync_method', 'manual')
            
            logger.info(f"Loaded alignment from {input_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading alignment: {e}")
            return False


def calculate_video_similarity(
    video1_path: str,
    video2_path: str,
    num_samples: int = 100
) -> float:
    """
    Calculate similarity between two videos for verification.
    
    Args:
        video1_path: Path to first video
        video2_path: Path to second video
        num_samples: Number of frames to sample
        
    Returns:
        Similarity score (0-1)
    """
    cap1 = cv2.VideoCapture(video1_path)
    cap2 = cv2.VideoCapture(video2_path)
    
    if not cap1.isOpened() or not cap2.isOpened():
        cap1.release()
        cap2.release()
        return 0.0
    
    frame_count1 = int(cap1.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_count2 = int(cap2.get(cv2.CAP_PROP_FRAME_COUNT))
    
    min_frames = min(frame_count1, frame_count2)
    
    # Sample frames evenly
    sample_indices = np.linspace(0, min_frames - 1, num_samples, dtype=int)
    
    similarities = []
    
    for idx in sample_indices:
        cap1.set(cv2.CAP_PROP_POS_FRAMES, idx)
        cap2.set(cv2.CAP_PROP_POS_FRAMES, idx)
        
        ret1, frame1 = cap1.read()
        ret2, frame2 = cap2.read()
        
        if ret1 and ret2:
            # Resize to same size
            size = (640, 480)
            frame1 = cv2.resize(frame1, size)
            frame2 = cv2.resize(frame2, size)
            
            # Convert to grayscale
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            
            # Calculate structural similarity
            similarity = np.corrcoef(gray1.flatten(), gray2.flatten())[0, 1]
            similarities.append(similarity)
    
    cap1.release()
    cap2.release()
    
    return np.mean(similarities) if similarities else 0.0
