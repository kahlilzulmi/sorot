# Troubleshooting Guide

Complete troubleshooting reference for common issues and solutions.

---

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Application Launch Issues](#application-launch-issues)
3. [Detection Module Issues](#detection-module-issues)
4. [Game Module Issues](#game-module-issues)
5. [Stimulus Generation Issues](#stimulus-generation-issues)
6. [Database Issues](#database-issues)
7. [Performance Issues](#performance-issues)
8. [OBS Integration Issues](#obs-integration-issues)
9. [Logging and Diagnostics](#logging-and-diagnostics)

---

## Installation Issues

### Python Not Found

**Symptom**: `'python' is not recognized as an internal or external command`

**Solution**:
1. Install Python 3.10+ from python.org
2. During installation, check "Add Python to PATH"
3. Restart terminal
4. Verify: `python --version`

**Alternative**:
```powershell
# Use full path to Python
C:\Users\YourName\AppData\Local\Programs\Python\Python310\python.exe
```

### Pip Install Fails

**Symptom**: `ERROR: Could not install packages due to an OSError`

**Solutions**:

**A. Permission Error**
```powershell
# Run as administrator or use --user flag
pip install --user -r requirements.txt
```

**B. Network Error**
```powershell
# Use different mirror
pip install -r requirements.txt --index-url https://pypi.org/simple/

# Or retry with timeout
pip install -r requirements.txt --timeout=300
```

**C. Disk Space**
```powershell
# Check available space
Get-PSDrive C

# Clean pip cache
pip cache purge
```

### Module Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'cv2'`

**Solution**:
```powershell
# Verify virtual environment is activated
# (Should see (.venv) in prompt)
.\.venv\Scripts\Activate.ps1

# Reinstall specific package
pip install opencv-python

# Verify installation
python -c "import cv2; print(cv2.__version__)"
```

### Tkinter Not Available

**Symptom**: `ImportError: No module named 'tkinter'`

**Solution**:
- Tkinter comes with Python standard library
- Reinstall Python with "tcl/tk and IDLE" option checked
- Verify: `python -m tkinter`

---

## Application Launch Issues

### Application Won't Start

**Symptom**: Double-click exe does nothing

**Diagnostic Steps**:
1. Run from command line to see errors:
   ```powershell
   cd dist\EyeTracker
   .\EyeTracker.exe
   ```

2. Check antivirus logs
3. Run as administrator

**Solutions**:

**A. Antivirus Blocking**
- Add `EyeTracker.exe` to antivirus exceptions
- Temporarily disable antivirus and test

**B. Missing DLLs**
- Install Visual C++ Redistributables:
  https://support.microsoft.com/en-us/help/2977003

**C. Corrupted Installation**
- Delete and re-extract from ZIP
- Rebuild from source

### System Check Fails

**Symptom**: "System check failed" on first run

**Check Each Component**:

```python
# Test Python version
import sys
print(f"Python: {sys.version}")

# Test OpenCV
import cv2
print(f"OpenCV: {cv2.__version__}")

# Test camera
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
print(f"Camera: {'OK' if ret else 'FAIL'}")
cap.release()

# Test Pygame
import pygame
pygame.init()
print(f"Pygame: {pygame.version.ver}")
```

**Solutions**:
- Update drivers (camera, graphics)
- Reinstall dependencies
- Check camera permissions in Windows Settings

### Configuration Errors

**Symptom**: `KeyError` or `FileNotFoundError` on startup

**Solution**:
```powershell
# Delete corrupted config
Remove-Item config.json

# Application will recreate default on next run
python eye_tracker.py

# Or manually reset
python -c "from utils.config_manager import reset_to_defaults; reset_to_defaults('config.json')"
```

---

## Detection Module Issues

### Video Won't Load

**Symptom**: "Failed to load video" error

**Checks**:
1. **File exists**: Verify path is correct
2. **Format supported**: Use MP4, AVI, MKV, MOV
3. **Codec**: H.264 recommended
4. **File not corrupted**: Try playing in VLC

**Solution**:
```python
# Test video manually
import cv2
cap = cv2.VideoCapture("path/to/video.mp4")
print(f"Opened: {cap.isOpened()}")
print(f"Frames: {int(cap.get(cv2.CAP_PROP_FRAME_COUNT))}")
print(f"FPS: {cap.get(cv2.CAP_PROP_FPS)}")
cap.release()
```

**Convert if needed**:
```bash
ffmpeg -i input.avi -c:v libx264 -c:a aac output.mp4
```

### No Pupils Detected

**Symptom**: Success rate is 0% or very low

**Solutions**:

**A. Try Different Method**
- CHT: Best for clear, high-contrast pupils
- Blob: Good for noisy images
- Contour: Robust to lighting
- Threshold: Fast but simple
- Dlib: Most accurate with faces

**B. Adjust Parameters**:
```python
# Hough Transform
- Increase param2 (accumulator) for fewer false positives
- Decrease param2 for more detections
- Adjust radius range to match actual pupil size

# Blob Detection
- Increase min_area to filter noise
- Decrease max_area if detecting too large

# Contour
- Adjust threshold (lower for darker pupils)
```

**C. Improve Input**:
- Use higher resolution video
- Ensure good lighting
- Position eye closer to camera
- Remove reflections/glare

### Processing is Slow

**Symptom**: Detection takes very long

**Solutions**:

**A. Change Processing Mode**:
```json
// In Settings → Detection → Processing Mode
"processing_mode": "chunk"  // Instead of "full"
"chunk_size_frames": 500    // Reduce if out of memory
```

**B. Use Faster Method**:
- Threshold detection is fastest
- CHT is faster than Dlib

**C. Reduce Video Size**:
```bash
# Downscale video
ffmpeg -i input.mp4 -vf scale=640:480 output.mp4
```

### Memory Errors

**Symptom**: `MemoryError` or application crashes

**Solutions**:

**A. Enable Chunked Processing**:
```json
"processing_mode": "chunk",
"chunk_size_frames": 500  // Lower if still failing
```

**B. Close Other Applications**:
- Free up RAM
- Close browser tabs
- Close other video applications

**C. Upgrade System**:
- 8GB RAM minimum
- 16GB recommended for large videos

---

## Game Module Issues

### Camera Not Detected

**Symptom**: "No camera found" or black screen

**Solutions**:

**A. Check Camera Connection**:
```python
import cv2

# Try different camera IDs
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera {i}: Available")
        cap.release()
    else:
        print(f"Camera {i}: Not available")
```

**B. Update Camera ID in Settings**:
- Go to Settings → Game → Camera ID
- Try values 0, 1, 2 until camera works

**C. Check Permissions**:
- Windows Settings → Privacy → Camera
- Ensure "Allow apps to access your camera" is ON

**D. Update Drivers**:
- Device Manager → Cameras
- Right-click camera → Update driver

### Poor Eye Detection

**Symptom**: Cursor jumps around, doesn't follow gaze

**Solutions**:

**A. Improve Lighting**:
- Face towards light source
- Avoid backlighting
- Remove glare from glasses

**B. Adjust Kalman Filter**:
```json
// Settings → Detection
"kalman_process_noise": 0.1,    // Lower = smoother (0.01-1.0)
"kalman_measurement_noise": 2.0  // Lower = more responsive (0.1-10.0)
```

**C. Camera Position**:
- Position camera at eye level
- Distance: 40-60 cm from face
- Ensure face is fully visible

### Buttons Not Responding

**Symptom**: Looking at button doesn't select it

**Solutions**:

**A. Adjust Dwell Time**:
```json
// Settings → Game
"dwell_time_seconds": 1.5  // Reduce from 2.0 for faster response
```

**B. Check Gaze Detection**:
- Watch debug overlay (if enabled)
- Ensure gaze point moves when eyes move

**C. Calibration**:
- Restart game
- Complete calibration carefully
- Look directly at calibration points

---

## Stimulus Generation Issues

### Generation Fails

**Symptom**: "Failed to generate video" error

**Check Logs**:
```powershell
Get-Content Logs\eye_tracker_*.log | Select-String "stimulus"
```

**Solutions**:

**A. Disk Space**:
```powershell
# Check free space
Get-PSDrive C

# Large videos need 1-5 GB depending on settings
```

**B. Codec Issues**:
```python
# Verify OpenCV video writer
import cv2
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('test.mp4', fourcc, 30, (1920, 1080))
print(f"Writer opened: {out.isOpened()}")
out.release()
```

**C. Permissions**:
- Ensure write permissions for Sessions folder
- Run as administrator

### Video Quality Issues

**Symptom**: Blurry or pixelated output

**Solutions**:

**A. Increase Resolution**:
- Settings → Stimulus → Resolution
- Use 1080p or higher

**B. Increase FPS**:
- Settings → Stimulus → FPS
- Use 60 FPS for smooth motion

**C. Adjust Encoding**:
```python
# In stimulus_generator.py, modify:
fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264
# or
fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Alternative codec
```

---

## Database Issues

### Cannot Save Sessions

**Symptom**: "Database error" when saving

**Solutions**:

**A. Check Permissions**:
```powershell
# Ensure Database folder is writable
Test-Path -Path "Database" -IsValid
```

**B. Delete Corrupted Database**:
```powershell
# Backup first!
Copy-Item Database\*.db Database\backup\

# Delete corrupted DB (will be recreated)
Remove-Item Database\detection_sessions.db
```

**C. Check Disk Space**:
```powershell
Get-PSDrive C
```

### Search Not Working

**Symptom**: No results even though sessions exist

**Solutions**:

**A. Check Filters**:
- Clear all filters and try again
- Ensure date range is correct

**B. Rebuild Database Index**:
```python
from modules.database_manager import rebuild_index
rebuild_index("detection")
```

### Export Fails

**Symptom**: Cannot export to CSV/Excel

**Solutions**:

**A. Close Excel**:
- If file is open in Excel, close it first

**B. Check Permissions**:
- Ensure destination folder is writable

**C. Install openpyxl**:
```powershell
pip install openpyxl
```

---

## Performance Issues

### Application is Slow

**General Performance Tips**:

**A. Close Unnecessary Applications**:
- Free up CPU and RAM
- Close browser, other video apps

**B. Update Graphics Drivers**:
- Visit GPU manufacturer website
- Download latest drivers

**C. Reduce Visual Effects**:
```json
// Settings → UI Preferences
"theme": "light",  // Dark theme may be slower on some systems
```

**D. Disable Adaptive Settings**:
```json
// Settings → Game
"adaptive_params": false
```

### High Memory Usage

**Symptom**: Application uses >1GB RAM

**Solutions**:

**A. Reduce Chunk Size**:
```json
"chunk_size_frames": 500  // Instead of 1000
```

**B. Close Matplotlib Figures**:
```python
import matplotlib.pyplot as plt
# After creating plot
plt.savefig("plot.png")
plt.close()  # Important!
```

**C. Clear Cache**:
```python
# In detection wizard, add:
cv2.destroyAllWindows()
gc.collect()
```

### Video Playback Stutters

**Symptom**: Choppy playback in preview

**Solutions**:

**A. Reduce Preview Resolution**:
- Don't use full resolution for preview
- Scale down to 640x480

**B. Skip Frames**:
```python
# Read every Nth frame for preview
frame_skip = 2
cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num * frame_skip)
```

---

## OBS Integration Issues

### OBS Not Detected

**Symptom**: Wizard can't find OBS installation

**Solutions**:

**A. Install OBS Studio**:
- Download from obsproject.com
- Install in default location

**B. Manual Path**:
- Note where OBS is installed
- Provide path manually in wizard

**C. Check Registry**:
```powershell
# Verify registry entry
Get-ItemProperty -Path "HKLM:\SOFTWARE\OBS Studio" -Name "(default)" -ErrorAction SilentlyContinue
```

### OBS Won't Start

**Symptom**: OBS doesn't launch from application

**Solutions**:

**A. Launch Manually First**:
- Start OBS once manually
- Complete initial setup
- Close OBS
- Try from application again

**B. Check Path**:
```powershell
# Verify executable exists
Test-Path "C:\Program Files\obs-studio\bin\64bit\obs64.exe"
```

**C. Permissions**:
- Run application as administrator

---

## Logging and Diagnostics

### Enable Verbose Logging

```python
# Add to eye_tracker.py
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Check Log Files

```powershell
# View latest log
Get-Content Logs\eye_tracker_*.log -Tail 100

# Monitor real-time
Get-Content Logs\eye_tracker_*.log -Wait

# Search for errors
Get-Content Logs\*.log | Select-String "ERROR"

# Search for specific module
Get-Content Logs\*.log | Select-String "detection"
```

### Diagnostic Commands

```python
# Test all imports
python -c "from eye_tracker import *; print('✓ All imports OK')"

# Test detection
python -c "from modules.detect_gemini8 import *; print('✓ Detection OK')"

# Test database
python -c "from modules.database_manager import *; print('✓ Database OK')"

# Test visualization
python -c "from modules.visualization import *; print('✓ Visualization OK')"
```

### System Information

```python
# Get system info for bug reports
import platform
import sys
import cv2
import pygame

print(f"OS: {platform.system()} {platform.release()}")
print(f"Python: {sys.version}")
print(f"OpenCV: {cv2.__version__}")
print(f"Pygame: {pygame.version.ver}")
```

---

## Getting Additional Help

### Before Reporting Issues

1. **Check logs** in `Logs/` folder
2. **Try solutions** from this guide
3. **Test on different machine** (if possible)
4. **Collect system information**

### Bug Report Template

```
**Environment:**
- OS: Windows 10/11 (64-bit)
- Python version: 3.10.x
- Application version: 1.0.0

**Issue:**
Brief description of the problem

**Steps to Reproduce:**
1. Step one
2. Step two
3. ...

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Error Messages:**
Copy any error messages or stack traces

**Logs:**
Attach relevant log files from Logs/ folder

**Screenshots:**
If applicable, add screenshots
```

### Contact Information

**Author**: Kahlil Gibran Al Zulmi  
**Institution**: Institut Teknologi Sepuluh Nopember  
**Program**: Medical Technology Study Program

**Advisors**:
- Prof. Dr. Ir. Adhi Dharma Wibawa, S.T., M.T.
- dr. Zain Budi Syulthoni, Sp.KJ.

---

## Frequently Asked Questions

**Q: Can I use this on Mac or Linux?**  
A: Currently Windows-only due to pywin32 dependency. Linux port is possible with modifications.

**Q: Do I need internet connection?**  
A: No, application works completely offline after installation.

**Q: Can I use external eye tracker hardware?**  
A: Game module uses webcam only. Detection module can analyze videos from any source.

**Q: What video formats are supported?**  
A: MP4 (H.264), AVI, MKV, MOV. MP4 recommended.

**Q: Can I add my own questions to the game?**  
A: Yes! Edit the question bank Excel file referenced in Settings.

**Q: Is my data stored securely?**  
A: All data is stored locally in SQLite databases. No cloud upload.

**Q: Can I change the application language?**  
A: Yes, Settings → UI Preferences → Language (English/Indonesian).

**Q: How do I uninstall?**  
A: Delete the application folder. No registry entries are created.

---

**Last Updated**: November 2025
