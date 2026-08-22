<template>

	<div class="flex min-h-0 flex-1 flex-col gap-3 p-4">

		<div

			v-if="videoObjectUrl && gazeExtractionEnabled"

			class="video-stage relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-lg bg-black ring-1 ring-slate-700"

		>

			<VideoAnalyzer

				class="video-analyzer-host min-h-0 flex-1"

				:video-src="videoObjectUrl"

				:analyzing="gazeExtractionActive"

				:show-controls="true"

				:validation-mode="gazeExtractionValidation"

				@marker-detected="onMarkerDetected"

				@marker-lost="onMarkerLost"

				@frame-drops-exceeded="onFrameDropsExceeded"

			/>

			<p

				v-if="extractionBuffer.length > 0"

				class="pointer-events-none absolute bottom-3 left-3 rounded bg-slate-900/90 px-2 py-1 text-xs text-cyan-200"

			>

				{{ extractionBuffer.length.toLocaleString() }} samples captured

			</p>

		</div>



		<div

			v-else-if="videoObjectUrl"

			ref="containerRef"

			class="video-stage relative flex min-h-0 flex-1 items-center justify-center overflow-hidden rounded-lg bg-black ring-1 ring-slate-700"

		>

			<video

				ref="videoRef"

				class="max-h-full max-w-full object-contain"

				:src="videoObjectUrl"

				playsinline

				@loadedmetadata="onLoadedMetadata"

				@timeupdate="onTimeUpdate"

				@play="gazeStore.setPlaying(true)"

				@pause="gazeStore.setPlaying(false)"

				@ended="gazeStore.setPlaying(false)"

			/>

			<canvas

				ref="canvasRef"

				class="roi-canvas"

				aria-label="Region of interest drawing layer"

				@mousedown="onMouseDown"

				@mousemove="onMouseMove"

				@mouseup="onMouseUp"

			/>

		</div>



		<div

			v-else

			class="flex min-h-[280px] flex-1 flex-col items-center justify-center rounded-lg border border-dashed border-slate-600 bg-slate-900/50 text-center text-slate-500"

		>

			<p class="text-sm">No video loaded</p>

			<p class="mt-1 text-xs">Choose a video file in the sidebar</p>

		</div>

	</div>

</template>



<script setup lang="ts">

import { ref, watch } from 'vue'

import { useRoiCanvas } from '../../composables/useRoiCanvas'

import { useGazeStore, type GazeImportSummary } from '../../stores/useGazeStore'

import type { GazeCoordinate } from '../../types/gaze'

import type { FrameDropQualityPayload } from '../../types/analyzer'

import { getGazeSampleAtTime } from '../../utils/gazeRoi'

import VideoAnalyzer from './VideoAnalyzer.vue'



const props = defineProps<{

	videoObjectUrl: string | null

	gazeExtractionEnabled?: boolean

	gazeExtractionActive?: boolean

	gazeExtractionValidation?: boolean

}>()



const emit = defineEmits<{

	'extraction-status': [message: string]

}>()



const gazeStore = useGazeStore()

const containerRef = ref<HTMLElement | null>(null)

const videoRef = ref<HTMLVideoElement | null>(null)

const canvasRef = ref<HTMLCanvasElement | null>(null)

const roiInteractionDisabled = ref(false)

const extractionBuffer = ref<GazeCoordinate[]>([])



const {

	onMouseDown,

	onMouseMove,

	onMouseUp,

	syncCanvasToVideoLayout,

	renderRois

} = useRoiCanvas(canvasRef, videoRef, containerRef, roiInteractionDisabled, drawGazeOverlay)



watch(

	() => gazeStore.isPlaying,

	(playing) => {

		if (props.gazeExtractionEnabled) return

		const video = videoRef.value

		if (!video) return

		if (playing) {

			void video.play()

		} else {

			video.pause()

		}

	}

)



watch(

	() => gazeStore.currentTime,

	(time) => {

		if (props.gazeExtractionEnabled) return

		const video = videoRef.value

		if (!video || Math.abs(video.currentTime - time) < 0.05) return

		video.currentTime = time

	}

)



watch(

	() =>

		[

			props.videoObjectUrl,

			gazeStore.gazeDataRevision,

			gazeStore.currentTime,

			gazeStore.roiCount,

			gazeStore.selectedRoiIndex

		] as const,

	() => {

		if (props.gazeExtractionEnabled) return

		requestAnimationFrame(() => renderRois())

	}

)



watch(

	() => props.gazeExtractionEnabled,

	(enabled) => {

		if (!enabled) {

			extractionBuffer.value = []

			return

		}

		extractionBuffer.value = []

		emit('extraction-status', 'Tobii overlay extraction mode — play video and start extraction.')

	}

)



watch(

	() => props.gazeExtractionActive,

	(active, wasActive) => {

		if (wasActive && !active) {

			commitExtractionBuffer()

		}

	}

)



function onMarkerDetected(payload: {

	coordinates: { x: number; y: number }

	videoTimestamp: number

}): void {

	extractionBuffer.value.push({

		x: payload.coordinates.x,

		y: payload.coordinates.y,

		timestamp: payload.videoTimestamp

	})

}



function onMarkerLost(): void {

	// Marker gaps are expected; samples are committed only when extraction stops.

}



function onFrameDropsExceeded(payload: FrameDropQualityPayload): void {

	emit(

		'extraction-status',

		`Frame drops ${(payload.dropRate * 100).toFixed(0)}% — extraction paused. Retry with validation mode or a smaller video.`

	)

}



function commitExtractionBuffer(): void {

	if (extractionBuffer.value.length === 0) {

		emit('extraction-status', 'No gaze samples captured during extraction.')

		return

	}



	const summary: GazeImportSummary = {

		validRowCount: extractionBuffer.value.length,

		skippedRowCount: 0,

		columnMapping: { x: 'cv', y: 'cv', timestamp: 'video' },

		timestampUnit: 'seconds',

		assumedVideoFps: null,

		warnings: ['Gaze extracted from Tobii overlay video (client-side CV).']

	}



	gazeStore.setGazeData(

		[...extractionBuffer.value],

		gazeStore.videoFileName ?? 'tobii-extraction',

		summary

	)

	extractionBuffer.value = []

	emit(

		'extraction-status',

		`Committed ${summary.validRowCount.toLocaleString()} extracted samples to the session.`

	)

}



function refineFrameIndexTimestamps(video: HTMLVideoElement): void {

	const summary = gazeStore.importSummary

	if (!summary || summary.timestampUnit !== 'frame_index' || !summary.assumedVideoFps) {

		return

	}

	if (video.duration <= 0 || gazeStore.gazeCoordinates.length === 0) {

		return

	}



	const coordinates = gazeStore.gazeCoordinates

	const maxTimestamp = coordinates[coordinates.length - 1]?.timestamp ?? 0

	const maxFrame = maxTimestamp * summary.assumedVideoFps

	const refinedFps = maxFrame / video.duration

	if (!Number.isFinite(refinedFps) || refinedFps <= 0) {

		return

	}

	if (Math.abs(refinedFps - summary.assumedVideoFps) < 0.25) {

		gazeStore.setVideoMetadata(gazeStore.videoFileName, refinedFps)

		return

	}



	const scale = summary.assumedVideoFps / refinedFps

	const rescaled = coordinates.map((sample) => ({

		x: sample.x,

		y: sample.y,

		timestamp: sample.timestamp * scale

	}))



	gazeStore.setGazeData(rescaled, gazeStore.sourceFileName, {

		...summary,

		assumedVideoFps: refinedFps,

		warnings: [

			...summary.warnings,

			`Adjusted timestamps to ${refinedFps.toFixed(2)} FPS using loaded video duration.`

		]

	})

	gazeStore.setVideoMetadata(gazeStore.videoFileName, refinedFps)

}



function onLoadedMetadata(): void {

	const video = videoRef.value

	if (video) {

		refineFrameIndexTimestamps(video)

	}

	syncCanvasToVideoLayout()

}



function onTimeUpdate(): void {

	const video = videoRef.value

	if (!video) return

	gazeStore.setCurrentTime(video.currentTime)

}



function drawGazeOverlay(): void {

	const canvas = canvasRef.value

	if (!canvas || !props.videoObjectUrl) return



	const context = canvas.getContext('2d')

	if (!context) return



	const sample = getGazeSampleAtTime(gazeStore.gazeCoordinates, gazeStore.currentTime)

	if (!sample) return



	context.fillStyle = 'rgba(224, 108, 117, 0.9)'

	context.strokeStyle = 'rgba(255, 255, 255, 0.6)'

	context.lineWidth = 1.5

	context.beginPath()

	context.arc(sample.x, sample.y, 5, 0, Math.PI * 2)

	context.fill()

	context.stroke()

}

</script>

<style scoped>
.video-analyzer-host :deep(.canvas-wrapper) {
	position: relative;
	display: flex;
	flex-direction: column;
	height: 100%;
	min-height: 280px;
}

.video-analyzer-host :deep(.video-analyzer__video) {
	width: 100%;
	max-height: 100%;
	object-fit: contain;
}
</style>

