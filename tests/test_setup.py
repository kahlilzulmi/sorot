"""
Test script to verify installation and components.
"""

import sys

print("="*80)
print("Testing Advertisement Eye Tracking Components")
print("="*80)
print()

errors = []
warnings = []

# Test core imports
print("1. Testing core dependencies...")
try:
    import flask
    print("   ✓ Flask")
except ImportError as e:
    errors.append(f"Flask: {e}")
    print("   ✗ Flask - NOT FOUND")

try:
    import flask_socketio
    print("   ✓ Flask-SocketIO")
except ImportError as e:
    errors.append(f"Flask-SocketIO: {e}")
    print("   ✗ Flask-SocketIO - NOT FOUND")

try:
    import cv2
    print(f"   ✓ OpenCV ({cv2.__version__})")
except ImportError as e:
    errors.append(f"OpenCV: {e}")
    print("   ✗ OpenCV - NOT FOUND")

try:
    import numpy
    print(f"   ✓ NumPy ({numpy.__version__})")
except ImportError as e:
    errors.append(f"NumPy: {e}")
    print("   ✗ NumPy - NOT FOUND")

try:
    import pandas
    print(f"   ✓ Pandas ({pandas.__version__})")
except ImportError as e:
    errors.append(f"Pandas: {e}")
    print("   ✗ Pandas - NOT FOUND")

try:
    import matplotlib
    print(f"   ✓ Matplotlib ({matplotlib.__version__})")
except ImportError as e:
    errors.append(f"Matplotlib: {e}")
    print("   ✗ Matplotlib - NOT FOUND")

print()

# Test optional imports
print("2. Testing optional dependencies...")
try:
    import obswebsocket
    print("   ✓ OBS WebSocket")
except ImportError:
    warnings.append("OBS WebSocket not installed - OBS control will not work")
    print("   ⚠ OBS WebSocket - Optional (for OBS control)")

try:
    import yt_dlp
    print("   ✓ yt-dlp")
except ImportError:
    warnings.append("yt-dlp not installed - YouTube download will not work")
    print("   ⚠ yt-dlp - Optional (for YouTube download)")

try:
    import reportlab
    print("   ✓ ReportLab")
except ImportError:
    warnings.append("ReportLab not installed - PDF reports will not work")
    print("   ⚠ ReportLab - Optional (for PDF reports)")

try:
    import openpyxl
    print("   ✓ OpenPyXL")
except ImportError:
    warnings.append("OpenPyXL not installed - Excel reports may not work")
    print("   ⚠ OpenPyXL - Optional (for Excel reports)")

print()

# Test custom modules
print("3. Testing custom modules...")
try:
    from gaze_post_processor import GazePostProcessor
    print("   ✓ GazePostProcessor")
except ImportError as e:
    errors.append(f"GazePostProcessor: {e}")
    print("   ✗ GazePostProcessor - NOT FOUND")

try:
    from report_generator import ReportGenerator
    print("   ✓ ReportGenerator")
except ImportError as e:
    errors.append(f"ReportGenerator: {e}")
    print("   ✗ ReportGenerator - NOT FOUND")

print()

# Test file structure
print("4. Testing file structure...")
import os

required_files = [
    'sorot.py',
    'gaze_post_processor.py',
    'report_generator.py',
]

for file in required_files:
    if os.path.exists(file):
        print(f"   ✓ {file}")
    else:
        errors.append(f"Missing file: {file}")
        print(f"   ✗ {file} - NOT FOUND")

print()

# Test folders
required_folders = [
    'uploaded_videos',
    'downloaded_videos',
    'sessions',
    'projects',
    'frontend',
    'legacy/templates',
]

print("5. Testing folder structure...")
for folder in required_folders:
    if os.path.exists(folder):
        print(f"   ✓ {folder}/")
    else:
        warnings.append(f"Folder will be created at runtime: {folder}")
        print(f"   ⚠ {folder}/ - Will be created at runtime")

print()
print("="*80)

# Summary
if errors:
    print("❌ ERRORS FOUND:")
    for error in errors:
        print(f"   - {error}")
    print()
    print("Install dependencies: pip install -r requirements.txt")
    sys.exit(1)
else:
    print("✅ All critical components are installed!")

if warnings:
    print()
    print("⚠️  WARNINGS:")
    for warning in warnings:
        print(f"   - {warning}")
    print()
    print("Optional features may not work. See requirements.txt for optional packages.")

print()
print("="*80)
print("System is ready! Run: python sorot.py  (or .\\dev.ps1 for frontend + backend)")
print("="*80)
