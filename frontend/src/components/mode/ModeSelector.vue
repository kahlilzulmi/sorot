<template>
	<!-- Pattern: presentational child that emits intent, no side effects. -->
	<div v-if="appMode === 'select'" class="mode-selector-overlay">
		<div class="mode-selector-container">
			<div class="mode-selector-header">
				<img src="/sorot-icon.png" alt="SOROT logo" class="mode-logo" />
				<h1>SOROT</h1>
				<p>System for Optimized Region of Interest Tracking</p>
			</div>

			<div class="mode-cards">
				<button class="mode-card" type="button" @click="$emit('select-mode', 'live')">
					<TvMinimalPlay class="mode-icon"  size="128" />
					<br>
					<h2>Live Recording</h2>
					<p class="mode-description">Record a new eye-tracking session in real time.</p>
                        <ul class="mode-features">
                            <li>✓ Define ROIs before recording</li>
                            <li>✓ Real-time gaze capture</li>
                            <li>✓ OBS eye tracking</li>
                            <li>✓ Immediate analysis</li>
                        </ul>
				</button>

				<button class="mode-card" type="button" @click="$emit('select-mode', 'import')">
					<Import class="mode-icon" size="128"/>
					<br>
					<h2>Import and Analyze</h2>
					<p class="mode-description">Analyze an existing gaze dataset and video.</p>
					<ul class="mode-features">
                            <li>✓ Upload CSV gaze coordinates</li>
                            <li>✓ Define ROIs post-recording</li>
                            <li>✓ Frame offset support</li>
                            <li>✓ Reprocess old data</li>
                        </ul>
				</button>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import type { AppMode } from '../../composables/useWorkspaceState'
import { TvMinimalPlay, Import } from '@lucide/vue'

// Input-only contract from parent.
defineProps<{ appMode: AppMode }>()

// Output-only contract back to parent.
defineEmits<{
	(e: 'select-mode', mode: 'live' | 'import'): void
}>()
</script>

