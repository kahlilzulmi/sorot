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

Copy `.env.example` to `.env` and set `FLASK_SECRET_KEY` before any shared or production deployment. OBS connection settings can live in `.env` or in the app **Settings** page at `/settings`.

| Variable | Default | Purpose |
|----------|---------|---------|
| `FLASK_SECRET_KEY` | dev placeholder | Session signing |
| `FLASK_DEBUG` | `true` locally, `0` in Docker | Flask debug mode |
| `PORT` | `5000` | HTTP port (`sorot.py`); Render injects this automatically |

## Deploy on Render (Docker)

Full stack on one Web Service — Vue UI, Flask API, and Socket.IO.

### Option A — Blueprint (`render.yaml`)

1. Push this repo (includes `render.yaml` on `dev`).
2. Render dashboard → **New** → **Blueprint** → connect the repo.
3. Set `FLASK_SECRET_KEY` if not using `generateValue: true`.
4. Deploy; open the `*.onrender.com` URL.

### Option B — Manual Web Service

| Setting | Value |
|---------|-------|
| Runtime | **Docker** |
| Dockerfile path | `./Dockerfile` |
| Branch | `dev` or `main` |
| Health check path | `/health` |
| `FLASK_SECRET_KEY` | long random string |
| `FLASK_DEBUG` | `0` |

Do **not** hard-code port `5000` in Render — the platform sets `PORT`; `sorot.py` reads it.

### Render limits to know

- **Free tier:** service sleeps after idle; first request may take 30–60s (cold start).
- **Ephemeral disk:** uploads, sessions, and projects are lost on redeploy unless you add a [Render disk](https://render.com/docs/disks) (paid).
- **OBS / Tobii:** run on the researcher’s local machine; use Import mode on the hosted instance for remote work.
- **Socket.IO:** works on a single Render Web Service; avoid splitting frontend and API across hosts.

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
