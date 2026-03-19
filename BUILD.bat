@echo off
echo ================================================================================
echo Advertisement Eye Tracking - Portable Executable Builder
echo ================================================================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    echo.
)

REM Run build script
python build_exe.py

echo.
echo ================================================================================
echo Build process completed!
echo Check the dist/ folder for AdEyeTracker.exe
echo ================================================================================
echo.

pause
