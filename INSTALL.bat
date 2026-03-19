@echo off
echo ================================================================================
echo Advertisement Eye Tracking - Neuromarketing Solution
echo Post-Processing Architecture Setup
echo ================================================================================
echo.

echo Installing required dependencies...
echo.

REM Core dependencies
pip install flask flask-socketio
pip install opencv-python numpy pandas
pip install matplotlib

REM OBS WebSocket control
pip install obs-websocket-py

REM YouTube download (optional)
pip install yt-dlp

REM Report generation
pip install reportlab openpyxl

REM Additional utilities
pip install werkzeug tqdm

echo.
echo ================================================================================
echo Installation Complete!
echo ================================================================================
echo.
echo Next steps:
echo 1. Configure OBS with the settings in IMPLEMENTATION_GUIDE.md
echo 2. Run: python video_roi_webapp.py
echo 3. Open browser: http://localhost:5000
echo.
echo For detailed usage, see IMPLEMENTATION_GUIDE.md
echo.

pause
