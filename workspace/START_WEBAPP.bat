@echo off
echo ========================================
echo VIDEO ROI WEB APP - Startup Script
echo ========================================
echo.

echo Installing dependencies...
pip install flask flask-socketio obs-websocket-py yt-dlp

echo.
echo Starting Flask server...
echo Open browser: http://localhost:5000
echo.

python roi_web_app/video_roi_webapp.py

pause
