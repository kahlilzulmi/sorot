# SOROT

**S**timulus **O**riented **R**egion-**o**f-interest **T**ool — a web application for academic and laboratory eye-tracking studies on video advertisements and other stimuli.

The primary interface is a **Vue 3 + Vite + TypeScript** single-page app (`frontend/`) talking to a **Flask + Socket.IO** API (`sorot.py`). Define scenes and ROIs, import or record gaze data, and export metrics for neuromarketing and vision research.

## Features

- HTML5 video playback with frame-accurate scene boundaries
- Interactive ROI editor (position, size, labels, colors)
- Real-time gaze capture over WebSocket (live recording mode)
- Gaze CSV import and client-side extraction (Web Worker)
- Post-processing: fixations, ROI dwell time, validation overlays
- PDF/Excel report generation
- Optional OBS Studio control and YouTube stimulus download
- Workspace save/load (JSON projects)

## Quick start with Docker

The fastest way to run SOROT with the production Vue UI (no local Node.js required):

```bash
git clone https://github.com/kahlilzulmi/sorot.git
cd sorot
docker compose up --build
```

Open **http://localhost:5000**

Set a real secret for anything beyond localhost:

```bash
FLASK_SECRET_KEY=your-long-random-string docker compose up --build
```

Data (videos, sessions, workspaces) is stored in Docker volumes and persists across restarts.

Plain Docker:

```bash
docker build -t sorot .
docker run --rm -p 5000:5000 -e FLASK_SECRET_KEY=change-me sorot
```

## Development (Vue + Flask)

### Requirements

- Python 3.10+
- Node.js 18+

### Install

```bash
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

Copy `.env.example` to `.env` and set `FLASK_SECRET_KEY` when needed.

### Run

```powershell
.\dev.ps1
```

| Service | URL |
|---------|-----|
| **Vue UI (use this)** | http://localhost:5173 |
| Flask API / Socket.IO | http://127.0.0.1:5000 |

Vite proxies API and WebSocket traffic to Flask.

### Production-style local run (single port)

Build the frontend and serve it from Flask on port 5000:

```bash
cd frontend && npm run build && cd ..
python sorot.py
```

Open **http://localhost:5000**

### Verify installation

```bash
python tests/test_setup.py
```

## Repository layout

```
sorot/
├── sorot.py                 # Flask + Socket.IO API
├── frontend/                # Vue 3 + Vite UI (primary)
├── static/dist/             # Production build output (gitignored; created by npm run build)
├── legacy/                  # Archived CDN-Vue UI (see legacy/README.md)
├── gaze_post_processor.py   # Gaze analysis pipeline
├── report_generator.py      # PDF / Excel reports
├── tests/                   # Setup and integration tests
├── docs/                    # Architecture and deployment guides
└── projects/                # Workspace JSON (runtime; see example.workspace.json)
```

Runtime directories (`uploaded_videos/`, `sessions/`, etc.) are created automatically and are gitignored.

## Legacy UI

The pre-Vite interface lives under `legacy/` and is served at **http://localhost:5000/legacy/** when the backend is running. Do not add new features there; use `frontend/` instead.

## Documentation

- [Contributing](CONTRIBUTING.md)
- [Architecture](docs/architecture.md)
- [Development](docs/development.md)
- [Socket.IO production](docs/socketio-production.md)

## Research use

SOROT is intended for **educational and laboratory research** only. When publishing results, cite the tool and document your ROI definitions, gaze hardware, and sampling rate. Do not commit participant recordings or identifiable data to this repository.

Automating or analyzing commercial eye-tracking overlays (including Tobii Ghost) may conflict with vendor EULAs — you are responsible for compliance. See [NOTICE](NOTICE) for trademark disclaimers, third-party licenses, and algorithm attributions.

## License

[MIT](LICENSE) — third-party notices and disclaimers in [NOTICE](NOTICE).

## Acknowledgments

Developed for academic laboratory video ROI and gaze analysis. Contributions welcome via [CONTRIBUTING.md](CONTRIBUTING.md).
