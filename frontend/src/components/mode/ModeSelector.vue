<template>
	<!-- Pattern: presentational child that emits intent, no side effects. -->
	<div v-if="appMode === 'select'" class="mode-selector-overlay">
		<div class="mode-selector-container">
			<div class="mode-selector-header">
				<h1>Video ROI Analyzer</h1>
				<p>Choose your analysis workflow</p>
			</div>

			<div class="mode-cards">
				<button class="mode-card" type="button" @click="$emit('select-mode', 'live')">
					<div class="mode-icon">Live</div>
					<h2>Live Recording</h2>
					<p class="mode-description">Record a new eye-tracking session in real time.</p>
				</button>

				<button class="mode-card" type="button" @click="$emit('select-mode', 'import')">
					<div class="mode-icon">Import</div>
					<h2>Import and Analyze</h2>
					<p class="mode-description">Analyze an existing gaze dataset and video.</p>
				</button>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import type { AppMode } from '../../composables/useWorkspaceState'

// Input-only contract from parent.
defineProps<{ appMode: AppMode }>()

// Output-only contract back to parent.
defineEmits<{
	(e: 'select-mode', mode: 'live' | 'import'): void
}>()
</script>

