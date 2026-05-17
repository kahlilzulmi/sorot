import type {
	AnalyzeFrameMessage,
	AnalyzeResultMessage,
	AnalyzerPixelStride,
	AnalyzerWorkerInbound,
	ConfigureAnalyzerMessage,
	MarkerCoordinates
} from '../types/analyzer'

/*
 * =============================================================================
 * Tobii Ghost marker detection — worker-side notes
 * =============================================================================
 *
 * VISUAL TARGET
 * Tobii Ghost draws a cyan ring (~#00B4D8–#00D4FF) with a bright white core.
 * Recordings are BGRA in canvas ImageData (RGBA byte order: R,G,B,A).
 *
 * COLOR THRESHOLDS (tuned on 1080p OBS eyegaze captures)
 * - Cyan ring: B>130, G>110, R<110, (B−R)>50, (G−R)>35
 *   · Looser G/B → more recall, more UI blues false-positive
 *   · Tighter R cap → rejects warm highlights on skin/UI
 * - Bright core fallback: luminance>215, G>180, B>180
 *   · Used when compression crushes cyan saturation
 *   · Risk: specular highlights on glasses or window glare
 *
 * PIXEL_STRIDE tradeoffs
 * - stride 1 (validation): visits every pixel → best centroid precision (~0px
 *   subsampling bias), ~4× CPU vs stride 2; use for offline QC / ground-truth.
 * - stride 2 (realtime): visits every 2nd pixel → ~4× faster, centroid can shift
 *   up to ~1 stride px in analysis space (scale to video: ≤2×stride×scaleX).
 *
 * MIN_MARKER_PIXELS is counted in *sampled* cells (after stride), not raw pixels.
 *
 * VALIDATION PLAN (manual QC)
 * 1. Test video: 1080p MP4, Tobii Ghost on, fixation cross at screen center 5s,
 *    saccades to corners, 10s occlusion (blink/hand).
 * 2. Expected detection rate: ≥90% on fixation/saccade segments; drops during
 *    occlusion are valid marker-lost.
 * 3. False positives: blue UI buttons, loading spinners, HDR skies — expect <2%
 *    frames outside overlay segments; review with stride 1 + high confidence.
 * 4. Repeatability: same clip ×3 runs, σ(center) < 3px in analysis space at
 *    stride 1; stride 2 may jitter ±2px — gate with confidence hysteresis on main.
 * =============================================================================
 */

const DEFAULT_PIXEL_STRIDE: AnalyzerPixelStride = 2
const MIN_MARKER_PIXELS_BY_STRIDE: Record<AnalyzerPixelStride, number> = {
	1: 48,
	2: 24
}

let pixelStride: AnalyzerPixelStride = DEFAULT_PIXEL_STRIDE

function getMinMarkerPixels(): number {
	return MIN_MARKER_PIXELS_BY_STRIDE[pixelStride]
}

function detectVisualMarker(
	pixels: Uint8ClampedArray,
	width: number,
	height: number
): MarkerCoordinates | null {
	const stride = pixelStride
	const minMarkerPixels = getMinMarkerPixels()

	let sumX = 0
	let sumY = 0
	let cyanCount = 0
	let brightCount = 0
	let brightSumX = 0
	let brightSumY = 0

	for (let y = 0; y < height; y += stride) {
		for (let x = 0; x < width; x += stride) {
			const index = (y * width + x) * 4
			const red = pixels[index]
			const green = pixels[index + 1]
			const blue = pixels[index + 2]

			const isCyanMarker =
				blue > 130 &&
				green > 110 &&
				red < 110 &&
				blue - red > 50 &&
				green - red > 35

			if (isCyanMarker) {
				sumX += x
				sumY += y
				cyanCount += 1
				continue
			}

			const luminance = 0.299 * red + 0.587 * green + 0.114 * blue
			const isBrightCore = luminance > 215 && green > 180 && blue > 180

			if (isBrightCore) {
				brightSumX += x
				brightSumY += y
				brightCount += 1
			}
		}
	}

	const useCyan = cyanCount >= minMarkerPixels
	const activeCount = useCyan ? cyanCount : brightCount

	if (activeCount < minMarkerPixels) {
		return null
	}

	const centerX = useCyan ? sumX / cyanCount : brightSumX / brightCount
	const centerY = useCyan ? sumY / cyanCount : brightSumY / brightCount

	const sampleDensity = activeCount / minMarkerPixels
	const cyanDominance = useCyan ? cyanCount / activeCount : 0.5
	const confidence = Math.min(1, Math.sqrt(sampleDensity) * (0.65 + 0.35 * cyanDominance))

	return {
		x: Math.round(centerX),
		y: Math.round(centerY),
		confidence
	}
}

function handleConfigure(message: ConfigureAnalyzerMessage): void {
	pixelStride = message.pixelStride === 1 ? 1 : 2
}

function handleAnalyze(message: AnalyzeFrameMessage): void {
	const { frameIndex, width, height, buffer } = message
	const pixels = new Uint8ClampedArray(buffer)
	const marker = detectVisualMarker(pixels, width, height)

	const response: AnalyzeResultMessage = {
		type: 'result',
		frameIndex,
		marker
	}

	self.postMessage(response)
}

self.onmessage = (event: MessageEvent<AnalyzerWorkerInbound>): void => {
	const message = event.data
	if (message.type === 'configure') {
		handleConfigure(message)
		return
	}
	handleAnalyze(message)
}
