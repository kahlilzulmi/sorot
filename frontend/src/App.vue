<template>
	<div id="app">
		<!-- Pattern: parent owns state and wires child events. -->
		<ModeSelector :app-mode="state.appMode" @select-mode="selectMode" />

		<div v-show="state.appMode !== 'select'">
			<AppHeader
				:app-mode="state.appMode"
				:mode-title="modeTitle"
				@back="backToModeSelect"
				@new-project="openNewProjectExample"
			/>

			<main class="container" style="display: block; height: auto; min-height: calc(100vh - 120px);">
				<section class="center-panel" style="min-height: 420px;">
					<h2 style="margin-bottom: 12px;">Systematic Extraction Example</h2>
					<p style="margin-bottom: 12px; color: var(--color-text-dim);">
						This page is your migration starter. Keep each extraction small and preserve behavior.
					</p>
					<ol style="padding-left: 20px; line-height: 1.8;">
						<li>Extract one block from templates/index.html into one Vue component.</li>
						<li>Use props for input and emits for actions.</li>
						<li>Keep side effects (API, socket, canvas) in parent/composable first.</li>
						<li>Run smoke test before extracting the next block.</li>
					</ol>

					<div style="margin-top: 16px; padding: 12px; border: 1px solid var(--color-border); border-radius: 8px;">
						<strong>Next recommended block:</strong> App Header from templates/index.html
					</div>
				</section>
			</main>

			<StatusBar
				:status-message="state.statusMessage"
				:current-workspace-file="state.currentWorkspaceFile"
				:last-updated="state.lastUpdated"
			/>
		</div>
	</div>
</template>

<script setup lang="ts">
import AppHeader from './components/layouts/AppHeader.vue'
import StatusBar from './components/layouts/StatusBar.vue'
import ModeSelector from './components/mode/ModeSelector.vue'
import { useWorkspaceState } from './composables/useWorkspaceState'

// Pattern: shared app state and actions come from one composable.
const {
	state,
	modeTitle,
	selectMode,
	backToModeSelect,
	setStatus,
	markUpdated
} = useWorkspaceState()

// Pattern: keep side effects and status mutations in parent first.
function openNewProjectExample() {
	setStatus('Open New Project clicked (example action)')
	markUpdated()
}
</script>

