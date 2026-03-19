# 📦 Building Portable Executable Guide

## For You (Developer)

### Prerequisites
```bash
cd roi_web_app
pip install pyinstaller
```

### Quick Build (Recommended)
Simply run:
```bash
BUILD_SIMPLE.bat
```

This will:
1. ✅ Install PyInstaller (if needed)
2. ✅ Build single executable
3. ✅ Create `dist\AdEyeTracker.exe` (~150-250MB)

### Build Time
- First build: 5-10 minutes
- Subsequent builds: 2-5 minutes

### What Gets Packaged
- ✅ Flask web server
- ✅ All Python dependencies (OpenCV, NumPy, Pandas, etc.)
- ✅ Post-processing engine
- ✅ Report generator
- ✅ Templates and static files
- ✅ Custom modules

### Testing the Executable
```bash
cd dist
AdEyeTracker.exe
```

Browser should auto-open at `http://localhost:5000`

---

## For Your Professor (Distribution)

### What to Give Them

**Package Contents:**
```
📁 AdEyeTracker_Package/
   ├── AdEyeTracker.exe          (Main application - ~200MB)
   └── README.md                 (Copy DISTRIBUTION_README.md here)
```

### Simple Instructions for Professor

**Just 2 Steps:**

1. **Install OBS Studio** (one-time)
   - Download: https://obsproject.com/
   - Follow setup in README.md

2. **Run AdEyeTracker.exe**
   - Double-click
   - Browser opens automatically
   - Start analyzing!

### Distribution Methods

**Option A: USB Drive**
- Copy both files to USB
- Professor copies to their computer
- Run directly

**Option B: Cloud (Google Drive/OneDrive)**
- Upload the 2 files
- Share link
- Professor downloads and runs

**Option C: Network Share**
- Place on shared network drive
- Can run directly from network (slower)

---

## Troubleshooting Build Issues

### Issue: "ModuleNotFoundError"
**Solution:**
```bash
pip install --upgrade -r requirements.txt
pip install pyinstaller
```

### Issue: "Unable to find templates"
**Solution:**
Make sure `templates/` folder exists before building

### Issue: Build fails with OpenCV
**Solution:**
```bash
pip uninstall opencv-python opencv-contrib-python
pip install opencv-python-headless
```

### Issue: Executable is too large (>500MB)
**Solution:**
This is normal. The executable includes:
- Python runtime (~50MB)
- OpenCV + dependencies (~100MB)
- NumPy, Pandas, Matplotlib (~50MB)
- Flask and other packages (~50MB)

### Issue: Antivirus blocks executable
**Solution:**
- Add exception in Windows Defender
- Or: Code sign the executable (requires certificate)

---

## Advanced: Reducing Executable Size

If you need smaller size, edit `AdEyeTracker.spec`:

```python
# Exclude heavy packages you don't need
excludes=[
    'tkinter',  # GUI toolkit (not used)
    'tcl', 'tk',
    'PyQt5', 'PyQt6',  # Other GUI frameworks
    'PySide2', 'PySide6',
    'IPython',  # Interactive Python
    'jupyter',  # Notebook
],
```

Then rebuild:
```bash
pyinstaller --clean --noconfirm AdEyeTracker.spec
```

---

## Version Control

When distributing to professor:

### Version 1.0 (Initial)
- Basic functionality
- OBS integration
- Report generation

### Version 2.0 (Current - Post-Processing)
- Post-processing architecture
- Multi-participant support
- Professional reports

### Version Info in Exe
The exe will display version on startup screen.

---

## Security Notes

### Safe to Distribute
- ✅ No sensitive data embedded
- ✅ No hardcoded credentials
- ✅ Runs locally (no internet required except YouTube download)
- ✅ No telemetry or tracking

### Data Privacy
- All data stays on local machine
- Sessions saved in `sessions/` folder
- No cloud upload

---

## Platform Support

### Currently Supported
- ✅ Windows 10 (64-bit)
- ✅ Windows 11 (64-bit)

### Not Supported
- ❌ Windows 7/8 (Python 3.9+ requirement)
- ❌ 32-bit Windows
- ❌ macOS (different build required)
- ❌ Linux (different build required)

To build for macOS/Linux:
```bash
# On Mac/Linux:
pyinstaller --clean --noconfirm AdEyeTracker.spec
```

---

## Maintenance

### Updating the Application

If you make changes to the code:

1. Test changes in development:
   ```bash
   python video_roi_webapp.py
   ```

2. Rebuild executable:
   ```bash
   BUILD_SIMPLE.bat
   ```

3. Redistribute updated exe to professor

### Version Numbering
Update version in `app_launcher.py`:
```python
VERSION = "2.1"  # Update this
```

---

## Uninstallation

For the professor:
- Simply delete `AdEyeTracker.exe`
- Optionally delete generated folders:
  - `sessions/`
  - `uploaded_videos/`
  - `downloaded_videos/`
  - `projects/`

No registry entries or system changes made.

---

## Support Checklist

Before giving to professor, verify:

- [ ] Executable builds without errors
- [ ] Executable runs on your machine
- [ ] Browser opens automatically
- [ ] Can upload/download videos
- [ ] Can define ROIs
- [ ] Can start/stop recording
- [ ] OBS integration works
- [ ] Post-processing completes
- [ ] Reports generate (Excel + PDF)
- [ ] README is clear and complete

---

## Quick Commands Reference

```bash
# Build executable
BUILD_SIMPLE.bat

# Test build
cd dist
AdEyeTracker.exe

# Clean build
rmdir /s /q build dist
BUILD_SIMPLE.bat

# Check dependencies
pip list

# Update all packages
pip install --upgrade -r requirements.txt
```

---

## File Sizes (Approximate)

- Source code: ~50KB
- Built executable: ~200MB
- With all dependencies: ~250MB
- After compression (ZIP): ~80MB

**Tip**: Distribute as ZIP file to reduce download size.

---

## Success Criteria

✅ Professor can:
1. Download/receive the exe
2. Double-click to run
3. Use all features without errors
4. Generate professional reports
5. Use for their research

---

## Contact & Support

If professor has issues:
1. Check README troubleshooting section
2. Verify OBS is configured correctly
3. Check Windows firewall (port 5000, 4455)
4. Try running as administrator

---

**Build Status**: ✅ Ready for packaging
**Last Updated**: February 5, 2026
**Build Method**: PyInstaller + app_launcher.py
