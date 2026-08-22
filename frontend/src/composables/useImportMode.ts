import { computed, ref, type Ref } from 'vue'
import type { VideoInfo } from '../types/workspace'
import type { GazeCoordinate } from '../types/gaze'
import type { GazeImportSummary } from '../types/gazeImport'
import { apiPost, apiPostForm } from './useApiClient'
import { normalizeCsvText, parseCsvRecord, splitCsvRecords } from '../utils/csv/csvParse'
import { normalizeGazeTimestamps } from '../utils/gazeTimestamp'

export type ImportMethod = 'csv' | 'auto'

interface ImportColumnMapping {
	x: string
	y: string
	timestamp: string
}

interface BackendGazePoint {
	frame_num: number
	gaze_x: number
	gaze_y: number
}

interface ImportGazeResponse {
	success?: boolean
	message?: string
	gaze_points?: number
}

interface AutoDetectGazePoint {
	frame: number
	gaze_x: number | null
	gaze_y: number | null
	detection_confidence?: number
}

interface AutoDetectResponse {
	success?: boolean
	error?: string
	gaze_data?: AutoDetectGazePoint[]
	total_frames?: number
	total_points?: number
	detection_rate?: number
}

interface GazeVideoUploadResponse {
	success?: boolean
	path?: string
	filename?: string
	error?: string
}

export interface ImportedGazePayload {
	samples: GazeCoordinate[]
	fileName: string | null
	summary: GazeImportSummary
}

export interface ImportVideoUploadResult {
	videoInfo: VideoInfo
	gazeVideoPath?: string
	gazeVideoFilename?: string
}

export function useImportMode(
	videoInfo: Ref<VideoInfo | null>,
	onImportApplied: (payload: ImportedGazePayload) => void,
	setStatus: (message: string) => void
) {
	const importMethod = ref<ImportMethod>('auto')
	const csvFileName = ref<string | null>(null)
	const importedVideoFile = ref<File | null>(null)
	const importedGazeVideoFile = ref<File | null>(null)
	const headers = ref<string[]>([])
	const dataRows = ref<string[][]>([])
	const mapping = ref<ImportColumnMapping>({
		x: '',
		y: '',
		timestamp: ''
	})
	const frameOffset = ref(0)
	const warnings = ref<string[]>([])
	const errors = ref<string[]>([])
	const validRowCount = ref(0)
	const skippedRowCount = ref(0)

	const canApplyImport = computed(() => {
		return (
			headers.value.length > 0
			&& mapping.value.x.length > 0
			&& mapping.value.y.length > 0
			&& mapping.value.timestamp.length > 0
			&& mapping.value.x !== mapping.value.y
			&& mapping.value.x !== mapping.value.timestamp
			&& mapping.value.y !== mapping.value.timestamp
		)
	})

	const canApplyCsvImport = computed(() => canApplyImport.value)

	const canApplyAutoImport = computed(() => {
		return !!importedVideoFile.value && !!importedGazeVideoFile.value
	})

	function resetImportState(): void {
		importMethod.value = 'auto'
		csvFileName.value = null
		importedVideoFile.value = null
		importedGazeVideoFile.value = null
		headers.value = []
		dataRows.value = []
		mapping.value = { x: '', y: '', timestamp: '' }
		warnings.value = []
		errors.value = []
		validRowCount.value = 0
		skippedRowCount.value = 0
	}

	function suggestMapping(nextHeaders: string[]): ImportColumnMapping {
		const normalized = nextHeaders.map((h) => h.trim().toLowerCase())
		const pick = (candidates: RegExp[]): string => {
			for (let i = 0; i < normalized.length; i += 1) {
				if (candidates.some((pattern) => pattern.test(normalized[i]))) {
					return nextHeaders[i]
				}
			}
			return ''
		}

		const x = pick([/^x$/, /^gaze_x$/, /x_coord/, /position_x/])
		const y = pick([/^y$/, /^gaze_y$/, /y_coord/, /position_y/])
		let timestamp = pick([/^timestamp$/, /^time$/, /^ts$/, /frame/])
		if (!timestamp && nextHeaders.length > 0) {
			timestamp = nextHeaders[0]
		}

		return { x, y, timestamp }
	}

	async function parseCsvFile(file: File): Promise<void> {
		csvFileName.value = file.name
		headers.value = []
		dataRows.value = []
		mapping.value = { x: '', y: '', timestamp: '' }
		warnings.value = []
		errors.value = []
		validRowCount.value = 0
		skippedRowCount.value = 0
		importMethod.value = 'csv'
		try {
			const text = await file.text()
			const records = splitCsvRecords(normalizeCsvText(text))
			if (records.length < 2) {
				errors.value = ['CSV must include a header row and at least one data row.']
				return
			}

			const parsedHeaders = parseCsvRecord(records[0])
			headers.value = parsedHeaders
			mapping.value = suggestMapping(parsedHeaders)
			dataRows.value = records.slice(1).map((line) => parseCsvRecord(line))
			setStatus(`CSV loaded: ${file.name}`)
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Unknown CSV read error'
			errors.value = [`Failed to read CSV file: ${message}`]
		}
	}

	function setMappingField(field: keyof ImportColumnMapping, value: string): void {
		mapping.value = {
			...mapping.value,
			[field]: value
		}
	}

	function setFrameOffset(nextOffset: number): void {
		frameOffset.value = Number.isFinite(nextOffset) ? nextOffset : 0
	}

	function setImportMethod(method: ImportMethod): void {
		importMethod.value = method
	}

	function setImportedVideoFile(file: File | null): void {
		importedVideoFile.value = file
	}

	function setImportedGazeVideoFile(file: File | null): void {
		importedGazeVideoFile.value = file
	}

	function convertAutoDetectSamples(points: AutoDetectGazePoint[], fps: number): GazeCoordinate[] {
		return points
			.filter(
				(point) =>
					point.gaze_x !== null
					&& point.gaze_y !== null
					&& Number.isFinite(point.gaze_x)
					&& Number.isFinite(point.gaze_y)
			)
			.map((point) => ({
				x: point.gaze_x as number,
				y: point.gaze_y as number,
				timestamp: point.frame / fps
			}))
			.sort((a, b) => a.timestamp - b.timestamp)
	}

	async function uploadGazeVideoFile(file: File): Promise<GazeVideoUploadResponse> {
		const formData = new FormData()
		formData.append('video', file)
		return apiPostForm<GazeVideoUploadResponse>('/api/upload-gaze-video', formData)
	}

	async function syncGazeToBackend(samples: GazeCoordinate[], fps: number, offsetFrames: number): Promise<boolean> {
		const backendPayload: BackendGazePoint[] = samples.map((sample) => ({
			frame_num: Math.round(sample.timestamp * fps),
			gaze_x: sample.x,
			gaze_y: sample.y
		}))

		try {
			const response = await apiPost<ImportGazeResponse>('/api/import-gaze-data', {
				gaze_data: backendPayload,
				frame_offset: offsetFrames
			})
			if (!response.success) {
				errors.value = [response.message ?? 'Backend rejected imported gaze data.']
				return false
			}
			return true
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Failed to sync gaze data to backend'
			errors.value = [message]
			return false
		}
	}

	function buildImportPayload(
		shifted: GazeCoordinate[],
		fileName: string | null,
		normalized: ReturnType<typeof normalizeGazeTimestamps>
	): ImportedGazePayload {
		const summary: GazeImportSummary = {
			validRowCount: shifted.length,
			skippedRowCount: skippedRowCount.value,
			columnMapping: {
				x: mapping.value.x,
				y: mapping.value.y,
				timestamp: mapping.value.timestamp
			},
			timestampUnit: normalized.detectedUnit,
			assumedVideoFps: normalized.assumedVideoFps,
			warnings: warnings.value
		}

		return {
			samples: shifted,
			fileName,
			summary
		}
	}

	async function applyImport(
		uploadStimulusVideo?: (file: File) => Promise<boolean>,
		onComplete?: (result: ImportVideoUploadResult | null, payload: ImportedGazePayload) => void
	): Promise<boolean> {
		warnings.value = []
		errors.value = []
		validRowCount.value = 0
		skippedRowCount.value = 0

		if (!videoInfo.value) {
			if (!importedVideoFile.value || !uploadStimulusVideo) {
				errors.value = ['Load a stimulus video first, or select one in the import modal.']
				return false
			}
			const uploaded = await uploadStimulusVideo(importedVideoFile.value)
			if (!uploaded || !videoInfo.value) {
				errors.value = ['Failed to upload stimulus video.']
				return false
			}
		}

		if (!canApplyImport.value) {
			errors.value = ['Please map X, Y, and timestamp columns before importing.']
			return false
		}

		const xIndex = headers.value.indexOf(mapping.value.x)
		const yIndex = headers.value.indexOf(mapping.value.y)
		const tIndex = headers.value.indexOf(mapping.value.timestamp)

		if (xIndex < 0 || yIndex < 0 || tIndex < 0) {
			errors.value = ['Selected mapping columns are invalid.']
			return false
		}

		const parsed: GazeCoordinate[] = []
		for (const row of dataRows.value) {
			const x = Number(row[xIndex] ?? '')
			const y = Number(row[yIndex] ?? '')
			const timestamp = Number(row[tIndex] ?? '')
			if (!Number.isFinite(x) || !Number.isFinite(y) || !Number.isFinite(timestamp)) {
				skippedRowCount.value += 1
				continue
			}
			parsed.push({ x, y, timestamp })
		}

		if (parsed.length === 0) {
			errors.value = ['No valid gaze rows found after applying selected mapping.']
			return false
		}

		validRowCount.value = parsed.length
		if (skippedRowCount.value > 0) {
			warnings.value.push(`Skipped ${skippedRowCount.value} invalid row(s).`)
		}

		const normalized = normalizeGazeTimestamps(parsed, {
			timestampHeader: mapping.value.timestamp,
			videoFps: videoInfo.value?.fps ?? null
		})
		if (normalized.warnings.length > 0) {
			warnings.value.push(...normalized.warnings)
		}

		const fps = videoInfo.value!.fps > 0 ? videoInfo.value!.fps : 30
		const offsetSeconds = frameOffset.value / fps
		const shifted = normalized.coordinates
			.map((sample) => ({
				...sample,
				timestamp: Math.max(0, sample.timestamp + offsetSeconds)
			}))
			.sort((a, b) => a.timestamp - b.timestamp)

		const synced = await syncGazeToBackend(shifted, fps, 0)
		if (!synced) return false

		let gazeVideoPath: string | undefined
		let gazeVideoFilename: string | undefined
		if (importedGazeVideoFile.value) {
			try {
				const gazeUpload = await uploadGazeVideoFile(importedGazeVideoFile.value)
				if (gazeUpload.success && gazeUpload.path) {
					gazeVideoPath = gazeUpload.path
					gazeVideoFilename = importedGazeVideoFile.value.name
				} else {
					warnings.value.push(gazeUpload.error ?? 'Gaze video upload failed; continuing without dual-video view.')
				}
			} catch {
				warnings.value.push('Gaze video upload failed; continuing without dual-video view.')
			}
		}

		const payload = buildImportPayload(shifted, csvFileName.value, normalized)
		onImportApplied(payload)
		onComplete?.(
			gazeVideoPath && videoInfo.value
				? { videoInfo: videoInfo.value, gazeVideoPath, gazeVideoFilename }
				: null,
			payload
		)
		setStatus(`Imported ${shifted.length} gaze samples (offset ${frameOffset.value} frames)`)
		return true
	}

	function filenameFromVideoPath(path: string): string {
		const parts = path.split('/')
		return parts[parts.length - 1] ?? path
	}

	async function processAutoDetect(
		uploadStimulusVideo: (file: File) => Promise<boolean>,
		onComplete: (result: ImportVideoUploadResult, payload: ImportedGazePayload) => void
	): Promise<boolean> {
		warnings.value = []
		errors.value = []

		if (!canApplyAutoImport.value || !importedVideoFile.value || !importedGazeVideoFile.value) {
			errors.value = ['Select both eye gaze video and stimulus video for auto-detection.']
			return false
		}

		setStatus('Uploading videos for auto-detection...')

		const stimulusUploaded = await uploadStimulusVideo(importedVideoFile.value)
		if (!stimulusUploaded || !videoInfo.value) {
			errors.value = ['Failed to upload stimulus video.']
			return false
		}

		let gazeVideoPath: string | undefined
		let gazeVideoFilename: string | undefined
		try {
			const gazeUpload = await uploadGazeVideoFile(importedGazeVideoFile.value)
			if (!gazeUpload.success || !gazeUpload.filename) {
				errors.value = [gazeUpload.error ?? 'Failed to upload gaze video.']
				return false
			}
			gazeVideoPath = gazeUpload.path ?? `/video/${gazeUpload.filename}`
			gazeVideoFilename = importedGazeVideoFile.value.name
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Gaze video upload failed'
			errors.value = [message]
			return false
		}

		setStatus('Auto-detecting gaze coordinates from video...')
		try {
			const response = await apiPost<AutoDetectResponse>('/api/import/auto-detect-gaze', {
				gaze_video_filename: filenameFromVideoPath(gazeVideoPath),
				stimulus_video_info: videoInfo.value
			})

			if (!response.success || !response.gaze_data) {
				errors.value = [response.error ?? 'Auto-detection failed.']
				return false
			}

			const fps = videoInfo.value.fps > 0 ? videoInfo.value.fps : 30
			const samples = convertAutoDetectSamples(response.gaze_data, fps)
			if (samples.length === 0) {
				errors.value = ['Auto-detection found no valid gaze points.']
				return false
			}

			const synced = await syncGazeToBackend(samples, fps, frameOffset.value)
			if (!synced) return false

			const payload: ImportedGazePayload = {
				samples,
				fileName: importedGazeVideoFile.value.name,
				summary: {
					validRowCount: samples.length,
					skippedRowCount: (response.total_frames ?? 0) - (response.total_points ?? 0),
					columnMapping: { x: 'auto', y: 'auto', timestamp: 'frame' },
					timestampUnit: 'frame_index',
					assumedVideoFps: fps,
					warnings: [
						`Auto-detected ${response.total_points ?? samples.length} points (${(response.detection_rate ?? 0).toFixed(1)}% success rate).`
					]
				}
			}

			onImportApplied(payload)

			onComplete(
				{
					videoInfo: videoInfo.value,
					gazeVideoPath,
					gazeVideoFilename
				},
				payload
			)

			setStatus(
				`Auto-detection complete: ${response.total_points ?? samples.length} points (${(response.detection_rate ?? 0).toFixed(1)}% success rate)`
			)
			return true
		} catch (error) {
			const message = error instanceof Error ? error.message : 'Auto-detection failed'
			errors.value = [message]
			setStatus('Auto-detection failed')
			return false
		}
	}

	return {
		importMethod,
		csvFileName,
		importedVideoFile,
		importedGazeVideoFile,
		headers,
		mapping,
		frameOffset,
		warnings,
		errors,
		validRowCount,
		skippedRowCount,
		canApplyImport,
		canApplyCsvImport,
		canApplyAutoImport,
		parseCsvFile,
		setMappingField,
		setFrameOffset,
		setImportMethod,
		setImportedVideoFile,
		setImportedGazeVideoFile,
		applyImport,
		processAutoDetect,
		resetImportState
	}
}
