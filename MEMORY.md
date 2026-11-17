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

## 2026-08-24 — WebGazer.js live gaze (Phase 3)
- What was decided: Add `webgazer` npm dependency + `useWebGazer.ts` singleton (ref-counted start/stop, dynamic import, hidden preview). Wire into `useGazePoint` for cognitive games and `App.vue` for editor overlay when Settings device transport is `webgazer`. Device test starts WebGazer and reports success/failure.
- Why: User asked to finish the WebGazer.js phase (gaze device routing Phase 3).
- What was rejected and why: Separate gaze source picker in cognitive settings (already removed); loading WebGazer on every page load (lazy import on first use instead).

## 2026-08-24 — WebGazer hardening + mode selector settings
- What was decided: Alias Vite to `webgazer/dist/webgazer.js` (fixes `(void 0) is not a constructor` from raw ESM src). Add `shutdown()` (`stopVideo` + `end`, ref-count reset) when device transport ≠ `webgazer`. Device test no longer starts camera separately. Mode selector gets Settings button → `/settings`.
- Why: User reported constructor error, webcam staying on when deselected, and wanted settings access from mode select.
- What was rejected and why: Keeping `optimizeDeps.include` for webgazer src (caused broken constructor interop).

## 2026-08-23 — Cognitive hub mouse + math modules
- What was decided: Games hub uses normal mouse (no hide-OS-cursor / no dwell cursor). Dwell + eye-tracker cursor only after entering a game. Catalog includes UFYP math modules: `math-true-false` (Benar/Salah) and `math-fill-blank` (2×2 grid), ahead of Face / Visual Search / Memory.
- Why: Hub is navigation, not an eye-tracked trial; math games were in the reference set but missing from Phase 1 catalog.
- What was rejected and why: Keeping dwell cursor on the hub was rejected — it fights mouse UX before a session starts.
- What was decided: Option C fullscreen game shell; mode select adds Cognitive Games; hub supports playlist order (editable) or single-game pick; dwell cursor is settings-selectable (arrow/dot/ring/pie + color); CSS-only dwell animation; default dwell 1000ms (Visual Search 3000ms); gaze source selectable (mouse live in Phase 1; socket/tobii/webgazer stubs); operator hotkeys Q/S from day one.
- Why: Matches UFYP math-game shell pattern and reference images in `new-game/`, keeps editor chrome isolated, and lets experimenters configure cursor without shipping full modules yet.
- What was rejected and why: Pinia-heavy Option A and composable-only Option B deferred; embedding games inside editor chrome rejected for visual isolation.

## 2026-08-23 — Settings page “CSS gone” restyle
- What was decided: Restyle `SettingsView` / `SettingsTestCard` with scoped dark theme tokens and dedicated `settings-field` / `settings-input` (column layout). Keep global `app.css` loaded from `main.ts`.
- Why: Settings looked broken (huge dark inputs, light bg, poor contrast) because light fallback + global horizontal `.input-group` / `.input-text` fought the dark editor theme—not because CSS failed to load entirely.
- What was rejected and why: Relying on Bootstrap/legacy form classes or global `.input-group` for settings fields was rejected; those stretch inputs and clash with dark `.btn` / panel colors.

## 2026-08-23 — Cognitive hub mouse + math modules
- What was decided: Games hub uses normal mouse (no hide-OS-cursor / no dwell cursor). Dwell + eye-tracker cursor only after entering a game. Catalog includes UFYP math modules: `math-true-false` (Benar/Salah) and `math-fill-blank` (2x2 grid), ahead of Face / Visual Search / Memory.
- Why: Hub is navigation, not an eye-tracked trial; math games were in the reference set but missing from Phase 1 catalog.
- What was rejected and why: Keeping dwell cursor on the hub was rejected — it fights mouse UX before a session starts.

## 2026-08-23 — Games hub in editor shell + playlist editor
- What was decided: Cognitive Games uses Shell B (AppHeader + status bar like Live/Import). Hub playlist uses 2C: checkboxes (enabled set), drag handle, and up/down buttons. Play in order only runs enabled games.
- Why: User chose editor chrome continuity and full reorder UX.
- What was rejected and why: Standalone black fullscreen hub (Shell A/C) rejected for this iteration.

## 2026-08-23 — Cursor shape vs dwell effect
- What was decided: Cursor shapes are arrow / dot / transparent. Ring and pie are dwell-effect styles (progress while dwelling), stored as `dwellEffect`. Legacy saved `shape: ring|pie` migrates to `shape: dot` + matching dwellEffect.
- Why: User clarified ring/pie are dwell feedback, not pointer glyphs; requested transparent cursor.
- What was rejected and why: Keeping ring/pie in the shape grid was rejected.

## 2026-08-23 — Settings playlist order removed
- What was decided: Drop Playlist order from CognitiveSettingsOverlay; hub cards own reorder (drag + ↑↓).
- Why: Duplicate of hub controls.
- What was rejected and why: Keeping a second playlist editor in settings was rejected as redundant.

## 2026-08-23 — Cognitive gaze source uses global device
- What was decided: Remove Gaze source from CognitiveSettingsOverlay. In-game gaze follows `useGazeDevices` selected device (Settings → Gaze device).
- Why: Gaze hardware/source is app-global, not a game-cursor tweak.
- What was rejected and why: Duplicate gaze picker in game settings was rejected.

## 2026-08-23 — Split cursor vs dwell effect colors
- What was decided: `cursorColor` and `dwellEffectColor` are separate settings. Legacy single `color` migrates to both.
- Why: User asked to split the combined color control.
- What was rejected and why: One shared color for glyph + dwell effect was rejected.

## 2026-08-23 — Per-game dwell (approach C)
- What was decided: Hybrid C — dwell editable on each hub card; gear opens per-game settings panel. Day one panel fields: dwell only. Persist `sorot.cognitiveGameSettings`. Remove global default dwell from cursor settings overlay. Catalog `dwellMsOverride` seeds defaults (Visual Search 3000, others 1000).
- Why: User chose C; each module needs its own dwell; “another settings” deferred beyond dwell for day one.
- What was rejected and why: Global-only dwell and settings-only reorder of dwell were rejected.

## 2026-08-23 — Transparent dwell effect
- What was decided: Dwell effect options are transparent / ring / pie. Transparent hides dwell progress UI (dwell click still works).
- Why: User requested transparent dwell effect alongside ring/pie.
- What was rejected and why: Keeping only visible ring/pie feedback was rejected.

## 2026-08-23 — Hub drag reorder polish
- What was decided: Live index reorder while dragging (`moveGameToIndex`), lifted drag ghost, dashed placeholder card, accent drop-line before/after, smoother TransitionGroup FLIP easing.
- Why: User asked for more professional/intuitive drag-and-drop card motion on the hub.
- What was rejected and why: Drop-only reorder without live preview was rejected as less intuitive.

## 2026-08-23 — Animated cursor settings preview
- What was decided: CognitiveSettingsOverlay shows a live looping dwell preview (reuses DwellCursor `embedded` mode) for current shape + effect + colors.
- Why: User requested an animated cursor preview in Game settings.
- What was rejected and why: Static icon-only previews alone were rejected as insufficient.

## 2026-08-23 — Math · True / False playable module
- What was decided: Ship `math-true-false` as first playable module — equation list + Benar/Salah (mouse + dwell targets `math-tf-benar` / `math-tf-salah`), feedback colors, score, summary; `createMathTrueFalseSession` generates true/false equations; shell mounts `MathTrueFalseGame` when `activeGameId === 'math-true-false'`.
- Why: User chose Phase A (Math TF) next; matches UFYP `new-game/math-game.png` pattern.
- What was rejected and why: Leaving Math TF as placeholder until Face Familiarity; Fill-blank / Face / VS / Memory still placeholders.

## 2026-08-23 — In-game fullscreen + Math Fill Blank
- What was decided: Hub stays Shell B (header + status). Entering any game hides AppHeader/StatusBar and expands shell to full viewport (`cog-shell--fullscreen`, black stage). Ship `math-fill-blank` mirrored from Math TF: equation list with `...` blanks, 2×2 dwell grid (`math-fb-choice-0..3`), green/red filled feedback.
- Why: User chose “fullscreen in-game only” + “mirror math TF” for Fill Blank.
- What was rejected and why: Fullscreen for hub too (option 2); shared math-shell refactor (option 2) deferred.

## 2026-08-23 — In-game UI fills viewport (not card)
- What was decided: In-game shell uses `position: fixed; inset: 0` black stage; drop `center-panel` card chrome while playing; math TF/FB boards use large vh/vmin type and answer targets spanning the landscape (list left, controls right) like the single-image UFYP mock — not the compiled multi-panel reference strip.
- Why: User reported math games looked too small vs the full-screen single mock.
- What was rejected and why: Keeping max-width card / editor-panel inset layout in-game.

## 2026-08-23 — Restore OS cursor in Game settings
- What was decided: Hide OS cursor only while actively playing (`inGame && !settingsOpen && !quitConfirmOpen`). Opening Game settings (or quit) restores the normal mouse cursor and hides the dwell cursor so operators can click settings controls.
- Why: User could not select settings in-game because `cursor: none` covered the overlay.
- What was rejected and why: Keeping OS cursor hidden during settings and relying only on dwell for settings interaction.

## 2026-08-23 — Split cursor sizes (slider + input, WYSIWYG)
- What was decided: Separate cursorSizePx and dwellEffectSizePx (16–96px, default 36). Each has a range slider + numeric input in Game settings. DwellCursor scales glyph and ring/pie from those props; live preview and in-game share the same props (WYSIWYG). Persist via existing cognitive settings localStorage + normalize clamp.
- Why: User chose option 3 (split sizes) with slider + input each.
- What was rejected and why: Single shared size slider; presets-only S/M/L.

## 2026-08-23 — Face Familiarity playable module
- What was decided: Ship `face-familiarity` one-pair-at-a-time (dwell left/right, green/red borders, score/summary/playlist). Face pairs load from localStorage key `sorot.faceFamiliarityAssets` with SVG placeholders by default.
- Why: User chose approach 1 + provide images via frontend/localStorage.
- What was rejected and why: Stacked 5-row mockup layout (approach 2); scaffold-only (approach 3).

## 2026-08-23 — Memory Matrix playable module
- What was decided: Approach 1 — playable 3×3 Memory Matrix with gear settings (start sequence length, rounds, grow-by, flash ms, gap ms). Watch phase flashes yellow; input phase dwell: correct → green, wrong → red (retry round). Wired into shell + gaze (`mm-tile-*`, `mm-next-game`). Catalog id `memory-matrix`.
- Why: User chose approach 1 after Visual Search.
- What was rejected and why: Fixed-params-only (2); scaffold-only (3).

## 2026-08-23 — Visual Search playable module
- What was decided: Approach 2 — playable Visual Search with gear settings (columns, rows, targets/level, session timer). Levels: C→O, O→Q, `|`→I. Default dwell 3000ms from catalog. Found feedback = **letter color turns green only** (no bounding box / pad). Wired into shell + gaze (`vs-cell-*`, `vs-next-game`).
- Why: User chose approach 2 and clarified feedback is letter color change, not a larger box.
- What was rejected and why: Scaffold-only (3); oversized green plate/bounding box behind glyph.

## 2026-08-23 — Face Familiarity variable pair count
- What was decided: Approach 1 — settings **Add pair** / **Remove** (1–40 slots). Session length = number of fully supplied pairs (shuffled, one trial each). Defaults start at 3 placeholder slots. No separate “rounds” control.
- Why: User wants x pairs defined in settings, not fixed 5.
- What was rejected and why: Separate rounds slider that reuses pairs (approach 2); fixed slots with rounds-only (approach 3).

## 2026-08-23 — Face Familiarity answer feedback overlays
- What was decided: On answer, keep green/red borders and add a centered ✓/✕ badge over the image plus a slight darken overlay (`rgba(0,0,0,~0.4)`). Correct side always shows ✓ when locked; chosen wrong side shows ✕.
- Why: User found border-only feedback weak; chose overlay badge + keep border + darken.
- What was rejected and why: Corner chip; icon strip above image without overlay.

## 2026-08-23 — Face photos in game settings (not in-game)
- What was decided: Upload real/AI pairs only in Face Familiarity’s hub gear settings (`CognitiveGameSettingsPanel`). Play (single + playlist including face) is blocked until ≥1 fully supplied pair (`hasSuppliedFacePhotos`). Warning is an in-app modal (`CognitiveFacePhotosModal`), not `window.alert`. Modal offers OK + Open settings (opens that game’s gear panel). In-game has no asset editor; shell no longer tracks `faceAssetEditorOpen`.
- Why: User asked uploads in that game’s settings, warn when Play without photos; later asked for modal instead of browser prompt.
- What was rejected and why: In-game **Kelola gambar** / `@asset-editor-change` upload UI; native `window.alert`.

## 2026-08-23 — Hosting: Render Docker (Approach 3)
- What was decided: Host full SOROT stack on **Render** as a Docker Web Service (not Netlify). One container serves Vue + Flask + Socket.IO on port 5000.
- Why: User chose Approach 3 (single Docker host) and specified Render.
- What was rejected and why: Netlify frontend-only (Approach 1); Netlify + separate API (Approach 2) — Socket.IO split is fragile.

## 2026-08-24 — Render-ready hardening
- What was decided: `sorot.py` reads `PORT` env (Render injects it); add `GET /health` JSON endpoint; repo root `render.yaml` Blueprint (Docker, `healthCheckPath: /health`, `FLASK_DEBUG=0`, generated secret); document Render deploy + limits in `docs/development.md`.
- Why: User chose phase 1 (Render-ready hardening) after picking Render hosting.
- What was rejected and why: Persistent disk wiring in this pass (deferred to phase 3); Netlify split hosting.

## 2026-09-09 — Blank mode selector with `dev.ps1`
- What was decided: In `FLASK_DEBUG` (local default), Flask `/` and `/settings` must not serve `static/dist`. Return a pointer page that redirects to Vite `:5173` when it is up. Startup banner prints UI `:5173` and API `:5000`.
- Why: `dev.ps1` starts both servers, but Flask advertised `:5000`. That port served a stale Aug 23 production SPA (`index-CjiLtnkh.js`) that mounted Vue as an empty comment (`<!---->`), so the mode selector looked blank. Current source on `:5173` renders correctly.
- What was rejected and why: Rebuilding `static/dist` as the local fix (no HMR, goes stale again); reverse-proxying Vite through Flask (more moving parts). Production/Docker with `FLASK_DEBUG=0` still serves `static/dist`.

## 2026-09-09 — System camera pickers (Approach 2)
- What was decided: Two separate capture pickers. Overlay/virtual camera uses backend OpenCV list (`GET /api/settings/cameras`, DirectShow indexes, `cv2-enumerate-cameras` with probe fallback) and replaces the numeric index in Settings. WebGazer uses `navigator.mediaDevices.enumerateDevices()` and `setCameraConstraints({ deviceId })`, persisted as `sorot.webgazerCameraId`. Selecting an overlay camera applies `virtual_camera_index` immediately so tests use it without waiting for Save.
- Why: Index 0 is usually the laptop webcam; overlay and browser camera IDs are not the same namespace.
- What was rejected and why: Overlay-only picker (Approach 1); name-based auto-prefer OBS/Tobii (Approach 3).

## 2026-09-09 — Overlay gaze wired into cognitive games
- What was decided: Backend ref-counted live loop (`/api/gaze/live/start|stop`) reads the selected overlay camera, runs Hough marker detection, and emits `gaze_detected` with frame size. Games map that to the viewport and drive `DwellCursor` / dwell-click when Gaze Input Device is Tobii overlay or virtual camera. Changing `virtual_camera_index` restarts the live capture thread so a new camera is used immediately. Only one Flask process may bind `:5000`; a stale instance made `POST /api/gaze/live/start` return 405 via the GET-only `vite_public_files` catch-all.
- Why: User wants to play with a real eye tracker. Overlay samples previously never reached `useGazePoint` (and the server never emitted `gaze_detected`).
- What was rejected and why: Polling `/api/gaze` (needs a separate test capture session). Sharing App.vue’s socket instance (extra coupling); a second Socket.IO client in `useGazePoint` is enough. Name-based auto-prefer of OBS on Flask restart (still in-memory index; user re-selects overlay camera after backend restart).

## 2026-09-09 — Overlay gaze Kalman + display lerp
- What was decided: Port the legacy 4-state `cv2.KalmanFilter` (warmup 5 frames, processNoise 0.03, measurementNoise 5.0) into `_live_gaze_loop`. Emit Kalman-smoothed pixels on hit; on Hough miss emit last smoothed point. Games additionally lerp the dwell cursor toward each sample at display rate (`OVERLAY_LERP = 0.4` in `useGazePoint`).
- Why: User chose both. Raw Hough + silent misses made the in-game cursor hitch. The old smoother lived only in `legacy/tests/test_roi_gaze_webapp.py`.
- What was rejected and why: Backend-only or frontend-only (user asked for both). A second Kalman on the client (double lag). Capture-buffer / 15ms-sleep changes were deferred, then done in the snap-back pass below.

## 2026-09-09 — Overlay snap-back (circle test)
- What was decided: Live loop uses camera buffer size 1, Hough on a max-720px frame, and ~1ms wait instead of 15ms. Kalman emits `correct()` (not the pre-measurement prediction), with processNoise 0.12 and measurementNoise 2.5 so a circular path does not coast tangent then rewind. Duplicate last-known emits on Hough miss are skipped. The game cursor interpolates the last segment over 24–70ms and drops short reverse snaps (25–140px against recent velocity).
- Why: User confirmed a window-filling circular marker video. The glyph looked smooth but jumped back — constant-velocity predict-ahead plus a stale capture queue.
- What was rejected and why: Rejecting every reverse (breaks saccades back to the equation list). A second client Kalman.

## 2026-09-09 — Settings live gaze check
- What was decided: Settings opens with a black full-height preview (left) and a side panel (right) for overlay camera + Hough param1/2 + min/max radius. Changing those POSTs `/api/settings/update-config` immediately (250ms debounce). The live loop reads those globals each frame (radii scaled with the 720px Hough copy). Cursor is mapped to the stage, not the full window.
- Why: User wants to tune detection in real time against the circle overlay video without entering a game.
- What was rejected and why: Kalman Q/R sliders in this pass (Hough/camera only). Adaptive live radii (settings radii now drive the overlay path so the panel does something).

## 2026-09-09 — Cognitive play: fullscreen, focus, debug
- What was decided: Play (single or playlist) calls `requestFullscreen` on the game shell (CSS fullscreen remains if the browser blocks it). Hub + **S** expose Focus vs Debug (`playView` in cognitive settings). Focus hides `[data-session-chrome]` (hub back, titles/scores, hints). Debug keeps chrome and shows processed dwell cursor plus raw overlay sample (cyan ring) and a HUD (viewport processed/raw, camera pixels when overlay). Hotkey **d** toggles. **q** still leaves the game.
- Why: User wants an immersive play path and a debug path with raw vs Kalman/lerp positions.
- What was rejected and why: Fullscreen on the hub. Hiding gameplay targets (Benar/Salah, grids) in focus. A separate localStorage key (stored with existing cursor settings).
