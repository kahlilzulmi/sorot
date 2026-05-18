# Development

## Quick start (Vue + Flask)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd frontend; npm install; cd ..
.\dev.ps1
```

Open http://localhost:5173 (not :5000 — that port is API-only in dev).

## Docker (production-like, single port)

```bash
docker compose up --build
```

Open http://localhost:5000.

## Environment variables

Copy `.env.example` to `.env` and set `FLASK_SECRET_KEY` before any shared or production deployment. OBS connection settings can live in `.env` or in the legacy **Settings** page at `/legacy/settings`.

| Variable | Default | Purpose |
|----------|---------|---------|
| `FLASK_SECRET_KEY` | dev placeholder | Session signing |
| `FLASK_DEBUG` | `true` locally, `0` in Docker | Flask debug mode |

## Useful commands

| Command | Description |
|---------|-------------|
| `python sorot.py` | Flask backend on :5000 |
| `cd frontend && npm run dev` | Vite frontend on :5173 |
| `cd frontend && npm run dev:all` | Backend + frontend via `concurrently` |
| `cd frontend && npm run build` | Production bundle → `static/dist/` |
| `cd frontend && npm run type-check` | Vue/TS type check |
| `python tests/test_setup.py` | Dependency and layout smoke test |
| `docker compose up --build` | Full stack with built Vue UI |

## Tests

Scripts under `tests/` are run directly with Python:

```bash
python tests/test_setup.py
python tests/test_roi_api.py
```

Legacy gaze test server: `python legacy/tests/test_roi_gaze_webapp.py` (port 5001).

## Optional features

Install all of `requirements.txt` for OBS and YouTube support. If imports fail, `test_setup.py` reports warnings and the app still runs without those integrations.
