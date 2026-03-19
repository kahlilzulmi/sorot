"""
Build script for creating portable executable of Advertisement Eye Tracking Tool.
Packages everything into a single .exe file.
"""

import PyInstaller.__main__
import os
import sys
import shutil

print("="*80)
print("Building Advertisement Eye Tracking - Portable Executable")
print("="*80)
print()

# Clean previous builds
print("Step 1: Cleaning previous builds...")
for folder in ['build', 'dist']:
    if os.path.exists(folder):
        shutil.rmtree(folder)
        print(f"  Removed {folder}/")

print()
print("Step 2: Running PyInstaller...")
print("  This may take several minutes...")
print()

# PyInstaller arguments
PyInstaller.__main__.run([
    'video_roi_webapp.py',              # Main script
    '--name=AdEyeTracker',              # Output name
    '--onefile',                         # Single executable
    '--windowed',                        # No console window (will open browser)
    '--icon=app_icon.ico',              # App icon (if exists)
    
    # Add custom modules
    '--add-data=gaze_post_processor.py;.',
    '--add-data=report_generator.py;.',
    '--add-data=IMPLEMENTATION_GUIDE.md;.',
    
    # Add templates folder (Flask needs this)
    '--add-data=templates;templates',
    
    # Add static files if they exist
    '--add-data=static;static',
    
    # Hidden imports (packages PyInstaller might miss)
    '--hidden-import=flask',
    '--hidden-import=flask_socketio',
    '--hidden-import=engineio',
    '--hidden-import=socketio',
    '--hidden-import=cv2',
    '--hidden-import=numpy',
    '--hidden-import=pandas',
    '--hidden-import=matplotlib',
    '--hidden-import=PIL',
    '--hidden-import=openpyxl',
    '--hidden-import=reportlab',
    '--hidden-import=obswebsocket',
    '--hidden-import=yt_dlp',
    
    # Collect all submodules
    '--collect-all=flask',
    '--collect-all=flask_socketio',
    '--collect-all=cv2',
    '--collect-all=matplotlib',
    '--collect-all=reportlab',
    
    # Optimization
    '--noupx',                          # Don't use UPX compression (faster startup)
    
    # Clean
    '--clean',
    
    # Show details
    '--log-level=INFO'
])

print()
print("="*80)
print("Build Complete!")
print("="*80)
print()
print(f"Executable location: dist/AdEyeTracker.exe")
print(f"Size: ~{os.path.getsize('dist/AdEyeTracker.exe') / (1024*1024):.1f} MB")
print()
print("To distribute:")
print("  1. Copy dist/AdEyeTracker.exe to any location")
print("  2. Run it - browser will open automatically")
print("  3. Configure OBS as described in IMPLEMENTATION_GUIDE.md")
print()
print("="*80)
