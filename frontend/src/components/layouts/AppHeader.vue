<template>
	<!-- Pattern: layout child, receives display state and emits toolbar actions. -->
	<header class="app-header">
		<div class="header-left">
			<button class="btn btn-secondary btn-sm" type="button" @click="$emit('back')">
				Back
			</button>
			<div class="header-title">
				<h1>SOROT</h1>
				<p>{{ modeTitle }}</p>
			</div>
		</div>

		<div class="header-right">
			<button class="btn btn-primary btn-sm" type="button" @click="$emit('new-project')">
				New
			</button>
			<span style="font-size: 12px; color: var(--color-text-dim);">Mode: {{ appMode }}</span>
		</div>
	</header>
</template>

<script setup lang="ts">
import type { AppMode } from '../../composables/useWorkspaceState'

// Parent-controlled display inputs.
defineProps<{
	appMode: AppMode
	modeTitle: string
}>()

// Parent handles behavior for these actions.
defineEmits<{
	(e: 'back'): void
	(e: 'new-project'): void
}>()
</script>

