# Architecture

SOROT is a web application for defining **regions of interest (ROIs)** on advertisement or stimulus videos, aligning **eye-gaze** data with those ROIs, and exporting metrics for neuromarketing / vision research.

## Components

```mermaid
flowchart LR
  subgraph browser [Browser]
    Vue[Vue 3 + Vite UI]
    Worker[Analyzer Web Worker]
    Vue --> Worker
  end
  subgraph server [Python]
    Flask[Flask + Socket.IO]
    PP[GazePostProcessor]
    RG[ReportGenerator]
    Flask --> PP
    Flask --> RG
  end
  Vue <-->|REST / WebSocket| Flask
  Flask --> FS[(uploaded_videos / sessions / projects)]
```

| Layer | Technology | Role |
|-------|------------|------|
| UI | Vue 3, TypeScript, Tailwind, Pinia | Video playback, ROI editor, gaze import, workspace save/load |
| Real-time | Socket.IO | Live gaze streaming during recording sessions |
| API | Flask (`sorot.py`) | Uploads, workspace persistence, post-processing, reports |
| Analysis | OpenCV, NumPy, Pandas | Server-side gaze post-processing and validation |
| Optional | OBS WebSocket, yt-dlp | Live capture and YouTube stimulus download |

## Development vs production UI

- **Development**: Vite serves `frontend/` on port 5173 and proxies `/api`, `/socket.io`, and video paths to Flask on port 5000.
- **Production build**: `cd frontend && npm run build` emits assets to `static/dist/`; configure Flask to serve the Vite manifest (or deploy frontend and API behind one reverse proxy).
- **Legacy UI**: `templates/index.html` + `static/js/app.js` is an older CDN-based interface. New features belong in `frontend/`.

## Data on disk

| Directory | Gitignored | Contents |
|-----------|------------|----------|
| `uploaded_videos/` | Yes | User-uploaded stimulus files |
| `downloaded_videos/` | Yes | yt-dlp downloads |
| `sessions/` | Yes | Per-session gaze recordings and exports |
| `projects/` | Mostly | Workspace JSON (see `example.workspace.json`) |

## Further reading

- [Development setup](development.md)
- [Socket.IO production](socketio-production.md)
- [Vite migration notes](vite-migration.md)
