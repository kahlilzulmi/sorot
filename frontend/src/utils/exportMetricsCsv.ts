import type { RoiTimeMetric } from '../types/metrics'
import { buildCsvContent, escapeCsvField } from './csv/csvParse'

export interface ExportMetricsCsvOptions {
	/** Download filename without path; `.csv` is appended if missing. */
	filename?: string
	/** ISO timestamp included as a metadata row when true (default: true). */
	includeGeneratedAt?: boolean
}

const ROI_METRIC_HEADERS = [
	'scene',
	'custom_name',
	'display_name',
	'roi_label',
	'gaze_count',
	'percentage',
	'total_samples'
] as const

/**
 * Data dictionary (also written as `#` comment rows in exported CSV):
 * - scene: analysis window label (default "Session")
 * - custom_name: optional researcher-defined scene alias (empty if unused)
 * - display_name: human-readable scene label shown in reports
 * - roi_label: ROI name drawn on the video frame
 * - gaze_count: samples attributed to this ROI (15px margin, topmost if overlap)
 * - percentage: share of attributed hits for this ROI (0–100); outside-ROI samples excluded
 * - total_samples: all gaze rows in the scene, including samples outside every ROI
 */
const ROI_METRIC_DATA_DICTIONARY = [
	'# scene — analysis window label',
	'# custom_name — optional scene alias (empty if unused)',
	'# display_name — label shown in reports',
	'# roi_label — region name on the video frame',
	'# gaze_count — gaze samples inside ROI (15px margin; topmost wins on overlap)',
	'# percentage — percent of attributed hits (samples outside ROIs not in denominator)',
	'# total_samples — all gaze rows in scene, including outside ROI'
] as const

function ensureCsvFilename(filename: string): string {
	const trimmed = filename.trim() || 'sorot_metrics'
	return trimmed.toLowerCase().endsWith('.csv') ? trimmed : `${trimmed}.csv`
}

function triggerBrowserDownload(blob: Blob, filename: string): void {
	const objectUrl = URL.createObjectURL(blob)
	const anchor = document.createElement('a')
	anchor.href = objectUrl
	anchor.download = filename
	anchor.style.display = 'none'
	document.body.appendChild(anchor)
	anchor.click()
	document.body.removeChild(anchor)
	URL.revokeObjectURL(objectUrl)
}

function metricToRow(metric: RoiTimeMetric): Array<string | number> {
	return [
		metric.scene,
		metric.customName ?? '',
		metric.displayName ?? metric.scene,
		metric.roiLabel,
		metric.gazeCount,
		metric.percentage.toFixed(2),
		metric.totalSamples ?? ''
	]
}

/**
 * Export calculated ROI metrics (e.g. percentage of time in each ROI) as a CSV download.
 */
export function exportRoiMetricsToCsv(
	metrics: RoiTimeMetric[],
	options: ExportMetricsCsvOptions = {}
): void {
	if (metrics.length === 0) {
		throw new Error('No metrics to export.')
	}

	const filename = ensureCsvFilename(options.filename ?? 'roi_statistics')
	const includeGeneratedAt = options.includeGeneratedAt ?? true
	const rows = metrics.map(metricToRow)

	let csvContent = buildCsvContent([...ROI_METRIC_HEADERS], rows)

	const metadataLines = [...ROI_METRIC_DATA_DICTIONARY]
	if (includeGeneratedAt) {
		const generatedAt = new Date().toISOString()
		metadataLines.push(`# generated_at,${escapeCsvField(generatedAt)}`)
	}
	csvContent = `${metadataLines.join('\n')}\n${csvContent}`

	const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' })
	triggerBrowserDownload(blob, filename)
}

/**
 * Export arbitrary metric rows with explicit column headers (client-side only).
 */
export function exportMetricsToCsv(
	headers: string[],
	rows: Array<Record<string, string | number>>,
	options: ExportMetricsCsvOptions = {}
): void {
	if (headers.length === 0) {
		throw new Error('CSV headers are required.')
	}
	if (rows.length === 0) {
		throw new Error('No metrics to export.')
	}

	const filename = ensureCsvFilename(options.filename ?? 'sorot_metrics')
	const includeGeneratedAt = options.includeGeneratedAt ?? true

	const dataRows = rows.map((row) => headers.map((header) => row[header] ?? ''))
	let csvContent = buildCsvContent(headers, dataRows)

	if (includeGeneratedAt) {
		const generatedAt = new Date().toISOString()
		csvContent = `# generated_at,${escapeCsvField(generatedAt)}\n${csvContent}`
	}

	const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' })
	triggerBrowserDownload(blob, filename)
}
