# SOROT — Legacy Editor → Vue 3 + Vite Roadmap

This roadmap tracks **restoring full video-editor parity** in the Vite app (`frontend/`) so production and Docker at `http://localhost:5000/` match the experience previously available at `/legacy/`, without relying on the archived CDN stack.

**Why this exists:** The full editor UI was extracted into Vue SFCs (`ModeSelector`, `VideoWorkspace`, scene/ROI sidebars, etc.), but `App.vue` currently mounts a **minimal** shell (`ControlSidebar` + `VideoPlayerCanvas`). Legacy behavior lives in `legacy/` and is still served at `/legacy/` for reference.

**Goal:** `/` (Vite build + Flask) = full editor. Deprecate `/legacy/` after parity.

---

## Current state

| Area | Status |
|------|--------|
| Extracted components | `ModeSelector`, `AppHeader`, `StatusBar`, `SceneSidebar`, `RoiSidebar`, `VideoWorkspace`, `PlaybackControls`, partial modals |
| Root app | `App.vue` = minimal prototype only |
| Legacy styles | `frontend/src/styles/app.css` exists but **`main.ts` does not import it** — many SFCs use legacy class names |
| State model | `useWorkspaceState` (modes, navigation) + `useGazeStore` (flat ROIs) vs **legacy scene-nested** `scenes[].rois[]` |
| Backend | Unchanged: `sorot.py` Flask + Socket.IO + `/api/*` |

### Key files

| Role | Path |
|------|------|
| Legacy markup | `legacy/templates/index.html` |
| Legacy logic | `legacy/static/js/app.js` |
| Legacy styles | `legacy/static/css/app.css` |
| Vite entry | `frontend/src/main.ts`, `frontend/src/App.vue` |
| Component map | `docs/vite-componentization.md` |
| Extraction process | `docs/extraction-workflow.md` |
| Architecture | `docs/architecture.md` |
| Workspace types | `frontend/src/types/workspace.ts` |

---

## Phase 0 — Visual foundation

**Outcome:** Full three-column shell + mode selector visible (styling matches legacy intent).

- [ ] Import `frontend/src/styles/app.css` from `main.ts` (coordinate with Tailwind in `style.css` so utilities still work).
- [ ] Replace minimal `App.vue` with an **orchestrator** that mounts:
  - `ModeSelector` when `appMode === 'select'`
  - Else: `AppHeader` + `SceneSidebar` + `VideoWorkspace` + `RoiSidebar` + `StatusBar` + modals (stub handlers OK initially).
- [ ] Smoke: layout renders; no blank/unstyled regions.

---

## Phase 1 — Core editor loop (P0)

**Outcome:** Video, scenes, per-scene ROIs, timeline, and frame controls wired to real state and APIs.

| Deliverable | Notes |
|-------------|--------|
| Typed API layer | `fetch` wrapper for `/api/*` (replace legacy axios patterns) |
| Socket layer | `socket.io-client` for live gaze / recording events |
| Video session | `videoInfo`, `videoSrc`, `currentFrame`, play/pause, seek, metadata |
| Scenes | CRUD, active scene, boundaries; sync `GET`/`POST /api/scenes` |
| ROI editor | Per-**active-scene** `rois[]`; wire `useRoiCanvas` to scene ROIs, not only flat Pinia list |
| Layout | Use `videoLayout.ts` (or equivalent) so ROI canvas aligns with letterboxed video |
| History | Undo/redo from legacy patterns |

**References:** `legacy/static/js/app.js` (`data()`, `methods`), `sorot.py` routes for video, scenes, thumbnails.

---

## Phase 2 — Modes (P0)

**Outcome:** Live and Import flows usable end-to-end like legacy.

- [ ] **Import:** CSV + video + optional gaze video + frame offset; column mapping; reuse `parseGazeCsv.ts` where applicable; dual-video sync if legacy had it.
- [ ] **Live:** Recording start/stop, overlay, Socket.IO gaze stream; APIs under `/api/recording/*`.
- [ ] **Tobii overlay path:** Integrate `VideoAnalyzer.vue` + `analyzerWorker.ts` where auto-extraction applies; align with gaze coordinate model.

---

## Phase 3 — Modals & toolbar (P1)

**Outcome:** Header actions and modals match legacy coverage.

Extract missing modals from `legacy/templates/index.html` into `frontend/src/components/modals/`:

- [ ] RecordModal  
- [ ] ProcessModal  
- [ ] ImportModal  
- [ ] RoiNameModal  
- [ ] ProgressModal  
- [ ] ObsFilePickerModal  

Wire `AppHeader` (and any overflow menus) to: New, Open, Save, Save As, Export, Record, Process, dual-video toggle, etc., per legacy.

---

## Phase 4 — Post-processing & export (P1)

- [ ] Post-processing flow + progress polling (`/api/processing/*`).
- [ ] Export scenes + ROIs (`/api/export-scenes-rois` and related).
- [ ] Reports list/download where legacy exposed them.
- [ ] Client-side metrics where appropriate: `gazeRoi.ts`, `exportMetricsCsv.ts` (15px margin: `GAZE_POSITION_MARGIN_PX`); server paths for heatmaps/overlays as today.

---

## Phase 5 — Cleanup & deprecation (P2)

- [ ] Merge or remove minimal-only UI: `ControlSidebar.vue` / `VideoPlayerCanvas.vue` — keep valuable pieces (e.g. IndexedDB restore, extraction toggles) inside the full shell if still needed.
- [ ] **Single ROI model:** Prefer `scenes[].rois[]` + API alignment; narrow `useGazeStore` to gaze samples + playback + UI glue, or document a clear split.
- [ ] Update `README.md`: `/` = primary editor; `/legacy/` = archived reference until removed.
- [ ] Add `docs/MIGRATION_STATUS.md` (optional) with checkbox progress and known gaps.
- [ ] CI: `npm run type-check && npm run build`; Docker `docker compose up --build` smoke on `http://localhost:5000/`.

---

## Parity checklist (before “done”)

Side-by-side: **Vite app** vs **`/legacy/`** with the same workspace video.

- [ ] Mode selection (Live / Import)
- [ ] Header: New, Load, Save, Save As, Export, Record, Process, back to modes
- [ ] Scene sidebar: list, thumbnails, rename, delete, active scene
- [ ] Video + ROI canvas: draw, move, resize, select ROI
- [ ] Scene timeline: segments, playhead, scene selection
- [ ] Playback: play/pause, prev/next frame, prev/next scene, split/merge, undo/redo
- [ ] ROI sidebar: per-scene list, rename, delete
- [ ] Import: CSV + video + gaze video + offset as applicable
- [ ] Live: Socket.IO gaze overlay + recording
- [ ] Workspace save/load JSON
- [ ] Post-processing + progress UI
- [ ] **Docker:** `http://localhost:5000/` shows full editor (not minimal sidebar-only)

---

## Engineering constraints

From `.cursorrules` and project norms:

- Vue 3 **Composition API** with `<script setup lang="ts">` only (no Options API in new code).
- **Strict TypeScript** — no `any`.
- **Client-only** for gaze CSV parsing, worker CV, and in-browser metrics; Flask remains source of truth for uploads, recording, and server-side processing.
- **Web Workers** for heavy per-frame detection (`analyzerWorker.ts`).
- **~15px** gaze-to-ROI tolerance in client ROI logic (`gazeRoi.ts`).

Do **not** reintroduce CDN-loaded Vue/axios/socket scripts in HTML.

---

## Verification commands

```bash
# Dev: Vite + Flask (see README / dev.ps1)
cd frontend && npm run dev:all

# Compare
# http://localhost:5173/        ← target: full editor
# http://localhost:5000/legacy/  ← reference

# Production-style
cd frontend && npm run build && cd ..
python sorot.py
# http://localhost:5000/

# Docker
docker compose up --build
# http://localhost:5000/
```

---

## Suggested PR slicing

1. **PR1:** Phase 0 — styles + shell `App.vue` (mostly layout, stub actions).  
2. **PR2:** Phase 1 — API + scenes + ROI on canvas + video session.  
3. **PR3:** Phase 2 — Import + Live + analyzer integration.  
4. **PR4:** Phase 3 — Modals + header completeness.  
5. **PR5:** Phase 4 — Processing + export + reports.  
6. **PR6:** Phase 5 — Deprecate minimal UI, docs, migration status.

---

## Related documentation

- [Architecture](docs/architecture.md) — URLs, Docker, legacy path  
- [Vite componentization](docs/vite-componentization.md) — block → component map  
- [Extraction workflow](docs/extraction-workflow.md) — read → move → modify → check  
- [Legacy README](legacy/README.md) — archived UI scope  

---

*Last updated: roadmap created from legacy→Vite migration plan. Update this file as phases complete.*
