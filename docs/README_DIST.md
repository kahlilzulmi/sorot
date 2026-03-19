# Eye Tracker - Research Software

**Version 1.0.0**  
Medical Technology Study Program - Institut Teknologi Sepuluh Nopember

---

## 📋 About

Eye tracking research software for medical technology applications. This software provides comprehensive tools for:

- **Pupil Detection**: 5 detection algorithms (CHT, Blob, Contour, Threshold, Dlib)
- **Interactive Game**: Eye-controlled math quiz for cognitive assessment
- **Stimulus Generation**: Clinical and research protocol video generation
- **Data Analysis**: Visualization, reporting, and statistical analysis
- **Session Management**: Database for storing and retrieving sessions
- **OBS Integration**: Screen recording setup wizard

---

## 💻 System Requirements

### Minimum Requirements:
- **OS**: Windows 10 (64-bit) or later
- **Processor**: Intel Core i3 or equivalent
- **RAM**: 4 GB
- **Storage**: 500 MB free space
- **Display**: 1024x768 resolution
- **Camera**: Webcam (for game module)

### Recommended Requirements:
- **OS**: Windows 11 (64-bit)
- **Processor**: Intel Core i5 or better
- **RAM**: 8 GB or more
- **Storage**: 2 GB free space
- **Display**: 1920x1080 or higher
- **Camera**: HD Webcam

---

## 🚀 Installation

### Standalone Executable (Recommended)

1. Download the `EyeTracker` folder
2. Double-click `EyeTracker.exe` to launch
3. No Python installation required!

### First Run

On first launch, the application will:
1. Perform system check
2. Create necessary directories:
   - `Database/` - Session data storage
   - `Sessions/` - Temporary session files
   - `Logs/` - Application logs
3. Create default configuration (`config.json`)

---

## 📖 User Guide

### Main Interface

The main window provides access to all features:

1. **🔍 Detection**: Analyze videos for pupil detection
2. **🎮 Game**: Eye-controlled math quiz
3. **📹 Stimulus**: Generate calibration and test videos
4. **🎬 OBS Setup**: Configure screen recording
5. **⚙️ Settings**: Application preferences
6. **💾 Database**: View and manage sessions
7. **❓ Help**: Quick help guide
8. **ℹ️ About**: Application information

### Detection Module

**Purpose**: Analyze video files to detect and track pupil position.

**Steps**:
1. Click "Detection" button
2. Select video file (MP4, AVI, MKV, MOV)
3. Choose detection method:
   - **CHT**: Circular Hough Transform (recommended for clear pupils)
   - **Blob**: Blob detection (good for low contrast)
   - **Contour**: Contour analysis (robust to noise)
   - **Threshold**: Simple thresholding (fastest)
   - **Dlib**: Facial landmarks (most accurate)
4. Preview and adjust parameters
5. Process video
6. View results and export data

**Output**:
- CSV file with frame-by-frame pupil coordinates
- Statistics (success rate, average radius, etc.)
- Visualizations (trajectory, heatmap, scanpath)
- Excel report

### Game Module

**Purpose**: Assess cognitive function through eye-controlled interaction.

**Setup**:
1. Click "Game" button
2. Enter participant information
3. Configure settings:
   - Number of questions
   - Difficulty level
   - Time limit
4. Camera setup and calibration

**Gameplay**:
- Look at answer buttons to select
- Hold gaze for 2 seconds (dwell time)
- Progress through questions
- View final score and statistics

**Output**:
- Session recording with timestamps
- Performance metrics (accuracy, response time)
- Excel report with question-by-question breakdown

### Stimulus Module

**Purpose**: Generate standardized eye tracking test videos.

**Protocols**:
1. **Standard**: Basic calibration (5 minutes)
   - 9-point fixation
   - Horizontal smooth pursuit
   - Vertical smooth pursuit
   - Saccades

2. **Clinical**: Medical assessment (10 minutes)
   - Extended fixation tasks
   - Multiple pursuit patterns
   - Complex saccade sequences
   - Attention tasks

3. **Research**: Comprehensive testing (15 minutes)
   - All clinical tasks
   - Additional patterns (circular, diagonal)
   - Variable speeds and sizes
   - Longer durations

**Steps**:
1. Click "Stimulus" button
2. Select protocol
3. Configure settings:
   - Resolution (720p, 1080p, 1440p, 4K)
   - FPS (24, 30, 60)
   - Target size and color
4. Preview task sequence
5. Generate video (background processing)

**Output**:
- MP4 video file (H.264)
- JSON metadata file
- Task list with timestamps

### Database Module

**Purpose**: Manage all session data in one place.

**Features**:
- Browse all sessions (Detection, Game, Stimulus)
- Search and filter by date, type, participant
- View detailed session information
- Export data to CSV/Excel
- Delete old sessions
- Generate comparison reports

### Settings Module

**Purpose**: Customize application behavior.

**Tabs**:
1. **UI Preferences**
   - Language (English/Indonesian)
   - Theme (Light/Dark)
   - Window size
   - Font settings

2. **Detection**
   - Default method
   - Processing mode
   - Kalman filter parameters
   - Method-specific settings

3. **Game**
   - Camera settings
   - Timing (dwell time, exit time)
   - Display options
   - Adaptive difficulty

4. **Stimulus**
   - Default protocol
   - Quality threshold
   - Task durations
   - Target sizes

5. **File Paths**
   - Database directory
   - Sessions directory
   - Logs directory
   - Assets directory

6. **Advanced**
   - OBS integration
   - Report branding
   - Performance options

---

## 🎯 Quick Start Guide

### Scenario 1: Analyze Existing Video

1. Launch EyeTracker.exe
2. Click **Detection**
3. Select your video file
4. Choose **CHT** method (default)
5. Click **Process**
6. View results and export

**Time**: ~5 minutes (depending on video length)

### Scenario 2: Run Eye-Controlled Quiz

1. Launch EyeTracker.exe
2. Click **Game**
3. Enter participant info
4. Select 10 questions, Easy difficulty
5. Complete camera setup
6. Start game
7. View results

**Time**: ~10-15 minutes

### Scenario 3: Generate Calibration Video

1. Launch EyeTracker.exe
2. Click **Stimulus**
3. Select **Standard Protocol**
4. Choose 1080p, 30 FPS
5. Click **Generate**
6. Wait for completion
7. Use video for experiments

**Time**: ~2-3 minutes generation + 5 minutes video

---

## 📊 Output Files

### Detection Session
```
Database/
  detection_sessions.db       - SQLite database
Sessions/
  detection_YYYY-MM-DD_HH-MM-SS/
    results.csv              - Frame-by-frame data
    statistics.json          - Summary statistics
    report.xlsx              - Excel report
    trajectory.png           - Gaze trajectory plot
    heatmap.png             - Fixation heatmap
```

### Game Session
```
Database/
  game_sessions.db            - SQLite database
Sessions/
  game_YYYY-MM-DD_HH-MM-SS/
    responses.csv            - Question responses
    statistics.json          - Performance metrics
    report.xlsx              - Excel report
```

### Stimulus Session
```
Database/
  stimulus_sessions.db        - SQLite database
Sessions/
  stimulus_YYYY-MM-DD_HH-MM-SS/
    output_video.mp4         - Generated video
    metadata.json            - Task information
    tasks.csv                - Task list
    report.xlsx              - Excel report
```

---

## 🔧 Troubleshooting

### Application Won't Start

**Issue**: Double-clicking EyeTracker.exe does nothing  
**Solution**: 
- Right-click EyeTracker.exe → Run as Administrator
- Check antivirus - add exception for EyeTracker folder
- Ensure Windows 10/11 (64-bit)

### Camera Not Detected (Game Module)

**Issue**: "No camera found" error  
**Solution**:
- Check if camera is connected
- Try different camera (Settings → Game → Camera ID)
- Restart application
- Check camera permissions in Windows settings

### Video Processing Slow

**Issue**: Detection takes very long  
**Solution**:
- Use lower resolution video
- Try different detection method (CHT is fastest)
- Change processing mode to "chunk" (Settings → Detection)
- Close other applications
- Increase chunk size (Settings → Detection)

### Out of Memory Error

**Issue**: Application crashes during processing  
**Solution**:
- Process video in chunks (Settings → Detection → Processing Mode → chunk)
- Reduce chunk size (Settings → Detection → Chunk Size)
- Close other applications
- Upgrade RAM (minimum 4GB, recommended 8GB+)

### Translation Issues

**Issue**: Some text appears in wrong language  
**Solution**:
- Go to Settings → UI Preferences → Language
- Select desired language
- Click OK
- Restart application

### Database Errors

**Issue**: Cannot save session or view database  
**Solution**:
- Check write permissions for Database folder
- Delete corrupt database file (backup first!)
- Application will recreate on next launch
- Check disk space

---

## 📞 Support

### For Issues or Questions:

**Author**: Kahlil Gibran Al Zulmi  
**NRP**: 5049221015 
**Program**: Medical Technology Study Program  
**Institution**: Institut Teknologi Sepuluh Nopember

**Advisors**:
- Prof. Dr. Ir. Adhi Dharma Wibawa, S.T., M.T.
- dr. Zain Budi Syulthoni, Sp.KJ.

### Reporting Bugs:

When reporting issues, please include:
1. Windows version
2. Error message (if any)
3. Steps to reproduce
4. Screenshots (if applicable)
5. Log files from `Logs/` folder

---

## 📄 License

© 2025 All Rights Reserved  
Medical Technology Study Program - ITS

This software is developed for research and educational purposes.

---

## 🔄 Version History

### Version 1.0.0 (November 2025)
- Initial release
- 5 detection algorithms
- Eye-controlled game module
- Stimulus video generation (3 protocols)
- Database management
- Visualization and reporting
- OBS integration wizard
- Comprehensive settings interface
- Bilingual support (EN/ID)

---

## 🙏 Acknowledgments

- OpenCV Community
- Pygame Community
- Matplotlib Team
- PyInstaller Developers
- ITS Medical Technology Faculty

---

**Thank you for using Eye Tracker Research Software!**
