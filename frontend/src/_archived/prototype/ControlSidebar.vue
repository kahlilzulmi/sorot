<template>

	<aside

		class="flex h-full w-full flex-col gap-6 overflow-y-auto border-r border-slate-700 bg-slate-900 p-4 lg:w-72 lg:shrink-0"

		aria-label="Sorot controls"

	>

		<header>

			<h1 class="text-lg font-semibold tracking-tight text-cyan-400">Sorot</h1>

			<p class="mt-1 text-xs text-slate-400">Local-first gaze analysis</p>

		</header>



		<section class="space-y-3" aria-labelledby="playback-heading">

			<h2 id="playback-heading" class="text-xs font-medium uppercase tracking-wide text-slate-500">

				Playback

			</h2>

			<button

				type="button"

				class="w-full rounded-md bg-cyan-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-2 focus:ring-offset-slate-900"

				:aria-label="gazeStore.isPlaying ? 'Pause video' : 'Play video'"

				@click="gazeStore.togglePlayback()"

			>

				{{ gazeStore.isPlaying ? 'Pause' : 'Play' }}

			</button>

			<label class="block text-xs text-slate-400">

				<span class="mb-1 block">Current time (seconds)</span>

				<input

					:value="gazeStore.currentTime"

					type="number"

					min="0"

					step="0.01"

					aria-label="Seek to time in seconds"

					class="w-full rounded border border-slate-600 bg-slate-800 px-2 py-1.5 text-sm text-slate-100 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"

					@input="onTimeInput"

				>

			</label>

		</section>



		<section class="space-y-3" aria-labelledby="gaze-heading">

			<h2 id="gaze-heading" class="text-xs font-medium uppercase tracking-wide text-slate-500">

				Gaze data

			</h2>

			<label

				class="flex cursor-pointer flex-col items-center justify-center rounded-md border border-dashed border-slate-600 bg-slate-800/50 px-3 py-4 text-center text-xs text-slate-400 transition hover:border-cyan-500 hover:bg-slate-800"

			>

				<span class="font-medium text-slate-300">Import gaze CSV</span>

				<span class="mt-1">x, y, timestamp (auto-detected columns)</span>

				<input

					ref="csvInputRef"

					type="file"

					accept=".csv,text/csv"

					class="sr-only"

					aria-label="Import gaze CSV file"

					@change="onCsvSelected"

				>

			</label>

			<p class="text-xs text-slate-500" aria-live="polite">

				<template v-if="gazeStore.gazeSampleCount > 0">

					{{ gazeStore.gazeSampleCount.toLocaleString() }} gaze samples loaded

					<span v-if="gazeStore.sourceFileName"> from {{ gazeStore.sourceFileName }}</span>

					<span v-if="timestampUnitLabel" class="block text-slate-600">{{ timestampUnitLabel }}</span>

				</template>

				<template v-else>

					No gaze data imported. ROI hit-testing uses a {{ GAZE_POSITION_MARGIN_PX }}px margin when samples are loaded.

				</template>

			</p>

			<button

				v-if="gazeStore.gazeSampleCount > 0"

				type="button"

				class="text-xs text-slate-400 underline hover:text-slate-200"

				aria-label="Clear imported gaze data"

				@click="onClearGazeData"

			>

				Clear gaze data

			</button>

			<ul
				v-if="importWarnings.length > 0"
				class="list-inside list-disc space-y-1 text-xs text-amber-400/90"
				aria-label="CSV import warnings"
			>
				<li v-for="(warning, index) in importWarnings" :key="index">{{ warning }}</li>
			</ul>

		</section>



		<section class="space-y-3" aria-labelledby="extract-heading">

			<h2 id="extract-heading" class="text-xs font-medium uppercase tracking-wide text-slate-500">

				Tobii overlay extraction

			</h2>

			<label class="flex cursor-pointer items-start gap-2 text-xs text-slate-400">

				<input

					type="checkbox"

					class="mt-0.5 rounded border-slate-600 bg-slate-800 text-cyan-600 focus:ring-cyan-500"

					:checked="gazeExtractionEnabled"

					:disabled="!videoLoaded"

					@change="onExtractionModeChange"

				>

				<span>Extract gaze from Tobii overlay video (client-side CV)</span>

			</label>

			<template v-if="gazeExtractionEnabled">

				<label class="flex cursor-pointer items-start gap-2 text-xs text-slate-500">

					<input

						type="checkbox"

						class="mt-0.5 rounded border-slate-600 bg-slate-800 text-cyan-600 focus:ring-cyan-500"

						:checked="gazeExtractionValidation"

						@change="onValidationModeChange"

					>

					<span>Validation mode (full pixel stride, stricter QC)</span>

				</label>

				<button

					type="button"

					class="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 transition hover:border-cyan-600 hover:bg-slate-700 disabled:opacity-40"

					:disabled="!videoLoaded"

					@click="toggleExtractionActive"

				>

					{{ gazeExtractionActive ? 'Stop extraction' : 'Start extraction' }}

				</button>

			</template>

		</section>



		<section class="space-y-3" aria-labelledby="roi-heading">

			<h2 id="roi-heading" class="text-xs font-medium uppercase tracking-wide text-slate-500">

				Regions of interest

			</h2>

			<p class="text-xs text-slate-500">

				Click and drag on the video frame to draw. Corners resize; drag inside to move.

			</p>

			<button

				v-if="canExportMetrics"

				type="button"

				class="w-full rounded-md border border-cyan-800 bg-cyan-950/50 px-3 py-2 text-sm font-medium text-cyan-200 transition hover:border-cyan-600 hover:bg-cyan-950"

				aria-label="Export ROI statistics as CSV"

				@click="onExportRoiStatistics"

			>

				Export ROI statistics

			</button>

			<button

				v-if="gazeStore.activeRoi"

				type="button"

				class="w-full rounded-md border border-red-900/50 bg-red-950/40 px-3 py-2 text-sm text-red-300 transition hover:border-red-700 hover:bg-red-950/70"

				:aria-label="`Delete selected region ${gazeStore.activeRoi.label ?? 'ROI'}`"

				@click="gazeStore.deleteActiveRoi()"

			>

				Delete selected ROI

			</button>

			<ul

				v-if="gazeStore.roiCount > 0"

				class="max-h-40 space-y-2 overflow-y-auto text-xs text-slate-400"

				role="listbox"

				aria-label="Regions of interest"

			>

				<li

					v-for="(roi, index) in gazeStore.regionsOfInterest"

					:key="roi.id"

					role="option"

					:aria-selected="index === gazeStore.selectedRoiIndex"

					:class="[

						'flex min-h-11 cursor-pointer items-center justify-between gap-2 rounded px-2 py-2 transition',

						index === gazeStore.selectedRoiIndex

							? 'bg-cyan-950/60 ring-1 ring-cyan-600'

							: 'bg-slate-800 hover:bg-slate-700'

					]"

					@click="gazeStore.selectRoi(index)"

				>

					<span class="min-w-0 flex-1 truncate">{{ formatRoi(roi) }}</span>

					<button

						type="button"

						class="flex h-11 w-11 shrink-0 items-center justify-center text-lg text-slate-500 hover:text-red-400"

						:aria-label="`Remove ${roi.label ?? 'ROI'} at ${roi.x}, ${roi.y}`"

						@click.stop="gazeStore.removeRegionOfInterest(index)"

					>

						×

					</button>

				</li>

			</ul>

			<p v-else class="text-xs text-slate-500">No regions defined for this session.</p>

		</section>



		<section class="mt-auto space-y-2 border-t border-slate-700 pt-4" aria-labelledby="video-heading">

			<h2 id="video-heading" class="sr-only">Video source</h2>

			<label class="block text-xs text-slate-400">

				<span class="mb-1 block">Video file</span>

				<input

					type="file"

					accept="video/*"

					aria-label="Choose video file"

					class="w-full text-xs text-slate-300 file:mr-2 file:rounded file:border-0 file:bg-slate-700 file:px-2 file:py-1 file:text-slate-200"

					@change="onVideoSelected"

				>

			</label>

			<p v-if="gazeStore.videoFileName" class="text-xs text-slate-600">

				Last video: {{ gazeStore.videoFileName }}

				<span v-if="gazeStore.videoFps"> ({{ gazeStore.videoFps.toFixed(2) }} FPS)</span>

			</p>

		</section>



		<p

			v-if="statusMessage"

			class="text-xs text-amber-400/90"

			role="status"

			aria-live="polite"

		>

			{{ statusMessage }}

		</p>

	</aside>

</template>



<script setup lang="ts">

import { computed, ref } from 'vue'

import { useGazeStore } from '../../stores/useGazeStore'

import type { RegionOfInterest } from '../../types/gaze'

import { exportRoiMetricsToCsv } from '../../utils/exportMetricsCsv'

import { computeRoiMetrics, DEFAULT_SCENE_NAME, GAZE_POSITION_MARGIN_PX } from '../../utils/gazeRoi'

import { loadGazeCsvIntoStore } from '../../utils/parseGazeCsv'



const props = defineProps<{
	gazeExtractionEnabled: boolean
	gazeExtractionActive: boolean
	gazeExtractionValidation: boolean
}>()

const emit = defineEmits<{
	'video-selected': [file: File]
	'update:gazeExtractionEnabled': [enabled: boolean]
	'update:gazeExtractionActive': [active: boolean]
	'update:gazeExtractionValidation': [validation: boolean]
}>()



const gazeStore = useGazeStore()

const csvInputRef = ref<HTMLInputElement | null>(null)

const statusMessage = ref('')



const canExportMetrics = computed(

	() => gazeStore.gazeSampleCount > 0 && gazeStore.roiCount > 0

)



const timestampUnitLabel = computed(() => {

	const summary = gazeStore.importSummary

	if (!summary) return ''

	const stored = 'Stored timestamps: seconds (video sync)'

	const detected = `Detected in CSV: ${summary.timestampUnit}`

	const fps =

		summary.assumedVideoFps !== null ? ` · assumed ${summary.assumedVideoFps} FPS` : ''

	return `${stored}. ${detected}${fps}.`

})

const importWarnings = computed(() => gazeStore.importSummary?.warnings ?? [])

const videoLoaded = computed(() => Boolean(gazeStore.videoFileName))



function onTimeInput(event: Event): void {

	const target = event.target as HTMLInputElement

	const value = Number.parseFloat(target.value)

	if (!Number.isNaN(value)) {

		gazeStore.setCurrentTime(value)

	}

}



function onVideoSelected(event: Event): void {

	const input = event.target as HTMLInputElement

	const file = input.files?.[0]

	if (file) {

		gazeStore.setVideoMetadata(file.name, null)

		emit('video-selected', file)

		statusMessage.value = `Loaded video: ${file.name}`

	}

}



function formatRoi(roi: RegionOfInterest): string {

	const label = roi.label ?? 'ROI'

	return `${label}: (${roi.x}, ${roi.y}) ${roi.width}×${roi.height}`

}



async function onCsvSelected(event: Event): Promise<void> {

	const input = event.target as HTMLInputElement

	const file = input.files?.[0]

	if (!file) return



	statusMessage.value = 'Parsing gaze CSV…'



	try {

		const result = await loadGazeCsvIntoStore(file)

		if (!result.success) {

			statusMessage.value = result.errors.join(' ') || 'Failed to parse CSV'

			return

		}



		statusMessage.value = `Imported ${result.validRowCount.toLocaleString()} samples from ${file.name}`

		if (result.skippedRowCount > 0) {

			statusMessage.value += ` (${result.skippedRowCount.toLocaleString()} rows skipped)`

		}

	} catch (error) {

		statusMessage.value = error instanceof Error ? error.message : 'Failed to parse CSV'

	} finally {

		input.value = ''

	}

}



function onClearGazeData(): void {

	gazeStore.clearGazeCoordinates()

	statusMessage.value = 'Gaze data cleared'

}

function onExtractionModeChange(event: Event): void {

	const target = event.target as HTMLInputElement

	emit('update:gazeExtractionEnabled', target.checked)

	if (!target.checked) {

		emit('update:gazeExtractionActive', false)

	}

}

function onValidationModeChange(event: Event): void {

	const target = event.target as HTMLInputElement

	emit('update:gazeExtractionValidation', target.checked)

}

function toggleExtractionActive(): void {

	emit('update:gazeExtractionActive', !props.gazeExtractionActive)

}



function onExportRoiStatistics(): void {

	try {

		const metrics = computeRoiMetrics(

			gazeStore.gazeCoordinates,

			gazeStore.regionsOfInterest,

			DEFAULT_SCENE_NAME,

			GAZE_POSITION_MARGIN_PX

		)

		const baseName = gazeStore.sourceFileName?.replace(/\.[^/.]+$/, '') ?? 'roi_statistics'

		exportRoiMetricsToCsv(metrics, { filename: `${baseName}_roi_metrics` })

		statusMessage.value = `Exported ${metrics.length} ROI metric row(s) to CSV`

	} catch (error) {

		statusMessage.value = error instanceof Error ? error.message : 'Export failed'

	}

}

</script>


