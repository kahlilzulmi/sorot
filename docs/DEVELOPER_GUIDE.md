# Developer Setup Guide

Complete guide for setting up the Eye Tracker development environment.

---

## Prerequisites

### Required Software

1. **Python 3.10 or higher**
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"
   - Verify: `python --version`

2. **Git** (optional, for version control)
   - Download from [git-scm.com](https://git-scm.com/)
   - Verify: `git --version`

3. **Visual Studio Code** (recommended IDE)
   - Download from [code.visualstudio.com](https://code.visualstudio.com/)
   - Extensions to install:
     - Python (Microsoft)
     - Pylance
     - Python Docstring Generator
     - GitLens (optional)

### System Requirements

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 2GB free space (for development environment)
- **Camera**: USB webcam (for game module testing)

---

## Project Setup

### 1. Clone or Download Repository

**Option A: Clone with Git**
```bash
git clone https://github.com/kahlilzulmi/ufyp-eyetracker.git
cd ufyp-eyetracker
```

**Option B: Download ZIP**
- Download ZIP from repository
- Extract to desired location
- Open terminal in extracted folder

### 2. Create Virtual Environment

```powershell
# Create virtual environment
python -m venv .venv

# Activate (PowerShell)
.\.venv\Scripts\Activate.ps1

# Or activate (Command Prompt)
.\.venv\Scripts\activate.bat

# Verify activation (prompt should show (.venv))
python --version
```

### 3. Install Dependencies

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installations
pip list
```

**Expected packages:**
- opencv-python >= 4.8.0
- numpy >= 1.24.0
- pandas >= 2.0.0
- matplotlib >= 3.7.0
- seaborn >= 0.12.0
- scipy >= 1.11.0
- pygame >= 2.5.0
- openpyxl >= 3.1.0
- psutil >= 5.9.0
- pywin32 >= 305

### 4. Project Structure

```
tugasakhir/
├── eye_tracker.py          # Main entry point
├── requirements.txt        # Dependencies
├── config.json            # Configuration (created on first run)
│
├── modules/               # Feature modules
│   ├── __init__.py
│   ├── detection_wizard.py
│   ├── detect_gemini8.py
│   ├── game_wizard.py
│   ├── game_engine.py
│   ├── stimulus_wizard.py
│   ├── stimulus_generator.py
│   ├── database_viewer.py
│   ├── database_manager.py
│   ├── visualization.py
│   ├── report_generator.py
│   ├── obs_wizard.py
│   ├── settings_dialog.py
│   └── system_check.py
│
├── utils/                 # Utilities
│   ├── __init__.py
│   ├── config_manager.py
│   ├── localization.py
│   └── logger.py
│
├── assets/                # Resources
│   ├── translations/
│   │   ├── en.json
│   │   └── id.json
│   ├── fonts/
│   ├── icons/
│   └── templates/
│
├── Database/              # SQLite databases (created on first run)
├── Sessions/              # Temporary session files
├── Logs/                  # Application logs
│
├── build.ps1             # Build script
├── eye_tracker.spec      # PyInstaller spec
└── docs/                 # Documentation
    ├── API_DOCUMENTATION.md
    ├── BUILD_GUIDE.md
    └── README_DIST.md
```

---

## Running the Application

### Development Mode

```powershell
# Make sure virtual environment is activated
python eye_tracker.py
```

**First Run:**
- System check will run automatically
- Configuration file (`config.json`) will be created
- Empty directories will be created
- Translations will be loaded

### Testing Individual Modules

```python
# Test detection algorithm
python -c "from modules.detect_gemini8 import detect_pupil_hough; print('✓ Detection module OK')"

# Test database
python -c "from modules.database_manager import create_detection_session; print('✓ Database module OK')"

# Test visualization
python -c "from modules.visualization import plot_gaze_trajectory; print('✓ Visualization module OK')"

# Test game engine
python -c "from modules.game_engine import EyeGameEngine; print('✓ Game engine OK')"

# Test stimulus generator
python -c "from modules.stimulus_generator import StimulusGenerator; print('✓ Stimulus generator OK')"
```

### Debug Mode

Add logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or set console mode in PyInstaller spec:
```python
console=True  # Shows console for debugging
```

---

## Development Workflow

### 1. Code Organization

Follow the existing structure:
```
Feature Module (wizard.py)
    ↓
Business Logic (engine.py / generator.py / detector.py)
    ↓
Data Access (database_manager.py)
    ↓
Utilities (logger.py / config_manager.py)
```

### 2. Adding New Features

**Step 1: Create Module**
```python
# modules/my_feature.py
"""
My Feature Module

Description of what this module does.

Author: Your Name
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MyFeature:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logger.info("MyFeature initialized")
    
    def process(self):
        """Process something."""
        try:
            # Your logic here
            logger.info("Processing complete")
            return True
        except Exception as e:
            logger.error(f"Error in process: {e}", exc_info=True)
            return False
```

**Step 2: Add Translations**
```json
// assets/translations/en.json
{
  "my_feature": {
    "title": "My Feature",
    "description": "Feature description",
    "button_process": "Process"
  }
}
```

**Step 3: Create Wizard (if needed)**
```python
# modules/my_feature_wizard.py
import tkinter as tk
from tkinter import ttk
from utils.localization import get_text

def launch_my_feature_wizard(parent):
    """Launch my feature wizard."""
    dialog = tk.Toplevel(parent)
    dialog.title(get_text("my_feature.title"))
    # ... build UI
```

**Step 4: Integrate into Main GUI**
```python
# In eye_tracker.py
def launch_my_feature(self):
    """Launch my feature."""
    from modules.my_feature_wizard import launch_my_feature_wizard
    launch_my_feature_wizard(self.root)

# Add button to UI
ttk.Button(frame, text=get_text("my_feature.title"),
          command=self.launch_my_feature).pack()
```

### 3. Database Schema

Add new table for your feature:

```python
# In modules/database_manager.py
def _init_my_feature_db(conn):
    """Initialize my feature database."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS my_feature_sessions (
            session_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            data TEXT NOT NULL
        )
    """)
    conn.commit()
```

### 4. Testing

Create test file:

```python
# tests/test_my_feature.py
import unittest
from modules.my_feature import MyFeature

class TestMyFeature(unittest.TestCase):
    def setUp(self):
        self.feature = MyFeature({"param": "value"})
    
    def test_process(self):
        result = self.feature.process()
        self.assertTrue(result)
    
if __name__ == '__main__':
    unittest.main()
```

Run tests:
```powershell
python -m unittest discover tests
```

---

## Code Style Guide

### Python Style

Follow **PEP 8** with these specifics:

```python
# Imports: Standard library, third-party, local
import os
import sys
from typing import Dict, List, Optional

import numpy as np
import cv2

from utils.logger import log_info
from modules.database_manager import create_session

# Constants in CAPS
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Classes in PascalCase
class MyFeature:
    """Brief description.
    
    Detailed description.
    
    Attributes:
        attribute_name: Description
    """
    
    def __init__(self):
        """Initialize instance."""
        self.attribute_name = value

# Functions in snake_case
def process_data(input_data: List[int]) -> Dict[str, Any]:
    """
    Process the input data.
    
    Args:
        input_data: List of integers to process
        
    Returns:
        Dictionary with processed results
        
    Raises:
        ValueError: If input_data is empty
    """
    if not input_data:
        raise ValueError("Input data cannot be empty")
    
    result = {"count": len(input_data)}
    return result
```

### Documentation

**Module Docstring:**
```python
"""
Module Name

Brief description.

Author: Name
NRP: Student's Number (if applicable)
Institution: Name
"""
```

**Function Docstring:**
```python
def function_name(param1: type, param2: type) -> return_type:
    """
    Brief description.
    
    Detailed description if needed.
    
    Args:
        param1: Description
        param2: Description
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When this exception occurs
        
    Example:
        >>> result = function_name(1, 2)
        >>> print(result)
        3
    """
```

### Error Handling

```python
from utils.logger import log_error, log_warning

try:
    result = risky_operation()
except SpecificException as e:
    log_error(f"Specific error: {e}", exc_info=True)
    # Handle or re-raise
    raise
except Exception as e:
    log_error(f"Unexpected error: {e}", exc_info=True)
    # User-friendly message
    return None
finally:
    # Cleanup if needed
    cleanup()
```

---

## Common Development Tasks

### Update Translations

```powershell
# Edit translation files
code assets/translations/en.json
code assets/translations/id.json

# Verify JSON syntax
python -c "import json; json.load(open('assets/translations/en.json'))"
```

### Modify Configuration

```python
from utils.config_manager import load_config, save_config

config = load_config()
config["my_setting"] = "new_value"
save_config(config)
```

### Database Operations

```python
from modules.database_manager import (
    create_detection_session,
    get_detection_session,
    search_sessions
)

# Create
session_id = create_detection_session({
    "video_path": "test.mp4",
    "method": "hough"
})

# Read
session = get_detection_session(session_id)

# Search
results = search_sessions("detection", {"method": "hough"})

# Delete
from modules.database_manager import delete_session
delete_session("detection", session_id)
```

### Generate Reports

```python
from modules.report_generator import generate_detection_excel_report

report_path = "session_report.xlsx"
generate_detection_excel_report(session_data, report_path)
```

---

## Debugging Tips

### Common Issues

**Issue: ModuleNotFoundError**
```powershell
# Make sure virtual environment is activated
.\.venv\Scripts\Activate.ps1

# Reinstall requirements
pip install -r requirements.txt
```

**Issue: Import errors**
```python
# Add project root to Python path
import sys
sys.path.insert(0, 'path/to/project')
```

**Issue: Tkinter not found**
```powershell
# Tkinter comes with Python. Reinstall Python with tcl/tk support
# Or install via system package manager (Linux)
sudo apt-get install python3-tk
```

**Issue: OpenCV camera not working**
```python
# Test camera
import cv2
cap = cv2.VideoCapture(0)  # Try 0, 1, 2 for different cameras
ret, frame = cap.read()
print(f"Camera opened: {ret}")
cap.release()
```

### Logging

Check logs for errors:
```powershell
# View latest log
Get-Content Logs\eye_tracker_YYYY-MM-DD.log -Tail 50

# Monitor in real-time
Get-Content Logs\eye_tracker_YYYY-MM-DD.log -Wait
```

### Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

---

## Version Control

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes
git add .
git commit -m "Add: my feature description"

# Push to remote
git push origin feature/my-feature

# Create pull request on GitHub
```

### Commit Messages

Follow conventional commits:

```
Type: Short description

Detailed description if needed.

Types:
- Add: New feature
- Fix: Bug fix
- Update: Modify existing feature
- Refactor: Code restructuring
- Docs: Documentation
- Test: Tests
- Style: Formatting
```

Examples:
```
Add: Eye blink detection algorithm
Fix: Camera not releasing on game exit
Update: Improve Kalman filter parameters
Refactor: Extract detection methods to separate module
Docs: Add API documentation for stimulus generator
```

---

## Building for Distribution

See [BUILD_GUIDE.md](BUILD_GUIDE.md) for complete PyInstaller instructions.

Quick build:
```powershell
.\build.ps1
```

---

## Getting Help

### Internal Resources

- [API Documentation](API_DOCUMENTATION.md)
- [Build Guide](BUILD_GUIDE.md)
- [PyInstaller Reference](PYINSTALLER_REFERENCE.md)
- [User Manual](README_DIST.md)

### External Resources

- **Python**: https://docs.python.org/3/
- **OpenCV**: https://docs.opencv.org/
- **Tkinter**: https://docs.python.org/3/library/tkinter.html
- **Pygame**: https://www.pygame.org/docs/
- **Matplotlib**: https://matplotlib.org/stable/index.html
- **Pandas**: https://pandas.pydata.org/docs/
- **PyInstaller**: https://pyinstaller.org/

### Support

For project-specific questions:
- Check existing code examples
- Review module docstrings
- Consult API documentation

---

## Contributing Guidelines

When contributing:

1. **Follow code style** (PEP 8)
2. **Write docstrings** for all public functions/classes
3. **Add translations** for all UI text (EN + ID)
4. **Update documentation** for new features
5. **Test thoroughly** before committing
6. **Use meaningful commit messages**
7. **Keep modules focused** (single responsibility)

---

## Project Roadmap

Completed (10/11):
- ✅ System check module
- ✅ Detection algorithms (5 methods)
- ✅ Game module
- ✅ Stimulus generator
- ✅ Database management
- ✅ Visualization
- ✅ Report generation
- ✅ OBS integration
- ✅ Settings interface
- ✅ PyInstaller packaging

In Progress (1/11):
- 📝 Documentation

Future Enhancements:
- Real-time detection mode
- Advanced analytics dashboard
- Cloud synchronization
- Mobile companion app
- API for external integrations

---

**Author**: Kahlil Gibran Al Zulmi  
**Institution**: Institut Teknologi Sepuluh Nopember  
**Last Updated**: November 2025
