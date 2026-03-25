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
import { onMounted } from 'vue'
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
	setCurrentWorkspaceFile,
	setStatus,
	markUpdated
} = useWorkspaceState()

onMounted(() => {
	void restoreWorkspaceFromNavigation()
})

// Pattern: keep side effects and status mutations in parent first.
function openNewProjectExample() {
	setStatus('Open New Project clicked (example action)')
	markUpdated()
}

function getErrorMessage(error: unknown): string {
	if (error instanceof Error) return error.message
	if (typeof error === 'string') return error
	return 'Unknown error'
}

async function restoreWorkspaceFromNavigation(): Promise<void> {
	const workspaceFile = state.currentWorkspaceFile
	if (!workspaceFile) return

	try {
		setStatus(`Restoring workspace: ${workspaceFile}...`)

		const workspaceResponse = await fetch(`/api/workspace/${encodeURIComponent(workspaceFile)}`)
		const workspacePayload = (await workspaceResponse.json()) as {
			success?: boolean
			error?: string
			workspace?: Record<string, unknown>
			workspace_file?: string
		}

		if (!workspaceResponse.ok || !workspacePayload.success || !workspacePayload.workspace) {
			throw new Error(workspacePayload.error || 'Could not load workspace file')
		}

		const importResponse = await fetch('/api/import-workspace', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				...workspacePayload.workspace,
				workspace_file: workspacePayload.workspace_file || workspaceFile
			})
		})

		const importPayload = (await importResponse.json()) as {
			success?: boolean
			error?: string
			video_info?: Record<string, unknown>
			scenes?: Array<Record<string, unknown>>
			workspace_file?: string
		}

		if (!importResponse.ok || !importPayload.success) {
			throw new Error(importPayload.error || 'Could not import workspace data')
		}

		state.videoInfo = importPayload.video_info || (workspacePayload.workspace.video_info as Record<string, unknown>) || null
		state.scenes = importPayload.scenes || (workspacePayload.workspace.scenes as Array<Record<string, unknown>>) || []
		setCurrentWorkspaceFile(importPayload.workspace_file || workspacePayload.workspace_file || workspaceFile)

		if (state.appMode === 'select') {
			selectMode('import')
		} else {
			setStatus(`Workspace restored: ${state.currentWorkspaceFile}`)
		}

		markUpdated()
	} catch (error) {
		setStatus(`Workspace restore failed: ${getErrorMessage(error)}`)
	}
}
</script>