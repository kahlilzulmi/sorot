# Changelog

All notable changes to Eye Tracking Research Software will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2025-11-17

### Added

#### Core Modules
- **System Check Module**: Validates Python version, dependencies, camera access, and display on first launch
- **Detection Wizard**: GUI-based video processing wizard with 5 detection methods (CHT, Blob, Contour, Threshold, Dlib)
- **Detection Algorithms**: Comprehensive pupil detection with Kalman filtering and real-time processing
- **Game Module**: Interactive eye-tracking game with calibration, dynamic questions, scoring, and session recording
- **Stimulus Generator**: Creates eye movement stimulus videos (fixation, smooth pursuit, saccade, vergence)
- **Database Manager**: SQLite database management for detection and game sessions with advanced search/filter
- **Visualization Module**: Statistical analysis with matplotlib/seaborn plots, heatmaps, and gaze paths
- **Report Generator**: Automated PDF/Excel report generation with comprehensive statistics and visualizations
- **OBS Integration Wizard**: Automated OBS Studio setup with virtual camera, scenes, and recording profiles
- **Settings Interface**: Comprehensive 6-tab settings dialog for all configuration parameters

#### Configuration & Localization
- JSON-based configuration system with default settings and validation
- Bilingual support (English/Indonesian) with 438+ translation keys
- Theme support (light/dark mode)
- Customizable fonts and window sizes
- Per-module configuration sections

#### File Management
- SQLite databases for persistent session storage
- CSV/Excel export functionality
- Automated directory creation (Database/, Sessions/, Logs/)
- Template-based report generation
- Session replay from saved data

#### Performance Features
- Chunked video processing for large files (memory-efficient)
- Auto/manual processing mode selection
- Multi-threaded video generation
- Progress tracking with real-time updates
- Adaptive parameter adjustment

#### Build & Distribution
- PyInstaller specification for standalone executable
- Automated build scripts (PowerShell)
- Post-build finalization (README, LICENSE, directories)
- One-directory distribution package
- UPX compression for smaller file size

### Detection Methods

#### Circular Hough Transform (CHT)
- Configurable param1, param2, radius range
- Pre-processing: Gaussian blur, median filter
- Post-processing: Kalman filter for smoothing
- Best for: Clear, high-contrast pupils

#### Blob Detection
- Configurable area range, circularity, convexity
- Adaptive thresholding
- Best for: Noisy images with variable lighting

#### Contour Analysis
- Binary thresholding
- Contour area and shape filtering
- Best for: Well-defined pupil boundaries

#### Simple Threshold
- HSV color space filtering
- Fastest method (real-time capable)
- Best for: Quick testing and validation

#### Dlib Facial Landmarks
- 68-point facial landmark detection
- Eye region extraction
- Most accurate but slowest
- Best for: Research requiring high precision

### Game Features

#### Calibration System
- 9-point calibration grid
- Polynomial transformation mapping
- Visual feedback during calibration
- Recalibration option

#### Question System
- Excel-based question bank
- Multiple choice (2-4 options)
- Dynamic button positioning
- Dwell-time selection (gaze-based clicking)

#### Scoring & Statistics
- Real-time score tracking
- Accuracy percentage
- Time per question
- Session summary
- SQLite storage for history

#### Adaptive Features
- Dynamic parameter adjustment based on performance
- Configurable adaptation rate
- Toggleable on/off

### Stimulus Protocols

#### Standard Protocol
- Fixation: 30s center target
- Smooth Pursuit: 30s moving target (circular)
- Saccade: 30s point-to-point jumps (9 positions)
- Vergence: 30s depth changes (size variation)

#### Clinical Protocol
- Extended duration (60s tasks)
- Larger targets (easier for impaired vision)
- Slower movements

#### Research Protocol
- Precise timing
- Smaller targets (higher precision)
- Faster movements
- Additional metrics

### Database Schema

#### Detection Sessions
```sql
CREATE TABLE detection_sessions (
    id INTEGER PRIMARY KEY,
    filename TEXT,
    method TEXT,
    processing_mode TEXT,
    success_rate REAL,
    total_frames INTEGER,
    detected_frames INTEGER,
    timestamp TEXT,
    video_path TEXT,
    csv_path TEXT,
    results_json TEXT
)
```

#### Game Sessions
```sql
CREATE TABLE game_sessions (
    id INTEGER PRIMARY KEY,
    session_id TEXT UNIQUE,
    start_time TEXT,
    end_time TEXT,
    total_questions INTEGER,
    correct_answers INTEGER,
    score REAL,
    avg_time_per_question REAL,
    calibration_quality REAL,
    settings_json TEXT
)
```

### Documentation

#### User Documentation
- BUILD_GUIDE.md: Comprehensive build instructions
- README_DIST.md: End-user manual with screenshots
- PYINSTALLER_REFERENCE.md: Quick reference for PyInstaller
- TROUBLESHOOTING.md: Complete troubleshooting guide

#### Developer Documentation
- API_DOCUMENTATION.md: Complete API reference
- DEVELOPER_GUIDE.md: Development workflow and best practices
- CHANGELOG.md: Version history

### Dependencies

#### Core
- Python 3.10+
- OpenCV (cv2) 4.5+
- NumPy 1.21+
- Tkinter (included with Python)

#### Game & Visualization
- Pygame 2.0+
- Matplotlib 3.4+
- Seaborn 0.11+
- Scipy 1.7+

#### Data Management
- Pandas 1.3+
- openpyxl 3.0+
- Pillow (PIL) 8.3+

#### Packaging
- PyInstaller 6.16.0
- pywin32 (Windows-specific)

### System Requirements

#### Minimum
- OS: Windows 10 (64-bit)
- CPU: Intel Core i3 or equivalent
- RAM: 4 GB
- Storage: 2 GB free space
- Camera: 720p webcam
- Display: 1280x720

#### Recommended
- OS: Windows 11 (64-bit)
- CPU: Intel Core i5 or better
- RAM: 8 GB or more
- Storage: 5 GB free space
- Camera: 1080p webcam
- Display: 1920x1080 or higher

---

## [0.9.0] - 2025-11-11

### Added
- OBS integration wizard with automated setup
- Virtual camera detection and configuration
- Recording profile creation
- Scene setup automation

---

## [0.8.0] - 2025-11-10

### Added
- Report generator module with PDF/Excel output
- Statistical analysis functions
- Visualization module with matplotlib integration
- Heatmap generation for gaze patterns

---

## [0.7.0] - 2025-11-09

### Added
- Database management module
- SQLite database initialization
- Session search and filter UI
- Export functionality (CSV, Excel)

---

## [0.6.0] - 2025-11-08

### Added
- Stimulus generator wizard
- Protocol selection (standard, clinical, research)
- Video generation for eye movement tasks
- Quality assessment metrics

---

## [0.5.0] - 2025-11-07

### Added
- Game module with eye-tracking gameplay
- Calibration system (9-point)
- Question bank integration
- Scoring and session tracking

---

## [0.4.0] - 2025-11-06

### Added
- Blob detection algorithm
- Contour analysis method
- Simple threshold detection
- Dlib facial landmarks integration

---

## [0.3.0] - 2025-11-05

### Added
- Detection wizard GUI
- Circular Hough Transform (CHT) detection
- Kalman filter for smoothing
- Progress tracking and real-time updates

---

## [0.2.0] - 2025-11-04

### Added
- Configuration management system
- Bilingual localization (EN/ID)
- Theme support (light/dark)
- Logger utility with file/console output

---

## [0.1.0] - 2025-11-03

### Added
- Initial project setup
- System check module
- Main GUI framework with Tkinter
- Basic file structure
- Requirements file

---

## Development Roadmap

### Future Enhancements (v1.1.0+)

#### Planned Features
- [ ] Linux/Mac support (remove pywin32 dependency)
- [ ] Network streaming for remote eye tracking
- [ ] Real-time gaze overlay for presentations
- [ ] Machine learning-based pupil detection
- [ ] Calibration-free eye tracking
- [ ] Multi-monitor support
- [ ] 3D gaze mapping
- [ ] Eye fatigue detection
- [ ] Blink detection and analysis
- [ ] Fixation/saccade classification

#### Performance Improvements
- [ ] GPU acceleration (CUDA support)
- [ ] Parallel processing for multiple videos
- [ ] Incremental database updates
- [ ] Lazy loading for large datasets
- [ ] Memory-mapped file support

#### User Interface
- [ ] Drag-and-drop batch processing
- [ ] Live preview during detection
- [ ] Customizable dashboard
- [ ] Export templates editor
- [ ] Keyboard shortcuts
- [ ] Touch screen support

#### Integration
- [ ] Tobii eye tracker support
- [ ] EyeLink integration
- [ ] MATLAB export
- [ ] Python API for scripting
- [ ] REST API for web integration
- [ ] Plugin system for extensions

#### Clinical Features
- [ ] HIPAA-compliant data handling
- [ ] Patient management system
- [ ] Normative database comparison
- [ ] Automated diagnosis suggestions
- [ ] Progress tracking over time
- [ ] Multi-user access control

---

## Known Issues

### Version 1.0.0

#### Critical
- None

#### Major
- Dlib detection requires separate download of shape_predictor_68_face_landmarks.dat (70MB)
- Large videos (>10GB) may cause memory issues even with chunked processing
- OBS auto-start may fail if OBS is not in default installation path

#### Minor
- Settings dialog may not fit on screens <1280x720
- Dark theme not fully applied to all third-party widgets
- Some translation keys missing context in Indonesian

#### Cosmetic
- Progress bar animation slightly choppy on slow machines
- Report generation shows console window briefly on Windows
- matplotlib warnings in console (suppressible)

### Workarounds

**Dlib Shape Predictor**:
```bash
# Download from dlib-models repo
wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bunzip2 shape_predictor_68_face_landmarks.dat.bz2
```

**Large Video Processing**:
- Use lower chunk_size (500 instead of 1000)
- Convert video to lower resolution before processing
- Use faster detection method (threshold instead of dlib)

**OBS Path Issues**:
- Manually provide OBS installation path in wizard
- Add OBS to system PATH

---

## Migration Guide

### From v0.9.0 to v1.0.0

#### Configuration Changes
```json
// Old (v0.9.0)
{
  "language": "en",
  "detection_method": "hough"
}

// New (v1.0.0)
{
  "ui": {
    "language": "en",
    "theme": "light"
  },
  "detection": {
    "default_method": "hough",
    "processing_mode": "auto"
  }
}
```

#### Database Schema
No migration needed - databases are compatible.

#### API Changes
```python
# Old
from detect_gemini8 import process_video
results = process_video("video.mp4", "hough")

# New
from modules.detection_algorithms import detect_pupils_in_video
results = detect_pupils_in_video("video.mp4", method="hough", mode="auto")
```

---

## Acknowledgments

### Development Team
- **Developer**: Kahlil Gibran Al Zulmi (5049201113)
- **Advisor 1**: Prof. Dr. Ir. Adhi Dharma Wibawa, S.T., M.T.
- **Advisor 2**: dr. Zain Budi Syulthoni, Sp.KJ.

### Institution
- Medical Technology Study Program
- Faculty of Intelligent Electrical and Informatics Technology
- Institut Teknologi Sepuluh Nopember, Surabaya

### Libraries & Tools
- OpenCV Community
- Pygame Developers
- Matplotlib Project
- PyInstaller Team
- OBS Studio Project
- Python Software Foundation

### Special Thanks
- ITS Medical Technology Research Lab
- Early beta testers
- Indonesian translation contributors

---

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the tags on this repository.

**Version Format**: MAJOR.MINOR.PATCH

- **MAJOR**: Incompatible API changes
- **MINOR**: New features (backward-compatible)
- **PATCH**: Bug fixes (backward-compatible)

---

**Last Updated**: November 17, 2025
