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
				:disabled="modalBlocked"
				@click="$emit('new-project')"
				title="Create new workspace (Ctrl+N)"
			>
				<Plus class="header-icon" /> New
			</button>
			<button
				class="btn btn-secondary btn-sm"
				type="button"
				:disabled="modalBlocked"
				@click="$emit('open-project')"
				title="Open workspace JSON (Ctrl+O)"
			>
				<FolderOpen class="header-icon" /> Open
			</button>
			<button
				class="btn btn-secondary btn-sm"
				type="button"
				:disabled="!hasVideo || modalBlocked"
				@click="$emit('save-workspace')"
			>
				<Save class="header-icon" /> Save
			</button>
			<button
				class="btn btn-secondary btn-sm"
				type="button"
				:disabled="!hasVideo || modalBlocked"
				@click="$emit('save-workspace-as')"
			>
				<SaveAll class="header-icon" /> Save As
			</button>

			<div class="btn-group" style="position: relative;">
				<button
					class="btn btn-secondary btn-sm"
					type="button"
					:disabled="!hasVideo || !hasScenes || modalBlocked"
					@click="$emit('export-csv')"
				>
					<FileText class="header-icon" /> Export CSV
				</button>
				<button
					class="btn btn-secondary btn-sm"
					type="button"
					:disabled="!hasVideo || !hasScenes || modalBlocked"
					title="More export formats"
					@click="showExportDropdown = !showExportDropdown"
				>
					<ChevronDown class="header-icon" />
				</button>
				<div v-if="showExportDropdown" class="dropdown-menu" style="right: 0; left: auto; min-width: 140px;">
					<button class="menu-item" type="button" @click="exportAs('csv')">Export CSV</button>
					<button class="menu-item" type="button" @click="exportAs('json')">Export JSON</button>
				</div>
			</div>

			<div v-if="appMode === 'live'" class="btn-divider"></div>

			<button
				v-if="appMode === 'live'"
				class="btn btn-danger btn-sm"
				type="button"
				:disabled="!hasVideo || modalBlocked"
				@click="recordingActive ? $emit('stop-record') : $emit('open-record')"
			>
				<Circle class="header-icon" /> {{ recordingActive ? 'Stop' : 'Record' }}
			</button>
			<button
				v-if="appMode === 'live'"
				class="btn btn-info btn-sm"
				type="button"
				:disabled="!hasVideo || !hasSession || modalBlocked"
				@click="$emit('open-process')"
			>
				<Settings class="header-icon" /> Post-process
			</button>

			<button
				v-if="appMode === 'import'"
				class="btn btn-success btn-sm"
				type="button"
				:disabled="!hasVideo || !hasScenes || !hasImportedGaze || modalBlocked"
				@click="$emit('generate-reports')"
			>
				<BarChart3 class="header-icon" /> Generate Reports
			</button>
			<button
				v-if="appMode === 'import'"
				class="btn btn-secondary btn-sm"
				type="button"
				:disabled="!hasVideo || modalBlocked"
				@click="$emit('open-import')"
			>
				Import data
			</button>
			<button
				v-if="appMode === 'import' && hasGazeVideo"
				class="btn btn-info btn-sm"
				type="button"
				:disabled="modalBlocked"
				@click="$emit('toggle-dual-video')"
			>
				<Monitor class="header-icon" /> {{ dualVideoMode === 'dual' ? 'Single Video' : 'Dual Video' }}
			</button>
			<a
				href="/settings"
				class="btn btn-secondary btn-sm"
				title="System tests, configuration, and diagnostics"
				@click.prevent="$emit('open-settings')"
			>
				<Settings class="header-icon" /> Settings
			</a>
		</div>
	</header>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import type { AppMode } from '../../composables/useWorkspaceState'
import type { VideoMode } from '../../composables/useDualVideo'
import {
	BarChart3,
	ChevronDown,
	Circle,
	FileText,
	FolderOpen,
	House,
	Monitor,
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
	hasImportedGaze: boolean
	hasGazeVideo: boolean
	dualVideoMode: VideoMode
	recordingActive: boolean
	modalBlocked: boolean
	hasSession: boolean
}>()

const emit = defineEmits<{
	(e: 'back'): void
	(e: 'new-project'): void
	(e: 'open-project'): void
	(e: 'save-workspace'): void
	(e: 'save-workspace-as'): void
	(e: 'export-csv'): void
	(e: 'export-json'): void
	(e: 'open-record'): void
	(e: 'stop-record'): void
	(e: 'open-process'): void
	(e: 'open-import'): void
	(e: 'generate-reports'): void
	(e: 'toggle-dual-video'): void
	(e: 'open-settings'): void
}>()

const showExportDropdown = ref(false)

function exportAs(format: 'csv' | 'json'): void {
	showExportDropdown.value = false
	if (format === 'csv') {
		emit('export-csv')
	} else {
		emit('export-json')
	}
}

function closeDropdownOnOutsideClick(event: MouseEvent): void {
	const target = event.target as HTMLElement | null
	if (!target?.closest('.btn-group')) {
		showExportDropdown.value = false
	}
}

onMounted(() => {
	document.addEventListener('click', closeDropdownOnOutsideClick)
})

onBeforeUnmount(() => {
	document.removeEventListener('click', closeDropdownOnOutsideClick)
})
</script>
