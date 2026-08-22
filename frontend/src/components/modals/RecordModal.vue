<template>
	<div class="modal-overlay" @click.self="$emit('close')">
		<div class="modal-content">
			<div class="modal-header">
				<h2>Start Recording</h2>
				<button class="btn-close" type="button" @click="$emit('close')">x</button>
			</div>
			<div class="modal-body">
				<div class="device-status-section">
					<h3>Device and Software Status</h3>
					<div class="device-status-card status-success">
						<div class="status-header">
							<strong>Eye Tracking Mode</strong>
						</div>
						<div class="status-details">
							<div class="status-list">
								<div class="status-item">
									<span class="status-icon">OBS</span>
									<span><strong>OBS Studio:</strong> Connected and ready</span>
								</div>
								<div class="status-item">
									<span class="status-icon">Eye</span>
									<span><strong>Eye Tracker:</strong> Tobii Ghost or virtual camera</span>
								</div>
							</div>
						</div>
					</div>
				</div>

				<div class="recording-instructions-section">
					<h3>Recording Instructions</h3>
					<div class="instructions-list">
						<div v-for="step in steps" :key="step.n" class="instruction-item">
							<span class="instruction-bullet">{{ step.n }}</span>
							<span>{{ step.text }}</span>
						</div>
					</div>
				</div>

				<div class="modal-actions">
					<button class="btn btn-danger btn-primary-action" type="button" @click="$emit('confirm')">
						Start Recording
					</button>
					<button class="btn btn-secondary btn-cancel" type="button" @click="$emit('close')">
						Cancel
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
const steps = [
	{ n: 1, text: 'Eye tracker must be active and camera index set correctly.' },
	{ n: 2, text: 'OBS must be running with virtual camera enabled.' },
	{ n: 3, text: 'Video will play in fullscreen when available.' },
	{ n: 4, text: 'Press START on the video overlay to begin playback.' },
	{ n: 5, text: 'Recording auto-stops at video end.' },
	{ n: 6, text: 'Gaze data is saved to the sessions folder.' }
]

defineEmits<{
	(e: 'close'): void
	(e: 'confirm'): void
}>()
</script>
