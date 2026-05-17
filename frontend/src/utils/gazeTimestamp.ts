import type { GazeCoordinate } from '../types/gaze'

/**
 * Gaze timestamps in Pinia are always seconds (video playback time).
 * CSV sources may use seconds, milliseconds, or frame indices.
 */
export type GazeTimestampUnit = 'seconds' | 'milliseconds' | 'frame_index'

export interface NormalizeGazeTimestampsOptions {
	/** Raw timestamp column header from CSV (hints unit detection). */
	timestampHeader?: string
	/** Video FPS for frame_index → seconds; defaults to 30 when unknown. */
	videoFps?: number | null
}

export interface NormalizeGazeTimestampsResult {
	coordinates: GazeCoordinate[]
	detectedUnit: GazeTimestampUnit
	assumedVideoFps: number | null
	warnings: string[]
}

const DEFAULT_FPS = 30

function medianDelta(timestamps: number[]): number {
	if (timestamps.length < 2) {
		return 0
	}

	const sorted = [...timestamps].sort((a, b) => a - b)
	const deltas: number[] = []
	for (let index = 1; index < sorted.length; index += 1) {
		const delta = sorted[index] - sorted[index - 1]
		if (delta > 0) {
			deltas.push(delta)
		}
	}

	if (deltas.length === 0) {
		return 0
	}

	deltas.sort((a, b) => a - b)
	return deltas[Math.floor(deltas.length / 2)]
}

function unitFromHeader(timestampHeader: string | undefined): GazeTimestampUnit | null {
	if (!timestampHeader) {
		return null
	}

	const normalized = timestampHeader.trim().toLowerCase()
	if (/time_ms|timestamp_ms|_ms$|\bms\b/.test(normalized)) {
		return 'milliseconds'
	}
	if (/frame|frame_num|frame_index|frame_idx/.test(normalized)) {
		return 'frame_index'
	}
	if (/time_s|seconds|sec\b/.test(normalized)) {
		return 'seconds'
	}
	if (/^timestamp$|^time$|^ts$|^sample_time$/.test(normalized)) {
		return null
	}

	return null
}

/**
 * Infer timestamp unit from value distribution when the header is ambiguous.
 */
export function detectTimestampUnit(
	timestamps: number[],
	timestampHeader?: string
): GazeTimestampUnit {
	const fromHeader = unitFromHeader(timestampHeader)
	if (fromHeader) {
		return fromHeader
	}

	if (timestamps.length === 0) {
		return 'seconds'
	}

	const maxValue = Math.max(...timestamps)
	const medianStep = medianDelta(timestamps)
	const mostlyIntegers = timestamps.every((value) => Number.isInteger(value))

	if (mostlyIntegers && medianStep >= 0.9 && medianStep <= 1.1 && maxValue < 5_000_000) {
		return 'frame_index'
	}

	if (medianStep >= 5 && medianStep <= 120) {
		return 'milliseconds'
	}

	if (medianStep > 0 && medianStep < 0.25) {
		return 'seconds'
	}

	if (maxValue > 86_400 && mostlyIntegers) {
		return 'milliseconds'
	}

	if (maxValue <= 86_400) {
		return 'seconds'
	}

	return 'milliseconds'
}

function toSeconds(
	rawTimestamp: number,
	unit: GazeTimestampUnit,
	videoFps: number
): number {
	switch (unit) {
		case 'milliseconds':
			return rawTimestamp / 1000
		case 'frame_index':
			return rawTimestamp / videoFps
		default:
			return rawTimestamp
	}
}

/**
 * Normalize gaze sample timestamps to seconds for sync with HTML video `currentTime`.
 */
export function normalizeGazeTimestamps(
	coordinates: GazeCoordinate[],
	options: NormalizeGazeTimestampsOptions = {}
): NormalizeGazeTimestampsResult {
	const warnings: string[] = []

	if (coordinates.length === 0) {
		return {
			coordinates: [],
			detectedUnit: 'seconds',
			assumedVideoFps: null,
			warnings
		}
	}

	const rawTimestamps = coordinates.map((sample) => sample.timestamp)
	const detectedUnit = detectTimestampUnit(rawTimestamps, options.timestampHeader)
	const videoFps =
		options.videoFps && options.videoFps > 0 ? options.videoFps : DEFAULT_FPS
	const assumedVideoFps = detectedUnit === 'frame_index' ? videoFps : null

	if (detectedUnit === 'frame_index' && !options.videoFps) {
		warnings.push(
			`Timestamps look like frame indices; converted to seconds using ${videoFps} FPS (load video to refine).`
		)
	} else if (detectedUnit === 'milliseconds') {
		warnings.push('Timestamps detected as milliseconds; converted to seconds.')
	}

	const normalizedCoordinates = coordinates.map((sample) => ({
		x: sample.x,
		y: sample.y,
		timestamp: toSeconds(sample.timestamp, detectedUnit, videoFps)
	}))

	return {
		coordinates: normalizedCoordinates,
		detectedUnit,
		assumedVideoFps,
		warnings
	}
}
