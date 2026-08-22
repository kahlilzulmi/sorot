# SOROT Vite migration status

Last updated: 2026-05-20

**Primary UI:** `http://localhost:5173/` (dev) and `http://localhost:5000/` (production)  
**Settings:** `/settings`  
**Legacy:** `/legacy/` → `/`; editor assets archived under `legacy/_archived/`

## Migration complete

Phases 0–5 are done. The Vite editor is the sole supported UI.

### Phase 5 — Cleanup, archive & cutover
- [x] Gaze-only Pinia store + `useGazePersistence`
- [x] Legacy editor archived (`legacy/_archived/`) — not deleted
- [x] Prototype Vue archived (`frontend/src/_archived/prototype/`)
- [x] Settings migrated to `SettingsView.vue` at `/settings`
- [x] `/legacy/` and `/legacy/settings` redirect to Vue routes
- [x] README + docs updated

## Verification

```bash
cd frontend && npm run dev:all
# http://localhost:5173/
# http://localhost:5173/settings

cd frontend && npm run build && cd ..
python sorot.py
# http://localhost:5000/
# http://localhost:5000/settings
```
