# Eye Tracker - API Documentation

**Version 1.0.0**  
Medical Technology Study Program - Institut Teknologi Sepuluh Nopember

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Core Modules](#core-modules)
4. [Detection Module](#detection-module)
5. [Game Module](#game-module)
6. [Stimulus Module](#stimulus-module)
7. [Database Module](#database-module)
8. [Visualization Module](#visualization-module)
9. [Report Generation](#report-generation)
10. [Utilities](#utilities)
11. [Configuration](#configuration)
12. [Localization](#localization)

---

## Overview

The Eye Tracker application is a comprehensive research software built with Python for eye tracking research in medical technology applications. It provides tools for pupil detection, cognitive assessment, stimulus generation, data management, and analysis.

### Key Technologies

- **Python 3.10+**: Core language
- **OpenCV**: Computer vision and image processing
- **Tkinter**: GUI framework
- **Pygame**: Game engine
- **Matplotlib/Seaborn**: Visualization
- **Pandas**: Data analysis
- **SQLite**: Database storage
- **Openpyxl**: Excel report generation

### Design Principles

- **Modular**: Each feature is independent and can be used standalone
- **Extensible**: Easy to add new detection methods or protocols
- **Bilingual**: Full support for English and Indonesian
- **User-friendly**: Wizard-based interfaces for all complex tasks
- **Data-driven**: All sessions stored in databases for later analysis

---

## Architecture

```
eye_tracker/
├── eye_tracker.py          # Main application entry point
├── modules/                # Feature modules
│   ├── detection_wizard.py
│   ├── detect_gemini8.py
│   ├── game_wizard.py
│   ├── game_engine.py
│   ├── stimulus_wizard.py
│   ├── stimulus_generator.py
│   ├── database_viewer.py
│   ├── database_manager.py
│   ├── visualization.py
│   ├── report_generator.py
│   ├── obs_wizard.py
│   ├── settings_dialog.py
│   └── system_check.py
├── utils/                  # Utility modules
│   ├── config_manager.py
│   ├── localization.py
│   └── logger.py
└── assets/                 # Resources
    └── translations/
        ├── en.json
        └── id.json
```

### Data Flow

```
User Input → Wizard → Processing → Database → Visualization/Reports
```

1. User interacts with wizard (detection/game/stimulus)
2. Wizard collects configuration and data
3. Processing module performs analysis/generation
4. Results stored in SQLite database
5. Visualization and reports generated on demand

---

## Core Modules

### eye_tracker.py

Main application entry point and GUI manager.

**Class: `EyeTrackerMainGUI`**

Main application window with feature launchers.

```python
class EyeTrackerMainGUI:
    def __init__(self, root: tk.Tk)
    def setup_ui(self) -> None
    def launch_detection(self) -> None
    def launch_game(self) -> None
    def launch_stimulus(self) -> None
    def launch_obs_wizard(self) -> None
    def open_settings(self) -> None
    def open_database(self) -> None
```

**Usage Example:**

```python
import tkinter as tk
from eye_tracker import EyeTrackerMainGUI

root = tk.Tk()
app = EyeTrackerMainGUI(root)
root.mainloop()
```

---

## Detection Module

Pupil detection from video files using multiple algorithms.

### modules/detect_gemini8.py

Core detection algorithms implementation.

**Functions:**

```python
def detect_pupil_hough(
    frame: np.ndarray,
    param1: int = 50,
    param2: int = 13,
    min_radius: int = 73,
    max_radius: int = 75
) -> Tuple[Optional[int], Optional[int], Optional[int]]
"""
Circular Hough Transform detection.

Args:
    frame: Input grayscale frame
    param1: Canny edge threshold
    param2: Accumulator threshold
    min_radius: Minimum pupil radius
    max_radius: Maximum pupil radius

Returns:
    (x, y, radius) or (None, None, None) if not detected
"""

def detect_pupil_blob(
    frame: np.ndarray,
    min_area: int = 100,
    max_area: int = 1000
) -> Tuple[Optional[int], Optional[int], Optional[int]]
"""
Blob detection method.

Args:
    frame: Input grayscale frame
    min_area: Minimum blob area
    max_area: Maximum blob area

Returns:
    (x, y, radius) or (None, None, None) if not detected
"""

def detect_pupil_contour(
    frame: np.ndarray,
    threshold: int = 200
) -> Tuple[Optional[int], Optional[int], Optional[int]]
"""
Contour analysis method.

Args:
    frame: Input grayscale frame
    threshold: Binary threshold value

Returns:
    (x, y, radius) or (None, None, None) if not detected
"""

def detect_pupil_threshold(
    frame: np.ndarray,
    lower_hsv: List[int] = [0, 0, 200],
    upper_hsv: List[int] = [180, 30, 255]
) -> Tuple[Optional[int], Optional[int], Optional[int]]
"""
Simple threshold-based detection.

Args:
    frame: Input BGR frame
    lower_hsv: Lower HSV threshold
    upper_hsv: Upper HSV threshold

Returns:
    (x, y, radius) or (None, None, None) if not detected
"""

def detect_pupil_dlib(
    frame: np.ndarray,
    predictor_path: str = "shape_predictor_68_face_landmarks.dat"
) -> Tuple[Optional[int], Optional[int], Optional[int]]
"""
Dlib facial landmarks detection.

Args:
    frame: Input BGR frame
    predictor_path: Path to shape predictor file

Returns:
    (x, y, radius) or (None, None, None) if not detected
"""
```

**Usage Example:**

```python
import cv2
from modules.detect_gemini8 import detect_pupil_hough

# Load frame
frame = cv2.imread("eye_frame.jpg", cv2.IMREAD_GRAYSCALE)

# Detect pupil
x, y, radius = detect_pupil_hough(frame)

if x is not None:
    print(f"Pupil detected at ({x}, {y}) with radius {radius}")
else:
    print("Pupil not detected")
```

### modules/detection_wizard.py

GUI wizard for detection workflow.

**Class: `DetectionWizard`**

7-step wizard for video analysis.

```python
class DetectionWizard:
    def __init__(self, parent: tk.Tk)
    def launch(self) -> None
    def _show_step(self, step: int) -> None
```

**Steps:**

1. Video Selection
2. Method Selection (CHT/Blob/Contour/Threshold/Dlib)
3. Preview with Frame Scrubbing
4. Parameter Adjustment
5. Processing with Progress
6. Results Display
7. Export Options

---

## Game Module

Eye-controlled math quiz for cognitive assessment.

### modules/game_engine.py

Core game logic with Kalman filtering and button detection.

**Class: `EyeGameEngine`**

```python
class EyeGameEngine:
    def __init__(self, config: Dict[str, Any])
    def start_session(self, participant_info: Dict[str, str]) -> str
    def initialize_camera(self) -> bool
    def detect_eye_gaze(self, frame: np.ndarray) -> Tuple[int, int]
    def check_button_hover(self, gaze_x: int, gaze_y: int, buttons: List) -> Optional[int]
    def record_response(self, question_id: int, answer: str, correct: bool, time: float) -> None
    def save_session(self) -> str
```

**Features:**

- Kalman filter for smooth gaze tracking
- Dwell time detection (configurable)
- Adaptive difficulty
- Session recording
- Performance metrics

**Usage Example:**

```python
from modules.game_engine import EyeGameEngine

config = {
    "camera_id": 0,
    "dwell_time_seconds": 2.0,
    "adaptive_params": True
}

engine = EyeGameEngine(config)
session_id = engine.start_session({
    "participant_id": "P001",
    "age": "25",
    "session_date": "2025-11-11"
})

# Game loop
while running:
    frame = capture.read()
    gaze_x, gaze_y = engine.detect_eye_gaze(frame)
    button = engine.check_button_hover(gaze_x, gaze_y, buttons)
    # ... handle interaction

engine.save_session()
```

### modules/game_wizard.py

GUI wizard for game configuration and execution.

**Class: `GameWizard`**

```python
class GameWizard:
    def __init__(self, parent: tk.Tk)
    def launch(self) -> None
    def _configure_game(self) -> None
    def _start_game(self) -> None
```

---

## Stimulus Module

Generate standardized eye tracking test videos.

### modules/stimulus_generator.py

Video generation with multiple task types.

**Class: `StimulusGenerator`**

```python
class StimulusGenerator:
    def __init__(self, config: Dict[str, Any])
    def generate_video(
        self,
        protocol: str,
        output_path: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]
```

**Supported Protocols:**

- **Standard**: 5-minute basic calibration
- **Clinical**: 10-minute medical assessment
- **Research**: 15-minute comprehensive testing

**Task Types:**

```python
def generate_fixation_task(
    duration: int,
    positions: List[Tuple[int, int]],
    target_size: int
) -> List[np.ndarray]
"""Generate fixation point task."""

def generate_smooth_pursuit_task(
    duration: int,
    path_type: str,  # 'horizontal', 'vertical', 'circular', 'diagonal'
    speed: float
) -> List[np.ndarray]
"""Generate smooth pursuit task."""

def generate_saccade_task(
    duration: int,
    points: int,
    interval: float
) -> List[np.ndarray]
"""Generate saccade task."""
```

**Usage Example:**

```python
from modules.stimulus_generator import StimulusGenerator

config = {
    "resolution": (1920, 1080),
    "fps": 30,
    "target_size": 30,
    "target_color": (255, 0, 0)
}

generator = StimulusGenerator(config)

def progress(percent, message):
    print(f"{percent}%: {message}")

result = generator.generate_video(
    protocol="standard",
    output_path="stimulus_video.mp4",
    progress_callback=progress
)

print(f"Video generated: {result['output_path']}")
print(f"Duration: {result['duration']} seconds")
print(f"Tasks: {len(result['tasks'])}")
```

---

## Database Module

SQLite database management for all session types.

### modules/database_manager.py

CRUD operations for session data.

**Functions:**

```python
def create_detection_session(
    session_data: Dict[str, Any]
) -> str
"""
Create new detection session.

Args:
    session_data: Dictionary with session metadata and results

Returns:
    session_id: Unique session identifier
"""

def get_detection_session(
    session_id: str
) -> Optional[Dict[str, Any]]
"""Get detection session by ID."""

def search_sessions(
    session_type: str,
    filters: Dict[str, Any],
    limit: int = 100
) -> List[Dict[str, Any]]
"""
Search sessions with filters.

Args:
    session_type: 'detection', 'game', or 'stimulus'
    filters: Dictionary of filter criteria
    limit: Maximum results

Returns:
    List of matching sessions
"""

def delete_session(
    session_type: str,
    session_id: str
) -> bool
"""Delete session by ID."""

def export_to_csv(
    session_type: str,
    session_ids: List[str],
    output_path: str
) -> bool
"""Export sessions to CSV file."""

def get_statistics(
    session_type: str,
    date_range: Optional[Tuple[str, str]] = None
) -> Dict[str, Any]
"""Get statistics for session type."""
```

**Usage Example:**

```python
from modules.database_manager import (
    create_detection_session,
    search_sessions,
    get_statistics
)

# Create session
session_data = {
    "video_path": "eye_video.mp4",
    "method": "hough",
    "total_frames": 1000,
    "detected_frames": 950,
    "results": [...]
}

session_id = create_detection_session(session_data)

# Search sessions
sessions = search_sessions(
    session_type="detection",
    filters={"method": "hough", "date_from": "2025-11-01"},
    limit=50
)

# Get statistics
stats = get_statistics("detection", date_range=("2025-11-01", "2025-11-30"))
print(f"Total sessions: {stats['total_sessions']}")
print(f"Average success rate: {stats['avg_success_rate']:.1f}%")
```

---

## Visualization Module

Data visualization with multiple plot types.

### modules/visualization.py

**Functions:**

```python
def plot_gaze_trajectory(
    data: pd.DataFrame,
    output_path: Optional[str] = None
) -> None
"""Plot gaze trajectory over time with color coding."""

def generate_gaze_heatmap(
    data: pd.DataFrame,
    resolution: Tuple[int, int],
    sigma: float = 50,
    output_path: Optional[str] = None
) -> None
"""Generate fixation density heatmap."""

def plot_scanpath(
    data: pd.DataFrame,
    output_path: Optional[str] = None
) -> None
"""Plot fixations with saccade arrows."""

def plot_velocity_profile(
    data: pd.DataFrame,
    threshold: Optional[float] = None,
    output_path: Optional[str] = None
) -> None
"""Plot gaze velocity over time."""

def plot_roi_analysis(
    data: pd.DataFrame,
    rois: List[Dict[str, Any]],
    background_image: Optional[np.ndarray] = None,
    output_path: Optional[str] = None
) -> None
"""Plot gaze overlaid on regions of interest."""
```

**Usage Example:**

```python
import pandas as pd
from modules.visualization import (
    plot_gaze_trajectory,
    generate_gaze_heatmap,
    plot_scanpath
)

# Load data
data = pd.read_csv("gaze_data.csv")

# Generate plots
plot_gaze_trajectory(data, output_path="trajectory.png")
generate_gaze_heatmap(data, resolution=(1920, 1080), output_path="heatmap.png")
plot_scanpath(data, output_path="scanpath.png")
```

---

## Report Generation

Excel report generation with formatted sheets and charts.

### modules/report_generator.py

**Functions:**

```python
def generate_detection_excel_report(
    session_data: Dict[str, Any],
    output_path: str
) -> bool
"""
Generate comprehensive detection session report.

Creates 3-sheet workbook:
- Summary: Session metadata
- Results: Frame-by-frame data
- Statistics: Calculated metrics
"""

def generate_game_excel_report(
    session_data: Dict[str, Any],
    output_path: str
) -> bool
"""
Generate game session report with charts.

Creates 3-sheet workbook:
- Summary: Participant info
- Results: Question-by-question with color coding
- Analysis: Performance metrics
"""

def generate_comparison_report(
    sessions: List[Dict[str, Any]],
    output_path: str
) -> bool
"""
Generate multi-session comparison report.

Compares metrics across multiple sessions.
"""
```

---

## Utilities

### utils/config_manager.py

Configuration management with JSON storage.

**Functions:**

```python
def load_config(config_path: str = "config.json") -> Dict[str, Any]
"""Load configuration from file."""

def save_config(config_dict: Dict[str, Any], config_path: str = "config.json") -> bool
"""Save configuration to file."""

def get_default_config() -> Dict[str, Any]
"""Get default configuration values."""

def update_config_value(
    config_path: str,
    section: str,
    key: str,
    value: Any
) -> bool
"""Update specific configuration value."""
```

### utils/localization.py

Bilingual text management.

**Functions:**

```python
def load_translations(language_code: str) -> Dict[str, Any]
"""Load translation file for language."""

def get_text(key: str, language: Optional[str] = None, **kwargs) -> str
"""
Get translated text with dot notation support.

Args:
    key: Translation key (e.g., 'menu.detection')
    language: Optional language override
    **kwargs: Format arguments

Returns:
    Translated text

Example:
    get_text('messages.welcome', name='John')  # With formatting
    get_text('menu.settings')  # Simple lookup
"""

def switch_language(new_language: str) -> bool
"""Switch application language."""
```

### utils/logger.py

Logging configuration and utilities.

**Functions:**

```python
def init_logger(log_dir: str = "Logs") -> logging.Logger
"""Initialize application logger."""

def log_info(message: str) -> None
"""Log info message."""

def log_error(message: str, exc_info: bool = False) -> None
"""Log error message."""

def log_warning(message: str) -> None
"""Log warning message."""
```

---

## Configuration

Default configuration structure:

```json
{
  "version": "1.0.0",
  "language": "en",
  "first_run": true,
  "detection": {
    "default_method": "hough",
    "processing_mode": "auto",
    "kalman_process_noise": 0.1,
    "kalman_measurement_noise": 2.0,
    "hough_param1": 50,
    "hough_param2": 13,
    "hough_min_radius": 73,
    "hough_max_radius": 75
  },
  "game": {
    "camera_id": 0,
    "dwell_time_seconds": 2.0,
    "exit_hover_seconds": 3.0,
    "dark_mode": true,
    "fullscreen": true,
    "adaptive_params": true
  },
  "stimulus": {
    "default_protocol": "standard",
    "quality_threshold": 0.7,
    "target_size_range": [15, 40],
    "fixation_duration": 5,
    "smooth_pursuit_duration": 10
  },
  "ui": {
    "theme": "light",
    "window_width": 1024,
    "window_height": 768,
    "font_family": "Arial",
    "font_size": 12
  },
  "paths": {
    "database_dir": "Database",
    "sessions_dir": "Sessions",
    "logs_dir": "Logs"
  }
}
```

---

## Localization

Translation file structure (`assets/translations/en.json`):

```json
{
  "menu": {
    "detection": "Pupil Detection",
    "game": "Math Quiz Game",
    "stimulus": "Stimulus Generator",
    "settings": "Settings",
    "database": "Database",
    "help": "Help",
    "about": "About"
  },
  "messages": {
    "welcome": "Welcome to Eye Tracker",
    "select_video": "Please select a video file",
    "processing": "Processing..."
  }
}
```

**Adding New Language:**

1. Create `assets/translations/xx.json` (xx = language code)
2. Copy structure from `en.json`
3. Translate all values
4. Update `_available_languages` in `localization.py`

---

## Error Handling

All modules follow consistent error handling:

```python
try:
    result = risky_operation()
    log_info("Operation successful")
    return result
except SpecificError as e:
    log_error(f"Specific error: {e}", exc_info=True)
    # Handle gracefully
    return default_value
except Exception as e:
    log_error(f"Unexpected error: {e}", exc_info=True)
    # Show user-friendly message
    messagebox.showerror("Error", "An error occurred")
    return None
```

---

## Testing

### Unit Testing

```python
# Test detection algorithm
def test_hough_detection():
    frame = cv2.imread("test_eye.jpg", cv2.IMREAD_GRAYSCALE)
    x, y, radius = detect_pupil_hough(frame)
    assert x is not None
    assert 0 <= x < frame.shape[1]
    assert 0 <= y < frame.shape[0]
    assert radius > 0
```

### Integration Testing

```python
# Test full detection workflow
def test_detection_workflow():
    # Create session
    session_id = create_detection_session(test_data)
    
    # Verify in database
    session = get_detection_session(session_id)
    assert session is not None
    
    # Generate report
    success = generate_detection_excel_report(session, "test_report.xlsx")
    assert success
    
    # Cleanup
    delete_session("detection", session_id)
```

---

## Performance Considerations

### Optimization Tips

1. **Video Processing**: Use chunk-based processing for large videos
2. **Memory Management**: Close matplotlib figures after saving
3. **Database Queries**: Use indexes for search operations
4. **Caching**: Cache expensive computations (Kalman filter state)

### Benchmarks

- **Detection**: ~30 FPS (Hough), ~50 FPS (Threshold)
- **Game**: 60 FPS with Kalman filtering
- **Stimulus Generation**: Real-time (1x speed for 30 FPS)
- **Database Operations**: <100ms for typical queries
- **Report Generation**: ~2-5 seconds for full session

---

## Version History

### Version 1.0.0 (November 2025)

- Initial release
- 5 detection algorithms
- Eye-controlled game
- 3 stimulus protocols
- Full database management
- Visualization and reporting
- OBS integration
- Settings interface
- Bilingual support (EN/ID)

---

## Contributing

When extending the application:

1. Follow existing code structure
2. Add docstrings to all functions
3. Update translations for new UI text
4. Add logging for important operations
5. Handle errors gracefully
6. Update documentation
7. Test thoroughly

---

## License

© 2025 Medical Technology Study Program - ITS  
All Rights Reserved

---

**Author**: Kahlil Gibran Al Zulmi  
**NRP**: 5049221015  
**Institution**: Institut Teknologi Sepuluh Nopember
