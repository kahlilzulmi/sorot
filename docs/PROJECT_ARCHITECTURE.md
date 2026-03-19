# Eye Tracker Research Software - Architecture Document

**Project:** Undergraduate Final Year Project 2025  
**Author:** Kahlil Gibran Al Zulmi (5049201113)  
**Program:** Medical Technology, ITS  
**Deadline:** Week of November 10-17, 2025  

---

## 🎯 Project Overview

Integrated eye tracking research software with three main features:
1. **Gaze Detection** - Post-process recorded eye tracking videos
2. **Math Quiz Game** - Real-time eye-controlled game with recording
3. **Stimulus Simulation** - Generate/run stimulus protocols with tracking

## 📁 File Structure

```
tugasakhir/
├── eye_tracker.py              # Main entry point with GUI
├── config.json                 # User configuration
├── requirements.txt            # Python dependencies
├── README.md                   # Installation & usage guide
│
├── modules/                    # Core functionality modules
│   ├── system_check.py        # System requirements verification
│   ├── detection_algorithms.py # 5 detection methods
│   ├── detection_wizard.py    # Detection UI wizard
│   ├── game_engine.py         # Math game logic
│   ├── game_wizard.py         # Game UI wizard
│   ├── stimulus_generator.py  # Video stimulus creation
│   ├── stimulus_live.py       # Live stimulus with tracking
│   ├── stimulus_wizard.py     # Stimulus UI wizard
│   ├── database_manager.py    # SQLite session management
│   ├── report_generator.py    # PDF/Excel reports
│   ├── visualization.py       # Charts, heatmaps, plots
│   ├── kalman_filter.py       # Smoothing algorithm
│   ├── obs_integration.py     # OBS setup & control
│   └── localization.py        # EN/ID language support
│
├── utils/                      # Utility functions
│   ├── config_manager.py      # Config load/save
│   ├── logger.py              # Logging system
│   ├── video_utils.py         # Video I/O operations
│   ├── file_utils.py          # File operations
│   └── ui_helpers.py          # Common UI components
│
├── assets/                     # Resources
│   ├── fonts/
│   │   └── arial.ttf
│   ├── icons/
│   │   └── logo.png
│   ├── templates/
│   │   ├── obs_scene.json
│   │   ├── questions_template.xlsx
│   │   └── report_template.html
│   └── translations/
│       ├── en.json
│       └── id.json
│
├── Database/                   # Session storage
│   ├── detection_sessions.db
│   ├── game_sessions.db
│   ├── stimulus_sessions.db
│   └── participants.db
│
└── Sessions/                   # Output data
    ├── detection_YYYYMMDD_HHMMSS/
    │   ├── gaze_position.csv
    │   ├── overlayed_video_hough.mp4
    │   ├── overlayed_video_contour.mp4
    │   ├── comparison_report.pdf
    │   └── summary.xlsx
    ├── game_session_YYYYMMDD_HHMMSS/
    │   ├── participant_001_YYYYMMDD_HHMMSS/
    │   │   ├── gaze_data.csv
    │   │   ├── answers.csv
    │   │   ├── metadata.csv
    │   │   ├── area_timeline.png
    │   │   ├── area_duration_percentage.png
    │   │   ├── heatmap.png
    │   │   └── participant_report.pdf
    │   └── batch_summary.pdf
    └── stimulus_YYYYMMDD_HHMMSS/
        ├── protocol_standard.json
        ├── live_tracking_data.csv
        └── session_report.pdf
```

## 🔧 Technical Specifications

### Python Environment
- **Version:** Python 3.10+ (via venv)
- **Style Guide:** PEP 8 compliant
- **Programming Style:** Functional (def only, no classes)
- **GUI Framework:** Tkinter (main), Pygame (game)

### System Requirements
- **OS:** Windows 10/11
- **RAM:** Minimum 8 GB (auto-chunking for detection)
- **Tobii:** Eye Tracker 5 + Tobii Ghost + Tobii Experience
- **OBS:** OBS Studio with Virtual Camera
- **Python:** 3.10+ with venv

### Key Dependencies
```
opencv-python>=4.8.0
numpy>=1.24.0
pandas>=2.0.0
matplotlib>=3.7.0
Pillow>=10.0.0
pygame>=2.5.0
openpyxl>=3.1.0
reportlab>=4.0.0
psutil>=5.9.0
```

## 🏗️ Module Specifications

### 1. system_check.py
**Purpose:** Verify system requirements on first launch  
**Functions:**
- `check_windows_version()` - Returns Windows 10/11 status
- `check_tobii_installed()` - Check processes/services
- `check_tobii_connected()` - Verify USB device
- `check_obs_installed()` - Check OBS installation
- `check_ram_available()` - Get available RAM (min 8GB)
- `run_system_check()` - Full check with GUI progress
- `save_check_results(config_path)` - Save to config
- `load_check_results(config_path)` - Load previous check

### 2. detection_algorithms.py
**Purpose:** 5 detection methods for gaze position  
**Functions:**
- `detect_hough_circle(frame, params)` - Hough Circle Transform
- `detect_contour(frame, params)` - Contour-based detection
- `detect_color(frame, params)` - Color-based detection
- `detect_combined(frame, params)` - Contour + Color hybrid
- `detect_blob(frame, params)` - Blob detector
- `apply_kalman_filter(positions, kalman_state)` - Smooth trajectory
- `process_video_single_method(video_path, method, params)` - Single method
- `process_video_parallel(video_path, methods, params)` - Parallel processing
- `align_multiple_videos(video_paths)` - Sync start points
- `compare_detection_methods(results_dict)` - Generate comparison

### 3. detection_wizard.py
**Purpose:** Step-by-step detection interface  
**Steps:**
1. Video selection (single/multiple)
2. Method selection (checkboxes for 5 methods)
3. Parameter tuning (sliders with real-time preview)
4. Processing mode (auto/parallel/sequential based on RAM)
5. Video alignment (if multiple videos)
6. Execute processing (with progress bar)
7. Results visualization & export

### 4. game_engine.py
**Purpose:** Eye-controlled math quiz game  
**Functions:**
- `load_questions_from_excel(file_path)` - Import question bank
- `initialize_virtual_camera(camera_id)` - Setup OBS cam
- `detect_gaze_realtime(frame, params)` - Real-time detection
- `update_kalman_filter(measurement, kalman_state)` - Smooth gaze
- `check_button_hover(gaze_pos, button_rects)` - Collision detection
- `handle_dwell_click(hover_time, threshold)` - Dwell-time click
- `calculate_roi(gaze_pos, screen_elements)` - Area of interest
- `render_game_frame(screen, game_state, debug_mode)` - Draw game
- `render_debug_overlay(screen, roi_areas)` - F12 debug view
- `save_gaze_data(session_data, output_dir)` - Export CSV
- `generate_game_report(session_data, output_dir)` - Create report

### 5. stimulus_generator.py
**Purpose:** Generate pre-recorded stimulus videos  
**Functions:**
- `create_stimulus_protocol(protocol_dict)` - Define protocol
- `load_protocol_from_file(json_path)` - Load preset
- `save_protocol_to_file(protocol_dict, json_path)` - Save custom
- `generate_fixation_task(duration, params)` - Static target
- `generate_smooth_pursuit(duration, path_type, params)` - Moving target
- `generate_saccade_task(duration, points, params)` - Jump task
- `render_stimulus_video(protocol, output_path)` - Create video
- `get_default_protocol()` - genvidsim4.py preset

### 6. stimulus_live.py
**Purpose:** Real-time stimulus with tracking  
**Functions:**
- `initialize_live_stimulus(protocol, camera_id)` - Setup
- `detect_gaze_quality(frame, detection_result)` - Quality score
- `adapt_target_size(quality_history, current_size)` - Auto-adjust
- `adapt_detection_params(quality_history, current_params)` - Learn
- `run_live_stimulus(protocol, camera_id, output_dir)` - Execute
- `pause_for_repositioning(screen, message)` - Quality warning
- `save_live_session(tracking_data, output_dir)` - Export

### 7. database_manager.py
**Purpose:** SQLite session management  
**Functions:**
- `init_databases()` - Create DB files
- `add_detection_session(metadata)` - Insert detection record
- `add_game_session(metadata)` - Insert game record
- `add_stimulus_session(metadata)` - Insert stimulus record
- `add_participant(participant_data)` - New participant
- `update_participant(participant_id, data)` - Update record
- `delete_participant(participant_id)` - Remove record
- `search_sessions(query, filters)` - Search by date/participant
- `get_batch_sessions(session_ids)` - Retrieve multiple
- `export_database_to_excel(db_path, output_path)` - Backup

### 8. report_generator.py
**Purpose:** Generate PDF/Excel reports  
**Functions:**
- `create_detection_report(session_data, output_path)` - Detection PDF
- `create_game_report(session_data, output_path)` - Game PDF
- `create_stimulus_report(session_data, output_path)` - Stimulus PDF
- `create_batch_report(sessions_list, output_path)` - Multi-session
- `export_to_excel(session_data, output_path)` - Excel export
- `add_its_branding(pdf_doc, header_path, footer_path)` - Branding
- `generate_statistical_summary(data_list)` - Stats table
- `compare_participants(participant_ids, metric)` - Comparison
- `compare_sessions(session_ids, metric)` - Session comparison

### 9. visualization.py
**Purpose:** Generate charts, heatmaps, plots  
**Functions:**
- `create_timeline_plot(gaze_df, output_path)` - Area over time
- `create_duration_histogram(gaze_df, output_path)` - Bar chart
- `create_trajectory_plot(gaze_df, output_path)` - X/Y histograms
- `create_heatmap(gaze_df, screen_size, output_path)` - Density map
- `create_scanpath(gaze_df, screen_size, output_path)` - Path trace
- `create_fixation_plot(fixations, output_path)` - Fixation circles
- `create_comparison_chart(methods_dict, metric, output_path)` - Compare
- `create_statistical_boxplot(data_groups, output_path)` - Box plot
- `calculate_fixations(gaze_df, threshold)` - Detect fixations
- `calculate_saccades(gaze_df, threshold)` - Detect saccades

### 10. obs_integration.py
**Purpose:** OBS setup and configuration  
**Functions:**
- `check_obs_running()` - Is OBS active?
- `launch_obs(obs_path)` - Start OBS
- `create_obs_scene_template(template_path)` - Generate scene JSON
- `guide_ssoverlay_setup()` - Step-by-step instructions
- `test_virtual_camera()` - Verify OBS Virtual Camera
- `get_virtual_camera_id()` - Find camera index
- `save_obs_config(config_dict)` - Store settings

### 11. localization.py
**Purpose:** Bilingual support (EN/ID)  
**Functions:**
- `load_translations(language_code)` - Load JSON
- `get_text(key, language)` - Get translated string
- `switch_language(new_language, config_path)` - Change language
- `get_available_languages()` - List supported langs

### 12. config_manager.py
**Purpose:** Configuration management  
**Functions:**
- `load_config(config_path)` - Load JSON/INI config
- `save_config(config_dict, config_path)` - Save config
- `get_default_config()` - Default settings
- `validate_config(config_dict)` - Check validity
- `migrate_config(old_config, version)` - Update old configs

### 13. logger.py
**Purpose:** Comprehensive logging  
**Functions:**
- `init_logger(log_dir)` - Setup logging
- `log_info(message)` - Info level
- `log_warning(message)` - Warning level
- `log_error(message, exception)` - Error level
- `log_debug(message)` - Debug level
- `log_session_start(feature, metadata)` - Session begin
- `log_session_end(feature, metadata)` - Session end
- `get_log_history(days)` - Retrieve logs

## 🎨 GUI Design

### Main Window (eye_tracker.py)
```
┌─────────────────────────────────────────────────────────┐
│  Eye Tracker Research Software v1.0        🌐 EN | ID   │
├─────────────────────────────────────────────────────────┤
│  👤 Kahlil Gibran Al Zulmi - Medical Technology - ITS   │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ SYSTEM STATUS                                      │ │
│  │ ✓ Windows 11 Detected                             │ │
│  │ ✓ Tobii Eye Tracker Connected                     │ │
│  │ ✓ OBS Studio Running                              │ │
│  │ ✓ 16 GB RAM Available                             │ │
│  │ [ Run System Check Again ]  [ Skip Setup ]        │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   📹 GAZE    │  │   🎮 MATH    │  │   🎯 STIMULUS│  │
│  │  DETECTION   │  │   QUIZ GAME  │  │  SIMULATION  │  │
│  │              │  │              │  │              │  │
│  │  Process eye │  │  Eye-control │  │  Generate or │  │
│  │  tracking    │  │  math quiz   │  │  run live    │  │
│  │  videos      │  │  with record │  │  stimulus    │  │
│  │              │  │              │  │              │  │
│  │ [Start Wizard]│ │ [Start Game] │  │[Start Wizard]│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ RECENT SESSIONS                         [View All]│ │
│  │ • 2025-11-09 14:30 - Game Session (P001)          │ │
│  │ • 2025-11-09 10:15 - Detection (Hough + Contour)  │ │
│  │ • 2025-11-08 16:45 - Stimulus Protocol Standard   │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  [⚙️ Settings]  [📊 Database]  [📖 Help]  [ℹ️ About]    │
└─────────────────────────────────────────────────────────┘
```

## 📊 Data Flow

### Detection Workflow
```
Video Input → Method Selection → Parameter Tuning → 
Processing (w/ progress) → Kalman Smoothing → 
CSV + Overlayed Video → Comparison (if multiple) → 
Report Generation → Database Save
```

### Game Workflow
```
Question Bank Load → Trial Mode → Main Game Start →
Real-time Gaze Detection → Kalman Smoothing → 
Dwell-time Click Detection → ROI Recording →
Game End → Visualization → Report → Database Save
```

### Stimulus Workflow
```
Protocol Selection → (Video Gen OR Live Mode) →
[Live: Real-time Detection + Quality Monitoring + 
Adaptive Adjustment] → Session Recording →
Report Generation → Database Save
```

## 🔐 Configuration Schema

```json
{
  "version": "1.0",
  "language": "en",
  "system_check": {
    "completed": true,
    "last_check": "2025-11-10T10:30:00",
    "tobii_connected": true,
    "obs_configured": true
  },
  "detection": {
    "default_method": "hough",
    "processing_mode": "auto",
    "chunk_size_frames": 1000,
    "kalman_process_noise": 0.1,
    "kalman_measurement_noise": 2.0
  },
  "game": {
    "camera_id": 0,
    "dwell_time_seconds": 2.0,
    "exit_hover_seconds": 3.0,
    "debug_mode_key": "F12",
    "question_bank": "assets/templates/questions_template.xlsx"
  },
  "stimulus": {
    "default_protocol": "standard",
    "quality_threshold": 0.7,
    "adaptation_enabled": true,
    "target_size_range": [15, 40]
  },
  "ui": {
    "theme": "light",
    "window_size": [1024, 768],
    "font_size": 12
  },
  "paths": {
    "database_dir": "Database/",
    "sessions_dir": "Sessions/",
    "logs_dir": "Logs/",
    "assets_dir": "assets/"
  }
}
```

## 🚀 Implementation Phases

### Phase 1: Foundation (Days 1-2)
- [ ] Project structure setup
- [ ] requirements.txt and venv
- [ ] Config management
- [ ] Logger system
- [ ] System check module
- [ ] Main GUI skeleton

### Phase 2: Detection Module (Days 2-3)
- [ ] 5 detection algorithms
- [ ] Kalman filter
- [ ] Video processing pipeline
- [ ] Detection wizard UI
- [ ] Video alignment tool
- [ ] Visualization functions

### Phase 3: Game Module (Days 3-4)
- [ ] Port game3_with_recording.py
- [ ] Modularize functions
- [ ] Excel question import
- [ ] Debug overlay (F12)
- [ ] Adaptive parameters
- [ ] Game wizard UI

### Phase 4: Stimulus Module (Days 4-5)
- [ ] Port genvidsim4.py
- [ ] Protocol CRUD system
- [ ] Live stimulus engine
- [ ] Quality adaptation
- [ ] Stimulus wizard UI

### Phase 5: Data & Reports (Days 5-6)
- [ ] SQLite databases
- [ ] Database manager UI
- [ ] Report generator (PDF/Excel)
- [ ] Statistical analysis
- [ ] Batch comparison

### Phase 6: Integration & Polish (Day 6-7)
- [ ] OBS integration
- [ ] Bilingual support (EN/ID)
- [ ] Testing & debugging
- [ ] Documentation
- [ ] PyInstaller executable
- [ ] Final review

## 📝 Notes

- All functions follow PEP 8
- No classes used (functional programming only)
- Comprehensive logging for all operations
- Graceful error handling with user-friendly messages
- Progress indicators for long operations
- Session recovery mechanisms
- Adaptive performance based on system resources

---

**Status:** Architecture Complete ✅  
**Next:** Begin Phase 1 Implementation  
**Deadline:** November 17, 2025
