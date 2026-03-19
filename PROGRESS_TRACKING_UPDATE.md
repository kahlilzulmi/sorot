# Progress Tracking & Heatmap Position Fix - Implementation Notes

## Changes Made (February 20, 2026)

### 1. ✅ Fixed Heatmap Positioning Issue

**Problem**: Heatmaps showed gaze positions in incorrect locations due to coordinate transformation between low-resolution heatmap and video resolution.

**Solution**: Modified `generate_heatmaps_from_data()` to use the same approach as trajectory generation:
- No longer scales to `HEATMAP_RESOLUTION` (192x108) and back
- Uses full video resolution (e.g., 1920x1080) directly
- Applies coordinates at actual pixel positions like trajectory visualization
- Same normalization and visualization approach

**Code Changes**:
```python
# OLD: Scaled to low resolution then back
heatmap = np.zeros(HEATMAP_RESOLUTION, dtype=np.float32)  # 192x108
# ... scaling math ...
heatmap_resized = cv2.resize(heatmap, (video_width, video_height))

# NEW: Use full resolution directly (like trajectory)
heatmap = np.zeros((video_height, video_width), dtype=np.float32)  # 1920x1080
px = int(round(gaze_x))
py = int(round(gaze_y))
heatmap[py, px] += 1
```

**Expected Result**: Heatmap hotspots now align with trajectory fixation points and ROI boundaries.

---

### 2. ✅ Improved Progress Tracking & UI Integration

**Problem**: UI showed "processing failed" even though backend continued processing successfully. No detailed status feedback.

**Solution**: Enhanced progress tracking with:
- Granular progress updates (10%, 20%, 50%, 65%, 80%, 90%, 100%)
- Status messages for each processing stage
- File verification after completion
- Better error handling and reporting

**New API Endpoints**:

#### `/api/processing/progress` (Enhanced)
Now returns:
```json
{
  "progress": 65,
  "status": "Generating gaze trajectories...",
  "is_processing": true,
  "complete": false,
  "error": false,
  "files": {
    "excel": "report_Participant.xlsx",
    "pdf": "report_Participant.pdf",
    "heatmaps": ["heatmap_Scene_1.png", "heatmap_Scene_2.png"],
    "trajectories": ["trajectory_Scene_1.png", "trajectory_Scene_2.png"]
  },
  "session_dir": "/path/to/session"
}
```

#### `/api/processing/verify-completion` (New)
Verifies files exist after processing:
```json
{
  "complete": true,
  "files_found": {
    "excel": "report_Participant.xlsx",
    "pdf": "report_Participant.pdf",
    "gaze_csv": "gaze_data_processed.csv",
    "heatmaps": ["heatmap_Scene_1.png", ...],
    "trajectories": ["trajectory_Scene_1.png", ...]
  },
  "session_dir": "/path/to/session",
  "total_files": 12
}
```

#### `/api/reports/list` (Enhanced)
Now includes detailed file metadata:
```json
{
  "reports": [
    {
      "filename": "report_Participant.xlsx",
      "size": 45678,
      "size_mb": 0.04,
      "modified": "2026-02-20T14:30:45",
      "type": "xlsx"
    }
  ],
  "session_dir": "/path/to/session",
  "total_files": 8
}
```

---

## Frontend Integration Guide

### Recommended Progress Polling Pattern

```javascript
// Start processing
async function startProcessing() {
    const response = await fetch('/api/processing/start-post-processing', {
        method: 'POST'
    });
    
    if (response.ok) {
        // Start polling for progress
        pollProgress();
    }
}

// Poll progress with timeout protection
let pollCount = 0;
const MAX_POLLS = 600; // 10 minutes at 1 poll/second
let processingComplete = false;

async function pollProgress() {
    if (pollCount >= MAX_POLLS || processingComplete) {
        console.log('Polling stopped');
        return;
    }
    
    try {
        const response = await fetch('/api/processing/progress');
        const data = await response.json();
        
        // Update UI with progress and status
        updateProgressBar(data.progress);
        updateStatusText(data.status);
        
        // Check completion
        if (data.complete && data.progress === 100) {
            // Verify files actually exist
            await verifyCompletion();
            processingComplete = true;
            return;
        }
        
        // Check for errors
        if (data.error || data.progress < 0) {
            showError(`Processing failed: ${data.status}`);
            processingComplete = true;
            return;
        }
        
        // Continue polling if still processing
        if (data.is_processing || data.progress < 100) {
            pollCount++;
            setTimeout(pollProgress, 1000); // Poll every 1 second
        }
        
    } catch (error) {
        console.error('Error polling progress:', error);
        setTimeout(pollProgress, 2000); // Retry after 2 seconds
    }
}

// Verify completion and list files
async function verifyCompletion() {
    try {
        const response = await fetch('/api/processing/verify-completion');
        const data = await response.json();
        
        if (data.complete) {
            console.log('Processing verified complete!');
            console.log('Files found:', data.files_found);
            
            // List all reports
            const reportsResponse = await fetch('/api/reports/list');
            const reports = await reportsResponse.json();
            
            displayResults(reports);
        } else {
            console.warn('Processing marked complete but files missing');
            showWarning('Some output files may be missing');
        }
        
    } catch (error) {
        console.error('Error verifying completion:', error);
    }
}

// Update UI elements
function updateProgressBar(percent) {
    const progressBar = document.getElementById('progress-bar');
    progressBar.style.width = percent + '%';
    progressBar.textContent = Math.round(percent) + '%';
}

function updateStatusText(status) {
    const statusText = document.getElementById('status-text');
    statusText.textContent = status;
}

function displayResults(reports) {
    const resultsDiv = document.getElementById('results');
    
    let html = '<h3>Processing Complete!</h3>';
    html += '<p>Session: ' + reports.session_dir + '</p>';
    html += '<ul>';
    
    reports.reports.forEach(file => {
        html += `<li>
            <a href="/api/reports/download/${file.filename}" download>
                ${file.filename}
            </a> 
            (${file.size_mb} MB)
        </li>`;
    });
    
    html += '</ul>';
    resultsDiv.innerHTML = html;
}
```

---

## Testing the Fixes

### Test Heatmap Positioning

1. **Process a recording** with clear ROI interactions
2. **Compare outputs**:
   - Open `trajectory_Scene_X.png` - note where fixation points (red circles) are
   - Open `heatmap_Scene_X.png` - heatmap hotspots should align with fixation locations
   - Both should align with ROI boundaries

3. **Console Output**:
```
✓ Heatmap saved: heatmap_Scene_1.png (245678 bytes, 342 gaze points)
✓ Trajectory saved: trajectory_Scene_1.png (198234 bytes)
```

### Test Progress Tracking

1. **Start a processing session**
2. **Monitor console output**:
```
================================================================================
Starting Post-Processing Pipeline...
================================================================================

Generating heatmaps...
✓ Heatmap saved: heatmap_Scene_1.png (245678 bytes, 342 gaze points)
✓ Heatmap saved: heatmap_Scene_2.png (198234 bytes, 287 gaze points)

Generating gaze trajectories...
✓ Trajectory saved: trajectory_Scene_1.png (198234 bytes)
✓ Trajectory saved: trajectory_Scene_2.png (165432 bytes)

Generating reports...

================================================================================
Post-Processing Complete!
Excel Report: /path/to/report_Participant.xlsx
PDF Report: /path/to/report_Participant.pdf
Heatmaps: 2
Trajectories: 2
================================================================================
```

3. **Check progress endpoint** at intervals:
```bash
curl http://localhost:5000/api/processing/progress
```

4. **Verify completion**:
```bash
curl http://localhost:5000/api/processing/verify-completion
```

---

## Troubleshooting

### "Heatmap still not aligned"

**Check these:**
1. Gaze data coordinate system - should match video resolution
2. OBS recording resolution vs ad video resolution
3. Aspect ratio differences (see `gaze_post_processor.py` coordinate mapping)

**Debug steps:**
```python
# Add to generate_heatmaps_from_data after the loop
print(f"Video size: {video_width}x{video_height}")
print(f"Gaze points in scene: {len(valid_gaze)}")
print(f"Sample gaze coords: {valid_gaze[['gaze_x', 'gaze_y']].head()}")
print(f"Heatmap max value: {heatmap.max()}")
```

### "UI still shows failure"

**Check frontend polling:**
1. Open browser DevTools → Network tab
2. Verify `/api/processing/progress` is being called every 1-2 seconds
3. Check response data shows increasing progress
4. Verify `is_processing` becomes `false` when `progress` reaches 100

**Backend status:**
```bash
# Check processing thread status
# In Python console or add to progress endpoint:
print(f"Thread alive: {state.processing_thread.is_alive()}")
print(f"Progress: {state.processing_progress}")
print(f"Status: {state.processing_status}")
```

---

## Summary of Improvements

✅ **Heatmap Positioning**: Now matches trajectory coordinates exactly  
✅ **Progress Tracking**: Granular updates with clear status messages  
✅ **File Verification**: Dedicated endpoint to verify completion  
✅ **Error Handling**: Better error messages and recovery  
✅ **UI Integration**: Complete polling pattern with timeout protection  

## Next Steps

1. Update frontend HTML/JavaScript to use new polling pattern
2. Add UI elements for status messages and file listing
3. Test with various video resolutions and aspect ratios
4. Consider adding calibration workflow for even better accuracy
