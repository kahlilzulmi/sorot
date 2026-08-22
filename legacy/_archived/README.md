# Archived legacy editor assets

Moved here instead of deleted (2026-05-20).

| Path | Was |
|------|-----|
| `templates/index.html` | Main legacy CDN-Vue editor shell |
| `templates/settings.html` | Legacy settings page (migrated to `frontend/src/components/settings/`) |
| `static/js/app.js` | Legacy editor logic (~2900 lines) |
| `static/css/app.css` | Legacy editor styles (canonical copy lives in `frontend/src/styles/app.css`) |

Still active under `legacy/`:

- `templates/test_roi_gaze.html` — gaze/ROI test page (`/legacy/test-gaze`)
- `tests/test_roi_gaze_webapp.py` — standalone test server

Routes:

- `/legacy/` → redirects to `/`
- `/legacy/settings` → redirects to `/settings`
