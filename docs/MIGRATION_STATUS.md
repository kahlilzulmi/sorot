# SOROT Vite migration status

Last updated: 2026-05-20

Reference UI: `http://localhost:5000/legacy/`  
Target UI: `http://localhost:5173/` (dev) and `http://localhost:5000/` (production build)

## Parity checklist

| Feature | Legacy | Vite | Notes |
|---------|--------|------|-------|
| Mode selection (Live / Import) | Yes | Yes | Phase 0 |
| Header: New, Load, Save, Save As | Yes | Yes | Phase 0–1 |
| Header: Export CSV/JSON | Yes | Partial | API wired; dropdown UI simplified |
| Header: Record, Post-process (live) | Yes | Stub | Opens modal flags; modals not extracted |
| Header: Import / reports (import) | Yes | Stub | `showImportModal` flag only |
| Scene sidebar | Yes | Yes | Rename via prompt (legacy inline edit pending) |
| Video + ROI canvas | Yes | Partial | Canvas uses Pinia flat ROIs, not `scene.rois[]` |
| Scene timeline + frame slider | Yes | Yes | Phase 0–1 |
| Playback controls | Yes | Yes | Play/pause, frame/scene navigation |
| Split / merge scenes | Yes | Yes | Phase 1 |
| Undo / redo | Yes | Yes | Phase 1 |
| ROI sidebar (per scene) | Yes | Partial | List works; draw sync to scenes pending |
| Import flow (CSV, gaze video) | Yes | No | Phase 2 |
| Live recording + Socket.IO | Yes | Partial | Socket connect only; record UI pending |
| Workspace save/load | Yes | Yes | Phase 1 |
| Post-processing modal + progress | Yes | No | Phase 3–4 |
| Docker `/` full editor shell | Yes | Yes | After `npm run build` |

## Completed phases

### Phase 0 — Visual foundation
- [x] `main.ts` imports `styles/app.css` (legacy editor theme)
- [x] `App.vue` orchestrates ModeSelector, AppHeader, 3-column `container`, StatusBar
- [x] Modals: NewVideoModal, SaveAsModal

### Phase 1 — Core editor loop (partial)
- [x] `useApiClient.ts` — typed `fetch` for `/api/*`
- [x] `useVideoSession.ts` — upload, YouTube, playback state
- [x] `useScenes.ts` — scenes CRUD, timeline index, split/merge, API sync
- [x] `useHistory.ts` — undo/redo stack
- [x] `useWorkspaceFiles.ts` — save, save-as, import, export
- [x] `useSocket.ts` — Socket.IO client scaffold
- [ ] `useRoiEditor.ts` — per-scene ROI draw (still on Pinia via `useRoiCanvas`)

## Known gaps (priority)

1. **ROI model**: `useRoiCanvas` / `useGazeStore` flat list vs `scenes[].rois[]` — must unify on scene-nested ROIs.
2. **Missing modals**: RecordModal, ProcessModal, ImportModal, RoiNameModal, ProgressModal, ObsFilePickerModal.
3. **Import mode**: CSV mapping, frame offset, dual-video — not ported.
4. **Live mode**: recording loop, gaze overlay, post-process polling.
5. **Minimal prototype**: `ControlSidebar.vue` / `VideoPlayerCanvas.vue` retained but unmounted; merge IndexedDB restore later.

## Verification

```bash
cd frontend && npm run dev:all
# Compare http://localhost:5173/ vs http://localhost:5000/legacy/

cd frontend && npm run build && cd ..
docker compose up --build
# http://localhost:5000/ should show mode selector + editor shell (not minimal sidebar)
```
