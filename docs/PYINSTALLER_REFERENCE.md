# PyInstaller Quick Reference

## Build Commands

### Standard Build (Recommended)
```powershell
.\build.ps1
```
Creates `dist\EyeTracker\` folder with all files.

### Manual Build
```powershell
python -m PyInstaller --clean --noconfirm eye_tracker.spec
.\post_build.ps1
```

### Clean Build (Remove Everything First)
```powershell
Remove-Item -Recurse -Force build, dist, __pycache__
.\build.ps1
```

## Testing

### Quick Test
```powershell
cd dist\EyeTracker
.\EyeTracker.exe
```

### Full Test Checklist
- [ ] Application starts
- [ ] System check runs (first launch)
- [ ] Detection wizard opens
- [ ] Game wizard opens
- [ ] Stimulus wizard opens
- [ ] OBS wizard opens
- [ ] Settings dialog opens
- [ ] Database viewer opens
- [ ] Language switching works
- [ ] Session data saves correctly

## File Structure

```
dist/EyeTracker/
├── EyeTracker.exe           # Main executable (200-400 MB)
├── README.md                # User documentation
├── assets/
│   └── translations/
│       ├── en.json         # English translations
│       └── id.json         # Indonesian translations
├── Database/                # Session databases (created on run)
├── Sessions/                # Temporary files (created on run)
├── Logs/                    # Application logs (created on run)
└── [Many DLLs and .pyd files]  # Python and dependencies
```

## Common Issues

| Issue | Solution |
|-------|----------|
| "Module not found" error | Add to `hiddenimports` in spec file |
| Large executable size (>500MB) | Normal for OpenCV + Matplotlib apps |
| Slow first startup | Expected - extracting files |
| Antivirus warning | False positive - add exception |
| Missing translations | Check `assets/translations/*.json` copied |

## Customization

### Change Executable Name
Edit `eye_tracker.spec`:
```python
exe = EXE(
    ...
    name='YourName',  # Change this
    ...
)
```

### Add Icon
1. Create `app_icon.ico` in `assets/icons/`
2. Edit `eye_tracker.spec`:
```python
exe = EXE(
    ...
    icon='assets/icons/app_icon.ico',  # Add this
    ...
)
```

### Include Additional Files
Edit `eye_tracker.spec`:
```python
datas = [
    ('assets/translations/*.json', 'assets/translations'),
    ('your/file.txt', 'destination/folder'),  # Add this
]
```

## Distribution

### Create ZIP Archive
```powershell
Compress-Archive -Path dist\EyeTracker -DestinationPath EyeTracker-v1.0.0.zip
```

### Upload to Cloud
- Google Drive
- Dropbox  
- OneDrive
- GitHub Releases

### Create Installer
Use Inno Setup or NSIS for professional installer with:
- Start menu shortcuts
- Desktop shortcut
- Uninstaller
- File associations

## Performance

**Build Time**: 3-5 minutes (first build)  
**Executable Size**: 300-500 MB (typical)  
**Startup Time**: 3-5 seconds (after first run)  
**Memory Usage**: 200-400 MB (running)

## Support

**PyInstaller Docs**: https://pyinstaller.org/  
**GitHub Issues**: https://github.com/pyinstaller/pyinstaller/issues

---

**Quick Start**: Just run `.\build.ps1` and wait! 🚀
