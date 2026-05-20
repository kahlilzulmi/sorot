<template>
	<!-- Pattern: read-only display component for global status context. -->
	<footer class="status-bar" style="display: flex; gap: 14px; padding: 10px 16px; border-top: 1px solid var(--color-border);">
		<span>Status: {{ statusMessage }}</span>
		<span v-if="currentWorkspaceFile">Workspace: {{ currentWorkspaceFile }}</span>
		<span v-if="lastUpdated">Last updated: {{ formatTimestamp(lastUpdated) }}</span>
	</footer>
</template>

<script setup lang="ts">
// Parent passes already-prepared values; this component only formats display.
defineProps<{
	statusMessage: string
	currentWorkspaceFile?: string | null
	lastUpdated?: string | null
}>()

// Local formatting helper kept pure for easy reuse/testing.
function formatTimestamp(value: string | null | undefined): string {
	if (!value) return ''
	const date = new Date(value)
	return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}
</script>

