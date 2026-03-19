# Eye Tracker Research Software

**Undergraduate Final Year Project 2025**  
Medical Technology Study Program - Institut Teknologi Sepuluh Nopember

## Project Information

- **Author:** Kahlil Gibran Al Zulmi
- **NRP:** 5049221015
- **Advisor:** Prof. Dr. Ir. Adhi Dharma Wibawa, S.T., M.T.
- **Co-Advisor:** dr. Zain Budi Syulthoni, Sp.KJ.

## Overview

Integrated eye tracking research software designed for medical technology applications with three main features:

1. **Gaze Detection** - Post-process recorded eye tracking videos with 5 different detection methods
2. **Math Quiz Game** - Real-time eye-controlled math quiz with comprehensive gaze recording
3. **Stimulus Simulation** - Generate or run live stimulus protocols for eye tracking experiments

## Key Features

- **Multiple Detection Algorithms**: Hough Circle, Contour, Color-based, Combined, and Blob detection
- **Eye-Controlled Game**: Math quiz controlled entirely by eye gaze with dwell-time clicking
- **Stimulus Protocols**: Pre-recorded and live stimulus generation with adaptive quality adjustment
- **Comprehensive Reporting**: PDF and Excel reports with statistical analysis, heatmaps, and visualizations
- **Database Management**: SQLite databases for session tracking and participant management
- **Bilingual Support**: English and Indonesian languages
- **Adaptive Parameters**: Machine learning-based parameter adjustment for optimal tracking
- **Batch Analysis**: Compare multiple sessions, participants, or methods

## System Requirements

### Hardware
- **OS:** Windows 10 or Windows 11 (64-bit)
- **RAM:** Minimum 8 GB (16 GB recommended)
- **Processor:** Intel Core i5 or equivalent (i7 recommended)
- **Storage:** 2 GB free space minimum
- **Eye Tracker:** Tobii Eye Tracker 5

### Software
- **Tobii Experience** - Eye tracker driver
- **Tobii Ghost** - Gaze overlay software
- **OBS Studio** - For virtual camera and recording (latest version)
- **Python 3.10+** - Programming environment

## Installation

### Step 1: Install System Requirements

1. **Install Tobii Software:**
   - Download and install Tobii Experience from [Tobii website](https://gaming.tobii.com/)
   - Install Tobii Ghost for gaze overlay
   - Connect your Tobii Eye Tracker 5 and calibrate

2. **Install OBS Studio:**
   - Download from [OBS Project](https://obsproject.com/)
   - Install with default settings
   - Enable Virtual Camera in OBS

### Step 2: Set Up Python Environment

1. **Install Python 3.10+:**
   ```powershell
   # Download from https://www.python.org/downloads/
   # During installation, check "Add Python to PATH"
   ```

2. **Clone or Download This Repository:**
   ```powershell
   cd C:\Users\kahli\tugasakhir
   # Or your preferred directory
   ```

3. **Create Virtual Environment:**
   ```powershell
   python -m venv venv
   ```

4. **Activate Virtual Environment:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

5. **Install Dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

### Step 3: First Run Setup

1. **Run the Application:**
   ```powershell
   python eye_tracker.py
   ```

2. **Complete System Check:**
   - The software will automatically check your system
   - Follow on-screen instructions for Tobii calibration
   - Configure OBS Virtual Camera if prompted

3. **Configure OBS (if needed):**
   - Add Window Capture source
   - Select SSOverlay.exe (from Tobii Ghost)
   - Configure Virtual Camera
   - The software provides step-by-step guidance

## Usage Guide

### Main Menu

When you launch the software, you'll see three main options:

#### 1. Gaze Detection

Process recorded eye tracking videos to extract gaze positions:

- **Input:** Video files (MP4, MKV, AVI)
- **Methods:** Choose one or multiple detection methods
- **Output:** CSV data, overlayed videos, comparison charts

**Workflow:**
1. Select video file(s)
2. Choose detection method(s)
3. Adjust parameters (or use defaults)
4. Select processing mode (auto/parallel/sequential)
5. If multiple videos: align start points
6. Process and view results

#### 2. Math Quiz Game

Eye-controlled math quiz for testing and research:

- **Control:** Look at buttons for 2 seconds to "click"
- **Recording:** Automatic gaze tracking during gameplay
- **Analysis:** Generates comprehensive reports and visualizations

**Workflow:**
1. Start game wizard
2. Complete tutorial mode (2 questions)
3. Press START for main game
4. Answer questions by looking at BENAR (correct) or SALAH (wrong)
5. View results and reports after completion

**Debug Mode:** Press F12 to toggle ROI visualization

#### 3. Stimulus Simulation

Generate or run stimulus protocols:

- **Video Generation:** Create pre-recorded stimulus videos
- **Live Simulation:** Run real-time stimulus with gaze tracking
- **Protocols:** Fixation, smooth pursuit, saccadic tasks

**Workflow:**
1. Choose "Generate Video" or "Run Live"
2. Select or customize protocol
3. Run stimulus
4. View tracking data and reports

### Database Management

Access session history and participant data:

- **Search:** Find sessions by date, participant, or type
- **Filter:** Sort by various criteria
- **Export:** Export data to Excel
- **Batch Analysis:** Compare multiple sessions

### Settings

Configure software preferences:

- **Language:** Switch between English and Indonesian
- **Detection Parameters:** Adjust default settings
- **Game Settings:** Modify dwell time, questions, etc.
- **Stimulus Protocols:** Edit or create protocols
- **Reports:** Customize report branding

## Project Structure

```
tugasakhir/
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── requirements.txt
│
├── main_app/                           # Main application
│   ├── eye_tracker.py                  # Application entry point
│   ├── config.json                     # User configuration
│   ├── requirements.txt
│   ├── modules/                        # Core functionality
│   │   ├── detection_algorithms.py
│   │   ├── detection_wizard.py
│   │   ├── game_engine.py
│   │   ├── game_wizard.py
│   │   ├── stimulus_generator.py
│   │   ├── stimulus_wizard.py
│   │   ├── video_alignment.py
│   │   ├── video_alignment_wizard.py
│   │   ├── database_manager.py
│   │   ├── database_viewer.py
│   │   ├── report_generator.py
│   │   ├── settings_dialog.py
│   │   ├── system_check.py
│   │   ├── obs_wizard.py
│   │   └── visualization.py
│   ├── utils/                          # Utility functions
│   │   ├── logger.py                   # Logging system
│   │   ├── config_manager.py           # Configuration management
│   │   └── localization.py             # Bilingual support
│   ├── assets/                         # Resources
│   │   ├── fonts/
│   │   ├── icons/
│   │   ├── templates/
│   │   └── translations/               # EN/ID translations
│   ├── build/                          # Build scripts and specifications
│   │   ├── build.ps1
│   │   ├── eye_tracker.spec
│   │   └── post_build.ps1
│   ├── databases/                      # SQLite databases
│   ├── Sessions/                       # Session output data
│   ├── Logs/                           # Application logs
│   └── tests/                          # Test files
│
├── roi_web_app/                        # ROI Web Application
│   ├── README.md
│   ├── requirements.txt
│   ├── video_roi_webapp.py             # Main web application
│   ├── video_roi_demo.py
│   ├── test_roi_gaze_webapp.py
│   ├── test_roi_gaze_connection.py
│   ├── static/                         # Web assets
│   ├── templates/                      # HTML templates
│   ├── projects/                       # ROI project data
│   ├── uploaded_videos/
│   └── downloaded_videos/
│
├── workspace/                          # Development and analysis workspace
│   ├── requirements.txt
│   ├── analysis_scripts/               # Data analysis scripts
│   ├── detection_scripts/              # Detection testing scripts
│   ├── game_scripts/                   # Game development scripts
│   ├── utilities/                      # Development utilities
│   ├── sessions/                       # Test session data
│   ├── projects/                       # Project files
│   └── output/                         # Analysis outputs
│
├── docs/                               # Documentation
│   ├── API_DOCUMENTATION.md
│   ├── BUILD_GUIDE.md
│   ├── DEVELOPER_GUIDE.md
│   ├── PROJECT_ARCHITECTURE.md
│   ├── PROJECT_SUMMARY.md
│   ├── QUICKSTART.md
│   ├── TROUBLESHOOTING.md
│   └── ... (more documentation)
│
└── Archived/                           # Archived data and results
    ├── comparison_results_offset_-660.csv
    ├── stimulus_ground_truth.csv
    └── output_v*/                      # Previous version outputs
```

## Configuration

The `config.json` file stores all settings. You can edit it directly or through the Settings menu.

Key configuration sections:
- `detection` - Detection algorithm parameters
- `game` - Game settings and controls
- `stimulus` - Stimulus protocol defaults
- `ui` - Interface preferences
- `paths` - Directory locations

## Output Data

### Detection Sessions
```
Sessions/detection_YYYYMMDD_HHMMSS/
├── gaze_position.csv           # Frame-by-frame gaze data
├── overlayed_video_hough.mp4   # Processed video
├── comparison_report.pdf       # Analysis report
└── summary.xlsx               # Statistical summary
```

### Game Sessions
```
Sessions/game_session_YYYYMMDD_HHMMSS/
├── participant_001_YYYYMMDD_HHMMSS/
│   ├── gaze_data.csv
│   ├── answers.csv
│   ├── metadata.csv
│   ├── area_timeline.png
│   ├── heatmap.png
│   └── participant_report.pdf
└── batch_summary.pdf
```

### Stimulus Sessions
```
Sessions/stimulus_YYYYMMDD_HHMMSS/
├── protocol_standard.json
├── live_tracking_data.csv
└── session_report.pdf
```

## Troubleshooting

### Tobii Not Detected
- Ensure Tobii Experience is running
- Check USB connection
- Run Tobii calibration
- Restart the application

### OBS Virtual Camera Not Found
- Open OBS Studio
- Start Virtual Camera (Tools → Virtual Camera)
- Verify camera index in Settings

### Low Performance
- Close other applications
- Reduce video resolution for detection
- Use sequential processing instead of parallel
- Check available RAM (minimum 8 GB)

### Video Processing Errors
- Verify video file format (MP4, MKV, AVI supported)
- Check if video file is corrupted
- Try re-exporting or remuxing the video

## Logging

All activities are logged in `Logs/` directory:
- Daily log files: `eyetracker_YYYYMMDD.log`
- Includes timestamps, function names, and detailed messages
- Logs are kept permanently for audit trail

## Support

For issues or questions:
- Check `Logs/` for error messages
- Review `PROJECT_ARCHITECTURE.md` for technical details
- Contact: [Your Email/Contact]

## License

This software is developed for academic research purposes as part of an undergraduate final year project at Institut Teknologi Sepuluh Nopember.

## Disclaimer

This project was developed solely for educational and academic research purposes in the field of Medical Technology. This software performs visual data processing from video recordings (post-processing) and does not perform any modification, disassembly, or piracy of the original hardware or software from Tobii AB.

## Acknowledgments

- **Advisor:** Prof. Dr. Ir. Adhi Dharma Wibawa, S.T., M.T.
- **Co-Advisor:** dr. Zain Budi Syulthoni, Sp.KJ.
- **Medical Technology Study Program** - Faculty of Medicine and Health, ITS
- **Tobii Technology** - For eye tracking hardware and software

---

**Version:** 1.0.0  
**Last Updated:** January 26, 2026  
**Status:** In Development

Developed for Medical Technology Study Program, Institut Teknologi Sepuluh Nopember

