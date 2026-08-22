# Project Memory

## 2026-05-20 — Phase 1 ROI model decision
- What was decided: ROI editing in the Vite editor now uses `scenes[].rois[]` as the single source of truth via `useRoiEditor.ts` + adapter-based `useRoiCanvas.ts`.
- Why: Legacy behavior and backend `/api/scenes` persistence are scene-centric, while flat Pinia ROIs caused mismatch between canvas edits and scene data.
- What was rejected and why: Continuing with flat `useGazeStore.regionsOfInterest` for editor ROI state was rejected because it breaks parity and requires duplicate synchronization logic.

## 2026-05-20 — Gaze session unification decision
- What was decided: Introduce `useGazeSession.ts` as the runtime gaze source for overlay rendering (imported gaze samples + live socket gaze), and feed overlay into `useRoiCanvas`.
- Why: This decouples editor overlay behavior from legacy flat Pinia ROI/gaze coupling and creates one place to drive gaze visualization.
- What was rejected and why: Keeping overlay sampling directly inside canvas/store internals was rejected because it fragments ownership and makes Import/Live parity harder to complete.

## 2026-05-20 — Live-first Phase 2 execution decision
- What was decided: Implement live recording control in-app now (record prepare overlay, start `/api/recording/start`, frame sync via `record_frame`, stop `/api/recording/stop`) using `useLiveRecording.ts`.
- Why: This delivers visible live-mode parity earlier and keeps roadmap momentum while import mode and modal extraction are deferred.
- What was rejected and why: Waiting for full modal extraction before wiring live APIs was rejected because it delays core behavior parity without technical need.

## 2026-05-20 — Import mode Phase 2 (core) decision
- What was decided: Import flow uses `useImportMode` + `ImportModal` with manual column mapping, timestamp normalization, frame offset, direct hydration into `useGazeSession`, and backend sync via `/api/import-gaze-data`.
- Why: Delivers usable import-mode parity without waiting for dual-video/auto-detect complexity.
- What was rejected and why: Keeping an ongoing Pinia bridge watch as the gaze source was rejected; import now writes directly to gaze session on apply (IndexedDB restore on startup only).

## 2026-05-20 — Phase 3 modals decision
- What was decided: Extract all legacy modals into Vue SFCs (`RecordModal`, `ProcessModal`, `RoiNameModal`, `ProgressModal`, `ObsFilePickerModal`) with `usePostProcessing.ts` for API orchestration. ROI draw opens naming modal before persisting. Record header opens disclaimer modal first. Auto post-processing pipeline runs after recording stop when manual import is not required.
- Why: Matches legacy UX flow, prevents unnamed ROIs, and completes live-mode post-process path without blocking on Phase 4 export polish.
- What was rejected and why: Immediate ROI auto-add on mouse-up was rejected to preserve legacy naming step and clearer user intent.

## 2026-05-20 — Phase 4 import depth decision
- What was decided: Extend import with auto-detect tab (`processAutoDetect`), optional gaze video upload for CSV path, `useDualVideo` side-by-side sync with frame offset controls, Generate Reports header action, export dropdown, inline scene rename, status bar session info.
- Why: Closes remaining import-mode parity gaps without waiting for Phase 5 cleanup; dual-video sync is essential for eyegaze/stimulus alignment validation.
- What was rejected and why: Client-only auto-detect in browser was rejected; backend Hough pipeline already exists and matches legacy behavior.

## 2026-05-20 — Phase 5 cutover decision
- What was decided: Slim `useGazeStore` to gaze-only + IndexedDB; ROIs only in `scenes[].rois[]`; `useGazePersistence` for restore/hydrate; `/legacy/` redirects to `/`; prototype components excluded from type-check; settings stay at `/legacy/settings` until migrated.
- Why: Completes migration cutover without deleting files yet; avoids dual ROI sources; keeps OBS settings usable.
- What was rejected and why: Deleting `legacy/` and prototype Vue files was rejected; files moved to `_archived/` instead.

## 2026-05-20 — Archive + settings migration decision
- What was decided: Move legacy editor assets to `legacy/_archived/`, prototype Vue to `frontend/src/_archived/prototype/`, migrate settings to `SettingsView.vue` at `/settings`, redirect `/legacy/settings` → `/settings`.
- Why: User requested archive-not-delete plus full settings migration into Vite.
- What was rejected and why: Keeping Bootstrap settings.html as the primary settings surface was rejected after Vue parity was implemented.

## 2026-08-23 — Empty JS stubs shadowing TypeScript composables
- What was decided: Move zero-byte `useHistory.js` (and sibling empty `.js` files) from `src/composables/` to `src/_archived/empty-js-stubs/` so Vite resolves the real `.ts` modules.
- Why: Vite prefers `.js` over `.ts` for extensionless imports; empty stubs caused `does not provide an export named 'useHistory'`.
- What was rejected and why: Leaving the stubs in place or deleting without archive was rejected; archive preserves evidence of the failure mode.

## 2026-08-23 — Gaze device selection (phased)
- What was decided: Phase 1 — frontend device registry (`types/gazeDevice.ts`), `GazeDeviceSelector` in settings, localStorage persistence, mouse fallback default, Tobii ET5 + major trackers as catalog entries, custom device add/remove. Defer Tobii Ghost overlay test card; device-aware tests in selector.
- Why: User wants vendor-neutral device choice with extensibility (webcam/custom later) without hard-coding Tobii-only UX.
- What was rejected and why: Single Tobii-only settings card and immediate backend SDK integrations — deferred to Phase 2–4.
- Phases planned: (2) persist `gaze_device_id` in backend config, (3) route live gaze by transport (mouse, overlay, WebGazer), (4) custom device pipeline hooks.

## 2026-08-23 — Settings page “CSS gone” restyle
- What was decided: Restyle `SettingsView` / `SettingsTestCard` with scoped dark theme tokens and dedicated `settings-field` / `settings-input` (column layout). Keep global `app.css` loaded from `main.ts`.
- Why: Settings looked broken (huge dark inputs, light bg, poor contrast) because light fallback + global horizontal `.input-group` / `.input-text` fought the dark editor theme—not because CSS failed to load entirely.
- What was rejected and why: Relying on Bootstrap/legacy form classes or global `.input-group` for settings fields was rejected; those stretch inputs and clash with dark `.btn` / panel colors.
