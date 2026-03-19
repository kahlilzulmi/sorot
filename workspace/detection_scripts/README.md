# Detection Scripts

Collection of eye/pupil detection algorithms for post-processing eye tracking videos.

## Installation

```bash
pip install -r ../../requirements_workspace.txt
```

## Available Algorithms

### Basic Detection
- `detect_blob.py` - Blob detection algorithm
- `detect_color.py` - Color-based detection
- `detect_color_contour.py` - Color + contour detection
- `detect_contour.py` - Contour-based detection

### Advanced Detection
- `detect_houghcircletransform.py` - Hough circle transform
- `detect_houghcircletransform_kalman.py` - Hough + Kalman filter (v1)
- `detect_houghcircletransform_kalman2.py` - Hough + Kalman filter (v2)

## Usage
Each script can be run independently to process eye tracking videos and output gaze coordinates.
