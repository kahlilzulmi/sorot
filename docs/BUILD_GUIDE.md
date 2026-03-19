# PyInstaller Build Guide

This guide explains how to build a standalone executable for the Eye Tracker application.

## Prerequisites

1. **Python 3.10+** installed
2. **Virtual environment** activated (`.venv`)
3. **All dependencies** installed (`pip install -r requirements.txt`)
4. **PyInstaller** installed (`pip install pyinstaller`)

## Quick Build

Simply run the build script:

```powershell
.\build.ps1
```

This will:
1. Clean previous builds
2. Run PyInstaller with the spec file
3. Copy additional files (README, etc.)
4. Create necessary directories
5. Display build statistics
6. Optionally run the executable

## Manual Build

If you prefer to build manually:

```powershell
# Clean previous builds
Remove-Item -Recurse -Force build, dist

# Run PyInstaller
python -m PyInstaller --clean --noconfirm eye_tracker.spec

# Run post-build tasks
.\post_build.ps1
```

## Build Configuration

The build is configured in `eye_tracker.spec`:

- **Entry point**: `eye_tracker.py`
- **Executable name**: `EyeTracker.exe`
- **Console**: Disabled (windowed application)
- **Icon**: None (can be added later)
- **Data files**: 
  - `assets/translations/*.json`
  - `assets/fonts/*`
  - `assets/icons/*`
  - `assets/templates/*`

### Hidden Imports

The spec file includes all necessary hidden imports:
- Detection modules
- Game engine
- Stimulus generator
- Database manager
- Visualization tools
- All utils and dependencies

### Excluded Packages

To reduce size, the following are excluded:
- Test modules (`*.tests`)
- Unittest
- Development tools

## Output Structure

```
dist/
  EyeTracker/
    EyeTracker.exe          # Main executable
    README.md               # User documentation
    assets/                 # Resources
      translations/
        en.json
        id.json
    Database/               # Created on first run
    Sessions/               # Temporary session files
    Logs/                   # Application logs
    [DLLs and dependencies] # Auto-included by PyInstaller
```

## Testing the Build

### 1. Basic Test

```powershell
cd dist\EyeTracker
.\EyeTracker.exe
```

Check:
- Application starts without errors
- Main window displays correctly
- Language selection works
- All buttons are clickable

### 2. Module Tests

Test each major feature:

**Detection**:
- Click "Detection" button
- Load sample video
- Process and view results

**Game**:
- Click "Game" button
- Enter participant info
- Camera detection works

**Stimulus**:
- Click "Stimulus" button
- Select protocol
- Generate video

**Database**:
- Click "Database" button
- View sessions tab
- Export functionality

**Settings**:
- Click "Settings" button
- Navigate tabs
- Save/cancel works

### 3. Clean System Test

For thorough testing:

1. Copy `dist\EyeTracker` to a different machine (without Python installed)
2. Run `EyeTracker.exe`
3. Complete full workflow
4. Check all generated files

## Troubleshooting

### Build Fails

**Error**: "Module not found"
- Add missing module to `hiddenimports` in `eye_tracker.spec`
- Rebuild

**Error**: "Permission denied"
- Close any running instances of EyeTracker
- Run PowerShell as Administrator

**Error**: "File not found" (data files)
- Check `datas` section in `eye_tracker.spec`
- Ensure paths are correct

### Executable Issues

**Problem**: Executable is too large (>500MB)
- This is normal for Python applications with OpenCV, Matplotlib, etc.
- Consider using UPX compression (already enabled)

**Problem**: Slow startup
- First-time extraction can be slow
- Subsequent runs are faster
- Consider using `--onefile` for single executable (slower startup)

**Problem**: Antivirus flags executable
- Common false positive for PyInstaller executables
- Add exception in antivirus
- Sign executable with code signing certificate (optional)

### Runtime Errors

**Error**: "Failed to execute script"
- Run with console enabled for debugging
- Change `console=False` to `console=True` in spec file
- Rebuild and check error messages

**Error**: Missing DLL
- Usually auto-resolved by PyInstaller
- If persistent, manually copy DLL to dist folder

**Error**: Import error at runtime
- Add missing import to `hiddenimports`
- Check if module needs data files

## Optimization

### Reduce Size

1. **Use `--onefile`** (creates single .exe but slower startup):
   ```python
   # In eye_tracker.spec, change EXE section:
   exe = EXE(
       pyz,
       a.scripts,
       a.binaries,  # Add this
       a.zipfiles,  # Add this
       a.datas,     # Add this
       [],
       name='EyeTracker',
       # ... rest stays same
   )
   # Remove COLLECT section
   ```

2. **Exclude more packages**:
   - Add unnecessary packages to `excludes` list
   - Test carefully after exclusion

3. **Use UPX aggressively**:
   - Already enabled with `upx=True`
   - Can compress DLLs further

### Improve Startup Time

1. **Lazy imports**: Import heavy modules only when needed
2. **Splash screen**: Add loading screen during startup
3. **Optimize imports**: Remove unused imports

### Add Features

1. **Application Icon**:
   ```python
   # In eye_tracker.spec, EXE section:
   icon='assets/icons/app_icon.ico'
   ```

2. **Version Information**:
   ```python
   # Add version_info parameter to EXE
   ```

3. **Code Signing**:
   - Requires code signing certificate
   - Use SignTool.exe (Windows SDK)

## Distribution

### Create Installer

Use **Inno Setup** or **NSIS** to create installer:

1. Install Inno Setup
2. Create script pointing to `dist\EyeTracker`
3. Build installer.exe
4. Includes:
   - Start menu shortcuts
   - Desktop shortcut
   - Uninstaller
   - File associations (optional)

### Create ZIP Archive

Simple distribution method:

```powershell
Compress-Archive -Path dist\EyeTracker -DestinationPath EyeTracker-v1.0.0.zip
```

Include:
- `README.md`
- `LICENSE` (if applicable)
- System requirements
- Installation instructions

## CI/CD Integration

For automated builds:

```yaml
# GitHub Actions example
name: Build Executable
on: [push]
jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pip install pyinstaller
      - run: python -m PyInstaller eye_tracker.spec
      - uses: actions/upload-artifact@v2
        with:
          name: EyeTracker-Windows
          path: dist/EyeTracker
```

## Best Practices

1. **Test before distribution**
   - Test on clean system
   - Test all features
   - Test with various inputs

2. **Version control**
   - Tag releases
   - Document changes
   - Keep spec file in repository

3. **User feedback**
   - Collect crash reports
   - Monitor error logs
   - Update regularly

4. **Security**
   - Don't include sensitive data
   - Validate all user inputs
   - Keep dependencies updated

## Support

For PyInstaller issues:
- [PyInstaller Documentation](https://pyinstaller.org/)
- [PyInstaller GitHub](https://github.com/pyinstaller/pyinstaller)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/pyinstaller)

---

**Last Updated**: November 2025  
**Author**: Kahlil Gibran Al Zulmi
