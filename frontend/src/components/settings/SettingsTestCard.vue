<template>
	<div class="settings-test-card">
		<h4>{{ title }}</h4>
		<p class="help-text">{{ description }}</p>
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
	border: 1px solid var(--color-border, #ddd);
	border-radius: 8px;
	padding: 16px;
	background: #fff;
}

.settings-test-result {
	margin-top: 10px;
	padding: 10px;
	border-radius: 6px;
	font-size: 13px;
}

.settings-test-result.success {
	background: #d4edda;
	color: #155724;
}

.settings-test-result.error {
	background: #f8d7da;
	color: #721c24;
}

.settings-test-result.warning,
.settings-test-result.loading {
	background: #fff3cd;
	color: #856404;
}
</style>
