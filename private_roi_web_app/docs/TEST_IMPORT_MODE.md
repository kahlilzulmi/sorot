# Import Mode Testing Checklist

## Phase 3 Implementation Status: ✅ COMPLETE

### Backend Endpoints (All Implemented)

#### 1. `/api/import-gaze-data` (POST)
**Status:** ✅ Implemented
- Accepts: JSON with `gaze_data` array and `frame_offset`
- Validates: Data structure (frame_num, gaze_x, gaze_y)
- Applies: Frame offset to imported data
- Stores: In `state.imported_gaze_data`
- Returns: Success, gaze points count, frame range

#### 2. `/api/upload-video` (POST)
**Status:** ✅ Implemented (existing)
- Accepts: Video file upload
- Returns: Video info (resolution, FPS, total_frames, duration)
- Creates: Default scene spanning full video

#### 3. `/api/upload-gaze-video` (POST)
**Status:** ✅ Implemented
- Accepts: Tobii Ghost gaze video file
- Returns: Video path for dual-video mode
- Stores: In upload folder with 'gaze_' prefix

#### 4. `/api/generate-reports-from-import` (POST)
**Status:** ✅ Implemented
- Processes: Imported gaze data with current ROI definitions
- Creates: Session directory with timestamp
- Generates:
  - CSV with frame-by-frame gaze + ROI mapping
  - Heatmaps (jet colormap) per scene
  - Trajectories (saccades + fixations) per scene
  - Excel report with statistics
  - PDF report with all visualizations
- Returns: Session directory, report filenames, gaze points processed

### Frontend Integration (All Implemented)

#### 1. Mode Selection
**Status:** ✅ Implemented
- Mode selector overlay with two cards
- "Live Recording" and "Import & Analyze" options
- Back button to return to mode selection

#### 2. CSV Import Modal
**Status:** ✅ Implemented
- Step 1: CSV upload with column mapping
  - Auto-detects common column names
  - Manual dropdown mapping for frame_num, gaze_x, gaze_y
  - Real-time preview with statistics
- Step 2: Video upload
  - Original stimulus video (required)
  - Optional Tobii Ghost gaze video
- Step 3: Info note about dual-video offset

#### 3. Dual-Video Mode
**Status:** ✅ Implemented
- Toggle button in toolbar (appears when gaze video uploaded)
- Side-by-side layout:
  - Left: Stimulus video with ROI canvas
  - Right: Tobii Ghost gaze video
- Frame offset control panel:
  - -10, -1, +1, +10 frame buttons
  - Manual input field
  - Reset button
  - Real-time synchronization

#### 4. Report Generation
**Status:** ✅ Implemented
- "Generate Reports" button (import mode only)
- Progress modal with status
- Success message with report details
- Reports list refresh

### Testing Scenarios

#### Test 1: Basic Import (CSV + Video)
1. ✅ Select "Import & Analyze" mode
2. ✅ Upload CSV with any column names
3. ✅ Map columns using dropdowns
4. ✅ Preview shows correct statistics
5. ✅ Upload stimulus video
6. ✅ Click "Load & Analyze"
7. ✅ Video loads with single scene
8. ✅ Define ROIs
9. ✅ Click "Generate Reports"
10. ✅ Reports created successfully

#### Test 2: Dual-Video Mode
1. ✅ Upload CSV with gaze data
2. ✅ Upload stimulus video
3. ✅ Upload Tobii Ghost gaze video
4. ✅ Click "Load & Analyze"
5. ✅ Click "Dual Video" button
6. ✅ Both videos appear side-by-side
7. ✅ Test frame offset controls:
   - ✅ -10, -1, +1, +10 buttons work
   - ✅ Manual input updates in real-time
   - ✅ Reset button returns to 0
8. ✅ Play/pause syncs both videos
9. ✅ Seek/scrub syncs with offset applied

#### Test 3: Column Mapping Flexibility
1. ✅ CSV with exact names (frame_num, gaze_x, gaze_y) → Auto-detected
2. ✅ CSV with alternative names (frame, x, y) → Auto-detected
3. ✅ CSV with custom names (timestamp, x_coord, y_coord) → Manual mapping
4. ✅ CSV with extra columns → Ignored correctly
5. ✅ CSV with invalid rows → Skipped, count shown in preview

#### Test 4: Frame Offset Application
1. ✅ Import with offset = 0 → Default sync
2. ✅ Import with offset = +50 → Gaze ahead by 50 frames
3. ✅ Import with offset = -50 → Stimulus ahead by 50 frames
4. ✅ Adjust offset in dual-video mode → Updates in real-time
5. ✅ Generate reports → Offset reflected in tracking mode label

#### Test 5: Error Handling
1. ✅ Upload empty CSV → Error message
2. ✅ Upload CSV without numeric data → No preview, warning
3. ✅ Try to generate reports without ROIs → Confirmation dialog
4. ✅ Upload invalid video file → Error message
5. ✅ Generate reports without gaze data → Error message

### Performance Benchmarks

| Scenario | Data Size | Expected Time |
|----------|-----------|---------------|
| CSV parsing | 10k rows | < 1 second |
| CSV parsing | 100k rows | < 3 seconds |
| Video upload | 100 MB | < 10 seconds |
| Report generation | 10k gaze points, 5 ROIs | < 15 seconds |
| Heatmap generation | Per scene | < 2 seconds |
| Trajectory generation | Per scene | < 3 seconds |

### Known Limitations

1. **CSV Format:** Only supports numeric frame_num, gaze_x, gaze_y
2. **Video Sync:** Assumes constant FPS (no VFR support)
3. **Memory:** Large datasets (>500k points) may be slow
4. **Browser:** Chrome/Edge recommended for best performance
5. **File Size:** Large video files (>500MB) may timeout on upload

### Future Enhancements (Optional)

- [ ] Multi-file batch import
- [ ] Automatic offset detection using cross-correlation
- [ ] Support for timestamp-based synchronization
- [ ] Export annotated gaze video with ROI overlays
- [ ] Real-time gaze preview in dual-video mode
- [ ] Support for additional tracker formats (EyeLink, Pupil Labs)
- [ ] Cloud storage integration for large files

### Summary

**All Phase 3 components are implemented and functional:**
- ✅ Backend endpoints for gaze data import and report generation
- ✅ Frontend CSV column mapping with flexible parsing
- ✅ Dual-video mode with visual frame offset adjustment
- ✅ Complete report generation pipeline with all visualizations
- ✅ Error handling and validation throughout

**The import mode workflow is production-ready.**
