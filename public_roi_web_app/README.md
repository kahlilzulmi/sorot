# SOROT - System for Optimized Region of Interest Tracking

**Web-based eye tracking analysis tool for video stimuli with Region of Interest (ROI) annotation**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)

---

## 📋 Overview

SOROT is a comprehensive web-based platform for eye tracking research, designed to facilitate the analysis of gaze behavior during video stimuli presentation. The application provides an intuitive interface for defining Regions of Interest (ROIs), managing video scenes, and generating detailed gaze analytics.

### Key Features

✅ **Interactive ROI Editor** - Draw and label regions of interest directly on video frames  
✅ **Scene Management** - Split videos into meaningful segments for targeted analysis  
✅ **Multiple Input Modes**:
  - Live gaze recording with mouse tracking
  - Import existing gaze data from CSV files  
  - Generic webcam eye tracking support

✅ **Comprehensive Analysis**:
  - Gaze heatmap generation
  - Fixation duration statistics
  - ROI-based attention metrics
  - Frame-by-frame gaze visualization

✅ **Professional Reporting**:
  - CSV data export
  - JSON workspace format
  - Statistical summaries
  - Visual analytics

---

## 🎓 Academic Context

This tool was developed as part of academic research in human-computer interaction and visual attention analysis. It supports:

- **Psychology Research** - Studying attention patterns in multimedia content
- **UX Research** - Evaluating user interface designs
- **Marketing Research** - Analyzing advertisement effectiveness
- **Educational Research** - Understanding learning behavior from video materials

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Windows 10/11, macOS, or Linux
- Modern web browser (Chrome, Firefox, Edge)

### Installation

```bash
# 1. Clone or extract the repository
cd video-roi-analyzer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python video_roi_webapp.py

# 4. Open your browser
# Navigate to: http://localhost:5000
```

### First Use

1. **Select Mode**: Choose between "Live Recording" or "Import & Analyze"
2. **Upload Video**: Provide a video stimulus file or download from YouTube
3. **Define Scenes**: Split your video into meaningful segments
4. **Draw ROIs**: Create regions of interest for each scene
5. **Record/Import**: Capture gaze data or import existing CSV files
6. **Analyze**: Generate heatmaps, statistics, and reports

---

## 📊 Features In Detail

### 1. Dual Operation Modes

#### Live Recording Mode
- Real-time gaze capture using mouse tracking (no special hardware required)
- Fullscreen video playback
- Automatic session recording and data storage
- Post-processing pipeline for immediate analysis

#### Import & Analyze Mode
- Import CSV files with gaze coordinates
- Column mapping interface for flexible data formats
- Frame offset synchronization for multi-camera setups
- Retroactive ROI definition on existing data

### 2. ROI Management

- **Interactive Drawing**: Click and drag to create rectangular ROIs
- **Labeling System**: Name ROIs for semantic analysis
- **Scene-Specific ROIs**: Different ROIs for each video segment
- **Visual Feedback**: Color-coded overlays and boundary indicators

### 3. Scene Segmentation

- **Flexible Splitting**: Divide videos at any frame
- **Merge Capability**: Combine adjacent scenes
- **Custom Naming**: Label scenes with descriptive names
- **Timeline Visualization**: Interactive scene boundary markers
- **Undo/Redo**: Full edit history support

### 4. Analysis & Reporting

- **Heatmaps**: Visual representation of gaze distribution
- **Fixation Metrics**: Duration, count, and percentage per ROI
- **CSV Export**: Raw data and processed statistics
- **JSON Workspace**: Save and reload entire projects
- **Frame-by-frame Review**: Detailed playback with gaze overlay

---

## 🏗️ Architecture

### Technology Stack

- **Backend**: Flask 3.0+ (Python web framework)
- **Frontend**: Vue.js 3 (reactive UI)
- **Real-time**: Flask-SocketIO (WebSocket communication)
- **Video Processing**: OpenCV (computer vision)
- **Data Analysis**: Pandas, NumPy (data manipulation)
- **Visualization**: Matplotlib (heatmaps and plots)
- **PDF Reports**: ReportLab (document generation)

### Directory Structure

```
video-roi-analyzer/
├── video_roi_webapp.py          # Main Flask application
├── gaze_post_processor.py       # Analysis engine
├── report_generator.py          # Report creation
├── export_scenes_rois.py        # Data export utilities
├── static/
│   ├── css/app.css              # Stylesheets
│   └── js/app.js                # Vue.js frontend
├── templates/
│   └── index.html               # Main UI template
├── projects/                    # Saved workspaces
├── sessions/                    # Recording sessions
├── uploaded_videos/             # Video files
└── docs/                        # Additional documentation
```

---

## 📖 Usage Guide

### Recording a Session (Live Mode)

1. **Upload or download a video** stimulus
2. **Define scenes** by splitting the video at key points
3. **Create ROIs** for each scene (e.g., "Product", "Brand", "Call-to-Action")
4. **Click Record** - video will play in fullscreen
5. **Move your mouse** to simulate gaze position during playback
6. **Data is saved** automatically to `sessions/` folder
7. **Generate reports** from the post-processing menu

### Importing Existing Data

1. **Select "Import & Analyze"** mode on startup
2. **Upload your gaze CSV** file (any format)
3. **Map columns** to frame number, gaze X, and gaze Y
4. **Upload the stimulus video** for visualization
5. **(Optional) Upload eye gaze video** for dual-video comparison
6. **Define ROIs** on the imported data
7. **Generate reports** with retroactive ROI analysis

### Exporting Results

- **Workspace**: `File → Save As` → JSON format with all scenes and ROIs
- **Scene Data**: `File → Export Data` → CSV with scene boundaries
- **ROI Statistics**: Automatically generated in session folders
- **Heatmaps**: PNG images saved during post-processing

---

## 🔬 Data Formats

### Input CSV Format (Import Mode)

```csv
frame_number,gaze_x,gaze_y
0,640,360
1,645,365
2,650,370
...
```

**Note**: Column names are flexible - the app provides a mapping interface.

### Output ROI Statistics

```csv
scene_name,roi_label,fixation_count,total_duration,percentage
Scene 1,Product,45,2.5,35.2
Scene 1,Brand,32,1.8,24.1
...
```

### Workspace JSON

```json
{
  "video_filename": "advertisement.mp4",
  "scenes": [
    {
      "name": "Scene 1",
      "start_frame": 0,
      "end_frame": 150,
      "rois": [
        {"label": "Product", "x": 100, "y": 200, "width": 300, "height": 200}
      ]
    }
  ]
}
```

---

## 📚 Documentation

- **[API Documentation](docs/API_DOCUMENTATION.md)** - REST endpoints and WebSocket events (if available)
- **[Export Guide](docs/EXPORT_DOCUMENTATION.md)** - Data export formats and usage (if available)
- **[Build Guide](docs/BUILD_GUIDE.md)** - Creating standalone executables (if available)

---

## 🧑‍💻 Development

### Running Tests

```bash
# Test basic setup
python tests/test_setup.py

# Test video compatibility
python tests/test_video_compatibility.py
```

### Building Standalone Application

```bash
# Windows
BUILD.bat

# Or manually with PyInstaller
pyinstaller --onefile video_roi_webapp.py
```

---

## 📄 License

MIT License

This software is provided for academic and research purposes.

---

## 🙏 Acknowledgments

- Developed for academic research in visual attention analysis
- Built with Flask, Vue.js, OpenCV, and modern web technologies
- Designed to be accessible for researchers without specialized hardware

---

## 📧 Contact

For questions, issues, or collaboration opportunities:
- **GitHub Issues**: For bug reports and feature requests
- **Academic Inquiries**: Contact the Artificial Intelligence and Digital Technology Research Center (KATD), Institut Teknologi Sepuluh Nopember, Surabaya, Indonesia.

---

**Built for the research community**
