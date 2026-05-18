# Development

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd frontend; npm install; cd ..
.\dev.ps1
```

Open http://localhost:5173.

## Environment variables

Copy `.env.example` to `.env` and set `FLASK_SECRET_KEY` before any shared or production deployment. OBS connection settings can live in `.env` or in the in-app **Settings** page.

## Useful commands

| Command | Description |
|---------|-------------|
| `python sorot.py` | Flask backend on :5000 |
| `cd frontend && npm run dev` | Vite frontend on :5173 |
| `cd frontend && npm run dev:all` | Backend + frontend via `concurrently` |
| `cd frontend && npm run build` | Production bundle → `static/dist/` |
| `cd frontend && npm run type-check` | Vue/TS type check |
| `python tests/test_setup.py` | Dependency and layout smoke test |
| `python app_launcher.py` | Opens browser to legacy :5000 entry (packaged builds) |

## Tests

Scripts under `tests/` are run directly with Python (not a unified pytest suite yet):

```bash
python tests/test_setup.py
python tests/test_roi_api.py
```

Add new tests alongside existing files and document any required sample media in the test module docstring.

## Optional features

Install all of `requirements.txt` for OBS and YouTube support. If imports fail, `test_setup.py` reports warnings and the app still runs without those integrations.
