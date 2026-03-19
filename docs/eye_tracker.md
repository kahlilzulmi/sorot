# Eye Tracker Research Software  
This markdown is a plan to integrate the projects into one file: eye_tracker.py  

💖 Developed with love for my beloved Medical Technology study program.  

This software should checks the software required to be installed in the PC and it's specs:  
* Windows 10 or 11
* Tobii Experience
* Tobii Ghost
* Open Broadcasting Software (OBS) Studio  
  
The user should prompted to calibrate the eye tracker and config the OBS to have window record the SSOverlay.exe and nice to have if user config "Source Control" plugin.  
  
The UI should have 3 button of below features, each feature have wizard (step-by-step).

## Key Features  

### Detect Gaze Point Position from Screen-Recorded Eye Gaze Overlay from Tobii Ghost  
This software will detect the position (x, y) from eye gaze of Tobii Ghost screen-recorded-able overlay video.  
* Input: Video  
* Process: We have five options: using contour-based detection, color-based detection, contour-color-combined detection, blob detector, and hough circle transform based detection. It should be checkbox button in the GUI, if one selected, just it is, but if we choose multiple, we can make comparation.
* Output: beside the CSV and overlayed video, we can compare diagrams between methods in Process.  

Reference: detect_gemini7_smooth.py

### Math Quiz Game  
This math quiz is unique because the mouse will be controlled or pointer with the eye only. Oh, and the eye gaze will be recorded and we will see the diagrams. Reference: game3_with_recording.py  

### Stimulus Simulation  
This simulation page should show two buttons:  
1. Generate stimulus video
2. Open live stimulus simulation + recording in the background like in Math Quiz Game

Reference: genvidsim4.py

