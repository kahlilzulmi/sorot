# Contributing to SOROT

Thank you for helping improve this laboratory video ROI and gaze analysis tool. This guide covers local setup and what we expect in pull requests.

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** (for the Vue frontend)
- Optional: [OBS Studio](https://obsproject.com/) with WebSocket plugin for live recording

## Local development

```bash
# Backend dependencies
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
cd ..
```

Run backend and frontend together (recommended):

```powershell
.\dev.ps1
```

- Frontend: http://localhost:5173 (Vite dev server, proxies API to Flask)
- Backend: http://127.0.0.1:5000

Or run separately:

```bash
python sorot.py          # backend only
cd frontend && npm run dev
```

Verify your environment:

```bash
python tests/test_setup.py
```

## Project layout

| Path | Purpose |
|------|---------|
| `sorot.py` | Flask + Socket.IO API and session handling |
| `frontend/` | Vue 3 + Vite + TypeScript UI |
| `gaze_post_processor.py`, `report_generator.py` | Analysis and export |
| `tests/` | Integration and setup checks |
| `docs/` | Architecture notes and migration guides |
| `legacy/` | Archived CDN-Vue UI; prefer `frontend/` for all new work |

See [docs/architecture.md](docs/architecture.md) for how the pieces connect.

## Code guidelines

- **Frontend**: Vue 3 Composition API with `<script setup lang="ts">`, strict typing, Tailwind for styling. See `.cursorrules` for detailed conventions.
- **Gaze / video processing in the browser** must stay client-side; use Web Workers for heavy frame work.
- **Backend**: Keep API routes in `sorot.py` focused; extract reusable logic into modules when it grows.
- Match existing naming and file structure; avoid drive-by refactors in the same PR as a feature fix.

## What not to commit

- Videos, gaze CSVs, or session exports (`uploaded_videos/`, `downloaded_videos/`, `sessions/`)
- Personal workspace files under `projects/` (only `example.workspace.json` is tracked)
- Secrets (`.env`, OBS passwords, API keys)
- `node_modules/`, `static/dist/`, virtualenvs

## Pull requests

1. Open an issue or comment on an existing one for large changes.
2. Use a focused branch and a clear title (e.g. `fix: roi hit detection at scene boundaries`).
3. Describe **what** changed and **why**; include screenshots for UI changes.
4. Run `python tests/test_setup.py` and, for frontend changes, `cd frontend && npm run type-check`.
5. Ensure CI-relevant tests pass if you add or change `tests/test_*.py`.

## Questions

Open a [GitHub issue](https://github.com/kahlilzulmi/sorot/issues) for bugs, feature ideas, or lab-specific deployment questions.
