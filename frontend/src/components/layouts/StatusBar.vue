<template>
	<footer class="status-bar" style="display: flex; flex-wrap: wrap; gap: 14px; padding: 10px 16px; border-top: 1px solid var(--color-border);">
		<span>Status: {{ statusMessage }}</span>
		<span v-if="currentWorkspaceFile">Workspace: {{ currentWorkspaceFile }}</span>
		<span v-if="sessionDir">Session: {{ sessionDir }}</span>
		<span v-if="framesRecorded !== null && framesRecorded > 0">Frames recorded: {{ framesRecorded }}</span>
		<span v-if="lastUpdated">Last updated: {{ formatTimestamp(lastUpdated) }}</span>
	</footer>
</template>

<script setup lang="ts">
defineProps<{
	statusMessage: string
	currentWorkspaceFile?: string | null
	lastUpdated?: string | null
	sessionDir?: string | null
	framesRecorded?: number | null
}>()

function formatTimestamp(value: string | null | undefined): string {
	if (!value) return ''
	const date = new Date(value)
	return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}
</script>
