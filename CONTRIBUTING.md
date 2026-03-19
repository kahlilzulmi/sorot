# Contributing to Eye Tracking Research Software

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Pull Request Process](#pull-request-process)
6. [Reporting Bugs](#reporting-bugs)
7. [Suggesting Enhancements](#suggesting-enhancements)
8. [Translation Contributions](#translation-contributions)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all.

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment, discriminatory language, or personal attacks
- Publishing others' private information
- Trolling or insulting/derogatory comments
- Other conduct deemed inappropriate

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:

1. **Python 3.10+** installed
2. **Git** for version control
3. **Virtual environment** tool (venv)
4. **IDE** with Python support (VS Code recommended)
5. **Basic knowledge** of Tkinter, OpenCV, and Pygame

### Setup Development Environment

```powershell
# Clone repository
git clone https://github.com/yourusername/eye-tracker.git
cd eye-tracker

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy

# Run tests to verify setup
pytest tests/
```

### Project Structure

```
eye-tracker/
├── eye_tracker.py          # Main application entry
├── modules/                # Core functionality modules
│   ├── detection_wizard.py
│   ├── detection_algorithms.py
│   ├── game_wizard.py
│   ├── stimulus_wizard.py
│   ├── obs_wizard.py
│   ├── settings_dialog.py
│   ├── database_manager.py
│   ├── visualization.py
│   └── report_generator.py
├── utils/                  # Utility modules
│   ├── config_manager.py
│   ├── localization.py
│   └── logger.py
├── assets/                 # Static resources
│   ├── translations/       # Language files (en.json, id.json)
│   ├── templates/          # Report templates
│   ├── icons/              # UI icons
│   └── fonts/              # Custom fonts
├── tests/                  # Unit tests
│   ├── test_config.py
│   ├── test_detection.py
│   └── test_database.py
└── docs/                   # Documentation
```

---

## Development Workflow

### Branch Strategy

We follow Git Flow workflow:

```
main              # Production-ready code
├── develop       # Development branch
    ├── feature/  # New features
    ├── bugfix/   # Bug fixes
    ├── hotfix/   # Urgent fixes
    └── release/  # Release preparation
```

### Creating a Feature Branch

```bash
# Update develop branch
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add your feature"

# Push to remote
git push origin feature/your-feature-name
```

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:

```bash
# Good commit messages
git commit -m "feat(detection): add dlib facial landmark detection"
git commit -m "fix(game): resolve calibration drift issue"
git commit -m "docs: update API documentation for config_manager"
git commit -m "style: format code with black"

# Bad commit messages (avoid)
git commit -m "fixed stuff"
git commit -m "update"
git commit -m "WIP"
```

### Testing Your Changes

```powershell
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_detection.py

# Run with coverage
pytest --cov=modules --cov-report=html

# View coverage report
start htmlcov\index.html
```

---

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://peps.python.org/pep-0008/) with minor modifications.

#### Formatting

```python
# Use black for automatic formatting
black modules/ utils/ tests/

# Check with flake8
flake8 modules/ utils/ tests/
```

#### Type Hints

Always use type hints for function signatures:

```python
# Good
def detect_pupil(frame: np.ndarray, method: str = "hough") -> Tuple[int, int, int]:
    """Detect pupil in frame."""
    pass

# Bad
def detect_pupil(frame, method="hough"):
    """Detect pupil in frame."""
    pass
```

#### Docstrings

Use Google-style docstrings:

```python
def process_video(
    video_path: str,
    method: str = "hough",
    mode: str = "auto"
) -> Dict[str, Any]:
    """
    Process video for pupil detection.
    
    Args:
        video_path: Path to input video file
        method: Detection method (hough, blob, contour, threshold, dlib)
        mode: Processing mode (auto, chunk, full)
    
    Returns:
        Dictionary containing:
            - success_rate: Percentage of frames with detected pupils
            - positions: List of (x, y, radius) tuples
            - metadata: Video information
    
    Raises:
        FileNotFoundError: If video file doesn't exist
        ValueError: If method is invalid
    
    Example:
        >>> results = process_video("test.mp4", method="hough")
        >>> print(f"Success rate: {results['success_rate']}%")
    """
    pass
```

#### Naming Conventions

```python
# Classes: PascalCase
class DetectionWizard:
    pass

# Functions: snake_case
def calculate_success_rate():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_FRAME_COUNT = 10000

# Private methods: prefix with underscore
def _internal_helper():
    pass

# Protected attributes: prefix with underscore
self._config = {}

# Very private (name mangling): double underscore
self.__internal = None
```

#### Import Organization

```python
# Standard library imports
import os
import sys
from typing import List, Dict, Optional

# Third-party imports
import cv2
import numpy as np
import pandas as pd

# Local application imports
from utils.config_manager import get_config
from modules.detection_algorithms import detect_pupil_hough
```

### GUI Development

#### Tkinter Best Practices

```python
# Use ttk widgets for modern look
from tkinter import ttk

# Create labeled frames for organization
frame = ttk.LabelFrame(parent, text="Detection Settings")

# Use grid for complex layouts
label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

# Configure column weights for responsiveness
parent.columnconfigure(1, weight=1)

# Always provide translations
button = ttk.Button(
    parent,
    text=get_text("button.save"),  # Good
    # text="Save",  # Bad (hardcoded)
    command=self._save
)

# Use StringVar for dynamic text
self.status_var = tk.StringVar(value=get_text("status.idle"))
label = ttk.Label(parent, textvariable=self.status_var)
```

#### Game Development (Pygame)

```python
# Initialize properly
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()

# Game loop structure
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Update game state
    update()
    
    # Draw everything
    screen.fill((0, 0, 0))
    draw()
    pygame.display.flip()
    
    # Control frame rate
    clock.tick(60)

# Clean up
pygame.quit()
```

### Database Operations

```python
# Always use context managers
with sqlite3.connect("database.db") as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions")
    results = cursor.fetchall()

# Use parameterized queries (prevent SQL injection)
cursor.execute(
    "INSERT INTO sessions (name, score) VALUES (?, ?)",
    (name, score)  # Good (parameterized)
)

# Never use string formatting (SQL injection risk)
cursor.execute(
    f"INSERT INTO sessions VALUES ('{name}', {score})"  # Bad!
)
```

### Error Handling

```python
# Be specific with exceptions
try:
    with open(file_path) as f:
        data = json.load(f)
except FileNotFoundError:
    logger.error(f"File not found: {file_path}")
    # Provide fallback
    data = {}
except json.JSONDecodeError:
    logger.error(f"Invalid JSON: {file_path}")
    # Reset to defaults
    data = get_default_config()

# Log exceptions with context
except Exception as e:
    logger.exception(f"Unexpected error processing {file_path}: {e}")
    raise

# Use custom exceptions for domain errors
class CalibrationError(Exception):
    """Raised when calibration fails."""
    pass

if quality < threshold:
    raise CalibrationError("Calibration quality below threshold")
```

---

## Pull Request Process

### Before Submitting

1. **Test thoroughly**:
   ```powershell
   pytest tests/
   ```

2. **Format code**:
   ```powershell
   black modules/ utils/ tests/
   ```

3. **Check linting**:
   ```powershell
   flake8 modules/ utils/ tests/
   ```

4. **Update documentation**:
   - Add docstrings to new functions
   - Update API_DOCUMENTATION.md if API changed
   - Update CHANGELOG.md with your changes

5. **Update translations**:
   - Add new keys to en.json
   - Add Indonesian translations to id.json

### Submission Checklist

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New code has tests (aim for >80% coverage)
- [ ] Documentation updated
- [ ] Translations added
- [ ] No merge conflicts with develop branch
- [ ] Commit messages follow convention
- [ ] PR description is clear

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Screenshots
If UI changes, add screenshots

## Checklist
- [ ] Tests pass locally
- [ ] Code formatted with black
- [ ] Documentation updated
- [ ] Translations added

## Related Issues
Closes #123
```

### Review Process

1. **Automated checks**: CI runs tests and linting
2. **Code review**: Maintainer reviews code
3. **Revisions**: Address feedback if needed
4. **Approval**: Maintainer approves
5. **Merge**: Squash and merge to develop

---

## Reporting Bugs

### Before Reporting

1. **Search existing issues**: Check if already reported
2. **Try latest version**: Bug may be fixed
3. **Reproduce**: Ensure bug is reproducible

### Bug Report Template

```markdown
**Environment:**
- OS: Windows 10/11 (64-bit)
- Python version: 3.10.x
- Application version: 1.0.0

**Description:**
Clear description of the bug

**Steps to Reproduce:**
1. Step one
2. Step two
3. ...

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Error Messages:**
```
Paste error messages here
```

**Logs:**
Attach relevant log files from Logs/ folder

**Screenshots:**
If applicable, add screenshots

**Additional Context:**
Any other relevant information
```

---

## Suggesting Enhancements

### Enhancement Proposal Template

```markdown
**Feature Name:**
Brief name for the feature

**Problem Statement:**
What problem does this solve?

**Proposed Solution:**
How would you implement this?

**Alternatives Considered:**
Other approaches you thought about

**Additional Context:**
Mockups, examples, etc.
```

---

## Translation Contributions

### Adding New Language

1. **Create translation file**:
   ```bash
   cp assets/translations/en.json assets/translations/fr.json
   ```

2. **Translate all keys**:
   ```json
   {
     "app_title": "Logiciel de Suivi Oculaire",
     "menu": {
       "detection": "Détection",
       "game": "Jeu"
     }
   }
   ```

3. **Update language selector**:
   ```python
   # In settings_dialog.py
   LANGUAGES = {
       "en": "English",
       "id": "Bahasa Indonesia",
       "fr": "Français"  # Add new language
   }
   ```

4. **Test thoroughly**:
   - Ensure all UI text displays correctly
   - Check for text overflow
   - Verify special characters render properly

### Improving Existing Translations

1. **Find translation file**: `assets/translations/id.json`
2. **Update translations**: Improve clarity or accuracy
3. **Submit PR**: Include reason for changes

---

## Recognition

Contributors will be acknowledged in:

- CHANGELOG.md (version credits)
- README.md (contributors section)
- About dialog in application

Thank you for contributing! 🎉

---

**Questions?**

Contact: [Your contact information]

---

**Last Updated**: November 17, 2025
