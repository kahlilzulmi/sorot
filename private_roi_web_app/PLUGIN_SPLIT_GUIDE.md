# Code Split Guide: Public Repo + Private Plugin

## Repository Structure

### 📁 PUBLIC REPO: `video-roi-analyzer` (GitHub Public)
```
video-roi-analyzer/
├── roi_web_app/
│   ├── video_roi_webapp.py          # Main Flask app
│   ├── gaze_post_processor.py       # Report generation
│   ├── report_generator.py          # CSV/PDF reports
│   ├── modules/
│   │   ├── detection_algorithms.py  # ✅ Generic webcam tracking ONLY
│   │   ├── game_engine.py
│   │   ├── database_manager.py
│   │   └── pro_features_loader.py   # 🆕 Plugin detection & loader
│   ├── static/
│   ├── templates/
│   └── requirements.txt             # Basic dependencies
├── README.md                        # Public documentation
└── LICENSE                          # MIT or similar

Features in Public Repo:
✅ Mouse tracking mode
✅ Generic webcam eye tracking (dlib/MediaPipe)
✅ ROI editing & scene management
✅ CSV import/export
✅ Video playback & annotation
✅ Basic gaze heatmaps
✅ Report generation
❌ Tobii Ghost detection
❌ OBS virtual camera integration
❌ Advanced eye tracking algorithms
```

### 🔒 PRIVATE REPO: `tobii-pro-plugin` (GitHub Private - Verified Researchers Only)

```
tobii-pro-plugin/
├── tobii_pro_plugin/
│   ├── __init__.py                  # Plugin interface
│   ├── tobii_detector.py            # Tobii Ghost detection
│   ├── obs_integration.py           # OBS virtual camera
│   ├── advanced_algorithms.py       # Advanced tracking
│   └── device_checker.py            # Tobii overlay detection
├── setup.py                         # Installation script
├── requirements.txt                 # obs-websocket-py, psutil
├── README.md                        # Installation instructions
└── LICENSE                          # Restricted license

Features in Private Plugin:
🔒 Tobii Ghost overlay detection (SSOverlay.exe)
🔒 OBS virtual camera integration
🔒 Advanced eye tracking algorithms
🔒 Hardware-specific optimizations
```

---

## Installation Instructions

### For Public Users (Free/Open Source):
```bash
git clone https://github.com/yourusername/video-roi-analyzer.git
cd video-roi-analyzer
pip install -r requirements.txt
python roi_web_app/video_roi_webapp.py
```

### For Verified Researchers (Licensed):
```bash
# Step 1: Clone public repo
git clone https://github.com/yourusername/video-roi-analyzer.git
cd video-roi-analyzer
pip install -r requirements.txt

# Step 2: Clone private plugin (requires GitHub collaborator access)
cd ..
git clone https://github.com/yourusername/tobii-pro-plugin.git
cd tobii-pro-plugin
pip install -e .

# Step 3: Run with Tobii features
cd ../video-roi-analyzer
python roi_web_app/video_roi_webapp.py
# Tobii features automatically detected and enabled!
```

---

## How Plugin Detection Works

The main app checks if `tobii_pro_plugin` is installed:

```python
# In video_roi_webapp.py
try:
    from tobii_pro_plugin import TobiiDetector, OBSIntegration
    TOBII_PRO_AVAILABLE = True
    print("✅ Tobii Pro Plugin detected - Advanced features enabled")
except ImportError:
    TOBII_PRO_AVAILABLE = False
    print("ℹ️ Running in open-source mode (mouse/generic webcam tracking)")
```

---

## Access Control Strategy

### Granting Access to Verified Researchers:

1. **Researcher applies** via email with:
   - Research proposal
   - Institutional affiliation
   - IRB approval (if applicable)

2. **You review** their credentials

3. **Grant GitHub access**:
   - Go to `tobii-pro-plugin` repo Settings → Collaborators
   - Add researcher's GitHub username
   - They get email invitation

4. **They clone** both repos and install

5. **Revoke access** anytime:
   - Remove from collaborators list
   - They can no longer pull updates

---

## Next Steps

Would you like me to:

1. ✅ **Create `tobii_pro_plugin/__init__.py`** - Plugin interface
2. ✅ **Create `modules/pro_features_loader.py`** - Detection logic
3. ✅ **Extract Tobii code** from main app into plugin
4. ✅ **Update `requirements.txt`** to split dependencies
5. ✅ **Create README templates** for both repos

Let me know which parts to implement!
