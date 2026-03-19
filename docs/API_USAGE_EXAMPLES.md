# ROI Processing API Usage Examples

## Endpoint: `/api/process_roi`

**Method:** POST  
**Content-Type:** application/json

This endpoint processes ROI regions from video frames and returns statistical analysis including:
- Mean pixel intensity (RGB + Grayscale) for each ROI per frame
- Gaze hit counts if gaze data is provided
- Aggregated summary statistics per ROI

---

## Request Payload

```json
{
    "video_path": "path/to/video.mp4",
    "rois": [
        {
            "x": 100,
            "y": 100,
            "width": 200,
            "height": 150,
            "label": "Product Logo"
        },
        {
            "x": 400,
            "y": 200,
            "width": 300,
            "height": 200,
            "label": "Brand Name"
        }
    ],
    "gaze_data": [
        {"frame": 0, "x": 250, "y": 200},
        {"frame": 1, "x": 255, "y": 205}
    ],
    "start_frame": 0,
    "end_frame": 100,
    "analysis_type": "both"
}
```

### Required Fields
- **video_path** (string): Absolute or relative path to video file
- **rois** (array): List of ROI objects with x, y, width, height, label

### Optional Fields
- **gaze_data** (array): Gaze coordinates per frame. Default: []
- **start_frame** (integer): Starting frame number. Default: 0
- **end_frame** (integer|null): Ending frame number. Default: null (all frames)
- **analysis_type** (string): "intensity", "gaze_hits", or "both". Default: "both"

---

## Response Format

```json
{
    "success": true,
    "summary": {
        "total_frames_processed": 101,
        "start_frame": 0,
        "end_frame": 100,
        "fps": 30.0,
        "roi_summaries": [
            {
                "label": "Product Logo",
                "total_gaze_hits": 45,
                "avg_intensity": {
                    "r": 128.45,
                    "g": 132.89,
                    "b": 125.67,
                    "gray": 129.34,
                    "avg": 129.00
                }
            }
        ]
    },
    "frames": [
        {
            "frame": 0,
            "timestamp": 0.0,
            "rois": [
                {
                    "label": "Product Logo",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 150,
                    "mean_intensity": {
                        "r": 130.25,
                        "g": 135.42,
                        "b": 128.91,
                        "gray": 131.53,
                        "avg": 131.53
                    },
                    "gaze_hits": 1,
                    "gaze_total": 1
                }
            ]
        }
    ]
}
```

---

## Usage Examples

### 1. Python (requests)

```python
import requests
import json

# Prepare request data
payload = {
    "video_path": "uploaded_videos/advertisement_v2.mp4",
    "rois": [
        {"x": 100, "y": 100, "width": 200, "height": 150, "label": "Logo"},
        {"x": 400, "y": 200, "width": 300, "height": 200, "label": "Product"}
    ],
    "gaze_data": [
        {"frame": 0, "x": 150, "y": 175},
        {"frame": 1, "x": 155, "y": 180}
    ],
    "start_frame": 0,
    "end_frame": 100,
    "analysis_type": "both"
}

# Send request
response = requests.post(
    'http://localhost:5000/api/process_roi',
    json=payload,
    headers={'Content-Type': 'application/json'}
)

# Process response
if response.status_code == 200:
    result = response.json()
    print(f"Processed {result['summary']['total_frames_processed']} frames")
    
    # Print ROI summaries
    for roi_summary in result['summary']['roi_summaries']:
        print(f"\nROI: {roi_summary['label']}")
        print(f"  Total gaze hits: {roi_summary['total_gaze_hits']}")
        print(f"  Avg intensity: {roi_summary['avg_intensity']['avg']:.2f}")
    
    # Access per-frame data
    for frame_data in result['frames'][:5]:  # First 5 frames
        print(f"\nFrame {frame_data['frame']} @ {frame_data['timestamp']:.2f}s")
        for roi in frame_data['rois']:
            print(f"  {roi['label']}: intensity={roi['mean_intensity']['avg']:.2f}")
else:
    print(f"Error: {response.json()['error']}")
```

### 2. JavaScript (Vue.js App - Already integrated)

```javascript
// Inside Vue component method
async analyzeCurrentScene() {
    if (!this.currentScene || !this.videoInfo) {
        alert('No scene or video loaded');
        return;
    }
    
    try {
        const result = await this.analyzeROIFromVideo(
            this.videoInfo.filename,
            this.currentScene.rois,
            this.importedGazeData,
            {
                start_frame: this.currentScene.start_frame,
                end_frame: this.currentScene.end_frame,
                analysis_type: 'both'
            }
        );
        
        console.log('Analysis complete!', result.summary);
        
        // Display results
        alert(`Analysis complete!\n\nProcessed ${result.summary.total_frames_processed} frames\n` +
              `ROIs analyzed: ${result.summary.roi_summaries.length}`);
        
    } catch (error) {
        console.error('Analysis failed:', error);
    }
}
```

### 3. cURL (Command Line)

```bash
curl -X POST http://localhost:5000/api/process_roi \
  -H "Content-Type: application/json" \
  -d '{
    "video_path": "uploaded_videos/ad_campaign.mp4",
    "rois": [
      {"x": 100, "y": 100, "width": 200, "height": 150, "label": "Logo"},
      {"x": 400, "y": 200, "width": 300, "height": 200, "label": "CTA Button"}
    ],
    "start_frame": 0,
    "end_frame": 50,
    "analysis_type": "intensity"
  }' | jq '.'
```

### 4. Pandas DataFrame Processing

```python
import pandas as pd

# Get results from API
result = requests.post('http://localhost:5000/api/process_roi', json=payload).json()

# Convert to DataFrame for analysis
frames_data = []
for frame in result['frames']:
    for roi in frame['rois']:
        frames_data.append({
            'frame': frame['frame'],
            'timestamp': frame['timestamp'],
            'roi_label': roi['label'],
            'intensity_r': roi['mean_intensity']['r'],
            'intensity_g': roi['mean_intensity']['g'],
            'intensity_b': roi['mean_intensity']['b'],
            'intensity_gray': roi['mean_intensity']['gray'],
            'gaze_hits': roi.get('gaze_hits', 0)
        })

df = pd.DataFrame(frames_data)

# Analysis examples
print(df.groupby('roi_label')['gaze_hits'].sum())
print(df.groupby('roi_label')['intensity_gray'].mean())

# Save to CSV
df.to_csv('roi_frame_analysis.csv', index=False)
```

---

## Performance Notes

- Processing speed depends on video resolution and number of ROIs
- For large videos, consider processing in chunks using `start_frame` and `end_frame`
- Typical processing speed: ~30-60 FPS for 1080p video with 5 ROIs
- Memory usage scales with frame count and ROI count

---

## Error Handling

Common error responses:

```json
// Missing required fields
{
    "error": "Missing required fields: video_path and rois"
}

// Video not found
{
    "error": "Video file not found: path/to/video.mp4"
}

// Invalid ROI format
{
    "error": "Each ROI must have: ['x', 'y', 'width', 'height', 'label']"
}

// Invalid frame range
{
    "error": "Invalid frame range"
}
```

---

## Use Cases

1. **Advertisement Analysis**: Measure visual attention to brand elements
2. **UI/UX Testing**: Track gaze interaction with interface components
3. **Video Quality Assessment**: Monitor brightness/contrast changes per region
4. **A/B Testing**: Compare pixel intensity differences between video variants
5. **Scene Change Detection**: Track ROI intensity variations over time
6. **Eye Tracking Validation**: Verify gaze data accuracy within defined regions

---

## Integration Tips

1. **Batch Processing**: Process multiple videos sequentially
2. **Real-time Analysis**: Use small frame ranges for near real-time feedback
3. **Data Export**: Convert results to CSV/Excel for further analysis
4. **Visualization**: Use matplotlib/plotly to graph intensity trends
5. **Caching**: Store results to avoid reprocessing unchanged videos
