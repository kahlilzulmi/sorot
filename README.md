# SOROT

**S**timulus **O**riented **R**egion-**o**f-interest **T**ool — a web application for academic and laboratory eye-tracking studies on video advertisements and other stimuli.

Define scenes and ROIs on video, import or record gaze data, and export metrics for neuromarketing and vision research.

## Features

- HTML5 video playback with frame-accurate scene boundaries
- Interactive ROI editor (position, size, labels, colors)
- Real-time gaze capture over WebSocket (live recording mode)
- Gaze CSV import and client-side extraction (Web Worker)
- Post-processing: fixations, ROI dwell time, validation overlays
- PDF/Excel report generation
- Optional OBS Studio control and YouTube stimulus download
- Workspace save/load (JSON projects)

## Screenshots

_Add screenshots or a short demo GIF before publishing — helps reviewers and collaborators._

## Quick start

### Requirements

- Python 3.10+
- Node.js 18+ (for the Vue frontend)

### Install

```bash
git clone https://github.com/kahlilzulmi/sorot.git
cd sorot

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt

cd frontend
npm install
cd ..
```

### Run (development)

```powershell
.\dev.ps1
```

- **App UI**: http://localhost:5173  
- **API / Socket.IO**: http://127.0.0.1:5000  

Or run the backend alone: `python sorot.py`

Copy `.env.example` to `.env` and set `FLASK_SECRET_KEY` before deploying beyond localhost.

### Verify installation

```bash
python tests/test_setup.py
```

## Repository layout

```
sorot/
├── sorot.py                 # Flask + Socket.IO application
├── gaze_post_processor.py   # Gaze analysis pipeline
├── report_generator.py      # PDF / Excel reports
├── app_launcher.py          # Desktop-style launcher (optional)
├── frontend/                # Vue 3 + Vite + TypeScript UI
├── tests/                   # Setup and integration tests
├── docs/                    # Architecture and contributor guides
├── templates/               # Legacy HTML UI (CDN Vue)
├── static/                  # Legacy assets; production build → static/dist/
└── projects/                # Workspace JSON (runtime; see example.workspace.json)
```

Runtime directories (`uploaded_videos/`, `sessions/`, etc.) are created automatically and are gitignored.

## Documentation

- [Contributing](CONTRIBUTING.md)
- [Architecture](docs/architecture.md)
- [Development](docs/development.md)
- [Socket.IO production](docs/socketio-production.md)

## Research use

SOROT is intended for controlled laboratory workflows. When publishing results, cite the tool and document your ROI definitions, gaze hardware, and sampling rate. Do not commit participant recordings or identifiable data to this repository.

## License

[MIT](LICENSE) — see file for copyright notice. Replace the copyright holder name in `LICENSE` with your laboratory or institution if required by your policy.

## Acknowledgments

Developed for academic laboratory video ROI and gaze analysis. Contributions welcome via [CONTRIBUTING.md](CONTRIBUTING.md).
