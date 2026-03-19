"""
Stimulus Video Generator Module

This module provides functions to generate eye tracking stimulus videos with various
motion patterns and tasks including fixation, smooth pursuit, and saccades.

Author: Kahlil Gibran Al Zulmi
Institution: Institut Teknologi Sepuluh Nopember
Date: November 2025
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import time
from typing import Tuple, List, Dict, Any, Optional
from datetime import datetime

from utils.logger import log_info, log_error, log_warning
from utils.localization import get_text


# ============================================================================
# PROTOCOL DEFINITIONS
# ============================================================================

def get_default_protocols() -> Dict[str, Dict[str, Any]]:
    """
    Get predefined stimulus protocols.
    
    Returns:
        Dictionary of protocol configurations
    """
    return {
        "standard": {
            "name": get_text("stimulus.protocols.standard"),
            "description": "Standard clinical protocol with all tasks",
            "tasks": [
                {"type": "opening", "duration": 5},
                {"type": "tutorial", "duration": 8},
                {"type": "fixation", "duration": 5, "position": "center"},
                {"type": "smooth_horizontal_lr", "duration": 10},
                {"type": "smooth_horizontal_rl", "duration": 10},
                {"type": "smooth_vertical_tb", "duration": 10},
                {"type": "smooth_vertical_bt", "duration": 10},
                {"type": "smooth_circular_cw", "duration": 10},
                {"type": "smooth_circular_ccw", "duration": 10},
                {"type": "saccade_structured", "duration": 3, "points": 5},
                {"type": "saccade_random", "duration": 3, "points": 5},
                {"type": "closing", "duration": 5}
            ],
            "settings": {
                "width": 1920,
                "height": 1080,
                "fps": 60,
                "background_color": (0, 0, 0),
                "target_color": (255, 255, 255),
                "text_color": (255, 255, 255),
                "margin": 150,
                "command_duration": 3,
                "prepare_duration": 3
            }
        },
        "quick": {
            "name": get_text("stimulus.protocols.quick"),
            "description": "Quick test protocol (5 minutes)",
            "tasks": [
                {"type": "opening", "duration": 3},
                {"type": "fixation", "duration": 3, "position": "center"},
                {"type": "smooth_horizontal_lr", "duration": 5},
                {"type": "smooth_vertical_tb", "duration": 5},
                {"type": "smooth_circular_cw", "duration": 5},
                {"type": "saccade_structured", "duration": 2, "points": 5},
                {"type": "closing", "duration": 3}
            ],
            "settings": {
                "width": 1920,
                "height": 1080,
                "fps": 60,
                "background_color": (0, 0, 0),
                "target_color": (255, 255, 255),
                "text_color": (255, 255, 255),
                "margin": 150,
                "command_duration": 2,
                "prepare_duration": 2
            }
        },
        "extended": {
            "name": get_text("stimulus.protocols.extended"),
            "description": "Extended research protocol (20+ minutes)",
            "tasks": [
                {"type": "opening", "duration": 5},
                {"type": "tutorial", "duration": 10},
                {"type": "fixation", "duration": 8, "position": "center"},
                {"type": "fixation", "duration": 5, "position": "top_left"},
                {"type": "fixation", "duration": 5, "position": "top_right"},
                {"type": "fixation", "duration": 5, "position": "bottom_left"},
                {"type": "fixation", "duration": 5, "position": "bottom_right"},
                {"type": "smooth_horizontal_lr", "duration": 15},
                {"type": "smooth_horizontal_rl", "duration": 15},
                {"type": "smooth_vertical_tb", "duration": 15},
                {"type": "smooth_vertical_bt", "duration": 15},
                {"type": "smooth_circular_cw", "duration": 15},
                {"type": "smooth_circular_ccw", "duration": 15},
                {"type": "smooth_diagonal_tlbr", "duration": 12},
                {"type": "smooth_diagonal_brtl", "duration": 12},
                {"type": "saccade_structured", "duration": 4, "points": 9},
                {"type": "saccade_random", "duration": 4, "points": 9},
                {"type": "closing", "duration": 5}
            ],
            "settings": {
                "width": 1920,
                "height": 1080,
                "fps": 60,
                "background_color": (0, 0, 0),
                "target_color": (255, 255, 255),
                "text_color": (255, 255, 255),
                "margin": 150,
                "command_duration": 3,
                "prepare_duration": 3
            }
        }
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def bgr_to_rgb(bgr_tuple: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """Convert BGR color to RGB."""
    return (bgr_tuple[2], bgr_tuple[1], bgr_tuple[0])


def draw_text_pil(
    frame_bgr: np.ndarray,
    text: str,
    position: Tuple[int, int],
    font: ImageFont.FreeTypeFont,
    color_bgr: Tuple[int, int, int]
) -> np.ndarray:
    """
    Draw text on frame using PIL for better font rendering.
    
    Args:
        frame_bgr: Input frame in BGR format
        text: Text to draw
        position: (x, y) position
        font: PIL ImageFont object
        color_bgr: Text color in BGR format
        
    Returns:
        Frame with text drawn
    """
    pil_img = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    draw.text(position, text, font=font, fill=bgr_to_rgb(color_bgr))
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def draw_overlay_info(
    frame: np.ndarray,
    width: int,
    height: int,
    instruction_text: str,
    timer_text: str,
    fonts: Dict[str, ImageFont.FreeTypeFont],
    text_color: Tuple[int, int, int],
    overlay_bg_color: Tuple[int, int, int],
    overlay_alpha: float = 0.5
) -> np.ndarray:
    """
    Draw instruction and timer overlay on frame.
    
    Args:
        frame: Input frame
        width, height: Frame dimensions
        instruction_text: Instruction text to display
        timer_text: Timer text to display
        fonts: Dictionary of fonts
        text_color: Text color
        overlay_bg_color: Overlay background color
        overlay_alpha: Overlay transparency
        
    Returns:
        Frame with overlay
    """
    overlay = frame.copy()
    
    # Command box (top right)
    cmd_box = (width - 450, 30, width - 30, 180)
    cv2.rectangle(overlay, (cmd_box[0], cmd_box[1]), (cmd_box[2], cmd_box[3]), overlay_bg_color, -1)
    
    # Timer box (bottom right)
    timer_box = (width - 450, height - 120, width - 30, height - 30)
    cv2.rectangle(overlay, (timer_box[0], timer_box[1]), (timer_box[2], timer_box[3]), overlay_bg_color, -1)
    
    # Blend overlay
    cv2.addWeighted(overlay, overlay_alpha, frame, 1 - overlay_alpha, 0, frame)
    
    # Draw titles
    frame = draw_text_pil(frame, get_text("stimulus.instruction_label"), 
                          (cmd_box[0] + 15, cmd_box[1] + 10), 
                          fonts['title'], text_color)
    frame = draw_text_pil(frame, get_text("stimulus.timer_label"), 
                          (timer_box[0] + 15, timer_box[1] + 10), 
                          fonts['title'], text_color)
    
    # Draw instruction text (multiple lines)
    y_text = cmd_box[1] + 45
    for line in instruction_text.split('\n'):
        frame = draw_text_pil(frame, line, (cmd_box[0] + 15, y_text), 
                              fonts['content'], text_color)
        y_text += 35
    
    # Draw timer
    if timer_text:
        frame = draw_text_pil(frame, timer_text, (timer_box[0] + 15, timer_box[1] + 45), 
                              fonts['content'], text_color)
    
    return frame


def draw_target_and_coords(
    frame: np.ndarray,
    center_xy: Tuple[float, float],
    target_color: Tuple[int, int, int],
    crosshair_color: Tuple[int, int, int],
    background_color: Tuple[int, int, int],
    width: int,
    height: int,
    font: ImageFont.FreeTypeFont,
    text_color: Tuple[int, int, int],
    show_crosshair: bool = True
) -> np.ndarray:
    """
    Draw target circle and coordinate crosshair.
    
    Args:
        frame: Input frame
        center_xy: Target center position
        target_color: Color of target circle
        crosshair_color: Color of crosshair lines
        background_color: Background color for center dot
        width, height: Frame dimensions
        font: Font for coordinates
        text_color: Text color for coordinates
        show_crosshair: Whether to show crosshair lines
        
    Returns:
        Frame with target drawn
    """
    cx, cy = int(center_xy[0]), int(center_xy[1])
    
    # Draw crosshair lines
    if show_crosshair:
        cv2.line(frame, (0, cy), (width, cy), crosshair_color, 1)
        cv2.line(frame, (cx, 0), (cx, height), crosshair_color, 1)
    
    # Draw target circle
    cv2.circle(frame, (cx, cy), 20, target_color, -1)
    cv2.circle(frame, (cx, cy), 5, background_color, -1)
    
    # Draw coordinates
    coord_text = f"X: {cx}\nY: {cy}"
    frame = draw_text_pil(frame, coord_text, (30, 30), font, text_color)
    
    return frame


def draw_pie_countdown(
    frame: np.ndarray,
    center_xy: Tuple[float, float],
    progress_ratio: float,
    countdown_color: Tuple[int, int, int],
    radius: int = 30
) -> np.ndarray:
    """
    Draw pie-chart countdown visualization around target.
    
    Args:
        frame: Input frame
        center_xy: Center position
        progress_ratio: Progress from 0 to 1
        countdown_color: Color of countdown pie
        radius: Countdown circle radius
        
    Returns:
        Frame with countdown drawn
    """
    cx, cy = int(center_xy[0]), int(center_xy[1])
    start_angle = -90
    end_angle = start_angle + (360 * progress_ratio)
    cv2.ellipse(frame, (cx, cy), (radius, radius), 0, start_angle, end_angle, countdown_color, -1)
    return frame


# ============================================================================
# FRAME GENERATION FUNCTIONS
# ============================================================================

def generate_fullscreen_text_frames(
    text: str,
    duration: float,
    width: int,
    height: int,
    fps: int,
    background_color: Tuple[int, int, int],
    text_color: Tuple[int, int, int],
    font: ImageFont.FreeTypeFont
) -> List[np.ndarray]:
    """
    Generate frames with fullscreen centered text.
    
    Args:
        text: Text to display (supports multiple lines with \\n)
        duration: Duration in seconds
        width, height: Frame dimensions
        fps: Frames per second
        background_color: Background color
        text_color: Text color
        font: Font for text
        
    Returns:
        List of generated frames
    """
    frames = []
    total_frames = int(duration * fps)
    
    for _ in range(total_frames):
        frame = np.full((height, width, 3), background_color, dtype=np.uint8)
        
        lines = text.split('\n')
        # Calculate total height of all lines
        total_text_height = sum([font.getbbox(line)[3] for line in lines]) + (len(lines) - 1) * 10
        start_y = (height - total_text_height) // 2
        current_y = start_y
        
        for line in lines:
            bbox = font.getbbox(line)
            text_width = bbox[2] - bbox[0]
            pos_x = (width - text_width) // 2
            frame = draw_text_pil(frame, line, (pos_x, current_y), font, text_color)
            current_y += bbox[3] + 10
        
        frames.append(frame)
    
    return frames


def generate_command_frames(
    instruction: str,
    duration: float,
    width: int,
    height: int,
    fps: int,
    background_color: Tuple[int, int, int],
    fonts: Dict[str, ImageFont.FreeTypeFont],
    text_color: Tuple[int, int, int],
    overlay_bg_color: Tuple[int, int, int]
) -> List[np.ndarray]:
    """
    Generate command instruction frames before a task.
    
    Args:
        instruction: Instruction text
        duration: Duration in seconds
        width, height: Frame dimensions
        fps: Frames per second
        background_color: Background color
        fonts: Dictionary of fonts
        text_color: Text color
        overlay_bg_color: Overlay background color
        
    Returns:
        List of generated frames
    """
    frames = []
    total_frames = int(duration * fps)
    
    for _ in range(total_frames):
        frame = np.full((height, width, 3), background_color, dtype=np.uint8)
        frame = draw_overlay_info(frame, width, height, instruction, "---", 
                                   fonts, text_color, overlay_bg_color)
        frames.append(frame)
    
    return frames


def generate_static_target_frames(
    position: Tuple[float, float],
    duration: float,
    instruction_text: str,
    width: int,
    height: int,
    fps: int,
    background_color: Tuple[int, int, int],
    target_color: Tuple[int, int, int],
    crosshair_color: Tuple[int, int, int],
    fonts: Dict[str, ImageFont.FreeTypeFont],
    text_color: Tuple[int, int, int],
    overlay_bg_color: Tuple[int, int, int],
    show_crosshair: bool = True
) -> List[np.ndarray]:
    """
    Generate frames with static fixation target.
    
    Args:
        position: Target position (x, y)
        duration: Duration in seconds
        instruction_text: Instruction to display
        width, height: Frame dimensions
        fps: Frames per second
        background_color, target_color, crosshair_color: Colors
        fonts: Dictionary of fonts
        text_color: Text color
        overlay_bg_color: Overlay background color
        show_crosshair: Whether to show crosshair
        
    Returns:
        List of generated frames
    """
    frames = []
    total_frames = int(duration * fps)
    
    for i in range(total_frames):
        frame = np.full((height, width, 3), background_color, dtype=np.uint8)
        
        # Calculate remaining time
        sisa_waktu = duration - (i / fps)
        timer_text = f"{sisa_waktu:.1f} s"
        
        # Draw target and overlay
        frame = draw_target_and_coords(frame, position, target_color, crosshair_color, 
                                        background_color, width, height, fonts['coords'], 
                                        text_color, show_crosshair)
        frame = draw_overlay_info(frame, width, height, instruction_text, timer_text,
                                   fonts, text_color, overlay_bg_color)
        
        frames.append(frame)
    
    return frames


def generate_smooth_pursuit_frames(
    path_x: np.ndarray,
    path_y: np.ndarray,
    duration: float,
    prepare_duration: float,
    instruction_text: str,
    width: int,
    height: int,
    fps: int,
    background_color: Tuple[int, int, int],
    target_color: Tuple[int, int, int],
    crosshair_color: Tuple[int, int, int],
    countdown_color: Tuple[int, int, int],
    fonts: Dict[str, ImageFont.FreeTypeFont],
    text_color: Tuple[int, int, int],
    overlay_bg_color: Tuple[int, int, int]
) -> List[np.ndarray]:
    """
    Generate frames with smooth pursuit target movement.
    
    Args:
        path_x, path_y: Arrays of x and y coordinates for motion path
        duration: Duration of movement in seconds
        prepare_duration: Preparation countdown duration
        instruction_text: Instruction to display
        width, height: Frame dimensions
        fps: Frames per second
        background_color, target_color, crosshair_color, countdown_color: Colors
        fonts: Dictionary of fonts
        text_color: Text color
        overlay_bg_color: Overlay background color
        
    Returns:
        List of generated frames
    """
    frames = []
    
    # Preparation phase with countdown
    start_pos = (path_x[0], path_y[0])
    total_prepare_frames = int(prepare_duration * fps)
    
    for i in range(total_prepare_frames):
        frame = np.full((height, width, 3), background_color, dtype=np.uint8)
        frame = draw_target_and_coords(frame, start_pos, target_color, crosshair_color,
                                        background_color, width, height, fonts['coords'],
                                        text_color, True)
        
        # Draw countdown pie
        progress_ratio = 1 - (i / total_prepare_frames)
        frame = draw_pie_countdown(frame, start_pos, progress_ratio, countdown_color)
        
        frame = draw_overlay_info(frame, width, height, instruction_text, 
                                   get_text("stimulus.preparing"),
                                   fonts, text_color, overlay_bg_color)
        frames.append(frame)
    
    # Movement phase
    total_move_frames = len(path_x)
    
    for i in range(total_move_frames):
        frame = np.full((height, width, 3), background_color, dtype=np.uint8)
        
        # Calculate remaining time
        sisa_waktu = duration - (i / fps)
        timer_text = f"{sisa_waktu:.1f} s"
        
        # Current position
        current_pos = (path_x[i], path_y[i])
        
        frame = draw_target_and_coords(frame, current_pos, target_color, crosshair_color,
                                        background_color, width, height, fonts['coords'],
                                        text_color, True)
        frame = draw_overlay_info(frame, width, height, instruction_text, timer_text,
                                   fonts, text_color, overlay_bg_color)
        
        frames.append(frame)
    
    return frames


def generate_saccade_frames(
    points: List[Tuple[float, float]],
    duration_per_point: float,
    instruction_text: str,
    width: int,
    height: int,
    fps: int,
    background_color: Tuple[int, int, int],
    target_color: Tuple[int, int, int],
    crosshair_color: Tuple[int, int, int],
    fonts: Dict[str, ImageFont.FreeTypeFont],
    text_color: Tuple[int, int, int],
    overlay_bg_color: Tuple[int, int, int]
) -> List[np.ndarray]:
    """
    Generate frames with saccadic target jumps.
    
    Args:
        points: List of target positions
        duration_per_point: Duration at each point in seconds
        instruction_text: Instruction to display
        width, height: Frame dimensions
        fps: Frames per second
        background_color, target_color, crosshair_color: Colors
        fonts: Dictionary of fonts
        text_color: Text color
        overlay_bg_color: Overlay background color
        
    Returns:
        List of generated frames
    """
    frames = []
    
    for point in points:
        frames_per_point = int(duration_per_point * fps)
        
        for i in range(frames_per_point):
            frame = np.full((height, width, 3), background_color, dtype=np.uint8)
            
            # Calculate remaining time for this point
            sisa_waktu = duration_per_point - (i / fps)
            timer_text = f"{sisa_waktu:.1f} s"
            
            frame = draw_target_and_coords(frame, point, target_color, crosshair_color,
                                            background_color, width, height, fonts['coords'],
                                            text_color, True)
            frame = draw_overlay_info(frame, width, height, instruction_text, timer_text,
                                       fonts, text_color, overlay_bg_color)
            
            frames.append(frame)
    
    return frames


# ============================================================================
# PATH GENERATION FUNCTIONS
# ============================================================================

def generate_horizontal_path(
    width: int,
    height: int,
    margin: int,
    duration: float,
    fps: int,
    left_to_right: bool = True
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate horizontal motion path."""
    total_frames = int(duration * fps)
    path_x = np.linspace(margin, width - margin, total_frames)
    path_y = np.full_like(path_x, height // 2)
    
    if not left_to_right:
        path_x = path_x[::-1]
    
    return path_x, path_y


def generate_vertical_path(
    width: int,
    height: int,
    margin: int,
    duration: float,
    fps: int,
    top_to_bottom: bool = True
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate vertical motion path."""
    total_frames = int(duration * fps)
    path_y = np.linspace(margin, height - margin, total_frames)
    path_x = np.full_like(path_y, width // 2)
    
    if not top_to_bottom:
        path_y = path_y[::-1]
    
    return path_x, path_y


def generate_circular_path(
    width: int,
    height: int,
    margin: int,
    duration: float,
    fps: int,
    clockwise: bool = True
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate circular motion path."""
    total_frames = int(duration * fps)
    center_x, center_y = width // 2, height // 2
    radius = min(width, height) // 2 - margin
    
    # Two full rotations
    t = np.linspace(0, 2 * np.pi * 2, total_frames)
    path_x = center_x + radius * np.cos(t)
    path_y = center_y + radius * np.sin(t)
    
    if not clockwise:
        path_y = center_y - radius * np.sin(t)
    
    return path_x, path_y


def generate_diagonal_path(
    width: int,
    height: int,
    margin: int,
    duration: float,
    fps: int,
    top_left_to_bottom_right: bool = True
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate diagonal motion path."""
    total_frames = int(duration * fps)
    
    if top_left_to_bottom_right:
        path_x = np.linspace(margin, width - margin, total_frames)
        path_y = np.linspace(margin, height - margin, total_frames)
    else:
        path_x = np.linspace(width - margin, margin, total_frames)
        path_y = np.linspace(height - margin, margin, total_frames)
    
    return path_x, path_y


def generate_saccade_points(
    width: int,
    height: int,
    margin: int,
    num_points: int,
    structured: bool = True
) -> List[Tuple[float, float]]:
    """
    Generate saccade target points.
    
    Args:
        width, height: Screen dimensions
        margin: Margin from edges
        num_points: Number of points
        structured: If True, use grid pattern; if False, use random
        
    Returns:
        List of (x, y) positions
    """
    if structured:
        # Structured grid pattern
        if num_points == 5:
            return [
                (margin, margin),
                (width - margin, margin),
                (width - margin, height - margin),
                (margin, height - margin),
                (width // 2, height // 2)
            ]
        elif num_points == 9:
            return [
                (margin, margin),
                (width // 2, margin),
                (width - margin, margin),
                (width - margin, height // 2),
                (width - margin, height - margin),
                (width // 2, height - margin),
                (margin, height - margin),
                (margin, height // 2),
                (width // 2, height // 2)
            ]
    else:
        # Random positions
        np.random.seed(42)  # For reproducibility
        points = []
        for _ in range(num_points - 1):
            x = np.random.randint(margin, width - margin)
            y = np.random.randint(margin, height - margin)
            points.append((x, y))
        # Always end at center
        points.append((width // 2, height // 2))
        return points
    
    # Default: return center point
    return [(width // 2, height // 2)]


def get_fixed_position(
    position_name: str,
    width: int,
    height: int,
    margin: int
) -> Tuple[float, float]:
    """
    Get fixed position coordinates.
    
    Args:
        position_name: Name of position (center, top_left, etc.)
        width, height: Screen dimensions
        margin: Margin from edges
        
    Returns:
        (x, y) coordinates
    """
    positions = {
        "center": (width // 2, height // 2),
        "top_left": (margin, margin),
        "top_right": (width - margin, margin),
        "bottom_left": (margin, height - margin),
        "bottom_right": (width - margin, height - margin),
        "top_center": (width // 2, margin),
        "bottom_center": (width // 2, height - margin),
        "left_center": (margin, height // 2),
        "right_center": (width - margin, height // 2)
    }
    
    return positions.get(position_name, (width // 2, height // 2))


# ============================================================================
# MAIN GENERATION FUNCTION
# ============================================================================

def generate_stimulus_video(
    protocol: Dict[str, Any],
    output_path: str,
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Generate stimulus video based on protocol configuration.
    
    Args:
        protocol: Protocol configuration dictionary
        output_path: Path to save output video
        progress_callback: Optional callback function(current, total, message)
        
    Returns:
        Dictionary with generation results
    """
    try:
        start_time = time.time()
        
        # Extract settings
        settings = protocol.get('settings', {})
        width = settings.get('width', 1920)
        height = settings.get('height', 1080)
        fps = settings.get('fps', 60)
        background_color = tuple(settings.get('background_color', [0, 0, 0]))
        target_color = tuple(settings.get('target_color', [255, 255, 255]))
        text_color = tuple(settings.get('text_color', [255, 255, 255]))
        crosshair_color = tuple(settings.get('crosshair_color', [0, 0, 0]))
        countdown_color = tuple(settings.get('countdown_color', [255, 255, 255]))
        overlay_bg_color = tuple(settings.get('overlay_bg_color', [0, 0, 0]))
        margin = settings.get('margin', 150)
        command_duration = settings.get('command_duration', 3)
        prepare_duration = settings.get('prepare_duration', 3)
        
        # Load fonts
        font_path = settings.get('font_path', 'arial.ttf')
        try:
            fonts = {
                'title': ImageFont.truetype(font_path, 28),
                'content': ImageFont.truetype(font_path, 32),
                'coords': ImageFont.truetype(font_path, 22),
                'fullscreen': ImageFont.truetype(font_path, 50)
            }
        except IOError:
            log_warning(f"Font file '{font_path}' not found, using default")
            fonts = {
                'title': ImageFont.load_default(),
                'content': ImageFont.load_default(),
                'coords': ImageFont.load_default(),
                'fullscreen': ImageFont.load_default()
            }
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not video.isOpened():
            raise Exception("Failed to create video writer")
        
        log_info(f"Generating stimulus video: {output_path}")
        log_info(f"Resolution: {width}x{height} @ {fps} FPS")
        
        # Get tasks
        tasks = protocol.get('tasks', [])
        total_tasks = len(tasks)
        
        # Generate frames for each task
        for task_idx, task in enumerate(tasks):
            task_type = task.get('type')
            duration = task.get('duration', 5)
            
            if progress_callback:
                progress_callback(task_idx, total_tasks, f"Generating: {task_type}")
            
            log_info(f"Generating task {task_idx + 1}/{total_tasks}: {task_type}")
            
            frames = []
            
            # Opening/Closing screens
            if task_type in ["opening", "closing"]:
                if task_type == "opening":
                    text = get_text("stimulus.opening_text")
                else:
                    text = get_text("stimulus.closing_text")
                
                frames = generate_fullscreen_text_frames(
                    text, duration, width, height, fps,
                    background_color, text_color, fonts['fullscreen']
                )
            
            # Tutorial
            elif task_type == "tutorial":
                # Command frames
                frames.extend(generate_command_frames(
                    get_text("stimulus.tutorial_instruction"),
                    command_duration, width, height, fps,
                    background_color, fonts, text_color, overlay_bg_color
                ))
                
                # Tutorial smooth movement
                path_x, path_y = generate_horizontal_path(width, height, margin, duration, fps, True)
                frames.extend(generate_smooth_pursuit_frames(
                    path_x, path_y, duration, prepare_duration,
                    get_text("stimulus.tutorial_instruction"),
                    width, height, fps, background_color, target_color,
                    crosshair_color, countdown_color, fonts, text_color, overlay_bg_color
                ))
            
            # Fixation
            elif task_type == "fixation":
                position_name = task.get('position', 'center')
                position = get_fixed_position(position_name, width, height, margin)
                
                # Command frames
                frames.extend(generate_command_frames(
                    get_text("stimulus.fixation_instruction"),
                    command_duration, width, height, fps,
                    background_color, fonts, text_color, overlay_bg_color
                ))
                
                # Fixation frames
                frames.extend(generate_static_target_frames(
                    position, duration, get_text("stimulus.fixation_instruction"),
                    width, height, fps, background_color, target_color,
                    crosshair_color, fonts, text_color, overlay_bg_color, True
                ))
            
            # Smooth pursuit horizontal
            elif task_type in ["smooth_horizontal_lr", "smooth_horizontal_rl"]:
                lr = task_type == "smooth_horizontal_lr"
                
                # Command frames
                if lr:
                    instruction = get_text("stimulus.smooth_horizontal_lr")
                else:
                    instruction = get_text("stimulus.smooth_horizontal_rl")
                
                frames.extend(generate_command_frames(
                    instruction, command_duration, width, height, fps,
                    background_color, fonts, text_color, overlay_bg_color
                ))
                
                # Movement frames
                path_x, path_y = generate_horizontal_path(width, height, margin, duration, fps, lr)
                frames.extend(generate_smooth_pursuit_frames(
                    path_x, path_y, duration, prepare_duration, instruction,
                    width, height, fps, background_color, target_color,
                    crosshair_color, countdown_color, fonts, text_color, overlay_bg_color
                ))
            
            # Smooth pursuit vertical
            elif task_type in ["smooth_vertical_tb", "smooth_vertical_bt"]:
                tb = task_type == "smooth_vertical_tb"
                
                # Command frames
                if tb:
                    instruction = get_text("stimulus.smooth_vertical_tb")
                else:
                    instruction = get_text("stimulus.smooth_vertical_bt")
                
                frames.extend(generate_command_frames(
                    instruction, command_duration, width, height, fps,
                    background_color, fonts, text_color, overlay_bg_color
                ))
                
                # Movement frames
                path_x, path_y = generate_vertical_path(width, height, margin, duration, fps, tb)
                frames.extend(generate_smooth_pursuit_frames(
                    path_x, path_y, duration, prepare_duration, instruction,
                    width, height, fps, background_color, target_color,
                    crosshair_color, countdown_color, fonts, text_color, overlay_bg_color
                ))
            
            # Smooth pursuit circular
            elif task_type in ["smooth_circular_cw", "smooth_circular_ccw"]:
                cw = task_type == "smooth_circular_cw"
                
                # Command frames
                if cw:
                    instruction = get_text("stimulus.smooth_circular_cw")
                else:
                    instruction = get_text("stimulus.smooth_circular_ccw")
                
                frames.extend(generate_command_frames(
                    instruction, command_duration, width, height, fps,
                    background_color, fonts, text_color, overlay_bg_color
                ))
                
                # Movement frames
                path_x, path_y = generate_circular_path(width, height, margin, duration, fps, cw)
                frames.extend(generate_smooth_pursuit_frames(
                    path_x, path_y, duration, prepare_duration, instruction,
                    width, height, fps, background_color, target_color,
                    crosshair_color, countdown_color, fonts, text_color, overlay_bg_color
                ))
            
            # Smooth pursuit diagonal
            elif task_type in ["smooth_diagonal_tlbr", "smooth_diagonal_brtl"]:
                tlbr = task_type == "smooth_diagonal_tlbr"
                
                # Command frames
                if tlbr:
                    instruction = get_text("stimulus.smooth_diagonal_tlbr")
                else:
                    instruction = get_text("stimulus.smooth_diagonal_brtl")
                
                frames.extend(generate_command_frames(
                    instruction, command_duration, width, height, fps,
                    background_color, fonts, text_color, overlay_bg_color
                ))
                
                # Movement frames
                path_x, path_y = generate_diagonal_path(width, height, margin, duration, fps, tlbr)
                frames.extend(generate_smooth_pursuit_frames(
                    path_x, path_y, duration, prepare_duration, instruction,
                    width, height, fps, background_color, target_color,
                    crosshair_color, countdown_color, fonts, text_color, overlay_bg_color
                ))
            
            # Saccades
            elif task_type in ["saccade_structured", "saccade_random"]:
                structured = task_type == "saccade_structured"
                num_points = task.get('points', 5)
                duration_per_point = duration
                
                # Command frames
                if structured:
                    instruction = get_text("stimulus.saccade_structured")
                else:
                    instruction = get_text("stimulus.saccade_random")
                
                frames.extend(generate_command_frames(
                    instruction, command_duration, width, height, fps,
                    background_color, fonts, text_color, overlay_bg_color
                ))
                
                # Saccade frames
                points = generate_saccade_points(width, height, margin, num_points, structured)
                frames.extend(generate_saccade_frames(
                    points, duration_per_point, instruction,
                    width, height, fps, background_color, target_color,
                    crosshair_color, fonts, text_color, overlay_bg_color
                ))
            
            # Write frames to video
            for frame in frames:
                video.write(frame)
        
        # Cleanup
        video.release()
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        # Get video info
        cap = cv2.VideoCapture(output_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_duration = frame_count / fps
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        cap.release()
        
        log_info(f"Video generation complete: {output_path}")
        log_info(f"Duration: {video_duration:.2f}s, Size: {file_size:.2f}MB, Generation time: {generation_time:.2f}s")
        
        if progress_callback:
            progress_callback(total_tasks, total_tasks, "Complete!")
        
        return {
            'success': True,
            'output_path': output_path,
            'duration': video_duration,
            'frame_count': frame_count,
            'file_size_mb': file_size,
            'generation_time': generation_time,
            'resolution': (width, height),
            'fps': fps
        }
        
    except Exception as e:
        log_error(f"Error generating stimulus video: {str(e)}")
        if 'video' in locals():
            video.release()
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    # Test code
    protocols = get_default_protocols()
    print("Available protocols:")
    for key, protocol in protocols.items():
        print(f"  - {key}: {protocol['name']}")
