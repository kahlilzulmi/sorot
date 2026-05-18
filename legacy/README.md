# Legacy web UI

Pre-Vite interface built with CDN Vue 3, Jinja templates, and `static/js/app.js`.

- **URL**: http://localhost:5000/legacy/ (when the Flask backend is running)
- **Settings**: http://localhost:5000/legacy/settings

New development should use the Vue 3 app in `frontend/`. This tree is kept for reference and gradual migration of any remaining features.

## Standalone gaze test server

```bash
python legacy/tests/test_roi_gaze_webapp.py
```

Opens the ROI/gaze connection test page on port 5001.
