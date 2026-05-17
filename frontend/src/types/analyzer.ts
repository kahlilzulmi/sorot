/** Pixel coordinates of a detected gaze / Tobii overlay marker in video space. */
export interface MarkerCoordinates {
	x: number
	y: number
	/** Normalized detection strength in [0, 1]. */
	confidence: number
}

export type AnalyzerPixelStride = 1 | 2

export interface ConfigureAnalyzerMessage {
	type: 'configure'
	/** 1 = validation (full grid), 2 = realtime (4× fewer samples). */
	pixelStride: AnalyzerPixelStride
}

export interface AnalyzeFrameMessage {
	type: 'analyze'
	frameIndex: number
	width: number
	height: number
	buffer: ArrayBuffer
}

export interface AnalyzeResultMessage {
	type: 'result'
	frameIndex: number
	marker: MarkerCoordinates | null
}

export interface FrameDropQualityPayload {
	/** Dropped ÷ offered over the current QC window, in [0, 1]. */
	dropRate: number
	framesDropped: number
	framesOffered: number
	framesProcessed: number
	windowSize: number
}

export type AnalyzerWorkerInbound = ConfigureAnalyzerMessage | AnalyzeFrameMessage
export type AnalyzerWorkerOutbound = AnalyzeResultMessage
