<template>
	<div class="modal-overlay" @click.self="$emit('close')">
		<div class="modal-content modal-large">
			<div class="modal-header">
				<h2>Import and Analyze Gaze Data</h2>
				<button class="btn-close" type="button" @click="$emit('close')">x</button>
			</div>
			<div class="modal-body">
				<div class="import-mode-selector" style="margin-bottom: 25px;">
					<h3 style="margin-bottom: 15px;">Choose Import Method</h3>
					<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
						<button
							type="button"
							:class="['mode-option', { active: importMethod === 'auto' }]"
							style="padding: 15px; border: 2px solid #ddd; border-radius: 8px; cursor: pointer; text-align: left; background: white;"
							@click="$emit('update:import-method', 'auto')"
						>
							<strong>Auto-Detect (Recommended)</strong>
							<small style="display: block; color: #666; margin-top: 6px;">
								Process eye gaze video automatically using detection algorithms
							</small>
						</button>
						<button
							type="button"
							:class="['mode-option', { active: importMethod === 'csv' }]"
							style="padding: 15px; border: 2px solid #ddd; border-radius: 8px; cursor: pointer; text-align: left; background: white;"
							@click="$emit('update:import-method', 'csv')"
						>
							<strong>CSV Import</strong>
							<small style="display: block; color: #666; margin-top: 6px;">
								Import pre-extracted gaze coordinates from CSV file
							</small>
						</button>
					</div>
				</div>

				<div v-if="importMethod === 'auto'" class="import-step">
					<h3>Step 1: Upload Eye Gaze Recording</h3>
					<input ref="autoGazeInputRef" type="file" accept="video/*" style="display: none" @change="onAutoGazeSelected">
					<button class="btn btn-primary" type="button" @click="autoGazeInputRef?.click()">
						Choose Eye Gaze Video
					</button>
					<span v-if="importedGazeVideoName" style="margin-left: 10px; color: #28a745;">{{ importedGazeVideoName }}</span>

					<h3 style="margin-top: 20px;">Step 2: Upload Stimulus Video</h3>
					<input ref="autoStimulusInputRef" type="file" accept="video/*" style="display: none" @change="onStimulusSelected">
					<button class="btn btn-primary" type="button" @click="autoStimulusInputRef?.click()">
						Choose Stimulus Video
					</button>
					<span v-if="importedVideoName" style="margin-left: 10px; color: #28a745;">{{ importedVideoName }}</span>

					<div class="info-box" style="margin-top: 16px;">
						<strong>How it works:</strong>
						<ol style="margin: 10px 0 0 20px;">
							<li>Eye gaze video is analyzed frame-by-frame</li>
							<li>Gaze coordinates are extracted automatically</li>
							<li>Both videos are shown side-by-side for synchronization</li>
						</ol>
					</div>
				</div>

				<div v-else>
					<div class="import-step">
						<h3>Step 1: Upload Gaze Data CSV</h3>
						<input ref="csvInputRef" type="file" accept=".csv,text/csv" style="display: none" @change="onCsvChange">
						<button class="btn btn-primary" type="button" @click="csvInputRef?.click()">Choose CSV File</button>
						<span v-if="csvFileName" style="margin-left: 10px;">{{ csvFileName }}</span>

						<div v-if="headers.length > 0" class="import-grid" style="margin-top: 16px;">
							<label>
								X column
								<select class="input-text" :value="mapping.x" @change="emitMapping('x', $event)">
									<option value="">Choose...</option>
									<option v-for="header in headers" :key="`x-${header}`" :value="header">{{ header }}</option>
								</select>
							</label>
							<label>
								Y column
								<select class="input-text" :value="mapping.y" @change="emitMapping('y', $event)">
									<option value="">Choose...</option>
									<option v-for="header in headers" :key="`y-${header}`" :value="header">{{ header }}</option>
								</select>
							</label>
							<label>
								Timestamp column
								<select class="input-text" :value="mapping.timestamp" @change="emitMapping('timestamp', $event)">
									<option value="">Choose...</option>
									<option v-for="header in headers" :key="`t-${header}`" :value="header">{{ header }}</option>
								</select>
							</label>
						</div>
					</div>

					<div v-if="!hasVideo" class="import-step">
						<h3>Step 2: Upload Stimulus Video</h3>
						<input ref="csvStimulusInputRef" type="file" accept="video/*" style="display: none" @change="onStimulusSelected">
						<button class="btn btn-primary" type="button" @click="csvStimulusInputRef?.click()">Choose Video File</button>
						<span v-if="importedVideoName" style="margin-left: 10px; color: #28a745;">{{ importedVideoName }}</span>
					</div>
					<p v-else class="help-text" style="margin: 12px 0;">Using loaded stimulus video: workspace video is already available.</p>

					<div class="import-step" style="margin-top: 16px;">
						<h3>Optional: Eye Gaze Video (Side-by-Side View)</h3>
						<input ref="csvGazeInputRef" type="file" accept="video/*" style="display: none" @change="onCsvGazeSelected">
						<button class="btn btn-info btn-sm" type="button" @click="csvGazeInputRef?.click()">Choose Eye Gaze Video</button>
						<span v-if="importedGazeVideoName" style="margin-left: 10px; color: #17a2b8;">{{ importedGazeVideoName }}</span>
					</div>

					<div class="input-group" style="margin-top: 16px;">
						<label>
							Frame offset
							<input class="input-text" type="number" :value="frameOffset" @input="onOffsetInput">
						</label>
						<small class="help-text">Positive shifts gaze forward in time. Adjust further in Dual Video mode after import.</small>
					</div>
				</div>

				<div v-if="warnings.length > 0" class="info-box">
					<strong>Warnings</strong>
					<div v-for="warning in warnings" :key="warning">{{ warning }}</div>
				</div>
				<div v-if="errors.length > 0" class="info-box" style="border-left-color: var(--color-danger);">
					<strong>Errors</strong>
					<div v-for="error in errors" :key="error">{{ error }}</div>
				</div>
				<div v-if="validRowCount > 0" class="info-box">
					Valid rows: {{ validRowCount }} | Skipped rows: {{ skippedRowCount }}
				</div>

				<div class="modal-actions">
					<button class="btn btn-secondary" type="button" @click="$emit('close')">Cancel</button>
					<button
						v-if="importMethod === 'csv'"
						class="btn btn-success"
						type="button"
						:disabled="!canApplyCsvImport || (!hasVideo && !importedVideoName)"
						@click="$emit('apply-csv')"
					>
						Import CSV
					</button>
					<button
						v-else
						class="btn btn-success"
						type="button"
						:disabled="!canApplyAutoImport"
						@click="$emit('apply-auto')"
					>
						Start Auto-Detection
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { ImportMethod } from '../../composables/useImportMode'

interface ImportMapping {
	x: string
	y: string
	timestamp: string
}

const csvInputRef = ref<HTMLInputElement | null>(null)
const autoGazeInputRef = ref<HTMLInputElement | null>(null)
const autoStimulusInputRef = ref<HTMLInputElement | null>(null)
const csvStimulusInputRef = ref<HTMLInputElement | null>(null)
const csvGazeInputRef = ref<HTMLInputElement | null>(null)

defineProps<{
	importMethod: ImportMethod
	hasVideo: boolean
	csvFileName: string | null
	importedVideoName: string | null
	importedGazeVideoName: string | null
	headers: string[]
	mapping: ImportMapping
	frameOffset: number
	warnings: string[]
	errors: string[]
	validRowCount: number
	skippedRowCount: number
	canApplyCsvImport: boolean
	canApplyAutoImport: boolean
}>()

const emit = defineEmits<{
	(e: 'close'): void
	(e: 'update:import-method', value: ImportMethod): void
	(e: 'csv-selected', file: File): void
	(e: 'stimulus-selected', file: File): void
	(e: 'gaze-video-selected', file: File): void
	(e: 'update:mapping', field: 'x' | 'y' | 'timestamp', value: string): void
	(e: 'update:frame-offset', value: number): void
	(e: 'apply-csv'): void
	(e: 'apply-auto'): void
}>()

function onCsvChange(event: Event): void {
	const input = event.target as HTMLInputElement
	const file = input.files?.[0]
	input.value = ''
	if (!file) return
	emit('csv-selected', file)
}

function onStimulusSelected(event: Event): void {
	const input = event.target as HTMLInputElement
	const file = input.files?.[0]
	input.value = ''
	if (!file) return
	emit('stimulus-selected', file)
}

function onAutoGazeSelected(event: Event): void {
	const input = event.target as HTMLInputElement
	const file = input.files?.[0]
	input.value = ''
	if (!file) return
	emit('gaze-video-selected', file)
}

function onCsvGazeSelected(event: Event): void {
	onAutoGazeSelected(event)
}

function emitMapping(field: 'x' | 'y' | 'timestamp', event: Event): void {
	const target = event.target as HTMLSelectElement
	emit('update:mapping', field, target.value)
}

function onOffsetInput(event: Event): void {
	const target = event.target as HTMLInputElement
	const parsed = Number(target.value)
	emit('update:frame-offset', Number.isFinite(parsed) ? parsed : 0)
}
</script>

<style scoped>
.mode-option.active {
	border-color: var(--color-primary) !important;
	background: #e7f3ff !important;
}
</style>
