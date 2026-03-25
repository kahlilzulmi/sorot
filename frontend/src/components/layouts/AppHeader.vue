<template>
	<!-- Pattern: layout child, receives display state and emits toolbar actions. -->
	<header class="app-header">
		<div class="header-left">
			<button
				class="btn btn-secondary btn-sm"
				type="button"
				@click="$emit('back')"
				title="Back to mode selector (H)"
				aria-label="Back to mode selector"
				aria-keyshortcuts="H"
			>
				<House class="header-icon"/>
			</button>
			<div class="header-title">
				<img src="/favicon-16x16.png" alt="SOROT logo" class="header-logo" />
				<h1>SOROT</h1>
				<p>{{ modeTitle }}</p>
			</div>
		</div>

		<div class="header-right">
			<button
				class="btn btn-primary btn-sm"
				type="button"
				@click="$emit('new-project')"
				title="Create new workspace (Ctrl+N)"
				aria-label="Create new workspace"
				aria-keyshortcuts="Control+N"
			>
				<Plus class="header-icon" /> New
			</button>
			<button
				class="btn btn-secondary btn-sm"
				type="button"
				@click="$emit('open-project')"
				title="Open workspace JSON (Ctrl+O)"
				aria-label="Open workspace"
				aria-keyshortcuts="Control+O"
			>
				<FolderOpen class="header-icon" /> Open
			</button>
			<button
				class="btn btn-secondary btn-sm"
				type="button"
				@click="$emit('save-workspace')"
				:disabled="!hasVideo"
				title="Save workspace (Ctrl+S)"
				aria-label="Save workspace"
				aria-keyshortcuts="Control+S"
			>
				<Save class="header-icon" /> Save
			</button>
			<button
				class="btn btn-secondary btn-sm"
				type="button"
				@click="$emit('save-workspace-as')"
				:disabled="!hasVideo"
				title="Save workspace as (Ctrl+Shift+S)"
				aria-label="Save workspace as"
				aria-keyshortcuts="Control+Shift+S"
			>
				<SaveAll class="header-icon" /> Save As
			</button>
		</div>
	</header>
</template>

<script setup lang="ts">
import type { AppMode } from '../../composables/useWorkspaceState'
import { House, Plus, FolderOpen, Save, SaveAll } from '@lucide/vue'

// Parent-controlled display inputs.
defineProps<{
	appMode: AppMode
	modeTitle: string
	hasVideo: boolean
}>()

// Parent handles behavior for these actions.
defineEmits<{
	(e: 'back'): void
	(e: 'new-project'): void
	(e: 'open-project'): void
	(e: 'save-workspace'): void
	(e: 'save-workspace-as'): void
}>()
</script>

