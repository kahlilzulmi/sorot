# Implementation Checklist: Public/Private Repository Split

## ✅ What's Been Created

I've created the plugin architecture for you:

### 📁 Files Created:

1. **`PLUGIN_SPLIT_GUIDE.md`** - Complete architecture documentation
2. **`modules/pro_features_loader.py`** - Plugin detection (goes in PUBLIC repo)
3. **`PLUGIN_TEMPLATE/`** - Complete private plugin structure:
   - `tobii_pro_plugin/__init__.py` - Plugin interface
   - `tobii_pro_plugin/tobii_detector.py` - Tobii Ghost integration
   - `tobii_pro_plugin/obs_integration.py` - OBS WebSocket control
   - `setup.py` - Installation script
   - `requirements.txt` - Plugin dependencies
   - `README.md` - Private repo documentation
4. **`requirements_public.txt`** - Public repo dependencies (without Tobii/OBS)

---

## 🚀 Next Steps to Implement

### Step 1: Extract Tobii Code from Main App

You need to move Tobii-specific code from `video_roi_webapp.py` to the plugin:

**Code to extract:**
- Lines 105-131: `is_tobii_overlay_running()` function → Move to `tobii_detector.py`
- Lines 202-320: `OBSController` class → Already created in `obs_integration.py`
- Lines 1292-1330: Tobii device detection → Move to `tobii_detector.py`

**How to update main app:**
```python
# OLD (in video_roi_webapp.py):
def is_tobii_overlay_running():
    # ... code ...

class OBSController:
    # ... code ...

# NEW (in video_roi_webapp.py):
from modules.pro_features_loader import (
    TOBII_PRO_AVAILABLE,
    is_tobii_overlay_running,
    OBSController,
    is_obs_running
)

# Rest of your code works the same!
```

### Step 2: Create GitHub Repositories

**Public Repository:**
```bash
cd roi_web_app
git init
git add .
git commit -m "Initial public release - open source eye tracking"
gh repo create video-roi-analyzer --public --source=. --push
```

**Private Repository:**
```bash
cd PLUGIN_TEMPLATE
git init
git add .
git commit -m "Initial Tobii Pro Plugin"
gh repo create tobii-pro-plugin --private --source=. --push
```

### Step 3: Test the Installation Flow

**As a public user (no plugin):**
```bash
git clone https://github.com/yourusername/video-roi-analyzer.git
cd video-roi-analyzer  
pip install -r requirements_public.txt
python roi_web_app/video_roi_webapp.py

# Expected output:
# ℹ️ Running in Open Source Mode
# Features available:
#   • Mouse gaze tracking
#   • Generic webcam eye tracking
#   ...
```

**As a verified researcher (with plugin):**
```bash
# Clone both repos
git clone https://github.com/yourusername/video-roi-analyzer.git
git clone https://github.com/yourusername/tobii-pro-plugin.git

# Install main app
cd video-roi-analyzer
pip install -r requirements_public.txt

# Install plugin
cd ../tobii-pro-plugin
pip install -e .

# Run
cd ../video-roi-analyzer
python roi_web_app/video_roi_webapp.py

# Expected output:
# ✅ Tobii Pro Plugin detected
# Version: 1.0.0
# Features enabled: ...
```

### Step 4: Update requirements.txt

Replace your current `requirements.txt` with `requirements_public.txt`:
```bash
cd roi_web_app
mv requirements.txt requirements_original_backup.txt
mv requirements_public.txt requirements.txt
```

### Step 5: Grant Access to Researchers

**Via GitHub Web Interface:**
1. Go to `https://github.com/yourusername/tobii-pro-plugin`
2. Settings → Collaborators
3. Add researcher's GitHub username
4. They receive an email invitation

**Via GitHub CLI:**
```bash
gh api repos/:owner/tobii-pro-plugin/collaborators/:username -X PUT
```

---

## 📋 Files Modified Checklist

Update these files in the main app to use the plugin loader:

- [ ] `video_roi_webapp.py` - Replace Tobii imports with `from modules.pro_features_loader import ...`
- [ ] Remove `is_tobii_overlay_running()` function (now in plugin)
- [ ] Remove `OBSController` class (now in plugin)
- [ ] Keep all other features (ROI, scenes, reports, mouse tracking)

---

##  Would You Like Me To:

1. **Automatically update `video_roi_webapp.py`** to use the plugin loader?
2. **Create a `advanced_algorithms.py`** stub for future features?
3. **Add license headers** to all files?
4. **Create a migration script** to automate the split?

Let me know what you'd like me to implement next!
