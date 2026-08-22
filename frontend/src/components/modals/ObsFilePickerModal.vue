<template>
	<div class="modal-overlay" @click.self="$emit('close')">
		<div class="modal-content modal-medium">
			<div class="modal-header">
				<h2>Select Eye Gaze Recording File</h2>
				<button class="btn-close" type="button" @click="$emit('close')">x</button>
			</div>
			<div class="modal-body">
				<div v-if="loading" class="processing-status">
					<div class="spinner"></div>
					<p>Loading available files...</p>
				</div>

				<div v-else-if="files.length === 0" class="error-box">
					<p><strong>No eye gaze recording files found.</strong></p>
					<p>Expected location: Videos folder (eyegaze-*.mp4)</p>
				</div>

				<div v-else>
					<p style="margin-bottom: 15px;"><strong>Select a recording file to import:</strong></p>
					<div class="file-list">
						<div v-for="file in files" :key="file.path" class="file-item-result">
							<div style="flex: 1;">
								<div style="font-weight: 600;">{{ file.filename }}</div>
								<div style="font-size: 11px; color: #666;">
									{{ file.size_mb }} MB · Created: {{ file.created }}
								</div>
							</div>
							<button
								class="btn btn-primary btn-sm"
								type="button"
								:disabled="importing"
								@click="$emit('select-file', file.path)"
							>
								{{ importing ? 'Importing...' : 'Select' }}
							</button>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import type { ObsRecordingFile } from '../../composables/usePostProcessing'

defineProps<{
	loading: boolean
	importing: boolean
	files: ObsRecordingFile[]
}>()

defineEmits<{
	(e: 'close'): void
	(e: 'select-file', path: string): void
}>()
</script>
