# Convert Raw Template HTML into Vite Vue Components

This guide is specific to this repository.

Goal:
- Turn the large page template into maintainable Vue Single File Components (SFC).
- Keep Flask backend and APIs unchanged.
- Migrate safely in small steps without breaking recording or analysis workflows.

## 1) Starting Point in This Repo

Current state:
- Main template markup is very large in templates/index.html.
- App logic is centralized in static/js/app.js.
- Vite entry is already present in frontend/src/main.js.

Important note:
- Your Vite config file is named frontend/vite.cofig.js (typo).
- Vite expects frontend/vite.config.js.

## 2) Migration Target Architecture

Frontend target structure:

  frontend/
  - src/
    - App.vue
    - main.js
    - styles/
      - app.css
    - components/
      - layout/
        - AppHeader.vue
        - StatusBar.vue
      - mode/
        - ModeSelector.vue
      - scene/
        - SceneSidebar.vue
      - video/
        - VideoWorkspace.vue
        - PlaybackControls.vue
      - roi/
        - RoiSidebar.vue
      - modals/
        - NewVideoModal.vue
        - RecordModal.vue
        - ProcessModal.vue
        - ImportModal.vue
        - RoiNameModal.vue
        - SaveAsModal.vue
        - ProgressModal.vue
        - ObsFilePickerModal.vue
    - composables/
      - useWorkspaceState.js
      - useVideoControls.js
      - useRoiEditor.js
      - useImportMode.js
      - useRecording.js
      - usePostProcessing.js
      - useHistory.js
      - useSocket.js

Backend stays:
- Flask routes, APIs, and Socket.IO in sorot.py.

## 3) Component Mapping from Existing HTML

Use this direct mapping from templates/index.html blocks:

1. Mode Selection Screen
- Source: mode-selector-overlay block.
- Target component: ModeSelector.vue.
- Props/events:
  - props: appMode
  - emits: select-mode

2. Header Toolbar
- Source: header.app-header block.
- Target component: AppHeader.vue.
- Props/events:
  - props: appMode, videoInfo, scenes, importedGazeData, importedGazeVideoFile, videoMode, modal state flags
  - emits: new-project, load-workspace, save, save-as, export-csv, export-json, open-record, open-process, generate-import-reports, toggle-video-mode, back-mode

3. Scene Sidebar
- Source: left-sidebar block with scene list.
- Target component: SceneSidebar.vue.
- Props/events:
  - props: scenes, activeSceneIdx, editingSceneIdx, editingCustomName, openSceneMenu, videoInfo
  - emits: select-scene, rename-start, rename-finish, rename-cancel, scene-delete, scene-menu-toggle

4. Video Workspace
- Source: center-panel block (video player, dual mode, slider, boundaries).
- Target component: VideoWorkspace.vue.
- Internal children:
  - PlaybackControls.vue
  - (optional) SceneTimeline.vue

5. ROI Sidebar
- Source: right-sidebar block.
- Target component: RoiSidebar.vue.
- Props/events:
  - props: currentScene, selectedROIIdx, editingROIIdx, editingName, openROIMenu
  - emits: select-roi, rename-roi-start, rename-roi-finish, rename-roi-cancel, delete-roi

6. Modals
- Source: each modal overlay block.
- One component per modal under components/modals.

7. Footer Status Bar
- Source: footer.status-bar.
- Target component: StatusBar.vue.

## 4) State Refactor Plan (from app.js)

Do not move all state at once.

Step A: Keep one root state object
- Start with a single composable useWorkspaceState.js containing existing data() fields.

Step B: Move methods by concern
- Move scene methods to useSceneManager.js (optional).
- Move ROI drawing/editing to useRoiEditor.js.
- Move playback controls to useVideoControls.js.
- Move import workflow to useImportMode.js.
- Move recording/post-processing to useRecording.js and usePostProcessing.js.

Step C: Keep API calls unchanged
- Preserve endpoint URLs and payload shapes.

Step D: Keep Socket events unchanged
- Wrap setup in useSocket.js, but keep event names exactly as now.

## 5) Incremental Sprint Plan (Recommended)

Sprint 1: Structural extraction only
1. Create App.vue.
2. Move Mode Selector block into ModeSelector.vue.
3. Move Header block into AppHeader.vue.
4. Keep most logic in parent and pass props/events.

Sprint 2: Sidebars
1. Extract SceneSidebar.vue.
2. Extract RoiSidebar.vue.
3. Keep methods in parent to avoid behavior changes.

Sprint 3: Video workspace
1. Extract VideoWorkspace.vue.
2. Extract PlaybackControls.vue.
3. Verify timeline, boundaries, slider, and canvas interactions.

Sprint 4: Modalization
1. Extract each modal one-by-one.
2. Test each modal behavior after extraction.

Sprint 5: Composables
1. Move related state/methods into composables.
2. Keep API contracts untouched.
3. Add smoke tests.

## 6) Example: First Real Extraction

Create frontend/src/components/mode/ModeSelector.vue:

```vue
<template>
  <div v-if="appMode === 'select'" class="mode-selector-overlay">
    <div class="mode-selector-container">
      <div class="mode-selector-header">
        <h1>📹 Video ROI Analyzer</h1>
        <p>Choose your analysis workflow</p>
      </div>

      <div class="mode-cards">
        <div class="mode-card" @click="$emit('select-mode', 'live')">
          <div class="mode-icon">🔴</div>
          <h2>Live Recording</h2>
          <p class="mode-description">Record new eye tracking session in real-time</p>
        </div>

        <div class="mode-card" @click="$emit('select-mode', 'import')">
          <div class="mode-icon">📁</div>
          <h2>Import & Analyze</h2>
          <p class="mode-description">Analyze existing gaze data retroactively</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  appMode: {
    type: String,
    required: true
  }
})

defineEmits(['select-mode'])
</script>
```

Then in App.vue:

```vue
<template>
  <div id="app">
    <ModeSelector :appMode="state.appMode" @select-mode="selectMode" />

    <div v-show="state.appMode !== 'select'">
      <!-- existing page content stays here initially -->
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import ModeSelector from './components/mode/ModeSelector.vue'

const state = reactive({
  appMode: 'select'
})

function selectMode(mode) {
  state.appMode = mode
}
</script>
```

This gives your first component win with minimal risk.

## 7) Adapting Existing main.js

Move from global bootstrap toward App.vue bootstrap.

Temporary bridge (safe):
- Keep existing app logic alive while extracting components.
- Gradually replace old initialization with createApp(App).

Target frontend/src/main.js:

```js
import { createApp } from 'vue'
import App from './App.vue'
import './styles/app.css'

createApp(App).mount('#app')
```

If you still need globals during transition:
- Import axios, socket.io-client, lucide and temporarily expose them on window.
- Remove this bridge only after all modules are import-based.

## 8) Modal Extraction Pattern

For each modal:
1. Keep visible state in parent.
2. Pass visible and data as props.
3. Emit close/confirm actions.
4. Parent performs side-effects (API calls, state updates).

This keeps behavior deterministic and easier to debug.

## 9) Robustness Rules While Refactoring

1. One UI block per commit
- Avoid giant refactors that mix 10 concerns.

2. No API contract changes
- Preserve endpoint paths, payload keys, and response handling.

3. Stable event names
- Keep existing method names/event semantics until fully migrated.

4. Visual parity first
- Componentization should not alter UI behavior initially.

5. Smoke test every extraction
- Open app, upload/load workspace, select scenes, draw ROI, play video, open each modal.

## 10) Suggested Test Checklist per Sprint

After every extraction sprint:
- App loads without console errors.
- Scene selection and active scene tracking still work.
- ROI create/edit/delete still work.
- Timeline and playback controls still work.
- Import mode flow still works.
- Recording and post-processing controls still render and trigger.

## 11) Practical Next Steps for You

Use this exact order now:
1. Rename frontend/vite.cofig.js to frontend/vite.config.js.
2. Create App.vue and ModeSelector.vue.
3. Update main.js to mount App.vue.
4. Extract AppHeader.vue next.
5. Run dev and smoke test before extracting another block.

If you follow this sequence, you will turn the raw HTML into real Vite components safely and keep production behavior stable.