# Advertisement Eye Tracking Tool - Portable Version

## 📦 What's Inside
A complete neuromarketing eye tracking analysis tool packaged as a single portable executable.

## 🚀 Quick Start (For Your Professor)

### Step 1: Run the Application
1. Double-click **`AdEyeTracker.exe`**
2. Browser will open automatically at `http://localhost:5000`
3. If browser doesn't open, manually navigate to `http://localhost:5000`

### Step 2: Configure OBS Studio (One-Time Setup)

#### Install OBS Studio
1. Download from: https://obsproject.com/
2. Install and run OBS Studio

#### Configure Scenes
**Scene 1: "Window Capture - SSOverlay"**
- Add Source → Window Capture
- Select: SSOverlay.exe (eye tracker software)
- Right-click source → Filters → Add "Source Record"

**Scene 2: "Display Capture - Monitor"**
- Add Source → Display Capture
- Select your main monitor
- Right-click source → Filters → Add "Source Record"

#### Configure Output
1. Go to: Settings → Output
2. Recording tab:
   - Recording Path: `C:\Users\[YourName]\Videos`
   - Recording Format: MP4
   - Filename Formatting: `eyegaze-%CCYY-%MM-%DD %hh-%mm-%ss`

#### Enable WebSocket
1. Go to: Tools → WebSocket Server Settings
2. Check "Enable WebSocket server"
3. Server Port: `4455`
4. Server Password: (leave empty)

### Step 3: Use the Tool

#### A. Load Advertisement Video
1. Click "Upload Video" or "Download from YouTube"
2. Video will load in the player

#### B. Define Regions of Interest (ROIs)
1. Click "Add Scene" to create scenes
2. For each scene:
   - Set start/end frame
   - Draw ROIs (Product, Logo, Text, etc.)
   - Label each ROI
3. Click "Save Workspace" to save your setup

#### C. Record Participant
1. Start SSOverlay.exe (eye tracker software)
2. In the web app, enter participant name
3. Click "Start Recording"
4. Play the advertisement video
5. Participant watches while eye tracker records
6. Click "Stop Recording" when done

#### D. Process & Generate Reports
1. Click "Start Post-Processing"
2. Wait for processing (shows progress bar)
3. When complete, download:
   - **Excel Report**: Detailed statistics per ROI
   - **PDF Report**: Executive summary with heatmaps
   - **Heatmaps**: Attention visualization per scene

#### E. Analyze Multiple Participants
- Repeat steps C-D for each participant
- All use the same advertisement and ROIs
- Each gets individual reports

## 📊 What You Get

### Excel Report
- **Overview**: Total frames, detection rate, duration
- **ROI Statistics**: Attention percentage per ROI per scene
- **Scene Summary**: Detection rates by scene
- **Raw Data**: All gaze coordinates and timestamps

### PDF Report
- Executive summary
- ROI performance tables
- Heatmaps for all scenes
- Professional formatting ready for presentations

### Heatmaps
- Visual attention maps per scene
- Red = High attention
- Blue = Low attention
- Overlaid on actual video frames

## 🔧 System Requirements

- **OS**: Windows 10/11
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 500MB free space
- **OBS Studio**: Latest version
- **Eye Tracker**: SSOverlay.exe compatible device

## 🐛 Troubleshooting

### Issue: "Cannot connect to OBS"
**Solution**: 
1. Make sure OBS Studio is running
2. Check WebSocket is enabled (Tools → WebSocket Server Settings)
3. Port should be 4455

### Issue: "Recording file not found"
**Solution**:
1. Check OBS output settings
2. Verify filename format: `eyegaze-%CCYY-%MM-%DD %hh-%mm-%ss`
3. Check Videos folder path

### Issue: "Low detection rate"
**Solution**:
1. Ensure good lighting on participant's face
2. Run eye tracker calibration (in SSOverlay.exe)
3. Position camera properly

### Issue: "Browser doesn't open"
**Solution**:
Manually open: `http://localhost:5000`

### Issue: "Port already in use"
**Solution**:
Close other applications using port 5000, or edit port in config

## 📁 Generated Files

All session data is saved in:
```
sessions/
└── session_2026-02-05_14-30-25_ParticipantName/
    ├── report_ParticipantName.xlsx
    ├── report_ParticipantName.pdf
    ├── heatmap_Scene_1.png
    ├── heatmap_Scene_2.png
    └── ...
```

## 🎓 Research Use

### Recommended Workflow for Studies
1. **Preparation Phase**
   - Set up advertisement videos
   - Define scenes and ROIs
   - Save workspace

2. **Data Collection Phase**
   - Record each participant (5-10 minutes per person)
   - Use consistent eye tracker settings
   - Save recordings

3. **Analysis Phase**
   - Process all recordings (automated)
   - Generate reports
   - Compare across participants

4. **Reporting Phase**
   - Aggregate statistics
   - Create presentation from PDFs
   - Publish findings

## 💡 Tips for Best Results

1. **Calibrate Eye Tracker**: Run calibration before each participant
2. **Consistent Lighting**: Keep room lighting stable
3. **Clear Instructions**: Brief participants on what to expect
4. **Test Run**: Do a test recording before actual study
5. **Multiple Takes**: If detection rate is low, re-record

## 📞 Support

For technical issues or questions:
- Check `IMPLEMENTATION_GUIDE.md` in the app folder
- Review OBS configuration
- Verify eye tracker is calibrated

## 📝 Version Information

- **Version**: 2.0 (Post-Processing Architecture)
- **Build Date**: February 2026
- **Compatible with**: OBS Studio 29+, Windows 10/11

---

**Note**: This is a research tool. Ensure proper informed consent and ethical approval before conducting studies with human participants.

## 🎉 Features at a Glance

✅ Single portable executable (no installation)  
✅ Auto-open browser interface  
✅ YouTube video download support  
✅ Real-time ROI editor  
✅ Post-processing for 100% frame coverage  
✅ Multi-participant sessions  
✅ Professional Excel & PDF reports  
✅ Heatmap generation  
✅ OBS integration  
✅ Timestamp synchronization  

---

**Made for**: Advertisement neuromarketing research  
**License**: Academic use  
**Author**: Auto-generated research tool  
