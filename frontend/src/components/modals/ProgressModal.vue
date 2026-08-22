<template>
	<div class="modal-overlay modal-progress" @click.self="$emit('close')">
		<div class="modal-content modal-medium">
			<div class="modal-header">
				<h2 v-if="!progressComplete && !progressError">Processing Recording</h2>
				<h2 v-else-if="progressComplete">Processing Complete</h2>
				<h2 v-else>Processing Failed</h2>
			</div>
			<div class="modal-body">
				<div v-if="!progressComplete && !progressError" class="progress-bar-container">
					<div class="progress-bar-track">
						<div class="progress-bar-fill" :style="{ width: `${progressPercent}%` }"></div>
					</div>
					<div class="progress-bar-text">{{ Math.round(progressPercent) }}%</div>
				</div>

				<p class="progress-message">{{ progressMessage }}</p>

				<div v-if="progressSteps.length > 0" class="progress-steps">
					<div v-for="step in progressSteps" :key="step.key" class="progress-step">
						<span :class="['status-dot', step.status]"></span>
						<span class="progress-step-label">{{ step.label }}</span>
						<span class="progress-step-status">{{ progressStatusLabel(step.status) }}</span>
					</div>
				</div>

				<div v-if="progressError" class="error-box">
					<strong>Error:</strong> {{ progressError }}
				</div>

				<div v-if="progressComplete && !progressError">
					<div v-if="Object.keys(generatedFiles).length > 0" class="generated-files">
						<p><strong>Generated files:</strong></p>
						<ul>
							<li v-for="(path, key) in generatedFiles" :key="key">{{ key }}: {{ path }}</li>
						</ul>
					</div>
					<div class="modal-actions">
						<button class="btn btn-primary btn-block" type="button" @click="$emit('close')">
							Close
						</button>
					</div>
				</div>

				<div v-else-if="!progressError" class="modal-actions">
					<div class="spinner"></div>
					<p style="margin-top: 10px; font-size: 12px; color: #666;">Please wait. This may take a few minutes.</p>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import type { ProgressStep, ProgressStepStatus } from '../../composables/usePostProcessing'

defineProps<{
	progressComplete: boolean
	progressError: string | null
	progressPercent: number
	progressMessage: string
	progressSteps: ProgressStep[]
	generatedFiles: Record<string, string>
	progressStatusLabel: (status: ProgressStepStatus) => string
}>()

defineEmits<{
	(e: 'close'): void
}>()
</script>
