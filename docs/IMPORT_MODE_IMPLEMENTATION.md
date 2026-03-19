# Import & Analyze Mode Implementation

## Overview
Complete implementation of reversed-ROI analysis workflow allowing users to import existing gaze data (CSV format) and define ROIs retroactively for analysis.

## Features Implemented

### 1. Mode Selection System
- Full-screen mode selector overlay with two workflow options:
  - **Live Recording Mode**: Original real-time recording workflow
  - **Import & Analyze Mode**: New retroactive analysis workflow
- Smooth transitions with animated cards
- Back button to return to mode selection

### 2. CSV Import Modal
- Multi-step import wizard:
  - **Step 1**: Upload gaze data CSV (frame_num, gaze_x, gaze_y)
  - **Step 2**: Upload corresponding video file
  - **Step 3**: Set frame offset for synchronization
- Real-time data preview showing:
  - Total frames in gaze data
  - Valid gaze points count
  - Detection rate percentage
- CSV validation with error handling

### 3. Frame Offset Support
- Adjustable frame offset parameter to sync gaze data with video
- Positive offset: gaze data started earlier than video
- Negative offset: video started earlier than gaze data
- Applied automatically during report generation

### 4. Report Generation from Imported Data
- New endpoint: `/api/generate-reports-from-import`
- Processes imported gaze data with current ROI definitions
- Generates:
  - **CSV**: Frame-by-frame gaze coordinates with ROI mapping
  - **Excel**: Statistical summary with detection rates per ROI
  - **PDF**: Complete report with metadata, heatmaps, and trajectories
  - **Heatmaps**: Jet colormap visualization per scene
  - **Trajectories**: Saccadic movement lines with fixation points

### 5. UI Integration
- Mode-specific toolbar buttons:
  - Live mode: Record, Post-process, Test Eye Gaze
  - Import mode: Generate Reports
- Conditional UI rendering based on active mode
- Disabled state management for buttons

## Technical Implementation

### Frontend (Vue.js 3)
**Files Modified:**
- `static/js/app.js`: Mode selection logic, CSV import handlers, report generation
- `templates/index.html`: Mode selector overlay, import modal, conditional toolbar
- `static/css/app.css`: Import modal styles, preview stats, mode cards

**Key Methods:**
```javascript
selectMode(mode)              // Switch between live/import modes
backToModeSelect()            // Return to mode selection screen
selectGazeCSV(event)          // Handle CSV file selection and parsing
selectImportVideo(event)      // Handle video file selection
processImportedData()         // Upload CSV and video to backend
generateReportsFromImport()   // Trigger report generation
```

### Backend (Flask/Python)
**Files Modified:**
- `video_roi_webapp.py`: Import endpoint, report generation, state management

**New Endpoints:**
```python
POST /api/import-gaze-data
  - Input: gaze_csv (file), frame_offset (int)
  - Output: {success, gaze_points, frame_offset, frame_range}
  - Validates CSV format, applies offset, stores in session

POST /api/generate-reports-from-import
  - Processes imported gaze data with current ROI definitions
  - Generates all report types (CSV, Excel, PDF, visualizations)
  - Returns: {success, session_dir, excel_report, pdf_report, gaze_points_processed}
```

**State Management:**
```python
class AppState:
    imported_gaze_data: List[dict]  # [{frame_num, gaze_x, gaze_y}]
    frame_offset: int               # Frame synchronization offset
    tracking_mode: str              # 'Live Recording', 'Mouse Tracking', 'Imported Data'
```

## Usage Workflow

### Import Mode Workflow
1. Launch application → Select "Import & Analyze" mode
2. Import modal opens:
   - Choose gaze data CSV file (frame_num, gaze_x, gaze_y columns required)
   - Choose corresponding video file
   - Set frame offset if needed (default: 0)
   - Preview shows total frames, valid points, detection rate
3. Click "Load & Analyze" → Video loads with single full-length scene
4. Define ROIs by:
   - Splitting scenes as needed
   - Drawing ROI rectangles on video
   - Naming ROIs for analysis
5. Click "Generate Reports" button
6. Reports generated in session directory:
   - `imported_gaze_data.csv`
   - `roi_analysis_report.xlsx`
   - `roi_analysis_report.pdf`
   - `heatmap_<scene_name>.png` (per scene)
   - `trajectory_<scene_name>.png` (per scene)

### Frame Offset Examples
- **Offset = 0**: Gaze and video start simultaneously
- **Offset = -100**: Video frame 0 corresponds to gaze frame 100 (video started 100 frames later)
- **Offset = 50**: Gaze frame 0 corresponds to video frame 50 (gaze started 50 frames later)

## CSV Format Requirements

### Required Columns
```csv
frame_num,gaze_x,gaze_y
0,512.3,384.7
1,515.1,386.2
2,520.4,390.8
...
```

### Optional Columns
- `timestamp`: Frame timestamp (ignored during import)
- Any other metadata columns (preserved but not used)

### Validation
- Header row must contain: `frame_num`, `gaze_x`, `gaze_y` (case-insensitive)
- `frame_num`: Integer frame number
- `gaze_x`, `gaze_y`: Float pixel coordinates
- Invalid rows are skipped with warning

## File Structure
```
roi_web_app/
├── static/
│   ├── js/
│   │   └── app.js              # Vue.js app logic (mode selection, import handlers)
│   └── css/
│       └── app.css             # Import modal styles
├── templates/
│   └── index.html              # Mode selector, import modal UI
├── video_roi_webapp.py         # Flask backend with import endpoints
├── report_generator.py         # Report generation (uses tracking_mode metadata)
└── sessions/
    └── import_session_<timestamp>/  # Generated reports storage
        ├── imported_gaze_data.csv
        ├── roi_analysis_report.xlsx
        ├── roi_analysis_report.pdf
        ├── heatmap_*.png
        └── trajectory_*.png
```

## Testing Checklist

### Import Workflow
- [ ] Mode selector displays correctly
- [ ] Import modal opens when "Import & Analyze" clicked
- [ ] CSV file upload validates required columns
- [ ] Preview shows correct statistics
- [ ] Video upload works for common formats (mp4, avi, mov)
- [ ] Frame offset accepts positive/negative integers
- [ ] "Load & Analyze" enables only when both files selected

### Report Generation
- [ ] Generate Reports button enabled after ROI definition
- [ ] Progress modal shows during generation
- [ ] All reports created in session directory
- [ ] CSV contains correct frame_num + offset
- [ ] Heatmaps show gaze concentration
- [ ] Trajectories show saccades and fixations
- [ ] PDF contains all sections with correct metadata
- [ ] Excel has per-ROI statistics

### Edge Cases
- [ ] CSV with missing rows handled gracefully
- [ ] Video/gaze mismatch detected (frame count)
- [ ] Empty CSV rejected with error message
- [ ] Large CSV files (>100k rows) processed efficiently
- [ ] Switching back to Live mode resets import state
- [ ] Multiple imports in same session work correctly

## Known Limitations
1. **CSV Format**: Only supports simple CSV with frame_num, gaze_x, gaze_y
2. **Video Sync**: Assumes constant frame rate (no variable FPS support)
3. **Memory**: Large gaze datasets (>1M points) may cause performance issues
4. **Validation**: No automatic video/gaze duration matching
5. **Offset Range**: Frame offset not validated against video/gaze duration

## Future Enhancements
- Support for additional CSV formats (EyeLink, Tobii, Pupil Labs)
- Automatic frame offset calculation using video/gaze timestamps
- Batch processing for multiple videos/gaze files
- Interactive offset adjustment with video/gaze preview
- Gaze data resampling for FPS mismatches
- Export gaze data with ROI labels for machine learning

## Debugging Tips
- Check browser console for import errors
- Verify CSV encoding (UTF-8 recommended)
- Check Flask logs for backend processing errors
- Ensure video file is readable by OpenCV
- Test with small CSV first (<1000 frames)
- Verify frame_num is 0-indexed

## API Reference

### POST /api/import-gaze-data
**Request:**
```
Content-Type: multipart/form-data
Body:
  - gaze_csv: File (CSV format)
  - frame_offset: Integer (default: 0)
```

**Response:**
```json
{
  "success": true,
  "gaze_points": 15000,
  "frame_offset": -100,
  "frame_range": [0, 14999]
}
```

### POST /api/generate-reports-from-import
**Request:**
```json
No body required (uses session state)
```

**Response:**
```json
{
  "success": true,
  "session_dir": "/path/to/sessions/import_session_20260205_123456",
  "excel_report": "roi_analysis_report.xlsx",
  "pdf_report": "roi_analysis_report.pdf",
  "gaze_points_processed": 12450
}
```

## Credits
- Implemented: February 2026
- Framework: Flask + Vue.js 3 + OpenCV
- Visualization: Matplotlib (jet colormap), ReportLab (PDF)
