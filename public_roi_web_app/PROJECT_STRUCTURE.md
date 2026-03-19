# SOROT Project Structure

**Clean, essential-only architecture - All Tobii-specific code removed**

Last Updated: February 18, 2026

---

## 📁 Directory Structure

```
public_roi_web_app/
│
├── Core Application Files
│   ├── video_roi_webapp.py       # Main Flask web application (126 KB)
│   ├── gaze_post_processor.py    # Gaze data processing pipeline (8 KB)
│   ├── report_generator.py       # PDF/Excel report generation (13 KB)
│   ├── export_scenes_rois.py     # Scene/ROI data export utilities (10 KB)
│   └── app_launcher.py           # Application launcher (3 KB)
│
├── Build & Configuration
│   ├── requirements.txt          # Python dependencies (clean, no Tobii refs)
│   ├── build_exe.py              # PyInstaller build script (3 KB)
│   ├── BUILD.bat                 # Windows build script
│   ├── BUILD_SIMPLE.bat          # Simplified build script
│   ├── INSTALL.bat               # Dependency installer
│   └── START.bat                 # Application launcher
│
├── Frontend Assets
│   ├── static/                   # CSS, JavaScript, images
│   │   ├── css/
│   │   │   └── app.css
│   │   └── js/
│   │       └── app.js
│   └── templates/                # Flask HTML templates
│       ├── index.html            # Main application interface
│       └── test_roi_gaze.html    # Gaze testing page
│
├── Data Storage
│   ├── uploaded_videos/         # User-uploaded video files
│   ├── downloaded_videos/        # YouTube-downloaded videos
│   ├── projects/                 # Saved workspace files (.json)
│   └── sessions/                 # Recording sessions & reports
│
├── Documentation
│   └── docs/                     # API & implementation guides
│       ├── API_USAGE_EXAMPLES.md
│       ├── BUILD_GUIDE.md
│       ├── DISTRIBUTION_README.md
│       ├── EXPORT_DOCUMENTATION.md
│       ├── IMPLEMENTATION_GUIDE.md
│       ├── IMPORT_MODE_IMPLEMENTATION.md
│       └── TEST_IMPORT_MODE.md
│
└── Tests
    └── tests/                    # Unit & integration tests
        ├── test_roi_api.py
        ├── test_roi_gaze_connection.py
        ├── test_roi_gaze_webapp.py
        ├── test_setup.py
        ├── test_video_compatibility.py
        └── test_vue.html

```

---

## 🗑️ Removed Files (Cleanup Summary)

### Tobii-Specific Components
- `setup.py` - Tobii Pro Plugin packaging script
- `modules/pro_features_loader.py` - Tobii plugin loader
- `validation_points.py` - Tobii Ghost validation tool (858 lines)
- Comments in `requirements.txt` referencing Tobii Pro plugin

### Obsolete/Duplicate Files
- `video_roi_demo.py` - Old Tkinter GUI version (1,830 lines)
- `requirements_public.txt` - Duplicate of requirements.txt
- `CLEANUP_SUMMARY.md` - Outdated documentation
- `modules/` - Empty folder (removed)

**Total removed**: 7 files + 1 folder (~2,700 lines of code)

---

## 🎯 Core Functionality (Tobii-Free)

### Input Methods
1. **Mouse Tracking** - Built-in fallback gaze simulation
2. **CSV Import** - Import pre-recorded gaze data from any eye tracker
3. **Generic Webcam** - Hough Circle detection for basic eye tracking
4. **OBS Integration** (optional) - External eye tracking via OBS Studio

### Analysis Features
- Heatmap generation (vectorized NumPy for 10x performance)
- Fixation detection using spatial clustering
- ROI hit statistics and dwell time analysis
- Scene-based segmentation
- Trajectory visualization with saccade mapping

### Export Formats
- Excel (.xlsx) - Comprehensive data tables
- PDF - Visual reports with charts
- CSV - Raw gaze coordinates
- JSON - Project workspace files
- PNG - Heatmaps and trajectory images

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Application
```bash
# Windows
START.bat

# Linux/Mac
python video_roi_webapp.py
```

### 3. Access Web Interface
Open browser: `http://localhost:5000`

---

## 📊 Technical Details

### Architecture
- **Backend**: Flask 3.0+ with SocketIO for real-time communication
- **Frontend**: Vue.js-inspired reactive components
- **Image Processing**: OpenCV 4.8+ with NumPy vectorization
- **Data Analysis**: Pandas 2.0+ for efficient data manipulation
- **Visualization**: Matplotlib 3.7+ for heatmaps and trajectories

### Performance Optimizations
✅ Vectorized heatmap generation (10x faster)  
✅ Lazy loading for large video files  
✅ WebSocket for real-time gaze streaming  
✅ Server-side rendering for heavy computations

### Security Features
✅ Path traversal protection  
✅ File type validation  
✅ Size limits (500MB max uploads)  
✅ CORS configuration  
✅ Input sanitization

---

## 📝 License

MIT License - See LICENSE file for details

---

## 👨‍💻 Author

**Kahlil Gibran Al Zulmi**  
- Research: Eye tracking and visual attention analysis
- Implementation: Professional Python engineering standards
- Date: February 2026

---

## 🔄 Version History

### v2.0.0 (2026-02-18) - Clean Architecture Release
✅ Removed all Tobii-specific dependencies  
✅ Refactored with professional Python standards  
✅ Added comprehensive type hints  
✅ Improved error handling  
✅ Optimized performance with NumPy vectorization  
✅ Streamlined codebase (removed 2,700+ lines)

### v1.x (2026-01-06)
- Initial implementation with Tobii Ghost support
- Basic ROI editing and heatmap generation

---

**Note**: This is a clean, academic research tool designed for general eye tracking analysis. No proprietary eye tracker hardware is required - mouse tracking and CSV import modes make it accessible to all researchers.
