<template>
	<div class="modal-overlay" @click.self="$emit('close')">
		<div class="modal-content">
			<div class="modal-header">
				<h2>Post-processing Options</h2>
				<button class="btn-close" type="button" @click="$emit('close')">x</button>
			</div>
			<div class="modal-body">
				<div v-if="!sessionDir" class="info-box">
					<p>No recording session available. Complete a recording first.</p>
				</div>
				<div v-else>
					<div v-if="manualImportRequired" class="error-box" style="margin-bottom: 20px;">
						<h4 style="margin-top: 0;">Eye gaze recording file not found</h4>
						<p style="margin-bottom: 10px;">The eye gaze recording file was not detected automatically.</p>
						<button
							class="btn btn-warning btn-block"
							type="button"
							:disabled="importingObsFile"
							@click="$emit('import-obs-file')"
						>
							{{ importingObsFile ? 'Importing...' : 'Import Eye Gaze File (eyegaze-*.mp4)' }}
						</button>
					</div>

					<p><strong>Available processing options:</strong></p>

					<div v-if="!manualImportRequired && obsRecordingPath" class="info-box" style="margin-bottom: 15px; padding: 8px;">
						<small>Eye gaze recording file ready</small>
					</div>

					<div class="process-option">
						<h4>Generate Heatmaps</h4>
						<p>Creates visual heatmaps showing gaze concentration areas for each scene.</p>
						<button
							class="btn btn-secondary btn-block"
							type="button"
							:disabled="processing || manualImportRequired"
							@click="$emit('generate-heatmaps')"
						>
							Generate Heatmaps
						</button>
					</div>

					<div class="process-option">
						<h4>ROI Statistics</h4>
						<p>Calculates fixation counts and durations for each region of interest.</p>
						<button
							class="btn btn-secondary btn-block"
							type="button"
							:disabled="processing || manualImportRequired"
							@click="$emit('generate-roi-stats')"
						>
							Generate Statistics
						</button>
					</div>

					<div class="process-option">
						<h4>Overlay Video</h4>
						<p>Creates video with gaze overlay and ROI boundaries.</p>
						<button
							class="btn btn-secondary btn-block"
							type="button"
							:disabled="processing || manualImportRequired"
							@click="$emit('generate-overlay-video')"
						>
							Generate Overlay Video
						</button>
					</div>

					<div class="process-option">
						<h4>Heatmap Overlay Videos</h4>
						<p>Creates per-scene videos with transparent heatmap overlay.</p>
						<button
							class="btn btn-secondary btn-block"
							type="button"
							:disabled="processing || manualImportRequired"
							@click="$emit('generate-heatmap-overlay')"
						>
							Generate Heatmap Overlay Videos
						</button>
					</div>

					<div class="process-option process-all">
						<button
							class="btn btn-primary btn-large"
							type="button"
							:disabled="processing || manualImportRequired"
							@click="$emit('process-all')"
						>
							Process All (Recommended)
						</button>
					</div>
				</div>

				<div v-if="processing" class="processing-status">
					<p><strong>{{ processingStatus }}</strong></p>
					<div class="spinner"></div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
defineProps<{
	sessionDir: string | null
	manualImportRequired: boolean
	obsRecordingPath: string | null
	processing: boolean
	processingStatus: string
	importingObsFile: boolean
}>()

defineEmits<{
	(e: 'close'): void
	(e: 'import-obs-file'): void
	(e: 'generate-heatmaps'): void
	(e: 'generate-roi-stats'): void
	(e: 'generate-overlay-video'): void
	(e: 'generate-heatmap-overlay'): void
	(e: 'process-all'): void
}>()
</script>
