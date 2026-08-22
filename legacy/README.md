# Legacy web UI (archived)

The legacy editor is archived under `_archived/`. **`/legacy/` redirects to `/`**.

| URL | Status |
|-----|--------|
| `/` | Primary Vue 3 editor |
| `/settings` | Settings and diagnostics (Vue) |
| `/legacy/settings` | Redirects to `/settings` |
| `/legacy/test-gaze` | ROI/gaze connection test page (still served) |

New development: **`frontend/`** only.

## Standalone gaze test server

```bash
python legacy/tests/test_roi_gaze_webapp.py
```

Opens the ROI/gaze connection test page on port 5001.
