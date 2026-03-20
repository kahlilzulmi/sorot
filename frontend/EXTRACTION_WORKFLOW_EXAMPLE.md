# Extraction Runbook (Read, Move, Modify, Check)

Use this guide as a practical loop while converting templates/index.html into Vue components.

## Current Baseline

Already in place:
- Parent orchestrator: src/App.vue
- First extracted block: src/components/mode/ModeSelector.vue
- Shared typed state: src/composables/useWorkspaceState.ts
- Starter layout components:
  - src/components/layouts/AppHeader.vue
  - src/components/layouts/StatusBar.vue

## Core Rule

For each extraction, do exactly this sequence:
1. Read one block in templates/index.html (one visual section only).
2. Move markup to one component file.
3. Modify parent wiring in src/App.vue.
4. Check behavior immediately before touching another block.

## How To Extract One Block

## Step 1: Read

In templates/index.html, locate one root block by class name.

Good root examples:
- div.mode-selector-overlay
- header.app-header
- div.left-sidebar
- div.center-panel
- div.right-sidebar
- footer.status-bar

Pick only one root block per commit.

## Step 2: Move

Create target component and move the HTML template first.

Mapping:
- div.mode-selector-overlay -> src/components/mode/ModeSelector.vue
- header.app-header -> src/components/layouts/AppHeader.vue
- div.left-sidebar -> src/components/scene/SceneSidebar.vue
- div.center-panel -> src/components/video/VideoWorkspace.vue
- div.right-sidebar -> src/components/roi/RoiSidebar.vue
- footer.status-bar -> src/components/layouts/StatusBar.vue

At this stage:
- Keep markup structure almost identical.
- Do not refactor logic yet.
- Keep existing class names so CSS still works.

## Step 3: Modify

After moving markup, wire data flow.

In child component:
- Add typed props for incoming data.
- Add typed emits for user actions.
- Do not call APIs in child yet.

In src/App.vue:
- Import the new child component.
- Pass props from state/composable.
- Handle emits with parent functions.

In src/composables/useWorkspaceState.ts:
- Add only missing shared state for this block.
- Keep side effects in parent until extraction is stable.

## Step 4: Check

Run this after every block:

1. npm run build
2. Open app and use only the extracted section
3. Confirm there is no behavior change

Quick checklist:
- Renders correctly
- Click handlers still work
- No console errors
- No missing icon or CSS class regressions

If any check fails:
- Revert only the last block change.
- Fix wiring first (props/emits mismatch is most common).

## First 5 Extractions (Recommended Order)

Use this order to reduce risk:

1. Mode Selector
- Read: div.mode-selector-overlay
- Move: src/components/mode/ModeSelector.vue
- Modify: src/App.vue mode events
- Check: select live/import switches state

2. Header
- Read: header.app-header
- Move: src/components/layouts/AppHeader.vue
- Modify: pass appMode, modeTitle, action emits
- Check: buttons trigger parent handlers

3. Status Bar
- Read: footer.status-bar
- Move: src/components/layouts/StatusBar.vue
- Modify: pass statusMessage, workspace, timestamp
- Check: values update when parent state changes

4. Scene Sidebar
- Read: div.left-sidebar including scene list block
- Move: src/components/scene/SceneSidebar.vue
- Modify: scenes props + select/rename/delete emits
- Check: scene select and menu actions still work

5. ROI Sidebar
- Read: div.right-sidebar including roi-list
- Move: src/components/roi/RoiSidebar.vue
- Modify: currentScene/selectedROI props + roi emits
- Check: roi select/rename/delete still work

Only after these are stable, extract video workspace and modal blocks.

## Props/Emits Template (Copy This)

Use this structure in each new component:

```vue
<script setup lang="ts">
type Item = { id: number; name: string }

defineProps<{
  items: Item[]
  selectedId: number | null
}>()

defineEmits<{
  (e: 'select-item', id: number): void
  (e: 'delete-item', id: number): void
}>()
</script>
```

## Naming Rules

- Props: noun-based and explicit (selectedSceneIdx, currentScene, statusMessage).
- Emits: verb-based and kebab-case (select-scene, rename-scene, delete-roi).
- Parent handlers: action-focused (onSelectScene or selectScene).

## What Not To Do

- Do not move multiple unrelated root blocks in one commit.
- Do not change API payloads while extracting UI blocks.
- Do not push API calls into child components too early.
- Do not rename CSS classes during first extraction pass.

## Next Action For You

Start with Scene Sidebar now:
1. Read div.left-sidebar in templates/index.html.
2. Move into src/components/scene/SceneSidebar.vue.
3. Add typed props and emits.
4. Wire in src/App.vue.
5. Run npm run build and manually test scene interactions.
