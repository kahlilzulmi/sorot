import type { GazeTimestampUnit } from '../utils/gazeTimestamp'

export interface GazeImportSummary {
	validRowCount: number
	skippedRowCount: number
	columnMapping: {
		x: string
		y: string
		timestamp: string
	}
	timestampUnit: GazeTimestampUnit
	assumedVideoFps: number | null
	warnings: string[]
}
