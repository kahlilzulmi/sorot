<!--
  INTEGRATION (Vue / Pinia) — minimal mount API
  ─────────────────────────────────────────────
  1. Import VideoAnalyzer in App.vue (or VideoWorkspace) alongside / instead of raw <video>.
  2. Wire props:
       <VideoAnalyzer
         :video-src="videoObjectUrl"
         :analyzing="isExtractingGaze"
         :pixel-stride="validationMode ? 1 : 2"
         @marker-detected="appendGazeSample"
         @marker-lost="onMarkerLost"
         @frame-drops-exceeded="onFrameDropQc"
       />
  3. Stream into Pinia (useGazeStore):
       import { useGazeStore } from '@/stores/useGazeStore'
       import type { GazeCoordinate } from '@/types/gaze'
       import { GAZE_POSITION_MARGIN_PX } from '@/constants/gaze' // ROI export only

       const gazeStore = useGazeStore()
       const extractionSamples = ref<GazeCoordinate[]>([])

       function appendGazeSample(payload: {
         coordinates: { x: number; y: number }
         videoTimestamp: number
       }): void {
         extractionSamples.value.push({
           x: payload.coordinates.x,
           y: payload.coordinates.y,
           timestamp: payload.videoTimestamp
         })
       }

       function commitExtractionToStore(): void {
         gazeStore.setGazeCoordinates([...extractionSamples.value])
         extractionSamples.value = []
       }
  4. ROI hit tests: use gazeRoi utils with GAZE_POSITION_MARGIN_PX — not MARKER_MARGIN_PX
     (overlay crosshair only).
  5. Pause extraction when drop QC fires; offer stride-1 retry for validation runs.
-->
<template>
	<div class="canvas-wrapper video-analyzer">
		<video
			ref="videoElementRef"
			class="video-analyzer__video"
			:src="videoSrc"
			crossorigin="anonymous"
			playsinline
			:controls="showControls"
			@loadedmetadata="onVideoMetadataLoaded"
			@play="onVideoPlay"
			@pause="onVideoPause"
			@seeked="onVideoSeeked"
		/>
		<canvas
			ref="overlayCanvasRef"
			class="roi-canvas video-analyzer__overlay"
			:class="{ 'roi-disabled': !showOverlayInteractions }"
		/>
		<canvas ref="captureCanvasRef" class="video-analyzer__capture" aria-hidden="true" />
		<div v-if="analyzing" class="video-analyzer__status">
			<span class="video-analyzer__pulse" />
			Analyzing
			<span v-if="validationMode" class="video-analyzer__badge">validation</span>
			<template v-if="markerPosition">
				· ({{ markerPosition.x }}, {{ markerPosition.y }})
			</template>
			<template v-if="frameDropStats.framesOffered > 0">
				· drops {{ (frameDropStats.dropRate * 100).toFixed(0) }}%
			</template>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import type {
	AnalyzeFrameMessage,
	AnalyzeResultMessage,
	AnalyzerPixelStride,
	ConfigureAnalyzerMessage,
	FrameDropQualityPayload,
	MarkerCoordinates
} from '../../types/analyzer'

const MAX_ANALYSIS_WIDTH = 640
const MARKER_RADIUS_PX = 14
/** Visual crosshair extent only — ROI math uses GAZE_POSITION_MARGIN_PX in constants/gaze.ts */
const MARKER_MARGIN_PX = 15

const DEFAULT_CONFIDENCE_HIGH = 0.4
const DEFAULT_CONFIDENCE_LOW = 0.28
const DEFAULT_FRAME_DROP_RATE_THRESHOLD = 0.3
const DEFAULT_FRAME_DROP_WINDOW = 30
const COORDINATE_SMOOTHING_ALPHA = 0.35

const props = withDefaults(
	defineProps<{
		videoSrc: string
		analyzing?: boolean
		showControls?: boolean
		showOverlayInteractions?: boolean
		/** 1 = validation (full pixel grid), 2 = realtime default. */
		pixelStride?: AnalyzerPixelStride
		/** Shorthand: pixelStride 1 + stricter drop threshold for QC runs. */
		validationMode?: boolean
		/** Emit marker-lost when confidence falls below this (hysteresis low band). */
		minDetectionConfidence?: number
		/** Fraction of offered frames dropped before frame-drops-exceeded (0–1). */
		frameDropRateThreshold?: number
		frameDropWindowSize?: number
	}>(),
	{
		analyzing: false,
		showControls: true,
		showOverlayInteractions: false,
		pixelStride: 2,
		validationMode: false,
		minDetectionConfidence: DEFAULT_CONFIDENCE_HIGH,
		frameDropRateThreshold: DEFAULT_FRAME_DROP_RATE_THRESHOLD,
		frameDropWindowSize: DEFAULT_FRAME_DROP_WINDOW
	}
)

const emit = defineEmits<{
	(
		e: 'marker-detected',
		payload: { coordinates: MarkerCoordinates; frameIndex: number; videoTimestamp: number }
	): void
	(e: 'marker-lost', payload: { frameIndex: number; videoTimestamp: number; reason: 'no-marker' | 'low-confidence' }): void
	(e: 'frame-drops-exceeded', payload: FrameDropQualityPayload): void
}>()

const videoElementRef = ref<HTMLVideoElement | null>(null)
const overlayCanvasRef = ref<HTMLCanvasElement | null>(null)
const captureCanvasRef = ref<HTMLCanvasElement | null>(null)

const markerPosition = ref<MarkerCoordinates | null>(null)

const frameDropStats = reactive({
	framesOffered: 0,
	framesDropped: 0,
	framesProcessed: 0,
	dropRate: 0
})

const effectivePixelStride = computed<AnalyzerPixelStride>(() =>
	props.validationMode ? 1 : props.pixelStride
)

const confidenceLowThreshold = computed(
	() => props.minDetectionConfidence * (DEFAULT_CONFIDENCE_LOW / DEFAULT_CONFIDENCE_HIGH)
)

let analyzerWorker: Worker | null = null
let frameIndex = 0
let workerBusy = false
let analysisLoopActive = false
let videoFrameCallbackId: number | null = null
let analysisWidth = 0
let analysisHeight = 0
let videoNativeWidth = 0
let videoNativeHeight = 0
let markerTrackingActive = false
let hasSmoothedSample = false
let smoothedVideoX = 0
let smoothedVideoY = 0
let frameDropQcEmitted = false

const qcWindow = reactive({
	offered: 0,
	dropped: 0,
	processed: 0
})

function getWorker(): Worker {
	if (!analyzerWorker) {
		analyzerWorker = new Worker(
			new URL('../../workers/analyzerWorker.ts', import.meta.url),
			{ type: 'module' }
		)
		analyzerWorker.onmessage = onWorkerMessage
		analyzerWorker.onerror = (error) => {
			console.error('Analyzer worker error:', error)
			workerBusy = false
		}
		postWorkerConfigure()
	}
	return analyzerWorker
}

function postWorkerConfigure(): void {
	const message: ConfigureAnalyzerMessage = {
		type: 'configure',
		pixelStride: effectivePixelStride.value
	}
	getWorker().postMessage(message)
}

function terminateWorker(): void {
	analyzerWorker?.terminate()
	analyzerWorker = null
	workerBusy = false
}

function resetFrameDropAccounting(): void {
	qcWindow.offered = 0
	qcWindow.dropped = 0
	qcWindow.processed = 0
	frameDropStats.framesOffered = 0
	frameDropStats.framesDropped = 0
	frameDropStats.framesProcessed = 0
	frameDropStats.dropRate = 0
	frameDropQcEmitted = false
}

function recordFrameOffered(): void {
	qcWindow.offered += 1
	frameDropStats.framesOffered += 1
}

function recordFrameDropped(): void {
	qcWindow.dropped += 1
	frameDropStats.framesDropped += 1
	updateDropRate()
	evaluateFrameDropThreshold()
}

function recordFrameProcessed(): void {
	qcWindow.processed += 1
	frameDropStats.framesProcessed += 1
	updateDropRate()

	if (qcWindow.processed >= props.frameDropWindowSize) {
		qcWindow.offered = 0
		qcWindow.dropped = 0
		qcWindow.processed = 0
		frameDropQcEmitted = false
	}
}

function updateDropRate(): void {
	const denominator = frameDropStats.framesOffered
	frameDropStats.dropRate = denominator > 0 ? frameDropStats.framesDropped / denominator : 0
}

function evaluateFrameDropThreshold(): void {
	if (frameDropQcEmitted || qcWindow.offered < props.frameDropWindowSize) {
		return
	}

	const windowDropRate = qcWindow.dropped / qcWindow.offered
	const threshold = props.validationMode
		? props.frameDropRateThreshold * 0.5
		: props.frameDropRateThreshold

	if (windowDropRate < threshold) {
		return
	}

	frameDropQcEmitted = true
	const payload: FrameDropQualityPayload = {
		dropRate: windowDropRate,
		framesDropped: qcWindow.dropped,
		framesOffered: qcWindow.offered,
		framesProcessed: qcWindow.processed,
		windowSize: props.frameDropWindowSize
	}
	emit('frame-drops-exceeded', payload)
}

/**
 * Maps analysis-buffer coordinates to native video pixel space.
 * captureCanvas is filled with drawImage(video, 0, 0, analysisW, analysisH) using
 * uniform scale s = analysisWidth / videoNativeWidth (width-limited to 640px).
 * Therefore videoX = analysisX * (videoNativeWidth / analysisWidth) — same factor for Y.
 */
function scaleMarkerToVideoSpace(marker: MarkerCoordinates): MarkerCoordinates {
	if (analysisWidth <= 0 || analysisHeight <= 0 || videoNativeWidth <= 0) {
		return marker
	}

	const scaleX = videoNativeWidth / analysisWidth
	const scaleY = videoNativeHeight / analysisHeight

	return {
		x: Math.round(marker.x * scaleX),
		y: Math.round(marker.y * scaleY),
		confidence: marker.confidence
	}
}

function applyConfidenceGate(rawMarker: MarkerCoordinates | null): {
	marker: MarkerCoordinates | null
	reason: 'no-marker' | 'low-confidence' | null
} {
	if (!rawMarker) {
		markerTrackingActive = false
		hasSmoothedSample = false
		return { marker: null, reason: 'no-marker' }
	}

	const { confidence } = rawMarker

	if (markerTrackingActive) {
		if (confidence < confidenceLowThreshold.value) {
			markerTrackingActive = false
			hasSmoothedSample = false
			return { marker: null, reason: 'low-confidence' }
		}
		return { marker: rawMarker, reason: null }
	}

	if (confidence >= props.minDetectionConfidence) {
		markerTrackingActive = true
		return { marker: rawMarker, reason: null }
	}

	return { marker: null, reason: 'low-confidence' }
}

function smoothVideoSpaceMarker(marker: MarkerCoordinates): MarkerCoordinates {
	if (!hasSmoothedSample) {
		hasSmoothedSample = true
		smoothedVideoX = marker.x
		smoothedVideoY = marker.y
		return marker
	}

	const alpha = COORDINATE_SMOOTHING_ALPHA
	smoothedVideoX = smoothedVideoX * (1 - alpha) + marker.x * alpha
	smoothedVideoY = smoothedVideoY * (1 - alpha) + marker.y * alpha

	return {
		x: Math.round(smoothedVideoX),
		y: Math.round(smoothedVideoY),
		confidence: marker.confidence
	}
}

function computeAnalysisDimensions(videoWidth: number, videoHeight: number): { width: number; height: number } {
	if (videoWidth <= MAX_ANALYSIS_WIDTH) {
		return { width: videoWidth, height: videoHeight }
	}
	const scale = MAX_ANALYSIS_WIDTH / videoWidth
	return {
		width: MAX_ANALYSIS_WIDTH,
		height: Math.round(videoHeight * scale)
	}
}

function syncOverlayCanvasSize(): void {
	const overlayCanvas = overlayCanvasRef.value
	if (!overlayCanvas || videoNativeWidth === 0) {
		return
	}

	overlayCanvas.width = videoNativeWidth
	overlayCanvas.height = videoNativeHeight
	drawMarkerOverlay(markerPosition.value)
}

function onVideoMetadataLoaded(): void {
	const video = videoElementRef.value
	const captureCanvas = captureCanvasRef.value
	if (!video || !captureCanvas || video.videoWidth === 0) {
		return
	}

	videoNativeWidth = video.videoWidth
	videoNativeHeight = video.videoHeight

	const dimensions = computeAnalysisDimensions(videoNativeWidth, videoNativeHeight)
	analysisWidth = dimensions.width
	analysisHeight = dimensions.height
	captureCanvas.width = analysisWidth
	captureCanvas.height = analysisHeight

	syncOverlayCanvasSize()

	if (props.analyzing) {
		startAnalysisLoop()
	}
}

function onVideoPlay(): void {
	if (props.analyzing) {
		startAnalysisLoop()
	}
}

function onVideoPause(): void {
	stopAnalysisLoop()
}

function onVideoSeeked(): void {
	if (props.analyzing) {
		enqueueFrameAnalysis()
	}
}

function startAnalysisLoop(): void {
	if (analysisLoopActive) {
		return
	}
	analysisLoopActive = true
	scheduleNextFrame()
}

function stopAnalysisLoop(): void {
	analysisLoopActive = false
	if (videoFrameCallbackId !== null && videoElementRef.value) {
		videoElementRef.value.cancelVideoFrameCallback(videoFrameCallbackId)
		videoFrameCallbackId = null
	}
}

function scheduleNextFrame(): void {
	const video = videoElementRef.value
	if (!video || !analysisLoopActive || !props.analyzing) {
		return
	}

	if ('requestVideoFrameCallback' in video) {
		videoFrameCallbackId = video.requestVideoFrameCallback(() => {
			enqueueFrameAnalysis()
			scheduleNextFrame()
		})
		return
	}

	requestAnimationFrame(() => {
		if (!analysisLoopActive) {
			return
		}
		enqueueFrameAnalysis()
		scheduleNextFrame()
	})
}

function enqueueFrameAnalysis(): void {
	if (!props.analyzing) {
		return
	}

	recordFrameOffered()

	if (workerBusy) {
		recordFrameDropped()
		return
	}

	const video = videoElementRef.value
	const captureCanvas = captureCanvasRef.value
	if (!video || !captureCanvas || video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
		return
	}
	if (analysisWidth === 0 || analysisHeight === 0) {
		return
	}

	const captureContext = captureCanvas.getContext('2d', { willReadFrequently: true })
	if (!captureContext) {
		return
	}

	captureContext.drawImage(video, 0, 0, analysisWidth, analysisHeight)
	const imageData = captureContext.getImageData(0, 0, analysisWidth, analysisHeight)
	const currentFrameIndex = frameIndex
	frameIndex += 1
	workerBusy = true

	const message: AnalyzeFrameMessage = {
		type: 'analyze',
		frameIndex: currentFrameIndex,
		width: analysisWidth,
		height: analysisHeight,
		buffer: imageData.data.buffer
	}

	getWorker().postMessage(message, [imageData.data.buffer])
}

function onWorkerMessage(event: MessageEvent<AnalyzeResultMessage>): void {
	workerBusy = false
	recordFrameProcessed()

	const { frameIndex: resultFrameIndex, marker: rawAnalysisMarker } = event.data
	const video = videoElementRef.value
	const videoTimestamp = video?.currentTime ?? 0

	const scaledMarker = rawAnalysisMarker ? scaleMarkerToVideoSpace(rawAnalysisMarker) : null
	const { marker: gatedMarker, reason } = applyConfidenceGate(scaledMarker)

	if (gatedMarker) {
		const stableMarker = smoothVideoSpaceMarker(gatedMarker)
		markerPosition.value = stableMarker
		drawMarkerOverlay(stableMarker)
		emit('marker-detected', {
			coordinates: stableMarker,
			frameIndex: resultFrameIndex,
			videoTimestamp
		})
		return
	}

	markerPosition.value = null
	drawMarkerOverlay(null)
	emit('marker-lost', {
		frameIndex: resultFrameIndex,
		videoTimestamp,
		reason: reason ?? 'no-marker'
	})
}

function drawMarkerOverlay(marker: MarkerCoordinates | null): void {
	const overlayCanvas = overlayCanvasRef.value
	if (!overlayCanvas) {
		return
	}

	const context = overlayCanvas.getContext('2d')
	if (!context) {
		return
	}

	context.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height)

	if (!marker) {
		return
	}

	const { x, y } = marker

	context.save()
	context.strokeStyle = '#56B6C2'
	context.fillStyle = 'rgba(6, 158, 189, 0.25)'
	context.lineWidth = 2

	context.beginPath()
	context.arc(x, y, MARKER_RADIUS_PX, 0, Math.PI * 2)
	context.fill()
	context.stroke()

	context.strokeStyle = '#E5C07B'
	context.beginPath()
	context.moveTo(x - MARKER_RADIUS_PX - MARKER_MARGIN_PX, y)
	context.lineTo(x + MARKER_RADIUS_PX + MARKER_MARGIN_PX, y)
	context.moveTo(x, y - MARKER_RADIUS_PX - MARKER_MARGIN_PX)
	context.lineTo(x, y + MARKER_RADIUS_PX + MARKER_MARGIN_PX)
	context.stroke()

	context.restore()
}

watch(
	() => props.analyzing,
	(isAnalyzing) => {
		if (isAnalyzing) {
			resetFrameDropAccounting()
			startAnalysisLoop()
			enqueueFrameAnalysis()
			return
		}
		stopAnalysisLoop()
	}
)

watch(
	() => [effectivePixelStride.value, props.validationMode] as const,
	() => {
		if (analyzerWorker) {
			postWorkerConfigure()
		}
	}
)

watch(
	() => props.videoSrc,
	() => {
		markerPosition.value = null
		markerTrackingActive = false
		hasSmoothedSample = false
		frameIndex = 0
		resetFrameDropAccounting()
		drawMarkerOverlay(null)
	}
)

onBeforeUnmount(() => {
	stopAnalysisLoop()
	terminateWorker()
})

defineExpose({
	markerPosition,
	frameDropStats,
	enqueueFrameAnalysis,
	resetFrameDropAccounting
})
</script>

<style scoped>
.video-analyzer__capture {
	position: absolute;
	width: 0;
	height: 0;
	overflow: hidden;
	pointer-events: none;
	visibility: hidden;
}

.video-analyzer__status {
	position: absolute;
	left: 12px;
	bottom: 12px;
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 6px 10px;
	border-radius: 6px;
	font-size: 12px;
	color: var(--color-text);
	background: rgba(30, 33, 39, 0.85);
	border: 1px solid var(--color-border);
	pointer-events: none;
	z-index: 2;
}

.video-analyzer__badge {
	padding: 1px 6px;
	border-radius: 4px;
	font-size: 10px;
	text-transform: uppercase;
	background: var(--color-info);
	color: var(--color-background);
}

.video-analyzer__pulse {
	width: 8px;
	height: 8px;
	border-radius: 50%;
	background: var(--color-success);
	animation: video-analyzer-pulse 1.2s ease-in-out infinite;
}

@keyframes video-analyzer-pulse {
	0%,
	100% {
		opacity: 1;
		transform: scale(1);
	}
	50% {
		opacity: 0.45;
		transform: scale(0.85);
	}
}
</style>
