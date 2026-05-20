<template>
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
				<House class="header-icon" />
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
			>
				<Plus class="header-icon" /> New
			</button>
			<button
				class="btn btn-secondary btn-sm"
				type="button"
				@click="$emit('open-project')"
				title="Open workspace JSON (Ctrl+O)"
			>
				<FolderOpen class="header-icon" /> Open
			</button>
			<button
				class="btn btn-secondary btn-sm"
				type="button"
				:disabled="!hasVideo"
				@click="$emit('save-workspace')"
			>
				<Save class="header-icon" /> Save
			</button>
			<button
				class="btn btn-secondary btn-sm"
				type="button"
				:disabled="!hasVideo"
				@click="$emit('save-workspace-as')"
			>
				<SaveAll class="header-icon" /> Save As
			</button>

			<div class="btn-group">
				<button
					class="btn btn-secondary btn-sm"
					type="button"
					:disabled="!hasVideo || !hasScenes"
					@click="$emit('export-csv')"
				>
					<FileText class="header-icon" /> Export CSV
				</button>
				<button
					class="btn btn-secondary btn-sm"
					type="button"
					:disabled="!hasVideo || !hasScenes"
					@click="$emit('export-json')"
					title="Export JSON"
				>
					<FileJson class="header-icon" />
				</button>
			</div>

			<div v-if="appMode === 'live'" class="btn-divider"></div>

			<button
				v-if="appMode === 'live'"
				class="btn btn-danger btn-sm"
				type="button"
				:disabled="!hasVideo"
				@click="$emit('open-record')"
			>
				<Circle class="header-icon" /> Record
			</button>
			<button
				v-if="appMode === 'live'"
				class="btn btn-info btn-sm"
				type="button"
				:disabled="!hasVideo"
				@click="$emit('open-process')"
			>
				<Settings class="header-icon" /> Post-process
			</button>

			<button
				v-if="appMode === 'import'"
				class="btn btn-success btn-sm"
				type="button"
				:disabled="!hasVideo || !hasScenes"
				@click="$emit('open-import')"
			>
				<BarChart3 class="header-icon" /> Import data
			</button>
		</div>
	</header>
</template>

<script setup lang="ts">
import type { AppMode } from '../../composables/useWorkspaceState'
import {
	BarChart3,
	Circle,
	FileJson,
	FileText,
	FolderOpen,
	House,
	Plus,
	Save,
	SaveAll,
	Settings
} from '@lucide/vue'

defineProps<{
	appMode: AppMode
	modeTitle: string
	hasVideo: boolean
	hasScenes: boolean
}>()

defineEmits<{
	(e: 'back'): void
	(e: 'new-project'): void
	(e: 'open-project'): void
	(e: 'save-workspace'): void
	(e: 'save-workspace-as'): void
	(e: 'export-csv'): void
	(e: 'export-json'): void
	(e: 'open-record'): void
	(e: 'open-process'): void
	(e: 'open-import'): void
}>()
</script>
