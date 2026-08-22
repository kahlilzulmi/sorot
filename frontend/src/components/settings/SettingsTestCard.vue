<template>
	<div class="settings-test-card">
		<h4>{{ title }}</h4>
		<p class="settings-test-desc">{{ description }}</p>
		<button class="btn btn-secondary btn-sm" type="button" :disabled="result.tone === 'loading'" @click="$emit('run')">
			{{ result.tone === 'loading' ? 'Testing...' : 'Test' }}
		</button>
		<div v-if="result.tone !== 'idle'" class="settings-test-result" :class="result.tone">
			{{ result.message }}
		</div>
	</div>
</template>

<script setup lang="ts">
import type { TestResultState } from '../../composables/useSettings'

defineProps<{
	title: string
	description: string
	result: TestResultState
}>()

defineEmits<{
	(e: 'run'): void
}>()
</script>

<style scoped>
.settings-test-card {
	border: 1px solid var(--color-border);
	border-radius: 8px;
	padding: 16px;
	background: var(--color-background);
	color: var(--color-text);
	display: flex;
	flex-direction: column;
	gap: 10px;
	min-height: 150px;
}

.settings-test-card h4 {
	margin: 0;
	font-size: 14px;
	color: var(--color-text);
}

.settings-test-desc {
	margin: 0;
	flex: 1;
	font-size: 12px;
	color: var(--color-text-dim);
}

.settings-test-result {
	margin-top: 4px;
	padding: 8px 10px;
	border-radius: 6px;
	font-size: 12px;
}

.settings-test-result.success {
	background: rgba(152, 195, 121, 0.15);
	color: var(--color-success);
	border: 1px solid var(--color-success);
}

.settings-test-result.error {
	background: rgba(224, 108, 117, 0.15);
	color: var(--color-danger);
	border: 1px solid var(--color-danger);
}

.settings-test-result.warning,
.settings-test-result.loading {
	background: rgba(229, 192, 123, 0.15);
	color: var(--color-warning);
	border: 1px solid var(--color-warning);
}
</style>
