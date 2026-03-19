@echo off
echo ================================================================================
echo Building Portable Executable - Simple Method
echo ================================================================================
echo.

REM Install PyInstaller if needed
pip install pyinstaller

echo.
echo Building with spec file...
pyinstaller --clean --noconfirm AdEyeTracker.spec

echo.
echo ================================================================================
echo Build Complete!
echo ================================================================================
echo.
echo Executable: dist\AdEyeTracker.exe
echo.
echo To test:
echo   1. cd dist
echo   2. AdEyeTracker.exe
echo.
echo To distribute:
echo   - Copy dist\AdEyeTracker.exe anywhere
echo   - Include DISTRIBUTION_README.md for your professor
echo.
pause
