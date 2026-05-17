import type { GazeCoordinate } from '../types/gaze'
import { useGazeStore, type GazeImportSummary } from '../stores/useGazeStore'
import {
	normalizeCsvText,
	parseCsvRecord,
	splitCsvRecords
} from './csv/csvParse'
import { normalizeGazeTimestamps } from './gazeTimestamp'

export interface GazeCsvColumnMapping {
	x: number
	y: number
	timestamp: number
	headerLabels: {
		x: string
		y: string
		timestamp: string
	}
}

export interface GazeCsvParseResult {
	success: boolean
	gazeCoordinates: GazeCoordinate[]
	sourceFileName: string | null
	columnMapping: GazeCsvColumnMapping | null
	validRowCount: number
	skippedRowCount: number
	errors: string[]
	warnings: string[]
}

const X_HEADER_PATTERNS = [
	/^gaze_x$/i,
	/^x$/i,
	/^pos_x$/i,
	/^position_x$/i,
	/^gazex$/i,
	/^x_coord$/i
]

const Y_HEADER_PATTERNS = [
	/^gaze_y$/i,
	/^y$/i,
	/^pos_y$/i,
	/^position_y$/i,
	/^gazey$/i,
	/^y_coord$/i
]

const TIMESTAMP_HEADER_PATTERNS = [
	/^timestamp$/i,
	/^time$/i,
	/^ts$/i,
	/^time_ms$/i,
	/^time_s$/i,
	/^frame_num$/i,
	/^frame$/i,
	/^frame_index$/i,
	/^frame_idx$/i,
	/^sample_time$/i
]

function normalizeHeaderLabel(label: string): string {
	return label.trim().toLowerCase().replace(/\s+/g, '_')
}

function findColumnIndex(headers: string[], patterns: RegExp[]): number {
	const normalizedHeaders = headers.map(normalizeHeaderLabel)

	for (const pattern of patterns) {
		const index = normalizedHeaders.findIndex((header) => pattern.test(header))
		if (index !== -1) {
			return index
		}
	}

	return -1
}

function findLooseColumnIndex(headers: string[], keywords: string[]): number {
	const normalizedHeaders = headers.map(normalizeHeaderLabel)

	return normalizedHeaders.findIndex((header) => {
		const matchesKeyword = keywords.every((keyword) => header.includes(keyword))
		return matchesKeyword
	})
}

function detectColumnMapping(headers: string[]): GazeCsvColumnMapping | null {
	let xIndex = findColumnIndex(headers, X_HEADER_PATTERNS)
	let yIndex = findColumnIndex(headers, Y_HEADER_PATTERNS)
	let timestampIndex = findColumnIndex(headers, TIMESTAMP_HEADER_PATTERNS)

	if (xIndex === -1) {
		xIndex = findLooseColumnIndex(headers, ['gaze', 'x'])
	}
	if (yIndex === -1) {
		yIndex = findLooseColumnIndex(headers, ['gaze', 'y'])
	}
	if (timestampIndex === -1) {
		timestampIndex = findLooseColumnIndex(headers, ['time'])
	}
	if (timestampIndex === -1) {
		timestampIndex = findLooseColumnIndex(headers, ['frame'])
	}

	if (headers.length >= 3 && (xIndex === -1 || yIndex === -1 || timestampIndex === -1)) {
		const used = new Set<number>()
		const pickUnused = (preferred: number, fallback: number): number => {
			if (preferred !== -1 && !used.has(preferred)) {
				used.add(preferred)
				return preferred
			}
			if (!used.has(fallback)) {
				used.add(fallback)
				return fallback
			}
			return -1
		}

		if (timestampIndex === -1) timestampIndex = pickUnused(timestampIndex, 0)
		if (xIndex === -1) xIndex = pickUnused(xIndex, 1)
		if (yIndex === -1) yIndex = pickUnused(yIndex, 2)
	}

	if (xIndex === -1 || yIndex === -1 || timestampIndex === -1) {
		return null
	}

	if (new Set([xIndex, yIndex, timestampIndex]).size !== 3) {
		return null
	}

	return {
		x: xIndex,
		y: yIndex,
		timestamp: timestampIndex,
		headerLabels: {
			x: headers[xIndex] ?? 'x',
			y: headers[yIndex] ?? 'y',
			timestamp: headers[timestampIndex] ?? 'timestamp'
		}
	}
}

function parseNumericField(rawValue: string): number | null {
	const trimmed = rawValue.trim()
	if (trimmed.length === 0) {
		return null
	}

	const parsed = Number(trimmed)
	return Number.isFinite(parsed) ? parsed : null
}

function toImportSummary(
	result: GazeCsvParseResult,
	mapping: GazeCsvColumnMapping,
	timestampUnit: GazeImportSummary['timestampUnit'],
	assumedVideoFps: number | null
): GazeImportSummary {
	return {
		validRowCount: result.validRowCount,
		skippedRowCount: result.skippedRowCount,
		columnMapping: mapping.headerLabels,
		timestampUnit,
		assumedVideoFps,
		warnings: result.warnings
	}
}

function applyTimestampNormalization(
	rawCoordinates: GazeCoordinate[],
	timestampHeader: string,
	videoFps: number | null
): { coordinates: GazeCoordinate[]; summary: Pick<GazeImportSummary, 'timestampUnit' | 'assumedVideoFps' | 'warnings'> } {
	const normalization = normalizeGazeTimestamps(rawCoordinates, {
		timestampHeader,
		videoFps
	})

	return {
		coordinates: normalization.coordinates,
		summary: {
			timestampUnit: normalization.detectedUnit,
			assumedVideoFps: normalization.assumedVideoFps,
			warnings: normalization.warnings
		}
	}
}

/**
 * Parse raw CSV text containing gaze samples (X, Y, timestamp) into coordinates.
 */
export function parseGazeCsvText(csvText: string, sourceFileName: string | null = null): GazeCsvParseResult {
	const errors: string[] = []
	const warnings: string[] = []
	const gazeCoordinates: GazeCoordinate[] = []

	const normalizedText = normalizeCsvText(csvText)
	const records = splitCsvRecords(normalizedText)

	if (records.length < 2) {
		return {
			success: false,
			gazeCoordinates: [],
			sourceFileName,
			columnMapping: null,
			validRowCount: 0,
			skippedRowCount: 0,
			errors: ['CSV must include a header row and at least one data row.'],
			warnings
		}
	}

	const headers = parseCsvRecord(records[0])
	const columnMapping = detectColumnMapping(headers)

	if (!columnMapping) {
		return {
			success: false,
			gazeCoordinates: [],
			sourceFileName,
			columnMapping: null,
			validRowCount: 0,
			skippedRowCount: Math.max(0, records.length - 1),
			errors: [
				'Could not map CSV columns to X, Y, and timestamp. Expected headers such as gaze_x, gaze_y, timestamp (or frame_num).'
			],
			warnings
		}
	}

	let skippedRowCount = 0

	for (let rowIndex = 1; rowIndex < records.length; rowIndex += 1) {
		const fields = parseCsvRecord(records[rowIndex])
		const requiredWidth = Math.max(columnMapping.x, columnMapping.y, columnMapping.timestamp) + 1

		if (fields.length < requiredWidth) {
			skippedRowCount += 1
			continue
		}

		const x = parseNumericField(fields[columnMapping.x])
		const y = parseNumericField(fields[columnMapping.y])
		const timestamp = parseNumericField(fields[columnMapping.timestamp])

		if (x === null || y === null || timestamp === null) {
			skippedRowCount += 1
			continue
		}

		gazeCoordinates.push({ x, y, timestamp })
	}

	if (gazeCoordinates.length === 0) {
		errors.push('No valid gaze rows found after parsing.')
	}

	if (skippedRowCount > 0) {
		warnings.push(`Skipped ${skippedRowCount} invalid or incomplete row(s).`)
	}

	return {
		success: gazeCoordinates.length > 0,
		gazeCoordinates,
		sourceFileName,
		columnMapping,
		validRowCount: gazeCoordinates.length,
		skippedRowCount,
		errors,
		warnings
	}
}

/** Read a File as UTF-8 text and parse gaze coordinates. */
export async function parseGazeCsvFile(file: File): Promise<GazeCsvParseResult> {
	try {
		const csvText = await file.text()
		return parseGazeCsvText(csvText, file.name)
	} catch (error) {
		const message = error instanceof Error ? error.message : 'Unknown file read error'
		return {
			success: false,
			gazeCoordinates: [],
			sourceFileName: file.name,
			columnMapping: null,
			validRowCount: 0,
			skippedRowCount: 0,
			errors: [`Failed to read CSV file: ${message}`],
			warnings: []
		}
	}
}

/**
 * Parse an uploaded gaze CSV and load the result into the Pinia gaze store.
 */
export async function loadGazeCsvIntoStore(file: File): Promise<GazeCsvParseResult> {
	const gazeStore = useGazeStore()
	const parseResult = await parseGazeCsvFile(file)

	if (!parseResult.success || !parseResult.columnMapping) {
		gazeStore.clearGazeData()
		return parseResult
	}

	const normalization = applyTimestampNormalization(
		parseResult.gazeCoordinates,
		parseResult.columnMapping.headerLabels.timestamp,
		gazeStore.videoFps
	)

	const normalizedResult: GazeCsvParseResult = {
		...parseResult,
		gazeCoordinates: normalization.coordinates,
		warnings: [...parseResult.warnings, ...normalization.summary.warnings]
	}

	gazeStore.setGazeData(
		normalizedResult.gazeCoordinates,
		normalizedResult.sourceFileName,
		toImportSummary(
			normalizedResult,
			parseResult.columnMapping,
			normalization.summary.timestampUnit,
			normalization.summary.assumedVideoFps
		)
	)

	return normalizedResult
}
