<template>
	<!-- Pattern: presentational child that emits intent, no side effects. -->
	<div v-if="appMode === 'select'" class="mode-selector-overlay">
		<div class="mode-selector-container">
			<div class="mode-selector-header">
				<img src="/sorot-logo.svg" alt="SOROT logo" class="mode-logo" width="96" height="96" />
				<h1>SOROT</h1>
				<p>System for Optimized Region of Interest Tracking</p>
			</div>
			<div class="mode-health-strip">
				<span :class="['health-pill', backendReady ? 'health-ok' : 'health-warn']">
					Backend {{ backendReady ? 'ready' : 'waiting' }}
				</span>
				<span :class="['health-pill', socketConnected ? 'health-ok' : 'health-warn']">
					Socket {{ socketConnected ? 'connected' : 'disconnected' }}
				</span>
				<span class="health-pill">{{ gazeSourceLabel }}</span>
				<span v-if="lastGazeAt" class="health-pill">Last gaze: {{ lastGazeAt }}</span>
			</div>

			<div class="mode-cards">
				<button class="mode-card" type="button" @click="$emit('select-mode', 'live')">
					<TvMinimalPlay class="mode-icon" size="128" />
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
					<Import class="mode-icon" size="128" />
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

				<button class="mode-card" type="button" @click="$emit('select-mode', 'games')">
					<Gamepad2 class="mode-icon" size="128" />
					<br>
					<h2>Cognitive Games</h2>
					<p class="mode-description">Face familiarity, visual search, and memory matrix with dwell selection.</p>
					<ul class="mode-features">
						<li>✓ Gaze dwell interaction</li>
						<li>✓ Play in order or pick one</li>
						<li>✓ Customizable playlist</li>
						<li>✓ Operator hotkeys (Q / S)</li>
					</ul>
				</button>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import type { AppMode } from '../../composables/useWorkspaceState'
import { TvMinimalPlay, Import, Gamepad2 } from '@lucide/vue'

// Input-only contract from parent.
defineProps<{
	appMode: AppMode
	backendReady: boolean
	socketConnected: boolean
	gazeSourceLabel: string
	lastGazeAt: string | null
}>()

// Output-only contract back to parent.
defineEmits<{
	(e: 'select-mode', mode: 'live' | 'import' | 'games'): void
}>()
</script>

